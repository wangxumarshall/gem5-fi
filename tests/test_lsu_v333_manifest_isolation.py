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
import shutil
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
    assert sum(1 for row in rows if row["EvidenceKind"] == "FORMAL") == 0
    for row in rows:
        assert row["EvidenceKind"] == "NON_FORMAL", row
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
    # v3.3.3: FORMAL requires complete canonical evidence, so a missing
    # summary is NON_FORMAL (never admitted as formal evidence).
    assert row["EvidenceKind"] == "NON_FORMAL", row
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
        # Attempt and applied counts are always present as separate fields.
        assert row["InjectionAttemptCount"] != "", row
        assert row["InjectionAppliedCount"] != "", row
    assert rc == 0, f"an all-good campaign must exit 0, got {rc}"


# ---------------------------------------------------------------------------
# (e) canonical attempt resolution (v3.3.3 final-launch closure, BUG 2)
# ---------------------------------------------------------------------------
PASS_LIKE = {"PASS", "COMPLETED", "ORACLE_FAIL", "QUALIFIED"}


def _copy_root(tmp_path: Path, source: str) -> Path:
    runs = tmp_path / "runs"
    shutil.copytree(FIX / source, runs)
    return runs


def _filtered_design(tmp_path: Path, source: str, sample_run_id: str
                     ) -> tuple[Path, Path]:
    """Write a one-row design matrix/mapping pair for ``sample_run_id``."""
    design = tmp_path / "design"
    design.mkdir(exist_ok=True)
    paths = {}
    for kind in ("SAMPLE_MATRIX", "ROI_MAPPING"):
        src = FIX / "design" / f"{source}_{kind}.csv"
        with src.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            rows = [row for row in reader
                    if row.get("SampleRunID") == sample_run_id]
        assert rows, f"{src} has no row for {sample_run_id}"
        dst = design / f"{source}_{kind}.csv"
        with dst.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        paths[kind] = dst
    return paths["SAMPLE_MATRIX"], paths["ROI_MAPPING"]


def _run_design(tmp_path: Path, runs: Path, campaign_id: str,
                matrix: Path, mapping: Path,
                tag: str = "out") -> tuple[Path, int]:
    out = tmp_path / tag
    rc = _collector().main([
        "--runs", str(runs),
        "--campaign-id", campaign_id,
        "--design-matrix", str(matrix),
        "--design-mapping", str(mapping),
        "--out", str(out),
        "--manifest-only",
    ])
    return out, rc


def _adopt_attempt(run: Path, attempt_id: str = "attempt_001",
                   status: str = "COMPLETED",
                   campaign_id: str = CLEAN_ID) -> Path:
    """Move a legacy flat run's evidence into ``attempts/<attempt_id>``."""
    adir = run / "attempts" / attempt_id
    adir.mkdir(parents=True)
    for child in list(run.iterdir()):
        if child.name == "attempts":
            continue
        child.rename(adir / child.name)
    (adir / "attempt.json").write_text(json.dumps({
        "attempt_id": attempt_id, "status": status,
        "campaign_id": campaign_id}))
    return adir


def _clone_attempt(run: Path, source: str, attempt_id: str,
                   status: str) -> Path:
    src = run / "attempts" / source
    dst = run / "attempts" / attempt_id
    shutil.copytree(src, dst)
    (dst / "attempt.json").write_text(json.dumps({
        "attempt_id": attempt_id, "status": status,
        "campaign_id": CLEAN_ID}))
    return dst


def _write_canonical(run: Path, attempt_id: str,
                     campaign_id: str = CLEAN_ID) -> None:
    (run / "canonical.json").write_text(json.dumps({
        "attempt_id": attempt_id, "campaign_id": campaign_id}))


def test_canonical_attempt_is_graded_not_a_failed_sibling(tmp_path):
    runs = _copy_root(tmp_path, "campaign_clean")
    run = runs / "A01-R01-fault"
    adir = _adopt_attempt(run)
    _clone_attempt(run, "attempt_001", "attempt_002", "FAILED")
    _write_canonical(run, "attempt_001")
    matrix, mapping = _filtered_design(tmp_path, "CLEAN", "SYNTH-A01-R01")

    out, rc = _run_design(tmp_path, runs, CLEAN_ID, matrix, mapping)
    row = _find(_manifest(out), "A01", "R01", "fault")
    assert row["EvidenceKind"] == "FORMAL", row
    assert row["Status"] in {"COMPLETED", "ORACLE_FAIL"}, row
    # The canonical attempt is the evidence; the non-canonical FAILED sibling
    # is never read.
    assert "attempts/attempt_001" in row["Evidence"], row
    assert "attempt_002" not in row["Evidence"], row
    assert str(adir.resolve()) == str(Path(row["Evidence"]).resolve())
    assert rc == 0, rc


def test_canonical_failed_attempt_is_never_formal(tmp_path):
    runs = _copy_root(tmp_path, "campaign_clean")
    run = runs / "A01-R01-fault"
    _adopt_attempt(run, "attempt_001", "COMPLETED")
    _clone_attempt(run, "attempt_001", "attempt_002", "FAILED")
    _write_canonical(run, "attempt_002")
    matrix, mapping = _filtered_design(tmp_path, "CLEAN", "SYNTH-A01-R01")

    out, rc = _run_design(tmp_path, runs, CLEAN_ID, matrix, mapping)
    row = _find(_manifest(out), "A01", "R01", "fault")
    assert row["EvidenceKind"] == "NON_FORMAL", row
    assert row["Status"] not in PASS_LIKE, row
    assert "CANONICAL_FAILED" in row["Reason"], row
    assert rc != 0


def test_uncanonical_attempts_are_never_formal(tmp_path):
    experiments = tmp_path / "experiments"
    experiments.mkdir()
    # a non-canonical FAILED attempt (no canonical.json) must never be graded
    runs = _copy_root(experiments, "campaign_clean")
    run = runs / "A01-R01-fault"
    _adopt_attempt(run, "attempt_001", "COMPLETED")
    _clone_attempt(run, "attempt_001", "attempt_002", "FAILED")
    matrix, mapping = _filtered_design(experiments, "CLEAN", "SYNTH-A01-R01")

    out, rc = _run_design(experiments, runs, CLEAN_ID, matrix, mapping)
    row = _find(_manifest(out), "A01", "R01", "fault")
    assert row["EvidenceKind"] == "NON_FORMAL", row
    assert row["Status"] not in PASS_LIKE, row
    assert "CANONICAL" in row["Reason"], row
    assert rc != 0


def test_evidence_outside_runs_is_non_formal(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    shutil.copytree(FIX / "campaign_clean" / "A01-R01-control",
                    runs / "A01-R01-control")
    outside = tmp_path / "outside" / "A01-R01-fault"
    shutil.copytree(FIX / "campaign_clean" / "A01-R01-fault", outside)
    (runs / "A01-R01-fault").symlink_to(outside)
    matrix, mapping = _filtered_design(tmp_path, "CLEAN", "SYNTH-A01-R01")

    out, rc = _run_design(tmp_path, runs, CLEAN_ID, matrix, mapping)
    row = _find(_manifest(out), "A01", "R01", "fault")
    assert row["EvidenceKind"] == "NON_FORMAL", row
    assert row["Status"] not in PASS_LIKE, row
    assert row["Reason"] == "EVIDENCE_OUTSIDE_RUNS", row
    assert rc != 0


def test_missing_summary_trace_or_oracle_are_never_pass(tmp_path):
    # summary / trace defects already exist in the mixed campaign root.
    out, rc = _run(tmp_path, "campaign", CAMPAIGN_ID, "SYNTH")
    rows = _manifest(out)
    for model, context, role in (("A01", "R02", "fault"),   # missing summary
                                 ("A01", "R03", "fault"),   # missing trace
                                 ("A01", "R03", "control")):  # missing trace
        row = _find(rows, model, context, role)
        assert row["EvidenceKind"] == "NON_FORMAL", row
        assert row["Status"] not in PASS_LIKE, row
    assert rc != 0

    # Missing oracle.log on an otherwise complete run.
    runs = _copy_root(tmp_path / "oracle", "campaign_clean")
    (runs / "A01-R01-fault" / "oracle.log").unlink()
    matrix, mapping = _filtered_design(tmp_path / "oracle", "CLEAN",
                                       "SYNTH-A01-R01")
    out2, rc2 = _run_design(tmp_path / "oracle", runs, CLEAN_ID, matrix,
                            mapping)
    row = _find(_manifest(out2), "A01", "R01", "fault")
    assert row["EvidenceKind"] == "NON_FORMAL", row
    assert row["Status"] not in PASS_LIKE, row
    assert "oracle.log" in row["MissingEvidence"], row
    assert rc2 != 0


def test_qualified_is_never_upgraded_to_pass(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    for role in ("fault", "control"):
        shutil.copytree(FIX / "campaign" / f"SP05-R01-{role}",
                        runs / f"SP05-R01-{role}")
    # A non-SDC terminal lets the qualification verdict decide the status.
    summary_path = runs / "SP05-R01-fault" / "summary.json"
    summary = json.loads(summary_path.read_text())
    summary["terminal"] = "UNRESOLVED"
    summary["terminal_reason"] = "NO_TERMINAL"
    summary_path.write_text(json.dumps(summary))
    matrix, mapping = _filtered_design(tmp_path, "SYNTH", "SYNTH-SP05-R01")

    out, _rc = _run_design(tmp_path, runs, CAMPAIGN_ID, matrix, mapping)
    row = _find(_manifest(out), "SP05", "R01", "fault")
    assert row["QualifiedStatus"] == "QUALIFIED", row
    assert row["Status"] == "QUALIFIED", row
    assert row["Status"] != "PASS", row
    assert row["EvidenceKind"] == "FORMAL", row
    # Separate counts survive even on a qualified record.
    assert row["InjectionAppliedCount"] == "1", row
    assert row["InjectionAttemptCount"] == "UNKNOWN", row
