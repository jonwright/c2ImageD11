#!/usr/bin/env python3
"""migrate_docs.py -- Carry ImageD11 docstrings into c2ImageD11 C2PY_BEGIN blocks."""
from __future__ import absolute_import, division, print_function, unicode_literals
import ast, os, re, sys

DOCS_PATH = "/home/worker/ImageD11/ImageD11/cImageD11_docstrings.py"
FUNC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lib", "functions")

NAME_MAP = {
    "checks": "verify_rounding", "overlaps": "coverlaps",
    "computes_xlylzl": "compute_xlylzl", "reorderlut_u16_a32lut": "reorderlut_u16_a32",
}

def load_old_docs():
    if not os.path.exists(DOCS_PATH):
        print("WARNING: %s not found" % DOCS_PATH, file=sys.stderr); return {}
    with open(DOCS_PATH) as f:
        text = f.read()
    docs = {}
    for m in re.finditer(r'^(\w+)\s*=\s*"""\s*(.*?)\s*"""\s*$', text, re.DOTALL | re.MULTILINE):
        name = m.group(1); doc = m.group(2).strip()
        if doc:
            docs[name] = doc
    return docs

def escape_for_json(s):
    """Escape a Python string to a single-line JSON string value suitable for C source."""
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')

def func_name_from_sig(py_sig):
    m = re.match(r"(\w+)\(.*\)", py_sig)
    return m.group(1) if m else None

def apply_doc(filepath, old_docs):
    with open(filepath) as f:
        lines = f.readlines()
    modified = False
    i = 0
    while i < len(lines):
        if "C2PY_BEGIN" in lines[i]:
            start = i
            i += 1
            content = []
            while i < len(lines) and "C2PY_END" not in lines[i]:
                content.append(lines[i]); i += 1
            end = i
            # Parse the block to find py_sig
            block_lines = [re.sub(r'^\s*\*\s?', '', ln.rstrip("\n\r")) for ln in content]
            block_text = "\n".join(block_lines).strip()
            if block_text:
                block_text = re.sub(r'(?<=[\s,\[{:])true(?=\s*[\s,\]\}:])', 'True', block_text)
                block_text = re.sub(r'(?<=[\s,\[{:])false(?=\s*[\s,\]\}:])', 'False', block_text)
                try:
                    obj = ast.literal_eval(block_text)
                except Exception:
                    i += 1; continue
                if isinstance(obj, dict) and "py_sig" in obj:
                    fname = obj["py_sig"].split("(")[0].strip()
                    lookup = NAME_MAP.get(fname, fname)
                    old_doc = old_docs.get(lookup)
                    if old_doc:
                        current_doc = obj.get("doc", "")
                        if len(current_doc) >= len(old_doc) * 0.8:
                            i += 1; continue
                        # Find the "doc" line and replace
                        doc_pat = re.compile(r'^(\s*\*\s*"doc":\s*)"[^"]*"(.*)$')
                        for j in range(start + 1, end):
                            m = doc_pat.match(lines[j])
                            if m:
                                new_escaped = m.group(1) + '"' + escape_for_json(old_doc) + '"' + m.group(2) + "\n"
                                if lines[j] != new_escaped:
                                    print("  %-30s %d -> %d chars" % (fname, len(current_doc), len(old_doc)))
                                    lines[j] = new_escaped
                                    modified = True
                                break
            i += 1
        else:
            i += 1
    if modified:
        with open(filepath, "w") as f:
            f.writelines(lines)
        return 1
    return 0

def main():
    old_docs = load_old_docs()
    print("Loaded %d old docstrings\n" % len(old_docs))
    updated = 0
    for root, dirs, files in os.walk(FUNC_DIR):
        for fn in sorted(files):
            if fn.endswith(".c") or fn.endswith(".cpp"):
                fp = os.path.join(root, fn)
                try:
                    updated += apply_doc(fp, old_docs)
                except Exception as e:
                    print("ERROR: %s - %s" % (fp, e), file=sys.stderr)
    print("\nUpdated %d/%d functions" % (updated, len(old_docs)))

if __name__ == "__main__":
    main()
