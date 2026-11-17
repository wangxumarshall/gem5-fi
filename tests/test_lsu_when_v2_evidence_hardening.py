"""Unit tests for the LSU When-v2 evidence-hardening rules (v3.3.4).

These pin the failure modes this round removed:

* a foreign squash/commit in the same trace is never attached to the target;
* the injection is chosen by the census target seq, not "last in the file";
* a no-change stuck-at target is a documented limitation, not a full chain;
* RP01 never auto-passes on an injection + replay marker alone;
* SQ01's load-only stages are N/A (not missing) on a forwarding path;
* the strict gates reject a boundary whose seq is not the target.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
RUNNER = ROOT.parent / "runner"
sys.path.insert(0, str(PLATFORM))
sys.path.insert(0, str(PLATFORM / "tools"))
sys.path.insert(0, str(RUNNER))

from trace_writer import TraceWriter, TraceWriteError  # noqa: E402
from trace_completeness import (check_completeness,  # noqa: E402
                                normalize_terminal,
                                select_target_injection)
import evidence_hardening as eh  # noqa: E402
import acceptance_hardened as ah  # noqa: E402


def _event(w, etype, seq, tick, *, ptag=1, detail="", **kw):
    base = dict(ptag=ptag, dyn_inst_seq=seq, timestamp=tick, detail=detail,
                trace_completeness="COMPLETE")
    base.update(kw)
    return w.event(etype, **base)


def _load_chain(path: Path, seq=100, foreign_squash=True):
    w = TraceWriter(path, "T", "T", "T", "A01", "A01")
    inj = _event(w, "injection", seq, 10, injection_status="INJECTED",
                 activation_status="TRIGGERED",
                 detail="site=lsq_pushRequest_PRE;value_changed=1")
    _event(w, "address_formed", seq, 11)
    req = _event(w, "memory_request", seq, 20, request_id=7)
    resp = _event(w, "memory_response", seq, 30, request_id=7,
                  detail="family=addrpath;data_fnv=aa")
    _event(w, "register_writeback", seq, 31, source_event_id=resp,
           detail="writeback_value_fnv=aa")
    _event(w, "consumer_commit", 101, 40, source_event_id=resp,
           detail="consumer_input_fnv=aa")
    _event(w, "commit", seq, 50, ptag=0, commit_status="COMMITTED")
    if foreign_squash:
        _event(w, "squash", 999, 60, ptag=0, squash_status="SQUASHED")
    w.close(run_status="COMPLETED", activation="TRIGGERED", terminal="SDC",
            completeness="COMPLETE")
    return inj


def test_foreign_squash_is_never_attached(tmp_path):
    path = tmp_path / "trace_v31.jsonl"
    _load_chain(path, seq=100, foreign_squash=True)
    target = {"dyn_inst_seq": 100, "seq_set": [100]}
    report = check_completeness(path, target=target, hardened=True)
    assert report["target_squash_event_ids"] == []
    assert report["foreign_squash_events"] >= 1
    assert report["dimensions"]["identity_linkage"] == "PASS"
    assert report["dimensions"]["architectural_boundary"] == "TARGET_COMMIT"


def test_injection_selected_by_target_not_position(tmp_path):
    path = tmp_path / "trace_v31.jsonl"
    w = TraceWriter(path, "T", "T", "T", "A01", "A01")
    _event(w, "injection", 100, 10, injection_status="INJECTED")
    _event(w, "injection", 200, 20, injection_status="INJECTED")
    _event(w, "injection_nochange", 300, 30, injection_status="NO_CHANGE")
    w.close(run_status="COMPLETED", activation="TRIGGERED", terminal="SDC",
            completeness="COMPLETE")
    events, _, _ = eh.read_records(path)
    injs = [e for e in events if e.get("event_type") in
            ("injection", "injection_nochange")]
    picked = select_target_injection(injs, {"dyn_inst_seq": 100,
                                            "seq_set": [100]})
    assert picked["dyn_inst_seq"] == 100


def test_terminal_alias_prevents_writer_failure(tmp_path):
    # The old runner passed NO_VISIBLE_MISMATCH straight to the writer, which
    # raised and left a trace without a summary (the 82 INCOMPLETE runs).
    assert normalize_terminal("NO_VISIBLE_MISMATCH") == "MASKED"
    assert normalize_terminal("HANG_WATCHDOG") == "HANG"
    assert eh.SCHEMA_TERMINAL["NO_VISIBLE_MISMATCH"] == "MASKED"
    path = tmp_path / "t.jsonl"
    w = TraceWriter(path, "T", "T", "T", "A01", "A01")
    with pytest.raises(TraceWriteError):
        w.close(run_status="COMPLETED", activation="TRIGGERED",
                terminal="NO_VISIBLE_MISMATCH", completeness="COMPLETE")


def test_boundary_bound_only_by_target_seq():
    events = [
        {"event_id": 1, "event_type": "commit", "dyn_inst_seq": 100,
         "detail": ""},
        {"event_id": 2, "event_type": "squash", "dyn_inst_seq": 999,
         "detail": ""},
    ]
    ids = {"target_seq": 100, "seq_set": [100]}
    b = eh.build_boundary(events, ids, "A01")
    assert b["boundary_class"] == "TARGET_COMMIT"
    assert b["target_commit"][0]["event_id"] == 1
    assert b["target_squash"] == []
    assert b["foreign_squash_count"] == 1


def test_lq_free_reason_commit_is_architectural_commit():
    events = [{
        "event_id": 5, "event_type": "lq_lifecycle", "dyn_inst_seq": 100,
        "detail": "queue=LQ;action=free;index=3;generation=4;reason=commit"}]
    b = eh.build_boundary(events, {"target_seq": 100, "seq_set": [100]},
                          "A03")
    assert b["boundary_class"] == "TARGET_COMMIT_LQ_FREE"
    assert b["target_lq_commit"][0]["event_id"] == 5
    assert eh.classify({"terminal": "NO_VISIBLE_MISMATCH",
                        "oracle_pass": True}, {}, {"event_type": "injection"},
                       b) == "COMMITTED_NO_VISIBLE_MISMATCH"


def test_a03_nochange_target_is_documented_limitation():
    st = {"terminal": "SDC", "oracle_pass": False, "model": "A03",
          "injection_count": 1}
    ids = {"target_seq": 100, "seq_set": [100], "target_role": "load"}
    events = [{
        "event_id": 1, "event_type": "injection_nochange",
        "dyn_inst_seq": 100, "injection_status": "NO_CHANGE", "ptag": 0,
        "detail": "site=lsq_pushRequest_PRE;value_changed=0"},
        {"event_id": 2, "event_type": "injection_stream",
         "dyn_inst_seq": 100, "activation_status": "TRIGGERED",
         "detail": "affected=0;reason=ALREADY_STUCK"}]
    inj = eh.pick_injection(events, ids)
    a03 = eh.a03_semantics(events[1], inj, st)
    g = eh.grade(st, ids, events, inj, {"dimensions": {}}, {
        "boundary_class": "OTHER_INSTRUCTION_ONLY", "target_commit": [],
        "target_lq_commit": [], "target_squash": [], "target_replay": []},
        a03, None, None)
    assert a03["target_value_unchanged"] is True
    assert g["status"] == "COMPLETE_WITH_DOCUMENTED_LIMITATION"


def test_rp01_never_autopasses_on_injection_plus_replay():
    rec = {"ModelID": "RP01", "StructuralChainCompleteness": "COMPLETE",
           "BoundaryEvidence": {"boundary_class": "TARGET_STALL_WATCHDOG"},
           "InjectionEffectiveEvidence": {"rp01": {"checks": {
               "A_injection_effective": True,
               "B_microarch_state": True,
               "C_replay_not_rescheduled": True,
               "D_pipeline_no_progress": False,
               "E_watchdog_terminal": True}}}}
    # G11 (chain evidence) must fail: the watchdog boundary alone is not a
    # completed causal chain.
    status, _ = ah.edge_ok(rec)
    assert status == "FAIL"
    # G12 is narrower: the watchdog boundary itself is real (terminal + id).
    ok, _ = ah.boundary_ok(rec)
    assert ok is True
    # Only the full A-E set passes G11.
    rec["InjectionEffectiveEvidence"]["rp01"]["checks"][
        "D_pipeline_no_progress"] = True
    assert ah.edge_ok(rec)[0] == "PASS"


def test_sq01_memory_response_is_na_on_forwarding_path():
    ids = {"target_seq": 7577, "seq_set": [7577], "target_role": "store"}
    events = [
        {"event_id": 1, "event_type": "injection", "dyn_inst_seq": 7577,
         "injection_status": "INJECTED", "ptag": 1, "detail": ""},
        {"event_id": 2, "event_type": "store_writeback", "dyn_inst_seq": 7577,
         "ptag": 1, "detail": ""},
        {"event_id": 3, "event_type": "commit", "dyn_inst_seq": 7577,
         "ptag": 0, "detail": ""},
        {"event_id": 4, "event_type": "forwarding_decision",
         "dyn_inst_seq": 7578, "ptag": 1,
         "detail": "load_seq=7578;store_seq=7577;decision=forwarded;"
                   "store_data_forwarded=1"},
        {"event_id": 5, "event_type": "lq_lifecycle", "dyn_inst_seq": 7578,
         "ptag": 0,
         "detail": "queue=LQ;action=free;index=1;generation=2;reason=commit"},
        {"event_id": 6, "event_type": "chain_verdict", "dyn_inst_seq": 7577,
         "ptag": 1,
         "detail": "chain_verdict=STORE_COMMITTED_LANE_NOT_READ;"
                   "reload_seq=0;consumer_seq=0"},
    ]
    sq = eh.sq01_evidence({"outdir": "/tmp"}, events, ids)
    inj = eh.pick_injection(events, ids)
    b = eh.build_boundary(events, ids, "SQ01")
    g = eh.grade({"terminal": "SDC", "oracle_pass": False, "model": "SQ01"},
                 ids, events, inj, {"dimensions": {}}, b, None, None, sq)
    assert "memory_response" in g["na"]
    assert "memory_response" not in g["missing"]
    assert sq["consumer_load_seqs"] == [7578]
    assert g["status"] == "COMPLETE_WITH_DOCUMENTED_LIMITATION"


def test_gate12_rejects_foreign_boundary_seq():
    rec = {
        "ModelID": "A01",
        "TargetIdentity": {"target_seq": 100, "seq_set": [100]},
        "BoundaryEvidence": {
            "boundary_class": "TARGET_SQUASH",
            "target_commit": [],
            "target_lq_commit": [],
            "target_squash": [{"event_id": 9, "dyn_inst_seq": 999}],
        },
    }
    ok, why = ah.boundary_ok(rec)
    assert ok is False
    assert "not the target" in why


def test_gate10_rejects_request_id_mismatch():
    rec = {
        "ModelID": "A01",
        "TargetIdentity": {"target_seq": 100, "seq_set": [100]},
        "Dimensions": {"identity_linkage": "PASS"},
        "PropagationEvents": [
            {"event_type": "lq_lifecycle", "dyn_inst_seq": 100,
             "lq_entry_id": 4, "entry_generation": 5},
            {"event_type": "memory_request", "dyn_inst_seq": 100,
             "request_id": 7},
            {"event_type": "memory_response", "dyn_inst_seq": 100,
             "request_id": 8},
        ],
    }
    ok, why = ah.linkage_ok(rec)
    assert ok is False
    assert "request_id" in why
