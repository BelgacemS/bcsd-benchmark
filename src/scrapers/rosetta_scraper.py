""" Scraper RosettaCode """

import re
import json
import time
import argparse 
from pathlib import Path # Pour du multi OS 
from typing import Optional # Pour des params de retour qui peuvent être None
import requests 
from tqdm import tqdm # Pour l'affichage de la progression (pour pouvoir debug)



API_URL = "https://rosettacode.org/w/api.php"

class CodeValidator:

    def __init__(
        self,
        strict_mode: bool = True, # Si True il faut au moins 2 marqueurs pour le langage cible pour accepter un bloc
        check_compilation: bool = False, # Prévu pour une future vérification par compilation apres la validation post heuristique
        min_chars: Optional[int] = None,
        min_lines: Optional[int] = None,
    ):
        self.strict_mode = strict_mode
        self.check_compilation = check_compilation
        self.min_chars = min_chars if min_chars is not None else (80 if strict_mode else 30) # 80 caractères minimum pour un bloc de code valide sinon 30 caractères
        self.min_lines = min_lines if min_lines is not None else (5 if strict_mode else 3) # 5 lignes minimum pour un bloc de code valide sinon 3 lignes

        self._wiki_patterns = [
            re.compile(r"\{\{\s*header\s*\|", re.IGNORECASE), # pattern pour détecter le header de la section
            re.compile(r"\{\{\s*lang\s*\|", re.IGNORECASE), # pattern pour détecter le langage de la section
            re.compile(r"\[\[\s*Category:", re.IGNORECASE),
            re.compile(r"<ref\b", re.IGNORECASE), 
            re.compile(r"</ref>", re.IGNORECASE),
        ]

        # Si plus tard si on ajoute un autre langage, on doit supprimer ses patterns ici
        self._non_c_patterns = [

            # Python 
            re.compile(r"^\s*def\s+\w+\s*\(.*\)\s*:", re.MULTILINE),
            re.compile(r"^\s*class\s+\w+\s*:\s*$", re.MULTILINE),
            re.compile(r"^\s*print\s*\(", re.MULTILINE),

            # JavaScript 
            re.compile(r"\bconsole\.log\s*\(", re.IGNORECASE),
            re.compile(r"\bfunction\s+\w+\s*\(", re.IGNORECASE),

            # Java 
            re.compile(r"\bSystem\.out\.print", re.IGNORECASE),
            re.compile(r"^\s*public\s+class\b", re.MULTILINE),

            # Factor 
            re.compile(r"^\s*USING\s*:", re.MULTILINE),
            re.compile(r"^\s*IN\s*:\s+\S+", re.MULTILINE),
            re.compile(r"^\s*TUPLE\s*:\s+\w+", re.MULTILINE),
            re.compile(r"^\s*:\s+\S+\s+\([^)]*--[^)]*\)", re.MULTILINE),

            # Fortran 
            re.compile(r"^\s*program\s+\w+", re.MULTILINE | re.IGNORECASE),
            re.compile(r"^\s*implicit\s+none", re.MULTILINE | re.IGNORECASE),
            re.compile(r"^\s*subroutine\s+\w+", re.MULTILINE | re.IGNORECASE),
            re.compile(r"\bINTEGER\s*::", re.IGNORECASE),

            # COBOL 
            re.compile(r">>SOURCE", re.IGNORECASE),
            re.compile(r"IDENTIFICATION\s+DIVISION", re.IGNORECASE),
            re.compile(r"PROGRAM-ID\.", re.IGNORECASE),

            # Lisp / Scheme / Clojure 
            re.compile(r"^\s*\(defun\b", re.MULTILINE),
            re.compile(r"^\s*\(define\b", re.MULTILINE),
            re.compile(r"^\s*\(defpackage\b", re.MULTILINE | re.IGNORECASE),
            re.compile(r"^\s*\(ns\s", re.MULTILINE),
            re.compile(r"^\s*\(defconstant\b", re.MULTILINE),

            # Pascal / Delphi 
            re.compile(r"\{\$APPTYPE", re.IGNORECASE),
            re.compile(r"^\s*program\s+\w+\s*;", re.MULTILINE | re.IGNORECASE),
            re.compile(r"^\s*procedure\s+\w+\s*;", re.MULTILINE | re.IGNORECASE),

            # D language 
            re.compile(r"^\s*import\s+std\.\w+", re.MULTILINE),
            re.compile(r"^\s*import\s+core\.\w+", re.MULTILINE),

            # Haskell 
            re.compile(r"^\s*import\s+Data\.\w+", re.MULTILINE),
            re.compile(r"^\s*import\s+Control\.\w+", re.MULTILINE),
            re.compile(r"\{-#", re.MULTILINE),

            # Erlang 
            re.compile(r"^-module\(", re.MULTILINE),
            re.compile(r"^-export\(", re.MULTILINE),

            # BASIC (lignes numérotées) 
            re.compile(r"^\d+\s+rem\b", re.MULTILINE | re.IGNORECASE),
            re.compile(r"^\d+\s+\w+", re.MULTILINE),

            # OCaml / F# 
            re.compile(r"^\s*let\s+rec\b", re.MULTILINE),
            re.compile(r"^\s*open\s+System\b", re.MULTILINE),
            re.compile(r"\|>\s*\w+", re.MULTILINE),

            # Nim 
            re.compile(r"^\s*proc\s+\w+.*=\s*$", re.MULTILINE),
            re.compile(r"^\s*import\s+\w+\s*,\s*\w+", re.MULTILINE),
            
            # Ring 
            re.compile(r'^\s*load\s+".*\.ring"', re.MULTILINE | re.IGNORECASE),

            # REXX 
            re.compile(r"/\*REXX", re.IGNORECASE),

            # Perl 
            re.compile(r"^\s*use\s+strict\b", re.MULTILINE),
            re.compile(r"\bmy\s+\$\w+", re.MULTILINE),

            # Ruby 
            re.compile(r"^\s*require\s+['\"]", re.MULTILINE),
            re.compile(r"^\s*puts\s+", re.MULTILINE),

            # Icon / Unicon 
            re.compile(r"^\s*procedure\s+\w+\s*\(", re.MULTILINE),
            re.compile(r"\bevery\b.*:=\s*!", re.MULTILINE),
        ]
        self._lang_markers = {
            "C": [
                re.compile(r"#\s*include\b"),
                re.compile(
                    r"\bint\b|\bvoid\b|\bchar\b|\bdouble\b|\bfloat\b|"
                    r"\blong\b|\bshort\b|\bunsigned\b|\bsigned\b"
                ),
                re.compile(r"\bprintf\s*\(|\bscanf\s*\(|\bmalloc\s*\(|\bfree\s*\(|\bputs\s*\("),
                re.compile(r"\bstruct\b|\btypedef\b|\benum\b|\bunion\b"),
                re.compile(r"\breturn\b"),
            ],
            "C++": [
                re.compile(r"#\s*include\b"),
                re.compile(
                    r"\bint\b|\bvoid\b|\bchar\b|\bdouble\b|\bfloat\b|"
                    r"\blong\b|\bshort\b|\bunsigned\b|\bsigned\b"
                ),
                re.compile(r"\bstd::\b|\bcout\b|\bcin\b|\bstring\b|\bvector<"),
                re.compile(r"\bnamespace\b|\btemplate\b|\bclass\b"),
                re.compile(r"\bstruct\b|\btypedef\b|\benum\b|\bunion\b"),
                re.compile(r"\breturn\b"),
            ],
            "Rust": [
                re.compile(r"\bfn\s+\w+"),
                re.compile(r"\blet\s+(mut\s+)?\w+"),
                re.compile(r"\bimpl\b|\bpub\b|\bmod\b|\buse\b"),
                re.compile(r"\bmatch\b"),
                re.compile(r"\bprintln!\s*\(|\bprint!\s*\(|\bformat!\s*\("),
                re.compile(r"\bOption\b|\bResult\b|\bSome\b|\bNone\b|\bOk\b|\bErr\b"),
                re.compile(r"->|::|\bunwrap\s*\("),
                re.compile(r"&str|&mut\b|&self\b"),
            ],
            "Go": [
                re.compile(r"\bfunc\s+\w+"),
                re.compile(r"\bpackage\s+\w+"),
                re.compile(r"\bimport\s*[\(\"]"),
                re.compile(r"\bfmt\.\w+"),
                re.compile(r":="),
                re.compile(r"\brange\b|\bdefer\b|\bchan\b|\bgo\s+\w+"),
                re.compile(r"\bPrintln\b|\bSprintf\b|\bPrintf\b"),
                re.compile(r"\breturn\b"),
            ],
        }

    def validate(self, code: str, lang: str):
        """ Validation heuristique """

        cleaned = code.strip() # sans espaces, tabulations et retour à la ligne

        if not cleaned:

            return False, "vide"

        if self.has_wiki_markup(cleaned):

            return False, "wikitext"

        stripped = self._strip_comments(cleaned) # sans commentaires

        if len(stripped) < self.min_chars or self.count_lines(stripped) < self.min_lines:
            return False, "trop_court"

        if self.looks_like_other_language(stripped):
            return False, "autre_langage"

        if not self.has_code_shape(stripped, lang):
            return False, "pas_du_code"

        if self.strict_mode and not self.has_lang_markers(stripped, lang):
            return False, "marqueurs_insuffisants"

        return True, "ok"

    def _strip_comments(self, code: str) -> str:

        code = re.sub(r"//.*", "", code)
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL) 

        return code

    def count_lines(self, code: str) -> int:
        """Compte le nombre de lignes non vides"""

        return sum(1 for line in code.splitlines() if line.strip())

    def has_wiki_markup(self, code: str) -> bool:
        """Vérifie si le code contient du wikitext"""

        return any(pat.search(code) for pat in self._wiki_patterns)

    def looks_like_other_language(self, code: str) -> bool:
        """Vérifie si le code ressemble à un autre langage"""

        hits = sum(1 for pat in self._non_c_patterns if pat.search(code))

        return hits >= 2

    def has_code_shape(self, code: str, lang: str = "") -> bool:
        """Vérifie si le code a une forme de code"""

        if lang in ("Go", "Rust"):
            # Go/Rust utilisent {} mais pas forcément 
            if not re.search(r"[{}]", code):
                return False
        else:
            if not re.search(r"[;{}]", code):
                return False

        if not re.search(r"\w\s*\(", code): # contient au moins une forme d'appel de fonction
            return False

        return True

    def has_lang_markers(self, code: str, lang: str) -> bool:
        """Vérifie si le code contient des marqueurs du langage cible"""

        markers = self._lang_markers.get(lang, [])
        if not markers:
            return True

        hits = sum(1 for pat in markers if pat.search(code))

        return hits >= 2


def task_name_to_snake_case(task_name):
    """ exemple: "Binary search" -> "binary_search"""

    # Remplacer caractères spéciaux par underscore 
    name = re.sub(r'[^\w\s]', '_', task_name)

    # Remplacer espaces multiples par underscore
    name = re.sub(r'\s+', '_', name)

    # Minuscules
    name = name.lower()

    # Retirer underscores multiples
    name = re.sub(r'_+', '_', name)

    # Retirer underscores début et fin
    name = name.strip('_')

    return name


class RosettaScraper:
    
    def __init__(self, output_dir: str = "data/sample", delay: float = 0.5, strict_validation: bool = True):

        self.base_dir = Path(output_dir)
        self.rosetta_dir = self.base_dir / "rosetta_code"
        self.delay = delay
        self.validator = CodeValidator(strict_mode=strict_validation) 
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "RosettaCode_1.0"
        })
        
        self.lang_dirs = {
            "C": "C",
            "C++": "Cpp",
            "Rust": "Rust",
            "Go": "Go",
        }
        
        self.stats = {
            "tasks_processed": 0,
            "tasks_saved": 0,
            "implementations": {"C": 0, "Cpp": 0, "Rust": 0, "Go": 0},
            "rejections": {},
        }
    
    def api_request(self, params):
        """Requête API MediaWiki"""

        params["format"] = "json"
        time.sleep(self.delay)
        
        try:
            response = self.session.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            
            print(f"Erreur API: {e}")

            return {}
    
    def _has_main_function(self, code: str, lang: str) -> bool:
        """Détecte si un bloc de code contient une fonction main() selon le langage"""

        if lang in ("C", "C++"):
            return bool(re.search(r'\b(int|void)\s+main\s*\(', code))
        elif lang == "Go":
            return bool(re.search(r'\bfunc\s+main\s*\(', code))
        elif lang == "Rust":
            return bool(re.search(r'\bfn\s+main\s*\(', code))
        return False

    def _merge_fragments(self, blocks: list[str], lang: str) -> list[str]:
        """Fusionne les fragments de code pour créer des implémentations complètes.
        
        - Blocs sans main() = code bibliothèque (headers, fonctions partagées)
        - Blocs avec main() = programmes
        - Si des blocs bibliothèques existent, on ne garde que le premier bloc main()
          car les autres mains sont des variantes/démos du même algorithme,
          pas des implémentations distinctes
        """

        if len(blocks) <= 1:
            return blocks

        blocs_bibliothèques = []
        main_blocks = []

        for block in blocks:
            if self._has_main_function(block, lang):
                main_blocks.append(block)
            else:
                blocs_bibliothèques.append(block)

        # Pas de blocs bibliothèques -> implémentations indépendantes (garder toutes)
        if not blocs_bibliothèques:
            return main_blocks if main_blocks else blocks

        # Blocs bibliothèques existent -> fusionner avec le premier bloc main uniquement
        # Les autres blocs main sont des variantes/démos du même algorithme
        prefix = "\n\n".join(blocs_bibliothèques)

        if main_blocks:
            return [prefix + "\n\n" + main_blocks[0]]

        # Aucun bloc main ->  tout fusionner en un seul bloc
        return [prefix]

    def is_csharp_code(self, code: str) -> bool:

        patterns = [
            r'using\s+System\b', r'Console\.Write', r'\.ToArray\s*\(',
            r'foreach\s*\(', r'\bList<', r'\bDictionary<',
        ]

        return sum(1 for p in patterns if re.search(p, code)) >= 2
    
    def get_all_tasks(self, filter_keyword: Optional[str] = None) -> list[str]:
        """Récupère toutes les tâches"""

        tasks = []
        
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": "Category:Programming_Tasks",
            "cmlimit": "500",
        }
        
        while True:

            data = self.api_request(params)

            if not data or "query" not in data:
                break
            
            for member in data["query"]["categorymembers"]:
                tasks.append(member["title"])
            
            if "continue" in data:
                params["cmcontinue"] = data["continue"]["cmcontinue"]

            else:
                break
        print("\n")
        print(f"{len(tasks)} tâches trouvées")
        
        if filter_keyword:
            tasks = [t for t in tasks if filter_keyword.lower() in t.lower()]

            print(f"{len(tasks)} après filtre '{filter_keyword}'")
        
        return tasks
    
    def get_task_contenu(self, task_name: str) -> Optional[str]:
        """Récupère le wikitext d'une tâche"""

        params = {
            "action": "query",
            "titles": task_name,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
        }
        
        data = self.api_request(params)

        if not data or "query" not in data:
            return None
        
        pages = data["query"]["pages"]
        page = next(iter(pages.values()))
        
        if "revisions" not in page:
            return None
        
        revision = page["revisions"][0]

        if "slots" in revision:
            return revision["slots"]["main"].get("*", "")

        elif "*" in revision:
            return revision["*"]
        
        return None
    
    def parse_blocs_code(self, wikitext: str) -> dict[str, list[str]]:
        """Parse et valide les blocs de code"""

        raw_codes = {}
        target_langs = {"C", "C++", "Rust", "Go"}
        
        # Trouver TOUS les headers (toutes langues confondues)
        # Pattern souple : détecte aussi les headers combinés comme
        # =={{header|Icon}} and {{header|Unicon}}==
        header_pattern = r'==\s*\{\{header\|([^}]+)\}\}'
        all_headers = []
        
        for match in re.finditer(header_pattern, wikitext, re.IGNORECASE):
            lang = match.group(1).strip()
            all_headers.append((match.start(), match.end(), lang))
        
        # Ne garder que les headers des langages cibles pour l'extraction
        target_headers = [(s, e, l) for s, e, l in all_headers if l in target_langs]
        
        # Extraire code par section (délimitée par le prochain header de n'importe quel langage)
        for start, end, lang in target_headers:

            # Trouver le prochain header (de n'importe quel langage) après celui-ci
            section_end = len(wikitext)
            for ah_start, _, _ in all_headers:
                if ah_start > start:
                    section_end = ah_start
                    break
            
            section = wikitext[end:section_end]
            
            # Patterns de code
            patterns = [
                r'<syntaxhighlight[^>]*>(.*?)</syntaxhighlight>',
                r'<lang[^>]*>(.*?)</lang>',
            ]
            
            for pattern in patterns:
                for match in re.finditer(pattern, section, re.DOTALL | re.IGNORECASE):

                    code = match.group(1).strip()
                    
                    if not code:
                        continue
                    
                    # Filtrer C# (uniquement pour les sections C/C++)
                    if lang in {"C", "C++"} and self.is_csharp_code(code):
                        self.stats["rejections"]["csharp"] = \
                            self.stats["rejections"].get("csharp", 0) + 1
                        continue
                    
                    # Validation
                    is_valid, reason = self.validator.validate(code, lang)
                    
                    if not is_valid:
                        self.stats["rejections"][reason] = \
                            self.stats["rejections"].get(reason, 0) + 1
                        continue
                    
                    # Code valide ->  collecte brute sans fusion
                    if lang not in raw_codes:
                        raw_codes[lang] = []
                    raw_codes[lang].append(code)
        
        # Fusion des fragments de code pour chaque langage
        codes = {}
        for lang, blocks in raw_codes.items():
            codes[lang] = self._merge_fragments(blocks, lang)
        
        return codes
    
    def save_task(self, task_name: str, codes: dict[str, list[str]]) -> bool:

        if not codes:
            return False
        
        # Nom de tâche en snake_case
        safe_name = task_name_to_snake_case(task_name)
        task_dir = self.rosetta_dir / safe_name
        
        # Sauvegarder chaque langage
        for lang, implementations in codes.items():
            lang_dir_name = self.lang_dirs[lang] 
            lang_dir = task_dir / lang_dir_name
            lang_dir.mkdir(parents=True, exist_ok=True)
            
            # Extension
            ext_map = {"C": ".c", "C++": ".cpp", "Rust": ".rs", "Go": ".go"}
            ext = ext_map.get(lang, ".txt")
            
            for i, code in enumerate(implementations, start=1):
                filename = f"impl_{i:02d}{ext}"  # impl_01.c, impl_02.c, ...
                filepath = lang_dir / filename
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code)
                
                # Stats
                self.stats["implementations"][lang_dir_name] = \
                    self.stats["implementations"].get(lang_dir_name, 0) + 1
        
        return True
    
    def scrape(self, 
               limit: Optional[int] = None,
               min_languages: int = 1,
               filter_keyword: Optional[str] = None,
               verbose: bool = False):
        """
        Lance le scraping
        
        Args: limit: Nombre max de tâches, min_languages: Minimum de langages requis (au moins 1 langage, au moins 2 langages, etc...), filter_keyword: Filtrer par mot-clé, verbose: Affichage détaillé

        """

        # Créer la structure de base si elle n'existe pas
        self.rosetta_dir.mkdir(parents=True, exist_ok=True)
        
        # Récupérer les tâches
        tasks = self.get_all_tasks(filter_keyword=filter_keyword)
        if limit:
            tasks = tasks[:limit]
        
        print(f"Scraping de {len(tasks)} tâches RosettaCode")
        print("\n")

        
        # Scraper les tâches
        for task_name in tqdm(tasks, desc="Progression"):
            self.stats["tasks_processed"] += 1
            
            content = self.get_task_contenu(task_name)
            if not content:
                continue
            
            codes = self.parse_blocs_code(content)
            
            # Filtrer par nombre de langages requis
            if len(codes) >= min_languages:
                if self.save_task(task_name, codes):
                    self.stats["tasks_saved"] += 1
                    
                    if verbose:
                        safe_name = task_name_to_snake_case(task_name)
                        langs = ", ".join(codes.keys())
                        
                        print(f"{safe_name}: [{langs}]")
        
        # Afficher les statistiques
        self.print_stats()
        self.save_metadata()
    
    def print_stats(self):
        """Affiche les statistiques"""

        print("\n")
        print(f"Scraping terminé")
        print("\n")

        print(f"Tâches analysées:    {self.stats['tasks_processed']}")
        print(f"Tâches sauvegardées: {self.stats['tasks_saved']}")
        print(f"\nImplémentations par langage:")

        for lang, count in self.stats["implementations"].items():
            print(f"   {lang:5s}: {count:4d} fichiers")
        
        if self.stats["rejections"]:
            print(f"\nRejets:")

            top_rejections = sorted( self.stats["rejections"].items(),key=lambda x: -x[1])[:5]

            for reason, count in top_rejections:
                print(f"   {reason:30s}: {count:4d}")
        
    
    def save_metadata(self):
        """Sauvegarde métadonnées globales"""
        
        from datetime import datetime
        
        metadata = {
            "source": "rosetta_code",
            "scrape_date": datetime.now().isoformat(),
            "total_tasks": self.stats["tasks_saved"],
            "implementations": self.stats["implementations"],
            "structure": "<output_dir>/rosetta_code/<task>/<C|Cpp|Rust|Go>/impl_XX.<ext>",
        }
        
        metadata_file = self.base_dir / "rosetta_metadata.json"

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        


def main():
    
    parser = argparse.ArgumentParser(
        description="Scraper RosettaCode",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    
    parser.add_argument(
        "-o", "--output",
        default="data/sample",
        help="Dossier de sortie (défaut : data/sample ; pour un run complet, passer -o vers GCP ou un chemin temporaire)"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=None,
        help="Nombre max de tâches"
    )
    parser.add_argument(
        "-m", "--min-languages",
        type=int,
        default=1,
        help="Langages minimum (1=au moins 1 langage, 2 = au moins 2 langages, etc...)"
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=0.5,
        help="Délai entre requêtes (en secondes)"
    )
    parser.add_argument(
        "-f", "--filter",
        type=str,
        default=None,
        help="Filtrer par mot-clé (ex: 'sort' pour filtrer les tâches contenant le mot 'sort')"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Affichage détaillé"
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Désactiver validation stricte"
    )
    
    args = parser.parse_args()
    
    scraper = RosettaScraper(
        output_dir=args.output,
        delay=args.delay,
        strict_validation=not args.no_strict
    )
    
    scraper.scrape(
        limit=args.limit,
        min_languages=args.min_languages,
        filter_keyword=args.filter,
        verbose=args.verbose
    )


if __name__ == "__main__":
    main()