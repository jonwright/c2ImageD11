#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "quickorient(ubi: buffer, bt: buffer) -> void",
 *     "doc": "quickorient takes two g-vectors in UBI and overwrites with UBI orientation using cache in bt.",
 *     "params": {
 *         "ubi": "Orientation matrix (9-element). First 2 rows are g-vectors on entry; overwritten with UBI on exit.",
 *         "bt": "Busing-Levy cache (9-element).",
 *     },
 *     "checks": ["ubi.format == 'd'", "ubi.ndim == 2", "ubi.shape[0] == 3", "ubi.shape[1] == 3",
 *                "bt.format == 'd'", "bt.ndim == 2", "bt.shape[0] == 3", "bt.shape[1] == 3"],
 *     "c_overloads": [{
 *         "sig": "void quickorient(double ubi[3][3], const double bt[3][3])",
 *         "map": {"ubi": "ubi.ptr", "bt": "bt.ptr"},
 *     }],
 * }
C2PY_END */

void quickorient(double UBI[9], const double BT[9]) {
    /* On entry UBI[0] is g1, UBI[1] is g2, BT is made for this to work.
       0 1 2  == g1
       3 4 5  == g2
       6 7 8  <- g1xg2
     */
    double t0, t1, M[9];
    /* g2 = g0xg1 */
    M[6] = UBI[1] * UBI[5] - UBI[2] * UBI[4];
    M[7] = UBI[2] * UBI[3] - UBI[0] * UBI[5];
    M[8] = UBI[0] * UBI[4] - UBI[1] * UBI[3];
    /* u0 = norm(g0) */
    t0 = sqrt(UBI[0] * UBI[0] + UBI[1] * UBI[1] + UBI[2] * UBI[2]);
    M[0] = UBI[0] / t0;
    M[1] = UBI[1] / t0;
    M[2] = UBI[2] / t0;
    /* u3 = norm(g3) */
    t1 = sqrt(M[6] * M[6] + M[7] * M[7] + M[8] * M[8]);
    M[6] /= t1;
    M[7] /= t1;
    M[8] /= t1;
    /* u2 = u1xu3 */
    M[3] = M[1] * M[8] - M[2] * M[7];
    M[4] = M[2] * M[6] - M[0] * M[8];
    M[5] = M[0] * M[7] - M[1] * M[6];
    /* ubi = dot( BT, (u1,u2,u2) */
    UBI[0] = BT[0] * M[0] + BT[1] * M[3] + BT[2] * M[6];
    UBI[1] = BT[0] * M[1] + BT[1] * M[4] + BT[2] * M[7];
    UBI[2] = BT[0] * M[2] + BT[1] * M[5] + BT[2] * M[8];
    UBI[3] = BT[3] * M[0] + BT[4] * M[3] + BT[5] * M[6];
    UBI[4] = BT[3] * M[1] + BT[4] * M[4] + BT[5] * M[7];
    UBI[5] = BT[3] * M[2] + BT[4] * M[5] + BT[5] * M[8];
    UBI[6] = BT[6] * M[0] + BT[7] * M[3] + BT[8] * M[6];
    UBI[7] = BT[6] * M[1] + BT[7] * M[4] + BT[8] * M[7];
    UBI[8] = BT[6] * M[2] + BT[7] * M[5] + BT[8] * M[8];
}
