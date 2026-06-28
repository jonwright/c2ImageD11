from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np


def generate_random_rotations(n, seed=42):
    """Generate n random 3x3 rotation matrices (uniform on SO(3))."""
    rng = np.random.RandomState(seed)
    rotations = []
    for _ in range(n):
        A = rng.randn(3, 3)
        U, _ = np.linalg.qr(A)
        if np.linalg.det(U) < 0:
            U[:, 0] = -U[:, 0]
        rotations.append(U)
    return np.array(rotations)  # shape (n, 3, 3)


def generate_hkl_grid(hmax=8):
    """Generate all integer hkl triples in [-hmax, hmax]."""
    r = np.arange(-hmax, hmax + 1)
    grid = np.array(np.meshgrid(r, r, r)).T.reshape(-1, 3)
    # Remove (0,0,0) which is a trivial match
    mask = ~((grid[:, 0] == 0) & (grid[:, 1] == 0) & (grid[:, 2] == 0))
    return grid[mask]  # shape (n_hkls, 3)


def generate_bench_data(n_ubis=1000, hmax=8, seed=42, tol=0.05):
    """Generate benchmark data for score_and_refine.

    Returns a dict with:
      ubis:     array of shape (n_ubis, 3, 3) -- perfect UBI matrices
      gvs_list: list of (n_hkls, 3) arrays, one per UBI
      tol:      float
      info:     dict with metadata
    """
    B = np.eye(3) / 4.06
    hkls = generate_hkl_grid(hmax)
    n_hkls = len(hkls)
    Us = generate_random_rotations(n_ubis, seed)

    ubis = np.zeros((n_ubis, 3, 3))
    gvs_list = []
    for i in range(n_ubis):
        UB = np.dot(Us[i], B)
        ubis[i] = np.linalg.inv(UB)
        gv = np.dot(hkls, UB.T)  # shape (n_hkls, 3)
        gvs_list.append(gv)

    return {
        "ubis": ubis,
        "gvs_list": gvs_list,
        "hkls": hkls,
        "tol": float(tol),
        "info": {
            "n_ubis": n_ubis,
            "n_hkls_per_ubi": n_hkls,
            "hmax": hmax,
            "seed": seed,
        },
    }


def generate_single_ubi_data(ng, seed=42, tol=0.05):
    """Generate data for a single UBI with args ng g-vectors.

    Returns: (ubi, gv, tol)
    """
    B = np.eye(3) / 4.06
    Us = generate_random_rotations(1, seed)
    UB = np.dot(Us[0], B)
    ubi = np.linalg.inv(UB)

    rng = np.random.RandomState(seed + 1)
    hkls = rng.randint(-8, 9, size=(ng, 3)).astype(np.float64)
    gv = np.dot(hkls, UB.T)

    return ubi, gv, tol
