#include "compute_geometry_soa.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_geometry_soa(xl: buffer, yl: buffer, zl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, tth: buffer, eta: buffer, ds: buffer, gx: buffer, gy: buffer, gz: buffer) -> void",
 *     "c_overloads": [{
 *         "when": "xl.format == 'd' and yl.format == 'd' and zl.format == 'd' and omega.format == 'd' and tth.format == 'd' and eta.format == 'd' and ds.format == 'd' and gx.format == 'd' and gy.format == 'd' and gz.format == 'd' and xl.n == yl.n and yl.n == zl.n and zl.n == omega.n and omega.n == tth.n and tth.n == eta.n and eta.n == ds.n and ds.n == gx.n and gx.n == gy.n and gy.n == gz.n",
 *         "sig": "void compute_geometry_soa_split_f64(const double xl[], const double yl[], const double zl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double tth[], double eta[], double ds[], double gx[], double gy[], double gz[], intptr_t n)",
 *         "map": {"xl": "xl.ptr", "yl": "yl.ptr", "zl": "zl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "tth": "tth.ptr", "eta": "eta.ptr", "ds": "ds.ptr", "gx": "gx.ptr", "gy": "gy.ptr", "gz": "gz.ptr", "n": "xl.n"},
 *     }],
 * }
 C2PY_END */

extern "C" void compute_geometry_soa_split_f64(const double xl[], const double yl[],
                                                 const double zl[], const double omega[],
                                                 double omegasign, double wvln,
                                                 double wedge, double chi,
                                                 const double t[3],
                                                 double tth[], double eta[], double ds[],
                                                 double gx[], double gy[], double gz[],
                                                 intptr_t n) {
    compute_geometry_soa_kernel<double>(xl, yl, zl, omega,
                                         omegasign, wvln, wedge, chi, t,
                                         tth, eta, ds, gx, gy, gz, n);
}
