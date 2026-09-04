# Campaign `prf_bitseg_pilot` — summary

- injector: `physreg`  config: `C2`  mode: `SE`
- cells: 12  reps done: 1200  wall: 1094s
- workload: `workloads/directed/cholesky_numeric`  golden_id: `cholesky-golden-v1`
- base_seed: 20260825  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| phys_mode=arch_frontend target_index=3 bit=0 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=3 bit=11 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=3 bit=31 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=3 bit=32 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=3 bit=47 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=3 bit=63 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=9 bit=0 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=9 bit=11 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=9 bit=31 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=9 bit=32 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=9 bit=47 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| phys_mode=arch_frontend target_index=9 bit=63 fault_model=transient_bit_flip protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
