# LSU v3.2.3 — Remaining Models Source Audit (workstream B)

**Scope:** read-only audit of the eight models not yet implemented, run in parallel
with the v3.2.3 platform repair. Line numbers are from this worktree's vendored
tree. No file was modified by the audit.

**Reusable platform facts**

- Trigger API: `CHaOSLsuTrigger` (`src/cpu/o3/chaos_lsu_trigger.hh`); F0 fires at
  the eligible ordinal (167-181); F6 fires only through `onF6Event()` (208-221)
  and needs the single `chaosLsuF6Notify` consumer (57). `CHAOSLSQFwd` never
  registers that consumer, so `lsuTier=F6` on it currently injects 0; FW05 and
  MD04 need the private ordinal pattern (`f6_fired/f6_observed/f6_event_ordinal`,
  `CHAOSLSQFwd.hh:136-144`) or an F6 source.
- Trace API: `CHAOSPropagation::registerInjection` (not `noteInjection`);
  existing node kinds inj / inj_nochange / inj_store_data / addr_form / mem_req /
  resp / fwd / replay / squash / commit / lq_sq_lifecycle are enough. Do not
  add a second trace format.

## Per-model matrix

| Model | Unit/mode | Real structure | Hook point (file:line) | Existing state | Workload / eligible event | Safety |
|---|---|---|---|---|---|---|
| DA04 | ALIGN/F0 | `LSQRequest::_byteEnable` public (`lsq.hh:279-287`); `Request::setByteEnable` (`request.hh:715-720`) | `lsq.cc:833-834` (mask built) / `lsq.cc:1005,1127` (setByteEnable) | None; PRE hook refuses byte-enable (`lsq.cc:776-778`) | W8 alignment; first size=4 access with mask all ones | Medium-high: keep size unchanged, reads ignore BE; bound maxFaults=1 |
| LP01 | LP/F0 | `LSQUnit::completeDataAccess(PacketPtr)` (`lsq_unit.cc:107-214`), packet data (`packet.hh:387`) | `lsq_unit.cc:199-201` calls `CHAOSL1DForward::maybeCorrupt` before writeback | Partial injector exists, but `uint64_t*` cast (`CHAOSL1DForward.cc:100-104`) is OOB for size<8; no trace link | W5 load_response; first response with `!isWrite` | Low after byte-wise fix; data-only, maxFaults=1 |
| MD04 | MD/F6 | `LSQUnit::checkViolations` (`lsq_unit.cc:566-652`), `possibleLoadViolation` set at 624, store-side violator 632-645 | `lsq_unit.cc:624` (flag set), store-side 638/642 | Only L03 address corruption; no suppression; F6 not wired | W7 replay_dependency; first overlap that would set the flag | Medium-high: suppressed flag can let stale load commit or hang; one-shot + watchdog |
| FW05 | FWD/F6 | `LSQUnit::read` full-coverage branch (`lsq_unit.cc:1557`), older-entry scan 1606-1615 | `lsq_unit.cc:1617-1623` calls `maybeSubstituteSource` | `fwd_source_sub` wrong-source copy exists (F5-style); no F6 ordinal; trace shows forwarded/none | W8 workbook; W4 sq_forward is stronger (6 forwards + 1 mismatch); first full forward with an older entry | Low/medium: bounds-safe `min(copy_size, alt_size)`; tail may stay uninitialized if alt smaller |
| SQ03 | SQ/F0 | `SQEntry::_canWB` (`lsq_unit.hh:155,185-186`), `storesToWB` (`lsq_unit.hh:484`) | `LSQUnit::executeStore` (`lsq_unit.cc:731-791`), after `assert(store_fault==NoFault)` at 779 | None | W3 sq_drain; first normal store after warm-up | Safe-with-bound: set canWB and ++storesToWB exactly once, exclude SC/atomic; otherwise underflow/assert |
| SP05 | SP/F6 | `_completed` (`lsq_unit.hh:159,187-188`), `storesToWB`; `completeStore` (`lsq_unit.cc:1237-1298`) | `lsq_unit.cc:1240-1241` (`completed=true; --storesToWB`) | None | W6 store_path; one live store completion | Safe-with-bound: entry-keyed one-shot; a "next call" flag is defeated by instant-complete paths; watchdog needed; drain assert can misclassify HANG as SimulatorError |
| LQ04 | LQ/F0 | `LSQEntry::_valid/_request` (`lsq_unit.hh:101,105`), `clear()` frees request (116-126) | End of `executeLoad` (`lsq_unit.cc:658-728`) | None; `valid()` has no setter | W2 lq_lifetime; target LQ entry after executeLoad | **HIGH-RISK as specified**: clear() nulls `_inst`, commitLoad asserts (796/824), squash dereferences (1007-1012), freeLSQEntry may orphan/delete an in-flight request. Salvage requires a shadow poisoned flag, tolerant consumers, no request destruction, watchdog |
| RP01 | RPL/F6 | `IEW::rescheduleMemInst` (`iew.cc:563-566`), partial-forward branch (`lsq_unit.cc:1731-1772`) | exactly `lsq_unit.cc:1757` (`iewStage->rescheduleMemInst(load_inst)`) | None; call unconditional; noteReplay at 1755 | W7 replay_dependency; partial-forward mismatch | Safe-with-bound: skip one only, keep clearIssued(), watchdog + HANG classification; a prior `instsToReplay` entry can revive the load (Masked) |

## Safety verdicts

- **DA04** SAFE-WITH-BOUND (one mask, size unchanged).
- **LP01** SAFE after fixing the existing size<8 OOB cast.
- **MD04** SAFE-WITH-BOUND (one flag, watchdog, count-only first because W7's
  seven violations may all be on the store-side path, not line 624).
- **FW05** SAFE-WITH-BOUND (data-only; check alt_size >= load size).
- **SQ03** SAFE-WITH-BOUND (paired canWB/storesToWB update).
- **SP05** SAFE-WITH-BOUND (entry-keyed suppression + timeout).
- **LQ04** **HIGH-RISK**; the model as written is an assert/use-after-free
  generator. Do not implement without a shadow flag and tolerant consumers.
- **RP01** SAFE-WITH-BOUND (one skip + watchdog).

## Recommended next order

SQ01 (done in v3.2.3) → DA04 → LP01 (fix the OOB first) → MD04 → FW05 →
SQ03 → SP05 → LQ04 → RP01. Each model still needs its own commit with config,
unit test, compile, target proof, trace link and pilot.
