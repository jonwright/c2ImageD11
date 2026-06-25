#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_gv(xlylzl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, gv: buffer) -> void",
 *     "doc": "compute_gv computes scattering vectors given spot positions in the laboratory frame.",
 *     "params": {
 *         "xlylzl": "Spot positions in laboratory frame, shape (n, 3).",
 *         "omega": "Omega rotation per spot (radians), shape (n,).",
 *         "omegasign": "Omega rotation sign.",
 *         "wvln": "Wavelength (angstroms).",
 *         "wedge": "Wedge angle (radians).",
 *         "chi": "Chi angle (radians).",
 *         "t": "Translation vector (3 elements).",
 *         "gv": "Output g-vectors array, shape (n, 3).",
 *     },
 *     "checks": ["xlylzl.format == 'd'", "xlylzl.ndim == 2", "xlylzl.shape[1] == 3",
 *         "omega.format == 'd'", "omega.n == xlylzl.shape[0]",
 *         "t.format == 'd'", "t.n == 3",
 *         "gv.format == 'd'", "gv.ndim == 2", "gv.shape[0] == xlylzl.shape[0]", "gv.shape[1] == 3"],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "xlylzl.format == 'd' and omega.format == 'd' and gv.format == 'd'",
 *         "sig": "void compute_gv(const double xlylzl[][3], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double gv[][3], intptr_t n)",
 *         "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gv": "gv.ptr", "n": "xlylzl.shape[0]"},
 *     }],
 * }
C2PY_END */

void compute_gv(const double xlylzl[][3], const double omega[], double omegasign,
                double wvln, double wedge, double chi, const double t[3],
                double gv[][3], intptr_t n) {
    double sc, cc, sw, cw, wmat[9], cmat[9], mat[9], u[3], d[3], v[3];
    double modyz, o[3], co, so, ds, k[3];
    intptr_t i;
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
#pragma omp parallel for if(n > 5000) private(so, co, u, o, d, modyz, ds, v, k)
    for (i = 0; i < n; i++) {
        // ! Compute translation + rotation for grain origin
        so = sin(RAD * omega[i] * omegasign);
        co = cos(RAD * omega[i] * omegasign);
        // Omega matrix vector on translation
        u[0] = co * t[0] - so * t[1];
        u[1] = so * t[0] + co * t[1];
        u[2] = t[2];
        // grain origin, difference vec, |yz| component
        matvec(mat, u, o);
        // d is difference vector
        vec3sub(xlylzl[i], o, d);
        modyz = 1. / sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
        //     ! k-vector
        ds = 1. / wvln;
        k[0] = ds * (d[0] * modyz - 1.);
        k[1] = ds * d[1] * modyz;
        k[2] = ds * d[2] * modyz;
        matTvec(mat, k, v);
        // Forwards rotation with omega finally
        gv[i][0] = co * v[0] + so * v[1];
        gv[i][1] = -so * v[0] + co * v[1];
        gv[i][2] = v[2];
    } //  enddo
} // end subroutine compute_gv
