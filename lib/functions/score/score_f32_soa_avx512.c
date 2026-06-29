#include <immintrin.h>
#include "../score_and_refine/sar_popcnt.h"
#include <stdint.h>
#ifdef _OPENMP
#include <omp.h>
#include <math.h>
#endif

/* C2PY_BEGIN
 * {
 *     "py_sig": "score(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx512f",
 *         "sig": "int score_f32_soa_avx512(const double ubi[3][3], const float gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
 *     }],
 * }
 * C2PY_END
 */

static int score_f32_soa_avx512_kernel(const double ubi[9],
    const float *gvx, const float *gvy, const float *gvz, double tol, intptr_t ng)
{
    __m512 u00=_mm512_set1_ps((float)ubi[0]),u01=_mm512_set1_ps((float)ubi[1]),u02=_mm512_set1_ps((float)ubi[2]);
    __m512 u10=_mm512_set1_ps((float)ubi[3]),u11=_mm512_set1_ps((float)ubi[4]),u12=_mm512_set1_ps((float)ubi[5]);
    __m512 u20=_mm512_set1_ps((float)ubi[6]),u21=_mm512_set1_ps((float)ubi[7]),u22=_mm512_set1_ps((float)ubi[8]);
    float t2=(float)(tol*tol); __m512 tvec=_mm512_set1_ps(t2); int n=0; intptr_t k;
    for(k=0;k+16<=ng;k+=16){
        __m512 gvx_v=_mm512_loadu_ps(&gvx[k]),gvy_v=_mm512_loadu_ps(&gvy[k]),gvz_v=_mm512_loadu_ps(&gvz[k]);
        __m512 hx=_mm512_fmadd_ps(u00,gvx_v,_mm512_fmadd_ps(u01,gvy_v,_mm512_mul_ps(u02,gvz_v)));
        __m512 hy=_mm512_fmadd_ps(u10,gvx_v,_mm512_fmadd_ps(u11,gvy_v,_mm512_mul_ps(u12,gvz_v)));
        __m512 hz=_mm512_fmadd_ps(u20,gvx_v,_mm512_fmadd_ps(u21,gvy_v,_mm512_mul_ps(u22,gvz_v)));
        __m512 ihx=_mm512_roundscale_ps(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512 ihy=_mm512_roundscale_ps(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512 ihz=_mm512_roundscale_ps(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512 tx=_mm512_sub_ps(hx,ihx),ty=_mm512_sub_ps(hy,ihy),tz=_mm512_sub_ps(hz,ihz);
        __m512 sumsq=_mm512_fmadd_ps(tx,tx,_mm512_fmadd_ps(ty,ty,_mm512_mul_ps(tz,tz)));
        __mmask16 mask=_mm512_cmp_ps_mask(sumsq,tvec,_CMP_LT_OS);
        if(mask)n+=popcnt32((unsigned)mask);
    }
    double tol2=tol*tol;
    for(;k<ng;k++){double gx=gvx[k],gy=gvy[k],gz=gvz[k];
        double hx_=ubi[0]*gx+ubi[1]*gy+ubi[2]*gz;hx_-=nearbyint(hx_);
        double hy_=ubi[3]*gx+ubi[4]*gy+ubi[5]*gz;hy_-=nearbyint(hy_);
        double hz_=ubi[6]*gx+ubi[7]*gy+ubi[8]*gz;hz_-=nearbyint(hz_);
        if(hx_*hx_+hy_*hy_+hz_*hz_<tol2)n++;}
    return n;
}

int score_f32_soa_avx512(const double ubi[3][3], const float gv[], double tol, intptr_t ng)
{
    const float *gvx=gv,*gvy=gv+ng,*gvz=gv+2*ng; int n=0;
#ifdef _OPENMP
    int nthr=omp_get_max_threads();
    if(ng>10000&&nthr>1){
        #pragma omp parallel reduction(+:n)
        { int tid=omp_get_thread_num(); intptr_t chunk=(ng+nthr-1)/nthr,start=tid*chunk;
          intptr_t end=(start+chunk<ng)?start+chunk:ng;
          if(start<ng)n=score_f32_soa_avx512_kernel((const double*)ubi,gvx+start,gvy+start,gvz+start,tol,end-start);}
        return n;}
#endif
    return score_f32_soa_avx512_kernel((const double*)ubi,gvx,gvy,gvz,tol,ng);
}
