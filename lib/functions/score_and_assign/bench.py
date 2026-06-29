#!/usr/bin/env python3
"""Benchmark score_and_assign -- 1T vs nT, f64 vs f32, AoS vs SoA.

Usage:
    python bench.py                     default sizes, 1T and nT
    python bench.py --sizes 50000 200000 1000000
    python bench.py --threads           threading scaling sweep
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, argparse, numpy as np

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_SIZES = [50000, 200000, 1000000]


# ── data generation ────────────────────────────────────────────────

def gen_data(n_gv, n_ubis=1000, seed=42, tol=0.05):
    sys.path.insert(0, os.path.join(PROJECT, "lib", "functions", "score_and_refine"))
    from test_data import generate_random_rotations
    rng = np.random.RandomState(seed)
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(n_ubis, seed + 77)
    ubis   = np.zeros((n_ubis, 3, 3))
    UBs    = np.zeros((n_ubis, 3, 3))
    for i in range(n_ubis):
        UBs[i] = np.dot(Us[i], B)
        ubis[i] = np.linalg.inv(UBs[i])
    hkls      = rng.randint(-8, 9, size=(n_gv, 3)).astype(np.float64)
    grain_ids = rng.randint(0, n_ubis, size=n_gv)
    gv = np.empty((n_gv, 3))
    for i in range(n_gv):
        gv[i] = np.dot(hkls[i], UBs[grain_ids[i]].T)
    return ubis, gv, tol, np.full(n_gv, 999.0), np.full(n_gv, -1, dtype=np.int32)


# ── measurement ─────────────────────────────────────────────────────

def measure_one(fn, ubis, gv, tol, drlv2_tpl, labels_tpl, label, nc, n_cores, n_ubis):
    ng = gv.shape[1] if (gv.ndim == 2 and gv.shape[0] == 3) else gv.shape[0]
    import c2ImageD11
    # 1T
    c2ImageD11.cimaged11_omp_set_num_threads(1)
    dv = drlv2_tpl.copy(); lb = labels_tpl.copy()
    t0 = time.perf_counter()
    for i in range(nc):
        fn(ubis[i % n_ubis].copy(), gv, tol, dv, lb, label)
    t1 = time.perf_counter()
    thr_1t = ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0
    # nT
    c2ImageD11.cimaged11_omp_set_num_threads(n_cores)
    dv = drlv2_tpl.copy(); lb = labels_tpl.copy()
    t0 = time.perf_counter()
    for i in range(nc):
        fn(ubis[i % n_ubis].copy(), gv, tol, dv, lb, label)
    t1 = time.perf_counter()
    thr_nt = ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0
    return thr_1t, thr_nt


def measure_f2py(ubis, gv, tol, drlv2_tpl, labels_tpl, nc, n_ubis):
    ng = gv.shape[1] if (gv.ndim == 2 and gv.shape[0] == 3) else gv.shape[0]
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
    except ImportError:
        return 0
    dv = drlv2_tpl.copy(); lb = labels_tpl.copy()
    t0 = time.perf_counter()
    for i in range(nc):
        old.score_and_assign(ubis[i % n_ubis].copy(), gv, tol, dv, lb, 1)
    t1 = time.perf_counter()
    return ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0


# ── main ────────────────────────────────────────────────────────────

def do_default(args):
    import c2ImageD11

    fn = c2ImageD11.score_and_assign
    n_cores  = os.cpu_count() or 4
    N_UBIS   = 1000

    print("score_and_assign  (multi-grain: %d UBIs cycling, tol=0.05, %d cores)" % (N_UBIS, n_cores))
    print()

    # f2py check
    try:
        import ImageD11._cImageD11
        have_f2py = True
    except ImportError:
        have_f2py = False

    header = "%8s" % "ng"
    if have_f2py:
        header += "  %7s" % "f2py"
    header += "  %8s  %8s  %5s  %8s  %8s  %5s  %8s  %8s  %5s  %8s  %8s  %5s" % \
              ("A64_1T", "A64_nT", "spd", "S64_1T", "S64_nT", "spd",
               "A32_1T", "A32_nT", "spd", "S32_1T", "S32_nT", "spd")
    print(header)
    print("-" * len(header))

    for ng in args.sizes:
        ubis, gv_f64, tol, dv_f64, lb = gen_data(ng, N_UBIS)
        gv_f32 = gv_f64.astype(np.float32)
        gv_s64 = gv_f64.T.copy()
        gv_s32 = gv_f64.T.copy().astype(np.float32)
        dv_f32 = np.full(ng, 999.0, dtype=np.float32)
        nc = max(10, int(2e8 / ng))

        f2py_M = 0
        if have_f2py:
            f2py_M = measure_f2py(ubis, gv_f64, tol, dv_f64, lb, nc, N_UBIS)

        if have_f2py:
            row = "%8d  %7.0f" % (ng, f2py_M)
        else:
            row = "%8d" % ng

        for gv, dv in ((gv_f64, dv_f64), (gv_s64, dv_f64),
                       (gv_f32, dv_f32), (gv_s32, dv_f32)):
            thr_1t, thr_nt = measure_one(fn, ubis, gv, tol, dv, lb, 1, nc, n_cores, N_UBIS)
            ratio = "  -" if thr_1t == 0 else "%5.2fx" % (thr_nt / thr_1t)
            row += "  %6.0fM %6.0fM %5s" % (thr_1t, thr_nt, ratio)
        print(row)


def do_threads(args):
    import c2ImageD11

    fn = c2ImageD11.score_and_assign
    n_cores = os.cpu_count() or 4
    sizes = [5000, 10000, 25000, 50000, 75000, 100000, 200000, 500000, 1000000]

    print("Threading scaling (%d cores)" % n_cores)
    print("OMP_MIN_NG = %d" % c2ImageD11.OMP_MIN_NG)
    print()
    header = "%8s  %8s  %8s  %6s  %8s  %8s  %6s  %8s  %8s  %6s  %8s  %8s  %6s" % \
             ("ng", "A_f64_1T", "A_f64_nT", "x", "S_f64_1T", "S_f64_nT", "x",
              "A_f32_1T", "A_f32_nT", "x", "S_f32_1T", "S_f32_nT", "x")
    print(header)
    print("-" * len(header))
    for ng in sizes:
        ubis, gv_f64, tol, dv_f64, lb = gen_data(ng, 1000)
        gv_f32 = gv_f64.astype(np.float32)
        gv_s64 = gv_f64.T.copy()
        gv_s32 = gv_f64.T.copy().astype(np.float32)
        dv_f32 = np.full(ng, 999.0, dtype=np.float32)
        nc = max(5, int(2e8 / ng))
        row = "%8d" % ng
        for gv, dv in ((gv_f64, dv_f64), (gv_s64, dv_f64),
                       (gv_f32, dv_f32), (gv_s32, dv_f32)):
            thr_1t, thr_nt = measure_one(fn, ubis, gv, tol, dv, lb, 1, nc, n_cores, 1000)
            ratio = "  -" if thr_1t == 0 else "%5.2fx" % (thr_nt / thr_1t)
            row += "  %7.0fM %7.0fM %5s" % (thr_1t, thr_nt, ratio)
        print(row)


def main():
    p = argparse.ArgumentParser(description="Benchmark score_and_assign")
    p.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    p.add_argument("--threads", action="store_true",
                   help="1T vs nT threading sweep")
    args = p.parse_args()
    if args.threads:
        return do_threads(args)
    return do_default(args)


if __name__ == "__main__":
    main()
