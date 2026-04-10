import sys
import re
import json
import random
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

import yaml
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

# imports PalmTree (meme setup que embed_palmtree.py)
ROOT = Path(__file__).resolve().parent.parent
PALMTREE_DIR = ROOT / "lib" / "palmtree"
if not PALMTREE_DIR.exists():
    ROOT = Path(__file__).resolve().parent
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

# le pickle attend bert_pytorch, on cree les alias
for _mn in list(sys.modules.keys()):
    if _mn.startswith("palmtree"):
        sys.modules[_mn.replace("palmtree", "bert_pytorch", 1)] = sys.modules[_mn]

sys.path.insert(0, str(PALMTREE_DIR / "pre-trained_model"))
import config as palmtree_config
import vocab as palmtree_vocab


# === Modele : PalmTree + tete de projection ===

class PalmTreeFT(nn.Module):

    def __init__(self, bert, proj_dim=128):
        super().__init__()
        self.bert = bert
        h = bert.hidden
        self.proj = nn.Sequential(
            nn.Linear(h, h),
            nn.ReLU(),
            nn.Linear(h, proj_dim)
        )

    def forward(self, tokens, segments, bounds):
        # passe toutes les instructions du batch dans BERT
        enc = self.bert(tokens, segments)   # (nb_instr, seq_len, hidden)
        inst_embs = enc.mean(dim=1)         # (nb_instr, hidden)

        # mean pooling par fonction selon les bornes
        func_embs = []
        for start, end in bounds:
            func_embs.append(inst_embs[start:end].mean(dim=0))

        func_embs = torch.stack(func_embs)
        return F.normalize(self.proj(func_embs), dim=1)


# === InfoNCE (NT-Xent) loss ===

def info_nce_loss(embs_a, embs_b, temperature=0.07):
    n = embs_a.shape[0]
    embs = torch.cat([embs_a, embs_b], dim=0)
    sim = embs @ embs.t() / temperature

    # masquer la diag
    mask = ~torch.eye(2 * n, dtype=torch.bool, device=sim.device)
    sim = sim.masked_fill(~mask, float('-inf'))

    # le positif de embs_a[i] c'est embs_b[i] et vice versa
    labels = torch.cat([torch.arange(n, 2 * n), torch.arange(n)]).to(sim.device)
    return F.cross_entropy(sim, labels)


# === Normalisation et tokenisation (meme logique que embed_palmtree.py) ===

def normalize_insn(mnemonic, op_str):
    if not op_str or not op_str.strip():
        return mnemonic
    clean = op_str.replace(",", "")
    tokens = re.findall(r'[\w.]+|[+\-\*\[\]]', clean)
    out = []
    for tok in tokens:
        if re.match(r'^0x[0-9a-fA-F]+$', tok):
            if int(tok, 16) > 0xFFFF:
                out.append("address")
                continue
        out.append(tok)
    return mnemonic + " " + " ".join(out)


def tokenize_insn(text, vocab, seq_len=20):
    toks = text.split(" ")
    seg = (len(toks) + 2) * [1]
    seq = vocab.to_seq(text)
    seq = [3] + seq + [2]
    seg = (seg[:seq_len] + [0] * seq_len)[:seq_len]
    seq = (seq[:seq_len] + [0] * seq_len)[:seq_len]
    return seq, seg


# === Chargement et preparation des donnees ===

def load_functions(disasm_dir, vocab, max_insns=200, min_insns=5):
    # groupe les fonctions par (source_id, func_name)
    # chaque "concept" = meme code source, meme fonction, compilations differentes
    concepts = defaultdict(list)
    concept_prob = {}

    disasm_dir = Path(disasm_dir)
    json_files = sorted(disasm_dir.rglob("*.json"))
    print(f"{len(json_files)} fichiers de disasm")

    for jf in tqdm(json_files, desc="Chargement"):
        try:
            with open(jf) as f:
                data = json.load(f)
        except Exception:
            continue

        src_id = data.get("source_id", "")
        problem = data.get("problem", "")
        if not src_id or not problem:
            continue

        # config_key depuis le chemin : compiler_arch_optim
        rel = jf.relative_to(disasm_dir)
        parts = list(rel.parts)
        if len(parts) < 3:
            continue
        config_key = f"{parts[0]}_{parts[1]}_{parts[2]}"

        for func in data.get("functions", []):
            name = func.get("name", "")
            insns = func.get("instructions", [])
            if not name or len(insns) < min_insns:
                continue

            insns = insns[:max_insns]
            toks, segs = [], []
            for m, o in insns:
                t, s = tokenize_insn(normalize_insn(m, o), vocab)
                toks.append(t)
                segs.append(s)

            key = (src_id, name)
            concepts[key].append({
                "config": config_key,
                "tokens": toks,
                "segments": segs
            })
            concept_prob[key] = problem

    # garder que les concepts avec >= 2 vues (sinon pas de paire)
    before = len(concepts)
    concepts = {k: v for k, v in concepts.items() if len(v) >= 2}
    concept_prob = {k: v for k, v in concept_prob.items() if k in concepts}

    nb_views = sum(len(v) for v in concepts.values())
    print(f"{len(concepts)} concepts (sur {before}), {nb_views} vues")
    return concepts, concept_prob


def split_by_problem(concepts, concept_prob, seed=42):
    problems = sorted(set(concept_prob.values()))
    rng = random.Random(seed)
    rng.shuffle(problems)

    n = len(problems)
    n_train = int(n * 0.7)
    n_val = int(n * 0.15)

    train_p = set(problems[:n_train])
    val_p = set(problems[n_train:n_train + n_val])
    test_p = set(problems[n_train + n_val:])

    train = {k: v for k, v in concepts.items() if concept_prob[k] in train_p}
    val = {k: v for k, v in concepts.items() if concept_prob[k] in val_p}
    test = {k: v for k, v in concepts.items() if concept_prob[k] in test_p}

    print(f"Split: {len(train_p)} / {len(val_p)} / {len(test_p)} problemes (train/val/test)")
    print(f"  {len(train)} / {len(val)} / {len(test)} concepts")
    return train, val, test, {
        "train": sorted(train_p),
        "val": sorted(val_p),
        "test": sorted(test_p)
    }


# === Dataset de paires contrastives ===

class PairDataset(Dataset):

    def __init__(self, concepts):
        self.items = list(concepts.values())

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        views = self.items[idx]
        v1, v2 = random.sample(views, 2)
        return (v1["tokens"], v1["segments"]), (v2["tokens"], v2["segments"])


def collate_pairs(batch):
    # concatene les instructions, garde les bornes par fonction
    tok_a, seg_a, bounds_a = [], [], []
    tok_b, seg_b, bounds_b = [], [], []
    off_a = off_b = 0

    for (ta, sa), (tb, sb) in batch:
        na, nb = len(ta), len(tb)
        tok_a.extend(ta); seg_a.extend(sa)
        bounds_a.append((off_a, off_a + na)); off_a += na
        tok_b.extend(tb); seg_b.extend(sb)
        bounds_b.append((off_b, off_b + nb)); off_b += nb

    return {
        'tok_a': torch.LongTensor(tok_a), 'seg_a': torch.LongTensor(seg_a),
        'bounds_a': bounds_a,
        'tok_b': torch.LongTensor(tok_b), 'seg_b': torch.LongTensor(seg_b),
        'bounds_b': bounds_b,
    }


# === Boucles train/eval ===

def train_epoch(model, loader, optim, device, temp):
    model.train()
    total_loss, nb = 0, 0

    for batch in tqdm(loader, desc="  train"):
        ea = model(batch['tok_a'].to(device), batch['seg_a'].to(device), batch['bounds_a'])
        eb = model(batch['tok_b'].to(device), batch['seg_b'].to(device), batch['bounds_b'])

        loss = info_nce_loss(ea, eb, temp)
        optim.zero_grad()
        loss.backward()
        optim.step()

        total_loss += loss.item()
        nb += 1

    return total_loss / max(nb, 1)


@torch.no_grad()
def eval_epoch(model, loader, device, temp):
    model.eval()
    total_loss, nb = 0, 0

    for batch in tqdm(loader, desc="  val  "):
        ea = model(batch['tok_a'].to(device), batch['seg_a'].to(device), batch['bounds_a'])
        eb = model(batch['tok_b'].to(device), batch['seg_b'].to(device), batch['bounds_b'])

        loss = info_nce_loss(ea, eb, temp)
        total_loss += loss.item()
        nb += 1

    return total_loss / max(nb, 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--temperature", type=float, default=0.07)
    parser.add_argument("--max-insns", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default="data/finetune")
    args = parser.parse_args()

    # device
    if args.device == "cuda" or (args.device == "auto" and torch.cuda.is_available()):
        device = torch.device("cuda")
        palmtree_config.USE_CUDA = True
        print("GPU detecte, CUDA")
    else:
        device = torch.device("cpu")
        palmtree_config.USE_CUDA = False
        print("CPU")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed(args.seed)

    with open(args.config) as f:
        cfg = yaml.safe_load(f)

    disasm_dir = Path(cfg["paths"]["disasm"])
    if not disasm_dir.exists():
        print(f"Erreur: {disasm_dir} n'existe pas")
        sys.exit(1)

    # charger vocab et modele pre-entraine
    model_path = PALMTREE_DIR / "pre-trained_model" / "palmtree" / "transformer.ep19"
    vocab_path = PALMTREE_DIR / "pre-trained_model" / "palmtree" / "vocab"

    print(f"Vocab: {vocab_path}")
    vocab = palmtree_vocab.WordVocab.load_vocab(str(vocab_path))
    print(f"  {len(vocab)} tokens")

    print(f"Modele pre-entraine: {model_path}")
    bert = torch.load(str(model_path), weights_only=False, map_location=device)
    model = PalmTreeFT(bert).to(device)
    print(f"  {sum(p.numel() for p in model.parameters()):,} parametres")

    # charger et preparer les donnees
    concepts, concept_prob = load_functions(
        disasm_dir, vocab, max_insns=args.max_insns
    )
    if not concepts:
        print("Aucun concept trouve, verifie data/disasm/")
        sys.exit(1)

    train_data, val_data, test_data, split_info = split_by_problem(
        concepts, concept_prob, seed=args.seed
    )
    del test_data, concepts, concept_prob

    train_loader = DataLoader(
        PairDataset(train_data), batch_size=args.batch_size,
        shuffle=True, collate_fn=collate_pairs, num_workers=0
    )
    val_loader = DataLoader(
        PairDataset(val_data), batch_size=args.batch_size,
        collate_fn=collate_pairs, num_workers=0
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    # entrainement
    best_val = float('inf')
    patience = 3
    no_improve = 0

    print(f"\nFine-tuning: {args.epochs} epochs, bs={args.batch_size}, lr={args.lr}, temp={args.temperature}")
    print(f"  train: {len(train_data)} concepts, val: {len(val_data)} concepts\n")

    for epoch in range(args.epochs):
        print(f"Epoch {epoch + 1}/{args.epochs}")
        t_loss = train_epoch(model, train_loader, optimizer, device, args.temperature)
        v_loss = eval_epoch(model, val_loader, device, args.temperature)

        print(f"  train_loss={t_loss:.4f}  val_loss={v_loss:.4f}")

        if v_loss < best_val:
            best_val = v_loss
            no_improve = 0
            # sauve juste le BERT (compatible avec embed_palmtree.py)
            torch.save(model.bert.cpu(), str(out_dir / "palmtree_ft.pt"))
            model.bert.to(device)
            print(f"  -> best model (val={v_loss:.4f})")
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"  early stopping ({patience} epochs sans amelioration)")
                break

    # sauver le split et les hyperparametres
    with open(out_dir / "split.json", "w") as f:
        json.dump(split_info, f, indent=2)

    with open(out_dir / "finetune_config.json", "w") as f:
        json.dump({
            "epochs_run": epoch + 1,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "temperature": args.temperature,
            "max_insns": args.max_insns,
            "seed": args.seed,
            "best_val_loss": best_val,
        }, f, indent=2)

    print(f"\nTermine!")
    print(f"Modele:  {out_dir}/palmtree_ft.pt")
    print(f"Split:   {out_dir}/split.json")
    print(f"Config:  {out_dir}/finetune_config.json")
    print(f"\nPour embeddings: python src/embed_palmtree.py --model-path {out_dir}/palmtree_ft.pt --approach palmtree_ft")
