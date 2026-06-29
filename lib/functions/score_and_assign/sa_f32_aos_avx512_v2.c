/* sa_f32_aos_avx512_v2.c -- Wide-load + permute deinterleave AoS f32 AVX-512
 *
 * Replaces 48 scalar-gather loads per iteration (16x3) with
 * 3 wide loads + 6 _mm512_permutex2var_ps permutes.
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_avx512f",
 *         "sig": "int score_and_assign_f32_aos_avx512_v2(double ubi[3][3], const float gv[], double tol, float *drlv2, int *labels, int label, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "drlv2": "drlv2.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[0]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "../score_and_refine/sar_popcnt.h"
#include <stdint.h>
#include <math.h>
#ifdef _OPENMP
#include <omp.h>
#endif

/* Computed permute indices for AoS->SoA deinterleave of 16 f32 triples (48 floats) */
static const int I1X[16] = {0,3,6,9,12,15,18,21,24,27,30,0,0,0,0,0};
static const int I2X[16] = {0,1,2,3,4,5,6,7,8,9,10,17,20,23,26,29};
static const int I1Y[16] = {1,4,7,10,13,16,19,22,25,28,31,0,0,0,0,0};
static const int I2Y[16] = {0,1,2,3,4,5,6,7,8,9,10,18,21,24,27,30};
static const int I1Z[16] = {2,5,8,11,14,17,20,23,26,29,0,0,0,0,0,0};
static const int I2Z[16] = {0,1,2,3,4,5,6,7,8,9,16,19,22,25,28,31};

static int
sa_f32_aos_avx512_v2_kernel(const double ubi[9], const float *gv, double tol,
                             float *drlv2, int *labels, int label, intptr_t ng)
{
    __m512 u00=_mm512_set1_ps((float)ubi[0]),u01=_mm512_set1_ps((float)ubi[1]),u02=_mm512_set1_ps((float)ubi[2]);
    __m512 u10=_mm512_set1_ps((float)ubi[3]),u11=_mm512_set1_ps((float)ubi[4]),u12=_mm512_set1_ps((float)ubi[5]);
    __m512 u20=_mm512_set1_ps((float)ubi[6]),u21=_mm512_set1_ps((float)ubi[7]),u22=_mm512_set1_ps((float)ubi[8]);
    float tol2=(float)(tol*tol); __m512 tvec=_mm512_set1_ps(tol2);
    __m512i lbl_vec=_mm512_set1_epi32(label), neg=_mm512_set1_epi32(-1);
    __m512i idx1x=_mm512_loadu_si512(I1X), idx2x=_mm512_loadu_si512(I2X);
    __m512i idx1y=_mm512_loadu_si512(I1Y), idx2y=_mm512_loadu_si512(I2Y);
    __m512i idx1z=_mm512_loadu_si512(I1Z), idx2z=_mm512_loadu_si512(I2Z);
    int n=0; intptr_t k;

    for(k=0;k+16<=ng;k+=16){
        __m512 d0=_mm512_loadu_ps(&gv[k*3]);
        __m512 d1=_mm512_loadu_ps(&gv[k*3+16]);
        __m512 d2=_mm512_loadu_ps(&gv[k*3+32]);

        __m512 tmp_x=_mm512_permutex2var_ps(d0, idx1x, d1);
        __m512 gvx  =_mm512_permutex2var_ps(tmp_x, idx2x, d2);
        __m512 tmp_y=_mm512_permutex2var_ps(d0, idx1y, d1);
        __m512 gvy  =_mm512_permutex2var_ps(tmp_y, idx2y, d2);
        __m512 tmp_z=_mm512_permutex2var_ps(d0, idx1z, d1);
        __m512 gvz  =_mm512_permutex2var_ps(tmp_z, idx2z, d2);

        __m512 hx=_mm512_fmadd_ps(u00,gvx,_mm512_fmadd_ps(u01,gvy,_mm512_mul_ps(u02,gvz)));
        __m512 hy=_mm512_fmadd_ps(u10,gvx,_mm512_fmadd_ps(u11,gvy,_mm512_mul_ps(u12,gvz)));
        __m512 hz=_mm512_fmadd_ps(u20,gvx,_mm512_fmadd_ps(u21,gvy,_mm512_mul_ps(u22,gvz)));

        __m512 ihx=_mm512_roundscale_ps(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hx=_mm512_sub_ps(hx,ihx);
        __m512 ihy=_mm512_roundscale_ps(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hy=_mm512_sub_ps(hy,ihy);
        __m512 ihz=_mm512_roundscale_ps(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hz=_mm512_sub_ps(hz,ihz);
        __m512 sumsq=_mm512_fmadd_ps(hx,hx,_mm512_fmadd_ps(hy,hy,_mm512_mul_ps(hz,hz)));

        __m512 cur=_mm512_loadu_ps(&drlv2[k]);
        __mmask16 mask=_mm512_cmp_ps_mask(sumsq,tvec,_CMP_LT_OS);
        mask&=_mm512_cmp_ps_mask(sumsq,cur,_CMP_LT_OS);

        __m512i lbl=_mm512_loadu_si512(&labels[k]);
        __mmask16 eq=_mm512_cmpeq_epi32_mask(lbl,lbl_vec);
        __mmask16 clr=_kandn_mask16(mask,eq);
        lbl=_mm512_mask_mov_epi32(lbl,mask,lbl_vec);
        lbl=_mm512_mask_mov_epi32(lbl,clr,neg);
        _mm512_storeu_si512(&labels[k],lbl);

        if(mask){
            n+=popcnt32((unsigned)mask);
            _mm512_storeu_ps(&drlv2[k],_mm512_mask_blend_ps(mask,cur,sumsq));
        }
    }

    float tol_f=(float)(tol*tol);
    for(;k<ng;k++){
        float gx=gv[k*3],gy=gv[k*3+1],gz=gv[k*3+2];
        float hx_=(float)ubi[0]*gx+(float)ubi[1]*gy+(float)ubi[2]*gz; float ix=nearbyintf(hx_);
        float hy_=(float)ubi[3]*gx+(float)ubi[4]*gy+(float)ubi[5]*gz; float iy=nearbyintf(hy_);
        float hz_=(float)ubi[6]*gx+(float)ubi[7]*gy+(float)ubi[8]*gz; float iz=nearbyintf(hz_);
        float s=(hx_-ix)*(hx_-ix)+(hy_-iy)*(hy_-iy)+(hz_-iz)*(hz_-iz);
        if(s<tol_f&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

int score_and_assign_f32_aos_avx512_v2(double ubi[3][3], const float gv[], double tol,
                                        float *drlv2, int *labels, int label, intptr_t ng)
{
    int n=0;
#ifdef _OPENMP
    int nthr=omp_get_max_threads();
    if(ng>10000&&nthr>1){
        #pragma omp parallel reduction(+:n)
        { int tid=omp_get_thread_num(); intptr_t chunk=(ng+nthr-1)/nthr,start=tid*chunk;
          intptr_t end=(start+chunk<ng)?start+chunk:ng;
          if(start<ng)n=sa_f32_aos_avx512_v2_kernel((const double*)ubi,gv+start*3,tol,drlv2+start,labels+start,label,end-start);}
        return n;}
#endif
    return sa_f32_aos_avx512_v2_kernel((const double*)ubi,gv,tol,drlv2,labels,label,ng);
}
