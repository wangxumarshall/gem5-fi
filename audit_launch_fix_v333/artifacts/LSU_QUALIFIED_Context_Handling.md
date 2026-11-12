# LSU v3.3.3 — Qualified-Evidence Context Handling (A03 / SP05 / RP01)

**Owner:** Agent D · **Module:** `tools/lsu_v333_qualified.py` · **Tests:**
`tests/test_lsu_v333_qualified.py` · **Interface:** `audit_launch_fix_v333/README_INTERFACES.md`
**Baseline:** HEAD 58d77b34; source b5031bf7; binary 1126e0fd; config 8309da72.

## 1. Interface

```python
qualified_evidence(model: str, run_dir: Path) -> dict
```

Returned keys are exactly:

`model, required_fields, found, missing, status, terminal_rule, evidence`

- The function reads **only** `run_dir` (summary.json, oracle.log,
  `addrpath_injections.log`, `lsq_fwd_injections.log`, stdout/stderr,
  `trace_v31.jsonl`, `prop_trace.csv[.gz]`). It never reads
  `audit_v3_3_3/...`, `LSU_*_Matrix.csv` or any historical summary table.
- If a value cannot be derived from `run_dir`, it is left `None` and the field
  is listed in `missing`; it is **never** defaulted to `0`, `PASS` or `n/a`.
- Only A03/SP05/RP01 have extra rules. Every other model returns
  `status="PASS"`, `required_fields=[]`, `found=[]`, `missing=[]`,
  `terminal_rule="NO_EXTRA_RULES"`.

### Status precedence (evidence completeness, not oracle verdict)

| Precedence | Condition | Status |
|---|---|---|
| 1 | Trace/log evidence missing, truncated, or cut by a watchdog/timeout | `TRACE_INCOMPLETE` |
| 2 | Evidence readable and complete, but ≥1 required causal-chain field absent | `QUALIFIED` |
| 3 | All required fields found and the evidence source is complete | `PASS` |

`PASS` means *the causal chain is fully documented by this run dir*. It does
**not** mean the application oracle passed: an `ORACLE_FAIL`/SDC terminal is a
valid measured terminal and is reported by `terminal_rule`/`evidence`, not by
the status. A `QUALIFIED` or `TRACE_INCOMPLETE` state is never upgraded to
`PASS`.

Placeholder tokens (`null`, `None`, `n/a`, `unknown`, `?`, empty string) are
treated as **absent**, so a trace that writes `store_data_fnv=null` cannot
satisfy `store_data_hash`.

## 2. Exact rules per model

### A03 — persistent stuck-at address family

Required fields (`A03_FIELDS`, in order):

1. `persistent_stuck_lifecycle` — `A03_STUCK_LIFECYCLE` record
   (`summary.a03.lifecycle` or the log line).
2. `stuck_at_active` — the lifecycle proves the stuck state is active
   (`applications > 0` or at least one `STUCK_APPLIED` stream row).
3. `selected_event_first_activated` — `A03_ACTIVATION` record (tick/bit/mode).
4. `first_downstream_instruction_affected` — first `A03_STREAM` row with
   `affected=1` **and** `reason=STUCK_APPLIED`.
5. `first_affected_load_dyn_seq` — `dyn_inst_seq` of that row.
6. `first_affected_load_pc` — `pc` of that row.
7. `load_result` — `resp` node of the affected dyn seq in `prop_trace`
   (`data_hex`/`data_fnv`).
8. `register_writeback` — `taint_reg` node of the affected dyn seq
   (`arch_reg`/`phys_reg`/`writeback_value_fnv`).
9. `consumer` — a `consumer` node linked through the `prop_edge` whose
   `source_event_id` is that `taint_reg` node.
10. `application_checksum` — 16-hex checksum from `summary.json`/`stdout.log`.
11. `internal_watchdog_reason` — `A03_WATCHDOG_EXPIRED` line or the
    `watchdog_expired` summary flag.

**Three-event rule.** `stuck_at_active`, `selected_event_first_activated` and
`first_downstream_instruction_affected` are three *different* records. A run
that has only the activation/lifecycle but no genuinely applied downstream
stream row is never `PASS` (missing `first_downstream_instruction_affected`).
The summary's `first_affected` string is accepted only when it really says
`affected=1;reason=STUCK_APPLIED`; otherwise the first such log row is used.

**Terminal rule.** `APPLICATION_CHECKSUM` is the terminal witness, compared
with `oracle.log expected=`. Qualifiers: `ORACLE_FAIL_SDC` / `ORACLE_PASS`;
`POST_ORACLE_INTERNAL_WATCHDOG` when `A03_WATCHDOG_EXPIRED` fired after the
checksum. The internal watchdog alone (`INTERNAL_WATCHDOG_NO_CHECKSUM`) is not
an application terminal.

### SP05 — store premature-completion / lost writeback

Required fields (`SP05_FIELDS`, in order):

1. `store_dyn_seq` — target store `store_seq`.
2. `store_pc` — target `store_pc`.
3. `sq_entry` — `sq_entry_id` + `sq_entry_generation`.
4. `store_address` — `store_addr`.
5. `store_data_hash` — `store_data_fnv` (a literal `null` does not count).
6. `commit_event` — an **independent** commit observation:
   a `store_commit`/`commit` record for the target, or
   `sp05_stage` with `commit_observed=1`. A `commit_tick` whose
   `commit_tick_source` is `caller_supplied` is the injection call, not a
   commit event, and is rejected.
7. `writeback_event` — a `store_writeback`/`writeback`/`memory_write` record,
   or `sp05_stage writeback_observed=1`, or post-completion
   `stores_to_wb_after>0` with `mem_sent=1`. `sp05_write_skipped`
   (`write_skipped=1`) proves the writeback did **not** happen and therefore
   does not satisfy this field.
8. `memory_visibility` — `mem_sent`/`write_skipped`/`store_not_written_yet`
   observation.
9. `reload` — `sp05_stage reload_seq`/`reload_data_hash` (or the reload
   request/response chain).
10. `consumer` — `consumer_commit` record.
11. `golden_memory_value` — `oracle.log expected=` and/or the golden
    `store_data_hex`.
12. `application_oracle` — `ORACLE_PASS`/`ORACLE_FAIL` or `expected=/got=`.

**Terminal rule.** The application oracle is the terminal
(`APPLICATION_ORACLE` + `ORACLE_PASS`/`ORACLE_FAIL_SDC`). A missing commit or
writeback event does not change the measured oracle terminal; it qualifies the
chain with `STORE_COMMIT_ABSENT`/`STORE_WRITEBACK_ABSENT` and forces
`QUALIFIED`, never `PASS`.

### RP01 — replay suppression

Required fields (`RP01_FIELDS`, in order):

1. `replay_eligibility` — `RP01_ELIGIBLE` / first eligible replay record.
2. `replay_decision` — skip record with `replay_gen_pre/post` (or
   `skipped_call`).
3. `faulty_replay_state` — the skip target's
   `replay_gen_pre/post` + `in_instsToReplay_pre/post` transition
   (replay generation advanced but no instruction enqueued).
4. `replay_skip` — `RP01_SKIP_REPLAY` / `skipped_call=1`.
5. `dyn_seq` — target `load_seq`.
6. `lq_sq_entry` — LQ entry (`lq_idx`, `lq_gen`) of the skipped load, plus the
   paired `store_seq`.
7. `internal_watchdog` — `rp01.watchdog` / `CHAOS_RP01_WATCHDOG=EXPIRED`.
8. `external_timeout` — `summary.timed_out` (present with either value).
9. `final_progress_state` — terminal / terminal_reason.

**Terminal rule** (`terminal_rule`):

- `MODEL_INTERNAL_WATCHDOG` — the in-model watchdog fired;
- `EXTERNAL_TIMEOUT` — the runner timed the run out;
- `NORMAL` — neither.

A watchdog/timeout cut leaves a **partial** trace. The run is then
`TRACE_INCOMPLETE` even when all nine fields are present; it is never `PASS`,
because a partial trace is not a complete causal chain.

## 3. Current 15 pre-formal contexts (NON_FORMAL)

These are the historical `audit_v3_3_3/runs/<Model>-R0x-fault` directories,
i.e. **NON_FORMAL** evidence under the collector's isolation rule. They are
listed here only to show today's state; the formal campaign must re-collect
under its own `--runs CampaignRoot`.

| Model | Ctx | Status | Missing required fields | terminal_rule |
|---|---|---|---|---|
| A03 | R01 | `PASS` | — | `APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG` |
| A03 | R02 | `QUALIFIED` | `load_result`, `register_writeback`, `consumer` | `APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG` |
| A03 | R03 | `PASS` | — | `APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG` |
| A03 | R04 | `PASS` | — | `APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG` |
| A03 | R05 | `PASS` | — | `APPLICATION_CHECKSUM;ORACLE_FAIL_SDC;POST_ORACLE_INTERNAL_WATCHDOG` |
| SP05 | R01 | `QUALIFIED` | `commit_event`, `writeback_event` | `APPLICATION_ORACLE;ORACLE_FAIL_SDC;STORE_COMMIT_ABSENT;STORE_WRITEBACK_ABSENT` |
| SP05 | R02 | `QUALIFIED` | `commit_event`, `writeback_event` | same |
| SP05 | R03 | `QUALIFIED` | `commit_event`, `writeback_event` | same |
| SP05 | R04 | `QUALIFIED` | `commit_event`, `writeback_event` | same |
| SP05 | R05 | `QUALIFIED` | `commit_event`, `writeback_event` | same |
| RP01 | R01 | `TRACE_INCOMPLETE` | — (all 9 fields found) | `MODEL_INTERNAL_WATCHDOG` |
| RP01 | R02 | `TRACE_INCOMPLETE` | — | `MODEL_INTERNAL_WATCHDOG` |
| RP01 | R03 | `TRACE_INCOMPLETE` | — | `MODEL_INTERNAL_WATCHDOG` |
| RP01 | R04 | `TRACE_INCOMPLETE` | — | `MODEL_INTERNAL_WATCHDOG` |
| RP01 | R05 | `TRACE_INCOMPLETE` | — | `MODEL_INTERNAL_WATCHDOG` |

Observed detail behind the non-PASS rows:

- **A03 R02** — the first `STUCK_APPLIED` load (dyn seq 13718) is squashed
  before any response (`squash_cause=unrelated`); there is no `resp`/`taint_reg`/
  `consumer` node for it, so the downstream chain is honestly incomplete.
- **A03 R01/R03/R04/R05** — the first affected load has `resp`, `taint_reg`,
  a `register_dataflow` edge and a linked `consumer`; the checksum differs from
  the golden value (SDC) and the internal watchdog fires *after* the checksum.
  `PASS` here is chain completeness; the measured terminal is `ORACLE_FAIL/SDC`.
- **SP05 R01–R05** — the trace is `COMPLETE`/`VALID` and `store_data_fnv` is
  present, but the only commit timestamp is `commit_tick_source=caller_supplied`
  (`commit_status=UNKNOWN`) and `sp05_write_skipped` records `write_skipped=1`,
  i.e. the writeback never happened. There is no independent commit event and no
  writeback event, hence `QUALIFIED`.
- **RP01 R01–R05** — all nine fields are present, but the run ends in the
  in-model watchdog and `prop_trace.csv.gz` is gzip-truncated
  (`unexpected end of file`), so the trace is partial and the status is
  `TRACE_INCOMPLETE`. The terminal classification is
  `MODEL_INTERNAL_WATCHDOG`, not `EXTERNAL_TIMEOUT` (`timed_out=false`).

**No QUALIFIED/TRACE_INCOMPLETE row above is upgraded to PASS.**

## 4. What the formal run must collect

### A03
- `summary.json.a03` with `lifecycle`, `first_activation`, `first_affected`,
  `watchdog_expired`;
- `addrpath_injections.log` (or equivalent) containing
  `A03_STUCK_LIFECYCLE`, `A03_ACTIVATION` and the first `A03_STREAM`
  `affected=1;reason=STUCK_APPLIED` row;
- a **complete** `prop_trace` containing, for the first affected dyn seq,
  `resp` + `taint_reg` + `prop_edge` + `consumer`;
- `oracle.log` with `expected=<golden> got=<checksum>`;
- `stdout.log` with the 16-hex checksum and `A03_WATCHDOG_EXPIRED`.

A context whose first affected load is squashed before writeback stays
`QUALIFIED`; selecting a non-squashed first affected load is a context-design
decision, not a collector default.

### SP05
- `summary.json.first_injection.detail` with `store_seq`, `store_pc`,
  `store_addr`, `sq_entry_id`/`sq_entry_generation`, `store_data_fnv`;
- `trace_v31.jsonl` with `injection`, `sp05_stage`, `memory_request`,
  `memory_response`, `register_writeback`, `consumer_commit`;
- **new**: an independent `store_commit` event and an independent
  `store_writeback`/memory-write event for the target store (see §5);
- `oracle.log` with `expected=/got=`;
- `trace_completeness` declared `COMPLETE` and `record_integrity=VALID`.

### RP01
- `summary.rp01` with `first_eligible`, `first_skip`, `watchdog`,
  `watchdog_marker`; `summary.timed_out`; `terminal`/`terminal_reason`;
- `lsq_fwd_injections.log` with the eligible record, the skip decision and the
  watchdog marker;
- a `prop_trace` that is complete/readable. If the run legitimately ends in the
  in-model watchdog, the trace must be flushed/snapshotted before exit for the
  chain to become `PASS`; today it is truncated and therefore
  `TRACE_INCOMPLETE`.

## 5. Fields that would require a new C++ hook (for researcher approval)

These are **reported only**; no C++/collector/runner change was made.

1. **SP05 independent store-commit event.** The trace has no store-commit node;
   `commit_tick` is caller-supplied (`commit_tick_source=caller_supplied`) and
   `commit_status=UNKNOWN`. A `commitStores` observer would produce a genuine
   `store_commit` node. Until then `commit_event` stays missing.
2. **SP05 independent store-writeback / memory-write event.** The trace can
   prove the writeback was **skipped** (`sp05_write_skipped`,
   `write_skipped=1`, `mem_sent=0`) but has no writeback/memory-write node. A
   drain/writeback observation hook would make `writeback_event` collectable
   for a non-skipped store. Until then `writeback_event` stays missing.
3. **RP01 trace flush at the in-model watchdog.** The watchdog exits through
   `m5_fail`, leaving `prop_trace.csv.gz` truncated. A snapshot/flush before the
   watchdog exit (or runner-side extraction before exit) is needed for a
   complete RP01 causal chain.
4. **RP01 paired-store SQ entry (only if required).** RP01 records the skipped
   load's LQ entry (`lq_idx`/`lq_gen`) and the paired `store_seq`, but not the
   paired store's SQ entry index. The current module accepts the LQ entry for
   `lq_sq_entry`; if the researcher requires the SQ entry too, a small
   observation hook is needed.
5. **A03 (no new hook strictly required).** All required fields are derivable
   from the existing `prop_trace` (`resp`/`taint_reg`/`prop_edge`/`consumer`)
   cross-linked by dyn seq. Optionally, making the `A03_STREAM` record
   self-contained (load result, writeback, consumer) would remove the need for
   cross-linking, but it is not required for `PASS` under this module.

## 6. Verification (real commands)

```
$ python3 -m py_compile tools/lsu_v333_qualified.py tests/test_lsu_v333_qualified.py; echo "py_compile exit=$?"
py_compile exit=0

$ python3 -m pytest tests/test_lsu_v333_qualified.py -v
... (23 tests) ...
============================== 23 passed in 0.09s ==============================
```

The 15-context table above was produced by calling
`qualified_evidence(model, Path("audit_v3_3_3/runs/<Model>-R0x-fault"))` for
each context; the module read only those run dirs.
