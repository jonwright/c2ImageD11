/* sa_f64_aos_avx2.c -- f64 AoS AVX2 intrinsics for score_and_assign()
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_avx2",
 *         "sig": "int score_and_assign_f64_avx2(double ubi[3][3], const double gv[], double tol, double *drlv2, int *labels, int label, intptr_t ng) -> int",
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

static int
sa_f64_aos_avx2_kernel(const double ubi[9], const double *gv, double tol,
                        double *drlv2, int *labels, int label, intptr_t ng)
{
    __m256d u00=_mm256_set1_pd(ubi[0]),u01=_mm256_set1_pd(ubi[1]),u02=_mm256_set1_pd(ubi[2]);
    __m256d u10=_mm256_set1_pd(ubi[3]),u11=_mm256_set1_pd(ubi[4]),u12=_mm256_set1_pd(ubi[5]);
    __m256d u20=_mm256_set1_pd(ubi[6]),u21=_mm256_set1_pd(ubi[7]),u22=_mm256_set1_pd(ubi[8]);
    __m256d tvec=_mm256_set1_pd(tol*tol);
    int n=0; intptr_t k;

    for(k=0;k+4<=ng;k+=4){
        __m256d gvx=_mm256_set_pd(gv[k*3+9],gv[k*3+6],gv[k*3+3],gv[k*3+0]);
        __m256d gvy=_mm256_set_pd(gv[k*3+10],gv[k*3+7],gv[k*3+4],gv[k*3+1]);
        __m256d gvz=_mm256_set_pd(gv[k*3+11],gv[k*3+8],gv[k*3+5],gv[k*3+2]);

        __m256d hx=_mm256_fmadd_pd(u00,gvx,_mm256_fmadd_pd(u01,gvy,_mm256_mul_pd(u02,gvz)));
        __m256d hy=_mm256_fmadd_pd(u10,gvx,_mm256_fmadd_pd(u11,gvy,_mm256_mul_pd(u12,gvz)));
        __m256d hz=_mm256_fmadd_pd(u20,gvx,_mm256_fmadd_pd(u21,gvy,_mm256_mul_pd(u22,gvz)));

        __m256d ihx=_mm256_round_pd(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC), ihy=_mm256_round_pd(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC), ihz=_mm256_round_pd(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m256d tx=_mm256_sub_pd(hx,ihx),ty=_mm256_sub_pd(hy,ihy),tz=_mm256_sub_pd(hz,ihz);
        __m256d sumsq=_mm256_fmadd_pd(tx,tx,_mm256_fmadd_pd(ty,ty,_mm256_mul_pd(tz,tz)));

        __m256d cur=_mm256_loadu_pd(&drlv2[k]);
        __m256d mask1=_mm256_cmp_pd(sumsq,tvec,_CMP_LT_OS);
        mask1=_mm256_and_pd(mask1,_mm256_cmp_pd(sumsq,cur,_CMP_LT_OS));

        int mm=_mm256_movemask_pd(mask1);
        if(mm){
            n+=popcnt32(mm);
            _mm256_storeu_pd(&drlv2[k], _mm256_blendv_pd(cur, sumsq, mask1));
        }
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

int score_and_assign_f64_avx2(double ubi[3][3], const double gv[], double tol,
                               double *drlv2, int *labels, int label, intptr_t ng)
{
    int n=0;
#ifdef _OPENMP
    int nthr=omp_get_max_threads();
    if(ng>10000&&nthr>1){
        #pragma omp parallel reduction(+:n)
        { int tid=omp_get_thread_num(); intptr_t chunk=(ng+nthr-1)/nthr,start=tid*chunk;
          intptr_t end=(start+chunk<ng)?start+chunk:ng;
          if(start<ng)n=sa_f64_aos_avx2_kernel((const double*)ubi,gv+start*3,tol,drlv2+start,labels+start,label,end-start);}
        return n;}
#endif
    return sa_f64_aos_avx2_kernel((const double*)ubi,gv,tol,drlv2,labels,label,ng);
}
