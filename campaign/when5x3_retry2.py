#!/usr/bin/env python3
"""0202c targeted re-run driver for the 23 PARTIAL WHEN-5X3 MMU chains.

Re-runs the 8 matching Controls + the 23 PARTIAL Fault conditions under the
new observation-only gem5 build into runs/W5X3_RETRY2/ (originals in
runs/W5X3/ are never touched).  Verifies Control N is unchanged before faults.

Usage:
  python3 campaign/when5x3_retry2.py --dry-run
  python3 campaign/when5x3_retry2.py --controls-only --jobs 8
  python3 campaign/when5x3_retry2.py --jobs 16
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "campaign"))

import when5x3_runner as R

RETRY2 = os.path.join(ROOT, "runs", "W5X3_RETRY2")
R.RUNS = RETRY2  # redirect manifest + run-dir output

# PARTIAL_23[..] = (SampleRunID, Model, WL, NewContext, ControlContext,
#                   TimingID, frozen_ordinal)
PARTIAL_23 = [
    ("M03-F0-W11-W5X3-C02-T01", "M03", "W11", "C02", "R05", "T01", 1),
    ("M03-F0-W11-W5X3-C02-T02", "M03", "W11", "C02", "R05", "T02", 2),
    ("M03-F0-W11-W5X3-C02-T03", "M03", "W11", "C02", "R05", "T03", 3),
    ("M04-F0-W12-W5X3-C02-T01", "M04", "W12", "C02", "R05", "T01", 2001),
    ("M04-F0-W12-W5X3-C02-T02", "M04", "W12", "C02", "R05", "T02", 10003),
    ("M04-F0-W12-W5X3-C02-T03", "M04", "W12", "C02", "R05", "T03", 18005),
    ("M05-F0-W13-W5X3-C02-T01", "M05", "W13", "C02", "R05", "T01", 1),
    ("M05-F0-W13-W5X3-C02-T02", "M05", "W13", "C02", "R05", "T02", 2),
    ("M05-F0-W13-W5X3-C02-T03", "M05", "W13", "C02", "R05", "T03", 3),
    ("M05-F0-W13-W5X3-C03-T01", "M05", "W13", "C03", "C03", "T01", 1),
    ("M05-F0-W13-W5X3-C03-T02", "M05", "W13", "C03", "C03", "T02", 2),
    ("M05-F0-W13-W5X3-C03-T03", "M05", "W13", "C03", "C03", "T03", 3),
    ("M05-F0-W13-W5X3-C04-T01", "M05", "W13", "C04", "R04", "T01", 1),
    ("M05-F0-W13-W5X3-C04-T02", "M05", "W13", "C04", "R04", "T02", 2),
    ("M05-F0-W13-W5X3-C04-T03", "M05", "W13", "C04", "R04", "T03", 3),
    ("M05-F0-W13-W5X3-C05-T01", "M05", "W13", "C05", "R03", "T01", 1),
    ("M05-F0-W13-W5X3-C05-T02", "M05", "W13", "C05", "R03", "T02", 2),
    ("M05-F0-W13-W5X3-C05-T03", "M05", "W13", "C05", "R03", "T03", 3),
    ("M07-F0-W14-W5X3-C02-T01", "M07", "W14", "C02", "R03", "T01", 1),
    ("M07-F0-W14-W5X3-C02-T02", "M07", "W14", "C02", "R03", "T02", 3),
    ("M07-F0-W14-W5X3-C05-T01", "M07", "W14", "C05", "R05", "T01", 1),
    ("M07-F0-W14-W5X3-C05-T02", "M07", "W14", "C05", "R05", "T02", 2),
    ("M07-F0-W14-W5X3-C05-T03", "M07", "W14", "C05", "R05", "T03", 3),
]

# (model, ControlContext, NewContext, m04_decoy, frozen_N)
CONTROLS = [
    ("M03", "R05", "C02", 0, 3),
    ("M04", "R05", "C02", 537716, 20005),
    ("M05", "R05", "C02", 0, 3),
    ("M05", "C03", "C03", 0, 3),
    ("M05", "R04", "C04", 0, 3),
    ("M05", "R03", "C05", 0, 3),
    ("M07", "R03", "C02", 0, 6),
    ("M07", "R05", "C05", 0, 3),
]


def find_ctrl(model, nctx):
    for (m, cctx, nc, decoy, n) in CONTROLS:
        if m == model and nc == nctx:
            return (cctx, decoy, n)
    raise KeyError("no control for %s-%s" % (model, nctx))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--controls-only", action="store_true")
    ap.add_argument("--jobs", type=int, default=8)
    args = ap.parse_args()

    if args.dry_run:
        print("gem5:", R.GEM5)
        print("gem5_sha256:", R.sha256(R.GEM5))
        print("controls:")
        for (m, cctx, nc, decoy, n) in CONTROLS:
            print("  %s-%s (cctx=%s) frozen_N=%d" % (m, nc, cctx, n))
        print("faults:", len(PARTIAL_23))
        for s in PARTIAL_23:
            print("  ", s[0])
        return

    print("[retry2] gem5_sha256=%s" % R.sha256(R.GEM5))
    print("[retry2] runs -> %s" % RETRY2)

    ctrl_results = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {}
        for (m, cctx, nc, decoy, n) in CONTROLS:
            rid = "CTRL2-%s-%s" % (m, nc)
            futs[ex.submit(R.execute, rid, m, cctx, 1, True, None, None,
                           R.log, nc, decoy)] = (m, cctx, nc, n)
        for fut in as_completed(futs):
            m, cctx, nc, n_frozen = futs[fut]
            info = fut.result()
            n_new = int((info.get("eligible_summary") or {}).get(
                "eligible_total", 0) or 0)
            ok = "OK" if n_new == n_frozen else "MISMATCH"
            ctrl_results[(m, nc)] = (info, n_new, n_frozen)
            print("[retry2][ctrl] %s-%s N=%d frozen=%d %s" %
                  (m, nc, n_new, n_frozen, ok))

    if args.controls_only:
        return

    mism = [(m, nc) for (m, nc), (_, nn, nf) in ctrl_results.items()
            if nn != nf]
    if mism:
        print("[retry2] ABORT: control N mismatch %s" % mism)
        sys.exit(2)

    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {}
        for s in PARTIAL_23:
            (sid, model, wl, nctx, cctx, tidx, f_ord) = s
            _, decoy, _ = find_ctrl(model, nctx)
            rid = "%s-F0-%s-W5X3-RETRY2-%s-%s" % (model, wl, nctx, tidx)
            futs[ex.submit(R.execute, rid, model, cctx, f_ord, False, None,
                           None, R.log, nctx, decoy)] = sid
        for fut in as_completed(futs):
            sid = futs[fut]
            info = fut.result()
            print("[retry2][fault] %s rc=%s act=%s" %
                  (sid, info.get("returncode"), info.get("activation_count")))

    # SampleRunID -> RETRY2 run id mapping (for evidence-index fix).
    mapping = {}
    for (sid, model, wl, nctx, cctx, tidx, f_ord) in PARTIAL_23:
        rid = "%s-F0-%s-W5X3-RETRY2-%s-%s" % (model, wl, nctx, tidx)
        mp = os.path.join(RETRY2, rid, "manifest.json")
        if os.path.isfile(mp):
            with open(mp) as fh:
                d = json.load(fh)
            mapping[sid] = {
                "retry_run_id": rid,
                "trace": d.get("trace"),
                "trace_sha256": d.get("trace_sha256"),
                "gem5_sha256": d.get("gem5_sha256"),
            }
    with open(os.path.join(ROOT, "analysis", "retry2_map.json"), "w") as fh:
        json.dump(mapping, fh, indent=2, sort_keys=True)
    print("[retry2] wrote analysis/retry2_map.json (%d entries)" % len(mapping))


if __name__ == "__main__":
    main()