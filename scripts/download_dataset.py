#!/usr/bin/env python3
# Telecharge et decompresse le dataset BCSD depuis le Hugging Face Hub.
#
#   https://huggingface.co/datasets/BelgacemS/bcsd-benchmark
#
# Pour juste lancer le benchmark, seul "embeddings" est necessaire :
#
#   python3 scripts/download_dataset.py            # -> embeddings (defaut)
#   python3 scripts/download_dataset.py embeddings
#   python3 scripts/download_dataset.py disasm sources
#   python3 scripts/download_dataset.py all
#
# Chaque archive .tar.zst est extraite sous data/ :
#   embeddings.tar.zst  -> data/embeddings/   (index.json + vecteurs .npy)
#   disasm.tar.zst      -> data/disasm/
#   sources.tar.zst     -> data/sources/
#   binaries.tar.zst    -> data/binaries/     (~1 Go compresse, ~2 Go extrait)

import argparse
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ID = "BelgacemS/bcsd-benchmark"

# nom logique -> archive sur le Hub
ARCHIVES = {
    "embeddings": "embeddings.tar.zst",
    "disasm": "disasm.tar.zst",
    "sources": "sources.tar.zst",
    "binaries": "binaries.tar.zst",
    "disasm_jtrans": "disasm_jtrans.tar.zst",
}

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = DATA_DIR / "_hf_cache"


def human(n):
    for unit in ["o", "Ko", "Mo", "Go"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} To"


def download(archive):
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        print("Erreur: huggingface_hub manquant. Installe-le :")
        print("  pip install -r requirements.txt   (ou: pip install huggingface_hub)")
        sys.exit(1)

    print(f"[download] {archive} depuis {REPO_ID} ...")
    return Path(hf_hub_download(
        repo_id=REPO_ID,
        filename=archive,
        repo_type="dataset",
        local_dir=str(CACHE_DIR),
    ))


def verify(archive_path):
    # Verifie l'integrite du flux zstd avant extraction. Certaines archives
    # publiees sur le Hub sont corrompues (bloc invalide) : on prefere le
    # signaler clairement plutot que d'extraire des donnees partielles.
    if not _has_zstd_bin():
        return True  # pas de binaire zstd : on tente l'extraction directement
    res = subprocess.run(["zstd", "-t", str(archive_path)],
                         capture_output=True, text=True)
    return res.returncode == 0


def extract(archive_path):
    # Extraction zstd -> tar, en streaming pour ne pas tout charger en RAM.
    # On utilise le binaire `zstd` s'il est dispo (rapide), sinon le module
    # python `zstandard`.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[extract] {archive_path.name} -> {DATA_DIR}/ ...")

    if _has_zstd_bin():
        proc = subprocess.Popen(
            ["zstd", "-dc", str(archive_path)], stdout=subprocess.PIPE)
        with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
            tar.extractall(DATA_DIR)
        proc.stdout.close()
        proc.wait()
        if proc.returncode != 0:
            raise RuntimeError("zstd a echoue (archive corrompue ?)")
    else:
        try:
            import zstandard
        except ImportError:
            print("Erreur: ni le binaire `zstd` ni le module python `zstandard`.")
            print("  Installe l'un des deux :  sudo apt install zstd   (ou)  pip install zstandard")
            sys.exit(1)
        dctx = zstandard.ZstdDecompressor()
        with open(archive_path, "rb") as fh, dctx.stream_reader(fh) as reader:
            with tarfile.open(fileobj=reader, mode="r|") as tar:
                tar.extractall(DATA_DIR)


def _has_zstd_bin():
    from shutil import which
    return which("zstd") is not None


def main():
    parser = argparse.ArgumentParser(
        description="Telecharge le dataset BCSD depuis Hugging Face.")
    parser.add_argument("parts", nargs="*", default=["embeddings"],
                        help="parties a recuperer: "
                             + ", ".join(ARCHIVES) + ", all (defaut: embeddings)")
    parser.add_argument("--keep-archive", action="store_true",
                        help="ne pas supprimer le .tar.zst apres extraction")
    args = parser.parse_args()

    parts = args.parts or ["embeddings"]
    if "all" in parts:
        parts = list(ARCHIVES)

    unknown = [p for p in parts if p not in ARCHIVES]
    if unknown:
        print(f"Inconnu: {unknown}. Choix valides: {', '.join(ARCHIVES)}, all")
        sys.exit(1)

    failed = []
    for part in parts:
        archive = ARCHIVES[part]
        path = download(archive)
        print(f"  -> {path} ({human(path.stat().st_size)})")

        if not verify(path):
            print(f"[!] {archive} est corrompue cote Hub (flux zstd invalide), "
                  f"partie '{part}' ignoree.")
            path.unlink(missing_ok=True)
            failed.append(part)
            continue

        try:
            extract(path)
        except (RuntimeError, tarfile.TarError, OSError) as e:
            print(f"[!] extraction de {archive} echouee ({e}), partie '{part}' ignoree.")
            failed.append(part)
            continue
        finally:
            if not args.keep_archive:
                path.unlink(missing_ok=True)
        print(f"[ok] {part} pret sous data/{part}/\n")

    if failed:
        print(f"\nParties non recuperees: {', '.join(failed)}")
    if "embeddings" not in failed and "embeddings" in parts:
        print("\nEmbeddings prets. Pour lancer le benchmark :")
        print("  python3 src/benchmark.py")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
