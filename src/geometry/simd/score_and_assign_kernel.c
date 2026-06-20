/* Auto-extracted from ImageD11/src/closest.c, function score_and_assign, commit 8f7d29e
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

int KERNEL_FN(vec *restrict ubi, vec *restrict gv, double tol,
                     double *restrict drlv2, int *restrict labels, int label,
                     intptr_t ng) {

    double h0, h1, h2, t0, t1, t2, sumsq, tolsq;
    int n;
    intptr_t k;
    tolsq = tol * tol;
    n = 0;
#pragma omp parallel for private(h0, h1, h2, t0, t1, t2, sumsq)                \
    reduction(+ : n) schedule(static, 4096)
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k][0] + ubi[0][1] * gv[k][1] + ubi[0][2] * gv[k][2];
        h1 = ubi[1][0] * gv[k][0] + ubi[1][1] * gv[k][1] + ubi[1][2] * gv[k][2];
        h2 = ubi[2][0] * gv[k][0] + ubi[2][1] * gv[k][1] + ubi[2][2] * gv[k][2];
        t0 = h0 - conv_double_to_int_fast(h0);
        t1 = h1 - conv_double_to_int_fast(h1);
        t2 = h2 - conv_double_to_int_fast(h2);
        sumsq = t0 * t0 + t1 * t1 + t2 * t2;
        /* If this peak fits better than the one in drlv2 then we
         * assign it:
         */
        if ((sumsq < tolsq) && (sumsq < drlv2[k])) {
            labels[k] = label;
            drlv2[k] = sumsq;
            n++;
        } else if (labels[k] == label) {
            /* We thought it belonged but it does not */
            labels[k] = -1;
        }
    }
    return n;
}
