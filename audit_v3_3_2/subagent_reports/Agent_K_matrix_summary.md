# Agent K — v3.3.2 60-Context Fault/Control Matrix (SP05, DA04, LP01, MD04, LQ04, RP01)

Date: 2026-11-11
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
Binary: `build/ARM/gem5.opt`, SHA256 `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca`
Driver: committed `tools/lsu_v332_matrix.py`
Requested CSV: `audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final_K.csv`
Runs: `audit_v3_3_2/runs/<MODEL>-R<ctx>-<role>/`

## 1. Execution

Command run (as specified):

```
python3 tools/lsu_v332_matrix.py --models SP05,DA04,LP01,MD04,LQ04,RP01 \
  --roles fault,control --contexts 1,2,3,4,5 \
  --out-csv audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final_K.csv
```

- Driver exited 0 and printed `wrote ... (60 rows)`.
- 6 models x 5 contexts x 2 roles = 60 runs, sequential (one gem5 process at a time
  inside this driver). Wall time ~24 min (22:12-22:36).
- All 60 `summary.json` files exist. 30 fault runs, 30 control runs.

## 2. Results (real observed values)

`terminal` for non-RP01 runs is from `pilot_meta.json -> classification.terminal_state`
(the driver's own `summary.json -> terminal` is null for pilot-path runs; see anomaly C).
Controls have no injection, so `terminal_state = UNRESOLVED` and
`fault_activation_status = NOT_TRIGGERED` by construction; their oracle (golden
program output) passes.

| Model | Ctx | Role | Inj | Terminal | Oracle |
|---|---|---|---|---|---|
| SP05 | R01-R05 | fault | 1 | SDC | False |
| SP05 | R01-R05 | control | 0 | UNRESOLVED | True |
| DA04 | R01-R05 | fault | 1 | SDC | False |
| DA04 | R01-R05 | control | 0 | UNRESOLVED | True |
| LP01 | R01-R05 | fault | 1 | SDC | False |
| LP01 | R01-R05 | control | 0 | UNRESOLVED | True |
| MD04 | R01 | fault | 1 | MASKED | True |
| MD04 | R02-R05 | fault | 1 | SDC | False |
| MD04 | R01-R05 | control | 0 | UNRESOLVED | True |
| LQ04 | R01-R05 | fault | 1 | MASKED | True |
| LQ04 | R01-R05 | control | 0 | UNRESOLVED | True |
| RP01 | R01-R05 | fault | 1 (SKIP_REPLAY) | HANG | False (no terminal checksum) |
| RP01 | R01-R05 | control | 0 | COMPLETED | True (checksum f3b1c554273d23f7) |

All completed non-RP01 fault runs have `run_status = COMPLETED`,
`fault_activation_status = TRIGGERED`, trace completeness `COMPLETE`.

## 3. First injection identity (from `pilot_meta.json` injection event / parsed log)

- **SP05** (SP05 complete-store hook; hook logs SQ identity, no PC/VA):
  R01 store_seq=13328 sq_idx=956 ordinal=952; R02 15122/982/978;
  R03 16847/1007/1003; R04 18641/1033/1029; R05 20435/1059/1055.
- **DA04** (LSQFwd byte-enable clear; no PC/VA logged):
  R01 seq=14320 sq_idx=1563 addr=0x491b29 old_be=15->14 bit0;
  R02 15345/1768/0x491e5d; R03 16365/1972/0x49218d;
  R04 17390/2177/0x4924c1; R05 18415/2382/0x4927f5. (All: BE 0xF -> 0xE.)
- **LP01** (L1D forward load; full PC/VA/PA):
  Pc=0x400588 for all five.
  R01 va=0x491f0f pa=0x76f0f seq=34741 lq_entry=2407 ord=2549;
  R02 va=0x492c0f pa=0x77c0f seq=54709 lq=5735 ord=5877;
  R03 va=0x49390f pa=0x7890f seq=74677 lq=9063 ord=9205;
  R04 va=0x49460f pa=0x7960f seq=94645 lq=12391 ord=12533;
  R05 va=0x49530f pa=0x7a30f seq=114613 lq=15719 ord=15861.
- **MD04** (store->load violation window; addr + load/store seq):
  R01 addr=0x491990 load=125104 store=125103 lq=750 ord=3;
  R02 addr=0x494990 load=141725 store=141724 lq=3822 ord=5;
  R03 addr=0x4929c8 load=147152 store=147151 lq=4839 ord=6;
  R04 addr=0x4939e8 load=171530 store=171529 lq=9951 ord=8;
  R05 addr=0x491990 load=188215 store=188213 lq=14038 ord=10.
- **LQ04** (recovered run, see anomaly B):
  R01 pc=0x400338 addr=0x41ffe8 seq=3 lq_idx=1 gen=1 ord=1;
  R02 pc=0x40033c addr=0x41fff0 seq=4 lq_idx=2 gen=2 ord=2;
  R03 pc=0x400340 addr=0x41fff8 seq=5 lq_idx=3 gen=3 ord=3;
  R04 pc=0x400344 addr=0x420000 seq=6 lq_idx=4 gen=4 ord=4;
  R05 pc=0x400348 addr=0x420008 seq=7 lq_idx=5 gen=5 ord=5.
- **RP01** (SKIP_REPLAY; load identity from stdout):
  target ordinal 26/77/128/179/230; in every run load_pc=0x4005a0 (4195680);
  R01 load_seq=16293 lq_idx=774 gen=1283 store_seq=16292;
  R02 23229/825/1334/23228; R03 30165/876/1385/30164;
  R04 37101/927/1436/37100; R05 44037/978/1487/44036.

## 4. Control verification

- **30 of 30 controls have `injection_count == 0`**, `control_valid = true`,
  `fault_activation_status = NOT_TRIGGERED`.
- Command-line guard evidence (`command.txt` in each control outdir):
  - **DA04** and **MD04**: no injector flag at all; only `--chaos_propagation`
    (runner guard removes the injector).
  - **RP01**: no `--chaos_lsqfwd` (only `--chaos_propagation`); `--probability 0.0`.
  - **SP05**: `--chaos_lsqfwd` mounted with `--probability 0.0` -> 0 injections.
  - **LP01**: `--chaos_l1dfwd` mounted with `--probability 0.0` -> 0 injections.
  - **LQ04** (recovered): no `--chaos_lq04` in the control command; 0 injections.
- All control oracles pass; RP01 controls report the expected checksum
  `f3b1c554273d23f7`.

## 5. RP01 — honest HANG accounting (not MASKED)

RP01 fault runs are bounded at 90 s by the driver (`RP01_TIMEOUT = 90`); the
process was killed by that wall-clock limit in all five contexts:

| Ctx | target ord | RP01_ELIGIBLE | RP01_SKIP_REPLAY | CHAOS_RP01_WATCHDOG | exit | timed_out | prop_trace.csv.gz | lsq_fwd_injections.log | stdout |
|---|---|---|---|---|---|---|---|---|---|
| R01 | 26 | 26 | 1 | not printed | 124 | True | 140,394 B | 27 lines | 6,530 B |
| R02 | 77 | 77 | 1 | not printed | 124 | True | 146,399 B | 78 lines | 16,270 B |
| R03 | 128 | 128 | 1 | not printed | 124 | True | 152,378 B | 129 lines | 26,043 B |
| R04 | 179 | 179 | 1 | not printed | 124 | True | 158,383 B | 180 lines | 35,835 B |
| R05 | 230 | 230 | 1 | not printed | 124 | True | 164,344 B | 231 lines | 45,627 B |

- `RP01_ELIGIBLE` fires exactly at ordinals 1..target; exactly one
  `RP01_SKIP_REPLAY` is emitted at the target ordinal.
- The injector's internal watchdog (`CHAOS_RP01_WATCHDOG`) never fired inside the
  90 s budget; the HANG is the driver's external wall-clock timeout, recorded as
  `terminal = HANG`, `timed_out = true`, `exit_code = 124`. It is **not**
  classified or relabeled as MASKED.
- No `trace_v31.jsonl` exists for these runs (process killed before conversion);
  only the partial `prop_trace.csv.gz` and injection log listed above.

## 6. Driver/tool anomalies (no source files were edited)

**A. `write_csv()` ignores `--out-csv`.** In `tools/lsu_v332_matrix.py`,
`write_csv(rows, path=...)` opens the module-global `SUMMARY_CSV`
(`audit_v3_3_2/controls/LSU_Fault_Control_Pair_Final.csv`) instead of `path`.
Consequence: every concurrent driver invocation (Agent J's `_J.csv` run, this
`_K.csv` run, and the LQ04 recovery) writes the same default file; the
requested `*_K.csv` was never created by the driver. Recovery action: the
60-row K result set was captured from the default CSV after this driver
finished and written to `LSU_Fault_Control_Pair_Final_K.csv` (the file exists
with 60 data rows; columns match the driver schema). No source file was modified.

**B. LQ04 was 100% blocked in the first pass.** The driver's `CONTEXTS["LQ04"]`
has no `workload` key, so `run_pilot.py` was called without `--workload`,
`allow_workload_override=False`, and the manifest check compared the frozen
Excel sample checksum for `lq_lifetime` against the pilot-only
`lq_lifetime_ordinal` binary. All 10 first-pass LQ04 runs exited 1 before gem5:

```
manifest.ManifestError: workload SHA mismatch for LQ04-R01-fault:
expected 7c69fd27fabf406e00b5706469fabfa082be1dbe44ee2e8f49587e6839b0156d,
got fa25f785a4822eb578ae8da2d26c400d7450f40d975b2d7da84de900b48d97ba
```

(actual file `docs/gem5-fi/lsu/implementation_v3_2/workloads/lq_lifetime_ordinal`,
SHA256 `fa25f785...`; expected frozen value is for `lq_lifetime`, `7c69fd27...`).
Recovery (no source edit): re-invoked the same committed driver's `main()` with
`CONTEXTS["LQ04"]["workload"] = WORKLOADS/"lq_lifetime_ordinal"` set in memory,
which is exactly what `run_pilot._workload_for("LQ04")` already declares.
Result: 10/10 LQ04 runs executed and produced real data (table above). The
LQ04 rows carry this provenance in the CSV `error` column; the diagnostic
subset CSV is at `audit_v3_3_2/controls/_lq04_workloadfix.csv`
(note: the driver's write_csv bug means the recovery output actually landed in
the default `LSU_Fault_Control_Pair_Final.csv`; its 10 LQ04 rows were merged
into the K CSV).

**C. `terminal` is null in driver summaries for pilot-path rows.** `run_pilot.py`
stores the terminal under `classification.terminal_state`; the driver reads
`meta.get("terminal")`, which does not exist. The real values are reported in
section 2 from `pilot_meta.json`.

**D. Observed MD04 fault elapsed ~5.0-5.5 s per run** (the task note expected
~47 s); this is the real measured value, not a truncation.

**E. Identity fields available per hook.** SP05 logs only SQ identity
(store_seq/sq_idx/gen); DA04 logs seq + address + byte-enable; LP01 logs full
PC/VA/PA; LQ04 logs PC/addr + LQ index; MD04 logs addr/load_seq/store_seq;
RP01 logs load identity on stdout. Missing PC/VA in SP05/DA04 is a hook
property, not a run failure.

## 7. Missing/error rows

- First pass: LQ04 R01-R05 fault and control (10 rows), all exit 1 with the
  ManifestError quoted above (no gem5 execution).
- All other 50 rows completed; **no missing rows and no other errors** after the
  LQ04 recovery (60/60 rows now have real data).

## 8. Scope discipline

Only runs for SP05, DA04, LP01, MD04, LQ04, RP01 were created or modified.
Agent J's models (A01, A03, FW02, FW05, SQ01, SQ03) and their `runs/` dirs were
not touched. No git add/commit/push was performed; no source files were edited.
Note that the shared default CSV (`LSU_Fault_Control_Pair_Final.csv`) is subject
to the write_csv collision described in anomaly A for any concurrent driver run.
