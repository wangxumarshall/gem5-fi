# LSU v3.3.3 — Final Acceptance Report

**Date:** 2026-11-12
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
**Final source HEAD:** `b5031bf7d857ca7901810a3bf3629f5649ddaaac`
**Final binary:** `build/ARM/gem5.opt`, SHA256 `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
**Scope:** 12 models × R01–R05 = 60 dynamic contexts; 60 fault runs + 60 matched controls.
**Final status:** **`READY_FOR_FORMAL_EXPERIMENT`** (independent audit PASS — Agent F3, 2026-11-12; see `LSU_Independent_Acceptance.md`).

---

## 1. Headline

The v3.3.2 round's five P0 defects and the tooling/identity defects are closed on one
final binary. The three root-cause source fixes are:

1. **PRE retry exclusion (A01/A03):** a `pushRequest` re-entry with
   `translationStarted()` is no longer an eligible event; A01-R03's dead-copy
   injection (`a01_ea_discarded; applied_to_request=0`) is gone.
2. **A01 8-byte model scope (L-A12):** the 50% context was a 16-byte vector load
   (`ldr q0`); `EA ^ 0x8` made it misaligned and bypassed the GPR writeback
   observer. A01 now counts only 8-byte GPR loads; the count-only census gives
   ROI `585–713` (N=129), ordinals `597/623/649/675/701`. A01 is 5/5 SDC with
   `register_writeback`, commit, consumers and oracle FAIL.
3. **A03 in-simulator watchdog + honest terminal:** the persistent stuck-at
   fault reaches the application checksum; the watchdog terminates cleanly after
   the oracle (tick 400,963,640, lifecycle emitted, gzip-valid trace). A03 is
   5/5 `SDC / POST_ORACLE_SIM_HANG`, not HANG-without-evidence.
4. **SP05 store-data binding:** `store_data_fnv` is non-null
   (`b6180e0c195fd2e9` for R01), `data_correct=0`,
   `stage_outcome=CHAIN_VISIBILITY_LOST`, plus an explicit `sp05_write_skipped`
   node. The store→visibility→reload→consumer chain is complete.
5. **Control close paths:** `probability<=0` is a true disable across the
   injectors; MD04's separate probability follows the global value; DA04/LQ04/
   RP01/SQ01/SQ03/SP05 cannot misfire when mounted at p=0.

The final 120-run matrix is on the single binary `1126e0fd`. The terminal
distribution is **SDC 43, MASKED 12, HANG_WATCHDOG 5**; every context is
explainable by its designed mechanism.

---

## 2. Final evidence

| Check | Real result |
|---|---|
| Final run set | 120 summaries; one binary SHA (`1126e0fd`) in all 120 |
| Fault injection | 60/60 fault `injection_count>0` |
| Control zero | 60/60 control `injection_count==0`; all control oracles PASS |
| Control classification | 35 `MOUNTED_BUT_DISABLED`, 25 `INJECTOR_ABSENT`, 0 `SUPPRESSED` |
| ROI arithmetic | 60/60 `N=end-start+1`, `absolute=start+ceil(p*N)-1` |
| Distinctness | 60/60 unique identities within each model |
| Causal rows | 60/60 closed: 50 `COMPLETE` + 5 `COMPLETE_PROP_TRACE` (A03) + 5 `PARTIAL_WATCHDOG` (RP01 HANG) |
| Oracle | 43 FAIL (SDC), 12 PASS (MASKED), 5 NO_CHECKSUM (RP01 HANG) |
| Workbook | 8 sheets; 60 manifest rows; 60/60 authoritative SampleRunID/Seed; ConfigFrozen=YES; ConfigSHA `8309da72…` |
| Regression | `pytest tests/ -q` → **232 passed**; platform → **121 passed** |
| Runner dry-run | 120 commands, no run dirs written |
| Binary/source | `git diff --stat b5031bf7 -- CHAOS/gem5/src` empty; 0 build errors |

### Terminal distribution by model

| Model | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| A01 | SDC | SDC | SDC | SDC | SDC |
| A03 | SDC | SDC | SDC | SDC | SDC |
| FW02 | SDC | SDC | MASKED | SDC | SDC |
| FW05 | SDC | SDC | SDC | SDC | SDC |
| SQ01 | SDC | SDC | SDC | SDC | SDC |
| SQ03 | MASKED | MASKED | MASKED | MASKED | MASKED |
| SP05 | SDC | SDC | SDC | SDC | SDC |
| DA04 | SDC | SDC | SDC | SDC | SDC |
| LP01 | SDC | SDC | SDC | SDC | SDC |
| MD04 | MASKED | SDC | SDC | SDC | SDC |
| LQ04 | MASKED | MASKED | MASKED | MASKED | MASKED |
| RP01 | HANG | HANG | HANG | HANG | HANG |

### MASKED mechanisms (12/12 have evidence)

- FW02-R03: `SUPPRESSED_FORWARD_NORMAL_VALUE`
  (`normal_decision=forwarded; fault_decision=suppressed; replay_count=0`).
- SQ03-R01/R03/R04/R05: `VISIBILITY_TIMING_SHIFT` /
  `DRAIN_BEFORE_COMMIT_WITH_RELOAD_CONSUMER`; SQ03-R02:
  `VISIBILITY_TIMING_SHIFT` / `LIFECYCLE_ONLY`. The reload is after commit in all
  five; the oracle PASSes; this is not SDC.
- MD04-R01: `INERT_AFTER_COMPLETION` (`no_wrong_value_produced`).
- LQ04-R01–R05: `ENTRY_INVALIDATED_RESTORED`
  (`data_unchanged=1; no_pop=1; no_reuse=1`).

### RP01 HANG evidence

All five faults record the target `RP01_SKIP_REPLAY` ordinal
(26/77/128/179/230), one injection, and the in-simulator
`CHAOS_RP01_WATCHDOG_EXPIRED` (20M-cycle deadline), with no checksum. The
control completes and prints golden `f3b1c554273d23f7`.

---

## 3. Answers to the required 11 questions

1. **12 models complete?** Yes, 12/12.
2. **60 dynamic contexts correct?** Yes, 60/60 mapped, distinct, with the
   approved 10/30/50/70/90 percentile rule. A01 uses the corrected 8-byte-only
   window `585–713` (N=129); A03 uses `1040–1222` (N=183).
3. **Which workloads changed, approved?** Six candidate workloads adopted
   (FW02 W4-v2, RP01 partial-overlap, MD04 violations, SQ01/SQ03/SP05
   `sq_reload_v3212`) plus the A01 8-byte scope correction and the A01/A03
   PRE-retry fix; all approved by the researcher on 2026-11-12
   (`decisions/LSU_v3.3.3_Researcher_Approval.md`). SampleRunID/Seed unchanged.
4. **Propagation chains closed?** Yes, 60/60 closed: 50 `COMPLETE` + 5
   `COMPLETE_PROP_TRACE` (A03) + 5 `PARTIAL_WATCHDOG` (RP01 HANG). Every row has an injection,
   activation/first divergence, downstream/consumer, commit/squash/hang, and
   oracle/terminal. MASKED rows carry a mechanism; RP01 carries the internal
   watchdog. A03's raw trace is the complete `prop_trace.csv.gz` (no
   `trace_v31` in the direct driver); RP01's partial trace is accepted only
   for its designed `HANG_WATCHDOG`.
5. **Application Oracle?** Yes, 60/60: 43 SDC oracle FAIL, 12 MASKED oracle PASS
   (no wrong value / visibility shift), 5 RP01 HANG with no checksum by design.
6. **60 Fault-Control matched?** Yes, 60/60: same seed, ELF, binary, config,
   ROI, ordinal; controls zero-inject (35 mounted-p0 + 25 absent).
7. **Seed/SampleRunID complete?** Yes, 60/60 authoritative IDs and seeds copied
   from the frozen matrix; no null seed, no invented value.
8. **Final binary unique/traceable?** Yes, one binary `1126e0fd` for all 120
   runs; source HEAD `b5031bf7`; build log, config SHA and ELF SHAs recorded.
9. **Excel complete?** Yes, the v3.3.3 workbook has the 8 required sheets,
   60 manifest rows, and no blank critical field marked PASS.
10. **Remaining blockers?** None blocking. The ledger is reconciled
    (`LSU_v3.3.3_Ledger_Reconciliation.md`): 11 VERIFIED, 32 CLOSED, 1
    SUPERSEDED, 3 OPEN_NONBLOCKING tool fields (single exit code,
    manifest-validator selftest, null `injection_events`) that no gate depends
    on. The independent re-audit of the post-audit fixes is the last gate; the
    formal campaign awaits explicit authorization.
11. **Ready to launch?** `READY_FOR_FORMAL_EXPERIMENT` once the independent
    re-audit signs off; the campaign command is in §5, not executed here.

## 3.1 Independent-audit findings addressed (post-audit fixes)

The first independent audit returned `PARTIALLY_READY` on documentation/
provenance defects. Each was fixed and is reflected in the current artifacts:

| Finding | Fix |
|---|---|
| F-01 config SHA `7fd7e12d` stale | Final config SHA `8309da72…` recorded in the provenance and `Binary_Config`; matches every run manifest |
| F-02 `685d88f7` backup was the final binary | Misleading hardlink removed; only `gem5.opt.v333-1126e0fd` is retained; the pre-correction binary is explicitly not retained, its runs archived |
| F-03 `ConfigFrozen=NO/PENDING` | v3.3.3 workbook now `ConfigFrozen=YES (approved 2026-11-12)` with config SHA; `Readiness_Gate` is 60/60 PASS; the frozen source Excel is untouched |
| F-04 trace overclaim | Honest labels: A03 `COMPLETE_PROP_TRACE` (prop_trace), RP01 `PARTIAL_WATCHDOG` (HANG); causal is 55+5, not 60 `COMPLETE` |
| F-05 stale ROI in manifest | A01 `585–713/N=129`, A03 `1040–1222/N=183` in the manifest, ROI sheet and causal table |
| F-06 stale A03 provenance row | Final A03-R01: ordinal 1058, checksum `1cf7a5a9f11dab7e`, watchdog tick 400,958,635 |
| F-07 unreconciled ledger | 47 rows reconciled; 0 blocking OPEN; `LSU_v3.3.3_Ledger_Reconciliation.md` |
| F-10/F-12/F-13/F-14 | Documented: no standalone A03 census (the fault stream is the census), SQ01≡SQ03 shared workload stated, RP01 oracle `NO_CHECKSUM` is the correct label for HANG, 15 direct runs have manifest/oracle (verified) |

---

## 4. Ready Gate

| Gate | Result |
|---|---|
| Models | 12/12 PASS |
| Dynamic Contexts | 60/60 PASS |
| Workload | 12/12 approved and frozen |
| ROI | 60/60 PASS |
| Context Distinctness | 60/60 PASS |
| Injection | 60/60 injection>0 |
| Propagation | 60/60 closed (50 COMPLETE + 5 COMPLETE_PROP_TRACE + 5 PARTIAL_WATCHDOG accepted for HANG) |
| Application Oracle | 60/60 valid |
| Fault-Control | 60/60 strict pairs |
| Control Zero Proof | 60/60 |
| SampleRunID | 60/60 |
| Seed | 60/60 |
| Binary Provenance | complete |
| Config Freeze | YES (`1126e0fd`, config `8309da72…`, warm-up=0, measured ROI; frozen Excel unchanged) |
| Runner Dry-run | PASS (120 commands) |
| Regression | PASS (232 + 121) |
| Independent Audit | PASS (Agent F3, 2026-11-12; see `LSU_Independent_Acceptance.md`) |

---

## 5. Formal campaign command (do not run until authorized)

```bash
python3 tools/lsu_v332_matrix.py --models all --roles fault,control \
  --out-base runs/lsu/formal_v333 \
  --out-csv runs/lsu/formal_v333/LSU_Fault_Control_Pair_RAW.csv
```

- Task mapping: 12 models × 5 contexts × {fault, control} = 120 runs.
- Resources: 1 gem5 process per run; ≤4 concurrent; 58 GiB free; the driver
  serializes the set; estimate ~30–40 min on the current host (RP01 is the
  long pole at the 20M-cycle watchdog).
- The campaign uses the frozen binary `1126e0fd`, warm-up=0, the measured ROI
  and the executed EventOrdinals in `ROI_Context_Mapping`.

---

## 6. What is in the package

The 14 required items plus the raw per-run evidence (`runs/`), the pre-correction
history (`runs_685d88f7/`), the A01 8-byte census, the gate tests, the build logs,
the source diff patch, the runbook, and the six Phase-1 agent reports. Every
claim above cites a real path or a real command output.
