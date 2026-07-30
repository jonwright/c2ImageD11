#ifndef CONNECTEDPIXELS_HPP
#define CONNECTEDPIXELS_HPP

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
static int connectedpixels_impl(const TPixel *data, int32_t *labels,
                                 TPixel threshold,
                                 int verbose, int eightconnected,
                                 intptr_t ns, intptr_t nf) {
    intptr_t i, j, irp, ir, ipx;
    int32_t k, *S, *T, np;

    if (verbose) {
        printf("Welcome to connectedpixels ");
        if (eightconnected)
            printf("Using connectivity 8\n");
        else
            printf("Using connectivity 4\n");
    }

    S = dset_initialise(16384);

    if (data[0] > threshold) {
        S = dset_new(&S, &labels[0]);
    } else {
        labels[0] = 0;
    }
    for (j = 1; j < nf; j++) {
        labels[j] = 0;
        if (data[j] > threshold) {
            if (labels[j - 1] > 0) {
                labels[j] = labels[j - 1];
            } else {
                S = dset_new(&S, &labels[j]);
            }
        }
    }

    for (i = 1; i < ns; i++) {
        ir = i * nf;
        irp = ir - nf;
        labels[ir] = 0;
        if (data[ir] > threshold) {
            if (labels[irp] > 0) {
                labels[ir] = labels[irp];
            }
            if (eightconnected && (labels[irp + 1] > 0)) {
                match(labels[ir], labels[irp + 1], S);
            }
            if (labels[ir] == 0) {
                S = dset_new(&S, &labels[ir]);
            }
        }
        for (j = 1; j < nf - 1; j++) {
            ipx = ir + j;
            irp = ipx - nf;
            labels[ipx] = 0;
            if (data[ipx] > threshold) {
                if (eightconnected && (labels[irp - 1] > 0)) {
                    match(labels[ipx], labels[irp - 1], S);
                }
                if (labels[irp] > 0) {
                    match(labels[ipx], labels[irp], S);
                }
                if (eightconnected && (labels[irp + 1] > 0)) {
                    match(labels[ipx], labels[irp + 1], S);
                }
                if (labels[ipx - 1] > 0) {
                    match(labels[ipx], labels[ipx - 1], S);
                }
                if (labels[ipx] == 0) {
                    S = dset_new(&S, &labels[ipx]);
                }
            }
        }
        ipx = ir + nf - 1;
        irp = ipx - nf;
        labels[ipx] = 0;
        if (data[ipx] > threshold) {
            if (eightconnected && (labels[irp - 1] > 0)) {
                match(labels[ipx], labels[irp - 1], S);
            }
            if (labels[irp] > 0) {
                match(labels[ipx], labels[irp], S);
            }
            if (labels[ipx - 1] > 0) {
                match(labels[ipx], labels[ipx - 1], S);
            }
            if (labels[ipx] == 0) {
                S = dset_new(&S, &labels[ipx]);
            }
        }
    }
    T = dset_compress(&S, &np);
#pragma omp parallel for private(j, ipx, k) shared(labels)
    for (i = 0; i < ns; i++) {
        for (j = 0; j < nf; j++) {
            ipx = i * nf + j;
            k = labels[ipx];
            if (k > 0) {
                if (T[k] == 0) {
                    printf("Error in connectedpixels\n");
                }
                if (T[k] != k) {
                    labels[i * nf + j] = T[k];
                }
            }
        }
    }
    free(S);
    free(T);
    return np;
}

#endif
