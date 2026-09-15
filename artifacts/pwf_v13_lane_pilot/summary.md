# Campaign `pwf_v13_lane_pilot` — summary

- injector: `physreg`  config: `C0`  mode: `SE`
- cells: 4  reps done: 400  wall: 2089s
- workload: `workloads/directed/neon_lane`  golden_id: `neon-golden-v1`
- base_seed: 20260940  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=transient_bit_flip vec_lane=0 | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip vec_lane=1 | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip vec_lane=2 | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip vec_lane=3 | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
