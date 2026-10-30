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
# [R6-S-B2/B3 2026-10-30] F4 IS authoritatively defined (LSU spec: every
# 100,000 eligible events, then 2-4 consecutive pollutions) and is
# EVENT-counted, not cycle-counted. Its first-fire floor is 100,000 eligible
# events; the 3 F4 cells are reachability-blocked, not spec-blocked.
INTERVAL_EVENTS = {"F4": 100_000}

# The census is over the ORIGINAL S-unit NO_FIRE round (frozen evidence in
# runs/lsu/r6_s_unit).  The repair round re-ran some cells and changed their
# current seed status (e.g. S10-F5 from NO_FIRE to CHAIN_INCOMPLETE_S10_MODEL);
# that must NOT erase the historical reachability census.  This list is the
# exact 20-cell original set.
ORIGINAL_NO_FIRE = {
 "S01-F1-W5","S01-F2-W5","S02-F2-W5","S04-F2-W0","S04-F2-W5",
 "S05-F2-W3","S05-F2-W5","S06-F2-W5","S06-F2-W6","S07-F4-W5",
 "S08-F2-W5","S09-F2-W5","S10-F5-W5","S10-F5-W9","S11-F4-W5",
 "S11-F4-W6","S13-F1-W12","S13-F1-W5","S13-F2-W12","S13-F2-W5",
}


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


def _field(line, key):
    m = re.search(rf" {key}=(\S+)", line or "")
    if not m or m.group(1) in ("n/a", ""):
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return m.group(1)


def _log_lines(seed_dir):
    p = seed_dir / "lsq_fwd_injections.log"
    if not p.exists():
        return None
    return len([ln for ln in p.read_text(errors="replace").splitlines()
                if "faults_injected:" in ln])


def _stats_injected(seed_dir):
    p = seed_dir / "stats.txt"
    if not p.exists():
        return None
    for ln in p.read_text(errors="replace").splitlines():
        if ".numFaultsInjected" in ln:
            parts = ln.split()
            if len(parts) >= 2:
                try:
                    return int(parts[1])
                except ValueError:
                    return None
    return None


def census():
    st = json.loads(STATUS.read_text())
    rows = []
    for r in st["rows"]:
        if (r["run_id"] not in ORIGINAL_NO_FIRE
                and r.get("seed1") not in ("SEED1_NO_FIRE", "NO_FIRE")):
            continue
        rid = r["run_id"]
        tier = rid.split("-")[1]
        seed_dir = EVID / f"{rid}_s1" / rid / "seed1"
        runout = (seed_dir / "run.out")
        stats = (seed_dir / "stats.txt")
        trig = _trigger(runout.read_text(errors="replace")) if runout.exists() else ""
        simticks = _simticks(stats.read_text(errors="replace")) if stats.exists() else None
        eligible_total = _field(trig, "eligible")
        iv = INTERVAL_CYCLES.get(tier)
        floor_tick = iv * TICKS_PER_CYCLE if iv else None
        floor_events = INTERVAL_EVENTS.get(tier)

        row = {"run_id": rid, "tier": tier, "trigger": trig,
               "simTicks": simticks, "eligible_total": eligible_total,
               "interval_cycles": iv, "earliest_fire_tick": floor_tick,
               "earliest_fire_events": floor_events}

        if "F5_UNREPORTED_OUTCOME" in trig:
            inj = _field(trig, "injected")
            fires = _field(trig, "fires")
            outcomes = _field(trig, "outcomes_recorded")
            logn = _log_lines(seed_dir)
            statsn = _stats_injected(seed_dir)
            contradiction = bool(
                (logn is not None and inj is not None and logn != inj)
                or (logn is not None and statsn is not None
                    and logn != statsn))
            row.update({
                "classification": "BLOCKED_TRIGGER_REPORTING",
                "fires": fires, "outcomes_recorded": outcomes,
                "injected": inj, "log_lines": logn,
                "stats_numFaultsInjected": statsn,
                "count_contradiction": contradiction,
                "reason": ("injector fired but recorded no outcome "
                           f"(fires={fires} outcomes_recorded={outcomes} "
                           f"injected={inj}); three-way counts "
                           f"trigger/log/stats = {inj}/{logn}/{statsn}"),
                "unblock_condition": ("fix the injector's F5 outcome "
                                      "reporting and re-run this seed; the "
                                      "trigger/log/stats counts must agree "
                                      "(fires == injected + no_effect)"),
            })
            rows.append(row)
            continue

        if floor_tick is not None:
            if simticks is not None and simticks < floor_tick:
                cls = "BLOCKED_TRIGGER_REACHABILITY"
                reason = (f"whole run simTicks={simticks} < earliest fire "
                          f"{floor_tick} ({iv} cycles x {TICKS_PER_CYCLE}); "
                          "the program exits before the first fire")
                unblock = ("requires a workload whose WHOLE run lasts at "
                           f"least {floor_tick} simTicks, or an authoritative "
                           "tier re-assignment; no wall timeout can reach a "
                           "fire position the program never reaches")
            else:
                cls = "REACHABLE_NOT_FIRED"
                reason = (f"simTicks={simticks} >= floor {floor_tick}: a "
                          "bounded re-run can reach the first fire position")
                unblock = "bounded re-run with the SAME seed and budget"
            row.update({"classification": cls, "reason": reason,
                        "unblock_condition": unblock,
                        "count_contradiction": False})
            rows.append(row)
            continue

        if floor_events is not None:
            if (isinstance(eligible_total, int)
                    and eligible_total < floor_events):
                cls = "BLOCKED_TRIGGER_REACHABILITY"
                reason = (f"whole run eligible={eligible_total} < F4 first-"
                          f"fire floor {floor_events} eligible events "
                          "(authoritative: every 100,000 eligible events, "
                          "then 2-4 consecutive pollutions)")
                unblock = ("requires a workload with at least "
                           f"{floor_events} eligible events in its whole "
                           "run, or an authoritative tier re-assignment; "
                           "seed hunting is forbidden")
            else:
                cls = "REACHABLE_NOT_FIRED"
                reason = (f"eligible={eligible_total} >= floor "
                          f"{floor_events}: a bounded re-run can reach the "
                          "first fire position")
                unblock = "bounded re-run with the SAME seed and budget"
            row.update({"classification": cls, "reason": reason,
                        "unblock_condition": unblock,
                        "count_contradiction": False})
            rows.append(row)
            continue

        row.update({
            "classification": "BLOCKED_TRIGGER_SEMANTICS",
            "reason": (f"tier {tier} has no authoritative interval/frequency "
                       "definition in the LSU spec; it cannot be run"),
            "unblock_condition": ("requires an authoritative specification "
                                  "of this tier's cycle/event interval before "
                                  "any run; inventing a frequency is forbidden"),
            "count_contradiction": False,
        })
        rows.append(row)
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
