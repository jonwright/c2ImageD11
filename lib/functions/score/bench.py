#!/usr/bin/env python3
"""Benchmark score() — all ISA tiers via runtime flag toggling."""

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, time, argparse, struct, numpy as np

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
N_UBIS  = 1000
DEFAULT_SIZES = [50000, 200000]


def gen_data(ng, seed=42, tol=0.05):
    sys.path.insert(0, os.path.join(PROJECT, "lib", "functions", "score_and_refine"))
    from test_data import generate_random_rotations
    rng = np.random.RandomState(seed)
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(N_UBIS, seed + 77)
    ubis = np.zeros((N_UBIS, 3, 3))
    for i in range(N_UBIS):
        ubis[i] = np.linalg.inv(np.dot(Us[i], B))
    hkls = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    grain_ids = rng.randint(0, N_UBIS, size=ng)
    gv = np.empty((ng, 3))
    for i in range(ng):
        gv[i] = np.dot(hkls[i], np.dot(Us[grain_ids[i]], B).T)
    return ubis, gv, tol


def measure(fn, mod, ubis, gv, tol, ng, nc, n_threads, n_ubis):
    import c2ImageD11
    for a in sorted(dir(mod)):
        if "_c2py_ol_ptr_score__" in a:
            mod._c2py_perf_reset(int(getattr(mod, a)))
    mod._c2py_perf_set_enabled(1)
    fn(ubis[0].copy(), gv, tol)
    mod._c2py_perf_set_enabled(0)
    variant = "none"
    for a in sorted(dir(mod)):
        if "_c2py_ol_ptr_score__" in a:
            ptr = int(getattr(mod, a))
            buf = bytearray(128)
            mod._c2py_perf_read(ptr, buf)
            if struct.unpack_from("Q", buf)[0] > 0:
                variant = a.replace("_c2py_ol_ptr_score__", "").replace("score_", "")
                break
    c2ImageD11.cimaged11_omp_set_num_threads(n_threads)
    for _ in range(5): fn(ubis[0].copy(), gv, tol)
    t0 = time.perf_counter()
    for i in range(nc):
        fn(ubis[i % n_ubis].copy(), gv, tol)
    t1 = time.perf_counter()
    thr = ng * nc / (t1 - t0) / 1e6 if t1 > t0 else 0
    return variant, thr


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", type=int, nargs="+", default=DEFAULT_SIZES)
    args = p.parse_args()

    import c2ImageD11
    fn = c2ImageD11.score
    mod = c2ImageD11._cImageD11

    # f2py
    f2py = {}
    for ng in args.sizes:
        ubis, gv, tol = gen_data(ng)
        nc = max(5, int(2e8 / ng))
        try:
            import ImageD11._cImageD11 as old
            old.cimaged11_omp_set_num_threads(1)
            for _ in range(5): old.score(ubis[0].copy(), gv, tol)
            t0 = time.perf_counter()
            for i in range(nc): old.score(ubis[i % N_UBIS].copy(), gv, tol)
            t1 = time.perf_counter()
            f2py[ng] = ng * nc / (t1 - t0) / 1e6
            print("f2py ng={:>8d} {:>7.0f}M".format(ng, f2py[ng]))
        except ImportError:
            f2py[ng] = 0
            print("f2py ng={:>8d} (not found)".format(ng))

    header = "{:>8s}  {:>5s}  {:>8s}  {:>8s}  {:>9s}  {:>6s}  {:>4s}  {:s}".format(
        "ng", "nthr", "tier", "layout", "M_gv/s", "xf2py", "gve", "variant")
    print()
    print(header)
    print("-" * 110)

    for tier, avx512_v, avx2_v in [("avx512", 1, 1), ("avx2", 0, 1), ("baseline", 0, 0)]:
        mod._c2py_set_avx512f(avx512_v)
        mod._c2py_set_avx2(avx2_v)

        for ng in args.sizes:
            ubis, gv_f64, tol = gen_data(ng)
            nc = max(5, int(2e8 / ng))
            gv_f32 = gv_f64.astype(np.float32)
            gv_s64 = gv_f64.T.copy()
            gv_s32 = gv_f64.T.copy().astype(np.float32)
            for nthr in [1, 4]:
                for label, gv in [("AoS_f64", gv_f64), ("SoA_f64", gv_s64),
                                   ("AoS_f32", gv_f32), ("SoA_f32", gv_s32)]:
                    try:
                        variant, thr = measure(fn, mod, ubis, gv, tol, ng, nc, nthr, N_UBIS)
                    except (ValueError, SystemError):
                        print("{:>8d}  {:>5d}  {:>8s}  {:>8s}  {:>9s}  {:>6s}  {:>4s}  {:s}".format(
                            ng, nthr, tier, label, "-", "-", "-", "no_match"), flush=True)
                        continue
                    fp = f2py.get(ng, 0)
                    v1 = thr / fp if fp > 0 else 0
                    shape = "({},{})".format(ng, 3) if "AoS" in label else "(3,{})".format(ng)
                    print("{:>8d}  {:>5d}  {:>8s}  {:>8s}  {:>9.0f}  {:>5.1f}x  {:>4s}  {:s}".format(
                        ng, nthr, tier, label, thr, v1, shape, variant), flush=True)

    mod._c2py_set_avx512f(1)
    mod._c2py_set_avx2(1)


if __name__ == "__main__":
    main()
