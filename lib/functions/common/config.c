/* config.c — Runtime CPU flag control for benchmarking.
 * Allows temporarily disabling ISA detection to measure lower-tier
 * variants without rebuilding the .so.
 */

/* Declared in c2py_runtime.c */
extern int c2py_amd64_avx512f;
extern int c2py_amd64_avx2;

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_avx512f(val: int) -> int",
 *     "doc": "Temporarily set c2py_amd64_avx512f flag (0=off, 1=on). Returns old value.",
 *     "params": { "val": "New value (0 or 1)." },
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_avx512f(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 * C2PY_END */
int _c2py_set_avx512f(int val) {
    int old = c2py_amd64_avx512f;
    c2py_amd64_avx512f = val;
    return old;
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_avx2(val: int) -> int",
 *     "doc": "Temporarily set c2py_amd64_avx2 flag (0=off, 1=on). Returns old value.",
 *     "params": { "val": "New value (0 or 1)." },
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_avx2(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 * C2PY_END */
int _c2py_set_avx2(int val) {
    int old = c2py_amd64_avx2;
    c2py_amd64_avx2 = val;
    return old;
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_avx512f() -> int",
 *     "doc": "Returns 1 if the CPU supports AVX-512F, 0 otherwise. Read-only.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_avx512f() -> int",
 *         "map": {},
 *     }],
 * }
 * C2PY_END */
int _c2py_has_avx512f(void) {
    return c2py_amd64_avx512f;
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_avx2() -> int",
 *     "doc": "Returns 1 if the CPU supports AVX2, 0 otherwise. Read-only.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_avx2() -> int",
 *         "map": {},
 *     }],
 * }
 * C2PY_END */
int _c2py_has_avx2(void) {
    return c2py_amd64_avx2;
}
