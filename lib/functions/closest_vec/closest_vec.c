#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "closest_vec(x: buffer, ic: buffer) -> void",
 *     "doc": "finds the closest neighbors for each row of X\nignoring the self. Treated as a X=[v1,v2,v3,...], computes\nsum{(vi-vj)**2} for all i!=j and places minimum in ic.",
 *     "params": {
 *         "x": "2D array of feature vectors, shape (nv, dim). Each row is a vector.",
 *         "ic": "Output array of shape (nv,). For each row i, ic[i] = index j of the nearest neighbor (j != i).",
 *     },
 *     "checks": [
 *         "x.format == 'd'",
 *         "x.ndim == 2",
 *         "x.shape[1] >= 1",
 *         "( ic.format == 'i' or ic.format == 'l' )",
 *         "ic.n == x.shape[0]",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void closest_vec(const double *x, intptr_t dim, intptr_t nv, int *ic)",
 *         "map": {"x": "x.ptr", "dim": "x.shape[1]", "nv": "x.shape[0]", "ic": "ic.ptr"},
 *     }],
 * }
C2PY_END */

void closest_vec(double x[], intptr_t dim, intptr_t nv, int closest[]) {
    /*
     * For each x it finds the closest neighbor
     *   this will grow as n^2, which means it rapidly becomes slow
     */
    intptr_t i, j, k; int ib;
    double scor, best, t;

#pragma omp parallel for private(i, j, k, ib, scor, best, t)
    for (i = 0; i < nv; i++) { /* source vector */
        /* init with something */
        j = (i + 1) % nv;
        best = 0.;
        for (k = 0; k < dim; k++) {
            t = x[i * dim + k] - x[j * dim + k];
            best += t * t;
        }
        ib = j;
        /* now check all the others */
        for (j = 0; j < nv; j++) {
            if (i == j)
                continue;
            scor = 0.;
            for (k = 0; k < dim; k++) {
                t = x[i * dim + k] - x[j * dim + k];
                scor += t * t;
            }
            if (scor < best) {
                ib = j;
                best = scor;
            }
        }
        closest[i] = ib;
    }
}
