## Python polyglot compatibility (2.7 / 3.x)

Target the intersection of Python 2.7 and 3.x. Code must run on the system Python 3
and pass lint under Python 2.7 rules.

### Tooling

- **Run**: system `python3` (3.12)
- **Lint**: pyright with `pythonVersion: "2.7"` in `pyrightconfig.json`
- **Verify 2.7 syntax**: `~/.pyenv/versions/2.7.18/bin/python -m py_compile *.py`

### pyrightconfig.json

```json
{
  "pythonVersion": "2.7",
  "typeCheckingMode": "basic"
}
```

### Avoid (Python-3-only)

- f-strings (`f"hello {name}"`)
- `async` / `await`
- type annotations (`def foo(x: int) -> str:`)
- `print()` as the only print syntax — use `print x` for 2.7, or `from __future__ import print_function`
- `nonlocal`
- keyword-only arguments (`def foo(*, bar):`)
- `yield from`
- `except Exc as e` — OK in both
- `@` matrix multiplication operator
- `pathlib`, `unittest.mock`, `concurrent.futures` (3.x stdlib only)

### Do (works in both)

- `from __future__ import print_function, division, absolute_import, unicode_literals` at the top of every file
- Use `.format()` instead of f-strings: `"hello {}".format(name)`
- `try/except/finally`
- `class Foo(object):` (explicit `object` base for new-style classes)
- `super(ClassName, self).__init__()`
- `isinstance()`, `issubclass()`, `hasattr()`, `getattr()`, `setattr()`
- `iteritems()` / `items()` — prefer `items()` with `from __future__ import absolute_import` and check

### Strings

- Prefer `u"unicode"` for text on 2.7; it's a no-op on 3.x
- Use `b"bytes"` for raw bytes
- `str` means bytes on 2.7, unicode on 3.x — be explicit

### Imports

```python
from __future__ import absolute_import, division, print_function, unicode_literals
import sys
import os
import io

if sys.version_info[0] >= 3:
    unicode = str
    raw_input = input
else:
    input = raw_input
```

### File I/O

```python
import io
with io.open("file.txt", "r", encoding="utf-8") as f:
    content = f.read()
```
