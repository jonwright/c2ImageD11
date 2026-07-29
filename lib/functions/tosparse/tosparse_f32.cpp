#include "tosparse_impl.hpp"

/* C2PY_BEGIN
 * {"py_sig": "tosparse_f32(img: buffer, msk: buffer, row: buffer, col: buffer, val: buffer, cut: float) -> int",
 *  "doc": "Convert dense float32 image to sparse COO.",
 *  "params": {"img": "Input float32 2D.", "msk": "Mask (uint8).", "row": "Output rows.", "col": "Output cols.", "val": "Output values.", "cut": "Threshold."},
 *  "checks": ["img.format == 'f'", "img.ndim == 2",
 *         "img.slow_axis == 0",
 *      "msk.format == 'B' or msk.format == 'b' or msk.format == '?'", "msk.n == img.n",
 *      "row.format == 'H' or row.itemsize == 2", "col.format == 'H' or col.itemsize == 2",
 *      "val.format == 'f'"],
 *  "c_overloads": [{"sig": "int tosparse_f32(const float *img, const uint8_t *msk, uint16_t *row, uint16_t *col, float *val, float cut, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"img": "img.ptr", "msk": "msk.ptr", "row": "row.ptr", "col": "col.ptr", "val": "val.ptr", "cut": "cut", "ns": "img.shape[0]", "nf": "img.shape[1]"}}]}
C2PY_END */

extern "C" int tosparse_f32(const float * img, const uint8_t * msk,
                             uint16_t * row, uint16_t * col,
                             float * val, float cut,
                             intptr_t ns, intptr_t nf) {
    return tosparse_impl<float>(img, msk, row, col, val, (double)cut, ns, nf);
}
