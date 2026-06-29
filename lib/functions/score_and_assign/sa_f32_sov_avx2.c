/* sa_f32_sov_avx2.c -- f32 SoA AVX2 intrinsics for score_and_assign()
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx2",
 *         "sig": "int score_and_assign_f32_sov_avx2(double ubi[3][3], const float gv[], double tol, float *drlv2, int *labels, int label, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "drlv2": "drlv2.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[1]"},
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

static int
sa_f32_sov_avx2_kernel(const double ubi[9], const float *gvx, const float *gvy,
                        const float *gvz, double tol, float *drlv2, int *labels,
                        int label, intptr_t ng)
{
    __m256 u00=_mm256_set1_ps((float)ubi[0]),u01=_mm256_set1_ps((float)ubi[1]),u02=_mm256_set1_ps((float)ubi[2]);
    __m256 u10=_mm256_set1_ps((float)ubi[3]),u11=_mm256_set1_ps((float)ubi[4]),u12=_mm256_set1_ps((float)ubi[5]);
    __m256 u20=_mm256_set1_ps((float)ubi[6]),u21=_mm256_set1_ps((float)ubi[7]),u22=_mm256_set1_ps((float)ubi[8]);
    float tol2=(float)(tol*tol); __m256 tvec=_mm256_set1_ps(tol2);
    
    int n=0; intptr_t k;

    for(k=0;k+8<=ng;k+=8){
        __m256 gx=_mm256_loadu_ps(&gvx[k]);
        __m256 gy=_mm256_loadu_ps(&gvy[k]);
        __m256 gz=_mm256_loadu_ps(&gvz[k]);

        __m256 hx=_mm256_fmadd_ps(u00,gx,_mm256_fmadd_ps(u01,gy,_mm256_mul_ps(u02,gz)));
        __m256 hy=_mm256_fmadd_ps(u10,gx,_mm256_fmadd_ps(u11,gy,_mm256_mul_ps(u12,gz)));
        __m256 hz=_mm256_fmadd_ps(u20,gx,_mm256_fmadd_ps(u21,gy,_mm256_mul_ps(u22,gz)));

        __m256 ihx=_mm256_round_ps(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hx=_mm256_sub_ps(hx,ihx);
        __m256 ihy=_mm256_round_ps(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hy=_mm256_sub_ps(hy,ihy);
        __m256 ihz=_mm256_round_ps(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hz=_mm256_sub_ps(hz,ihz);

        __m256 sumsq=_mm256_fmadd_ps(hx,hx,_mm256_fmadd_ps(hy,hy,_mm256_mul_ps(hz,hz)));

        __m256 cur=_mm256_loadu_ps(&drlv2[k]);
        __m256 mask1=_mm256_cmp_ps(sumsq,tvec,_CMP_LT_OS);
        mask1=_mm256_and_ps(mask1,_mm256_cmp_ps(sumsq,cur,_CMP_LT_OS));

        int mm=_mm256_movemask_ps(mask1);
        if(mm){
            n+=popcnt32(mm);
            _mm256_storeu_ps(&drlv2[k],_mm256_blendv_ps(cur,sumsq,mask1));
        }
        {
            __m256i lbl=_mm256_loadu_si256((__m256i*)&labels[k]);
            __m256i lbl_vec=_mm256_set1_epi32(label), neg=_mm256_set1_epi32(-1);
            __m256i eq=_mm256_cmpeq_epi32(lbl,lbl_vec);
            __m256i mw=_mm256_set_epi32((mm&128)?-1:0,(mm&64)?-1:0,(mm&32)?-1:0,(mm&16)?-1:0,
                                       (mm&8)?-1:0,(mm&4)?-1:0,(mm&2)?-1:0,(mm&1)?-1:0);
            __m256i clr=_mm256_andnot_si256(mw,eq);
            lbl=_mm256_blendv_epi8(lbl,lbl_vec,mw);
            lbl=_mm256_blendv_epi8(lbl,neg,clr);
            _mm256_storeu_si256((__m256i*)&labels[k],lbl);
        }
    }

    for(;k<ng;k++){
        float hx_=(float)ubi[0]*gvx[k]+(float)ubi[1]*gvy[k]+(float)ubi[2]*gvz[k];hx_-=nearbyintf(hx_);
        float hy_=(float)ubi[3]*gvx[k]+(float)ubi[4]*gvy[k]+(float)ubi[5]*gvz[k];hy_-=nearbyintf(hy_);
        float hz_=(float)ubi[6]*gvx[k]+(float)ubi[7]*gvy[k]+(float)ubi[8]*gvz[k];hz_-=nearbyintf(hz_);
        float s=hx_*hx_+hy_*hy_+hz_*hz_;
        if(s<tol2&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

int score_and_assign_f32_sov_avx2(double ubi[3][3], const float gv[], double tol,
                                   float *drlv2, int *labels, int label, intptr_t ng)
{
    const float *gvx=gv,*gvy=gv+ng,*gvz=gv+ng*2;
    int n=0;
#ifdef _OPENMP
    int nthr=omp_get_max_threads();
    if(ng>10000&&nthr>1){
        #pragma omp parallel reduction(+:n)
        { int tid=omp_get_thread_num(); intptr_t chunk=(ng+nthr-1)/nthr,start=tid*chunk;
          intptr_t end=(start+chunk<ng)?start+chunk:ng;
          if(start<ng)n=sa_f32_sov_avx2_kernel((const double*)ubi,gvx+start,gvy+start,gvz+start,tol,drlv2+start,labels+start,label,end-start);}
        return n;}
#endif
    return sa_f32_sov_avx2_kernel((const double*)ubi,gvx,gvy,gvz,tol,drlv2,labels,label,ng);
}
