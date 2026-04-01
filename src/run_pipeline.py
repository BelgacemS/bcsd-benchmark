import argparse
import subprocess
import shutil
import time
import sys
import os

import yaml


def load_config(path="config.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


# on definit les etapes dans l'ordre de la pipeline
STEPS = ["compile", "disasm", "embed", "benchmark"]

# les scripts python de chaque etape
SCRIPTS = {
    "compile": "src/compile.py",
    "disasm": "src/disasm.py",
    "embed": "src/embed_palmtree.py",
    "benchmark": "src/benchmark.py",
}


def check_gsutil():
    # on verifie que gsutil est dispo
    if not shutil.which("gsutil"):
        print("[ERREUR] gsutil pas installe ou pas dans le PATH")
        sys.exit(1)
    print("[OK] gsutil trouve")


def check_bucket(bucket):
    # on teste l'acces au bucket
    ret = subprocess.run(["gsutil", "ls", bucket], capture_output=True, text=True)
    if ret.returncode != 0:
        print(f"[ERREUR] bucket inaccessible : {bucket}")
        print(f"  {ret.stderr.strip()}")
        sys.exit(1)
    print(f"[OK] bucket accessible : {bucket}")


def check_scripts(active_steps):
    # on verifie que les scripts des etapes demandees existent
    for step in active_steps:
        script = SCRIPTS[step]
        if not os.path.isfile(script):
            print(f"[ERREUR] script manquant : {script} (etape {step})")
            sys.exit(1)
    print(f"[OK] scripts presents pour : {', '.join(active_steps)}")


def run_gsutil(cmd, dry_run=False):
    # lance une commande gsutil, ou l'affiche si dry run
    cmd_str = " ".join(cmd)
    if dry_run:
        print(f"  [DRY-RUN] {cmd_str}")
        return 0, 0.0

    t0 = time.time()
    ret = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = time.time() - t0

    if ret.returncode != 0:
        print(f"  [ERREUR] {cmd_str}")
        print(f"  {ret.stderr.strip()}")
    else:
        print(f"  [OK] ({elapsed:.1f}s)")

    return ret.returncode, elapsed


def do_pull(step, bucket, gcp_paths, local_paths, dry_run):
    # on pull les donnees necessaires avant chaque etape
    # chaque etape a besoin des outputs de l'etape precedente
    pull_map = {
        "compile": [
            ("rsync", gcp_paths["sources"], local_paths["sources"]),
        ],
        "disasm": [
            ("rsync", gcp_paths["binaries"], local_paths["binaries"]),
            ("cp", "compile_manifest.json", "data/compile_manifest.json"),
        ],
        "embed": [
            ("rsync", gcp_paths["disasm"], local_paths["disasm"]),
        ],
        "benchmark": [
            ("rsync", gcp_paths["embeddings"], local_paths["embeddings"]),
        ],
    }

    total = 0.0
    for op in pull_map.get(step, []):
        if op[0] == "rsync":
            _, gcp_dir, local_dir = op
            src = f"{bucket}/{gcp_dir}/"
            dst = f"{local_dir}/"
            print(f"[PULL] gsutil -m rsync -r {src} {dst}")
            _, elapsed = run_gsutil(["gsutil", "-m", "rsync", "-r", src, dst], dry_run)
        else:
            _, gcp_file, local_file = op
            src = f"{bucket}/{gcp_file}"
            print(f"[PULL] gsutil cp {src} {local_file}")
            _, elapsed = run_gsutil(["gsutil", "cp", src, local_file], dry_run)
        total += elapsed

    return total


def do_push(step, bucket, gcp_paths, local_paths, dry_run):
    # on push les resultats de l'etape vers le bucket
    push_map = {
        "compile": [
            ("rsync", local_paths["binaries"], gcp_paths["binaries"]),
            ("cp", "data/compile_manifest.json", "compile_manifest.json"),
        ],
        "disasm": [
            ("rsync", local_paths["disasm"], gcp_paths["disasm"]),
        ],
        "embed": [
            ("rsync", local_paths["embeddings"], gcp_paths["embeddings"]),
        ],
        "benchmark": [
            ("rsync", local_paths["results"], gcp_paths["results"]),
        ],
    }

    total = 0.0
    for op in push_map.get(step, []):
        if op[0] == "rsync":
            _, local_dir, gcp_dir = op
            src = f"{local_dir}/"
            dst = f"{bucket}/{gcp_dir}/"
            print(f"[PUSH] gsutil -m rsync -r {src} {dst}")
            _, elapsed = run_gsutil(["gsutil", "-m", "rsync", "-r", src, dst], dry_run)
        else:
            _, local_file, gcp_file = op
            dst = f"{bucket}/{gcp_file}"
            print(f"[PUSH] gsutil cp {local_file} {dst}")
            _, elapsed = run_gsutil(["gsutil", "cp", local_file, dst], dry_run)
        total += elapsed

    return total


def run_script(step, config_path, test_mode):
    # on lance le script python de l'etape
    script = SCRIPTS[step]
    cmd = [sys.executable, script, "--config", config_path]
    if test_mode:
        cmd.append("--test")

    cmd_str = " ".join(cmd)
    print(f"[RUN] {cmd_str}")

    t0 = time.time()
    ret = subprocess.run(cmd)
    elapsed = time.time() - t0

    print(f"[RUN] {step} termine en {elapsed:.1f}s (code: {ret.returncode})")
    return ret.returncode, elapsed


def needs_pull(step, active_steps):
    # on skip le pull si l'etape precedente vient de tourner
    # (les donnees sont deja en local)
    idx = STEPS.index(step)
    if idx == 0:
        # compile : on pull toujours les sources
        return True
    prev = STEPS[idx - 1]
    return prev not in active_steps


def run_pipeline(args):
    cfg = load_config(args.config)

    # config GCP
    gcp_cfg = cfg.get("gcp", {})
    bucket = gcp_cfg.get("bucket", "gs://bscd-database")
    gcp_paths = gcp_cfg.get("paths", {})
    sync_enabled = gcp_cfg.get("sync", True)

    # chemins locaux depuis config
    local_paths = cfg.get("paths", {})

    # etapes a executer
    if args.steps:
        active_steps = [s.strip() for s in args.steps.split(",")]
        for s in active_steps:
            if s not in STEPS:
                print(f"[ERREUR] etape inconnue : '{s}'")
                print(f"  etapes valides : {', '.join(STEPS)}")
                sys.exit(1)
    else:
        active_steps = list(STEPS)

    # on determine si on sync avec GCP
    do_sync = sync_enabled and not args.no_sync and not args.test
    if args.test and sync_enabled and not args.no_sync:
        print("[WARNING] mode --test : sync GCP desactivee automatiquement")

    # affichage de la config
    print(f"[CONFIG] fichier   : {args.config}")
    print(f"[CONFIG] etapes    : {', '.join(active_steps)}")
    print(f"[CONFIG] sync GCP  : {'oui' if do_sync else 'non'}")
    print(f"[CONFIG] test      : {'oui' if args.test else 'non'}")
    print(f"[CONFIG] dry run   : {'oui' if args.dry_run else 'non'}")
    if do_sync:
        print(f"[CONFIG] bucket    : {bucket}")
    print()

    # verifications de base
    check_scripts(active_steps)
    if do_sync:
        check_gsutil()
        if not args.dry_run:
            check_bucket(bucket)
        else:
            print(f"[DRY-RUN] skip verification bucket")
    print()

    # on execute les etapes dans l'ordre
    total_time = 0.0
    results = {}

    for step in STEPS:
        if step not in active_steps:
            continue

        print(f"\n>>> ETAPE : {step.upper()}")

        step_time = 0.0

        # pull
        if do_sync and needs_pull(step, active_steps):
            t = do_pull(step, bucket, gcp_paths, local_paths, args.dry_run)
            step_time += t
        elif do_sync:
            print(f"[SKIP] pull (donnees deja locales, {STEPS[STEPS.index(step) - 1]} vient de tourner)")
        else:
            print(f"[SKIP] pull (sync desactivee)")

        # run
        ret, t = run_script(step, args.config, args.test)
        step_time += t

        if ret != 0:
            results[step] = "ECHEC"
            if args.test:
                print(f"[ERREUR] {step} a echoue en mode test, arret de la pipeline")
                sys.exit(1)
            else:
                print(f"[ERREUR] {step} a echoue (code {ret})")
                print("Continuer avec les etapes suivantes ? (o/n) ", end="", flush=True)
                try:
                    rep = input().strip().lower()
                except EOFError:
                    rep = "n"
                if rep != "o":
                    print("[ARRET] pipeline interrompue")
                    sys.exit(1)
                print("[CONTINUE] on passe a la suite")
                print()
                continue
        else:
            results[step] = "OK"

        # push
        if do_sync:
            t = do_push(step, bucket, gcp_paths, local_paths, args.dry_run)
            step_time += t
        else:
            print(f"[SKIP] push (sync desactivee)")

        total_time += step_time
        print(f"[TEMPS] {step} : {step_time:.1f}s")
        print()

    # resume
    print(f"\n>>> RESUME")
    for step, status in results.items():
        print(f"  {step:12s} : {status}")
    print(f"  {'total':12s} : {total_time:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="orchestre la pipeline BSCD avec sync GCP")
    parser.add_argument("--test", action="store_true",
                        help="mode test local (data/sources/_test/, pas de sync GCP)")
    parser.add_argument("--config", default="config.yaml",
                        help="fichier de config (defaut: config.yaml)")
    parser.add_argument("--steps", default=None,
                        help="etapes a executer, separees par des virgules (ex: compile,disasm)")
    parser.add_argument("--no-sync", action="store_true",
                        help="desactive les sync GCP (tout en local)")
    parser.add_argument("--dry-run", action="store_true",
                        help="affiche les commandes gsutil sans les executer")
    args = parser.parse_args()
    run_pipeline(args)
