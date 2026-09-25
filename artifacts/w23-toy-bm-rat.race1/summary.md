# Campaign `w23-toy-bm-rat` — summary

- injector: `rat`  config: `C3`  mode: `SE`
- cells: 1  reps done: 2  wall: 418s
- workload: `workloads/ooo/branch_mispred/branch_mispred`  golden_id: `branchmispred-golden-v1`
- base_seed: 20260924  (rep seed = base + cell_ordinal*1000 + rep)
- trace two-pass (W2.3): ref_run=`once` replay_for=`['SDC', 'Crash', 'Hang']` replayed reps: 2 (five-class commit_diff result + latency in each replayed rep's `l2` block in results.jsonl; ref traces at runs/<cid>/ctrace_ref_cNNNN.csv.gz)

## Per-cell (Wilson 95% CI)

| cell | n | n_valid | P_SDC [CI] | P_DUE [CI] | Reach [CI] | frozen |
|---|---|---|---|---|---|---|
| bit=0 fault_model=transient_bit_flip | 2 | 2 | 50.0% [9.5,90.5] | 50.0% [9.5,90.5] | 100.0% [34.2,100.0] | yes |

## Honesty notes

- Trace replay determinism relies on gem5 same-environment reproducibility (W2.1: two no-injection smoke traces are field-identical). A replay classification differing from pass 1 is recorded as replay_determinism=MISMATCH in the rep's l2 block — that mismatch is a finding, not noise to be dropped. All campaign children ran with PYTHONHASHSEED=0.
- This fault machine (cpu179) takes ~92s/run; formal n=384 belongs on a healthy 2nd machine (§0.4, §3.1 S6).
- `SimulatorError` counts are runs where the tool/simulator broke (gem5 panic or runner.py mapping error) — NOT valid FI outcomes; excluded from N_valid (§1.4).
- `frozen` cells failed the §1.5 replay-consistency check (same manifest gave different classification on re-run).
- Rates are conditional probabilities under the gem5 O3 + config family; NOT product FIT (§4.3).
