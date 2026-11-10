# RP01 Five Dynamic Contexts — v3.2.11 Design

**Status: design only. No RP01 fault pilot was launched. The five contexts must be re-proven by a clean count-only preflight before any pilot.**

## 1. Frozen identities (unchanged)

| Pilot | SampleRunID | Seed | EventOrdinal |
|---|---|---:|---:|
| R01 | RP01-F6-W7-S01-R01 | 3135797961 | 1 |
| R02 | RP01-F6-W7-S01-R02 | 226489823 | 2 |
| R03 | RP01-F6-W7-S01-R03 | 1735144973 | 3 |
| R04 | RP01-F6-W7-S01-R04 | 2455796178 | 4 |
| R05 | RP01-F6-W7-S01-R05 | 3984724524 | 5 |

## 2. Candidate contexts from the existing replay probe

The existing `pilots_v3_2_2/REPLAY-RW02` run (workload `replay_dependency`, seed 3135797961, FW02 fault-on, `--prop_replay_all`) recorded exactly five `partial_forward_mismatch` replay events. They are listed here in **ordinal order** (the order they occur), not selected by outcome:

| Ordinal | dyn_inst_seq | PC | Tick | LQ entry | Entry gen | Pre→post replay gen | Final result (recorded, not used for selection) |
|---:|---:|---|---:|---:|---:|---|---|
| 1 | 69296 | 0x4015fc | 31072965 | 9200 | 9690 | 0→1 | COMMITTED |
| 2 | 70968 | 0x42a6d8 | 35427700 | 9348 | 9912 | 0→1 | SQUASHED |
| 3 | 70969 | 0x42a6dc | 35428085 | 9349 | 9913 | 0→1 | SQUASHED |
| 4 | 71973 | 0x422a58 | 36564990 | 9426 | 10046 | 0→1 | COMMITTED |
| 5 | 72305 | 0x44e2ec | 37424310 | 9466 | 10093 | 0→1 | COMMITTED |

The five tuples `(seq, pc, lq_entry, entry_generation)` are all distinct. The probe's own note states the replays are real partial-forward reschedules observed under a fault run and are not claimed to be caused by the injected bit flip — so they are evidence of the **event stream**, not of RP01 causality.

## 3. Proposed mapping and required preflight

The mapping R01–R05 to the five observed events is a **design hypothesis**, because the probe used one seed (R01's) under a different fault. Before any RP01 pilot:

1. Run a clean **count-only** probe for each of the five seeds (no injection, no fault), with the `CHAOSRP01` selector in count-only mode (to be implemented after approval) or an equivalent read-only replay observer.
2. For each seed, record the first five eligible partial-forward events (ordinal 1–5) with `(seq, pc, tick, lq_entry, entry_generation, pre/post replay_generation)`.
3. Require five **distinct** contexts per the table's dimensions (store/load address overlap, store coverage, load size, load PC, store PC, dependency, pre/post replay state).
4. If a seed cannot supply five distinct events, report `WORKLOAD_INSUFFICIENT_FOR_FIVE_CONTEXTS` and propose the workload adjustment in `RP01_Workload_Verification_v3.2.11.md` §4. Do not reuse one event five times and do not select events by whether they later produce SDC or a consumer.
5. Preserve the SampleRunIDs and Seeds above; no formal fault pilot until the researcher approves the definition and the count-only proof is attached.

## 4. What a valid context must record

- Target Load: `dyn_inst_seq`, PC, `lq_entry_id`, `entry_generation`, `execution_attempt_id`, `replay_generation` (pre and post).
- Target Store: `stallingStoreIsn` / `stallingLoadIdx`, store PC, store size, coverage kind (`PartialAddrRangeCoverage`), overlapping byte range.
- Pre-replay state: issued / `canIssue` cleared / `instsToReplay` membership.
- Expected fault action: the single skipped `rescheduleMemInst` at `lsq_unit.cc:2016` for this ordinal.
- Expected terminal: HANG/TIMEOUT unless a squash intervenes (then SQUASHED). No SDC claim is made for this model.

## 5. Current status

- Five distinct event tuples are **observed** in an existing probe.
- Five distinct contexts under the five frozen seeds are **not yet proven**.
- No pilot was run. The design remains `NEEDS_USER_DECISION`.
