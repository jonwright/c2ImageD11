#!/usr/bin/env python3
"""Benchmark score_and_refine -- throughput, threading, f2py comparison.

Usage:
    python bench.py                     throughput, 1T vs nT, f2py baseline
    python bench.py --threads           detailed 1T vs nT scaling sweep
    python bench.py --overhead          c2py23 wrapper overhead vs f2py
    python bench.py --sizes 10000 50000 200000 1000000
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, argparse, struct, ctypes
import numpy as np

DEFAULT_SIZES = [100000, 500000, 2000000]


def gen_data(ng, gv_dtype, seed=42):
    """Generate realistic crystallographic data -- g-vectors from random UBI.
    This ensures the inner loop body executes (peaks match), making
    threading meaningful."""
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    from test_data import generate_single_ubi_data
    ubi, gv, tol = generate_single_ubi_data(ng, seed)
    # tol from generate_single_ubi_data is 0.05 which is good
    if gv_dtype == np.float32:
        gv = gv.astype(np.float32)
    return ubi, gv, tol


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
    thr = ng * n_calls / (t1 - t0) / 1e6
    return thr


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

    # Detect variants
    ng0 = args.sizes[0]
    ubi0, gv_f64_0, tol0 = gen_data(ng0, np.float64)
    mod = c2ImageD11._cImageD11
    variants = {}
    for name, (ub, gv, t) in [
            ("AoS_f64", (ubi0, gv_f64_0, tol0)),
            ("SoA_f64", (ubi0, gv_f64_0.T.copy(), tol0)),
            ("AoS_f32", (ubi0, gv_f64_0.astype(np.float32), tol0)),
            ("SoA_f32", (ubi0, gv_f64_0.T.copy().astype(np.float32), tol0))]:
        variants[name] = detect_variant(fn, ub, gv, t, mod)

    # Try f2py
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
        have_f2py = True
    except ImportError:
        have_f2py = False

    print("score_and_refine throughput")
    print("Sizes: %s, %d cores" % (", ".join(str(s) for s in args.sizes), n_cores))
    print()
    for name in ("AoS_f64", "SoA_f64", "AoS_f32", "SoA_f32"):
        print("  %s => %s" % (name, variants.get(name, "?")))
    print()

    print("%8s  %6s  %8s  %8s  %5s  %8s  %8s  %5s  %8s  %8s  %5s  %8s  %8s  %5s" %
          ("ng", "f2py_M", "A64_1T", "A64_nT", "x", "S64_1T", "S64_nT", "x",
           "A32_1T", "A32_nT", "x", "S32_1T", "S32_nT", "x"))
    print("-" * 130)

    for ng in args.sizes:
        ubi = data[ng]["AoS_f64"][0]
        nc = max(5, int(2e8 / ng))

        # f2py baseline (f64 AoS only, 1 thread)
        f2py_M = 0
        if have_f2py:
            old.cimaged11_omp_set_num_threads(1)
            f2py_M = time_calls(old.score_and_refine, ubi, data[ng]["AoS_f64"][1], 0.05, nc)

        row = "%8d  %6.0f" % (ng, f2py_M)

        # c2py: 1T and nT for each layout
        for layout in ("AoS_f64", "SoA_f64", "AoS_f32", "SoA_f32"):
            _, gv, tol = data[ng][layout]
            thr_1t, thr_nt = 0, 0
            c2ImageD11.cimaged11_omp_set_num_threads(1)
            thr_1t = time_calls(fn, ubi, gv, tol, nc)
            c2ImageD11.cimaged11_omp_set_num_threads(n_cores)
            thr_nt = time_calls(fn, ubi, gv, tol, nc)
            ratio = " -" if thr_1t == 0 else "%5.2fx" % (thr_nt / thr_1t)
            row += "  %6.0fM %6.0fM %5s" % (thr_1t, thr_nt, ratio)
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
            c2ImageD11.cimaged11_omp_set_num_threads(1)
            thr_1t = time_calls(fn, ubi, gv, tol, nc)
            c2ImageD11.cimaged11_omp_set_num_threads(n_cores)
            thr_nt = time_calls(fn, ubi, gv, tol, nc)
            ratio = " -" if thr_1t == 0 else "%5.2fx" % (thr_nt / thr_1t)
            row += "  %7.0fM %7.0fM %5s" % (thr_1t, thr_nt, ratio)
        print(row)


def do_overhead():
    import c2ImageD11

    NG = 10000
    ubi, gv, tol = gen_data(NG, np.float64)
    c2ImageD11.cimaged11_omp_set_num_threads(1)
    nc = 50000

    results = {}
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
        thr = time_calls(old.score_and_refine, ubi, gv, tol, nc)
        results["f2py"] = thr
    except ImportError:
        pass

    thr = time_calls(c2ImageD11.score_and_refine, ubi, gv, tol, nc)
    results["c2py"] = thr

    print("=" * 70)
    print("Wrapper overhead -- ng=%d, 1T (c2py23 dispatch)" % NG)
    print("=" * 70)
    print()
    print("  %-22s %8s %8s" % ("Wrapper", "M gv/s", "vs f2py"))
    print("  " + "-" * 40)
    ref = results.get("f2py", results["c2py"])
    for k, thr in results.items():
        label = "1.00x" if k == "f2py" else ("%.2fx" % (thr / ref))
        print("  %-22s %7.0fM %7s" % (k, thr, label))

    if "f2py" in results and "c2py" in results:
        c2py_oh = NG / results["c2py"] / 1e6 * 1e6 - NG / results["f2py"] / 1e6 * 1e6
        rthr = results["c2py"]
        print()
        print("  Extrapolation at ng:")
        for ng in [10000, 100000, 1000000, 50000000]:
            cu = ng / rthr / 1e6 * 1e6
            print("    %9d:  %.0f us  (%.0f%% overhead)" %
                  (ng, cu + c2py_oh, c2py_oh / (cu + c2py_oh) * 100))


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
