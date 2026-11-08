import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from trace_completeness import check_completeness  # noqa: E402
from trace_writer import TraceWriter  # noqa: E402


def _md04_chain(tmp_path: Path, *, req_id, detail: str):
    path = tmp_path / "t.jsonl"
    w = TraceWriter(path, "MD04-R03", "MD04-F6-W7", "MD04-F6-W7-S01",
                    "MD04-CFG01", "MD04")
    w.event("injection", ptag=1, dyn_inst_seq=17443,
            execution_attempt_id=1, replay_generation=0,
            lq_entry_id=748, entry_generation=1235,
            injection_status="INJECTED", activation_status="TRIGGERED",
            trace_completeness="COMPLETE", detail=detail)
    w.event("memory_response", ptag=1, dyn_inst_seq=17443,
            execution_attempt_id=2, replay_generation=0,
            lq_entry_id=748, entry_generation=1235, request_id=req_id,
            timestamp=200, trace_completeness="COMPLETE",
            detail="family=md04;data_fnv=aa")
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    return path


def test_cross_attempt_without_request_id_is_unverified(tmp_path):
    path = _md04_chain(
        tmp_path, req_id=None,
        detail=("family=md04;load_request_id=67;lq_entry_id=748;"
                "lq_entry_generation=1235;request_tick=50"))
    report = check_completeness(path)
    assert report["execution_attempt_link"] == "CROSS_ATTEMPT_UNVERIFIED"
    assert "cross_attempt_without_identity" in report["chain_reasons"]
    assert report["chain_integrity"] == "FAIL"


def test_cross_attempt_with_full_identity_is_verified(tmp_path):
    path = _md04_chain(
        tmp_path, req_id=67,
        detail=("family=md04;load_request_id=67;lq_entry_id=748;"
                "lq_entry_generation=1235;request_tick=50"))
    report = check_completeness(path)
    assert report["execution_attempt_link"] == "CROSS_ATTEMPT_VERIFIED"
    assert "cross_attempt_without_identity" not in report["chain_reasons"]
    assert report["chain_integrity"] == "PASS"


def test_same_attempt_chain_is_labelled(tmp_path):
    path = tmp_path / "same.jsonl"
    w = TraceWriter(path, "MD04-R02", "MD04-F6-W7", "MD04-F6-W7-S01",
                    "MD04-CFG01", "MD04")
    w.event("injection", ptag=1, dyn_inst_seq=2251,
            execution_attempt_id=1, lq_entry_id=162, entry_generation=275,
            injection_status="INJECTED", activation_status="TRIGGERED",
            trace_completeness="COMPLETE", detail="family=md04")
    w.event("memory_response", ptag=1, dyn_inst_seq=2251,
            execution_attempt_id=1, lq_entry_id=162, entry_generation=275,
            timestamp=200, trace_completeness="COMPLETE",
            detail="family=md04;data_fnv=aa")
    w.close(run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    report = check_completeness(path)
    assert report["execution_attempt_link"] == "SAME_ATTEMPT"
