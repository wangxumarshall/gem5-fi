# SDD ledger — plan: docs/superpowers/plans/2026-11-08-lsu-v3.2.10-lq04.md

Baseline: 37692d2beffcb73fc9303ad9de4c6bb341d5de71 (lsu-platform-v3.2.10)
Spec: docs/superpowers/specs/2026-11-08-lsu-v3.2.10-lq04-design.md (read; binding)

## Pre-flight scan

| Pair | Interface | Finding |
|---|---|---|
| T1 → all | spec decisions D1–D6 → every task | clean |
| T2 → T10 | workload ELF + Oracle + SHA → pilots | clean |
| T3 → T5/T6 | `isEligible/shouldSelect/identityMatches/shouldInject` | clean |
| T4 → T6 | `corruptLifetime/restoreLifetime/lq04Corrupt` | **conflict fixed: `commitLoads` pre-assert at :890 fires before `commitLoad` restores** |
| T5 → T6 | `maybeSelect/isTarget` signatures | clean |
| T6 → T7 | `noteLQ04Injection(...)` argument list | clean |
| T7 → T8 | `lq04` trace family + resp fields | clean |
| T8 → T10 | `run_pilot --model LQ04` | **conflict fixed: `EXCEL` pointed at v3.2.3 and no `MODELS` constant** |
| T9 → T10/T11/T13 | binary SHA + regression + build log | clean |
| T10 → T11/T12/T13 | ten pilot dirs + summary CSV | clean |
| T12 → T13 | v3.2.5 xlsx + matrix | clean |
| T2 self | assembly vs exit status | **conflict fixed: `_start` inherited main's return in x0 as exit code** |
| T6 self | response probe vs squashed/reused slot | **conflict fixed: guard `!inst->isSquashed()`** |
| T9 self | regression expectation | **conflict fixed: expect `checksum=0xf247ef3fe6f02cfd`** |
| T8 self | test references `run_pilot.MODELS` | **conflict fixed: introduce `MODELS` and use it in argparse** |
| T4 self | destructor vs side channel | clean (destructor frees the stash) |
| T13 self | zip contents vs 24 required sections | clean |

Rulings:
- Ruling: `commitLoads()` pre-loop check accepts `lq04Corrupt()` and `drainSanityCheck()` accepts it; `commitLoad()` restores before its own assert — the corrupted entry can be the head without aborting, no other assertion relaxed. Why: the documented corrupt state must survive until its real commit boundary. Cost if wrong: a corrupted head still aborts, caught by the Task 6 smoke and fixable in one line.
- Ruling: `run_pilot.py` reads the authoritative v3.2.4 workbook (not v3.2.3) and exposes `MODELS`; pilots are transcribed into v3.2.5 afterwards. Why: v3.2.4 is the frozen authority and the planned test needs a stable model list. Cost if wrong: pilot rows are read from a stale workbook; evidence would be re-run.
- Ruling: anchor `_start` zeroes x0 before `exit`. Why: a checksum-derived exit code would fail the oracle check for reasons unrelated to the fault. Cost if wrong: non-zero exit misclassified as CRASH.
- Ruling: response probe is guarded by `!inst->isSquashed()`. Why: `lqIdx` can be reused after squash. Cost if wrong: probe reads an unrelated entry.
- Ruling: canonical regression must print `checksum=0xf247ef3fe6f02cfd`. Why: CLAUDE.md's canonical regression golden. Cost if wrong: regression check is weaker.

## Progress

Task 1: complete (commits 37692d2b..7f397e2f, review clean)
Task 1: minor (deferred): report-side arithmetic "11 FW05 stdout.log" vs committed 10; audit citation `lsq.hh:538-542` starts one line before the stated block.
Task 2: complete (commits 7f397e2f..36d89497, review clean)
Task 2: minor (deferred): workload build is not byte-reproducible (build-id/other bytes); frozen SHA pins the committed artifact. `volatile` added to arr/guard (documented).
Task 2: fact — gem5 process exit code does not propagate the simulated workload exit status; the oracle must be the checksum line, not `exit_code`. Task 8/10 must treat `ORACLE_FAIL: no checksum line` as failure.
Note: the plan file remains untracked; commit it in Task 3 (explicit path) so the live plan is in git.
Plan committed separately: 12cc4ab8 [PLAN].
Task 3: review found Important — the brief's assertion set never passes `squashed=true`, so `!squashed` is unverified.
Task 3: Ruling: add `assert(!isEligible(true, true, true, false));` (and the executed+squashed combination) to the test; the spec requires `isEligible` to reject squashed entries and the test must pin every branch. Fix round 1 dispatched. Cost if wrong: one extra assertion and a fix commit.
Task 3: fix round 1/5 (1 addressed, 0 open; commits 00bad521..8ff3d596)
Task 3: complete (commits 12cc4ab8..8ff3d596, review clean after fix)
Task 3: minor (deferred): `shouldSelect` assertions do not distinguish `==` from `>=`; equality is correct for exactly-once ordinal semantics.
Task 4: complete (commits 8ff3d596..b28f81ee, review clean)
Task 4: minor (deferred): `lq04Restore` is public though the brief's file-list label said private helpers; inert because `LQEntry` is a private nested alias. Plan-checkbox DOCS commit included.
Task 4: fact — clean build from scratch succeeded, binary SHA 1c1022f2… at both repo-root and CHAOS/gem5 paths; reg_chain checksum f247ef3fe6f02cfd.
Ruling: Task 5 cannot prove the five eligible probes because the `executeLoad` call site belongs to Task 6; Task 5's acceptance is "SimObject compiles, mounts, and the no-fault run is unchanged", and the five-anchor probe assertion moves to Task 6 Step 4. Why: keeping the hook in one unit (one patch per unit) outweighs an earlier probe. Cost if wrong: probe validation slips one task.
Task 5: complete (commits b28f81ee..2f71c564, review clean)
Task 5: minor (deferred): watchdog not canceled after injection (500M cycles >> workload); armed in count-only; target_restored/attempt_id written but unread; watchdog units are cycles vs SQ03 ticks — Task 8 must not copy SQ03's value.
Ruling: Task 6's call to `CHAOSPropagation::noteLQ04Injection` requires the method that Task 7's Step 1 defined; move the `lq04_registry` + `noteLQ04Injection` declaration/implementation into Task 6 (injection node belongs with the injection unit), leaving Task 7 the response/writeback/consumer binding. Why: Task 6 cannot compile otherwise, and splitting registry+binding is still one coherent unit each. Cost if wrong: Task 7's diff is smaller than planned; no semantic change.
Task 6: fact — `LSQCheckLoads` defaults true, so `executeLoad`'s `else` branch early-returns via `checkViolations` and the literal function tail is unreachable for normal loads; the early return was restructured into a conditional return (identical fault on every path) so a clean check reaches the injection point and a violation-triggered replay never injects.
Task 6: fix — Task 5's `cpu.hh` member used an inline `class CHAOSLQ04` inside `o3::CPU`, implicitly declaring the unrelated incomplete `gem5::o3::CHAOSLQ04` in TUs that include `cpu.hh` first (first build failed on lsq_unit.o); fixed with a gem5-namespace forward declaration in the same commit. Also caught a masked-exit stale-binary copy (pipe hid scons Error 1; re-ran with pipefail).
Task 6: complete (commits a6abe75d code + 027c5f39 plan checkboxes, pushed; binary dca3aa3e…). A: five probes on 400338/33c/340/344/348, N=4317, checksum b097eb83f71545cb. B (ordinal 1): one injection seq=3 lq_idx=1 gen=1, restore reason=commit, one inj/response_probe(valid=0)/restore row, checksum unchanged, exit 0. C (ordinal 5): one injection seq=7 lq_idx=5 gen=5 on the fifth anchor, same rows, checksum unchanged, exit 0. Regression reg_chain f247ef3fe6f02cfd exit 0.
Task 6: minor (deferred): watchdog still exits non-zero at watchdogCycles even after a successful injection (Task 5 carryover; harmless for pilots but Task 8 must keep workloads far under 5e8 cycles or cancel it); response_probe/restore rows are ptag=0 by noteLQLifecycle design — chain binding happens on the resp node in Task 7; noteRestore now wired (CHAOS_LQ04_RESTORE line) — was a dead interface after Task 5.
Task 6: complete (commits 44ff2677..027c5f39, review clean; opus reviewer verified executeLoad control-flow equivalence and one-shot/identity safety)
Ruling: Task 7 owns only the `lq04` binding in `noteMemResponse`/`noteChainWriteback` (registry + injection node landed in Task 6). Why: one unit per patch with the compile dependency satisfied. Cost if wrong: response/consumer nodes lack the LQ04 ptag and Task 8 would see no chain.
Task 7: review found Important — Task 6's injection detail `field=valid,request` contains a comma, violating the CSV no-comma contract and truncating the JSONL injection record.
Task 7: Ruling: fix the token to `field=valid+request` in `CHAOSPropagation.cc` now (inside Task 7's allowed files); the CSV contract is binding and the plan text's comma is a defect. Why: Task 8/11 need the injection identity fields in JSONL. Cost if wrong: trace detail spelling changes; no semantics.
Task 7: minor (deferred): `entry_valid/request_at_response=0` in the resp detail are constants (mitigated by the live `response_probe` node); ~50 lines duplicated from the generic writeback tail.
Task 7: fact — binding yields inj→resp→taint_reg→326 real consumer_commit nodes, all hash-matched; validator VALID; completeness COMPLETE (before the Task 8 profile); checksum unchanged.
Task 8: complete (commit 1dbe2797 code + plan-checkbox/report DOCS commit). TDD: tests/test_lq04_platform.py RED 7-fail → GREEN 8/8; test_lsu_v324_workbook 5/5; full suite 48 passed / 2 known disk-guard failures (free 13.4 GiB < 70.6 GiB red line, environmental). Real-gem5 smoke pilot LQ04-PLATFORM-SMOKE (R01, --preserve-sample-id, workload lq_lifetime_ordinal): exit 0, one injection seq=3 lq_idx=1 gen=1 request_id=3 addr=0x41ffe8 ordinal=1, restore reason=commit, oracle PASS checksum=0xb097eb83f71545cb (workload_golden), terminal MASKED / TARGET_COMMITTED_DATA_VALUE_PRESENT / DIRECT_DATAFLOW_EVIDENCE, trace COMPLETE+VALID, coverage COMPLETE, chain_integrity PASS (ptag=1, 335 chain events, SAME_ATTEMPT), accepted=true, JSONL injection record unit=LQ sub_unit=executeLoad.
Task 8: additions beyond the nine listed gaps (both SQ03/SP05-precedent, no other-model behavior change): CHAOS_LQ04_WATCHDOG_EXPIRED added to watchdog_hit (watchdog abort → HANG, not CRASH); matched control (probability 0.0) empties the whole LQ04 extra list because the selector is ordinal-gated, not probability-gated.
Task 8: minor (deferred): no ("LQ04","SDC") profile — unexpected SDC would fall back to DEFAULT_PROFILE ("injection",); the matched-control path is implemented but not yet exercised against real gem5 (Task 10 owns the five controls); Excel LQ04 WorkloadPath still names the legacy lq_lifetime binary until the Task 12 v3.2.5 transcription (pilots override with --workload and the oracle comes from the golden).

