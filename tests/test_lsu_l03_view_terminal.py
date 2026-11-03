"""R6-L terminal shapes on real L evidence (skips when evidence is absent).

* L03 violation-view -> real errant_commit: `full` at L5 (silent SDC escape).
* L03 violation-view -> real squash_discarded: `detected_contained` (L4).
* L01 translation fault -> squash_discarded: `detected_contained` (L4).
"""
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools"))

import lsu_chain_check as C  # noqa: E402
import lsu_prop_fields as PF  # noqa: E402

RUNS = Path("/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/runs_repeat_20261103")


def _events(rel):
    p = RUNS / rel / "prop_evt.txt.gz"
    if not p.is_file():
        pytest.skip(f"evidence absent: {p}")
    ev, _tr, _s, _i = PF.read_stream(str(p))
    return ev


def _admit(ev, rid):
    act = sum(1 for e in ev
              if e.get("kind") == "inj"
              and str(e.get("fault_id", "")) not in ("", "0"))
    cont = C.containment_from_events(ev, rid)
    return C.check_admission({
        "run_id": rid, "activated": act, "events": ev, "rc": 0,
        "oracle_outcome": "Masked", "containment": cont,
        "crash_exit": None, "summary_issues": [],
        "consumer_summary_accounting": {"conservation": "n/a"}})


def test_l03_view_errant_commit_is_full_escape():
    ev = _events("L03-F4-W12_s1/L03-F4-W12/seed1")
    v = C.check_chain(ev, oracle_outcome="Masked")
    fulls = [f for f in v["faults"].values() if f["terminal"] == "full"]
    assert fulls, {k: f["terminal"] for k, f in v["faults"].items()}
    assert any(f["provable_to"] == "L5" for f in fulls)
    r = _admit(ev, "L03-F4-W12")
    assert r["admitted"] is True, r["violations"]
    assert r["terminal"] == "full"


def test_l03_view_squash_is_contained():
    ev = _events("L03-F4-W12_s3/L03-F4-W12/seed3")
    v = C.check_chain(ev, oracle_outcome="Masked")
    assert any(f["terminal"] == "detected_contained"
               for f in v["faults"].values())
    r = _admit(ev, "L03-F4-W12")
    assert r["admitted"] is True, r["violations"]
    assert r["terminal"] == "detected_contained"


def test_l01_translation_squash_is_contained():
    ev = _events("L01-F2-W5_s2/L01-F2-W5/seed2")
    v = C.check_chain(ev, oracle_outcome="Masked")
    assert any(f["terminal"] == "detected_contained"
               for f in v["faults"].values())
    r = _admit(ev, "L01-F2-W5")
    assert r["admitted"] is True, r["violations"]
    assert r["terminal"] == "detected_contained"
