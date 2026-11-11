# LSU 12-Model Pre-Formal Acceptance Report (v3.3.0)

Date: 2026-11-11 · Branch `lsu-preformal-v3.3.0-20261111` (base
`lsu-platform-v3.2.12` @ `9e3d104c`, HEAD `c1846ae4`).
Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`.
Scope: the researcher's 2026-11-11 decision — **12 models × R01–R05 = 60
contexts only**; the 74-model/4075-sample baseline is out of scope.

## Verdict

**`12_MODEL_FORMAL_READY = NO` — `NOT_READY` for a formal campaign.**

The 12 models are implemented and their evidence layer is substantively
audited, and four source-level evidence/control defects were fixed and
verified on the final binary. But three hard gates remain open: warm-up/ROI
(and therefore the frozen EventOrdinal values), matched controls for 42/60
contexts, and final-binary reproducibility for 45/60 contexts. Reporting
`READY` would require exactly the substitutions this round forbids.

## 1. What changed this round (real, committed, verified)

| Commit | Change | Verification on final binary `d3807fbe…` |
|---|---|---|
| `5541648c` | A01 matched-control probe (golden EA, ptag-0 nodes); FW05 `fw05_reload` observation; A03 `a03_fault` crash-address link from translation-finish faults | `V33F-A01-C02` control_valid=true; `V33F-A03-R01` a03_fault fault_va `0xffffffffffb73c50` == actual_ea, matches=1; `V33F-FW05-R02` fw05_reload load_seq=12093 reload_seq=50512 |
| `364a6057` | FW02 F6 decision honours `probability<=0` (fixes the `SUPP-FW02-C01` misfire) | `V33F-FW02-C01` control_valid=true, misfire=false; p=1.0 fault still suppresses |
| `c8fc4353` | RP01 records the real squash `triggering_seq` | `V33-RP01-R02` triggering_seq=87/110/237, `triggering_seq_recorded=1`; exit 0 |
| `c1846ae4` | W4 load-preserving implementation **proposal** (`sq_forward_v33`, 10 loads/12 stores in main) | FW02 R01 on it: fw02_decision load_seq=258/store_seq=248, suppressed, memory_path=1; p=0 control valid |

Regression: `pytest tests/` **180 passed**; platform tests **107 passed**;
`scons -j126 build/ARM/gem5.opt` exit 0, no new warnings; no gem5 campaign
was launched.

Binary provenance: root `build/ARM/gem5.opt` =
`d3807fbe…` (final, carries the A03 0/0-match guard); the earlier candidate
`f43c5ddf…` produced the first A03 link but lacked that guard. Both are
recorded in `LSU_v3.3_BINARY_PROVENANCE.md`.

## 2. Required metrics

**12/12 models source and injection semantics.** Implemented and audited:
SQ01/SQ03/LP01 CONFORMING; A01/A03/FW05/DA04/SP05/LQ04/MD04/RP01 MINOR_RISK
(observation/control gaps, not semantic failures); FW02 MAJOR_RISK before
this round's guard, fixed in `364a6057`. 0 UNIMPLEMENTED.
`LSU_12Model_Source_Hook_Audit.csv`.

**60-context readiness (final adjudication).**

| Status | Count |
|---|---:|
| READY | **0** |
| PARTIAL | 3 |
| BLOCKED | 35 |
| DESIGN_CHANGE_REQUIRED | 22 |

For comparison, the evidence-only grade before the formal gates is
13 READY / 30 PARTIAL / 17 DESIGN_CHANGE_REQUIRED. The difference is the
unfrozen warm-up/ROI (no context can be formally READY) plus missing
controls/final-binary evidence. See `LSU_60Context_Readiness_Matrix.csv`
(columns `EvidenceStatus_AgentA`, `MatchedControlValid`,
`CurrentBinaryEvidence`, `WarmUpGate`, `FinalStatus`).

**60 fault dynamic events.** All 60 have an injection/attempt record on some
binary. Only 5 fault contexts and 2 controls were re-executed on the v3.3
binary; 45/60 remain historical-only (two source binaries no longer exist on
disk). With `WarmUp=0`, the frozen ordinals 1–5 select startup events
(A01 seq 48 PC 0x400ad0; FW02 stack pair 0x7ffffefbd0), so "event exists" is
not "designed event is selected".

**Fault/Control pairing.** 18/60 valid matched controls; 42 missing; the one
historical misfire (FW02-C01) is fixed in code and re-verified. Control
validity is never inferred from `--probability 0.0` alone.

**Workload golden.** W1–W8 final-binary baselines 9/9 PASS (exit 0 + oracle
checksum) — but note that the SPDX baseline used binary `68c6ce73…`; W4 is
DESIGN_CHANGE_REQUIRED because the frozen ELF cannot execute its designed
pair; 6 workloads PARTIAL on trigger/ordinal evidence; W8a/W8b READY.

**Propagation closure.** 47/60 complete evidence (31 frozen exception
conjunctions + 14 frozen prior + 2 generic), 9 PARTIAL, 2 LIFECYCLE_ONLY,
2 UNRESOLVED. Terminal distribution: MASKED 25, SDC 16, SQUASHED 8, CRASH 7,
HANG 3, UNRESOLVED 1. Oracle: PASS 21, FAIL 14, MISSING 22,
NOT_APPLICABLE 3. No rule was relaxed; PARTIAL stays PARTIAL.

**SDC / MASKED / SQUASHED / CRASH / HANG distribution.** As above; expected
terminals are preserved per model (SQ01/SP05 SDC, SQ03 MASKED, LQ04 MASKED,
RP01 HANG on R01/R04/R05, A03 CRASH, A01 MASKED on the wrong-EA contexts).

**Binary / config / seed / ROI freeze.** Binary candidate is frozen
(`d3807fbe…`, full SHA in the provenance file), but `ConfigFrozen=NO`, the
workbook `gem5Commit` is stale (`6f98088a`, an ATLAS commit), warm-up/ROI and
EventOrdinal are not approved, and the runner has no `--dry-run`. Seeds and
SampleRunIDs are unchanged (60/60 unique, identical to v3.2.6/v3.2.7).

**Remaining formal blockers.** See `LSU_Final_Blockers.md` B1–B9.

## 3. Priority-model outcomes

- **FW05** — Native register consumer chain proven on the v3.3 binary
  (`inj_fw05` alt-store hash `a06ea71b…` → `taint_reg` → consumer seq 12094
  → commit 5798, hash-equal). The new `fw05_reload` node exists but reads
  neither store hash (0/0), so a store→reload edge is **not** proven; the
  frozen v3.2.11 import remains the only complete FW05 verdict.
- **A01** — Control now records golden EA/Request/Response (ptag-0, no
  injection); control_valid. R01 crash remains UNRESOLVED (panic VA 0);
  R02/R04/R05 wrong-EA MASKED remain the complete contexts; R03 PARTIAL
  (discard companion).
- **RP01** — `triggering_seq` fixed; R02/R03 squashes are honestly
  `fault_tracked=0 / squash_cause=unrelated` and stay PARTIAL. HANG R01/R04/
  R05 retain watchdog + truncated traces; never relabelled MASKED.
- **A03** — Native crash link now on-chain (fault VA == stream actual EA,
  5/5 contexts); persistent stuck-at semantics and STUCK_APPLIED/
  ALREADY_STUCK were already correct; TRUNCATED stays honest.

## 4. Platform and resources

`lsu_guard.py gate`: ok=true; disk free 65.9 GiB (20 GiB redline);
MemAvailable 25.7 GiB; 0 gem5 processes. Host 126 cores. These are not
blockers.

## 5. Shortest path to READY (approval-dependent)

1. Researcher approves warm-up/ROI boundaries and converted EventOrdinals
   for the 60 rows (B1).
2. Researcher approves the W4 ELF replacement (c1846ae4) and the
   SQ01/SQ03/SP05 workload-row reconciliation (B4/B5).
3. Generate the 42 missing matched controls and re-run all 60 fault +
   control pairs on one frozen binary under the approved ROI (pre-formal,
   ~120 short SE runs).
4. Freeze `ConfigFrozen=YES`, add a runner dry-run, and update the audit
   workbook fields without touching SampleRunID/Seed semantics.

Until then the honest status is **NOT_READY**, with the four fixed
mechanisms and the audited evidence layers ready to be reused.
