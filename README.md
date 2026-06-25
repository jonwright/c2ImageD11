# c2ImageD11

Standalone C extensions for ImageD11, ported from f2py to **c2py23**.
C functions are exposed by a generated CPython extension wrapper.
Two functions (`blobproperties`, `sparse_blob2Dproperties`) have thin
Python allocation wrappers in `__init__.py` to match f2py's convention
of auto-allocating output arrays.

## Build

A normal build needs only meson + ninja + a C compiler.  The generated
files in `lib/interface/` are checked into git, so c2py23 is **not**
required.

```bash
mkdir -p build/libc2ImageD11
cd build/libc2ImageD11
meson setup ../../lib
ninja
cp _cImageD11.so ../../c2ImageD11/
```

## Regenerate `lib/interface/`

Run this when C2PY_BLOCKs change or c2py23 is updated (requires c2py23):

```bash
python3 tools/harvester.py --output-dir lib/interface
```

## Test

```bash
python3 -m pytest tests/
```

## Distributing

Copy `_cImageD11.so` into `c2ImageD11/` and the package is ready — same
pattern as a ctypes library. A two-tier build is planned.
