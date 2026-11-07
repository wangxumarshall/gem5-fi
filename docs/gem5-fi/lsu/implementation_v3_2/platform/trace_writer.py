"""Trace v3.1 JSONL writer.

Every event record contains the full field set from
``LSU_Trace_Schema_v3.2.json``; fields the microarchitecture cannot supply are
written as JSON null rather than omitted or guessed.  Propagation is always a
separate ``propagation_edge`` record.  The writer refuses to close a trace that
would report ``MASKED`` with ``INCOMPLETE`` completeness.
"""
from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TextIO

from trace_schema import (
    ACTIVATION, COMMIT_STATUS, COMPLETENESS, EDGE_FIELDS, EVENT_FIELDS,
    INJECTION_STATUS, RUN_STATUS, SQUASH_STATUS, TERMINAL, TRACE_VERSION,
)


class TraceWriteError(ValueError):
    pass


@dataclass
class TraceWriter:
    path: Path
    sample_run_id: str
    run_id: str
    sub_task_id: str
    fault_id: str
    fault_model_id: str
    _event_id: int = 0
    _edge_id: int = 0
    _nodes: dict[int, dict[str, Any]] = field(default_factory=dict)
    _counts: dict[str, int] = field(default_factory=lambda: {
        "events": 0, "edges": 0, "injections": 0, "activations": 0})
    _fh: TextIO | None = field(default=None, init=False, repr=False)
    _closed: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.suffix == ".gz":
            self._fh = gzip.open(self.path, "wt", encoding="utf-8", compresslevel=1)
        else:
            self._fh = self.path.open("w", encoding="utf-8")
        for key in ("sample_run_id", "run_id", "sub_task_id", "fault_id", "fault_model_id"):
            if not getattr(self, key):
                raise TraceWriteError(f"{key} must be non-empty")

    # -- writing ---------------------------------------------------------
    def event(self, event_type: str, *, parent_event_id: int | None = None,
              injection_event_id: int = 1, **fields: Any) -> int:
        if self._closed or self._fh is None:
            raise TraceWriteError("writer is closed")
        self._event_id += 1
        eid = self._event_id
        rec: dict[str, Any] = {name: None for name in EVENT_FIELDS}
        rec.update({
            "record_type": "event",
            "trace_version": TRACE_VERSION,
            "sample_run_id": self.sample_run_id,
            "run_id": self.run_id,
            "sub_task_id": self.sub_task_id,
            "fault_id": self.fault_id,
            "fault_model_id": self.fault_model_id,
            "injection_event_id": injection_event_id,
            "event_id": eid,
            "parent_event_id": parent_event_id,
            "event_type": event_type,
            "timestamp": 0,
            "injection_status": "NOT_APPLICABLE",
            "activation_status": "UNKNOWN",
            "commit_status": "UNKNOWN",
            "squash_status": "UNKNOWN",
            "trace_completeness": "INCOMPLETE",
        })
        rec.update(fields)
        self._validate_event(rec)
        self._write(rec)
        self._nodes[eid] = rec
        self._counts["events"] += 1
        if (rec.get("injection_status") in ("INJECTED", "NO_CHANGE")
                or event_type in ("injection", "injection_nochange")):
            self._counts["injections"] += 1
        if rec.get("activation_status") == "TRIGGERED":
            self._counts["activations"] += 1
        return eid

    def edge(self, source_event_id: int, destination_event_id: int, *,
             producer_inst_seq: int | None = None,
             consumer_inst_seq: int | None = None,
             edge_kind: str = "data", value_hash: str | None = None,
             source_value_hash: str | None = None,
             destination_value_hash: str | None = None,
             edge_type: str | None = None,
             trace_completeness: str = "INCOMPLETE") -> int:
        if self._closed or self._fh is None:
            raise TraceWriteError("writer is closed")
        if source_event_id not in self._nodes or destination_event_id not in self._nodes:
            raise TraceWriteError(
                f"orphan propagation edge: {source_event_id} -> {destination_event_id}")
        self._edge_id += 1
        src = self._nodes[source_event_id]
        dst = self._nodes[destination_event_id]
        rec = {name: None for name in EDGE_FIELDS}
        rec.update({
            "record_type": "propagation_edge",
            "trace_version": TRACE_VERSION,
            "event_type": "propagation_edge",
            "sample_run_id": self.sample_run_id,
            "fault_id": self.fault_id,
            "fault_model_id": self.fault_model_id,
            "propagation_edge_id": self._edge_id,
            "source_event_id": source_event_id,
            "destination_event_id": destination_event_id,
            "producer_inst_seq": (producer_inst_seq if producer_inst_seq is not None
                                  else src.get("dyn_inst_seq")),
            "consumer_inst_seq": (consumer_inst_seq if consumer_inst_seq is not None
                                  else dst.get("dyn_inst_seq")),
            "edge_kind": edge_kind,
            "value_hash": value_hash,
            "source_value_hash": source_value_hash,
            "destination_value_hash": destination_value_hash,
            "edge_type": edge_type,
            "trace_completeness": trace_completeness,
        })
        if trace_completeness not in COMPLETENESS:
            raise TraceWriteError(f"bad edge trace_completeness {trace_completeness!r}")
        self._write(rec)
        self._counts["edges"] += 1
        return self._edge_id

    def close(self, *, run_status: str, activation: str, terminal: str,
              completeness: str, terminal_state_reason: str | None = None,
              observed_terminal: str | None = None,
              fault_causality: str | None = None,
              terminal_evidence: dict | None = None) -> dict:
        if self._closed or self._fh is None:
            raise TraceWriteError("writer is already closed")
        if run_status not in RUN_STATUS:
            raise TraceWriteError(f"bad run_status {run_status!r}")
        if activation not in ACTIVATION:
            raise TraceWriteError(f"bad activation {activation!r}")
        if terminal not in TERMINAL:
            raise TraceWriteError(f"bad terminal state {terminal!r}")
        if completeness not in COMPLETENESS:
            raise TraceWriteError(f"bad completeness {completeness!r}")
        if completeness == "INCOMPLETE" and terminal == "MASKED":
            raise TraceWriteError(
                "incomplete trace cannot be classified MASKED (v3.2 honesty rule)")
        summary = {
            "record_type": "summary",
            "trace_version": TRACE_VERSION,
            "sample_run_id": self.sample_run_id,
            "fault_id": self.fault_id,
            "fault_model_id": self.fault_model_id,
            "run_status": run_status,
            "fault_activation_status": activation,
            "terminal_state": terminal,
            "observed_terminal": observed_terminal or terminal,
            "trace_completeness": completeness,
            "terminal_state_reason": terminal_state_reason,
            "fault_causality": fault_causality,
            "terminal_evidence": terminal_evidence,
            "counts": dict(self._counts),
        }
        self._write(summary)
        self._fh.close()
        self._closed = True
        return summary

    def abort(self) -> None:
        """Close without a summary. Used only when the trace is known to be
        incomplete; the validator and completeness checker then report the
        missing summary instead of a fabricated terminal verdict."""
        if not self._closed and self._fh is not None:
            self._fh.close()
            self._closed = True

    def __enter__(self) -> "TraceWriter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if not self._closed and self._fh is not None:
            self._fh.close()
            self._closed = True

    # -- helpers ---------------------------------------------------------
    def _write(self, rec: dict[str, Any]) -> None:
        assert self._fh is not None
        self._fh.write(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n")
        self._fh.flush()

    def _validate_event(self, rec: dict[str, Any]) -> None:
        missing = [k for k in EVENT_FIELDS if k not in rec]
        if missing:
            raise TraceWriteError(f"event missing fields: {missing}")
        if rec["record_type"] != "event":
            raise TraceWriteError("record_type must be event")
        if rec["trace_version"] != TRACE_VERSION:
            raise TraceWriteError("trace_version must be v3.1")
        for field_name, allowed in (
            ("injection_status", INJECTION_STATUS),
            ("activation_status", ACTIVATION),
            ("commit_status", COMMIT_STATUS),
            ("squash_status", SQUASH_STATUS),
            ("trace_completeness", COMPLETENESS),
        ):
            if rec[field_name] not in allowed:
                raise TraceWriteError(f"{field_name}={rec[field_name]!r} not in {allowed}")
        if rec["terminal_state"] is not None and rec["terminal_state"] not in TERMINAL:
            raise TraceWriteError(f"terminal_state={rec['terminal_state']!r} not in {TERMINAL}")
