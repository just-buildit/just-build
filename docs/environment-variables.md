# Environment variables

## Variables set by just-buildit

just-buildit sets these before calling your build command:

| Variable | Example value | Description |
|---|---|---|
| `JUST_BUILDIT_NAME` | `mylib` | Normalized package name (used to name the output file) |
| `JUST_BUILDIT_PYTHON` | `/usr/bin/python3.12` | Path to the Python interpreter running the build |
| `JUST_BUILDIT_INCLUDE_DIR` | `/usr/include/python3.12` | Python header directory; pass as `-I$JUST_BUILDIT_INCLUDE_DIR` |
| `JUST_BUILDIT_OUTPUT_DIR` | `/tmp/just-buildit-xyz/output` | Wheel content root — write all output here |
| `JUST_BUILDIT_EXT_SUFFIX` | `.cpython-312-x86_64-linux-gnu.so` | Platform extension suffix; use as the filename suffix for `.so`/`.pyd` files |

### Platform-specific link flags

| Variable | Linux | macOS | Windows (MinGW) |
|---|---|---|---|
| `JUST_BUILDIT_LDFLAGS` | `-shared -fPIC` | `-dynamiclib -undefined dynamic_lookup` | `-shared` |
| `JUST_BUILDIT_LIBS` | *(empty)* | *(empty)* | `-L/ucrt64/lib -lpython3.14` |

`JUST_BUILDIT_LIBS` is only non-empty when a custom `command` is configured
**and** the platform is Windows/MinGW (where Python's import library must be
linked explicitly). On Linux and macOS it is always empty — linker flags in
`JUST_BUILDIT_LDFLAGS` are sufficient. Always place `$JUST_BUILDIT_LIBS`
**after** the output file (`-o`) in your linker invocation; GNU `ld`'s
`--as-needed` will silently drop it otherwise.

`$JUST_BUILDIT_OUTPUT_DIR` is the wheel content root. Write everything your
wheel needs there — extensions, Python sources, data files. just-buildit
packages the entire directory verbatim, preserving structure.

---

## Variables read by just-buildit

These are not set by just-buildit, but are read from the environment if present:

| Variable | Default | Description |
|---|---|---|
| `CC` | `cc` | C compiler used for zero-config builds (no `command` set). Override to select a specific compiler: `CC=gcc pip install .` |
| `SOURCE_DATE_EPOCH` | *(current time)* | Unix timestamp for reproducible wheel and sdist builds. Set to a fixed value to make archive timestamps deterministic. Standard [build-reproducibility](https://reproducible-builds.org/docs/source-date-epoch/) env var. |
