#!/usr/bin/env python3
"""Benchmark score() -- throughput, threading, f2py baseline.

Also runs an exact-count correctness check (--check, or always via --check-all)
that compares against the f2py reference or a numpy reference on IMPERFECT
data at ng % 8 != 0, 1 thread and n threads.  This is the check that would
have caught the -ffast-math magic-trick miscompile in the SIMD scalar tails
(issue #33): perfect-match data and ng divisible by 8 never exercise the
tail path.
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from score_and_refine.test_data import (
    generate_single_ubi_data, generate_single_ubi_data_perturbed)
import c2ImageD11

ng = 200000
niter = 30
n_cores = os.cpu_count() or 4

ubi, gv, tol = generate_single_ubi_data(ng)
gv_f32 = gv.astype(np.float32)
gv_soa = gv.T.copy()
gv_soa_f32 = gv_f32.T.copy()


def numpy_score(ubi, gv, tol):
    """Exact reference for score() using numpy round-half-to-even."""
    hkl = np.dot(gv, ubi.T)
    ih = np.rint(hkl)
    drlv2 = ((hkl - ih) ** 2).sum(axis=1)
    return int((drlv2 < tol * tol).sum())


def measure(fn, ubi, gv, tol, nthr):
    c2ImageD11.cimaged11_omp_set_num_threads(nthr)
    for _ in range(5): fn(ubi.copy(), gv, tol)
    t0 = time.perf_counter()
    for _ in range(niter): fn(ubi.copy(), gv, tol)
    t1 = time.perf_counter()
    return ng * niter / (t1 - t0) / 1e6

try:
    import ImageD11._cImageD11 as old
    old.cimaged11_omp_set_num_threads(1)
    f2py_1t = measure(old.score, ubi, gv, tol, 1)
    have_f2py = True
except ImportError:
    have_f2py = False


def check_correctness():
    """Exact-count check on imperfect data, tail-exercising ng, 1T and nT.

    Fails loudly if the count differs from the reference.  The perfect data
    used for throughput measurement would hide this, as would any ng that is
    a multiple of the SIMD width (8 for f64 AVX-512, 4 for AVX2).
    """
    cng = 200011  # not a multiple of 8: exercises the scalar tails
    ubi_p, gv_p, tol_p = generate_single_ubi_data_perturbed(cng)
    if have_f2py:
        old.cimaged11_omp_set_num_threads(1)
    reference = old.score if have_f2py else numpy_score
    exp_1t = reference(ubi_p, gv_p, tol_p)
    exp_nt = reference(ubi_p, gv_p, tol_p)
    got_1t = None
    for nthr in [1, n_cores]:
        c2ImageD11.cimaged11_omp_set_num_threads(nthr)
        got = c2ImageD11.score(ubi_p, gv_p, tol_p)
        exp = exp_1t if nthr == 1 else exp_nt
        assert got == exp, (
            "score() correctness FAILED at %d threads: "
            "c2=%d reference=%d (ng=%d)" % (nthr, got, exp, cng))
        if nthr == 1:
            got_1t = got
    print("score() correctness OK: %d peaks @ ng=%d (1T and nT match reference)"
          % (got_1t, cng))


print("score() throughput (ng=%d)" % ng)
if have_f2py:
    print("f2py baseline: %.0f M/s" % f2py_1t)
print()
print("%-10s  %10s  %10s  %10s  %10s" % ("threads", "AoS_f64", "SoA_f64", "AoS_f32", "SoA_f32"))
print("-" * 55)

row_1t = "%10s" % "1T"
row_nt = "%10s" % ("nT (%d)" % n_cores)
for gv_arr in [gv, gv_soa, gv_f32, gv_soa_f32]:
    t1 = measure(c2ImageD11.score, ubi, gv_arr, tol, 1)
    tn = measure(c2ImageD11.score, ubi, gv_arr, tol, n_cores)
    row_1t += "  %8.0fM" % t1
    row_nt += "  %8.0fM" % tn
print(row_1t)
print(row_nt)

if "--check" in sys.argv or "--check-all" in sys.argv:
    check_correctness()

if "--json" in sys.argv:
    import json
    data = {
        "function": "score",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "cpu_info": os.popen("cat /proc/cpuinfo | grep 'model name' | head -1 | cut -d: -f2-").read().strip(),
        "measurements": {
            "AoS_f64_1T": {"ng": ng, "M_gv_per_s": int(measure(c2ImageD11.score, ubi, gv, tol, 1))},
            "AoS_f64_nT": {"ng": ng, "M_gv_per_s": int(measure(c2ImageD11.score, ubi, gv, tol, n_cores))},
            "SoA_f64_1T": {"ng": ng, "M_gv_per_s": int(measure(c2ImageD11.score, ubi, gv_soa, tol, 1))},
            "SoA_f64_nT": {"ng": ng, "M_gv_per_s": int(measure(c2ImageD11.score, ubi, gv_soa, tol, n_cores))},
            "AoS_f32_1T": {"ng": ng, "M_gv_per_s": int(measure(c2ImageD11.score, ubi, gv_f32, tol, 1))},
            "SoA_f32_1T": {"ng": ng, "M_gv_per_s": int(measure(c2ImageD11.score, ubi, gv_soa_f32, tol, 1))},
        },
        "f2py_baseline": {"M_gv_per_s": int(f2py_1t)} if have_f2py else None,
    }
    print(json.dumps(data))
