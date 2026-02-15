## BCSD Benchmark (Work In Progress)

L'objectif du projet est de construire un benchmark diversifié et réaliste pour la détection de similarité de code binaire en exploitant des implémentations multi-langages de tâches identiques, puis d'évaluer les approches état de l'art sur ce nouveau benchmark.

### Structure du projet

```
bcsd-benchmark/
├── src/                     Code source principal
│   ├── scrapers/            Collecte de code (RosettaCode, etc.)
│   ├── compilation/         Pipeline de compilation en binaires (à venir)
│   └── evaluation/          Évaluation des modèles BCSD (à venir)
├── data/
│   └── sample/              Échantillon du dataset (commité sur git)
├── scripts/                 Scripts de lancement et utilitaires
├── tests/                   Tests unitaires et d'intégration
├── docs/                    Documentation et guides
├── requirements.txt         Dépendances Python
└── README.md
```

Le dataset complet est envoyé sur GCP (pipeline à venir), seul l'échantillon est commité sur git.

### Composants

| Composant | Dossier | Statut |
|-----------|---------|--------|
| Scraper RosettaCode | `src/scrapers/` | Fonctionnel |
| Pipeline de compilation | `src/compilation/` | À venir |
| Évaluation BCSD | `src/evaluation/` | À venir |
| Scripts et utilitaires | `scripts/` | À venir |
| Tests | `tests/` | À venir |

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

### Étapes du projet (voir sujet)

1. **Collecte et curation** — scraping RosettaCode (fait), CodinGame (à venir)
2. **Compilation** — multi-compilateurs, multi-architectures, multi-optimisations
3. **Construction du dataset** — paires annotées avec labels de similarité sémantique
4. **Baselines** — features manuelles, méthodes graph-based
5. **Évaluation état de l'art** — LLMs, k-trans, Asm2Vec
6. **Analyse comparative** — forces, faiblesses, limites des approches
