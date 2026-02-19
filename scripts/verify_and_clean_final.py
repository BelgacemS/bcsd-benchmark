#!/usr/bin/env python3
"""
Verification finale + nettoyage du dataset.
Check la compilation C/C++ avec gcc/g++, et fait un check statique
pour Go/Rust (pas de compilateur dispo sur cette machine).
Supprime les fichiers invalides et les taches avec < 2 langages.
"""

import subprocess
import os
import shutil
import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "data" / "organized_dataset"


def check_c_compilable(filepath):
    try:
        result = subprocess.run(
            ['gcc', '-fsyntax-only', '-c', str(filepath)],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False

def check_cpp_compilable(filepath):
    try:
        result = subprocess.run(
            ['g++', '-fsyntax-only', '-std=c++17', '-c', str(filepath)],
            capture_output=True, timeout=5
        )
        return result.returncode == 0
    except:
        return False

def check_go_valid(filepath):
    """Check statique : on verifie juste la structure du fichier."""
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        if 'github.com/TheAlgorithms' in content:
            return False
        if 'package ' not in content:
            return False
        return True
    except:
        return False

def check_rust_valid(filepath):
    """Check statique : on verifie l'absence de deps internes."""
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
        if 'use crate::' in content or 'use super::' in content:
            return False
        return True
    except:
        return False


def main():
    print("=" * 50)
    print("Verification et nettoyage final")
    print("=" * 50)

    stats = defaultdict(lambda: defaultdict(int))
    deleted_files_count = 0

    # 1. verification fichier par fichier
    checkers = [
        ('.c', check_c_compilable, 'C'),
        ('.cpp', check_cpp_compilable, 'Cpp'),
        ('.go', check_go_valid, 'Go'),
        ('.rs', check_rust_valid, 'Rust')
    ]

    for lang_ext, checker, lang_name in checkers:
        print(f"Verification {lang_name}...")
        files = list(DATASET_DIR.rglob(f"*{lang_ext}"))
        count = 0
        for f in files:
            count += 1
            if count % 500 == 0:
                print(f"  {count}/{len(files)}...")

            is_valid = checker(f)
            stats[lang_name]['total'] += 1

            if is_valid:
                stats[lang_name]['kept'] += 1
            else:
                stats[lang_name]['deleted'] += 1
                f.unlink()
                deleted_files_count += 1

    print(f"\n{deleted_files_count} fichiers invalides supprimes.")

    # 2. nettoyage des taches avec moins de 2 langages
    print("\nNettoyage taches < 2 langages...")
    removed_tasks = 0
    kept_tasks = 0
    final_task_counts = {'the_algorithms': 0, 'leetcode': 0}

    for source in ['the_algorithms', 'leetcode']:
        source_dir = DATASET_DIR / source
        if not source_dir.exists():
            continue

        for task_dir in list(source_dir.iterdir()):
            if not task_dir.is_dir():
                continue

            langs = []
            for lang_dir in task_dir.iterdir():
                if lang_dir.is_dir() and any(lang_dir.iterdir()):
                    langs.append(lang_dir.name)

            if len(langs) < 2:
                shutil.rmtree(task_dir)
                removed_tasks += 1
            else:
                kept_tasks += 1
                final_task_counts[source] += 1

    print(f"{removed_tasks} taches supprimees, {kept_tasks} conservees.")

    # 3. regeneration metadata
    print("\nGeneration metadata...")
    for source in ['the_algorithms', 'leetcode']:
        source_dir = DATASET_DIR / source
        if not source_dir.exists():
            continue

        tasks_data = {}
        file_counts = defaultdict(int)

        for task_dir in source_dir.iterdir():
            if not task_dir.is_dir():
                continue
            current_langs = []
            for lang_dir in task_dir.iterdir():
                if lang_dir.is_dir():
                    count = len(list(lang_dir.glob("impl_*")))
                    if count > 0:
                        file_counts[lang_dir.name] += count
                        current_langs.append(lang_dir.name)
            if current_langs:
                tasks_data[task_dir.name] = current_langs

        dist = defaultdict(int)
        for t, l in tasks_data.items():
            dist[len(l)] += 1

        metadata = {
            "source": source,
            "scrape_date": "2026-02-17T01:30:00+01:00",
            "total_tasks": len(tasks_data),
            "implementations": dict(file_counts),
            "language_coverage": {
                "tasks_with_2_langs": dist[2],
                "tasks_with_3_langs": dist[3],
                "tasks_with_4_langs": dist[4]
            }
        }

        with open(source_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

    # 4. rapport
    print("\n" + "=" * 50)
    print("Rapport")
    print("=" * 50)
    print(f"Taches: {kept_tasks}")
    print(f"  TheAlgorithms: {final_task_counts['the_algorithms']}")
    print(f"  Leetcode:      {final_task_counts['leetcode']}")
    print("\nFichiers (gardes / total):")
    for lang in ['C', 'Cpp', 'Go', 'Rust']:
        k = stats[lang]['kept']
        t = stats[lang]['total']
        print(f"  {lang}: {k}/{t} ({100*k/t if t > 0 else 0:.1f}%)")


if __name__ == "__main__":
    main()
