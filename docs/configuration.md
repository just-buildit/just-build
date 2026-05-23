# Configuration

## Full reference

```toml
[tool.just-buildit]
command       = "make"        # optional — omit for zero-config src/{package}/ build
pure          = true          # optional — pure-Python: copy src/{package}/ verbatim, compile nothing
package       = "my_package"  # optional — package dir name when it differs from project name
editable_path = "src"         # optional — src root for fast .pth-file editable installs
repair        = "uvx ..."     # optional — auto-detected by platform, or false to skip
repair-args   = ["--plat", "manylinux_2_28_x86_64"]  # optional — extra args appended to the repair command
exclude = [                   # optional — glob patterns relative to $JUST_BUILDIT_OUTPUT_DIR
    "mypkg/tests/**",
    "mypkg/bench/**",
]
```

`__pycache__/`, `*.pyc`, and `*.pyo` are always excluded.

---

## Pure-Python packages

A zero-config build compiles every `.c` file it finds under
`src/{package}/`. That is wrong for a pure-Python package that *ships* `.c`
files as data (sample sources, test fixtures, scaffolding templates) — they
must land in the wheel untouched, not be handed to a compiler.

Set `pure = true` to tell just-buildit the package is pure Python:

```toml
[tool.just-buildit]
pure = true
```

With `pure = true`, just-buildit:

- compiles nothing — the `.c` scan is skipped entirely;
- copies the whole `src/{package}/` tree verbatim into the wheel, **keeping**
  any `.c`/`.h` files as package data;
- tags the wheel `py3-none-any` (`Root-Is-Purelib: true`);
- skips the wheel-repair step — a pure wheel has no native binary to repair.

`pure` and `command` are mutually exclusive: `pure` means "compile nothing",
so a build command makes no sense alongside it.

---

## Wheel repair

just-buildit automatically runs the right repair tool for your platform:

| Platform | Tool |
|---|---|
| Linux | `uvx auditwheel repair` |
| macOS | `uvx --from delocate delocate-wheel` |
| Windows / MinGW | `uvx delvewheel repair` |

Override or disable repair in your config:

```toml
[tool.just-buildit]
command = "make"
repair  = "uvx auditwheel repair"          # override the auto-detected command
# repair = false                           # skip repair entirely
```

Pass extra arguments without replacing the whole command using `repair-args`.
The args are appended after the wheel path:

```toml
[tool.just-buildit]
command     = "make"
repair-args = ["--plat", "manylinux_2_28_x86_64"]
```

Accepts either a list of strings or a single space-separated string:

```toml
repair-args = "--plat manylinux_2_28_x86_64 --strip"
```

---

## Editable installs

Set `editable_path` to the directory that should be added to `sys.path`:

```toml
[tool.just-buildit]
command       = "make"
editable_path = "src"
```

`pip install -e .` then installs a single `.pth` file pointing at `src/` —
no build command is run. Python finds your source directly. The C extension
must be compiled in place once (e.g. `make`) before importing.

Without `editable_path`, `pip install -e .` falls back to a full wheel build.
