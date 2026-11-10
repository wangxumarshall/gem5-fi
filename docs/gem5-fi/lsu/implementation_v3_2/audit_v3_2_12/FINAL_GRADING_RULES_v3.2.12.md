# FINAL GRADING RULES — LSU v3.2.12 terminal-grading closure (E5/E6/E7 + the frozen prior-audit import)

**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Authority:** standard `LSU_Propagation_Acceptance_Standard_v3.2.12.md`
§6 clause 3d + §12 (frozen amendment 2026-11-11, recorded through the
standard's own revise path); every rule below is computed by
`tools/lsu_12model_closure.py` from proven runtime records — **no matrix,
Excel cell or report may apply any of them by hand**. This file records each
exception's exact conjunction and the resulting per-model class; it cites,
never replaces, the standard.

---

## 1. The three model-scoped terminal exceptions (§12.3 conjunctions, verbatim from the tool)

Placement: evaluated in `final_classification` BEFORE rule 1's integrity
gates, because each exception names the integrity state it relaxes. Every
condition is a proven runtime record — no upgrade on inference. An INVALID
record stream is never excepted; only the TRUNCATED shapes named below are.

### E5 — RP01 HANG/TIMEOUT (mechanism `REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT`)

Fires when ALL hold:

1. `ModelID = RP01` and `ObservedTerminal ∈ {HANG, TIMEOUT}`;
2. `InjectionVerified = yes`, `ActivationVerified = yes`,
   `FaultCausality = PROVEN` — proven through the identity-linked
   replay/skip record on the fault's own chain (`replay`/`rp01_skip` among
   the chain kinds, §2 identity);
3. the RP01 watchdog record exists: the pilot sidecar
   `lsq_fwd_injections.log` (fallback `stdout.log`) carries the
   `CHAOS_RP01_WATCHDOG=EXPIRED` line with `injected=1` (parsed verbatim
   into the record's `RP01Watchdog` field);
4. the partial trace is retained (≥1 chain event survived the fatal cut);
5. `RecordIntegrity ≠ INVALID`.

Result: a complete verdict (§4 unchanged: `VERIFIED_SINGLE_CONTEXT` per
pilot; model-level `COMPLETE_CAUSAL_CHAIN` with ≥2 distinct frozen contexts)
with `ObservedTerminal=HANG/TIMEOUT` — **even though
`RecordIntegrity=TRUNCATED` and `TraceCompleteness=INCOMPLETE`; both fields
keep their honest platform values.** A SQUASHED RP01 run never fires E5 and
stays `PARTIAL` (the frozen v3.2.11 line) unless the squash trigger is
identity-linked.

### E6 — A03 CRASH (mechanism `STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH`)

Fires when ALL hold:

1. `ModelID = A03`, `ObservedTerminal = CRASH`,
   `InjectionVerified`/`ActivationVerified` = yes,
   `RecordIntegrity ≠ INVALID`;
2. the F5 activation record is present (run-level `a03_activation`) and at
   least one `a03_stream` record sits on the fault's own chain;
3. the `simulator_abort` node records a real panic page-table fault VA;
4. the identity-linked DIRECT_ADDRESS_MATCH: the panic VA equals the
   `actual_ea` of an on-chain `a03_stream` record with `affected=1`, and
   the abort's `last_injection_dyn_seq` equals that record's
   `dyn_inst_seq` (when the abort records it).

Result: a complete verdict with `ObservedTerminal=CRASH`, even though the
crash cut the record (`RecordIntegrity=TRUNCATED`; the structural chain
stays PARTIAL because the panic is the terminal). **A TRUNCATED crash-cut
trace no longer forces UNRESOLVED when the address match is
identity-linked**; a crash whose panic VA matches nothing on the chain
(e.g. A01's R01C panic VA `0`) stays `UNRESOLVED` under rule 1.

### E7 — A01 wrong-EA chain (mechanism `WRONG_EA_LOAD_DELIVERED_AND_CONSUMED`) and its discard companion

Complete branch, fires when ALL hold:

1. `ModelID = A01`, `InjectionVerified`/`ActivationVerified` = yes;
2. the on-chain `a01_ea` record proves a wrong EA: `golden_ea != actual_ea`
   (both real) and `affected=1`;
3. either
   - **MASKED branch:** `ObservedTerminal = MASKED` over the §6 invariant
     set (VALID/COMPLETE/structurally COMPLETE/`FaultCausality=PROVEN`), with
     an on-chain `memory_response`, a verified `register_writeback`, the
     §3 platform data rule on the consumer edge
     (`WritebackValueFnv == ConsumerInputFnv`, both real), and the on-chain
     `a01_consumed` record whose `input_hash` equals that same writeback
     hash; or
   - **CRASH branch:** `ObservedTerminal = CRASH` with the panic VA equal
     to the on-chain `a01_ea` `actual_ea` (the direct match;
     `RecordIntegrity ≠ INVALID`).

Discard companion, fires when ALL hold: `ModelID = A01`,
`ObservedTerminal = UNRESOLVED`, the injection verified/activated, and the
on-chain `a01_ea_discarded` record carries `applied_to_request=0` (the
runtime proof the corrupted EA never reached a Request). Result:
**`PARTIAL`** (§1.8 — real on-chain evidence, the discard naming the
missing link), never `UNRESOLVED`, never a complete verdict.

R03 with `a01_ea_discarded` therefore stays `PARTIAL`; R01's
temporal-association-only crash (panic VA `0` ≠ on-chain actual EA
`7ffffefd98`) fires nothing and stays `UNRESOLVED`.

---

## 2. The keyed frozen prior-audit import (§12.5 — DA04/LP01/MD04/FW05 are never re-graded)

The frozen v3.2.11 audit already verified the four models per pilot
(`audit_v3_2_11/{DA04,LP01,MD04,FW05}_verdict.json`); re-grading them with
the v3.2.12 generic classifier would only under-report them (§3/T4: the
generic `value_divergence` analysis does not bind the model-specific
records). The `frozen` subcommand imports their per-pilot verdicts as
closure records, **keyed by (model + binary SHA + evidence path)**, the key
enforced loudly:

- a supplied `--model` key that mismatches the verdict file is refused;
- every imported pilot must carry a 64-hex `binary_sha` and a non-empty
  `evidence_path` (an incomplete key is refused);
- `--binary-sha` imports only the pilots recorded under that binary — a key
  the file carries no pilot under is refused ("the import is keyed by
  binary and refuses to import a different binary's verdicts");
- the imported record carries the prior verdict **verbatim**
  (`FinalClassification` = the prior classification,
  `ObservedTerminal`/`ApplicationOracle` = the prior terminal/oracle, the
  prior stages and `classification_rule`) plus `PriorAudit="v3.2.11"`; the
  five §1 fields the prior audit did not record per pilot
  (`RecordIntegrity`, `TraceCompleteness`, `StructuralChainCompleteness`,
  `FaultEffectPropagationCoverage`, `FaultCausality`) are the literal
  `NULL` — never fabricated, never re-derived.

`matrix`/`features` take the frozen JSONs via `--frozen-prior`: a frozen
group supersedes the generic records of the **same (model, binary) key
only** (excluded with a loud note, never merged — no double count) and never
touches any other binary's records. `--frozen-prior` also refuses a plain
generic records file (no `PriorAudit` marker). Tests pinning the keying:
`test_frozen_import_is_keyed_by_model_and_binary`,
`test_frozen_import_supersedes_only_the_same_binary_key`.

Imported artifacts: `audit_v3_2_12/{LP01,DA04,MD04,FW05}_frozen_records_v3.2.11.json`
(22 records; supersession notes printed by the regeneration run).

---

## 3. Resulting per-model classes (deterministic tool output, 2026-11-11 regeneration)

Matrix `LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv` — 32 rows (one
per (model, binary) group), 173 merged records; feature dataset
`LSU_12Model_Diagnostic_Feature_Dataset_v3.2.12.csv` — 607 rows (173
`PILOT` + 434 `PATH_FRAGMENT`). Validation: 0 blank cells, 0 bare `PASS`
outside `ApplicationOracle`, 0 complete-over-unverified defects, 0
`BINARY_SHA_MISMATCH`.

| Model | Row (binary) | FinalClassification (matrix cell) | Reading |
|---|---|---|---|
| **RP01** | `RP01` (68c6ce73) | `mixed(COMPLETE_CAUSAL_CHAIN=3;PARTIAL=2;UNRESOLVED=5)` | **Model-level COMPLETE_CAUSAL_CHAIN (E5)** — R01/R04/R05 HANG contexts (ordinals 1/4/5) each grade VERIFIED_SINGLE_CONTEXT with `REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT`; R02/R03 stay PARTIAL (SQUASHED, `fault_caused=0`); 5 controls UNRESOLVED by design |
| **A03** | `A03@68c6ce73` | `mixed(COMPLETE_CAUSAL_CHAIN=5;UNRESOLVED=2)` | **Model-level COMPLETE_CAUSAL_CHAIN (E6)** — all five crash contexts DIRECT_ADDRESS_MATCH (panic VA == on-chain `a03_stream.actual_ea`, 5/5) with `STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH`; 2 controls UNRESOLVED. Older vintages (0fa610c2/275111d8/720eb780) stay UNRESOLVED — no stream/abort evidence in their traces |
| **A01** | `A01@68c6ce73` | `mixed(COMPLETE_CAUSAL_CHAIN=3;PARTIAL=1;UNRESOLVED=3)` | **Model-level COMPLETE_CAUSAL_CHAIN (E7)** — R02C/R04C/R05C wrong-EA MASKED contexts with `WRONG_EA_LOAD_DELIVERED_AND_CONSUMED`; R03C PARTIAL (discard companion); R01C UNRESOLVED (temporal-only crash, panic VA 0); 2 controls UNRESOLVED |
| A01 | `A01@720eb780` | `mixed(COMPLETE_CAUSAL_CHAIN=3;UNRESOLVED=4)` | E7 also fires on the old-binary Task-7 reruns (their traces carry `a01_ea`+`a01_consumed`): R02/R04/R05 complete; R03 stays UNRESOLVED there (no `a01_ea_discarded` node in that vintage) — keyed to its own row, never merged with 68c6ce73 |
| **DA04** (frozen) | `DA04@0de25644` | `COMPLETE_CAUSAL_CHAIN` (2/2) | **2/5 COMPLETE** — the prior audit's two complete frozen contexts (R04/R05, `DISABLED_LANE_REACHED_CONSUMER_AND_ORACLE_FAILED`) under the verified binary; `DA04@3e9148fc` carries the prior PARTIAL/LIFECYCLE_ONLY verdicts of the older vintage (0/5 complete there) |
| **LP01** (frozen) | `LP01@0de25644` | `COMPLETE_CAUSAL_CHAIN` (5/5) | **5/5 COMPLETE** — all five prior MASKED verdicts (`MODEL_SPECIFIC_ORIG_VS_INJ_DIVERGENCE_WITH_CONSUMER`) |
| **MD04** (frozen) | `MD04@0de25644` | `mixed(COMPLETE_CAUSAL_CHAIN=3;PARTIAL=2)` | **3/5 COMPLETE** — R02/R03/R05; R01/R04 squash-causality unproven per the prior audit |
| **FW05** (frozen) | `FW05@8377c011` | `mixed(COMPLETE_CAUSAL_CHAIN=4;PARTIAL=1)` | **4/5 COMPLETE** — R02–R05 (SDC); R01 squash-causality unproven per the prior audit |
| LQ04 | `LQ04` | `mixed(COMPLETE_CAUSAL_CHAIN=5;UNRESOLVED=5)` | E1 (§10), unchanged this round |
| SQ01/SQ03/SP05 | `@720eb780` | `mixed(COMPLETE_CAUSAL_CHAIN=5;LIFECYCLE_ONLY=5;UNRESOLVED=2)` each | E2/E3/E4 (§11), unchanged this round |
| FW02 | `FW02@720eb780` | `mixed(COMPLETE_CAUSAL_CHAIN=2;PARTIAL=3;UNRESOLVED=2)` | generic ≥2-context upgrade (§4), unchanged |

Per-pilot verdict artifacts re-recorded with the tool (no hand edits):
`audit_v3_2_12/A01_verdict_v3.2.12_v3.json`,
`A03_verdict_v3.2.12_v3.json`,
`RP01_records_v3.2.12.binary-68c6ce73.json` — the RP01 HANG pilots now read
`VERIFIED_SINGLE_CONTEXT`/HANG/`REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT`
(superseding the Task-15 "honest cap" UNRESOLVED reading, which was correct
under the pre-§12 rules), the A03 fault runs
`VERIFIED_SINGLE_CONTEXT`/CRASH/`STUCK_EA_PANIC_VA_DIRECT_ADDRESS_MATCH`
(superseding the pre-§12 UNRESOLVED), and A01 R02C/R04C/R05C
`VERIFIED_SINGLE_CONTEXT`/MASKED with R03C `PARTIAL` (the discard
companion's §1.8 grade).

## 4. Reproduction

```bash
# one record group (repeat per CLOSURE_RUNBOOK_v3.2.12.md sections 2.1/2.2;
# the regeneration of 2026-11-11 rebuilt all 33 groups into
# audit_v3_2_12/*_records_v3.2.12.binary-*.json)
python3 tools/lsu_12model_closure.py record --model RP01 \
  --pilot-dir pilots_v3_2_12/RP01-R01 ... --binary-sha 68c6ce73... \
  --json audit_v3_2_12/RP01_records_v3.2.12.binary-68c6ce73.json
# the frozen imports (keyed by model + binary SHA + evidence path)
python3 tools/lsu_12model_closure.py frozen \
  --prior audit_v3_2_11/LP01_verdict.json \
  --json audit_v3_2_12/LP01_frozen_records_v3.2.11.json
# the matrix + feature dataset (frozen groups supersede only their own key)
python3 tools/lsu_12model_closure.py matrix --records ... \
  --frozen-prior audit_v3_2_12/LP01_frozen_records_v3.2.11.json ... \
  --out audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv
python3 tools/lsu_12model_closure.py features --records ... \
  --frozen-prior ... --out audit_v3_2_12/LSU_12Model_Diagnostic_Feature_Dataset_v3.2.12.csv
```

Tests: `tests/test_lsu_12model_closure.py` — 36 passed (11 new §12/§12.5
tests: E5 fires + every guard removed; E6 fires + every guard removed; E7
MASKED/CRASH-direct/discard companion + every guard removed; model scoping;
the frozen import's verbatim carry, NULL absences, model/binary key
refusals, same-key supersession and different-binary non-override).
