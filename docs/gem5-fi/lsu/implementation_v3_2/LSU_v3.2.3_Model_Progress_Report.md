# LSU v3.2.3 — Implementation and Model Progress Report

**Package:** `LSU_v3.2.3_Implementation_and_Model_Progress_Package.zip`
**Branch:** `lsu-platform-v3.2.3`
**HEAD:** `4c53f50e0622ba4ece7c89c60905e92c3461aafb`
**Binary SHA256:** `8eb7ce8d76ab63d90dbd00694efb90c7c2545da47ad07ecf5325399274a3b682`
**Formal 60-sample campaign:** NOT STARTED.

---

## 1. Status vocabulary (strict)

| Level | Meaning |
|---|---|
| DESIGNED | fault definition / hook point documented |
| SOURCE_AUDITED | real microarchitectural structure, hook line, workload and trigger verified in the vendored tree |
| IMPLEMENTED | code hook + config parsing exist |
| COMPILED | `scons build/ARM/gem5.opt` succeeds with the change |
| UNIT_TESTED | host unit test covers the new logic |
| PILOT_RUN | a real gem5 pilot produced the target event and a trace |
| PROPAGATION_VERIFIED | the pilot trace proves the fault reached the claimed downstream stage with a causal link |

A row is never promoted without the evidence for that level. "Partial" is
explicitly marked when only some contexts reach a level.

## 2. Model status matrix

| Model | DESIGNED | SOURCE_AUDITED | IMPLEMENTED | COMPILED | UNIT_TESTED | PILOT_RUN | PROPAGATION_VERIFIED | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|---|
| A01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (R02/R04/R05) | R01 TEMPORAL_ASSOCIATION_ONLY; R03 SQUASHED |
| A03 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (R01–R05) | DIRECT_ADDRESS_MATCH, dyn seq 1146 |
| FW02 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (R02–R04) | fault load commit; R01/R05 squash |
| SQ01 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | MASKED; injected byte overwritten, no SDC observed |
| DA04 | ✓ | ✓ | — | — | — | — | — | hook + safety audited |
| LP01 | ✓ | ✓ | — | — | — | — | — | existing injector has size<8 OOB to fix first |
| MD04 | ✓ | ✓ | — | — | — | — | — | F6 wiring gap in CHAOSLSQFwd |
| FW05 | ✓ | ✓ | — | — | — | — | — | F5 path exists; F6 ordinal missing |
| SQ03 | ✓ | ✓ | — | — | — | — | — | paired canWB/storesToWB bound |
| SP05 | ✓ | ✓ | — | — | — | — | — | HANG risk; watchdog required |
| LQ04 | ✓ | ✓ | — | — | — | — | — | **HIGH-RISK as specified** |
| RP01 | ✓ | ✓ | — | — | — | — | — | one skip + watchdog |

## 3. v3.2.3 platform fixes

1. **Address matching.** `run_pilot.py` cleared the A01/A03 address-event list
   after reading it (`events = []` after the branch). Fixed. A03 R01–R05 now all
   report `DIRECT_ADDRESS_MATCH`: last injection dyn seq 1146, injected address
   `0xffffffffffb73c50`, Page Table Fault address identical. The PT address is
   written into a structured `simulator_abort` event and `terminal_evidence`.
2. **A01-R03.** Target seq 169 has injection → address_formed → memory_request →
   squash and no response/writeback/commit. Terminal is `SQUASHED`
   (`TARGET_SQUASHED_NO_COMMIT`), consistent in JSONL/meta/sweep.
3. **PropagationCoverage.** Per-(model, terminal) expected profiles; a missing
   stage is PARTIAL, no stages is NONE. RecordIntegrity, TraceCompleteness and
   PropagationCoverage are independent.
4. **Replay commit.** Replay-tracked instructions now get a real commit node
   (`tracked=replay`) with commit_seq, attempt and generation.
5. **Causality.** `observed_terminal` and `fault_causality` are separate fields:
   DIRECT_ADDRESS_MATCH / DIRECT_DATAFLOW_EVIDENCE / INDIRECT_EVIDENCE /
   TEMPORAL_ASSOCIATION_ONLY / UNKNOWN. `accepted` means record validity only.

## 4. A01 / A03 / FW02 pilots (v3.2.3 binary)

15/15 contexts recorded and accepted (`pilots_v3_2_3/sweep/context_sweep_summary.json`).

| Model | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| A01 | CRASH / TEMPORAL | MASKED / DIRECT_DATAFLOW | SQUASHED / INDIRECT | MASKED / DIRECT_DATAFLOW | MASKED / DIRECT_DATAFLOW |
| A03 | CRASH / DIRECT_ADDRESS ×5 (146/145/144/143/142 applications) | | | | |
| FW02 | MASKED | CRASH / TEMPORAL | MASKED | MASKED | MASKED |

A03/F5 R01–R05 are five activation start positions of one continuous stuck-at
condition, not five independent single injections.

## 5. Replay and commit verification

`pilots_v3_2_3/REPLAY-RW01` (COMPLETED, oracle PASS, trace COMPLETE/VALID):
5 real `partial_forward_mismatch` replays. Three have independent commit nodes
(69296 commit_seq 62176; 71973 commit_seq 63557; 72305 commit_seq 63787;
attempt 2, generation 1); two have squash nodes (70968, 70969). The replays are
not claimed to be caused by the injected suppression.

## 6. SQ01 progress

- SOURCE_AUDITED: hook at `LSQUnit::write()` after the SQ entry memcpy
  (`lsq_unit.cc`), data-only.
- IMPLEMENTED: `CHAOSLSQFwd::maybeCorruptStoreData`, mode `sq01_bit3`, F0 trigger
  via existing `--lsqfwd_lsu_tier F0 / --max_faults / --lsqfwd_event_ordinal`.
- COMPILED: `logs/build_v323_sq01.log`, exit 0.
- UNIT_TESTED: SQ01 log parser + converter (`inj_store_data` → unit SQ,
  sub_unit store_data, old/new byte, SQ index/generation). 52 tests pass.
- PILOT_RUN: R01–R05, 5/5 accepted, 1 injection each, `all_store_bit3=true`,
  observed/terminal MASKED, causality DIRECT_DATAFLOW_EVIDENCE, coverage
  COMPLETE. The injected byte is overwritten by a later store; no SDC was
  observed, so PROPAGATION_VERIFIED is NOT claimed.
- Raw JSONL 189 MB/context: in this package and on disk; excluded from Git
  (GitHub 100 MB limit) with sha256 sidecars.

## 7. Remaining eight models

All SOURCE_AUDITED only (0/8 implemented). Details, hook lines, workloads and
safety verdicts are in `LSU_Remaining_Models_Audit_v3.2.3.md`. LQ04 is
HIGH-RISK; RP01/SP05/MD04/SQ03 are safe-with-bound (one-shot + watchdog);
DA04/LP01/FW05 are data-level. LP01's existing injector has a size<8 OOB cast
that must be fixed before use. FW05/MD04 need F6 wiring because CHAOSLSQFwd does
not register an F6 event consumer.

## 8. W1–W8 baseline

v3.2.3 binary, `baselines_v3_2_3/`: **8/8 exit 0 and 8/8 oracle PASS**; target
events confirmed (W7 267 forwards, 5 reschedules). Counts are identical to
v3.2.2 because the v3.2.3 changes are inert without a fault. See
`LSU_Baseline_v3.2.3.md`.

## 9. Artifacts in the package

- `repo/`: full modified source files, `git_log`, `git_diff`, `source_changes.patch`,
  `git_branch.txt`, `git_status.txt`.
- `docs/`: this report, v3.2.3 status report, remaining-model audit, warm-up/ROI
  recommendation, trace schema, validator source, `GIT_COMMIT_v323.txt`, the
  current authoritative Excel (v3.2.1 workbook).
- `evidence/`: `pilots_v3_2_3/` (15-context sweep, replay pilot, SQ01 R01–R05
  with real JSONL) and `baselines_v3_2_3/`.
- `logs/`: build logs (`build_v323_replay_commit`, `build_v323_sq01`), unit-test
  log, and the pilot/integration logs inside the evidence tree.

## 10. Preserved historical deliverables (not overwritten)

| Deliverable | SHA256 |
|---|---|
| `LSU_v3.2.2_Implementation_Package.zip` | `d20315152048e9191a453f8b37f6ec37fcd9e24f09327687aa98d545b0a709ac` |
| `LSU_v3.2.3_Propagation_Closure_Package.zip` | `1e3e8377f20d03bb3ee9a1d41e5e715f95c8e6df732a8d432a0aa56bc267b141` |

v3.2.1 and earlier artifacts remain in the tree unchanged. No historical file
was deleted or modified by this package.

## 11. Unresolved issues and next steps

1. Implement the remaining eight models one per commit, in order: DA04 → LP01
   (fix the size<8 OOB first) → MD04 → FW05 → SQ03 → SP05 → LQ04 → RP01.
2. LQ04 requires a shadow poisoned flag and tolerant consumers; the current
   `clear()` path asserts/use-after-frees. Do not implement it as specified.
3. Add an F6 event consumer or the private one-shot ordinal to CHAOSLSQFwd for
   FW05/MD04.
4. Define the HANG path in the pilot runner (watchdog + TIMEOUT/HANG) before
   SP05/RP01, so a hang is not misclassified as a simulator crash.
5. Researcher confirmation of Warm-up/ROI; then phase-instrumented runs to fix
   the concrete EventOrdinal values.
6. The 60 formal samples remain BLOCKED until the above is resolved.
7. Disk is at 92 % (28 GB free); the archive plan still waits for approval.
8. SQ01 produced MASKED only; a workload/context that exposes the corrupted
   store to the checksum or a consumer is needed for SDC/PROPAGATION_VERIFIED.
