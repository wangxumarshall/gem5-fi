"""Fault-effect propagation coverage tests (LSU v3.2.11 Task 2 / A1).

Structural chain completeness (``trace_completeness.propagation_coverage``)
answers "did the expected stages appear on the fault's own chain".  The
classifier tested here answers the different question "did the fault's
EFFECT actually propagate": a trace can be structurally complete while the
injected fault never diverged any value or control decision (LQ04 is the
canonical case -- its effect is the entry-lifetime window, and the delivered
data is unchanged by construction).

The synthetic event lists mirror the real v3.1 JSONL schema: ``record_type``
``event``/``summary`` records, semicolon-separated ``detail`` key=value
strings, and ``source_event_id`` linking a consumer to its producer.
Numeric identity fields appear as ints in some trace vintages and as JSON
strings in others, so every identity comparison must go through ``str()``
normalization (covered by the mixed-type tests below).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
sys.path.insert(0, str(PLATFORM))

from fault_effect_coverage import EFFECT_MARKERS, classify  # noqa: E402
from trace_completeness import check_completeness  # noqa: E402
from trace_validator import validate  # noqa: E402
from trace_writer import TraceWriter  # noqa: E402
import run_pilot  # noqa: E402

LQ04_HASH = "c6d4496e17859d5"
MD04_SOURCE_HASH = "aa11aa11aa11aa11"
MD04_CONSUMER_HASH = "bb22bb22bb22bb22"


def _ev(event_id, event_type, ptag, seq, detail="", **extra):
    rec = {"record_type": "event", "event_id": event_id,
           "event_type": event_type, "ptag": ptag, "dyn_inst_seq": seq,
           "detail": detail}
    rec.update(extra)
    return rec


def _summary(terminal, completeness="COMPLETE", model="LQ04",
             activation="TRIGGERED"):
    return {"record_type": "summary", "fault_model_id": model,
            "fault_activation_status": activation, "terminal_state": terminal,
            "trace_completeness": completeness}


# --------------------------------------------------------------------------
# Synthetic chains (brief Step 1 assertions)
# --------------------------------------------------------------------------

lq04_injection = _ev(
    3, "injection", "1", "3",
    detail="site=executeLoad_post;family=lq04;field=valid+request"
           ";valid_before=1;valid_after=0;request_before=1;request_after=0"
           ";lq_idx=1;lq_gen=1;request_id=3;injected=1;data_unchanged=1",
    injection_status="INJECTED", activation_status="TRIGGERED")

# LQ04 with the correct payload on every consumer edge: the chain is
# structurally complete (response -> writeback -> consumers -> commit) but
# nothing ever diverged.
lq04_correct_events = [
    _ev(1, "lq_lifecycle", "0", "3",
        detail="queue=LQ;action=alloc;index=1;generation=1;reason=insert"),
    lq04_injection,
    _ev(8, "memory_response", "1", "3",
        detail=f"family=lq04;data_fnv={LQ04_HASH};request_id=1;response_id=1"),
    _ev(9, "register_writeback", "1", "3", source_event_id=8,
        detail=f"family=lq04;data_corruption=0;writeback_value_fnv={LQ04_HASH}"
               f";payload_fnv={LQ04_HASH};value_matches_payload=1"
               f";source_value_hash={LQ04_HASH}"),
    _ev(10, "commit", "0", "3", detail="trigger=fault_instruction_commit"),
    _ev(11, "errant_commit", "1", "3", detail="trigger=faulting_load_commit"),
    _ev(18, "consumer_commit", "1", "8", source_event_id=9,
        detail=f"source_value_hash={LQ04_HASH};consumer_input_fnv={LQ04_HASH}"
               f";consumer_input_matches_source=1"),
    _summary("MASKED", model="LQ04"),
]

md04_injection = _ev(
    5, "injection", "1", "7",
    detail="site=LSQUnit::checkViolations;family=md04;load_seq=7;store_seq=5"
           ";violation_report_suppressed=1",
    injection_status="INJECTED", activation_status="TRIGGERED")

# A consumer edge whose input hash differs from the source hash.
md04_diverged_events = [
    md04_injection,
    _ev(30, "register_writeback", "1", "7", source_event_id=5,
        detail=f"family=md04;writeback_value_fnv={MD04_SOURCE_HASH}"
               f";source_value_hash={MD04_SOURCE_HASH}"),
    _ev(31, "consumer_commit", "1", "9", source_event_id=30,
        detail=f"source_value_hash={MD04_SOURCE_HASH}"
               f";consumer_input_fnv={MD04_CONSUMER_HASH}"
               f";consumer_input_matches_source=0"),
    _summary("MASKED", model="MD04"),
]

fw02_injection = _ev(
    2, "injection", "1", "5",
    detail="site=lsq_fwd_decision;family=addrpath;is_load=1;old_size=8"
           ";new_size=8;old_addr=7ffffefc28;new_addr=7ffffefc28",
    injection_status="INJECTED", activation_status="TRIGGERED")

# Injection plus an unrelated time-adjacent event: different ptag AND
# different dyn_inst_seq, so no chain identity links it.  Its diverged-looking
# writeback must never be counted as fault-effect evidence.
adjacent_unlinked_events = [
    fw02_injection,
    _ev(3, "register_writeback", "2", "9", timestamp=1001,
        detail="family=addrpath;data_corruption=1;writeback_value_fnv=dead"
               ";value_matches_payload=0"),
    _summary("UNRESOLVED", model="FW02"),
]

events_without_injection = [
    _ev(1, "sq_lifecycle", "0", "18",
        detail="queue=SQ;action=alloc;index=1;generation=1;reason=insert"),
    _ev(2, "store_mem_write", "1", "18",
        detail="family=store_data;before_hex=00;after_hex=08"),
    _summary("UNRESOLVED", model="SQ01"),
]


def test_lq04_correct_payload_is_lifecycle_only():
    result = classify("LQ04", lq04_correct_events, lq04_injection, "MASKED")
    assert result["fault_effect_propagation_coverage"] == "LIFECYCLE_ONLY"
    assert result["fault_effect_evidence"]["value_divergence"] == []
    assert result["fault_effect_evidence"]["control_divergence"] == []


def test_md04_consumer_hash_mismatch_is_complete_causal_chain():
    result = classify("MD04", md04_diverged_events, md04_injection, "MASKED")
    assert result["fault_effect_propagation_coverage"] == "COMPLETE_CAUSAL_CHAIN"
    kinds = {d["kind"] for d in
             result["fault_effect_evidence"]["value_divergence"]}
    assert "consumer_input_matches_source" in kinds
    assert "consumer_input_fnv_mismatch" in kinds


def test_fw02_adjacent_unlinked_event_is_never_complete():
    result = classify("FW02", adjacent_unlinked_events, fw02_injection,
                      "UNRESOLVED")
    assert result["fault_effect_propagation_coverage"] in ("PARTIAL",
                                                           "UNRESOLVED")
    # The time-adjacent diverged writeback is not on the fault's chain:
    # the chain is the injection alone, and no divergence was credited.
    assert result["fault_effect_evidence"]["chain_events"] == 1
    assert result["fault_effect_evidence"]["value_divergence"] == []


def test_no_injection_event_is_unresolved():
    result = classify("SQ01", events_without_injection, None, "UNRESOLVED")
    assert result["fault_effect_propagation_coverage"] == "UNRESOLVED"
    assert result["fault_effect_reason"] == "NO_INJECTION_EVENT"


# --------------------------------------------------------------------------
# str() normalization of numeric identity fields
# --------------------------------------------------------------------------

def test_mixed_int_str_identity_fields_still_link_the_chain():
    # Injection ptag is an int while the chained events carry strings (and
    # the injection seq is a string while the writeback carries an int); the
    # consumer's source_event_id is an int pointing at a string event_id.
    # Without str() normalization the chain would be empty and the hash
    # mismatch invisible.
    injection = {"record_type": "event", "event_id": "5",
                 "event_type": "injection", "ptag": 1, "dyn_inst_seq": "7",
                 "injection_status": "INJECTED",
                 "activation_status": "TRIGGERED",
                 "detail": "family=md04;violation_report_suppressed=1"}
    events = [
        injection,
        {"record_type": "event", "event_id": "30",
         "event_type": "register_writeback", "ptag": "1", "dyn_inst_seq": 7,
         "source_event_id": "5",
         "detail": f"writeback_value_fnv={MD04_SOURCE_HASH}"},
        {"record_type": "event", "event_id": 31,
         "event_type": "consumer_commit", "ptag": "1", "dyn_inst_seq": "9",
         "source_event_id": 30,
         "detail": f"consumer_input_fnv={MD04_CONSUMER_HASH}"
                   f";consumer_input_matches_source=1"},
        _summary("MASKED", model="MD04"),
    ]
    result = classify("MD04", events, injection, "MASKED")
    assert result["fault_effect_evidence"]["chain_events"] == 3
    # matches_source=1, so only the fnv comparison exposes the divergence.
    kinds = {d["kind"] for d in
             result["fault_effect_evidence"]["value_divergence"]}
    assert kinds == {"consumer_input_fnv_mismatch"}
    assert result["fault_effect_propagation_coverage"] == "COMPLETE_CAUSAL_CHAIN"


def test_mixed_types_never_fabricate_divergence():
    # Same mixed-type chain as above but with every hash agreeing: the type
    # mismatch itself must not be read as a value divergence.
    injection = {"record_type": "event", "event_id": "3",
                 "event_type": "injection", "ptag": 1, "dyn_inst_seq": "3",
                 "injection_status": "INJECTED",
                 "activation_status": "TRIGGERED",
                 "detail": "family=lq04;data_unchanged=1"}
    events = [
        injection,
        {"record_type": "event", "event_id": "9",
         "event_type": "register_writeback", "ptag": "1", "dyn_inst_seq": 3,
         "source_event_id": "3",
         "detail": f"data_corruption=0;value_matches_payload=1"
                   f";writeback_value_fnv={LQ04_HASH}"},
        {"record_type": "event", "event_id": 18,
         "event_type": "consumer_commit", "ptag": "1", "dyn_inst_seq": "8",
         "source_event_id": 9,
         "detail": f"consumer_input_fnv={LQ04_HASH}"
                   f";consumer_input_matches_source=1"},
        _summary("MASKED", model="LQ04"),
    ]
    result = classify("LQ04", events, injection, "MASKED")
    assert result["fault_effect_evidence"]["value_divergence"] == []
    assert result["fault_effect_propagation_coverage"] == "LIFECYCLE_ONLY"


# --------------------------------------------------------------------------
# Consumer->consumer re-taint edges (Task 2 review fix)
# --------------------------------------------------------------------------

# Real-trace shape (verified on pilots_v3_2_10/LQ04-R01): 325 of the 326
# chained consumer edges are consumer->consumer re-taints (their source is
# itself a consumer_commit whose source hash lives in consumer_output_fnv;
# the remaining edge sources the register_writeback), and every
# consumer_commit carries its own source_value_hash next to its
# consumer_input_fnv.
RETAINT_IN_HASH = "1a2b3c4d5e6f7a8b"   # value the first consumer read
RETAINT_OUT_HASH = "9988776655443322"  # value the first consumer produced
RETAINT_BAD_HASH = "deadbeefdeadbeef"  # corrupted value read downstream

retaint_injection = _ev(
    4, "injection", "1", "4",
    detail="site=executeLoad_post;family=lq04;valid_before=1"
           ";valid_after=0",
    injection_status="INJECTED", activation_status="TRIGGERED")


def _retaint_events(first_output_fnv, second_consumer_detail):
    """Injection -> writeback -> consumer 40 -> consumer 41.

    The edge into event 41 is a consumer->consumer re-taint edge;
    ``first_output_fnv`` is the consumer_output_fnv recorded by the source
    consumer (event 40).
    """
    return [
        retaint_injection,
        _ev(9, "register_writeback", "1", "4", source_event_id=8,
            detail=f"family=lq04;data_corruption=0;value_matches_payload=1"
                   f";writeback_value_fnv={RETAINT_IN_HASH}"),
        _ev(40, "consumer_commit", "1", "9", source_event_id=9,
            detail=f"source_value_hash={RETAINT_IN_HASH}"
                   f";consumer_input_fnv={RETAINT_IN_HASH}"
                   f";consumer_output_fnv={first_output_fnv}"
                   f";consumer_input_matches_source=1"),
        _ev(41, "consumer_commit", "1", "10", source_event_id=40,
            detail=second_consumer_detail),
        _summary("MASKED", model="LQ04"),
    ]


def test_retaint_edge_own_source_value_hash_mismatch_diverges():
    # The second consumer's own re-taint bookkeeping (source_value_hash)
    # disagrees with the value it actually read (consumer_input_fnv).  The
    # source consumer's output hash agrees with the read and every
    # consumer_input_matches_source flag is 1, so ONLY the own-hash signal
    # fires -- before the review fix this divergence was invisible.
    events = _retaint_events(
        RETAINT_BAD_HASH,
        f"source_value_hash={RETAINT_OUT_HASH}"
        f";consumer_input_fnv={RETAINT_BAD_HASH}"
        f";consumer_input_matches_source=1")
    result = classify("LQ04", events, retaint_injection, "MASKED")
    diverged = result["fault_effect_evidence"]["value_divergence"]
    assert diverged
    assert {d["kind"] for d in diverged} == {"source_value_hash_mismatch"}
    assert result["fault_effect_propagation_coverage"] == \
        "COMPLETE_CAUSAL_CHAIN"


def test_retaint_edge_source_consumer_output_fnv_mismatch_diverges():
    # The value diverged between the source consumer's output and the
    # downstream consumer's input, while the downstream bookkeeping
    # (source_value_hash) followed the corrupted value: only the source's
    # consumer_output_fnv exposes the divergence.  Before the review fix
    # that key was missing from _SOURCE_HASH_KEYS, so the source-hash
    # comparison was inert on consumer->consumer edges.
    events = _retaint_events(
        RETAINT_OUT_HASH,
        f"source_value_hash={RETAINT_BAD_HASH}"
        f";consumer_input_fnv={RETAINT_BAD_HASH}"
        f";consumer_input_matches_source=1")
    result = classify("LQ04", events, retaint_injection, "MASKED")
    diverged = result["fault_effect_evidence"]["value_divergence"]
    assert diverged
    assert {d["kind"] for d in diverged} == {"consumer_input_fnv_mismatch"}
    assert all(d["source_hash_kind"] == "consumer_output_fnv"
               for d in diverged)
    assert result["fault_effect_propagation_coverage"] == \
        "COMPLETE_CAUSAL_CHAIN"


def test_retaint_edge_matching_hashes_do_not_diverge():
    # The intact re-taint edge: the second consumer's own hashes agree and
    # match the source consumer's output -- no divergence may be fabricated
    # (the real LQ04-R01 trace is 325 such edges plus one writeback edge,
    # and must grade LIFECYCLE_ONLY).
    events = _retaint_events(
        RETAINT_OUT_HASH,
        f"source_value_hash={RETAINT_OUT_HASH}"
        f";consumer_input_fnv={RETAINT_OUT_HASH}"
        f";consumer_input_matches_source=1")
    result = classify("LQ04", events, retaint_injection, "MASKED")
    assert result["fault_effect_evidence"]["value_divergence"] == []
    assert result["fault_effect_propagation_coverage"] == "LIFECYCLE_ONLY"


# --------------------------------------------------------------------------
# Converter null hash sentinels (Task 2 fix loop, second finding)
# --------------------------------------------------------------------------

# Real-trace shape (verified on pilots_v3_2_5/LP01-R01): the converter writes
# the LITERAL STRING "null" into hash fields it has no value for, and older
# vintages write "0" (e.g. forward_data_fnv=0).  LP01 class=cc consumer
# nodes carry source_value_hash=null / consumer_output_fnv=null next to a
# real consumer_input_fnv.  Truthiness-only guards read those sentinels as
# real hashes and fabricated 204 null-artifact evidence items archive-wide
# (LP01-R01: 96 items -- every single hash-based item on that trace), so
# every hash comparison must first normalize the field to a real hash or
# ABSENT; divergence must never be fabricated from an absent hash.
SENTINEL_REAL_HASH = "0f1e2d3c4b5a6978"  # real hash for the sentinel tests


def test_null_consumer_input_fnv_against_real_source_hash_does_not_diverge():
    # (a) consumer_input_fnv="null" while the own-edge bookkeeping and the
    # source event both carry real hashes: "null" is a sentinel, not a hash,
    # so neither the own-edge check nor the source-hash lookup may compare
    # it against anything.
    events = _retaint_events(
        RETAINT_OUT_HASH,
        f"source_value_hash={SENTINEL_REAL_HASH}"
        f";consumer_input_fnv=null"
        f";consumer_input_matches_source=1")
    result = classify("LQ04", events, retaint_injection, "MASKED")
    assert result["fault_effect_evidence"]["value_divergence"] == []
    assert result["fault_effect_propagation_coverage"] == "LIFECYCLE_ONLY"


def test_both_null_hashes_do_not_diverge():
    # (b) the converter wrote "null" on both sides of the edge.  The
    # own-edge check compares equal sentinels anyway; the source-hash
    # lookup compared the sentinel consumer_input_fnv against the source's
    # real consumer_output_fnv and fabricated a mismatch before the fix.
    events = _retaint_events(
        RETAINT_OUT_HASH,
        "source_value_hash=null;consumer_input_fnv=null"
        ";consumer_input_matches_source=1")
    result = classify("LQ04", events, retaint_injection, "MASKED")
    assert result["fault_effect_evidence"]["value_divergence"] == []
    assert result["fault_effect_propagation_coverage"] == "LIFECYCLE_ONLY"


def test_zero_sentinel_hashes_do_not_diverge():
    # (c) the "0" sentinel (seen in real traces as forward_data_fnv=0), on
    # the consumer side (own-edge guard) and on the source side (source-hash
    # lookup).
    events = _retaint_events(
        RETAINT_OUT_HASH,
        f"source_value_hash={SENTINEL_REAL_HASH}"
        f";consumer_input_fnv=0;consumer_input_matches_source=1")
    result = classify("LQ04", events, retaint_injection, "MASKED")
    assert result["fault_effect_evidence"]["value_divergence"] == []
    assert result["fault_effect_propagation_coverage"] == "LIFECYCLE_ONLY"

    events = _retaint_events(
        "0",
        f"source_value_hash={RETAINT_OUT_HASH}"
        f";consumer_input_fnv={RETAINT_OUT_HASH}"
        f";consumer_input_matches_source=1")
    result = classify("LQ04", events, retaint_injection, "MASKED")
    assert result["fault_effect_evidence"]["value_divergence"] == []
    assert result["fault_effect_propagation_coverage"] == "LIFECYCLE_ONLY"


def test_real_differing_hashes_still_diverge():
    # (d) positive control for the sentinel normalization: two REAL
    # differing hashes must keep diverging through both guards, and no
    # sentinel value may leak into the recorded evidence.
    events = _retaint_events(
        "7777000044448888",
        f"source_value_hash=aaaabbbbccccdddd"
        f";consumer_input_fnv=1111222233334444"
        f";consumer_input_matches_source=1")
    result = classify("LQ04", events, retaint_injection, "MASKED")
    diverged = result["fault_effect_evidence"]["value_divergence"]
    assert {d["kind"] for d in diverged} == {"source_value_hash_mismatch",
                                             "consumer_input_fnv_mismatch"}
    for d in diverged:
        for key in ("consumer_input_fnv", "source_value_hash", "source_hash"):
            value = d.get(key)
            if value is not None:
                assert str(value).strip().lower() not in ("null", "none", "",
                                                          "0")
    assert result["fault_effect_propagation_coverage"] == \
        "COMPLETE_CAUSAL_CHAIN"


def test_none_and_empty_sentinel_hashes_do_not_diverge():
    # Completes the sentinel family: the Python-style "None" string and the
    # empty field are absent hashes on either side of both guards.
    for sentinel in ("None", ""):
        events = _retaint_events(
            RETAINT_OUT_HASH,
            f"source_value_hash={SENTINEL_REAL_HASH}"
            f";consumer_input_fnv={sentinel}"
            f";consumer_input_matches_source=1")
        result = classify("LQ04", events, retaint_injection, "MASKED")
        assert result["fault_effect_evidence"]["value_divergence"] == []

        events = _retaint_events(
            sentinel,
            f"source_value_hash={RETAINT_OUT_HASH}"
            f";consumer_input_fnv={RETAINT_OUT_HASH}"
            f";consumer_input_matches_source=1")
        result = classify("LQ04", events, retaint_injection, "MASKED")
        assert result["fault_effect_evidence"]["value_divergence"] == []
        assert result["fault_effect_propagation_coverage"] == "LIFECYCLE_ONLY"


# --------------------------------------------------------------------------
# Markers, platform fields and wiring
# --------------------------------------------------------------------------

def test_effect_markers_cover_test_models_and_lq04_is_empty():
    for model in ("LQ04", "MD04", "FW02", "SQ01"):
        assert model in EFFECT_MARKERS
    # LQ04's effect is the entry-lifetime window itself: no control marker
    # exists, so LQ04 pilots must grade LIFECYCLE_ONLY when data is intact.
    assert EFFECT_MARKERS["LQ04"] == ()


def test_structural_chain_completeness_alias(tmp_path):
    path = tmp_path / "trace_v31.jsonl"
    w = TraceWriter(path, "PILOT-LQ04", "PILOT-LQ04", "PILOT-LQ04-S01",
                    "LQ04", "LQ04")
    w.event("injection", ptag=41, dyn_inst_seq=7, timestamp=100,
            injection_status="INJECTED", activation_status="TRIGGERED",
            trace_completeness="COMPLETE",
            detail="site=executeLoad_post;family=lq04;valid_before=1"
                   ";valid_after=0")
    resp = w.event("memory_response", ptag=41, dyn_inst_seq=7, timestamp=200,
                   activation_status="TRIGGERED",
                   trace_completeness="COMPLETE", request_id=7, response_id=1,
                   detail=f"family=lq04;data_fnv={LQ04_HASH};size=8")
    wb = w.event("register_writeback", ptag=41, dyn_inst_seq=7, timestamp=300,
                 activation_status="TRIGGERED",
                 trace_completeness="COMPLETE", new_value="5f5e5d5c",
                 source_event_id=resp,
                 detail=f"family=lq04;data_corruption=0"
                        f";writeback_value_fnv={LQ04_HASH}")
    w.event("consumer_commit", ptag=41, dyn_inst_seq=9, timestamp=400,
            commit_status="COMMITTED", trace_completeness="COMPLETE",
            source_event_id=wb,
            detail=f"consumer_input_fnv={LQ04_HASH}"
                   f";consumer_input_matches_source=1")
    w.event("commit", ptag=0, dyn_inst_seq=7, timestamp=350,
            commit_status="COMMITTED", trace_completeness="COMPLETE")
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    assert validate(path) == []
    report = check_completeness(path)
    # Backward compatibility: propagation_coverage keeps its exact value and
    # structural_chain_completeness mirrors it.
    assert report["propagation_coverage"] == "COMPLETE"
    assert report["structural_chain_completeness"] == \
        report["propagation_coverage"]


def test_run_pilot_wires_fault_effect_fields():
    # run_pilot imports the classifier the same way it imports the other
    # platform modules, and the classification block carries the new fields.
    assert run_pilot.classify is classify
    src = (PLATFORM / "run_pilot.py").read_text(encoding="utf-8")
    for key in ('"structural_chain_completeness"',
                '"fault_effect_propagation_coverage"',
                '"fault_effect_evidence"',
                '"fault_effect_reason"'):
        assert key in src
