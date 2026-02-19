#!/usr/bin/env python3
"""
Pipeline de compilation du dataset BCSD.
Compile chaque fichier source avec differents compilateurs et niveaux
d'optimisation. La config est dans compile_config.json.

Arborescence de sortie (meme structure que la source) :
  data/binaries/<source>/<task>/<Lang>/<impl>_<compiler>_<opt>.bin
"""

import json
import os
import subprocess
import shutil
import hashlib
import tempfile
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent


def load_config(config_path=None):
    if config_path is None:
        config_path = SCRIPT_DIR / "compile_config.json"
    with open(config_path) as f:
        return json.load(f)


def sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def compile_c_cpp(source_path, output_path, compiler_path, opt_level, extra_flags, timeout):
    """Compile un fichier C ou C++.
    Essaie de linker normalement, et si le fichier n'a pas de main(),
    on compile en objet (-c) a la place.
    """
    cmd = [compiler_path, opt_level, str(source_path), "-o", str(output_path)]
    cmd.extend(extra_flags)
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        if r.returncode == 0 and output_path.exists():
            return True, ""

        # si le probleme c'est juste qu'il n'y a pas de main, on compile en .o
        if "undefined reference to" in r.stderr and "main" in r.stderr:
            obj_path = output_path.with_suffix(".o")
            cmd_obj = [compiler_path, "-c", opt_level, str(source_path), "-o", str(obj_path)]
            # on rajoute les flags sauf ceux de link (-l...)
            cmd_obj.extend([f for f in extra_flags if not f.startswith("-l")])
            r2 = subprocess.run(cmd_obj, capture_output=True, timeout=timeout, text=True)
            if r2.returncode == 0 and obj_path.exists():
                # on renomme le .o en .bin pour rester coherent
                obj_path.rename(output_path)
                return True, ""
            return False, r2.stderr.strip()[:200]

        return False, r.stderr.strip()[:200]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:200]


def compile_go(source_path, output_path, go_bin, opt_level, timeout):
    """Compile un fichier Go."""
    try:
        content = source_path.read_text(encoding='utf-8', errors='ignore')

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_src = Path(tmpdir) / "main.go"
            mod_content = content

            # s'assurer qu'on a package main
            lines = content.splitlines()
            pkg_lines = [l for l in lines if l.strip().startswith('package ')]
            if pkg_lines and 'package main' not in content:
                mod_content = content.replace(pkg_lines[0], 'package main', 1)

            # ajouter un main vide si absent
            if 'func main()' not in mod_content:
                mod_content += '\nfunc main() {}\n'

            tmp_src.write_text(mod_content, encoding='utf-8')
            (Path(tmpdir) / "go.mod").write_text("module tmp\n\ngo 1.22\n")

            env = os.environ.copy()
            go_dir = str(Path(go_bin).parent)
            env['PATH'] = go_dir + ':' + env.get('PATH', '')
            env['GOPATH'] = tmpdir + '/gopath'

            # options d'optimisation Go
            gcflags = ""
            if opt_level == "noinline":
                gcflags = "-gcflags=-l"
            # "default" = pas de flags speciaux

            cmd = [go_bin, "build"]
            if gcflags:
                cmd.append(gcflags)
            cmd.extend(["-o", str(output_path), str(tmp_src)])

            r = subprocess.run(cmd, capture_output=True, timeout=timeout,
                               text=True, cwd=tmpdir, env=env)
            if r.returncode == 0 and output_path.exists():
                return True, ""
            return False, r.stderr.strip()[:200]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:200]


def compile_rust(source_path, output_path, rustc_bin, opt_level, timeout):
    """Compile un fichier Rust."""
    try:
        env = os.environ.copy()
        rustc_dir = str(Path(rustc_bin).parent)
        env['PATH'] = rustc_dir + ':' + env.get('PATH', '')

        # pour les fichiers sans main, on compile en lib
        content = source_path.read_text(encoding='utf-8', errors='ignore')
        has_main = 'fn main()' in content

        cmd = [rustc_bin, "-C", f"opt-level={opt_level}"]
        if not has_main:
            cmd.extend(["--crate-type", "lib"])
        cmd.extend(["-o", str(output_path), str(source_path)])

        r = subprocess.run(cmd, capture_output=True, timeout=timeout,
                           text=True, env=env)
        if r.returncode == 0 and output_path.exists():
            return True, ""
        return False, r.stderr.strip()[:200]
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:200]


def compile_one(task):
    """Compile un fichier source avec un compilateur et un niveau d'opt donnes."""
    source_path = task["source"]
    output_path = task["output"]
    lang = task["lang"]
    compiler = task["compiler"]
    opt = task["opt"]
    config = task["config"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    timeout = config.get("timeout", 30)

    start = time.time()

    if lang in ("C", "Cpp"):
        ok, err = compile_c_cpp(
            source_path, output_path,
            compiler["path"], opt,
            compiler.get("flags", []), timeout
        )
    elif lang == "Go":
        ok, err = compile_go(
            source_path, output_path,
            os.path.expanduser(compiler["path"]),
            opt, timeout
        )
    elif lang == "Rust":
        ok, err = compile_rust(
            source_path, output_path,
            os.path.expanduser(compiler["path"]),
            opt, timeout
        )
    else:
        return {"ok": False, "error": f"langage inconnu: {lang}", **task}

    elapsed = round(time.time() - start, 2)

    result = {
        "ok": ok,
        "source": str(source_path),
        "output": str(output_path),
        "lang": lang,
        "compiler": compiler["name"],
        "opt": opt,
        "time": elapsed,
    }

    if ok:
        result["size"] = output_path.stat().st_size
        result["sha256"] = sha256(output_path)
    else:
        result["error"] = err

    return result


def build_tasks(config):
    """Genere la liste de toutes les compilations a faire."""
    source_dir = PROJECT_DIR / config["source_dir"]
    output_dir = PROJECT_DIR / config["output_dir"]
    compilers = config["compilers"]

    tasks = []
    ext_to_lang = {".c": "C", ".cpp": "Cpp", ".go": "Go", ".rs": "Rust"}

    for source_name in ["rosetta_code", "leetcode", "the_algorithms"]:
        src_base = source_dir / source_name
        if not src_base.exists():
            continue

        for task_dir in sorted(src_base.iterdir()):
            if not task_dir.is_dir():
                continue
            task_name = task_dir.name

            for lang_dir in sorted(task_dir.iterdir()):
                if not lang_dir.is_dir():
                    continue
                lang = lang_dir.name

                if lang not in compilers:
                    continue

                for src_file in sorted(lang_dir.iterdir()):
                    if src_file.suffix not in ext_to_lang:
                        continue

                    impl_stem = src_file.stem  # ex: impl_01

                    for compiler_cfg in compilers[lang]:
                        for opt in compiler_cfg["opt_levels"]:
                            # nom du binaire: impl_01_gcc_O2.bin
                            opt_suffix = opt.replace("-", "").replace("=", "")
                            bin_name = f"{impl_stem}_{compiler_cfg['name']}_{opt_suffix}.bin"

                            out_path = output_dir / source_name / task_name / lang / bin_name

                            tasks.append({
                                "source": src_file,
                                "output": out_path,
                                "lang": lang,
                                "compiler": compiler_cfg,
                                "opt": opt,
                                "config": config,
                                "source_name": source_name,
                                "task": task_name,
                            })

    return tasks


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline de compilation BCSD")
    parser.add_argument("--config", type=str, default=None,
                        help="chemin vers le fichier de config JSON")
    parser.add_argument("--clean", action="store_true",
                        help="nettoyer le dossier binaries avant de compiler")
    args = parser.parse_args()

    config = load_config(args.config)
    output_dir = PROJECT_DIR / config["output_dir"]

    print("=" * 50)
    print("Pipeline de compilation BCSD")
    print("=" * 50)
    print(f"Source: {config['source_dir']}")
    print(f"Output: {config['output_dir']}")
    print(f"Compilateurs:")
    for lang, comps in config["compilers"].items():
        for c in comps:
            print(f"  {lang}: {c['name']} ({len(c['opt_levels'])} niveaux d'opt)")

    if args.clean and output_dir.exists():
        print(f"\nNettoyage de {output_dir}...")
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # generer toutes les taches
    tasks = build_tasks(config)
    print(f"\n{len(tasks)} compilations a effectuer")

    if len(tasks) == 0:
        print("Rien a faire.")
        return

    # lancer les compilations en parallele
    workers = config.get("workers", 4)
    results = []
    done = 0

    stats = defaultdict(lambda: {"ok": 0, "fail": 0})

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(compile_one, t): t for t in tasks}
        for fut in as_completed(futures):
            r = fut.result()
            results.append(r)
            done += 1

            key = f"{r['lang']}_{r['compiler']}"
            if r["ok"]:
                stats[key]["ok"] += 1
            else:
                stats[key]["fail"] += 1

            if done % 50 == 0 or done == len(tasks):
                print(f"  [{done}/{len(tasks)}]")

    # rapport
    print("\n" + "=" * 50)
    print("Resultats")
    print("=" * 50)

    total_ok = sum(s["ok"] for s in stats.values())
    total_fail = sum(s["fail"] for s in stats.values())

    for key in sorted(stats.keys()):
        s = stats[key]
        total = s["ok"] + s["fail"]
        print(f"  {key}: {s['ok']}/{total} OK")

    print(f"\nTotal: {total_ok}/{total_ok + total_fail} compilations reussies")

    # sauvegarder les metadonnees de compilation
    meta = {
        "compilation_date": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total_compilations": len(results),
        "successful": total_ok,
        "failed": total_fail,
        "config": config,
        "results_summary": {}
    }

    # resume par source/langage
    for r in results:
        src = r.get("source_name", "unknown")
        lang = r["lang"]
        k = f"{src}/{lang}"
        if k not in meta["results_summary"]:
            meta["results_summary"][k] = {"ok": 0, "fail": 0}
        if r["ok"]:
            meta["results_summary"][k]["ok"] += 1
        else:
            meta["results_summary"][k]["fail"] += 1

    with open(output_dir / "compilation_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    # sauvegarder les erreurs pour debug
    errors = [r for r in results if not r["ok"]]
    if errors:
        error_log = []
        for e in errors:
            error_log.append({
                "source": str(e.get("source", "")),
                "compiler": e.get("compiler", ""),
                "opt": e.get("opt", ""),
                "error": e.get("error", "")
            })
        with open(output_dir / "compilation_errors.json", "w") as f:
            json.dump(error_log, f, indent=2)
        print(f"\n{len(errors)} erreurs loguees dans {output_dir}/compilation_errors.json")

    print(f"Metadata dans {output_dir}/compilation_metadata.json")
    print("Done.")


if __name__ == "__main__":
    main()
