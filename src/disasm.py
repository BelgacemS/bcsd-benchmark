#!/usr/bin/env python3
# src/disasm.py
# desassemblage des executables ELF avec angr
# filtre le runtime (startup, PLT, libc) et ne garde que le code utilisateur
# utilise les symboles DWARF pour les vrais noms de fonctions

import argparse
import json
import os
import re
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
    # blocs tries par adresse (comme IDA Pro et jTrans gen_funcstr)
    # format : [hex(addr), mnemonic, op_str] pour permettre la resolution JUMP_ADDR_N
    insns = []
    blocs_tries = sorted(func.blocks, key=lambda b: b.addr)
    for blk in blocs_tries:
        try:
            for i in blk.capstone.insns:
                insns.append([hex(i.address), i.mnemonic, i.op_str])
        except Exception:
            # certains blocs sont vides ou inaccessibles
            pass
    return insns


def extract_cfg_edges(func):
    # on extrait les aretes du CFG (pour les futures approches CFG-based)
    edges = []
    try:
        for src, dst in func.graph.edges():
            edges.append([hex(src.addr), hex(dst.addr)])
    except Exception:
        pass
    return edges


def should_skip(func, skip_pfx, skip_plt, use_dwarf):
    # on decide si on garde ou pas cette fonction
    name = func.name

    # noms internes angr
    if name in ANGR_INTERNALS:
        return True

    # PLT : on vire les stubs de la libc (printf@plt, etc.)
    if skip_plt and (func.is_plt or "@plt" in name):
        return True

    # sub_XXXX : angr a pas trouve de symbole, c'est du bruit
    if use_dwarf and RE_SUB.match(name):
        return True

    # cold path splits (gcc O2/O3 separe le hot/cold path, c'est pas une vraie fonction)
    if ".cold" in name:
        return True

    # skip_prefixes de la config
    for pfx in skip_pfx:
        if name.startswith(pfx):
            return True

    return False


def check_has_dwarf(proj):
    # on verifie si le binaire a des sections DWARF
    # c'est plus fiable que regarder les noms de fonctions
    try:
        obj = proj.loader.main_object
        for sec in obj.sections:
            if sec.name.startswith(".debug"):
                return True
    except Exception:
        pass
    return False


def disasm_one(bin_path, cfg_disasm):
    # on desassemble un executuable et on retourne les fonctions filtrees
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

    # on filtre les fonctions runtime/PLT/startup
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

    # on collecte les jobs a faire
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
        # les executables n'ont pas d'extension
        bin_path = os.path.join(bin_dir, comp, arch, opt, src_id)

        if not os.path.exists(bin_path):
            tqdm.write(f"  [!] manquant: {bin_path}")
            nb_err += 1
            continue

        # on skip les fichiers trop gros (angr rame)
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

        # on construit le JSON avec toutes les metadonnees
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

        # on ecrit le JSON en conservant la hierarchie
        json_path = os.path.join(out_dir, comp, arch, opt, f"{src_id}.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w") as f:
            json.dump(result, f, indent=2)

        nb_ok += 1
        total_funcs += nb_kept

    print(f"\nResultat: {nb_ok} ok, {nb_skip} skip, {nb_err} erreurs")
    print(f"Fonctions: {global_total} trouvees, {global_filtered} filtrees, {total_funcs} gardees")
    print(f"DWARF: {nb_dwarf} avec symboles, {nb_no_dwarf} sans")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Desassemblage BSCD (angr)")
    parser.add_argument("--config", default="config.yaml",
                        help="chemin vers config.yaml")
    parser.add_argument("--manifest", default="data/compile_manifest.json",
                        help="chemin vers compile_manifest.json")
    parser.add_argument("--test", action="store_true",
                        help="mode test: ne traite que les binaires de test")
    args = parser.parse_args()

    cfg = load_config(args.config)
    d = cfg["pipeline"]["disassembly"]
    print(f"Backend: {d['backend']}")
    print(f"skip_plt: {d.get('skip_plt', True)}")
    print(f"use_dwarf_symbols: {d.get('use_dwarf_symbols', True)}")
    print(f"extract_cfg: {d.get('extract_cfg', False)}")
    print(f"min_instructions: {d['min_instructions']}")
    print(f"skip_prefixes: {d['skip_prefixes']}")

    if not os.path.exists(args.manifest):
        print(f"Erreur: {args.manifest} introuvable, lance compile.py d'abord")
        exit(1)

    with open(args.manifest) as f:
        manifest = json.load(f)
    print(f"Manifest: {len(manifest)} source(s)\n")

    run_disasm(cfg, manifest, test_mode=args.test)
