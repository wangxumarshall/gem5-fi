# Actor A — 60-Context Readiness & Eligibility Findings (LSU pre-formal v3.3)

**Round:** LSU pre-formal finalization, 2026-11-11 (read-only evidence audit)  
**Scope:** the 12 in-scope models x dynamic contexts R01–R05 = **60 formal SampleRunIDs** (A01, A03, FW02, FW05, SQ01, SQ03, SP05, DA04, LP01, MD04, LQ04, RP01). The 74-model baseline is out of scope.  
**Worktree audited:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`  
**Authoritative design:** `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`, sheet `5.60个样本执行矩阵` (60 rows)  
**Workbook SHA-256:** `3b219ee060b51cb9f07567e7c60e57b431b366cd432aaf4c1e0ec8f35d03db1c`  
**Current/final binary:** `build/ARM/gem5.opt` = `68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8` (v3.2.12 FINAL, per `GIT_COMMIT_v3212.txt`)  
**Companion CSV:** `LSU_60Context_Readiness_Matrix.csv` (exactly 60 data rows; every row cites existing in-tree evidence paths).  

No file outside these two deliverables was modified; gem5 was not run.

## 1. Tally

| Status | Count | Meaning used here |
|---|---:|---|
| READY | 13 | seed exact, workload identity verified, pilot exists with injection, distinct target, terminal+oracle evidence, matched control (where required), all cited files exist |
| PARTIAL | 30 | real evidence exists but at least one required attribute is missing/weak (no matched control, oracle MISSING, squashed/unproven causality, ALREADY_STUCK activation, non-final binary only) |
| BLOCKED | 0 | no context was found unknowable/seed-mismatched; nothing is fabricated or silently zeroed |
| DESIGN_CHANGE_REQUIRED | 17 | the executed context identity no longer matches the authoritative Excel row (workload substitution, ordinal re-selection, or duplicate dynamic instruction) |
| **Total** | **60** | 12 models x 5 contexts |

Seed check: **60/60 Excel seeds match the pilot/record seed exactly**. No seed drift was found in any model.

## 2. Per-model summary

| Model | Status breakdown (5 ctx) | Evidence binary (by ctx) | Terminals | Matched control |
|---|---|---|---|---|
| A01 | READY=3 / PARTIAL=1 / DESIGN_CHANGE_REQUIRED=1 | 68c6ce73x5 | CRASH, MASKED, UNRESOLVED | YES C01C/C02C (2/5) |
| A03 | PARTIAL=4 / DESIGN_CHANGE_REQUIRED=1 | 68c6ce73x5 | CRASH | YES C01C/C05C (2/5) |
| LQ04 | READY=5 | f3c2a442x5 | MASKED | YES CONTROL-R01..R05 |
| SQ01 | DESIGN_CHANGE_REQUIRED=5 | 720eb780x5 | SDC (B) / MASKED (literal) | YES C01/C01B |
| SQ03 | DESIGN_CHANGE_REQUIRED=5 | 720eb780x5 | MASKED (B and literal) | YES C01/C01B |
| SP05 | DESIGN_CHANGE_REQUIRED=5 | 720eb780x5 | SDC (B) / MASKED (literal) | YES C01/C01B |
| LP01 | PARTIAL=5 | 0de25644x5 | MASKED | NO (W5 baseline only) |
| FW02 | READY=2 / PARTIAL=3 | 720eb780x5 | CRASH (SIMULATOR_ERROR), MASKED, SQUASHED | YES C02 valid (C01 misfired) |
| FW05 | PARTIAL=5 | 8377c011x5 | SDC, SQUASHED | NO (W8a/W8b baseline only) |
| MD04 | PARTIAL=5 | 0de25644x5 | MASKED, SQUASHED | NO (W7 baseline only) |
| RP01 | READY=3 / PARTIAL=2 | 68c6ce73x5 | HANG, SQUASHED | YES CONTROL-R01..R05 |
| DA04 | PARTIAL=5 | 3e9148fcx3, 0de25644x2 | MASKED, SDC, SQUASHED | NO (W8 baseline only) |

## 3. Contexts that are READY (13)

- **A01-F0-W1-S01-R02** (A01): dyn_inst_seq=48 PC=0x400ad0 tick=197890; terminal MASKED, oracle PASS (728e604ffcec539d); binary `68c6ce73`.
- **A01-F0-W1-S01-R04** (A01): dyn_inst_seq=245 PC=0x40c0f0 tick=517440; terminal MASKED, oracle PASS (728e604ffcec539d); binary `68c6ce73`.
- **A01-F0-W1-S01-R05** (A01): dyn_inst_seq=253 PC=0x40c110 tick=518210; terminal MASKED, oracle PASS (728e604ffcec539d); binary `68c6ce73`.
- **FW02-F6-W4-S01-R03** (FW02): load_seq=10011 store_seq=10008 PC=0x4448a4 tick=12774685; terminal MASKED, oracle PASS; binary `720eb780`.
- **FW02-F6-W4-S01-R04** (FW02): load_seq=11101 store_seq=11099 PC=0x4448c8 tick=13002990; terminal MASKED, oracle PASS; binary `720eb780`.
- **LQ04-F0-W2-S01-R01** (LQ04): dyn_inst_seq=3 PC=0x400338 tick=80080 lq_idx=1; terminal MASKED, oracle PASS (b097eb83f71545cb); binary `f3c2a442`.
- **LQ04-F0-W2-S01-R02** (LQ04): dyn_inst_seq=4 PC=0x40033c tick=80465 lq_idx=2; terminal MASKED, oracle PASS (b097eb83f71545cb); binary `f3c2a442`.
- **LQ04-F0-W2-S01-R03** (LQ04): dyn_inst_seq=5 PC=0x400340 tick=133210 lq_idx=3; terminal MASKED, oracle PASS (b097eb83f71545cb); binary `f3c2a442`.
- **LQ04-F0-W2-S01-R04** (LQ04): dyn_inst_seq=6 PC=0x400344 tick=133595 lq_idx=4; terminal MASKED, oracle PASS (b097eb83f71545cb); binary `f3c2a442`.
- **LQ04-F0-W2-S01-R05** (LQ04): dyn_inst_seq=7 PC=0x400348 tick=133980 lq_idx=5; terminal MASKED, oracle PASS (b097eb83f71545cb); binary `f3c2a442`.
- **RP01-F6-W7-S01-R01** (RP01): dyn_inst_seq=69341 PC=0x4015fc tick=31072965; terminal HANG, oracle NOT_APPLICABLE (watchdog); binary `68c6ce73`.
- **RP01-F6-W7-S01-R04** (RP01): dyn_inst_seq=72018 PC=0x422a58 tick=36564990; terminal HANG, oracle NOT_APPLICABLE (watchdog); binary `68c6ce73`.
- **RP01-F6-W7-S01-R05** (RP01): dyn_inst_seq=72350 PC=0x44e2ec tick=37424310; terminal HANG, oracle NOT_APPLICABLE (watchdog); binary `68c6ce73`.

## 4. DESIGN_CHANGE_REQUIRED contexts (17)

### 4.1 SQ01 / SQ03 / SP05 — the B-variant question, answered explicitly

Each of these models has **two** pilot families for the same five Excel rows (same Excel seed and same row):

- `SUPP-{MODEL}-R01..R05` — uses the **literal Excel EventOrdinal 1..5** on `sq_reload_v3212`; it injects on C-runtime startup stores (`STORE_COMMITTED_LANE_NOT_READ`, MASKED, no consumer).
- `SUPP-{MODEL}-R01B..R05B` — **re-selected ordinals** `K*+0..K*+4` (SQ01 K*=1006, SQ03 K*=1009, SP05 K*=940), hitting the workload buffer `buf[0..4]` (`0x491990..0x4919b0`).

**Verdict: the B pilots are NOT extra contexts.** They are the same five formal rows (R01–R05, identical Excel seeds) re-run with a later eligible ordinal selected by the frozen address-eligibility preflight (`audit_v3_2_12/SQ_Ordinal_Eligibility_Preflight_v3.2.12.md`). They correspond to authoritative R01–R05, but the **actual target event is not the Excel EventOrdinal** and the **workload/oracle is not the Excel workload/oracle**: Excel `sq_drain` (SHA `d423539c…`, oracle `ba3b3185…`) was replaced by `sq_reload_v3212` (SHA `bcab9cc5…`, oracle `7df5034c…`). Hence all 15 rows are DESIGN_CHANGE_REQUIRED until the authoritative workbook is updated with the new workload, oracle, and ordinals (K*=1006/1009/940).

| Model | literal-ordinal run (Excel 1–5) | B re-selection (K*) | B terminal |
|---|---|---|---|
| SQ01 | seq {18,19,23,24,28}, MASKED/PASS | 1006–1010 -> seq {12108,12227,12423,12643,12776} | SDC/FAIL (mem_write==reload==consumer hash) |
| SQ03 | seq {18,19,23,24,28}, MASKED/PASS | 1009–1013 -> same buffer stores | MASKED/PASS (drain_tick<commit_tick, visible_before_commit=1) |
| SP05 | seq {18,19,23,24,28}, MASKED/PASS | 940–944 -> same buffer stores | SDC/FAIL (write_skipped=1, premature complete) |

### 4.2 A01-R03 and A03-R03 — duplicate dynamic instruction

- **A01-F0-W1-S01-R03**: ordinal 3 fires `dyn_inst_seq=48` at tick 204820 — the **replayed second attempt** of R02's load (R02 = seq 48, tick 197890). Same static instruction/PC `0x400ad0`; the A01 audit documents that R03 is the savedRequest-reuse replay and that no writeback edge exists. Ordinal counting is invalidated by replay.
- **A03-F5-W1-S01-R03**: activation at `dyn_inst_seq=48` tick 204820 — the same replayed pushRequest (independent cross-model corroboration in `A03_Propagation_Audit_v3.2.12.md`).

### 4.3 Full DESIGN_CHANGE_REQUIRED list

- A01-F0-W1-S01-R03: same static instruction (dyn seq 48) as R02 - R03 selects the REPLAYED attempt (tick 204820 vs 197890); ordinal/eligible semantics invalidated by replay
- A03-F5-W1-S01-R03: activation dyn seq 48 = replay attempt of R02 (tick 204820 vs 197890), same static instruction; ordinal semantics invalidated by replay
- SQ01-F0-W3-S01-R01: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1006+n, not Excel EventOrdinal 1-5; authoritative Excel row must be updated
- SQ01-F0-W3-S01-R02: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1006+n, not Excel EventOrdinal 1-5; authoritative Excel row must be updated
- SQ01-F0-W3-S01-R03: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1006+n, not Excel EventOrdinal 1-5; authoritative Excel row must be updated
- SQ01-F0-W3-S01-R04: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1006+n, not Excel EventOrdinal 1-5; authoritative Excel row must be updated
- SQ01-F0-W3-S01-R05: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1006+n, not Excel EventOrdinal 1-5; authoritative Excel row must be updated
- SQ03-F0-W3-S02-R01: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1009+n, not Excel EventOrdinal 1-5
- SQ03-F0-W3-S02-R02: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1009+n, not Excel EventOrdinal 1-5
- SQ03-F0-W3-S02-R03: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1009+n, not Excel EventOrdinal 1-5
- SQ03-F0-W3-S02-R04: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1009+n, not Excel EventOrdinal 1-5
- SQ03-F0-W3-S02-R05: workload override: Excel sq_drain (d423539c, oracle ba3b3185) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=1009+n, not Excel EventOrdinal 1-5
- SP05-F6-W6-S01-R01: workload override: Excel store_path (906b3798, oracle 2543a2a6) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=940+n, not Excel EventOrdinal 1-5
- SP05-F6-W6-S01-R02: workload override: Excel store_path (906b3798, oracle 2543a2a6) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=940+n, not Excel EventOrdinal 1-5
- SP05-F6-W6-S01-R03: workload override: Excel store_path (906b3798, oracle 2543a2a6) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=940+n, not Excel EventOrdinal 1-5
- SP05-F6-W6-S01-R04: workload override: Excel store_path (906b3798, oracle 2543a2a6) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=940+n, not Excel EventOrdinal 1-5
- SP05-F6-W6-S01-R05: workload override: Excel store_path (906b3798, oracle 2543a2a6) -> sq_reload_v3212 (bcab9cc5, oracle 7df5034c); propagation event uses re-selected ordinal K*=940+n, not Excel EventOrdinal 1-5

## 5. Drifting / unproven targets (explicit)

**Duplicate (same dynamic instruction reused):**
- A01 R03 and A03 R03 (dyn seq 48 = replay of R02; see 4.2).

**Ordinal drift (actual event ordinal != Excel EventOrdinal 1–5):**
- SQ01 R01–R05: actual 1006–1010 (B), literal 1–5 also run; workload override.
- SQ03 R01–R05: actual 1009–1013 (B), literal 1–5 also run; workload override.
- SP05 R01–R05: actual 940–944 (B), literal 1–5 also run; workload override.
- DA04 R02/R03/R04/R05: actual ordinals 6 / 16 / 50 / 200 (Excel 2/3/4/5); distinct dynamic stores, but the authoritative EventOrdinal is stale.
- LP01 R05: actual ordinal 14 (Excel 5).

**Unproven propagation / missing causal evidence:**
- **A03 R01–R05 (all five):** the `a03_stream` / `a03_activation` trace sink does not exist in the binary; the audit explicitly declares the five runs NOT_EVIDENCE_BEARING for the stream. Every A03 chain is the last injection at `dyn_inst_seq=1014`, PA `0xffffffffffb73c50`, CRASH, oracle MISSING. R01 and R04 activate ALREADY_STUCK (`affected=0`).
- **A01 R01:** CRASH (exit -6) with no oracle checksum line; audit finds the transient crash not causally attributed (UNPROVEN). R01 injection seq 5 @ PC 0x400790.
- **FW02 R01 / R05:** SQUASHED, FaultCausality PARTIAL/NONE. **FW02 R02:** SIMULATOR_ERROR/CRASH, oracle MISSING, UNPROVEN.
- **MD04 R01 / R04:** SQUASHED, PARTIAL/NONE. **DA04 R01:** SQUASHED, PARTIAL. **DA04 R02/R03:** MASKED but LIFECYCLE_ONLY (store committed, lane never read; no consumer edge).
- **FW05 R01:** SQUASHED, PARTIAL. **RP01 R02/R03:** SQUASHED, causality PARTIAL (`fault_caused=0`).
- **A01 R02/R04/R05, SQ01/SQ03/SP05 B, LQ04, LP01, MD04 R02/R03/R05, FW05 R02–R05:** coverage is LIFECYCLE_ONLY even where the chain is COMPLETE; SDC only where the terminal says so.

## 6. Contexts whose only evidence is on a NON-FINAL binary

Binary lineage (all clearly identified in `GIT_COMMIT*` / audit headers): 
- `68c6ce73` = v3.2.12 FINAL (current) — A01, A03, RP01 (15 rows).
- `720eb780` = v3.2.12 pre-final binary (SQ01/SQ03/SP05/FW02, 20 rows).
- `0de25644` = v3.2.7 binary (LP01 all; MD04 all; DA04 R04/R05, 12 rows).
- `3e9148fc` = v3.2.4/5 DA04 binary (DA04 R01–R03, 3 rows).
- `8377c011` = v3.2.7 FW05 binary (FW05 R01–R05, 5 rows).
- `f3c2a442` = v3.2.10/11 LQ04 binary (LQ04 R01–R05, 5 rows).

**45 of 60 rows have no fault pilot on the final `68c6ce73` binary.** They are evidence provenance, not current-binary eligibility; a final-binary rerun (same seeds) remains required before formal execution:

- SQ01: SQ01-F0-W3-S01-R01, SQ01-F0-W3-S01-R02, SQ01-F0-W3-S01-R03, SQ01-F0-W3-S01-R04, SQ01-F0-W3-S01-R05
- SQ03: SQ03-F0-W3-S02-R01, SQ03-F0-W3-S02-R02, SQ03-F0-W3-S02-R03, SQ03-F0-W3-S02-R04, SQ03-F0-W3-S02-R05
- SP05: SP05-F6-W6-S01-R01, SP05-F6-W6-S01-R02, SP05-F6-W6-S01-R03, SP05-F6-W6-S01-R04, SP05-F6-W6-S01-R05
- FW02: FW02-F6-W4-S01-R01, FW02-F6-W4-S01-R02, FW02-F6-W4-S01-R03, FW02-F6-W4-S01-R04, FW02-F6-W4-S01-R05
- LP01: LP01-F0-W5-S01-R01, LP01-F0-W5-S01-R02, LP01-F0-W5-S01-R03, LP01-F0-W5-S01-R04, LP01-F0-W5-S01-R05
- MD04: MD04-F6-W7-S01-R01, MD04-F6-W7-S01-R02, MD04-F6-W7-S01-R03, MD04-F6-W7-S01-R04, MD04-F6-W7-S01-R05
- DA04: DA04-F0-W8-S02-R01, DA04-F0-W8-S02-R02, DA04-F0-W8-S02-R03, DA04-F0-W8-S02-R04, DA04-F0-W8-S02-R05
- FW05: FW05-F6-W8-S01-R01, FW05-F6-W8-S01-R02, FW05-F6-W8-S01-R03, FW05-F6-W8-S01-R04, FW05-F6-W8-S01-R05
- LQ04: LQ04-F0-W2-S01-R01, LQ04-F0-W2-S01-R02, LQ04-F0-W2-S01-R03, LQ04-F0-W2-S01-R04, LQ04-F0-W2-S01-R05

## 7. A03 supplementary-context naming

The five A03 contexts used for the final evidence are **`SUPP-A03-R01C..R05C`** on binary `68c6ce73` (`pilots_v3_2_12/`). They are the same Excel rows R01–R05 (identical seeds/ordinals 1–5); the `C` suffix denotes the final-binary re-run, not a new context. Earlier `SUPP-A03-R01..R05` on `720eb780` are the same five rows on the pre-final binary. Controls are `SUPP-A03-C01C` and `SUPP-A03-C05C` (only 2 of 5 contexts have a matched control).

## 8. FW05 evidence provenance

FW05 has **no current-binary evidence**. The accepted records are the frozen v3.2.11 import (`audit_v3_2_12/FW05_frozen_records_v3.2.11.json`) on binary `8377c011` (v3.2.7): R01 SQUASHED/PASS, R02–R05 SDC/FAIL (complete causal chain). Raw `trace_v31.jsonl`/`oracle.log` for these five pilots live only inside the git-tracked v3.2.7 package zip; the frozen matrix `EvidencePath` (`audit_v3_2_11/extracted_evidence/FW05_v3_2_7/…`) is a dangling gitignored scratch path. In-tree pilot dirs `pilots_v3_2_7/FW05-R01..R05` carry manifest/meta/stats but not the raw trace. This is a traceability defect, not fabrication (final independent audit §Check 1). There is **no matched control** for FW05 (W8a/W8b no-fault baselines only).

## 9. Evidence and method

- Primary per-record grading: `audit_v3_2_12/{MODEL}_records_v3.2.12.binary-*.json` (and the four `*_frozen_records_v3.2.11.json` imports).
- Per-pilot provenance: each cited pilot dir's `pilot_meta.json` + `manifest.json` (seed, `event_ordinal`/`event_ordinal_used`, binary SHA, workload SHA, command).
- Eligibility: `RP01_CountOnly_Preflight_v3.2.12.csv`; `SQ_Ordinal_Eligibility_Preflight_v3.2.12.md`; `DA04_PILOT_SUMMARY.csv`; per-pilot `injection`/`eligible_ordinal` fields.
- Preflight status in the workbook is stale by design (`PILOT_ONLY_NOT_FORMAL`, `BLOCKED_NO_HOOK`, `ExecutionStatus=NOT_RUN`); this audit uses the real pilot/record evidence instead.
- Squash/replay: the A01/A03 audits document that ordinal counting counts replayed pushRequests; the A01 R03 record is the concrete invalidation. No A01/A03 context is upgraded on a squash.
- Terminal/oracle values are taken verbatim from the record JSON; no terminal was hand-relabelled and no missing oracle was converted to PASS.

## 10. Key file paths

- Workbook: `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
- Closure matrix: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix_v3.2.12.csv`
- Grading rules: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/FINAL_GRADING_RULES_v3.2.12.md`
- Standard: `docs/gem5-fi/lsu/implementation_v3_2/LSU_Propagation_Acceptance_Standard_v3.2.12.md`
- Pilots: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/`, `pilots_v3_2_10/` (LQ04), `pilots_v3_2_7/` (FW05/MD04), `pilots_v3_2_6/` (LP01/MD04/DA04 R04/R05), `pilots_v3_2_4/` (DA04 R01–R03)

