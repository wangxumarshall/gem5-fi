# LSU v3.2.5 — LP01 Implementation Package

**Date:** 2026-11-08
**Branch:** `lsu-platform-v3.2.5` (base `lsu-platform-v3.2.4` @ `d4b8276e`)
**Binary:** `69a1ca9c5b1cbfb160d0502a8cad8acf7d17101625228978ec79ede588b2287d`
**Scope:** LP01 implementation + five W5 pilots + the nine v3.2.4 DA04
trace/document corrections. **No 60-sample formal run.**

## Contents

| Path | What it is |
|---|---|
| `LP01_Source_Audit_v3.2.5.md` | hook mapping, payload semantics ruling, size matrix |
| `LP01_Implementation_Report_v3.2.5.md` | code changes and hook order |
| `LP01_PILOTS.md` | five pilots: hashes, writeback, consumer, commit, oracle, terminal |
| `LP01_EVENT_SELECTION.md` | Excel vs clinical ordinal, actual dyn seq/tick/address |
| `LP01-R01..R05/` | per-pilot manifest, command, logs, JSONL, oracle |
| `LP01_TRACE_HASH_EVIDENCE.txt` | extracted before/after/writeback/consumer hashes |
| `LP01_Payload_Size_Tests.txt` | real unit-test output |
| `LSU_v3.2.5_DA04_Trace_Fix_Evidence.md` | R04/R05 rerun; request-time retraction |
| `DA04_PILOTS.md` (corrected) | R04 count 1,009; R05 checksum; retraction banner |
| `DA04_BINARY_PROVENANCE.md` | five manifests agree on `3e9148fc…` |
| `LSU_v3.2.5_SE_Address_Semantics.md` | SE has no PA |
| `LSU_v3.2.5_Status_Report.md` | full status + state ladder + remaining problems |
| `MODEL_STATUS_MATRIX.csv` | 12-model matrix (LP01 verified; DA04 verified bit retracted) |
| `LSU_v3.2.5_Gate_Report.md` | build/unit/regression gate |
| `build_v325_lp01.log` | build log |
| `LSU_v3.2.5_Git_Diff.txt`, `GIT_COMMIT_v325.txt` | provenance |
| `REMAINING_ISSUES.md` | open problems, explicitly not hidden |

## Status ladder

- LP01: DESIGNED / SOURCE_AUDITED / IMPLEMENTED / COMPILED / UNIT_TESTED /
  PILOT_RUN / PROPAGATION_VERIFIED (chain-level, all five MASKED).
- DA04: model unchanged; **R04/R05 SDC retracted** under request-time
  causality → UNRESOLVED; `PROPAGATION_VERIFIED` bit set to 0.
- All other models unchanged from v3.2.4.

## Integrity

The package checksum is `LSU_v3.2.5_LP01_Implementation_Package.zip.sha256`
in the repository root.
