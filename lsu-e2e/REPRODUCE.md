# Reproduction guide

## 1. Environment

* Linux aarch64 host (the E2E workload binaries are statically linked ARM64).
* Python 3.11, pytest >= 8.
* gem5 build prerequisites: `scons`, a C++17 compiler, `python3`, `m4`,
  `zlib`, and the packages required by `CHAOS/gem5/requirements.txt`.
* No network access is required after cloning.

## 2. Build gem5

```bash
cd CHAOS/gem5
scons build/ARM/gem5.opt -j16
ls -l build/ARM/gem5.opt
```

The final source commit is `2bbf2907668f78e0b67473caf5a63153b70bede3`.
The build must produce the ARM `gem5.opt` binary.

## 3. Workloads

The 60 E2E-instrumented binaries (12 families x 5 contexts) are included
under `lsu-e2e/code/workloads/bin/`, with `MANIFEST.csv` and `SHA256SUMS`.
To rebuild and re-check them against the frozen goldens:

```bash
cd lsu-e2e/code/workloads
./build_e2e_workloads.sh
```

The script uses the local `frozen/` goldens by default; set
`LSU_FROZEN_WORKLOADS=/path/to/frozen/bin` if you have another copy.

## 4. Single representative fault

```bash
./lsu-e2e/run_representative.sh fault
```

This runs `E2E-A01-C03-T01` with the frozen command line and produces:

```text
lsu-e2e/code/results/smoke/A01-C03-T01-FAULT/
  prop_trace.csv.gz
  commit_trace.csv.gz
  micro_snap.csv.gz
  stdout.log
  ...
```

## 5. Paired control

```bash
./lsu-e2e/run_representative.sh control
```

The control uses the same binary/config and the count-only eligible-event
census; it produces the same trace set under `.../A01-C03-CTRL/`.

## 6. Full 180 fault + 60 control matrix

```bash
./lsu-e2e/run_campaign.sh --help
./lsu-e2e/run_campaign.sh --jobs 8 --resume
```

The wrapper exports the clone-relative paths and invokes
`code/runner/e2e_experiment.py`. The runner covers:

* 12 models: A01, A03, DA04, FW02, FW05, LP01, LQ04, MD04, RP01, SP05,
  SQ01, SQ03;
* C01-C05 contexts;
* T01/T02/T03 timings (10/50/90 percent of the eligible stream);
* one count-only control per model x context.

## 7. Propagation traces

Every run is invoked with:

```text
--chaos_propagation --prop_replay_all --prop_trace_file prop_trace.csv.gz
--chaos_ctrace --ctrace_file commit_trace.csv.gz
--chaos_msnap --msnap_every 200 --msnap_file micro_snap.csv.gz
```

The `prop_trace.csv.gz` is the LSQ/cache/commit propagation stream;
`commit_trace.csv.gz` is the per-instruction architectural trace used for
the semantic walk. Both are produced in each run's `attempt_1/` directory.

## 8. Result checks

```bash
# Code-level tests (do not need the frozen evidence archive)
python3 -m pytest lsu-e2e/code/tests/test_arm64_semantics.py \
                   lsu-e2e/code/tests/test_strict_edges.py -q

# The full acceptance suite also needs the frozen evidence ZIP
# (causal-chain JSONs, semantic ledger, 262 MB aggregate edge CSV).
```

The frozen acceptance results are recorded in
`lsu-e2e/verification/FINAL_PYTEST.txt` and the final reports in
`lsu-e2e/reports/`.

## 9. Verify against the frozen release

Compare:

* `lsu-e2e/FREEZE_MANIFEST.json` (status, checks, counts, source hashes)
* `lsu-e2e/reports/FINAL_STATISTICS_RECONCILIATION.md`
* `lsu-e2e/reports/FINAL_ROOT_CAUSE_MATRIX_180.csv`
* `lsu-e2e/reports/FINAL_EVIDENCE_MANIFEST.csv`

Expected canonical totals: 180/180 `E2E_CAUSAL_COMPLETE`, 712,998 edges,
180 faults, 60 controls, 15 RP01 watchdog runs, 6 historical squash cells.
