# Campaign `pwf_v12_l2_arms_pilot` — summary

- injector: `l2`  config: `C0-CACHE`  mode: `SE`
- cells: 4  reps done: 400  wall: 238s
- workload: `workloads/directed/stencil_5pt_kernel`  golden_id: `stencil5pt-golden-v1`
- base_seed: 20260915  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=transient_bit_flip target_field=data protection_model=none | 100 | 100 | 47.0% [37.5,56.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip target_field=data protection_model=secded | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip target_field=tag protection_model=none | 100 | 95 | 38.9% [29.8,49.0] | 0.0% [0.0,3.9] | 100.0% [96.1,100.0] | no |
| fault_model=transient_bit_flip target_field=tag protection_model=secded | 100 | 100 | 47.0% [37.5,56.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
