#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "misori_orthorhombic(u1: buffer, u2: buffer) -> float",
 *     "doc": "computes the trace of the smallest misorientation\n u1 and u2 are both orientation matrices \"U\"\n     compute u1. u2.T  to get the rotation from one to the other\n     find the flips that will maximise the trace:\n       abs( trace(dot(u1,u2.T) ))\n Looks like point group mmm. Not sure why this is in C?\n Beware: work in progress",
 *     "params": {
 *         "u1": "Orientation matrix U (9-element flattened double).",
 *         "u2": "Orientation matrix U (9-element flattened double).",
 *     },
 *     "checks": [
 *         "u1.format == 'd'",
 *         "u1.n == 9",
 *         "u2.format == 'd'",
 *         "u2.n == 9",
 *     ],
 *     "c_overloads": [{
 *         "sig": "double misori_orthorhombic(const double u1[3][3], const double u2[3][3]) -> double",
 *         "map": {"u1": "u1.ptr", "u2": "u2.ptr"},
 *     }],
 * }
C2PY_END */

double misori_orthorhombic(const double u1[3][3], const double u2[3][3]) {
    /* Compute the trace of the smallest misorientation
     * for orthorhombic symmetry
     *  u1 and u2 are both orientation matrices "U"
     *
     * compute u1. u2.T  to get the rotation from one to the other
     * find the flips - just abs(trace)
     */
    int i, k;
    double ti, t;
    t = 0;
    for (i = 0; i < 3; i++) {
        ti = 0.;
        for (k = 0; k < 3; k++) {
            ti += u1[k][i] * u2[k][i];
        }
        t += fabs(ti);
    }
    return t;
}
