#!/usr/bin/env python3
"""W5X3-OBS-0222: re-run M07-C02-T01/T02 + matching control under the new
observation-only build (ce80a9c9...).  Unique RunIDs under runs/W5X3_OBS/,
never overwriting the historical runs/W5X3 or runs/W5X3_RETRY2 traces."""
import os
import sys
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = "/home/sdc/gem5-fi-mmu-impl-v2"
sys.path.insert(0, os.path.join(ROOT, "campaign"))
import when5x3_runner as R

R.RUNS = os.path.join(ROOT, "runs", "W5X3_OBS")
os.makedirs(R.RUNS, exist_ok=True)

def log(msg):
    print("[obs0222] %s" % msg, flush=True)

# (run_id, model, ctx(ControlContext), ordinal, prescan, label_ctx)
JOBS = [
    ("CTRL-OBS-M07-C02", "M07", "R03", 1, True,  "C02"),
    ("M07-F0-W14-W5X3-OBS-C02-T01", "M07", "R03", 1, False, "C02"),
    ("M07-F0-W14-W5X3-OBS-C02-T02", "M07", "R03", 3, False, "C02"),
]

def main():
    log("gem5_sha256=%s" % R.sha256(R.GEM5))
    log("runs -> %s" % R.RUNS)
    results = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futs = {}
        for (rid, model, ctx, ordinal, prescan, label_ctx) in JOBS:
            futs[ex.submit(R.execute, rid, model, ctx, ordinal, prescan,
                           None, None, log, label_ctx, 0)] = rid
        for fut in as_completed(futs):
            rid = futs[fut]
            try:
                info = fut.result()
                results[rid] = info
                log("OK %s rc=%s act=%s N=%s elapsed=%ss kinds_act=%s" % (
                    rid, info.get("returncode"), info.get("activation_count"),
                    (info.get("eligible_summary") or {}).get("eligible_total"),
                    info.get("elapsed_sec"),
                    info.get("kinds", {}).get("mmu_fault_activate", 0)))
            except Exception as e:
                log("FAILED %s: %s" % (rid, e))
    with open(os.path.join(ROOT, "work", "obs0222_results.json"), "w") as fh:
        json.dump(results, fh, indent=2, sort_keys=True, default=str)
    log("DONE: %d results" % len(results))

if __name__ == "__main__":
    main()
