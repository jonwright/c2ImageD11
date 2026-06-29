/* sar_f32_aos_avx2.c -- f32 AoS AVX2 intrinsics variant
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[1] == 3 and gv.slow_axis == 0 and c2py_amd64_avx2",
 *         "sig": "void score_and_refine_f32_avx2(double ubi[3][3], const float gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "sar_popcnt.h"
#include <stdint.h>
#include "sar_omp.h"
#include <math.h>

static float hsum8(__m256 v) {
    __m128 lo = _mm256_castps256_ps128(v), hi = _mm256_extractf128_ps(v, 1);
    lo = _mm_add_ps(lo, hi); lo = _mm_hadd_ps(lo, lo);
    lo = _mm_hadd_ps(lo, lo); return _mm_cvtss_f32(lo);
}

extern int inverse3x3(double A[3][3]);

static void
sar_f32_aos_avx2_kernel(const double ubi[9], const float *__restrict gv,
    double tol, intptr_t ng, double *__restrict H, double *__restrict R,
    int *__restrict n_out, double *__restrict sumdrlv2_out)
{
    __m256 u00 = _mm256_set1_ps((float)ubi[0]), u01 = _mm256_set1_ps((float)ubi[1]),
            u02 = _mm256_set1_ps((float)ubi[2]);
    __m256 u10 = _mm256_set1_ps((float)ubi[3]), u11 = _mm256_set1_ps((float)ubi[4]),
            u12 = _mm256_set1_ps((float)ubi[5]);
    __m256 u20 = _mm256_set1_ps((float)ubi[6]), u21 = _mm256_set1_ps((float)ubi[7]),
            u22 = _mm256_set1_ps((float)ubi[8]);
    float t2 = (float)(tol * tol);
    __m256 tvec = _mm256_set1_ps(t2);

    __m256 H00 = _mm256_setzero_ps(), H01 = _mm256_setzero_ps(),
            H02 = _mm256_setzero_ps(), H10 = _mm256_setzero_ps(),
            H11 = _mm256_setzero_ps(), H12 = _mm256_setzero_ps(),
            H20 = _mm256_setzero_ps(), H21 = _mm256_setzero_ps(),
            H22 = _mm256_setzero_ps();
    __m256 R00 = _mm256_setzero_ps(), R01 = _mm256_setzero_ps(),
            R02 = _mm256_setzero_ps(), R10 = _mm256_setzero_ps(),
            R11 = _mm256_setzero_ps(), R12 = _mm256_setzero_ps(),
            R20 = _mm256_setzero_ps(), R21 = _mm256_setzero_ps(),
            R22 = _mm256_setzero_ps();
    __m256 s_vec = _mm256_setzero_ps();
    int n_scalar = 0;

    intptr_t k;
    for (k = 0; k + 8 <= ng; k += 8) {
        /* AoS layout for floats: 8 g-vectors = 24 floats = 3 ymm loads */
        /* AoS: scalar-gather loads below */
        /* Actually f32 AoS shuffle is complex.  Do 2 g-vectors per xmm,
         * then 4 per ymm.  Let me use scalar gather approach. */
        /* For f32 AoS, the safe cross-platform approach: scalar loads */
        __m256 gvx = _mm256_set_ps(
            gv[k*3+21], gv[k*3+18], gv[k*3+15], gv[k*3+12],
            gv[k*3+9],  gv[k*3+6],  gv[k*3+3],  gv[k*3+0]);
        __m256 gvy = _mm256_set_ps(
            gv[k*3+22], gv[k*3+19], gv[k*3+16], gv[k*3+13],
            gv[k*3+10], gv[k*3+7],  gv[k*3+4],  gv[k*3+1]);
        __m256 gvz = _mm256_set_ps(
            gv[k*3+23], gv[k*3+20], gv[k*3+17], gv[k*3+14],
            gv[k*3+11], gv[k*3+8],  gv[k*3+5],  gv[k*3+2]);

        __m256 hx = _mm256_fmadd_ps(u00, gvx,
                    _mm256_fmadd_ps(u01, gvy, _mm256_mul_ps(u02, gvz)));
        __m256 hy = _mm256_fmadd_ps(u10, gvx,
                    _mm256_fmadd_ps(u11, gvy, _mm256_mul_ps(u12, gvz)));
        __m256 hz = _mm256_fmadd_ps(u20, gvx,
                    _mm256_fmadd_ps(u21, gvy, _mm256_mul_ps(u22, gvz)));

        __m256 ihx = _mm256_round_ps(hx, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m256 ihy = _mm256_round_ps(hy, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m256 ihz = _mm256_round_ps(hz, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);

        __m256 tx = _mm256_sub_ps(hx, ihx);
        __m256 ty = _mm256_sub_ps(hy, ihy);
        __m256 tz = _mm256_sub_ps(hz, ihz);

        __m256 sumsq = _mm256_fmadd_ps(tx, tx,
                       _mm256_fmadd_ps(ty, ty, _mm256_mul_ps(tz, tz)));
        __m256 mask = _mm256_cmp_ps(sumsq, tvec, _CMP_LT_OS);
        int mm = _mm256_movemask_ps(mask);
        if (mm == 0) continue;

        n_scalar += popcnt32(mm);
        s_vec = _mm256_add_ps(s_vec, _mm256_and_ps(sumsq, mask));

#define MA(a, v) a = _mm256_add_ps(a, _mm256_and_ps(v, mask))
        MA(H00, _mm256_mul_ps(ihx, ihx));
        MA(H01, _mm256_mul_ps(ihx, ihy));
        MA(H02, _mm256_mul_ps(ihx, ihz));
        MA(H10, _mm256_mul_ps(ihy, ihx));
        MA(H11, _mm256_mul_ps(ihy, ihy));
        MA(H12, _mm256_mul_ps(ihy, ihz));
        MA(H20, _mm256_mul_ps(ihz, ihx));
        MA(H21, _mm256_mul_ps(ihz, ihy));
        MA(H22, _mm256_mul_ps(ihz, ihz));

        MA(R00, _mm256_mul_ps(ihx, gvx));
        MA(R01, _mm256_mul_ps(ihy, gvx));
        MA(R02, _mm256_mul_ps(ihz, gvx));
        MA(R10, _mm256_mul_ps(ihx, gvy));
        MA(R11, _mm256_mul_ps(ihy, gvy));
        MA(R12, _mm256_mul_ps(ihz, gvy));
        MA(R20, _mm256_mul_ps(ihx, gvz));
        MA(R21, _mm256_mul_ps(ihy, gvz));
        MA(R22, _mm256_mul_ps(ihz, gvz));
#undef MA
    }

    H[0] = hsum8(H00); H[1] = hsum8(H01); H[2] = hsum8(H02);
    H[3] = hsum8(H10); H[4] = hsum8(H11); H[5] = hsum8(H12);
    H[6] = hsum8(H20); H[7] = hsum8(H21); H[8] = hsum8(H22);
    R[0] = hsum8(R00); R[1] = hsum8(R01); R[2] = hsum8(R02);
    R[3] = hsum8(R10); R[4] = hsum8(R11); R[5] = hsum8(R12);
    R[6] = hsum8(R20); R[7] = hsum8(R21); R[8] = hsum8(R22);
    *n_out = n_scalar;
    *sumdrlv2_out = (double)hsum8(s_vec);

    double tol2 = tol * tol;
    for (; k < ng; k++) {
        double gx = gv[k*3], gy = gv[k*3+1], gz = gv[k*3+2];
        double hx_ = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        double hy_ = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        double hz_ = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        double ix = nearbyint(hx_);
        double iy = nearbyint(hy_);
        double iz = nearbyint(hz_);
        double tx_ = hx_ - ix, ty_ = hy_ - iy, tz_ = hz_ - iz;
        double s = tx_*tx_ + ty_*ty_ + tz_*tz_;
        if (s < tol2) {
            (*n_out)++;
            *sumdrlv2_out += s;
            H[0] += ix*ix; H[1] += ix*iy; H[2] += ix*iz;
            H[3] += iy*ix; H[4] += iy*iy; H[5] += iy*iz;
            H[6] += iz*ix; H[7] += iz*iy; H[8] += iz*iz;
            R[0] += ix*gx; R[1] += iy*gx; R[2] += iz*gx;
            R[3] += ix*gy; R[4] += iy*gy; R[5] += iz*gy;
            R[6] += ix*gz; R[7] += iy*gz; R[8] += iz*gz;
        }
    }
}

void score_and_refine_f32_avx2(
    double ubi[3][3], const float gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    double H[3][3] = {{0}}, R[3][3] = {{0}}, UB[3][3] = {{0}};
    int n; double sumdrlv2;
        SAR_OMP_DISPATCH_AOS(sar_f32_aos_avx2_kernel, (const double *)ubi, gv, sizeof(float), ng, tol, H, R, &n, &sumdrlv2);
    if (n > 0) sumdrlv2 /= n;
    if (inverse3x3(H) == 0) {
        int i, j, l;
        for (i = 0; i < 3; i++) for (j = 0; j < 3; j++) for (l = 0; l < 3; l++)
            UB[i][j] += R[i][l] * H[l][j];
    }
    if (inverse3x3(UB) == 0) {
        int i, j;
        for (i = 0; i < 3; i++) for (j = 0; j < 3; j++)
            ubi[i][j] = UB[i][j];
    }
    *n_arg = n; *sumdrlv2_arg = sumdrlv2;
}
