/* score_and_refine_f32_avx512.cpp  -- f32_avx512 variant */
#define SAR_IMPL_NAME score_and_refine_impl_f32_avx512
#ifdef SAR_SOA
#undef SAR_SOA
#endif

#include "score_and_refine.hpp"


extern "C" void score_and_refine_f32_avx512(double ubi[3][3], const float gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)
{
    SAR_IMPL_NAME<float, float>(ubi, (const float *)gv, tol, n_arg, sumdrlv2_arg, ng);
}
