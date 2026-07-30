#include "blobproperties.hpp"

/* C2PY_BEGIN
 * {"py_sig": "blobproperties(data: buffer, labels: buffer, np: int, results: buffer, omega: float = 0.0, verbose: int = 0) -> void",
 *  "doc": "fills the array results with properties of each labelled\nobject described by data (pixel values) and labels. The omega value\nis the angle for this frame.\nresults are FIXME",
 *  "params": {"data": "Input float32 2D.", "labels": "Input int32 labels.", "np": "Number of objects.",
 *      "results": "Output array (np, 36).", "omega": "Omega angle.", "verbose": "Print diagnostics."},
 *  "checks": ["data.ndim == 2",
 *         "data.slow_axis == 0", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == data.n",
 *      "results.format == 'd'", "results.shape[0] == np", "results.shape[1] == 36"],
 *  "gil_release": true,
 *  "c_overloads": [{"when": "data.format == 'f' and data.ndim == 2 and data.slow_axis == 0",
 *         "sig": "void blobproperties(const float *data, const int32_t *labels, int32_t npk, double omega, int verbose, intptr_t ns, intptr_t nf, double *res)",
 *      "map": {"data": "data.ptr", "labels": "labels.ptr", "npk": "np", "omega": "omega", "verbose": "verbose", "ns": "data.shape[0]", "nf": "data.shape[1]", "res": "results.ptr"}}]}
C2PY_END */

extern "C" void blobproperties(const float *data, const int32_t *labels, int32_t npk, double omega,
                    int verbose, intptr_t ns, intptr_t nf, double *res) {
    blobproperties_impl<float>(data, labels, npk, (float)omega, verbose, ns, nf, res);
}

/* C2PY_BEGIN
 * {"py_sig": "blobproperties(data: buffer, labels: buffer, np: int, results: buffer, omega: float = 0.0, verbose: int = 0) -> void",
 *  "c_overloads": [{"when": "data.format == 'B' and data.ndim == 2 and data.slow_axis == 0",
 *         "sig": "void blobproperties_u8(const uint8_t *data, const int32_t *labels, int32_t npk, double omega, int verbose, intptr_t ns, intptr_t nf, double *res)",
 *      "map": {"data": "data.ptr", "labels": "labels.ptr", "npk": "np", "omega": "omega", "verbose": "verbose", "ns": "data.shape[0]", "nf": "data.shape[1]", "res": "results.ptr"}}]}
C2PY_END */

extern "C" void blobproperties_u8(const uint8_t *data, const int32_t *labels,
                                   int32_t npk, double omega, int verbose,
                                   intptr_t ns, intptr_t nf, double *res) {
    blobproperties_impl<uint8_t>(data, labels, npk, (float)omega, verbose, ns, nf, res);
}

/* C2PY_BEGIN
 * {"py_sig": "blobproperties(data: buffer, labels: buffer, np: int, results: buffer, omega: float = 0.0, verbose: int = 0) -> void",
 *  "c_overloads": [{"when": "data.format == 'H' and data.ndim == 2 and data.slow_axis == 0",
 *         "sig": "void blobproperties_u16(const uint16_t *data, const int32_t *labels, int32_t npk, double omega, int verbose, intptr_t ns, intptr_t nf, double *res)",
 *      "map": {"data": "data.ptr", "labels": "labels.ptr", "npk": "np", "omega": "omega", "verbose": "verbose", "ns": "data.shape[0]", "nf": "data.shape[1]", "res": "results.ptr"}}]}
C2PY_END */

extern "C" void blobproperties_u16(const uint16_t *data, const int32_t *labels,
                                    int32_t npk, double omega, int verbose,
                                    intptr_t ns, intptr_t nf, double *res) {
    blobproperties_impl<uint16_t>(data, labels, npk, (float)omega, verbose, ns, nf, res);
}

/* C2PY_BEGIN
 * {"py_sig": "blobproperties(data: buffer, labels: buffer, np: int, results: buffer, omega: float = 0.0, verbose: int = 0) -> void",
 *  "c_overloads": [{"when": "(data.format == 'I' or data.format == 'L') and data.itemsize == 4 and data.ndim == 2 and data.slow_axis == 0",
 *         "sig": "void blobproperties_u32(const uint32_t *data, const int32_t *labels, int32_t npk, double omega, int verbose, intptr_t ns, intptr_t nf, double *res)",
 *      "map": {"data": "data.ptr", "labels": "labels.ptr", "npk": "np", "omega": "omega", "verbose": "verbose", "ns": "data.shape[0]", "nf": "data.shape[1]", "res": "results.ptr"}}]}
C2PY_END */

extern "C" void blobproperties_u32(const uint32_t *data, const int32_t *labels,
                                    int32_t npk, double omega, int verbose,
                                    intptr_t ns, intptr_t nf, double *res) {
    blobproperties_impl<uint32_t>(data, labels, npk, (float)omega, verbose, ns, nf, res);
}
