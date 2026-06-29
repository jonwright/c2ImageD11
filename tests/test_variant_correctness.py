"""Test every ISA variant for correctness via _rebind_.

Verifies each available variant produces the same output as its baseline
(scalar) reference for the given type+shape combo. Also checks ASM vs
C-intrinsic consistency, f32 vs f64, AoS vs SoA, and threading invariance.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import sys, os, numpy as np

sys.path.insert(0,
    os.path.join(os.path.dirname(__file__), "..", "lib", "functions",
                 "score_and_refine"))
from test_data import generate_single_ubi_data, generate_random_rotations

import c2ImageD11._cImageD11 as _mod
from c2ImageD11 import cimaged11_omp_set_num_threads, OMP_MIN_NG

N_UBIS = 20
TEST_NG = 500  # below OMP_MIN_NG for fast single-thread tests
THREAD_NG = OMP_MIN_NG + 100  # above cutoff for threading tests
TOL = 0.05


def _has_avx512():
    try:
        return bool(_mod._c2py_has_avx512f())
    except AttributeError:
        return False


def _has_avx2():
    try:
        return bool(_mod._c2py_has_avx2())
    except AttributeError:
        return False


def _parse_variant(name):
    """Return (type, shape, isa, is_asm) from variant name."""
    vtype = "f32" if "f32" in name else "f64"
    shape = "SoA" if ("soa" in name or "sov" in name) else "AoS"
    if "avx512" in name:
        isa = "avx512"
    elif "avx2" in name:
        isa = "avx2"
    elif "sse41" in name:
        isa = "sse41"
    else:
        isa = "baseline"
    is_asm = "_asm" in name and not "_v2" in name
    return vtype, shape, isa, is_asm


def _isa_allowed(isa):
    """Check if a given ISA level is safe to run on this CPU."""
    if isa in ("baseline", "sse41"):
        return True
    if isa == "avx2":
        return _has_avx2() or _has_avx512()
    if isa == "avx512":
        return _has_avx512()
    return False


def _gen_score_data(ng=TEST_NG, seed=42):
    rng = np.random.RandomState(seed)
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(N_UBIS, seed + 77)
    ubis = np.zeros((N_UBIS, 3, 3))
    for i in range(N_UBIS):
        ubis[i] = np.linalg.inv(np.dot(Us[i], B))
    hkls = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    grain_ids = rng.randint(0, N_UBIS, size=ng)
    gv = np.empty((ng, 3))
    for i in range(ng):
        gv[i] = np.dot(hkls[i], np.dot(Us[grain_ids[i]], B).T)
    return ubis, gv, TOL


def _gen_sar_data(ng=TEST_NG, seed=42):
    ubi, gv, tol = generate_single_ubi_data(ng)
    return ubi.reshape(1, 3, 3), gv, TOL


def _gen_sa_data(ng=TEST_NG, seed=42):
    ubis, gv, tol = _gen_score_data(ng, seed)
    return ubis, gv, tol, np.full(ng, 999.0), np.full(ng, -1, dtype=np.int32)


def _variants(func_name):
    """Get variant list for a function; return empty tuple if unavailable."""
    vfn = getattr(_mod, "_variants_" + func_name, None)
    if vfn is None:
        return ()
    return vfn()


def _rebind(func_name, target):
    """Rebind to a specific variant or None to reset."""
    rfn = getattr(_mod, "_rebind_" + func_name, None)
    if rfn is None:
        return
    rfn(target)


def _find_baseline(variants, vtype, shape):
    """Find the lowest-tier variant for a given type+shape combo."""
    candidates = [v for v in variants
                  if _parse_variant(v)[:2] == (vtype, shape)]
    if not candidates:
        return None
    # Prefer the one with no ISA suffix; fall back to sse41, then avx2, etc.
    for isa in ("baseline", "sse41", "avx2", "avx512"):
        for v in candidates:
            if _parse_variant(v)[2] == isa:
                return v
    return candidates[0]


def _score_run(ubi, gv, tol):
    return _mod.score(ubi.copy(), gv, tol)


def _sar_run(ubi, gv, tol):
    return _mod.score_and_refine(ubi.copy(), gv, tol)


def _sa_run(ubi, gv, tol, drlv2, labels, ng):
    return _mod.score_and_assign(ubi.copy(), gv, tol, drlv2.copy(),
                                  labels.copy(), ng)


# ------------------------------------------------------------------------
# score
# ------------------------------------------------------------------------

class TestScoreVariants(object):
    """score() — each variant matches its baseline."""

    FUNC = "score"
    _run = staticmethod(_score_run)

    def get_variants(self):
        return _variants(self.FUNC)

    def get_baseline(self, variants, vtype, shape):
        return _find_baseline(variants, vtype, shape)

    def get_data(self, ng=TEST_NG, seed=42):
        ubis, gv, tol = _gen_score_data(ng, seed)
        return ubis, gv, tol

    def call(self, ubi, gv, tol):
        return self._run(ubi.copy(), gv, tol)

    def test_vs_baseline_f64_AoS(self):
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data()
        baseline = self.get_baseline(variants, "f64", "AoS")
        assert baseline, "no baseline for score f64 AoS"
        _rebind(self.FUNC, baseline)
        ref = self.call(ubis[0], gv_f64, tol)
        for v in variants:
            vt, shape, isa, is_asm = _parse_variant(v)
            if vt != "f64" or shape != "AoS" or v == baseline:
                continue
            if not _isa_allowed(isa):
                continue
            _rebind(self.FUNC, v)
            res = self.call(ubis[0], gv_f64, tol)
            assert res == ref, "score %s != baseline %s: %r != %r" % (v, baseline, res, ref)
        _rebind(self.FUNC, None)

    def test_vs_baseline_f64_SoA(self):
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data()
        gv_s64 = np.ascontiguousarray(gv_f64.T)
        baseline = self.get_baseline(variants, "f64", "SoA")
        assert baseline, "no baseline for score f64 SoA"
        _rebind(self.FUNC, baseline)
        ref = self.call(ubis[0], gv_s64, tol)
        for v in variants:
            vt, shape, isa, is_asm = _parse_variant(v)
            if vt != "f64" or shape != "SoA" or v == baseline:
                continue
            if not _isa_allowed(isa):
                continue
            _rebind(self.FUNC, v)
            res = self.call(ubis[0], gv_s64, tol)
            assert res == ref, "score %s != baseline %s: %r != %r" % (v, baseline, res, ref)
        _rebind(self.FUNC, None)

    def test_vs_baseline_f32_AoS(self):
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data()
        gv_f32 = gv_f64.astype(np.float32)
        baseline = self.get_baseline(variants, "f32", "AoS")
        assert baseline, "no baseline for score f32 AoS"
        _rebind(self.FUNC, baseline)
        ref = self.call(ubis[0], gv_f32, tol)
        for v in variants:
            vt, shape, isa, is_asm = _parse_variant(v)
            if vt != "f32" or shape != "AoS" or v == baseline:
                continue
            if not _isa_allowed(isa):
                continue
            _rebind(self.FUNC, v)
            res = self.call(ubis[0], gv_f32, tol)
            assert res == ref, "score %s != baseline %s: %r != %r" % (v, baseline, res, ref)
        _rebind(self.FUNC, None)

    def test_vs_baseline_f32_SoA(self):
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data()
        gv_s32 = np.ascontiguousarray(gv_f64.T).astype(np.float32)
        baseline = self.get_baseline(variants, "f32", "SoA")
        assert baseline, "no baseline for score f32 SoA"
        _rebind(self.FUNC, baseline)
        ref = self.call(ubis[0], gv_s32, tol)
        for v in variants:
            vt, shape, isa, is_asm = _parse_variant(v)
            if vt != "f32" or shape != "SoA" or v == baseline:
                continue
            if not _isa_allowed(isa):
                continue
            _rebind(self.FUNC, v)
            res = self.call(ubis[0], gv_s32, tol)
            assert res == ref, "score %s != baseline %s: %r != %r" % (v, baseline, res, ref)
        _rebind(self.FUNC, None)

    def test_AoS_SoA_match_f64(self):
        """All f64 AoS variants must match their SoA counterparts."""
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data()
        gv_s64 = np.ascontiguousarray(gv_f64.T)
        isa_levels = [isa for isa in ("avx512", "avx2", "baseline") if _isa_allowed(isa)]
        for vt in ("f64", "f32"):
            for isa in isa_levels:
                aos_name = None
                soa_name = None
                for v in variants:
                    pvt, pshape, pisa, _ = _parse_variant(v)
                    if pvt != vt or pisa != isa:
                        continue
                    if pshape == "AoS" and aos_name is None:
                        aos_name = v
                    if pshape == "SoA" and soa_name is None:
                        soa_name = v
                if not aos_name or not soa_name:
                    continue
                if vt == "f64":
                    gv_aos = gv_f64
                    gv_soa = gv_s64
                else:
                    gv_aos = gv_f64.astype(np.float32)
                    gv_soa = gv_s64.astype(np.float32)
                _rebind(self.FUNC, aos_name)
                raos = self.call(ubis[0], gv_aos, tol)
                _rebind(self.FUNC, soa_name)
                rsoa = self.call(ubis[0], gv_soa, tol)
                assert raos == rsoa, \
                    "score AoS(%s)/SoA(%s) mismatch: %r != %r" % (
                        aos_name, soa_name, raos, rsoa)
        _rebind(self.FUNC, None)

    def test_threading(self):
        """Each variant produces same result with 1T and nT (above cutoff)."""
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data(ng=THREAD_NG, seed=99)
        ncores = max(2, os.cpu_count() or 2)
        for v in variants:
            vt, shape, isa, _ = _parse_variant(v)
            if not _isa_allowed(isa):
                continue
            _rebind(self.FUNC, v)
            if shape == "SoA":
                gv = np.ascontiguousarray(gv_f64.T) if vt == "f64" else \
                     np.ascontiguousarray(gv_f64.T).astype(np.float32)
            else:
                gv = gv_f64 if vt == "f64" else gv_f64.astype(np.float32)
            cimaged11_omp_set_num_threads(1)
            r1 = self.call(ubis[0], gv, tol)
            cimaged11_omp_set_num_threads(ncores)
            rn = self.call(ubis[0], gv, tol)
            assert r1 == rn, \
                "score %s 1T/%dT mismatch: %r != %r" % (v, ncores, r1, rn)
        _rebind(self.FUNC, None)


# ------------------------------------------------------------------------
# score_and_refine
# ------------------------------------------------------------------------

class TestScoreAndRefineVariants(object):
    """score_and_refine() — each variant matches its baseline."""

    FUNC = "score_and_refine"
    _run = staticmethod(_sar_run)

    def get_variants(self):
        return _variants(self.FUNC)

    def get_baseline(self, variants, vtype, shape):
        return _find_baseline(variants, vtype, shape)

    def get_data(self, ng=TEST_NG, seed=42):
        return _gen_sar_data(ng, seed)

    def call(self, ubi, gv, tol):
        return self._run(ubi.copy(), gv, tol)

    def _assert_close(self, got, ref, vname, bname):
        ngot, sgot = got
        nref, sref = ref
        assert ngot == nref, \
            "%s != baseline %s: n %d != %d" % (vname, bname, ngot, nref)
        assert abs(sgot - sref) < 1e-10, \
            "%s != baseline %s: sumdrlv2 %.12e != %.12e" % (vname, bname, sgot, sref)

    def test_vs_baseline(self):
        """All variants must match the baseline for their type+shape combo."""
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data()
        isa_levels = [isa for isa in ("sse41", "baseline") if isa in {
            _parse_variant(v)[2] for v in variants} or isa == "baseline"]
        for vtype in ("f64", "f32"):
            for shape in ("AoS", "SoA"):
                baseline = self.get_baseline(variants, vtype, shape)
                if baseline is None:
                    continue
                if vtype == "f32":
                    gv = gv_f64.astype(np.float32)
                else:
                    gv = gv_f64
                if shape == "SoA":
                    gv = np.ascontiguousarray(gv.T)
                _rebind(self.FUNC, baseline)
                ref = self.call(ubis[0], gv, tol)
                for v in variants:
                    vt, vs, isa, is_asm = _parse_variant(v)
                    if vt != vtype or vs != shape or v == baseline:
                        continue
                    if not _isa_allowed(isa):
                        continue
                    _rebind(self.FUNC, v)
                    res = self.call(ubis[0], gv, tol)
                    self._assert_close(res, ref, v, baseline)
        _rebind(self.FUNC, None)

    def test_AoS_SoA_match(self):
        """AoS and SoA paths at same ISA level must produce identical results."""
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data()
        gv_s64 = np.ascontiguousarray(gv_f64.T)
        isa_levels = [isa for isa in ("avx512", "avx2", "sse41", "baseline")
                      if _isa_allowed(isa)]
        for vt in ("f64", "f32"):
            for isa in isa_levels:
                aos_name = None
                soa_name = None
                for v in variants:
                    pvt, pshape, pisa, _ = _parse_variant(v)
                    if pvt != vt or pisa != isa:
                        continue
                    if pshape == "AoS" and aos_name is None:
                        aos_name = v
                    if pshape == "SoA" and soa_name is None:
                        soa_name = v
                if not aos_name or not soa_name:
                    continue
                if vt == "f64":
                    gv_aos = gv_f64
                    gv_soa = gv_s64
                else:
                    gv_aos = gv_f64.astype(np.float32)
                    gv_soa = gv_s64.astype(np.float32)
                _rebind(self.FUNC, aos_name)
                na, sa = self.call(ubis[0], gv_aos, tol)
                _rebind(self.FUNC, soa_name)
                ns, ss = self.call(ubis[0], gv_soa, tol)
                assert na == ns, \
                    "sar AoS(%s)/SoA(%s) n mismatch: %d != %d" % (
                        aos_name, soa_name, na, ns)
                assert abs(sa - ss) < 1e-10, \
                    "sar AoS(%s)/SoA(%s) s mismatch" % (aos_name, soa_name)
        _rebind(self.FUNC, None)

    def test_f32_f64_consistent(self):
        """f32 and f64 variants at same ISA level should agree approximately."""
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data()
        isa_levels = [isa for isa in ("avx512", "avx2", "sse41", "baseline")
                      if _isa_allowed(isa)]
        for shape in ("AoS", "SoA"):
            for isa in isa_levels:
                f64_name = None
                f32_name = None
                for v in variants:
                    vt, vs, visa, _ = _parse_variant(v)
                    if vs != shape or visa != isa:
                        continue
                    if vt == "f64" and f64_name is None:
                        f64_name = v
                    if vt == "f32" and f32_name is None:
                        f32_name = v
                if not f64_name or not f32_name:
                    continue
                gv64 = gv_f64 if shape == "AoS" else np.ascontiguousarray(gv_f64.T)
                gv32 = gv64.astype(np.float32)
                _rebind(self.FUNC, f64_name)
                n64, s64 = self.call(ubis[0], gv64, tol)
                _rebind(self.FUNC, f32_name)
                n32, s32 = self.call(ubis[0], gv32, tol)
                assert abs(n64 - n32) <= 2, \
                    "sar %s/%s n too far: %d vs %d" % (f64_name, f32_name, n64, n32)
                assert abs(s64 - s32) < 1e-4, \
                    "sar %s/%s s too far" % (f64_name, f32_name)
        _rebind(self.FUNC, None)

    def test_threading(self):
        """Each variant: 1T == nT above OMP_MIN_NG."""
        variants = self.get_variants()
        ubis, gv_f64, tol = self.get_data(ng=THREAD_NG, seed=99)
        ncores = max(2, os.cpu_count() or 2)
        for v in variants:
            vt, shape, isa, _ = _parse_variant(v)
            if not _isa_allowed(isa):
                continue
            _rebind(self.FUNC, v)
            if vt == "f32":
                gv = gv_f64.astype(np.float32)
            else:
                gv = gv_f64
            if shape == "SoA":
                gv = np.ascontiguousarray(gv.T)
            cimaged11_omp_set_num_threads(1)
            n1, s1 = self.call(ubis[0], gv, tol)
            cimaged11_omp_set_num_threads(ncores)
            nn, sn = self.call(ubis[0], gv, tol)
            assert n1 == nn, \
                "sar %s 1T/%dT n mismatch: %d != %d" % (v, ncores, n1, nn)
            assert abs(s1 - sn) < 1e-10, \
                "sar %s 1T/%dT s mismatch" % v
        _rebind(self.FUNC, None)


# ------------------------------------------------------------------------
# score_and_assign
# ------------------------------------------------------------------------

class TestScoreAndAssignVariants(object):
    """score_and_assign() — each variant matches its baseline; ASM vs C."""

    FUNC = "score_and_assign"
    _run = staticmethod(_sa_run)

    def get_variants(self):
        return _variants(self.FUNC)

    def get_baseline(self, variants, vtype, shape):
        return _find_baseline(variants, vtype, shape)

    def get_data(self, ng=TEST_NG, seed=42):
        ubis, gv, tol, drlv2, labels = _gen_sa_data(ng, seed)
        return ubis, gv, tol, drlv2, labels

    def call(self, ubi, gv, tol, drlv2, labels, ng):
        return self._run(ubi.copy(), gv, tol, drlv2.copy(), labels.copy(), ng)

    def test_vs_baseline(self):
        """All variants must match the baseline for their type+shape."""
        variants = self.get_variants()
        ubis, gv_f64, tol, drlv2, labels = self.get_data()
        ng = TEST_NG
        for vtype in ("f64", "f32"):
            for shape in ("AoS", "SoA"):
                baseline = self.get_baseline(variants, vtype, shape)
                if baseline is None:
                    continue
                if vtype == "f32":
                    gv = gv_f64.astype(np.float32)
                    dv = drlv2.astype(np.float32)
                else:
                    gv = gv_f64
                    dv = drlv2
                if shape == "SoA":
                    gv = np.ascontiguousarray(gv.T)
                _rebind(self.FUNC, baseline)
                ref_drlv2 = dv.copy()
                ref_labels = labels.copy()
                self.call(ubis[0], gv, tol, ref_drlv2, ref_labels, ng)
                for v in variants:
                    vt, vs, isa, is_asm = _parse_variant(v)
                    if vt != vtype or vs != shape or v == baseline:
                        continue
                    if not _isa_allowed(isa):
                        continue
                    _rebind(self.FUNC, v)
                    test_drlv2 = dv.copy()
                    test_labels = labels.copy()
                    self.call(ubis[0], gv, tol, test_drlv2, test_labels, ng)
                    assert np.allclose(test_drlv2, ref_drlv2, rtol=0, atol=1e-10), \
                        "sa %s drlv2 != baseline %s" % (v, baseline)
                    assert np.array_equal(test_labels, ref_labels), \
                        "sa %s labels != baseline %s" % (v, baseline)
        _rebind(self.FUNC, None)

    def test_asm_matches_C_intrinsic(self):
        """Each ASM variant must match its C-intrinsic sibling."""
        variants = self.get_variants()
        ubis, gv_f64, tol, drlv2, labels = self.get_data()
        ng = TEST_NG
        asm_pairs = []
        for v in variants:
            if "_asm" in v:
                c_sibling = v.replace("_asm", "")
                if c_sibling in variants:
                    asm_pairs.append((v, c_sibling))
        for asm_name, c_name in asm_pairs:
            vt, shape, isa, _ = _parse_variant(asm_name)
            if not _isa_allowed(isa):
                continue
            if vt == "f32":
                gv = gv_f64.astype(np.float32)
                dv = drlv2.astype(np.float32)
            else:
                gv = gv_f64
                dv = drlv2
            if shape == "SoA":
                gv = np.ascontiguousarray(gv.T)

            _rebind(self.FUNC, asm_name)
            asm_drlv2 = dv.copy()
            asm_labels = labels.copy()
            self.call(ubis[0], gv, tol, asm_drlv2, asm_labels, ng)

            _rebind(self.FUNC, c_name)
            c_drlv2 = dv.copy()
            c_labels = labels.copy()
            self.call(ubis[0], gv, tol, c_drlv2, c_labels, ng)

            assert np.allclose(asm_drlv2, c_drlv2, rtol=0, atol=1e-10), \
                "sa ASM %s drlv2 != C %s" % (asm_name, c_name)
            assert np.array_equal(asm_labels, c_labels), \
                "sa ASM %s labels != C %s" % (asm_name, c_name)
        _rebind(self.FUNC, None)

    def test_AoS_SoA_match(self):
        """AoS and SoA at same ISA level produce identical results."""
        variants = self.get_variants()
        ubis, gv_f64, tol, drlv2, labels = self.get_data()
        gv_s64 = np.ascontiguousarray(gv_f64.T)
        ng = TEST_NG
        isa_levels = [isa for isa in ("avx512", "avx2", "baseline")
                      if _isa_allowed(isa)]
        for vt in ("f64", "f32"):
            for isa in isa_levels:
                aos_name = None
                soa_name = None
                for v in variants:
                    pvt, pshape, pisa, is_asm = _parse_variant(v)
                    if pvt != vt or pisa != isa:
                        continue
                    # Prefer non-asm for AoS, asm for SoA (if both exist)
                    if pshape == "AoS" and (aos_name is None or is_asm):
                        if not is_asm or aos_name is None:
                            aos_name = v if not is_asm else aos_name
                    if pshape == "SoA" and soa_name is None:
                        soa_name = v
                # Fallback: just pick first match of each shape
                if not aos_name:
                    for v in variants:
                        pvt, pshape, pisa, _ = _parse_variant(v)
                        if pvt == vt and pshape == "AoS" and pisa == isa:
                            aos_name = v; break
                if not soa_name:
                    for v in variants:
                        pvt, pshape, pisa, _ = _parse_variant(v)
                        if pvt == vt and pshape == "SoA" and pisa == isa:
                            soa_name = v; break
                if not aos_name or not soa_name:
                    continue
                if vt == "f64":
                    gv_aos = gv_f64
                    gv_soa = gv_s64
                    dv = drlv2
                else:
                    gv_aos = gv_f64.astype(np.float32)
                    gv_soa = gv_s64.astype(np.float32)
                    dv = drlv2.astype(np.float32)

                _rebind(self.FUNC, aos_name)
                aos_drlv2 = dv.copy()
                aos_labels = labels.copy()
                self.call(ubis[0], gv_aos, tol, aos_drlv2, aos_labels, ng)

                _rebind(self.FUNC, soa_name)
                soa_drlv2 = dv.copy()
                soa_labels = labels.copy()
                self.call(ubis[0], gv_soa, tol, soa_drlv2, soa_labels, ng)

                assert np.allclose(aos_drlv2, soa_drlv2, rtol=0, atol=1e-10), \
                    "sa AoS(%s)/SoA(%s) drlv2 mismatch" % (aos_name, soa_name)
                assert np.array_equal(aos_labels, soa_labels), \
                    "sa AoS(%s)/SoA(%s) labels mismatch" % (aos_name, soa_name)
        _rebind(self.FUNC, None)

    def test_threading(self):
        """Each variant: 1T == nT above OMP_MIN_NG."""
        variants = self.get_variants()
        ubis, gv_f64, tol, drlv2, labels = self.get_data(ng=THREAD_NG, seed=99)
        ng = THREAD_NG
        ncores = max(2, os.cpu_count() or 2)
        for v in variants:
            vt, shape, isa, _ = _parse_variant(v)
            if not _isa_allowed(isa):
                continue
            _rebind(self.FUNC, v)
            if vt == "f32":
                gv = gv_f64.astype(np.float32)
                dv = drlv2.astype(np.float32)
            else:
                gv = gv_f64
                dv = drlv2
            if shape == "SoA":
                gv = np.ascontiguousarray(gv.T)

            cimaged11_omp_set_num_threads(1)
            dv1 = dv.copy(); lb1 = labels.copy()
            self.call(ubis[0], gv, tol, dv1, lb1, ng)

            cimaged11_omp_set_num_threads(ncores)
            dvn = dv.copy(); lbn = labels.copy()
            self.call(ubis[0], gv, tol, dvn, lbn, ng)

            assert np.allclose(dv1, dvn, rtol=0, atol=1e-10), \
                "sa %s 1T/nT drlv2 mismatch" % v
            assert np.array_equal(lb1, lbn), \
                "sa %s 1T/nT labels mismatch" % v
        _rebind(self.FUNC, None)
