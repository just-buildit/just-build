# Changelog

## [0.3.6] — 2026-05-19

### Added

- `pure` option in `[tool.just-buildit]` — declares a pure-Python package: just-buildit compiles nothing, copies the `src/{package}/` tree verbatim (keeping `.c`/`.h` files as package data), tags the wheel `py3-none-any`, and skips wheel repair. For pure-Python packages that ship `.c` sources as data, where the zero-config build would otherwise try to compile them.
- `TestPureBuild` integration tests and a `fixture_pure/` test fixture (ships an uncompilable `sample.c` to prove pure builds never invoke the compiler)

### Changed

- `[tool.just-buildit]` rejects setting both `pure` and `command` — `pure` means "compile nothing", so a build command is contradictory

---

## [0.3.5] — 2026-05-10

### Added

- MinGW UCRT64 example (`examples/mingw/`) — explicit Makefile build demonstrating `JUST_BUILDIT_LIBS` placement after `-o` on Windows
- `TestMinGWExample` (Windows-only) and `TestJustMakeitExample` integration tests
- CI `test-just-makeit` job: scaffolds a project with `just-makeit new`, verifies layout, builds wheel, and smoke-tests `my_dsp.Gain`

### Fixed

- `examples/meson/meson.build`: added `build_by_default: true` — without it, `install: false` implies `build_by_default: false` since Meson 0.38, causing ninja to produce no output
- `examples/meson/Makefile`: changed `--reconfigure` to `--wipe` so a clean configure is forced each build
- CI `test` job: install meson via `uv tool install meson` instead of `apt-get install meson` — apt meson 1.3.x silently produces no build targets when `find_installation()` encounters a uv-managed Python path

### Docs

- `examples.md` overhauled: every section now shows actual runnable code from `examples/`, browse links, prerequisite lists, and `pip install` smoke-test commands
- `environment-variables.md`: corrected `JUST_BUILDIT_LDFLAGS` for Windows/MinGW — it is `-shared` (not `-shared -fPIC`); `-fPIC` is meaningless on Windows x64
- `examples.md` just-makeit section updated: `--component` → `--object`, config file is `just-makeit.toml`, layout tree reflects current scaffold output

---

## [0.3.4] — 2026-05-07

### Added

- `repair-args` config option in `[tool.just-buildit]` — accepts a list or string of extra arguments passed to the wheel repair command (e.g. `--plat manylinux_2_28_x86_64` for `auditwheel repair`)

---

## [0.3.3] — 2026-05-06

### Fixed

- Sdist `PKG-INFO` now includes classifiers, keywords, project URLs, and dependencies (previously only written into wheel `METADATA`)
- `__version__` now derived from installed package metadata instead of a hardcoded string

---

## [0.3.2] — 2026-05-06

### Fixed

- Classifiers, keywords, project URLs, and dependencies were parsed from `pyproject.toml` but never written into the wheel METADATA or sdist PKG-INFO — they now appear correctly on PyPI

---

## [0.3.1] — 2026-05-05

### Added

- PyPI metadata: keywords, classifiers (Python 3.11–3.14), project URLs (Homepage, Documentation, Changelog)
- README: just-makeit callout and cross-link for projects needing a CMake scaffold

---

## [0.3.0] — 2026-04-30

### Added

- Bazel example (`examples/bazel/`) — `genrule`-based build with a `build_ext.py` bridge script forwarding just-buildit env vars via `--action_env`
- Nested package example (`examples/nested/`) — recursive package tree with multiple extensions across subdirectories
- CLI integration tests (`tests/test_cli.py`) — 15 tests covering `inspect`, `build`, `sdist`, `help`, and error handling via subprocess
- CI: dedicated `test-bazel` job running the Bazel example across all Python versions

### Docs

- Env variable table split into platform-neutral and platform-specific sections
- Examples page updated with Bazel and recursive package tree sections
- Quickstart updated to call out flat, nested, multi-extension, and mixed layouts
- PyPI doc links updated to point to GitHub Pages

---

## [0.2.1] — 2026-04-15

### Breaking

- Renamed config section from `[tool.just-build]` to `[tool.just-buildit]`

---

## [0.2.0] — 2026-04-15

### Breaking

- Renamed Python module from `just_build` to `just_buildit`. Update your `pyproject.toml`:
  ```toml
  [build-system]
  requires = ["just-buildit"]
  build-backend = "just_buildit"   # was: just_build
  ```
- Renamed all environment variables from `JUST_BUILD_*` to `JUST_BUILDIT_*`. Update your Makefiles and build scripts:
  - `JUST_BUILD_NAME` → `JUST_BUILDIT_NAME`
  - `JUST_BUILD_PYTHON` → `JUST_BUILDIT_PYTHON`
  - `JUST_BUILD_INCLUDE_DIR` → `JUST_BUILDIT_INCLUDE_DIR`
  - `JUST_BUILD_OUTPUT_DIR` → `JUST_BUILDIT_OUTPUT_DIR`
  - `JUST_BUILD_EXT_SUFFIX` → `JUST_BUILDIT_EXT_SUFFIX`
  - `JUST_BUILD_LDFLAGS` → `JUST_BUILDIT_LDFLAGS`
  - `JUST_BUILD_LIBS` → `JUST_BUILDIT_LIBS`

### Added

- CLI entry point: `just-buildit inspect`, `just-buildit build [DIR]`, `just-buildit sdist [DIR]`
  - `inspect` shows parsed config, build mode, env vars, and predicted wheel filename without running anything
  - `build` builds a wheel into the given directory (default: `dist/`)
  - `sdist` builds a source distribution into the given directory (default: `dist/`)
- `build_sdist()` / `get_requires_for_build_sdist()` — PEP 517 sdist support

---

## [0.1.5] — 2026-04-03

### Fixed

- Don't delete the original wheel when the repair tool writes an output file with the same filename

---

## [0.1.4] — 2026-04-03

### Fixed

- Repair into a temp subdirectory to avoid a `PermissionError` on Windows when pip holds the source wheel open

---

## [0.1.3] — 2026-04-02

### Fixed

- MSYS2 Python 3.14: search `lib/` and check `.dll.a` suffix for link flags
- Windows native CPython link flags via `libs/python3X.lib`
- CI: release gate, example Makefile fixes

---

## [0.1.2] — 2026-04-02

### Added

- `editable_path` config option: `build_editable()` writes a `.pth` file instead of rebuilding, enabling instant `uv sync` for projects with C extensions compiled in place

---

## [0.1.1] — 2026-04-02

### Added

- Initial release on PyPI
- Zero-config `src/{package}/*.c` auto-discovery and compilation
- PEP 517 `build_wheel()` and `build_editable()`
- Platform auto-repair: auditwheel (Linux), delocate (macOS), delvewheel (Windows)
- Pure Python detection: no `*{ext_suffix}` in output → `py3-none-any` tags
