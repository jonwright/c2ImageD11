#include "cImageD11.h"
#include "blobs.h"
#include "make_clean_mask.hpp"

int clean_mask(const int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf);

/* C2PY_BEGIN
 * {"py_sig": "make_clean_mask(img: buffer, cut: float, msk: buffer, ret: buffer) -> int",
 *  "doc": "is a lot like clean msk but it generates\nthe msk using img and cut.\nBeware: work in progress",
 *  "params": {"img": "Input float32 2D.", "cut": "Threshold.", "msk": "Priority mask (int8).", "ret": "Output cleaned mask."},
 *  "checks": ["img.ndim == 2",
 *         "img.slow_axis == 0", "msk.format == 'b' or msk.format == 'B'", "msk.n == img.n",
 *      "ret.format == 'b' or ret.format == 'B'", "ret.n == img.n"],
 *  "c_overloads": [{"when": "img.format == 'f' and img.ndim == 2 and img.slow_axis == 0",
 *         "sig": "int make_clean_mask(const float *img, double cut, int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf) -> int"
int make_clean_mask(const float *img, double cut, int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf) -> int",
 *      "map": {"img": "img.ptr", "cut": "cut", "msk": "msk.ptr", "ret": "ret.ptr", "ns": "img.shape[0]", "nf": "img.shape[1]"}}]}
C2PY_END */

extern "C" int make_clean_mask(const float * img, double cut, int8_t * msk,
                    int8_t * ret, intptr_t ns, intptr_t nf) {
    return make_clean_mask_impl<float>(img, cut, msk, ret, ns, nf);
}

/* C2PY_BEGIN
 * {"py_sig": "make_clean_mask(img: buffer, cut: float, msk: buffer, ret: buffer) -> int",
 *  "c_overloads": [{
 *    "when": "img.format == 'B' and img.ndim == 2 and img.slow_axis == 0",
 *    "sig": "int make_clean_mask_u8(const uint8_t *img, double cut, int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf) -> int",
 *    "map": {"img": "img.ptr", "cut": "cut", "msk": "msk.ptr", "ret": "ret.ptr", "ns": "img.shape[0]", "nf": "img.shape[1]"}}]}
C2PY_END */

extern "C" int make_clean_mask_u8(const uint8_t *img, double cut,
                                          int8_t *msk, int8_t *ret,
                                          intptr_t ns, intptr_t nf) {
    return make_clean_mask_impl<uint8_t>(img, cut, msk, ret, ns, nf);
}

/* C2PY_BEGIN
 * {"py_sig": "make_clean_mask(img: buffer, cut: float, msk: buffer, ret: buffer) -> int",
 *  "c_overloads": [{
 *    "when": "img.format == 'H' and img.ndim == 2 and img.slow_axis == 0",
 *    "sig": "int make_clean_mask_u16(const uint16_t *img, double cut, int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf) -> int",
 *    "map": {"img": "img.ptr", "cut": "cut", "msk": "msk.ptr", "ret": "ret.ptr", "ns": "img.shape[0]", "nf": "img.shape[1]"}}]}
C2PY_END */

extern "C" int make_clean_mask_u16(const uint16_t *img, double cut,
                                            int8_t *msk, int8_t *ret,
                                            intptr_t ns, intptr_t nf) {
    return make_clean_mask_impl<uint16_t>(img, cut, msk, ret, ns, nf);
}

/* C2PY_BEGIN
 * {"py_sig": "make_clean_mask(img: buffer, cut: float, msk: buffer, ret: buffer) -> int",
 *  "c_overloads": [{
 *    "when": "(img.format == 'I' or img.format == 'L') and img.itemsize == 4 and img.ndim == 2 and img.slow_axis == 0",
 *    "sig": "int make_clean_mask_u32(const uint32_t *img, double cut, int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf) -> int",
 *    "map": {"img": "img.ptr", "cut": "cut", "msk": "msk.ptr", "ret": "ret.ptr", "ns": "img.shape[0]", "nf": "img.shape[1]"}}]}
C2PY_END */

extern "C" int make_clean_mask_u32(const uint32_t *img, double cut,
                                            int8_t *msk, int8_t *ret,
                                            intptr_t ns, intptr_t nf) {
    return make_clean_mask_impl<uint32_t>(img, cut, msk, ret, ns, nf);
}
