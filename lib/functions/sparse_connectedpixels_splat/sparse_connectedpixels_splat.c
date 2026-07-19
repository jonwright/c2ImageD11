#include "cImageD11.h"
#include "blobs.h"
extern int sparse_is_sorted(const uint16_t i[], const uint16_t j[], intptr_t nnz);
static int NOISY = 0;

/* C2PY_BEGIN
 * {"py_sig": "sparse_connectedpixels_splat(v: buffer, i: buffer, j: buffer, th: float, lbl: buffer, Z: buffer, ni: int, nj: int) -> int",
 *  "doc": "is for debugging/timing. It splats\nthe sparse array into a dense array and runs the old connectedpixels\ncode on that.",
 *  "params": {"v": "Values (float32).", "i": "Rows (uint16).", "j": "Cols (uint16).",
 *      "th": "Threshold.", "lbl": "Output labels.", "Z": "Temp buffer.", "ni": "Rows.", "nj": "Cols."},
 *  "checks": ["v.format == 'f'", "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2",
 *      "j.n == i.n", "v.n == i.n", "( lbl.format == 'i' or lbl.format == 'l' )", "lbl.n == i.n", "( Z.format == 'i' or Z.format == 'l' )"],
 *  "c_overloads": [{"sig": "int sparse_connectedpixels_splat(const float *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, float threshold, int32_t *labels, int32_t *Z, intptr_t imax, intptr_t jmax) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "th", "labels": "lbl.ptr", "Z": "Z.ptr", "imax": "ni", "jmax": "nj"}}]}
C2PY_END */

int sparse_connectedpixels_splat(float *restrict v, uint16_t *restrict i,
                                 uint16_t *restrict j, intptr_t nnz, float threshold,
                                 int32_t *restrict labels, /* nnz */
                                 int32_t *restrict Z,
                                 /* workspace, at least (imax+2)*(jmax+2) */
                                 intptr_t imax, intptr_t jmax) {
    intptr_t k, p, pp, jdim, ik, jk; int ir;
    int32_t *S, *T, np;
    /* Read k = kurrent
       p = prev */
    double start, mid;
    if (NOISY) {
        start = my_get_time();
        k = sparse_is_sorted(i, j, nnz);
        if (k != 0)
            return k;
    }
    if (NOISY) {
        mid = my_get_time();
        printf("check sorted %.3f ms\n", (mid - start) * 1000);
        start = my_get_time();
    }

    jdim = jmax + 2;
    /* This is not! delivered with zeros, we put a border in too
     *  Z = (int32_t *) malloc(idim*jdim* sizeof(int32_t));
     * later we will write into Z as a scratch area for labels (filled at very
     * end) */
    pp = 0;
    p = 0;
    S = dset_initialise(16384);
    if (NOISY) {
        mid = my_get_time();
        printf("mallocs %.3f ms\n", (mid - start) * 1000);
        start = my_get_time();
    }
    /* zero the parts of Z that we will read from (pixel neighbors) */
    for (k = 0; k < nnz; k++) {
        ik = i[k] + 1; /* the plus 1 is because we padded Z */
        jk = j[k] + 1;
        p = ik * jdim + jk;
        Z[p] = 0;
        Z[p - 1] = 0;
        Z[p - jdim - 1] = 0;
        Z[p - jdim] = 0;
        Z[p - jdim + 1] = 0;
    }
    if (NOISY) {
        mid = my_get_time();
        printf("zeros %.3f ms\n", (mid - start) * 1000);
        start = my_get_time();
    }

    /* Main loop */
    for (k = 0; k < nnz; k++) {
        if (v[k] <= threshold) {
            continue;
        }
        /* Decide on label for this one ...
         *
         * 4 neighbors : k-1 is prev
         */
        ik = i[k] + 1; /* the plus 1 is because we padded Z */
        jk = j[k] + 1;
        p = ik * jdim + jk;
        /* previous pixel, same row */
        if (Z[p - 1] > 0) {
            Z[p] = Z[p - 1];
        }
        /* 3 pixels on previous row */
        ir = (ik - 1) * jdim + jk;
        for (pp = ir - 1; pp <= ir + 1; pp++) {
            if (Z[pp] > 0) {
                // Union p, k
                match(Z[p], Z[pp], S);
            }
        }
        if (Z[p] == 0)
            S = dset_new(&S, &Z[p]);
    } // end loop over data
    if (NOISY) {
        mid = my_get_time();
        printf("main loop %.3f ms\n", (mid - start) * 1000);
        start = my_get_time();
    }
    T = dset_compress(&S, &np);
    // renumber labels
    for (k = 0; k < nnz; k++) {
        ik = i[k] + 1; /* the plus 1 is because we padded Z */
        jk = j[k] + 1;
        p = ik * jdim + jk;
        if (Z[p] > 0) {
            labels[k] = T[Z[p]];
        }
    }
    if (NOISY) {
        mid = my_get_time();
        printf("Relabelling %f ms\n", 1000 * (mid - start));
        start = my_get_time();
    }
    free(S);
    free(T);
    if (NOISY) {
        mid = my_get_time();
        printf("Free %f ms\n", 1000 * (mid - start));
    }
    return np;
}
