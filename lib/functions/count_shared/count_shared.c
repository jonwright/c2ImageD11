#include "cImageD11.h"
#include "ImageD11_cmath.h"

/* C2PY_BEGIN
 * {
 *     "py_sig": "count_shared(pi: buffer, pj: buffer) -> int",
 *     "doc": "takes two sorted arrays in pi and pj and counts\nhow many collisions there are. Useful to compare two lists of\npeak to grain assignments, or pixel to peak assignments, etc",
 *     "params": {
 *         "pi": "First sorted array of integer labels.",
 *         "pj": "Second sorted array of integer labels.",
 *     },
 *     "checks": [
 *         "( pi.format == 'i' or pi.format == 'l' )",
 *         "( pj.format == 'i' or pj.format == 'l' )",
 *     ],
 *     "c_overloads": [{
 *         "sig": "int count_shared(const int *pi, intptr_t ni, const int *pj, intptr_t nj) -> int",
 *         "map": {"pi": "pi.ptr", "ni": "pi.n", "pj": "pj.ptr", "nj": "pj.n"},
 *     }],
 * }
C2PY_END */

int count_shared(const int pi[], intptr_t ni, const int pj[], intptr_t nj) {
    /* Given two sorted arrays compute how many collisions
     * For comparing list of grain - peak indices for overlap
     */
    intptr_t i, j; int c;
    i = 0;
    j = 0;
    c = 0;
    while ((i < ni) && (j < nj)) {
        if (pi[i] > pj[j]) {
            j++;
        } else if (pi[i] < pj[j]) {
            i++;
        } else {
            i++;
            j++;
            c++;
        }
    }
    return c;
}
