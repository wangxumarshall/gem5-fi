#!/usr/bin/env python3
"""LSU E2E causal-reconstruction campaign runner.

Design is inherited unchanged from LSU_When_v2_FINAL_FROZEN:
  * Where  : the frozen 12 LSU models and their original injector modes.
  * When   : C01-C05 context workloads x T01/T02/T03 = 10/50/90 % of the
             full-ROI eligible-event stream.
  * Control: one count-only full-ROI census per Model x Context.

New observation layers (read-only, attached only in this extension):
  * commit_trace.csv.gz v2 — every committed instruction: DynInst seqNum,
    PC, opcode, destination values, source (class,arch,phys) triples.
  * micro_snap.csv.gz    — ROB/IQ/free-list occupancy + front RAT every
    N commits (N=200 here), for the stall/watchdog chains.
  * prop_trace.csv.gz    — the existing L3 propagation tracer, with
    --prop_replay_all so every LSQ replay is visible.
  * sw markers           — the instrumented ELFs emit four `mov x28`
    instructions per software event; the commit trace turns them into an
    exact (dyn_inst_seq, event tag, address, value) record.  No load, no
    store, no syscall: the eligible-event stream is unchanged (verified by
    the control census against the frozen When-v2 counts).

Run IDs are E2E-<Model>-<Context>-<Timing>[-CTRL], and every state records
the mapped When-v2 RunID.  The frozen results are never touched.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(os.environ.get("LSU_E2E_ROOT", str(Path(__file__).resolve().parents[1])))
FROZEN_ROOT = Path(os.environ.get("LSU_WORKSPACE_ROOT", str(ROOT.parent)))
REPO = Path(os.environ.get("LSU_GEM5_ROOT", str(FROZEN_ROOT / "repo")))
GEM5 = REPO / "build/ARM/gem5.opt"
CONFIG = ROOT / "configs/lsu_proxy_e2e.py"
WORK = ROOT / "workloads"
RUNS = ROOT / "results"
STATE = RUNS / "state"
LOGS = ROOT / "logs"
INPUT_XLSX = Path(os.environ.get("LSU_INPUT_XLSX", str(FROZEN_ROOT / "inputs/gem5-fi-LSU-Final-Paper-Experiment.xlsx")))

MODELS = ("A01", "A03", "LQ04", "SQ01", "SQ03", "SP05",
          "FW02", "FW05", "MD04", "RP01", "DA04", "LP01")
CONTEXTS = ("C01", "C02", "C03", "C04", "C05")
TIMINGS = {"T01": Decimal("0.1"), "T02": Decimal("0.5"), "T03": Decimal("0.9")}

FAMILY = {
    "A01": "agu", "A03": "agu", "LQ04": "lq",
    "SQ01": "sq", "SQ03": "sq", "SP05": "sq",
    "FW02": "fwd_full", "FW05": "fwd_partial",
    "MD04": "md", "RP01": "md", "DA04": "align", "LP01": "lp",
}
LOG_NAME = {
    "A01": "addrpath_injections.log", "A03": "addrpath_injections.log",
    "LQ04": "lq04_injections.log",
    "SQ01": "lsq_fwd_injections.log", "SQ03": "lsq_fwd_injections.log",
    "SP05": "lsq_fwd_injections.log", "FW02": "lsq_fwd_injections.log",
    "FW05": "lsq_fwd_injections.log", "MD04": "md04_injections.log",
    "RP01": "lsq_fwd_injections.log", "DA04": "lsq_fwd_injections.log",
    "LP01": "l1d_fwd_injections.log",
}
TIMEOUT = {"A03": 900, "RP01": 900, "SQ03": 600, "SP05": 600,
           "LQ04": 600}
DEFAULT_TIMEOUT = 480

_state_lock = threading.Lock()


# ---------------------------------------------------------------------------
def sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


_BINARY_SHA: str | None = None


def gem5_sha() -> str | None:
    global _BINARY_SHA
    if _BINARY_SHA is None:
        _BINARY_SHA = sha256(GEM5)
    return _BINARY_SHA


def load_matrix() -> dict:
    import openpyxl
    wb = openpyxl.load_workbook(INPUT_XLSX, data_only=True)
    ws = wb["16.When全交叉矩阵"]
    rows = list(ws.iter_rows(values_only=True))
    head = list(rows[0])
    out = {"faults": [], "seed": {}}
    for r in rows[1:]:
        d = dict(zip(head, r))
        mid, ctx, tid = d.get("ModelID"), d.get("ContextID"), d.get("TimingID")
        if not mid or not ctx or not tid:
            continue
        seed = int(d["Seed_by_ModelContext"])
        percent = Decimal(str(d["TimingPercent"]))
        out["seed"][(mid, ctx)] = seed
        out["faults"].append({
            "model": mid, "context": ctx, "timing": tid,
            "seed": seed, "percent": percent,
            "old_run_id": f"{mid}-WHEN-{ctx}-{tid}-FAULT",
            "task_id": f"E2E-{mid}-{ctx}-{tid}-FAULT",
        })
    return out


def ordinal(n: int, p: Decimal) -> int:
    v = Decimal(1) + Decimal(n - 1) * p
    return int(v.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def select_ordinals(n: int) -> dict:
    return {t: ordinal(n, p) for t, p in TIMINGS.items()}


def workload(model: str, context: str) -> Path:
    return WORK / "bin" / f"{FAMILY[model]}_{context}"


def golden(model: str, context: str) -> str:
    return workload(model, context).with_suffix(".golden").read_text().strip()


# ---------------------------------------------------------------------------
# model command lines (identical injector semantics to the frozen campaign)
# ---------------------------------------------------------------------------
def census_extra(model: str) -> list[str]:
    if model in ("A01", "A03"):
        mode = ("a01_bit3_load" if model == "A01"
                else "a03_bit3_stuck0_load")
        tier = "F0" if model == "A01" else "F5"
        return ["--chaos_addrpath", "--agu_pre_mode", mode,
                "--addrpath_lsu_tier", tier,
                "--addrpath_max_faults", "1" if model == "A01" else "0",
                "--addrpath_warmup_events", "0",
                "--addrpath_span_events", "10",
                "--addrpath_count_only"]
    if model == "LQ04":
        return ["--chaos_lq04", "--lq04_count_only",
                "--lq04_probe_first_n", "1000000"]
    if model == "SQ01":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sq01_bit3",
                "--lsqfwd_lsu_tier", "F0", "--lsqfwd_warmup_events", "0",
                "--lsqfwd_span_events", "10", "--max_faults", "1",
                "--chaos_lsqfwd_count_only"]
    if model == "SQ03":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sq03_canwb",
                "--max_faults", "1", "--chaos_lsqfwd_count_only"]
    if model == "SP05":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sp05_complete",
                "--max_faults", "1", "--chaos_lsqfwd_count_only"]
    if model == "FW02":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
                "--max_faults", "1", "--chaos_lsqfwd_count_only"]
    if model == "FW05":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "fw05_older_src",
                "--max_faults", "1", "--chaos_lsqfwd_count_only"]
    if model == "DA04":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "da04_be_bit0",
                "--lsqfwd_lsu_tier", "F0", "--lsqfwd_warmup_events", "0",
                "--lsqfwd_span_events", "10", "--max_faults", "1",
                "--chaos_lsqfwd_count_only"]
    if model == "MD04":
        return ["--chaos_md04", "--md04_first_clock", "0",
                "--md04_max_faults", "1", "--md04_probability", "1.0",
                "--md04_count_only"]
    if model == "RP01":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "rp01_count_only",
                "--max_faults", "1", "--rp01_event_ordinal", "0"]
    if model == "LP01":
        return ["--chaos_l1dfwd", "--l1dfwd_first_clock", "0",
                "--l1dfwd_max_faults", "1", "--l1dfwd_fault_mask", "0x8",
                "--l1dfwd_count_only"]
    raise KeyError(model)


def fault_extra(model: str, seed: int, k: int) -> list[str]:
    o = str(k)
    if model == "A01":
        return ["--chaos_addrpath", "--agu_pre_mode", "a01_bit3_load",
                "--addrpath_lsu_tier", "F0", "--addrpath_max_faults", "1",
                "--addrpath_warmup_events", "0", "--addrpath_span_events",
                "10", "--addrpath_rng_seed", str(seed),
                "--addrpath_event_ordinal", o]
    if model == "A03":
        return ["--chaos_addrpath", "--agu_pre_mode", "a03_bit3_stuck0_load",
                "--addrpath_lsu_tier", "F5", "--addrpath_max_faults", "0",
                "--addrpath_warmup_events", "0", "--addrpath_rng_seed",
                str(seed), "--addrpath_event_ordinal", o,
                "--addrpath_watchdog_cycles", "1000000"]
    if model == "LQ04":
        return ["--chaos_lq04", "--lq04_event_ordinal", o,
                "--lq04_max_faults", "1", "--lq04_rng_seed", str(seed),
                "--lq04_watchdog_cycles", "500000000"]
    if model == "SQ01":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sq01_bit3",
                "--lsqfwd_lsu_tier", "F0", "--lsqfwd_warmup_events", "0",
                "--lsqfwd_span_events", "10", "--max_faults", "1",
                "--rng_seed", str(seed), "--lsqfwd_event_ordinal", o]
    if model == "SQ03":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sq03_canwb",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--lsqfwd_event_ordinal", o,
                "--sq03_watchdog_cycles", "500000000"]
    if model == "SP05":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "sp05_complete",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--sp05_event_ordinal", o,
                "--sp05_watchdog_cycles", "500000000"]
    if model == "FW02":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "f6_fw02",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--lsqfwd_event_ordinal", o]
    if model == "FW05":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "fw05_older_src",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--lsqfwd_event_ordinal", o]
    if model == "DA04":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "da04_be_bit0",
                "--lsqfwd_lsu_tier", "F0", "--lsqfwd_warmup_events", "0",
                "--lsqfwd_span_events", "10", "--max_faults", "1",
                "--rng_seed", str(seed), "--lsqfwd_event_ordinal", o]
    if model == "MD04":
        return ["--chaos_md04", "--md04_first_clock", "0",
                "--md04_max_faults", "1", "--md04_probability", "1.0",
                "--md04_rng_seed", str(seed), "--md04_event_ordinal", o]
    if model == "RP01":
        return ["--chaos_lsqfwd", "--lsq_struct_mode", "rp01_skip_replay",
                "--max_faults", "1", "--rng_seed", str(seed),
                "--rp01_event_ordinal", o,
                "--rp01_watchdog_cycles", "20000000"]
    if model == "LP01":
        return ["--chaos_l1dfwd", "--l1dfwd_first_clock", "0",
                "--l1dfwd_max_faults", "1", "--l1dfwd_fault_mask", "0x8",
                "--l1dfwd_rng_seed", str(seed),
                "--l1dfwd_event_ordinal", o]
    raise KeyError(model)


def build_cmd(model: str, context: str, outdir: Path, extra: list[str],
              probability: float) -> list[str]:
    return [str(GEM5), f"--outdir={outdir}", str(CONFIG),
            f"--cmd={workload(model, context)}", "--cpu", "O3",
            "--variant", "B0", "--probability", str(probability),
            "--chaos_propagation", "--prop_replay_all",
            "--prop_trace_file", "prop_trace.csv.gz",
            "--chaos_ctrace", "--ctrace_file", "commit_trace.csv.gz",
            "--chaos_msnap", "--msnap_every", "200",
            "--msnap_file", "micro_snap.csv.gz"] + extra


# ---------------------------------------------------------------------------
def run_gem5(cmd: list[str], timeout: int, outdir: Path) -> dict:
    started = time.time()
    try:
        p = subprocess.Popen(cmd, cwd=REPO, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True,
                             start_new_session=True)
    except OSError as exc:
        return {"returncode": 126, "stdout": "", "stderr": repr(exc),
                "timed_out": False, "elapsed": 0.0}
    timed_out = False
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except OSError:
            p.kill()
        try:
            out, err = p.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            out, err = "", ""
        err += "\nTIMEOUT: wall-clock limit reached; process group killed\n"
    (outdir / "stdout.log").write_text(out or "", errors="replace")
    (outdir / "stderr.log").write_text(err or "", errors="replace")
    return {"returncode": 124 if timed_out else p.returncode,
            "stdout": out or "", "stderr": err or "",
            "timed_out": timed_out, "elapsed": round(time.time() - started, 2)}


def parse_checksum(text: str) -> str | None:
    m = re.findall(r"checksum=0x([0-9a-fA-F]+)", text)
    if m:
        return m[-1].lower()
    m = re.findall(r"^\s*([0-9a-fA-F]{16})\s*$", text, re.MULTILINE)
    return m[-1].lower() if m else None


def injection_count(text: str) -> int:
    vals = []
    for pat in (r"faults_injected:\s*(\d+)",
                r"CHAOS_FW02_SUMMARY:.*?suppressed=(\d+)",
                r"CHAOS_SQ03_STATUS:.*?injected=(\d+)",
                r"CHAOS_SP05_STATUS:.*?injected=(\d+)",
                r"CHAOS_RP01_STATUS:.*?injected=(\d+)",
                r"CHAOS_LQ04_INJECTION:.*?injected=(\d+)",
                r"CHAOS_L0_FUNNEL:.*?injected=(\d+)",
                r"FUNNEL:.*?injected=(\d+)"):
        for m in re.finditer(pat, text):
            vals.append(int(m.group(1)))
    return max(vals) if vals else 0


def observed_ordinal(model: str, text: str) -> int | None:
    if model == "A03":
        m = re.search(r"A03_STREAM: event_ordinal=(\d+)", text)
        if m:
            return int(m.group(1))
    if model == "RP01":
        m = re.search(r"RP01_SKIP_REPLAY ordinal=(\d+)", text)
        if m:
            return int(m.group(1))
    if model == "LQ04":
        m = re.search(r"CHAOS_LQ04_INJECTION:.*?\bordinal=(\d+)", text)
        if m:
            return int(m.group(1))
    if model in ("A01", "A03"):
        m = re.search(r"FUNNEL: attempted=\d+ eligible=(\d+) injected=1",
                      text)
        if m:
            return int(m.group(1))
    m = re.search(r"eligible_ordinal=(\d+)", text)
    if m:
        return int(m.group(1))
    m = re.search(r"EligibleOrdinal:\s*(\d+)", text)
    if m:
        return int(m.group(1))
    return None


def parse_eligible_lines(model: str, text: str) -> list[dict]:
    events, seen = [], set()
    for line in text.splitlines():
        ev = None
        if line.startswith("CHAOS_ELIGIBLE:"):
            body = line.split(":", 1)[1]
            kv = {}
            for part in body.split(";"):
                if "=" in part:
                    k, v = part.split("=", 1)
                    kv[k.strip()] = v.strip()
            if "ordinal" in kv:
                ev = {**kv, "ordinal": int(kv["ordinal"]), "raw": line}
        elif "RP01_ELIGIBLE ordinal=" in line:
            kv = dict(re.findall(r"(\w+)=([^\s]+)", line))
            ev = {**kv, "ordinal": int(kv["ordinal"]), "raw": line}
        elif "CHAOS_LQ04_ELIGIBLE_PROBE" in line:
            kv = dict(re.findall(r"(\w+)=([^\s]+)", line))
            ev = {**kv, "ordinal": int(kv["ordinal"]), "raw": line}
        if ev and ev["ordinal"] not in seen:
            seen.add(ev["ordinal"])
            events.append(ev)
    events.sort(key=lambda e: e["ordinal"])
    return events


def census_hash(events: list[dict]) -> str:
    h = hashlib.sha256()
    for e in events:
        h.update((e["raw"].strip() + "\n").encode())
    return h.hexdigest()


def census_event(ctrl: dict, k: int) -> dict | None:
    p = Path(ctrl.get("outdir", "")) / "eligible_events.csv"
    try:
        with open(p, newline="") as fh:
            for row in csv.DictReader(fh):
                if int(row["ordinal"]) == k:
                    ev = parse_eligible_lines(ctrl.get("model", ""),
                                              row["raw"])
                    return ev[0] if ev else None
    except (OSError, ValueError, KeyError):
        return None
    return None


def _injection_fields(model: str, text: str) -> dict:
    out = {}
    if model == "A01":
        m = re.search(r"A01_EA:.*?dyn_inst_seq=(\d+);pc=([0-9a-f]+);"
                      r"golden_ea=([0-9a-f]+)", text)
        if m:
            out = {"dyn_inst_seq": m[1], "pc_int": str(int(m[2], 16)),
                   "ea_int": str(int(m[3], 16))}
    elif model == "FW02":
        m = re.search(r"f6_fw02_suppress.*?load_seq: (\d+).*?store_seq: (\d+)",
                      text, re.S)
        if m:
            out = {"load_seq": m[1], "store_seq": m[2]}
    elif model == "FW05":
        m = re.search(r"FaultType: fw05_older_src, LoadSeq: (\d+), "
                      r"TrueSeq: (\d+), AltSeq: (\d+)", text)
        if m:
            out = {"load_seq": m[1], "true_seq": m[2], "alt_seq": m[3]}
    elif model == "SQ01":
        m = re.search(r"FaultType: sq01_bit3_flip, seq: (\d+), "
                      r"sq_idx: (\d+), entry_generation: (\d+)", text)
        if m:
            out = {"dyn_inst_seq": m[1], "sq_idx": m[2], "sq_gen": m[3]}
    elif model == "SQ03":
        m = re.search(r"executeStore_canWB, store_seq=(\d+), "
                      r"sq_idx=(\d+), sq_gen=(\d+)", text)
        if m:
            out = {"store_seq": m[1], "sq_idx": m[2], "sq_gen": m[3]}
    elif model == "SP05":
        m = re.search(r"writebackStores_prematureComplete, store_seq=(\d+), "
                      r"sq_idx=(\d+), sq_gen=(\d+)", text)
        if m:
            out = {"store_seq": m[1], "sq_idx": m[2], "sq_gen": m[3]}
    elif model == "DA04":
        m = re.search(r"FaultModel: DA04, seq: (\d+), sq_idx: (\d+), "
                      r"entry_generation: (\d+)", text)
        if m:
            out = {"dyn_inst_seq": m[1], "sq_idx": m[2], "sq_gen": m[3]}
    elif model == "MD04":
        m = re.search(r"Site: checkViolations, load_seq=(\d+), "
                      r"store_seq=(\d+)", text)
        if m:
            out = {"load_seq": m[1], "store_seq": m[2]}
    elif model == "LP01":
        m = re.search(r"Site: l1d_load_complete.*?dyn_inst_seq=(\d+)", text)
        if m:
            out = {"dyn_inst_seq": m[1]}
    return out


def _norm_num(v) -> int | None:
    s = str(v).strip().lower()
    try:
        return int(s, 16) if s.startswith("0x") else int(s, 10)
    except ValueError:
        return None


def identity_matches(model: str, text: str, ev: dict | None) -> bool | None:
    if not ev:
        return None
    fields = _injection_fields(model, text)
    if not fields:
        return None
    checked = 0
    for k, v in fields.items():
        ck = {"pc_int": "pc", "ea_int": "ea"}.get(k, k)
        if ck not in ev:
            continue
        checked += 1
        gi, wi = _norm_num(v), _norm_num(ev[ck])
        if gi is None or wi is None:
            if str(v).lower() != str(ev[ck]).lower():
                return False
        elif gi != wi:
            return False
    return True if checked else None


# ---------------------------------------------------------------------------
def setup_outdir(task_id: str, attempt: int, kind: str) -> Path:
    base = RUNS / ("controls" if kind == "control" else "faults")
    out = base / task_id / f"attempt_{attempt}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    return out


def write_state(task: dict, state: dict) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    p = STATE / f"{task['task_id']}.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True))
    tmp.replace(p)


def read_state(task_id: str) -> dict | None:
    p = STATE / f"{task_id}.json"
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def status_summary() -> dict:
    counts, total = {}, 0
    for p in STATE.glob("*.json"):
        total += 1
        try:
            s = json.loads(p.read_text())
        except ValueError:
            s = {}
        k = s.get("status", "UNKNOWN")
        counts[k] = counts.get(k, 0) + 1
    return {"updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_state_files": total, "status_counts": counts}


def write_run_status() -> None:
    p = RUNS / "run_status.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(status_summary(), indent=2, sort_keys=True))
    tmp.replace(p)


def artifact_record(out: Path) -> dict:
    rec = {}
    for name in ("commit_trace.csv.gz", "micro_snap.csv.gz",
                 "prop_trace.csv.gz", "stats.txt", "config.ini"):
        p = out / name
        rec[name] = {"exists": p.exists(),
                     "size": p.stat().st_size if p.exists() else None,
                     "sha256": sha256(p) if p.exists() else None}
    return rec


# ---------------------------------------------------------------------------
def do_control(task: dict, attempt: int, retries: int) -> dict:
    model, ctx = task["model"], task["context"]
    out = setup_outdir(task["task_id"], attempt, "control")
    cmd = build_cmd(model, ctx, out, census_extra(model), 1.0)
    (out / "command.txt").write_text(" ".join(cmd) + "\n")
    run = run_gem5(cmd, TIMEOUT.get(model, DEFAULT_TIMEOUT), out)
    log = out / LOG_NAME[model]
    text = log.read_text(errors="replace") if log.exists() else ""
    events = parse_eligible_lines(model, text + "\n" + run["stdout"])
    got = parse_checksum(run["stdout"])
    want = golden(model, ctx)
    inj = injection_count(text + "\n" + run["stdout"])
    n = len(events)
    r = select_ordinals(n) if n else {}
    state = {
        "task_id": task["task_id"], "kind": "control",
        "run_id": task["task_id"], "old_run_id": task["old_run_id"],
        "model": model, "context": ctx, "seed": task["seed"],
        "attempt": attempt, "outdir": str(out),
        "exit_code": run["returncode"], "timed_out": run["timed_out"],
        "elapsed": run["elapsed"],
        "oracle_expected": want, "oracle_got": got,
        "oracle_pass": got == want,
        "injection_count": inj,
        "eligible_n": n, "eligible_ordinals": r,
        "eligible_hash": census_hash(events) if events else None,
        "checksum_observed": got,
        "binary_sha": gem5_sha(), "elf_sha": sha256(workload(model, ctx)),
        "config_sha": sha256(CONFIG),
        "artifacts": artifact_record(out),
        "status": "PENDING",
    }
    if n:
        with open(out / "eligible_events.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ordinal", "raw"])
            for e in events:
                w.writerow([e["ordinal"], e["raw"]])
    if run["timed_out"]:
        state["status"] = "TIMEOUT"
    elif run["returncode"] != 0:
        state["status"] = "CONTROL_EXIT_NONZERO"
    elif inj != 0:
        state["status"] = "CONTROL_INJECTED"
    elif got != want:
        state["status"] = "CONTROL_ORACLE_FAIL"
    elif n < 3:
        state["status"] = "INSUFFICIENT_ELIGIBLE"
    elif len(set(r.values())) != 3:
        state["status"] = "ORDINALS_NOT_DISTINCT"
    else:
        state["status"] = "COMPLETED"
    state["attempts_allowed"] = retries
    return state


def do_fault(task: dict, attempt: int, retries: int) -> dict:
    model, ctx, t = task["model"], task["context"], task["timing"]
    ctrl = read_state(f"E2E-{model}-{ctx}-CTRL")
    out = setup_outdir(task["task_id"], attempt, "fault")
    if not ctrl or ctrl.get("status") != "COMPLETED":
        return {"task_id": task["task_id"], "kind": "fault",
                "status": "BLOCKED_NO_CONTROL", "attempt": attempt,
                "model": model, "context": ctx, "timing": t,
                "outdir": str(out)}
    k = ctrl["eligible_ordinals"][t]
    cmd = build_cmd(model, ctx, out, fault_extra(model, task["seed"], k),
                    1.0)
    (out / "command.txt").write_text(" ".join(cmd) + "\n")
    run = run_gem5(cmd, TIMEOUT.get(model, DEFAULT_TIMEOUT), out)
    log = out / LOG_NAME[model]
    text = log.read_text(errors="replace") if log.exists() else ""
    alltext = text + "\n" + run["stdout"] + "\n" + run["stderr"]
    inj = injection_count(alltext)
    obs = observed_ordinal(model, alltext)
    ev = census_event(ctrl, k)
    ident = identity_matches(model, alltext, ev)
    if obs is None and ident is True:
        obs = k
    got = parse_checksum(run["stdout"])
    want = golden(model, ctx)
    oracle_pass = got == want
    watchdog = bool(re.search(
        r"WATCHDOG_EXPIRED|WATCHDOG=EXPIRED|CHAOS_A03_WATCHDOG", alltext))
    if run["timed_out"]:
        terminal, status = "HANG", "COMPLETED_HANG"
    elif watchdog:
        terminal, status = "HANG_WATCHDOG", "COMPLETED_HANG"
    elif run["returncode"] != 0:
        terminal, status = "CRASH", "COMPLETED_CRASH"
    elif inj == 0:
        terminal, status = "NO_INJECTION", "INJECTION_NOT_OBSERVED"
    elif oracle_pass:
        terminal, status = "NO_VISIBLE_MISMATCH", "COMPLETED"
    else:
        terminal, status = "SDC", "COMPLETED_SDC"
    state = {
        "task_id": task["task_id"], "kind": "fault",
        "run_id": task["task_id"], "old_run_id": task["old_run_id"],
        "model": model, "context": ctx, "timing": t,
        "seed": task["seed"], "timing_percent": str(task["percent"]),
        "selected_ordinal": k, "observed_ordinal": obs,
        "ordinal_match": (obs == k) if obs is not None else None,
        "identity_match": ident, "census_event": ev,
        "attempt": attempt, "outdir": str(out),
        "exit_code": run["returncode"], "timed_out": run["timed_out"],
        "elapsed": run["elapsed"],
        "oracle_expected": want, "oracle_got": got,
        "oracle_pass": oracle_pass,
        "injection_count": inj, "watchdog": watchdog,
        "terminal": terminal, "status": status,
        "binary_sha": gem5_sha(), "elf_sha": sha256(workload(model, ctx)),
        "config_sha": sha256(CONFIG),
        "control_run_id": ctrl["run_id"],
        "control_hash": ctrl.get("eligible_hash"),
        "artifacts": artifact_record(out),
    }
    if status.startswith("COMPLETED") and obs is not None and obs != k:
        state["status"] = "ORDINAL_MISMATCH"
    return state


def execute(task: dict, retries: int) -> dict:
    st = {}
    for attempt in range(1, retries + 1):
        st = (do_control(task, attempt, retries) if task["kind"] == "control"
              else do_fault(task, attempt, retries))
        st["attempt"] = attempt
        write_state(task, st)
        with _state_lock:
            write_run_status()
        if st["status"] in ("COMPLETED", "COMPLETED_SDC",
                            "COMPLETED_HANG", "COMPLETED_CRASH",
                            "BLOCKED_NO_CONTROL", "INSUFFICIENT_ELIGIBLE",
                            "ORDINALS_NOT_DISTINCT", "ORDINAL_MISMATCH"):
            return st
        time.sleep(min(5 * attempt, 20))
    return st


def should_skip(task: dict) -> bool:
    st = read_state(task["task_id"])
    if not st:
        return False
    if st.get("binary_sha") != gem5_sha():
        return False
    try:
        cur_elf = sha256(workload(task["model"], task["context"]))
    except OSError:
        cur_elf = None
    if not cur_elf or st.get("elf_sha") != cur_elf:
        return False
    if st.get("config_sha") != sha256(CONFIG):
        return False
    if st.get("status") not in ("COMPLETED", "COMPLETED_SDC",
                                "COMPLETED_HANG", "COMPLETED_CRASH",
                                "BLOCKED_NO_CONTROL", "INSUFFICIENT_ELIGIBLE",
                                "ORDINALS_NOT_DISTINCT"):
        return False
    out = Path(st.get("outdir", ""))
    if task["kind"] == "control":
        return (out / "eligible_events.csv").exists()
    return (out / "stdout.log").exists() and (out / "command.txt").exists()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="all",
                    choices=["census", "faults", "all"])
    ap.add_argument("--models", default="all")
    ap.add_argument("--contexts", default="C01,C02,C03,C04,C05")
    ap.add_argument("--timings", default="T01,T02,T03")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    matrix = load_matrix()
    models = (list(MODELS) if args.models == "all"
              else [m.strip() for m in args.models.split(",")])
    contexts = [c.strip() for c in args.contexts.split(",")]
    timings = [t.strip() for t in args.timings.split(",")]

    tasks = []
    if args.phase in ("census", "all"):
        for m in models:
            for c in contexts:
                tasks.append({
                    "kind": "control", "model": m, "context": c,
                    "seed": matrix["seed"][(m, c)],
                    "task_id": f"E2E-{m}-{c}-CTRL",
                    "old_run_id": f"{m}-WHEN-{c}-CTRL"})
    if args.phase in ("faults", "all"):
        for f in matrix["faults"]:
            if f["model"] in models and f["context"] in contexts \
                    and f["timing"] in timings:
                tasks.append({**f, "kind": "fault"})
    if args.limit:
        tasks = tasks[:args.limit]
    if args.resume:
        tasks = [t for t in tasks if not should_skip(t)]
    print(f"scheduled {len(tasks)} tasks (jobs={args.jobs})", flush=True)

    controls = [t for t in tasks if t["kind"] == "control"]
    faults = [t for t in tasks if t["kind"] == "fault"]
    results = []
    for group in (controls, faults):
        if not group:
            continue
        with ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(execute, t, args.retries): t for t in group}
            for fut in as_completed(futs):
                t = futs[fut]
                try:
                    st = fut.result()
                except Exception as exc:  # noqa: BLE001
                    st = {"task_id": t["task_id"],
                          "status": "RUNNER_EXCEPTION", "error": repr(exc)}
                    write_state(t, st)
                results.append(st)
                print(f"{st.get('status'):24s} {t['task_id']} "
                      f"inj={st.get('injection_count','-')} "
                      f"n={st.get('eligible_n','-')} "
                      f"term={st.get('terminal','-')}", flush=True)
        write_run_status()

    bad = [r for r in results
           if r.get("status") not in ("COMPLETED", "COMPLETED_SDC",
                                      "COMPLETED_HANG", "COMPLETED_CRASH")]
    print(f"finished {len(results)}; non-terminal {len(bad)}", flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
