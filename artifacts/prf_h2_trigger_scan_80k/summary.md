# Campaign `prf_h2_trigger_scan_80k` — summary

- injector: `physreg`  config: `C2`  mode: `SE`
- cells: 3  reps done: 90  wall: 60s
- workload: `workloads/directed/cholesky_numeric`  golden_id: `cholesky-golden-v1`
- base_seed: 20260825  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=128 fault_model=transient_bit_flip protection_model=none | 30 | 30 | 0.0% [0.0,11.4] | 0.0% [0.0,11.4] | 100.0% [88.6,100.0] | no |
| phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=160 fault_model=transient_bit_flip protection_model=none | 30 | 30 | 0.0% [0.0,11.4] | 0.0% [0.0,11.4] | 100.0% [88.6,100.0] | no |
| phys_mode=arch_frontend target_index=3 bit=0 rob=160 phys_int=192 fault_model=transient_bit_flip protection_model=none | 30 | 30 | 0.0% [0.0,11.4] | 0.0% [0.0,11.4] | 100.0% [88.6,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
