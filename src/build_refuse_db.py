#!/usr/bin/env python3

import argparse
import hashlib
import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from elftools.elf.elffile import ELFFile


AGGRESSIVE_OPT_LEVELS = {"O2", "O3"}


@dataclass(frozen=True)
class ParsedBinaryPath:
    compiler: str
    optimization: str
    platform: str
    problem_name: str
    implementation_folder: str
    binary_rel_path: str
    binary_abs_path: str


@dataclass(frozen=True)
class ExtractedFunction:
    function_name: str
    raw_bytes: bytes
    byte_size: int
    byte_hash: str


def guess_language(implementation_folder: str) -> Optional[str]:
    lowered = implementation_folder.lower()
    if "cpp" in lowered or "c++" in lowered:
        return "cpp"
    if lowered.startswith("c_") or lowered == "c" or lowered.endswith("_c"):
        return "c"
    if "java" in lowered:
        return "java"
    if "rust" in lowered:
        return "rust"
    if "go" in lowered:
        return "go"
    if "python" in lowered or "py" in lowered:
        return "python"
    return None


def parse_binary_path(root_dir: Path, binary_path: Path) -> Optional[ParsedBinaryPath]:
    rel_parts = binary_path.relative_to(root_dir).parts
    if len(rel_parts) < 6:
        return None

    # ACTUAL STRUCTURE:
    # Compiler / Architecture / Optimization / Platform / Problem_Name / Implementation_Binary
    compiler = rel_parts[0]           # gcc, clang
    architecture = rel_parts[1]       # x86_64
    optimization = rel_parts[2]       # O0, O1, O2, O3, Os
    platform = rel_parts[3]           # atcoder, leetcode, rosetta_code
    problem_name = rel_parts[4]       # abc100_a, 0001_two_sum, ...
    implementation_folder = rel_parts[5]  # C__impl_01, Cpp__impl_02, ...
    binary_rel_path = str(Path(*rel_parts[3:]))

    return ParsedBinaryPath(
        compiler=compiler,
        optimization=optimization,
        platform=platform,
        problem_name=problem_name,
        implementation_folder=implementation_folder,
        binary_rel_path=binary_rel_path,
        binary_abs_path=str(binary_path.resolve()),
    )


def is_elf(binary_path: Path) -> bool:
    try:
        with binary_path.open("rb") as f:
            return f.read(4) == b"\x7fELF"
    except OSError:
        return False


def _extract_symbol_bytes(elf: ELFFile, file_bytes: bytes, symbol) -> Optional[bytes]:
    st_size = int(symbol["st_size"])
    st_value = int(symbol["st_value"])
    st_shndx = symbol["st_shndx"]

    if st_size <= 0 or st_value <= 0:
        return None
    if not isinstance(st_shndx, int):
        return None

    section = elf.get_section(st_shndx)
    if section is None:
        return None

    sh_addr = int(section["sh_addr"])
    sh_offset = int(section["sh_offset"])
    sh_flags = int(section["sh_flags"])

    if (sh_flags & 0x4) == 0:
        return None

    byte_offset = sh_offset + (st_value - sh_addr)
    end_offset = byte_offset + st_size
    if byte_offset < 0 or end_offset > len(file_bytes):
        return None

    return file_bytes[byte_offset:end_offset]


def extract_functions_from_elf(binary_path: Path) -> List[ExtractedFunction]:
    functions: List[ExtractedFunction] = []
    try:
        with binary_path.open("rb") as f:
            file_bytes = f.read()
            f.seek(0)
            elf = ELFFile(f)

            symtab = elf.get_section_by_name(".symtab")
            if symtab is None:
                return functions

            for symbol in symtab.iter_symbols():
                info = symbol["st_info"]
                if info["type"] != "STT_FUNC":
                    continue

                name = symbol.name.strip()
                if not name:
                    continue

                raw = _extract_symbol_bytes(elf, file_bytes, symbol)
                if not raw:
                    continue

                functions.append(
                    ExtractedFunction(
                        function_name=name,
                        raw_bytes=raw,
                        byte_size=len(raw),
                        byte_hash=hashlib.sha256(raw).hexdigest(),
                    )
                )
    except Exception:
        return []

    return functions


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=ON")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            problem_name TEXT NOT NULL,
            UNIQUE(platform, problem_name)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS implementations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            implementation_folder TEXT NOT NULL,
            source_language TEXT,
            UNIQUE(problem_id, implementation_folder),
            FOREIGN KEY(problem_id) REFERENCES problems(id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS binaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            implementation_id INTEGER NOT NULL,
            compiler TEXT NOT NULL,
            architecture TEXT NOT NULL,
            optimization TEXT NOT NULL,
            binary_rel_path TEXT NOT NULL,
            binary_abs_path TEXT NOT NULL,
            UNIQUE(implementation_id, compiler, architecture, optimization, binary_rel_path),
            FOREIGN KEY(implementation_id) REFERENCES implementations(id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS functions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            binary_id INTEGER NOT NULL,
            function_name TEXT NOT NULL,
            raw_bytes BLOB NOT NULL,
            byte_size INTEGER NOT NULL,
            byte_hash TEXT NOT NULL,
            UNIQUE(binary_id, function_name, byte_hash),
            FOREIGN KEY(binary_id) REFERENCES binaries(id)
        )
        """
    )

    conn.execute("CREATE INDEX IF NOT EXISTS idx_binaries_impl ON binaries(implementation_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_functions_binary ON functions(binary_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_functions_name ON functions(function_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_functions_hash ON functions(byte_hash)")
    conn.commit()


def get_or_create_problem(conn: sqlite3.Connection, platform: str, problem_name: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO problems(platform, problem_name) VALUES(?, ?)",
        (platform, problem_name),
    )
    row = conn.execute(
        "SELECT id FROM problems WHERE platform=? AND problem_name=?",
        (platform, problem_name),
    ).fetchone()
    return int(row[0])


def get_or_create_implementation(
    conn: sqlite3.Connection,
    problem_id: int,
    implementation_folder: str,
    source_language: Optional[str],
) -> int:
    conn.execute(
        """
        INSERT OR IGNORE INTO implementations(problem_id, implementation_folder, source_language)
        VALUES(?, ?, ?)
        """,
        (problem_id, implementation_folder, source_language),
    )

    row = conn.execute(
        """
        SELECT id FROM implementations
        WHERE problem_id=? AND implementation_folder=?
        """,
        (problem_id, implementation_folder),
    ).fetchone()
    return int(row[0])


def get_or_create_binary(
    conn: sqlite3.Connection,
    implementation_id: int,
    compiler: str,
    architecture: str,
    optimization: str,
    binary_rel_path: str,
    binary_abs_path: str,
) -> int:
    conn.execute(
        """
        INSERT OR IGNORE INTO binaries(
            implementation_id, compiler, architecture, optimization, binary_rel_path, binary_abs_path
        ) VALUES(?, ?, ?, ?, ?, ?)
        """,
        (
            implementation_id,
            compiler,
            architecture,
            optimization,
            binary_rel_path,
            binary_abs_path,
        ),
    )

    row = conn.execute(
        """
        SELECT id FROM binaries
        WHERE implementation_id=? AND compiler=? AND architecture=? AND optimization=? AND binary_rel_path=?
        """,
        (implementation_id, compiler, architecture, optimization, binary_rel_path),
    ).fetchone()
    return int(row[0])


def collect_binaries(root_dir: Path) -> List[ParsedBinaryPath]:
    binaries = []
    for p in root_dir.rglob("*"):
        if not p.is_file():
            continue
        parsed = parse_binary_path(root_dir, p)
        if parsed is None:
            continue
        if is_elf(p):
            binaries.append(parsed)
    return sorted(
        binaries,
        key=lambda x: (
            x.compiler,
            x.optimization,
            x.platform,
            x.problem_name,
            x.implementation_folder,
            x.binary_rel_path,
        ),
    )


def build_db(
    root_dir: Path,
    db_path: Path,
    strict_aggressive_presence: bool,
    reset_db: bool,
) -> None:
    if reset_db and db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    init_db(conn)

    binaries = collect_binaries(root_dir)
    print(f"[build_refuse_db] ELF binaries found: {len(binaries)}")

    if not binaries:
        conn.close()
        return

    extracted_by_binary: Dict[Tuple[str, str, str, str, str, str], List[ExtractedFunction]] = {}
    names_by_group_opt: Dict[Tuple[str, str, str, str, str], Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))

    for b in binaries:
        key = (
            b.compiler,
            b.optimization,
            b.platform,
            b.problem_name,
            b.implementation_folder,
            b.binary_rel_path,
        )
        funcs = extract_functions_from_elf(Path(b.binary_abs_path))
        extracted_by_binary[key] = funcs

        group_key = (
            b.compiler,
            b.platform,
            b.problem_name,
            b.implementation_folder,
            b.binary_rel_path,
        )
        for fn in funcs:
            names_by_group_opt[group_key][b.optimization].add(fn.function_name)

    total_inserted = 0
    total_skipped_aggressive = 0

    for b in binaries:
        problem_id = get_or_create_problem(conn, b.platform, b.problem_name)
        impl_id = get_or_create_implementation(conn, problem_id, b.implementation_folder, guess_language(b.implementation_folder))
        arch = b.platform
        binary_id = get_or_create_binary(
            conn,
            impl_id,
            b.compiler,
            arch,
            b.optimization,
            b.binary_rel_path,
            b.binary_abs_path,
        )

        key = (
            b.compiler,
            b.optimization,
            b.platform,
            b.problem_name,
            b.implementation_folder,
            b.binary_rel_path,
        )
        funcs = extracted_by_binary.get(key, [])

        keep_names: Optional[Set[str]] = None
        if strict_aggressive_presence:
            group_key = (
                b.compiler,
                b.platform,
                b.problem_name,
                b.implementation_folder,
                b.binary_rel_path,
            )
            opt_map = names_by_group_opt[group_key]

            present_aggressive = [opt for opt in AGGRESSIVE_OPT_LEVELS if opt in opt_map]
            if present_aggressive:
                stable_names = set.intersection(*(opt_map[opt] for opt in present_aggressive))
                keep_names = stable_names

        for fn in funcs:
            if keep_names is not None and fn.function_name not in keep_names:
                total_skipped_aggressive += 1
                continue

            conn.execute(
                """
                INSERT OR IGNORE INTO functions(binary_id, function_name, raw_bytes, byte_size, byte_hash)
                VALUES(?, ?, ?, ?, ?)
                """,
                (binary_id, fn.function_name, sqlite3.Binary(fn.raw_bytes), fn.byte_size, fn.byte_hash),
            )
            total_inserted += 1

    conn.commit()

    n_problems = conn.execute("SELECT COUNT(*) FROM problems").fetchone()[0]
    n_impls = conn.execute("SELECT COUNT(*) FROM implementations").fetchone()[0]
    n_bins = conn.execute("SELECT COUNT(*) FROM binaries").fetchone()[0]
    n_funcs = conn.execute("SELECT COUNT(*) FROM functions").fetchone()[0]
    conn.close()

    print("[build_refuse_db] done")
    print(f"  problems: {n_problems}")
    print(f"  implementations: {n_impls}")
    print(f"  binaries: {n_bins}")
    print(f"  functions: {n_funcs}")
    print(f"  inserted function rows (attempted): {total_inserted}")
    print(f"  skipped due to O2/O3 inlining-removal filter: {total_skipped_aggressive}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Assemblage-style SQLite DB for REFuSe")
    parser.add_argument(
        "--root-dir",
        default="binaries",
        help="Root folder containing Compiler/Architecture/Optimization/Platform/Problem_Name/Implementation_Binary",
    )
    parser.add_argument(
        "--db-path",
        default="refuse_benchmark.db",
        help="Output sqlite database path",
    )
    parser.add_argument(
        "--no-strict-aggressive-presence",
        action="store_true",
        help="Disable dropping functions not stable across present O2/O3 binaries",
    )
    parser.add_argument(
        "--reset-db",
        action="store_true",
        help="Delete existing DB before rebuild",
    )
    args = parser.parse_args()

    build_db(
        root_dir=Path(args.root_dir),
        db_path=Path(args.db_path),
        strict_aggressive_presence=not args.no_strict_aggressive_presence,
        reset_db=args.reset_db,
    )


if __name__ == "__main__":
    main()
