"""Deterministic 12-model closure tool (LSU v3.2.12 Task 3).

Every verdict of the v3.2.12 closure round is computed here from the raw
per-pilot artifacts, deterministically, per the frozen standard
``docs/gem5-fi/lsu/implementation_v3_2/LSU_Propagation_Acceptance_Standard_v3.2.12.md``
and its normative companion
``audit_v3_2_12/pilot_record.schema.md``.  No status matrix or Excel cell may
ever override the fixed order below.

The tool reuses ``tools.lsu_propagation_audit.audit_pilot`` (keys
``identity, stages, evidence, terminal, oracle, missing, classification``)
for every trace-derived fact; it never re-parses a trace independently and
never forks the classifier.  The only files it reads directly, besides what
``audit_pilot`` already exports, are pilot sidecars (``pilot_meta.json`` for
the run-harness truncation flag / oracle-by-design markers and the
``supplementary.json`` SUPP sidecar), which are records, not traces.

Field mapping (standard §7, frozen):

- platform ``fault_effect_coverage`` ``PARTIAL`` -> coverage ``NONE`` +
  ``FinalClassification=PARTIAL`` (ruling recorded in the SDD ledger);
- ``fault_effect_coverage`` ``UNRESOLVED`` reason ``NO_INJECTION_EVENT`` ->
  coverage ``NOT_APPLICABLE``;
- ``terminal_rules.adjudicate`` hard terminals (CRASH/HANG) and the
  run-level TIMEOUT/NO_INJECTION/INCOMPLETE observations map onto
  ``ObservedTerminal``; a hard terminal always beats the oracle.

``FinalClassification`` (standard §6, fixed order, first rule that fires):

1. missing injection / absent or unusable evidence -> ``UNRESOLVED``;
2. HANG/TIMEOUT/SQUASHED with a proven trigger -> complete verdict;
3. complete effect with consumer -> complete verdict;
4. internal-only change -> ``LIFECYCLE_ONLY``;
5. otherwise -> ``PARTIAL`` (with the missing link named).

Complete verdicts obey the single-context rule (standard §4): one verified
complete chain in the pilot's own trace -> ``VERIFIED_SINGLE_CONTEXT``; two
or more -> ``COMPLETE_CAUSAL_CHAIN``.  A verdict is never computed across
binaries: the closure matrix splits per ``BinarySHA256`` and never merges.

Honesty invariants enforced loudly (a violating row is never written):

- every CSV cell is a value or the literal ``NULL``/``NOT_APPLICABLE``;
  an empty string is a defect;
- a bare ``PASS`` is a defect everywhere except the ``ApplicationOracle``
  column, whose mandated enum (standard §1.7) contains ``PASS``;
- ``FinalClassification`` complete while ``InjectionVerified`` is ``no`` is
  a defect.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from lsu_propagation_audit import audit_pilot  # noqa: E402

MODELS = ("A01", "A03", "FW02", "SQ01", "DA04", "LP01", "MD04", "FW05",
          "SQ03", "SP05", "LQ04", "RP01")

META_NAME = "pilot_meta.json"
SUPP_SIDECAR = "supplementary.json"

# -- the eight per-pilot fields (standard §1, closed value sets) -------------
RECORD_INTEGRITY_VALUES = ("VALID", "INVALID", "TRUNCATED")
TRACE_COMPLETENESS_VALUES = ("COMPLETE", "INCOMPLETE", "MISSING")
STRUCTURAL_VALUES = ("COMPLETE", "PARTIAL", "NONE")
COVERAGE_VALUES = ("COMPLETE", "LIFECYCLE_ONLY", "NONE", "NOT_APPLICABLE")
CAUSALITY_VALUES = ("PROVEN", "PARTIAL", "UNPROVEN")
TERMINAL_VALUES = ("SDC", "MASKED", "SQUASHED", "CRASH", "HANG", "TIMEOUT",
                   "NO_INJECTION", "INCOMPLETE", "UNRESOLVED")
ORACLE_VALUES = ("PASS", "FAIL", "MISSING", "NOT_APPLICABLE")
FINAL_VALUES = ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT",
                "LIFECYCLE_ONLY", "PARTIAL", "UNRESOLVED")

# terminal_rules reasons whose outcome is derived from the fault's own
# committed node (identity-verified by construction of the adjudication)
_PROVEN_REASONS = frozenset((
    "TARGET_COMMITTED_DATA_VALUE_PRESENT",
    "ORACLE_FAIL",
    "STORE_COMMITTED_LANE_CONSUMED_ORACLE_PASS",
    "STORE_COMMITTED_LANE_NOT_READ",
))
# an oracle FAIL without a causally attributable consumer: hops verified,
# decisive link not (standard §1.5)
_PARTIAL_REASONS = frozenset(("ORACLE_FAIL_NO_CAUSAL_CONSUMER",))

# chain event kinds that identity-link a hard terminal to the faulting entry:
# a replay/non-progress record on the fault's own dyn_inst_seq (RP01's skipped
# replay), or the abort record on the fault's own chain (A01/A03).
_HANG_EVIDENCE_KINDS = frozenset(("replay", "rp01_skip"))

# the ten brief-mandated missing-evidence matrix columns
MISSING_MATRIX_COLUMNS = [
    "ModelID", "PilotID", "MissingStage", "MissingEvent",
    "MissingCausalEdge", "RootCause", "RequiredHook",
    "RequiredWorkloadChange", "RequiredRunCount", "ExpectedEvidence",
]

# the 24 brief-mandated closure-matrix columns: the 20 v3.2.11 audit-matrix
# columns (EvidencePaths renamed to the plan's EvidencePath) plus the four
# standard fields the v3.2.11 matrix did not carry
CLOSURE_MATRIX_COLUMNS = [
    "ModelID", "SubUnit", "FaultDefinition", "PilotCount",
    "InjectionVerified", "ActivationVerified", "EarlyAnomalyVerified",
    "IntermediatePropagationVerified", "RegisterWritebackVerified",
    "ConsumerVerified", "CommitVerified", "TerminalVerified",
    "OracleVerified",
    "RecordIntegrity", "TraceCompleteness", "StructuralChainCompleteness",
    "FaultEffectPropagationCoverage", "ObservedTerminal",
    "ApplicationOracle", "FaultCausality", "FinalClassification",
    "MissingEvidence", "SupplementaryPilotRequired", "EvidencePath",
]

# the diagnostic feature dataset: five feature groups, one row per pilot or
# per path fragment (RowKind=PILOT, then RowKind=PATH_FRAGMENT in canonical
# chain order; EventOrdinal is the pilot's frozen ordinal on every row)
FEATURE_GROUP_COLUMNS = [
    # 1. provenance / identity
    "ModelID", "PilotID", "SampleRunID", "Seed", "EventOrdinal",
    "BinarySHA256", "WorkloadSHA256", "EvidencePath", "RowKind",
    "FragmentOrdinal", "FragmentStage", "FragmentEventID", "SupplementaryOf",
    # 2. injection site
    "PrimaryFaultModel", "InjectionSeq", "InjectionPC", "InjectionTick",
    "ActivationStatus", "InjectionCount",
    # 3. chain path
    "ChainEventCount", "ChainEdgeCount", "EarliestAnomalyType",
    "EarliestAnomalyEventID", "WritebackValueFnv", "ConsumerInputFnv",
    "ConsumerSourceLinked", "CommitSeq",
    # 4. outcome
    "ObservedTerminal", "TerminalReason", "ApplicationOracle",
    "OracleExpected", "OracleActual",
    # 5. verdict
    "RecordIntegrity", "TraceCompleteness", "StructuralChainCompleteness",
    "FaultEffectPropagationCoverage", "FaultCausality", "FinalClassification",
    "MissingEvidence",
]
FEATURE_DATASET_COLUMNS = FEATURE_GROUP_COLUMNS

# stage-gap codes a supplementary pilot could in principle close (the audit
# tool's STAGE_GAP_CODES contract, restated for the run-count column)
STAGE_GAP_CODES = frozenset((
    "NO_INJECTION_EVENT", "INJECTION_NOT_TRIGGERED",
    "NO_EARLY_ANOMALY_EVENT", "NO_INTERMEDIATE_PROPAGATION_EVENT",
    "NO_REGISTER_WRITEBACK_EVENT", "NO_CONSUMER_EDGE", "NO_COMMIT_EVENT",
))

_EARLY_HOOK_TEXT = ("the model's first post-injection observable stage "
                    "(address_formed A01/A03; forwarding_decision FW02/FW05; "
                    "store_writeback/store_mem_write DA04/SQ01/SQ03/SP05; "
                    "memory_response LP01/LQ04/MD04)")

# MissingEvidence row spec: every audit code maps to a complete row (no blank
# cell).  ``RequiredRunCount``: 1 = one supplementary/extended run closes it,
# 0 = no run closes it (a by-design absence or a recording requirement).
_MISSING_ROW_SPEC: dict[str, dict] = {
    "NO_INJECTION_EVENT": dict(
        stage="INJECTION", event="injection", edge="NOT_APPLICABLE",
        cause="no injection event exists in the run (trigger never fired, or "
              "a determinism control by design)",
        hook="NOT_APPLICABLE", workload="a trigger window that reaches an "
              "injectable event for the model",
        runs=1, expected="an injection record in trace_v31.jsonl"),
    "INJECTION_NOT_TRIGGERED": dict(
        stage="ACTIVATION", event="activation_status=TRIGGERED",
        edge="NOT_APPLICABLE",
        cause="the injection event exists but the fault never activated "
              "(dormant injection)",
        hook="the model's activation condition under the frozen trigger",
        workload="an activation-eligible instruction stream at the frozen "
                 "ordinal",
        runs=1, expected="activation_status=TRIGGERED on the injection"),
    "NO_EARLY_ANOMALY_EVENT": dict(
        stage="EARLY_ANOMALY", event="the model's early-anomaly event kind",
        edge="injection -> early anomaly (ptag/dyn_inst_seq identity)",
        cause="the fault's own chain carries no early-anomaly event after "
              "the injection",
        hook=_EARLY_HOOK_TEXT,
        workload="an instruction stream that exercises the faulted resource",
        runs=1, expected="the early-anomaly record on the fault's chain"),
    "NO_INTERMEDIATE_PROPAGATION_EVENT": dict(
        stage="INTERMEDIATE_PROPAGATION",
        event="propagation_edge with an endpoint on the chain",
        edge="an identity-linked propagation edge",
        cause="no propagation edge touches the fault's own chain",
        hook="CHAOSPropagation edge emission for the fault's events",
        workload="a consumer of the faulted value/site",
        runs=1, expected="at least one on-chain propagation_edge"),
    "NO_REGISTER_WRITEBACK_EVENT": dict(
        stage="REGISTER_WRITEBACK", event="register_writeback",
        edge="response -> writeback (data_fnv -> writeback_value_fnv)",
        cause="the faulting instruction produced no register writeback "
              "record on its chain",
        hook="the writeback trace point of the faulting instruction",
        workload="a load/consumer path that writes the register",
        runs=1, expected="register_writeback with a real value hash"),
    "NO_CONSUMER_EDGE": dict(
        stage="CONSUMER", event="consumer_commit",
        edge="writeback -> consumer (consumer_input_fnv == producer hash)",
        cause="no causally attributable consumer of the faulted value "
              "exists in the trace",
        hook="CHAOSPropagation consumer events",
        workload="an instruction that consumes the faulted value (e.g. the "
                 "same-address reload workload)",
        runs=1, expected="consumer_commit identity- and hash-linked to the "
                         "writeback"),
    "NO_COMMIT_EVENT": dict(
        stage="COMMIT", event="commit/errant_commit",
        edge="writeback -> commit (dyn_inst_seq identity)",
        cause="the faulting instruction never committed (or the commit node "
              "is absent from the chain)",
        hook="the commit trace point",
        workload="NOT_APPLICABLE",
        runs=1, expected="a commit node on the fault's own dyn_inst_seq"),
    "TERMINAL_MISSING": dict(
        stage="TERMINAL", event="terminal_state in the summary",
        edge="NOT_APPLICABLE",
        cause="no terminal state could be adjudicated for the run",
        hook="the run harness must complete or explicitly cut the run",
        workload="NOT_APPLICABLE",
        runs=1, expected="an adjudicable terminal record"),
    "TERMINAL_UNRESOLVED": dict(
        stage="TERMINAL", event="an outcome terminal",
        edge="terminal -> injection (identity + data rule)",
        cause="chain-scoped adjudication could not resolve an outcome "
              "terminal (target not committed, no writeback evidence, store "
              "not committed)",
        hook="the missing upstream stage named in the terminal reason",
        workload="NOT_APPLICABLE",
        runs=1, expected="the terminal reason's prerequisite stage evidence"),
    "ORACLE_FILE_MISSING": dict(
        stage="ORACLE", event="raw oracle.log/stdout.log checksum",
        edge="NOT_APPLICABLE",
        cause="the raw oracle artifact is absent although the run type "
              "expects one; the outcome survives only in pilot_meta.json "
              "(v3.2.11 DA04/LP01/MD04/FW05 gap)",
        hook="NOT_APPLICABLE", workload="NOT_APPLICABLE",
        runs=1, expected="a SUPP pilot with a raw oracle.log under the "
                         "original seed and context"),
    "ORACLE_MALFORMED": dict(
        stage="ORACLE", event="raw oracle.log checksum",
        edge="NOT_APPLICABLE",
        cause="the raw oracle artifact exists but does not parse",
        hook="the run harness oracle writer",
        workload="NOT_APPLICABLE",
        runs=1, expected="a parseable two-line oracle.log"),
    "ORACLE_META_INCONSISTENT": dict(
        stage="ORACLE", event="oracle.log vs pilot_meta.json",
        edge="NOT_APPLICABLE",
        cause="the raw oracle artifact contradicts the meta-recorded "
              "outcome; the raw artifact wins and the conflict is flagged",
        hook="the run harness oracle writer",
        workload="NOT_APPLICABLE",
        runs=1, expected="a SUPP raw-oracle run that corroborates one side"),
    "TRACE_FILE_MISSING": dict(
        stage="TRACE", event="trace_v31.jsonl",
        edge="NOT_APPLICABLE",
        cause="no trace file exists for the pilot, so no stage evidence "
              "can be derived",
        hook="the run harness trace writer",
        workload="NOT_APPLICABLE",
        runs=1, expected="a trace_v31.jsonl with injection, chain and "
                         "summary records"),
    "TRACE_INCOMPLETE": dict(
        stage="TRACE", event="the closing summary record",
        edge="NOT_APPLICABLE",
        cause="the trace declares itself INCOMPLETE (forbidden "
              "incomplete-declares-MASKED combination, or missing/inconsistent "
              "summary)",
        hook="the run harness must run to the workload's natural completion",
        workload="NOT_APPLICABLE",
        runs=1, expected="a COMPLETE trace with exactly one consistent "
                         "summary"),
    "SUMMARY_RECORD_COUNT": dict(
        stage="TRACE", event="exactly one summary record",
        edge="NOT_APPLICABLE",
        cause="the trace does not carry exactly one summary record",
        hook="the trace writer's single closing summary",
        workload="NOT_APPLICABLE",
        runs=1, expected="exactly one internally consistent summary record"),
    "MALFORMED_RECORDS": dict(
        stage="RECORD_INTEGRITY", event="every JSONL record parses",
        edge="NOT_APPLICABLE",
        cause="the record stream contains malformed lines",
        hook="the trace writer", workload="NOT_APPLICABLE",
        runs=1, expected="a stream where every record parses"),
    "VALIDATOR_ERRORS": dict(
        stage="RECORD_INTEGRITY", event="the trace validator",
        edge="NOT_APPLICABLE",
        cause="the trace validator reported errors (malformed or "
              "inconsistent records)",
        hook="the injector/converter record emission",
        workload="NOT_APPLICABLE",
        runs=1, expected="a validator-clean stream"),
    "HASH_MISMATCH": dict(
        stage="TRACE", event="trace_v31.jsonl.sha256",
        edge="NOT_APPLICABLE",
        cause="the recorded trace sidecar hash does not match the trace "
              "file",
        hook="the run harness sidecar writer", workload="NOT_APPLICABLE",
        runs=0, expected="the correct sidecar re-recorded; the historical "
                         "artifact itself is never overwritten"),
    "META_MISSING": dict(
        stage="PROVENANCE", event="pilot_meta.json",
        edge="NOT_APPLICABLE",
        cause="the pilot meta record is absent",
        hook="the run harness meta writer", workload="NOT_APPLICABLE",
        runs=0, expected="pilot_meta.json recorded by the run that produced "
                         "the pilot"),
    "META_MALFORMED": dict(
        stage="PROVENANCE", event="pilot_meta.json",
        edge="NOT_APPLICABLE",
        cause="the pilot meta record does not parse",
        hook="the run harness meta writer", workload="NOT_APPLICABLE",
        runs=0, expected="a parseable pilot_meta.json"),
    "MANIFEST_MISSING": dict(
        stage="PROVENANCE", event="manifest.json",
        edge="NOT_APPLICABLE",
        cause="the run manifest is absent (no recorded binary/workload SHA)",
        hook="the run harness manifest writer", workload="NOT_APPLICABLE",
        runs=0, expected="manifest.json with binary and workload SHA256"),
    "MANIFEST_MALFORMED": dict(
        stage="PROVENANCE", event="manifest.json",
        edge="NOT_APPLICABLE",
        cause="the run manifest does not parse",
        hook="the run harness manifest writer", workload="NOT_APPLICABLE",
        runs=0, expected="a parseable manifest.json"),
    "BINARY_SHA_UNRECORDED": dict(
        stage="PROVENANCE", event="the recorded binary SHA256",
        edge="NOT_APPLICABLE",
        cause="the manifest records no binary SHA256, so the pilot cannot be "
              "purity-checked or binary-keyed",
        hook="the run harness manifest writer", workload="NOT_APPLICABLE",
        runs=0, expected="the binary SHA256 recorded next to the run that "
                         "produced the pilot"),
    "BINARY_SHA_MISMATCH": dict(
        stage="PROVENANCE", event="the recorded binary SHA256",
        edge="NOT_APPLICABLE",
        cause="the pilot's recorded binary SHA differs from the expected "
              "one; pilots from different binaries are never merged",
        hook="NOT_APPLICABLE", workload="NOT_APPLICABLE",
        runs=0, expected="the pilot re-run under the expected binary, or an "
                         "explicit per-binary split"),
    "PILOT_DIR_ABSENT": dict(
        stage="PILOT", event="the pilot directory",
        edge="NOT_APPLICABLE",
        cause="the pilot directory does not exist",
        hook="NOT_APPLICABLE", workload="NOT_APPLICABLE",
        runs=1, expected="the pilot directory with its raw artifacts"),
}

_GENERIC_ROW_SPEC = dict(
    stage="UNSPECIFIED", event="NOT_APPLICABLE", edge="NOT_APPLICABLE",
    cause="audit code not yet mapped in the closure tool's spec table",
    hook="NOT_APPLICABLE", workload="NOT_APPLICABLE",
    runs=1, expected="the evidence the audit code names, supplied by a "
                     "supplementary run or an injector trace addition",
)


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _agg(values):
    """Aggregate per-pilot values: ``yes(5/5)`` when uniform,
    ``mixed(yes=3;missing=2)`` otherwise; never empty (the v3.2.11 matrix
    format, restated locally so the classifier is not forked)."""
    if not values:
        return "n/a(0)"
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    if len(counts) == 1:
        return f"{next(iter(counts))}({len(values)}/{len(values)})"
    order = ["yes", "no", "missing", "n/a", "PASS", "FAIL",
             "MISSING", "NOT_APPLICABLE"]
    parts = [f"{key}={counts[key]}" for key in order if key in counts]
    parts.extend(f"{key}={counts[key]}" for key in sorted(counts)
                 if key not in order)
    return "mixed(" + ";".join(parts) + ")"


def _read_json(path: Path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _value_or_null(value) -> str:
    return "NULL" if value in (None, "") else str(value)


def _value_or_na(value) -> str:
    return "NOT_APPLICABLE" if value in (None, "") else str(value)


def _write_csv(rows, columns, out: Path) -> None:
    """Write a CSV honouring the honesty invariants: every cell is a value or
    the literal NULL/NOT_APPLICABLE; an empty string is a defect; a bare PASS
    is a defect everywhere except the ApplicationOracle column, whose
    mandated enum (standard §1.7) contains PASS."""
    out = Path(out)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(columns)
        for row in rows:
            cells = []
            for column in columns:
                value = row.get(column)
                text = "" if value is None else str(value)
                if not text.strip():
                    raise ValueError(
                        f"empty cell for column {column!r} in row "
                        f"{row.get('PilotID') or row.get('ModelID')!r}")
                if text.strip().upper() == "PASS" and column != (
                        "ApplicationOracle"):
                    raise ValueError(
                        f"bare PASS in column {column!r} in row "
                        f"{row.get('PilotID') or row.get('ModelID')!r}")
                cells.append(text)
            writer.writerow(cells)


# ---------------------------------------------------------------------------
# the record builder
# ---------------------------------------------------------------------------

def _record_integrity(audit: dict, meta, trace_exists: bool):
    missing = audit["missing"]
    records = audit["evidence"]["records"]
    truncated_flag = bool(((meta or {}).get("trace") or {})
                          .get("truncated")) if isinstance(meta, dict) \
        else False
    if trace_exists and (truncated_flag or records["summaries"] == 0):
        return "TRUNCATED"
    if "TRACE_FILE_MISSING" in missing:
        # an absent stream is never read as VALID (standard §8 T5); the cause
        # is named explicitly in MissingEvidence
        return "INVALID"
    if ({"VALIDATOR_ERRORS", "MALFORMED_RECORDS", "SUMMARY_RECORD_COUNT"}
            & set(missing)):
        return "INVALID"
    return "VALID"


def _trace_completeness(audit: dict, trace_exists: bool) -> str:
    if not trace_exists or "TRACE_FILE_MISSING" in audit["missing"]:
        return "MISSING"
    if ({"TRACE_INCOMPLETE", "SUMMARY_RECORD_COUNT", "MALFORMED_RECORDS",
         "VALIDATOR_ERRORS"} & set(audit["missing"])):
        return "INCOMPLETE"
    declared = audit["terminal"].get("trace_completeness")
    return "COMPLETE" if declared == "COMPLETE" else "INCOMPLETE"


def _structural(audit: dict) -> str:
    value = audit["evidence"]["structural_chain_completeness"]
    if value == "COMPLETE":
        return "COMPLETE"
    if value == "INCOMPLETE":
        return "PARTIAL"
    return "NONE"  # "n/a": no chain identity exists


def _coverage(audit: dict) -> str:
    classification = audit["classification"]
    reason = audit["evidence"]["fault_effect"].get("reason")
    if classification == "COMPLETE_CAUSAL_CHAIN":
        return "COMPLETE"
    if classification == "LIFECYCLE_ONLY":
        return "LIFECYCLE_ONLY"
    if classification == "UNRESOLVED" and reason == "NO_INJECTION_EVENT":
        return "NOT_APPLICABLE"
    # platform PARTIAL (divergence, no downstream link) and the remaining
    # UNRESOLVED gates both carry no verified effect (ruling + standard §7)
    return "NONE"


def _observed_terminal(audit: dict) -> str:
    terminal = audit["terminal"]
    adjudicated = terminal.get("adjudicated")
    observed = terminal.get("observed")
    reason = terminal.get("reason")
    injection_verified = audit["stages"]["injection_verified"] == "yes"
    if adjudicated in ("SDC", "CRASH", "HANG", "SQUASHED"):
        return adjudicated
    if observed == "TIMEOUT":
        return "TIMEOUT"
    if not injection_verified:
        return "NO_INJECTION"
    if adjudicated == "UNRESOLVED" and reason == "TRACE_INCOMPLETE":
        return "INCOMPLETE"
    return adjudicated or "UNRESOLVED"


def _application_oracle(audit: dict, meta) -> str:
    oracle = audit["oracle"]
    status = oracle.get("status")
    if status in ("ok", "inconsistent"):
        # the raw artifact wins; a meta contradiction is flagged in evidence
        return "PASS" if oracle.get("pass") else "FAIL"
    # absent or malformed raw artifact: by-design no-golden runs are the only
    # NOT_APPLICABLE case, and only when the run records it explicitly
    if isinstance(meta, dict):
        classification = meta.get("classification") or {}
        if (classification.get("oracle_outcome") == "NOT_APPLICABLE"
                or meta.get("run_type") in ("count_only", "preflight")):
            return "NOT_APPLICABLE"
    return "MISSING"


def _causality(audit: dict) -> str:
    stages = audit["stages"]
    if stages["injection_verified"] != "yes":
        return "UNPROVEN"
    if stages["activation_verified"] != "yes":
        # a dormant fault has no effect to attribute (RF2: ActivationVerified
        # never grades a complete verdict)
        return "UNPROVEN"
    terminal = audit["terminal"]
    adjudicated = terminal.get("adjudicated")
    reason = terminal.get("reason")
    chain = audit["evidence"]["chain"]
    kinds = set(chain.get("kinds") or ())
    if reason in _PROVEN_REASONS:
        return "PROVEN"
    if reason in _PARTIAL_REASONS:
        return "PARTIAL"
    if adjudicated == "CRASH":
        # attributable only when the abort record sits on the fault's own
        # chain (the v3.2.11 A01/A03 crashes were off-chain -> UNPROVEN)
        return "PROVEN" if "simulator_abort" in kinds else "UNPROVEN"
    if adjudicated in ("HANG", "TIMEOUT"):
        if kinds & _HANG_EVIDENCE_KINDS:
            return "PROVEN"
        return ("PARTIAL" if chain.get("events", 0) > 1 else "UNPROVEN")
    if adjudicated == "SQUASHED":
        # the squash node is the faulting instruction's own (identity-linked)
        # but nothing proves the squash is fault-CAUSED: the frozen v3.2.11
        # line keeps unproven squashes below a complete verdict
        return "PARTIAL"
    if adjudicated in ("MASKED", "SDC", "UNRESOLVED"):
        return ("PARTIAL" if chain.get("events", 0) > 1 else "UNPROVEN")
    return "UNPROVEN"


def _verified_chain_count(audit: dict, coverage: str, terminal: str,
                          causality: str) -> int:
    if coverage == "COMPLETE":
        detail = audit["evidence"]["fault_effect"].get("detail")
        ids = set()
        if isinstance(detail, dict):
            for item in detail.get("value_divergence") or []:
                if item.get("event_type") == "consumer_commit" \
                        and item.get("event_id") is not None:
                    ids.add(str(item["event_id"]))
        return len(ids) if ids else 1
    if terminal in ("HANG", "TIMEOUT", "SQUASHED") and causality == "PROVEN":
        return 1
    return 0


def build_pilot_record(pilot_dir, model: str,
                       supplementary_of: str | None = None,
                       binary_sha: str | None = None) -> dict:
    """Build the per-pilot closure record: the eight standard fields plus the
    identity/provenance columns and the writer internals (all JSON-safe)."""
    if model not in MODELS:
        raise ValueError(f"unknown model {model!r}; expected one of {MODELS}")
    pilot_dir = Path(pilot_dir)
    audit = audit_pilot(pilot_dir, model, binary_sha=binary_sha)

    meta = _read_json(pilot_dir / META_NAME)
    trace_exists = (pilot_dir / "trace_v31.jsonl").is_file()

    supp_of = supplementary_of
    if supp_of is None:
        sidecar = _read_json(pilot_dir / SUPP_SIDECAR)
        if isinstance(sidecar, dict) and sidecar.get("supplementary_of"):
            supp_of = str(sidecar["supplementary_of"])

    identity = audit["identity"]
    stages = audit["stages"]
    evidence = audit["evidence"]

    integrity = _record_integrity(audit, meta, trace_exists)
    completeness = _trace_completeness(audit, trace_exists)
    structural = _structural(audit)
    coverage = _coverage(audit)
    terminal = _observed_terminal(audit)
    oracle_field = _application_oracle(audit, meta)
    causality = _causality(audit)
    chains = _verified_chain_count(audit, coverage, terminal, causality)

    record = {
        # identity / provenance (schema §3)
        "ModelID": model,
        "PilotID": pilot_dir.name,
        "SampleRunID": identity.get("sample_run_id"),
        "Seed": identity.get("seed"),
        "EventOrdinal": identity.get("event_ordinal"),
        "BinarySHA256": identity.get("binary_sha256"),
        "WorkloadSHA256": identity.get("workload_sha256"),
        "EvidencePath": identity.get("pilot_dir"),
        "MissingEvidence": (";".join(audit["missing"]) if audit["missing"]
                             else "none"),
        "SupplementaryOf": supp_of,
        # the eight standard fields
        "RecordIntegrity": integrity,
        "TraceCompleteness": completeness,
        "StructuralChainCompleteness": structural,
        "FaultEffectPropagationCoverage": coverage,
        "FaultCausality": causality,
        "ObservedTerminal": terminal,
        "ApplicationOracle": oracle_field,
        # writer internals
        "InjectionVerified": ("yes" if stages["injection_verified"] == "yes"
                              else "no"),
        "ActivationVerified": ("yes" if stages["activation_verified"] == "yes"
                               else "no"),
        "Stages": dict(stages),
        "SubUnit": identity.get("sub_unit"),
        "FaultDefinition": identity.get("fault_definition"),
        "TerminalReason": audit["terminal"].get("reason"),
        "AdjudicatedTerminal": audit["terminal"].get("adjudicated"),
        "VerifiedChainCount": chains,
        "MissingCodes": list(audit["missing"]),
        "ChainKinds": list(evidence["chain"].get("kinds") or ()),
        "ChainEventCount": evidence["chain"].get("events", 0),
        "ChainEdgeCount": evidence["chain"].get("edges_on_chain", 0),
        "InjectionSeq": evidence.get("injection_seq"),
        "InjectionPC": evidence.get("pc"),
        "InjectionTick": evidence.get("tick"),
        "ActivationStatus": (evidence["fault_effect"]["detail"] or {}).get(
            "activation_status") if isinstance(
            evidence["fault_effect"].get("detail"), dict) else None,
        "InjectionCount": identity.get("injection_count"),
        "EarliestAnomalyType": (evidence.get("earliest_anomaly") or {}).get(
            "event_type"),
        "EarliestAnomalyEventID": (evidence.get("earliest_anomaly") or {}).get(
            "event_id"),
        # stage features carry the explicit absence literal when the stage
        # did not occur (never a silent zero, never a blank)
        "WritebackValueFnv": (
            (evidence.get("writeback") or {}).get("writeback_value_fnv")
            if stages["register_writeback_verified"] == "yes"
            else "NOT_APPLICABLE"),
        "ConsumerInputFnv": (
            (evidence.get("consumer") or {}).get("consumer_input_fnv")
            if stages["consumer_verified"] == "yes"
            else "NOT_APPLICABLE"),
        "ConsumerSourceLinked": (
            (evidence.get("consumer") or {}).get("source_linked")
            if stages["consumer_verified"] == "yes"
            else "NOT_APPLICABLE"),
        "CommitSeq": (
            (evidence.get("commit") or {}).get("commit_seq")
            if stages["commit_verified"] == "yes"
            else "NOT_APPLICABLE"),
        "OracleExpected": audit["oracle"].get("expected"),
        "OracleActual": audit["oracle"].get("actual"),
        "OracleStatus": audit["oracle"].get("status"),
    }
    record["PathFragments"] = _path_fragments(record)
    record["FinalClassification"] = final_classification(record)
    return record


def _path_fragments(record: dict) -> list[dict]:
    """The pilot's verified path fragments in canonical chain order
    (injection -> early anomaly -> writeback -> consumer -> commit); absent
    stages contribute no fragment, never a zero placeholder."""
    fragments = [
        {"stage": "injection",
         "event_id": (None if record["InjectionSeq"] is None
                      else f"seq={record['InjectionSeq']}")},
    ]
    if record.get("EarliestAnomalyEventID") is not None:
        fragments.append({"stage": record["EarliestAnomalyType"],
                          "event_id": record["EarliestAnomalyEventID"]})
    if record["Stages"].get("register_writeback_verified") == "yes":
        fragments.append({"stage": "register_writeback", "event_id": "NULL"})
    if record["Stages"].get("consumer_verified") == "yes":
        fragments.append({"stage": "consumer_commit", "event_id": "NULL"})
    if record["Stages"].get("commit_verified") == "yes":
        fragments.append({"stage": "commit", "event_id": "NULL"})
    return fragments


# ---------------------------------------------------------------------------
# FinalClassification — the fixed order (standard §6)
# ---------------------------------------------------------------------------

def final_classification(record: dict) -> str:
    """Apply the frozen five-rule order; the first rule that fires decides."""
    def field(name: str) -> str:
        value = record.get(name)
        return str(value).upper() if value is not None else ""

    terminal = field("ObservedTerminal")
    if terminal in ("NO_INJECTION", "INCOMPLETE", "UNRESOLVED"):
        return "UNRESOLVED"  # rule 1: a missing injection is never a terminal
    if field("RecordIntegrity") in ("INVALID", "TRUNCATED"):
        return "UNRESOLVED"
    if field("TraceCompleteness") in ("MISSING", "INCOMPLETE"):
        return "UNRESOLVED"
    if field("StructuralChainCompleteness") == "NONE":
        return "UNRESOLVED"

    injection_ok = record.get("InjectionVerified") == "yes"
    activation_ok = record.get("ActivationVerified") == "yes"
    proven = field("FaultCausality") == "PROVEN"
    struct_complete = field("StructuralChainCompleteness") == "COMPLETE"
    integrity_ok = (field("RecordIntegrity") == "VALID"
                    and field("TraceCompleteness") == "COMPLETE")
    chains = int(record.get("VerifiedChainCount") or 0)
    complete = ("COMPLETE_CAUSAL_CHAIN" if chains >= 2
               else "VERIFIED_SINGLE_CONTEXT")

    if terminal in ("HANG", "TIMEOUT", "SQUASHED") and proven:
        # rule 2: proven-trigger hard terminals
        if injection_ok and activation_ok and struct_complete and integrity_ok:
            return complete
        return "PARTIAL"  # an unverified injection caps at PARTIAL (rule 5)
    if field("FaultEffectPropagationCoverage") == "COMPLETE" and proven:
        # rule 3: complete effect with a consumer
        if injection_ok and activation_ok and struct_complete and integrity_ok:
            return complete
        return "PARTIAL"
    if (field("FaultEffectPropagationCoverage") == "LIFECYCLE_ONLY"
            and activation_ok and struct_complete
            and terminal not in ("HANG", "TIMEOUT", "SQUASHED", "CRASH")):
        # rule 4: internal-only change; an unproven hard terminal is a
        # divergence of control, never a "nothing diverged" observation
        return "LIFECYCLE_ONLY"
    return "PARTIAL"  # rule 5: the missing link is named in MissingEvidence


# ---------------------------------------------------------------------------
# the missing-evidence matrix
# ---------------------------------------------------------------------------

def write_missing_matrix(records: list, out) -> None:
    """One row per missing item: every missing stage carries a root cause and
    an integer run count; no cell is ever blank."""
    rows = []
    for record in records:
        for code in record.get("MissingCodes") or []:
            spec = _MISSING_ROW_SPEC.get(code, _GENERIC_ROW_SPEC)
            runs = spec["runs"]
            if code == "NO_INJECTION_EVENT" \
                    and "CONTROL" in str(record.get("PilotID", "")).upper():
                # a determinism control is zero-injection by design: not a
                # gap, never counted as an independent sample
                rows.append({
                    "ModelID": record.get("ModelID"),
                    "PilotID": record.get("PilotID"),
                    "MissingStage": spec["stage"],
                    "MissingEvent": spec["event"],
                    "MissingCausalEdge": spec["edge"],
                    "RootCause": "determinism control: zero injection by "
                                 "design (a replication, not a gap)",
                    "RequiredHook": "NOT_APPLICABLE",
                    "RequiredWorkloadChange": "NOT_APPLICABLE",
                    "RequiredRunCount": "0",
                    "ExpectedEvidence": "NOT_APPLICABLE (control "
                                         "replication)",
                })
                continue
            rows.append({
                "ModelID": record.get("ModelID"),
                "PilotID": record.get("PilotID"),
                "MissingStage": spec["stage"],
                "MissingEvent": spec["event"],
                "MissingCausalEdge": spec["edge"],
                "RootCause": spec["cause"],
                "RequiredHook": spec["hook"],
                "RequiredWorkloadChange": spec["workload"],
                "RequiredRunCount": str(int(runs)),
                "ExpectedEvidence": spec["expected"],
            })
    if not rows:
        # an explicit empty matrix would silently read as "nothing missing";
        # the literal keeps the artifact honest
        rows = [{"ModelID": "NONE", "PilotID": "NONE",
                 "MissingStage": "NONE", "MissingEvent": "NOT_APPLICABLE",
                 "MissingCausalEdge": "NOT_APPLICABLE",
                 "RootCause": "no missing evidence in the supplied records",
                 "RequiredHook": "NOT_APPLICABLE",
                 "RequiredWorkloadChange": "NOT_APPLICABLE",
                 "RequiredRunCount": "0",
                 "ExpectedEvidence": "NOT_APPLICABLE"}]
    _write_csv(rows, MISSING_MATRIX_COLUMNS, Path(out))


# ---------------------------------------------------------------------------
# the closure matrix
# ---------------------------------------------------------------------------

def _validate_record_for_matrix(record: dict) -> None:
    """Hard invariants (schema §2): a complete verdict over an unverified
    injection or a dormant activation is a defect and must be rejected
    loudly."""
    final = record.get("FinalClassification")
    if final in ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT"):
        for column in ("InjectionVerified", "ActivationVerified"):
            if record.get(column) != "yes":
                raise ValueError(
                    f"defect: FinalClassification={final!r} while "
                    f"{column}={record.get(column)!r} in pilot "
                    f"{record.get('PilotID')!r}")


def _closure_rows(records: list) -> list:
    for record in records:
        _validate_record_for_matrix(record)
    models = []
    for record in records:
        if record.get("ModelID") not in models:
            models.append(record.get("ModelID"))
    rows = []
    for model in models:
        model_records = [r for r in records if r.get("ModelID") == model]
        by_binary: dict[str, list] = {}
        for record in model_records:
            sha = record.get("BinarySHA256") or "unknown"
            by_binary.setdefault(sha, []).append(record)
        shas = sorted(by_binary)
        for sha in shas:
            group = by_binary[sha]
            row = _closure_row(model, group)
            if len(by_binary) > 1:
                # a verdict is never computed across binaries (standard §6):
                # one row per recorded binary, never a merged verdict
                row["ModelID"] = f"{model}@{sha[:8]}"
            rows.append(row)
    return rows


def _closure_row(model: str, records: list) -> dict:
    def stage_values(field):
        return [r.get("Stages", {}).get(field, "n/a") for r in records]

    complete_records = [r for r in records if r.get("FinalClassification") in
                        ("COMPLETE_CAUSAL_CHAIN", "VERIFIED_SINGLE_CONTEXT")]
    # single-context corroboration (standard §4): per model, two or more
    # frozen contexts with a verified complete chain -> COMPLETE_CAUSAL_CHAIN
    upgrade = len(complete_records) >= 2
    finals = []
    for record in records:
        final = record.get("FinalClassification")
        if upgrade and final == "VERIFIED_SINGLE_CONTEXT":
            final = "COMPLETE_CAUSAL_CHAIN"
        finals.append(final)

    missing_union: list[str] = []
    for record in records:
        for code in record.get("MissingCodes") or []:
            if code not in missing_union:
                missing_union.append(code)
    sub_unit = next((r.get("SubUnit") for r in records
                     if r.get("SubUnit")), "n/a")
    fault_def = next((r.get("FaultDefinition") for r in records
                      if r.get("FaultDefinition")), "n/a")

    row = {
        "ModelID": model,
        "SubUnit": sub_unit,
        "FaultDefinition": fault_def,
        "PilotCount": str(len(records)),
        "InjectionVerified": _agg(stage_values("injection_verified")),
        "ActivationVerified": _agg(stage_values("activation_verified")),
        "EarlyAnomalyVerified": _agg(stage_values("early_anomaly_verified")),
        "IntermediatePropagationVerified": _agg(
            stage_values("intermediate_propagation_verified")),
        "RegisterWritebackVerified": _agg(
            stage_values("register_writeback_verified")),
        "ConsumerVerified": _agg(stage_values("consumer_verified")),
        "CommitVerified": _agg(stage_values("commit_verified")),
        "TerminalVerified": _agg(stage_values("terminal_verified")),
        "OracleVerified": _agg(stage_values("oracle_verified")),
        "RecordIntegrity": _agg([r.get("RecordIntegrity") for r in records]),
        "TraceCompleteness": _agg([r.get("TraceCompleteness") for r
                                  in records]),
        "StructuralChainCompleteness": _agg(
            [r.get("StructuralChainCompleteness") for r in records]),
        "FaultEffectPropagationCoverage": _agg(
            [r.get("FaultEffectPropagationCoverage") for r in records]),
        "ObservedTerminal": _agg([r.get("ObservedTerminal") for r
                                  in records]),
        "ApplicationOracle": _agg([r.get("ApplicationOracle") for r
                                   in records]),
        "FaultCausality": _agg([r.get("FaultCausality") for r in records]),
        "FinalClassification": (finals[0] if len(set(finals)) == 1
                                else _agg(finals)),
        "MissingEvidence": (";".join(missing_union) if missing_union
                            else "none"),
        "SupplementaryPilotRequired": str(
            len([c for c in missing_union if c in STAGE_GAP_CODES])),
        "EvidencePath": ";".join(
            str(r.get("EvidencePath")) for r in records
            if r.get("EvidencePath")) or "none",
    }
    return row


def write_closure_matrix(records: list, out) -> None:
    _write_csv(_closure_rows(records), CLOSURE_MATRIX_COLUMNS, Path(out))


# ---------------------------------------------------------------------------
# the diagnostic feature dataset
# ---------------------------------------------------------------------------

def _feature_row(record: dict, kind: str, ordinal: int,
                 fragment: dict | None) -> dict:
    stage = fragment["stage"] if fragment else None
    present = {
        "consumer_commit": record["Stages"].get("consumer_verified") == "yes",
        "register_writeback": (record["Stages"].get(
            "register_writeback_verified") == "yes"),
        "commit": record["Stages"].get("commit_verified") == "yes",
    }
    consumer_feature = (record.get("ConsumerInputFnv")
                        if present["consumer_commit"] else None)
    commit_feature = (record.get("CommitSeq") if present["commit"]
                      else None)
    writeback_feature = (record.get("WritebackValueFnv")
                         if present["register_writeback"] else None)
    return {
        # group 1: provenance / identity
        "ModelID": record.get("ModelID"),
        "PilotID": record.get("PilotID"),
        "SampleRunID": _value_or_null(record.get("SampleRunID")),
        "Seed": _value_or_null(record.get("Seed")),
        "EventOrdinal": _value_or_null(record.get("EventOrdinal")),
        "BinarySHA256": _value_or_null(record.get("BinarySHA256")),
        "WorkloadSHA256": _value_or_null(record.get("WorkloadSHA256")),
        "EvidencePath": _value_or_null(record.get("EvidencePath")),
        "RowKind": kind,
        "FragmentOrdinal": str(ordinal),
        "FragmentStage": _value_or_na(stage),
        "FragmentEventID": _value_or_na(
            fragment["event_id"] if fragment else None),
        "SupplementaryOf": _value_or_na(record.get("SupplementaryOf")),
        # group 2: injection site
        "PrimaryFaultModel": record.get("ModelID"),
        "InjectionSeq": _value_or_null(record.get("InjectionSeq")),
        "InjectionPC": _value_or_null(record.get("InjectionPC")),
        "InjectionTick": _value_or_null(record.get("InjectionTick")),
        "ActivationStatus": _value_or_null(record.get("ActivationStatus")),
        "InjectionCount": _value_or_null(record.get("InjectionCount")),
        # group 3: chain path (explicit NOT_APPLICABLE for absent stages)
        "ChainEventCount": _value_or_null(record.get("ChainEventCount")),
        "ChainEdgeCount": _value_or_null(record.get("ChainEdgeCount")),
        "EarliestAnomalyType": _value_or_na(record.get("EarliestAnomalyType")),
        "EarliestAnomalyEventID": _value_or_na(
            record.get("EarliestAnomalyEventID")),
        "WritebackValueFnv": _value_or_na(writeback_feature),
        "ConsumerInputFnv": _value_or_na(consumer_feature),
        "ConsumerSourceLinked": _value_or_na(
            record.get("ConsumerSourceLinked")
            if present["consumer_commit"] else None),
        "CommitSeq": _value_or_na(commit_feature),
        # group 4: outcome
        "ObservedTerminal": record.get("ObservedTerminal"),
        "TerminalReason": _value_or_na(record.get("TerminalReason")),
        "ApplicationOracle": record.get("ApplicationOracle"),
        "OracleExpected": _value_or_null(record.get("OracleExpected")),
        "OracleActual": _value_or_null(record.get("OracleActual")),
        # group 5: verdict
        "RecordIntegrity": record.get("RecordIntegrity"),
        "TraceCompleteness": record.get("TraceCompleteness"),
        "StructuralChainCompleteness": record.get(
            "StructuralChainCompleteness"),
        "FaultEffectPropagationCoverage": record.get(
            "FaultEffectPropagationCoverage"),
        "FaultCausality": record.get("FaultCausality"),
        "FinalClassification": record.get("FinalClassification"),
        "MissingEvidence": record.get("MissingEvidence"),
    }


def write_feature_dataset(records: list, out) -> None:
    """One row per pilot (RowKind=PILOT) plus one row per verified path
    fragment (RowKind=PATH_FRAGMENT) in canonical chain order; the frozen
    per-pilot EventOrdinal is constant — hence monotonic — on every row of
    the pilot's block, and absent stages are explicit NOT_APPLICABLE."""
    rows = []
    for record in records:
        rows.append(_feature_row(record, "PILOT", 0, None))
        for index, fragment in enumerate(record.get("PathFragments") or [],
                                         start=1):
            rows.append(_feature_row(record, "PATH_FRAGMENT", index,
                                     fragment))
    _write_csv(rows, FEATURE_DATASET_COLUMNS, Path(out))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _load_records(paths) -> list:
    records: list = []
    for path in paths:
        payload = _read_json(Path(path))
        if payload is None:
            raise ValueError(f"records file {path!r} is absent or malformed")
        if isinstance(payload, dict) and isinstance(
                payload.get("records"), list):
            records.extend(payload["records"])
        elif isinstance(payload, list):
            records.extend(payload)
        else:
            raise ValueError(f"records file {path!r} carries no record list")
    if not records:
        raise ValueError("no records supplied")
    return records


def _pilot_model(pilot_dir: Path) -> str | None:
    manifest = _read_json(pilot_dir / "manifest.json")
    if isinstance(manifest, dict):
        model = manifest.get("model_id") or manifest.get("model")
        if model in MODELS:
            return model
    meta = _read_json(pilot_dir / META_NAME)
    if isinstance(meta, dict) and meta.get("model") in MODELS:
        return meta["model"]
    return None


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lsu_12model_closure.py",
        description="Deterministic 12-model propagation closure tool "
                    "(LSU v3.2.12 Task 3).")
    sub = parser.add_subparsers(dest="command", required=True)

    p_record = sub.add_parser(
        "record", help="build the per-pilot closure records for one model")
    p_record.add_argument("--model", required=True,
                          help="fault model id, e.g. LQ04")
    p_record.add_argument("--pilot-dir", action="append", type=Path,
                          required=True, help="pilot dir (repeatable)")
    p_record.add_argument("--json", type=Path, default=None,
                          help="write the records as JSON")
    p_record.add_argument("--binary-sha", default=None,
                          help="expected gem5 binary SHA256 (purity check)")

    p_missing = sub.add_parser(
        "missing", help="write the missing-evidence matrix for pilot roots")
    p_missing.add_argument("--pilots-root", action="append", type=Path,
                           required=True,
                           help="root dir containing pilot dirs "
                                "(repeatable)")
    p_missing.add_argument("--out", type=Path, required=True,
                           help="output CSV path")

    p_matrix = sub.add_parser(
        "matrix", help="write the per-model closure matrix from record JSON")
    p_matrix.add_argument("--records", action="append", type=Path,
                          required=True, help="records JSON (repeatable)")
    p_matrix.add_argument("--out", type=Path, required=True,
                          help="output CSV path")

    p_features = sub.add_parser(
        "features", help="write the diagnostic feature dataset from records")
    p_features.add_argument("--records", action="append", type=Path,
                            required=True, help="records JSON (repeatable)")
    p_features.add_argument("--out", type=Path, required=True,
                            help="output CSV path")

    args = parser.parse_args(argv)

    if args.command == "record":
        records = [build_pilot_record(p, args.model,
                                       binary_sha=args.binary_sha)
                   for p in args.pilot_dir]
        if args.json:
            args.json.write_text(
                json.dumps({"model": args.model, "records": records},
                           indent=2) + "\n", encoding="utf-8")
        print(f"model={args.model} pilots={len(records)}")
        for record in records:
            print(f"  {record['PilotID']}: "
                  f"FinalClassification={record['FinalClassification']} "
                  f"ObservedTerminal={record['ObservedTerminal']} "
                  f"missing=[{record['MissingEvidence']}]")
        return 0

    if args.command == "missing":
        records = []
        for root in args.pilots_root:
            for pilot_dir in sorted(Path(root).iterdir()):
                if not pilot_dir.is_dir():
                    continue
                if not any((pilot_dir / name).is_file() for name in
                           ("pilot_meta.json", "manifest.json",
                            "trace_v31.jsonl")):
                    continue
                model = _pilot_model(pilot_dir)
                if model is None:
                    print(f"  skipping {pilot_dir}: no 12-model id")
                    continue
                records.append(build_pilot_record(pilot_dir, model))
        write_missing_matrix(records, args.out)
        print(f"missing-matrix rows written to {args.out} "
              f"(records={len(records)})")
        return 0

    if args.command == "matrix":
        records = _load_records(args.records)
        write_closure_matrix(records, args.out)
        print(f"closure matrix written to {args.out} "
              f"(records={len(records)})")
        return 0

    if args.command == "features":
        records = _load_records(args.records)
        write_feature_dataset(records, args.out)
        print(f"feature dataset written to {args.out} "
              f"(records={len(records)})")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
