#include "compute_geometry.hpp"
#include "compute_geometry_soa.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_geometry(xlylzl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, out: buffer) -> void",
 *     "doc": "is for the \"updateGeometry\" method of columnfiles\nfrom xlylzl it will compute tth, eta, ds, gve into out\nin the laboratory in xlylzl[npks], the omega rotation[npks], and\nthe rest of the parameters (wedge,wvln,chi,t[3] and omegasign)\nout should contain : (tth, eta, ds, gx, gy, gz)",
 *     "params": {
 *         "xlylzl": "Spot positions in lab frame, (n,3) AoS or (3,n) SoA.",
 *         "omega": "Omega rotation per spot (radians), shape (n,).",
 *         "omegasign": "Omega rotation sign (+1 or -1).",
 *         "wvln": "Wavelength (angstroms).",
 *         "wedge": "Wedge angle (detector tilt, radians).",
 *         "chi": "Chi angle (radians).",
 *         "t": "Translation vector (3 elements).",
 *         "out": "Output (n,6) AoS or (6,n) SoA: tth, eta, ds, gx, gy, gz.",
 *     },
 *     "checks": ["xlylzl.ndim == 2",
 *         "t.n == 3",
 *         "out.ndim == 2"],
 *     "gil_release": true,
 *     "c_overloads": [
 *         {
 *             "when": "xlylzl.format == 'd' and omega.format == 'd' and out.format == 'd' and xlylzl.shape[1] == 3 and xlylzl.slow_axis == 0",
 *             "sig": "void compute_geometry(const double xlylzl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double out[], intptr_t n)",
 *             "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "out": "out.ptr", "n": "xlylzl.shape[0]"},
 *         },
 *         {
 *             "when": "xlylzl.format == 'f' and omega.format == 'f' and out.format == 'f' and xlylzl.shape[1] == 3 and xlylzl.slow_axis == 0",
 *             "sig": "void compute_geometry_f32(const float xlylzl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float out[], intptr_t n)",
 *             "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "out": "out.ptr", "n": "xlylzl.shape[0]"},
 *         },
 *         {
 *             "when": "xlylzl.format == 'd' and omega.format == 'd' and out.format == 'd' and xlylzl.shape[0] == 3 and xlylzl.slow_axis == 0 and xlylzl.shape[1] != 3",
 *             "sig": "void compute_geometry_soa_f64(const double xlylzl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double out[], intptr_t n)",
 *             "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "out": "out.ptr", "n": "xlylzl.shape[1]"},
 *         },
 *         {
 *             "when": "xlylzl.format == 'f' and omega.format == 'f' and out.format == 'f' and xlylzl.shape[0] == 3 and xlylzl.slow_axis == 0 and xlylzl.shape[1] != 3",
 *             "sig": "void compute_geometry_soa_f32(const float xlylzl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float out[], intptr_t n)",
 *             "map": {"xlylzl": "xlylzl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "out": "out.ptr", "n": "xlylzl.shape[1]"},
 *         }
 *     ],
 * }
 C2PY_END */

extern "C" void compute_geometry(const double xlylzl[], const double omega[], double omegasign,
                      double wvln, double wedge, double chi, const double t[3],
                      double out[], intptr_t n) {
    compute_geometry_aos_impl<double>(xlylzl, omega, omegasign, wvln, wedge, chi, t, out, n);
}

extern "C" void compute_geometry_f32(const float xlylzl[], const float omega[],
                                      double omegasign, double wvln,
                                      double wedge, double chi,
                                      const float t[3], float out[], intptr_t n) {
    compute_geometry_aos_impl<float>(xlylzl, omega, omegasign, wvln, wedge, chi, t, out, n);
}

extern "C" void compute_geometry_soa_f64(const double xlylzl[], const double omega[],
                                          double omegasign, double wvln,
                                          double wedge, double chi,
                                          const double t[3], double out[], intptr_t n) {
    compute_geometry_soa_kernel<double>(xlylzl, xlylzl + n, xlylzl + 2*n,
                                         omega, omegasign, wvln, wedge, chi, t,
                                         out, out + n, out + 2*n,
                                         out + 3*n, out + 4*n, out + 5*n, n);
}

extern "C" void compute_geometry_soa_f32(const float xlylzl[], const float omega[],
                                          double omegasign, double wvln,
                                          double wedge, double chi,
                                          const float t[3], float out[], intptr_t n) {
    compute_geometry_soa_kernel<float>(xlylzl, xlylzl + n, xlylzl + 2*n,
                                        omega, omegasign, wvln, wedge, chi, t,
                                        out, out + n, out + 2*n,
                                        out + 3*n, out + 4*n, out + 5*n, n);
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "compute_geometry_soa(xl: buffer, yl: buffer, zl: buffer, omega: buffer, omegasign: float, wvln: float, wedge: float, chi: float, t: buffer, tth: buffer, eta: buffer, ds: buffer, gx: buffer, gy: buffer, gz: buffer) -> void",
 *     "c_overloads": [
 *         {
 *             "when": "xl.format == 'd' and yl.format == 'd' and zl.format == 'd' and omega.format == 'd' and tth.format == 'd' and eta.format == 'd' and ds.format == 'd' and gx.format == 'd' and gy.format == 'd' and gz.format == 'd' and xl.n == yl.n and yl.n == zl.n and zl.n == omega.n and omega.n == tth.n and tth.n == eta.n and eta.n == ds.n and ds.n == gx.n and gx.n == gy.n and gy.n == gz.n",
 *             "sig": "void compute_geometry_soa_split_f64(const double xl[], const double yl[], const double zl[], const double omega[], double omegasign, double wvln, double wedge, double chi, const double t[3], double tth[], double eta[], double ds[], double gx[], double gy[], double gz[], intptr_t n)",
 *             "map": {"xl": "xl.ptr", "yl": "yl.ptr", "zl": "zl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "tth": "tth.ptr", "eta": "eta.ptr", "ds": "ds.ptr", "gx": "gx.ptr", "gy": "gy.ptr", "gz": "gz.ptr", "n": "xl.n"},
 *         },
 *         {
 *             "when": "xl.format == 'f' and yl.format == 'f' and zl.format == 'f' and omega.format == 'f' and tth.format == 'f' and eta.format == 'f' and ds.format == 'f' and gx.format == 'f' and gy.format == 'f' and gz.format == 'f' and xl.n == yl.n and yl.n == zl.n and zl.n == omega.n and omega.n == tth.n and tth.n == eta.n and eta.n == ds.n and ds.n == gx.n and gx.n == gy.n and gy.n == gz.n",
 *             "sig": "void compute_geometry_soa_split_f32(const float xl[], const float yl[], const float zl[], const float omega[], double omegasign, double wvln, double wedge, double chi, const float t[3], float tth[], float eta[], float ds[], float gx[], float gy[], float gz[], intptr_t n)",
 *             "map": {"xl": "xl.ptr", "yl": "yl.ptr", "zl": "zl.ptr", "omega": "omega.ptr", "omegasign": "omegasign", "wvln": "wvln", "wedge": "wedge", "chi": "chi", "t": "t.ptr", "tth": "tth.ptr", "eta": "eta.ptr", "ds": "ds.ptr", "gx": "gx.ptr", "gy": "gy.ptr", "gz": "gz.ptr", "n": "xl.n"},
 *         }
 *     ],
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
