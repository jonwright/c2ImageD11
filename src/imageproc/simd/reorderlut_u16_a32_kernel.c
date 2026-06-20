/* reorderlut_u16_a32_kernel.c -- SIMD kernel for reorderlut_u16_a32()
 *
 * Gather: out[i] = data[lut[i]]  (uint16 version)
 */

#include "cImageD11.h"
#include <stdint.h>

#ifndef KERNEL_FN
#define KERNEL_FN reorderlut_u16_a32_sse42
#endif

void KERNEL_FN(uint16_t *restrict data, const uint32_t *restrict lut,
               uint16_t *restrict out, int N)
{
    int i;

#pragma omp parallel for
    for (i = 0; i < N; i++)
        out[i] = data[lut[i]];
}
