#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "sparse_overlaps(i1: buffer, j1: buffer, k1: buffer, i2: buffer, j2: buffer, k2: buffer) -> int",
 *  "doc": "Find overlapping pixels between two sparse arrays.",
 *  "params": {"i1": "Rows 1 (uint16).", "j1": "Cols 1 (uint16).", "k1": "Output indices into 1.",
 *      "i2": "Rows 2 (uint16).", "j2": "Cols 2 (uint16).", "k2": "Output indices into 2."},
 *  "checks": ["i1.format == 'H' or i1.itemsize == 2", "j1.format == 'H' or j1.itemsize == 2", "j1.n == i1.n",
 *      "k1.format == 'i' or k1.format == 'l'", "k1.n == i1.n",
 *      "i2.format == 'H' or i2.itemsize == 2", "j2.format == 'H' or j2.itemsize == 2", "j2.n == i2.n",
 *      "k2.format == 'i' or k2.format == 'l'", "k2.n == i2.n"],
 *  "c_overloads": [{"sig": "int sparse_overlaps(const uint16_t *i1, const uint16_t *j1, int *k1, intptr_t nnz1, const uint16_t *i2, const uint16_t *j2, int *k2, intptr_t nnz2) -> int",
 *      "map": {"i1": "i1.ptr", "j1": "j1.ptr", "k1": "k1.ptr", "nnz1": "i1.n", "i2": "i2.ptr", "j2": "j2.ptr", "k2": "k2.ptr", "nnz2": "i2.n"}}]}
C2PY_END */

int sparse_overlaps(uint16_t *restrict i1, uint16_t *restrict j1,
                    int *restrict k1, intptr_t nnz1, uint16_t *restrict i2,
                    uint16_t *restrict j2, int *restrict k2, intptr_t nnz2

) {
    /*
     * Identify the overlapping pixels that are common to both
     *   i1[k1]==i2[k2] ; j1[k1]==j2[k2];
     *   fill in k1/k2
     */
    int p1, p2, nhit;
    p1 = 0;
    p2 = 0;
    nhit = 0;
    while ((p1 < nnz1) && (p2 < nnz2)) {
        /* Three cases:
         * k1 and k2 are the same pixel or one or the other is ahead */
        if (i1[p1] > i2[p2]) {
            p2++;
        } else if (i1[p1] < i2[p2]) {
            p1++;
        } else { /* i1==i2 */
            if (j1[p1] > j2[p2]) {
                p2++;
            } else if (j1[p1] < j2[p2]) {
                p1++;
            } else { /* i1=i2,j1=j2 */
                k1[nhit] = p1;
                k2[nhit] = p2;
                nhit++;
                p1++;
                p2++;
            }
        }
    }
    for (p1 = nhit; p1 < nnz1; p1++)
        k1[p1] = 0;
    for (p2 = nhit; p2 < nnz2; p2++)
        k2[p2] = 0;
    return nhit;
}
