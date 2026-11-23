#!/usr/bin/env python3
"""Targeted re-run of M07-C05 and M04-C02 (control + 3 fault timings each)
under the NEW gem5 binary (observational activation-tid / synthetic-seq link).
Writes into runs/W5X3_RETRY so the 117 original runs / 39 controls are never
overwritten."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "campaign"))
import when5x3_runner as R  # noqa: E402

ORIG_RUNS = R.RUNS  # runs/W5X3 (unmodified historical data)


def orig_manifest(run_id):
    import json
    p = os.path.join(ORIG_RUNS, run_id, "manifest.json")
    with open(p) as fh:
        return json.load(fh)


R.RUNS = os.path.join(R.ROOT, "runs", "W5X3_RETRY")
R.GEM5_SHA = R.sha256(R.GEM5)
os.makedirs(R.RUNS, exist_ok=True)

JOBS = [
    # (model, ctx, label_ctx, ctrl_id, control run_id, sample prefix)
    ("M07", "R05", "C05", "CTRL-M07-C05", "CTRL-M07-C05", "M07-F0-W14-W5X3-RETRY"),
    ("M04", "R05", "C02", "CTRL-M04-C02", "CTRL-M04-C02", "M04-F0-W12-W5X3-RETRY"),
]


def main():
    for model, ctx, lbl, ctrl_id, ctrl_run, prefix in JOBS:
        # load the ORIGINAL control manifest to get the frozen N / decoy / asid
        orig_ctrl = orig_manifest(ctrl_id)
        n_orig = int((orig_ctrl.get("eligible_summary") or {}).get(
            "eligible_total", 0) or 0)
        m04_decoy = orig_ctrl.get("m04_decoy", 0) or 0
        print("=== %s-%s original control N=%d decoy=%s ===" %
              (model, ctx, n_orig, hex(m04_decoy)))

        # re-run the control under the NEW binary (matched timeline)
        ctrl = R.prescan(model, ctx, run_id=ctrl_run, label_ctx=lbl,
                         log=print, m04_decoy=m04_decoy)
        n = int((ctrl.get("eligible_summary") or {}).get("eligible_total", 0)
                or 0)
        print("CONTROL %s-%s NEW N=%d (orig %d) act=%s" %
              (model, ctx, n, n_orig, ctrl.get("activation_count")))
        if n < 3:
            print("N<3, skipping fault runs for %s-%s" % (model, ctx))
            continue
        for tid_t in ("T01", "T02", "T03"):
            num, den = {"T01": (1, 10), "T02": (1, 2), "T03": (9, 10)}[tid_t]
            ordinal = (num * n + den - 1) // den
            run_id = "%s-%s" % (prefix, tid_t)
            info = R.execute(run_id, model, ctx, ordinal, False,
                             ctrl.get("asid"), ctrl.get("old_pfn"), print,
                             label_ctx=lbl, m04_decoy=m04_decoy)
            print("FAULT %s-%s rc=%s act=%s elapsed=%ss" %
                  (model, tid_t, info.get("returncode"),
                   info.get("activation_count"), info.get("elapsed_sec")))


if __name__ == "__main__":
    main()