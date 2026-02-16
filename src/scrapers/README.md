## Scrapers

Ce dossier contient les scripts de collecte de code source depuis différentes plateformes.

### Scrapers disponibles

| Script | Source | Langages | Statut |
|---|---|---|---|
| `rosetta_scraper.py` | RosettaCode | C, C++, Rust, Go | Fonctionnel |

### Utilisation

#### RosettaCode

```bash
python src/scrapers/rosetta_scraper.py -l 20 -v (exemple)
```

Options :
- `-o <dir>` : dossier de sortie (défaut: `data/sample` ; pour un run complet vers GCP,on doit passer un chemin bucket ou temporaire)
- `-l N` : N max de tâches
- `-v` : mode verbose (affichage détaillé pendant l'exécution du scraper)
- `-m N` : impose qu'une tâche possède au moins N langages différents parmi C, C++, Rust, Go (important pour la détection de similarité binaire)
- `-f <mot>` : filtrer par mot-clé
- `-d <sec>` : délai entre requêtes en cas de rate limit
- `--no-strict` : désactive la validation stricte par CodeValidator

### Pipeline du scraper

```
API RosettaCode
      │
      ▼
  Liste des tâches (Category:Programming_Tasks)
      │
      ▼ 
  Récupération du wikitext (pour chaque tâche)
      │
      ▼
  Détection de tous les headers de section (toutes langues)
      │
      ▼
  Découpage en sections (frontière = prochain header de N'IMPORTE QUEL langage)
      │
      ▼ 
  Extraction des blocs <syntaxhighlight> et <lang> (pour chaque section C/C++/Rust/Go)
      │
      ▼
  Filtrage C# (pour sections C/C++ uniquement)
      │
      ▼
  Validation heuristique (CodeValidator)
      │
      ▼
  Fusion des fragments (_merge_fragments)
      │
      ▼
  Sauvegarde
```

### Système de validation (CodeValidator)

Le `CodeValidator` applique une série de vérifications heuristiques pour rejeter les blocs invalides :

1. **Bloc vide** -> rejeté
2. **Wikitext** -> détection de `{{header|`, `{{lang|`, `[[Category:`, `<ref>` -> rejeté
3. **Trop court** -> seuils min de caractères (80) et lignes (5) en mode strict
4. **Autre langage** -> détection de patterns typiques de **~20 langages** :
   - Python, JavaScript, Java, Factor, Fortran, COBOL, Lisp/Scheme/Clojure, Pascal/Delphi, D, Haskell, Erlang, BASIC, OCaml/F#, Nim, Ring, REXX, Perl, Ruby, Icon/Unicon
   - Rejeté si >= 2 patterns d'un autre langage matchent
5. **Pas du code** -> vérifie la présence de `{}` (Go/Rust) ou `[;{}]` (C/C++) et d'appels de fonctions
6. **Marqueurs insuffisants** (mode strict) -> vérifie >= 2 marqueurs du langage cible (ex: `#include`, `printf`, `struct` pour C)

### Fusion des fragments

Sur RosettaCode, certaines sections contiennent un programme **découpé en plusieurs blocs** `<syntaxhighlight>` (code bibliothèque + différents `main()`). Le scraper détecte et fusionne ces fragments :

- **Blocs sans `main()`** = code bibliothèque (headers, fonctions partagées)
- **Blocs avec `main()`** = programmes de démonstration

Règles :
- **Pas de blocs bibliothèqes** -> chaque bloc main = implémentation indépendante (gardées toutes)
- **Blocs bibliothèques présents** -> fusionnés avec **le premier `main()` uniquement**
  - Les autres `main()` sont des variantes/démos du même algorithme, pas des implémentations distinctes `bibliothèque+main_A` et `bibliothèque+main_B` produiraient des binaires quasi identiques, ce qui biaiserait les métriques de similarité
- **Aucun bloc main** -> tout fusionné en un seul fichier

### Gestion des headers combinés

Le scraper gère les headers RosettaCode combinés comme :
```
=={{header|Icon}} and {{header|Unicon}}==
```
Ces headers sont détectés pour délimiter les sections, même s'ils contiennent plusieurs langages dans un même titre.

### Ajouter un nouveau scraper

Chaque scraper doit :
1. Extraire du code source depuis une plateforme (ex: GitHub, LeetCode, …)
2. Sauvegarder dans `<output_dir>/<source>/<task>/<Langage>/impl_XX.ext`
3. Générer un fichier de métadonnées `<output_dir>/<source>_metadata.json`
4. Valider les blocs via `CodeValidator` (ou équivalent)

Par défaut la sortie est `data/sample/`. Pour un run complet, on doit utiliser `-o` vers un chemin GCP ou temporaire (le dataset complet est envoyé sur GCP, pas stocké localement)

### Structure de sortie commune

```
data/
└── sample/                 
    └── rosetta_code/
        ├── <task>/
        │   ├── C/
        │   │   └── impl_01.c
        │   ├── Cpp/
        │   │   └── impl_01.cpp
        │   ├── Rust/
        │   │   └── impl_01.rs
        │   └── Go/
        │       └── impl_01.go
        └── ...
```
