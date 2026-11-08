"""Stdlib validator for Trace v3.1 JSONL files.

Checks the same required fields and enums as
``LSU_Trace_Schema_v3.2.json`` plus cross-record integrity (unique event/edge
ids, edge endpoints exist, exactly one trailing summary, consistent identity).
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path
from typing import Any

from trace_schema import (
    ACTIVATION, COMMIT_STATUS, COMPLETENESS, EDGE_FIELDS, EVENT_FIELDS,
    INJECTION_STATUS, RUN_STATUS, SQUASH_STATUS, SUMMARY_FIELDS, TERMINAL,
    TRACE_VERSION,
)


def read_records(path: Path) -> list[dict[str, Any]]:
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    records: list[dict[str, Any]] = []
    with opener(path, "rt", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                records.append({"__parse_error__": f"line {line_no}: {exc}"})
                continue
            rec["__line__"] = line_no
            records.append(rec)
    return records


def validate_records(records: list[dict[str, Any]]) -> list[str]:
    errs: list[str] = []
    events: dict[int, dict[str, Any]] = {}
    edge_ids: set[int] = set()
    summaries: list[dict[str, Any]] = []
    sample_ids: set[str] = set()

    for rec in records:
        line = rec.get("__line__", "?")
        if "__parse_error__" in rec:
            errs.append(rec["__parse_error__"])
            continue
        if rec.get("trace_version") != TRACE_VERSION:
            errs.append(f"line {line}: trace_version must be {TRACE_VERSION!r}")
        kind = rec.get("record_type")
        if kind == "event":
            missing = [k for k in EVENT_FIELDS if k not in rec]
            if missing:
                errs.append(f"line {line}: event missing fields {missing}")
            eid = rec.get("event_id")
            if not isinstance(eid, int) or eid < 1:
                errs.append(f"line {line}: event_id must be a positive integer")
            elif eid in events:
                errs.append(f"line {line}: duplicate event_id {eid}")
            else:
                events[eid] = rec
            for field_name, allowed in (
                ("injection_status", INJECTION_STATUS),
                ("activation_status", ACTIVATION),
                ("commit_status", COMMIT_STATUS),
                ("squash_status", SQUASH_STATUS),
                ("trace_completeness", COMPLETENESS),
            ):
                value = rec.get(field_name)
                if value not in allowed:
                    errs.append(f"line {line}: {field_name}={value!r} not in {allowed}")
            terminal = rec.get("terminal_state")
            if terminal is not None and terminal not in TERMINAL:
                errs.append(f"line {line}: terminal_state={terminal!r} not in {TERMINAL}")
            for key in ("sample_run_id", "run_id", "sub_task_id", "fault_id",
                        "fault_model_id", "event_type"):
                if not isinstance(rec.get(key), str) or not rec.get(key):
                    errs.append(f"line {line}: {key} must be a non-empty string")
            if isinstance(rec.get("sample_run_id"), str):
                sample_ids.add(rec["sample_run_id"])
        elif kind == "propagation_edge":
            missing = [k for k in EDGE_FIELDS if k not in rec]
            if missing:
                errs.append(f"line {line}: edge missing fields {missing}")
            peid = rec.get("propagation_edge_id")
            if not isinstance(peid, int) or peid < 1:
                errs.append(f"line {line}: propagation_edge_id must be a positive integer")
            elif peid in edge_ids:
                errs.append(f"line {line}: duplicate propagation_edge_id {peid}")
            else:
                edge_ids.add(peid)
            if rec.get("event_type") != "propagation_edge":
                errs.append(f"line {line}: edge event_type must be 'propagation_edge'")
            if rec.get("trace_completeness") not in COMPLETENESS:
                errs.append(f"line {line}: bad edge trace_completeness")
            if not rec.get("edge_type"):
                errs.append(f"line {line}: edge missing edge_type")
            # Value hashes are required to be PRESENT-or-explicitly-null, not
            # universally non-null: vector/matrix consumers legitimately have
            # no scalar hash. Continuity is checked by trace_completeness only
            # when both endpoints expose a hash (v3.2.5 Review Focus #4).
            if isinstance(rec.get("sample_run_id"), str):
                sample_ids.add(rec["sample_run_id"])
        elif kind == "summary":
            missing = [k for k in SUMMARY_FIELDS if k not in rec]
            if missing:
                errs.append(f"line {line}: summary missing fields {missing}")
            for field_name, allowed in (
                ("run_status", RUN_STATUS),
                ("fault_activation_status", ACTIVATION),
                ("terminal_state", TERMINAL),
                ("trace_completeness", COMPLETENESS),
            ):
                value = rec.get(field_name)
                if value not in allowed:
                    errs.append(f"line {line}: {field_name}={value!r} not in {allowed}")
            if rec.get("trace_completeness") == "INCOMPLETE" and rec.get("terminal_state") == "MASKED":
                errs.append(f"line {line}: incomplete trace cannot be MASKED")
            counts = rec.get("counts")
            if not isinstance(counts, dict) or not all(
                    k in counts for k in ("events", "edges", "injections", "activations")):
                errs.append(f"line {line}: summary counts must contain events/edges/injections/activations")
            summaries.append(rec)
            if isinstance(rec.get("sample_run_id"), str):
                sample_ids.add(rec["sample_run_id"])
        else:
            errs.append(f"line {line}: unknown record_type {kind!r}")

    # Two-pass endpoint and parent checks.
    for rec in events.values():
        parent = rec.get("parent_event_id")
        if parent is not None and parent not in events:
            errs.append(f"event {rec.get('event_id')}: parent_event_id {parent} does not exist")
        # v3.2.7: an event's detail may restate its execution attempt; the
        # restated value must agree with the record field, otherwise a
        # cross-attempt chain is built from contradictory identities.
        if rec.get("event_type") == "memory_response":
            embedded = None
            for item in (rec.get("detail") or "").split(";"):
                if item.startswith("execution_attempt_id="):
                    embedded = item.split("=", 1)[1]
            if embedded is not None and rec.get("execution_attempt_id") is not None:
                try:
                    if int(embedded, 0) != rec.get("execution_attempt_id"):
                        errs.append(
                            f"event {rec.get('event_id')}: detail "
                            f"execution_attempt_id={embedded} disagrees with "
                            f"record field")
                except ValueError:
                    pass
    def _detail(text: str) -> dict[str, str]:
        return dict(item.split("=", 1) for item in (text or "").split(";")
                    if "=" in item)

    for rec in records:
        if rec.get("record_type") != "propagation_edge":
            continue
        for key in ("source_event_id", "destination_event_id"):
            target = rec.get(key)
            if target not in events:
                errs.append(
                    f"edge {rec.get('propagation_edge_id')}: {key}={target} is not an event")
        if rec.get("edge_type") != "register_dataflow":
            continue
        src = events.get(rec.get("source_event_id"))
        dst = events.get(rec.get("destination_event_id"))
        if not src or not dst:
            continue
        sd = _detail(src.get("detail"))
        dd = _detail(dst.get("detail"))
        src_hash = sd.get("writeback_value_fnv") or sd.get("consumer_output_fnv")
        dst_in = dd.get("consumer_input_fnv")
        dst_out = dd.get("consumer_output_fnv")
        if src_hash and rec.get("source_value_hash") and \
                src_hash != rec.get("source_value_hash"):
            errs.append(
                f"edge {rec.get('propagation_edge_id')}: source_value_hash "
                f"does not match source event output hash")
        # The edge carries the propagated input on source and the consumer's
        # new destination value on destination. The consumer's input must be
        # the propagated value; its output is the destination hash.
        if dst_out and rec.get("destination_value_hash") and \
                dst_out != rec.get("destination_value_hash"):
            errs.append(
                f"edge {rec.get('propagation_edge_id')}: destination_value_hash "
                f"does not match consumer output hash")
        if dst_in and rec.get("source_value_hash") and \
                dst_in != rec.get("source_value_hash"):
            errs.append(
                f"edge {rec.get('propagation_edge_id')}: consumer input hash "
                f"does not match propagated source hash")
        if dst.get("event_type") != "consumer_commit":
            errs.append(
                f"edge {rec.get('propagation_edge_id')}: register_dataflow "
                f"destination is not a consumer_commit")
        if rec.get("producer_inst_seq") != src.get("dyn_inst_seq"):
            errs.append(
                f"edge {rec.get('propagation_edge_id')}: producer_inst_seq "
                f"does not match source dyn_inst_seq")
        if rec.get("consumer_inst_seq") != dst.get("dyn_inst_seq"):
            errs.append(
                f"edge {rec.get('propagation_edge_id')}: consumer_inst_seq "
                f"does not match destination dyn_inst_seq")
    # v3.2.4: an injection_event_id must not mix different ptag chains.
    # This is the record-level guard against stitching a "complete" chain out
    # of events from different dynamic instructions.
    id_ptag: dict[int, int] = {}
    injection_ids: set[int] = set()
    for rec in events.values():
        ptag = rec.get("ptag") or 0
        if ptag <= 0:
            continue
        iid = rec.get("injection_event_id")
        if iid is None:
            continue
        if rec.get("event_type") in ("injection", "injection_nochange"):
            injection_ids.add(iid)
        prev = id_ptag.get(iid)
        if prev is None:
            id_ptag[iid] = ptag
        elif prev != ptag:
            errs.append(
                f"event {rec.get('event_id')}: injection_event_id {iid} "
                f"mixes ptag {prev} and {ptag}")
    for iid in id_ptag:
        if iid not in injection_ids:
            errs.append(
                f"injection_event_id {iid} has events but no injection event")

    if len(summaries) != 1:
        errs.append(f"expected exactly one summary record, got {len(summaries)}")
    elif records and summaries[0].get("__line__") != records[-1].get("__line__"):
        errs.append("summary record must be the last line")
    if len(sample_ids) > 1:
        errs.append(f"trace mixes sample_run_id values: {sorted(sample_ids)}")
    if summaries:
        summary = summaries[0]
        counts = summary.get("counts") or {}
        if counts.get("events") != len(events):
            errs.append(
                f"summary events={counts.get('events')} but trace has {len(events)}")
        if counts.get("edges") != len(edge_ids):
            errs.append(
                f"summary edges={counts.get('edges')} but trace has {len(edge_ids)}")
    return errs


def validate(path: Path) -> list[str]:
    return validate_records(read_records(path))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print("usage: trace_validator.py <trace.jsonl[.gz]>", file=sys.stderr)
        return 2
    errs = validate(Path(argv[0]))
    if errs:
        print("INVALID")
        for err in errs:
            print(f"  {err}")
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    sys.exit(main())
