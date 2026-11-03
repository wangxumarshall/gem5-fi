"""tests/test_fsu_index.py — 三 seed 完成度索引测试。"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import fsu_index as I
import fsu_suite as S


def admitted(out_root, rid, seed, audit_ok=True):
    seed_dir = out_root / rid / f"seed{seed}"
    attempt = seed_dir / "attempt-1"
    attempt.mkdir(parents=True)
    (attempt / "chain_report.json").write_text(json.dumps({
        "run_id": rid, "seed": seed,
        "oracle": {"category": "SDC"},
        "chain": {"admitted_faults": ["1"],
                  "faults": {"1": {"admitted": True, "terminal": "full"}}},
    }), encoding="utf-8")
    (attempt / "audit.json").write_text(json.dumps({
        "ok": audit_ok, "certified": audit_ok,
    }), encoding="utf-8")
    (seed_dir / "AUTHORITATIVE").write_text(str(attempt), encoding="utf-8")


def failed(out_root, rid, seed):
    seed_dir = out_root / rid / f"seed{seed}"
    attempt = seed_dir / "attempt-1"
    attempt.mkdir(parents=True)
    (attempt / ".failed").write_text("no chain\n", encoding="utf-8")


def _suite_seed(out, rid, seed, broken_pid=None, audit_ok=True):
    """A valid W5 suite seed directory with 5 component attempts."""
    programs = []
    for i, pid in enumerate(S.PROGRAM_ORDER):
        programs.append({
            "program_id": pid, "program_index": i,
            "source_sha256": hashlib.sha256(("src:" + pid).encode()).hexdigest(),
            "binary_sha256": hashlib.sha256(("bin:" + pid).encode()).hexdigest(),
            "scale": {"N": 8}, "golden": f"{i + 1:016x}",
        })
    suite = {
        "suite_id": "index-suite-v1", "suite_version": "1",
        "program_order": list(S.PROGRAM_ORDER), "program_count": 5,
        "compiler": {"version": "test-gcc", "cflags": ["-O2"]},
        "oracle": {"version": "1", "kind": "exact_hash"},
        "programs": programs,
    }
    suite["suite_hash"] = S.compute_suite_hash(suite)
    seed_dir = out / rid / f"seed{seed}"
    cseeds = S.derive_component_seeds(seed, S.DEFAULT_COMPONENT_SEED_POLICY,
                                      suite["suite_id"],
                                      suite["suite_version"])
    comps = []
    for p in programs:
        pid = p["program_id"]
        attempt = (seed_dir / "components" / pid / rid /
                   f"seed{cseeds[pid]}" / "attempt-1")
        attempt.mkdir(parents=True)
        mp = attempt / "manifest.json"
        mp.write_text(json.dumps({"run_id": rid}), encoding="utf-8")
        golden_sha, _ = S.component_golden_sha256(p)
        status = "failed" if broken_pid == pid else "admitted"
        cm = {
            "suite_id": suite["suite_id"],
            "suite_version": suite["suite_version"],
            "suite_hash": suite["suite_hash"],
            "suite_seed": seed,
            "program_id": pid,
            "program_index": p["program_index"],
            "program_count": 5,
            "component_seed_policy_version": S.DEFAULT_COMPONENT_SEED_POLICY,
            "component_seed": cseeds[pid],
            "component_attempt": 1,
            "component_manifest_sha256": S.sha256_file(mp),
            "component_binary_sha256": p["binary_sha256"],
            "component_source_sha256": p["source_sha256"],
            "component_golden_sha256": golden_sha,
            "component_status": status,
            "component_eligible": 100,
            "component_activated": 1,
            "component_faults": 1,
            "component_terminal": "full",
            "component_oracle": "SDC",
            "component_audit_ok": status == "admitted",
            "component_certified": status == "admitted",
        }
        (attempt / "component_manifest.json").write_text(
            json.dumps(cm), encoding="utf-8")
        (attempt / "audit.json").write_text(json.dumps({
            "ok": status == "admitted",
            "certified": status == "admitted"}), encoding="utf-8")
        (attempt / "inject").mkdir()
        (attempt / "inject/array.bin").write_bytes(b"\x00" * 8)
        (attempt / "oracle_elements.json").write_text(
            json.dumps({"ok": True, "program_id": pid,
                        "mismatch_count": 0}), encoding="utf-8")
        (attempt / "evidence_sha256.json").write_text(json.dumps({
            "oracle_elements.json": S.sha256_file(
                attempt / "oracle_elements.json"),
            "inject/array.bin": S.sha256_file(attempt / "inject/array.bin"),
        }), encoding="utf-8")
        comps.append({**cm, "attempt": str(attempt)})
    (seed_dir / "suite_manifest.json").write_text(json.dumps({
        "suite": suite, "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "suite_hash": suite["suite_hash"], "suite_seed": seed,
        "run_id": rid, "program_order": list(S.PROGRAM_ORDER),
        "program_count": 5,
        "component_seed_policy_version": S.DEFAULT_COMPONENT_SEED_POLICY,
        "components": comps,
    }), encoding="utf-8")
    (seed_dir / "audit.json").write_text(
        json.dumps({"ok": audit_ok}), encoding="utf-8")
    return seed_dir


def test_suite_seed_counts_as_one_seed_not_five(tmp_path):
    out = tmp_path / "runs"
    rid = "FSU-AA01-F0-W5"
    _suite_seed(out, rid, 1)
    runids = tmp_path / "runids.json"
    runids.write_text(json.dumps({"runids": [{"RunID": rid}]}),
                      encoding="utf-8")
    summary, rows = I.write_index(I._load_runids(runids), out, runids, None)
    assert summary["admitted_seeds_total"] == 1        # not 5
    assert summary["suite_seed_dirs"] == 1
    assert summary["suite_seed_admitted"] == 1
    assert summary["component_runs_in_admitted_suites"] == 5
    assert rows[0]["admitted_seeds"] == 1
    assert rows[0]["seeds"][1]["state"] == "admitted"
    md = (out / "COMPLETE_PROPAGATION_PATHS" / "INDEX.md").read_text(
        encoding="utf-8")
    assert "suite seed（5 component run 只计 1 seed）" in md


def test_suite_seed_with_broken_component_not_counted(tmp_path):
    out = tmp_path / "runs"
    rid = "FSU-BB02-F0-W5"
    _suite_seed(out, rid, 1, broken_pid="2mm")
    runids = tmp_path / "runids.json"
    runids.write_text(json.dumps({"runids": [{"RunID": rid}]}),
                      encoding="utf-8")
    summary, rows = I.write_index(I._load_runids(runids), out, runids, None)
    assert summary["admitted_seeds_total"] == 0
    assert rows[0]["seeds"][1]["state"] != "admitted"


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


def test_index_requires_audit_ok(tmp_path):
    out = tmp_path / "runs"
    admitted(out, "FSU-AA01-F0-W1", 1)                 # audit ok → counted
    admitted(out, "FSU-BB02-F0-W3", 1, audit_ok=False)  # audit failed → invalid
    seed_dir = out / "FSU-CC03-F0-W4" / "seed1"
    seed_dir.mkdir(parents=True)
    (seed_dir / "AUTHORITATIVE").write_text("missing-attempt", encoding="utf-8")
    runids = tmp_path / "runids.json"
    runids.write_text(json.dumps({"runids": [
        {"RunID": "FSU-AA01-F0-W1"}, {"RunID": "FSU-BB02-F0-W3"},
        {"RunID": "FSU-CC03-F0-W4"}]}), encoding="utf-8")
    summary, rows = I.write_index(
        I._load_runids(runids), out, runids, None)
    by_id = {r["runid"]: r for r in rows}
    assert by_id["FSU-AA01-F0-W1"]["seeds"][1]["state"] == "admitted"
    assert by_id["FSU-BB02-F0-W3"]["seeds"][1]["state"] == "invalid"
    assert by_id["FSU-CC03-F0-W4"]["seeds"][1]["state"] == "invalid"
    assert summary["admitted_seeds_total"] == 1
