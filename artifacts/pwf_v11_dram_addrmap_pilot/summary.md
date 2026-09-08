# Campaign `pwf_v11_dram_addrmap_pilot` — summary

- injector: `memory`  config: `C0`  mode: `SE`
- cells: 1  reps done: 100  wall: 712s
- workload: `workloads/directed/stream_triad_kernel`  golden_id: `streamtriad-golden-v1`
- base_seed: 20260908  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=stuck_at_one mem_addr_start=4194304 mem_addr_end=5242880 | 100 | 100 | 88.0% [80.2,93.0] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
