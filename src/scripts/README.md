## Scripts

Ce dossier contient tous les scripts annexes du projet.

### Objectif

- **Lancement du pipeline** : scripts qui lancent les grandes étapes (scraping, compilation, évaluation)
- **Utilitaires** : statistiques, interactions avec GCP (upload/download), génération de paires, nettoyage

  - `run_compilation.sh` — lancer la compilation multi-config (à faire)
  - `run_eval_trex.sh` — lancer l'évaluation Trex (à faire)
  - `download_sample.sh` — télécharger un échantillon du dataset depuis GCP
  - `upload_gcp.sh` — uploader le dataset complet vers GCP
  - `stats_dataset.py` — générer des statistiques sur le dataset ( à faire)
  - `generate_pairs.py` — générer des paires (similaires / non similaires) ( à faire)
