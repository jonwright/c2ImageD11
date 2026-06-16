/* score_and_assign_kernel.c -- SIMD kernel for score_and_assign()
 *
 * Scores g-vectors against a UBI and assigns peaks if this grain
 * fits better than the current best (stored in drlv2/labels).
 * Takes flat double* (matches c2py23 .ptr) instead of vec[3].
 */

#include "cImageD11.h"
#include <math.h>

#ifndef KERNEL_FN
#define KERNEL_FN score_and_assign_sse42
#endif

#define MAGIC 6755399441055744.0
static inline double fast_round(double x) { return (x + MAGIC) - MAGIC; }

int KERNEL_FN(const double *restrict ubi, const double *restrict gv,
              double tol, double *restrict drlv2, int *restrict labels,
              int label, int ng)
{
    double sumsq, h0, h1, h2, atol;
    int n, k;
    n = 0;
    atol = tol * tol;

    for (k = 0; k < ng; k++) {
        const double *g = gv + k * 3;
        h0 = ubi[0]*g[0] + ubi[1]*g[1] + ubi[2]*g[2];
        h0 -= fast_round(h0);
        h1 = ubi[3]*g[0] + ubi[4]*g[1] + ubi[5]*g[2];
        h1 -= fast_round(h1);
        h2 = ubi[6]*g[0] + ubi[7]*g[1] + ubi[8]*g[2];
        h2 -= fast_round(h2);
        sumsq = h0*h0 + h1*h1 + h2*h2;
        if (sumsq < atol) {
            if (sumsq < drlv2[k]) {
                drlv2[k] = sumsq;
                labels[k] = label;
            }
            n++;
        }
    }
    return n;
}
