"""v3.2.6 workbook: A2 LQ04 line-number corrections only; all else unchanged.

Excel v3.2.6 is v3.2.5 plus the corrections ordered by
``docs/gem5-fi/lsu/implementation_v3_2/LQ04_Source_Audit_line_corrections_v3.2.11.md``
(§5/§6 for sheet ``4.源码Hook审计`` ``G4``, §7.1 for sheet ``7.Trace Hook规范``
``D20``, §7.2/§7.3 for sheet ``11.风险与待确认事项`` ``F19``/``F33``/``F45``)
plus the new ``19.v3.2.11变更记录`` sheet. Every other cell must keep its
v3.2.5 value: the 60 SampleRunID/RunID/SubTaskID/Seed identities,
ConfigFrozen=NO, Warm-up/ROI NEEDS_RESEARCHER_CONFIRMATION and the RP01
DecisionStatus NEEDS_USER_DECISION.
"""
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
EXCEL = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/excel"
V325 = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx"
V326 = EXCEL / "gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx"

SAMPLE_SHEET = "5.60个样本执行矩阵"
MODEL_SHEET = "3.最终12模型矩阵"
HOOK_SHEET = "4.源码Hook审计"
TRACE_SHEET = "7.Trace Hook规范"
RISK_SHEET = "11.风险与待确认事项"
REVISION_SHEET = "19.v3.2.11变更记录"
AUDIT_SHEET = "20.v3.2.11传播链审计"

OLD_G4 = ("LSQUnit::insertLoad (353-414); commitLoad (775-798); "
          "squash (986-1020); clear/pop_front")
NEW_G4 = ("LSQUnit::insertLoad (394-463); executeLoad (719-831, "
          "LQ04 hook 796-828); lq04Restore (927-943); commitLoad (945-973); "
          "commitLoads (975-987); squash (1202-1338, "
          "load-side window 1205-1254)")

OLD_D20 = "lsq_unit.cc:353-414,775-798,986-1020,1376-1727"
NEW_D20 = ("lsq_unit.cc:394-463,719-831,927-943,945-973,975-987,"
           "1202-1338,1641-2074")

OLD_F19 = "lsq_unit.cc:775-798,986-1020"
NEW_F19 = "lsq_unit.cc:945-973,1202-1338"
OLD_F33 = "lsq_unit.cc:775-798"
NEW_F33 = "lsq_unit.cc:945-973"
OLD_F45 = "lsq_unit.hh:107-125; lsq.hh:539"
NEW_F45 = "lsq_unit.hh:117-140; lsq.hh:539"

# (sheet, coordinate): (v3.2.5 value, v3.2.6 value) -- the only cells that
# may differ between the two workbooks.
CHANGED = {
    (HOOK_SHEET, "G4"): (OLD_G4, NEW_G4),
    (TRACE_SHEET, "D20"): (OLD_D20, NEW_D20),
    (RISK_SHEET, "F19"): (OLD_F19, NEW_F19),
    (RISK_SHEET, "F33"): (OLD_F33, NEW_F33),
    (RISK_SHEET, "F45"): (OLD_F45, NEW_F45),
}

IDENTITY_COLS = ("SampleRunID", "RunID", "SubTaskID", "Seed")

# Frozen LQ04 fault-definition fields of sheet 4 row 4 (correction doc §4):
# TargetField, NormalValue (both), FaultValue (both), InjectionTiming,
# Duration, plus the accepted DecisionStatus.
FROZEN_COORDS = ("H4", "K4", "AB4", "L4", "AC4", "M4", "N4", "AG4")


def _load(path):
    return openpyxl.load_workbook(path, data_only=True)


def _headers(ws):
    return {str(c.value).strip(): c.column for c in ws[1] if c.value}


def _sample_rows(ws):
    return [r for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value]


def test_v326_is_v325_sheets_plus_revision_sheet():
    old = _load(V325)
    new = _load(V326)
    assert new.sheetnames == old.sheetnames + [REVISION_SHEET, AUDIT_SHEET]
    assert len(new.sheetnames) == 20


def test_60_identity_rows_unchanged():
    a = _load(V325)[SAMPLE_SHEET]
    b = _load(V326)[SAMPLE_SHEET]
    ca, cb = _headers(a), _headers(b)
    rows = _sample_rows(b)
    assert len(rows) == 60
    for r in rows:
        for name in IDENTITY_COLS:
            assert a.cell(r, ca[name]).value == b.cell(r, cb[name]).value, \
                (r, name)


def test_config_frozen_all_no():
    b = _load(V326)[SAMPLE_SHEET]
    cb = _headers(b)
    rows = _sample_rows(b)
    assert len(rows) == 60
    for r in rows:
        assert b.cell(r, cb["ConfigFrozen"]).value == "NO", r


def test_warmup_and_roi_need_researcher_confirmation():
    b = _load(V326)[SAMPLE_SHEET]
    cb = _headers(b)
    rows = _sample_rows(b)
    assert len(rows) == 60
    for r in rows:
        assert b.cell(r, cb["WarmUp"]).value == \
            "NEEDS_RESEARCHER_CONFIRMATION", r
        assert b.cell(r, cb["ROI"]).value == \
            "NEEDS_RESEARCHER_CONFIRMATION", r


def test_rp01_decision_status_needs_user_decision():
    new = _load(V326)
    m = new[MODEL_SHEET]
    cm = _headers(m)
    rp = [r for r in range(2, m.max_row + 1)
          if m.cell(r, cm["ModelID"]).value == "RP01"]
    assert len(rp) == 1
    assert m.cell(rp[0], cm["DecisionStatus"]).value == "NEEDS_USER_DECISION"
    s = new[SAMPLE_SHEET]
    cs = _headers(s)
    rows = [r for r in _sample_rows(s)
            if str(s.cell(r, cs["SampleRunID"]).value).startswith("RP01")]
    assert len(rows) == 5
    for r in rows:
        assert s.cell(r, cs["DecisionStatus"]).value == \
            "NEEDS_USER_DECISION", r


def test_sheet4_lq04_g4_corrected():
    a = _load(V325)[HOOK_SHEET]
    b = _load(V326)[HOOK_SHEET]
    assert b["A4"].value == "LQ04"
    assert b["B4"].value == "LQ04-F0-W2-S01"
    assert a["G4"].value == OLD_G4
    assert b["G4"].value == NEW_G4
    for stale in ("353-414", "775-798", "986-1020", "clear/pop_front"):
        assert stale not in b["G4"].value, stale
    for span in ("insertLoad (394-463)", "executeLoad (719-831",
                 "LQ04 hook 796-828", "lq04Restore (927-943)",
                 "commitLoad (945-973)", "commitLoads (975-987)",
                 "squash (1202-1338", "load-side window 1205-1254"):
        assert span in b["G4"].value, span
    # frozen fault-definition fields (correction doc §4) are untouched
    for coord in FROZEN_COORDS:
        assert a[coord].value == b[coord].value, coord


def test_sheet7_d20_corrected():
    a = _load(V325)[TRACE_SHEET]
    b = _load(V326)[TRACE_SHEET]
    assert b["A20"].value == "Node"
    assert b["B20"].value == "LQ"
    assert a["D20"].value == OLD_D20
    assert b["D20"].value == NEW_D20
    for stale in ("353-414", "775-798", "986-1020", "1376-1727"):
        assert stale not in b["D20"].value, stale


def test_sheet11_lq04_risk_evidence_corrected():
    a = _load(V325)[RISK_SHEET]
    b = _load(V326)[RISK_SHEET]
    assert b["A19"].value == "R18" and b["C19"].value == "LQ04"
    assert b["A33"].value == "R32" and b["C33"].value == "LQ04"
    assert b["A45"].value == "R44" and b["C45"].value == "LQ04"
    assert a["F19"].value == OLD_F19
    assert b["F19"].value == NEW_F19
    assert a["F33"].value == OLD_F33
    assert b["F33"].value == NEW_F33
    assert a["F45"].value == OLD_F45
    assert b["F45"].value == NEW_F45
    for stale in ("775-798", "986-1020"):
        assert stale not in b["F19"].value, stale
    assert "775-798" not in b["F33"].value
    assert "107-125" not in b["F45"].value
    assert "lsq.hh:539" in b["F45"].value


def test_only_the_five_lq04_cells_differ():
    old = _load(V325)
    new = _load(V326)
    for name in old.sheetnames:
        if name == REVISION_SHEET:
            continue  # v3.2.11 appends audit/RP01 rows
        wa, wb = old[name], new[name]
        assert (wa.max_row, wa.max_column) == (wb.max_row, wb.max_column), \
            name
        for row in range(1, wa.max_row + 1):
            for col in range(1, wa.max_column + 1):
                if name == "3.最终12模型矩阵" and col == 18:
                    continue  # v3.2.11 appends the audit verdict to Notes
                coord = wa.cell(row, col).coordinate
                va = wa.cell(row, col).value
                vb = wb.cell(row, col).value
                if (name, coord) in CHANGED:
                    assert va == CHANGED[(name, coord)][0], (name, coord)
                    assert vb == CHANGED[(name, coord)][1], (name, coord)
                else:
                    assert va == vb, (name, coord)


def test_revision_sheet_records_corrections_and_scope():
    ws = _load(V326)[REVISION_SHEET]
    header = [c.value for c in ws[3]]
    assert header[:3] == ["Item", "Change", "Reason"]
    data = [row for row in ws.iter_rows(min_row=4, values_only=True)
            if row and row[0]]
    assert len(data) >= 2
    text = " ".join(str(v) for row in ws.iter_rows(values_only=True)
                    for v in row if v is not None)
    # the A2 correction is recorded with its authoritative source
    assert "LQ04_Source_Audit_line_corrections_v3.2.11.md" in text
    assert "394-463" in text
    assert "1641-2074" in text
    assert "117-140" in text
    # the round scope and the unchanged-scope / platform notes are recorded
    assert "v3.2.11" in text
    assert "NEEDS_RESEARCHER_CONFIRMATION" in text
    assert "run_pilot.py" in text
    assert "v3.2.4" in text
