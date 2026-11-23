# WHEN-5X3 MMU 0202c source diff (observation-only)

Round 0202c · `gem5-fi-mmu-when5x3` · 2026-11-17
No git commit / push / branch. All gem5 changes are trace-only; the frozen
Where / Context / Timing definitions and all fault-injection semantics are
unchanged (verified: all 8 re-run Controls reproduce their frozen N exactly).

## gem5 source changes (5 files)

### 1. `src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh`
- `mmuNoteIfuResponse(tid, va, pa)` / `mmuRegisterFetchSeq(tid, seq, pc)` /
  `mmuTakeFetchTxn(req)` — new IFU propagation hooks (doc block §0202c).
- `mmuEntryFaultReuseCapped(instance, entry_id, gen)` — bounded warm-hit
  consumer-observation accessor.
- `std::map<const Request *, uint64_t> mmu_req_txn;` — Execute-fetch Request
  -> open translation_id registry (object identity, never VA/tick).
- Register `masked_reason` in the PROP-EVT field registry.

### 2. `src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`
- `MMU_CONSUMER_REUSE_CAP = 16` — bound on warm-hit consumer transactions.
- `mmuNoteLsuRequest`: registers the fetch translation_id under the REAL
  Request object identity (`mmu_req_txn[req.get()] = tid`) when `is_fetch`.
- `mmuTakeFetchTxn` / `mmuNoteIfuResponse` / `mmuRegisterFetchSeq`:
  emit `ifu_response` / `ifu_decode` and bind the DynInst seq -> fetch tid
  (`mmu_seq_txn[seq] = tid; mmu_traced_seqs.insert(seq)`), so the existing
  `mmuNoteCommit` / `mmuNoteSquash` fault-tag the fetched instruction's
  retirement.
- `mmuNoteEntryInsert`: for M05, register every fault-tagged COMPLETE entry
  insert into the entry-fault registry (`mmuRegisterEntryFault(..., "M05")`)
  so a later warm hit of that poisoned DTB entry adopts the fault.
- `mmuEntryFaultReuseCapped`: returns true once a poisoned entry's reuse_count
  reaches the cap.
- `mmu_fault_summary`: adds `masked_reason` (consumed /
  faulting_inst_squashed / exception_delivered /
  request_issued_not_completed_at_roi_end / not_consumed).

### 3. `src/cpu/o3/fetch.cc`
- `#include "cpu/o3/CHAOSPropagation/CHAOSPropagation.hh"`.
- `finishTranslation` (success) — `fetchBufferTxnId[tid] = mmuTakeFetchTxn(mem_req)`.
- `processCacheCompletion` — emit `ifu_response` when the faulted line arrives.
- `buildInst` — `mmuRegisterFetchSeq(fetchBufferTxnId[tid], seq, pc)` for each
  DynInst built from the faulted line.
- Reset `fetchBufferTxnId[tid] = 0` in the two fetch-buffer init sites.

### 4. `src/cpu/o3/fetch.hh`
- `uint64_t fetchBufferTxnId[MaxThreads];` — per-thread open MMU fetch
  transaction id for the line in the fetch buffer.

### 5. `src/arch/arm/tlb.cc`
- `phase3_entry_model` now includes M05 (so a COMPLETE poisoned DTB entry
  warm hit adopts the fault).
- Warm-hit consumer-transaction creation gated on
  `!mmuEntryFaultReuseCapped(...)` — bounds the fan-out to the first 16
  reuses, the rest stay silent like a normal warm hit.

## gem5 binaries

| role | SHA256 (first 16) | full |
|---|---|---|
| 0202c (fetch IFU + masked reason) | `eb327197c073dddf` | `eb327197c073dddf039fdb63662d2cfa266394507ae0cb4630d0f4ff4dd76f65` |
| 0202c (bounded warm-hit fan-out) | `fb1b6f010034f273` | `fb1b6f010034f27312f2df215e00ada08cb7df811ef7425e4585b623a7e1d3f8` |

Both are observation-only; the second differs only by the `MMU_CONSUMER_REUSE_CAP`
bound, which affects only the M05 data-path trace volume, never the fault
semantics (the 9 M05-C03/C04/C05 faults were re-run under the second binary).
The 12 fetch chains + 2 M07-C02 masked chains + all 8 Controls ran under the
first binary (their traces never exercise the warm-hit path).

## campaign analysis changes

- `campaign/propagation.py`:
  - `build_branches` maps `ifu_response` -> response stage, `ifu_decode` ->
    consumer stage.
  - `expected_stages`: Execute fetch boundary only when terminal is
    `lsu_request`; `masked_reason=request_issued_not_completed_at_roi_end`
    declares response/commit_squash not-applicable.
  - `edge_basis`: new `fault_entry_lineage` basis (same fault_id +
    partial_entry_insert -> tlb_entry_insert) for the M05 poison bridge.
  - `mutation_handoff`: M05 partial-entry -> poisoned-DTB-entry handoff.
- `campaign/finalize.py`, `campaign/export_evidence.py`,
  `campaign/acceptance.py`, `campaign/validate.py`: honour
  `analysis/retry2_map.json` so fault manifests / ActualOrdinal / oracle /
  EvidencePath resolve to the RETRY2 runs (fixes the round-0202b stale-path /
  trace-SHA mismatch).
- new `campaign/when5x3_retry2.py`, `campaign/make_retry2_index.py`,
  `tools/prop_trace_dump.py`.