#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_gv(xlylzl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, gv: buffer) -> void",
 *     "doc": "computes scattering vectors given thr positions of the spot\nin the laboratory in xlylzl[npks], the omega rotation[npks], and\nthe rest of the parameters (wedge,wvln,chi,t[3] and omegasign)",
 *     "params": {
 *         "xlylzl": "Spot positions in lab frame, (n,3) AoS or (3,n) SoA.",
 *         "omega": "Omega rotation per spot (radians), shape (n,).",
 *         "omegasign": "Omega rotation sign.",
 *         "wvln": "Wavelength (angstroms).",
 *         "wedge": "Wedge angle (radians).",
 *         "chi": "Chi angle (radians).",
 *         "t": "Translation vector (3 elements).",
 *         "gv": "Output g-vectors, (n,3) AoS or (3,n) SoA.",
 *     },
 *     "checks": ["xlylzl.ndim == 2",
 *         "t.n == 3",
 *         "gv.ndim == 2"],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "xlylzl.format == 'd' and omega.format == 'd' and gv.format == 'd' and xlylzl.shape[1] == 3 and xlylzl.slow_axis == 0",
 *         "sig": "void compute_gv(const double xlylzl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double gv[], intptr_t n)",
 *         "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gv": "gv.ptr", "n": "xlylzl.shape[0]"},
 *     }],
 * }
 C2PY_END */

void compute_gv(const double xlylzl[], const double omega[],
                double omegasign, double wvln, double wedge, double chi,
                const double t[3], double gv[], intptr_t n) {
    double sc, cc, sw, cw, wmat[9], cmat[9], mat[9], u[3], d[3], v[3];
    double modyz, o[3], co, so, ds, k[3];
    intptr_t i;
    /* AoS layout: [x0,y0,z0, x1,y1,z1, ...] */
    sw = sin(wedge * RAD);  cw = cos(wedge * RAD);
    wmat[0] = cw;  wmat[1] = 0.0; wmat[2] = -sw;
    wmat[3] = 0.; wmat[4] = 1.0; wmat[5] = 0.;
    wmat[6] = sw;  wmat[7] = 0.0; wmat[8] = cw;
    sc = sin(chi * RAD);   cc = cos(chi * RAD);
    cmat[0] = 1.; cmat[1] = 0.0; cmat[2] = 0.;
    cmat[3] = 0.; cmat[4] = cc;  cmat[5] = -sc;
    cmat[6] = 0.; cmat[7] = sc;  cmat[8] = cc;
    matmat(cmat, wmat, mat);
#pragma omp parallel for if(n > 5000) private(so, co, u, o, d, modyz, ds, v, k)
    for (i = 0; i < n; i++) {
        so = sin(RAD * omega[i] * omegasign);
        co = cos(RAD * omega[i] * omegasign);
        u[0] = co * t[0] - so * t[1];
        u[1] = so * t[0] + co * t[1];
        u[2] = t[2];
        matvec(mat, u, o);
        d[0] = xlylzl[i*3+0] - o[0];
        d[1] = xlylzl[i*3+1] - o[1];
        d[2] = xlylzl[i*3+2] - o[2];
        modyz = 1. / sqrt(d[0]*d[0] + d[1]*d[1] + d[2]*d[2]);
        ds = 1. / wvln;
        {
            double R = d[1]*d[1] + d[2]*d[2];
            k[0] = -ds * R * modyz / (d[0] + 1./modyz);
        }
        k[1] = ds * d[1] * modyz;
        k[2] = ds * d[2] * modyz;
        matTvec(mat, k, v);
        gv[i*3+0] =  co * v[0] + so * v[1];
        gv[i*3+1] = -so * v[0] + co * v[1];
        gv[i*3+2] = v[2];
    }
}
