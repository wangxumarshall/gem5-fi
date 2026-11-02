"""tests/test_fsu_index.py — 三 seed 完成度索引测试。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_index as I


def admitted(out_root, rid, seed):
    seed_dir = out_root / rid / f"seed{seed}"
    attempt = seed_dir / "attempt-1"
    attempt.mkdir(parents=True)
    (attempt / "chain_report.json").write_text(json.dumps({
        "run_id": rid, "seed": seed,
        "oracle": {"category": "SDC"},
        "chain": {"admitted_faults": ["1"],
                  "faults": {"1": {"admitted": True, "terminal": "full"}}},
    }), encoding="utf-8")
    (seed_dir / "AUTHORITATIVE").write_text(str(attempt), encoding="utf-8")


def failed(out_root, rid, seed):
    seed_dir = out_root / rid / f"seed{seed}"
    attempt = seed_dir / "attempt-1"
    attempt.mkdir(parents=True)
    (attempt / ".failed").write_text("no chain\n", encoding="utf-8")


def test_index_counts(tmp_path):
    out = tmp_path / "runs"
    for s in (1, 2, 3):
        admitted(out, "FSU-AA01-F0-W1", s)
    admitted(out, "FSU-AA01-F2-W2", 1)
    failed(out, "FSU-AA01-F2-W2", 2)
    runids = tmp_path / "runids.json"
    runids.write_text(json.dumps({"runids": [
        {"RunID": "FSU-AA01-F0-W1"},
        {"RunID": "FSU-AA01-F2-W2"},
        {"RunID": "FSU-BB02-F0-W3"},
    ]}), encoding="utf-8")
    matrix = tmp_path / "matrix.json"
    matrix.write_text(json.dumps({"runids": [
        {"runid": "FSU-AA01-F0-W1", "coverage_status": "PILOT_SUBMODEL_ONLY",
         "coverage_reason": "pilot only"},
        {"runid": "FSU-AA01-F2-W2", "coverage_status": "PARTIAL",
         "coverage_reason": "partial"},
        {"runid": "FSU-BB02-F0-W3", "coverage_status": "BLOCKED_NOT_IMPLEMENTED",
         "coverage_reason": "missing"},
    ]}), encoding="utf-8")
    summary, rows = I.write_index(
        I._load_runids(runids), out, runids, matrix)
    assert summary["total_runids"] == 3
    assert summary["complete_3_of_3"] == 1
    assert summary["with_1_of_3"] == 1
    assert summary["with_0_of_3"] == 1
    assert summary["admitted_seeds_total"] == 4
    assert summary["target_seeds"] == 9
    assert summary["seed_completion_counts"] == {"0/3": 1, "1/3": 1, "3/3": 1}
    assert summary["coverage_status_counts"] == {
        "PILOT_SUBMODEL_ONLY": 1, "PARTIAL": 1,
        "BLOCKED_NOT_IMPLEMENTED": 1}
    cr = out / "COMPLETE_PROPAGATION_PATHS"
    for f in ("INDEX.json", "INDEX.md", "README.md"):
        assert (cr / f).exists()
    md = (cr / "INDEX.md").read_text(encoding="utf-8")
    assert "COMPLETE_3_OF_3" in md and "PARTIAL_1_OF_3" in md
    assert "✅" in md and "❌" in md and "—" in md
    assert "PILOT_SUBMODEL_ONLY" in md and "BLOCKED_NOT_IMPLEMENTED" in md
