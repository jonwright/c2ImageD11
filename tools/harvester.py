#!/usr/bin/env python
"""harvester.py - Regenerate all files in lib/interface/.

Extracts C2PY_BEGIN..C2PY_END blocks from C sources in lib/src/,
assembles _cImageD11.c2py, copies c2py23 runtime, and runs
c2py23.cli.generate to produce the wrapper.

Usage:
    python tools/harvester.py --output-dir lib/interface
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import ast
import os
import re
import shutil
import subprocess
import sys

import yaml

C2PY_RUNTIME_FILES = [
    "c2py_runtime.c",
    "c2py_runtime.h",
    "c2py_amd64.h",
    "c2py_arm64.h",
    "c2py_ppc64.h",
]


def extract_c2py_blocks(text):
    """Yield (line_start, python_dict) for each C2PY_BLOCK."""
    begin_re = re.compile(r"C2PY_BEGIN")
    end_re = re.compile(r"C2PY_END")
    lines = text.splitlines(True)
    i = 0
    while i < len(lines):
        if begin_re.search(lines[i]):
            start_line = i + 1
            i += 1
            content_lines = []
            while i < len(lines) and not end_re.search(lines[i]):
                content_lines.append(lines[i])
                i += 1
            comment_prefix = re.compile(r"^\s*\*\s?")
            cleaned = []
            for ln in content_lines:
                s = ln.rstrip("\n\r")
                s = comment_prefix.sub("", s, count=1)
                cleaned.append(s)
            block_text = "\n".join(cleaned).strip()
            if block_text:
                block_text = re.sub(
                    r'(?<=[\s,\[{:])true(?=\s*[\s,\]\}:])', 'True', block_text)
                block_text = re.sub(
                    r'(?<=[\s,\[{:])false(?=\s*[\s,\]\}:])', 'False', block_text)
                try:
                    obj = ast.literal_eval(block_text)
                except (ValueError, SyntaxError) as e:
                    print("ERROR: %s around line %d" % (e, start_line),
                          file=sys.stderr)
                    print("  Block text:\n%s" % block_text, file=sys.stderr)
                    sys.exit(1)
                if not isinstance(obj, dict):
                    print("ERROR: C2PY_BLOCK must be a dict (got %s) at line %d"
                          % (type(obj).__name__, start_line), file=sys.stderr)
                    sys.exit(1)
                yield start_line, obj
            if i < len(lines):
                i += 1
        else:
            i += 1


def find_c_sources(src_dir):
    """Find all .c files in src_dir recursively, sorted."""
    sources = []
    for root, dirs, files in os.walk(src_dir):
        for f in sorted(files):
            if f.endswith(".c") and not f.startswith("."):
                sources.append(os.path.join(root, f))
    return sources


def find_h_headers(src_dir):
    """Find all .h files in src_dir recursively, sorted, skipping vendor dirs."""
    headers = []
    for root, dirs, files in os.walk(src_dir):
        basename = os.path.basename(root)
        if basename == "vendor":
            continue
        for f in sorted(files):
            if f.endswith(".h") and not f.startswith("."):
                headers.append(os.path.join(root, f))
    return headers


def block_to_c2py_entry(block):
    """Convert a C2PY_BLOCK dict to a c2py23 YAML entry dict."""
    entry = {
        "py_sig": block["py_sig"],
        "doc": block.get("doc", ""),
    }
    if "params" in block:
        entry["params"] = block["params"]
    if "checks" in block:
        entry["checks"] = block["checks"]
    if block.get("gil_release"):
        entry["gil_release"] = True
    if "c_overloads" in block:
        entry["c_overloads"] = block["c_overloads"]
    return entry


def is_constants_block(obj):
    """True if obj is a dict where all values are integers (a constants block)."""
    if not isinstance(obj, dict):
        return False
    if "py_sig" in obj:
        return False
    return all(isinstance(v, int) for v in obj.values())


def extract_blocks_from_file(filepath):
    """Extract all C2PY_BLOCKs from a file, returning (func_blocks, const_blocks)."""
    funcs = []
    consts = {}
    with open(filepath, "r") as f:
        text = f.read()
    for line_no, obj in extract_c2py_blocks(text):
        if is_constants_block(obj):
            consts.update(obj)
        elif "py_sig" in obj:
            funcs.append((line_no, obj))
        else:
            print("  WARNING: %s:%d: unknown block type" % (filepath, line_no),
                  file=sys.stderr)
    return funcs, consts


def assemble_c2py(src_dir, output_dir):
    """Assemble the complete .c2py document."""
    c_sources = find_c_sources(src_dir)
    h_headers = find_h_headers(src_dir)
    all_blocks = []
    all_consts = {}

    # Process all C sources and headers for C2PY_BLOCKs
    for filepath in c_sources + h_headers:
        funcs, consts = extract_blocks_from_file(filepath)
        if consts:
            print("  %s: constants" % os.path.relpath(filepath, output_dir),
                  file=sys.stderr)
        all_consts.update(consts)
        if funcs:
            rel = os.path.relpath(filepath, output_dir)
            print("  %s: %d function(s)" % (rel, len(funcs)),
                  file=sys.stderr)
            all_blocks.append((filepath, funcs))

    output = []
    output.append("# c2py23 interface definition for c2ImageD11")
    output.append("#")
    output.append("# AUTO-ASSEMBLED by harvester.py from C2PY_BLOCKs in C sources.")
    output.append("")
    output.append("module: _cImageD11")
    output.append("timing: true")
    output.append("free_threading: true")
    output.append("")
    output.append("source:")
    for src in c_sources:
        rel = os.path.relpath(src, output_dir)
        output.append("  - %s" % rel)
    output.append("")
    output.append("headers:")
    for hdr in h_headers:
        rel = os.path.relpath(hdr, output_dir)
        output.append("  - %s" % rel)
    output.append("")

    if all_consts:
        output.append("constants:")
        for k, v in sorted(all_consts.items()):
            output.append("  %s: %d" % (k, v))
        output.append("")

    output.append("functions:")
    output.append("")

    for filepath, funcs in all_blocks:
        rel = os.path.relpath(filepath, output_dir)
        output.append("  # ==================================================="
                      "==================")
        output.append("  # %s" % rel)
        output.append("  # ==================================================="
                      "==================")
        output.append("")
        for line_no, block in funcs:
            entry = block_to_c2py_entry(block)
            yaml_text = yaml.dump(
                [entry],
                default_flow_style=None,
                allow_unicode=True,
                width=120,
                indent=2,
                sort_keys=False,
            )
            for line in yaml_text.splitlines():
                output.append("  " + line)
            output.append("")

    return "\n".join(output) + "\n"


def copy_runtime(output_dir):
    """Copy c2py23 runtime files to output_dir."""
    try:
        import c2py23
        pkg_dir = os.path.dirname(c2py23.__file__)
        runtime_dir = os.path.join(pkg_dir, "runtime")
    except ImportError:
        print("ERROR: c2py23 not installed. Cannot copy runtime files.",
              file=sys.stderr)
        sys.exit(1)
    for fname in C2PY_RUNTIME_FILES:
        src = os.path.join(runtime_dir, fname)
        dst = os.path.join(output_dir, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print("  COPIED: %s" % fname, file=sys.stderr)
        else:
            print("  WARNING: %s not found in c2py23 runtime" % fname,
                  file=sys.stderr)


def generate_wrapper(output_dir):
    """Run c2py23.cli.generate to produce _cImageD11_wrapper.c."""
    c2py_path = os.path.join(output_dir, "_cImageD11.c2py")
    wrapper_path = os.path.join(output_dir, "_cImageD11_wrapper.c")
    if not os.path.isfile(c2py_path):
        print("ERROR: %s not found. Run harvester first." % c2py_path,
              file=sys.stderr)
        sys.exit(1)
    print("  GENERATING: %s" % wrapper_path, file=sys.stderr)
    subprocess.check_call([
        sys.executable, "-m", "c2py23.cli", "generate",
        c2py_path, "-o", wrapper_path,
    ])


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Regenerate lib/interface/ from C sources + c2py23")
    parser.add_argument("--output-dir", required=True,
                        help="Output directory (e.g. lib/interface)")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    parent_dir = os.path.dirname(output_dir)
    src_dir = os.path.join(parent_dir, "src")

    if not os.path.isdir(src_dir):
        print("ERROR: source directory not found: %s" % src_dir,
              file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # 1. Assemble _cImageD11.c2py
    c2py_text = assemble_c2py(src_dir, output_dir)
    c2py_path = os.path.join(output_dir, "_cImageD11.c2py")
    with open(c2py_path, "w") as f:
        f.write(c2py_text)
    print("WROTE: %s (%d bytes)" % (c2py_path, len(c2py_text)),
          file=sys.stderr)

    # 2. Copy c2py23 runtime files
    copy_runtime(output_dir)

    # 3. Generate wrapper
    generate_wrapper(output_dir)

    print("DONE", file=sys.stderr)


if __name__ == "__main__":
    main()
