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


def test_lp01_injection_before_after_and_edge_type(tmp_path):
    """LP01: both payload hashes survive; every edge carries type + hashes."""
    import gzip
    csv = tmp_path / "p.csv.gz"
    rows = [
        "0,100,1,inj_l1dfwd,7,,80e30,,,orig_data_fnv=aa;orig_data_hex=a514af81;"
        "inj_data_fnv=bb;inj_data_hex=ad14af81;mask=0x8;eligible_ordinal=5;"
        "request_tick=90;addr=0x80e30;entry_generation=3",
        "1,101,1,resp,7,11,80e30,,,family=l1d_fwd;data_fnv=bb;data_hex=ad14af81;"
        "orig_data_fnv=aa;request_tick=90;response_tick=101",
        "2,102,1,taint_reg,7,11,80e30,4,0,family=l1d_fwd;writeback_value=0xad14af81;"
        "writeback_value_fnv=bb;source_value_hash=bb;source_event_id=1",
    ]
    with gzip.open(csv, "wt") as fh:
        fh.write("\n".join(rows) + "\n")
    out = tmp_path / "t.jsonl"
    convert(csv, out, sample_run_id="LP01-R01", run_id="LP01-F0-W5",
            sub_task_id="LP01-F0-W5-S01", fault_id="LP01-CFG01",
            fault_model_id="LP01", run_status="COMPLETED",
            activation="TRIGGERED", terminal="SDC", completeness="COMPLETE")
    recs = [json.loads(line) for line in out.read_text().splitlines()]
    inj = next(r for r in recs if r.get("event_type") == "injection")
    assert inj["unit"] == "L1D" and inj["sub_unit"] == "load_response_data"
    assert inj["old_value"] == "a514af81"
    assert inj["new_value"] == "ad14af81"
    assert inj["original_data_fnv"] == "aa"
    assert inj["injected_data_fnv"] == "bb"
    assert inj["fault_mask"] == 8
    assert inj["eligible_event_ordinal"] == 5
    assert inj["request_timestamp"] == 90
    edges = [r for r in recs if r.get("record_type") == "propagation_edge"]
    assert edges and all(e.get("edge_type") for e in edges)
    assert all(e.get("source_value_hash") for e in edges)


def test_truncated_complete_requires_crash(tmp_path):
    import pytest
    with pytest.raises(SystemExit):
        convert(A03_CSV, tmp_path / "trace.jsonl",
                sample_run_id="PILOT-A03-TEST", run_id="PILOT-A03",
                sub_task_id="PILOT-A03-S01", fault_id="A03-CFG01",
                fault_model_id="A03", run_status="COMPLETED",
                activation="TRIGGERED", terminal="MASKED", completeness="COMPLETE",
                allow_truncated_complete=True)


def _sp05_detail(text):
    return dict(item.split("=", 1) for item in text.split(";") if "=" in item)


def _sp05_stage_verdict(fields):
    """Mirror CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/sp05_rules.hh stageVerdict."""
    def hash_value(value):
        if value in (None, "", "null", "None", "0"):
            return 0
        return int(value, 16)

    if fields.get("reload_seq") in (None, "", "0"):
        return "NO_RELOAD_OBSERVED", "null"
    if (hash_value(fields.get("store_data_fnv")) == 0
            or hash_value(fields.get("reload_data_hash")) == 0):
        return "RELOAD_UNVERIFIABLE", "null"
    if (hash_value(fields["reload_data_hash"])
            == hash_value(fields["store_data_fnv"])):
        return "MASKED", "1"
    return "CHAIN_VISIBILITY_LOST", "0"


def test_sp05_store_data_is_recorded(tmp_path):
    """L-A05: the skipped store's bytes are bound, not left as a null hash.

    noteSP05Injection now hashes the SQ entry bytes (FNV-1a-64, the same
    idiom as every store-family record) and stores them on the fault store
    entry, so the deferred sp05_stage record carries a 16-hex store_data_fnv.
    With the reload reading the zero word (a8c7f832281a39c5) the verdict must
    be data_correct=0 / CHAIN_VISIBILITY_LOST, not RELOAD_UNVERIFIABLE.
    """
    import gzip
    import re

    def fnv1a64(data):
        h = 14695981039346656037
        for byte in data:
            h ^= byte
            h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
        return f"{h:016x}"

    store_bytes = bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])
    store_fnv = fnv1a64(store_bytes)
    zero_word_fnv = "a8c7f832281a39c5"
    assert re.fullmatch(r"[0-9a-f]{16}", store_fnv)
    assert store_fnv != zero_word_fnv

    csv = tmp_path / "sp05.csv.gz"
    with gzip.open(csv, "wt", encoding="utf-8") as fh:
        fh.write(
            "1,1500,1,sp05_stage,952,0,0,0,0,"
            "record=sp05_stage;family=sp05_complete;model=SP05;"
            "store_seq=952;sq_idx=7;gen=9;completion_tick=1400;"
            "commit_tick=1450;writeback_tick=1440;drain_tick=0;"
            "write_skipped=1;reload_seq=1010;"
            f"reload_data_hash={zero_word_fnv};"
            f"store_data_fnv={store_fnv};data_correct=0;"
            "stage_outcome=CHAIN_VISIBILITY_LOST;"
            "masking_mechanism=NOT_APPLICABLE\n")
        fh.write(
            "2,1450,1,sp05_write_skipped,952,0,0,0,0,"
            "site=writebackStores_prematureComplete;family=sp05_complete;"
            "model=SP05;write_skipped=1;mem_sent=0;store_seq=952;"
            f"sq_entry_id=7;store_data_fnv={store_fnv};drain_tick=0\n")
    out = tmp_path / "trace.jsonl"
    convert(csv, out, sample_run_id="PILOT-SP05-TEST", run_id="PILOT-SP05",
            sub_task_id="PILOT-SP05-S01", fault_id="SP05-CFG01",
            fault_model_id="SP05", run_status="COMPLETED",
            activation="TRIGGERED", terminal="SDC", completeness="COMPLETE")
    events = [json.loads(line) for line in out.read_text().splitlines()]

    stage = next(e for e in events if e.get("event_type") == "sp05_stage")
    fields = _sp05_detail(stage["detail"])
    assert re.fullmatch(r"[0-9a-f]{16}", fields["store_data_fnv"])
    assert fields["store_data_fnv"] == store_fnv
    assert fields["data_correct"] == "0"
    assert fields["stage_outcome"] == "CHAIN_VISIBILITY_LOST"
    assert fields["reload_data_hash"] == zero_word_fnv
    assert _sp05_stage_verdict(fields) == ("CHAIN_VISIBILITY_LOST", "0")

    # The pre-fix shape (no store hash) must stay honestly unverifiable: a
    # null hash can never be promoted to a claimed chain.
    null_fields = dict(fields, store_data_fnv="null")
    assert _sp05_stage_verdict(null_fields) == ("RELOAD_UNVERIFIABLE", "null")

    skipped = next(e for e in events
                   if e.get("event_type") == "sp05_write_skipped")
    skipped_fields = _sp05_detail(skipped["detail"])
    assert skipped_fields["write_skipped"] == "1"
    assert skipped_fields["mem_sent"] == "0"
    assert skipped_fields["store_data_fnv"] == store_fnv
