/* put_incr64_kernel.c -- SIMD kernel for put_incr64()
 *
 * Scatter-add: data[ind[i]] += vals[i]
 * Uses 64-bit addressing.
 */

#include "cImageD11.h"
#include <stdio.h>
#include <stdint.h>

#ifndef KERNEL_FN
#define KERNEL_FN put_incr64_sse42
#endif

void KERNEL_FN(float *restrict data, const int64_t *restrict ind,
               const float *restrict vals, int boundscheck, int n, int m)
{
    int i;
    (void)m;
    if (boundscheck == 0) {
#pragma omp parallel for
        for (i = 0; i < n; i++)
            data[ind[i]] += vals[i];
    } else {
        int64_t ik;
#pragma omp parallel for private(ik)
        for (i = 0; i < n; i++) {
            ik = ind[i];
            if (ik < 0 || ik >= m) {
                printf("Array bounds error! i=%d ind[i]=%lld\n",
                       (int)i, (long long)ik);
            } else {
                data[ik] += vals[i];
            }
        }
    }
}
