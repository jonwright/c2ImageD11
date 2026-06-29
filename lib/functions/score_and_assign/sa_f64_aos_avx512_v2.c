/* sa_f64_aos_avx512_v2.c -- Wide-load + permute deinterleave AoS f64 AVX-512
 *
 * The 24 scalar loads per iteration (8x3 for AoS gather) are replaced
 * by 3 wide loads + 6 vpermt2pd permutes that deinterleave x/y/z.
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_avx512f",
 *         "sig": "int score_and_assign_f64_avx512_v2(double ubi[3][3], const double gv[], double tol, double *drlv2, int *labels, int label, intptr_t ng) -> int",
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

/* Permute indices for deinterleaving AoS -> SoA within 24 consecutive doubles.
 * The 3 input vectors (zmm0,zmm1,zmm2) contain ABCABC... data.
 * Two rounds of vpermt2pd extract the x, y, z components.
 *
 * Round 1: select from zmm0+zmm1 (16 elements). 6 of 8 are correct.
 * Round 2: select from round-1 temp + zmm2. All 8 correct.
 */
static const int64_t I1X[8] = {0,3,6,9,12,15, 0,0};  // x0-x5
static const int64_t I2X[8] = {0,1,2,3,4,5,10,13};  // x0-x5 + x6-x7
static const int64_t I1Y[8] = {1,4,7,10,13, 0,0,0};  // y0-y4
static const int64_t I2Y[8] = {0,1,2,3,4,8,11,14};   // y0-y4 + y5-y7
static const int64_t I1Z[8] = {2,5,8,11,14, 0,0,0};  // z0-z4
static const int64_t I2Z[8] = {0,1,2,3,4,9,12,15};   // z0-z4 + z5-z7

static int
sa_f64_aos_avx512_v2_kernel(const double ubi[9], const double *gv, double tol,
                             double *drlv2, int *labels, int label, intptr_t ng)
{
    __m512d u00=_mm512_set1_pd(ubi[0]),u01=_mm512_set1_pd(ubi[1]),u02=_mm512_set1_pd(ubi[2]);
    __m512d u10=_mm512_set1_pd(ubi[3]),u11=_mm512_set1_pd(ubi[4]),u12=_mm512_set1_pd(ubi[5]);
    __m512d u20=_mm512_set1_pd(ubi[6]),u21=_mm512_set1_pd(ubi[7]),u22=_mm512_set1_pd(ubi[8]);
    __m512d tvec=_mm512_set1_pd(tol*tol);
    __m256i lbl_vec=_mm256_set1_epi32(label), neg=_mm256_set1_epi32(-1);
    __m512i idx1x=_mm512_loadu_si512(I1X), idx2x=_mm512_loadu_si512(I2X);
    __m512i idx1y=_mm512_loadu_si512(I1Y), idx2y=_mm512_loadu_si512(I2Y);
    __m512i idx1z=_mm512_loadu_si512(I1Z), idx2z=_mm512_loadu_si512(I2Z);
    int n=0; intptr_t k;

    for(k=0;k+8<=ng;k+=8){
        /* Wide loads: 24 doubles in 3 vectors */
        __m512d d0=_mm512_loadu_pd(&gv[k*3]);
        __m512d d1=_mm512_loadu_pd(&gv[k*3+8]);
        __m512d d2=_mm512_loadu_pd(&gv[k*3+16]);

        /* Deinterleave: extract gvx, gvy, gvz via two rounds of permute */
        __m512d tmp_x=_mm512_permutex2var_pd(d0, idx1x, d1);
        __m512d gvx  =_mm512_permutex2var_pd(tmp_x, idx2x, d2);

        __m512d tmp_y=_mm512_permutex2var_pd(d0, idx1y, d1);
        __m512d gvy  =_mm512_permutex2var_pd(tmp_y, idx2y, d2);

        __m512d tmp_z=_mm512_permutex2var_pd(d0, idx1z, d1);
        __m512d gvz  =_mm512_permutex2var_pd(tmp_z, idx2z, d2);

        __m512d hx=_mm512_fmadd_pd(u00,gvx,_mm512_fmadd_pd(u01,gvy,_mm512_mul_pd(u02,gvz)));
        __m512d hy=_mm512_fmadd_pd(u10,gvx,_mm512_fmadd_pd(u11,gvy,_mm512_mul_pd(u12,gvz)));
        __m512d hz=_mm512_fmadd_pd(u20,gvx,_mm512_fmadd_pd(u21,gvy,_mm512_mul_pd(u22,gvz)));

        __m512d ihx=_mm512_roundscale_pd(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hx=_mm512_sub_pd(hx,ihx);
        __m512d ihy=_mm512_roundscale_pd(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hy=_mm512_sub_pd(hy,ihy);
        __m512d ihz=_mm512_roundscale_pd(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hz=_mm512_sub_pd(hz,ihz);
        __m512d sumsq=_mm512_fmadd_pd(hx,hx,_mm512_fmadd_pd(hy,hy,_mm512_mul_pd(hz,hz)));

        __m512d cur=_mm512_loadu_pd(&drlv2[k]);
        __mmask8 mask=_mm512_cmp_pd_mask(sumsq,tvec,_CMP_LT_OS);
        mask&=_mm512_cmp_pd_mask(sumsq,cur,_CMP_LT_OS);

        __m256i lbl=_mm256_loadu_si256((__m256i*)&labels[k]);
        __mmask8 eq=_mm256_cmpeq_epi32_mask(lbl,lbl_vec);
        __mmask8 clr=_kandn_mask8(mask,eq);
        lbl=_mm256_mask_mov_epi32(lbl,mask,lbl_vec);
        lbl=_mm256_mask_mov_epi32(lbl,clr,neg);
        _mm256_storeu_si256((__m256i*)&labels[k],lbl);

        if(mask){
            n+=popcnt32((unsigned)mask);
            _mm512_storeu_pd(&drlv2[k],_mm512_mask_blend_pd(mask,cur,sumsq));
        }
    }

    double tol2=tol*tol;
    for(;k<ng;k++){
        double gx=gv[k*3],gy=gv[k*3+1],gz=gv[k*3+2];
        double hx_=ubi[0]*gx+ubi[1]*gy+ubi[2]*gz; double ix=nearbyint(hx_);
        double hy_=ubi[3]*gx+ubi[4]*gy+ubi[5]*gz; double iy=nearbyint(hy_);
        double hz_=ubi[6]*gx+ubi[7]*gy+ubi[8]*gz; double iz=nearbyint(hz_);
        double s=(hx_-ix)*(hx_-ix)+(hy_-iy)*(hy_-iy)+(hz_-iz)*(hz_-iz);
        if(s<tol2&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

int score_and_assign_f64_avx512_v2(double ubi[3][3], const double gv[], double tol,
                                    double *drlv2, int *labels, int label, intptr_t ng)
{
    int n=0;
#ifdef _OPENMP
    int nthr=omp_get_max_threads();
    if(ng>10000&&nthr>1){
        #pragma omp parallel reduction(+:n)
        { int tid=omp_get_thread_num(); intptr_t chunk=(ng+nthr-1)/nthr,start=tid*chunk;
          intptr_t end=(start+chunk<ng)?start+chunk:ng;
          if(start<ng)n=sa_f64_aos_avx512_v2_kernel((const double*)ubi,gv+start*3,tol,drlv2+start,labels+start,label,end-start);}
        return n;}
#endif
    return sa_f64_aos_avx512_v2_kernel((const double*)ubi,gv,tol,drlv2,labels,label,ng);
}
