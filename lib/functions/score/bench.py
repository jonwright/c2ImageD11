#!/usr/bin/env python3
"""Benchmark score() -- throughput and threading scaling."""
from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from score_and_refine.test_data import generate_single_ubi_data
import c2ImageD11

sizes = [100000, 500000, 2000000]
n_cores = os.cpu_count() or 4

for ng in sizes:
    ubi, gv, tol = generate_single_ubi_data(ng)
    gv_f32 = gv.astype(np.float32)
    
    for nthr in [1, n_cores]:
        c2ImageD11.cimaged11_omp_set_num_threads(nthr)
        nc = max(5, int(2e8 // ng))
        fn = c2ImageD11.score
        for _ in range(3): fn(ubi.copy(), gv, tol)
        t0 = time.perf_counter()
        for _ in range(nc): fn(ubi.copy(), gv, tol)
        t1 = time.perf_counter()
        thr = ng * nc / (t1 - t0) / 1e6
        sys.stdout.write("ng=%7d  f64_%dT=%7.0fM/s" % (ng, nthr, thr))
        
        c2ImageD11.cimaged11_omp_set_num_threads(nthr)
        fn = c2ImageD11.score
        for _ in range(3): fn(ubi.copy(), gv_f32, tol)
        t0 = time.perf_counter()
        for _ in range(nc): fn(ubi.copy(), gv_f32, tol)
        t1 = time.perf_counter()
        thr = ng * nc / (t1 - t0) / 1e6
        sys.stdout.write("  f32_%dT=%7.0fM/s\n" % (nthr, thr))
    print()
