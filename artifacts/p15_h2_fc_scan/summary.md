# Campaign `p15_h2_fc_scan` — summary

- injector: `physreg`  config: `C2`  mode: `SE`
- cells: 1  reps done: 10  wall: 4s
- workload: `workloads/directed/cholesky_numeric`  golden_id: `cholesky-golden-v1`
- base_seed: 20260825  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=transient_bit_flip bit=0 target_index=3 rob=160 | 10 | 10 | 0.0% [0.0,27.8] | 0.0% [0.0,27.8] | 100.0% [72.2,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
