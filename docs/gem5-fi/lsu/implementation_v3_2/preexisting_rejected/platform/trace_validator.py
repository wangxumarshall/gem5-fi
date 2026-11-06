"""Minimal Trace v3.1 JSONL validator (stdlib only)."""
from __future__ import annotations
import json, sys
from pathlib import Path

REQUIRED_EVENT = {"sample_run_id","fault_id","fault_model_id","event_id","parent_event_id","event_type","trace_completeness"}
REQUIRED_EDGE = {"sample_run_id","fault_id","propagation_edge_id","source_event_id","destination_event_id","event_type"}

def validate(path: Path) -> list[str]:
    errs=[]; events=0; edges=0
    for n,line in enumerate(path.read_text(encoding="utf-8").splitlines(),1):
        if not line.strip(): continue
        try: rec=json.loads(line)
        except Exception as e:
            errs.append(f"line {n}: invalid JSON: {e}"); continue
        if rec.get("event_type")=="propagation_edge":
            edges+=1
            miss=REQUIRED_EDGE-set(rec)
        elif rec.get("event_type")=="summary":
            continue
        else:
            events+=1
            miss=REQUIRED_EVENT-set(rec)
        if miss: errs.append(f"line {n}: missing {sorted(miss)}")
        if rec.get("trace_completeness") not in (None,"COMPLETE","INCOMPLETE"):
            errs.append(f"line {n}: bad trace_completeness")
    if not events: errs.append("no events")
    return errs

if __name__=="__main__":
    if len(sys.argv)!=2:
        print("usage: trace_validator.py <trace.jsonl>"); sys.exit(2)
    errs=validate(Path(sys.argv[1]))
    print("VALID" if not errs else "INVALID\n"+"\n".join(errs))
    sys.exit(0 if not errs else 1)
