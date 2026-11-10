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
``audit_pilot`` already exports, are pilot sidecars — ``pilot_meta.json``
(run-harness truncation flag / oracle-by-design markers), the
``supplementary.json`` SUPP sidecar, the raw ``stdout.log`` checksum line,
and the RP01 injector sidecar ``lsq_fwd_injections.log`` (the
``CHAOS_RP01_WATCHDOG=EXPIRED`` watchdog record, with the ``stdout.log``
fatal line as its fallback source) — which are records, not traces.

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
3b. exception E1 (standard §6/§10, model-scoped to LQ04): the runtime-proven
   senderState masking chain -> ``COMPLETE_CAUSAL_CHAIN`` with
   ``ObservedTerminal=MASKED`` and
   ``MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE``, even
   though ``FaultEffectPropagationCoverage`` stays ``LIFECYCLE_ONLY``;
3c. exceptions E2/E3/E4 (standard §6 clause 3c / §11, model-scoped to
   SQ01/SQ03/SP05): a runtime-proven model-record chain (the sq01_chain /
   sq03_effect / sp05_stage record on the fault's own chain, with its hop
   hashes / visibility ticks / skip flags) -> a complete verdict following
   the single-context rule (§4): ``VERIFIED_SINGLE_CONTEXT`` per pilot,
   model-level ``COMPLETE_CAUSAL_CHAIN`` with two or more distinct frozen
   contexts, with ``ObservedTerminal=SDC`` (E2 SQ01, E4 SP05) or ``MASKED``
   (E3 SQ03) and the ``ChainMechanism`` of §11 named, even though
   ``FaultEffectPropagationCoverage`` stays ``LIFECYCLE_ONLY``;
3d. exceptions E5/E6/E7 (standard §6 clause 3d / §12, model-scoped terminal
   exceptions, frozen amendment 2026-11-11), evaluated before the rule-1
   integrity gates because each names the integrity state it relaxes:
   E5 RP01 — the watchdog-timed-out skipped-replay load: when the
   ``CHAOS_RP01_WATCHDOG=EXPIRED ... injected=1`` record exists, the
   injection is identity-linked to the skipped load (the replay/skip record
   on the fault's own chain) with ``FaultCausality=PROVEN``, and the partial
   trace is retained, the record grades a complete verdict with
   ``ObservedTerminal=HANG/TIMEOUT`` and
   ``TerminalMechanism=REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT`` even
   though ``RecordIntegrity=TRUNCATED`` and ``TraceCompleteness=INCOMPLETE``
   (both stay what the platform graded); a SQUASHED RP01 run never fires E5
   and stays below a complete verdict unless the squash trigger is
   identity-linked.  E6 A03 — the panic direct address match: when the panic
   page-table fault VA equals the ``actual_ea`` of the on-chain ``a03_stream``
   record of the crash-linked load (``affected=1``, the abort's
   ``last_injection_dyn_seq`` tying the pair) and the F5 activation/stream
   records are present, the record grades a complete verdict with
   ``ObservedTerminal=CRASH`` and
   ``TerminalMechanism=STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH`` even though
   the crash cut the record (``RecordIntegrity=TRUNCATED``).  E7 A01 — the
   wrong-EA delivery chain: when the on-chain ``a01_ea`` record proves a
   wrong EA (``golden_ea != actual_ea``, ``affected=1``) that was delivered
   (an on-chain ``memory_response`` and ``register_writeback``) and consumed
   (the consumer hash equals the writeback hash, and the ``a01_consumed``
   record's input hash matches both) with terminal ``MASKED`` — or the
   terminal is ``CRASH`` with the panic VA equal to the on-chain
   ``a01_ea`` ``actual_ea`` (the direct match) — the record grades a
   complete verdict with
   ``TerminalMechanism=WRONG_EA_LOAD_DELIVERED_AND_CONSUMED``; an A01 record
   whose corrupted EA was discarded before any request (the on-chain
   ``a01_ea_discarded`` record with ``applied_to_request=0``, terminal
   honestly ``UNRESOLVED`` for a missing writeback) grades ``PARTIAL`` —
   real on-chain evidence, the discard naming the missing link — never
   ``UNRESOLVED``;
4. internal-only change -> ``LIFECYCLE_ONLY``;
5. otherwise -> ``PARTIAL`` (with the missing link named).

Complete verdicts obey the single-context rule (standard §4): one verified
complete chain in the pilot's own trace -> ``VERIFIED_SINGLE_CONTEXT``; two
or more -> ``COMPLETE_CAUSAL_CHAIN``.  A verdict is never computed across
binaries: the closure matrix splits per ``BinarySHA256`` and never merges.

Frozen prior-audit import (standard §12.5): the four models the frozen
v3.2.11 audit already verified (DA04/LP01/MD04/FW05) are NOT re-graded by
the generic classifier.  The ``frozen`` subcommand reads a v3.2.11 verdict
JSON, keyed by (model, binary SHA, evidence path) — each pilot record must
carry a 64-hex ``binary_sha`` and a non-empty ``evidence_path``, and the
import refuses a keyed binary the file carries no pilot under — and emits
closure-schema records that carry the prior per-pilot verdicts verbatim
(``FinalClassification`` = the prior classification, ``PriorAudit`` = the
prior-audit tag).  The four v3.2.12 standard fields the prior audit did
not record per pilot (``RecordIntegrity``, ``TraceCompleteness``,
``StructuralChainCompleteness``, ``FaultEffectPropagationCoverage``,
``FaultCausality``) are carried as the literal ``NULL`` — never fabricated,
never re-derived.  ``matrix``/``features`` accept the frozen JSONs via
``--frozen-prior``; a frozen group supersedes the generic records of the
SAME (model, binary) key only (with a loud note) and never touches any other
binary's records.

The missing-evidence matrix closes every ``ORACLE_FILE_MISSING`` row against
the frozen context's real raw-oracle availability, in a fixed standard-derived
precedence (never per-model hand-routing): (1) a Task 5 ``SUPP-<MODEL>-<Rxx>``
raw-oracle run of the same (ModelID, Seed) context remediates the row
(``RequiredRunCount=0``, the SUPP ``oracle.log`` named — it corroborates and
never replaces the original verdict, and the two binaries' verdicts are never
merged); (2) another original vintage of the same context whose raw
``oracle.log`` parsed supplies it in-repo; (3) the pilot's own ``stdout.log``
raw checksum line supplies it in-repo; (4) with no causally attributable
consumer no oracle outcome can adjudicate the verdict (standard sections
1.5/1.7) and the row is decision-moot with ``RequiredRunCount=0``; (5) only
otherwise does the frozen open row stand (``RequiredRunCount=1``).  A 12-model
model with no pilot at all carries its missing pilot set as an explicit row.

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
import re
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

# Standard §6 exception E1 (§10, frozen amendment 2026-11-10): the LQ04
# senderState masking rule.  The researcher brief §八 ruling (binding per the
# v3.2.12 SDD ledger) grades the runtime-proven senderState masking chain
# COMPLETE_CAUSAL_CHAIN with ObservedTerminal=MASKED and the named masking
# mechanism, even though FaultEffectPropagationCoverage stays LIFECYCLE_ONLY
# (the effect itself stayed inside the LQ-entry lifecycle).  The rule is
# model-scoped: it upgrades no other model.
MASKING_MECHANISM_SENDERSTATE = "RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE"
_LQ04_SENDER_STATE = "sender_state"
# hash sentinels that can neither establish continuity nor verify the
# consumer edge (platform _real_hash semantics + this tool's stage literal)
_ABSENT_HASH_SENTINELS = frozenset(("null", "none", "0", "", "not_applicable"))

# Standard §6 clause 3c / §11 (frozen amendment 2026-11-10): exceptions
# E2/E3/E4 — the SQ-family model-record chains.  The v3.2.12 SQ ordinal
# re-selection round proved, 5/5 contexts per model, chains whose every hop
# is a runtime-recorded field of the model's own rule record (sq01_chain /
# sq03_effect / sp05_stage): SQ01's corrupted SQ-entry byte reached memory,
# was reloaded and was consumed (the three-hop hash triple equal); SQ03's
# canWB move drained the store to memory strictly before architectural
# commit with a reload consumer reading it; SP05's skipped store completion
# left the stale word in memory for the reload to read.  The generic
# value_divergence analysis does not bind these model-record hops, so
# coverage honestly stays LIFECYCLE_ONLY — the exceptions stop that value
# from forcing the classification down.  Each rule is a conjunction of
# proven fields only (no upgrade on inference) and is model-scoped.
_SQ_MODEL_RULE_MECHANISMS = {
    "SQ01": "SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER",
    "SQ03": "SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT",
    "SP05": "STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED",
}

# Standard §6 clause 3d / §12 (frozen amendment 2026-11-11): exceptions
# E5/E6/E7 — the model-scoped terminal exceptions.  Each fires on a
# conjunction of proven runtime records only (no upgrade on inference) and
# names the integrity state it relaxes: E5 the TRUNCATED watchdog-fatal
# record with its retained partial trace (TraceCompleteness stays
# INCOMPLETE), E6 the TRUNCATED crash-cut record whose panic VA is
# identity-linked to the on-chain a03_stream actual EA, E7 the wrong-EA
# A01 delivery whose corrupted address reached a delivered, consumed load
# (with the discard context graded PARTIAL, never UNRESOLVED).  The
# TerminalMechanism record field is emitted exactly when the model's
# conjunction holds, NOT_APPLICABLE otherwise (including every other
# model) — computed from the same conjunction final_classification applies.
_TERMINAL_MECHANISMS = {
    "RP01": "REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT",
    "A03": "STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH",
    "A01": "WRONG_EA_LOAD_DELIVERED_AND_CONSUMED",
}

# the frozen prior-audit tag carried by imported records (standard §12.5):
# the four models the frozen v3.2.11 audit verified are not re-graded by
# the generic classifier; their per-pilot verdicts are imported verbatim,
# keyed by (model, binary SHA, evidence path).
FROZEN_PRIOR_AUDIT = "v3.2.11"

# the RP01 injector sidecar carrying the watchdog record (a run-harness
# record, not a trace): the CHAOS_RP01_WATCHDOG=EXPIRED line with its kv
# fields; the stdout.log fatal line is the fallback source.
_RP01_WATCHDOG_LOG = "lsq_fwd_injections.log"
_RP01_WATCHDOG_LINE = "CHAOS_RP01_WATCHDOG"

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
        # exception-E1 evidence (standard §10): how the in-flight response and
        # the writeback were associated to the original request while the LQ
        # entry was visibly invalid.  For LQ04 the early-anomaly stage IS the
        # memory_response (platform EARLY_ANOMALY_KINDS), so the first field
        # below is exactly the association recorded on the chain's
        # memory_response; both come from audit_pilot's evidence export (no
        # independent trace re-parse, no forked classifier).
        "MemoryResponseAssociation": (
            (evidence.get("earliest_anomaly") or {}).get("association")
            if stages["early_anomaly_verified"] == "yes" else "NOT_APPLICABLE"),
        "WritebackAssociation": (
            (evidence.get("writeback") or {}).get("association")
            if stages["register_writeback_verified"] == "yes"
            else "NOT_APPLICABLE"),
        "CommitSeq": (
            (evidence.get("commit") or {}).get("commit_seq")
            if stages["commit_verified"] == "yes"
            else "NOT_APPLICABLE"),
        # exception-E2/E3/E4 evidence (standard §11): the SQ-family model
        # rule record on the fault's own chain (sq01_chain / sq03_effect /
        # sp05_stage), exported verbatim by audit_pilot's evidence bundle
        # (hop hashes, visibility ticks, skip flags) — no independent trace
        # re-parse, no forked classifier
        "ModelRuleRecord": evidence.get("model_rule"),
        # exception-E5/E6/E7 evidence (standard §12): the model's own
        # stream records on the fault's own chain (a01_ea / a01_ea_discarded
        # / a01_consumed / a03_stream, with their detail fields) and the
        # run-level records that carry no chain identity (a03_activation,
        # simulator_abort) — exported verbatim by audit_pilot's evidence
        # bundle, plus the RP01 watchdog record read from the pilot's
        # run-harness sidecars (lsq_fwd_injections.log / stdout.log, which
        # are records, not traces)
        "ModelStreamRecords": evidence.get("model_records") or [],
        "ModelRunRecords": evidence.get("model_run_records") or {},
        "RP01Watchdog": (_rp01_watchdog_record(pilot_dir)
                         if model == "RP01" else None),
        "OracleExpected": audit["oracle"].get("expected"),
        "OracleActual": audit["oracle"].get("actual"),
        "OracleStatus": audit["oracle"].get("status"),
    }
    record["PathFragments"] = _path_fragments(record)
    # standard §10: the exception-E1 record field, computed from the same
    # conjunction that final_classification applies (never hand-set)
    record["MaskingMechanism"] = (
        MASKING_MECHANISM_SENDERSTATE
        if _lq04_sender_state_masking(record) else "NOT_APPLICABLE")
    # standard §11: the exception-E2/E3/E4 record fields, computed from the
    # same conjunction that final_classification applies (never hand-set).
    # A proven model-record chain is one verified complete chain, so the
    # pilot's VerifiedChainCount is at least 1 when the exception fires —
    # §4 then decides VERIFIED_SINGLE_CONTEXT vs COMPLETE_CAUSAL_CHAIN
    # exactly as for every generic complete verdict.
    record["ChainMechanism"] = _sq_model_record_mechanism(record)
    if record["ChainMechanism"] != "NOT_APPLICABLE":
        record["VerifiedChainCount"] = max(int(chains), 1)
    # standard §12: the exception-E5/E6/E7 record field, computed from the
    # same conjunction that final_classification applies (never hand-set).
    # As with E2/E3/E4, a proven terminal exception chain is one verified
    # complete chain, so VerifiedChainCount is at least 1 when it fires and
    # §4 decides the value exactly as for every generic complete verdict;
    # the E7 discard companion carries its PARTIAL grade through the record
    # fields themselves (no mechanism, no complete verdict).
    record["TerminalMechanism"] = _terminal_mechanism(record)
    if record["TerminalMechanism"] != "NOT_APPLICABLE":
        record["VerifiedChainCount"] = max(int(chains), 1)
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

def _lq04_sender_state_masking(record: dict) -> bool:
    """Standard §6 exception E1 (§10): the LQ04 senderState masking rule.

    Fires only when ALL conditions hold (the researcher brief §八 binding
    ruling, frozen as standard §10): the record is LQ04 with terminal MASKED;
    causality is PROVEN over a VALID/COMPLETE record with a structurally
    COMPLETE chain and a verified injection/activation (the §6 invariants
    every complete verdict obeys); the chain evidence carries the senderState
    association on BOTH the memory_response and the register_writeback; and
    the consumer input hash equals the writeback value hash (both real
    hashes).  Model-scoped: no other model is ever upgraded by it, and an
    LQ04 record missing any condition follows the generic §6 rules exactly
    as before (LIFECYCLE_ONLY/PARTIAL) — no upgrade on inference alone.
    """
    def field(name: str) -> str:
        value = record.get(name)
        return str(value).strip().upper() if value is not None else ""

    def detail(name: str) -> str:
        value = record.get(name)
        return str(value).strip().lower() if value is not None else ""

    if field("ModelID") != "LQ04":
        return False  # model-scoped: the exception upgrades no other model
    if field("ObservedTerminal") != "MASKED":
        # E1 names a masking mechanism; it never relabels another terminal
        return False
    if field("FaultCausality") != "PROVEN":
        return False
    if (field("RecordIntegrity") != "VALID"
            or field("TraceCompleteness") != "COMPLETE"
            or field("StructuralChainCompleteness") != "COMPLETE"):
        return False
    if (record.get("InjectionVerified") != "yes"
            or record.get("ActivationVerified") != "yes"):
        # §6 invariant: no complete verdict over unverified/dormant stages
        return False
    if detail("MemoryResponseAssociation") != _LQ04_SENDER_STATE:
        return False  # the response binding is not runtime-proven
    if detail("WritebackAssociation") != _LQ04_SENDER_STATE:
        return False  # the writeback binding is not runtime-proven
    writeback_fnv = detail("WritebackValueFnv")
    if writeback_fnv in _ABSENT_HASH_SENTINELS:
        # an absent hash can neither verify nor fabricate the consumer edge
        return False
    return writeback_fnv == detail("ConsumerInputFnv")


# ---------------------------------------------------------------------------
# standard §6 clause 3c / §11 — exceptions E2/E3/E4, the SQ-family
# model-record chains (frozen amendment 2026-11-10)
# ---------------------------------------------------------------------------

def _sq_field(record: dict, name: str) -> str:
    """A record field as stripped, lower-cased text (the identity-field
    comparison convention of standard §2: trace vintages carry ints or JSON
    strings; hash/flag comparison is str-normalized)."""
    value = record.get(name)
    return "" if value is None else str(value).strip().lower()


def _model_rule_fields(record: dict, kind: str) -> dict:
    """The model rule record of the given kind (standard §11): the
    sq01_chain / sq03_effect / sp05_stage record the injector's rule emitted
    on the fault's own chain, exported verbatim by ``audit_pilot``'s evidence
    bundle (``ModelRuleRecord``).  Empty when the record is absent or of a
    different kind."""
    rule = record.get("ModelRuleRecord")
    if not isinstance(rule, dict) or rule.get("event_type") != kind:
        return {}
    fields = rule.get("fields")
    return fields if isinstance(fields, dict) else {}


def _rule_value(fields: dict, name: str) -> str:
    value = fields.get(name)
    return "" if value is None else str(value).strip().lower()


def _real_rule_hash(fields: dict, name: str) -> str | None:
    """A model-record hash field as a real hash, or None when absent (the
    §3 absent-hash sentinels can neither establish continuity nor verify a
    hop — a sentinel never satisfies an E2/E3/E4 equality)."""
    value = _rule_value(fields, name)
    return None if value in _ABSENT_HASH_SENTINELS else value


def _bound_seq(fields: dict, name: str) -> bool:
    """A model-record sequence binding (reload_seq / consumer_seq) is
    present only as a non-empty, non-sentinel value."""
    return _rule_value(fields, name) not in _ABSENT_HASH_SENTINELS


def _complete_invariants(record: dict) -> bool:
    """The §6 invariant set every complete verdict enforces (identical to
    E1's §10.3 condition 4): a valid, complete record over a structurally
    complete chain with a verified, activated injection and proven
    causality."""
    return (_sq_field(record, "RecordIntegrity") == "valid"
            and _sq_field(record, "TraceCompleteness") == "complete"
            and _sq_field(record, "StructuralChainCompleteness") == "complete"
            and record.get("InjectionVerified") == "yes"
            and record.get("ActivationVerified") == "yes"
            and _sq_field(record, "FaultCausality") == "proven")


def _writeback_consumer_edge_verified(record: dict) -> bool:
    """The platform data rule (§3) on the reload's delivery edge: the
    consumer's input hash equals the writeback's value hash, both real
    hashes.  Shared by E2/E3/E4 as the last conjunct."""
    writeback_fnv = _sq_field(record, "WritebackValueFnv")
    if writeback_fnv in _ABSENT_HASH_SENTINELS:
        return False
    return writeback_fnv == _sq_field(record, "ConsumerInputFnv")


def _sq01_data_corruption_chain(record: dict) -> bool:
    """Standard §11.3 exception E2 — SQ01, mechanism
    SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER.

    Fires only when ALL conditions hold (a conjunction of proven runtime
    fields; no upgrade on inference): an SQ01 record with terminal SDC and
    proven causality over the §6 invariant set, whose sq01_chain rule record
    sits on the fault's own chain and proves the corrupted SQ-entry byte
    reached memory, was reloaded and was consumed — data_diverged=1, a bound
    reload_seq and consumer_seq, the three-hop hash triple
    mem_write_hash == reload_data_hash == consumer_hash over real hashes —
    with the platform data rule verifying the reload's delivery edge."""
    if _sq_field(record, "ModelID") != "sq01":
        return False  # model-scoped: the exception upgrades no other model
    if _sq_field(record, "ObservedTerminal") != "sdc":
        # E2's outcome terminal is the oracle-failing corrupted delivery
        return False
    if not _complete_invariants(record):
        return False
    fields = _model_rule_fields(record, "sq01_chain")
    if not fields:
        return False  # no model rule record on the fault's own chain
    if _rule_value(fields, "data_diverged") != "1":
        return False  # the injected flip never changed the SQ entry byte
    if not (_bound_seq(fields, "reload_seq")
            and _bound_seq(fields, "consumer_seq")):
        return False  # no bound reload / consumer on the model record
    mem_write = _real_rule_hash(fields, "mem_write_hash")
    reload_data = _real_rule_hash(fields, "reload_data_hash")
    consumer = _real_rule_hash(fields, "consumer_hash")
    if not (mem_write and reload_data and consumer):
        return False  # an absent hash can never verify a hop
    if not (mem_write == reload_data == consumer):
        return False  # the three hops are not hash-equal
    return _writeback_consumer_edge_verified(record)


def _sq03_visibility_moved_chain(record: dict) -> bool:
    """Standard §11.3 exception E3 — SQ03, mechanism
    SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT.

    Fires only when ALL conditions hold: an SQ03 record with terminal MASKED
    (correct payload, oracle PASS — the effect is the visibility violation)
    and proven causality over the §6 invariant set, whose sq03_effect rule
    record sits on the fault's own chain and proves the canWB move made the
    store visible before architectural commit — canwb_state_changed=1,
    drain_tick and commit_tick both > 0 with drain_tick < commit_tick,
    visible_before_commit=1 — with a bound reload (reload_seq present,
    reload_data_hash real) and the platform data rule verifying the reload's
    delivery edge."""
    if _sq_field(record, "ModelID") != "sq03":
        return False  # model-scoped: the exception upgrades no other model
    if _sq_field(record, "ObservedTerminal") != "masked":
        # E3 never relabels an SDC/CRASH/HANG/SQUASHED record; the effect
        # it names is a visibility move of a correct payload
        return False
    if not _complete_invariants(record):
        return False
    fields = _model_rule_fields(record, "sq03_effect")
    if not fields:
        return False  # no model rule record on the fault's own chain
    if _rule_value(fields, "canwb_state_changed") != "1":
        return False  # the fault never moved the canWB bit
    try:
        drain_tick = int(_rule_value(fields, "drain_tick"))
        commit_tick = int(_rule_value(fields, "commit_tick"))
    except ValueError:
        return False  # the visibility ticks are not both numeric
    if drain_tick <= 0 or commit_tick <= 0:
        return False  # a zero tick records "not observed", never a proof
    if not drain_tick < commit_tick:
        return False  # the drain did not precede architectural commit
    if _rule_value(fields, "visible_before_commit") != "1":
        return False
    if not _bound_seq(fields, "reload_seq"):
        return False  # no bound reload on the model record
    if _real_rule_hash(fields, "reload_data_hash") is None:
        return False  # the reload's data hash is absent
    return _writeback_consumer_edge_verified(record)


def _sp05_store_skipped_chain(record: dict) -> bool:
    """Standard §11.3 exception E4 — SP05, mechanism
    STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED.

    Fires only when ALL conditions hold: an SP05 record with terminal SDC
    and proven causality over the §6 invariant set, whose sp05_stage rule
    record sits on the fault's own chain and proves the premature completion
    skipped the store write (write_skipped=1) and a reload then read the
    word memory still held (reload_seq present, reload_data_hash a real
    hash) — with the platform data rule verifying the reload's delivery
    edge.  store_data_fnv is honestly null in this binary (the field's
    wiring is unimplemented) and is deliberately NOT a condition: E4 never
    claims the store-side data question was answered, only that the write
    was skipped and the reload read something that failed the oracle."""
    if _sq_field(record, "ModelID") != "sp05":
        return False  # model-scoped: the exception upgrades no other model
    if _sq_field(record, "ObservedTerminal") != "sdc":
        # E4's outcome terminal is the oracle-failing stale delivery
        return False
    if not _complete_invariants(record):
        return False
    fields = _model_rule_fields(record, "sp05_stage")
    if not fields:
        return False  # no model rule record on the fault's own chain
    if _rule_value(fields, "write_skipped") != "1":
        return False  # the store write was not skipped
    if not _bound_seq(fields, "reload_seq"):
        return False  # no bound reload on the model record
    if _real_rule_hash(fields, "reload_data_hash") is None:
        return False  # the reload read nothing the rule could hash
    return _writeback_consumer_edge_verified(record)


def _sq_model_record_mechanism(record: dict) -> str:
    """The §11 ChainMechanism value for the record: the model's mechanism
    name exactly when its E2/E3/E4 conjunction holds, NOT_APPLICABLE
    otherwise (including every non-SQ-family record).  Computed from the
    same conjunction ``final_classification`` applies — never hand-set."""
    if _sq01_data_corruption_chain(record):
        return _SQ_MODEL_RULE_MECHANISMS["SQ01"]
    if _sq03_visibility_moved_chain(record):
        return _SQ_MODEL_RULE_MECHANISMS["SQ03"]
    if _sp05_store_skipped_chain(record):
        return _SQ_MODEL_RULE_MECHANISMS["SP05"]
    return "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# standard §6 clause 3d / §12 — exceptions E5/E6/E7, the model-scoped
# terminal exceptions (frozen amendment 2026-11-11)
# ---------------------------------------------------------------------------

def _norm_addr(value) -> str:
    """An address as bare lowercase hex (``0xFFFF...`` -> ``ffff...``);
    never zero-stripped, so a panic VA of 0 never equals a real EA."""
    text = "" if value is None else str(value).strip().lower()
    if text.startswith("0x"):
        text = text[2:]
    return text


def _stream_records(record: dict, kind: str) -> list[dict]:
    """The model's own on-chain stream records of the given kind (standard
    §12), exported verbatim by ``audit_pilot`` (``ModelStreamRecords``):
    a01_ea / a01_ea_discarded / a01_consumed / a03_stream with their detail
    fields — the runtime address evidence."""
    out = []
    for item in record.get("ModelStreamRecords") or []:
        if (isinstance(item, dict) and item.get("event_type") == kind
                and isinstance(item.get("fields"), dict)):
            out.append(item)
    return out


def _run_record_fields(record: dict, kind: str) -> dict:
    """The model's run-level record of the given kind (standard §12),
    exported verbatim by ``audit_pilot`` (``ModelRunRecords``): the
    a03_activation F5 record and the simulator_abort panic-VA node, which
    carry no chain identity.  Empty when the record is absent."""
    item = (record.get("ModelRunRecords") or {}).get(kind)
    if (isinstance(item, dict) and isinstance(item.get("fields"), dict)):
        return item["fields"]
    return {}


def _rp01_watchdog_record(pilot_dir: Path) -> dict | None:
    """The RP01 watchdog record from the pilot's run-harness sidecars
    (standard §12, exception E5): the ``CHAOS_RP01_WATCHDOG=EXPIRED`` line
    of the injector sidecar ``lsq_fwd_injections.log`` — the ``stdout.log``
    ``fatal: CHAOS_RP01_WATCHDOG_EXPIRED`` line is the fallback source.
    Both are run records, not traces; every field is taken from the line and
    the raw line itself is carried as provenance.  ``None`` when no expired
    line exists (a completed/SQUASHED run, or a control with no injector)."""
    pilot_dir = Path(pilot_dir)
    for name in (_RP01_WATCHDOG_LOG, "stdout.log"):
        path = pilot_dir / name
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            if _RP01_WATCHDOG_LINE not in line or "EXPIRED" not in line:
                continue
            kv = dict(token.split("=", 1) for token in line.split()
                      if "=" in token)
            return {"source": name,
                    "line": line.strip(),
                    "expired": True,
                    "fired": kv.get("fired"),
                    "injected": kv.get("injected"),
                    "eligible": kv.get("eligible"),
                    "tick": kv.get("tick")}
    return None


def _rp01_watchdog_timeout(record: dict) -> bool:
    """Standard §6 exception E5 (§12) — RP01, mechanism
    REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT.

    Fires only when ALL conditions hold (a conjunction of proven runtime
    records; no upgrade on inference): an RP01 record whose observed
    terminal is HANG or TIMEOUT, over a verified/activated injection whose
    causality is PROVEN through the identity-linked replay/skip record on
    the fault's own chain (the skipped load the trigger suppression left
    un-replayed), with the run-harness ``CHAOS_RP01_WATCHDOG=EXPIRED
    injected=1`` record present and the partial trace retained (real chain
    events survived the fatal cut).  The exception relaxes exactly the
    integrity states it names: the record grades a complete verdict even
    though ``RecordIntegrity=TRUNCATED`` and ``TraceCompleteness=INCOMPLETE``
    — both fields keep their honest platform values.  A SQUASHED RP01 run
    never fires E5 (an unproven squash stays below a complete verdict unless
    its trigger is identity-linked, the frozen v3.2.11 line)."""
    if _sq_field(record, "ModelID") != "rp01":
        return False  # model-scoped: the exception upgrades no other model
    if _sq_field(record, "ObservedTerminal") not in ("hang", "timeout"):
        return False  # E5 names the watchdog-timeout terminals only
    if (record.get("InjectionVerified") != "yes"
            or record.get("ActivationVerified") != "yes"):
        return False  # the skipped-replay injection must be the record's own
    if _sq_field(record, "FaultCausality") != "proven":
        # the hang must be proven fault-caused: the identity-linked replay
        # marker on the fault's own chain (the §2 identity rules) is what
        # proves the trigger; without it rule 5 caps the record at PARTIAL
        return False
    kinds = {str(kind).strip().lower()
             for kind in (record.get("ChainKinds") or [])}
    if not kinds & {"replay", "rp01_skip"}:
        return False  # no skip/replay record identity-links the hang
    watchdog = record.get("RP01Watchdog")
    if not isinstance(watchdog, dict) or not watchdog.get("expired"):
        return False  # the watchdog EXPIRED line is absent
    if str(watchdog.get("injected") or "") != "1":
        return False  # the timeout did not fire on the injected run
    if _sq_field(record, "RecordIntegrity") == "invalid":
        # only the TRUNCATED shape is excepted: a malformed stream is
        # unusable as evidence, and a cleanly closed trace needs no
        # exception (generic rule 2 already grades it)
        return False
    # the partial trace is retained: chain events survived the fatal cut
    return int(record.get("ChainEventCount") or 0) >= 1


def _a03_panic_direct_match(record: dict) -> bool:
    """Standard §6 exception E6 (§12) — A03, mechanism
    STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH.

    Fires only when ALL conditions hold: an A03 record whose observed
    terminal is CRASH, over a verified/activated injection, whose run
    carries the F5 activation record (a03_activation) and whose fault's own
    chain carries at least one a03_stream record, and whose simulator_abort
    node records a panic page-table fault VA that equals the ``actual_ea``
    of an on-chain a03_stream record of the crash-linked load (``affected=1``,
    and the abort's ``last_injection_dyn_seq`` equals that record's
    ``dyn_inst_seq`` — the DIRECT_ADDRESS_MATCH, identity-linked through the
    §2 rules because the stream record sits on the fault's own chain).  The
    exception relaxes exactly the integrity state it names: the crash-cut
    record (``RecordIntegrity=TRUNCATED``, structural chain PARTIAL because
    the panic terminated the run) no longer forces UNRESOLVED when the
    address match is identity-linked; an INVALID stream is still refused."""
    if _sq_field(record, "ModelID") != "a03":
        return False  # model-scoped: the exception upgrades no other model
    if _sq_field(record, "ObservedTerminal") != "crash":
        return False  # E6 names the crash terminal only
    if (record.get("InjectionVerified") != "yes"
            or record.get("ActivationVerified") != "yes"):
        return False
    if not _run_record_fields(record, "a03_activation"):
        return False  # the F5 activation record is absent
    streams = _stream_records(record, "a03_stream")
    if not streams:
        return False  # the F5 stream is absent from the fault's own chain
    abort = _run_record_fields(record, "simulator_abort")
    panic = _norm_addr(abort.get("page_table_fault_addr"))
    if not panic or panic in _ABSENT_HASH_SENTINELS:
        return False  # no panic VA is recorded
    if _sq_field(record, "RecordIntegrity") == "invalid":
        return False  # only the TRUNCATED crash cut is excepted
    crash_seq = _rule_value(abort, "last_injection_dyn_seq")
    for stream in streams:
        fields = stream["fields"]
        if _rule_value(fields, "affected") != "1":
            continue  # the F5 fault was not applied on this load
        if _norm_addr(fields.get("actual_ea")) != panic:
            continue  # not a direct address match
        if crash_seq and str(stream.get("dyn_inst_seq") or "") != crash_seq:
            continue  # the abort does not name this load: not identity-linked
        return True
    return False


def _a01_wrong_ea_chain(record: dict) -> bool:
    """Standard §6 exception E7 (§12) — A01, mechanism
    WRONG_EA_LOAD_DELIVERED_AND_CONSUMED.

    Fires only when ALL conditions hold (the wrong-EA chain): an A01 record
    over a verified/activated injection whose fault's own chain carries the
    a01_ea record proving a wrong EA (``golden_ea != actual_ea``,
    ``affected=1``), and either

    - the terminal is MASKED and the wrong EA was delivered and consumed: an
      on-chain memory_response, a verified register_writeback, the consumer
      input hash equal to the writeback value hash (the §3 platform data
      rule, both real hashes), and the a01_consumed model record whose
      input_hash equals that same writeback hash (the runtime record of the
      consumed wrong-EA value); or
    - the terminal is CRASH with a direct match: the panic page-table fault
      VA equals the on-chain a01_ea ``actual_ea`` (the crash-cut shape,
      ``RecordIntegrity=TRUNCATED`` accepted, INVALID refused).

    The MASKED branch additionally enforces the §6 invariant set (VALID,
    COMPLETE, structurally COMPLETE, causality PROVEN) exactly like E1/E2;
    a temporal-association-only crash (panic VA 0 / off the fault's EA)
    never fires E7 and stays UNRESOLVED under the generic rules."""
    if _sq_field(record, "ModelID") != "a01":
        return False  # model-scoped: the exception upgrades no other model
    terminal = _sq_field(record, "ObservedTerminal")
    if terminal not in ("masked", "crash"):
        return False  # E7 names the masked wrong-EA chain or the direct crash
    if (record.get("InjectionVerified") != "yes"
            or record.get("ActivationVerified") != "yes"):
        return False
    ea_records = _stream_records(record, "a01_ea")
    if not ea_records:
        return False  # no a01_ea record on the fault's own chain
    fields = ea_records[0]["fields"]
    golden = _norm_addr(fields.get("golden_ea"))
    actual = _norm_addr(fields.get("actual_ea"))
    if (not golden or not actual or golden == actual
            or golden in _ABSENT_HASH_SENTINELS
            or actual in _ABSENT_HASH_SENTINELS):
        return False  # the EA pair does not prove a wrong EA
    if _rule_value(fields, "affected") != "1":
        return False  # the fault was not applied on this load
    if terminal == "crash":
        if _sq_field(record, "RecordIntegrity") == "invalid":
            return False  # only the TRUNCATED crash cut is excepted
        abort = _run_record_fields(record, "simulator_abort")
        panic = _norm_addr(abort.get("page_table_fault_addr"))
        if not panic or panic in _ABSENT_HASH_SENTINELS:
            return False
        return panic == actual  # the direct match; TEMPORAL_ASSOCIATION_ONLY
    # the MASKED branch: the wrong EA was delivered, written back, consumed
    # and committed while the application oracle passed
    if not _complete_invariants(record):
        return False  # the §6 invariant set every complete verdict enforces
    if "memory_response" not in {str(kind).strip().lower() for kind in
                                 (record.get("ChainKinds") or [])}:
        return False  # no delivered response on the fault's own chain
    if record.get("Stages", {}).get("register_writeback_verified") != "yes":
        return False  # no register writeback on the fault's own chain
    if not _writeback_consumer_edge_verified(record):
        return False  # the §3 data rule failed on the consumer edge
    consumed = _stream_records(record, "a01_consumed")
    if not consumed:
        return False  # no runtime record of the consumed wrong-EA value
    writeback_fnv = _sq_field(record, "WritebackValueFnv")
    for item in consumed:
        input_hash = _rule_value(item["fields"], "input_hash")
        if input_hash and input_hash not in _ABSENT_HASH_SENTINELS \
                and input_hash == writeback_fnv:
            return True
    return False


def _a01_discarded_partial(record: dict) -> bool:
    """Standard §6 exception E7's discard companion (§12): an A01 record
    whose fault's own chain carries the ``a01_ea_discarded`` record with
    ``applied_to_request=0`` — the runtime proof that the corrupted EA never
    reached a Request (the saved request was reused, so the load executed
    on the golden EA) — while the terminal is honestly UNRESOLVED (no
    register-writeback evidence exists for a value that was never
    delivered).  Real on-chain evidence exists but no complete chain can be
    verified and the discard record names exactly the missing link, so the
    record grades PARTIAL (§1.8), never UNRESOLVED.  Model-scoped and gated
    on a verified, activated injection; a discard record on a non-A01
    chain never fires it."""
    if _sq_field(record, "ModelID") != "a01":
        return False
    if _sq_field(record, "ObservedTerminal") != "unresolved":
        # only the rule-1 UNRESOLVED cap is relaxed; every other terminal
        # keeps the generic rules
        return False
    if (record.get("InjectionVerified") != "yes"
            or record.get("ActivationVerified") != "yes"):
        return False  # a zero-injection record is never upgraded
    for item in _stream_records(record, "a01_ea_discarded"):
        if _rule_value(item["fields"], "applied_to_request") == "0":
            return True
    return False


def _terminal_mechanism(record: dict) -> str:
    """The §12 TerminalMechanism value for the record: the model's mechanism
    name exactly when its E5/E6/E7 conjunction holds, NOT_APPLICABLE
    otherwise (including every other model and the E7 discard companion,
    whose PARTIAL grade is carried by the record fields themselves).
    Computed from the same conjunction ``final_classification`` applies —
    never hand-set."""
    if _rp01_watchdog_timeout(record):
        return _TERMINAL_MECHANISMS["RP01"]
    if _a03_panic_direct_match(record):
        return _TERMINAL_MECHANISMS["A03"]
    if _a01_wrong_ea_chain(record):
        return _TERMINAL_MECHANISMS["A01"]
    return "NOT_APPLICABLE"


def final_classification(record: dict) -> str:
    """Apply the frozen five-rule order; the first rule that fires decides.

    Exception E1 (standard §6 clause 3b / §10, frozen amendment 2026-11-10)
    sits between rules 3 and 4 and is model-scoped to the runtime-proven
    LQ04 senderState masking chain (``_lq04_sender_state_masking``).
    Exceptions E2/E3/E4 (standard §6 clause 3c / §11, frozen amendment
    2026-11-10) sit at the same layer, immediately after E1, and are
    model-scoped to the runtime-proven SQ-family model-record chains
    (``_sq_model_record_mechanism``).  Exceptions E5/E6/E7 (standard §6
    clause 3d / §12, frozen amendment 2026-11-11) are the model-scoped
    terminal exceptions; they are evaluated BEFORE the rule-1 integrity
    gates because each names the integrity state it relaxes (E5 the
    TRUNCATED watchdog-fatal record with its retained partial trace; E6
    the TRUNCATED crash-cut record with the identity-linked panic-VA
    direct match; E7's discard companion the on-chain a01_ea_discarded
    record that names the missing link of an honestly-UNRESOLVED
    terminal).  Each exception's conjunction is self-gating on a verified,
    activated injection with real on-chain records, so none can fire on a
    NO_INJECTION record.  Every other record — and every RP01/A03/A01
    record missing any of its §12 conditions — follows the generic rules
    unchanged."""
    def field(name: str) -> str:
        value = record.get(name)
        return str(value).upper() if value is not None else ""

    terminal = field("ObservedTerminal")

    injection_ok = record.get("InjectionVerified") == "yes"
    activation_ok = record.get("ActivationVerified") == "yes"
    proven = field("FaultCausality") == "PROVEN"
    struct_complete = field("StructuralChainCompleteness") == "COMPLETE"
    integrity_ok = (field("RecordIntegrity") == "VALID"
                    and field("TraceCompleteness") == "COMPLETE")
    chains = int(record.get("VerifiedChainCount") or 0)
    complete = ("COMPLETE_CAUSAL_CHAIN" if chains >= 2
               else "VERIFIED_SINGLE_CONTEXT")

    # exceptions E5/E6/E7 (standard §6 clause 3d / §12, frozen amendment
    # 2026-11-11), ahead of the rule-1 gates: each conjunction is a set of
    # proven runtime records over a verified, activated injection, and each
    # names the integrity state it relaxes — no upgrade on inference alone
    if _rp01_watchdog_timeout(record):
        # E5 RP01: the watchdog-timed-out skipped-replay load.  The record
        # grades a complete verdict (§4 decides the value: one verified
        # chain -> VERIFIED_SINGLE_CONTEXT; the model-level row upgrades
        # with two or more distinct frozen contexts) with
        # ObservedTerminal=HANG/TIMEOUT and
        # TerminalMechanism=REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT,
        # even though RecordIntegrity=TRUNCATED and TraceCompleteness stays
        # INCOMPLETE (both fields keep their honest platform values).
        return complete
    if _a03_panic_direct_match(record):
        # E6 A03: the panic VA equals the on-chain a03_stream actual_ea of
        # the crash-linked, F5-affected load — the identity-linked
        # DIRECT_ADDRESS_MATCH.  The TRUNCATED crash-cut record no longer
        # forces UNRESOLVED; §4 decides the value as for every complete
        # verdict, with ObservedTerminal=CRASH and
        # TerminalMechanism=STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH.
        return complete
    if _a01_wrong_ea_chain(record):
        # E7 A01: the wrong-EA delivery chain (a01_ea golden != actual,
        # affected=1, delivered through an on-chain response and
        # register_writeback, consumed with the hash-equal a01_consumed
        # record, terminal MASKED; or a CRASH with the panic VA equal to
        # the on-chain actual_ea).  §4 decides the value as for every
        # complete verdict, with
        # TerminalMechanism=WRONG_EA_LOAD_DELIVERED_AND_CONSUMED.
        return complete
    if _a01_discarded_partial(record):
        # E7's discard companion: the on-chain a01_ea_discarded record
        # (applied_to_request=0) proves the corrupted EA never reached a
        # Request — real on-chain evidence, the discard naming the missing
        # link — so the honestly-UNRESOLVED terminal grades PARTIAL, never
        # UNRESOLVED and never a complete verdict.
        return "PARTIAL"

    if terminal in ("NO_INJECTION", "INCOMPLETE", "UNRESOLVED"):
        return "UNRESOLVED"  # rule 1: a missing injection is never a terminal
    if field("RecordIntegrity") in ("INVALID", "TRUNCATED"):
        return "UNRESOLVED"
    if field("TraceCompleteness") in ("MISSING", "INCOMPLETE"):
        return "UNRESOLVED"
    if field("StructuralChainCompleteness") == "NONE":
        return "UNRESOLVED"

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
    if _lq04_sender_state_masking(record):
        # exception E1 (standard §6 clause 3b / §10, frozen amendment
        # 2026-11-10): the runtime-proven LQ04 senderState masking chain.
        # FaultEffectPropagationCoverage stays LIFECYCLE_ONLY — the effect
        # stayed inside the LQ-entry lifecycle — but per the researcher §八
        # binding ruling it no longer forces the classification down: the
        # chain that delivered the intact payload and produced the MASKED
        # terminal is complete, identity- and hash-verified, so the record
        # grades COMPLETE_CAUSAL_CHAIN and carries
        # MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE.
        return "COMPLETE_CAUSAL_CHAIN"
    if _sq_model_record_mechanism(record) != "NOT_APPLICABLE":
        # exceptions E2/E3/E4 (standard §6 clause 3c / §11, frozen
        # amendment 2026-11-10): the runtime-proven SQ-family model-record
        # chain (SQ01 data corruption reaching a reload consumer; SQ03
        # canWB visibility moved before commit with a reload consumer;
        # SP05 skipped store completion with a stale reload consumed).
        # FaultEffectPropagationCoverage stays LIFECYCLE_ONLY — the generic
        # value_divergence analysis does not bind the model-record hops —
        # but per the §11 conjunction it no longer forces the
        # classification down.  Unlike E1 there is no per-record authority
        # bypassing the context count: §4 applies unchanged, so the verdict
        # is `complete` (one verified model-record chain per pilot ->
        # VERIFIED_SINGLE_CONTEXT; two or more distinct frozen contexts ->
        # COMPLETE_CAUSAL_CHAIN at model level).
        return complete
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

# a pilot's own stdout.log is a raw application-oracle artifact when it carries
# the workload's checksum line (the raw source the v3.2.11 audit read for
# FW05/SQ01/SQ03; the schema names "raw oracle.log/stdout.log" as the
# ApplicationOracle artifact -- the audit tool itself parses only oracle.log)
_STDOUT_CHECKSUM_RE = re.compile(
    r"checksum\s*=\s*0x[0-9a-fA-F]+|expected\s*=\s*\S+\s+got\s*=\s*\S+")


def _supp_index(records: list) -> dict:
    """(ModelID, Seed) -> the SUPP record that re-ran that frozen context.

    The v3.2.12 Task 5 raw-oracle runs are named ``SUPP-<MODEL>-<Rxx>``
    (schema section 3) and reuse the original Excel seed, so the
    (ModelID, Seed) pair is the frozen-context join the SUPPLEMENTARY_ORACLE
    manifest records.  A SUPP run corroborates the raw oracle and never
    replaces the original verdict, and it never merges binaries.  Only a SUPP
    record whose own raw artifact parsed (ApplicationOracle PASS/FAIL)
    supplies anything."""
    index: dict = {}
    for record in records:
        if not str(record.get("PilotID") or "").startswith("SUPP-"):
            continue
        if record.get("ApplicationOracle") not in ("PASS", "FAIL"):
            continue
        key = (str(record.get("ModelID")), str(record.get("Seed")))
        index.setdefault(key, record)
    return index


def _raw_oracle_index(records: list) -> dict:
    """(ModelID, Seed) -> a non-SUPP, non-control record whose own raw
    ``oracle.log`` parsed (ApplicationOracle PASS/FAIL): the raw artifact for
    that frozen context exists in-repo at that vintage's dir (e.g. the v3.2.7
    MD04 fault-run vintage supplies the v3.2.6 contexts' raw oracle; seeds
    verified equal).  A determinism control is a zero-injection replication:
    its golden-checksum artifact is never the fault run's raw oracle."""
    index: dict = {}
    for record in records:
        pilot_id = str(record.get("PilotID") or "")
        if pilot_id.startswith("SUPP-") or "CONTROL" in pilot_id.upper():
            continue
        if record.get("ApplicationOracle") not in ("PASS", "FAIL"):
            continue
        key = (str(record.get("ModelID")), str(record.get("Seed")))
        index.setdefault(key, record)
    return index


def _stdout_oracle_path(record: dict) -> str | None:
    """The pilot's own stdout.log carrying the raw application checksum, or
    ``None``.  Read as a record artifact (the same class as
    pilot_meta.json), never as an independent trace re-parse."""
    evidence = str(record.get("EvidencePath") or "")
    if not evidence:
        return None
    path = Path(evidence) / "stdout.log"
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    return str(path) if _STDOUT_CHECKSUM_RE.search(text) else None


def _oracle_missing_row(record: dict, spec: dict, supp: dict,
                        raws: dict) -> dict:
    """The ORACLE_FILE_MISSING row, closed against the frozen context's real
    raw-oracle availability (standard section 1.7: ApplicationOracle
    ``MISSING`` is a raw-artifact-level state, closed by SUPP raw-oracle runs
    which corroborate and never replace the original verdict).

    Fixed precedence, all standard-derived (never per-model hand-routing):

    1. a Task 5 SUPP raw-oracle run of the same (ModelID, Seed) context ->
       remediated, RequiredRunCount=0, the SUPP oracle.log named;
    2. another original vintage of the same context whose raw oracle.log
       parsed (PASS/FAIL) -> supplied in-repo, RequiredRunCount=0;
    3. the pilot's own stdout.log raw checksum line -> supplied in-repo,
       RequiredRunCount=0;
    4. no causally attributable consumer exists (a passing oracle never
       relabels a terminal, a failing oracle is not SDC without a consumer --
       standard sections 1.5/1.7) -> decision-moot: no oracle outcome can
       adjudicate this pilot's verdict, RequiredRunCount=0;
    5. otherwise the frozen open row: RequiredRunCount=1, a SUPP run under
       the original seed and context is what closes it.
    """
    base = {
        "ModelID": record.get("ModelID"),
        "PilotID": record.get("PilotID"),
        "MissingStage": spec["stage"],
        "MissingEvent": spec["event"],
        "MissingCausalEdge": spec["edge"],
        "RequiredHook": spec["hook"],
        "RequiredWorkloadChange": spec["workload"],
    }
    key = (str(record.get("ModelID")), str(record.get("Seed")))

    supplier = supp.get(key)
    if supplier is not None:
        return {**base,
                "RootCause": "the raw oracle artifact is absent from the "
                             "original pilot dir; remediated by the v3.2.12 "
                             f"SUPP raw-oracle run {supplier.get('PilotID')} "
                             "under the original seed and frozen context "
                             "(corroborates, never replaces the original "
                             "verdict; a different binary, the two binaries' "
                             "verdicts are never merged)",
                "RequiredRunCount": "0",
                "ExpectedEvidence": "supplied: "
                                    f"{supplier.get('EvidencePath')}"
                                    "/oracle.log"}

    supplier = raws.get(key)
    if supplier is not None:
        # the supplier is never the record itself: a record carrying
        # ORACLE_FILE_MISSING never has a parsed raw artifact (ApplicationOracle
        # PASS/FAIL requires a parseable oracle.log), so this is always
        # another vintage of the same frozen context
        return {**base,
                "RootCause": "the raw oracle artifact is absent from this "
                             "vintage's dir; supplied in-repo by the "
                             "same-context original vintage "
                             f"{supplier.get('PilotID')} (same model, seed "
                             "and frozen context) whose raw oracle.log "
                             "parsed",
                "RequiredRunCount": "0",
                "ExpectedEvidence": "supplied: "
                                    f"{supplier.get('EvidencePath')}"
                                    "/oracle.log"}

    stdout_path = _stdout_oracle_path(record)
    if stdout_path is not None:
        return {**base,
                "RootCause": "the raw oracle artifact is absent as "
                             "oracle.log, but the pilot's own stdout.log "
                             "records the raw application checksum (the raw "
                             "artifact the v3.2.11 audit read; the audit "
                             "tool parses only oracle.log)",
                "RequiredRunCount": "0",
                "ExpectedEvidence": f"supplied: {stdout_path}"}

    stages = record.get("Stages") or {}
    if stages.get("consumer_verified") != "yes":
        others = ";".join(code for code in record.get("MissingCodes") or []
                         if code != "ORACLE_FILE_MISSING") or "none"
        return {**base,
                "RootCause": "decision-moot: the raw artifact is absent and "
                             "no same-context supply exists, but no oracle "
                             "outcome can adjudicate this pilot's verdict "
                             "(no causally attributable consumer: a passing "
                             "oracle never relabels a terminal and a failing "
                             "oracle is not SDC without a consumer, standard "
                             "sections 1.5/1.7); the decision-relevant gaps "
                             f"are this pilot's other rows: {others}",
                "RequiredRunCount": "0",
                "ExpectedEvidence": "NOT_APPLICABLE (no run is required for "
                                    "the oracle item; close the named stage "
                                    "gaps instead)"}

    return {**base,
            "RootCause": spec["cause"],
            "RequiredRunCount": str(int(spec["runs"])),
            "ExpectedEvidence": spec["expected"]}


def _model_pilot_set_row(model: str) -> dict:
    """The missing pilot-set row for a 12-model closure model that has no
    pilot at all under the supplied roots: the absence of the model's whole
    pilot set is itself a missing-evidence item (never a silent zero)."""
    return {
        "ModelID": model,
        "PilotID": "NONE",
        "MissingStage": "PILOT",
        "MissingEvent": "the model's pilot directory set",
        "MissingCausalEdge": "NOT_APPLICABLE",
        "RootCause": "no pilot directory for this model exists under the "
                     "supplied roots; the model's pilots have not been "
                     "produced (or their run artifacts were archived only "
                     "as extracted evidence rows and never committed as "
                     "pilot directories)",
        "RequiredHook": "the model's injector and trace stage (the missing "
                        "stage rows of the produced pilots will name the "
                        "exact hooks)",
        "RequiredWorkloadChange": "the model's consumer workload where its "
                                   "fault definition requires one (the "
                                   "same-address reload for store-side "
                                   "models)",
        "RequiredRunCount": "5",
        "ExpectedEvidence": "five pilot dirs (R01-R05) under the model's "
                            "frozen seeds, each with trace_v31.jsonl and a "
                            "raw oracle artifact (oracle.log or the "
                            "stdout.log checksum line)",
    }


def write_missing_matrix(records: list, out) -> None:
    """One row per missing item: every missing stage carries a root cause and
    an integer run count; no cell is ever blank."""
    rows = []
    supp = _supp_index(records)
    raws = _raw_oracle_index(records)
    for record in records:
        for code in record.get("MissingCodes") or []:
            spec = _MISSING_ROW_SPEC.get(code, _GENERIC_ROW_SPEC)
            runs = spec["runs"]
            if code == "ORACLE_FILE_MISSING":
                rows.append(_oracle_missing_row(record, spec, supp, raws))
                continue
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
    # a 12-model closure model with no pilot at all carries its missing pilot
    # set as an explicit row (never a silent "nothing to report" zero)
    present = {str(record.get("ModelID")) for record in records}
    for model in MODELS:
        if model not in present:
            rows.append(_model_pilot_set_row(model))
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

def _validate_record(record: dict) -> None:
    """Hard invariants (schema §2), shared by every verdict-bearing writer
    (the closure matrix and the feature dataset): a complete verdict over an
    unverified injection or a dormant activation is a defect and must be
    rejected loudly."""
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
        _validate_record(record)
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
    # DISTINCT frozen contexts with a verified complete chain ->
    # COMPLETE_CAUSAL_CHAIN.  The context key is the original SampleRunID
    # (SupplementaryOf or SampleRunID), so the same pilot supplied twice and
    # an original plus its SUPP re-run of the same frozen context are ONE
    # context; SUPP records (SupplementaryOf present) are excluded from the
    # corroboration count altogether — a SUPP run corroborates the oracle,
    # never a second context.  One context never grades
    # COMPLETE_CAUSAL_CHAIN.
    complete_contexts = set()
    for complete in complete_records:
        if complete.get("SupplementaryOf"):
            continue
        complete_contexts.add(complete.get("SupplementaryOf")
                              or complete.get("SampleRunID"))
    upgrade = len(complete_contexts) >= 2
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
# the frozen prior-audit import (standard §12.5)
# ---------------------------------------------------------------------------

# the four v3.2.12 standard fields the v3.2.11 per-pilot verdicts did not
# record (the prior audit predates the eight-field schema §1).  Carried as
# the literal NULL — never fabricated, never re-derived: re-grading them
# with the generic classifier is exactly what the import exists to avoid.
_PRIOR_AUDIT_UNRECORDED_FIELDS = ("RecordIntegrity", "TraceCompleteness",
                                  "StructuralChainCompleteness",
                                  "FaultEffectPropagationCoverage",
                                  "FaultCausality")


def build_frozen_records(prior_path, model: str | None = None,
                         binary_sha: str | None = None) -> list:
    """Import the frozen v3.2.11 prior audit's per-pilot verdicts as closure
    records (standard §12.5), keyed by (model, binary SHA, evidence path).

    The four models the prior audit already verified (DA04/LP01/MD04/FW05)
    are not re-graded by the generic classifier: every imported record
    carries the prior verdict verbatim — ``FinalClassification`` IS the
    prior ``classification``, ``ObservedTerminal`` the prior ``terminal``,
    ``ApplicationOracle`` the prior ``oracle`` — plus the ``PriorAudit``
    provenance tag.  Keying (loudly enforced, never silently bent):

    - ``--model`` must equal the verdict file's own model (a mismatched key
      is refused);
    - every imported pilot must carry a 64-hex ``binary_sha`` and a
      non-empty ``evidence_path`` (the key's second and third components);
    - ``--binary-sha``, when given, imports ONLY the pilots recorded under
      that binary — a key the file carries no pilot under is refused (the
      import can never bend the key to reach another binary's verdicts);
      without it every pilot imports under its own recorded binary;
    - the fields the prior audit did not record per pilot are the literal
      ``NULL``, never re-derived.
    """
    prior_path = Path(prior_path)
    payload = _read_json(prior_path)
    if not isinstance(payload, dict) \
            or not isinstance(payload.get("pilots"), list):
        raise ValueError(
            f"frozen prior audit {str(prior_path)!r} carries no pilot list; "
            f"expected the v3.2.11 verdict shape (model/pilots/model_row)")
    prior_model = payload.get("model")
    if prior_model not in MODELS:
        raise ValueError(
            f"frozen prior audit {str(prior_path)!r} names model "
            f"{prior_model!r}, which is not one of the twelve closure models")
    if model is not None and model != prior_model:
        # keyed by model: the import never bends the key to another model
        raise ValueError(
            f"frozen prior audit {str(prior_path)!r} is keyed to model "
            f"{prior_model!r}; the requested key {model!r} does not match "
            f"(the import is keyed by model + binary SHA + evidence path)")
    model_row = payload.get("model_row") or {}
    if not isinstance(model_row, dict):
        model_row = {}

    records: list = []
    for pilot in payload["pilots"]:
        if not isinstance(pilot, dict):
            raise ValueError(f"frozen prior audit {str(prior_path)!r} has a "
                             f"malformed pilot entry")
        sha = pilot.get("binary_sha")
        if not isinstance(sha, str) or not re.fullmatch(
                r"[0-9a-fA-F]{64}", sha):
            raise ValueError(
                f"frozen prior audit {str(prior_path)!r} pilot "
                f"{pilot.get('pilot_id')!r} carries no valid binary SHA256 "
                f"— the (model, binary SHA, evidence path) key is incomplete")
        if binary_sha is not None \
                and sha.lower() != str(binary_sha).lower():
            continue  # keyed by binary: another binary's pilots never import
        evidence_path = pilot.get("evidence_path")
        if not isinstance(evidence_path, str) or not evidence_path.strip():
            raise ValueError(
                f"frozen prior audit {str(prior_path)!r} pilot "
                f"{pilot.get('pilot_id')!r} carries no evidence path "
                f"— the (model, binary SHA, evidence path) key is incomplete")
        stages = pilot.get("stages") or {}
        if not isinstance(stages, dict):
            stages = {}
        missing = [str(code) for code in pilot.get("missing") or []]
        record = {
            # the frozen key (model + binary SHA + evidence path), verbatim
            "ModelID": prior_model,
            "PilotID": pilot.get("pilot_id"),
            "SampleRunID": pilot.get("sample_run_id"),
            "Seed": pilot.get("seed"),
            "EventOrdinal": pilot.get("event_ordinal"),
            "BinarySHA256": sha,
            "EvidencePath": evidence_path,
            # the prior verdict, carried verbatim (never re-graded)
            "FinalClassification": pilot.get("classification"),
            "ObservedTerminal": pilot.get("terminal"),
            "ApplicationOracle": pilot.get("oracle"),
            "TerminalReason": pilot.get("terminal_reason"),
            "PriorAuditRule": pilot.get("classification_rule"),
            "MissingEvidence": (";".join(missing) if missing else "none"),
            "MissingCodes": missing,
            # the prior audit's own stage flags, verbatim
            "InjectionVerified": stages.get("injection_verified", "n/a"),
            "ActivationVerified": stages.get("activation_verified", "n/a"),
            "Stages": stages,
            "SubUnit": model_row.get("SubUnit") or "n/a",
            "FaultDefinition": model_row.get("FaultDefinition") or "n/a",
            "SupplementaryOf": None,
            # the four §1 fields the prior audit did not record per pilot:
            # the literal NULL, never fabricated, never re-derived
            **{name: "NULL" for name in _PRIOR_AUDIT_UNRECORDED_FIELDS},
            # writer internals the aggregation reads; absences are explicit
            "AdjudicatedTerminal": pilot.get("terminal"),
            "VerifiedChainCount": None,
            "ChainKinds": [],
            "ChainEventCount": None,
            "ChainEdgeCount": None,
            "PathFragments": [],
            "MaskingMechanism": "NOT_APPLICABLE",
            "ChainMechanism": "NOT_APPLICABLE",
            "TerminalMechanism": "NOT_APPLICABLE",
            "ModelRuleRecord": None,
            "ModelStreamRecords": [],
            "ModelRunRecords": {},
            "RP01Watchdog": None,
            # the provenance marker distinguishing a frozen record from a
            # generically graded one in every downstream artifact
            "PriorAudit": FROZEN_PRIOR_AUDIT,
            "PriorAuditPath": str(prior_path),
        }
        records.append(record)
    if binary_sha is not None and not records:
        raise ValueError(
            f"frozen prior audit {str(prior_path)!r} (model {prior_model!r}) "
            f"carries no pilot under binary SHA {binary_sha!r}; the import "
            f"is keyed by binary and refuses to import a different "
            f"binary's verdicts")
    if not records:
        raise ValueError(
            f"frozen prior audit {str(prior_path)!r} carries no importable "
            f"pilot record")
    return records


def _merge_frozen(generic: list, frozen: list) -> tuple[list, list]:
    """Merge the frozen prior-audit records with the generically graded
    ones, keyed by (ModelID, BinarySHA256): a frozen group supersedes the
    generic records of the SAME key only (the prior audit already verified
    that (model, binary) group — re-grading it with the generic classifier
    is exactly what the import exists to avoid), and every other binary's
    records are untouched (a verdict is never computed across binaries, and
    a frozen import never overrides a different binary).  Returns the
    merged record list plus one loud note per supersession."""
    for record in frozen:
        if not record.get("PriorAudit"):
            raise ValueError(
                "a --frozen-prior records file carries a record without "
                f"the PriorAudit marker ({record.get('PilotID')!r}); only "
                "frozen imports built by the `frozen` subcommand are "
                "accepted there")
    frozen_keys = {(str(r.get("ModelID")), str(r.get("BinarySHA256")))
                   for r in frozen}
    kept = []
    dropped: dict[tuple, int] = {}
    for record in generic:
        key = (str(record.get("ModelID")),
               str(record.get("BinarySHA256") or "unknown"))
        if key in frozen_keys:
            dropped[key] = dropped.get(key, 0) + 1
            continue
        kept.append(record)
    notes = []
    for (model, sha), count in sorted(dropped.items()):
        notes.append(
            f"frozen prior audit {FROZEN_PRIOR_AUDIT} supersedes {count} "
            f"generic record(s) for {model}@{sha[:8]} (the prior audit "
            f"already verified that (model, binary) group; the generic "
            f"records are excluded, never merged)")
    return kept + frozen, notes


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
    for record in records:
        # the same schema §2 hard-invariant rejection the closure matrix
        # applies: a poisoned record is never emitted silently
        _validate_record(record)
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
    # the v3.2.12 supplementary naming (schema section 3: PilotID
    # ``SUPP-<MODEL>-<Rxx>``): a SUPP dir whose manifest/meta carry no
    # 12-model id is recognized from its frozen name, never silently skipped
    parts = pilot_dir.name.split("-")
    if parts[0] == "SUPP" and len(parts) >= 3 and parts[1] in MODELS:
        return parts[1]
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

    p_frozen = sub.add_parser(
        "frozen", help="import a frozen prior audit's per-pilot verdicts "
                       "(keyed by model + binary SHA + evidence path)")
    p_frozen.add_argument("--prior", required=True, type=Path,
                          help="v3.2.11 verdict JSON "
                               "(audit_v3_2_11/<MODEL>_verdict.json)")
    p_frozen.add_argument("--model", default=None,
                          help="the key's model id; must match the verdict "
                               "file's own model (refused otherwise)")
    p_frozen.add_argument("--binary-sha", default=None,
                          help="the key's binary SHA256; imports only the "
                               "pilots recorded under it (refused when the "
                               "file carries none)")
    p_frozen.add_argument("--json", required=True, type=Path,
                          help="write the imported records as JSON")

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
    p_matrix.add_argument("--frozen-prior", action="append", type=Path,
                          default=[],
                          help="frozen prior-audit records JSON built by "
                               "the `frozen` subcommand (repeatable); a "
                               "frozen group supersedes the generic records "
                               "of the same (model, binary) key only")
    p_matrix.add_argument("--out", type=Path, required=True,
                          help="output CSV path")

    p_features = sub.add_parser(
        "features", help="write the diagnostic feature dataset from records")
    p_features.add_argument("--records", action="append", type=Path,
                            required=True, help="records JSON (repeatable)")
    p_features.add_argument("--frozen-prior", action="append", type=Path,
                            default=[],
                            help="frozen prior-audit records JSON built by "
                                 "the `frozen` subcommand (repeatable); a "
                                 "frozen group supersedes the generic "
                                 "records of the same (model, binary) key "
                                 "only")
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
                  f"MaskingMechanism={record['MaskingMechanism']} "
                  f"ChainMechanism={record['ChainMechanism']} "
                  f"TerminalMechanism={record['TerminalMechanism']} "
                  f"missing=[{record['MissingEvidence']}]")
        return 0

    if args.command == "frozen":
        records = build_frozen_records(args.prior, model=args.model,
                                       binary_sha=args.binary_sha)
        args.json.write_text(
            json.dumps({"model": records[0]["ModelID"],
                        "prior_audit": FROZEN_PRIOR_AUDIT,
                        "prior_path": str(args.prior),
                        "records": records}, indent=2) + "\n",
            encoding="utf-8")
        print(f"frozen prior audit {args.prior} imported: "
              f"model={records[0]['ModelID']} pilots={len(records)} "
              f"(verdicts carried verbatim, never re-graded)")
        for record in records:
            print(f"  {record['PilotID']}: "
                  f"FinalClassification={record['FinalClassification']} "
                  f"ObservedTerminal={record['ObservedTerminal']} "
                  f"binary={str(record['BinarySHA256'])[:8]} "
                  f"prior_rule={record['PriorAuditRule']}")
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
        if args.frozen_prior:
            frozen = _load_records(args.frozen_prior)
            records, notes = _merge_frozen(records, frozen)
            for note in notes:
                print(note)
        write_closure_matrix(records, args.out)
        print(f"closure matrix written to {args.out} "
              f"(records={len(records)})")
        return 0

    if args.command == "features":
        records = _load_records(args.records)
        if args.frozen_prior:
            frozen = _load_records(args.frozen_prior)
            records, notes = _merge_frozen(records, frozen)
            for note in notes:
                print(note)
        write_feature_dataset(records, args.out)
        print(f"feature dataset written to {args.out} "
              f"(records={len(records)})")
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
