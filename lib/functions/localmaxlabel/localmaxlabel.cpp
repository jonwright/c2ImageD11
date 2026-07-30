#include "localmaxlabel.hpp"

/* C2PY_BEGIN
 * {"py_sig": "localmaxlabel(data: buffer, labels: buffer, wrk: buffer) -> int",
 *  "doc": "assigns a label for each pixel so they are grouped\nto the local maximum. Equal values choose to assign towards the earlier\nvalue in memory.\ncpu arg (1)0=C, (1)1=SSE2, (1)2=AVX2; if > 9 prints timing",
 *  "params": {"data": "Input float32 2D.", "labels": "Output int32 labels.", "wrk": "Temp uint8 workspace."},
 *  "checks": ["data.ndim == 2",
 *         "data.slow_axis == 0", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == data.n",
 *      "wrk.format == 'B' or wrk.format == 'b'", "wrk.n == data.n"],
 *  "c_overloads": [{"when": "data.format == 'f' and data.ndim == 2 and data.slow_axis == 0",
 *         "sig": "int localmaxlabel(const float *im, int32_t *lout, uint8_t *l, intptr_t dim0, intptr_t dim1) -> int"
 *      "map": {"im": "data.ptr", "lout": "labels.ptr", "l": "wrk.ptr", "dim0": "data.shape[0]", "dim1": "data.shape[1]"}}]}
C2PY_END */

extern "C" int localmaxlabel(const float * im, int32_t * lout,
                   uint8_t * l, intptr_t dim0, intptr_t dim1) {
    return localmaxlabel_impl<float>(im, lout, l, dim0, dim1);
}

/* C2PY_BEGIN
 * {"py_sig": "localmaxlabel(data: buffer, labels: buffer, wrk: buffer) -> int",
 *  "c_overloads": [{"when": "data.format == 'B' and data.ndim == 2 and data.slow_axis == 0",
 *         "sig": "int localmaxlabel_u8(const uint8_t *im, int32_t *lout, uint8_t *l, intptr_t dim0, intptr_t dim1) -> int",
 *      "map": {"im": "data.ptr", "lout": "labels.ptr", "l": "wrk.ptr", "dim0": "data.shape[0]", "dim1": "data.shape[1]"}}]}
C2PY_END */

extern "C" int localmaxlabel_u8(const uint8_t * im, int32_t * lout,
                                 uint8_t * l, intptr_t dim0, intptr_t dim1) {
    return localmaxlabel_impl<uint8_t>(im, lout, l, dim0, dim1);
}

/* C2PY_BEGIN
 * {"py_sig": "localmaxlabel(data: buffer, labels: buffer, wrk: buffer) -> int",
 *  "c_overloads": [{"when": "data.format == 'H' and data.ndim == 2 and data.slow_axis == 0",
 *         "sig": "int localmaxlabel_u16(const uint16_t *im, int32_t *lout, uint8_t *l, intptr_t dim0, intptr_t dim1) -> int",
 *      "map": {"im": "data.ptr", "lout": "labels.ptr", "l": "wrk.ptr", "dim0": "data.shape[0]", "dim1": "data.shape[1]"}}]}
C2PY_END */

extern "C" int localmaxlabel_u16(const uint16_t * im, int32_t * lout,
                                  uint8_t * l, intptr_t dim0, intptr_t dim1) {
    return localmaxlabel_impl<uint16_t>(im, lout, l, dim0, dim1);
}

/* C2PY_BEGIN
 * {"py_sig": "localmaxlabel(data: buffer, labels: buffer, wrk: buffer) -> int",
 *  "c_overloads": [{"when": "(data.format == 'I' or data.format == 'L') and data.itemsize == 4 and data.ndim == 2 and data.slow_axis == 0",
 *         "sig": "int localmaxlabel_u32(const uint32_t *im, int32_t *lout, uint8_t *l, intptr_t dim0, intptr_t dim1) -> int",
 *      "map": {"im": "data.ptr", "lout": "labels.ptr", "l": "wrk.ptr", "dim0": "data.shape[0]", "dim1": "data.shape[1]"}}]}
C2PY_END */

extern "C" int localmaxlabel_u32(const uint32_t * im, int32_t * lout,
                                  uint8_t * l, intptr_t dim0, intptr_t dim1) {
    return localmaxlabel_impl<uint32_t>(im, lout, l, dim0, dim1);
}
