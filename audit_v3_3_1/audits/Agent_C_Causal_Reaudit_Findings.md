# Agent C — LSU 60-Context Causal-Chain Re-Audit (v3.3.1)

**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Scope:** the 60 formal (ModelID, ContextID) rows of the v3.3.0 package
(12 models × R01–R05), re-derived in v3.3.1 from raw evidence.
**Mode:** read-only. No gem5/gem5.opt, no scons, no edit to records, verdicts,
pilots, Excel or source. The only files written by this audit are:

- `audit_v3_3_1/propagation/LSU_60Context_Causal_Chain_Reaudit.csv` (60 rows × 19 cols)
- `audit_v3_3_1/audits/Agent_C_Causal_Reaudit_Findings.md` (this file)

**Inputs:** v3.3.0 package `B_Audits/Agent_C_Propagation_Findings.md`,
`A_Report/LSU_60Context_Readiness_Matrix.csv`,
`B_Audits/LSU_Propagation_Closure_Final.csv`, `E_Evidence/runs/*`; historical
pilots and record JSONs under `docs/gem5-fi/lsu/implementation_v3_2/`;
`LSU_Propagation_Acceptance_Standard_v3.2.12.md` and
`FINAL_GRADING_RULES_v3.2.12.md`.

---

## 0. Bottom line

1. **55 of 60 contexts have a raw `trace_v31.jsonl` in their own keyed
   evidence directory and were re-parsed from scratch in this round.** The
   earlier v3.3.0 audit only named raw-trace re-derivation for the three
   frozen models (DA04/LP01/MD04); in fact A01, A03, FW02, SQ01, SQ03, SP05,
   LQ04 and RP01 traces are also on disk and are now independently parsed.
2. **FW05 is the only model without a raw trace on its formal binary**
   (`8377c011`). Its R02–R05 chains remain prior-quoted (`RAW_TRACE_ABSENT`),
   but two same-seed supplementary traces on newer binaries (`e527f26a` and
   the final binary `d3807fbe`) now reproduce the chain natively. FW05-R01
   has no trace at any binary and its record contradicts the prior squash
   quote; it is left **UNRESOLVED**.
3. Chain classes (honest, terminal-aware):
   **MASKED 23 · SDC 16 · SQUASHED 7 · CRASH 5 · HANG 3 · UNRESOLVED 4 ·
   ARCH_STATE 2** (= 60). Terminal tally: MASKED 25 · SDC 16 · SQUASHED 7 ·
   CRASH 7 · HANG 3 · UNRESOLVED 2.
4. **No verdict was upgraded by hand.** Every class is anchored on an
   identity key (dyn_inst_seq / ptag / (lq|sq_entry_id, generation) /
   (attempt, replay_generation)) plus the data rule where a consumer exists.
   Time adjacency alone was never accepted.
5. Eight groups fail an edge: no consumer (10 contexts), no commit (7),
   squash not fault-causally proven (7), crash-VA mismatch (2), store commit
   not observed (SP05 ×5), store-side hash null (SP05 ×5), discard-before-
   request (A01-R03), missing writeback (3); plus raw-oracle absence (23)
   and malformed oracle (7). Details in §4.

---

## 1. Evidence mapping and binary keying (never merged)

The mapping is taken from `LSU_Propagation_Closure_Final.csv` and verified
against each directory's `manifest.json` / `pilot_meta.json` and the trace
header. **No chain crosses a SHA boundary.** 45/60 contexts are still on a
non-final binary; 15 are on the old "final" `68c6ce73`, which itself is
superseded by `d3807fbe` for formal.

| Model | Contexts | Keyed SampleRunID | Binary SHA256 (prefix) | Evidence dir | Raw trace |
|---|---|---|---|---|---|
| A01 | R01–R05 | `SUPP-A01-R01C` … `R05C` | `68c6ce73…` | `pilots_v3_2_12/SUPP-A01-R0xC` | yes (5/5) |
| A03 | R01–R05 | `SUPP-A03-R01C` … `R05C` | `68c6ce73…` | `pilots_v3_2_12/SUPP-A03-R0xC` | yes (5/5) |
| FW02 | R01–R05 | `SUPP-FW02-R01` … `R05` | `720eb780…` | `pilots_v3_2_12/SUPP-FW02-R0x` | yes (5/5) |
| FW05 | R01–R05 | `FW05-F6-W8-S01-R0x` | `8377c011…` | `pilots_v3_2_7/FW05-R0x` | **no (0/5)** |
| SQ01 | R01–R05 | `SUPP-SQ01-R0xB` | `720eb780…` | `pilots_v3_2_12/SUPP-SQ01-R0xB` | yes (5/5) |
| SQ03 | R01–R05 | `SUPP-SQ03-R0xB` | `720eb780…` | `pilots_v3_2_12/SUPP-SQ03-R0xB` | yes (5/5) |
| SP05 | R01–R05 | `SUPP-SP05-R0xB` | `720eb780…` | `pilots_v3_2_12/SUPP-SP05-R0xB` | yes (5/5) |
| DA04 | R01–R03 | `DA04-F0-W8-S02-R0x` | `3e9148fc…` | `pilots_v3_2_4/DA04-R0x` | yes (3/3) |
| DA04 | R04–R05 | `DA04-F0-W8-S02-R0x` | `0de25644…` | `pilots_v3_2_6/DA04-R0x` | yes (2/2) |
| LP01 | R01–R05 | `LP01-F0-W5-S01-R0x` | `0de25644…` | `pilots_v3_2_6/LP01-R0x` | yes (5/5) |
| MD04 | R01–R05 | `MD04-F6-W7-S01-R0x` | `0de25644…` | `pilots_v3_2_6/MD04-R0x` | yes (5/5) |
| LQ04 | R01–R05 | `LQ04-F0-W2-S01-R0x` | `f3c2a442…` | `pilots_v3_2_10/LQ04-R0x` | yes (5/5) |
| RP01 | R01–R05 | `RP01-F6-W7-S01-R0x` | `68c6ce73…` | `pilots_v3_2_12/RP01-R0x` | yes (5/5) |

### 1.1 Relabels (stated, not silently merged)

- **A01/A03 `…RnnC`** are final-binary (`68c6ce73`) reruns of the same seed
  and ordinal as the `720eb780` `SUPP-A0x-Rnn` series. They are a different
  binary, hence separate chains by construction. A01 seeds:
  2108120075 / 1113826800 / 1302709433 / 2194451614 / 3228552887. A03 seeds:
  663646247 / 1626885462 / 110775855 / 2766846323 / 1156093484.
- **SQ01/SQ03/SP05 `…RnnB`** are ordinal-reselected eligible reruns
  (K\* = 1006 / 1009 / 940) with the store moved into the reload-consumed
  buffer `[0x491990, 0x492190)`. Same seed index as the original pilot but a
  different target store event; they are the formal evidence for the
  SQ-family.
- **FW02 `SUPP-Rnn`** is the `720eb780` supplementary rerun with the same
  seed/ordinal as the original pilot.
- **DA04** mixes vintages: R01–R03 on `3e9148fc`, R04–R05 on `0de25644`.
- **FW05** is on the v3.2.7 binary `8377c011`; the e527f26a and d3807fbe
  traces discussed below are **supplementary, never merged**.

### 1.2 Evidence types (CSV column)

- `NATIVE_PARSE` — 55 rows, trace in the row's own evidence dir.
- `PRIOR_QUOTE` — 5 rows (FW05 R01–R05); no raw trace on `8377c011`.
  `RAW_TRACE_ABSENT` is named in `MissingEdges` for all five.

---

## 2. Method

For each context the audit extracted, from the raw trace:

Injection → activation → first divergence → memory request/response →
register writeback (or store writeback / store-mem-write) → consumer commit
→ faulting-instruction commit or squash/replay/abort → run summary and raw
`oracle.log`.

An edge was accepted only when the two records share a §2 identity key:

- `dyn_inst_seq` for load/forwarding/commit chains;
- `(lq_entry_id, entry_generation)` for LQ/replay chains;
- `(sq_entry_id, entry_generation)` for store chains;
- `(execution_attempt_id, replay_generation)` for replay chains;
- `ptag` where the trace supplies it.

and, where a consumer exists, the §3 data rule was checked numerically:

- load models: `writeback_value_fnv == consumer_input_fnv`;
- store models: `store_writeback.data_fnv == store_mem_write.packet_data_fnv`,
  and (where the reload is the same width/address) `reload.data_fnv ==
  consumer hash`; subword stores are recorded as `EDGE_WISE` and not
  overstated as triple equality.

`lastClock`/tick adjacency was never used as a substitute for identity.

---

## 3. Chain-class tally

### 3.1 Per class (60)

| ChainClass | n | Contexts |
|---|---|---|
| MASKED | 23 | A01 R02/R04/R05; FW02 R03/R04; SQ03 ×5; LP01 ×5; MD04 R02/R03/R05; LQ04 ×5 |
| SDC | 16 | FW05 R02–R05; SQ01 ×5; SP05 ×5; DA04 R04/R05 |
| SQUASHED | 7 | FW02 R01/R05; DA04 R01; MD04 R01/R04; RP01 R02/R03 |
| CRASH | 5 | A03 ×5 |
| HANG | 3 | RP01 R01/R04/R05 |
| UNRESOLVED | 4 | A01 R01/R03; FW02 R02; FW05 R01 |
| ARCH_STATE | 2 | DA04 R02/R03 (fault reached committed memory; lane never read) |

### 3.2 Per model

| Model | ChainClass distribution | Terminal distribution | Binary role |
|---|---|---|---|
| A01 | MASKED 3, UNRESOLVED 2 | MASKED 3, CRASH 1, UNRESOLVED 1 | `68c6ce73` |
| A03 | CRASH 5 | CRASH 5 | `68c6ce73` |
| FW02 | MASKED 2, SQUASHED 2, UNRESOLVED 1 | MASKED 2, SQUASHED 2, CRASH 1 | `720eb780` |
| FW05 | SDC 4, UNRESOLVED 1 | SDC 4, UNRESOLVED 1 | `8377c011` |
| SQ01 | SDC 5 | SDC 5 | `720eb780` |
| SQ03 | MASKED 5 | MASKED 5 | `720eb780` |
| SP05 | SDC 5 | SDC 5 | `720eb780` |
| DA04 | SDC 2, ARCH_STATE 2, SQUASHED 1 | SDC 2, MASKED 2, SQUASHED 1 | `3e9148fc` / `0de25644` |
| LP01 | MASKED 5 | MASKED 5 | `0de25644` |
| MD04 | MASKED 3, SQUASHED 2 | MASKED 3, SQUASHED 2 | `0de25644` |
| LQ04 | MASKED 5 | MASKED 5 | `f3c2a442` |
| RP01 | HANG 3, SQUASHED 2 | HANG 3, SQUASHED 2 | `68c6ce73` |

**"Injected" versus "affected":** all 60 have an observed injection except
FW05 (prior-quoted) and A01-R03 (injected but the corrupted EA was
discarded before Request construction). A03 is the clearest case where the
ordinal anchor injection is *not* the crashing load: the fault activates at
seq 48/253, but the CRASH terminal is a later F5-affected load at seq 1014.

---

## 4. Missing-edge census (contexts that fail each edge)

| Missing edge | n | Contexts |
|---|---|---|
| `NO_CONSUMER_EDGE` | 10 | FW02 R01/R05; DA04 R01/R02/R03; MD04 R01/R04; RP01 R02/R03 |
| `NO_COMMIT_EVENT` | 7 | FW02 R01/R05; DA04 R01; MD04 R01/R04; RP01 R02/R03 |
| `SQUASH_NOT_FAULT_CAUSALLY_PROVEN` | 7 | FW02 R01/R05 (`squash_cause=fault_victim_unproven`, `fault_caused=0`); DA04 R01; MD04 R01/R04; RP01 R02/R03 (`squash_cause=unrelated`, `fault_tracked=0`) |
| `CRASH_VA_MISMATCH` | 2 | A01 R01 (panic VA 0 vs on-chain EA `0x7ffffefd98`); FW02 R02 (panic `0x409c80` vs injection VA `0x496798`) |
| `ORACLE_MALFORMED` | 7 | A01 R01; A03 ×5; FW02 R02 (all ``ORACLE_FAIL: no checksum line``) |
| `RAW_ORACLE_ABSENT` | 23 | DA04 ×5; LP01 ×5; MD04 ×5; RP01 R01/R04/R05; FW05 ×5 |
| `RAW_TRACE_ABSENT` | 5 | FW05 R01–R05 |
| `STORE_COMMIT_NOT_OBSERVED` | 5 | SP05 ×5 (`sp05_stage.commit_tick=0`) |
| `STORE_SIDE_DATA_HASH_NULL` | 5 | SP05 ×5 (`store_data_fnv=null`) |
| `NO_REGISTER_WRITEBACK` | 3 | A01 R03; DA04 R01; MD04 R04 |
| `MEMORY_REQUEST_DISCARDED` | 1 | A01 R03 (`applied_to_request=0`, `discard_reason=saved_request_reuse`) |
| `NO_EARLY_ANOMALY_EVENT` | 1 | MD04 R05 (no `memory_response` on the chain; only writeback→consumer verified) |
| `CONSUMER/COMMIT_ABSENT_AT_CRASH_TERMINAL` | 5 | A03 ×5 (by construction; E6 supplies the address match) |
| `CONSUMER/COMMIT_ABSENT_AT_HANG_TERMINAL` | 3 | RP01 R01/R04/R05 (by construction; E5 watchdog) |
| `RECORD_SAYS_NO_INJECTION` | 1 | FW05 R01 |

---

## 5. Data-rule status

- **PASS (36):** A01 R01/R02/R04/R05; FW02 R02/R03/R04; SQ01 ×5; SQ03 ×5;
  LP01 ×5; MD04 R02/R03/R05; LQ04 ×5; DA04 R02/R03 (store-side data_fnv ==
  mem-write packet; no reload); FW05 R02–R05 (prior-quoted equality).
- **EDGE_WISE / PARTIAL (7):** SP05 ×5 (reload `a8c7f832281a39c5` == writeback
  == consumer, but `store_data_fnv=null` by construction); DA04 R04/R05
  (writeback value `a959f41d27dbce18` / `bdb2b3575183d5c` == consumer;
  store data == mem-write packet; the 4-byte store hash is not equal to the
  8-byte reload full-word hash — the masked lane must be compared bytewise,
  which the prior "triple equality" phrasing overstated).
- **n/a (17):** A01 R03; A03 ×5; FW02 R01/R05; FW05 R01; DA04 R01;
  MD04 R01/R04; RP01 ×5. No consumer or no data edge exists.

---

## 6. Record-integrity findings (record vs. raw trace)

`RecordIntegrity` values in the CSV: **MATCH 35, MATCH_CORE 3, UNDER_REPORT 5,
CONFLICT 5, FROZEN_NULL 12.**

1. **LQ04 duplicate SampleRunID in the records file.** Both
   `LQ04_f0…` entries exist: a CONTROL entry (`PilotID=LQ04-CONTROL-R01`,
   `EvidencePath=…/LQ04-CONTROL-R01`, `ObservedTerminal=NO_INJECTION`) and the
   FAULT entry (`PilotID=LQ04-R01`, `EvidencePath=…/LQ04-R01`,
   `VALID/MASKED/PROVEN`). They share the same `SampleRunID`
   (`LQ04-F0-W2-S01-R01`). Naive keying by SampleRunID yields a false
   "NO_INJECTION". The row must be keyed by EvidencePath/PilotID. This is a
   record-tool defect to fix before formal.
2. **A03 under-reports causality.** The `68c6ce73` record says
   `FaultCausality=UNPROVEN`, `StructuralChainCompleteness=PARTIAL`,
   `FaultEffectPropagationCoverage=LIFECYCLE_ONLY`, while the trace summary
   says `page_table_fault_after_injection_address_match` /
   `DIRECT_ADDRESS_MATCH` and the abort carries `address_match=True`. The
   forgiving E6 exception is what makes the terminal acceptable; the CSV
   reports the record value verbatim and names E6.
3. **A01 and SQ-family coverage under-report.** The records set
   `FaultEffectPropagationCoverage=LIFECYCLE_ONLY` even where the trace
   proves a hash-equal consumer (A01 R02/R04/R05; SQ01/SQ03/SP05 ×5 each).
   The closure classification is correct, but the coverage field is not a
   reliable indicator of chain completeness.
4. **FW05 record/quote conflict.** `FW05_records_v3.2.12.binary-8377c011.json`
   marks all five contexts `INVALID / NO_INJECTION / TERMINAL_UNRESOLVED /
   TRACE_FILE_MISSING`; the prior v3.2.11 audit quotes a SQUASHED chain for
   R01 and complete SDC chains for R02–R05. Both cannot describe the same
   trace because there is no trace on `8377c011`. The CSV keeps the formal
   row as `PRIOR_QUOTE` and flags `CONFLICT`.
5. **Frozen NULL is preserved.** LP01/MD04 and DA04 R04/R05 records are
   literal `NULL`; their integrity/quality fields in the CSV were re-derived
   from the on-disk trace (§12.5) and are marked `FROZEN_NULL`.

---

## 7. Model-specific specifics

### A01 (E7)
- R02/R04/R05: wrong EA (`7ffffefda8→7ffffefda0`, `…db0→…db8`,
  `…db8→…db0`), wrong EA delivered, writeback == consumer
  (`a8c7f832281a39c5`, `1505defdf2164c5b`, `987468c2d70edbd5`), faulting
  load commits, oracle PASS → MASKED.
- **R01**: the dataflow chain is *complete* through consumer
  (`f971edcd05e4ccc2`), commit seq 5, but the abort at ev 1011 has
  `page_table_fault_addr=0`, `address_match=False`. The CRASH is temporal
  only; oracle has no checksum line → UNRESOLVED.
- **R03**: `a01_ea_discarded` ev 25 (`applied_to_request=0`,
  `saved_request_reuse`); no request/response/writeback/consumer → UNRESOLVED
  (E7 discard companion).

### A03 (E6)
All five: anchor injection ev 25/21/22/111/107 (seq 48/253), activation ev
4/23/24/102/109, first affected stream at the anchor, then the crashing load
`dyn_inst_seq=1014` (`a03_stream` ev 1456/1453/1445/1440/1437,
`actual_ea=0xffffffffffb73c50`), abort ev 1471/1468/1460/1455/1452 with
`address_match=True` and `last_injection_dyn_seq=1014`. No consumer/commit
exists for the crashing load (CRASH is the terminal). The ordinal anchor load
does commit and is consumed, but that is a *different* dynamic instruction
from the crash load; the chain is accepted only on the E6 direct address
match.

### FW05
No raw trace on `8377c011` (only checksum stubs/logs). Prior-quoted chains:
R02 ev 5047/5048/5055, commit 5810; R03 5062/5063/5070, 5829; R04
5075/5076/5083, 5848; R05 5088/5089/5096, 5867; oracle FAIL
(`0x549c9e0347adaf23/f25/f27/f19` vs golden `0x67afad307642983e`). R01 is
left UNRESOLVED due to the record/prior conflict.

**Same-seed supplementary native parses (not merged):**
- `pilots_v3_2_12/SUPP-FW05-R02…R05` on `e527f26a`: injection ev
  5044/5059/5072/5085 (seq 12093/12128/12163/12198), writeback
  `a06ea71be9c5aa88` / `141ad82d6cd5f32f` / `fe9b431f6a056432` /
  `5b96aecb6003c639`, consumer ev 5053/5068/5081/5094 with equal input hash,
  commit 5797/5816/5835/5854, oracle FAIL `…f23/…f25/…f27/…f19`. Records:
  `VALID / SDC / PROVEN`.
- `E_Evidence/runs/V33F-FW05-R02` on the final binary `d3807fbe`: injection
  ev 5044 (seq 12093, old `12446998b6871244` → new `a06ea71be9c5aa88`),
  writeback ev 5046, consumer ev 5053 with
  `consumer_input_fnv=a06ea71be9c5aa88`, commit ev 5050, oracle FAIL
  `0x549c9e0347adaf23`. This independently corroborates the prior R02 chain
  on a newer binary.

### RP01 (E5)
- HANG R01/R04/R05: injection ev 25780/27214/27386 (`skipped_call=1`,
  suppressed partial-replay reschedule) at the same tick as replay ev
  25746/27192/27381 on the same `(lq_entry_id, entry_generation)`; no
  consumer/commit; run TIMEOUT and trace INCOMPLETE; stdout carries
  `CHAOS_RP01_WATCHDOG_EXPIRED … injected=1 eligible=1/4/5`.
- SQUASHED R02/R03: replay ev 26677/26680, then squash ev 26691/26689 with
  `fault_tracked=0`, `squash_cause=unrelated`, `fault_caused=0`. The squash
  is explicitly not fault-caused; the run completes with oracle PASS. These
  two are terminal SQUASHED but **not** a proven propagation chain.

### SQ family (E2/E3/E4)
- **SQ01** ×5: `data_before≠data_after` (`0x61→0x69`, …, `0x65→0x6d`);
  `mem_write_hash == reload_data_hash == consumer_hash`
  (`f86e18335679a771`, `2a7c881ab831bd95`, `e6371a5feb48222d`,
  `a74045b6b4580b81`, `fff725544d920281`); store commit observed; oracle
  FAIL → SDC.
- **SQ03** ×5: `canWB 0→1`, `drain_tick < commit_tick`,
  `visible_before_commit=1`; triple hash equality
  (`f6a2a263b2e746b9`, `69a6347498f3c2dd`, `fbbcba348bb2aaf5`,
  `781d22051fdb27f9`, `849c6aba106027e9`); oracle PASS → MASKED (the effect
  is the visibility move, not a data corruption).
- **SP05** ×5: `write_skipped=1`, `completed 0→1`, `commit_tick=0`;
  reload reads stale `a8c7f832281a39c5`; reload == writeback == consumer;
  `store_data_fnv=null`; oracle FAIL → SDC. The only open edge is the
  store-commit node; E4 defines the verdict without it.

### DA04
- R01 (`3e9148fc`): BE `0xf→0xe`; no writeback/mem-write before squash ev
  227 on the fault store; no consumer/commit → SQUASHED, causality unproven.
- R02/R03 (`3e9148fc`): store writeback data_fnv == mem-write packet hash
  (`5558979605539197941` / `12478008331234465636`); store commits; the
  masked lane is never reloaded → ARCH_STATE (LIFECYCLE_ONLY).
- R04/R05 (`0de25644`): store data == mem-write packet
  (`1079154960948788268` / `5037817100498823030`); reload payload hash
  `d9a56276a6025898` / `7cc505782442859c` → writeback value hash
  `a959f41d27dbce18` / `bdb2b3575183d5c` == consumer input. This is
  `EDGE_WISE`, not triple equality: a 4-byte store cannot hash equal to an
  8-byte reload word. Oracle raw log absent (prior meta FAIL) → SDC.

### LQ04 (E1)
Response == writeback == consumer hash (`c6d4496e17859d5`,
`46f9187bab44bc35`, `14fe41788a431ad5`, `4f8a555d540fe9f5`,
`f9468ffeedcb9ad5`), `association=sender_state`,
`entry_valid_at_response=0`, `data_unchanged=1`; oracle PASS → MASKED. The
duplicate CONTROL/FAULT record keying is the only integrity caveat.

### LP01 / MD04 (frozen)
LP01 ×5: model-specific `orig_data_fnv≠inj_data_fnv` then response ==
writeback == consumer; oracle raw absent (prior meta PASS) → MASKED.
MD04 R02/R03/R05: `violation_report_suppressed=1`, writeback == consumer
(`a8c7f832281a39c5`), commits 917/10911/63399; R05 has no memory_response
on chain. R01/R04: squash before consumer, causality unproven.

---

## 8. Final-binary (`d3807fbe`) supplementary evidence and controls

Raw traces in `E_Evidence/runs/` on `d3807fbe`:

| Run | Model/seed/ord | Result |
|---|---|---|
| `V33G-A01-R02` | A01 / 1113826800 / 2 | complete MASKED chain, ev 21/23/33/34/35/39, hash `a8c7f832281a39c5`; oracle PASS |
| `V33C-A03-R01`, `V33F-A03-R01` | A03 / 663646247 / 1 | CRASH, `DIRECT_ADDRESS_MATCH`, panic VA `0xffffffffffb73c50` == `a03_stream(seq1014).actual_ea`; abort ev 1472 (V33C) |
| `V33G-FW02-R01`, `V33-W4V33-FW02-R01` | FW02 / 2941542370 / 1 | SQUASHED, `squash_cause=unrelated`, `fault_caused=0` |
| `V33F-FW05-R02` | FW05 / 1653118510 / 2 | SDC complete chain, seq 12093, wb `a06ea71be9c5aa88`, consumer ev 5053, oracle FAIL `0x549c9e0347adaf23` |
| `V33-RP01-R02` | RP01 | **no `trace_v31.jsonl`** (only `prop_trace.csv.gz`); cannot re-parse |
| `V33G-FW02-MOUNTED-P0` | FW02 | **no manifest and no trace** |

Control sanity (all inspected controls contain **0 injections**, oracle
PASS, terminal `NO_INJECTION_EVENT`/UNRESOLVED): `V33-A01-C02`,
`V33F-A01-C02`, `V33B-A01-C02`, `V33-FW02-C01`, `V33F-FW02-C01`,
`V33-W4V33-FW02-C01`. This supports the fault runs' injection attribution.

No evidence from these runs was merged into a 60-row formal row; they are
same-seed chains on a different SHA and are cited only as corroboration.

---

## 9. What must be re-run on the final binary (`d3807fbe`) before formal

1. **All 60 contexts on one binary.** 45/60 are still evidenced on a
   non-final SHA, and the 15 on `68c6ce73` are on a binary that is not the
   formal target. A single-binary 12-model × R01–R05 campaign on `d3807fbe`
   with raw `trace_v31.jsonl` retained is required before any
   `COMPLETE_CAUSAL_CHAIN` model-level claim.
2. **FW05 R01–R05 on `d3807fbe` with traces stored.** Only R02 is currently
   covered by a d3807fbe trace (`V33F-FW05-R02`). R01 has no trace at any
   binary; the formal claim cannot rest on prior quotes.
3. **A01-R01, A01-R03, FW02-R02 with a working oracle checksum line.**
   These three have malformed/absent oracle output; R01/R02 also fail the
   crash-VA identity test. Re-run and record the raw checksum.
4. **A03 on `d3807fbe`.** Confirm the crash-load dynamic numbering (seq
   1014) and abort event IDs on the new binary; `V33C-A03-R01` already
   suggests the crash sequence is stable but event IDs shift (abort 1472 vs.
   1471).
5. **SP05 ×5 with a store-commit observation.** Either add a store-commit
   hook or formally record E4's store-commit-absent exception for the
   d3807fbe run. Also record a non-null store-side data hash if available.
6. **DA04 R04/R05 with byte-level reload comparison.** The full-word FNV
   comparison cannot close the store→reload data edge for a 4-byte store;
   a byte-mask comparison (or a same-width reload) is required for a
   `COMPLETE_CAUSAL_CHAIN` claim.
7. **RP01 ×5 with trace retention.** `V33-RP01-R02` has no trace. Retain
   `trace_v31.jsonl` for the HANG runs and capture the watchdog line; for
   R02/R03, run a configuration in which the suppressed replay is on a live
   path, otherwise the squash remains `unrelated`.
8. **LQ04 records keying.** Fix the CONTROL/FAULT duplicate SampleRunID
   before generating the final records, and re-key by EvidencePath/PilotID.
9. **Controls for every model on `d3807fbe`**, with the same seed/ordinal
   and the same binary, to keep the fault/control pair valid.

---

## 10. Honest limitations

- FW05's formal chains are prior quotes, not a fresh parse of the
  `8377c011` trace, which does not exist on disk.
- 23 contexts have no raw `oracle.log`; their oracle status is prior-meta
  or absent, never silently PASS.
- 7 contexts have a malformed raw oracle (no checksum line).
- `EDGE_WISE` DA04 and `PARTIAL` SP05 data-rule statuses are deliberate: the
  stored data hash and the reloaded word hash are not numerically
  interchangeable across widths, and SP05 has no store-side hash.
- A03's `FaultCausality` in the platform record remains `UNPROVEN`; the CSV
  reports the record value and names the E6 runtime match rather than
  upgrading it by hand.
- No evidence was merged across binary SHAs; same-seed supplementary runs
  are labelled as such in every CSV `Notes` cell.
