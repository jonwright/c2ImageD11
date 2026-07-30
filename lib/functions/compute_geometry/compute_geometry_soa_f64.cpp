#include "compute_geometry_soa.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_geometry(xlylzl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, out: buffer) -> void",
 *     "c_overloads": [{
 *         "when": "xlylzl.format == 'd' and omega.format == 'd' and out.format == 'd' and xlylzl.shape[0] == 3 and xlylzl.slow_axis == 0 and xlylzl.shape[1] != 3",
 *         "sig": "void compute_geometry_soa_f64(const double xlylzl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double out[], intptr_t n)",
 *         "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "out": "out.ptr", "n": "xlylzl.shape[1]"},
 *     }],
 * }
 C2PY_END */

extern "C" void compute_geometry_soa_f64(const double xlylzl[], const double omega[],
                                          double omegasign, double wvln,
                                          double wedge, double chi,
                                          const double t[3], double out[], intptr_t n) {
    compute_geometry_soa_kernel<double>(xlylzl, xlylzl + n, xlylzl + 2*n,
                                         omega, omegasign, wvln, wedge, chi, t,
                                         out, out + n, out + 2*n,
                                         out + 3*n, out + 4*n, out + 5*n, n);
}
