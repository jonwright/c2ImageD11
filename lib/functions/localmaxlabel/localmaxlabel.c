#include "cImageD11.h"
#include "blobs.h"
#include "cimaged11utils.h"

/* C2PY_BEGIN
 * {"py_sig": "localmaxlabel(data: buffer, labels: buffer, wrk: buffer) -> int",
 *  "doc": "Label each pixel to its local maximum.",
 *  "params": {"data": "Input float32 2D.", "labels": "Output int32 labels.", "wrk": "Temp uint8 workspace."},
 *  "checks": ["data.format == 'f'", "data.ndim == 2", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == data.n",
 *      "wrk.format == 'B' or wrk.format == 'b'", "wrk.n == data.n"],
 *  "c_overloads": [{"sig": "int localmaxlabel(const float *im, int32_t *lout, uint8_t *l, intptr_t dim0, intptr_t dim1) -> int",
 *      "map": {"im": "data.ptr", "lout": "labels.ptr", "l": "wrk.ptr", "dim0": "data.shape[0]", "dim1": "data.shape[1]"}}]}
C2PY_END */

int localmaxlabel(const float *restrict im, // input
                  int32_t *restrict lout,   // output
                  uint8_t *restrict l,      // workspace temporary
                  intptr_t dim0,                 // Image dimensions
                  intptr_t dim1) {
    // old msvc for python 2.7 requires ALL variables declared up here.
    intptr_t i, j, p, q, nt, lo, hi; int k, npk, t, npks;
    //   int noisy=0;
#define noisy 0
    double tic, toc;
    int o[10] = {0, // special case
                 -1 - dim1, -1,        -1 + dim1, -dim1,    0,
                 +dim1,     +1 - dim1, +1,        +1 + dim1}; // 7,8,9

    if (noisy)
        printf("Not using intrinsics\n");
    npks = neighbormax(im, lout, l, dim0, dim1); //, o);
    if (noisy) {
        toc = my_get_time();
        printf("    neighbormax %.3f ms %d peaks\n", 1000 * (toc - tic), npks);
        tic = toc;
    }
    // Cumulate lout[i] so that lout[i] holds cumulative sums
    npk = 0;
    for (i = 0; i < dim0 * dim1; i = i + dim1) {
        t = npk;
        npk += lout[i];
        lout[i] = t;
    }
    if (noisy) {
        toc = my_get_time();
        printf("    cumsum %.3f ms %d\n", 1000 * (toc - tic), npk);
        tic = toc;
    }
    // Now pass with row offsets in place
    for (i = 0; i < (dim0 - 1); i++) {
        t = lout[i * dim1];
        nt = lout[(i + 1) * dim1];
        if (t == nt)
            continue;
        // Break early if there is no peak on this row or you already got it
        for (j = 1; j < (dim1 - 1); j++) {
            p = dim1 * i + j;
            if (l[p] == 5) { // pointing to self : k+1==5
                t++;
                lout[p] = t; // final label
                l[p] = 0;    // done, so tagged as zero
                if (t == nt)
                    break; // no more peaks
            }
        }
    }
    /* overwrite front border as zero again */
    for (i = 0; i < dim0 * dim1; i = i + dim1) {
        lout[i] = 0;
    }
    if (noisy) {
        toc = my_get_time();
        printf("    relabel %.3f ms\n", 1000 * (toc - tic));
        tic = toc;
    }
    //
    // Now make all point to their max
    // If we re-write the paths we cannot run in parallel
    //  ... this was the slowest part, so try openmp
    // 105 ms to always walk to max
    // 40 ms if path relabelled
    //
    // This is the same for all versions (optimised or not)
    //  ... perhaps re-write to be a manual loop and fill in
    //  ... the steps that are thread local
    {
        lo = 0;
        hi = dim0 * dim1;
        for (i = lo; i < hi; i++) {
            if (l[i] == 0)
                continue; // done
            // Now we need to walk to find a label
            k = 0;
            q = i + o[l[i]];
            while (l[q]) {
                q = q + o[l[q]];
                k++;
            } // Now q addresses a max or a correct label
            lout[i] = lout[q]; // take label from max
            if (k >
                0) { // relabel the path taken while we know the top label value
                q = i + o[l[i]];
                while (l[q]) {
                    if ((q >= lo) && (q < hi)) {
                        l[q] = 0;
                        lout[q] = lout[i];
                    }
                    q = q + o[l[q]];
                }
            }
            l[i] = 0; // sharing problems??
        }
    }
    if (noisy) {
        toc = my_get_time();
        printf("    write %.3f ms\n", 1000 * (toc - tic));
        tic = toc;
    }
    return npk;
}
