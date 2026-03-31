# benchmark rapide : precharge tout en RAM, calculs vectorises
import sys
import json
import argparse
import numpy as np
from pathlib import Path
from collections import defaultdict
import yaml
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import roc_auc_score, roc_curve


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def load_index(emb_dir):
    with open(Path(emb_dir) / "index.json") as f:
        return json.load(f)


def parse_config_key(key):
    last = key.rfind("_")
    optim = key[last + 1:]
    rest = key[:last]
    first = rest.find("_")
    return rest[:first], rest[first + 1:], optim


# on precharge TOUS les embeddings en un gros array numpy
# chaque embedding est identifie par un (func_key, config_key) -> idx dans la matrice
def preload_embeddings(index, approach):
    print("  chargement des embeddings en RAM...", end=" ", flush=True)
    emb_list = []
    key_to_idx = {}
    idx = 0

    # on charge chaque .npy une seule fois
    npy_cache = {}
    for func_key, entry in index.items():
        for ck, info in entry.get("embeddings", {}).get(approach, {}).items():
            path = info["path"]
            if path not in npy_cache:
                npy_cache[path] = np.load(path)
            vec = npy_cache[path][info["idx"]]
            emb_list.append(vec)
            key_to_idx[(func_key, ck)] = idx
            idx += 1

    matrix = np.array(emb_list, dtype=np.float32)
    # on normalise pour que le cosine sim = dot product
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1
    matrix = matrix / norms
    print(f"{len(emb_list)} vecteurs charges")
    return matrix, key_to_idx


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


def run_pool_experiment_fast(matrix, key_to_idx, index, approach, pairs, pool_sz, rng, max_queries=5000):
    # on sample les paires si y'en a trop
    if len(pairs) > max_queries:
        sample_idx = rng.choice(len(pairs), size=max_queries, replace=False)
        sampled = [pairs[i] for i in sample_idx]
    else:
        sampled = pairs

    # on precalcule les indices et les problemes pour les distracteurs
    all_indices = list(range(matrix.shape[0]))

    # index inverse : idx -> problem
    idx_to_prob = {}
    for func_key, entry in index.items():
        prob = entry.get("problem", "")
        for ck in entry.get("embeddings", {}).get(approach, {}):
            if (func_key, ck) in key_to_idx:
                idx_to_prob[key_to_idx[(func_key, ck)]] = prob

    ranks = []
    pos_sims = []
    neg_sims_all = []

    for q_key, q_ck, p_key, p_ck in sampled:
        q_idx = key_to_idx.get((q_key, q_ck))
        p_idx = key_to_idx.get((p_key, p_ck))
        if q_idx is None or p_idx is None:
            continue

        q_prob = idx_to_prob.get(q_idx, "")

        # distracteurs : problems differents, rapide avec numpy
        nb_distract = min(pool_sz - 1, len(all_indices) - 2)
        if nb_distract < 1:
            continue

        # on sample des indices au hasard et on filtre
        candidates = rng.choice(len(all_indices), size=min(nb_distract * 3, len(all_indices)), replace=False)
        distract_idxs = []
        for ci in candidates:
            if ci == q_idx or ci == p_idx:
                continue
            if idx_to_prob.get(ci, "") == q_prob and q_prob:
                continue
            distract_idxs.append(ci)
            if len(distract_idxs) >= nb_distract:
                break

        # fallback si pas assez
        if len(distract_idxs) < nb_distract:
            for ci in candidates:
                if ci == q_idx or ci == p_idx:
                    continue
                if ci not in distract_idxs:
                    distract_idxs.append(ci)
                    if len(distract_idxs) >= nb_distract:
                        break

        if not distract_idxs:
            continue

        # similarite cosinus vectorisee (matrice normalisee, dot = cosine sim)
        q_vec = matrix[q_idx]
        p_sim = float(np.dot(q_vec, matrix[p_idx]))
        d_sims = np.dot(matrix[np.array(distract_idxs)], q_vec)

        rank = 1 + int(np.sum(d_sims >= p_sim))
        ranks.append(rank)
        pos_sims.append(p_sim)
        rng.shuffle(d_sims)
        neg_sims_all.extend(d_sims[:200].tolist())

    return ranks, pos_sims, neg_sims_all


def run_multi_pool_fast(matrix, key_to_idx, index, approach, pairs, pool_sz, seed, n_runs, max_queries=5000):
    all_r1 = []
    all_mrr = []
    all_auc = []
    last_pos = []
    last_neg = []

    for run in range(n_runs):
        rng = np.random.RandomState(seed + run)
        ranks, pos_s, neg_s = run_pool_experiment_fast(
            matrix, key_to_idx, index, approach, pairs, pool_sz, rng, max_queries
        )
        if not ranks:
            continue
        r = np.array(ranks)
        all_r1.append(float(np.mean(r == 1)))
        all_mrr.append(float(np.mean(1.0 / r)))
        if pos_s and neg_s:
            labels = [1] * len(pos_s) + [0] * len(neg_s)
            scores = list(pos_s) + list(neg_s)
            try:
                all_auc.append(float(roc_auc_score(labels, scores)))
            except ValueError:
                pass
        last_pos = pos_s
        last_neg = neg_s

    last_nb = len(ranks) if ranks else 0
    res = {"nb_queries": last_nb}
    if all_r1:
        res["recall_at_1"] = {"mean": float(np.mean(all_r1)), "std": float(np.std(all_r1))}
        res["mrr"] = {"mean": float(np.mean(all_mrr)), "std": float(np.std(all_mrr))}
    else:
        res["recall_at_1"] = {"mean": 0.0, "std": 0.0}
        res["mrr"] = {"mean": 0.0, "std": 0.0}
    if all_auc:
        res["roc_auc"] = {"mean": float(np.mean(all_auc)), "std": float(np.std(all_auc))}
    else:
        res["roc_auc"] = None
    return res, last_pos, last_neg


# ======= plots =======

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


def plot_cross_compiler_heatmap(matrix, key_to_idx, index, approach, pairs, out_path):
    # on calcule la similarite pour TOUTES les combinaisons (comp1_Ox vs comp2_Oy)
    # pas seulement les paires du benchmark (qui sont meme-optim uniquement)
    acc = defaultdict(list)
    compilers = set()
    optims = set()

    # on regroupe les configs par fonction pour comparer toutes les combinaisons
    nb_sampled = 0
    for func_key, entry in index.items():
        configs = entry.get("embeddings", {}).get(approach, {})
        if len(configs) < 2:
            continue

        # grouper par compilateur
        by_comp = defaultdict(list)
        for ck in configs:
            comp, arch, opt = parse_config_key(ck)
            by_comp[comp].append((ck, opt))
            compilers.add(comp)
            optims.add(opt)

        comp_list = sorted(by_comp.keys())
        if len(comp_list) < 2:
            continue

        # toutes les paires (comp1_Ox, comp2_Oy)
        for ck1, o1 in by_comp[comp_list[0]]:
            for ck2, o2 in by_comp[comp_list[1]]:
                qi = key_to_idx.get((func_key, ck1))
                pi = key_to_idx.get((func_key, ck2))
                if qi is None or pi is None:
                    continue
                sim = float(np.dot(matrix[qi], matrix[pi]))
                acc[(o1, o2)].append(sim)

        nb_sampled += 1
        if nb_sampled >= 5000:
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


def run_benchmark(approach, index, cfg, results_dir, matrix, key_to_idx):
    print(f"\nBenchmark: {approach}")
    bench_cfg = cfg["pipeline"]["benchmark"]
    pair_types_cfg = bench_cfg["pair_types"]
    pool_sizes = bench_cfg.get("pool_sizes", [100])
    seed = bench_cfg.get("seed", 42)
    n_runs = bench_cfg.get("n_runs", 10)
    max_queries = bench_cfg.get("max_queries", 5000)

    out_dir = results_dir / approach
    out_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    all_pos = []
    all_neg = []
    recall_data = {}
    roc_data = {}
    cc_pairs = []
    inl_stats = {}

    for pt_name, builder in PAIR_BUILDERS.items():
        if not pair_types_cfg.get(pt_name, False):
            results[pt_name] = {"status": "desactive"}
            continue

        pairs, skipped = builder(index, approach)
        print(f"  {pt_name}: {len(pairs)} paires ({skipped} skippees)")
        if skipped:
            inl_stats[pt_name] = skipped
        if not pairs:
            results[pt_name] = {"nb_pairs": 0, "status": "aucune paire"}
            continue
        if pt_name == "cross_compiler":
            cc_pairs = pairs

        pt_res = {"nb_pairs": len(pairs), "pools": {}}
        recall_pts = {}

        for pool_sz in pool_sizes:
            metrics, pos_s, neg_s = run_multi_pool_fast(
                matrix, key_to_idx, index, approach, pairs,
                pool_sz, seed, n_runs, max_queries
            )
            pk = f"pool_{pool_sz}"
            pt_res["pools"][pk] = metrics
            all_pos.extend(pos_s)
            all_neg.extend(neg_s)

            r1 = metrics.get("recall_at_1", {})
            mrr = metrics.get("mrr", {})
            nq = metrics.get("nb_queries", 0)
            r1m = r1.get("mean", 0) if isinstance(r1, dict) else 0
            r1s = r1.get("std", 0) if isinstance(r1, dict) else 0
            mrrm = mrr.get("mean", 0) if isinstance(mrr, dict) else 0
            print(f"    pool {pool_sz}: R@1={r1m:.4f}+/-{r1s:.4f} MRR={mrrm:.4f} ({nq}q)")

            recall_pts[pool_sz] = r1 if isinstance(r1, dict) else {"mean": 0, "std": 0}

            if pool_sz == max(pool_sizes) and pos_s and neg_s:
                roc_data[pt_name] = ([1]*len(pos_s) + [0]*len(neg_s), list(pos_s) + list(neg_s))

        results[pt_name] = pt_res
        recall_data[pt_name] = recall_pts

    # plots
    if all_pos or all_neg:
        plot_similarity_distribution(all_pos, all_neg, out_dir / "similarity_distribution.png")
    if roc_data:
        plot_roc_curves(roc_data, out_dir / "roc_curve.png")
    if recall_data:
        plot_recall_vs_poolsize(recall_data, pool_sizes, out_dir / "recall_vs_poolsize.png")
    if cc_pairs:
        plot_cross_compiler_heatmap(matrix, key_to_idx, index, approach, cc_pairs, out_dir / "cross_compiler_heatmap.png")

    stats = {"total_functions": len(index), "pairs_skipped_inlining": inl_stats}
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
    parser.add_argument("--approach", default=None,
                        help="ne lancer que cette approche (ex: palmtree, asm2vec)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    paths = cfg["paths"]
    emb_dir = Path(paths["embeddings"])
    results_dir = Path(paths["results"])

    if not emb_dir.exists():
        print(f"Erreur: {emb_dir} n'existe pas")
        sys.exit(1)

    index = load_index(emb_dir)
    print(f"{len(index)} fonctions dans l'index")

    approaches_found = set()
    for entry in index.values():
        for app in entry.get("embeddings", {}):
            approaches_found.add(app)
    print(f"Approches: {', '.join(sorted(approaches_found))}")

    if args.approach:
        if args.approach not in approaches_found:
            print(f"Erreur: approche '{args.approach}' pas dans l'index")
            print(f"  disponibles: {', '.join(sorted(approaches_found))}")
            sys.exit(1)
        to_run = [args.approach]
    else:
        to_run = sorted(approaches_found)

    for approach in to_run:
        matrix, key_to_idx = preload_embeddings(index, approach)
        run_benchmark(approach, index, cfg, results_dir, matrix, key_to_idx)

    print("\nBenchmark termine")