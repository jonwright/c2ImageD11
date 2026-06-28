/* score_and_refine.hpp -- merged AoS/SoA C++ template
 *
 * C++ subset: C99 + templates only.
 * - No std::*, no exceptions, no RTTI, no iostream
 * - __restrict on pointer parameters
 * - math.h for nearbyint/nearbyintf
 * - Parameterized by T_gv (float/double) and T_accum (float/double).
 *   UBI is always double.
 * - Define SAR_SOA before #include for SoA layout (separate gvx,gvy,gvz ptrs).
 *   Otherwise AoS layout (interleaved gv[ng][3]).
 * - Define SAR_IMPL_NAME before #include for unique template name
 *   (avoids linker symbol collisions with different compiler flags).
 * - Baseline (no SSE4.1): magic integer trick for rounding.
 *   SSE4.1+: nearbyint inlines to roundsd/roundss.
 * - x/y/z scalar subscripts for alias-free auto-vectorization.
 */

#ifndef SCORE_AND_REFINE_HPP
#define SCORE_AND_REFINE_HPP

#include <math.h>
#include <stdint.h>
#include <string.h>

#ifdef _OPENMP
#include <omp.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif
int inverse3x3(double A[3][3]);
#ifdef __cplusplus
}
#endif

/* Round to nearest integer. */
template <typename T>
static inline T rint_h(T x) {
#if defined(__SSE4_1__) || defined(__AVX__)
    if (sizeof(T) == sizeof(float))
        return (T)nearbyintf((float)x);
    return nearbyint(x);
#else
    if (sizeof(T) == sizeof(float)) {
        const float magic = 12582912.0f;          /* 1.5 * 2^23 */
        return (T)(((float)x + magic) - magic);
    } else {
        const double magic = 6755399441055744.0;  /* 1.5 * 2^52 */
        return (T)((x + magic) - magic);
    }
#endif
}

#ifndef SAR_IMPL_NAME
#define SAR_IMPL_NAME score_and_refine_impl
#endif

/* Single template handling both AoS and SoA layouts.
 * SoA: define SAR_SOA before #include; function gets gvx,gvy,gvz parameters.
 * AoS (default): one gv pointer, accessed as gv[k*3+0..2]. */
template <typename T_gv, typename T_accum>
void SAR_IMPL_NAME(
    double ubi[3][3],
#ifdef SAR_SOA
    const T_gv * __restrict gvx,
    const T_gv * __restrict gvy,
    const T_gv * __restrict gvz,
#else
    const T_gv * __restrict gv,
#endif
    double tol,
    int *n_arg,
    double *sumdrlv2_arg,
    intptr_t ng)
{
    T_gv ubi_00 = (T_gv)ubi[0][0];
    T_gv ubi_01 = (T_gv)ubi[0][1];
    T_gv ubi_02 = (T_gv)ubi[0][2];
    T_gv ubi_10 = (T_gv)ubi[1][0];
    T_gv ubi_11 = (T_gv)ubi[1][1];
    T_gv ubi_12 = (T_gv)ubi[1][2];
    T_gv ubi_20 = (T_gv)ubi[2][0];
    T_gv ubi_21 = (T_gv)ubi[2][1];
    T_gv ubi_22 = (T_gv)ubi[2][2];

    T_accum R_00 = 0, R_01 = 0, R_02 = 0;
    T_accum R_10 = 0, R_11 = 0, R_12 = 0;
    T_accum R_20 = 0, R_21 = 0, R_22 = 0;

    T_accum H_00 = 0, H_01 = 0, H_02 = 0;
    T_accum H_10 = 0, H_11 = 0, H_12 = 0;
    T_accum H_20 = 0, H_21 = 0, H_22 = 0;

    intptr_t k;
    int  n = 0;
    T_accum sumdrlv2 = 0;
    T_gv tolsq = (T_gv)(tol * tol);

#ifdef _OPENMP
/* Threshold for OpenMP parallelization.  Must match c2ImageD11.OMP_MIN_NG.  Lower cutoff for MSVC
   in ../../c2ImageD11/__init__.py.  Measured cutoff on x86_64 (4C Zen3):
   ng <= 10000 | single-thread; ng > 10000 | threaded. */
#pragma omp parallel for reduction(+: n, sumdrlv2, \
    R_00, R_01, R_02, R_10, R_11, R_12, R_20, R_21, R_22, \
    H_00, H_01, H_02, H_10, H_11, H_12, H_20, H_21, H_22) \
    if(ng > 10000 && omp_get_max_threads() > 1)
#endif
    for (k = 0; k < ng; k++) {
#ifdef SAR_SOA
        T_gv gvx_v = gvx[k];
        T_gv gvy_v = gvy[k];
        T_gv gvz_v = gvz[k];
#else
        T_gv gvx_v = gv[k * 3 + 0];
        T_gv gvy_v = gv[k * 3 + 1];
        T_gv gvz_v = gv[k * 3 + 2];
#endif
        T_gv hx = ubi_00 * gvx_v + ubi_01 * gvy_v + ubi_02 * gvz_v;
        T_gv hy = ubi_10 * gvx_v + ubi_11 * gvy_v + ubi_12 * gvz_v;
        T_gv hz = ubi_20 * gvx_v + ubi_21 * gvy_v + ubi_22 * gvz_v;

        T_gv ihx = rint_h(hx);
        T_gv ihy = rint_h(hy);
        T_gv ihz = rint_h(hz);

        T_gv tx = hx - ihx;
        T_gv ty = hy - ihy;
        T_gv tz = hz - ihz;

        T_gv sumsq = tx * tx + ty * ty + tz * tz;
        if (sumsq < tolsq) {
            n++;
            sumdrlv2 += (T_accum)sumsq;

            T_accum ihx_a = (T_accum)ihx;
            T_accum ihy_a = (T_accum)ihy;
            T_accum ihz_a = (T_accum)ihz;

            H_00 += ihx_a * ihx_a;
            H_01 += ihx_a * ihy_a;
            H_02 += ihx_a * ihz_a;
            H_10 += ihy_a * ihx_a;
            H_11 += ihy_a * ihy_a;
            H_12 += ihy_a * ihz_a;
            H_20 += ihz_a * ihx_a;
            H_21 += ihz_a * ihy_a;
            H_22 += ihz_a * ihz_a;

            T_accum gvx_a = (T_accum)gvx_v;
            T_accum gvy_a = (T_accum)gvy_v;
            T_accum gvz_a = (T_accum)gvz_v;

            R_00 += ihx_a * gvx_a;
            R_01 += ihy_a * gvx_a;
            R_02 += ihz_a * gvx_a;
            R_10 += ihx_a * gvy_a;
            R_11 += ihy_a * gvy_a;
            R_12 += ihz_a * gvy_a;
            R_20 += ihx_a * gvz_a;
            R_21 += ihy_a * gvz_a;
            R_22 += ihz_a * gvz_a;
        }
    }

    double H[3][3] = {
        {(double)H_00, (double)H_01, (double)H_02},
        {(double)H_10, (double)H_11, (double)H_12},
        {(double)H_20, (double)H_21, (double)H_22}
    };
    double R[3][3] = {
        {(double)R_00, (double)R_01, (double)R_02},
        {(double)R_10, (double)R_11, (double)R_12},
        {(double)R_20, (double)R_21, (double)R_22}
    };
    double UB[3][3] = {{0.0}};

    k = inverse3x3(H);
    if (k == 0) {
        int i, j, l;
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                for (l = 0; l < 3; l++)
                    UB[i][j] += R[i][l] * H[l][j];
    }

    if ((k == 0) && (inverse3x3(UB) == 0)) {
        ubi[0][0] = UB[0][0]; ubi[0][1] = UB[0][1]; ubi[0][2] = UB[0][2];
        ubi[1][0] = UB[1][0]; ubi[1][1] = UB[1][1]; ubi[1][2] = UB[1][2];
        ubi[2][0] = UB[2][0]; ubi[2][1] = UB[2][1]; ubi[2][2] = UB[2][2];
    }

    if (n > 0)
        sumdrlv2 = (T_accum)((double)sumdrlv2 / n);

    *n_arg = n;
    *sumdrlv2_arg = (double)sumdrlv2;
}

#endif /* SCORE_AND_REFINE_HPP */
