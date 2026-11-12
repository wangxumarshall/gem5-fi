# Agent C — Fault/Control Zero-Injection Evidence Report (LSU v3.3.3)

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Mode:** read-only. No data/source/Excel/gem5/scons changes. This report is the only file written.
**Scope:** all 60 `*-control` runs of the v3.3.3 12-model x 5-context matrix; classification against the executed `command.txt` and the current source gates; per-control proof that `InjectionApplied = 0`.

## 0. Inputs actually read

- `audit_v3_3_3/controls/LSU_Fault_Control_Pair_FINAL.csv` (61 lines, 60 rows) and `audit_v3_3_3/LSU_Fault_Control_Final_Audit.csv` (`cmp` says **byte-identical**).
- All 60 `audit_v3_3_3/runs/<Model>-R<NN>-control/{command.txt,summary.json,pilot_meta.json,manifest.json,trace_v31.jsonl,prop_trace.csv.gz,stdout.log,stderr.log,oracle.log,*.log}`.
- The 60 matched `*-fault` `command.txt`/`summary.json` (for pair/seed/gate comparison).
- `audit_v3_3_3/gate_tests_final/{DA04-p0,MD04-p0}.stdout` and their run dirs.
- `configs/se/lsu_proxy.py`, `tools/lsu_v332_matrix.py`, `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`, `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py`, `tests/test_lsu_v333_control.py`.
- Injector sources: `CHAOS/gem5/src/cpu/o3/{CHAOSAddrPath,CHAOSLSQFwd,CHAOSL1DForward,CHAOSLQ04,CHAOSMD04}/*.cc|.hh`.
- `audit_v3_3_3/LSU_v3.3.3_Final_Acceptance_Report.md`, `audit_v3_3_3/LSU_Independent_Acceptance.md`.

## 1. Executive verdict

| Claim | Verdict |
|---|---|
| 60/60 controls have `summary.injection_count == 0` | **PASS (verified)** |
| 60/60 controls exit 0 and `oracle.log` = `ORACLE_PASS` | **PASS (verified)** |
| Zero-injection classification 35 `MOUNTED_BUT_DISABLED` / 25 `INJECTOR_ABSENT` / 0 `MOUNTED_BUT_SUPPRESSED` / 0 `MOUNTED_BUT_ACTIVE` | **PASS (re-derived from `command.txt`; matches CSV 60/60)** |
| Every mounted control (the 35) is gated by `--probability 0.0` in the current source | **PASS (source-confirmed, file:line in §5)** |
| Mounted-at-p=0 cannot inject — runtime artifact per model | **PASS: 7 models via their own p=0 controls (A01/A03/FW05/LP01/SQ01/SQ03/SP05) + 2 via gate runs (DA04/MD04); PARTIAL: FW02/LQ04/RP01 are source-only. See §6** |
| "60/60 strict matched pairs, same config" | **OVER-STATED**: true for the 35 mounted controls; the 25 absent controls intentionally omit the injector (same workload/ELF/binary/context, not same config). |

No control is FAIL and no control's zero-injection claim is UNVERIFIED. The gaps are evidence-strength/provenance gaps, not data defects; they are enumerated in §7 and §10.

## 2. Evidence classes used

| Token | Meaning |
|---|---|
| `CMD` | executed `command.txt` (authoritative mount/probability record) |
| `SUM` | `summary.json` `injection_count`, `exit_code`, `terminal_reason` |
| `ORC` | `oracle.log` `ORACLE_PASS` |
| `TRC` | `trace_v31.jsonl`: zero `injection_status != NOT_APPLICABLE`, `missing_stages=["injection"]` |
| `LOG` | injector model log / stdout funnel line with `injected=0` |
| `SRC` | injector source `probability <= 0.0f` early return (file:line in §5) |
| `GATE` | a real mounted-p=0 gem5 run under `gate_tests_final/` |
| `NONE` | absence of the artifact (called out, never silently treated as proof) |

## 3. Per-model classification and gate evidence

| Model | n | Class | Mount flag | Fault-run activation (fault cmd) | Control disable | Runtime attempt evidence | Mounted-p0 runtime artifact |
|---|---|---|---|---|---|---|---|
| A01 | 5 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | `--probability 1.0`, F0, `max_faults=1`, ordinal+seed | `--probability 0.0`, same mode/ordinal/seed | `CHAOS_LSU_TRIGGER attempted=0 eligible=597..701 injected=0` | 5/5 control runs |
| A03 | 5 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | `--probability 1.0`, F5, `max_faults=0` (unlimited), ordinal+seed+watchdog | `--probability 0.0`, same mode/ordinal/seed (no watchdog flag) | `CHAOS_LSU_TRIGGER attempted=0 eligible=0 injected=0` | 5/5 control runs (eligible counter is 0; see F7) |
| DA04 | 5 | INJECTOR_ABSENT | none | `--chaos_lsqfwd da04_be_bit0`, F0, `max_faults=1`, ordinal+seed | injector omitted | n/a (not instantiated) | **1 gate run** `gate_tests_final/DA04-p0` |
| FW02 | 5 | INJECTOR_ABSENT | none | `--chaos_lsqfwd f6_fw02`, `max_faults=1`, ordinal+seed | injector omitted | n/a (not instantiated) | **none** (SRC only) |
| FW05 | 5 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | `--chaos_lsqfwd fw05_older_src`, `max_faults=1`, ordinal+seed | `--probability 0.0`, same mode/ordinal/seed | attached log present but 0 bytes (no injection line) | 5/5 control runs |
| LP01 | 5 | MOUNTED_BUT_DISABLED | `--chaos_l1dfwd` | `--chaos_l1dfwd mask=0x8`, `max_faults=1`, ordinal+seed | `--probability 0.0`, same mask/ordinal/seed | no counter (log is only created at p>0); SUM=0 | 5/5 control runs (command+SRC+SUM) |
| LQ04 | 5 | INJECTOR_ABSENT | none | `--chaos_lq04`, `max_faults=1`, ordinal | injector omitted | n/a (not instantiated) | **none** (SRC only) |
| MD04 | 5 | INJECTOR_ABSENT | none | `--chaos_md04`, `--md04_probability 1.0`, `max_faults=1`, ordinal+seed | injector omitted | n/a (not instantiated) | **1 gate run** `gate_tests_final/MD04-p0` |
| RP01 | 5 | INJECTOR_ABSENT | none | `--chaos_lsqfwd rp01_skip_replay`, `max_faults=1`, ordinal+seed+watchdog | injector omitted | n/a (not instantiated) | **none** (SRC only) |
| SP05 | 5 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | `--chaos_lsqfwd sp05_complete`, `max_faults=1`, ordinal+seed | `--probability 0.0`, same mode/ordinal/seed | `CHAOS_SP05_STATUS selected=0 fired=0 injected=0 eligible=0` | 5/5 control runs |
| SQ01 | 5 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | `--chaos_lsqfwd sq01_bit3`, F0, `max_faults=1`, ordinal+seed | `--probability 0.0`, same mode/ordinal/seed | `CHAOS_LSU_TRIGGER attempted=0 eligible=0 injected=0` | 5/5 control runs |
| SQ03 | 5 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | `--chaos_lsqfwd sq03_canwb`, `max_faults=1`, ordinal+seed | `--probability 0.0`, same mode/ordinal/seed | `CHAOS_SQ03_STATUS fired=0 injected=0 eligible=0` | 5/5 control runs |

Counts: **35 MOUNTED_BUT_DISABLED** (A01, A03, FW05, LP01, SQ01, SQ03, SP05) + **25 INJECTOR_ABSENT** (DA04, FW02, LQ04, MD04, RP01) = 60. This is exactly the 35/25 split in the FINAL CSV. Re-derived from the executed `command.txt` with the same predicate as `tools/lsu_v332_matrix.py:classify_control`: **0 mismatches**.

## 4. Compact 60-row table

`Applied` = `summary.injection_count`. `Fault inj` = matched fault-run `injection_count` (pair anchor). Every row is `PASS` for zero-injection; the class column and the evidence column state *why*.

| Model | Ctx | Class | Mount | Fault-run activation | Control gate | Attempts | Applied | Fault inj | Evidence | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| A01 | R01 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F0; mf=1; ord=597 | p=0.0 | 0 (eligible=597) | 0 | 1 | CMD+SUM+ORC+TRC+LOG `attempted=0 injected=0`+SRC | PASS |
| A01 | R02 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F0; mf=1; ord=623 | p=0.0 | 0 (eligible=623) | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| A01 | R03 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F0; mf=1; ord=649 | p=0.0 | 0 (eligible=649) | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| A01 | R04 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F0; mf=1; ord=675 | p=0.0 | 0 (eligible=675) | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| A01 | R05 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F0; mf=1; ord=701 | p=0.0 | 0 (eligible=701) | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| A03 | R01 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F5; mf=0; ord=1058; wd | p=0.0 | 0 | 0 | 51310 | CMD+SUM+ORC+TRC+LOG `attempted=0 injected=0`+SRC | PASS |
| A03 | R02 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F5; mf=0; ord=1094; wd | p=0.0 | 0 | 0 | 51303 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| A03 | R03 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F5; mf=0; ord=1131; wd | p=0.0 | 0 | 0 | 51304 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| A03 | R04 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F5; mf=0; ord=1168; wd | p=0.0 | 0 | 0 | 51283 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| A03 | R05 | MOUNTED_BUT_DISABLED | `--chaos_addrpath` | p=1.0; F5; mf=0; ord=1204; wd | p=0.0 | 0 | 0 | 51253 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| DA04 | R01 | INJECTOR_ABSENT | none | lsqfwd/da04_be_bit0; F0; mf=1; ord=135 | omitted | n/a | 0 | 1 | CMD(no mount)+SUM+ORC+TRC+GATE `injected=0`+SRC | PASS |
| DA04 | R02 | INJECTOR_ABSENT | none | lsqfwd/da04_be_bit0; F0; mf=1; ord=340 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC (+same gate) | PASS |
| DA04 | R03 | INJECTOR_ABSENT | none | lsqfwd/da04_be_bit0; F0; mf=1; ord=544 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS |
| DA04 | R04 | INJECTOR_ABSENT | none | lsqfwd/da04_be_bit0; F0; mf=1; ord=749 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS |
| DA04 | R05 | INJECTOR_ABSENT | none | lsqfwd/da04_be_bit0; F0; mf=1; ord=954 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS |
| FW02 | R01 | INJECTOR_ABSENT | none | lsqfwd/f6_fw02; mf=1; ord=13 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| FW02 | R02 | INJECTOR_ABSENT | none | lsqfwd/f6_fw02; mf=1; ord=25 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| FW02 | R03 | INJECTOR_ABSENT | none | lsqfwd/f6_fw02; mf=1; ord=37 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| FW02 | R04 | INJECTOR_ABSENT | none | lsqfwd/f6_fw02; mf=1; ord=49 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| FW02 | R05 | INJECTOR_ABSENT | none | lsqfwd/f6_fw02; mf=1; ord=61 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| FW05 | R01 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/fw05_older_src; mf=1; ord=200 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+0-byte LOG+SRC | PASS |
| FW05 | R02 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/fw05_older_src; mf=1; ord=600 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+0-byte LOG+SRC | PASS |
| FW05 | R03 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/fw05_older_src; mf=1; ord=1000 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+0-byte LOG+SRC | PASS |
| FW05 | R04 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/fw05_older_src; mf=1; ord=1400 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+0-byte LOG+SRC | PASS |
| FW05 | R05 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/fw05_older_src; mf=1; ord=1800 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+0-byte LOG+SRC | PASS |
| LP01 | R01 | MOUNTED_BUT_DISABLED | `--chaos_l1dfwd` | l1dfwd; mask=0x8; mf=1; ord=2549 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+SRC (no counter) | PASS* |
| LP01 | R02 | MOUNTED_BUT_DISABLED | `--chaos_l1dfwd` | l1dfwd; mask=0x8; mf=1 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| LP01 | R03 | MOUNTED_BUT_DISABLED | `--chaos_l1dfwd` | l1dfwd; mask=0x8; mf=1 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| LP01 | R04 | MOUNTED_BUT_DISABLED | `--chaos_l1dfwd` | l1dfwd; mask=0x8; mf=1 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| LP01 | R05 | MOUNTED_BUT_DISABLED | `--chaos_l1dfwd` | l1dfwd; mask=0x8; mf=1 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| LQ04 | R01 | INJECTOR_ABSENT | none | `--chaos_lq04`; mf=1; ord=1 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| LQ04 | R02 | INJECTOR_ABSENT | none | `--chaos_lq04`; mf=1; ord=2 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| LQ04 | R03 | INJECTOR_ABSENT | none | `--chaos_lq04`; mf=1; ord=3 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| LQ04 | R04 | INJECTOR_ABSENT | none | `--chaos_lq04`; mf=1; ord=4 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| LQ04 | R05 | INJECTOR_ABSENT | none | `--chaos_lq04`; mf=1; ord=5 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS* |
| MD04 | R01 | INJECTOR_ABSENT | none | `--chaos_md04` md04_p=1.0; mf=1; ord=3 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+GATE `ORDINAL_NOT_REACHED eligible=0`+SRC | PASS |
| MD04 | R02 | INJECTOR_ABSENT | none | `--chaos_md04` md04_p=1.0; mf=1; ord=5 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC (+same gate) | PASS |
| MD04 | R03 | INJECTOR_ABSENT | none | `--chaos_md04` md04_p=1.0; mf=1; ord=6 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS |
| MD04 | R04 | INJECTOR_ABSENT | none | `--chaos_md04` md04_p=1.0; mf=1; ord=8 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS |
| MD04 | R05 | INJECTOR_ABSENT | none | `--chaos_md04` md04_p=1.0; mf=1; ord=10 | omitted | n/a | 0 | 1 | CMD+SUM+ORC+TRC+SRC | PASS |
| RP01 | R01 | INJECTOR_ABSENT | none | lsqfwd/rp01_skip_replay; mf=1; ord=26; wd | omitted | n/a | 0 | 1 | CMD+SUM+ORC+SRC (no trace_v31) | PASS* |
| RP01 | R02 | INJECTOR_ABSENT | none | lsqfwd/rp01_skip_replay; mf=1; ord=77; wd | omitted | n/a | 0 | 1 | CMD+SUM+ORC+SRC | PASS* |
| RP01 | R03 | INJECTOR_ABSENT | none | lsqfwd/rp01_skip_replay; mf=1; ord=128; wd | omitted | n/a | 0 | 1 | CMD+SUM+ORC+SRC | PASS* |
| RP01 | R04 | INJECTOR_ABSENT | none | lsqfwd/rp01_skip_replay; mf=1; ord=179; wd | omitted | n/a | 0 | 1 | CMD+SUM+ORC+SRC | PASS* |
| RP01 | R05 | INJECTOR_ABSENT | none | lsqfwd/rp01_skip_replay; mf=1; ord=230; wd | omitted | n/a | 0 | 1 | CMD+SUM+ORC+SRC | PASS* |
| SP05 | R01 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sp05_complete; mf=1; ord=952 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG `selected=0 fired=0 injected=0`+SRC | PASS |
| SP05 | R02 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sp05_complete; mf=1; ord=978 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SP05 | R03 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sp05_complete; mf=1; ord=1003 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SP05 | R04 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sp05_complete; mf=1; ord=1029 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SP05 | R05 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sp05_complete; mf=1; ord=1055 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SQ01 | R01 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq01_bit3; F0; mf=1; ord=1018 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG `attempted=0 injected=0`+SRC | PASS |
| SQ01 | R02 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq01_bit3; F0; mf=1; ord=1044 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SQ01 | R03 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq01_bit3; F0; mf=1; ord=1069 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SQ01 | R04 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq01_bit3; F0; mf=1; ord=1095 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SQ01 | R05 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq01_bit3; F0; mf=1; ord=1121 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SQ03 | R01 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq03_canwb; mf=1; ord=1021 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG `fired=0 injected=0`+SRC | PASS |
| SQ03 | R02 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq03_canwb; mf=1; ord=1047 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SQ03 | R03 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq03_canwb; mf=1; ord=1072 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SQ03 | R04 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq03_canwb; mf=1; ord=1098 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |
| SQ03 | R05 | MOUNTED_BUT_DISABLED | `--chaos_lsqfwd` | lsqfwd/sq03_canwb; mf=1; ord=1124 | p=0.0 | 0 | 0 | 1 | CMD+SUM+ORC+TRC+LOG+SRC | PASS |

`PASS*` = zero-injection is proven, but the *mounted-at-p=0* capability for that model is source-only (no per-context positive counter). See §6 and §10; it is **not** a failure of the control row.

## 5. Source-gate audit — a mounted p=0 injector cannot inject

All five injectors were inspected in the current tree. Every mutation path has an unconditional `probability <= 0.0f` early return **before** any eligibility/attempt accounting or data mutation.

| Injector | Path / hook | p<=0 gate | Models |
|---|---|---|---|
| `CHAOSAddrPath` | AGU address path (PRE) | `CHAOSAddrPath.cc:124` `if (!cpu \|\| probability <= 0.0f) return false;`; observe-only branch `:252`; `max_faults=0` means *unlimited* (`:143`), so p=0 is the disable | A01, A03 |
| `CHAOSLSQFwd` | legacy forward corruption | `CHAOSLSQFwd.cc:317` `if (probability <= 0.0f) return;` | generic |
| `CHAOSLSQFwd` | wrong-source substitution (F5) | `:458` | (not in the 60) |
| `CHAOSLSQFwd` | SQ01 store-data bit3 | `maybeCorruptStoreData` `:951` | SQ01 |
| `CHAOSLSQFwd` | DA04 byte-enable | `maybeCorruptStoreByteEnable` `:993` | DA04 |
| `CHAOSLSQFwd` | FW02 suppress-forward | `maybeSuppressForwarding` `:1047` | FW02 |
| `CHAOSLSQFwd` | SQ03 canWB | `maybeSetCanWB` `:743` | SQ03 |
| `CHAOSLSQFwd` | SP05 select/complete | `maybeSelectSP05` `:542`, `maybeCompleteSP05` `:579` | SP05 |
| `CHAOSLSQFwd` | FW05 older-source | `maybeSubstituteFW05` `:805` | FW05 |
| `CHAOSLSQFwd` | RP01 skip-replay | `maybeSkipPartialReplay` `:643` | RP01 |
| `CHAOSLSQFwd` | phase-offset | `maybeDelayForward` `:898` | (not in the 60) |
| `CHAOSL1DForward` | load-response corruption | `CHAOSL1DForward.cc:74`; `startup()` attaches even at p=0 (`:154-158`) so a p=0 control is genuinely mounted-but-disabled | LP01 |
| `CHAOSLQ04` | executeLoad lifetime | `CHAOSLQ04.cc:131` `if (probability <= 0.0f) return;` | LQ04 |
| `CHAOSMD04` | checkViolations duplicate-detect | `CHAOSMD04.cc:79` `if (probability <= 0.0f) return;` | MD04 |

MD04's separate probability is correctly coupled to the global value at `configs/se/lsu_proxy.py:1111-1114` (`None` override ⇒ follow `--probability`); its `--md04_probability` default is `None` (`:496-497`). The fault runs pass `--md04_probability 1.0` explicitly; a p=0 mount would resolve to 0.0.

Model-specific runtime gate artifacts:

- **DA04 gate** (`audit_v3_3_3/gate_tests_final/DA04-p0.stdout`): command is the fault command minus `--probability` (0.0). Output: `CHAOS_LSU_TRIGGER: injector=CHAOSLSQFwd tier=F0 attempted=0 eligible=0 injected=0` and `CHAOS_L0_FUNNEL: CHAOSLSQFwd attempted=0 eligible=0 injected=0`. The matched fault run injects 1.
- **MD04 gate** (`audit_v3_3_3/gate_tests_final/MD04-p0.stdout` + `MD04-p0/md04_injections.log`): stdout `[lsu_proxy] CHAOSMD04 probability=0.0 (global=0.0, override=None)`; log `CHAOS_MD04_TARGET_STATUS=ORDINAL_NOT_REACHED eligible_count=0 target_ordinal=3`. The matched fault run injects 1.
- **No equivalent gate artifact exists for FW02, LQ04, RP01.** Their p=0 safety is source-confirmed only.

## 6. Artifact consistency checks (all real, all re-derived)

1. **CSV vs command.txt**: 60/60 rows agree on `ControlInjected=0`, `ControlZeroProof`, `ControlMountEvidence.mounts`, `probability`, `md04_probability`. `ControlInjected` is `0` ×60; `ControlZeroProof` is `35 MOUNTED_BUT_DISABLED` + `25 INJECTOR_ABSENT`; `ControlOracle=PASS` ×60; `ControlExitCode=0` ×60.
2. **Summary**: `injection_count == 0` ×60; `exit_code == 0` ×60; `oracle == true` ×60. `injection_events` is `[]` for 35 and `null` for 25 (A01/A03/FW02/RP01); this is the known non-blocking null-field issue, and it is never used as proof here.
3. **Trace**: 55 controls have `trace_v31.jsonl`; every event record is `injection_status=NOT_APPLICABLE` (0 non-NA records). 50 of them report `missing_stages=["injection"]`; the 5 FW02 controls report `COMPLETE` with `expected_stages=["forwarding_decision"]` and no injection stage (FW02 is a suppression mode, so no injection stage is expected). RP01 controls have no `trace_v31.jsonl` (0 records, `trace_completeness` = null). For SQ03/SP05, `prop_trace.csv.gz` contains only `lq_lifecycle`/`sq_lifecycle`/`fwd` nodes — no `canwb`/premature-completion injection node.
4. **Oracle**: `oracle.log` is `ORACLE_PASS` for all 60 (RP01 golden `f3b1c554273d23f7`, A01/A03 `728e604ffcec539d`, etc.).
5. **Fault pairing**: every matched fault run has `injection_count > 0` (1 ×55, A03 51,253–51,310 ×5); same binary SHA `1126e0fd1fea…` in all 120 summaries; same workload ELF per model/context.
6. **Seed matching**: for the 35 mounted controls, every injector seed flag equals the fault run's (`--addrpath_rng_seed`, `--l1dfwd_rng_seed`, `--rng_seed`); the 25 absent controls carry no injector seed by construction (not a mismatch, a design consequence).
7. **Command diff**: for the 35 mounted controls the only non-`--outdir` difference from the fault command is `--probability 1.0 → 0.0` (plus A03's fault-only `--addrpath_watchdog_cycles 1000000`, whose arming is itself `probability > 0`). For the 25 absent controls the fault-only tokens are exactly the injector mount block — i.e. the config deliberately differs.

## 7. Root causes / adversarial findings

- **C-01 (LOW, stale rationale).** `run_pilot.py:build_model_extra` (`docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py:604-720`) and `platform/tests/test_v332_control_guards.py` still justify the omitted-mount controls with *"the decision never consults `--probability`; a mounted injector would still fire"* (DA04 `:638-646`, MD04 `:649-656`, LQ04 `:681-686`, FW02 `:691-699`, RP01 `:703-710`). That was true before v3.3.3; the v3.3.3 L-A06 gates (§5) now make p=0 a true disable for all five. The controls remain valid, but the recorded *reason* is stale and under-states the current safety.
- **C-02 (MEDIUM, evidence strength).** Three of the five absent-control models (FW02, LQ04, RP01) have **no runtime mounted-at-p=0 artifact**. The acceptance report's sentence "DA04/LQ04/RP01/SQ01/SQ03/SP05 cannot misfire when mounted at p=0" is source-true but runtime-proven only for DA04 (and, separately, MD04).
- **C-03 (LOW, non-discriminating trace).** `trace_v31.jsonl` does not record injections for LP01/FW05/SQ03/MD04 even in the *fault* runs (fault traces also show 0 `INJECTED` events; the direct-driver aggregate traces are `prop_trace.csv.gz`/model logs). Therefore trace absence must not be cited as independent evidence for those controls; the proof stands on CMD+SUM+ORC+LOG/SRC instead.
- **C-04 (LOW, LP01).** `CHAOSL1DForward` creates its log only when `probability > 0` (`:24`), so an LP01 control has no positive counter; zero proof = command p=0 + `startup()` attach (`:154-158`) + source gate (`:74`) + summary 0 + oracle PASS.
- **C-05 (LOW, RP01 provenance).** RP01 controls have no `trace_v31.jsonl`, and `pilot_meta.json` carries `control_valid=null`, `control_misfire=null` (they come from the replay pilot path). Zero proof = command (no mount) + summary 0 + oracle PASS.
- **C-06 (LOW, A03 counter).** A03's control trigger reports `eligible=0` (not "eligible but declined"), so its runtime evidence is weaker than A01's `eligible=597..701`. A03's disable is still unambiguously `--probability 0.0`; `max_faults=0` means unlimited, not disabled.
- **C-07 (INFO, test coverage).** `tests/test_lsu_v333_control.py` asserts the 35/25 split against `audit_v3_3_2/runs`, not `audit_v3_3_3/runs`. The v3.3.3 tree reproduces the same counts (verified manually here), but the v3.3.3 artifacts are not themselves pytest-pinned.
- **C-08 (LOW, wording).** The acceptance report's "same seed, ELF, binary, config, ROI, ordinal" is strictly true only for the 35 mounted controls. For the 25 absent controls the *config intentionally differs* (no injector); seed is inapplicable. The classification itself is honest (`INJECTOR_ABSENT`), so this is a wording fix, not a data defect.

## 8. Proposed one-shot fix

**No control needs a re-run for zero-injection correctness.** The 60 control rows are valid as executed.

Label/doc-only (recommended, no gem5):
1. Update `run_pilot.py:build_model_extra` comments and `platform/tests/test_v332_control_guards.py` docstrings: state that after v3.3.3 (L-A06) `probability<=0` is a hard disable in DA04/MD04/LQ04/FW02/RP01 too, and that omission is retained as the conservative control construction, not because a mounted p=0 would fire.
2. Reword the acceptance report's "same config" sentence to "same model/context/workload/ELF/binary/ordinal; injector deliberately omitted for the 25 absent controls".
3. Re-point `tests/test_lsu_v333_control.py` at `audit_v3_3_3/runs` (add a v3.3.3 35/25 assertion) so the frozen package is pinned.

One-shot runtime strengthening (recommended but **not** gate-blocking, needs authorization; do not run in this audit):
4. Add three mounted-p=0 gate runs following the DA04/MD04 pattern — FW02 `f6_fw02`, LQ04, RP01 `rp01_skip_replay` — with the R01 ordinal and seed, `--probability 0.0`. Expected: `injected=0` / `injected=0` / no `RP01_SKIP_REPLAY` line. This converts C-02 from source-only to runtime-verified for all 12 models.
5. Only if the researcher wants uniformly strong matched controls: re-run the 25 controls with the injector mounted at p=0 (now safe) and reclassify to 60 `MOUNTED_BUT_DISABLED`. This touches the frozen 120-run package, ConfigSHA, manifest and workbook; treat it as a deliberate version bump, not a silent relabel.

Validation for the label-only fix: `pytest tests/test_lsu_v333_control.py docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py -q` should stay green, and the re-derived classification must remain 35/25.

## 9. Proposed `LSU_Control_Zero_Injection_Proof.csv` schema

One row per control (60). Paths are relative to the worktree root; `<run>` = `audit_v3_3_3/runs/<ModelID>-<ContextID>-control`, `<fault>` = the same with `-fault`.

```
ModelID,ContextID,RunID,ConfigClass,MountFlags,Probability,Md04Probability,
FaultRunActivation,SuppressionReason,AttemptInstrumented,InjectionAttemptCount,
InjectionAppliedCount,SummaryInjectionCount,TraceInjectionEvents,ModelLogInjectionLine,
OracleResult,ExitCode,SourceGate,SourceGateFileLine,MountedP0RuntimeArtifact,
ZeroProofResult,EvidencePaths,Notes
```

Column semantics:
- `ConfigClass` ∈ {INJECTOR_ABSENT, MOUNTED_BUT_DISABLED, MOUNTED_BUT_SUPPRESSED, MOUNTED_BUT_ACTIVE}.
- `FaultRunActivation` = the matched fault run's gate string (e.g. `p=1.0;F0;mf=1;ord=597`).
- `AttemptInstrumented` = `yes` only for A01/A03/SQ01 (`CHAOS_LSU_TRIGGER`); `no` otherwise.
- `TraceInjectionEvents` = count of non-`NOT_APPLICABLE` `injection_status` records; `n/a (no trace_v31)` for RP01.
- `MountedP0RuntimeArtifact` = `control-run` / `gate_tests_final/DA04-p0` / `none (source only)`.
- `ZeroProofResult` ∈ {PASS, UNVERIFIED}. The proposed file would be **60 PASS**, with `Notes` carrying the `PASS*` caveat for FW02/LQ04/RP01/LP01.

Per-row evidence path templates (all present unless marked):
- `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/<run>/command.txt` (CMD)
- `.../<run>/summary.json` (SUM: `injection_count`, `exit_code`, `oracle`, `mount_evidence`)
- `.../<run>/oracle.log` (ORC)
- `.../<run>/trace_v31.jsonl` (TRC; absent for RP01)
- `.../<run>/prop_trace.csv.gz` (aggregate trace; TRC for SQ03/SP05)
- `.../<run>/stdout.log` and `.../<run>/stderr.log` (LOG: trigger/funnel/status lines)
- `.../<run>/pilot_meta.json` and `.../<run>/manifest.json` (mount provenance / run identity)
- `.../<run>/lsq_fwd_injections.log` (FW02/FW05/SQ01/SQ03/SP05/RP01 when created; FW05 control is 0 bytes)
- `.../<run>/addrpath_injections.log` (A01/A03 fault only; control has none)
- `.../<run>/md04_injections.log`, `.../<run>/lq04_injections.log`, `.../<run>/l1d_fwd_injections.log` (model-specific; controls generally do not create these at p=0)
- `.../<fault>/summary.json` (fault `injection_count > 0` pairing anchor)
- `audit_v3_3_3/gate_tests_final/DA04-p0.stdout`, `.../MD04-p0.stdout` (GATE)
- Source gates: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc:124`, `.../CHAOSLSQFwd/CHAOSLSQFwd.cc:{317,458,542,579,643,743,805,898,951,993,1047}`, `.../CHAOSL1DForward/CHAOSL1DForward.cc:74,154-158`, `.../CHAOSLQ04/CHAOSLQ04.cc:131`, `.../CHAOSMD04/CHAOSMD04.cc:79`; `configs/se/lsu_proxy.py:496-497,1111-1114`.

## 10. Could not verify

1. **Runtime mounted-at-p=0 for FW02, LQ04, RP01** — no gate artifact exists; only source inspection (`§5`). This is the single strongest evidence gap. It does not invalidate the control rows (those injectors are absent), but it means the acceptance report's mounted-p=0 claim for these three is source-only.
2. **A positive LP01 control counter** — the injector intentionally creates no log at p=0; the trace is non-discriminating (fault runs also lack `INJECTED` events). LP01's zero proof is command + startup attach + source gate + summary + oracle.
3. **RP01 control trace** — no `trace_v31.jsonl`; `pilot_meta.json` lacks `control_valid`/`control_misfire`. Zero proof is command (no mount) + summary 0 + oracle PASS.
4. **A03 "eligible but declined"** — control trigger reports `eligible=0`, so the decline is not demonstrated on a populated eligible stream (unlike A01).
5. **Re-running gem5/scons** — forbidden by this audit's scope; all gate claims above rest on already-present artifacts plus source inspection. The three proposed gate runs in §8.4 were **not** executed.

No fabricated PASS: every `PASS` row above cites an existing artifact; every unproven capability is explicitly marked here and with `PASS*` in the table.
