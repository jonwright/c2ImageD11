/* reorder_u16_a32_kernel.c -- SIMD kernel for reorder_u16_a32()
 *
 * Scatter: out[adr[i]] = data[i]  (uint16 version)
 */

#include "cImageD11.h"
#include <stdint.h>

#ifndef KERNEL_FN
#define KERNEL_FN reorder_u16_a32_sse42
#endif

void KERNEL_FN(const uint16_t *restrict data, const uint32_t *restrict adr,
               uint16_t *restrict out, int N)
{
    int i;

#pragma omp parallel for
    for (i = 0; i < N; i++)
        out[adr[i]] = data[i];
}
