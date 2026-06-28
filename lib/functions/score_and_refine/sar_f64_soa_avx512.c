/* sar_f64_soa_avx512.c -- f64 SoA AVX-512 intrinsics variant
 *
 * 8 doubles per zmm register.  Uses AVX-512 mask registers for
 * branchless masked accumulation (no AND/MOVEMASK trick needed).
 *
 * Alignment: _mm512_loadu_pd — unaligned loads, zero-penalty on
 *   AVX-512 hardware.  No alignment requirement on input arrays.
 * Prefetch: not used.  Sequential forward stride-1 access is handled
 *   optimally by hardware L1/L2 prefetchers.
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx512f",
 *         "sig": "void score_and_refine_f64_soa_avx512(double ubi[3][3], const double gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "sar_popcnt.h"
#include <stdint.h>

extern int inverse3x3(double A[3][3]);

/* ── f64 SoA AVX-512 kernel (8 doubles/zmm) ──────────────────────────
 * Uses __mmask8 for comparison results, _mm512_mask_add_pd for
 * branchless masked accumulation.  No MOVEMASK or AND trick.
 */
static void
sar_f64_soa_avx512_kernel(
    const double ubi[9],
    const double *__restrict gvx,
    const double *__restrict gvy,
    const double *__restrict gvz,
    double tol, intptr_t ng,
    double *__restrict H,
    double *__restrict R,
    int *__restrict n_out,
    double *__restrict sumdrlv2_out)
{
    /* Broadcast UBI to all 8 lanes */
    __m512d u00 = _mm512_set1_pd(ubi[0]), u01 = _mm512_set1_pd(ubi[1]),
            u02 = _mm512_set1_pd(ubi[2]);
    __m512d u10 = _mm512_set1_pd(ubi[3]), u11 = _mm512_set1_pd(ubi[4]),
            u12 = _mm512_set1_pd(ubi[5]);
    __m512d u20 = _mm512_set1_pd(ubi[6]), u21 = _mm512_set1_pd(ubi[7]),
            u22 = _mm512_set1_pd(ubi[8]);
    __m512d tvec = _mm512_set1_pd(tol * tol);

    __m512d H00 = _mm512_setzero_pd(), H01 = _mm512_setzero_pd(),
            H02 = _mm512_setzero_pd(), H10 = _mm512_setzero_pd(),
            H11 = _mm512_setzero_pd(), H12 = _mm512_setzero_pd(),
            H20 = _mm512_setzero_pd(), H21 = _mm512_setzero_pd(),
            H22 = _mm512_setzero_pd();
    __m512d R00 = _mm512_setzero_pd(), R01 = _mm512_setzero_pd(),
            R02 = _mm512_setzero_pd(), R10 = _mm512_setzero_pd(),
            R11 = _mm512_setzero_pd(), R12 = _mm512_setzero_pd(),
            R20 = _mm512_setzero_pd(), R21 = _mm512_setzero_pd(),
            R22 = _mm512_setzero_pd();
    __m512d s_vec = _mm512_setzero_pd();
    int n_scalar = 0;

    intptr_t k;
    for (k = 0; k + 8 <= ng; k += 8) {
        __m512d gvx_v = _mm512_loadu_pd(&gvx[k]);
        __m512d gvy_v = _mm512_loadu_pd(&gvy[k]);
        __m512d gvz_v = _mm512_loadu_pd(&gvz[k]);

        __m512d hx = _mm512_fmadd_pd(u00, gvx_v,
                     _mm512_fmadd_pd(u01, gvy_v, _mm512_mul_pd(u02, gvz_v)));
        __m512d hy = _mm512_fmadd_pd(u10, gvx_v,
                     _mm512_fmadd_pd(u11, gvy_v, _mm512_mul_pd(u12, gvz_v)));
        __m512d hz = _mm512_fmadd_pd(u20, gvx_v,
                     _mm512_fmadd_pd(u21, gvy_v, _mm512_mul_pd(u22, gvz_v)));

        __m512d ihx = _mm512_roundscale_pd(hx, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m512d ihy = _mm512_roundscale_pd(hy, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m512d ihz = _mm512_roundscale_pd(hz, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);

        __m512d tx = _mm512_sub_pd(hx, ihx);
        __m512d ty = _mm512_sub_pd(hy, ihy);
        __m512d tz = _mm512_sub_pd(hz, ihz);

        __m512d sumsq = _mm512_fmadd_pd(tx, tx,
                        _mm512_fmadd_pd(ty, ty, _mm512_mul_pd(tz, tz)));

        __mmask8 mask = _mm512_cmp_pd_mask(sumsq, tvec, _CMP_LT_OS);
        if (mask == 0) continue;

        n_scalar += popcnt32((unsigned int)mask);

        /* Branchless masked accumulation: v = mask ? v + x : v */
        s_vec = _mm512_mask_add_pd(s_vec, mask, s_vec, sumsq);

#define MA(a, v) a = _mm512_mask_add_pd(a, mask, a, v)
        MA(H00, _mm512_mul_pd(ihx, ihx));
        MA(H01, _mm512_mul_pd(ihx, ihy));
        MA(H02, _mm512_mul_pd(ihx, ihz));
        MA(H10, _mm512_mul_pd(ihy, ihx));
        MA(H11, _mm512_mul_pd(ihy, ihy));
        MA(H12, _mm512_mul_pd(ihy, ihz));
        MA(H20, _mm512_mul_pd(ihz, ihx));
        MA(H21, _mm512_mul_pd(ihz, ihy));
        MA(H22, _mm512_mul_pd(ihz, ihz));

        MA(R00, _mm512_mul_pd(ihx, gvx_v));
        MA(R01, _mm512_mul_pd(ihy, gvx_v));
        MA(R02, _mm512_mul_pd(ihz, gvx_v));
        MA(R10, _mm512_mul_pd(ihx, gvy_v));
        MA(R11, _mm512_mul_pd(ihy, gvy_v));
        MA(R12, _mm512_mul_pd(ihz, gvy_v));
        MA(R20, _mm512_mul_pd(ihx, gvz_v));
        MA(R21, _mm512_mul_pd(ihy, gvz_v));
        MA(R22, _mm512_mul_pd(ihz, gvz_v));
#undef MA
    }

    H[0] = _mm512_reduce_add_pd(H00); H[1] = _mm512_reduce_add_pd(H01);
    H[2] = _mm512_reduce_add_pd(H02); H[3] = _mm512_reduce_add_pd(H10);
    H[4] = _mm512_reduce_add_pd(H11); H[5] = _mm512_reduce_add_pd(H12);
    H[6] = _mm512_reduce_add_pd(H20); H[7] = _mm512_reduce_add_pd(H21);
    H[8] = _mm512_reduce_add_pd(H22);
    R[0] = _mm512_reduce_add_pd(R00); R[1] = _mm512_reduce_add_pd(R01);
    R[2] = _mm512_reduce_add_pd(R02); R[3] = _mm512_reduce_add_pd(R10);
    R[4] = _mm512_reduce_add_pd(R11); R[5] = _mm512_reduce_add_pd(R12);
    R[6] = _mm512_reduce_add_pd(R20); R[7] = _mm512_reduce_add_pd(R21);
    R[8] = _mm512_reduce_add_pd(R22);
    *n_out = n_scalar;
    *sumdrlv2_out = _mm512_reduce_add_pd(s_vec);

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

void score_and_refine_f64_soa_avx512(
    double ubi[3][3], const double gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    const double *gvx = gv;
    const double *gvy = gv + ng;
    const double *gvz = gv + 2 * ng;

    double H[3][3] = {{0}}, R[3][3] = {{0}}, UB[3][3] = {{0}};
    int n;
    double sumdrlv2;

    sar_f64_soa_avx512_kernel((const double *)ubi, gvx, gvy, gvz, tol, ng,
                               (double *)H, (double *)R, &n, &sumdrlv2);

    if (n > 0) sumdrlv2 /= n;
    if (sumdrlv2 > 0) {} /* suppress unused */

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
