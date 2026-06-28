/* score_and_refine_f64_soa_avx2.cpp  -- f64_soa_avx2 variant */
#define SAR_IMPL_NAME score_and_refine_impl_f64_soa_avx2
#ifdef SAR_SOA
#undef SAR_SOA
#endif
#define SAR_SOA
#include "score_and_refine.hpp"


extern "C" void score_and_refine_f64_soa_avx2(
    double ubi[3][3], const double gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    const double *gvx = gv;
    const double *gvy = gv + ng;
    const double *gvz = gv + 2 * ng;
    SAR_IMPL_NAME<double, double>(ubi, gvx, gvy, gvz, tol, n_arg, sumdrlv2_arg, ng);
}
