# MMU Final Formal Campaign Results Package

Campaign: `MMU-FORMAL-20261113`
Workspace: `/home/sdc/gem5-fi-mmu-impl-v2`
Binary SHA256: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`
Source closure: `60f1a8760410288128061d85582e5395b24c0106`

## Verdict

`FORMAL_CAMPAIGN_COMPLETE_WITH_LIMITATIONS`

| Metric | Value |
|---|---|
| Planned samples | 40 |
| Started samples | 40 |
| Completed samples | 40 |
| Valid injection evidence | 40 |
| Fault state consumed | 40 |
| Propagation chain complete (trace) | 40 |
| Legal terminal | 40 |
| Unfinished samples | 0 |
| Control runs referenced | 28 |
| Control zero proof | 28 / 28 |

Terminal distribution: {"SDC": 31, "SQUASHED": 4, "DETECTED_CONTAINED": 5}

## Why COMPLETE_WITH_LIMITATIONS

- 4 sample(s) end SQUASHED with PARTIAL downstream propagation by design (the faulted translation is squashed before a data-side consumer); their raw trace is COMPLETE.
- The frozen binary does not emit per-instruction IFU fetch-response, decode, or IFU-specific commit events; instruction-side samples use MMU translation/permission -> Execute Request -> Guest Oracle and mark the unobserved nodes NOT_EMITTED_BY_FROZEN_BINARY.
- Two samples were re-run under AttemptID A02 after an external process kill; original A01 partial attempts are preserved.

## Contents

- `40_Sample_Matrix_Completed.csv` — 40 SampleRunID completion matrix with
  CampaignID, Role, AttemptID and hashes.
- `fault_control_pairs.csv` — Fault -> approved independent control mapping.
- `control_zero_proof.json` — executed-config evidence of zero injection.
- `evidence_index/raw_trace_and_evidence_index.{csv,json}` — absolute paths
  and SHA256 for every manifest, verdict, oracle, config, stats and raw
  PROP-EVT trace.
- `propagation_chains/` — 40 structured chains (JSON + CSV).
- `diagnostic_features.json` — per-sample microarchitectural feature library.
- `model_specific_validation.{json,md}` — §10 gates, 40/40 PASS.
- `batch_acceptance.md`, `per_context_completeness.csv`.
- `MMU_Final_Formal_Campaign_Results.xlsx` — paper experiment workbook.
- `authority/` — frozen Excel, CSV, parameter authority, change log.
- `runner/` — frozen runner + validator + chain library copies.
- `provenance.json`, `failed_timeout_incomplete.md`.
- `extract_campaign.sh` — reproducible regeneration script.
- `SHA256_MANIFEST.txt` — hashes of every packaged file.

Raw traces remain at the absolute paths in
`evidence_index/raw_trace_and_evidence_index.csv` (not duplicated in this ZIP).

## Retries

M06 R04 and M08 R04 were interrupted by an external process kill during
Batch 3/4. The partial A01 directories are retained untouched; their formal
results are from a new AttemptID A02. No completed attempt was overwritten.
