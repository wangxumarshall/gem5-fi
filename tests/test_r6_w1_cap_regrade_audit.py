"""EVENT_CAP regrade audit: original recovery, allowed diff, provenance."""
import gzip
import hashlib
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
import audit_r6_w1_cap_regrade as AU  # noqa: E402

STAMP = "20261102"


def _write_evt(path, n):
    with gzip.open(path, "wt") as f:
        f.write("# prop-evt v1: header\n")
        for i in range(n):
            f.write("PROP-EVT: kind=probe fault_id=1 event_id=%d "
                    "parent_event_id=0 tick=%d\n" % (i, i))


def _fixture(tmp_path, wrong_sha=False, illegal_change=False):
    root = tmp_path / "S01-F2-W1_s1"
    inner = root / "S01-F2-W1"
    sdir = inner / "seed1"
    sdir.mkdir(parents=True)
    base = {
        "run_id": "S01-F2-W1", "sample_run_id": "s1",
        "oracle_outcome": "Crash", "exit_code": 139,
        "stream_present": True, "truncated": True,
        "evidence_truncated": True, "event_count": 200000, "faults": {},
        "terminal": "full", "provable_to": "L5", "beyond": None,
        "summary": "old", "chain_valid": False, "admitted": False,
        "certified": False, "admission": {"admitted": False, "violations": []},
        "consumer_summary": [], "consumer_summary_accounting":
            {"conservation": "ok"}, "truncation_reason": "cap",
    }
    original = dict(base)
    new = dict(base)
    new.update({"truncated": False, "evidence_truncated": False,
                "event_count": 5, "chain_valid": True, "admitted": True,
                "certified": True,
                "admission": {"admitted": True, "violations": []},
                "faults": {"f1": {"terminal": "full", "provable_to": "L5"}},
                "summary": "new", "truncation_reason": ""})
    if illegal_change:
        new["oracle_outcome"] = "SDC"
    canon = json.dumps(original, indent=1, ensure_ascii=False).encode()

    (sdir / "chain_report.json").write_text(
        json.dumps(new, indent=1, ensure_ascii=False))
    (inner / f"chain_report.json.pre-capregrade-{STAMP}").write_text(
        json.dumps({"runid": "S01-F2-W1", "samples": [original]}, indent=1))
    # simulate the pre-fix ordering defect: seed backup == new report
    (sdir / f"chain_report.json.pre-capregrade-{STAMP}").write_text(
        json.dumps(new, indent=1, ensure_ascii=False))
    (inner / f"cell_results.json.pre-capregrade-{STAMP}").write_text("{}")
    (root / f"manifest.json.pre-capregrade-{STAMP}").write_text("{}")

    _write_evt(sdir / "prop_evt.txt.gz", 5)
    _write_evt(sdir / "prop_trace.csv.gz", 0)
    (sdir / "stats.txt").write_text("simTicks 1\n")
    old = "0" * 64 if wrong_sha else hashlib.sha256(canon).hexdigest()
    (root / "manifest.json").write_text(json.dumps({
        "run_id": "S01-F2-W1", "seed": 1,
        "chain_regrade": {"events": 5, "orig_seed_sha": old,
                          "original_seed_chain_sha256": old}}))
    # evidence older than the backup, backup newer
    for p in ("prop_evt.txt.gz", "prop_trace.csv.gz", "stats.txt"):
        os.utime(sdir / p, (1_700_000_000, 1_700_000_000))
    os.utime(root / f"manifest.json.pre-capregrade-{STAMP}",
             (1_700_000_100, 1_700_000_100))
    return str(root), canon


def test_audit_passes_and_recovers_original(tmp_path):
    root, canon = _fixture(tmp_path)
    rec = AU.audit(root)
    assert rec["pass"], rec["errors"]
    assert rec["reconstructed_original_seed_sha256"] == \
        hashlib.sha256(canon).hexdigest()
    assert rec["seed_backup_is_original"] is False
    assert any("ordering defect" in w for w in rec["warnings"])


def test_audit_refuses_non_cap_change(tmp_path):
    root, _ = _fixture(tmp_path, illegal_change=True)
    rec = AU.audit(root)
    assert not rec["pass"]
    assert any("non-cap fields changed" in e for e in rec["errors"])


def test_audit_fixes_wrong_provenance(tmp_path):
    root, canon = _fixture(tmp_path, wrong_sha=True)
    rec = AU.audit(root)
    assert not rec["pass"]
    rec = AU.audit(root, apply_fix=True)
    assert rec["pass"], rec["errors"]
    man = json.load(open(os.path.join(root, "manifest.json")))
    reg = man["chain_regrade"]
    assert reg["original_seed_chain_sha256"] == \
        hashlib.sha256(canon).hexdigest()
    assert reg["original_seed_chain_sha256_corrected_from"] == "0" * 64
    assert "original_seed_chain_reconstructed_from" in reg
