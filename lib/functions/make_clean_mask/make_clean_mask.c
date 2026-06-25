#include "cImageD11.h"
#include "blobs.h"

/* clean_mask is defined in clean_mask/clean_mask.c */
int clean_mask(const int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf);

/* C2PY_BEGIN
 * {"py_sig": "make_clean_mask(img: buffer, cut: float, msk: buffer, ret: buffer) -> int",
 *  "doc": "Generate mask from threshold then clean isolated pixels.",
 *  "params": {"img": "Input float32 2D.", "cut": "Threshold.", "msk": "Priority mask (int8).", "ret": "Output cleaned mask."},
 *  "checks": ["img.format == 'f'", "img.ndim == 2", "msk.format == 'b' or msk.format == 'B'", "msk.n == img.n",
 *      "ret.format == 'b' or ret.format == 'B'", "ret.n == img.n"],
 *  "c_overloads": [{"sig": "int make_clean_mask(const float *img, float cut, int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"img": "img.ptr", "cut": "cut", "msk": "msk.ptr", "ret": "ret.ptr", "ns": "img.shape[0]", "nf": "img.shape[1]"}}]}
C2PY_END */

int make_clean_mask(const float *restrict img, float cut, int8_t *restrict msk,
                    int8_t *restrict ret, intptr_t ns, intptr_t nf) {
    /* cleans pixels with no 4 connected neighbors */
    intptr_t i;
#pragma omp parallel for
    for (i = 0; i < ns * nf; i++) {
        if (img[i] > cut) {
            msk[i] = 1;
        } else {
            msk[i] = 0;
        }
    }
    return clean_mask(&msk[0], &ret[0], ns, nf);
}
