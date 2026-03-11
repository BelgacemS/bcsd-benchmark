## Scrapers

Ce dossier contient les scripts de collecte de code source depuis differentes plateformes

### Scrapers disponibles

- **`rosetta_scraper.py`** — RosettaCode (C, C++, Rust, Go)
- **`leetcode_scraper.py`** — LeetCode via le repo GitHub doocs/leetcode (C, C++, Rust, Go)
- **`atcoder_scraper.py`** — AtCoder, contests ABC (C, C++, Rust, Go)

### Structure de sortie

Tous les scrapers produisent la meme structure :

```
<output_dir>/
    <source>/
        <task>/
            C/
                impl_01.c
            Cpp/
                impl_01.cpp
            Rust/
                impl_01.rs
            Go/
                impl_01.go
    <source>_metadata.json
```

Par defaut la sortie est `data/sample/`. Pour un run complet, utiliser `-o` vers un chemin temporaire puis uploader sur GCP via `scripts/scrape_and_upload.sh`

---

### Utilisation

#### RosettaCode

```bash
python src/scrapers/rosetta_scraper.py -l 20 -v
```

Options :
- `-o <dir>` : dossier de sortie (defaut: `data/sample`)
- `-l N` : N max de taches
- `-v` : mode verbose
- `-m N` : impose qu'une tache possede au moins N langages
- `-f <mot>` : filtrer par mot-cle
- `-d <sec>` : delai entre requetes

Le scraper recupere les taches via l'API MediaWiki, extrait le code depuis les balises `<syntaxhighlight>` et `<lang>`, puis valide chaque bloc avec le `CodeValidator` (detection de wikitext, filtrage des autres langages, verification de la forme du code).

Quand une tache a plusieurs blocs de code pour un meme langage, le scraper essaie de les fusionner intelligemment (blocs bibliotheque + bloc main)

#### LeetCode (doocs/leetcode GitHub)

```bash
python src/scrapers/leetcode_scraper.py -l 50 -m 2 -v
```

Options :
- `-o <dir>` : dossier de sortie (defaut: `data/sample`)
- `-l N` : N max de problemes
- `-m N` : langages minimum par probleme
- `-d <sec>` : delai entre telechargements (defaut: 0.05s)
- `-v` : mode verbose

Le scraper utilise l'API Git Trees de GitHub pour recuperer l'arborescence complete du repo `doocs/leetcode` en une seule requete, puis telecharge les fichiers `Solution.{c,cpp,go,rs}` via `raw.githubusercontent.com`. Pas besoin d'authentification.

#### AtCoder (ABC)

```bash
python src/scrapers/atcoder_scraper.py -o data/sample
```

Options :
- `-o <dir>` : dossier de sortie (defaut: `data/sample` ou `$OUTPUT_DIR`)
- `--contest-start N` : numero du premier contest ABC (defaut: 100)
- `--contest-end N` : numero du dernier contest ABC (defaut: 445)
- `--problems a,b,c,d` : lettres des problemes
- `--langs C++,C,Rust,Go` : langages cibles
- `--num-impl N` : nombre d'implementations par langage (defaut: 3)

Configuration `.env` (pour le cookie) :
- `REVEL_SESSION` : cookie de session AtCoder (obligatoire)

Les autres parametres (CONTEST_START, etc.) peuvent etre passes en `.env` ou en arguments CLI. Les arguments CLI ont la priorite.

---

### Upload vers GCP

Le script `scripts/scrape_and_upload.sh` lance les 3 scrapers et upload sur GCP :

```bash
bash scripts/scrape_and_upload.sh
```

Le bucket cible est `gs://bscd-database/sources/`.

---

### CodeValidator (RosettaCode)

Le `CodeValidator` sert a filtrer les blocs de code invalides recup sur RosettaCode. Il fait ca :

1. Rejete les blocs vides
2. Detecte le wikitext (`{{header|`, `[[Category:`, etc.)
3. Rejete les blocs trop courts (< 80 chars ou < 5 lignes en mode strict)
4. Detecte les blocs qui sont en fait du Python, Java, JavaScript etc. (et pas du C/C++/Rust/Go)
5. Verifie que le code a la bonne "forme" (accolades, appels de fonction) et les marqueurs du langage cible

