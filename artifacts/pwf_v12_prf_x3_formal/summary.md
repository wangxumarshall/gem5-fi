# Campaign `pwf_v12_prf_x3_formal` — summary

- injector: `physreg`  config: `C2`  mode: `SE`
- cells: 2  reps done: 768  wall: 188s
- workload: `workloads/directed/cholesky_numeric`  golden_id: `cholesky-golden-v1`
- base_seed: 20260825  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=transient_bit_flip bit=0 target_index=3 rob=96 | 384 | 384 | 100.0% [99.0,100.0] | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | no |
| fault_model=transient_bit_flip bit=0 target_index=3 rob=128 | 384 | 384 | 100.0% [99.0,100.0] | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
