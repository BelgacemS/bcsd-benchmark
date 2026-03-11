from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Optional


# ── Language detection

EXT_TO_LANG: dict[str, str] = {
    ".c":   "C",
    ".cpp": "C++",
    ".rs":  "Rust",
    ".go":  "Go",
}


GCC_TOOLCHAINS: dict[str, tuple[str, list[str]]] = {
    "x86":     ("gcc",                       ["-m32"]),
    "x86_64":  ("gcc",                       []),
    "arm":     ("arm-linux-gnueabihf-gcc",   []),
    "aarch64": ("aarch64-linux-gnu-gcc",     []),
}

GXX_TOOLCHAINS: dict[str, tuple[str, list[str]]] = {
    "x86":     ("g++",                       ["-m32"]),
    "x86_64":  ("g++",                       []),
    "arm":     ("arm-linux-gnueabihf-g++",   []),
    "aarch64": ("aarch64-linux-gnu-g++",     []),
}

# clang cross-compilation uses --target + gcc sysroot/linker
CLANG_TOOLCHAINS: dict[str, tuple[str, list[str]]] = {
    "x86":     ("clang",   ["-m32"]),
    "x86_64":  ("clang",   []),
    "arm":     ("clang",   ["--target=arm-linux-gnueabihf"]),
    "aarch64": ("clang",   ["--target=aarch64-linux-gnu"]),
}

CLANGXX_TOOLCHAINS: dict[str, tuple[str, list[str]]] = {
    "x86":     ("clang++", ["-m32"]),
    "x86_64":  ("clang++", []),
    "arm":     ("clang++", ["--target=arm-linux-gnueabihf"]),
    "aarch64": ("clang++", ["--target=aarch64-linux-gnu"]),
}


# All C/C++ compiler configs: (toolchain_dict, compiler_label, lang)
C_COMPILER_CONFIGS = [
    (GCC_TOOLCHAINS,   "gcc",    "C"),
    (CLANG_TOOLCHAINS, "clang",  "C"),
]
CPP_COMPILER_CONFIGS = [
    (GXX_TOOLCHAINS,    "g++",     "C++"),
    (CLANGXX_TOOLCHAINS,"clang++", "C++"),
]

RUST_TARGETS: dict[str, str] = {
    "x86":     "i686-unknown-linux-gnu",
    "x86_64":  "x86_64-unknown-linux-gnu",
    "arm":     "armv7-unknown-linux-gnueabihf",
    "aarch64": "aarch64-unknown-linux-gnu",
}

RUST_LINKERS: dict[str, Optional[str]] = {
    "x86":     "gcc",  # uses native gcc with -m32 via cargo config
    "x86_64":  None,
    "arm":     "arm-linux-gnueabihf-gcc",
    "aarch64": "aarch64-linux-gnu-gcc",
}

GO_ARCHES: dict[str, dict[str, str]] = {
    "x86":     {"GOARCH": "386"},
    "x86_64":  {"GOARCH": "amd64"},
    "arm":     {"GOARCH": "arm", "GOARM": "7"},
    "aarch64": {"GOARCH": "arm64"},
}

ALL_ARCHITECTURES = ["x86", "x86_64", "arm", "aarch64"]

OPT_LEVELS: dict[str, list[str]] = {
    "C":    ["O0", "O1", "O2", "O3", "Os"],
    "C++":  ["O0", "O1", "O2", "O3", "Os"],
    "Rust": ["O0", "O1", "O2", "O3"],
    "Go":   ["O0", "O2"],
}

GCC_DEBUG_FLAGS   = ["-g3", "-gdwarf-4"]
CLANG_DEBUG_FLAGS = ["-g", "-gdwarf-4", "-fstandalone-debug"]


C_EXTRA_FLAGS   = ["-Wno-implicit-int", "-Wno-implicit-function-declaration"]
CPP_EXTRA_FLAGS = ["-std=c++20"]


COMPILE_TIMEOUT = 120


CARGO_CRATES: dict[str, str] = {
    "proconio":    'proconio = { version = "*", features = ["derive"] }',
    "itertools":   'itertools = "*"',
    "rand":        'rand = "*"',
    "rand_chacha": 'rand_chacha = "*"',
    "ndarray":     'ndarray = "*"',
    "num":         'num = "*"',
    "num_integer": 'num-integer = "*"',
    "num_traits":  'num-traits = "*"',
    "regex":       'regex = "*"',
    "lazy_static": 'lazy_static = "*"',
    "ordered_float": 'ordered-float = "*"',
    "superslice":  'superslice = "*"',
    "permutohedron": 'permutohedron = "*"',
}

ATCODER_ONLY_CRATES: set[str] = {"ac_library", "ac_library_rs"}
_STDLIB_PREFIXES:    set[str] = {"std", "core", "alloc", "self", "super", "crate"}