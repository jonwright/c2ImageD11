"""setup.py for c2ImageD11.

Build the .so with meson first, then pip install:

   pip install .

Force a rebuild:

   C2IMAGED11_REBUILD=1 pip install .
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import platform
import sys

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.dist import Distribution


class PlatlibDistribution(Distribution):
    """Force platlib layout so auditwheel accepts our .so in package_data."""
    def has_ext_modules(self):
        return True


HERE = os.path.dirname(os.path.abspath(__file__))
# str() for Python 2.7 unicode_literals compatibility
PKG_DIR = str(os.path.join(HERE, "c2ImageD11"))
ARCH = str(platform.machine())
EXT = ".pyd" if sys.platform == "win32" else ".so"
SO_NAME = "_cImageD11_{}{}".format(ARCH, EXT)
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
        shutil.copy(
            os.path.join(build_dir, "_cImageD11.dll" if sys.platform == "win32" else "_cImageD11.so"),
            SO_PATH)
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


if "bdist_wheel" in sys.argv:
    # Prefer setuptools' built-in bdist_wheel (>=70.1) over separate wheel package
    # to properly place .so in platlib (required by auditwheel).
    try:
        from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
    except ImportError:
        try:
            from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
        except ImportError:
            _bdist_wheel = None

    if _bdist_wheel is not None:
        python_tag = "py2" if sys.version_info[0] == 2 else "py3"

        class bdist_wheel_override(_bdist_wheel):
            def finalize_options(self):
                _bdist_wheel.finalize_options(self)
                self.root_is_pure = False

            def get_tag(self):
                impl, abi, plat = _bdist_wheel.get_tag(self)
                return python_tag, "none", plat

        bdist_wheel_cmd = bdist_wheel_override
    else:
        bdist_wheel_cmd = None
else:
    bdist_wheel_cmd = None

cmdclass = {"build_py": build_cmodule}
if bdist_wheel_cmd:
    cmdclass["bdist_wheel"] = bdist_wheel_cmd

setup(
    name=str("c2ImageD11"),
    version=str("0.2.0"),
    description=str("C extensions for ImageD11 (c2py23 binding)"),
    packages=[str("c2ImageD11")],
    package_data={str("c2ImageD11"): [SO_NAME]},
    include_package_data=True,
    distclass=PlatlibDistribution,
    cmdclass=cmdclass,
    zip_safe=False,
)
