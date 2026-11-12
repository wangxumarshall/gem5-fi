# LSU v3.3.3 — Formal Manifest Data-Isolation Audit

**File:** `tools/lsu_v333_launch.py` (rewritten)
**Tests:** `tests/test_lsu_v333_manifest_isolation.py` (6 passed) +
`tests/test_lsu_v333_synthetic.py` collector section (12 passed).

## 1. Single evidence root

Every evidence read is relative to the explicit campaign root:

```console
$ grep -c "audit_v3_3" tools/lsu_v333_launch.py
0
```

The collector reads, for each scheduled task:
`<runs>/<Model>-<ctx>-<role>/` → `campaign.json`, `summary.json`,
`trace_v31.jsonl`, `oracle.log`, `prop_trace.csv.gz`, model injection log.
Design CSVs (`--design-matrix`, `--design-mapping`) supply **identity only**
(SampleRunID, model, context, seed, workload, ROI, injection identity).

## 2. `--runs` controls all reads

`tests/test_lsu_v333_manifest_isolation.py` asserts that every record's
`Evidence` path resolves under `--runs`. The synthetic negative control
`historical_evidence/` (complete files, campaign id `SYNTH-V332-PRE-FORMAL`)
produces **zero** `EvidenceKind=FORMAL` records.

```console
campaign_clean       EXIT=0  formal=4 non_formal=0
campaign             EXIT=1  formal=24 non_formal=0 (defects recorded)
historical_evidence  EXIT=1  formal=0
```

## 3. EvidenceKind

`FORMAL` requires all of:

1. the run dir is under `--runs`;
2. `campaign.json.campaign_id == --campaign-id`;
3. `model/context/role/sample_run_id/seed` match the design row.

Otherwise the record is `NON_FORMAL` and cannot satisfy a formal gate.
A directory named `*formal*` is not sufficient evidence.

## 4. Missing fields never default to PASS/0

| Missing / broken | Record |
|---|---|
| run dir absent | `OUTPUT_INCOMPLETE` / `RUN_DIR_MISSING` |
| `campaign.json` absent | `OUTPUT_INCOMPLETE` / `MANIFEST_MISSING` |
| campaign id mismatch | `OUTPUT_INCOMPLETE` / `HISTORICAL_CAMPAIGN_MISMATCH` |
| identity mismatch | `OUTPUT_INCOMPLETE` / `ID_MISMATCH` |
| SHA missing | `OUTPUT_INCOMPLETE` / `SHA_MISSING` |
| SHA disagreement | `HASH_MISMATCH` |
| `summary.json` absent | `OUTPUT_INCOMPLETE` / `SUMMARY_MISSING` |
| required trace/oracle/log absent | `OUTPUT_INCOMPLETE` / `MISSING_REQUIRED_OUTPUT` |
| control counts absent | `CONTROL_PROOF_INCOMPLETE`, counts `UNKNOWN` |
| external timeout | `TIMEOUT` |

`InjectionCount` is `UNKNOWN` when the run does not provide it; it is never
silently written as 0.

## 5. Control zero-injection proof

Controls are graded by `lsu_v333_control_proof.classify_control_run()` on the
**current** run dir. It distinguishes `INJECTOR_ABSENT`,
`MOUNTED_BUT_DISABLED`, `MOUNTED_BUT_SUPPRESSED` (plus
`CONTROL_PROOF_INCOMPLETE`), records attempt/applied counts verbatim, and
fails when `injection_applied_count > 0`. Historical proofs are never read.

## 6. Qualified evidence

A03/SP05/RP01 fault runs additionally call
`lsu_v333_qualified.qualified_evidence(model, run_dir)`. `QUALIFIED` and
`TRACE_INCOMPLETE` are recorded as-is and are never upgraded; an external
timeout is never converted into an internal `HANG_WATCHDOG`.

## 7. No writes into run directories

All outputs go under `--out` (`LSU_120Run_Campaign_Manifest.csv`,
`LSU_60Fault_60Control_Pair_Map.csv`, `LSU_Control_Zero_Proof_Final.csv`,
`per_run/<dir>/campaign_manifest.json`). Fixture run dirs remain byte-clean
(`find tests/fixtures/lsu_v333_synthetic -name campaign_manifest.json` → empty).

## 8. Verdict

`Formal Evidence Source = Current Campaign Run Directory` — enforced by code
and by 18 passing isolation/collector tests.
