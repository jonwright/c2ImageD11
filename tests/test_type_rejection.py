"""Test that ALL exposed functions reject wrong data types and shapes."""
from __future__ import absolute_import, division, print_function, unicode_literals

import pytest
import numpy as np
import c2ImageD11


# ======================== score / score_and_refine / score_and_assign =========

def test_score_f64_rejects_int_gv():
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randint(0, 10, size=(10, 3))
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.score(ubi, gv, 0.5)

def test_score_f64_rejects_1d_ubi():
    gv = np.random.randn(10, 3).astype(np.float64)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.score(np.ones(9), gv, 0.5)

def test_score_f64_rejects_2x2_ubi():
    gv = np.random.randn(10, 3).astype(np.float64)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.score(np.eye(2, dtype=np.float64), gv, 0.5)

def test_score_and_refine_rejects_int_gv():
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randint(0, 10, size=(10, 3))
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.score_and_refine(ubi, gv, 0.5)

def test_score_and_refine_rejects_1d_gv():
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randn(10).astype(np.float64)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.score_and_refine(ubi, gv, 0.5)

def test_score_and_assign_rejects_int_gv():
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randint(0, 10, size=(10, 3))
    dv = np.full(10, 999.0, dtype=np.float64)
    lb = np.full(10, -1, dtype=np.int32)
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.score_and_assign(ubi, gv, 0.5, dv, lb, 1)

def test_score_and_assign_rejects_int_labels():
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randn(10, 3).astype(np.float64)
    dv = np.full(10, 999.0, dtype=np.float64)
    lb = np.full(10, -1, dtype=np.float64)  # wrong dtype for labels
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.score_and_assign(ubi, gv, 0.5, dv, lb, 1)


# ======================== geometry ===========================================

def test_compute_geometry_rejects_int_xlylzl():
    omega = np.random.randn(10).astype(np.float64)
    t = np.zeros(3)
    out = np.zeros((10, 3))
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.compute_geometry(
            np.random.randint(0, 100, size=(10, 3)), omega, 1.0, 0.7, 1.5, 0.0, t, out)

def test_compute_gv_rejects_int_xlylzl():
    omega = np.random.randn(10).astype(np.float64)
    t = np.zeros(3)
    gv = np.zeros((10, 3))
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.compute_gv(
            np.random.randint(0, 100, size=(10, 3)), omega, 1.0, 0.7, 1.5, 0.0, t, gv)

def test_compute_xlylzl_rejects_int_s():
    f = np.random.randn(10, 3).astype(np.float64)
    p = np.random.randn(10, 3).astype(np.float64)
    r = np.eye(3, dtype=np.float64)
    dist = np.array([200.0])
    xlylzl = np.zeros((10, 3))
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.compute_xlylzl(
            np.random.randint(0, 100, size=(10, 3)), f, p, r, dist, xlylzl)


# ======================== image processing ===================================

def test_connectedpixels_rejects_int_data():
    labels = np.zeros((10, 10), dtype=np.int32)
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.connectedpixels(
            np.random.randint(0, 100, size=(10, 10)), labels, 50.0)

def test_connectedpixels_rejects_1d_data():
    data = np.random.randn(100).astype(np.float32)
    labels = np.zeros(100, dtype=np.int32)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.connectedpixels(data, labels, 50.0)

def test_localmaxlabel_rejects_int_data():
    labels = np.zeros((10, 10), dtype=np.int32)
    wrk = np.zeros((10, 10), dtype=np.int32)
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.localmaxlabel(
            np.random.randint(0, 100, size=(10, 10)), labels, wrk)

def test_clean_mask_rejects_wrong_dtype():
    msk = np.ones((10, 10), dtype=np.int32)
    ret = np.zeros((10, 10), dtype=np.int32)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.clean_mask(msk.astype(np.float32), ret)

def test_blobproperties_rejects_int_data():
    data = np.random.randn(10, 10).astype(np.float32)
    labels = np.random.randint(0, 3, size=(10, 10)).astype(np.int32)
    results = np.zeros((10, 8), dtype=np.float64)
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.blobproperties(
            np.random.randint(0, 100, size=(10, 10)), labels, 3, results)


# ======================== sparse =============================================

def test_tosparse_f32_rejects_int_img():
    msk = np.ones((10, 10), dtype=np.int32)
    row = np.zeros(100, dtype=np.int32)
    col = np.zeros(100, dtype=np.int32)
    val = np.zeros(100, dtype=np.float32)
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.tosparse_f32(
            np.random.randint(0, 100, size=(10, 10)), msk, row, col, val, 50.0)

def test_sparse_is_sorted_on_sorted():
    i = np.arange(10, dtype=np.uint16)
    j = np.zeros(10, dtype=np.uint16)
    result = c2ImageD11.sparse_is_sorted(i, j)
    assert isinstance(result, (int, np.integer))

def test_sparse_is_sorted_rejects_float_i():
    j = np.zeros(10, dtype=np.int32)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.sparse_is_sorted(np.arange(10).astype(np.float64), j)

def test_sparse_connectedpixels_rejects_float_i():
    nnz = 50
    imgsz = 50
    v = np.random.randn(nnz).astype(np.float32)
    i = np.arange(nnz, dtype=np.uint16)
    j = np.zeros(nnz, dtype=np.uint16)
    labels = np.zeros(imgsz, dtype=np.int32)
    c2ImageD11.sparse_connectedpixels(v, i, j, 0.5, labels)  # works
    # wrong dtype for i
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.sparse_connectedpixels(
            v, i.astype(np.float64), j, 0.5, labels)


# ======================== misc ===============================================

def test_closest_vec_rejects_int_x():
    ic = np.zeros(3, dtype=np.int32)
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.closest_vec(np.random.randint(0, 10, size=(10, 3)), ic)

def test_cluster1d_rejects_float_ids():
    ar = np.random.randn(20).astype(np.float64)
    order = np.argsort(ar).astype(np.int32)
    ids = np.zeros(20, dtype=np.float64)  # wrong dtype
    avgs = np.zeros(20, dtype=np.float64)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.cluster1d(ar, order, 0.5, ids, avgs)

def test_count_shared_good():
    i = np.array([1, 2, 3], dtype=np.int32)
    j = np.array([3, 4, 5], dtype=np.int32)
    assert c2ImageD11.count_shared(i, j) >= 0

def test_count_shared_rejects_float():
    i = np.array([1, 2, 3], dtype=np.int32)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.count_shared(i.astype(np.float64), i)

def test_refine_assigned_rejects_int_gv():
    ubi = np.eye(3, dtype=np.float64)
    gv = np.random.randint(0, 10, size=(10, 3))
    labels = np.full(10, 1, dtype=np.int32)
    with pytest.raises((ValueError, TypeError, SystemError)):
        c2ImageD11.refine_assigned(ubi, gv, labels, 1)

def test_put_incr32_good():
    data = np.zeros(10, dtype=np.float32)
    ind = np.array([1, 2, 3], dtype=np.int32)
    vals = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    c2ImageD11.put_incr32(data, ind, vals)

def test_put_incr32_rejects_float_ind():
    data = np.zeros(10, dtype=np.float32)
    vals = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.put_incr32(
            data, np.array([1.0, 2.0, 3.0], dtype=np.float64), vals)


# ======================== tosparse ===========================================

def test_tosparse_u16_bad_img_format():
    """tosparse_u16 expects uint16 img; float32 should raise."""
    img = np.random.randn(10, 10).astype(np.float32)
    msk = np.ones((10, 10), dtype=np.int32)
    row = np.zeros(100, dtype=np.int32)
    col = np.zeros(100, dtype=np.int32)
    val = np.zeros(100, dtype=np.uint16)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.tosparse_u16(img, msk, row, col, val, 0)


# ======================== darkflat ===========================================

def test_uint16_to_float_darksub_rejects_int_drk():
    """darksub expects float drk; uint16 should raise."""
    img = np.random.randint(0, 100, size=(10, 10)).astype(np.uint16)
    drk = np.random.randint(0, 100, size=(10, 10)).astype(np.uint16)
    data = np.zeros((10, 10), dtype=np.float32)
    with pytest.raises((ValueError, TypeError)):
        c2ImageD11.uint16_to_float_darksub(img, drk, data)
