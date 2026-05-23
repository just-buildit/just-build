# Configuration

## Full reference

```toml
[tool.just-buildit]
command       = "make"        # optional — omit for zero-config src/{package}/ build
pure          = true          # optional — pure-Python: copy src/{package}/ verbatim, compile nothing
package       = "my_package"  # optional — package dir; defaults to normalized project name
editable_path = "src"         # optional — src root for .pth editable installs; auto-detected as src/ if present
repair        = "uvx ..."     # optional — auto-detected by platform, or false to skip
repair-args   = ["--plat", "manylinux_2_28_x86_64"]  # optional — extra args appended to the repair command
exclude = [                   # optional — glob patterns relative to $JUST_BUILDIT_OUTPUT_DIR
    "mypkg/tests/**",
    "mypkg/bench/**",
]
```

`__pycache__/`, `*.pyc`, and `*.pyo` are always excluded.

!!! note "Package directory name"

    If `package` is omitted, the directory name is derived from
    `[project] name` by replacing runs of non-alphanumeric characters with
    underscores and lower-casing — the same rule Python uses for import
    names. A project named `my-lib` will look for `src/my_lib/`.

!!! info "`.c` and `.h` files in the wheel"

    In a normal (non-`pure`) build, `.c` and `.h` files are **excluded from
    the wheel** — they compile into the extension and have no place in the
    distribution.

    Set `pure = true` to keep them as package data (useful when shipping C
    source templates or scaffolding examples alongside Python code).

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

- compiles nothing — the `.c` scan is skipped entirely
- copies the whole `src/{package}/` tree verbatim into the wheel, **keeping**
  any `.c`/`.h` files as package data
- tags the wheel `py3-none-any` (`Root-Is-Purelib: true`)
- skips the wheel-repair step — a pure wheel has no native binary to repair

!!! failure "Cannot combine `pure` and `command`"

    Setting both is a configuration error:

    ```
    [tool.just-buildit] sets both 'pure' and 'command'.
    'pure' means compile nothing — drop 'command', or drop 'pure'.
    ```

    `pure` means "compile nothing and copy the source tree verbatim."
    A build `command` is only needed when there is something to compile.

---

## Wheel repair

just-buildit automatically runs the right repair tool for your platform:

| Platform | Auto-detected command |
|:---|:---|
| **Linux** | `uvx auditwheel repair` |
| **macOS** | `uvx --from delocate delocate-wheel` |
| **Windows / MinGW** | `uvx delvewheel repair` |

Override or disable repair in your config:

```toml
[tool.just-buildit]
command = "make"
repair  = "uvx auditwheel repair"   # override the auto-detected command
# repair = false                    # skip repair entirely
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

`pip install -e .` installs a single `.pth` file pointing at your source
tree — no build command is run. Python finds your source directly. The C
extension must be compiled in place once (e.g. `make`) before importing.

!!! tip "Standard src-layout: zero config needed"

    If `editable_path` is not set and a `src/` directory exists at the
    project root, just-buildit uses it automatically:

    ```toml
    [tool.just-buildit]
    command = "make"
    # editable_path = "src"  ← omit; auto-detected when src/ exists
    ```

Set `editable_path` explicitly only when your source root differs from `src/`:

```toml
[tool.just-buildit]
command       = "make"
editable_path = "lib"     # non-standard layout
```

!!! warning "Fallback to full wheel build"

    If neither `editable_path` is set nor a `src/` directory exists,
    `pip install -e .` falls back to a full wheel build — slower and
    not truly editable for Python changes.
