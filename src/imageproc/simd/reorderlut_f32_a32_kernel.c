/* Auto-extracted from ImageD11/src/darkflat.c, function reorderlut_f32_a32, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"

void KERNEL_FN(const float *restrict data, uint32_t *restrict lut,
                        float *restrict out, int N) {
    int i;
#pragma omp parallel for
    for (i = 0; i < N; i++) {
        out[i] = data[lut[i]];
    }
}
