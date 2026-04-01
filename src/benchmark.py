# benchmark optimise : matmul GPU (ROCm/CUDA) + ranking vectorise
# supporte 100-1000 runs, fallback CPU numpy si pas de GPU
import sys
import json
import argparse
import pickle
import time
import numpy as np
from pathlib import Path
from collections import defaultdict
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_auc_score, roc_curve


# --- detection GPU ---

GPU = False
DEVICE = None
torch = None


def init_gpu():
    global GPU, DEVICE, torch
    try:
        import torch as _t
        torch = _t
        if torch.cuda.is_available():
            GPU = True
            DEVICE = torch.device("cuda")
            name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"  GPU: {name} ({vram:.1f} GB)")
        else:
            print("  GPU non disponible, fallback numpy CPU")
    except ImportError:
        print("  torch absent, fallback numpy CPU")


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def parse_config_key(key):
    last = key.rfind("_")
    optim = key[last + 1:]
    rest = key[:last]
    first = rest.find("_")
    return rest[:first], rest[first + 1:], optim


# --- chargement embeddings ---

def load_embeddings(emb_dir, approach):
    emb_dir = Path(emb_dir)
    mat_p = emb_dir / f"{approach}_matrix.npy"
    meta_p = emb_dir / f"{approach}_meta.pkl"

    if mat_p.exists() and meta_p.exists():
        # chargement consolide
        t0 = time.perf_counter()
        matrix = np.load(mat_p)
        with open(meta_p, "rb") as f:
            meta = pickle.load(f)
        dt = time.perf_counter() - t0
        print(f"  consolide: {matrix.shape[0]} vecteurs en {dt:.2f}s")
    else:
        # fallback index.json + .npy individuels
        print("  pas de fichier consolide, chargement index.json...")
        matrix, meta = _load_fallback(emb_dir, approach)
        print(f"  {matrix.shape[0]} vecteurs charges")

    # index inverse rapide : idx -> problem_id (int)
    prob_map = {}
    pid = 0
    problem_ids = np.empty(matrix.shape[0], dtype=np.int32)
    for i, fk in enumerate(meta["idx_to_func_key"]):
        prob = meta["func_meta"][fk]["problem"]
        if prob not in prob_map:
            prob_map[prob] = pid
            pid += 1
        problem_ids[i] = prob_map[prob]

    mat_gpu = None
    if GPU:
        mat_gpu = torch.from_numpy(matrix).to(DEVICE)
        print(f"  matrice sur GPU ({matrix.nbytes / 1e6:.0f} MB)")

    return matrix, meta, problem_ids, mat_gpu


def _load_fallback(emb_dir, approach):
    with open(emb_dir / "index.json") as f:
        index = json.load(f)

    npy_cache = {}
    vecs, key_to_idx = [], {}
    idx_to_fk, idx_to_ck = [], []
    func_meta = {}
    idx = 0

    for fk, entry in index.items():
        cfgs = entry.get("embeddings", {}).get(approach, {})
        if not cfgs:
            continue
        if fk not in func_meta:
            func_meta[fk] = {k: entry.get(k, "") for k in
                             ["source_id", "function", "dataset", "problem", "lang"]}
        for ck, info in cfgs.items():
            p = info["path"]
            if p not in npy_cache:
                npy_cache[p] = np.load(p)
            vecs.append(npy_cache[p][info["idx"]])
            key_to_idx[(fk, ck)] = idx
            idx_to_fk.append(fk)
            idx_to_ck.append(ck)
            idx += 1

    matrix = np.array(vecs, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix /= norms

    return matrix, {"key_to_idx": key_to_idx, "idx_to_func_key": idx_to_fk,
                    "idx_to_config_key": idx_to_ck, "func_meta": func_meta}


# --- reconstruit un index pour les pair builders ---

def rebuild_index(meta, approach):
    index = {}
    for (fk, ck), idx in meta["key_to_idx"].items():
        if fk not in index:
            fm = meta["func_meta"][fk]
            index[fk] = {**fm, "embeddings": {approach: {}}}
        index[fk]["embeddings"][approach][ck] = idx
    return index


# --- pair builders (inchanges) ---

def build_cross_compiler_pairs(index, approach):
    pairs = []
    for key, entry in index.items():
        configs = list(entry["embeddings"].get(approach, {}).keys())
        by_ao = defaultdict(list)
        for ck in configs:
            comp, arch, opt = parse_config_key(ck)
            by_ao[(arch, opt)].append(ck)
        for cks in by_ao.values():
            for i in range(len(cks)):
                for j in range(i + 1, len(cks)):
                    c1, _, _ = parse_config_key(cks[i])
                    c2, _, _ = parse_config_key(cks[j])
                    if c1 != c2:
                        pairs.append((key, cks[i], key, cks[j]))
    return pairs, 0


def build_cross_optim_pairs(index, approach):
    pairs = []
    skipped = 0
    by_func = defaultdict(dict)
    for key, entry in index.items():
        sid = entry.get("source_id", "")
        fname = entry.get("function", "")
        for ck in entry["embeddings"].get(approach, {}):
            comp, arch, opt = parse_config_key(ck)
            by_func[(sid, fname, comp, arch)][opt] = (key, ck)
    for (sid, fname, comp, arch), opt_map in by_func.items():
        opts = list(opt_map.keys())
        for i in range(len(opts)):
            for j in range(i + 1, len(opts)):
                k1, ck1 = opt_map[opts[i]]
                k2, ck2 = opt_map[opts[j]]
                pairs.append((k1, ck1, k2, ck2))
    return pairs, skipped


def build_cross_implementation_pairs(index, approach):
    by_pl = defaultdict(list)
    for key, entry in index.items():
        prob = entry.get("problem", "")
        lang = entry.get("lang", "")
        if prob and lang:
            by_pl[(prob, lang)].append(key)
    pairs = []
    for keys in by_pl.values():
        if len(keys) < 2:
            continue
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                if index[k1]["source_id"] == index[k2]["source_id"]:
                    continue
                c1 = set(index[k1]["embeddings"].get(approach, {}).keys())
                c2 = set(index[k2]["embeddings"].get(approach, {}).keys())
                for ck in c1 & c2:
                    pairs.append((k1, ck, k2, ck))
    return pairs, 0


def build_cross_language_pairs(index, approach):
    by_prob = defaultdict(list)
    for key, entry in index.items():
        prob = entry.get("problem", "")
        if prob:
            by_prob[prob].append(key)
    pairs = []
    for keys in by_prob.values():
        if len(keys) < 2:
            continue
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                k1, k2 = keys[i], keys[j]
                if index[k1]["lang"] == index[k2]["lang"]:
                    continue
                c1 = set(index[k1]["embeddings"].get(approach, {}).keys())
                c2 = set(index[k2]["embeddings"].get(approach, {}).keys())
                for ck in c1 & c2:
                    pairs.append((k1, ck, k2, ck))
    return pairs, 0


def build_cross_arch_pairs(index, approach):
    pairs = []
    for key, entry in index.items():
        configs = list(entry["embeddings"].get(approach, {}).keys())
        by_co = defaultdict(list)
        for ck in configs:
            comp, arch, opt = parse_config_key(ck)
            by_co[(comp, opt)].append(ck)
        for cks in by_co.values():
            for i in range(len(cks)):
                for j in range(i + 1, len(cks)):
                    if parse_config_key(cks[i])[1] != parse_config_key(cks[j])[1]:
                        pairs.append((key, cks[i], key, cks[j]))
    return pairs, 0


def build_cross_mixed_pairs(index, approach):
    pairs = []
    for key, entry in index.items():
        configs = list(entry["embeddings"].get(approach, {}).keys())
        for i in range(len(configs)):
            for j in range(i + 1, len(configs)):
                c1, a1, o1 = parse_config_key(configs[i])
                c2, a2, o2 = parse_config_key(configs[j])
                if (c1 != c2) + (a1 != a2) + (o1 != o2) >= 2:
                    pairs.append((key, configs[i], key, configs[j]))
    return pairs, 0


PAIR_BUILDERS = {
    "cross_compiler": build_cross_compiler_pairs,
    "cross_optim": build_cross_optim_pairs,
    "cross_arch": build_cross_arch_pairs,
    "cross_implementation": build_cross_implementation_pairs,
    "cross_language": build_cross_language_pairs,
    "cross_mixed": build_cross_mixed_pairs,
}


# --- conversion paires -> arrays d'indices ---

def pairs_to_arrays(pairs, key_to_idx):
    q, p = [], []
    for qk, qc, pk, pc in pairs:
        qi = key_to_idx.get((qk, qc))
        pi = key_to_idx.get((pk, pc))
        if qi is not None and pi is not None:
            q.append(qi)
            p.append(pi)
    return np.array(q, dtype=np.int64), np.array(p, dtype=np.int64)


# --- coeur vectorise ---

def run_experiment(matrix, mat_gpu, q_idxs, p_idxs, pool_sizes, seed, n_runs, max_queries):
    # au lieu de q @ M.T (n x 142K), on calcule :
    #   pos_sim = dot(q, p) directement (n dot products)
    #   d_sims  = q @ D.T (n x pool_size) avec D = distracteurs partages par run
    # meme protocole (pool-based retrieval), matmul 14x plus petite
    N = matrix.shape[0]
    n_pairs = len(q_idxs)

    if n_pairs == 0:
        empty = {"nb_queries": 0, "recall_at_1": {"mean": 0, "std": 0},
                 "mrr": {"mean": 0, "std": 0}, "roc_auc": None}
        return {f"pool_{ps}": empty for ps in pool_sizes}, [], []

    # pour les paires fixes (pas de reechantillonnage), on precalcule q_vecs et pos_sim
    fixed = n_pairs <= max_queries
    cached_q = cached_pos = None
    if fixed:
        if GPU and mat_gpu is not None:
            qi_t = torch.from_numpy(q_idxs).to(DEVICE)
            pi_t = torch.from_numpy(p_idxs).to(DEVICE)
            cached_q = mat_gpu[qi_t]
            cached_pos = (cached_q * mat_gpu[pi_t]).sum(dim=1)
        else:
            cached_q = matrix[q_idxs]
            cached_pos = (cached_q * matrix[p_idxs]).sum(axis=1)
        print(f"    pre-calcul: {n_pairs} paires fixes")

    pool_metrics = {ps: {"r1": [], "mrr": [], "auc": []} for ps in pool_sizes}
    last_pos, last_neg = [], []
    max_ps = max(pool_sizes)

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

        for ps in pool_sizes:
            nb_d = min(ps - 1, N - 2)
            if nb_d < 1:
                continue

            # pool partage : memes distracteurs pour toutes les queries d'un run
            # E[R@1] identique au per-query sampling, variance lissee par les 1000 runs
            d_idx = rng.choice(N, nb_d, replace=False)

            # petite matmul : (n, 128) x (128, nb_d) au lieu de (n, 128) x (128, 142K)
            if GPU and mat_gpu is not None:
                d_t = torch.from_numpy(d_idx).to(DEVICE)
                d_sims = torch.mm(q_vecs, mat_gpu[d_t].T)
                ranks = 1 + (d_sims >= pos_sim.unsqueeze(1)).sum(dim=1)
                ranks_np = ranks.cpu().numpy()
            else:
                d_sims = q_vecs @ matrix[d_idx].T
                ranks_np = 1 + np.sum(d_sims >= pos_sim[:, None], axis=1)

            pool_metrics[ps]["r1"].append(float(np.mean(ranks_np == 1)))
            pool_metrics[ps]["mrr"].append(float(np.mean(1.0 / ranks_np)))

            # AUC
            neg_sz = min(200, nb_d)
            if GPU and torch.is_tensor(d_sims):
                pos_np = pos_sim.cpu().numpy()
                neg_np = d_sims[:, :neg_sz].cpu().numpy().ravel()
            else:
                pos_np = np.asarray(pos_sim)
                neg_np = np.asarray(d_sims[:, :neg_sz]).ravel()
            try:
                labs = np.concatenate([np.ones(len(pos_np)), np.zeros(len(neg_np))])
                scores = np.concatenate([pos_np.ravel(), neg_np])
                pool_metrics[ps]["auc"].append(float(roc_auc_score(labs, scores)))
            except ValueError:
                pass

            if run == n_runs - 1 and ps == max_ps:
                last_pos = pos_np.ravel().tolist() if hasattr(pos_np, 'tolist') else list(pos_np)
                last_neg = neg_np.tolist()

    # formater les resultats
    results = {}
    for ps in pool_sizes:
        pk = f"pool_{ps}"
        m = pool_metrics[ps]
        res = {"nb_queries": n if n_pairs > 0 else 0}
        if m["r1"]:
            res["recall_at_1"] = {"mean": float(np.mean(m["r1"])), "std": float(np.std(m["r1"]))}
            res["mrr"] = {"mean": float(np.mean(m["mrr"])), "std": float(np.std(m["mrr"]))}
        else:
            res["recall_at_1"] = {"mean": 0, "std": 0}
            res["mrr"] = {"mean": 0, "std": 0}
        if m["auc"]:
            res["roc_auc"] = {"mean": float(np.mean(m["auc"])), "std": float(np.std(m["auc"]))}
        else:
            res["roc_auc"] = None
        results[pk] = res

    return results, last_pos, last_neg


# --- plots (quasi inchanges) ---

def plot_similarity_distribution(pos_sims, neg_sims, out_path):
    plt.figure(figsize=(10, 6))
    if pos_sims:
        plt.hist(pos_sims, bins=30, alpha=0.6, label="Positifs", color="green", density=True)
    if neg_sims:
        plt.hist(neg_sims, bins=30, alpha=0.6, label="Negatifs", color="red", density=True)
    plt.xlabel("Similarite cosinus")
    plt.ylabel("Densite")
    plt.title("Distribution des similarites")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  -> {out_path}")


def plot_roc_curves(roc_data, out_path):
    plt.figure(figsize=(8, 8))
    for label, (labs, scores) in roc_data.items():
        if not labs or len(set(labs)) < 2:
            continue
        fpr, tpr, _ = roc_curve(labs, scores)
        auc = roc_auc_score(labs, scores)
        plt.plot(fpr, tpr, label=f"{label} (AUC={auc:.3f})")
    plt.plot([0, 1], [0, 1], "k--", alpha=0.5)
    plt.xlabel("Taux de faux positifs")
    plt.ylabel("Taux de vrais positifs")
    plt.title("Courbes ROC par pair type")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  -> {out_path}")


def plot_recall_vs_poolsize(recall_data, pool_sizes, out_path):
    plt.figure(figsize=(10, 6))
    for pt, pools in recall_data.items():
        xs, ys, yerr = [], [], []
        for psz in pool_sizes:
            if psz in pools:
                xs.append(psz)
                ys.append(pools[psz]["mean"])
                yerr.append(pools[psz]["std"])
        if xs:
            plt.errorbar(xs, ys, yerr=yerr, fmt="o-", label=pt, capsize=4)
    plt.xscale("log")
    plt.xlabel("Taille du pool")
    plt.ylabel("Recall@1")
    plt.title("Recall@1 en fonction de la taille du pool")
    plt.legend()
    plt.ylim(0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  -> {out_path}")


def plot_cross_compiler_heatmap(matrix, meta, approach, out_path):
    # pre-build par fonction
    fk_configs = defaultdict(dict)
    for (fk, ck), idx in meta["key_to_idx"].items():
        fk_configs[fk][ck] = idx

    acc = defaultdict(list)
    compilers = set()
    optims = set()

    nb = 0
    for fk, configs in fk_configs.items():
        if len(configs) < 2:
            continue

        by_comp = defaultdict(list)
        for ck, idx in configs.items():
            comp, arch, opt = parse_config_key(ck)
            by_comp[comp].append((opt, idx))
            compilers.add(comp)
            optims.add(opt)

        comp_list = sorted(by_comp.keys())
        if len(comp_list) < 2:
            continue

        for o1, i1 in by_comp[comp_list[0]]:
            for o2, i2 in by_comp[comp_list[1]]:
                acc[(o1, o2)].append(float(np.dot(matrix[i1], matrix[i2])))

        nb += 1
        if nb >= 5000:
            break

    compilers = sorted(compilers)
    optims = sorted(optims)
    if len(compilers) < 2:
        return

    mat = np.full((len(optims), len(optims)), np.nan)
    for (o_r, o_c), vals in acc.items():
        mat[optims.index(o_r), optims.index(o_c)] = np.mean(vals)

    plt.figure(figsize=(8, 6))
    sns.heatmap(mat,
                xticklabels=[f"{compilers[1]}_{o}" for o in optims],
                yticklabels=[f"{compilers[0]}_{o}" for o in optims],
                annot=True, fmt=".3f", cmap="YlOrRd", vmin=0, vmax=1)
    plt.title(f"Similarite {compilers[0]} vs {compilers[1]}")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"  -> {out_path}")


def fmt_metric(m):
    if m is None:
        return "N/A"
    if isinstance(m, dict):
        return f"{m['mean']:.4f} +/- {m['std']:.4f}"
    return f"{m:.4f}"


def generate_report(approach, results, pool_sizes, seed, n_runs, stats, out_path):
    lines = []
    lines.append(f"# Rapport benchmark : {approach}\n")
    lines.append(f"Approche : **{approach}**")
    lines.append(f"Cadre : **optimiste** (noms DWARF)")
    lines.append(f"Seed : {seed}, n_runs : {n_runs}")
    lines.append(f"Max queries par pool : 5000\n")
    lines.append("## Statistiques\n")
    lines.append(f"Fonctions : {stats.get('total_functions', 0)}")
    inl = stats.get("pairs_skipped_inlining", {})
    if inl:
        for pt, n in inl.items():
            lines.append(f"Paires skippees ({pt}) : {n}")
    lines.append("")
    lines.append("## Resultats\n")
    for pt, pt_res in results.items():
        if pt_res.get("status") == "desactive":
            continue
        nb = pt_res.get("nb_pairs", 0)
        lines.append(f"### {pt} ({nb} paires)\n")
        if not pt_res.get("pools"):
            lines.append("Aucune donnee.\n")
            continue
        lines.append("| Pool | Recall@1 | MRR | ROC AUC |")
        lines.append("|------|----------|-----|---------|")
        for psz in pool_sizes:
            pk = f"pool_{psz}"
            m = pt_res["pools"].get(pk, {})
            if not m:
                lines.append(f"| {psz} | N/A | N/A | N/A |")
                continue
            lines.append(f"| {psz} | {fmt_metric(m.get('recall_at_1'))} | {fmt_metric(m.get('mrr'))} | {fmt_metric(m.get('roc_auc'))} |")
        lines.append("")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"  -> {out_path}")


# --- orchestration ---

def run_benchmark(approach, meta, cfg, results_dir, matrix, mat_gpu):
    print(f"\nBenchmark: {approach}")

    bench_cfg = cfg["pipeline"]["benchmark"]
    pair_types_cfg = bench_cfg["pair_types"]
    pool_sizes = bench_cfg.get("pool_sizes", [100])
    seed = bench_cfg.get("seed", 42)
    n_runs = bench_cfg.get("n_runs", 10)
    max_queries = bench_cfg.get("max_queries", 5000)

    # on reconstruit un index pour les pair builders
    index = rebuild_index(meta, approach)
    key_to_idx = meta["key_to_idx"]

    out_dir = results_dir / approach
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    all_pos, all_neg = [], []
    recall_data = {}
    roc_data = {}
    inl_stats = {}
    has_cc = False

    t_total = time.perf_counter()

    for pt_name, builder in PAIR_BUILDERS.items():
        if not pair_types_cfg.get(pt_name, False):
            results[pt_name] = {"status": "desactive"}
            continue

        t_pt = time.perf_counter()
        pairs, skipped = builder(index, approach)
        print(f"  {pt_name}: {len(pairs)} paires ({skipped} skippees)")

        if skipped:
            inl_stats[pt_name] = skipped
        if not pairs:
            results[pt_name] = {"nb_pairs": 0, "status": "aucune paire"}
            continue
        if pt_name == "cross_compiler":
            has_cc = True

        # conversion en arrays d'indices
        q_idxs, p_idxs = pairs_to_arrays(pairs, key_to_idx)
        print(f"    {len(q_idxs)} paires valides (sur {len(pairs)})")

        # experiment vectorise
        pool_results, pos_s, neg_s = run_experiment(
            matrix, mat_gpu, q_idxs, p_idxs,
            pool_sizes, seed, n_runs, max_queries
        )

        pt_res = {"nb_pairs": len(pairs), "pools": pool_results}
        recall_pts = {}

        for ps in pool_sizes:
            pk = f"pool_{ps}"
            m = pool_results.get(pk, {})
            r1 = m.get("recall_at_1", {})
            mrr = m.get("mrr", {})
            nq = m.get("nb_queries", 0)
            r1m = r1.get("mean", 0) if isinstance(r1, dict) else 0
            r1s = r1.get("std", 0) if isinstance(r1, dict) else 0
            mrrm = mrr.get("mean", 0) if isinstance(mrr, dict) else 0
            print(f"    pool {ps}: R@1={r1m:.4f}+/-{r1s:.4f} MRR={mrrm:.4f} ({nq}q)")
            recall_pts[ps] = r1 if isinstance(r1, dict) else {"mean": 0, "std": 0}

        results[pt_name] = pt_res
        recall_data[pt_name] = recall_pts
        all_pos.extend(pos_s)
        all_neg.extend(neg_s)

        if pos_s and neg_s:
            roc_data[pt_name] = ([1]*len(pos_s) + [0]*len(neg_s), list(pos_s) + list(neg_s))

        dt_pt = time.perf_counter() - t_pt
        print(f"    {pt_name} termine en {dt_pt:.1f}s")

    dt_total = time.perf_counter() - t_total
    print(f"\n  Total benchmark: {dt_total:.1f}s ({n_runs} runs x {len(pool_sizes)} pools)")

    # plots
    if all_pos or all_neg:
        plot_similarity_distribution(all_pos, all_neg, out_dir / "similarity_distribution.png")
    if roc_data:
        plot_roc_curves(roc_data, out_dir / "roc_curve.png")
    if recall_data:
        plot_recall_vs_poolsize(recall_data, pool_sizes, out_dir / "recall_vs_poolsize.png")
    if has_cc:
        plot_cross_compiler_heatmap(matrix, meta, approach, out_dir / "cross_compiler_heatmap.png")

    stats = {"total_functions": len(meta["func_meta"]), "pairs_skipped_inlining": inl_stats}
    output = {
        "approach": approach, "cadre": "optimiste", "seed": seed, "n_runs": n_runs,
        "pool_sizes": pool_sizes, "max_queries": max_queries,
        "results": results, "stats": stats,
    }
    with open(out_dir / "metrics.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"  -> {out_dir / 'metrics.json'}")
    generate_report(approach, results, pool_sizes, seed, n_runs, stats, out_dir / "rapport_benchmark.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--approach", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    paths = cfg["paths"]
    emb_dir = Path(paths["embeddings"])
    results_dir = Path(paths["results"])

    if not emb_dir.exists():
        print(f"Erreur: {emb_dir} n'existe pas")
        sys.exit(1)

    print("Initialisation...")
    init_gpu()

    approaches_found = set()
    # on detecte les approches depuis les fichiers consolides ET l'index
    for f in emb_dir.glob("*_matrix.npy"):
        approaches_found.add(f.stem.replace("_matrix", ""))
    idx_path = emb_dir / "index.json"
    if idx_path.exists():
        with open(idx_path) as f:
            index = json.load(f)
        for entry in index.values():
            for app in entry.get("embeddings", {}):
                approaches_found.add(app)

    print(f"Approches: {', '.join(sorted(approaches_found))}")

    if args.approach:
        if args.approach not in approaches_found:
            print(f"Erreur: approche '{args.approach}' pas trouvee")
            sys.exit(1)
        to_run = [args.approach]
    else:
        to_run = sorted(approaches_found)

    for approach in to_run:
        matrix, meta, problem_ids, mat_gpu = load_embeddings(emb_dir, approach)
        run_benchmark(approach, meta, cfg, results_dir, matrix, mat_gpu)

    print("\nBenchmark termine")
