#!/usr/bin/env python
"""strip_c2py.py - Strip all C2PY_BEGIN...C2PY_END blocks from C source.

Reads C source from stdin or a file, removes every /* C2PY_BEGIN ... C2PY_END */
block (including the markers), and writes the result to stdout.

Usage:
    python strip_c2py.py < input.c > output.c
    python strip_c2py.py input.c > output.c
    python strip_c2py.py input.c -o output.c
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import re
import sys


def strip_c2py_blocks(text):
    """Remove all /* C2PY_BEGIN ... C2PY_END */ blocks from text.

    A block starts with a line containing 'C2PY_BEGIN' (inside a /* comment)
    and ends with a line containing 'C2PY_END' (inside the same comment).

    Both the markers and all lines between them are removed.
    """
    begin_re = re.compile(r"C2PY_BEGIN")
    end_re = re.compile(r"C2PY_END")
    lines = text.splitlines(True)  # keep line endings
    out = []
    i = 0
    while i < len(lines):
        if begin_re.search(lines[i]):
            # skip until we find C2PY_END
            i += 1
            while i < len(lines) and not end_re.search(lines[i]):
                i += 1
            # skip the C2PY_END line too
            if i < len(lines):
                i += 1
            # eat blank lines after the block
            while i < len(lines) and lines[i].strip() == "":
                i += 1
        else:
            out.append(lines[i])
            i += 1
    return "".join(out)


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] != "-o":
        path = sys.argv[1]
        with open(path, "r") as f:
            text = f.read()
    else:
        text = sys.stdin.read()

    result = strip_c2py_blocks(text)

    if "-o" in sys.argv:
        idx = sys.argv.index("-o") + 1
        outpath = sys.argv[idx]
        with open(outpath, "w") as f:
            f.write(result)
    else:
        sys.stdout.write(result)


if __name__ == "__main__":
    main()
