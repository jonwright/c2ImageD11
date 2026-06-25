#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "refine_assigned(ubi: buffer, gv: buffer, labels: buffer, label: int) -> void",
 *     "doc": "refine_assigned fits a ubi matrix to a set of g-vectors and assignments in labels.",
 *     "params": {
 *         "ubi": "Orientation matrix (9-element flattened double).",
 *         "gv": "G-vectors array, shape (ng, 3) flattened.",
 *         "labels": "Peak-to-grain assignments (ng ints).",
 *         "label": "Grain label to refine.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gv.format == 'd'",
 *         "( labels.format == 'i' or labels.format == 'l' )",
 *         "labels.n == gv.shape[0]",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void refine_assigned(double ubi[3][3], const double gv[][3], const int *labels, int label, int *npk, double *drlv2, intptr_t ng)",
 *         "outputs": {"npk": "int", "drlv2": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "labels": "labels.ptr", "label": "label", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */

void refine_assigned(vec ubi[3], const vec gv[], const int labels[], int label, int *npk,
                     double *sumdrlv2, intptr_t ng) {
    /* Skip the part about weights, not used */
    double sumsqtot, sumsq, h[3], t[3], ih[3];
    double R[3][3], H[3][3], UB[3][3];
    int i, j, n; intptr_t k; int l;
    n = 0;
    sumsqtot = 0;
    for ( i = 0; i < 3; i++ ){
        for ( j = 0; j < 3; j++ ){
            R[i][j] = 0.;
            H[i][j] = 0.;
            UB[i][j] = 0.;
        }
    }
    for (k = 0; k < ng; k++) {
        if (label != labels[k]) {
            continue;
        }
        n++;
        for (j = 0; j < 3; j++) {
            h[j] = ubi[j][0] * gv[k][0] + ubi[j][1] * gv[k][1] +
                   ubi[j][2] * gv[k][2];
            ih[j] = conv_double_to_int_fast(h[j]);
            t[j] = h[j] - ih[j];
        }
        sumsq = t[0] * t[0] + t[1] * t[1] + t[2] * t[2];
        sumsqtot += sumsq;
        for (i = 0; i < 3; i++) {
            for (j = 0; j < 3; j++) {
                R[i][j] = R[i][j] + ih[j] * gv[k][i];
                H[i][j] = H[i][j] + ih[j] * ih[i];
            }
        }
    }
    /* outputs */
    *npk = n;
    if (n > 0) {
        *sumdrlv2 = sumsqtot / n;
    } else {
        *sumdrlv2 = 0.;
    }
    /* And the fitted matrix */
    k = inverse3x3(H);
    if (k == 0) {
        /* Form best fit UB */
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                for (l = 0; l < 3; l++)
                    UB[i][j] = UB[i][j] + R[i][l] * H[l][j];
    }

    if (k == 0 && inverse3x3(UB) == 0) {
        /* Copy to output */
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                ubi[i][j] = UB[i][j];
    }
}
