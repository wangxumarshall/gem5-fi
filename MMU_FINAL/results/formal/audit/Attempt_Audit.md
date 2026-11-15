# Attempt History Audit

Inventoried from the raw `attempt_A01/` and `attempt_A02/` directories, per-sample `sample_manifest.json`, `Validation/verdict.json`, `SHA256/SHA256SUMS.txt`, `Run_Log/` and `logs/*.result.json`. No count below is copied from the campaign summary.

## Verified counts

| Metric | Value |
|---|---|
| unique_sample_run_ids | 40 |
| completed_final_attempts | 40 |
| completed_superseded_attempts | 0 |
| interrupted_attempts | 2 |
| attempt_directories_total | 42 |
| a01_dirs | 40 |
| a02_dirs | 2 |

## Interrupted attempts

### M06-F0-W10-S01-R04 / A01

- Directory: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M06-F0-W10-S01-R04`
- Started: `gem5_stdout: Nov 13 2026 21:53:44`; finished: `n/a`
- Evidence: no sample_manifest.json; no Validation/verdict.json; no SHA256/SHA256SUMS.txt; no Run_Log/stats.txt; no gem5_exit_code.txt; no per-attempt logs/M06-F0-W10-S01-R04.result.json (campaign result JSON is for the adopted attempt only); trace gzip truncated (EOF before end marker)
- Partial trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M06-F0-W10-S01-R04/run/prop_evt.txt.gz` (28401 bytes, 308 events, truncated=True, fault activation observed: False)
- Binary SHA256: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`
- Config SHA256: `a81ddd11557ee388387f9a4f4174af764b1d2ca8087e289fec9e865050414484`
- Workload SHA256: `733b8a80150b9728b640fbaad0889f139b09b92a98462778753975a4917a63ae` (rcS.scoped embedded payload)

### M08-F0-W10-S01-R04 / A01

- Directory: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M08-F0-W10-S01-R04`
- Started: `gem5_stdout: Nov 13 2026 22:15:22`; finished: `n/a`
- Evidence: no sample_manifest.json; no Validation/verdict.json; no SHA256/SHA256SUMS.txt; no Run_Log/stats.txt; no gem5_exit_code.txt; no per-attempt logs/M08-F0-W10-S01-R04.result.json (campaign result JSON is for the adopted attempt only); trace gzip truncated (EOF before end marker)
- Partial trace: `/home/sdc/gem5-fi-mmu-impl-v2/runs/MMU_FORMAL_CAMPAIGN_20261113/attempt_A01/M08-F0-W10-S01-R04/run/prop_evt.txt.gz` (17254 bytes, 174 events, truncated=True, fault activation observed: False)
- Binary SHA256: `b3eb1559f742e86f1f9796e8ad21d0bb4f35ae1106d3ddae22b9df1eb91f7185`
- Config SHA256: `4c2af2633eec142a6e53f5b0860f91ef0fef066fc241dec6d5af7fbccc9afc74`
- Workload SHA256: `733b8a80150b9728b640fbaad0889f139b09b92a98462778753975a4917a63ae` (rcS.scoped embedded payload)

## Final attempt adoption

| Sample | Attempt | Status | Adopted | Reason |
|---|---|---|---|---|
| M06-F0-W10-S01-R04 | A01 | INTERRUPTED_PARTIAL | adopted=False | superseded by completed attempt A02; A01 lacks completion artifacts (see interruption evidence) and has a 0-byte stats file / truncated trace |
| M06-F0-W10-S01-R04 | A02 | COMPLETED_FINAL | adopted=True | adopted final attempt: status COMPLETED, gem5 exit 0, manifest+verdict+SHA256SUMS present; replaces interrupted A01 |
| M08-F0-W10-S01-R04 | A01 | INTERRUPTED_PARTIAL | adopted=False | superseded by completed attempt A02; A01 lacks completion artifacts (see interruption evidence) and has a 0-byte stats file / truncated trace |
| M08-F0-W10-S01-R04 | A02 | COMPLETED_FINAL | adopted=True | adopted final attempt: status COMPLETED, gem5 exit 0, manifest+verdict+SHA256SUMS present; replaces interrupted A01 |

For both retries the frozen binary and workload hashes are identical across A01/A02; the `ConfigSHA256` differs because `config.ini` embeds the absolute attempt `outdir` (3 occurrences), not because the parameters changed.


The A02 result JSONs record `status=COMPLETED`, `runner_exit_code=0`, `gem5_exit_code=0`, and start/finish times; A01 has no result JSON and no completion artifacts. The exact external signal that killed A01 is not recorded in the artifacts; the campaign report attributes it to an external process interruption, and the artifact state is consistent with that.
