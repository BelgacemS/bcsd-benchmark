## Scripts

Ce dossier contient tous les scripts annexes du projet.

### Objectif

- **Lancement du pipeline** : scripts qui lancent les étapes (scraping, compilation, évaluation)
- **Utilitaires** : statistiques, upload GCP, génération de paires, nettoyage

### Convention

- Nommage : `run_<étape>.sh` pour les lancements, `<action>_<cible>.py` pour les utilitaires
- Exemples :
  - `run_compilation.sh` — lancer la compilation multi-config
  - `run_eval_trex.sh` — lancer l'évaluation Trex
  - `stats_dataset.py` — statistiques sur le dataset
  - `upload_gcp.sh` — upload du dataset vers GCP
  - `generate_pairs.py` — génération des paires similaires / non similaires
