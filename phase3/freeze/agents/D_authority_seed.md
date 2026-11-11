# Agent D — Authority + Seed Freeze Report

Date: 2026-11-12 (freeze decision dated 2026-11-11)
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2`
Status: all tasks + two coordinator corrections complete. **Nothing committed**
(Main integrates and commits per unit). No gem5/scons run; no C++/workload
edits; the design package is untouched.

## 1. Files created

| Path | SHA256 |
|---|---|
| `phase3/freeze/authority/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx` | `aa304e63b6b1e4c404d9de5a08f91363fdb241e34e69d9d756bb4cc4186df0f6` |
| `phase3/freeze/authority/MMU_40_Sample_Matrix.csv` | `a8a084eb67cef6a5289b112831c84bf7d0760d9ca9c43b3086715cb5d9d8b5ea` |
| `phase3/freeze/authority/MMU_Formal_Config.json` | `0dae8d3113d420b9dba0056ad52f3657e06a6ddcd52a86fd1df1f5a8f199329f` |
| `phase3/freeze/authority/MMU_Formal_Config.yaml` | `5a799fd5e2ae3f1f5bd112e983d7c743faebcf1a0dc2565eb9c17221ab5d6c70` |
| `tools/mmu_formal_freeze_authority.py` | freeze generator (read-only source) |
| `phase3/freeze/MMU_Seed_Semantics_Audit.md` | audit with per-source evidence |
| `phase3/freeze/evidence/preflight_frozen/` | preflight CSV/MD/seed report + JSON |
| `phase3/freeze/agents/D_authority_seed.md` | this report |

`sha256sum phase3/freeze/authority/*` gives the current values; self-check `ok: true`.

## 2. Frozen workbook verification (openpyxl, real output)

```
sheets: 00_Readme ... 15_Diagnostic_Feature_Schema, 16_Freeze_Record (all preserved)
07_Sample_Matrix: 41 rows x 27 cols (40 data + header)
header tail: ['OracleMethod','SeedPolicy','SeedSource','SampleFreezeStatus']
Seed='N/A_DETERMINISTIC' number_format='@'; SampleIDStatus='FROZEN';
SeedPolicy='DETERMINISTIC'; SeedSource='RESEARCHER_APPROVED';
SampleFreezeStatus='FROZEN' for all 40 rows
models M01..M08 each 5; contexts R01..R05 each 8; 40 unique IDs;
unique_seeds: ['N/A_DETERMINISTIC']; stale-string scan: []
```

Consistency edits recorded in `16_Freeze_Record`: `00_Readme!B13/B14`,
`09_Trace_Configuration!D3`, `11_Acceptance_Checklist!D12/D13`,
`12_Blockers!B10` -> RESOLVED, appended `13_Change_Log` v2.0-freeze row.
Historical wording is retained and explicitly marked superseded.

Original package unchanged (matches its own MANIFEST):
xlsx `4f2833614dec99ec20a336bb42ee4cdcd576b8eb82c06331c507777fef967e9d`,
csv `2c60bcfb7922c0ad9ff59f399b1c3afa035ccb6117a7615df5d6ef4fdb364765`.

## 3. Seed / authority semantics (preflight + runner)

* `N/A_DETERMINISTIC` is valid iff `SeedPolicy=DETERMINISTIC`; never parsed as
  int, never passed to gem5. Numeric seed + DETERMINISTIC, or literal +
  random policy -> `BLOCKED_SEED_POLICY`.
* `SampleIDStatus=FROZEN` accepted; unfrozen still refused.
* Default inputs: explicit `--excel/--csv` override > frozen authority >
  design package. A present-but-broken frozen directory raises instead of
  silently falling back.
* Runner hard guard: any `--*seed*` token in the gem5 command raises
  `BLOCKED_SEED_POLICY`; `--describe` reports `seed-flag args: []`.

## 4. Preflight Gate 3 — runtime evidence is now part of PRIMARY

Implemented order (documented in the module docstring and used by the CSV
`PrimaryStatus`/`AllBlockers`):

1. no pilot evidence / `RuntimePilotEvidenceStatus != PASS` -> `BLOCKED_TRACE`
2. `TerminalState=TRACE_INCOMPLETE` -> `BLOCKED_TRACE`
3. `PropagationEvidenceStatus=PARTIAL` -> `BLOCKED_TRACE`
4. `FaultActivationEvidenceStatus=NO_ELIGIBLE_EVENT` or `NOT_ACTIVATED`
   -> `BLOCKED_HOOK` (no current sample has a knowably-wrong target, which
   would be `BLOCKED_CONTEXT`; the detail says so)
5. propagation `NOT_RUN`/`NOT_OBSERVED` -> `BLOCKED_TRACE`
6. `OracleResult=NOT_OBSERVED` or terminal not in the sample's expected
   terminal set -> `BLOCKED_ORACLE`
7. independent control oracle missing -> `BLOCKED_ORACLE`
8. ACTIVATED + admissible terminal + complete trace + independent control
   -> `READY`

Build provenance is checked first: `BLOCKED_BINARY` / `BLOCKED_SOURCE`
precede all static blockers when a `sample_manifest.json` hash disagrees with
the frozen formal config. While the config says `PENDING_MAIN_BUILD` the
comparison is reported as `PENDING`, never PASS.

Real preflight result against the frozen authority (no gem5):

```
primary_counts: {"BLOCKED_TRACE": 23, "BLOCKED_HOOK": 4, "READY": 13}
all_blocker_counts: {"BLOCKED_TRACE": 23, "BLOCKED_HOOK": 4}
BinaryProvenanceStatus: PENDING x40; SourceProvenanceStatus: PENDING x40
seed_gate_fail_count: 0; triple_issues: []
authority.excel_source/csv_source: FROZEN_AUTHORITY
```

The 4 `BLOCKED_HOOK` rows are the `NO_ELIGIBLE_EVENT` samples:
`M06-R02`, `M07-R02`, `M07-R03`, `M07-R05`. The 23 `BLOCKED_TRACE` rows are
4+4 M01/M02 NOT_RUN pilots, 4 M03 PARTIAL, 5 M05 PARTIAL/TRACE_INCOMPLETE,
3 M06 PARTIAL/TRACE_INCOMPLETE, and 3 M08 PARTIAL/TRACE_INCOMPLETE. This is
the honest Gate-3 result; the earlier 40/40 READY was false.

Runtime evidence columns remain in the CSV (`RuntimePilotEvidenceStatus`,
`FaultActivationEvidenceStatus`, `FaultConsumptionEvidenceStatus`,
`PropagationEvidenceStatus`, `TerminalOracleStatus`, `TerminalState`,
`OracleResult`) plus the new `RuntimeEvidenceStatus`/`RuntimeGateDetail`.

## 5. Coordinator correction 2 — build provenance in the formal config

`MMU_Formal_Config.json/.yaml` now carry, as `PENDING_MAIN_BUILD` placeholders:

```
provenance_status: PENDING_MAIN_BUILD
gem5_sha256: PENDING_MAIN_BUILD
gem5_binary: CHAOS/gem5/build/ARM/gem5.opt
source_sha256:
  CHAOS/gem5/src/arch/arm/mmu.cc: PENDING_MAIN_BUILD
  CHAOS/gem5/src/arch/arm/table_walker.cc: PENDING_MAIN_BUILD
  CHAOS/gem5/src/arch/arm/table_walker.hh: PENDING_MAIN_BUILD
  CHAOS/gem5/src/arch/arm/tlb.cc: PENDING_MAIN_BUILD
workload_sha256: {W9,W10,W10S,W11,W12,W13,W14}: PENDING_MAIN_BUILD
workload_variant: {M06/R02: W10S-COLD-STORE, M08/R05: W10S-WARM-STORE}
```

The preflight gate was verified with a temporary repo:
matching manifest -> PASS; binary mismatch -> `BLOCKED_BINARY` primary with
`AllBlockers=BLOCKED_BINARY;BLOCKED_HOOK;...`; source mismatch ->
`BLOCKED_SOURCE` primary; PENDING config -> `PENDING`; no manifest ->
`NO_MANIFEST` (not blocked). No hash was fabricated.

## 6. Coordinator correction 1 — runner manifest + stale-verdict race

`tools/mmu_formal_runner.py`:

* `build_plan()` hashes the gem5 binary, the four MMU sources and the run
  workload before launch and puts `gem5_sha256`, `source_sha256`,
  `workload_binary`, `workload_sha256`, `workload_variant` into the plan and
  every `sample_manifest.json` (also into `SHA256/SHA256SUMS.txt`).
* `execute_plan()` re-hashes them immediately before launch and fails closed
  (`BLOCKED_BINARY`/`BLOCKED_SOURCE`/`BLOCKED_WORKLOAD`) if anything changed.
  Unit-tested: binary mismatch -> `BLOCKED_BINARY 5`, outdir not created.
* After gem5 exits, `wait_for_stable_file()` requires `prop_evt.txt.gz` (and
  `prop_trace.csv.gz` when present) size+mtime to be identical across two
  consecutive checks. Validation is skipped and `trace_read_error` recorded if
  the trace never stabilises. A truncated/EOF validator read triggers one
  stability re-check and one re-validation; a persisting error is recorded and
  the runner returns 6. Unit-tested with a concurrent writer and an
  `EOFError: compressed file ended...` log.
* Control oracle is now resolved for BOTH formal and pilot runs from the
  preflight mapping, or from explicit `--control-run`; `control_oracle_sha256`
  and `control_oracle_source` (PREFLIGHT_RESOLVED / EXPLICIT_OVERRIDE) are
  recorded in the manifest and in `--describe`.

Real `--describe` provenance (frozen sample `M06-F0-W10-S01-R01`, exit 0):

```
gem5_sha256 = 3ec51b2cbfe1cbd743862eb4b260bb05da9bebc3b8e63e75578662b2ad3359e6
              (first run; the binary was being rebuilt concurrently, later
               reads were de00725d.../f589a6fa..., mtime 00:23. Re-run after
               the Main build is frozen; never reuse a stale value.)
source_sha256: mmu.cc e4006c04..., table_walker.cc 54dbeeff...,
               table_walker.hh 89110e20..., tlb.cc 1b7cc0f3...
workload_binary = workloads/mmu_rev/W10/Binary/mmu_w10
workload_sha256 = 4a3367107c0d6778677d22d9bfb90dcea3ce60ca33e47dd45a6ce75d3494d5e7
control_oracle_source = PREFLIGHT_RESOLVED
control_oracle_sha256 = 9e7d7a84866c739229fb692498e9b8464ff75531ab04e193bc1b66827df480b5
seed = N/A_DETERMINISTIC, seed_policy = DETERMINISTIC,
seed_source = RESEARCHER_APPROVED, seed_used_by_gem5 = false
seed-flag args: []
```

Pilot regression: `--pilot TEST-PILOT-D ... --describe` -> exit 0, READY,
control oracle resolved (`ec3ca4f3...`), `seed_status=PILOT_NO_SEED`.

Negative seed fixtures (temp copies, explicit override): numeric+DETERMINISTIC
-> BLOCKED_SEED_POLICY (exit 3); literal+RANDOM -> BLOCKED_SEED_POLICY;
PROPOSED_NOT_FROZEN -> BLOCKED_SAMPLE_ID_NOT_FROZEN (exit 5);
NEEDS_AUTHORITATIVE_EXCEL -> BLOCKED_MISSING_SEED (exit 3). Explicit original
package override is labelled DESIGN_PACKAGE_ORIGINAL and still reports 40
unfrozen/40 missing.

## 7. Seed-semantics audit result

`phase3/freeze/MMU_Seed_Semantics_Audit.md` has the per-source table. Key
facts: `lsu_b0_fs.py` has no seed/random token and execs `arm_chaos_fs.py`;
no `--seed` CLI; legacy `--*_rng_seed` (fixed 20260825) belongs to injectors
the MMU runner never mounts; stdlib caches DO attach `StridePrefetcher`
(correcting the earlier audit) but it has no RNG call; replacement is LRURP;
default BP is TournamentBP (no RNG); the only reachable global-RNG consumer is
the O3 fetch SMT pick at fixed seed 5489 with `num_cores=1` (range 0..0);
checkpoint/restore is fixed; workloads are static ET_EXEC with fixed
`MAP_FIXED` VAs and no rand/time calls. **No nondeterministic source found.**

## 8. Remaining blockers / handoff

1. Gate 3: 23 BLOCKED_TRACE + 4 BLOCKED_HOOK remain (listed above). They are
   real evidence gaps, not seed/authority problems.
2. `PENDING_MAIN_BUILD` placeholders must be filled by Main (preflight
   truthfully reports PENDING, never PASS). The gem5 binary was being rebuilt
   during verification (hash changed across runs, mtime 2026-11-12 00:23);
   Main must freeze it first, then record the final hash. The runner's
   plan-vs-execution check refuses a changed binary with `BLOCKED_BINARY`.
3. Main integrates and commits per unit: (a) freeze generator + authority
   outputs, (b) preflight seed/authority/runtime/provenance gates, (c) runner
   seed/provenance/stability/control-oracle changes, (d) audit + this report.
4. `tools/mmu_formal_validate.py` was audited; no change needed.
