#include "cImageD11.h"

extern int c2py_amd64_sse4_1;
extern int c2py_amd64_avx2;
extern int c2py_amd64_avx512f;
extern int c2py_arm64_asimd;
extern int c2py_arm64_sve;
extern int c2py_arm64_sve2;
extern int c2py_ppc64_altivec;
extern int c2py_ppc64_vsx;

/* ---- x86_64 ---- */

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_sse4_1() -> int",
 *     "doc": "Returns 1 if the CPU supports SSE4.1, 0 otherwise.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_sse4_1() -> int",
 *         "map": {},
 *     }],
 * }
 C2PY_END */
int _c2py_has_sse4_1(void) { return c2py_amd64_sse4_1; }

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_sse4_1(val: int) -> int",
 *     "doc": "Set c2py_amd64_sse4_1 (0=off, 1=on). Returns old value.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_sse4_1(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 C2PY_END */
int _c2py_set_sse4_1(int val) {
    int old = c2py_amd64_sse4_1;
    c2py_amd64_sse4_1 = val;
    return old;
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_avx2() -> int",
 *     "doc": "Returns 1 if the CPU supports AVX2, 0 otherwise.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_avx2() -> int",
 *         "map": {},
 *     }],
 * }
 C2PY_END */
int _c2py_has_avx2(void) { return c2py_amd64_avx2; }

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_avx2(val: int) -> int",
 *     "doc": "Set c2py_amd64_avx2 (0=off, 1=on). Returns old value.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_avx2(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 C2PY_END */
int _c2py_set_avx2(int val) {
    int old = c2py_amd64_avx2;
    c2py_amd64_avx2 = val;
    return old;
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_avx512f() -> int",
 *     "doc": "Returns 1 if the CPU supports AVX-512F, 0 otherwise.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_avx512f() -> int",
 *         "map": {},
 *     }],
 * }
 C2PY_END */
int _c2py_has_avx512f(void) { return c2py_amd64_avx512f; }

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_avx512f(val: int) -> int",
 *     "doc": "Set c2py_amd64_avx512f (0=off, 1=on). Returns old value.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_avx512f(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 C2PY_END */
int _c2py_set_avx512f(int val) {
    int old = c2py_amd64_avx512f;
    c2py_amd64_avx512f = val;
    return old;
}

/* ---- arm64 ---- */

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_asimd() -> int",
 *     "doc": "Returns 1 if the CPU supports ASIMD (NEON), 0 otherwise.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_asimd() -> int",
 *         "map": {},
 *     }],
 * }
 C2PY_END */
int _c2py_has_asimd(void) { return c2py_arm64_asimd; }

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_asimd(val: int) -> int",
 *     "doc": "Set c2py_arm64_asimd (0=off, 1=on). Returns old value.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_asimd(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 C2PY_END */
int _c2py_set_asimd(int val) {
    int old = c2py_arm64_asimd;
    c2py_arm64_asimd = val;
    return old;
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_sve() -> int",
 *     "doc": "Returns 1 if the CPU supports SVE, 0 otherwise.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_sve() -> int",
 *         "map": {},
 *     }],
 * }
 C2PY_END */
int _c2py_has_sve(void) { return c2py_arm64_sve; }

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_sve(val: int) -> int",
 *     "doc": "Set c2py_arm64_sve (0=off, 1=on). Returns old value.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_sve(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 C2PY_END */
int _c2py_set_sve(int val) {
    int old = c2py_arm64_sve;
    c2py_arm64_sve = val;
    return old;
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_sve2() -> int",
 *     "doc": "Returns 1 if the CPU supports SVE2, 0 otherwise.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_sve2() -> int",
 *         "map": {},
 *     }],
 * }
 C2PY_END */
int _c2py_has_sve2(void) { return c2py_arm64_sve2; }

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_sve2(val: int) -> int",
 *     "doc": "Set c2py_arm64_sve2 (0=off, 1=on). Returns old value.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_sve2(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 C2PY_END */
int _c2py_set_sve2(int val) {
    int old = c2py_arm64_sve2;
    c2py_arm64_sve2 = val;
    return old;
}

/* ---- ppc64 ---- */

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_altivec() -> int",
 *     "doc": "Returns 1 if the CPU supports AltiVec, 0 otherwise.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_altivec() -> int",
 *         "map": {},
 *     }],
 * }
 C2PY_END */
int _c2py_has_altivec(void) { return c2py_ppc64_altivec; }

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_altivec(val: int) -> int",
 *     "doc": "Set c2py_ppc64_altivec (0=off, 1=on). Returns old value.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_altivec(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 C2PY_END */
int _c2py_set_altivec(int val) {
    int old = c2py_ppc64_altivec;
    c2py_ppc64_altivec = val;
    return old;
}

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_has_vsx() -> int",
 *     "doc": "Returns 1 if the CPU supports VSX, 0 otherwise.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_has_vsx() -> int",
 *         "map": {},
 *     }],
 * }
 C2PY_END */
int _c2py_has_vsx(void) { return c2py_ppc64_vsx; }

/* C2PY_BEGIN
 * {
 *     "py_sig": "_c2py_set_vsx(val: int) -> int",
 *     "doc": "Set c2py_ppc64_vsx (0=off, 1=on). Returns old value.",
 *     "c_overloads": [{
 *         "sig": "int _c2py_set_vsx(int val) -> int",
 *         "map": {"val": "val"},
 *     }],
 * }
 C2PY_END */
int _c2py_set_vsx(int val) {
    int old = c2py_ppc64_vsx;
    c2py_ppc64_vsx = val;
    return old;
}
