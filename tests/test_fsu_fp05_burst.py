"""FP05 burst gate tests (offline; no gem5, no formal runs).

These tests exercise the contract validator with SYNTHETIC event streams.
They are not evidence that gem5 emits bursts: the real source check below
proves the opposite for the current tree (CHAOSFPU has no burst emitter), and
the gate must therefore return SKIP/BLOCKED, never PASS.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fsu_fp05_burst_gate as G  # noqa: E402


def ev(burst_id=None, ordinal=None, length=None, eligible=None,
       kind="fault_applied", model="FP05", **extra):
    d = {"kind": kind, "model_id": model, "fault_id": "1",
         "event_id": str(extra.pop("event_id", 0))}
    if burst_id is not None:
        d["burst_id"] = str(burst_id)
    if ordinal is not None:
        d["burst_ordinal"] = str(ordinal)
    if length is not None:
        d["burst_length"] = str(length)
    if eligible is not None:
        d["eligible_ordinal"] = str(eligible)
    d.update({k: str(v) for k, v in extra.items()})
    return d


def burst(burst_id, ordinals, length, eligible_start=100):
    return [ev(burst_id, o, length, eligible_start + o)
            for o in ordinals]


def status(events):
    return G.check_burst_stream(events)


def assert_status(report, expected, reason_contains=None):
    assert report["status"] == expected, json.dumps(report, indent=2)
    if reason_contains:
        assert reason_contains in report["reason"], report["reason"]


def test_valid_burst_len_2_3_4():
    for length in (2, 3, 4):
        rep = status(burst(7, range(length), length))
        assert_status(rep, "PASS")
        assert rep["burst_episode_count"] == 1
        assert rep["burst_event_count"] == length
        assert rep["recurring_event_count"] == 0
        assert rep["episodes"][0]["burst_id"] == 7


def test_two_valid_episodes_are_counted_separately():
    events = burst(1, range(2), 2, 10) + burst(2, range(3), 3, 20)
    rep = status(events)
    assert_status(rep, "PASS")
    assert rep["burst_episode_count"] == 2
    assert rep["burst_event_count"] == 5
    assert [e["burst_id"] for e in rep["episodes"]] == [1, 2]


def test_length_out_of_range_fails():
    # declared 5 with 5 events: a valid run of events but NOT an FP05 burst
    rep = status(burst(3, range(5), 5))
    assert_status(rep, "FAIL", "contract")


def test_declared_length_mismatch_fails():
    rep = status(burst(3, range(3), 4))
    assert_status(rep, "FAIL")


def test_duplicate_ordinal_fails():
    rep = status(burst(4, [0, 1, 1], 3))
    assert_status(rep, "FAIL")


def test_missing_ordinal_fails():
    rep = status(burst(4, [0, 2, 3], 3))
    assert_status(rep, "FAIL")


def test_out_of_order_ordinal_fails():
    rep = status(burst(4, [1, 0, 2], 3))
    assert_status(rep, "FAIL")


def test_cross_burst_id_mixing_fails():
    # Episode 1 is interrupted by episode 2 and resumes: the id reappears.
    events = [ev(10, 0, 2, 1), ev(11, 0, 2, 2),
              ev(10, 1, 2, 3), ev(11, 1, 2, 4)]
    rep = status(events)
    assert_status(rep, "FAIL", "reappears")


def test_identical_burst_ids_in_one_run_cannot_be_split():
    # Two sequential bursts that reuse the same id are indistinguishable from
    # one 4-event burst; the contract requires one id per episode.
    events = burst(5, range(2), 2, 10) + burst(5, range(2), 2, 20)
    rep = status(events)
    assert_status(rep, "FAIL")


def test_recurring_events_are_excluded_not_counted():
    events = burst(9, range(3), 3)
    events.append(ev(None, None, None, field="recurring_result_stuck"))
    events.append(ev(None, None, None, field="recurring_result_stuck"))
    rep = status(events)
    assert_status(rep, "PASS")
    assert rep["recurring_event_count"] == 2
    assert rep["burst_event_count"] == 3


def test_recurring_event_tagged_as_burst_fails():
    events = [ev(1, 0, 2, 1, field="recurring_result_stuck"),
              ev(1, 1, 2, 2, field="recurring_result_stuck")]
    rep = status(events)
    assert_status(rep, "FAIL", "recurring")
    # The failure is specifically that recurring is not a burst, not that the
    # ordinals were malformed.
    assert any(c["check"] == "recurring_not_burst_tagged"
               for c in rep["checks"])


def test_permanent_exposure_is_not_a_burst():
    events = [ev(kind="exposure", fixed_mask="0x1"),
              ev(kind="exposure", fixed_mask="0x1")]
    rep = status(events)
    assert_status(rep, "SKIP")
    assert rep["recurring_event_count"] == 2
    assert "burst_id" in rep["evidence_missing"]


def test_no_burst_events_is_skip_never_pass():
    # Normal FP05 per-event injections without burst tags: recurring_stuck
    # style per-event repetition is NOT the workbook burst.
    events = [ev(None, None, None, field="recurring_result_stuck")
              for _ in range(4)]
    rep = status(events)
    assert_status(rep, "SKIP")
    assert "burst_id" in rep["evidence_missing"]
    assert rep["burst_episode_count"] == 0


def test_empty_stream_is_skip():
    rep = status([])
    assert_status(rep, "SKIP")
    assert rep["evidence_missing"]


def test_mixed_tagged_and_untagged_fails():
    events = burst(2, range(2), 2) + [ev(None, None, None)]
    rep = status(events)
    assert_status(rep, "FAIL", "mixed burst tagging")


def test_other_model_events_are_filtered_out():
    events = burst(2, range(2), 2)
    other = ev(None, None, None, model="FP04")
    rep = status([other] + events)
    assert_status(rep, "PASS")
    assert rep["burst_event_count"] == 2


def test_other_model_only_is_skip():
    rep = status([ev(None, None, None, model="FP04")])
    assert_status(rep, "SKIP")


def test_partial_burst_tag_is_skip():
    events = [ev(2, 0, None, 1), ev(2, 1, None, 2)]
    rep = status(events)
    assert_status(rep, "SKIP")
    assert "burst_length" in rep["evidence_missing"]


def test_parse_stream_text_roundtrip():
    text = "\n".join([
        "# header",
        "PROP-EVT: kind=fault_applied model_id=FP05 burst_id=1 "
        "burst_ordinal=0 burst_length=2",
        "FSU_PROP-EVT: kind=fault_applied model_id=FP05 burst_id=1 "
        "burst_ordinal=1 burst_length=2",
        "",
    ])
    parsed = G.parse_stream_text(text)
    assert len(parsed) == 2
    assert parsed[0]["burst_id"] == "1"
    assert parsed[1]["burst_ordinal"] == "1"
    rep = status(parsed)
    assert_status(rep, "PASS")


def test_current_source_has_no_burst_emitter_and_gate_skips():
    source = G.check_source_support(ROOT)
    # TRUE for the current tree: the workbook itself records FP05 as partial
    # and F0-READINESS-ORDER.md says burst_id/ordinal are missing.
    assert source["implemented"] is False, source
    assert set(source["missing"]) == {"burst_id", "burst_ordinal",
                                      "burst_length"}
    rep = G.build_report(None, ROOT)
    assert rep["status"] == "SKIP"
    assert rep["blocked"] is True
    assert "burst_id" in rep["evidence_missing"]


def test_synthetic_burst_cannot_pass_against_a_burstless_source(tmp_path):
    stream = tmp_path / "events.txt"
    lines = ["PROP-EVT: kind=fault_applied model_id=FP05 burst_id=1 "
             "burst_ordinal=%d burst_length=2" % o for o in (0, 1)]
    stream.write_text("\n".join(lines) + "\n", encoding="utf-8")
    rep = G.build_report(stream, ROOT)
    # The validator itself accepts the synthetic stream...
    assert any(c["check"] == "ordinal_0_to_len_minus_1"
               and c["ok"] for c in rep["checks"])
    # ...but the gate fails closed because this source cannot emit it.
    assert rep["status"] == "FAIL"
    assert "no burst emitter" in rep["reason"]


def test_cli_exit_codes(tmp_path):
    stream = tmp_path / "events.txt"
    stream.write_text("PROP-EVT: kind=fault_applied model_id=FP05 "
                      "burst_id=1 burst_ordinal=0 burst_length=2\n",
                      encoding="utf-8")
    # source-only run: SKIP -> exit 2
    p = subprocess.run([sys.executable, str(ROOT / "tools/fsu_fp05_burst_gate.py"),
                        "--json"], capture_output=True, text=True)
    assert p.returncode == 2, p.stdout + p.stderr
    assert json.loads(p.stdout)["status"] == "SKIP"
    # explicit bad stream against the real tree: FAIL -> exit 1
    p = subprocess.run([sys.executable, str(ROOT / "tools/fsu_fp05_burst_gate.py"),
                        "--stream", str(stream), "--json"],
                       capture_output=True, text=True)
    assert p.returncode == 1, p.stdout + p.stderr
    assert json.loads(p.stdout)["status"] == "FAIL"
