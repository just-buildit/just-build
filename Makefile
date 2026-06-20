# just-buildit — development control centre
#
# Targets:
#   make / make test           Run full test suite
#   make test-fast             Stop on first failure
#   make lint                  Run pre-commit hooks on all files
#   make build                 Build wheel → dist/
#   make docs                  Build docs site → site/
#   make docs-serve            Serve docs with live reload
#   make setup                 One-time per clone: uv sync + pre-commit install
#   make bump-version VERSION= Update version in pyproject.toml
#   make check-version VERSION= Verify version matches
#   make release-branch VERSION= Create release branch + bump
#   make tag-release VERSION=  Tag merged main + push to trigger release
#   make clean                 Remove build artifacts
#   make help                  Show this message

SHELL = /bin/sh
UV    = uv

.PHONY: all test test-fast lint build docs docs-serve setup \
        bump-version check-version release-branch tag-release \
        clean help

# ── default ───────────────────────────────────────────────────────────────────
all: test

# ── test ──────────────────────────────────────────────────────────────────────
test:
	$(UV) run --no-project python -m unittest \
	    tests.test_build tests.test_examples \
	    tests.test_cli tests.test_metadata -v

test-fast:
	$(UV) run --no-project python -m unittest --failfast \
	    tests.test_build tests.test_examples \
	    tests.test_cli tests.test_metadata

# ── lint ──────────────────────────────────────────────────────────────────────
lint:
	@test -f .git/hooks/pre-commit || pre-commit install
	$(UV) run pre-commit run --all-files

# ── build ─────────────────────────────────────────────────────────────────────
build:
	PYTHONPATH=src $(UV) build --wheel --no-build-isolation --python 3.11
	@echo ""
	@ls -lh dist/*.whl

# ── docs ──────────────────────────────────────────────────────────────────────
docs:
	$(UV) run --group dev zensical build --clean

docs-serve:
	$(UV) run --group dev zensical serve

# ── setup ─────────────────────────────────────────────────────────────────────
setup:
	$(UV) sync --group dev
	pre-commit install

# ── release ───────────────────────────────────────────────────────────────────
bump-version:
ifndef VERSION
	@echo "usage: make bump-version VERSION=<x.y.z>"
	@exit 1
endif
	sed -i 's/^version = "[^"]*"/version = "$(VERSION)"/' pyproject.toml
	@echo "Bumped to $(VERSION) in pyproject.toml"
	@echo "Next: edit CHANGELOG.md, commit, push PR, merge, then:"
	@echo "      git checkout main && git pull && make tag-release VERSION=$(VERSION)"

check-version:
ifndef VERSION
	@echo "usage: make check-version VERSION=<x.y.z>"
	@exit 1
endif
	@PY=$$(grep '^version = ' pyproject.toml | sed 's/.*"\(.*\)".*/\1/'); \
	 if [ "$$PY" != "$(VERSION)" ]; then \
	     echo "ERROR: pyproject.toml has $$PY, expected $(VERSION)"; exit 1; \
	 fi; \
	 echo "Version OK: $(VERSION)"

release-branch:
ifndef VERSION
	@echo "usage: make release-branch VERSION=<x.y.z>"
	@exit 1
endif
	git checkout -b chore/release-$(VERSION) origin/main
	$(MAKE) bump-version VERSION=$(VERSION)
	@echo "  - edit CHANGELOG.md ([Unreleased] -> [$(VERSION)] -- YYYY-MM-DD)"
	@echo "  - git commit -am 'chore: release v$(VERSION)', push PR, merge"
	@echo "  - then: git checkout main && git pull && make tag-release"

tag-release:
ifndef VERSION
	@echo "usage: make tag-release VERSION=<x.y.z>"
	@exit 1
endif
	@git fetch origin main
	@CURRENT=$$(git rev-parse HEAD); \
	 ORIGIN=$$(git rev-parse origin/main); \
	 if [ "$$CURRENT" != "$$ORIGIN" ]; then \
	     echo "ERROR: not at origin/main — checkout main and pull first"; \
	     exit 1; \
	 fi
	$(MAKE) check-version VERSION=$(VERSION)
	git tag -a "v$(VERSION)" -m "Release v$(VERSION)"
	git push origin "v$(VERSION)"
	@echo "Tagged v$(VERSION) — release workflow starting on GitHub"

# ── clean ─────────────────────────────────────────────────────────────────────
clean:
	rm -rf dist/ site/ .pytest_cache/
	find src -name "*.pyc" -delete
	find src -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true

# ── help ──────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  just-buildit development"
	@echo ""
	@echo "  make setup                       one-time: uv sync + pre-commit install"
	@echo "  make test                         run full test suite"
	@echo "  make test-fast                    stop on first failure"
	@echo "  make lint                         run pre-commit hooks on all files"
	@echo "  make build                        build wheel → dist/"
	@echo "  make docs                         build docs → site/"
	@echo "  make docs-serve                   serve docs with live reload"
	@echo "  make bump-version VERSION=x.y.z   update version in pyproject.toml"
	@echo "  make check-version VERSION=x.y.z  verify version matches"
	@echo "  make release-branch VERSION=x.y.z create release branch"
	@echo "  make tag-release VERSION=x.y.z    tag + push to trigger release"
	@echo "  make clean                        remove build artifacts"
	@echo ""
