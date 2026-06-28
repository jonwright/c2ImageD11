"""Test that type mismatches in buffer arguments are properly rejected."""
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
import numpy as np
import c2ImageD11


def test_score_f64_only():
    """score() with f64 gv works."""
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randn(10, 3).astype(np.float64)
    n = c2ImageD11.score(ubi, gv, 0.5)
    assert isinstance(n, (int, np.integer))
    assert n >= 0


def test_score_f32_works():
    """score() with f32 gv works (via score_f32 baseline)."""
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randn(10, 3).astype(np.float32)
    n = c2ImageD11.score(ubi, gv, 0.5)
    assert isinstance(n, (int, np.integer))
    assert n >= 0


def test_score_and_refine_f64_works():
    """score_and_refine() with f64 gv works."""
    ubi = np.random.randn(3, 3).astype(np.float64)
    gv = np.random.randn(10, 3).astype(np.float64)
    n, s = c2ImageD11.score_and_refine(ubi, gv, 0.5)
    assert isinstance(n, (int, np.integer))


def test_score_and_refine_f32_works():
    """score_and_refine() with f32 gv works."""
    ubi = np.random.randn(3, 3).astype(np.float64)
    gv = np.random.randn(10, 3).astype(np.float32)
    n, s = c2ImageD11.score_and_refine(ubi, gv, 0.5)
    assert isinstance(n, (int, np.integer))


def test_score_rejects_int_gv():
    """score() given int gv raises an error (no matching overload)."""
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randint(0, 10, size=(10, 3))
    with pytest.raises((ValueError, SystemError)):
        c2ImageD11.score(ubi, gv, 0.5)


def test_score_rejects_1d_ubi():
    """score() rejects 1D ubi (needs 3x3)."""
    gv = np.random.randn(10, 3).astype(np.float64)
    with pytest.raises(ValueError):
        c2ImageD11.score(np.ones(9), gv, 0.5)


def test_score_and_refine_soa_via_T():
    """score_and_refine() accepts (3,N) SoA via .T.copy()."""
    ubi = np.random.randn(3, 3).astype(np.float64)
    gv = np.random.randn(10, 3).astype(np.float64)
    n, s = c2ImageD11.score_and_refine(ubi, gv.T.copy(), 0.5)
    assert isinstance(n, (int, np.integer))
