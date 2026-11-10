# LSU 12-Model Propagation Acceptance Standard (v3.2.12)

**Status:** FROZEN (2026-11-10). This document is the single authority for every
propagation verdict in the v3.2.12 closure round. Later tasks cite it instead of
redefining verdicts. No status matrix or Excel cell may ever be hand-set to a
verdict: `tools/lsu_12model_closure.py` computes every field deterministically
from the raw per-pilot artifacts (`trace_v31.jsonl`, `pilot_meta.json`,
`manifest.json`, `oracle.log`/`stdout.log`).

**Scope:** the twelve LSU fault models
A01, A03, FW02, SQ01, DA04, LP01, MD04, FW05, SQ03, SP05, LQ04, RP01 —
the eleven models audited in v3.2.11 plus RP01, whose implementation this round
approves (`APPROVED_BY_RESEARCHER_V3.2.12`).

**Builds on (and tightens):**

- `platform/terminal_rules.py` — chain-scoped terminal adjudication (v3.2.4/3.2.5)
- `platform/fault_effect_coverage.py` — fault-effect grading (v3.2.11 Task 2)
- `platform/trace_completeness.py` — record/trace/structural grading; the
  `structural_chain_completeness` alias exists since v3.2.11
- `audit_v3_2_11/LSU_11Model_Propagation_Audit_Summary_v3.2.11.md` — the
  eleven-model audit whose model-specific evidence rules this standard freezes

---

## 1. The eight per-pilot record fields

`tools/lsu_12model_closure.py` must emit exactly these eight fields per pilot,
with exactly these closed value sets (no other value may ever be written):

- `RecordIntegrity ∈ {VALID, INVALID, TRUNCATED}`
- `TraceCompleteness ∈ {COMPLETE, INCOMPLETE, MISSING}`
- `StructuralChainCompleteness ∈ {COMPLETE, PARTIAL, NONE}`
- `FaultEffectPropagationCoverage ∈ {COMPLETE, LIFECYCLE_ONLY, NONE, NOT_APPLICABLE}`
- `FaultCausality ∈ {PROVEN, PARTIAL, UNPROVEN}`
- `ObservedTerminal ∈ {SDC, MASKED, SQUASHED, CRASH, HANG, TIMEOUT, NO_INJECTION, INCOMPLETE, UNRESOLVED}`
- `ApplicationOracle ∈ {PASS, FAIL, MISSING, NOT_APPLICABLE}`
- `FinalClassification ∈ {COMPLETE_CAUSAL_CHAIN, VERIFIED_SINGLE_CONTEXT, LIFECYCLE_ONLY, PARTIAL, UNRESOLVED}`

Workflow stage flags (DESIGNED, SOURCE_AUDITED, IMPLEMENTED, COMPILED,
UNIT_TESTED, PILOT_RUN) are not evidence and are not among these fields: per the
v3.2.11 audit, "a pilot run alone (IMPLEMENTED/COMPILED/UNIT_TESTED/PILOT_RUN)
is never treated as propagation evidence."

### 1.1 RecordIntegrity — physical integrity of the record stream

- `VALID` — every record of `trace_v31.jsonl` parses and the trace validator
  reports no errors (the platform's `record_integrity` is `VALID` exactly when
  `validate()` returns no errors).
- `INVALID` — validation errors exist: malformed or inconsistent records.
- `TRUNCATED` — the stream is verifiably cut before its well-formed end (event
  cap reached, wall-clock cutoff, killed writer), so no closing summary record
  exists. New in v3.2.12: the per-file platform checker can only grade a file
  that exists and parses; a stream cutoff is a run-level fact recorded from the
  run harness.

### 1.2 TraceCompleteness — completeness of the trace as evidence

- `COMPLETE` — the trace validates, carries exactly one summary, and the summary
  is internally consistent with the events (TRIGGERED requires an injection
  event) and declares itself COMPLETE.
- `INCOMPLETE` — the trace exists but fails the completeness contract (declared
  INCOMPLETE, missing or inconsistent summary, or the forbidden
  incomplete-declares-MASKED combination). An incomplete trace never reports a
  terminal MASKED state (platform rule).
- `MISSING` — no trace file exists for the pilot (audit code
  `TRACE_FILE_MISSING`). New in v3.2.12: the platform checker cannot express
  file absence.

### 1.3 StructuralChainCompleteness — the STRUCTURAL question

Did the expected stage kinds appear on the fault's own chain? The value set is
exactly the platform's `structural_chain_completeness` values. Stage presence is
a structural claim only; whether the fault's EFFECT propagated is graded
separately (§1.4).

- `COMPLETE` — at least one frozen alternative stage profile for the
  (model, terminal) pair is fully present among the chain events
  (`trace_completeness.PROFILES`), and chain integrity holds.
- `PARTIAL` — chain events exist but no alternative profile is satisfied (or a
  chain-integrity failure downgrades coverage).
- `NONE` — no chain events at all, or no chain identity exists (no injection
  event, or the injection carries neither a usable `ptag` nor a
  `dyn_inst_seq`).

### 1.4 FaultEffectPropagationCoverage — the EFFECT question

Did the injected fault actually diverge a value or a control decision, and did
that divergence reach a committed architectural outcome? This field re-grades
the platform's `fault_effect_coverage` classification into the v3.2.12 standard
(see §7 for the mapping; the platform module itself is unchanged):

- `COMPLETE` — a verified divergence reached committed architectural state: a
  chained `commit`/`errant_commit`/`consumer_commit`, or an oracle-failing (SDC)
  terminal, or a directly evidenced fault-caused terminal (a proven-trigger
  HANG/TIMEOUT/SQUASHED chain, the RP01 case).
- `LIFECYCLE_ONLY` — the injection is TRIGGERED, the structural chain executed,
  and nothing diverged: the delivered payload is intact by construction, the
  fault's effect stayed internal. Canonical: LQ04 ("structural chain complete,
  correct payload, no corruption propagation" — v3.2.11 audit §4).
- `NONE` — no fault-effect propagation is observed: the injection is present but
  dormant, the trace yields no divergence evidence, or a divergence — where one
  is verified — reached no committed architectural outcome (no downstream
  link).
- `NOT_APPLICABLE` — no injection event exists in the run, so the effect
  question has no subject: determinism-control runs (no injection by design)
  and runs whose trigger never fired (the honest `NO_INJECTION` repeats).

### 1.5 FaultCausality — is the observed outcome proven fault-caused?

- `PROVEN` — every hop of the attributing path from the injection to the
  outcome satisfies the identity rules (§2) and the data rule (§3), and the
  terminal event sits on the fault's own chain.
- `PARTIAL` — some hops are verified but the decisive link to the terminal is
  not: a squash observed without proof it is fault-caused; a crash whose address
  mismatches the injected effective address; an oracle FAIL without a causally
  attributable consumer.
- `UNPROVEN` — no verified causal path exists between injection and the observed
  outcome (time-adjacent or off-chain terminal only).

### 1.6 ObservedTerminal — the run's observed outcome

The six values SDC, MASKED, SQUASHED, CRASH, HANG, TIMEOUT are outcome
terminals; NO_INJECTION, INCOMPLETE, UNRESOLVED record absences and are never
outcome terminals (§5).

- `SDC` — the application oracle FAILs and the fault's chain carries the
  corrupted value to a causally attributable consumer. An oracle failure without
  a causal consumer is not SDC (v3.2.5 rule, `ORACLE_FAIL_NO_CAUSAL_CONSUMER`).
- `MASKED` — the fault triggered, the faulting instruction committed with a
  data value present, and the application oracle PASSes (e.g. LP01 5/5: "All
  five pilots commit with the correct application checksum (MASKED): the
  corrupted byte is not used in the final result" — v3.2.11 audit §3).
- `SQUASHED` — the faulting instruction was squashed before commit; the
  writeback never became architectural.
- `CRASH` — the run aborted. For address-affecting models (A01/A03) the abort is
  attributable only when the fault address matches the injected effective
  address.
- `HANG` — the run stopped making architectural progress (ROB stall /
  non-progress termination observed on the fault's own entry).
- `TIMEOUT` — an external wall-clock or event-record limit ended the run before
  the workload's natural completion.
- `NO_INJECTION` — no injection event exists in the run.
- `INCOMPLETE` — the run/trace ended before any terminal could be observed.
- `UNRESOLVED` — chain-scoped adjudication could not resolve an outcome terminal
  (missing terminal, target not committed, no register-writeback evidence,
  store not committed).

### 1.7 ApplicationOracle — the raw application-level oracle result

- `PASS` — the checksum in the raw `oracle.log`/`stdout.log` equals the frozen
  golden.
- `FAIL` — the raw checksum differs from the frozen golden. A FAIL is never
  changed to obtain a verdict; it is recorded as FAIL/SDC.
- `MISSING` — the raw oracle artifact is absent although the run type expects
  one. A result recorded only in `pilot_meta.json` or an evidence file is
  MISSING at the raw-artifact level: per the v3.2.11 audit (DA04 R04/R05
  caveat), "`OracleVerified` is therefore `missing` at the raw-file level."
  The meta-recorded value is preserved as evidence; MISSING is recorded in the
  missing-evidence matrix and closed by supplementary runs.
- `NOT_APPLICABLE` — the run type defines no application-level golden by
  design (e.g. a count-only preflight).

### 1.8 FinalClassification — the verdict

See §6 for the fixed determination order. The five values:

- `COMPLETE_CAUSAL_CHAIN` — a verified complete causal chain, corroborated in
  more than one context (§4).
- `VERIFIED_SINGLE_CONTEXT` — a verified complete causal chain in exactly one
  context (§4); never upgraded without a second verified context.
- `LIFECYCLE_ONLY` — the injection triggered and its lifecycle/structural path
  executed intact, with no value or control divergence of the delivered
  payload.
- `PARTIAL` — real on-chain evidence exists but no complete chain is verified;
  the missing link is always named (`MissingEvidence`).
- `UNRESOLVED` — the evidence needed for any outcome grade is absent or
  unusable.

---

## 2. The five identity rules for a causal edge

An edge between two trace records is causal only through one of these five
identities. Time adjacency NEVER links events: a later tick that shares none of
these identities with the injection is not on the chain and creates no
propagation edge (v3.2.11 scope B3; enforced by `terminal_rules.chain_events`
and `fault_effect_coverage._chain_events`).

1. **`ptag`** — an event belongs to the fault's store/load/consumer chain only
   when its `ptag` equals the injection's `ptag`. `ptag` 0/empty carries no
   identity: commit, squash and lifecycle nodes are written with `ptag=0` and
   never link through `ptag`.
2. **`dyn_inst_seq`** — commit/squash/lifecycle nodes link through the faulting
   instruction's own `dyn_inst_seq`. Identity fields are compared
   `str()`-normalized, because numeric identity fields are ints in some trace
   vintages and JSON strings in others.
3. **`(lq_entry_id, generation)`** — a load-queue entry is identified only by
   the pair. A reused entry id under a later generation is a different entry,
   never the same edge.
4. **`(sq_entry_id, generation)`** — the same rule for store-queue entries.
5. **`(execution_attempt_id, replay_generation)`** — a re-executed instruction
   is a distinct execution attempt. An edge that crosses an execution attempt
   is causal only when the attempt id and the replay generation tie the two
   attempts of the same dynamic instruction; without that identity the chain is
   INCONCLUSIVE, never COMPLETE (`trace_completeness` cross-attempt rule). This
   identity is load-bearing for RP01, whose fault removes a replay trigger: a
   partial-address stall record without `instsToReplay` membership must be
   tied to the skipped attempt by `(execution_attempt_id, replay_generation)`
   before the hang can be attributed to the fault.

---

## 3. The data rule

**A consumer edge requires the consumer's input hash to equal the producer's
writeback hash.**

- On a writeback-sourced edge, `consumer_input_fnv` must equal the producer's
  `writeback_value_fnv` (the platform's `hash_discontinuity_wb_consumer`
  check). On a response-sourced edge the producer hash is `data_fnv`; on a
  consumer-to-consumer re-taint edge — the dominant form on real traces — the
  producer's output hash rides in `consumer_output_fnv`.
- A hash is REAL or ABSENT. The converter's `null`/`None`/`0`/empty sentinels
  are ABSENT hashes (`fault_effect_coverage._real_hash`): an absent hash can
  neither establish continuity, nor fabricate a divergence, nor verify an edge.
  An edge whose two hashes do not both exist as real hashes is not verified.
- Model-specific divergence records are part of the data rule, not an
  exception to it. The v3.2.11 audit found that "the generic structural/effect
  classifier is deliberately conservative and uses the delivered payload as its
  reference. That is correct for LQ04 (correct payload) but **under-reports
  LP01 and FW05**, whose fault effect is encoded in model-specific injection
  fields (`orig_data_*`/`inj_data_*` and `true_data_fnv`/`alt_data_fnv`)." For
  LP01 the decisive record is `orig_data_*` vs `inj_data_*` (byte0 before/after);
  for FW05 it is `true_data_fnv` vs `alt_data_fnv` with `selected_source`. The
  acceptance record must consult the model-specific record as the divergence
  evidence, then carry the effect forward through the hash chain above.
- The reverse direction is equally binding: "the tool does not upgrade a pilot
  to `COMPLETE` merely because a consumer exists" (v3.2.11 audit §6). A
  `consumer_commit` node whose input hash is absent, or whose edge fails the
  identity rules, is never a verified consumer edge.

---

## 4. The single-context rule

**One complete chain → `VERIFIED_SINGLE_CONTEXT`, not `COMPLETE_CAUSAL_CHAIN`.**

A *complete chain* is an end-to-end causal path from the injection event to a
committed architectural outcome (a chained `commit`/`errant_commit`/
`consumer_commit`, or a proven-trigger HANG/TIMEOUT/SQUASHED terminal) in which
every hop satisfies the identity rules (§2) and every consumer hop satisfies
the data rule (§3).

- **Per pilot:** count the distinct verified complete chains in the pilot's own
  trace — distinct committed outcomes are distinct chains. Exactly one →
  `VERIFIED_SINGLE_CONTEXT`; two or more → `COMPLETE_CAUSAL_CHAIN`.
- **Per model** (closure matrix / model verdict): count the distinct frozen
  contexts (injection sites, one pilot identity each) in which at least one
  complete chain is verified. Exactly one context → `VERIFIED_SINGLE_CONTEXT`;
  two or more → `COMPLETE_CAUSAL_CHAIN`.

A `VERIFIED_SINGLE_CONTEXT` record is never upgraded to `COMPLETE_CAUSAL_CHAIN`
without a second verified context; however internally perfect, a single chain
does not corroborate itself. This rule applies to A01 ("if only one context
forms a full chain, record `VERIFIED_SINGLE_CONTEXT`; do not upgrade" — plan
Task 7) and is the expected honest ceiling for RP01 unless the preflight proves
the chain in more than one of its five contexts.

`VERIFIED_SINGLE_CONTEXT` imposes the same evidential requirements as
`COMPLETE_CAUSAL_CHAIN` (§6); the only difference is the context count. It
differs from v3.2.11, which reported complete chains without a corroboration
requirement (§8, tightening T1).

---

## 5. The terminal rule

**`HANG`/`TIMEOUT`/`SQUASHED` are valid terminals; a missing injection is never
a terminal.**

- HANG, TIMEOUT and SQUASHED are accepted outcome terminals on the same footing
  as SDC, MASKED and CRASH. RP01's approved design predicts exactly these:
  "the ROB stalls → HANG/TIMEOUT unless an older squash clears the entry (then
  SQUASHED)" (`RP01_Final_Design_Gate_v3.2.11.md`), and its audit target is
  "`COMPLETE_CAUSAL_CHAIN` only for a directly evidenced HANG/SQUASHED chain,
  never for a run that silently masks the fault."
- A hard terminal beats the oracle: a run whose terminal is HANG (or TIMEOUT)
  is HANG regardless of an oracle PASS — a passing oracle never relabels an
  outcome terminal. Conversely an oracle FAIL alone never creates an SDC
  without a causally attributable consumer (§1.6).
- A missing injection is never a terminal. When no injection event exists,
  `ObservedTerminal=NO_INJECTION` records the absence and the record can only
  grade `UNRESOLVED` (§6 rule 1) — never an outcome grade. The platform
  agrees: `terminal_rules.adjudicate` returns `UNRESOLVED` with reason
  `NO_INJECTION_EVENT`, and `run_pilot.py` never relabels that honest state.
- A SQUASHED/HANG/TIMEOUT terminal contributes to a complete verdict ONLY with
  a proven trigger (`FaultCausality=PROVEN`): the terminal event must be
  identity-linked to the injection through §2/§3. The v3.2.11 audit set this
  line — MD04 R01/R04 and FW02 R01/R05 "SQUASHED; the trace does not prove the
  squash is fault-caused → `PARTIAL`" — and unproven squashes stay `PARTIAL`
  under this standard.

---

## 6. FinalClassification — the fixed determination order

`final_classification(record)` applies the rules below in this exact order; the
first rule that fires decides the verdict. The order is deterministic and is
the only path to a verdict — a matrix or Excel cell may never override it.

1. **Missing injection → `UNRESOLVED`.** The absence states that force
   `UNRESOLVED` are: no injection event (`ObservedTerminal=NO_INJECTION`,
   including design controls); `RecordIntegrity ∈ {INVALID, TRUNCATED}`;
   `TraceCompleteness ∈ {MISSING, INCOMPLETE}`; `StructuralChainCompleteness
   = NONE` (no chain identity exists); `ObservedTerminal ∈ {INCOMPLETE,
   UNRESOLVED}`. A record with any of these never grades an outcome value.
2. **HANG/TIMEOUT/SQUASHED with a proven trigger → `COMPLETE_CAUSAL_CHAIN`**
   (or `VERIFIED_SINGLE_CONTEXT` when the complete-chain evidence rests on one
   context, §4). Requires `FaultCausality=PROVEN` (§5); otherwise the record
   falls through to rule 5.
3. **Complete effect with consumer → `COMPLETE_CAUSAL_CHAIN`**
   (or `VERIFIED_SINGLE_CONTEXT` per §4). Requires
   `FaultEffectPropagationCoverage=COMPLETE` with hash-verified consumer edges
   (§3).
4. **Internal-only change → `LIFECYCLE_ONLY`.**
   `FaultEffectPropagationCoverage=LIFECYCLE_ONLY` with a structurally complete
   lifecycle observation: the injection triggered, the chain executed, nothing
   diverged.
5. **Otherwise → `PARTIAL`.** Real on-chain evidence exists but no complete
   chain is verified: a verified divergence without a downstream committed
   link; a suspected-but-unproven divergence (A01/A03: "the trace has no
   reference value for the correct address, so it cannot prove the delivered
   value differs, and the crashes are not attributable" — v3.2.11 audit §4);
   a squash/hang without a proven trigger; a dormant injection
   (`ActivationVerified=no`). `PARTIAL` always names its missing link in
   `MissingEvidence`.

Invariants (violations are defects; the writer must reject them loudly):

- `InjectionVerified=no` or `ActivationVerified=no` never grades
  `COMPLETE_CAUSAL_CHAIN` (or `VERIFIED_SINGLE_CONTEXT`); it can only grade
  `PARTIAL` or `UNRESOLVED`.
- `COMPLETE_CAUSAL_CHAIN` and `VERIFIED_SINGLE_CONTEXT` require
  `RecordIntegrity=VALID`, `TraceCompleteness=COMPLETE`,
  `StructuralChainCompleteness=COMPLETE` and `FaultCausality=PROVEN`.
- `LIFECYCLE_ONLY` requires a TRIGGERED injection and
  `StructuralChainCompleteness=COMPLETE` — a partially observed chain cannot
  prove that nothing diverged.
- A verdict is never computed across binaries: records are keyed by
  `BinarySHA256`, and pilots from different binaries split into separate
  verdicts, never merged.

---

## 7. Relation to the platform modules (what maps where)

This standard does not modify the platform modules; the closure tool maps their
outputs into the eight fields:

| Platform output | Standard field |
|---|---|
| `trace_completeness.record_integrity` (`VALID`/`INVALID`) + run-harness cutoff record | `RecordIntegrity` (+ `TRUNCATED` at run level) |
| `trace_completeness.trace_completeness` (`COMPLETE`/`INCOMPLETE`); absent file | `TraceCompleteness` (+ `MISSING`) |
| `trace_completeness.structural_chain_completeness` (`COMPLETE`/`PARTIAL`/`NONE`) | `StructuralChainCompleteness` (identical value set) |
| `fault_effect_coverage.classify` → `COMPLETE_CAUSAL_CHAIN` | `FaultEffectPropagationCoverage=COMPLETE` |
| `fault_effect_coverage.classify` → `LIFECYCLE_ONLY` | `FaultEffectPropagationCoverage=LIFECYCLE_ONLY` |
| `fault_effect_coverage.classify` → `PARTIAL` (divergence, no downstream link) | `FaultEffectPropagationCoverage=NONE`; `FinalClassification=PARTIAL` |
| `fault_effect_coverage.classify` → `UNRESOLVED`, reason `NO_INJECTION_EVENT` | `FaultEffectPropagationCoverage=NOT_APPLICABLE` |
| `fault_effect_coverage.classify` → `UNRESOLVED`, other reasons (dormant, gated) | `FaultEffectPropagationCoverage=NONE` |
| `terminal_rules.adjudicate` terminal + reason | `ObservedTerminal` |
| raw `oracle.log`/`stdout.log` vs frozen golden | `ApplicationOracle` |

`FinalClassification` is computed from the seven fields by the fixed order in
§6 and exists nowhere in the platform — the platform's per-pilot
`fault_effect_propagation_coverage` value (e.g. `COMPLETE_CAUSAL_CHAIN`) is an
input to the mapping, not the final verdict.

---

## 8. What v3.2.12 tightens, with the v3.2.11 evidence

- **T1 — Single-context corroboration.** v3.2.11 reported "COMPLETE 2/5
  unique" (DA04), "COMPLETE 5/5" (LP01), "COMPLETE 3/5" (MD04), "COMPLETE 4/5"
  (FW05) at pilot granularity, and "Four models have a verified fault-effect
  propagation chain: DA04, LP01, MD04, FW05." v3.2.12 keeps the complete-chain
  evidence bar but adds the corroboration requirement (§4): one complete chain
  grades `VERIFIED_SINGLE_CONTEXT`, never `COMPLETE_CAUSAL_CHAIN`. Re-grading
  of historical pilots is the closure tool's job (plan Tasks 3/16), not this
  document's.
- **T2 — FaultCausality is a required field.** v3.2.11 reasoned ad hoc that
  A01/A03 crashes "are not attributable" and MD04/FW02/FW05 squashes are not
  proven fault-caused. v3.2.12 freezes that reasoning into
  `FaultCausality ∈ {PROVEN, PARTIAL, UNPROVEN}` and requires `PROVEN` for
  every terminal-attributed complete verdict (§5, §6).
- **T3 — Raw-artifact oracle grading.** v3.2.11 recorded "the raw
  `oracle.log`/`stdout.log` for the v3.2.6 R04/R05 directories is absent; the
  oracle FAIL is recorded in `pilot_meta.json` and the E2E evidence file.
  `OracleVerified` is therefore `missing` at the raw-file level." v3.2.12 makes
  that the rule: `ApplicationOracle=MISSING` whenever only a meta record
  exists (§1.7); supplementary raw-oracle runs (plan Task 5) close the gap and
  corroborate, never replace, the original verdict.
- **T4 — The model-specific divergence record is mandatory evidence.** Quoted
  in §3: the generic payload check under-reports LP01 and FW05. The standard
  requires the model-specific record as the divergence evidence for those
  models, and forbids the converse shortcut (consumer presence alone).
- **T5 — TRUNCATED and MISSING are explicit.** Run-level stream cutoffs and
  absent trace files were implicit in v3.2.11 reason codes; v3.2.12 carries
  them as first-class values so no absence can be silently read as a pass.

---

## 9. Compatibility with the existing platform (Step 3 verification)

- `ObservedTerminal` covers every outcome terminal the platform can produce for
  the twelve models: SDC, MASKED, SQUASHED, CRASH, HANG from
  `terminal.py`/`terminal_rules.py`, plus the run-level observations TIMEOUT
  (external limit, `terminal.py` `RUN_STATUS`), NO_INJECTION (zero-injection
  repeats, `terminal_rules` `NO_INJECTION_EVENT`) and INCOMPLETE (stream
  cutoff). The platform's `HARD_TERMINALS` values `ARCH_STATE_CORRUPTION` and
  `DETECTED_CONTAINED` are outside the twelve-model observation space; if a
  run ever records one, the record keeps the raw value in evidence, grades
  `UNRESOLVED`, and the standard is revised — the value is never silently
  folded into an enumerated terminal.
- `FinalClassification` is a strict superset of `fault_effect_coverage`'s value
  set: `COMPLETE_CAUSAL_CHAIN`, `PARTIAL`, `LIFECYCLE_ONLY`, `UNRESOLVED`
  unchanged; `VERIFIED_SINGLE_CONTEXT` added by §4.
- `StructuralChainCompleteness` is exactly the platform's
  `structural_chain_completeness` value set.
- `RecordIntegrity` and `TraceCompleteness` are supersets of the platform's
  `record_integrity` (`VALID`/`INVALID`) and `trace_completeness`
  (`COMPLETE`/`INCOMPLETE`), adding the run-level states `TRUNCATED` and
  `MISSING`.

Per-pilot record layout, sources, evidence requirements, and the per-field
mapping rules are specified in
`audit_v3_2_12/pilot_record.schema.md`, which is normative with this document.
