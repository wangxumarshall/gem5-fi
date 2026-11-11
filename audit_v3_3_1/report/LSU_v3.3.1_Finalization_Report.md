# LSU v3.3.1 — Context & Workload Finalization Report

**Date:** 2026-11-11
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111` (base `8f7a1354`)
**Binary:** `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`
**Scope:** 12 models × R01–R05 = 60 contexts. No formal campaign was launched.
**Final status:** **`PARTIALLY_READY`** — `12_MODEL_FORMAL_READY = NO`.

---

## 1. What this round did

1. Re-audited every v3.3.0 claim against files in this worktree (Agents B, C, D, E).
2. Implemented the approved Decision A method as a real census tool:
   `tools/lsu_v331_census.py` runs one `platform/run_pilot.py` probe per eligible
   ordinal with the model's own selector, then records `dyn_inst_seq` / PC /
   address / entry identity. Probes are census artifacts; oracles are ignored.
3. Measured the ROI ordinal window and N_ROI for each model that the current
   hooks can expose, then ran the five percentile probes `k(p)=ceil(p·N)`.
4. Produced the 60-row mapping and distinctness tables, the causal re-audit,
   the control-readiness table, and the three SQ workload comparisons.

Raw census: `audit_v3_3_1/roi/census/*.jsonl` (18 files, 175 probes; 15 probes
timed out after activation by design and kept their partial records).

---

## 2. Answers to the 11 required questions

### Q1. Can all 60 dynamic contexts be mapped into a valid ROI?

**No. 40/60 are mapped; 20/60 are not.**

| Mapping status | n | Models |
|---|---:|---|
| MAPPED (observed) | 20 | A01×5, FW05×5, DA04×5, LQ04×5 |
| MAPPED_WITH_SEMANTIC_CAVEAT | 5 | A03×5 |
| MAPPED_ON_RECOMMENDED_WORKLOAD | 15 | SQ01×5, SQ03×5, SP05×5 (on `sq_reload_v3212`, approval pending) |
| INSUFFICIENT_EVENTS | 15 | FW02×5, MD04×5, RP01×5 |
| OBSERVABILITY_GAP | 5 | LP01×5 |

### Q2. Do the five percentiles form five real, meaningful contexts?

- **A01** ROI = eligible ordinals **1040–1234**, N_ROI=195. The five events are
  seq 12978 / 13638 / 14049 / 14719 / 15086 at PCs 0x400598, 0x40068c,
  0x4006a8, 0x4006d0, 0x4006d0. R04/R05 share a static PC but differ in dynamic
  instance and address (0x493230 vs 0x493368).
- **FW05** ROI = **1–2000**, N_ROI=2000. Five seq 16084 / 23684 / 31284 / 38884 /
  46484 at the same load PC 0x400564, with distinct dynamic iterations and
  forwarding entry generations. R01 and R05 happen to reuse the same buffer
  address (0x4919c8), so they are distinct by sequence/iteration, not address.
- **DA04** ROI = **33–1056**, N_ROI=1024. Five distinct store addresses
  (0x491b29 … 0x4927f5).
- **LQ04** ROI = the five `_start` anchor loads, N_ROI=5; ranks 1..5 map to
  seq 3..7, PCs 0x400338..0x400348, lq_idx 1..5. It is the minimum sufficient N.
- **SQ01/SQ03/SP05** on `sq_reload_v3212`: N_ROI=128 (the loop's 128 stores);
  ranks 13/39/64/90/116 map to store seq 13328 / 15122 / 16847 / 18641 / 20435
  and five distinct buffer addresses 0x4919f0 … 0x491d28.

A01/A03 share the same eligible stream (verified: A03 ordinal 1059 activation
seq 12978 = A01 ordinal 1059 seq 12978). Event identity is **seed-independent**:
A01 K=1059 with the R02 seed and FW05 K=200 with the R02 seed reproduce the
exact seq/PC/address of the R01 seed.

### Q3. Which contexts still land in libc or initialization code?

- **Old EventOrdinal 1–5** (the v3.3.0 configuration) for A01/A03 are **all**
  outside the ROI: ordinal 2 is `seq=48 PC=0x400ad0` (libc); the ROI starts at
  ordinal 1040.
- DA04 old ordinals 1–3 are libc; the ROI starts at ordinal 33.
- MD04 old ordinals 1, 2, 4, 5 are libc/helper; only ordinal 3 is in `main`.
- SQ01/SQ03/SP05 literal ordinals 1–5 are C-runtime startup stores.
- FW02 (all), RP01 (all), LP01 (unresolved) remain outside any proven ROI.
- FW05 is the exception: its whole eligible stream (1–2000) is in `main`, so
  old ordinals 1–5 were already in-ROI.
- LQ04 old ordinals 1–5 are the designed `_start` anchors (in-ROI by design).

### Q4. Which models have too few eligible events?

- **FW02**: N_ROI = 0. The frozen W4 `sq_forward` `main` has no data load at
  all (GCC -O2 folded every store→load pair).
- **MD04**: N_ROI = 1 (only ordinal 3, PC 0x400530, addr 0x491990). Five
  percentiles collapse.
- **RP01**: N_ROI = 0. W7 has only a full 8B store→8B load pair; the designed
  partial-overlap event does not exist in the workload.
- **LP01**: N_ROI unmeasurable with the current hook (see Q5).
- **LQ04**: N_ROI = 5, exactly the minimum; any stricter eligibility rule would
  make the five percentiles impossible.

### Q5. Which target instructions or microarchitectural states do not match the design?

1. **FW02/W4**: the designed forwarding pair does not execute in `main`.
2. **RP01/W7**: the designed partial-overlap store→load does not exist.
3. **MD04/W7**: only one in-`main` violation report is eligible.
4. **A03**: `A03_STREAM` logs `pc=0` for every row; the PC cannot be audited
   natively, and **3/5 percentile activations are `ALREADY_STUCK`
   (affected=0)** — the 10/50/70 % events have bit3=0, so no fault is applied
   at activation (F5 may still affect later loads).
5. **LP01**: the L1DForward record exposes only a physical address (`addr=…`)
   and no PC or virtual address; the eligible stream cannot be separated into
   the designed loop with the existing observation hook.
6. **SQ family**: the formal W3/W6 rows and the v3.2.12 closure evidence use
   different workloads (`sq_drain`/`store_path` vs `sq_reload_v3212`).

### Q6. Which propagation chains lack a first-divergence, consumer, or terminal edge?

From `LSU_60Context_Causal_Chain_Reaudit.csv` (Agent C, 60 rows, 55 native
parses, 5 prior-quoted):

- `NO_CONSUMER_EDGE`: 10 (A01-R03, FW02 R01/R05, DA04 R01–R03, MD04 R01/R04, RP01 R02/R03)
- `NO_COMMIT_EVENT`: 7 (same squash set)
- `SQUASH_NOT_FAULT_CAUSALLY_PROVEN`: 7 (same set; RP01 `fault_tracked=0`)
- `CRASH_VA_MISMATCH`: 2 (A01-R01 panic VA 0; FW02-R02 0x409c80 vs 0x496798)
- `ORACLE_MALFORMED`: 7 (A01-R01, A03×5, FW02-R02); `RAW_ORACLE_ABSENT`: 23
- `RAW_TRACE_ABSENT`: 5 (FW05, no trace on `8377c011`)
- `STORE_COMMIT_NOT_OBSERVED` / `STORE_SIDE_DATA_HASH_NULL`: 5 each (SP05)
- `NO_REGISTER_WRITEBACK`: 3; `MEMORY_REQUEST_DISCARDED`: 1 (A01-R03);
  `NO_EARLY_ANOMALY_EVENT`: 1 (MD04-R05)

Consumer/commit are absent by construction for A03 (CRASH) and RP01 (HANG).

### Q7. Which workload is recommended for SQ01/SQ03/SP05?

**`ADOPT_SQ_RELOAD` for all three**, pending researcher approval (Decision B).
Evidence is in `audit_v3_3_1/sq_workload/*.md`:

- SQ01: W3 has no per-store reload; `sq_reload` gives
  `mem_write_hash == reload_data_hash == consumer_hash` and SDC 5/5.
- SQ03: W3 is MASKED with `visible_before_commit=0`; `sq_reload` gives
  `CHAIN_VISIBILITY_MOVED` 5/5 (visibility/time shift, **not** SDC — this must
  be stated honestly in the paper).
- SP05: W3/W6 have no consumer; `sq_reload` gives `write_skipped=1` and SDC 5/5,
  conditional on wiring `store_data_fnv` (currently null) and the
  `NO_EARLY_ANOMALY_EVENT` binding.

The frozen workbook still names `sq_drain`/`store_path`; adopting `sq_reload`
changes WorkloadPath, ELF SHA, golden (`7df5034c23f3e703`) and ordinals
(K*=1006/1009/940).

### Q8. Which Fault-Controls must be redone?

From `LSU_60Context_Control_Readiness.csv` / Agent E:

- **READY: 2** (A01-R02, FW02-R01; the only controls on `d3807fbe`).
- **NEEDS_REDO: 16** (valid zero-injection but on superseded binary/config).
- **MISSING: 42** (all DA04/FW05/LP01/MD04 plus most R02–R05 rows).

Every control whose ordinal was re-selected by the percentile mapping must be
re-run: the context no longer matches. Hidden-mount risks persist for
**DA04** (attaches at p=0, selector ignores probability) and **MD04**
(`run_pilot.py` hard-codes `--md04_probability 1.0`); FW02 is mitigated by the
injector-omit branch and commit `364a6057`.

### Q9. Which historical evidence can be retained?

- Retain only as **SHA-keyed historical evidence**: A01/A03/RP01 on
  `68c6ce73`, FW02/SQ on `720eb780`, FW05 on `8377c011`, LQ04 on `f3c2a442`,
  LP01/MD04/DA04 on `0de25644`/`3e9148fc`.
- Do **not** mix chains across SHAs. 45/60 contexts are historical-only;
  `720eb780` and `e527f26a` are no longer on disk.
- FW05's raw trace is absent; its four complete verdicts are prior quotes.
- The final binary `d3807fbe` is the only binary on disk.

### Q10. Which items require researcher approval?

1. SQ01/SQ03/SP05 workload switch to `sq_reload_v3212` (Decision B).
2. Freezing the measured ROI boundaries and percentile ordinals from this
   report into the authoritative workbook.
3. Warm-up/ROI fields (`NEEDS_RESEARCHER_CONFIRMATION` on all 60).
4. FW02/W4 workload change (frozen ELF cannot execute the event).
5. RP01/W7 workload redesign (no partial-overlap event).
6. MD04/W7 workload redesign (N_ROI=1).
7. LP01 observation hook change (add VA/PC; observation-only rebuild).
8. A03 percentile semantics: 3/5 activations are `ALREADY_STUCK`; accept or
   define a tie-breaking rule.
9. Re-running all 60 faults + 58 controls on one binary/config.

### Q11. Minimum next-stage source changes and pilots

1. **Observation-only**: add `va`/`pc` to the `CHAOSL1DForward` record (LP01).
2. **Observation-only**: record the real PC in `A03_STREAM` (currently 0).
3. **Workload**: approve and freeze a W4 with real store→load pairs
   (`sq_forward_v33` is a proposal; its ordinal-1 event still lands in libc
   under WarmUp=0, so the ROI mapping must use the measured window).
4. **Workload**: redesign W7 for RP01 (partial overlap) and MD04 (≥5
   in-loop violations).
5. **Config**: approve `sq_reload_v3212` migration + workbook/oracle update.
6. **Runner**: DA04 control omit-branch; MD04 control forcing
   `--md04_probability 0.0`; RP01 `--dry-run`.
7. **Pilot**: after approval, run one 5-context percentile pilot per model on
   `d3807fbe`, with its five matched controls, before any formal campaign.

---

## 3. Why the status is PARTIALLY_READY

- 40/60 contexts have an observed percentile mapping (25 on formal workloads,
  15 on the recommended SQ workload).
- 20/60 cannot be mapped without a workload redesign (FW02, MD04, RP01) or an
  observation-hook change (LP01).
- Even the 40 mapped contexts are **not formal-ready**: the ROI/ordinal values
  are not frozen in the workbook, the controls cover 2/60 on this binary, and
  the SQ mapping depends on an unapproved workload switch.

No formal campaign was launched. No frozen design was modified.

---

## 4. Independent acceptance (Agent F) and corrections

Agent F re-derived the package independently and returned
`PARTIALLY_READY`/`12_MODEL_FORMAL_READY=NO` as honest. It raised eight
concrete issues; all were corrected or explicitly reconciled in this revision:

1. **LQ04 provenance**: the mapping now records the evidence binary
   `f3c2a442` (v3.2.10) and the on-disk binary `d3807fbe` separately.
2. **LQ04 generation**: the distinctness table now records generations 1..5
   from `lq04_injections.log`, not a hardcoded 1.
3. **FW05 address claim**: corrected to "distinct seq/iterations; R01/R05
   reuse 0x4919c8".
4. **MD04 sufficiency**: the 12-model CSV no longer claims 256 usable pairs;
   it records the measured N_ROI=1 and cites `MD04_w7_r01.jsonl`.
5. **"FINAL binary 68c6ce73"**: relabeled as the historical v3.2.12 baseline;
   the only on-disk binary is `d3807fbe`.
6. **A01 ROI lower bound**: boundary probes K=1035 (PC 0x400a20, outside),
   K=1040 (PC 0x400558, inside) and K=1235 (PC 0x409928, outside) are now
   retained in `A01_w1_r01.jsonl`.
7. **NO_CONSUMER_EDGE list**: the parenthetical now includes A01-R03 (10 rows,
   matching the CSV).
8. **Tool docstring**: no longer claims "no value is invented"; it states that
   ROI/N/ordinals are the measured census table and each row cites its tag.

Residual accepted limitation: only 2/60 controls are valid on the on-disk
binary, and the SQ percentile rows depend on an unapproved workload switch.
No READY claim is made anywhere in this package.

## 5. Reproducibility

- Tooling: `tools/lsu_v331_census.py`, `tools/lsu_v331_build_mapping.py`.
- Probe commands are persisted in every `audit_v3_3_1/roi/census/<tag>/K*/command.txt`.
- Full command/result log: `audit_v3_3_1/report/ROUND_LOG.md`.
- Provenance: `audit_v3_3_1/report/PROVENANCE.md`.
