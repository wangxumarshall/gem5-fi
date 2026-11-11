# MMU Formal Freeze — Change Log (2026-11-12)

Workspace: `/home/sdc/gem5-fi-mmu-impl-v2`. Original `/home/sdc/gem5-fi-mmu` was
not modified. No formal SampleRunID was launched.

## Authority / configuration

1. Created the frozen workbook
   `phase3/freeze/authority/gem5-fi-MMU-Final-Paper-Experiment-Plan.xlsx`
   from the read-only design package: 40 SampleRunIDs set to `FROZEN`,
   Seed set to the literal text `N/A_DETERMINISTIC` (number format `@`),
   SeedPolicy=DETERMINISTIC, SeedSource=RESEARCHER_APPROVED,
   SampleFreezeStatus=FROZEN. The source workbook is untouched.
2. Created `MMU_40_Sample_Matrix.csv`, `MMU_Formal_Config.json/.yaml`; the
   config now carries the frozen binary/source/workload SHA256 values, not
   PENDING placeholders.
3. Seed audit: no real nondeterministic source on the MMU path (LRURP,
   StridePrefetcher without RNG, TournamentBP, fixed checkpoint, fixed-VA
   static workloads; the only global-RNG consumer is the O3 SMT fetch pick
   with num_cores=1). The runner refuses any `--*seed*` gem5 flag.

## Runner / preflight / validator

4. `tools/mmu_formal_preflight.py`:
   - frozen-authority default resolution + `BLOCKED_SEED_POLICY`;
   - runtime evidence is now part of the PRIMARY status (no static-only
     READY); TraceCompleteness (not PropagationStatus) is the trace gate, so
     a legitimate SQUASHED/DETECTED_CONTAINED row is not blocked for the
     expected PARTIAL propagation;
   - build-provenance gate now hashes the REAL pilot manifest from the
     evidence index, not `runs/<formal SampleRunID>/` (which does not exist
     before the formal run), and a missing manifest is `BLOCKED_BINARY`;
   - workload resolution: live `workloads/mmu/<W>` first, except W9, whose
     canonical ASID table (220/224/228/232/236) belongs to the mmu_rev W9
     build (the live rebuild uses 234–250).
5. `tools/mmu_formal_runner.py`:
   - records `gem5_sha256`, six source SHA256 (including CHAOSPropagation),
     `workload_sha256`, control-oracle SHA256, and fails closed on a
     plan-vs-execution hash change;
   - waits for `prop_evt.txt.gz` size+mtime stability before validation,
     retries once, and records `trace_read_error`;
   - W9 and W10 rcS embed the canonical binary payloads (no stale guest-disk
     binary); W9 runs all five contexts so the authoritative ASIDs are
     assigned in order; W10 uses `--ctx R0x` with the fixed VA index.
6. `tools/mmu_trace_validate_v3.py`: fixed `UnboundLocalError` when a chain
   has no resolvable W9 ASID/W10 VA (record `ctx=""`, basis `unresolved`).
7. `tools/mmu_formal_validate.py`: removed the blanket
   "Execute => COMPLETE" shortcut that hid missing causal kinds; fixed the
   all-digit hex PA comparison in `_cross_dynamic_wrong_commit` (trace `pa`
   fields are unprefixed hex).

## C++ (one patch unit)

8. `mmu.cc` + `CHAOSPropagation.{hh,cc}`: added `mmuSeqSquashed(seq)` and
   gated the M08 one-shot on it. An already-squashed wrong-path translation
   no longer burns the injection; the first live translation of the target
   is corrupted instead. Fault site, PA-only corruption and SDC semantics
   are unchanged. Final binary `a71ce0ca…` (BUILD_RC=0,
   `phase3/freeze/build_m08_gate.log`).

## Workloads

9. W10: fixed `--ctx R0x` always using VA index 0; embedded the live binary
   in `configs/fs/mmu_w10_run.rcS`.
10. W10S: cold-mode target mmap immediately before the STRB; all printf
    moved after the store (removes the wrong-path `__strlen_asimd` target
    fill that made the store hit a stale TLB entry).
11. W13: added a fresh `+0x1000` alias consumer in the same 2 MiB region,
    accessed BEFORE the guest TLBI. The alias has a populated PTE but no
    complete TLB entry, so it resumes from the corrupted L2 partial entry
    and returns the decoy sentinel. Historical W13 binary preserved in
    `phase3/freeze/evidence/legacy_bins/mmu_w13.bak`.
12. W14: R02 uses `LDADDAL` (LSE AMO) so the translation class is genuinely
    Atomic; every context maps RW+MAP_POPULATE, touches the page, then
    mprotects to the restricted protection, so the PTE is present.
    Historical W14 binary preserved in the legacy_bins directory.
13. Base rcS templates `mmu_w10_run.rcS`, `mmu_w13_run.rcS`,
    `mmu_w14_run.rcS`, `mmu_w10s_run.rcS` embed the frozen binaries.

## Evidence handling

14. Every old run directory is preserved. Failed runs (e.g.
    `TEST-M06-R02B`, gem5 exit 124) are kept. Two stale verdicts
    (`TEST-M06-R05B`, `TEST-M08-R03`) were produced on a live gzip stream;
    their complete traces were revalidated into
    `phase3/freeze/evidence/reval/`.
15. Metadata corrections are explicit in the manifests
    (`workload_sha256_recorded_pre_fix`, `source_sha256_note`), never silent.
