# Announcement draft — GitHub Discussions

**Introducing just-buildit — the missing PEP 517 build backend for C extensions**

You know how to build your project. just-buildit knows how to package it. That's the whole deal.

Add four lines to `pyproject.toml` and `pip install .` works — whether you're using Make, CMake, Meson, Bazel, or anything else. just-buildit calls your build command, collects the output, and ships the wheel.

```toml
[build-system]
requires = ["just-buildit"]
build-backend = "just_buildit"

[tool.just-buildit]
command = "make"
```

If you're building Python C extensions and have hit friction getting them packaged, this is for you. We'd love to hear how you're using it, what's working, and what isn't.

→ [just-buildit.github.io/just-buildit](https://just-buildit.github.io/just-buildit/)
