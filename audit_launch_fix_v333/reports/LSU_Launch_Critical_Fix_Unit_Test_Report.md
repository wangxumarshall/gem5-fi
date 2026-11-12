# LSU v3.3.3 — Launch-Critical Fix Unit Test Report

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Baseline:** HEAD `58d77b34`; source `b5031bf7`; binary `1126e0fd`; config `8309da72`.
**Nature:** synthetic only. No gem5/scons process was started; no historical
run evidence is read by any assertion except the explicitly isolated negative
fixture `tests/fixtures/lsu_v333_synthetic/historical_evidence/`.

## 1. Full suite — exact output

```console
$ python3 -m pytest tests/test_lsu_v333_runner_errors.py tests/test_lsu_v333_control_proof.py \
    tests/test_lsu_v333_qualified.py tests/test_lsu_v333_manifest_isolation.py \
    tests/test_lsu_v333_synthetic.py -q -p no:cacheprovider
123 passed in 16.63s
```

- `tests/test_lsu_v333_runner_errors.py`: 40 passed (runner exit/timeout/status,
  parse-error persistence, campaign identity, RP01 paired seed).
- `tests/test_lsu_v333_control_proof.py` + `tests/test_lsu_v333_qualified.py`:
  41 passed.
- `tests/test_lsu_v333_manifest_isolation.py`: 6 passed.
- `tests/test_lsu_v333_synthetic.py`: 36 passed, 0 skipped (the 12 collector
  tests that were `PENDING (Agent B)` now execute).

## 2. Required scenario matrix

| # | Scenario | Test | Result |
|---|---|---|---|
| 1 | complete Fault run → FORMAL | `test_collector_complete_fault_and_control_are_formal` | PASS |
| 2 | complete Control run → real zero proof | `test_control_complete_zero_applied_passes` / collector test 1 | PASS |
| 3 | missing `summary.json` | `test_collector_missing_evidence_is_never_pass[A01-R02-fault]` | PASS (`OUTPUT_INCOMPLETE`) |
| 4 | missing Fault trace | `...[A01-R03-fault]` | PASS (`OUTPUT_INCOMPLETE`) |
| 5 | missing Control trace | `...[A01-R03-control]` | PASS (`OUTPUT_INCOMPLETE`) |
| 6 | Control applied > 0 | `test_control_applied_greater_than_zero_fails` | PASS (`FAIL`) |
| 7 | Control missing count | `test_control_missing_count_is_incomplete_never_zero` | PASS (`CONTROL_PROOF_INCOMPLETE`, `UNKNOWN`) |
| 8 | Binary SHA mismatch | `test_collector_sha_mismatches_are_flagged` | PASS (`HASH_MISMATCH`) |
| 9 | ELF SHA mismatch | same test | PASS (`HASH_MISMATCH`) |
| 10 | external timeout | `test_collector_external_timeout_is_flagged` | PASS (`TIMEOUT`, exit ≠ 0) |
| 11 | internal model watchdog | `test_collector_internal_watchdog_is_not_external_timeout` | PASS (not `TIMEOUT`) |
| 12 | Python child exception | `test_collector_child_exception_is_failed` | PASS (`FAILED`) |
| 13 | partial success | `test_collector_partial_campaign_reports_good_tasks_and_nonzero` | PASS (nonzero exit, good rows kept) |
| 14 | historical PRE_FORMAL root | `test_collector_historical_evidence_is_never_formal` | PASS (0 FORMAL) |
| 15 | formal run dir | collector test 1 / clean campaign | PASS (`EvidenceKind=FORMAL`) |
| 16 | 120-task uniqueness | `test_runner_120_tasks_unique_paired_and_non_colliding` + dry-run | PASS (120/120) |
| 17 | Fault/Control pairing | same + `test_rp01_control_command_carries_the_frozen_seed` | PASS (60/60 same seed) |
| 18 | output path non-collision | `test_runner_120_tasks_unique_paired_and_non_colliding` | PASS (0) |
| 19 | no duplicate launch | `test_runner_complete_pair_and_no_duplicate_launch` | PASS |
| 20 | missing file never PASS | scenario rows 3–7 | PASS |

## 3. Collector manual exit codes (fixture roots)

```console
campaign_clean  EXIT=0  statuses {"COMPLETED": 2, "ORACLE_FAIL": 2}
campaign        EXIT=1  statuses include OUTPUT_INCOMPLETE, HASH_MISMATCH, TIMEOUT, FAILED, FAIL, CONTROL_PROOF_INCOMPLETE
campaign_partial EXIT=1 (good rows kept; broken rows non-PASS)
historical_evidence EXIT=1 with 0 EvidenceKind=FORMAL
```

## 4. Isolation checks

```console
$ grep -c "audit_v3_3" tools/lsu_v333_launch.py
0
$ find tests/fixtures/lsu_v333_synthetic -name campaign_manifest.json -o -name '*.tmp'
(no output)
```

The collector reads only `--runs`; it does not write into campaign run dirs.

## 5. Verdict

`ALL SYNTHETIC TESTS PASS — 123 passed, 0 failed, 0 skipped.`
