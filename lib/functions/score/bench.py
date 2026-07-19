#!/usr/bin/env python3
"""Benchmark score() -- throughput, threading, f2py baseline."""

from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from score_and_refine.test_data import generate_single_ubi_data
import c2ImageD11

ng = 200000
niter = 30
n_cores = os.cpu_count() or 4

ubi, gv, tol = generate_single_ubi_data(ng)
gv_f32 = gv.astype(np.float32)
gv_soa = gv.T.copy()
gv_soa_f32 = gv_f32.T.copy()

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
