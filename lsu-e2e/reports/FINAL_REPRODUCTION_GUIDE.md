# FINAL reproduction guide

## Scope and environment

* gem5 ARM O3CPU, Syscall Emulation (SE) only; no full-system runs.
* Python 3.11 (tested: 3.11), pytest >= 8.
* gem5 source commit `2bbf2907668f78e0b67473caf5a63153b70bede3`
  (branch in the original workspace), built for ARM.
* No network access is required for package-internal checks.

## Package layout

```
code/runner/     analysis, freeze and report generators
code/tests/      pytest suites (self-contained path resolution)
code/configs/, code/workloads/, code/gem5_observation/
evidence/causal_chains/   180 chains (JSON + per-run CSV + MD)
evidence/rp01/           15 observation chains + canonical stall traces
evidence/controls/       60-control evidence indexes
evidence/semantic/       before/reconciliation/revalidation ledgers, stats
evidence/squash/         six historical squash audit files
evidence/manifest/       raw-trace manifest and checksum lists
reports/                 FINAL_* authoritative reports
verification/            executed test and checksum evidence
```

## Package-internal checks (no server data needed)

```bash
unzip LSU_E2E_PAPER_FINAL_FROZEN*.zip
cd LSU_E2E_PAPER_FINAL_FROZEN*
python -m pytest code/tests -q
sha256sum -c SHA256SUMS
```

Expected: 0 failed, 0 errors, and every SHA256SUMS line OK. The package
suite contains one explicitly documented skip: the server raw-trace hash
test (`SERVER_EVIDENCE_REQUIRED`), which requires
`LSU_E2E_SERVER_EVIDENCE=1` and is executed and recorded separately on the
server (`verification/FINAL_SERVER_EVIDENCE_TEST.txt`). No key acceptance
test is skipped.

`reports/FINAL_EVIDENCE_MANIFEST.csv` has a `Scope` column: `PACKAGE` rows
resolve from the package root via `RelativePath`; `SERVER_WORKSPACE` rows
(735 original traces) resolve via `AbsolutePath` on the original server and
are marked `SERVER_EVIDENCE_NOT_IN_PACKAGE` if only the package is present.

## Original server evidence

Raw prop/commit traces stay in the original workspace
`/home/sdc/gem5-fi-LSU/e2e_extension/results/` (faults and controls) and
`results_strict_rp01/` (RP01 reruns). Their size/SHA256 are recorded in
`reports/FINAL_EVIDENCE_MANIFEST.csv` and
`evidence/manifest/STRICT_E2E_LARGE_TRACE_MANIFEST.csv`. To verify them on
the server:

```bash
cd /home/sdc/gem5-fi-LSU/e2e_extension
python -m pytest tests -q
python runner/e2e_final_reports.py        # deterministic regeneration
```

The package extraction does not need those absolute paths; the
server-evidence verification is reported separately in
`verification/FINAL_SHA256_VALIDATION.txt`.

## Regenerating statistics

```bash
python code/runner/e2e_final_reports.py --root .
```

The generator reads only the 180 chain JSONs and the semantic/control
tables, and rewrites the `FINAL_*` reports. It asserts 180 chains, 15 RP01
chains, 57 masked runs, 20 IVD runs, 180 complete graphs and the documented
edge total.

## Verification of a specific run

1. Open `reports/FINAL_ROOT_CAUSE_MATRIX_180.csv` and select the RunID.
2. Open `evidence/causal_chains/<RunID>.causal_chain.json`: `nodes`,
   `edges`, `semantic_walk` and `software` carry the raw evidence line
   numbers.
3. For RP01, open `evidence/rp01/RP01OBS-<C>-<T>-FAULT.strict.json` and the
   corresponding `stall_traces/*.csv.gz`.
4. Cross-check `reports/FINAL_SOFTWARE_SYMPTOMS.csv` and
   `reports/FINAL_PROPAGATION_TERMINATION.csv`.

## Semantic record accounting

The all-180 ledger contains different record types and they must not be
conflated:

* semantic revalidation records: **1141566**;
* sentinel rows: **27** (12 `NO_TAINTED_INSTRUCTION` and 15
  `RP01_SEPARATE_TRACE`);
* CSV data rows: **1141593** = 1141566 + 27.

`SEMANTIC_STATISTICS.json` points to
`evidence/semantic/SEMANTIC_REVALIDATION_ALL_180.csv.gz`. Only the
1141566 revalidation rows are instruction-semantic checks.

## Observation Instrumentation Impact and Validity

The E2E binaries are observation-instrumented. From
`STRICT_E2E_OBSERVATION_EQUIVALENCE.csv` (60 paired controls):

* 60/60 control output checksums agree;
* 60/60 E2E ELF hashes differ from the original frozen ELF;
* 60/60 dynamic execution streams changed;
* 33/60 eligible-event counts are unchanged and
  27/60 changed;
* 26/60 timing-ordinal sets changed.

Injection timing was re-enumerated on the instrumented build: each fault
targets an eligible event selected from the observation-instrumented
execution. A fault and its paired control use the same E2E binary, ELF and
configuration. The conclusions therefore describe the instrumented SE
execution environment. This study does not claim that instrumentation
leaves the original dynamic execution stream unchanged, and output-checksum
agreement is not evidence of an identical dynamic trace. This is a
methodological boundary, not an experimental defect, and requires no rerun.

## Historical squash

In the six When-v2 cases the target fault instruction was squashed, but the
direct cause was an unrelated control-flow recovery event
(`FaultCausedSquash = 0`, `SquashCause = unrelated`). The speculative result
of the fault instruction was subsequently withdrawn and never entered
architectural state; the fault itself did not trigger the squash. The six
cases are an independent historical set, excluded from the 180-run
denominator.
