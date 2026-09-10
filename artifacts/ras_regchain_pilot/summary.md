# Campaign `ras_regchain_pilot` — summary

- injector: `memory`  config: `C0`  mode: `SE`
- cells: 1  reps done: 5  wall: 10s
- workload: `workloads/directed/ras_checksum_kernel`  golden_id: `raschecksum-golden-v1`
- base_seed: 20260825  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| phys_mode=arch_frontend target_index=0 fault_model=transient_bit_flip protection_model=none | 5 | 5 | 0.0% [0.0,43.4] | 0.0% [0.0,43.4] | 100.0% [56.6,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
