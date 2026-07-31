#include <immintrin.h>
#include "../score_and_refine/sar_popcnt.h"
#include <stdint.h>
#include "../common/omp_dispatch.h"
#include "../common/score_tail.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx512f",
 *         "sig": "int score_f64_soa_avx512(const double ubi[3][3], const double gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
 *     }],
 * }
 * C2PY_END
 */

static int score_f64_soa_avx512_kernel(const double ubi[9],
    const double *gvx, const double *gvy, const double *gvz, double tol, intptr_t ng)
{
    __m512d u00=_mm512_set1_pd(ubi[0]),u01=_mm512_set1_pd(ubi[1]),u02=_mm512_set1_pd(ubi[2]);
    __m512d u10=_mm512_set1_pd(ubi[3]),u11=_mm512_set1_pd(ubi[4]),u12=_mm512_set1_pd(ubi[5]);
    __m512d u20=_mm512_set1_pd(ubi[6]),u21=_mm512_set1_pd(ubi[7]),u22=_mm512_set1_pd(ubi[8]);
    __m512d tvec=_mm512_set1_pd(tol*tol); int n=0; intptr_t k;
    for(k=0;k+8<=ng;k+=8){
        __m512d gvx_v=_mm512_loadu_pd(&gvx[k]),gvy_v=_mm512_loadu_pd(&gvy[k]),gvz_v=_mm512_loadu_pd(&gvz[k]);
        __m512d hx=_mm512_fmadd_pd(u00,gvx_v,_mm512_fmadd_pd(u01,gvy_v,_mm512_mul_pd(u02,gvz_v)));
        __m512d hy=_mm512_fmadd_pd(u10,gvx_v,_mm512_fmadd_pd(u11,gvy_v,_mm512_mul_pd(u12,gvz_v)));
        __m512d hz=_mm512_fmadd_pd(u20,gvx_v,_mm512_fmadd_pd(u21,gvy_v,_mm512_mul_pd(u22,gvz_v)));
        __m512d ihx=_mm512_roundscale_pd(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512d ihy=_mm512_roundscale_pd(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512d ihz=_mm512_roundscale_pd(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512d tx=_mm512_sub_pd(hx,ihx),ty=_mm512_sub_pd(hy,ihy),tz=_mm512_sub_pd(hz,ihz);
        __m512d sumsq=_mm512_fmadd_pd(tx,tx,_mm512_fmadd_pd(ty,ty,_mm512_mul_pd(tz,tz)));
        __mmask8 mask=_mm512_cmp_pd_mask(sumsq,tvec,_CMP_LT_OS);
        if(mask)n+=popcnt32((unsigned)mask);
    }
    return n + score_tail_soa_f64(ubi, gvx + k, gvy + k, gvz + k, tol, ng - k);
}

int score_f64_soa_avx512(const double ubi[3][3], const double gv[], double tol, intptr_t ng)
{
    int n;
    OMP_DISPATCH_INT_SOA(score_f64_soa_avx512_kernel, (const double *)ubi, gv, gv + ng, gv + 2*ng, sizeof(double), ng, tol, n);
    return n;
}
