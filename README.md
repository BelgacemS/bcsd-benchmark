## BCSD Benchmark (Work In Progress)

L'objectif du projet est de construire un benchmark diversifié et réaliste pour la détection de similarité de code binaire en exploitant des implémentations multi-langages de tâches identiques, puis d'évaluer les approches état de l'art sur ce nouveau benchmark.

### Structure du projet

```
bcsd-benchmark/
├── src/
│   ├── scrapers/
│   ├── compilation/  
│   └── evaluation/
├── data/
│   └── sample/
├── scripts/
├── tests/
├── docs/       
├── requirements.txt
└── README.md
```

Le dataset complet est envoyé sur GCP (pipeline à venir).


### Installation

```bash
pip install -r requirements.txt
```

### Utilisation rapide

```bash
# Scraper RosettaCode (20 tâches, mode verbose, sortie dans data/sample/)
python src/scrapers/rosetta_scraper.py -l 20 -v
```

Voir `src/scrapers/README.md` pour la documentation complète du scraper.

### Langages supportés

- C
- C++
- Rust
- Go