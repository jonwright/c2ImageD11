#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "closest(x: buffer, v: buffer) -> void",
 *     "doc": "closest finds the value and index in x closest to a value in v.",
 *     "params": {
 *         "x": "Array of candidate values to search (e.g. ideal cosines from hkl geometry).",
 *         "v": "Array of values to search for (e.g. experimental cosines).",
 *     },
 *     "checks": [
 *         "x.format == 'd'",
 *         "v.format == 'd'",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void closest(const double *x, const double *v, int *ribest, double *rbest, intptr_t nx, intptr_t nv)",
 *         "outputs": {"ribest": "int", "rbest": "double"},
 *         "doc": "Standard O(nx*nv) scan-find-closest.",
 *         "map": {"x": "x.ptr", "v": "v.ptr", "nx": "x.n", "nv": "v.n"},
 *     }],
 * }
C2PY_END */

void closest(const double x[], const double v[], int *ribest, double *rbest, intptr_t nx,
             intptr_t nv) {
    /*
     * Finds value and index in x closest to a value in v
     */
    intptr_t i, j; int ibest;
    double best;
    best = DBL_MAX;
    ibest = 0;
    for (i = 0; i < nx; i++) {
        for (j = 0; j < nv; j++) {
            if (fabs(x[i] - v[j]) < best) {
                best = fabs(x[i] - v[j]);
                ibest = i;
            }
        }
    }
    *ribest = ibest;
    *rbest = best;
}
