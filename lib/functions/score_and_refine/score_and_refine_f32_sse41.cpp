/* score_and_refine_f32_sse41.cpp — f32_sse41 variant */
#define SAR_IMPL_NAME score_and_refine_impl_f32_sse41
#ifdef SAR_SOA
#undef SAR_SOA
#endif

#include "score_and_refine.hpp"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'f' and c2py_amd64_sse4_1",
 *         "sig": "void score_and_refine_f32_sse41(double ubi[3][3], const float gv[][3], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */

extern "C" void score_and_refine_f32_sse41(double ubi[3][3], const float gv[][3], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    SAR_IMPL_NAME<float, float>(ubi, (const float *)gv, tol, n_arg, sumdrlv2_arg, ng);
}
