#ifndef TOSPARSE_IMPL_HPP
#define TOSPARSE_IMPL_HPP

#include <stdint.h>
#include <stddef.h>

template<typename TPixel>
static int tosparse_impl(const TPixel * img, const uint8_t * msk,
                          uint16_t * row, uint16_t * col,
                          TPixel * val, double cut,
                          intptr_t ns, intptr_t nf) {
    TPixel th = TPixel(cut);
    intptr_t i;
    int k = 0;
    for (i = 0; i < ns * nf; i++) {
        if (msk[i] && (img[i] > th)) {
            row[k] = i / nf;
            col[k] = i % nf;
            val[k] = img[i];
            k++;
        }
    }
    return k;
}

#endif
