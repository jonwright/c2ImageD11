#include "connectedpixels.hpp"

/* C2PY_BEGIN
 * {"py_sig": "connectedpixels(data: buffer, labels: buffer, threshold: float, verbose: int = 0, con8: int = 1) -> int",
 *  "doc": "Determines which pixels in data are above the\nuser supplied threshold and assigns them into connected objects\nwhich are output in labels. Connectivity is 3x3 box (8) by default\nand reduces to a +(4) is con8==0",
 *  "params": {"data": "Input float32 2D.", "labels": "Output int32 labels.", "threshold": "Threshold.",
 *      "verbose": "Print diagnostics.", "con8": "8-connected (1) or 4-connected (0)."},
 *  "checks": ["data.ndim == 2",
 *         "data.slow_axis == 0", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == data.n"],
 *  "c_overloads": [{"when": "data.format == 'H' and data.ndim == 2 and data.slow_axis == 0",
  *         "sig": "int connectedpixels_u16(const uint16_t *data, int32_t *labels, double threshold, int verbose, int eightconnected, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"data": "data.ptr", "labels": "labels.ptr", "threshold": "threshold", "verbose": "verbose", "eightconnected": "con8", "ns": "data.shape[0]", "nf": "data.shape[1]"}}]}
C2PY_END */

extern "C" int connectedpixels_u16(const uint16_t *data, int32_t *labels,
                                     double threshold, int verbose,
                                     int eightconnected, intptr_t ns, intptr_t nf) {
    return connectedpixels_impl<uint16_t>(data, labels, (uint16_t)threshold,
                                           verbose, eightconnected, ns, nf);
}
