"""Parse the frozen LSU Excel design into a validated run configuration.

Seed authority: the Excel SampleRunID -> Seed mapping. No seed generation here.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import Counter
import openpyxl

REQUIRED = ["SampleRunID","RunID","SubTaskID","Seed","FaultModelID","FaultLocation",
            "TargetField","BitEntryByteIndex","NormalValue","FaultValue","InjectionMode",
            "InjectionTiming","FaultDuration","TargetInstruction","EligibleEventCondition",
            "EventOrdinal","WorkloadPath","BinarySHA256","Oracle","WarmUp","ROI",
            "OutputDir","DecisionStatus","RunStatus","FaultActivationStatus",
            "TerminalState_v31","TraceCompleteness_v31"]

class ConfigError(RuntimeError): pass

def load_config(xlsx: Path) -> dict:
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    ws = wb["5.60个样本执行矩阵"]
    hdr = [ws.cell(1,c).value for c in range(1, ws.max_column+1)]
    missing = [h for h in REQUIRED if h not in hdr]
    if missing:
        raise ConfigError(f"missing required columns: {missing}")
    rows = []
    for r in range(2, ws.max_row+1):
        if not ws.cell(r,1).value: continue
        row = {hdr[c-1]: ws.cell(r,c).value for c in range(1, ws.max_column+1)}
        rows.append(row)
    samples = [x["SampleRunID"] for x in rows]
    if len(samples) != len(set(samples)):
        dup = [k for k,v in Counter(samples).items() if v>1]
        raise ConfigError(f"duplicate SampleRunID: {dup[:5]}")
    seeds = [x["Seed"] for x in rows]
    if len(seeds) != len(set(seeds)):
        raise ConfigError("duplicate Seed in samples")
    models = sorted({x["FaultModelID"] for x in rows})
    if len(models) != 12:
        raise ConfigError(f"expected 12 models, got {len(models)}: {models}")
    for x in rows:
        for k in ("ModelID","FaultModelID"):
            pass
        if not str(x["SampleRunID"]).startswith(str(x["SubTaskID"])+"-R"):
            raise ConfigError(f"SampleRunID/SubTaskID parent mismatch: {x['SampleRunID']}")
        if not str(x["SubTaskID"]).startswith(str(x["RunID"])+"-S"):
            raise ConfigError(f"SubTaskID/RunID parent mismatch: {x['SubTaskID']}")
    return {"source": str(xlsx), "models": models, "samples": rows,
            "counts": {"samples":len(rows),"models":len(models),"seeds":len(set(seeds))}}

if __name__ == "__main__":
    if len(sys.argv)!=3:
        print("usage: config_parser.py <excel> <out.json>"); sys.exit(2)
    cfg = load_config(Path(sys.argv[1]))
    Path(sys.argv[2]).write_text(json.dumps(cfg,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    print(f"OK samples={cfg['counts']['samples']} models={cfg['counts']['models']} seeds={cfg['counts']['seeds']}")
