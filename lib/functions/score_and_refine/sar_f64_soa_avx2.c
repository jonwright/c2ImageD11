/* sar_f64_soa_avx2.c -- f64 SoA AVX2 intrinsics variant
 *
 * Replaces score_and_refine_f64_soa_avx2.cpp.
 * Single gv[] param — computes gvx/gvy/gvz offsets internally.
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx2",
 *         "sig": "void score_and_refine_f64_soa_avx2(double ubi[3][3], const double gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "sar_popcnt.h"
/* Horizontal sum: 4 doubles in ymm -> scalar */
static double hsum4(__m256d v) {
    __m128d lo = _mm256_castpd256_pd128(v);
    __m128d hi = _mm256_extractf128_pd(v, 1);
    lo = _mm_add_pd(lo, hi);
    lo = _mm_hadd_pd(lo, lo);
    return _mm_cvtsd_f64(lo);
}

#include <stdint.h>

extern int inverse3x3(double A[3][3]);

/* ── f64 SoA AVX2 kernel (4 doubles/ymm) ──────────────────────────── */
static void
sar_f64_soa_avx2_kernel(const double ubi[9],
                         const double *__restrict gvx, const double *__restrict gvy, const double *__restrict gvz,
                         double tol, intptr_t ng,
                         double *__restrict H, double *__restrict R,
                         int *__restrict n_out, double *__restrict sumdrlv2_out)
{
    __m256d u00 = _mm256_set1_pd(ubi[0]), u01 = _mm256_set1_pd(ubi[1]),
            u02 = _mm256_set1_pd(ubi[2]);
    __m256d u10 = _mm256_set1_pd(ubi[3]), u11 = _mm256_set1_pd(ubi[4]),
            u12 = _mm256_set1_pd(ubi[5]);
    __m256d u20 = _mm256_set1_pd(ubi[6]), u21 = _mm256_set1_pd(ubi[7]),
            u22 = _mm256_set1_pd(ubi[8]);
    __m256d tvec = _mm256_set1_pd(tol * tol);

    __m256d H00 = _mm256_setzero_pd(), H01 = _mm256_setzero_pd(),
            H02 = _mm256_setzero_pd(), H10 = _mm256_setzero_pd(),
            H11 = _mm256_setzero_pd(), H12 = _mm256_setzero_pd(),
            H20 = _mm256_setzero_pd(), H21 = _mm256_setzero_pd(),
            H22 = _mm256_setzero_pd();
    __m256d R00 = _mm256_setzero_pd(), R01 = _mm256_setzero_pd(),
            R02 = _mm256_setzero_pd(), R10 = _mm256_setzero_pd(),
            R11 = _mm256_setzero_pd(), R12 = _mm256_setzero_pd(),
            R20 = _mm256_setzero_pd(), R21 = _mm256_setzero_pd(),
            R22 = _mm256_setzero_pd();
    __m256d s_vec = _mm256_setzero_pd();
    int n_scalar = 0;

    intptr_t k;
    for (k = 0; k + 4 <= ng; k += 4) {
        __m256d gvx_v = _mm256_loadu_pd(&gvx[k]);
        __m256d gvy_v = _mm256_loadu_pd(&gvy[k]);
        __m256d gvz_v = _mm256_loadu_pd(&gvz[k]);

        __m256d hx = _mm256_fmadd_pd(u00, gvx_v,
                     _mm256_fmadd_pd(u01, gvy_v, _mm256_mul_pd(u02, gvz_v)));
        __m256d hy = _mm256_fmadd_pd(u10, gvx_v,
                     _mm256_fmadd_pd(u11, gvy_v, _mm256_mul_pd(u12, gvz_v)));
        __m256d hz = _mm256_fmadd_pd(u20, gvx_v,
                     _mm256_fmadd_pd(u21, gvy_v, _mm256_mul_pd(u22, gvz_v)));

        __m256d ihx = _mm256_round_pd(hx, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m256d ihy = _mm256_round_pd(hy, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m256d ihz = _mm256_round_pd(hz, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);

        __m256d tx = _mm256_sub_pd(hx, ihx);
        __m256d ty = _mm256_sub_pd(hy, ihy);
        __m256d tz = _mm256_sub_pd(hz, ihz);

        __m256d sumsq = _mm256_fmadd_pd(tx, tx,
                        _mm256_fmadd_pd(ty, ty, _mm256_mul_pd(tz, tz)));
        __m256d mask = _mm256_cmp_pd(sumsq, tvec, _CMP_LT_OS);
        int mm = _mm256_movemask_pd(mask);
        if (mm == 0) continue;

        n_scalar += popcnt32(mm);
        s_vec = _mm256_add_pd(s_vec, _mm256_and_pd(sumsq, mask));

#define MA(a, v) a = _mm256_add_pd(a, _mm256_and_pd(v, mask))
        MA(H00, _mm256_mul_pd(ihx, ihx));
        MA(H01, _mm256_mul_pd(ihx, ihy));
        MA(H02, _mm256_mul_pd(ihx, ihz));
        MA(H10, _mm256_mul_pd(ihy, ihx));
        MA(H11, _mm256_mul_pd(ihy, ihy));
        MA(H12, _mm256_mul_pd(ihy, ihz));
        MA(H20, _mm256_mul_pd(ihz, ihx));
        MA(H21, _mm256_mul_pd(ihz, ihy));
        MA(H22, _mm256_mul_pd(ihz, ihz));

        MA(R00, _mm256_mul_pd(ihx, gvx_v));
        MA(R01, _mm256_mul_pd(ihy, gvx_v));
        MA(R02, _mm256_mul_pd(ihz, gvx_v));
        MA(R10, _mm256_mul_pd(ihx, gvy_v));
        MA(R11, _mm256_mul_pd(ihy, gvy_v));
        MA(R12, _mm256_mul_pd(ihz, gvy_v));
        MA(R20, _mm256_mul_pd(ihx, gvz_v));
        MA(R21, _mm256_mul_pd(ihy, gvz_v));
        MA(R22, _mm256_mul_pd(ihz, gvz_v));
#undef MA
    }

    /* Horizontal reduction */
    
    H[0] = hsum4(H00); H[1] = hsum4(H01); H[2] = hsum4(H02);
    H[3] = hsum4(H10); H[4] = hsum4(H11); H[5] = hsum4(H12);
    H[6] = hsum4(H20); H[7] = hsum4(H21); H[8] = hsum4(H22);
    R[0] = hsum4(R00); R[1] = hsum4(R01); R[2] = hsum4(R02);
    R[3] = hsum4(R10); R[4] = hsum4(R11); R[5] = hsum4(R12);
    R[6] = hsum4(R20); R[7] = hsum4(R21); R[8] = hsum4(R22);
    *n_out = n_scalar;
    *sumdrlv2_out = hsum4(s_vec);

    /* Scalar tail */
    double tol2 = tol * tol, magic = 6755399441055744.0;
    for (; k < ng; k++) {
        double gx = gvx[k], gy = gvy[k], gz = gvz[k];
        double hx_ = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        double hy_ = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        double hz_ = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        double ix = (hx_ + magic) - magic;
        double iy = (hy_ + magic) - magic;
        double iz = (hz_ + magic) - magic;
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

/* ── extern "C" entry point ─────────────────────────────────────────── */
void score_and_refine_f64_soa_avx2(
    double ubi[3][3], const double gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    const double *gvx = gv;
    const double *gvy = gv + ng;
    const double *gvz = gv + 2 * ng;

    double H[3][3] = {{0}}, R[3][3] = {{0}}, UB[3][3] = {{0}};
    int n;
    double sumdrlv2;

    sar_f64_soa_avx2_kernel((const double *)ubi, gvx, gvy, gvz, tol, ng,
                             (double *)H, (double *)R, &n, &sumdrlv2);

    if (n > 0) sumdrlv2 /= n;

    if (inverse3x3(H) == 0) {
        int i, j, l;
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                for (l = 0; l < 3; l++)
                    UB[i][j] += R[i][l] * H[l][j];
    }
    if (inverse3x3(UB) == 0) {
        int i, j;
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                ubi[i][j] = UB[i][j];
    }

    *n_arg = n;
    *sumdrlv2_arg = sumdrlv2;
}
