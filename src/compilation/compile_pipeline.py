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


def _run(cmd: list[str], env: Optional[dict] = None) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=COMPILE_TIMEOUT,
            env=env if env is not None else os.environ.copy(),
        )
        msg = (result.stderr or result.stdout).strip()
        return result.returncode == 0, msg
    except subprocess.TimeoutExpired:
        return False, f"compilation a pris trop de temps {COMPILE_TIMEOUT}s"


def _compile_c_family(
    src: Path, out: Path, arch: str, opt: str,
    toolchain: dict, lang: str, debug_flags: list[str],
) -> tuple[bool, str]:
    actual, wrapped = _prepare_c_source(src, lang)
    try:
        bin_, arch_flags = toolchain[arch]
        extra = CPP_EXTRA_FLAGS if lang == "C++" else C_EXTRA_FLAGS
        cmd = [bin_, *arch_flags, *extra, f"-{opt}", *debug_flags, "-o", str(out), str(actual)]
        # Add -lm for math library linking
        cmd.append("-lm")
        return _run(cmd)
    finally:
        if wrapped:
            actual.unlink(missing_ok=True)


def compile_gcc(src: Path, out: Path, arch: str, opt: str) -> tuple[bool, str]:
    return _compile_c_family(src, out, arch, opt, GCC_TOOLCHAINS, "C", GCC_DEBUG_FLAGS)

def compile_gxx(src: Path, out: Path, arch: str, opt: str) -> tuple[bool, str]:
    return _compile_c_family(src, out, arch, opt, GXX_TOOLCHAINS, "C++", GCC_DEBUG_FLAGS)

def compile_clang(src: Path, out: Path, arch: str, opt: str) -> tuple[bool, str]:
    return _compile_c_family(src, out, arch, opt, CLANG_TOOLCHAINS, "C", CLANG_DEBUG_FLAGS)

def compile_clangxx(src: Path, out: Path, arch: str, opt: str) -> tuple[bool, str]:
    return _compile_c_family(src, out, arch, opt, CLANGXX_TOOLCHAINS, "C++", CLANG_DEBUG_FLAGS)


def compile_rust(src: Path, out: Path, arch: str, opt: str) -> tuple[bool, str]:
    crates, has_atcoder = _detect_external_crates(src)
    if has_atcoder:
        return False, "utilise ac_library AtCoder juge seulement"
    if crates:
        return _compile_rust_cargo(src, out, arch, opt, crates)
    target    = RUST_TARGETS[arch]
    opt_level = opt[1]
    cmd = [
        "rustc",
        "--target", target,
        "-C", f"opt-level={opt_level}",
        "-C", "debuginfo=2",    
    ]
    linker = RUST_LINKERS.get(arch)
    if linker:
        cmd += ["-C", f"linker={linker}"]
    cmd += ["-o", str(out), str(src)]
    return _run(cmd)


_RE_GO_EXTERNAL_IMPORT = re.compile(
    r'import\s+(?:\(\s*(?:[^)]*\n)*?\s*"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[^"]+)"'
    r'|"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[^"]+)")',
    re.MULTILINE,
)


def _detect_go_external_imports(src: Path) -> list[str]:
    code = src.read_text(errors="replace")
    imports: set[str] = set()
    for line in code.splitlines():
        line = line.strip().strip('"')
        if re.match(r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/', line):
            imports.add(line)
        m = re.match(r'\s*"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[^"]+)"', line)
        if m:
            imports.add(m.group(1))
    block_re = re.compile(r'import\s*\((.*?)\)', re.DOTALL)
    for block in block_re.findall(code):
        for line in block.splitlines():
            m = re.match(r'\s*(?:\w+\s+)?"([a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/[^"]+)"', line)
            if m:
                imports.add(m.group(1))
    return sorted(imports)


def compile_go(src: Path, out: Path, arch: str, opt: str) -> tuple[bool, str]:
    go_bin = shutil.which("go")
    if not go_bin:
        return False, "go not found"
    goroot = subprocess.run(
        [go_bin, "env", "GOROOT"], capture_output=True, text=True
    ).stdout.strip()

    env = {
        **os.environ,
        "GOOS":   "linux",
        "GOROOT": goroot,
        "GOPATH": "/tmp/bscd_gopath",
        "GOMODCACHE": "/tmp/bscd_gopath/pkg/mod",
        "CGO_ENABLED": "0",
        **GO_ARCHES[arch],
    }
    env.pop("GOFLAGS", None)

    external_imports = _detect_go_external_imports(src)

    if external_imports:
        with tempfile.TemporaryDirectory(prefix="bscd_go_") as tmp_str:
            tmp = Path(tmp_str)
            shutil.copy(src, tmp / "main.go")
            init_result = subprocess.run(
                [go_bin, "mod", "init", "bscd"],
                cwd=str(tmp), capture_output=True, text=True, env=env,
                timeout=COMPILE_TIMEOUT,
            )
            if init_result.returncode != 0:
                return False, f"go mod init a échoué: {init_result.stderr.strip()}"
            tidy_result = subprocess.run(
                [go_bin, "mod", "tidy"],
                cwd=str(tmp), capture_output=True, text=True, env=env,
                timeout=COMPILE_TIMEOUT,
            )
            if tidy_result.returncode != 0:
                return False, f"go mod tidy a échoué: {tidy_result.stderr.strip()}"
            cmd = [go_bin, "build"]
            if opt == "O0":
                cmd += ["-gcflags=all=-N -l"]
            cmd += ["-o", str(out.resolve()), "."]
            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True,
                    timeout=COMPILE_TIMEOUT, env=env, cwd=str(tmp),
                )
                msg = (result.stderr or result.stdout).strip()
                return result.returncode == 0, msg
            except subprocess.TimeoutExpired:
                return False, f"compilation a pris trop de temps {COMPILE_TIMEOUT}s"
    else:
        cmd = [go_bin, "build"]
        if opt == "O0":
            cmd += ["-gcflags=all=-N -l"]
        cmd += ["-o", str(out), str(src)]
        return _run(cmd, env)



COMPILE_FN: dict[tuple[str, str], ...] = {
    ("C",    "gcc"):    compile_gcc,
    ("C",    "clang"):  compile_clang,
    ("C++",  "g++"):    compile_gxx,
    ("C++",  "clang++"): compile_clangxx,
    ("Rust", "rustc"):  compile_rust,
    ("Go",   "go"):     compile_go,
}

LANG_COMPILERS: dict[str, list[str]] = {
    "C":    ["gcc", "clang"],
    "C++":  ["g++", "clang++"],
    "Rust": ["rustc"],
    "Go":   ["go"],
}



@dataclass
class CompileStats:
    ok: int = 0
    fail: int = 0
    skip: int = 0
    _lock: Lock = field(default_factory=Lock)

    def add(self, ok: int = 0, fail: int = 0, skip: int = 0) -> None:
        with self._lock:
            self.ok += ok
            self.fail += fail
            self.skip += skip


def setup_logging(log_file: Path) -> logging.Logger:
    log = logging.getLogger("compile_pipeline")
    log.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    log.addHandler(console)
    log.addHandler(file_handler)
    return log


def find_sources(input_dir: Path) -> list[Path]:
    sources: list[Path] = []
    for ext in EXT_TO_LANG:
        sources.extend(input_dir.rglob(f"*{ext}"))
    # Exclude already-compiled binaries sitting inside the output tree
    return sorted(s for s in sources if "binaries" not in s.parts)

    


@dataclass(frozen=True)
class CompileJob:
    src: Path
    out: Path
    lang: str
    compiler: str
    arch: str
    opt: str
    label: str  # for logging


def _execute_job(job: CompileJob, log: logging.Logger) -> tuple[str, bool, str]:
    job.out.parent.mkdir(parents=True, exist_ok=True)
    success, msg = COMPILE_FN[(job.lang, job.compiler)](job.src, job.out, job.arch, job.opt)
    return job.label, success, msg


def _generate_jobs(
    sources: list[Path],
    input_dir: Path,
    output_dir: Path,
    available: dict[tuple[str, str], dict[str, bool]],
    archs: list[str],
    opts: Optional[list[str]],
    log: logging.Logger,
    stats: CompileStats,
) -> list[CompileJob]:
    jobs: list[CompileJob] = []
    for src in sources:
        lang = EXT_TO_LANG[src.suffix]
        rel_dir = src.parent.relative_to(input_dir)
        stem = src.stem
        compilers = LANG_COMPILERS[lang]

        for compiler in compilers:
            opt_list = opts if opts is not None else OPT_LEVELS[lang]

            for arch in archs:
                if not available.get((lang, compiler), {}).get(arch):
                    skip_count = sum(1 for o in opt_list if o in OPT_LEVELS[lang])
                    log.debug("SKIP  %s/%s [%s/%s] — toolchain unavailable",
                              rel_dir, stem, compiler, arch)
                    stats.add(skip=skip_count)
                    continue

                for opt in opt_list:
                    if opt not in OPT_LEVELS[lang]:
                        continue
                    out_dir = output_dir / rel_dir / compiler / arch / opt
                    out = out_dir / f"{stem}.exe"
                    label = f"{rel_dir}/{stem} [{compiler}/{arch}/{opt}]"
                    jobs.append(CompileJob(
                        src=src, out=out, lang=lang, compiler=compiler,
                        arch=arch, opt=opt, label=label,
                    ))
    return jobs


def run_pipeline(
    input_dir: Path,
    output_dir: Path,
    archs: list[str],
    opts: Optional[list[str]],
    log: logging.Logger,
    jobs: int = 1,
) -> None:
    log.info("Verifie les compilateurs necessaires")
    available = probe_toolchains()

    for (lang, compiler), arch_map in available.items():
        for arch, ok in arch_map.items():
            if arch in archs:
                status = "OK" if ok else "MANQUANT"
                level = logging.DEBUG if ok else logging.WARNING
                log.log(level, "Toolchain %-5s / %-8s / %-7s — %s",
                        lang, compiler, arch, status)

    sources = find_sources(input_dir)
    log.info("Trouvé %d fichier source dans %s", len(sources), input_dir)

    stats = CompileStats()
    compile_jobs = _generate_jobs(
        sources, input_dir, output_dir, available, archs, opts, log, stats,
    )
    log.info("Généré %d job de compilation, utilisant %d worker(s)", len(compile_jobs), jobs)

    if jobs == 1:
        for i, job in enumerate(compile_jobs, 1):
            label, success, msg = _execute_job(job, log)
            if success:
                log.debug("OK    %s", label)
                stats.add(ok=1)
            else:
                first_line = msg.splitlines()[0] if msg else "erreur inconnue"
                log.info("ECHEC  %s — %s", label, first_line)
                log.debug("      Erreur complète:\n%s", msg)
                stats.add(fail=1)
            if i % 100 == 0:
                log.info("Progression: %d/%d jobs faits", i, len(compile_jobs))
    else:
        
        completed = 0
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            futures = {
                pool.submit(_execute_job, job, log): job
                for job in compile_jobs
            }
            for future in as_completed(futures):
                completed += 1
                try:
                    label, success, msg = future.result()
                except Exception as exc:
                    job = futures[future]
                    log.info("ECHEC  %s — exception: %s", job.label, exc)
                    stats.add(fail=1)
                    continue

                if success:
                    log.debug("OK    %s", label)
                    stats.add(ok=1)
                else:
                    first_line = msg.splitlines()[0] if msg else "erreur inconnue"
                    log.info("ECHEC  %s — %s", label, first_line)
                    log.debug("      Erreur complète:\n%s", msg)
                    stats.add(fail=1)

                if completed % 100 == 0:
                    log.info("Progression: %d/%d jobs faits", completed, len(compile_jobs))

    log.info(
        "Terminé — %d compilés  |  %d échoués  |  %d ignorés (toolchain manquant)",
        stats.ok, stats.fail, stats.skip,
    )