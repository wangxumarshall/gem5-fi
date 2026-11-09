# Task 8 Report: Pilot-platform LQ04 wiring

Date: 2026-11-09
Branch: `lsu-platform-v3.2.10` (worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.10`)
Code commit: `1dbe2797` — `[LSU][MDSPEC][V3.2.10][LQ04] wire LQ04 into the pilot platform and terminal rules`
Docs commit: see `git log -1` after this report is committed.

## What was done

All nine known gaps from the task description were closed:

1. `run_pilot.EXCEL` moved from the v3.2.3 to the v3.2.4 workbook
   (`gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx`, verified to carry
   5 LQ04 rows R01–R05, ordinals 1–5, seeds from the frozen matrix).
2. Module-level `MODELS = ("A01","A03","FW02","SQ01","DA04","LP01","MD04",
   "FW05","SQ03","SP05","LQ04")` introduced and used as the `--model`
   argparse `choices` (previously a hard-coded list without LQ04).
3. `_workload_for("LQ04") == "lq_lifetime_ordinal"`.
4. LQ04 extra args for a fault run: `--chaos_lq04 --lq04_event_ordinal
   <Excel EventOrdinal> --lq04_max_faults 1 --lq04_watchdog_cycles
   500000000`. For `--probability 0.0` (matched control) the whole `extra`
   list is emptied — the LQ04 selector is ordinal-gated, not
   probability-gated, so a mounted injector would still fire;
   `--chaos_propagation` stays on (it is in the base command).
5. `_lq04_events(path)` parses `lq04_injections.log`:
   `CHAOS_LQ04_INJECTION` → `kind="injection"` (seq, pc, lq_idx, gen,
   request_id, addr, size, eligible, ordinal, injected, tick),
   `CHAOS_LQ04_ELIGIBLE_PROBE` → `kind="probe"`, `CHAOS_LQ04_RESTORE` →
   `kind="restore"`; `ELIGIBLE_COUNT` / `WATCHDOG_EXPIRED` are status
   lines, not events; missing file → `[]`.
6. `target_proof` for LQ04: `site="executeLoad_post"`, `all_one_injection`
   (len==1), `ordinal_matches` (log ordinal == Excel/used EventOrdinal),
   `valid_1_to_0=True`, `request_1_to_0=True`, `no_pop_no_reuse=True`,
   `address_size_data_unchanged=True` (by-construction facts of
   `LSQEntry::corruptLifetime`, which asserts the before-state; the
   request moves to the LQEntry side channel; address/size/data are never
   touched) plus the standard `events` count used by the `accepted` gate.
7. `"LQ04"` added to `terminal_rules.LOAD_SIDE`.
8. Completeness profiles for `("LQ04","MASKED")` (three alternatives:
   inj→memory_response→register_writeback→consumer_commit;
   inj→memory_response→register_writeback; inj→squash), `("LQ04","SQUASHED")`
   (inj→squash), `("LQ04","CRASH")` (inj→simulator_abort),
   `("LQ04","UNRESOLVED")` (inj), and `"LQ04": ("injection",)` in
   `DEFAULT_PROFILE`.
9. `platform/tools/prop_trace_to_v31.py`: the LQ04 injection row reuses the
   generic `inj` CSV kind, which `UNIT_MAP` binds to `("AGU","injection")`;
   a minimal conditional now maps `kind=="inj"` with `family=lq04` to
   `unit="LQ", sub_unit="executeLoad"`. Other models' `inj` rows keep AGU.

One addition beyond the nine listed gaps, following the SQ03/SP05
precedent: `CHAOS_LQ04_WATCHDOG_EXPIRED` was added to the `watchdog_hit`
detection so a watchdog abort is classified `HANG/SIMULATOR_ERROR` instead
of `CRASH`. Without it a stuck LQ04 run would be mislabelled; it changes no
other model's behavior (the marker string is LQ04-specific).

## TDD evidence

### RED (before wiring)

```
$ python3 -m pytest tests/test_lq04_platform.py -v
FAILED tests/test_lq04_platform.py::test_platform_wiring_constants - Attribut...
FAILED tests/test_lq04_platform.py::test_lq04_events_parses_injection_line - ...
FAILED tests/test_lq04_platform.py::test_lq04_events_probe_restore_and_status_lines
FAILED tests/test_lq04_platform.py::test_lq04_is_load_side_and_masked_when_committed
FAILED tests/test_lq04_platform.py::test_lq04_completeness_profiles - Asserti...
FAILED tests/test_lq04_platform.py::test_lq04_masked_chain_is_complete - Asse...
FAILED tests/test_lq04_platform.py::test_converter_binds_lq04_injection_to_the_lq_unit
========================= 7 failed, 1 passed in 0.47s ==========================
```

Concrete first failures: `AttributeError: module 'run_pilot' has no attribute
'MODELS'`, no `_lq04_events`, `"LQ04" not in LOAD_SIDE`,
`expected_stages("LQ04","MASKED") == [("injection",)]` (DEFAULT fallback),
and `assert 'AGU' == 'LQ'` in the converter test. The single pre-existing
pass is `test_lq04_squashed_when_no_commit` — squash adjudication precedes
the LOAD_SIDE branch, so it guards that path in both states.

### GREEN (after wiring)

```
$ python3 -m pytest tests/test_lq04_platform.py -v
tests/test_lq04_platform.py::test_platform_wiring_constants PASSED       [ 12%]
tests/test_lq04_platform.py::test_lq04_events_parses_injection_line PASSED [ 25%]
tests/test_lq04_platform.py::test_lq04_events_probe_restore_and_status_lines PASSED [ 37%]
tests/test_lq04_platform.py::test_lq04_is_load_side_and_masked_when_committed PASSED [ 50%]
tests/test_lq04_platform.py::test_lq04_squashed_when_no_commit PASSED    [ 62%]
tests/test_lq04_platform.py::test_lq04_completeness_profiles PASSED      [ 75%]
tests/test_lq04_platform.py::test_lq04_masked_chain_is_complete PASSED   [ 87%]
tests/test_lq04_platform.py::test_converter_binds_lq04_injection_to_the_lq_unit PASSED [100%]
============================== 8 passed in 0.32s ===============================
```

Test assets: fixture `tests/data_lq04_platform/lq04_injections.log` (one
injection line, ordinal=3, injected=1 — force-added because `.gitignore`
has `*.log`, same as existing tracked evidence logs) and a synthetic
Trace v3.1 JSONL built in-test via `TraceWriter` for the completeness
profile (chain injection→response→writeback→consumer→commit, hashes
consistent, validator clean).

### Unaffected-regression checks

```
$ python3 -m pytest tests/test_lsu_v324_workbook.py -q
.....                                                                    [100%]
5 passed in 1.55s

$ python3 -m pytest tests/ -q
FAILED tests/test_claim_concurrency.py::test_d_run_concurrency_cap - Assertio...
FAILED tests/test_claim_concurrency.py::test_e_heartbeat - AssertionError: e_...
2 failed, 48 passed in 10.93s
```

The only two failures are the known environmental disk-guard tests
(`磁盘 free 13.4 GiB < 红线 70.6 GiB (=max(50, 20%×353))` — same class as
the known "22.9 < 70.6 GiB"; the free-disk reading drifted during the
session). Everything else, including all pre-existing suites, is green.

## Platform smoke pilot (real gem5)

Command (from the task verification section):

```
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py --model LQ04 \
  --context-index 1 --preserve-sample-id --pilot-id LQ04-PLATFORM-SMOKE \
  --workload $PWD/docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal \
  --outdir /tmp/lq04_platform_smoke --timeout 900 --gem5 $PWD/build/ARM/gem5.opt
```

Observed (from `/tmp/lq04_platform_smoke/pilot_meta.json`, real run,
elapsed 2.034 s, gem5 exit 0):

- Classification: `run_status=COMPLETED`, `fault_activation_status=TRIGGERED`,
  `observed_terminal=MASKED` → **`terminal_state=MASKED`**,
  `terminal_state_reason=TARGET_COMMITTED_DATA_VALUE_PRESENT`,
  `fault_causality=DIRECT_DATAFLOW_EVIDENCE`, `accepted=true`.
- Oracle: expected `checksum=0xb097eb83f71545cb`
  (`workload_golden`), **PASS** — the same checksum appears in the
  workload's stdout; per the task constraint the oracle is the checksum
  line, not the gem5 exit code (which was 0 anyway).
- Exactly one injection, from `lq04_injections.log`:
  `CHAOS_LQ04_INJECTION: seq=3 pc=0x400338 lq_idx=1 gen=1 request_id=3
  addr=0x41ffe8 size=8 eligible=1 ordinal=1 injected=1 tick=80080`
  followed by `CHAOS_LQ04_RESTORE: seq=3 lq_idx=1 gen=1 reason=commit
  tick=136675` (boundary restore observed).
- `target_event_proof`: `events=1, all_one_injection=true,
  ordinal_matches=true, valid_1_to_0=true, request_1_to_0=true,
  no_pop_no_reuse=true, address_size_data_unchanged=true`.
- `trace_v31.jsonl` valid (`record_integrity=VALID`, no validator errors),
  `trace_completeness=COMPLETE`, `propagation_coverage=COMPLETE`,
  `missing_stages=[]`, chain scoped by `ptag=1` with 335 chain events,
  `chain_integrity=PASS`, `chain_reasons=[]`,
  `execution_attempt_link=SAME_ATTEMPT`; 17728 CSV rows, not truncated.
- The injection record in the JSONL carries **`unit=LQ`,
  `sub_unit=executeLoad`**, `ptag=1`, `dyn_inst_seq=3` (the converter
  mapping works on the real trace, not only the synthetic one).

This matches the task's expected outcome exactly (MASKED, oracle pass,
checksum `0xb097eb83f71545cb`, unit LQ); nothing had to be forced.

## Files changed (commit 1dbe2797)

- `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py` (modified)
- `docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py` (modified)
- `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_completeness.py` (modified)
- `docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py` (modified)
- `tests/test_lq04_platform.py` (new)
- `tests/data_lq04_platform/lq04_injections.log` (new fixture, `git add -f`)

Plus this report and the Task 8 plan checkboxes
(`docs/superpowers/plans/2026-11-08-lsu-v3.2.10-lq04.md`) in the follow-up
docs commit.

## Self-review

- Every claim above is backed by a command I actually ran in this session;
  pytest outputs and pilot numbers are copied from real output, not
  predicted.
- The matched-control path (`--probability 0.0`) is implemented and reasoned
  about, but not exercised against real gem5 in this task — that is Task
  10's five-controls deliverable. Code path: `extra = []` → no
  `CHAOSLQ04` SimObject → no `lq04_injections.log` → `injected=0` →
  `NOT_TRIGGERED`, and `adjudicate` returns `UNRESOLVED/NO_INJECTION_EVENT`,
  so a control is recorded but not accepted as a pilot (consistent with the
  other models' control convention).
- `str(sample.get("event_ordinal") or 1)` deviates cosmetically from the
  plan's literal `str(sample["event_ordinal"])`: it follows the defensive
  house pattern used by every other model branch and is behaviorally
  identical for the Excel rows (all LQ04 rows carry ordinal 1–5).
- The four `True` proof fields are by-construction facts (asserted by
  `corruptLifetime` / the injector's single code path), stated as such in a
  comment; they follow the existing DA04/LP01 `"..._only": True` precedent.
  The live corroboration lives elsewhere: the restore line
  (`reason=commit`) and the response_probe/`errant`/consumer nodes on the
  real trace.
- Other models untouched: the converter change is gated on
  `family=lq04` (only LQ04 emits that family on an `inj` row — verified in
  `CHAOSPropagation.cc noteLQ04Injection`); the test asserts a plain
  `addrpath` `inj` row still maps to AGU. `MODELS`/`EXCEL`/`LOAD_SIDE` are
  additive. Full-suite evidence above.

## Concerns

1. **No `("LQ04","SDC")` profile** — the task specified exactly four
   profiles. If a LQ04 pilot ever lands SDC (not expected: the injector
   never touches data), coverage falls back to `DEFAULT_PROFILE`
   `("injection",)`, which is permissive but not wrong. Task 11/12 can
   tighten this if the audit wants it.
2. **Watchdog units** — per the progress.md ruling, LQ04's watchdog is in
   cycles (not SQ03 ticks); the value 500000000 cycles came from the task
   specification itself. The smoke workload finishes at tick ≈ 1.4e5, far
   below the limit, so the watchdog never fired; the HANG mapping is
   therefore verified by code inspection and the SQ03/SP05 precedent, not
   by a live expiry.
3. **Disk headroom** — the host is at 13.4 GiB free (below the 70.6 GiB
   red line the guard enforces). This blocks the two claim-concurrency
   tests (known) and is worth watching before Task 9's builds and Task
   10's pilots write more data.
4. The Excel `WorkloadPath` for LQ04 rows still points at the legacy
   `lq_lifetime` binary; pilots override with `--workload
   lq_lifetime_ordinal` and the oracle comes from the workload golden
   (`oracle_source=workload_golden` recorded in the meta). Task 12's
   v3.2.5 transcription should update the rows to the frozen workload.
