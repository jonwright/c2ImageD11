/* score_and_refine_f64_soa.cpp — f64 SoA baseline variant */
#define SAR_SOA
#define SAR_IMPL_NAME score_and_refine_impl_f64_soa
#include "score_and_refine.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine_soa(ubi: buffer, gvx: buffer, gvy: buffer, gvz: buffer, tol: float) -> int",
 *     "doc": "SoA variant: gvx,gvy,gvz are separate 1D arrays (ng,).",
 *     "params": {
 *         "ubi": "Orientation matrix UBI (9-element flattened double).",
 *         "gvx": "G-vector x components, shape (ng,).",
 *         "gvy": "G-vector y components, shape (ng,).",
 *         "gvz": "G-vector z components, shape (ng,).",
 *         "tol": "Matching tolerance on |h - round(h)|.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gvx.ndim == 1",
 *         "gvx.n == gvy.n",
 *         "gvy.n == gvz.n",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gvx.format == 'd'",
 *         "sig": "void score_and_refine_f64_soa(double ubi[3][3], const double gvx[], const double gvy[], const double gvz[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gvx": "gvx.ptr", "gvy": "gvy.ptr", "gvz": "gvz.ptr", "tol": "tol", "ng": "gvx.shape[0]"},
 *     }],
 * }
C2PY_END */

extern "C" void score_and_refine_f64_soa(
    double ubi[3][3], const double gvx[], const double gvy[], const double gvz[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    SAR_IMPL_NAME<double, double>(ubi, gvx, gvy, gvz, tol, n_arg, sumdrlv2_arg, ng);
}
