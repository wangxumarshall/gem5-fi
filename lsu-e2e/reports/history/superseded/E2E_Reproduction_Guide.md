# E2E reproduction guide

All commands are local; no network/remote write is used.

## 1. Build the instrumented workloads

```bash
cd /home/sdc/gem5-fi-LSU/e2e_extension
./workloads/build_e2e_workloads.sh
```

The script builds 8 families x 5 contexts, verifies every native checksum
against the frozen When-v2 golden, and writes `workloads/MANIFEST.csv`.

## 2. Run the campaign (60 controls + 180 faults)

```bash
cd /home/sdc/gem5-fi-LSU/e2e_extension
# controls first
python3 runner/e2e_experiment.py --phase census --jobs 16 --retries 2 --resume
# faults (ordinals come from each new control's eligible census)
python3 runner/e2e_experiment.py --phase faults --jobs 24 --retries 2 --resume
```

Every run directory contains `command.txt`, `stdout.log`, `stderr.log`,
`commit_trace.csv.gz` (v2), `prop_trace.csv.gz`, `micro_snap.csv.gz`,
`stats.txt`, and the injector ledger. States are under `results/state/`;
`--resume` skips only runs whose ELF, binary and config hashes still match.

## 3. Rebuild the software-event caches and site catalogue

```bash
python3 runner/e2e_cache.py
python3 runner/e2e_catalog.py
```

## 4. Reconstruct all 180 causal chains

```bash
python3 runner/e2e_analyze.py --jobs 16
```

Outputs: `evidence/causal_chains/<RunID>.causal_chain.{json,csv}` and
`<RunID>.causal_report.md`.

## 5. Rebuild the acceptance matrices and reports

```bash
python3 runner/e2e_deliver.py
```

## 6. Single-run reproduction

```bash
python3 runner/e2e_experiment.py --phase all   --models A01 --contexts C01 --timings T02 --jobs 1 --resume
python3 runner/e2e_analyze.py --runs E2E-A01-C01-T02-FAULT
```

The injector command line is recorded verbatim in
`results/faults/<RunID>/attempt_1/command.txt`.
