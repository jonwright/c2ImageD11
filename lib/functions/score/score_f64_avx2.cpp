/* score_f64_avx2.c -- f64 AoS AVX2 intrinsics for score()
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_avx2",
 *         "sig": "int score_f64_avx2(const double ubi[3][3], const double gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "../score_and_refine/sar_popcnt.h"
#include <stdint.h>
#include "../common/omp_dispatch.hpp"
#include "../common/score_tail.hpp"

static int
score_f64_avx2_kernel(const double ubi[9], const double *gv, double tol, intptr_t ng)
{
    __m256d u00 = _mm256_set1_pd(ubi[0]), u01 = _mm256_set1_pd(ubi[1]), u02 = _mm256_set1_pd(ubi[2]);
    __m256d u10 = _mm256_set1_pd(ubi[3]), u11 = _mm256_set1_pd(ubi[4]), u12 = _mm256_set1_pd(ubi[5]);
    __m256d u20 = _mm256_set1_pd(ubi[6]), u21 = _mm256_set1_pd(ubi[7]), u22 = _mm256_set1_pd(ubi[8]);
    __m256d tvec = _mm256_set1_pd(tol * tol);
    int n = 0;
    intptr_t k;

    for (k = 0; k + 4 <= ng; k += 4) {
        __m256d gvx = _mm256_set_pd(gv[k*3+9], gv[k*3+6], gv[k*3+3], gv[k*3+0]);
        __m256d gvy = _mm256_set_pd(gv[k*3+10], gv[k*3+7], gv[k*3+4], gv[k*3+1]);
        __m256d gvz = _mm256_set_pd(gv[k*3+11], gv[k*3+8], gv[k*3+5], gv[k*3+2]);

        __m256d hx = _mm256_fmadd_pd(u00, gvx, _mm256_fmadd_pd(u01, gvy, _mm256_mul_pd(u02, gvz)));
        __m256d hy = _mm256_fmadd_pd(u10, gvx, _mm256_fmadd_pd(u11, gvy, _mm256_mul_pd(u12, gvz)));
        __m256d hz = _mm256_fmadd_pd(u20, gvx, _mm256_fmadd_pd(u21, gvy, _mm256_mul_pd(u22, gvz)));

        __m256d ihx = _mm256_round_pd(hx, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m256d ihy = _mm256_round_pd(hy, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m256d ihz = _mm256_round_pd(hz, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);

        __m256d tx = _mm256_sub_pd(hx, ihx);
        __m256d ty = _mm256_sub_pd(hy, ihy);
        __m256d tz = _mm256_sub_pd(hz, ihz);

        __m256d sumsq = _mm256_fmadd_pd(tx, tx, _mm256_fmadd_pd(ty, ty, _mm256_mul_pd(tz, tz)));
        __m256d mask = _mm256_cmp_pd(sumsq, tvec, _CMP_LT_OS);
        int mm = _mm256_movemask_pd(mask);
        if (mm) n += popcnt32(mm);
    }

    return n + score_tail_aos(ubi, gv + k*3, tol, ng - k);
}

extern "C" int score_f64_avx2(const double ubi[3][3], const double gv[], double tol, intptr_t ng)
{
    return dispatch_score_aos(score_f64_avx2_kernel, (const double *)ubi, gv, ng, tol);
}
