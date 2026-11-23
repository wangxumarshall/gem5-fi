#!/usr/bin/env python3
"""Targeted re-run of M07-C05 (control + 3 fault timings) under the NEW gem5
binary (observational M07 activation-tid link).  Writes into runs/W5X3_RETRY
so the 117 original runs / 39 controls are never overwritten."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "campaign"))
import when5x3_runner as R  # noqa: E402

# Redirect output to a NEW run tree and record the new build hash.
R.RUNS = os.path.join(R.ROOT, "runs", "W5X3_RETRY")
R.GEM5_SHA = R.sha256(R.GEM5)
os.makedirs(R.RUNS, exist_ok=True)

CTRL = "CTRL-M07-C05"
MODEL, CTX, LBL = "M07", "R05", "C05"


def main():
    # 1. control (defines N) — re-run under the new binary so the timeline is
    #    matched to the new build.
    ctrl = R.prescan(MODEL, CTX, run_id=CTRL, label_ctx=LBL, log=print)
    n = int((ctrl.get("eligible_summary") or {}).get("eligible_total", 0) or 0)
    print("CONTROL N =", n, "activation_count =", ctrl.get("activation_count"))
    if n < 3:
        print("N<3, aborting fault runs")
        return
    # 2. three fault runs
    for tid_t in ("T01", "T02", "T03"):
        num, den = {"T01": (1, 10), "T02": (1, 2), "T03": (9, 10)}[tid_t]
        ordinal = (num * n + den - 1) // den
        run_id = "M07-F0-W14-W5X3-RETRY-%s" % tid_t
        info = R.execute(run_id, MODEL, CTX, ordinal, False,
                         ctrl.get("asid"), ctrl.get("old_pfn"), print,
                         label_ctx=LBL,
                         m04_decoy=ctrl.get("m04_decoy", 0) or 0)
        print("FAULT", tid_t, "rc=", info.get("returncode"),
              "act=", info.get("activation_count"))


if __name__ == "__main__":
    main()