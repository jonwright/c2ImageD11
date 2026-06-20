/* Auto-extracted from ImageD11/src/cdiffraction.c, function compute_geometry, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"
#include <math.h>
#include "cdiffraction.h"

void KERNEL_FN(double xlylzl[][3], double omega[], double omegasign,
                      double wvln, double wedge, double chi, double t[3],
                      double out[][6], int n) {
    double sc, cc, sw, cw, wmat[9], cmat[9], mat[9], u[3], d[3], v[3];
    double modyz, o[3], co, so, ds, k[3];
    int i;
    // ! Fill in rotation matrix of wedge, chi
    sw = sin(wedge * RAD);
    cw = cos(wedge * RAD);
    wmat[0] = cw;
    wmat[1] = 0.0;
    wmat[2] = -sw;
    wmat[3] = 0.;
    wmat[4] = 1.0;
    wmat[5] = 0.;
    wmat[6] = sw;
    wmat[7] = 0.0;
    wmat[8] = cw;
    sc = sin(chi * RAD);
    cc = cos(chi * RAD);
    cmat[0] = 1.;
    cmat[1] = 0.0;
    cmat[2] = 0.;
    cmat[3] = 0.;
    cmat[4] = cc;
    cmat[5] = -sc;
    cmat[6] = 0.;
    cmat[7] = sc;
    cmat[8] = cc;
    // Combined mat = chi.wedge
    matmat(cmat, wmat, mat);
#pragma omp parallel for private(so, co, u, o, d, modyz, ds, v, k)
    for (i = 0; i < n; i++) {
        // ! Compute translation + rotation for grain origin
        so = sin(RAD * omega[i] * omegasign);
        co = cos(RAD * omega[i] * omegasign);
        // Omega matrix vector on translation
        u[0] = co * t[0] - so * t[1];
        u[1] = so * t[0] + co * t[1];
        u[2] = t[2];
        // o=grain origin
        matvec(mat, u, o);
        // d is difference vector
        vec3sub(xlylzl[i], o, d);
        modyz = 1. / sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
        // two theta
        out[i][0] = DEG * atan2(sqrt(d[1] * d[1] + d[2] * d[2]), d[0]);
        //     ! k-vector
        ds = 1. / wvln;
        k[0] = ds * (d[0] * modyz - 1.);
        k[1] = ds * d[1] * modyz;
        k[2] = ds * d[2] * modyz;
        // eta
        out[i][1] = DEG * atan2(-d[1], d[2]);
        // dstar
        out[i][2] = sqrt(k[0] * k[0] + k[1] * k[1] + k[2] * k[2]);
        // g-vector
        matTvec(mat, k, v);
        // Forwards rotation with omega finally
        out[i][3] = co * v[0] + so * v[1];
        out[i][4] = -so * v[0] + co * v[1];
        out[i][5] = v[2];
    } //  enddo
} // end subroutine compute_geometry
