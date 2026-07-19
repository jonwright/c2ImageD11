#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "connectedpixels(data: buffer, labels: buffer, threshold: float, verbose: int = 0, con8: int = 1) -> int",
 *  "doc": "Determines which pixels in data are above the\nuser supplied threshold and assigns them into connected objects\nwhich are output in labels. Connectivity is 3x3 box (8) by default\nand reduces to a +(4) is con8==0",
 *  "params": {"data": "Input float32 2D.", "labels": "Output int32 labels.", "threshold": "Threshold.",
 *      "verbose": "Print diagnostics.", "con8": "8-connected (1) or 4-connected (0)."},
 *  "checks": ["data.format == 'f'", "data.ndim == 2", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == data.n"],
 *  "c_overloads": [{"sig": "int connectedpixels(const float *data, int32_t *labels, float threshold, int verbose, int eightconnected, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"data": "data.ptr", "labels": "labels.ptr", "threshold": "threshold", "verbose": "verbose", "eightconnected": "con8", "ns": "data.shape[0]", "nf": "data.shape[1]"}}]}
C2PY_END */

int connectedpixels(const float *data, int32_t *labels, float threshold, int verbose,
                    int eightconnected, intptr_t ns, intptr_t nf) {

    intptr_t i, j, irp, ir, ipx;
    int32_t k, *S, *T, np;

    if (verbose) {
        printf("Welcome to connectedpixels ");
        if (eightconnected)
            printf("Using connectivity 8\n");
        else
            printf("Using connectivity 4\n");
    }

    /* lots of peaks possible */
    S = dset_initialise(16384);

    /* To simplify later we hoist the first row and first pixel
     * out of the loops
     *
     * Algorithm scans image looking at stuff previously seen
     */

    /* First point */
    /*  i = 0;   j = 0; */
    if (data[0] > threshold) {
        S = dset_new(&S, &labels[0]);
    } else {
        labels[0] = 0;
    }
    /* First row */
    for (j = 1; j < nf; j++) {
        labels[j] = 0; /* initialize */
        if (data[j] > threshold) {
            if (labels[j - 1] > 0) {
                labels[j] = labels[j - 1];
            } else {
                S = dset_new(&S, &labels[j]);
            }
        }
    }

    /* === Mainloop ============================================= */
    for (i = 1; i < ns; i++) { /* i-1 prev row always exists, see above */
        ir = i * nf;           /* this row */
        irp = ir - nf;         /* prev row */
        /* First point */
        /* j=0; */
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
        /* Run along row to just before end */
        for (j = 1; j < nf - 1; j++) {
            ipx = ir + j;
            irp = ipx - nf;
            labels[ipx] = 0;
            if (data[ipx] > threshold) {
                /* Pixel needs to be assigned */
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
                if (labels[ipx] == 0) { /* Label is new ! */
                    S = dset_new(&S, &labels[ipx]);
                }
            } /* (val > threshold) */
        } /* Mainloop j */
        /* Last pixel on the row */
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
            if (labels[ipx] == 0) { /* Label is new ! */
                S = dset_new(&S, &labels[ipx]);
            }
        }
    }
    /* Now compress the disjoint set to make single list of
     * unique labels going from 1->n
     */
    T = dset_compress(&S, &np);
    /* Now scan through image re-assigning labels as needed */
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
