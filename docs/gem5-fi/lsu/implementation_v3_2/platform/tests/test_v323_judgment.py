import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from run_pilot import (_fault_causality, _sq01_summary, _terminal_evidence)
from terminal_rules import adjudicate


def _judge(events):
    """v3.2.4 chain-scoped adjudication (replaces _decide_masked_terminal)."""
    return adjudicate(events, model="A01", observed_terminal="MASKED",
                      oracle_pass=True, trace_complete=True)


def _events(*rows):
    return [{"record_type": "event", **r} for r in rows]


def test_target_squash_without_commit_is_squashed():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 169,
         "new_value": "0x7ffffefdc8"},
        {"event_type": "squash", "dyn_inst_seq": 169},
    )
    assert _judge(events) == ("SQUASHED", "TARGET_SQUASHED_NO_COMMIT")


def test_other_sequence_squash_does_not_count():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 169,
         "new_value": "0x7ffffefdc8"},
        {"event_type": "squash", "dyn_inst_seq": 170},
    )
    assert _judge(events)[0] == "UNRESOLVED"


def test_committed_target_is_not_squashed():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 169,
         "new_value": "0x7ffffefdc8"},
        {"event_type": "squash", "dyn_inst_seq": 169},
        {"event_type": "commit", "dyn_inst_seq": 169},
    )
    assert _judge(events)[0] == "UNRESOLVED"


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


def test_sq01_log_parser(tmp_path):
    log = tmp_path / "lsq_fwd_injections.log"
    log.write_text(
        "Tick: 140910, Site: lsq_write_sq_entry, FaultType: sq01_bit3_flip, "
        "seq: 18, sq_idx: 1, entry_generation: 1, old_byte0: 0x0, "
        "new_byte0: 0x8, faults_injected: 1\n")
    summary = _sq01_summary(log)
    assert summary["injected"] == 1
    assert summary["events"][0] == {"seq": 18, "idx": 1, "gen": 1,
                                    "old": 0x0, "new": 0x8}


def test_dataflow_evidence_for_masked():
    events = _events(
        {"event_type": "injection", "dyn_inst_seq": 48,
         "new_value": "0x1008"},
        {"event_type": "memory_response", "dyn_inst_seq": 48},
    )
    assert _fault_causality(events, "MASKED", None) == \
        "DIRECT_DATAFLOW_EVIDENCE"
