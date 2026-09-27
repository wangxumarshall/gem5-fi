# Campaign `ooo_w82_d15_rat_emb_wikisort` — summary

- injector: `rat`  config: `C3`  mode: `SE`
- cells: 1  reps done: 334  wall: 419s
- workload: `workloads/ooo/embench/wikisort/wikisort`  golden_id: `embenchwikisort-golden-v1`
- base_seed: 82015050  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| target_index=-1 field=map width_bits=7 sub_field=f5_rat_stuck fault_model=stuck_at_zero protection_model=none | 334 | 332 | 0.0% [0.0,1.1] | 88.9% [85.0,91.8] | 100.0% [98.9,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
