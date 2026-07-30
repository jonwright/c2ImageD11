#ifndef SPARSE_LOCALMAXLABEL_HPP
#define SPARSE_LOCALMAXLABEL_HPP

#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <assert.h>

#include "cImageD11.h"

#ifdef __cplusplus
extern "C" {
#endif
int sparse_is_sorted(const uint16_t i[], const uint16_t j[], intptr_t nnz);
#ifdef __cplusplus
}
#endif

template<typename TPixel>
static int sparse_localmaxlabel_impl(TPixel *restrict v, uint16_t *restrict i,
                                      uint16_t *restrict j, intptr_t nnz,
                                      float *restrict MV,
                                      int32_t *restrict iMV,
                                      int32_t *restrict labels) {
    intptr_t k, p, pp; int ir, pnext;
    float MV_LOW;
    MV_LOW = -1e10f;
    static int NOISY = 0;
#define CHECKSANITY 0
#define TRACE 0
    if (NOISY) {
        k = sparse_is_sorted(i, j, nnz);
        if (k != 0) {
            printf("Not sorted! k=%td\n", k);
        }
    }
    pp = 0;
    p = 0;
    iMV[0] = 0;
    MV[0] = (float)v[0];
    for (k = 1; k < nnz; k++) {
        iMV[k] = k;
        MV[k] = MV_LOW;
        ir = ((int)i[k]) - 1;
        while (ir > i[pp]) {
            pp++;
            if (CHECKSANITY) {
                assert((pp >= 0) && (pp < nnz));
            }
        }
        if (TRACE)
            printf("k %td    i[k] %td  j[k] %td  v[k] %f MV[k] %f\n", k, i[k],
                   j[k], (float)v[k], MV[k]);
        if (i[pp] < i[k]) {
            while (((j[pp] + 1) < j[k]) && (i[pp] == ir)) {
                pp++;
                if (CHECKSANITY) {
                    assert((pp >= 0) && (pp < nnz));
                }
            }
            for (p = pp; j[p] <= j[k] + 1; p++) {
                if (CHECKSANITY) {
                    assert((p >= 0) && (p < nnz));
                    assert(p < k);
                }
                if (TRACE)
                    printf("p %td   i[p] %td   j[p] %td  v[p] %f MV[k] %f\n", p,
                           i[p], j[p], (float)v[p], MV[k]);
                if (i[p] != ir)
                    break;
                if (v[k] > v[p]) {
                    if ((float)v[k] > MV[p]) {
                        iMV[p] = k;
                        MV[p] = (float)v[k];
                    }
                } else {
                    if ((float)v[p] > MV[k]) {
                        iMV[k] = p;
                        MV[k] = (float)v[p];
                    }
                }
            }
        }
        p = k - 1;
        if (CHECKSANITY) {
            assert((p >= 0) && (p < nnz));
        }
        if ((i[k] == i[p]) &&
            (j[k] == (j[p] + 1))) {
            if (TRACE)
                printf("p %td   i[p] %td   j[p] %td  v[p] %f\n", p, i[p], j[p],
                       (float)v[p]);
            if (v[k] > v[p]) {
                if ((float)v[k] > MV[p]) {
                    iMV[p] = k;
                    MV[p] = (float)v[k];
                }
            } else {
                if ((float)v[p] > MV[k]) {
                    iMV[k] = p;
                    MV[k] = (float)v[p];
                }
            }
        }
        if ((float)v[k] > MV[k]) {
            iMV[k] = k;
            MV[k] = (float)v[k];
        }
    }
    pp = 0;
    for (k = 0; k < nnz; k++) {
        labels[k] = -1;
        if (iMV[k] == k) {
            pp = pp + 1;
            labels[k] = pp;
        }
    }
    for (k = 0; k < nnz; k++) {
        p = iMV[k];
        pnext = 0;
        while (iMV[p] != p) {
            p = iMV[p];
            pnext++;
            if (CHECKSANITY) {
                assert((p >= 0) && (p < nnz));
            }
        }
        labels[k] = labels[p];

        if (pnext > 0) {
            p = iMV[k];
            iMV[k] = k;
            while (iMV[p] != p) {
                labels[p] = labels[k];
                pnext = iMV[p];
                iMV[p] = p;
                p = pnext;
            }
        }
    }
    return pp;
}

#endif
