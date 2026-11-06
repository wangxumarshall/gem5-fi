# LSU Implementation Status v3.2

**Updated:** 2026-11-06
**Branch:** `lsu-platform-v3.2` (worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2`)
**Base commit:** `6f98088a7144d7f6fb22d985be3023ac5658e71b`
**Environment:** native AArch64, openEuler 24.03, gcc 12.3.1, Python 3.11.6, SCons 4.5.2, gem5 v25.1.0.1 (vendored upstream `62c7bf2848`)

## Gate 1 — Common base

| Component | Status | Real evidence |
|---|---|---|
| Config parser | PASS | v3.1 input: 255 deficits correctly rejected; v3.2 workbook: `samples=60 models=12 seeds=60 workloads_present=60`, strict exit 0 |
| Run manifest | PASS | `tests/test_manifest_oracle.py`: 5 passed; seed copied from Excel (`2108120075`), binary SHA present |
| Oracle interface | PASS | same test file: PASS/FAIL/MISSING cases |
| F0/F5/F6 manager | PASS | `tests/test_fault_manager.py`: 7 passed, including F5 `nochange` accounting and F6 named trigger |
| Trace v3.1 schema/writer | PASS | `LSU_Trace_Schema_v3.2.json`; writer emits all 39 event fields |
| Trace validator | PASS | `LSU_Trace_Sample_v3.2.jsonl` → `VALID` |
| Completeness checker | PASS | sample → `COMPLETE`, `terminal_state=MASKED`, 4 events / 3 edges |
| Trace summary | PASS | `logs/trace_sample_summary.json` |
| Terminal classification | PASS | `tests/test_terminal.py`: 7 passed; incomplete trace returns `terminal_state=None`, never `MASKED` |
| Full unit suite | PASS | `logs/gate1_tests.log`: **35 passed** |

**Gate 1 verdict:** the common-base components are implemented and unit-verified.
The frozen v3.1 workbook was **not** a complete run configuration (255
validation errors); the repaired v3.2 workbook now passes strict validation
with all 60 paths, SHAs and oracles present.

## Frozen-workbook deficits (input, not silently defaulted)

From `logs/config_v31.json`:

| Field | Count | Meaning |
|---|---:|---|
| `WorkloadPath` | 45 | W2-W8 rows are `ABSENT` |
| `BinarySHA256` | 45 | `N/A` on the same rows |
| `Oracle` | 45 | `N/A` on the same rows |
| `WarmUp` | 60 | `NEEDS_CONFIG（工作负载专属warm-up）` |
| `ROI` | 60 | `NEEDS_CONFIG（工作负载专属ROI）` |

The parser exits 2 in strict mode on this frozen input and lists every
affected SampleRunID. The v3.2 repair does **not** claim these were present in
v3.1: it sets `WarmUp=0` and `ROI=full workload` as explicit v3.2 platform
choices and records that provenance in the new `v3.2_ConfigProvenance` column.

## Gate 2 — Workloads and pilots

**Status: PASS for the three pilots.** Details are in
`pilots/GATE2_REPORT.md`; every number below comes from the committed run
artifacts.

| Item | Real result |
|---|---|
| Build | `build/ARM/gem5.opt` SHA256 `b233a4cb…eaabe`, zero-error build after the duplicate-declaration fix |
| W1-W8 baselines | 8/8 exit 0, 8/8 oracle PASS, re-run under the Gate-2 binary |
| W6/W8 repair | guard-page probe: original offsets SIGSEGV (139), fixed offsets `NO_FAULT` (0); new goldens and SHAs |
| A01/F0 | `pushRequest`, `injected=1`, `old=0x7ffffefdc0 → new=0x7ffffefdc8`, 12 events / 10 edges, MASKED, oracle PASS |
| A03/F5 | `pushRequest`, `injected=146` (all eligible loads), first change `db8 → db0`; persistent condition causes a real page-table crash (`TERMINAL=CRASH`); 564 events / 489 edges, 73 injections |
| FW02/F6 | 6 real full-coverage pairs, 1 suppression (`load_seq=397`, `store_seq=383`); 4 events / 3 edges, MASKED, oracle PASS |

A03 is accepted as a real F5 trigger with `TerminalState=CRASH`; it is not
counted as Masked or SDC. Its gzip stream lacks a trailer because gem5
aborted, but every flushed node is present and a terminal `simulator_abort`
event is appended; `TraceCompleteness=COMPLETE` to that observed terminal.
Gate 3 (remaining nine models) and Gate 4 (60 formal samples) are not
started.

## Workbook v3.2

`gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.xlsx` was generated from the
frozen v3.1 workbook. All 60 SampleRunIDs and all 60 seeds are byte-preserved.
Every row now has a real workload path, real rebuilt-binary SHA256 and real
golden oracle. The strict parser run is:

```
CONFIG_OK samples=60 models=12 seeds=60 workloads_present=60
```

Log: `logs/config_v32_validation.log`. The legacy `TerminalState` /
`TraceCompleteness` columns are renamed `*_LEGACY_DEPRECATED` and cleared;
only `TerminalState_v31` / `TraceCompleteness_v31` remain. Formal rows are
`ExecutionStatus=NOT_RUN`; the three pilot models are `PILOT_VERIFIED_FORMAL_NOT_RUN`,
the other nine are `BLOCKED_GATE3_NOT_STARTED`. No formal sample is marked
READY or PASS.

## Rejected pre-existing artifacts

The artifacts found in the main checkout at 2026-11-06 09:43-09:45 are in
`preexisting_rejected/` and are not used. Reasons:

1. A01 was injected at `sendFragmentToTranslation`, which the v3.1 source audit
   explicitly rejects (the audited hook is `LSQ::pushRequest`).
2. A03 recorded `injected=0`, so it cannot be a passing F5 pilot.
3. The bundled trace writer omits required v3.1 fields and its classifier can
   report `MASKED` for an incomplete trace.

## Next actions

1. Gate 3: implement and unit-test the remaining nine models (LQ04, SQ01,
   SQ03, LP01, SP05, FW05, MD04, RP01, DA04); LQ04/RP01 need the documented
   safety review first.
2. Gate 4: only after Gates 1-3 pass and the researcher confirms, run the 60
   formal samples with the frozen seeds.
3. The v3.2 workbook repair is complete; no further workbook edit is needed
   before Gate 3.
