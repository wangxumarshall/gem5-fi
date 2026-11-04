"""tests/test_fsu_implementation_matrix.py — 阶段 B 实施矩阵完整性测试.

只读真实工作簿；不运行 gem5。
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_implementation_matrix as m
import fsu_index as I

ROOT = Path(__file__).resolve().parents[1]


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
                    "FSU-FP04-F2-W4": "3/3", "FSU-FP04-F1-W4": "3/3",
                    "FSU-FP04-F0-W3": "3/3",
                    "FSU-FP04-F0-W1": "3/3",
                    "FSU-FP04-F0-W5": "3/3",
                    "FSU-FP06-F5-W3": "3/3",
                    "FSU-FP06-F5-W1": "3/3",
                    "FSU-FP06-F5-W4": "3/3",
                    "FSU-FP06-F5-W5": "3/3",
                    "FSU-FR03-F5-W3": "2/3",
                    "FSU-FP04-F0-W6": "3/3",
                    "FSU-FP06-F5-W6": "3/3",
                    "FSU-FR03-F5-W5": "3/3",
                    "FSU-FR03-F5-W6": "3/3"}.get(r["runid"], "0/3")
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
    # seed 计数必须来自磁盘权威索引，而不是硬编码或 AUTHORITATIVE 文件存在。
    runids = I._load_runids(ROOT / "docs/gem5-fi/fsu/runids.json")
    _, idx_summary, _ = I.scan(runids, ROOT / "runs/fsu", None)
    assert summary["seed_completion_counts"] == \
        idx_summary["seed_completion_counts"]
    assert summary["seed_index"]["admitted_seeds_total"] == \
        idx_summary["admitted_seeds_total"]
    w1 = next(r for r in matrix if r["runid"] == "FSU-FP04-F0-W1")
    assert w1["seed_completion"] == "3/3"
    assert w1["workload_identity_status"] == "REAL"
    assert w1["coverage_status"] == "PARTIAL"
    assert "FP32" in w1["coverage_reason"] and "B0" in w1["coverage_reason"]
    assert summary["current_status"]["config_b0_match"] is True
    w3 = next(r for r in matrix if r["runid"] == "FSU-FP04-F0-W3")
    assert w3["seed_completion"] == "3/3"
    assert w3["coverage_status"] == "PARTIAL"
    assert "lane2" in w3["coverage_reason"]
    f3 = next(r for r in matrix if r["runid"] == "FSU-FP04-F3-W4")
    assert f3["seed_completion"] == "3/3"
    assert f3["coverage_status"] == "PARTIAL"
    assert "3/3" in f3["coverage_reason"] and "0/3 official" not in f3["coverage_reason"]
    expected = {
        "FSU-FP04-F1-W4": ("PARTIAL", "3/3"),
        "FSU-FP04-F0-W3": ("PARTIAL", "3/3"),
        "FSU-FP04-F0-W1": ("PARTIAL", "3/3"),
        # W1 now has a real FP-ScalarProbe artifact, so the workload-identity
        # blocker no longer applies; FR01's injector coverage remains PARTIAL.
        "FSU-FR01-F0-W1": ("PARTIAL", "0/3"),
        "FSU-FQ03-F0-W2": ("BLOCKED_NOT_IMPLEMENTED", "0/3"),
    }
    for rid, (status, seeds) in expected.items():
        r = next(x for x in matrix if x["runid"] == rid)
        assert r["coverage_status"] == status, (rid, r["coverage_status"])
        assert r["seed_completion"] == seeds


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


def test_f5_rows_and_capability_evidence():
    matrix, summary = m.build()
    by_id = {r["runid"]: r for r in matrix}
    assert by_id["FSU-FP06-F5-W3"]["seed_completion"] == "3/3"
    assert by_id["FSU-FP06-F5-W3"]["f5_readiness"] == "COMPLETE_3_OF_3"
    assert "FP06-d" in by_id["FSU-FP06-F5-W3"]["coverage_reason"]
    assert by_id["FSU-FP06-F5-W1"]["seed_completion"] == "3/3"
    assert by_id["FSU-FP06-F5-W1"]["f5_readiness"] == "COMPLETE_3_OF_3"
    assert by_id["FSU-FR03-F5-W3"]["f5_readiness"] == "PARTIAL_2_OF_3"
    for rid in ("FSU-FR03-F5-W5", "FSU-FR03-F5-W6"):
        assert by_id[rid]["f5_readiness"] == "COMPLETE_3_OF_3"
    cap = summary["capability_evidence"]
    assert cap["FP06"]["permanent_stuck"]["code_present"] is True
    assert cap["FP06"]["partial_product_proxy_fp06d"]["code_present"] is False
    # FR03-W3 已有正式 3/3 认证；W5/W6 仍不得借用该证据。
    assert cap["FR03"]["vec_stuck_write_path"]["certified"] is True
    assert cap["FR03"]["chaosphysreg_fsu_prop"]["certified"] is True
    assert cap["FR03"]["runner_chaosphysreg_path"]["certified"] is True
    assert cap["FR03"]["fr03_formal_seeds"]["certified"] is True


def test_generator_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "OUT", tmp_path)
    m.write_outputs(*m.build())
    first = {p.name: p.read_text(encoding="utf-8")
             for p in tmp_path.iterdir() if p.is_file()}
    m.write_outputs(*m.build())
    second = {p.name: p.read_text(encoding="utf-8")
              for p in tmp_path.iterdir() if p.is_file()}
    # 不写 generated_at；两次输出必须逐字节一致。
    assert first == second
    assert "generated_at" not in first["IMPLEMENTATION_MATRIX.json"]
    # JSON 中 capability_evidence 必须存在且含证据路径。
    data = json.loads(first["IMPLEMENTATION_MATRIX.json"])
    ev = data["summary"]["capability_evidence"]["FP06"]["chain_end"]
    assert ev["evidence"] and ev["evidence"][0]
