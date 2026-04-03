<p align="center">
  <img src="docs/assets/logo-wordmark.svg" alt="just-build" width="480">
</p>

Minimum viable [PEP 517](https://peps.python.org/pep-0517/) build backend for C extensions.

You know how to build your project. just-build knows how to package it.
That's the whole deal.

---

## The problem

Every existing Python build backend either wants to own your build system,
assumes you're using setuptools extensions, or drags in a dependency tree
bigger than your project. There's no option that just says:

> "Here are your C files. Build them however you want. I'll ship the result."

just-build is that option.

---

## Zero-config

Got a single C extension in `src/mylib/`? No configuration needed:

```toml
[build-system]
requires = ["just-buildit"]
build-backend = "just_build"

[project]
name = "mylib"
version = "0.1.0"
```

Run `pip install .` and just-build will find `src/mylib/`, compile every `.c`
file it contains, and ship the result.

---

## Custom build command

For anything more complex, tell it your build command:

```toml
[build-system]
requires = ["just-buildit"]
build-backend = "just_build"

[project]
name = "mylib"
version = "0.1.0"

[tool.just-build]
command = "make"
```

just-build sets five environment variables, calls your command, packages
everything your command writes to `$JUST_BUILD_OUTPUT_DIR`, and ships the
result.

---

## Environment variables

just-build sets these before calling your command:

| Variable | Example value |
|---|---|
| `JUST_BUILD_NAME` | `mylib` |
| `JUST_BUILD_PYTHON` | `/usr/bin/python3.12` |
| `JUST_BUILD_INCLUDE_DIR` | `/usr/include/python3.12` |
| `JUST_BUILD_OUTPUT_DIR` | `/tmp/just-build-xyz/output` |
| `JUST_BUILD_EXT_SUFFIX` | `.cpython-312-x86_64-linux-gnu.so` |

`$JUST_BUILD_OUTPUT_DIR` is the wheel content root. Write everything your
wheel needs there — extensions, Python sources, data files. just-build
packages the entire directory verbatim, preserving structure.

---

## Makefile example

```makefile
TARGET := $(JUST_BUILD_OUTPUT_DIR)/$(JUST_BUILD_NAME)$(JUST_BUILD_EXT_SUFFIX)

all: $(TARGET)

$(TARGET):
	$(CC) -shared -fPIC \
		-I$(JUST_BUILD_INCLUDE_DIR) \
		src/mylib/mylib.c \
		-o $(TARGET)
```

For multi-extension or mixed Python/C projects, write the whole package tree:

```makefile
just-build: pyext
	cp -r python/mylib $(JUST_BUILD_OUTPUT_DIR)/mylib
```

---

## Wheel repair

just-build automatically runs the right repair tool for your platform:

| Platform | Tool |
|---|---|
| Linux | `uvx auditwheel repair` |
| macOS | `uvx delocate-wheel` |
| Windows / MinGW | `uvx delvewheel repair` |

Override or disable repair in your config:

```toml
[tool.just-build]
command = "make"
repair = "uvx auditwheel repair --plat manylinux_2_28_x86_64"  # custom
# repair = false  # skip entirely
```

---

## Full configuration reference

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

## Requirements

- Python 3.11+
- A compiler (you already have one)
- `uv` for wheel repair (`uvx auditwheel` / `uvx delocate-wheel` / `uvx delvewheel`)

---

## Running the tests

```sh
python -m unittest tests.test_build -v
```

No dependencies required. The test suite builds a real C extension, verifies
the wheel structure, imports the extension, and confirms it produces correct
results.

---

## Bootstrapping (offline or pre-release)

just-build is a pure Python package with no dependencies. If you need it
before it can be fetched from PyPI — air-gapped environment, initial release
bootstrap, or simply testing a local change — add the source directly to your
path:

```sh
git clone https://github.com/just-buildit/just-build.git
export PYTHONPATH=/path/to/just-build/src:$PYTHONPATH
```

Then use your build frontend with `--no-isolation` so it picks up the local
copy:

```sh
pip install --no-build-isolation .
# or
python -m build --wheel --no-isolation
# or
uv build --no-build-isolation
```

No build step, no compiler, no install required. `src/just_build/` is
importable as-is.

---

## License

MIT
