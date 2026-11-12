# Agent F — Independent Preflight Baseline Audit (LSU v3.3.3)

**Auditor:** Agent F (independent baseline preflight; wrote none of the audited artifacts)
**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Repo HEAD at audit:** `b8405580b09e9d85c59af0b64ed2215aba41a95a` (branch `lsu-v3.3.1-context-workload-20261111`)
**Final source HEAD claimed/verified:** `b5031bf7d857ca7901810a3bf3629f5649ddaaac`
**Final binary claimed/verified:** `build/ARM/gem5.opt` = `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Final config claimed/verified:** `configs/se/lsu_proxy.py` = `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
**Mode:** read-only. No gem5, no scons. Only this file was written. Tools used: `sha256sum`, `unzip -t/-l/-p`, `git`, `stat`, `df/free/nproc/pgrep`, read-only `python3` + openpyxl.

**Method:** every number below was recomputed from raw artifacts (`audit_v3_3_3/runs/*/` 120 summaries + 120 manifests, the ROI/controls/propagation/readiness CSVs, the workbook via openpyxl, the build/dry-run logs, git, and the binary). The v3.3.3 "READY" claim, the Final Acceptance Report, and `LSU_Independent_Acceptance.md` were treated as claims to re-test, not trusted.

---

## 0. Preliminary verdict

> ## `READY_TO_LAUNCH_FORMAL_CAMPAIGN = NO`
>
> The **60×2 measured matrix re-derives correctly** (12 models, 60 contexts, 60 fault + 60 control, one binary, zero-injection controls, oracle split 43/12/5, pairing, ROI arithmetic, ELF SHAs, source/binary/config provenance). The scientific core is sound.
>
> However, the **launch tooling that will generate the formal campaign's own provenance is stale**: the persisted run manifests (105/120) carry `warmup=NEEDS_RESEARCHER_CONFIRMATION`, `roi=NEEDS_RESEARCHER_CONFIRMATION`, provisional `sample_run_id`/`PILOT-*` IDs, and a null top-level `binary_sha256`; `run_pilot.py` still reads the un-frozen v3.2.7 workbook (`ConfigFrozen=NO`). The campaign command does not pass `--preserve-sample-id`, so every newly generated manifest will reproduce these placeholders. This directly contradicts the "60/60 authoritative SampleRunID / ConfigFreeze YES" Ready-Gate rows. The 30 candidate contexts are also still labelled `APPROVAL_PENDING` in the delivered readiness CSV despite the recorded 2026-11-12 approval.
>
> These are **D-category (Excel/seed/control/binary/runner) tooling/provenance defects**, not measured-data defects; none invalidates a terminal, oracle, seed, ordinal, or binary SHA. They are fixable without re-running gem5 (manifest regeneration + CSV/label regeneration). The final re-audit should re-check F-01..F-04 below.

---

## 1. Gate-by-gate result (independent re-derivation)

| # | Launch gate | Result | Re-derived evidence |
|---|---|---|---|
| 1 | 12 models | **PASS** | `audit_v3_3_3/runs/` = 120 dirs; model counts `{A01:10, A03:10, DA04:10, FW02:10, FW05:10, LP01:10, LQ04:10, MD04:10, RP01:10, SP05:10, SQ01:10, SQ03:10}` |
| 2 | 60/60 authoritative SampleRunID + Seed | **PASS (workbook/CSV) / FAIL (run manifests)** | Workbook `Fault_Sample_Manifest`: 60 rows, 60 unique `SampleRunID`, 60 unique `Seed`, all IDs present in frozen `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv`, 0 seed mismatches; run summaries: 0 null seeds, 0 seed mismatches vs workbook. **But** 105/120 `audit_v3_3_3/runs/*/manifest.json` bind `sample_run_id` = pilot id (e.g. `A01-R01-control`) and `sub_task_id` = `PILOT-A01-S01` — 0/120 match the authoritative `A01-F0-W1-S01-R01` pattern (F-01). |
| 3 | 60/60 context mapping | **PASS** | `audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv`: 60 rows, 0 null seeds, all `EvidenceBinarySHA` = `1126e0fd…`, status `MAPPED` 30 / `MAPPED_ON_CANDIDATE_WORKLOAD` 30; `start+ceil(p·N)−1` recomputation = 0 failures (A01 585–713/N=129 → 597/623/649/675/701; A03 1040–1222/N=183 → 1058/1094/1131/1168/1204). |
| 4 | Workload approval | **PASS (evidence present) with stale label** | `audit_v3_3_3/decisions/LSU_v3.3.3_Researcher_Approval.md` records "全部采用" for the six candidate workloads + A01/A03 re-census + evidence labels; workbook `WorkloadIdentityStatus` = 30 `FORMAL` / 30 `OVERRIDE_APPROVED`; all 12 `ELF_SHA256` match on-disk bytes (12/12 MATCH). The delivered readiness CSV still says `CANDIDATE_PENDING_APPROVAL` (F-02). |
| 5 | 60/60 fault–control pairing | **PASS** | Recomputed 60 pairs from summaries: 0 seed mismatches, 0 ordinal mismatches, 0 workload mismatches, 0 binary-SHA mismatches. |
| 6 | 60/60 control zero proof, correct 3-way | **PASS** | 60/60 control `injection_count == 0`; `control_proof` = 35 `MOUNTED_BUT_DISABLED` / 25 `INJECTOR_ABSENT` / **0 `SUPPRESSED`**; 60/60 control `oracle == true`; `LSU_Fault_Control_Final_Audit.csv` matches (60 rows, `ControlInjected=0`×60, `ControlOracle=PASS`×60). |
| 7 | 60/60 application oracle | **PASS** | Summaries: fault terminals 43 `SDC` / 12 `MASKED` / 5 `HANG_WATCHDOG`; causal CSV `ApplicationOracle` 43 `FAIL` / 12 `PASS` / 5 `NO_CHECKSUM`; causal-vs-summary recomputation 0 mismatches; 12/12 MASKED rows carry a non-empty mechanism. |
| 8 | Binary provenance (source/binary/config) | **PASS** | live `sha256sum build/ARM/gem5.opt` = `1126e0fd…`; `audit_v3_3_3/binary/gem5.opt.v333-1126e0fd` same inode/hash; `sha256sum configs/se/lsu_proxy.py` = `8309da72…`; `git rev-parse b5031bf7` resolves; `git diff --stat b5031bf7 HEAD -- CHAOS/gem5/src` **empty**; `v333_build2.log`: `error:` count 0, `scons: done building targets` present; 120/120 summaries and 120/120 manifests carry `1126e0fd` + `8309da72`. |
| 9 | 120/120 manifests generable | **PASS (count) / FAIL (field fidelity)** | 120 `manifest.json` exist (120 `pilot_meta.json`, 120 `oracle.log`, 120 `command.txt`); `build/dry_run_final.log` = 120 `DRY-RUN` lines + "dry-run: 120 commands; no run dirs written". **But** 105/120 manifests are the stale `lsu-run-manifest-v3.2` schema with placeholder `warmup`/`roi`, provisional IDs, and null top-level `binary_sha256` (F-01). |
| 10 | Runner dry-run | **PASS** | `audit_v3_3_3/build/dry_run_final.log`: 120 commands, final line "dry-run: 120 commands; no run dirs written"; commands carry the correct final binary/config/workload/ordinal. |
| 11 | Output collision = 0 | **PASS** | `runs/lsu/formal_v333` does not exist (`ls` → "No such file or directory"); only `runs/lsu/guard/` exists; `tools/lsu_v332_matrix.py` holds `matrix_lock()` (`flock` on `audit_v3_3_2/controls/.lsu_v332_matrix.lock`) and separates RAW (`--out-csv`) from the curated FINAL CSV. |
| 12 | Resources (disk/mem/cpu/gem5 procs) | **PASS** | `/home` 51 G free (20 GiB floor met); 25 G RAM available of 29 G; 126 cores; 0 live `gem5.opt` processes; loadavg 1.01. |
| 13 | ConfigFreeze = YES | **PASS (declared) / FAIL (as consumed by runner)** | Workbook `Fault_Sample_Manifest` `ConfigFrozen=YES…`×60 and `Binary_Config` YES×12 with `ConfigSHA256=8309da72…`; **but** `run_pilot.py:48 EXCEL` points at `…-v3.2.7.xlsx`, where all 60 rows are `ConfigFrozen=NO`, `WarmUp=NEEDS_RESEARCHER_CONFIRMATION`, `ROI=NEEDS_RESEARCHER_CONFIRMATION` (F-01). The manifest fields are copied from that file (`manifest.py:126-127`). |

Additional independently verified positives: 60/60 `DistinctFromOtherContexts=YES`; causal rows have 0 blank critical cells; A03 5/5 `COMPLETE_PROP_TRACE`, RP01 5/5 `PARTIAL_WATCHDOG`; package zip SHA256 `168a13300c5ec85b8e125a9ca6f4ef126fb81088a948ca6a4d962c97a2a8cf23` matches its sidecar and `unzip -t` reports "No errors detected" (1,812 files); key packaged deliverables are byte-identical to the worktree copies (Acceptance Report, workbook, readiness, causal, fault-control, workload-oracle, ledger, provenance, independent acceptance).

---

## 2. Findings

### F-01 — HIGH (D: runner/manifest) — Formal-campaign manifests will carry provisional IDs and unfrozen placeholder fields

**Root cause (two code paths):**
1. `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py:48` sets
   `EXCEL = docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`.
   That source workbook has `WarmUp=NEEDS_RESEARCHER_CONFIRMATION` (60/60), `ROI=NEEDS_RESEARCHER_CONFIRMATION` (60/60), `ConfigFrozen=NO` (60/60). `manifest.py:126-127` copies these verbatim into `manifest["warmup"]` / `manifest["roi"]`.
2. `tools/lsu_v332_matrix.py:388-400 run_pilot_cmd()` builds the runner argv with `--pilot-id <outdir.name>` and **does not pass `--preserve-sample-id`**, so `run_pilot.py:758-765` keeps `sample["sample_run_id"] = args.pilot_id`, `run_id = PILOT-<model>`, `sub_task_id = PILOT-<model>-S01`.

**Raw evidence**
```
$ python3 (manifest scan over audit_v3_3_3/runs/*/manifest.json)
top-level binary_sha256:   {'None': 105, '1126e0fd1fea8e': 15}
nested gem5.binary_sha256: {'1126e0fd1fea8e': 105}
schema:                    {'lsu-run-manifest-v3.2': 105, 'None': 15}
warmup:                    {'NEEDS_RESEARCHER_CONFIRMATION': 105}
roi:                       {'NEEDS_RESEARCHER_CONFIRMATION': 105}
sample_run_id pattern:     106 distinct, 0 authoritative (examples: A01-R01-control, A01-R01-fault)
sub_task_id:               PILOT-A01-S01, PILOT-DA04-S01, ...
$ grep -n "preserve-sample-id" tools/lsu_v332_matrix.py   -> (no match)
$ grep -n "NEEDS\|WarmUp\|ROI" on 60_SAMPLE_MATRIX.csv -> WarmUp/ROI = NEEDS_RESEARCHER_CONFIRMATION (60/60), ConfigFrozen=NO (60/60)
```
The 15 direct-driver manifests (A03 faults + RP01) do carry `binary_sha256`/`config_sha256` but explicitly say `"no Excel SampleRunID is claimed here"` (`audit_v3_3_3/runs/A03-R01-fault/manifest.json`, note field).

**Affected:** all future formal-campaign manifests (120/120), and the packaged evidence manifests (105/120 stale schema). Does not affect the 60 measured terminals/oracles/seeds (summaries and workbook are correct).

**Proposed one-shot fix:** (a) point `run_pilot.EXCEL` at the frozen v3.3.3 workbook (or pass a frozen-config/ROI object into `build_manifest`); (b) add `--preserve-sample-id` to `run_pilot_cmd()` and to the direct-driver manifest writer so `sample_run_id/sub_task_id/run_id` bind the authoritative IDs; (c) fill top-level `binary_sha256`/`config_sha256` for both manifest schemas. Do **not** silently rewrite the v3.2.7 workbook.

**Validation:** regenerate the 120 manifests (or a dry manifest pass) and assert `warmup=0`, `roi` = measured `start–end/N`, `sample_run_id` ∈ `60_SAMPLE_MATRIX.csv`, `ConfigFrozen=YES`, top-level `binary_sha256=1126e0fd…`.

**Approval required:** N (tooling only). **Regression risk:** Low (manifest generation only; no injection semantics).

---

### F-02 — MEDIUM (D: readiness labels) — 30 delivered readiness rows still say `APPROVAL_PENDING` after the approval was recorded

`audit_v3_3_3/LSU_60Context_Final_Readiness.csv` (and the byte-identical `_Matrix.csv`, both SHA `d261b600…`) contains 30 rows with `WorkloadStatus=CANDIDATE_PENDING_APPROVAL` and `Ready=TECHNICALLY_READY_APPROVAL_PENDING` (FW02, SQ01, SQ03, SP05, MD04, RP01 × R01–R05), while `decisions/LSU_v3.3.3_Researcher_Approval.md` records "全部采用" on 2026-11-12 and the workbook says `OVERRIDE_APPROVED` for the same 30. The file mtime is 12:41, after the 08:59 approval, so it was regenerated without applying the approval status.

**Evidence:** `grep` of the CSV (rows 12–14 etc.); workbook `Fault_Sample_Manifest.WorkloadIdentityStatus` = `{FORMAL:30, OVERRIDE_APPROVED:30}`; `LSU_12Model_Workload_Oracle_Audit.csv` = `OVERRIDE_APPROVED` for the 6 candidate models.
**Fix:** regenerate the readiness CSV from the approval-aware workbook so the 30 candidate rows read `APPROVAL_RECORDED`/`OVERRIDE_APPROVED` and `TECHNICALLY_READY` (or keep a distinct "approved" label), or annotate the approval reference in the row.
**Validation:** 0 rows with `PENDING` in the delivered readiness CSV while the approval file exists.
**Approval required:** N. **Regression risk:** None (label only).

---

### F-03 — MEDIUM (D/provenance documentation) — The packaged "ground truth" is stale and contradicts the final artifacts

`README_GROUND_TRUTH.md` is included at the root of the zip (entry `README_GROUND_TRUTH.md`, 6,508 B) and states:
```
Git HEAD 3097ad82…; Source-equivalent fc608224…; Final binary 070d68a6…
B6: ConfigFrozen=NO; ROI/warm-up/binary approval pending.
A01/A03 ROI 1040–1234 (N=195)
```
The verified final state is HEAD `b5031bf7`, source-equivalent/working source `b5031bf7`, binary `1126e0fd`, `ConfigFrozen=YES`, A01 `585–713/N=129`, A03 `1040–1222/N=183`. A reader of the package will therefore see two contradictory baselines. (The file is dated 2026-11-11 and is explicitly a Phase-1 baseline, so this is a labelling/packaging defect, not a data defect.)
**Fix:** exclude it from the final package or retitle/annotate it `SUPERSEDED_BASELINE_2026-11-11` and add the final values. **Validation:** no packaged doc states `070d68a6`/`1040-1234` as final. **Approval:** N. **Risk:** Low.

---

### F-04 — LOW (D: package contents) — Acceptance report claims `runs_685d88f7/` is in the package; the zip contains only the RAW CSV

`LSU_v3.3.3_Final_Acceptance_Report.md:197` says the package includes "the pre-correction history (`runs_685d88f7/`)". The zip has **no** `runs_685d88f7/` entry; the only `685d` entry is `controls/LSU_Fault_Control_Pair_RAW_685d88f7.csv`. `LSU_v3.3.3_PACKAGE_README.md:39` correctly lists the 685d run dirs as *not* in the zip (retained locally). This is an internal contradiction between the two package documents.
**Fix:** correct the acceptance report sentence to match the PACKAGE README. **Validation:** `unzip -l … | grep -c runs_685d88f7` = 0 and both docs agree. **Approval:** N. **Risk:** None.

---

### F-05 — LOW (D: workbook hygiene) — `Workload_Oracle` has duplicate candidate rows and a reused `W7-v2` label

The sheet has 16 data rows: two byte-identical `W3-v2 sq_reload_v3212` rows and `W7-v2` used for both `replay_partial_v332` and `md04_violations_v332`. No value is wrong (all ELF/golden/control checksums are correct and match on-disk bytes), but the duplicate/ambiguous WorkloadID can break a consumer that keys on `WorkloadID`.
**Fix:** de-duplicate the W3-v2 row and give MD04 a distinct candidate ID. **Validation:** unique `WorkloadID` per candidate row. **Approval:** N. **Risk:** Low.

---

### F-06 — LOW (D: repo hygiene) — Duplicate/untracked audit artifacts at the audit root

`audit_v3_3_3/LSU_Fault_Control_Audit.csv` is untracked and byte-identical to the tracked `LSU_Fault_Control_Final_Audit.csv` (and to `controls/LSU_Fault_Control_Pair_FINAL.csv`); it is not in the package. `git status` also shows untracked `audit_v3_3_3/binary/`, `runs_685d88f7/`, `census/A01_8B/{stats,config.*}`, `gate_tests/`, `gate_tests_final/{DA04-p0,MD04-p0}`, `correction_smoke/`, and `.tmp_lsu_conc/` (99 contention-test dirs). The tracked key deliverables are all clean. These are packaging/cleanup items, not gate inputs.
**Fix:** delete the duplicate CSV (or symlink), and decide explicitly which raw evidence to track vs. keep zip-only; clear `.tmp_lsu_conc/`. **Approval:** N. **Risk:** None.

---

### F-07 — INFO — Residual wording in the acceptance report

`LSU_v3.3.3_Final_Acceptance_Report.md:145` still says "causal is 55+5, not 60 `COMPLETE`". The line is arithmetically correct as a count and the corrected literal breakdown appears at lines 53, 110, and 163; this is not a data defect. Optional rewording to "50 COMPLETE + 5 COMPLETE_PROP_TRACE + 5 PARTIAL_WATCHDOG".

---

## 3. Ledger / acceptance-claim cross-check

- Ledger (47 rows): 32 `CLOSED_V333`, 11 `VERIFIED_V333`, 3 `OPEN_NONBLOCKING` (L-A11 single exit code, L-D11 selftest-only validator, L-D15 null `injection_events`), 1 `SUPERSEDED_BY-L-A12`; 0 blocking — matches `LSU_v3.3.3_Ledger_Reconciliation.md`.
- **L-D16 ("authoritative SampleRunID binding") is overstated:** the workbook binds the IDs, but the persisted run manifests do not (F-01). The ledger row should be reopened or narrowed to "workbook-only binding".
- **L-D02/L-D13/L-D14** claims hold (0 null seeds/terminals; RP01 dispatch present; file lock present).
- The acceptance report's "one binary SHA in all 120" is true for **summaries** (120/120 `1126e0fd`) and for the nested `gem5.binary_sha256` in manifests, but **not** for the top-level manifest field (105 null) — see F-01.

---

## 4. Could not verify (explicitly)

- **Live gem5 behavior** of the 120-run campaign was not re-executed (mission forbids gem5/scons); the dry-run, summaries, traces, and logs were the evidence.
- **The 232 + 121 + 24 pytest results** were read from captured logs (`build/pytest_final2.log`, `platform_pytest_final.log`, `pytest_targeted_final.log`), not re-run.
- **The binary build** was not rebuilt; provenance is established by live SHA + empty `git diff b5031bf7 -- CHAOS/gem5/src` + the 0-error build log.
- **The zip's 3.37 GB tree** was integrity-tested (`unzip -t`, 1,812 files, "No errors detected") and key files SHA-compared, but not fully extracted.
- **Concurrent-session collision at launch time** cannot be known statically; the target directory does not exist today and the matrix holds an `flock`.
- **Whether the researcher's approval file is the sole authority** for the six candidate workloads is taken at face value from `decisions/LSU_v3.3.3_Researcher_Approval.md`.

---

## 5. Bottom line

The measured 120-run matrix is internally consistent and scientifically usable: 12 models × 5 contexts, one final binary `1126e0fd`, one config `8309da72`, source `b5031bf7`, 60/60 injections, 60/60 zero-injection controls with a correct 35/25/0 three-way proof, 43 SDC / 12 MASKED / 5 HANG_WATCHDOG, 12/12 MASKED mechanisms, 60/60 oracle-consistent causal rows, 60/60 ROI arithmetic, 60/60 unique authoritative IDs/seeds in the workbook, and all 12 workload ELF SHAs match on-disk bytes. The package SHA matches its sidecar and is intact.

The baseline launch verdict is **NO** solely because the runtime manifest/provenance path (F-01) would stamp every formal-campaign run with `NEEDS_RESEARCHER_CONFIRMATION` warm-up/ROI, provisional `PILOT-*` IDs, and the unfrozen v3.2.7 `ConfigFrozen=NO`; and because the delivered readiness CSV still labels 30 approved contexts `APPROVAL_PENDING` (F-02). Fixing F-01/F-02 (and the low-severity F-03/F-04 doc/package items) does not require gem5 reruns and should make the final re-audit an unconditional PASS.

**Report path:** `audit_launch_v333/reports/Agent_F_Independent_Preflight_Baseline.md`
