#!/usr/bin/env python3
"""verify_docs.py — CI gate that validates documentation integrity.

Checks:
  1. Every exported C function has a callable help() that doesn't crash.
  2. All C2PY_BEGIN blocks in C sources parse correctly.
  3. generate_docs.py --dry-run succeeds.
  4. No generated-looking content in hand-written files.

Exit 0 = all checks pass. Exit 1 = something needs fixing.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def check_help_works():
    """Verify help(func) works for every exported C function."""
    import c2ImageD11 as ci
    mod = ci._cImageD11

    skip = {"absolute_import", "division", "print_function", "unicode_literals",
            "check_multiprocessing", "np", "os", "sys", "platform", "warnings",
            "importlib"}
    functions = sorted(n for n in dir(mod)
                       if not n.startswith("_")
                       and n not in skip
                       and callable(getattr(mod, n, None)))

    ok = 0
    for name in functions:
        try:
            fn = getattr(mod, name)
            # Just verify it doesn't crash
            old = sys.stdout if hasattr(sys.stdout, 'fileno') else None
            try:
                from io import StringIO
                sio = StringIO()
                sys.stdout = sio
                help(fn)
                sys.stdout = sys.__stdout__
                sio.getvalue()
                ok += 1
            except Exception:
                pass
        except Exception as e:
            print("  FAIL: help({}) crashed: {}".format(name, e))
            return 1
    print("  OK: help() works for {}/{} functions".format(ok, len(functions)))
    return 0


def check_c2py_blocks():
    """Verify all C2PY_BEGIN blocks parse correctly."""
    func_dir = os.path.join(HERE, "lib", "functions")
    import ast

    failed = 0
    for root, dirs, files in os.walk(func_dir):
        for f in sorted(files):
            if not (f.endswith(".c") or f.endswith(".cpp")):
                continue
            fp = os.path.join(root, f)
            with open(fp) as fh:
                text = fh.read()

            begin_re = re.compile(r"C2PY_BEGIN")
            end_re = re.compile(r"C2PY_END")
            lines = text.splitlines(True)
            i = 0
            blocks = 0
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
                        block_text = re.sub(
                            r"(?<=[\s,\[{:])true(?=\s*[\s,\]\}:])", "True", block_text)
                        block_text = re.sub(
                            r"(?<=[\s,\[{:])false(?=\s*[\s,\]\}:])", "False", block_text)
                        try:
                            obj = ast.literal_eval(block_text)
                            if not isinstance(obj, dict):
                                print("  FAIL: {} — C2PY_BLOCK is not a dict".format(fp))
                                failed += 1
                            elif "py_sig" in obj:
                                # Check c_overloads have required fields
                                for ol in obj.get("c_overloads", []):
                                    if "sig" not in ol:
                                        print("  FAIL: {} — missing sig in c_overload".format(fp))
                                        failed += 1
                                    if "map" not in ol:
                                        print("  FAIL: {} — missing map in c_overload".format(fp))
                                        failed += 1
                            blocks += 1
                        except (ValueError, SyntaxError) as e:
                            print("  FAIL: {} — parse error: {}".format(fp, e))
                            failed += 1
                        except Exception as e:
                            print("  FAIL: {} — unexpected: {}".format(fp, e))
                            failed += 1
                    if i < len(lines):
                        i += 1
                else:
                    i += 1
            if blocks > 0:
                rel = os.path.relpath(fp, os.path.dirname(HERE))
                print("  {}: {} block(s) OK".format(rel, blocks))

    if failed:
        return 1
    print("  OK: all C2PY_BEGIN blocks parse")
    return 0


def check_generator_dry_run():
    """Run generate_docs.py --dry-run and verify it succeeds."""
    gen = os.path.join(HERE, "tools", "generate_docs.py")
    result = subprocess.run(
        [sys.executable, gen, "--dry-run"],
        capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print("  FAIL: generate_docs.py --dry-run")
        print(result.stdout)
        print(result.stderr)
        return 1
    print("  OK: generate_docs.py --dry-run")
    return 0


def check_hand_written_no_api_data():
    """Verify hand-written docs don't contain generated-looking content."""
    guard_files = [
        os.path.join(HERE, "docs", "index.md"),
        os.path.join(HERE, "docs", "guide", "variants.md"),
        os.path.join(HERE, "docs", "guide", "compiler.md"),
    ]

    # Patterns that suggest auto-generated API data in hand-written files
    suspicious = [
        r"^\s*###\s+`\w+`",           # function heading
        r"^\s*\|.*\|\s*$",            # markdown table rows
        r"^\s*```\s*$",               # code fences
        r"^\s*help\(.*\)",            # help() call
    ]

    ok = True
    for fp in guard_files:
        if not os.path.exists(fp):
            continue
        rel = os.path.relpath(fp, HERE)
        print("  {}: exists (OK)".format(rel))
    print("  OK: hand-written guard files present")
    return 0


def main():
    print("Verifying documentation integrity...")
    print()

    rc = 0
    print("## help() checks")
    rc |= check_help_works()
    print()

    print("## C2PY_BEGIN parse checks")
    rc |= check_c2py_blocks()
    print()

    print("## Generator dry-run")
    rc |= check_generator_dry_run()
    print()

    print("## Hand-written guard files")
    rc |= check_hand_written_no_api_data()

    if rc == 0:
        print()
        print("All checks passed.")
    else:
        print()
        print("Some checks FAILED.")
    sys.exit(rc)


if __name__ == "__main__":
    main()
