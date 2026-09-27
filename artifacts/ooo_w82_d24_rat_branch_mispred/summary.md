# Campaign `ooo_w82_d24_rat_branch_mispred` — summary

- injector: `rat`  config: `C3`  mode: `SE`
- cells: 1  reps done: 2000  wall: 1928s
- workload: `workloads/ooo/branch_mispred/branch_mispred`  golden_id: `branchmispred-golden-v1`
- base_seed: 82024000  (rep seed = base + cell_ordinal*1000 + rep)
- counting (W3.2): event_coverage target_events=2000 density=490766 (source: counting.density (yaml)) -> n runs = ceil(target/density) = 2000

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| target_index=-1 field=checkpoint width_bits=7 sub_field=hb_bitflip2 fault_model=local_mbu protection_model=none | 2000 | 1989 | 0.1% [0.0,0.3] | 59.6% [57.4,61.7] | 100.0% [99.8,100.0] | no |

## Honesty notes

- Event-coverage n is derived from a MEAN density (event_density.py aggregate or operator value); actual covered events are not measured inline — verify from per-run evidence (faults_injected sums in results.jsonl, the W3.3 backfill rule) before quoting a coverage claim. A shortfall is reported in coverage.json, never silent.
- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
