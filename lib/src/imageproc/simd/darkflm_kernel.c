/* Auto-extracted from ImageD11/src/darkflat.c, function uint16_to_float_darkflm, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"
#include <stdint.h>

void KERNEL_FN(float *restrict img, const float *restrict drk,
                             const float *restrict flm,
                             const uint16_t *restrict data, intptr_t npx) {
    intptr_t i;
#ifdef GOT_OMP_SIMD
#pragma omp parallel for simd
#else
#pragma omp parallel for
#endif
    for (i = 0; i < npx; i++) {
        img[i] = (((float)data[i]) - drk[i]) * flm[i];
    }
}
