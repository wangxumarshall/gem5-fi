# MMU Formal Preflight Report (no gem5 launched)

Date: 2026-11-12  
Frozen binary: `a71ce0ca21de143d9aa5ab05e29d9bee86dff213576941a3191a256f1d842024`  
Authority: `phase3/freeze/authority/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx`
(40 FROZEN SampleRunIDs, Seed `N/A_DETERMINISTIC`, SeedPolicy DETERMINISTIC)  
Evidence index: `phase3/formal/evidence_index.json` (real pilot runs only)  
Raw preflight: `phase3/freeze/evidence/preflight_final/MMU_40_Sample_DryRun.csv`

## 1. Result

| Metric | Value |
|---|---|
| Samples checked | 40 |
| SampleRunID uniqueness / triple issues | 40 unique, 0 triple issues |
| Seed gate failures | 0 (all 40 literal `N/A_DETERMINISTIC`, policy DETERMINISTIC) |
| **READY** | **18** |
| BLOCKED_BINARY | 19 |
| BLOCKED_TRACE | 3 |
| BLOCKED_SOURCE | 0 |
| BLOCKED_HOOK / BLOCKED_CONTEXT / BLOCKED_ORACLE | 0 in the primary column (M07 R03/R05 are blocked by binary provenance first; their runtime status is NO_ELIGIBLE_EVENT) |

`MMU_FORMAL_READINESS = **PARTIAL**` — **not** READY.

## 2. READY contexts (18)

- M05 R01–R04: SDC/FAIL (real partial-walk-cache hit on the substituted base,
  alias consumer observed the decoy sentinel).
- M06 R01–R05: DETECTED_CONTAINED / PASS_EXPECTED_DETECTION.
- M07 R01, R02, R04: SDC/FAIL.
- M08 R01–R05: R01/R05 SDC/FAIL; R02–R04 SQUASHED/PASS.

## 3. Per-model status

| Model | Ready | Readiness | Primary blockers |
|---|---|---|---|
| M01 | 1/5 (R02) | PARTIAL | R01/R03/R04/R05 historical binary `bea5f813`/`3ec51b2c` |
| M02 | 0/5 | BLOCKED | R02 NO_ELIGIBLE_EVENT (M02 old_pfn hardcoded 0x83480 vs actual 0x834b6); R01/R03–R05 historical binary |
| M03 | 0/5 | BLOCKED | all five on `6dca2195`/`3ec51b2c`, not frozen `a71ce0ca` |
| M04 | 0/5 | BLOCKED | all five on `3ec51b2c`, not frozen `a71ce0ca` |
| M05 | 4/5 | PARTIAL | R05 Execute trace incomplete (no fetch transaction) |
| M06 | 5/5 | READY | — |
| M07 | 3/5 | PARTIAL | R03 PROT_NONE = Translation fault; R05 PROT_NONE fetch unreachable as a distinct M07 case |
| M08 | 5/5 | READY | — |

## 4. What the preflight actually checks

Static: authoritative triple, hook site in real C++, workload assets,
context identity, config flags, trace validator support, oracle definition,
output collision, seed policy.  
Runtime: pilot trace exists and is complete, activation/consumption real,
terminal admissible for the sample, independent control oracle present.  
Provenance: the pilot `sample_manifest.json` `gem5_sha256` and six
`source_sha256` must equal the frozen config; a missing manifest is
`BLOCKED_BINARY`, never READY.

## 5. Reproduce

```bash
cd /home/sdc/gem5-fi-mmu-impl-v2
python3 tools/mmu_build_evidence_index.py \
  --manifest phase3/freeze/pilot_runs.json \
  --out phase3/formal/evidence_index.json
python3 tools/mmu_formal_preflight.py \
  --outdir phase3/freeze/evidence/preflight_final \
  --summary-json phase3/freeze/evidence/preflight_final_summary.json
sha256sum CHAOS/gem5/build/ARM/gem5.opt
```

## 6. Honest conclusion

The formal platform is **not** 40/40 READY. All 40 IDs and the deterministic
seed policy are frozen and consistent; 18 contexts have frozen-binary
evidence with complete traces and admissible terminals. The remaining 22
are blocked by (a) historical-binary provenance (M01–M04), (b) the M02
target-PFN constant, (c) the M05 Execute trace gap, and (d) the two M07
PROT_NONE contexts that have no permission-grant decision to invert. See
`MMU_Final_Blockers.md` for the minimal fix for each.
