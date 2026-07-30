#include "compute_geometry_soa.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_geometry(xlylzl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, out: buffer) -> void",
 *     "c_overloads": [{
 *         "when": "xlylzl.format == 'f' and omega.format == 'f' and out.format == 'f' and xlylzl.shape[0] == 3 and xlylzl.slow_axis == 0 and xlylzl.shape[1] != 3",
 *         "sig": "void compute_geometry_soa_f32(const float xlylzl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float out[], intptr_t n)",
 *         "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "out": "out.ptr", "n": "xlylzl.shape[1]"},
 *     }],
 * }
 C2PY_END */

extern "C" void compute_geometry_soa_f32(const float xlylzl[], const float omega[],
                                          double omegasign, double wvln,
                                          double wedge, double chi,
                                          const float t[3], float out[], intptr_t n) {
    compute_geometry_soa_kernel<float>(xlylzl, xlylzl + n, xlylzl + 2*n,
                                        omega, omegasign, wvln, wedge, chi, t,
                                        out, out + n, out + 2*n,
                                        out + 3*n, out + 4*n, out + 5*n, n);
}
