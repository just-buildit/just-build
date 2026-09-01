# just-buildit — configuration only.
#
# The shared targets are NOT written here. `standard.mk` is vendored from the
# cross-org standard (canonical: https://just-buildit.github.io/standard.mk)
# and this file is feature flags and command variables.
#
# It used to be 135 lines that reimplemented THIRTEEN of the standard's
# fourteen targets by hand -- including a hand-written `help` listing them,
# which is what let `make wheel` stay advertised in doppler after its rule was
# gone. `help` is generated from the `## description` on each rule now, so it
# cannot disagree with what exists.
#
# Two targets changed name in the move, and nothing called either one -- no
# workflow, README or doc invokes `make` in this repo:
#   make build         -> make wheel          (`build` is the native-library
#                                              target in the standard)
#   make check-version -> make version-check
#
# Never edit standard.mk or anything in VENDORED_FILES in place: the
# `standard-check` drift gate holds them to canonical byte-for-byte. Per-repo
# variation is a variable here; a shared change goes to canonical and comes
# back through the vendored copy.

HAS_PYTHON  = 1
HAS_DOCS    = 1
HAS_RELEASE = 1

UV         = uv
DEV_RUN    = $(UV) run --group dev
SYNC_CMD   = $(UV) sync --group dev

# ── test ─────────────────────────────────────────────────────────────────────
# `--no-project` deliberately: the suite exercises the INSTALLED entry points
# rather than the working tree, so resolving this project into the environment
# would test something the user never runs.
#
# `--with pip --with numpy` is not decoration: `TestJustMakeitExample`
# scaffolds a just-makeit project and builds it, which needs both. The
# Makefile omitted them while ci.yml supplied them, so `make test` could NOT
# pass in this repo -- it failed in `setUpClass` with `make just-build` exit 2
# while CI was green, and the same command run CI's way passes. That is the
# drift a hand-maintained second copy of the test command produces; the
# standard's `gates-check` is what holds them together, and adopting it is the
# follow-up.
_TEST_RUN     = $(UV) run --no-project --with pip --with numpy python
_TEST_MODULES = tests.test_build tests.test_examples \
                tests.test_examples_target_interpreter \
                tests.test_cli tests.test_metadata
TEST_CMD      = $(_TEST_RUN) -m unittest $(_TEST_MODULES) -v
TEST_FAST_CMD = $(_TEST_RUN) -m unittest --failfast $(_TEST_MODULES)

# ── wheel ────────────────────────────────────────────────────────────────────
# PYTHONPATH=src and --no-build-isolation because the build backend imports the
# package it is building; --python 3.11 pins the interpreter the wheel is
# produced with.
WHEEL_CMD = PYTHONPATH=src $(UV) build --wheel --no-build-isolation \
                --python 3.11

# ── docs ─────────────────────────────────────────────────────────────────────
DOCS_CMD = $(ZENSICAL) build --clean

# ── clean ────────────────────────────────────────────────────────────────────
CLEAN_PATHS = dist site .pytest_cache
CLEAN_CMD   = find src -name '*.pyc' -delete; \
              find src -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null; true

# ── release ──────────────────────────────────────────────────────────────────
PROJECT = just-buildit

BUMP_VERSION_CMD = sed -i 's/^version = "[^"]*"/version = "$(VERSION)"/' \
                       pyproject.toml

# Every file that states the version, and how to read it back. `version-check`
# fails when any two disagree, so a bump that misses a file is caught before
# the tag rather than by a consumer.
define VERSION_PROBES
pyproject.toml|grep '^version = ' pyproject.toml | sed 's/.*"\(.*\)".*/\1/'
endef

# The release watcher is VENDORED from canonical and gated by standard-check;
# everything repo-specific is here.
#
# This repo previously had NO watcher: `tag-release` pushed the tag, printed
# "release workflow starting on GitHub", and stopped. Nothing followed the run,
# nothing recovered a pre-publish flake, and nothing verified that PyPI or the
# GitHub Release actually carried the version.
RELEASE_WATCH_CMD = REPO=just-buildit/just-buildit RW_PKG=just-buildit \
                        scripts/release-watch.sh "$(VERSION)"

# ── Vendored from canonical ──────────────────────────────────────────────────
# Verbatim copies the drift gate holds to canonical, alongside standard.mk
# itself. Edit canonical and re-vendor; never edit these in place.
VENDORED_FILES = scripts/release-watch.sh

include standard.mk
