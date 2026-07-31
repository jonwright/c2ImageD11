/* omp_dispatch.h -- shared OpenMP parallel dispatch for intrinsics kernels
 *
 * Separates the OpenMP parallelization decision (parallel vs sequential)
 * from the per-ISA kernel selection.  Kernels are pure: they never know
 * how many threads are running.  Each extern "C" entry point is a one-liner
 * that picks a kernel and delegates the threading to these macros.
 *
 * Include AFTER the kernel function declaration.  The macros run the kernel
 * sequentially, or in parallel if ng > OMP_MIN_NG and OpenMP reports more
 * than one thread.  OMP_MIN_NG must match c2ImageD11.OMP_MIN_NG in
 * c2ImageD11/__init__.py (measured cutoff: ng <= 10000 single-thread;
 * ng > 10000 threads well on x86_64).
 *
 * Four macros:
 *   OMP_DISPATCH_INT_AOS(fn, ubi, gv, sr, ng, tol, n_out)
 *       -- int reduce for score(); gv is interleaved AoS [ng][3],
 *          element stride 3 * sr bytes.
 *   OMP_DISPATCH_INT_SOA(fn, ubi, gvx, gvy, gvz, sr, ng, tol, n_out)
 *       -- int reduce for score() SoA layout (three separate arrays).
 *   SAR_OMP_DISPATCH_AOS / SAR_OMP_DISPATCH_SOA(fn, ubi, ...gv..., sr, ng,
 *          tol, H, R, n, sd)
 *       -- score_and_refine: multi-accumulator merge (H, R, n, sumdrlv2)
 *          via per-thread locals + critical section.
 */

#ifndef OMP_DISPATCH_H
#define OMP_DISPATCH_H

#include <stdint.h>

#ifndef OMP_MIN_NG
#define OMP_MIN_NG 10000
#endif

#ifdef _OPENMP
#include <omp.h>

#define OMP_DISPATCH_INT_AOS(fn, ubi, gv, sr, ng, tol, n_out) do { \
    int _nthr = omp_get_max_threads(); \
    if ((ng) > OMP_MIN_NG && _nthr > 1) { \
        int _tid; intptr_t _start, _end, _chunk; \
        _chunk = ((ng) + _nthr - 1) / _nthr; \
        n_out = 0; \
        _Pragma("omp parallel private(_tid, _start, _end)") \
        { \
            int _loc = 0; \
            _tid = omp_get_thread_num(); \
            _start = _tid * _chunk; \
            _end = (_start + _chunk < (ng)) ? _start + _chunk : (ng); \
            if (_start < (ng)) \
                _loc = fn(ubi, \
                    (const void *)((const char *)(gv) + _start * 3 * (sr)), \
                    (tol), _end - _start); \
            _Pragma("omp atomic") \
            n_out += _loc; \
        } \
    } else { \
        n_out = fn(ubi, gv, tol, ng); \
    } \
} while (0)

#define OMP_DISPATCH_INT_SOA(fn, ubi, gvx, gvy, gvz, sr, ng, tol, n_out) do { \
    int _nthr = omp_get_max_threads(); \
    if ((ng) > OMP_MIN_NG && _nthr > 1) { \
        int _tid; intptr_t _start, _end, _chunk; \
        _chunk = ((ng) + _nthr - 1) / _nthr; \
        n_out = 0; \
        _Pragma("omp parallel private(_tid, _start, _end)") \
        { \
            int _loc = 0; \
            _tid = omp_get_thread_num(); \
            _start = _tid * _chunk; \
            _end = (_start + _chunk < (ng)) ? _start + _chunk : (ng); \
            if (_start < (ng)) \
                _loc = fn(ubi, \
                    (const void *)((const char *)(gvx) + _start * (sr)), \
                    (const void *)((const char *)(gvy) + _start * (sr)), \
                    (const void *)((const char *)(gvz) + _start * (sr)), \
                    (tol), _end - _start); \
            _Pragma("omp atomic") \
            n_out += _loc; \
        } \
    } else { \
        n_out = fn(ubi, gvx, gvy, gvz, tol, ng); \
    } \
} while (0)

#define SAR_OMP_DISPATCH_AOS(fn, ubi, gv, sr, ng, tol, H, R, n, sd) do { \
    int _nthr = omp_get_max_threads(); \
    if ((ng) > OMP_MIN_NG && _nthr > 1) { \
        int _tid, _i, _j; \
        intptr_t _start, _end, _chunk; \
        _chunk = ((ng) + _nthr - 1) / _nthr; \
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
            _end = (_start + _chunk < (ng)) ? _start + _chunk : (ng); \
            if (_start < (ng)) { \
                fn(ubi, (const void *)((const char *)(gv) + _start * 3 * (sr)), \
                   (tol), _end - _start, (double *)H_loc, (double *)R_loc, \
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
} while (0)

#define SAR_OMP_DISPATCH_SOA(fn, ubi, gvx, gvy, gvz, sr, ng, tol, H, R, n, sd) do { \
    int _nthr = omp_get_max_threads(); \
    if ((ng) > OMP_MIN_NG && _nthr > 1) { \
        int _tid, _i, _j; \
        intptr_t _start, _end, _chunk; \
        _chunk = ((ng) + _nthr - 1) / _nthr; \
        for (_i = 0; _i < 3; _i++) for (_j = 0; _j < 3; _j++) { \
            H[_i][_j] = 0; R[_i][_j] = 0; } \
        *n = 0; *sd = 0; \
        _Pragma("omp parallel private(_tid, _start, _end, _i, _j)") \
        { \
            double H_loc[3][3] = {{0}}, R_loc[3][3] = {{0}}; \
            int n_loc = 0; double sd_loc = 0; \
            _tid = omp_get_thread_num(); \
            _start = _tid * _chunk; \
            _end = (_start + _chunk < (ng)) ? _start + _chunk : (ng); \
            if (_start < (ng)) { \
                fn(ubi, \
                   (const void *)((const char *)(gvx) + _start * (sr)), \
                   (const void *)((const char *)(gvy) + _start * (sr)), \
                   (const void *)((const char *)(gvz) + _start * (sr)), \
                   (tol), _end - _start, (double *)H_loc, (double *)R_loc, \
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
} while (0)

#else
/* No OpenMP: direct calls */
#define OMP_DISPATCH_INT_AOS(fn, ubi, gv, sr, ng, tol, n_out) \
    n_out = fn(ubi, gv, tol, ng)
#define OMP_DISPATCH_INT_SOA(fn, ubi, gvx, gvy, gvz, sr, ng, tol, n_out) \
    n_out = fn(ubi, gvx, gvy, gvz, tol, ng)
#define SAR_OMP_DISPATCH_AOS(fn, ubi, gv, sr, ng, tol, H, R, n, sd) \
    fn(ubi, gv, tol, ng, (double *)H, (double *)R, n, sd)
#define SAR_OMP_DISPATCH_SOA(fn, ubi, gvx, gvy, gvz, sr, ng, tol, H, R, n, sd) \
    fn(ubi, gvx, gvy, gvz, tol, ng, (double *)H, (double *)R, n, sd)
#endif

#endif /* OMP_DISPATCH_H */
