#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "put_incr32(data: buffer, ind: buffer, vals: buffer, boundscheck: int = 0) -> void",
 *     "doc": "does the simple loop : data[ind] += vals\nnot sure why this isn't in numpy\nuses 32 bit addressing",
 *     "params": {
 *         "data": "Destination array (float32).",
 *         "ind": "Indices array (int32).",
 *         "vals": "Values array (float32) to add.",
 *         "boundscheck": "If non-zero, enables bounds checking on ind.",
 *     },
 *     "checks": [
 *         "data.format == 'f'",
 *         "( ind.format == 'i' or ind.format == 'l' )",
 *         "ind.n == vals.n",
 *         "vals.format == 'f'",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "data.format == 'f' and vals.format == 'f' and (ind.format == 'i' or ind.format == 'l')",
 *         "sig": "void put_incr32(float *data, const int32_t *ind, const float *vals, int boundscheck, intptr_t n, intptr_t m)",
 *         "map": {"data": "data.ptr", "ind": "ind.ptr", "vals": "vals.ptr", "boundscheck": "boundscheck", "n": "ind.n", "m": "data.n"},
 *     }],
 * }
C2PY_END */

void put_incr32(float data[], const int32_t ind[], const float vals[], int boundscheck,
                intptr_t n, intptr_t m) {
    int32_t k, ik;
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
