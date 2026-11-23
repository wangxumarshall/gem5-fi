#!/usr/bin/env python3
"""WHEN-5X3 MMU fault-injection campaign runner.

Modes:
  --prescan M C        one golden no-fault pre-scan (also the Control)
  --fault  SAMPLE_ID   one fault run at the planned ordinal
  --all                prescan every (M,C), then every fault T01-T03
  --status             print the status matrix

The campaign is resumable: a run directory containing a final manifest.json
is never re-executed.  Every run is independent (fresh disk copy, private
output directory) and gem5 is invoked with the SAME binary/config used by the
frozen formal campaign (configs/fs/lsu_b0_fs.py, O3, lsu_b0 parameters).

WHEN definition: N = number of eligible events in the golden ROI of
(M, Context); TargetOrdinal = ceil(p*N), p in {1/10, 1/2, 9/10}.
"""
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMPAIGN = os.path.join(ROOT, "campaign")
COND_FILE = os.path.join(CAMPAIGN, "conditions.json")
CTX_FILE = os.path.join(CAMPAIGN, "context_map.json")
RCS_DIR = os.path.join(CAMPAIGN, "rcs")
GEM5 = os.path.join(ROOT, "CHAOS", "gem5", "build", "ARM", "gem5.opt")
CONFIG = os.path.join(ROOT, "configs", "fs", "lsu_b0_fs.py")
KERNEL = os.path.join(ROOT, "gem5-fs", "vmlinux")
BOOTLOADER = os.path.join(ROOT, "gem5-fs", "boot.arm64")
CHECKPOINT = os.environ.get("W5X3_CHECKPOINT") or os.path.join(
    ROOT, "runs", "mmu_bootF1", "cpt.244799013609")
DISK_TEMPLATE = os.path.join(ROOT, "runs", "disks",
                             "mmu_template.img")
RUNS = os.path.join(ROOT, "runs", "W5X3")
STATUS_CSV = os.path.join(ROOT, "experiment_status.csv")
MANIFEST = os.path.join(ROOT, "run_manifest.json")
BLOCKED_MD = os.path.join(ROOT, "blocked_tasks.md")

# Frozen 4 KiB M02 PFN observed by the independent legacy W10 scoped
# controls.  A pre-scan with this value yields N>0 when the guest allocation
# is unchanged; otherwise the runner re-reads the real PFN from the guest
# output and retries (still no source/Where change).
M02_PFN_DEFAULT = 0x834B2

# (model, internal guest context) -> target VA/mode.  Derived from the
# frozen workload macros and the 07_Sample_Matrix context identities.
TARGET = {
    ("M01", "R01"): (0x4000000000, ""),
    ("M01", "R05"): (0x4000000000, ""),
    ("M01", "C03"): (0x4000000000, ""),
    ("M01", "R04"): (0x4000000000, ""),
    ("M01", "R03"): (0x4000000000, ""),
    ("M02", "R01"): (0x4001000000, "Read"),
    ("M02", "R05"): (0x4001400000, "Read"),
    ("M02", "C03"): (0x4001000000, "Read"),
    ("M02", "R04"): (0x4001300000, "Read"),
    ("M02", "R03"): (0x4001200000, "Read"),
    ("M03", "R01"): (0x4004000000, "Read"),
    ("M03", "R05"): (0x4005000000, "Execute"),
    ("M03", "C03"): (0x4004000000, "Read"),
    ("M03", "R04"): (0x4004000000, "Read"),
    ("M03", "R03"): (0x4004000000, "Read"),
    ("M04", "R01"): (0x4008000000, "Read"),
    ("M04", "R05"): (0x4008000000, "Execute"),
    ("M04", "C03"): (0x4008000000, "Read"),
    ("M04", "R04"): (0x4008000000, "Read"),
    ("M04", "R03"): (0x4008000000, "Read"),
    ("M05", "R01"): (0x4010000000, "Read"),
    ("M05", "R05"): (0x4010000000, "Execute"),
    ("M05", "C03"): (0x4010000000, "Read"),
    ("M05", "R04"): (0x4010000000, "Read"),
    ("M05", "R03"): (0x4010000000, "Read"),
    ("M06", "R01"): (0x4001000000, "Read"),
    ("M06", "R02"): (0x4001100000, "Write"),
    ("M06", "C03"): (0x4001000000, "Read"),
    ("M06", "R04"): (0x4001300000, "Read"),
    ("M07", "R01"): (0x400D000000, "Write"),
    ("M07", "R03"): (0x400D200000, "Read"),
    ("M07", "C03"): (0x400D200000, "Read"),
    ("M07", "R02"): (0x400D000000, "Atomic"),
    ("M07", "R05"): (0x400D600180, "Execute"),
    ("M08", "R01"): (0x4001000000, "Read"),
    ("M08", "R05"): (0x4001400000, "Write"),
    ("M08", "C03"): (0x4001000000, "Read"),
    ("M08", "R04"): (0x4001300000, "Read"),
    ("M08", "R03"): (0x4001200000, "Read"),
}

ROI = {
    "W9": (0x4000000000, 0x4003001000),
    "W10": (0x4001000000, 0x4001700000),
    "W10S": (0x4001100000, 0x4001700000),
    "W11": (0x4004000000, 0x4006002000),
    "W12": (0x4008000000, 0x400A001000),
    "W13": (0x4010000000, 0x4010202000),
    "W14": (0x400C000000, 0x400D601000),
}

MODEL_CHANNEL = {"M01": 1, "M02": 2, "M03": 3, "M04": 4, "M05": 5,
                 "M06": 6, "M07": 7, "M08": 8}
ACTIVATION_KIND = {"M01": "mmu_fault_arm", "M02": "refill_pfn_corrupt"}
for _m in ("M03", "M04", "M05", "M06", "M07", "M08"):
    ACTIVATION_KIND[_m] = "mmu_fault_activate"

STATUS_LOCK = threading.Lock()


def load_conditions():
    with open(COND_FILE) as fh:
        return json.load(fh)


def load_ctx_map():
    with open(CTX_FILE) as fh:
        return json.load(fh)


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_terminal(path):
    lines = []
    try:
        with open(path, errors="replace") as fh:
            lines = [ln.rstrip("\n") for ln in fh]
    except OSError:
        pass
    return lines


def parse_trace(path):
    """Return a compact summary of a PROP-EVT stream."""
    import gzip
    kinds = {}
    selected = []
    summary = {}
    activations = []
    eligible_first = None
    total_lines = 0
    try:
        with gzip.open(path, "rt", errors="replace") as fh:
            for line in fh:
                if not line.startswith("PROP-EVT:"):
                    continue
                total_lines += 1
                kv = dict(re.findall(r"(\w+)=([^ ]*)", line))
                kind = kv.get("kind", "")
                kinds[kind] = kinds.get(kind, 0) + 1
                if kind == "mmu_eligible_selected":
                    selected.append(kv)
                if kind == "mmu_eligible_event" and eligible_first is None:
                    eligible_first = kv
                if kind == "mmu_eligible_summary":
                    summary = kv
                if kind in ("mmu_fault_activate", "mmu_fault_arm",
                            "refill_pfn_corrupt"):
                    activations.append(kv)
    except (OSError, EOFError) as exc:
        return {"error": str(exc), "kinds": kinds, "selected": selected,
                "summary": summary, "activations": activations,
                "eligible_first": eligible_first,
                "total_lines": total_lines}
    return {"kinds": kinds, "selected": selected, "summary": summary,
            "activations": activations, "eligible_first": eligible_first,
            "total_lines": total_lines}


def model_args(model, ctx, va, mode, asid, old_pfn, ordinal, prescan,
               m04_decoy=0):
    a = ["--mmu_fault_model", model, "--mmu_fault_enable", "true",
         "--mmu_eligible_event_index", str(ordinal),
         "--mmu_prescan", "true" if prescan else "false",
         "--mmu_m02_dram_lo", "0x80000000",
         "--mmu_m02_dram_hi", "0x100000000"]
    if model == "M01":
        a += ["--mmu_m01_va", hex(va), "--mmu_m01_asid", str(asid),
              "--mmu_m01_vmid", "0", "--mmu_m01_regime", "0",
              "--mmu_m01_security_state", "0", "--mmu_m01_n", "12"]
    elif model == "M02":
        a += ["--mmu_m02_va", hex(va), "--mmu_m02_old_pfn", hex(old_pfn),
              "--mmu_m02_xor_mask", "1"]
    else:
        n = 21 if model == "M05" else 12
        a += ["--mmu_target_va", hex(va), "--mmu_target_n", str(n)]
        if mode:
            a += ["--mmu_target_mode", mode]
        if model == "M03":
            a += ["--mmu_m03_candidate_asid", "-1"]
        elif model == "M04":
            a += ["--mmu_target_instance",
                  "itb" if ctx == "R05" else "dtb",
                  "--mmu_m04_decoy_pfn",
                  hex(m04_decoy) if m04_decoy else "0"]
        elif model == "M05":
            a += ["--mmu_target_instance", "l2_shared",
                  "--mmu_target_walk_level", "2",
                  "--mmu_fault_persistence", "entry_lifetime",
                  "--mmu_m05_decoy_va", "0x4010200000",
                  "--mmu_m05_decoy_table_base", "0"]
        elif model == "M06":
            a += ["--mmu_target_walk_level", "3"]
        elif model == "M07":
            a += ["--mmu_fault_persistence", "one_shot"]
        elif model == "M08":
            a += ["--mmu_m08_pa_xor_mask", "0x1000"]
    return a


def run_dir(run_id):
    return os.path.join(RUNS, run_id)


def manifest_path(run_id):
    return os.path.join(run_dir(run_id), "manifest.json")


def read_manifest(run_id):
    try:
        with open(manifest_path(run_id)) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def write_manifest(run_id, data):
    os.makedirs(run_dir(run_id), exist_ok=True)
    tmp = manifest_path(run_id) + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
    os.replace(tmp, manifest_path(run_id))


def execute(run_id, model, ctx, ordinal, prescan, asid, old_pfn,
            log, label_ctx=None, m04_decoy=0):
    """Invoke one gem5 run. Returns a manifest dict."""
    outdir = run_dir(run_id)
    if os.path.isdir(outdir) and os.listdir(outdir):
        old = read_manifest(run_id)
        if old and old.get("final"):
            return old
        shutil.rmtree(outdir)
    os.makedirs(os.path.join(outdir, "Trace"), exist_ok=True)
    os.makedirs(os.path.join(outdir, "Run_Log"), exist_ok=True)
    disk = os.path.join(outdir, "disk.img")
    subprocess.run(["cp", "--reflink=auto", DISK_TEMPLATE, disk],
                   check=True)
    rcs = os.path.join(RCS_DIR, "%s-%s.rcS" % (model, label_ctx or ctx))
    if not os.path.isfile(rcs):
        raise RuntimeError("missing rcS %s" % rcs)
    va, mode = TARGET[(model, ctx)]
    wl = {("W9",): "W9"}
    # workload id for the ROI: taken from the rcS header
    with open(rcs) as fh:
        head = fh.read(400)
    m = re.search(r"WorkloadID=(\S+)", head)
    workload = m.group(1) if m else "W10"
    lo, hi = ROI[workload]
    gem5_run = os.path.join(outdir, "run")
    cmd = [GEM5, "--outdir", gem5_run, CONFIG,
           "--kernel", KERNEL, "--disk", disk, "--bootloader", BOOTLOADER,
           "--cpu", "O3", "--restore-checkpoint", CHECKPOINT,
           "--readfile", rcs, "--chaos_propagation",
           "--prop_mmu_va_lo", hex(lo), "--prop_mmu_va_hi", hex(hi),
           "--prop_run_id", run_id, "--prop_sample_run_id", run_id,
           "--prop_mmu_trace", "--prop_write_log", "on"]
    cmd += model_args(model, ctx, va, mode, asid, old_pfn, ordinal, prescan,
                      m04_decoy=m04_decoy)
    cmd_path = os.path.join(outdir, "Run_Log", "command.txt")
    with open(cmd_path, "w") as fh:
        fh.write(" ".join(cmd) + "\n")
    stdout_path = os.path.join(outdir, "Run_Log", "gem5_stdout.log")
    t0 = time.time()
    timed_out = False
    with open(stdout_path, "w") as logf:
        try:
            proc = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT,
                                  timeout=1800)
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            rc = 124
            timed_out = True
            logf.write("\n[w5x3] TIMEOUT\n")
    elapsed = round(time.time() - t0, 1)
    evt = os.path.join(gem5_run, "prop_evt.txt.gz")
    term = os.path.join(gem5_run, "board.terminal")
    tr = parse_trace(evt) if os.path.isfile(evt) else {
        "error": "trace missing", "kinds": {}, "selected": [],
        "summary": {}, "activations": [], "total_lines": 0}
    terminal_lines = parse_terminal(term)
    # Copy the durable evidence out of gem5's outdir.
    trace_dst = os.path.join(outdir, "Trace", "prop_evt.txt.gz")
    if os.path.isfile(evt):
        shutil.copy2(evt, trace_dst)
    term_dst = os.path.join(outdir, "Run_Log", "board.terminal")
    if os.path.isfile(term):
        shutil.copy2(term, term_dst)
    stats_src = os.path.join(gem5_run, "stats.txt")
    if os.path.isfile(stats_src):
        shutil.copy2(stats_src, os.path.join(outdir, "Run_Log",
                                             "stats.txt"))
    # Disk images are reproducible from the template; keeping 160 of them
    # would exhaust the volume. Record the hash, then remove.
    disk_sha = sha256(disk)
    os.remove(disk)
    shutil.rmtree(gem5_run, ignore_errors=True)

    act_kind = ACTIVATION_KIND[model]
    activation_count = tr["kinds"].get(act_kind, 0)
    info = {
        "run_id": run_id, "model": model, "context": ctx,
        "ordinal": ordinal, "prescan": prescan, "asid": asid,
        "old_pfn": old_pfn, "m04_decoy": m04_decoy,
        "returncode": rc, "timed_out": timed_out,
        "elapsed_sec": elapsed, "gem5_sha256": GEM5_SHA,
        "rcs": os.path.relpath(rcs, ROOT), "rcs_sha256": sha256(rcs),
        "disk_sha256": disk_sha,
        "trace": os.path.relpath(trace_dst, ROOT),
        "trace_sha256": sha256(trace_dst) if os.path.isfile(trace_dst)
        else "",
        "terminal": os.path.relpath(term_dst, ROOT),
        "terminal_sha256": sha256(term_dst) if os.path.isfile(term_dst)
        else "",
        "terminal_lines": terminal_lines,
        "eligible_summary": tr["summary"],
        "eligible_selected": tr["selected"],
        "eligible_first": tr.get("eligible_first"),
        "kinds": tr["kinds"],
        "activation_count": activation_count,
        "total_events": tr["total_lines"],
        "trace_error": tr.get("error", ""),
        "started_utc": now(), "final": True,
    }
    write_manifest(run_id, info)
    log("done %s rc=%s act=%s N=%s elapsed=%ss" %
        (run_id, rc, activation_count,
         tr["summary"].get("eligible_total", "?"), elapsed))
    return info


GEM5_SHA = sha256(GEM5) if os.path.isfile(GEM5) else ""


def prescan(model, ctx, asid=None, old_pfn=None, tag="", run_id=None,
            log=None, label_ctx=None, m04_decoy=0):
    if log is None:
        log = globals()["log"]
    """Run the golden pre-scan / Control for one (M,C). Returns manifest."""
    if run_id is None:
        run_id = "PRESCAN-%s-%s%s" % (model, ctx, tag)
    old = read_manifest(run_id)
    if old and old.get("final") and old.get("returncode") == 0:
        return old
    if model == "M01" and asid is None:
        asid = -1
    if model == "M02" and old_pfn is None:
        old_pfn = M02_PFN_DEFAULT
    return execute(run_id, model, ctx, 1, True, asid, old_pfn, log,
                   label_ctx=label_ctx, m04_decoy=m04_decoy)


def ensure_control(cond, ctx_map, log):
    """Return (control manifest, N, asid, old_pfn). May run discovery."""
    model, ctx, ctrl = cond["ModelID"], cond["ControlContext"], cond["ControlID"]
    if ctx == "SPEC":
        return {"final": False, "returncode": -1,
                "eligible_summary": {"eligible_total": "0"}}, 0, None, None
    asid = None
    old_pfn = None
    if model == "M01":
        # Discover the real ASID from a permissive golden run, then rerun
        # the Control with the exact frozen key.
        disc = prescan(model, ctx, asid=-1, tag="-DISCOVER",
                       run_id="DISC-%s-%s" % (model, ctx),
                       label_ctx=cond["NewContext"])
        sel = disc.get("eligible_selected") or []
        first = disc.get("eligible_first") or (sel[0] if sel else None)
        if first:
            try:
                asid = int(first.get("asid", "-1"))
            except (TypeError, ValueError):
                asid = -1
        if asid is None or asid < 0:
            return disc, 0, None, None
        ctrl_m = prescan(model, ctx, asid=asid, run_id=ctrl,
                         label_ctx=cond["NewContext"])
    elif model == "M02":
        ctrl_m = prescan(model, ctx, old_pfn=old_pfn, run_id=ctrl,
                         label_ctx=cond["NewContext"])
        n = int((ctrl_m.get("eligible_summary") or {}).get(
            "eligible_total", 0) or 0)
        if n == 0:
            # The guest allocation may have shifted from the frozen
            # controls. Read the real target PFN from this run's own
            # no-fault output and retry with the same Where predicate.
            pfn = None
            for line in ctrl_m.get("terminal_lines") or []:
                m = re.search(r"target_pfn=0x([0-9a-fA-F]+)", line)
                if m:
                    pfn = int(m.group(1), 16)
                    break
            if pfn:
                old_pfn = pfn
                retry = prescan(model, ctx, old_pfn=old_pfn,
                                run_id=ctrl + "-PFN", tag="-PFN",
                                label_ctx=cond["NewContext"])
                rn = int((retry.get("eligible_summary") or {}).get(
                    "eligible_total", 0) or 0)
                if rn > 0:
                    write_manifest(ctrl, retry)
                    ctrl_m = retry
    elif model == "M04":
        ctrl_m = prescan(model, ctx, run_id=ctrl,
                         label_ctx=cond["NewContext"])
        n = int((ctrl_m.get("eligible_summary") or {}).get(
            "eligible_total", 0) or 0)
        if n == 0:
            decoy = None
            for line in ctrl_m.get("terminal_lines") or []:
                m = re.search(r"decoy_pfn=0x([0-9a-fA-F]+)", line)
                if m:
                    decoy = int(m.group(1), 16)
                    break
            if decoy:
                retry = prescan(model, ctx, run_id=ctrl + "-DECOY",
                                label_ctx=cond["NewContext"],
                                m04_decoy=decoy, tag="-DECOY")
                rn = int((retry.get("eligible_summary") or {}).get(
                    "eligible_total", 0) or 0)
                if rn > 0:
                    write_manifest(ctrl, retry)
                    ctrl_m = retry
                else:
                    ctrl_m = retry
    else:
        ctrl_m = prescan(model, ctx, run_id=ctrl,
                         label_ctx=cond["NewContext"])
    n = int((ctrl_m.get("eligible_summary") or {}).get(
        "eligible_total", 0) or 0)
    return ctrl_m, n, asid, old_pfn


def ceil_ordinal(p_num, p_den, n):
    return (p_num * n + p_den - 1) // p_den


def write_status(rows):
    with STATUS_LOCK:
        with open(STATUS_CSV, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


def log(msg):
    line = "[%s] %s" % (now(), msg)
    print(line, flush=True)
    with open(os.path.join(ROOT, "work", "when5x3.log"), "a") as fh:
        fh.write(line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--prescan", nargs=2, metavar=("MODEL", "CTX"))
    ap.add_argument("--fault", metavar="SAMPLE_ID")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--models", default="")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--faults-only", action="store_true")
    args = ap.parse_args()

    conditions = load_conditions()
    ctx_map = load_ctx_map()
    by_id = {c["NewSampleRunID"]: c for c in conditions}

    if args.status:
        for c in conditions:
            m = read_manifest(c["NewSampleRunID"])
            print(c["NewSampleRunID"], (m or {}).get("returncode", "?"),
                  (m or {}).get("activation_count", "?"))
        return

    if args.fault:
        c = by_id[args.fault]
        ctrl_id = c["ControlID"]
        ctrl = read_manifest(ctrl_id)
        if not ctrl:
            raise SystemExit("control not run: %s" % ctrl_id)
        n = int((ctrl.get("eligible_summary") or {}).get(
            "eligible_total", 0) or 0)
        num, den = {"T01": (1, 10), "T02": (1, 2), "T03": (9, 10)}[
            c["TimingID"]]
        ordinal = ceil_ordinal(num, den, n)
        info = execute(c["NewSampleRunID"], c["ModelID"],
                       c["ControlContext"], ordinal, False,
                       ctrl.get("asid"), ctrl.get("old_pfn"), log,
                       label_ctx=c["NewContext"],
                       m04_decoy=ctrl.get("m04_decoy", 0) or 0)
        print(json.dumps(info, indent=2)[:2000])
        return

    if args.prescan:
        model, ctx = args.prescan
        info = prescan(model, ctx)
        print(json.dumps(info, indent=2)[:3000])
        return

    # --all: controls first (they define N), then faults.
    models = [m for m in ("M01", "M02", "M03", "M04", "M05", "M06", "M07",
                          "M08") if not args.models or m in args.models]
    control_ctx = {}
    if args.faults_only:
        for c in conditions:
            key = (c["ModelID"], c["ControlContext"])
            if key in control_ctx:
                continue
            m = read_manifest(c["ControlID"]) or {}
            control_ctx[key] = (m, int((m.get("eligible_summary") or {}).get(
                "eligible_total", 0) or 0), m.get("asid"),
                m.get("old_pfn"))
        log("faults-only: loaded %d controls" % len(control_ctx))
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {}
        seen = set()
        for c in conditions:
            if args.faults_only or c["ModelID"] not in models:
                continue
            key = (c["ModelID"], c["ControlContext"])
            if key in seen or key in control_ctx:
                continue
            seen.add(key)
            futs[ex.submit(ensure_control, c, ctx_map, log)] = key
        for fut in as_completed(futs):
            key = futs[fut]
            try:
                ctrl, n, asid, pfn = fut.result()
                control_ctx[key] = (ctrl, n, asid, pfn)
                log("control %s-%s N=%d asid=%s pfn=%s" %
                    (key[0], key[1], n, asid, pfn))
            except Exception as exc:  # keep the campaign alive
                log("control FAILED %s: %s" % (key, exc))
    # Fault runs
    jobs = []
    for c in conditions:
        if c["ModelID"] not in models:
            continue
        key = (c["ModelID"], c["ControlContext"])
        if key not in control_ctx:
            continue
        ctrl, n, asid, pfn = control_ctx[key]
        num, den = {"T01": (1, 10), "T02": (1, 2), "T03": (9, 10)}[
            c["TimingID"]]
        if n < 3:
            log("SKIP %s: N=%d<3" % (c["NewSampleRunID"], n))
            continue
        ordinal = ceil_ordinal(num, den, n)
        jobs.append((c, ordinal, asid, pfn, ctrl.get("m04_decoy", 0) or 0))
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(execute, c["NewSampleRunID"], c["ModelID"],
                         c["ControlContext"], ordn, False, asid, pfn, log,
                         c["NewContext"], decoy): c
                for c, ordn, asid, pfn, decoy in jobs}
        for fut in as_completed(futs):
            c = futs[fut]
            try:
                fut.result()
            except Exception as exc:
                log("fault FAILED %s: %s" % (c["NewSampleRunID"], exc))
    log("campaign pass finished")


if __name__ == "__main__":
    main()
