#!/usr/bin/env python3
"""Generate the 40-sample pilot queue for the F1 closure round.

All runs are TEST IDs only.  Each pilot points at an independent no-fault
control produced on the same final binary + checkpoint.  Nothing here is a
formal SampleRunID.

Usage: python3 phase3/final/gen_pilots.py [--asids phase3/final/w9_asids.json]
"""
import argparse
import json
import os

WS = "/home/sdc/gem5-fi-mmu-impl-v2"
RUNNER = "python3 tools/mmu_formal_runner.py"


def ctrl(run, kind="golden_output.txt"):
    return "runs/%s/Run_Log/%s" % (run, kind)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--asids", default="phase3/final/w9_asids.json")
    ap.add_argument("--out", default="phase3/final/f1_pilots.json")
    a = ap.parse_args()
    asids = json.load(open(os.path.join(WS, a.asids)))
    jobs = []

    def add(model, ctx, workload, target, extra="", mode=None,
            control=None):
        rid = "TEST-F1-%s-%s" % (model, ctx)
        cmd = [RUNNER, "--pilot", rid, "--model", model,
               "--workload", workload, "--context", ctx,
               "--target", str(target), "--eligible-event-index", "1"]
        if mode:
            cmd += ["--target-mode", mode]
        if control:
            cmd += ["--control-run", control]
        if extra:
            cmd += extra.split()
        jobs.append({
            "id": rid,
            "cmd": ["bash", "-lc", "cd %s && %s" % (WS, " ".join(cmd))],
            "log": "%s/phase3/final/logs/%s.log" % (WS, rid),
            "timeout": 5400,
        })

    # M01 (W9, target = ASID; control carries all five context lines)
    for ctx in ("R01", "R02", "R03", "R04", "R05"):
        add("M01", ctx, "W9", asids[ctx],
            control=ctrl("TEST-F1-CTRL-W9"))

    for m, wl, targets, mode in (
            ("M02", "W10", ["0x4001000000", "0x4001100000", "0x4001200000",
                            "0x4001300000", "0x4001400000"], "Read"),
            ("M06", "W10", ["0x4001000000", "0x4001100000", "0x4001200000",
                            "0x4001300000", "0x4001400000"], "Read"),
            ("M08", "W10", ["0x4001000000", "0x4001100000", "0x4001200000",
                            "0x4001300000", "0x4001400000"], "Read")):
        for i, va in enumerate(targets):
            ctx = "R%02d" % (i + 1)
            c = ctrl("TEST-F1-CTRL-W10-%s" % ctx)
            md = mode
            if m == "M06" and ctx == "R02":
                c = ctrl("TEST-F1-CTRL-W10S-COLD", "board.terminal")
                md = "Write"
            if m == "M08" and ctx == "R05":
                c = ctrl("TEST-F1-CTRL-W10S-WARM", "board.terminal")
                md = "Write"
            add(m, ctx, wl, va, mode=md, control=c)

    for i in range(5):
        ctx = "R%02d" % (i + 1)
        va = "0x4005000000" if ctx == "R05" else "0x4004000000"
        md = "Execute" if ctx == "R05" else "Read"
        add("M03", ctx, "W11", va, mode=md,
            control=ctrl("TEST-F1-CTRL-W11-%s" % ctx))
        add("M04", ctx, "W12", "0x4008000000",
            mode="Execute" if ctx == "R05" else "Read",
            control=ctrl("TEST-F1-CTRL-W12-%s" % ctx))
        add("M05", ctx, "W13", "0x4010000000",
            extra="--extra-gem5-arg=--mmu_m05_decoy_va "
                  "--extra-gem5-arg=0x4010200000",
            control=ctrl("TEST-F1-CTRL-W13-%s" % ctx))

    for ctx, va, md in (("R01", "0x400d000000", "Write"),
                        ("R02", "0x400d000000", "Atomic"),
                        ("R03", "0x400d200000", "Read"),
                        ("R04", "0x400d400100", "Execute"),
                        ("R05", "0x400d600180", "Execute")):
        add("M07", ctx, "W14", va, mode=md,
            control=ctrl("TEST-F1-CTRL-W14-%s" % ctx))

    os.makedirs(os.path.join(WS, "phase3/final/logs"), exist_ok=True)
    json.dump(jobs, open(os.path.join(WS, a.out), "w"), indent=1)
    print("%d pilot jobs -> %s" % (len(jobs), a.out))


if __name__ == "__main__":
    main()
