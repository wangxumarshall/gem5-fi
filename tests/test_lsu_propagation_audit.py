"""Tests for tools/lsu_propagation_audit.py (LSU v3.2.11 Task 8 / B2+B6+B7+B9).

The fixtures under tests/fixtures/audit/ are synthetic v3.1 JSONL pilots that
mirror the real trace contract: ``record_type`` event/propagation_edge/summary
records, semicolon ``detail`` key=value strings, identity fields as JSON
strings (real vintages mix ints and strings, so the tool must normalize with
``str()``), a two-line ``oracle.log`` and a ``manifest.json`` carrying the
recorded binary SHA256.

Coverage required by the task brief and the scope spec:

- a linked LQ04 chain grades ``LIFECYCLE_ONLY`` with ``consumer_verified=yes``
  (intact payload end to end -- structural completeness is not effect);
- an adjacent-but-unlinked FW02 pair is never ``COMPLETE_CAUSAL_CHAIN``
  (B3: time adjacency is not causality);
- a binary SHA mismatch is reported as ``BINARY_SHA_MISMATCH`` and never
  silently merged (B9);
- a missing pilot dir yields ``PILOT_DIR_ABSENT`` (never a blank);
- the matrix writer emits exactly the 20 enumerated columns with no empty cell
  and no bare ``PASS`` (B7);
- a malformed JSONL line is counted, not fatal (B2 streaming).
"""
import csv
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lsu_propagation_audit import (  # noqa: E402
    MATRIX_COLUMNS,
    STAGE_FIELDS,
    audit_model,
    audit_pilot,
    write_matrix,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "audit"
REAL_SHA = "f3c2a4423aab81ca565c7adcfb840a7b8f9cdb9f2a6b6b5ecc3d0e148af20694"


# ---------------------------------------------------------------------------
# audit_pilot
# ---------------------------------------------------------------------------

def test_linked_lq04_chain_stages_yes_and_lifecycle_only():
    result = audit_pilot(FIXTURES / "linked_lq04", "LQ04")
    assert result["stages"]["consumer_verified"] == "yes"
    assert result["classification"] == "LIFECYCLE_ONLY"
    # every one of the nine stages is verified on the intact chain
    for field in STAGE_FIELDS:
        assert result["stages"][field] == "yes", field
    assert result["missing"] == []
    # evidence bundle carries the required primary facts
    ev = result["evidence"]
    assert ev["injection_seq"] == "3"
    assert ev["pc"] == "400338"
    assert ev["tick"] == "80080"
    assert ev["event_ordinal"] == "1"
    assert ev["earliest_anomaly"]["event_id"] == "8"
    assert ev["earliest_anomaly"]["event_type"] == "memory_response"
    assert ev["writeback"]["phys_reg"] == "44"
    assert ev["writeback"]["writeback_value_fnv"] == "c6d4496e17859d5"
    assert ev["consumer"]["event_id"] == "18"
    assert ev["consumer"]["pc"] == "40034c"
    assert ev["consumer"]["consumer_input_fnv"] == "c6d4496e17859d5"
    assert ev["commit"]["commit_seq"] == "3"
    assert result["terminal"]["adjudicated"] == "MASKED"
    assert result["terminal"]["reason"] == "TARGET_COMMITTED_DATA_VALUE_PRESENT"
    assert result["oracle"]["expected"] == "b097eb83f71545cb"
    assert result["oracle"]["actual"] == "b097eb83f71545cb"
    assert result["oracle"]["pass"] is True
    assert ev["binary_sha"] == REAL_SHA
    assert ev["structural_chain_completeness"] == "COMPLETE"
    assert result["identity"]["sample_run_id"] == "LQ04-F0-W2-S01-R01"
    assert result["identity"]["seed"] == "1842987246"


def test_adjacent_unlinked_is_never_complete_causal_chain():
    result = audit_pilot(FIXTURES / "adjacent_unlinked", "FW02")
    assert result["classification"] in ("UNRESOLVED", "PARTIAL")
    assert result["classification"] == "UNRESOLVED"
    assert result["classification"] != "COMPLETE_CAUSAL_CHAIN"
    # the adjacent events carry a different ptag/dyn_inst_seq and no link,
    # so no downstream stage is verified and every gap has an explicit code
    assert result["stages"]["consumer_verified"] == "missing"
    assert result["stages"]["register_writeback_verified"] == "missing"
    assert result["stages"]["commit_verified"] == "missing"
    assert "NO_CONSUMER_EDGE" in result["missing"]
    assert "NO_EARLY_ANOMALY_EVENT" in result["missing"]
    assert result["missing"]  # never empty when stages are missing
    assert result["terminal"]["adjudicated"] == "UNRESOLVED"


def test_binary_mismatch_reported_not_merged():
    result = audit_pilot(FIXTURES / "linked_lq04", "LQ04",
                         binary_sha="deadbeef")
    assert result["missing"] == ["BINARY_SHA_MISMATCH"]
    # the effect grade is still derived from trace evidence, but the
    # provenance failure is an explicit, unmergeable code
    assert result["classification"] == "LIFECYCLE_ONLY"


def test_binary_sha_match_produces_no_code():
    result = audit_pilot(FIXTURES / "linked_lq04", "LQ04",
                         binary_sha=REAL_SHA)
    assert result["missing"] == []


def test_missing_pilot_dir():
    result = audit_pilot(Path("/nonexistent/audit/XYZ-R99"), "LQ04")
    assert "PILOT_DIR_ABSENT" in result["missing"]
    assert result["classification"] == "UNRESOLVED"
    assert all(v == "missing" for v in result["stages"].values())


def test_malformed_line_counted_not_fatal():
    result = audit_pilot(FIXTURES / "malformed_line", "LQ04")
    assert result["evidence"]["malformed_records"] == 1
    assert "MALFORMED_RECORDS" in result["missing"]
    # the rest of the chain is still evaluated
    assert result["stages"]["injection_verified"] == "yes"
    assert result["stages"]["consumer_verified"] == "yes"


def test_trace_hash_mismatch_detected(tmp_path):
    pilot = tmp_path / "LQ04-R04"
    shutil.copytree(FIXTURES / "linked_lq04", pilot)
    (pilot / "trace_v31.jsonl.sha256").write_text("00" * 32 + "\n")
    result = audit_pilot(pilot, "LQ04")
    assert "HASH_MISMATCH" in result["missing"]


# ---------------------------------------------------------------------------
# audit_model
# ---------------------------------------------------------------------------

def test_audit_model_single_pilot_row_fields():
    row = audit_model("LQ04", [FIXTURES / "linked_lq04"])
    for col in MATRIX_COLUMNS:
        assert col in row, col
    assert row["ModelID"] == "LQ04"
    assert row["PilotCount"] == "1"
    assert row["InjectionVerified"] == "yes(1/1)"
    assert row["OracleVerified"] == "yes(1/1)"
    assert row["StructuralChainCompleteness"] == "COMPLETE(1/1)"
    assert row["FaultEffectPropagationCoverage"] == "LIFECYCLE_ONLY(1/1)"
    assert row["FinalClassification"] == "LIFECYCLE_ONLY"
    assert row["MissingEvidence"] == "none"
    assert row["SupplementaryPilotRequired"] == "0"
    assert str(FIXTURES / "linked_lq04") in row["EvidencePaths"]
    assert row["SubUnit"] == "LQ"
    assert "LQEntry" in row["FaultDefinition"]
    assert row["binary_splits"] == []


def test_audit_model_binary_split_never_merges(tmp_path):
    other = tmp_path / "LQ04-R02"
    shutil.copytree(FIXTURES / "linked_lq04", other)
    manifest = json.loads((other / "manifest.json").read_text())
    manifest["gem5"]["binary_sha256"] = "cc33" * 16
    manifest["sample_run_id"] = "LQ04-F0-W2-S01-R02"
    (other / "manifest.json").write_text(json.dumps(manifest, indent=2))
    meta = json.loads((other / "pilot_meta.json").read_text())
    meta["pilot_id"] = "LQ04-F0-W2-S01-R02"
    meta["excel_identity"]["sample_run_id"] = "LQ04-F0-W2-S01-R02"
    (other / "pilot_meta.json").write_text(json.dumps(meta, indent=2))

    result = audit_model("LQ04", [FIXTURES / "linked_lq04", other])
    assert result["FinalClassification"] == "MIXED_BINARY_SPLIT"
    splits = result["binary_splits"]
    assert len(splits) == 2
    assert {s["ModelID"] for s in splits} == {"LQ04@f3c2a442", "LQ04@cc33cc33"}
    for split in splits:
        for col in MATRIX_COLUMNS:
            assert split.get(col) not in (None, ""), col
        assert split["FinalClassification"] == "LIFECYCLE_ONLY"
    assert result["PilotCount"] == "2"


# ---------------------------------------------------------------------------
# write_matrix (B7)
# ---------------------------------------------------------------------------

def _synthetic_row(model):
    """A well-formed non-LQ04 row; the writer test is about the format."""
    row = {"ModelID": model, "SubUnit": "TEST", "FaultDefinition": "synthetic",
           "PilotCount": "1", "FinalClassification": "UNRESOLVED",
           "MissingEvidence": "NO_INJECTION_EVENT",
           "SupplementaryPilotRequired": "1",
           "EvidencePaths": f"/synthetic/{model}-R01",
           "StructuralChainCompleteness": "INCOMPLETE(1/1)",
           "FaultEffectPropagationCoverage": "UNRESOLVED(1/1)",
           "FaultCausality": "n/a(1/1)"}
    for col in ("InjectionVerified", "ActivationVerified", "EarlyAnomalyVerified",
                "IntermediatePropagationVerified",
                "RegisterWritebackVerified", "ConsumerVerified",
                "CommitVerified", "TerminalVerified", "OracleVerified"):
        row[col] = "yes(1/1)"
    return row


def test_write_matrix_exact_20_columns_11_rows_no_empty_cells(tmp_path):
    rows = [_synthetic_row(m) for m in
            ("A01", "A03", "FW02", "SQ01", "DA04", "LP01", "MD04",
             "FW05", "SQ03", "SP05")]
    lq04 = audit_model("LQ04", [FIXTURES / "linked_lq04"])
    rows.append({col: lq04[col] for col in MATRIX_COLUMNS})
    out = tmp_path / "matrix.csv"
    write_matrix(rows, out)

    with open(out, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        data = list(reader)
    expected_header = [
        "ModelID", "SubUnit", "FaultDefinition", "PilotCount",
        "InjectionVerified", "ActivationVerified", "EarlyAnomalyVerified",
        "IntermediatePropagationVerified", "RegisterWritebackVerified",
        "ConsumerVerified", "CommitVerified", "TerminalVerified",
        "OracleVerified", "StructuralChainCompleteness",
        "FaultEffectPropagationCoverage", "FaultCausality",
        "FinalClassification", "MissingEvidence",
        "SupplementaryPilotRequired", "EvidencePaths"]
    assert header == expected_header
    assert header == MATRIX_COLUMNS
    assert len(header) == 20
    assert len(data) == 11
    for row in data:
        assert len(row) == 20
        for cell in row:
            assert cell.strip() != ""
            assert cell.strip().upper() != "PASS"
    # the LQ04 row is the real audit verdict, not a copy of history
    assert data[10][0] == "LQ04"
    assert data[10][16] == "LIFECYCLE_ONLY"
    assert data[10][18] == "0"


def test_write_matrix_rejects_empty_cell_and_bare_pass(tmp_path):
    bad = _synthetic_row("A01")
    bad["SubUnit"] = ""
    with pytest.raises(ValueError):
        write_matrix([bad], tmp_path / "m1.csv")
    bad2 = _synthetic_row("A01")
    bad2["OracleVerified"] = "PASS"
    with pytest.raises(ValueError):
        write_matrix([bad2], tmp_path / "m2.csv")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_json_and_matrix_outputs(tmp_path, capsys):
    from lsu_propagation_audit import main
    rc = main(["--model", "LQ04",
               "--pilot-dir", str(FIXTURES / "linked_lq04"),
               "--binary-sha", REAL_SHA,
               "--json", str(tmp_path / "audit.json"),
               "--matrix", str(tmp_path / "matrix.csv")])
    assert rc == 0
    payload = json.loads((tmp_path / "audit.json").read_text())
    assert payload["row"]["FinalClassification"] == "LIFECYCLE_ONLY"
    assert payload["row"]["MissingEvidence"] == "none"
    assert payload["pilots"][0]["classification"] == "LIFECYCLE_ONLY"
    with open(tmp_path / "matrix.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    assert len(rows) == 2  # header + one model row
    out = capsys.readouterr().out
    assert "LIFECYCLE_ONLY" in out
