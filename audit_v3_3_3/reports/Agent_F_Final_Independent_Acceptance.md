# Agent F — Final Independent Acceptance Audit (LSU v3.3.3)

**Auditor:** Agent F (fresh, independent; did not write any of the artifacts)
**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Mode:** read-only. No source/config/tool/test/data/Excel edit; no gem5 and no scons run. The only file written is this report.
**Method:** every number below was recomputed from raw artifacts (`audit_v3_3_3/runs/*/summary.json|command.txt|pilot_meta.json|manifest.json|trace_v31.jsonl`, the CSVs under `roi|controls|propagation`, the workbook via openpyxl, the pytest/build logs, the binary and the git tree). The main agent's `LSU_v3.3.3_Final_Acceptance_Report.md` was treated as a claim to be tested, not as evidence.

---

## 0. Executive summary

The **measured 120-run dataset is genuine and internally consistent**: 120 run dirs, one binary SHA `1126e0fd…`, 60 fault runs with `injection_count>0`, 60 controls with `injection_count==0` and a classified zero-proof (35 `MOUNTED_BUT_DISABLED` / 25 `INJECTOR_ABSENT`), ROI arithmetic exact, terminal distribution SDC 43 / MASKED 12 / HANG_WATCHDOG 5, and the required causal witnesses present for all 60 rows.

However, the **Ready package/provenance closure layer is not consistent with its own artifacts**, and several acceptance-report claims are contradicted by per-run metadata:

- the packaged `Config` SHA is the **pre-correction** config, not the one the final runs used;
- the "retained" pre-correction binary `gem5.opt.v333-685d88f7` is **the final binary** (same inode), i.e. the 685d binary is not actually preserved;
- the report's "Config Freeze = YES" is contradicted by 105/120 run manifests (`warmup`/`roi` = `NEEDS_RESEARCHER_CONFIRMATION`), by the workbook (`ConfigFrozen=NO` for 60 rows; `PENDING` in Binary_Config; `Final = NOT_STARTED` in the Readiness_Gate summary), and by the authoritative `Final_Readiness.csv`;
- "60/60 TraceCompleteness=COMPLETE" is contradicted by `LSU_60Context_Final_Readiness.csv`, which says **50 COMPLETE / 10 PARTIAL** (A03 faults + RP01 faults have no `trace_v31.jsonl`);
- the Master Defect Ledger is **40/47 OPEN + 1 OPEN_AWAITING_RESEARCHER + 6 VERIFIED_V333**, unreconciled with the final artifacts;
- the package is not assembled (no zip, no SHA sidecar) and 1 of the 14 required items is missing.

Verdict: **PARTIALLY_READY** (see §9). The data are usable for the formal experiment; the gate/provenance/Excel/package closure is not.

---

## 1. Ready-Gate table (per the ten required checks)

| # | Ready-Gate item | Result | One-line basis |
|---|---|---|---|
| 1 | Binary / provenance | **FAIL** | binary SHA, src-diff empty, 0 build errors, identical warning classes, 9/9 ELF SHAs all PASS; but packaged config SHA is stale and the 685d backup is not 685d. |
| 2 | Run set (120; 60/60 injection; 60/60 zero; proofs) | **PASS** | recomputed from 120 `summary.json`. |
| 3 | ROI arithmetic (60/60; A01 585–713/129; A03 1040–1222/183) | **PASS** | 0 arithmetic failures in the authoritative mapping and in every `command.txt`; A01/A03 windows/ordinals exact. |
| 4 | Context distinctness | **PASS** | 5/5 unique within every model; SQ01≡SQ03 cross-model shared workload (stated §4). |
| 5 | Causal chain (60 rows; witnesses; MASKED mechanism; COMPLETE not structural) | **PARTIAL** | all 60 have injection/activation/divergence/commit-squash-replay-hang/oracle; 12/12 MASKED have a mechanism; **but** the "60/60 COMPLETE" claim is false — 10 rows are PARTIAL in the authoritative readiness table. |
| 6 | Terminal honesty | **PASS** | A03=SDC/POST_ORACLE_SIM_HANG + checksum; RP01=HANG_WATCHDOG + internal watchdog + target ordinal; SP05 `store_data_fnv` non-null; no UNRESOLVED/TRACE_INCOMPLETE masquerade. |
| 7 | Fault-control pairing | **PASS** | same seed/ELF/config/ordinal; command diff is only the fault switch (p=1.0→0.0, or injector mount omitted). |
| 8 | Identity / Excel | **PARTIAL** | 8 sheets, 60 manifest rows, 60/60 authoritative SampleRunID/Seed, 0 blank critical fields, 30 `OVERRIDE_APPROVED` all PASS; but workbook internal contradictions (ConfigFrozen/gate summary/stale ROI fields). |
| 9 | Regression | **PASS** | captured 232 passed + 121 passed; dry-run 120 commands; build 0 errors; warning classes identical to v3.3.2. |
| 10 | Package readiness | **FAIL** | 12/14 items present; `LSU_Independent_Acceptance.md` missing; zip + SHA sidecar not built; 15 runs have no `trace_v31.jsonl`. |

---

## 2. Check 1 — binary / provenance

### 2.1 PASS sub-checks (real commands/output)

```text
$ sha256sum build/ARM/gem5.opt
1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338  build/ARM/gem5.opt

$ git cat-file -t b5031bf7 && git log --oneline b5031bf7..HEAD
commit
df7f86ed [LSU][V3.3.3][RESULTS] final 120-pair matrix, workbook and acceptance evidence

$ git diff --stat b5031bf7..HEAD -- CHAOS/gem5/src     # (empty)
$ git diff --stat HEAD -- CHAOS/gem5/src               # (empty)
```

`audit_v3_3_3/build/v333_build2.log`: `scons: done building targets.` (line 1157), `error:` count **0**. Warning-class comparison against `/tmp/v332_build2.log`:

```text
v332 warning classes: 4 | v333: 4
NEW in v333: (none)
GONE in v333: (none)
  classes: HDF5 missing / capstone missing / png missing / systemc architecture
```

All nine workload ELF SHAs recorded in `build/PROVENANCE.md` match the on-disk bytes (agu_addrmodes, fw05_forward, sq_reload_v3212, alignment, load_response, lq_lifetime_ordinal, sq_forward_w4v2, replay_partial_v332, md04_violations_v332 — 9/9 OK).

Note on HEAD: the live worktree HEAD is `df7f86ed`, one results commit *after* the source HEAD `b5031bf7`. That commit touches only results + `tools/lsu_v333_oracle_audit.py` + 3 test assertions + the plan doc; `git diff --stat b5031bf7..HEAD -- CHAOS/gem5/src` is empty, so the built source is `b5031bf7`. This is acceptable.

### 2.2 FAIL sub-checks

**(a) Packaged config SHA is the pre-correction config.**

`audit_v3_3_3/LSU_Final_Binary_Provenance.md:22` and `build/PROVENANCE.md:22` record:

```text
| Config | configs/se/lsu_proxy.py SHA256 7fd7e12ded42c319d6e33b14b9df4c0505b65cf9c89219e34bc1197fce3e2a72 |
```

Actual file at `b5031bf7`, at `HEAD`, and in the working tree:

```text
$ git show b5031bf7:configs/se/lsu_proxy.py | sha256sum
8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225  -
$ sha256sum configs/se/lsu_proxy.py
8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225  configs/se/lsu_proxy.py
```

The recorded `7fd7e12d…` is exactly the `gem5.config_script_sha256` in the **pre-correction** `runs_685d88f7/*/manifest.json`; the final 120 runs correctly record `8309da72…`:

```text
$ (recompute) FINAL runs manifest gem5.config_script_sha256 -> {8309da72…: 105, None: 15}
              runs_685d88f7 manifest config_script_sha256     -> {7fd7e12d…: 120}
```

=> The required deliverable `LSU_Final_Binary_Provenance.md` states the wrong config identity. The matrix artifacts themselves are correct; the packaged provenance is stale.

**(b) The "retained" pre-correction binary is the final binary.**

```text
$ sha256sum audit_v3_3_3/binary/gem5.opt.v333-1126e0fd \
            audit_v3_3_3/binary/gem5.opt.v333-685d88f7 \
            build/ARM/gem5.opt
1126e0fd…  audit_v3_3_3/binary/gem5.opt.v333-1126e0fd
1126e0fd…  audit_v3_3_3/binary/gem5.opt.v333-685d88f7
1126e0fd…  build/ARM/gem5.opt

$ stat -c '%i %h %n' build/ARM/gem5.opt audit_v3_3_3/binary/gem5.opt.v333-1126e0fd audit_v3_3_3/binary/gem5.opt.v333-685d88f7
7341432 4 build/ARM/gem5.opt
7341432 4 audit_v3_3_3/binary/gem5.opt.v333-1126e0fd
7341432 4 audit_v3_3_3/binary/gem5.opt.v333-685d88f7
```

All three names are the same inode (hardlink). `PROVENANCE.md` §6 ("the pre-correction `gem5.opt.v333-685d88f7` is retained as history") is therefore false: the rebuild wrote the binary **in place**, so the 685d byte image is gone. (`audit_v3_3_3/binary/SHA256.txt` also lists only the 1126e0fd file.) The archived `runs_685d88f7/` data are intact (120 summaries, all SHA `685d88f7…`) and are **not mixed** with the final runs, but they can no longer be reproduced from a preserved binary.

**(c) Mixed-binary row inside the "on this binary" verification table.**

`build/PROVENANCE.md:49` / `LSU_Final_Binary_Provenance.md:49` ("Pre-matrix verification **on this binary**") cite:

```text
A03-R01 fault | A03_WATCHDOG_EXPIRED at tick 400,963,640; ... activation ordinal 1059, first affected 1060; final checksum 32a11657db750fc1
```

but `audit_v3_3_3/controls/smoke_a03.csv` shows that row was produced by the **685d88f7** binary at the **old ordinal 1059**:

```text
A03,R01,fault,1059,…,checksum 32a11657db750fc1,…,binary_sha 685d88f77324d8ba…
```

The final archived run is `1126e0fd`, ordinal 1058, checksum `1cf7a5a9f11dab7e` (`A03-R01-fault/summary.json`, `oracle.log`). So the verification table mixes a pre-correction smoke value into a table titled as final-binary evidence.

---

## 3. Check 2 — run set

Recomputed from `audit_v3_3_3/runs/*/summary.json`:

```text
total dirs 120  fault 60  control 60
missing summary: 0
bad SHA: 0
fault injection<=0: 0
control injection!=0: 0
fault terminals: {'SDC': 43, 'MASKED': 12, 'HANG_WATCHDOG': 5}
control terminals: {'UNRESOLVED': 55, 'MASKED': 5}
control oracle not True: 0
control_proof counts: {'MOUNTED_BUT_DISABLED': 35, 'INJECTOR_ABSENT': 25}
proof inconsistencies (p!=0 for MOUNTED_BUT_DISABLED, mounts present for INJECTOR_ABSENT): 0
```

Per-model control proof: A01/A03/FW05/LP01/SP05/SQ01/SQ03 = 5 `MOUNTED_BUT_DISABLED`; DA04/FW02/LQ04/MD04/RP01 = 5 `INJECTOR_ABSENT`. Exactly the claimed 35/25 with 0 `SUPPRESSED`.

Zero-proof is a real artifact, not a label: e.g. `A01-R01-control/stdout.log` shows `CHAOS_LSU_TRIGGER … injected=0` and `CHAOS_L0_DECLINE … trigger_injected=0`; `oracle.log` = `expected=728e604ffcec539d got=728e604ffcec539d / ORACLE_PASS`. All 60 control `oracle.log` contain `ORACLE_PASS` (0 non-PASS).

**Result: PASS.**

---

## 4. Check 3 — ROI arithmetic

Authoritative source `audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv`; recomputed in Python for all 60 rows:

```text
ROI arithmetic failures: 0
  (N == end-start+1) and (k == ceil(p*N)) and (abs == start+k-1)
  AND summary.json ordinal == abs  AND summary.json seed == CSV Seed
command.txt ordinal mismatches (with correct per-model flag): 0
```

A01: `585–713`, N=129 → 597/623/649/675/701 (`585+ceil(0.1·129)−1=597`, …) — matches the brief exactly. A03: `1040–1222`, N=183 → 1058/1094/1131/1168/1204 — matches the brief exactly. `A01_8B/CENSUS.md` independently records 817 eligible 8-byte events, first main event 585, last 713, and the five ordinals; the A01 fault `pilot_meta.injection.eligible=817`.

`command.txt` spot-checks: A01 `--addrpath_event_ordinal 597`; A03 `--addrpath_event_ordinal 1058`; DA04 `--lsqfwd_event_ordinal 135`; MD04 `--md04_event_ordinal 3`; SP05 `--sp05_event_ordinal 952`; LP01 `--l1dfwd_event_ordinal 2549`; LQ04 `--lq04_event_ordinal 1`; RP01 `--rp01_event_ordinal 26`.

**Result: PASS** (arithmetic and executed ordinals). See finding F-05 for stale ROI *labels* elsewhere.

---

## 5. Check 4 — context distinctness

`roi/LSU_60Context_Distinctness_Audit.csv`, 60 rows, all `DistinctFromOtherContexts=YES`; recomputed per model: every model has 5/5 unique identity tuples. Example identities: A01 `seq=12909;pc=400578;…;lq=756`; RP01 skip-replay record with `load_seq=16293 … lq_gen=1283`; A03 activation `tick=15958635;bit=3`.

**Cross-model shared-workload fact (explicit):** SQ01 and SQ03 use the same workload `sq_reload_v3212` and the **same five dynamic stores** (`seq=13328;pc=40053c;addr=0x4919f0`, …, R05 `seq=20435`). Their 5 identities are byte-identical to each other. This is legitimate (different fault models on the same dynamic event) but the two models are **not globally distinct**; distinctness holds only within each model. (This is also recorded as ledger L-C09.)

**Result: PASS** (within-model 5/5), with the cross-model caveat stated.

---

## 6. Check 5 — causal chain

`LSU_60Context_Causal_Propagation.csv` (16 columns, 60 rows) recomputed against each raw `summary.json`:

```text
Terminal dist: {'SDC': 43, 'MASKED': 12, 'HANG_WATCHDOG': 5}
Oracle        : {'FAIL': 43, 'PASS': 12, 'NO_CHECKSUM': 5}
TraceCompleteness: {'COMPLETE': 60}      <-- claim in the CSV / workbook / report
```

All 60 rows carry injection, activation, first divergence, commit/squash/replay/hang and oracle/terminal. Concrete witnesses:

- **A01-R01**: `Injection seq=12909;pc=400578;…;lq=756`; `Activation a01_ea;ordinal=597`; `Downstream consumer_commit=394;first=consumer_commit@seq12911`; `Consumer consumer_commit;seq=12911`; `CommitSquashReplay commit;commit_seq=6169`; `Terminal SDC / ORACLE_FAIL`. Raw `summary.json` chain: `injection,address_formed,memory_request,memory_response,register_writeback,consumer_commit,errant_commit`, `missing_stages: []`, `chain_integrity: PASS`.
- **MASKED 12/12 have a mechanism** (no blank): FW02-R03 `SUPPRESSED_FORWARD_NORMAL_VALUE`; SQ03-R01/R03/R04/R05 `VISIBILITY_TIMING_SHIFT:DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`; SQ03-R02 `VISIBILITY_TIMING_SHIFT:LIFECYCLE_ONLY` (the 4/5 + 1/5 split); MD04-R01 `INERT_AFTER_COMPLETION;no_wrong_value_produced`; LQ04-R01..R05 `ENTRY_INVALIDATED_RESTORED;data_unchanged=1;no_pop=1;no_reuse=1`.
- **RP01-R01..R05**: `HANG_WATCHDOG / INTERNAL_WATCHDOG_DEADLINE`; target ordinal present (26/77/128/179/230); `CommitSquashReplay watchdog_expired; src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:627: fatal: CHAOS_RP01_WATCHDOG_EXPIRED tick=7700000000 injected=1 eligible=26`; `summary.rp01.watchdog=true, deadline_cycles=20000000, no_checksum=true`.
- **SQ03-R02** is the lifecycle-only 1/5: `effect_outcome=LIFECYCLE_ONLY;no_downstream_effect;not_sdc`, oracle PASS.
- **A01-R03** (brief's specific demand): `addrpath_injections.log` has `register_writeback` chain and the trace contains **1** `register_writeback` record and **0** `a01_ea_discarded` records; `pilot_meta.target_event_proof={site: lsq_pushRequest_PRE, events: 1, all_load_bit3: True}`. `CHAOS_L0_DECLINE … pre_retry_skipped=22`.

**Problem with the "COMPLETE" label (part of this gate).** The authoritative `LSU_60Context_Final_Readiness.csv` reports:

```text
Trace: {'COMPLETE': 50, 'PARTIAL': 10}
PARTIAL rows: A03-R01..R05, RP01-R01..R05
```

and the `propagation/LSU_60Context_Causal_Propagation_Final.csv` also marks those 10 `PARTIAL`. The reason is verifiable: these 15 run dirs (A03 faults + RP01 fault & control) have **no `trace_v31.jsonl`**:

```text
trace_v31.jsonl missing in 15 runs: A03-R01..R05-fault, RP01-R01..R05-{fault,control}
A03-R01-fault/pilot_meta.json: "trace": null
RP01-R01-fault/pilot_meta.json: "trace": null
```

The top-level CSV, the workbook `Causal_Propagation` sheet, and the acceptance report all say `COMPLETE` 60/60. That promotion is not backed by the v31 trace validator for 10 rows (A03/RP01 are terminal-witness evidence — legitimate for those models, but not "COMPLETE" by the v31 criterion). The acceptance report's "Causal rows 60/60, TraceCompleteness=COMPLETE" is therefore **overstated**; the honest value is **50 COMPLETE / 10 PARTIAL**.

**Result: PARTIAL** — witnesses PASS, the 60/60 COMPLETE claim FAIL.

---

## 7. Check 6 — terminal honesty

| Model | Expected | Observed (raw) | Verdict |
|---|---|---|---|
| A03 5/5 | SDC + POST_ORACLE_SIM_HANG + checksum | `summary.terminal=SDC`, `terminal_qualifier=POST_ORACLE_SIM_HANG`, `terminal_reason=ORACLE_FAIL`, `checksum` present (R01=`1cf7a5a9f11dab7e` ≠ golden `728e604ffcec539d`), `exit_code=1`, `timed_out=false`, `a03.watchdog_expired=true`, lifecycle emitted, `gzip -t prop_trace.csv.gz` OK | PASS |
| RP01 5/5 | HANG_WATCHDOG, internal watchdog, target ordinal | `terminal=HANG_WATCHDOG`, `terminal_reason=INTERNAL_WATCHDOG_DEADLINE`, `watchdog=true`, `deadline_cycles=20000000`, `no_checksum=true`, target ordinal recorded, fatal line at `CHAOSLSQFwd.cc:627` | PASS |
| SP05 | `store_data_fnv` non-null | `store_data_fnv=b6180e0c195fd2e9`, `store_data_hex=6d7b78717e6b7d7f`, `store_data_len=8`, `stage_outcome=CHAIN_VISIBILITY_LOST`, `sp05_write_skipped` node | PASS |
| A01-R02 | (brief says SQUASHED/UNRELATED_SQUASH_NO_ARCH_ENTRY) | final run is **SDC** (`ORACLE_FAIL;committed_data_value_diverged`) with `register_writeback` + `errant_commit`; see F-11 — the brief's SQUASHED expectation is superseded by the approved A01 8-byte scope correction (L-A12) | internally consistent; brief stale |
| no masquerade | no UNRESOLVED / TRACE_INCOMPLETE terminal | 0 rows with `UNRESOLVED`/`TRACE_INCOMPLETE` as fault terminal | PASS |

**Result: PASS.** A03's exit path prints a Python `NotImplementedError: Exit event 'CHAOS_A03_WATCHDOG_EXPIRED' not implemented` traceback on stderr and returns `exit_code=1`; the watchdog still fires after the oracle and the checksum is captured, so the terminal is honest, but "terminates cleanly" is imprecise (F-09).

---

## 8. Checks 7–10

### 7. Fault-control pairing — **PASS**

Recomputed token-level `command.txt` diff for all 60 pairs. The only differences are the fault switch:

- `MOUNTED_BUT_DISABLED` (35): only `--probability 1.0 → 0.0` (A03 controls additionally drop `--addrpath_watchdog_cycles`, which is part of the fault harness, not the workload);
- `INJECTOR_ABSENT` (25): the model mount and its model-specific flags are **omitted** from the control (e.g. `--chaos_lsqfwd --lsq_struct_mode … --lsqfwd_event_ordinal …` for DA04/FW02), plus `--probability 0.0`.

`summary.json` pairing: 0 seed mismatches, 0 workload mismatches, 0 ordinal mismatches across 60 pairs. Expected goldens hold: e.g. RP01 control `f3b1c554273d23f7`, MD04 control `0x22be5ae3364d0c9f`, DA04 control `0x3f89eab79392ce69`.

Gate-test re-evidence (`gate_tests_final/`): `MD04-p0.stdout` shows `[lsu_proxy] CHAOSMD04 probability=0.0 (global=0.0, override=None)` and `checksum=0x22be5ae3364d0c9f`; `DA04-p0.stdout` shows `injected=0` and `checksum=0x3f89eab79392ce69`. Consistent with the 35/25 matrix classification.

### 8. Identity / Excel — **PARTIAL**

Present and correct:

```text
sheets: ['Model_Design','Fault_Sample_Manifest','Control_Manifest','ROI_Context_Mapping',
         'Causal_Propagation','Workload_Oracle','Binary_Config','Readiness_Gate']  (8)
Fault_Sample_Manifest data rows: 60
SampleRunID not in frozen 60_SAMPLE_MATRIX.csv: 0
Seed mismatches vs frozen: 0
blank critical fields (SampleRunID/Seed/binary SHA/ELF SHA/Oracle/ROI_Start/ROI_N/
  EligibleEventOrdinal/TerminalState/TraceCompleteness/ExecutionStatus): 0
WorkloadIdentityStatus x DecisionStatus: FORMAL 30 / OVERRIDE_APPROVED 30
Control_Manifest: ControlInjected 0/60, ControlOracle PASS 60, zero proof 35/25
Readiness_Gate per-row ReadyGate: PASS 60
```

Contradictions inside the same workbook (F-03, F-05):

```text
Fault_Sample_Manifest ConfigFrozen: {'NO': 60}
Binary_Config ConfigFrozen: 'PENDING (freeze after Task-7 binary validation)' (×12), field block 'PENDING'
Readiness_Gate bottom gate summary: FaultInjected/ControlClean/TerminalEvidence/TraceComplete/Provenance = PENDING; Final = NOT_STARTED
Fault_Sample_Manifest ROI_Start/ROI_N for A01 & A03: 1040 / 195 (old design window) while EligibleEventOrdinal is 597/…/1058 (corrected)
Causal_Propagation ROI string A01-R01: 'ROI=1040-1234;N=195;p=0.10;ordinal=597'
```

`ROI_Context_Mapping` is correct (A01 585/129, A03 1040/183). So the workbook has the right ROI in one sheet and the stale ROI in two others, and its own gate summary says `NOT_STARTED`.

Also: `LSU_60Context_Final_Readiness.csv` marks the 30 candidate contexts `TECHNICALLY_READY_APPROVAL_PENDING` and their workbook `DecisionStatus` is `NEEDS_USER_DECISION`, even though the researcher approval record (`decisions/LSU_v3.3.3_Researcher_Approval.md`, decision #1) says all six candidates were **adopted**. `WorkloadIdentityStatus=OVERRIDE_APPROVED` (30) is present, so the brief's specific "30 candidate contexts carry OVERRIDE_APPROVED" is satisfied; the approval *status* columns are stale (F-08).

**Result: PARTIAL** — the enumerated identity criteria pass; internal workbook consistency does not.

### 9. Regression — **PASS**

```text
audit_v3_3_3/build/pytest_final.log:           232 passed in 142.68s
audit_v3_3_3/build/platform_pytest_final.log:  121 passed in 4.67s
audit_v3_3_3/build/dry_run_final.log:          "dry-run: 120 commands; no run dirs written" (grep count = 120)
build logs:                                    0 "error:"; warning classes identical to /tmp/v332_build2.log
```

The two updated-tests check: the commits after `b5031bf7` update only three assertions (A03 watchdog `1e9→1e6`, report out-dir `audit_v3_3_2→audit_v3_3_3`, gem5 SHA `070d…→1126…`) — all justified by the final binary. The brief's named tests exist and are included in the 232: `tests/test_lsu_v333_control.py:270 test_a01_ea_discarded_is_injection_not_activated`, `tests/test_lsu_12model_closure.py:1666 test_a01_discard_context_grades_injection_not_activated`, `tests/test_lsu_v333_control.py:320 test_planned_rp01_and_a03_commands` (RP01 is in `MODELS` in both `tools/lsu_v332_report.py:35` and `tools/lsu_v333_propagation.py:48`).

Caveat: `pytest_final.log` is a 4-line summary (not a verbose capture); it is consistent with 232 passed but is prose-level, not a full transcript (ledger L-D12).

### 10. Package readiness — **FAIL**

The 14 items from `docs/superpowers/plans/2026-11-12-lsu-v333-final-closure.md` ("Task 9 / Step 4"):

| # | Item | Status |
|---|---|---|
| 1 | Final_Acceptance_Report | present |
| 2 | Master_Defect_Ledger | present (but stale — F-07) |
| 3 | Consolidated_Repair_Plan | present |
| 4 | Researcher_Decision_Packet (+ decisions/) | present |
| 5 | workbook | present |
| 6 | 60Context_Final_Readiness | present (50/10 trace split) |
| 7 | Causal_Propagation | present |
| 8 | Fault_Control_Final_Audit | present (byte-identical to controls/FINAL) |
| 9 | Workload_Oracle_Audit | present |
| 10 | Final_Binary_Provenance | present (wrong config SHA — F-01) |
| 11 | Final_Source_Diff.patch | present (26 files, includes configs/se/lsu_proxy.py) |
| 12 | Independent_Acceptance | **MISSING** (`audit_v3_3_3/LSU_Independent_Acceptance.md` absent; this report is under `reports/`) |
| 13 | raw pilot traces/logs/oracles/tests | present, **but 15 runs have no `trace_v31.jsonl`** |
| 14 | exact commands and runner config | present (`RUNBOOK.md`, per-run `command.txt`/`pilot_meta.json`) |

Also missing for assembly: the zip `LSU_v3.3.3_Formal_Experiment_Ready_Package.zip` and its `.sha256` sidecar (prompt states the zip is not built yet; I confirm neither exists in the worktree root).

---

## 9. Findings (severity + evidence)

**F-01 — HIGH — packaged config SHA is the pre-correction config.**
`audit_v3_3_3/LSU_Final_Binary_Provenance.md:22`, `audit_v3_3_3/build/PROVENANCE.md:22` record `7fd7e12d…`; actual `configs/se/lsu_proxy.py` at `b5031bf7`/`HEAD`/worktree = `8309da72…`; final-run manifests record `8309da72…`; `7fd7e12d…` belongs to `runs_685d88f7/*/manifest.json`. Fix: update both provenance files to `8309da72…`.

**F-02 — HIGH — the "retained" pre-correction binary is the final binary.**
`audit_v3_3_3/binary/gem5.opt.v333-685d88f7` = inode 7341432 (same as `build/ARM/gem5.opt`) = SHA `1126e0fd…`, not `685d88f7…`. `PROVENANCE.md:62` claim is false. The `runs_685d88f7/` archive (120 runs, all `685d88f7…`) is intact and not mixed, but is no longer reproducible from a preserved binary. Fix: re-materialize the true 685d88f7 binary from a build log/backup, or relabel the archive as "binary not preserved".

**F-03 — HIGH — "Config Freeze = YES" is unsupported by every per-run artifact.**
105/120 `manifest.json` have `warmup = roi = NEEDS_RESEARCHER_CONFIRMATION` (15 A03/RP01 manifests have `None`); 120 `pilot_meta.json` either say `TEMPORARY_EVENT_SELECTION (Excel EventOrdinal; warm-up/ROI not frozen)` (105) or omit the field (15). Workbook `Fault_Sample_Manifest.ConfigFrozen = NO ×60`; `Binary_Config.ConfigFrozen = PENDING`; `Readiness_Gate` summary `Final = NOT_STARTED`. The acceptance report's Ready-Gate row "Config Freeze | YES" has no supporting artifact. Fix: regenerate manifests/workbook after the freeze decision is recorded, or change the report to state the freeze is "definition approved, artifact not yet frozen".

**F-04 — MEDIUM — trace-completeness overstatement (60/60 COMPLETE).**
`LSU_60Context_Final_Readiness.csv` and `propagation/…_Final.csv` say 50 COMPLETE / 10 PARTIAL; the top-level CSV, workbook `Causal_Propagation`, and the report say 60 COMPLETE. Root cause: A03 faults + RP01 fault/control (15 dirs) have no `trace_v31.jsonl`; `pilot_meta.trace = null`. Fix: report 50/10 (or distinguish "v31-validated" vs "terminal-witness").

**F-05 — MEDIUM — stale ROI fields in two workbook sheets.**
`Fault_Sample_Manifest.ROI_Start/ROI_N` = 1040/195 for A01 and A03; `Causal_Propagation` ROI string = `1040-1234;N=195` for both. The approved values are A01 `585/129` and A03 `1040/183` (`ROI_Context_Mapping` is correct). The `ROI` text column simultaneously says "measured main-loop eligible window on the final binary", which is false for these 20 rows. Fix: propagate the corrected window into the manifest/causal sheets.

**F-06 — MEDIUM — mixed-binary evidence in the "on this binary" verification table.**
`PROVENANCE.md:49` / `LSU_Final_Binary_Provenance.md:49` cite the A03-R01 smoke from the **685d88f7** binary at ordinal 1059 (`controls/smoke_a03.csv`), not the final 1126e0fd run (ordinal 1058, checksum `1cf7a5a9f11dab7e`). The other rows (A01-R01, SP05-R01) do match the final runs. Fix: re-run the A03 smoke on 1126e0fd or label the row "pre-correction smoke".

**F-07 — MEDIUM — Master Defect Ledger not reconciled.**
`LSU_v3.3.3_Master_Defect_Ledger.csv` `FinalStatus`: `OPEN ×40`, `OPEN_AWAITING_RESEARCHER ×1` (L-A12), `VERIFIED_V333 ×6`. Several OPEN rows are demonstrably fixed in the final artifacts (L-D01: final controls are 35 mounted-p0 / 25 absent, not "INJECTOR_ABSENT for 35"; L-D02: final summaries carry seeds), while others remain true (L-C01: A03 has no `trace_v31.jsonl`; L-A07; L-A08 label now superseded). The acceptance report does not mention 40 OPEN rows. Fix: re-status each ledger row against the final evidence.

**F-08 — LOW — approval-status columns stale.**
30 candidate contexts are `WorkloadIdentityStatus=OVERRIDE_APPROVED` (correct) but `DecisionStatus=NEEDS_USER_DECISION` / `TECHNICALLY_READY_APPROVAL_PENDING`, while `decisions/LSU_v3.3.3_Researcher_Approval.md` adopts all six candidates. Fix: regenerate readiness/DecisionStatus.

**F-09 — LOW — A03 exit path raises an unhandled exit event.**
`A03-R01-fault/stderr.log`: `NotImplementedError: Exit event 'CHAOS_A03_WATCHDOG_EXPIRED' not implemented` (Python traceback, `exit_code=1`). The watchdog terminal and checksum are genuine; "terminates cleanly" should be softened or the exit event registered.

**F-10 — LOW — A03 ROI window has no standalone census artifact.**
The A01 correction ships `census/A01_8B/CENSUS.md` + logs; A03's `1040–1222/N=183` is asserted only in the CSV/PROVENANCE (the fault run's funnel is `eligible=52367`, the persistent F5 stream). Arithmetic is correct, but N=183 cannot be independently re-derived from an archived count-only run. Fix: archive the A03 count-only re-census alongside `A01_8B`.

**F-11 — INFO — brief expectation superseded (no artifact defect).**
The brief expects A01-R02 = SQUASHED/UNRELATED_SQUASH_NO_ARCH_ENTRY. After the approved L-A12 8-byte scope change, A01-R02's executed ordinal moved 1098→623 and the final run is a genuine **SDC** with `register_writeback` + `errant_commit` and oracle FAIL. The final data are internally consistent; ledger L-A08 (SQUASHED) is stale. A01-R03 meets the brief exactly (`register_writeback=1`, `a01_ea_discarded=0`).

**F-12 — INFO — SQ01/SQ03 cross-model non-distinctness.**
Both models use `sq_reload_v3212` and the identical five dynamic stores; distinctness holds only within a model. Ledger L-C09 records this. Legitimate for different fault models; should be stated whenever "60 distinct contexts" is claimed.

**F-13 — INFO — two labels for RP01 oracle.**
`RP01-*-fault/oracle.log` = `ORACLE_FAIL: no checksum line`; the summary has `oracle=false, no_checksum=true`; the CSV says `NO_CHECKSUM`. The `NO_CHECKSUM` label is the honest reading; note the raw log says FAIL.

**F-14 — INFO — 15 runs bypass run_pilot.**
A03 faults + all RP01 fault/control have `manifest.json` without the `gem5` block (binary/config SHA null) and no `pilot_meta.excel_identity`; the binary SHA is still present in `summary.json`. Evidence is complete via `summary.json`/prop logs, but not through the same manifest schema as the other 105.

---

## 10. Things I could not verify (n ≤ 1)

- Build log ↔ binary byte lineage: I confirm `v333_build2.log` ends `scons: done building targets.`, 0 errors, and the runs report `gem5 compiled Nov 12 2026 10:45:35`; I did not rebuild.
- `pytest` full transcript: only the 4-line summary is captured; the 232 pass count is quoted from it.
- A03 N=183 re-census: no standalone artifact (F-10).
- The true `685d88f7` binary: not preserved in the worktree (F-02).

---

## 11. Final verdict

**`PARTIALLY_READY`**

Rationale, stated honestly:

- The **experiment itself is sound**: 120 runs, one binary (`1126e0fd…`), 60 fault injections > 0, 60 controls == 0 with real zero-proof, exact ROI arithmetic, correct executed ordinals, valid fault/control pairing, and honest terminals (A03 checksum + post-oracle hang, RP01 internal watchdog + target ordinal, SP05 store-data hash non-null). No fabricated run and no mixed-binary run was found in `runs/`.
- The **Ready Gate cannot be signed as "READY_FOR_FORMAL_EXPERIMENT"** because four gate items are contradicted by the package's own evidence: the packaged config SHA is wrong (F-01), the pre-correction binary backup is not what it claims (F-02), "Config Freeze = YES" is contradicted by 105/120 manifests and the workbook's own `NOT_STARTED` gate summary (F-03), the "60/60 COMPLETE" trace claim is overstated (F-04), the ledger is 40 OPEN (F-07), and the package is not assembled and is missing item 12 (Check 10).

Concretely, to reach `READY_FOR_FORMAL_EXPERIMENT` the owners should (one patch/unit each): fix the provenance config SHA and the 685d archive claim; regenerate manifests/workbook with the approved warm-up/ROI/ConfigFrozen state and the corrected A01/A03 ROI fields; set the reported trace completeness to 50 COMPLETE / 10 terminal-witness PARTIAL; re-status the defect ledger; reconcile the 30-candidate approval status; and assemble the package with item 12 (this report) + zip + SHA sidecar.
