## Tests

Ce dossier contient les tests unitaires et d'intégration du projet

### Objectif

Vérifier le bon fonctionnement des composants :
- `CodeValidator` : validation heuristique correcte
- `RosettaScraper` : parsing des sections, fusion des fragments
- Pipeline de compilation : compilation réussie sur des cas connus

### Convention

- Framework (probablement à confirmer plus tard) : `pytest`
- Nommage : `test_<module>.py`
- Exemples : `test_validator.py`, `test_scraper.py`, `test_compilation.py`

### Lancer les tests

```bash
pytest tests/
```