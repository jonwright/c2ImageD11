/* darkflm_kernel.c -- SIMD kernel for uint16_to_float_darkflm()
 *
 * img[i] = ((float)data[i] - drk[i]) * flm[i]  (uint16 -> float dark+flat)
 * Simple element-wise loop, auto-vectorizes cleanly.
 */

#include "cImageD11.h"
#include <stdint.h>

#ifndef KERNEL_FN
#define KERNEL_FN uint16_to_float_darkflm_sse42
#endif

void KERNEL_FN(float *restrict img, const float *restrict drk,
               const float *restrict flm, const uint16_t *restrict data,
               int npx)
{
    int i;

#pragma omp parallel for simd
    for (i = 0; i < npx; i++)
        img[i] = (((float)data[i]) - drk[i]) * flm[i];
}
