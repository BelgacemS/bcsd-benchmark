""" Scraper AtCoder """

import requests
import time
import os
import json
import urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

CONTEST_START = int(os.getenv("CONTEST_START", "100"))
CONTEST_END = int(os.getenv("CONTEST_END", "445"))
PROBLEMS = os.getenv("PROBLEMS", "a,b,c,d").split(",")
TARGET_LANGS = os.getenv("TARGET_LANGS").split(",")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
NUM_IMPLEMENTATIONS = int(os.getenv("NUM_IMPLEMENTATIONS", "3"))

REVEL_SESSION_VALUE = os.getenv("REVEL_SESSION")

BASE_URL = "https://atcoder.jp"

# Correspondance entre noms de langages et dossiers/extensions
LANG_MAP = {
    "C++": {"folder": "Cpp", "ext": ".cpp"},
    "C":   {"folder": "C",   "ext": ".c"},
    "Rust":{"folder": "Rust","ext": ".rs"},
    "Go":  {"folder": "Go",  "ext": ".go"},
}

# Création d'une session pour conserver le cookie d'authentification
session = requests.Session()
session.cookies.set("REVEL_SESSION", REVEL_SESSION_VALUE, domain="atcoder.jp")

# User-Agent pour éviter d'être bloqué par le serveur
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})


def get_problem_name(contest, problem_char):
    """Récupère le titre du problème depuis la page de la tâche pour l'utiliser comme nom de dossier."""
    problem_id = f"{contest}_{problem_char}"
    url = f"{BASE_URL}/contests/{contest}/tasks/{problem_id}"
    try:
        resp = session.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        title_tag = soup.find("span", class_="h2")
        if title_tag:
            # Récupérer uniquement le texte direct, pas celui des éléments enfants
            full_title = title_tag.find(string=True, recursive=False)
            if full_title:
                full_title = full_title.strip()
            else:
                full_title = title_tag.get_text().split("\n")[0].strip()
            # Supprimer le préfixe "A - "
            if " - " in full_title:
                name = full_title.split(" - ", 1)[1]
            else:
                name = full_title
            # Assainir le nom pour l'utiliser comme dossier
            name = name.replace(" ", "_").replace("!", "").replace("?", "")
            name = name.replace("'", "").replace('"', "").replace("/", "_")
            name = name.replace("*", "").replace(":", "").replace(",", "")
            return name
    except Exception as e:
        print(f"  Erreur lors de la récupération du nom du problème : {e}")
    # Nom par défaut en cas d'échec
    return f"{contest}_{problem_char}"


def lang_matches(language_name, lang_text):
    """Vérifie si le texte de la colonne langage correspond au langage cible."""
    if language_name == "C++" and "C++" in lang_text:
        return True
    elif language_name == "C":
        # Doit commencer par "C " ou "C(" pour éviter C++, C#, Cython, etc.
        stripped = lang_text.strip()
        if stripped.startswith("C ") or stripped.startswith("C(") or stripped == "C":
            return True
    elif language_name == "Rust" and lang_text.startswith("Rust"):
        return True
    elif language_name == "Go" and lang_text.startswith("Go"):
        return True
    return False


def get_submission_urls(contest, problem_char, language_name, count=3):
    """
    Recherche jusqu'à `count` URLs de soumissions AC pour un langage et un problème donnés,
    provenant d'utilisateurs différents pour obtenir des implémentations diversifiées.
    Utilise le filtre f.LanguageName d'AtCoder pour cibler le bon langage.
    """
    problem_id = f"{contest}_{problem_char}"
    urls = []
    seen_users = set()
    page = 1

    # Paramètre de filtre langage d'AtCoder pour un filtrage précis
    lang_filter = urllib.parse.quote(language_name)

    while len(urls) < count and page <= 10:
        list_url = (f"{BASE_URL}/contests/{contest}/submissions"
                    f"?f.Task={problem_id}&f.Status=AC"
                    f"&f.LanguageName={lang_filter}&page={page}")

        try:
            resp = session.get(list_url)

            if "Sign In" in resp.text or "login" in resp.url:
                print("  ERREUR : Connexion échouée. Vérifiez votre cookie REVEL_SESSION.")
                return urls

            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            table = soup.find("table", class_="table")
            if not table:
                break

            tbody = table.find("tbody")
            if not tbody:
                break

            rows = tbody.find_all("tr")
            if not rows:
                break

            found_any_on_page = False
            for row in rows:
                cols = row.find_all("td")
                if not cols:
                    continue

                lang_text = cols[3].text.strip()

                if lang_matches(language_name, lang_text):
                    # Récupérer le nom d'utilisateur (colonne index 2)
                    user_link = cols[2].find("a")
                    username = user_link.text.strip() if user_link else ""

                    # Ignorer si on a déjà une soumission de cet utilisateur
                    if username in seen_users:
                        continue

                    detail_link = row.find("a", href=True, string="Detail")
                    if detail_link:
                        urls.append(BASE_URL + detail_link['href'])
                        seen_users.add(username)
                        found_any_on_page = True

                        if len(urls) >= count:
                            break

            # Vérifier s'il y a une page suivante
            pager = soup.find("ul", class_="pager")
            has_next = pager and pager.find("a", string="Next >") if pager else False
            if not has_next or not found_any_on_page:
                break

            page += 1
            time.sleep(1)  # Délai de politesse entre les pages

        except Exception as e:
            print(f"  Erreur lors de la recherche page {page} : {e}")
            break

    return urls


def download_code(submission_url, save_path):
    """Télécharge le code source depuis la page de soumission."""
    try:
        resp = session.get(submission_url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        code_block = soup.find("pre", id="submission-code")

        if code_block:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(code_block.text)
            return True
        else:
            print(f"    Bloc de code introuvable sur {submission_url}")
    except Exception as e:
        print(f"  Erreur lors du téléchargement du code : {e}")
    return False


def scrape_contest(contest, all_stats):
    """Scrape tous les problèmes d'un contest donné."""
    contest_dir = OUTPUT_DIR

    for prob in PROBLEMS:
        print(f"  Problème {prob.upper()}...")

        # Récupérer le nom du problème pour le dossier
        problem_name = get_problem_name(contest, prob)
        if not problem_name:
            print(f"    Impossible de récupérer le nom du problème, ignoré.")
            continue
        print(f"    Nom : {problem_name}")
        problem_dir = os.path.join(contest_dir, problem_name)

        task_key = f"{contest}/{problem_name}"
        all_stats[task_key] = {}

        for lang in TARGET_LANGS:
            lang_info = LANG_MAP.get(lang, {"folder": lang, "ext": ".txt"})
            lang_folder = lang_info["folder"]
            ext = lang_info["ext"]
            lang_dir = os.path.join(problem_dir, lang_folder)

            sub_urls = get_submission_urls(contest, prob, lang, count=NUM_IMPLEMENTATIONS)

            if not sub_urls:
                all_stats[task_key][lang_folder] = 0
                continue

            downloaded = 0
            for i, url in enumerate(sub_urls, start=1):
                filename = f"impl_{i:02d}{ext}"
                save_path = os.path.join(lang_dir, filename)

                success = download_code(url, save_path)
                if success:
                    downloaded += 1

                time.sleep(2)  # Délai de politesse

            all_stats[task_key][lang_folder] = downloaded
            print(f"    [{lang}] {downloaded}/{NUM_IMPLEMENTATIONS}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    total_contests = CONTEST_END - CONTEST_START + 1
    print(f"Scraping des contests ABC {CONTEST_START} à {CONTEST_END} ({total_contests} contests)")
    print(f"{NUM_IMPLEMENTATIONS} implémentations par langage.")
    print(f"Sortie : {OUTPUT_DIR}\n")

    # Suivi des statistiques pour les métadonnées
    all_stats = {}

    for contest_num in range(CONTEST_START, CONTEST_END + 1):
        contest = f"abc{contest_num}"
        print(f"\n{'='*60}")
        print(f"Contest {contest} ({contest_num - CONTEST_START + 1}/{total_contests})")
        print(f"{'='*60}")

        try:
            scrape_contest(contest, all_stats)
        except Exception as e:
            print(f"  ERREUR sur {contest} : {e}")
            continue

    # Écriture du fichier de métadonnées
    metadata = {
        "source": "atcoder",
        "contests": f"abc{CONTEST_START}-abc{CONTEST_END}",
        "scrape_date": datetime.now().isoformat(),
        "total_contests": total_contests,
        "total_tasks": len(all_stats),
        "implementations": {},
        "tasks": all_stats,
    }
    # Agrégation du nombre total d'implémentations par langage
    for lang in TARGET_LANGS:
        lang_folder = LANG_MAP.get(lang, {"folder": lang})["folder"]
        total = sum(task.get(lang_folder, 0) for task in all_stats.values())
        metadata["implementations"][lang_folder] = total

    metadata_path = os.path.join(OUTPUT_DIR, "atcoder_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nMétadonnées écrites dans {metadata_path}")
    print(f"Terminé ! {len(all_stats)} problèmes scrapés sur {total_contests} contests.")


if __name__ == "__main__":
    main()