/* sar_f32_soa_avx512.c -- f32 SoA AVX-512 intrinsics variant
 *
 * 16 floats per zmm register.  Uses AVX-512 mask registers.
 * Alignment: unaligned loads, zero-penalty on AVX-512 hardware.
 * Prefetch: not used — sequential stride-1, hw prefetcher handles it.
 *
 * C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx512f",
 *         "sig": "void score_and_refine_f32_soa_avx512(double ubi[3][3], const float gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
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

static void
sar_f32_soa_avx512_kernel(
    const double ubi[9],
    const float *__restrict gvx,
    const float *__restrict gvy,
    const float *__restrict gvz,
    double tol, intptr_t ng,
    double *__restrict H,
    double *__restrict R,
    int *__restrict n_out,
    double *__restrict sumdrlv2_out)
{
    /* UBI is f64; cast to f32 for the inner loop */
    __m512 u00 = _mm512_set1_ps((float)ubi[0]), u01 = _mm512_set1_ps((float)ubi[1]),
            u02 = _mm512_set1_ps((float)ubi[2]);
    __m512 u10 = _mm512_set1_ps((float)ubi[3]), u11 = _mm512_set1_ps((float)ubi[4]),
            u12 = _mm512_set1_ps((float)ubi[5]);
    __m512 u20 = _mm512_set1_ps((float)ubi[6]), u21 = _mm512_set1_ps((float)ubi[7]),
            u22 = _mm512_set1_ps((float)ubi[8]);
    float t2 = (float)(tol * tol);
    __m512 tvec = _mm512_set1_ps(t2);

    __m512 H00 = _mm512_setzero_ps(), H01 = _mm512_setzero_ps(),
            H02 = _mm512_setzero_ps(), H10 = _mm512_setzero_ps(),
            H11 = _mm512_setzero_ps(), H12 = _mm512_setzero_ps(),
            H20 = _mm512_setzero_ps(), H21 = _mm512_setzero_ps(),
            H22 = _mm512_setzero_ps();
    __m512 R00 = _mm512_setzero_ps(), R01 = _mm512_setzero_ps(),
            R02 = _mm512_setzero_ps(), R10 = _mm512_setzero_ps(),
            R11 = _mm512_setzero_ps(), R12 = _mm512_setzero_ps(),
            R20 = _mm512_setzero_ps(), R21 = _mm512_setzero_ps(),
            R22 = _mm512_setzero_ps();
    __m512 s_vec = _mm512_setzero_ps();
    int n_scalar = 0;

    intptr_t k;
    for (k = 0; k + 16 <= ng; k += 16) {
        __m512 gvx_v = _mm512_loadu_ps(&gvx[k]);
        __m512 gvy_v = _mm512_loadu_ps(&gvy[k]);
        __m512 gvz_v = _mm512_loadu_ps(&gvz[k]);

        __m512 hx = _mm512_fmadd_ps(u00, gvx_v,
                    _mm512_fmadd_ps(u01, gvy_v, _mm512_mul_ps(u02, gvz_v)));
        __m512 hy = _mm512_fmadd_ps(u10, gvx_v,
                    _mm512_fmadd_ps(u11, gvy_v, _mm512_mul_ps(u12, gvz_v)));
        __m512 hz = _mm512_fmadd_ps(u20, gvx_v,
                    _mm512_fmadd_ps(u21, gvy_v, _mm512_mul_ps(u22, gvz_v)));

        __m512 ihx = _mm512_roundscale_ps(hx, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m512 ihy = _mm512_roundscale_ps(hy, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);
        __m512 ihz = _mm512_roundscale_ps(hz, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC);

        __m512 tx = _mm512_sub_ps(hx, ihx);
        __m512 ty = _mm512_sub_ps(hy, ihy);
        __m512 tz = _mm512_sub_ps(hz, ihz);

        __m512 sumsq = _mm512_fmadd_ps(tx, tx,
                       _mm512_fmadd_ps(ty, ty, _mm512_mul_ps(tz, tz)));

        __mmask16 mask = _mm512_cmp_ps_mask(sumsq, tvec, _CMP_LT_OS);
        if (mask == 0) continue;

        n_scalar += popcnt32((unsigned int)mask);

        s_vec = _mm512_mask_add_ps(s_vec, mask, s_vec, sumsq);

#define MA(a, v) a = _mm512_mask_add_ps(a, mask, a, v)
        MA(H00, _mm512_mul_ps(ihx, ihx));
        MA(H01, _mm512_mul_ps(ihx, ihy));
        MA(H02, _mm512_mul_ps(ihx, ihz));
        MA(H10, _mm512_mul_ps(ihy, ihx));
        MA(H11, _mm512_mul_ps(ihy, ihy));
        MA(H12, _mm512_mul_ps(ihy, ihz));
        MA(H20, _mm512_mul_ps(ihz, ihx));
        MA(H21, _mm512_mul_ps(ihz, ihy));
        MA(H22, _mm512_mul_ps(ihz, ihz));

        MA(R00, _mm512_mul_ps(ihx, gvx_v));
        MA(R01, _mm512_mul_ps(ihy, gvx_v));
        MA(R02, _mm512_mul_ps(ihz, gvx_v));
        MA(R10, _mm512_mul_ps(ihx, gvy_v));
        MA(R11, _mm512_mul_ps(ihy, gvy_v));
        MA(R12, _mm512_mul_ps(ihz, gvy_v));
        MA(R20, _mm512_mul_ps(ihx, gvz_v));
        MA(R21, _mm512_mul_ps(ihy, gvz_v));
        MA(R22, _mm512_mul_ps(ihz, gvz_v));
#undef MA
    }

    H[0] = _mm512_reduce_add_ps(H00); H[1] = _mm512_reduce_add_ps(H01);
    H[2] = _mm512_reduce_add_ps(H02); H[3] = _mm512_reduce_add_ps(H10);
    H[4] = _mm512_reduce_add_ps(H11); H[5] = _mm512_reduce_add_ps(H12);
    H[6] = _mm512_reduce_add_ps(H20); H[7] = _mm512_reduce_add_ps(H21);
    H[8] = _mm512_reduce_add_ps(H22);
    R[0] = _mm512_reduce_add_ps(R00); R[1] = _mm512_reduce_add_ps(R01);
    R[2] = _mm512_reduce_add_ps(R02); R[3] = _mm512_reduce_add_ps(R10);
    R[4] = _mm512_reduce_add_ps(R11); R[5] = _mm512_reduce_add_ps(R12);
    R[6] = _mm512_reduce_add_ps(R20); R[7] = _mm512_reduce_add_ps(R21);
    R[8] = _mm512_reduce_add_ps(R22);
    *n_out = n_scalar;
    *sumdrlv2_out = (double)_mm512_reduce_add_ps(s_vec);

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

void score_and_refine_f32_soa_avx512(
    double ubi[3][3], const float gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    const float *gvx = gv;
    const float *gvy = gv + ng;
    const float *gvz = gv + 2 * ng;

    double H[3][3] = {{0}}, R[3][3] = {{0}}, UB[3][3] = {{0}};
    int n;
    double sumdrlv2;

    sar_f32_soa_avx512_kernel((const double *)ubi, gvx, gvy, gvz, tol, ng,
                               (double *)H, (double *)R, &n, &sumdrlv2);

    if (n > 0) sumdrlv2 /= n;
    if (sumdrlv2 > 0) {}

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
