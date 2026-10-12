#!/usr/bin/env python3
"""ooo_handoff.py -- per-campaign and master handoff generation (plan Task 12;
task-book §四).

Reads a finished campaign's results.jsonl + per-sample observation.json files
and writes handoff.json + handoff.md into the campaign directory. Everything
the task book demands is included, and everything absent is reported as
"n/a" -- never a silent zero (the honesty convention).

  handoff campaign --dir <campaign_dir> --campaign-yaml <y>
      [--guard-dir G] [--runs-root R]
  handoff master  --dirs <d1> <d2> ... --batch <batch.yaml>
      [--guard-dir G] [--runs-root R]

The master handoff aggregates the per-campaign ones and adds the batch-level
identity (frozen head / gem5 sha), totals, and the absolute-path index.
"""

import argparse
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.realpath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from wilson import cell_stats, ALL_CLASSES  # noqa: E402  (one stats source)

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip install pyyaml (needed for campaign yaml parsing)")

DEFAULT_RUNS_ROOT = "/home/sdc/gem5-fi-ding/runs"
DEFAULT_GUARD_DIR = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard"

FIVE_PRIMARY = ("Masked", "DetectedContained", "SDC", "Crash", "Hang")


def _read_json(path):
    with open(path) as f:
        return json.load(f)


def _load_results(campaign_dir):
    rows = []
    p = os.path.join(campaign_dir, "results.jsonl")
    if not os.path.exists(p):
        return rows
    with open(p) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError:
                rows.append({"classification": "UNPARSEABLE_ROW", "raw": line})
    return rows


def _load_observations(campaign_dir):
    """samples/<run_id>/observation.json -> {run_id: obs}, sorted by rep."""
    out = {}
    sdir = os.path.join(campaign_dir, "samples")
    if not os.path.isdir(sdir):
        return out
    for name in sorted(os.listdir(sdir)):
        op = os.path.join(sdir, name, "observation.json")
        if os.path.exists(op):
            try:
                out[name] = _read_json(op)
            except (OSError, ValueError):
                out[name] = None  # unreadable is honest data, not a skip
    return out


def _count_quarantined(campaign_dir):
    q = os.path.join(campaign_dir, "QUARANTINE")
    return len(os.listdir(q)) if os.path.isdir(q) else 0


def _count_staging_leftovers(campaign_dir):
    s = os.path.join(campaign_dir, "samples", ".staging")
    return len(os.listdir(s)) if os.path.isdir(s) else 0


def _parse_ts(s):
    try:
        return time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%S"))
    except (TypeError, ValueError):
        return None


def _resource_peaks(guard_dir, t_lo, t_hi):
    """min MemAvailable / max gem5 RSS+count over the campaign's wall window,
    from the guard monitor CSV. Values absent from the log -> None (n/a)."""
    p = os.path.join(guard_dir, "monitor", "resources.log")
    if not os.path.exists(p):
        return None
    min_mem = None
    max_rss = None
    max_g5 = None
    with open(p) as f:
        header = f.readline().strip().split(",")
        idx = {k: i for i, k in enumerate(header)}
        for line in f:
            parts = line.rstrip("\n").split(",")
            if len(parts) < len(header):
                continue
            ts = _parse_ts(parts[idx["ts"]])
            if ts is None:
                continue
            if t_lo is not None and ts < t_lo:
                continue
            if t_hi is not None and ts > t_hi + 60:
                continue
            try:
                mem = int(parts[idx["mem_available_kib"]])
                min_mem = mem if min_mem is None else min(min_mem, mem)
                rss = int(parts[idx["gem5_rss_kib"]])
                max_rss = rss if max_rss is None else max(max_rss, rss)
                g5 = int(parts[idx["gem5_count"]])
                max_g5 = g5 if max_g5 is None else max(max_g5, g5)
            except (ValueError, KeyError):
                continue
    if min_mem is None:
        return None
    return {"min_mem_available_kib": min_mem,
            "max_gem5_rss_kib": max_rss,
            "max_gem5_processes": max_g5}


def _n_a(v):
    return "n/a" if v is None else v


def build_campaign_handoff(campaign_dir, campaign_yaml, guard_dir):
    with open(campaign_yaml) as f:
        cy = yaml.safe_load(f)
    rows = _load_results(campaign_dir)
    obs = _load_observations(campaign_dir)

    # --- classification counts (from results rows; observations as source
    # of truth for conservation/chain data) --------------------------------
    counts = {c: 0 for c in ALL_CLASSES}
    for r in rows:
        cls = r.get("classification")
        counts[cls if cls in counts else "SimulatorError"] += 1
    n_rows = len(rows)
    valid_rows = [r for r in rows
                  if r.get("classification") not in ("SimulatorError",
                                                     "UNPARSEABLE_ROW")]
    n_valid = len(valid_rows)

    # --- seeds / attempts ---------------------------------------------------
    seeds = sorted({r.get("seed") for r in rows if r.get("seed") is not None})
    reps = sorted({r.get("rep") for r in rows if r.get("rep") is not None})
    n_topup = len([r for r in rows if r.get("rep") is not None
                   and r["rep"] >= 385])

    # --- conservation + chain completeness from observations ---------------
    n_obs_ok = 0
    activated_total = 0
    primary_total = 0
    post_sim_total = 0
    inactive_total = 0
    conservation_ok_all = True
    chain_complete_n = 0
    gap_hist = {}
    l3_unsupported_only = 0
    unreadable_obs = 0
    first_div = None
    first_l1_div = None
    for run_id, o in sorted(obs.items()):
        if o is None:
            unreadable_obs += 1
            conservation_ok_all = False
            continue
        n_obs_ok += 1
        l5 = o.get("l5") or {}
        l0 = o.get("l0") or {}
        activated = l0.get("activated", l0.get("injected"))
        if isinstance(activated, int):
            activated_total += activated
        cls = l5.get("classification")
        if cls in FIVE_PRIMARY:
            primary_total += 1
        elif cls == "SimulatorError" and isinstance(l0.get("injected"), int) \
                and l0["injected"] >= 1:
            post_sim_total += 1
        elif cls == "Inactive":
            inactive_total += 1
        cons = (l5.get("conservation") or {}).get("ok")
        if cons is not True:
            conservation_ok_all = False
        if o.get("chain_complete"):
            chain_complete_n += 1
        else:
            for g in o.get("chain_gaps") or ["UNKNOWN"]:
                gap_hist[g] = gap_hist.get(g, 0) + 1
            gaps = set(o.get("chain_gaps") or [])
            if gaps == {"L3"}:
                l3_unsupported_only += 1
        # first divergence summary (first non-Masked sample with L2 evidence)
        fd = ((o.get("l2") or {}).get("first_divergent_commit"))
        if fd and first_div is None and cls not in ("Masked", "Inactive"):
            first_div = {"run_id": run_id, "seq": fd.get("seq"),
                         "class": fd.get("class"),
                         "detail": (fd.get("detail") or "")[:160]}
        l1fd = ((o.get("l1") or {}).get("first_divergence") or {})
        if l1fd.get("snap_seq") is not None and first_l1_div is None:
            first_l1_div = {"run_id": run_id,
                            "snap_seq": l1fd.get("snap_seq"),
                            "tick": l1fd.get("tick")}

    # --- wall window (from results ts) --------------------------------------
    ts_all = [_parse_ts(r.get("ts")) for r in rows]
    ts_all = [t for t in ts_all if t is not None]
    t_lo = min(ts_all) if ts_all else None
    t_hi = max(ts_all) if ts_all else None
    wall_s = (t_hi - t_lo) if (t_lo is not None and t_hi is not None) else None
    peaks = _resource_peaks(guard_dir, t_lo, t_hi)

    # an observation identity sample for the hash block
    ident_sample = None
    for o in obs.values():
        if o:
            ident_sample = o.get("identity")
            break

    stats = cell_stats(dict(counts))
    h = {
        "schema_version": "ooo-handoff/v1",
        "campaign_id": cy.get("campaign_id"),
        "runid_row": cy.get("runid_row"),
        "submodel": cy.get("submodel"),
        "phase": cy.get("phase"),
        "status": ("COMPLETE"
                   if n_valid >= cy.get("n_per_cell", 10**9)
                   else "PARTIAL"),
        "identity": {
            "chaos_commit": cy.get("chaos_commit"),
            "patchset_sha256": cy.get("patchset_sha256"),
            "gem5_sha256": (ident_sample or {}).get("gem5_sha256")
            or cy.get("frozen_gem5_sha256", "n/a"),
            "config": (ident_sample or {}).get("config")
            or {"path": "configs/se/ooo_proxy.py", "sha256": "n/a"},
            "workload": {
                "path": cy.get("workload", {}).get("binary"),
                "sha256": cy.get("workload", {}).get("binary_sha256"),
                "golden_id": cy.get("workload", {}).get("golden_id"),
            },
            "golden_key": (ident_sample or {}).get("golden_key", "n/a"),
        },
        "seeds": {
            "base_seed": cy.get("base_seed"),
            "seeds_used": {"n": len(seeds),
                           "min": seeds[0] if seeds else "n/a",
                           "max": seeds[-1] if seeds else "n/a"},
            "reps": {"n": len(reps), "min": reps[0] if reps else "n/a",
                     "max": reps[-1] if reps else "n/a"},
            "topup_rows": n_topup,
        },
        "counts": {
            "n_rows": n_rows,
            "n_valid": n_valid,
            "n_simulator_error": counts["SimulatorError"],
            "per_class": {c: counts[c] for c in ALL_CLASSES if counts[c]},
            "P_SDC": f"{stats['P_SDC']*100:.1f}% "
                     f"[{stats['P_SDC_ci'][0]*100:.1f},"
                     f"{stats['P_SDC_ci'][1]*100:.1f}]",
            "P_DUE": f"{stats['P_DUE']*100:.1f}% "
                     f"[{stats['P_DUE_ci'][0]*100:.1f},"
                     f"{stats['P_DUE_ci'][1]*100:.1f}]",
        },
        "conservation": {
            "activated_total": activated_total,
            "five_primary_total": primary_total,
            "post_activation_simulator_failure_total": post_sim_total,
            "inactive_total": inactive_total,
            "ok": (conservation_ok_all
                   and activated_total == primary_total + post_sim_total),
            "note": ("all observations readable and conservation holds"
                     if conservation_ok_all else
                     "some observations missing/unreadable or per-sample "
                     "conservation failed -- see chain_audit"),
        },
        "chain": {
            "observations_readable": n_obs_ok,
            "observations_unreadable": unreadable_obs,
            "n_chain_complete": chain_complete_n,
            "n_chain_incomplete": n_obs_ok - chain_complete_n,
            "gap_histogram": gap_hist,
            "l3_unsupported_only": l3_unsupported_only,
            "note": ("decode/rat components have no L3 source-read "
                     "association; chain_complete=false with gap L3 is the "
                     "honest recorded state (task-book §二.3), counted "
                     "separately from real gaps"),
        },
        "first_divergence": {
            "l2_first_divergent_commit": first_div or "n/a",
            "l1_first_divergence": first_l1_div or "n/a",
        },
        "retries_and_quarantine": {
            "quarantined_samples": _count_quarantined(campaign_dir),
            "staging_leftovers": _count_staging_leftovers(campaign_dir),
        },
        "resources": peaks or "n/a",
        "wall_seconds": wall_s,
        "paths": {
            "campaign_dir": os.path.abspath(campaign_dir),
            "results_jsonl": os.path.abspath(
                os.path.join(campaign_dir, "results.jsonl")),
            "samples_dir": os.path.abspath(
                os.path.join(campaign_dir, "samples")),
            "campaign_yaml": os.path.abspath(campaign_yaml),
        },
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    return h


def write_campaign_handoff(campaign_dir, campaign_yaml, guard_dir):
    h = build_campaign_handoff(campaign_dir, campaign_yaml, guard_dir)
    jp = os.path.join(campaign_dir, "handoff.json")
    with open(jp, "w") as f:
        json.dump(h, f, indent=2, ensure_ascii=False)
        f.write("\n")
    mp = os.path.join(campaign_dir, "handoff.md")
    with open(mp, "w") as f:
        f.write(f"# Handoff — {h['campaign_id']} "
                f"({h['runid_row']}-{h['submodel']}, {h['phase']})\n\n")
        f.write(f"- status: **{h['status']}**  rows: {h['counts']['n_rows']}  "
                f"valid: {h['counts']['n_valid']}\n")
        f.write(f"- identity: chaos_commit `{h['identity']['chaos_commit']}` "
                f"gem5 `{str(h['identity']['gem5_sha256'])[:12]}...` "
                f"golden_key `{h['identity']['golden_key']}`\n")
        f.write(f"- seeds: base {h['seeds']['base_seed']} "
                f"({h['seeds']['seeds_used']['n']} used, reps "
                f"{h['seeds']['reps']['min']}..{h['seeds']['reps']['max']}"
                f", topup rows {h['seeds']['topup_rows']})\n")
        pc = ", ".join(f"{k}={v}" for k, v in
                       h["counts"]["per_class"].items())
        f.write(f"- classes: {pc}\n")
        f.write(f"- P_SDC {h['counts']['P_SDC']}  P_DUE "
                f"{h['counts']['P_DUE']}\n")
        c = h["conservation"]
        f.write(f"- conservation: activated {c['activated_total']} == "
                f"five-primary {c['five_primary_total']} + post-sim "
                f"{c['post_activation_simulator_failure_total']} -> "
                f"{'OK' if c['ok'] else 'CHECK'}\n")
        ch = h["chain"]
        f.write(f"- chain: complete {ch['n_chain_complete']}/"
                f"{ch['observations_readable']} "
                f"(L3-unsupported-only {ch['l3_unsupported_only']}; "
                f"gaps {ch['gap_histogram']})\n")
        f.write(f"- first divergence: L2 {h['first_divergence']['l2_first_divergent_commit']}  "
                f"L1 {h['first_divergence']['l1_first_divergence']}\n")
        f.write(f"- quarantine: {h['retries_and_quarantine']['quarantined_samples']}  "
                f"staging leftovers: "
                f"{h['retries_and_quarantine']['staging_leftovers']}\n")
        f.write(f"- resources: {_n_a(h['resources'])}\n")
        f.write(f"- wall: {_n_a(h['wall_seconds'])}s\n")
        f.write(f"- evidence: `{h['paths']['results_jsonl']}`, "
                f"`{h['paths']['samples_dir']}`\n")
    return jp, mp


def build_master_handoff(campaign_dirs, batch_yaml, guard_dir, runs_root):
    with open(batch_yaml) as f:
        batch = yaml.safe_load(f)
    per = []
    for d in campaign_dirs:
        # the campaign yaml is recorded in the batch spec
        cy = batch.get("campaign_yamls", {}).get(os.path.basename(d))
        if cy is None:
            # fall back: campaign dir name -> campaigns/ooo-l0l5/<id>.yaml
            cy = os.path.join(runs_root, "..", "campaigns", "ooo-l0l5",
                              os.path.basename(d) + ".yaml")
            cy = os.path.normpath(cy)
        per.append(build_campaign_handoff(d, cy, guard_dir))
    master = {
        "schema_version": "ooo-handoff-master/v1",
        "batch_id": batch.get("batch_id"),
        "frozen": batch.get("frozen", {}),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "campaigns": per,
        "totals": {
            "n_valid": sum(p["counts"]["n_valid"] for p in per),
            "n_rows": sum(p["counts"]["n_rows"] for p in per),
            "per_class": {},
            "n_chain_complete": sum(p["chain"]["n_chain_complete"]
                                    for p in per),
            "n_chain_incomplete": sum(p["chain"]["n_chain_incomplete"]
                                      for p in per),
        },
        "paths": [p["paths"] for p in per],
    }
    for p in per:
        for k, v in p["counts"]["per_class"].items():
            master["totals"]["per_class"][k] = \
                master["totals"]["per_class"].get(k, 0) + v
    return master


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("campaign")
    c.add_argument("--dir", required=True)
    c.add_argument("--campaign-yaml", required=True)
    m = sub.add_parser("master")
    m.add_argument("--dirs", nargs="+", required=True)
    m.add_argument("--batch", required=True)
    for s in (c, m):
        s.add_argument("--guard-dir", default=DEFAULT_GUARD_DIR)
        s.add_argument("--runs-root", default=DEFAULT_RUNS_ROOT)
    args = ap.parse_args()

    if args.cmd == "campaign":
        jp, mp = write_campaign_handoff(args.dir, args.campaign_yaml,
                                        args.guard_dir)
        print(f"[handoff] wrote {jp}\n[handoff] wrote {mp}")
        return 0
    master = build_master_handoff(args.dirs, args.batch, args.guard_dir,
                                  args.runs_root)
    out = os.path.join(os.path.dirname(os.path.abspath(args.dirs[0])),
                       "handoff_master.json")
    with open(out, "w") as f:
        json.dump(master, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"[handoff] wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
