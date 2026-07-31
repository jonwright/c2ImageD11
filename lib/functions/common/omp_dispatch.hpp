/* omp_dispatch.hpp -- shared OpenMP parallel dispatch for intrinsics kernels
 *
 * Separates the OpenMP parallelization decision (parallel vs sequential)
 * from the per-ISA kernel selection.  Kernels are pure: they never know
 * how many threads are running.  Each extern "C" entry point is a one-liner
 * that picks a kernel and delegates the threading to one of the templates
 * below.
 *
 * The dispatch runs the kernel sequentially, or in parallel if ng >
 * cimaged11_omp_get_min_ng() and OpenMP reports more than one thread.  The
 * threshold is a runtime value (default 10000) settable from Python via
 * c2ImageD11.cimaged11_omp_set_min_ng().
 *
 * One template per (score|sar) x (AoS|SoA) combination, parameterized by the
 * gv element type T (float or double) and the kernel function (deduced from
 * the function-pointer argument, so the call stays direct and inlinable).
 * No element stride or void* arithmetic is needed: the pointer type is exact.
 *
 * The four templates:
 *   dispatch_score_aos  -- int reduce for score(); gv is interleaved AoS
 *       [ng][3].
 *   dispatch_score_soa  -- int reduce for score() SoA layout (three separate
 *       arrays).
 *   dispatch_sar_aos    -- score_and_refine AoS: multi-accumulator merge
 *       (H, R, n, sumdrlv2) via per-thread locals + critical section.
 *   dispatch_sar_soa    -- score_and_refine SoA, same merge.
 */

#ifndef OMP_DISPATCH_HPP
#define OMP_DISPATCH_HPP

#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif
int cimaged11_omp_get_min_ng(void);
#ifdef __cplusplus
}
#endif

#ifdef _OPENMP
#include <omp.h>
#endif

/* ---- score(): integer count, no accumulators ---- */

template <typename T, typename Kernel>
static inline int
dispatch_score_aos(Kernel fn, const double *ubi, const T *gv,
                   intptr_t ng, double tol) {
#ifdef _OPENMP
    int nthr = omp_get_max_threads();
    if (ng > cimaged11_omp_get_min_ng() && nthr > 1) {
        intptr_t chunk = (ng + nthr - 1) / nthr;
        int n = 0;
        #pragma omp parallel
        {
            int loc = 0;
            int tid = omp_get_thread_num();
            intptr_t start = tid * chunk;
            intptr_t end = (start + chunk < ng) ? start + chunk : ng;
            if (start < ng)
                loc = fn(ubi, gv + start * 3, tol, end - start);
            #pragma omp atomic
            n += loc;
        }
        return n;
    }
#endif
    return fn(ubi, gv, tol, ng);
}

template <typename T, typename Kernel>
static inline int
dispatch_score_soa(Kernel fn, const double *ubi,
                   const T *gvx, const T *gvy, const T *gvz,
                   intptr_t ng, double tol) {
#ifdef _OPENMP
    int nthr = omp_get_max_threads();
    if (ng > cimaged11_omp_get_min_ng() && nthr > 1) {
        intptr_t chunk = (ng + nthr - 1) / nthr;
        int n = 0;
        #pragma omp parallel
        {
            int loc = 0;
            int tid = omp_get_thread_num();
            intptr_t start = tid * chunk;
            intptr_t end = (start + chunk < ng) ? start + chunk : ng;
            if (start < ng)
                loc = fn(ubi, gvx + start, gvy + start, gvz + start,
                         tol, end - start);
            #pragma omp atomic
            n += loc;
        }
        return n;
    }
#endif
    return fn(ubi, gvx, gvy, gvz, tol, ng);
}

/* ---- score_and_refine(): multi-accumulator merge (H, R, n, sumdrlv2) ---- */

template <typename T, typename Kernel>
static inline void
dispatch_sar_aos(Kernel fn, const double *ubi, const T *gv,
                 intptr_t ng, double tol,
                 double H[3][3], double R[3][3], int *n, double *sd) {
#ifdef _OPENMP
    int nthr = omp_get_max_threads();
    if (ng > cimaged11_omp_get_min_ng() && nthr > 1) {
        int i, j;
        intptr_t chunk = (ng + nthr - 1) / nthr;
        /* Zero accumulator matrices (merged across threads) */
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++) {
                H[i][j] = 0;
                R[i][j] = 0;
            }
        *n = 0;
        *sd = 0;
        #pragma omp parallel
        {
            double H_loc[3][3] = {{0}}, R_loc[3][3] = {{0}};
            int n_loc = 0;
            double sd_loc = 0;
            int tid = omp_get_thread_num();
            intptr_t start = tid * chunk;
            intptr_t end = (start + chunk < ng) ? start + chunk : ng;
            if (start < ng)
                fn(ubi, gv + start * 3, tol, end - start,
                   (double *)H_loc, (double *)R_loc, &n_loc, &sd_loc);
            #pragma omp critical
            {
                int i, j;
                for (i = 0; i < 3; i++)
                    for (j = 0; j < 3; j++) {
                        H[i][j] += H_loc[i][j];
                        R[i][j] += R_loc[i][j];
                    }
                *n += n_loc;
                *sd += sd_loc;
            }
        }
        return;
    }
#endif
    fn(ubi, gv, tol, ng, (double *)H, (double *)R, n, sd);
}

template <typename T, typename Kernel>
static inline void
dispatch_sar_soa(Kernel fn, const double *ubi,
                 const T *gvx, const T *gvy, const T *gvz,
                 intptr_t ng, double tol,
                 double H[3][3], double R[3][3], int *n, double *sd) {
#ifdef _OPENMP
    int nthr = omp_get_max_threads();
    if (ng > cimaged11_omp_get_min_ng() && nthr > 1) {
        int i, j;
        intptr_t chunk = (ng + nthr - 1) / nthr;
        /* Zero accumulator matrices (merged across threads) */
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++) {
                H[i][j] = 0;
                R[i][j] = 0;
            }
        *n = 0;
        *sd = 0;
        #pragma omp parallel
        {
            double H_loc[3][3] = {{0}}, R_loc[3][3] = {{0}};
            int n_loc = 0;
            double sd_loc = 0;
            int tid = omp_get_thread_num();
            intptr_t start = tid * chunk;
            intptr_t end = (start + chunk < ng) ? start + chunk : ng;
            if (start < ng)
                fn(ubi, gvx + start, gvy + start, gvz + start, tol,
                   end - start, (double *)H_loc, (double *)R_loc,
                   &n_loc, &sd_loc);
            #pragma omp critical
            {
                int i, j;
                for (i = 0; i < 3; i++)
                    for (j = 0; j < 3; j++) {
                        H[i][j] += H_loc[i][j];
                        R[i][j] += R_loc[i][j];
                    }
                *n += n_loc;
                *sd += sd_loc;
            }
        }
        return;
    }
#endif
    fn(ubi, gvx, gvy, gvz, tol, ng, (double *)H, (double *)R, n, sd);
}

#endif /* OMP_DISPATCH_HPP */
