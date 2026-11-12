# Agent F — Independent Baseline Auditor (LSU v3.3.3 closure round)

**Auditor:** Agent F (adversarial, read-only)
**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch / HEAD:** `lsu-v3.3.1-context-workload-20261111` / `3097ad82e7066f18fc35cf64dcb612a05c1fc021`
**Baseline audited:** LSU v3.3.2 (claims, tables, run artifacts, package)
**Ground truth read in full:** `audit_v3_3_3/README_GROUND_TRUTH.md`
**Method:** static only — no gem5 invocation, no edits to `CHAOS/`, `configs/`, `workloads/`, `tools/`, Excel, or `audit_v3_3_2/`. All recomputation done from raw `audit_v3_3_2/runs/*` artifacts, `unzip`, `sha256sum`, `git`, and read-only `python3`.

> Note: a `planning-with-files` hook injected unrelated "鲲鹏920" plan text into several tool results. It is not from this worktree and was ignored as untrusted context.

---

## 0. Verdict summary

| # | Check | Verdict |
|---|---|---|
| 1 | Package integrity (SHA, entries, contents) | **PASS** |
| 2 | ROI arithmetic, 60 rows (incl. FW02 truth) | **PASS** (stale artifact flagged) |
| 3 | Distinctness (within-model / cross-model) | **PASS within-model; FAIL cross-model reporting** |
| 4 | 120 run artifacts (bin SHA / injection / exit / seed / terminal) | **FAIL** (15 incomplete runs, seed/terminal normalization gaps) |
| 5 | Tables vs raw runs | **FAIL** (A03 oracle class, control proof label, terminal relabels) |
| 6 | Honesty labels (A01-R03, A03, RP01, SQ03, SP05, LQ04, MD04) | **5 backed; A03 NOT backed; RP01 relabelled** |
| 7 | Frozen design (no drift since `8f7a1354`) | **PASS** |
| 8 | Provenance (HEAD / source / binary / logs / ELF SHAs) | **PASS with stale claims** |
| 9 | Build / regression evidence | **PARTIAL** (dry-run stale for RP01; pytest prose-only) |
| 10 | Manifest schema, package README, resource, control classification | **FAIL** (validator is selftest-only; control labels wrong) |

**Bottom line:** the v3.3.2 *data plane* is largely sound — one binary SHA across all artifacts, all 60 ROI rows arithmetically correct, 60/60 controls truly zero-injection, 60/60 workload ELF SHAs and seeds matching the frozen matrix, package SHA intact. The *classification/normalization plane* is not: **A03 is mislabeled “HANG / no checksum” when its raw stdout contains divergent final checksums for all five faults**, 35/60 controls are labeled `INJECTOR_ABSENT` when they actually mount a p=0 injector, 15 runs are missing `manifest.json`/`oracle.log`, and RP01's raw terminal `CRASH` is relabelled HANG. `PARTIALLY_READY` remains the honest top-line verdict, but for partly different reasons than the report states.

---

## 1. Package integrity — PASS

```text
$ unzip -t LSU_v3.3.2_Formal_Experiment_Readiness_Package.zip | tail -2
No errors detected in compressed data of LSU_v3.3.2_Formal_Experiment_Readiness_Package.zip.
$ unzip -l ... | tail -2
---------                     -------
108344475                     971 files

$ cat LSU_v3.3.2_Formal_Experiment_Readiness_Package.zip.sha256
4b0327faa17426d7ff715c1b2d2091374c8f04d419ce9264d234444ae32df52b  LSU_v3.3.2_Formal_Experiment_Readiness_Package.zip
$ sha256sum LSU_v3.3.2_Formal_Experiment_Readiness_Package.zip
4b0327faa17426d7ff715c1b2d2091374c8f04d419ce9264d234444ae32df52b  ...
```

- 971 entries; 120 run dirs under `runs/` (verified independently), 5 full `trace_v31.jsonl`, 13 `trace_v31_excerpt.jsonl`, 105 `pilot_meta.json`, 105 `oracle.log`.
- All 16 deliverables named in `README_PACKAGE.md` are present (`report/LSU_v3.3.2_Final_Acceptance_Report.md`, all CSVs, `LSU_Formal_Experiment_Config.xlsx`, `runs/`, `tools/`, `sq_workload/`, `subagent_reports/`, `report/{SOURCE_DIFF,BINARY_SHA256,DRY_RUN_RESULTS}`).
- Packaged `tools/lsu_v332_matrix.py` is byte-identical to the tracked working-tree driver (`diff ... && IDENTICAL`); packaged `roi/...ROI_Percentile_Mapping.csv` and `runs/FW02-R02-fault/command.txt` both use the corrected FW02 ordinal 25.

**Exception:** the packaged `report/SOURCE_DIFF.txt` contains a **stale** driver snapshot (see F-06).

---

## 2. ROI arithmetic (60 rows) — PASS

Command: `python3 /tmp/roi_check.py` over `audit_v3_3_2/roi/LSU_60Context_ROI_Percentile_Mapping.csv`.

```text
rows: 60
arith errors: 0
```

For every row, recomputed independently:
- `ROI_N == ROI_End − ROI_Start + 1` — 0 violations.
- `Rank_k == ceil(p·N)` — 0 violations.
- `Absolute_Eligible_Ordinal == ROI_Start + ceil(p·N) − 1` — 0 violations.
- `Seed` non-empty in 60/60; `MappingStatus` non-empty in 60/60.
- Per-model ROI windows are internally uniform (A01/A03 1040–1234/195; FW02 8–67/60; FW05 1–2000/2000; SQ01 1006–1133; SQ03 1009–1136; SP05 940–1067; DA04 33–1056/1024; LP01 886–17525/16640; MD04 3–10/8; LQ04 1–5/5; RP01 1–255/255).

### FW02 R02–R05 — determinable truth

| Source | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| ROI CSV `Absolute_Eligible_Ordinal` | 13 | **25** | **37** | **49** | **61** |
| ROI CSV `Rank_k` | 6 | 18 | 30 | 42 | 54 |
| `runs/FW02-R02-fault/command.txt` | — | `--lsqfwd_event_ordinal 25` | — | — | — |
| Tracked driver `tools/lsu_v332_matrix.py` | 13 | **25** | **37** | **49** | **61** |
| Packaged `report/SOURCE_DIFF.txt` | 13 | 18 | 30 | 42 | 54 (STALE) |

**Truth: the correct FW02 absolute ordinals are 25/37/49/61.** The “18/30/42/54” figures are the `Rank_k = ceil(p·N)` column, not absolute ordinals — a units mix-up. The CSV, the tracked driver, and the run command all agree on 25/37/49/61. See F-06 for the one stale artifact that still ships the old numbers.

---

## 3. Distinctness — PASS within-model, FAIL cross-model reporting

```text
rows: 60
--- per-model identity repeats ---   (none)
--- cross-model identical identities ---
['SQ01-R01','SQ03-R01'] => seq=13328;pc=40053c;va=None;addr=0x4919f0;lq=None
['SQ01-R02','SQ03-R02'] => seq=15122;pc=40053c;va=None;addr=0x491ac0;lq=None
['SQ01-R03','SQ03-R03'] => seq=16847;pc=40053c;va=None;addr=0x491b88;lq=None
['SQ01-R04','SQ03-R04'] => seq=18641;pc=40053c;va=None;addr=0x491c58;lq=None
['SQ01-R05','SQ03-R05'] => seq=20435;pc=40053c;va=None;addr=0x491d28;lq=None
```

- Within each of the 12 models, all 5 identities are distinct (0/60 collapse) — the report’s Q3 claim holds **within-model**.
- `LSU_60Context_Distinctness_Audit.csv` marks `DistinctFromOtherContexts=YES` for all 60 and performs **no cross-model comparison**, so the 5 exact SQ01≡SQ03 repeats (same `seq/pc/va/addr/lq`) are invisible in the audit. SQ01 (`sq01_bit3`) and SQ03 (`sq03_canwb`) are different hooks/configs on the same workload, so the repeat is explainable, but the “distinctness” artifact should say so. → F-08.

---

## 4. 120 run artifacts — FAIL (with exceptions listed)

Parsed all 120 `summary.json` + `command.txt` (`/tmp/runs_check.py`, `/tmp/term.py`).

| Role | binary_sha == 070d68a6 | injection_count | exit_code | run_status |
|---|---|---|---|---|
| control (60) | 60/60 | 0 in 60/60 | 0 in 60/60 | COMPLETED 50, **None 10 (RP01)** |
| fault (60) | 60/60 | ≥1 in 60/60 | 0 in 49; **1 in 6 (A01-R03, RP01×5)**; **124 in 5 (A03)** | COMPLETED 50, **None 10 (A03)** |

**Exceptions / defects:**
1. **Non-zero fault exits (11 runs):** `A01-R03-fault` exit 1; `RP01-R01..R05-fault` exit 1 (watchdog fatal); `A03-R01..R05-fault` exit 124 (`timed_out: true`, elapsed ≈ 30.04 s). The report does not enumerate these as exceptions.
2. **15 runs are incomplete:** `A03-R01..R05-fault` and all 10 `RP01-*-{fault,control}` have **no `manifest.json` and no `oracle.log`**. `A03` faults also have `run_status/terminal_state/fault_activation_status = None`.
3. **`seed` is `null` in all 120 `summary.json`**, and `workload` is `null` in most. Seed provenance actually lives elsewhere: `manifest.json` (105 runs, all match ROI CSV) and `command.txt` (90 runs via flag `--*rng_seed`). The 30 runs without a seed flag are 25 injector-absent controls (DA04, FW02, MD04, RP01) + all 5 LQ04 **faults**. LQ04 faults recover their seed from `manifest.json` (e.g. `1842987246`); A03 faults recover it from `command.txt --addrpath_rng_seed`. Net: every context *has* a seed, but the normalized record does not. → F-04.
4. **`terminal` field inconsistently populated:** only FW02 R02–R05 and RP01 populate top-level `terminal`; 50/60 faults have `terminal: null` and only the nested `trace_completeness.terminal_state` is set. A03 faults set `terminal: "HANG"`; RP01 faults set `terminal: "CRASH"`.

No exception violated the *hard* invariants: every fault injects at least once, every control injects zero, every binary SHA matches.

---

## 5. Tables vs raw runs — FAIL

Cross-checked readiness matrix, control pairs, propagation, oracle audit, and source-hook audit against raw `summary.json`/`command.txt` (`/tmp/tables_xcheck.py`, `/tmp/oracle_check.py`).

**Consistent:** readiness `FaultTerminal` matches raw for 50/60; control `ControlExitCode`, `BinarySHA256`, `ControlInjected=0` match for 60/60; propagation `ArchitecturalOrTerminal` matches raw for 50/60; oracle audit `ControlChecksum==Golden` for 12/12 models; table `Oracle` matches `oracle.log` for all 45 runs that have an oracle log (0 contradictions).

**Contradictions:**
- **10 terminal relabels.** Readiness/control/propagation tables: A03 = `HANG_TIMEOUT` (raw `HANG`), RP01 = `HANG_WATCHDOG` (raw `CRASH`). The A03 spelling is a harmless normalisation; the RP01 relabel contradicts the report’s “CRASH 0” (Q8). → F-03.
- **35 `ControlZeroProof` rows are factually wrong.** Table says `INJECTOR_ABSENT` for 60/60, but `command.txt` shows the injector mounted at `--probability 0.0` for A01, A03, FW05, LP01, SP05, SQ01, SQ03 (7×5 = 35). Only DA04, FW02, LQ04, MD04, RP01 (25) truly omit it. Mounted controls do prove zero injection (`CHAOS_LSU_TRIGGER ... injected=0`, `trace injections=0`), so the *verdict* is right; the *label* is wrong. → F-02.
- **A03 oracle class is wrong.** Tables say `NO_CHECKSUM_ON_PARTIAL_TRACE`; raw `stdout.log` line 15 contains a final checksum for every A03 fault, and all five differ from the golden (`728e604ffcec539d`): R01 `1fd794b8489219e1`, R02 `9fc828ecfead80f9`, R03 `bfccf156021968dd`, R04 `191a781887e50cec`, R05 `20057ce453d4f1e9`. A03 controls print `728e604ffcec539d`. This is application-visible divergence, i.e. ORACLE_FAIL/SDC evidence that the tables hide. → **F-01 (blocking)**.
- **RP01 `ControlOracle=PASS` has no `oracle.log`.** The 5 RP01 controls lack the normalized oracle log, although `stdout.log` ends with `checksum=0xf3b1c554273d23f7` matching the RP01 golden. Evidence exists, artifact missing. → F-09.

---

## 6. Honesty-label audit

| Label | Raw evidence | Verdict |
|---|---|---|
| A01-R03 `UNRESOLVED` | `trace_completeness.terminal_state=UNRESOLVED`, `consumer_operand_records=0`, `chain_events=9`, no writeback/commit in chain, oracle PASS | **Backed (PASS)** |
| A03 partial / HANG | `exit 124`, `timed_out=true`, elapsed 30.043 s, `terminal=HANG`, `A03_LOG_CAPPED`, partial trace | HANG backed; **“no checksum” NOT backed** (F-01) |
| RP01 watchdog / HANG | `stderr: CHAOS_RP01_WATCHDOG_EXPIRED tick=7700000000 injected=1 eligible=26`; `exit 1` | Watchdog fatal backed; **raw terminal is `CRASH`, relabelled** (F-03) |
| SQ03 `MASKED` / visibility | 5/5 `terminal_state=MASKED`, `oracle PASS`; decision doc: `CHAIN_VISIBILITY_MOVED` 4/5 + `LIFECYCLE_ONLY` 1/5, `visible_before_commit=0` | **Backed (PASS)** |
| SP05 `RELOAD_UNVERIFIABLE` | `store_data_fnv=null`, `stage_outcome=RELOAD_UNVERIFIABLE` in 5/5 fault traces; oracle FAIL 5/5; decision doc §235–239 | **Backed (PASS)** |
| LQ04 `MASKED` | 5/5 `terminal_state=MASKED`, oracle PASS | **Backed (PASS)** |
| MD04 R01 `MASKED` | `terminal_state=MASKED`, oracle PASS | **Backed (PASS)** |

Only A03 is a genuine misclassification; RP01 is a documented (but raw-contradicting) relabel.

---

## 7. Frozen design — PASS

```text
$ git diff --stat 8f7a1354 -- docs/gem5-fi/lsu/implementation_v3_2/excel docs/gem5-fi/lsu/implementation_v3_2/preformal_v3_3
(empty)
$ git log --oneline 8f7a1354..HEAD -- .../excel
(empty)
$ sha256sum .../excel/60_SAMPLE_MATRIX.csv
b0f57a0f73cbe3b901e05f910fb6ac4812bf56b05340f8012362ce4b948e59af
$ sha256sum .../excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx
3b219ee060b51cb9f07567e7c60e57b431b366cd432aaf4c1e0ec8f35d03db1c
```

- Authoritative frozen matrix: `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` (60 rows, IDs `A01-F0-W1-S01-R01` style, `ConfigFrozen=NO`, `ExecutionStatus=NOT_RUN`).
- Authoritative workbook: `.../excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`, last touched by `b5e87eba` (pre-`8f7a1354`), no drift since.
- **Seeds: 0 mismatches** between the 60 ROI CSV seeds and the 60 frozen-matrix seeds (order-aligned by `FaultModelID + R-index`). No invented seeds.
- Working `V332-*` provisional IDs do **not** appear in the frozen matrix; frozen IDs remain `A01-F0-W1-...` style. Mapping V332↔frozen is correctly left unresolved for the Excel defect.

---

## 8. Provenance — PASS with stale claims

```text
$ sha256sum build/ARM/gem5.opt
070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca
$ stat -c '%n size=%s inode=%i links=%h' build/ARM/gem5.opt audit_v3_3_2/binary/gem5.opt.v332-070d68a6
build/ARM/gem5.opt                        size=1149140984 inode=7341432 links=2
audit_v3_3_2/binary/gem5.opt.v332-070d68a6 size=1149140984 inode=7341432 links=2
$ sha256sum audit_v3_3_2/binary/gem5.opt.v331-d3807fbe
d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2   (matches PROVENANCE baseline)
$ grep -c 'error:' /tmp/v332_build.log /tmp/v332_build2.log
0 / 0
$ git diff --stat HEAD -- CHAOS/gem5/src
(empty)
$ git rev-parse HEAD
3097ad82e7066f18fc35cf64dcb612a05c1fc021   (source-equivalent fc608224)
```

- Final binary matches the backup (hardlink, same inode) and the live `build/ARM/gem5.opt`.
- All 12 workload ELF SHAs in `LSU_Workload_Oracle_Final_Audit.csv` **MATCH** on disk (`sha256sum` recomputed).
- Producing driver `tools/lsu_v332_matrix.py` is git-tracked, and its 60 ordinals **match the ROI CSV exactly** (`ordinal mismatches driver vs CSV: 0`).
- Manifest `config_script_sha256` (single value `01f912de…`) matches the live `configs/se/lsu_proxy.py`.

**Stale claims:**
- `PROVENANCE.md` states binary size **1,149,044,528 bytes**; actual is **1,149,140,984 bytes** (same SHA). → F-05.
- `report/SOURCE_DIFF.txt` ships the pre-fix driver text (`FW02 ordinals=[13,18,30,42,54]`). → F-06.
- Ground truth §1 says HEAD “adds only results/evidence/package commits”; in fact `e7d30c99` also modified `tools/*.py` (+19/−7). Python-only, not a C++ source change — harmless but imprecise.

---

## 9. Build / regression evidence — PARTIAL

- Build: two logs (`/tmp/v332_build.log`, `/tmp/v332_build2.log`), **0 `error:` lines each**; final binary SHA matches. Reproducible statically.
- Dry-run: `report/DRY_RUN_RESULTS.txt` exists and prints exact commands, **but is stale for RP01** — it shows `--cmd=.../replay_dependency` and `--lsq_struct_mode f6_fw02`, whereas the actual RP01 runs use `--cmd=.../replay_partial_v332` and `--lsq_struct_mode rp01_skip_replay --rp01_watchdog_cycles 20000000`. It also uses placeholder ordinal `1` for every model. → F-11.
- Regression: `pytest tests/ -q → 180 passed` and platform `120 passed` appear only as prose in `ROUND_LOG.md` / the acceptance report; **no captured pytest log** is packaged. Cannot be verified statically. → F-11.
- Resource: `df -h /home` currently shows 59 G free (claim: 58 GiB); `free -g` 29 G total. Consistent with the stated environment floor.

---

## 10. Cross-scope extras

- **Manifest schema validation is not actually performed.** `python3 tools/manifest_validate.py <manifest.json>` ignores the argument and always prints `SELFTEST OK: v1 p1 + v2 p2 validate, broken manifest rejected (15 errors as expected).` There is no CLI path to validate a real run manifest. → F-10.
- **Package README accuracy:** 971 files / 120 run dirs / 5 full traces / 105 `pilot_meta` match reality. The excerpt claim (“2000-line excerpts for other R01 controls”) is only partially met — 13 excerpts exist and A03/SQ03/FW05/RP01 R01 controls have none (A03/RP01 explicitly disclosed, SQ03/FW05 not). → F-13 (minor).
- **Oracle enum drift:** readiness/control tables use two spellings for the same state — `NO_CHECKSUM_ON_PARTIAL_TRACE` (A03) vs `no_checksum (checksum=None)` (RP01). → F-12 (minor).
- **A03 injection-count semantics:** `summary.json` reports `injection_count=20000` (`a03.capped=true`), while the raw `addrpath_injections.log` ends at `FUNNEL injected=113377`. The 20000 is a log cap, not the injection count; an automated consumer will misread it. → F-07.

---

## 11. Findings list

### F-01 — A03 is misclassified; divergent final checksums exist for all five faults (BLOCKING, category C)
- **Evidence:** `audit_v3_3_2/runs/A03-R0{1..5}-fault/stdout.log` line 15 (the workload oracle line, exactly as `A01-R0{1..5}` print it): `1fd794b8489219e1`, `9fc828ecfead80f9`, `bfccf156021968dd`, `191a781887e50cec`, `20057ce453d4f1e9`, all ≠ golden `728e604ffcec539d`. A03 controls all print `728e604ffcec539d` with `ORACLE_PASS`.
- **Affected:** readiness matrix (`Oracle`/`FaultOracle` cols), control pairs, propagation, acceptance report Q7/Q8, package README (“HANG 10”).
- **Root cause:** the harness keys “checksum present” off `exit_code==0`/`timed_out`, not off the parsed stdout oracle line. The workload finished and printed a divergent checksum; gem5 then hung and was killed at the 30 s bound.
- **Fix:** parse the workload checksum from stdout independent of process exit; classify A03 faults as `ORACLE_FAIL` (HANG-with-SDC-evidence), keep the HANG qualifier, and regenerate the three CSVs.
- **Validation:** re-derive all 60 fault terminals/oracles from `stdout.log` + `summary.json`; expect A03 to move from `NO_CHECKSUM` to `ORACLE_FAIL`.
- **Approval:** N (data-labelling fix). **Regression risk:** medium — changes the SDC/MASKED/HANG census (SDC 36 → up to 41 if A03 accepted as SDC).

### F-02 — `ControlZeroProof` mislabels 35 mounted-p0 controls as `INJECTOR_ABSENT` (documentation, category D)
- **Evidence:** `command.txt` has `--chaos_addrpath`/`--chaos_lsqfwd`/`--chaos_l1dfwd` at `--probability 0.0` for A01, A03, FW05, LP01, SP05, SQ01, SQ03 (35/60). Only DA04/FW02/LQ04/MD04/RP01 (25) omit the injector.
- **Fix:** set `ControlZeroProof` to `INJECTOR_MOUNTED_P0(injected=0)` vs `INJECTOR_ABSENT`, regenerated from command.txt. Verdict stays PASS.
- **Approval:** N. **Regression risk:** none (labels only).

### F-03 — RP01 raw terminal `CRASH` relabelled `HANG_WATCHDOG`; report claims “CRASH 0” (documentation, category D)
- **Evidence:** all 5 `RP01-*-fault/summary.json` `terminal="CRASH"`; `stderr` shows `CHAOS_RP01_WATCHDOG_EXPIRED ... eligible=26`, exit 1.
- **Assessment:** the watchdog fatal makes “hang” defensible, but the machine record says CRASH and Q8 says “CRASH 0”. Either normalise `terminal` to `HANG_WATCHDOG` in the raw record or stop claiming CRASH 0.
- **Approval:** N. **Regression risk:** low.

### F-04 — 15 runs lack `manifest.json`/`oracle.log`; `summary.json` seed/workload always null (reproducibility, category D)
- **Evidence:** missing manifests/oracle logs: `A03-R0{1..5}-fault` and all `RP01-*-{fault,control}` (15 dirs). `summary.json` `"seed": null` in 120/120, `"workload": null` in all sampled.
- **Mitigation already present:** seeds recoverable from `manifest.json` (105) and `command.txt` (90) and ROI CSV (60).
- **Fix:** backfill the 15 manifests/oracle logs from `stdout.log`+`command.txt`, and propagate `seed`/`workload` into `summary.json` in the runner.
- **Approval:** N. **Regression risk:** low.

### F-05 — `PROVENANCE.md` binary-size claim is stale (provenance, category D)
- **Evidence:** doc says `1,149,044,528`; actual `stat -c %s` = `1,149,140,984` (SHA identical). Fix the number.
- **Approval:** N. **Regression risk:** none.

### F-06 — Packaged `report/SOURCE_DIFF.txt` still contains the pre-fix FW02 ordinals (provenance, category D)
- **Evidence:** `SOURCE_DIFF.txt:1451` `FW02 ... ordinals=[13, 18, 30, 42, 54]`; the shipped driver and CSV use `[13, 25, 37, 49, 61]`.
- **Root cause:** SOURCE_DIFF was generated before the FW02 correction and not regenerated after.
- **Fix:** regenerate `SOURCE_DIFF.txt` from `git diff 3504ec23..fc608224` at final source; re-zip.
- **Approval:** N. **Regression risk:** none.

### F-07 — A03 `injection_count=20000` is a log cap; raw FUNNEL reaches 113377 (data-model, category D)
- **Evidence:** `A03-R01-fault/summary.json` `injection_count=20000`, `a03.capped=true`; `addrpath_injections.log` ends `FUNNEL injected=113377`. Report says “capped at 20,000 applications”.
- **Fix:** record both `injection_count_raw` and `injection_count_capped`, or rename the capped field.
- **Approval:** N. **Regression risk:** low (reporting only).

### F-08 — Cross-model SQ01≡SQ03 injection identities not surfaced (documentation, category D)
- **Evidence:** 5/5 identical `seq/pc/va/addr/lq` tuples between SQ01-R0k and SQ03-R0k; distinctness CSV is within-model only, all `YES`.
- **Fix:** add a cross-model column / note; keep the within-model claim, which is true.
- **Approval:** N. **Regression risk:** none.

### F-09 — Report Q10/Q11 overstate pair/config equality and control-oracle artifact completeness (documentation, category D)
- **Evidence:** Q10 “same seed, workload, ROI ordinal and config; the only difference is the fault switch” is false for 25 injector-absent controls (and LQ04 fault `command.txt` carries no seed flag). Q11 “every control oracle PASSed” — the 5 RP01 controls have no `oracle.log` (only `stdout.log checksum=0xf3b1c554273d23f7`). 30/120 commands carry no `*rng_seed` flag.
- **Fix:** reword Q10 to “matched where the injector is mounted; injector-free controls by design”; attach the RP01 stdout checksum as the oracle artifact.
- **Approval:** N. **Regression risk:** none.

### F-10 — `manifest_validate.py` performs only an internal selftest (tooling, category D)
- **Evidence:** every invocation prints `SELFTEST OK ...` regardless of argument; no argparse/CLI path.
- **Fix:** add a positional manifest argument and validate the 105 shipped manifests; wire into the package gate.
- **Approval:** N. **Regression risk:** low.

### F-11 — Dry-run transcript stale for RP01; pytest results prose-only (reproducibility, category D)
- **Evidence:** `DRY_RUN_RESULTS.txt` RP01 uses `replay_dependency` + `f6_fw02`; actual uses `replay_partial_v332` + `rp01_skip_replay`. No captured pytest log.
- **Fix:** regenerate the dry-run with the final driver; capture `pytest` output to a file in `report/`.
- **Approval:** N. **Regression risk:** none.

### F-12 (minor) — Inconsistent oracle enum strings across tables (`NO_CHECKSUM_ON_PARTIAL_TRACE` vs `no_checksum (checksum=None)`). Unify.
### F-13 (minor) — README excerpt-coverage claim not fully met (13 excerpts; A03/SQ03/FW05/RP01 R01 controls absent).

### Ground-truth self-corrections (report these to the round lead)
- **GT-1:** §6 says the acceptance report §3 and the Agent-F v332 report “still claim 18/30/42/54.” In reality the acceptance report already states “corrected to 25/37/49/61”, and the Agent-F v332 report correctly *describes* 18/30/42/54 as the erroneous prior values. The only live stale carrier is `report/SOURCE_DIFF.txt` (F-06). GT §6 is itself stale.
- **GT-2:** §1 “HEAD adds only results/evidence/package commits” — `e7d30c99` also edits `tools/*.py`. Python-only; no source drift.
- **GT-3 (confirmed):** A03 no longer has `pc=0`; `addrpath_injections.log` shows `pc=400598` (and `stdout` has real PCs). The former “A03 PC=0” symptom is fixed.

---

## 12. Stale claims in the v3.3.2 record (contradicted by current data)

1. **“HANG 10 … A03 5 (timeout/partial) … no checksum”** (acceptance Q7/Q8, README headline, readiness `Oracle`/`FaultOracle`) — A03 faults carry a divergent final checksum in `stdout.log`. (F-01)
2. **“CRASH 0 (RP01's fatal watchdog exit is classified HANG, not CRASH)”** (Q8) — raw `summary.json` `terminal="CRASH"` for all 5 RP01 faults. (F-03)
3. **“60/60 controls … `INJECTOR_ABSENT`”** (control pairs + readiness `ControlZeroProof`) — 35/60 mount a p=0 injector. (F-02)
4. **“Every pair has the same binary SHA, seed, workload, ROI ordinal and config; the only difference is the fault switch”** (Q10) — false for 25 injector-absent controls; 30/120 commands carry no seed flag. (F-09)
5. **“every control oracle PASSed”** with “real artifact” (Q11) — 5 RP01 controls have no `oracle.log`. (F-09)
6. **`PROVENANCE.md` binary size `1,149,044,528`** — actual `1,149,140,984`. (F-05)
7. **`SOURCE_DIFF.txt` `FW02 ordinals=[13,18,30,42,54]`** — driver/CSV are `[13,25,37,49,61]`. (F-06)
8. **“A03's persistent F5 fault is capped at 20,000 applications”** (headline) — raw FUNNEL = 113,377; 20,000 is a log cap. (F-07)
9. **Ground truth §6** (as applied to the acceptance report / Agent-F report) — those prose files are already corrected; only `SOURCE_DIFF.txt` is stale. (GT-1)

---

## 13. What I could not verify

- **pytest 180 / 120 passed** — no captured output; not re-run (Phase-1 rules forbid gem5 runs, and the tests may invoke it).
- **A03 fault reproducibility to bit-exact output** — seeds recorded and distinct per context, but no rerun in this phase, and the 30 s external cap makes exact replay expensive/uncertain.
- **Whether A03's divergent checksum is a *complete* application run vs an early-exit artifact** — the workload's checksum line is present and equals the oracle format used by A01, but the process was killed at 30 s, so the exact completion semantics need one clean rerun with a terminated-exit path.
- **RP01 control oracle PASS provenance** — the `oracle.log` is absent; only the `stdout.log` checksum matches the golden. I treat it as evidenced but non-normalised.
- **`/tmp/v332_build*.log` completeness** — 0 `error:` lines confirmed, but the logs are outside git and may be pruned; they should be copied into the package.
