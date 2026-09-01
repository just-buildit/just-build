cmake_minimum_required(VERSION 3.15)
project(add C)

# Build for the interpreter just-buildit is building FOR, not whatever cmake
# finds first. They differ whenever the build runs under a venv or a
# uv-managed Python while a different python3 leads PATH -- and this example
# forces SUFFIX from JUST_BUILDIT_EXT_SUFFIX below, so without this the file is
# NAMED for the target ABI while being COMPILED against another one. That
# succeeds, produces a plausible artifact, and fails at import.
#
# Measured on aarch64: cmake found /usr/include/python3.14 and wrote
# add.cpython-312-aarch64-linux-gnu.so, exit 0.
# `Python3_EXECUTABLE` alone is NOT enough, measured: with only that set,
# `Development.Module` still searched the system and reported
# /usr/include/python3.14 while the executable was a real 3.12. The component
# looks for HEADERS, so it needs the header hint -- which just-buildit already
# hands every build as JUST_BUILDIT_INCLUDE_DIR. Prefer being told over
# searching better.
if(DEFINED ENV{JUST_BUILDIT_PYTHON})
    set(Python3_EXECUTABLE "$ENV{JUST_BUILDIT_PYTHON}")
endif()
if(DEFINED ENV{JUST_BUILDIT_INCLUDE_DIR})
    set(Python3_INCLUDE_DIR "$ENV{JUST_BUILDIT_INCLUDE_DIR}")
endif()
find_package(Python3 COMPONENTS Development.Module REQUIRED)
Python3_add_library(add MODULE src/add.c)
set_target_properties(add PROPERTIES
    OUTPUT_NAME "$ENV{JUST_BUILDIT_NAME}"
    SUFFIX      "$ENV{JUST_BUILDIT_EXT_SUFFIX}"
    PREFIX      "")
