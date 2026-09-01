"""Every example builds for the interpreter just-buildit is building FOR.

An example that asks its build system to *find* Python instead of taking the
one it is handed can build against the wrong ABI. just-buildit already tells
every build which interpreter to target -- `JUST_BUILDIT_PYTHON` and
`JUST_BUILDIT_INCLUDE_DIR` -- and two examples ignored both.

Measured on aarch64, with a uv-managed 3.12 as the target and the system
python3 at 3.14:

    examples/meson   built .cpython-314-...so; the copy step matched nothing
                     and the failure surfaced as "Build produced no
                     extension", pointing at the copy rather than the
                     interpreter.

    examples/cmake   found /usr/include/python3.14, compiled against those
                     headers, and -- because it forces SUFFIX from
                     JUST_BUILDIT_EXT_SUFFIX -- wrote
                     add.cpython-312-...so and exited 0.

The cmake one is the dangerous half: a right-NAMED, wrong-ABI extension that
succeeds at build time and fails at import. The meson one at least failed
loudly.

Neither is visible on CI, and that is the point: CI's default `python3` IS the
interpreter under test, so the two can never disagree there. The condition only
appears where they differ, which is every developer machine with a venv or a
uv-managed Python.

So this gate is STATIC. It does not need two interpreters, it runs everywhere,
and it asks the one question that separates the two designs: does this example
take the interpreter it is given, or go looking for one?
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

EXAMPLES = Path(__file__).parent.parent / "examples"

#: Build files worth reading. An example may have several.
_BUILD_FILES = (
    "CMakeLists.txt",
    "meson.build",
    "Makefile",
    "BUILD",
    "BUILD.bazel",
    "setup.py",
)

#: Asking the build system to locate a Python. Each of these returns an
#: interpreter or its headers chosen by SEARCH, which is the thing that can
#: disagree with the target.
_DISCOVERY = re.compile(
    r"""(
        find_package\s*\(\s*Python3?\b     # cmake
      | find_installation\s*\(             # meson
      | \bpython3-config\b                 # make / shell
      | \bwhich\s+python3?\b
    )""",
    re.VERBOSE,
)

#: The contract that says which interpreter to build for. Taking either one is
#: enough -- the executable steers the search, the include dir settles it.
_CONTRACT = re.compile(r"JUST_BUILDIT_(PYTHON|INCLUDE_DIR)\b")


def _example_dirs() -> list[Path]:
    return sorted(d for d in EXAMPLES.iterdir() if d.is_dir())


def _build_files(example: Path) -> list[Path]:
    out = []
    for name in _BUILD_FILES:
        p = example / name
        if p.is_file():
            out.append(p)
    return out


class TestExamplesTargetTheGivenInterpreter(unittest.TestCase):
    def test_there_are_examples_to_check(self):
        """A scan that finds nothing must be proven armed, not assumed so."""
        dirs = _example_dirs()
        self.assertGreater(len(dirs), 3, f"only found {dirs}")

    def test_the_discovery_pattern_matches_what_it_claims_to(self):
        """The other half of arming it: the pattern must actually recognise
        the two forms this was written for, or the gate below passes because
        it sees nothing rather than because nothing is wrong."""
        self.assertRegex(
            "find_package(Python3 COMPONENTS Development.Module REQUIRED)",
            _DISCOVERY,
        )
        self.assertRegex(
            "py = import('python').find_installation()", _DISCOVERY
        )
        self.assertNotRegex("add_library(add MODULE src/add.c)", _DISCOVERY)

    def test_an_example_that_searches_also_takes_the_contract(self):
        """The gate. An example may search -- cmake's `Python3_add_library`
        needs the found target -- but it must first be TOLD what to find, or
        the search silently answers a different question.

        Judged per EXAMPLE, not per file. meson is why: `meson.build` cannot
        read the environment, so it takes `get_option('python_path')` and the
        Makefile beside it passes `JUST_BUILDIT_PYTHON` through. Reading each
        file alone called that a violation when the contract is honoured --
        just across two files, which is the only way meson can honour it.
        """
        offenders = []
        for example in _example_dirs():
            files = _build_files(example)
            texts = {
                p: p.read_text(encoding="utf-8", errors="replace")
                for p in files
            }
            searches = [p for p, t in texts.items() if _DISCOVERY.search(t)]
            if not searches:
                continue
            if any(_CONTRACT.search(t) for t in texts.values()):
                continue
            offenders.append(
                f"{example.name}/ searches for a Python "
                f"({', '.join(p.name for p in searches)}) but no build file "
                f"in it reads JUST_BUILDIT_PYTHON or JUST_BUILDIT_INCLUDE_DIR"
            )
        self.assertEqual(
            [],
            offenders,
            "these can build against an interpreter other than the one "
            "just-buildit is building for:\n  " + "\n  ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
