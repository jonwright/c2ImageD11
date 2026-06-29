#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "doc": "Count g-vectors indexed by ubi matrix within tol.",
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
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3",
 *         "sig": "int score_sov_f64(const double ubi[3][3], const double gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
 *     }, {
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[1] == 3 and gv.slow_axis == 0",
 *         "sig": "int score_f32(const double ubi[3][3], const float gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }, {
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[0] == 3 and gv.slow_axis == 0 and gv.shape[1] != 3",
 *         "sig": "int score_sov_f32(const double ubi[3][3], const float gv[], double tol, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[1]"},
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
    double t2 = tol * tol;
    intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = gv[k*3], gy = gv[k*3+1], gz = gv[k*3+2];
        double h0 = ubi[0][0]*gx + ubi[0][1]*gy + ubi[0][2]*gz;
        h0 -= nearbyint(h0);
        double h1 = ubi[1][0]*gx + ubi[1][1]*gy + ubi[1][2]*gz;
        h1 -= nearbyint(h1);
        double h2 = ubi[2][0]*gx + ubi[2][1]*gy + ubi[2][2]*gz;
        h2 -= nearbyint(h2);
        if (h0*h0 + h1*h1 + h2*h2 < t2) n++;
    }
    return n;
}

/* Scalar SoA -- splits gv[] into gvx/gvy/gvz */
int score_sov_f64(const double ubi[3][3], const double gv[], double tol, intptr_t ng) {
    const double *restrict gvx = gv, *restrict gvy = gv + ng, *restrict gvz = gv + ng * 2;
    int n = 0;
    double t2 = tol * tol;
    intptr_t k;
    for (k = 0; k < ng; k++) {
        double h0 = ubi[0][0]*gvx[k] + ubi[0][1]*gvy[k] + ubi[0][2]*gvz[k]; h0 -= nearbyint(h0);
        double h1 = ubi[1][0]*gvx[k] + ubi[1][1]*gvy[k] + ubi[1][2]*gvz[k]; h1 -= nearbyint(h1);
        double h2 = ubi[2][0]*gvx[k] + ubi[2][1]*gvy[k] + ubi[2][2]*gvz[k]; h2 -= nearbyint(h2);
        if (h0*h0 + h1*h1 + h2*h2 < t2) n++;
    }
    return n;
}

int score_sov_f32(const double ubi[3][3], const float gv[], double tol, intptr_t ng) {
    const float *restrict gvx = gv, *restrict gvy = gv + ng, *restrict gvz = gv + ng * 2;
    int n = 0;
    double t2 = tol * tol;
    intptr_t k;
    for (k = 0; k < ng; k++) {
        double gx = gvx[k], gy = gvy[k], gz = gvz[k];
        double h0 = ubi[0][0]*gx + ubi[0][1]*gy + ubi[0][2]*gz; h0 -= nearbyint(h0);
        double h1 = ubi[1][0]*gx + ubi[1][1]*gy + ubi[1][2]*gz; h1 -= nearbyint(h1);
        double h2 = ubi[2][0]*gx + ubi[2][1]*gy + ubi[2][2]*gz; h2 -= nearbyint(h2);
        if (h0*h0 + h1*h1 + h2*h2 < t2) n++;
    }
    return n;
}
