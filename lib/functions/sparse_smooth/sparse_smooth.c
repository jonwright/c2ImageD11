#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "sparse_smooth(v: buffer, i: buffer, j: buffer, s: buffer) -> void",
 *  "doc": "smooths data in coo format. Workaround for avoiding\nequal pixels on peak tails for localmaxlabel\nsingle threaded",
 *  "params": {"v": "Values (float32).", "i": "Rows (uint16).", "j": "Cols (uint16).", "s": "Output smoothed (float32)."},
 *  "checks": ["v.format == 'f'", "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2",
 *      "j.n == i.n", "v.n == i.n", "s.format == 'f'", "s.n == i.n"],
 *  "c_overloads": [{"sig": "void sparse_smooth(const float *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, float *s)",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "s": "s.ptr"}}]}
C2PY_END */

void sparse_smooth(float *restrict v,    // input image
                   uint16_t *restrict i, // indices
                   uint16_t *restrict j,
                   intptr_t nnz,             // bounds
                   float *restrict s) { // smoothed output
    int k, di, dj, r, prow, p;
    float m;
    m = 1.0 / 16.0;
    /* First make a copy */
    for (k = 0; k < nnz; k++) {
        s[k] = v[k] * m;
    }
    /*   2 1 2   == distance. 3-x:   1 2 1
         1 0 1                       2 3 2
         2 1 2                       1 2 1  total = 15
         */
    prow = 0;
    for (k = 0; k < nnz; k++) {
        while ((int)i[prow] < (int)(i[k] - 1)) {
            prow++; /* find this row */
        }
        p = prow;
        while (i[p] <= (i[k] + 1)) {
            di = (int)i[p] - (int)i[k];
            dj = (int)j[p] - (int)j[k];
            r = di * di + dj * dj; //  # 1 or 1+1 for neighbors
            if (r < 3) {
                s[k] += v[p] * (m * (float)(3 - r));
            }
            p++;
            if (p == nnz)
                break;
        }
    }
}
