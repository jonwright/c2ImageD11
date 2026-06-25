#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "cluster1d(ar: buffer, order: buffer, tol: float, ids: buffer, avgs: buffer) -> void",
 *     "doc": "cluster1d is used to find clusters of peaks.",
 *     "params": {
 *         "ar": "Array of values to cluster.",
 *         "order": "Permutation that sorts ar ascending.",
 *         "tol": "Distance tolerance for cluster membership.",
 *         "ids": "Output: cluster id for each element.",
 *         "avgs": "Output: average value of each cluster.",
 *     },
 *     "checks": [
 *         "ar.format == 'd'",
 *         "( order.format == 'i' or order.format == 'l' )",
 *         "order.n == ar.n",
 *         "( ids.format == 'i' or ids.format == 'l' )",
 *         "ids.n == ar.n",
 *         "avgs.format == 'd'",
 *         "avgs.n == ar.n",
 *     ],
 *     "c_overloads": [{
 *         "sig": "void cluster1d(const double *ar, intptr_t n, const int *order, double tol, int *nclusters, int *ids, double *avgs)",
 *         "map": {"ar": "ar.ptr", "n": "ar.n", "order": "order.ptr", "tol": "tol", "ids": "ids.ptr", "avgs": "avgs.ptr"},
 *         "outputs": {"nclusters": "int"},
 *     }],
 * }
C2PY_END */

void cluster1d(const double ar[], intptr_t n, const int order[], double tol, // IN
               int *nclusters, int ids[], double avgs[]) {  // OUT
    // Used in sandbox/friedel.py
    intptr_t i; int ncl;
    double dv;
    // order is the order of the peaks to get them sorted
    avgs[0] = ar[order[0]];
    ncl = 1;    // number in this cluster
    ids[0] = 0; // cluster assignments ( in order )
    for (i = 1; i < n; i++) {
        dv = ar[order[i]] - ar[order[i - 1]]; // difference in values
        if (dv > tol) {                       // make a new cluster
            if (ncl > 1) {                    // make avg for the last one
                avgs[ids[i - 1]] = avgs[ids[i - 1]] / ncl;
            }
            ids[i] = ids[i - 1] + 1;     // increment id
            ncl = 1;                     // pks in this cluster
            avgs[ids[i]] = ar[order[i]]; // store value for avg
        } else {
            ids[i] = ids[i - 1]; // copy last id
            ncl = ncl + 1;
            avgs[ids[i]] = avgs[ids[i]] + ar[order[i]]; // sum on for avg
        }
    } // end for(i ...
    // make the last average if necessary
    if (ncl > 1) {
        avgs[ids[i - 1]] /= ncl;
    }
    *nclusters = ids[n - 1] + 1;
}
