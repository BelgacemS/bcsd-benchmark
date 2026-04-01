# fusionne les 91K .npy individuels en une matrice unique + index pickle
# a lancer UNE FOIS apres avoir pull les embeddings depuis GCP
import json
import pickle
import argparse
import numpy as np
from pathlib import Path
import yaml


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def consolidate(approach, emb_dir):
    index_path = emb_dir / "index.json"
    print(f"Index: {index_path}")
    with open(index_path) as f:
        index = json.load(f)

    npy_cache = {}
    vecs = []
    key_to_idx = {}
    idx_to_func_key = []
    idx_to_config_key = []
    func_meta = {}
    idx = 0
    nb_miss = 0

    for fk, entry in index.items():
        configs = entry.get("embeddings", {}).get(approach, {})
        if not configs:
            continue

        if fk not in func_meta:
            func_meta[fk] = {
                "source_id": entry.get("source_id", ""),
                "function": entry.get("function", ""),
                "dataset": entry.get("dataset", ""),
                "problem": entry.get("problem", ""),
                "lang": entry.get("lang", ""),
            }

        for ck, info in configs.items():
            path = info["path"]
            try:
                if path not in npy_cache:
                    npy_cache[path] = np.load(path)
                vecs.append(npy_cache[path][info["idx"]])
                key_to_idx[(fk, ck)] = idx
                idx_to_func_key.append(fk)
                idx_to_config_key.append(ck)
                idx += 1
            except Exception:
                nb_miss += 1

        # on vide le cache periodiquement pour limiter la RAM
        if len(npy_cache) > 10000:
            npy_cache.clear()

    if not vecs:
        print("Aucun vecteur trouve")
        return

    # matrice normalisee
    print(f"{len(vecs)} vecteurs ({nb_miss} manquants)")
    matrix = np.array(vecs, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix /= norms

    out_mat = emb_dir / f"{approach}_matrix.npy"
    out_meta = emb_dir / f"{approach}_meta.pkl"

    np.save(out_mat, matrix)
    with open(out_meta, "wb") as f:
        pickle.dump({
            "key_to_idx": key_to_idx,
            "idx_to_func_key": idx_to_func_key,
            "idx_to_config_key": idx_to_config_key,
            "func_meta": func_meta,
        }, f)

    print(f"Matrice: {out_mat} {matrix.shape} ({matrix.nbytes / 1e6:.1f} MB)")
    print(f"Meta: {out_meta}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--approach", default="palmtree")
    args = parser.parse_args()

    cfg = load_config(args.config)
    emb_dir = Path(cfg["paths"]["embeddings"])
    consolidate(args.approach, emb_dir)
