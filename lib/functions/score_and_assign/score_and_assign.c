#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_assign(ubi: buffer, gv: buffer, tol: float, drlv2: buffer, labels: buffer, label: int) -> int",
 *     "doc": "score_and_assign assigns peaks to this ubi only if they fit the data better.",
 *     "params": {
 *         "ubi": "Orientation matrix (9-element flattened double).",
 *         "gv": "G-vectors array, shape (ng, 3) flattened.",
 *         "tol": "Matching tolerance.",
 *         "drlv2": "Input/output array (ng). Current best squared residuals per peak.",
 *         "labels": "Input/output array (ng). Current grain labels per peak.",
 *         "label": "Grain label assigned to peaks that match this UBI.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gv.ndim == 2",
 *         "( labels.format == 'i' or labels.format == 'l' )",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[1] == 3 and gv.slow_axis == 0",
 *         "sig": "int score_and_assign(double ubi[3][3], const double gv[], double tol, double *drlv2, int *labels, int label, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "drlv2": "drlv2.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[0]"},
 *     }, {
 *         "when": "ubi.format == 'd' and gv.format == 'f' and gv.shape[1] == 3 and gv.slow_axis == 0",
 *         "sig": "int score_and_assign_f32(double ubi[3][3], const float gv[], double tol, float *drlv2, int *labels, int label, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "drlv2": "drlv2.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */

int score_and_assign_f32(double ubi[3][3], const float gv[], double tol,
                         float *restrict drlv2, int *restrict labels, int label,
                         intptr_t ng) {
    double h0, h1, h2, t0, t1, t2, sumsq, tolsq, magic=6755399441055744.0;
    intptr_t k; int n;
    tolsq = tol * tol;
    n = 0;
    for (k = 0; k < ng; k++) {
        double gx=gv[k*3],gy=gv[k*3+1],gz=gv[k*3+2];
        h0 = ubi[0][0]*gx + ubi[0][1]*gy + ubi[0][2]*gz; h0-=((h0+magic)-magic);
        h1 = ubi[1][0]*gx + ubi[1][1]*gy + ubi[1][2]*gz; h1-=((h1+magic)-magic);
        h2 = ubi[2][0]*gx + ubi[2][1]*gy + ubi[2][2]*gz; h2-=((h2+magic)-magic);
        sumsq = h0*h0 + h1*h1 + h2*h2;
        if ((sumsq < tolsq) && (sumsq < (double)drlv2[k])) {
            labels[k] = label;
            drlv2[k] = (float)sumsq;
            n++;
        } else if (labels[k] == label) {
            labels[k] = -1;
        }
    }
    return n;
}

int score_and_assign(double ubi[3][3], const double gv[], double tol,
                     double *restrict drlv2, int *restrict labels, int label,
                     intptr_t ng) {

    double h0, h1, h2, sumsq, tolsq, magic=6755399441055744.0;
    intptr_t k; int n;
    tolsq = tol * tol;
    n = 0;
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k*3] + ubi[0][1] * gv[k*3+1] + ubi[0][2] * gv[k*3+2];
        h0 -= ((h0+magic)-magic);
        h1 = ubi[1][0] * gv[k*3] + ubi[1][1] * gv[k*3+1] + ubi[1][2] * gv[k*3+2];
        h1 -= ((h1+magic)-magic);
        h2 = ubi[2][0] * gv[k*3] + ubi[2][1] * gv[k*3+1] + ubi[2][2] * gv[k*3+2];
        h2 -= ((h2+magic)-magic);
        sumsq = h0*h0 + h1*h1 + h2*h2;
        if ((sumsq < tolsq) && (sumsq < drlv2[k])) {
            labels[k] = label;
            drlv2[k] = sumsq;
            n++;
        } else if (labels[k] == label) {
            labels[k] = -1;
        }
    }
    return n;
}
