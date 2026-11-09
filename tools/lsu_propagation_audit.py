"""Streaming propagation audit tool (LSU v3.2.11 Task 8 / B2+B6+B7+B9).

Re-derives, from the raw per-pilot artifacts (``trace_v31.jsonl``,
``pilot_meta.json``, ``manifest.json``, ``oracle.log``), the seven-stage
propagation audit plus the two adjudication fields, without ever loading a
whole trace into memory: the JSONL is read line by line in three bounded
passes (find injection+summary, collect the fault's own chain, collect the
chain's edges), so 196 MB SQ03 traces audit in constant memory.

Contracts (scope spec B2/B6/B7/B9):

- ``audit_pilot(pilot_dir, model, binary_sha=None) -> dict`` with keys
  ``identity, stages, evidence, terminal, oracle, missing, classification``.
  Stage values are ``yes|no|n/a|missing``; a stage that is ``no``/``missing``
  always has at least one explicit reason code in ``missing`` (never a blank,
  never a bare ``PASS``).
- ``audit_model(model, pilot_dirs) -> dict`` carrying the 20 matrix-column
  fields at top level plus ``model``, ``pilots`` (per-pilot audit dicts) and
  ``binary_splits`` (one row per recorded binary SHA when the pilots span
  binaries -- never a merged verdict).
- ``write_matrix(rows, out)`` writes the 20-column audit matrix CSV and
  rejects any empty cell or bare ``PASS`` loudly.

Chain semantics (B3 -- time adjacency is not causality): an event is on the
fault's chain only when its ``ptag`` equals the injection's ``ptag`` or its
``dyn_inst_seq`` equals the injection's ``dyn_inst_seq`` (``str()``-normalized
because identity fields are ints in some trace vintages and JSON strings in
others; ``ptag`` 0/empty carries no identity).  Edges are on-chain only when
an endpoint event id is on the chain.  The terminal is re-adjudicated with
``terminal_rules.adjudicate`` and the fault-effect class with Task 2's
``fault_effect_coverage.classify`` -- historical verdicts are inputs to
re-derive, never values to copy.

Binary purity (B9): when ``binary_sha`` is given, it is compared with the
pilot's recorded binary SHA; a mismatch is reported as
``BINARY_SHA_MISMATCH`` and ``audit_model`` splits per binary instead of
merging.

Model-specific early-anomaly stage (B6: expected paths come from the frozen
per-model definitions): A01/A03 ``address_formed``; FW02/FW05
``forwarding_decision``; DA04/SQ01/SQ03/SP05 ``store_writeback``/
``store_mem_write``; LP01/LQ04/MD04 the load path ``memory_response``.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = (ROOT / "docs" / "gem5-fi" / "lsu" / "implementation_v3_2"
            / "platform")
sys.path.insert(0, str(PLATFORM))

from fault_effect_coverage import classify as classify_fault_effect  # noqa: E402
import terminal_rules  # noqa: E402
from trace_completeness import expected_stages  # noqa: E402

TRACE_NAME = "trace_v31.jsonl"
TRACE_SIDECAR = "trace_v31.jsonl.sha256"
META_NAME = "pilot_meta.json"
MANIFEST_NAME = "manifest.json"
ORACLE_NAME = "oracle.log"

INJECTION_TYPES = ("injection", "injection_nochange")
COMMIT_TYPES = ("commit", "errant_commit")

# B6: the model's first post-injection observable stage (frozen sheet-4
# definitions).  Models absent from this table have no early-anomaly stage
# defined and report "n/a".
EARLY_ANOMALY_KINDS: dict[str, tuple[str, ...]] = {
    "A01": ("address_formed",),
    "A03": ("address_formed",),
    "FW02": ("forwarding_decision",),
    "FW05": ("forwarding_decision",),
    "DA04": ("store_writeback", "store_mem_write"),
    "SQ01": ("store_writeback", "store_mem_write"),
    "SQ03": ("store_writeback", "store_mem_write"),
    "SP05": ("store_writeback", "store_mem_write"),
    "LP01": ("memory_response",),
    "LQ04": ("memory_response",),
    "MD04": ("memory_response",),
}

# SubUnit labels mirror MODEL_STATUS_MATRIX.csv; the fault definition falls
# back to these short labels when the pilot manifest carries no frozen
# fault.location.
MODEL_INFO: dict[str, tuple[str, str]] = {
    "A01": ("AGU", "load address value fault (pushRequest addr)"),
    "A03": ("AGU", "persistent address fault (pushRequest addr, F5)"),
    "FW02": ("FWD", "store->load forwarding decision corruption"),
    "SQ01": ("SQ", "store data bit flip"),
    "DA04": ("SQ", "store byte-enable corruption (0xF->0xE)"),
    "LP01": ("L1D", "load response data fault (bytewise)"),
    "MD04": ("LSU", "memory-order violation report suppression"),
    "FW05": ("FWD", "wrong-source store->load forwarding"),
    "SQ03": ("SQ", "premature store writeback permission"),
    "SP05": ("SQ", "premature store completion (completeStores)"),
    "LQ04": ("LQ", "LQ entry lifetime corruption (valid+request)"),
}

MATRIX_COLUMNS = [
    "ModelID", "SubUnit", "FaultDefinition", "PilotCount",
    "InjectionVerified", "ActivationVerified", "EarlyAnomalyVerified",
    "IntermediatePropagationVerified", "RegisterWritebackVerified",
    "ConsumerVerified", "CommitVerified", "TerminalVerified",
    "OracleVerified", "StructuralChainCompleteness",
    "FaultEffectPropagationCoverage", "FaultCausality",
    "FinalClassification", "MissingEvidence", "SupplementaryPilotRequired",
    "EvidencePaths",
]

STAGE_FIELDS = (
    "injection_verified", "activation_verified", "early_anomaly_verified",
    "intermediate_propagation_verified", "register_writeback_verified",
    "consumer_verified", "commit_verified", "terminal_verified",
    "oracle_verified",
)

_STAGE_TO_COLUMN = {
    "injection_verified": "InjectionVerified",
    "activation_verified": "ActivationVerified",
    "early_anomaly_verified": "EarlyAnomalyVerified",
    "intermediate_propagation_verified": "IntermediatePropagationVerified",
    "register_writeback_verified": "RegisterWritebackVerified",
    "consumer_verified": "ConsumerVerified",
    "commit_verified": "CommitVerified",
    "terminal_verified": "TerminalVerified",
    "oracle_verified": "OracleVerified",
}

# Reason codes whose evidence a supplementary pilot could in principle
# supply (B8); they drive the SupplementaryPilotRequired count.
STAGE_GAP_CODES = frozenset((
    "NO_INJECTION_EVENT", "INJECTION_NOT_TRIGGERED",
    "NO_EARLY_ANOMALY_EVENT", "NO_INTERMEDIATE_PROPAGATION_EVENT",
    "NO_REGISTER_WRITEBACK_EVENT", "NO_CONSUMER_EDGE", "NO_COMMIT_EVENT",
))

# Fields kept when slimming streamed records; everything classify/adjudicate
# needs, nothing else, so chain memory stays small on 196 MB traces.
_EVENT_KEYS = ("record_type", "event_id", "event_type", "ptag",
               "dyn_inst_seq", "source_event_id", "detail",
               "activation_status", "injection_status", "commit_status",
               "commit_seq", "timestamp", "new_value")
_EDGE_KEYS = ("record_type", "propagation_edge_id", "source_event_id",
              "destination_event_id", "edge_kind", "value_hash",
              "source_value_hash", "destination_value_hash")

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


# ---------------------------------------------------------------------------
# streaming JSONL passes
# ---------------------------------------------------------------------------

def _lines(path: Path):
    """Yield parsed records one line at a time; malformed lines yield None."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                yield None
                continue
            yield rec if isinstance(rec, dict) else None


def _slim(record: dict, keys) -> dict:
    return {k: record.get(k) for k in keys}


def _scan_head(path: Path):
    """Pass 1: the injection (last one, mirroring run_pilot), the last
    summary, record counts and the malformed-line count."""
    injection = None
    summary = None
    sample_run_id = None
    counts = {"records": 0, "events": 0, "edges": 0, "summaries": 0,
              "malformed": 0}
    for rec in _lines(path):
        counts["records"] += 1
        if rec is None:
            counts["malformed"] += 1
            continue
        if sample_run_id is None and rec.get("sample_run_id"):
            sample_run_id = str(rec["sample_run_id"])
        rt = rec.get("record_type")
        if rt == "event":
            counts["events"] += 1
            if rec.get("event_type") in INJECTION_TYPES:
                injection = _slim(rec, _EVENT_KEYS)
        elif rt == "propagation_edge":
            counts["edges"] += 1
        elif rt == "summary":
            counts["summaries"] += 1
            summary = rec
    return injection, summary, counts, sample_run_id


def _chain_identity(injection: dict):
    """str()-normalized (ptag, dyn_inst_seq); ptag 0/empty carries no chain
    identity (platform convention for commit/squash/lifecycle nodes)."""
    ptag = injection.get("ptag")
    seq = injection.get("dyn_inst_seq")
    ptag_s = None if ptag in (None, "") or str(ptag) == "0" else str(ptag)
    seq_s = None if seq in (None, "") else str(seq)
    return ptag_s, seq_s


def _collect_chain(path: Path, injection: dict) -> list[dict]:
    """Pass 2: the fault's own chain (same ptag or same dyn_inst_seq)."""
    ptag_s, seq_s = _chain_identity(injection)
    chain: list[dict] = []
    if ptag_s is None and seq_s is None:
        return chain
    for rec in _lines(path):
        if rec is None or rec.get("record_type") != "event":
            continue
        if ptag_s is not None and str(rec.get("ptag")) == ptag_s:
            chain.append(_slim(rec, _EVENT_KEYS))
        elif seq_s is not None and str(rec.get("dyn_inst_seq")) == seq_s:
            chain.append(_slim(rec, _EVENT_KEYS))
    return chain


def _collect_chain_edges(path: Path, chain_ids: set[str]) -> list[dict]:
    """Pass 3: edges with an endpoint on the chain (B3 explicit links)."""
    edges: list[dict] = []
    for rec in _lines(path):
        if rec is None or rec.get("record_type") != "propagation_edge":
            continue
        if (str(rec.get("source_event_id")) in chain_ids
                or str(rec.get("destination_event_id")) in chain_ids):
            edges.append(_slim(rec, _EDGE_KEYS))
    return edges


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _detail_kv(detail) -> dict:
    return dict(item.split("=", 1) for item in (str(detail or "")).split(";")
                if "=" in item)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_sha(manifest: dict, subject: str) -> str | None:
    """Locate a recorded 64-hex SHA under keys naming ``subject`` (binary or
    workload).  Manifest vintages spell keys differently (``binary_sha256``
    vs ``BinarySHA256``) and the binary SHA lives under the ``gem5``
    section, so known spots are tried first and a bounded recursive key
    scan follows."""
    if not isinstance(manifest, dict):
        return None
    section_name = "gem5" if subject == "binary" else subject
    section = manifest.get(section_name)
    if isinstance(section, dict):
        for key in (f"{subject}_sha256", f"{subject}_SHA256", "sha256",
                    "SHA256"):
            value = section.get(key)
            if isinstance(value, str) and _SHA256_RE.fullmatch(value):
                return value
    for key in (f"{subject}_sha256", f"{subject}_SHA256"):
        value = manifest.get(key)
        if isinstance(value, str) and _SHA256_RE.fullmatch(value):
            return value

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if (isinstance(value, str)
                        and _SHA256_RE.fullmatch(value)
                        and subject in str(key).lower()
                        and "sha" in str(key).lower()):
                    return value
                found = walk(value)
                if found:
                    return found
        elif isinstance(node, list):
            for value in node:
                found = walk(value)
                if found:
                    return found
        return None

    return walk(manifest)


def _normalize_hash(value) -> str | None:
    """Bare lowercase hex: ``checksum=0x99c1...`` -> ``99c1...``."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if "0x" in text:
        text = text.split("0x", 1)[1]
    return text or None


def _read_oracle(path: Path, meta: dict | None) -> dict:
    """Parse the two-line oracle.log; cross-check with pilot_meta.

    Status: ``ok`` (parsed and consistent with meta), ``inconsistent``
    (contradicts meta's oracle_pass), ``malformed``, ``absent``.  An
    ORACLE_FAIL outcome is still a *verified* oracle stage -- the comparison
    executed and detected the divergence; the outcome is carried in
    ``pass`` and feeds the terminal/classification, not this status.

    When the log file is absent or malformed (older pilot vintages keep the
    oracle outcome only in pilot_meta.json), the meta-recorded values fill
    the evidence fields and ``source`` says so; the explicit missing code
    (``ORACLE_FILE_MISSING`` / ``ORACLE_MALFORMED``) is still emitted --
    a meta-only oracle is a recorded claim, not the primary artifact.
    """
    meta_expected = None
    meta_pass = None
    if isinstance(meta, dict):
        meta_pass = meta.get("oracle_pass")
        raw = meta.get("oracle_expected")
        if raw is not None:
            meta_expected = _normalize_hash(raw)

    def _fallback(status: str) -> dict:
        return {"status": status, "source": "pilot_meta",
                "expected": meta_expected, "actual": None,
                "pass": meta_pass if isinstance(meta_pass, bool) else None,
                "meta_pass": meta_pass}

    if not path.is_file():
        return _fallback("absent")
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"expected=(\S+)\s+got=(\S+)", text)
    verdict_pass = "ORACLE_PASS" in text
    verdict_fail = "ORACLE_FAIL" in text
    if not match or verdict_pass == verdict_fail:
        return _fallback("malformed")
    expected, actual = match.group(1), match.group(2)
    result = {"status": "ok", "source": "oracle.log", "expected": expected,
              "actual": actual, "pass": verdict_pass, "meta_pass": meta_pass}
    if isinstance(meta_pass, bool) and meta_pass != verdict_pass:
        result["status"] = "inconsistent"
    return result


def _agg(values: list[str]) -> str:
    """Aggregate per-pilot stage/class values: ``yes(5/5)`` when uniform,
    ``mixed(yes=3;missing=2)`` otherwise; never empty."""
    if not values:
        return "n/a(0)"
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    if len(counts) == 1:
        only = next(iter(counts))
        return f"{only}({len(values)}/{len(values)})"
    parts = [f"{key}={counts[key]}" for key in ("yes", "no", "missing", "n/a")
             if key in counts]
    for key in sorted(counts):
        if key not in ("yes", "no", "missing", "n/a"):
            parts.append(f"{key}={counts[key]}")
    return "mixed(" + ";".join(parts) + ")"


# ---------------------------------------------------------------------------
# audit_pilot
# ---------------------------------------------------------------------------

def audit_pilot(pilot_dir: Path, model: str,
                binary_sha: str | None = None) -> dict:
    """Audit one pilot dir; returns identity/stages/evidence/terminal/oracle/
    missing/classification (all JSON-safe values)."""
    pilot_dir = Path(pilot_dir)
    missing: list[str] = []

    def add(code: str) -> None:
        if code not in missing:
            missing.append(code)

    stages = {field: "missing" for field in STAGE_FIELDS}
    if not pilot_dir.is_dir():
        add("PILOT_DIR_ABSENT")
        return {
            "identity": {"model": model, "pilot_dir": str(pilot_dir),
                         "sample_run_id": None, "binary_sha256": None},
            "stages": stages,
            "evidence": {"paths": {"pilot_dir": str(pilot_dir)},
                         "malformed_records": 0,
                         "structural_chain_completeness": "n/a",
                         "fault_effect": {"reason": "PILOT_DIR_ABSENT"}},
            "terminal": {"observed": None, "adjudicated": "UNRESOLVED",
                         "reason": "PILOT_DIR_ABSENT"},
            "oracle": {"status": "absent", "expected": None, "actual": None,
                       "pass": None},
            "missing": missing,
            "classification": "UNRESOLVED",
        }

    trace_path = pilot_dir / TRACE_NAME
    sidecar_path = pilot_dir / TRACE_SIDECAR
    meta_path = pilot_dir / META_NAME
    manifest_path = pilot_dir / MANIFEST_NAME
    oracle_path = pilot_dir / ORACLE_NAME

    # -- sidecar artifacts ------------------------------------------------
    meta = None
    if meta_path.is_file():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            add("META_MALFORMED")
    else:
        add("META_MISSING")

    manifest = None
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            add("MANIFEST_MALFORMED")
    else:
        add("MANIFEST_MISSING")

    oracle = _read_oracle(oracle_path, meta)
    if oracle["status"] == "absent":
        add("ORACLE_FILE_MISSING")
    elif oracle["status"] == "malformed":
        add("ORACLE_MALFORMED")
    elif oracle["status"] == "inconsistent":
        add("ORACLE_META_INCONSISTENT")

    # -- streaming trace passes -------------------------------------------
    injection = None
    summary = None
    counts = {"records": 0, "events": 0, "edges": 0, "summaries": 0,
              "malformed": 0}
    trace_sample_run_id = None
    trace_sha = None
    if trace_path.is_file():
        injection, summary, counts, trace_sample_run_id = _scan_head(
            trace_path)
        if counts["malformed"]:
            add("MALFORMED_RECORDS")
        if sidecar_path.is_file():
            recorded = sidecar_path.read_text(
                encoding="utf-8", errors="replace").strip().split()
            trace_sha = _sha256_file(trace_path)
            if recorded and recorded[0].lower() != trace_sha:
                add("HASH_MISMATCH")
    else:
        add("TRACE_FILE_MISSING")

    validator_errors = []
    if isinstance(meta, dict):
        validator_errors = ((meta.get("trace") or {}).get("validator_errors")
                            or [])
    if validator_errors:
        add("VALIDATOR_ERRORS")

    # -- provenance (B9) ----------------------------------------------------
    recorded_binary = _find_sha(manifest, "binary") if manifest else None
    recorded_workload = _find_sha(manifest, "workload") if manifest else None
    if binary_sha and manifest:
        if recorded_binary is None:
            add("BINARY_SHA_UNRECORDED")
        elif str(binary_sha).lower() != recorded_binary.lower():
            add("BINARY_SHA_MISMATCH")

    # -- completeness inputs ------------------------------------------------
    declared = (summary or {}).get("trace_completeness")
    if declared is None and isinstance(meta, dict):
        declared = (((meta.get("trace") or {}).get("completeness") or {})
                    .get("trace_completeness")
                    or (meta.get("classification") or {})
                    .get("trace_completeness"))
    trace_complete = (
        declared == "COMPLETE"
        and not validator_errors
        and counts["malformed"] == 0
        and counts["summaries"] == 1
        and trace_path.is_file()
    )
    if trace_path.is_file() and declared == "INCOMPLETE":
        add("TRACE_INCOMPLETE")
    if trace_path.is_file() and counts["summaries"] != 1:
        add("SUMMARY_RECORD_COUNT")

    # -- chain (B3) ---------------------------------------------------------
    chain: list[dict] = []
    edges: list[dict] = []
    on_chain_edges: list[dict] = []
    chain_ids: set[str] = set()
    if injection is not None:
        chain = _collect_chain(trace_path, injection)
        chain_ids = {str(e.get("event_id")) for e in chain
                     if e.get("event_id") is not None}
        edges = _collect_chain_edges(trace_path, chain_ids)
        on_chain_edges = [
            e for e in edges
            if str(e.get("source_event_id")) in chain_ids
            and str(e.get("destination_event_id")) in chain_ids]
    else:
        add("NO_INJECTION_EVENT")

    # -- terminal re-adjudication -------------------------------------------
    observed = None
    if summary:
        observed = summary.get("observed_terminal") or summary.get(
            "terminal_state")
    if observed is None and isinstance(meta, dict):
        classification = meta.get("classification") or {}
        observed = classification.get("observed_terminal") or classification \
            .get("terminal_state")
    oracle_pass = oracle["pass"]
    if oracle_pass is None and isinstance(meta, dict):
        oracle_pass = meta.get("oracle_pass")
    own_chain = terminal_rules.chain_events(chain, injection)
    terminal_state, terminal_reason = terminal_rules.adjudicate(
        own_chain, model=model, observed_terminal=observed,
        oracle_pass=oracle_pass, trace_complete=trace_complete)

    # -- stages ---------------------------------------------------------------
    stages["injection_verified"] = "yes" if injection is not None else "missing"
    if injection is None:
        stages["activation_verified"] = "n/a"
    else:
        activation = injection.get("activation_status") or (
            summary or {}).get("fault_activation_status")
        stages["activation_verified"] = (
            "yes" if str(activation).upper() == "TRIGGERED" else "no")
        if stages["activation_verified"] == "no":
            add("INJECTION_NOT_TRIGGERED")

    early_kinds = EARLY_ANOMALY_KINDS.get(model)
    early_event = None
    if early_kinds is None:
        stages["early_anomaly_verified"] = "n/a"
    elif injection is None:
        stages["early_anomaly_verified"] = "missing"
    else:
        early_event = next(
            (e for e in chain if e.get("event_type") in early_kinds), None)
        if early_event is not None:
            stages["early_anomaly_verified"] = "yes"
        else:
            stages["early_anomaly_verified"] = "missing"
            add("NO_EARLY_ANOMALY_EVENT")

    linked_source = any(
        e.get("source_event_id") is not None
        and str(e.get("source_event_id")) in chain_ids for e in chain)
    if injection is None:
        stages["intermediate_propagation_verified"] = "missing"
    elif on_chain_edges or linked_source:
        stages["intermediate_propagation_verified"] = "yes"
    else:
        stages["intermediate_propagation_verified"] = "missing"
        add("NO_INTERMEDIATE_PROPAGATION_EVENT")

    writeback = next(
        (e for e in chain if e.get("event_type") == "register_writeback"),
        None)
    if injection is None:
        stages["register_writeback_verified"] = "missing"
    elif writeback is not None:
        stages["register_writeback_verified"] = "yes"
    else:
        stages["register_writeback_verified"] = "missing"
        add("NO_REGISTER_WRITEBACK_EVENT")

    consumer = next(
        (e for e in chain if e.get("event_type") == "consumer_commit"), None)
    if injection is None:
        stages["consumer_verified"] = "missing"
    elif consumer is not None:
        stages["consumer_verified"] = "yes"
    else:
        stages["consumer_verified"] = "missing"
        add("NO_CONSUMER_EDGE")

    commit = next(
        (e for e in chain if e.get("event_type") in COMMIT_TYPES), None)
    if injection is None:
        stages["commit_verified"] = "missing"
    elif commit is not None:
        stages["commit_verified"] = "yes"
    else:
        stages["commit_verified"] = "missing"
        add("NO_COMMIT_EVENT")

    if terminal_state is None:
        stages["terminal_verified"] = "missing"
        add("TERMINAL_MISSING")
    elif str(terminal_state).upper() == "UNRESOLVED":
        stages["terminal_verified"] = "no"
        add("TERMINAL_UNRESOLVED")
    else:
        stages["terminal_verified"] = "yes"

    stages["oracle_verified"] = {
        "ok": "yes", "inconsistent": "no", "malformed": "missing",
        "absent": "missing"}[oracle["status"]]

    # -- structural completeness (re-derived, chain-scoped) ------------------
    if injection is None or terminal_state is None:
        structural = "n/a"
    else:
        kinds_present = {str(e.get("event_type")) for e in chain}
        profiles = expected_stages(model, terminal_state)
        structural = ("COMPLETE" if any(set(p) <= kinds_present
                                        for p in profiles) else "INCOMPLETE")

    # -- fault-effect classification (Task 2) --------------------------------
    classify_input = list(chain) + ([summary] if summary else [])
    effect = classify_fault_effect(model, classify_input, injection,
                                   terminal_state)
    classification = effect["fault_effect_propagation_coverage"]

    # -- evidence bundle -------------------------------------------------------
    inj_detail = _detail_kv(injection.get("detail")) if injection else {}
    pc = inj_detail.get("pc")
    if pc is None and injection is not None:
        # the fault instruction's own PC: the injection record carries it on
        # some models, otherwise its commit/lifecycle nodes do (same seq)
        inj_seq_s = str(injection.get("dyn_inst_seq"))
        own_events = [e for e in chain
                      if str(e.get("dyn_inst_seq")) == inj_seq_s]
        for event in own_events:
            value = _detail_kv(event.get("detail")).get("pc")
            if value:
                pc = value
                break
    if pc is None:
        for event in chain:
            value = _detail_kv(event.get("detail")).get("pc")
            if value:
                pc = value
                break
    if pc is None and isinstance(meta, dict):
        events = ((meta.get("injection") or {}).get("events") or [])
        if events and events[0].get("pc") is not None:
            pc = str(events[0]["pc"])
    tick = injection.get("timestamp") if injection else None
    if tick is None and injection:
        tick = inj_detail.get("tick") or inj_detail.get("request_tick")

    wb_detail = _detail_kv(writeback.get("detail")) if writeback else {}
    cons_detail = _detail_kv(consumer.get("detail")) if consumer else {}

    excel = {}
    if isinstance(meta, dict):
        excel = meta.get("excel_identity") or {}
    fault_section = {}
    if isinstance(manifest, dict):
        fault_section = manifest.get("fault") or {}
    ordinal = (excel.get("event_ordinal")
               or fault_section.get("event_ordinal"))
    seed = None
    for source in (manifest, meta):
        if isinstance(source, dict) and source.get("seed") is not None:
            seed = str(source["seed"])
            break
    sample_run_id = (excel.get("sample_run_id")
                     or (meta or {}).get("pilot_id")
                     or (manifest or {}).get("sample_run_id")
                     or trace_sample_run_id)
    fault_definition = None
    if fault_section.get("location"):
        fault_definition = str(fault_section["location"])
        if fault_section.get("target_field"):
            fault_definition += f" / {fault_section['target_field']}"
    if fault_definition is None and model in MODEL_INFO:
        fault_definition = MODEL_INFO[model][1]

    evidence = {
        "injection_seq": (str(injection["dyn_inst_seq"])
                          if injection and injection.get("dyn_inst_seq")
                          is not None else None),
        "pc": str(pc) if pc is not None else None,
        "tick": str(tick) if tick is not None else None,
        "event_ordinal": str(ordinal) if ordinal is not None else None,
        "earliest_anomaly": (
            {"event_id": str(early_event["event_id"]),
             "event_type": str(early_event["event_type"])}
            if early_event is not None else None),
        "writeback": (
            {"event_id": str(writeback["event_id"]),
             "phys_reg": wb_detail.get("phys_reg"),
             "arch_reg": wb_detail.get("arch_reg"),
             "writeback_value_fnv": wb_detail.get("writeback_value_fnv"),
             "payload_fnv": wb_detail.get("payload_fnv"),
             "value_matches_payload": wb_detail.get("value_matches_payload")}
            if writeback is not None else None),
        "consumer": (
            {"event_id": str(consumer["event_id"]),
             "pc": cons_detail.get("pc"),
             "source_event_id": (str(consumer["source_event_id"])
                                 if consumer.get("source_event_id") is not None
                                 else None),
             "source_linked": (
                 str(consumer.get("source_event_id")) in chain_ids),
             "consumer_input_fnv": cons_detail.get("consumer_input_fnv"),
             "consumer_input_matches_source":
                 cons_detail.get("consumer_input_matches_source")}
            if consumer is not None else None),
        "commit": (
            {"event_id": str(commit["event_id"]),
             "commit_seq": (str(commit["commit_seq"])
                            if commit.get("commit_seq") is not None
                            else _detail_kv(commit.get("detail"))
                            .get("commit_seq"))}
            if commit is not None else None),
        "terminal": {"state": terminal_state, "reason": terminal_reason,
                     "observed": observed},
        "oracle": {"expected": oracle["expected"],
                   "actual": oracle["actual"], "pass": oracle["pass"]},
        "binary_sha": recorded_binary,
        "workload_sha": recorded_workload,
        "trace_sha256": trace_sha,
        "paths": {
            "pilot_dir": str(pilot_dir),
            "trace": str(trace_path),
            "meta": str(meta_path),
            "manifest": str(manifest_path),
            "oracle_log": str(oracle_path),
        },
        "records": counts,
        "malformed_records": counts["malformed"],
        "chain": {
            "events": len(chain),
            "edges_touching": len(edges),
            "edges_on_chain": len(on_chain_edges),
            "consumer_commits": sum(1 for e in chain
                                    if e.get("event_type")
                                    == "consumer_commit"),
            "kinds": sorted({str(e.get("event_type")) for e in chain}),
        },
        "structural_chain_completeness": structural,
        "validator_errors": len(validator_errors),
        "fault_effect": {
            "coverage": classification,
            "reason": effect["fault_effect_reason"],
            "detail": effect["fault_effect_evidence"],
        },
    }

    def _s(value):
        return str(value) if value is not None else None

    def _first(*values):
        for value in values:
            if value is not None:
                return value
        return None

    manifest_get = manifest.get if isinstance(manifest, dict) else (lambda
                                                                    k: None)
    identity = {
        "model": model,
        "pilot_dir": str(pilot_dir),
        "sample_run_id": _s(sample_run_id),
        "run_id": _s(_first(manifest_get("run_id"), excel.get("run_id"))),
        "sub_task_id": _s(_first(manifest_get("sub_task_id"),
                                 excel.get("sub_task_id"))),
        "fault_id": _s(manifest_get("fault_id")),
        "seed": seed,
        "event_ordinal": (str(ordinal) if ordinal is not None else None),
        "binary_sha256": recorded_binary,
        "workload_sha256": recorded_workload,
        "injection_count": str(
            (meta or {}).get("injection_count")
            if isinstance(meta, dict)
            and (meta or {}).get("injection_count") is not None
            else (1 if injection is not None else 0)),
        "fault_definition": fault_definition,
        "sub_unit": MODEL_INFO.get(model, ("n/a",))[0],
    }

    causality = None
    if summary:
        causality = summary.get("fault_causality")
    if causality is None and isinstance(meta, dict):
        causality = (meta.get("classification") or {}).get("fault_causality")

    return {
        "identity": identity,
        "stages": stages,
        "evidence": evidence,
        "terminal": {
            "observed": observed,
            "adjudicated": terminal_state,
            "reason": terminal_reason,
            "causality_recorded": causality,
            "trace_completeness": declared,
            "run_status": (summary or {}).get("run_status"),
        },
        "oracle": {
            "status": oracle["status"],
            "source": oracle.get("source"),
            "expected": oracle["expected"],
            "actual": oracle["actual"],
            "pass": oracle["pass"],
            "meta_pass": oracle["meta_pass"],
        },
        "missing": missing,
        "classification": classification,
    }


# ---------------------------------------------------------------------------
# audit_model
# ---------------------------------------------------------------------------

def _model_row(model: str, pilots: list[dict]) -> dict:
    """Aggregate per-pilot audits into the 20 matrix-column fields."""
    count = len(pilots)
    stage_values = {field: [p["stages"][field] for p in pilots]
                    for field in STAGE_FIELDS}
    structural = [p["evidence"]["structural_chain_completeness"]
                  for p in pilots]
    coverage = [p["classification"] for p in pilots]
    causality = [p["terminal"].get("causality_recorded") or "n/a"
                 for p in pilots]
    union_missing: list[str] = []
    for pilot in pilots:
        for code in pilot["missing"]:
            if code not in union_missing:
                union_missing.append(code)
    sub_unit = (pilots[0]["identity"].get("sub_unit")
                if pilots else MODEL_INFO.get(model, ("n/a",))[0])
    fault_definition = (pilots[0]["identity"].get("fault_definition")
                        if pilots else MODEL_INFO.get(model, ("",))[1]
                        if model in MODEL_INFO else "n/a")

    row = {
        "ModelID": model,
        "SubUnit": sub_unit or "n/a",
        "FaultDefinition": fault_definition or "n/a",
        "PilotCount": str(count),
        "StructuralChainCompleteness": _agg(structural),
        "FaultEffectPropagationCoverage": _agg(coverage),
        "FaultCausality": _agg(causality),
        "MissingEvidence": (";".join(union_missing) if union_missing
                            else "none"),
        "SupplementaryPilotRequired": str(
            len([c for c in union_missing if c in STAGE_GAP_CODES])),
        "EvidencePaths": ";".join(p["identity"]["pilot_dir"]
                                  for p in pilots) or "none",
    }
    for field, column in _STAGE_TO_COLUMN.items():
        row[column] = _agg(stage_values[field])

    binaries = sorted({p["identity"].get("binary_sha256")
                       for p in pilots
                       if p["identity"].get("binary_sha256")})
    if len(binaries) > 1:
        row["FinalClassification"] = "MIXED_BINARY_SPLIT"
    elif len(set(coverage)) == 1 and coverage:
        row["FinalClassification"] = coverage[0]
    else:
        row["FinalClassification"] = _agg(coverage)
    return row


def audit_model(model: str, pilot_dirs: list[Path],
                binary_sha: str | None = None) -> dict:
    """Audit every pilot dir and aggregate into the matrix row fields.

    Returns the 20 matrix columns at top level plus ``model``, ``pilots``
    (the per-pilot audit dicts) and ``binary_splits``: when the pilots carry
    more than one recorded binary SHA, one full row per binary labelled
    ``<MODEL>@<sha8>`` -- never a merged verdict (B9)."""
    pilots = [audit_pilot(Path(p), model, binary_sha=binary_sha)
              for p in pilot_dirs]
    row = _model_row(model, pilots)
    result = dict(row)
    result["model"] = model
    result["pilots"] = pilots
    splits: list[dict] = []
    by_binary: dict[str, list[dict]] = {}
    for pilot in pilots:
        sha = pilot["identity"].get("binary_sha256") or "unknown"
        by_binary.setdefault(sha, []).append(pilot)
    if len(by_binary) > 1:
        for sha in sorted(by_binary):
            split = _model_row(model, by_binary[sha])
            split["ModelID"] = f"{model}@{sha[:8]}"
            split["EvidencePaths"] = ";".join(
                p["identity"]["pilot_dir"] for p in by_binary[sha])
            splits.append(split)
    result["binary_splits"] = splits
    return result


# ---------------------------------------------------------------------------
# write_matrix (B7)
# ---------------------------------------------------------------------------

def write_matrix(rows: list[dict], out: Path) -> None:
    """Write the 20-column audit matrix; an empty cell or a bare ``PASS`` is
    a loud failure, never a silent blank."""
    out = Path(out)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(MATRIX_COLUMNS)
        for row in rows:
            cells = []
            for column in MATRIX_COLUMNS:
                value = row.get(column)
                text = "" if value is None else str(value)
                if not text.strip():
                    raise ValueError(
                        f"empty matrix cell for column {column!r} in row "
                        f"{row.get('ModelID')!r}")
                if text.strip().upper() == "PASS":
                    raise ValueError(
                        f"bare PASS in matrix column {column!r} in row "
                        f"{row.get('ModelID')!r}")
                cells.append(text)
            writer.writerow(cells)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Streaming seven-stage LSU propagation audit "
                    "(v3.2.11 Task 8).")
    parser.add_argument("--model", required=True,
                        help="fault model id, e.g. LQ04")
    parser.add_argument("--pilot-dir", action="append", type=Path,
                        required=True,
                        help="pilot output dir (repeatable)")
    parser.add_argument("--binary-sha", default=None,
                        help="expected gem5 binary SHA256 (B9 purity check)")
    parser.add_argument("--json", type=Path, default=None,
                        help="write the full audit result as JSON")
    parser.add_argument("--matrix", type=Path, default=None,
                        help="write the audit matrix CSV (model row plus any "
                             "binary-split rows)")
    args = parser.parse_args(argv)

    result = audit_model(args.model, args.pilot_dir,
                         binary_sha=args.binary_sha)
    rows = [{col: result[col] for col in MATRIX_COLUMNS}]
    rows.extend({col: split[col] for col in MATRIX_COLUMNS}
                for split in result["binary_splits"])

    if args.matrix:
        write_matrix(rows, args.matrix)
    if args.json:
        payload = {"model": result["model"], "row": rows[0],
                   "binary_splits": rows[1:], "pilots": result["pilots"]}
        args.json.write_text(json.dumps(payload, indent=2) + "\n",
                             encoding="utf-8")

    print(f"model={result['model']} pilots={result['PilotCount']} "
          f"binary_splits={len(result['binary_splits'])}")
    for pilot in result["pilots"]:
        codes = ",".join(pilot["missing"]) or "none"
        print(f"  {pilot['identity']['pilot_dir']}: "
              f"classification={pilot['classification']} missing=[{codes}]")
    print(f"FinalClassification={result['FinalClassification']}")
    print(f"FaultEffectPropagationCoverage="
          f"{result['FaultEffectPropagationCoverage']}")
    print(f"StructuralChainCompleteness="
          f"{result['StructuralChainCompleteness']}")
    print(f"MissingEvidence={result['MissingEvidence']}")
    print(f"SupplementaryPilotRequired="
          f"{result['SupplementaryPilotRequired']}")
    for split in result["binary_splits"]:
        print(f"  split {split['ModelID']}: "
              f"{split['FinalClassification']} "
              f"({split['PilotCount']} pilots)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
