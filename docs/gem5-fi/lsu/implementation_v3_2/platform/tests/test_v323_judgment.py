import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from run_pilot import (_decide_masked_terminal, _fault_causality,
                       _terminal_evidence)


def _events(*rows):
    return [{"record_type": "event", **r} for r in rows]


def test_target_squash_without_commit_is_squashed():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 169,
         "new_value": "0x7ffffefdc8"},
        {"event_type": "squash", "dyn_inst_seq": 169},
    )
    assert _decide_masked_terminal(events) == (
        "SQUASHED", "TARGET_SQUASHED_NO_COMMIT")


def test_other_sequence_squash_does_not_count():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 169,
         "new_value": "0x7ffffefdc8"},
        {"event_type": "squash", "dyn_inst_seq": 170},
    )
    assert _decide_masked_terminal(events)[0] == "UNRESOLVED"


def test_committed_target_is_not_squashed():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 169,
         "new_value": "0x7ffffefdc8"},
        {"event_type": "squash", "dyn_inst_seq": 169},
        {"event_type": "commit", "dyn_inst_seq": 169},
    )
    assert _decide_masked_terminal(events)[0] == "UNRESOLVED"


def test_causality_address_match_and_temporal_only():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 1146,
         "new_value": "0xffffffffffb73c50"})
    assert _fault_causality(events, "CRASH", "0xffffffffffb73c50") == \
        "DIRECT_ADDRESS_MATCH"
    assert _fault_causality(events, "CRASH", "0xffffffffffb73c58") == \
        "TEMPORAL_ASSOCIATION_ONLY"
    evidence = _terminal_evidence(events, "0xffffffffffb73c50", "")
    assert evidence["address_match"] is True
    assert evidence["last_injection_dyn_seq"] == 1146


def test_dataflow_evidence_for_masked():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 48,
         "new_value": "0x1008"},
        {"event_type": "memory_response", "dyn_inst_seq": 48},
    )
    assert _fault_causality(events, "MASKED", None) == \
        "DIRECT_DATAFLOW_EVIDENCE"
