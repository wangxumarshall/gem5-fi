# LSU v3.2.2 — Remaining Nine Models: Design and Safety Review

**Status of this document:** design + safety review. It records what exists and
what is still missing. It does **not** claim IMPLEMENTED/COMPILED/UNIT_TESTED for
any of the nine models. The public Trace interface (injection/no-change nodes,
LQ/SQ lifecycle, forwarding normal/fault decision, replay, real commit,
UNRESOLVED terminal) is now stable, so each model can be added without inventing
a second trace format.

| Model | Unit | Mode | Source hook (real location) | Trace link | Safety risk | Status |
|---|---|---|---|---|---|---|
| LQ04 | LQ | F0 | `LSQUnit::executeLoad` after the LQ entry/request exists; invalidate the request state of one entry | `noteInjection` + `lq_lifecycle free(reason=early_invalidate)` | **HIGH**: clearing/invalidating an entry can alias another request or hang the LSU | DESIGNED — safety review below; not implemented |
| SQ01 | SQ | F0 | `LSQUnit::insertStore` after `storeQueue.back().set()`, flip byte0 bit3 of the SQ entry data | `noteInjection` with old/new data hash; later `sq_lifecycle` free/complete | LOW: data-only, no state machine change | DESIGNED; not implemented |
| SQ03 | SQ | F0 | `LSQUnit::executeStore` after `canWB` is set; set it early for one entry | `noteInjection` with entry index/generation; `sq_lifecycle` | MEDIUM: premature writeback changes memory-side ordering | DESIGNED; not implemented |
| LP01 | LP | F0 | `CHAOSL1DForward` already corrupts load-response data (`faultMask`, `maxFaults=1`) at the pre-`completeDataAccess` hook | needs `noteInjection` wiring into `CHAOSPropagation` (currently absent) | LOW: data-only | DESIGNED — injector exists, trace wiring missing |
| SP05 | SP | F6 | `LSQUnit::completeStore` accounting (`_completed`, `storesToWB`) | `noteInjection` + `sq_lifecycle` | **HIGH**: a suppressed completion can hold the entry forever (HANG) | DESIGNED — safety review below; not implemented |
| FW02 | FWD | F6 | done in this round (`noteForwarding` + commit node) | full | — | IMPLEMENTED / PILOT_RUN |
| FW05 | FWD | F6 | existing `fwd_source_sub` branch in `LSQUnit::executeLoad` (`alt_src` older store) | `noteForwarding` with `bookkeeping=alt_src` | LOW/MEDIUM: wrong source data is a data-only fault | DESIGNED — F5 path exists; F6 ordinal wiring missing |
| MD04 | MD | F6 | `LSQUnit::checkViolations` where `possibleLoadViolation` is set | `noteInjection` + replay/squash nodes | MEDIUM: skipped violation lets a stale load commit (SDC) or hang | DESIGNED; not implemented |
| RP01 | RPL | F6 | `LSQUnit::executeLoad` partial-forward branch: `iewStage->rescheduleMemInst(load_inst)` | `noteReplay`/`noteSquash` + commit node | **HIGH**: skipping the reschedule can leave the load never completing (HANG) | DESIGNED — safety review below; not implemented |
| DA04 | ALIGN | F0 | `LSQ::pushRequest` when constructing the fragment Request (`Request::setByteEnable`) | `noteInjection` with old/new byte-enable | MEDIUM: a wrong byte-enable changes which bytes are written | DESIGNED; not implemented |

## Safety review: LQ04

**Fault definition (Excel):** after `executeLoad`, clear the LQ entry's
`_valid`/`_request` for the target `lqIdx`; do not pop and do not reuse.

**Blast radius:** the LSU circular queue is indexed by `lqIdx`; the entry's
`LSQRequest` owns the in-flight `Request` and packet state. Clearing
`_request` while packets are outstanding can orphan a `Request` that the memory
system still references (use-after-free) or make `completeDataAccess` dereference
null. The entry must not be reused before the outstanding request is drained.

**Gate for a future implementation:**
1. Fire only when `maxFaults=1` and the target entry has no outstanding packet
   (`!request->isAnyOutstandingRequest()`), otherwise decline (count as
   `NO_ELIGIBLE_EVENT`, never a silent no-op).
2. Invalidate a per-entry "valid" shadow used by the trace and by a safe
   early-return path; do **not** destroy the `LSQRequest` object.
3. Add a watchdog (`--maxinsts`/wall timeout) and classify HANG explicitly; a
   hang is a valid model outcome, not a pass.
4. Verify with a PILOT_RUN that the entry is not reused before the request is
   drained; if the queue asserts, the design is rejected.

## Safety review: RP01

**Fault definition (Excel):** at the partial-forward mismatch branch, skip one
`rescheduleMemInst` call; the load is not replayed.

**Blast radius:** `rescheduleMemInst` is the only path that returns the load to
the IQ for a retry. Skipping it while still calling `clearIssued()` can leave the
load permanently non-issued and non-complete → the ROB fills and the run hangs.
The model explicitly allows HANG as an outcome, but the platform must be able to
observe and classify it.

**Gate for a future implementation:**
1. Fire once (`maxFaults=1`) at a configured partial-forward ordinal; record the
   skip in the trace as `replay_skipped` with reason `rp01_no_reschedule`.
2. Keep `rescheduleMemInst` for every other load; only the target load skips.
3. Run with `--maxinsts` and a wall timeout; map a no-checksum/exit-timeout run
   to `HANG` (`TIMEOUT`), never to MASKED.
4. Add a post-skip commit/squash node from the real commit path; if the load
   later commits stale data, record SDC, not a fabricated correct commit.

## Safety review: SP05

**Fault definition (Excel):** suppress one `completeStore`/`_completed` update.
**Blast radius:** the SQ entry never pops; backpressure can fill the 16-entry
queue and hang. Gate: one store, explicit HANG classification, watchdog; never
suppress the accounting of a store that already produced a memory side effect.

## What is deliberately not done in this round

No model above was added as code because each one needs its own injector mode,
config parsing, unit test, target-event proof and a real pilot run. Adding nine
hooks without those checks would violate the repository's "one verified patch per
unit" rule. The trace contract they will write into is frozen by this round's
commits:

- `injection` / `injection_nochange` with real `dyn_inst_seq` and values,
- `lq_lifecycle` / `sq_lifecycle` with index + generation,
- `forwarding_decision` with normal vs fault decision and memory path,
- `replay` / `squash` from real LSQ paths,
- `commit` for the fault instruction,
- `UNRESOLVED` as an explicit terminal.

## Recommended next order

1. SQ01 (lowest risk, data-only) → DA04 → LP01 (wire the existing injector) →
   MD04 → FW05 (F6 on the existing alt-source path) → SQ03 → SP05 → LQ04 → RP01
   (the last two only after the watchdog/HANG path is added to the pilot runner).
