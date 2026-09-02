"""
Tests that the sdist carries source and not build output.

The exclusion list is a list of NAMES, so the only way to know it covers a
directory is to put that directory in a tree and build from it. Asserting on
`_EXCLUDE_DIRS` itself would restate the constant and pass for any value of
it -- including the one that shipped `_build/` (#25).
"""

import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

SRC = Path(__file__).parent.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from just_buildit import _meta, _sdist

# Every directory the walk must prune, with the spelling a real tree uses.
# `_build` is here because it was NOT, and every example's Makefile builds
# into it: a local sdist of this repo carried 62 entries of object files and
# ninja logs. CI builds from a fresh checkout, so the release path was blind
# to it.
BUILD_DIRS = ("build", "_build", "dist", "__pycache__", ".git")


def _project(root: Path) -> None:
    """Write a minimal buildable project, then dirty it with build output."""
    (root / "pyproject.toml").write_text(
        '[build-system]\nrequires = ["just-buildit"]\n'
        'build-backend = "just_buildit"\n\n'
        '[project]\nname = "demo"\nversion = "0.1.0"\n\n'
        '[tool.just-buildit]\npackage = "demo"\n',
        encoding="utf-8",
    )
    pkg = root / "src" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")

    # Real source that must survive.
    ex = root / "examples" / "cmake"
    ex.mkdir(parents=True)
    (ex / "CMakeLists.txt").write_text("# source\n", encoding="utf-8")

    # Build output that must not, at both top level and nested under an
    # example -- the nested one is the shape that actually shipped.
    for d in BUILD_DIRS:
        for parent in (root, ex):
            out = parent / d
            out.mkdir(parents=True, exist_ok=True)
            (out / "artifact.o").write_text("junk\n", encoding="utf-8")


class TestSdistExcludesBuildOutput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name) / "proj"
        root.mkdir()
        _project(root)
        out = Path(cls._tmp.name) / "dist"
        out.mkdir()
        cfg = _meta.load(root)
        archive = _sdist.build_sdist(root, out, cfg)
        with tarfile.open(archive) as tf:
            cls._names = tf.getnames()

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_source_survives(self):
        """The exclusion must not be so broad it drops real files."""
        self.assertTrue(
            any(
                n.endswith("examples/cmake/CMakeLists.txt")
                for n in self._names
            ),
            f"real source missing from sdist: {self._names}",
        )

    def test_no_build_output_anywhere(self):
        """No excluded directory contributes an entry, at any depth."""
        for d in BUILD_DIRS:
            leaked = [n for n in self._names if f"/{d}/" in n]
            self.assertEqual(
                leaked, [], f"sdist carries {d}/ output (see #25): {leaked}"
            )

    def test_no_artifact_files(self):
        """Belt and braces: the junk filename itself must be absent."""
        leaked = [n for n in self._names if n.endswith("artifact.o")]
        self.assertEqual(leaked, [], f"build artifacts in sdist: {leaked}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
