"""JSONL Trace v3.1 writer with independent PropagationEdge records."""
from __future__ import annotations
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

@dataclass
class TraceWriter:
    path: Path
    sample_run_id: str
    fault_id: str
    fault_model_id: str
    _event_id: int = 0
    _edge_id: int = 0
    _nodes: dict[int,dict] = field(default_factory=dict)

    def __post_init__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(self.path, "w", encoding="utf-8")

    def event(self, kind: str, *, parent_event_id: int|None = None,
              dyn_inst_seq: int|None = None, execution_attempt_id: int|None = None,
              replay_generation: int|None = None, unit: str|None = None,
              sub_unit: str|None = None, old_value: Any=None, new_value: Any=None,
              commit_status: str="not_committed", squash_status: str="none",
              terminal_state: str="UNKNOWN", trace_completeness: str="INCOMPLETE",
              **extra) -> int:
        self._event_id += 1
        eid = self._event_id
        rec = {"sample_run_id":self.sample_run_id,"fault_id":self.fault_id,
               "fault_model_id":self.fault_model_id,"injection_event_id":1,
               "event_id":eid,"parent_event_id":parent_event_id,
               "dyn_inst_seq":dyn_inst_seq,"execution_attempt_id":execution_attempt_id,
               "replay_generation":replay_generation,"event_type":kind,
               "microarchitecture_unit":unit,"sub_unit":sub_unit,
               "old_value":old_value,"new_value":new_value,
               "commit_status":commit_status,"squash_status":squash_status,
               "terminal_state":terminal_state,"trace_completeness":trace_completeness,
               "timestamp":extra.pop("timestamp",0)}
        rec.update(extra)
        self._nodes[eid]=rec
        self.fh.write(json.dumps(rec,ensure_ascii=False,default=str)+"\n")
        return eid

    def edge(self, source_event_id: int, destination_event_id: int, *,
             producer_inst_seq: int|None=None, consumer_inst_seq: int|None=None,
             kind: str="data", value_hash: str|None=None) -> int:
        self._edge_id += 1
        rec = {"sample_run_id":self.sample_run_id,"fault_id":self.fault_id,
               "propagation_edge_id":self._edge_id,
               "source_event_id":source_event_id,
               "destination_event_id":destination_event_id,
               "producer_inst_seq":producer_inst_seq,
               "consumer_inst_seq":consumer_inst_seq,
               "edge_kind":kind,"value_hash":value_hash,
               "event_type":"propagation_edge","trace_completeness":"COMPLETE"}
        self.fh.write(json.dumps(rec,ensure_ascii=False,default=str)+"\n")
        return self._edge_id

    def close(self, run_status="COMPLETED", activation="TRIGGERED",
              terminal="UNKNOWN", completeness="INCOMPLETE", trace_completeness=None):
        if trace_completeness is not None: completeness=trace_completeness
        rec = {"sample_run_id":self.sample_run_id,"fault_id":self.fault_id,
               "fault_model_id":self.fault_model_id,"event_type":"summary",
               "run_status":run_status,"fault_activation_status":activation,
               "terminal_state":terminal,"trace_completeness":completeness}
        self.fh.write(json.dumps(rec,ensure_ascii=False)+"\n")
        self.fh.close()
