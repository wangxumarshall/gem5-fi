# A03 — real faulting PC + persistent stuck-at lifecycle (v3.3.2 P0-5)

Status: implementation complete; host unit test green. gem5 rebuild NOT run by
this patch author (the main agent builds once).

## 1. Problem

Two A03 observation gaps on the F5 `a03_bit3_stuck0_load` path:

1. **PC was always `kPcUnknown`.** `lsq.cc` already passes
   `inst->pcState().instAddr()` into `CHAOSAddrPath::maybeCorruptPre` (verified
   at `CHAOS/gem5/src/cpu/o3/lsq.cc:784-786`, introduced by 95a2205c), but the
   A03 branch dropped it on the floor: `a03NoteEligibleLoad(...)` had no `pc`
   parameter and `streamEvent(...)` was built with the literal
   `chaos_a01::kPcUnknown`, so every `A03_STREAM` row printed `;pc=0;`.
2. **No lifecycle accounting.** The per-event stream showed each application
   but not that they are all applications of ONE persistent fault:
   `affected=1` (STUCK_APPLIED) and `affected=0` (ALREADY_STUCK) were only
   distinguishable row-by-row, with no run-level split, and the activation row
   / first row that actually changed the EA were not recorded as identities.
   An ALREADY_STUCK activation (a no-op application at the activation load)
   could therefore read like "nothing happened", hiding that the fault stays
   active for every later eligible load.

## 2. Changes (exact signatures)

### `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh`

- `void a03NoteEligibleLoad(uint64_t dyn_seq, Addr golden_ea, Addr actual_ea, int bit, uint64_t pc);`
  (was `(..., int bit)`).
- New member `uint64_t a03_fault_id = 0;` — 1-based fault ordinal of the
  persistent fault (activation application's `faults_injected_count + 1`).

### `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc`

- Call site in the `a03_bit3_stuck0_load` branch:
  `a03NoteEligibleLoad(dyn_seq, old_addr, addr, 3, pc);` (was `... 3);`).
  `pc` is the `maybeCorruptPre` parameter fed by
  `inst->pcState().instAddr()` at `lsq.cc:784-786`. No fault behavior
  changes: the `addr & ~0x8` mask and the no-change early return are untouched.
- `a03NoteEligibleLoad(..., uint64_t pc)` now derives
  `event_pc = pc ? pc : chaos_a01::kPcUnknown` and passes it to
  `chaos_a03::streamEvent(...)`, so `A03_STREAM` carries the real PC.
- The `Activation` record is filled with `event_ordinal`, `dyn_inst_seq`,
  `pc`, `golden_ea` at activation (the frozen `{tick, bit, mode}`
  `activationDetail` line is unchanged).
- The existing `registerExitCallback` (trigger path) emits exactly one
  observation-only line when the A03 stream activated:
  `A03_STUCK_LIFECYCLE: <lifecycleDetail>` to `addrpath_injections.log`
  (same stream/writer as `A03_ACTIVATION` / `A03_STREAM`).

### `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/a03_stream.hh` (pure header)

- `struct Activation` gains `event_ordinal`, `dyn_inst_seq`, `pc`,
  `golden_ea` (defaulted — `activationDetail` byte-identical).
- New `struct StuckLifecycle` with
  `fault_id, bit, mode, eligible_events, applications, already_stuck,
  has_activation, activation_{ordinal,dyn_inst_seq,pc,golden_ea},
  has_first_affected, first_affected_{ordinal,dyn_inst_seq,pc}`.
- New `std::string lifecycleDetail(const StuckLifecycle &l)` — frozen
  `k=v;k=v`, NO commas; counts decimal; PC/EA bare lowercase hex; absent
  identities `NOT_APPLICABLE`.
- `StreamRecorder` additions:
  - `uint64_t eligibleEvents() const` (= `recorded()`; the recorder only
    sees post-activation fired events, i.e. the applications of this one
    fault),
  - `bool hasFirstAffected() const`, `const StreamEvent &firstAffected() const`,
    set on the FIRST record whose `affected=1` (not merely the first record),
  - `StuckLifecycle lifecycle(uint64_t fault_id, const std::string &mode) const`.
- `record()` still rejects non-advancing ordinals exactly as before; the
  lifecycle counters ride on accepted records only (no double counting).

### `tests/test_addrpath_a03_stream.cc`

New assertions (existing style, `check(...)`):
- `streamEvent(1, 4242, 0x400558, ...)` → `e.pc == 0x400558`, detail contains
  `;pc=400558;` and does NOT contain `;pc=0;`.
- Lifecycle: activation row ordinal 1 is ALREADY_STUCK, ordinal 2 is the
  affected row, ordinal 3 is ALREADY_STUCK →
  `eligible_events=3, applications=1, already_stuck=2`;
  `first_affected_{ordinal,dyn_inst_seq,pc} = {2, 901, 0x400560}` (the first
  AFFECTED row, not the already-stuck activation row);
  `activation_{ordinal,seq,pc,golden_ea} = {1, 900, 0x400500, 0x100}`;
  detail string field-order/comma-free checks; an all-ALREADY_STUCK stream
  yields `first_affected_ordinal=NOT_APPLICABLE` (honest absence, not 0).

## 3. Verification (real command output)

```
$ g++ -O2 -std=c++17 -Wall -Wextra -I CHAOS/gem5/src tests/test_addrpath_a03_stream.cc -o /tmp/test_a03_v332 && /tmp/test_a03_v332; echo "EXIT=$?"
A03_STREAM_OK
EXIT=0
```

Unaffected-header regression (A01 coords, same include tree):

```
$ g++ -O2 -std=c++17 -Wall -Wextra -I CHAOS/gem5/src tests/test_addrpath_a01_coords.cc -o /tmp/test_a01_v332 && /tmp/test_a01_v332; echo "EXIT_A01=$?"
A01_COORDS_OK
EXIT_A01=0
```

No compiler warnings under `-Wall -Wextra`. `scons`/gem5 build was not run
(per the patch-author contract; the main agent builds once).

## 4. Semantic interpretation (the one thing this record is asserting)

**One persistent fault, five observation points.** The F5 A03 condition pins
one EA bit (bit 3 on the pilot path) from the activation event onward; the
`a03_stream` rows are successive APPLICATIONS of that same stuck bit at
eligible loads, not independent injections and not five separate faults
(R01–R05 are five activation-start positions of the same semantics).

`affected=0` / `ALREADY_STUCK` at activation is a **no-op application**:
the golden EA bit already equalled the stuck level at that load, so nothing
could propagate *from that load*. The fault is **not** cancelled — it stays
active and is re-applied at every later eligible load, where it can flip the
bit (STUCK_APPLIED) and propagate. The lifecycle record keeps `applications`
(affected=1) and `already_stuck` (affected=0) separate, and `first_affected`
names the earliest load at which this persistent fault actually changed the
EA — the earliest load at which propagation is even possible. A run whose
`already_stuck` equals `eligible_events` (and `first_affected` =
NOT_APPLICABLE) is a run where the persistent fault never changed any EA;
that is a distinct, reportable fact from "the injector never activated".

## 5. Residual issues / notes

- `kPcUnknown` remains only for the impossible-at-this-hook case `pc == 0`;
  there is no other PRE-hook caller of `maybeCorruptPre` in the tree
  (`grep -rn maybeCorruptPre` shows only `lsq.cc:784`).
- The lifecycle line is emitted only on the trigger path (the A03 pilot is
  F5-mounted by construction; the legacy cycle-window path has no activation
  concept and no lifecycle line — honest absence).
- The lifecycle line is written to `addrpath_injections.log` (simout, lost on
  abort), consistent with all other A03 lines; the abort-survivable copy
  remains the CHAOSPropagation `a03_activation` / `a03_stream` nodes, which
  are unchanged by this patch.
