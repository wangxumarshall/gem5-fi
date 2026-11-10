#!/usr/bin/env python3
"""Convert a CHAOSPropagation CSV trace into Trace v3.1 JSONL.

The CSV is the gem5-side real trace (one row per propagation node). This
adapter preserves its node identity, dyn_inst_seq, request id, address and
detail fields, and emits the full v3.1 field set plus separate
``propagation_edge`` records. Fields gem5 does not expose (replay generation,
LQ/SQ entry generation, response id) are written as null, never guessed.

RP01 log bridge (LSU v3.2.12 Task 15): the committed RP01 hook in binary
SHA 68c6ce73... prints ``RP01_SKIP_REPLAY`` to the run log only — the prop
trace carries the skipped load's ``replay`` marker (``noteReplay`` fires
before the guarded call) but no injection record, so the audit pipeline
would grade ``NO_INJECTION_EVENT``. ``--rp01-skip-log`` parses the single
real skip line and emits it as the trace injection record. Every field is
taken verbatim from the log line; the record carries the raw line, the log
path and the log SHA256 as provenance. The bridge refuses zero/multiple
skip lines, a line missing required fields, and a CSV trace that already
has an injection record — a bridged record is never fabricated and never
duplicated.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path

PLATFORM = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLATFORM))

from trace_writer import TraceWriter  # noqa: E402

KIND_MAP = {
    "inj": "injection",
    "inj_nochange": "injection_nochange",
    "inj_store_data": "injection",
    "inj_store_be": "injection",
    "inj_l1dfwd": "injection",
    "inj_md04": "injection",
    "inj_fw05": "injection",
    "inj_sq03": "injection",
    "inj_sp05": "injection",
    "sq03_wb": "store_writeback",
    "sq03_complete": "sq03_complete",
    "sp05_complete": "sp05_complete",
    "store_wb": "store_writeback",
    "store_mem": "store_mem_write",
    "store_overwrite": "store_overwrite",
    "addr_form": "address_formed",
    "mem_req": "memory_request",
    "resp": "memory_response",
    "taint_reg": "register_writeback",
    "consumer": "consumer_commit",
    "taint_value_mismatch": "taint_value_mismatch",
    "errant_commit": "errant_commit",
    "funnel": "funnel",
    "fwd": "forwarding_decision",
    "commit": "commit",
    "lq_lifecycle": "lq_lifecycle",
    "sq_lifecycle": "sq_lifecycle",
    "replay": "replay",
    "squash": "squash",
    "prop_edge": "propagation_edge",
}
UNIT_MAP = {
    "inj": ("AGU", "injection"),
    "inj_nochange": ("AGU", "injection_nochange"),
    "inj_store_data": ("SQ", "store_data"),
    "inj_store_be": ("SQ", "byte_enable"),
    "inj_l1dfwd": ("L1D", "load_response_data"),
    "inj_md04": ("MD", "dependency_violation"),
    "inj_fw05": ("FWD", "wrong_source_forward"),
    "inj_sq03": ("SQ", "writeback_permission"),
    "inj_sp05": ("SQ", "completion"),
    "sq03_wb": ("SQ", "writeback"),
    "sq03_complete": ("SQ", "complete"),
    "sp05_complete": ("SQ", "complete"),
    "store_wb": ("SQ", "writeback"),
    "store_mem": ("L1D", "memory_write"),
    "store_overwrite": ("SQ", "overwrite"),
    "addr_form": ("AGU", "effective_address"),
    "mem_req": ("LSQ", "request"),
    "resp": ("L1D", "response"),
    "taint_reg": ("RF", "writeback"),
    "consumer": ("Commit", "consumer"),
    "taint_value_mismatch": ("Commit", "taint_value_mismatch"),
    "errant_commit": ("Commit", "errant_commit"),
    "funnel": ("Funnel", "counts"),
    "fwd": ("FWD", "Store-to-Load Forwarding"),
    "commit": ("Commit", "commit"),
    "lq_lifecycle": ("LSQ", "LQ lifecycle"),
    "sq_lifecycle": ("LSQ", "SQ lifecycle"),
    "replay": ("LSQ", "replay"),
    "squash": ("LSQ", "squash"),
}


def _detail(text: str) -> dict[str, str]:
    out = {}
    for item in (text or "").split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            out[key.strip()] = value.strip()
    return out


def _hex(value: str | None) -> str | None:
    if not value:
        return None
    value = value.lower()
    return value if value.startswith("0x") else "0x" + value


def _int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value, 0)
    except ValueError:
        return None


# RP01 log bridge (LSU v3.2.12): the exact stdout line
# CHAOSLSQFwd::maybeSkipPartialReplay prints when it skips the
# rescheduleMemInst call (CHAOSLSQFwd.cc, `RP01_SKIP_REPLAY ordinal=...`).
# Every field below is printed by that one line; the bridge never derives
# or guesses a value that is not on it.
RP01_SKIP_PREFIX = "RP01_SKIP_REPLAY"
RP01_SKIP_INT_FIELDS = (
    "ordinal", "load_seq", "load_pc", "lq_idx", "lq_gen", "store_seq",
    "replay_gen_pre", "replay_gen_post", "in_instsToReplay_pre",
    "in_instsToReplay_post", "tick")


def parse_rp01_skip_line(log_path: Path) -> dict:
    """Parse the single real ``RP01_SKIP_REPLAY`` line from a gem5 run log.

    Returns a dict with every integer field of the line plus ``raw_line``.
    Refuses (SystemExit) when the log carries zero or multiple skip lines,
    or when the line is missing a required field or carries a non-integer
    value — a bridged injection record must come from the real line, never
    be completed by hand.
    """
    log_path = Path(log_path)
    text = log_path.read_text(encoding="utf-8", errors="replace")
    lines = [ln.strip() for ln in text.splitlines()
             if ln.strip().startswith(RP01_SKIP_PREFIX)]
    if not lines:
        raise SystemExit(
            f"REFUSE: no {RP01_SKIP_PREFIX} line in {log_path} — nothing to "
            f"bridge (a control log has no skip and must not be bridged)")
    if len(lines) > 1:
        raise SystemExit(
            f"REFUSE: {len(lines)} {RP01_SKIP_PREFIX} lines in {log_path} "
            f"(expected exactly 1; RP01 is one-shot)")
    raw = lines[0]
    fields: dict[str, str] = {}
    for token in raw.split():
        if "=" in token:
            key, _, value = token.partition("=")
            fields[key.strip()] = value.strip()
    absent = [name for name in RP01_SKIP_INT_FIELDS if name not in fields]
    if absent:
        raise SystemExit(
            f"REFUSE: {RP01_SKIP_PREFIX} line in {log_path} is missing "
            f"fields {absent} — refusing to bridge an incomplete line")
    out: dict = {"raw_line": raw}
    for name in RP01_SKIP_INT_FIELDS:
        try:
            out[name] = int(fields[name], 0)
        except ValueError:
            raise SystemExit(
                f"REFUSE: {RP01_SKIP_PREFIX} field {name}={fields[name]!r} "
                f"in {log_path} is not an integer")
    return out


def _bridge_rp01_injection(w, log_path: Path, declared: str) -> int:
    """Emit the log-bridged RP01 injection record (see module docstring).

    The record carries every field of the real skip line, the raw line
    itself, and the log path + SHA256 as provenance. It has no CSV node
    (``source_node_id=None``, ``ptag=0``): the chain identity is the
    skipped load's ``dyn_inst_seq``, which the call-site ``replay`` marker
    (emitted by ``noteReplay`` before the guarded call) shares.
    """
    skip = parse_rp01_skip_line(log_path)
    log_sha = hashlib.sha256(
        Path(log_path).read_bytes()).hexdigest()
    detail = (
        "site=read_partial_reschedule;skipped_call=1"
        f";ordinal={skip['ordinal']}"
        f";load_seq={skip['load_seq']}"
        f";load_pc={skip['load_pc']}"
        f";pc={hex(skip['load_pc'])}"
        f";lq_idx={skip['lq_idx']}"
        f";lq_gen={skip['lq_gen']}"
        f";store_seq={skip['store_seq']}"
        f";replay_gen_pre={skip['replay_gen_pre']}"
        f";replay_gen_post={skip['replay_gen_post']}"
        f";in_instsToReplay_pre={skip['in_instsToReplay_pre']}"
        f";in_instsToReplay_post={skip['in_instsToReplay_post']}"
        f";tick={skip['tick']}"
        f";source_log={log_path}"
        f";source_log_sha256={log_sha}"
        ";bridge=rp01_skip_replay_log")
    return w.event(
        "injection",
        parent_event_id=None,
        injection_event_id=1,
        dyn_inst_seq=skip["load_seq"],
        timestamp=skip["tick"],
        unit="LSQ", sub_unit="partial_replay_reschedule",
        lq_entry_id=skip["lq_idx"],
        entry_generation=skip["lq_gen"],
        replay_generation=skip["replay_gen_post"],
        injection_status="INJECTED",
        activation_status="TRIGGERED",
        commit_status="UNKNOWN",
        squash_status="UNKNOWN",
        trace_completeness=("COMPLETE" if declared == "COMPLETE"
                            else "INCOMPLETE"),
        detail=detail,
        source_node_id=None,
        ptag=0,
        event_ordinal=skip["ordinal"],
        store_seq=skip["store_seq"],
        rp01_replay_gen_pre=skip["replay_gen_pre"],
        rp01_in_instsToReplay_pre=skip["in_instsToReplay_pre"],
        rp01_in_instsToReplay_post=skip["in_instsToReplay_post"],
        rp01_load_pc=skip["load_pc"],
        source_log=str(log_path),
        source_log_sha256=log_sha,
        rp01_skip_replay_line=skip["raw_line"])


def convert(csv_path: Path, out_path: Path, *, sample_run_id: str, run_id: str,
            sub_task_id: str, fault_id: str, fault_model_id: str,
            run_status: str, activation: str, terminal: str,
            completeness: str, terminal_reason: str | None = None,
            observed_terminal: str | None = None,
            fault_causality: str | None = None,
            terminal_evidence: dict | None = None,
            no_summary: bool = False,
            allow_truncated_complete: bool = False,
            rp01_skip_log: Path | None = None) -> dict:
    rows = []
    truncated = False
    try:
        with gzip.open(csv_path, "rt", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if line.startswith("#"):
                    continue
                if not line.strip():
                    continue
                rows.append(next(csv.reader([line])))
    except (EOFError, OSError):
        truncated = True

    if allow_truncated_complete and terminal != "CRASH":
        raise SystemExit("REFUSE: a truncated stream may only be completed for CRASH")
    declared = "INCOMPLETE" if truncated and not allow_truncated_complete else completeness
    if not no_summary and declared == "INCOMPLETE" and terminal == "MASKED":
        raise SystemExit("REFUSE: incomplete trace cannot be MASKED")

    w = TraceWriter(out_path, sample_run_id, run_id, sub_task_id,
                    fault_id, fault_model_id)
    last_by_ptag: dict[int, int] = {}
    injection_by_ptag: dict[int, int] = {}
    node_to_event: dict[int, int] = {}
    next_injection = 0
    csv_injection_seen = False
    for row in rows:
        if len(row) < 10:
            continue
        node_id, tick, ptag, kind, dyn_seq, req_id, addr, phys, arch, detail = row[:10]
        ptag_i = int(ptag or 0)
        kind = kind.strip()
        if (rp01_skip_log is not None
                and KIND_MAP.get(kind, kind) in ("injection",
                                                 "injection_nochange")):
            csv_injection_seen = True
        d = _detail(detail)
        if kind == "prop_edge":
            src = _int(d.get("source_event_id"))
            dst = _int(d.get("destination_event_id"))
            if src is None or dst is None or src not in node_to_event or dst not in node_to_event:
                continue
            w.edge(node_to_event[src], node_to_event[dst],
                   producer_inst_seq=_int(d.get("producer_inst_seq")),
                   consumer_inst_seq=_int(d.get("consumer_inst_seq")),
                   edge_kind=d.get("edge_type") or "data",
                   value_hash=(None if d.get("source_value_hash") in (None, "null")
                               else d.get("source_value_hash")),
                   source_value_hash=(None if d.get("source_value_hash") in (None, "null")
                                      else d.get("source_value_hash")),
                   destination_value_hash=(None if d.get("destination_value_hash") in (None, "null")
                                           else d.get("destination_value_hash")),
                   edge_type=d.get("edge_type") or "data",
                   trace_completeness=("COMPLETE" if declared == "COMPLETE"
                                       else "INCOMPLETE"))
            continue
        old_addr = _hex(d.get("old_addr"))
        new_addr = _hex(d.get("new_addr")) or _hex(addr)
        injection_status = "NOT_APPLICABLE"
        if kind in ("inj", "inj_nochange", "inj_store_data", "inj_store_be",
                    "inj_sp05"):
            injection_status = ("NO_CHANGE" if kind == "inj_nochange"
                                or d.get("value_changed") == "0"
                                else "INJECTED")
            next_injection += 1
            injection_by_ptag[ptag_i] = next_injection
        injection_event_id = injection_by_ptag.get(ptag_i, 1)
        activation_status = ("TRIGGERED"
                             if (ptag_i > 0 or kind in ("inj", "inj_nochange",
                                                        "inj_store_data",
                                                        "inj_sp05"))
                             and kind != "taint_value_mismatch"
                             else "UNKNOWN")
        commit_status = ("COMMITTED" if kind in ("consumer", "errant_commit", "commit")
                         else "UNKNOWN")
        squash_status = "SQUASHED" if kind == "squash" else "UNKNOWN"
        unit, sub_unit = UNIT_MAP.get(kind, ("Unknown", kind))
        if kind in ("lq_lifecycle", "sq_lifecycle"):
            sub_unit = d.get("action") or kind
        # LQ04 (v3.2.10): its injection row reuses the generic "inj" kind;
        # bind it to the Load Queue so the record names the faulted
        # structure instead of the AGU default.
        if kind == "inj" and d.get("family") == "lq04":
            unit, sub_unit = "LQ", "executeLoad"
        # Address and data are separate fields. resp/t_aint carry actual
        # packet/writeback data; fwd carries the forwarded buffer.
        if kind == "resp":
            va, pa = None, _hex(addr)
            old_value = None
            new_value = d.get("data_hex") or d.get("data_fnv")
        elif kind in ("addr_form", "mem_req"):
            va, pa = _hex(addr), None
            old_value, new_value = old_addr, new_addr
        elif kind == "taint_reg":
            va, pa = None, None
            old_value = None
            new_value = d.get("writeback_value") or d.get("writeback_fnv")
        elif kind == "inj_store_data":
            va, pa = _hex(d.get("addr")), None
            old_value = d.get("old_byte")
            new_value = d.get("new_byte")
        elif kind == "inj_store_be":
            va, pa = _hex(d.get("addr_before")), None
            old_value = d.get("old_be")
            new_value = d.get("new_be")
        elif kind == "store_wb":
            va, pa = _hex(d.get("addr")), None
            old_value = None
            new_value = d.get("data_fnv")
        elif kind == "store_mem":
            va, pa = None, _hex(d.get("blk_addr"))
            old_value = d.get("before_hex")
            new_value = d.get("after_hex")
        elif kind == "inj_l1dfwd":
            va, pa = None, _hex(d.get("addr"))
            old_value = d.get("orig_data_hex")
            new_value = d.get("inj_data_hex")
        elif kind == "inj_md04":
            va, pa = _hex(d.get("addr")), None
            old_value, new_value = None, None
        elif kind == "inj_fw05":
            va, pa = _hex(d.get("load_addr")), None
            old_value = d.get("true_data_fnv")
            new_value = d.get("alt_data_fnv")
        elif kind == "inj_sq03":
            va, pa = _hex(d.get("store_addr")), None
            old_value = d.get("canwb_before")
            new_value = d.get("canwb_after")
        elif kind == "inj_sp05":
            va, pa = _hex(d.get("store_addr")), None
            old_value = d.get("completed_before")
            new_value = d.get("completed_after")
        elif kind in ("lq_lifecycle", "sq_lifecycle"):
            va, pa = None, None
            old_value, new_value = None, None
        elif kind == "fwd":
            va, pa = _hex(d.get("byte_begin")), None
            old_value = d.get("store_data_hex") or d.get("store_data_fnv")
            new_value = d.get("forward_data_hex") or d.get("forward_data_fnv")
        else:
            va, pa = None, None
            old_value, new_value = old_addr, new_addr
        parent = last_by_ptag.get(ptag_i)
        if ptag_i == 0:
            parent = None
        if kind == "consumer" and d.get("source_event_id") in node_to_event:
            parent = node_to_event[int(d["source_event_id"])]
        extra = {}
        if kind == "inj_store_be":
            extra = {
                "original_byte_enable": d.get("old_be"),
                "injected_byte_enable": d.get("new_be"),
                "changed_bit": _int(d.get("changed_bit")),
                "address_before": _hex(d.get("addr_before")),
                "address_after": _hex(d.get("addr_after")),
                "access_size_before": _int(d.get("size_before")),
                "access_size_after": _int(d.get("size_after")),
                "store_data_before": d.get("store_data_fnv"),
                "store_data_after": d.get("store_data_fnv"),
            }
        if kind == "inj_md04":
            extra = {
                "load_seq": _int(d.get("load_seq")),
                "store_seq": _int(d.get("store_seq")),
                "eligible_event_ordinal": _int(d.get("eligible_ordinal")),
                "load_complete_at_injection": _int(d.get("load_complete")),
                "violation_report_suppressed": _int(
                    d.get("violation_report_suppressed")),
                # v3.2.7 frozen target-pair identity.
                "target_pair_id": d.get("target_pair_id"),
                "older_store_dyn_inst_seq": _int(
                    d.get("older_store_dyn_inst_seq")),
                "younger_load_dyn_inst_seq": _int(
                    d.get("younger_load_dyn_inst_seq")),
                "store_addr": _hex(d.get("store_addr")),
                "load_addr": _hex(d.get("load_addr")) or _hex(d.get("addr")),
                "store_size": _int(d.get("store_size")),
                "load_size": _int(d.get("load_size")) or _int(d.get("size")),
                "load_pc": _hex(d.get("load_pc")),
                "store_pc": _hex(d.get("store_pc")),
                "sq_entry_generation": _int(d.get("sq_entry_generation")),
                "lq_entry_generation": _int(d.get("lq_entry_generation")),
                "violation_tick": _int(d.get("violation_tick")),
                "eligible_violation_pair_ordinal": _int(
                    d.get("eligible_violation_pair_ordinal")),
                "event_ordinal": _int(d.get("event_ordinal")),
                "seed": _int(d.get("seed")),
                "load_request_id": _int(d.get("load_request_id")),
                "address_modified": _int(d.get("address_modified")),
                "size_modified": _int(d.get("size_modified")),
                "data_modified": _int(d.get("data_modified")),
            }
        if kind == "inj_sp05":
            extra = {
                "store_seq": _int(d.get("store_seq")),
                "store_pc": _hex(d.get("store_pc")),
                "store_addr": _hex(d.get("store_addr")),
                "store_size": _int(d.get("store_size")),
                "sq_entry_generation": _int(d.get("sq_entry_generation")),
                "completed_before": _int(d.get("completed_before")),
                "completed_after": _int(d.get("completed_after")),
                "stores_to_wb_before": _int(d.get("stores_to_wb_before")),
                "stores_to_wb_after": _int(d.get("stores_to_wb_after")),
                "mem_sent": _int(d.get("mem_sent")),
                "inject_tick": _int(d.get("inject_tick")),
                "eligible_ordinal": _int(d.get("eligible_ordinal")),
                "event_ordinal": _int(d.get("event_ordinal")),
            }
        if kind == "inj_sq03":
            extra = {
                "store_seq": _int(d.get("store_seq")),
                "store_pc": _hex(d.get("store_pc")),
                "store_addr": _hex(d.get("store_addr")),
                "store_size": _int(d.get("store_size")),
                "sq_entry_generation": _int(d.get("sq_entry_generation")),
                "canwb_before": _int(d.get("canwb_before")),
                "canwb_after": _int(d.get("canwb_after")),
                "stores_to_wb_before": _int(d.get("stores_to_wb_before")),
                "stores_to_wb_after": _int(d.get("stores_to_wb_after")),
                "inject_tick": _int(d.get("inject_tick")),
                "eligible_ordinal": _int(d.get("eligible_ordinal")),
                "event_ordinal": _int(d.get("event_ordinal")),
                "seed": _int(d.get("seed")),
                "address_modified": _int(d.get("address_modified")),
                "size_modified": _int(d.get("size_modified")),
                "data_modified": _int(d.get("data_modified")),
            }
        if kind == "sq03_wb":
            extra = {
                "store_seq": _int(d.get("store_seq")),
                "writeback_tick": _int(d.get("writeback_tick")),
                "inject_tick": _int(d.get("inject_tick")),
                "canwb_after": _int(d.get("canwb_after")),
                "stores_to_wb_after": _int(d.get("stores_to_wb_after")),
            }
        if kind == "sq03_complete":
            extra = {
                "store_seq": _int(d.get("store_seq")),
                "complete_tick": _int(d.get("complete_tick")),
                "writeback_tick": _int(d.get("writeback_tick")),
                "inject_tick": _int(d.get("inject_tick")),
            }
        if kind == "inj_fw05":
            extra = {
                "target_pair_id": d.get("target_pair_id"),
                "load_seq": _int(d.get("load_seq")),
                "load_pc": _hex(d.get("load_pc")),
                "true_store_seq": _int(d.get("true_store_seq")),
                "alt_store_seq": _int(d.get("alt_store_seq")),
                "true_addr": _hex(d.get("true_addr")),
                "alt_addr": _hex(d.get("alt_addr")),
                "load_addr": _hex(d.get("load_addr")),
                "load_size": _int(d.get("load_size")),
                "true_store_size": _int(d.get("true_store_size")),
                "alt_store_size": _int(d.get("alt_store_size")),
                "true_data_fnv": d.get("true_data_fnv"),
                "alt_data_fnv": d.get("alt_data_fnv"),
                "selected_source": d.get("selected_source"),
                "wrong_source_substitution": _int(
                    d.get("wrong_source_substitution")),
                "data_differs": _int(d.get("data_differs")),
                "sq_entry_generation": _int(d.get("sq_entry_generation")),
                "lq_entry_generation": _int(d.get("lq_entry_generation")),
                "eligible_forwarding_pair_ordinal": _int(
                    d.get("eligible_forwarding_pair_ordinal")),
                "event_ordinal": _int(d.get("event_ordinal")),
                "seed": _int(d.get("seed")),
                "address_modified": _int(d.get("address_modified")),
                "size_modified": _int(d.get("size_modified")),
            }
        if kind == "inj_l1dfwd":
            extra = {
                "original_data_hex": d.get("orig_data_hex"),
                "original_data_fnv": d.get("orig_data_fnv"),
                "injected_data_hex": d.get("inj_data_hex"),
                "injected_data_fnv": d.get("inj_data_fnv"),
                "fault_mask": _int(d.get("mask")),
                "eligible_event_ordinal": _int(d.get("eligible_ordinal")),
                "request_timestamp": _int(d.get("request_tick")),
                "lq_entry_generation": _int(d.get("entry_generation")),
            }
        if kind == "fwd":
            extra = {
                "store_seq": _int(d.get("store_seq")),
                "load_seq": _int(d.get("load_seq")),
                "byte_begin": _hex(d.get("byte_begin")),
                "byte_end": _hex(d.get("byte_end")),
                "forward_decision": d.get("decision"),
                "normal_decision": d.get("normal_decision"),
                "fault_decision": d.get("fault_decision"),
                "memory_path": _int(d.get("memory_path")),
                "store_data_fnv": d.get("store_data_fnv"),
                "forward_data_fnv": d.get("forward_data_fnv"),
            }
        eid = w.event(
            KIND_MAP.get(kind, kind),
            parent_event_id=parent,
            injection_event_id=injection_event_id,
            dyn_inst_seq=_int(dyn_seq),
            execution_attempt_id=_int(d.get("execution_attempt_id")),
            replay_generation=_int(d.get("replay_generation")),
            commit_seq=_int(d.get("commit_seq")),
            timestamp=int(tick or 0),
            unit=unit, sub_unit=sub_unit,
            request_id=_int(d.get("request_id")) or _int(req_id),
            response_id=_int(d.get("response_id")),
            fragment_id=_int(d.get("fragment_id")),
            # CSV node ids are not JSONL event ids (rows can be skipped);
            # map through the converted node registry when possible.
            source_event_id=node_to_event.get(
                _int(d.get("source_event_id")),
                _int(d.get("source_event_id"))),
            destination_event_id=node_to_event.get(
                _int(d.get("destination_event_id")),
                _int(d.get("destination_event_id"))),
            lq_entry_id=(_int(d.get("index")) if kind == "lq_lifecycle"
                         else _int(d.get("lq_entry_id"))),
            sq_entry_id=(_int(d.get("index"))
                         if kind in ("sq_lifecycle", "inj_store_data")
                         else _int(d.get("sq_entry_id"))),
            # inj_store_be/store_wb carry sq_entry_id directly; the expression
            # above already reads it for every non-lifecycle kind.
            entry_generation=(_int(d.get("generation")) or
                              _int(d.get("entry_generation")) or
                              _int(d.get("lq_entry_generation")) or
                              _int(d.get("sq_entry_generation"))),
            va=va, pa=pa,
            old_value=old_value,
            new_value=new_value,
            injection_status=injection_status,
            activation_status=activation_status,
            commit_status=commit_status,
            squash_status=squash_status,
            trace_completeness="COMPLETE" if declared == "COMPLETE" else "INCOMPLETE",
            detail=detail,
            source_node_id=int(node_id or 0),
            ptag=ptag_i,
            **extra,
        )
        node_to_event[int(node_id or 0)] = eid
        prev = last_by_ptag.get(ptag_i)
        # consumer edges are emitted explicitly from taint-set dependencies;
        # do not manufacture a ptag-order edge for them.
        if prev is not None and ptag_i > 0 and kind not in (
                "consumer", "replay", "squash", "funnel"):
            # Preserve the data hashes on synthesized ptag-order edges instead
            # of writing a null-hash edge (v3.2.5 edge-integrity fix).
            def _node_hash(rec):
                rd = _detail(rec.get("detail", ""))
                return (rd.get("data_fnv") or rd.get("inj_data_fnv")
                        or rd.get("writeback_value_fnv")
                        or rd.get("packet_data_fnv"))
            src_hash = _node_hash(w._nodes.get(prev, {}))
            dst_hash = _node_hash(w._nodes.get(eid, {}))
            w.edge(prev, eid, edge_kind=kind, edge_type="ptag_sequence",
                   value_hash=src_hash,
                   source_value_hash=src_hash,
                   destination_value_hash=dst_hash,
                   trace_completeness=("COMPLETE" if declared == "COMPLETE"
                                       else "INCOMPLETE"))
        last_by_ptag[ptag_i] = eid

    # RP01 log bridge: emit the injection record from the real skip line.
    # Placed after the CSV loop so the record lands on the fault's chain by
    # dyn_inst_seq identity (the call-site replay marker shares it); the
    # record is never fabricated and never duplicated (a trace that already
    # carries an injection — e.g. a future binary emitting inj_rp01 nodes —
    # refuses the bridge).
    if rp01_skip_log is not None:
        if csv_injection_seen:
            raise SystemExit(
                "REFUSE: --rp01-skip-log given but the CSV trace already "
                "carries an injection record; the bridge is only for the "
                "RP01 binary whose hook prints the skip to the log without "
                "a trace record")
        _bridge_rp01_injection(w, rp01_skip_log, declared)

    if not no_summary and terminal == "CRASH":
        # The simulator aborted before its normal trailer. Record the abort
        # itself as the terminal event, with the structured fault evidence,
        # so the terminal does not live only in stderr text.
        detail = ("gzip truncation observed" if truncated else
                  "simulator abort after last completed node")
        if terminal_evidence:
            detail += (";page_table_fault_addr={};last_injection_dyn_seq={}"
                       ";address_match={}").format(
                           terminal_evidence.get("page_table_fault_addr"),
                           terminal_evidence.get("last_injection_dyn_seq"),
                           terminal_evidence.get("address_match"))
        w.event("simulator_abort", unit="Simulator", sub_unit="abort",
                terminal_state="CRASH", commit_status="UNKNOWN",
                squash_status="UNKNOWN", trace_completeness=declared,
                fault_causality=fault_causality,
                terminal_evidence=terminal_evidence,
                detail=detail)
    if no_summary:
        w.abort()
        return {"rows": len(rows), "truncated": truncated, "summary": None}
    summary = w.close(run_status=run_status, activation=activation,
                      terminal=terminal, completeness=declared,
                      terminal_state_reason=terminal_reason,
                      observed_terminal=observed_terminal,
                      fault_causality=fault_causality,
                      terminal_evidence=terminal_evidence)
    return {"rows": len(rows), "truncated": truncated, "summary": summary}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("csv")
    ap.add_argument("out")
    ap.add_argument("--sample-run-id", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--sub-task-id", required=True)
    ap.add_argument("--fault-id", required=True)
    ap.add_argument("--fault-model-id", required=True)
    ap.add_argument("--run-status", required=True)
    ap.add_argument("--activation", required=True)
    ap.add_argument("--terminal", required=True)
    ap.add_argument("--completeness", required=True)
    ap.add_argument("--terminal-reason", default=None)
    ap.add_argument("--observed-terminal", default=None,
                    help="the raw observed terminal when it differs from the "
                         "trace terminal state (an externally cut run is "
                         "written terminal HANG + observed TIMEOUT + reason "
                         "RP01_EXTERNAL_TIMEOUT; TIMEOUT is a run_status, "
                         "not a TERMINAL enum value)")
    ap.add_argument("--no-summary", action="store_true",
                    help="write events/edges only when the trace is incomplete")
    ap.add_argument("--allow-truncated-complete", action="store_true",
                    help="accept a gzip-truncated stream when a terminal CRASH "
                         "event is appended (abort is the terminal state)")
    ap.add_argument("--rp01-skip-log", default=None, type=Path,
                    help="RP01 bridge: parse the single real "
                         "RP01_SKIP_REPLAY line from this gem5 run log "
                         "(stdout.log / lsq_fwd_injections.log) and emit it "
                         "as the trace injection record — binary SHA "
                         "68c6ce73... prints the skip to the log only. "
                         "Every record field comes from the line; refuses "
                         "zero/multiple lines, an incomplete line, or a "
                         "trace that already has an injection record")
    args = ap.parse_args(argv)
    result = convert(
        Path(args.csv), Path(args.out),
        sample_run_id=args.sample_run_id, run_id=args.run_id,
        sub_task_id=args.sub_task_id, fault_id=args.fault_id,
        fault_model_id=args.fault_model_id, run_status=args.run_status,
        activation=args.activation, terminal=args.terminal,
        completeness=args.completeness, terminal_reason=args.terminal_reason,
        observed_terminal=args.observed_terminal,
        no_summary=args.no_summary,
        allow_truncated_complete=args.allow_truncated_complete,
        rp01_skip_log=(Path(args.rp01_skip_log)
                       if args.rp01_skip_log else None))
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
