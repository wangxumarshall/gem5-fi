"""Fault-effect propagation coverage (LSU v3.2.11 Task 2 / A1).

``trace_completeness.propagation_coverage`` (aliased as
``structural_chain_completeness`` since v3.2.11) answers a STRUCTURAL
question: did the expected stage kinds appear on the fault's own chain?
This module answers the different, EFFECT question: did the injected fault
actually diverge a value or a control decision, and did that divergence
reach a committed architectural outcome?

The two questions are deliberately separate.  A structurally complete chain
can carry an intact payload end to end (LQ04 is the canonical case: the
fault corrupts LQ-entry lifetime metadata, the response is bound by
senderState, and the delivered data is unchanged by construction), so the
honest effect grade for such a run is LIFECYCLE_ONLY, not COMPLETE.

Classification rules (v3.2.11 A1 spec):

- The chain is ONLY the events whose ``ptag`` equals the injection's
  ``ptag`` or whose ``dyn_inst_seq`` equals the injection's
  ``dyn_inst_seq`` (mirrors ``terminal_rules.chain_events``, with ``str()``
  normalization because numeric identity fields are ints in some trace
  vintages and JSON strings in others).  Time adjacency NEVER links events.
- ``value_diverged``: a chained ``register_writeback`` with
  ``data_corruption=1`` or ``value_matches_payload=0``; a chained
  ``consumer_commit`` with ``consumer_input_matches_source=0``; a chained
  ``consumer_commit`` whose own ``source_value_hash`` differs from its
  ``consumer_input_fnv`` when both exist; or a chained ``consumer_commit``
  whose ``consumer_input_fnv`` differs from its source event's
  ``writeback_value_fnv``/``data_fnv``/``consumer_output_fnv`` when both
  exist (``consumer_output_fnv`` carries the source hash on
  consumer->consumer re-taint edges, which dominate real traces).  "Both
  exist" means both are REAL hashes: the converter writes the literal
  string ``null`` into hash fields it has no value for (older vintages
  wrote ``0``, e.g. ``forward_data_fnv=0``), so every hash field is first
  normalized through ``_real_hash`` and a sentinel/empty/missing field is
  ABSENT -- a divergence is never fabricated from an absent hash.
- ``control_diverged``: a chained event whose ``detail`` contains any
  marker key from ``EFFECT_MARKERS[model]``.  Marker scanning is
  presence-based per the A1 spec; the marker VALUE is recorded in the
  evidence so the v3.2.11 audit round can refine it (for FW02 the
  refinement is ``fault_decision != none`` -- equivalently
  ``decision != normal_decision``: real traces record
  ``fault_decision=none`` on unaffected forwarding nodes and
  ``fault_decision=suppressed`` under the fault, whereas comparing
  ``fault_decision`` against ``normal_decision`` would flag every node).
- ``COMPLETE_CAUSAL_CHAIN`` only when a divergence exists AND a chained
  commit/errant_commit/consumer_commit or an oracle-failing terminal (SDC)
  explains it; ``PARTIAL`` when divergence/control evidence exists without
  that downstream link; ``LIFECYCLE_ONLY`` when the injection is TRIGGERED
  and nothing diverged; ``UNRESOLVED`` when there is no injection, the
  terminal is missing/UNRESOLVED, the trace declares itself INCOMPLETE, no
  summary record exists, or the injection never activated.
"""
from __future__ import annotations

# Control-flow effect marker keys per fault model: a chained event whose
# detail carries the key is control-divergence evidence for that model.
# v3.2.11 Task 2 seeds the models covered by the tests; the audit round
# (Task 6/7) extends and value-refines the table from real traces.
EFFECT_MARKERS: dict[str, tuple[str, ...]] = {
    # LQ04 corrupts LQ-entry lifetime metadata (valid+request bits).  Its
    # observable effect IS the entry-lifetime window; the delivered data is
    # unchanged by construction, so no control marker exists and intact
    # LQ04 chains grade LIFECYCLE_ONLY.
    "LQ04": (),
    # MD04 suppresses a memory-order violation report.  The suppression is
    # recorded on the injection node (verified: pilots_v3_2_6/MD04-R01).
    "MD04": ("violation_report_suppressed",),
    # FW02 corrupts the store->load forwarding decision; the forwarding
    # node records the decision taken under the fault (verified:
    # pilots_v3_2_4/FW02-R01).
    "FW02": ("fault_decision",),
    # SQ01 flips a bit of a store's data byte (verified:
    # pilots_v3_2_3/SQ01-R01 log, converter kind inj_store_data): a pure
    # value-domain fault whose divergence is captured by the hash checks,
    # with no control decision to mark.
    "SQ01": (),
}

# Terminals that by themselves explain a divergence: the oracle observed
# wrong output.  MASKED/SQUASHED/CRASH do not -- a crash may be unrelated
# and a squash erases the effect before the oracle sees it.
ORACLE_FAILING_TERMINALS = ("SDC",)

# Event types that turn a divergence into a committed architectural
# outcome.  consumer_commit is included: it records a consumer
# instruction's commit with its input/output values.
DOWNSTREAM_COMMIT_TYPES = ("commit", "errant_commit", "consumer_commit")

# Cap on the per-item divergence evidence lists; the counts stay exact.
_EVIDENCE_CAP = 20

_VALUE_FLAGS = (
    # (event_type, detail key, divergent value, evidence kind)
    ("register_writeback", "data_corruption", "1", "data_corruption"),
    ("register_writeback", "value_matches_payload", "0",
     "value_matches_payload"),
    ("consumer_commit", "consumer_input_matches_source", "0",
     "consumer_input_matches_source"),
)
# Source-event detail keys that can carry the hash of the value a consumer
# read.  Writeback-sourced edges carry it in writeback_value_fnv/data_fnv;
# consumer->consumer re-taint edges (the vast majority on real traces, e.g.
# 325 of the 326 consumer edges on pilots_v3_2_10/LQ04-R01) carry it in the
# source consumer's consumer_output_fnv.
_SOURCE_HASH_KEYS = ("writeback_value_fnv", "data_fnv", "consumer_output_fnv")

# Values the trace converter writes into a hash field when no hash exists
# for that edge: the current converter writes the literal string "null"
# (LP01 class=cc consumer nodes carry source_value_hash=null /
# consumer_output_fnv=null next to a real consumer_input_fnv), older
# vintages wrote "0" (seen as forward_data_fnv=0).  Truthiness-only guards
# read these sentinels as real hashes and fabricated 204 null-artifact
# evidence items archive-wide before _real_hash existed -- on
# pilots_v3_2_5/LP01-R01 every one of the 96 hash-based items was a
# "null"-vs-real comparison.  Comparison is case-insensitive so "None"
# (Python-repr style) is covered too; "0" cannot collide with a real FNV
# hash because these fields carry full fixed-width hex strings.
_ABSENT_HASH_SENTINELS = frozenset(("null", "none", "0", ""))


def _real_hash(value) -> str | None:
    """Normalize a hash field to a real hash string, or None when absent.

    Absent means: the key is missing (None), the field is empty or
    whitespace-only, or it holds one of the converter's null sentinels
    ("null"/"None", older "0").  Every hash comparison in this module goes
    through this helper, so a sentinel is never read as a real hash and a
    divergence is never fabricated from an absent hash.
    """
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in _ABSENT_HASH_SENTINELS:
        return None
    return text


def _detail(event: dict) -> dict:
    return dict(item.split("=", 1) for item in (event.get("detail") or "")
                .split(";") if "=" in item)


def _is_event(record: dict) -> bool:
    """Event records only: excludes edges, summaries and parse-error
    placeholders (which carry no record_type and no event_type)."""
    if "record_type" in record:
        return record["record_type"] == "event"
    return "event_type" in record


def _chain_events(events: list[dict], injection: dict) -> list[dict]:
    """Fault's own chain: same ptag or same dyn_inst_seq, str()-normalized.

    ptag 0/""/None carries no chain identity (platform convention: commit,
    squash and lifecycle nodes are written with ptag=0); such injections
    fall back to the dyn_inst_seq identity alone.
    """
    ptag = injection.get("ptag")
    seq = injection.get("dyn_inst_seq")
    ptag_s = None if ptag in (None, "") or str(ptag) == "0" else str(ptag)
    seq_s = None if seq in (None, "") else str(seq)
    chain = []
    for e in events:
        if ptag_s is not None and str(e.get("ptag")) == ptag_s:
            chain.append(e)
        elif seq_s is not None and str(e.get("dyn_inst_seq")) == seq_s:
            chain.append(e)
    return chain


def classify(model: str, events: list[dict], injection: dict | None,
             terminal: str) -> dict:
    """Grade the fault-effect propagation of one trace.

    ``events`` is the record list (event records plus, when available, the
    summary record); ``injection`` is the injection event record or None
    (controls); ``terminal`` is the adjudicated terminal state.
    """
    records = list(events or [])
    evt = [r for r in records if _is_event(r)]
    summaries = [r for r in records if r.get("record_type") == "summary"]
    summary = summaries[-1] if summaries else {}

    def _unresolved(reason: str, evidence: dict) -> dict:
        return {"fault_effect_propagation_coverage": "UNRESOLVED",
                "fault_effect_evidence": evidence,
                "fault_effect_reason": reason}

    if injection is None:
        # Controls (no injection event) and injection-less traces.
        return _unresolved("NO_INJECTION_EVENT", {
            "model": model,
            "chain_identity": "ptag+dyn_inst_seq (str-normalized)",
            "chain_events": 0,
        })

    # The chain exists as soon as the injection does; every later path
    # (including the UNRESOLVED gates) reports truthful chain statistics and
    # the chain-scoped divergence observation.
    chain = _chain_events(evt, injection)
    by_id = {}
    for e in evt:
        if e.get("event_id") is not None:
            by_id.setdefault(str(e["event_id"]), e)

    value_divergence: list[dict] = []
    control_divergence: list[dict] = []

    def _value(ev: dict, kind: str, **extra) -> None:
        item = {"event_id": ev.get("event_id"),
                "event_type": ev.get("event_type"), "kind": kind}
        item.update(extra)
        value_divergence.append(item)

    for e in chain:
        et = e.get("event_type")
        d = _detail(e)
        for ev_type, key, divergent, kind in _VALUE_FLAGS:
            if et == ev_type and str(d.get(key)) == divergent:
                _value(e, kind, **{key: d.get(key)})
        if et == "consumer_commit":
            # Both hash guards normalize through _real_hash first: the
            # converter's "null"/"None"/"0"/empty sentinels are ABSENT
            # hashes, never hashes to compare against.
            consumer_fnv = _real_hash(d.get("consumer_input_fnv"))
            # Own-edge check: the re-taint bookkeeping hash of the source
            # value vs. what this consumer actually read.  Independent of
            # the source event's records, so it also fires on edges whose
            # source event is missing or carries no source hash.
            own_hash = _real_hash(d.get("source_value_hash"))
            if consumer_fnv and own_hash and own_hash != consumer_fnv:
                _value(e, "source_value_hash_mismatch",
                       consumer_input_fnv=consumer_fnv,
                       source_value_hash=own_hash)
            src = by_id.get(str(e.get("source_event_id")))
            if consumer_fnv and src is not None:
                sd = _detail(src)
                for hk in _SOURCE_HASH_KEYS:
                    source_hash = _real_hash(sd.get(hk))
                    if source_hash and source_hash != consumer_fnv:
                        _value(e, "consumer_input_fnv_mismatch",
                               consumer_input_fnv=consumer_fnv,
                               source_event_id=e.get("source_event_id"),
                               source_hash_kind=hk,
                               source_hash=source_hash)

    markers = EFFECT_MARKERS.get(model, ())
    for e in chain:
        d = _detail(e)
        for marker in markers:
            if marker in d:
                control_divergence.append(
                    {"event_id": e.get("event_id"),
                     "event_type": e.get("event_type"),
                     "marker": marker, "marker_value": d.get(marker)})

    def _gate(reason: str) -> dict:
        return _unresolved(reason, {
            "model": model,
            "chain_identity": "ptag+dyn_inst_seq (str-normalized)",
            "injection_event_id": injection.get("event_id"),
            "activation_status": (injection.get("activation_status")
                                  or summary.get("fault_activation_status")),
            "chain_ptag": injection.get("ptag"),
            "chain_dyn_inst_seq": injection.get("dyn_inst_seq"),
            "chain_events": len(chain),
            "chain_event_types": sorted({str(e.get("event_type"))
                                         for e in chain}),
            "value_divergence_count": len(value_divergence),
            "value_divergence": value_divergence[:_EVIDENCE_CAP],
            "control_divergence_count": len(control_divergence),
            "control_divergence": control_divergence[:_EVIDENCE_CAP],
        })

    # -- UNRESOLVED gates, in order ------------------------------------
    if terminal is None:
        return _gate("TERMINAL_MISSING")
    if str(terminal).upper() == "UNRESOLVED":
        return _gate("TERMINAL_UNRESOLVED")
    if not summaries:
        return _gate("NO_SUMMARY_RECORD")
    if summary.get("trace_completeness") == "INCOMPLETE":
        return _gate("TRACE_DECLARED_INCOMPLETE")

    activation = (injection.get("activation_status")
                  or summary.get("fault_activation_status"))
    if str(activation).upper() != "TRIGGERED":
        # A dormant injection produced no fault effect to resolve.
        return _gate("INJECTION_NOT_TRIGGERED")

    # -- downstream explanation -----------------------------------------
    commit_types = sorted({str(e.get("event_type")) for e in chain
                           if e.get("event_type") in DOWNSTREAM_COMMIT_TYPES})
    oracle_failing = str(terminal).upper() in ORACLE_FAILING_TERMINALS

    evidence = {
        "model": model,
        "chain_identity": "ptag+dyn_inst_seq (str-normalized)",
        "injection_event_id": injection.get("event_id"),
        "activation_status": activation,
        "chain_ptag": injection.get("ptag"),
        "chain_dyn_inst_seq": injection.get("dyn_inst_seq"),
        "chain_events": len(chain),
        "chain_event_types": sorted({str(e.get("event_type"))
                                     for e in chain}),
        "control_markers": list(markers),
        "value_divergence_count": len(value_divergence),
        "value_divergence": value_divergence[:_EVIDENCE_CAP],
        "control_divergence_count": len(control_divergence),
        "control_divergence": control_divergence[:_EVIDENCE_CAP],
        "downstream_commit_types": commit_types,
        "oracle_failing_terminal": oracle_failing,
    }
    if len(value_divergence) > _EVIDENCE_CAP:
        evidence["value_divergence_truncated"] = True
    if len(control_divergence) > _EVIDENCE_CAP:
        evidence["control_divergence_truncated"] = True

    diverged = bool(value_divergence or control_divergence)
    if diverged and (commit_types or oracle_failing):
        reason = ("DIVERGENCE_WITH_ORACLE_FAILING_TERMINAL" if oracle_failing
                  and not commit_types
                  else "DIVERGENCE_WITH_DOWNSTREAM_COMMIT")
        return {"fault_effect_propagation_coverage": "COMPLETE_CAUSAL_CHAIN",
                "fault_effect_evidence": evidence,
                "fault_effect_reason": reason}
    if diverged:
        return {"fault_effect_propagation_coverage": "PARTIAL",
                "fault_effect_evidence": evidence,
                "fault_effect_reason": "DIVERGENCE_WITHOUT_DOWNSTREAM_LINK"}
    return {"fault_effect_propagation_coverage": "LIFECYCLE_ONLY",
            "fault_effect_evidence": evidence,
            "fault_effect_reason": "TRIGGERED_NO_DIVERGENCE"}
