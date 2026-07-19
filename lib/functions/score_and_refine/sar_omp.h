/* sar_omp.h -- OpenMP parallel dispatch for intrinsics kernels
 *
 * Include this header AFTER the kernel function declaration.
 * Call SAR_OMP_DISPATCH(kernel_name, ubi, ptr_args, ng, tol) from the
 * extern "C" entry point.  It runs the kernel sequentially, or in
 * parallel if ng > SAR_OMP_MIN_NG and OpenMP is available.
 */

#ifndef SAR_OMP_H
#define SAR_OMP_H

#include <stdint.h>

#ifndef SAR_OMP_MIN_NG
#define SAR_OMP_MIN_NG 10000
#endif

#ifdef _OPENMP
#include <omp.h>

/* Array offset helper: pointer + stride*start */
/* Dispatch: split ng across threads, call kernel per thread, merge results.
 * ubi: 9-element double array (always f64, shared across threads)
 * gv0,gv1,gv2: three pointer args to the kernel (gv or gvx/gvy/gvz)
 * sr: sizeof kernel element (sizeof(double) or sizeof(float))
 * fn: the kernel function to call per thread
 *
 * Each thread gets its slice of [start, end) and local accumulators.
 * Results are merged into the caller's H, R, n, sd via critical section.
 */
#define SAR_OMP_DISPATCH_AOS(fn, ubi, gv, sr, ng, tol, H, R, n, sd) do { \
    int _nthr = omp_get_max_threads(); \
    if (ng > SAR_OMP_MIN_NG && _nthr > 1) { \
        int _tid, _i, _j; \
        intptr_t _start, _end, _chunk; \
        _chunk = (ng + _nthr - 1) / _nthr; \
        /* Zero accumulator matrices (merged across threads) */ \
        for (_i = 0; _i < 3; _i++) for (_j = 0; _j < 3; _j++) { \
            H[_i][_j] = 0; R[_i][_j] = 0; } \
        *n = 0; *sd = 0; \
        _Pragma("omp parallel private(_tid, _start, _end, _i, _j)") \
        { \
            double H_loc[3][3] = {{0}}, R_loc[3][3] = {{0}}; \
            int n_loc = 0; double sd_loc = 0; \
            _tid = omp_get_thread_num(); \
            _start = _tid * _chunk; \
            _end = (_start + _chunk < ng) ? _start + _chunk : ng; \
            if (_start < ng) { \
                fn(ubi, (const void *)((const char *)gv + _start * 3 * sr), \
                   tol, _end - _start, (double *)H_loc, (double *)R_loc, \
                   &n_loc, &sd_loc); \
            } \
            _Pragma("omp critical") \
            { \
                for (_i = 0; _i < 3; _i++) for (_j = 0; _j < 3; _j++) { \
                    H[_i][_j] += H_loc[_i][_j]; \
                    R[_i][_j] += R_loc[_i][_j]; \
                } \
                *n += n_loc; *sd += sd_loc; \
            } \
        } \
    } else { \
        fn(ubi, gv, tol, ng, (double *)H, (double *)R, n, sd); \
    } \
} while(0)

#define SAR_OMP_DISPATCH_SOA(fn, ubi, gvx, gvy, gvz, sr, ng, tol, H, R, n, sd) do { \
    int _nthr = omp_get_max_threads(); \
    if (ng > SAR_OMP_MIN_NG && _nthr > 1) { \
        int _tid, _i, _j; \
        intptr_t _start, _end, _chunk; \
        _chunk = (ng + _nthr - 1) / _nthr; \
        for (_i = 0; _i < 3; _i++) for (_j = 0; _j < 3; _j++) { \
            H[_i][_j] = 0; R[_i][_j] = 0; } \
        *n = 0; *sd = 0; \
        _Pragma("omp parallel private(_tid, _start, _end, _i, _j)") \
        { \
            double H_loc[3][3] = {{0}}, R_loc[3][3] = {{0}}; \
            int n_loc = 0; double sd_loc = 0; \
            _tid = omp_get_thread_num(); \
            _start = _tid * _chunk; \
            _end = (_start + _chunk < ng) ? _start + _chunk : ng; \
            if (_start < ng) { \
                fn(ubi, \
                   (const void *)((const char *)gvx + _start * sr), \
                   (const void *)((const char *)gvy + _start * sr), \
                   (const void *)((const char *)gvz + _start * sr), \
                   tol, _end - _start, (double *)H_loc, (double *)R_loc, \
                   &n_loc, &sd_loc); \
            } \
            _Pragma("omp critical") \
            { \
                for (_i = 0; _i < 3; _i++) for (_j = 0; _j < 3; _j++) { \
                    H[_i][_j] += H_loc[_i][_j]; \
                    R[_i][_j] += R_loc[_i][_j]; \
                } \
                *n += n_loc; *sd += sd_loc; \
            } \
        } \
    } else { \
        fn(ubi, gvx, gvy, gvz, tol, ng, (double *)H, (double *)R, n, sd); \
    } \
} while(0)

#else
/* No OpenMP: direct call */
#define SAR_OMP_DISPATCH_AOS(fn, ubi, gv, sr, ng, tol, H, R, n, sd) \
    fn(ubi, gv, tol, ng, (double *)H, (double *)R, n, sd)

#define SAR_OMP_DISPATCH_SOA(fn, ubi, gvx, gvy, gvz, sr, ng, tol, H, R, n, sd) \
    fn(ubi, gvx, gvy, gvz, tol, ng, (double *)H, (double *)R, n, sd)
#endif

#endif /* SAR_OMP_H */
