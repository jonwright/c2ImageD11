#include "compute_geometry_soa.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_geometry_soa(xl: buffer, yl: buffer, zl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, tth: buffer, eta: buffer, ds: buffer, gx: buffer, gy: buffer, gz: buffer) -> void",
 *     "c_overloads": [{
 *         "when": "xl.format == 'f' and yl.format == 'f' and zl.format == 'f' and omega.format == 'f' and tth.format == 'f' and eta.format == 'f' and ds.format == 'f' and gx.format == 'f' and gy.format == 'f' and gz.format == 'f' and xl.n == yl.n and yl.n == zl.n and zl.n == omega.n and omega.n == tth.n and tth.n == eta.n and eta.n == ds.n and ds.n == gx.n and gx.n == gy.n and gy.n == gz.n",
 *         "sig": "void compute_geometry_soa_split_f32(const float xl[], const float yl[], const float zl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float tth[], float eta[], float ds[], float gx[], float gy[], float gz[], intptr_t n)",
 *         "map": {"xl": "xl.ptr", "yl": "yl.ptr", "zl": "zl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "tth": "tth.ptr", "eta": "eta.ptr", "ds": "ds.ptr", "gx": "gx.ptr", "gy": "gy.ptr", "gz": "gz.ptr", "n": "xl.n"},
 *     }],
 * }
 C2PY_END */

extern "C" void compute_geometry_soa_split_f32(const float xl[], const float yl[],
                                                 const float zl[], const float omega[],
                                                 double omegasign, double wvln,
                                                 double wedge, double chi,
                                                 const float t[3],
                                                 float tth[], float eta[], float ds[],
                                                 float gx[], float gy[], float gz[],
                                                 intptr_t n) {
    compute_geometry_soa_kernel<float>(xl, yl, zl, omega,
                                        omegasign, wvln, wedge, chi, t,
                                        tth, eta, ds, gx, gy, gz, n);
}
