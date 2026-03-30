#!/usr/bin/env python3
# src/disasm.py
# desassemblage des executables ELF avec angr
# filtre le runtime (startup, PLT, libc) et ne garde que le code utilisateur
# utilise les symboles DWARF pour les vrais noms de fonctions
# mode normal : sequentiel avec tqdm (local)
# mode batch : traite un fichier de jobs avec timeout (VM GCP)

import argparse
import json
import os
import re
import signal
import sys
import warnings

import yaml

# angr est tres verbeux, on coupe tout
warnings.filterwarnings("ignore")
os.environ["ANGR_DISABLE_UNICORN"] = "1"

import logging
logging.disable(logging.CRITICAL)

import angr
from tqdm import tqdm

# 10 MB max par binaire, au dela angr rame trop
MAX_FILE_SIZE = 10 * 1024 * 1024

# noms auto generes par angr quand il a pas de symbole
RE_SUB = re.compile(r"^sub_[0-9a-fA-F]+$")

# noms internes angr pour les sauts non resolus
ANGR_INTERNALS = {"UnresolvableJumpTarget", "UnresolvableCallTarget"}


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def extract_instructions(func):
    # on recupere les instructions de chaque bloc de la fonction
    insns = []
    for blk in func.blocks:
        try:
            for i in blk.capstone.insns:
                insns.append([i.mnemonic, i.op_str])
        except Exception:
            pass
    return insns


def extract_cfg_edges(func):
    # aretes du CFG (pour les futures approches CFG-based)
    edges = []
    try:
        for src, dst in func.graph.edges():
            edges.append([hex(src.addr), hex(dst.addr)])
    except Exception:
        pass
    return edges


def should_skip(func, skip_pfx, skip_plt, use_dwarf):
    name = func.name

    if name in ANGR_INTERNALS:
        return True

    if skip_plt and (func.is_plt or "@plt" in name):
        return True

    if use_dwarf and RE_SUB.match(name):
        return True

    if ".cold" in name:
        return True

    for pfx in skip_pfx:
        if name.startswith(pfx):
            return True

    return False


def check_has_dwarf(proj):
    try:
        obj = proj.loader.main_object
        for sec in obj.sections:
            if sec.name.startswith(".debug"):
                return True
    except Exception:
        pass
    return False


def disasm_one(bin_path, cfg_disasm):
    # desassemble un executuable et retourne les fonctions filtrees
    min_insns = cfg_disasm.get("min_instructions", 5)
    skip_pfx = cfg_disasm.get("skip_prefixes", [])
    skip_plt = cfg_disasm.get("skip_plt", True)
    do_cfg = cfg_disasm.get("extract_cfg", False)
    use_dwarf = cfg_disasm.get("use_dwarf_symbols", True)

    try:
        proj = angr.Project(bin_path, auto_load_libs=False)
        cfg_res = proj.analyses.CFGFast(normalize=True)
    except Exception as e:
        return None, False, 0, str(e).split("\n")[0]

    has_dwarf = check_has_dwarf(proj)
    nb_total = len(cfg_res.kb.functions)
    nb_filtered = 0

    kept = []
    for addr, func in sorted(cfg_res.kb.functions.items()):
        if should_skip(func, skip_pfx, skip_plt, use_dwarf):
            nb_filtered += 1
            continue

        insns = extract_instructions(func)
        if len(insns) < min_insns:
            nb_filtered += 1
            continue

        entry = {
            "name": func.name,
            "addr": hex(addr),
            "nb_instructions": len(insns),
            "instructions": insns,
            "cfg_edges": extract_cfg_edges(func) if do_cfg else [],
        }
        kept.append(entry)

    nb_kept = len(kept)
    return kept, has_dwarf, nb_total, None


# ---- mode normal : sequentiel avec tqdm (local) ----

def run_disasm(cfg, manifest, test_mode=False):
    bin_dir = cfg["paths"]["binaries"]
    out_dir = cfg["paths"]["disasm"]
    cfg_disasm = cfg["pipeline"]["disassembly"]
    test_src = cfg["paths"].get("test_sources", "data/sources/_test")
    compilers = list(cfg["pipeline"]["compilers"].keys())
    archs = list(cfg["pipeline"]["architectures"].keys())
    optims = cfg["pipeline"]["optimizations"]
    backend = cfg_disasm.get("backend", "angr")

    if backend != "angr":
        print(f"Backend '{backend}' pas supporte, seulement angr")
        return

    jobs = []
    for src_id, entry in manifest.items():
        if test_mode and test_src not in entry.get("source", ""):
            continue

        results = entry.get("results", {})
        for comp in compilers:
            if comp not in results:
                continue
            for arch in archs:
                if arch not in results[comp]:
                    continue
                for opt in optims:
                    if results[comp].get(arch, {}).get(opt, "") != "ok":
                        continue
                    jobs.append((src_id, entry, comp, arch, opt))

    print(f"{len(jobs)} binaires a desassembler\n")
    if not jobs:
        print("Rien a faire")
        return

    nb_ok, nb_skip, nb_err = 0, 0, 0
    nb_dwarf, nb_no_dwarf = 0, 0
    total_funcs = 0
    global_total, global_filtered = 0, 0

    for src_id, entry, comp, arch, opt in tqdm(jobs, desc="disasm"):
        bin_path = os.path.join(bin_dir, comp, arch, opt, src_id)

        if not os.path.exists(bin_path):
            tqdm.write(f"  [!] manquant: {bin_path}")
            nb_err += 1
            continue

        fsize = os.path.getsize(bin_path)
        if fsize > MAX_FILE_SIZE:
            tqdm.write(f"  [!] trop gros ({fsize // (1024*1024)}MB): {src_id}")
            nb_skip += 1
            continue

        funcs, has_dwarf, nb_total, err = disasm_one(bin_path, cfg_disasm)

        if funcs is None:
            tqdm.write(f"  [!] erreur {src_id} [{comp}/{arch}/{opt}]: {err}")
            nb_err += 1
            continue

        if has_dwarf:
            nb_dwarf += 1
        else:
            nb_no_dwarf += 1

        nb_kept = len(funcs)
        nb_filt = nb_total - nb_kept
        global_total += nb_total
        global_filtered += nb_filt

        if nb_kept == 0:
            nb_skip += 1
            continue

        result = {
            "source_id": src_id,
            "source_path": entry.get("source", ""),
            "compiler": comp,
            "arch": arch,
            "optim": opt,
            "backend": backend,
            "dataset": entry.get("dataset", ""),
            "problem": entry.get("problem", ""),
            "lang": entry.get("lang", ""),
            "has_dwarf": has_dwarf,
            "nb_functions_total": nb_total,
            "nb_functions_filtered": nb_filt,
            "nb_functions_kept": nb_kept,
            "functions": funcs,
        }

        json_path = os.path.join(out_dir, comp, arch, opt, f"{src_id}.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2)

        nb_ok += 1
        total_funcs += nb_kept

    print(f"\nResultat: {nb_ok} ok, {nb_skip} skip, {nb_err} erreurs")
    print(f"Fonctions: {global_total} trouvees, {global_filtered} filtrees, {total_funcs} gardees")
    print(f"DWARF: {nb_dwarf} avec symboles, {nb_no_dwarf} sans")


# ---- mode batch : traite un fichier de jobs avec timeout (VM GCP) ----

def alarm_handler(signum, frame):
    raise TimeoutError("angr timeout")


def run_batch(jobs_file, cfg, timeout=120):
    cfg_disasm = cfg["pipeline"]["disassembly"]

    # timeout via SIGALRM (Linux/Mac seulement)
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, alarm_handler)

    with open(jobs_file) as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"Batch: {len(lines)} jobs, timeout={timeout}s")

    for line in lines:
        parts = line.split()
        if len(parts) < 10:
            continue
        bp, jp, comp, arch, opt, sid, sp, ds, pb, lang = parts[:10]

        if not os.path.exists(bp):
            continue
        if os.path.getsize(bp) > MAX_FILE_SIZE:
            print(f"SKIP: {sid} trop gros")
            continue

        # timeout pour proteger contre angr qui bloque
        if hasattr(signal, "SIGALRM"):
            signal.alarm(timeout)

        try:
            funcs, has_dwarf, nb_total, err = disasm_one(bp, cfg_disasm)

            if funcs is None or not funcs:
                continue

            nb_kept = len(funcs)
            result = {
                "source_id": sid,
                "source_path": sp,
                "compiler": comp,
                "arch": arch,
                "optim": opt,
                "backend": "angr",
                "dataset": ds,
                "problem": pb,
                "lang": lang,
                "has_dwarf": has_dwarf,
                "nb_functions_total": nb_total,
                "nb_functions_filtered": nb_total - nb_kept,
                "nb_functions_kept": nb_kept,
                "functions": funcs,
            }

            os.makedirs(os.path.dirname(jp), exist_ok=True)
            with open(jp, "w") as f:
                json.dump(result, f)

        except TimeoutError:
            print(f"TIMEOUT: {sid} [{comp}/{arch}/{opt}]")
        except Exception as e:
            print(f"FAIL: {sid} [{comp}/{arch}/{opt}] {str(e)[:100]}")
        finally:
            if hasattr(signal, "SIGALRM"):
                signal.alarm(0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Desassemblage BSCD (angr)")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--mode", choices=["normal", "batch"], default="normal")
    parser.add_argument("--manifest", default="data/compile_manifest.json")
    parser.add_argument("--jobs-file", default=None, help="fichier de jobs (mode batch)")
    parser.add_argument("--timeout", type=int, default=120, help="timeout par binaire en sec (mode batch)")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if args.mode == "batch":
        if not args.jobs_file:
            print("Erreur: --jobs-file requis en mode batch")
            sys.exit(1)
        run_batch(args.jobs_file, cfg, args.timeout)

    else:
        d = cfg["pipeline"]["disassembly"]
        print(f"Backend: {d['backend']}")
        print(f"skip_plt: {d.get('skip_plt', True)}")
        print(f"use_dwarf_symbols: {d.get('use_dwarf_symbols', True)}")
        print(f"extract_cfg: {d.get('extract_cfg', False)}")
        print(f"min_instructions: {d['min_instructions']}")
        print(f"skip_prefixes: {d['skip_prefixes']}")

        if not os.path.exists(args.manifest):
            print(f"Erreur: {args.manifest} introuvable, lance compile.py d'abord")
            sys.exit(1)

        with open(args.manifest) as f:
            manifest = json.load(f)
        print(f"Manifest: {len(manifest)} source(s)\n")

        run_disasm(cfg, manifest, test_mode=args.test)
