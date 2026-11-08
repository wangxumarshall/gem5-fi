# MD04 source audit and definition (v3.2.6)

**State:** SOURCE_AUDITED (unified with the existing audit commit; the matrix
previously still said 0).

## Source finding that corrects the earlier audit

`DynInst::possibleLoadViolation(true)` at `lsq_unit.cc:637` is in the
`inst->isLoad()` branch of `LSQUnit::checkViolations` — a load/load ordering
flag that is consumed by the snoop path (`lsq_unit.cc:550`). It is **not**
the store→younger-load dependency violation used by W7.

W7 `replay_dependency` (a store `q[idx]=r` followed by `a[idx]` load through
an alias) hits the store branch of `checkViolations`: the function detects a
younger load that passed the store and returns `M5PanicFault` at
`lsq_unit.cc:655` (7 such detections in a no-fault run; 0
`possibleLoadViolation` lines). The unique MD04 fault is therefore defined
at that store→load detection:

> MD04-CFG01 (option A): suppress exactly one real same-address 8-byte store
> alias violation report. The store is 8 bytes at the load's start address;
> a wider load (16-byte LDP) that covers the store is a same-address alias
> and is included. A 4-byte pair or a different address is excluded. The
> younger load keeps its stale data and may commit it; addresses and sizes
> are never modified.

This is the single fault definition used by the implementation, unit test,
config and pilots.

## Frozen identity (Excel v3.2.1)

`MD04-F6-W7-S01`, W7 `replay_dependency`, oracle `59fc61c040618747`,
seeds 2595563470 / 811948497 / 2545691512 / 2149193331 / 1008734674,
EventOrdinal 1..5, injection `checkViolations`, F6, recommended option A
(`NEEDS_USER_DECISION` in the workbook; option A adopted and recorded).

## Hook

`LSQUnit::checkViolations`, store branch, before the `M5PanicFault` return:
`if (cpu->chaosMD04 && cpu->chaosMD04->maybeSkipViolation(ld_inst, inst,
load_complete)) break;`

Eligibility counts only real same-address 8-byte store aliases; the selected
1-based ordinal (`--md04_event_ordinal`) is suppressed once
(`maxFaults=1`). No address/size change.
