#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "tosparse_u32(img: buffer, msk: buffer, row: buffer, col: buffer, val: buffer, cut: float) -> int",
 *  "doc": "Convert dense uint32 image to sparse COO.",
 *  "params": {"img": "Input uint32 2D.", "msk": "Mask (uint8).", "row": "Output rows.", "col": "Output cols.", "val": "Output values.", "cut": "Threshold (float)."},
 *  "checks": ["img.format == 'I' or img.itemsize == 4", "img.ndim == 2",
 *      "msk.format == 'B' or msk.format == 'b' or msk.format == '?'", "msk.n == img.n",
 *      "row.format == 'H' or row.itemsize == 2", "col.format == 'H' or col.itemsize == 2",
 *      "val.format == 'I' or val.itemsize == 4"],
 *  "c_overloads": [{"sig": "int tosparse_u32(const uint32_t *img, const uint8_t *msk, uint16_t *row, uint16_t *col, uint32_t *val, float cut, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"img": "img.ptr", "msk": "msk.ptr", "row": "row.ptr", "col": "col.ptr", "val": "val.ptr", "cut": "cut", "ns": "img.shape[0]", "nf": "img.shape[1]"}}]}
C2PY_END */

int tosparse_u32(uint32_t *restrict img, uint8_t *restrict msk,
                 uint16_t *restrict row, uint16_t *restrict col,
                 uint32_t *restrict val, float cut, intptr_t ns, intptr_t nf) {
    intptr_t i; int k;
    uint32_t uicut;
    uicut = (uint32_t)cut;
    k = 0;
    for (i = 0; i < ns * nf; i++) {
        if (msk[i] && (img[i] > uicut)) {
            row[k] = i / nf;
            col[k] = i % nf;
            val[k] = img[i];
            k++;
        }
    }
    return k;
}
