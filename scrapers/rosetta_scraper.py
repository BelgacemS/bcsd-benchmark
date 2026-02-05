""" Scraper RosettaCode 

Structure de sortie :

dataset/
├── rosetta_code/
│   ├── binary_search/
│   │   ├── C/
│   │   │   ├── impl_01.c
│   │   │   └── impl_02.c
│   │   └── Cpp/
│   │       └── impl_01.cpp
│   ├── bubble_sort/
│   │   ├── C/
│   │   │   └── impl_01.c
│   │   └── Cpp/
│   │       └── impl_01.cpp
...
"""

import re
import json
import time
import argparse
from pathlib import Path
from typing import Optional
import requests
from tqdm import tqdm



API_URL = "https://rosettacode.org/w/api.php"

class CodeValidator:

    def __init__(
        self,
        strict_mode: bool = True,
        check_compilation: bool = False,
        min_chars: Optional[int] = None,
        min_lines: Optional[int] = None,
    ):
        self.strict_mode = strict_mode
        self.check_compilation = check_compilation
        self.min_chars = min_chars if min_chars is not None else (80 if strict_mode else 30)
        self.min_lines = min_lines if min_lines is not None else (5 if strict_mode else 3)

        self._wiki_patterns = [
            re.compile(r"\{\{\s*header\s*\|", re.IGNORECASE),
            re.compile(r"\{\{\s*lang\s*\|", re.IGNORECASE),
            re.compile(r"\[\[\s*Category:", re.IGNORECASE),
            re.compile(r"<ref\b", re.IGNORECASE),
            re.compile(r"</ref>", re.IGNORECASE),
        ]
        self._non_c_patterns = [
            re.compile(r"^\s*def\s+\w+\s*\(.*\)\s*:", re.MULTILINE),
            re.compile(r"^\s*class\s+\w+\s*:\s*$", re.MULTILINE),
            re.compile(r"^\s*(import|from)\s+\w+", re.MULTILINE),
            re.compile(r"\bconsole\.log\s*\(", re.IGNORECASE),
            re.compile(r"\bSystem\.out\.print", re.IGNORECASE),
            re.compile(r"^\s*public\s+class\b", re.MULTILINE),
            re.compile(r"\bfunction\s+\w+\s*\(", re.IGNORECASE),
            re.compile(r"^\s*print\s*\(", re.MULTILINE),
        ]
        self._c_family_markers = [
            re.compile(r"#\s*include\b"),
            re.compile(
                r"\bint\b|\bvoid\b|\bchar\b|\bdouble\b|\bfloat\b|"
                r"\blong\b|\bshort\b|\bunsigned\b|\bsigned\b"
            ),
            re.compile(r"\bprintf\s*\(|\bscanf\s*\(|\bmalloc\s*\(|\bfree\s*\(|\bputs\s*\("),
            re.compile(r"\bstruct\b|\btypedef\b|\benum\b|\bunion\b"),
            re.compile(r"\bstd::\b|\bcout\b|\bcin\b|\bstring\b|\bvector<"),
            re.compile(r"\bnamespace\b|\btemplate\b|\bclass\b"),
            re.compile(r"\breturn\b"),
        ]

    def validate(self, code: str, lang: str):
        """Validation heuristique """

        cleaned = code.strip()

        if not cleaned:

            return False, "vide"

        if self.has_wiki_markup(cleaned):

            return False, "wikitext"

        stripped = self._strip_comments(cleaned)

        if len(stripped) < self.min_chars or self.count_lines(stripped) < self.min_lines:
            return False, "trop_court"

        if self.looks_like_other_language(stripped):
            return False, "autre_langage"

        if not self.has_code_shape(stripped):
            return False, "pas_du_code"

        if self.strict_mode and not self.has_c_family_markers(stripped):
            return False, "marqueurs_c_insuffisants"

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

    def has_code_shape(self, code: str) -> bool:
        """Vérifie si le code a une forme de code"""

        if not re.search(r"[;{}]", code):
            return False

        if not re.search(r"\w\s*\(", code):
            return False

        return True

    def has_c_family_markers(self, code: str) -> bool:
        """Vérifie si le code contient des marqueurs C/C++"""

        hits = sum(1 for pat in self._c_family_markers if pat.search(code))
        
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

    # Retirer underscores début/fin
    name = name.strip('_')

    return name


class RosettaScraper:
    
    def __init__(self, output_dir: str = "dataset", delay: float = 0.5, strict_validation: bool = True):

        self.base_dir = Path(output_dir)
        self.rosetta_dir = self.base_dir / "rosetta_code"
        self.delay = delay
        self.validator = CodeValidator(strict_mode=strict_validation) 
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "RosettaCode-Dataset-Builder/1.0"
        })
        
        self.lang_dirs = {

            "C": "C",
            "C++": "Cpp"
        }
        
        self.stats = {

            "tasks_processed": 0,
            "tasks_saved": 0,
            "implementations": {"C": 0, "Cpp": 0},
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

        codes = {}
        target_langs = {"C", "C++"}
        
        # Trouver headers
        header_pattern = r'==\s*\{\{header\|([^}]+)\}\}\s*=='
        headers = []
        
        for match in re.finditer(header_pattern, wikitext, re.IGNORECASE):
            lang = match.group(1).strip()

            if lang in target_langs:
                headers.append((match.start(), match.end(), lang))
        
        # Extraire code par section
        for idx, (start, end, lang) in enumerate(headers):

            if idx + 1 < len(headers):
                section_end = headers[idx + 1][0]

            else:
                next_h = re.search(r'==\s*\{\{header\|', wikitext[end:])
                section_end = end + next_h.start() if next_h else len(wikitext)
            
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
                    
                    # Filtrer C#
                    if self.is_csharp_code(code):
                        self.stats["rejections"]["csharp"] = \
                            self.stats["rejections"].get("csharp", 0) + 1
                        continue
                    
                    # Validation
                    is_valid, reason = self.validator.validate(code, lang)
                    if not is_valid:
                        self.stats["rejections"][reason] = \
                            self.stats["rejections"].get(reason, 0) + 1
                        continue
                    
                    # Code valide
                    if lang not in codes:
                        codes[lang] = []
                    codes[lang].append(code)
        
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
            ext = ".c" if lang == "C" else ".cpp"
            
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
        
        Args: limit: Nombre max de tâches, min_languages: Minimum de langages requis (1 ou 2), filter_keyword: Filtrer par mot-clé, verbose: Affichage détaillé

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
            "structure": "dataset/rosetta_code/task/C/impl_XX.c",
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
        default="dataset",
        help="Dossier racine (default: dataset)"
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
        help="Langages minimum (1=C ou C++, 2=C et C++)"
    )
    parser.add_argument(
        "-d", "--delay",
        type=float,
        default=0.5,
        help="Délai entre requêtes (secondes)"
    )
    parser.add_argument(
        "-f", "--filter",
        type=str,
        default=None,
        help="Filtrer par mot-clé (ex: 'sort')"
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