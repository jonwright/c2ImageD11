"""setup.py for c2ImageD11.

Build the .so with meson first, then pip install:

   pip install .

Force a rebuild even if .so exists:

   C2IMAGED11_REBUILD=1 pip install .
   python setup.py --force-rebuild install
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

from setuptools import setup
from setuptools.command.build_py import build_py

HERE = os.path.dirname(os.path.abspath(__file__))
PKG_DIR = os.path.join(HERE, "c2ImageD11")
SO_NAME = "_cImageD11.so"
SO_PATH = os.path.join(PKG_DIR, SO_NAME)


def _build_so(force=False):
    if not force and os.path.exists(SO_PATH):
        return
    build_dir = os.path.join(HERE, "build", "libc2ImageD11")
    lib_dir = os.path.join(HERE, "lib")
    import shutil
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir, exist_ok=True)
    try:
        import subprocess
        subprocess.check_call(["meson", "setup", lib_dir], cwd=build_dir)
        subprocess.check_call(["ninja"], cwd=build_dir)
        shutil.copy(os.path.join(build_dir, SO_NAME), SO_PATH)
    except Exception as exc:
        print("meson build failed: %s" % exc, file=sys.stderr)
        print("Build manually: see lib/meson.build for instructions",
              file=sys.stderr)
        sys.exit(1)


class build_cmodule(build_py):
    def run(self):
        force = os.environ.get("C2IMAGED11_REBUILD") == "1"
        _build_so(force=force)
        build_py.run(self)


# Consume --force-rebuild before setuptools sees it
if "--force-rebuild" in sys.argv:
    sys.argv.remove("--force-rebuild")
    os.environ["C2IMAGED11_REBUILD"] = "1"

setup(
    name="c2ImageD11",
    version="0.2.0",
    description="C extensions for ImageD11 (c2py23 binding)",
    packages=["c2ImageD11"],
    package_data={"c2ImageD11": [SO_NAME]},
    include_package_data=True,
    cmdclass={"build_py": build_cmodule},
    zip_safe=False,
)
