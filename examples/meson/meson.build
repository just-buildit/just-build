project('add', 'c')
# Build for the interpreter just-buildit is building FOR. `find_installation()`
# with no argument takes whatever meson finds, which is a different Python
# whenever the build runs under a venv or a uv-managed interpreter while
# another python3 leads PATH. meson then builds a working extension with the
# WRONG ABI suffix, the copy step below matches nothing, and the failure
# surfaces as "Build produced no extension" -- pointing at the copy rather than
# at the interpreter.
#
# meson.build cannot read the environment, so the Makefile passes it through
# this option. The default keeps the example runnable standalone.
py = import('python').find_installation(get_option('python_path'))
py.extension_module('add', 'src/add.c', install: false, build_by_default: true)
