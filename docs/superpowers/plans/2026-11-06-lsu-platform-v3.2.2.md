# LSU Platform v3.2.2 — Trace Closure, Pilot Closeout, 9-Model Development

> Status legend per acceptance: DESIGNED / IMPLEMENTED / COMPILED / UNIT_TESTED /
> PILOT_RUN / PROPAGATION_VERIFIED. A claim may only advance when the evidence for
> that exact level exists in the repo.

**Goal:** close the nine Trace defects listed in the v3.2.2 task, finish the three
pilots with honest terminal states, prove Replay with a real run, and start the
remaining nine model hooks — without touching the 12 models, 60 SampleRunIDs,
seeds, F0/F5/F6 semantics or W1–W8.

**Branch/worktree:** `lsu-platform-v3.2.2` in
`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2` (base `33e50fa0`).
v3.2.1 deliverables remain untouched; v3.2.2 artifacts go to new paths.

**Hard rules carried from CLAUDE.md:** one patch per unit; build + real run +
regression before each commit; push after each commit; no formal 60-sample runs;
null stays null; never infer Masked from an incomplete trace.

---

## Task 0 — plan + branch

- [x] Create branch `lsu-platform-v3.2.2`; commit this plan.
- [x] Record carried-over uncommitted v3.2.2 work from the interrupted session
      (`git diff` inventory) as the starting point of Tasks 1–4.

## Task 1 — A03 NO_CHANGE events (Trace defect 8)

**Files:** `CHAOSAddrPath.{hh,cc}`, `lsq.cc`, `CHAOSPropagation.{hh,cc}`,
`platform/trace_writer.py`, `platform/tools/prop_trace_to_v31.py`,
`platform/tests/*`.

- [x] `maybeCorruptPre` takes the real `dyn_seq` (call site passes `inst->seqNum`).
- [x] F5 stuck-at with `addr == old_addr` emits `inj_nochange` with `value_changed=0`.
- [x] Converter maps it to `event_type=injection_nochange`,
      `injection_status=NO_CHANGE`; writer counts it as an injection.
- [x] Unit test: converter NO_CHANGE row; writer count.
- [x] Build (zero new warnings), run A03-R01.
- [x] Verify: `FUNNEL injected == count(injection)+count(injection_nochange)`,
      `NO_CHANGE > 0`, every row has non-zero `dyn_inst_seq`.

## Task 2 — LQ/SQ lifecycle events (Trace defect 4)

**Files:** `lsq_unit.{hh,cc}`, `CHAOSPropagation.{hh,cc}`, converter, `run_pilot.py`, `run_context_sweep.py`.

- [x] alloc on insert, reuse when an index is re-allocated, free on commit/squash
      (`LQ`: commitLoad/squash, `SQ`: completeStore/squash), real index+generation.
- [x] Converter/JSONL: `lq_lifecycle`/`sq_lifecycle`, `lq_entry_id`/`sq_entry_id`,
      `entry_generation`, `sub_unit=alloc|reuse|free`.
- [x] Build, run A01/A03.
- [x] Verify: alloc==free+live at end (or documented truncation on CRASH),
      generation monotonic per index, every event has real seq/gen.

## Task 3 — A01-R03 terminal consistency (Trace defect 7)

**Files:** `platform/run_pilot.py`, `platform/trace_schema.py`,
`LSU_Trace_Schema_v3.2.json`, `platform/terminal.py`, tests.

- [x] Add `UNRESOLVED` to the terminal enum (trace + summary), never null.
- [x] `terminal_state_reason` is written to JSONL summary, pilot_meta and the sweep.
- [x] `accepted=true` requires a non-empty, evidence-backed terminal.
- [x] Re-run A01 R03; verify meta == JSONL summary == sweep row.

## Task 4 — Replay observation mode (defect 5 groundwork)

**Files:** `CHAOSPropagation.{hh,cc,py}`, `configs/se/lsu_proxy.py`.

- [x] `traceReplayAll` records every LSQ replay/squash, not only fault seqs.
- [x] Replay rows carry reason, dyn seq, execution_attempt_id,
      replay_generation, LQ generation.
- [x] Build; verify with the replay pilot (Task 7).

## Task 5 — 15-context sweep with failures (defect 9)

**Files:** new `platform/run_context_sweep.py`.

- [x] Runs A01/A03/FW02 × R01–R05, writes per-context dirs and a 15-entry
      `context_sweep_summary.json`; failed contexts are entries, not omissions.
- [x] Includes accepted, run/activation/terminal + reason, injection funnel,
      record integrity, coverage, oracle, trace counts.
- [x] Run all 15 on the rebuilt binary.

## Task 6 — FW02 closure (defect 6, Phase 2)

**Files:** converter `UNIT_MAP`, `CHAOSPropagation` commit path, `lsq_unit.cc`.

- [x] FW02 unit=`FWD`, sub_unit=`Store-to-Load Forwarding` (Excel model matrix).
- [x] Fault-tracked loads emit a real `commit` node from `commit.cc`; the
      forwarding row keeps store/load seq, store data, decision, memory path.
- [x] Diagnose R02 (no injection) and R03 (INVALID/PARTIAL) with real logs; fix
      the cause or keep the failure with the exact reason.
- [x] Re-run R01–R05; all five present in the sweep with explicit results.

## Task 7 — replay pilot (Phase 3)

**Files:** `platform/run_replay_pilot.py` (new), RC01 pilot config.

- [x] Stable replay trigger on W7 `replay_dependency` (partial-forward branch).
- [x] JSONL: replay reason, original dyn seq, attempt id, replay generation,
      pre/post state, final commit/squash.
- [x] PILOT_RUN evidence required; a hook in source is not evidence.

## Tasks 8–16 — remaining nine models (Phase 4)

**Status in this round: DESIGNED only (0/9 implemented).** The per-model hook
points and the LQ04/RP01/SP05 safety reviews are in
`LSU_Model4_Design_and_Safety_v3.2.2.md`; no unverified hook was committed.


Each task = one model = one commit, with: unique fault definition, real source
hook, config parsing, trigger condition, unit test, target-event proof, trace
association, compile evidence. LQ04 and RP01 get an explicit safety review
(blast radius, bound, hang risk).

- [ ] T8 LQ04 (F0, W2): early LQ-entry invalidation after executeLoad.
- [ ] T9 SQ01 (F0, W3): SQ entry byte0 bit3 after write().
- [ ] T10 SQ03 (F0, W3): premature `canWB` after executeStore.
- [ ] T11 LP01 (F0, W5): load response byte0 bit3 before completeDataAccess.
- [ ] T12 DA04 (F0, W8): byte-enable mask 0xF→0xE for size-4 accesses.
- [ ] T13 FW05 (F6, W8): older-source substitution on partial overlap.
- [ ] T14 MD04 (F6, W7): skip one possibleLoadViolation.
- [ ] T15 RP01 (F6, W7): skip one partial-forward reschedule (safety review).
- [ ] T16 SP05 (F6, W6): suppress one completeStore accounting update.

## Task 17 — Warm-up/ROI recommendation table (Phase 5)

- [x] Per W1–W8: init phase, warm-up end condition, ROI start/end events,
      R01–R05 statistics origin, injection-allowed range.
- [x] Mark every row `NEEDS_RESEARCHER_CONFIRMATION`; do not alter the 60 rows.

## Task 18 — final W1–W8 baseline (Phase 6)

- [x] Rebuild from the final commit; record SHA256.
- [x] Run 8 fault-free baselines, save logs + oracle + target-event evidence.
- [x] New report; old v3.2/v3.2.1 results stay labelled as old.

## Task 19 — disk inventory (Phase 7)

- [x] Read-only inventory: duplicate builds, regenerable temp files, historical
      traces, 60-run space estimate, archive recommendation.
- [x] No deletion; deletions wait for researcher approval.

## Task 20 — package + A–H status report

- [x] `LSU_v3.2.2_Implementation_Package.zip` with git diff/commits, source,
      logs, real JSONL and pilot results.
- [x] Report A–H with per-item DESIGNED/IMPLEMENTED/COMPILED/UNIT_TESTED/
      PILOT_RUN/PROPAGATION_VERIFIED. No item is upgraded without evidence.
