# Campaign `pwf_v12_exec_formal` — summary

- injector: `exec`  config: `C0`  mode: `SE`
- cells: 2  reps done: 768  wall: 509s
- workload: `workloads/directed/elemwise_int_kernel`  golden_id: `elemwiseint-golden-v1`
- base_seed: 20260910  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=transient_bit_flip | 384 | 384 | 69.5% [64.8,73.9] | 20.1% [16.4,24.3] | 100.0% [99.0,100.0] | no |
| fault_model=recurring_result_stuck | 384 | 384 | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | 100.0% [99.0,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
