import gzip
import json
from pathlib import Path

from tools.prop_trace_to_v31 import convert


def test_md04_identity_fields_survive_conversion(tmp_path: Path):
    csv = tmp_path / "p.csv.gz"
    with gzip.open(csv, "wt", encoding="utf-8") as fh:
        fh.write(
            "1,100,1,inj_md04,17443,67,0x491990,0,0,"
            "site=LSQUnit::checkViolations;family=md04;"
            "target_pair_id=MD04-MD04-F6-W7-S01-R03:17443:17442;"
            "store_addr=0x491990;store_size=8;load_pc=0x400530;"
            "store_pc=0x40052c;eligible_violation_pair_ordinal=3;"
            "event_ordinal=3;seed=2545691512;load_request_id=67;"
            "lq_entry_id=748;lq_entry_generation=1235;"
            "load_size=8;eligible_ordinal=3;load_seq=17443;store_seq=17442;"
            "address_modified=0;size_modified=0;data_modified=0\n")
    out = tmp_path / "o.jsonl"
    convert(csv, out, sample_run_id="MD04-R03", run_id="MD04-F6-W7",
            sub_task_id="MD04-F6-W7-S01", fault_id="MD04-CFG01",
            fault_model_id="MD04", run_status="COMPLETED",
            activation="TRIGGERED", terminal="MASKED", completeness="COMPLETE",
            no_summary=True)
    events = [json.loads(line) for line in out.read_text().splitlines()]
    inj = [e for e in events if e.get("event_type") == "injection"][0]
    assert inj["target_pair_id"] == "MD04-MD04-F6-W7-S01-R03:17443:17442"
    assert int(inj["store_addr"], 16) == 0x491990
    assert inj["store_size"] == 8
    assert inj["load_size"] == 8
    assert int(inj["load_pc"], 16) == 0x400530
    assert int(inj["store_pc"], 16) == 0x40052c
    assert inj["eligible_violation_pair_ordinal"] == 3
    assert inj["event_ordinal"] == 3
    assert inj["seed"] == 2545691512
    assert inj["load_request_id"] == 67
    assert inj["lq_entry_id"] == 748
    assert inj["lq_entry_generation"] == 1235
    assert inj["address_modified"] == 0
    assert inj["size_modified"] == 0
    assert inj["data_modified"] == 0
