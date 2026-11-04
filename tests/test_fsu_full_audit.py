"""tests/test_fsu_full_audit.py — full current-tool re-audit classification.

The heavy real-evidence pass is run by the CLI.  These tests exercise the
four-category classification and provenance logic with synthetic directories
and stubbed recomputation; they never claim a real seed passed.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_full_audit as F  # noqa: E402


def _component(pid, ok=True, missing=False):
    return {
        "program_id": pid, "program_index": 0,
        "execution_complete": True, "evidence_valid": not missing,
        "audit_ok": ok, "certified": ok,
        "recomputed_audit_ok": ok, "recomputed_certified": ok,
        "component_status": "admitted" if ok else "rejected",
        "oracle_category": "SDC", "chain_terminal": "full",
        "missing_evidence": ["boom"] if missing else [],
        "violations": [] if ok else ["bad"],
        "plan_binding_key": "seed_plan_entry", "plan_binding_ok": ok,
        "manifest_sha256": "a" * 64, "evidence_sha256": "b" * 64,
    }


def _suite_report(status, certified, components, violations=None,
                  missing=None):
    return {
        "suite_id": "polybench-fp-v1-f5", "suite_seed": 1,
        "suite_hash": "c" * 64, "suite_hash_declared": "c" * 64,
        "suite_certified": certified, "recompute_status": status,
        "components": components, "violations": violations or [],
        "missing_evidence": missing or [], "component_count": len(components),
        "seed_plan_schema": "f5-v1",
    }


def _seed_dir(root, rid, seed, suite=False):
    d = root / rid / f"seed{seed}"
    d.mkdir(parents=True)
    if suite:
        (d / "suite_manifest.json").write_text("{}", encoding="utf-8")
    else:
        attempt = d / "attempt-1"
        attempt.mkdir()
        (attempt / "manifest.json").write_text(json.dumps(
            {"run_id": rid, "seed": seed, "sample_run_id": f"s{seed}"}),
            encoding="utf-8")
        (attempt / "chain_report.json").write_text("{}", encoding="utf-8")
        (attempt / "inject").mkdir()
        (attempt / "inject/prop_evt.txt.gz").write_bytes(b"")
        (d / "AUTHORITATIVE").write_text(str(attempt), encoding="utf-8")
    return d


def test_discover_separates_suite_and_non_suite(tmp_path):
    _seed_dir(tmp_path, "FSU-A", 1, suite=True)
    _seed_dir(tmp_path, "FSU-B", 1, suite=False)
    suites, non = F.discover(tmp_path)
    assert [r for _d, r in suites] == ["FSU-A"]
    assert [r for _d, r in non] == ["FSU-B"]


def test_suite_categories(tmp_path, monkeypatch):
    good = _seed_dir(tmp_path, "FSU-GOOD", 1, suite=True)
    bad = _seed_dir(tmp_path, "FSU-BAD", 1, suite=True)
    miss = _seed_dir(tmp_path, "FSU-MISS", 1, suite=True)

    def fake_audit(seed_dir):
        if seed_dir == good:
            return _suite_report("current_verified", True,
                                 [_component(pid) for pid in
                                  ("gemm", "2mm", "lu", "cholesky",
                                   "jacobi-2d")])
        if seed_dir == bad:
            return _suite_report("current_verification_failed", False,
                                 [_component("gemm", ok=False)],
                                 violations=["identity: drift"])
        return _suite_report("missing_evidence", False,
                             [_component("gemm", missing=True)],
                             missing=["missing artifact"])
    monkeypatch.setattr(F.U, "audit_seed", fake_audit)
    report = F.build(tmp_path)
    by_run = {d["run_id"]: d for d in report["suite_seeds"]}
    assert by_run["FSU-GOOD"]["category"] == "current_verified"
    assert by_run["FSU-BAD"]["category"] == "current_verification_failed"
    assert by_run["FSU-MISS"]["category"] == "missing_evidence"
    assert report["summary"]["suite_seeds"]["current_verified"] == 1
    assert report["summary"]["components"]["current_verified"] == 5
    assert report["summary"]["components"][
        "current_verification_failed"] == 1
    assert report["summary"]["components"]["missing_evidence"] == 1
    assert report["tool_git_sha"]
    assert report["generated_at"]
    assert report["inputs"]["suite_configs_sha256"]


def test_non_suite_categories(tmp_path, monkeypatch):
    ok = _seed_dir(tmp_path, "FSU-OK", 1, suite=False)
    bad = _seed_dir(tmp_path, "FSU-NO", 1, suite=False)
    gone = tmp_path / "FSU-GONE" / "seed1"
    gone.mkdir(parents=True)
    (gone / "AUTHORITATIVE").write_text("attempt-1", encoding="utf-8")

    class Result:
        def __init__(self, ok):
            self.ok = ok

        def get(self, key, default=None):
            return {"ok": self.ok,
                    "failures": [] if self.ok else ["chain bad"]}.get(
                        key, default)

    monkeypatch.setattr(
        F.A, "audit_attempt",
        lambda attempt: Result("FSU-OK" in str(attempt)))
    monkeypatch.setattr(
        F.C, "check_stream",
        lambda path, run_id=None, sample_run_id=None: {
            "certified": run_id == "FSU-OK", "violations": [],
            "faults": {"1": {"certified": run_id == "FSU-OK"}}})
    report = F.build(tmp_path)
    by_run = {d["run_id"]: d for d in report["non_suite_seeds"]}
    assert by_run["FSU-OK"]["category"] == "current_verified"
    assert by_run["FSU-NO"]["category"] == "current_verification_failed"
    assert by_run["FSU-GONE"]["category"] == "missing_evidence"
    assert report["summary"]["non_suite_seeds"]["current_verified"] == 1
    assert report["summary"]["non_suite_seeds"][
        "current_verification_failed"] == 1
    assert report["summary"]["non_suite_seeds"]["missing_evidence"] == 1


def test_legacy_report_is_echoed_not_counted(tmp_path, monkeypatch):
    d = _seed_dir(tmp_path, "FSU-OLD", 1, suite=True)
    (d / "audit_v2.json").write_text(json.dumps({
        "schema_version": "fsu-suite-audit/v1",
        "tool_version": "fsu_fr03_suite_gate/v1",
        "suite_certified": True,
    }), encoding="utf-8")

    def fake_audit(seed_dir):
        return _suite_report("current_verification_failed", False,
                             [_component("gemm", ok=False)],
                             violations=["suite_hash drift"])
    monkeypatch.setattr(F.U, "audit_seed", fake_audit)
    report = F.build(tmp_path)
    detail = report["suite_seeds"][0]
    assert detail["category"] == "current_verification_failed"
    assert detail["legacy_audit_v2"]["suite_certified"] is True
    assert report["summary"]["suite_seeds"]["current_verified"] == 0


def test_markdown_lists_failures(tmp_path):
    report = {
        "schema_version": F.SCHEMA_VERSION,
        "generated_at": "now", "tool_git_sha": "deadbeef",
        "summary": {
            "suite_seeds": {"total": 1, "current_verified": 0,
                            "legacy_report_only": 0,
                            "current_verification_failed": 1,
                            "missing_evidence": 0},
            "components": {"total": 1, "current_verified": 0,
                           "legacy_report_only": 0,
                           "current_verification_failed": 1,
                           "missing_evidence": 0},
            "non_suite_seeds": {"total": 0, "current_verified": 0,
                                "legacy_report_only": 0,
                                "current_verification_failed": 0,
                                "missing_evidence": 0},
            "authoritative_seeds": {"total": 1, "current_verified": 0,
                                    "legacy_report_only": 0,
                                    "current_verification_failed": 1,
                                    "missing_evidence": 0},
        },
        "suite_seeds": [{
            "run_id": "FSU-X", "seed": "seed1",
            "category": "current_verification_failed",
            "reason": "drift", "violations": ["identity: x"],
            "missing_evidence": [], "components": [],
        }],
        "non_suite_seeds": [],
    }
    md = F.render_markdown(report)
    assert "FSU-X/seed1" in md
    assert "current_verification_failed" in md
    assert "identity: x" in md
