# Strict E2E reproduction guide

All commands are local; no network or remote write is used.

## 1. Rebuild the strict analysis from the raw traces

```bash
cd /home/sdc/gem5-fi-LSU/e2e_extension
python3 runner/e2e_strict_engine.py --jobs 8
python3 runner/e2e_rp01_audit.py
python3 runner/e2e_squash_audit.py
python3 runner/e2e_observation_equiv.py
python3 runner/e2e_strict_deliver.py
python3 runner/e2e_semantic_audit.py
```

The analysis reads only `results/faults/*/attempt_1/commit_trace.csv.gz`,
`prop_trace.csv.gz`, `stdout.log`, the paired control caches and the
instrumented ELF disassembly. No previous causal_chain.json is used.

## 2. Rebuild the RP01 observation binary (only if the source changed)

```bash
cd /home/sdc/gem5-fi-LSU/repo/CHAOS/gem5
scons -j16 build/ARM/gem5.opt
cp build/ARM/gem5.opt /home/sdc/gem5-fi-LSU/e2e_extension/bin/gem5.opt.obs
cd /home/sdc/gem5-fi-LSU/e2e_extension
python3 runner/e2e_rp01_rerun.py --jobs 5
```

The observation code is read-only: it adds ROB/IQ/LSQ accessors and a
post-injection sampler. It does not change the replay-skip rule, the RNG,
the ordinal selection or any fault parameter.

## 3. Re-run one sample

```bash
python3 runner/e2e_strict_engine.py --runs E2E-A01-C01-T01-FAULT
python3 -m pytest tests -q
```

## 4. Semantic revalidation

The full per-instruction ledger is
`reports/SEMANTIC_REVALIDATION_ALL_180.csv`; every pre-repair mismatch is
reconciled in `reports/SEMANTIC_MISMATCH_RECONCILIATION.csv`.  The gate is
part of `validate_end_to_end_graph()`: a run cannot be COMPLETE with a
semantic mismatch, a critical unsupported instruction, an unverified
taint edge, unverified NZCV, incomplete pair-memory semantics or a
dropped taint source.  The expected totals are in
`reports/SEMANTIC_STATISTICS.json`.

## 5. Integrity and frozen package

```bash
sha256sum -c LSU_E2E_PAPER_FINAL_FROZEN.zip.sha256
unzip -t LSU_E2E_PAPER_FINAL_FROZEN.zip
```

The freeze directory is `LSU_E2E_PAPER_FINAL_FROZEN/`; large original
traces stay in `e2e_extension/results/` and are bound by absolute path,
size and SHA256 in `STRICT_E2E_LARGE_TRACE_MANIFEST.csv`.  Per-run
binary/ELF/config hashes are in each strict JSON's `versions`, in
`STRICT_E2E_EVIDENCE_INDEX.csv` and in the 60-control index.

## 6. Freeze rule

After `LSU_E2E_PAPER_FINAL_FROZEN_20261118` is created, the frozen
commit, the 12 fault models, the 180-run matrix and the reported
statistics are read-only.  New review-driven work must start from a new
research branch, never by editing the frozen version.
