# Announcement draft — GitHub Discussions

**Introducing just-buildit — the missing PEP 517 build backend for C extensions**

You know how to build your project. `just-buildit` knows how to package it. That's the whole deal.

Add four lines to `pyproject.toml` and `pip install .` just works — whether you're using Make, CMake, Meson, Bazel, or anything else. `just-buildit` calls your build command, collects the output, and ships the package.

```toml
[build-system]
requires = ["just-buildit"]
build-backend = "just_buildit"

[tool.just-buildit]
command = "make"
```

If, like us, you've struggled with or been dissatisfied by existing tools for building C extensions, this is for you. We'd love to hear how you're using it, what's working, and what isn't.

→ [just-buildit.github.io/just-buildit](https://just-buildit.github.io/just-buildit/)
