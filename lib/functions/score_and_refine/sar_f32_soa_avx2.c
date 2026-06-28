/* sar_f32_soa_avx2.c -- f32 SoA AVX2 intrinsics variant
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx2",
 *         "sig": "void score_and_refine_f32_soa_avx2(double ubi[3][3], const float gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
 *     }],
 * }
 * C2PY_END
 */

#include <immintrin.h>
#include "sar_popcnt.h"
/* Horizontal sum: 8 floats in ymm -> scalar */
static float hsum8(__m256 v) {
    __m128 lo = _mm256_castps256_ps128(v);
    __m128 hi = _mm256_extractf128_ps(v, 1);
    lo = _mm_add_ps(lo, hi);
    lo = _mm_hadd_ps(lo, lo);
    lo = _mm_hadd_ps(lo, lo);
    return _mm_cvtss_f32(lo);
}

#include <stdint.h>

extern int inverse3x3(double A[3][3]);

static void
sar_f32_soa_avx2_kernel(const double ubi[9],
                         const float *__restrict gvx, const float *__restrict gvy, const float *__restrict gvz,
                         double tol, intptr_t ng,
                         double *__restrict H, double *__restrict R,
                         int *__restrict n_out, double *__restrict sumdrlv2_out)
{
    /* UBI is f64; cast to f32 for computation */
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
        __m256 gvx_v = _mm256_loadu_ps(&gvx[k]);
        __m256 gvy_v = _mm256_loadu_ps(&gvy[k]);
        __m256 gvz_v = _mm256_loadu_ps(&gvz[k]);

        __m256 hx = _mm256_fmadd_ps(u00, gvx_v,
                    _mm256_fmadd_ps(u01, gvy_v, _mm256_mul_ps(u02, gvz_v)));
        __m256 hy = _mm256_fmadd_ps(u10, gvx_v,
                    _mm256_fmadd_ps(u11, gvy_v, _mm256_mul_ps(u12, gvz_v)));
        __m256 hz = _mm256_fmadd_ps(u20, gvx_v,
                    _mm256_fmadd_ps(u21, gvy_v, _mm256_mul_ps(u22, gvz_v)));

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

        MA(R00, _mm256_mul_ps(ihx, gvx_v));
        MA(R01, _mm256_mul_ps(ihy, gvx_v));
        MA(R02, _mm256_mul_ps(ihz, gvx_v));
        MA(R10, _mm256_mul_ps(ihx, gvy_v));
        MA(R11, _mm256_mul_ps(ihy, gvy_v));
        MA(R12, _mm256_mul_ps(ihz, gvy_v));
        MA(R20, _mm256_mul_ps(ihx, gvz_v));
        MA(R21, _mm256_mul_ps(ihy, gvz_v));
        MA(R22, _mm256_mul_ps(ihz, gvz_v));
#undef MA
    }

    /* Horizontal reduction */
    
    H[0] = hsum8(H00); H[1] = hsum8(H01); H[2] = hsum8(H02);
    H[3] = hsum8(H10); H[4] = hsum8(H11); H[5] = hsum8(H12);
    H[6] = hsum8(H20); H[7] = hsum8(H21); H[8] = hsum8(H22);
    R[0] = hsum8(R00); R[1] = hsum8(R01); R[2] = hsum8(R02);
    R[3] = hsum8(R10); R[4] = hsum8(R11); R[5] = hsum8(R12);
    R[6] = hsum8(R20); R[7] = hsum8(R21); R[8] = hsum8(R22);
    #undef HS
    *n_out = n_scalar;
    *sumdrlv2_out = ({ __m128 lo = _mm256_castps256_ps128(s_vec);
                        __m128 hi = _mm256_extractf128_ps(s_vec, 1);
                        lo = _mm_add_ps(lo, hi); lo = _mm_hadd_ps(lo, lo);
                        lo = _mm_hadd_ps(lo, lo); (double)_mm_cvtss_f32(lo); });

    /* Scalar tail */
    double tol2 = tol * tol;
    for (; k < ng; k++) {
        double gx = gvx[k], gy = gvy[k], gz = gvz[k];
        double hx_ = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        double hy_ = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        double hz_ = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        double magic = 6755399441055744.0;
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

void score_and_refine_f32_soa_avx2(
    double ubi[3][3], const float gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    const float *gvx = gv;
    const float *gvy = gv + ng;
    const float *gvz = gv + 2 * ng;

    double H[3][3] = {{0}}, R[3][3] = {{0}}, UB[3][3] = {{0}};
    int n;
    double sumdrlv2;

    sar_f32_soa_avx2_kernel((const double *)ubi, gvx, gvy, gvz, tol, ng,
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
