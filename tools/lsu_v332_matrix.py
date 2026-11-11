#!/usr/bin/env python3
"""LSU v3.3.2 60-context fault/control matrix driver.

Runs one FAULT and one matched CONTROL per (model, R01-R05) context on the
frozen final binary, then records the observed injection identity, oracle,
terminal and raw artifact paths. Census-only: nothing is graded and no
formal identity is consumed.

Drivers:
  * run_pilot.py  -- A01, A03(control), FW02, FW05, SQ01, SQ03, SP05, DA04,
                     LP01, LQ04, MD04
  * direct gem5   -- A03 fault (bounded wall clock; the persistent stuck-at
                     fault can hang and run_pilot's trace conversion is too
                     expensive for a partial trace)
  * direct gem5   -- RP01 (run_replay_pilot does not drive the RP01 modes)

Usage:
  python3 tools/lsu_v332_matrix.py --models A01,RP01 --roles fault,control
  python3 tools/lsu_v332_matrix.py --models all --roles fault
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
RUN_PILOT = PLATFORM / "run_pilot.py"
GEM5 = ROOT / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/lsu_proxy.py"
WORKLOADS = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads"
DIRECTED = ROOT / "workloads/directed"
OUT_BASE = ROOT / "audit_v3_3_2/runs"
SUMMARY_CSV = ROOT / "audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final.csv"

MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05", "DA04",
          "LP01", "MD04", "LQ04", "RP01")

# Percentile ordinals measured by the v3.3.2 census on binary 070d68a6
# (v3.3.1 values reused where the workload and hook are unchanged).
# ROI is the per-model eligible-event window inside main; ordinals are the
# injector's global eligible ordinals.
CONTEXTS = {
    "A01":  dict(roi=(1040, 1234), n=195,  ordinals=[1059, 1098, 1137, 1176, 1215]),
    "A03":  dict(roi=(1040, 1234), n=195,  ordinals=[1059, 1098, 1137, 1176, 1215]),
    "FW02": dict(roi=(8, 67),      n=60,   ordinals=[13, 18, 30, 42, 54],
                 workload=DIRECTED / "sq_forward_w4v2"),
    "FW05": dict(roi=(1, 2000),    n=2000, ordinals=[200, 600, 1000, 1400, 1800]),
    "SQ01": dict(roi=(1006, 1133), n=128,  ordinals=[1018, 1044, 1069, 1095, 1121],
                 workload=WORKLOADS / "sq_reload_v3212"),
    "SQ03": dict(roi=(1009, 1136), n=128,  ordinals=[1021, 1047, 1072, 1098, 1124],
                 workload=WORKLOADS / "sq_reload_v3212"),
    "SP05": dict(roi=(940, 1067),  n=128,  ordinals=[952, 978, 1003, 1029, 1055],
                 workload=WORKLOADS / "sq_reload_v3212"),
    "DA04": dict(roi=(33, 1056),   n=1024, ordinals=[135, 340, 544, 749, 954]),
    "LP01": dict(roi=(886, 17525), n=16640, ordinals=[2549, 5877, 9205, 12533, 15861]),
    "MD04": dict(roi=(3, 10),      n=8,    ordinals=[3, 5, 6, 8, 10],
                 workload=DIRECTED / "md04_violations_v332"),
    "LQ04": dict(roi=(1, 5),       n=5,    ordinals=[1, 2, 3, 4, 5]),
    "RP01": dict(roi=(1, 255),     n=255,  ordinals=[26, 77, 128, 179, 230],
                 workload=DIRECTED / "replay_partial_v332",
                 seeds=[3135797961, 226489823, 1735144973, 2455796178,
                        3984724524]),
}

# Per-model special handling.
DIRECT = {"A03"}          # fault runs are direct + bounded
RP01 = "RP01"
A03_TIMEOUT = 30          # seconds of simulation before HANG is recorded
RP01_TIMEOUT = 90


def parse_kv(text: str) -> dict:
    out = {}
    for k, v in re.findall(r"([A-Za-z_]\w*)=([^;\s,]+)", text or ""):
        out.setdefault(k, v)
    return out


def read_jsonl(path: Path, wanted=None):
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(errors="replace").splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if wanted is None or d.get("event_type") in wanted:
            rows.append(d)
    return rows


def first_injection(outdir: Path):
    for ev in read_jsonl(outdir / "trace_v31.jsonl", {"injection"}):
        detail = ev.get("detail") or ""
        kv = parse_kv(detail)
        row = {"seq": ev.get("dyn_inst_seq"), "detail": detail}
        for k in ("pc", "vaddr", "va", "addr", "pa", "store_seq", "load_seq",
                  "eligible_ordinal", "dyn_inst_seq", "lq_entry_id",
                  "entry_generation", "request_id"):
            if k in kv:
                row[k] = kv[k]
        return row
    return None


def parse_addrpath_log(path: Path) -> dict:
    info = {"stream_rows": 0, "first_activation": None,
            "first_affected": None, "capped": False, "injections": 0,
            "last_line": None}
    if not path.exists():
        return info
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("A03_ACTIVATION:") and info["first_activation"] is None:
            info["first_activation"] = line
        elif line.startswith("A03_STREAM:"):
            info["stream_rows"] += 1
            kv = parse_kv(line)
            if kv.get("affected") == "1" and info["first_affected"] is None:
                info["first_affected"] = line
        elif line.startswith("A03_STUCK_LIFECYCLE:"):
            info["lifecycle"] = line
        elif line.startswith("A03_LOG_CAPPED:"):
            info["capped"] = True
        elif "faults_injected:" in line:
            info["injections"] += 1
            info["last_line"] = line
    return info


def parse_rp01_stdout(path: Path) -> dict:
    info = {"eligible": 0, "skips": 0, "watchdog": False,
            "first_eligible": None, "first_skip": None, "checksum": None}
    if not path.exists():
        return info
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("RP01_ELIGIBLE"):
            info["eligible"] += 1
            if info["first_eligible"] is None:
                info["first_eligible"] = line
        elif line.startswith("RP01_SKIP_REPLAY"):
            info["skips"] += 1
            if info["first_skip"] is None:
                info["first_skip"] = line
        elif "CHAOS_RP01_WATCHDOG" in line:
            info["watchdog"] = True
        m = re.search(r"checksum=0x([0-9a-fA-F]+)", line)
        if m:
            info["checksum"] = m.group(1)
    return info


def run_pilot_cmd(model, ctx_idx, ordinal, outdir, role, workload):
    cmd = [sys.executable, str(RUN_PILOT), "--model", model,
           "--context-index", str(ctx_idx),
           "--event-ordinal", str(ordinal),
           "--pilot-id", outdir.name,
           "--outdir", str(outdir),
           "--timeout", "180"]
    if workload:
        cmd += ["--workload", str(workload)]
    if role == "control":
        cmd += ["--probability", "0.0"]
    return cmd


def run_direct(cmd_base, outdir, timeout):
    outdir.mkdir(parents=True, exist_ok=True)
    # Drop any dry-run outdir token and inject ours right after the binary.
    cmd = [c for c in cmd_base if not c.startswith("--outdir=")]
    cmd.insert(1, f"--outdir={outdir}")
    (outdir / "command.txt").write_text("\n".join(cmd) + "\n")
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              timeout=timeout)
        rc, out, err = proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        rc = 124
        out = (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (exc.stderr or b"").decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
    (outdir / "stdout.log").write_text(out)
    (outdir / "stderr.log").write_text(err)
    return {"cmd": cmd, "exit_code": rc, "timed_out": timed_out,
            "elapsed": round(time.time() - started, 3)}


def dry_run_command(model, ctx_idx, ordinal, role, workload, outdir):
    cmd = run_pilot_cmd(model, ctx_idx, ordinal, outdir, role, workload)
    cmd.append("--dry-run")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"dry-run failed: {proc.stderr[-500:]}")
    return proc.stdout.strip().split()


def run_context(model, ctx_idx, role):
    spec = CONTEXTS[model]
    ordinal = spec["ordinals"][ctx_idx - 1]
    seed = spec.get("seeds", [None] * 5)[ctx_idx - 1]
    workload = spec.get("workload")
    tag = f"{model}-R{ctx_idx:02d}-{role}"
    outdir = OUT_BASE / tag
    if outdir.exists():
        subprocess.run(["rm", "-rf", str(outdir)])
    outdir.mkdir(parents=True, exist_ok=True)

    summary = {"model": model, "context": f"R{ctx_idx:02d}",
               "ctx_index": ctx_idx, "role": role, "ordinal": ordinal,
               "seed": seed, "workload": str(workload) if workload else None,
               "outdir": str(outdir), "binary": str(GEM5),
               "binary_sha": None}

    if model == RP01:
        base = [str(GEM5), f"--outdir={outdir}", str(CONFIG),
                f"--cmd={spec['workload']}", "--cpu", "O3",
                "--variant", "B0", "--probability",
                "1.0" if role == "fault" else "0.0",
                "--chaos_propagation",
                "--prop_trace_file", "prop_trace.csv.gz"]
        if role == "fault":
            base += ["--chaos_lsqfwd", "--lsq_struct_mode", "rp01_skip_replay",
                     "--max_faults", "1", "--rng_seed", str(seed),
                     "--rp01_event_ordinal", str(ordinal),
                     "--rp01_watchdog_cycles", "500000000"]
        info = run_direct(base, outdir, RP01_TIMEOUT)
        parsed = parse_rp01_stdout(outdir / "stdout.log")
        summary.update(info)
        summary["rp01"] = parsed
        summary["injection_count"] = parsed["skips"]
        summary["terminal"] = ("HANG" if info["timed_out"] or parsed["watchdog"]
                               else ("COMPLETED" if info["exit_code"] == 0
                                     else "CRASH"))
        summary["oracle"] = (parsed["checksum"] == "f3b1c554273d23f7")
    elif model in DIRECT:
        if role == "fault":
            base = dry_run_command(model, ctx_idx, ordinal, role, workload, outdir)
            # The A03 fault is persistent and may not terminate; do not pay
            # the full-trace conversion, run gem5 directly and keep raw logs.
            base = [c for c in base if not c.startswith("--outdir=")]
            info = run_direct(base, outdir, A03_TIMEOUT)
            parsed = parse_addrpath_log(outdir / "addrpath_injections.log")
            summary.update(info)
            summary["a03"] = parsed
            summary["injection_count"] = parsed["injections"]
            summary["terminal"] = ("HANG" if info["timed_out"]
                                   else ("COMPLETED" if info["exit_code"] == 0
                                         else "CRASH"))
            # The oracle is absent on a partial trace; parse what exists.
            m = re.search(r"checksum=0x([0-9a-fA-F]+)",
                          (outdir / "stdout.log").read_text(errors="replace"))
            summary["oracle"] = bool(m and m.group(1) == "728e604ffcec539d")
        else:
            cmd = run_pilot_cmd(model, ctx_idx, ordinal, outdir, role, workload)
            proc = subprocess.run(cmd, cwd=ROOT, capture_output=True,
                                  text=True, timeout=300)
            summary["cmd"] = cmd
            summary["exit_code"] = proc.returncode
            summary["injection_count"] = 0
            meta = outdir / "pilot_meta.json"
            if meta.exists():
                m = json.load(open(meta))
                summary["injection_count"] = m.get("injection_count")
                summary["oracle"] = m.get("oracle_pass")
                summary["terminal"] = m.get("terminal")
    else:
        cmd = run_pilot_cmd(model, ctx_idx, ordinal, outdir, role, workload)
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              timeout=400)
        summary["cmd"] = cmd
        summary["exit_code"] = proc.returncode
        meta_path = outdir / "pilot_meta.json"
        if meta_path.exists():
            meta = json.load(open(meta_path))
            summary["injection_count"] = meta.get("injection_count")
            summary["oracle"] = meta.get("oracle_pass")
            summary["terminal"] = meta.get("terminal")
            summary["elapsed"] = meta.get("elapsed_seconds")
            summary["injection_events"] = meta.get("injection", {}).get("events")
            summary["trace_completeness"] = (meta.get("trace") or {}).get(
                "completeness")
        inj = first_injection(outdir)
        if inj:
            summary["first_injection"] = inj

    # Common binary identity.
    import hashlib
    h = hashlib.sha256()
    with open(GEM5, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    summary["binary_sha"] = h.hexdigest()

    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="all")
    ap.add_argument("--roles", default="fault,control")
    ap.add_argument("--contexts", default="1,2,3,4,5")
    ap.add_argument("--out-csv", default=str(SUMMARY_CSV))
    args = ap.parse_args(argv)
    models = list(MODELS) if args.models == "all" else args.models.split(",")
    roles = args.roles.split(",")
    ctxs = [int(x) for x in args.contexts.split(",")]
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for model in models:
        if model not in CONTEXTS:
            print(f"skip unknown model {model}", file=sys.stderr)
            continue
        for ctx in ctxs:
            for role in roles:
                print(f"== {model} R{ctx:02d} {role}", flush=True)
                try:
                    rows.append(run_context(model, ctx, role))
                except Exception as exc:  # keep the matrix going; record it
                    row = {"model": model, "context": f"R{ctx:02d}",
                           "role": role, "error": repr(exc)}
                    rows.append(row)
                    print(f"   ERROR {exc!r}", file=sys.stderr)
    write_csv(rows, Path(args.out_csv))
    print(f"wrote {args.out_csv} ({len(rows)} rows)")
    return 0


def write_csv(rows, path=SUMMARY_CSV):
    keys = ["model", "context", "role", "ordinal", "seed", "workload",
            "injection_count", "oracle", "terminal", "exit_code",
            "timed_out", "elapsed", "binary_sha", "outdir", "error"]
    with open(SUMMARY_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    sys.exit(main())
