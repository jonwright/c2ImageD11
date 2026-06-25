#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "misori_cubic(u1: buffer, u2: buffer) -> float",
 *     "doc": "misori_cubic computes the smallest misorientation for cubic symmetry.",
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
 *         "sig": "double misori_cubic(const double u1[3][3], const double u2[3][3]) -> double",
 *         "map": {"u1": "u1.ptr", "u2": "u2.ptr"},
 *     }],
 * }
C2PY_END */

double misori_cubic(const double u1[3][3], const double u2[3][3]) {
    /* Compute the trace of the smallest misorientation
     * for cubic symmetry
     *  u1 and u2 are both orientation matrices "U"
     *
     * compute u1. u2.T  to get the rotation from one to the other
     * find the permutation that will maximise the trace
     *   one of six...
     *      xyz   yxz   zxy
     *      xzy   yzx   zyx
     */
    int i, j, k;
    double t[6], m1, m2, m3;
    vec r[3];
    for (i = 0; i < 3; i++) {
        for (j = 0; j < 3; j++) {
            r[i][j] = 0.;
            for (k = 0; k < 3; k++)
                r[i][j] += u1[k][i] * u2[k][j];
        }
    }
    /* 6 possibilities, 18 entries, each appears twice
       [0,0][1,1][2,2]
       [0,0][1,2][2,1]
       [0,1][1,0][2,2]
       [0,1][2,0][1,2]
       [0,2][1,0][2,1]
       [0,2][2,0][1,1]
     */
    t[0] = fabs(r[0][0]) + fabs(r[1][1]) + fabs(r[2][2]);
    t[1] = fabs(r[0][0]) + fabs(r[1][2]) + fabs(r[2][1]);
    t[2] = fabs(r[0][1]) + fabs(r[1][0]) + fabs(r[2][2]);
    t[3] = fabs(r[0][1]) + fabs(r[2][0]) + fabs(r[1][2]);
    t[4] = fabs(r[0][2]) + fabs(r[1][0]) + fabs(r[2][1]);
    t[5] = fabs(r[0][2]) + fabs(r[2][0]) + fabs(r[1][1]);
    /* select the maximum */
    m1 = (t[0] > t[1]) ? t[0] : t[1];
    m2 = (t[2] > t[3]) ? t[2] : t[3];
    m3 = (t[4] > t[5]) ? t[4] : t[5];
    m2 = (m2 > m3) ? m2 : m3;
    m1 = (m1 > m2) ? m1 : m2;
    return m1;
}
