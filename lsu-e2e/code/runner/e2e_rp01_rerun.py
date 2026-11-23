#!/usr/bin/env python3
"""Targeted RP01 re-run with the post-injection stall observation binary.

The observation binary is built from the same frozen source plus read-only
accessors (no replay-decision change).  Because the binary hash differs,
the controls and prepass ordinals are re-established here instead of being
copied from the original campaign.  The original results stay untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e2e_experiment as X
import e2e_lib as L

ROOT = L.EXT
SLOT = ROOT / "results_strict_rp01"
STATE = SLOT / "state"
OBS = ROOT / "bin" / "gem5.opt.obs"
OLDRES = ROOT / "results"

_lock = threading.Lock()


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def status():
    c = {}
    for p in STATE.glob("*.json"):
        try:
            s = json.loads(p.read_text()).get("status", "?")
        except ValueError:
            s = "?"
        c[s] = c.get(s, 0) + 1
    return c


def write_state(task_id, st):
    STATE.mkdir(parents=True, exist_ok=True)
    p = STATE / f"{task_id}.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=2, sort_keys=True))
    tmp.replace(p)


def read_state(task_id):
    p = STATE / f"{task_id}.json"
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def base_cmd(outdir, model, ctx, extra):
    return [str(OBS), f"--outdir={outdir}",
            str(ROOT / "configs/lsu_proxy_e2e.py"),
            f"--cmd={X.workload(model, ctx)}", "--cpu", "O3",
            "--variant", "B0", "--probability", "1.0",
            "--chaos_propagation", "--prop_replay_all",
            "--prop_trace_file", "prop_trace.csv.gz",
            "--chaos_ctrace", "--ctrace_file", "commit_trace.csv.gz",
            "--chaos_msnap", "--msnap_every", "200",
            "--msnap_file", "micro_snap.csv.gz"] + extra


def run(cmd, timeout, outdir):
    started = time.time()
    try:
        p = subprocess.Popen(cmd, cwd=str(X.REPO), stdout=subprocess.PIPE,
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
        err += "\nTIMEOUT\n"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "stdout.log").write_text(out or "", errors="replace")
    (outdir / "stderr.log").write_text(err or "", errors="replace")
    return {"returncode": 124 if timed_out else p.returncode,
            "stdout": out or "", "stderr": err or "",
            "timed_out": timed_out,
            "elapsed": round(time.time() - started, 2)}


def do_control(model, ctx, seed, attempt=1):
    tid = f"RP01OBS-{ctx}-CTRL"
    out = SLOT / "controls" / tid / f"attempt_{attempt}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    cmd = base_cmd(out, model, ctx, X.census_extra(model))
    (out / "command.txt").write_text(" ".join(cmd) + "\n")
    r = run(cmd, X.TIMEOUT.get(model, X.DEFAULT_TIMEOUT), out)
    log = out / X.LOG_NAME[model]
    text = log.read_text(errors="replace") if log.exists() else ""
    events = X.parse_eligible_lines(model, text + "\n" + r["stdout"])
    got = X.parse_checksum(r["stdout"])
    want = X.golden(model, ctx)
    inj = X.injection_count(text + "\n" + r["stdout"])
    n = len(events)
    ords = X.select_ordinals(n) if n else {}
    old = json.loads((OLDRES / "state" /
                      f"E2E-{model}-{ctx}-CTRL.json").read_text())
    st = {
        "task_id": tid, "kind": "control", "model": model, "context": ctx,
        "seed": seed, "outdir": str(out), "attempt": attempt,
        "exit_code": r["returncode"], "timed_out": r["timed_out"],
        "elapsed": r["elapsed"], "oracle_expected": want,
        "oracle_got": got, "oracle_pass": got == want,
        "injection_count": inj, "eligible_n": n, "eligible_ordinals": ords,
        "eligible_hash": X.census_hash(events) if events else None,
        "old_eligible_n": old.get("eligible_n"),
        "eligible_census_matches_old": old.get("eligible_n") == n,
        "binary_sha": sha(OBS), "config_sha": sha(
            ROOT / "configs/lsu_proxy_e2e.py"),
        "elf_sha": sha(X.workload(model, ctx)),
        "artifacts": X.artifact_record(out), "status": "PENDING",
    }
    if n:
        with open(out / "eligible_events.csv", "w", newline="") as fh:
            import csv
            w = csv.writer(fh)
            w.writerow(["ordinal", "raw"])
            for e in events:
                w.writerow([e["ordinal"], e["raw"]])
    if r["timed_out"]:
        st["status"] = "TIMEOUT"
    elif r["returncode"] != 0:
        st["status"] = "CONTROL_EXIT_NONZERO"
    elif inj != 0:
        st["status"] = "CONTROL_INJECTED"
    elif got != want:
        st["status"] = "CONTROL_ORACLE_FAIL"
    elif n < 3:
        st["status"] = "INSUFFICIENT_ELIGIBLE"
    elif len(set(ords.values())) != 3:
        st["status"] = "ORDINALS_NOT_DISTINCT"
    elif not st["eligible_census_matches_old"]:
        st["status"] = "CENSUS_CHANGED"
    else:
        st["status"] = "COMPLETED"
    return st


def do_fault(model, ctx, timing, seed, percent, attempt=1):
    tid = f"RP01OBS-{ctx}-{timing}-FAULT"
    ctrl = read_state(f"RP01OBS-{ctx}-CTRL")
    out = SLOT / "faults" / tid / f"attempt_{attempt}"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    if not ctrl or ctrl.get("status") != "COMPLETED":
        return {"task_id": tid, "status": "BLOCKED_NO_CONTROL",
                "outdir": str(out)}
    k = ctrl["eligible_ordinals"][timing]
    extra = X.fault_extra(model, seed, k) + [
        "--rp01_stall_trace", "rp01_stall.csv.gz",
        "--rp01_probe_cycles", "100000",
        "--rp01_probe_dense_cycles", "10000",
        "--rp01_probe_dense_count", "100",
    ]
    cmd = base_cmd(out, model, ctx, extra)
    (out / "command.txt").write_text(" ".join(cmd) + "\n")
    r = run(cmd, X.TIMEOUT.get(model, X.DEFAULT_TIMEOUT), out)
    log = out / X.LOG_NAME[model]
    text = log.read_text(errors="replace") if log.exists() else ""
    alltext = text + "\n" + r["stdout"] + "\n" + r["stderr"]
    inj = X.injection_count(alltext)
    obs = X.observed_ordinal(model, alltext)
    ev = X.census_event(ctrl, k)
    ident = X.identity_matches(model, alltext, ev)
    if obs is None and ident is True:
        obs = k
    got = X.parse_checksum(r["stdout"])
    want = X.golden(model, ctx)
    watchdog = bool(__import__("re").search(
        r"WATCHDOG_EXPIRED|WATCHDOG=EXPIRED|CHAOS_RP01_WATCHDOG", alltext))
    if r["timed_out"]:
        terminal, stt = "HANG", "COMPLETED_HANG"
    elif watchdog:
        terminal, stt = "HANG_WATCHDOG", "COMPLETED_HANG"
    elif r["returncode"] != 0:
        terminal, stt = "CRASH", "COMPLETED_CRASH"
    elif inj == 0:
        terminal, stt = "NO_INJECTION", "INJECTION_NOT_OBSERVED"
    elif got == want:
        terminal, stt = "NO_VISIBLE_MISMATCH", "COMPLETED"
    else:
        terminal, stt = "SDC", "COMPLETED_SDC"
    st = {
        "task_id": tid, "kind": "fault", "model": model, "context": ctx,
        "timing": timing, "seed": seed, "timing_percent": str(percent),
        "selected_ordinal": k, "observed_ordinal": obs,
        "ordinal_match": (obs == k) if obs is not None else None,
        "identity_match": ident, "census_event": ev, "attempt": attempt,
        "outdir": str(out), "exit_code": r["returncode"],
        "timed_out": r["timed_out"], "elapsed": r["elapsed"],
        "oracle_expected": want, "oracle_got": got,
        "oracle_pass": got == want, "injection_count": inj,
        "watchdog": watchdog, "terminal": terminal, "status": stt,
        "binary_sha": sha(OBS),
        "elf_sha": sha(X.workload(model, ctx)),
        "config_sha": sha(ROOT / "configs/lsu_proxy_e2e.py"),
        "control_run_id": ctrl["task_id"],
        "control_hash": ctrl.get("eligible_hash"),
        "artifacts": {n: {"exists": (out / n).exists(),
                          "size": (out / n).stat().st_size
                          if (out / n).exists() else None,
                          "sha256": sha(out / n)
                          if (out / n).exists() else None}
                      for n in ("commit_trace.csv.gz", "micro_snap.csv.gz",
                                "prop_trace.csv.gz", "rp01_stall.csv.gz",
                                "stats.txt", "config.ini")},
    }
    if stt.startswith("COMPLETED") and obs is not None and obs != k:
        st["status"] = "ORDINAL_MISMATCH"
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=6)
    args = ap.parse_args()
    if not OBS.exists():
        raise SystemExit(f"observation binary missing: {OBS}")
    matrix = X.load_matrix()
    controls = [(c, matrix["seed"][("RP01", c)]) for c in X.CONTEXTS]
    tasks = []
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(do_control, "RP01", c, s): c for c, s in controls}
        for fut in as_completed(futs):
            st = fut.result()
            write_state(st["task_id"], st)
            print(st["status"], st["task_id"], st.get("eligible_n"),
                  "census_old", st.get("eligible_census_matches_old"),
                  flush=True)
    for c in X.CONTEXTS:
        for timing in ("T01", "T02", "T03"):
            tasks.append((c, timing, matrix["seed"][("RP01", c)],
                          X.TIMINGS[timing]))
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(do_fault, "RP01", c, t, s, p): (c, t)
                for c, t, s, p in tasks}
        for fut in as_completed(futs):
            st = fut.result()
            write_state(st["task_id"], st)
            print(st["status"], st["task_id"], st.get("terminal"),
                  st.get("observed_ordinal"), flush=True)
    print("state", status())


if __name__ == "__main__":
    main()
