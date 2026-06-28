/* score_and_refine_f64_soa_avx512.cpp — f64_soa_avx512 variant */
#define SAR_IMPL_NAME score_and_refine_impl_f64_soa_avx512
#ifdef SAR_SOA
#undef SAR_SOA
#endif
#define SAR_SOA
#include "score_and_refine.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3 and c2py_amd64_avx512f",
 *         "sig": "void score_and_refine_f64_soa_avx512(double ubi[3][3], const double gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
 *     }],
 * }
C2PY_END */

extern "C" void score_and_refine_f64_soa_avx512(
    double ubi[3][3], const double gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    const double *gvx = gv;
    const double *gvy = gv + ng;
    const double *gvz = gv + 2 * ng;
    SAR_IMPL_NAME<double, double>(ubi, gvx, gvy, gvz, tol, n_arg, sumdrlv2_arg, ng);
}
