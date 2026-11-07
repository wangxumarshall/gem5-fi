import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from trace_completeness import check_completeness  # noqa: E402
from trace_writer import TraceWriter  # noqa: E402


def _da04_chain(tmp_path, *, store_ptag=1, resp_ptag=1, resp_seq=300,
                resp_hash="abc", taint_hash="abc", consumer_src="taint",
                disabled="1"):
    path = tmp_path / "chain.jsonl"
    w = TraceWriter(path, "S-R01", "R", "S", "F1", "DA04")
    e_inj = w.event("injection", ptag=store_ptag, dyn_inst_seq=250,
                    injection_status="INJECTED",
                    activation_status="TRIGGERED",
                    trace_completeness="COMPLETE",
                    old_value="0xf", new_value="0xe",
                    sq_entry_id=7, entry_generation=9)
    w.event("store_writeback", ptag=store_ptag, dyn_inst_seq=250,
            trace_completeness="COMPLETE", detail="be_mask=0xe")
    w.event("store_mem_write", ptag=store_ptag, dyn_inst_seq=250,
            trace_completeness="COMPLETE",
            detail=f"family=byte_enable;disabled_unchanged={disabled}")
    w.event("memory_response", ptag=resp_ptag, dyn_inst_seq=resp_seq,
            trace_completeness="COMPLETE",
            detail=f"data_fnv={resp_hash}")
    e_taint = w.event("register_writeback", ptag=resp_ptag,
                      dyn_inst_seq=resp_seq,
                      trace_completeness="COMPLETE",
                      detail=f"source_value_hash={taint_hash}")
    src = e_taint if consumer_src == "taint" else None
    w.event("consumer_commit", ptag=resp_ptag, dyn_inst_seq=301,
            trace_completeness="COMPLETE", source_event_id=src)
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="SDC", completeness="COMPLETE")
    return path, e_inj


def test_single_ptag_full_chain_is_complete(tmp_path):
    path, _ = _da04_chain(tmp_path)
    report = check_completeness(path)
    assert report["propagation_coverage"] == "COMPLETE"
    assert report["chain_integrity"] == "PASS"
    assert report["chain_ptag"] == 1
    assert report["chain_scoped"] is True


def test_stages_from_a_different_ptag_do_not_complete_the_chain(tmp_path):
    path, _ = _da04_chain(tmp_path, resp_ptag=2)
    report = check_completeness(path)
    assert report["propagation_coverage"] == "PARTIAL"
    assert "memory_response" in report["missing_stages"]


def test_response_on_the_store_seq_is_invalid(tmp_path):
    path, _ = _da04_chain(tmp_path, resp_seq=250)
    report = check_completeness(path)
    assert report["chain_integrity"] == "FAIL"
    assert "response_on_store_seq" in report["chain_reasons"]


def test_hash_discontinuity_is_invalid(tmp_path):
    path, _ = _da04_chain(tmp_path, resp_hash="abc", taint_hash="def")
    report = check_completeness(path)
    assert report["chain_integrity"] == "FAIL"
    assert "hash_discontinuity_resp_taint" in report["chain_reasons"]


def test_consumer_without_taint_edge_is_invalid(tmp_path):
    path, _ = _da04_chain(tmp_path, consumer_src="none")
    report = check_completeness(path)
    assert report["chain_integrity"] == "FAIL"
    assert "consumer_without_taint_edge" in report["chain_reasons"]


def test_da04_disabled_lane_must_be_unchanged(tmp_path):
    path, _ = _da04_chain(tmp_path, disabled="0")
    report = check_completeness(path)
    assert report["chain_integrity"] == "FAIL"
    assert "byte_enable_not_applied" in report["chain_reasons"]
