/* score_tail.hpp -- shared scalar tails + horizontal reductions for ISA kernels
 *
 * The AVX2/AVX-512 score()/score_and_refine() kernels process most rows with
 * intrinsics and hand the remainder (ng % SIMD width, and every OpenMP
 * chunk's remainder) to a scalar loop.  That loop is the scalar score()
 * body (see score.c); it used to be copy-pasted into all 16 kernel files.
 * It lives here instead, as templates parameterized by the gv element type
 * T (float or double).
 *
 * Rounding uses nearbyint() (round-half-even): these helpers are included by
 * kernels compiled with -ffast-math, which folds the (x+MAGIC)-MAGIC trick to
 * identity (issue #33).  The -O2 baseline (score.c, score_and_refine.c) keeps
 * the magic trick and is guarded by verify_rounding() on import.
 *
 * Include from the AVX2/AVX-512 kernel files only.
 */

#ifndef SCORE_TAIL_HPP
#define SCORE_TAIL_HPP

#include <immintrin.h>
#include <math.h>
#include <stdint.h>

/* ---- score(): integer count, no accumulators ---- */

template <typename T>
static inline int
score_tail_aos(const double ubi[9], const T *gv, double tol, intptr_t ng) {
    double t2 = tol * tol;
    int n = 0;
    intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = (double)gv[k*3], gy = (double)gv[k*3+1], gz = (double)gv[k*3+2];
        double hx_ = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        hx_ -= nearbyint(hx_);
        double hy_ = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        hy_ -= nearbyint(hy_);
        double hz_ = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        hz_ -= nearbyint(hz_);
        if (hx_*hx_ + hy_*hy_ + hz_*hz_ < t2) n++;
    }
    return n;
}

template <typename T>
static inline int
score_tail_soa(const double ubi[9], const T *gvx, const T *gvy,
               const T *gvz, double tol, intptr_t ng) {
    double t2 = tol * tol;
    int n = 0;
    intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = (double)gvx[k], gy = (double)gvy[k], gz = (double)gvz[k];
        double hx_ = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        hx_ -= nearbyint(hx_);
        double hy_ = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        hy_ -= nearbyint(hy_);
        double hz_ = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        hz_ -= nearbyint(hz_);
        if (hx_*hx_ + hy_*hy_ + hz_*hz_ < t2) n++;
    }
    return n;
}

/* ---- score_and_refine(): accumulate H[9], R[9], n, sumdrlv2 ---- */

template <typename T>
static inline void
sar_tail_aos(const double ubi[9], const T *gv, double tol, intptr_t ng,
             double *H, double *R, int *n, double *sd) {
    double tol2 = tol * tol;
    intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = (double)gv[k*3], gy = (double)gv[k*3+1], gz = (double)gv[k*3+2];
        double hx_ = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        double hy_ = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        double hz_ = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        double ix = nearbyint(hx_), iy = nearbyint(hy_), iz = nearbyint(hz_);
        double tx_ = hx_ - ix, ty_ = hy_ - iy, tz_ = hz_ - iz;
        double s = tx_*tx_ + ty_*ty_ + tz_*tz_;
        if (s < tol2) {
            (*n)++; (*sd) += s;
            H[0]+=ix*ix; H[1]+=ix*iy; H[2]+=ix*iz;
            H[3]+=iy*ix; H[4]+=iy*iy; H[5]+=iy*iz;
            H[6]+=iz*ix; H[7]+=iz*iy; H[8]+=iz*iz;
            R[0]+=ix*gx; R[1]+=iy*gx; R[2]+=iz*gx;
            R[3]+=ix*gy; R[4]+=iy*gy; R[5]+=iz*gy;
            R[6]+=ix*gz; R[7]+=iy*gz; R[8]+=iz*gz;
        }
    }
}

template <typename T>
static inline void
sar_tail_soa(const double ubi[9], const T *gvx, const T *gvy,
             const T *gvz, double tol, intptr_t ng,
             double *H, double *R, int *n, double *sd) {
    double tol2 = tol * tol;
    intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = (double)gvx[k], gy = (double)gvy[k], gz = (double)gvz[k];
        double hx_ = ubi[0]*gx + ubi[1]*gy + ubi[2]*gz;
        double hy_ = ubi[3]*gx + ubi[4]*gy + ubi[5]*gz;
        double hz_ = ubi[6]*gx + ubi[7]*gy + ubi[8]*gz;
        double ix = nearbyint(hx_), iy = nearbyint(hy_), iz = nearbyint(hz_);
        double tx_ = hx_ - ix, ty_ = hy_ - iy, tz_ = hz_ - iz;
        double s = tx_*tx_ + ty_*ty_ + tz_*tz_;
        if (s < tol2) {
            (*n)++; (*sd) += s;
            H[0]+=ix*ix; H[1]+=ix*iy; H[2]+=ix*iz;
            H[3]+=iy*ix; H[4]+=iy*iy; H[5]+=iy*iz;
            H[6]+=iz*ix; H[7]+=iz*iy; H[8]+=iz*iz;
            R[0]+=ix*gx; R[1]+=iy*gx; R[2]+=iz*gx;
            R[3]+=ix*gy; R[4]+=iy*gy; R[5]+=iz*gy;
            R[6]+=ix*gz; R[7]+=iy*gz; R[8]+=iz*gz;
        }
    }
}

/* ---- horizontal reductions (sar AVX2 kernels) ---- */

static inline double hsum4(__m256d v) {
    __m128d lo = _mm256_castpd256_pd128(v), hi = _mm256_extractf128_pd(v, 1);
    lo = _mm_add_pd(lo, hi); lo = _mm_hadd_pd(lo, lo); return _mm_cvtsd_f64(lo);
}

static inline float hsum8(__m256 v) {
    __m128 lo = _mm256_castps256_ps128(v), hi = _mm256_extractf128_ps(v, 1);
    lo = _mm_add_ps(lo, hi); lo = _mm_hadd_ps(lo, lo);
    lo = _mm_hadd_ps(lo, lo); return _mm_cvtss_f32(lo);
}

#endif /* SCORE_TAIL_HPP */
