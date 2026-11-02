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
        "blockers",
    ]
    for r in matrix:
        for k in required:
            assert k in r, (r["runid"], k)
            assert r[k] not in (None, "", []), (r["runid"], k)
        assert r["three_seed_status"] == "0/3"
        assert r["audited_status"] in ("IMPLEMENTED", "PARTIAL", "MISSING")
        assert hasattr(r["blockers"], "__len__") and len(r["blockers"]) >= 5


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
