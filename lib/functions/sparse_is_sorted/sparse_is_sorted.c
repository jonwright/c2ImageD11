#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "sparse_is_sorted(i: buffer, j: buffer) -> int",
 *  "doc": "checks whether the indices in i and j of a sparse\ncoo format come in the order that they would appear inside an image\n*  @param i, j index arrays\n*  @param nnz dimension of i, j\n   returns 0 for all OK\n        k for first non-sorted element\n        -k for first duplicate",
 *  "params": {"i": "Row indices (uint16).", "j": "Col indices (uint16)."},
 *  "checks": ["i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2", "j.n == i.n"],
 *  "c_overloads": [{"sig": "int sparse_is_sorted(const uint16_t *i, const uint16_t *j, intptr_t nnz) -> int",
 *      "map": {"i": "i.ptr", "j": "j.ptr", "nnz": "i.n"}}]}
C2PY_END */

int sparse_is_sorted(const uint16_t i[], const uint16_t j[], intptr_t nnz) {
    intptr_t k; int es, ed;
    es = nnz + 1;
    ed = nnz + 1;
    for (k = 1; k < nnz; k++) {
        if (i[k] < i[k - 1]) { /* bad, not sorted */
            es = (k < es) ? k : es;
            continue;
        }
        if (i[k] == i[k - 1]) {    /* Same row, j must be gt prev */
            if (j[k] < j[k - 1]) { /* bad */
                es = (k < es) ? k : es;
            } else if (j[k] == j[k - 1]) {
                ed = (k < ed) ? k : ed;
            } else {
                continue;
            }
        }
    }
    if ((es == (nnz + 1)) && (ed == (nnz + 1)))
        return 0;
    if (es > ed)
        return -ed;
    else
        return es;
}
