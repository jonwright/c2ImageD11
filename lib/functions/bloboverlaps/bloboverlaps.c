#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "bloboverlaps(labels1: buffer, npk1: int, results1: buffer, labels2: buffer, npk2: int, results2: buffer, verbose: int = 0) -> int",
 *  "doc": "Determine overlaps between two frames label images.",
 *  "params": {"labels1": "First frame labels (int32 2D).", "npk1": "Objects in first frame.",
 *      "results1": "First frame properties.", "labels2": "Second frame labels.", "npk2": "Objects in second frame.",
 *      "results2": "Second frame properties.", "verbose": "Print diagnostics."},
 *  "checks": ["( labels1.format == 'i' or labels1.format == 'l' )", "labels1.ndim == 2", "( labels2.format == 'i' or labels2.format == 'l' )", "labels2.n == labels1.n",
 *      "results1.format == 'd'", "results1.shape[0] == npk1", "results1.shape[1] == 36",
 *      "results2.format == 'd'", "results2.shape[0] == npk2", "results2.shape[1] == 36"],
 *  "c_overloads": [{"sig": "int bloboverlaps(int32_t *b1, int32_t n1, double *res1, int32_t *b2, int32_t n2, double *res2, int verbose, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"b1": "labels1.ptr", "n1": "npk1", "res1": "results1.ptr", "b2": "labels2.ptr", "n2": "npk2", "res2": "results2.ptr", "verbose": "verbose", "ns": "labels1.shape[0]", "nf": "labels1.shape[1]"}}]}
C2PY_END */

int bloboverlaps(int32_t *b1, int32_t n1, double *res1, int32_t *b2, int32_t n2,
                 double *res2, int verbose, intptr_t ns, intptr_t nf) {

    intptr_t i, j, ipx; int safelyneed;
    int32_t *link, p1, p2, ipk, jpk, npk, *T;

    /* Initialise a disjoint set in link
     * image 2 has peak[i]=i ; i=1->n2
     * image 1 has peak[i]=i+n1+1 ; i=1->n1
     *                          0, 1, 2, 3, n2
     *                          4, 5, 6, 7, 8, 9, n1   need 0, 4 == n1+n2+3
     * link to hold 0->n1-1 ; n1->n2+n2-1
     * */

    /* This is a disjoint merge operation ... */
    if (verbose)
        printf("Enter bloboverlaps\n");
    safelyneed = n1 + n2 + 3;
    link = (int *)malloc(safelyneed * sizeof(int32_t));
    link[0] = safelyneed;
    for (i = 1; i < safelyneed; i++) {
        link[i] = i;
    }
    /* flag the start of image number 2 */
    link[n2 + 1] = -99999; /* ==n2=0 Should never be touched by anyone */
    /* results lists of pairs of number */
    /* link holds a disjoint set, we label directly overlapping pixels (i==j) */
    for (i = 0; i < ns; i++) {
        for (j = 0; j < nf; j++) {
            ipx = i * nf + j;
            if ((p1 = b1[ipx]) == 0)
                continue;
            if ((p2 = b2[ipx]) == 0)
                continue;
            if (link[p2] < 0 || link[p1 + n2 + 1] < 0) {
                printf("Whoops!!\n");
                return 0;
            }
            dset_makeunion(link, p2, p1 + n2 + 1);
            if (verbose > 10)
                printf("link %d %d\n", p2, p1 + n2 + 1);
        }
    }
    if (verbose)
        printf("Scanning images\n");
    /* Now we re-label and merge peaks scanning disjoint set */
    for (i = 1; i < safelyneed; i++) {
        if (link[i] != i && i != n2 + 1) {
            j = dset_find(i, link);
            if ((i > n2 + 1) && (j < n2 + 1)) { /* linking between images */
                jpk = j - 1;
                ipk = i - n2 - 2;
                /* Bounds checking */
                boundscheck(jpk, n2, ipk, n1);
                merge(&res2[NPROPERTY * jpk], &res1[NPROPERTY * ipk]);
                if (verbose > 10)
                    printf("merged res2[%d] res1[%d]\n", jpk, ipk);
                continue;
            }
            if ((i > n2 + 1) &&
                (j > n2 + 1)) { /* linking on the same image (1) */
                jpk = j - n2 - 2;
                ipk = i - n2 - 2;
                boundscheck(jpk, n1, ipk, n1);
                assert((n1 > jpk) && (jpk >= 0) && (n1 > ipk) && (ipk >= 0));
                merge(&res1[NPROPERTY * jpk], &res1[NPROPERTY * ipk]);
                if (verbose > 10)
                    printf("merge res1[%d] res1[%d]\n", jpk, ipk);
                continue;
            }
            if (i < n2 + 1 && j < n2 + 1) { /* linking on the same image (2) */
                jpk = j - 1;
                ipk = i - 1;
                boundscheck(jpk, n2, ipk, n2);
                merge(&res2[NPROPERTY * jpk], &res2[NPROPERTY * ipk]);
                if (verbose > 10)
                    printf("merge res2[%d] res2[%d]\n", jpk, ipk);
                continue;
            }
            assert(0 && "unreachable: bloboverlaps linking logic");
        }
    }

    /* This is the case where two spots on the current image become linked by
     * by a spot overlap on the previous one
     *
     * The labels are now wrong, in fact there is a single peak in 3D and
     * two peaks in 2D
     *
     * Thanks to Stine West from Riso for finding this subtle bug
     */

    /* First, work out the new labels */
    /* Make each T[i] contain the unique ascending integer for the set */
    if (verbose)
        printf("Compress set\n");
    T = (int32_t *)(calloc((n2 + 3), sizeof(int32_t)));
    assert(T != NULL);

    npk = 0;
    for (i = 1; i < n2 + 1; i++) {
        if (link[i] == i) {
            npk = npk + 1;
            T[i] = npk;
        } else {
            j = dset_find(i, link);
            assert(j < i);
            T[i] = T[j];
        }
    }
    if (verbose) {
        printf("n1 = %td n2 = %td ", n1, n2);
        for (i = 0; i < n2 + 3; i++)
            printf("T[%td]=%td ", i, T[i]);
    }
    /* T is now compressed, merge the peaks */
    if (verbose)
        printf("Merge peaks in res2\n");
    for (i = 1; i < n2 + 1; i++) {
        /* dest  = T[i]; */
        /* src   = link[i]; */
        if (link[i] == T[i])
            continue;
        if (T[i] < link[i]) {   /* copy and zero out */
            if (link[i] == i) { /* This is the place accumulating */
                for (j = 0; j < NPROPERTY; j++) {
                    res2[NPROPERTY * (T[i] - 1) + j] =
                        res2[NPROPERTY * (link[i] - 1) + j];
                    res2[NPROPERTY * (link[i] - 1) + j] = 0;
                }
            } else {
                /* assert this is empty */
                assert(res2[NPROPERTY * (i - 1) + s_1] < 0.01);
            }
            if (verbose > 1) {
                printf("np i %d j %d %f \n", T[i], link[i],
                       res2[NPROPERTY * T[i] + 1]);
            }
        } else {
            assert("Bad logic in bloboverlaps");
        }
    }
    if (verbose)
        printf("Relabel image of blobs\n");
    /* Relabel the image where they change */
    for (i = 0; i < ns; i++) {
        for (j = 0; j < nf; j++) {
            ipx = i * nf + j;
            if ((p2 = b2[ipx]) == 0)
                continue;
            ipk = T[p2];
            if (ipk != p2) {
                assert(ipk > 0 && ipk <= n2);
                b2[ipx] = ipk;
            }
        }
    }
    if (verbose)
        printf("Done relabelling\n");
    free(T);
    free(link);
    return npk;
}
