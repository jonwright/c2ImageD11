#ifndef REORDERLUT_IMPL_HPP
#define REORDERLUT_IMPL_HPP

#include <stdint.h>
#include <stddef.h>

template<typename TPixel>
static void reorderlut_impl(const TPixel * data, const uint32_t * lut,
                             TPixel * out, intptr_t N) {
    intptr_t i;
#pragma omp parallel for
    for (i = 0; i < N; i++) {
        out[i] = data[lut[i]];
    }
}

#endif
