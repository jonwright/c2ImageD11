/* reorderlut_f32_a32_kernel.c -- SIMD kernel for reorderlut_f32_a32()
 *
 * Gather: out[i] = data[lut[i]]
 * Simple indirect load, OpenMP parallel.
 */

#include "cImageD11.h"
#include <stdint.h>

#ifndef KERNEL_FN
#define KERNEL_FN reorderlut_f32_a32_sse42
#endif

void KERNEL_FN(const float *restrict data, const uint32_t *restrict lut,
               float *restrict out, int N)
{
    int i;

#pragma omp parallel for
    for (i = 0; i < N; i++)
        out[i] = data[lut[i]];
}
