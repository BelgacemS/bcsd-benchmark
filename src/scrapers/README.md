## Scrapers

Ce dossier contient les scripts de collecte de code source depuis différentes plateformes.

### Scrapers disponibles

| Script | Source | Langages | Statut |
|---|---|---|---|
| `rosetta_scraper.py` | RosettaCode | C, C++, Rust, Go | Fonctionnel |
| `atcode_scraper.py` | AtCoder (ABC) | C, C++, Rust, Go | Fonctionnel |

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
  Découpage en sections (frontière = prochain header de n'importe quel langage)
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

---

### AtCoder (ABC)

```bash
python src/scrapers/atcode_scraper.py
```

Configuration via `.env` :
- `CONTEST_START` : numéro du premier contest ABC (défaut : `100`)
- `CONTEST_END` : numéro du dernier contest ABC (défaut : `445`)
- `REVEL_SESSION` : cookie de session AtCoder (obligatoire, obtenu après connexion)
- `TARGET_LANGS` : langages cibles séparés par des virgules (défaut : `C++,C,Rust,Go`)
- `PROBLEMS` : lettres des problèmes (défaut : `a,b,c,d`)
- `OUTPUT_DIR` : dossier de sortie (défaut : `data/atcoder`)
- `NUM_IMPLEMENTATIONS` : nombre d'implémentations par langage (défaut : `3`)

### Pipeline du scraper AtCoder

```
Boucle sur les contests ABC (100 → 445)
      │
      ▼
  Pour chaque problème (a, b, c, d)
      │
      ▼
  Récupération du nom du problème (page de la tâche AtCoder)
      │
      ▼
  Pour chaque langage cible (C, C++, Rust, Go)
      │
      ▼
  Recherche de soumissions AC (f.Status=AC, f.LanguageName=...)
      │
      ▼
  Filtrage par utilisateurs distincts (max 3 par langage)
      │
      ▼
  Pagination (jusqu'à 10 pages si nécessaire)
      │
      ▼
  Téléchargement du code source (<pre id="submission-code">)
      │
      ▼
  Sauvegarde dans <output_dir>/<problem_name>/<Lang>/impl_XX.ext
      │
      ▼
  Génération du fichier de métadonnées atcoder_metadata.json
```

### Filtrage des langages

Le scraper utilise deux niveaux de filtrage pour garantir la bonne correspondance des langages :

1. **Filtre URL** (`f.LanguageName`) : paramètre de requête AtCoder pour pré-filtrer côté serveur
2. **Vérification locale** (`lang_matches`) : validation stricte du texte de la colonne langage
   - **C** : doit commencer par `C ` ou `C(` pour éviter C++, C#, Cython, etc.
   - **C++** : vérifie la présence de `C++` dans le texte
   - **Rust** / **Go** : vérifie que le texte commence par le nom du langage

### Diversité des implémentations

Pour chaque langage et problème, le scraper collecte jusqu'à 3 soumissions provenant d'**utilisateurs différents** (`seen_users`), ce qui garantit des implémentations diversifiées plutôt que des doublons du même auteur.

### Authentification

Le scraper nécessite un cookie `REVEL_SESSION` valide pour accéder aux soumissions AtCoder. Ce cookie est obtenu en se connectant manuellement sur le site et en copiant la valeur depuis les outils développeur du navigateur.
