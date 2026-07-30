#include "sparse_localmaxlabel.hpp"

/* C2PY_BEGIN
 * {"py_sig": "sparse_localmaxlabel(v: buffer, i: buffer, j: buffer, MV: buffer, iMV: buffer, labels: buffer) -> int",
 *  "doc": "assigns labels to sparse array in sorted coo format\nsupplied in (v,(i,j)). MV and iMV are temporaries.\nsingle threaded",
 *  "params": {"v": "Values (float32).", "i": "Rows (uint16).", "j": "Cols (uint16).",
 *      "MV": "Temp float32.", "iMV": "Temp int32.", "labels": "Output labels (int32)."},
 *  "checks": ["v.slow_axis == 0", "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2",
 *      "j.n == i.n", "v.n == i.n", "MV.format == 'f'", "MV.n == i.n",
 *      "( iMV.format == 'i' or iMV.format == 'l' )", "iMV.n == i.n", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == i.n"],
 *  "c_overloads": [{"when": "v.format == 'B' and v.slow_axis == 0",
 *         "sig": "int sparse_localmaxlabel_u8(const uint8_t *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, float *MV, int32_t *iMV, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "MV": "MV.ptr", "iMV": "iMV.ptr", "labels": "labels.ptr"}}]}
C2PY_END */

extern "C" int sparse_localmaxlabel_u8(uint8_t *restrict v, uint16_t *restrict i,
                                        uint16_t *restrict j, intptr_t nnz,
                                        float *restrict MV, int32_t *restrict iMV,
                                        int32_t *restrict labels) {
    return sparse_localmaxlabel_impl<uint8_t>(v, i, j, nnz, MV, iMV, labels);
}
