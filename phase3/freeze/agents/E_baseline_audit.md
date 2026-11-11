# Agent E — Independent Baseline Audit (read-only)

Workspace: `/home/sdc/gem5-fi-mmu-impl-v2` (original `/home/sdc/gem5-fi-mmu` not touched).
Snapshot: 2026-11-11T16:12Z (local 2026-11-12 00:12). No scons/gem5 was run. The only file
written is this report. Numbers below come from the commands in §9.

Scope: existing M01–M08 evidence **before** the new M05–M08 patches. During the audit,
another session created `phase3/freeze/authority/` (23:59 local); that state is recorded
separately in §6.

## 1. Binary inventory (the "two SHA" question)

The brief's "two binaries" framing is insufficient. The evidence chain names **ten**
distinct `gem5.opt` hashes:

| Prefix | Where it was used | Evidence |
|---|---|---|
| `1f9d3de2` | original pre-implementation workspace binary | `docs/gem5-fi/mmu/MMU_Final_Review_Package/04_WORKSPACE_AND_VERSION/Binary_Manifest.txt:3` |
| `bea5f813` | Phase 2.1, incl. **all ten M01/M02 five-context runs** | `phase2_1/06_Source_and_Build/Git_Baseline.md:11`; run logs compiled 2026-11-10 12:06:48 |
| `9a78728a` | Phase 2.2 primary (M01 R01, M02 R01/R04/R05) | `phase2_2/02_Build/Binary_SHA256.txt:4`; logs compiled 16:28:02 |
| `45a8b87a` | Phase 2.2 lifecycle-confirmation runs | `phase2_2/02_Build/Binary_SHA256.txt:5` |
| `6f85cc7f` | Phase 2.2 source-identical rebuild | `phase2_2/02_Build/Binary_SHA256.txt:6` |
| `5f3b74f7` | phase-3 build A, historical `TEST-M08-P3-R01` (not the CSV run) | `phase3/m08/M08_PILOT_R01.md:5` |
| `d80a52ad` | phase-3 build B, M04–M07 first pilots`TEST-*-P3-*` | `phase3/m04/M04_PILOT_R01.md:4`, `phase3/m05/M05_PILOT_R01.md:4`, `phase3/m06/M06_PILOT_R01.md:4`, `phase3/m07/M07_PILOT_R01.md:4` |
| `6ae93b03` | phase-3 00:56 "final clean" build | `phase3/package/MMU_PreFormal_Implementation_Package/A_Status/MMU_PreFormal_Summary.md:56` |
| `6dca2195` | 12:49 build: **M03 R01/R02 and every W11/W12 control** | `phase3/m03/M03_R01_EVIDENCE.md:4`, `phase3/formal/FS_RUN_MATRIX.md:5`; logs compiled 12:49:18 |
| `3ec51b2c` | 15:26 build, current file and freeze baseline | `phase3/final_binary.sha256`; `phase3/freeze/BASELINE_SNAPSHOT.txt:5`; measured by `sha256sum` |

The concrete "two finals" conflict is **`3ec51b2c` vs `6dca2195`**: the freeze baseline and
`MMU_Formal_Readiness_FINAL.md:4-5` claim `3ec51b2c`, while `FS_RUN_MATRIX.md:1-5` and
`M03_R01_EVIDENCE.md:3-4` call `6dca2195` final. M03 R01/R02 and all W11/W12 controls ran
on the 12:49 (`6dca2195`) build, not on `3ec51b2c`.

**Per-run binary provenance is not recorded.** Every `sample_manifest.json` stores only the
`gem5` path, never a hash; the `binary_hash=` trace column exists but is empty in all 54
traces checked (`zcat runs/*/Trace/prop_evt.txt.gz | grep binary_hash=` -> only empty
values). Provenance is therefore inferred from `gem5_stdout.log` "gem5 compiled" time.

## 2. M01/M02 five-context historical evidence

Raw terminals support the Phase 2.1 claims: **every target context FAILs and the other four
contexts PASS** in all ten runs (`board.terminal`), traces are valid gzip. Phase 2.1
acceptance reports M01 5/5 COMPLETE and M02 3/5 COMPLETE + R04/R05 PARTIAL.

| Model/Ctx | Target-context run(s) | Binary | Verdict | Raw support |
|---|---|---|---|---|
| M01 R01 | `phase2_1/02_M01_Context/R01`; `phase2_2/runs/M01_R01`; `runs/TEST-M01-R01` | bea5 / 9a78 / 3ec5 | FAIL/SDC | OK in all three; final run has **no control loaded** |
| M01 R02 | `phase2_1/02_M01_Context/R02` | bea5f813 | FAIL/SDC | OK (target FAIL, 4 PASS) |
| M01 R03 | `phase2_1/02_M01_Context/R03` | bea5f813 | FAIL/SDC | OK |
| M01 R04 | `phase2_1/02_M01_Context/R04` | bea5f813 | FAIL/SDC | OK |
| M01 R05 | `phase2_1/02_M01_Context/R05` | bea5f813 | FAIL/SDC | OK |
| M02 R01 | `phase2_1/03_M02_Context/R01`; `phase2_2/runs/M02_R01`; `runs/TEST-M02-R01` | bea5 / 9a78 / 3ec5 | FAIL/SDC | OK; final control is `TEST-ENV-CTRL-W10` (older binary) |
| M02 R02 | `phase2_1/03_M02_Context/R02` | bea5f813 | FAIL/SDC | OK |
| M02 R03 | `phase2_1/03_M02_Context/R03` | bea5f813 | FAIL/SDC | OK |
| M02 R04 | `phase2_1/03_M02_Context/R04`; `phase2_2/runs/M02_R04` | bea5 / 9a78 | FAIL/SDC | OK (Phase 2.1 chain PARTIAL) |
| M02 R05 | `phase2_1/03_M02_Context/R05`; `phase2_2/runs/M02_R05` | bea5 / 9a78 | FAIL/SDC | OK (Phase 2.1 chain PARTIAL) |

`phase2_2` contains **no M01 R02–R05 and no M02 R02/R03 target runs**
(`ls phase2_2/runs` -> M01_R01, M02_R01/R04/R05 + controls). Therefore
`MMU_Formal_Readiness_FINAL.md:14-15` ("phase2_2 (reused) 5/5, READY") is false as written:
the 5/5 evidence is Phase 2.1 on `bea5f813`, not Phase 2.2 and not `3ec51b2c`.

## 3. M03/M04 evidence

All five contexts exist for both models. Controls are separate no-fault run directories
(commands contain no `--mmu_fault_model`). Control vs fault binary differs for all M04
contexts and for M03 R03–R05.

| Model/Ctx | Run | Binary | Verdict | Raw support / caveat |
|---|---|---|---|---|
| M03 R01 | `TEST-M03-R01` | 6dca2195 | SQUASHED/PASS | OK; control `TEST-CTRL-W11-CLOSURE` same 12:49 build |
| M03 R02 | `TEST-M03-R02` | 6dca2195 | SQUASHED/PASS | OK; same control/build |
| M03 R03 | `TEST-M03-R03` | 3ec51b2c | SQUASHED/PASS | OK; control is 6dca2195 (binary mismatch) |
| M03 R04 | `TEST-M03-R04` | 3ec51b2c | SQUASHED/PASS | OK; control mismatch |
| M03 R05 | `TEST-M03-R05` | 3ec51b2c | SDC/FAIL PASS | **WEAK**: verdict has `missing_kind:tlb_lookup_hit`; fault trace has only activation + 7 inserts + summary (events 220/243), no lookup/consumer/commit. Guest `W11_RESULT observed=0xa5` is real, but "TraceCompleteness=COMPLETE / Propagation=FULL" are produced by a validator shortcut (see C7). |
| M04 R01 | `TEST-M04-FR01` | 3ec51b2c | SDC/FAIL PASS | Guest reads decoy `0x51` (real). Fault-tagged chain is activation 629 -> lookup -> consume -> LSU/cache -> memory_response 645 -> **squash 646**, no fault-tagged commit. FULL/COMPLETE come from the override. |
| M04 R02 | `TEST-M04-FR02` | 3ec51b2c | SDC/FAIL PASS | Same shape: fault-tagged chain ends in squash; control `TEST-CTRL-W12-R02` is 6dca2195 |
| M04 R03 | `TEST-M04-FR03` | 3ec51b2c | SDC/FAIL PASS | Same; control mismatch |
| M04 R04 | `TEST-M04-FR04` | 3ec51b2c | SDC/FAIL PASS | Same; control mismatch |
| M04 R05 | `TEST-M04-FR05` | 3ec51b2c | SDC/FAIL PASS | Guest decoy `0x51` real; trace has 20,004 `fault_entry_reuse`, **no commit/squash/memory_response in the fault_id=1 chain**; summary `result_propagated=0`, `commit_event_id=0`; FULL is an override |

M04 controls are genuinely per-context (`TEST-CTRL-W12-R01..R05`, scoped rcS). Their
`golden_output.txt` values differ per context. The controls were all run at 13:18 local
(6dca2195 build), while FR01–FR05 ran 18:32–19:15 on 3ec51b2c.

## 4. M05–M08 latest results vs every CSV PASS

CSV rows were compared field-by-field with `Validation/verdict.json`; **all 40 rows match
their verdict JSON exactly**. The problems are inside the verdicts, not CSV transcription.

| Model/Ctx | Run | Binary/Provenance | Verdict | Audit status |
|---|---|---|---|---|
| M05 R01 | `TEST-M05-R01` | 3ec51b2c, manifest | ACTIVATED_MASKED, NOT_CONSUMED, Oracle **PASS**, COMPLETE | PASS = golden observed (masked); no consumption proof. Final doc's PASS definition (`Readiness:23-25`) does not allow this. |
| M05 R02 | `TEST-M05-R02` | 3ec51b2c, manifest | same | same |
| M05 R03 | `TEST-M05-R03` | 3ec51b2c, manifest | same, COMPLETE | same. `MMU_Formal_Readiness_FINAL.md:50-51` says R03 trace is truncated; CSV:24 and verdict say COMPLETE. |
| M05 R04 | `TEST-M05-R04` | 3ec51b2c, manifest | NOT_CONSUMED, Oracle **PASS**, PARTIAL/TRACE_INCOMPLETE | **Flag**: PASS + TRACE_INCOMPLETE; missing commit/response/writeback |
| M05 R05 | `TEST-M05-R05` | 3ec51b2c, manifest | NOT_CONSUMED, Oracle **PASS**, PARTIAL/TRACE_INCOMPLETE | **Flag**: PASS + TRACE_INCOMPLETE; also missing `partial_entry_insert`, lsu, translation_result |
| M06 R01 | `TEST-M06-R01` | 3ec51b2c, manifest | DETECTED_CONTAINED, PASS_EXPECTED | OK: `exception_delivery=1`, state/result witnesses real |
| M06 R02 | `TEST-M06-R02C` | NA | NO_ELIGIBLE_EVENT, NOT_RUN | honest |
| M06 R03 | `TEST-M06-R03B` | 3ec51b2c by log, **no manifest** | DETECTED_CONTAINED, PASS_EXPECTED | **WEAK**: summary `exception_delivered=0`; no `exception_delivery` event. Terminal comes from validator branch "no commit -> contained" (C8) |
| M06 R04 | `TEST-M06-R04B` | no manifest | DETECTED_CONTAINED, PASS_EXPECTED | same weakness |
| M06 R05 | `TEST-M06-R05B` | no manifest | TRACE_INCOMPLETE, NOT_OBSERVED | honest |
| M07 R01 | `TEST-M07-R01` | 3ec51b2c, manifest | SDC/FAIL PASS | OK: `shared_changed=1`, `injected_success=1`, commit event 305; control `TEST-M07-P3B-CTRL-R01` is 2026-11-10 22:11 build |
| M07 R02/R03/R05 | `TEST-M07-R02/R03/R05` | 3ec51b2c | NO_ELIGIBLE_EVENT, NOT_RUN | honest; no control |
| M07 R04 | `TEST-M07-R04` | 3ec51b2c, manifest | SDC/FAIL PASS | Trace has commit, but activation event 268 has empty `parent_event_id`; control older binary |
| M08 R01 | `TEST-M08-R01` | 3ec51b2c by log, **no manifest** | SDC/FAIL PASS | Trace OK (activation 4311 -> commit 4326); control `TEST-ENV-CTRL-W10` older binary |
| M08 R02 | `TEST-M08-R02` | no manifest | PARTIAL/TRACE_INCOMPLETE, Oracle **PASS** | **Flag**: PASS from a golden file byte-identical to `TEST-ENV-CTRL-W10` (C5); no commit/memory_response |
| M08 R03 | `TEST-M08-R03` | no manifest | TRACE_INCOMPLETE, NOT_OBSERVED | honest; old verdict logged a gzip EOF (file now passes `gzip -t`) |
| M08 R04 | `TEST-M08-R04` | no manifest | PARTIAL/TRACE_INCOMPLETE, Oracle **PASS** | same as R02 |
| M08 R05 | `TEST-M08-R05B` | 3ec51b2c, manifest | SDC/FAIL PASS | Trace OK (8621 -> consumer 8622 -> commit 8624); **no independent control supplied** |

PASS-with-caveat: all 19 CSV Readiness=PASS rows carry at least one of (a) no final-binary
control, (b) missing manifest, (c) a validator override, or (d) no independent control.
None is fabricated at the guest-output layer, but the metadata does not meet the doc's own
PASS definition.

## 5. Oracle independence

| Model | Independent control used? | Same binary as fault run? | Notes |
|---|---|---|---|
| M01 | **No** | n/a | `pilot_runs.json` names `runs/w9_trace_on_final`; the dir exists with `board.terminal`, but there is no `Run_Log/golden_output.txt` or `observed_output.txt`, so `evidence_index.json` records `present:false`. Verdict compares the fault run's own line only. |
| M02 | Yes, `TEST-ENV-CTRL-W10` | **No** (2026-11-10 18:05 build vs 3ec51b2c) | Separate no-fault command |
| M03 | Yes, `TEST-CTRL-W11-CLOSURE` | No for R03–R05 (12:49 vs 15:26) | same for R01/R02 |
| M04 | Yes, per-context `TEST-CTRL-W12-R0x` | **No** (12:49 vs 15:26) | controls have no fault flags |
| M05 | Yes, `TEST-P3-W13-CTRL` | **No** (2026-11-10 22:11) | |
| M06 | Yes, `TEST-ENV-CTRL-W10` | **No** (2026-11-10 18:05) | R03B/R04B "faulted observation" is read from a byte-identical copy of this control |
| M07 | Yes, `TEST-M07-P3B-CTRL-R01` | **No** (2026-11-10 22:11) | R02/R03/R05 have no control (not run) |
| M08 | `TEST-ENV-CTRL-W10` for R01/R02/R04 | **No** (2026-11-10 18:05) | R02/R04 use the control copy as the faulted observation; R05B has no control |

## 6. 40 SampleRunIDs and seeds
Before the freeze: source workbook `/home/sdc/mmu_phase1_work/.../MMU_Final_Experiment_Plan.xlsx`
sheet `07_Sample_Matrix`, its CSV, and `phase3/formal/MMU_40_Sample_DryRun.csv` all contain
**40 unique SampleRunIDs, 8 models x 5 contexts, no duplicates, no missing entries**.
Every Seed cell read `NEEDS_AUTHORITATIVE_EXCEL`; SampleIDStatus `PROPOSED_NOT_FROZEN`; the
dry-run correctly reported 40/40 `BLOCKED_MISSING_SEED` and generated no seed.
During the audit a new frozen authority was created at `phase3/freeze/authority/`
(`16_Freeze_Record`): 40 unique FROZEN IDs, Seed literal `N/A_DETERMINISTIC`,
SeedSource=RESEARCHER_APPROVED, SeedPolicy=DETERMINISTIC, "NumericSeed=none". Diff of
source vs frozen sheet 07 shows **only** Seed and SampleIDStatus changed (80 cells) plus
three new columns. No numeric seed exists anywhere: all pilot manifests have
`seed=""`, `seed_present=false`, `seed_used_by_gem5=false` (checked across
`runs/*/sample_manifest.json` and `phase3/**/sample_manifest.json`).

## 7. Contradictions (file:line)

- C1 `MMU_Formal_Readiness_FINAL.md:14-15` says M01/M02 "phase2_2 (reused) 5/5, READY".
  `phase2_2/runs` has M01 R01 and M02 R01/R04/R05 only; the 5/5 evidence is Phase 2.1 on
  `bea5f813`. `MMU_Readiness_Matrix_FINAL.md:5-6` and `MMU_Context_Readiness_FINAL.csv:3-11`
  say M01/M02 R02–R05 `NOT_RUN`, `PARTIAL`.
- C2 `MMU_Formal_Readiness_FINAL.md:4-5` says final binary `3ec51b2c`;
  `FS_RUN_MATRIX.md:1-5` and `M03_R01_EVIDENCE.md:3-4` say `6dca2195`; gem5 logs show M03
  R01/R02 and W11/W12 controls compiled 12:49:18, final binary compiled 15:26:22.
- C3 `MMU_Formal_Readiness_FINAL.md:10` calls the matrix "real final-binary evidence", but
  M03 R01/R02 (line 16) used `6dca2195`, and no run records a binary SHA.
- C4 `MMU_Formal_Readiness_FINAL.md:54-56` claims R01/R03B/R04B all show
  `exception_delivery`. Raw traces: R01 has event 4309/`exception_delivered=1`; R03B and
  R04B have **no `exception_delivery` event** and summary `exception_delivered=0`.
- C5 `runs/TEST-M08-R02/Run_Log/golden_output.txt` and `TEST-M08-R04/.../golden_output.txt`
  are byte-identical to `runs/TEST-ENV-CTRL-W10/Run_Log/golden_output.txt`
  (sha256 `9e7d7a84…`). The validator's "faulted_observed" for those rows is therefore the
  control's own value; the comparison is control-vs-control.
  Same pattern in `TEST-M06-R03B` and `TEST-M06-R04B`.
- C6 `tools/mmu_formal_validate.py:123-124` falls back from `observed_output.txt` to
  `golden_output.txt`; combined with `:961-969` this can read the faulted observation from
  a control copy. Seven evidence runs have no `sample_manifest.json`
  (M06 R03B/R04B/R05B, M08 R01/R02/R03/R04).
- C7 `tools/mmu_formal_validate.py:1279-1282` sets `TraceCompleteness=COMPLETE` for any
  activated M03/M04/M07 Execute run, bypassing `missing_kinds`/`missing_edges`. M03 R05 has
  `missing_kind:tlb_lookup_hit` and no consumer/commit in its trace, yet reports COMPLETE.
  This branch did not exist in the 2026-11-11 00:59 packaged validator.
- C8 `tools/mmu_formal_validate.py:1193-1197` classifies M06 as DETECTED_CONTAINED when
  `state_consumed=1`, `result_propagated=1`, and no commit — without any exception or
  containment event. This is weaker than authoritative sheet `10_Terminal_Oracle`
  ("exception + containment/recovery + no wrong commit").
- C9 `tools/mmu_formal_validate.py:1238-1242` changes SQUASHED/TRACE_INCOMPLETE to SDC and
  Propagation=FULL on `oracle FAIL + proof`. For M04 the proof only checks activation
  `old_pfn != new_pfn` plus an entry-lifetime consumer; it does not require the committed
  wrong-PA access the comment describes. FR01–FR04 fault-tagged chains end in squash.
- C10 `MMU_Formal_Readiness_FINAL.md:16` marks M03 R05 PASS while its own verdict has
  `MissingCausalEdges=['missing_kind:tlb_lookup_hit']`; the trace has 259 events, no
  lookup/translation/commit.
- C11 `MMU_Formal_Readiness_FINAL.md:40-41` claims M04 Propagation=FULL/Trace=COMPLETE for
  all five; FR01–FR04 `fault_id=1` chains contain one `squash` and no commit; FR05 has
  20,004 reuses and no terminal commit/squash.
- C12 `MMU_Formal_Readiness_FINAL.md:50-51` says M05 R03–R05 traces are truncated; M05 R03
  trace passes `gzip -t`, has `W13_RESULT`, and CSV:24/verdict are COMPLETE.
- C13 `MMU_Formal_Readiness_FINAL.md:23-25` defines PASS as requiring "real
  consumption/propagation where the model has a consumer", yet M05 R01–R05 are
  `NOT_CONSUMED` and still carry `OracleResult=PASS`.
- C14 `M05_PILOT_R01.md`/`M04_PILOT_R01.md`/`M06_PILOT_R01.md`/`M07_PILOT_R01.md:4` report
  `d80a52ad`; the CSV rows they are used to justify are different `TEST-*-FR/ R0x` runs on
  `3ec51b2c`. `MMU_PreFormal_Summary.md:56` separately calls `6ae93b03` final.
- C15 No manifest or trace records the executed binary SHA: `sample_manifest.json` lacks a
  hash field and `binary_hash=` is empty in every trace. The freeze baseline itself relies
  on the filesystem hash of the current file, which cannot identify historical runs.
- C16 `phase3/freeze/authority/` (created 23:59, after the formal dry-run) flips
  Seed/Status as approved, while `phase3/formal/*` still says `NEEDS_AUTHORITATIVE_EXCEL`/
  `PROPOSED_NOT_FROZEN`. Both states must be kept distinct in the final package.

## 8. Priority fixes before MMU_FORMAL_READINESS=READY

P0 — claims that must be corrected before any READY statement:
1. Replace C1/C3 text: mark M01/M02 R02–R05 as historical `bea5f813` evidence or rerun
   them on `3ec51b2c`; stop calling `phase2_2` 5/5.
2. Resolve the `3ec51b2c` vs `6dca2195` split (C2): rebuild/rerun M03 R01/R02 and all
   controls on one frozen binary, or freeze `6dca2195` and retract `3ec51b2c` as "final".
3. Record binary SHA in `sample_manifest.json` and populate trace `binary_hash`; fail the
   preflight when absent (C15).
4. Remove the execute COMPLETE shortcut (`:1279-1282`) and the M04/M05/M08 SDC/FULL
   override (`:1238-1242`) unless a committed consumer with the injected PA is present
   (C7/C9). M03 R05 and M04 FR01–FR04 must be downgraded or retraced.
5. Require an exception/containment event for M06 DETECTED_CONTAINED (`:1193-1197`);
   rerun/downgrade R03B/R04B and correct C4.
6. Generate `observed_output.txt` from each fault run's own `board.terminal`; never let
   `golden_output.txt` (control copy) serve as the faulted observation (C5/C6). Revalidate
   M08 R02/R04, M06 R03B/R04B.
7. Provide an independent control for M01 (parse `runs/w9_trace_on_final/board.terminal`)
   and M08 R05B, on the same binary; otherwise mark those PASS unsupported (C13/§5).

P1 — evidence-quality fixes:
8. M05 R01–R05: relabel `OracleResult=PASS` as masked/contained, not a model PASS; fix
   M05 R03 doc/CSV mismatch (C12).
9. M05 R04/R05, M08 R02/R04: keep `TRACE_INCOMPLETE` and do not count as PASS rows.
10. Add the seven missing manifests; preserve the failed/partial runs.

P2 — consistency:
11. Regenerate `MMU_Formal_Readiness_FINAL.md` and both matrix docs from the verdict JSON,
    not by hand; keep the freeze-authority seed state separate from the pre-freeze dry-run.

## 9. Reproduce (exact commands, read-only)

```bash
cd /home/sdc/gem5-fi-mmu-impl-v2
sha256sum CHAOS/gem5/build/ARM/gem5.opt
cat phase3/final_binary.sha256 phase3/freeze/BASELINE_SNAPSHOT.txt
grep -a -m1 'gem5 compiled' runs/<RUN>/Run_Log/gem5_stdout.log
zcat runs/<RUN>/Trace/prop_evt.txt.gz | grep -E 'kind=(mmu_fault_activate|mmu_fault_summary|commit|squash)'
sha256sum runs/TEST-M08-R02/Run_Log/golden_output.txt runs/TEST-ENV-CTRL-W10/Run_Log/golden_output.txt
diff -u phase3/package/MMU_PreFormal_Implementation_Package/F_Formal/tools/mmu_formal_validate.py tools/mmu_formal_validate.py
python3 -c "import csv; r=list(csv.DictReader(open('phase3/formal/MMU_Context_Readiness_FINAL.csv'))); print(len(r),len({x['SampleRunID'] if 'SampleRunID' in x else (x['Model'],x['Context']) for x in r}))"
# 40-sample cross-check (source workbook sheet 07, CSV, dry-run, freeze authority):
#   openpyxl read_only; compare SampleRunID sets, Seed and SampleIDStatus counters
# fault-chain kinds per run:
python3 - <<'PY'
import gzip,re,collections
for d in ['TEST-M04-FR01','TEST-M04-FR05','TEST-M06-R03B','TEST-M08-R02','TEST-M03-R05']:
    ev=[dict(re.findall(r'(\w+)=([^ ]*)',l)) for l in gzip.open(f'runs/{d}/Trace/prop_evt.txt.gz','rt',errors='replace') if l.startswith('PROP-EVT:')]
    print(d, collections.Counter(e['kind'] for e in ev if e.get('fault_id')=='1'))
PY
```
