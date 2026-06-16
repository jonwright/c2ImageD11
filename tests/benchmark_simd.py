#!/usr/bin/env python3
"""Benchmark: SIMD variant comparison for c2ImageD11.

Times each SIMD variant (sse, avx2, avx512) for every dispatched function.
Uses ~1 second of wall-clock time per variant, auto-adapting iteration count.
Reports per-variant ns/call and speedup ratios relative to SSE baseline.

Uses c2py23.perf for C-only time, and time.time() for wall-clock.
"""
from __future__ import print_function

import sys, os, time, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, "/home/worker/c2py23")

import c2ImageD11._cImageD11 as C
from c2py23.perf import read_perf, set_enabled

_TARGET_SECONDS = 1.0  # target wall-clock time per variant


def time_variant(func, args, n_iter):
    """Wall-clock time for n_iter calls. Returns ns/call (mean)."""
    t0 = time.time()
    for _ in range(n_iter):
        func(*args)
    return (time.time() - t0) / n_iter * 1e9


def time_variant_perf(func, perf_ptrs, args, n_iter):
    """Wall-clock + c2py23 C-time for n_iter calls."""
    for ptr in perf_ptrs:
        if ptr:
            set_enabled(ptr, 0)
            set_enabled(ptr, 1)
    t0 = time.time()
    for _ in range(n_iter):
        func(*args)
    wall_ns = (time.time() - t0) / n_iter * 1e9

    cmin_ns = float('inf')
    for ptr in perf_ptrs:
        if ptr:
            stats = read_perf(ptr)
            if stats.get('c_mean_ns'):
                cmin_ns = min(cmin_ns, stats['c_mean_ns'])
    if cmin_ns == float('inf'):
        cmin_ns = 0
    return wall_ns, cmin_ns


def benchmark_func(name, rebind_fn, call_fn, build_args):
    """Benchmark all 3 SIMD variants for one function.

    Returns dict with per-variant wall_ns, c_ns, and speedup vs SSE.
    """
    args = build_args()

    # --- Find iteration count with a warmup call ---
    rebind_fn('sse')
    call_fn(*args)  # single warmup
    t0 = time.time()
    for _ in range(20):
        call_fn(*args)
    dt = (time.time() - t0) / 20
    n_iter = max(1, int(_TARGET_SECONDS / dt))

    # --- Collect per-variant perf pointers ---
    perf_ptrs = []
    for vname in ['sse', 'avx2', 'avx512']:
        for attr in dir(C):
            suffix = '_{}'.format(name)
            if attr.startswith('_perf_') and attr.endswith(suffix + '_' + vname):
                perf_ptrs.append(getattr(C, attr, 0))
    # Also check variant naming: _perf_func__cname
    for vname in ['sse42', 'avx2', 'avx512']:
        for attr in dir(C):
            if attr.startswith('_perf_'):
                parts = attr.split('__')
                if len(parts) == 2 and parts[0] == '_perf_' + name:
                    if parts[1].endswith('_' + vname):
                        perf_ptrs.append(getattr(C, attr, 0))

    results = {}
    variants = ['sse', 'avx2', 'avx512']
    for vname in variants:
        rebind_fn(vname)
        wall_ns, c_ns = time_variant_perf(call_fn, perf_ptrs, args, n_iter)
        results[vname] = {'wall_ns': wall_ns, 'c_ns': c_ns, 'n_iter': n_iter}

    # Reset to auto
    rebind_fn(None)

    # Speedups
    baseline = results['sse']['wall_ns'] or 1
    for vname in variants:
        results[vname]['speedup'] = baseline / (results[vname]['wall_ns'] or 1)
    return results


# ---------------------------------------------------------------------------
# Data builders -- sized to fill ~1 second at SSE speed
# ---------------------------------------------------------------------------

def _score_args():
    n = 200000  # 200k peaks
    ubi = np.random.randn(9)
    gv = np.random.randn(n, 3)
    tol = 0.05
    return [ubi, gv, tol]

def _score_and_refine_args():
    n = 200000
    ubi = np.random.randn(9)
    gv = np.random.randn(n, 3)
    tol = 0.05
    s2 = np.zeros(1, dtype=np.float64)
    return [ubi, gv, tol, s2]

def _score_and_assign_args():
    n = 200000
    ubi = np.random.randn(9)
    gv = np.random.randn(n, 3)
    tol = 0.05
    drlv2 = np.ones(n, dtype=np.float64) * 1e9
    labels = np.zeros(n, dtype=np.int32)
    return [ubi, gv, tol, drlv2, labels, 1]

def _compute_gv_args():
    n = 500000
    xl = np.random.randn(n, 3) * 0.1
    w = np.random.random(n) * 360.0
    t = np.random.randn(3) * 10
    gv = np.zeros((n, 3), dtype=np.float64)
    return [xl, w, 1.0, 0.3, 5.0, 3.0, t, gv]

def _compute_geometry_args():
    n = 500000
    xl = np.random.randn(n, 3) * 0.1
    w = np.random.random(n) * 360.0
    t = np.random.randn(3) * 10
    out = np.zeros((n, 6), dtype=np.float64)
    return [xl, w, 1.0, 0.3, 5.0, 3.0, t, out]

def _compute_xlylzl_args():
    n = 1000000
    s = np.random.randn(n) * 100 + 500
    f = np.random.randn(n) * 100 + 500
    p = np.array([500.0, 500.0, 0.1, 0.1], dtype=np.float64)
    r = np.array([0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.5], dtype=np.float64)
    d = np.array([10.0, 0.0, 0.0], dtype=np.float64)
    out = np.zeros((n, 3), dtype=np.float64)
    return [s, f, p, r, d, out]

def _compute_xlylzl_xpos_args():
    n = 1000000
    s = np.random.randn(n) * 100 + 500
    f = np.random.randn(n) * 100 + 500
    xpos = np.random.randn(n) * 0.1
    p = np.array([500.0, 500.0, 0.1, 0.1], dtype=np.float64)
    r = np.array([0.5, 0.0, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.5], dtype=np.float64)
    d = np.array([10.0, 0.0, 0.0], dtype=np.float64)
    out = np.zeros((n, 3), dtype=np.float64)
    return [s, f, p, r, d, xpos, out]

def _put_incr32_args():
    m = 5000000
    n = 3000000
    data = np.zeros(m, dtype=np.float32)
    ind = np.random.randint(0, m, n, dtype=np.int32)
    vals = np.random.randn(n).astype(np.float32) * 0.01
    return [data, ind, vals, 0]

def _put_incr64_args():
    m = 5000000
    n = 3000000
    data = np.zeros(m, dtype=np.float32)
    ind = np.random.randint(0, m, n, dtype=np.int64)
    vals = np.random.randn(n).astype(np.float32) * 0.01
    return [data, ind, vals, 0]

def _blobproperties_args():
    ns, nf = 1000, 1000  # 1M pixels
    data = np.random.randn(ns, nf).astype(np.float32) + 10.0
    labels = np.random.randint(0, 101, (ns, nf), dtype=np.int32)
    npk = 100
    res = np.zeros((npk, 36), dtype=np.float64)
    return [data, labels, npk, res, 0.0, 0]

def _darksub_args():
    n = 10000000
    data = np.random.randint(0, 65535, n, dtype=np.uint16)
    drk = np.random.randn(n).astype(np.float32)
    img = np.zeros(n, dtype=np.float32)
    return [img, drk, data]

def _darkflm_args():
    n = 10000000
    data = np.random.randint(0, 65535, n, dtype=np.uint16)
    drk = np.random.randn(n).astype(np.float32)
    flm = np.random.randn(n).astype(np.float32) * 0.1 + 1.0
    img = np.zeros(n, dtype=np.float32)
    return [img, drk, flm, data]

def _reorder_f32_args():
    n = 10000000
    data = np.random.randn(n).astype(np.float32)
    adr = np.random.permutation(n).astype(np.uint32)
    out = np.zeros(n, dtype=np.float32)
    return [data, adr, out]

def _reorder_u16_args():
    n = 20000000
    data = np.random.randint(0, 65535, n, dtype=np.uint16)
    adr = np.random.permutation(n).astype(np.uint32)
    out = np.zeros(n, dtype=np.uint16)
    return [data, adr, out]

def _reorderlut_f32_args():
    n = 10000000
    data = np.random.randn(n).astype(np.float32)
    lut = np.random.randint(0, n, n, dtype=np.uint32)
    out = np.zeros(n, dtype=np.float32)
    return [data, lut, out]

def _reorderlut_u16_args():
    n = 20000000
    data = np.random.randint(0, 65535, n, dtype=np.uint16)
    lut = np.random.randint(0, n, n, dtype=np.uint32)
    out = np.zeros(n, dtype=np.uint16)
    return [data, lut, out]


# ---------------------------------------------------------------------------
# Benchmark table
# ---------------------------------------------------------------------------

BENCHMARKS = [
    ("score", C._rebind_score, C.score, _score_args),
    ("score_and_refine", C._rebind_score_and_refine, C.score_and_refine, _score_and_refine_args),
    ("score_and_assign", C._rebind_score_and_assign, C.score_and_assign, _score_and_assign_args),
    ("compute_gv", C._rebind_compute_gv, C.compute_gv, _compute_gv_args),
    ("compute_geometry", C._rebind_compute_geometry, C.compute_geometry, _compute_geometry_args),
    ("compute_xlylzl", C._rebind_compute_xlylzl, C.compute_xlylzl, _compute_xlylzl_args),
    ("compute_xlylzl_xpos_variable", C._rebind_compute_xlylzl_xpos_variable, C.compute_xlylzl_xpos_variable, _compute_xlylzl_xpos_args),
    ("put_incr32", C._rebind_put_incr32, C.put_incr32, _put_incr32_args),
    ("put_incr64", C._rebind_put_incr64, C.put_incr64, _put_incr64_args),
    ("blobproperties", C._rebind_blobproperties, C.blobproperties, _blobproperties_args),
    ("uint16_to_float_darksub", C._rebind_uint16_to_float_darksub, C.uint16_to_float_darksub, _darksub_args),
    ("uint16_to_float_darkflm", C._rebind_uint16_to_float_darkflm, C.uint16_to_float_darkflm, _darkflm_args),
    ("reorder_f32_a32", C._rebind_reorder_f32_a32, C.reorder_f32_a32, _reorder_f32_args),
    ("reorder_u16_a32", C._rebind_reorder_u16_a32, C.reorder_u16_a32, _reorder_u16_args),
    ("reorderlut_f32_a32", C._rebind_reorderlut_f32_a32, C.reorderlut_f32_a32, _reorderlut_f32_args),
    ("reorderlut_u16_a32", C._rebind_reorderlut_u16_a32, C.reorderlut_u16_a32, _reorderlut_u16_args),
]


def main():
    print("=== c2ImageD11 SIMD Variant Benchmark ===")
    print("Target: ~{}s per variant per function\n".format(_TARGET_SECONDS))
    print("{:38s} {:>6s} {:>14s} {:>14s} {:>14s} {:>8s} {:>8s}".format(
        "Function", "Var", "wall_ns/call", "C_ns/call", "speedup", "n_iter", "dt(s)"))
    print("-" * 130)

    for name, rebind_fn, call_fn, build in BENCHMARKS:
        try:
            res = benchmark_func(name, rebind_fn, call_fn, build)
        except Exception as e:
            print("--- {:38s} ERROR: {}".format(name, e))
            continue

        first = True
        for vname in ['sse', 'avx2', 'avx512']:
            r = res[vname]
            if first:
                print("{:38s} {:>6s} {:>14.1f} {:>14.1f} {:>7.2f}x {:>8d} {:>7.2f}".format(
                    name, vname, r['wall_ns'], r['c_ns'],
                    r['speedup'], r['n_iter'],
                    r['wall_ns'] * r['n_iter'] / 1e9))
                first = False
            else:
                print("{:38s} {:>6s} {:>14.1f} {:>14.1f} {:>7.2f}x {:>8d} {:>7.2f}".format(
                    "", vname, r['wall_ns'], r['c_ns'],
                    r['speedup'], r['n_iter'],
                    r['wall_ns'] * r['n_iter'] / 1e9))


if __name__ == "__main__":
    main()
