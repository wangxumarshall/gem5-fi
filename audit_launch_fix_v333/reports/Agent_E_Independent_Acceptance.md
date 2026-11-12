# Agent E — Synthetic fixtures + independent integration acceptance

**Round:** LSU v3.3.3 launch-critical fix (baseline HEAD `58d77b34`).
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`.
**Nature:** synthetic only. No gem5/scons process was started; no historical run
evidence is read by any assertion. Every fixture file is a few hundred bytes.

Module versions observed by the final run (concurrent agents were still
editing; these timestamps pin the evidence):

| file | mtime | note |
|---|---|---|
| `tools/lsu_v332_matrix.py` | 2026-11-12 16:24 | Agent A, after the control-path fix |
| `tools/lsu_v333_control_proof.py` | 2026-11-12 16:17 | Agent C |
| `tools/lsu_v333_qualified.py` | 2026-11-12 16:13 | Agent D |
| `tools/lsu_v333_launch.py` | 2026-11-12 15:08 | **legacy CLI**, no `--campaign-id` / `--design-matrix` / `--design-mapping` (Agent B pending) |

---

## 1. Fixture layout

Everything lives under `tests/fixtures/lsu_v333_synthetic/` and is regenerated
deterministically by `build_fixtures.py` (gzip `mtime=0`, sorted JSON keys):

```
payload/                      tiny fake gem5.opt / lsu_proxy.py / workload ELFs
design/                       synthetic --design-matrix / --design-mapping CSVs
                              (SYNTH_*, CLEAN_*, PARTIAL_*, HISTORICAL_*)
campaign/                     12 fault/control pairs, one defect per scenario
campaign_clean/               all-good positive control (A01-R01, SP05-R01)
campaign_partial/             partial success: 2 good + 2 broken (A01-R01/R02)
historical_evidence/          campaign_id SYNTH-V332-PRE-FORMAL (never FORMAL)
README.md                     generated scenario table
```

Each run dir contains `campaign.json` (the 14 README fields), `summary.json`
(absent for the missing-summary scenario), `pilot_meta.json`, `trace_v31.jsonl`,
`prop_trace.csv.gz`, `command.txt`, `stdout.log`, `stderr.log`, `oracle.log`,
plus the model log or watchdog markers where relevant. Identity values
(`SampleRunID`, seeds, ROI ordinals) are copied from the frozen design.

Scenario map (`campaign/` unless noted):

| scenario | run dir | injected defect |
|---|---|---|
| complete fault | `A01-R01-fault` | none; SDC/ORACLE_FAIL, count 1 |
| complete control | `A01-R01-control` | none; mounted + `--probability 0.0`, count 0 |
| missing summary | `A01-R02-fault` | no `summary.json` (campaign says OUTPUT_INCOMPLETE) |
| missing fault trace | `A01-R03-fault` | no `trace_v31.jsonl`; summary still **claims** COMPLETE |
| missing control trace | `A01-R03-control` | no `trace_v31.jsonl` |
| control applied > 0 | `A01-R04-control` | summary/pilot_meta counts 1 despite disabled mount |
| control missing count | `A01-R05-control` | no counts in summary, pilot_meta or trace |
| binary SHA mismatch | `A03-R01-fault` | `binary_sha = deadbeef...` |
| ELF SHA mismatch | `A03-R02-fault` | `elf_sha = feedface...` |
| external timeout | `A03-R03-fault` | `status TIMEOUT`, exit 124, no checksum |
| internal RP01 watchdog | `RP01-R01-fault` | `CHAOS_RP01_WATCHDOG=EXPIRED`, HANG_WATCHDOG |
| internal A03 watchdog | `A03-R04-fault` | `A03_WATCHDOG_EXPIRED`, HANG_WATCHDOG |
| Python child exception | `FW02-R01-fault` | `status FAILED`, exit 1, Traceback |
| formal campaign_id | `SP05-R01-fault` | complete + matching `SYNTH-V333-FORMAL` |
| historical PRE_FORMAL | `historical_evidence/A01-R01-*` | complete files, non-matching campaign_id |
| partial success | `campaign_partial/*` | 2 good + missing-summary + timeout |

Runner-only scenarios are produced in `tmp_path` by monkeypatching the single
public execution seam `mx.run_subprocess` (no subprocess is spawned) and a
preflight stub that keeps the real run-dir collision rule.

---

## 2. Exact test output (final run)

```
$ python3 -m pytest tests/test_lsu_v333_synthetic.py -v -p no:cacheprovider
...
tests/test_lsu_v333_synthetic.py::test_fixture_scenario_dirs_exist PASSED
tests/test_lsu_v333_synthetic.py::test_fixture_files_are_tiny PASSED
tests/test_lsu_v333_synthetic.py::test_fixture_missing_files_are_really_missing PASSED
tests/test_lsu_v333_synthetic.py::test_fixture_campaign_json_matches_campaign_ids PASSED
tests/test_lsu_v333_synthetic.py::test_fixture_gzip_trace_is_valid PASSED
tests/test_lsu_v333_synthetic.py::test_fixture_design_matrix_matches_campaign_pairs PASSED
tests/test_lsu_v333_synthetic.py::test_builder_regenerates_identical_fixtures PASSED
tests/test_lsu_v333_synthetic.py::test_runner_120_tasks_unique_paired_and_non_colliding PASSED
tests/test_lsu_v333_synthetic.py::test_runner_control_status_mapping_is_defined PASSED
tests/test_lsu_v333_synthetic.py::test_runner_complete_pair_and_no_duplicate_launch PASSED
tests/test_lsu_v333_synthetic.py::test_runner_external_timeout_is_timed_out_not_pass PASSED
tests/test_lsu_v333_synthetic.py::test_runner_internal_watchdogs_are_not_external_timeouts PASSED
tests/test_lsu_v333_synthetic.py::test_runner_child_exception_recorded_and_partial_campaign_continues PASSED
tests/test_lsu_v333_synthetic.py::test_control_complete_zero_applied_passes PASSED
tests/test_lsu_v333_synthetic.py::test_control_applied_greater_than_zero_fails PASSED
tests/test_lsu_v333_synthetic.py::test_control_missing_count_is_incomplete_never_zero PASSED
tests/test_lsu_v333_synthetic.py::test_control_missing_summary_is_incomplete PASSED
tests/test_lsu_v333_synthetic.py::test_control_missing_trace_is_incomplete PASSED
tests/test_lsu_v333_synthetic.py::test_control_injector_absent_is_a_pass PASSED
tests/test_lsu_v333_synthetic.py::test_qualified_a01_complete_has_no_extra_rules PASSED
tests/test_lsu_v333_synthetic.py::test_qualified_missing_trace_is_not_pass PASSED
tests/test_lsu_v333_synthetic.py::test_qualified_watchdog_terminal_is_never_a_timeout PASSED
tests/test_lsu_v333_synthetic.py::test_qualified_truncated_trace_is_never_upgraded PASSED
tests/test_lsu_v333_synthetic.py::test_qualified_never_reports_pass_with_missing_fields PASSED
tests/test_lsu_v333_synthetic.py::test_collector_* ... SKIPPED (12 tests)
======================== 24 passed, 12 skipped in 0.50s ========================
EXIT=0
```

Cross-check of the other agents' own suites (read-only, for context):

```
$ python3 -m pytest tests/test_lsu_v333_runner_errors.py -q
32 passed in 1.89s
$ python3 -m pytest tests/test_lsu_v333_control_proof.py tests/test_lsu_v333_qualified.py -q
41 passed in 12.19s
```

---

## 3. Scenario table

| # | Scenario | Exercised through | Result |
|---|---|---|---|
| 1 | complete Fault run | runner (fake child), qualified, collector | **PASS** (runner/qualified); collector **PENDING (Agent B)** |
| 2 | complete Control run | runner (fake child), control, collector | **PASS** (runner/control); collector **PENDING (Agent B)** |
| 3 | missing summary.json | collector (+fixture assert) | fixture **PASS**; collector **PENDING** |
| 4 | missing Fault trace | qualified A03 variant, collector | qualified **PASS**; collector **PENDING** |
| 5 | missing Control trace | control, collector | control **PASS**; collector **PENDING** |
| 6 | Control applied > 0 | control, collector | control **PASS** (`FAIL`, applied 1); collector **PENDING** |
| 7 | Control missing count | control | **PASS** (`CONTROL_PROOF_INCOMPLETE`, `UNKNOWN`, never 0) |
| 8 | Binary SHA mismatch | collector | **PENDING (Agent B)** |
| 9 | ELF SHA mismatch | collector | **PENDING (Agent B)** |
| 10 | external timeout | runner A03/RP01, collector | runner **PASS** (`TIMEOUT`, external source); collector **PENDING** |
| 11 | internal RP01 watchdog | runner, qualified, collector | runner **PASS** (`HANG_WATCHDOG`, MODEL_INTERNAL_WATCHDOG); qualified **PASS** (watchdog rule / TRACE_INCOMPLETE); collector **PENDING** |
| 12 | internal A03 watchdog | runner, qualified, collector | runner **PASS**; qualified **PASS**; collector **PENDING** |
| 13 | Python child exception | runner `main` (partial), collector | runner **PASS** (`FAILED` + parse_error in campaign.json); collector **PENDING** |
| 14 | partial success | collector | **PENDING (Agent B)** |
| 15 | historical PRE_FORMAL never FORMAL | collector | **PENDING (Agent B)** |
| 16 | formal run with matching campaign_id | collector | **PENDING (Agent B)** |
| 17 | 120-task uniqueness | runner | **PASS** (120 unique outdirs) |
| 18 | fault/control pairing | runner | **PASS** (frozen seed shared; see finding F-E4) |
| 19 | output path non-collision | runner | **PASS** |
| 20 | no duplicate task launch | runner | **PASS** (second launch refused at preflight, child count unchanged) |
| 21 | missing file != PASS | control now, collector later | control **PASS**; collector **PENDING** |

### Pending B-dependent tests (will run automatically once Agent B lands)

All 12 skips are `tools/lsu_v333_launch.py` CLI-interface skips with an explicit
reason:

```
PENDING (Agent B): tools/lsu_v333_launch.py does not yet expose
['--campaign-id', '--design-matrix', '--design-mapping']; collector interface
is per README_INTERFACES.md
```

Tests: complete pair → FORMAL; clean campaign exit 0; missing summary / missing
fault trace / missing control trace never PASS; control-proof defects; binary &
ELF SHA mismatch flagged; external timeout; internal watchdog not external
timeout; child exception FAILED; partial campaign nonzero with good records;
historical evidence never FORMAL.

---

## 4. Independent acceptance findings (not a rubber stamp)

### F-E1 — LAUNCH-CRITICAL, caught then fixed during this round

`tools/lsu_v332_matrix.py:446` evaluated, for **every control task**:

```python
if exit_code == 0 and terminal in ("UNRESOLVED",) | MODEL_TERMINALS:
```

`tuple | frozenset` raises `TypeError: unsupported operand type(s) for |:
'tuple' and 'frozenset'`, so `measured_status()` crashed for every CONTROL run
and `main` recorded it as `FAILED`. Raw evidence from the earlier run:

```
tools/lsu_v332_matrix.py:446: TypeError
E       TypeError: unsupported operand type(s) for |: 'tuple' and 'frozenset'
FAILED tests/test_lsu_v333_synthetic.py::test_runner_control_status_mapping_is_defined
FAILED tests/test_lsu_v333_synthetic.py::test_runner_complete_pair_and_no_duplicate_launch
```

Agent A fixed it at 16:24 (`control_ok = frozenset({"UNRESOLVED"}) |
MODEL_TERMINALS`); both tests now pass. Agent A's own 32 tests did not cover
`measured_status(role="control", ...)` before this synthetic test did.

### F-E2 — failure evidence is not duplicated into summary.json / RAW CSV

For an internal execution failure (e.g. `OSError` from the child), the runner
records `parse_error` in `campaign.json` (good) and sets `status=FAILED` in
`summary.json`, but `summary.json` **does not contain** `parse_error`, and
`write_csv()` has no `parse_error`/`error` column for in-process parse errors
(raw path: `tools/lsu_v332_matrix.py`, `run_context` final `summary.update(...)`
and `write_csv` keys). The evidence is not lost (campaign.json carries it), but
the per-run summary and the RAW CSV are weaker than the campaign record. The
test asserts the campaign record; recommend adding `parse_error` to the summary
and the RAW CSV.

### F-E3 — a missing summary can still yield a corroborated zero count

`classify_control_run()` on a control with `summary.json` removed returns
`status=CONTROL_PROOF_INCOMPLETE` (correct) but `injection_applied_count=0`
because the `trace_v31.jsonl` summary record carries `counts.injections=0`.
This is a corroborated zero, not a silent default, and the evidence list says
so (`applied candidates: ... trace_v31.jsonl:counts.injections=0`). The frozen
sentence "Missing summary/count => INCOMPLETE (never 0/PASS)" can be read as
demanding `UNKNOWN` there; the test therefore fails only a *silent* zero
(no trace corroboration), not this corroborated value. Flagged for the main
agent to confirm the intended reading.

### F-E4 — RP01 control command carries no seed flag (pairing is by identity only)

`build_rp01_cmd(role="control", ...)` omits `--rng_seed`; only the fault command
carries it. Fault/control pairing is still structurally guaranteed because
`run_context` takes `(sample_run_id, seed)` from the same `FROZEN_ID[(model,
ctx)]` entry and both are written to `campaign.json`/`summary.json`. The
planned-command test asserts the frozen seed for the fault and only accepts the
frozen seed or absence for the control. If command-level pairing evidence is a
requirement, pass `--rng_seed` on the RP01 control too (cosmetic / evidence
strength, not a correctness failure).

### F-E5 — qualified A01 is always PASS by interface

Per README, only A03/SP05/RP01 carry extra rules; `qualified_evidence("A01", …)`
returns `PASS` with `required_fields=[]` even when the run's trace is missing.
That is the documented contract (trace completeness for non-qualified models is
the collector's job), so the missing-trace test uses an A03 clone (removing
`prop_trace.csv.gz`), which correctly returns `TRACE_INCOMPLETE`.

### F-E6 — collector interface still pending

`tools/lsu_v333_launch.py` at 15:08 is still the pre-round artifact generator
(0 occurrences of `--campaign-id`). No conclusion can be drawn about the
EvidenceKind/isolation/SHA/timeout behaviour until Agent B's rewrite lands; the
12 tests will execute automatically then. No PASS is claimed for those
scenarios.

---

## 5. Files produced by Agent E

* `tests/fixtures/lsu_v333_synthetic/build_fixtures.py` (generator)
* `tests/fixtures/lsu_v333_synthetic/{payload,design,campaign,campaign_clean,campaign_partial,historical_evidence}/` (321 tiny files, ~1.4 MB on disk incl. block overhead; no file > 8.5 KB except the generator and design CSV)
* `tests/fixtures/lsu_v333_synthetic/README.md` (generated scenario table)
* `tests/test_lsu_v333_synthetic.py`
* `audit_launch_fix_v333/reports/Agent_E_Independent_Acceptance.md` (this file)

No runner, collector, control, qualified or data file was edited by Agent E.
