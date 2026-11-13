# LSU v3.3.3 — Final Formal Evidence Normalization (collector/report only)

**Date:** 2026-11-13
**Scope:** derived evidence extraction and reports only. **No gem5 run, no C++/Binary/Config/
Workload/Seed/SampleRunID/ROI change, no raw run-directory edit.**

## Ground truth verified from raw files (before any code)

A03 selected/effective/consumer values were read from `addrpath_injections.log` and
`prop_trace.csv.gz`; all five match the researcher's table. R02 seq 13718 carries
`squash_cause=unrelated`; R03 ordinal 1131 has `affected=0;reason=ALREADY_STUCK`, first
affected is 1150/14594. Hash linkage verified: `taint_reg.writeback_value_fnv ==
consumer.source_value_hash == consumer.consumer_input_fnv`, `consumer_input_matches_source=1`,
`consumer.source_event_id == taint node`.

## Units

1. **A03 direct-driver parser** (`tools/lsu_v333_propagation.py`): parse raw trace; emit
   `SelectedOrdinal/SelectedDynInstSeq/SelectedPC`, `FirstAffectedInstruction`,
   `FirstAffectedSquash`, `FirstCommittedAffectedInstruction`, `FirstConsumer`, plus
   `ResponseEventID/TaintEventID/SourceEventID/ProducerDynInstSeq/ConsumerDynInstSeq/
   WritebackValueFNV/ConsumerInputFNV/ConsumerInputMatchesSource`. Never merge them into
   `FirstDivergence`. Keep `EvidenceClass` and terminal unchanged.
2. **Manifest backfill** (`tools/lsu_v333_launch.py`): A03 selected DynInstSeq+PC from
   `addrpath_injections.log`; RP01 load DynInstSeq+PC from `summary.rp01.first_skip`; SP05
   store PC from the `sp05_stage/store_commit` trace event. Add `DynInstSeqSource`/`PC_Source`.
   Add `FaultStateActivationCount`, `AffectedAccessCount`, `A03StreamEventCount`; keep raw
   `InjectionCount`.
3. **Evidence completeness audit**: new `tools/lsu_v333_evidence_audit.py` emitting
   `TraceV31Status`, `RawPropTraceStatus`, `RawTraceIntegrity`, `PropagationCoverage`,
   `CausalChainCompleteness` for 120 runs.
4. **Workbook**: extend `Causal_Propagation` sheet with the new event columns; keep 8 sheets.
5. **Provenance**: mark `collector_manifest.stage2-failed-20261113` NON_CANONICAL; report
   stale lock PID 3527664 (process dead, file not deleted); cite L-D09 ledger.
6. **Regenerate** 02→03→04 (FORCE for 04), then the audit; verify 38/12/5/5/0 unchanged,
   60/60 controls zero-injection, SHA manifests.
7. **Independent agent** acceptance against the 8-point checklist.
8. **Final ZIP** `LSU_v3.3.3_Final_Formal_Results_Accepted.zip` + SHA256.

## Verification

- `sha256sum -c SHA256SUMS.campaign` still verifies the original tree.
- New `SHA256SUMS.deliverables` verifies all updated reports.
- No file under any run `attempts/` directory changes (compare mtimes/hashes before/after).
