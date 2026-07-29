#ifndef SPARSE_CONNECTEDPIXELS_HPP
#define SPARSE_CONNECTEDPIXELS_HPP

#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <stdio.h>

#include "cImageD11.h"

#ifdef __cplusplus
extern "C" {
#endif
int32_t *dset_initialise(int32_t size);
int32_t *dset_new(int32_t **S, int32_t *v);
void dset_makeunion(int32_t *S, int32_t r1, int32_t r2);
int32_t *dset_compress(int32_t **pS, int32_t *np);
int sparse_is_sorted(const uint16_t i[], const uint16_t j[], intptr_t nnz);
#ifdef __cplusplus
}
#endif

#ifndef match
#define match(X, Y, Z)                                                         \
    do {                                                                       \
        if ((X) == 0) {                                                        \
            (X) = (Y);                                                         \
        } else {                                                               \
            if ((X) != (Y)) {                                                  \
                dset_makeunion((Z), (X), (Y));                                  \
            }                                                                  \
        }                                                                      \
    } while (0)
#endif

template<typename TPixel>
static int sparse_connectedpixels_impl(TPixel *restrict v, uint16_t *restrict i,
                                        uint16_t *restrict j, intptr_t nnz,
                                        TPixel threshold,
                                        int32_t *restrict labels) {
    intptr_t k, p, pp; int ir;
    int32_t *S, *T, np;
    double start, mid, end;
    static int NOISY = 0;
    if (NOISY) {
        start = my_get_time();
        k = sparse_is_sorted(i, j, nnz);
        if (k != 0)
            return k;
    }
    pp = 0;
    p = 0;
    S = dset_initialise(16384);
    if (NOISY)
        printf("ok to main loop\n");
    for (k = 0; k < nnz; k++) {
        labels[k] = 0;
        if (v[k] <= threshold) {
            continue;
        }
        if (k == 0)
            goto newlabel;
        p = k - 1;
        if (((j[p] + 1) == j[k]) && (i[p] == i[k]) && (labels[p] > 0)) {
            labels[k] = labels[p];
        }
        if (i[k] == 0)
            goto newlabel;
        ir = i[k] - 1;
        while (ir > i[pp])
            pp++;
        if (i[pp] == i[k])
            goto newlabel;
        while (((j[k] - j[pp]) > 1) && (i[pp] == ir))
            pp++;
        for (p = pp; j[p] <= j[k] + 1; p++) {
            if (i[p] == ir) {
                if (labels[p] > 0) {
                    match(labels[k], labels[p], S);
                }
            } else {
                break;
            }
        }
    newlabel:
        if (labels[k] == 0)
            S = dset_new(&S, &labels[k]);
    }
    if (NOISY)
        mid = my_get_time();
    T = dset_compress(&S, &np);
    for (k = 0; k < nnz; k++) {
        if (labels[k] > 0) {
            labels[k] = T[labels[k]];
        }
    }
    free(S);
    free(T);
    if (NOISY) {
        end = my_get_time();
        printf("Time in sparse image %f ms %f ms\n", 1000 * (end - mid),
               1000 * (mid - start));
    }
    return np;
}

#endif
