/* make_clean_mask_u16.cpp — uint16_t variant */
#include "make_clean_mask.hpp"

/* C2PY_BEGIN
 * {"py_sig": "make_clean_mask(img: buffer, cut: float, msk: buffer, ret: buffer) -> int",
 *  "c_overloads": [{
 *    "when": "img.format == 'H' and img.ndim == 2 and img.slow_axis == 0",
 *    "sig": "int make_clean_mask_u16(const uint16_t *img, double cut, int8_t *msk, int8_t *ret, intptr_t ns, intptr_t nf) -> int",
 *    "map": {"img": "img.ptr", "cut": "cut", "msk": "msk.ptr", "ret": "ret.ptr", "ns": "img.shape[0]", "nf": "img.shape[1]"}
 *  }]}
 C2PY_END */

extern "C" int make_clean_mask_u16(const uint16_t *img, double cut,
                                     int8_t *msk, int8_t *ret,
                                     intptr_t ns, intptr_t nf) {
    return make_clean_mask_impl<uint16_t>(img, cut, msk, ret, ns, nf);
}
