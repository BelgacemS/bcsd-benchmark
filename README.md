## BCSD Benchmark (Work In Progress)

L'objectif du projet est de construire un benchmark diversifié et réaliste pour la détection de similarité de code binaire en exploitant des implémentations multi-langages de tâches identiques, puis d'évaluer les approches état de l'art sur ce nouveau benchmark.

### Structure du projet

```
bcsd-benchmark/
├── src/
│   ├── scrapers/          # collecte de code source
│   ├── compilation/       # pipeline de compilation
│   └── evaluation/        # evaluation BCSD
├── data/
│   └── sample/            # echantillon local du dataset
├── scripts/               # utilitaires (download, upload GCP, metadata)
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

### Installation

```bash
pip install -r requirements.txt
```

### Utilisation rapide

```bash
# Scrapers
python src/scrapers/rosetta_scraper.py
python src/scrapers/leetcode_scraper.py
python src/scrapers/atcoder_scraper.py

# Telecharger un sample depuis GCP
./scripts/download_sample.sh leetcode 20
./scripts/download_sample.sh all 20

# Scraper + upload GCP
bash scripts/scrape_and_upload.sh
```

Voir `src/scrapers/README.md` pour la documentation complete des scrapers.

### Langages cibles

C, C++, Rust, Go

### Donnees

Le dataset complet est stocke sur GCP (`gs://bscd-database/sources/`). En local on travaille avec un sample telecharge via `scripts/download_sample.sh`.