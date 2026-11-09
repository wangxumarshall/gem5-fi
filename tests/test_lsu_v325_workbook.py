"""v3.2.5 workbook: only LQ04 may change; identities and the other 11 models stay.

Covers sheets ``3.最终12模型矩阵`` / ``4.源码Hook审计`` /
``5.60个样本执行矩阵``, the derived ``60_SAMPLE_MATRIX.csv`` round-trip and
``MODEL_STATUS_MATRIX.csv`` (LQ04 stages only).
"""
import csv

import openpyxl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
V324 = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx"
V325 = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx"
SAMPLE_CSV = EXCEL / "60_SAMPLE_MATRIX.csv"
MATRIX = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv"

SAMPLE_SHEET = "5.60个样本执行矩阵"
MODEL_SHEET = "3.最终12模型矩阵"
HOOK_SHEET = "4.源码Hook审计"
REVISION_SHEET = "18.v3.2.10变更记录"

WORKLOAD = ("/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10"
            "/docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal")
SHA = "fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba"
ORACLE = "b097eb83f71545cb"

IDENTITY_COLS = ["SampleRunID", "RunID", "SubTaskID", "Seed", "FaultModelID"]
LQ04_DEFINITION_COLS = [
    "FaultLocation", "TargetField", "BitEntryByteIndex", "NormalValue",
    "FaultValue", "InjectionMode", "InjectionTiming", "FaultDuration",
    "TargetInstruction", "EligibleEventCondition", "EventOrdinal",
    "FaultConfigID", "ContextDifferenceRule",
]
MATRIX_STAGES = {
    "DESIGNED": 1, "SOURCE_AUDITED": 1, "IMPLEMENTED": 1, "COMPILED": 1,
    "UNIT_TESTED": 1, "PILOT_RUN": 1, "PROPAGATION_VERIFIED": 0,
}
MATRIX_EVIDENCE = ("v3.2.10: literal fields cleared; boundary restore; "
                   "5/5 pilots MASKED; consumers correct data "
                   "(no corrupting propagation); no SDC")
OTHER_MATRIX_ROWS = {
    "A01": ["A01", "AGU", "xv", "1", "1", "1", "1", "1", "1", "0",
            "v3.2.1 pilots; v3.2.4 re-adjudicated (R03 SQUASHED)"],
    "A03": ["A03", "AGU", "xv", "1", "1", "1", "1", "1", "1", "0",
            "v3.2.1 pilots; CRASH x5"],
    "FW02": ["FW02", "FWD", "xv", "1", "1", "1", "1", "1", "1", "0",
             "v3.2.4 R01/R05 SQUASHED; R03/R04 MASKED; R02 CRASH"],
    "SQ01": ["SQ01", "SQ", "store_data", "1", "1", "1", "1", "1", "1", "0",
             "v3.2.4 store_wb+store_mem; no consumer"],
    "DA04": ["DA04", "SQ", "byte_enable", "1", "1", "1", "1", "1", "1", "1",
             "v3.2.6 R04/R05 end-to-end chain with actual PRF hashes: "
             "1,009/7,714 matched consumers, 0 mismatches, SDC"],
    "LP01": ["LP01", "L1D", "load_response", "1", "1", "1", "1", "1", "1", "1",
             "v3.2.6 five pilots: matched consumer edges only, mismatch "
             "diagnostics 45/0/3/0/3; all MASKED (no SDC)"],
    "MD04": ["MD04", "LSU", "LSQ", "1", "1", "1", "1", "1", "1", "1",
             "MD04-DEF-v2 frozen 2026-11-08; checkViolations "
             "store->younger-load M5PanicFault suppression; 5 frozen pilots "
             "(R01/R04/R05 SQUASHED, R02 6 consumers, R03 259 consumers "
             "CROSS_ATTEMPT_VERIFIED); R05 historical ordinal drift; no SDC"],
    "FW05": ["FW05", "FWD", "forward", "1", "1", "1", "1", "1", "1", "1",
             "v3.2.8 fw05_forward frozen/archived; v3.2.9 run_pilot.sh fixed "
             "(GEM5_ROOT/archived bin, /tmp test); strict matched baselines "
             "fw05_older_src/prob0 all PASS; fault-on reproduces R02-R05 SDC "
             "549c...; Excel v3.2.4 consistent"],
    "SQ03": ["SQ03", "SQ", "writeback", "1", "1", "1", "1", "1", "1", "0",
             "v3.2.8 five pilots MASKED (no consumer); v3.2.9 trace analysis "
             "separates permission (140910) from cache update (198275); probe "
             "P00/P01 identical checksums and 136 identical forwards; "
             "PROPAGATION_VERIFIED=0"],
    "SP05": ["SP05", "SQ", "completion", "1", "1", "1", "1", "1", "1", "0",
             "v3.2.9 real completeStore hook (writebackStores premature "
             "completion); one-shot+watchdog; 5 pilots MASKED/PASS, seq "
             "18/19/23/24/28, storesToWB -1, trace COMPLETE, consumer 0; "
             "no SDC"],
    "RP01": ["RP01", "RPL", "replay", "1", "0", "0", "0", "0", "0", "0",
             "v3.2.3 audit"],
}


def _headers(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value}


def _header_list(ws):
    return [str(c.value).strip() if c.value is not None else None
            for c in ws[1]]


def _rows(ws, cols, model):
    return [r for r in range(2, ws.max_row + 1)
            if str(ws.cell(r, cols["FaultModelID"]).value) == model]


def _sample_rows(ws):
    return [r for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value]


def test_exactly_60_rows_and_identities_unchanged():
    a = openpyxl.load_workbook(V324, data_only=True)[SAMPLE_SHEET]
    b = openpyxl.load_workbook(V325, data_only=True)[SAMPLE_SHEET]
    ca, cb = _headers(a), _headers(b)
    rows = _sample_rows(b)
    assert len(rows) == 60
    for r in rows:
        for name in IDENTITY_COLS:
            assert a.cell(r, ca[name]).value == b.cell(r, cb[name]).value, (r, name)


def test_lq04_rows_new_workload_identity_and_status():
    ws = openpyxl.load_workbook(V325, data_only=True)[SAMPLE_SHEET]
    cols = _headers(ws)
    rows = _rows(ws, cols, "LQ04")
    assert len(rows) == 5
    for i, r in enumerate(rows, start=1):
        assert str(ws.cell(r, cols["SampleRunID"]).value) == \
            f"LQ04-F0-W2-S01-R0{i}"
        assert ws.cell(r, cols["WorkloadPath"]).value == WORKLOAD
        assert ws.cell(r, cols["BinaryPath"]).value == WORKLOAD
        assert ws.cell(r, cols["BinarySHA256"]).value == SHA
        assert ws.cell(r, cols["Oracle"]).value == ORACLE
        assert int(ws.cell(r, cols["EventOrdinal"]).value) == i
        cmd = str(ws.cell(r, cols["FullCommand"]).value)
        assert "gem5.opt" in cmd
        assert "configs/se/lsu_proxy.py" in cmd
        assert f"--cmd={WORKLOAD}" in cmd
        assert "--cpu O3" in cmd
        assert "--variant B0" in cmd
        assert "--probability 1.0" in cmd
        assert "--chaos_propagation" in cmd
        assert "--chaos_lq04" in cmd
        assert f"--lq04_event_ordinal {i}" in cmd
        assert "--lq04_max_faults 1" in cmd
        assert "--lq04_watchdog_cycles 500000000" in cmd
        assert ws.cell(r, cols["ExecutionStatus"]).value == "PILOT_RUN"
        assert ws.cell(r, cols["RunStatus"]).value == "PILOT_MASKED"
        assert ws.cell(r, cols["FaultActivationStatus"]).value == "TRIGGERED"
        assert ws.cell(r, cols["TerminalState_v31"]).value == "MASKED"
        assert ws.cell(r, cols["TraceCompleteness_v31"]).value == "COMPLETE"
        assert str(ws.cell(r, cols["EvidencePath"]).value).startswith(
            "runs/lsu/final/LQ04-")
        assert ws.cell(r, cols["DecisionStatus"]).value == \
            "ACCEPTED_BY_RESEARCHER_2026-11-08"
        prov = str(ws.cell(r, cols["v3.2_ConfigProvenance"]).value)
        assert "literal" in prov
        assert "boundary restore" in prov
        assert "ordinal anchors 1-5" in prov
        assert "LIFECYCLE_ONLY" in prov
        assert "PROPAGATION_VERIFIED=0" in prov


def test_lq04_fault_definition_cells_unchanged():
    a = openpyxl.load_workbook(V324, data_only=True)[SAMPLE_SHEET]
    b = openpyxl.load_workbook(V325, data_only=True)[SAMPLE_SHEET]
    ca, cb = _headers(a), _headers(b)
    for r in _rows(b, cb, "LQ04"):
        for name in LQ04_DEFINITION_COLS:
            assert a.cell(r, ca[name]).value == b.cell(r, cb[name]).value, (r, name)


def test_other_models_rows_identical():
    a = openpyxl.load_workbook(V324, data_only=True)[SAMPLE_SHEET]
    b = openpyxl.load_workbook(V325, data_only=True)[SAMPLE_SHEET]
    ca, cb = _headers(a), _headers(b)
    for r in _sample_rows(b):
        if str(b.cell(r, cb["FaultModelID"]).value) == "LQ04":
            continue
        for name in ca:
            if name in cb:
                assert a.cell(r, ca[name]).value == b.cell(r, cb[name]).value, \
                    (r, name)


def test_config_frozen_and_warmup_roi_unchanged():
    a = openpyxl.load_workbook(V324, data_only=True)[SAMPLE_SHEET]
    b = openpyxl.load_workbook(V325, data_only=True)[SAMPLE_SHEET]
    ca, cb = _headers(a), _headers(b)
    for r in _sample_rows(b):
        assert b.cell(r, cb["ConfigFrozen"]).value == "NO"
        for name in ("WarmUp", "ROI"):
            assert a.cell(r, ca[name]).value == b.cell(r, cb[name]).value, (r, name)
            assert b.cell(r, cb[name]).value == "NEEDS_RESEARCHER_CONFIRMATION"


def test_sheet3_lq04_status_and_others_unchanged():
    a = openpyxl.load_workbook(V324, data_only=True)[MODEL_SHEET]
    b = openpyxl.load_workbook(V325, data_only=True)[MODEL_SHEET]
    ca, cb = _headers(a), _headers(b)
    lq = [r for r in range(2, b.max_row + 1)
          if str(b.cell(r, cb["ModelID"]).value) == "LQ04"]
    assert len(lq) == 1
    r = lq[0]
    assert b.cell(r, cb["WorkloadName"]).value == "lq_lifetime_ordinal"
    assert b.cell(r, cb["WorkloadStatus"]).value == "READY"
    assert b.cell(r, cb["ImplementationStatus"]).value == \
        ("PILOT_IMPLEMENTED_VERIFIED_F0 (literal _valid/_request clear; "
         "boundary restore; MASKED 5/5)")
    assert b.cell(r, cb["OverallStatus"]).value == "PILOT_RUN_MASKED_5/5"
    notes = str(b.cell(r, cb["Notes"]).value)
    assert "literal semantics accepted by the researcher 2026-11-08" in notes
    assert "pkt->senderState" in notes
    assert "no response loss" in notes
    assert "MASKED" in notes
    assert "ordinal anchors 1-5" in notes
    assert "PROPAGATION_VERIFIED=0" in notes
    for r2 in range(2, b.max_row + 1):
        if str(b.cell(r2, cb["ModelID"]).value) == "LQ04":
            continue
        for name in ca:
            if name in cb:
                assert a.cell(r2, ca[name]).value == \
                    b.cell(r2, cb[name]).value, (r2, name)


def test_sheet4_lq04_hook_audit_and_others_unchanged():
    a = openpyxl.load_workbook(V324, data_only=True)[HOOK_SHEET]
    b = openpyxl.load_workbook(V325, data_only=True)[HOOK_SHEET]
    ca, cb = _headers(a), _headers(b)
    ha, hb = _header_list(a), _header_list(b)
    lq = [r for r in range(2, b.max_row + 1)
          if str(b.cell(r, cb["ModelID"]).value) == "LQ04"]
    assert len(lq) == 1
    r = lq[0]
    assert b.cell(r, cb["ExistingHook"]).value == "CHAOSLQ04"
    assert b.cell(r, cb["RequiredSourceChange"]).value == \
        ("implemented: CHAOSLQ04 SimObject + LQEntry side channel + "
         "executeLoad hook")
    assert b.cell(r, cb["ImplementationStatus"]).value == "IMPLEMENTED_VERIFIED"
    ev = str(b.cell(r, cb["Evidence"]).value)
    assert "CHAOS/gem5/src/cpu/o3/CHAOSLQ04/" in ev
    assert "lsq_unit.hh side channel" in ev
    assert "pilots_v3_2_10" in ev
    # only the four audited cells may differ, position-wise
    allowed = {"ExistingHook", "RequiredSourceChange", "ImplementationStatus",
               "Evidence"}
    for c in range(1, b.max_column + 1):
        name = hb[c - 1]
        if name is None:
            continue
        if name in allowed:
            continue
        assert a.cell(r, c).value == b.cell(r, c).value, (name,)
    for r2 in range(2, b.max_row + 1):
        if str(b.cell(r2, cb["ModelID"]).value) == "LQ04":
            continue
        for c in range(1, b.max_column + 1):
            assert a.cell(r2, c).value == b.cell(r2, c).value, (r2, c)


def test_revision_sheet_exists():
    wb = openpyxl.load_workbook(V325, data_only=True)
    assert REVISION_SHEET in wb.sheetnames
    ws = wb[REVISION_SHEET]
    text = " ".join(str(c.value) for row in ws.iter_rows() for c in row
                    if c.value is not None)
    assert "LQ04" in text
    assert "MASKED" in text
    assert "PROPAGATION_VERIFIED=0" in text
    assert "LIFECYCLE_ONLY" in text


def test_sample_csv_roundtrip_matches_lq04():
    ws = openpyxl.load_workbook(V325, data_only=True)[SAMPLE_SHEET]
    cols = _headers(ws)
    with SAMPLE_CSV.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 60
    lq = [row for row in rows if row["FaultModelID"] == "LQ04"]
    assert len(lq) == 5
    for row in lq:
        assert row["WorkloadPath"] == WORKLOAD
        assert row["BinarySHA256"] == SHA
        assert row["Oracle"] == ORACLE
        assert row["ExecutionStatus"] == "PILOT_RUN"
        assert row["RunStatus"] == "PILOT_MASKED"
        assert row["TerminalState_v31"] == "MASKED"
        assert row["ConfigFrozen"] == "NO"
        assert row["DecisionStatus"] == "ACCEPTED_BY_RESEARCHER_2026-11-08"
    # CSV equals the sheet for every cell of every row
    xl_rows = [[("" if ws.cell(r, c).value is None else str(ws.cell(r, c).value))
                for c in range(1, ws.max_column + 1)]
               for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value]
    csv_rows = [[row[k] for k in rows[0].keys()] for row in rows]
    assert xl_rows == csv_rows


def test_model_status_matrix_lq04_and_others():
    with MATRIX.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    header = rows[0]
    by_model = {row[0]: row for row in rows[1:]}
    assert len(rows[1:]) == 12
    lq = by_model["LQ04"]
    for stage, value in MATRIX_STAGES.items():
        assert lq[header.index(stage)] == str(value), stage
    assert lq[header.index("evidence")] == MATRIX_EVIDENCE
    for model, expected in OTHER_MATRIX_ROWS.items():
        assert by_model[model] == expected, model
