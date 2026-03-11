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

def _detect_external_crates(src: Path) -> tuple[list[str], bool]:
    crates: set[str] = set()
    for line in src.read_text(errors="replace").splitlines():
        m = re.match(r"\s*use\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
        if m and m.group(1) not in _STDLIB_PREFIXES:
            crates.add(m.group(1))
        m = re.match(r"\s*extern\s+crate\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
        if m:
            crates.add(m.group(1))
    has_atcoder = bool(crates & ATCODER_ONLY_CRATES)
    resolvable  = [c for c in crates if c in CARGO_CRATES]
    unknown     = [c for c in crates if c not in CARGO_CRATES and c not in ATCODER_ONLY_CRATES]
    return resolvable + unknown, has_atcoder


def _compile_rust_cargo(
    src: Path, out: Path, arch: str, opt: str, crates: list[str]
) -> tuple[bool, str]:
    target    = RUST_TARGETS[arch]
    opt_level = opt[1]
    dep_lines = "\n".join(
        CARGO_CRATES.get(c, f'{c} = "*"') for c in crates
    )
    with tempfile.TemporaryDirectory(prefix="bscd_rust_") as tmp_str:
        tmp = Path(tmp_str)
        (tmp / "src").mkdir()
        shutil.copy(src, tmp / "src" / "main.rs")
        (tmp / "Cargo.toml").write_text(
            "[package]\nname = \"bscd\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n"
            f"[dependencies]\n{dep_lines}\n"
        )
        env = {
            **os.environ,
            "CARGO_PROFILE_RELEASE_OPT_LEVEL": opt_level,
            "CARGO_PROFILE_RELEASE_DEBUG":      "true",
        }
        linker = RUST_LINKERS.get(arch)
        if linker:
            env[f"CARGO_TARGET_{target.upper().replace('-', '_')}_LINKER"] = linker
        cmd = [
            "cargo", "build", "--release",
            "--target", target,
            "--manifest-path", str(tmp / "Cargo.toml"),
        ]
        success, msg = _run(cmd, env)
        if success:
            built = tmp / "target" / target / "release" / "bscd"
            if built.exists():
                shutil.copy(built, out)
                return True, ""
            return False, "binary not found after cargo build"
        return False, msg

_CPP_BOILERPLATE = """\
#include <algorithm>
#include <climits>
#include <cmath>
#include <cstring>
#include <iostream>
#include <map>
#include <queue>
#include <set>
#include <sstream>
#include <stack>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
using namespace std;

struct ListNode {
    int val; ListNode *next;
    ListNode() : val(0), next(nullptr) {}
    ListNode(int x) : val(x), next(nullptr) {}
};
struct TreeNode {
    int val; TreeNode *left, *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
};

"""

_C_BOILERPLATE = """\
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <limits.h>
#include <stdbool.h>
#include <ctype.h>

"""

_RE_HAS_INCLUDE = re.compile(r"^\s*#\s*include\b", re.MULTILINE)

_RE_HAS_MAIN = re.compile(r"^[^/]*\b(?:int|void|signed|auto|int32_t)\s+main\s*\(",
    re.MULTILINE,)

_RE_HAS_MAIN_BARE = re.compile(r"^\s*main\s*\(", re.MULTILINE)

_RE_ATCODER_HEADER = re.compile(r'#\s*include\s*[<"]atcoder/')


def _prepare_c_source(src: Path, lang: str) -> tuple[Path, bool]:
    code = src.read_text(errors="replace")

    if _RE_ATCODER_HEADER.search(code):
        return src, False 

    has_includes = bool(_RE_HAS_INCLUDE.search(code))
    has_main = bool(_RE_HAS_MAIN.search(code)) or bool(_RE_HAS_MAIN_BARE.search(code))

    if has_includes and has_main:
        return src, False

    boilerplate = _CPP_BOILERPLATE if lang == "C++" else _C_BOILERPLATE
    prefix = boilerplate if not has_includes else ""
    suffix = "\nint main(void) { return 0; }\n" if not has_main else ""

    tmp = tempfile.NamedTemporaryFile(
        suffix=src.suffix, delete=False, mode="w", encoding="utf-8"
    )
    tmp.write(prefix + code + suffix)
    tmp.close()
    return Path(tmp.name), True




def _tool_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _rust_target_installed(target: str) -> bool:
    result = subprocess.run(
        ["rustup", "target", "list", "--installed"],
        capture_output=True, text=True,
    )
    return target in result.stdout


def probe_toolchains() -> dict[tuple[str, str], dict[str, bool]]:
    available: dict[tuple[str, str], dict[str, bool]] = {}

    for toolchain, name, lang in C_COMPILER_CONFIGS + CPP_COMPILER_CONFIGS:
        available[(lang, name)] = {
            arch: _tool_exists(bin_)
            for arch, (bin_, _) in toolchain.items()
        }

    has_rustup = _tool_exists("rustup") and _tool_exists("rustc")
    available[("Rust", "rustc")] = {
        arch: has_rustup and _rust_target_installed(target)
        for arch, target in RUST_TARGETS.items()
    }

    has_go = _tool_exists("go")
    available[("Go", "go")] = {arch: has_go for arch in GO_ARCHES}

    return available