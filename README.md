# c2ImageD11

Standalone binary distribution of ImageD11 C extensions, ported from
f2py to c2py23.  Provides ~58 C functions (closest-vec, score, compute_gv,
connectedpixels, sparse operations, etc.) as a compiled Python extension.

**Status:** All 53 equivalence tests pass (1 expected skip). CI green on
Python 2.7–3.14.

## Quick start

```bash
pip install --no-build-isolation -e .
pytest tests/
```

Requires GCC with `-fopenmp` and a c2py23 installation in a sibling directory.
