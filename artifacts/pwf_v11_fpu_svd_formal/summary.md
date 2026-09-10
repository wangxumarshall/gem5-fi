# Campaign `pwf_v11_fpu_svd_formal` — summary

- injector: `fsu`  config: `C0`  mode: `SE`
- cells: 2  reps done: 768  wall: 184s
- workload: `workloads/directed/svd_iterative_kernel`  golden_id: `svditerative-golden-v1`
- base_seed: 20260909  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fpu_bitseg=mant_hi fault_model=transient_bit_flip | 384 | 384 | 92.4% [89.4,94.7] | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | no |
| fpu_bitseg=mant_lo fault_model=transient_bit_flip | 384 | 384 | 83.1% [79.0,86.5] | 0.0% [0.0,1.0] | 100.0% [99.0,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
