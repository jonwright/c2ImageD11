#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "coverlaps(row1: buffer, col1: buffer, labels1: buffer, row2: buffer, col2: buffer, labels2: buffer, mat: buffer, results: buffer) -> int",
 *  "doc": "Determine overlapping labels between two sparse frames.",
 *  "params": {"row1": "Rows 1 (uint16).", "col1": "Cols 1 (uint16).", "labels1": "Labels 1 (int32).",
 *      "row2": "Rows 2 (uint16).", "col2": "Cols 2 (uint16).", "labels2": "Labels 2 (int32).",
 *      "mat": "Output overlap matrix (int32).", "results": "Output triples (int32)."},
 *  "checks": ["row1.format == 'H' or row1.itemsize == 2", "col1.format == 'H' or col1.itemsize == 2", "col1.n == row1.n",
 *      "labels1.format == 'i' or labels1.format == 'l'", "labels1.n == row1.n",
 *      "row2.format == 'H' or row2.itemsize == 2", "col2.format == 'H' or col2.itemsize == 2", "col2.n == row2.n",
 *      "labels2.format == 'i' or labels2.format == 'l'", "labels2.n == row2.n",
 *      "( mat.format == 'i' or mat.format == 'l' )", "mat.ndim == 2", "( results.format == 'i' or results.format == 'l' )"],
 *  "c_overloads": [{"sig": "int coverlaps(const uint16_t *row1, const uint16_t *col1, const int *labels1, intptr_t nnz1, const uint16_t *row2, const uint16_t *col2, const int *labels2, intptr_t nnz2, int *mat, intptr_t npk1, intptr_t npk2, int *results) -> int",
 *      "map": {"row1": "row1.ptr", "col1": "col1.ptr", "labels1": "labels1.ptr", "nnz1": "row1.n",
 *          "row2": "row2.ptr", "col2": "col2.ptr", "labels2": "labels2.ptr", "nnz2": "row2.n",
 *          "mat": "mat.ptr", "npk1": "mat.shape[0]", "npk2": "mat.shape[1]", "results": "results.ptr"}}]}
C2PY_END */

int coverlaps(uint16_t *restrict row1, uint16_t *restrict col1,
              int *restrict labels1, intptr_t nnz1, uint16_t *restrict row2,
              uint16_t *restrict col2, int *restrict labels2, intptr_t nnz2,
              int *restrict mat, int npk1, int npk2, int *restrict results) {
    intptr_t i1, i2; int npk;
    uint32_t p1, p2;
    //    printf("nnz %d %d %d %d\n",nnz1,nnz2,npk1,npk2);
    for (i1 = 0; i1 < npk1 * npk2; i1++) {
        mat[i1] = 0;
    }
    i1 = 0;
    i2 = 0;
    while ((i1 < nnz1) && (i2 < nnz2)) {
        p1 = (((uint32_t)row1[i1]) << 16) + col1[i1];
        p2 = (((uint32_t)row2[i2]) << 16) + col2[i2];
        //        printf("%d ijij %d %d %d %d %d %d %d
        //        %d\n",k,i1,i2,row1[i1],col1[i1],row2[i2],col2[i2], p1, p2);
        if (p1 == p2) {
            mat[(labels1[i1] - 1) * npk2 + labels2[i2] - 1] += 1;
            i1++;
            i2++;
        } else if (p1 > p2) {
            i2++;
        } else {
            i1++;
        }
    }
    npk = 0;
    for (i1 = 0; i1 < npk1; i1++) {
        for (i2 = 0; i2 < npk2; i2++) {
            if (mat[i1 * npk2 + i2] > 0) {
                results[npk * 3] = i1 + 1;
                results[npk * 3 + 1] = i2 + 1;
                results[npk * 3 + 2] = mat[i1 * npk2 + i2];
                npk++;
            }
        }
    }
    return npk;
}
