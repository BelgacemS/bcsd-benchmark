# pipeline de compilation BSCD
# compile les sources C/C++ en executables ELF x86-64
# mode local : tout en un (staging + compile + manifest)
# modes VM : prepare, manifest, disasm-jobs (pour parallelisation sur GCP)

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


# boilerplate C pour les fichiers LeetCode sans includes
C_BOILERPLATE = (
    "#include <stdio.h>\n"
    "#include <stdlib.h>\n"
    "#include <string.h>\n"
    "#include <math.h>\n"
    "#include <limits.h>\n"
    "#include <stdbool.h>\n"
    "#include <ctype.h>\n\n"
)

# boilerplate C++ pour les fichiers LeetCode sans includes
CPP_BOILERPLATE = (
    "#include <algorithm>\n"
    "#include <climits>\n"
    "#include <cmath>\n"
    "#include <cstring>\n"
    "#include <iostream>\n"
    "#include <map>\n"
    "#include <queue>\n"
    "#include <set>\n"
    "#include <sstream>\n"
    "#include <stack>\n"
    "#include <string>\n"
    "#include <unordered_map>\n"
    "#include <unordered_set>\n"
    "#include <vector>\n"
    "using namespace std;\n\n"
    "struct ListNode {\n"
    "    int val; ListNode *next;\n"
    "    ListNode() : val(0), next(nullptr) {}\n"
    "    ListNode(int x) : val(x), next(nullptr) {}\n"
    "};\n"
    "struct TreeNode {\n"
    "    int val; TreeNode *left, *right;\n"
    "    TreeNode() : val(0), left(nullptr), right(nullptr) {}\n"
    "    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}\n"
    "};\n\n"
)

RE_HAS_INCLUDE = re.compile(r"^\s*#\s*include\b", re.MULTILINE)
RE_ATCODER_HEADER = re.compile(r'#\s*include\s*[<"]atcoder/')


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def build_dir_map(cfg):
    # mapping nom de dossier -> lang_key via dir_names dans la config
    dm = {}
    for lang_key, lang_cfg in cfg["pipeline"]["languages"].items():
        for dn in lang_cfg.get("dir_names", []):
            dm[dn] = lang_key
    return dm


def build_ext_map(cfg):
    # mapping extension -> lang_key
    em = {}
    for lang_key, lang_cfg in cfg["pipeline"]["languages"].items():
        for ext in lang_cfg["extensions"]:
            em[ext] = lang_key
    return em


def find_sources(src_dir, dir_map, ext_map):
    # cherche les fichiers dans les dossiers dont le nom matche un langage
    sources = []
    src_dir = Path(src_dir)
    for f in sorted(src_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix not in ext_map:
            continue
        lang_dir_name = f.parent.name
        if lang_dir_name not in dir_map:
            continue
        if ext_map.get(f.suffix) != dir_map[lang_dir_name]:
            continue
        sources.append(f)
    return sources


def extract_meta(src_path, src_dir, dir_map):
    # extrait dataset, problem, lang_dir, filename depuis le chemin
    rel = src_path.relative_to(src_dir)
    parts = list(rel.parts)

    lang_dir = parts[-2]
    filename = Path(parts[-1]).stem
    sub_parts = parts[:-2]

    if len(sub_parts) >= 2:
        dataset = sub_parts[0]
        problem = sub_parts[1]
    elif len(sub_parts) == 1:
        dataset = sub_parts[0]
        problem = sub_parts[0]
    else:
        dataset = "unknown"
        problem = "unknown"

    sub_path = "/".join(sub_parts)
    key = f"{sub_path}/{lang_dir}__{filename}"

    return {
        "key": key,
        "lang": dir_map[lang_dir],
        "lang_dir": lang_dir,
        "dataset": dataset,
        "problem": problem,
        "filename": filename,
        "sub_path": sub_path,
        "rel_src": str(rel),
    }


def prepare_source(src_path, lang_key):
    # boilerplate pour les fichiers sans includes
    code = src_path.read_text(errors="replace")

    if RE_ATCODER_HEADER.search(code):
        return None

    if not RE_HAS_INCLUDE.search(code):
        bp = CPP_BOILERPLATE if lang_key == "cpp" else C_BOILERPLATE
        code = bp + code

    return code


def build_flags(cfg, comp_name, lang_key, arch_name, opt):
    pipe = cfg["pipeline"]
    comp_cfg = pipe["compilers"][comp_name]
    lang_cfg = pipe["languages"][lang_key]
    arch_cfg = pipe["architectures"][arch_name]

    flags = list(pipe["compile_flags"]["common"])
    flags.extend(arch_cfg.get("flags", []))
    # debug flags par compilateur (gcc != clang)
    flags.extend(comp_cfg.get("debug_flags", ["-g"]))
    flags.append(f"-std={lang_cfg['standard']}")
    flags.append(f"-{opt}")

    # flags C pour eviter les erreurs sur du code old-style
    if lang_key == "c":
        flags.extend(["-Wno-implicit-int", "-Wno-implicit-function-declaration", "-D_GNU_SOURCE"])

    return flags


# ---- mode local : staging + compile + manifest en une passe ----

def stage_sources(sources, src_dir, staging_dir, dir_map):
    # copie dans le staging en preservant la structure de dossiers
    staged = {}
    staging = Path(staging_dir)

    for src in sources:
        meta = extract_meta(src, src_dir, dir_map)
        code = prepare_source(src, meta["lang"])

        if code is None:
            print(f"  skip (header atcoder) : {src.name}")
            continue

        rel = src.relative_to(src_dir)
        staged_path = staging / rel
        staged_path.parent.mkdir(parents=True, exist_ok=True)
        staged_path.write_text(code, encoding="utf-8")

        staged[meta["key"]] = {
            "rel_src": meta["rel_src"],
            "lang": meta["lang"],
            "lang_dir": meta["lang_dir"],
            "dataset": meta["dataset"],
            "problem": meta["problem"],
            "filename": meta["filename"],
            "source": str(src),
        }

    return staged


def generate_script(staged, cfg, bin_pfx="/workspace/binaries", src_pfx="/workspace/sources"):
    # genere le script shell avec toutes les commandes
    compilers = cfg["pipeline"]["compilers"]
    archs = cfg["pipeline"]["architectures"]
    optims = cfg["pipeline"]["optimizations"]

    lines = [
        "#!/bin/bash",
        "# script de compilation genere par compile.py",
        "",
        "total=0",
        "ok=0",
        "fail=0",
        "",
        "try_compile() {",
        '    total=$((total + 1))',
        '    local tag="$1"',
        '    local outdir="$2"',
        '    shift 2',
        '    mkdir -p "$outdir"',
        '    if "$@" 2>/dev/null; then',
        '        echo "OK $tag"',
        '        ok=$((ok + 1))',
        '    else',
        '        echo "FAIL $tag"',
        '        fail=$((fail + 1))',
        '    fi',
        "}",
        "",
    ]

    nb_jobs = 0
    for key, info in sorted(staged.items()):
        src_file = f"{src_pfx}/{info['rel_src']}"
        key_parts = key.rsplit("/", 1)
        key_dir = key_parts[0] if len(key_parts) > 1 else ""
        key_file = key_parts[-1]

        for comp_name, comp_cfg in compilers.items():
            comp_bin = comp_cfg.get(info["lang"])
            if not comp_bin:
                continue

            for arch_name in archs:
                for opt in optims:
                    flags = build_flags(cfg, comp_name, info["lang"], arch_name, opt)
                    out_dir = f"{bin_pfx}/{comp_name}/{arch_name}/{opt}"
                    if key_dir:
                        out_dir += f"/{key_dir}"
                    out_file = f"{out_dir}/{key_file}"
                    tag = f"{key}|{comp_name}|{arch_name}|{opt}"

                    cmd_parts = [comp_bin] + flags + ["-o", out_file, src_file]
                    cmd = " ".join(cmd_parts)
                    lines.append(f'try_compile "{tag}" "{out_dir}" {cmd}')
                    nb_jobs += 1

    lines.append("")
    lines.append('echo ""')
    lines.append('echo "SUMMARY $total $ok $fail"')
    lines.append("")

    return "\n".join(lines), nb_jobs


def run_local(script_path, staging_dir, bin_dir):
    # compilation locale (machine x86 native)
    script = Path(script_path).read_text()
    script = script.replace("/workspace/sources", os.path.abspath(staging_dir))
    script = script.replace("/workspace/binaries", os.path.abspath(bin_dir))

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(script)
        local_script = f.name

    print("Compilation locale")
    print(f"  sources  : {staging_dir}")
    print(f"  binaires : {bin_dir}")
    print()

    try:
        proc = subprocess.Popen(
            ["bash", local_script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )

        stdout_lines = []
        for line in proc.stdout:
            stdout_lines.append(line)
            s = line.strip()
            if s.startswith("FAIL"):
                print(f"  {s}")
            elif s.startswith("SUMMARY"):
                print(f"  {s}")

        proc.wait()
        stderr = proc.stderr.read()
        stdout = "".join(stdout_lines)

        return stdout, stderr, proc.returncode
    finally:
        os.unlink(local_script)


def parse_results(stdout, staged):
    # construit le manifest depuis la sortie du script
    manifest = {}

    for key, info in staged.items():
        manifest[key] = {
            "source": info["source"],
            "lang": info["lang"],
            "dataset": info["dataset"],
            "problem": info["problem"],
            "lang_dir": info["lang_dir"],
            "filename": info["filename"],
            "results": {},
        }

    nb_ok = 0
    nb_fail = 0

    for line in stdout.splitlines():
        line = line.strip()
        if not (line.startswith("OK ") or line.startswith("FAIL ")):
            continue

        status = "ok" if line.startswith("OK ") else "fail"
        tag = line.split(" ", 1)[1]
        parts = tag.split("|")
        if len(parts) != 4:
            continue

        key, comp, arch, opt = parts
        if key not in manifest:
            continue

        res = manifest[key]["results"]
        if comp not in res:
            res[comp] = {}
        if arch not in res[comp]:
            res[comp][arch] = {}
        res[comp][arch][opt] = status

        if status == "ok":
            nb_ok += 1
        else:
            nb_fail += 1

    return manifest, nb_ok, nb_fail


def print_stats(manifest):
    stats_comp = {}
    stats_opt = {}

    for entry in manifest.values():
        for comp, arch_res in entry["results"].items():
            for arch, opt_res in arch_res.items():
                for opt, status in opt_res.items():
                    stats_comp.setdefault(comp, {"ok": 0, "fail": 0})
                    stats_comp[comp][status] += 1
                    stats_opt.setdefault(opt, {"ok": 0, "fail": 0})
                    stats_opt[opt][status] += 1

    if stats_comp:
        print("\nPar compilateur:")
        for c, s in sorted(stats_comp.items()):
            print(f"  {c}: {s['ok']} ok, {s['fail']} fail")

    if stats_opt:
        print("\nPar optimisation:")
        for o, s in sorted(stats_opt.items()):
            print(f"  {o}: {s['ok']} ok, {s['fail']} fail")


def run_local_mode(cfg, src_dir, bin_dir):
    # mode local : staging + compile + manifest, tout en un
    bin_dir.mkdir(parents=True, exist_ok=True)

    dir_map = build_dir_map(cfg)
    ext_map = build_ext_map(cfg)

    print(f"Sources : {src_dir}")
    print(f"Sortie  : {bin_dir}")
    print(f"Langages: {list(dir_map.keys())}")
    print()

    sources = find_sources(src_dir, dir_map, ext_map)
    print(f"{len(sources)} fichiers trouves")

    if not sources:
        print("Rien a compiler")
        return

    with tempfile.TemporaryDirectory(prefix="bscd_staging_") as staging_dir:
        print("Preparation des sources (staging)")
        staged = stage_sources(sources, src_dir, staging_dir, dir_map)
        print(f"  {len(staged)} fichiers prepares")

        if not staged:
            print("Aucun fichier a compiler apres filtrage")
            return

        script_path = os.path.join(staging_dir, "compile.sh")
        script, nb_jobs = generate_script(staged, cfg)
        with open(script_path, "w") as f:
            f.write(script)
        print(f"  {nb_jobs} compilations a lancer")
        print()

        stdout, stderr, rc = run_local(script_path, staging_dir, str(bin_dir))

        if stderr and stderr.strip():
            print(f"\nStderr : {stderr[:500]}")

        manifest, nb_ok, nb_fail = parse_results(stdout or "", staged)

        total = nb_ok + nb_fail
        pct = (nb_ok / total * 100) if total else 0
        print(f"\n{nb_ok}/{total} compiles ({pct:.0f}% de reussite)")
        print_stats(manifest)

        manifest_path = Path("data") / "compile_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"\nManifest ecrit : {manifest_path}")


# ---- modes VM : prepare / manifest / disasm-jobs ----
# utilises par gcp_build.py pour decouper le travail et paralleliser

def prepare_vm(cfg, src_dir, bin_dir, work_dir):
    # injecte le boilerplate en place et genere compile_cmds.txt
    dir_map = build_dir_map(cfg)
    ext_map = build_ext_map(cfg)
    sources = find_sources(src_dir, dir_map, ext_map)

    nb_inj, nb_del = 0, 0
    for src in sources:
        lang_key = dir_map[src.parent.name]
        code = prepare_source(src, lang_key)
        if code is None:
            src.unlink()
            nb_del += 1
            continue
        # reecrit seulement si le boilerplate a ete injecte
        original = src.read_text(errors="replace")
        if code != original:
            src.write_text(code, encoding="utf-8")
            nb_inj += 1

    print(f"Boilerplate: {nb_inj} injectes, {nb_del} supprimes (atcoder)")

    # re-scan apres suppression des fichiers atcoder
    sources = find_sources(src_dir, dir_map, ext_map)
    print(f"{len(sources)} fichiers source")

    # generation des commandes de compilation (une par ligne, pour xargs)
    compilers = cfg["pipeline"]["compilers"]
    archs = cfg["pipeline"]["architectures"]
    optims = cfg["pipeline"]["optimizations"]

    cmds = []
    for src in sources:
        meta = extract_meta(src, src_dir, dir_map)
        key_parts = meta["key"].rsplit("/", 1)
        key_dir = key_parts[0] if len(key_parts) > 1 else ""
        key_file = key_parts[-1]

        for comp_name, comp_cfg in compilers.items():
            comp_bin = comp_cfg.get(meta["lang"])
            if not comp_bin:
                continue
            for arch_name in archs:
                for opt in optims:
                    flags = build_flags(cfg, comp_name, meta["lang"], arch_name, opt)
                    out_dir = f"{bin_dir}/{comp_name}/{arch_name}/{opt}"
                    if key_dir:
                        out_dir += f"/{key_dir}"
                    out_file = f"{out_dir}/{key_file}"
                    tag = f"{meta['key']}|{comp_name}|{arch_name}|{opt}"
                    fl = " ".join(flags)
                    cmd = (f"mkdir -p {out_dir} && {comp_bin} {fl} "
                           f"-o {out_file} {src} 2>/dev/null "
                           f'&& echo "OK {tag}" '
                           f'|| echo "FAIL {tag}"')
                    cmds.append(cmd)

    cmds_path = work_dir / "compile_cmds.txt"
    with open(cmds_path, "w") as f:
        f.write("\n".join(cmds) + "\n")
    print(f"compile_cmds.txt: {len(cmds)} commandes -> {cmds_path}")


def gen_manifest(cfg, src_dir, bin_dir, work_dir):
    # parcourt les binaires produits et verifie ce qui a compile ou pas
    dir_map = build_dir_map(cfg)
    ext_map = build_ext_map(cfg)
    sources = find_sources(src_dir, dir_map, ext_map)

    compilers = cfg["pipeline"]["compilers"]
    archs = cfg["pipeline"]["architectures"]
    optims = cfg["pipeline"]["optimizations"]

    manifest = {}
    nb_ok, nb_fail = 0, 0

    for src in sources:
        meta = extract_meta(src, src_dir, dir_map)
        key = meta["key"]
        key_parts = key.rsplit("/", 1)
        key_dir = key_parts[0] if len(key_parts) > 1 else ""
        key_file = key_parts[-1]

        if key not in manifest:
            manifest[key] = {
                "source": f"data/sources/{meta['rel_src']}",
                "lang": meta["lang"],
                "dataset": meta["dataset"],
                "problem": meta["problem"],
                "lang_dir": meta["lang_dir"],
                "filename": meta["filename"],
                "results": {},
            }

        for comp_name, comp_cfg in compilers.items():
            if not comp_cfg.get(meta["lang"]):
                continue
            manifest[key]["results"].setdefault(comp_name, {})

            for arch_name in archs:
                manifest[key]["results"][comp_name].setdefault(arch_name, {})

                for opt in optims:
                    out_dir = f"{bin_dir}/{comp_name}/{arch_name}/{opt}"
                    if key_dir:
                        out_dir += f"/{key_dir}"
                    out_file = f"{out_dir}/{key_file}"

                    if os.path.isfile(out_file):
                        manifest[key]["results"][comp_name][arch_name][opt] = "ok"
                        nb_ok += 1
                    else:
                        manifest[key]["results"][comp_name][arch_name][opt] = "fail"
                        nb_fail += 1

    manifest_path = work_dir / "compile_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    total = nb_ok + nb_fail
    pct = (nb_ok / total * 100) if total else 0
    print(f"Manifest: {len(manifest)} sources, {nb_ok}/{total} ok ({pct:.0f}%)")
    print(f"  -> {manifest_path}")


def gen_disasm_jobs(cfg, bin_dir, work_dir):
    # lit le manifest et genere la liste de jobs pour le desassemblage
    manifest_path = work_dir / "compile_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    disasm_dir = Path(cfg["paths"]["disasm"])
    jobs = []

    for sid, entry in manifest.items():
        for comp, arch_res in entry.get("results", {}).items():
            for arch, opt_res in arch_res.items():
                for opt, status in opt_res.items():
                    if status != "ok":
                        continue
                    key_parts = sid.rsplit("/", 1)
                    key_dir = key_parts[0] if len(key_parts) > 1 else ""
                    key_file = key_parts[-1]

                    bp = f"{bin_dir}/{comp}/{arch}/{opt}"
                    if key_dir:
                        bp += f"/{key_dir}"
                    bp += f"/{key_file}"

                    jp = f"{disasm_dir}/{comp}/{arch}/{opt}/{sid}.json"
                    sp = entry.get("source", "")
                    ds = entry.get("dataset", "")
                    pb = entry.get("problem", "")
                    lang = entry.get("lang", "")
                    jobs.append(f"{bp} {jp} {comp} {arch} {opt} {sid} {sp} {ds} {pb} {lang}")

    jobs_path = work_dir / "disasm_jobs.txt"
    with open(jobs_path, "w") as f:
        f.write("\n".join(jobs) + "\n")
    print(f"disasm_jobs.txt: {len(jobs)} jobs -> {jobs_path}")


def main():
    parser = argparse.ArgumentParser(description="Compilation BSCD")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--mode", choices=["local", "prepare", "manifest", "disasm-jobs"],
                        default="local")
    parser.add_argument("--src-dir", default=None, help="override dossier sources")
    parser.add_argument("--bin-dir", default=None, help="override dossier binaires")
    parser.add_argument("--work-dir", default=None, help="dossier de travail (VM: /workspace)")
    parser.add_argument("--test", action="store_true", help="utilise les sources de test")
    args = parser.parse_args()

    cfg = load_config(args.config)

    # chemins : les flags CLI overrident la config
    if args.src_dir:
        src_dir = Path(args.src_dir)
    elif args.test:
        src_dir = Path(cfg["paths"]["test_sources"])
    else:
        src_dir = Path(cfg["paths"]["sources"])

    bin_dir = Path(args.bin_dir) if args.bin_dir else Path(cfg["paths"]["binaries"])
    work_dir = Path(args.work_dir) if args.work_dir else src_dir.parent

    # disasm-jobs n'a pas besoin des sources (il lit le manifest)
    if args.mode != "disasm-jobs" and not src_dir.exists():
        print(f"Erreur : dossier source introuvable : {src_dir}")
        sys.exit(1)

    if args.mode == "local":
        run_local_mode(cfg, src_dir, bin_dir)
    elif args.mode == "prepare":
        prepare_vm(cfg, src_dir, bin_dir, work_dir)
    elif args.mode == "manifest":
        gen_manifest(cfg, src_dir, bin_dir, work_dir)
    elif args.mode == "disasm-jobs":
        gen_disasm_jobs(cfg, bin_dir, work_dir)


if __name__ == "__main__":
    main()
