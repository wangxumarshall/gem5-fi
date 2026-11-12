#!/usr/bin/env python3
"""Agent B — formal collector evidence isolation.

These tests drive ``tools/lsu_v333_launch.py`` against the synthetic fixtures
(``tests/fixtures/lsu_v333_synthetic``) and assert the four isolation
properties required by the launch-critical fix:

1. every record's ``Evidence`` path is under the explicit ``--runs`` root;
2. a historical root (non-matching campaign id) yields zero ``FORMAL`` records;
3. a run with no ``summary.json`` is ``OUTPUT_INCOMPLETE`` and reports no
   numeric ``InjectionCount`` (no silent zero);
4. a matching-campaign, evidence-complete run is ``FORMAL``.

No gem5 process is started and no historical audit tree is read.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = Path(__file__).resolve().parent / "fixtures" / "lsu_v333_synthetic"
COLLECTOR = ROOT / "tools" / "lsu_v333_launch.py"

CAMPAIGN_ID = "SYNTH-V333-FORMAL"
CLEAN_ID = "SYNTH-V333-CLEAN"

_MODULE = None


def _collector():
    global _MODULE
    if _MODULE is None:
        spec = importlib.util.spec_from_file_location(
            "lsu_v333_launch_isolation", COLLECTOR)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _MODULE = module
    return _MODULE


def _run(tmp_path: Path, root_name: str, campaign_id: str,
         design_name: str) -> tuple[Path, int]:
    out = tmp_path / f"out_{root_name}"
    rc = _collector().main([
        "--runs", str(FIX / root_name),
        "--campaign-id", campaign_id,
        "--design-matrix",
        str(FIX / "design" / f"{design_name}_SAMPLE_MATRIX.csv"),
        "--design-mapping",
        str(FIX / "design" / f"{design_name}_ROI_MAPPING.csv"),
        "--out", str(out),
        "--manifest-only",
    ])
    return out, rc


def _manifest(out: Path) -> list[dict]:
    with open(out / "LSU_120Run_Campaign_Manifest.csv", newline="",
              encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _find(rows, model, context, role):
    hits = [row for row in rows
            if row["ModelID"] == model and row["ContextID"] == context
            and row["Role"] == role]
    assert hits, f"collector emitted no record for {model}-{context}-{role}"
    return hits[0]


# ---------------------------------------------------------------------------
# (a) evidence path always under --runs
# ---------------------------------------------------------------------------
def test_every_evidence_path_is_under_the_runs_root(tmp_path):
    out, _rc = _run(tmp_path, "campaign", CAMPAIGN_ID, "SYNTH")
    rows = _manifest(out)
    assert rows, "collector produced no manifest rows"
    runs = (FIX / "campaign").resolve()
    for row in rows:
        evidence = Path(row["Evidence"]).resolve()
        assert evidence.is_relative_to(runs), (
            f"{row['ModelID']}-{row['ContextID']}-{row['Role']}: "
            f"evidence escaped --runs: {evidence}")
        assert not evidence.is_relative_to(FIX / "historical_evidence")


def test_per_run_manifest_is_written_outside_the_campaign_root(tmp_path):
    out, _rc = _run(tmp_path, "campaign_clean", CLEAN_ID, "CLEAN")
    per_run = out / "per_run"
    assert per_run.is_dir()
    assert (per_run / "A01-R01-fault" / "campaign_manifest.json").is_file()
    record = json.loads(
        (per_run / "A01-R01-fault" / "campaign_manifest.json").read_text())
    assert record["EvidenceKind"] == "FORMAL", record
    assert Path(record["Evidence"]).resolve().is_relative_to(
        (FIX / "campaign_clean").resolve())
    # Nothing may be written back into the campaign run dirs.
    assert not (FIX / "campaign_clean" / "A01-R01-fault" /
                "campaign_manifest.json").exists()


# ---------------------------------------------------------------------------
# (b) historical root yields zero FORMAL records
# ---------------------------------------------------------------------------
def test_historical_root_never_yields_formal_records(tmp_path):
    # The design matches the run dirs, but the runs carry a different
    # campaign_id (SYNTH-V332-PRE-FORMAL), so nothing may be admitted.
    out, rc = _run(tmp_path, "historical_evidence", CAMPAIGN_ID, "HISTORICAL")
    rows = _manifest(out)
    assert rows, "collector produced no manifest rows"
    assert rc != 0, "a wholly non-formal root must exit nonzero"
    for row in rows:
        assert row["EvidenceKind"] != "FORMAL", row
        assert row["Status"] not in {
            "PASS", "COMPLETED", "ORACLE_FAIL", "QUALIFIED"}, row
        assert row["Reason"] in {
            "HISTORICAL_CAMPAIGN_MISMATCH", "ID_MISMATCH"}, row


# ---------------------------------------------------------------------------
# (c) missing summary => OUTPUT_INCOMPLETE, no numeric InjectionCount
# ---------------------------------------------------------------------------
def test_missing_summary_is_incomplete_without_a_numeric_count(tmp_path):
    out, rc = _run(tmp_path, "campaign", CAMPAIGN_ID, "SYNTH")
    row = _find(_manifest(out), "A01", "R02", "fault")
    assert row["Status"] == "OUTPUT_INCOMPLETE", row
    assert row["EvidenceKind"] == "FORMAL", row
    assert row["Reason"] == "SUMMARY_MISSING", row
    count = str(row["InjectionCount"]).strip()
    assert not count.isdigit(), (
        "a missing summary must not silently default InjectionCount to a "
        f"number: {row}")
    assert count in {"n/a", "", "UNKNOWN"}, row
    assert rc != 0


def test_historical_reroot_is_non_formal_even_with_matching_design(tmp_path):
    out, _rc = _run(tmp_path, "historical_evidence", CAMPAIGN_ID, "HISTORICAL")
    for row in _manifest(out):
        assert row["EvidenceKind"] == "NON_FORMAL", row


# ---------------------------------------------------------------------------
# (d) matching campaign, complete run => FORMAL
# ---------------------------------------------------------------------------
def test_matching_campaign_complete_run_is_formal(tmp_path):
    out, rc = _run(tmp_path, "campaign_clean", CLEAN_ID, "CLEAN")
    rows = _manifest(out)
    for model, context, role in (("A01", "R01", "fault"),
                                 ("A01", "R01", "control")):
        row = _find(rows, model, context, role)
        assert row["EvidenceKind"] == "FORMAL", row
        assert row["Status"] in {"COMPLETED", "ORACLE_FAIL"}, row
    assert rc == 0, f"an all-good campaign must exit 0, got {rc}"
