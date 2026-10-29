#!/usr/bin/env python3
"""[LSU][R6-S] F1/F2/F4 NO_FIRE cells are bounded-budget unreachable, not PASS.

The unified trigger is cycle-interval based (F1=2.6M cycles, F2=260K,
F3=26K; 385 ticks/cycle at 2.6 GHz).  A workload that exits before the
earliest fire tick can never fire at any timeout.  This test pins the
census to the real evidence and forbids classifying any NO_FIRE cell as
a pass.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tools"))

import r6_s_trigger_census as C  # noqa: E402


def test_census_covers_all_20_no_fire_cells():
    rows = C.census()
    assert len(rows) == 20, len(rows)


def test_every_no_fire_cell_is_blocked_never_pass():
    for r in C.census():
        assert r["classification"].startswith("BLOCKED_"), r
        assert "PASS" not in r["classification"], r


def test_interval_floors_are_cycle_derived():
    assert C.TICKS_PER_CYCLE == 385
    rows = {r["run_id"]: r for r in C.census()}
    assert rows["S04-F2-W0"]["earliest_fire_tick"] == 260_000 * 385
    assert rows["S13-F1-W5"]["earliest_fire_tick"] == 2_600_000 * 385


def test_short_runs_are_reachability_blocked():
    rows = {r["run_id"]: r for r in C.census()}
    for rid in ("S04-F2-W0", "S06-F2-W6", "S13-F2-W12", "S13-F1-W12"):
        assert rows[rid]["classification"] == "BLOCKED_TRIGGER_REACHABILITY", rid
        assert rows[rid]["simTicks"] < rows[rid]["earliest_fire_tick"], rid


def test_f5_reporting_gap_is_named():
    rows = {r["run_id"]: r for r in C.census()}
    for rid in ("S10-F5-W5", "S10-F5-W9"):
        assert rows[rid]["classification"] == "BLOCKED_TRIGGER_REPORTING", rid
        assert "F5_UNREPORTED_OUTCOME" in rows[rid]["trigger"], rid


def test_f4_has_no_interval_mapping():
    rows = {r["run_id"]: r for r in C.census()}
    for rid in ("S07-F4-W5", "S11-F4-W5", "S11-F4-W6"):
        assert rows[rid]["classification"] == "BLOCKED_TRIGGER_SEMANTICS", rid


def test_fired_sisters_confirm_the_interval_model():
    """S13-F1-W1 / S13-F2-W1 did fire, and only after the floor — the
    interval model is not an excuse, it is the measured behaviour."""
    base = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit")
    for rid, floor in (("S13-F1-W1", 2_600_000 * 385),
                       ("S13-F2-W1", 260_000 * 385)):
        runout = base / f"{rid}_s1" / rid / "seed1" / "run.out"
        text = runout.read_text(errors="replace")
        inj_ticks = [int(x) for x in __import__("re").findall(
            r"Tick: (\d+), Site:", (base / f"{rid}_s1" / rid / "seed1" /
                                    "addrpath_injections.log").read_text())]
        assert inj_ticks and inj_ticks[0] > floor, (rid, inj_ticks, floor)
        assert "injected=1" in text, rid


if __name__ == "__main__":
    import pytest
    rc = pytest.main([str(Path(__file__)), "-q", "-p", "no:cacheprovider"])
    print("R6 S TRIGGER CENSUS TEST:",
          "ALL PASSED" if rc == 0 else "FAILURES")
    sys.exit(rc)
