#!/usr/bin/env python3
"""Run the 3 fb1b-build Controls for M05-C03/C04/C05 into runs/W5X3_RETRY2/
CTRL2B-* (never overwrites the eb327 CTRL2-* Controls).

The current gem5 binary is the fb1b build; these Controls give the 9 fb1b
M05-C03/C04/C05 faults a build-matched golden.  Runs sequentially to bound
memory (each copies a 2.3 GB disk template).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "campaign"))
import when5x3_runner as R

R.RUNS = os.path.join(R.ROOT, "runs", "W5X3_RETRY2")

# (run_id, model, ctx(ControlContext), label_ctx(NewContext))
CONTROLS = [
    ("CTRL2B-M05-C03", "M05", "C03", "C03"),
    ("CTRL2B-M05-C04", "M05", "R04", "C04"),
    ("CTRL2B-M05-C05", "M05", "R03", "C05"),
]

print("gem5:", R.GEM5, flush=True)
print("gem5_sha256:", R.GEM5_SHA, flush=True)
for rid, model, ctx, lctx in CONTROLS:
    print("--- running %s (model=%s ctx=%s label=%s) ---" %
          (rid, model, ctx, lctx), flush=True)
    info = R.execute(rid, model, ctx, 1, True, None, None, R.log, lctx, 0)
    n = int((info.get("eligible_summary") or {}).get("eligible_total", 0) or 0)
    print("RESULT %s N=%d rc=%s act=%s build=%s" %
          (rid, n, info.get("returncode"), info.get("activation_count"),
           (info.get("gem5_sha256") or "")[:16]), flush=True)
print("ALL_CONTROLS_DONE", flush=True)