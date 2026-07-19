#include "cImageD11.h"
#include "blobs.h"

/* C2PY_BEGIN
 * {"py_sig": "bgcalc(img: buffer, bg: buffer, msk: buffer, gain: float, sp: float, st: float) -> void",
 *  "doc": "computes a background on a 1d signal where gain\nand sp and st are defined by:\n    diff = difference to neighbors or bg estimate\n    sigmap = weight for abs background value\n    sigmat = constant weight\n    gain for b += diff * gain\nimg - source data\nbg  - computed background\nmsk - mask",
 *  "checks": ["img.format == 'f'", "img.ndim == 2", "bg.format == 'f'", "bg.n == img.n",
 *      "msk.format == 'B' or msk.format == 'b'", "msk.n == img.n"],
 *  "c_overloads": [{"sig": "void bgcalc(const float *img, float *bg, uint8_t *msk, intptr_t ns, intptr_t nf, float gain, float sigmap, float sigmat)",
 *      "map": {"img": "img.ptr", "bg": "bg.ptr", "msk": "msk.ptr", "ns": "img.shape[0]", "nf": "img.shape[1]", "gain": "gain", "sigmap": "sp", "sigmat": "st"}}]}
C2PY_END */

void bgcalc(const float *restrict img, float *restrict bg,
            uint8_t *restrict msk, intptr_t ns, intptr_t nf, float gain, float sigmap,
            float sigmat) {
    intptr_t ir; int i;
    float b, diff, t;
    /*
    printf("gain %f sigmap %f sigmat %f ns %d nf %d\n",
    gain, sigmap, sigmat, ns, nf); */
#pragma omp parallel for private(b, diff, t, ir, i)
    for (ir = 0; ir < ns; ir++) { // in range( 1, len(data) ):
        i = ir * nf;
        b = img[i];
        bg[i] = b;
        msk[i] = 1;
        for (i = ir * nf; i < (ir + 1) * nf; i++) {
            diff = img[i] - b;
            t = sigmap * fabsf(b) + sigmat;
            if (diff > t) {
                diff = t * diff / fabsf(diff) / 16;
                msk[i] = 1;
            } else if (diff < -t) {
                diff = t * diff / fabsf(diff) / 4;
                msk[i] = 1;
            } else {
                msk[i] = 0;
            }
            b += diff * gain;
            bg[i] = b;
        }
        i = (ir + 1) * nf - 1;
        b = img[i];
        bg[i] = b;
        msk[i] = 1;
        for (i = (ir + 1) * nf - 1; i >= ir * nf; i--) {
            diff = img[i] - b;
            t = sigmap * fabsf(b) + sigmat;
            if (diff > t) {
                diff = t * diff / fabsf(diff) / 16;
                msk[i] += 1;
            } else if (diff < -t) {
                diff = t * diff / fabsf(diff) / 4;
                msk[i] += 1;
            } else {
                if (msk[i] == 1) {
                    bg[i] = b;
                }
                if ((msk[i] == 0) || (msk[i] == 2)) {
                    bg[i] = (bg[i] + b) / 2;
                }
            }
            b += diff * gain;
        }
    }
}
