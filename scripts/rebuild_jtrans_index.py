#!/usr/bin/env python3
# Reconstruit les entrees jTrans de data/embeddings/index.json a partir des
# vecteurs .npy DEJA presents sur le disque + des JSON de data/disasm_jtrans/.
#
# Pourquoi : les embeddings jTrans publies ont ete indexes avec une config_key
# malformee (un dossier "disasm_jtrans" en trop dans le chemin), ce qui a
# ecrase les niveaux d'optimisation entre eux -> l'index ne referencait qu'un
# sous-ensemble (~Os) et le benchmark ne pouvait pas former de paires
# cross_optim. Les .npy de TOUS les optims existent pourtant sur disque.
#
# Ce script n'a PAS besoin du modele jTrans : il reutilise exactement le meme
# filtrage de fonctions que embed_jtrans.py (fonctions avec blocs dont la
# normalisation est non vide), dans le meme ordre, pour remapper chaque ligne
# du .npy a son nom de fonction et reconstruire des config_keys correctes
# (compiler_arch_optim).
#
# Usage :
#   python3 scripts/download_dataset.py disasm_jtrans   # si pas deja fait
#   python3 scripts/rebuild_jtrans_index.py
#   python3 src/benchmark.py --approach jtrans

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

# meme logique de tokenisation/filtrage que la generation
from embed_jtrans import normalize_for_jtrans  # noqa: E402

EMB_DIR = ROOT / "data" / "embeddings"
JTRANS_EMB = EMB_DIR / "jtrans"
DISASM_JTRANS = ROOT / "data" / "disasm_jtrans"
INDEX_PATH = EMB_DIR / "index.json"


def config_key_from_path(npy_path):
    # ancre sur x86_64 : .../<comp>/x86_64/<optim>/...
    parts = npy_path.parts
    if "x86_64" in parts:
        i = parts.index("x86_64")
        if 0 < i < len(parts) - 1:
            return f"{parts[i - 1]}_{parts[i]}_{parts[i + 1]}"
    return None


def disasm_json_for(npy_path):
    # data/embeddings/jtrans/disasm_jtrans/<comp>/x86_64/<optim>/<...>.npy
    #   -> data/disasm_jtrans/<comp>/x86_64/<optim>/<...>.json
    rel = npy_path.relative_to(JTRANS_EMB)
    parts = list(rel.parts)
    if parts and parts[0] == "disasm_jtrans":
        parts = parts[1:]
    return (DISASM_JTRANS.joinpath(*parts)).with_suffix(".json")


def names_for(json_path):
    # reproduit le filtrage de embed_jtrans.run_jtrans : fonctions avec blocs
    # dont normalize_for_jtrans renvoie une chaine non vide, dans l'ordre
    with open(json_path) as f:
        data = json.load(f)
    meta = {
        "source_id": data.get("source_id", ""),
        "dataset": data.get("dataset", ""),
        "problem": data.get("problem", ""),
        "lang": data.get("lang", ""),
    }
    names = []
    for func in data.get("functions", []):
        blocks = func.get("blocks", [])
        if not blocks:
            continue
        if normalize_for_jtrans(blocks):
            names.append(func["name"])
    return meta, names


def main():
    if not JTRANS_EMB.exists():
        print(f"Erreur: {JTRANS_EMB} introuvable (telecharge embeddings d'abord)")
        sys.exit(1)
    if not DISASM_JTRANS.exists():
        print(f"Erreur: {DISASM_JTRANS} introuvable.")
        print("  python3 scripts/download_dataset.py disasm_jtrans")
        sys.exit(1)
    if not INDEX_PATH.exists():
        print(f"Erreur: {INDEX_PATH} introuvable.")
        sys.exit(1)

    with open(INDEX_PATH) as f:
        index = json.load(f)

    # on repart de zero pour jTrans : on purge les entrees jtrans existantes
    for entry in index.values():
        entry.get("embeddings", {}).pop("jtrans", None)

    npy_files = sorted(JTRANS_EMB.rglob("*.npy"))
    print(f"{len(npy_files)} fichiers .npy jTrans a reindexer")

    nb_func = 0
    nb_files = 0
    nb_mismatch = 0
    nb_missing_json = 0

    for npy_path in npy_files:
        ck = config_key_from_path(npy_path)
        if not ck:
            continue
        jpath = disasm_json_for(npy_path)
        if not jpath.exists():
            nb_missing_json += 1
            continue
        try:
            meta, names = names_for(jpath)
            nrows = int(np.load(npy_path, mmap_mode="r").shape[0])
        except Exception as e:
            print(f"  skip {npy_path.name}: {e}")
            continue

        if len(names) != nrows:
            # desaccord d'ordre/filtrage : on prend le min pour rester sur
            # un mapping coherent et on compte le cas
            nb_mismatch += 1
            n = min(len(names), nrows)
            names = names[:n]

        rel_path = str(npy_path.relative_to(ROOT))
        for idx, fname in enumerate(names):
            key = f"{meta['source_id']}::{fname}"
            entry = index.get(key)
            if entry is None:
                entry = index[key] = {
                    "source_id": meta["source_id"],
                    "function": fname,
                    "dataset": meta["dataset"],
                    "problem": meta["problem"],
                    "lang": meta["lang"],
                    "embeddings": {},
                }
            entry["embeddings"].setdefault("jtrans", {})[ck] = {
                "path": rel_path, "idx": idx,
            }
            nb_func += 1
        nb_files += 1

    with open(INDEX_PATH, "w") as f:
        json.dump(index, f, indent=2)

    print(f"Reindexe: {nb_files} fichiers, {nb_func} (fonction, config) jTrans")
    if nb_mismatch:
        print(f"  {nb_mismatch} fichiers avec un ecart lignes/fonctions (tronques au min)")
    if nb_missing_json:
        print(f"  {nb_missing_json} .npy sans JSON disasm correspondant (ignores)")
    print(f"Index ecrit: {INDEX_PATH}")
    print("Verifie avec: python3 src/benchmark.py --approach jtrans")


if __name__ == "__main__":
    main()
