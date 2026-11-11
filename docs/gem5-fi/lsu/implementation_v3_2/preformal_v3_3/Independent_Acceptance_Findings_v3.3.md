# LSU v3.3.0 Pre-Formal Round — Independent Acceptance (Subagent F, second pass)

**Date:** 2026-11-11, snapshot taken 12:38–12:52 CST
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-preformal-v3.3.0-20261111` (HEAD `c1846ae4`)
**Scope:** 12 models x R01–R05 = 60 formal contexts; the 74-model baseline is out of scope.
**Mode:** read-only. No gem5 run, no scons, no file under `CHAOS/gem5/src` touched. Only this report was written.
**Caveat:** the `preformal_v3_3/` tree was being written by other agents while this audit ran (CSV/xlsx mtimes 12:40–12:48; `V33F-*` rerun dirs appeared at 12:42). Counts below are the state at the snapshot time; a moving target is itself a finding.

---

## 0. Verdict

**CONFIRMED (with evidence):** the four commits are on the branch; the working tree has no tracked modification outside them; both `gem5.opt` copies are identical; `pytest tests/ -q` = 180 passed and the platform suite = 107 passed; the five key pilot claims (A01 control, A03 single nonzero fault, FW05 reload 0/0, FW02 suppression, RP01 triggering_seq) are exactly as stated; the 60 SampleRunIDs and seeds are unique and unchanged versus v3.2.1/v3.2.x; no tool generates formal seeds; sheet 5 has EventOrdinal 1–5 with WarmUp/ROI = NEEDS_RESEARCHER_CONFIRMATION for all 60; controls cover only 18/60 contexts.

**CONTRADICTED:** the expected binary SHA `f43c5ddf…` is **not** the on-disk binary (actual `d3807fbe…`); the claim that `V33-FW02-C01` is a **mounted** p=0 control is false (the injector is not mounted, so its zero injections are vacuous); 4 rows are `Status=READY` with `MatchedControlValid=MISSING`; the patches README says "nothing here is applied" while 3 of the 5 patches are already applied; the package cites three different binaries (68c6ce73 / f43c5ddf / d3807fbe) as "the" binary.

**UNVERIFIABLE:** that any on-disk binary was built from the exact committed HEAD source (no rebuild allowed, and gem5 embeds its compile timestamp, so every rebuild changes the SHA); that a mounted-probability-0 FW02 run actually exercises commit 364a6057 (no such run exists).

**No READY claim is defensible.** The package's own `FormalReady` column is `NO` on all 60, `ConfigFrozen=NO` on all 60, and the freeze checklist is still BLOCKED on warm-up/ROI, controls, and per-context final-binary evidence.

---

## 1. Check table (command -> observed)

| # | Check | Command (abridged) | Observed |
|---|---|---|---|
| 1 | Branch/HEAD | `git rev-parse --abbrev-ref HEAD; git log --oneline -5` | `lsu-preformal-v3.3.0-20261111`; `c1846ae4`, `c8fc4353`, `364a6057`, `5541648c`, `9e3d104c` |
| 1b | Four commits present | `git show --stat 5541648c 364a6057 c8fc4353 c1846ae4` | all four present; 5541648c touches CHAOSAddrPath/CHAOSPropagation/chaos_lsu_trigger/lsq.cc; 364a6057 CHAOSLSQFwd.cc; c8fc4353 lsq_unit.cc; c1846ae4 `workloads/directed/sq_forward_v33{,.c}` |
| 1c | No other tracked change | `git status --porcelain` | only `?? .tmp_lsu_conc/`, `?? docs/.../preformal_v3_3/`, `?? docs/superpowers/plans/2026-11-11-lsu-preformal-finalization.md` |
| 2 | Binary SHA both copies | `sha256sum build/ARM/gem5.opt CHAOS/gem5/build/ARM/gem5.opt` | both `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2` (1,149,087,848 B, mtime 12:33:48) |
| 2b | Expected SHA | same | **mismatch**: expected `f43c5ddf7bab1fd9fab37a4962f1f34b89be3f76ac7d39dcf0ddb9318350b882` is absent from disk |
| 3a | Top-level tests | `python3 -m pytest tests/ -q -p no:cacheprovider` | `180 passed in 95.47s` |
| 3b | Platform tests | `python3 -m pytest docs/.../platform/tests -q -p no:cacheprovider` | `107 passed in 3.83s` |
| 4a | A01 control | trace parse of `runs/V33F-A01-C02` (d3807fbe) | `probe`=1, `a01_ea`=1, zero `inj`/`a01_fault`; pilot_meta `control_valid=true`, `injection={}`, exit 0; probe detail `injected=0;control_only=1`, both nodes ptag=0 |
| 4b | A03 fault link | trace parse of `runs/V33F-A03-R01` (d3807fbe) | exactly **1** `a03_fault`: `fault_va=ffffffffffb73c50; golden_ea=…c58; actual_ea=…c50; crash_addr_matches=1`; no 0/0 row; panic in stderr is `Page table fault … 0xffffffffffb73c50`; exit -6 (SIGABRT by design) |
| 4c | FW05 reload | trace parse of `runs/V33F-FW05-R02` (d3807fbe) | `fw05_reload` exists: `reload_data_fnv=af64514c8602b35b; true_fnv=12446998b6871244; alt_fnv=a06ea71be9c5aa88; reads_true_store=0; reads_alt_store=0` |
| 4d | FW05 register chain | same trace | `inj_fw05`: `selected_source=alt_store; wrong_source_substitution=1; data_differs=1`; `taint_reg` FNV `a06ea71b…` == `alt_fnv`; `value_matches_payload=1`; `commit tracked=fault`; `errant_commit`; consumer chain input hashes match (`consumer_input_matches_source=1`) |
| 4e | FW02 controls | `command.txt`, `config.ini`, trace of `V33F-FW02-C01` | zero injection nodes, but command has **no** `--chaos_lsqfwd`/`--lsq_struct_mode`; `config.ini` has only `board.chaos_propagation` -> injector not mounted |
| 4f | FW02 fault | `V33-FW02-R01` trace | `inj`=1, `fw02_decision: normal=forwarded, fault_decision=suppressed`, `squash cause=unrelated fault_tracked=1`, oracle PASS (MASKED) |
| 4g | RP01 squash | `V33-RP01-R02` trace | 1205 `squash` rows; e.g. `triggering_seq=87/110/237; triggering_seq_recorded=1; fault_tracked=0; squash_cause=unrelated`; exit 0, checksum `0x59fc61c040618747` |
| 5 | CSV row counts | `csv.DictReader` | Readiness 60; Fault_Control 68; Propagation 60; Workload 9; Source_Hook 12; Freeze_Checklist **44** (was 35 when Agent E wrote its MD) |
| 5b | Evidence paths exist | path resolution over Readiness/Closure/Fault_Control | 0 missing / 0 missing / 0 missing |
| 6a | Sheet 5 | `openpyxl` read-only on `LSU_12Model_60Sample_PreFormal_v3.3.xlsx` | 60 rows; EventOrdinal {1:12,2:12,3:12,4:12,5:12}; WarmUp and ROI both `NEEDS_RESEARCHER_CONFIRMATION` x60; `ConfigFrozen=NO` x60; `gem5Commit=6f98088a…` x60 (stale) |
| 6b | Controls | `LSU_Fault_Control_Pair_Audit.csv` | 25 VALID rows = **18 unique non-ALT contexts** (+7 `-ALT` duplicates); 42 MISSING; 1 INVALID_MISFIRE; Status 67 BLOCKED / 1 FAIL |
| 7 | Seed identity | compare v3.3 vs v3.2.1 vs v3.2.7 sheet 5 | 60 unique IDs, 60 unique seeds; 0 SampleRunID/Seed/EventOrdinal mismatches vs both workbooks |
| 7b | No seed generator | `grep random/randint/urandom/secrets` in `platform/*.py`, `tools/*.py` | no formal seed generation; `run_pilot.py` defaults to the Excel seed (`seed_source = excel:5.60个样本执行矩阵!Seed`) |

---

## 2. Independent counts

### 2.1 60-context status tally (as reported, re-derived)
- `LSU_60Context_Readiness_Matrix.csv` `Status`: **PARTIAL 30 / READY 13 / DESIGN_CHANGE_REQUIRED 17**.
- `FinalStatus`: **BLOCKED 35 / PARTIAL 3 / DESIGN_CHANGE_REQUIRED 22**.
- `FormalReady`: **NO 60/60**.
- `WarmUpGate`: `NOT_FROZEN (NEEDS_RESEARCHER_CONFIRMATION)` 60/60.

### 2.2 Matched controls (Agent E says 18 — confirmed)
- 25 VALID rows in the audit CSV, but 7 are `-ALT` re-runs of an already-counted context -> **18 unique formal contexts (18/60)**.
- Covered: A01 R01,R02; A03 R01,R05; FW02 R01; LQ04 R01–R05; RP01 R01–R05; SP05 R01; SQ01 R01; SQ03 R01.
- Uncovered (42): all DA04/FW05/LP01/MD04; FW02/SP05/SQ01/SQ03 R02–R05; A01 R03–R05; A03 R02–R04.
- FW02's "valid" control is `SUPP-FW02-C02`, which **omits the injector**; it is a structural no-injector control, not a mounted p=0 control.

### 2.3 Current-binary vs historical evidence
- On-disk binary: `d3807fbe…`, compiled 2026-11-11 12:29:52 (embedded in stdout).
- Three builds were used this round: `aeb99f11…` (12:07:19; old A01/FW02/FW05 runs), `f43c5ddf…` (12:23:12; V33B A01/A03, RP01), `d3807fbe…` (12:29:52; V33C, W4V33 and all `V33F-*` reruns).
- Formal contexts with any V33 pilot: about **5/60** (A01 R02, A03 R01, FW02 R01, FW05 R02, RP01 R02). Of these, only **A03 R01 and FW05 R02 have a fault run on `d3807fbe`**; A01 R02 and RP01 R02 are on `f43c5ddf`; FW02 R01 is on `aeb99f11`. Controls on `d3807fbe`: A01 R02, FW02 R01 (injector omitted).
- `CurrentBinaryEvidence` column: `HISTORICAL_ONLY` 55, non-historical 5 — but only one of those five (A03 R01) is a fault run on the actual on-disk binary; the label "current binary" is therefore misleading.
- The closure CSV (`LSU_Propagation_Closure_Final.csv`, 60 rows) is entirely historical (`SUPP-*`, binary 68c6ce73, `pilots_v3_2_12/`), with only 2 `COMPLETE_CHAIN` rows.

---

## 3. Pilot evidence, judged against the native mechanisms

### 3.1 V33F-A01-C02 (control, d3807fbe, seed 1113826800, ordinal 2) — CONFIRMED
`control_valid=true`, `injection={}`, exit 0, oracle pass. Trace has exactly one `probe` and one `a01_ea` node, both `ptag=0`; probe detail `injected=0;control_only=1`; `a01_ea` detail `xor_delta=0; affected=0; fault_va=NOT_APPLICABLE`. The ptag 0 is a reference tag, not an injection id (fault runs use 1,2,…). Zero injection is real.

### 3.2 V33F-A03-R01 (fault, d3807fbe) — CONFIRMED, with a broken-stream caveat
Exactly one `a03_fault` node, `fault_va = actual_ea = ffffffffffb73c50` (nonzero), `golden_ea = …c58`, `crash_addr_matches=1`, `reason=STUCK_APPLIED`. The earlier `V33B-A03-R01` (f43c5ddf) contained **two** rows, one of them the bogus 0/0 `ALREADY_STUCK` row; the cited V33C/V33F rerun removed it, so the fix works. Caveats: the run intentionally SIGABRTs (`exit -6`, page-table fault at exactly the fault VA), `stats.txt` is 0 bytes, and the gzip trace is truncated (no end-of-stream marker) for all three A03 traces. Evidence up to the crash is readable; it is not a complete stream.

### 3.3 V33F-FW05-R02 (fault, d3807fbe) — CONFIRMED, and the reload is NOT proof
What the native chain proves:
- `inj_fw05`: the forwarding decision selected the older full-cover store (`selected_source=alt_store`, `wrong_source_substitution=1`, `data_differs=1`; true hash `12446998b6871244`, alt hash `a06ea71be9c5aa88`).
- `taint_reg`: the loaded register writeback FNV is exactly the alt-store payload (`a06ea71b…`), `value_matches_payload=1`.
- `commit` (`tracked=fault`) + `errant_commit`; downstream `consumer` nodes carry `consumer_input_matches_source=1`.
So the register/dataflow chain injection -> register -> consumer -> commit is hash-equal and complete.

What it does **not** prove: the later `fw05_reload` node reads **neither** source (`reads_true_store=0; reads_alt_store=0`), and its `reload_data_fnv=af64514c8602b35b` differs from both the true and alt store hashes. The reload is therefore **not** evidence that the wrong-source data reached the later memory-path load (the "store->reload visibility" leg remains open). The run also ends with `ORACLE_FAIL` (expected `67afad307642983e`, got `549c9e0347adaf23`), consistent with an SDC but not a proof of the reload lane.

### 3.4 FW02 — the parenthetical claim "mounted p=0 control" is REFUTED
`V33-FW02-C01`, `V33-W4V33-FW02-C01` and the new `V33F-FW02-C01` all lack `--chaos_lsqfwd` and `--lsq_struct_mode f6_fw02`; `config.ini` contains only `board.chaos_propagation`. Zero injections are guaranteed because the injector does not exist in the config, not because the probability guard works. The platform test `test_run_pilot_fw02_control_mount.py` documents this design: the F6_fw02 control is *intentionally* injector-omitted. Consequence: commit 364a6057 (the `probability <= 0` gate) has **no gem5 evidence exercising it**; only unit tests of command construction cover it.

The fault side is correct: `V33-FW02-R01` observes once and suppresses once (`fault_decision=suppressed`, `squash_cause=unrelated`, oracle PASS = MASKED).

### 3.5 V33-RP01-R02 — CONFIRMED
1205 `squash` rows with real `triggering_seq` (87, 110, 237, 74165 in the V33F-era data), `triggering_seq_recorded=1`, `fault_tracked=0`, `squash_cause=unrelated`, `fault_caused=0`; exit 0, checksum `0x59fc61c040618747`. Caveat: this dir has no manifest.json/command.txt (provenance only from stdout), and it ran on `f43c5ddf`, not the on-disk binary.

### 3.6 W4 / FW02 workload (v3.3 proposal)
The frozen `sq_forward` ELF has **zero data loads in `main`** (all `ldr` are libc; the audit and `objdump` agree), so FW02's target store->load pair is unproducible in `main`. The new `sq_forward_v33` (commit c1846ae4) does produce main loads (8 `ldr` / 10 `str` by mnemonic in `main`), but the V33-W4V33-FW02-R01 run injected at `pc=0x40c0e0`, which is inside `_dl_aux_init` (0x40c080), i.e. **libc startup, not `main`**. Ordinal 1 with WarmUp=0 still selects libc even on the proposal ELF. The proposal is not promoted to the formal workload.

---

## 4. Excel / warm-up / seeds

- Sheet 5 (`5.60个样本执行矩阵`): 60 rows, 60 unique SampleRunIDs, 60 unique seeds; EventOrdinal exactly 1–5 (12 each, one per model per ordinal); `WarmUp` and `ROI` = `NEEDS_RESEARCHER_CONFIRMATION` on **all 60**; `ConfigFrozen=NO` on all 60; `gem5Commit` = `6f98088a7144d7f6fb22d985be3023ac5658e71b` on all 60 (an ATLAS commit, not the code HEAD).
- Seed/identity stability: 0 mismatches in SampleRunID/Seed/EventOrdinal vs v3.2.1 and v3.2.7 (both 60x43 with identical headers). v3.3 adds sheets 23–29 but does not alter the frozen identity.
- Warm-up doc `implementation_v3_2/LSU_Warmup_ROI_Recommendation_v3.2.2.md` explicitly says "Why not 0 / full": `WarmUp=0` injects into libc/initializer (no steady state) and full-workload ROI lets the checksum loop consume the fault; both "are explicitly rejected". It recommends R01–R05 at 10/30/50/70/90% quantiles **inside** the ROI and states the boundaries must be converted to event counts with a phase-instrumented run.
- The pilots use `--addrpath_warmup_events 0` and `EventOrdinal 1..5` directly. Therefore the frozen ordinals **cannot be used as-is**: they are currently "first 5 eligible events after libc has started", not ROI positions. The evidence agrees with the package's own changelog row: "EventOrdinal 1..5 with WarmUp=0 selects libc startup events".

---

## 5. Discrepancy list (things that would mislead a trusting researcher)

1. **Binary SHA.** The round context/changelog says `f43c5ddf…`; the on-disk binary is `d3807fbe…`. The freeze checklist's V3.3 rows (added during this audit) do say `d3807fbe`, so artifacts now contradict each other. In addition, gem5 embeds its compile timestamp, so every rebuild produces a new SHA: SHA equality is not source identity, and none of the four commits was followed by a rebuild (commits at 12:35:55–12:38:54; final binary compiled 12:29:52). Source-to-binary correspondence is inferred from content, not proven.
2. **"Mounted p=0" FW02 control.** No such run exists; all FW02 controls omit the injector. The stated verification of commit 364a6057 is therefore not backed by a run.
3. **READY rows without controls.** 4 contexts are `Status=READY` with `MatchedControlValid=MISSING` (A01 R04, A01 R05, FW02 R03, FW02 R04); 8 more READY rows have a control but only historical evidence. Zero READY rows have both a valid control and evidence on the on-disk binary. Only the `FinalStatus`/`FormalReady` layer is honest (`NO` 60/60); the intermediate `Status` column is unsafe to read alone.
4. **"CurrentBinaryEvidence" label.** 55 rows are historical; of the 5 non-historical, only A03 R01 is a fault run on the on-disk binary. FW02 R01 is on `aeb99f11` and FW05 R02 is on `aeb99f11`; A01 R02 and RP01 R02 are on `f43c5ddf`.
5. **Three binaries / stale narratives.** `Agent_E_Config_Control_Findings.md` still says HEAD `9e3d104c` and binary `68c6ce73` present on disk, while the CSV now says `c1846ae4`/`d3807fbe`; the Agent E MD also says "35 checklist rows" while the CSV has 44 (9 V3.3 rows appended). The workbook changelog still pins `f43c5ddf`.
6. **Freeze-checklist arithmetic.** The V3.3 row says "5 fault + 2 control on v3.3; 45 historical-only". That does not reconcile with 60 contexts (60−7=53) nor with the readiness matrix (`HISTORICAL_ONLY` 55, non-historical 5).
7. **Patch README false.** `patches/README.md` says "Nothing here is applied" and "All five pass git apply --check". In fact FW02/FW05/RP01 patches reverse-apply cleanly (already applied by the commits); apply-check fails for all five. A01/A03 reverse-check also fails, meaning the proposal diff is not byte-identical to what was committed.
8. **A03 traces are truncated and stats empty.** All A03 traces lack the gzip end marker and `stats.txt` is 0 B because the run aborts by design. The `a03_fault` row is present, but the stream is incomplete; this must be described as an intentional-crash artifact, not a clean completed trace.
9. **FW05 reload overstatement risk.** The package correctly records `reads_true/alt=0/0`, but a casual reader could treat "fw05_reload node exists" as proof of the store->reload leg. It is not: the reload reads neither source and its hash matches neither.
10. **W4 proposal vs formal workload.** The `V33F` checklist row says the frozen ELF has 1 load in `main`; the workload audit says 0 data loads in `main`. Either way, the formal W4 cannot host FW02's target pair, and the proposal run's ordinal-1 event is in libc (`0x40c0e0`), not `main`.

---

## 6. Residual blockers that prevent any READY claim

1. **Warm-up/ROI unfrozen.** 60/60 `NEEDS_RESEARCHER_CONFIRMATION`; the recommendation rejects WarmUp=0 and full-ROI; pilots use WarmUp=0 and raw ordinals 1–5 (libc-phase events). Frozen ordinals cannot be used as-is.
2. **Control coverage 18/60.** 42 contexts have no matched control; FW02's valid control is injector-omitted, and DA04/MD04 have no control and hidden-probability risks.
3. **Per-context final-binary evidence is 5/60 at best, and only 1–2 are fault/control pairs on the on-disk binary.** Two historical binaries (`720eb780`, `e527f26a`) are no longer on disk; LQ04 is on `f3c2a442`.
4. **The new FW02 probability guard has no executed p=0-with-injector verification.**
5. **Binary/source provenance is not reproducible** (compile-time-embedded SHA; no rebuild after the commits), and three binaries are conflated in the package.
6. **Workload validity:** W4 frozen ELF has no main data loads, so FW02's target is unproducible on the frozen workload; the W4 v3.3 ELF is a proposal and even then ordinal 1 lands in libc.
7. **Spreadsheet provenance is stale:** `gem5Commit` 6f98088a on all 60 rows; `ConfigFrozen=NO`; path fields point at older worktrees.
8. **Only 2/60 closure rows are `COMPLETE_CHAIN`; 31 are `COMPLETE_CHAIN_EXCEPTION`; 22 have no oracle result.**

**Bottom line:** the round's five pilot claims are individually reproducible and the four commits are real, but the package is a well-labelled *progress* package, not a formal-ready one. Its own `FormalReady=NO (60/60)` and `ConfigFrozen=NO (60/60)` are the correct headline; any summary that turns `Status=READY` or "valid control" into a formal claim would be wrong.
