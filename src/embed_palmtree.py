import sys
import re
import json
import argparse
import numpy as np
from pathlib import Path
from tqdm import tqdm

import yaml
import torch

# imports PalmTree (renomme de bert_pytorch en palmtree dans le repo)
ROOT = Path(__file__).resolve().parent.parent
PALMTREE_DIR = ROOT / "lib" / "palmtree"

sys.path.insert(0, str(PALMTREE_DIR / "src"))

import palmtree
import palmtree.model
import palmtree.model.bert
import palmtree.model.embedding
import palmtree.model.embedding.bert
import palmtree.model.embedding.position
import palmtree.model.embedding.segment
import palmtree.model.embedding.token
import palmtree.model.transformer
import palmtree.model.attention
import palmtree.model.attention.multi_head
import palmtree.model.attention.single
import palmtree.model.utils
import palmtree.model.utils.feed_forward
import palmtree.model.utils.sublayer
import palmtree.model.utils.gelu
import palmtree.model.language_model

# le pickle attend le namespace bert_pytorch, faut creer les alias
for _mn in list(sys.modules.keys()):
    if _mn.startswith("palmtree"):
        sys.modules[_mn.replace("palmtree", "bert_pytorch", 1)] = sys.modules[_mn]

sys.path.insert(0, str(PALMTREE_DIR / "pre-trained_model"))

# detection GPU (ROCm ou CUDA)
import config as palmtree_config

if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    palmtree_config.USE_CUDA = True
    print(f"GPU: {torch.cuda.get_device_name(0)}")
else:
    DEVICE = torch.device("cpu")
    palmtree_config.USE_CUDA = False
    print("CPU mode (pas de GPU detecte)")

import vocab as palmtree_vocab


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def normalize_instruction(mnemonic, op_str):
    # Capstone -> format PalmTree ("mov rax [ rbp + 0x8 ]", espaces, pas de virgules)
    if not op_str or not op_str.strip():
        return mnemonic

    clean = op_str.replace(",", "")
    # regex un peu sale mais ca fait le job
    tokens = re.findall(r'[\w.]+|[+\-\*\[\]]', clean)

    out = []
    for tok in tokens:
        # grandes adresses hex -> placeholder "address"
        if re.match(r'^0x[0-9a-fA-F]+$', tok):
            val = int(tok, 16)
            if val > 0xFFFF:
                out.append("address")
                continue
        out.append(tok)

    return mnemonic + " " + " ".join(out)


class PalmTreeEncoder:

    def __init__(self, model_path, vocab_path, batch_size=512, device=None):
        self.device = device or DEVICE
        print(f"Chargement du vocab: {vocab_path}")
        self.vocab = palmtree_vocab.WordVocab.load_vocab(str(vocab_path))
        print(f"  vocab size: {len(self.vocab)}")

        print(f"Chargement du modele: {model_path} (device={self.device})")
        self.model = torch.load(str(model_path), weights_only=False, map_location=self.device)
        self.model.to(self.device)
        self.model.eval()
        self.batch_size = batch_size
        print("  PalmTree pret")

    def encode(self, instructions):
        if not instructions:
            return np.zeros((0, 128))

        all_embs = []
        for i in range(0, len(instructions), self.batch_size):
            batch = instructions[i:i + self.batch_size]
            all_embs.append(self._encode_batch(batch))
        return np.vstack(all_embs)

    def _encode_batch(self, text):
        seg_labels = []
        seqs = []
        for t in text:
            toks = t.split(" ")
            l = (len(toks) + 2) * [1]
            s = self.vocab.to_seq(t)
            s = [3] + s + [2]
            seg_labels.append((l[:20] + [0] * 20)[:20])
            seqs.append((s[:20] + [0] * 20)[:20])

        seg_labels = torch.LongTensor(seg_labels).to(self.device)
        seqs = torch.LongTensor(seqs).to(self.device)

        with torch.no_grad():
            enc = self.model.forward(seqs, seg_labels)
            res = torch.mean(enc, dim=1)
        return res.cpu().numpy()


def process_disasm_file(json_path, encoder):
    # JSON disasm -> (metadata, emb_matrix, func_names)
    with open(json_path) as f:
        data = json.load(f)

    # on recupere les metadonnees du disasm
    meta = {
        "source_id": data.get("source_id", ""),
        "dataset": data.get("dataset", ""),
        "problem": data.get("problem", ""),
        "lang": data.get("lang", ""),
    }

    funcs = data.get("functions", [])
    if not funcs:
        return meta, None, []

    names = []
    embs = []

    for func in funcs:
        insns = func.get("instructions", [])
        if not insns:
            continue

        normalized = [normalize_instruction(m, o) for m, o in insns]
        enc = encoder.encode(normalized)

        # mean pooling -> un vecteur par fonction
        embs.append(np.mean(enc, axis=0))
        names.append(func["name"])

    if not embs:
        return meta, None, []

    return meta, np.stack(embs), names


def build_index_entry(approach, meta, config_key, out_path, idx, fname):
    # on construit une entree d'index avec tous les champs necessaires
    # pour que benchmark.py puisse faire n'importe quel type de paire
    return {
        "source_id": meta["source_id"],
        "function": fname,
        "dataset": meta["dataset"],
        "problem": meta["problem"],
        "lang": meta["lang"],
        "embeddings": {
            approach: {
                config_key: {
                    "path": str(out_path),
                    "idx": idx
                }
            }
        }
    }


def run_approach(approach, encoder_fn, cfg, disasm_dir, emb_base):
    # boucle generique : parcourt les disasm, encode, sauve
    json_files = sorted(disasm_dir.rglob("*.json"))
    if not json_files:
        print(f"Aucun JSON dans {disasm_dir}")
        return False

    print(f"\n{len(json_files)} fichiers de disasm")

    index = {}
    nb_total = 0

    for jf in tqdm(json_files, desc=f"Embeddings {approach}"):
        try:
            meta, emb_matrix, func_names = encoder_fn(jf)
        except Exception as e:
            print(f"  erreur sur {jf.name}: {e}")
            continue

        if emb_matrix is None:
            continue

        # chemin de sortie : garde la meme hierarchie que disasm
        rel = jf.relative_to(disasm_dir)
        out_path = emb_base / approach / rel.with_suffix(".npy")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(out_path, emb_matrix)

        # config_key depuis le chemin : compiler/arch/optim
        parts = list(rel.parts)
        compiler, arch, optim = parts[0], parts[1], parts[2]
        config_key = f"{compiler}_{arch}_{optim}"

        nb_total += len(func_names)

        for idx, fname in enumerate(func_names):
            key = f"{meta['source_id']}::{fname}"
            if key not in index:
                index[key] = build_index_entry(
                    approach, meta, config_key, out_path, idx, fname
                )
            else:
                # on ajoute la config a l'entree existante
                if approach not in index[key]["embeddings"]:
                    index[key]["embeddings"][approach] = {}
                index[key]["embeddings"][approach][config_key] = {
                    "path": str(out_path),
                    "idx": idx
                }

    # on sauve l'index
    index_path = emb_base / "index.json"
    emb_base.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nTermine: {nb_total} fonctions encodees, index dans {index_path}")
    return True


def run_palmtree(cfg, disasm_dir, emb_base):
    model_path = PALMTREE_DIR / "pre-trained_model" / "palmtree" / "transformer.ep19"
    vocab_path = PALMTREE_DIR / "pre-trained_model" / "palmtree" / "vocab"

    if not model_path.exists():
        print(f"Modele PalmTree introuvable: {model_path}")
        return False

    encoder = PalmTreeEncoder(model_path, vocab_path)

    def encode_file(jf):
        return process_disasm_file(jf, encoder)

    return run_approach("palmtree", encode_file, cfg, disasm_dir, emb_base)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    cfg = load_config(args.config)
    paths = cfg["paths"]
    pipeline = cfg["pipeline"]

    disasm_dir = Path(paths["disasm"])
    emb_base = Path(paths["embeddings"])

    if not disasm_dir.exists():
        print(f"Erreur: {disasm_dir} n'existe pas, lance d'abord disasm.py")
        sys.exit(1)

    approaches = pipeline["similarity"]["approaches"]
    if not approaches.get("palmtree", {}).get("enabled"):
        print("PalmTree pas active dans config.yaml")
        sys.exit(0)

    ok = run_palmtree(cfg, disasm_dir, emb_base)
    if not ok:
        print("PalmTree a echoue")
        sys.exit(1)
