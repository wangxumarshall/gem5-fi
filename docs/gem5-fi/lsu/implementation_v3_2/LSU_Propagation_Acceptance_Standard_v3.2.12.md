# LSU 12-Model Propagation Acceptance Standard (v3.2.12)

**Status:** FROZEN (2026-11-10); **amended 2026-11-10** (plan Task 4 review
round 1) with §6 clause 3b and §10 — exception E1, the LQ04 senderState
masking exception — recorded through this standard's own revise,
never-silently-fold path; no other section changed. **Amended again
2026-11-10** (SQ grading closure) with §6 clause 3c and §11 — exceptions E2
(SQ01), E3 (SQ03) and E4 (SP05), the SQ-family model-record chain exceptions
— through the same revise path; no other section changed. This document is
the single authority for every
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
  more than one context (§4); or, per exception E1 (§6 clause 3b, §10), the
  runtime-proven LQ04 senderState masking chain (model-scoped, §10); or, per
  exceptions E2/E3/E4 (§6 clause 3c, §11), a runtime-proven SQ-family
  model-record chain (model-scoped to SQ01/SQ03/SP05, §11) corroborated in
  two or more distinct contexts under §4.
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
3b. **Exception E1 — the LQ04 senderState masking chain →
   `COMPLETE_CAUSAL_CHAIN`** (model-scoped, frozen amendment 2026-11-10,
   §10). Between rules 3 and 4: an LQ04 record whose senderState masking
   chain is runtime-proven (the full §10 conjunction) grades
   `COMPLETE_CAUSAL_CHAIN` with `ObservedTerminal=MASKED` and
   `MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE`, even
   though `FaultEffectPropagationCoverage=LIFECYCLE_ONLY` — the coverage
   value stays what the platform graded, but no longer forces the
   classification down. The exception upgrades no other model, and an LQ04
   record missing any §10 condition follows rules 4/5 exactly as before.
3c. **Exceptions E2/E3/E4 — the SQ-family model-record chains → complete
   verdict** (model-scoped to SQ01/SQ03/SP05, frozen amendment 2026-11-10,
   §11). At the same layer, immediately after E1: an SQ01, SQ03 or SP05
   record whose model-record chain is runtime-proven (the full §11
   conjunction of proven fields) grades a complete verdict —
   `VERIFIED_SINGLE_CONTEXT` per §4, `COMPLETE_CAUSAL_CHAIN` at model level
   with two or more distinct frozen contexts — with `ObservedTerminal=SDC`
   (E2 SQ01, E4 SP05) or `ObservedTerminal=MASKED` (E3 SQ03) and the
   `ChainMechanism` of §11 named, even though
   `FaultEffectPropagationCoverage=LIFECYCLE_ONLY` — the coverage value
   stays what the platform graded, but no longer forces the classification
   down. The exceptions upgrade no other model, and a record missing any
   §11 condition follows rules 4/5 exactly as before — no upgrade on
   inference alone.
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

---

## 10. Exception E1 — the LQ04 senderState masking chain (frozen amendment, 2026-11-10)

This section is the standard's own "revise, never silently fold" path: the
amendment is recorded explicitly, with its authority and its exact
conditions, and `tools/lsu_12model_closure.py` computes it from the record —
no matrix, Excel cell, or report may apply it by hand.

### 10.1 The researcher authority (binding)

The researcher brief §八 (v3.2.12, 2026-11-10) is the binding authority for
LQ04's verdict; its ruling, recorded in the v3.2.12 SDD ledger
(`.superpowers/sdd/2026-11-10-lsu-v3-2-12-propagation-closure/progress.md`),
is quoted verbatim:

> "Ruling: LQ04 FinalClassification = COMPLETE_CAUSAL_CHAIN with
> ObservedTerminal=MASKED and
> MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE when the
> senderState path is runtime-proven (it is, 5/5), even though
> FaultEffectPropagationCoverage stays LIFECYCLE_ONLY. The researcher brief
> §八 is the binding authority; the Task-2 generic rule must yield via the
> standard's own revise-don't-silently-fold path."

The plan's Task 4 interface line records the same outcome pair
(`docs/superpowers/plans/2026-11-10-lsu-v3-2-12-propagation-closure.md`):
"Produces: `FinalClassification` for LQ04, either `COMPLETE_CAUSAL_CHAIN`
with `TerminalState=MASKED` and
`MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE`, or
`LIFECYCLE_ONLY` with the missing link named."

### 10.2 Why an exception is needed

Rule 3 requires `FaultEffectPropagationCoverage=COMPLETE` — a verified
**divergence** (§1.4). The LQ04 masking chain is the exact opposite: the
response is resolved to the original request through the packet's
`senderState` while the LQ entry is visibly invalid (`valid=0`,
`_request=nullptr`, the `corruptLifetime` window), so the delivered payload
is intact by construction and the honest effect grade stays `LIFECYCLE_ONLY`
(`platform/fault_effect_coverage.py`, unchanged this round). Under rule 4
alone that coverage value forces the classification down even when the
chain that delivered the intact payload — injection → `memory_response` →
`register_writeback` → consumer → commit — is complete, identity-linked
(§2) and hash-verified (§3) on the fault's own chain, with the MASKED
terminal sitting on that chain. The ruling separates the two questions: the
*effect* stayed inside the LQ-entry lifecycle, but the *causal chain* that
delivered the intact payload and produced the MASKED terminal is complete
and runtime-proven, and grades `COMPLETE_CAUSAL_CHAIN` with the masking
mechanism named.

### 10.3 The rule (deterministic, model-scoped)

Between rules 3 and 4 of §6, the closure tool upgrades a record to
`COMPLETE_CAUSAL_CHAIN` — and emits
`MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE` — only when
ALL of the following hold:

1. `ModelID = LQ04`. The exception upgrades no other model; every other
   model follows §6 unchanged.
2. `ObservedTerminal = MASKED` — the ruling's outcome terminal; E1 names a
   *masking* mechanism and never relabels SDC/CRASH/HANG/SQUASHED records.
3. `FaultCausality = PROVEN`.
4. `RecordIntegrity = VALID`, `TraceCompleteness = COMPLETE`,
   `StructuralChainCompleteness = COMPLETE`, and
   `InjectionVerified`/`ActivationVerified` = yes — the §6 invariant set for
   every complete verdict, which E1 also enforces.
5. The chain evidence carries the senderState association on BOTH the
   `memory_response` and the `register_writeback` (the record's
   `MemoryResponseAssociation` = `WritebackAssociation` = `sender_state`):
   the runtime records `association=sender_state;
   entry_valid_at_response=0; entry_request_at_response=0; data_unchanged=1`
   quoted per pilot in
   `audit_v3_2_12/LQ04_Propagation_Audit_v3.2.12.md` (§§3.1, 5.1).
6. The consumer input hash equals the writeback value hash, both real
   hashes (§3): `WritebackValueFnv == ConsumerInputFnv`.

When any condition fails, the LQ04 record follows §6 exactly as before
(`LIFECYCLE_ONLY` under rule 4, `PARTIAL` under rule 5) — no upgrade on
inference alone. E1 does **not** change `FaultEffectPropagationCoverage`:
the field keeps whatever the platform graded (`LIFECYCLE_ONLY` for the
intact chain); E1 only stops that value from forcing the classification
down.

### 10.4 Relation to §4 (single-context corroboration) and the record field

Within E1 the per-pilot record grades `COMPLETE_CAUSAL_CHAIN` directly, on
the researcher's binding authority (§10.1): the masking chain's completeness
is runtime-proven per record (conditions 3–6 are per-record facts — a
stronger evidence bar than §4's context count), and the model-level verdict
still carries the five distinct frozen contexts (ordinals 1–5, one pilot
identity each). §4 continues to govern every generic rule-2/rule-3 complete
verdict, unchanged.

E1 adds one record field: `MaskingMechanism ∈
{RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE, NOT_APPLICABLE}` — the former
exactly when E1 fires, the latter otherwise (including every non-LQ04
record). It is emitted by the tool from the same §10.3 conjunction; a
matrix or report may quote it but never set it.

---

## 11. Exceptions E2/E3/E4 — the SQ-family model-record chains (frozen amendment, 2026-11-10)

This section uses the standard's own "revise, never silently fold" path
(the same path §10 used for E1): the amendment is recorded explicitly, with
its authority and its exact conditions, and `tools/lsu_12model_closure.py`
computes it from the record — no matrix, Excel cell, or report may apply it
by hand.

### 11.1 The authority (binding)

The binding evidence is the v3.2.12 SQ ordinal re-selection round
(2026-11-10), whose artifacts are frozen in this repo:

- `audit_v3_2_12/SQ_Ordinal_Eligibility_Preflight_v3.2.12.md` — the
  predetermined address-eligibility selection rule (frozen before any fault
  run: the first ordinal whose selected store lies inside the workload's
  reload-consumed buffer `[0x491990, 0x492190)`; address eligibility only,
  never an outcome criterion), the 99-probe census, and the per-model
  K\* (SQ01 1006, SQ03 1009, SP05 940);
- `audit_v3_2_12/SQ01_SQ03_SP05_Eligible_Run_Records_v3.2.12.csv` — the 18
  per-run records (15 fault runs R01B..R05B, 3 controls C01B) with the
  model-record hop fields quoted per run;
- `audit_v3_2_12/{SQ01,SQ03,SP05}_verdict_elig_v3.2.12.json` — the closure
  tool's own per-pilot records for those runs;
- `audit_v3_2_12/FW02_SQ01_SQ03_SP05_Evidence_Audit_v3.2.12.md` §2.2 — the
  audit that found the original ordinals 1–5 select C-runtime startup
  stores and prescribed the re-selection method.

That round's finding, quoted from the preflight §5: the fault runs carry
"**complete per-hop runtime evidence** — SQ01 `mem_write_hash ==
reload_data_hash == consumer_hash` (all three hops hash-equal per context);
SQ03 drain_tick < commit_tick with `visible_before_commit=1` and a valid
`reload_data_hash`; SP05 `write_skipped=1` with the reload reading the
stale zero word (`reload_data_hash` present, `store_data_fnv=null` — the
honest unwired field)" — 5/5 contexts per model, with `FaultCausality=PROVEN`
and (SQ01/SQ03) all nine stage flags yes. The verdict recorded there as
concern #1 — that the frozen tool still grades these runs `LIFECYCLE_ONLY`
because the trace converter's generic `value_divergence` analysis reports
`TRIGGERED_NO_DIVERGENCE` — is the gap this amendment closes.

### 11.2 Why an exception is needed

Rule 3 requires `FaultEffectPropagationCoverage=COMPLETE` — a divergence
recognized by the platform's **generic** `value_divergence` analysis
(`platform/fault_effect_coverage.py`, unchanged this round). That analysis
compares the delivered payload's hashes on the generic
response→writeback→consumer hops; it does not bind the three SQ-family
models' own rule records (`sq01_chain`, `sq03_effect`, `sp05_stage`) into
its divergence list. For SQ01 the corrupted byte IS the delivered payload
(all hops hash-equal — divergence from the *golden*, not from the *payload*),
for SQ03 the fault effect is a visibility/ordering move (correct payload,
wrong visibility time), and for SP05 the store-side hash is honestly null
(the `store_data_fnv` wiring is unimplemented in this binary). In all three
cases the generic analysis correctly reports `TRIGGERED_NO_DIVERGENCE` and
the honest coverage grade stays `LIFECYCLE_ONLY` — exactly the
under-reporting the v3.2.11 audit already identified for LP01/FW05 (§3,
T4): "the generic structural/effect classifier is deliberately conservative
and uses the delivered payload as its reference… **under-reports** LP01 and
FW05, whose fault effect is encoded in model-specific injection fields."
This amendment extends that same principle to the three SQ-family models'
rule records: the model-specific record is mandatory divergence/chain
evidence (§3), and the acceptance verdict must consult it. As with E1, the
ruling separates the two questions: the generic *coverage* field keeps its
honest platform value (`LIFECYCLE_ONLY`), but the *model-record chain* —
recorded at runtime by the injector's own rule, identity-linked to the
fault's chain (§2), hash-verified on every data hop (§3) — is complete and
runtime-proven, and no longer forces the classification down.

### 11.3 The rules (deterministic, model-scoped)

`tools/lsu_12model_closure.py` exports each model's rule record from
`audit_pilot`'s evidence bundle (the `sq01_chain` / `sq03_effect` /
`sp05_stage` record on the fault's own chain, with its detail fields
verbatim — the same export pattern E1 used for the LQ04 `association`
fields; no independent trace re-parse, no forked classifier). The tool
upgrades a record to a complete verdict — and emits the matching
`ChainMechanism` — only when ALL conditions of the model's conjunction
hold. Every condition is a proven runtime field; **no upgrade on
inference**. Shared prefix (all three rules):

1. `ModelID` is the rule's own model (SQ01 / SQ03 / SP05). Each exception
   upgrades no other model; every other model follows §6 unchanged.
2. `ObservedTerminal` is the rule's outcome terminal: `SDC` for E2/E4
   (the corrupted or stale delivery failed the application oracle),
   `MASKED` for E3 (correct payload, oracle PASS — the effect is the
   visibility violation, not a data corruption).
3. `FaultCausality = PROVEN`.
4. `RecordIntegrity = VALID`, `TraceCompleteness = COMPLETE`,
   `StructuralChainCompleteness = COMPLETE`, and
   `InjectionVerified`/`ActivationVerified` = yes — the §6 invariant set
   every complete verdict enforces (identical to E1 §10.3 condition 4).
5. The model's rule record exists on the fault's own chain (exported as
   the record's `ModelRuleRecord`).

**E2 — SQ01 (`sq01_chain`), mechanism
`SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER`:**

6. `data_diverged = 1` — the injected bit flip actually changed the SQ
   entry's data byte (`data_before != data_after` at runtime).
7. A bound reload and consumer exist on the model record:
   `reload_seq` and `consumer_seq` present (non-empty, non-sentinel).
8. The three-hop hash triple is pairwise equal over real hashes:
   `mem_write_hash == reload_data_hash == consumer_hash`, each a real hash
   (§3 absent-hash sentinels `null`/`none`/`0`/empty can neither establish
   the equality nor verify a hop) — the corrupted SQ-entry data reached
   the memory write, was read back by the reload, and was consumed.
9. The platform data rule on the reload's delivery edge holds:
   `WritebackValueFnv == ConsumerInputFnv`, both real hashes.

**E3 — SQ03 (`sq03_effect`), mechanism
`SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT`:**

6. `canwb_state_changed = 1` — the fault actually moved the canWB bit
   (`canwb_before != canwb_after` at runtime).
7. The visibility violation is time-proven: `drain_tick` and `commit_tick`
   both present and numeric, both > 0, and `drain_tick < commit_tick` (the
   store drained to memory strictly before architectural commit; a zero
   `drain_tick` records "no drain" and never satisfies the inequality).
8. `visible_before_commit = 1`.
9. A bound reload exists with a real data hash: `reload_seq` present
   (non-empty, non-sentinel) and `reload_data_hash` a real hash — the
   pre-commit drain was actually read by the reload.
10. The platform data rule on the reload's delivery edge holds:
    `WritebackValueFnv == ConsumerInputFnv`, both real hashes.

**E4 — SP05 (`sp05_stage`), mechanism
`STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED`:**

6. `write_skipped = 1` — the premature completion actually skipped the
   store's write to memory.
7. A bound reload exists with a real data hash: `reload_seq` present
   (non-empty, non-sentinel) and `reload_data_hash` a real hash — the
   reload read the word memory still held after the skipped write (the
   stale word). `store_data_fnv` is honestly `null` in this binary (the
   field's wiring is unimplemented) and is deliberately NOT a condition:
   E4 never claims the store-side data question was answered, only that
   the write was skipped and the reload read something that failed the
   oracle.
8. The platform data rule on the reload's delivery edge holds:
   `WritebackValueFnv == ConsumerInputFnv`, both real hashes.

When any condition fails, the record follows §6 exactly as before
(`LIFECYCLE_ONLY` under rule 4, `PARTIAL` under rule 5). E2/E3/E4 do
**not** change `FaultEffectPropagationCoverage`: the field keeps whatever
the platform graded (`LIFECYCLE_ONLY` for these chains); the exceptions
only stop that value from forcing the classification down.

### 11.4 Relation to §4 (single-context corroboration) and the record fields

Unlike E1 (§10.4, where the researcher's binding ruling grades the LQ04
record `COMPLETE_CAUSAL_CHAIN` directly per record), E2/E3/E4 sit at the
rule-3 layer and **do not bypass §4**: the conjunction establishes the
complete-chain predicate, and the context count decides the value exactly
as for every generic complete verdict — one verified model-record chain in
the pilot's own trace → `VERIFIED_SINGLE_CONTEXT`; two or more distinct
frozen contexts with a verified complete chain → `COMPLETE_CAUSAL_CHAIN`
at model level (closure matrix). Each proven model-record chain counts as
one verified chain (`VerifiedChainCount` is at least 1 when the exception
fires). For the v3.2.12 eligible runs this yields five distinct frozen
contexts per model (R01B..R05B, one pilot identity each), so the
model-level verdict is `COMPLETE_CAUSAL_CHAIN`; the C01B controls remain
`UNRESOLVED` (`NO_INJECTION`) and never contribute a context.

E2/E3/E4 add two record fields, emitted by the tool from the same §11.3
conjunction (a matrix or report may quote them but never set them):

- `ModelRuleRecord` — the exported model rule record (`event_type` plus
  its detail `fields`, verbatim), `null` when the model emits no rule
  record on the chain;
- `ChainMechanism ∈ {SQ_ENTRY_DATA_CORRUPTION_MEM_RELOAD_CONSUMER,
  SQ_CANWB_VISIBILITY_MOVED_DRAIN_BEFORE_COMMIT,
  STORE_COMPLETION_SKIPPED_STALE_RELOAD_CONSUMED, NOT_APPLICABLE}` — the
  former exactly when the model's E2/E3/E4 conjunction fires, the latter
  otherwise (including every non-SQ-family record).

`MaskingMechanism` (§10.4) is unchanged and stays `NOT_APPLICABLE` for
E2/E3/E4 records: E3's visibility mechanism is named by `ChainMechanism`,
and E1 remains the only source of a masking mechanism.

---

Per-pilot record layout, sources, evidence requirements, and the per-field
mapping rules are specified in
`audit_v3_2_12/pilot_record.schema.md`, which is normative with this document.
