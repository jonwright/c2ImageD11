#include "compute_gv.hpp"
#include "compute_gv_soa.hpp"

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
 *     "c_overloads": [
 *         {
 *             "when": "xlylzl.format == 'd' and omega.format == 'd' and gv.format == 'd' and xlylzl.shape[1] == 3 and xlylzl.slow_axis == 0",
 *             "sig": "void compute_gv(const double xlylzl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double gv[], intptr_t n)"
 *             "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gv": "gv.ptr", "n": "xlylzl.shape[0]"},
 *         },
 *         {
 *             "when": "xlylzl.format == 'f' and omega.format == 'f' and gv.format == 'f' and xlylzl.shape[1] == 3 and xlylzl.slow_axis == 0",
 *             "sig": "void compute_gv_f32(const float xlylzl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float gv[], intptr_t n)",
 *             "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gv": "gv.ptr", "n": "xlylzl.shape[0]"},
 *         },
 *         {
 *             "when": "xlylzl.format == 'd' and omega.format == 'd' and gv.format == 'd' and xlylzl.shape[0] == 3 and xlylzl.slow_axis == 0 and xlylzl.shape[1] != 3",
 *             "sig": "void compute_gv_soa_f64(const double xlylzl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double gv[], intptr_t n)",
 *             "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gv": "gv.ptr", "n": "xlylzl.shape[1]"},
 *         },
 *         {
 *             "when": "xlylzl.format == 'f' and omega.format == 'f' and gv.format == 'f' and xlylzl.shape[0] == 3 and xlylzl.slow_axis == 0 and xlylzl.shape[1] != 3",
 *             "sig": "void compute_gv_soa_f32(const float xlylzl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float gv[], intptr_t n)",
 *             "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gv": "gv.ptr", "n": "xlylzl.shape[1]"},
 *         }
 *     ],
 * }
 C2PY_END */

extern "C" void compute_gv(const double xlylzl[], const double omega[],
                double omegasign, double wvln, double wedge, double chi,
                const double t[3], double gv[], intptr_t n) {
    compute_gv_aos_impl<double>(xlylzl, omega, omegasign, wvln, wedge, chi, t, gv, n);
}

extern "C" void compute_gv_f32(const float xlylzl[], const float omega[],
                                double omegasign, double wvln,
                                double wedge, double chi,
                                const float t[3], float gv[], intptr_t n) {
    compute_gv_aos_impl<float>(xlylzl, omega, omegasign, wvln, wedge, chi, t, gv, n);
}

extern "C" void compute_gv_soa_f64(const double xlylzl[], const double omega[],
                                    double omegasign, double wvln,
                                    double wedge, double chi,
                                    const double t[3], double gv[], intptr_t n) {
    compute_gv_soa_kernel<double>(xlylzl, xlylzl + n, xlylzl + 2*n,
                                   omega, omegasign, wvln, wedge, chi, t,
                                   gv, gv + n, gv + 2*n, n);
}

extern "C" void compute_gv_soa_f32(const float xlylzl[], const float omega[],
                                    double omegasign, double wvln,
                                    double wedge, double chi,
                                    const float t[3], float gv[], intptr_t n) {
    compute_gv_soa_kernel<float>(xlylzl, xlylzl + n, xlylzl + 2*n,
                                  omega, omegasign, wvln, wedge, chi, t,
                                  gv, gv + n, gv + 2*n, n);
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_gv_soa(xl: buffer, yl: buffer, zl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, gx: buffer, gy: buffer, gz: buffer) -> void",
 *     "c_overloads": [
 *         {
 *             "when": "xl.format == 'd' and yl.format == 'd' and zl.format == 'd' and omega.format == 'd' and gx.format == 'd' and gy.format == 'd' and gz.format == 'd' and xl.n == yl.n and yl.n == zl.n and zl.n == omega.n and omega.n == gx.n and gx.n == gy.n and gy.n == gz.n",
 *             "sig": "void compute_gv_soa_split_f64(const double xl[], const double yl[], const double zl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double gx[], double gy[], double gz[], intptr_t n)",
 *             "map": {"xl": "xl.ptr", "yl": "yl.ptr", "zl": "zl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gx": "gx.ptr", "gy": "gy.ptr", "gz": "gz.ptr", "n": "xl.n"},
 *         },
 *         {
 *             "when": "xl.format == 'f' and yl.format == 'f' and zl.format == 'f' and omega.format == 'f' and gx.format == 'f' and gy.format == 'f' and gz.format == 'f' and xl.n == yl.n and yl.n == zl.n and zl.n == omega.n and omega.n == gx.n and gx.n == gy.n and gy.n == gz.n",
 *             "sig": "void compute_gv_soa_split_f32(const float xl[], const float yl[], const float zl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float gx[], float gy[], float gz[], intptr_t n)",
 *             "map": {"xl": "xl.ptr", "yl": "yl.ptr", "zl": "zl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "gx": "gx.ptr", "gy": "gy.ptr", "gz": "gz.ptr", "n": "xl.n"},
 *         }
 *     ],
 * }
 C2PY_END */

extern "C" void compute_gv_soa_split_f64(const double xl[], const double yl[],
                                          const double zl[], const double omega[],
                                          double omegasign, double wvln,
                                          double wedge, double chi,
                                          const double t[3],
                                          double gx[], double gy[], double gz[],
                                          intptr_t n) {
    compute_gv_soa_kernel<double>(xl, yl, zl, omega,
                                   omegasign, wvln, wedge, chi, t,
                                   gx, gy, gz, n);
}

extern "C" void compute_gv_soa_split_f32(const float xl[], const float yl[],
                                          const float zl[], const float omega[],
                                          double omegasign, double wvln,
                                          double wedge, double chi,
                                          const float t[3],
                                          float gx[], float gy[], float gz[],
                                          intptr_t n) {
    compute_gv_soa_kernel<float>(xl, yl, zl, omega,
                                  omegasign, wvln, wedge, chi, t,
                                  gx, gy, gz, n);
}
