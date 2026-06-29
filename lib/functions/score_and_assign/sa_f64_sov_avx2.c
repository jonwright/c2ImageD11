/* sa_f64_sov_avx2.c -- f64 SoA AVX2 intrinsics for score_and_assign()
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx2",
 *         "sig": "int score_and_assign_f64_sov_avx2(double ubi[3][3], const double gv[], double tol, double *drlv2, int *labels, int label, intptr_t ng) -> int",
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
sa_f64_sov_avx2_kernel(const double ubi[9], const double *gvx, const double *gvy,
                        const double *gvz, double tol, double *drlv2, int *labels,
                        int label, intptr_t ng)
{
    __m256d u00=_mm256_set1_pd(ubi[0]),u01=_mm256_set1_pd(ubi[1]),u02=_mm256_set1_pd(ubi[2]);
    __m256d u10=_mm256_set1_pd(ubi[3]),u11=_mm256_set1_pd(ubi[4]),u12=_mm256_set1_pd(ubi[5]);
    __m256d u20=_mm256_set1_pd(ubi[6]),u21=_mm256_set1_pd(ubi[7]),u22=_mm256_set1_pd(ubi[8]);
    __m256d tvec=_mm256_set1_pd(tol*tol);
    
    int n=0; intptr_t k;

    for(k=0;k+4<=ng;k+=4){
        __m256d gx=_mm256_loadu_pd(&gvx[k]);
        __m256d gy=_mm256_loadu_pd(&gvy[k]);
        __m256d gz=_mm256_loadu_pd(&gvz[k]);

        __m256d hx=_mm256_fmadd_pd(u00,gx,_mm256_fmadd_pd(u01,gy,_mm256_mul_pd(u02,gz)));
        __m256d hy=_mm256_fmadd_pd(u10,gx,_mm256_fmadd_pd(u11,gy,_mm256_mul_pd(u12,gz)));
        __m256d hz=_mm256_fmadd_pd(u20,gx,_mm256_fmadd_pd(u21,gy,_mm256_mul_pd(u22,gz)));

        __m256d ihx=_mm256_round_pd(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hx=_mm256_sub_pd(hx,ihx);
        __m256d ihy=_mm256_round_pd(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hy=_mm256_sub_pd(hy,ihy);
        __m256d ihz=_mm256_round_pd(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC); hz=_mm256_sub_pd(hz,ihz);

        __m256d sumsq=_mm256_fmadd_pd(hx,hx,_mm256_fmadd_pd(hy,hy,_mm256_mul_pd(hz,hz)));

        __m256d cur=_mm256_loadu_pd(&drlv2[k]);
        __m256d mask1=_mm256_cmp_pd(sumsq,tvec,_CMP_LT_OS);
        mask1=_mm256_and_pd(mask1,_mm256_cmp_pd(sumsq,cur,_CMP_LT_OS));

        int mm=_mm256_movemask_pd(mask1);
        if(mm){
            n+=popcnt32(mm);
            _mm256_storeu_pd(&drlv2[k],_mm256_blendv_pd(cur,sumsq,mask1));
        }
        /* SIMD label update: load 4 int32, blend assign+clear */
        {
            __m128i lbl=_mm_loadu_si128((__m128i*)&labels[k]);
            __m128i lbl_vec=_mm_set1_epi32(label), neg=_mm_set1_epi32(-1);
            __m128i eq=_mm_cmpeq_epi32(lbl,lbl_vec);
            __m128i mw=_mm_set_epi32((mm&8)?-1:0,(mm&4)?-1:0,(mm&2)?-1:0,(mm&1)?-1:0);
            __m128i clr=_mm_andnot_si128(mw,eq);
            lbl=_mm_blendv_epi8(lbl,lbl_vec,mw);
            lbl=_mm_blendv_epi8(lbl,neg,clr);
            _mm_storeu_si128((__m128i*)&labels[k],lbl);
        }
    }

    double tol2=tol*tol;
    for(;k<ng;k++){
        double hx_=ubi[0]*gvx[k]+ubi[1]*gvy[k]+ubi[2]*gvz[k];hx_-=nearbyint(hx_);
        double hy_=ubi[3]*gvx[k]+ubi[4]*gvy[k]+ubi[5]*gvz[k];hy_-=nearbyint(hy_);
        double hz_=ubi[6]*gvx[k]+ubi[7]*gvy[k]+ubi[8]*gvz[k];hz_-=nearbyint(hz_);
        double s=hx_*hx_+hy_*hy_+hz_*hz_;
        if(s<tol2&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

int score_and_assign_f64_sov_avx2(double ubi[3][3], const double gv[], double tol,
                                   double *drlv2, int *labels, int label, intptr_t ng)
{
    const double *gvx=gv,*gvy=gv+ng,*gvz=gv+ng*2;
    int n=0;
#ifdef _OPENMP
    int nthr=omp_get_max_threads();
    if(ng>10000&&nthr>1){
        #pragma omp parallel reduction(+:n)
        { int tid=omp_get_thread_num(); intptr_t chunk=(ng+nthr-1)/nthr,start=tid*chunk;
          intptr_t end=(start+chunk<ng)?start+chunk:ng;
          if(start<ng)n=sa_f64_sov_avx2_kernel((const double*)ubi,gvx+start,gvy+start,gvz+start,tol,drlv2+start,labels+start,label,end-start);}
        return n;}
#endif
    return sa_f64_sov_avx2_kernel((const double*)ubi,gvx,gvy,gvz,tol,drlv2,labels,label,ng);
}
