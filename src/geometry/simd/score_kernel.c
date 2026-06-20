/* Auto-extracted from ImageD11/src/closest.c, function score, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"
#include <math.h>
#include <stdint.h>
static inline double conv_double_to_int_fast(double x) {
    return (x + 6755399441055744.0) - 6755399441055744.0;
}

int KERNEL_FN(vec ubi[3], vec gv[], double tol, intptr_t ng) {
    /*
     * Counts g-vectors indexed by ubi within tol
     */
    double sumsq, h0, h1, h2, atol;
    int n;
    intptr_t k;
    n = 0;
    atol = tol * tol;
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k][0] + ubi[0][1] * gv[k][1] + ubi[0][2] * gv[k][2];
        h0 -= conv_double_to_int_fast(h0);
        h1 = ubi[1][0] * gv[k][0] + ubi[1][1] * gv[k][1] + ubi[1][2] * gv[k][2];
        h1 -= conv_double_to_int_fast(h1);
        h2 = ubi[2][0] * gv[k][0] + ubi[2][1] * gv[k][1] + ubi[2][2] * gv[k][2];
        h2 -= conv_double_to_int_fast(h2);
        sumsq = h0 * h0 + h1 * h1 + h2 * h2;
        if (sumsq < atol) {
            n = n + 1;
        }
    }
    return n;
}
