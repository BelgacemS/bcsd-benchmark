# genere les embeddings REFuSE (raw bytes -> vecteur)
# meme pipeline que palmtree : lit les disasm JSONs pour la liste de fonctions,
# extrait les raw bytes depuis les binaires, passe dans le modele, sauve dans index.json
#
# REFuSE travaille sur les octets bruts des fonctions, pas sur les instructions
# desassemblees. Mais on utilise les memes fonctions que palmtree/baseline
# (filtrees par angr dans disasm.py) pour que le benchmark soit comparable.

import sys
import json
import argparse
import numpy as np
from pathlib import Path
from tqdm import tqdm
import yaml

from elftools.elf.elffile import ELFFile


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


# --- extraction des raw bytes depuis les ELF ---

def _symbol_bytes(elf, file_data, sym):
    # recupere les octets machine d'un symbole STT_FUNC
    sz = int(sym["st_size"])
    val = int(sym["st_value"])
    shndx = sym["st_shndx"]

    if sz <= 0 or val <= 0 or not isinstance(shndx, int):
        return None

    sec = elf.get_section(shndx)
    if sec is None:
        return None

    # SHF_EXECINSTR : on veut seulement les sections executables
    if (int(sec["sh_flags"]) & 0x4) == 0:
        return None

    off = int(sec["sh_offset"]) + (val - int(sec["sh_addr"]))
    end = off + sz
    if off < 0 or end > len(file_data):
        return None

    return file_data[off:end]


def extract_func_bytes(bin_path, func_names):
    # lit le symtab du binaire ELF et retourne {nom: bytes} pour les fonctions demandees
    result = {}
    try:
        with open(bin_path, "rb") as f:
            data = f.read()
            f.seek(0)
            elf = ELFFile(f)

            symtab = elf.get_section_by_name(".symtab")
            if not symtab:
                return result

            targets = set(func_names)
            for sym in symtab.iter_symbols():
                if sym["st_info"]["type"] != "STT_FUNC":
                    continue
                name = sym.name.strip()
                if name not in targets:
                    continue
                raw = _symbol_bytes(elf, data, sym)
                if raw and len(raw) > 0:
                    result[name] = raw
    except Exception:
        pass
    return result


# --- chargement du modele REFuSE (JAX/Flax) ---

def load_refuse(repo_root, ckpt_path, trim_len, emb_dim):
    refuse_dir = repo_root / "model-evaluation" / "refuse"
    if not refuse_dir.exists():
        print(f"Erreur: {refuse_dir} introuvable")
        print("Clone le repo REFuSE dans lib/refuse/")
        sys.exit(1)

    sys.path.insert(0, str(refuse_dir))

    import jax
    from jax import numpy as jnp
    import optax
    from flax.training.train_state import TrainState
    from flax.training import checkpoints
    from utils.net_modules import REFUSE

    net = REFUSE(channels=emb_dim, window_size=8, stride=8, embd_size=8, log_stride=None)

    init_x = jnp.zeros((1, trim_len), dtype=jnp.int16)
    params = net.init({"params": jax.random.PRNGKey(0)}, init_x)

    tx = optax.chain(optax.clip(max_delta=1.0), optax.adam(learning_rate=0.005))
    state = TrainState.create(apply_fn=net.apply, params=params, tx=tx)
    state = checkpoints.restore_checkpoint(
        ckpt_dir=str(ckpt_path.parent),
        target=state,
        prefix=ckpt_path.name,
        step=None,
    )

    print(f"REFuSE charge (dim={emb_dim}, trim={trim_len})")
    return net, state, jnp


def encode_batch(net, state, jnp_mod, raw_list, trim_len):
    # chaque octet est un int16 (0-255), 256 = padding
    inp = np.full((len(raw_list), trim_len), 256, dtype=np.int16)
    for i, raw in enumerate(raw_list):
        arr = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)
        n = min(len(arr), trim_len)
        inp[i, :n] = arr[:n]

    emb = net.apply(state.params, jnp_mod.array(inp))
    return np.array(emb, dtype=np.float32)


# --- pipeline principale ---

def run_refuse(cfg, disasm_dir, bin_dir, emb_base):
    approach = "refuse"
    refuse_cfg = cfg["pipeline"]["similarity"]["approaches"].get("refuse", {})

    trim_len = refuse_cfg.get("trim_length", 250)
    emb_dim = refuse_cfg.get("embedding_dim", 128)
    batch_sz = refuse_cfg.get("batch_size", 512)
    # chemins relatifs au CWD (comme disasm_dir, emb_base dans le main)
    repo_root = Path(refuse_cfg.get("repo_root", "lib/refuse"))
    ckpt = Path(refuse_cfg.get("checkpoint",
        "lib/refuse/model-training/checkpoints/refuse_checkpoint_1/checkpoint"))

    json_files = sorted(disasm_dir.rglob("*.json"))
    if not json_files:
        print(f"Aucun JSON dans {disasm_dir}")
        return False

    print(f"{len(json_files)} fichiers de disasm")

    # passe 1 : extraire les raw bytes de chaque fonction
    # on utilise les memes fonctions que palmtree (filtrees par disasm.py)
    print("Passe 1 : extraction des raw bytes depuis les binaires...")
    all_data = []
    nb_skip = 0

    for jf in tqdm(json_files, desc="extraction"):
        try:
            with open(jf) as f:
                data = json.load(f)
        except Exception:
            continue

        funcs = data.get("functions", [])
        if not funcs:
            continue

        # le binaire correspondant est au meme chemin relatif dans bin_dir, sans .json
        rel = jf.relative_to(disasm_dir)
        bin_path = bin_dir / rel.with_suffix("")
        if not bin_path.exists():
            nb_skip += 1
            continue

        meta = {
            "source_id": data.get("source_id", ""),
            "dataset": data.get("dataset", ""),
            "problem": data.get("problem", ""),
            "lang": data.get("lang", ""),
        }
        parts = list(rel.parts)
        ck = f"{parts[0]}_{parts[1]}_{parts[2]}"

        func_names = [f["name"] for f in funcs]
        bytes_map = extract_func_bytes(bin_path, func_names)

        for name in func_names:
            raw = bytes_map.get(name)
            if raw:
                all_data.append((jf, meta, ck, name, raw, rel))

    if not all_data:
        print("Aucune fonction avec raw bytes")
        return False

    print(f"{len(all_data)} fonctions extraites ({nb_skip} binaires introuvables)")

    # chargement du modele
    net, state, jnp_mod = load_refuse(repo_root, ckpt, trim_len, emb_dim)

    # passe 2 : encoder par batch (batch fixe pour eviter la recompilation JIT de JAX)
    print("Passe 2 : encodage REFuSE...")
    all_embs = []
    for i in tqdm(range(0, len(all_data), batch_sz), desc="encode"):
        batch_raw = [d[4] for d in all_data[i:i + batch_sz]]
        emb = encode_batch(net, state, jnp_mod, batch_raw, trim_len)
        all_embs.append(emb)

    all_embs = np.vstack(all_embs)

    # passe 3 : sauvegarder les .npy et construire l'index
    print("Passe 3 : sauvegarde...")

    index_path = emb_base / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {}

    # grouper par fichier disasm (un .npy par fichier, comme palmtree)
    by_file = {}
    for i, (jf, meta, ck, fname, _, rel) in enumerate(all_data):
        k = str(jf)
        if k not in by_file:
            by_file[k] = {"meta": meta, "config_key": ck, "rel": rel, "names": [], "idxs": []}
        by_file[k]["names"].append(fname)
        by_file[k]["idxs"].append(i)

    nb_total = 0
    for info in by_file.values():
        mat = all_embs[info["idxs"]]
        out_path = emb_base / approach / info["rel"].with_suffix(".npy")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_path, mat)

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

    emb_base.mkdir(parents=True, exist_ok=True)
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
    bin_dir = Path(paths["binaries"])
    emb_base = Path(paths["embeddings"])

    if not disasm_dir.exists():
        print(f"Erreur: {disasm_dir} n'existe pas, lance d'abord disasm.py")
        sys.exit(1)

    if not bin_dir.exists():
        print(f"Erreur: {bin_dir} n'existe pas, lance d'abord compile.py")
        sys.exit(1)

    approaches = cfg["pipeline"]["similarity"]["approaches"]
    if not approaches.get("refuse", {}).get("enabled"):
        print("REFuSE pas active dans config.yaml")
        sys.exit(0)

    run_refuse(cfg, disasm_dir, bin_dir, emb_base)
