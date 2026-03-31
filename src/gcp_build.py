# VM pour le pipeline BSCD
# upload les scripts (compile.py, disasm.py, embed, benchmark) et les lance
# la VM est toujours supprimee a la fin (sauf --keep-vm)

import argparse
import os
import subprocess
import sys
import time

import yaml


VM = "bscd-builder"
CPU_MACHINES = ["n2-highcpu-96", "c2d-highcpu-56", "e2-standard-16"]
GPU_MACHINE = "n1-standard-8"
GPU_TYPE = "nvidia-tesla-t4"
MAX_POLL_TIME = 24 * 3600 # on sait jamais car c'est payant

# scripts a uploader sur la VM
SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
SRC_DIR = os.path.dirname(__file__)


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def run(cmd, dry_run=False):
    s = " ".join(cmd)
    if dry_run:
        print(f"  [DRY-RUN] {s}")
        return True, ""

    ret = subprocess.run(cmd, capture_output=True, text=True)
    out = ret.stdout.strip()

    if out:
        for line in out.splitlines()[:5]:
            print(f"  {line}")
    if ret.returncode != 0 and ret.stderr.strip():
        for line in ret.stderr.strip().splitlines()[:3]:
            print(f"  [stderr] {line}")

    return ret.returncode == 0, out


def ssh(zone, command, dry_run=False, fatal=True):
    short = command if len(command) <= 100 else command[:97] + "..."
    print(f"[SSH] {short}")
    ok, out = run(
        ["gcloud", "compute", "ssh", VM, f"--zone={zone}", f"--command={command}"],
        dry_run=dry_run,
    )
    if not ok and fatal and not dry_run:
        raise RuntimeError(f"SSH echoue: {command[:60]}")
    return ok, out


def ssh_quiet(zone, command):
    # version silencieuse pour le polling
    ret = subprocess.run(
        ["gcloud", "compute", "ssh", VM, f"--zone={zone}", f"--command={command}"],
        capture_output=True, text=True,
    )
    return ret.stdout.strip()


def scp_up(local, remote, zone, dry_run=False):
    print(f"[SCP] {os.path.basename(local)} -> {VM}:{remote}")
    ok, _ = run(
        ["gcloud", "compute", "scp", local, f"{VM}:{remote}", f"--zone={zone}"],
        dry_run=dry_run,
    )
    return ok


def scp_dir_up(local_dir, remote_dir, zone, dry_run=False):
    # upload un dossier entier
    print(f"[SCP] {os.path.basename(local_dir)}/ -> {VM}:{remote_dir}/")
    ok, _ = run(
        ["gcloud", "compute", "scp", "--recurse", local_dir, f"{VM}:{remote_dir}", f"--zone={zone}"],
        dry_run=dry_run,
    )
    return ok


def create_vm(zone, machine, dry_run, gpu=False):
    if gpu:
        machines = [machine] if machine else [GPU_MACHINE]
        accel = f"--accelerator=type={GPU_TYPE},count=1"
    else:
        machines = [machine] if machine else list(CPU_MACHINES)
        accel = None

    for mt in machines:
        print(f"\n[VM] tentative {mt} ({zone}){' + GPU' if gpu else ''}")
        cmd = [
            "gcloud", "compute", "instances", "create", VM,
            f"--zone={zone}",
            f"--machine-type={mt}",
            "--image-family=ubuntu-2204-lts",
            "--image-project=ubuntu-os-cloud",
            "--boot-disk-size=200GB",
            "--boot-disk-type=pd-ssd",
            "--scopes=storage-full",
        ]
        if accel:
            cmd.append(accel)
            cmd.append("--maintenance-policy=TERMINATE")

        ok, _ = run(cmd, dry_run=dry_run)
        if ok:
            print(f"[VM] creee : {mt}")
            return mt
        print(f"[VM] {mt} echec, on essaie la suivante")

    print("[VM] aucune machine disponible")
    sys.exit(1)


def delete_vm(zone, dry_run):
    print(f"\n[CLEANUP] suppression {VM}")
    run(["gcloud", "compute", "instances", "delete", VM,
         f"--zone={zone}", "--quiet"], dry_run=dry_run)


def wait_ssh(zone, dry_run):
    if dry_run:
        print("[VM] (dry-run) skip attente SSH")
        return
    print("[VM] attente SSH...")
    for _ in range(30):
        ok, _ = run(
            ["gcloud", "compute", "ssh", VM, f"--zone={zone}", "--command=echo ready"],
            dry_run=False,
        )
        if ok:
            print("[VM] SSH pret")
            return
        time.sleep(10)
    raise RuntimeError("SSH timeout (5 min)")


def poll(zone, done_file, count_cmd, total, label, dry_run, interval=60):
    if dry_run:
        print(f"  [DRY-RUN] poll {label} (total: {total})")
        return

    t0 = time.time()
    while True:
        if time.time() - t0 > MAX_POLL_TIME:
            print(f"[{label}] TIMEOUT ({MAX_POLL_TIME // 3600}h)")
            break

        status = ssh_quiet(zone, f"test -f {done_file} && echo DONE || echo RUNNING")
        if "DONE" in status:
            break

        raw = ssh_quiet(zone, count_cmd)
        try:
            nb = int(raw)
        except (ValueError, TypeError):
            nb = 0

        elapsed = time.time() - t0
        pct = (nb / total * 100) if total > 0 else 0
        eta = ((elapsed / nb) * (total - nb) / 60) if nb > 0 else 0

        print(f"[{label}] {nb}/{total} ({pct:.1f}%) "
              f"elapsed: {elapsed / 60:.0f}min, ETA: {eta:.0f}min")

        time.sleep(interval)

    elapsed = (time.time() - t0) / 60
    print(f"[{label}] termine en {elapsed:.1f}min")


def setup_base(zone, dry_run):
    # installe les paquets de base et cree le workspace
    print("\n[SETUP] installation gcc, g++, clang, python3")
    ssh(zone,
        "sudo apt-get update -qq && "
        "sudo apt-get install -y -qq gcc g++ clang python3-pip",
        dry_run)
    ssh(zone,
        "pip3 install pyyaml tqdm --break-system-packages -q",
        dry_run)
    ssh(zone,
        "sudo mkdir -p /workspace && sudo chown $(whoami) /workspace",
        dry_run)


def setup_angr(zone, dry_run):
    print("[SETUP] installation angr")
    ssh(zone, "pip3 install angr --break-system-packages -q", dry_run)


def setup_gpu(zone, dry_run):
    # installe les drivers CUDA et pytorch
    print("[SETUP] installation drivers CUDA + PyTorch")
    ssh(zone,
        "sudo apt-get install -y -qq linux-headers-$(uname -r) && "
        "sudo apt-get install -y -qq nvidia-driver-535",
        dry_run)
    ssh(zone,
        "pip3 install torch torchvision --break-system-packages -q",
        dry_run)


def upload_scripts(zone, config_path, dry_run, phases):
    # on upload seulement les scripts necessaires
    print("\n[SETUP] upload des scripts")
    scp_up(config_path, "/workspace/config.yaml", zone, dry_run)

    if "compile" in phases or "disasm" in phases:
        scp_up(os.path.join(SRC_DIR, "compile.py"), "/workspace/compile.py", zone, dry_run)
        scp_up(os.path.join(SCRIPTS_DIR, "launch_compile.sh"), "/workspace/launch_compile.sh", zone, dry_run)
        ssh(zone, "chmod +x /workspace/launch_compile.sh", dry_run, fatal=False)

    if "disasm" in phases:
        scp_up(os.path.join(SRC_DIR, "disasm.py"), "/workspace/disasm.py", zone, dry_run)
        scp_up(os.path.join(SCRIPTS_DIR, "launch_disasm.sh"), "/workspace/launch_disasm.sh", zone, dry_run)
        ssh(zone, "chmod +x /workspace/launch_disasm.sh", dry_run, fatal=False)

    if "embed" in phases:
        scp_up(os.path.join(SRC_DIR, "embed_palmtree.py"), "/workspace/embed_palmtree.py", zone, dry_run)
        scp_up(os.path.join(SRC_DIR, "embed_baseline.py"), "/workspace/embed_baseline.py", zone, dry_run)

    if "benchmark" in phases:
        scp_up(os.path.join(SRC_DIR, "benchmark.py"), "/workspace/benchmark.py", zone, dry_run)


def pull_sources(zone, bucket, gcp_src, dry_run):
    print(f"\n[PULL] sources depuis {bucket}/{gcp_src}/")
    ssh(zone, "mkdir -p /workspace/data", dry_run, fatal=False)
    ssh(zone, f"gsutil -m rsync -r {bucket}/{gcp_src}/ /workspace/data/sources/", dry_run)
    ssh(zone,
        "echo -n 'Fichiers source: ' && "
        "find /workspace/data/sources -type f | wc -l | tr -d ' '",
        dry_run, fatal=False)


def phase_compile(zone, bucket, dry_run, parallel):
    print("\n[COMPILE] preparation des sources")
    ssh(zone,
        "cd /workspace && python3 compile.py --mode prepare "
        "--src-dir data/sources --bin-dir data/binaries "
        "--work-dir . --config config.yaml",
        dry_run)

    total_str = ssh_quiet(zone,
        "wc -l < /workspace/compile_cmds.txt 2>/dev/null | tr -d ' '"
    ) if not dry_run else "0"
    total = int(total_str) if total_str.isdigit() else 0

    par = f" {parallel}" if parallel else ""
    print(f"\n[COMPILE] lancement ({total} commandes)")
    ssh(zone,
        f"nohup bash /workspace/launch_compile.sh{par} "
        f"> /workspace/nohup_compile.log 2>&1 < /dev/null &",
        dry_run)

    if not dry_run:
        time.sleep(5)
    poll(zone, "/workspace/compile.done",
         "wc -l < /workspace/compile.log 2>/dev/null | tr -d ' '",
         total, "COMPILE", dry_run)

    # manifest
    print("\n[COMPILE] generation du manifest")
    ssh(zone,
        "cd /workspace && python3 compile.py --mode manifest "
        "--src-dir data/sources --bin-dir data/binaries "
        "--work-dir . --config config.yaml",
        dry_run)

    # push binaires
    print(f"\n[PUSH] binaires vers {bucket}/binaries/")
    ssh(zone, f"gsutil -m rsync -r /workspace/data/binaries/ {bucket}/binaries/", dry_run)
    ssh(zone, f"gsutil cp /workspace/compile_manifest.json {bucket}/compile_manifest.json", dry_run)


def phase_disasm(zone, bucket, dry_run, parallel, skip_compile):
    if skip_compile:
        print(f"\n[PULL] binaires depuis {bucket}/binaries/")
        ssh(zone, "mkdir -p /workspace/data", dry_run, fatal=False)
        ssh(zone, f"gsutil -m rsync -r {bucket}/binaries/ /workspace/data/binaries/", dry_run)
        ssh(zone, f"gsutil cp {bucket}/compile_manifest.json /workspace/compile_manifest.json", dry_run)

    # generation des jobs
    print("\n[DISASM] generation des jobs")
    ssh(zone,
        "cd /workspace && python3 compile.py --mode disasm-jobs "
        "--bin-dir data/binaries --work-dir . --config config.yaml",
        dry_run)

    total_str = ssh_quiet(zone,
        "wc -l < /workspace/disasm_jobs.txt 2>/dev/null | tr -d ' '"
    ) if not dry_run else "0"
    total = int(total_str) if total_str.isdigit() else 0

    par = f" {parallel}" if parallel else ""
    print(f"\n[DISASM] lancement ({total} jobs)")
    ssh(zone,
        f"nohup bash /workspace/launch_disasm.sh{par} "
        f"> /workspace/nohup_disasm.log 2>&1 < /dev/null &",
        dry_run)

    if not dry_run:
        time.sleep(10)
    poll(zone, "/workspace/disasm.done",
         "find /workspace/data/disasm -name '*.json' 2>/dev/null | wc -l | tr -d ' '",
         total, "DISASM", dry_run)

    # push disasm
    print(f"\n[PUSH] disasm vers {bucket}/disasm/")
    ssh(zone, f"gsutil -m rsync -r /workspace/data/disasm/ {bucket}/disasm/", dry_run)


def phase_embed(zone, bucket, dry_run):
    # pull des disasm depuis le bucket
    print(f"\n[PULL] disasm depuis {bucket}/disasm/")
    ssh(zone, "mkdir -p /workspace/data", dry_run, fatal=False)
    ssh(zone, f"gsutil -m rsync -r {bucket}/disasm/ /workspace/data/disasm/", dry_run)

    # upload du modele PalmTree depuis le bucket (plus rapide que SCP)
    print("\n[PULL] modele PalmTree")
    ssh(zone, "mkdir -p /workspace/lib", dry_run, fatal=False)
    ssh(zone, f"gsutil -m rsync -r {bucket}/palmtree/ /workspace/lib/palmtree/", dry_run)

    # pip install torch si pas deja fait
    ssh(zone, "pip3 install torch --break-system-packages -q", dry_run)

    # lancement des embeddings PalmTree
    print("\n[EMBED] PalmTree")
    ssh(zone,
        "cd /workspace && python3 embed_palmtree.py "
        "--config config.yaml --device auto",
        dry_run)

    # baseline (pas besoin de GPU)
    print("\n[EMBED] baseline")
    ssh(zone,
        "cd /workspace && python3 embed_baseline.py --config config.yaml",
        dry_run)

    # push embeddings
    print(f"\n[PUSH] embeddings vers {bucket}/embeddings/")
    ssh(zone, f"gsutil -m rsync -r /workspace/data/embeddings/ {bucket}/embeddings/", dry_run)


def phase_benchmark(zone, bucket, dry_run):
    # pull des embeddings
    print(f"\n[PULL] embeddings depuis {bucket}/embeddings/")
    ssh(zone, "mkdir -p /workspace/data", dry_run, fatal=False)
    ssh(zone, f"gsutil -m rsync -r {bucket}/embeddings/ /workspace/data/embeddings/", dry_run)

    # pip install sklearn, matplotlib, seaborn
    ssh(zone,
        "pip3 install scikit-learn matplotlib seaborn --break-system-packages -q",
        dry_run)

    print("\n[BENCHMARK] lancement")
    ssh(zone,
        "cd /workspace && python3 benchmark.py --config config.yaml",
        dry_run)

    # push resultats
    print(f"\n[PUSH] resultats vers {bucket}/results/")
    ssh(zone, f"gsutil -m rsync -r /workspace/results/ {bucket}/results/", dry_run)


def main():
    parser = argparse.ArgumentParser(description="Pipeline BSCD sur VM GCP")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--zone", default="europe-west9-a")
    parser.add_argument("--machine", default=None, help="forcer un type de machine")
    parser.add_argument("--keep-vm", action="store_true", help="ne pas supprimer la VM")
    parser.add_argument("--dry-run", action="store_true", help="affiche sans executer")
    parser.add_argument("--phases", nargs="+",
                        choices=["compile", "disasm", "embed", "benchmark"],
                        default=["compile", "disasm"],
                        help="phases a executer (defaut: compile disasm)")
    parser.add_argument("--parallel", type=int, default=None,
                        help="nombre de workers paralleles (defaut: nproc)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    bucket = cfg.get("gcp", {}).get("bucket", "gs://bscd-database")
    gcp_src = cfg.get("gcp", {}).get("paths", {}).get("sources", "sources")
    dry = args.dry_run
    zone = args.zone
    phases = set(args.phases)

    # GPU necessaire seulement pour l'embedding
    need_gpu = "embed" in phases

    if not dry:
        ret = subprocess.run(["gcloud", "version"], capture_output=True, text=True)
        if ret.returncode != 0:
            print("[ERREUR] gcloud pas installe ou pas configure")
            sys.exit(1)
        print("[OK] gcloud installe")

    print(f"[CONFIG] bucket   : {bucket}")
    print(f"[CONFIG] zone     : {zone}")
    print(f"[CONFIG] phases   : {', '.join(args.phases)}")
    print(f"[CONFIG] GPU      : {'oui' if need_gpu else 'non'}")
    if args.parallel:
        print(f"[CONFIG] parallel : {args.parallel}")

    t_global = time.time()

    mt = create_vm(zone, args.machine, dry, gpu=need_gpu)

    try:
        wait_ssh(zone, dry)

        # setup de base
        setup_base(zone, dry)
        if "disasm" in phases:
            setup_angr(zone, dry)
        if need_gpu:
            setup_gpu(zone, dry)

        # upload des scripts et des sources
        upload_scripts(zone, args.config, dry, phases)
        if "compile" in phases:
            pull_sources(zone, bucket, gcp_src, dry)

        # execution des phases dans l'ordre
        skip_compile = "compile" not in phases

        if "compile" in phases:
            phase_compile(zone, bucket, dry, args.parallel)

        if "disasm" in phases:
            phase_disasm(zone, bucket, dry, args.parallel, skip_compile)

        if "embed" in phases:
            phase_embed(zone, bucket, dry)

        if "benchmark" in phases:
            phase_benchmark(zone, bucket, dry)

        elapsed = (time.time() - t_global) / 60
        print(f"\n[OK] pipeline terminee en {elapsed:.0f}min")

    except (Exception, KeyboardInterrupt) as e:
        print(f"\n[ERREUR] {e}")

    finally:
        if args.keep_vm:
            print(f"\n[VM] conservee (--keep-vm)")
            print(f"  connexion  : gcloud compute ssh {VM} --zone={zone}")
            print(f"  suppression: gcloud compute instances delete {VM} "
                  f"--zone={zone} --quiet")
        else:
            delete_vm(zone, dry)


if __name__ == "__main__":
    main()
