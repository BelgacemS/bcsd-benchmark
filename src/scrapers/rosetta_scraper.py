"""Scraper RosettaCode"""
import re
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import requests
from tqdm import tqdm
from constants import LANG_DIRS, EXT_MAP



API_URL = "https://rosettacode.org/w/api.php"

class CodeValidator:
    """Filtre les blocs de code invalides recup depuis RosettaCode"""

    def __init__(self):
        self.min_chars = 80
        self.min_lines = 5

        self._wiki_patterns = [
            re.compile(r"\{\{\s*header\s*\|", re.IGNORECASE), # pattern pour détecter le header de la section
            re.compile(r"\{\{\s*lang\s*\|", re.IGNORECASE), # pattern pour détecter le langage de la section
            re.compile(r"\[\[\s*Category:", re.IGNORECASE),
            re.compile(r"<ref\b", re.IGNORECASE), 
            re.compile(r"</ref>", re.IGNORECASE),
        ]

        # Patterns pour detecter du code qui n'est pas C/C++/Rust/Go
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

            # Lisp / Scheme (assez frequent sur RosettaCode)
            re.compile(r"^\s*\(defun\b", re.MULTILINE),
            re.compile(r"^\s*\(define\b", re.MULTILINE),

            # Perl
            re.compile(r"^\s*use\s+strict\b", re.MULTILINE),
            re.compile(r"\bmy\s+\$\w+", re.MULTILINE),
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

    def validate(self, code: str, lang: str) -> tuple[bool, str]:
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

        if not self.looks_like_target_lang(stripped, lang):
            return False, "pas_du_code"

        return True, "ok"

    def _strip_comments(self, code: str) -> str:
        code = re.sub(r"//.*", "", code)
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL) 

        return code

    def count_lines(self, code):

        return sum(1 for line in code.splitlines() if line.strip())

    def has_wiki_markup(self, code: str) -> bool:
        return any(pat.search(code) for pat in self._wiki_patterns)

    def looks_like_other_language(self, code: str) -> bool:
        hits = sum(1 for pat in self._non_c_patterns if pat.search(code))
        return hits >= 2

    def looks_like_target_lang(self, code: str, lang: str) -> bool:
        # forme generale + marqueurs du langage
        if lang in ("Go", "Rust"):
            if not re.search(r"[{}]", code):
                return False
        else:
            if not re.search(r"[;{}]", code):
                return False

        if not re.search(r"\w\s*\(", code):
            return False

        markers = self._lang_markers.get(lang, [])
        if markers:
            hits = sum(1 for pat in markers if pat.search(code))
            # 2 marqueurs min pour eviter les faux positifs
            if hits < 2:
                return False

        return True


def task_name_to_snake_case(task_name: str) -> str:
    # 'Binary search' -> 'binary_search'
    name = re.sub(r'[^\w\s]', '_', task_name)
    name = re.sub(r'\s+', '_', name)
    name = name.lower()
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return name


class RosettaScraper:
    
    def __init__(self, output_dir="data/sample", delay=0.5):

        self.base_dir = Path(output_dir)
        self.rosetta_dir = self.base_dir / "rosetta_code"
        self.delay = delay
        self.validator = CodeValidator()
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "RosettaCode_1.0"
        })
        
        self.lang_dirs = LANG_DIRS
        
        self.stats = {
            "tasks_processed": 0,
            "tasks_saved": 0,
            "implementations": {"C": 0, "Cpp": 0, "Rust": 0, "Go": 0},
            "rejections": {},
        }
    
    def api_request(self, params: dict) -> dict:
        params["format"] = "json"
        time.sleep(self.delay)
        
        try:
            response = self.session.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            
            print(f"Erreur API: {e}")

            return {}
    
    def _has_main_function(self, code, lang):

        if lang in ("C", "C++"):
            return bool(re.search(r'\b(int|void)\s+main\s*\(', code))
        elif lang == "Go":
            return bool(re.search(r'\bfunc\s+main\s*\(', code))
        elif lang == "Rust":
            return bool(re.search(r'\bfn\s+main\s*\(', code))
        return False

    def _merge_fragments(self, blocks: list, lang: str) -> list:
        """Fusionne les blocs lib + main en un seul fichier

        Sur RosettaCode certaines tasks ont plusieurs blocs de code : des blocs bibliotheque (sans main) + un ou plusieurs blocs "main"
        On fusionne les libs avec le premier main uniquement
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
        # y'a du C# qui se glisse dans les sections C/C++ sur rosettacode

        patterns = [
            r'using\s+System\b', r'Console\.Write', r'\.ToArray\s*\(',
            r'foreach\s*\(', r'\bList<', r'\bDictionary<',
        ]

        return sum(1 for p in patterns if re.search(p, code)) >= 2
    
    def get_all_tasks(self, filter_keyword=None) -> list:
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
    
    def get_task_contenu(self, task_name: str) -> str | None:
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
    
    def parse_blocs_code(self, wikitext: str) -> dict:
        """Parse le wikitext d'une page RosettaCode et extrait le code par langage"""
        raw_codes = {}
        target_langs = {"C", "C++", "Rust", "Go"}
        
        # Trouver tous les headers (toutes langues confondues)
        # Pattern qui détecte aussi les headers combinés comme =={{header|Icon}} and {{header|Unicon}}==

        header_pattern = r'==\s*\{\{header\|([^}]+)\}\}'
        all_headers = []
        
        for match in re.finditer(header_pattern, wikitext, re.IGNORECASE):
            lang = match.group(1).strip()
            all_headers.append((match.start(), match.end(), lang))
        
        # On garde que les headers des langages cibles pour l'extraction
        target_headers = [(s, e, l) for s, e, l in all_headers if l in target_langs]
        
        # Extraire le code par section (délimitée par le prochain header de n'importe quel langage)
        for start, end, lang in target_headers:

            # Trouve le prochain header (de n'importe quel langage) après celui-ci
            section_end = len(wikitext)
            for ah_start, _, _ in all_headers:
                if ah_start > start:
                    section_end = ah_start
                    break
            
            section = wikitext[end:section_end]

            # d'autres formats wiki existent surement (mais là ca march plutot bien)
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
    
    def extract_description(self, wikitext: str) -> str:
        # tout ce qui est avant le premier header = description de la task

        header_pattern = r'==\s*\{\{header\|'
        match = re.search(header_pattern, wikitext, re.IGNORECASE)

        if match:
            raw_desc = wikitext[:match.start()]
        else:
            raw_desc = wikitext

        # Nettoyage basique du wikitext
        desc = raw_desc.strip()
        desc = re.sub(r'<ref[^>]*>.*?</ref>', '', desc, flags=re.DOTALL)
        desc = re.sub(r'\{\{[^}]*\}\}', '', desc)
        desc = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]*)\]\]', r'\1', desc)
        desc = re.sub(r"'''?", '', desc)
        desc = re.sub(r'</?[a-zA-Z][^>]*>', '', desc)
        desc = re.sub(r'\n{3,}', '\n\n', desc)

        return desc.strip()

    def save_task(self, task_name: str, codes: dict, description="") -> bool:
        if not codes:
            return False
        
        safe_name = task_name_to_snake_case(task_name)
        task_dir = self.rosetta_dir / safe_name
        
        for lang, implementations in codes.items():
            lang_dir_name = self.lang_dirs[lang] 
            lang_dir = task_dir / lang_dir_name
            lang_dir.mkdir(parents=True, exist_ok=True)
            
            ext = EXT_MAP.get(lang, ".txt")
            
            for i, code in enumerate(implementations, start=1):
                filename = f"impl_{i:02d}{ext}"  # impl_01.c, impl_02.c, ...
                filepath = lang_dir / filename
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(code)
                
                self.stats["implementations"][lang_dir_name] = \
                    self.stats["implementations"].get(lang_dir_name, 0) + 1

        if description:
            task_dir.mkdir(parents=True, exist_ok=True)
            desc_path = task_dir / "task_description.md"
            with open(desc_path, "w", encoding="utf-8") as f:
                f.write(f"# {task_name}\n\n{description}\n")
        
        return True
    
    def scrape(self, limit=None, min_languages=1, filter_keyword=None, verbose=False):
        self.rosetta_dir.mkdir(parents=True, exist_ok=True)

        tasks = self.get_all_tasks(filter_keyword=filter_keyword)
        if limit:
            tasks = tasks[:limit]
        
        print(f"Scraping de {len(tasks)} tâches RosettaCode")
        print("\n")

        for task_name in tqdm(tasks, desc="Progression"):
            self.stats["tasks_processed"] += 1
            
            content = self.get_task_contenu(task_name)
            if not content:
                continue
            
            codes = self.parse_blocs_code(content)
            description = self.extract_description(content)
            
            if len(codes) >= min_languages:
                if self.save_task(task_name, codes, description):
                    self.stats["tasks_saved"] += 1
                    
                    if verbose:
                        safe_name = task_name_to_snake_case(task_name)
                        langs = ", ".join(codes.keys())
                        
                        print(f"{safe_name}: [{langs}]")
        
        self.print_stats()
        self.save_metadata()
    
    def print_stats(self):

        print("\n")
        print(f"Scraping terminé")
        print("\n")

        print(f"Tâches analysées: {self.stats['tasks_processed']}")
        print(f"Tâches sauvegardées: {self.stats['tasks_saved']}")
        print(f"\n Implémentations par langage:")

        for lang, count in self.stats["implementations"].items():
            print(f" {lang:5s}: {count:4d} fichiers")
        
        if self.stats["rejections"]:
            print(f"\nRejets:")

            top_rejections = sorted(self.stats["rejections"].items(), key=lambda x: -x[1])[:5]

            for reason, count in top_rejections:
                print(f"{reason:30s}: {count:4d}")
        
    
    def save_metadata(self):

        metadata = {
            "source": "rosetta_code",
            "scrape_date": datetime.now().isoformat(),
            "total_tasks": self.stats["tasks_saved"],
            "implementations": self.stats["implementations"],
            "structure": "<output_dir>/rosetta_code/<task>/<C|Cpp|Rust|Go>/impl_XX.<ext>",
        }
        
        metadata_file = self.base_dir / "rosetta_code_metadata.json"

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        


def main():
    
    parser = argparse.ArgumentParser(description="Scraper RosettaCode")
    
    parser.add_argument("-o", "--output", default="data/sample", help="Dossier de sortie")
    parser.add_argument("-l", "--limit", type=int, default=None, help="Nombre max de taches")
    parser.add_argument("-m", "--min-languages", type=int, default=1, help="Langages minimum par tache")
    parser.add_argument("-d", "--delay", type=float, default=0.5, help="Delai entre requetes (en secondes)")
    parser.add_argument("-f", "--filter", type=str, default=None, help="Filtrer par mot-cle")
    parser.add_argument("-v", "--verbose", action="store_true", help="Affichage detaille")
    
    args = parser.parse_args()
    
    scraper = RosettaScraper(args.output, args.delay)
    scraper.scrape(args.limit, args.min_languages, args.filter, args.verbose)


if __name__ == "__main__":
    main()