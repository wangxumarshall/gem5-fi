# Agent F — Independent Acceptance, LSU v3.3.2

- Date: 2026-11-11
- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
- Mode: read-only on sources/tests/workloads; no git add/commit/push; no gem5 process started (spot-check was not needed — artifacts are self-consistent and the raw traces/logs were sufficient).
- Verdict summary: **PARTIALLY_READY** (see bottom line).

Legend: PASS = verified against raw artifacts; FAIL = verified contradiction; PASS* = meets the stated requirement but with a provenance/labelling caveat listed under contradictions.

---

## 1. Binary provenance — PASS

Commands and real output:

```
$ git rev-parse HEAD
fc60822408cbb3f5af4788bd99fc82c114917367

$ sha256sum build/ARM/gem5.opt
070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca  build/ARM/gem5.opt

$ git diff --stat HEAD -- CHAOS/gem5/src
(empty)

$ grep -c "error:" /tmp/v332_build.log
0
$ grep -c "error:" /tmp/v332_build2.log
0
```

- HEAD matches the required `fc60822408cbb3f5af4788bd99fc82c114917367`.
- Binary SHA matches the required `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca`.
- Working tree has **no C++ diff** vs HEAD (`git diff --stat HEAD -- CHAOS/gem5/src` is empty).
- Both build logs contain zero `error:`. `/tmp/v332_build2.log` ends with `scons: done building targets.` and only the known non-fatal warnings (capstone/png/HDF5 absent).
- Every one of the 120 `summary.json` files also carries `binary_sha = 070d68…` (checked programmatically; zero mismatches).

Provenance caveat (not a C++ change): the working tree has `M tools/lsu_v332_matrix.py` (+11/−6) and untracked `tools/lsu_v332_report.py`. The uncommitted driver contains the actual ordinals, RP01 watchdog/timeout values and terminal-parsing used to produce these artifacts, so the artifact set is not byte-reproducible from HEAD alone.

---

## 2. 120 run artifacts — PASS*

Checks performed programmatically over `audit_v3_3_2/runs/*/summary.json`:

```
total dirs: 120
missing summary.json: none
FAULT_ZERO (fault injection_count <= 0): none
CONTROL_NONZERO (control injection_count != 0): none

per-model fault/control injection counts:
A01  fault [1,1,1,1,1]    control [0,0,0,0,0]
A03  fault [20000 x5]     control [0,0,0,0,0]   (capped per-application count; terminal HANG, exit 124)
DA04 fault [1,1,1,1,1]    control [0,0,0,0,0]
FW02 fault [1,1,1,1,1]    control [0,0,0,0,0]
FW05 fault [1,1,1,1,1]    control [0,0,0,0,0]
LP01 fault [1,1,1,1,1]    control [0,0,0,0,0]
LQ04 fault [1,1,1,1,1]    control [0,0,0,0,0]
MD04 fault [1,1,1,1,1]    control [0,0,0,0,0]
RP01 fault [1,1,1,1,1]    control [0,0,0,0,0]   (RP01_SKIP_REPLAY count = 1)
SP05 fault [1,1,1,1,1]    control [0,0,0,0,0]
SQ01 fault [1,1,1,1,1]    control [0,0,0,0,0]
SQ03 fault [1,1,1,1,1]    control [0,0,0,0,0]
```

Mount inspection (from `command.txt`, 60 controls):

- DA04, MD04, FW02, LQ04, RP01 controls: no injector mount at all (only `--chaos_propagation`), `--probability 0.0`.
- A01, A03, FW05, LP01, SP05, SQ01, SQ03 controls: injector mounted at `--probability 0.0` (`--chaos_addrpath` / `--chaos_lsqfwd` / `--chaos_l1dfwd`), as permitted.
- All fault runs have `--probability 1.0`.
- Zero injection events in every control trace: `grep -c '"injection_status": "INJECTED"' audit_v3_3_2/runs/*-control/trace_v31.jsonl` returned `0` for all 60 control traces.

Caveats (verified, not blocking):
- `summary.json.seed` is `null` for 110/120 runs; the real seeds are in `pilot_meta.json` (e.g. A01-R01 seed `2108120075`). No seed is missing from the raw evidence, but the summary schema is incomplete.
- `summary.json.terminal` is `null` for run_pilot-driven models; terminal classes are derived post hoc from the trace (present in the propagation/readiness tables).
- RP01 and A03 fault runs have no `trace_v31.jsonl`; their partial evidence is in `stdout.log` (RP01 eligible/skip/watchdog lines) and `addrpath_injections.log` + `prop_trace.csv.gz` (A03). This is consistent with their HANG classification.

---

## 3. Tables — FAIL on ROI ordinal arithmetic (4 candidate cells); other tables pass

### 3.1 ROI mapping (`audit_v3_3_2/roi/LSU_60Context_ROI_Percentile_Mapping.csv`)

60 rows; 12 models × 5 contexts; ROI_N == end−start+1 for all rows; no duplicate identity within a model; `MappingStatus` ∈ {MAPPED, MAPPED_ON_CANDIDATE_WORKLOAD}. **But the ordinal arithmetic does not match the stated `k = ceil(p*N)` rule uniformly:**

- 56/60 rows satisfy `Absolute_Eligible_Ordinal = ROI_Start_Ordinal + ceil(p*N) − 1`.
- **FW02 R02–R05 fail this rule** (4 candidate cells). Recorded absolute ordinals are `18, 30, 42, 54` = `ceil(p*N)` with the ROI start offset dropped; the correct values are `8+18−1=25`, `37`, `49`, `61`.
  - Verified against the independent census run: `FW02_w4v2_p30/command.txt` uses `--lsqfwd_event_ordinal 25`, while `runs/FW02-R02-fault/command.txt` uses `--lsqfwd_event_ordinal 18`. The matrix run therefore injected the wrong event for the claimed 30th percentile.
- `Rank_k` column is internally inconsistent in labelling: 29 rows record the 0-indexed offset (`floor(p*N)`, e.g. A01 R01 `k=19` for `ceil=20`) while the remaining rows record the 1-indexed rank (`ceil(p*N)`, e.g. FW05 R01 `k=200`). 31 rows have `Rank_k != ceil(p*N)`. The absolute ordinal is nevertheless correct for those 56 rows, because `start + floor(p*N) == start + ceil(p*N) − 1` when `p*N` is non-integer.
- A03 rows have a blank `Seed` even though the A03 run uses the frozen seed (e.g. `--addrpath_rng_seed 663646247` for R01, matching the frozen `60_SAMPLE_MATRIX.csv`).
- FW02 `pilot_meta.json` itself declares `"TEMPORARY_EVENT_SELECTION (Excel EventOrdinal; warm-up/ROI not frozen)"`.

### 3.2 Distinctness (`audit_v3_3_2/roi/LSU_60Context_Distinctness_Audit.csv`) — PASS

60 rows; every `Identity` is unique **within each model**. Five identities repeat across models, all of them the SQ01/SQ03 pair on the same `sq_reload_v3212` event (R01–R05) — different fault models on the same workload/event, which does not violate "no duplicate identity within a model".

### 3.3 Readiness matrix (`audit_v3_3_2/LSU_60Context_Final_Readiness_Matrix.csv`) — PASS

60 rows. `Ready`: 30 `TECHNICALLY_READY` + 30 `TECHNICALLY_READY_APPROVAL_PENDING`; `WorkloadStatus`: 30 `FORMAL` + 30 `CANDIDATE_PENDING_APPROVAL`; `ControlInjected`: 60×`0`. Cross-check against raw summaries: ordinals, fault injection>0, control injection==0, oracle and control-oracle all agree. A03/RP01 terminal strings are post-hoc analysis labels (see §4), not raw `summary.json` values.

### 3.4 Control pairs (`audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final.csv`) — PASS

60 rows = 60 unique (ModelID, ContextID) pairs; `ControlInjected` is `0` in all 60; `ControlZeroProof` is `INJECTOR_ABSENT` in all 60; `ControlExitCode` is `0` in all 60; `ControlOracle` is `PASS` in all 60. (Minor schema issue: the `ControlProof` column exists but is empty; the populated field is `ControlZeroProof`.)

### 3.5 Causal propagation (`audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv`) — PASS

60 rows; required terminal/oracle/evidence fields all populated. Terminal distribution: SDC 36, MASKED 12, HANG_TIMEOUT 5, HANG_WATCHDOG 5, SQUASHED 1, UNRESOLVED 1. EvidenceClass: DIRECT_DATAFLOW 48, HANG_PARTIAL 5, DIRECT_SKIP_AND_WATCHDOG 5, INDIRECT 2. TraceCompleteness: COMPLETE 50, PARTIAL 10 (the 5 A03 + 5 RP01).

---

## 4. Honesty checks — PASS

- **A03**: propagation table = `HANG_TIMEOUT` (5/5), `HANG_PARTIAL_EVIDENCE`, `PARTIAL`, reason `A03_LOG_CAPPED=True stream_rows≈113–115k`; raw summary `capped=true`, `injections=20000`, exit 124. Not MASKED. PASS.
- **RP01**: all five `stderr.log` contain the watchdog fatal, e.g.
  `src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:620: fatal: CHAOS_RP01_WATCHDOG_EXPIRED tick=7700000000 injected=1 eligible=26`
  ; propagation table = `HANG_WATCHDOG`, `DIRECT_SKIP_AND_WATCHDOG`, reason `eligible=26 skip=1 watchdog=True`. Not MASKED/SDC. PASS. (The literal is `CHAOS_RP01_WATCHDOG_EXPIRED`, not `CHAOS_RP01_WATCHDOG=EXPIRED`; semantics match. Raw `summary.json`/watchdog CSV say `terminal=CRASH` because gem5 exits via `fatal`; the HANG_WATCHDOG label is post hoc.)
- **A01-R03**: propagation = `UNRESOLVED`, reason `UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE`, `INDIRECT_EVIDENCE`. Direct trace inspection of `A01-R03-fault/trace_v31.jsonl`: 6707 events, event types include `injection`, `address_formed`, `memory_response`, `commit`, but **zero writeback-type events**; `terminal_state` is `UNRESOLVED` on all non-null occurrences. PASS.
- **SQ03**: terminal is `MASKED` in the matrix/propagation (never SDC); the work dossier explicitly states it is a **visibility-timing shift** (`CHAIN_VISIBILITY_MOVED`, 4/5) / `LIFECYCLE_ONLY` (1/5), "not a software-visible SDC". PASS.
- **SP05 `store_data_fnv`**: the injected store's `sp05_stage` record literally contains `store_data_fnv=null; data_correct=null; stage_outcome=RELOAD_UNVERIFIABLE`, and `LSU_SQ_Workload_Decision.md` documents the instrumentation gap and makes adoption conditional. PASS.

---

## 5. Frozen-design check — PASS (with documentation divergence)

```
$ git diff --stat 8f7a1354 -- docs/gem5-fi/lsu/implementation_v3_2/excel
(empty)
$ git diff 8f7a1354 -- docs/gem5-fi/lsu/implementation_v3_2/excel | head
(empty)
$ git merge-base --is-ancestor 8f7a1354 HEAD   -> YES
```

- No workbook edit since `8f7a1354`; no SampleRunID/Seed change inside the frozen workbook or `60_SAMPLE_MATRIX.csv`.
- Candidate names are absent from the frozen xlsx: `sq_forward_w4v2`, `replay_partial_v332`, `md04_violations_v332`, `sq_reload_v3212`, `CANDIDATE`, `w4v2`, `v332` each occur 0 times; candidate rows are labelled `CANDIDATE_PENDING_APPROVAL` only in the working audit tables.
- Divergence (documentation, not a frozen-workbook edit): the working ROI table renames `SampleRunID` to `V332-<model>-R<ctx>` (frozen `A01-F0-W1-S01-R01` → `V332-A01-R01`) and blanks the A03 seeds that the frozen matrix records.

---

## 6. Resource / provenance — PASS* with a stale provenance bundle

```
$ df -h /home/sdc
/dev/mapper/openeuler-home  354G  278G   58G  83% /home
```

- 58 GiB free ≥ the 20 GiB floor.
- Raw evidence exists under `audit_v3_3_2/`: `runs/` 7.7 GiB across 120 dirs, `roi/census_v332/` (123 dirs, incl. the percentile census), `sq_workload/evidence/`, `workloads/*.md`, `patches/`, `report/`.

Caveat: `audit_v3_3_2/binary/` contains only the **stale v3.3.1 binary** `gem5.opt.v331-d3807fbe` (no SHA sidecar, not the current 070d68… binary). `audit_v3_3_2/report/PROVENANCE.md` still records branch `lsu-v3.3.1-context-workload-20261111`, base commit `3504ec23…`, binary SHA `d3807fbe…` — i.e. the round-start baseline, not the final `fc608224…` / `070d68…`. **No file under `audit_v3_3_2/` cites `fc608224` at all** (`grep -rl fc608224 audit_v3_3_2` → 0 files); only the per-run `summary.json` binary SHA is current.

---

## Contradictions / findings list

1. **[blocking for FW02] ROI ordinal error in FW02 R02–R05.** Absolute ordinals `18/30/42/54` omit the ROI start offset; correct values `25/37/49/61`. Confirmed against the independent census p30 run, which uses ordinal 25. These are candidate cells (`CANDIDATE_PENDING_APPROVAL`), so the 30 formal-workload cells are unaffected.
2. **[documentation] `Rank_k` mixes 0-indexed offsets and 1-indexed ranks** (29 vs 31 rows); 31 rows have `Rank_k != ceil(p*N)` even though their absolute ordinals are correct. A03 `Seed` is blank in the ROI table although the run uses frozen seed values.
3. **[provenance] `PROVENANCE.md` is stale** (base 3504ec23 / d3807fbe / old branch) and `audit_v3_3_2/binary/` holds only the v3.3.1 binary; no artifact cites final HEAD `fc608224` or binary `070d68…`.
4. **[reproducibility] `tools/lsu_v332_matrix.py` is modified and `tools/lsu_v332_report.py` is untracked**; the exact driver that produced the runs is not committed.
5. **[labelling] SP05 is reported as `SDC` / `DIRECT_DATAFLOW_EVIDENCE` in the matrix**, while its own model record says `stage_outcome=RELOAD_UNVERIFIABLE` with `store_data_fnv=null`; the dossier flags this and keeps adoption conditional, but the matrix does not carry that qualifier.
6. **[labelling, benign] RP01 raw `summary.json` terminal = `CRASH`** (gem5 `fatal`) while the analysis tables say `HANG_WATCHDOG`; A03 raw = `HANG` vs table `HANG_TIMEOUT`. Both are explainable post-hoc remaps, but should be documented in the package.

---

## Bottom line: **PARTIALLY_READY**

Reasons:
- The 30 FORMAL-workload contexts (A01, A03, FW05, DA04, LP01, LQ04 × R01–R05) are technically ready and pass every data-integrity/honesty check: 30 fault runs with real injections, 30 injector-free control runs with zero injections, correct terminal classification (SDC/SQUASHED/UNRESOLVED/HANG), complete traces, and no frozen-workbook drift.
- The other 30 contexts (FW02, SQ01, SQ03, SP05, MD04, RP01) rest on candidate workloads explicitly marked `CANDIDATE_PENDING_APPROVAL` in every table; they cannot be called formal-ready without researcher approval. FW02 additionally carries a verified ordinal-mapping error in 4/5 cells.
- Provenance packaging is stale and the artifact-producing driver is uncommitted, so the round is not yet self-describing/reproducible.

Shortest blocking path:
1. Fix the FW02 R02–R05 ordinal formula (`start + ceil(p*N) − 1`), rerun those 4 cells, and correct the ROI table (also normalize the `Rank_k` convention and populate A03 seeds).
2. Update `audit_v3_3_2/report/PROVENANCE.md` to final HEAD `fc608224…` / binary `070d68…` and copy the current binary + SHA sidecar into `audit_v3_3_2/binary/`.
3. Commit `tools/lsu_v332_matrix.py` + `tools/lsu_v332_report.py` so the exact producing code is in history.
4. Obtain researcher approval for the 30 candidate contexts (or freeze the formal matrix to the 30 FORMAL cells now); resolve/qualify the SP05 `RELOAD_UNVERIFIABLE` vs `SDC` labelling before inclusion.

No check was rubber-stamped: checks 3 (ROI arithmetic) is a genuine FAIL for the FW02 candidate cells, and checks 2/5/6 carry verified caveats.
