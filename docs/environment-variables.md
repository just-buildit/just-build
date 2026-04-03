# Environment variables

just-build sets these before calling your command:

| Variable | Example value |
|---|---|
| `JUST_BUILD_NAME` | `mylib` |
| `JUST_BUILD_PYTHON` | `/usr/bin/python3.12` |
| `JUST_BUILD_INCLUDE_DIR` | `/usr/include/python3.12` |
| `JUST_BUILD_OUTPUT_DIR` | `/tmp/just-build-xyz/output` |
| `JUST_BUILD_EXT_SUFFIX` | `.cpython-312-x86_64-linux-gnu.so` |
| `JUST_BUILD_LDFLAGS` | `-shared -fPIC` (Linux) / `-dynamiclib -undefined dynamic_lookup` (macOS) |
| `JUST_BUILD_LIBS` | `` (Linux/macOS) / `-L/ucrt64/lib -lpython3.14` (Windows/MinGW) |

`$JUST_BUILD_OUTPUT_DIR` is the wheel content root. Write everything your
wheel needs there — extensions, Python sources, data files. just-build
packages the entire directory verbatim, preserving structure.
