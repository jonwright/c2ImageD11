/* Auto-extracted from ImageD11/src/closest.c, function put_incr64, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"
#include <stdio.h>
#include <stdint.h>

void KERNEL_FN(float data[], int64_t ind[], float vals[], int boundscheck,
                intptr_t n, intptr_t m) {
    intptr_t k;
    int64_t ik;
    if (boundscheck == 0) {
        for (k = 0; k < n; k++)
            data[ind[k]] += vals[k];
    } else {
        for (k = 0; k < n; k++) {
            ik = ind[k];
            if (ik < 0 || ik >= m) {
                printf("Array bounds error! k=%d ind[k]=%d\n", (int)k,
                       (int)ind[k]);
            } else {
                data[ind[k]] += vals[k];
            }
        }
    }
}
