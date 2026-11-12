#!/usr/bin/env python3
"""Qualified-evidence rules for the LSU v3.3.3 formal campaign (Agent D).

``qualified_evidence(model, run_dir)`` inspects **only** ``run_dir`` (its
summary, logs, ``trace_v31.jsonl`` and ``prop_trace.csv[.gz]``).  It never
reads historical audit tables and never imports campaign-wide summaries, so a
formal run is graded from its own evidence or it is graded non-PASS.

Return contract (README_INTERFACES.md):

    keys: model, required_fields, found, missing, status, terminal_rule,
          evidence
    status: PASS | QUALIFIED | TRACE_INCOMPLETE

Semantics of ``status`` (evidence completeness, **not** an oracle verdict):

* ``PASS``              every model-specific causal-chain field was found and
                        the trace/log evidence source is complete/readable.
                        An ORACLE_FAIL/SDC terminal can still be a PASS here:
                        the measured terminal is reported by the collector,
                        not by this module.
* ``QUALIFIED``         the evidence source is readable and complete, but one
                        or more required causal-chain fields is absent.  A
                        QUALIFIED result is never upgraded to PASS.
* ``TRACE_INCOMPLETE``  the trace/log evidence is missing, truncated or cut
                        by a watchdog/timeout, so the causal chain cannot be
                        established from this run dir.

Only A03, SP05 and RP01 carry extra rules.  Every other model returns
``status='PASS'`` with empty ``required_fields``/``missing`` lists: those nine
models are graded by the collector, not here.

File ownership: this file is written by Agent D.  Do not edit the collector,
the runner, the control module or any C++/data file from here.
"""
from __future__ import annotations

import gzip
import json
import re
from pathlib import Path
from typing import Any, Iterable

__all__ = ["qualified_evidence", "QUALIFIED_MODELS"]

QUALIFIED_MODELS = ("A03", "SP05", "RP01")

# ---------------------------------------------------------------------------
# small parsers
# ---------------------------------------------------------------------------

_HEX16 = re.compile(r"(?m)^([0-9a-fA-F]{16})\s*$")


def _json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _lines(path: Path) -> list[str]:
    return _text(path).splitlines()


def _kv(text: str | None) -> dict[str, str]:
    """Parse ``key=value;key=value`` fragments (values may contain ``=``)."""
    out: dict[str, str] = {}
    if not text:
        return out
    for part in text.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, val = part.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def _tokens_kv(text: str | None) -> dict[str, str]:
    """Parse whitespace- or ``;``-separated ``key=value`` tokens (RP01 logs)."""
    out: dict[str, str] = {}
    if not text:
        return out
    for tok in re.split(r"[;\s]+", text.strip()):
        if "=" in tok:
            key, val = tok.split("=", 1)
            out[key.strip()] = val.strip()
    return out


def _first(predicate, items: Iterable[Any]):
    for item in items:
        if predicate(item):
            return item
    return None


def _int_or_none(value: Any) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _boolish(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("1", "true", "yes"):
        return True
    if text in ("0", "false", "no"):
        return False
    return None


def _hex16(text: str) -> str | None:
    found = _HEX16.findall(text)
    return found[-1].lower() if found else None


_ABSENT = {"", "none", "null", "n/a", "na", "unknown", "?"}


def _present(value: Any) -> bool:
    """True only for a real observed value (never a placeholder/null token)."""
    if value is None:
        return False
    return str(value).strip().lower() not in _ABSENT


def _oracle(path: Path) -> dict[str, Any]:
    """Return the oracle.log observations without inventing anything."""
    out: dict[str, Any] = {"present": path.exists()}
    text = _text(path)
    out["line"] = text.strip() or None
    m = re.search(r"expected=([0-9a-fA-F]+)\s+got=([0-9a-fA-F]+)", text)
    if m:
        out["expected"] = m.group(1).lower()
        out["got"] = m.group(2).lower()
    if "ORACLE_PASS" in text:
        out["verdict"] = "PASS"
    elif "ORACLE_FAIL" in text:
        out["verdict"] = "FAIL"
    else:
        out["verdict"] = None
    return out


# ---------------------------------------------------------------------------
# trace readers
# ---------------------------------------------------------------------------

_PROP_KINDS = ("resp", "taint_reg", "prop_edge", "consumer", "commit")


def _scan_prop_trace(run_dir: Path, target_seq: str | None = None) -> tuple[dict, bool, dict]:
    """Stream prop_trace.csv[.gz] once.

    Returns ``(records, complete, meta)``.  ``complete`` is False when the
    file is missing or a gzip/read error interrupts the stream (truncated
    evidence).  Record retention is deliberately narrow: only the kinds needed
    to link one target dynamic instruction are kept.
    """
    gz = run_dir / "prop_trace.csv.gz"
    plain = run_dir / "prop_trace.csv"
    if gz.exists():
        opener = lambda: gzip.open(gz, "rt", encoding="utf-8", errors="replace")
        source = str(gz)
    elif plain.exists():
        opener = lambda: plain.open(encoding="utf-8", errors="replace")
        source = str(plain)
    else:
        return {}, False, {"trace": None, "reason": "prop_trace absent"}

    records: dict[str, Any] = {
        "resp": None, "taint_reg": [], "prop_edge": [], "consumer": {}, "commit": None,
    }
    complete = False
    rows = 0
    try:
        with opener() as fh:
            for raw in fh:
                if raw.startswith("#"):
                    continue
                parts = raw.rstrip("\n").split(",")
                if len(parts) < 10:
                    continue
                rows += 1
                kind = parts[3]
                if kind not in _PROP_KINDS:
                    continue
                detail = ",".join(parts[9:])
                row = {
                    "node_id": parts[0],
                    "tick": parts[1],
                    "ptag": parts[2],
                    "kind": kind,
                    "dyn_inst_seq": parts[4],
                    "request_id": parts[5],
                    "addr": parts[6],
                    "phys_reg": parts[7],
                    "arch_reg": parts[8],
                    "detail": detail,
                    "kv": _kv(detail),
                }
                if target_seq is not None:
                    if kind == "prop_edge":
                        # Keep only edges produced by the target instruction.
                        if row["kv"].get("producer_inst_seq") != target_seq:
                            continue
                    elif kind == "consumer":
                        pass  # consumers are keyed by source_event_id below
                    elif row["dyn_inst_seq"] != target_seq:
                        continue
                if kind == "resp" and records["resp"] is None:
                    records["resp"] = row
                elif kind == "taint_reg":
                    records["taint_reg"].append(row)
                elif kind == "prop_edge":
                    records["prop_edge"].append(row)
                elif kind == "commit" and records["commit"] is None:
                    records["commit"] = row
                elif kind == "consumer":
                    src = row["kv"].get("source_event_id")
                    if src is not None:
                        records["consumer"].setdefault(src, row)
        complete = True
    except (EOFError, OSError, ValueError):
        complete = False
    return records, complete, {"trace": source, "rows_scanned": rows}


def _scan_trace_v31(run_dir: Path) -> tuple[dict[str, list[dict]], bool, dict]:
    """Read trace_v31.jsonl completely; a JSON truncation marks it incomplete."""
    path = run_dir / "trace_v31.jsonl"
    if not path.exists():
        return {}, False, {"trace": None, "reason": "trace_v31 absent"}
    by_type: dict[str, list[dict]] = {}
    complete = True
    rows = 0
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    rec = json.loads(raw)
                except ValueError:
                    complete = False
                    continue
                if not isinstance(rec, dict):
                    continue
                rows += 1
                etype = rec.get("event_type") or rec.get("record_type") or "None"
                by_type.setdefault(etype, []).append(rec)
    except OSError:
        complete = False
    return by_type, complete, {"trace": str(path), "rows_scanned": rows}


def _trace_record_kv(rec: dict, *names: str) -> dict[str, str]:
    """Merge selected top-level values with the parsed ``detail`` fragment."""
    kv = _kv(rec.get("detail"))
    for name in names:
        if rec.get(name) is not None and name not in kv:
            kv[name] = str(rec[name])
    return kv


# ---------------------------------------------------------------------------
# A03
# ---------------------------------------------------------------------------

A03_FIELDS = (
    "persistent_stuck_lifecycle",
    "stuck_at_active",
    "selected_event_first_activated",
    "first_downstream_instruction_affected",
    "first_affected_load_dyn_seq",
    "first_affected_load_pc",
    "load_result",
    "register_writeback",
    "consumer",
    "application_checksum",
    "internal_watchdog_reason",
)


def _a03(run_dir: Path) -> tuple[dict, list[str], str]:
    summary = _json(run_dir / "summary.json")
    a03 = summary.get("a03") or {}
    log = _lines(run_dir / "addrpath_injections.log")
    stdout = _text(run_dir / "stdout.log")
    stderr = _text(run_dir / "stderr.log")
    oracle = _oracle(run_dir / "oracle.log")

    lifecycle = a03.get("lifecycle") or _first(
        lambda ln: ln.startswith("A03_STUCK_LIFECYCLE:"), log)
    activation = a03.get("first_activation") or _first(
        lambda ln: ln.startswith("A03_ACTIVATION:"), log)

    def _stream_affected(line: str | None) -> dict[str, str]:
        kv = _tokens_kv(line.split(":", 1)[1] if line and ":" in line else line)
        return kv

    affected_line = a03.get("first_affected")
    aff = _stream_affected(affected_line)
    if not (aff.get("affected") == "1" and aff.get("reason") == "STUCK_APPLIED"):
        # The summary's "first_affected" must really be an applied downstream
        # fault; otherwise locate the first STUCK_APPLIED stream row itself.
        log_affected = _first(
            lambda ln: ln.startswith("A03_STREAM:")
            and "affected=1" in ln and "reason=STUCK_APPLIED" in ln, log)
        if log_affected is not None:
            affected_line = log_affected
            aff = _stream_affected(log_affected)
    affected_ok = aff.get("affected") == "1" and aff.get("reason") == "STUCK_APPLIED"

    # The three distinct A03 events must not be collapsed into one another.
    lifecycle_kv = _kv(lifecycle.split(":", 1)[1] if lifecycle and ":" in lifecycle else lifecycle)
    applications = _int_or_none(lifecycle_kv.get("applications"))
    stuck_applied_streams = [
        ln for ln in log
        if ln.startswith("A03_STREAM:") and "reason=STUCK_APPLIED" in ln
    ]

    seq = aff.get("dyn_inst_seq")
    trace, trace_complete, trace_meta = _scan_prop_trace(run_dir, target_seq=seq)

    resp = trace.get("resp") if seq else None
    taint = _first(lambda row: row["dyn_inst_seq"] == seq, trace.get("taint_reg", [])) if seq else None

    # Link taint_reg -> propagation edge -> consumer instruction.
    consumer = None
    edge = None
    if taint is not None:
        edges = trace.get("prop_edge", [])
        candidates = [e for e in edges if e["kv"].get("source_event_id") == taint["node_id"]]
        if not candidates:
            candidates = [e for e in edges
                          if e["kv"].get("producer_inst_seq") == taint["dyn_inst_seq"]]
        edge = candidates[0] if candidates else None
    if edge is not None:
        dest = edge["kv"].get("destination_event_id")
        consumer = trace.get("consumer", {}).get(dest)
        if consumer is None:
            # Fall back to the first consumer of the target's edge chain; the
            # edge record above still binds the producer to this instruction.
            consumer = next(iter(trace.get("consumer", {}).values()), None)

    checksum = summary.get("checksum")
    if not checksum:
        checksum = _hex16(stdout)
    checksum = str(checksum).lower() if checksum else None
    golden = oracle.get("expected") or summary.get("golden_checksum")
    golden = str(golden).lower() if golden else None

    watchdog = _first(
        lambda ln: "A03_WATCHDOG_EXPIRED" in ln or "A03_WATCHDOG" in ln,
        stdout.splitlines() + stderr.splitlines())
    watchdog_conf = _boolish(a03.get("watchdog_expired", summary.get("watchdog_expired")))

    values: dict[str, Any] = {
        "persistent_stuck_lifecycle": lifecycle,
        "stuck_at_active": None,
        "selected_event_first_activated": activation,
        "first_downstream_instruction_affected": affected_line if affected_ok else None,
        "first_affected_load_dyn_seq": seq if affected_ok else None,
        "first_affected_load_pc": aff.get("pc") if affected_ok else None,
        "load_result": None,
        "register_writeback": None,
        "consumer": None,
        "application_checksum": checksum,
        "application_golden_checksum": golden,
        "internal_watchdog_reason": watchdog
        or (f"watchdog_expired={watchdog_conf}" if watchdog_conf is not None else None),
        "first_affected_event_ordinal": aff.get("event_ordinal"),
        "first_affected_reason": aff.get("reason"),
        "load_golden_ea": aff.get("golden_ea"),
        "load_actual_ea": aff.get("actual_ea"),
        "trace_present": trace_meta.get("trace") is not None,
        "trace_complete": trace_complete,
        "trace_rows_scanned": trace_meta.get("rows_scanned"),
    }

    if lifecycle is not None and (applications is not None and applications > 0
                                  or stuck_applied_streams):
        values["stuck_at_active"] = (
            f"applications={applications};stuck_applied_streams={len(stuck_applied_streams)}")
    if resp is not None and (_present(resp["kv"].get("data_hex"))
                             or _present(resp["kv"].get("data_fnv"))):
        values["load_result"] = (
            f"data_hex={resp['kv'].get('data_hex')};"
            f"data_fnv={resp['kv'].get('data_fnv')};"
            f"request_id={resp['kv'].get('request_id')}")
    if taint is not None and any(
            _present(taint["kv"].get(k)) for k in
            ("arch_reg", "phys_reg", "writeback_value_fnv", "writeback_value")):
        values["register_writeback"] = (
            f"arch_reg={taint['kv'].get('arch_reg')};"
            f"phys_reg={taint['kv'].get('phys_reg')};"
            f"writeback_value_fnv={taint['kv'].get('writeback_value_fnv')};"
            f"writeback_value={taint['kv'].get('writeback_value')}")
    if consumer is not None and (_present(consumer["kv"].get("pc"))
                                 or _present(consumer["dyn_inst_seq"])):
        values["consumer"] = (
            f"dyn_inst_seq={consumer['dyn_inst_seq']};"
            f"pc={consumer['kv'].get('pc')};"
            f"src_idx={consumer['kv'].get('src_idx')};"
            f"consumer_input_fnv={consumer['kv'].get('consumer_input_fnv')};"
            f"commit_seq={consumer['kv'].get('commit_seq')}")
    values["consumer_edge"] = edge["detail"] if edge is not None else None

    found: list[str] = []
    missing: list[str] = []
    for field in A03_FIELDS:
        if _present(values.get(field)):
            found.append(field)
        else:
            missing.append(field)

    if checksum and golden:
        terminal = ["APPLICATION_CHECKSUM",
                    "ORACLE_FAIL_SDC" if checksum != golden else "ORACLE_PASS"]
    elif checksum:
        terminal = ["APPLICATION_CHECKSUM", "GOLDEN_CHECKSUM_ABSENT"]
    elif watchdog or watchdog_conf:
        terminal = ["INTERNAL_WATCHDOG_NO_CHECKSUM"]
    else:
        terminal = ["NO_TERMINAL_WITNESS"]
    if watchdog or watchdog_conf:
        terminal.append("POST_ORACLE_INTERNAL_WATCHDOG")

    return values, _status(found, missing, trace_complete), ";".join(terminal)


# ---------------------------------------------------------------------------
# SP05
# ---------------------------------------------------------------------------

SP05_FIELDS = (
    "store_dyn_seq",
    "store_pc",
    "sq_entry",
    "store_address",
    "store_data_hash",
    "commit_event",
    "writeback_event",
    "memory_visibility",
    "reload",
    "consumer",
    "golden_memory_value",
    "application_oracle",
)

_CALLER_SUPPLIED = ("caller_supplied", "caller-supplied", "caller")
_COMMIT_TYPES = ("store_commit", "commit", "sq_commit")
_WRITEBACK_TYPES = ("store_writeback", "writeback", "memory_write", "store_mem_write")


def _sp05_records(run_dir: Path) -> tuple[dict[str, list[dict]], list[dict], bool, dict]:
    """Prefer trace_v31.jsonl; fall back to prop_trace for the same fields."""
    by_type, complete, meta = _scan_trace_v31(run_dir)
    if by_type:
        return by_type, [], complete, meta
    # Fallback: prop_trace has no event_type but the same family/kind rows.
    trace, complete, pmeta = _scan_prop_trace(run_dir, target_seq=None)
    rows: list[dict] = []
    if trace.get("resp"):
        rows.append(trace["resp"])
    rows.extend(trace.get("taint_reg", []))
    rows.extend(trace.get("consumer", {}).values())
    meta = dict(pmeta)
    return {}, rows, complete, meta


def _sp05(run_dir: Path) -> tuple[dict, list[str], str]:
    summary = _json(run_dir / "summary.json")
    first = summary.get("first_injection") or {}
    events = summary.get("injection_events") or []
    first_event = events[0] if events else {}
    detail = _kv(first.get("detail"))
    inj = dict(first_event)
    inj.update(detail)

    store_seq = str(first.get("store_seq") or inj.get("store_seq") or "") or None
    by_type, fallback_rows, trace_complete, trace_meta = _sp05_records(run_dir)

    def recs(*types: str) -> list[dict]:
        out: list[dict] = []
        for t in types:
            out.extend(by_type.get(t, []))
        return out

    def match_store(rec: dict) -> bool:
        return store_seq is None or str(rec.get("store_seq")) in (store_seq, "None")

    injections = [r for r in recs("injection") if match_store(r)]
    injection = injections[0] if injections else None
    if injection is not None:
        ikv = _trace_record_kv(injection, "store_seq", "store_pc", "store_addr",
                               "sq_entry_id", "sq_entry_generation", "store_data_fnv",
                               "mem_sent", "commit_status", "commit_tick_source")
        for key, val in ikv.items():
            if val not in (None, "") and key not in inj:
                inj[key] = val

    stage = None
    for rec in recs("sp05_stage"):
        if match_store(rec):
            stage = _trace_record_kv(rec)
            break
    skipped = None
    for rec in recs("sp05_write_skipped"):
        if match_store(rec):
            skipped = _trace_record_kv(rec)
            break
    complete_rec = None
    for rec in recs("sp05_complete"):
        if match_store(rec):
            complete_rec = _trace_record_kv(rec)
            break

    # --- commit event: an independent commit observation, never the caller
    # supplied injection tick.  Current pre-formal evidence has neither.
    commit_event = None
    for rec in recs(*_COMMIT_TYPES):
        if not match_store(rec):
            continue
        rkv = _trace_record_kv(rec, "store_seq", "commit_tick", "commit_tick_source",
                               "commit_status")
        src = (rkv.get("commit_tick_source") or "").lower()
        if src in _CALLER_SUPPLIED:
            continue
        commit_event = rec.get("detail") or json.dumps(rec, sort_keys=True)
        break
    if commit_event is None:
        for rkv in (inj, stage):
            if not rkv:
                continue
            if _boolish(rkv.get("commit_observed")) is True:
                src = (rkv.get("commit_tick_source") or "").lower()
                if src not in _CALLER_SUPPLIED:
                    commit_event = (
                        f"commit_observed=1;commit_tick={rkv.get('commit_tick')};"
                        f"commit_tick_source={rkv.get('commit_tick_source')}")
                    break

    # --- writeback event: the store data reaching memory/writeback queue.
    writeback_event = None
    for rec in recs(*_WRITEBACK_TYPES):
        if match_store(rec):
            writeback_event = rec.get("detail") or json.dumps(rec, sort_keys=True)
            break
    if writeback_event is None and stage is not None:
        if _boolish(stage.get("writeback_observed")) is True:
            writeback_event = (
                f"writeback_observed=1;writeback_tick={stage.get('writeback_tick')}")
        elif str(stage.get("write_skipped")) == "1":
            writeback_event = None  # skipped write is the fault, not a writeback
        elif _int_or_none(stage.get("stores_to_wb_after")) not in (None, 0) \
                and str(stage.get("mem_sent")) == "1":
            writeback_event = (
                f"stores_to_wb_after={stage.get('stores_to_wb_after')};mem_sent=1")

    # --- memory visibility: an observation of mem_sent / write_skipped.
    visibility = None
    for rkv in (stage, complete_rec, skipped, inj):
        if not rkv:
            continue
        if any(k in rkv for k in ("mem_sent", "write_skipped", "store_not_written_yet")):
            visibility = (
                f"mem_sent={rkv.get('mem_sent')};"
                f"write_skipped={rkv.get('write_skipped')};"
                f"store_not_written_yet={rkv.get('store_not_written_yet')}")
            break

    reload = None
    if stage is not None and (stage.get("reload_seq") or stage.get("reload_data_hash")):
        reload = (f"reload_seq={stage.get('reload_seq')};"
                  f"reload_data_hash={stage.get('reload_data_hash')}")
    if reload is None and fallback_rows:
        rr = _first(lambda r: r["kv"].get("request_id"), fallback_rows)
        if rr is not None:
            reload = f"request_id={rr['kv'].get('request_id')};data_fnv={rr['kv'].get('data_fnv')}"

    # --- consumer: a consumer record linked to the reload dataflow (ptag is
    # the trace's chain key; no value is invented when absent).
    consumer = None
    consumers = recs("consumer_commit")
    if consumers:
        c = consumers[0]
        ckv = _trace_record_kv(c, "consumer_inst_seq", "dyn_inst_seq", "commit_seq")
        consumer = (f"pc={ckv.get('pc')};consumer_inst_seq={ckv.get('consumer_inst_seq')};"
                    f"dyn_inst_seq={ckv.get('dyn_inst_seq')};commit_seq={ckv.get('commit_seq')}")
    elif fallback_rows:
        c = _first(lambda r: r["dyn_inst_seq"] not in (None, ""), fallback_rows)
        if c is not None:
            consumer = f"dyn_inst_seq={c['dyn_inst_seq']};pc={c['kv'].get('pc')}"

    oracle = _oracle(run_dir / "oracle.log")
    summary_oracle = summary.get("oracle")
    oracle_found = None
    if oracle.get("verdict") or oracle.get("expected") or summary_oracle is not None:
        oracle_found = (oracle.get("line")
                        or f"summary_oracle={summary_oracle}")
    golden = None
    if oracle.get("expected") or inj.get("store_data_hex"):
        golden = (f"oracle_expected={oracle.get('expected')};"
                  f"store_data_hex={inj.get('store_data_hex')}")

    values: dict[str, Any] = {
        "store_dyn_seq": store_seq if _present(store_seq) else None,
        "store_pc": inj.get("store_pc") if _present(inj.get("store_pc")) else None,
        "sq_entry": (f"sq_entry_id={inj.get('sq_entry_id')};"
                     f"sq_entry_generation={inj.get('sq_entry_generation')}")
        if _present(inj.get("sq_entry_id")) else None,
        "store_address": inj.get("store_addr") if _present(inj.get("store_addr")) else None,
        "store_data_hash": inj.get("store_data_fnv")
        if _present(inj.get("store_data_fnv")) else None,
        "commit_event": commit_event,
        "writeback_event": writeback_event,
        "memory_visibility": visibility,
        "reload": reload,
        "consumer": consumer,
        "golden_memory_value": golden,
        "application_oracle": oracle_found,
        "commit_status": inj.get("commit_status"),
        "commit_tick_source": inj.get("commit_tick_source"),
        "trace_present": trace_meta.get("trace") is not None,
        "trace_complete": trace_complete,
    }

    # Metadata may declare the trace truncated even when the file parses.
    tc = summary.get("trace_completeness") or {}
    declared = str(tc.get("trace_completeness") or "").upper()
    if declared in ("TRUNCATED", "INCOMPLETE", "MISSING"):
        trace_complete = False
        values["trace_complete"] = False
        values["trace_declared"] = declared
    elif declared == "COMPLETE":
        values["trace_declared"] = declared

    found: list[str] = []
    missing: list[str] = []
    for field in SP05_FIELDS:
        if _present(values.get(field)):
            found.append(field)
        else:
            missing.append(field)

    if oracle.get("verdict") == "PASS":
        terminal = ["APPLICATION_ORACLE", "ORACLE_PASS"]
    elif oracle.get("verdict") == "FAIL":
        terminal = ["APPLICATION_ORACLE", "ORACLE_FAIL_SDC"]
    elif oracle_found:
        terminal = ["APPLICATION_ORACLE", "ORACLE_VERDICT_UNKNOWN"]
    else:
        terminal = ["NO_APPLICATION_ORACLE"]
    if "commit_event" in missing:
        terminal.append("STORE_COMMIT_ABSENT")
    if "writeback_event" in missing:
        terminal.append("STORE_WRITEBACK_ABSENT")

    return values, _status(found, missing, trace_complete), ";".join(terminal)


# ---------------------------------------------------------------------------
# RP01
# ---------------------------------------------------------------------------

RP01_FIELDS = (
    "replay_eligibility",
    "replay_decision",
    "faulty_replay_state",
    "replay_skip",
    "dyn_seq",
    "lq_sq_entry",
    "internal_watchdog",
    "external_timeout",
    "final_progress_state",
)

_RP01_SKIP = ("RP01_SKIP_REPLAY", "skipped_call=1")


def _rp01(run_dir: Path) -> tuple[dict, list[str], str]:
    summary = _json(run_dir / "summary.json")
    rp = summary.get("rp01") or {}
    log = _lines(run_dir / "lsq_fwd_injections.log")
    stdout = _text(run_dir / "stdout.log")
    stderr = _text(run_dir / "stderr.log")
    combined = stdout + "\n" + stderr + "\n" + "\n".join(log)

    first_eligible_line = rp.get("first_eligible") or _first(
        lambda ln: "RP01_ELIGIBLE" in ln or
        ("read_partial_reschedule" in ln and "eligible_ordinal=" in ln), log)
    first_skip_line = rp.get("first_skip") or _first(
        lambda ln: any(tok in ln for tok in _RP01_SKIP), log)

    elig = _tokens_kv(first_eligible_line)
    skip = _tokens_kv(first_skip_line)

    watchdog_fired = _boolish(rp.get("watchdog"))
    if watchdog_fired is None:
        watchdog_fired = any(
            ("CHAOS_RP01_WATCHDOG=EXPIRED" in ln
             or "CHAOS_RP01_WATCHDOG_EXPIRED" in ln
             or "RP01_WATCHDOG_EXPIRED" in ln) for ln in combined.splitlines())
    marker = rp.get("watchdog_marker") or _first(
        lambda ln: "RP01_WATCHDOG" in ln, combined.splitlines())
    timed_out = _boolish(summary.get("timed_out"))
    if summary.get("timed_out") is None:
        timed_out = None

    terminal = summary.get("terminal") or rp.get("terminal")
    terminal_reason = summary.get("terminal_reason") or rp.get("terminal_reason")

    replay_decision = None
    if skip and any(k in skip for k in ("replay_gen_pre", "in_instsToReplay_pre",
                                        "skipped_call")):
        replay_decision = first_skip_line
    faulty_state = None
    if skip:
        needed = ("replay_gen_pre", "replay_gen_post",
                  "in_instsToReplay_pre", "in_instsToReplay_post")
        if all(k in skip for k in needed):
            faulty_state = (
                f"replay_gen_pre={skip.get('replay_gen_pre')};"
                f"replay_gen_post={skip.get('replay_gen_post')};"
                f"in_instsToReplay_pre={skip.get('in_instsToReplay_pre')};"
                f"in_instsToReplay_post={skip.get('in_instsToReplay_post')}")
    lq_sq = None
    if skip and skip.get("lq_idx") not in (None, ""):
        lq_sq = (f"lq_idx={skip.get('lq_idx')};lq_gen={skip.get('lq_gen')};"
                 f"store_seq={skip.get('store_seq')}")

    values: dict[str, Any] = {
        "replay_eligibility": first_eligible_line,
        "replay_decision": replay_decision,
        "faulty_replay_state": faulty_state,
        "replay_skip": first_skip_line,
        "dyn_seq": skip.get("load_seq"),
        "dyn_seq_pc": skip.get("load_pc"),
        "lq_sq_entry": lq_sq,
        "internal_watchdog": (
            f"watchdog={watchdog_fired};marker={marker}" if watchdog_fired is not None
            else None),
        "external_timeout": (f"timed_out={timed_out}" if timed_out is not None else None),
        "final_progress_state": terminal or terminal_reason,
        "final_progress_reason": terminal_reason,
        "internal_watchdog_fired": watchdog_fired,
        "external_timeout_fired": timed_out,
        "trace_present": (run_dir / "prop_trace.csv.gz").exists()
        or (run_dir / "prop_trace.csv").exists(),
    }

    # RP01's trace is cut by the internal watchdog; a watchdog cut is a
    # partial trace by construction, so it can never be a PASS chain.
    _records, trace_complete, trace_meta = _scan_prop_trace(run_dir)
    values["trace_complete"] = trace_complete and not watchdog_fired and timed_out is not True
    values["trace_rows_scanned"] = trace_meta.get("rows_scanned")
    if watchdog_fired and trace_complete:
        values["trace_cut_reason"] = "MODEL_INTERNAL_WATCHDOG"
    elif timed_out:
        values["trace_cut_reason"] = "EXTERNAL_TIMEOUT"

    found: list[str] = []
    missing: list[str] = []
    for field in RP01_FIELDS:
        if _present(values.get(field)):
            found.append(field)
        else:
            missing.append(field)

    if watchdog_fired:
        terminal_rule = "MODEL_INTERNAL_WATCHDOG"
    elif timed_out:
        terminal_rule = "EXTERNAL_TIMEOUT"
    else:
        terminal_rule = "NORMAL"

    return values, _status(found, missing, values["trace_complete"]), terminal_rule


# ---------------------------------------------------------------------------
# status + public entry point
# ---------------------------------------------------------------------------


def _status(found: list[str], missing: list[str], trace_complete: bool) -> str:
    if not trace_complete:
        return "TRACE_INCOMPLETE"
    if missing:
        return "QUALIFIED"
    return "PASS"


_GRADERS = {"A03": _a03, "SP05": _sp05, "RP01": _rp01}
_FIELDS = {"A03": A03_FIELDS, "SP05": SP05_FIELDS, "RP01": RP01_FIELDS}


def qualified_evidence(model: str, run_dir: Path) -> dict:
    """Grade one run dir's qualified-evidence chain.

    ``run_dir`` is the only evidence source.  The function never reads a
    historical summary table, never infers a value from another context, and
    never upgrades QUALIFIED/TRACE_INCOMPLETE to PASS.
    """
    run_dir = Path(run_dir)
    if model not in QUALIFIED_MODELS:
        return {
            "model": model,
            "required_fields": [],
            "found": [],
            "missing": [],
            "status": "PASS",
            "terminal_rule": "NO_EXTRA_RULES",
            "evidence": {
                "note": "only A03/SP05/RP01 carry qualified-evidence rules; "
                        "this model is graded by the collector",
            },
        }

    values, status, terminal_rule = _GRADERS[model](run_dir)
    found = [f for f in _FIELDS[model] if values.get(f) not in (None, "")]
    missing = [f for f in _FIELDS[model] if f not in found]
    return {
        "model": model,
        "required_fields": list(_FIELDS[model]),
        "found": found,
        "missing": missing,
        "status": status,
        "terminal_rule": terminal_rule,
        "evidence": values,
    }


if __name__ == "__main__":  # pragma: no cover - manual diagnostics only
    import argparse

    parser = argparse.ArgumentParser(
        description="Grade one LSU v3.3.3 run dir's qualified evidence")
    parser.add_argument("model")
    parser.add_argument("run_dir")
    args = parser.parse_args()
    print(json.dumps(qualified_evidence(args.model, Path(args.run_dir)),
                     indent=2, sort_keys=False))
