#!/usr/bin/env python3
"""Benchmark: c2py23 vs f2py timing comparison for c2ImageD11 functions.

Compares per-function runtime between:
  - ImageD11._cImageD11 (f2py-based)
  - c2ImageD11._cImageD11 (c2py23-based)

Uses c2py23.perf for c2py23 side (C time + wrapper overhead in ns).
Uses timeit for f2py side.
"""

from __future__ import print_function

import sys, os, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, "/home/worker/c2py23")

import ImageD11._cImageD11 as OLD
import c2ImageD11._cImageD11 as NEW
from c2py23.perf import read_perf, set_enabled


def time_f2py(fn, args, n=50):
    t0 = time.time()
    for _ in range(n):
        fn(*args)
    t1 = time.time()
    return (t1 - t0) / n * 1e9  # seconds -> ns


def benchmark(name, old_fn, args_builder, n_calls=200):
    """Benchmark one function."""
    args = args_builder()
    enabled_ptr = getattr(NEW, "_c2py_timing_enabled", None)
    if enabled_ptr:
        set_enabled(enabled_ptr, 1)

    # Warmup
    for _ in range(10):
        old_fn(*args)
    for _ in range(10):
        getattr(NEW, name)(*args)

    # c2py23 timing
    perf_name = "_perf_" + name
    if hasattr(NEW, perf_name):
        set_enabled(enabled_ptr, 1)
        for _ in range(n_calls):
            getattr(NEW, name)(*args)
        set_enabled(enabled_ptr, 0)
        stats = read_perf(getattr(NEW, perf_name))
        c2py_c_ns = stats["c_mean_ns"]
        c2py_wrap_ns = stats["wrap_mean_ns"]
    else:
        c2py_c_ns = 0
        c2py_wrap_ns = 0

    # f2py timing
    f2py_ns = time_f2py(old_fn, args, n=n_calls)

    if c2py_c_ns > 0:
        speedup = f2py_ns / (c2py_c_ns + c2py_wrap_ns)
    else:
        speedup = 0

    return {
        "name": name,
        "c2py_C_ns": c2py_c_ns,
        "c2py_wrap_ns": c2py_wrap_ns,
        "c2py_total_ns": c2py_c_ns + c2py_wrap_ns,
        "f2py_ns": f2py_ns,
        "speedup": speedup,
    }


def build_score_args():
    np.random.seed(42)
    ubi = np.random.randn(3, 3)
    gv = np.random.randn(500, 3)
    tol = 0.1
    return [ubi, gv, tol]


def build_closest_args():
    np.random.seed(42)
    x = np.sort(np.random.random(500))
    v = np.random.random(100)
    ibest = np.zeros(1, dtype=np.int32)
    best = np.zeros(1, dtype=np.float64)
    # f2py returns tuple (ibest, best)
    return [x, v, ibest, best]


def build_array_stats_args():
    np.random.seed(42)
    img = np.random.randn(100000).astype(np.float32)
    mn = np.zeros(1, dtype=np.float32)
    mx = np.zeros(1, dtype=np.float32)
    me = np.zeros(1, dtype=np.float32)
    va = np.zeros(1, dtype=np.float32)
    return [img, mn, mx, me, va]


def build_misori_args():
    np.random.seed(42)
    u1 = np.random.randn(3, 3)
    u2 = np.random.randn(3, 3)
    return [u1, u2]


def build_compute_geometry_args():
    np.random.seed(42)
    n = 200
    xl = np.random.randn(n, 3) * 0.1
    w = np.random.random(n) * 360
    t = np.random.randn(3) * 10
    out = np.zeros((n, 6))
    return [xl, w, 1.0, 0.3, 5.0, 3.0, t, out]


def build_connectedpixels_args():
    np.random.seed(42)
    data = np.random.randn(100, 100).astype(np.float32)
    labels = np.zeros((100, 100), dtype=np.int32)
    return [data, labels, 0.5, 0, 1]


def build_uint16_darksub_args():
    np.random.seed(42)
    n = 50000
    data = np.random.randint(0, 65535, n, dtype=np.uint16)
    drk = np.random.randn(n).astype(np.float32)
    img = np.zeros(n, dtype=np.float32)
    return [img, drk, data]


def build_tosparse_args():
    np.random.seed(42)
    ns, nf = 100, 100
    img = np.random.randn(ns, nf).astype(np.float32) + 5
    msk = np.ones((ns, nf), dtype=np.uint8)
    return [img, msk,
            np.zeros((ns, nf), dtype=np.uint16),
            np.zeros((ns, nf), dtype=np.uint16),
            np.zeros((ns, nf), dtype=np.float32), 3.0]


# Functions to benchmark: (name, old_fn, args_builder)
BENCHMARKS = [
    ("score", lambda *a: OLD.score(*a[:3]), build_score_args),
    ("closest", lambda *a: OLD.closest(*a[:2]), build_closest_args),
    ("array_stats", lambda *a: OLD.array_stats(*a[:1]), build_array_stats_args),
    ("misori_cubic", OLD.misori_cubic, build_misori_args),
    ("compute_geometry", OLD.compute_geometry, build_compute_geometry_args),
    ("connectedpixels", OLD.connectedpixels, build_connectedpixels_args),
    ("uint16_to_float_darksub", OLD.uint16_to_float_darksub, build_uint16_darksub_args),
    ("tosparse_f32", OLD.tosparse_f32, build_tosparse_args),
]


def main():
    print("{:35s} {:>10s} {:>10s} {:>10s} {:>10s} {:>8s}".format(
        "Function", "c2py_C_ns", "c2py_wrap", "c2py_total", "f2py_ns", "speedup"))
    print("-" * 90)

    for name, old_fn, builder in BENCHMARKS:
        result = benchmark(name, old_fn, builder)
        if result["c2py_C_ns"] == 0:
            print("{:35s} {:>10s} {:>10s} {:>10s} {:>10s} {:>8s}".format(
                name, "-", "-", "-", "-", "-"))
            continue
        print("{:35s} {:>10.0f} {:>10.0f} {:>10.0f} {:>10.0f} {:>7.2f}x".format(
            result["name"],
            result["c2py_C_ns"],
            result["c2py_wrap_ns"],
            result["c2py_total_ns"],
            result["f2py_ns"],
            result["speedup"]))


if __name__ == "__main__":
    main()
