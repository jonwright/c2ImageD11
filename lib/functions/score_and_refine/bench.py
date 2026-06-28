#!/usr/bin/env python3
"""Benchmark score_and_refine — throughput, threading, f2py comparison.

Usage:
    python bench.py                     throughput at 3 sizes
    python bench.py --threads           1T vs nT scaling sweep
    python bench.py --overhead          c2py23 wrapper overhead vs f2py
    python bench.py --sizes 10000 50000 200000 1000000
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, argparse
import numpy as np

DEFAULT_SIZES = [100000, 500000, 2000000]


def gen_data(ng, gv_dtype, seed=42):
    rng = np.random.RandomState(seed)
    return rng.randn(3, 3).astype(np.float64), rng.randn(ng, 3).astype(gv_dtype), 0.05


def time_calls(fn, ubi, gv, tol, n_calls):
    ng = gv.shape[0]
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
        data[ng] = {"f64": gen_data(ng, np.float64), "f32": gen_data(ng, np.float32)}

    print("score_and_refine throughput (%d threads, dispatch via Python API)" % n_cores)
    print("Sizes: %s" % ", ".join(str(s) for s in args.sizes))
    print()
    print("%10s  %8s  %12s  %8s  %12s" % ("ng", "f64_us", "f64_M/s", "f32_us", "f32_M/s"))
    print("-" * 60)
    for ng in args.sizes:
        row = "%10d" % ng
        for dt in ("f64", "f32"):
            ubi, gv, tol = data[ng][dt]
            nc = max(3, int(1e8 / ng))
            us, thr = time_calls(fn, ubi, gv, tol, nc)
            row += "  %8.0f %10.2f" % (us, thr)
        print(row)


def do_threads(args):
    import c2ImageD11

    fn = c2ImageD11.score_and_refine
    n_cores = os.cpu_count() or 4
    sizes = [10000, 25000, 50000, 75000, 100000, 200000, 500000, 1000000]

    print("Threading scaling (%d cores, Python dispatch)" % n_cores)
    print("OMP_MIN_NG = %d" % c2ImageD11.OMP_MIN_NG)
    print()
    print("%8s  %8s  %8s  %6s  %8s  %8s  %6s" %
          ("ng", "f64_1T", "f64_nT", "x", "f32_1T", "f32_nT", "x"))
    print("-" * 65)

    for ng in sizes:
        ubi, gv_f64, tol = gen_data(ng, np.float64)
        gv_f32 = gv_f64.astype(np.float32)
        nc = max(5, int(2e8 / ng))
        row = "%8d" % ng
        for gv in (gv_f64, gv_f32):
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

    us, thr = time_calls(c2ImageD11._score_and_refine_c, ubi, gv, tol, 50000)
    results["c2py raw"] = (us, thr)

    us, thr = time_calls(c2ImageD11.score_and_refine, ubi, gv, tol, 5000)
    results["c2py dispatch"] = (us, thr)

    print("=" * 70)
    print("Wrapper overhead — ng=%d, 1T (Python dispatch)" % NG)
    print("=" * 70)
    print()
    print("  %-22s %8s %8s %8s" % ("Wrapper", "us/call", "M gv/s", "vs f2py"))
    print("  " + "-" * 50)
    ref = results.get("f2py", results["c2py raw"])[1]
    for k, (us, thr) in results.items():
        label = {"f2py": "1.00x", "c2py raw": "%.2fx" % (thr / ref),
                 "c2py dispatch": "%.2fx" % (thr / ref)}.get(k, "")
        print("  %-22s %7.1f us %7.0fM %7s" % (k, us, thr, label))

    if "f2py" in results and "c2py raw" in results:
        raw_oh = results["c2py raw"][0] - results["f2py"][0]
        disp_oh = results["c2py dispatch"][0] - results["c2py raw"][0]
        rthr = results["c2py raw"][1]
        r_us = results["c2py raw"][0]
        d_us = disp_oh
        print()
        print("  c2py wrapper: %.1f us  Python dispatch: %.1f us" % (raw_oh, disp_oh))
        print()
        print("  Extrapolation at ng:")
        for ng in [10000, 100000, 1000000, 50000000]:
            cu = ng / rthr / 1e6 * 1e6
            total = cu + r_us + d_us
            print("    %9d:  %.0f us  (%.0f%% wrap)" %
                  (ng, total, (r_us + d_us) / total * 100))


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
