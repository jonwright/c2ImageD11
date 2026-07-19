#include "cImageD11.h"
#include "blobs.h"
extern int sparse_is_sorted(const uint16_t i[], const uint16_t j[], intptr_t nnz);
static int NOISY = 0;

/* C2PY_BEGIN
 * {"py_sig": "sparse_connectedpixels(v: buffer, i: buffer, j: buffer, threshold: float, labels: buffer) -> int",
 *  "doc": "runs the connectedpixels algorithm on\na sparse image using a supplied threshold putting labels\ninto labels array and returning the number of blobs found",
 *  "params": {"v": "Values (float32).", "i": "Rows (uint16).", "j": "Cols (uint16).", "threshold": "Threshold.", "labels": "Output labels (int32)."},
 *  "checks": ["v.format == 'f'", "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2",
 *      "j.n == i.n", "v.n == i.n", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == i.n"],
 *  "c_overloads": [{"sig": "int sparse_connectedpixels(const float *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, float threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}}]}
C2PY_END */

int sparse_connectedpixels(float *restrict v, uint16_t *restrict i,
                           uint16_t *restrict j, intptr_t nnz, float threshold,
                           int32_t *restrict labels /* nnz */
) {
    intptr_t k, p, pp; int ir;
    int32_t *S, *T, np;
    /* Read k = kurrent
       p = prev */
    double start, mid, end;
    if (NOISY) {
        start = my_get_time();
        k = sparse_is_sorted(i, j, nnz);
        if (k != 0)
            return k;
    }
    pp = 0;
    p = 0;
    S = dset_initialise(16384);
    /* Main loop */
    if (NOISY)
        printf("ok to main loop\n");
    for (k = 0; k < nnz; k++) {
        labels[k] = 0;
        if (v[k] <= threshold) {
            continue;
        }
        if (k == 0)
            goto newlabel;
        /* Decide on label for this one ...
         *
         * 4 neighbors : k-1 is prev
         */
        p = k - 1; /* previous pixel, same row */
        if (((j[p] + 1) == j[k]) && (i[p] == i[k]) && (labels[p] > 0)) {
            labels[k] = labels[p];
            /* check for unions below */
        }
        if (i[k] == 0)
            goto newlabel;
        ir = i[k] - 1;
        /* pp should be on row above, on or after j-1 */
        while (ir > i[pp])
            pp++;
        /* out if nothing on row above */
        if (i[pp] == i[k])
            goto newlabel;
        /* Locate previous pixel on row above */
        while (((j[k] - j[pp]) > 1) && (i[pp] == ir))
            pp++;
        for (p = pp; j[p] <= j[k] + 1; p++) {
            if (i[p] == ir) {
                if (labels[p] > 0) {
                    // Union p, k
                    match(labels[k], labels[p], S);
                }
            } else {
                break; // not same row
            }
        }
    newlabel:
        if (labels[k] == 0)
            S = dset_new(&S, &labels[k]);
    } // end loop over data
    if (NOISY)
        mid = my_get_time();
    T = dset_compress(&S, &np);
    // renumber labels
    for (k = 0; k < nnz; k++) {
        if (labels[k] > 0) {
            /* if( T[labels[k]] == 0 ){
               printf("Error in sparse_connectedpixels\n");
               } */
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
