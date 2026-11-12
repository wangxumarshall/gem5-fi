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
import fcntl
import json
import os
import re
import shlex
import subprocess
import sys
import time
from collections import Counter
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
RUN_PILOT = PLATFORM / "run_pilot.py"
GEM5 = ROOT / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/lsu_proxy.py"
WORKLOADS = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads"
DIRECTED = ROOT / "workloads/directed"
OUT_BASE = ROOT / "audit_v3_3_2/runs"
# v3.3.3: the matrix writes its own RAW CSV; the curated FINAL CSV is written
# by tools/lsu_v332_report.py. The two paths must never collide (the _J file
# is the v3.3.2 evidence of that collision; it is history and stays untouched).
SUMMARY_CSV = ROOT / "audit_v3_3_2/controls/LSU_Fault_Control_Pair_RAW.csv"
LOCK_FILE = ROOT / "audit_v3_3_2/controls/.lsu_v332_matrix.lock"

MODELS = ("A01", "A03", "FW02", "FW05", "SQ01", "SQ03", "SP05", "DA04",
          "LP01", "MD04", "LQ04", "RP01")

# Percentile ordinals measured by the v3.3.2 census on binary 070d68a6
# (v3.3.1 values reused where the workload and hook are unchanged).
# ROI is the per-model eligible-event window inside main; ordinals are the
# injector's global eligible ordinals.
CONTEXTS = {
    # v3.3.3 re-census after the PRE retry exclusion (L-A01): the main-loop
    # eligible window on the fixed stream is 1040-1222 (N=183); the five
    # percentile ordinals are measured from that window. SampleRunID/Seed
    # unchanged; the v3.3.2 1040-1234/195 set is retained as history.
    "A01":  dict(roi=(1040, 1222), n=183,  ordinals=[1058, 1094, 1131, 1168, 1204]),
    "A03":  dict(roi=(1040, 1222), n=183,  ordinals=[1058, 1094, 1131, 1168, 1204],
                 workload=WORKLOADS / "agu_addrmodes",
                 seeds=[663646247, 1626885462, 110775855, 2766846323,
                        1156093484]),
    "FW02": dict(roi=(8, 67),      n=60,   ordinals=[13, 25, 37, 49, 61],
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
    "LQ04": dict(roi=(1, 5),       n=5,    ordinals=[1, 2, 3, 4, 5],
                 workload=WORKLOADS / "lq_lifetime_ordinal"),
    "RP01": dict(roi=(1, 255),     n=255,  ordinals=[26, 77, 128, 179, 230],
                 workload=DIRECTED / "replay_partial_v332",
                 seeds=[3135797961, 226489823, 1735144973, 2455796178,
                        3984724524]),
}

# Per-model special handling.
DIRECT = {"A03"}          # fault runs are direct + bounded
RP01 = "RP01"
A03_TIMEOUT = 300         # wall-clock backstop (v3.3.2 used 30 s and cut the
                          # post-oracle sim before the log/exit callbacks)
# In-simulator A03 watchdog budget after activation, in CPU cycles.
# The B0 clock is 385 ticks/cycle; the matched control completes in
# 19,642,700 ticks (~51k cycles). 1,000,000 cycles = ~385M ticks, about
# 20x the control's whole execution, so the watchdog fires only well after
# the workload's final put_hex on a real post-oracle exit hang. (The first
# v3.3.3 smoke used 1e9 cycles = ~385G ticks and never fired before the
# 300 s wall backstop; that was a unit error, not a source defect.)
A03_WATCHDOG_CYCLES = 1_000_000
A03_GOLDEN = "728e604ffcec539d"
RP01_TIMEOUT = 300
RP01_DEADLINE_CYCLES = 20_000_000   # value passed to --rp01_watchdog_cycles
RP01_GOLDEN = "f3b1c554273d23f7"

# Injector mount surface (docs/superpowers/plans/2026-11-12 Task 5).
MOUNT_FLAGS = ("--chaos_lsqfwd", "--chaos_addrpath", "--chaos_l1dfwd",
               "--chaos_lq04", "--chaos_md04")
# An explicit suppression token (never present in v3.3.2) is distinct from
# --probability 0.0: it disables an otherwise-active mount without changing
# the global probability semantics.
SUPPRESS_FLAGS = ("--chaos_suppress", "--injector_suppress",
                  "--suppress_injectors")
PROOFS = ("INJECTOR_ABSENT", "MOUNTED_BUT_DISABLED",
          "MOUNTED_BUT_SUPPRESSED", "MOUNTED_BUT_ACTIVE",
          "NO_COMMAND_EVIDENCE")


def read_command(outdir: Path) -> str:
    """The executed command, as written by the driver into command.txt."""
    p = Path(outdir) / "command.txt"
    if not p.exists():
        return ""
    return " ".join(p.read_text(errors="replace").split())


def _option(tokens: list[str], name: str):
    for i, tok in enumerate(tokens[:-1]):
        if tok == name:
            return tokens[i + 1]
    for tok in tokens:
        if tok.startswith(name + "="):
            return tok.split("=", 1)[1]
    return None


def classify_control(command_text: str) -> dict:
    """Classify a control run from its EXECUTED command.txt (not run_pilot argv).

    * no --chaos_<injector> mount      -> INJECTOR_ABSENT
    * an explicit suppression token    -> MOUNTED_BUT_SUPPRESSED
    * --probability 0.0 (or an explicit --md04_probability 0.0)
                                       -> MOUNTED_BUT_DISABLED
    * mounted and enabled             -> MOUNTED_BUT_ACTIVE (a control misfire
      candidate: the report must reject it)
    """
    if isinstance(command_text, (list, tuple)):
        command_text = " ".join(str(t) for t in command_text)
    tokens = shlex.split(command_text or "")
    mounts = [flag for flag in MOUNT_FLAGS if flag in tokens]
    suppress = [flag for flag in SUPPRESS_FLAGS if flag in tokens]
    suppress += [tok for tok in tokens
                 if (tok.startswith("--suppress_")
                     or tok.endswith("_suppress"))]
    raw_prob = _option(tokens, "--probability")
    raw_md04 = _option(tokens, "--md04_probability")
    probability = float(raw_prob) if raw_prob is not None else None
    md04_probability = float(raw_md04) if raw_md04 is not None else None
    if not command_text:
        proof = "NO_COMMAND_EVIDENCE"
    elif not mounts:
        proof = "INJECTOR_ABSENT"
    elif suppress:
        proof = "MOUNTED_BUT_SUPPRESSED"
    elif ((probability is not None and probability == 0.0)
          or (md04_probability is not None and md04_probability == 0.0)):
        proof = "MOUNTED_BUT_DISABLED"
    else:
        proof = "MOUNTED_BUT_ACTIVE"
    return {
        "proof": proof,
        "mounts": mounts,
        "suppression_flags": sorted(set(suppress)),
        "probability": probability,
        "md04_probability": md04_probability,
        "source": "command.txt" if command_text else "missing",
    }


def classify_controls(runs_dir: Path | None = None) -> dict:
    """Count the zero-injection proofs over every <MODEL>-R<NN>-control dir."""
    runs_dir = runs_dir or OUT_BASE
    counts: Counter = Counter()
    for outdir in sorted(Path(runs_dir).glob("*-control")):
        counts[classify_control(read_command(outdir))["proof"]] += 1
    return dict(counts)


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
    """Parse the A03 addrpath log honestly (L-A03).

    ``injected_applications`` is the last ``FUNNEL: ... injected=N`` line (the
    real fault-application count; fallback = number of ``affected=1`` stream
    rows). ``A03_LOG_CAPPED`` is a separate logging fact and is NEVER used as
    an injection count. ``watchdog_expired`` records the in-simulator
    ``A03_WATCHDOG_EXPIRED`` marker (Task 3).
    """
    info = {"stream_rows": 0, "affected_rows": 0,
            "injected_applications": None, "first_activation": None,
            "first_affected": None, "capped": False,
            "watchdog_expired": False, "last_funnel": None,
            "log_line_injections": 0, "lifecycle": None}
    if not path.exists():
        return info
    for line in path.read_text(errors="replace").splitlines():
        if line.startswith("A03_ACTIVATION:") and info["first_activation"] is None:
            info["first_activation"] = line
        elif line.startswith("A03_STREAM:"):
            info["stream_rows"] += 1
            kv = parse_kv(line)
            if kv.get("affected") == "1":
                info["affected_rows"] += 1
                if info["first_affected"] is None:
                    info["first_affected"] = line
        elif line.startswith("A03_STUCK_LIFECYCLE:"):
            info["lifecycle"] = line
        elif line.startswith("A03_LOG_CAPPED:"):
            info["capped"] = True
        elif "A03_WATCHDOG_EXPIRED" in line:
            info["watchdog_expired"] = True
        elif line.startswith("FUNNEL:"):
            kv = parse_kv(line)
            info["last_funnel"] = line
            if "injected" in kv:
                try:
                    info["injected_applications"] = int(kv["injected"])
                except ValueError:
                    pass
        elif "faults_injected:" in line:
            # A per-line counter inside the generic injection log — kept only
            # as diagnostic, never promoted to injection_count.
            info["log_line_injections"] += 1
    if info["injected_applications"] is None:
        info["injected_applications"] = info["affected_rows"]
    return info


def parse_bare_checksum(text: str):
    """The workload's final bare 16-hex stdout line (no 0x / no prefix)."""
    matches = re.findall(r"^\s*([0-9a-fA-F]{16})\s*$", text or "",
                         re.MULTILINE)
    return matches[-1].lower() if matches else None


def a03_terminal(checksum, watchdog_expired: bool, timed_out: bool,
                 exit_code) -> dict:
    """Evidence-based A03 terminal (L-A04; researcher-approved labels).

    * checksum present and different -> SDC / ORACLE_FAIL
      (qualifier POST_ORACLE_SIM_HANG when the in-sim watchdog fired after the
      print — the oracle verdict is never relabelled as a hang)
    * checksum present and equal     -> MASKED (oracle PASS)
    * no checksum + watchdog fired   -> HANG_WATCHDOG
    * no checksum, no watchdog       -> HANG (external timeout) / CRASH
    """
    if checksum is not None:
        oracle_pass = checksum == A03_GOLDEN
        return {
            "checksum": checksum,
            "oracle_pass": oracle_pass,
            "terminal": "MASKED" if oracle_pass else "SDC",
            "terminal_qualifier": ("POST_ORACLE_SIM_HANG"
                                   if watchdog_expired else None),
            "terminal_reason": ("ORACLE_PASS" if oracle_pass
                                else "ORACLE_FAIL"),
        }
    if watchdog_expired:
        return {"checksum": None, "oracle_pass": None,
                "terminal": "HANG_WATCHDOG", "terminal_qualifier": None,
                "terminal_reason": "WATCHDOG_EXPIRED_NO_CHECKSUM"}
    if timed_out:
        return {"checksum": None, "oracle_pass": None, "terminal": "HANG",
                "terminal_qualifier": None,
                "terminal_reason": "NO_CHECKSUM_EXTERNAL_TIMEOUT"}
    if exit_code not in (0, None):
        return {"checksum": None, "oracle_pass": None, "terminal": "CRASH",
                "terminal_qualifier": None,
                "terminal_reason": f"NO_CHECKSUM_EXIT_{exit_code}"}
    return {"checksum": None, "oracle_pass": None, "terminal": "UNRESOLVED",
            "terminal_qualifier": None, "terminal_reason": "NO_CHECKSUM"}


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
    bare = parse_bare_checksum(
        "\n".join(ln for ln in
                  path.read_text(errors="replace").splitlines()
                  if not ln.startswith("RP01_")))
    if info["checksum"] is None and bare is not None:
        info["checksum"] = bare
    return info


def parse_rp01_evidence(outdir: Path) -> dict:
    """RP01 terminal from the model log, not stdout only (L-A07).

    ``CHAOS_RP01_WATCHDOG=EXPIRED`` is written to lsq_fwd_injections.log and
    the fatal line to stderr; v3.3.2 parsed stdout only and recorded
    CRASH/watchdog=false. The raw fatal location is retained verbatim.
    """
    info = parse_rp01_stdout(outdir / "stdout.log")
    marker_line = None
    raw_path = None
    for name in ("lsq_fwd_injections.log", "stderr.log", "stdout.log"):
        p = outdir / name
        if not p.exists():
            continue
        for line in p.read_text(errors="replace").splitlines():
            if ("CHAOS_RP01_WATCHDOG" in line):
                info["watchdog"] = True
                if marker_line is None:
                    marker_line = line.strip()
                    raw_path = str(p)
                break
    info["watchdog_marker"] = marker_line
    info["raw_fatal_path"] = raw_path
    info["deadline_cycles"] = RP01_DEADLINE_CYCLES
    info["no_checksum"] = info.get("checksum") is None
    info["oracle_pass"] = (info.get("checksum") == RP01_GOLDEN)
    if info["watchdog"]:
        info["terminal"] = "HANG_WATCHDOG"
        info["terminal_reason"] = "INTERNAL_WATCHDOG_DEADLINE"
    elif info.get("checksum") is not None:
        info["terminal"] = "SDC" if not info["oracle_pass"] else "MASKED"
        info["terminal_reason"] = ("ORACLE_FAIL" if not info["oracle_pass"]
                                   else "ORACLE_PASS")
    else:
        info["terminal"] = "UNRESOLVED"
        info["terminal_reason"] = "NO_CHECKSUM_NO_WATCHDOG"
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


def build_a03_fault_cmd(ordinal, seed, workload, outdir) -> list[str]:
    """A03 direct fault run: same flags as run_pilot's A03 mount + watchdog."""
    return [str(GEM5), f"--outdir={outdir}", str(CONFIG),
            f"--cmd={workload}", "--cpu", "O3", "--variant", "B0",
            "--probability", "1.0", "--chaos_propagation",
            "--prop_trace_file", "prop_trace.csv.gz",
            "--chaos_addrpath", "--agu_pre_mode", "a03_bit3_stuck0_load",
            "--addrpath_lsu_tier", "F5", "--addrpath_max_faults", "0",
            "--addrpath_warmup_events", "0",
            "--addrpath_rng_seed", str(seed),
            "--addrpath_event_ordinal", str(ordinal),
            "--addrpath_watchdog_cycles", str(A03_WATCHDOG_CYCLES)]


def build_rp01_cmd(role, ordinal, seed, workload, outdir) -> list[str]:
    base = [str(GEM5), f"--outdir={outdir}", str(CONFIG),
            f"--cmd={workload}", "--cpu", "O3", "--variant", "B0",
            "--probability", "1.0" if role == "fault" else "0.0",
            "--chaos_propagation",
            "--prop_trace_file", "prop_trace.csv.gz"]
    if role == "fault":
        base += ["--chaos_lsqfwd", "--lsq_struct_mode", "rp01_skip_replay",
                 "--max_faults", "1", "--rng_seed", str(seed),
                 "--rp01_event_ordinal", str(ordinal),
                 "--rp01_watchdog_cycles", str(RP01_DEADLINE_CYCLES)]
    return base


def planned_command(model, ctx_idx, role, outdir) -> list[str]:
    """The command this matrix row would execute (pure; no subprocess)."""
    spec = CONTEXTS[model]
    ordinal = spec["ordinals"][ctx_idx - 1]
    seed = spec.get("seeds", [None] * 5)[ctx_idx - 1]
    workload = spec.get("workload")
    if model == RP01:
        return build_rp01_cmd(role, ordinal, seed, workload, outdir)
    if model in DIRECT and role == "fault":
        workload = workload or (WORKLOADS / "agu_addrmodes")
        return build_a03_fault_cmd(ordinal, seed, workload, outdir)
    return run_pilot_cmd(model, ctx_idx, ordinal, outdir, role, workload)


def _sha256(path: Path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def injector_meta(command_text: str, probability) -> dict:
    """Mount/attach/gate provenance recorded in pilot_meta.json."""
    cls = classify_control(command_text)
    gate = ("probability" if probability is not None and probability > 0
            else "probability_zero")
    if "--chaos_md04" in cls["mounts"]:
        gate = "md04_probability"
    elif any(m in cls["mounts"]
             for m in ("--chaos_lsqfwd", "--chaos_addrpath", "--chaos_lq04")):
        # These models select their target by an eligible-event ordinal; the
        # ordinal is the effective gate for the F0/F6 family.
        gate = "ordinal"
    return {
        "mount_flags": cls["mounts"],
        "mounted": bool(cls["mounts"]),
        "probability": probability,
        "md04_probability": cls["md04_probability"],
        "gate": gate,
        "gate_enabled": (bool(cls["mounts"])
                         and cls["probability"] != 0.0
                         and cls["md04_probability"] != 0.0
                         and not cls["suppression_flags"]),
        "suppression_flags": cls["suppression_flags"],
        "zero_injection_proof": cls["proof"],
        "attach_mechanism": "self_attach_at_startup",
    }


def write_direct_artifacts(model, role, outdir, command, workload, ordinal,
                           seed, info, terminal, oracle_pass, checksum=None,
                           extra=None) -> dict:
    """Direct-driver runs must carry manifest/oracle/pilot_meta (v3.3.3)."""
    outdir = Path(outdir)
    golden_path = Path(workload).with_suffix(".golden")
    expected = (golden_path.read_text().strip()
                if golden_path.exists() else None)
    oracle_log = "ORACLE_SKIPPED: no .golden for workload"
    if expected is not None:
        proc = subprocess.run(
            [sys.executable, str(WORKLOADS / "oracle_check.py"), expected,
             str(outdir / "stdout.log")],
            capture_output=True, text=True)
        oracle_log = proc.stdout + proc.stderr
        if oracle_pass is None:
            oracle_pass = proc.returncode == 0
    (outdir / "oracle.log").write_text(oracle_log)

    binary_sha = _sha256(GEM5)
    manifest = {
        "schema": "LSU_V333_DIRECT_MANIFEST",
        "pilot_id": outdir.name,
        "model": model,
        "role": role,
        "driver": "matrix_direct",
        "binary": str(GEM5),
        "binary_sha256": binary_sha,
        "config": str(CONFIG),
        "config_sha256": _sha256(CONFIG),
        "workload": str(workload),
        "workload_sha256": _sha256(Path(workload)),
        "golden": expected,
        "event_ordinal": ordinal,
        "seed": seed,
        "command": command,
        "note": ("direct-driver run: no Excel SampleRunID is claimed here; "
                 "identity columns are populated by the matrix's authoritative "
                 "sample binding, not invented"),
    }
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    meta = {
        "pilot_id": outdir.name,
        "model": model,
        "run_role": "CONTROL" if role == "control" else "FAULT",
        "driver": "matrix_direct",
        "seed": seed,
        "workload": str(workload),
        "event_ordinal": ordinal,
        "command": command,
        "exit_code": info.get("exit_code"),
        "timed_out": info.get("timed_out"),
        "elapsed_seconds": info.get("elapsed"),
        "oracle_expected": expected,
        "oracle_source": "workload_golden" if expected else "none",
        "oracle_pass": oracle_pass,
        "checksum": checksum,
        "terminal": terminal,
        "terminal_state": terminal,
        "terminal_reason": (extra or {}).get("terminal_reason"),
        "terminal_qualifier": (extra or {}).get("terminal_qualifier"),
        "injection_count": (extra or {}).get("injection_count"),
        "injector": injector_meta(" ".join(map(str, command)),
                                  (extra or {}).get(
                                      "probability",
                                      1.0 if role == "fault" else 0.0)),
        "classification": {
            "terminal_state": terminal,
            "terminal_state_reason": (extra or {}).get("terminal_reason"),
            "oracle_outcome": ("PASS" if oracle_pass else
                               "FAIL" if oracle_pass is False else "n/a"),
        },
    }
    meta.update(extra or {})
    (outdir / "pilot_meta.json").write_text(json.dumps(meta, indent=2))
    return {"oracle_pass": oracle_pass, "manifest": manifest, "meta": meta}


@contextmanager
def matrix_lock(path: Path = LOCK_FILE):
    """Serialize matrix run sets (L-D14): concurrent writers cannot clobber."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(path, "w")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.write(str(os.getpid()))
        fh.flush()
        yield fh
    finally:
        fcntl.flock(fh, fcntl.LOCK_UN)
        fh.close()


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


def _seed_from_command(outdir: Path):
    text = read_command(outdir)
    m = re.search(r"--[A-Za-z0-9_]*rng_seed(?:\s+|=)(\d+)", text)
    return int(m.group(1)) if m else None


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
        cmd = build_rp01_cmd(role, ordinal, seed, workload, outdir)
        info = run_direct(cmd, outdir, RP01_TIMEOUT)
        parsed = parse_rp01_evidence(outdir)
        extra = {"terminal_reason": parsed.get("terminal_reason"),
                 "injection_count": parsed["skips"],
                 "probability": 1.0 if role == "fault" else 0.0,
                 "watchdog": parsed["watchdog"],
                 "deadline_cycles": parsed["deadline_cycles"],
                 "no_checksum": parsed["no_checksum"],
                 "raw_fatal_path": parsed["raw_fatal_path"]}
        direct = write_direct_artifacts(
            model, role, outdir, cmd, workload, ordinal, seed, info,
            parsed["terminal"], parsed.get("oracle_pass"),
            parsed.get("checksum"), extra)
        summary.update(info)
        summary["rp01"] = parsed
        summary["injection_count"] = parsed["skips"]
        summary["terminal"] = parsed["terminal"]
        summary["terminal_reason"] = parsed.get("terminal_reason")
        summary["watchdog"] = parsed["watchdog"]
        summary["deadline_cycles"] = parsed["deadline_cycles"]
        summary["no_checksum"] = parsed["no_checksum"]
        summary["raw_fatal_path"] = parsed["raw_fatal_path"]
        summary["checksum"] = parsed.get("checksum")
        summary["oracle"] = direct["oracle_pass"]
    elif model in DIRECT and role == "fault":
        workload = workload or (WORKLOADS / "agu_addrmodes")
        summary["workload"] = str(workload)
        cmd = build_a03_fault_cmd(ordinal, seed, workload, outdir)
        info = run_direct(cmd, outdir, A03_TIMEOUT)
        parsed = parse_addrpath_log(outdir / "addrpath_injections.log")
        stdout_text = (outdir / "stdout.log").read_text(errors="replace")
        checksum = parse_bare_checksum(stdout_text)
        # Task 3 may emit the marker on stdout (after the addrpath log flush);
        # accept either location.
        if "A03_WATCHDOG_EXPIRED" in stdout_text:
            parsed["watchdog_expired"] = True
        term = a03_terminal(checksum, parsed["watchdog_expired"],
                            info["timed_out"], info["exit_code"])
        extra = {"terminal_reason": term["terminal_reason"],
                 "terminal_qualifier": term["terminal_qualifier"],
                 "injection_count": parsed["injected_applications"],
                 "a03_log_capped": parsed["capped"],
                 "watchdog_expired": parsed["watchdog_expired"],
                 "watchdog_cycles": A03_WATCHDOG_CYCLES,
                 "probability": 1.0}
        direct = write_direct_artifacts(
            model, role, outdir, cmd, workload, ordinal, seed, info,
            term["terminal"], term["oracle_pass"], checksum, extra)
        summary.update(info)
        summary["a03"] = parsed
        summary["injection_count"] = parsed["injected_applications"]
        summary["a03_log_capped"] = parsed["capped"]
        summary["watchdog_expired"] = parsed["watchdog_expired"]
        summary["watchdog_cycles"] = A03_WATCHDOG_CYCLES
        summary["checksum"] = checksum
        summary["oracle"] = direct["oracle_pass"]
        summary["terminal"] = term["terminal"]
        summary["terminal_qualifier"] = term["terminal_qualifier"]
        summary["terminal_reason"] = term["terminal_reason"]
    else:
        cmd = run_pilot_cmd(model, ctx_idx, ordinal, outdir, role, workload)
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                              timeout=400)
        summary["cmd"] = cmd
        summary["exit_code"] = proc.returncode
        meta_path = outdir / "pilot_meta.json"
        meta = json.load(open(meta_path)) if meta_path.exists() else {}
        if meta:
            summary["injection_count"] = meta.get("injection_count")
            summary["oracle"] = meta.get("oracle_pass")
            summary["terminal"] = (meta.get("terminal")
                                   or (meta.get("classification") or {}).get(
                                       "terminal_state"))
            summary["terminal_reason"] = (meta.get("classification") or {}).get(
                "terminal_state_reason")
            summary["elapsed"] = meta.get("elapsed_seconds")
            summary["injection_events"] = meta.get("injection", {}).get("events")
            summary["trace_completeness"] = (meta.get("trace") or {}).get(
                "completeness")
            summary["seed"] = summary.get("seed") or meta.get("seed")
        inj = first_injection(outdir)
        if inj:
            summary["first_injection"] = inj

    # Common provenance population (L-D02/L-D04): seed, terminal, workload and
    # the executed FaultCommand all come from the run artifacts, never from a
    # re-derived argv.
    meta = {}
    if (outdir / "pilot_meta.json").exists():
        meta = json.load(open(outdir / "pilot_meta.json"))
    if summary.get("seed") is None:
        summary["seed"] = meta.get("seed") or _seed_from_command(outdir)
    if not summary.get("workload"):
        summary["workload"] = meta.get("workload")
    if not summary.get("terminal"):
        summary["terminal"] = ((meta.get("classification") or {}).get(
            "terminal_state") or "UNRESOLVED")
    if not summary.get("terminal_reason"):
        summary["terminal_reason"] = (meta.get("classification") or {}).get(
            "terminal_state_reason")
    command_text = read_command(outdir)
    summary["fault_command"] = command_text
    control = classify_control(command_text)
    summary["control_proof"] = control["proof"]
    summary["mount_evidence"] = control
    if role == "control" and summary.get("injection_count") is None:
        summary["injection_count"] = 0
    if summary.get("binary_sha") is None:
        summary["binary_sha"] = _sha256(GEM5)

    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main(argv=None):
    global OUT_BASE, SUMMARY_CSV
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="all")
    ap.add_argument("--roles", default="fault,control")
    ap.add_argument("--contexts", default="1,2,3,4,5")
    ap.add_argument("--out-base", default=str(ROOT / "audit_v3_3_3/runs"),
                    help="run directory base (default: the v3.3.3 round)")
    ap.add_argument("--out-csv",
                    default=str(ROOT / "audit_v3_3_3/controls/"
                                      "LSU_Fault_Control_Pair_RAW.csv"))
    ap.add_argument("--dry-run", action="store_true",
                    help="print the exact command for every row and exit; "
                         "no run dir, summary or CSV is written")
    args = ap.parse_args(argv)
    OUT_BASE = Path(args.out_base)
    SUMMARY_CSV = Path(args.out_csv)
    models = list(MODELS) if args.models == "all" else args.models.split(",")
    roles = args.roles.split(",")
    ctxs = [int(x) for x in args.contexts.split(",")]
    selected = [m for m in models if m in CONTEXTS]
    for model in models:
        if model not in CONTEXTS:
            print(f"skip unknown model {model}", file=sys.stderr)

    if args.dry_run:
        count = 0
        for model in selected:
            for ctx in ctxs:
                for role in roles:
                    outdir = OUT_BASE / f"{model}-R{ctx:02d}-{role}"
                    cmd = planned_command(model, ctx, role, outdir)
                    print(f"DRY-RUN {model} R{ctx:02d} {role}: "
                          f"{' '.join(cmd)}", flush=True)
                    count += 1
        print(f"dry-run: {count} commands; no run dirs written")
        return 0

    OUT_BASE.mkdir(parents=True, exist_ok=True)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    # Serialize the run set (L-D14): another matrix invocation waits instead of
    # clobbering outdirs / the RAW CSV.
    with matrix_lock():
        for model in selected:
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
            "injection_count", "oracle", "terminal", "terminal_qualifier",
            "terminal_reason", "watchdog", "watchdog_expired",
            "deadline_cycles", "checksum", "a03_log_capped",
            "control_proof", "exit_code", "timed_out", "elapsed",
            "binary_sha", "outdir", "fault_command", "error"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    sys.exit(main())
