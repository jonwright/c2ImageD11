#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "clean_mask(msk: buffer, ret: buffer) -> int",
 *  "doc": "removes pixels which are not 4 connected from msk\nwhile copying into ret.",
 *  "params": {"msk": "Input int8 2D mask.", "ret": "Output cleaned int8 mask."},
 *  "checks": ["msk.format == 'b' or msk.format == 'B'", "msk.ndim == 2",
 *      "ret.format == 'b' or ret.format == 'B'", "ret.n == msk.n"],
 *  "c_overloads": [{"sig": "int clean_mask(const int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"msk": "msk.ptr", "ret": "ret.ptr", "ns": "msk.shape[0]", "nf": "msk.shape[1]"}}]}
C2PY_END */

int clean_mask(const int8_t *restrict msk, int8_t *restrict ret, intptr_t ns,
               intptr_t nf) {
    /* cleans pixels with no 4 connected neighbors */
    intptr_t i, j, q, npx;
    int8_t t;
    npx = 0;
#pragma omp parallel for private(i)
    for (i = 0; i < ns * nf; i++) {
        if (msk[i] > 0) {
            ret[i] = 1;
        } else {
            ret[i] = 0;
        }
    }
    i = 0;
    for (j = 0; j < nf; j++) {
        q = i * nf + j;
        if (ret[q] > 0) {
            t = msk[q + nf];
            if (j > 0)
                t += msk[q - 1];
            if (j < (nf - 1))
                t += msk[q + 1];
            if (t > 0) {
                npx++;
            } else {
                ret[q] = 0;
            }
        }
    }
#pragma omp parallel for private(i, j, q, t) reduction(+ : npx)
    for (i = 1; i < (ns - 1); i++) {
        /* j==0 */
        q = i * nf;
        if (ret[q] > 0) {
            t = msk[q - nf] + msk[q + nf] + msk[q + 1];
            if (t > 0) {
                npx++;
            } else {
                ret[q] = 0;
            }
        }
        for (j = 1; j < (nf - 1); j++) {
            q = i * nf + j;
            if (ret[q] > 0) {
                t = msk[q - nf] + msk[q + nf] + msk[q - 1] + msk[q + 1];
                if (t > 0) {
                    npx++;
                } else {
                    ret[q] = 0;
                }
            }
        }
        q = (i + 1) * nf - 1;
        if (ret[q] > 0) {
            t = msk[q - nf] + msk[q + nf] + msk[q - 1];
            if (t > 0) {
                npx++;
            } else {
                ret[q] = 0;
            }
        }
    }
    i = ns - 1;
    for (j = 0; j < nf; j++) {
        q = i * nf + j;
        if (ret[q] > 0) {
            t = msk[q - nf];
            if (j > 0)
                t += msk[q - 1];
            if (j < (nf - 1))
                t += msk[q + 1];
            if (t > 0) {
                npx++;
            } else {
                ret[q] = 0;
            }
        }
    }
    return npx;
}
