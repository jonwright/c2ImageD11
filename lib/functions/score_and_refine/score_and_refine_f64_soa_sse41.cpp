/* score_and_refine_f64_soa_sse41.cpp — f64_soa_sse41 variant */
#define SAR_IMPL_NAME score_and_refine_impl_f64_soa_sse41
#ifdef SAR_SOA
#undef SAR_SOA
#endif
#define SAR_SOA
#include "score_and_refine.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine_soa(ubi: buffer, gvx: buffer, gvy: buffer, gvz: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gvx.format == 'd' and c2py_amd64_sse4_1",
 *         "sig": "void score_and_refine_f64_soa_sse41(double ubi[3][3], const double gvx[], const double gvy[], const double gvz[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gvx": "gvx.ptr", "gvy": "gvy.ptr", "gvz": "gvz.ptr", "tol": "tol", "ng": "gvx.shape[0]"},
 *     }],
 * }
C2PY_END */

extern "C" void score_and_refine_f64_soa_sse41(double ubi[3][3], const double gvx[], const double gvy[], const double gvz[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    SAR_IMPL_NAME<double, double>(ubi, gvx, gvy, gvz, tol, n_arg, sumdrlv2_arg, ng);
}
