# Agent F3 — Final Independent Acceptance (LSU v3.3.3)

**Auditor:** Agent F3 (fresh adversarial re-auditor; wrote none of the artifacts under audit)
**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**HEAD at audit:** `135ebcfeab86dc911f40c1bd79b92663f65de037` ("fix the causal ROI strings and finalize readiness labels"); final source HEAD `b5031bf7d857ca7901810a3bf3629f5649ddaaac`
**Mode:** read-only. No source/config/tool/test/data/Excel edit; no gem5, no scons. Only this report was written (superseding the F2 re-audit). Tools used: `sha256sum`, `git`, `stat`, `find`, `gzip -t`, `unzip -l`, openpyxl (read-only), read-only Python.

**Method:** every number below was recomputed from raw artifacts (`runs/*/summary.json|manifest.json|command.txt`, the ROI/controls/propagation CSVs, the workbook via openpyxl, the build/pytest/dry-run logs, the binary and the git tree). The main agent's acceptance report and the F2 report were treated as claims to be re-tested, not trusted.

---

## 0. Verdict

> ## `READY_FOR_FORMAL_EXPERIMENT`
>
> The blocking defect **F-05 is genuinely fixed** in every place the F2 audit named (tool source, top-level causal CSV, workbook `Causal_Propagation` sheet, workbook `Fault_Sample_Manifest`, ROI mapping) and the fix is committed at `135ebcfe`. Residuals **R-02** and **R-03** are cleared. **R-05** is confirmed as a pre-existing, out-of-scope v3.3.2 packaging artifact. **R-04 is substantially cleared but one stale wording instance remains** (Ready-Gate table line 163: "55 COMPLETE_PROP_TRACE") — a LOW documentation nit, not a data defect, and it does not contradict the corrected breakdown given in the headline table and Q4. All core data gates re-derive exactly. The 14 package items are present on disk (two under `build/`/`reports/` rather than the exact top-level paths named by the plan); only the zip itself is not built.
>
> Two LOW provenance notes are worth committing before zipping (see §6): the `LSU_60Context_Final_Readiness_Matrix.csv` label fix is present in the worktree but **not** in HEAD `135ebcfe`, and `LSU_Independent_Acceptance.md` is referenced by the acceptance report but exists only as `reports/Agent_F_Final_Independent_Acceptance.md`.

---

## 1. F-05 — stale A01/A03 ROI in the causal table — **PASS (fixed)**

The stale tuple is gone from the tool source and every artifact.

```text
$ grep -nE '"A01"|"A03"' tools/lsu_v333_propagation.py
55:    "A01": (585, 713, 129, [597, 623, 649, 675, 701]),
56:    "A03": (1040, 1222, 183, [1058, 1094, 1131, 1168, 1204]),

$ grep -E '^(A01|A03),' audit_v3_3_3/LSU_60Context_Causal_Propagation.csv | cut -c1-55
A01,R01,ROI=585-713;N=129;p=0.10;ordinal=597,...
...
A03,R05,ROI=1040-1222;N=183;p=0.90;ordinal=1204,...

$ grep -cE '1040-1234|N=195' audit_v3_3_3/LSU_60Context_Causal_Propagation.csv
0

$ grep -cE '1040-1234|N=195' audit_v3_3_3/LSU_60Context_Final_Readiness.csv \
      audit_v3_3_3/LSU_60Context_Final_Readiness_Matrix.csv \
      audit_v3_3_3/LSU_Fault_Control_Audit.csv
0 / 0 / 0
```

Workbook, read-only via openpyxl — whole-workbook cell scan for `1040-1234`/`N=195`: **NONE**. `Causal_Propagation` rows 2–11:

```text
A01 R01 | ROI=585-713;N=129;p=0.10;ordinal=597
A01 R02 | ROI=585-713;N=129;p=0.30;ordinal=623
A01 R03 | ROI=585-713;N=129;p=0.50;ordinal=649
A01 R04 | ROI=585-713;N=129;p=0.70;ordinal=675
A01 R05 | ROI=585-713;N=129;p=0.90;ordinal=701
A03 R01 | ROI=1040-1222;N=183;p=0.10;ordinal=1058
A03 R02 | ROI=1040-1222;N=183;p=0.30;ordinal=1094
A03 R03 | ROI=1040-1222;N=183;p=0.50;ordinal=1131
A03 R04 | ROI=1040-1222;N=183;p=0.70;ordinal=1168
A03 R05 | ROI=1040-1222;N=183;p=0.90;ordinal=1204
```

`Fault_Sample_Manifest` A01/A03 rows carry `ROI_Start/ROI_N = 585/129` and `1040/183` with `Executed_EventOrdinal` `597…701` / `1058…1204`; `ROI_Context_Mapping` carries the same. All ten rows satisfy `ordinal = start + ceil(p·N) − 1`:

```text
585+ceil(0.10*129)-1=597 … 585+ceil(0.90*129)-1=701
1040+ceil(0.10*183)-1=1058 … 1040+ceil(0.90*183)-1=1204
```

Full 60-row arithmetic recomputation: **0 failures**; **0 stale A01/A03 rows**. The committed HEAD blob `135ebcfe:audit_v3_3_3/LSU_60Context_Causal_Propagation.csv` also reads `585-713;N=129` / `1040-1222;N=183` (0 stale strings).

---

## 2. R-02 — stale 685d smoke CSVs — **PASS (cleared)**

```text
$ ls audit_v3_3_3/controls/
LSU_Fault_Control_Pair_FINAL.csv
LSU_Fault_Control_Pair_RAW_685d88f7.csv      # clearly labelled pre-correction archive
LSU_Fault_Control_Pair_RAW.csv

$ find audit_v3_3_3 -iname 'smoke*'
audit_v3_3_3/correction_smoke/…              # only the legitimate A01-R03 correction smoke
```

`controls/smoke.csv` and `controls/smoke_a03.csv` are gone. The surviving `correction_smoke/smoke.csv` contains **no** `685d88f7` rows and points at the final binary:

```text
A01,R03,fault,649,…1,False,SDC,…1126e0fd…,audit_v3_3_3/correction_smoke/A01-R03-fault
A01,R03,control,649,…0,True,UNRESOLVED,…1126e0fd…,audit_v3_3_3/correction_smoke/A01-R03-control
```

---

## 3. R-03 — workbook Readiness_Gate PENDING labels — **PASS (cleared)**

Read-only openpyxl scan of `Readiness_Gate` (71 rows): **no `PENDING` anywhere**. Bottom summary block now:

```text
FaultInjected    | fault run has an injection artifact                          | ENFORCED
ControlClean     | control run injected 0 and oracle PASS                         | ENFORCED
TerminalEvidence | terminal measured by the causal generator                      | ENFORCED
TraceComplete    | COMPLETE / COMPLETE_PROP_TRACE; PARTIAL_WATCHDOG only for HANG  | ENFORCED
Provenance       | gem5 binary SHA and evidence path recorded                     | ENFORCED
Final            | READY_FOR_FORMAL_EXPERIMENT only when every row passes         | PASS (v3.3.3 final; independent audit separate)
```

Per-row `ReadyGate` = **PASS 60 / 60** (9 trailing non-row cells are blank/summary and excluded). Each row `FaultInjected=YES`, `ControlClean=YES`, `TerminalEvidence=MEASURED`.

---

## 4. R-04 — trace-completeness wording — **PARTIAL (core fixed; one stale instance remains)**

The headline evidence table and Q4 now state the literal split correctly:

```text
LSU_v3.3.3_Final_Acceptance_Report.md:53  | Causal rows | 60/60 closed: 50 `COMPLETE` + 5 `COMPLETE_PROP_TRACE` (A03) + 5 `PARTIAL_WATCHDOG` (RP01 HANG) |
LSU_v3.3.3_Final_Acceptance_Report.md:109 4. … Yes, 60/60 closed: 50 `COMPLETE` + 5 `COMPLETE_PROP_TRACE` (A03) + 5 `PARTIAL_WATCHDOG` (RP01 HANG) …
```

```text
$ grep -n '55' audit_v3_3_3/LSU_v3.3.3_Final_Acceptance_Report.md
145:| F-04 trace overclaim | … causal is 55+5, not 60 `COMPLETE` |
163:| Propagation | 60/60 closed (55 COMPLETE_PROP_TRACE + 5 PARTIAL_WATCHDOG accepted for HANG) |
```

**Residual:** the Ready-Gate row (line 163) still reads `55 COMPLETE_PROP_TRACE`, which mislabels the 50 `COMPLETE` rows as `COMPLETE_PROP_TRACE` (only A03's 5 are). Line 145's "55+5" is arithmetically correct as a *count*. This is a documentation wording nit; the corrected breakdown appears verbatim twice in the same report, and every data artifact (`Final_Readiness.csv`, `Final_Readiness_Matrix.csv` worktree copy, causal CSV, workbook) carries `{COMPLETE:50, COMPLETE_PROP_TRACE:5, PARTIAL_WATCHDOG:5}`. **Non-blocking**, but the exact string the task asked to eliminate survives at line 163 and should be edited to "50 COMPLETE + 5 COMPLETE_PROP_TRACE + 5 PARTIAL_WATCHDOG".

Artifact-level check (all consistent):

```text
LSU_60Context_Final_Readiness.csv        {COMPLETE:50, COMPLETE_PROP_TRACE:5, PARTIAL_WATCHDOG:5}
LSU_60Context_Final_Readiness_Matrix.csv {COMPLETE:50, COMPLETE_PROP_TRACE:5, PARTIAL_WATCHDOG:5}   (worktree)
LSU_60Context_Causal_Propagation.csv     {COMPLETE:50, COMPLETE_PROP_TRACE:5, PARTIAL_WATCHDOG:5}
Workbook Fault_Sample_Manifest           {COMPLETE:50, COMPLETE_PROP_TRACE:5, PARTIAL_WATCHDOG:5}
```

---

## 5. R-05 — `audit_v3_3_2` hardlink — **CONFIRMED (historical, out of v3.3.3 scope)**

```text
$ stat -c '%i %h %n' build/ARM/gem5.opt audit_v3_3_3/binary/gem5.opt.v333-1126e0fd audit_v3_3_2/binary/gem5.opt.v332-070d68a6
7341432 3 build/ARM/gem5.opt
7341432 3 audit_v3_3_3/binary/gem5.opt.v333-1126e0fd
7341432 3 audit_v3_3_2/binary/gem5.opt.v332-070d68a6

$ sha256sum build/ARM/gem5.opt audit_v3_3_3/binary/gem5.opt.v333-1126e0fd audit_v3_3_2/binary/gem5.opt.v332-070d68a6
1126e0fd…  build/ARM/gem5.opt
1126e0fd…  audit_v3_3_3/binary/gem5.opt.v333-1126e0fd
1126e0fd…  audit_v3_3_2/binary/gem5.opt.v332-070d68a6
```

The v3.3.2 package's "760d68a6-preserved" file is a third hardlink to the final inode and now hashes `1126e0fd`. It is pre-existing, untracked, and referenced by no v3.3.3 deliverable. **It does not affect the final v3.3.3 binary SHA** (`build/ARM/gem5.opt` = `1126e0fd…`, matching `audit_v3_3_3/binary/SHA256.txt` and all 120 summaries). Recorded as a historical v3.3.2 packaging note only.

---

## 6. Core gates recomputed from raw artifacts

| Gate | Result | Recomputed evidence |
|---|---|---|
| Run set | **PASS** | 120 run dirs; 120 `summary.json`; 60 fault + 60 control |
| One binary | **PASS** | `{1126e0fd…: 120}`, zero other SHAs |
| Fault injection | **PASS** | 60/60 fault `injection_count > 0` |
| Control zero | **PASS** | 60/60 control `injection_count == 0`; 60/60 `oracle = True` |
| Control proofs | **PASS** | 35 `MOUNTED_BUT_DISABLED` / 25 `INJECTOR_ABSENT` / 0 `SUPPRESSED` |
| Fault terminals | **PASS** | SDC 43 / MASKED 12 / HANG_WATCHDOG 5 |
| Control terminals | **PASS** | UNRESOLVED 55 / MASKED 5 (no injection event) |
| Pairing | **PASS** | 60 pairs; 0 seed mismatches; 0 ordinal mismatches |
| ROI arithmetic | **PASS** | 60/60 `N=end−start+1`, `ordinal=start+ceil(p·N)−1`; 0 failures |
| A01 window | **PASS** | 585–713 / N=129 / 597,623,649,675,701 |
| A03 window | **PASS** | 1040–1222 / N=183 / 1058,1094,1131,1168,1204 |
| Causal rows | **PASS** | 60 rows; 0 blank/`n/a` in Injection/Activation/FirstDivergence/Downstream/Consumer/CommitSquashReplay/Terminal/ApplicationOracle |
| Oracle consistency | **PASS** | 43 FAIL (SDC) / 12 PASS (MASKED) / 5 NO_CHECKSUM (HANG); 0 mismatches |
| MASKED mechanisms | **PASS** | 12/12 non-empty (FW02 ×1, SQ03 ×5, MD04 ×1, LQ04 ×5) |
| A03 trace | **PASS** | 5/5 `COMPLETE_PROP_TRACE`; `prop_trace.csv.gz` `gzip -t` OK on all five |
| RP01 HANG | **PASS** | 5/5 `HANG_WATCHDOG`; `target_ordinal=26/77/128/179/230`; checksum None |
| Distinctness | **PASS** | 60/60 `DistinctFromOtherContexts=YES` within model |
| Workbook | **PASS** | 8 sheets; 60 manifest rows; 60 unique `SampleRunID`; 60 unique `Seed`; 60/60 `Gem5BinarySHA256=1126e0fd…`; `ConfigFrozen=YES` ×60 |
| Control_Manifest | **PASS** | 60 rows; `ControlInjected=0` ×60; zero-proof 35/25 |
| Config provenance | **PASS** | `sha256sum configs/se/lsu_proxy.py = 8309da72…`; workbook `ConfigSHA256=8309da72…` all models |
| Workload ELFs | **PASS** | 9/9 provenance SHAs match on-disk bytes (incl. the three under `workloads/directed/`) |
| Regression | **PASS** | `pytest_final2.log` → **232 passed in 142.19s**; `pytest_final.log` → 232 passed; `platform_pytest_final.log` → **121 passed in 4.67s** |
| Dry-run | **PASS** | `dry_run_final.log` → 120 `DRY-RUN` lines; "dry-run: 120 commands; no run dirs written" |
| Source/binary | **PASS** | `git diff --stat b5031bf7 -- CHAOS/gem5/src` empty; worktree diff empty; `v333_build2.log` `error:` count 0, `scons: done building targets` present |
| Gate-test evidence | **PASS** | `MD04-p0.stdout`: `CHAOSMD04 probability=0.0`, golden `0x22be5ae3364d0c9f`; `DA04-p0.stdout`: `injected=0`, golden `0x3f89eab79392ce69` |
| Ledger reconciliation | **PASS** | 47 rows → 11 `VERIFIED_V333`, 32 `CLOSED_V333`, 3 `OPEN_NONBLOCKING` (L-A11, L-D11, L-D15), 1 `SUPERSEDED_BY-L-A12`; 0 blocking |

### Observation (not a defect)
A03-R03's causal row reports `Activation;ordinal=1131` (configured/executed ordinal, matching summary/ROI) while its `Injection`/`FirstDivergence` witness is the first `affected=1` stream event, `event_ordinal=1150`. This is correct trace semantics: the stuck bit latches at 1131 (`A03_ACTIVATION`), and the first load whose EA actually changes is 1150 (`STUCK_APPLIED`). The generator binds `Injection` to the first `affected=1` line (`tools/lsu_v333_propagation.py:628-643`); the configured ordinal stays 1131. No gate is violated and the row is internally explained by its `reason=ALREADY_STUCK`/`STUCK_APPLIED` fields.

---

## 7. Package readiness — 14 required items (plan Task 10, Step 4)

| # | Required item | Status | Location |
|---|---|---|---|
| 1 | Final Acceptance Report | PRESENT | `audit_v3_3_3/LSU_v3.3.3_Final_Acceptance_Report.md` |
| 2 | Master Defect Ledger | PRESENT | `audit_v3_3_3/LSU_v3.3.3_Master_Defect_Ledger.csv` |
| 3 | Consolidated Repair Plan | PRESENT | `audit_v3_3_3/LSU_v3.3.3_Consolidated_Repair_Plan.md` |
| 4 | Researcher Decision Packet (+ approval) | PRESENT | `…_Researcher_Decision_Packet.md`; `decisions/LSU_v3.3.3_Researcher_Approval.md` |
| 5 | Workbook | PRESENT | `audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx` |
| 6 | 60Context Final Readiness | PRESENT | `LSU_60Context_Final_Readiness.csv` (and `_Matrix.csv`) |
| 7 | Causal Propagation | PRESENT | `LSU_60Context_Causal_Propagation.csv` (+ `propagation/…_Final.csv`) |
| 8 | Fault Control Final Audit | PRESENT | `LSU_Fault_Control_Final_Audit.csv` (== `controls/…_FINAL.csv`) |
| 9 | Workload Oracle Audit | PRESENT | `LSU_12Model_Workload_Oracle_Audit.csv` |
| 10 | Final Binary Provenance | PRESENT | `LSU_Final_Binary_Provenance.md` (== `build/PROVENANCE.md`) |
| 11 | Final Source Diff patch | PRESENT (under `build/`) | `audit_v3_3_3/build/LSU_Final_Source_Diff.patch` |
| 12 | Independent Acceptance | PRESENT as `reports/…` | `reports/Agent_F_Final_Independent_Acceptance.md` (top-level `LSU_Independent_Acceptance.md` alias absent) |
| 13 | Raw pilot traces/logs/oracles/tests | PRESENT | `runs/` (120 × ~13 files), `runs_685d88f7/`, `gate_tests_final/`, `census/`, `correction_smoke/` |
| 14 | Exact commands and runner config | PRESENT | `build/RUNBOOK.md`, `runs/*/command.txt`, `config.json`, `dry_run_final.log` |
| — | Zip + sidecar | **NOT BUILT** (expected) | no `LSU_v3.3.3_*.zip` yet |

No required item is missing in substance. Items 11 and 12 live under `build/` and `reports/` rather than the exact top-level paths named in the plan/acceptance report; item 12's referenced filename `LSU_Independent_Acceptance.md` does not exist as an alias. Note these before zipping.

---

## 8. Remaining findings

- **R-04-residual — LOW (non-blocking, documentation).** `LSU_v3.3.3_Final_Acceptance_Report.md:163` still reads "55 COMPLETE_PROP_TRACE" (and line 145 says "55+5"). Correct breakdown (50 `COMPLETE` + 5 `COMPLETE_PROP_TRACE` + 5 `PARTIAL_WATCHDOG`) already appears at lines 53 and 109–110 and in every data artifact. Fix: reword line 163.
- **P-01 — LOW (provenance/commit hygiene).** `audit_v3_3_3/LSU_60Context_Final_Readiness_Matrix.csv` is modified in the worktree (corrected `COMPLETE_PROP_TRACE`/`PARTIAL_WATCHDOG` labels) but **not committed**; HEAD `135ebcfe` still has the stale `{COMPLETE:50, PARTIAL:10}` split for that file. The top-level `LSU_60Context_Final_Readiness.csv` at HEAD is already correct, so the primary deliverable is fine. Commit the Matrix fix before zipping so git matches the package.
- **P-02 — INFO.** Acceptance report §4 references `LSU_Independent_Acceptance.md`, which does not exist; the actual independent-acceptance artifact is `reports/Agent_F_Final_Independent_Acceptance.md`. Add the alias or correct the reference.
- **P-03 — INFO.** `audit_v3_3_2/binary/gem5.opt.v332-070d68a6` is a hardlink to the final binary (inode 7341432) and hashes `1126e0fd`; pre-existing v3.3.2 packaging artifact, outside the v3.3.3 package, no effect on the final binary SHA (R-05 above).
- **P-04 — INFO (out of scope).** `audit_v3_3_3/LSU_Fault_Control_Audit.csv` is an untracked duplicate of the tracked `LSU_Fault_Control_Final_Audit.csv`; not a required item.

No blocking defect was found. No measured data, seed, ordinal, binary SHA, or gate result is invalidated by any remaining finding.

---

## 9. Final verdict

**`READY_FOR_FORMAL_EXPERIMENT`**

- **F-05 fixed and verified end-to-end:** tool tuple (`tools/lsu_v333_propagation.py:55-56`), causal CSV, workbook `Causal_Propagation` and `Fault_Sample_Manifest`, ROI mapping all carry `A01 585–713/N=129` and `A03 1040–1222/N=183`; all 60 ordinals satisfy `start+ceil(p·N)−1`; zero stale `1040-1234`/`N=195` anywhere in the deliverables or workbook.
- **R-02 and R-03 cleared; R-05 confirmed out-of-scope.**
- **All core gates re-derive exactly from raw artifacts:** 120 summaries on one SHA `1126e0fd…`; 60/60 fault inject > 0; 60/60 controls == 0 with oracles PASS; 35/25 zero-proof; 43 SDC / 12 MASKED / 5 HANG_WATCHDOG; 12/12 MASKED mechanisms; RP01 target ordinals 26/77/128/179/230; 60/60 distinct; workbook 8 sheets / 60 unique IDs / 60 unique seeds; regression 232 + 121; dry-run 120; `git diff b5031bf7 -- CHAOS/gem5/src` empty; build 0 errors; 9/9 ELF SHAs.
- **Package:** all 14 required items present on disk; only the zip is not yet built. Recommended one-line edits/commits before zipping: reword acceptance-report line 163 (R-04-residual), commit the `Final_Readiness_Matrix.csv` label fix (P-01), and reconcile the `LSU_Independent_Acceptance.md` reference (P-02). None of these touches measured data.

The experiment itself is sound, reproducible, and traceable to a single binary and config. Authorize the formal campaign only after the main agent acknowledges the three LOW/INFO cleanups above.
