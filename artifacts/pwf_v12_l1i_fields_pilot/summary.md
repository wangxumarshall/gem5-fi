# Campaign `pwf_v12_l1i_fields_pilot` — summary

- injector: `l1i`  config: `C0-CACHE`  mode: `SE`
- cells: 12  reps done: 1200  wall: 31009s
- workload: `workloads/directed/l1i_loop`  golden_id: `l1iloop-golden-v1`
- base_seed: 20260925  (rep seed = base + cell_ordinal*1000 + rep)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| fault_model=transient_bit_flip l1i_field=opcode protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 2.0% [0.6,7.0] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=opcode protection_model=sed | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=rn protection_model=none | 100 | 99 | 1.0% [0.2,5.5] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=rn protection_model=sed | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=rm protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=rm protection_model=sed | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=rd protection_model=none | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=rd protection_model=sed | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=imm12 protection_model=none | 100 | 100 | 1.0% [0.2,5.4] | 1.0% [0.2,5.4] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=imm12 protection_model=sed | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |
| fault_model=transient_bit_flip l1i_field=cond protection_model=none | 100 | 98 | 0.0% [0.0,3.8] | 0.0% [0.0,3.8] | 100.0% [96.2,100.0] | no |
| fault_model=transient_bit_flip l1i_field=cond protection_model=sed | 100 | 100 | 0.0% [0.0,3.7] | 0.0% [0.0,3.7] | 100.0% [96.3,100.0] | no |

## Honesty notes

- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
