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
import hashlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import lsu_run_state as run_state
from lsu_campaign_lock import LockHeld, campaign_lock

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
RUN_PILOT = PLATFORM / "run_pilot.py"
GEM5 = ROOT / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/se/lsu_proxy.py"
WORKLOADS = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/workloads"
DIRECTED = ROOT / "workloads/directed"
OUT_BASE = ROOT / "runs/lsu/formal_v333"
# v3.3.3: the matrix writes its own RAW CSV; the curated FINAL CSV is written
# by tools/lsu_v332_report.py. The two paths must never collide (the _J file
# is the v3.3.2 evidence of that collision; it is history and stays untouched).
SUMMARY_CSV = OUT_BASE / "LSU_Fault_Control_Pair_RAW.csv"
# The campaign lock is resolved at CALL time from the selected --out-base
# (tools/lsu_campaign_lock.py); there is deliberately no module-level path.
FORCE = False
# Frozen launch provenance: the per-model ELF SHA table the dry-run gates on.
FROZEN_PROVENANCE = (ROOT / "audit_launch_fix_v333" / "authorization"
                     / "LSU_Final_Binary_Provenance.md")
# Campaign-root index, rewritten atomically after every task.
CAMPAIGN_INDEX_NAME = "campaign_index.json"
# An accepted attempt must still expose these two evidence files before the
# index may report it COMPLETED (the attempt record carries the full
# validation result; these files prove the terminal write happened).
RESUME_REQUIRED = ("summary.json", "campaign.json")

# Authoritative formal identity: SampleRunID + Seed are read from the frozen
# matrix and passed through to every run (never generated here).
FROZEN_MATRIX = (ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
                 / "60_SAMPLE_MATRIX.csv")


def _load_frozen_identity():
    with open(FROZEN_MATRIX, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {(r["FaultModelID"], r["SampleRunID"][-3:]):
            (r["SampleRunID"], r["Seed"]) for r in rows}


FROZEN_ID = _load_frozen_identity()

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
    # A01 v3.3.3 correction (ledger L-A12): 8-byte-only eligible stream
    # (count-only census, 817 eligible; main-loop window 585-713, N=129).
    "A01":  dict(roi=(585, 713),   n=129,  ordinals=[597, 623, 649, 675, 701]),
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

# ---------------------------------------------------------------------------
# v3.3.3 launch-critical status vocabulary (audit_launch_fix_v333/
# README_INTERFACES.md).  ORACLE_FAIL is a *measured* terminal (SDC), never a
# runner failure by itself; every other non-COMPLETED status is an execution
# or integrity failure that must make the campaign exit nonzero.
# ---------------------------------------------------------------------------
CAMPAIGN_ID_DEFAULT = "LSU-V333-FORMAL-20261112"

STATUS_PENDING = "PENDING"
STATUS_RUNNING = "RUNNING"
STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_OUTPUT_INCOMPLETE = "OUTPUT_INCOMPLETE"
STATUS_HASH_MISMATCH = "HASH_MISMATCH"
STATUS_ORACLE_FAIL = "ORACLE_FAIL"
TASK_STATUSES = (STATUS_PENDING, STATUS_RUNNING, STATUS_COMPLETED,
                 STATUS_FAILED, STATUS_TIMEOUT, STATUS_OUTPUT_INCOMPLETE,
                 STATUS_HASH_MISMATCH, STATUS_ORACLE_FAIL)
# The only statuses that may coexist with campaign exit 0.  ORACLE_FAIL is a
# valid measured terminal: it is recorded but never forces a nonzero exit.
ACCEPTED_STATUSES = frozenset({STATUS_COMPLETED, STATUS_ORACLE_FAIL})
FAILURE_STATUSES = frozenset({STATUS_FAILED, STATUS_TIMEOUT,
                              STATUS_OUTPUT_INCOMPLETE,
                              STATUS_HASH_MISMATCH})
# Internal preflight marker -- never written as a task terminal status.
PREFLIGHT_OK = "OK"

TERMINAL_SOURCE_NORMAL = "NORMAL"
TERMINAL_SOURCE_MODEL_WATCHDOG = "MODEL_INTERNAL_WATCHDOG"
TERMINAL_SOURCE_EXTERNAL_TIMEOUT = "EXTERNAL_TIMEOUT"
TERMINAL_SOURCE_PYTHON_TIMEOUT = "PYTHON_TIMEOUT"
TERMINAL_SOURCES = (TERMINAL_SOURCE_NORMAL, TERMINAL_SOURCE_MODEL_WATCHDOG,
                    TERMINAL_SOURCE_EXTERNAL_TIMEOUT,
                    TERMINAL_SOURCE_PYTHON_TIMEOUT)

# Frozen v3.3.3 baseline (README_INTERFACES.md + LSU_v3.3.3_PACKAGE_README.md).
# A formal task may only start on this binary/config; a rebuild requires an
# explicit --expected-binary-sha/--expected-config-sha override.
EXPECTED_BINARY_SHA256 = (
    "62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd")
EXPECTED_CONFIG_SHA256 = (
    "8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225")

# Runtime overrides (--expected-*-sha); the defaults are the frozen baseline.
EXPECTED_BINARY_SHA = EXPECTED_BINARY_SHA256
EXPECTED_CONFIG_SHA = EXPECTED_CONFIG_SHA256
EXPECTED_ELF_SHA = None

# The model-specific injection log each model's result parser reads.  For a
# FAULT run it is a required output; a matched control may legitimately omit
# the injector (and therefore the log).
MODEL_LOG_NAME = {
    "A01": "addrpath_injections.log",
    "A03": "addrpath_injections.log",
    "FW02": "lsq_fwd_injections.log",
    "FW05": "lsq_fwd_injections.log",
    "SQ01": "lsq_fwd_injections.log",
    "SQ03": "lsq_fwd_injections.log",
    "SP05": "lsq_fwd_injections.log",
    "DA04": "lsq_fwd_injections.log",
    "LP01": "l1d_fwd_injections.log",
    "MD04": "md04_injections.log",
    "LQ04": "lq04_injections.log",
    "RP01": "lsq_fwd_injections.log",
}
# A03/RP01 have documented partial-output terminals: prop_trace + oracle +
# the in-simulator watchdog marker are enough even when the per-model log or
# the converted trace_v31.jsonl was truncated by the model-terminal hang.
PARTIAL_MARKER_MODELS = frozenset({"A03", "RP01"})
WATCHDOG_MARKERS = {
    "A03": ("A03_WATCHDOG_EXPIRED",),
    "RP01": ("CHAOS_RP01_WATCHDOG", "CHAOS_RP01_WATCHDOG=EXPIRED"),
}

# Default workload per model when CONTEXTS does not pin one (mirrors
# run_pilot._workload_for; preflight needs the real ELF path).
DEFAULT_WORKLOADS = {
    "A01": WORKLOADS / "agu_addrmodes",
    "A03": WORKLOADS / "agu_addrmodes",
    "FW02": DIRECTED / "sq_forward_w4v2",
    "FW05": WORKLOADS / "fw05_forward",
    "SQ01": WORKLOADS / "sq_reload_v3212",
    "SQ03": WORKLOADS / "sq_reload_v3212",
    "SP05": WORKLOADS / "sq_reload_v3212",
    "DA04": WORKLOADS / "alignment",
    "LP01": WORKLOADS / "load_response",
    "MD04": DIRECTED / "md04_violations_v332",
    "LQ04": WORKLOADS / "lq_lifetime_ordinal",
    "RP01": DIRECTED / "replay_partial_v332",
}

_SHA_CACHE: dict[tuple, str] = {}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha256_cached(path: Path) -> str:
    """SHA256 with a (path,size,mtime) cache so 120 preflights stay cheap."""
    path = Path(path)
    st = path.stat()
    key = (str(path.resolve()), st.st_size, st.st_mtime_ns)
    if key not in _SHA_CACHE:
        _SHA_CACHE[key] = _sha256(path)
    return _SHA_CACHE[key]


def resolve_workload(model, workload=None) -> Path | None:
    """The ELF a matrix row will execute (CONTEXTS override wins)."""
    if workload:
        return Path(workload)
    return DEFAULT_WORKLOADS.get(model)


def driver_for(model: str, role: str) -> str:
    """Which driver run_context dispatches to (mirrors planned_command)."""
    if model == RP01 or (model in DIRECT and role == "fault"):
        return "direct"
    return "run_pilot"


def required_outputs(model: str, role: str) -> list[str]:
    """Artifacts a successful task of this model/role must leave behind."""
    names = ["summary.json", "prop_trace.csv.gz", "oracle.log"]
    if role == "fault":
        names.append(MODEL_LOG_NAME[model])
    if driver_for(model, role) == "run_pilot":
        names.append("trace_v31.jsonl")
    return names


def _file_contains(path: Path, tokens) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="replace")
    return any(token in text for token in tokens)


def watchdog_marker_present(outdir: Path, model: str) -> bool:
    """True when the model's own in-simulator watchdog marker was written."""
    tokens = WATCHDOG_MARKERS.get(model)
    if not tokens:
        return False
    outdir = Path(outdir)
    candidates = [outdir / name for name in
                  (MODEL_LOG_NAME.get(model), "stdout.log", "stderr.log")
                  if name]
    return any(_file_contains(p, tokens) for p in candidates)


def preflight_task(*, model: str, role: str, binary, config, workload, seed,
                   sample_run_id, outdir, expected_binary_sha=None,
                   expected_config_sha=None, expected_elf_sha=None,
                   force: bool = False, sha_fn=None,
                   outdir_exists: bool | None = None) -> dict:
    """Validate every input BEFORE gem5 is launched.

    Missing metadata/artifact => FAILED; a present artifact whose SHA differs
    from the expected frozen hash => HASH_MISMATCH.  Nothing is executed and
    no existing run dir is touched on failure.
    """
    sha_fn = sha_fn or _sha256_cached
    evidence = {"checks": {}, "missing": [], "sha_mismatches": [],
                "observed_sha": {}, "expected_sha": {}}

    def check_file(name: str, path) -> None:
        if path is None:
            evidence["checks"][name] = "MISSING"
            evidence["missing"].append(name)
            return
        p = Path(path)
        if not p.is_file():
            evidence["checks"][name] = "MISSING"
            evidence["missing"].append(name)
            return
        evidence["checks"][name] = "PRESENT"
        evidence["observed_sha"][name] = sha_fn(p)

    check_file("binary", binary)
    check_file("config", config)
    check_file("workload", workload)

    for name, value in (("seed", seed), ("sample_run_id", sample_run_id)):
        if value is None or str(value).strip() == "":
            evidence["checks"][name] = "MISSING"
            evidence["missing"].append(name)
        else:
            evidence["checks"][name] = "PRESENT"

    outdir = Path(outdir)
    if outdir_exists is None:
        outdir_exists = (outdir.exists()
                         and (not outdir.is_dir() or any(outdir.iterdir())))
    if outdir_exists and not force:
        evidence["checks"]["outdir_unique"] = "COLLISION"
        evidence["missing"].append("outdir_unique")
    else:
        evidence["checks"]["outdir_unique"] = "OK"

    for key, expected in (("binary", expected_binary_sha),
                          ("config", expected_config_sha),
                          ("workload", expected_elf_sha)):
        observed = evidence["observed_sha"].get(key)
        if expected and observed and observed != expected:
            evidence["sha_mismatches"].append(key)
            evidence["expected_sha"][key] = expected

    if evidence["sha_mismatches"]:
        status = STATUS_HASH_MISMATCH
    elif evidence["missing"]:
        status = STATUS_FAILED
    else:
        status = PREFLIGHT_OK
    return {
        "status": status,
        "ok": status == PREFLIGHT_OK,
        "model": model,
        "role": role,
        "evidence": evidence,
        "binary_sha": evidence["observed_sha"].get("binary"),
        "config_sha": evidence["observed_sha"].get("config"),
        "elf_sha": evidence["observed_sha"].get("workload"),
    }


def validate_outputs(model: str, outdir, *, role: str, parse_error=None,
                     sha_evidence=None) -> dict:
    """Post-run artifact validation.

    summary.json is mandatory; FAULT runs must also leave their model log;
    run_pilot rows must leave the converted trace.  A03/RP01 may instead
    present the documented partial set (prop_trace + oracle + watchdog
    marker).  A result-parsing exception is FAILED, never a silent pass.
    """
    outdir = Path(outdir)
    required = required_outputs(model, role)
    present = {name: (outdir / name).is_file() for name in required}
    missing = [name for name in required if not present[name]]
    marker = watchdog_marker_present(outdir, model)
    partial = False
    if (missing and model in PARTIAL_MARKER_MODELS and marker
            and {"summary.json", "prop_trace.csv.gz", "oracle.log"}
            .isdisjoint(missing)):
        # Documented A03/RP01 partial: prop_trace + oracle + marker stand in
        # for the per-model log / converted trace cut by the model hang.
        if set(missing) <= {"trace_v31.jsonl", MODEL_LOG_NAME[model]}:
            partial = True
            missing = []

    sha_status = (sha_evidence or {}).get("status")
    if sha_status == STATUS_HASH_MISMATCH:
        status = STATUS_HASH_MISMATCH
    elif parse_error:
        status = STATUS_FAILED
    elif missing:
        status = STATUS_OUTPUT_INCOMPLETE
    else:
        status = PREFLIGHT_OK
    return {
        "status": status,
        "required": required,
        "present": present,
        "missing": missing,
        "partial": partial,
        "watchdog_marker": marker,
        "parse_error": parse_error,
    }


MODEL_TERMINALS = frozenset({"MASKED", "SQUASHED", "HANG_WATCHDOG"})


def measured_status(*, model: str, role: str, terminal, oracle_pass,
                    exit_code, timed_out: bool, validation_status,
                    parse_error=None, runner_status=None,
                    crash_by_fault: bool = False) -> str:
    """Map a finished run to the v3.3.3 task-status vocabulary.

    A timeout (Python or the inner runner) is TIMEOUT; a measured SDC is
    ORACLE_FAIL; model terminals (MASKED/SQUASHED/HANG_WATCHDOG, plus a
    fault-induced CRASH) are COMPLETED.  Anything else is an execution
    failure.
    """
    if parse_error or runner_status == STATUS_FAILED:
        return STATUS_FAILED
    if timed_out or runner_status == STATUS_TIMEOUT:
        return STATUS_TIMEOUT
    if validation_status == STATUS_HASH_MISMATCH:
        return STATUS_HASH_MISMATCH
    if validation_status == STATUS_OUTPUT_INCOMPLETE:
        return STATUS_OUTPUT_INCOMPLETE
    if validation_status == STATUS_FAILED:
        return STATUS_FAILED
    if role == "fault":
        if terminal == "SDC":
            return STATUS_ORACLE_FAIL
        if terminal in MODEL_TERMINALS:
            return STATUS_COMPLETED
        if terminal == "CRASH" and crash_by_fault:
            return STATUS_COMPLETED
        return STATUS_FAILED
    # CONTROL: only a clean-exit run is a completed control.  A control's
    # oracle FAIL is an infrastructure defect (golden mismatch), not SDC.
    control_ok = frozenset({"UNRESOLVED"}) | MODEL_TERMINALS
    if exit_code == 0 and terminal in control_ok:
        return STATUS_COMPLETED
    return STATUS_FAILED


def terminal_source(*, timed_out: bool = False, exit_code=None,
                    watchdog: bool = False, text: str = "") -> str:
    """Never conflate the model's own watchdog with an external kill.

    * Python/subprocess timeout in this driver   -> PYTHON_TIMEOUT
    * the inner runner's wall-clock timeout      -> EXTERNAL_TIMEOUT
    * A03_WATCHDOG_EXPIRED / CHAOS_RP01_WATCHDOG -> MODEL_INTERNAL_WATCHDOG
    * otherwise                                  -> NORMAL
    """
    if timed_out:
        return TERMINAL_SOURCE_PYTHON_TIMEOUT
    # An external/inner timeout means the process was killed: that fact wins
    # over a watchdog marker the model may have written before being cut.
    if exit_code == 124 or "TIMEOUT: external wall-clock limit" in (text or ""):
        return TERMINAL_SOURCE_EXTERNAL_TIMEOUT
    if watchdog:
        return TERMINAL_SOURCE_MODEL_WATCHDOG
    return TERMINAL_SOURCE_NORMAL


def campaign_record(*, campaign_id: str, model: str, context: str, role: str,
                    sample_run_id, seed, status: str, binary_sha, config_sha,
                    elf_sha, started_at, ended_at, exit_code, timed_out: bool,
                    terminal_source: str, **extra) -> dict:
    """The per-run campaign.json record the collector reads."""
    record = {
        "campaign_id": campaign_id,
        "model": model,
        "context": context,
        "role": role,
        "sample_run_id": sample_run_id,
        "seed": seed,
        "status": status,
        "binary_sha": binary_sha,
        "config_sha": config_sha,
        "elf_sha": elf_sha,
        "started_at": started_at,
        "ended_at": ended_at,
        "exit_code": exit_code,
        "timed_out": bool(timed_out),
        "terminal_source": terminal_source,
    }
    record.update(extra)
    return record


def write_campaign_json(outdir, record: dict) -> Path:
    path = Path(outdir) / "campaign.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2, sort_keys=False) + "\n",
                    encoding="utf-8")
    return path


def write_campaign_identity(out_base, campaign_id: str, *, tasks=None,
                            sha_fn=None) -> Path:
    """Write the campaign-root identity record read by the formal collector.

    ``elf_sha`` is keyed by workload basename.  The record is metadata only:
    it never replaces a per-run ``campaign.json`` and it is written before the
    first task so a partial campaign still carries provenance.
    """
    sha_fn = sha_fn or _sha256
    if tasks is None:
        tasks = [(model, ctx, resolve_workload(model,
                                               CONTEXTS[model].get("workload")))
                 for model in MODELS for ctx in range(1, 6)]
    elf_sha: dict[str, str] = {}
    for _model, _ctx, workload in tasks:
        if not workload:
            continue
        path = Path(workload)
        if path.is_file():
            elf_sha.setdefault(path.name, sha_fn(path))
    record = {
        "campaign_id": campaign_id,
        "binary_sha": sha_fn(Path(GEM5)) if Path(GEM5).is_file() else None,
        "config_sha": sha_fn(Path(CONFIG)) if Path(CONFIG).is_file() else None,
        "elf_sha": elf_sha,
    }
    out_base = Path(out_base)
    out_base.mkdir(parents=True, exist_ok=True)
    path = out_base / "campaign_identity.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return path


def campaign_exit_code(rows) -> int:
    """0 iff every scheduled task ended COMPLETED/ORACLE_FAIL, else 1."""
    rows = list(rows)
    if any(row.get("status") not in ACCEPTED_STATUSES for row in rows):
        return 1
    return 0


def status_summary(rows) -> dict:
    counts = Counter(row.get("status", STATUS_FAILED) for row in rows)
    for status in TASK_STATUSES:
        counts.setdefault(status, 0)
    return dict(counts)


def _kill_process_group(proc) -> None:
    """Kill the child AND its descendants (gem5 may fork helpers)."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except OSError:
            pass


def run_subprocess(cmd, *, outdir, timeout, cwd=None,
                   stdout_name="stdout.log", stderr_name="stderr.log") -> dict:
    """Run a child in its own session and kill the whole group on timeout.

    Records start time, PID, timeout, exit code and both streams.  A timeout
    is always TIMEOUT; never COMPLETED.  OSError (missing binary/permission)
    is converted to FAILED evidence instead of escaping.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    started_at = _now_iso()
    started_mono = time.monotonic()
    result = {"cmd": list(cmd), "pid": None, "exit_code": None,
              "timed_out": False, "elapsed": None, "started_at": started_at,
              "ended_at": None, "status": None}
    try:
        proc = subprocess.Popen(
            cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True)
    except OSError as exc:
        (outdir / stdout_name).write_text("")
        (outdir / stderr_name).write_text(f"OSError: {exc!r}\n")
        result.update(exit_code=None, error=repr(exc), status=STATUS_FAILED,
                      ended_at=_now_iso(),
                      elapsed=round(time.monotonic() - started_mono, 3))
        return result

    result["pid"] = proc.pid
    timed_out = False
    try:
        out, err = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        _kill_process_group(proc)
        try:
            out, err = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            out, err = "", ""
        err = (err or "") + (
            "\nTIMEOUT: external wall-clock limit reached; "
            "process group killed\n")
    (outdir / stdout_name).write_text(out or "")
    (outdir / stderr_name).write_text(err or "")
    result.update(
        # A killed child reports -SIGKILL; record the documented wall-clock
        # timeout code 124 and keep the raw signal in evidence.
        exit_code=(124 if timed_out else proc.returncode),
        signal=(-proc.returncode if (timed_out and proc.returncode
                                    and proc.returncode < 0) else None),
        timed_out=timed_out,
        elapsed=round(time.monotonic() - started_mono, 3),
        ended_at=_now_iso(),
        status=(STATUS_TIMEOUT if timed_out else None),
        stdout=out or "",
        stderr=err or "",
    )
    return result


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


def run_pilot_cmd(model, ctx_idx, ordinal, outdir, role, workload,
                  pilot_id=None):
    # ``--outdir`` is the attempt directory; the identity the collector keys
    # on stays the task tag (run dir basename), never "attempt_NNN".
    cmd = [sys.executable, str(RUN_PILOT), "--model", model,
           "--context-index", str(ctx_idx),
           "--event-ordinal", str(ordinal),
           "--pilot-id", pilot_id or Path(outdir).name,
           "--outdir", str(outdir),
           "--timeout", "180"]
    if workload:
        cmd += ["--workload", str(workload)]
    if role == "control":
        cmd += ["--probability", "0.0"]
    # Formal identity: the frozen Seed is passed explicitly and the frozen
    # SampleRunID is preserved (run_pilot's default would replace it with a
    # PILOT-* id). This is metadata only; it does not change the fault.
    _sid, seed = FROZEN_ID[(model, f"R{ctx_idx:02d}")]
    cmd += ["--seed", str(seed), "--preserve-sample-id"]
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
    # The frozen seed is carried by BOTH roles so fault/control pairing is
    # visible in the executed command text, not only in the identity record.
    base += ["--rng_seed", str(seed)]
    if role == "fault":
        base += ["--chaos_lsqfwd", "--lsq_struct_mode", "rp01_skip_replay",
                 "--max_faults", "1",
                 "--rp01_event_ordinal", str(ordinal),
                 "--rp01_watchdog_cycles", str(RP01_DEADLINE_CYCLES)]
    return base


def planned_command(model, ctx_idx, role, outdir) -> list[str]:
    """The command this matrix row would execute (pure; no subprocess)."""
    spec = CONTEXTS[model]
    ordinal = spec["ordinals"][ctx_idx - 1]
    _sid, seed = FROZEN_ID[(model, f"R{ctx_idx:02d}")]
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


def matrix_lock(out_base=None, campaign_id=None):
    """Compatibility shim around the campaign-scoped lock.

    Kept for callers/tests that monkeypatch ``matrix_lock``; it resolves the
    lock path at CALL time from ``out_base`` (never a module-level default)
    and delegates to :func:`lsu_campaign_lock.campaign_lock`.
    """
    return campaign_lock(Path(out_base) if out_base is not None else OUT_BASE,
                         campaign_id or CAMPAIGN_ID_DEFAULT)


def run_direct(cmd_base, outdir, timeout):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    # Drop any dry-run outdir token and inject ours right after the binary.
    cmd = [c for c in cmd_base if not c.startswith("--outdir=")]
    cmd.insert(1, f"--outdir={outdir}")
    (outdir / "command.txt").write_text("\n".join(cmd) + "\n")
    return run_subprocess(cmd, outdir=outdir, timeout=timeout, cwd=ROOT)


def _seed_from_command(outdir: Path):
    text = read_command(outdir)
    m = re.search(r"--[A-Za-z0-9_]*rng_seed(?:\s+|=)(\d+)", text)
    return int(m.group(1)) if m else None


WATCHDOG_ANY = ("CHAOS_SQ03_WATCHDOG_EXPIRED", "CHAOS_SP05_WATCHDOG_EXPIRED",
                "CHAOS_LQ04_WATCHDOG_EXPIRED", "CHAOS_RP01_WATCHDOG",
                "CHAOS_RP01_WATCHDOG=EXPIRED", "A03_WATCHDOG_EXPIRED")


def any_watchdog_marker(outdir: Path) -> bool:
    outdir = Path(outdir)
    for name in ("stdout.log", "stderr.log", "addrpath_injections.log",
                 "lsq_fwd_injections.log", "lq04_injections.log"):
        if _file_contains(outdir / name, WATCHDOG_ANY):
            return True
    return False


# ---------------------------------------------------------------------------
# v3.3.3 attempt isolation / canonical selection / campaign index
# ---------------------------------------------------------------------------
def load_frozen_elf_table(path: Path | None = None) -> dict[str, str]:
    """The frozen per-workload ELF SHA256 table from the provenance document.

    Parsed from the real file (never duplicated as constants) so a stale or
    edited provenance table is detected by the dry-run, not silently trusted.
    """
    path = Path(path or FROZEN_PROVENANCE)
    table: dict[str, str] = {}
    if not path.is_file():
        return table
    pattern = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`([0-9a-fA-F]{64})`\s*\|\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            table[match.group(1)] = match.group(2).lower()
    return table


def _attempt_artifact_hashes(adir: Path, names) -> dict[str, str]:
    """SHA256 of every required artifact, recorded in the attempt record."""
    hashes = {}
    for name in names:
        path = Path(adir) / name
        if path.is_file():
            hashes[name] = _sha256(path)
    return hashes


def _publish_attempt_view(run_dir: Path, adir: Path) -> None:
    """Point the run-dir root convenience view at ``adir``.

    Only symlinks that this tool created (targets under ``attempts/``) are
    replaced; legacy regular files are never touched.
    """
    run_dir = Path(run_dir)
    for name in run_state.VIEW_NAMES:
        dst = run_dir / name
        if not dst.is_symlink():
            continue
        try:
            target = Path(os.readlink(dst))
        except OSError:
            continue
        if target.parts and target.parts[0] == "attempts":
            try:
                dst.unlink()
            except OSError:
                pass
    run_state.link_canonical_view(run_dir, adir)


def _task_attempt_state(run_dir: Path, campaign_id: str) -> dict:
    return run_state.scan_task_state(run_dir, campaign_id,
                                     required_outputs=RESUME_REQUIRED)


def _ensure_canonical(run_dir: Path, campaign_id: str) -> dict:
    """Register the first accepted attempt as canonical if it is missing.

    Repairs the crash window between the terminal attempt write and the
    canonical write without ever re-executing or replacing an existing
    canonical.
    """
    state = _task_attempt_state(run_dir, campaign_id)
    if state["state"] not in run_state.CANONICAL_ACCEPTED:
        return state
    if state.get("canonical") is not None:
        return state
    accepted = []
    for adir in sorted(run_state.attempts_root(run_dir).glob("attempt_*")):
        rec = run_state.read_attempt_record(adir)
        if rec is None or rec.get("status") not in run_state.CANONICAL_ACCEPTED:
            continue
        if any(not (adir / name).is_file() for name in RESUME_REQUIRED):
            continue
        accepted.append((adir, rec))
    if not accepted:
        return state
    adir, rec = accepted[0]              # the FIRST accepted attempt wins
    run_state.write_canonical(run_dir, {
        "campaign_id": campaign_id,
        "attempt_id": adir.name,
        "model": rec.get("model"),
        "context": rec.get("context"),
        "role": rec.get("role"),
        "sample_run_id": rec.get("sample_run_id"),
        "seed": rec.get("seed"),
        "status": rec.get("status"),
        "registered_at": _now_iso(),
        "registration": "RESUME_REPAIR",
    })
    _publish_attempt_view(run_dir, adir)
    return _task_attempt_state(run_dir, campaign_id)


def build_campaign_index(out_base, campaign_id: str, tasks) -> dict:
    """Derive the campaign index from DISK; never asserts a status itself."""
    out_base = Path(out_base)
    entries = []
    for model, ctx, role in tasks:
        run_dir = out_base / run_state.task_tag(model, ctx, role)
        state = _task_attempt_state(run_dir, campaign_id)
        entries.append({
            "model": model,
            "context": f"R{int(ctx):02d}",
            "role": role,
            "run_dir": str(run_dir),
            "state": state["state"],
            "attempt_id": state.get("attempt_id"),
            "canonical_attempt_id": (
                (state.get("canonical") or {}).get("attempt_id")),
            "reason": state.get("reason"),
        })
    counts = Counter(entry["state"] for entry in entries)
    for status in TASK_STATUSES:
        counts.setdefault(status, 0)
    return {
        "campaign_id": campaign_id,
        "out_base": str(out_base),
        "updated_at": _now_iso(),
        "task_count": len(entries),
        "counts": dict(counts),
        "tasks": entries,
    }


def write_campaign_index(out_base, index: dict) -> Path:
    """Atomically replace ``<out-base>/campaign_index.json``."""
    path = Path(out_base) / CAMPAIGN_INDEX_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp.{os.getpid()}")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
    return path


def _resumed_row(model, ctx_idx, role, run_dir, state, campaign_id,
                 fallback=None) -> dict:
    """A row for a task resume skipped (never re-executed)."""
    row = dict(fallback or {})
    adir = None
    if state.get("canonical"):
        adir = run_state.canonical_dir(run_dir)
    elif state.get("attempt_id"):
        adir = run_state.attempt_dir(run_dir, state["attempt_id"])
    summary = {}
    if adir is not None and (adir / "summary.json").is_file():
        try:
            summary = json.loads((adir / "summary.json").read_text())
        except (OSError, ValueError):
            summary = {}
    row.update({
        "model": model,
        "context": f"R{int(ctx_idx):02d}",
        "role": role,
        "campaign_id": campaign_id,
        "status": state["state"],
        "outdir": str(run_dir),
        "attempt_id": state.get("attempt_id"),
        "attempt_dir": str(adir) if adir is not None else None,
        "resumed": True,
        "terminal": row.get("terminal", summary.get("terminal")),
        "sample_run_id": (row.get("sample_run_id")
                          or summary.get("sample_run_id")
                          or (state.get("canonical") or {}).get("sample_run_id")),
        "seed": (row.get("seed") if row.get("seed") is not None
                 else summary.get("seed")),
        "terminal_source": row.get("terminal_source",
                                   TERMINAL_SOURCE_NORMAL),
    })
    return row


# ---------------------------------------------------------------------------
# v3.3.3 dry-run: validate the complete frozen matrix without executing
# ---------------------------------------------------------------------------
def dry_run_validation(*, models, ctxs, roles, out_base, campaign_id,
                       expected_binary_sha, expected_config_sha,
                       sha_fn=None, elf_table=None,
                       workload_fn=None) -> dict:
    """Gate the whole launch matrix; returns a JSON-serialisable summary."""
    sha_fn = sha_fn or _sha256
    workload_fn = workload_fn or resolve_workload
    elf_table = (load_frozen_elf_table() if elf_table is None else elf_table)
    out_base = Path(out_base)
    errors: list[str] = []

    tasks = [(model, int(ctx), role)
             for model in models for ctx in ctxs for role in roles]
    unique_tasks = len(set(tasks))
    gate = {"task_count": len(tasks), "unique_task_count": unique_tasks,
            "unique_tasks": unique_tasks == len(tasks) == 120}
    if not gate["unique_tasks"]:
        errors.append(f"UNIQUE_TASKS: {unique_tasks} unique of {len(tasks)}")

    identities = {}
    for model, ctx, role in tasks:
        key = (model, ctx)
        if key not in identities:
            identities[key] = FROZEN_ID.get((model, f"R{ctx:02d}"))
    pairs_ok = True
    for model, ctx, _role in tasks:
        if FROZEN_ID.get((model, f"R{ctx:02d}")) is None:
            pairs_ok = False
            errors.append(f"MISSING_IDENTITY: {model} R{ctx:02d}")
    ids = [sid for sid, _seed in identities.values() if sid]
    seeds = [seed for _sid, seed in identities.values() if seed]
    gate["unique_sample_run_ids"] = len(set(ids))
    gate["unique_seeds"] = len(set(seeds))
    gate["sample_run_ids_ok"] = len(set(ids)) == 60
    gate["seeds_ok"] = len(set(seeds)) == 60
    if not gate["sample_run_ids_ok"]:
        errors.append(f"UNIQUE_SAMPLE_RUN_IDS: {len(set(ids))} != 60")
    if not gate["seeds_ok"]:
        errors.append(f"UNIQUE_SEEDS: {len(set(seeds))} != 60")
    # Every fault/control pair must share the frozen SampleRunID and Seed.
    by_pair = {}
    for model, ctx, role in tasks:
        by_pair.setdefault((model, ctx), {})[role] = \
            FROZEN_ID.get((model, f"R{ctx:02d}"))
    pairing_ok = all(len(v) == 2 and len(set(v.values())) == 1
                     for v in by_pair.values())
    gate["pairing_ok"] = bool(pairs_ok and pairing_ok)
    if not gate["pairing_ok"]:
        errors.append("FAULT_CONTROL_PAIRING")

    outdirs = [str(out_base / run_state.task_tag(model, ctx, role))
               for model, ctx, role in tasks]
    gate["unique_outdirs"] = len(set(outdirs))
    gate["unique_outdirs_ok"] = len(set(outdirs)) == len(outdirs)
    if not gate["unique_outdirs_ok"]:
        errors.append("DUPLICATE_OUTDIRS")
    collisions = [d for d in sorted(set(outdirs)) if Path(d).exists()]
    gate["existing_outdir_collisions"] = len(collisions)
    if collisions:
        errors.append("EXISTING_OUTDIR:" + ",".join(collisions[:3]))

    binary_sha = sha_fn(Path(GEM5)) if Path(GEM5).is_file() else None
    config_sha = sha_fn(Path(CONFIG)) if Path(CONFIG).is_file() else None
    gate["binary_sha"] = binary_sha
    gate["config_sha"] = config_sha
    gate["expected_binary_sha"] = expected_binary_sha
    gate["expected_config_sha"] = expected_config_sha
    gate["binary_sha_ok"] = binary_sha == expected_binary_sha
    gate["config_sha_ok"] = config_sha == expected_config_sha
    if not gate["binary_sha_ok"]:
        errors.append("BINARY_SHA_MISMATCH")
    if not gate["config_sha_ok"]:
        errors.append("CONFIG_SHA_MISMATCH")

    elf_checks = []
    elf_ok = True
    for model in models:
        workload = workload_fn(model, CONTEXTS[model].get("workload"))
        name = Path(workload).name if workload else None
        expected = elf_table.get(name) if name else None
        observed = None
        if workload is not None and Path(workload).is_file():
            observed = sha_fn(Path(workload))
        ok = bool(expected and observed and observed == expected)
        elf_ok = elf_ok and ok
        elf_checks.append({"model": model, "workload": str(workload)
                           if workload else None, "basename": name,
                           "expected": expected, "observed": observed,
                           "ok": ok})
        if not ok:
            errors.append(f"ELF_SHA:{model}:{name}:{observed}:{expected}")
    gate["elf_ok"] = elf_ok
    gate["elf_checks"] = elf_checks
    gate["campaign_id"] = campaign_id
    gate["campaign_id_ok"] = bool(str(campaign_id).strip())
    if not gate["campaign_id_ok"]:
        errors.append("INVALID_CAMPAIGN_ID")

    passed_keys = ("unique_tasks", "sample_run_ids_ok", "seeds_ok",
                   "pairing_ok", "unique_outdirs_ok", "binary_sha_ok",
                   "config_sha_ok", "elf_ok", "campaign_id_ok")
    gate["existing_outdir_collisions_ok"] = not collisions
    passed_keys = passed_keys + ("existing_outdir_collisions_ok",)
    gate["ok"] = all(gate[k] for k in passed_keys) and not errors
    gate["errors"] = errors
    return gate


def run_context(model, ctx_idx, role, campaign_id=CAMPAIGN_ID_DEFAULT):
    spec = CONTEXTS[model]
    ordinal = spec["ordinals"][ctx_idx - 1]
    sample_run_id, seed = FROZEN_ID[(model, f"R{ctx_idx:02d}")]
    # CONTEXTS pins an override for some models; run_pilot must keep receiving
    # the RAW override (None = its own default), never the resolved path --
    # passing it explicitly would switch run_pilot's manifest/oracle source.
    workload_override = spec.get("workload")
    workload = resolve_workload(model, workload_override)
    tag = run_state.task_tag(model, ctx_idx, role)
    run_dir = OUT_BASE / tag
    started_at = _now_iso()

    # Duplicate submission: an accepted canonical result is immutable, so the
    # task is never re-executed (and never replaced) as a "new attempt".
    prior = _task_attempt_state(run_dir, campaign_id)
    if prior["state"] in run_state.CANONICAL_ACCEPTED:
        return {"model": model, "context": f"R{ctx_idx:02d}", "role": role,
                "campaign_id": campaign_id, "status": STATUS_FAILED,
                "outdir": str(run_dir),
                "attempt_id": prior.get("attempt_id"),
                "error": ("outdir_unique: canonical result already exists "
                          f"({prior.get('attempt_id')}); refusing duplicate "
                          "submission"),
                "duplicate": True}

    attempt_id = run_state.next_attempt_id(run_dir)
    adir = run_state.attempt_dir(run_dir, attempt_id)

    # ---- Preflight BEFORE any gem5 process --------------------------------
    pre = preflight_task(
        model=model, role=role, binary=GEM5, config=CONFIG,
        workload=workload, seed=seed, sample_run_id=sample_run_id,
        outdir=adir, expected_binary_sha=EXPECTED_BINARY_SHA,
        expected_config_sha=EXPECTED_CONFIG_SHA,
        expected_elf_sha=EXPECTED_ELF_SHA, force=FORCE)
    binary_sha = pre["binary_sha"]
    config_sha = pre["config_sha"]
    elf_sha = pre["elf_sha"]
    base_row = {"model": model, "context": f"R{ctx_idx:02d}", "role": role,
                "ordinal": ordinal, "seed": seed,
                "sample_run_id": sample_run_id,
                "workload": str(workload) if workload else None,
                "outdir": str(run_dir), "attempt_id": attempt_id,
                "attempt_dir": str(adir), "campaign_id": campaign_id,
                "binary_sha": binary_sha, "config_sha": config_sha,
                "elf_sha": elf_sha, "started_at": started_at}
    if not pre["ok"]:
        # Never run gem5.  The refusal is still preserved as attempt evidence
        # (a HASH_MISMATCH attempt makes resume refuse rather than retry).
        adir.mkdir(parents=True, exist_ok=True)
        ended_at = _now_iso()
        run_state.write_attempt_record(adir, {
            "attempt_id": attempt_id, "campaign_id": campaign_id,
            "model": model, "context": f"R{ctx_idx:02d}", "role": role,
            "sample_run_id": sample_run_id, "seed": seed,
            "status": pre["status"], "started_at": started_at,
            "ended_at": ended_at, "binary_sha": binary_sha,
            "config_sha": config_sha, "elf_sha": elf_sha,
            "run_dir": str(run_dir), "attempt_dir": str(adir),
            "reason": "PREFLIGHT",
            "preflight": pre["evidence"],
            "error": "preflight " + ",".join(
                pre["evidence"]["missing"] or
                pre["evidence"]["sha_mismatches"]),
        })
        write_campaign_json(adir, campaign_record(
            campaign_id=campaign_id, model=model,
            context=f"R{ctx_idx:02d}", role=role,
            sample_run_id=sample_run_id, seed=seed,
            status=pre["status"], binary_sha=binary_sha,
            config_sha=config_sha, elf_sha=elf_sha,
            started_at=started_at, ended_at=ended_at,
            exit_code=None, timed_out=False,
            terminal_source=TERMINAL_SOURCE_NORMAL,
            preflight=pre["evidence"]))
        _publish_attempt_view(run_dir, adir)
        row = dict(base_row)
        row.update(
            status=pre["status"], ended_at=ended_at,
            terminal_source=TERMINAL_SOURCE_NORMAL,
            error="preflight " + ",".join(
                pre["evidence"]["missing"] or
                pre["evidence"]["sha_mismatches"]),
            preflight=pre["evidence"])
        return row

    adir.mkdir(parents=True, exist_ok=True)
    outdir = adir                       # every execution writes into the attempt
    run_state.write_attempt_record(adir, {
        "attempt_id": attempt_id, "campaign_id": campaign_id,
        "model": model, "context": f"R{ctx_idx:02d}", "role": role,
        "sample_run_id": sample_run_id, "seed": seed,
        "status": STATUS_RUNNING, "started_at": started_at,
        "ended_at": None, "binary_sha": binary_sha,
        "config_sha": config_sha, "elf_sha": elf_sha,
        "run_dir": str(run_dir), "attempt_dir": str(adir),
        "reason": "EXECUTING",
    })

    summary = {"model": model, "context": f"R{ctx_idx:02d}",
               "ctx_index": ctx_idx, "role": role, "ordinal": ordinal,
               "seed": seed, "sample_run_id": sample_run_id,
               "workload": str(workload) if workload else None,
               "outdir": str(run_dir), "attempt_dir": str(adir),
               "attempt_id": attempt_id, "binary": str(GEM5),
               "binary_sha": binary_sha, "config_sha": config_sha,
               "elf_sha": elf_sha, "campaign_id": campaign_id,
               "started_at": started_at, "status": STATUS_RUNNING}
    write_campaign_json(outdir, campaign_record(
        campaign_id=campaign_id, model=model, context=f"R{ctx_idx:02d}",
        role=role, sample_run_id=sample_run_id, seed=seed,
        status=STATUS_RUNNING, binary_sha=binary_sha, config_sha=config_sha,
        elf_sha=elf_sha, started_at=started_at, ended_at=None,
        exit_code=None, timed_out=False,
        terminal_source=TERMINAL_SOURCE_NORMAL,
        attempt_id=attempt_id))

    info = None
    meta = {}
    parsed = {}
    cmd = []
    parse_error = None
    runner_status = None
    watchdog = False
    crash_by_fault = False
    inner_exit = None
    timeout_seconds = None
    try:
        if model == RP01:
            timeout_seconds = RP01_TIMEOUT
            cmd = build_rp01_cmd(role, ordinal, seed, workload, outdir)
            info = run_direct(cmd, outdir, RP01_TIMEOUT)
            runner_status = info.get("status")
            parsed = parse_rp01_evidence(outdir)
            watchdog = bool(parsed.get("watchdog"))
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
            summary.update({k: info[k] for k in
                            ("exit_code", "timed_out", "elapsed") if k in info})
            summary["pid"] = info.get("pid")
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
            timeout_seconds = A03_TIMEOUT
            cmd = build_a03_fault_cmd(ordinal, seed, workload, outdir)
            info = run_direct(cmd, outdir, A03_TIMEOUT)
            runner_status = info.get("status")
            parsed = parse_addrpath_log(outdir / "addrpath_injections.log")
            stdout_text = (outdir / "stdout.log").read_text(errors="replace")
            checksum = parse_bare_checksum(stdout_text)
            # Task 3 may emit the marker on stdout (after the addrpath log
            # flush); accept either location.
            if "A03_WATCHDOG_EXPIRED" in stdout_text:
                parsed["watchdog_expired"] = True
            watchdog = bool(parsed["watchdog_expired"])
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
            summary.update({k: info[k] for k in
                            ("exit_code", "timed_out", "elapsed") if k in info})
            summary["pid"] = info.get("pid")
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
            timeout_seconds = 400
            cmd = run_pilot_cmd(model, ctx_idx, ordinal, outdir, role,
                                workload_override, pilot_id=tag)
            info = run_subprocess(
                cmd, outdir=outdir, timeout=400, cwd=ROOT,
                stdout_name="runner_stdout.log",
                stderr_name="runner_stderr.log")
            runner_status = info.get("status")
            summary["cmd"] = cmd
            summary["exit_code"] = info.get("exit_code")
            summary["pid"] = info.get("pid")
            summary["timed_out"] = info.get("timed_out")
            summary["elapsed"] = info.get("elapsed")
            meta_path = outdir / "pilot_meta.json"
            try:
                meta = (json.load(open(meta_path))
                        if meta_path.exists() else {})
            except (json.JSONDecodeError, OSError) as exc:
                parse_error = repr(exc)
                meta = {}
            if meta:
                inner_exit = meta.get("exit_code")
                summary["injection_count"] = meta.get("injection_count")
                summary["oracle"] = meta.get("oracle_pass")
                summary["terminal"] = (
                    meta.get("terminal")
                    or (meta.get("classification") or {}).get("terminal_state"))
                summary["terminal_reason"] = (
                    meta.get("classification") or {}).get(
                        "terminal_state_reason")
                summary["elapsed"] = meta.get("elapsed_seconds",
                                              summary.get("elapsed"))
                summary["injection_events"] = (
                    meta.get("injection", {}).get("events"))
                summary["trace_completeness"] = (
                    meta.get("trace") or {}).get("completeness")
                summary["seed"] = summary.get("seed") or meta.get("seed")
                crash_by_fault = bool(meta.get("crash_evidence"))
                if (meta.get("classification") or {}).get("run_status") == \
                        "TIMEOUT":
                    runner_status = STATUS_TIMEOUT
            watchdog = any_watchdog_marker(outdir)
            inj = first_injection(outdir)
            if inj:
                summary["first_injection"] = inj

        # Common provenance population (L-D02/L-D04): seed, terminal,
        # workload and the executed FaultCommand all come from the run
        # artifacts, never from a re-derived argv.
        if not meta and (outdir / "pilot_meta.json").exists():
            try:
                meta = json.load(open(outdir / "pilot_meta.json"))
            except (json.JSONDecodeError, OSError) as exc:
                parse_error = parse_error or repr(exc)
                meta = {}
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
        # The oracle verdict key always exists so "oracle parsed" is a real
        # fact of the run, even when the verdict itself is unknown (None).
        summary.setdefault("oracle", None)
        if summary.get("binary_sha") is None:
            summary["binary_sha"] = binary_sha
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError,
            KeyError, ValueError, IndexError, EOFError) as exc:
        # Any parse/execution failure becomes an explicit FAILED row; it is
        # never allowed to escape and be dropped from the campaign tally.
        parse_error = repr(exc)
        if info is None:
            info = {"exit_code": None, "timed_out": False, "pid": None,
                    "elapsed": None, "status": STATUS_FAILED}

    # Write a provisional summary so output validation can require it.
    summary["status"] = STATUS_RUNNING
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))

    exit_code = inner_exit if inner_exit is not None else (
        info.get("exit_code") if info else None)
    timed_out = bool(info and info.get("timed_out"))
    source = terminal_source(
        timed_out=timed_out, exit_code=exit_code, watchdog=watchdog,
        text=(info or {}).get("stderr") or "")
    validation = validate_outputs(model, outdir, role=role,
                                  parse_error=parse_error)
    status = measured_status(
        model=model, role=role, terminal=summary.get("terminal"),
        oracle_pass=summary.get("oracle"), exit_code=exit_code,
        timed_out=timed_out, validation_status=validation["status"],
        parse_error=parse_error, runner_status=runner_status,
        crash_by_fault=crash_by_fault)
    ended_at = _now_iso()

    summary.update(status=status, terminal_source=source,
                   ended_at=ended_at, timed_out=timed_out,
                   timeout_seconds=timeout_seconds,
                   output_validation=validation,
                   crash_by_fault=crash_by_fault,
                   parse_error=parse_error)
    if summary.get("exit_code") is None:
        summary["exit_code"] = exit_code
    if summary.get("pid") is None:
        summary["pid"] = (info or {}).get("pid")
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2))
    write_campaign_json(outdir, campaign_record(
        campaign_id=campaign_id, model=model, context=f"R{ctx_idx:02d}",
        role=role, sample_run_id=sample_run_id, seed=seed, status=status,
        binary_sha=binary_sha, config_sha=config_sha, elf_sha=elf_sha,
        started_at=started_at, ended_at=ended_at, exit_code=exit_code,
        timed_out=timed_out, terminal_source=source,
        pid=(info or {}).get("pid"), timeout_seconds=timeout_seconds,
        terminal=summary.get("terminal"),
        terminal_reason=summary.get("terminal_reason"),
        output_validation=validation,
        parse_error=parse_error, attempt_id=attempt_id))

    # A terminal attempt record is written ONLY after the evidence exists:
    # the required outputs, their SHA256 hashes, and the parsed oracle.
    artifact_names = required_outputs(model, role)
    artifacts = _attempt_artifact_hashes(outdir, artifact_names)
    oracle_parsed = ("oracle" in summary and "terminal" in summary)
    outputs_complete = (not validation["missing"]
                        and set(artifact_names) <= set(artifacts))
    accepted = (status in run_state.CANONICAL_ACCEPTED
                and outputs_complete and oracle_parsed)
    run_state.write_attempt_record(adir, {
        "attempt_id": attempt_id, "campaign_id": campaign_id,
        "model": model, "context": f"R{ctx_idx:02d}", "role": role,
        "sample_run_id": sample_run_id, "seed": seed,
        "status": status, "started_at": started_at, "ended_at": ended_at,
        "binary_sha": binary_sha, "config_sha": config_sha,
        "elf_sha": elf_sha, "run_dir": str(run_dir),
        "attempt_dir": str(adir), "terminal": summary.get("terminal"),
        "terminal_reason": summary.get("terminal_reason"),
        "oracle": summary.get("oracle"), "oracle_parsed": oracle_parsed,
        "exit_code": exit_code, "timed_out": timed_out,
        "terminal_source": source, "pid": (info or {}).get("pid"),
        "artifacts": artifacts,
        "output_validation": validation,
        "accepted_canonical": accepted,
        "reason": (validation.get("missing") and
                   "MISSING_OUTPUT:" + ",".join(validation["missing"]))
                  or summary.get("terminal_reason"),
    })
    if accepted:
        try:
            run_state.write_canonical(run_dir, {
                "campaign_id": campaign_id, "attempt_id": attempt_id,
                "model": model, "context": f"R{ctx_idx:02d}", "role": role,
                "sample_run_id": sample_run_id, "seed": seed,
                "status": status, "terminal": summary.get("terminal"),
                "written_at": ended_at, "registration": "RUNNER",
            })
        except RuntimeError as exc:
            # A different canonical already exists: never replace it.  This
            # task is recorded as an integrity failure, not as a new result.
            status = STATUS_HASH_MISMATCH
            summary["status"] = status
            summary["canonical_conflict"] = repr(exc)
            (outdir / "summary.json").write_text(json.dumps(summary,
                                                           indent=2))
            write_campaign_json(outdir, campaign_record(
                campaign_id=campaign_id, model=model,
                context=f"R{ctx_idx:02d}", role=role,
                sample_run_id=sample_run_id, seed=seed, status=status,
                binary_sha=binary_sha, config_sha=config_sha,
                elf_sha=elf_sha, started_at=started_at, ended_at=ended_at,
                exit_code=exit_code, timed_out=timed_out,
                terminal_source=source, pid=(info or {}).get("pid"),
                timeout_seconds=timeout_seconds,
                terminal=summary.get("terminal"),
                terminal_reason=summary.get("terminal_reason"),
                output_validation=validation, parse_error=parse_error,
                attempt_id=attempt_id, canonical_conflict=repr(exc)))
            record = run_state.read_attempt_record(adir) or {}
            record.update(status=status, reason="CANONICAL_CONFLICT",
                          accepted_canonical=False,
                          canonical_conflict=repr(exc))
            run_state.write_attempt_record(adir, record)
    _publish_attempt_view(run_dir, adir)

    row = dict(base_row)
    row.update(summary)
    row.update(status=status, terminal_source=source, ended_at=ended_at,
               timed_out=timed_out, exit_code=exit_code,
               output_validation=validation, parse_error=parse_error,
               attempt_id=attempt_id, attempt_dir=str(adir),
               canonical=accepted and status in run_state.CANONICAL_ACCEPTED)
    return row


def main(argv=None):
    global OUT_BASE, SUMMARY_CSV, FORCE
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="all")
    ap.add_argument("--roles", default="fault,control")
    ap.add_argument("--contexts", default="1,2,3,4,5")
    ap.add_argument("--out-base", default=str(ROOT / "runs/lsu/formal_v333"),
                    help="run directory base (default: the formal campaign)")
    ap.add_argument("--out-csv", default=None,
                    help="RAW CSV path (default: "
                         "<out-base>/LSU_Fault_Control_Pair_RAW.csv, resolved "
                         "at call time; never a hard-coded historical root)")
    ap.add_argument("--force", action="store_true",
                    help="allow overwriting an existing run dir (never "
                         "bypasses the campaign lock)")
    ap.add_argument("--resume", action="store_true",
                    help="continue an existing campaign: skip accepted "
                         "tasks, retry failed ones as a new attempt")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the exact command for every row and exit; "
                         "no run dir, summary or CSV is written")
    ap.add_argument("--campaign-id", default=CAMPAIGN_ID_DEFAULT,
                    help="campaign id recorded in every run's campaign.json")
    ap.add_argument("--expected-binary-sha", default=EXPECTED_BINARY_SHA256,
                    help="frozen gem5.opt SHA256 enforced at preflight")
    ap.add_argument("--expected-config-sha", default=EXPECTED_CONFIG_SHA256,
                    help="frozen lsu_proxy.py SHA256 enforced at preflight")
    ap.add_argument("--expected-elf-sha", default=None,
                    help="optional workload ELF SHA256 enforced at preflight")
    args = ap.parse_args(argv)
    OUT_BASE = Path(args.out_base)
    FORCE = args.force
    # Resolve the RAW CSV against the SELECTED campaign root at call time.
    SUMMARY_CSV = (Path(args.out_csv) if args.out_csv else
                   OUT_BASE / "LSU_Fault_Control_Pair_RAW.csv")
    global EXPECTED_BINARY_SHA, EXPECTED_CONFIG_SHA, EXPECTED_ELF_SHA
    EXPECTED_BINARY_SHA = args.expected_binary_sha
    EXPECTED_CONFIG_SHA = args.expected_config_sha
    EXPECTED_ELF_SHA = args.expected_elf_sha
    models = list(MODELS) if args.models == "all" else args.models.split(",")
    roles = args.roles.split(",")
    ctxs = [int(x) for x in args.contexts.split(",")]
    selected = [m for m in models if m in CONTEXTS]
    for model in models:
        if model not in CONTEXTS:
            print(f"skip unknown model {model}", file=sys.stderr)

    task_triples = [(model, ctx, role) for model in selected
                    for ctx in ctxs for role in roles]

    if args.dry_run:
        # Validation only: no campaign directory, no gem5 process.
        count = 0
        for model, ctx, role in task_triples:
            outdir = OUT_BASE / run_state.task_tag(model, ctx, role)
            cmd = planned_command(model, ctx, role, outdir)
            print(f"DRY-RUN {model} R{ctx:02d} {role}: "
                  f"{' '.join(cmd)}", flush=True)
            count += 1
        gate = dry_run_validation(
            models=selected, ctxs=ctxs, roles=roles, out_base=OUT_BASE,
            campaign_id=args.campaign_id,
            expected_binary_sha=args.expected_binary_sha,
            expected_config_sha=args.expected_config_sha)
        print(f"dry-run: {count} commands; no run dirs written")
        print("DRY_RUN_SUMMARY " + json.dumps(gate, sort_keys=True),
              flush=True)
        if gate["ok"]:
            print("READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES", flush=True)
            return 0
        print("READY_TO_LAUNCH_FORMAL_CAMPAIGN=NO", file=sys.stderr)
        return 2

    # Without --resume the campaign root must be fresh: a stale root could
    # silently mix evidence from a different/partial campaign.
    if not args.resume and OUT_BASE.exists() and any(OUT_BASE.iterdir()):
        print(f"REFUSING non-empty campaign root {OUT_BASE}: "
              "pass --resume to continue an existing campaign",
              file=sys.stderr)
        return 2

    OUT_BASE.mkdir(parents=True, exist_ok=True)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    try:
        # Campaign-scoped lock, resolved at CALL time from --out-base.  --force
        # never bypasses it: a second runner would corrupt shared evidence.
        with campaign_lock(OUT_BASE, args.campaign_id):
            # Campaign-root provenance record: written before the first task.
            identity_tasks = [
                (model, ctx,
                 resolve_workload(model, CONTEXTS[model].get("workload")))
                for model in selected for ctx in ctxs]
            write_campaign_identity(OUT_BASE, args.campaign_id,
                                    tasks=identity_tasks)
            for model, ctx, role in task_triples:
                print(f"== {model} R{ctx:02d} {role}", flush=True)
                try:
                    if args.resume:
                        run_dir = OUT_BASE / run_state.task_tag(model, ctx,
                                                               role)
                        state = _ensure_canonical(run_dir, args.campaign_id)
                        if state["state"] == STATUS_HASH_MISMATCH:
                            print("   RESUME REFUSED: "
                                  f"{run_dir} {state.get('reason')} "
                                  "(HASH_MISMATCH is never retried)",
                                  file=sys.stderr)
                            return 2
                        if state["state"] in run_state.CANONICAL_ACCEPTED:
                            rows.append(_resumed_row(
                                model, ctx, role, run_dir, state,
                                args.campaign_id))
                            print(f"   status {rows[-1].get('status')} "
                                  "(resumed; no execution)", flush=True)
                            write_campaign_index(
                                OUT_BASE, build_campaign_index(
                                    OUT_BASE, args.campaign_id,
                                    task_triples))
                            continue
                    rows.append(run_context(model, ctx, role,
                                            campaign_id=args.campaign_id))
                except Exception as exc:  # keep the matrix going; record it
                    # An escaped exception is an execution failure: it is
                    # never silently dropped and always trips the exit.
                    row = {"model": model, "context": f"R{ctx:02d}",
                           "role": role, "status": STATUS_FAILED,
                           "campaign_id": args.campaign_id,
                           "terminal_source": TERMINAL_SOURCE_NORMAL,
                           "error": repr(exc)}
                    rows.append(row)
                    print(f"   ERROR {exc!r}", file=sys.stderr)
                print(f"   status {rows[-1].get('status')}", flush=True)
                write_campaign_index(
                    OUT_BASE,
                    build_campaign_index(OUT_BASE, args.campaign_id,
                                         task_triples))
            write_csv(rows, SUMMARY_CSV)
    except LockHeld as exc:
        print(f"LOCK_HELD: {exc}", file=sys.stderr)
        print(f"REFUSING to run: {OUT_BASE} is owned by another campaign "
              "(--force does not bypass the lock)", file=sys.stderr)
        return 3
    counts = status_summary(rows)
    print("status summary: " + ", ".join(
        f"{k}={v}" for k, v in sorted(counts.items())))
    print(f"wrote {SUMMARY_CSV} ({len(rows)} rows)")
    return campaign_exit_code(rows)


def write_csv(rows, path=SUMMARY_CSV):
    keys = ["model", "context", "role", "ordinal", "seed", "sample_run_id",
            "injection_count", "oracle", "terminal", "terminal_qualifier",
            "terminal_reason", "watchdog", "watchdog_expired",
            "deadline_cycles", "checksum", "a03_log_capped",
            "control_proof", "exit_code", "timed_out", "elapsed",
            "status", "campaign_id", "terminal_source", "started_at",
            "ended_at", "pid", "binary_sha", "config_sha", "elf_sha",
            "outdir", "attempt_id", "attempt_dir", "resumed", "canonical",
            "fault_command", "error", "parse_error"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    sys.exit(main())
