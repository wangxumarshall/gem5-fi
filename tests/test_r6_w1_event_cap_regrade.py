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
