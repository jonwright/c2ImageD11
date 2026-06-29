/* score_f32_avx2.c -- f32 AoS AVX2 intrinsics for score()
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_avx2",
 *         "sig": "int score_f32_avx2(const double ubi[3][3], const float gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "../score_and_refine/sar_popcnt.h"
#include <stdint.h>
#ifdef _OPENMP
#include <omp.h>
#include <math.h>
#endif

static int
score_f32_avx2_kernel(const double ubi[9], const float *gv, double tol, intptr_t ng)
{
    __m256 u00 = _mm256_set1_ps((float)ubi[0]), u01 = _mm256_set1_ps((float)ubi[1]), u02 = _mm256_set1_ps((float)ubi[2]);
    __m256 u10 = _mm256_set1_ps((float)ubi[3]), u11 = _mm256_set1_ps((float)ubi[4]), u12 = _mm256_set1_ps((float)ubi[5]);
    __m256 u20 = _mm256_set1_ps((float)ubi[6]), u21 = _mm256_set1_ps((float)ubi[7]), u22 = _mm256_set1_ps((float)ubi[8]);
    float t2 = (float)(tol * tol);
    __m256 tvec = _mm256_set1_ps(t2);
    int n = 0;
    intptr_t k;

    for (k = 0; k + 8 <= ng; k += 8) {
        __m256 gvx = _mm256_set_ps(gv[k*3+21], gv[k*3+18], gv[k*3+15], gv[k*3+12],
                                    gv[k*3+9], gv[k*3+6], gv[k*3+3], gv[k*3+0]);
        __m256 gvy = _mm256_set_ps(gv[k*3+22], gv[k*3+19], gv[k*3+16], gv[k*3+13],
                                    gv[k*3+10], gv[k*3+7], gv[k*3+4], gv[k*3+1]);
        __m256 gvz = _mm256_set_ps(gv[k*3+23], gv[k*3+20], gv[k*3+17], gv[k*3+14],
                                    gv[k*3+11], gv[k*3+8], gv[k*3+5], gv[k*3+2]);

        __m256 hx = _mm256_fmadd_ps(u00, gvx, _mm256_fmadd_ps(u01, gvy, _mm256_mul_ps(u02, gvz)));
        __m256 hy = _mm256_fmadd_ps(u10, gvx, _mm256_fmadd_ps(u11, gvy, _mm256_mul_ps(u12, gvz)));
        __m256 hz = _mm256_fmadd_ps(u20, gvx, _mm256_fmadd_ps(u21, gvy, _mm256_mul_ps(u22, gvz)));

        __m256 ihx = _mm256_round_ps(hx, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m256 ihy = _mm256_round_ps(hy, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m256 ihz = _mm256_round_ps(hz, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);

        __m256 tx = _mm256_sub_ps(hx, ihx);
        __m256 ty = _mm256_sub_ps(hy, ihy);
        __m256 tz = _mm256_sub_ps(hz, ihz);

        __m256 sumsq = _mm256_fmadd_ps(tx, tx, _mm256_fmadd_ps(ty, ty, _mm256_mul_ps(tz, tz)));
        __m256 mask = _mm256_cmp_ps(sumsq, tvec, _CMP_LT_OS);
        int mm = _mm256_movemask_ps(mask);
        if (mm) n += popcnt32(mm);
    }

    double tol2 = tol * tol;
    for (; k < ng; k++) {
        double gx = gv[k*3], gy = gv[k*3+1], gz = gv[k*3+2];
        double hx_ = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        hx_ -= nearbyint(hx_);
        double hy_ = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        hy_ -= nearbyint(hy_);
        double hz_ = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        hz_ -= nearbyint(hz_);
        if (hx_*hx_ + hy_*hy_ + hz_*hz_ < tol2) n++;
    }
    return n;
}

int score_f32_avx2(const double ubi[3][3], const float gv[], double tol, intptr_t ng)
{
    int n = 0;
#ifdef _OPENMP
    int nthr = omp_get_max_threads();
    if (ng > 10000 && nthr > 1) {
        #pragma omp parallel reduction(+:n)
        {
            int tid = omp_get_thread_num();
            intptr_t chunk = (ng + nthr - 1) / nthr;
            intptr_t start = tid * chunk;
            intptr_t end = (start + chunk < ng) ? start + chunk : ng;
            if (start < ng)
                n = score_f32_avx2_kernel((const double *)ubi, gv + start*3, tol, end - start);
        }
        return n;
    }
#endif
    return score_f32_avx2_kernel((const double *)ubi, gv, tol, ng);
}
