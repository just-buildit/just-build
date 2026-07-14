"""
_meta.py — parse pyproject.toml for just-buildit.

Extracts:
  - project.name
  - project.version
  - project.description           (optional -> METADATA Summary)
  - project.readme                (optional -> METADATA Description
                                    + content-type)
  - project.requires-python       (optional -> METADATA Requires-Python)
  - project.license               (optional -> METADATA License /
                                    License-File)
  - project.authors               (optional -> METADATA Author /
                                    Author-email)
  - project.maintainers           (optional -> METADATA Maintainer /
                                    Maintainer-email)
  - project.dependencies          (optional -> METADATA Requires-Dist)
  - project.optional-dependencies (optional -> METADATA Provides-Extra
                                    + Requires-Dist)
  - tool.just-buildit.command        (optional; omit for zero-config
                                       src/{name}/ default)
  - tool.just-buildit.pure           (optional; True = pure-Python: copy
                                       src/{name}/ verbatim, compile nothing)
  - tool.just-buildit.repair         (optional; auto-detected if omitted,
                                       False to skip)
  - tool.just-buildit.editable_path  (optional; src root for .pth editable
                                       installs; defaults to src/ if present)
"""

from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 has no stdlib tomllib
    from ._vendor import tomli as tomllib

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

_CONTENT_TYPES = {
    ".md": "text/markdown",
    ".rst": "text/x-rst",
    ".txt": "text/plain",
}


@dataclass
class BuildConfig:
    name: str
    version: str
    command: str | None  # None = zero-config src/{package}/ default
    pure: bool = (
        False  # True = pure-Python: copy tree verbatim, compile nothing
    )
    repair: str | Literal[False] | None = None  # None = auto-detect
    repair_args: list[str] = field(
        default_factory=list
    )  # extra args passed to the repair command
    package: str | None = (
        None  # package dir name; defaults to normalized project name
    )
    exclude: list[str] = field(default_factory=list)
    editable_path: str | None = (
        None  # src root for .pth-file editable installs
    )
    scripts: dict[str, str] = field(default_factory=dict)
    summary: str | None = None
    readme_text: str | None = None
    readme_content_type: str | None = None
    requires_python: str | None = None
    classifiers: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    urls: dict[str, str] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    # PEP 621 author/maintainer/license/extras
    license_expression: str | None = (
        None  # project.license string or {text=...}
    )
    license_files: list[str] = field(
        default_factory=list
    )  # project.license {file=...}
    authors: list[dict[str, str]] = field(default_factory=list)
    maintainers: list[dict[str, str]] = field(default_factory=list)
    optional_dependencies: dict[str, list[str]] = field(default_factory=dict)


def _read_readme(
    project_root: Path, raw: str | dict[str, Any]
) -> tuple[str | None, str | None]:
    """Return (text, content_type) from a project.readme value."""
    if isinstance(raw, str):
        path = project_root / raw
        text = path.read_text(encoding="utf-8") if path.exists() else None
        content_type = _CONTENT_TYPES.get(
            Path(raw).suffix.lower(), "text/plain"
        )
        return text, content_type
    # table form: {file = "..."} or {text = "...", content-type = "..."}
    content_type = raw.get("content-type", "text/plain")
    if "file" in raw:
        path = project_root / raw["file"]
        text = path.read_text(encoding="utf-8") if path.exists() else None
    else:
        text = raw.get("text")
    return text, content_type


def _parse_license(
    project: dict[str, Any],
) -> tuple[str | None, list[str]]:
    """Return (license_expression, license_files) from the project table.

    Handles three PEP 621 forms:
    - String: ``license = "MIT"`` -> expression "MIT", no files.
    - Dict with text: ``license = {text = "MIT"}`` -> expression "MIT",
      no files.
    - Dict with file: ``license = {file = "LICENSE"}`` -> no expression,
      ["LICENSE"].
    """
    raw = project.get("license")
    if raw is None:
        return None, []
    if isinstance(raw, str):
        return raw, []
    if isinstance(raw, dict):
        expr = raw.get("text") or None
        files = [raw["file"]] if "file" in raw else []
        return expr, files
    return None, []


def load(project_root: Path) -> BuildConfig:
    toml_path = project_root / "pyproject.toml"
    if not toml_path.exists():
        raise FileNotFoundError(f"No pyproject.toml found in {project_root}")

    with toml_path.open("rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})

    name = project.get("name")
    if not name:
        raise ValueError("[project] name is required in pyproject.toml")

    version = project.get("version")
    if not version:
        raise ValueError("[project] version is required in pyproject.toml")

    jb = data.get("tool", {}).get("just-buildit", {})

    command = (
        jb.get("command") or None
    )  # None -> zero-config src/{package}/ default
    pure = bool(
        jb.get("pure", False)
    )  # pure-Python: copy tree verbatim, no compile
    if pure and command:
        raise ValueError(
            "[tool.just-buildit] sets both 'pure' and 'command'.\n"
            "'pure' means compile nothing — drop 'command', or drop 'pure'."
        )
    package = (
        jb.get("package") or None
    )  # override package dir name for src/ lookup
    editable_path = (
        jb.get("editable_path") or None
    )  # src root for .pth editable installs
    scripts = project.get("scripts", {})
    exclude = jb.get("exclude", [])

    repair: str | Literal[False] | None
    if "repair" not in jb:
        repair = None  # auto-detect
    elif jb["repair"] is False:
        repair = False  # explicitly disabled
    else:
        repair = str(jb["repair"])

    raw_repair_args = jb.get("repair-args", [])
    if isinstance(raw_repair_args, str):
        import shlex

        repair_args = shlex.split(raw_repair_args)
    else:
        repair_args = list(raw_repair_args)

    readme_text, readme_content_type = None, None
    raw_readme = project.get("readme")
    if raw_readme:
        readme_text, readme_content_type = _read_readme(
            project_root, raw_readme
        )

    license_expression, license_files = _parse_license(project)

    return BuildConfig(
        name=name,
        version=version,
        command=command,
        pure=pure,
        repair=repair,
        repair_args=repair_args,
        package=package,
        exclude=exclude,
        editable_path=editable_path,
        scripts=scripts,
        summary=project.get("description") or None,
        readme_text=readme_text,
        readme_content_type=readme_content_type,
        requires_python=project.get("requires-python") or None,
        classifiers=project.get("classifiers", []),
        keywords=project.get("keywords", []),
        urls=project.get("urls", {}),
        dependencies=project.get("dependencies", []),
        license_expression=license_expression,
        license_files=license_files,
        authors=project.get("authors", []),
        maintainers=project.get("maintainers", []),
        optional_dependencies=project.get("optional-dependencies", {}),
    )
