#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "frelon_lines_sub(img: buffer, drk: buffer, cut: float) -> void",
 *  "doc": "Dark subtract then per-row baseline removal.",
 *  "checks": ["img.format == 'f'", "img.ndim == 2", "drk.format == 'f'", "drk.n == img.n"],
 *  "c_overloads": [{"sig": "void frelon_lines_sub(float *img, const float *drk, intptr_t ns, intptr_t nf, float cut)",
 *      "map": {"img": "img.ptr", "drk": "drk.ptr", "ns": "img.shape[0]", "nf": "img.shape[1]", "cut": "cut"}}]}
C2PY_END */

void frelon_lines_sub(float *restrict img, const float *restrict drk, intptr_t ns, intptr_t nf,
                      float cut) {
    intptr_t i, j, p, npx;
    float rowsum, avg;
    avg = img[0];
#pragma omp parallel for private(i, j, rowsum, npx, p) firstprivate(avg)
    for (i = 0; i < ns; i++) {
        rowsum = 0.;
        npx = 0;
        p = i * nf;
#ifdef GOT_OMP_SIMD
#pragma omp simd
#endif
        for (j = 0; j < nf; j++) {
            img[p + j] = img[p + j] - drk[p + j];
            if (img[p + j] < cut) {
                rowsum += img[p + j];
                npx++;
            }
        }
        if (npx > 0)
            avg = rowsum / npx;
#ifdef GOT_OMP_SIMD
#pragma omp simd
#endif
        for (j = 0; j < nf; j++)
            img[p + j] = img[p + j] - avg;
    }
}
