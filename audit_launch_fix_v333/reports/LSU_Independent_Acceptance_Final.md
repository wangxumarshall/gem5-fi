# LSU v3.3.3 — Independent Final Launch Acceptance

**Date:** 2026-11-13
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Branch:** `lsu-v3.3.1-context-workload-20261111`
**Verified source tree:** `896b64b1` (all launch tooling changes)
**Final tooling HEAD:** `e291857e` (adds this report and evidence logs only; no source change follows)
**Campaign ID:** `LSU-V333-FINAL-20261112`
**Campaign root:** `runs/lsu/formal_v333_final_20261112` (absent before and after every check)

## Verdict

**ACCEPT — `READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES`** for the launch toolchain.

This verdict covers launch readiness only. The 120-run formal campaign has **not**
been started; the researcher's authorization is the only remaining action.

## Measured frozen artifacts

| Artifact | Path | SHA256 | Result |
|---|---|---|---|
| gem5 binary | `build/ARM/gem5.opt` | `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` | match |
| Config | `configs/se/lsu_proxy.py` | `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` | match |
| C++ source | `git diff e3293856..HEAD -- CHAOS/gem5/src` | 0 lines | unchanged |

All 12 models' workload ELFs were hashed from bytes and match the frozen
nine-row table; `FormalExecutionPath == resolve_workload(model)` for every
model; no path points at a v3.2/v3.2.10/archive worktree.

## Test evidence

| Check | Real result |
|---|---|
| `python3 -m pytest tests/ -q` | **513 passed** in 209.25 s |
| Acceptance suite (`tests/test_lsu_v333_final_launch_acceptance.py`) | included above (59 tests) |
| `bash -n` on 01/02/03/04, launch_commands_final, authorization launch | all OK |
| Provenance CLI | `PASS: all 12 models resolve to frozen ELF bytes` |
| 120-task dry-run | **120 DRY-RUN commands**, `READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES`, campaign root not created |
| Control tri-state demo | 0→NO, 1→YES, missing→UNKNOWN, `abc`→UNKNOWN, -3→INVALID; emitter exit 1 |
| Full logs | `LSU_Test_Matrix_Final.log`, `LSU_120Run_Dryrun_Final.log` |

## Gate table

| Gate | Standard | Result |
|---|---|---|
| 12 Fault Models | 12/12 | PASS |
| 60 Contexts | 60/60 | PASS |
| SampleRunID | 60/60 (unique) | PASS |
| Seed | 60/60 (unique) | PASS |
| Fault-Control Pairing | 60/60 (same SampleRunID+Seed) | PASS |
| Control Zero Proof Logic | strict tri-state, missing≠NO | PASS |
| Binary SHA | `62e1b1be…67a6cd` | PASS |
| Config SHA | `8309da72…cb225` | PASS |
| Workload ELF SHA | 12/12 real-byte matches | PASS |
| Campaign Lock | authored under final root, campaign-id bound, live-holder fail-closed, dead-PID reclaim | PASS |
| Resume/Recovery | COMPLETED skip; FAILED/TIMEOUT/OUTPUT_INCOMPLETE new attempt; HASH_MISMATCH refuse; ORACLE_FAIL not replaced; completed bytes immutable | PASS |
| Manifest Isolation | historical root → 0 FORMAL; identity + campaign + containment enforced | PASS |
| Missing Evidence | fail-closed (summary/trace/oracle/InjectionCount never PASS) | PASS |
| Runner Error Handling | nonzero on partial campaign; timeout and child-exception paths tested | PASS |
| Shell Scripts | syntax + ordered dependencies + disjoint outputs | PASS |
| Full Collector | fixture: 18 formal / 6 non-formal, exit 1 correctly | PASS |
| Final Reports | strict control audit; UNKNOWN/INVALID exit nonzero | PASS |
| Python Tests | 513/513 | PASS |
| 120 Task Dry-run | 120/120, 0 collisions | PASS |
| Output Collision | 0 | PASS |
| Historical Data Overwrite | 0 (campaign root untouched) | PASS |
| Independent Acceptance | ACCEPT | PASS |

## Research limitations retained (not launch defects)

- COMPLETE_CAUSAL_CHAIN = 38
- VALID_TERMINAL_CHAIN = 12
- QUALIFIED = 5 (SP05)
- TRACE_INCOMPLETE = 5 (RP01)
- UNRESOLVED = 0

These are approved research limits. No classifier was changed to turn them
into PASS. `QUALIFIED` is never upgraded.

## Honest scope notes

1. No gem5 process was started during this closure; no C++ was compiled; the
   frozen binary was not replaced.
2. The formal campaign root does not exist and no formal result is claimed.
3. The earlier `NOT_ACCEPT` finding (stale authorization packet naming the
   superseded binary/historical root) was corrected by commit `896b64b1`; the
   acceptance test `test_authorization_packet_matches_final_launch_configuration`
   now passes.
4. The `runs/lsu/formal_v333/.lsu_v332_matrix.lock` file with dead PID 3141249
   is historical and irrelevant: the new lock lives under the new campaign root
   and was verified independently.
