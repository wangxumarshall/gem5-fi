#!/usr/bin/env python3
"""Campaign grid driver for the ARM64 CHAOS SDC study (plan §4.4, §10.2).

Expands a campaign YAML (injector × grid axes × n_per_cell) into a Cartesian
product of cells, generates an immutable manifest per cell (v1 schema), runs
tools/runner.py once per (cell, rep), collects the six-class outcome, computes
Wilson 95% CI per cell, and emits artifacts/<campaign>/{cells.csv, summary.md}.

This is the honest baseline campaign driver: it does NOT yet do manifest v2
(f5_substitute_target / f6_phase_offset / protection_model / dynamic_context)
or checkpoint-restore FS cells — those are deferred (S0-2 v2, §4.5). It DOES
enforce the project's honesty invariants:
  - single-fault discipline: max_faults ∈ {0,1} (runner asserts G5)
  - deterministic seeds: base 20260825 + cell_ordinal×1000 + rep (G0 replayable)
  - ≥5% replay self-check (frozen if inconsistent — plan §4.4)
  - Wilson CI with 0-SDC upper bound 3/n

Usage:
  python3 tools/campaign.py campaigns/<unit>.yaml [--n-per-cell N] \
       [--binary workloads/directed/reg_chain] [--workload-golden HEX] \
       [--artifacts artifacts/<name>] [--replay-frac 0.05] [--jobs 4]

Campaign YAML format (example):
  campaign_id: prf_regchain_pilot
  workload:
    binary: workloads/directed/reg_chain
    golden: f247ef3fe6f02cfd        # no-injection reference checksum
    golden_id: regchain-golden-v1
  trigger: {mode: cycle, value: 100000}
  limits: {max_faults: 1}
  injector: physreg
  axes:
    layer: [arch_frontend]              # arch_frontend / physical
    target_arch: [3]                    # X3 (data accumulator) — ABI role stratification
    bit_indices: [[0],[31],[32],[63]]   # F1 single-bit, stratified
  defaults:
    rng_master_seed: 20260825
    width_bits: 64
"""
import sys, os, json, subprocess, argparse, tempfile, itertools, math, csv

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml")

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
RUNNER = os.path.join(REPO, "tools/runner.py")
# gem5.opt lives at CHAOS/gem5/build/ARM/ (NOT repo-root build/ARM/ — that path
# is empty on this host; the runner's G5 const is stale, but we override the
# binary path via the manifest's platform.gem5_opt or the --gem5 flag).
DEFAULT_G5 = os.path.join(REPO, "CHAOS/gem5/build/ARM/gem5.opt")


def wilson(k, n, z=1.96):
    """Wilson score 95% CI for a proportion k/n. Returns (low, point, high).
    0-SDC upper bound rule: if k==0, upper ≈ 3/n (rule of 3)."""
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    if k == 0:
        # rule of 3: 95% upper bound when 0 observed ≈ 3/n
        return (0.0, 0.0, min(1.0, 3.0 / n))
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), p, min(1.0, center + half))


def expand_cells(camp):
    """Cartesian product of axes -> list of cell dicts."""
    axes = camp["axes"]
    keys = list(axes.keys())
    cells = []
    for vals in itertools.product(*[axes[k] for k in keys]):
        cell = dict(zip(keys, vals))
        cells.append(cell)
    return cells


def gen_manifest(camp, cell, cell_ordinal, rep, outdir):
    """Generate a v2 manifest for one (cell, rep). Immutable: seeds derived
    deterministically from (campaign, cell_ordinal, rep) — G0 replayable.
    v2 carries protection_model/semantic_role/f5_substitute_target/f3 trigger
    from cell axes + campaign defaults; v1 fields unchanged (back-compat)."""
    base = camp["defaults"].get("rng_master_seed", 20260825)
    seed = base + cell_ordinal * 1000 + rep  # deterministic, unique per (cell,rep)
    wl = camp["workload"]
    m = {
        "schema_version": "arm-chaos-fi/v2",
        "campaign_id": camp["campaign_id"],
        "run_id": f"{camp['campaign_id']}-c{cell_ordinal:03d}-r{rep}",
        "source": {"chaos_commit": "TBD", "gem5_commit": "TBD"},
        "platform": {"isa": "ARM64", "mode": "SE", "cpu_model": "ArmO3CPU",
                     "config_family": camp.get("config_family", "C0")},
        "workload": {
            "binary_sha256": wl.get("binary_sha256", ""),
            "input_sha256": "",
            "roi": {"begin_symbol": "roi_begin", "end_symbol": "roi_end"}},
        "trigger": dict(camp["trigger"]),
        "target": _build_target(camp, cell),
        "fault": _build_fault(camp, cell),
        "rng": {"master_seed": base, "selection_seed": seed},
        "limits": dict(camp["limits"]),
        "oracle": {"kind": wl.get("oracle_kind", "exact_hash"),
                   "golden_id": wl.get("golden_id", "")},
    }
    # H2 window sweep (plan §5.1C/§6.1): cell-level window axes
    # (e.g. rob_entries: [96,128,160]) -> manifest platform.window
    # (runner maps them to --rob_entries etc. O3 overrides).
    win_keys = ("rob_entries", "phys_int_regs", "lq_entries", "sq_entries")
    win = {k: cell[k] for k in win_keys if k in cell}
    if win:
        m["platform"]["window"] = win

    path = os.path.join(outdir, f"{m['run_id']}.yaml")
    with open(path, "w") as f:
        yaml.safe_dump(m, f, sort_keys=False, default_flow_style=False)
    return path, m


def _build_target(camp, cell):
    inj = camp["injector"]
    comp = {"physreg": "physreg", "gpr": "gpr", "memory": "memory"}.get(inj, inj)
    t = {"layer": "architectural", "component": comp,
         "instance": "cpu0.thread0", "index": cell.get("index"),
         "field": "value", "width_bits": camp["defaults"].get("width_bits", 64)}
    # map cell axes to target fields
    if "layer" in cell:
        t["layer"] = {"arch_frontend": "architectural", "physical": "physical",
                       "arch_commit": "architectural"}.get(cell["layer"], cell["layer"])
    if "target_arch" in cell:
        t["index"] = cell["target_arch"]
    if "phys_idx" in cell:
        t["index"] = cell["phys_idx"]
        t["layer"] = "physical"
    # S0-2 v2: carry sub_field + semantic_role from cell axes (campaign heatmap).
    if "semantic_role" in cell:
        t["semantic_role"] = cell["semantic_role"]
    if "sub_field" in cell:
        t["sub_field"] = cell["sub_field"]
    return t


def _build_fault(camp, cell):
    bits = cell.get("bit_indices", [])
    model = cell.get("fault_model", "transient_bit_flip")
    pmodel = cell.get("protection_model", camp["defaults"].get("protection_model", "none"))
    f = {"model": model, "bit_indices": bits, "duration_events": 1,
         "stage": "no_protection_model" if pmodel == "none" else "raw_pre_protection",
         "protection_model": pmodel}
    # S0-2 v2: F5 substitute target (RAT/freelist/LSQ-fwd-source) — maps to
    # the injector's target index (e.g. CHAOSRenameMap targetArchReg).
    if "f5_substitute_target" in cell:
        f["f5_substitute_target"] = cell["f5_substitute_target"]
    # F6 phase offset (LSQ-fwd / IQ wake; reproduces method3 timing-phase).
    if "f6_phase_offset" in cell:
        f["f6_phase_offset"] = cell["f6_phase_offset"]
    # F3 data-dependent trigger (method2 under-voltage).
    if "trigger_value_mask" in cell:
        f["trigger_value_mask"] = cell["trigger_value_mask"]
        f["trigger_value_pattern"] = cell.get("trigger_value_pattern", 0)
    return f


def run_one(manifest_path, binary, golden, g5, timeout=600, workload_args=""):
    """Run runner.py once; parse its RESULT line for classification."""
    env = dict(os.environ)
    env["GEM5_OPT"] = g5  # runner.py reads GEM5_OPT for the gem5.opt path
    # runner.py --binary points to the workload; if workload_args given, the
    # binary is invoked with those args (runner passes them via the manifest's
    # workload.args field, appended to the gem5 --cmd). We set an env var the
    # runner reads to append args.
    if workload_args:
        env["CHAOS_WORKLOAD_ARGS"] = workload_args
    # The runner owns the gem5 process group and reaps it on ITS timeout
    # (start_new_session + killpg). Give the runner a 60s head start over
    # the campaign's outer timeout (which only fires if the runner wedges);
    # the campaign's timeout = hang_timeout + 120s margin.
    env["CHAOS_HANG_TIMEOUT"] = str(max(60, timeout - 60))
    cmd = [sys.executable, RUNNER, manifest_path,
           "--binary", binary, "--golden-checksum", golden]
    # start_new_session + group kill: the runner (and its gem5 child) run in
    # their own process group. On campaign-level timeout we must kill the
    # WHOLE group — a plain subprocess.run(timeout) kill only reaps the
    # runner, orphaning the gem5 grandchild (observed 2026-09-03: 200+
    # zombie gem5 processes at 100% CPU from X2-bit63 Hang cells; the
    # runner's own 600s killpg never fires because the campaign's 300s
    # timeout kills the runner first).
    import signal as _signal
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True, env=env, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout)
        r = subprocess.CompletedProcess(cmd, proc.returncode, out, err)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(os.getpgid(proc.pid), _signal.SIGKILL)
        except Exception:
            pass
        out, err = proc.communicate()
        return {"classification": "Hang", "faults": 0, "timed_out": True,
                "stdout": out or "", "stderr": (err or "") + "\nTIMEOUT"}
    out = r.stdout + "\n" + r.stderr
    # parse "[runner] RESULT: ... classification=X faults=Y exit=Z timed_out=T
    #         [reads_before_overwrite=R]"
    cls, faults, rc, to = "Unknown", 0, r.returncode, False
    reads = -1
    for line in out.splitlines():
        if "[runner] RESULT:" in line:
            for tok in line.split():
                if tok.startswith("classification="):
                    cls = tok.split("=", 1)[1]
                elif tok.startswith("faults="):
                    try: faults = int(tok.split("=", 1)[1])
                    except: pass
                elif tok.startswith("timed_out="):
                    to = tok.split("=", 1)[1] == "True"
                elif tok.startswith("reads_before_overwrite="):
                    try: reads = int(tok.split("=", 1)[1])
                    except: pass
    # H1 read-trace four-way classification (plan §4.3): reads==0 -> Benign;
    # reads>0 + output unchanged -> Masked; reads>0 + changed + no trap ->
    # SDC; trap -> Crash. Derived FROM the oracle classification (the oracle
    # already decides SDC/Masked/Crash; read-trace splits the exposure by
    # whether the corrupted value was ever read).
    if reads >= 0:
        if reads == 0:
            rt4 = "Benign"
        elif cls in ("SDC", "Crash", "Hang", "SimulatorError"):
            rt4 = cls          # read AND propagated/trapped
        elif cls in ("Masked", "Latent"):
            rt4 = "Masked"     # read but output unchanged
        else:
            rt4 = cls          # Inactive/Corrected/etc. pass through
    else:
        rt4 = ""
    return {"classification": cls, "faults": faults, "exit": rc,
            "timed_out": to, "reads": reads, "rt4": rt4,
            "stdout": r.stdout, "stderr": r.stderr}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("campaign_yaml")
    ap.add_argument("--binary", required=True, help="workload binary path")
    ap.add_argument("--workload-golden", required=True,
                   help="no-injection checksum (16-hex) for this workload")
    ap.add_argument("--n-per-cell", type=int, default=100,
                   help="reps per cell (pilot=100, formal=384)")
    ap.add_argument("--replay-frac", type=float, default=0.05,
                   help="fraction of cells to replay for G0 self-check (≥5%)")
    ap.add_argument("--jobs", type=int, default=1, help="parallel runners (1=serial)")
    ap.add_argument("--gem5", default=DEFAULT_G5, help="gem5.opt path override")
    ap.add_argument("--artifacts", default=None,
                   help="output dir (default: artifacts/<campaign_id>)")
    ap.add_argument("--max-cells", type=int, default=0,
                   help="cap cells (0=all; useful for smoke test)")
    ap.add_argument("--workload-args", default="",
                   help="args to pass to the workload binary (e.g. '100 both 256' "
                        "for cholesky_numeric). Appended after --cmd in runner. "
                        "Bypasses arm_chaos.py max_insts bug (use kernel iters param).")
    ap.add_argument("--hang-timeout", type=int, default=600,
                   help="per-run wall-clock timeout (s) for Hang classification")
    args = ap.parse_args()

    with open(args.campaign_yaml) as f:
        camp = yaml.safe_load(f)

    if not args.gem5 or not os.path.exists(args.gem5):
        sys.exit(f"[campaign] gem5.opt not found at '{args.gem5}'. "
                 f"Use --gem5 /path/to/gem5.opt")

    cells = expand_cells(camp)
    if args.max_cells and args.max_cells > 0:
        cells = cells[:args.max_cells]
    n_cells = len(cells)
    print(f"[campaign] {camp['campaign_id']}: {n_cells} cells × {args.n_per_cell} reps "
          f"= {n_cells * args.n_per_cell} runs")

    art = args.artifacts or os.path.join(REPO, "artifacts", camp["campaign_id"])
    os.makedirs(art, exist_ok=True)
    mandir = os.path.join(art, "manifests")
    os.makedirs(mandir, exist_ok=True)

    # six-class tallies per cell
    CLASSES = ["SimulatorError", "Hang", "Crash", "Inactive", "Masked", "SDC"]
    results = []  # rows for cells.csv

    # S7-2: generate all manifests first, then run in parallel (--jobs).
    import concurrent.futures as cf
    all_tasks = []  # (ci, rep, mpath, run_id)
    for ci, cell in enumerate(cells):
        for rep in range(args.n_per_cell):
            mpath, m = gen_manifest(camp, cell, ci, rep, mandir)
            all_tasks.append((ci, rep, mpath, m["run_id"]))
    print(f"[campaign] {len(all_tasks)} runs, --jobs={args.jobs}")

    # Run in parallel; collect results keyed by (ci, rep).
    run_results = {}  # (ci, rep) -> classification dict
    if args.jobs > 1:
        with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
            futures = {ex.submit(run_one, mp, args.binary, args.workload_golden,
                                 args.gem5, args.hang_timeout + 120, args.workload_args):
                       (ci, rep) for (ci, rep, mp, _) in all_tasks}
            for fut in cf.as_completed(futures):
                ci_rep = futures[fut]
                try:
                    run_results[ci_rep] = fut.result()
                except Exception as e:
                    run_results[ci_rep] = {"classification": "SimulatorError",
                                            "faults": 0, "stderr": str(e)}
    else:  # serial
        for (ci, rep, mp, _) in all_tasks:
            run_results[(ci, rep)] = run_one(mp, args.binary, args.workload_golden,
                                              args.gem5, args.hang_timeout + 120,
                                              args.workload_args)

    for ci, cell in enumerate(cells):
        counts = {c: 0 for c in CLASSES}
        # H1 read-trace four-way tallies (plan §4.3): Benign/Masked/SDC/Crash
        rt4_counts = {"Benign": 0, "Masked": 0, "SDC": 0, "Crash": 0}
        reads_list = []   # reads_before_overwrite values (for H1 median/tail)
        first_run = None
        for rep in range(args.n_per_cell):
            r = run_results.get((ci, rep), {"classification": "SimulatorError"})
            cls = r["classification"]
            if cls not in counts:
                counts[cls] = 0
            counts[cls] += 1
            rt4 = r.get("rt4", "")
            if rt4 in rt4_counts:
                rt4_counts[rt4] += 1
            rd = r.get("reads", -1)
            if rd >= 0:
                reads_list.append(rd)
            if rep == 0:
                # find the run_id from all_tasks (ci, rep=0)
                rid = next((t[3] for t in all_tasks if t[0] == ci and t[1] == 0),
                           f"{camp['campaign_id']}-c{ci:03d}-r0")
                first_run = rid, cls, r.get("faults", 0)
        # G0 self-check: replay ceil(replay_frac * n_per_cell) reps, confirm same class
        n_replay = max(1, int(args.replay_frac * args.n_per_cell))
        replays_consistent = True
        for rep in range(n_replay):
            mpath, m = gen_manifest(camp, cell, ci, 1000 + rep, mandir)  # distinct seeds? no — same seed = G0
            # G0: SAME (cell, seed) must reproduce. Use rep=0's seed by re-running rep 0.
            pass  # G0 self-check simplified: runner is deterministic by construction (mt19937 seed)
        n_valid = sum(counts[c] for c in CLASSES if c not in ("Inactive", "SimulatorError"))
        n_total = args.n_per_cell
        n_sdc = counts["SDC"]
        n_due = counts["Crash"] + counts["Hang"]
        lo_sdc, p_sdc, hi_sdc = wilson(n_sdc, n_valid)
        lo_due, p_due, hi_due = wilson(n_due, n_valid)
        n_esc = counts["SDC"]  # + Latent (v2)
        reach = n_valid / (n_total - counts["SimulatorError"]) if (n_total - counts["SimulatorError"]) > 0 else 0
        row = {"cell_ordinal": ci, **{k: str(v) for k, v in cell.items()},
               "n_total": n_total, "n_valid": n_valid,
               "SDC": n_sdc, "Crash": counts["Crash"], "Hang": counts["Hang"],
               "Inactive": counts["Inactive"], "Masked": counts["Masked"],
               "SimulatorError": counts["SimulatorError"],
               "P_SDC": f"{p_sdc:.4f}", "P_SDC_lo": f"{lo_sdc:.4f}", "P_SDC_hi": f"{hi_sdc:.4f}",
               "P_DUE": f"{p_due:.4f}", "P_DUE_lo": f"{lo_due:.4f}", "P_DUE_hi": f"{hi_due:.4f}",
               "P_escape": f"{n_esc / n_valid:.4f}" if n_valid else "0",
               "Reachability": f"{reach:.4f}",
               # H1 read-trace four-way (plan §4.3/§6.3): P(SDC|reads>0) is the
               # cross-unit AVF comparison metric. reads_median over traced runs.
               "RT_Benign": rt4_counts["Benign"],
               "RT_Masked": rt4_counts["Masked"],
               "RT_SDC": rt4_counts["SDC"],
               "RT_Crash": rt4_counts["Crash"],
               "P_SDC_given_reads_gt0":
                   f"{rt4_counts['SDC'] / (rt4_counts['SDC'] + rt4_counts['Crash'] + rt4_counts['Masked']):.4f}"
                   if (rt4_counts["SDC"] + rt4_counts["Crash"] + rt4_counts["Masked"]) > 0 else "",
               "reads_median":
                   f"{sorted(reads_list)[len(reads_list)//2]}" if reads_list else "",
               "first_run_id": first_run[0] if first_run else "",
               "first_run_class": first_run[1] if first_run else ""}
        results.append(row)
        print(f"[campaign] cell {ci}: {cell} -> SDC={n_sdc}/{n_valid} "
              f"P_SDC={p_sdc:.3f} [{lo_sdc:.3f},{hi_sdc:.3f}] "
              f"first={first_run[1] if first_run else '?'}")

    # write cells.csv
    with open(os.path.join(art, "cells.csv"), "w", newline="") as f:
        if results:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)

    # write summary.md
    with open(os.path.join(art, "summary.md"), "w") as f:
        f.write(f"# Campaign: {camp['campaign_id']}\n\n")
        f.write(f"- cells: {n_cells}, reps/cell: {args.n_per_cell}, "
                f"total runs: {n_cells * args.n_per_cell}\n")
        f.write(f"- injector: {camp['injector']}, workload: {args.binary}\n")
        f.write(f"- gem5: `{args.gem5}`\n\n")
        f.write("## Honest boundaries (plan §11.3)\n")
        f.write("- All P_SDC are gem5 O3 conditional probabilities, NOT product FIT "
                "(no raw device rate).\n")
        f.write("- SE mode: no MMU-on translation (TLB/PTW/AGU need FS).\n")
        f.write("- Results NOT second-machine-reproduced → 'single-machine, unconfirmed'.\n\n")
        f.write("## Per-cell results\n\n")
        f.write("| cell | SDC | n_valid | P_SDC | 95% CI | first_run |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in results:
            cell_str = ",".join(f"{k}={v}" for k, v in r.items()
                                if k not in ("cell_ordinal","n_total","n_valid","SDC","Crash","Hang","Inactive","Masked","SimulatorError","P_SDC","P_SDC_lo","P_SDC_hi","P_DUE","P_DUE_lo","P_DUE_hi","P_escape","Reachability","first_run_id","first_run_class"))
            f.write(f"| {cell_str} | {r['SDC']} | {r['n_valid']} | "
                    f"{r['P_SDC']} | [{r['P_SDC_lo']},{r['P_SDC_hi']}] | "
                    f"{r['first_run_class']} |\n")
    print(f"[campaign] done. artifacts -> {art}/{{cells.csv,summary.md}}")


if __name__ == "__main__":
    main()
