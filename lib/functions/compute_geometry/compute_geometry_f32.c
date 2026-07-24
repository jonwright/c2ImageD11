#include "cImageD11.h"
#include "ImageD11_cmath.h"
#include <math.h>

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_geometry(xlylzl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, out: buffer) -> void",
 *     "c_overloads": [{
 *         "when": "xlylzl.format == 'f' and omega.format == 'f' and out.format == 'f' and xlylzl.shape[1] == 3 and xlylzl.slow_axis == 0",
 *         "sig": "void compute_geometry_f32(const float xlylzl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float out[], intptr_t n)",
 *         "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "out": "out.ptr", "n": "xlylzl.shape[0]"},
 *     }],
 * }
 C2PY_END */

void compute_geometry_f32(const float xlylzl[], const float omega[],
                           double omegasign, double wvln, double wedge, double chi,
                           const float t[3], float out[], intptr_t n) {
    float sw, cw, wmat[9], cmat[9], mat[9], u[3], d[3], v[3];
    float modyz, o[3], co, so, ds, k[3];
    intptr_t i;
    sw = sinf((float)(wedge * RAD));
    cw = cosf((float)(wedge * RAD));
    wmat[0] = cw;  wmat[1] = 0.0f; wmat[2] = -sw;
    wmat[3] = 0.f; wmat[4] = 1.0f; wmat[5] = 0.f;
    wmat[6] = sw;  wmat[7] = 0.0f; wmat[8] = cw;
    {
        float sc = sinf((float)(chi * RAD));
        float cc = cosf((float)(chi * RAD));
        cmat[0] = 1.f;  cmat[1] = 0.0f; cmat[2] = 0.f;
        cmat[3] = 0.f;  cmat[4] = cc;   cmat[5] = -sc;
        cmat[6] = 0.f;  cmat[7] = sc;   cmat[8] = cc;
    }
    matmat(cmat, wmat, mat);
#pragma omp parallel for if(n > 5000) private(so, co, u, o, d, modyz, ds, v, k)
    for (i = 0; i < n; i++) {
        so = sinf((float)(RAD * omega[i] * omegasign));
        co = cosf((float)(RAD * omega[i] * omegasign));
        u[0] = co * t[0] - so * t[1];
        u[1] = so * t[0] + co * t[1];
        u[2] = t[2];
        matvec(mat, u, o);
        d[0] = xlylzl[i*3+0] - o[0]; d[1] = xlylzl[i*3+1] - o[1]; d[2] = xlylzl[i*3+2] - o[2];
        {
            float R = d[1]*d[1] + d[2]*d[2];
            modyz = 1.f / sqrtf(d[0]*d[0] + R);
            out[i*6+0] = (float)(DEG * atan2f(sqrtf(R), d[0]));
            ds = (float)(1. / wvln);
            k[0] = -ds * R * modyz / (d[0] + 1.f/modyz);
            k[1] = ds * d[1] * modyz;
            k[2] = ds * d[2] * modyz;
        }
        out[i*6+1] = (float)(DEG * atan2f(-d[1], d[2]));
        out[i*6+2] = sqrtf(k[0]*k[0] + k[1]*k[1] + k[2]*k[2]);
        matTvec(mat, k, v);
        out[i*6+3] = co * v[0] + so * v[1];
        out[i*6+4] = -so * v[0] + co * v[1];
        out[i*6+5] = v[2];
    }
}
