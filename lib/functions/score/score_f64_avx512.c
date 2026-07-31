/* score_f64_avx512.c -- f64 AoS AVX-512 intrinsics for score()
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_avx512f",
 *         "sig": "int score_f64_avx512(const double ubi[3][3], const double gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "../score_and_refine/sar_popcnt.h"
#include <stdint.h>
#include "../common/omp_dispatch.h"
#include "../common/score_tail.h"

static int
score_f64_avx512_kernel(const double ubi[9], const double *gv, double tol, intptr_t ng)
{
    __m512d u00=_mm512_set1_pd(ubi[0]),u01=_mm512_set1_pd(ubi[1]),u02=_mm512_set1_pd(ubi[2]);
    __m512d u10=_mm512_set1_pd(ubi[3]),u11=_mm512_set1_pd(ubi[4]),u12=_mm512_set1_pd(ubi[5]);
    __m512d u20=_mm512_set1_pd(ubi[6]),u21=_mm512_set1_pd(ubi[7]),u22=_mm512_set1_pd(ubi[8]);
    __m512d tvec=_mm512_set1_pd(tol*tol);
    int n=0; intptr_t k;
    for(k=0;k+8<=ng;k+=8){
        __m512d gvx=_mm512_set_pd(gv[k*3+21],gv[k*3+18],gv[k*3+15],gv[k*3+12],gv[k*3+9],gv[k*3+6],gv[k*3+3],gv[k*3+0]);
        __m512d gvy=_mm512_set_pd(gv[k*3+22],gv[k*3+19],gv[k*3+16],gv[k*3+13],gv[k*3+10],gv[k*3+7],gv[k*3+4],gv[k*3+1]);
        __m512d gvz=_mm512_set_pd(gv[k*3+23],gv[k*3+20],gv[k*3+17],gv[k*3+14],gv[k*3+11],gv[k*3+8],gv[k*3+5],gv[k*3+2]);
        __m512d hx=_mm512_fmadd_pd(u00,gvx,_mm512_fmadd_pd(u01,gvy,_mm512_mul_pd(u02,gvz)));
        __m512d hy=_mm512_fmadd_pd(u10,gvx,_mm512_fmadd_pd(u11,gvy,_mm512_mul_pd(u12,gvz)));
        __m512d hz=_mm512_fmadd_pd(u20,gvx,_mm512_fmadd_pd(u21,gvy,_mm512_mul_pd(u22,gvz)));
        __m512d ihx=_mm512_roundscale_pd(hx,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512d ihy=_mm512_roundscale_pd(hy,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512d ihz=_mm512_roundscale_pd(hz,_MM_FROUND_TO_NEAREST_INT|_MM_FROUND_NO_EXC);
        __m512d tx=_mm512_sub_pd(hx,ihx),ty=_mm512_sub_pd(hy,ihy),tz=_mm512_sub_pd(hz,ihz);
        __m512d sumsq=_mm512_fmadd_pd(tx,tx,_mm512_fmadd_pd(ty,ty,_mm512_mul_pd(tz,tz)));
        __mmask8 mask=_mm512_cmp_pd_mask(sumsq,tvec,_CMP_LT_OS);
        if(mask)n+=popcnt32((unsigned)mask);
    }
    return n + score_tail_aos_f64(ubi, gv + k*3, tol, ng - k);
}

int score_f64_avx512(const double ubi[3][3], const double gv[], double tol, intptr_t ng)
{
    int n;
    OMP_DISPATCH_INT_AOS(score_f64_avx512_kernel, (const double *)ubi, gv, sizeof(double), ng, tol, n);
    return n;
}
