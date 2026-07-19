#include "cImageD11.h"
#include "blobs.h"
extern int sparse_is_sorted(const uint16_t i[], const uint16_t j[], intptr_t nnz);
static int NOISY = 0;
#define CHECKSANITY 0
#define TRACE 0

/* C2PY_BEGIN
 * {"py_sig": "sparse_localmaxlabel(v: buffer, i: buffer, j: buffer, MV: buffer, iMV: buffer, labels: buffer) -> int",
 *  "doc": "assigns labels to sparse array in sorted coo format\nsupplied in (v,(i,j)). MV and iMV are temporaries.\nsingle threaded",
 *  "params": {"v": "Values (float32).", "i": "Rows (uint16).", "j": "Cols (uint16).",
 *      "MV": "Temp float32.", "iMV": "Temp int32.", "labels": "Output labels (int32)."},
 *  "checks": ["v.format == 'f'", "i.format == 'H' or i.itemsize == 2", "j.format == 'H' or j.itemsize == 2",
 *      "j.n == i.n", "v.n == i.n", "MV.format == 'f'", "MV.n == i.n",
 *      "( iMV.format == 'i' or iMV.format == 'l' )", "iMV.n == i.n", "( labels.format == 'i' or labels.format == 'l' )", "labels.n == i.n"],
 *  "c_overloads": [{"sig": "int sparse_localmaxlabel(const float *v, const uint16_t *i, const uint16_t *j, intptr_t nnz, float *MV, int32_t *iMV, int32_t *labels) -> int",
 *      "map": {"v": "v.ptr", "i": "i.ptr", "j": "j.ptr", "nnz": "i.n", "MV": "MV.ptr", "iMV": "iMV.ptr", "labels": "labels.ptr"}}]}
C2PY_END */

int sparse_localmaxlabel(float *restrict v, uint16_t *restrict i,
                         uint16_t *restrict j, intptr_t nnz,
                         float *restrict MV, // neighbor Max Val (of 3x3 square)
                         int32_t *restrict iMV,   // Which neighbor is higher?
                         int32_t *restrict labels // Which neighbor is higher?
) {
    intptr_t k, p, pp; int ir, pnext;
    float MV_LOW;
    MV_LOW = -1e10;
    /* Read k = kurrent
       p = prev */
    if (NOISY) {
        k = sparse_is_sorted(i, j, nnz);
        if (k != 0) {
            printf("Not sorted! k=%td\n", k);
        }
    }
    /* prev row */
    pp = 0;
    p = 0;
    /* First pixel -  we assume it is a max, it will be stolen later
       has no previous...*/
    iMV[0] = 0;
    MV[0] = v[0];
    /* Main loop */
    for (k = 1; k < nnz; k++) {
        iMV[k] = k;     /* iMV[k] == k tags a max */
        MV[k] = MV_LOW; /* MV[k] is value of that max - a temporary */
        /* previous row first */
        ir = ((int)i[k]) - 1;
        /* pp should be on row above, on or after j-1 */
        while (ir > i[pp]) {
            pp++;
            if (CHECKSANITY) {
                assert((pp >= 0) && (pp < nnz));
            }
        }
        if (TRACE)
            printf("k %td    i[k] %td  j[k] %td  v[k] %f MV[k] %f\n", k, i[k],
                   j[k], v[k], MV[k]);
        /* skip if nothing on row above */
        if (i[pp] < i[k]) {
            /* Locate previous pixel on row above */
            while (((j[pp] + 1) < j[k]) && (i[pp] == ir)) {
                pp++;
                if (CHECKSANITY) {
                    assert((pp >= 0) && (pp < nnz));
                }
            }
            /* Now the 3 pixels on the row above, if they are present */
            for (p = pp; j[p] <= j[k] + 1; p++) {
                if (CHECKSANITY) {
                    assert((p >= 0) && (p < nnz));
                    assert(p < k);
                }
                if (TRACE)
                    printf("p %td   i[p] %td   j[p] %td  v[p] %f MV[k] %f\n", p,
                           i[p], j[p], v[p], MV[k]);
                if (i[p] != ir)
                    break;
                if (v[k] > v[p]) { /* This one is higher */
                    /* Steal if we are higher than neighbor currently points to
                     */
                    if (v[k] > MV[p]) {
                        iMV[p] = k;
                        MV[p] = v[k];
                    }
                } else {
                    if (v[p] > MV[k]) { /* this one is higher than our max,
                                           point to it */
                        iMV[k] = p;
                        MV[k] = v[p];
                    }
                }
            } /* 3 previous */
        } /* row above */
        /* 4 preceding neighbors : k-1 is prev */
        p = k - 1;
        if (CHECKSANITY) {
            assert((p >= 0) && (p < nnz));
        }
        if ((i[k] == i[p]) &&
            (j[k] == (j[p] + 1))) { /* previous pixel, same row */
            if (TRACE)
                printf("p %td   i[p] %td   j[p] %td  v[p] %f\n", p, i[p], j[p],
                       v[p]);
            if (v[k] > v[p]) { /* This one is higher */
                /* Steal if we are higher than neighbor currently points to */
                if (v[k] > MV[p]) {
                    iMV[p] = k;
                    MV[p] = v[k];
                }
            } else {
                if (v[p] > MV[k]) { /* Previous one was higher */
                    iMV[k] = p;
                    MV[k] = v[p];
                }
            }
        }
        /* Finally, check for your own value */
        /* Steal if we are higher than neighbor currently points to */
        if (v[k] > MV[k]) {
            iMV[k] = k;
            MV[k] = v[k];
        }
    } // end loop over data
    /* Count max values and assign unique labels */
    pp = 0;
    for (k = 0; k < nnz; k++) {
        labels[k] = -1;
        if (iMV[k] == k) {
            pp = pp + 1; /* Labels start at one */
            labels[k] = pp;
        }
    }
    /* Now make all labels point to their root */
    for (k = 0; k < nnz; k++) {
        p = iMV[k];
        pnext = 0;
        while (iMV[p] != p) {
            p = iMV[p]; // pointing to uphill
            pnext++;
            if (CHECKSANITY) {
                assert((p >= 0) && (p < nnz));
            }
        }
        labels[k] = labels[p];

        if (pnext > 0) { // Fill in all the pixels in L1
            p = iMV[k];  // Back to the start
            iMV[k] = k;  // labels[k] is set already
            while (iMV[p] != p) {
                labels[p] = labels[k];
                pnext = iMV[p];
                iMV[p] = p;
                p = pnext;
            }
        }
    }
    return pp;
}
