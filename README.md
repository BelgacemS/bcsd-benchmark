# BCSD Benchmark

Projet de recherche en Binary Code Similarity Detection, Sorbonne Université, L3 Informatique.

## Contexte

Les modèles de similarité binaire (PalmTree, jTrans, Asm2Vec...) obtiennent de très
bons résultats sur les benchmarks classiques (binutils, coreutils, OpenSSL) pour
retrouver la même fonction compilée différemment. Mais ces benchmarks ne testent
qu'un seul scénario : **même code source, compilations différentes**.

Une question reste ouverte : est-ce que ces modèles capturent la **sémantique** du
code, ou seulement sa syntaxe ? Deux implémentations différentes du même algorithme
produisent du code binaire très différent. Aucun benchmark existant ne permet
vraiment de tester ce cas.

## Objectif

On construit un benchmark qui teste la similarité à **3 niveaux de difficulté** :

| Niveau | Description | Exemple |
|--------|-------------|---------|
| **Facile** | Même code, compilation différente | gcc -O0 vs clang -O3 |
| **Moyen** | Même algorithme, implémentation différente | deux quicksorts différents en C |
| **Difficile** | Même algorithme, langages différents | quicksort en C vs en C++ |

Les niveaux moyen et difficile sont quasiment absents de la littérature. Notre dataset,
construit à partir de plateformes de programmation compétitive (RosettaCode, LeetCode,
AtCoder), contient plusieurs implémentations indépendantes des mêmes problèmes
algorithmiques, ce qui rend ces niveaux possibles.

## Pipeline

```
sources C/C++ (28 000 fichiers)
    | compilation (gcc, clang x O0-Os)
exécutables ELF x86-64
    | désassemblage (angr, filtrage DWARF)
fonctions assembleur (JSON)
    | embeddings (PalmTree, baselines)
vecteurs de similarité
    | benchmark (recall@1, MRR, ROC AUC)
résultats + graphes
```

## Résultats

Les résultats sont dans `results/{approach}/` : métriques JSON, distribution
des similarités, courbes ROC, heatmaps cross-compilateur, et recall@1 en
fonction de la taille du pool.

Le benchmark teste avec plusieurs tailles de pool (100, 1000, 10000) et des
milliers de runs pour des intervalles de confiance solides.

## Usage

### Test local (sample)

```bash
python3 src/compile.py --test
python3 src/disasm.py --test
python3 src/embed_palmtree.py --device cpu
python3 src/embed_baseline.py
python3 src/benchmark.py
```

### Full dataset (VM GCP)

```bash
python3 src/gcp_build.py --phases compile disasm    # VM CPU
python3 src/gcp_build.py --phases embed              # VM GPU
python3 src/gcp_build.py --phases benchmark           # VM CPU
```

## Installation

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Configuration dans `config.yaml` : compilateurs, optimisations, backend de
désassemblage, métriques du benchmark, niveaux de similarité.
