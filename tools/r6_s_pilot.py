#!/usr/bin/env python3
"""R6-S seed1 pilot orchestrator.

Runs each RUNNABLE RunID's seed1 via tools/r6_s_run_one.sh with a hard
concurrency cap of 2 (=> at most 2 gem5 processes). Resumable: cells whose
output dir already has .done are skipped. Status is written atomically after
every completion. No bypass flags. No scons.
"""
import csv, fcntl, json, os, subprocess, sys, tempfile, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path("/home/sdc/gem5-fi-ding/.claude/worktrees/r6-s-unit-20261029")
MAIN = Path("/home/sdc/gem5-fi-ding")
RUNS = MAIN / "runs/lsu"
OUTROOT = RUNS / "r6_s_unit"
BATCH = OUTROOT / "_batch"
LAUNCHER = REPO / "tools/r6_s_run_one.sh"
PLAN = MAIN / "runs/lsu/RESULTS/STATUS/R6-S-UNIT-PLAN.tsv"
SEED = sys.argv[1] if len(sys.argv) > 1 else "1"
MAXP = 2

def atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(dir=str(path.parent))
    with os.fdopen(fd, "w") as f:
        f.write(text)
    os.replace(tmp, path)

def load_cells():
    override = os.environ.get("PILOT_CELLS", "").strip()
    if override:
        return [x.strip() for x in override.split(",") if x.strip()]
    rows = list(csv.DictReader(open(PLAN), delimiter="\t"))
    return [r["run_id"] for r in rows
            if r["final_status"] in ("RUNNABLE_SEED1_PENDING", "RUNNABLE",
                                     "SEED1_PASS", "SEED1_FAIL")]

def write_status(results):
    lines = ["run_id\tseed\tstatus\texit_code\tout_dir\tmanifest\tlog"]
    for r in sorted(results, key=lambda x: x["run_id"]):
        lines.append("\t".join(str(r.get(k, "")) for k in
                     ("run_id","seed","status","exit_code","out_dir","manifest","log")))
    atomic_write(BATCH / f"seed{SEED}_status.tsv", "\n".join(lines) + "\n")

def run_cell(rid):
    out = OUTROOT / f"{rid}_s{SEED}"
    manifest = out / "manifest.json"
    log = OUTROOT / f"{rid}_s{SEED}.log"
    # resume: already finished
    if (out / ".done").exists():
        return {"run_id": rid, "seed": SEED, "status": "ALREADY_DONE",
                "exit_code": (out / ".exit_code").read_text().strip() if (out/".exit_code").exists() else "",
                "out_dir": str(out), "manifest": str(manifest), "log": str(log)}
    p = subprocess.run(["bash", str(LAUNCHER), rid, SEED],
                       capture_output=True, text=True)
    code = ""
    if (out / ".exit_code").exists():
        code = (out / ".exit_code").read_text().strip()
    st = "FINISHED" if (out / ".done").exists() else "LAUNCH_REFUSED"
    if p.returncode not in (0, None) and st == "FINISHED":
        st = "FINISHED_NONZERO"
    return {"run_id": rid, "seed": SEED, "status": st, "exit_code": code,
            "out_dir": str(out), "manifest": str(manifest), "log": str(log),
            "launcher_rc": p.returncode,
            "launcher_tail": (p.stdout + p.stderr)[-300:]}

def main():
    BATCH.mkdir(parents=True, exist_ok=True)
    # single orchestrator guard
    g = open(BATCH / f".orchestrator_seed{SEED}.lock", "w")
    try:
        fcntl.flock(g, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit("REFUSED: another orchestrator holds the seed lock")
    cells = load_cells()
    results = []
    write_status(results)
    print(f"[pilot] seed={SEED} cells={len(cells)} max_parallel={MAXP}", flush=True)
    with ThreadPoolExecutor(max_workers=MAXP) as pool:
        futs = {pool.submit(run_cell, rid): rid for rid in cells}
        for fut in as_completed(futs):
            r = fut.result()
            results.append(r)
            write_status(results)
            print(f"[pilot] {r['run_id']} {r['status']} rc={r.get('launcher_rc')} "
                  f"exit={r['exit_code']}", flush=True)
    write_status(results)
    done = sum(1 for r in results if r["status"] in ("FINISHED","ALREADY_DONE"))
    print(f"[pilot] COMPLETE seed={SEED} launched={len(results)} finished={done}", flush=True)

if __name__ == "__main__":
    main()
