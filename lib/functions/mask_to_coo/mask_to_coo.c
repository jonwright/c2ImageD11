#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "mask_to_coo(msk: buffer, i: buffer, j: buffer, w: buffer) -> int",
 *  "doc": "takes a mask and converts it to a list\nof i,j coordinates in a sparse array coo format\nreturns :\n   0 => success\n   1 => ns out of range ; 2 => nf out of range\n   3 => nnz < 1 empty mask\n   4 => nnz did not match this mask",
 *  "params": {"msk": "Input int8 2D mask.", "i": "Output row indices (uint16).",
 *      "j": "Output col indices (uint16).", "w": "Output per-row counts (int32)."},
 *  "checks": ["msk.format == 'b' or msk.format == 'B'", "msk.ndim == 2",
 *      "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2", "j.n == i.n",
 *      "( w.format == 'i' or w.format == 'l' )", "w.n == msk.shape[0]"],
 *  "c_overloads": [{"sig": "int mask_to_coo(const int8_t *msk, intptr_t ns, intptr_t nf, uint16_t *i, uint16_t *j, intptr_t nnz, int *nrow) -> int",
 *      "map": {"msk": "msk.ptr", "ns": "msk.shape[0]", "nf": "msk.shape[1]", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "nrow": "w.ptr"}}]}
C2PY_END */

int mask_to_coo(int8_t msk[], intptr_t ns, intptr_t nf, uint16_t i[], uint16_t j[],
                intptr_t nnz, int nrow[]) {
    intptr_t mi, mj; int idx;
    /*  int *nrow;
      nrow = (int*) malloc(ns*sizeof(int)); */
    if ((ns < 1) || (ns > 65535))
        return 1;
    if ((nf < 1) || (nf > 65535))
        return 2;
    if (nnz < 1)
        return 3;
        /* pixels per row , 2D image */
#pragma omp parallel for private(mi, mj)
    for (mi = 0; mi < ns; mi++) {
        nrow[mi] = 0;
        for (mj = 0; mj < nf; mj++) {
            if (msk[mi * nf + mj] != 0) {
                nrow[mi]++;
            }
        }
    }
    /* cumsum */
    for (mi = 1; mi < ns; mi++) {
        nrow[mi] += nrow[mi - 1];
    }
    if (nrow[ns - 1] != nnz) {
        return 4;
    }
    /* fill in */
#pragma omp parallel for private(mi, mj, idx)
    for (mi = 0; mi < ns; mi++) {
        if (mi == 0) {
            idx = 0;
        } else {
            idx = nrow[mi - 1];
        }
        if (nrow[mi] > idx) {
            for (mj = 0; mj < nf; mj++) {
                if (msk[mi * nf + mj] != 0) {
                    i[idx] = (uint16_t)mi;
                    j[idx] = (uint16_t)mj;
                    idx++;
                }
            }
        }
    }
    /*  free(nrow); */
    return 0;
}
