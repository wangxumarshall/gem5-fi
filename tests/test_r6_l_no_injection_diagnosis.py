"""R6-L NO_INJECTION diagnosis (read-only, real evidence)."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import r6_l_no_injection_diagnosis as D  # noqa: E402

RUNS = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/runs")


def test_first_fire_matches_trigger_lcg():
    assert D.first_fire("F1", 1) == 1256412
    assert D.first_fire("F1", 2) == 1049417
    assert D.first_fire("F1", 3) == 1290806
    assert D.first_fire("F2", 1) == 106412
    assert D.first_fire("F4", 3) == 140806


def test_f1_w5_seed1_is_supply_gap():
    if not (RUNS / "L01-F1-W5_s1").is_dir():
        return  # evidence root not present in this checkout
    r = D.diagnose_seed("L01-F1-W5", 1, str(RUNS))
    assert r["tier"] == "F1"
    assert r["attempted"] == 2572 and r["eligible"] == 1262
    assert r["injected"] == 0
    assert r["first_fire"] == 1256412
    assert r["gap"] == 1256412 - 1262
    assert r["routing_ok"] is True
    assert r["conclusion"] == "workload-supply-insufficient"


def test_f0_seed3_uses_draw_alarm():
    if not (RUNS / "L03-F0-W5_s3").is_dir():
        return
    r = D.diagnose_seed("L03-F0-W5", 3, str(RUNS))
    assert r["tier"] == "F0"
    assert r["draw_next_fire"] == 561
    assert r["eligible"] == 540
    assert r["gap"] == 21
    assert r["conclusion"] == "workload-supply-insufficient"


def test_all_current_zeros_are_supply_gaps():
    if not RUNS.is_dir():
        return
    rows = [D.diagnose_seed(rid, seed, str(RUNS))
            for rid, seed in D.discover_runs(str(RUNS))]
    zeros = [r for r in rows if r.get("injected") == 0]
    assert len(zeros) == 25
    assert all(r["conclusion"] == "workload-supply-insufficient" for r in zeros)
