/* Auto-extracted from ImageD11/src/darkflat.c, function reorder_f32_a32, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"
#include <stdio.h>

void KERNEL_FN(const float *restrict data, const uint32_t *restrict adr,
                     float *restrict out, int N) {
    int i;
    /*  printf("Hello, got N=%d\n",N);*/
#pragma omp parallel for
    for (i = 0; i < N; i++) {
        out[adr[i]] = data[i];
    }
}
