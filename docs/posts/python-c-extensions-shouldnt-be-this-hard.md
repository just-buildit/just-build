# Python C extensions shouldn't be this hard

You have an algorithm. It's fast in C. You want to call it from Python.

What follows is, historically, an afternoon of pain.

______________________________________________________________________

## The packaging wall

Writing the C code is the easy part. The wall is packaging: getting
`pip install .` to compile your code, link it correctly, and produce a wheel
that works on the target machine.

The options, as they exist today:

**setuptools + `Extension()`** — works if your build is trivial. The moment you
need CMake, a vendor library, generated headers, or any build complexity at all,
you're writing `setup.py` hooks and hoping the incantations hold across
platforms.

**scikit-build** — delegates to CMake, which is progress. But it still owns the
outer packaging loop, imposes its own CMake module conventions, and the
`scikit-build-core` rewrite means two partially-documented API surfaces to
navigate.

**meson-python** — excellent if you're already committed to Meson. If you're
not, you're adopting a new build system to solve a packaging problem.

**cibuildwheel** — solves cross-platform wheel building, not the
configure-and-compile step. A different layer entirely.

None of these say the thing that should be simple to say:

> "You know how to build your project. Just tell me where the output is."

______________________________________________________________________

## just-buildit

That is exactly what [just-buildit](https://just-buildit.github.io/just-buildit/)
says.

```toml
[build-system]
requires = ["just-buildit"]
build-backend = "just_buildit"

[tool.just-buildit]
command = "make"
```

That's it. `pip install .` calls `make`, collects whatever `.so` files land in
`$JUST_BUILDIT_OUTPUT_DIR`, and builds the wheel. CMake, Meson, Bazel, a shell
script — whatever your build system is, just-buildit doesn't care. It gets out
of the way.

Zero dependency tree. No build system opinions. No conventions to learn.

______________________________________________________________________

## What this unlocks

Once the packaging problem is solved at the right layer, everything above it
gets easier. Which is how [just-makeit](https://just-buildit.github.io/just-makeit/)
came to exist.

just-makeit is a scaffolding tool built on just-buildit. One command generates
a complete, tested, production-ready C extension project:

```sh
pip install just-makeit

just-makeit new my_dsp \
    --object fir_filter \
    --state "coeffs:float[16]" \
    --state "delay:float _Complex[16]" \
    --state "gain:float:1.0"

cd my_dsp && make && make test
```

What you get:

- C99 lifecycle pattern (`create` / `step` / `steps` / `reset` / `destroy`)
- Thin Python binding with NumPy `steps()` block processor
- pytest + CTest test suites, passing before you write a line of algorithm code
- `pip install .` working out of the box via just-buildit

Implement your algorithm in the generated stub, run `make`, and you have a
working Python C extension. The packaging machinery is already there — because
just-buildit makes it a non-problem.

______________________________________________________________________

## It's also a C library

This part surprises people. The generated project doesn't just produce a Python
wheel. Every component compiles as a CMake OBJECT library, which links into
*both* the Python DSO and a combined `lib<project>.so`. Same C code, two
consumers, one compilation.

```sh
cmake -S . -B build -DCMAKE_INSTALL_PREFIX=/usr/local
cmake --install build
```

After that, any C, C++, or Rust project on the system can use it:

```sh
gcc $(pkg-config --cflags my-dsp) consumer.c \
    $(pkg-config --libs my-dsp) -lm -o consumer
```

```cmake
find_package(my_dsp REQUIRED)
target_link_libraries(my_app PRIVATE my_dsp::my_dsp_lib m)
```

The Python package and the C library are the same project. You write the
algorithm once.

______________________________________________________________________

## The stack

```
your algorithm  (C99, in *_core.h)
      │
      ├── Python extension  (*_ext.c  →  pip install .)
      │         packaged by just-buildit
      │
      └── C shared library  (lib<project>.so  →  cmake --install)
                consumed via pkg-config or CMake find_package
```

just-buildit sits at the packaging layer and does one thing well. just-makeit
sits above it and handles everything else. Neither tool tries to own more than
its layer.

______________________________________________________________________

## Try it

```sh
pip install just-makeit
just-makeit new my_project --object engine --state gain:double:1.0
cd my_project && make && make test
```

- [just-buildit](https://just-buildit.github.io/just-buildit/) — the PEP 517
    backend
- [just-makeit](https://just-buildit.github.io/just-makeit/) — the scaffolding
    tool
- [just-makeit: C library guide](https://just-buildit.github.io/just-makeit/c-library/)
    — end-user install and consumption
