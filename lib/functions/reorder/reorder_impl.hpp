#ifndef REORDER_IMPL_HPP
#define REORDER_IMPL_HPP

#include <stdint.h>
#include <stddef.h>

template<typename TPixel>
static void reorder_impl(const TPixel * data, const uint32_t * adr,
                          TPixel * out, intptr_t N) {
    intptr_t i;
#pragma omp parallel for
    for (i = 0; i < N; i++) {
        out[adr[i]] = data[i];
    }
}

#endif
