#!/usr/bin/env python3
"""
Script d'organisation du dataset BCSD.
Prend les sources brutes (TheAlgorithms + doocs/leetcode) et les range
dans une structure unifiee pour le benchmark.
"""

import json
import os
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ALGO_DIR = BASE_DIR / "Algorithm"
LEETCODE_DIR = BASE_DIR / "leetcode"
OUTPUT_DIR = BASE_DIR / "data" / "organized_dataset"

LANG_CONFIG = {
    "C":    {"extensions": {".c"},           "source_dirs_algo": ["C"]},
    "Cpp":  {"extensions": {".cpp", ".cc"},  "source_dirs_algo": ["C-Plus-Plus"]},
    "Go":   {"extensions": {".go"},          "source_dirs_algo": ["Go"]},
    "Rust": {"extensions": {".rs"},          "source_dirs_algo": ["Rust"]},
}

HEADER_EXTENSIONS = {".h", ".hpp"}

# fichiers a ignorer
SKIP_PATTERNS = [
    re.compile(r"_test\.\w+$"),
    re.compile(r"test_.*\.\w+$"),
    re.compile(r"sorts_test\.go$"),
    re.compile(r"CMakeLists\.txt$"),
    re.compile(r"mod\.rs$"),
    re.compile(r"lib\.rs$"),
    re.compile(r"doc\.go$"),
    re.compile(r"go\.mod$"),
    re.compile(r"go\.sum$"),
    re.compile(r"Cargo\.toml$"),
    re.compile(r"README.*\.md$", re.IGNORECASE),
    re.compile(r"sort_utils\.rs$"),
]

SCRAPE_DATE = "2026-02-16T23:02:13+01:00"

# mots connus pour decouper les noms composes (ex: bubblesort -> bubble_sort)
# tries par taille decroissante pour matcher le plus long en premier
KNOWN_WORDS = sorted([
    "insertion", "selection", "counting", "pigeonhole", "cocktail",
    "exchange", "patience", "fibonacci", "euclidean", "dijkstra",
    "bellman", "floyd", "warshall", "kruskal", "hamilton", "hamiltonian",
    "binary", "linear", "ternary", "interpolation", "exponential",
    "recursive", "recursion", "iteration", "iterative",
    "bubble", "merge", "quick", "heap", "radix", "bucket", "shell",
    "gnome", "stooge", "shaker", "circle", "cycle", "comb", "bogo",
    "bead", "bitonic", "pancake", "sleep", "tree", "wave", "wiggle",
    "tim", "intro", "simple", "odd", "even", "sort", "search",
    "depth", "breadth", "first", "matrix", "array", "list", "stack",
    "queue", "graph", "number", "string", "linked", "hash", "table",
    "random", "pivot", "non", "nr",
], key=len, reverse=True)


def split_compound_word(word):
    """Decoupe un mot compose comme 'bubblesort' en ['bubble', 'sort']."""
    if "_" in word:
        return word.lower().split("_")

    word_lower = word.lower()
    parts = []
    remaining = word_lower

    while remaining:
        matched = False
        for known in KNOWN_WORDS:
            if remaining.startswith(known) and len(known) > 1:
                parts.append(known)
                remaining = remaining[len(known):]
                matched = True
                break
        if not matched:
            if remaining:
                parts.append(remaining)
            break

    return parts if parts else [word_lower]


def normalize_algo_name(filename_stem):
    """
    Normalise un nom de fichier algo en nom de tache.
    Ex: bubblesort -> bubble_sort, quick_sort_2 -> quick_sort
    """
    name = filename_stem.lower().strip()
    name = re.sub(r'[_]?\d+$', '', name)  # vire les suffixes numeriques
    parts = split_compound_word(name)
    result = "_".join(parts).strip("_")

    # deduplique les mots consecutifs identiques
    result_parts = result.split("_")
    deduped = [result_parts[0]]
    for p in result_parts[1:]:
        if p != deduped[-1]:
            deduped.append(p)
    return "_".join(deduped)


def normalize_task_name_simple(name):
    """Normalisation simple pour les noms de problemes leetcode."""
    name = name.strip()
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def should_skip_file(filepath):
    for pattern in SKIP_PATTERNS:
        if pattern.search(filepath.name):
            return True
    return False


def get_lang_for_ext(ext):
    for lang, config in LANG_CONFIG.items():
        if ext in config["extensions"]:
            return lang
    return None


def is_standalone(filepath, lang):
    """Verifie si un fichier peut compiler tout seul."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return True

    if lang in ("C", "Cpp"):
        local_includes = re.findall(r'#include\s+"([^"]+)"', content)
        for inc in local_includes:
            if (filepath.parent / inc).exists():
                return False
        return True
    elif lang == "Go":
        if "github.com/TheAlgorithms" in content:
            return False
        pkg_match = re.search(r"^package\s+(\w+)", content, re.MULTILINE)
        if pkg_match and pkg_match.group(1) != "main":
            return False
        return True
    elif lang == "Rust":
        return "use crate::" not in content and "use super::" not in content
    return True


def copy_file_to_dataset(src, dest_dir, ext):
    """Copie un fichier avec le nommage impl_XX."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(dest_dir.glob(f"impl_*{ext}"))
    next_num = len(existing) + 1
    dest_path = dest_dir / f"impl_{next_num:02d}{ext}"
    shutil.copy2(src, dest_path)
    return dest_path


# categories a exclure (pas des algos)
EXCLUDED_CATEGORIES = {
    "scripts", "doc", ".github", ".git", ".vscode", "git_hooks",
    "exercism", "client_server", "games", "graphics", "audio",
    "developer_tools", "project_euler", "constraints",
}


def process_the_algorithms():
    print("=" * 60)
    print("Processing TheAlgorithms...")
    print("=" * 60)

    source_name = "the_algorithms"
    output_base = OUTPUT_DIR / source_name
    stats = {"C": 0, "Cpp": 0, "Go": 0, "Rust": 0}
    tasks = {}
    non_standalone_files = {"C": 0, "Cpp": 0, "Go": 0, "Rust": 0}

    for lang, config in LANG_CONFIG.items():
        for src_dir_name in config["source_dirs_algo"]:
            src_dir = ALGO_DIR / src_dir_name
            if not src_dir.exists():
                continue

            if lang == "Rust":
                src_dir = src_dir / "src"
                if not src_dir.exists():
                    continue

            print(f"\n  Processing {lang} from {src_dir}...")
            file_count = 0

            for root, dirs, files in os.walk(src_dir):
                dirs[:] = [d for d in dirs if d not in EXCLUDED_CATEGORIES and not d.startswith(".")]
                root_path = Path(root)

                for filename in sorted(files):
                    filepath = root_path / filename
                    ext = filepath.suffix
                    file_lang = get_lang_for_ext(ext)
                    if file_lang != lang:
                        continue
                    if should_skip_file(filepath):
                        continue

                    # on utilise juste le nom du fichier, pas la categorie
                    task_name = normalize_algo_name(filepath.stem)
                    if not task_name:
                        continue

                    standalone = is_standalone(filepath, lang)
                    if not standalone:
                        non_standalone_files[lang] += 1

                    ext_map = {".c": ".c", ".cpp": ".cpp", ".cc": ".cpp", ".go": ".go", ".rs": ".rs"}
                    out_ext = ext_map.get(ext, ext)

                    dest_dir = output_base / task_name / lang
                    copy_file_to_dataset(filepath, dest_dir, out_ext)

                    stats[lang] += 1
                    if task_name not in tasks:
                        tasks[task_name] = set()
                    tasks[task_name].add(lang)
                    file_count += 1

            print(f"    -> {file_count} files processed for {lang}")

    # stats multi-langage
    lang_count_dist = {}
    for task_name, langs in tasks.items():
        n = len(langs)
        lang_count_dist[n] = lang_count_dist.get(n, 0) + 1

    print(f"\n  Task language distribution: {dict(sorted(lang_count_dist.items()))}")

    non_standalone_langs = [lang for lang, count in non_standalone_files.items() if count > 0]

    metadata = {
        "source": "the_algorithms",
        "scrape_date": SCRAPE_DATE,
        "total_tasks": len(tasks),
        "implementations": stats,
        "structure": "dataset/the_algorithms/<task>/<C|Cpp|Rust|Go>/impl_XX.<ext>",
        "language_coverage": {
            "tasks_with_1_lang": lang_count_dist.get(1, 0),
            "tasks_with_2_langs": lang_count_dist.get(2, 0),
            "tasks_with_3_langs": lang_count_dist.get(3, 0),
            "tasks_with_4_langs": lang_count_dist.get(4, 0),
        },
        "notes": {
            "non_standalone_languages": sorted(non_standalone_langs),
            "non_standalone_file_counts": non_standalone_files,
            "description": "Go files import project packages, Rust files use crate modules."
        }
    }

    output_base.mkdir(parents=True, exist_ok=True)
    with open(output_base / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n  TheAlgorithms done: {len(tasks)} tasks, {sum(stats.values())} files")
    print(f"     Stats: {stats}")
    return stats, tasks


def process_leetcode():
    print("\n" + "=" * 60)
    print("Processing Leetcode...")
    print("=" * 60)

    source_name = "leetcode"
    output_base = OUTPUT_DIR / source_name
    solution_dir = LEETCODE_DIR / "solution"
    stats = {"C": 0, "Cpp": 0, "Go": 0, "Rust": 0}
    tasks = {}

    if not solution_dir.exists():
        print(f"  [ERROR] {solution_dir} does not exist!")
        return stats, tasks

    target_files = {
        "Solution.c": ("C", ".c"),
        "Solution.cpp": ("Cpp", ".cpp"),
        "Solution.go": ("Go", ".go"),
        "Solution.rs": ("Rust", ".rs"),
    }

    range_dirs = sorted([d for d in solution_dir.iterdir() if d.is_dir() and re.match(r"\d{4}-\d{4}", d.name)])

    for range_dir in range_dirs:
        problem_dirs = sorted([d for d in range_dir.iterdir() if d.is_dir()])

        for problem_dir in problem_dirs:
            task_name = normalize_task_name_simple(problem_dir.name)
            if not task_name:
                continue

            for target_file, (lang, ext) in target_files.items():
                src_file = problem_dir / target_file
                if src_file.exists():
                    dest_dir = output_base / task_name / lang
                    copy_file_to_dataset(src_file, dest_dir, ext)
                    stats[lang] += 1
                    if task_name not in tasks:
                        tasks[task_name] = set()
                    tasks[task_name].add(lang)

    # LCCI (Cracking the Coding Interview) - noms anglais, on garde
    # on exclut lcof/lcof2/lcp/lcs car noms en chinois
    lcci_dir = LEETCODE_DIR / "lcci"
    if lcci_dir.exists():
        print(f"\n  Processing leetcode/lcci...")
        for problem_dir in sorted([d for d in lcci_dir.iterdir() if d.is_dir()]):
            raw_name = problem_dir.name
            name_match = re.match(r"[\d.]+\s*(.*)", raw_name)
            if name_match:
                clean_name = name_match.group(1)
            else:
                clean_name = raw_name
            task_name = normalize_task_name_simple(f"lcci_{clean_name}")
            if not task_name:
                continue

            for target_file, (lang, ext) in target_files.items():
                src_file = problem_dir / target_file
                if src_file.exists():
                    dest_dir = output_base / task_name / lang
                    copy_file_to_dataset(src_file, dest_dir, ext)
                    stats[lang] += 1
                    if task_name not in tasks:
                        tasks[task_name] = set()
                    tasks[task_name].add(lang)

    lang_count_dist = {}
    for task_name, langs in tasks.items():
        n = len(langs)
        lang_count_dist[n] = lang_count_dist.get(n, 0) + 1

    print(f"\n  Task language distribution: {dict(sorted(lang_count_dist.items()))}")

    metadata = {
        "source": "leetcode",
        "scrape_date": SCRAPE_DATE,
        "total_tasks": len(tasks),
        "implementations": stats,
        "structure": "dataset/leetcode/<task>/<C|Cpp|Rust|Go>/impl_XX.<ext>",
        "language_coverage": {
            "tasks_with_1_lang": lang_count_dist.get(1, 0),
            "tasks_with_2_langs": lang_count_dist.get(2, 0),
            "tasks_with_3_langs": lang_count_dist.get(3, 0),
            "tasks_with_4_langs": lang_count_dist.get(4, 0),
        },
        "notes": {
            "non_standalone_languages": ["Go", "Rust"],
            "description": "Leetcode solutions are function-level snippets."
        }
    }

    output_base.mkdir(parents=True, exist_ok=True)
    with open(output_base / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n  Leetcode done: {len(tasks)} tasks, {sum(stats.values())} files")
    print(f"     Stats: {stats}")
    return stats, tasks


def cleanup_single_lang_tasks(source_name, tasks):
    """Supprime les taches qui n'ont qu'un seul langage (inutile pour BCSD)."""
    output_base = OUTPUT_DIR / source_name
    removed_tasks = 0
    removed_files = 0
    kept_stats = {"C": 0, "Cpp": 0, "Go": 0, "Rust": 0}

    for task_name, langs in list(tasks.items()):
        task_dir = output_base / task_name
        if len(langs) < 2:
            if task_dir.exists():
                for f in task_dir.rglob("*"):
                    if f.is_file():
                        removed_files += 1
                shutil.rmtree(task_dir)
            removed_tasks += 1
            del tasks[task_name]
        else:
            for lang in langs:
                lang_dir = task_dir / lang
                if lang_dir.exists():
                    file_count = len(list(lang_dir.glob("impl_*")))
                    kept_stats[lang] += file_count

    # maj metadata
    lang_count_dist = {}
    for task_name, langs in tasks.items():
        n = len(langs)
        lang_count_dist[n] = lang_count_dist.get(n, 0) + 1

    meta_path = output_base / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        metadata["total_tasks"] = len(tasks)
        metadata["implementations"] = kept_stats
        metadata["language_coverage"] = {
            "tasks_with_2_langs": lang_count_dist.get(2, 0),
            "tasks_with_3_langs": lang_count_dist.get(3, 0),
            "tasks_with_4_langs": lang_count_dist.get(4, 0),
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    return removed_tasks, removed_files, kept_stats


def main():
    print(f"Base directory: {BASE_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    if OUTPUT_DIR.exists():
        print(f"Removing existing output directory: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    algo_stats, algo_tasks = process_the_algorithms()
    lc_stats, lc_tasks = process_leetcode()

    # nettoyage des taches a un seul langage
    print("\n" + "=" * 60)
    print("CLEANUP: Removing single-language tasks...")
    print("=" * 60)

    algo_removed, algo_removed_files, algo_kept = cleanup_single_lang_tasks("the_algorithms", algo_tasks)
    print(f"\n  TheAlgorithms: removed {algo_removed} tasks ({algo_removed_files} files)")
    print(f"  Kept: {len(algo_tasks)} tasks, {sum(algo_kept.values())} files")

    lc_removed, lc_removed_files, lc_kept = cleanup_single_lang_tasks("leetcode", lc_tasks)
    print(f"\n  Leetcode: removed {lc_removed} tasks ({lc_removed_files} files)")
    print(f"  Kept: {len(lc_tasks)} tasks, {sum(lc_kept.values())} files")

    # resume
    total_tasks = len(algo_tasks) + len(lc_tasks)
    total_files = sum(algo_kept.values()) + sum(lc_kept.values())
    total_removed = algo_removed + lc_removed

    print(f"\n{'=' * 60}")
    print(f"DONE")
    print(f"{'=' * 60}")
    print(f"TheAlgorithms: {len(algo_tasks)} tasks, {sum(algo_kept.values())} files")
    print(f"Leetcode: {len(lc_tasks)} tasks, {sum(lc_kept.values())} files")
    print(f"Total: {total_tasks} tasks, {total_files} files")
    print(f"Removed: {total_removed} single-language tasks")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
