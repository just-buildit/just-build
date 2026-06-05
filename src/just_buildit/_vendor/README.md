# Vendored dependencies

just-buildit ships zero runtime dependencies. To parse `pyproject.toml` on
Python 3.8–3.10 (which lack the stdlib `tomllib`, added in 3.11), we vendor
`tomli` instead of declaring a dependency.

## tomli

- **Source**: https://pypi.org/project/tomli/ (sdist `tomli-2.0.1.tar.gz`)
- **Version**: 2.0.1
- **License**: MIT (see `tomli/LICENSE`)
- **Modifications**: none — vendored verbatim from the upstream `src/tomli/`.

On Python 3.11+ the stdlib `tomllib` is used instead; this copy is only
imported as a fallback (see `just_buildit/_meta.py`).
