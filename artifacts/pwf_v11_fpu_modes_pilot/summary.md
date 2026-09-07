# Campaign `pwf_v11_fpu_modes_pilot` — summary

- injector: `fsu`  config: `C0`  mode: `SE`
- cells: 6  reps done: 600  wall: 587s
- workload: `workloads/directed/elemwise_fma_kernel`  golden_id: `elemwisefma-golden-v1`
- base_seed: 20260907  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fpu_bitseg=sign fault_model=transient_bit_flip | 100 | 100 | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fpu_bitseg=exp_hi fault_model=transient_bit_flip | 100 | 100 | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fpu_bitseg=exp_lo fault_model=transient_bit_flip | 100 | 100 | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fpu_bitseg=mant_hi fault_model=transient_bit_flip | 100 | 100 | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fpu_bitseg=mant_mid fault_model=transient_bit_flip | 100 | 100 | 100.0% [96.3,100.0] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fpu_bitseg=mant_lo fault_model=transient_bit_flip | 100 | 100 | 99.0% [94.6,99.8] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
