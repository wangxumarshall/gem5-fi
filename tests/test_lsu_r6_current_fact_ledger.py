#!/usr/bin/env python3
"""[R6-PROPAGATION-V3] Ledger current-fact overlay for the 11 runnable T cells.

Pins the generator (not just the generated JSON):
  * T05/T06/T07 W4 + T10 W4 lose the stale FS-INFRA residual and are
    RUNNABLE_EVIDENCE_PENDING.
  * T08-F0/F4-W4 are PARTIAL_SUBMODEL_PROVEN (T08-a canary only).
  * T08-*-W9 stay BLOCKED_WORKLOAD_GAP.
  * W11 stays BLOCKED_SPEC.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import lsu_runid_map as rm  # noqa: E402
import lsu_coverage_matrix as cm  # noqa: E402
import lsu_ready_contract as rc  # noqa: E402

XLSX = os.path.join(ROOT, "docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.xlsx")

RUNNABLE = [
    "T05-F0-W4", "T05-F2-W4", "T06-F0-W4", "T06-F2-W4",
    "T07-F0-W4", "T07-F4-W4",
    "T10-F0-W4", "T10-F1-W4", "T10-F2-W4",
]
T08_W4 = ["T08-F0-W4", "T08-F4-W4"]
T08_W9 = ["T08-F0-W9", "T08-F4-W9", "T08-F6-W9"]


def _map():
    return rm.generate_map(XLSX)


def _by(m):
    return {e["run_id"]: e for e in m["entries"]}


def test_runnable_cells_have_no_stale_fs_infra():
    by = _by(_map())
    for rid in RUNNABLE:
        e = by[rid]
        assert e["status"] == "PARTIAL", rid
        assert e["status_reasons"] == [], (rid, e["status_reasons"])
        assert e["capability_status"] == "RUNNABLE_EVIDENCE_PENDING", rid
        assert "fs-infra" not in json.dumps(e, ensure_ascii=False), rid


def test_t08_w4_is_partial_submodel():
    by = _by(_map())
    for rid in T08_W4:
        e = by[rid]
        assert e["status"] == "PARTIAL", rid
        assert e["status_reasons"] == [], rid
        assert e["capability_status"] == "PARTIAL_SUBMODEL_PROVEN", rid
        assert "T08-b" in e["capability_note"] and "T08-a" in e["capability_note"]


def test_t08_w9_is_workload_gap():
    by = _by(_map())
    for rid in T08_W9:
        e = by[rid]
        assert e["status"] == "BLOCKED", rid
        joined = " ".join(e["status_reasons"])
        assert joined.startswith("workload:BLOCKED_WORKLOAD_GAP"), rid
        assert "GAP/Graph500" in joined
        assert "tlb_probe" in joined  # explains why it must NOT be used


def test_w11_is_blocked_spec():
    by = _by(_map())
    e = by["T10-F0-W11"]
    assert e["status"] == "BLOCKED"
    assert e["status_reasons"] == [
        "BLOCKED_SPEC: SPEC CPU2017 needs a license"]


def test_coverage_pass_for_runnable_and_t08_w4():
    m = _map()
    ev = cm.load_evidence(os.path.join(
        ROOT, "docs/gem5-fi/lsu/mdspec/pilot_evidence.json"))
    by = _by(m)
    for rid in RUNNABLE + T08_W4:
        st, why = cm.assess(by[rid], ev)
        assert st == "PASS", (rid, st, why)
    for rid in T08_W9:
        st, _why = cm.assess(by[rid], ev)
        assert st == "BLOCKED", rid


def test_ready_classifier_labels():
    entry = {"status_reasons": ["workload:BLOCKED_WORKLOAD_GAP: x"],
             "capability_status": "BLOCKED_WORKLOAD_GAP"}
    assert rc._classify(entry, "PASS", None)[:2] == ("BLOCKED", "WORKLOAD-GAP")
    entry = {"status_reasons": [], "capability_status":
             "PARTIAL_SUBMODEL_PROVEN", "capability_note": "partial"}
    assert rc._classify(entry, "PASS", ["flag"])[:2] == (
        "PARTIAL", "PARTIAL-SUBMODEL")
    entry = {"status_reasons": ["BLOCKED_SPEC: SPEC CPU2017 needs a license"]}
    assert rc._classify(entry, "PASS", None)[:2] == ("BLOCKED", "LICENSE")
