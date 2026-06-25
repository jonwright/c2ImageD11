#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "uint16_to_float_darksub(img: buffer, drk: buffer, data: buffer) -> void",
 *  "doc": "Subtract dark current from uint16 data, result in float32 img.",
 *  "checks": ["img.format == 'f'", "drk.format == 'f'", "drk.n == img.n",
 *      "data.format == 'H' or data.itemsize == 2", "data.n == img.n"],
 *  "gil_release": true,
 *  "c_overloads": [{"when": "img.format == 'f' and drk.format == 'f'",
 *      "sig": "void uint16_to_float_darksub(float *img, const float *drk, const uint16_t *data, intptr_t npx)",
 *      "map": {"img": "img.ptr", "drk": "drk.ptr", "data": "data.ptr", "npx": "img.n"}}]}
C2PY_END */

void uint16_to_float_darksub(float *restrict img, const float *restrict drk,
                             const uint16_t *restrict data, intptr_t npx) {
    intptr_t i;
#ifdef GOT_OMP_SIMD
#pragma omp parallel for simd
#else
#pragma omp parallel for
#endif
    for (i = 0; i < npx; i++) {
        img[i] = ((float)data[i]) - drk[i];
    }
}
