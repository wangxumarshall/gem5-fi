# LSU v3.3.3 — Runner Error-Handling Audit

**Files:** `tools/lsu_v332_matrix.py`,
`docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`
**Tests:** `tests/test_lsu_v333_runner_errors.py` — 40 passed.

## 1. Preflight (before any gem5 process)

`preflight_task()` rejects and records, without launching gem5:

| Condition | Status |
|---|---|
| binary / config / ELF missing | `FAILED` (`missing=[...]`) |
| seed or SampleRunID missing | `FAILED` |
| non-empty output directory (collision) | `FAILED` (`outdir_unique=COLLISION`) |
| binary/config/ELF SHA ≠ frozen expected | `HASH_MISMATCH` |

A preflight failure writes `campaign.json` only into a directory the task owns
(and never deletes an existing run dir).

## 2. Execution

`run_subprocess()` records start time, PID, timeout, stdout and stderr, and on
timeout kills the **process group** (`os.killpg(SIGKILL)`), then records the
real exit code and `timed_out=True`. No timeout can be recorded as `COMPLETED`.

## 3. Terminal-source separation

`terminal_source()` never conflates the three timeout classes:

| Source | Condition |
|---|---|
| `PYTHON_TIMEOUT` | this driver's subprocess timeout |
| `EXTERNAL_TIMEOUT` | inner runner exit 124 / “external wall-clock limit”, which wins over a watchdog marker written before the kill |
| `MODEL_INTERNAL_WATCHDOG` | `A03_WATCHDOG_EXPIRED`, `CHAOS_RP01_WATCHDOG*` |
| `NORMAL` | otherwise |

## 4. Per-task status and campaign exit

`measured_status()` returns one of `COMPLETED, FAILED, TIMEOUT,
OUTPUT_INCOMPLETE, HASH_MISMATCH, ORACLE_FAIL`. `ORACLE_FAIL` is a measured
SDC terminal; it does not force a nonzero exit. Every other failure status
does. `campaign_exit_code()` returns 0 only when every scheduled row is
`COMPLETED` or `ORACLE_FAIL`.

Output validation requires `summary.json`, `trace_v31.jsonl`, `oracle.log`, and
the fault model log; A03/RP01 may use the documented watchdog partial set.
A result-parsing exception is `FAILED`, never a silent pass.

## 5. Defects found and fixed this round

| ID | Defect | Fix |
|---|---|---|
| F-E1 | `tuple | frozenset` TypeError crashed `measured_status()` for every control | `control_ok = frozenset({"UNRESOLVED"}) | MODEL_TERMINALS` |
| F-E2 | parse errors reached `campaign.json` but not `summary.json` / RAW CSV | `parse_error` added to the final summary and the CSV header |
| F-E4 | RP01 control command omitted the frozen seed | `--rng_seed` emitted for both roles |
| — | collector had no campaign-root identity record | `write_campaign_identity()` writes `campaign_identity.json` before the first task |

## 6. Evidence

```console
$ python3 -m pytest tests/test_lsu_v333_runner_errors.py -q -p no:cacheprovider
40 passed in 4.00s
$ python3 tools/lsu_v332_matrix.py --dry-run --out-base /tmp/lsu_v333_dryrun_t6
dry-run: 120 commands; no run dirs written
```

No gem5 rebuild and no pre-formal re-execution were performed.
