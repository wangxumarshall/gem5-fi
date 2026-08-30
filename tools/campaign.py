#!/usr/bin/env python3
"""Grid campaign driver for the ARM64 CHAOS SDC fault-injection tool
(design doc `docs/KUNPENG920-故障注入方案详细工程设计.md` §1.5).

A campaign expands a Cartesian product of grid axes into immutable per-rep
single-fault manifests (max_faults=1), runs each rep via the EXISTING
`tools/runner.py` (subprocess), collects the 9-class outcome, and summarizes
per-cell Wilson 95% CI (§1.4) + a 5% replay-consistency check (§1.5).

THIS DRIVER REUSES runner.py — it does NOT reimplement the manifest->gem5
arg mapping, the classifier, or the G5 single-fault assertion. Each rep shells
out to `tools/runner.py <manifest.yaml> --binary <bin>` and parses the
`RESULT: classification=... faults_injected=... exit=...` stdout line. This is
the honest path: one classifier, one mapping, no drift.

It is injector-agnostic by construction: any injector already wired into
runner.py (gpr/physreg/memory/cache/lsqfwd) is campaignable today. Injectors
declared in the schema enum but not yet mapped (rat/rob/iq/...) cause runner.py
to reject with a clear error — the driver surfaces that as a SimulatorError
cell, never silently mis-runs.

Usage:
  python3 tools/campaign.py campaigns/example-prf-pilot.yaml [--jobs N] \\
      [--n_per_cell N] [--replay_pct P] [--dry] [--keep_manifests]

Outputs:
  runs/<campaign_id>/<cell_idx>/<run_id>.yaml   (immutable per-rep manifest)
  runs/<campaign_id>/<cell_idx>/results.jsonl  (one JSON per rep)
  artifacts/<campaign_id>/heatmap.csv          (per-cell point + CI)
  artifacts/<campaign_id>/summary.md           (human-readable + honesty notes)

NOTE (§0.4 honesty): this fault machine (cpu179) takes ~92s/run — formal n=384
campaigns belong on a healthy 2nd machine. This driver is machine-agnostic; the
results it produces on cpu179 are PILOT-only and must be replicated before any
formal claim (§3.1 S6).
"""
import sys, os, json, argparse, tempfile, subprocess, itertools, time

REPO = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from wilson import cell_stats, ALL_CLASSES  # noqa: E402

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml  (needed for campaign.yaml parsing)")

# jsonschema optional (runner.py already does light manifest validation; the
# campaign schema check here is best-effort and degrades to a manual review).
try:
    import jsonschema
    HAVE_SCHEMA = True
except ImportError:
    HAVE_SCHEMA = False

RUNNER = os.path.join(REPO, "tools", "runner.py")


# ---------------------------------------------------------------- grid expansion

def _expand_axis(val):
    """A grid axis value is either a scalar or a list-of-scalars. Normalize to
    a list of scalars so itertools.product can consume it."""
    if isinstance(val, list):
        return val
    return [val]


def expand_grid(grid):
    """Cartesian product of grid axes. Returns a list of dicts, one per cell:
    each dict maps axis-name -> chosen scalar value. Order is deterministic
    (Python dict preserves insertion order; itertools.product is ordered).

    An axis whose value list is EMPTY is treated as 'no stratification on this
    axis' (e.g. bit: [] means 'random mask, no specific bit') — it is dropped
    from the product rather than collapsing the product to zero cells. This
    mirrors runner.py's 'faultMask=0 -> randomly generated' convention.
    """
    if not grid:
        return [{}]
    # drop empty-list axes (random/unstratified), keep the rest
    keys = [k for k in grid if len(_expand_axis(grid[k])) > 0]
    value_lists = [_expand_axis(grid[k]) for k in keys]
    cells = []
    for combo in itertools.product(*value_lists):
        cells.append({k: v for k, v in zip(keys, combo)})
    return cells


def cell_id_str(cell_idx, cell):
    """Stable short string identifying a cell for logs, e.g. 'idx3_bit20'."""
    parts = [f"{k}={v}" for k, v in cell.items()]
    return " ".join(parts)


# ---------------------------------------------------------------- manifest write

def manifest_for_cell(campaign, cell, cell_ordinal, rep, outdir):
    """Build an arm-chaos-fi/v1 manifest (reuses the EXISTING v1 schema that
    runner.py validates) for one (cell, rep), write it to outdir, return path.

    Seed rule (§1.5): base_seed + cell_ordinal*1000 + rep -> deterministic,
    reproducible across machines.
    """
    wl = campaign["workload"]
    inj = campaign["injector"]
    limits = campaign.get("limits", {})
    base = campaign["base_seed"]
    seed = base + cell_ordinal * 1000 + rep
    run_id = f"{campaign['campaign_id']}-c{cell_ordinal:04d}-r{rep:04d}"

    # target component <-> injector (schema enum is wider than what runner.py
    # maps today; runner.py will reject unmapped ones with a clear error).
    comp_map = {
        "gpr": "gpr", "physreg": "physreg", "memory": "memory",
        "cache": "l1d", "lsqfwd": "physreg",  # cache->l1d; lsqfwd uses physreg
        # forward-declared; runner.py rejects until mapping lands:
        "rat": "rat", "freelist": "rat", "rob": "rat", "iq": "rat",
    }
    comp = comp_map.get(inj, inj)
    layer = "physical" if (inj == "physreg" and cell.get("phys_mode") == "phys") else "architectural"

    manifest = {
        "schema_version": "arm-chaos-fi/v1",
        "campaign_id": campaign["campaign_id"],
        "run_id": run_id,
        "source": {
            "chaos_commit": campaign.get("chaos_commit", "HEAD"),
            "gem5_commit": "62c7bf284864b83f7308f5e14ca9c80812621c29",
            "patchset_sha256": "TBD",
        },
        "platform": {
            "isa": "ARM64",
            "mode": campaign.get("mode", "SE"),
            "cpu_model": campaign.get("cpu_model", "ArmO3CPU"),
            "config_family": campaign.get("config", "C0"),
        },
        "workload": {
            "binary_sha256": wl.get("binary_sha256", ""),
            "input_sha256": "",
            "roi": wl.get("roi", {}),
        },
        "trigger": {
            "mode": wl.get("trigger_mode", "cycle"),
            "value": wl.get("trigger_value", 100000),
        },
        "target": {
            "layer": layer,
            "component": comp,
            "instance": "cpu0.thread0",
            "index": cell.get("target_index") if cell.get("target_index") is not None else None,
            "field": cell.get("field", "value"),
            "width_bits": cell.get("width_bits", 64),
        },
        "fault": {
            "model": cell.get("fault_model", "transient_bit_flip"),
            "bit_indices": [cell["bit"]] if "bit" in cell else [],
            "duration_events": 1,
            "stage": campaign.get("fault_stage", "no_protection_model"),
        },
        "rng": {"master_seed": seed, "selection_seed": seed},
        "limits": {"max_faults": limits.get("max_faults", 1), "max_ticks": 0},
        "oracle": {"kind": "exact_hash", "golden_id": wl.get("golden_id", "")},
    }
    # clean None values the v1 schema doesn't want
    for k in list(manifest["target"]):
        if manifest["target"][k] is None:
            del manifest["target"][k]

    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f"{run_id}.yaml")
    with open(path, "w") as f:
        yaml.safe_dump(manifest, f, sort_keys=False, default_flow_style=False)
    return path, manifest


# ---------------------------------------------------------------- run one rep

RESULT_PREFIX = "RESULT:"

def parse_runner_result(stdout):
    """Extract (classification, faults, exit_code) from runner.py's
    `[runner] RESULT: run_id=... classification=X faults_injected=N exit=E timed_out=...`
    line. Returns dict; fields None if the line is missing (counted as a
    SimulatorError by the caller — honest, never a silent Masked).

    runner.py prefixes its prints with "[runner] ", so we search for the
    RESULT marker anywhere in the line (not startswith)."""
    res = {"classification": None, "faults_injected": None, "exit": None,
           "timed_out": False, "run_id": None}
    for line in (stdout or "").splitlines():
        line = line.strip()
        if RESULT_PREFIX in line:
            body = line.split(RESULT_PREFIX, 1)[1].strip()
            for tok in body.split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    if k == "classification":
                        res["classification"] = v
                    elif k == "faults_injected":
                        try:
                            res["faults_injected"] = int(v)
                        except ValueError:
                            pass
                    elif k == "exit":
                        try:
                            res["exit"] = int(v)
                        except ValueError:
                            pass
                    elif k == "timed_out":
                        res["timed_out"] = (v.lower() == "true")
                    elif k == "run_id":
                        res["run_id"] = v
            break
    return res


def run_one_rep(manifest_path, binary, hang_timeout, keep_manifests, log_bad):
    """Shell out to tools/runner.py for one manifest. Returns a result dict
    (classification etc.) for the results.jsonl line."""
    cmd = [sys.executable, RUNNER, manifest_path, "--binary", binary]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=hang_timeout + 30)
    except subprocess.TimeoutExpired as e:
        res = {"classification": "Hang", "faults_injected": None,
               "exit": -1, "timed_out": True,
               "reason": f"runner.py exceeded {hang_timeout+30}s wall budget"}
        return res
    out = r.stdout or ""
    parsed = parse_runner_result(out)
    cls = parsed["classification"]
    if cls is None:
        # runner.py itself crashed/errored before printing RESULT (e.g.
        # unsupported injector mapping, schema fail). Honest: SimulatorError.
        cls = "SimulatorError"
        if log_bad:
            log_bad(r.stderr or "", out, manifest_path)
    res = {
        "classification": cls,
        "faults_injected": parsed["faults_injected"],
        "exit": parsed["exit"],
        "timed_out": parsed["timed_out"],
        "run_id": parsed["run_id"],
    }
    return res


# ---------------------------------------------------------------- summary writers

def write_heatmap(cell_results, campaign_id, artifacts_dir):
    """Per-cell CSV: each axis + counts + P_SDC/P_DUE/Reach point + Wilson CI."""
    os.makedirs(artifacts_dir, exist_ok=True)
    csv = os.path.join(artifacts_dir, "heatmap.csv")
    # collect all axis keys across cells for the header
    axis_keys = []
    for cell in cell_results:
        for k in cell["cell"]:
            if k not in axis_keys:
                axis_keys.append(k)
    header = (axis_keys + ["n_total", "n_valid", "n_inactive", "n_simerror",
                           "P_SDC", "P_SDC_lo", "P_SDC_hi",
                           "P_DUE", "P_DUE_lo", "P_DUE_hi",
                           "Reach", "Reach_lo", "Reach_hi", "frozen"])
    with open(csv, "w") as f:
        f.write(",".join(header) + "\n")
        for cell in cell_results:
            st = cell_stats(dict(cell["counter"]))
            row = []
            for k in axis_keys:
                row.append(str(cell["cell"].get(k, "")))
            row += [str(st["n_total"]), str(st["n_valid"]), str(st["n_inactive"]),
                    str(st["n_simerror"]),
                    f"{st['P_SDC']:.4f}", f"{st['P_SDC_ci'][0]:.4f}", f"{st['P_SDC_ci'][1]:.4f}",
                    f"{st['P_DUE']:.4f}", f"{st['P_DUE_ci'][0]:.4f}", f"{st['P_DUE_ci'][1]:.4f}",
                    f"{st['Reachability']:.4f}", f"{st['Reachability_ci'][0]:.4f}", f"{st['Reachability_ci'][1]:.4f}",
                    "1" if cell["frozen"] else "0"]
            f.write(",".join(row) + "\n")
    return csv


def write_summary(cell_results, campaign, artifacts_dir, wall_s, n_reps_done,
                  n_cells, runs_skipped):
    """Human-readable summary.md with per-cell table + honesty notes."""
    md = os.path.join(artifacts_dir, "summary.md")
    lines = []
    lines.append(f"# Campaign `{campaign['campaign_id']}` — summary\n")
    lines.append(f"- injector: `{campaign['injector']}`  config: `{campaign.get('config','C0')}`  mode: `{campaign.get('mode','SE')}`")
    lines.append(f"- cells: {n_cells}  reps done: {n_reps_done}  wall: {wall_s:.0f}s")
    wl = campaign["workload"]
    lines.append(f"- workload: `{wl.get('binary')}`  golden_id: `{wl.get('golden_id')}`")
    lines.append(f"- base_seed: {campaign['base_seed']}  (rep seed = base + cell_ordinal*1000 + rep)")
    if runs_skipped:
        lines.append(f"- **skipped reps**: {runs_skipped} (see log)")
    lines.append("")
    lines.append("## Per-cell (Wilson 95% CI)\n")
    lines.append("| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |")
    lines.append("|---|---|---|---|---|---|---|")
    for cell in cell_results:
        st = cell_stats(dict(cell["counter"]))
        cid = cell_id_str(cell["ordinal"], cell["cell"])
        def fmt(p, ci):
            return f"{p*100:.1f}% [{ci[0]*100:.1f},{ci[1]*100:.1f}]"
        lines.append(
            f"| {cid} | {st['n_total']} | {st['n_valid']} | "
            f"{fmt(st['P_SDC'], st['P_SDC_ci'])} | "
            f"{fmt(st['P_DUE'], st['P_DUE_ci'])} | "
            f"{fmt(st['Reachability'], st['Reachability_ci'])} | "
            f"{'yes' if cell['frozen'] else 'no'} |"
        )
    lines.append("")
    lines.append("## Honesty notes\n")
    lines.append("- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs "
                 "on a healthy 2nd machine (§0.4, §3.1 S6).")
    lines.append("- `SimulatorError` counts are runs where the tool/simulator broke "
                 "(gem5 panic or runner.py mapping error) — NOT valid FI outcomes; "
                 "excluded from N_valid (§1.4).")
    lines.append("- `frozen` cells failed the §1.5 replay-consistency check "
                 "(same manifest gave different classification on re-run).")
    lines.append("- Rates are conditional probabilities under the gem5 O3 + config "
                 "family; NOT product FIT (§4.3).")
    with open(md, "w") as f:
        f.write("\n".join(lines) + "\n")
    return md


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description="ARM64 CHAOS grid campaign driver (§1.5)")
    ap.add_argument("campaign", help="campaign.yaml path")
    ap.add_argument("--jobs", type=int, default=1,
                    help="concurrent rep workers (gem5 ~1 core ~2GB; this machine "
                         "~92s/run — keep small here). Default 1 (pilot on this fault machine).")
    ap.add_argument("--n_per_cell", type=int, default=0,
                    help="override n_per_cell (0 = use campaign.yaml value). Useful for tiny pilot verify.")
    ap.add_argument("--replay_pct", type=float, default=-1,
                    help="override replay_pct (§1.5). -1 = use campaign.yaml (default 5).")
    ap.add_argument("--dry", action="store_true",
                    help="expand grid + write manifests only, do NOT run gem5.")
    ap.add_argument("--keep_manifests", action="store_true", default=True,
                    help="keep per-rep manifests in runs/ (default on, for provenance).")
    args = ap.parse_args()

    with open(args.campaign) as f:
        campaign = yaml.safe_load(f)

    # campaign schema check (best-effort)
    if HAVE_SCHEMA:
        sp = os.path.join(REPO, "schemas", "campaign.schema.json")
        with open(sp) as sf:
            schema = json.load(sf)
        try:
            jsonschema.validate(campaign, schema)
            print(f"[campaign] schema: OK ({sp})")
        except jsonschema.ValidationError as e:
            sys.exit(f"[campaign] schema validation FAILED: {e.message}")
    else:
        print("[campaign] jsonschema not installed — skipping schema check")

    n_per_cell = args.n_per_cell or campaign["n_per_cell"]
    replay_pct = args.replay_pct if args.replay_pct >= 0 else campaign.get("replay_pct", 5.0)
    hang_timeout = campaign.get("hang_timeout", 600)
    binary = os.path.join(REPO, campaign["workload"]["binary"])

    cells = expand_grid(campaign["grid"])
    print(f"[campaign] {len(cells)} cells x {n_per_cell} reps = {len(cells)*n_per_cell} runs")
    print(f"[campaign] jobs={args.jobs}  hang_timeout={hang_timeout}s  replay_pct={replay_pct}")

    runs_dir = os.path.join(REPO, "runs", campaign["campaign_id"])
    artifacts_dir = os.path.join(REPO, "artifacts", campaign["campaign_id"])
    os.makedirs(runs_dir, exist_ok=True)
    os.makedirs(artifacts_dir, exist_ok=True)

    # bad-run log (runner.py stderr when no RESULT line) for provenance.
    bad_log_path = os.path.join(artifacts_dir, "bad_runs.log")

    def log_bad(stderr, stdout, manifest_path):
        with open(bad_log_path, "a") as f:
            f.write(f"=== {manifest_path} ===\n--- stderr ---\n{stderr[-500:]}\n--- stdout ---\n{stdout[-500:]}\n\n")

    cell_results = []
    total_runs = len(cells) * n_per_cell
    runs_done = 0
    t0 = time.time()

    # build the full rep work-list first (so ProcessPoolExecutor can batch),
    # preserving cell ordering for deterministic cell_ordinal.
    work = []  # (cell_ordinal, cell, rep, manifest_path, outdir)
    for ord_i, cell in enumerate(cells):
        outdir = os.path.join(runs_dir, f"c{ord_i:04d}")
        for rep in range(n_per_cell):
            mpath, _ = manifest_for_cell(campaign, cell, ord_i, rep, outdir)
            work.append((ord_i, cell, rep, mpath, outdir))

    if args.dry:
        print(f"[campaign] --dry: wrote {len(work)} manifests to {runs_dir}/, not running gem5.")
        return 0

    # run reps (concurrency optional; default 1 = serial, safe on this machine)
    from concurrent.futures import ProcessPoolExecutor, as_completed
    results_by_cell = {i: [] for i in range(len(cells))}
    cell_of = {}  # manifest_path -> cell_ordinal (for result routing)
    for (ord_i, cell, rep, mpath, outdir) in work:
        cell_of[mpath] = ord_i

    def _do_rep(item):
        ord_i, cell, rep, mpath, outdir = item
        res = run_one_rep(mpath, binary, hang_timeout, args.keep_manifests, log_bad)
        return (mpath, res)

    if args.jobs <= 1:
        for item in work:
            runs_done += 1
            mpath, res = _do_rep(item)
            results_by_cell[cell_of[mpath]].append((mpath, res))
            if runs_done % 5 == 0 or runs_done == total_runs:
                el = time.time() - t0
                print(f"[campaign] {runs_done}/{total_runs} reps done ({el:.0f}s, "
                      f"~{el/runs_done:.0f}s/rep)")
    else:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = {ex.submit(_do_rep, item): item for item in work}
            for fut in as_completed(futs):
                runs_done += 1
                mpath, res = fut.result()
                results_by_cell[cell_of[mpath]].append((mpath, res))
                if runs_done % 5 == 0 or runs_done == total_runs:
                    el = time.time() - t0
                    print(f"[campaign] {runs_done}/{total_runs} reps done ({el:.0f}s)")

    # write per-cell results.jsonl + aggregate counts
    for ord_i, cell in enumerate(cells):
        cdir = os.path.join(runs_dir, f"c{ord_i:04d}")
        jpath = os.path.join(cdir, "results.jsonl")
        counter = {c: 0 for c in ALL_CLASSES}
        with open(jpath, "w") as f:
            for (mpath, res) in results_by_cell[ord_i]:
                rec = {"manifest": os.path.basename(mpath),
                       "classification": res["classification"],
                       "faults_injected": res["faults_injected"],
                       "exit": res["exit"], "timed_out": res["timed_out"]}
                f.write(json.dumps(rec) + "\n")
                if res["classification"] in counter:
                    counter[res["classification"]] += 1
                else:
                    counter["SimulatorError"] += 1  # unknown class -> tool error

        # §1.5 replay-consistency check: re-run max(1, round(replay_pct%)) reps,
        # compare classification. Mismatch -> freeze cell.
        n_replay = max(1, round(replay_pct / 100.0 * n_per_cell))
        frozen = False
        for (mpath, res) in results_by_cell[ord_i][:n_replay]:
            r2 = run_one_rep(mpath, binary, hang_timeout, args.keep_manifests, log_bad)
            if r2["classification"] != res["classification"]:
                frozen = True
                with open(bad_log_path, "a") as f:
                    f.write(f"[replay-mismatch] {mpath}: {res['classification']} -> {r2['classification']}\n")

        cell_results.append({"ordinal": ord_i, "cell": cell, "counter": counter, "frozen": frozen})

    wall = time.time() - t0
    csv = write_heatmap(cell_results, campaign["campaign_id"], artifacts_dir)
    md = write_summary(cell_results, campaign, artifacts_dir, wall, runs_done, len(cells), 0)
    print(f"\n[campaign] DONE — {runs_done} reps in {wall:.0f}s")
    print(f"[campaign] heatmap: {csv}")
    print(f"[campaign] summary: {md}")
    # print the summary to stdout for quick inspection
    print("\n--- summary.md ---")
    with open(md) as f:
        print(f.read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
