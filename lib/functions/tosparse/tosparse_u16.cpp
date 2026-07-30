#include "tosparse_impl.hpp"

/* C2PY_BEGIN
 * {"py_sig": "tosparse_u16(img: buffer, msk: buffer, row: buffer, col: buffer, val: buffer, cut: int) -> int",
 *  "doc": "stores pixels from img into row/col/val.\nmsk determines whether pixels are masked (e.g. eiger mask)\nreturns the number of pixels found",
 *  "params": {"img": "Input uint16 2D.", "msk": "Mask (uint8, 0=include).", "row": "Output rows.", "col": "Output cols.", "val": "Output values.", "cut": "Threshold."},
 *  "checks": ["img.format == 'H' or img.itemsize == 2", "img.ndim == 2",
 *         "img.slow_axis == 0",
 *      "msk.format == 'B' or msk.format == 'b' or msk.format == '?'", "msk.n == img.n",
 *      "row.format == 'H' or row.itemsize == 2", "col.format == 'H' or col.itemsize == 2",
 *      "val.format == 'H' or val.itemsize == 2"],
 *  "c_overloads": [{"sig": "int tosparse_u16(const uint16_t *img, const uint8_t *msk, uint16_t *row, uint16_t *col, uint16_t *val, int cut, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"img": "img.ptr", "msk": "msk.ptr", "row": "row.ptr", "col": "col.ptr", "val": "val.ptr", "cut": "cut", "ns": "img.shape[0]", "nf": "img.shape[1]"}}]}
C2PY_END */

extern "C" int tosparse_u16(const uint16_t * img, const uint8_t * msk,
                             uint16_t * row, uint16_t * col,
                             uint16_t * val, int cut,
                             intptr_t ns, intptr_t nf) {
    return tosparse_impl<uint16_t>(img, msk, row, col, val, (double)cut, ns, nf);
}
