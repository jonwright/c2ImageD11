#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "compress_duplicates(i: buffer, j: buffer, oi: buffer, oj: buffer, tmp: buffer) -> int",
 *  "doc": "Remove duplicate (i,j) pairs via counting sort.",
 *  "params": {"i": "I/O int32 col 0.", "j": "I/O int32 col 1.", "oi": "Output counts.", "oj": "Temp.", "tmp": "Temp."},
 *  "checks": ["( i.format == 'i' or i.format == 'l' )", "( j.format == 'i' or j.format == 'l' )", "j.n == i.n",
 *      "( oi.format == 'i' or oi.format == 'l' )", "oi.n == i.n", "( oj.format == 'i' or oj.format == 'l' )", "oj.n == i.n", "( tmp.format == 'i' or tmp.format == 'l' )"],
 *  "c_overloads": [{"sig": "int compress_duplicates(int *i, int *j, int *oi, int *oj, int *tmp, intptr_t n, intptr_t nt) -> int",
 *      "map": {"i": "i.ptr", "j": "j.ptr", "oi": "oi.ptr", "oj": "oj.ptr", "tmp": "tmp.ptr", "n": "i.n", "nt": "tmp.n"}}]}
C2PY_END */

int compress_duplicates(int *restrict i, int *restrict j, int *restrict oi,
                        int *restrict oj, int *restrict tmp, intptr_t n, intptr_t nt) {
    intptr_t k; int vmax, c, t, ik, jk;
    /* First sort on j */
    vmax = i[0];
    for (k = 0; k < n; k++) { /* length of histogram */
        if (i[k] > vmax)
            vmax = i[k];
        if (j[k] > vmax)
            vmax = j[k];
    }
    assert(vmax < nt);
    for (k = 0; k <= vmax; k++) { /* Zero the histogram */
        tmp[k] = 0;
    }
    for (k = 0; k < n; k++) { /* Make the histogram */
        tmp[j[k]] = tmp[j[k]] + 1;
    }
    c = 0;
    for (k = 0; k <= vmax; k++) { /* Cumsum */
        t = tmp[k];
        tmp[k] = c;
        c = c + t;
    }
    for (k = 0; k < n; k++) { /* Now the order is: */
        oi[tmp[j[k]]] = i[k];
        oj[tmp[j[k]]] = j[k];
        tmp[j[k]]++;
    }
    /* Now sort on i */
    for (k = 0; k <= vmax; k++) { /* Zero the histogram */
        tmp[k] = 0;
    }
    for (k = 0; k < n; k++) { /* Make the histogram */
        tmp[i[k]]++;
    }
    c = 0;
    for (k = 0; k <= vmax; k++) { /* Cumsum */
        t = tmp[k];
        tmp[k] = c;
        c = c + t;
    }
    for (k = 0; k < n; k++) { /* Now the order is: */
        /* t = order to read the original array to get sorted on j */
        j[tmp[oi[k]]] = oj[k];
        i[tmp[oi[k]]] = oi[k];
        tmp[oi[k]]++;
    }
    /* init */
    ik = i[0];
    jk = j[0];
    t = 1; /* nhits */
    c = 0; /* write pos */
    for (k = 1; k < n; k++) {
        if ((ik == i[k]) && (jk == j[k])) {
            t++; /* add one */
        } else {
            /* write prev */
            i[c] = ik;
            j[c] = jk;
            oi[c] = t;
            /* init next */
            c++;
            t = 1;
            ik = i[k];
            jk = j[k];
        }
    }
    /* write last */
    i[c] = ik;
    j[c] = jk;
    oi[c] = t;
    c++;
    return c;
}
