# Campaign `p12_setB_l2` — summary

- injector: `l2`  config: `C0-CACHE`  mode: `SE`
- cells: 1  reps done: 20  wall: 17s
- workload: `workloads/directed/stencil_5pt_kernel`  golden_id: `stencil5pt-golden-v1`
- base_seed: 20260908  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=transient_bit_flip target_block_addr=4325376 | 20 | 20 | 50.0% [29.9,70.1] | 0.0% [0.0,16.1] | 100.0% [83.9,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
