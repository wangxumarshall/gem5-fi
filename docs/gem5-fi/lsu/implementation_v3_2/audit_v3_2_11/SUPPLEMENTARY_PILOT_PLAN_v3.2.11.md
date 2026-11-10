# Supplementary Pilot Plan (v3.2.11) — AWAITING_RESEARCHER_APPROVAL

**Status:** No supplementary run was executed in this round. Every item below is a proposal only.
**Rules applied (B8):** use the existing traces first; name the missing event; prove the current trace cannot supply it; name the hook/workload change; give the minimum run count; preserve the original SampleRunID and Seed; never overwrite a historical pilot; never mix binaries.

## 1. Items

### A01 — AGU wrong-EA reference value
1. **Missing:** the data value at the *correct* EA (the trace records only the corrupted-EA response).
2. **Why the current trace cannot supply it:** the injection record stores old/new EA but no reference read; the delivered value cannot be compared.
3. **Change:** add a read-only reference-value hash at the original EA to the A01 trace hook (no change to the fault), and record the page-table-fault address with the injected VA.
4. **Minimum runs:** 2 (one re-run of a masked pilot, one of the crash pilot).
5. **Identity:** preserve the original SampleRunID/Seed; new output directory, no overwrite.
6. **Decision it enables:** PARTIAL → COMPLETE for the pilots whose reference data differs; address-matched CRASH attribution.

### A03 — AGU F5 stream + crash attribution
1. **Missing:** writeback/consumer events in 5/6 pilots; an address-matched crash.
2. **Why:** the v3.2.1 traces stop before writeback and the crash address is not the injected EA.
3. **Change:** record the F5 eligible stream and the page-table-fault address in the trace (read-only additions).
4. **Minimum runs:** 2 (one completed pilot, one crash pilot).
5. **Identity:** preserved; no overwrite.

### FW02 — complete the v3.2.4 pair
1. **Missing:** consumer/commit records in the v3.2.4 R01/R05 traces; proof that the R01/R05 squashes are fault-caused.
2. **Why:** the existing v3.2.4 traces lack the consumer node; the squash reason is not recorded.
3. **Change:** trace the consumer and squash reason; no fault-definition change.
4. **Minimum runs:** 2 (R01/R05 re-runs under the same seeds/ordinals).
5. **Decision it enables:** whether FW02 has a data/control chain beyond R04.

### DA04 — raw oracle files for the two complete chains
1. **Missing:** raw `oracle.log`/`stdout.log` for `pilots_v3_2_6/DA04-R04,R05` (the SDC is meta/E2E-recorded).
2. **Why:** the files are absent from the directories; the E2E evidence is a summary.
3. **Change:** none to the fault; re-run the two preserved pilots and keep the raw oracle/stdout.
4. **Minimum runs:** 2.
5. **Decision it enables:** `OracleVerified=yes` at the raw-file level for the two SDC chains.

### MD04 — squash causality
1. **Missing:** the reason for the R01/R04 squash.
2. **Change:** record the squash trigger/reason in the trace.
3. **Minimum runs:** 2.
4. **Decision it enables:** PARTIAL → COMPLETE if the squash is fault-caused, otherwise SQUASHED (still not a failure).

### FW05 — R01 squash reason
1. **Missing:** proof that the R01 squash is fault-caused.
2. **Change:** trace the squash reason.
3. **Minimum runs:** 1.

### SQ01 / SQ03 — a consumer of the corrupted lane
1. **Missing:** a later load of the same address after the store.
2. **Why:** the current workload never reads the lane; the trace cannot manufacture a consumer.
3. **Change:** a dedicated workload with a same-address reload after the store (new workload, new SHA, new golden oracle; old workload preserved).
4. **Minimum runs:** 5 each (one per preserved SampleRunID/Seed).
5. **Decision it enables:** data-propagation capability for the store-side models.

### SP05 — entry-free/drain trace
1. **Missing:** the entry-free/drain event and a consumer.
2. **Change:** trace the entry release path (read-only hook addition); a consumer still needs a reload workload.
3. **Minimum runs:** 1-2 (lifecycle) or 5 (with reload workload).

### LQ04
None. The literal definition is frozen and must not be changed to obtain SDC.

## 2. Cost and risk

- Binary changes: A01/A03/FW02/MD04/FW05/SP05 need trace-only additions; SQ01/SQ03/SP05 data propagation needs a new workload.
- No C++ fault-definition change is proposed for any existing model.
- Every run must use the preserved SampleRunID/Seed and a new output directory; historical artifacts are read-only.
- None of these runs is authorized by this round. `Formal experiment = NOT_STARTED`.
