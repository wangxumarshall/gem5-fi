# LSU v3.3.3 — Final Launch Blockers

**Verdict:** `READY_TO_LAUNCH_FORMAL_CAMPAIGN = YES`
**Blocking count:** 0.
**Independent audit:** PASS (Agent F final, 2026-11-12;
`LSU_Independent_Launch_Acceptance.md`).

## Closed blocker

**B1 — A01 census/executed dyn-seq offset (CLOSED, not a blocker).**
Census ordinal 597 = dyn 12752; executed fault = dyn 12909. Independent F
verified all five A01 contexts: identical PC/EA, constant +157 dyn-seq offset
for R01–R05. Root cause: the census used a relative `--cmd` path (SE stack
shift); the fault run uses an absolute path. The percentile rule is defined on
the eligible-event ordinal axis (N=129, [585,713]), which is preserved; the
A01 fault/writeback/consumer/oracle evidence is complete. No re-census and no
source/workload/seed/ID change is required.

## Non-blocking notes (no launch gate depends on them)

1. **A03 watchdog exit event**: trace/oracle complete, terminal
   `SDC/POST_ORACLE_SIM_HANG`; gem5 reports
   `NotImplementedError: Exit event 'CHAOS_A03_WATCHDOG_EXPIRED' not implemented`
   (exit 1). The runner classifies via the marker/checksum. A clean exit would
   require a C++ rebuild; not required for launch.
2. **Source-only mounted-p0 gates** for FW02/LQ04/RP01: their controls are
   `INJECTOR_ABSENT`, so zero is proven by absence + oracle; the 35 mounted
   controls and DA04/MD04 have mounted-p0 gate evidence. Optional 3 gate runs
   would make the source-only claim runtime-verified.
3. **Legacy LQ04 pre-formal runs** used `rngSeed=0` (F0 ordinal selection is
   deterministic). The formal runner passes the frozen
   `--lq04_rng_seed`; historical runs are kept as history.
4. **Historical manifests** (105 run_pilot + 15 direct) are pre-formal and lack
   the full campaign fields. The formal sequence writes the 120-row manifest
   and one `campaign_manifest.json` per run after the matrix; historical
   manifests are not backfilled.
5. **Legacy frozen CSV flags**: `60_SAMPLE_MATRIX.csv` still says
   `ConfigFrozen=NO` / `NEEDS_USER_DECISION`; it is the authoritative identity
   source and is intentionally not edited. The launch workbook/manifest carry
   `ConfigFrozen=YES` (approval 2026-11-12).
6. **Propagation versions**: the lossy 14-column `_Final.csv` and older copies
   are ARCHIVED; the authoritative file is the 16-column
   `LSU_60Context_Causal_Propagation_Final.csv`.
7. **v3.3.2 archival hardlink**: `audit_v3_3_2/binary/gem5.opt.v332-070d68a6`
   is a pre-existing hardlink to the final binary and hashes `1126e0fd`; it is
   outside the v3.3.3 package and does not affect the final binary SHA.
