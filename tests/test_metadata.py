"""
Unit tests for metadata generation (_meta.load, _wheel._metadata_bytes) and
integration tests verifying METADATA file content in built wheels/sdists.

Covers every PEP 621 field that just-buildit maps to wheel METADATA:
  - name, version, summary, readme, requires-python
  - license (string, {text=}, {file=})
  - authors, maintainers (name-only, email-only, name+email)
  - classifiers, keywords, urls
  - dependencies (Requires-Dist)
  - optional-dependencies (Provides-Extra + Requires-Dist with extras)
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

SRC = Path(__file__).parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from just_buildit import _meta, _wheel


def _load(toml: str, project_root: Path | None = None) -> _meta.BuildConfig:
    """Write toml to a temp dir and load it, returning the BuildConfig."""
    if project_root is None:
        with tempfile.TemporaryDirectory(prefix="jb-meta-") as tmp:
            (Path(tmp) / "pyproject.toml").write_text(toml)
            return _meta.load(Path(tmp))
    (project_root / "pyproject.toml").write_text(toml)
    return _meta.load(project_root)


def _meta_str(**kwargs) -> str:
    """Return decoded _metadata_bytes output for easy assertions."""
    return _wheel._metadata_bytes("pkg", "1.0", **kwargs).decode()


class TestMetadataBytesCore(unittest.TestCase):
    """_metadata_bytes — required and basic optional fields."""

    def test_required_headers_present(self):
        out = _meta_str()
        self.assertIn("Metadata-Version: 2.1", out)
        self.assertIn("Name: pkg", out)
        self.assertIn("Version: 1.0", out)

    def test_summary(self):
        out = _meta_str(summary="A cool package")
        self.assertIn("Summary: A cool package", out)

    def test_no_summary_omitted(self):
        out = _meta_str()
        self.assertNotIn("Summary:", out)

    def test_requires_python(self):
        out = _meta_str(requires_python=">=3.11")
        self.assertIn("Requires-Python: >=3.11", out)

    def test_classifiers(self):
        out = _meta_str(classifiers=["Programming Language :: Python :: 3"])
        self.assertIn("Classifier: Programming Language :: Python :: 3", out)

    def test_keywords(self):
        out = _meta_str(keywords=["dsp", "audio"])
        self.assertIn("Keywords: dsp,audio", out)

    def test_urls(self):
        out = _meta_str(urls={"Homepage": "https://example.com"})
        self.assertIn("Project-URL: Homepage, https://example.com", out)

    def test_readme_body_and_content_type(self):
        out = _meta_str(
            readme_text="# Hello",
            readme_content_type="text/markdown",
        )
        self.assertIn("Description-Content-Type: text/markdown", out)
        self.assertIn("# Hello", out)

    def test_blank_line_before_body(self):
        out = _meta_str(readme_text="body")
        # Blank line must separate headers from body
        self.assertIn("\n\nbody", out)

    def test_blank_line_present_without_body(self):
        out = _meta_str()
        self.assertTrue(out.endswith("\n"))


class TestMetadataBytesRequiresDist(unittest.TestCase):
    """Requires-Dist — dependencies and optional-dependencies."""

    def test_single_dependency(self):
        out = _meta_str(dependencies=["numpy>=2.0.0"])
        self.assertIn("Requires-Dist: numpy>=2.0.0", out)

    def test_multiple_dependencies(self):
        out = _meta_str(dependencies=["numpy>=2.0.0", "scipy>=1.10.0"])
        self.assertIn("Requires-Dist: numpy>=2.0.0", out)
        self.assertIn("Requires-Dist: scipy>=1.10.0", out)

    def test_no_dependencies_no_header(self):
        out = _meta_str()
        self.assertNotIn("Requires-Dist:", out)

    def test_optional_dependencies_provides_extra(self):
        out = _meta_str(optional_dependencies={"dev": ["pytest", "black"]})
        self.assertIn("Provides-Extra: dev", out)

    def test_optional_dependencies_requires_dist_with_marker(self):
        out = _meta_str(optional_dependencies={"dev": ["pytest"]})
        self.assertIn('Requires-Dist: pytest ; extra == "dev"', out)

    def test_optional_multiple_extras(self):
        out = _meta_str(
            optional_dependencies={
                "dev": ["pytest"],
                "docs": ["sphinx"],
            }
        )
        self.assertIn("Provides-Extra: dev", out)
        self.assertIn("Provides-Extra: docs", out)
        self.assertIn('Requires-Dist: pytest ; extra == "dev"', out)
        self.assertIn('Requires-Dist: sphinx ; extra == "docs"', out)

    def test_optional_no_extras_no_provides(self):
        out = _meta_str()
        self.assertNotIn("Provides-Extra:", out)


class TestMetadataBytesLicense(unittest.TestCase):
    """License header and License-File."""

    def test_license_expression(self):
        out = _meta_str(license_expression="MIT")
        self.assertIn("License: MIT", out)

    def test_no_license_omitted(self):
        out = _meta_str()
        self.assertNotIn("License:", out)

    def test_license_file(self):
        out = _meta_str(license_files=["LICENSE"])
        self.assertIn("License-File: LICENSE", out)

    def test_license_file_no_expression(self):
        out = _meta_str(license_files=["LICENSE"])
        self.assertNotIn("License: ", out)

    def test_license_expression_and_file(self):
        out = _meta_str(
            license_expression="MIT",
            license_files=["LICENSE"],
        )
        self.assertIn("License: MIT", out)
        self.assertIn("License-File: LICENSE", out)


class TestMetadataBytesContacts(unittest.TestCase):
    """Author and Maintainer headers — name-only, email-only, name+email."""

    def test_author_name_only(self):
        out = _meta_str(authors=[{"name": "Alice"}])
        self.assertIn("Author: Alice", out)
        self.assertNotIn("Author-email:", out)

    def test_author_email_only(self):
        out = _meta_str(authors=[{"email": "alice@example.com"}])
        self.assertIn("Author-email: alice@example.com", out)
        self.assertNotIn("Author: ", out)

    def test_author_name_and_email(self):
        out = _meta_str(
            authors=[{"name": "Alice", "email": "alice@example.com"}]
        )
        self.assertIn("Author-email: Alice <alice@example.com>", out)

    def test_multiple_authors(self):
        out = _meta_str(
            authors=[
                {"name": "Alice"},
                {"name": "Bob", "email": "bob@example.com"},
            ]
        )
        self.assertIn("Author: Alice", out)
        self.assertIn("Author-email: Bob <bob@example.com>", out)

    def test_maintainer_name_only(self):
        out = _meta_str(maintainers=[{"name": "Carol"}])
        self.assertIn("Maintainer: Carol", out)

    def test_maintainer_name_and_email(self):
        out = _meta_str(
            maintainers=[{"name": "Carol", "email": "carol@example.com"}]
        )
        self.assertIn("Maintainer-email: Carol <carol@example.com>", out)

    def test_no_authors_no_header(self):
        out = _meta_str()
        self.assertNotIn("Author", out)
        self.assertNotIn("Maintainer", out)

    def test_empty_dict_author_ignored(self):
        out = _meta_str(authors=[{}])
        self.assertNotIn("Author", out)


class TestParseLicense(unittest.TestCase):
    """_meta._parse_license — all three PEP 621 license forms."""

    def test_string_form(self):
        expr, files = _meta._parse_license({"license": "MIT"})
        self.assertEqual(expr, "MIT")
        self.assertEqual(files, [])

    def test_dict_text(self):
        expr, files = _meta._parse_license({"license": {"text": "MIT"}})
        self.assertEqual(expr, "MIT")
        self.assertEqual(files, [])

    def test_dict_file(self):
        expr, files = _meta._parse_license(
            {"license": {"file": "LICENSE.txt"}}
        )
        self.assertIsNone(expr)
        self.assertEqual(files, ["LICENSE.txt"])

    def test_absent(self):
        expr, files = _meta._parse_license({})
        self.assertIsNone(expr)
        self.assertEqual(files, [])


class TestMetaLoad(unittest.TestCase):
    """_meta.load — pyproject.toml parsing for all relevant fields."""

    def _tmpload(self, toml: str) -> _meta.BuildConfig:
        with tempfile.TemporaryDirectory(prefix="jb-meta-") as tmp:
            (Path(tmp) / "pyproject.toml").write_text(toml)
            return _meta.load(Path(tmp))

    def test_dependencies_parsed(self):
        cfg = self._tmpload(
            '[project]\nname="pkg"\nversion="1.0"\n'
            'dependencies = ["numpy>=2.0", "scipy>=1.10"]\n'
        )
        self.assertEqual(cfg.dependencies, ["numpy>=2.0", "scipy>=1.10"])

    def test_optional_dependencies_parsed(self):
        cfg = self._tmpload(
            '[project]\nname="pkg"\nversion="1.0"\n'
            "[project.optional-dependencies]\n"
            'dev = ["pytest", "black"]\n'
            'docs = ["sphinx"]\n'
        )
        self.assertEqual(cfg.optional_dependencies["dev"], ["pytest", "black"])
        self.assertEqual(cfg.optional_dependencies["docs"], ["sphinx"])

    def test_license_string_parsed(self):
        cfg = self._tmpload(
            '[project]\nname="pkg"\nversion="1.0"\nlicense = "MIT"\n'
        )
        self.assertEqual(cfg.license_expression, "MIT")
        self.assertEqual(cfg.license_files, [])

    def test_license_dict_text_parsed(self):
        cfg = self._tmpload(
            '[project]\nname="pkg"\nversion="1.0"\n'
            '[project.license]\ntext = "Apache-2.0"\n'
        )
        self.assertEqual(cfg.license_expression, "Apache-2.0")

    def test_license_dict_file_parsed(self):
        cfg = self._tmpload(
            '[project]\nname="pkg"\nversion="1.0"\n'
            '[project.license]\nfile = "LICENSE"\n'
        )
        self.assertIsNone(cfg.license_expression)
        self.assertEqual(cfg.license_files, ["LICENSE"])

    def test_authors_parsed(self):
        cfg = self._tmpload(
            '[project]\nname="pkg"\nversion="1.0"\n'
            '[[project.authors]]\nname = "Alice"\nemail = "a@example.com"\n'
        )
        self.assertEqual(
            cfg.authors, [{"name": "Alice", "email": "a@example.com"}]
        )

    def test_maintainers_parsed(self):
        cfg = self._tmpload(
            '[project]\nname="pkg"\nversion="1.0"\n'
            '[[project.maintainers]]\nname = "Bob"\n'
        )
        self.assertEqual(cfg.maintainers, [{"name": "Bob"}])

    def test_no_deps_defaults_empty(self):
        cfg = self._tmpload('[project]\nname="pkg"\nversion="1.0"\n')
        self.assertEqual(cfg.dependencies, [])
        self.assertEqual(cfg.optional_dependencies, {})
        self.assertEqual(cfg.authors, [])
        self.assertEqual(cfg.maintainers, [])
        self.assertIsNone(cfg.license_expression)
        self.assertEqual(cfg.license_files, [])


class TestPrepareMetadataContent(unittest.TestCase):
    """prepare_metadata_for_build_wheel — METADATA file content end-to-end."""

    def _prepare(self, toml: str) -> str:
        import just_buildit

        with tempfile.TemporaryDirectory(prefix="jb-meta-") as tmp:
            tmpdir = Path(tmp)
            (tmpdir / "pyproject.toml").write_text(toml)
            meta_dir = tmpdir / "meta"
            meta_dir.mkdir()
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                dist_info_name = just_buildit.prepare_metadata_for_build_wheel(
                    str(meta_dir)
                )
                return (meta_dir / dist_info_name / "METADATA").read_text()
            finally:
                os.chdir(orig)

    def test_requires_dist_in_metadata(self):
        meta = self._prepare(
            '[project]\nname="pkg"\nversion="1.0"\n'
            'dependencies = ["numpy>=2.0.0"]\n'
        )
        self.assertIn("Requires-Dist: numpy>=2.0.0", meta)

    def test_no_requires_dist_when_no_deps(self):
        meta = self._prepare('[project]\nname="pkg"\nversion="1.0"\n')
        self.assertNotIn("Requires-Dist:", meta)

    def test_optional_deps_in_metadata(self):
        meta = self._prepare(
            '[project]\nname="pkg"\nversion="1.0"\n'
            '[project.optional-dependencies]\ndev = ["pytest"]\n'
        )
        self.assertIn("Provides-Extra: dev", meta)
        self.assertIn('Requires-Dist: pytest ; extra == "dev"', meta)

    def test_license_in_metadata(self):
        meta = self._prepare(
            '[project]\nname="pkg"\nversion="1.0"\nlicense = "MIT"\n'
        )
        self.assertIn("License: MIT", meta)

    def test_author_in_metadata(self):
        meta = self._prepare(
            '[project]\nname="pkg"\nversion="1.0"\n'
            '[[project.authors]]\nname = "Alice"\nemail = "a@example.com"\n'
        )
        self.assertIn("Author-email: Alice <a@example.com>", meta)

    def test_maintainer_in_metadata(self):
        meta = self._prepare(
            '[project]\nname="pkg"\nversion="1.0"\n'
            '[[project.maintainers]]\nname = "Bob"\n'
        )
        self.assertIn("Maintainer: Bob", meta)


class TestWheelMetadataContent(unittest.TestCase):
    """build_wheel — METADATA content in a pure-Python wheel (no compiler)."""

    def _build_pure_meta(self, extra_toml: str = "") -> str:
        """Build a no-op pure wheel and return the METADATA contents."""
        import just_buildit

        with tempfile.TemporaryDirectory(prefix="jb-whl-") as tmp:
            tmpdir = Path(tmp)
            toml = (
                '[project]\nname="pkg"\nversion="1.0"\n'
                + extra_toml
                + "[tool.just-buildit]\npure = true\nrepair = false\n"
            )
            (tmpdir / "pyproject.toml").write_text(toml)
            src = tmpdir / "src" / "pkg"
            src.mkdir(parents=True)
            (src / "__init__.py").write_text("")
            wheel_dir = tmpdir / "dist"
            wheel_dir.mkdir()
            orig = os.getcwd()
            os.chdir(tmpdir)
            try:
                wheel_name = just_buildit.build_wheel(str(wheel_dir))
            finally:
                os.chdir(orig)
            wheel_path = wheel_dir / wheel_name
            with zipfile.ZipFile(wheel_path) as zf:
                meta_name = next(
                    n for n in zf.namelist() if n.endswith("/METADATA")
                )
                return zf.read(meta_name).decode()

    def test_requires_dist_in_wheel(self):
        meta = self._build_pure_meta('dependencies = ["requests>=2.0"]\n')
        self.assertIn("Requires-Dist: requests>=2.0", meta)

    def test_no_requires_dist_when_no_deps(self):
        meta = self._build_pure_meta()
        self.assertNotIn("Requires-Dist:", meta)

    def test_optional_deps_in_wheel(self):
        meta = self._build_pure_meta(
            '[project.optional-dependencies]\ndev = ["pytest"]\n'
        )
        self.assertIn("Provides-Extra: dev", meta)
        self.assertIn('Requires-Dist: pytest ; extra == "dev"', meta)

    def test_license_in_wheel(self):
        meta = self._build_pure_meta('license = "MIT"\n')
        self.assertIn("License: MIT", meta)

    def test_author_name_email_in_wheel(self):
        meta = self._build_pure_meta(
            '[[project.authors]]\nname="Eve"\nemail="e@example.com"\n'
        )
        self.assertIn("Author-email: Eve <e@example.com>", meta)

    def test_license_file_in_wheel(self):
        meta = self._build_pure_meta('[project.license]\nfile = "LICENSE"\n')
        self.assertIn("License-File: LICENSE", meta)


if __name__ == "__main__":
    unittest.main(verbosity=2)
