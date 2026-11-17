import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runner"))

import final_closure as fc  # noqa: E402


def _ev(**over):
    ev = {
        "RunID": "SYN-WHEN-C01-T01-FAULT", "ModelID": "A01",
        "ContextID": "C01", "TimingID": "T01",
        "TargetIdentity": {"target_seq": 10, "seq_set": [10]},
        "InjectionEvent": {"event_id": 1, "event_type": "injection",
                           "dyn_inst_seq": 10, "old_value": "a",
                           "new_value": "b"},
        "InjectionEffectiveEvidence": {"value_changed": True},
        "BoundaryEvidence": {
            "boundary_class": "TARGET_COMMIT",
            "target_commit": [{"event_id": 3, "dyn_inst_seq": 10}],
            "target_lq_commit": [], "target_squash": [],
            "target_replay": [], "watchdog": None,
        },
        "SoftwareOracle": {"terminal": "SDC"},
        "PresentStages": ["injection", "commit"], "MissingStages": [],
        "PropagationEdgeCount": 1, "TraceCompleteness": "COMPLETE",
        "A03Semantics": None, "SQ01Semantics": None,
    }
    ev.update(over)
    return ev


def test_target_squash_before_commit_is_complete_even_if_unrelated():
    ev = _ev(
        ModelID="FW02",
        BoundaryEvidence={
            "boundary_class": "TARGET_SQUASH",
            "target_commit": [], "target_lq_commit": [],
            "target_squash": [{
                "event_id": 7, "dyn_inst_seq": 10,
                "detail": "squash_cause=unrelated;fault_caused=0"}],
            "target_replay": [], "watchdog": None,
        },
        SoftwareOracle={"terminal": "NO_VISIBLE_MISMATCH"},
        PropagationEvents=[{"event_type": "forwarding_decision",
                            "detail": "fault_decision=suppressed"}],
    )
    c = fc.classify(ev)
    assert c["TARGET_SQUASHED"] == "YES"
    assert c["TARGET_COMMITTED"] == "NO"
    assert c["FAULT_CAUSED_SQUASH"] == "NO"
    assert c["FINAL_CLASS"] == "COMPLETE"


def test_a03_already_stuck_is_limitation_not_false_value_change():
    ev = _ev(
        ModelID="A03",
        InjectionEvent={"event_id": 1, "event_type": "injection_nochange",
                        "dyn_inst_seq": 10, "old_value": "a", "new_value": "a"},
        InjectionEffectiveEvidence={"value_changed": False},
        A03Semantics={"target_value_unchanged": True},
    )
    c = fc.classify(ev)
    assert c["TARGET_VALUE_CHANGED"] == "NO"
    assert c["FINAL_CLASS"] == "COMPLETE_WITH_DOCUMENTED_LIMITATION"


def test_rp01_requires_all_five_checks():
    ev = _ev(
        ModelID="RP01",
        BoundaryEvidence={
            "boundary_class": "TARGET_STALL_WATCHDOG",
            "target_commit": [], "target_lq_commit": [],
            "target_squash": [], "target_replay": [],
            "watchdog": {"event_id": 9},
        },
        InjectionEffectiveEvidence={
            "value_changed": False,
            "rp01": {"checks": {"A": True, "B": True, "C": True,
                                "D": True, "E": True}},
        },
        SoftwareOracle={"terminal": "HANG_WATCHDOG"},
    )
    c = fc.classify(ev)
    assert c["FINAL_CLASS"] == "COMPLETE_WITH_DOCUMENTED_LIMITATION"
    ev["InjectionEffectiveEvidence"]["rp01"]["checks"]["E"] = False
    assert fc.classify(ev)["FINAL_CLASS"] == "UNRESOLVED"


def test_full_edge_export_keeps_all_edges_and_only_marks_preview(tmp_path):
    trace = tmp_path / "trace.jsonl"
    events = []
    for i in range(1, 252):
        events.append({"record_type": "event", "event_id": i,
                       "event_type": "injection" if i == 1 else "writeback",
                       "dyn_inst_seq": 10, "ptag": 5,
                       "old_value": "a", "new_value": "b"})
    with open(trace, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
        for i in range(1, 251):
            f.write(json.dumps({
                "record_type": "propagation_edge", "propagation_edge_id": i,
                "source_event_id": i, "destination_event_id": i + 1,
                "edge_kind": "taint", "producer_inst_seq": 10,
                "consumer_inst_seq": 10}) + "\n")
    ev = {"RunID": "SYN", "TargetIdentity": {"target_seq": 10,
                                              "seq_set": [10]},
          "InjectionEvent": {"event_id": 1}}
    meta = fc.export_full_edges(ev, trace, tmp_path / "edges.csv.gz")
    assert meta["full_count"] == 250
    assert meta["preview_count"] == 200
    preview = fc.preview_metadata(ev, meta, str(tmp_path / "edges.csv.gz"))
    assert preview["PropagationEdgesPreviewOnly"] is True
    assert preview["PropagationEdgesFullCount"] == 250
