# baseline de features manuelles pour le benchmark BSCD
# chaque fonction est representee par un vecteur de 16 features statistiques
# normalise en z-score sur l'ensemble du dataset

import argparse
import json
import sys
import numpy as np
from pathlib import Path
from tqdm import tqdm

import yaml


ARITH = {"add", "sub", "imul", "idiv", "mul", "div", "inc", "dec", "neg", "lea"}
TRANSFER = {"mov", "push", "pop", "lea", "xchg"}
CONTROL = {"jmp", "je", "jne", "jg", "jl", "jge", "jle", "ja", "jb",
           "call", "ret", "jnz", "jz", "js", "jns", "jbe", "jae"}
CMP = {"cmp", "test"}
STACK = {"push", "pop"}


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def extract_features(insns):
    # 16 features par fonction
    nb = len(insns)
    if nb == 0:
        return np.zeros(16)

    mnemonics = [m for m, _ in insns]
    operands = [o for _, o in insns]

    nb_arith = sum(1 for m in mnemonics if m in ARITH)
    nb_transfer = sum(1 for m in mnemonics if m in TRANSFER)
    nb_control = sum(1 for m in mnemonics if m in CONTROL)
    nb_cmp = sum(1 for m in mnemonics if m in CMP)
    nb_stack = sum(1 for m in mnemonics if m in STACK)
    nb_call = sum(1 for m in mnemonics if m == "call")
    nb_ret = sum(1 for m in mnemonics if m == "ret")

    unique_ops = len(set(mnemonics))

    nb_reg = 0
    nb_mem = 0
    nb_imm = 0
    for op in operands:
        if not op:
            continue
        # on compte par operande (split sur virgule)
        for part in op.split(","):
            part = part.strip()
            if not part:
                continue
            if "[" in part:
                nb_mem += 1
            elif part.startswith("0x") or part.isdigit():
                nb_imm += 1
            elif any(r in part for r in ["ax", "bx", "cx", "dx", "si", "di",
                                         "sp", "bp", "ip", "r8", "r9", "r1",
                                         "xmm", "ymm"]):
                nb_reg += 1

    return np.array([
        nb,
        nb_arith,
        nb_transfer,
        nb_control,
        nb_cmp,
        nb_stack,
        nb_call,
        nb_ret,
        nb_arith / nb,
        nb_transfer / nb,
        nb_control / nb,
        nb_cmp / nb,
        unique_ops,
        nb_reg,
        nb_mem,
        nb_imm,
    ], dtype=np.float32)


def run_baseline(cfg, disasm_dir, emb_base):
    approach = "baseline"
    json_files = sorted(disasm_dir.rglob("*.json"))
    if not json_files:
        print(f"Aucun JSON dans {disasm_dir}")
        return False

    print(f"{len(json_files)} fichiers de disasm")

    # passe 1 : extraire toutes les features (pour le z-score)
    print("Passe 1 : extraction des features...")
    all_data = []
    for jf in tqdm(json_files, desc="features"):
        try:
            with open(jf) as f:
                data = json.load(f)
        except Exception:
            continue

        meta = {
            "source_id": data.get("source_id", ""),
            "dataset": data.get("dataset", ""),
            "problem": data.get("problem", ""),
            "lang": data.get("lang", ""),
        }
        rel = jf.relative_to(disasm_dir)
        parts = list(rel.parts)
        compiler, arch, optim = parts[0], parts[1], parts[2]
        config_key = f"{compiler}_{arch}_{optim}"

        for func in data.get("functions", []):
            insns = func.get("instructions", [])
            if not insns:
                continue
            feat = extract_features(insns)
            all_data.append((jf, meta, config_key, func["name"], feat, rel))

    if not all_data:
        print("Aucune fonction trouvee")
        return False

    # z-score sur toutes les features
    print(f"\nNormalisation z-score sur {len(all_data)} fonctions...")
    all_feats = np.array([d[4] for d in all_data])
    mu = all_feats.mean(axis=0)
    sigma = all_feats.std(axis=0)
    sigma[sigma == 0] = 1
    all_feats_norm = (all_feats - mu) / sigma

    # passe 2 : sauvegarder les embeddings et construire l'index
    print("Passe 2 : sauvegarde des embeddings...")

    # charger l'index existant ou en creer un nouveau
    index_path = emb_base / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {}

    # grouper par fichier disasm pour sauver un .npy par fichier
    by_file = {}
    for i, (jf, meta, config_key, fname, _, rel) in enumerate(all_data):
        key = str(jf)
        if key not in by_file:
            by_file[key] = {"meta": meta, "config_key": config_key,
                            "rel": rel, "names": [], "indices": []}
        by_file[key]["names"].append(fname)
        by_file[key]["indices"].append(i)

    nb_total = 0
    for file_key, info in tqdm(by_file.items(), desc="sauvegarde"):
        indices = info["indices"]
        emb_matrix = all_feats_norm[indices]

        out_path = emb_base / approach / info["rel"].with_suffix(".npy")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_path, emb_matrix)

        for idx, fname in enumerate(info["names"]):
            func_key = f"{info['meta']['source_id']}::{fname}"
            if func_key not in index:
                index[func_key] = {
                    "source_id": info["meta"]["source_id"],
                    "function": fname,
                    "dataset": info["meta"]["dataset"],
                    "problem": info["meta"]["problem"],
                    "lang": info["meta"]["lang"],
                    "embeddings": {},
                }
            if approach not in index[func_key]["embeddings"]:
                index[func_key]["embeddings"][approach] = {}
            index[func_key]["embeddings"][approach][info["config_key"]] = {
                "path": str(out_path),
                "idx": idx,
            }
            nb_total += 1

    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nTermine: {nb_total} fonctions encodees, index dans {index_path}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    paths = cfg["paths"]

    disasm_dir = Path(paths["disasm"])
    emb_base = Path(paths["embeddings"])

    if not disasm_dir.exists():
        print(f"Erreur: {disasm_dir} n'existe pas, lance d'abord disasm.py")
        sys.exit(1)

    run_baseline(cfg, disasm_dir, emb_base)
