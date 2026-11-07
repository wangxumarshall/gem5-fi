# SQ01 — Source Audit and Implementation Record

**Model:** SQ01 (Unit SQ, F0, "Store 数据错误")
**Workload:** W3 `sq_drain`
**Status:** SOURCE_AUDITED / IMPLEMENTED / COMPILED / UNIT_TESTED / PILOT_RUN
(PROPAGATION_VERIFIED not claimed; see below)

## Source audit

| Item | Finding |
|---|---|
| Real structure | `o3::LSQUnit::StoreQueue storeQueue` (`lsq_unit.hh:469`); SQ entry data written by `LSQUnit::write(LSQRequest*, uint8_t*, ssize_t)` (`lsq_unit.cc:1818`) |
| Exact hook | `lsq_unit.cc:1836-1839`: the `memcpy(storeQueue[store_idx].data(), data, size)` that installs store data |
| Normal consumers | forwarding (`read()`), `writebackStores()`, `completeStore()` |
| Existing state before v3.2.3 | no SQ01 hook; no config surface |
| Eligible event | one normal store whose data has been copied into the SQ entry; only non-atomic, non-cache-maintenance, non-zero-block stores |
| Workload proof | `sq_drain` 66,721 committed loads / 31,092 committed stores in the v3.2.3 baseline |

## Implementation

- `CHAOSLSQFwd::StructMode::Sq01Bit3`, string `sq01_bit3`
  (`--lsq_struct_mode sq01_bit3`).
- `CHAOSLSQFwd::maybeCorruptStoreData(data, size, dyn_seq, sq_idx, generation)`:
  calls the existing F0 trigger (`onAttempt`/`onEligible`), flips `data[0] ^= 0x08`,
  increments the fault count, emits the trace node and the injection log line.
- `LSQUnit::write`: after the memcpy and only for real data stores, calls the
  injector. Entry, request, SQ state and pointers are untouched.
- Trace: `CHAOSPropagation::noteStoreDataInjection` writes `inj_store_data`
  (site, mode, SQ index, generation, old/new byte); the converter emits a
  top-level `injection` event with `unit=SQ`, `sub_unit=store_data`,
  `injection_status=INJECTED`, SQ entry id and generation. The store is added to
  `fault_seqs`, so its real commit node is emitted later.
- Coverage profile: `(SQ01, MASKED|SDC) = injection → sq_lifecycle`.

## Compile and tests

- `logs/build_v323_sq01.log`: scons exit 0.
- Unit tests: `_sq01_summary` log parser; converter mapping/values (52 tests).

## Pilot

`pilots_v3_2_3/SQ01-R01..R05` (W3 sq_drain, F0 ordinals 1–5):

| Context | Injected | bit3 flip | Observed | Terminal | Causality | Coverage |
|---|---:|---|---|---|---|---|
| R01–R05 | 1 each | true | MASKED | MASKED | DIRECT_DATAFLOW_EVIDENCE | COMPLETE |

All five accepted. The oracle passes because the injected byte is overwritten by
a later store in this workload; no SDC is observed, so the model is not marked
PROPAGATION_VERIFIED. A workload/context that consumes or checksums the
corrupted store byte before overwrite is the next step for that level.

## Safety

Data-only, one entry, one fault, no state-machine change. No assert, pointer or
request-lifetime risk. SAFE.

## Raw trace storage

Each `trace_v31.jsonl` is 189 MB (sq_drain ~198k events), above the GitHub
100 MB limit; files are in this delivery package and on disk, with sha256
sidecars, and excluded from Git (`pilots_v3_2_3/TRACE_STORAGE.md`).
