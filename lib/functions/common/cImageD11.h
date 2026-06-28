/* Try to collect all the compiler workarounds in one place */

#ifndef _cImageD11_h
#define _cImageD11_h

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <float.h>
#include <assert.h>

/* These did not expand properly anyway
 * #if _OPENMP >= 201307
 * #define SIMDCLAUSE simd
 * #define SIMDFOR omp simd
 * #else
 * #define SIMDCLAUSE
 * #define SIMDFOR ignore
 * #endif
 */

#ifdef _OPENMP
#include <omp.h>
#if _OPENMP >= 201307
#define GOT_OMP_SIMD
#endif
#endif

/* No really, thanks for standardising C99 20 years ago */
#define restrict __restrict

/* If we define functions as local they can be inlined at link time
 * in a shared library (e.g. not shared and overridden by LD_PRELOAD)
 * unlcear if/how this works currently across compilers...
 */
#if defined(__GNUC__) && !defined(__clang__) && !defined(__INTEL_COMPILER)
#if __GNUC__ >= 4
#define DLL_PUBLIC __attribute__((visibility("default")))
#define DLL_LOCAL __attribute__((visibility("hidden")))
#else
#define DLL_PUBLIC
#define DLL_LOCAL
#endif
#else
#define DLL_PUBLIC
#define DLL_LOCAL
#endif

#ifdef _MSC_VER
typedef __int8 int8_t;
typedef __int16 int16_t;
typedef __int32 int32_t;
typedef __int64 int64_t;
typedef unsigned char uint8_t;
typedef unsigned __int16 uint16_t;
typedef unsigned __int32 uint32_t;
typedef unsigned __int64 uint64_t;

#define inline __inline
#else
#include <stdint.h>
#endif

/* 3-vector type used by geometry kernels (from ImageD11/src/closest.c) */
typedef double vec[3];

/* implemented in imaged11utils.c */
void cimaged11_omp_set_num_threads(int);
int cimaged11_omp_get_max_threads(void);
DLL_LOCAL
double my_get_time(void);

/* Rounding helper used by score/refine/misori functions
 * Magic integer trick: safe without -ffast-math (no libm call).
 * Returns a double that is exactly integer-valued for |x| < 2^51.
 * See: https://stackoverflow.com/questions/59632005/
 * ImageD11 uses the same trick.
 */
#ifndef conv_double_to_int_fast
#define conv_double_to_int_fast(x) ((x + 6755399441055744.0) - 6755399441055744.0)
#endif

/* CPU feature flags for SIMD dispatch (from c2py23 runtime).
 * These are extern globals probed at load time by c2py_runtime.c.
 * All three headers are included unconditionally so that the wrapper
 * code compiles on every platform (flags for absent ISAs resolve to 0). */
#include "c2py_amd64.h"
#include "c2py_arm64.h"
#include "c2py_ppc64.h"

#endif
