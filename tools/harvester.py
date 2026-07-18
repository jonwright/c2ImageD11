#!/usr/bin/env python
"""harvester.py - Regenerate all files in lib/interface/.

Extracts C2PY_BEGIN..C2PY_END blocks from C sources in lib/functions/,
assembles _cImageD11.c2py (Python dict format), copies c2py23 runtime,
and generates the wrapper in-process via from_c2py_dict() + generate().

Usage:
    python tools/harvester.py --output-dir lib/interface
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import ast
import json
import os
import re
import shutil
import sys

from c2py23.parser import from_c2py_dict
from c2py23.generator import generate

C2PY_RUNTIME_FILES = [
    "c2py_dlsym.c",
    "c2py_dlsym.h",
    "c2py_pythonh.c",
    "c2py_pythonh.h",
    "c2py_runtime.c",
    "c2py_runtime.h",
    "c2py_amd64.h",
    "c2py_arm64.h",
    "c2py_ppc64.h",
]


def _py_repr(obj, indent=0):
    """Render a Python object as a pretty-printed Python dict literal."""
    sp = "    "
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = []
        for k in sorted(obj.keys()):
            kr = json.dumps(k)
            vr = _py_repr(obj[k], indent + 1)
            items.append(sp * (indent + 1) + kr + ": " + vr)
        inner = ",\n".join(items)
        return "{\n" + inner + ",\n" + sp * indent + "}"
    elif isinstance(obj, list):
        if not obj:
            return "[]"
        if len(obj) == 1 and not isinstance(obj[0], (dict, list)):
            return "[" + _py_repr(obj[0], indent) + "]"
        items = []
        for v in obj:
            items.append(sp * (indent + 1) + _py_repr(v, indent + 1))
        inner = ",\n".join(items)
        return "[\n" + inner + ",\n" + sp * indent + "]"
    elif isinstance(obj, bool):
        return "True" if obj else "False"
    elif obj is None:
        return "None"
    elif isinstance(obj, (int, float)):
        return json.dumps(obj)
    else:
        return json.dumps(obj)


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
    """Find all .c files in src_dir recursively, sorted by ISA priority
    for files under score_and_refine/, alphabetical for others."""
    sources = []
    for root, dirs, files in os.walk(src_dir):
        for f in sorted(files):
            if f.endswith(".c") and not f.startswith("."):
                sources.append(os.path.join(root, f))

    def _isa_priority(filepath):
        name = os.path.basename(filepath)
        if "avx512" in name:
            return 3
        if "avx2" in name:
            return 2
        if "sse41" in name:
            return 1
        return 0

    # Sort: ISA priority first (for score_and_refine kernels), then alphabetical
    sources.sort(key=lambda f: (_isa_priority(f), f))
    return sources


def find_cpp_sources(src_dir):
    """Find all .cpp files in src_dir recursively, sorted by ISA priority.
    
    ISA priority (lowest to highest, so highest is prepended first):
      baseline (no ISA suffix) < sse41 < avx2 < avx512
    """
    sources = []
    for root, dirs, files in os.walk(src_dir):
        for f in sorted(files):
            if f.endswith(".cpp") and not f.startswith("."):
                sources.append(os.path.join(root, f))
    
    def _isa_priority(filepath):
        name = os.path.basename(filepath)
        if "avx512" in name:
            return 3
        if "avx2" in name:
            return 2
        if "sse41" in name:
            return 1
        return 0
    
    sources.sort(key=_isa_priority)
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


def block_to_func_entry(block):
    """Convert a C2PY_BLOCK dict to a c2py function entry dict."""
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
    """Assemble the complete c2py interface dict."""
    c_sources = find_c_sources(src_dir)
    cpp_sources = find_cpp_sources(src_dir)
    h_headers = find_h_headers(src_dir)

    def _isa_priority(filepath):
        name = os.path.basename(filepath)
        if "avx512" in name: return 3
        if "avx2" in name:   return 2
        if "sse41" in name:   return 1
        return 0

    # Combine and sort by ISA priority so that higher-ISA files
    # (avx512) are processed last and their overloads prepended first.
    all_sources = c_sources + cpp_sources
    all_sources.sort(key=_isa_priority)

    # py_sig -> entry (merge overloads across .c, .cpp, .h files)
    func_entries = {}
    all_consts = {}

    for filepath in all_sources + h_headers:
        funcs, consts = extract_blocks_from_file(filepath)
        if consts:
            print("  %s: constants" % os.path.relpath(filepath, output_dir),
                  file=sys.stderr)
        all_consts.update(consts)
        if funcs:
            rel = os.path.relpath(filepath, output_dir)
            print("  %s: %d function(s)" % (rel, len(funcs)),
                  file=sys.stderr)
            for line_no, block in funcs:
                entry = block_to_func_entry(block)
                py_sig = block["py_sig"]
                if py_sig in func_entries:
                    # Merge: variant .cpp adds c_overloads,
                    # PREPENDED so they win first-match dispatch
                    existing = func_entries[py_sig]
                    c_overloads = entry.get("c_overloads", [])
                    if c_overloads:
                        existing_overloads = existing.get("c_overloads", [])
                        existing["c_overloads"] = c_overloads + existing_overloads
                else:
                    func_entries[py_sig] = entry

    result = {
        "module": "_cImageD11",
        "timing": True,
        "free_threading": True,
    }

    result["source"] = [
        os.path.relpath(src, output_dir) for src in c_sources
    ]

    result["cpp_source"] = [
        os.path.relpath(src, output_dir) for src in cpp_sources
    ]

    result["headers"] = [
        os.path.relpath(hdr, output_dir) for hdr in h_headers
    ]

    if all_consts:
        result["constants"] = all_consts

    result["functions"] = list(func_entries.values())

    return result


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


def generate_wrapper(assembled, output_dir):
    """Generate _cImageD11_wrapper.c from the assembled dict in-process."""
    wrapper_path = os.path.join(output_dir, "_cImageD11_wrapper.c")
    print("  GENERATING: %s" % wrapper_path, file=sys.stderr)
    mod = from_c2py_dict(assembled, "_cImageD11")
    wrapper_code = generate(mod)
    with open(wrapper_path, "w") as f:
        f.write(wrapper_code)


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Regenerate lib/interface/ from C sources + c2py23")
    parser.add_argument("--output-dir", required=True,
                        help="Output directory (e.g. lib/interface)")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    parent_dir = os.path.dirname(output_dir)
    src_dir = os.path.join(parent_dir, "functions")

    if not os.path.isdir(src_dir):
        print("ERROR: source directory not found: %s" % src_dir,
              file=sys.stderr)
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # 1. Assemble the interface dict
    assembled = assemble_c2py(src_dir, output_dir)

    # 2. Write _cImageD11.c2py in Python dict format (checked into git)
    c2py_path = os.path.join(output_dir, "_cImageD11.c2py")
    c2py_text = ("# c2py23 interface definition for c2ImageD11\n"
                 "#\n"
                 "# AUTO-ASSEMBLED by harvester.py from C2PY_BLOCKs in C sources.\n"
                 "# Python dict format -- load_c2py() auto-detects.\n"
                 "\n")
    c2py_text += _py_repr(assembled, 0) + "\n"
    with open(c2py_path, "w") as f:
        f.write(c2py_text)
    print("WROTE: %s (%d bytes)" % (c2py_path, len(c2py_text)),
          file=sys.stderr)

    # 3. Copy c2py23 runtime files
    copy_runtime(output_dir)

    # 4. Generate wrapper in-process
    generate_wrapper(assembled, output_dir)

    print("DONE", file=sys.stderr)


if __name__ == "__main__":
    main()
