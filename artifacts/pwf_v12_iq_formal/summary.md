# Campaign `pwf_v12_iq_formal` — summary

- injector: `iq`  config: `C0`  mode: `SE`
- cells: 1  reps done: 384  wall: 5098s
- workload: `workloads/directed/stale_plausible_kernel`  golden_id: `staleplausible-golden-v1`
- base_seed: 20260911  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=transient_bit_flip | 384 | 384 | 0.0% [0.0,1.0] | 63.5% [58.6,68.2] | 100.0% [99.0,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
