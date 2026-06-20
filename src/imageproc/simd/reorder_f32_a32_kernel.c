/* reorder_f32_a32_kernel.c -- SIMD kernel for reorder_f32_a32()
 *
 * Scatter: out[adr[i]] = data[i]
 * Simple indirect store, OpenMP parallel.
 */

#include "cImageD11.h"
#include <stdint.h>

#ifndef KERNEL_FN
#define KERNEL_FN reorder_f32_a32_sse42
#endif

void KERNEL_FN(const float *restrict data, const uint32_t *restrict adr,
               float *restrict out, int N)
{
    int i;

#pragma omp parallel for
    for (i = 0; i < N; i++)
        out[adr[i]] = data[i];
}
