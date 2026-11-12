"""LSU v3.3.3 workload provenance tests (Agent C).

Every hash asserted here is recomputed from the real file bytes inside the
test; no expected digest is taken from the tool under test except the frozen
authorization table's own published values, which are cross-checked against
``hashlib``.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lsu_v332_matrix as matrix  # noqa: E402
import lsu_v333_provenance as provenance  # noqa: E402


def real_sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def test_frozen_table_has_nine_workloads():
    table = provenance.load_frozen_table()
    assert len(table) == 9, table
    for name, digest in table.items():
        assert len(digest) == 64 and int(digest, 16) >= 0, (name, digest)


def test_all_12_models_exist_readable_and_match_real_bytes():
    rows = provenance.provenance_table()
    assert len(rows) == 12
    assert [row["ModelID"] for row in rows] == list(matrix.MODELS)

    seen = set()
    for row in rows:
        path = Path(row["FormalExecutionPath"])
        assert row["Exists"], row
        assert row["Readable"], row
        assert path.is_file(), path
        assert row["ELF_SHA256"] == real_sha(path), row
        assert row["MatchesFrozen"], row
        assert row["ELF_SHA256"] == row["FrozenSHA256"], row
        # The source artifact must hold the same approved bytes.
        source = Path(row["WorkloadSourcePath"])
        assert source.is_file(), source
        assert real_sha(source) == row["FrozenSHA256"], row
        seen.add(row["Workload"])
    assert seen == set(provenance.load_frozen_table())


def test_frozen_hashes_match_actual_bytes_for_all_nine():
    frozen = provenance.load_frozen_table()
    checked = set()
    for model in matrix.MODELS:
        path = provenance.formal_execution_path(model)
        expected = frozen[path.name]
        assert real_sha(path) == expected, (model, path)
        checked.add(path.name)
    assert checked == set(frozen), sorted(set(frozen) - checked)


def test_formal_execution_path_equals_resolve_workload():
    for model in matrix.MODELS:
        expected = matrix.resolve_workload(model, matrix.CONTEXTS[model].get("workload"))
        assert provenance.formal_execution_path(model) == Path(expected), model


def test_paths_are_current_worktree_without_archive_markers():
    for row in provenance.provenance_table():
        for field in ("WorkloadSourcePath", "FormalExecutionPath"):
            text = row[field].replace("\\", "/").lower()
            assert "v3.2/" not in text, row
            assert "v3.2.10/" not in text, row
            assert "archive" not in text, row
            assert Path(row[field]).resolve().is_relative_to(ROOT), row


def test_no_provenance_errors_in_the_real_tree():
    assert provenance.provenance_errors() == []


def test_manifest_template_120_rows_and_columns():
    result = provenance.verify_manifest_template()
    assert result["errors"] == [], result["errors"]
    assert result["rows"] == 120
    assert result["unique_sample_run_ids"] == 60
    assert result["unique_seeds"] == 60
    for column in ("WorkloadSourcePath", "FormalExecutionPath", "ELF_SHA256", "Evidence"):
        assert column in result["columns_present"], column


def test_manifest_rows_carry_real_hashes_and_execution_path(tmp_path):
    template = provenance.MANIFEST_TEMPLATE
    with template.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 120
    for row in rows:
        model = row["ModelID"]
        exec_path = matrix.resolve_workload(model, matrix.CONTEXTS[model].get("workload"))
        assert Path(row["FormalExecutionPath"]) == Path(exec_path), row["RunID"]
        assert Path(row["ELF"]) == Path(exec_path), row["RunID"]
        assert row["ELF_SHA256"] == real_sha(exec_path), row["RunID"]
        assert row["Workload"] == Path(exec_path).name, row["RunID"]
        assert row["Evidence"].startswith(str(matrix.OUT_BASE.parent / "formal_v333_final_20261112"))


def test_wrong_expected_sha_is_detected():
    frozen = provenance.load_frozen_table()
    bad = dict(frozen)
    bad["agu_addrmodes"] = "0" * 64
    rows = provenance.provenance_table(frozen=bad)
    a01 = next(row for row in rows if row["ModelID"] == "A01")
    assert a01["MatchesFrozen"] is False
    assert a01["ELF_SHA256"] != bad["agu_addrmodes"]
    errors = provenance.provenance_errors(frozen=bad)
    assert any("sha256 mismatch" in error for error in errors), errors


def test_deliberately_wrong_frozen_sha_for_a_missing_entry_is_detected():
    frozen = provenance.load_frozen_table()
    frozen.pop("alignment")
    rows = provenance.provenance_table(frozen=frozen)
    da04 = next(row for row in rows if row["ModelID"] == "DA04")
    assert da04["FrozenSHA256"] == ""
    assert da04["MatchesFrozen"] is False
    errors = provenance.provenance_errors(frozen=frozen)
    assert any("absent from the frozen table" in error for error in errors), errors


def test_duplicate_basename_with_different_content_is_flagged(tmp_path):
    first = tmp_path / "a" / "kernel"
    second = tmp_path / "b" / "kernel"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_bytes(b"one build\n")
    second.write_bytes(b"another build\n")
    duplicates = provenance.find_duplicate_basenames([first, second])
    assert len(duplicates) == 1
    assert duplicates[0]["basename"] == "kernel"
    assert len(duplicates[0]["shas"]) == 2


def test_identical_duplicate_basename_is_not_flagged(tmp_path):
    first = tmp_path / "a" / "kernel"
    second = tmp_path / "b" / "kernel"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_bytes(b"same bytes\n")
    second.write_bytes(b"same bytes\n")
    assert provenance.find_duplicate_basenames([first, second]) == []


def test_manifest_tamper_is_detected(tmp_path):
    tampered = tmp_path / "template.csv"
    with provenance.MANIFEST_TEMPLATE.open(encoding="utf-8", newline="") as src:
        rows = list(csv.DictReader(src))
        fields = list(rows[0].keys())
    # Point an FW05 row at A01's ELF: same column, wrong model.
    a01_path = next(row["FormalExecutionPath"] for row in rows if row["ModelID"] == "A01")
    fw05 = next(row for row in rows if row["ModelID"] == "FW05")
    assert fw05["FormalExecutionPath"] != a01_path
    fw05["FormalExecutionPath"] = a01_path
    with tampered.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    result = provenance.verify_manifest_template(tampered)
    assert result["errors"], "tampered FormalExecutionPath must be detected"


def test_cli_json_reports_ok(capsys):
    assert provenance.main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["errors"] == []
    assert len(payload["rows"]) == 12
    assert payload["manifest"]["rows"] == 120
    assert payload["binary_config"]["BinaryMatchesFrozen"] is True
    assert payload["binary_config"]["ConfigMatchesFrozen"] is True
