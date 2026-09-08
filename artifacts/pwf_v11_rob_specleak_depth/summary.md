# Campaign `pwf_v11_rob_specleak_depth` — summary

- injector: `rat`  config: `C2`  mode: `SE`
- cells: 3  reps done: 384  wall: 209s
- workload: `workloads/directed/spec_leak_probe_kernel`  golden_id: `specleakprobe-golden-v1`
- base_seed: 20260908  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=intermittent_burst target_index=10 rob=96 | 128 | 124 | 8.1% [4.4,14.2] | 11.3% [6.8,18.1] | 96.9% [92.2,98.8] | no |
| fault_model=intermittent_burst target_index=10 rob=128 | 128 | 122 | 9.8% [5.7,16.4] | 13.1% [8.2,20.2] | 95.3% [90.2,97.8] | no |
| fault_model=intermittent_burst target_index=10 rob=160 | 128 | 126 | 5.6% [2.7,11.0] | 19.0% [13.1,26.8] | 98.4% [94.5,99.6] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
