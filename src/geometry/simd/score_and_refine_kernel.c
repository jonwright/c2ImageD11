/* score_and_refine_kernel.c -- SIMD kernel for score_and_refine()
 *
 * Scores g-vectors AND refines the UBI matrix using least-squares.
 * Takes flat double* (matches c2py23 .ptr) instead of vec[3].
 * Returns number of indexed peaks; sumdrlv2 is written via pointer.
 */

#include "cImageD11.h"
#include <math.h>
#include <string.h>

#ifndef KERNEL_FN
#define KERNEL_FN score_and_refine_sse42
#endif

#define MAGIC 6755399441055744.0
static inline double fast_round(double x) { return (x + MAGIC) - MAGIC; }

static int inverse3x3(double m[9])
{
    double det = m[0]*(m[4]*m[8] - m[5]*m[7])
               - m[1]*(m[3]*m[8] - m[5]*m[6])
               + m[2]*(m[3]*m[7] - m[4]*m[6]);
    if (fabs(det) < 1e-30) return 777;
    double inv_det = 1.0 / det;
    double a00 =  (m[4]*m[8] - m[5]*m[7]) * inv_det;
    double a01 = -(m[1]*m[8] - m[2]*m[7]) * inv_det;
    double a02 =  (m[1]*m[5] - m[2]*m[4]) * inv_det;
    double a10 = -(m[3]*m[8] - m[5]*m[6]) * inv_det;
    double a11 =  (m[0]*m[8] - m[2]*m[6]) * inv_det;
    double a12 = -(m[0]*m[5] - m[2]*m[3]) * inv_det;
    double a20 =  (m[3]*m[7] - m[4]*m[6]) * inv_det;
    double a21 = -(m[0]*m[7] - m[1]*m[6]) * inv_det;
    double a22 =  (m[0]*m[4] - m[1]*m[3]) * inv_det;
    m[0]=a00; m[1]=a01; m[2]=a02;
    m[3]=a10; m[4]=a11; m[5]=a12;
    m[6]=a20; m[7]=a21; m[8]=a22;
    return 0;
}

int KERNEL_FN(const double *restrict ubi, const double *restrict gv,
              double tol, double *sumdrlv2_arg, int ng)
{
    double h0, h1, h2, t0, t1, t2, ih[3];
    double sumsq, tolsq, sumdrlv2;
    double R[9], H[9], UB[9];
    int n, k, i, j, l;

    memset(R, 0, sizeof(R));
    memset(H, 0, sizeof(H));
    memset(UB, 0, sizeof(UB));
    tolsq = tol * tol;
    n = 0;
    sumdrlv2 = 0.;

    for (k = 0; k < ng; k++) {
        const double *g = gv + k * 3;
        h0 = ubi[0]*g[0] + ubi[1]*g[1] + ubi[2]*g[2];
        h1 = ubi[3]*g[0] + ubi[4]*g[1] + ubi[5]*g[2];
        h2 = ubi[6]*g[0] + ubi[7]*g[1] + ubi[8]*g[2];
        t0 = h0 - fast_round(h0);
        t1 = h1 - fast_round(h1);
        t2 = h2 - fast_round(h2);
        sumsq = t0*t0 + t1*t1 + t2*t2;
        if (sumsq < tolsq) {
            n++;
            sumdrlv2 += sumsq;
            ih[0] = fast_round(h0);
            ih[1] = fast_round(h1);
            ih[2] = fast_round(h2);
            for (i = 0; i < 3; i++) {
                for (j = 0; j < 3; j++) {
                    R[i*3+j] += ih[j] * g[i];
                    H[i*3+j] += ih[j] * ih[i];
                }
            }
        }
    }

    l = inverse3x3(H);
    if (l == 0) {
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                for (l = 0; l < 3; l++)
                    UB[i*3+j] += R[i*3+l] * H[l*3+j];
    }
    if ((l == 0) && (inverse3x3(UB) == 0)) {
        for (i = 0; i < 9; i++)
            ((double*)ubi)[i] = UB[i];
    }

    if (n > 0) sumdrlv2 /= n;
    *sumdrlv2_arg = sumdrlv2;
    return n;
}
