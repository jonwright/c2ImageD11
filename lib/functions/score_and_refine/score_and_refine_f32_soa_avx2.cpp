/* score_and_refine_f32_soa_avx2.cpp  -- f32_soa_avx2 variant */
#define SAR_IMPL_NAME score_and_refine_impl_f32_soa_avx2
#ifdef SAR_SOA
#undef SAR_SOA
#endif
#define SAR_SOA
#include "score_and_refine.hpp"


extern "C" void score_and_refine_f32_soa_avx2(
    double ubi[3][3], const float gv[], double tol,
    int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    const float *gvx = gv;
    const float *gvy = gv + ng;
    const float *gvz = gv + 2 * ng;
    SAR_IMPL_NAME<float, float>(ubi, gvx, gvy, gvz, tol, n_arg, sumdrlv2_arg, ng);
}
