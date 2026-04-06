#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Sequence, Tuple


np = None
torch = None
roc_auc_score = None


def _ensure_deps() -> None:
    global np, torch, roc_auc_score
    if np is not None and torch is not None and roc_auc_score is not None:
        return
    try:
        import numpy as _np
        import torch as _torch
        from sklearn.metrics import roc_auc_score as _roc_auc_score
    except ImportError as e:
        raise RuntimeError(
            "benchmark_refuse_vectorized.py requires numpy, torch, and scikit-learn. Install requirements.txt first."
        ) from e
    np = _np
    torch = _torch
    roc_auc_score = _roc_auc_score


def load_vectorized_embeddings(embeddings_npy: Path, embeddings_ids_npy: Path) -> Tuple[np.ndarray, np.ndarray]:
    """Load embeddings from .npy files and normalize them."""
    _ensure_deps()
    embeddings_matrix = np.load(str(embeddings_npy)).astype(np.float32)
    embedding_ids = np.load(str(embeddings_ids_npy)).astype(np.int64)
    
    # Normalize embeddings
    norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
    norms[norms == 0.0] = 1.0
    embeddings_matrix = embeddings_matrix / norms
    
    return embeddings_matrix, embedding_ids


def load_metadata(db_path: Path) -> List[dict]:
    """Load metadata from database (for pair construction)."""
    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        """
        SELECT f.id, f.function_name, b.compiler, b.architecture, b.optimization,
               i.id, i.implementation_folder, i.source_language, p.platform, p.problem_name
        FROM functions f
        JOIN binaries b ON b.id = f.binary_id
        JOIN implementations i ON i.id = b.implementation_id
        JOIN problems p ON p.id = i.problem_id
        ORDER BY f.id
        """
    ).fetchall()
    conn.close()
    
    records = []
    for row in rows:
        (
            fn_id,
            function_name,
            compiler,
            architecture,
            optimization,
            impl_id,
            impl_folder,
            source_language,
            platform,
            problem_name,
        ) = row
        records.append({
            'function_id': int(fn_id),
            'function_name': function_name,
            'compiler': compiler,
            'architecture': architecture,
            'optimization': optimization,
            'implementation_id': int(impl_id),
            'implementation_folder': impl_folder,
            'source_language': source_language or 'unknown',
            'platform': platform,
            'problem_name': problem_name,
        })
    return records


def _pairs_from_group(indexes: Sequence[int]) -> List[Tuple[int, int]]:
    out = []
    for i in range(len(indexes)):
        for j in range(i + 1, len(indexes)):
            out.append((indexes[i], indexes[j]))
    return out


def build_cross_compiler_pairs(records: List[dict], max_pairs: int = 0) -> List[Tuple[int, int]]:
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        key = (
            r["platform"],
            r["problem_name"],
            r["implementation_id"],
            r["function_name"],
            r["architecture"],
            r["optimization"],
        )
        groups[key].append(idx)

    pairs = []
    for idxs in groups.values():
        for i, j in _pairs_from_group(idxs):
            if records[i]["compiler"] != records[j]["compiler"]:
                pairs.append((i, j))
                if max_pairs > 0 and len(pairs) >= max_pairs:
                    return pairs
    return pairs


def build_cross_optim_pairs(records: List[dict], max_pairs: int = 0) -> List[Tuple[int, int]]:
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        key = (
            r["platform"],
            r["problem_name"],
            r["implementation_id"],
            r["function_name"],
            r["architecture"],
            r["compiler"],
        )
        groups[key].append(idx)

    pairs = []
    for idxs in groups.values():
        for i, j in _pairs_from_group(idxs):
            if records[i]["optimization"] != records[j]["optimization"]:
                pairs.append((i, j))
                if max_pairs > 0 and len(pairs) >= max_pairs:
                    return pairs
    return pairs


def build_cross_implementation_pairs(records: List[dict], max_pairs: int = 0) -> List[Tuple[int, int]]:
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        key = (
            r["platform"],
            r["problem_name"],
            r["source_language"],
            r["function_name"],
            r["compiler"],
            r["architecture"],
            r["optimization"],
        )
        groups[key].append(idx)

    pairs = []
    for idxs in groups.values():
        for i, j in _pairs_from_group(idxs):
            if records[i]["implementation_id"] != records[j]["implementation_id"]:
                pairs.append((i, j))
                if max_pairs > 0 and len(pairs) >= max_pairs:
                    return pairs
    return pairs


def build_cross_language_pairs(records: List[dict], max_pairs: int = 0) -> List[Tuple[int, int]]:
    groups = defaultdict(list)
    for idx, r in enumerate(records):
        key = (
            r["platform"],
            r["problem_name"],
            r["function_name"],
            r["compiler"],
            r["architecture"],
            r["optimization"],
        )
        groups[key].append(idx)

    pairs = []
    for idxs in groups.values():
        for i, j in _pairs_from_group(idxs):
            if records[i]["source_language"] != records[j]["source_language"]:
                pairs.append((i, j))
                if max_pairs > 0 and len(pairs) >= max_pairs:
                    return pairs
    return pairs


PAIR_BUILDERS = {
    "cross_compiler": build_cross_compiler_pairs,
    "cross_optim": build_cross_optim_pairs,
    "cross_implementation": build_cross_implementation_pairs,
    "cross_language": build_cross_language_pairs,
}


def _sample_distractors(
    rng: np.random.RandomState,
    records: List[dict],
    query_idx: int,
    positive_idx: int,
    pool_size: int,
) -> np.ndarray:
    """Sample distractor indices for a query-positive pair."""
    _ensure_deps()
    need = pool_size - 1
    if need <= 0:
        return np.array([], dtype=np.int64)

    q_problem = (records[query_idx]["platform"], records[query_idx]["problem_name"])
    candidates = [
        i
        for i in range(len(records))
        if i != query_idx
        and i != positive_idx
        and (records[i]["platform"], records[i]["problem_name"]) != q_problem
    ]
    if not candidates:
        return np.array([], dtype=np.int64)

    if len(candidates) >= need:
        picked = rng.choice(candidates, size=need, replace=False)
    else:
        picked = rng.choice(candidates, size=need, replace=True)
    return np.array(picked, dtype=np.int64)


def _build_problem_codes(records: List[dict]) -> np.ndarray:
    _ensure_deps()
    codebook = {}
    codes = np.empty(len(records), dtype=np.int32)
    next_code = 0
    for idx, rec in enumerate(records):
        key = (rec["platform"], rec["problem_name"])
        code = codebook.get(key)
        if code is None:
            code = next_code
            codebook[key] = code
            next_code += 1
        codes[idx] = code
    return codes


def _sample_distractors_fast(
    rng: np.random.RandomState,
    total_records: int,
    problem_codes: np.ndarray,
    query_idx: int,
    positive_idx: int,
    pool_size: int,
) -> np.ndarray:
    need = pool_size - 1
    if need <= 0:
        return np.empty((0,), dtype=np.int64)

    q_code = problem_codes[query_idx]
    out = np.empty((need,), dtype=np.int64)
    filled = 0

    while filled < need:
        remaining = need - filled
        draw = max(remaining * 2, 64)
        candidates = rng.randint(0, total_records, size=draw, dtype=np.int64)
        valid = (
            (candidates != query_idx)
            & (candidates != positive_idx)
            & (problem_codes[candidates] != q_code)
        )
        picked = candidates[valid]
        if picked.size == 0:
            continue
        take = min(remaining, picked.size)
        out[filled : filled + take] = picked[:take]
        filled += take

    return out


def run_pool_vectorized(
    embeddings_matrix: np.ndarray,
    records: List[dict],
    pairs: List[Tuple[int, int]],
    pool_size: int,
    seed: int,
    n_runs: int,
    max_queries: int,
    device: str,
) -> Dict:
    """Run vectorized similarity computation using numpy and optionally PyTorch for GPU."""
    _ensure_deps()
    all_r1 = []
    all_mrr = []
    all_auc = []
    
    # Check if we should use GPU
    use_gpu = device.startswith("cuda") or (device == "" and torch.cuda.is_available())
    dev = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))
    
    if use_gpu:
        embeddings_tensor = torch.from_numpy(embeddings_matrix).to(dev)

    total_records = len(records)
    problem_codes = _build_problem_codes(records)

    if pool_size <= 100:
        chunk_size = 1024
    elif pool_size <= 1000:
        chunk_size = 256
    else:
        chunk_size = 64
    
    for run in range(n_runs):
        rng = np.random.RandomState(seed + run)
        
        # Sample pairs for this run
        if len(pairs) > max_queries:
            sample_ids = rng.choice(len(pairs), size=max_queries, replace=False)
            sampled = [pairs[int(i)] for i in sample_ids]
        else:
            sampled = pairs
        
        if not sampled:
            continue
        
        # Extract query and positive indices, sample distractors
        q_idx = []
        p_idx = []
        distract_idx = []
        for i, j in sampled:
            d = _sample_distractors_fast(
                rng=rng,
                total_records=total_records,
                problem_codes=problem_codes,
                query_idx=i,
                positive_idx=j,
                pool_size=pool_size,
            )
            q_idx.append(i)
            p_idx.append(j)
            distract_idx.append(d)
        
        if not q_idx:
            continue
        
        q_idx_np = np.array(q_idx, dtype=np.int64)
        p_idx_np = np.array(p_idx, dtype=np.int64)
        
        if use_gpu:
            q_t = embeddings_tensor[torch.from_numpy(q_idx_np).to(dev)]
            p_t = embeddings_tensor[torch.from_numpy(p_idx_np).to(dev)]
            pos_scores = torch.sum(q_t * p_t, dim=1)
            ranks = torch.ones((q_t.shape[0],), dtype=torch.int32, device=dev)

            for start in range(0, q_t.shape[0], chunk_size):
                end = min(start + chunk_size, q_t.shape[0])
                d_chunk_np = np.stack(distract_idx[start:end], axis=0)
                d_chunk_t = embeddings_tensor[torch.from_numpy(d_chunk_np).to(dev)]
                q_chunk = q_t[start:end]
                pos_chunk = pos_scores[start:end]
                neg_scores = torch.einsum("nkd,nd->nk", d_chunk_t, q_chunk)
                ranks[start:end] += torch.sum(neg_scores >= pos_chunk.unsqueeze(1), dim=1).to(torch.int32)

            ranks_np = ranks.detach().cpu().numpy()
            pos_scores_np = pos_scores.detach().cpu().numpy()
        else:
            q_vecs = embeddings_matrix[q_idx_np]
            p_vecs = embeddings_matrix[p_idx_np]
            pos_scores_np = np.sum(q_vecs * p_vecs, axis=1)
            ranks_np = np.ones((q_vecs.shape[0],), dtype=np.int32)

            for start in range(0, q_vecs.shape[0], chunk_size):
                end = min(start + chunk_size, q_vecs.shape[0])
                d_chunk = np.stack(distract_idx[start:end], axis=0)
                d_vecs = embeddings_matrix[d_chunk]
                q_chunk = q_vecs[start:end]
                pos_chunk = pos_scores_np[start:end]
                neg_scores = np.einsum("nkd,nd->nk", d_vecs, q_chunk)
                ranks_np[start:end] += np.sum(neg_scores >= pos_chunk[:, None], axis=1)
        
        # Compute metrics
        r1 = np.mean(ranks_np == 1)
        mrr = np.mean(1.0 / ranks_np)
        all_r1.append(float(r1))
        all_mrr.append(float(mrr))
        
        all_auc = all_auc
    
    return {
        "recall_at_1": {
            "mean": float(np.mean(all_r1)) if all_r1 else 0.0,
            "std": float(np.std(all_r1)) if all_r1 else 0.0,
        },
        "mrr": {
            "mean": float(np.mean(all_mrr)) if all_mrr else 0.0,
            "std": float(np.std(all_mrr)) if all_mrr else 0.0,
        },
        "roc_auc": (
            {
                "mean": float(np.mean(all_auc)),
                "std": float(np.std(all_auc)),
            }
            if all_auc
            else None
        ),
    }


def fmt_metric(m):
    if m is None:
        return "N/A"
    if isinstance(m, dict):
        return f"{m['mean']:.4f} +/- {m['std']:.4f}"
    return f"{m:.4f}"


def write_report(
    out_path: Path,
    results: Dict,
    pool_sizes: List[int],
    n_runs: int,
    seed: int,
    total_functions: int,
):
    lines = []
    lines.append("# Rapport benchmark : refuse (vectorized)")
    lines.append("")
    lines.append("Approche : **REFuSe (Vectorized)**")
    lines.append(f"Seed : {seed}, n_runs : {n_runs}")
    lines.append(f"Fonctions : {total_functions}")
    lines.append("")
    lines.append("## Resultats")
    lines.append("")

    for pt, pt_res in results.items():
        lines.append(f"### {pt} ({pt_res.get('nb_pairs', 0)} paires)")
        lines.append("")
        lines.append("| Pool | Recall@1 | MRR | ROC AUC |")
        lines.append("|------|----------|-----|---------|")
        for psz in pool_sizes:
            pk = f"pool_{psz}"
            m = pt_res.get("pools", {}).get(pk)
            if m is None:
                lines.append(f"| {psz} | N/A | N/A | N/A |")
            else:
                lines.append(
                    f"| {psz} | {fmt_metric(m.get('recall_at_1'))} | {fmt_metric(m.get('mrr'))} | {fmt_metric(m.get('roc_auc'))} |"
                )
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def run_benchmark(
    db_path: Path,
    embeddings_npy: Path,
    embeddings_ids_npy: Path,
    out_dir: Path,
    pool_sizes: List[int],
    n_runs: int,
    seed: int,
    max_queries: int,
    device: str,
    pair_types: List[str],
    max_pairs_per_type: int,
) -> None:
    """Run vectorized benchmark using pre-computed embeddings."""
    _ensure_deps()
    
    print("[benchmark_refuse_vectorized] loading embeddings from .npy files...")
    embeddings_matrix, embedding_ids = load_vectorized_embeddings(embeddings_npy, embeddings_ids_npy)
    print(f"[benchmark_refuse_vectorized] loaded vectors: {embeddings_matrix.shape[0]}, dim={embeddings_matrix.shape[1]}")
    
    print("[benchmark_refuse_vectorized] loading metadata from database...")
    records = load_metadata(db_path)
    print(f"[benchmark_refuse_vectorized] loaded records: {len(records)}")
    
    if embeddings_matrix.shape[0] == 0:
        raise RuntimeError("No embeddings found. Run embed_refuse_db.py --export-npy first.")
    
    if len(records) != embeddings_matrix.shape[0]:
        raise RuntimeError(
            f"Mismatch: {len(records)} records but {embeddings_matrix.shape[0]} embeddings"
        )
    
    results = {}
    
    for pair_type in pair_types:
        builder = PAIR_BUILDERS[pair_type]
        pairs = builder(records, max_pairs=max_pairs_per_type)
        print(f"[benchmark_refuse_vectorized] {pair_type}: pairs={len(pairs)}")
        
        pt_res = {"nb_pairs": len(pairs), "pools": {}}
        for pool_size in pool_sizes:
            print(f"  Running pool_size={pool_size}...")
            metrics = run_pool_vectorized(
                embeddings_matrix=embeddings_matrix,
                records=records,
                pairs=pairs,
                pool_size=pool_size,
                seed=seed,
                n_runs=n_runs,
                max_queries=max_queries,
                device=device,
            )
            pt_res["pools"][f"pool_{pool_size}"] = metrics
            print(
                f"  pool={pool_size} R@1={metrics['recall_at_1']['mean']:.4f} "
                f"MRR={metrics['mrr']['mean']:.4f}"
            )
        
        results[pair_type] = pt_res
    
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
    write_report(
        out_path=out_dir / "rapport_benchmark.md",
        results=results,
        pool_sizes=pool_sizes,
        n_runs=n_runs,
        seed=seed,
        total_functions=len(records),
    )
    print(f"[benchmark_refuse_vectorized] wrote: {out_dir / 'metrics.json'}")
    print(f"[benchmark_refuse_vectorized] wrote: {out_dir / 'rapport_benchmark.md'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Vectorized benchmark for REFuSe embeddings")
    parser.add_argument("--db-path", default="refuse_benchmark.db", help="Path to SQLite DB")
    parser.add_argument("--embeddings-npy", default="results/refuse_embeddings.npy", help="Path to embeddings .npy file")
    parser.add_argument("--embeddings-ids-npy", default="results/refuse_embeddings.ids.npy", help="Path to embeddings IDs .npy file")
    parser.add_argument("--out-dir", default="results/refuse", help="Output directory for results")
    parser.add_argument("--pool-sizes", nargs="+", type=int, default=[100, 1000, 10000])
    parser.add_argument("--n-runs", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-queries", type=int, default=5000)
    parser.add_argument(
        "--max-pairs-per-type",
        type=int,
        default=250000,
        help="Cap generated positive pairs per pair type (0 = no cap)",
    )
    parser.add_argument("--device", default="", help="cuda, cpu, or empty for auto")
    parser.add_argument(
        "--pair-types",
        nargs="+",
        choices=list(PAIR_BUILDERS.keys()),
        default=list(PAIR_BUILDERS.keys()),
        help="Subset of pair types to benchmark",
    )
    args = parser.parse_args()

    _ensure_deps()

    run_benchmark(
        db_path=Path(args.db_path),
        embeddings_npy=Path(args.embeddings_npy),
        embeddings_ids_npy=Path(args.embeddings_ids_npy),
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
