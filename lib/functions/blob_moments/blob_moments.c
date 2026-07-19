#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "blob_moments(results: buffer) -> void",
 *  "doc": "fills in the reduced moments in results array.\n... FIXME - this would be clearer in python, fast anyway.",
 *  "params": {"results": "I/O array (np, 36). Raw moments in, reduced out."},
 *  "checks": ["results.format == 'd'", "results.ndim == 2", "results.shape[1] == 36"],
 *  "c_overloads": [{"sig": "void blob_moments(double *res, intptr_t np)",
 *      "map": {"res": "results.ptr", "np": "results.shape[0]"}}]}
C2PY_END */

void blob_moments(double *res, intptr_t np) { compute_moments(res, np); }
