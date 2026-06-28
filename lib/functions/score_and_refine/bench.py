#!/usr/bin/env python3
"""Benchmark score_and_refine -- throughput, threading, f2py comparison.

Usage:
    python bench.py                     throughput at 3 sizes
    python bench.py --threads           1T vs nT scaling sweep
    python bench.py --overhead          c2py23 wrapper overhead vs f2py
    python bench.py --sizes 10000 50000 200000 1000000
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, argparse, struct, ctypes
import numpy as np

DEFAULT_SIZES = [100000, 500000, 2000000]


def gen_data(ng, gv_dtype, seed=42):
    rng = np.random.RandomState(seed)
    return rng.randn(3, 3).astype(np.float64), rng.randn(ng, 3).astype(gv_dtype), 0.05


def detect_variant(fn, ubi, gv, tol, mod):
    """Return the name of the ISA variant dispatched for a given call."""
    ol_ptrs = {}
    prefix = "_c2py_ol_ptr_score_and_refine__"
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


def time_calls(fn, ubi, gv, tol, n_calls):
    ng = gv.shape[1] if (gv.ndim == 2 and gv.shape[0] == 3) else gv.shape[0]
    for _ in range(3):
        fn(ubi.copy(), gv, tol)
    t0 = time.perf_counter()
    for _ in range(n_calls):
        fn(ubi.copy(), gv, tol)
    t1 = time.perf_counter()
    us = (t1 - t0) / n_calls * 1e6
    thr = ng * n_calls / (t1 - t0) / 1e6
    return us, thr


def do_default(args):
    import c2ImageD11

    fn = c2ImageD11.score_and_refine
    n_cores = os.cpu_count() or 4

    data = {}
    for ng in args.sizes:
        ubi, gv_f64, tol = gen_data(ng, np.float64)
        gv_f32 = gv_f64.astype(np.float32)
        gv_soa_f64 = gv_f64.T.copy()
        gv_soa_f32 = gv_f64.T.copy().astype(np.float32)
        data[ng] = {"AoS_f64": (ubi, gv_f64, tol),
                    "SoA_f64": (ubi, gv_soa_f64, tol),
                    "AoS_f32": (ubi, gv_f32, tol),
                    "SoA_f32": (ubi, gv_soa_f32, tol)}

    print("score_and_refine throughput (%d threads, c2py23 dispatch)" % n_cores)
    print("Sizes: %s" % ", ".join(str(s) for s in args.sizes))

    # Detect which variants are dispatched for each layout
    ng0 = args.sizes[0]
    ubi0, gv_f64_0, tol0 = gen_data(ng0, np.float64)
    mod = c2ImageD11._cImageD11
    variants = {}
    for name, (ubi, gv, tol) in [
            ("AoS_f64", (ubi0, gv_f64_0, tol0)),
            ("SoA_f64", (ubi0, gv_f64_0.T.copy(), tol0)),
            ("AoS_f32", (ubi0, gv_f64_0.astype(np.float32), tol0)),
            ("SoA_f32", (ubi0, gv_f64_0.T.copy().astype(np.float32), tol0))]:
        variants[name] = detect_variant(fn, ubi, gv, tol, mod)
    for name in ("AoS_f64", "SoA_f64", "AoS_f32", "SoA_f32"):
        print("  %s => %s" % (name, variants.get(name, "?")))
    print()
    print("%10s  %8s  %10s  %8s  %10s  %8s  %10s  %8s  %10s" %
          ("ng", "AoS_f64", "M/s", "SoA_f64", "M/s", "AoS_f32", "M/s", "SoA_f32", "M/s"))
    print("-" * 105)
    for ng in args.sizes:
        row = "%10d" % ng
        for layout in ("AoS_f64", "SoA_f64", "AoS_f32", "SoA_f32"):
            ubi, gv, tol = data[ng][layout]
            ng_arr = gv.shape[1] if (gv.ndim == 2 and gv.shape[0] == 3) else gv.shape[0]
            nc = max(3, int(1e8 / ng_arr))
            us, thr = time_calls(fn, ubi, gv, tol, nc)
            row += "  %8.0f %8.0f" % (us, thr)
        print(row)


def do_threads(args):
    import c2ImageD11

    fn = c2ImageD11.score_and_refine
    n_cores = os.cpu_count() or 4
    sizes = [10000, 25000, 50000, 75000, 100000, 200000, 500000, 1000000]

    print("Threading scaling (%d cores, c2py23 dispatch)" % n_cores)
    print("OMP_MIN_NG = %d" % c2ImageD11.OMP_MIN_NG)
    print()
    print("%8s  %8s  %8s  %6s  %8s  %8s  %6s  %8s  %8s  %6s  %8s  %8s  %6s" %
          ("ng", "A_f64_1T","A_f64_nT","x","S_f64_1T","S_f64_nT","x",
           "A_f32_1T","A_f32_nT","x","S_f32_1T","S_f32_nT","x"))
    print("-" * 120)

    for ng in sizes:
        ubi, gv_f64, tol = gen_data(ng, np.float64)
        gv_f32 = gv_f64.astype(np.float32)
        gv_soa_f64 = gv_f64.T.copy()
        gv_soa_f32 = gv_f64.T.copy().astype(np.float32)
        nc = max(5, int(2e8 / ng))
        row = "%8d" % ng
        for gv in (gv_f64, gv_soa_f64, gv_f32, gv_soa_f32):
            thr_1t, thr_nt = 0, 0
            for nthr in (1, n_cores):
                c2ImageD11.cimaged11_omp_set_num_threads(nthr)
                _, thr = time_calls(fn, ubi, gv, tol, nc)
                if nthr == 1:
                    thr_1t = thr
                else:
                    thr_nt = thr
            ratio = thr_nt / thr_1t if thr_1t else 0
            row += "  %7.0fM %7.0fM %5.2fx" % (thr_1t, thr_nt, ratio)
        print(row)


def do_overhead():
    import c2ImageD11

    NG = 10000
    ubi, gv, tol = gen_data(NG, np.float64)
    c2ImageD11.cimaged11_omp_set_num_threads(1)

    results = {}

    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
        us, thr = time_calls(old.score_and_refine, ubi, gv, tol, 50000)
        results["f2py"] = (us, thr)
    except ImportError:
        pass

    us, thr = time_calls(c2ImageD11.score_and_refine, ubi, gv, tol, 50000)
    results["c2py"] = (us, thr)

    print("=" * 70)
    print("Wrapper overhead -- ng=%d, 1T (c2py23 dispatch)" % NG)
    print("=" * 70)
    print()
    print("  %-22s %8s %8s %8s" % ("Wrapper", "us/call", "M gv/s", "vs f2py"))
    print("  " + "-" * 50)
    ref = results.get("f2py", results["c2py"])[1]
    for k, (us, thr) in results.items():
        label = {"f2py": "1.00x", "c2py": "%.2fx" % (thr / ref)}.get(k, "")
        print("  %-22s %7.1f us %7.0fM %7s" % (k, us, thr, label))

    if "f2py" in results and "c2py" in results:
        c2py_oh = results["c2py"][0] - results["f2py"][0]
        rthr = results["c2py"][1]
        r_us = results["c2py"][0]
        print()
        print("  c2py overhead: %.1f us" % c2py_oh)
        print()

    print("  Extrapolation at ng:")
    for ng in [10000, 100000, 1000000, 50000000]:
        cu = ng / rthr / 1e6 * 1e6
        total = cu + r_us
        print("    %9d:  %.0f us  (%.0f%% overhead)" %
              (ng, total, r_us / total * 100))


def main():
    p = argparse.ArgumentParser(description="Benchmark score_and_refine")
    p.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    p.add_argument("--threads", action="store_true",
                   help="1T vs nT threading sweep")
    p.add_argument("--overhead", action="store_true",
                   help="wrapper overhead vs f2py")
    args = p.parse_args()

    if args.threads:
        return do_threads(args)
    if args.overhead:
        return do_overhead()
    return do_default(args)


if __name__ == "__main__":
    main()
