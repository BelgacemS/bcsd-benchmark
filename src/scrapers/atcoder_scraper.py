# Scraper AtCoder - recup les soumissions AC des contests ABC

import re
import requests
import time
import os
import json
import argparse
import urllib.parse
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from constants import LANG_MAP

load_dotenv()

BASE_URL = "https://atcoder.jp"

DELAY_BETWEEN_PAGES = 0.5
DELAY_BETWEEN_DOWNLOADS = 1
MAX_PAGINATION_PAGES = 10


def resolve_problem_id(session, contest: str, problem_char: str) -> str | None:
    # le problem_id peut etre une lettre ou un numero selon le contest
    
    if not problem_char.isalpha():
        return None

    # lettre d'abord
    problem_id = f"{contest}_{problem_char}"

    url = f"{BASE_URL}/contests/{contest}/tasks/{problem_id}"
    try:
        resp = session.get(url)
        if resp.status_code == 200:
            return problem_id
        
    except requests.RequestException:
        pass

    # sinon numero
    num = ord(problem_char) - ord('a') + 1
    problem_id = f"{contest}_{num}"
    url = f"{BASE_URL}/contests/{contest}/tasks/{problem_id}"

    try:
        resp = session.get(url)
        if resp.status_code == 200:
            return problem_id
    except requests.RequestException:
        pass

    return None


def get_problem_info(session, contest: str, problem_id: str):

    url = f"{BASE_URL}/contests/{contest}/tasks/{problem_id}"
    title = None
    description = None

    try:
        resp = session.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        title_tag = soup.find("span", class_="h2")

        if title_tag:
            full_title = title_tag.find(string=True, recursive=False)
            if full_title:
                full_title = full_title.strip()
            else:
                full_title = title_tag.get_text().split("\n")[0].strip()
            if " - " in full_title:
                title = full_title.split(" - ", 1)[1].strip()
            else:
                title = full_title.strip()

        # version anglaise si dispo
        task_stmt = soup.find("div", id="task-statement")

        if task_stmt:
            lang_en = task_stmt.find("span", class_="lang-en")
            section = lang_en if lang_en else task_stmt
            raw = section.get_text(separator="\n").strip()

            description = re.sub(r'\n{3,}', '\n\n', raw)

    except Exception as e:
        print(f"Erreur recup probleme : {e}")

    return title, description


def lang_matches(language_name: str, lang_text: str) -> bool:
    # AtCoder affiche les langages avec des noms du genre "C (GCC 9.2.1)" ou "C++ (GCC 9.2.1)" donc faut faire du matching approximatif

    if language_name == "C++" and "C++" in lang_text:
        return True

    elif language_name == "C":
        stripped = lang_text.strip()
        if stripped.startswith("C ") or stripped.startswith("C(") or stripped == "C":
            return True

    elif language_name == "Rust" and lang_text.startswith("Rust"):
        return True

    elif language_name == "Go" and lang_text.startswith("Go"):
        return True

    return False


def get_submission_urls(session, contest: str, problem_id: str, language_name: str, count=3) -> list:
    """Recup les urls de soumissions AC en prenant des utilisateurs differents"""

    urls = []
    seen_users = set()
    page = 1

    lang_filter = urllib.parse.quote(language_name)

    while len(urls) < count and page <= MAX_PAGINATION_PAGES:
        list_url = (f"{BASE_URL}/contests/{contest}/submissions"
                    f"?f.Task={problem_id}&f.Status=AC"
                    f"&f.LanguageName={lang_filter}&page={page}")

        try:
            resp = session.get(list_url)

            if "Sign In" in resp.text or "login" in resp.url:
                print("  Erreur connexion, verifier REVEL_SESSION")
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
                    user_link = cols[2].find("a")
                    username = user_link.text.strip() if user_link else ""

                    if username in seen_users:
                        continue

                    detail_link = row.find("a", href=True, string="Detail")

                    if detail_link:
                        urls.append(BASE_URL + detail_link['href'])
                        seen_users.add(username)
                        found_any_on_page = True

                        if len(urls) >= count:
                            break

            pager = soup.find("ul", class_="pager")
            has_next = pager and pager.find("a", string="Next >")

            if not has_next or not found_any_on_page:
                break

            page += 1
            time.sleep(DELAY_BETWEEN_PAGES)

        except Exception as e:
            
            print(f"  Erreur page {page} : {e}")
            break

    return urls


def download_code(session, submission_url: str, save_path: str) -> bool:

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
            print(f"    Code introuvable : {submission_url}")
    except Exception as e:
        print(f"  Erreur telechargement : {e}")

    return False


def scrape_contest(session, contest, atcoder_dir, target_langs, problems, num_impl, all_stats):

    for prob in problems:
        print(f"  Probleme {prob.upper()}...")

        problem_id = resolve_problem_id(session, contest, prob)

        if not problem_id:
            print(f"    Probleme introuvable, skip")
            continue

        title, description = get_problem_info(session, contest, problem_id)

        if title:
            print(f"    {problem_id} : {title}")
        else:
            print(f"    {problem_id}")

        problem_dir = atcoder_dir / problem_id

        if description:

            problem_dir.mkdir(parents=True, exist_ok=True)
            desc_path = problem_dir / "task_description.md"
            with open(desc_path, "w", encoding="utf-8") as f:
                f.write(f"# {title or problem_id}\n\n{description}\n")

        task_key = f"{contest}/{problem_id}"
        all_stats[task_key] = {}

        for lang in target_langs:
            lang_info = LANG_MAP.get(lang, {"folder": lang, "ext": ".txt"})
            lang_folder = lang_info["folder"]
            ext = lang_info["ext"]
            lang_dir = problem_dir / lang_folder

            sub_urls = get_submission_urls(session, contest, problem_id, lang, count=num_impl)

            if not sub_urls:
                all_stats[task_key][lang_folder] = 0
                continue

            downloaded = 0
            
            for i, url in enumerate(sub_urls, start=1):
                filename = f"impl_{i:02d}{ext}"
                save_path = str(lang_dir / filename)

                success = download_code(session, url, save_path)
                if success:
                    downloaded += 1

                time.sleep(DELAY_BETWEEN_DOWNLOADS)

            all_stats[task_key][lang_folder] = downloaded
            print(f"    [{lang}] {downloaded}/{num_impl}")


def main():
    parser = argparse.ArgumentParser(
        description="Scraper AtCoder (ABC contests)")

    parser.add_argument("-o", "--output", default=os.getenv("OUTPUT_DIR", "data/sample"), help="Dossier de sortie")
    parser.add_argument("--contest-start", type=int, default=int(os.getenv("CONTEST_START", "100")), help="Numero du premier contest ABC")
    parser.add_argument("--contest-end", type=int, default=int(os.getenv("CONTEST_END", "445")), help="Numero du dernier contest ABC")
    parser.add_argument("--problems", default=os.getenv("PROBLEMS", "a,b,c,d"), help="Lettres des problemes (virgules)")
    parser.add_argument("--langs", default=os.getenv("TARGET_LANGS", "C++,C,Rust,Go"), help="Langages cibles (virgules)")
    parser.add_argument("--num-impl", type=int, default=int(os.getenv("NUM_IMPLEMENTATIONS", "3")), help="Nombre d'implementations par langage")

    args = parser.parse_args()

    revel_session = os.getenv("REVEL_SESSION")
    
    if not revel_session:
        print("Erreur : REVEL_SESSION pas dans .env (cookie necessaire pour AtCoder)")
        return

    base_dir = Path(args.output)
    atcoder_dir = base_dir / "atcoder"
    atcoder_dir.mkdir(parents=True, exist_ok=True)

    target_langs = [l.strip() for l in args.langs.split(",")]
    problems = [p.strip() for p in args.problems.split(",")]
    contest_start = args.contest_start
    contest_end = args.contest_end
    num_impl = args.num_impl

    session = requests.Session()
    session.cookies.set("REVEL_SESSION", revel_session, domain="atcoder.jp")
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" # pour imiter un navigateur 
    })

    total_contests = contest_end - contest_start + 1
    print(f"Scraping des contests ABC {contest_start} a {contest_end} ({total_contests} contests)")
    print(f"{num_impl} implementations par langage.")
    print(f"Sortie : {atcoder_dir}\n")

    all_stats = {}

    for contest_num in range(contest_start, contest_end + 1):
        contest = f"abc{contest_num:03d}"
        print(f"\n{'='*60}")
        print(f"Contest {contest} ({contest_num - contest_start + 1}/{total_contests})")
        print(f"{'='*60}")

        try:
            scrape_contest(session, contest, atcoder_dir, target_langs, problems, num_impl, all_stats)
        except Exception as e:
            print(f"  ERREUR sur {contest} : {e}")
            continue

    metadata = {
        
        "source": "atcoder",
        "contests": f"abc{contest_start:03d}-abc{contest_end:03d}",
        "scrape_date": datetime.now().isoformat(),
        "total_contests": total_contests,
        "total_tasks": len(all_stats),
        "implementations": {},
        "tasks": all_stats,
    }

    for lang in target_langs:
        lang_folder = LANG_MAP.get(lang, {"folder": lang})["folder"]
        total = sum(task.get(lang_folder, 0) for task in all_stats.values())
        metadata["implementations"][lang_folder] = total

    metadata_path = base_dir / "atcoder_metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nMetadonnees ecrites dans {metadata_path}")
    print(f"Termine ! {len(all_stats)} problemes scrapes sur {total_contests} contests.")


if __name__ == "__main__":
    main()
