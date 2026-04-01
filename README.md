# BCSD Benchmark

Benchmark pour la detection de similarite de code binaire (Binary Code Similarity Detection).
On compile du code C/C++ avec differents compilateurs (GCC, Clang) et niveaux d'optimisation
(O0 a Os), on desassemble avec angr, et on evalue les modeles d'embeddings (PalmTree, Asm2Vec,
jTrans) sur leur capacite a capturer la similarite semantique plutot que syntaxique.

Projet de recherche, Sorbonne Universite, L3 Informatique.

## Structure du projet

```
bcsd-benchmark/
├── config.yaml              # configuration de toute la pipeline
├── CLAUDE.md                # instructions pour les agents
├── ARCHITECTURE.md          # specs I/O entre modules
├── AUDIT_REPORT.md          # audit de la codebase
├── requirements.txt
├── docker/
│   └── Dockerfile           # image x86-64 pour la compilation
├── lib/
│   └── palmtree/            # modele PalmTree (clone depuis github)
├── src/
│   ├── compile.py           # compilation des sources en ELF
│   ├── disasm.py            # desassemblage avec angr
│   ├── embed_palmtree.py    # generation des embeddings PalmTree
│   ├── benchmark.py         # evaluation (R@1, MRR, ROC AUC)
│   ├── run_pipeline.py      # orchestrateur avec sync GCP
│   ├── gcp_build.py         # compile + disasm sur VM GCP
│   └── scrapers/            # scraping RosettaCode, LeetCode, AtCoder
├── data/
│   ├── sources/             # code source (sur GCP, sample en local)
│   ├── binaries/            # executables ELF (gitignored)
│   ├── disasm/              # JSON desassembles (gitignored)
│   └── embeddings/          # vecteurs numpy (gitignored)
├── results/
│   └── palmtree/            # metriques, plots, rapport
├── scripts/                 # utilitaires (download, upload)
├── tests/
└── docs/                    # rapport, notes de reunion
```

## Prerequis

- Python 3.10+
- Docker (compilation cross x86-64 depuis Mac)
- Google Cloud SDK (gsutil, pour la sync avec le bucket)
- angr (desassemblage)

## Installation

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# image Docker pour la compilation
docker build -t bscd-compile docker/

# modele PalmTree
git clone https://github.com/AsmFinder/PalmTree.git lib/palmtree
```

## Configuration

Tout est dans `config.yaml` : langages, compilateurs, architectures, niveaux
d'optimisation, backend de desassemblage, approches de similarite, types de
paires pour le benchmark.

## Usage

### Test local rapide

```bash
python3 src/compile.py --test
python3 src/disasm.py --test
python3 src/embed_palmtree.py --test
python3 src/benchmark.py --test
```

Ou via l'orchestrateur :

```bash
python3 src/run_pipeline.py --test
```

### Full dataset sur VM GCP

La compilation et le desassemblage des ~28 000 fichiers sont trop lents en local.
`gcp_build.py` cree une VM x86-64 sur GCP, compile tout en parallele, desassemble
avec angr, et push les resultats sur le bucket.

```bash
python3 src/gcp_build.py
python3 src/gcp_build.py --dry-run
python3 src/gcp_build.py --skip-compile
python3 src/gcp_build.py --skip-disasm
python3 src/gcp_build.py --parallel 48
```

### Benchmark

```bash
python3 src/benchmark.py
python3 src/benchmark.py --approach palmtree
```

## Resultats

Les resultats sont dans `results/{approach}/` : metriques JSON, plots de
distribution des similarites, courbes ROC, heatmaps cross-compilateur,
et rapport markdown genere automatiquement.
