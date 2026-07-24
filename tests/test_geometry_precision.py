"""Test f32/f64 precision for compute_gv and compute_geometry.

Verifies that f32 and f64 dispatch produce consistent results
within float32 tolerance.  Covers compute_gv, compute_geometry,
random inputs, and edge cases.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import c2ImageD11 as ci


TOL_F32 = 1e-6   # float32 relative tolerance (~7 digits)
TOL_GEO = 1e-3    # geometry: atan2f near 180 deg has ~5e-4 abs diff


def gv_consistent(xlylzl_64, omega_64, omegasign, wvln, wedge, chi, t_64):
    """Return True if f32 and f64 compute_gv outputs are consistent."""
    n = len(xlylzl_64)
    gv_64 = np.empty((n, 3), dtype=np.float64)
    ci.compute_gv(xlylzl_64, omega_64, omegasign, wvln, wedge, chi, t_64, gv_64)

    xlylzl_32 = xlylzl_64.astype(np.float32)
    omega_32 = omega_64.astype(np.float32)
    t_32 = t_64.astype(np.float32)
    gv_32 = np.empty((n, 3), dtype=np.float32)
    ci.compute_gv(xlylzl_32, omega_32, omegasign, wvln, wedge, chi, t_32, gv_32)

    return np.allclose(gv_32, gv_64, rtol=TOL_F32, atol=TOL_F32)


def geom_consistent(xlylzl_64, omega_64, omegasign, wvln, wedge, chi, t_64):
    """Return True if f32 and f64 compute_geometry outputs are consistent."""
    n = len(xlylzl_64)
    out_64 = np.empty((n, 6), dtype=np.float64)
    ci.compute_geometry(xlylzl_64, omega_64, omegasign, wvln, wedge, chi, t_64, out_64)

    xlylzl_32 = xlylzl_64.astype(np.float32)
    omega_32 = omega_64.astype(np.float32)
    t_32 = t_64.astype(np.float32)
    out_32 = np.empty((n, 6), dtype=np.float32)
    ci.compute_geometry(xlylzl_32, omega_32, omegasign, wvln, wedge, chi, t_32, out_32)

    return np.allclose(out_32, out_64, rtol=TOL_F32, atol=TOL_GEO)


def gen_data(n, seed=42):
    """Generate realistic test data for geometry functions."""
    rng = np.random.RandomState(seed)
    xlylzl = rng.randn(n, 3).astype(np.float64) * 10.0
    xlylzl[:, 0] += 100.0  # detector distance ~100 mm
    omega = rng.rand(n).astype(np.float64) * 360.0  # degrees
    t = rng.randn(3).astype(np.float64) * 5.0  # grain position ~5 mm
    return xlylzl, omega, t


class TestGVPrecision(object):
    """compute_gv: f32 vs f64 precision."""

    def test_small(self):
        xlylzl, omega, t = gen_data(10, seed=1)
        assert gv_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_medium(self):
        xlylzl, omega, t = gen_data(1000, seed=2)
        assert gv_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_large(self):
        xlylzl, omega, t = gen_data(50000, seed=3)
        assert gv_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_zero_translation(self):
        xlylzl, omega, _ = gen_data(100, seed=4)
        t = np.zeros(3, dtype=np.float64)
        assert gv_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_zero_omega(self):
        xlylzl = np.random.randn(100, 3).astype(np.float64) * 10.0
        xlylzl[:, 0] += 100.0
        omega = np.zeros(100, dtype=np.float64)
        t = np.zeros(3, dtype=np.float64)
        assert gv_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_small_angles(self):
        """Spots near beam center: small 2theta.  Tests the cos(2theta)-1
        reformulated path in both f32 and f64."""
        rng = np.random.RandomState(5)
        n = 500
        xlylzl = rng.randn(n, 3).astype(np.float64) * 0.5  # small offsets
        xlylzl[:, 0] += 100.0
        omega = rng.rand(n).astype(np.float64) * 360.0
        t = np.zeros(3, dtype=np.float64)
        assert gv_consistent(xlylzl, omega, 1.0, 0.3, 0.0, 0.0, t)

    def test_different_wavelength(self):
        xlylzl, omega, t = gen_data(200, seed=7)
        # Short wavelength (hard X-rays): larger g-vectors
        assert gv_consistent(xlylzl, omega, 1.0, 0.3, 5.0, 3.0, t)
        assert gv_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_dispatch_fires(self):
        """Verify both f32 and f64 variants are called."""
        import struct
        mod = ci._cImageD11
        xlylzl, omega, t = gen_data(100, seed=8)

        # f32 call
        xl_f32 = xlylzl.astype(np.float32)
        om_f32 = omega.astype(np.float32)
        t_f32 = t.astype(np.float32)
        gv_f32 = np.empty((100, 3), dtype=np.float32)
        ci.compute_gv(xl_f32, om_f32, 1.0, 0.7, 5.0, 3.0, t_f32, gv_f32)

        # Check f32 variant fired
        f32_ptr = getattr(mod, "_c2py_ol_ptr_compute_gv__compute_gv_f32")
        buf = bytearray(128)
        mod._c2py_perf_read(int(f32_ptr), buf)
        assert struct.unpack_from("Q", buf)[0] > 0, "f32 variant did not fire"

        # f64 call
        gv_f64 = np.empty((100, 3), dtype=np.float64)
        ci.compute_gv(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t, gv_f64)

        # Check f64 variant fired
        f64_ptr = getattr(mod, "_c2py_ol_ptr_compute_gv__compute_gv")
        buf = bytearray(128)
        mod._c2py_perf_read(int(f64_ptr), buf)
        assert struct.unpack_from("Q", buf)[0] > 0, "f64 variant did not fire"


class TestGeometryPrecision(object):
    """compute_geometry: f32 vs f64 precision."""

    def test_small(self):
        xlylzl, omega, t = gen_data(10, seed=10)
        assert geom_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_medium(self):
        xlylzl, omega, t = gen_data(1000, seed=11)
        assert geom_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_large(self):
        xlylzl, omega, t = gen_data(50000, seed=12)
        assert geom_consistent(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t)

    def test_small_angles(self):
        rng = np.random.RandomState(13)
        n = 500
        xlylzl = rng.randn(n, 3).astype(np.float64) * 0.5
        xlylzl[:, 0] += 100.0
        omega = rng.rand(n).astype(np.float64) * 360.0
        t = np.zeros(3, dtype=np.float64)
        assert geom_consistent(xlylzl, omega, 1.0, 0.3, 0.0, 0.0, t)

    def test_output_columns(self):
        """Individual output columns should match within tolerance."""
        xlylzl, omega, t = gen_data(200, seed=14)
        n = 200
        out_64 = np.empty((n, 6), dtype=np.float64)
        ci.compute_geometry(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t, out_64)

        out_32 = np.empty((n, 6), dtype=np.float32)
        ci.compute_geometry(xlylzl.astype(np.float32),
                            omega.astype(np.float32), 1.0, 0.7, 5.0, 3.0,
                            t.astype(np.float32), out_32)

        for col, name in enumerate(["tth", "eta", "ds", "gx", "gy", "gz"]):
            diff = np.max(np.abs(out_32[:, col].astype(np.float64) - out_64[:, col]))
            assert diff < 1e-4, "column %s max diff %.2e exceeds tolerance" % (name, diff)


class TestGVEdgeCases(object):
    """compute_gv edge case tests."""

    def test_n0(self):
        """Zero spots: no crash, output empty."""
        xlylzl = np.empty((1, 3), dtype=np.float64)[:0]
        omega = np.empty((1,), dtype=np.float64)[:0]
        t = np.zeros(3, dtype=np.float64)
        gv = np.empty((0, 3), dtype=np.float64)
        ci.compute_gv(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t, gv)
        assert gv.shape == (0, 3)

    def test_n1(self):
        """Single spot."""
        xlylzl = np.array([[100.0, 5.0, -3.0]], dtype=np.float64)
        omega = np.array([45.0], dtype=np.float64)
        t = np.zeros(3, dtype=np.float64)
        gv_64 = np.empty((1, 3), dtype=np.float64)
        ci.compute_gv(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t, gv_64)
        assert not np.any(np.isnan(gv_64))
        assert not np.any(np.isinf(gv_64))

    def test_identity_omega(self):
        """Omega=0, no rotation: output should be deterministic."""
        xlylzl, _, t = gen_data(100, seed=15)
        omega = np.zeros(100, dtype=np.float64)
        gv1 = np.empty((100, 3), dtype=np.float64)
        gv2 = np.empty((100, 3), dtype=np.float64)
        ci.compute_gv(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t, gv1)
        ci.compute_gv(xlylzl, omega, 1.0, 0.7, 5.0, 3.0, t, gv2)
        assert np.allclose(gv1, gv2)
