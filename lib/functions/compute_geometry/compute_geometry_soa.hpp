#ifndef COMPUTE_GEOMETRY_SOA_HPP
#define COMPUTE_GEOMETRY_SOA_HPP

#include <cmath>
#include <cstdint>
#include "ImageD11_cmath.h"

template<typename T>
static void compute_geometry_soa_impl(const T xlylzl[], const T omega[],
                                       double omegasign, double wvln,
                                       double wedge, double chi,
                                       const T t[3], T out[], intptr_t n) {
    T sw, cw, wmat[9], cmat[9], mat[9], u[3], d[3], v[3];
    T modyz, o[3], co, so, ds, k[3];
    intptr_t i;
    const T *xl = xlylzl, *yl = xlylzl + n, *zl = xlylzl + 2*n;
    T *tth = out, *eta = out + n, *ds_out = out + 2*n;
    T *gx = out + 3*n, *gy = out + 4*n, *gz = out + 5*n;
    sw = std::sin(T(wedge * RAD));
    cw = std::cos(T(wedge * RAD));
    wmat[0] = cw;  wmat[1] = 0; wmat[2] = -sw;
    wmat[3] = 0;   wmat[4] = 1; wmat[5] = 0;
    wmat[6] = sw;  wmat[7] = 0; wmat[8] = cw;
    { T sc = std::sin(T(chi * RAD));
      T cc = std::cos(T(chi * RAD));
      cmat[0] = 1; cmat[1] = 0; cmat[2] = 0;
      cmat[3] = 0; cmat[4] = cc; cmat[5] = -sc;
      cmat[6] = 0; cmat[7] = sc; cmat[8] = cc; }
    matmat(cmat, wmat, mat);
#pragma omp parallel for if(n > 5000) private(so, co, u, o, d, modyz, ds, v, k)
    for (i = 0; i < n; i++) {
        so = std::sin(T(RAD * omega[i] * omegasign));
        co = std::cos(T(RAD * omega[i] * omegasign));
        u[0] = co * t[0] - so * t[1];
        u[1] = so * t[0] + co * t[1];
        u[2] = t[2];
        matvec(mat, u, o);
        d[0] = xl[i] - o[0]; d[1] = yl[i] - o[1]; d[2] = zl[i] - o[2];
        { T R = d[1]*d[1] + d[2]*d[2];
          modyz = T(1) / std::sqrt(d[0]*d[0] + R);
          tth[i] = T(DEG) * std::atan2(std::sqrt(R), d[0]);
          ds = T(1.0 / wvln);
          k[0] = -ds * R * modyz / (d[0] + T(1)/modyz);
          k[1] = ds * d[1] * modyz;
          k[2] = ds * d[2] * modyz; }
        eta[i] = T(DEG) * std::atan2(-d[1], d[2]);
        ds_out[i] = std::sqrt(k[0]*k[0] + k[1]*k[1] + k[2]*k[2]);
        matTvec(mat, k, v);
        gx[i] =  co * v[0] + so * v[1];
        gy[i] = -so * v[0] + co * v[1];
        gz[i] = v[2];
    }
}

#endif
