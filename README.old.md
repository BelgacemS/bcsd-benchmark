# BCSD Benchmark

Projet de recherche en Binary Code Similarity Detection (BCSD), Sorbonne Université, L3 Informatique.

## Contexte

Les modèles de similarité binaire (PalmTree, jTrans, Asm2Vec...) obtiennent de très
bons résultats sur les benchmarks classiques (binutils, coreutils, OpenSSL) pour
retrouver une même fonction compilée avec différents compilateurs ou niveaux
d'optimisation. Cependant, ces benchmarks ne couvrent qu'un seul scénario :
**même code source, compilations différentes**.

La question de savoir si ces modèles capturent réellement la **sémantique** du
code binaire, au-delà de sa syntaxe, reste largement ouverte. Deux implémentations
indépendantes du même algorithme produisent du code binaire structurellement
différent. Les benchmarks existants ne permettent pas d'évaluer ce cas.

## Objectif

Ce projet propose un benchmark qui évalue la similarité binaire à
**trois niveaux de difficulté** :

| Niveau | Description | Exemple |
|--------|-------------|---------|
| **Facile** | Même code, compilation différente | gcc -O0 vs clang -O3 |
| **Moyen** | Même algorithme, implémentation différente | deux quicksorts indépendants en C |
| **Difficile** | Même algorithme, langages différents | quicksort en C vs en C++ |

Les niveaux moyen et difficile sont quasiment absents de la littérature
(Marcelli et al., 2022). Notre dataset, construit à partir de plateformes de
programmation compétitive (RosettaCode, LeetCode, AtCoder), contient plusieurs
implémentations indépendantes des mêmes problèmes algorithmiques, ce qui rend
l'évaluation de ces niveaux possible.

## Pipeline

```
sources C/C++ (28 000 fichiers)
    | compilation (gcc, clang x O0-Os)
exécutables ELF x86-64
    | désassemblage (angr, filtrage DWARF)
fonctions assembleur (JSON)
    | embeddings (modèles BCSD)
vecteurs de similarité
    | benchmark (recall@1, MRR, ROC AUC)
résultats + graphes
```

## Résultats

Les résultats sont dans `results/{approach}/` : métriques JSON, distribution
des similarités, courbes ROC, heatmaps cross-compilateur, et recall@1 en
fonction de la taille du pool.

Le benchmark est évalué sur plusieurs tailles de pool (100, 1000, 10000) avec
des milliers de runs pour garantir des intervalles de confiance statistiquement
significatifs.

## Usage

### Test local (sample)

```bash
python3 src/compile.py --test        # compilation
python3 src/disasm.py --test         # désassemblage
python3 src/embed_palmtree.py        # embeddings (un script par approche)
python3 src/benchmark.py             # évaluation
```

### Full dataset (VM GCP)

```bash
python3 src/gcp_build.py --phases compile disasm    # VM CPU
python3 src/gcp_build.py --phases embed             # VM GPU
python3 src/gcp_build.py --phases benchmark         # VM CPU
```

## Installation

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Configuration dans `config.yaml` : compilateurs, optimisations, backend de
désassemblage, métriques du benchmark, niveaux de similarité.
