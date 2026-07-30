/* make_clean_mask.hpp — type-templated threshold + clean_mask */
#ifndef MAKE_CLEAN_MASK_HPP
#define MAKE_CLEAN_MASK_HPP

#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
int clean_mask(const int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf);
#ifdef __cplusplus
}
#endif

template<typename T>
static int make_clean_mask_impl(const T *img, double cut, int8_t *msk,
                                 int8_t *ret, intptr_t ns, intptr_t nf) {
    T th = (T)cut;
    intptr_t i;
#pragma omp parallel for
    for (i = 0; i < ns * nf; i++) {
        msk[i] = (img[i] > th) ? 1 : 0;
    }
    return clean_mask(msk, ret, ns, nf);
}

#endif
