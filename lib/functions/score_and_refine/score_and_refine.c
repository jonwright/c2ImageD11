#include "cImageD11.h"
#include "ImageD11_cmath.h"
#include "cimaged11utils.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "score_and_refine(ubi: buffer, gv: buffer, tol: float) -> int",
 *     "doc": "is very similar to score but it also refines the UB\nmatrix using the assigned peaks and overwrite the argument.\nIt returns the number of peaks and fit prior to refinement.",
 *     "params": {
 *         "ubi": "Orientation matrix UBI (9-element flattened double).",
 *         "gv": "G-vectors array, shape (ng, 3) flattened.",
 *         "tol": "Matching tolerance on |h - round(h)|.",
 *     },
 *     "checks": [
 *         "ubi.format == 'd'",
 *         "ubi.n == 9",
 *         "gv.ndim == 2",
 *     ],
 *     "gil_release": true,
 *     "c_overloads": [{
 *         "when": "ubi.format == 'd' and gv.format == 'd' and gv.shape[1] == 3 and gv.slow_axis == 0",
 *         "sig": "void score_and_refine(double ubi[3][3], const double gv[], double tol, int *n_arg, double *sumdrlv2_arg, intptr_t ng)",
 *         "outputs": {"n_arg": "int", "sumdrlv2_arg": "double"},
 *         "map": {"ubi": "ubi.ptr", "gv": "gv.ptr", "tol": "tol", "ng": "gv.shape[0]"},
 *     }],
 * }
C2PY_END */

void score_and_refine(vec ubi[3], const vec gv[], double tol, int *n_arg,
                      double *sumdrlv2_arg, intptr_t ng) {
    /* ng = number of g vectors */
    double h0, h1, h2, t0, t1, t2, ih[3];
    double sumsq, tolsq, sumdrlv2;
    double R[3][3], H[3][3], UB[3][3];
    int n; intptr_t k; int i, j, l;
    /* Zero some stuff for refinement */
    for (i = 0; i < 3; i++) {
        ih[i] = 0;
        for (j = 0; j < 3; j++) {
            R[i][j] = 0.;
            H[i][j] = 0.;
            UB[i][j] = 0.;
        }
    }
    tolsq = tol * tol;
    n = 0;
    sumdrlv2 = 0.;
    /* Test peaks */
    for (k = 0; k < ng; k++) {
        h0 = ubi[0][0] * gv[k][0] + ubi[0][1] * gv[k][1] + ubi[0][2] * gv[k][2];
        h1 = ubi[1][0] * gv[k][0] + ubi[1][1] * gv[k][1] + ubi[1][2] * gv[k][2];
        h2 = ubi[2][0] * gv[k][0] + ubi[2][1] * gv[k][1] + ubi[2][2] * gv[k][2];
        t0 = h0 - conv_double_to_int_fast(h0);
        t1 = h1 - conv_double_to_int_fast(h1);
        t2 = h2 - conv_double_to_int_fast(h2);
        sumsq = t0 * t0 + t1 * t1 + t2 * t2;
        if (sumsq < tolsq) { /* Add into lsq problem */
            n = n + 1;
            sumdrlv2 += sumsq;
            /*   From Paciorek et al Acta A55 543 (1999)
             *   UB = R H-1
             *   where:
             *   R = sum_n r_n h_n^t
             *   H = sum_n h_n h_n^t
             *   r = g-vectors
             *   h = hkl indices
             *   The hkl integer indices are: */
            ih[0] = conv_double_to_int_fast(h0);
            ih[1] = conv_double_to_int_fast(h1);
            ih[2] = conv_double_to_int_fast(h2);
            /* The g-vector is: gv[k][012] */
            for (i = 0; i < 3; i++) {
                for (j = 0; j < 3; j++) {
                    /* Robust weight factor, fn(tol), would go here */
                    R[i][j] = R[i][j] + ih[j] * gv[k][i];
                    H[i][j] = H[i][j] + ih[j] * ih[i];
                }
            } /* End lsq addins */
        } /* End selected peaks */
    } /* End first loop over spots */

    /* Now solve the least squares problem */
    /* inverse overwrites H with the inverse */
    k = inverse3x3(H);
    if (k == 0) {
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                for (l = 0; l < 3; l++)
                    UB[i][j] += R[i][l] * H[l][j];
    }
    /* Now form ubi and copy to argument */
    if ((k == 0) && (inverse3x3(UB) == 0)) {
        for (i = 0; i < 3; i++)
            for (j = 0; j < 3; j++)
                ubi[i][j] = UB[i][j];
    } else {
        /* Determinant was zero - leave ubi as it is */
    }

    if (n > 0) {
        sumdrlv2 /= n;
    }

    /* return values */
    *n_arg = n;
    *sumdrlv2_arg = sumdrlv2;
}
