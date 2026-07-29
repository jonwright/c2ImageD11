#include "compute_gv_soa.hpp"

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

extern "C" void compute_gv_soa_f64(const double xlylzl[], const double omega[],
                                    double omegasign, double wvln,
                                    double wedge, double chi,
                                    const double t[3], double gv[], intptr_t n) {
    compute_gv_soa_impl<double>(xlylzl, omega, omegasign, wvln, wedge, chi, t, gv, n);
}
