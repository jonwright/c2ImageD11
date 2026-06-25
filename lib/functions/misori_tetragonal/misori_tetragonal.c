#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "misori_tetragonal(u1: buffer, u2: buffer) -> float",
 *     "doc": "misori_tetragonal computes the smallest misorientation for tetragonal symmetry.",
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
 *         "sig": "double misori_tetragonal(const double u1[3][3], const double u2[3][3]) -> double",
 *         "map": {"u1": "u1.ptr", "u2": "u2.ptr"},
 *     }],
 * }
C2PY_END */

double misori_tetragonal(const double u1[3][3], const double u2[3][3]) {
    /* Compute the trace of the smallest misorientation
     * for orthorhombic symmetry
     *  u1 and u2 are both orientation matrices "U"
     *
     * compute u1. u2.T  to get the rotation from one to the other
     * find the flips for c and select ab versus ba
     */
    int i, j, k;
    double m1, m2, m3;
    vec r[3];
    /* c-axis */
    m3 = 0.;
    for (k = 0; k < 3; k++) {
        m3 += u1[k][2] * u2[k][2];
    }
    m3 = fabs(m3);
    /* ab */
    for (i = 0; i < 2; i++) {
        for (j = 0; j < 2; j++) {
            r[i][j] = 0.;
            for (k = 0; k < 3; k++) {
                r[i][j] += u1[k][i] * u2[k][j];
            }
        }
    }
    m1 = fabs(r[0][0]) + fabs(r[1][1]);
    m2 = fabs(r[1][0]) + fabs(r[0][1]);
    if (m1 > m2) {
        return m1 + m3;
    } else {
        return m2 + m3;
    }
}
