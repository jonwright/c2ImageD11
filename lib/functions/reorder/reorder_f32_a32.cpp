#include "reorder_impl.hpp"

/* C2PY_BEGIN
 * {"py_sig": "reorder_f32_a32(data: buffer, adr: buffer, out: buffer) -> void",
 *  "doc": "called in sandbox/fazit.py simple\nloop with openmp saying out[adr[i]] in data[i]\ne.g. semi-random writing",
 *  "checks": ["data.format == 'f'", "adr.format == 'I' or adr.itemsize == 4",
 *      "adr.n == data.n", "out.format == 'f'", "out.n >= data.n"],
 *  "gil_release": true,
 *  "c_overloads": [{"when": "data.format == 'f' and out.format == 'f'",
 *      "sig": "void reorder_f32_a32(const float *data, const uint32_t *adr, float *out, intptr_t N)",
 *      "map": {"data": "data.ptr", "adr": "adr.ptr", "out": "out.ptr", "N": "data.n"}}]}
C2PY_END */

extern "C" void reorder_f32_a32(const float * data, const uint32_t * adr,
                                 float * out, intptr_t N) {
    reorder_impl<float>(data, adr, out, N);
}
