# Configuration

## Full reference

```toml
[tool.just-build]
command = "make"         # optional — omit for zero-config src/{package}/ build
package = "my_package"  # optional — package directory name when it differs from project name
repair  = "uvx ..."     # optional — auto-detected by platform, or false to skip
exclude = [             # optional — glob patterns relative to $JUST_BUILD_OUTPUT_DIR
    "mypkg/tests/**",
    "mypkg/bench/**",
]
```

`__pycache__/`, `*.pyc`, and `*.pyo` are always excluded.

---

## Wheel repair

just-build automatically runs the right repair tool for your platform:

| Platform | Tool |
|---|---|
| Linux | `uvx auditwheel repair` |
| macOS | `uvx --from delocate delocate-wheel` |
| Windows / MinGW | `uvx delvewheel repair` |

Override or disable repair in your config:

```toml
[tool.just-build]
command = "make"
repair = "uvx auditwheel repair --plat manylinux_2_28_x86_64"  # custom
# repair = false  # skip entirely
```

---

## Editable installs

`pip install -e .` works. C extensions can't be truly editable — recompilation
is always required — so just-build builds a regular wheel and installs that.
The result is identical to `pip install .`.
