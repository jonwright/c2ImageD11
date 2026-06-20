/* compute_xlylzl_kernel.c -- SIMD kernel for compute_xlylzl()
 *
 * Converts detector pixel coordinates (slow, fast) to laboratory
 * frame (x, y, z) using detector parameters.
 * v[0]=0 (beam direction), v[1]=fast offset, v[2]=slow offset.
 * Uses only columns 1 and 2 of rotation matrix r[9].
 * Takes flat double* (matches c2py23 .ptr).
 */

#include "cImageD11.h"
#include <math.h>

#ifndef KERNEL_FN
#define KERNEL_FN compute_xlylzl_sse42
#endif

void KERNEL_FN(const double *restrict s, const double *restrict f,
               const double *p, const double *r, const double *dist,
               double *restrict xlylzl, int n)
{
    double s_cen, f_cen, s_size, f_size, v[3];
    int i, j;

    s_cen = p[0];
    f_cen = p[1];
    s_size = p[2];
    f_size = p[3];
    (void)v[0];

#pragma omp parallel for private(v, j)
    for (i = 0; i < n; i++) {
        double *xyz = xlylzl + i * 3;
        v[1] = (f[i] - f_cen) * f_size;
        v[2] = (s[i] - s_cen) * s_size;
        for (j = 0; j < 3; j++)
            xyz[j] = r[3*j + 1]*v[1] + r[3*j + 2]*v[2] + dist[j];
    }
}
