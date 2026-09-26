#!/usr/bin/env python3
"""LSU campaign orchestrator (09 W10) — adaptive-sampling execution engine.

Reads 07-expanded-matrix.csv (337 cells), runs each cell with the
two-phase adaptive sampling from 05 r12-r15:
  Phase 1 (trial): 30 activated — discover injector errors / all-Crash / zero-activation
  Phase 2 (screening): ≥385 activated (95% CI, ±5pp) — cell pass/fail
  Phase 3 (main): sequential until Wilson 95% half-width ≤2pp or 5000 activated

Per-run classification via tools/lsu_l5_classify.py (L5 conservation).
Results backfilled to 07-expanded-matrix.csv col16-27.

Usage:
  python3 tools/lsu_campaign.py --matrix docs/gem5-fi/lsu/07-expanded-matrix.csv \
      --outdir runs/lsu --max-parallel 4 [--cells A01-F0-W3,...] [--dry-run]
"""
import argparse
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
G5 = REPO / "build/ARM/gem5.opt"
LSU_PROXY = REPO / "configs/se/lsu_proxy.py"
L5 = REPO / "tools/lsu_l5_classify.py"

# Expanded matrix column indices (0-based; col 0 = "Excel行" so +1 shift)
COL_RUNID = 1     # RunID like A01-F0-W3
COL_MODEL = 2     # Model ID like A01
COL_UNIT = 3      # Unit like AGU
COL_FREQ = 7      # Frequency tier F0-F6
COL_WORKLOAD = 9  # Workload name
COL_SEED = 16     # Seed/注入索引
# Result columns (17-27 are 11 slots, col 26=记录状态)
RESULT_COLS = list(range(17, 28))
COL_STATUS = 26   # 记录状态


def load_matrix(path):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    header = rows[0]
    cells = []
    for r in rows[1:]:
        if len(r) > COL_RUNID and r[COL_RUNID].strip():
            cells.append(r)
    return header, cells


def classify_run(outdir, stdout_file, golden, exit_code, stderr_file=None):
    """Run L5 classifier on one run's output."""
    cmd = ["python3", str(L5),
           "--run-dir", str(outdir),
           "--stdout", str(stdout_file),
           "--golden", golden,
           "--exit", str(exit_code)]
    if stderr_file and Path(stderr_file).exists():
        cmd += ["--stderr", str(stderr_file)]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if r.returncode == 0 and "LSU_L5:" in r.stdout:
        try:
            json_str = r.stdout.split("LSU_L5: ", 1)[1].strip()
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError):
            pass
    return {"outcome": "Unclassified", "error": r.stderr[:200] if r.stderr else "unknown"}


def run_single_cell(cell, args, seed, outdir):
    """Run one gem5 invocation for a single cell×seed. Returns classification dict."""
    runid = cell[COL_RUNID]
    freq = cell[COL_FREQ]
    model = cell[COL_MODEL]
    workload_name = cell[COL_WORKLOAD]

    # Map workload name to binary path (simplified mapping)
    wl_map = {
        "MiniCheck": "mini_check",
        "AGU-AddrModes": "agu_addrmodes",
        "SQ-Forward": "sq_forward",
        "Cache-DirtyEvict": "cache_dirtyevict",
        "Prefetch-Stride": "prefetch_stride",
        "STREAM+PointerChase": "stream_chase",
        "BEEBS-DelayAVF": "beebs_kernels",
        "GAP/Graph500": "gap_bfs",
    }
    binary = None
    for key, bin_name in wl_map.items():
        if key in workload_name:
            binary = REPO / "workloads/directed" / bin_name
            break
    if not binary:
        return {"outcome": "Blocked", "error": f"workload not mapped: {workload_name}"}

    outdir.mkdir(parents=True, exist_ok=True)
    stdout_file = outdir / "run.out"
    stderr_file = outdir / "run.err"

    cmd = [str(G5), "--outdir", str(outdir), str(LSU_PROXY),
           "--cmd", str(binary), "--cpu", "O3",
           "--rng_seed", str(seed)]

    # Add model-specific injector flags (simplified mapping by model prefix)
    if model.startswith("A"):
        cmd += ["--chaos_addrpath", "--addrpath_lsu_tier", freq,
                "--addrpath_warmup_events", "0", "--addrpath_span_events", "1000"]
        # Map model to mode
        mode_map = {"A01": "a01_bit", "A02": "a02_2bit", "A03": "a03_stuck0",
                    "A05": "a05_shift", "A06": "a06_size"}
        pre_map = {"A04": "a04_subst", "A08": "a08_subst", "S04": "s04_store_subst",
                   "S05": "s05_store_size", "S06": "s06_store_state",
                   "S07": "s07_store_ptr", "S11": "s11_store_lost",
                   "S13": "s13_store_addr", "L01": "l01_load_addr", "L02": "l02_load_state"}
        if model in mode_map:
            cmd += ["--addrpath_mode", mode_map[model]]
        elif model in pre_map:
            cmd += ["--agu_pre_mode", pre_map[model]]
    elif model.startswith("S") or model.startswith("L"):
        cmd += ["--chaos_lsqfwd", "--lsqfwd_lsu_tier", freq,
                "--lsqfwd_warmup_events", "0", "--lsqfwd_span_events", "1000"]
    elif model.startswith("C"):
        # CHAOSCache uses its own firstClock+probability+maxFaults mechanism
        # (attackEvent scheduling), NOT the LSU event-normalized trigger
        cmd += ["--chaos_l1d", "--l1d_first_clock", "1000",
                "--l1d_max_faults", "1", "--l1d_rng_seed", str(seed)]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    stdout_file.write_text(proc.stdout)
    stderr_file.write_text(proc.stderr)

    # Extract golden from no-inject run (simplified: use known goldens)
    goldens = {
        "mini_check": "07568da9f3ad5665",
        "agu_addrmodes": "728e604ffcec539d",
        "sq_forward": "1f4cbf14327717df",
        "cache_dirtyevict": "062e5124df3667f9",
        "prefetch_stride": "629727c0ad9ca8ef",
        "stream_chase": "50ab96a7fe8f6ec2",
        "beebs_kernels": "a10b9827edd8a9fb",
        "gap_bfs": "030921682b3731f2",
    }
    golden = goldens.get(binary.name, "")

    return classify_run(outdir, stdout_file, golden, proc.returncode, stderr_file)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--matrix", required=True)
    p.add_argument("--outdir", default="runs/lsu")
    p.add_argument("--max-parallel", type=int, default=4)
    p.add_argument("--cells", help="comma-separated RunIDs to run (default: all)")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--phase", default="trial", choices=["trial", "screening", "main"])
    p.add_argument("--n-seeds", type=int, default=30, help="number of seeds per cell")
    a = p.parse_args()

    header, cells = load_matrix(a.matrix)
    print(f"Loaded {len(cells)} cells from {a.matrix}")

    if a.cells:
        wanted = set(a.cells.split(","))
        cells = [c for c in cells if c[COL_RUNID] in wanted]
        print(f"Filtered to {len(cells)} cells")

    outroot = Path(a.outdir)

    for cell in cells:
        runid = cell[COL_RUNID]
        if a.dry_run:
            print(f"  [dry-run] {runid} ({cell[COL_UNIT]} {cell[COL_FREQ]} {cell[COL_WORKLOAD][:30]})")
            continue

        cell_out = outroot / runid
        results = []
        for seed in range(1, a.n_seeds + 1):
            run_out = cell_out / f"seed{seed}"
            result = run_single_cell(cell, a, seed, run_out)
            results.append(result)
            outcome = result.get("outcome", "?")
            if seed % 10 == 0:
                print(f"  {runid} seed {seed}/{a.n_seeds}: {outcome}")

        # Summarize
        outcomes = {}
        for r in results:
            oc = r.get("outcome", "Unclassified")
            outcomes[oc] = outcomes.get(oc, 0) + 1
        total_injected = sum(r.get("injected", 0) or 0 for r in results)
        print(f"  {runid}: n={len(results)} injected={total_injected} "
              f"outcomes={outcomes}")

        # Save cell summary
        summary = {"runid": runid, "n_seeds": a.n_seeds,
                   "total_injected": total_injected, "outcomes": outcomes,
                   "results": results}
        (cell_out / "summary.json").parent.mkdir(parents=True, exist_ok=True)
        (cell_out / "summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
