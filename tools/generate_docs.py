#!/usr/bin/env python3
"""generate_docs.py — Generate API documentation from live module introspection.

Reads every exported C function from c2ImageD11, produces `docs/api/*.md`
pages with help() output, C2PY_BEGIN doc/params, and (when present)
function-specific example and benchmark output.

Usage:
    python tools/generate_docs.py              # generate docs/api/*.md
    python tools/generate_docs.py --dry-run    # validate only, no file writes
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import ast
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_DIR = os.path.join(HERE, "docs", "api")
FUNC_DIR = os.path.join(HERE, "lib", "functions")


def _find_c2py_begin_doc(source_path):
    """Extract 'doc' and 'params' from the first C2PY_BEGIN block in a .c file."""
    if not os.path.exists(source_path):
        return "", {}
    with open(source_path) as f:
        text = f.read()

    begin_re = re.compile(r"C2PY_BEGIN")
    end_re = re.compile(r"C2PY_END")
    lines = text.splitlines(True)
    i = 0
    while i < len(lines):
        if begin_re.search(lines[i]):
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
                block_text = re.sub(r"(?<=[\s,\[{:])true(?=\s*[\s,\]\}:])", "True", block_text)
                block_text = re.sub(r"(?<=[\s,\[{:])false(?=\s*[\s,\]\}:])", "False", block_text)
                try:
                    obj = ast.literal_eval(block_text)
                    if "py_sig" not in obj:
                        continue
                    doc = obj.get("doc", "")
                    params = obj.get("params", {})
                    checks = obj.get("checks", [])
                    return doc, params, checks
                except (ValueError, SyntaxError):
                    pass
            if i < len(lines):
                i += 1
        else:
            i += 1
    return "", {}, []


def _find_c_sources():
    """Map function names to their .c source files."""
    name_to_path = {}
    for root, dirs, files in os.walk(FUNC_DIR):
        for f in sorted(files):
            if f.endswith(".c") and not f.startswith("."):
                fp = os.path.join(root, f)
                name_to_path[os.path.basename(root)] = fp
                # Also map the .c filename (without .c) to the path
                # for functions where directory name != source file name
                c_name = f.replace(".c", "")
                name_to_path[c_name] = fp
    return name_to_path


def _gen_cpu_features_page():
    """Generate docs/api/cpu.md for the _c2py_has/set functions."""
    import c2ImageD11 as ci
    mod = ci._cImageD11

    arches = {
        "x86_64": [("sse4_1", "SSE4.1"), ("avx2", "AVX2"), ("avx512f", "AVX-512F")],
        "arm64": [("asimd", "ASIMD/NEON"), ("sve", "SVE"), ("sve2", "SVE2")],
        "ppc64": [("altivec", "AltiVec"), ("vsx", "VSX")],
    }

    lines = ["# CPU Feature Flags", ""]
    lines.append("Probed at module init by `c2py.h`. Modifiable at runtime for benchmarking.")
    lines.append("")

    for arch, flags in sorted(arches.items()):
        lines.append("## {}".format(arch))
        lines.append("")
        lines.append("| Flag | Supported | Has Function | Set Function |")
        lines.append("|------|-----------|-------------|-------------|")
        for suffix, label in flags:
            has_name = "_c2py_has_{}".format(suffix)
            set_name = "_c2py_set_{}".format(suffix)
            has_fn = getattr(mod, has_name, None)
            set_fn = getattr(mod, set_name, None)
            if has_fn:
                val = has_fn()
                status = "yes (current: {})".format(val) if val else "no"
                lines.append("| {} | {} | `{}()` | `{}(val)` |".format(
                    label, status, has_name, set_name))
        lines.append("")

    return "\n".join(lines)


def _format_help(name, fn):
    """Capture help(fn) output and format as markdown."""
    from io import StringIO
    old_stdout = sys.stdout
    s = StringIO()
    try:
        sys.stdout = s
        help(fn)
        sys.stdout = old_stdout
        text = s.getvalue()
    except Exception:
        sys.stdout = old_stdout
        text = "help() unavailable"
    return "```\n{}```".format(text.strip())


def _run_example(examples_path):
    """Run an examples.py file and capture stdout. Returns (code, output) or None."""
    if not os.path.exists(examples_path):
        return None
    result = subprocess.run(
        [sys.executable, examples_path],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.dirname(examples_path))
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _run_bench(bench_path):
    """Run a bench.py --md and capture stdout. Returns markdown table or None."""
    if not os.path.exists(bench_path):
        return None
    result = subprocess.run(
        [sys.executable, bench_path, "--md"],
        capture_output=True, text=True, timeout=120,
        cwd=os.path.dirname(bench_path))
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    if not output:
        return None
    return output


def _build_module_toc(functions):
    """Return a markdown table-of-contents listing all functions."""
    lines = ["# API Index", ""]
    lines.append("{} C functions exported by `c2ImageD11`.".format(len(functions)))
    lines.append("")
    for name in sorted(functions):
        lines.append("- [{}]({}.md)".format(name, name))
    return "\n".join(lines)


def generate(dry_run=False):
    """Generate all API documentation pages.

    Args:
        dry_run: If True, validate only; do not write files.
    Returns:
        Number of functions documented.
    """
    import c2ImageD11 as ci
    mod = ci._cImageD11

    # Identify C functions: not starting with _, callable, not the Python imports
    skip = {"absolute_import", "division", "print_function", "unicode_literals",
            "check_multiprocessing", "np", "os", "sys", "platform", "warnings",
            "importlib"}
    functions = sorted(n for n in dir(mod)
                       if not n.startswith("_")
                       and n not in skip
                       and callable(getattr(mod, n, None)))

    source_map = _find_c_sources()
    pages = {}

    for name in functions:
        fn = getattr(mod, name)
        lines = ["# `{}`".format(name), ""]
        lines.append(_format_help(name, fn))
        lines.append("")

        # Description and params from C2PY_BEGIN
        src_path = source_map.get(name)
        if src_path:
            doc, params, checks = _find_c2py_begin_doc(src_path)
            if doc:
                lines.append("## Description")
                lines.append("")
                lines.append(doc)
                lines.append("")
            if params:
                lines.append("## Parameters")
                lines.append("")
                lines.append("| Name | Description |")
                lines.append("|------|-------------|")
                for pname, pdesc in sorted(params.items()):
                    lines.append("| `{}` | {} |".format(pname, pdesc))
                lines.append("")
            if checks:
                lines.append("## Constraints")
                lines.append("")
                for c in checks:
                    lines.append("- `{}`".format(c))
                lines.append("")

        # Example section
        examples_path = os.path.join(FUNC_DIR, name, "examples.py")
        if os.path.exists(examples_path):
            example_output = _run_example(examples_path)
            if example_output:
                lines.append("## Example")
                lines.append("")
                lines.append("```")
                lines.append(example_output)
                lines.append("```")
                lines.append("")

        # Benchmark section
        bench_path = os.path.join(FUNC_DIR, name, "bench.py")
        if os.path.exists(bench_path):
            bench_output = _run_bench(bench_path)
            if bench_output:
                lines.append("## Performance")
                lines.append("")
                lines.append(bench_output)
                lines.append("")

        pages[name] = "\n".join(lines)

    # Write pages
    if dry_run:
        print("  Dry run: would write {} API pages".format(len(pages)))
    else:
        os.makedirs(API_DIR, exist_ok=True)
        for name, content in sorted(pages.items()):
            path = os.path.join(API_DIR, "{}.md".format(name))
            with open(path, "w") as f:
                f.write(content)
        print("  Wrote {} function pages to {}".format(len(pages), API_DIR))

    # API index
    index_content = _build_module_toc(functions)
    if dry_run:
        print("  Dry run: would write API index")
    else:
        path = os.path.join(API_DIR, "index.md")
        with open(path, "w") as f:
            f.write(index_content)

    # CPU features page
    cpu_content = _gen_cpu_features_page()
    if dry_run:
        print("  Dry run: would write CPU features page")
    else:
        path = os.path.join(API_DIR, "cpu.md")
        with open(path, "w") as f:
            f.write(cpu_content)

    return len(pages)


def write_mkdocs_nav(functions):
    """Write docs/mkdocs.yml with proper nav from function list."""
    api_pages = ["- API Index: api/index.md"]
    api_pages.append("- CPU Features: api/cpu.md")
    for name in sorted(functions):
        api_pages.append("- {}: api/{}.md".format(name, name))

    nav = """site_name: c2ImageD11
site_description: Standalone C extensions for ImageD11 (c2py23 binding)
theme:
  name: material
  features:
    - content.code.copy
    - search.highlight

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences

nav:
  - Home: index.md
  - Guide:
    - ISA Variants: guide/variants.md
    - Compiler Selection: guide/compiler.md
  - API Reference:
{}
""".format("\n".join("    " + p for p in api_pages))

    mkdocs_path = os.path.join(HERE, "docs", "mkdocs.yml")
    with open(mkdocs_path, "w") as f:
        f.write(nav)
    print("  Wrote docs/mkdocs.yml")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Generate c2ImageD11 API documentation")
    p.add_argument("--dry-run", action="store_true",
                   help="Validate without writing files")
    args = p.parse_args()

    print("Generating documentation...")
    count = generate(dry_run=args.dry_run)

    if not args.dry_run:
        # Identify functions for mkdocs nav
        import c2ImageD11 as ci
        mod = ci._cImageD11
        skip = {"absolute_import", "division", "print_function", "unicode_literals",
                "check_multiprocessing", "np", "os", "sys", "platform", "warnings",
                "importlib"}
        functions = sorted(n for n in dir(mod)
                           if not n.startswith("_")
                           and n not in skip
                           and callable(getattr(mod, n, None)))
        write_mkdocs_nav(functions)

    print("Done: {} functions documented".format(count))


if __name__ == "__main__":
    main()
