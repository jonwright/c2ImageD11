#include "sparse_connectedpixels.hpp"

/* C2PY_BEGIN
 * {"py_sig": "sparse_connectedpixels(v: buffer, i: buffer, j: buffer, threshold: float, labels: buffer) -> int",
 *  "doc": "runs the connectedpixels algorithm on\na sparse image using a supplied threshold putting labels\ninto labels array and returning the number of blobs found",
 *  "params": {"v": "Values (float32).", "i": "Rows (uint16).", "j": "Cols (uint16).", "threshold": "Threshold.", "labels": "Output labels (int32)."},
 *  "checks": ["v.slow_axis == 0", "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2",
 *      "j.n == i.n", "v.n == i.n", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == i.n"],
 *  "c_overloads": [{"when": "v.format == 'f' and v.slow_axis == 0",
 *         "sig": "int sparse_connectedpixels(const float *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, double threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}}]}
C2PY_END */

extern "C"
int sparse_connectedpixels(float * v, uint16_t * i,
                            uint16_t * j, intptr_t nnz, double threshold,
                            int32_t * labels /* nnz */
) {
    return sparse_connectedpixels_impl<float>(v, i, j, nnz, (float)threshold, labels);
}

/* C2PY_BEGIN
 * {"py_sig": "sparse_connectedpixels(v: buffer, i: buffer, j: buffer, threshold: float, labels: buffer) -> int",
 *  "c_overloads": [{"when": "v.format == 'B' and v.slow_axis == 0",
 *         "sig": "int sparse_connectedpixels_u8(const uint8_t *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, double threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}}]}
C2PY_END */

extern "C" int sparse_connectedpixels_u8(uint8_t * v, uint16_t * i,
                                          uint16_t * j, intptr_t nnz,
                                          double threshold,
                                          int32_t * labels) {
    return sparse_connectedpixels_impl<uint8_t>(v, i, j, nnz, (uint8_t)threshold, labels);
}

/* C2PY_BEGIN
 * {"py_sig": "sparse_connectedpixels(v: buffer, i: buffer, j: buffer, threshold: float, labels: buffer) -> int",
 *  "c_overloads": [{"when": "v.format == 'H' and v.slow_axis == 0",
 *         "sig": "int sparse_connectedpixels_u16(const uint16_t *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, double threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}}]}
C2PY_END */

extern "C" int sparse_connectedpixels_u16(uint16_t * v, uint16_t * i,
                                           uint16_t * j, intptr_t nnz,
                                           double threshold,
                                           int32_t * labels) {
    return sparse_connectedpixels_impl<uint16_t>(v, i, j, nnz, (uint16_t)threshold, labels);
}

/* C2PY_BEGIN
 * {"py_sig": "sparse_connectedpixels(v: buffer, i: buffer, j: buffer, threshold: float, labels: buffer) -> int",
 *  "c_overloads": [{"when": "(v.format == 'I' or v.format == 'L') and v.itemsize == 4 and v.slow_axis == 0",
 *         "sig": "int sparse_connectedpixels_u32(const uint32_t *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, double threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}}]}
C2PY_END */

extern "C" int sparse_connectedpixels_u32(uint32_t * v, uint16_t * i,
                                           uint16_t * j, intptr_t nnz,
                                           double threshold,
                                           int32_t * labels) {
    return sparse_connectedpixels_impl<uint32_t>(v, i, j, nnz, (uint32_t)threshold, labels);
}
