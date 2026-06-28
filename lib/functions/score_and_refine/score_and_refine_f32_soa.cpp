/* score_and_refine_f32_soa.cpp — f32 SoA baseline variant */
#define SAR_SOA
#define SAR_IMPL_NAME score_and_refine_impl_f32_soa
#include "score_and_refine.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3",
 *         "sig": "void score_and_refine_f32_soa(double ubi[3][3], const float gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
 *     }],
 * }
C2PY_END */

extern "C" void score_and_refine_f32_soa(
    double ubi[3][3], const float gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    const float *gvx = gv;
    const float *gvy = gv + ng;
    const float *gvz = gv + 2 * ng;
    SAR_IMPL_NAME<float, float>(ubi, gvx, gvy, gvz, tol, n_arg, sumdrlv2_arg, ng);
}
