def _isa_levels(when_str):
    """Return (isa_flag, stripped_when) if the when condition contains an ISA flag."""
    import re
    isa_flags = [
        "c2py_amd64_avx512f",
        "c2py_amd64_avx2",
        "c2py_amd64_sse4_1",
    ]
    for flag in isa_flags:
        if flag in when_str:
            # Remove the flag and its surrounding 'and' connector
            # Pattern: " and flag" or "flag and " or just "flag"
            stripped = re.sub(
                r'\s+and\s+' + re.escape(flag) + r'\b', '', when_str)
            stripped = re.sub(
                r'\b' + re.escape(flag) + r'\s+and\s+', '', stripped)
            stripped = re.sub(
                r'\s+and\s+' + re.escape(flag) + r'$', '', stripped)
            stripped = re.sub(
                r'^' + re.escape(flag) + r'\s+and\s+', '', stripped)
            stripped = re.sub(
                r'\b' + re.escape(flag) + r'\b', '', stripped)  # lone flag
            # Clean up double spaces, leading/trailing whitespace
            stripped = re.sub(r'\s{2,}', ' ', stripped).strip()
            # Clean up trailing "and" or leading "and"
            stripped = re.sub(r'\s+and\s*$', '', stripped).strip()
            stripped = re.sub(r'^\s*and\s+', '', stripped).strip()
            return flag, stripped
    return None, when_str


def _group_isa_variants(func_entries):
    """Group overloads that differ only in ISA flag into variants: groups."""
    for py_sig, entry in func_entries.items():
        overloads = entry.get("c_overloads", [])
        if len(overloads) < 2:
            continue

        # First pass: label each overload with its ISA flag and stripped when
        labelled = []
        for ol in overloads:
            w = ol.get("when", "")
            flag, stripped = _isa_levels(w)
            labelled.append((stripped, flag, ol))

        # Group by stripped when
        groups = {}
        for stripped, flag, ol in labelled:
            if stripped not in groups:
                groups[stripped] = []
            groups[stripped].append((flag, ol))

        # If all overloads map to a single group (all same stripped when), skip
        if len(groups) >= len(overloads):
            continue

        # Second pass: build variant groups
        new_overloads = []
        for stripped, items in groups.items():
            if len(items) == 1 and items[0][0] is None:
                # Solo non-ISA overload -- keep as flat
                new_overloads.append(items[0][1])
                continue

            # Check that all items have the same outputs structure
            # (same keys in outputs dict, otherwise can't group)
            outputs_keys = None
            compatible = True
            for _flag, ol in items:
                ol_outputs = frozenset(ol.get("outputs", {}).keys())
                if outputs_keys is None:
                    outputs_keys = ol_outputs
                elif ol_outputs != outputs_keys:
                    compatible = False
                    break
            if not compatible:
                # Can't group -- outputs differ. Keep as flat overloads.
                for _flag, ol in items:
                    new_overloads.append(ol)
                continue

            # Multiple items with same stripped when — merge into variants
            # Sort by ISA priority: avx512 > avx2 > sse41 > none
            priority = {
                "c2py_amd64_avx512f": 0,
                "c2py_amd64_avx2": 1,
                "c2py_amd64_sse4_1": 2,
                None: 3,
            }
            items.sort(key=lambda x: priority.get(x[0], 99))

            # Build the grouped overload
            base_ol = items[0][1]  # first as template for map
            variants = []
            seen_default = False
            for flag, ol in items:
                variant = {"sig": ol["sig"]}
                if flag:
                    variant["when"] = flag
                elif not seen_default:
                    seen_default = True
                else:
                    variant["default"] = False
                # Carry forward per-variant outputs
                if "outputs" in ol:
                    variant["outputs"] = ol["outputs"]
                variants.append(variant)

            grouped = {
                "when": stripped,
                "map": base_ol.get("map", {}),
                "variants": variants,
            }
            if "group" in base_ol:
                grouped["group"] = base_ol["group"]
            new_overloads.append(grouped)

        entry["c_overloads"] = new_overloads
