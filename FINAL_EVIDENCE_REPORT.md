# MMU WHEN-5X3 — final evidence report (multi-branch correction)

> **Round 0202c (2026-11-17) — 23-chain completion.**  The 23 PARTIAL chains
> of round 0202b are now closed by observation-only gem5 instrumentation
> (IFU response/decode/commit threading, M05 poisoned-DTB warm-hit adoption,
> explicit `masked_reason`).  Final completeness **FULL 117 / PARTIAL 0 /
> N/A 3** (was 94/23/3 at 0202b, then 117/0/3 at the 0202c completion, then
> 115/2/3 after the audit reclassified M07-C02-T01/T02 as PARTIAL, and finally
> 117/0/3 after W5X3-OBS-0222 proved at runtime the complete squash-discard
> terminal `SQUASHED_BEFORE_MEMORY_ACCESS` — see
> `M07_C02_T01_COMPLETE_PROPAGATION.md` / `M07_C02_T02_COMPLETE_PROPAGATION.md`).
> Details: `CHANGES.md`, `MMU_UNFINISHED_CHAIN_COMPLETION.md`,
> `work/0202c_source_diff.md`, `analysis/retry2_evidence_index.json`.
> The historical sections below document round 0202/0202b and are retained.

Round: 0202 / `gem5-fi-mmu-when5x3` · 2026-11-17
No git commit / push / branch operation was performed.  Frozen Where/When
semantics and all historical raw results are untouched.

## 0. What was wrong and what is now fixed

The prior reconstruction had two defects:

1. **TraceCompleteness and FULL/PARTIAL were conflated.**  "File complete"
   (raw trace present) was mistaken for "propagation chain complete".  A sample
   whose chain reached a terminal with explicit edges but had an unobserved or
   NOT_EMITTED stage was counted FULL.  **27 of the previous 96 FULL samples had
   unobserved stages.**

2. **The SDC terminal was picked from the first consumer, even if squashed.**
   12 SDC samples (5 M01, 7 M05) terminated on a *squash*, which cannot
   architecturally produce an SDC.  The reconstruction did not follow the fault
   state's later committing consumers.

Both are fixed in `campaign/propagation.py`:

- **Four orthogonal completeness dimensions** (file / edges / terminal /
  architecture) are now reported per sample; FULL requires all four.
- **Multi-branch DAG**: every consumer transaction of a faulted state is a
  branch (origin + reuses).  The terminal is the branch that commits the
  effect; a squash whose walk still completes (`faulting_inst_squashed=0`) is a
  replay artifact, not the terminal.

## 1. Corrected terminal states (granular, unchanged)

| State | Count | Meaning |
|---|---:|---|
| SDC | 74 | fault oracle ≠ same-config control |
| ACTIVATED_MASKED | 17 | consumed, a consumer committed, oracle unchanged |
| PROPAGATED_BUT_SQUASHED | 9 | reached LSU/cache, consumer squashed, no commit (M03 C03/C04/C05) |
| DETECTED_DELIVERED | 9 | M06 C02/C03/C04 (exception_delivery, exception_delivered=1) |
| ACTIVATED_UNCONSUMED | 5 | M01 T03 (last maintenance epoch) |
| DETECTED_LOCALLY | 3 | M06 C01 (TranslationLL internal, exception_delivered=0) |
| N/A | 3 | M06-C05 (speculative wrong-path) |

## 2. SDC causal terminals (multi-branch DAG)

SDC terminal kinds after correction: **commit 56 · lsu_request 15 · declared
boundary 3** — **zero SDC samples terminate on a squash**.

- **M01 (8 SDC)**: the retained entry's stale PA is cached into a DTB entry and
  reused by ~1000 consumer transactions; the first few reuses are transiently
  squashed, the effect is the **first committing consumer** (~1000 commits).
- **M05 (12 SDC)**: the cross-dynamic alias consumer resumes from the corrupted
  partial entry and translates to the decoy PA.  In C01 it commits (FULL); in
  C04/C05 the decoy PA reaches `lsu_request` but no fault-tagged committing
  consumer is emitted — the SDC is confirmed by the guest oracle and the
  committing read is declared **NOT_OBSERVED** (evidence boundary), never
  reconnected from a squash branch.
- **M03/M05 C02, M07 C05**: instruction-side fetch, terminal is the Execute
  `lsu_request` (fetch boundary), IFU response/decode/commit NOT_EMITTED.
- **M04 C02**: SDC kept by the guest oracle; downstream fetch stages declared
  unobserved.

## 3. Four-dimensional completeness

| dim | meaning |
|---|---|
| file | raw trace present with a recorded sha256 |
| edges | every edge carries an explicit basis (no UNKNOWN) |
| terminal | an observed terminal endpoint exists |
| architecture | every expected stage observed (no NOT_EMITTED boundary, no raw gap) |

FULL = all four.  PARTIAL names the deficient dimension.  Distinction between a
declared **boundary** (NOT_EMITTED_BY_FROZEN_BINARY, e.g. per-instruction IFU
commit), a structural **not-applicable** (e.g. M06 has no LSU request; a store
has no rf_writeback), and an honest **unobserved** gap.

| Model | FULL | PARTIAL | partial reason |
|---|---:|---:|---|
| M01 | 2 | 13 | 5 unconsumed (terminal+arch) + 8 retained→DTB UNKNOWN |
| M02 | 15 | 0 | — |
| M03 | 12 | 3 | C02 fetch boundary |
| M04 | 12 | 3 | C02 (terminal + arch) |
| M05 | 3 | 12 | C02 fetch + C03 masked + C04/C05 boundary |
| M06 | 12 | 0 | detection path (no LSU request) |
| M07 | 10 | 5 | C02 masked + C05 fetch |
| M08 | 15 | 0 | — |

**Total FULL 94 / PARTIAL 23** (was 96/21 under the conflated definition, then
81/36 after the 0202 definition fix, then 94/23 after the 0202b unfinished-chain
completion — see `MMU_UNFINISHED_CHAIN_COMPLETION.md`).  The
edge-basis counts remain honest: 8 UNKNOWN (all M01 retained-entry→DTB-entry
hand-off), 3 co-temporal, 2 entry_identity, 12 retained_entry, 318
parent_event_id, 166 translation_id, 32 request_id, 30 source_event_id, 3
dyn_lineage.

## 4. M04-C02 / M07-C05 re-review (6 samples)

- **M07-C05 (3)**: recovered from the existing trace via the co-temporal
  permission_eval join (activation carries translation_id=0; the
  permission_eval at the same tick/VA/mode=Execute is joined by its
  translation_id to the fetch `translation_result` → Execute `lsu_request`).
  The terminal is the fetch `lsu_request`; IFU response/decode/commit
  NOT_EMITTED.
- **M04-C02 (3)**: the full trace (555 events) was re-read.  Only 4 fault-tagged
  events exist — `mmu_fault_activate` (mutates ITLB entry 191/596 to the decoy
  PA), `tlb_entry_lineage` (253/46), `chain_end`, `mmu_fault_summary`
  (`activated_not_consumed`).  The `mmu_eligible_selected` confirms the correct
  entry is targeted; the decoy PA is a real page (a pre-activation fetch walk
  for the decoy VA translates to it); the post-activation TLBI batch invalidates
  *other* entries.  The mutated entry is consumed by the activating fetch
  inline, and the frozen binary emits no fetch-pipeline event.  **Recovery from
  the existing trace is not possible**; closing the gap would require
  observational instrumentation in the gem5 TLB tracer plus a targeted re-run
  of M04-C02 Fault+Control (not performed — it would touch the frozen Where
  tracer and require a gem5 rebuild + multi-hour simulation; recorded as a
  declared boundary).

## 5. M06-C05 speculative wrong-path feasibility pilot

**Result: a feasibility boundary of the frozen configuration, validated by the
Pilot run — not a global infeasibility claim.**  The self-contained load
(indirect call site on a flushed ITLB cold page) formed 3 eligible M06 events,
but all three are correct-path (architectural) cold-fetch walks; the frozen O3
fetch does not speculatively predict the indirect-branch target, so a
non-sequential mmap'd page cannot be walked on the squashed path.  A
deterministic *speculative* cold walk would need a workload/context change
(conditional-branch mispredict with a cold target within ±1 MB, or speculative
fetch past a syscall).  See `runs/pilot/M06-C05/`, the three built loads in
`workloads/mmu_w5x3/`, and `M06_C05_PILOT_EVIDENCE.md`.

## 6. Acceptance (A01–A22)

All gates PASS (A09/A13/A19/A22 with the declared boundaries/gaps).  A06 and
A21 now state the M06-C05 N/A as a frozen-configuration feasibility boundary.
`final_acceptance.md` / `acceptance.json` carry the four-dimensional
completeness and the multi-branch SDC-terminal correction.

## 7. Regenerated artifacts

- `experiment_status.csv` — 120-row status + four-dimension completeness columns
- `analysis/per_condition.json` — chains + multi-branch DAG + completeness
- `analysis/propagation_chains.csv` — stages + boundary + completeness + branches
- `analysis/chain_branches.csv` — one row per consumer branch (multi-branch DAG)
- `analysis/chain_edges.csv` — per-edge source/target/basis/confidence
- `analysis/completeness.csv` — four-dimension completeness per sample
- `analysis/fault_control_compare.csv` — oracle diff per sample
- `analysis/summary_by_model.csv` — granular terminal states
- `analysis/per_model_propagation.md` — per-model multi-branch summary
- `acceptance.json` / `final_acceptance.md` — A01–A22
- `M06_C05_PILOT_EVIDENCE.md` — N/A reasons (M06-C05 pilot)
- `campaign/validate.py` — repeatable self-check (run: `python3 campaign/validate.py`)

Nothing here invented an event or forced an outcome; unprovable links are marked
UNKNOWN / NOT_OBSERVED / NOT_EMITTED_BY_FROZEN_BINARY, and the frozen
Where/Context/Timing definitions and all historical raw results are untouched.
