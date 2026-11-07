# MD04 source audit (LSU v3.2.5 handoff)

**State:** DESIGNED / SOURCE_AUDITED. No code or workload change in this
commit. MD04 implementation needs its own plan before any patch.

## Frozen identity (Excel v3.2.1)

| Field | Value |
|---|---|
| ModelID | MD04 (Memory Dependency 漏报) |
| Unit | MD |
| InjectionMode | F6 |
| SubTaskID / RunID | `MD04-F6-W7-S01` / `MD04-F6-W7` |
| Workload | W7 `replay_dependency` (present in `implementation_v3_2/workloads/`) |
| Fault location | violation detection `checkViolations` |
| Target field | `possibleLoadViolation` |
| Normal value | alias detected → `possibleLoadViolation=true` |
| Fault value | skip one setting (forced false negative) |
| Recommended option | A: same-address 8-byte alias false negative |
| Oracle | `59fc61c040618747` |
| Seeds R01–R05 | 2595563470, 811948497, 2545691512, 2149193331, 1008734674 |
| EventOrdinal | 1..5 |
| Expected propagation | MD check → issue/replay → Load data → Commit |
| Expected observation | false negative → load uses stale data → commit → SDC |
| Decision status | NEEDS_USER_DECISION (A recommended) |

## Hook mapping (current tree)

- `LSQUnit::checkViolations(LoadQueue::iterator&, DynInst*, …)` —
  `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:580`.
- The normal set is `ld_inst->possibleLoadViolation(true)` at
  `lsq_unit.cc:637`.
- The consuming check is `ld_inst->possibleLoadViolation()` at
  `lsq_unit.cc:550` (squash decision).
- Accessor in `CHAOS/gem5/src/cpu/o3/dyn_inst.hh:434` / setter at `:439`.

A portable MD04 fault point is therefore: before the setter at
`lsq_unit.cc:637`, for a real same-address alias (option A), suppress the
single setting for the selected eligible event (F6 semantics; `maxFaults=1`).
Identity/address/size must not change; only the violation flag is skipped.

## Safety

Data-only effect, no address/size change. The risk is a false-negative
(load consumes stale data) → potential SDC; the trace must correlate the
suppressed check with that load, its response/writeback, consumers and
commit. SE address semantics from `LSU_v3.2.5_SE_Address_Semantics.md`
apply (VA matching; no FS PA).

## Next step

Write `docs/superpowers/plans/YYYY-MM-DD-lsu-v326-md04.md` before code. Do
not modify `CHAOS/gem5/src` in this handoff commit.
