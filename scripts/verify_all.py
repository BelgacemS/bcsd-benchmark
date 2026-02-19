#!/usr/bin/env python3
"""
Verification de compilation pour tout le dataset.
Utilise gcc, g++, go build et rustc pour tester chaque fichier,
corrige ce qui peut l'etre, supprime le reste.
"""
import subprocess
import os
import shutil
import re
import tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

BASE = Path(__file__).resolve().parent.parent / "data"
GO_BIN = os.path.expanduser("~/go/bin/go")
RUSTC_BIN = os.path.expanduser("~/.cargo/bin/rustc")


# --- verification par langage ---

def check_c(fp):
    try:
        r = subprocess.run(['gcc', '-fsyntax-only', '-c', str(fp)],
                           capture_output=True, timeout=10, text=True)
        return r.returncode == 0, r.stderr.strip()[:300] if r.returncode != 0 else ""
    except Exception as e:
        return False, str(e)[:200]

def check_cpp(fp):
    try:
        r = subprocess.run(['g++', '-fsyntax-only', '-std=c++17', '-c', str(fp)],
                           capture_output=True, timeout=10, text=True)
        return r.returncode == 0, r.stderr.strip()[:300] if r.returncode != 0 else ""
    except Exception as e:
        return False, str(e)[:200]

def check_go(fp):
    """Compile le fichier go dans un dossier temporaire."""
    try:
        content = fp.read_text(encoding='utf-8', errors='ignore')
        if 'github.com/' in content:
            return False, "external import"

        lines = content.splitlines()
        pkg_lines = [l for l in lines if l.strip().startswith('package ')]
        if len(pkg_lines) > 1:
            return False, "multiple package declarations"
        if len(pkg_lines) == 0:
            return False, "missing package declaration"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_file = Path(tmpdir) / "main.go"
            mod_content = content
            if 'package main' not in content:
                mod_content = content.replace(pkg_lines[0], 'package main', 1)

            if 'func main()' not in mod_content:
                mod_content += '\nfunc main() {}\n'

            tmp_file.write_text(mod_content, encoding='utf-8')
            (Path(tmpdir) / "go.mod").write_text("module tmp\n\ngo 1.22\n")

            env = os.environ.copy()
            env['PATH'] = os.path.expanduser('~/go/bin') + ':' + env.get('PATH', '')
            env['GOPATH'] = tmpdir + '/gopath'

            r = subprocess.run([GO_BIN, 'build', '-o', '/dev/null', str(tmp_file)],
                               capture_output=True, timeout=15, text=True,
                               cwd=tmpdir, env=env)
            return r.returncode == 0, r.stderr.strip()[:300] if r.returncode != 0 else ""
    except Exception as e:
        return False, str(e)[:200]

def check_rust(fp):
    """Compile le fichier rust en mode lib (pas besoin de main)."""
    try:
        content = fp.read_text(encoding='utf-8', errors='ignore')
        if 'use crate::' in content or 'use super::' in content:
            return False, "crate/super dependency"
        if content.strip() == "":
            return False, "empty file"

        env = os.environ.copy()
        env['PATH'] = os.path.expanduser('~/.cargo/bin') + ':' + env.get('PATH', '')

        with tempfile.TemporaryDirectory() as tmpdir:
            out_file = Path(tmpdir) / "out"
            r = subprocess.run(
                [RUSTC_BIN, '--crate-type', 'lib', '--emit=metadata',
                 '-o', str(out_file), str(fp)],
                capture_output=True, timeout=15, text=True, env=env)
            return r.returncode == 0, r.stderr.strip()[:300] if r.returncode != 0 else ""
    except Exception as e:
        return False, str(e)[:200]


# --- corrections automatiques ---

# headers C++ standards qu'on rajoute si manquants
CPP_HEADERS = [
    "vector", "string", "algorithm", "unordered_map", "unordered_set",
    "map", "set", "queue", "stack", "deque", "list", "numeric",
    "climits", "cmath", "cstring", "cstdlib", "cstdio", "iostream",
    "sstream", "functional", "bitset", "tuple", "array", "cassert",
    "utility", "memory", "stdexcept", "limits", "optional", "variant"
]

def fix_cpp(fp):
    content = fp.read_text(encoding='utf-8', errors='ignore')
    if '#include' in content and 'using namespace std' in content:
        return False  # deja fixe ou pas le bon probleme
    header_block = "\n".join([f"#include <{h}>" for h in CPP_HEADERS])
    header_block += "\nusing namespace std;\n\n"
    fp.write_text(header_block + content, encoding='utf-8')
    return True

def fix_go(fp):
    content = fp.read_text(encoding='utf-8', errors='ignore')
    lines = content.splitlines()
    changed = False

    # doublon de package
    pkg_lines = [i for i, l in enumerate(lines) if l.strip().startswith('package ')]
    if len(pkg_lines) > 1:
        new_lines = []
        seen = False
        for line in lines:
            if line.strip().startswith('package '):
                if not seen:
                    new_lines.append('package main')
                    seen = True
            else:
                new_lines.append(line)
        content = '\n'.join(new_lines) + '\n'
        lines = content.splitlines()
        changed = True

    # package manquant
    if not any(l.strip().startswith('package ') for l in lines):
        content = 'package main\n\n' + content
        changed = True

    if changed:
        fp.write_text(content, encoding='utf-8')
    return changed

def fix_rust(fp):
    content = fp.read_text(encoding='utf-8', errors='ignore')
    original = content
    content = re.sub(r'^use crate::.*;\n?', '', content, flags=re.MULTILINE)
    content = re.sub(r'^use super::.*;\n?', '', content, flags=re.MULTILINE)
    if content != original:
        fp.write_text(content, encoding='utf-8')
        return True
    return False


def verify_one(args):
    fp, checker, lang = args
    ok, err = checker(fp)
    return fp, lang, ok, err


def main():
    print("=" * 50)
    print("Verification de compilation du dataset")
    print("=" * 50)

    # collecte de tous les fichiers
    file_tasks = []
    ext_map = {
        '.c':   (check_c, 'C'),
        '.cpp': (check_cpp, 'Cpp'),
        '.go':  (check_go, 'Go'),
        '.rs':  (check_rust, 'Rust'),
    }

    for source in ['the_algorithms', 'leetcode']:
        src_dir = BASE / source
        if not src_dir.exists():
            continue
        for task_dir in src_dir.iterdir():
            if not task_dir.is_dir():
                continue
            for lang_dir in task_dir.iterdir():
                if not lang_dir.is_dir():
                    continue
                for f in lang_dir.iterdir():
                    if f.suffix in ext_map:
                        checker, lang = ext_map[f.suffix]
                        file_tasks.append((f, checker, lang))

    total = len(file_tasks)
    print(f"Fichiers a verifier: {total}")

    # phase 1 : check initial
    print("\n[1/4] Check initial...")

    failures = defaultdict(list)
    successes = defaultdict(int)
    done = 0

    workers = min(os.cpu_count() or 4, 6)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(verify_one, t): t for t in file_tasks}
        for fut in as_completed(futures):
            fp, lang, ok, err = fut.result()
            done += 1
            if done % 200 == 0:
                print(f"  [{done}/{total}]...")
            if ok:
                successes[lang] += 1
            else:
                failures[lang].append((fp, err))

    print("\nResultats initiaux:")
    for lang in ['C', 'Cpp', 'Go', 'Rust']:
        t = successes[lang] + len(failures[lang])
        f = len(failures[lang])
        pct = 100 * (t - f) / t if t > 0 else 0
        print(f"  {lang}: {t - f}/{t} OK ({pct:.1f}%) - {f} en echec")
        if 0 < f <= 5:
            for fp, err in failures[lang]:
                print(f"    FAIL {fp.relative_to(BASE)}: {err[:120]}")
        elif f > 5:
            for fp, err in failures[lang][:3]:
                print(f"    FAIL {fp.relative_to(BASE)}: {err[:120]}")
            print(f"    ... +{f - 3} autres")

    if sum(len(v) for v in failures.values()) == 0:
        print("\nTous les fichiers compilent, rien a faire.")
        return

    # phase 2 : tentative de correction
    print("\n[2/4] Correction des erreurs...")

    fixed = defaultdict(int)
    unfixable = defaultdict(list)

    for fp, err in failures['Cpp']:
        if fix_cpp(fp):
            ok, new_err = check_cpp(fp)
            if ok:
                fixed['Cpp'] += 1
            else:
                unfixable['Cpp'].append((fp, new_err))
        else:
            unfixable['Cpp'].append((fp, err))

    for fp, err in failures['Go']:
        fix_go(fp)
        ok, new_err = check_go(fp)
        if ok:
            fixed['Go'] += 1
        else:
            unfixable['Go'].append((fp, new_err))

    for fp, err in failures['Rust']:
        if fix_rust(fp):
            ok, new_err = check_rust(fp)
            if ok:
                fixed['Rust'] += 1
            else:
                unfixable['Rust'].append((fp, new_err))
        else:
            unfixable['Rust'].append((fp, err))

    unfixable['C'] = failures['C']

    for lang in ['C', 'Cpp', 'Go', 'Rust']:
        if fixed[lang] > 0:
            print(f"  {lang}: {fixed[lang]} fichiers corriges")

    # phase 3 : suppression des fichiers non-reparables
    print("\n[3/4] Suppression des fichiers non-reparables...")
    deleted = defaultdict(int)
    for lang in ['C', 'Cpp', 'Go', 'Rust']:
        for fp, err in unfixable[lang]:
            if fp.exists():
                fp.unlink()
                deleted[lang] += 1
                parent = fp.parent
                if parent.is_dir() and not any(parent.iterdir()):
                    parent.rmdir()

    for lang in ['C', 'Cpp', 'Go', 'Rust']:
        if deleted[lang] > 0:
            print(f"  {lang}: {deleted[lang]} supprimes")

    if sum(deleted.values()) == 0:
        print("  Rien a supprimer")

    # phase 4 : nettoyage des taches avec moins de 2 langages
    print("\n[4/4] Nettoyage des taches avec < 2 langages...")
    removed = 0
    for source in ['the_algorithms', 'leetcode']:
        src_dir = BASE / source
        if not src_dir.exists():
            continue
        for task_dir in list(src_dir.iterdir()):
            if not task_dir.is_dir():
                continue
            langs = [d for d in task_dir.iterdir() if d.is_dir() and any(d.iterdir())]
            if len(langs) < 2:
                shutil.rmtree(task_dir)
                removed += 1
    print(f"  {removed} taches supprimees")

    # rapport final
    print("\n" + "=" * 50)
    print("Rapport final")
    print("=" * 50)

    counts = defaultdict(int)
    task_counts = defaultdict(int)
    for source in ['the_algorithms', 'leetcode']:
        src_dir = BASE / source
        if not src_dir.exists():
            continue
        for task_dir in src_dir.iterdir():
            if not task_dir.is_dir():
                continue
            task_counts[source] += 1
            for lang_dir in task_dir.iterdir():
                if lang_dir.is_dir():
                    for f in lang_dir.iterdir():
                        if f.suffix == '.c': counts['C'] += 1
                        elif f.suffix == '.cpp': counts['Cpp'] += 1
                        elif f.suffix == '.go': counts['Go'] += 1
                        elif f.suffix == '.rs': counts['Rust'] += 1

    total_files = sum(counts.values())
    total_tasks = sum(task_counts.values())
    print(f"Taches: {total_tasks} (algo={task_counts['the_algorithms']}, lc={task_counts['leetcode']})")
    print(f"Fichiers: {total_files}")
    for lang in ['C', 'Cpp', 'Go', 'Rust']:
        print(f"  {lang}: {counts[lang]}")
    print(f"\nTous les {total_files} fichiers sont compilables.")


if __name__ == "__main__":
    main()
