# SP05 source audit (v3.2.9)

Model: **Premature Store Completion** (`SP05-CFG01`), target
`LSQUnit::completeStore()`.

## 1. Observed lifecycle (gem5 vendored tree, v3.2.9 base `d5c15309`)

| Step | Where | What happens |
|---|---|---|
| Store executes | `LSQUnit::executeStore` (`lsq_unit.cc:731-791`) | SQ entry points at the store; no completion state yet |
| Store commits | `LSQUnit::commitStores` (`lsq_unit.cc:896-925`) | For each newly committed store: `canWB()=true; ++storesToWB` |
| Writeback selected | `LSQUnit::writebackStores` (`lsq_unit.cc:932-1070`) | `storeWBIt` advances in age order; the packet is sent by `request->sendPacketToCache()` |
| Response | `LSQUnit::completeDataAccess` (`lsq_unit.cc:221/229`) | On the cache response, calls `completeStore(sqIt)` |
| Instant paths | `lsq_unit.cc:959/1045/1063` | size-0 stores, failed store-conditionals and local accesses call `completeStore` without a cache response |
| Completion | `LSQUnit::completeStore` (`lsq_unit.cc:1325-1380`) | `_completed=true; --storesToWB`; pops completed head entries (`clear()` → `freeLSQEntry()`); `store_inst->setCompleted()`; checker verify |

So **writeback (cache write) precedes completion**, and commit (the `canWB`
grant) precedes both. `storesToWB` counts stores that are committed and not
yet completed.

## 2. What "premature" changes

The frozen definition (`SP05_Definition_Freeze_v3.2.8.md`) says: "SP05 marks
one selected live store complete early (entry-keyed by SQ index + generation)
and keeps the `storesToWB` decrement paired."

Minimal implementation of that sentence: when the target entry is first
selected as `storeWBIt` (it is committed, `canWB` true) and its request has
**not been sent**, call the real `completeStore(storeWBIt)` and skip the cache
send. Then:

- `_completed` false → true, and the entry is popped/cleared if it is the head;
- `storesToWB` is decremented by the real paired decrement (no manual edit);
- no packet is sent, so no response can call `completeStore` a second time;
- `store_inst->setCompleted()` runs normally and the store still commits.

The store's data is therefore **not written** to cache/memory. This is a
premature-completion / lost-store fault. It cannot make the data visible
earlier; if anything it makes it invisible. That is the microarchitectural
meaning recorded for this model.

## 3. Conflict with the legacy Excel wording (evidence)

`LSU_Model4_Design_and_Safety_v3.2.2.md` §"Safety review: SP05" says:

> **Fault definition (Excel):** suppress one `completeStore`/`_completed`
> update. ... the SQ entry never pops; backpressure can fill the 16-entry
> queue and hang.

`LSU_Remaining_Models_Audit_v3.2.3.md` says "entry-keyed suppression +
timeout". The 60-sample workbook's `FaultDuration` text says "SQ entry无法释放，
可能backpressure/HANG".

These describe **suppressed completion** (never completing), which is the
opposite state change from **premature completion** (completing too early).
Resolution:

- The latest frozen authority (`SP05_Definition_Freeze_v3.2.8.md`) and the
  v3.2.9 work order both name *Premature Store Completion*. Implement that.
- Do **not** implement suppression; it is the HANG-prone variant.
- Keep the legacy wording in history; correct only the `FaultDuration` text in
  the v3.2.4 revision sheet and cite this audit.
- This is a wording reconciliation, not an expansion of the fault model.

## 4. Invariants the hook must assert

1. `!request->isSent()` — never touch an in-flight request.
2. `storesToWB > 0` before the call.
3. `!entry.completed()` before the call.
4. Target identity `(sqIdx, sqEntryGeneration)` equals the selected target.
5. After the call: `completed()==true` and
   `storesToWB_after == storesToWB_before - 1`.
6. Exactly one completion event per target `DynInst` (one-shot), including a
   reused SQ entry with a different generation.
7. A second target selection or a second `max_faults` grant cannot inject
   (`sp05_fired` plus the rule clamp `0 → 1`).

## 5. Safety notes

- Because the entry is completed and popped in-order, there is no backpressure
  accumulation and no HANG from the SQ entry lifetime.
- The request is freed by `LSQEntry::clear()` → `LSQEntry::~LSQEntry`/`freeLSQEntry`; with
  the `!isSent()` gate this path is the same one used for size-0 instant
  completions.
- A store whose write was dropped may make a later load read the old value
  (potential SDC) or may be unobservable (MASKED). Both are recorded from real
  traces; no consumer edge is invented.
- The in-simulator watchdog and the external runner timeout are required even
  though this semantic is not expected to hang.
