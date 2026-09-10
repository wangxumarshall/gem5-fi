# Campaign `pwf_v11_rob_specleak_formal` — summary

- injector: `rat`  config: `C0`  mode: `SE`
- cells: 3  reps done: 384  wall: 133s
- workload: `workloads/directed/spec_leak_probe_kernel`  golden_id: `specleakprobe-golden-v1`
- base_seed: 20260908  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=intermittent_burst target_index=10 | 128 | 121 | 16.5% [11.0,24.2] | 0.0% [0.0,3.1] | 94.5% [89.1,97.3] | no |
| fault_model=intermittent_burst target_index=9 | 128 | 0 | 0.0% [0.0,0.0] | 0.0% [0.0,0.0] | 0.0% [0.0,2.9] | no |
| fault_model=intermittent_burst target_index=3 | 128 | 128 | 0.0% [0.0,2.9] | 0.0% [0.0,2.9] | 100.0% [97.1,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
