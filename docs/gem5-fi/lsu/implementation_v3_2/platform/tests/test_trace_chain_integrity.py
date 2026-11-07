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
    e_resp = w.event("memory_response", ptag=resp_ptag, dyn_inst_seq=resp_seq,
                     trace_completeness="COMPLETE",
                     detail=f"data_fnv={resp_hash}")
    e_taint = w.event("register_writeback", ptag=resp_ptag,
                      dyn_inst_seq=resp_seq,
                      trace_completeness="COMPLETE",
                      source_event_id=e_resp,
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


def _lp01_chain(tmp_path, *, wb_hash="bb", consumer_input="bb",
                matches="1", basis="payload_equals_regval"):
    path = tmp_path / "lp01.jsonl"
    w = TraceWriter(path, "LP01-R01", "LP01-F0-W5", "LP01-F0-W5-S01",
                    "LP01-CFG01", "LP01")
    w.event("injection", ptag=1, dyn_inst_seq=50,
            injection_status="INJECTED", activation_status="TRIGGERED",
            trace_completeness="COMPLETE", old_value="a514af81",
            new_value="ad14af81",
            detail="family=l1d_fwd;orig_data_fnv=aa;inj_data_fnv=bb")
    e_resp = w.event("memory_response", ptag=1, dyn_inst_seq=50,
                     trace_completeness="COMPLETE",
                     detail="family=l1d_fwd;data_fnv=bb")
    e_wb = w.event("register_writeback", ptag=1, dyn_inst_seq=50,
                   trace_completeness="COMPLETE", source_event_id=e_resp,
                   detail=("family=l1d_fwd;source_value_hash=bb;"
                           f"writeback_value_fnv={wb_hash};"
                           f"hash_basis={basis};"
                           f"value_matches_payload={matches}"))
    w.event("consumer_commit", ptag=1, dyn_inst_seq=51,
            trace_completeness="COMPLETE", source_event_id=e_wb,
            detail=f"consumer_input_fnv={consumer_input}")
    w.event("commit", ptag=0, dyn_inst_seq=50,
            trace_completeness="COMPLETE")
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="SDC", completeness="COMPLETE")
    return path


def test_lp01_full_chain_passes(tmp_path):
    report = check_completeness(_lp01_chain(tmp_path))
    assert report["propagation_coverage"] == "COMPLETE"
    assert report["chain_integrity"] == "PASS"


def test_lp01_wb_consumer_hash_discontinuity_fails(tmp_path):
    report = check_completeness(_lp01_chain(tmp_path, consumer_input="cc"))
    assert report["chain_integrity"] == "FAIL"
    assert "hash_discontinuity_wb_consumer" in report["chain_reasons"]


def test_lp01_payload_writeback_mismatch_fails(tmp_path):
    report = check_completeness(_lp01_chain(tmp_path, matches="0"))
    assert report["chain_integrity"] == "FAIL"
    assert "hash_discontinuity_payload_wb" in report["chain_reasons"]


def test_lp01_faulted_no_writeback_is_not_a_hash_failure(tmp_path):
    """Review fix: writeback skipped by a pending fault is not a discontinuity."""
    report = check_completeness(_lp01_chain(
        tmp_path, wb_hash="", consumer_input="", matches="0",
        basis="no_writeback_fault"))
    assert report["chain_integrity"] == "PASS"


def test_lp01_non_scalar_destination_is_not_a_hash_failure(tmp_path):
    """Review fix: vector/matrix destinations have no scalar hash."""
    report = check_completeness(_lp01_chain(
        tmp_path, wb_hash="", consumer_input="", matches="0",
        basis="no_scalar_regval"))
    assert report["chain_integrity"] == "PASS"
