#!/usr/bin/env python3
# benchmark refuse : pool partage par run, matmul GPU (ROCm/CUDA) + ranking vectorise

from __future__ import annotations

import argparse
import json
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

torch = None
GPU = False
DEVICE = None


def init_gpu(device_arg):
    global torch, GPU, DEVICE
    try:
        import torch as _t
        torch = _t
    except ImportError:
        print("  torch absent, fallback numpy CPU")
        return

    if device_arg == "cpu":
        print("  device force CPU")
        return

    if torch.cuda.is_available():
        GPU = True
        DEVICE = torch.device("cuda")
        name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"  GPU: {name} ({vram:.1f} GB)")
    else:
        print("  GPU non disponible, fallback numpy CPU")


# --- chargement ---

def load_embeddings(emb_path, ids_path):
    mat = np.load(str(emb_path)).astype(np.float32)
    ids = np.load(str(ids_path)).astype(np.int64)

    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    mat /= norms

    print(f"  {mat.shape[0]} vecteurs, dim={mat.shape[1]}")
    return mat, ids


def load_metadata(db_path):
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute("""
        SELECT f.id, f.function_name, b.compiler, b.architecture, b.optimization,
               i.id, i.implementation_folder, i.source_language, p.platform, p.problem_name
        FROM functions f
        JOIN binaries b ON b.id = f.binary_id
        JOIN implementations i ON i.id = b.implementation_id
        JOIN problems p ON p.id = i.problem_id
        ORDER BY f.id
    """).fetchall()
    conn.close()

    records = []
    for row in rows:
        records.append({
            'function_id': int(row[0]),
            'function_name': row[1],
            'compiler': row[2],
            'architecture': row[3],
            'optimization': row[4],
            'implementation_id': int(row[5]),
            'implementation_folder': row[6],
            'source_language': row[7] or 'unknown',
            'platform': row[8],
            'problem_name': row[9],
        })
    return records


# --- pair builders ---

def _pairs_from_group(indexes):
    out = []
    for i in range(len(indexes)):
        for j in range(i + 1, len(indexes)):
            out.append((indexes[i], indexes[j]))
    return out


def build_cross_compiler_pairs(records, max_pairs=0):
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        key = (r["platform"], r["problem_name"], r["implementation_id"],
               r["function_name"], r["architecture"], r["optimization"])
        groups[key].append(idx)

    pairs = []
    for idxs in groups.values():
        for i, j in _pairs_from_group(idxs):
            if records[i]["compiler"] != records[j]["compiler"]:
                pairs.append((i, j))
                if 0 < max_pairs <= len(pairs):
                    return pairs
    return pairs


def build_cross_optim_pairs(records, max_pairs=0):
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        key = (r["platform"], r["problem_name"], r["implementation_id"],
               r["function_name"], r["architecture"], r["compiler"])
        groups[key].append(idx)

    pairs = []
    for idxs in groups.values():
        for i, j in _pairs_from_group(idxs):
            if records[i]["optimization"] != records[j]["optimization"]:
                pairs.append((i, j))
                if 0 < max_pairs <= len(pairs):
                    return pairs
    return pairs


def build_cross_implementation_pairs(records, max_pairs=0):
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        key = (r["platform"], r["problem_name"], r["source_language"],
               r["function_name"], r["compiler"], r["architecture"], r["optimization"])
        groups[key].append(idx)

    pairs = []
    for idxs in groups.values():
        for i, j in _pairs_from_group(idxs):
            if records[i]["implementation_id"] != records[j]["implementation_id"]:
                pairs.append((i, j))
                if 0 < max_pairs <= len(pairs):
                    return pairs
    return pairs


def build_cross_language_pairs(records, max_pairs=0):
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        key = (r["platform"], r["problem_name"], r["function_name"],
               r["compiler"], r["architecture"], r["optimization"])
        groups[key].append(idx)

    pairs = []
    for idxs in groups.values():
        for i, j in _pairs_from_group(idxs):
            if records[i]["source_language"] != records[j]["source_language"]:
                pairs.append((i, j))
                if 0 < max_pairs <= len(pairs):
                    return pairs
    return pairs


PAIR_BUILDERS = {
    "cross_compiler": build_cross_compiler_pairs,
    "cross_optim": build_cross_optim_pairs,
    "cross_implementation": build_cross_implementation_pairs,
    "cross_language": build_cross_language_pairs,
}


# --- coeur vectorise : pool partage par run ---

def run_experiment(matrix, mat_gpu, q_idxs, p_idxs, pool_size, seed, n_runs, max_queries):
    # pool partage : un seul set de distracteurs par run
    # matmul : (n_queries, dim) x (dim, pool_size) au lieu de per-query sampling
    N = matrix.shape[0]
    n_pairs = len(q_idxs)

    if n_pairs == 0:
        return {"nb_queries": 0, "recall_at_1": {"mean": 0, "std": 0},
                "mrr": {"mean": 0, "std": 0}}

    nb_d = min(pool_size - 1, N - 2)
    if nb_d < 1:
        return {"nb_queries": 0, "recall_at_1": {"mean": 0, "std": 0},
                "mrr": {"mean": 0, "std": 0}}

    # si moins de paires que max_queries, on les precalcule une seule fois
    fixed = n_pairs <= max_queries

    if fixed and GPU and mat_gpu is not None:
        qi_t = torch.from_numpy(q_idxs).to(DEVICE)
        pi_t = torch.from_numpy(p_idxs).to(DEVICE)
        cached_q = mat_gpu[qi_t]
        cached_pos = (cached_q * mat_gpu[pi_t]).sum(dim=1)
    elif fixed:
        cached_q = matrix[q_idxs]
        cached_pos = (cached_q * matrix[p_idxs]).sum(axis=1)
    else:
        cached_q = cached_pos = None

    all_r1 = []
    all_mrr = []

    for run in range(n_runs):
        rng = np.random.RandomState(seed + run)

        if fixed:
            q_vecs = cached_q
            pos_sim = cached_pos
            n = n_pairs
        else:
            sel = rng.choice(n_pairs, max_queries, replace=False)
            q, p = q_idxs[sel], p_idxs[sel]
            n = len(q)
            if GPU and mat_gpu is not None:
                q_t = torch.from_numpy(q).to(DEVICE)
                p_t = torch.from_numpy(p).to(DEVICE)
                q_vecs = mat_gpu[q_t]
                pos_sim = (q_vecs * mat_gpu[p_t]).sum(dim=1)
            else:
                q_vecs = matrix[q]
                pos_sim = (q_vecs * matrix[p]).sum(axis=1)

        # pool partage : memes distracteurs pour toutes les queries du run
        d_idx = rng.choice(N, nb_d, replace=False)

        # matmul : (n, dim) x (dim, nb_d) -> (n, nb_d)
        if GPU and mat_gpu is not None:
            d_t = torch.from_numpy(d_idx).to(DEVICE)
            d_sims = torch.mm(q_vecs, mat_gpu[d_t].T)
            ranks = 1 + (d_sims >= pos_sim.unsqueeze(1)).sum(dim=1)
            ranks_np = ranks.cpu().numpy()
        else:
            d_sims = q_vecs @ matrix[d_idx].T
            ranks_np = 1 + np.sum(d_sims >= pos_sim[:, None], axis=1)

        all_r1.append(float(np.mean(ranks_np == 1)))
        all_mrr.append(float(np.mean(1.0 / ranks_np)))

    return {
        "nb_queries": n_pairs if fixed else max_queries,
        "recall_at_1": {"mean": float(np.mean(all_r1)), "std": float(np.std(all_r1))},
        "mrr": {"mean": float(np.mean(all_mrr)), "std": float(np.std(all_mrr))},
    }


# --- rapport ---

def fmt_metric(m):
    if m is None:
        return "N/A"
    if isinstance(m, dict):
        return f"{m['mean']:.4f} +/- {m['std']:.4f}"
    return f"{m:.4f}"


def write_report(out_path, results, pool_sizes, n_runs, seed, total_functions):
    lines = []
    lines.append("# Rapport benchmark : REFuSe")
    lines.append("")
    lines.append("Approche : **REFuSe**")
    lines.append(f"Seed : {seed}, n_runs : {n_runs}")
    lines.append(f"Fonctions : {total_functions}")
    lines.append("")
    lines.append("## Resultats")
    lines.append("")

    for pt, pt_res in results.items():
        lines.append(f"### {pt} ({pt_res.get('nb_pairs', 0)} paires)")
        lines.append("")
        lines.append("| Pool | Recall@1 | MRR |")
        lines.append("|------|----------|-----|")
        for psz in pool_sizes:
            pk = f"pool_{psz}"
            m = pt_res.get("pools", {}).get(pk)
            if m is None:
                lines.append(f"| {psz} | N/A | N/A |")
            else:
                lines.append(f"| {psz} | {fmt_metric(m.get('recall_at_1'))} | {fmt_metric(m.get('mrr'))} |")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


# --- orchestration ---

def run_benchmark(db_path, emb_path, ids_path, out_dir, pool_sizes,
                  n_runs, seed, max_queries, device, pair_types, max_pairs_per_type):
    init_gpu(device)

    print("Chargement embeddings...")
    matrix, emb_ids = load_embeddings(emb_path, ids_path)

    print("Chargement metadata...")
    records = load_metadata(db_path)
    print(f"  {len(records)} records")

    if len(records) != matrix.shape[0]:
        raise RuntimeError(f"Mismatch: {len(records)} records mais {matrix.shape[0]} embeddings")

    # GPU : transferer la matrice une seule fois
    mat_gpu = None
    if GPU and torch is not None:
        mat_gpu = torch.from_numpy(matrix).to(DEVICE)
        print(f"  matrice sur GPU ({matrix.nbytes / 1e6:.0f} MB)")

    results = {}
    t_total = time.perf_counter()

    for pt_name in pair_types:
        builder = PAIR_BUILDERS[pt_name]
        t0 = time.perf_counter()

        pairs = builder(records, max_pairs=max_pairs_per_type)
        print(f"\n  {pt_name}: {len(pairs)} paires")

        if not pairs:
            results[pt_name] = {"nb_pairs": 0, "pools": {}}
            continue

        q_idxs = np.array([p[0] for p in pairs], dtype=np.int64)
        p_idxs = np.array([p[1] for p in pairs], dtype=np.int64)

        pt_res = {"nb_pairs": len(pairs), "pools": {}}

        for ps in pool_sizes:
            metrics = run_experiment(matrix, mat_gpu, q_idxs, p_idxs,
                                    ps, seed, n_runs, max_queries)
            pt_res["pools"][f"pool_{ps}"] = metrics
            r1 = metrics["recall_at_1"]
            mrr = metrics["mrr"]
            nq = metrics["nb_queries"]
            print(f"    pool {ps}: R@1={r1['mean']:.4f}+/-{r1['std']:.4f} MRR={mrr['mean']:.4f} ({nq}q)")

        results[pt_name] = pt_res
        dt = time.perf_counter() - t0
        print(f"    {pt_name} en {dt:.1f}s")

    dt_total = time.perf_counter() - t_total
    print(f"\n  Total: {dt_total:.1f}s")

    # sauvegarde
    out_dir.mkdir(parents=True, exist_ok=True)
    output = {
        "approach": "refuse",
        "pool_sizes": pool_sizes,
        "seed": seed,
        "n_runs": n_runs,
        "max_queries": max_queries,
        "results": results,
        "stats": {"total_functions": len(records)},
    }
    (out_dir / "metrics.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    write_report(out_dir / "rapport_benchmark.md", results, pool_sizes, n_runs, seed, len(records))
    print(f"  -> {out_dir / 'metrics.json'}")
    print(f"  -> {out_dir / 'rapport_benchmark.md'}")


def main():
    parser = argparse.ArgumentParser(description="Benchmark REFuSe vectorise")
    parser.add_argument("--db-path", default="refuse_benchmark.db")
    parser.add_argument("--embeddings-npy", default="results/refuse_embeddings.npy")
    parser.add_argument("--embeddings-ids-npy", default="results/refuse_embeddings.ids.npy")
    parser.add_argument("--out-dir", default="results/refuse")
    parser.add_argument("--pool-sizes", nargs="+", type=int, default=[100, 1000, 10000])
    parser.add_argument("--n-runs", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-queries", type=int, default=5000)
    parser.add_argument("--max-pairs-per-type", type=int, default=250000)
    parser.add_argument("--device", default="", help="cuda, cpu, ou vide pour auto")
    parser.add_argument("--pair-types", nargs="+",
                        choices=list(PAIR_BUILDERS.keys()),
                        default=list(PAIR_BUILDERS.keys()))
    args = parser.parse_args()

    run_benchmark(
        db_path=Path(args.db_path),
        emb_path=Path(args.embeddings_npy),
        ids_path=Path(args.embeddings_ids_npy),
        out_dir=Path(args.out_dir),
        pool_sizes=args.pool_sizes,
        n_runs=args.n_runs,
        seed=args.seed,
        max_queries=args.max_queries,
        device=args.device,
        pair_types=args.pair_types,
        max_pairs_per_type=args.max_pairs_per_type,
    )


if __name__ == "__main__":
    main()
