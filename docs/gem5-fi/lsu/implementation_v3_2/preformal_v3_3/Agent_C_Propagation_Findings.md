# Agent C — Causal Closure Audit of the 60 Formal Contexts (2026-11-11)

**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Scope:** 12 models × R01–R05 = 60 formal contexts (A01, A03, FW02, FW05,
SQ01, SQ03, SP05, DA04, LP01, MD04, LQ04, RP01). The 74-model baseline is
out of scope.
**Mode:** read-only analysis; no gem5 run, no edit to verdicts/records/matrix.
**Outputs (written by this audit only):**
- `preformal_v3_3/LSU_Propagation_Closure_Final.csv` (60 rows)
- `preformal_v3_3/LSU_Diagnostic_Features_Final.csv` (2,355 rows, 5 feature groups)
- `preformal_v3_3/Agent_C_Propagation_Findings.md` (this file)

**Authorities read first:** `LSU_Propagation_Acceptance_Standard_v3.2.12.md`
(E1–E7, §2 identity rules, §3 data rule, §4 single-context rule, §5 terminal
rule, §12.5 frozen import), `audit_v3_2_12/FINAL_GRADING_RULES_v3.2.12.md`,
`audit_v3_2_12/pilot_record.schema.md`.

---

## 1. Method and keying

1. Each (model, context) was mapped to the **actual SampleRunID and evidence
   directory** used by the v3.2.12 closure (see the ContextNote column). SUPP/
   relabelled contexts are identified and their relation to the original
   ordinal is stated; no evidence was merged across binary SHAs.
2. Every trace (`trace_v31.jsonl`) was parsed independently. For each context
   the audit extracted: the injection event; the first divergence record; the
   memory request/response; the register writeback (or store writeback /
   store-mem-write); the consumer commit; the commit/errant-commit or
   squash/replay/abort; the model-specific rule record; and the run summary.
3. An edge was accepted only on a §2 identity (`ptag`, `dyn_inst_seq`,
   `(lq_entry_id, generation)`, `(sq_entry_id, generation)`,
   `(execution_attempt_id, replay_generation)`) **and** the §3 data rule
   (`WritebackValueFnv == ConsumerInputFnv`, both real hashes; for store models
   the reload's `data_fnv == writeback_value_fnv == consumer_input_fnv`).
   Time adjacency alone was never used.
4. A chain was never accepted as "injection happened + oracle failed". All
   complete rows carry the linking event IDs in `RecordIDs` and the hash/EA
   values in `DataHashBefore`/`DataHashAfter`, `ConsumerSeq`, `CommitSeq`.
5. Verdict fields (`TerminalState`, `RecordIntegrity`, `TraceCompleteness`,
   `FaultCausality`) are the frozen record values except where noted; for the
   three frozen models with raw traces on disk (DA04, LP01, MD04) the three
   integrity/quality fields were re-derived from the trace and the prior record
   keeps its literal NULL (§12.5) — flagged in ContextNote. FW05 keeps NULL
   because its raw trace is absent.

### 1.1 Binary keying (never merged)

| Binary | Role | Contexts |
|---|---|---|
| `68c6ce73…` | **FINAL** (per `LSU_v3.2.12_Final_Acceptance_Report.md`) | A01 R01–R05 (C-reruns), A03 R01–R05 (C-reruns), RP01 R01–R05 — **15** |
| `720eb780…` | v3.2.12 pre-final | FW02 R01–R05, SQ01/SQ03/SP05 R01–R05 (B-reruns) — **20** |
| `8377c011…` | v3.2.7 formal for FW05 | FW05 R01–R05 — **5** |
| `0de25644…` | v3.2.11 formal (frozen) | LP01 R01–R05, MD04 R01–R05, DA04 R04–R05 — **12** |
| `3e9148fc…` | v3.2.11 older vintage | DA04 R01–R03 — **3** |
| `f3c2a442…` | v3.2.10 formal for LQ04 | LQ04 R01–R05 — **5** |

**45 of 60 formal contexts are evidenced only on a non-final binary.** Each is
keyed to its own BinarySHA256 row in the CSV; no chain crosses a SHA boundary.

### 1.2 Context relabelling (same dynamic context?)

- **A01/A03 "C" reruns (`SUPP-A0x-RnnC`)** are final-binary reruns with the
  **same seed and ordinal** as the `720eb780` `SUPP-A0x-Rnn` series (seeds
  verified: 2108120075 / 1113826800 / 1302709433 / 2194451614 / 3228552887 for
  A01; 663646247 / 1626885462 / 110775855 / 2766846323 / 1156093484 for A03).
  They target the same dynamic event ordinal; they are a different binary, so
  they are separate chains by construction.
- **SQ01/SQ03/SP05 "B" reruns** are the ordinal-reselected eligible runs
  (K\* = 1006 / 1009 / 940): the store ordinal was moved into the workload's
  reload-consumed buffer `[0x491990, 0x492190)`. Same seed/ordinal index as the
  original `SUPP-Rnn`, **but a different target store event** (e.g. SQ01
  `store_seq` 12108 vs the startup-store ordinal of the original run). These B
  runs are the formal evidence for the three SQ-family models.
- **FW02 `SUPP-Rnn`** is the `720eb780` supplementary rerun; same seed/ordinal
  as the original FW02 pilot; the formal evidence for FW02.
- **DA04** mixes vintages: R01–R03 on `3e9148fc`, R04–R05 on `0de25644`
  (separate frozen records, never merged).
- **LQ04** is the v3.2.10 formal set on `f3c2a442`; not rerun on the final
  binary.

---

## 2. Closure tally

### 2.1 Per terminal (60 contexts)

| Terminal | n | Closure distribution |
|---|---|---|
| SDC | 16 | COMPLETE_CHAIN_EXCEPTION 10 (SQ01×5, SP05×5) · COMPLETE_CHAIN_FROZEN_PRIOR 6 (FW05 R02–R05, DA04 R04–R05) |
| MASKED | 25 | COMPLETE_CHAIN_EXCEPTION 13 (A01 R02/R04/R05, SQ03×5, LQ04×5) · COMPLETE_CHAIN_FROZEN_PRIOR 8 (LP01×5, MD04 R02/R03/R05) · COMPLETE_CHAIN 2 (FW02 R03/R04) · LIFECYCLE_ONLY 2 (DA04 R02/R03) |
| SQUASHED | 8 | PARTIAL 8 (FW02 R01/R05, FW05 R01, DA04 R01, MD04 R01/R04, RP01 R02/R03) |
| CRASH | 7 | COMPLETE_CHAIN_EXCEPTION 5 (A03 R01–R05, E6) · UNRESOLVED 2 (A01 R01, FW02 R02) |
| HANG | 3 | COMPLETE_CHAIN_EXCEPTION 3 (RP01 R01/R04/R05, E5) |
| UNRESOLVED | 1 | PARTIAL 1 (A01 R03, E7 discard companion) |

### 2.2 Per model

| Model | Contexts | Closure distribution | Terminals | Binary role |
|---|---|---|---|---|
| A01 | 5 | EXCEPTION 3, PARTIAL 1, UNRESOLVED 1 | MASKED 3, CRASH 1, UNRESOLVED 1 | FINAL |
| A03 | 5 | EXCEPTION 5 (E6) | CRASH 5 | FINAL |
| FW02 | 5 | COMPLETE 2, PARTIAL 2, UNRESOLVED 1 | MASKED 2, SQUASHED 2, CRASH 1 | non-final |
| FW05 | 5 | FROZEN_PRIOR 4, PARTIAL 1 | SDC 4, SQUASHED 1 | non-final |
| SQ01 | 5 | EXCEPTION 5 (E2) | SDC 5 | non-final |
| SQ03 | 5 | EXCEPTION 5 (E3) | MASKED 5 | non-final |
| SP05 | 5 | EXCEPTION 5 (E4) | SDC 5 | non-final |
| DA04 | 5 | FROZEN_PRIOR 2, LIFECYCLE_ONLY 2, PARTIAL 1 | SDC 2, MASKED 2, SQUASHED 1 | non-final (2 vintages) |
| LP01 | 5 | FROZEN_PRIOR 5 | MASKED 5 | non-final |
| MD04 | 5 | FROZEN_PRIOR 3, PARTIAL 2 | MASKED 3, SQUASHED 2 | non-final |
| LQ04 | 5 | EXCEPTION 5 (E1) | MASKED 5 | non-final |
| RP01 | 5 | EXCEPTION 3 (E5), PARTIAL 2 | HANG 3, SQUASHED 2 | FINAL |

All 60 rows have 0 blank cells; all 60 EvidencePaths exist on disk.

---

## 3. Contexts with missing consumer/terminal edges

**Squash before any consumer/commit (PARTIAL):** FW02 R01/R05, FW05 R01,
DA04 R01, MD04 R01/R04, RP01 R02/R03. In each case the writeback exists (or the
squash is on the faulting `dyn_inst_seq`) but the trace proves no consumer and
no faulting-instruction commit; the squash trigger is not identity-linked to
the injection.

**Crash terminal with the consumer/commit absent by construction:**
A03 R01–R05 (the crashing load is the terminal; E6 supplies the direct address
match at a later F5-affected load) and RP01 R01/R04/R05 (HANG; E5 supplies the
watchdog proof). Two crashes remain genuinely unattributed:
- **A01 R01**: the dataflow chain does reach a consumer
  (`a01_consumed.input_hash = writeback_value_fnv = f971edcd05e4ccc2`), but the
  panic VA is `0` while the on-chain `a01_ea.actual_ea` is `0x7ffffefd98`
  (temporal association only), and the oracle log is malformed (`ORACLE_FAIL:
  no checksum line`). E7's crash branch does not fire → UNRESOLVED.
- **FW02 R02**: panic VA `0x409c80` ≠ injection VA `0x496798`;
  `address_match=False` → UNRESOLVED.

**No consumer because the store lane is never read (LIFECYCLE_ONLY):**
DA04 R02/R03 — the store commits and the byte-enable-masked write reaches
memory (`store_writeback`/`store_mem_write` events present) but no reload
consumes the lane; prior classification LIFECYCLE_ONLY.

**Corrupted EA never reached a Request (PARTIAL, discard companion):**
A01 R03 — `a01_ea_discarded.applied_to_request=0`,
`discard_reason=saved_request_reuse`; no memory request/response, no writeback,
no consumer. The `a01_golden_resp` node is reference-only.

**Store commit not observed although the chain is complete:** SP05 R01–R05 —
`sp05_stage.commit_tick=0` and no `commit` node for the store; E4 completes the
verdict from `write_skipped=1` + a real reload hash + the reload delivery-edge
hash equality. `CommitSeq` is therefore recorded as `n/a (store commit not
observed; sp05_stage commit_tick=0)` rather than a fabricated zero.

---

## 4. Model status

### A01 — FINAL binary (E7): 3 complete, 1 partial, 1 unresolved
- R02/R04/R05: wrong EA delivered and consumed. `a01_ea` golden≠actual,
  `affected=1`; response → writeback → consumer hash equality holds
  (`a8c7…`, `1505…`, `9874…`); oracle PASS (MASKED); E7
  `WRONG_EA_LOAD_DELIVERED_AND_CONSUMED`.
- R03: discard companion → PARTIAL.
- R01: crash not attributable (panic VA 0), oracle malformed → UNRESOLVED.
- Same-seed `720eb780` reruns independently reproduce R02/R04/R05 complete
  (their keyed row), but are not merged with the final-binary row.

### A03 — FINAL binary (E6): 5/5 complete
- Every context: F5 activation record present, on-chain `a03_stream` for the
  crashing load `dyn_inst_seq=1014` with `affected=1`,
  `actual_ea=0xffffffffffb73c50`, and `simulator_abort.page_table_fault_addr`
  equal to that VA, `last_injection_dyn_seq=1014`, `address_match=True`.
  Events: stream 1456/1453/1445/1440/1437; abort 1471/1468/1460/1455/1452.
- The crash load is a **later F5-affected load**, not the ordinal anchor load
  (seq 48 or 253); this is stated in ContextNote. The platform record keeps
  `RecordIntegrity=TRUNCATED`, `StructuralChainCompleteness=PARTIAL`,
  `FaultCausality=UNPROVEN`; E6 supplies the identity-linked direct match and
  the CSV reports the record's UNPROVEN value verbatim.

### FW05 — v3.2.7 binary, raw trace absent: 4/5 prior-complete, R01 open
- R02–R05: prior v3.2.11 audit records complete chains — forwarding decision
  (events 5047/5062/5075/5088), writeback (5048/5063/5076/5089), consumer
  (5055/5070/5083/5096) with `input_fnv == writeback_value_fnv`, commit seqs
  5810/5829/5848/5867, oracle FAIL (`0x549c9e0347adaf23/f25/f27/f19` vs golden
  `0x67afad307642983e`).
- **Known-open verified:** R01 is SQUASHED before a consumer
  (`NO_CONSUMER_EDGE;NO_COMMIT_EVENT`), PARTIAL.
- **Evidence limitation:** `trace_v31.jsonl` is not on disk and no in-tree zip
  contains it; only the v3.2.7 checksum stubs
  (`pilots_v3_2_7/FW05_TRACE_STORAGE.md`) and `stdout.log` remain. The
  checksum values, event IDs, and hashes above are prior-audit quotes
  (`audit_v3_2_11/FW05_Propagation_Audit_v3.2.11.md`), not independently
  re-parsed now. `RecordIntegrity`/`TraceCompleteness`/`FaultCausality` are
  literal NULL per §12.5. The closure status is therefore
  `COMPLETE_CHAIN_FROZEN_PRIOR` / `PARTIAL`, with
  `RAW_TRACE_ABSENT` named in MissingEdges.

### RP01 — FINAL binary (E5): 3 HANG complete, 2 SQUASHED partial
- R01/R04/R05: `CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1`; identity-linked
  replay record on the fault's own `dyn_inst_seq` (all five contexts:
  25746/26677/26680/27192/27381 for R01–R05; R01/R04/R05 are HANG),
  `TraceCompleteness=INCOMPLETE`, `RecordIntegrity=TRUNCATED`, HANG terminal;
  E5 `REPLAY_TRIGGER_SUPPRESSED_WATCHDOG_TIMEOUT`.
- R02/R03: run completes with SQUASHED, no watchdog expiry; the squash is not
  identity-linked → PARTIAL (frozen v3.2.11 line).
- Oracle is NOT_APPLICABLE for the HANG contexts (no checksum line), PASS for
  R02/R03.

### SQ family (E2/E3/E4): 5/5 each on `720eb780`
- **SQ01 (E2):** `data_before != data_after` (0x61→0x69 … 0x65→0x6d),
  `mem_write_hash == reload_data_hash == consumer_hash` for every context
  (e.g. f86e18335679a771, 2a7c881ab831bd95, e6371a5feb48222d,
  a74045b6b4580b81, fff725544d920281); oracle FAIL.
- **SQ03 (E3):** `canwb 0→1`, `drain_tick < commit_tick`
  (`visible_before_commit=1`), reload hash real and equal to the reload
  writeback/consumer hash; oracle PASS (MASKED — the effect is the visibility
  move, not a data corruption).
- **SP05 (E4):** `write_skipped=1`, `completed_before=0→1`, store write and
  store writeback absent, reload reads the stale word
  (`reload_data_hash=a8c7f832281a39c5`), reload delivery-edge hash equality
  holds; oracle FAIL. `store_data_fnv` is honestly null in this binary and is
  not used as a condition.

### LQ04 (E1): 5/5 complete, MASKED, `RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE`
- `memory_response` and `register_writeback` both carry
  `association=sender_state`, `entry_valid_at_response=0`,
  `entry_request_at_response=0`, `data_unchanged=1`; response data hash equals
  writeback hash equals consumer input hash (e.g. c6d4496e17859d5); oracle PASS.
- Evidence is on `f3c2a442` (v3.2.10), not the final binary.

### DA04 — frozen prior (never merged across binaries)
- R04/R05 on `0de25644`: SDC complete. Store byte-enable `0xf→0xe`; store
  writeback `data_fnv` equals the store-mem-write packet hash
  (1079154960948788268 / 5037817100498823030); the reload response
  (`d9a56276a6025898` / `7cc505782442859c`) → register writeback
  (`a959f41d27dbce18` / `bdb2b3575183d5c`) → consumer input equals the
  writeback value; oracle FAIL at raw-meta level (raw oracle.log absent).
- R01 on `3e9148fc`: SQUASHED, no consumer → PARTIAL.
- R02/R03 on `3e9148fc`: store commits, masked lane never read → LIFECYCLE_ONLY.

### LP01 — frozen prior: 5/5 complete MASKED
Model-specific divergence `orig_data_fnv != inj_data_fnv` (e.g.
89cd…→81a3…, a8c7…→a09e…), then response = writeback = consumer input hash;
oracle PASS. Raw oracle.log absent (prior meta PASS; T3 MISSING at raw level).

### MD04 — frozen prior: 3 complete MASKED, 2 squash PARTIAL
R02/R03/R05: `violation_report_suppressed=1`, writeback = consumer input
(`a8c7f832281a39c5`), commit seqs 917/10911/63399; oracle PASS. R02/R03 also
carry the memory response (`a8c7f832281a39c5`); R05 has no memory-response node
on the chain (prior record flags `NO_EARLY_ANOMALY_EVENT`), so only the
writeback→consumer edge is hash-verified there.
R01/R04: SQUASHED before consumer, causality unproven → PARTIAL.

### FW02 — generic, `720eb780`
R03/R04: `fw02_decision normal=forwarded / fault=suppressed`, consumer input
equals writeback (`a8c7f832281a39c5`), commit seqs 4720/5121, oracle PASS →
complete. R01/R05: SQUASHED before consumer → PARTIAL. R02: crash at panic VA
`0x409c80` ≠ injection VA `0x496798` → UNRESOLVED.

---

## 5. Oracle-artifact status (raw level)

22 of 60 contexts have `OracleResult=MISSING` at the raw-artifact level:
- 7 crash/malformed: A01 R01, A03 R01–R05, FW02 R02 (`oracle.log` exists but
  says `ORACLE_FAIL: no checksum line`; record ApplicationOracle=MISSING);
- 15 frozen v3.2.11 pilots: DA04 R01–R05, LP01 R01–R05, MD04 R01–R05 (no
  `oracle.log` in the evidence directories; prior `pilot_meta` values are
  preserved in ContextNote: LP01/MD04 PASS; DA04 R01–R03 PASS, R04/R05 FAIL).
FW05 has no `oracle.log` either, but its `stdout.log` carries the raw checksum
(0x67af… PASS for R01; 0x549c… FAIL for R02–R05), so those are graded
PASS/FAIL.
All other contexts carry a raw `oracle.log` PASS/FAIL and were parsed verbatim.

---

## 6. Limitations / open items (honest)

1. **FW05 raw traces are unavailable.** Its four "complete" verdicts are prior
   v3.2.11 quotes, not a fresh chain re-parse; the checksum stubs cannot
   substitute for the trace. If the v3.2.7 delivery zip is restored, the
   R02–R05 chains should be re-parsed and R01's squash reason traced.
2. **45/60 contexts are on non-final binaries.** Only A01/A03/RP01 (15) have
   final-binary evidence in this round. Re-running SQ-family, FW02, DA04,
   LP01, MD04, LQ04, FW05 on `68c6ce73` is required before a single-binary
   claim can be made; until then each chain stays keyed to its own SHA.
3. **A03's platform `FaultCausality` is UNPROVEN** even though E6's direct
   address match is runtime-proven. The CSV reports the record value and names
   E6 in ContextNote/MissingEdges; this is a record-tool under-report, not a
   contradiction of the terminal.
4. **SP05 has no store-commit node** (`commit_tick=0`); the E4 verdict rests on
   `write_skipped=1` + stale reload + delivery-edge hash equality, exactly as
   §11.3 E4 defines. The store-side `store_data_fnv` is null by construction.
5. **DA04 R02/R03 and the squash contexts** are LIFECYCLE_ONLY/PARTIAL, not
   complete: the runtime proof that the masked lane was never read (or that
   the squash was fault-caused) is absent.
6. **DataHash columns are typed**: `EA:` for address-affecting models,
   `BYTE:`/`CANWB:`/`COMPLETED:` for store models, `CTRL:` for forwarding
   control decisions, `fnv:`/bare hex for real hashes, and `RESP_DATA:` for
   LQ04's unchanged response data. No absent value was written as a zero.

---

## 7. Regeneration

The analysis scripts were scratch-only under `/tmp/agentc` (not committed):
they streamed each `trace_v31.jsonl`, resolved records from
`audit_v3_2_12/*_records_*.json` / `*_verdict_*.json`, and wrote the two CSVs
above. No file outside the three outputs was modified; no gem5 process was
started. Validation of the outputs: 60/60 rows, 0 blank cells, 60/60 evidence
directories present, 2,355 feature rows with 0 blank values
(2,135 OBSERVED, 130 ABSENT, 60 ABSENT(RAW_TRACE_ABSENT), 30 PRIOR_ONLY).
