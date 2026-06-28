#!/usr/bin/env python3
"""Benchmark score() -- throughput, threading, f2py comparison."""
from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from score_and_refine.test_data import generate_single_ubi_data
import c2ImageD11

sizes = [100000, 500000, 2000000]
n_cores = os.cpu_count() or 4

try:
    import ImageD11._cImageD11 as old
    have_f2py = True
except ImportError:
    have_f2py = False

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
