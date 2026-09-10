# Campaign `ptw_h7_pilot_fs` — summary

- injector: `ptw`  config: `C0-FS`  mode: `FS`
- cells: 4  reps done: 12  wall: 2566s
- workload: `workloads/directed/cholesky_numeric`  golden_id: `cholesky-golden-v1`
- base_seed: 20260825  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| target_index=0 fault_model=transient_bit_flip protection_model=none | 3 | 3 | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% [43.9,100.0] | yes |
| target_index=0 fault_model=transient_bit_flip protection_model=secded | 3 | 3 | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% [43.9,100.0] | yes |
| target_index=0 fault_model=stuck_at_zero protection_model=none | 3 | 3 | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% [43.9,100.0] | yes |
| target_index=0 fault_model=stuck_at_zero protection_model=secded | 3 | 3 | 0.0% [0.0,56.1] | 0.0% [0.0,56.1] | 100.0% [43.9,100.0] | yes |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
