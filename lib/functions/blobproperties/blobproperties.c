#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "blobproperties(data: buffer, labels: buffer, np: int, results: buffer, omega: float = 0.0, verbose: int = 0) -> void",
 *  "doc": "Compute blob properties for each labelled object.",
 *  "params": {"data": "Input float32 2D.", "labels": "Input int32 labels.", "np": "Number of objects.",
 *      "results": "Output array (np, 36).", "omega": "Omega angle.", "verbose": "Print diagnostics."},
 *  "checks": ["data.format == 'f'", "data.ndim == 2", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == data.n",
 *      "results.format == 'd'", "results.shape[0] == np", "results.shape[1] == 36"],
 *  "gil_release": true,
 *  "c_overloads": [{"sig": "void blobproperties(const float *data, const int32_t *labels, int32_t npk, float omega, int verbose, intptr_t ns, intptr_t nf, double *res)",
 *      "map": {"data": "data.ptr", "labels": "labels.ptr", "npk": "np", "omega": "omega", "verbose": "verbose", "ns": "data.shape[0]", "nf": "data.shape[1]", "res": "results.ptr"}}]}
C2PY_END */

void blobproperties(const float *data, const int32_t *labels, int32_t npk, float omega,
                    int verbose, intptr_t ns, intptr_t nf, double *res) {
    intptr_t i, j, ipx; int bad;
    double fval;
    int32_t ipk;
    if (verbose) {
        printf("Computing blob moments, ns %td, nf %td, npk %td\n", ns, nf, npk);
    }
    /* Initialise the results */
    for (i = 0; i < npk; i++) {
        for (j = 0; j < NPROPERTY; j++) {
            res[i * NPROPERTY + j] = 0.;
        }
        /* Set min to max +1 and vice versa */
        res[i * NPROPERTY + bb_mn_f] = (double)(nf + 1);
        res[i * NPROPERTY + bb_mn_s] = (double)(ns + 1);
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
                        printf("Found %d in your blob image at i=%td, j=%td\n",
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
