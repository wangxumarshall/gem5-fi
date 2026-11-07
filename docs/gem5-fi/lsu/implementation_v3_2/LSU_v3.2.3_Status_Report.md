# LSU v3.2.3 — Propagation Closure Status Report

**Branch:** `lsu-platform-v3.2.3` (base `97fb263f`, v3.2.2)
**Binary:** `build/ARM/gem5.opt` SHA256
`8eb7ce8d76ab63d90dbd00694efb90c7c2545da47ad07ecf5325399274a3b682`
(see `GIT_COMMIT_v323.txt` after the final commit).
**Formal 60 samples:** not started. No formal SampleRunID executed.

Status vocabulary: DESIGNED → IMPLEMENTED → COMPILED → UNIT_TESTED →
PILOT_RUN → PROPAGATION_VERIFIED.

---

## 1. run_pilot address matching (fixed)

The address-event list was initialized **after** the A01/A03 branch, wiping the
events that had just been read. It is now initialized before the branch.

A03 R01–R05 were re-run and all five have the same causal evidence:

| Context | Last injection dyn seq | Injected address | Page Table Fault address | Result |
|---|---:|---|---|---|
| R01 | 1146 | 0xffffffffffb73c50 | 0xffffffffffb73c50 | DIRECT_ADDRESS_MATCH |
| R02–R05 | 1146 | 0xffffffffffb73c50 | 0xffffffffffb73c50 | DIRECT_ADDRESS_MATCH |

The Page Table Fault address is parsed from stderr and written into a structured
`simulator_abort` event and `terminal_evidence` in pilot_meta; it is no longer
stderr-only. `FAULT_CAUSALITY = DIRECT_ADDRESS_MATCH` is recorded for all five.

A01-R01: Page Table Fault address is `0` and the injected address is
`0x7ffffefda8`; observed terminal stays CRASH but causality is
`TEMPORAL_ASSOCIATION_ONLY`. FW02-R02: PT address `0x409c80`, load address
`0x496798`, also TEMPORAL_ASSOCIATION_ONLY. Neither claims the fault caused the
crash. `accepted` now explicitly means "record validity", not causation.

## 2. A01-R03 terminal (fixed)

The target injection is dyn seq 169. The trace contains
injection → address_formed → memory_request → **squash (seq 169)** and no
memory_response, register_writeback or commit for that sequence. The terminal is
now **SQUASHED** with reason `TARGET_SQUASHED_NO_COMMIT`, consistently in the
JSONL summary, pilot_meta and the sweep. It is no longer UNRESOLVED merely
because a data value is absent.

## 3. PropagationCoverage (fixed)

Coverage is judged against a per-(model, terminal) expected profile; a single
stage no longer makes it COMPLETE. Missing required stages → PARTIAL; no stages
→ NONE. Profiles cover A01 (MASKED/SQUASHED/CRASH/SDC), A03
(CRASH/SQUASHED/MASKED), FW02 (MASKED/CRASH/SDC), SQ01
(MASKED/SDC/CRASH). `RecordIntegrity`, `TraceCompleteness` and
`PropagationCoverage` are judged independently (a validation/summary reason no
longer downgrades coverage; a TRIGGERED run without an injection stays
TraceCompleteness=INCOMPLETE while coverage can still be COMPLETE).

## 4. Replay commit (fixed)

Replay-tracked dynamic instructions now register for a real commit node. The
replay pilot (`pilots_v3_2_3/REPLAY-RW01`) has all five replays with an
independent final-result node:

| dyn seq | attempt | gen | final | commit_seq |
|---|---:|---:|---|---:|
| 69296 | 2 | 1 | COMMITTED | 62176 |
| 71973 | 2 | 1 | COMMITTED | 63557 |
| 72305 | 2 | 1 | COMMITTED | 63787 |
| 70968 | – | – | SQUASHED | – |
| 70969 | – | – | SQUASHED | – |

The original v3.2.2 replay data is preserved under `pilots_v3_2_2/`; the new run
is in `pilots_v3_2_3/REPLAY-RW01`.

## 5. R01–R05 semantics

A03/F5 R01–R05 are five different activation start positions of one continuous
stuck-at condition; after activation the condition continues to apply to every
eligible load. They are **not** five independent single injections. FW02 R01–R05
remain different store→load dynamic pairs. This wording is now used in the
reports; the original SampleRunID/SubTaskID/Seed are unchanged.

## 6. Fifteen-context result (final binary)

`pilots_v3_2_3/sweep/context_sweep_summary.json`: **15/15 recorded, 15/15
accepted**.

| Model | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| A01 | CRASH / TEMPORAL | MASKED | SQUASHED (169) | MASKED | MASKED |
| A03 | CRASH / DIRECT_ADDRESS_MATCH ×5 | | | | |
| FW02 | MASKED | CRASH / TEMPORAL | MASKED | MASKED | MASKED |

## 7. SQ01 (started, first of the nine)

Status: **IMPLEMENTED / COMPILED / UNIT_TESTED / PILOT_RUN**.

- Unique fault: SQ entry byte0 bit3 flip after `LSQUnit::write()` copies the
  store data into the entry.
- Real hook: `lsq_unit.cc::write` → `CHAOSLSQFwd::maybeCorruptStoreData`;
  config `--lsq_struct_mode sq01_bit3` with the existing F0 trigger args.
- Trace: `inj_store_data` → JSONL `injection` with `unit=SQ`,
  `sub_unit=store_data`, old/new byte, SQ index and entry generation; the store
  is registered for its real commit node. Coverage profile injection →
  sq_lifecycle.
- Safety: data-only; entry/request/state/pointers untouched; one fault; no
  state-machine change.
- Pilot: 5/5 accepted, one injection each, `all_store_bit3=true`, observed and
  final MASKED, `fault_causality=DIRECT_DATAFLOW_EVIDENCE`, coverage COMPLETE.
  The injected byte is overwritten by a later store in this workload, which is
  why the oracle still passes; this is recorded, not hidden.
- Raw JSONL is 189 MB per context; it is kept on disk and in the delivery zip
  with sha256 sidecars, but excluded from Git (GitHub 100 MB limit).

## 8. Remaining eight models (workstream B audit)

Audited with file:line evidence; **0/8 implemented**. See
`LSU_Remaining_Models_Audit_v3.2.3.md`. Safety verdicts: DA04/LP01/FW05
safe-with-bound, SQ03/SP05/MD04/RP01 safe-with-bound (one-shot + watchdog),
**LQ04 HIGH-RISK as specified** (assert/use-after-free chain). Recommended
order after SQ01: DA04 → LP01 (fix the existing size<8 OOB first) → MD04 →
FW05 → SQ03 → SP05 → LQ04 → RP01. Public trace interface was not changed by the
audit; models will write into the existing node kinds.

## 9. Warm-up / ROI

Unchanged from v3.2.2 and still `NEEDS_RESEARCHER_CONFIRMATION`:
libc startup outside ROI, W2 guard loop as oracle, W5 checksum read outside ROI,
R01–R05 at 10/30/50/70/90 % of the ROI. No Excel edit; no formal run.

## 10. Delivery

`LSU_v3.2.3_Propagation_Closure_Package.zip` contains the git log/diff, source
patch, updated platform source/tests, build logs, fixed A01/A03/FW02 traces and
sweep, replay evidence, SQ01 pilot evidence (including the large JSONL), the
trace schema and validator, the current final Excel, and this report + audit.
All historical versions and the original 60 sample IDs/seeds are preserved.
