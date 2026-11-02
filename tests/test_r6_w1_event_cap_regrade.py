"""EVENT_CAP regrade: parse/count and loud refusals (no analysis needed)."""
import gzip
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
import regrade_r6_w1_event_cap as RG  # noqa: E402


def _seed(tmp_path, n_events, truncate=False):
    root = tmp_path / "S01-F2-W1_s1"
    inner = root / "S01-F2-W1"
    sd = inner / "seed1"
    sd.mkdir(parents=True)
    (root / "manifest.json").write_text(json.dumps(
        {"run_id": "S01-F2-W1", "seed": 1, "status": "FINISHED",
         "exit_code": 0, "binary_sha256": "x"}))
    (inner / "cell_results.json").write_text(json.dumps(
        {"runs": [{"chain": {}, "activated": 1}],
         "admission_status": "EVIDENCE-TRUNCATED"}))
    (sd / "chain_report.json").write_text(json.dumps(
        {"oracle_outcome": "Crash", "exit_code": 139,
         "truncated": True, "evidence_truncated": True, "admitted": False,
         "certified": False, "event_count": 200000}))
    (sd / "stats.txt").write_text("simTicks 1\n")
    p = sd / "prop_evt.txt.gz"
    with gzip.open(p, "wt") as f:
        f.write("# prop-evt v1: header\n")
        for i in range(n_events):
            f.write(f"PROP-EVT: kind=probe fault_id=1 event_id={i} "
                    f"parent_event_id=0 tick={i}\n")
        f.write("CONSUMER-SUMMARY: schema=1\n")
    if truncate:
        b = p.read_bytes()
        p.write_bytes(b[:-8])
    return str(root)


def test_count_prop_events_ignores_summaries(tmp_path):
    root = _seed(tmp_path, 7)
    p = os.path.join(root, "S01-F2-W1", "seed1", "prop_evt.txt.gz")
    assert RG.count_prop_events(p) == 7


def test_refuses_stream_under_cap(tmp_path):
    root = _seed(tmp_path, 3)
    rec = RG.regrade(root, apply=False)
    assert rec["status"] == "REFUSED"
    assert "<= cap" in rec["reason"]
    # nothing written
    assert not os.path.exists(os.path.join(
        root, "S01-F2-W1", "seed1", "chain_report.json.pre-capregrade-20261102"))


def test_refuses_incomplete_gzip(tmp_path):
    root = _seed(tmp_path, 3, truncate=True)
    rec = RG.regrade(root, apply=False)
    assert rec["status"] == "REFUSED"
    assert "gzip incomplete" in rec["reason"]


def test_apply_backs_up_original_before_overwrite(tmp_path, monkeypatch):
    """The seed-level backup must be the PRE-regrade report, not a copy of the
    file analyze() just wrote.  Regression: apply used to analyze() (which
    overwrites seed*/chain_report.json in place) before backup()."""
    root = _seed(tmp_path, 3)
    inner = os.path.join(root, "S01-F2-W1")
    sdir = os.path.join(inner, "seed1")
    # aggregate report the campaign wrote (holds the original sample)
    (open(os.path.join(inner, "chain_report.json"), "w")).write(json.dumps(
        {"runid": "S01-F2-W1", "samples": [json.load(open(
            os.path.join(sdir, "chain_report.json")))]}))
    original = open(os.path.join(sdir, "chain_report.json"), "rb").read()

    monkeypatch.setattr(RG, "count_prop_events", lambda p: 200001)
    monkeypatch.setattr(RG, "SUMMARY", str(tmp_path / "summary.jsonl"))
    monkeypatch.setattr(RG, "REGRADE_LOG", str(tmp_path / "regrade.jsonl"))

    def fake_analyze(outdir, runid, seed, oracle, exit_code, cap):
        # write_chain_report writes the new report into <outdir> = seed dir
        new = {"run_id": runid, "sample_run_id": "s1", "oracle_outcome": oracle,
               "exit_code": exit_code, "stream_present": True,
               "truncated": False, "evidence_truncated": False,
               "event_count": 200001, "faults": {}, "terminal": "full",
               "provable_to": "L5", "beyond": None, "summary": "new",
               "chain_valid": True, "admitted": True, "certified": True,
               "admission": {"admitted": True, "violations": []},
               "consumer_summary": [], "consumer_summary_accounting": {},
               "truncation_reason": ""}
        with open(os.path.join(outdir, "chain_report.json"), "w") as f:
            json.dump(new, f, indent=1)
        return new

    monkeypatch.setattr(RG, "analyze", fake_analyze)
    rec = RG.regrade(root, apply=True)
    assert rec["status"] == "APPLIED"

    pre = open(os.path.join(
        sdir, "chain_report.json.pre-capregrade-20261102"), "rb").read()
    assert pre == original, "backup must hold the original report"
    man = json.load(open(os.path.join(root, "manifest.json")))
    import hashlib
    assert man["chain_regrade"]["original_seed_chain_sha256"] == \
        hashlib.sha256(original).hexdigest()

    # a second apply on an already-regraded sample must refuse (never silently
    # overwrite the only backup with the newer report)
    rec2 = RG.regrade(root, apply=True)
    assert rec2["status"] == "REFUSED"
    assert "already regraded" in rec2["reason"]
