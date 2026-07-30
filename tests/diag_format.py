"""Diagnostic: print buffer format characters for all numpy types.

Run on CI to see what the ndarray fast path produces for each dtype.
Compare Linux vs Windows format strings.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np
import c2ImageD11


def _get_format_for(arr):
    """Return the format string c2py23 sees for a numpy array."""
    mod = c2ImageD11._cImageD11
    # Use the perf counter overlay to indirectly check format
    # Actually just call a function that accepts 'buffer' with a format check
    # The error message will tell us the format
    try:
        # Use array_stats since it has format check
        mod.array_stats(arr)
        return "OK (no error)"
    except ValueError as e:
        msg = str(e)
        # Extract format from error: "got format='X'"
        if "format='" in msg:
            idx = msg.index("format='")
            return msg[idx + 8:].split("'")[0]
        return msg[:80]
    except Exception as e:
        return str(e)[:80]


def main():
    types = [
        ("float32", np.float32),
        ("float64", np.float64),
        ("int8", np.int8),
        ("uint8", np.uint8),
        ("int16", np.int16),
        ("uint16", np.uint16),
        ("int32", np.int32),
        ("uint32", np.uint32),
        ("int64", np.int64),
        ("uint64", np.uint64),
    ]

    print("=== Buffer format diagnostic ===")
    print()

    for name, dtype in types:
        arr = np.ones(5, dtype=dtype)
        dt = np.dtype(dtype)
        itemsize = dt.itemsize
        char = dt.char
        fmt = _get_format_for(arr)
        print("{:>10s}: dtype.char={!r} itemsize={}  c2py23 format: {}".format(
            name, char, itemsize, fmt))

    print()
    print("=== Variant symbol check ===")
    print()

    mod = c2ImageD11._cImageD11
    for func in ["connectedpixels", "blobproperties", "localmaxlabel",
                 "make_clean_mask", "sparse_connectedpixels", "sparse_localmaxlabel"]:
        variants = [n for n in dir(mod)
                    if "_c2py_ol_ptr_" in n
                    and func in n
                    and ("_u8" in n or "_u16" in n or "_u32" in n)]
        if variants:
            print("  {}: {} variant(s) present".format(func, len(variants)))
            for v in sorted(variants):
                print("    {}".format(v))
        else:
            print("  {}: NO u8/u16/u32 variants found".format(func))

    print()
    print("=== Dispatch test: call with uint16 data ===")
    print()

    # Test connectedpixels with uint16
    img16 = np.ones((5, 5), dtype=np.uint16) * 50
    lb16 = np.empty((5, 5), dtype=np.int32)
    try:
        r = mod.connectedpixels(img16, lb16, 100)
        print("  connectedpixels(u16): {} objects".format(r))
    except SystemError:
        print("  connectedpixels(u16): SystemError (no matching overload)")
    except ValueError as e:
        print("  connectedpixels(u16): ValueError: {}".format(e))
    except Exception as e:
        print("  connectedpixels(u16): {}: {}".format(type(e).__name__, e))

    # Test make_clean_mask with uint16
    img16b = np.ones((5, 5), dtype=np.uint16)
    msk = np.empty((5, 5), dtype=np.int8)
    ret = np.empty((5, 5), dtype=np.int8)
    try:
        r = mod.make_clean_mask(img16b, 100, msk, ret)
        print("  make_clean_mask(u16): {}".format(r))
    except SystemError:
        print("  make_clean_mask(u16): SystemError (no matching overload)")
    except ValueError as e:
        print("  make_clean_mask(u16): ValueError: {}".format(e))
    except Exception as e:
        print("  make_clean_mask(u16): {}: {}".format(type(e).__name__, e))

    print()
    print("=== Exact test reproduce ===")
    print()

    img = np.random.RandomState(1).randint(0, 256, (15, 20), dtype=np.uint8)
    th = 128
    labels = np.empty(img.shape[:2], dtype=np.int32)

    # f32 call (baseline -- should always work)
    try:
        ref_n = mod.connectedpixels(img.astype(np.float32), labels, 128.0)
        print("  f32: ref_n={}".format(ref_n))
    except Exception as e:
        print("  f32: {}: {}".format(type(e).__name__, e))
        labels = np.empty(img.shape[:2], dtype=np.int32)

    # u8 call
    try:
        n = mod.connectedpixels(img.astype(np.uint8), labels, th)
        print("  u8: n={}".format(n))
    except SystemError:
        print("  u8: SystemError (no matching overload)")
    labels[:] = 0

    # u16 call (same as test)
    try:
        n = mod.connectedpixels(img.astype(np.uint16), labels, th)
        print("  u16: n={}".format(n))
    except SystemError:
        print("  u16: SystemError (no matching overload)")
    labels[:] = 0

    # u32 call
    try:
        n = mod.connectedpixels(img.astype(np.uint32), labels, th)
        print("  u32: n={}".format(n))
    except SystemError:
        print("  u32: SystemError (no matching overload)")


if __name__ == "__main__":
    main()
