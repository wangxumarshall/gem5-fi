# MD04 final fault definition (frozen 2026-11-08)

## Identity

- Model: MD04
- Name: Suppression of Store-to-Load Violation Detection
- Chinese name: Store-to-Load违规检测抑制故障
- FaultConfigID: MD04-CFG01 (definition version `MD04-DEF-v2`)
- Unit / subunit: LSU / Violation Detection
- Target function: `LSQUnit::checkViolations`
- Target field: `M5PanicFault` return path (store → younger-load branch)

## Hook location (source-verified)

`CHAOS/gem5/src/cpu/o3/lsq_unit.cc`:

- `LSQUnit::checkViolations` starts at line 585.
- The store branch (`else` of `if (inst->isLoad())`) begins at line 646.
- The MD04 hook is lines 652–662, immediately before the real
  `return std::make_shared<GenericISA::M5PanicFault>(...)` at lines 676–679.
- The load/load `possibleLoadViolation(true)` flag is a different mechanism
  (line 642, consumed by the snoop path); the v3.2.1 workbook wording
  `possibleLoadViolation` is the superseded definition and is replaced in
  v3.2.2.

## Fault mechanism

For exactly one selected real store-to-younger-load violation event, skip the
normal `M5PanicFault` return. The load keeps its stale data and may commit
it. This is a detection/report suppression:

- no load-data modification;
- no store-data modification;
- no address change;
- no access-size change;
- no global disabling of `M5PanicFault`;
- no change to unrelated LSQ state.

## Eligibility (`MD04-ELIG-v1`)

Let S be the older store, L the younger load, and `dep_check_shift` the same
constant used by `checkViolations` (currently 3). Eligible iff ALL hold:

1. S is a real store with valid effective address and size exactly 8 bytes.
2. L is a real load with valid effective address; `L.seq > S.seq`.
3. The real byte ranges overlap:
   `S.addr + 7 >= L.addr` and `L.addr + L.size - 1 >= S.addr`.
4. The real gem5 range predicate also holds at the same shift granularity:
   `(S.addr+7)>>shift >= L.addr>>shift` and
   `S.addr>>shift <= (L.addr+L.size-1)>>shift`.
5. `L.size >= 8`. A 16-byte LDP covering the store is included; a 4-byte
   access is excluded.
6. Different, non-overlapping addresses are excluded even if they share an
   8-byte chunk.

The first matching pair is the dynamic violation event; pairs are numbered
1-based by the order in which `checkViolations` evaluates them. This ordinal
is `EligibleViolationPairOrdinal`. The Excel `EventOrdinal` is the design
target ordinal (which eligible pair to suppress), not a violation-pair count.
The two are recorded separately and never conflated.

## Injection scope

- Injection count: exactly 1 per sample (`maxFaults=1`).
- Probability: 1.0 for the selected ordinal; no random fallback.
- If the target ordinal is never reached, the run records
  `FaultActivationStatus=NOT_TRIGGERED` and
  `CHAOS_MD04_TARGET_STATUS=ORDINAL_NOT_REACHED`; no event is fabricated.
- If the target pair is reached, only that pair's report is skipped; later
  checks are unchanged. The hook does not switch to a later event when the
  target is absent.

## Trace identity (required for every injection)

TargetPairID, OlderStoreDynamicInstSeqNum, YoungerLoadDynamicInstSeqNum,
StorePC, LoadPC, StoreAddress, LoadAddress, StoreSize, LoadSize, SQEntryID,
SQGeneration, LQEntryID, LQGeneration, ViolationTick,
EligibleViolationPairOrdinal, EventOrdinal, Seed, SampleRunID,
load_request_id, injection execution_attempt_id, replay_generation.

## Provenance

- `MD04_Source_Audit_v3.2.6.md` corrected the `possibleLoadViolation`
  misreading: the W7 store→younger-load detection is the `M5PanicFault`
  return in the store branch of `checkViolations`.
- The researcher confirmed option A on 2026-11-08 and fixed the final
  definition in the v3.2.7 work order.
- Code, Excel v3.2.2, manifest, trace and the model status matrix must all
  cite this file. The revision history is in
  `excel/MD04_OLD_NEW_DIFF_v3.2.2.md`.
