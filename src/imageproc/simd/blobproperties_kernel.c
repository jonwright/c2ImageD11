/* Auto-extracted from ImageD11/src/connectedpixels.c, function blobproperties, commit 8f7d29e
 *
 * DO NOT EDIT BY HAND -- regenerate with tools/extract_kernels.py
 */
#ifndef KERNEL_FN
#error "KERNEL_FN must be defined (e.g. -DKERNEL_FN=score_sse42)"
#endif

#include "cImageD11.h"
#include <stdio.h>
#include <math.h>
#include "blobs.h"

void KERNEL_FN(float *data, int32_t *labels, int32_t npk, float omega,
                    int verbose, int ns, int nf, double *res) {
    int i, j, bad, ipx;
    double fval;
    int32_t ipk;
    if (verbose) {
        printf("Computing blob moments, ns %d, nf %d, npk %d\n", ns, nf, npk);
    }
    /* Initialise the results */
    for (i = 0; i < npk; i++) {
        for (j = 0; j < NPROPERTY; j++) {
            res[i * NPROPERTY + j] = 0.;
        }
        /* Set min to max +1 and vice versa */
        res[i * NPROPERTY + bb_mn_f] = nf + 1;
        res[i * NPROPERTY + bb_mn_s] = ns + 1;
        res[i * NPROPERTY + bb_mx_f] = -1;
        res[i * NPROPERTY + bb_mx_s] = -1;
        /* All pixels have the same omega in this frame */
        res[i * NPROPERTY + bb_mx_o] = omega;
        res[i * NPROPERTY + bb_mn_o] = omega;
    }
    if (verbose != 0)
        printf("Scanning image\n");

    bad = 0;
    /* i,j is looping along the indices data array */
    for (i = 0; i < ns; i++) {
        for (j = 0; j < nf; j++) {
            ipx = i * nf + j;
            ipk = labels[ipx];
            if (ipk > 0 && ipk <= npk) {
                fval = (double)data[ipx];
                add_pixel(&res[NPROPERTY * (ipk - 1)], i, j, fval, omega);
            } else {
                if (ipk != 0) {
                    bad++;
                    if (bad < 10) {
                        printf("Found %d in your blob image at i=%d, j=%d\n",
                               ipk, i, j);
                    }
                }
            }
        } /* j */
    } /* i */
    if (verbose) {
        printf("\nFound %d bad pixels in the blob image\n", bad);
    }
}
