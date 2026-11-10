"""v3.2.11 audit additions to the v3.2.6 workbook."""
from pathlib import Path
import openpyxl
import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/gem5-fi/lsu/implementation_v3_2"
V325 = BASE / "excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.5.xlsx"
V326 = BASE / "excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx"
AUDIT_SHEET = "20.v3.2.11传播链审计"
CHANGED = {("4.源码Hook审计", "G4"), ("7.Trace Hook规范", "D20"),
           ("11.风险与待确认事项", "F19"), ("11.风险与待确认事项", "F33"),
           ("11.风险与待确认事项", "F45")}


def load():
    return openpyxl.load_workbook(V325), openpyxl.load_workbook(V326)


def test_audit_sheet_and_matrix_rows():
    _, wb = load()
    assert AUDIT_SHEET in wb.sheetnames
    ws = wb[AUDIT_SHEET]
    header = [c.value for c in ws[1]]
    assert header == ["ModelID", "SubUnit", "FaultDefinition", "PilotCount",
                      "InjectionVerified", "ActivationVerified", "EarlyAnomalyVerified",
                      "IntermediatePropagationVerified", "RegisterWritebackVerified",
                      "ConsumerVerified", "CommitVerified", "TerminalVerified",
                      "OracleVerified", "StructuralChainCompleteness",
                      "FaultEffectPropagationCoverage", "FaultCausality",
                      "FinalClassification", "MissingEvidence",
                      "SupplementaryPilotRequired", "EvidencePaths"]
    models = [ws.cell(r, 1).value for r in range(2, ws.max_row + 1)]
    assert models == ["A01", "A03", "FW02", "SQ01", "DA04", "LP01", "MD04",
                      "FW05", "SQ03", "SP05", "LQ04"]
    for r in range(2, ws.max_row + 1):
        for c in range(1, 21):
            v = ws.cell(r, c).value
            assert v not in (None, "", "PASS"), (r, c, v)


def test_notes_and_changelog_present():
    _, wb = load()
    ws3 = wb["3.最终12模型矩阵"]
    notes = {ws3.cell(r, 1).value: (ws3.cell(r, 18).value or "")
             for r in range(2, ws3.max_row + 1)}
    for m in ("A01", "A03", "FW02", "SQ01", "DA04", "LP01", "MD04",
              "FW05", "SQ03", "SP05", "LQ04", "RP01"):
        assert "v3.2.11 audit:" in notes[m] or "v3.2.11 design:" in notes[m], m
    ws19 = wb["19.v3.2.11变更记录"]
    col_a = {ws19.cell(r, 1).value for r in range(1, ws19.max_row + 1)}
    assert "11-model propagation audit" in col_a
    assert "RP01 design gate" in col_a


def test_identity_and_freeze_invariants():
    _, wb = load()
    ws5 = wb["5.60个样本执行矩阵"]
    ids = [tuple(ws5.cell(r, c).value for c in (1, 2, 3, 4))
           for r in range(2, 62)]
    assert len(ids) == 60
    frozen = {ws5.cell(r, 38).value for r in range(2, 62)}
    assert frozen == {"NO"}
    warm = {ws5.cell(r, 23).value for r in range(2, 62)}
    roi = {ws5.cell(r, 24).value for r in range(2, 62)}
    assert warm == {"NEEDS_RESEARCHER_CONFIRMATION"}
    assert roi == {"NEEDS_RESEARCHER_CONFIRMATION"}
    ws3 = wb["3.最终12模型矩阵"]
    rp01 = next(r for r in range(2, ws3.max_row + 1)
                if ws3.cell(r, 1).value == "RP01")
    assert ws3.cell(rp01, 26).value == "NEEDS_USER_DECISION"


def test_no_other_cell_changed():
    old, new = load()
    for name in old.sheetnames:
        if name == "19.v3.2.11变更记录":
            continue
        wo, wn = old[name], new[name]
        for row in wo.iter_rows():
            for cell in row:
                coord = cell.coordinate
                if (name, coord) in CHANGED:
                    continue
                if name == "3.最终12模型矩阵" and cell.column == 18:
                    continue
                nv = wn[coord].value
                assert nv == cell.value, (name, coord, cell.value, nv)
