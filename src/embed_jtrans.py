# embeddings jTrans pour le benchmark BSCD
# lit les JSON de data/disasm_jtrans/ (format blocs BB avec adresses)
# normalise capstone -> tokens jTrans (reproduit gen_funcstr + parse_asm du papier)
# tokenization MANUELLE identique a data.py du repo jTrans (PAS de BertTokenizer)
# output : vecteur 768-dim (pooler_output, L2-norme)

import sys
import re
import json
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict
from tqdm import tqdm

import yaml
import torch

ROOT = Path(__file__).resolve().parent.parent
JTRANS_DIR = ROOT / "lib" / "jtrans"
if not JTRANS_DIR.exists():
    ROOT = Path(__file__).resolve().parent
    JTRANS_DIR = ROOT / "lib" / "jtrans"

MAXLEN = 512

# detection GPU
if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
else:
    DEVICE = torch.device("cpu")
    print("CPU mode (pas de GPU detecte)")


# --- vocabulaire jTrans (identique a data.py du papier) ---
# vocab.txt : 2898 lignes (JUMP_ADDR_0..511, [UNK], puis tokens asm)
# on ajoute [SEP], [PAD], [CLS], [MASK] a la fin comme dans le papier
# => [SEP]=2898, [PAD]=2899, [CLS]=2900, [MASK]=2901
# les tokens inconnus mappent vers 512 ([UNK])

def load_vocab():
    vocab_path = JTRANS_DIR / "jtrans_tokenizer" / "vocab.txt"
    if not vocab_path.exists():
        print(f"Erreur: vocab jTrans introuvable: {vocab_path}")
        sys.exit(1)
    data = open(vocab_path).read().strip().split("\n") + ["[SEP]", "[PAD]", "[CLS]", "[MASK]"]
    return defaultdict(lambda: 512, {data[i]: i for i in range(len(data))})


# --- mapping capstone -> IDA pour les mnemoniques ---
# le modele jTrans a ete entraine sur du desassemblage IDA Pro
# IDA utilise des noms differents de capstone pour certaines instructions
# sans ce mapping, ret/je/jne etc. tombent dans [UNK] et le modele perd l'info

MNEM_MAP = {
    "ret": "retn",
    "je": "jz",
    "jne": "jnz",
    "sete": "setz",
    "setne": "setnz",
    "cmove": "cmovz",
    "cmovne": "cmovnz",
    "jae": "jnb",
    "cmovae": "cmovnb",
    "setae": "setnb",
    "seta": "setnbe",
    "setg": "setnle",
    "setge": "setnl",
    "movabs": "mov",
}

# registres reconnus par jTrans (meme liste que readidadata.py)
REGISTERS = {
    "rax", "rbx", "rcx", "rdx", "esi", "edi", "rbp", "rsp",
    "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15",
}

SEGMENTS = ("cs:", "ss:", "fs:", "ds:", "es:", "gs:")

RE_HEX = re.compile(r"^0x[0-9a-fA-F]+$")
RE_DEC = re.compile(r"^\d+$")
RE_NEG = re.compile(r"^-\d+$")

RE_SIZE_PREFIX = re.compile(
    r"\b(byte|word|dword|qword|xmmword|ymmword|zmmword|tbyte|oword)\s+(ptr\s+)?",
    re.IGNORECASE,
)


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def help_tokenize(func_str, vocab):
    # tokenization identique a data.py du papier jTrans
    # PAS de WordPiece, PAS de BertTokenizer, split par espaces
    tokens = func_str.strip().split(" ")
    n = len(tokens)
    if n <= 509:
        tokens = ["[CLS]"] + tokens + ["[SEP]"]
        attn = [1] * len(tokens) + [0] * (512 - len(tokens))
        tokens = tokens + ["[PAD]"] * (512 - len(tokens))
    else:
        tokens = ["[CLS]"] + tokens[:510] + ["[SEP]"]
        attn = [1] * 512
    ids = [vocab[t] for t in tokens]
    return ids, attn


def is_register(x):
    return x in REGISTERS


def normalize_mem_addr(addr_str):
    # "[rbp + 0x8]" -> "[rbp+CONST]"
    # reproduit readidadata.py lignes 89-104
    inner = addr_str[1:-1]
    inner = inner.replace("-", "+")
    inner = re.sub(r"\s*\+\s*", "+", inner)
    parts = inner.split("+")

    normalized = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if is_register(p):
            normalized.append(p)
        elif RE_HEX.match(p):
            normalized.append("CONST")
        elif RE_DEC.match(p):
            normalized.append("CONST")
        elif p.startswith("var_"):
            normalized.append("var_xxx")
        elif p.startswith("arg_"):
            normalized.append("arg_xxx")
        elif "*" in p:
            normalized.append(p)
        elif not is_register(p):
            normalized.append("CONST_VAR")

    return "[" + "+".join(normalized) + "]"


def parse_capstone_operand(mnem, location, operand):
    # normalisation d'un operande capstone -> format jTrans
    # adapte pour capstone (0x au lieu de h, pas de var_/loc_/sub_)
    op = operand.strip()
    if not op:
        return None

    op = RE_SIZE_PREFIX.sub("", op).strip()
    op = op.replace("offset ", "")
    op = op.replace("short ", "")
    op = op.replace(" - ", "+")

    for seg in SEGMENTS:
        if op.startswith(seg):
            return seg + "xxx"

    # sauts : jXX -> hex_XXXXXX (sera resolu en JUMP_ADDR_N apres)
    if mnem[0] == "j" and not is_register(op):
        m = RE_HEX.match(op)
        if m:
            return "hex_" + op[2:]
        return "UNK_ADDR"

    # call -> callfunc_xxx
    if mnem == "call" and location == 1:
        if len(op) > 3:
            return "callfunc_xxx"

    # lea operande 2 : si pas hex et pas [addr] -> GLOBAL_VAR
    if mnem == "lea" and location == 2:
        if not RE_HEX.match(op) and not (op.startswith("[") and op.endswith("]")):
            if not is_register(op):
                return "GLOBAL_VAR"

    # adresse memoire [...]
    if op.startswith("[") and op.endswith("]"):
        return normalize_mem_addr(op)

    if RE_HEX.match(op):
        return "CONST"

    if RE_NEG.match(op):
        return "CONST"

    if RE_DEC.match(op):
        return "CONST"

    if not is_register(op) and len(op) > 4:
        return "CONST"

    return op


def normalize_for_jtrans(blocks):
    # reproduit gen_funcstr du papier (data.py lignes 37-72)
    # blocks : liste de {"addr": "0x...", "instructions": [[addr, mnem, op_str], ...]}
    # retourne : string de tokens separes par espaces

    blocs = sorted(blocks, key=lambda b: int(b["addr"], 16))

    code_lst = []
    map_id = {}  # addr_int -> position du 1er token du bloc

    for blk in blocs:
        addr_int = int(blk["addr"], 16)
        map_id[addr_int] = len(code_lst)

        for insn in blk["instructions"]:
            _, mnem, op_str = insn

            mnem = MNEM_MAP.get(mnem, mnem)
            code_lst.append(mnem)

            if op_str and op_str.strip():
                operands = op_str.split(",")
                for i, operand in enumerate(operands):
                    tok = parse_capstone_operand(mnem, i + 1, operand.strip())
                    if tok is not None:
                        code_lst.append(tok)

    # post-traitement : resoudre les hex_XXXXX -> JUMP_ADDR_N
    # reproduit gen_funcstr lignes 57-70 (y compris le bug original)
    for c in range(len(code_lst)):
        op = code_lst[c]
        if op.startswith("hex_"):
            try:
                jump_addr = int(op[4:], 16)
            except ValueError:
                code_lst[c] = "UNK_JUMP_ADDR"
                continue

            if map_id.get(jump_addr):
                # le .get retourne 0 (falsy) pour le 1er bloc -> jamais JUMP_ADDR_0
                # le modele a ete entraine avec ce bug, on le replique
                jump_id = map_id[jump_addr]
                if jump_id < MAXLEN:
                    code_lst[c] = f"JUMP_ADDR_{jump_id}"
                else:
                    code_lst[c] = "JUMP_ADDR_EXCEEDED"
            else:
                code_lst[c] = "UNK_JUMP_ADDR"

    return " ".join(code_lst)


class JTransEncoder:

    def __init__(self, model_dir, device=None):
        self.device = device or DEVICE

        print(f"Chargement du modele jTrans: {model_dir}")
        from transformers import BertModel

        # BinBertModel : position_embeddings = word_embeddings (specifique jTrans)
        class BinBertModel(BertModel):
            def __init__(self, config, add_pooling_layer=True):
                super().__init__(config, add_pooling_layer=add_pooling_layer)
                self.embeddings.position_embeddings = self.embeddings.word_embeddings

        self.model = BinBertModel.from_pretrained(str(model_dir))
        self.model.to(self.device)
        self.model.half()  # fp16 pour perf
        self.model.eval()
        self.batch_size = 128
        print("  jTrans pret (fp16)")

    def encode_batch(self, func_strs, vocab):
        if not func_strs:
            return []

        results = []
        for i in range(0, len(func_strs), self.batch_size):
            batch = func_strs[i:i + self.batch_size]

            all_ids = []
            all_masks = []
            for s in batch:
                ids, mask = help_tokenize(s, vocab)
                all_ids.append(ids)
                all_masks.append(mask)

            input_ids = torch.tensor(all_ids, dtype=torch.long).to(self.device)
            attn_mask = torch.tensor(all_masks, dtype=torch.long).to(self.device)

            with torch.no_grad(), torch.autocast("cuda", enabled=False):
                out = self.model(input_ids=input_ids, attention_mask=attn_mask)
                embs = out.pooler_output.float()
                norms = embs.norm(dim=1, keepdim=True).clamp(min=1e-8)
                embs = embs / norms

            results.extend(embs.cpu().numpy())
        return results


def build_index_entry(approach, meta, config_key, out_path, idx, fname):
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


def run_jtrans(cfg, disasm_dir, emb_base, max_files=None):
    approach = "jtrans"
    model_dir = JTRANS_DIR / "models" / "jTrans-finetune"

    if not model_dir.exists():
        print(f"Modele jTrans introuvable: {model_dir}")
        print("  telecharge-le depuis https://github.com/vul337/jTrans")
        return False

    vocab = load_vocab()
    encoder = JTransEncoder(model_dir)

    json_files = sorted(Path(disasm_dir).rglob("*.json"))
    if not json_files:
        print(f"Aucun JSON dans {disasm_dir}")
        return False

    # reprise auto : skip les fichiers deja traites
    todo = []
    for jf in json_files:
        rel = jf.relative_to(disasm_dir)
        out_path = emb_base / approach / rel.with_suffix(".npy")
        if not out_path.exists():
            todo.append(jf)

    skipped = len(json_files) - len(todo)
    if skipped > 0:
        print(f"\n{skipped} fichiers deja traites, {len(todo)} restants")
    else:
        print(f"\n{len(json_files)} fichiers de disasm")

    if max_files:
        todo = todo[:max_files]
        print(f"  mode test: limite a {max_files} fichiers")

    if not todo:
        print("Rien a faire, tout est deja encode")
        return True

    # index existant (on merge dedans)
    index_path = emb_base / "index.json"
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
    else:
        index = {}

    nb_total = 0
    FLUSH = encoder.batch_size

    # buffer cross-fichiers pour maximiser le throughput GPU
    buf_strs = []
    buf_records = []  # (json_path, meta, names, start_idx, count)

    def flush():
        nonlocal nb_total
        if not buf_strs:
            return
        embs = encoder.encode_batch(buf_strs, vocab)
        for jf2, meta2, names2, start, cnt in buf_records:
            file_embs = np.stack(embs[start:start + cnt])

            rel = jf2.relative_to(disasm_dir)
            out_path = emb_base / approach / rel.with_suffix(".npy")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            np.save(out_path, file_embs)

            parts = list(rel.parts)
            config_key = f"{parts[0]}_{parts[1]}_{parts[2]}"

            nb_total += cnt
            for i, fname in enumerate(names2):
                key = f"{meta2['source_id']}::{fname}"
                if key not in index:
                    index[key] = build_index_entry(
                        approach, meta2, config_key, out_path, i, fname
                    )
                else:
                    if approach not in index[key]["embeddings"]:
                        index[key]["embeddings"][approach] = {}
                    index[key]["embeddings"][approach][config_key] = {
                        "path": str(out_path), "idx": i
                    }
        buf_strs.clear()
        buf_records.clear()

    for jf in tqdm(todo, desc=f"Embeddings {approach}"):
        try:
            with open(jf) as f:
                data = json.load(f)
        except Exception as e:
            print(f"  erreur lecture {jf.name}: {e}")
            continue

        meta = {
            "source_id": data.get("source_id", ""),
            "dataset": data.get("dataset", ""),
            "problem": data.get("problem", ""),
            "lang": data.get("lang", ""),
        }

        func_strs, names = [], []
        for func in data.get("functions", []):
            blocks = func.get("blocks", [])
            if not blocks:
                continue
            s = normalize_for_jtrans(blocks)
            if s:
                func_strs.append(s)
                names.append(func["name"])

        if not func_strs:
            continue

        start = len(buf_strs)
        buf_strs.extend(func_strs)
        buf_records.append((jf, meta, names, start, len(func_strs)))

        if len(buf_strs) >= FLUSH:
            flush()

    flush()

    # sauvegarde index
    emb_base.mkdir(parents=True, exist_ok=True)
    with open(index_path, "w") as f:
        json.dump(index, f, indent=2)

    print(f"\nTermine: {nb_total} fonctions encodees, index dans {index_path}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--test", action="store_true",
                        help="mode test, limite a 50 fichiers")
    args = parser.parse_args()

    cfg = load_config(args.config)
    paths = cfg["paths"]
    pipeline = cfg["pipeline"]

    disasm_dir = Path(paths["disasm_jtrans"])
    emb_base = Path(paths["embeddings"])

    if not disasm_dir.exists():
        print(f"Erreur: {disasm_dir} n'existe pas, lance d'abord disasm_jtrans.py")
        sys.exit(1)

    approaches = pipeline["similarity"]["approaches"]
    if not approaches.get("jtrans", {}).get("enabled"):
        print("jTrans pas active dans config.yaml")
        sys.exit(0)

    max_files = 50 if args.test else None
    ok = run_jtrans(cfg, disasm_dir, emb_base, max_files)
    if not ok:
        print("jTrans a echoue")
        sys.exit(1)
