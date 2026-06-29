/* sa_f64_sov_avx512.c -- f64 SoA AVX-512 intrinsics for score_and_assign()
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx512f",
 *         "sig": "int score_and_assign_f64_sov_avx512(double ubi[3][3], const double gv[], double tol, double *drlv2, int *labels, int label, intptr_t ng) -> int",
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
sa_f64_sov_avx512_kernel(const double ubi[9], const double *gvx, const double *gvy,
                          const double *gvz, double tol, double *drlv2, int *labels,
                          int label, intptr_t ng)
{
    __m512d u00=_mm512_set1_pd(ubi[0]),u01=_mm512_set1_pd(ubi[1]),u02=_mm512_set1_pd(ubi[2]);
    __m512d u10=_mm512_set1_pd(ubi[3]),u11=_mm512_set1_pd(ubi[4]),u12=_mm512_set1_pd(ubi[5]);
    __m512d u20=_mm512_set1_pd(ubi[6]),u21=_mm512_set1_pd(ubi[7]),u22=_mm512_set1_pd(ubi[8]);
    __m512d tvec=_mm512_set1_pd(tol*tol);
    __m256i lbl_vec=_mm256_set1_epi32(label), neg=_mm256_set1_epi32(-1);
    int n=0; intptr_t k;

    for(k=0;k+8<=ng;k+=8){
        __m512d gx=_mm512_loadu_pd(&gvx[k]);
        __m512d gy=_mm512_loadu_pd(&gvy[k]);
        __m512d gz=_mm512_loadu_pd(&gvz[k]);

        __m512d hx=_mm512_fmadd_pd(u00,gx,_mm512_fmadd_pd(u01,gy,_mm512_mul_pd(u02,gz)));
        __m512d hy=_mm512_fmadd_pd(u10,gx,_mm512_fmadd_pd(u11,gy,_mm512_mul_pd(u12,gz)));
        __m512d hz=_mm512_fmadd_pd(u20,gx,_mm512_fmadd_pd(u21,gy,_mm512_mul_pd(u22,gz)));

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
        double hx_=ubi[0]*gvx[k]+ubi[1]*gvy[k]+ubi[2]*gvz[k]; double ix=nearbyint(hx_);
        double hy_=ubi[3]*gvx[k]+ubi[4]*gvy[k]+ubi[5]*gvz[k]; double iy=nearbyint(hy_);
        double hz_=ubi[6]*gvx[k]+ubi[7]*gvy[k]+ubi[8]*gvz[k]; double iz=nearbyint(hz_);
        double s=(hx_-ix)*(hx_-ix)+(hy_-iy)*(hy_-iy)+(hz_-iz)*(hz_-iz);
        if(s<tol2&&s<drlv2[k]){labels[k]=label;drlv2[k]=s;n++;}
        else if(labels[k]==label)labels[k]=-1;
    }
    return n;
}

int score_and_assign_f64_sov_avx512(double ubi[3][3], const double gv[], double tol,
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
          if(start<ng)n=sa_f64_sov_avx512_kernel((const double*)ubi,gvx+start,gvy+start,gvz+start,tol,drlv2+start,labels+start,label,end-start);}
        return n;}
#endif
    return sa_f64_sov_avx512_kernel((const double*)ubi,gvx,gvy,gvz,tol,drlv2,labels,label,ng);
}
