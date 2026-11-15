# MMU Final Research Closure Report

Campaign: `MMU-FORMAL-20261113`

## Final status

- **MMU_FINAL_RESEARCH_CLOSURE = PASS_WITH_DOCUMENTED_RESEARCH_LIMITATIONS**
- MMU_DIAGNOSTIC_FEATURE_GATE = `PASS`
- MMU_REPEATABILITY_LAUNCH_GATE = `READY_FOR_RESEARCHER_APPROVAL`

All four engineering gates pass. The final closure carries documented research limitations (observability and model separability), not hidden data failures.

## Gate 1 — Formal data integrity

`FORMAL_DATA_INTEGRITY = PASS`

- 40/40 SampleRunIDs present; terminal distribution `{"SDC": 31, "SQUASHED": 4, "DETECTED_CONTAINED": 5}`.
- 40/40 trace, manifest and verdict hashes unchanged.
- Frozen binary `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`; source closure commit present; original results ZIP `caeaf6506495ed119a06a12075f5193276e2e1279286ddc56610016f39caa151` unchanged.

## Gate 2 — Diagnostic feature integrity

`DIAGNOSTIC_FEATURE_INTEGRITY = PASS`

- Three views are separated: Ground Truth, Simulator-Assisted and Blinded.
- The old `UpstreamPathClass_SIM` used `TraceFaultSite` and is marked critical leakage; the blind view uses event-derived `ObservedPathClass` only.
- Fault consumption is separated into FaultInjected / FaultActivated / FaultStateConsumed / DownstreamArchitecturalConsumption.
- Recomputed consumption: **40/40 consumed**, **36/40 downstream**, only **5** literal `fault_state_consumed` events (M06).
- M03 R01-R04: consumed but squashed before architectural update. M06: detected and contained; not generic masked. M07: permission-policy manifestations.

## Gate 3 — Repeatability execution readiness

`REPEATABILITY_EXECUTION_READINESS = PASS`

- 10/10 launch rows READY; 10/10 read-only describes READY; 80 parity checks with no semantic mismatch.
- M01 uses executed guest `4f3ddbf2...`, not the canonical `ec525687...` field; the original matrix is untouched.
- M05 R05 uses explicit `--mmu_m05_decoy_va 0x4010200000` and `--mmu_m05_decoy_table_base 0`; no live-scan fallback.
- M07 R04/R05 exact target VAs are `0x400d400100` / `0x400d600180`.
- All commands are fully expanded; isolated outdirs, byte-copied rcS and independent hash-pinned disk copies exist. No placeholders, no collisions, no seed flag.

## Gate 4 — Independent acceptance

`INDEPENDENT_ACCEPTANCE = PASS`

- 33 automated tests pass; negative tests cover missing M05 decoy, wrong W9 guest, unresolved placeholders, output collision, missing consumption evidence, unsupported M03 exception labels and GT leakage.
- No gem5 process was started; no repeatability run was executed.
- The package SHA256 manifest is verified externally after zip creation (sibling `.sha256` file).

## Key research findings

1. The blinded view cannot distinguish M04 vs M08, and cannot reliably separate M02/M04/M08 from final wrong-value symptoms alone. Simulator-assisted entry/request-PA evidence is required.
2. M01 vs M03 is separable only when maintenance/ASID/permission or squash observations are available.
3. M06 vs M07 is separable when exception delivery or unexpected success is visible.
4. No classifier accuracy or cross-workload generalization is claimed for 40 contexts.

## Independent packaging review

An independent read-only review found a non-blocking ZIP self-containment gap: `common.py` was not vendored and `__pycache__` files were present. Both were fixed; the describe markdown was regenerated with fully expanded commands. A fresh extraction now passes `sha256sum -c` and all 33 tests. The review confirmed no new gem5 process, no disk-image entry in the ZIP, and no semantic parity failure.

## Stop condition

No new gem5 experiment was started. The 10 repeatability runs are prepared and await researcher approval.
