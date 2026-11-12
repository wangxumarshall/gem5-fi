#!/usr/bin/env python3
"""Tests for tools/lsu_v333_workbook.py (LSU v3.3.3, Agent J).

The scaffold path is exercised with deliberately absent run/mapping/control/
causal inputs: the workbook must still be structurally valid and every
measured field must read PENDING (never fabricated, never PASS).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parents[1]
MATRIX = (ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
          / "60_SAMPLE_MATRIX.csv")
V327 = (ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
        / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx")
V332 = ROOT / "audit_v3_3_2"

sys.path.insert(0, str(ROOT / "tools"))
import lsu_v333_workbook as wbmod  # noqa: E402

pytestmark = pytest.mark.skipif(
    not MATRIX.exists() or not V327.exists(),
    reason="authoritative matrix/workbook absent")

SHEETS = ("Model_Design", "Fault_Sample_Manifest", "Control_Manifest",
          "ROI_Context_Mapping", "Causal_Propagation", "Workload_Oracle",
          "Binary_Config", "Readiness_Gate")


def frozen_matrix():
    with MATRIX.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def scaffold(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("workbook_scaffold")
    out = tmp / "v333.xlsx"
    rc = wbmod.main([
        "--runs", str(tmp / "no_runs"),
        "--mapping", str(tmp / "no_mapping.csv"),
        "--controls", str(tmp / "no_controls.csv"),
        "--causal", str(tmp / "no_causal.csv"),
        "--out", str(out),
    ])
    assert rc == 0
    return openpyxl.load_workbook(out, data_only=True)


def sheet_rows(ws, width=None):
    rows = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        if not values or not values[0]:
            continue
        if width is not None:
            values = values[:width]
        rows.append(values)
    return rows


def header(ws):
    return [c.value for c in ws[1]]


def test_eight_sheets(scaffold):
    assert tuple(scaffold.sheetnames) == SHEETS


def test_fault_manifest_preserves_60_frozen_identities(scaffold):
    ws = scaffold["Fault_Sample_Manifest"]
    rows = sheet_rows(ws, width=8)
    assert len(rows) == 60
    ids = [r[0] for r in rows]
    assert len(set(ids)) == 60
    seeds = [str(r[3]) for r in rows]
    assert all(s and s != "None" for s in seeds)
    frozen = frozen_matrix()
    assert ids == [r["SampleRunID"] for r in frozen]
    assert seeds == [r["Seed"] for r in frozen]
    # design ordinal is frozen 1-5; executed is measured separately
    assert all(str(r[6]) in ("1", "2", "3", "4", "5") for r in rows)
    assert all(r[7] == "PENDING" for r in rows)


def test_a03_seeds_are_populated(scaffold):
    ws = scaffold["Fault_Sample_Manifest"]
    h = header(ws)
    model_i = h.index("FaultModelID")
    seed_i = h.index("Seed")
    a03 = [r for r in sheet_rows(ws) if r[model_i] == "A03"]
    assert len(a03) == 5
    assert [str(r[seed_i]) for r in a03] == [
        "663646247", "1626885462", "110775855", "2766846323", "1156093484"]
    assert all(str(r[seed_i]).strip() for r in a03)


def test_candidate_workload_identity_status(scaffold):
    ws = scaffold["Fault_Sample_Manifest"]
    h = header(ws)
    mi, si = h.index("FaultModelID"), h.index("WorkloadIdentityStatus")
    rows = sheet_rows(ws)
    candidates = {"FW02", "RP01", "MD04", "SQ01", "SQ03", "SP05"}
    n_cand = sum(1 for r in rows if r[mi] in candidates
                 and r[si] == "OVERRIDE_APPROVED")
    n_formal = sum(1 for r in rows if r[mi] not in candidates
                   and r[si] == "FORMAL")
    assert n_cand == 30
    assert n_formal == 30
    # the candidate rows carry the approved workload golden, not the old one
    oi = h.index("Oracle")
    osi = h.index("OracleSource")
    expected = {"FW02": "1f4cbf14327717df", "RP01": "0xf3b1c554273d23f7",
                "MD04": "0x22be5ae3364d0c9f", "SQ01": "7df5034c23f3e703",
                "SQ03": "7df5034c23f3e703", "SP05": "7df5034c23f3e703"}
    for r in rows:
        if r[mi] in candidates:
            assert r[oi] == expected[r[mi]], r
            assert "candidate" in str(r[osi])


def test_gem5_and_workload_hashes_are_separate(scaffold):
    ws = scaffold["Fault_Sample_Manifest"]
    h = header(ws)
    gi = h.index("Gem5BinarySHA256")
    wi = h.index("WorkloadELF_SHA256")
    rows = sheet_rows(ws)
    gem5 = {r[gi] for r in rows}
    workloads = {r[wi] for r in rows}
    # v3.3.3 trace-closure re-freeze: the workbook reads the live binary.
    assert gem5 == {"62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd"}
    assert len(workloads) > 1
    assert not (gem5 & workloads)


def test_workload_oracle_candidates_and_goldens(scaffold):
    ws = scaffold["Workload_Oracle"]
    h = header(ws)
    rows = [dict(zip(h, r)) for r in sheet_rows(ws)]
    w6 = next(r for r in rows if r.get("WorkloadID") == "W6"
              and r.get("CandidateFor") == "n/a")
    w8 = next(r for r in rows if r.get("WorkloadID") == "W8"
              and r.get("CandidateFor") == "n/a")
    assert w6["Golden"] == "2543a2a60de01795"
    assert w8["Golden"] == "3f89eab79392ce69"
    assert "stale" in str(w6["GoldenColumnConflict"])
    sq = [r for r in rows if r.get("WorkloadName") == "sq_reload_v3212"]
    assert len(sq) == 3
    for r in sq:
        assert r["ELF_SHA256"].startswith("bcab9cc5")
        assert r["Golden"] == "7df5034c23f3e703"
        assert r["WorkloadStatus"] == "OVERRIDE_APPROVED"
    assert {r["CandidateFor"]: r["K_Star"] for r in sq} == {
        "SQ01": "1006", "SQ03": "1009", "SP05": "940"}


def test_scaffold_marks_measured_fields_pending(scaffold):
    ws = scaffold["Fault_Sample_Manifest"]
    h = header(ws)
    for name in ("Executed_EventOrdinal", "TerminalState", "TerminalReason",
                 "TraceCompleteness", "EvidencePath"):
        i = h.index(name)
        assert all(r[i] == "PENDING" for r in sheet_rows(ws)), name
    es = h.index("ExecutionStatus")
    assert all(r[es] == "PENDING" for r in sheet_rows(ws))
    gate = scaffold["Readiness_Gate"]
    gh = header(gate)
    gi = gh.index("ReadyGate")
    assert all(r[gi] != "PASS" for r in sheet_rows(gate))


def test_no_blank_critical_field_marked_pass(scaffold):
    # Fault_Sample_Manifest
    ws = scaffold["Fault_Sample_Manifest"]
    h = header(ws)
    status = h.index("ExecutionStatus")
    critical = [h.index(c) for c in
                ("TerminalState", "TerminalReason", "TraceCompleteness",
                 "EvidencePath")]
    for r in sheet_rows(ws):
        if r[status] in ("PASS", "YES"):
            assert all(r[i] not in (None, "", "PENDING", "n/a")
                       for i in critical), r
    # Readiness_Gate
    gate = scaffold["Readiness_Gate"]
    gh = header(gate)
    gi = gh.index("ReadyGate")
    gc = [gh.index(c) for c in
          ("FaultInjected", "ControlClean", "TerminalEvidence",
           "TraceComplete", "ProvenanceOK")]
    for r in sheet_rows(gate):
        if r[gi] == "PASS":
            assert all(r[i] not in (None, "", "PENDING", "n/a") for i in gc), r


def test_control_and_causal_sheets_are_scaffolded(scaffold):
    for name in ("Control_Manifest", "Causal_Propagation",
                 "ROI_Context_Mapping"):
        ws = scaffold[name]
        model_col = 1 if name == "Control_Manifest" else 0
        rows = [r for r in sheet_rows(ws) if r[model_col] in wbmod.MODELS]
        assert len(rows) == 60, name


def test_refuses_to_overwrite_frozen_workbook(tmp_path):
    with pytest.raises(SystemExit):
        wbmod.main(["--out", str(V327)])


@pytest.mark.skipif(not (V332 / "propagation").is_dir(),
                    reason="v3.3.2 artifacts absent")
def test_populated_build_keeps_authoritative_ids(tmp_path):
    causal = (V332 / "propagation"
              / "LSU_60Context_Causal_Propagation_Final.csv")
    controls = (V332 / "controls" / "LSU_Fault_Control_Pair_Final.csv")
    mapping = (V332 / "roi" / "LSU_60Context_ROI_Percentile_Mapping.csv")
    runs = V332 / "runs"
    if not (causal.exists() and controls.exists() and mapping.exists()
            and runs.is_dir()):
        pytest.skip("v3.3.2 causal/control/mapping artifacts incomplete")
    out = tmp_path / "populated.xlsx"
    assert wbmod.main([
        "--runs", str(runs), "--mapping", str(mapping),
        "--controls", str(controls), "--causal", str(causal),
        "--out", str(out),
    ]) == 0
    wb = openpyxl.load_workbook(out, data_only=True)
    ws = wb["Fault_Sample_Manifest"]
    h = header(ws)
    rows = sheet_rows(ws)
    ids = [r[h.index("SampleRunID")] for r in rows]
    frozen = [r["SampleRunID"] for r in frozen_matrix()]
    assert ids == frozen                      # never replaced by V332-* ids
    executed = [r[h.index("Executed_EventOrdinal")] for r in rows]
    assert all(str(x).isdigit() for x in executed)
    status = [r[h.index("ExecutionStatus")] for r in rows]
    assert all(x != "PASS" for x in status)
    roi = wb["ROI_Context_Mapping"]
    rh = header(roi)
    source = [r[rh.index("SourceSampleRunID")] for r in sheet_rows(roi)]
    assert all(str(x).startswith("V332-") for x in source)
