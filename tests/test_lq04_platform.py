"""LQ04 pilot-platform wiring (LSU v3.2.10 Task 8).

The C++ side is complete: ``CHAOS_LQ04_INJECTION`` / ``_ELIGIBLE_PROBE`` /
``_RESTORE`` lines land in ``lq04_injections.log`` and the propagation trace
carries ``family=lq04`` injection/response/writeback/consumer nodes.  These
tests pin the platform contract: the ``LQ04`` model choice on the v3.2.4
workbook, the log parser, load-side terminal adjudication, the
(LQ04, terminal) completeness profiles and the converter's unit mapping.
"""
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = ROOT / "docs/gem5-fi/lsu/implementation_v3_2/platform"
sys.path.insert(0, str(PLATFORM))

import run_pilot  # noqa: E402
import terminal_rules  # noqa: E402
from tools.prop_trace_to_v31 import convert  # noqa: E402
from trace_completeness import check_completeness, expected_stages  # noqa: E402
from trace_validator import validate  # noqa: E402
from trace_writer import TraceWriter  # noqa: E402

FIXTURE_LOG = (Path(__file__).parent / "data_lq04_platform"
               / "lq04_injections.log")


def test_platform_wiring_constants():
    # MODELS tuple exists, carries LQ04 and RP01 (v3.3.3), and keeps every
    # earlier model. The workbook path follows the authoritative v3.2.7 file.
    assert "LQ04" in run_pilot.MODELS
    assert set(run_pilot.MODELS) == {
        "A01", "A03", "FW02", "SQ01", "DA04", "LP01", "MD04", "FW05",
        "SQ03", "SP05", "LQ04", "RP01"}
    assert run_pilot.EXCEL.name.endswith("-v3.2.7.xlsx")
    assert run_pilot._workload_for("LQ04") == "lq_lifetime_ordinal"
    assert "replay_partial_v332" in str(run_pilot._workload_for("RP01"))


def test_lq04_events_parses_injection_line():
    events = run_pilot._lq04_events(FIXTURE_LOG)
    assert len(events) == 1
    assert events[0]["injected"] == 1
    assert events[0]["ordinal"] == 3
    assert events[0]["kind"] == "injection"
    assert events[0]["seq"] == 142
    assert events[0]["pc"] == 0x104AC
    assert events[0]["lq_idx"] == 4
    assert events[0]["gen"] == 2
    assert events[0]["request_id"] == 7
    assert events[0]["addr"] == 0x1FFFFF10
    assert events[0]["size"] == 8
    assert events[0]["eligible"] == 3
    assert events[0]["tick"] == 918344


def test_lq04_events_probe_restore_and_status_lines(tmp_path):
    log = tmp_path / "lq04_injections.log"
    log.write_text(
        "CHAOS_LQ04_ELIGIBLE_PROBE: seq=57 pc=0x10488 lq_idx=0 gen=1 "
        "ordinal=1 tick=901222\n"
        "CHAOS_LQ04_INJECTION: seq=142 pc=0x104ac lq_idx=4 gen=2 "
        "request_id=7 addr=0x1fffff10 size=8 eligible=3 ordinal=3 "
        "injected=1 tick=918344\n"
        "CHAOS_LQ04_RESTORE: seq=142 lq_idx=4 gen=2 reason=commit "
        "tick=925001\n"
        "CHAOS_LQ04_ELIGIBLE_COUNT=9\n"
        "CHAOS_LQ04_WATCHDOG_EXPIRED: selected=0 injected=0 eligible=9 "
        "ordinal=3 tick=500000000\n", encoding="utf-8")
    events = run_pilot._lq04_events(log)
    # ELIGIBLE_COUNT / WATCHDOG_EXPIRED are status lines, not events.
    assert [e["kind"] for e in events] == ["probe", "injection", "restore"]
    assert events[0]["ordinal"] == 1
    assert events[0]["tick"] == 901222
    assert events[2]["reason"] == "commit"
    assert run_pilot._lq04_events(tmp_path / "absent.log") == []


def test_lq04_target_proof_control_is_not_applicable():
    # Matched no-fault control (injector not mounted, zero injections):
    # the proof must NOT claim a lifetime transition that did not happen.
    proof = run_pilot._lq04_target_proof([], 3)
    assert proof["applicable"] is False
    assert proof["events"] == 0
    assert proof["all_one_injection"] is False
    assert proof["ordinal_matches"] is None  # vacuous True is not a claim
    for key in ("valid_1_to_0", "request_1_to_0", "no_pop_no_reuse",
                "address_size_data_unchanged"):
        assert proof[key] is None
    assert "n/a" in proof["not_applicable_reason"]
    # JSON round-trip keeps the n/a fields as null.
    import json as _json
    assert _json.loads(_json.dumps(proof))["valid_1_to_0"] is None


def test_lq04_target_proof_fault_run_claims_transitions():
    events = run_pilot._lq04_events(FIXTURE_LOG)
    injections = [e for e in events if e.get("kind") == "injection"]
    proof = run_pilot._lq04_target_proof(injections, 3)
    assert proof["applicable"] is True
    assert proof["events"] == 1
    assert proof["all_one_injection"] is True
    assert proof["ordinal_matches"] is True
    assert proof["valid_1_to_0"] is True
    assert proof["request_1_to_0"] is True
    assert proof["no_pop_no_reuse"] is True
    assert proof["address_size_data_unchanged"] is True


def _committed_chain():
    """Minimal committed LQ04 chain: injection -> response -> register
    writeback -> consumer, plus the load's own commit node."""
    return [
        {"record_type": "event", "event_type": "injection", "ptag": 41,
         "dyn_inst_seq": 7, "injection_status": "INJECTED"},
        {"record_type": "event", "event_type": "memory_response", "ptag": 41,
         "dyn_inst_seq": 7},
        {"record_type": "event", "event_type": "register_writeback",
         "ptag": 41, "dyn_inst_seq": 7, "new_value": "5f5e5d5c"},
        {"record_type": "event", "event_type": "consumer_commit",
         "ptag": 41, "dyn_inst_seq": 9},
        {"record_type": "event", "event_type": "commit", "ptag": 0,
         "dyn_inst_seq": 7},
    ]


def test_lq04_is_load_side_and_masked_when_committed():
    assert "LQ04" in terminal_rules.LOAD_SIDE
    events_committed = _committed_chain()
    assert terminal_rules.adjudicate(
        events_committed, model="LQ04", observed_terminal="MASKED",
        oracle_pass=True)[0] == "MASKED"


def test_lq04_squashed_when_no_commit():
    events = [
        {"record_type": "event", "event_type": "injection", "ptag": 41,
         "dyn_inst_seq": 7, "injection_status": "INJECTED"},
        {"record_type": "event", "event_type": "register_writeback",
         "ptag": 41, "dyn_inst_seq": 7, "new_value": "5f5e5d5c"},
        {"record_type": "event", "event_type": "squash", "ptag": 0,
         "dyn_inst_seq": 7},
    ]
    assert terminal_rules.adjudicate(
        events, model="LQ04", observed_terminal="MASKED",
        oracle_pass=True)[0] == "SQUASHED"


def test_lq04_completeness_profiles():
    assert expected_stages("LQ04", "MASKED") == [
        ("injection", "memory_response", "register_writeback",
         "consumer_commit"),
        ("injection", "memory_response", "register_writeback"),
        ("injection", "squash"),
    ]
    assert expected_stages("LQ04", "SQUASHED") == [("injection", "squash")]
    assert expected_stages("LQ04", "CRASH") == [
        ("injection", "simulator_abort")]
    assert expected_stages("LQ04", "UNRESOLVED") == [("injection",)]
    # An unexpected (model, terminal) pair falls back to the DEFAULT_PROFILE.
    assert expected_stages("LQ04", None) == [("injection",)]


def _write_lq04_trace(path: Path) -> None:
    w = TraceWriter(path, "PILOT-LQ04", "PILOT-LQ04", "PILOT-LQ04-S01",
                    "LQ04", "LQ04")
    w.event("injection", ptag=41, dyn_inst_seq=7, timestamp=100,
            injection_status="INJECTED", activation_status="TRIGGERED",
            trace_completeness="COMPLETE",
            detail="site=executeLoad_post;family=lq04;field=valid+request"
                   ";valid_before=1;valid_after=0;request_before=1"
                   ";request_after=0;lq_idx=4;lq_gen=2;request_id=7"
                   ";eligible_ordinal=3;event_ordinal=3;injected=1")
    resp = w.event("memory_response", ptag=41, dyn_inst_seq=7, timestamp=200,
                   activation_status="TRIGGERED",
                   trace_completeness="COMPLETE", request_id=7, response_id=1,
                   lq_entry_id=4, entry_generation=2, execution_attempt_id=1,
                   detail="family=lq04;association=sender_state;size=8"
                          ";data_len=8;data_fnv=8f3a71c2;data_hex=5f5e5d5c"
                          ";request_id=7;response_id=1;lq_entry_id=4"
                          ";entry_generation=2;execution_attempt_id=1")
    wb = w.event("register_writeback", ptag=41, dyn_inst_seq=7, timestamp=300,
                 activation_status="TRIGGERED",
                 trace_completeness="COMPLETE", new_value="5f5e5d5c",
                 request_id=7, source_event_id=resp, execution_attempt_id=1,
                 detail="family=lq04;data_corruption=0"
                        ";writeback_value=5f5e5d5c"
                        ";writeback_value_fnv=8f3a71c2"
                        ";source_value_hash=8f3a71c2"
                        ";request_id=7;execution_attempt_id=1")
    w.event("consumer_commit", ptag=41, dyn_inst_seq=9, timestamp=400,
            commit_status="COMMITTED", trace_completeness="COMPLETE",
            source_event_id=wb, detail="consumer_input_fnv=8f3a71c2")
    w.event("commit", ptag=0, dyn_inst_seq=7, timestamp=350,
            commit_status="COMMITTED", trace_completeness="COMPLETE")
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")


def test_lq04_masked_chain_is_complete(tmp_path):
    path = tmp_path / "trace_v31.jsonl"
    _write_lq04_trace(path)
    assert validate(path) == []
    report = check_completeness(path)
    assert report["trace_completeness"] == "COMPLETE"
    assert report["chain_scoped"] is True
    assert report["chain_integrity"] == "PASS"
    assert report["propagation_coverage"] == "COMPLETE"
    assert report["expected_stages"] == [
        "injection", "memory_response", "register_writeback",
        "consumer_commit"]
    assert report["missing_stages"] == []


def _csv_line(node, tick, ptag, kind, seq, req, addr, detail):
    return f"{node},{tick},{ptag},{kind},{seq},{req},{addr},,,{detail}"


def test_converter_binds_lq04_injection_to_the_lq_unit(tmp_path):
    csv_path = tmp_path / "prop_trace.csv.gz"
    # Field layout mirrors CHAOSPropagation::writeNode: node,tick,ptag,kind,
    # dyn_seq,req_id,addr,phys,arch,detail; the lq04 detail is comma-free
    # and its addr column is bare hex (no 0x prefix).
    lq04_detail = ("site=executeLoad_post;family=lq04;field=valid+request"
                   ";valid_before=1;valid_after=0;request_before=1"
                   ";request_after=0;lq_idx=4;lq_gen=2;request_id=7"
                   ";addr=1fffff10;size=8;occ_before=1;occ_after=1"
                   ";eligible_ordinal=3;event_ordinal=3;injected=1"
                   ";attempt_id=1;replay_gen=0;no_pop=1;no_reuse=1"
                   ";data_unchanged=1")
    agu_detail = ("site=lsq_pushRequest_PRE;family=addrpath"
                  ";mode=a01_bit3_load;old_addr=0x7f00;new_addr=0x7f08")
    with gzip.open(csv_path, "wt", encoding="utf-8") as fh:
        fh.write(_csv_line(1, 1000, 41, "inj", 7, 5, "1fffff10",
                           lq04_detail) + "\n")
        fh.write(_csv_line(2, 900, 42, "inj", 3, 2, "7f00",
                           agu_detail) + "\n")
    out_path = tmp_path / "trace_v31.jsonl"
    convert(csv_path, out_path,
            sample_run_id="PILOT-LQ04", run_id="PILOT-LQ04",
            sub_task_id="PILOT-LQ04-S01", fault_id="LQ04",
            fault_model_id="LQ04", run_status="COMPLETED",
            activation="TRIGGERED", terminal="MASKED",
            completeness="COMPLETE")
    assert validate(out_path) == []
    events = [json.loads(line) for line in
              out_path.read_text(encoding="utf-8").splitlines()]
    events = [e for e in events if e.get("record_type") == "event"]
    lq04 = [e for e in events if e.get("event_type") == "injection"
            and "family=lq04" in (e.get("detail") or "")]
    assert len(lq04) == 1
    assert lq04[0]["unit"] == "LQ"
    assert lq04[0]["sub_unit"] == "executeLoad"
    assert lq04[0]["ptag"] == 41
    assert lq04[0]["dyn_inst_seq"] == 7
    assert lq04[0]["injection_status"] == "INJECTED"
    # Other models' generic "inj" rows keep the AGU mapping.
    agu = [e for e in events if e.get("event_type") == "injection"
           and "family=addrpath" in (e.get("detail") or "")]
    assert len(agu) == 1
    assert agu[0]["unit"] == "AGU"
