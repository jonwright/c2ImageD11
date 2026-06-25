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
 *         "gv.format == 'd'",
 *         "drlv2.format == 'd'",
 *         "drlv2.n == gv.shape[0]",
 *         "( labels.format == 'i' or labels.format == 'l' )",
 *         "labels.n == gv.shape[0]",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd'",
 *         "sig": "int score_and_assign(const double ubi[3][3], const double gv[][3], double tol, double *drlv2, int *labels, int label, intptr_t ng) -> int",
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "drlv2": "drlv2.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */

int score_and_assign(const vec *restrict ubi, const vec *restrict gv, double tol,
                     double *restrict drlv2, int *restrict labels, int label,
                     intptr_t ng) {

    double h0, h1, h2, t0, t1, t2, sumsq, tolsq;
    intptr_t k; int n;
    tolsq = tol * tol;
    n = 0;
#pragma omp parallel for private(h0, h1, h2, t0, t1, t2, sumsq)                \
    reduction(+ : n) schedule(static, 4096)
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k][0] + ubi[0][1] * gv[k][1] + ubi[0][2] * gv[k][2];
        h1 = ubi[1][0] * gv[k][0] + ubi[1][1] * gv[k][1] + ubi[1][2] * gv[k][2];
        h2 = ubi[2][0] * gv[k][0] + ubi[2][1] * gv[k][1] + ubi[2][2] * gv[k][2];
        t0 = h0 - conv_double_to_int_fast(h0);
        t1 = h1 - conv_double_to_int_fast(h1);
        t2 = h2 - conv_double_to_int_fast(h2);
        sumsq = t0 * t0 + t1 * t1 + t2 * t2;
        /* If this peak fits better than the one in drlv2 then we
         * assign it:
         */
        if ((sumsq < tolsq) && (sumsq < drlv2[k])) {
            labels[k] = label;
            drlv2[k] = sumsq;
            n++;
        } else if (labels[k] == label) {
            /* We thought it belonged but it does not */
            labels[k] = -1;
        }
    }
    return n;
}
