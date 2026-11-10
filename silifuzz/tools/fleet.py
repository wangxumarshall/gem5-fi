#!/usr/bin/env python3
"""Fleet scheduler: 4-core / 2-minute checker windows rotated over all cores.

Paper section 2.5.2: in production, a job scheduler reserves 4 cores (two
hyperthreaded pairs) for up to 2 minutes, and the window eventually covers all
cores of the machine.  This host has no SMT, so a window is 4 physical cores.

Results are stored in SQLite so that quarantine/feedback tooling (section 2.6)
can analyze them.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def parse_cores(spec: str) -> list[int]:
    out: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def init_db(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    db = sqlite3.connect(path)
    db.execute(
        """CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY,
            machine TEXT, started REAL, ended REAL, cores TEXT, corpus TEXT,
            mode TEXT, seconds INTEGER, executions INTEGER, mismatches INTEGER,
            timeouts INTEGER, errors INTEGER, exec_per_s REAL, run_dir TEXT,
            summary TEXT)"""
    )
    db.execute(
        """CREATE TABLE IF NOT EXISTS quarantine (
            snapshot TEXT, core INTEGER, hits INTEGER, last_seen REAL,
            confirmed INTEGER, details TEXT,
            PRIMARY KEY (snapshot, core))"""
    )
    db.commit()
    return db


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--db", default="work/fleet/results.db")
    ap.add_argument("--out-root", default="work/fleet/runs")
    ap.add_argument("--cores", default=None, help="default: all online CPUs")
    ap.add_argument("--window-cores", type=int, default=4)
    ap.add_argument("--window-seconds", type=int, default=120)
    ap.add_argument("--windows", type=int, default=0, help="0 = one full pass")
    ap.add_argument("--mode", default="sampled")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--inject", default="")
    ap.add_argument("--found", default="")
    ap.add_argument("--checker", default=os.path.join(ROOT, "bin", "sf_checker"))
    args = ap.parse_args()

    if args.cores:
        cores = parse_cores(args.cores)
    else:
        cores = sorted(os.sched_getaffinity(0))
    windows = [cores[i:i + args.window_cores]
               for i in range(0, len(cores), args.window_cores)]
    if args.windows:
        windows = windows[: args.windows]

    db = init_db(args.db)
    machine = socket.gethostname()
    os.makedirs(args.out_root, exist_ok=True)
    total_exec = 0
    total_mis = 0
    for idx, group in enumerate(windows):
        run_dir = os.path.join(args.out_root, f"window-{idx:03d}-{group[0]}-{group[-1]}")
        os.makedirs(run_dir, exist_ok=True)
        cmd = [args.checker, "--corpus", args.corpus,
               "--cores", ",".join(map(str, group)),
               "--seconds", str(args.window_seconds),
               "--mode", args.mode, "--seed", str(args.seed),
               "--out", run_dir]
        if args.inject:
            cmd += ["--inject", args.inject]
        if args.found:
            cmd += ["--found", args.found]
        started = time.time()
        print(f"window {idx + 1}/{len(windows)} cores={group} "
              f"seconds={args.window_seconds}", flush=True)
        proc = subprocess.run(cmd, capture_output=True, text=True)
        ended = time.time()
        lines = [l for l in proc.stdout.strip().splitlines() if l.startswith("{")]
        if not lines:
            print(proc.stdout + proc.stderr, file=sys.stderr)
            print(f"window failed (rc={proc.returncode})", file=sys.stderr)
            continue
        summary = json.loads(lines[-1])
        db.execute(
            """INSERT INTO runs(machine, started, ended, cores, corpus, mode,
                                seconds, executions, mismatches, timeouts, errors,
                                exec_per_s, run_dir, summary)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (machine, started, ended, ",".join(map(str, group)), args.corpus,
             args.mode, args.window_seconds, summary.get("executions", 0),
             summary.get("mismatches", 0), summary.get("timeouts", 0),
             summary.get("errors", 0), summary.get("exec_per_s", 0.0),
             run_dir, json.dumps(summary)),
        )
        db.commit()
        total_exec += summary.get("executions", 0)
        total_mis += summary.get("mismatches", 0)
        print(f"  executions={summary.get('executions')} "
              f"rate={summary.get('exec_per_s')}/s mismatches={summary.get('mismatches')}")
    print(json.dumps({"windows": len(windows), "executions": total_exec,
                      "mismatches": total_mis, "db": args.db}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
