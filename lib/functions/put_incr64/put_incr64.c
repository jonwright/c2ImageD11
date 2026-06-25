#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "put_incr64(data: buffer, ind: buffer, vals: buffer, boundscheck: int = 0) -> void",
 *     "doc": "put_incr64 does the simple loop: data[ind] += vals, 64 bit addressing",
 *     "params": {
 *         "data": "Destination array (float32). Updated in place with scatter-add.",
 *         "ind": "Indices array (int64).",
 *         "vals": "Values array (float32) to add.",
 *         "boundscheck": "If non-zero, enables bounds checking on ind. Default 0 (no check).",
 *     },
 *     "checks": [
 *         "data.format == 'f'",
 *         "ind.format == 'q' or ind.itemsize == 8",
 *         "ind.n == vals.n",
 *         "vals.format == 'f'",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "data.format == 'f' and vals.format == 'f'",
 *         "sig": "void put_incr64(float *data, const int64_t *ind, const float *vals, int boundscheck, intptr_t n, intptr_t m)",
 *         "map": {"data": "data.ptr", "ind": "ind.ptr", "vals": "vals.ptr", "boundscheck": "boundscheck", "n": "ind.n", "m": "data.n"},
 *     }],
 * }
C2PY_END */

void put_incr64(float data[], const int64_t ind[], const float vals[], int boundscheck,
                intptr_t n, intptr_t m) {
    int64_t k, ik;
    if (boundscheck == 0) {
        for (k = 0; k < n; k++)
            data[ind[k]] += vals[k];
    } else {
        for (k = 0; k < n; k++) {
            ik = ind[k];
            if (ik < 0 || ik >= m) {
                printf("Array bounds error! k=%d ind[k]=%d\n", (int)k,
                       (int)ind[k]);
            } else {
                data[ind[k]] += vals[k];
            }
        }
    }
}
