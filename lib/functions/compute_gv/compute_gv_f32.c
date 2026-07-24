#include "cImageD11.h"
#include "ImageD11_cmath.h"
#include <math.h>

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_gv(xlylzl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, gv: buffer) -> void",
 *     "c_overloads": [{
 *         "when": "xlylzl.format == 'f' and omega.format == 'f' and gv.format == 'f' and xlylzl.shape[1] == 3 and xlylzl.slow_axis == 0",
 *         "sig": "void compute_gv_f32(const float xlylzl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float gv[], intptr_t n)",
 *         "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gv": "gv.ptr", "n": "xlylzl.shape[0]"},
 *     }],
 * }
 C2PY_END */

void compute_gv_f32(const float xlylzl[], const float omega[],
                     double omegasign, double wvln, double wedge, double chi,
                     const float t[3], float gv[], intptr_t n) {
    float sw, cw, wmat[9], cmat[9], mat[9], u[3], d[3], v[3];
    float modyz, o[3], co, so, ds, k[3];
    intptr_t i;
    /* AoS layout: [x0,y0,z0, x1,y1,z1, ...] */
    sw = sinf((float)(wedge * RAD)); cw = cosf((float)(wedge * RAD));
    wmat[0] = cw;  wmat[1] = 0.f; wmat[2] = -sw;
    wmat[3] = 0.f; wmat[4] = 1.f; wmat[5] = 0.f;
    wmat[6] = sw;  wmat[7] = 0.f; wmat[8] = cw;
    { float sc = sinf((float)(chi * RAD)); float cc = cosf((float)(chi * RAD));
      cmat[0] = 1.f; cmat[1] = 0.f; cmat[2] = 0.f;
      cmat[3] = 0.f; cmat[4] = cc;  cmat[5] = -sc;
      cmat[6] = 0.f; cmat[7] = sc;  cmat[8] = cc; }
    matmat(cmat, wmat, mat);
#pragma omp parallel for if(n > 5000) private(so, co, u, o, d, modyz, ds, v, k)
    for (i = 0; i < n; i++) {
        so = sinf((float)(RAD * omega[i] * omegasign));
        co = cosf((float)(RAD * omega[i] * omegasign));
        u[0] = co * t[0] - so * t[1];
        u[1] = so * t[0] + co * t[1];
        u[2] = t[2];
        matvec(mat, u, o);
        d[0] = xlylzl[i*3+0] - o[0]; d[1] = xlylzl[i*3+1] - o[1];
        d[2] = xlylzl[i*3+2] - o[2];
        modyz = 1.f / sqrtf(d[0]*d[0] + d[1]*d[1] + d[2]*d[2]);
        ds = (float)(1. / wvln);
        { float R = d[1]*d[1] + d[2]*d[2];
          k[0] = -ds * R * modyz / (d[0] + 1.f/modyz); }
        k[1] = ds * d[1] * modyz;
        k[2] = ds * d[2] * modyz;
        matTvec(mat, k, v);
        gv[i*3+0] =  co * v[0] + so * v[1];
        gv[i*3+1] = -so * v[0] + co * v[1];
        gv[i*3+2] = v[2];
    }
}
