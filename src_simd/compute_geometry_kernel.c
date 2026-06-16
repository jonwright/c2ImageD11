/* compute_geometry_kernel.c -- SIMD kernel for compute_geometry()
 *
 * Computes tth, eta, ds, gx, gy, gz for each peak in laboratory frame.
 * Takes flat double* (matches c2py23 .ptr) instead of double[][3].
 */

#include "cImageD11.h"
#include <math.h>

#ifndef KERNEL_FN
#define KERNEL_FN compute_geometry_sse42
#endif

#define PI 3.14159265358979323846
#define RAD (PI / 180.0)
#define DEG (180.0 / PI)

static void matvec(const double *a, const double *b, double *c)
{
    c[0] = a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
    c[1] = a[3]*b[0] + a[4]*b[1] + a[5]*b[2];
    c[2] = a[6]*b[0] + a[7]*b[1] + a[8]*b[2];
}

static void matTvec(const double *a, const double *b, double *c)
{
    c[0] = a[0]*b[0] + a[3]*b[1] + a[6]*b[2];
    c[1] = a[1]*b[0] + a[4]*b[1] + a[7]*b[2];
    c[2] = a[2]*b[0] + a[5]*b[1] + a[8]*b[2];
}

void KERNEL_FN(const double *restrict xlylzl, const double *restrict omega,
               double omegasign, double wvln, double wedge, double chi,
               const double *t, double *restrict out, int n)
{
    double sw, cw, sc, cc, wmat[9], cmat[9], mat[9];
    double u[3], d[3], v[3], o[3], k[3];
    double modyz, co, so, ds;
    int i;

    sw = sin(wedge * RAD);
    cw = cos(wedge * RAD);
    wmat[0] = cw;   wmat[1] = 0.0;  wmat[2] = -sw;
    wmat[3] = 0.0;  wmat[4] = 1.0;  wmat[5] = 0.0;
    wmat[6] = sw;   wmat[7] = 0.0;  wmat[8] = cw;

    sc = sin(chi * RAD);
    cc = cos(chi * RAD);
    cmat[0] = 1.0;  cmat[1] = 0.0;  cmat[2] = 0.0;
    cmat[3] = 0.0;  cmat[4] = cc;   cmat[5] = -sc;
    cmat[6] = 0.0;  cmat[7] = sc;   cmat[8] = cc;

    mat[0] = cmat[0]*wmat[0] + cmat[3]*wmat[1] + cmat[6]*wmat[2];
    mat[1] = cmat[1]*wmat[0] + cmat[4]*wmat[1] + cmat[7]*wmat[2];
    mat[2] = cmat[2]*wmat[0] + cmat[5]*wmat[1] + cmat[8]*wmat[2];
    mat[3] = cmat[0]*wmat[3] + cmat[3]*wmat[4] + cmat[6]*wmat[5];
    mat[4] = cmat[1]*wmat[3] + cmat[4]*wmat[4] + cmat[7]*wmat[5];
    mat[5] = cmat[2]*wmat[3] + cmat[5]*wmat[4] + cmat[8]*wmat[5];
    mat[6] = cmat[0]*wmat[6] + cmat[3]*wmat[7] + cmat[6]*wmat[8];
    mat[7] = cmat[1]*wmat[6] + cmat[4]*wmat[7] + cmat[7]*wmat[8];
    mat[8] = cmat[2]*wmat[6] + cmat[5]*wmat[7] + cmat[8]*wmat[8];

    ds = 1.0 / wvln;

#pragma omp parallel for private(so, co, u, o, d, modyz, v, k)
    for (i = 0; i < n; i++) {
        const double *xyz = xlylzl + i * 3;
        double *outi = out + i * 6;

        so = sin(RAD * omega[i] * omegasign);
        co = cos(RAD * omega[i] * omegasign);

        u[0] = co * t[0] - so * t[1];
        u[1] = so * t[0] + co * t[1];
        u[2] = t[2];

        matvec(mat, u, o);

        d[0] = xyz[0] - o[0];
        d[1] = xyz[1] - o[1];
        d[2] = xyz[2] - o[2];
        modyz = 1.0 / sqrt(d[0]*d[0] + d[1]*d[1] + d[2]*d[2]);

        outi[0] = DEG * atan2(sqrt(d[1]*d[1] + d[2]*d[2]), d[0]);

        k[0] = ds * (d[0] * modyz - 1.0);
        k[1] = ds * d[1] * modyz;
        k[2] = ds * d[2] * modyz;

        outi[1] = DEG * atan2(-d[1], d[2]);
        outi[2] = sqrt(k[0]*k[0] + k[1]*k[1] + k[2]*k[2]);

        matTvec(mat, k, v);

        outi[3] = co * v[0] + so * v[1];
        outi[4] = -so * v[0] + co * v[1];
        outi[5] = v[2];
    }
}
