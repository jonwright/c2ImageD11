#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "doc": "takes a ubi matrix and list of g-vectors and computes\nhkl = dot(ubi, gv), then rounds these g-vectors to integer\nand computes drlv2 = (h-int(h))**2 + (k-int(k))**2 + (l-int(l))**2\nIf drlv2 is less than tol*tol then the peak is considered to\nbe indexed. Returns the number of peaks found.",
 *     "params": {
 *         "ubi": "Orientation matrix UBI (UB inverse), shape (9,) flattened double.",
 *         "gv": "G-vectors array, shape (ng, 3) flattened.",
 *         "tol": "Tolerance on |h - round(h)|.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gv.ndim == 2",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[1] == 3 and gv.slow_axis == 0",
 *         "sig": "int score(const double ubi[3][3], const double gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }, {
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[1] == 3 and gv.slow_axis == 0",
 *         "sig": "int score_f32(const double ubi[3][3], const float gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */

int score(const vec ubi[3], const double gv[], double tol, intptr_t ng) {
    /*
     * Counts g-vectors indexed by ubi within tol
     */
    double sumsq, h0, h1, h2, atol;
    int n; intptr_t k;
    n = 0;
    atol = tol * tol;
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k*3] + ubi[0][1] * gv[k*3+1] + ubi[0][2] * gv[k*3+2];
        h0 -= conv_double_to_int_fast(h0);
        h1 = ubi[1][0] * gv[k*3] + ubi[1][1] * gv[k*3+1] + ubi[1][2] * gv[k*3+2];
        h1 -= conv_double_to_int_fast(h1);
        h2 = ubi[2][0] * gv[k*3] + ubi[2][1] * gv[k*3+1] + ubi[2][2] * gv[k*3+2];
        h2 -= conv_double_to_int_fast(h2);
        sumsq = h0 * h0 + h1 * h1 + h2 * h2;
        if (sumsq < atol) {
            n = n + 1;
        }
    }
    return n;
}

/* f32 scalar fallback (called by dispatch on non-x86 or when ISA unavailable) */
int score_f32(const double ubi[3][3], const float gv[], double tol, intptr_t ng) {
    int n = 0;
    double t2 = tol * tol, magic = 6755399441055744.0;
    intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = gv[k*3], gy = gv[k*3+1], gz = gv[k*3+2];
        double h0 = ubi[0][0]*gx + ubi[0][1]*gy + ubi[0][2]*gz;
        h0 -= ((h0 + magic) - magic);
        double h1 = ubi[1][0]*gx + ubi[1][1]*gy + ubi[1][2]*gz;
        h1 -= ((h1 + magic) - magic);
        double h2 = ubi[2][0]*gx + ubi[2][1]*gy + ubi[2][2]*gz;
        h2 -= ((h2 + magic) - magic);
        if (h0*h0 + h1*h1 + h2*h2 < t2) n++;
    }
    return n;
}
