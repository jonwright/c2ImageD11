#include "reorderlut_impl.hpp"

/* C2PY_BEGIN
 * {"py_sig": "reorderlut_f32_a32(data: buffer, adr: buffer, out: buffer) -> void",
 *  "doc": "lut called in sandbox/fazit.py simple\nloop with openmp saying out[i] in data[adr[i]]\ne.g. semi-random reading",
 *  "checks": ["data.format == 'f'", "adr.format == 'I' or adr.itemsize == 4",
 *      "adr.n == data.n", "out.format == 'f'", "out.n == data.n"],
 *  "gil_release": true,
 *  "c_overloads": [{"when": "data.format == 'f' and out.format == 'f'",
 *      "sig": "void reorderlut_f32_a32(const float *data, const uint32_t *adr, float *out, intptr_t N)",
 *      "map": {"data": "data.ptr", "adr": "adr.ptr", "out": "out.ptr", "N": "data.n"}}]}
C2PY_END */

extern "C" void reorderlut_f32_a32(const float * data, const uint32_t * lut,
                                    float * out, intptr_t N) {
    reorderlut_impl<float>(data, lut, out, N);
}

/* C2PY_BEGIN
 * {"py_sig": "reorderlut_u16_a32(data: buffer, adr: buffer, out: buffer) -> void",
 *  "doc": "out[i] = data[adr[i]].",
 *  "checks": ["data.format == 'H' or data.itemsize == 2", "adr.format == 'I' or adr.itemsize == 4",
 *      "adr.n == data.n", "out.format == 'H' or out.itemsize == 2", "out.n == data.n"],
 *  "gil_release": true,
 *  "c_overloads": [{"when": "adr.format == 'I' or adr.itemsize == 4",
 *      "sig": "void reorderlut_u16_a32(const uint16_t *data, const uint32_t *adr, uint16_t *out, intptr_t N)",
 *      "map": {"data": "data.ptr", "adr": "adr.ptr", "out": "out.ptr", "N": "data.n"}}]}
C2PY_END */

extern "C" void reorderlut_u16_a32(const uint16_t * data, const uint32_t * lut,
                                    uint16_t * out, intptr_t N) {
    reorderlut_impl<uint16_t>(data, lut, out, N);
}
