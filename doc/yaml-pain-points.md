# Pain Points Writing .c2py YAML by Hand

Documented from building the `score_bench` exploration (18 variants across
4 dispatch groups).  Status updated for c2py23 v0.2.0.

## Resolved by c2py23 v0.2.0

### 1. Format-check / type mismatch (RESOLVED)
c2py23 v0.2.0 correctly validates P4 across groups with mixed formats.
The rule: remove global format checks and rely on per-group `when:`.

### 3. Naming convention (RESOLVED)
Variant `name:` defaults to the C function name extracted from `sig:`.
Explicit `name:` must match C function name or be omitted entirely.
No more mapping table needed.

### 4. when: grammar undocumented (RESOLVED)
Full expression table in `docs/specification.md`.
`buf.strides[N]`, `buf.itemsize`, `buf.len`, `buf.slow_axis`,
`buf.fast_axis`, `buf.slow_dim`, `buf.fast_dim` all documented.

### 5. map: vs when: quoting (DOCUMENTED)
Rule: any value containing `.`, `[`, `(`, or whitespace must be quoted.
`tol: tol` (bare scalar) vs `ng: "gv.shape[0]"` (quotes for `.`).
Documented in c2py23 spec.

### 6. Variant ordering (RESOLVED)
c2py23 v0.2.0 adds `default: false` to skip auto-resolve.
Production variant is `default: true` (the default).
Ordering still matters among `default: true` variants at the same ISA.

### 8. Per-call vs init-time dispatch (RESOLVED)
c2py23 spec now clearly documents: group `when:` is per-call,
variant `when:` is init-time.  `default: false` makes the distinction
explicit.

### 9. default_raise noise (RESOLVED)
Buffer detail suffix removed.  User's message stands alone.

### 10. Contiguity enforcement (RESOLVED)
`buf.fast_axis` and `buf.slow_axis` (PEP 3118-native, no C/F labels)
let `when:` conditions check which axis has `stride == itemsize`.
No numpy naming convention imported.

## Still open (for the yaml harvester)

### 2. Source list drift
The `.c2py` `source:` list is used by c2py23 for validation and
compilation.  In the two-tier build, c2py23 generates the wrapper but
does not compile sources (meson does).  The `source:` list must still
match for P0 validation.  The yaml harvester must generate it from
the source file inventory.

### 7. Build system integration
With meson producing the final `.so`, the `.c2py` is an INTERMEDIATE
build artifact.  The harvester's output feeds c2py23 generate, which
feeds meson's compilation.  No double bookkeeping — one meson.build
owns the entire pipeline.

### 11. YAML validity
c2py23 uses pyyaml.  Expressions look like Python but are c2py23's
own grammar.  The `@c2py` comment block in C sources must be valid
YAML.  The harvester extracts and validates before assembly.
