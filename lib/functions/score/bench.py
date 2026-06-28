#!/usr/bin/env python3
"""Benchmark score() -- throughput, threading, f2py comparison."""
from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys, time, struct, ctypes, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from score_and_refine.test_data import generate_single_ubi_data
import c2ImageD11

def detect_variant(fn, ubi, gv, tol, mod):
    prefix = "_c2py_ol_ptr_score__"
    ol_ptrs = {}
    for attr in dir(mod):
        if attr.startswith(prefix):
            ptr = getattr(mod, attr)
            mod._c2py_perf_reset(ptr)
            ol_ptrs[attr[len(prefix):]] = ptr
    mod._c2py_perf_set_enabled(1)
    fn(ubi.copy(), gv, tol)
    mod._c2py_perf_set_enabled(0)
    for name, ptr in ol_ptrs.items():
        raw = ctypes.string_at(ptr, 8)
        if struct.unpack('Q', raw)[0]:
            return name
    return "unknown"

sizes = [100000, 500000, 2000000]
n_cores = os.cpu_count() or 4

try:
    import ImageD11._cImageD11 as old
    have_f2py = True
except ImportError:
    have_f2py = False

mod = c2ImageD11._cImageD11

# Print variants
ubi0, gv0, tol0 = generate_single_ubi_data(sizes[0])
print("Variants dispatched:")
print("  f64: %s" % detect_variant(c2ImageD11.score, ubi0, gv0, tol0, mod))
print("  f32: %s" % detect_variant(c2ImageD11.score, ubi0, gv0.astype(np.float32), tol0, mod))
print()

for ng in sizes:
    ubi, gv, tol = generate_single_ubi_data(ng)
    gv_f32 = gv.astype(np.float32)

    if have_f2py:
        old.cimaged11_omp_set_num_threads(1)
        nc = max(5, int(2e8 // ng))
        for _ in range(3): old.score(ubi.copy(), gv, tol)
        t0 = time.perf_counter()
        for _ in range(nc): old.score(ubi.copy(), gv, tol)
        t1 = time.perf_counter()
        f2py_M = ng * nc / (t1 - t0) / 1e6
        sys.stdout.write("ng=%7d  f2py=%7.0fM/s" % (ng, f2py_M))
    else:
        sys.stdout.write("ng=%7d" % ng)

    for nthr in [1, n_cores]:
        c2ImageD11.cimaged11_omp_set_num_threads(nthr)
        nc = max(5, int(2e8 // ng))
        for _ in range(3): c2ImageD11.score(ubi.copy(), gv, tol)
        t0 = time.perf_counter()
        for _ in range(nc): c2ImageD11.score(ubi.copy(), gv, tol)
        t1 = time.perf_counter()
        thr = ng * nc / (t1 - t0) / 1e6
        sys.stdout.write("  f64_%dT=%7.0fM/s" % (nthr, thr))

        c2ImageD11.cimaged11_omp_set_num_threads(nthr)
        for _ in range(3): c2ImageD11.score(ubi.copy(), gv_f32, tol)
        t0 = time.perf_counter()
        for _ in range(nc): c2ImageD11.score(ubi.copy(), gv_f32, tol)
        t1 = time.perf_counter()
        thr = ng * nc / (t1 - t0) / 1e6
        sys.stdout.write("  f32_%dT=%7.0fM/s" % (nthr, thr))
    sys.stdout.write("\n")
