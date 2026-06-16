/* put_incr32_kernel.c -- SIMD kernel for put_incr32()
 *
 * Scatter-add: data[ind[i]] += vals[i]
 * Uses 32-bit addressing. SIMD limited by scatter pattern but still
 * benefits from loop-level auto-vectorization (esp. with AVX-512 scatter).
 */

#include "cImageD11.h"
#include <stdio.h>

#ifndef KERNEL_FN
#define KERNEL_FN put_incr32_sse42
#endif

void KERNEL_FN(float *restrict data, const int32_t *restrict ind,
               const float *restrict vals, int boundscheck, int n, int m)
{
    int32_t k, ik;
    (void)m;
    if (boundscheck == 0) {
#pragma omp parallel for
        for (k = 0; k < n; k++)
            data[ind[k]] += vals[k];
    } else {
#pragma omp parallel for private(ik)
        for (k = 0; k < n; k++) {
            ik = ind[k];
            if (ik < 0 || ik >= m) {
                printf("Array bounds error! k=%d ind[k]=%d\n",
                       (int)k, (int)ik);
            } else {
                data[ik] += vals[k];
            }
        }
    }
}
