"""tests/test_fsu_implementation_matrix.py — 阶段 B 实施矩阵完整性测试.

只读真实工作簿；不运行 gem5。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_implementation_matrix as m


def test_matrix_shape_and_provenance():
    matrix, summary = m.build()
    assert len(matrix) == 173
    assert len({r["runid"] for r in matrix}) == 173
    assert all(r["runid"].startswith("FSU-") for r in matrix)
    assert summary["runid_count"] == 173
    assert summary["unique_runids"] == 173
    assert summary["sheet7_sheet9_sets_equal"] is True
    assert summary["model_count"] == 30


def test_model_status_is_conservative():
    _, summary = m.build()
    assert summary["implemented_runids"] == []
    assert summary["model_status_counts"] == {"PARTIAL": 13, "MISSING": 17}
    assert "IMPLEMENTED" not in summary["model_status_counts"]
    # 工作簿声称直接已有 FR01/FP04，审计必须降级为 PARTIAL
    assert summary["models"]["FR01"] == "PARTIAL"
    assert summary["models"]["FP04"] == "PARTIAL"


def test_every_runid_has_required_fields():
    matrix, _ = m.build()
    required = [
        "runid", "model_id", "unit", "freq", "load_id", "submodels",
        "eligible_condition", "attempted_definition", "eligible_definition",
        "activated_definition", "audited_status", "existing_injector",
        "missing_hooks", "real_workload_identity", "workload_identity_status",
        "golden_oracle", "required_l0_l5", "test_status", "three_seed_status",
        "seed_completion", "coverage_status", "coverage_reason", "blockers",
    ]
    for r in matrix:
        for k in required:
            assert k in r, (r["runid"], k)
            assert r[k] not in (None, "", []), (r["runid"], k)
        expected = {"FSU-FP04-F0-W4": "3/3", "FSU-FP04-F3-W4": "3/3",
                    "FSU-FP04-F2-W4": "1/3"}.get(r["runid"], "0/3")
        assert r["three_seed_status"] == expected
        assert r["seed_completion"] == expected
        assert r["audited_status"] in ("IMPLEMENTED", "PARTIAL", "MISSING")
        # 最初审计事实必须完整保留；当前 blocker 只列剩余缺口。
        assert len(r["baseline_blockers"]) >= 6
        assert len(r["blockers"]) >= 1
        assert isinstance(r["remaining_gaps"], list)
        assert isinstance(r["resolved_by_commit"], dict)


def test_seed_completion_and_coverage_status():
    matrix, summary = m.build()
    pilot = next(r for r in matrix if r["runid"] == "FSU-FP04-F0-W4")
    assert pilot["seed_completion"] == "3/3"
    assert pilot["coverage_status"] == "PILOT_SUBMODEL_ONLY"
    assert "FP04-c" in pilot["coverage_reason"]
    assert summary["seed_completion_counts"] == {"0/3": 170, "1/3": 1, "3/3": 2}
    f3 = next(r for r in matrix if r["runid"] == "FSU-FP04-F3-W4")
    assert f3["seed_completion"] == "3/3"
    assert f3["coverage_status"] == "PARTIAL"
    assert "3/3" in f3["coverage_reason"] and "0/3 official" not in f3["coverage_reason"]
    expected = {
        "FSU-FP04-F1-W4": "PARTIAL",
        "FSU-FR01-F0-W1": "BLOCKED_NO_TRUE_ARTIFACT",
        "FSU-FQ03-F0-W2": "BLOCKED_NOT_IMPLEMENTED",
    }
    for rid, status in expected.items():
        r = next(x for x in matrix if x["runid"] == rid)
        assert r["coverage_status"] == status, (rid, r["coverage_status"])
        assert r["seed_completion"] == "0/3"


def test_pilot_candidate_has_real_workload():
    matrix, summary = m.build()
    assert summary["pilot_candidates"] == ["FSU-FP04-F0-W4"]
    pilot = next(r for r in matrix if r["runid"] == "FSU-FP04-F0-W4")
    assert pilot["workload_identity_status"] == "REAL"
    assert "ARRAYHASH" in pilot["golden_oracle"]


def test_no_masked_misclassification():
    matrix, _ = m.build()
    for r in matrix:
        blob = (str(r["audited_status"]) + str(r["workbook_status_sheet10"])
                + str(r["workbook_status_sheet9"]))
        assert "Masked" not in blob


def test_baseline_and_current_status_are_separated():
    _, s = m.build()
    for key in ("baseline_gap", "current_status", "resolved_by_commit",
                "current_binary_sha256", "remaining_gaps"):
        assert key in s, key
    # 历史审计原文不得被删除。
    ids = {g["id"] for g in s["baseline_gap"]}
    assert {"gem5_binary_missing", "fsu_prop_evt_missing",
            "fsu_chain_auditor_missing",
            "fsu_three_seed_runner_missing"} <= ids
    # 已解决的缺口不得再出现在当前 blocker 中。
    remaining_ids = {g["id"] for g in s["remaining_gaps"]}
    assert "gem5_binary_missing" not in remaining_ids
    assert "fsu_prop_evt_missing" not in remaining_ids
    assert "fsu_chain_auditor_missing" not in remaining_ids
    assert "fsu_three_seed_runner_missing" not in remaining_ids
    # 当前二进制必须真实存在并有 SHA-256。
    bin_ = s["current_status"]["gem5_binary"]
    assert bin_["exists"] is True
    assert len(bin_["sha256"]) == 64
    assert s["current_binary_sha256"] == bin_["sha256"]
    # 已解决条目必须给出提交证据。
    for r in s["resolved_by_commit"]:
        assert r["resolved_by_commit"]
        assert r["evidence"]
