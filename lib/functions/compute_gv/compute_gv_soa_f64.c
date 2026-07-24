#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_gv(xlylzl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, gv: buffer) -> void",
 *     "c_overloads": [{
 *         "when": "xlylzl.format == 'd' and omega.format == 'd' and gv.format == 'd' and xlylzl.shape[0] == 3 and xlylzl.slow_axis == 0 and xlylzl.shape[1] != 3",
 *         "sig": "void compute_gv_soa_f64(const double xlylzl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double gv[], intptr_t n)",
 *         "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gv": "gv.ptr", "n": "xlylzl.shape[1]"},
 *     }],
 * }
 C2PY_END */

void compute_gv_soa_f64(const double xlylzl[], const double omega[],
                         double omegasign, double wvln, double wedge, double chi,
                         const double t[3], double gv[], intptr_t n) {
    double sc, cc, sw, cw, wmat[9], cmat[9], mat[9], u[3], d[3], v[3];
    double modyz, o[3], co, so, ds, k[3];
    intptr_t i;
    const double *xl = xlylzl, *yl = xlylzl + n, *zl = xlylzl + 2*n;
    double *gx = gv, *gy = gv + n, *gz = gv + 2*n;
    sw = sin(wedge * RAD); cw = cos(wedge * RAD);
    wmat[0] = cw;  wmat[1] = 0.0; wmat[2] = -sw;
    wmat[3] = 0.;  wmat[4] = 1.0; wmat[5] = 0.;
    wmat[6] = sw;  wmat[7] = 0.0; wmat[8] = cw;
    sc = sin(chi * RAD); cc = cos(chi * RAD);
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
        d[0] = xl[i] - o[0]; d[1] = yl[i] - o[1]; d[2] = zl[i] - o[2];
        modyz = 1. / sqrt(d[0]*d[0] + d[1]*d[1] + d[2]*d[2]);
        ds = 1. / wvln;
        { double R = d[1]*d[1] + d[2]*d[2];
          k[0] = -ds * R * modyz / (d[0] + 1./modyz); }
        k[1] = ds * d[1] * modyz;
        k[2] = ds * d[2] * modyz;
        matTvec(mat, k, v);
        gx[i] =  co * v[0] + so * v[1];
        gy[i] = -so * v[0] + co * v[1];
        gz[i] = v[2];
    }
}
