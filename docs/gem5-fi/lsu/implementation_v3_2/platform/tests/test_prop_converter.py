import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from tools.prop_trace_to_v31 import convert  # noqa: E402
from trace_completeness import check_completeness  # noqa: E402
from trace_validator import validate  # noqa: E402

IMPL = PLATFORM.parent
CSV = IMPL / "preexisting_rejected/pilots/A01F0/prop_trace.csv.gz"
A03_CSV = IMPL / "pilots/A03F5/prop_trace.csv.gz"


def test_real_csv_converts_to_valid_complete_trace(tmp_path):
    out = tmp_path / "trace.jsonl"
    result = convert(
        CSV, out, sample_run_id="PILOT-A01-TEST", run_id="PILOT-A01",
        sub_task_id="PILOT-A01-S01", fault_id="A01-CFG01",
        fault_model_id="A01", run_status="COMPLETED", activation="TRIGGERED",
        terminal="MASKED", completeness="COMPLETE")
    assert result["rows"] == 6
    assert validate(out) == []
    report = check_completeness(out)
    assert report["trace_completeness"] == "COMPLETE"
    assert report["injections"] == 1


def test_truncated_or_incomplete_can_omit_summary(tmp_path):
    out = tmp_path / "trace.jsonl"
    convert(
        CSV, out, sample_run_id="PILOT-A01-TEST", run_id="PILOT-A01",
        sub_task_id="PILOT-A01-S01", fault_id="A01-CFG01",
        fault_model_id="A01", run_status="COMPLETED", activation="TRIGGERED",
        terminal="MASKED", completeness="INCOMPLETE", no_summary=True)
    report = check_completeness(out)
    assert report["trace_completeness"] == "INCOMPLETE"
    assert report["terminal_state"] is None


def test_fragment_and_source_ids_are_top_level(tmp_path):
    """Defect 1: fragment_id must be a populated JSONL top-level field."""
    import gzip
    csv = tmp_path / "prop.csv.gz"
    with gzip.open(csv, "wt", encoding="utf-8") as fh:
        fh.write(
            "1,100,1,resp,48,14,0x7edb0,0,0,"
            "fragment_id=15;request_id=14;response_id=1;data_len=8;"
            "data_hex=0000000000000000;data_fnv=a8c7f832281a39c5\n")
    out = tmp_path / "trace.jsonl"
    convert(csv, out, sample_run_id="PILOT-A01-TEST",
            run_id="PILOT-A01", sub_task_id="PILOT-A01-S01",
            fault_id="A01-CFG01", fault_model_id="A01",
            run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    resp = next(r for r in (json.loads(line) for line in out.read_text().splitlines())
                if r.get("event_type") == "memory_response")
    assert resp["fragment_id"] == 15
    assert resp["request_id"] == 14
    assert resp["response_id"] == 1


def test_response_address_is_pa_not_va(tmp_path):
    out = tmp_path / "trace.jsonl"
    convert(CSV, out, sample_run_id="PILOT-A01-TEST", run_id="PILOT-A01",
            sub_task_id="PILOT-A01-S01", fault_id="A01-CFG01",
            fault_model_id="A01", run_status="COMPLETED",
            activation="TRIGGERED", terminal="MASKED", completeness="COMPLETE")
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    resp = next(r for r in rows if r.get("event_type") == "memory_response")
    assert resp["pa"] is not None and resp["va"] is None


def test_each_injection_gets_its_own_injection_event_id(tmp_path):
    import pytest
    out = tmp_path / "trace.jsonl"
    convert(A03_CSV, out, sample_run_id="PILOT-A03-TEST", run_id="PILOT-A03",
            sub_task_id="PILOT-A03-S01", fault_id="A03-CFG01",
            fault_model_id="A03", run_status="SIMULATOR_ERROR",
            activation="TRIGGERED", terminal="CRASH", completeness="COMPLETE",
            allow_truncated_complete=True)
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    injections = [r for r in rows if r.get("event_type") == "injection"]
    ids = [r["injection_event_id"] for r in injections]
    assert len(ids) == len(set(ids)) == 73
    # Downstream nodes inherit the injection id of their own ptag.
    assert all(r["injection_event_id"] >= 1 for r in rows if r.get("record_type") == "event")


def test_f5_nochange_is_counted_as_an_injection(tmp_path):
    """A03 F5: the stuck-at condition can apply without changing the value.

    The application is still a real injection and must appear in the trace
    (defect 8: 146 applications vs 73 INJECTED nodes in v3.2.1).
    """
    import gzip
    csv = tmp_path / "prop.csv.gz"
    with gzip.open(csv, "wt", encoding="utf-8") as fh:
        fh.write(
            "1,100,1,inj_nochange,42,0,0x1000,0,0,"
            "site=lsq_pushRequest_PRE;mode=a03_bit3_stuck0_load;"
            "old_addr=0x1000;new_addr=0x1000;value_changed=0\n")
    out = tmp_path / "trace.jsonl"
    convert(csv, out, sample_run_id="PILOT-A03-TEST",
            run_id="PILOT-A03", sub_task_id="PILOT-A03-S01",
            fault_id="A03-CFG01", fault_model_id="A03",
            run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    event = next(r for r in rows if r.get("record_type") == "event")
    assert event["event_type"] == "injection_nochange"
    assert event["injection_status"] == "NO_CHANGE"
    assert event["dyn_inst_seq"] == 42
    assert event["unit"] == "AGU"
    assert check_completeness(out)["injections"] == 1


def test_fw02_forwarding_unit_and_fault_instruction_commit(tmp_path):
    """FW02: FWD unit, explicit normal/fault decision, real commit node."""
    import gzip
    csv = tmp_path / "prop.csv.gz"
    with gzip.open(csv, "wt", encoding="utf-8") as fh:
        fh.write(
            "1,100,1,fwd,397,0,0x1000,0,0,"
            "store_seq=383;load_seq=397;byte_begin=0x1000;byte_end=0x1008;"
            "size=8;store_data_fnv=aa;forward_data_fnv=bb;"
            "decision=suppressed;normal_decision=forwarded;"
            "fault_decision=suppressed;memory_path=1\n")
        fh.write(
            "2,200,0,commit,397,0,0,0,0,"
            "trigger=fault_instruction_commit;pc=0x400;commit_seq=46;"
            "execution_attempt_id=1;replay_generation=0;is_load=1;is_store=0\n")
    out = tmp_path / "trace.jsonl"
    convert(csv, out, sample_run_id="PILOT-FW02-TEST",
            run_id="PILOT-FW02", sub_task_id="PILOT-FW02-S01",
            fault_id="FW02-CFG01", fault_model_id="FW02",
            run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    fwd = next(r for r in rows if r.get("event_type") == "forwarding_decision")
    assert fwd["unit"] == "FWD"
    assert fwd["normal_decision"] == "forwarded"
    assert fwd["fault_decision"] == "suppressed"
    assert fwd["forward_decision"] == "suppressed"
    assert fwd["memory_path"] == 1
    commit = next(r for r in rows if r.get("event_type") == "commit")
    assert commit["commit_status"] == "COMMITTED"
    assert commit["commit_seq"] == 46
    assert commit["dyn_inst_seq"] == 397


def test_sq01_store_data_injection_is_sq_unit(tmp_path):
    import gzip
    csv = tmp_path / "prop.csv.gz"
    with gzip.open(csv, "wt", encoding="utf-8") as fh:
        fh.write(
            "1,100,0,inj_store_data,250,0,0,0,0,"
            "site=lsq_write_sq_entry;mode=sq01_bit3;queue=SQ;index=7;"
            "generation=9;old_byte=0x10;new_byte=0x18;value_changed=1\n")
    out = tmp_path / "trace.jsonl"
    convert(csv, out, sample_run_id="PILOT-SQ01-TEST",
            run_id="PILOT-SQ01", sub_task_id="PILOT-SQ01-S01",
            fault_id="SQ01-CFG01", fault_model_id="SQ01",
            run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    event = next(r for r in (json.loads(line) for line in out.read_text().splitlines())
                 if r.get("record_type") == "event")
    assert event["event_type"] == "injection"
    assert event["unit"] == "SQ"
    assert event["sub_unit"] == "store_data"
    assert event["injection_status"] == "INJECTED"
    assert event["old_value"] == "0x10"
    assert event["new_value"] == "0x18"
    assert event["sq_entry_id"] == 7
    assert event["entry_generation"] == 9
    assert event["dyn_inst_seq"] == 250


def test_da04_byte_enable_chain_is_sq_unit_and_ordered(tmp_path):
    """DA04: injection -> store writeback -> actual memory write, one chain."""
    import gzip
    csv = tmp_path / "prop.csv.gz"
    with gzip.open(csv, "wt", encoding="utf-8") as fh:
        fh.write(
            "1,100,3,inj_store_be,250,0,0x2000,0,0,"
            "site=lsq_pushRequest;family=byte_enable;fault_model=DA04;size=4;"
            "old_be=0xf;new_be=0xe;changed_bit=0;addr_before=0x2000;"
            "addr_after=0x2000;size_before=4;size_after=4;"
            "store_data_fnv=abc;store_data_hex=01020304;"
            "sq_entry_id=7;entry_generation=9\n")
        fh.write(
            "2,110,3,store_wb,250,0,0x2000,0,0,"
            "site=lsq_writebackStores;family=byte_enable;size=4;be_mask=0xe;"
            "data_fnv=abc;data_hex=01020304;sq_entry_id=7;"
            "entry_generation=9;addr=0x2000\n")
        fh.write(
            "3,120,3,store_mem,250,0,0x2000,0,0,"
            "site=BaseCache::updateBlockData;family=byte_enable;"
            "blk_addr=0x2000;offset=0;size=4;be_mask=0xe;"
            "packet_data_fnv=abc;packet_data_hex=01020304;"
            "before_hex=aabbccdd;after_hex=aabbcc04;enabled_written=1;"
            "disabled_unchanged=1;lane0_packet=0x04;lane0_before=0xdd;"
            "lane0_after=0xdd\n")
    out = tmp_path / "trace.jsonl"
    convert(csv, out, sample_run_id="PILOT-DA04-TEST",
            run_id="PILOT-DA04", sub_task_id="PILOT-DA04-S01",
            fault_id="DA04-CFG01", fault_model_id="DA04",
            run_status="COMPLETED", activation="TRIGGERED",
            terminal="MASKED", completeness="COMPLETE")
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    inj = next(r for r in rows if r.get("event_type") == "injection")
    assert inj["unit"] == "SQ" and inj["sub_unit"] == "byte_enable"
    assert inj["old_value"] == "0xf" and inj["new_value"] == "0xe"
    assert inj["original_byte_enable"] == "0xf"
    assert inj["injected_byte_enable"] == "0xe"
    assert inj["changed_bit"] == 0
    assert inj["address_before"] == "0x2000"
    assert inj["address_after"] == "0x2000"
    assert inj["access_size_before"] == 4
    assert inj["access_size_after"] == 4
    assert inj["store_data_before"] == inj["store_data_after"] == "abc"
    assert inj["sq_entry_id"] == 7
    wb = next(r for r in rows if r.get("event_type") == "store_writeback")
    assert wb["unit"] == "SQ" and wb["sub_unit"] == "writeback"
    assert wb["parent_event_id"] == inj["event_id"]
    mem = next(r for r in rows if r.get("event_type") == "store_mem_write")
    assert mem["unit"] == "L1D" and mem["sub_unit"] == "memory_write"
    assert mem["pa"] == "0x2000"
    assert mem["old_value"] == "aabbccdd"
    assert mem["new_value"] == "aabbcc04"
    assert mem["parent_event_id"] == wb["event_id"]


def test_truncated_complete_requires_crash(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        convert(A03_CSV, tmp_path / "trace.jsonl",
                sample_run_id="PILOT-A03-TEST", run_id="PILOT-A03",
                sub_task_id="PILOT-A03-S01", fault_id="A03-CFG01",
                fault_model_id="A03", run_status="COMPLETED",
                activation="TRIGGERED", terminal="MASKED", completeness="COMPLETE",
                allow_truncated_complete=True)
