# Campaign `prf_abiclass_pilot` — summary

- injector: `physreg`  config: `C2`  mode: `SE`
- cells: 30  reps done: 1500  wall: 1016s
- workload: `workloads/directed/cholesky_numeric`  golden_id: `cholesky-golden-v1`
- base_seed: 20260825  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| phys_mode=arch_frontend target_index=0 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=0 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=0 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=1 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 0 | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | no |
| phys_mode=arch_frontend target_index=1 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 0 | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | no |
| phys_mode=arch_frontend target_index=1 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=2 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 100.0% [92.9,100.0] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=2 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 100.0% [92.9,100.0] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=2 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=4 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=4 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=4 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=5 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 100.0% [92.9,100.0] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=5 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 100.0% [92.9,100.0] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=5 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=6 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=6 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=6 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=7 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=7 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=7 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=19 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=19 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=19 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=29 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=29 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=29 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=30 bit=0 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=30 bit=2 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |
| phys_mode=arch_frontend target_index=30 bit=31 fault_model=transient_bit_flip protection_model=none | 50 | 50 | 0.0% [0.0,7.1] | 0.0% [0.0,7.1] | 100.0% [92.9,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
