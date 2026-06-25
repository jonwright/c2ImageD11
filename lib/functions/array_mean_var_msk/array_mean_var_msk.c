#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "array_mean_var_msk(img: buffer, msk: buffer, n: int = 3, cut: float = 3.0, verbose: int = 0) -> void",
 *  "doc": "Sigma-clipped mean/var with mask.",
 *  "checks": ["img.format == 'f'", "msk.format == 'B' or msk.format == 'b'", "msk.n == img.n"],
 *  "c_overloads": [{"sig": "void array_mean_var_msk(const float *img, uint8_t *msk, intptr_t npx, float *mean, float *std, int n, float cut, int verbose)",
 *      "map": {"img": "img.ptr", "msk": "msk.ptr", "npx": "img.n", "n": "n", "cut": "cut", "verbose": "verbose"},
 *      "outputs": {"mean": "float", "std": "float"}}]}
C2PY_END */

void array_mean_var_msk(const float *restrict img, uint8_t *restrict msk, intptr_t npx,
                        float *mean, float *std, int n, float cut,
                        int verbose) {
    intptr_t i; int nactive;
    float t, s1, s2, wt, y0;
    y0 = img[0];
    s1 = 0;
    s2 = 0;
    if (verbose)
        printf("Args, img[0] %f npx %td n %td cut %f verbose %d\n", img[0], npx,
               n, cut, verbose);
#ifdef GOT_OMP_SIMD
#pragma omp parallel for simd private(t) reduction(+ : s1, s2)
#else
#pragma omp parallel for private(t) reduction(+ : s1, s2)
#endif
    for (i = 0; i < npx; i++) {
        t = img[i] - y0;
        s1 = s1 + t;
        s2 = s2 + t * t;
    }
    /* mean and std */
    *mean = (float)(s1 / npx + y0);
    *std = sqrtf((float)((s2 - (s1 * s1 / npx)) / npx));
    if (verbose > 0)
        printf("n=%d Mean %f, Std %f\n", n, *mean, *std);
    while (--n > 1) {
        y0 = *mean;
        wt = y0 + cut * (*std);
        s1 = 0;
        s2 = 0;
        nactive = 0;
#ifdef GOT_OMP_SIMD
#pragma omp parallel for simd private(t) reduction(+ : s1, s2, nactive)
#else
#pragma omp parallel for private(t) reduction(+ : s1, s2, nactive)
#endif
        for (i = 0; i < npx; i++) {
            if (img[i] < wt) {
                t = img[i] - y0;
                s1 = s1 + t;
                s2 = s2 + t * t;
                nactive++;
            }
        }
        *mean = (float)(s1 / nactive + *mean);
        *std = sqrtf(((s2 - (s1 * s1 / nactive)) / nactive));
        if (verbose > 0)
            printf("n=%d Mean %f, Std %f\n", n, *mean, *std);
    }

    /* Fill in mask */
    y0 = *mean;
    wt = y0 + cut * (*std);
    if (verbose > 0)
        printf("Cutting img > %f\n", wt);
#ifdef GOT_OMP_SIMD
#pragma omp parallel for simd
#else
#pragma omp parallel for
#endif
    for (i = 0; i < npx; i++) {
        if (img[i] < wt) {
            msk[i] = 0;
        } else {
            msk[i] = 1;
        }
    }
}
