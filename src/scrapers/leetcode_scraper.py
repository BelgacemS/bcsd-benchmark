# Scraper LeetCode — recup les solutions C/C++/Rust/Go depuis doocs/leetcode

import re
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import requests
from tqdm import tqdm


GITHUB_API = "https://api.github.com"
REPO = "doocs/leetcode"
RAW_BASE = f"https://raw.githubusercontent.com/{REPO}/main"

# Fichiers qu'on cherche et leur correspondance langage
TARGET_FILES = {
    "Solution.c":   ("C",    ".c"),
    "Solution.cpp": ("Cpp",  ".cpp"),
    "Solution.go":  ("Go",   ".go"),
    "Solution.rs":  ("Rust", ".rs"),
}

# lang -> extension, derive de TARGET_FILES
LANG_EXT = {lang: ext for _, (lang, ext) in TARGET_FILES.items()}


def normalize_task_name(raw_name: str) -> str:
    
    # snake_case
    name = raw_name.strip()
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = re.sub(r"_+", "_", name)

    return name.strip("_").lower()


class LeetcodeScraper:

    def __init__(self, output_dir="data/sample", delay=0.05):
        self.base_dir = Path(output_dir)
        self.leetcode_dir = self.base_dir / "leetcode"
        self.delay = delay

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BCSD-Benchmark-Scraper/1.0",
            "Accept": "application/vnd.github.v3+json",
        })

        self.stats = {
            "tasks_processed": 0,
            "tasks_saved": 0,
            "implementations": {"C": 0, "Cpp": 0, "Rust": 0, "Go": 0},
        }

    def get_repo_tree(self) -> list:

        url = f"{GITHUB_API}/repos/{REPO}/git/trees/main?recursive=1"
        print("Recuperation de l'arborescence du repo")

        resp = self.session.get(url, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if data.get("truncated"):
            print("Attention : l'arbre est tronque, certains fichiers peuvent manquer")

        return data.get("tree", [])

    def find_solutions(self, tree: list) -> dict:
        """ Regroupe les Solution.* par tache.
        Parcourt solution/ et lcci/ dans l'arbre git. _readme pointe vers le README_EN.md si dispo """

        # à faire : Si pas de README en anglais pas dispo, on pourrai recup celui en japonais
        tasks = {}

        for entry in tree:
            if entry["type"] != "blob":
                continue

            path = entry["path"]
            filename = path.split("/")[-1]

            # solution/XXXX-XXXX/<problem>/...
            if path.startswith("solution/"):
                parts = path.split("/")
                if len(parts) != 4:
                    continue
                problem_name = parts[2]
                task_name = normalize_task_name(problem_name)

            # lcci/<problem>/...
            # ajouter lcof/lcof2 un jour peut-etre
            elif path.startswith("lcci/"):
                parts = path.split("/")
                if len(parts) != 3:
                    continue
                problem_name = parts[1]
                task_name = normalize_task_name(f"lcci_{problem_name}")
            else:
                continue

            if task_name not in tasks:
                tasks[task_name] = {}

            if filename in TARGET_FILES:
                lang, ext = TARGET_FILES[filename]
                tasks[task_name][lang] = path
            elif filename == "README_EN.md":
                tasks[task_name]["_readme"] = path

        return tasks

    def download_file(self, github_path: str) -> str | None:

        url = f"{RAW_BASE}/{github_path}"
        time.sleep(self.delay)

        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            print(f"Erreur telechargement {github_path}: {e}")
            return None

    def save_task(self, task_name: str, files: dict) -> bool:

        task_dir = self.leetcode_dir / task_name
        saved_any = False

        for lang, github_path in files.items():
            if lang == "_readme":
                continue

            ext = LANG_EXT[lang]
            lang_dir = task_dir / lang
            lang_dir.mkdir(parents=True, exist_ok=True)

            code = self.download_file(github_path)

            if code is None:
                continue

            filepath = lang_dir / f"impl_01{ext}"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)

            self.stats["implementations"][lang] += 1
            saved_any = True

        if "_readme" in files:
            task_dir.mkdir(parents=True, exist_ok=True)
            readme_content = self.download_file(files["_readme"])

            if readme_content:
                description = self._extract_description(readme_content)

                if description:
                    desc_path = task_dir / "task_description.md"
                    with open(desc_path, "w", encoding="utf-8") as f:
                        f.write(description)

        if saved_any:
            self.stats["tasks_saved"] += 1
        return saved_any

    def _extract_description(self, readme_content: str) -> str:
        # extrait la description du README sans les solutions
        
        desc_match = re.search(
            r'<!-- description:start -->(.*?)<!-- description:end -->',
            readme_content, re.DOTALL
        )
        if desc_match:
            description = desc_match.group(1).strip()
        else:

            parts = readme_content.split("## Solutions")
            description = parts[0].strip()

        title_match = re.search(r'^#\s+\[?(.+?)[\]\(]', readme_content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else ""

        result = ""

        if title:
            result += f"# {title}\n\n"
        result += description

        return result

    def scrape(self, limit=None, min_languages=1, verbose=False):

        self.leetcode_dir.mkdir(parents=True, exist_ok=True)

        tree = self.get_repo_tree()
        tasks = self.find_solutions(tree)

        nb_with_langs = sum(1 for f in tasks.values() if any(k != "_readme" for k in f))
        print(f"{nb_with_langs} problemes trouves avec au moins 1 de nos langages")

        filtered = {
            name: files for name, files in tasks.items()
            if sum(1 for k in files if k != "_readme") >= min_languages
        }
        print(f"{len(filtered)} problemes avec >= {min_languages} langages")

        if limit:
            task_list = list(filtered.items())[:limit]
        else:
            task_list = list(filtered.items())

        print(f"Telechargement de {len(task_list)} problemes...")
        print()

        for task_name, files in tqdm(task_list, desc="Progression"):
            self.stats["tasks_processed"] += 1

            self.save_task(task_name, files)

            if verbose:
                langs = ", ".join(k for k in files.keys() if k != "_readme")
                print(f"  {task_name}: [{langs}]")

        self._finish()

    def _finish(self):
        """Affiche les stats et ecrit le fichier metadata"""

        print(f"\n--- Scraping termine ---")
        print(f"Analyses: {self.stats['tasks_processed']}  |  Sauvegardes: {self.stats['tasks_saved']}")

        for lang, count in self.stats["implementations"].items():
            print(f"  {lang}: {count}")

        metadata = {

            "source": "leetcode",
            "repo": f"https://github.com/{REPO}",
            "scrape_date": datetime.now().isoformat(),
            "total_tasks": self.stats["tasks_saved"],
            "implementations": self.stats["implementations"],
        }

        metadata_file = self.base_dir / "leetcode_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"Metadata -> {metadata_file}")


def main():
    
    parser = argparse.ArgumentParser(
        description="Scraper LeetCode (doocs/leetcode GitHub)")

    parser.add_argument("-o", "--output", default="data/sample", help="Dossier de sortie")
    parser.add_argument("-l", "--limit", type=int, default=None, help="Nombre max de problemes")
    parser.add_argument("-m", "--min-languages", type=int, default=1, help="Langages minimum par probleme")
    parser.add_argument("-d", "--delay", type=float, default=0.05, help="Delai entre telechargements (secondes)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Affichage detaille")

    args = parser.parse_args()

    scraper = LeetcodeScraper(args.output, args.delay)
    scraper.scrape(args.limit, args.min_languages, args.verbose)


if __name__ == "__main__":
    main()
