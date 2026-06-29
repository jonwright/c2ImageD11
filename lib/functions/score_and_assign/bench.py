#!/usr/bin/env python3
"""Benchmark score_and_assign -- variant-level timing, transposed output.

Runs each layoutxtype combo at multiple problem sizes, detects the
dispatched ISA variant, and prints a table with rows per variant.

Usage:
    python bench.py                     default sizes
    python bench.py --sizes 50000 200000 1000000
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, argparse, struct, numpy as np

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
DEFAULT_SIZES = [50000, 200000, 1000000]


# --- data ---

def gen_data(ng, n_ubis=1000, seed=42, tol=0.05):
    sys.path.insert(0, os.path.join(PROJECT, "lib", "functions", "score_and_refine"))
    from test_data import generate_random_rotations
    rng = np.random.RandomState(seed)
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(n_ubis, seed + 77)
    ubis = np.zeros((n_ubis, 3, 3))
    UBs  = np.zeros((n_ubis, 3, 3))
    for i in range(n_ubis):
        UBs[i] = np.dot(Us[i], B)
        ubis[i] = np.linalg.inv(UBs[i])
    hkls      = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    grain_ids = rng.randint(0, n_ubis, size=ng)
    gv = np.empty((ng, 3))
    for i in range(ng):
        gv[i] = np.dot(hkls[i], UBs[grain_ids[i]].T)
    return ubis, gv, tol, np.full(ng, 999.0), np.full(ng, -1, dtype=np.int32)


# -- measurement -----------------------------------------------------

def detect_and_measure(fn, mod, ubis, ubi, gv, tol, drlv2, labels, nc, n_cores, n_ubis, ng):
    """Return (variant_name, thr_1t, thr_nt)."""
    import c2ImageD11

    # Reset all perf counters
    for attr in sorted(dir(mod)):
        if attr.startswith('_c2py_ol_ptr_score_and_assign__'):
            mod._c2py_perf_reset(int(getattr(mod, attr)))

    mod._c2py_perf_set_enabled(1)
    fn(ubi.copy(), gv, tol, drlv2.copy(), labels.copy(), 1)
    mod._c2py_perf_set_enabled(0)

    variant = 'unknown'
    for attr in sorted(dir(mod)):
        if attr.startswith('_c2py_ol_ptr_score_and_assign__'):
            ptr = int(getattr(mod, attr))
            buf = bytearray(128)
            mod._c2py_perf_read(ptr, buf)
            if struct.unpack_from('Q', buf)[0] > 0:
                variant = attr.replace('_c2py_ol_ptr_', '')
                break

    # Warmup
    dv_w = drlv2.copy(); lb_w = labels.copy()
    for _ in range(5):
        fn(ubi.copy(), gv, tol, dv_w, lb_w, 1)

    # 1T
    c2ImageD11.cimaged11_omp_set_num_threads(1)
    dv_1 = drlv2.copy(); lb_1 = labels.copy()
    t0 = time.perf_counter()
    for i in range(nc):
        fn(ubis[i % n_ubis].copy(), gv, tol, dv_1, lb_1, 1)
    t1 = time.perf_counter()
    thr_1t = ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0

    # nT
    c2ImageD11.cimaged11_omp_set_num_threads(n_cores)
    dv_n = drlv2.copy(); lb_n = labels.copy()
    t0 = time.perf_counter()
    for i in range(nc):
        fn(ubis[i % n_ubis].copy(), gv, tol, dv_n, lb_n, 1)
    t1 = time.perf_counter()
    thr_nt = ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0

    return variant, thr_1t, thr_nt


def measure_f2py(ng, n_ubis, ubis, gv, tol, drlv2, labels, nc):
    try:
        import ImageD11._cImageD11 as old
        old.cimaged11_omp_set_num_threads(1)
    except ImportError:
        return 0
    dv = drlv2.copy(); lb = labels.copy()
    for _ in range(5):
        old.score_and_assign(ubis[0].copy(), gv, tol, dv, lb, 1)
    dv = drlv2.copy(); lb = labels.copy()
    t0 = time.perf_counter()
    for i in range(nc):
        old.score_and_assign(ubis[i % n_ubis].copy(), gv, tol, dv, lb, 1)
    t1 = time.perf_counter()
    return ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0


# -- main ------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Benchmark score_and_assign")
    p.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    args = p.parse_args()

    import c2ImageD11
    fn = c2ImageD11.score_and_assign
    mod = c2ImageD11._cImageD11
    n_cores = os.cpu_count() or 4
    N_UBIS  = 1000

    # f2py reference (f64 AoS only, 1T)
    f2py_ref = {}
    for ng in args.sizes:
        ubis, gv_f64, tol, dv_f64, lb = gen_data(ng, N_UBIS)
        nc = max(5, int(2e8 / ng))
        f2py_ref[ng] = measure_f2py(ng, N_UBIS, ubis, gv_f64, tol, dv_f64, lb, nc)

    # -- Build results --
    rows = []  # list of (layout, variant, ng, thr_1t, thr_nt, vf2py_1t, vf2py_nt, n_thr)

    for ng in args.sizes:
        ubis, gv_f64, tol, dv_f64, lb = gen_data(ng, N_UBIS)
        gv_f32  = gv_f64.astype(np.float32)
        gv_s64  = gv_f64.T.copy()
        gv_s32  = gv_f64.T.copy().astype(np.float32)
        dv_f32  = np.full(ng, 999.0, dtype=np.float32)
        nc = max(5, int(2e8 / ng))

        for label, gv, dv in [
                ("AoS_f64", gv_f64, dv_f64),
                ("SoA_f64", gv_s64,  dv_f64),
                ("AoS_f32", gv_f32,  dv_f32),
                ("SoA_f32", gv_s32,  dv_f32)]:
            variant, thr_1t, thr_nt = detect_and_measure(
                fn, mod, ubis, ubis[0], gv, tol, dv, lb, nc, n_cores, N_UBIS, ng)

            vf2py_1t = thr_1t / f2py_ref[ng] if f2py_ref[ng] > 0 else 0
            vf2py_nt = thr_nt / f2py_ref[ng] if f2py_ref[ng] > 0 else 0

            rows.append((label, variant, ng, thr_1t, thr_nt, vf2py_1t, vf2py_nt, n_cores))

    # -- Print table --
    print("{:>8s}  {:>8s}  {:>9s}  {:>9s}  {:>6s}  {:>6s}  {:>4s}  {:>8s}  {:s}".format(
        "ng", "layout", "1T_Mgv/s", "nT_Mgv/s", "xf2py1T", "xf2pynT", "nthr", "gve", "variant"))
    print("-" * 140)

    for layout, variant, ng, thr_1t, thr_nt, vf2py_1t, vf2py_nt, n_thr in rows:
        shape = "({},{})".format(ng, 3) if "AoS" in layout else "(3,{})".format(ng)
        # variant looks like "score_and_assign__score_and_assign_f64_avx512_v2"
        # strip the boilerplate prefix
        short_variant = variant.split("__")[-1] if "__" in variant else variant
        short_variant = short_variant.replace("score_and_assign_", "", 1)
        print("{:>8d}  {:>8s}  {:>9.0f}  {:>9.0f}  {:>5.1f}x  {:>5.1f}x  {:>4d}  {:>8s}  {:s}".format(
            ng, layout, thr_1t, thr_nt, vf2py_1t, vf2py_nt, n_thr, shape, short_variant))

    print()
    print("f2py reference (f64 AoS, 1T):")
    for ng in args.sizes:
        print("  ng={:>8d}  {:>7.0f}M gv/s".format(ng, f2py_ref[ng]))


if __name__ == "__main__":
    main()
