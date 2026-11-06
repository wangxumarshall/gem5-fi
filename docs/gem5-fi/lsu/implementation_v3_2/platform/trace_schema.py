"""Shared constants for Trace v3.1 records.

The JSON Schema is the published contract; these tuples are the validator's
stdlib implementation of the same contract (jsonschema is not a dependency of
this repository).
"""
from __future__ import annotations

import json
from pathlib import Path

TRACE_VERSION = "v3.1"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "LSU_Trace_Schema_v3.2.json"

RUN_STATUS = ("COMPLETED", "NO_ELIGIBLE_EVENT", "TIMEOUT", "SIMULATOR_ERROR")
ACTIVATION = ("NOT_TRIGGERED", "TRIGGERED", "UNKNOWN")
TERMINAL = ("MASKED", "SQUASHED", "DETECTED_CONTAINED",
            "ARCH_STATE_CORRUPTION", "SDC", "CRASH", "HANG", "UNRESOLVED")
COMPLETENESS = ("COMPLETE", "INCOMPLETE")
INJECTION_STATUS = ("INJECTED", "NO_CHANGE", "DECLINED", "NOT_APPLICABLE")
COMMIT_STATUS = ("NOT_COMMITTED", "COMMITTED", "SQUASHED", "UNKNOWN")
SQUASH_STATUS = ("NONE", "SQUASHED", "UNKNOWN")

EVENT_FIELDS = (
    "record_type", "trace_version", "sample_run_id", "run_id", "sub_task_id",
    "fault_id", "fault_model_id", "injection_event_id", "event_id",
    "parent_event_id", "event_type", "unit", "sub_unit", "timestamp",
    "dyn_inst_seq", "execution_attempt_id", "replay_generation", "commit_seq",
    "source_event_id", "destination_event_id", "propagation_edge_id",
    "producer_inst_seq", "consumer_inst_seq", "request_id", "response_id",
    "fragment_id", "va", "pa", "lq_entry_id", "sq_entry_id",
    "entry_generation", "old_value", "new_value", "injection_status",
    "activation_status", "commit_status", "squash_status", "terminal_state",
    "trace_completeness",
)

EDGE_FIELDS = (
    "record_type", "trace_version", "event_type", "sample_run_id", "fault_id",
    "fault_model_id", "propagation_edge_id", "source_event_id",
    "destination_event_id", "producer_inst_seq", "consumer_inst_seq",
    "edge_kind", "value_hash", "trace_completeness",
)

SUMMARY_FIELDS = (
    "record_type", "trace_version", "sample_run_id", "fault_id",
    "fault_model_id", "run_status", "fault_activation_status",
    "terminal_state", "trace_completeness", "counts",
)

IDENTITY_FIELDS = ("sample_run_id", "run_id", "sub_task_id", "fault_id",
                   "fault_model_id", "injection_event_id")


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def schema_required(kind: str) -> tuple[str, ...]:
    defs = load_schema()["$defs"]
    return tuple(defs[kind]["required"])
