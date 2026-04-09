# desassemblage BB-level pour jTrans
# jTrans a besoin des blocs de base avec adresses pour resoudre les JUMP_ADDR_N
# scan data/binaries/ directement (pas besoin de manifest)
# sort dans data/disasm_jtrans/ avec structure par blocs de base
# meme filtrage que disasm.py (PLT, DWARF, min insns, skip prefixes)

import argparse
import json
import os
import re
import warnings
import multiprocessing as mp
from functools import partial

import yaml

warnings.filterwarnings("ignore")
os.environ["ANGR_DISABLE_UNICORN"] = "1"

import logging
logging.disable(logging.CRITICAL)

import angr
from pathlib import Path
from tqdm import tqdm

MAX_FILE_SIZE = 10 * 1024 * 1024

RE_SUB = re.compile(r"^sub_[0-9a-fA-F]+$")

ANGR_INTERNALS = {"UnresolvableJumpTarget", "UnresolvableCallTarget"}

LANG_MAP = {"C": "c", "Cpp": "cpp", "C++": "cpp", "cpp": "cpp"}


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def extract_blocks(func):
    # blocs de base tries par adresse, avec instructions [addr, mnem, op_str]
    blocks = []
    blocs_tries = sorted(func.blocks, key=lambda b: b.addr)
    for blk in blocs_tries:
        insns = []
        try:
            for i in blk.capstone.insns:
                insns.append([hex(i.address), i.mnemonic, i.op_str])
        except Exception:
            continue
        if insns:
            blocks.append({
                "addr": hex(blk.addr),
                "instructions": insns,
            })
    return blocks


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


def count_insns(blocks):
    return sum(len(b["instructions"]) for b in blocks)


def disasm_one(bin_path, cfg_disasm):
    min_insns = cfg_disasm.get("min_instructions", 5)
    skip_pfx = cfg_disasm.get("skip_prefixes", [])
    skip_plt = cfg_disasm.get("skip_plt", True)
    use_dwarf = cfg_disasm.get("use_dwarf_symbols", True)

    try:
        proj = angr.Project(bin_path, auto_load_libs=False)
        cfg_res = proj.analyses.CFGFast(normalize=True)
    except Exception as e:
        return None, False, str(e).split("\n")[0]

    has_dwarf = check_has_dwarf(proj)

    kept = []
    for addr, func in sorted(cfg_res.kb.functions.items()):
        if should_skip(func, skip_pfx, skip_plt, use_dwarf):
            continue

        blocks = extract_blocks(func)
        nb = count_insns(blocks)
        if nb < min_insns:
            continue

        kept.append({
            "name": func.name,
            "addr": hex(addr),
            "nb_blocks": len(blocks),
            "nb_instructions": nb,
            "blocks": blocks,
        })

    return kept, has_dwarf, None


def parse_bin_path(bin_path, bin_dir):
    # extrait les metadonnees depuis le chemin du binaire
    # format GCP complet : compiler/arch/optim/dataset/problem/lang__impl_NN (6 parts)
    # format test local  : compiler/arch/optim/problem/lang__impl_NN (5 parts)
    rel = Path(bin_path).relative_to(bin_dir)
    parts = rel.parts

    if len(parts) < 5:
        return None

    comp = parts[0]
    arch = parts[1]
    opt = parts[2]
    impl_name = parts[-1]

    # lang depuis le nom du fichier : C__impl_01 -> c
    lang_raw = impl_name.split("__")[0]
    lang = LANG_MAP.get(lang_raw, lang_raw.lower())

    if len(parts) >= 6:
        # format complet : dataset/problem/impl
        dataset = parts[3]
        problem = parts[4]
        src_id = "/".join(parts[3:])
    else:
        # format test : problem/impl
        problem = parts[3]
        dataset = problem
        src_id = "/".join(parts[3:])

    return comp, arch, opt, dataset, problem, lang, src_id


def process_one(bp, bin_dir, out_dir, cfg_disasm):
    fsize = os.path.getsize(bp)
    if fsize > MAX_FILE_SIZE:
        return "skip", 0

    parsed = parse_bin_path(bp, bin_dir)
    if parsed is None:
        return "err", 0

    comp, arch, opt, dataset, problem, lang, src_id = parsed

    funcs, has_dwarf, err = disasm_one(bp, cfg_disasm)

    if funcs is None:
        return "err", 0

    if not funcs:
        return "skip", 0

    result = {
        "source_id": src_id,
        "compiler": comp,
        "arch": arch,
        "optim": opt,
        "dataset": dataset,
        "problem": problem,
        "lang": lang,
        "has_dwarf": has_dwarf,
        "nb_functions_kept": len(funcs),
        "functions": funcs,
    }

    json_path = os.path.join(out_dir, comp, arch, opt, f"{src_id}.json")
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)

    return "ok", len(funcs)


def run_disasm(cfg, max_workers=0, test_mode=False):
    bin_dir = cfg["paths"]["binaries"]
    out_dir = cfg["paths"]["disasm_jtrans"]
    cfg_disasm = cfg["pipeline"]["disassembly"]

    # scan tous les binaires (on ignore les .dSYM et autres)
    all_bins = []
    for root, dirs, files in os.walk(bin_dir):
        # skip les dossiers .dSYM (macOS debug info)
        dirs[:] = [d for d in dirs if not d.endswith(".dSYM")]
        for f in files:
            fp = os.path.join(root, f)
            # verifie que c'est un binaire (pas un .plist, .yml etc.)
            if "." not in f:
                all_bins.append(fp)

    print(f"{len(all_bins)} binaires trouves dans {bin_dir}")

    if test_mode:
        all_bins = all_bins[:20]
        print(f"  mode test: limite a {len(all_bins)} binaires")

    # reprise auto : on vire ceux deja traites
    todo = []
    for bp in all_bins:
        parsed = parse_bin_path(bp, bin_dir)
        if parsed is None:
            continue
        comp, arch, opt, dataset, problem, lang, src_id = parsed
        json_path = os.path.join(out_dir, comp, arch, opt, f"{src_id}.json")
        if not os.path.exists(json_path):
            todo.append(bp)

    skipped = len(all_bins) - len(todo)
    if skipped > 0:
        print(f"{skipped} deja traites, {len(todo)} restants")

    if not todo:
        print("Rien a faire")
        return

    nb_workers = max_workers if max_workers > 0 else max(1, mp.cpu_count() - 1)
    print(f"Parallelisation: {nb_workers} workers")

    worker = partial(process_one, bin_dir=bin_dir, out_dir=out_dir, cfg_disasm=cfg_disasm)

    nb_ok, nb_skip, nb_err = 0, 0, 0
    total_funcs = 0

    with mp.Pool(nb_workers) as pool:
        for status, nb_funcs in tqdm(
            pool.imap_unordered(worker, todo, chunksize=4),
            total=len(todo),
            desc="disasm_jtrans",
        ):
            if status == "ok":
                nb_ok += 1
                total_funcs += nb_funcs
            elif status == "skip":
                nb_skip += 1
            else:
                nb_err += 1

    print(f"\nResultat: {nb_ok} ok, {nb_skip} skip, {nb_err} erreurs")
    print(f"Fonctions: {total_funcs} gardees")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Desassemblage BB-level pour jTrans")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--test", action="store_true",
                        help="mode test: seulement les 20 premiers binaires")
    parser.add_argument("--workers", type=int, default=0,
                        help="nb de workers (0 = cpu_count - 1)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    d = cfg["pipeline"]["disassembly"]
    print(f"Backend: angr (BB-level pour jTrans)")
    print(f"skip_plt: {d.get('skip_plt', True)}")
    print(f"use_dwarf_symbols: {d.get('use_dwarf_symbols', True)}")
    print(f"min_instructions: {d['min_instructions']}")
    print(f"Sortie: {cfg['paths']['disasm_jtrans']}\n")

    run_disasm(cfg, max_workers=args.workers, test_mode=args.test)
