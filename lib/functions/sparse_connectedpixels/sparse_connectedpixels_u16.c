#include "cImageD11.h"
#include "blobs.h"
#include "cimaged11utils.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>

extern int sparse_is_sorted(const uint16_t i[], const uint16_t j[], intptr_t nnz);

/* C2PY_BEGIN
 * {"py_sig": "sparse_connectedpixels(v: buffer, i: buffer, j: buffer, threshold: float, labels: buffer) -> int",
 *  "doc": "runs the connectedpixels algorithm on\na sparse image using a supplied threshold putting labels\ninto labels array and returning the number of blobs found",
 *  "params": {"v": "Values (float32).", "i": "Rows (uint16).", "j": "Cols (uint16).", "threshold": "Threshold.", "labels": "Output labels (int32)."},
 *  "checks": ["v.slow_axis == 0", "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2",
 *      "j.n == i.n", "v.n == i.n", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == i.n"],
 *  "c_overloads": [
 *      {"when": "v.format == 'f' and v.slow_axis == 0",
 *         "sig": "int sparse_connectedpixels_f32(const float *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, float threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}},
 *      {"when": "v.format == 'B' and v.slow_axis == 0",
 *         "sig": "int sparse_connectedpixels_u8(const uint8_t *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, uint8_t threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}},
 *      {"when": "v.format == 'H' and v.slow_axis == 0",
 *         "sig": "int sparse_connectedpixels_u16(const uint16_t *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, uint16_t threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}},
 *      {"when": "v.format == 'I' and v.slow_axis == 0",
 *         "sig": "int sparse_connectedpixels_u32(const uint32_t *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, uint32_t threshold, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "threshold": "threshold", "labels": "labels.ptr"}}
 *  ]}
C2PY_END */

/* Instantiate for uint16_t */
#define T_val uint16_t
#define SPARSE_CONNECTEDPIXELS_IMPL_NAME sparse_connectedpixels_impl_u16
#include "sparse_connectedpixels.hpp"
#undef SPARSE_CONNECTEDPIXELS_IMPL_NAME
#undef T_val

int sparse_connectedpixels_u16(uint16_t *restrict v, uint16_t *restrict i,
                               uint16_t *restrict j, intptr_t nnz,
                               uint16_t threshold,
                               int32_t *restrict labels) {
    return sparse_connectedpixels_impl_u16(v, i, j, nnz, threshold, labels);
}
