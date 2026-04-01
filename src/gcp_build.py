#!/usr/bin/env python3
# src/gcp_build.py
# compile ET desassemble le full dataset BSCD sur une VM GCP x86-64
# tourne sur Mac et pilote la VM via gcloud compute ssh
# la VM est TOUJOURS supprimee a la fin (sauf --keep-vm)

import argparse
import os
import subprocess
import sys
import tempfile
import time

import yaml


VM = "bscd-builder"
MACHINES = ["n2-highcpu-96", "c2d-highcpu-56", "e2-standard-16"]
MAX_POLL_TIME = 24 * 3600


# script python qui tourne sur la VM
# modes: prepare (boilerplate + compile_cmds), manifest, disasm_cmds
VM_PREPARE = r'''#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path
import yaml

SRC = Path("/workspace/sources")
BIN = Path("/workspace/binaries")

C_BP = "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n#include <math.h>\n#include <limits.h>\n#include <stdbool.h>\n#include <ctype.h>\n\n"

CPP_BP = ("#include <algorithm>\n#include <climits>\n#include <cmath>\n"
    "#include <cstring>\n#include <iostream>\n#include <map>\n"
    "#include <queue>\n#include <set>\n#include <sstream>\n"
    "#include <stack>\n#include <string>\n#include <unordered_map>\n"
    "#include <unordered_set>\n#include <vector>\n"
    "using namespace std;\n\n"
    "struct ListNode {\n"
    "    int val; ListNode *next;\n"
    "    ListNode() : val(0), next(nullptr) {}\n"
    "    ListNode(int x) : val(x), next(nullptr) {}\n"
    "};\n"
    "struct TreeNode {\n"
    "    int val; TreeNode *left, *right;\n"
    "    TreeNode() : val(0), left(nullptr), right(nullptr) {}\n"
    "    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}\n"
    "};\n\n")

RE_INC = re.compile(r"^\s*#\s*include\b", re.MULTILINE)
RE_ATC = re.compile(r'#\s*include\s*[<"]atcoder/')


def load_cfg():
    with open("/workspace/config.yaml") as f:
        return yaml.safe_load(f)


def dir_map(cfg):
    dm = {}
    for lk, lc in cfg["pipeline"]["languages"].items():
        for dn in lc.get("dir_names", []):
            dm[dn] = lk
    return dm


def ext_map(cfg):
    em = {}
    for lk, lc in cfg["pipeline"]["languages"].items():
        for ext in lc["extensions"]:
            em[ext] = lk
    return em


def find_src(dm, em):
    out = []
    for f in sorted(SRC.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix not in em:
            continue
        ld = f.parent.name
        if ld not in dm:
            continue
        if em.get(f.suffix) != dm[ld]:
            continue
        out.append(f)
    return out


def get_meta(f, dm):
    rel = f.relative_to(SRC)
    parts = list(rel.parts)
    ld = parts[-2]
    fn = Path(parts[-1]).stem
    sub = parts[:-2]
    ds = sub[0] if len(sub) >= 1 else "unknown"
    pb = sub[1] if len(sub) >= 2 else ds
    sp = "/".join(sub)
    key = f"{sp}/{ld}__{fn}"
    return {"key": key, "lang": dm[ld], "ld": ld, "ds": ds, "pb": pb,
            "fn": fn, "sp": sp, "rel": str(rel)}


def prepare():
    # on injecte le boilerplate et on supprime les fichiers atcoder
    cfg = load_cfg()
    dm = dir_map(cfg)
    em = ext_map(cfg)
    srcs = find_src(dm, em)

    nb_inj, nb_del = 0, 0
    for f in srcs:
        code = f.read_text(errors="replace")
        if RE_ATC.search(code):
            f.unlink()
            nb_del += 1
            continue
        if not RE_INC.search(code):
            lang = dm[f.parent.name]
            bp = CPP_BP if lang == "cpp" else C_BP
            f.write_text(bp + code, encoding="utf-8")
            nb_inj += 1
    print(f"Boilerplate: {nb_inj} injectes, {nb_del} supprimes (atcoder)")

    srcs = find_src(dm, em)
    print(f"{len(srcs)} fichiers source")

    # on genere compile_cmds.txt (une commande par ligne pour xargs)
    comps = cfg["pipeline"]["compilers"]
    archs = cfg["pipeline"]["architectures"]
    opts = cfg["pipeline"]["optimizations"]
    pipe = cfg["pipeline"]

    cmds = []
    for f in srcs:
        m = get_meta(f, dm)
        kp = m["key"].rsplit("/", 1)
        kdir = kp[0] if len(kp) > 1 else ""
        kfile = kp[-1]
        for cn, cc in comps.items():
            cb = cc.get(m["lang"])
            if not cb:
                continue
            for an in archs:
                ac = archs[an]
                for opt in opts:
                    lc = pipe["languages"][m["lang"]]
                    flags = list(pipe["compile_flags"]["common"])
                    flags.extend(ac.get("flags", []))
                    # debug flags par compilateur (gcc != clang)
                    flags.extend(cc.get("debug_flags", ["-g"]))
                    flags.append(f"-std={lc['standard']}")
                    flags.append(f"-{opt}")
                    if m["lang"] == "c":
                        flags.extend(["-Wno-implicit-int",
                                      "-Wno-implicit-function-declaration",
                                      "-D_GNU_SOURCE"])
                    od = f"/workspace/binaries/{cn}/{an}/{opt}"
                    if kdir:
                        od += f"/{kdir}"
                    # executables sans extension (pas de .o)
                    of = f"{od}/{kfile}"
                    fl = " ".join(flags)
                    tag = f"{m['key']}|{cn}|{an}|{opt}"
                    cmd = (f"mkdir -p {od} && {cb} {fl} "
                           f"-o {of} {f} 2>/dev/null "
                           f'&& echo "OK {tag}" '
                           f'|| echo "FAIL {tag}"')
                    cmds.append(cmd)

    with open("/workspace/compile_cmds.txt", "w") as out:
        out.write("\n".join(cmds) + "\n")
    print(f"compile_cmds.txt: {len(cmds)} commandes")


def gen_manifest():
    cfg = load_cfg()
    dm = dir_map(cfg)
    em = ext_map(cfg)
    srcs = find_src(dm, em)
    comps = cfg["pipeline"]["compilers"]
    archs = cfg["pipeline"]["architectures"]
    opts = cfg["pipeline"]["optimizations"]

    mf = {}
    for f in srcs:
        m = get_meta(f, dm)
        key = m["key"]
        if key not in mf:
            mf[key] = {
                "source": f"data/sources/{m['rel']}",
                "lang": m["lang"],
                "dataset": m["ds"],
                "problem": m["pb"],
                "lang_dir": m["ld"],
                "filename": m["fn"],
                "results": {},
            }
        kp = key.rsplit("/", 1)
        kdir = kp[0] if len(kp) > 1 else ""
        kfile = kp[-1]
        for cn, cc in comps.items():
            if not cc.get(m["lang"]):
                continue
            mf[key]["results"].setdefault(cn, {})
            for an in archs:
                mf[key]["results"][cn].setdefault(an, {})
                for opt in opts:
                    od = f"/workspace/binaries/{cn}/{an}/{opt}"
                    if kdir:
                        od += f"/{kdir}"
                    # executables sans extension
                    of = f"{od}/{kfile}"
                    mf[key]["results"][cn][an][opt] = "ok" if os.path.isfile(of) else "fail"

    nb_ok = sum(1 for e in mf.values() for c in e["results"].values()
                for a in c.values() for s in a.values() if s == "ok")
    nb_fail = sum(1 for e in mf.values() for c in e["results"].values()
                  for a in c.values() for s in a.values() if s == "fail")

    with open("/workspace/compile_manifest.json", "w") as out:
        json.dump(mf, out, indent=2, ensure_ascii=False)
    print(f"Manifest: {len(mf)} sources, {nb_ok} ok, {nb_fail} fail")


def disasm_cmds():
    # on lit le manifest et on genere les jobs de desassemblage
    with open("/workspace/compile_manifest.json") as f:
        mf = json.load(f)

    jobs = []
    for sid, entry in mf.items():
        for comp, arch_res in entry.get("results", {}).items():
            for arch, opt_res in arch_res.items():
                for opt, status in opt_res.items():
                    if status != "ok":
                        continue
                    # executables sans extension
                    bp = f"/workspace/binaries/{comp}/{arch}/{opt}/{sid}"
                    jp = f"/workspace/disasm/{comp}/{arch}/{opt}/{sid}.json"
                    sp = entry.get("source", "")
                    ds = entry.get("dataset", "")
                    pb = entry.get("problem", "")
                    lang = entry.get("lang", "")
                    jobs.append(f"{bp} {jp} {comp} {arch} {opt} {sid} {sp} {ds} {pb} {lang}")

    with open("/workspace/disasm_jobs.txt", "w") as out:
        out.write("\n".join(jobs) + "\n")
    print(f"disasm_jobs.txt: {len(jobs)} jobs")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "prepare":
        prepare()
    elif mode == "manifest":
        gen_manifest()
    elif mode == "disasm_cmds":
        disasm_cmds()
    else:
        print("Usage: vm_prepare.py [prepare|manifest|disasm_cmds]")
        sys.exit(1)
'''


# worker de desassemblage par batch
# chaque worker importe angr UNE SEULE FOIS puis traite son chunk de .o
VM_DISASM_BATCH = r'''#!/usr/bin/env python3
# worker de desassemblage par batch
# importe angr UNE SEULE FOIS puis traite son chunk de binaires ELF
import json
import os
import re
import signal
import sys
import warnings

warnings.filterwarnings("ignore")
os.environ["ANGR_DISABLE_UNICORN"] = "1"

import logging
logging.disable(logging.CRITICAL)

import angr
import yaml

TIMEOUT = 120
MAX_SIZE = 10 * 1024 * 1024

# noms auto generes par angr (pas de symbole DWARF)
RE_SUB = re.compile(r"^sub_[0-9a-fA-F]+$")

# noms internes angr pour les sauts non resolus
ANGR_INTERNALS = {"UnresolvableJumpTarget", "UnresolvableCallTarget"}

cfg = yaml.safe_load(open("/workspace/config.yaml"))
dcfg = cfg["pipeline"]["disassembly"]
min_insns = dcfg.get("min_instructions", 5)
skip_pfx = dcfg.get("skip_prefixes", [])
skip_plt = dcfg.get("skip_plt", True)
do_cfg = dcfg.get("extract_cfg", False)
use_dwarf = dcfg.get("use_dwarf_symbols", True)


def alarm_handler(signum, frame):
    raise TimeoutError("angr timeout")

signal.signal(signal.SIGALRM, alarm_handler)


def extract_insns(func):
    insns = []
    for block in func.blocks:
        try:
            for i in block.capstone.insns:
                insns.append([i.mnemonic, i.op_str])
        except Exception:
            pass
    return insns


def extract_edges(func):
    edges = []
    try:
        for s, d in func.graph.edges():
            edges.append([hex(s.addr), hex(d.addr)])
    except Exception:
        pass
    return edges


def check_has_dwarf(proj):
    # on cherche les sections .debug dans le binaire
    try:
        obj = proj.loader.main_object
        for sec in obj.sections:
            if sec.name.startswith(".debug"):
                return True
    except Exception:
        pass
    return False


def should_skip(func):
    # on filtre runtime, PLT, stubs, sub_XXXX
    name = func.name

    # noms internes angr
    if name in ANGR_INTERNALS:
        return True

    # PLT : stubs de la libc (printf@plt, etc.)
    if skip_plt and (func.is_plt or "@plt" in name):
        return True

    # sub_XXXX : angr a pas trouve de symbole DWARF
    if use_dwarf and RE_SUB.match(name):
        return True

    # prefixes de la config (runtime, startup, etc.)
    for pfx in skip_pfx:
        if name.startswith(pfx):
            return True

    return False


def process(line):
    parts = line.strip().split()
    if len(parts) < 10:
        return
    bp, jp, comp, arch, opt, sid, sp, ds, pb, lang = parts[:10]

    if not os.path.exists(bp):
        return
    if os.path.getsize(bp) > MAX_SIZE:
        print(f"SKIP: {sid} trop gros")
        return

    signal.alarm(TIMEOUT)
    try:
        proj = angr.Project(bp, auto_load_libs=False)
        res = proj.analyses.CFGFast(normalize=True)

        has_dwarf = check_has_dwarf(proj)
        nb_total = len(res.kb.functions)
        nb_filtered = 0

        funcs = []
        for addr, func in sorted(res.kb.functions.items()):
            if should_skip(func):
                nb_filtered += 1
                continue
            insns = extract_insns(func)
            if len(insns) < min_insns:
                nb_filtered += 1
                continue
            funcs.append({
                "name": func.name,
                "addr": hex(addr),
                "nb_instructions": len(insns),
                "instructions": insns,
                "cfg_edges": extract_edges(func) if do_cfg else [],
            })

        nb_kept = len(funcs)
        if not funcs:
            return

        result = {
            "source_id": sid,
            "source_path": sp,
            "compiler": comp,
            "arch": arch,
            "optim": opt,
            "backend": "angr",
            "dataset": ds,
            "problem": pb,
            "lang": lang,
            "has_dwarf": has_dwarf,
            "nb_functions_total": nb_total,
            "nb_functions_filtered": nb_filtered,
            "nb_functions_kept": nb_kept,
            "functions": funcs,
        }
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        with open(jp, "w") as f:
            json.dump(result, f)

    except TimeoutError:
        print(f"TIMEOUT: {sid} [{comp}/{arch}/{opt}]")
    except Exception as e:
        print(f"FAIL: {sid} [{comp}/{arch}/{opt}] {str(e)[:100]}")
    finally:
        signal.alarm(0)


job_file = sys.argv[1]
with open(job_file) as f:
    for line in f:
        if line.strip():
            process(line)
'''


# lanceur bash : compilation parallele
SH_COMPILE = r'''#!/bin/bash
NPAR=${1:-$(nproc)}
echo "Compilation parallele sur $NPAR coeurs..."
xargs -d '\n' -P $NPAR -I {} bash -c '{}' < /workspace/compile_cmds.txt > /workspace/compile.log 2>&1
# on compte les executables ELF (pas d'extension, on cherche les fichiers non-dossiers)
NB=$(find /workspace/binaries -type f -executable 2>/dev/null | wc -l | tr -d ' ')
NO=$(grep -c '^OK ' /workspace/compile.log 2>/dev/null | tr -d ' ')
NF=$(grep -c '^FAIL ' /workspace/compile.log 2>/dev/null | tr -d ' ')
echo "Termine: ${NB} executables, ${NO:-0} ok, ${NF:-0} echecs"
touch /workspace/compile.done
'''


# lanceur bash : desassemblage parallele (split + batch workers)
SH_DISASM = r'''#!/bin/bash
NPAR=${1:-$(nproc)}
TOTAL=$(wc -l < /workspace/disasm_jobs.txt | tr -d ' ')
echo "Desassemblage: $TOTAL jobs sur $NPAR workers..."

if [ "$TOTAL" -eq 0 ]; then
    echo "Rien a desassembler"
    touch /workspace/disasm.done
    exit 0
fi

mkdir -p /workspace/logs
cd /workspace

if [ "$TOTAL" -lt "$NPAR" ]; then
    NPAR=$TOTAL
fi

split -n l/$NPAR disasm_jobs.txt disasm_chunk_
for f in disasm_chunk_*; do
    python3 /workspace/vm_disasm_batch.py "$f" > "/workspace/logs/$(basename $f).log" 2>&1 &
done
wait

NB=$(find /workspace/disasm -name '*.json' 2>/dev/null | wc -l | tr -d ' ')
echo "Termine: $NB JSON produits"
touch /workspace/disasm.done
'''


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
    # version silencieuse pour le polling (pas de print)
    ret = subprocess.run(
        ["gcloud", "compute", "ssh", VM, f"--zone={zone}", f"--command={command}"],
        capture_output=True, text=True,
    )
    return ret.stdout.strip()


def scp_up(local, remote, zone, dry_run=False):
    print(f"[SSH] scp {os.path.basename(local)} -> {VM}:{remote}")
    ok, _ = run(
        ["gcloud", "compute", "scp", local, f"{VM}:{remote}", f"--zone={zone}"],
        dry_run=dry_run,
    )
    return ok


def create_vm(zone, machine, dry_run):
    machines = [machine] if machine else list(MACHINES)
    for mt in machines:
        print(f"\n[VM] tentative {mt} ({zone})")
        ok, _ = run([
            "gcloud", "compute", "instances", "create", VM,
            f"--zone={zone}",
            f"--machine-type={mt}",
            "--image-family=ubuntu-2204-lts",
            "--image-project=ubuntu-os-cloud",
            "--boot-disk-size=200GB",
            "--boot-disk-type=pd-ssd",
            "--scopes=storage-full",
        ], dry_run=dry_run)
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


def upload_file(content, name, zone, dry_run):
    # on ecrit le contenu dans un temp et on le SCP sur la VM
    with tempfile.NamedTemporaryFile(mode="w", suffix=f"_{name}", delete=False) as f:
        f.write(content)
        tmp = f.name
    try:
        scp_up(tmp, f"/workspace/{name}", zone, dry_run)
    finally:
        os.unlink(tmp)


def poll(zone, done_file, count_cmd, total, label, dry_run, interval=60):
    # on poll la progression toutes les interval secondes
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


def main():
    parser = argparse.ArgumentParser(description="compile + desassemble BSCD sur VM GCP")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--zone", default="europe-west9-a")
    parser.add_argument("--machine", default=None, help="forcer un type de machine")
    parser.add_argument("--keep-vm", action="store_true", help="ne pas supprimer la VM")
    parser.add_argument("--dry-run", action="store_true", help="affiche sans executer")
    parser.add_argument("--skip-compile", action="store_true", help="skip la compilation")
    parser.add_argument("--skip-disasm", action="store_true", help="skip le desassemblage")
    parser.add_argument("--parallel", type=int, default=None,
                        help="nombre de workers paralleles (defaut: nproc)")
    args = parser.parse_args()

    cfg = load_config(args.config)
    bucket = cfg.get("gcp", {}).get("bucket", "gs://bscd-database")
    gcp_src = cfg.get("gcp", {}).get("paths", {}).get("sources", "sources")
    dry = args.dry_run
    zone = args.zone

    if not dry:
        ret = subprocess.run(["gcloud", "version"], capture_output=True, text=True)
        if ret.returncode != 0:
            print("[ERREUR] gcloud pas installe ou pas configure")
            sys.exit(1)
        print("[OK] gcloud installe")

    print(f"[CONFIG] bucket   : {bucket}")
    print(f"[CONFIG] zone     : {zone}")
    print(f"[CONFIG] compile  : {'skip' if args.skip_compile else 'oui'}")
    print(f"[CONFIG] disasm   : {'skip' if args.skip_disasm else 'oui'}")
    if args.parallel:
        print(f"[CONFIG] parallel : {args.parallel}")

    t_global = time.time()

    # Phase 1 : creer la VM
    mt = create_vm(zone, args.machine, dry)

    try:
        wait_ssh(zone, dry)

        # Phase 2 : setup
        print("\n[SETUP] installation gcc, g++, clang, python3, angr")
        ssh(zone,
            "sudo apt-get update -qq && "
            "sudo apt-get install -y -qq gcc g++ clang python3-pip",
            dry)
        ssh(zone,
            "pip3 install angr pyyaml tqdm --break-system-packages -q",
            dry)
        ssh(zone,
            "sudo mkdir -p /workspace && sudo chown $(whoami) /workspace",
            dry)

        # on pull les sources
        print(f"\n[PULL] sources depuis {bucket}/{gcp_src}/")
        ssh(zone, f"gsutil -m rsync -r {bucket}/{gcp_src}/ /workspace/sources/", dry)
        ssh(zone,
            "echo -n 'Fichiers source: ' && "
            "find /workspace/sources -type f | wc -l | tr -d ' '",
            dry, fatal=False)

        # on upload les scripts
        print("\n[SETUP] upload des scripts")
        scp_up(args.config, "/workspace/config.yaml", zone, dry)
        upload_file(VM_PREPARE, "vm_prepare.py", zone, dry)
        upload_file(VM_DISASM_BATCH, "vm_disasm_batch.py", zone, dry)
        upload_file(SH_COMPILE, "launch_compile.sh", zone, dry)
        upload_file(SH_DISASM, "launch_disasm.sh", zone, dry)
        ssh(zone, "chmod +x /workspace/launch_*.sh", dry, fatal=False)

        # Phases 3-5 : compilation
        if not args.skip_compile:
            print("\n[COMPILE] preparation des sources")
            ssh(zone, "python3 /workspace/vm_prepare.py prepare", dry)

            total_str = ssh_quiet(zone,
                "wc -l < /workspace/compile_cmds.txt 2>/dev/null | tr -d ' '"
            ) if not dry else "0"
            total_compile = int(total_str) if total_str.isdigit() else 0

            par = f" {args.parallel}" if args.parallel else ""
            print(f"\n[COMPILE] lancement ({total_compile} commandes)")
            ssh(zone,
                f"nohup bash /workspace/launch_compile.sh{par} "
                f"> /workspace/nohup_compile.log 2>&1 < /dev/null &",
                dry)

            if not dry:
                time.sleep(5)
            poll(zone, "/workspace/compile.done",
                 "wc -l < /workspace/compile.log 2>/dev/null | tr -d ' '",
                 total_compile, "COMPILE", dry)

            # Phase 4 : manifest
            print("\n[COMPILE] generation du manifest")
            ssh(zone, "python3 /workspace/vm_prepare.py manifest", dry)

            # Phase 5 : push binaires (sauvegarde intermediaire)
            print(f"\n[PUSH] binaires vers {bucket}/binaries/")
            ssh(zone,
                f"gsutil -m rsync -r /workspace/binaries/ {bucket}/binaries/",
                dry)
            ssh(zone,
                f"gsutil cp /workspace/compile_manifest.json "
                f"{bucket}/compile_manifest.json",
                dry)

        # Phases 6-7 : desassemblage
        if not args.skip_disasm:
            if args.skip_compile:
                # on pull les binaires et le manifest depuis le bucket
                print(f"\n[PULL] binaires depuis {bucket}/binaries/")
                ssh(zone,
                    f"gsutil -m rsync -r {bucket}/binaries/ /workspace/binaries/",
                    dry)
                ssh(zone,
                    f"gsutil cp {bucket}/compile_manifest.json "
                    f"/workspace/compile_manifest.json",
                    dry)

            print("\n[DISASM] generation des jobs")
            ssh(zone, "python3 /workspace/vm_prepare.py disasm_cmds", dry)

            total_str = ssh_quiet(zone,
                "wc -l < /workspace/disasm_jobs.txt 2>/dev/null | tr -d ' '"
            ) if not dry else "0"
            total_disasm = int(total_str) if total_str.isdigit() else 0

            par = f" {args.parallel}" if args.parallel else ""
            print(f"\n[DISASM] lancement ({total_disasm} jobs)")
            ssh(zone,
                f"nohup bash /workspace/launch_disasm.sh{par} "
                f"> /workspace/nohup_disasm.log 2>&1 < /dev/null &",
                dry)

            if not dry:
                time.sleep(10)
            poll(zone, "/workspace/disasm.done",
                 "find /workspace/disasm -name '*.json' 2>/dev/null | wc -l | tr -d ' '",
                 total_disasm, "DISASM", dry)

            # Phase 7 : push disasm
            print(f"\n[PUSH] disasm vers {bucket}/disasm/")
            ssh(zone,
                f"gsutil -m rsync -r /workspace/disasm/ {bucket}/disasm/",
                dry)

        elapsed = (time.time() - t_global) / 60
        print(f"\n[OK] pipeline terminee en {elapsed:.0f}min")

    except (Exception, KeyboardInterrupt) as e:
        print(f"\n[ERREUR] {e}")

    finally:
        # Phase 8 : on supprime TOUJOURS la VM
        if args.keep_vm:
            print(f"\n[VM] conservee (--keep-vm)")
            print(f"  connexion  : gcloud compute ssh {VM} --zone={zone}")
            print(f"  suppression: gcloud compute instances delete {VM} "
                  f"--zone={zone} --quiet")
        else:
            delete_vm(zone, dry)


if __name__ == "__main__":
    main()
