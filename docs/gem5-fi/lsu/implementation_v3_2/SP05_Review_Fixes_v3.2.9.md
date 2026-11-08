# SP05 review fixes (v3.2.9)

Final review found one Critical and one Important defect; both were fixed with
RED→GREEN evidence on the final binary `303c610d…`.

## Critical — legacy forward-corruption hook armed in SP05 mode

`CHAOSLSQFwd::corrupt()` did not list `Sp05Complete` as an inert structural
mode, so the legacy post-forward bit_flip could fire, write only the
log (no trace node) and consume the shared `faults_injected_count` before
SP05's own one-shot.

RED (pre-fix binary `d6e60863…`, `sq_forward`, ordinal 100, seed 1489155957):
`Cycle: 1445, Site: store->load_forward, FaultType: bit_flip` and
`CHAOS_SP05_STATUS: ... fired=0 injected=1` — the completion never injected.

GREEN (post-fix `303c610d…`, same command): zero `store->load_forward`
lines; `commitStores_select` at 4598, `writebackStores_prematureComplete`
at 4599, `CHAOS_SP05_STATUS: selected=1 fired=1 injected=1 eligible=100`.
The five standard pilots and controls are unchanged (MASKED, golden).

## Important — selection counted unreachable stores

The ordinal counted every newly-canWB store, but `writebackStores` completes
zero-size stores at `lsq_unit.cc:961` and skips prefetches at 969 before the
SP05 check. `chaos_sp05::isSelectable(size, prefetch)` now gates the count;
unit test extended first (compile failed with `isSelectable` undeclared),
then implemented. `SP05 completion rules: PASS`.

## Minor (fixed)

- `sp05WatchdogCycles` doc string now says cycles (it is a `Cycles` value).
- `sp05_complete` added to the v3.1 converter KIND_MAP/UNIT_MAP so unit
  filters see the completion node; `inj_sp05` extra fields are already mapped.
