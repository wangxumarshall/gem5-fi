# LSU v3.3.3 — Final Formal Evidence Normalization Report

- **Campaign ID:** `LSU-V333-FINAL-20261112`
- **Round:** collector/report normalization only. **No gem5 rerun, no C++/Binary/Config/
  Workload/Seed/SampleRunID/ROI change, no raw run file modified.**
- **Raw evidence:** 120/120 run directories byte-identical (`SHA256SUMS.raw_runs`,
  2,193 files, `sha256sum -c` exit 0).
- **Classification:** unchanged — COMPLETE_CAUSAL_CHAIN 38, VALID_TERMINAL_CHAIN 12,
  QUALIFIED 5 (SP05), TRACE_INCOMPLETE 5 (RP01), UNRESOLVED 0.

## 1. A03 direct-driver propagation chain (restored from raw files)

Parsed from `addrpath_injections.log`, `prop_trace.csv.gz`, `summary.json`, `oracle.log`.
No `trace_v31.jsonl` is required for A03.

| Context | Selected Ordinal | Selected DynInstSeq | First Effective Ordinal | First Effective DynInstSeq | Consumer |
|---|---:|---:|---:|---:|---:|
| R01 | 1058 | 13204 | 1058 | 13204 | 13206 |
| R02 | 1094 | 13718 | 1099 | 13772 | 13774 |
| R03 | 1131 | 14398 | 1150 | 14594 | 14596 |
| R04 | 1168 | 14930 | 1168 | 14930 | 14932 |
| R05 | 1204 | 15146 | 1204 | 15146 | 15148 |

These values match the researcher's supplied table exactly.

### A03-R02 — affected but squashed, then a real committed path

- `FirstAffectedInstruction`: ordinal 1094, seq 13718, pc `40068c`.
- `FirstAffectedSquash`: node 5339, `cause=unrelated`, `fault_caused=0`,
  `reason=lsq_squash`. Seq 13718 was injected but architecturally irrelevant.
- `FirstCommittedAffectedInstruction`: ordinal 1099, seq 13772, pc `400678`.
- `FirstConsumer`: seq 13774, node 5423.

### A03-R03 — selected event is ALREADY_STUCK

- Selected ordinal 1131 / seq 14398 has `affected=0;reason=ALREADY_STUCK`; it is
  recorded as the selected activation, **not** as a data error.
- `FirstAffectedInstruction` and `FirstCommittedAffectedInstruction`: ordinal 1150 /
  seq 14594 / pc `4006d0`.
- `FirstConsumer`: seq 14596, node 5677.

## 2. A03 data-dependency chain and hash linkage

Each context carries the chain
`inj → addr_form → a03_stream → mem_req → resp → taint_reg → consumer → commit/errant_commit → Oracle`.

| Ctx | RespEventID | TaintEventID | SourceEventID | ConsumerEventID | Producer seq | Consumer seq | WritebackValueFNV | ConsumerInputFNV | Match |
|---|---:|---:|---:|---:|---:|---:|---|---|---:|
| R01 | 5236 | 5237 | 5236 | 5244 | 13204 | 13206 | `877efd17c26c35e9` | `877efd17c26c35e9` | 1 |
| R02 | 5410 | 5411 | 5410 | 5423 | 13772 | 13774 | `5da39ae7a43fa14e` | `5da39ae7a43fa14e` | 1 |
| R03 | 5671 | 5672 | 5671 | 5677 | 14594 | 14596 | `3ade8b2d87d817fb` | `3ade8b2d87d817fb` | 1 |
| R04 | 5649 | 5650 | 5649 | 5674 | 14930 | 14932 | `66e123de71552687` | `66e123de71552687` | 1 |
| R05 | 5717 | 5718 | 5717 | 5759 | 15146 | 15148 | `afb68d9968d579b7` | `afb68d9968d579b7` | 1 |

`consumer_input_matches_source=1` in all five: the consumer input hash equals the
register-writeback source hash. Application Oracle uses the recorded checksum
(`stdout.log`): all five fail against the frozen golden, hence SDC.

## 3. Manifest DynInstSeq / PC provenance

| Model | Field | Source | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|---|---|
| A03 | DynInstSeq / PC | `addrpath_injections.log:A03_STREAM(selected ordinal)` | 13204 / 4005c0 | 13718 / 40068c | 14398 / 4006a8 | 14930 / 4006d0 | 15146 / 4006d0 |
| RP01 | DynInstSeq / PC | `summary.json:rp01.first_skip` | 16293 / 400560 | 23229 / 400560 | 30165 / 400560 | 37101 / 400560 | 44037 / 400560 |
| SP05 | DynInstSeq / PC | `lsq_fwd_injections.log:target_seq` + `prop_trace:store_commit(store_pc)` | 13328 / 40053c | 15122 / 40053c | 16847 / 40053c | 18641 / 40053c | 20435 / 40053c |

No value is guessed; every cell records its source column (`DynInstSeqSource`,
`PC_Source`).

## 4. Evidence completeness (five distinct statuses)

`LSU_Evidence_Completeness_Audit.csv` (120 rows):

| Status | Distribution |
|---|---|
| TraceV31Status | PRESENT 105; ABSENT_DIRECT_DRIVER 15 |
| RawPropTraceStatus | PRESENT_DECOMPRESSIBLE 120 |
| RawTraceIntegrity | VALID 115; VALID_TERMINAL_COMPLETE 5 |
| PropagationCoverage | COMPLETE 50; COMPLETE_PROP_TRACE 5 (A03); COMPLETE_CONTROL 60; PARTIAL_WATCHDOG 5 (RP01) |
| CausalChainCompleteness | CONTROL 60; COMPLETE_CAUSAL_CHAIN 38; VALID_TERMINAL_CHAIN 12; QUALIFIED 5; TRACE_INCOMPLETE 5 |

- **A03:** raw propagation trace complete; no converted `trace_v31.jsonl` because the
  direct driver does not emit it. `PropagationCoverage=COMPLETE_PROP_TRACE`,
  `CausalChainCompleteness=COMPLETE_CAUSAL_CHAIN`.
- **RP01:** raw trace valid and terminal metadata complete; normal execution trace cut
  by the internal watchdog. `RawTraceIntegrity=VALID_TERMINAL_COMPLETE`,
  `PropagationCoverage=PARTIAL_WATCHDOG`, `CausalChainCompleteness=TRACE_INCOMPLETE`.
  These two cases are no longer conflated.

## 5. A03 injection-count semantics

`LSU_A03_Injection_Count_Semantics.csv` preserves the raw `InjectionCount` and adds:

| Ctx | RawInjectionCount | FaultStateActivationCount | A03StreamEventCount | AffectedAccessCount |
|---|---:|---:|---:|---:|
| R01 | 51310 | 1 | 51310 | 51211 |
| R02 | 51303 | 1 | 51303 | 51222 |
| R03 | 51304 | 1 | 51304 | 51243 |
| R04 | 51283 | 1 | 51283 | 51250 |
| R05 | 51253 | 1 | 51253 | 51238 |

The raw count is a persistent stuck-at stream-event count, **not** tens of thousands
of independent fault instances.

## 6. Provenance and archive

- `collector_manifest.stage2-failed-20261113/` is marked **NON_CANONICAL** with
  `NON_CANONICAL.md`; retained as audit history, not used by any final artifact.
- Stale lock `.lsu_v332_matrix.lock` names PID 3527664; that process is **not
  running**. The file is **retained and not deleted** (pending explicit confirmation).
- W6/W8 golden overrides remain sourced from ledger **L-D09**
  (`audit_v3_3_3/LSU_v3.3.3_Master_Defect_Ledger.csv`), using the verified Oracle
  values `2543a2a60de01795` and `3f89eab79392ce69`.
- `SHA256SUMS.campaign.pre_normalization` preserves the pre-round full-tree manifest.
  `SHA256SUMS.campaign` now covers the current tree (2,219 files, verification exit 0).
  `SHA256SUMS.raw_runs` proves the original 120-run tree is unchanged.
  `SHA256SUMS.deliverables` covers the updated delivery set.

## 7. Regenerated artifacts

- `collector_manifest/LSU_120Run_Campaign_Manifest.csv` (+ pair map, control proof)
- `collector_full/LSU_120Run_Campaign_Manifest.csv` (+ pair map, control proof,
  readiness, workbook)
- `LSU_60Context_Causal_Propagation_Final.csv` (33 columns)
- `LSU_60Context_Final_Readiness.csv`
- `LSU_11Context_Repair_Validation.csv`
- `LSU_Control_Audit_Formal.csv`
- `LSU_Final_Experiment_Config.xlsx` (8 sheets; Causal_Propagation carries the new
  A03 fields)
- `LSU_Evidence_Completeness_Audit.csv`
- `LSU_A03_Injection_Count_Semantics.csv`

## 8. Verdict

`FORMAL_CAMPAIGN_EXECUTION=ACCEPTED`
`RAW_EVIDENCE=VERIFIED`
`CAUSAL_REPORT=FINALIZED`
