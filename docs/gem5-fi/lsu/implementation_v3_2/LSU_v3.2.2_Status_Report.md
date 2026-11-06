# LSU v3.2.2 — Final Status Report (A–H)

**Branch:** `lsu-platform-v3.2.2`
**Base:** `33e50fa0` (v3.2.1)
**Final commit:** see `git log --oneline` after this report; the binary is bound
in `GIT_COMMIT_v322.txt` (SHA256
`7a584a08d55df148eebe090530f56a14679b38567c936f6ed9723aa59dff278d`).
**Formal 60 samples:** not started. No formal SampleRunID was executed.

Status vocabulary used below, in the required order:
DESIGNED → IMPLEMENTED → COMPILED → UNIT_TESTED → PILOT_RUN →
PROPAGATION_VERIFIED. A higher level is only claimed when this round's evidence
exists.

---

## A. Trace public-function repair status

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | `fragment_id` in the JSONL top level | IMPLEMENTED / COMPILED / UNIT_TESTED / PILOT_RUN | C++ already wrote it in the detail; the converter now maps it. A03-R01: 66/66 `memory_response` rows have a fragment id (0/435 before the fix); test added |
| 2 | Load Response and Register Writeback data | IMPLEMENTED / COMPILED / PILOT_RUN | Real packet hex/FNV in `memory_response`, writeback value/hash + phys/arch reg in `register_writeback` (A01/A03/FW02 JSONL) |
| 3 | Real Producer–Consumer data dependency | IMPLEMENTED / COMPILED / PILOT_RUN | Edges come from the taint set (physical-register dependency), not ptag order; `consumer_commit` + `propagation_edge` with source/destination hashes |
| 4 | LQ/SQ alloc/free/reuse lifecycle | IMPLEMENTED / COMPILED / PILOT_RUN | 672 lifecycle nodes in A03-R01 (LQ 309, SQ 363), real index + monotonic generation, actions alloc/reuse/free |
| 5 | Replay / Squash real run events | IMPLEMENTED / COMPILED / PILOT_RUN (replay) / PILOT_RUN (squash) | Replay pilot: 5 real `partial_forward_mismatch` replays with attempt/generation and final commit/squash; 1203 squash nodes in the same run |
| 6 | FW02 unit/sub-unit | IMPLEMENTED / COMPILED / PILOT_RUN | Forwarding rows are `unit=FWD`, `sub_unit=Store-to-Load Forwarding` (Excel model matrix), with `normal_decision` / `fault_decision` |
| 7 | A01-R03 terminal consistency | IMPLEMENTED / UNIT_TESTED / PILOT_RUN | `UNRESOLVED` + `UNRESOLVED_NO_DATA_VALUE_EVIDENCE` in both `pilot_meta` and the JSONL summary; `accepted=false`; no empty terminal |
| 8 | A03 all NO_CHANGE events | IMPLEMENTED / COMPILED / UNIT_TESTED / PILOT_RUN | A03-R01: 73 `INJECTED` + 73 `NO_CHANGE` = 146 = Funnel `injected`; every row has a real `dyn_inst_seq` |
| 9 | `context_sweep_summary.json` with all 15 contexts | IMPLEMENTED / UNIT_TESTED / PILOT_RUN | 15/15 entries; the failed A01-R03 is an entry, not an omission |

## B. A01 / A03 / FW02 five-context validation

`pilots_v3_2_2/sweep/context_sweep_summary.json`: **15 recorded, 14 accepted,
1 honest failure**.

| Model | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| A01 | CRASH (1 inj) | MASKED | **UNRESOLVED** (no data value; accepted=false) | MASKED | MASKED |
| A03 | CRASH (146) | CRASH (145) | CRASH (144) | CRASH (143) | CRASH (142) |
| FW02 | MASKED | CRASH (real suppression, load 6048 / store 6042) | MASKED | MASKED | MASKED |

A01-R01/R02/R04/R05 and all A03/FW02 contexts are accepted with complete,
valid traces. FW02 R02 is a fault-caused crash; R03 was a tracer-induced panic
(`Unsupported register class type 2`) that is now fixed, so it is MASKED.
A01-R03 remains deliberately unresolved: the run has no memory-response or
writeback value, so it cannot be called MASKED.

## C. Replay actual-run validation

`pilots_v3_2_2/REPLAY-RW02` (PILOT-REPLAY-RW01): COMPLETED, TRIGGERED, oracle
PASS (MASKED), trace COMPLETE/VALID, **5 replays**, all
`reason=partial_forward_mismatch`:

| dyn seq | attempt | replay gen | final |
|---|---:|---:|---|
| 69296 | 1 | 1 | COMMITTED (tick 31129945) |
| 70968 | 1 | 1 | SQUASHED (35429240) |
| 70969 | 1 | 1 | SQUASHED (35429240) |
| 71973 | 1 | 1 | COMMITTED (36569225) |
| 72305 | 1 | 1 | COMMITTED (37428545) |

Status: **PILOT_RUN**, not PROPAGATION_VERIFIED: the replays are real but are
not caused by the injected FW02 suppression; the summary says so explicitly. A
separate A01-carried attempt (`REPLAY-RW01`) crashed before the replays and is
kept as a failed attempt.

## D. LQ/SQ lifecycle tracking

IMPLEMENTED / COMPILED / PILOT_RUN. A03-R01 contains 309 LQ and 363 SQ nodes
with real index and generation; alloc+reuse = 155 (LQ) / 182 (SQ) and free =
154 / 181, differing by exactly the one entry live at the crash. Every node has
a non-zero `dyn_inst_seq` and a non-null generation.

## E. Remaining nine models

**DESIGNED only — 0/9 implemented.** No hook was committed unverified.
`LSU_Model4_Design_and_Safety_v3.2.2.md` records each model's real hook point,
trace link, risk and gate, including the mandatory safety review for LQ04 and
RP01 (and SP05). Recommended order: SQ01 → DA04 → LP01 (wire the existing
L1DForward injector) → MD04 → FW05 → SQ03 → SP05 → LQ04 → RP01.

## F. Final W1–W8 binary baseline

COMPILED / PILOT_RUN. 8/8 exit 0, 8/8 oracle PASS with the final binary; target
events confirmed (loads/stores, W7 267 forwards and 5 reschedules, squashes).
Results in `baselines_v3_2_2/`; the v3.2.1 `baselines/` tree is untouched and
still labelled with its old binary (`b233a4cb…`). Report:
`LSU_Baseline_v3.2.2.md`.

## G. Warm-up / ROI items awaiting confirmation

DESIGNED, every row `NEEDS_RESEARCHER_CONFIRMATION`. See
`LSU_Warmup_ROI_Recommendation_v3.2.2.md`. The 60 SampleRunIDs, RunIDs,
SubTaskIDs and seeds are unchanged. Four explicit questions are listed for the
researcher.

## H. Disk-space risk

`/home` is at **92 %, 29 GB free**. Nine `gem5.opt` copies occupy 9.6 GB and the
inactive R6 worktrees ≈ 10 GB. The 60-sample campaign is estimated at 1.2 GB of
artifacts plus a 5 GB reserve. No deletion was performed. See
`LSU_Disk_Inventory_v3.2.2.md` for the approval-gated archive plan.

---

## Commits in this round

| Commit | Unit |
|---|---|
| plan commit | v3.2.2 work list |
| TRACE node contract | A03 NO_CHANGE + LQ/SQ lifecycle + outdir fix |
| TRACE replay switch | `traceReplayAll` / `--prop_replay_all` |
| PILOT terminal | `UNRESOLVED` consistency |
| TRACE register guard | no panic on a vector consumer |
| PILOT sweep | 15-context runner + evidence |
| FW02 closure | FWD unit, normal/fault decision, real commit |
| PILOT replay | replay mechanism pilot |
| DOCS 5/6/7 | warm-up/ROI, baseline, disk, model-4 safety |
| TRACE ids | fragment/source/destination top-level mapping |

## What must not be claimed

- No formal 60-sample result exists.
- The nine models are not implemented.
- The replay pilot proves the replay mechanism under a fault run, not that the
  SUPpression caused the replays.
- The A01-R03 failure is a real unresolved outcome, not a pass.
- Warm-up/ROI values are recommendations, not frozen configuration.
