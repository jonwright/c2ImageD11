#!/usr/bin/env python3
"""Benchmark score() -- per-ISA variant comparison, threading, f2py baseline.

Uses c2py23 CPU feature flags (c2py_amd64_avx512f, etc.) to force
dispatch to a specific ISA level.  Saves/restores original flags.
"""

from __future__ import absolute_import, division, print_function, unicode_literals
import os, sys, time, ctypes, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from score_and_refine.test_data import generate_single_ubi_data
import c2ImageD11

ng = 200000
niter = 30
n_cores = os.cpu_count() or 4

# Load the .so/.pyd for CPU flag access
so = c2ImageD11._cImageD11.__file__
lib = ctypes.CDLL(so)

def get_flag(name):
    return ctypes.c_int.in_dll(lib, name).value

def set_flag(name, val):
    ctypes.c_int.in_dll(lib, name).value = val

# Save original flags
orig_avx512 = get_flag("c2py_amd64_avx512f")
orig_avx2   = get_flag("c2py_amd64_avx2")
orig_sse41  = get_flag("c2py_amd64_sse4_1")

ubi, gv, tol = generate_single_ubi_data(ng)
gv_f32 = gv.astype(np.float32)
gv_soa = gv.T.copy()
gv_soa_f32 = gv_f32.T.copy()

def measure(fn, ubi, gv, tol):
    c2ImageD11.cimaged11_omp_set_num_threads(1)
    for _ in range(5): fn(ubi.copy(), gv, tol)
    t0 = time.perf_counter()
    for _ in range(niter): fn(ubi.copy(), gv, tol)
    t1 = time.perf_counter()
    return ng * niter / (t1 - t0) / 1e6

def measure_nT(fn, ubi, gv, tol):
    c2ImageD11.cimaged11_omp_set_num_threads(n_cores)
    for _ in range(5): fn(ubi.copy(), gv, tol)
    t0 = time.perf_counter()
    for _ in range(niter): fn(ubi.copy(), gv, tol)
    t1 = time.perf_counter()
    return ng * niter / (t1 - t0) / 1e6

# ISA configs: disable higher ISAs to force dispatch to a specific level
configs = [
    ("AVX-512", {"avx512f": 1, "avx2": 1, "sse4_1": 1}),
    ("AVX2",    {"avx512f": 0, "avx2": 1, "sse4_1": 1}),
    ("SSE2",    {"avx512f": 0, "avx2": 0, "sse4_1": 0}),
]

# f2py baseline
try:
    import ImageD11._cImageD11 as old
    old.cimaged11_omp_set_num_threads(1)
    f2py_1t = measure(old.score, ubi, gv, tol)
    have_f2py = True
except ImportError:
    have_f2py = False
    f2py_1t = 0

print("score() ISA variant comparison (ng=%d, 1T)" % ng)
if have_f2py:
    print("f2py baseline: %.0f M/s" % f2py_1t)
print()
print("%-10s  %10s  %10s  %10s  %10s" % ("ISA", "AoS_f64", "SoA_f64", "AoS_f32", "SoA_f32"))
print("-" * 55)

for label, flags in configs:
    set_flag("c2py_amd64_avx512f", flags["avx512f"])
    set_flag("c2py_amd64_avx2",    flags["avx2"])
    set_flag("c2py_amd64_sse4_1",  flags["sse4_1"])
    row = "%-10s" % label
    for gv_arr in [gv, gv_soa, gv_f32, gv_soa_f32]:
        if label == "SSE2" and (gv_arr is gv_soa or gv_arr is gv_soa_f32):
            row += "  %10s" % "n/a"
        else:
            try:
                thr = measure(c2ImageD11.score, ubi, gv_arr, tol)
            except SystemError:
                thr = 0
            row += "  %8.0fM" % thr
    print(row)

# Threading for best variant (AVX-512, all flags on)
set_flag("c2py_amd64_avx512f", orig_avx512)
set_flag("c2py_amd64_avx2",    orig_avx2)
set_flag("c2py_amd64_sse4_1",  orig_sse41)

print()
print("%-10s  %10s  %10s  %10s  %10s" % ("nT (%d)" % n_cores, "AoS_f64", "SoA_f64", "AoS_f32", "SoA_f32"))
print("-" * 55)
row = "%-10s" % ("nT (%d)" % n_cores)
for gv_arr in [gv, gv_soa, gv_f32, gv_soa_f32]:
    thr = measure_nT(c2ImageD11.score, ubi, gv_arr, tol)
    row += "  %8.0fM" % thr
print(row)

# Restore flags
set_flag("c2py_amd64_avx512f", orig_avx512)
set_flag("c2py_amd64_avx2",    orig_avx2)
set_flag("c2py_amd64_sse4_1",  orig_sse41)
