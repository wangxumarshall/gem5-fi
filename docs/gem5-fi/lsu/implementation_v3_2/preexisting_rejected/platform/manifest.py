"""Run manifest generation. Reads config JSON; never generates seeds."""
from __future__ import annotations
import json, hashlib, sys
from pathlib import Path

def sha(p: Path) -> str:
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def manifest(cfg: dict, sample_id: str, gem5: Path, config_script: Path) -> dict:
    row=next((x for x in cfg["samples"] if x["SampleRunID"]==sample_id),None)
    if row is None: raise KeyError(f"SampleRunID not found: {sample_id}")
    wl=row.get("WorkloadPath")
    if not wl or wl=="ABSENT" or not Path(wl).exists():
        raise FileNotFoundError(f"workload missing for {sample_id}: {wl}")
    return {"schema_version":"lsu-run-manifest-v3.2","sample_run_id":sample_id,
            "run_id":row["RunID"],"sub_task_id":row["SubTaskID"],"model_id":row["FaultModelID"],
            "seed":row["Seed"],"seed_source":"excel:5.60个样本执行矩阵",
            "fault_location":row["FaultLocation"],"target_field":row["TargetField"],
            "target_bit":row["BitEntryByteIndex"],"normal_value":row["NormalValue"],
            "fault_value":row["FaultValue"],"injection_mode":row["InjectionMode"],
            "injection_timing":row["InjectionTiming"],"workload":{"path":wl,"sha256":sha(Path(wl))},
            "warmup":row["WarmUp"],"roi":row["ROI"],"target_event":row["EligibleEventCondition"],
            "gem5":{"binary":str(gem5),"binary_sha256":sha(gem5),
                    "config_script":str(config_script)},
            "output_dir":row["OutputDir"]}
if __name__=="__main__":
    if len(sys.argv)!=6:
        print("usage: manifest.py <config.json> <sample_id> <gem5> <config_script> <out.json>"); sys.exit(2)
    cfg=json.load(open(sys.argv[1],encoding="utf-8"))
    m=manifest(cfg,sys.argv[2],Path(sys.argv[3]),Path(sys.argv[4]))
    Path(sys.argv[5]).write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding="utf-8")
    print("OK",m["sample_run_id"],"seed",m["seed"])
