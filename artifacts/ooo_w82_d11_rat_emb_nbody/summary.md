# Campaign `ooo_w82_d11_rat_emb_nbody` — summary

- injector: `rat`  config: `C3`  mode: `SE`
- cells: 1  reps done: 728  wall: 1983s
- workload: `workloads/ooo/embench/nbody/nbody`  golden_id: `embenchnbody-golden-v1`
- base_seed: 82011040  (rep seed = base + cell_ordinal*1000 + rep)
- two_phase (W3.1): tiers=['F0', 'F1', 'F2'] pilot_n=20 pick_top=2 formal runs/selected tier=334; full selection: artifacts/ooo_w82_d11_rat_emb_nbody/tier_selection.json
  - cell 0: selected ['F0', 'F1'] (pilot non-Crash rates: F0=0.450, F1=0.300, F2=0.300)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| target_index=-1 field=map width_bits=7 sub_field=map_bitflip fault_model=transient_bit_flip protection_model=none | 668 | 653 | 0.0% [0.0,0.6] | 62.5% [58.7,66.1] | 100.0% [99.4,100.0] | no |

## Honesty notes

- Two-phase (W3.1) discipline: PILOT reps never enter the result columns (ooo 06 §1.3) — heatmap/summary aggregate FORMAL-phase runs only; pilot records live in runs/<cid>/cNNNN/pilot_results.jsonl + tier_selection.json.
- F1-F3 tiers are SINGLE-fault first_clock approximations (first_clock ~ U[0.5x, 1.5x) of the tier's mean interval 2.6M/260K/26K cycles, seed-derived per rep); the exact fixed-interval multi-injection F0-F5 semantics (cpu/o3/chaos_trigger.hh, ready on the gem5 side) land with the injector wiring batches.
- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
