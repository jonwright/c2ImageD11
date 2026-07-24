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


if __name__ == "__main__":
    main()
