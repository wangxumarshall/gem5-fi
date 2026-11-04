"""tests/test_fsu_reclassify_outcomes.py — .failed -> .real_outcome only.

The reclassification changes the tool marker, never the raw evidence, and
only when the CURRENT chain tool says the attempt has a real terminal.
"""
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_prop_fields as P  # noqa: E402
import fsu_reclassify_outcomes as R  # noqa: E402


def line(**kw):
    d = {k: "" for k in P.PROP_EVT_FIELDS}
    d.update(kw)
    return "PROP-EVT: " + " ".join(f"{k}={d[k]}" for k in P.PROP_EVT_FIELDS)


def make_attempt(tmp_path, terminal="not_consumed", truncated=False):
    attempt = tmp_path / "attempt-1"
    attempt.mkdir(parents=True)
    (attempt / "inject").mkdir()
    run = "R"
    sample = "s1"
    base = dict(run_id=run, sample_run_id=sample, fault_id="1",
                model_id="FR01", unit="PRF_Vec", freq="F0",
                reg_class="vec", phys_reg="34", reg_generation="1",
                lane_width="64", lane_offset="0", lane_mask="0x20",
                bit_indices="5", field="transient_bit_flip")
    lines = [
        line(kind="fault_applied", event_id="0", tick="10", activated="1",
             **base),
        line(kind="carrier_state", event_id="1", parent_event_id="0",
             tick="10", **base),
        line(kind="chain_end", event_id="2", parent_event_id="1",
             tick="100", terminal=terminal, **base),
    ]
    if truncated:
        lines.append("PROP-EVT: kind=bad")
    (attempt / "inject/prop_evt.txt.gz").write_bytes(
        gzip.compress(("\n".join(lines) + "\n").encode()))
    (attempt / "manifest.json").write_text(json.dumps({
        "run_id": run, "seed": 1, "sample_run_id": sample,
    }), encoding="utf-8")
    (attempt / "chain_report.json").write_text(json.dumps({
        "run_id": run, "seed": 1, "sample_run_id": sample,
        "oracle": {"category": "Masked"}, "chain": {},
    }), encoding="utf-8")
    (attempt / ".failed").write_text("not admitted\n", encoding="utf-8")
    return attempt


def test_failed_real_outcome_is_reclassified(tmp_path):
    attempt = make_attempt(tmp_path)
    res = R.reclassify(attempt)
    assert res["changed"] is True
    assert res["terminals"] == ["not_consumed"]
    assert (attempt / ".real_outcome").exists()
    assert not (attempt / ".failed").exists()
    assert (attempt / ".failed.historical").read_text(
        encoding="utf-8") == "not admitted\n"


def test_simulator_error_is_not_reclassified(tmp_path):
    attempt = make_attempt(tmp_path)
    rep = json.loads((attempt / "chain_report.json").read_text(
        encoding="utf-8"))
    rep["oracle"] = {"category": "SimulatorError"}
    (attempt / "chain_report.json").write_text(json.dumps(rep),
                                               encoding="utf-8")
    res = R.reclassify(attempt)
    assert res["changed"] is False
    assert (attempt / ".failed").exists()


def test_missing_evidence_is_not_reclassified(tmp_path):
    attempt = make_attempt(tmp_path)
    (attempt / "inject/prop_evt.txt.gz").unlink()
    res = R.reclassify(attempt)
    assert res["changed"] is False
    assert (attempt / ".failed").exists()
