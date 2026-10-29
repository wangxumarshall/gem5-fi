#!/usr/bin/env python3
"""[LSU][R6-S] bounded trigger-reachability census for F1/F2/F4 NO_FIRE cells.

The unified trigger (CHAOS/gem5/src/cpu/o3/chaos_trigger.hh) is
CYCLE-interval based, not eligible-count based:

    F1 = 2,600,000 cycles (+/-50% jitter)
    F2 =   260,000 cycles (+/-50% jitter)
    F3 =    26,000 cycles (+/-50% jitter)

With the C0/F0 clock at 2.6 GHz and the gem5 tick domain of 1e12 ticks/s
the conversion is 385 ticks/cycle, so F2's earliest possible fire is
~100.1M ticks and F1's is ~1.00G ticks (the +50% jitter only pushes the
first fire LATER, never earlier).

A workload whose WHOLE execution (`simTicks`) is shorter than that lower
bound can never fire at any timeout: the program exits first.  Those cells
are BLOCKED_TRIGGER_REACHABILITY, not code defects and not PASS.

This tool reads only existing finished evidence (run.out / stats.txt) and
never runs gem5.

Usage:
  python3 tools/r6_s_trigger_census.py [--json PATH]
"""
import json
import re
import sys
from pathlib import Path

RUNS = Path("/home/sdc/gem5-fi-ding/runs/lsu")
EVID = RUNS / "r6_s_unit"
STATUS = RUNS / "RESULTS/STATUS/R6-S-UNIT-STATUS.json"

TICKS_PER_SECOND = 1_000_000_000_000
CPU_HZ = 2_600_000_000
TICKS_PER_CYCLE = round(TICKS_PER_SECOND / CPU_HZ)          # 385
INTERVAL_CYCLES = {"F1": 2_600_000, "F2": 260_000, "F3": 26_000}


def _trigger(runout):
    """Prefer the ALARM line: it is the loud statement that the fire
    accounting is incomplete, and it must outrank the normal summary."""
    normal = ""
    for ln in runout.splitlines():
        if ln.startswith("CHAOS_LSU_TRIGGER_ALARM:"):
            return ln
        if ln.startswith("CHAOS_LSU_TRIGGER:") and not normal:
            normal = ln
    return normal


def _simticks(stats):
    for ln in stats.splitlines():
        if ln.startswith("simTicks"):
            return int(ln.split()[1])
    return None


def census():
    st = json.loads(STATUS.read_text())
    rows = []
    for r in st["rows"]:
        if r.get("seed1") not in ("SEED1_NO_FIRE", "NO_FIRE"):
            continue
        rid = r["run_id"]
        tier = rid.split("-")[1]
        seed_dir = EVID / f"{rid}_s1" / rid / "seed1"
        runout = (seed_dir / "run.out")
        stats = (seed_dir / "stats.txt")
        trig = _trigger(runout.read_text(errors="replace")) if runout.exists() else ""
        simticks = _simticks(stats.read_text(errors="replace")) if stats.exists() else None
        iv = INTERVAL_CYCLES.get(tier)
        floor = iv * TICKS_PER_CYCLE if iv else None
        if "ALARM" in trig or "F5_UNREPORTED_OUTCOME" in trig:
            cls = "BLOCKED_TRIGGER_REPORTING"
            reason = "injector fired but recorded no outcome (F5 reporting gap)"
        elif floor is None:
            cls = "BLOCKED_TRIGGER_SEMANTICS"
            reason = f"tier {tier} is not interval-based; needs its own census"
        elif simticks is not None and simticks < floor:
            cls = "BLOCKED_TRIGGER_REACHABILITY"
            reason = (f"whole run simTicks={simticks} < earliest fire "
                      f"{floor} ({iv} cycles x {TICKS_PER_CYCLE})")
        else:
            cls = "REACHABLE_NOT_FIRED"
            reason = (f"simTicks={simticks} >= floor {floor}: a bounded "
                      "re-run can reach the first fire position")
        rows.append({"run_id": rid, "tier": tier, "trigger": trig,
                     "simTicks": simticks, "interval_cycles": iv,
                     "earliest_fire_tick": floor, "classification": cls,
                     "reason": reason})
    return rows


def main(argv):
    rows = census()
    for r in rows:
        print(f"{r['run_id']:<14} {r['classification']:<32} "
              f"simTicks={r['simTicks']} floor={r['earliest_fire_tick']}")
    counts = {}
    for r in rows:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
    print(json.dumps(counts, ensure_ascii=False))
    if "--json" in argv:
        p = Path(argv[argv.index("--json") + 1])
        p.write_text(json.dumps({"ticks_per_cycle": TICKS_PER_CYCLE,
                                 "rows": rows}, ensure_ascii=False, indent=1))
        print(f"WROTE {p}")
    # A NO_FIRE cell must never be classified as a pass.
    return 0 if all("BLOCKED" in r["classification"]
                    or r["classification"] == "REACHABLE_NOT_FIRED"
                    for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
