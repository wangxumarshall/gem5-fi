#!/usr/bin/env python3
"""Tests for tools/lsu_v333_qualified.py (LSU v3.3.3, Agent D).

Every test builds a synthetic run dir under ``tmp_path`` that mirrors the real
evidence formats (summary.json, oracle.log, model logs, trace_v31.jsonl,
prop_trace.csv.gz).  Nothing is read from the historical audit trees, and no
value is supplied to the module that is not written into the synthetic dir:
the "no fabrication" test asserts that absent evidence stays ``None`` rather
than becoming ``0``/``PASS``.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import lsu_v333_qualified as qual  # noqa: E402

PROP_HEADER = (
    "# lsu-propagation v1: node_id,tick,ptag,kind,dyn_inst_seq,request_id,"
    "addr,phys_reg,arch_reg,detail\n")


def _prop_line(node, kind, dyn, detail, tick=1, ptag=1, req="", addr="", phys="", arch=""):
    return f"{node},{tick},{ptag},{kind},{dyn},{req},{addr},{phys},{arch},{detail}\n"


def _write_prop(path: Path, lines: list[str]) -> None:
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        fh.write(PROP_HEADER)
        for line in lines:
            fh.write(line)


def _write_truncated_gz(path: Path) -> None:
    payload = (PROP_HEADER + _prop_line(1, "lq_lifecycle", "10", "queue=LQ;action=alloc"))
    data = gzip.compress(payload.encode("utf-8"))
    path.write_bytes(data[: max(1, len(data) // 2)])


# ---------------------------------------------------------------------------
# synthetic A03
# ---------------------------------------------------------------------------

A03_LIFECYCLE = (
    "A03_STUCK_LIFECYCLE: fault_id=1;bit=3;mode=a03_bit3_stuck0_load;"
    "eligible_events=1;applications=1;already_stuck=0;activation_ordinal=1;"
    "activation_dyn_inst_seq=10;activation_pc=400500;first_affected_ordinal=1;"
    "first_affected_dyn_inst_seq=10;first_affected_pc=400500")
A03_ACTIVATION = "A03_ACTIVATION: tick=100;bit=3;mode=a03_bit3_stuck0_load"
A03_AFFECTED = (
    "A03_STREAM: event_ordinal=1;dyn_inst_seq=10;pc=400500;eligible=1;"
    "affected=1;golden_ea=4096;actual_ea=4104;bit=3;reason=STUCK_APPLIED")


def _a03_dir(tmp_path: Path, *, with_consumer: bool = True,
             with_activation: bool = True, affected: bool = True,
             with_trace: bool = True, with_checksum: bool = True) -> Path:
    d = tmp_path / "A03-complete"
    d.mkdir(parents=True, exist_ok=True)
    first_affected = (A03_AFFECTED if affected else
                      "A03_STREAM: event_ordinal=1;dyn_inst_seq=10;pc=400500;"
                      "eligible=1;affected=0;golden_ea=4096;actual_ea=4096;"
                      "bit=3;reason=ALREADY_STUCK")
    summary = {
        "model": "A03",
        "checksum": ("1111111111111111" if with_checksum else None),
        "a03": {
            "lifecycle": A03_LIFECYCLE,
            "first_activation": (A03_ACTIVATION if with_activation else None),
            "first_affected": first_affected,
            "watchdog_expired": True,
        },
        "watchdog_expired": True,
    }
    (d / "summary.json").write_text(json.dumps(summary))
    stdout = "A03_WATCHDOG_EXPIRED: tick=200 activated=1 stream_rows=1 " \
             "injected_applications=1\n"
    if with_checksum:
        stdout = "1111111111111111\n" + stdout
    (d / "stdout.log").write_text(stdout)
    (d / "oracle.log").write_text(
        "expected=2222222222222222 got=1111111111111111\nORACLE_FAIL\n")
    log = [first_affected, A03_LIFECYCLE]
    if with_activation:
        log.insert(0, A03_ACTIVATION)
    (d / "addrpath_injections.log").write_text("\n".join(log) + "\n")

    if with_trace:
        lines = [
            _prop_line(1, "resp", "10",
                       "data_hex=deadbeefdeadbeef;data_fnv=877efd17c26c35e9;"
                       "request_id=59"),
            _prop_line(2, "taint_reg", "10",
                       "arch_reg=2;phys_reg=46;writeback_value=147ae147ae148ace;"
                       "writeback_value_fnv=877efd17c26c35e9"),
            _prop_line(3, "prop_edge", "10",
                       "source_event_id=2;destination_event_id=4;"
                       "producer_inst_seq=10;consumer_inst_seq=11;"
                       "edge_type=register_dataflow"),
        ]
        if with_consumer:
            lines.append(_prop_line(5, "consumer", "11",
                                    "source_event_id=4;pc=400504;src_idx=0;"
                                    "consumer_input_fnv=258fbbfb0b770c98;"
                                    "commit_seq=99"))
        _write_prop(d / "prop_trace.csv.gz", lines)
    return d


def test_a03_complete_is_pass(tmp_path):
    r = qual.qualified_evidence("A03", _a03_dir(tmp_path))
    assert r["model"] == "A03"
    assert r["status"] == "PASS"
    assert r["required_fields"] == list(qual.A03_FIELDS)
    assert r["missing"] == []
    assert set(r["found"]) == set(qual.A03_FIELDS)
    assert "APPLICATION_CHECKSUM" in r["terminal_rule"]
    ev = r["evidence"]
    assert ev["application_checksum"] == "1111111111111111"
    assert ev["application_golden_checksum"] == "2222222222222222"
    assert "A03_WATCHDOG_EXPIRED" in ev["internal_watchdog_reason"]
    assert ev["trace_complete"] is True


def test_a03_three_events_are_distinct_and_all_required(tmp_path):
    """stuck-at active, selected-event activation and downstream affectation
    are separate records; dropping the activation must never yield PASS."""
    d = _a03_dir(tmp_path / "missing-activation", with_activation=False)
    (d / "addrpath_injections.log").write_text(A03_AFFECTED + "\n" + A03_LIFECYCLE + "\n")
    r = qual.qualified_evidence("A03", d)
    assert r["status"] != "PASS"
    assert "selected_event_first_activated" in r["missing"]
    assert "stuck_at_active" in r["found"]
    assert "first_downstream_instruction_affected" in r["found"]


def test_a03_without_downstream_affectation_never_pass(tmp_path):
    d = _a03_dir(tmp_path / "already-stuck", affected=False)
    r = qual.qualified_evidence("A03", d)
    assert r["status"] != "PASS"
    assert "first_downstream_instruction_affected" in r["missing"]
    assert r["evidence"]["first_affected_load_dyn_seq"] is None


def test_a03_missing_consumer_is_qualified(tmp_path):
    r = qual.qualified_evidence("A03", _a03_dir(tmp_path, with_consumer=False))
    assert r["status"] == "QUALIFIED"
    assert "consumer" in r["missing"]
    assert "load_result" in r["found"]
    assert "register_writeback" in r["found"]


def test_a03_absent_trace_is_trace_incomplete(tmp_path):
    r = qual.qualified_evidence("A03", _a03_dir(tmp_path, with_trace=False))
    assert r["status"] == "TRACE_INCOMPLETE"
    assert "load_result" in r["missing"]
    assert "register_writeback" in r["missing"]


def test_a03_missing_checksum_is_not_fabricated(tmp_path):
    r = qual.qualified_evidence("A03", _a03_dir(tmp_path, with_checksum=False))
    assert r["status"] != "PASS"
    assert "application_checksum" in r["missing"]
    assert r["evidence"]["application_checksum"] is None


# ---------------------------------------------------------------------------
# synthetic SP05
# ---------------------------------------------------------------------------

SP05_STORE_SEQ = "100"
SP05_DATA_FNV = "b6180e0c195fd2e9"


def _sp05_dir(tmp_path: Path, *, with_commit: bool = True,
              with_writeback: bool = True, with_trace: bool = True,
              store_data_fnv: str = SP05_DATA_FNV) -> Path:
    d = tmp_path / "SP05-complete"
    d.mkdir(parents=True, exist_ok=True)
    inj_detail = (
        f"site=writebackStores_prematureComplete;family=sp05;model=SP05;"
        f"store_seq={SP05_STORE_SEQ};store_pc=0x40053c;store_addr=0x4919f0;"
        f"sq_entry_id=956;sq_entry_generation=1306;store_data_fnv={store_data_fnv};"
        f"store_data_hex=6d7b78717e6b7d7f;store_data_len=8;mem_sent=0;"
        f"commit_tick=300;commit_tick_source=caller_supplied;eligible_ordinal=952")
    summary = {
        "model": "SP05",
        "first_injection": {"store_seq": SP05_STORE_SEQ, "detail": inj_detail},
        "injection_events": [{"store_seq": int(SP05_STORE_SEQ), "sq_idx": 956,
                              "mem_sent": 0, "complete_tick": 300}],
        "trace_completeness": {"trace_completeness": "COMPLETE",
                               "record_integrity": "VALID"},
        "oracle": False,
        "terminal": "SDC",
        "terminal_reason": "ORACLE_FAIL",
    }
    (d / "summary.json").write_text(json.dumps(summary))
    (d / "oracle.log").write_text(
        "expected=7df5034c23f3e703 got=c7a1b3a591c68328\nORACLE_FAIL\n")

    records = [
        {"event_type": "injection", "store_seq": SP05_STORE_SEQ, "detail": inj_detail},
        {"event_type": "sp05_stage", "store_seq": SP05_STORE_SEQ,
         "detail": (
             f"record=sp05_stage;family=sp05_complete;store_seq={SP05_STORE_SEQ};"
             f"sq_idx=956;gen=1306;completion_tick=300;commit_tick=300;"
             f"writeback_tick=310;write_skipped=0;mem_sent=1;reload_seq=101;"
             f"reload_data_hash=a8c7f832281a39c5;store_data_fnv={store_data_fnv};"
             f"data_correct=1;stage_outcome=RELOAD_MATCHES_STORE_DATA")},
        {"event_type": "memory_request", "detail": "request_id=73;size=8"},
        {"event_type": "memory_response", "detail": "request_id=73;response_id=1;data_fnv=a8c7f832281a39c5"},
        {"event_type": "register_writeback", "detail": "writeback_value_fnv=a8c7f832281a39c5"},
        {"event_type": "consumer_commit", "dyn_inst_seq": "101",
         "detail": "pc=0x400550;consumer_inst_seq=101;commit_seq=400"},
    ]
    if with_commit:
        records.insert(0, {
            "event_type": "store_commit", "store_seq": SP05_STORE_SEQ,
            "detail": (f"store_seq={SP05_STORE_SEQ};commit_tick=300;"
                       "commit_tick_source=model;commit_status=COMMITTED")})
    if with_writeback:
        records.insert(1, {
            "event_type": "store_writeback", "store_seq": SP05_STORE_SEQ,
            "detail": f"store_seq={SP05_STORE_SEQ};writeback_tick=310;mem_sent=1"})
    if with_trace:
        with (d / "trace_v31.jsonl").open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec) + "\n")
    return d


def test_sp05_complete_is_pass(tmp_path):
    r = qual.qualified_evidence("SP05", _sp05_dir(tmp_path))
    assert r["status"] == "PASS"
    assert r["required_fields"] == list(qual.SP05_FIELDS)
    assert r["missing"] == []
    ev = r["evidence"]
    assert ev["store_dyn_seq"] == SP05_STORE_SEQ
    assert ev["store_data_hash"] == SP05_DATA_FNV
    assert ev["store_pc"] == "0x40053c"
    assert ev["commit_event"] is not None
    assert ev["writeback_event"] is not None
    assert "ORACLE_FAIL_SDC" in r["terminal_rule"]


def test_sp05_missing_writeback_event_is_qualified(tmp_path):
    r = qual.qualified_evidence("SP05", _sp05_dir(tmp_path, with_writeback=False))
    assert r["status"] == "QUALIFIED"
    assert r["missing"] == ["writeback_event"]
    assert "STORE_WRITEBACK_ABSENT" in r["terminal_rule"]


def test_sp05_missing_commit_event_is_qualified(tmp_path):
    r = qual.qualified_evidence("SP05", _sp05_dir(tmp_path, with_commit=False))
    assert r["status"] == "QUALIFIED"
    assert "commit_event" in r["missing"]
    assert "STORE_COMMIT_ABSENT" in r["terminal_rule"]


def test_sp05_null_store_data_hash_is_qualified(tmp_path):
    r = qual.qualified_evidence("SP05", _sp05_dir(tmp_path, store_data_fnv="null"))
    assert r["status"] == "QUALIFIED"
    assert "store_data_hash" in r["missing"]
    assert r["evidence"]["store_data_hash"] is None


def test_sp05_absent_trace_is_trace_incomplete(tmp_path):
    r = qual.qualified_evidence("SP05", _sp05_dir(tmp_path, with_trace=False))
    assert r["status"] == "TRACE_INCOMPLETE"


# ---------------------------------------------------------------------------
# synthetic RP01
# ---------------------------------------------------------------------------

RP01_ELIGIBLE = (
    "RP01_ELIGIBLE ordinal=1 load_seq=100 load_pc=4195600 lq_idx=7 lq_gen=3 "
    "store_seq=99 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=0 "
    "in_instsToReplay_post=1 tick=100")
RP01_SKIP = (
    "RP01_SKIP_REPLAY ordinal=5 load_seq=140 load_pc=4195600 lq_idx=11 lq_gen=4 "
    "store_seq=139 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=1 "
    "in_instsToReplay_post=0 tick=200")


def _rp01_dir(tmp_path: Path, *, watchdog: bool = False, timed_out: bool = False,
              with_skip: bool = True, with_trace: bool = True,
              truncated_trace: bool = False) -> Path:
    d = tmp_path / "RP01-complete"
    d.mkdir(parents=True, exist_ok=True)
    summary = {
        "model": "RP01",
        "timed_out": timed_out,
        "terminal": "HANG_WATCHDOG" if watchdog else "COMPLETED",
        "terminal_reason": ("INTERNAL_WATCHDOG_DEADLINE" if watchdog
                            else "APPLICATION_COMPLETED"),
        "rp01": {
            "eligible": 5,
            "skips": 1,
            "watchdog": watchdog,
            "first_eligible": RP01_ELIGIBLE,
            "first_skip": (RP01_SKIP if with_skip else None),
            "watchdog_marker": ("CHAOS_RP01_WATCHDOG=EXPIRED fired=1" if watchdog
                                else None),
        },
    }
    (d / "summary.json").write_text(json.dumps(summary))
    log = [RP01_ELIGIBLE]
    if with_skip:
        log.append(RP01_SKIP)
    if watchdog:
        log.append("CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 eligible=5 tick=900")
    (d / "lsq_fwd_injections.log").write_text("\n".join(log) + "\n")

    if with_trace:
        if truncated_trace:
            _write_truncated_gz(d / "prop_trace.csv.gz")
        else:
            _write_prop(d / "prop_trace.csv.gz", [
                _prop_line(1, "lq_lifecycle", "10", "queue=LQ;action=alloc"),
            ])
    return d


def test_rp01_complete_is_pass(tmp_path):
    r = qual.qualified_evidence("RP01", _rp01_dir(tmp_path))
    assert r["status"] == "PASS"
    assert r["missing"] == []
    assert r["terminal_rule"] == "NORMAL"
    ev = r["evidence"]
    assert ev["dyn_seq"] == "140"
    assert "lq_idx=11" in ev["lq_sq_entry"]
    assert "replay_gen_post=1" in ev["faulty_replay_state"]


def test_rp01_internal_watchdog_is_trace_incomplete(tmp_path):
    r = qual.qualified_evidence(
        "RP01", _rp01_dir(tmp_path, watchdog=True, truncated_trace=True))
    assert r["status"] == "TRACE_INCOMPLETE"
    assert r["terminal_rule"] == "MODEL_INTERNAL_WATCHDOG"
    assert r["missing"] == []


def test_rp01_external_timeout_is_classified(tmp_path):
    r = qual.qualified_evidence(
        "RP01", _rp01_dir(tmp_path, timed_out=True, truncated_trace=True))
    assert r["status"] == "TRACE_INCOMPLETE"
    assert r["terminal_rule"] == "EXTERNAL_TIMEOUT"


def test_rp01_missing_skip_record_is_qualified(tmp_path):
    r = qual.qualified_evidence("RP01", _rp01_dir(tmp_path, with_skip=False))
    assert r["status"] == "QUALIFIED"
    assert "replay_skip" in r["missing"]
    assert "replay_decision" in r["missing"]
    assert "dyn_seq" in r["missing"]
    assert r["evidence"]["dyn_seq"] is None


# ---------------------------------------------------------------------------
# non-qualified models, interface shape and never-upgrade invariant
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("model", ["A01", "FW02", "SQ03", "MD04", "LQ04"])
def test_non_qualified_models_return_pass_without_rules(model):
    # The run dir does not even exist: no read happens for these models.
    r = qual.qualified_evidence(model, Path("/nonexistent/run/dir"))
    assert r == {
        "model": model,
        "required_fields": [],
        "found": [],
        "missing": [],
        "status": "PASS",
        "terminal_rule": "NO_EXTRA_RULES",
        "evidence": r["evidence"],
    }
    assert "note" in r["evidence"]


def test_missing_run_dir_is_trace_incomplete_not_pass(tmp_path):
    r = qual.qualified_evidence("A03", tmp_path / "absent")
    assert r["status"] == "TRACE_INCOMPLETE"
    assert r["missing"] == list(qual.A03_FIELDS)
    assert all(v is None or isinstance(v, (str, bool, int)) for v in r["evidence"].values())


def test_never_upgrade_non_pass(tmp_path):
    cases = [
        ("A03", _a03_dir(tmp_path / "a03-no-consumer", with_consumer=False), "QUALIFIED"),
        ("A03", _a03_dir(tmp_path / "a03-no-trace", with_trace=False), "TRACE_INCOMPLETE"),
        ("SP05", _sp05_dir(tmp_path / "sp05-no-wb", with_writeback=False), "QUALIFIED"),
        ("SP05", _sp05_dir(tmp_path / "sp05-no-trace", with_trace=False), "TRACE_INCOMPLETE"),
        ("RP01", _rp01_dir(tmp_path / "rp01-watchdog", watchdog=True,
                           truncated_trace=True), "TRACE_INCOMPLETE"),
    ]
    for model, run_dir, expected in cases:
        r = qual.qualified_evidence(model, run_dir)
        assert r["status"] == expected
        assert r["status"] != "PASS"


def test_return_keys_are_exact(tmp_path):
    r = qual.qualified_evidence("A03", _a03_dir(tmp_path))
    assert set(r) == {"model", "required_fields", "found", "missing",
                      "status", "terminal_rule", "evidence"}
