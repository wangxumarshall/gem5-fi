# Pilot Record Schema (LSU v3.2.12)

**Status:** FROZEN (2026-11-10). Normative with
`../LSU_Propagation_Acceptance_Standard_v3.2.12.md`: the standard defines the
eight fields and the verdict rules; this document fixes the record layout —
sources, evidence requirements, and the per-field mapping to the final
classification — that `tools/lsu_12model_closure.py` emits and every later
matrix/dataset writer consumes. Task 3 implements against this schema; later
tasks cite it instead of redefining verdicts.

**Emitted by:** `tools/lsu_12model_closure.py build_pilot_record(pilot_dir,
model, supplementary_of=None) -> dict`, reusing
`tools.lsu_propagation_audit.audit_pilot` (keys `identity, stages, evidence,
terminal, oracle, missing, classification`); the tool never re-parses traces
independently and never hand-sets a verdict.

## 1. The eight per-pilot fields

| Field | Allowed values | Source artifact | Required evidence | Rule mapping to FinalClassification |
|---|---|---|---|---|
| `RecordIntegrity` | `{VALID, INVALID, TRUNCATED}` | `trace_v31.jsonl` (validator over every record) + run-harness cutoff record | `VALID`: zero validation errors. `INVALID`: the validator's error list. `TRUNCATED`: the writer/runner stopped mid-stream (event cap, wall-clock cutoff, killed process) so no closing summary exists. | `VALID` is required for any outcome grade. `INVALID` or `TRUNCATED` → rule 1: `UNRESOLVED`. |
| `TraceCompleteness` | `{COMPLETE, INCOMPLETE, MISSING}` | the trace's single `summary` record (`trace_completeness`), re-derived by `platform/trace_completeness.check_completeness` | `COMPLETE`: validates, one summary, summary consistent (TRIGGERED ⇒ injection event), declares COMPLETE. `INCOMPLETE`: any completeness-contract failure (declared INCOMPLETE, missing/inconsistent summary, incomplete-declares-MASKED). `MISSING`: no trace file (audit code `TRACE_FILE_MISSING`). | `COMPLETE` is required for any outcome grade. `INCOMPLETE` or `MISSING` → rule 1: `UNRESOLVED`. An incomplete trace never reports a terminal MASKED state. |
| `StructuralChainCompleteness` | `{COMPLETE, PARTIAL, NONE}` | `check_completeness(...).structural_chain_completeness` (chain-scoped stage profile) | The fault's own chain events (scoped by `ptag` / `dyn_inst_seq`, identity rules §2 of the standard) against the frozen alternative stage profiles for (model, terminal) in `trace_completeness.PROFILES`; chain-integrity reason codes must be empty for `COMPLETE`. | `COMPLETE` is required for `COMPLETE_CAUSAL_CHAIN`, `VERIFIED_SINGLE_CONTEXT` and `LIFECYCLE_ONLY`. `PARTIAL` caps the record at `PARTIAL` (rule 5). `NONE` (no chain identity) → rule 1: `UNRESOLVED`. |
| `FaultEffectPropagationCoverage` | `{COMPLETE, LIFECYCLE_ONLY, NONE, NOT_APPLICABLE}` | `platform/fault_effect_coverage.classify` re-derived via `audit_pilot`'s `classification`, plus the model-specific injection records | `COMPLETE`: hash-verified (or model-specific-record-verified) divergence reaching a chained commit/errant_commit/consumer_commit, an oracle-failing terminal, or a proven fault-caused terminal. `LIFECYCLE_ONLY`: TRIGGERED, chain executed, nothing diverged. `NONE`: injection present but dormant/no divergence evidence/no downstream link. `NOT_APPLICABLE`: no injection event exists. | `COMPLETE` → rules 2–3 (`COMPLETE_CAUSAL_CHAIN`, or `VERIFIED_SINGLE_CONTEXT` per the single-context rule). `LIFECYCLE_ONLY` → rule 4: `LIFECYCLE_ONLY`. `NONE` → at best `PARTIAL` (rule 5); `UNRESOLVED` when rule-1 absence states fire. `NOT_APPLICABLE` → rule 1: `UNRESOLVED`. |
| `FaultCausality` | `{PROVEN, PARTIAL, UNPROVEN}` | the identity-verified edges from injection to terminal, re-derived from the trace and its `propagation_edge` records | `PROVEN`: every hop of the attributing path satisfies the five identity rules and the data rule; the terminal is on the fault's own chain (CRASH: fault address matches the injected EA; SQUASHED: the squash of the faulting instruction is on its own chain; HANG/TIMEOUT: the non-progress state is identity-linked to the faulting entry). `PARTIAL`: some hops verified, the decisive terminal link is not. `UNPROVEN`: no verified causal path (time-adjacent/off-chain only). | `PROVEN` is required for rules 2–3 (terminal-attributed and consumer-path complete verdicts). `PARTIAL` or `UNPROVEN` caps the record at `PARTIAL` (rule 5), or `UNRESOLVED` under rule 1. |
| `ObservedTerminal` | `{SDC, MASKED, SQUASHED, CRASH, HANG, TIMEOUT, NO_INJECTION, INCOMPLETE, UNRESOLVED}` | `pilot_meta.json` (`classification.observed_terminal`), oracle, run status; adjudicated by `platform/terminal_rules.adjudicate` | The terminal records plus the adjudication reason codes. The six outcome values are terminals; `NO_INJECTION`, `INCOMPLETE`, `UNRESOLVED` record absences. `HANG`/`TIMEOUT`/`SQUASHED` are valid terminals; a missing injection is never a terminal. A passing oracle never relabels an outcome terminal; an oracle FAIL without a causal consumer is not SDC. | Outcome values enable rules 2–4. `NO_INJECTION` → rule 1: `UNRESOLVED` (missing injection is never a terminal). `INCOMPLETE`/`UNRESOLVED` → rule 1: `UNRESOLVED`. `HANG`/`TIMEOUT`/`SQUASHED` reach a complete verdict only with `FaultCausality=PROVEN` (rule 2). |
| `ApplicationOracle` | `{PASS, FAIL, MISSING, NOT_APPLICABLE}` | raw `oracle.log`/`stdout.log` vs the frozen golden in `pilot_meta.json`/`manifest.json` | `PASS`/`FAIL`: the checksum in the RAW artifact equals/differs from the golden. `MISSING`: the raw artifact is absent though expected — a result recorded only in `pilot_meta.json`/evidence files is `MISSING` at the raw-artifact level (v3.2.11 DA04/LP01/MD04 gap; closed by SUPP raw-oracle runs, which corroborate and never replace the original verdict). `NOT_APPLICABLE`: the run type defines no application-level golden by design. | `FAIL` contributes to `SDC` only with a causally attributable consumer. `PASS` never upgrades or relabels a terminal (HANG beats a passing oracle). `MISSING` never upgrades a verdict; it is recorded in `MissingEvidence`/the missing-evidence matrix. `NOT_APPLICABLE` has no grading effect. |
| `FinalClassification` | `{COMPLETE_CAUSAL_CHAIN, VERIFIED_SINGLE_CONTEXT, LIFECYCLE_ONLY, PARTIAL, UNRESOLVED}` | computed from the seven fields above — never from a status matrix, an Excel cell, or a hand edit | The fixed order below is the only path to a verdict; the first rule that fires decides. | Rules 1–5 (below). |

## 2. FinalClassification — the fixed order (normative)

1. Missing injection → `UNRESOLVED`. The absence states forcing `UNRESOLVED`:
   no injection event (`ObservedTerminal=NO_INJECTION`), `RecordIntegrity ∈
   {INVALID, TRUNCATED}`, `TraceCompleteness ∈ {MISSING, INCOMPLETE}`,
   `StructuralChainCompleteness=NONE`, `ObservedTerminal ∈ {INCOMPLETE,
   UNRESOLVED}`.
2. `HANG`/`TIMEOUT`/`SQUASHED` with a proven trigger (`FaultCausality=PROVEN`)
   → `COMPLETE_CAUSAL_CHAIN`; `VERIFIED_SINGLE_CONTEXT` when the
   complete-chain evidence rests on one context.
3. Complete effect with consumer (`FaultEffectPropagationCoverage=COMPLETE`
   with hash-verified consumer edges) → `COMPLETE_CAUSAL_CHAIN`;
   `VERIFIED_SINGLE_CONTEXT` per the single-context rule.
4. Internal-only change (`FaultEffectPropagationCoverage=LIFECYCLE_ONLY`,
   TRIGGERED, structurally complete lifecycle observation) → `LIFECYCLE_ONLY`.
5. Otherwise → `PARTIAL`, with the missing link named in `MissingEvidence`.

Exception E1 (LQ04, standard §6 clause 3b / §10, frozen amendment
2026-11-10): between rules 3 and 4, a runtime-proven LQ04 senderState masking
chain grades `COMPLETE_CAUSAL_CHAIN` with
`MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE` and
`ObservedTerminal=MASKED`, even though
`FaultEffectPropagationCoverage=LIFECYCLE_ONLY` (which stays what the
platform graded). Model-scoped — it upgrades no other model — and computed
by the tool from the record's association and hash fields; standard §10 lists
the full conjunction. The record carries the exception's evidence fields
(`MemoryResponseAssociation`, `WritebackAssociation`) and its outcome field
`MaskingMechanism ∈ {RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE,
NOT_APPLICABLE}` (`NOT_APPLICABLE` everywhere E1 does not fire).

Exceptions E2/E3/E4 (SQ01/SQ03/SP05, standard §6 clause 3c / §11, frozen
amendment 2026-11-10): at the same layer (immediately after E1, before rule
4), a runtime-proven SQ-family model-record chain grades a complete verdict
— `VERIFIED_SINGLE_CONTEXT` per the single-context rule, model-level
`COMPLETE_CAUSAL_CHAIN` with two or more distinct frozen contexts — with
`ObservedTerminal=SDC` (E2 SQ01, E4 SP05) or `ObservedTerminal=MASKED`
(E3 SQ03) and the `ChainMechanism` of standard §11 named, even though
`FaultEffectPropagationCoverage=LIFECYCLE_ONLY` (which stays what the
platform graded). Model-scoped — each exception upgrades no other model —
and computed by the tool from the record's model-rule fields; standard §11.3
lists each conjunction in full (a conjunction of proven runtime fields; no
upgrade on inference). The record carries the exception's evidence field
`ModelRuleRecord` (the `sq01_chain`/`sq03_effect`/`sp05_stage` record
exported verbatim from the fault's own chain, `null` when absent) and its
outcome field `ChainMechanism ∈ {SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER,
SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT,
STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED, NOT_APPLICABLE}`
(`NOT_APPLICABLE` everywhere the model's conjunction does not fire).

Exceptions E5/E6/E7 (RP01/A03/A01, standard §6 clause 3d / §12, frozen
amendment 2026-11-11): BEFORE rule 1's integrity gates (each names the
integrity state it relaxes — E5 the TRUNCATED/INCOMPLETE watchdog-fatal
record, E6 the TRUNCATED crash-cut record, E7's discard companion the
honestly-UNRESOLVED terminal), a runtime-proven terminal exception chain
grades a complete verdict exactly as E2/E3/E4 do (`VERIFIED_SINGLE_CONTEXT`
per pilot, model-level `COMPLETE_CAUSAL_CHAIN` with two or more distinct
frozen contexts), with the `TerminalMechanism` of standard §12 named; the
E7 discard companion (`a01_ea_discarded` with `applied_to_request=0`) grades
`PARTIAL`, never `UNRESOLVED` and never a complete verdict. Model-scoped and
computed from proven runtime records only (no upgrade on inference); standard
§12.3 lists each conjunction in full. The record carries the exceptions'
evidence fields `ModelStreamRecords` (the a01_ea / a01_ea_discarded /
a01_consumed / a03_stream records on the fault's own chain, exported
verbatim), `ModelRunRecords` (the run-level `a03_activation` and
`simulator_abort` records that carry no chain identity) and `RP01Watchdog`
(the parsed `CHAOS_RP01_WATCHDOG=EXPIRED ... injected=1` sidecar record, or
`null`), and its outcome field `TerminalMechanism ∈
{REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT,
STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH,
WRONG_EA_LOAD_DELIVERED_AND_CONSUMED, NOT_APPLICABLE}`
(`NOT_APPLICABLE` everywhere the model's conjunction does not fire,
including the E7 discard companion).

Frozen prior-audit records (standard §12.5): a record imported from the
frozen v3.2.11 prior audit by the `frozen` subcommand — keyed by (model,
binary SHA, evidence path) — carries the prior per-pilot verdict verbatim
(`FinalClassification` = the prior classification, `ObservedTerminal` /
`ApplicationOracle` = the prior terminal/oracle) plus the provenance
markers `PriorAudit` (= `v3.2.11`), `PriorAuditRule` and `PriorAuditPath`;
the four §1 fields the prior audit did not record per pilot
(`RecordIntegrity`, `TraceCompleteness`, `StructuralChainCompleteness`,
`FaultEffectPropagationCoverage`, `FaultCausality`) are the literal `NULL`,
never fabricated, never re-derived. In the matrix a frozen group supersedes
the generic records of the same (model, binary) key only; every other
binary's records are untouched.

Single-context rule: one complete chain → `VERIFIED_SINGLE_CONTEXT`, not
`COMPLETE_CAUSAL_CHAIN` (per-pilot: distinct verified complete chains in the
trace; per-model: distinct frozen contexts with at least one complete chain;
one context never grades `COMPLETE_CAUSAL_CHAIN`).

Hard invariants — a writer that violates any of these must raise rather than
emit the row:

- `FinalClassification ∈ {COMPLETE_CAUSAL_CHAIN, VERIFIED_SINGLE_CONTEXT}` with
  `InjectionVerified=no` is a defect (reject loudly).
- `ActivationVerified=no` can grade at most `PARTIAL` (or `UNRESOLVED`), never
  `COMPLETE_CAUSAL_CHAIN`/`VERIFIED_SINGLE_CONTEXT`.
- Every CSV cell is a value or the literal `NULL`/`NOT_APPLICABLE`; an empty
  string or a bare `PASS` is a defect. Absences are reported explicitly, never
  as silent zeros.
- A verdict is never computed across binaries: records are keyed by
  `BinarySHA256`; a model whose pilots span binaries splits into one row per
  binary SHA (`binary_splits`), never a merged verdict.

## 3. Record identity and provenance columns

`build_pilot_record` emits the eight fields above plus these columns:

| Column | Source | Notes |
|---|---|---|
| `ModelID` | the frozen model id | one of A01, A03, FW02, SQ01, DA04, LP01, MD04, FW05, SQ03, SP05, LQ04, RP01 |
| `PilotID` | the pilot directory name | `SUPP-<MODEL>-<Rxx>` for supplementary runs; a sidecar maps back to the original |
| `SampleRunID` | `pilot_meta.json` | frozen; never modified |
| `Seed` | `pilot_meta.json` | frozen; supplementary runs reuse the original seed and record it |
| `EventOrdinal` | `pilot_meta.json` event ordinal | the ordinal of the injected event; monotonic per pilot; the DA04 re-runs must read the original ordinal |
| `BinarySHA256` | the pilot's recorded binary SHA | a SUPP run under a new binary corroborates raw Oracle only; the original verdict stays tied to its original binary |
| `WorkloadSHA256` | the pilot's recorded workload SHA | every run records its own |
| `EvidencePath` | the pilot directory | raw artifacts live here; historical directories are never overwritten |
| `MissingEvidence` | the tool's missing-evidence codes | reason codes for every `no`/`missing` stage; feeds the missing-evidence matrix (`ModelID, PilotID, MissingStage, MissingEvent, MissingCausalEdge, RootCause, RequiredHook, RequiredWorkloadChange, RequiredRunCount, ExpectedEvidence`) |
| `supplementary_of` | SUPP sidecar | original `SampleRunID` the SUPP pilot corroborates (`None` for original pilots) |

## 4. Honesty rules carried by this schema

- Historical verdicts are inputs to re-derive, never values to copy
  (`lsu_propagation_audit` contract).
- A golden value is never changed to obtain `PASS`; a wrong application result
  is recorded as `FAIL`/`SDC`.
- Workflow stage flags (`IMPLEMENTED`, `COMPILED`, `UNIT_TESTED`, `PILOT_RUN`)
  are not among the fields and never influence them; only the raw artifacts do.
- `NOT_APPLICABLE`/`NULL` are explicit and reasoned (`NOT_APPLICABLE` for
  questions that do not arise; `NULL` for absent values), per the platform
  honesty convention: never a silent zero, never a blank cell.
