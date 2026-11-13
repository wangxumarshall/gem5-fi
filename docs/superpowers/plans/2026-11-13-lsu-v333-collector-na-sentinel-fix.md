# LSU v3.3.3 — collector N/A-sentinel and stale-workload-name fix

**Date:** 2026-11-13
**Authorized by:** researcher, after Stage 2 failed closed on the real 120-run campaign.
**Scope:** collection tooling only. **No change** to Binary, Config, Seed, SampleRunID,
Workload, campaign design, or any of the 120 raw run directories.

## Observed failure (real, from the formal campaign)

`02_manifest_only.sh` exited 1 with `formal=60, non_formal=60`:

```
NON_FORMAL: HASH_MISMATCH: FW02-R03-fault (SHA_DISAGREEMENT; missing=design.InputHash)
... (FW02, SQ01, SQ03, SP05, MD04, RP01 × 5 contexts × 2 roles = 60)
```

## Root cause (evidence-backed)

1. `tools/lsu_v333_launch.py:_base_record` derives `Workload`/`ELF` from the
   design matrix `WorkloadPath`. For six models that column still carries
   abstract, stale names (`sq_forward`, `store_path`, `sq_drain`,
   `replay_dependency`) pointing at the `lsu-platform-v3.2` worktree. The real
   formal run used the authorized ROI-mapped ELFs
   (`sq_forward_w4v2`, `sq_reload_v3212`, `md04_violations_v332`,
   `replay_partial_v332`), and all 120 `campaign.json` carry their real 64-hex
   `elf_sha`, matching the dry-run hashes.
2. The SHA gate falls back to `matrix_row["InputHash"]` only when the workload
   name is absent from `campaign_identity["elf_sha"]`. For those six models it
   is absent, so the fallback runs.
3. The fallback *intends* to skip when the design matrix has no input hash
   (`not in (None, "", NOT_AVAILABLE)`), but `NOT_AVAILABLE` is the lowercase
   `"n/a"` while the matrix uses `"N/A"` and `无（内建输入）`. The literal
   sentinel is therefore compared against the ELF SHA and always disagrees.

**Conclusion:** false-negative grading defect. The 120 runs and their evidence
are complete and identity-consistent.

## Fix (one unit, one commit)

In `tools/lsu_v333_launch.py`:

- [x] Normalize not-available sentinels (`N/A`, `n/a`, `无（内建输入）`, …) so a
      missing design `InputHash` skips the comparison instead of failing it.
- [x] When the design-matrix workload name is not present in
      `campaign_identity["elf_sha"]`, recover the real ELF basename by matching
      the run's own `elf_sha` against that map, and correct the record's
      `Workload`.
- [x] After reading `summary.json`, take `Workload`/`ELF` from the run's own
      evidence (authoritative), so the manifest never reports the stale
      design-matrix path.
- [x] Never weaken the gate: if no authorized hash matches, the record still
      fails `HASH_MISMATCH`.

### Second defect found after the first fix (same file, separate unit)

After the sentinel fix, Stage 2 graded 115/120; the five RP01 **controls** were
`OUTPUT_INCOMPLETE: missing=trace_v31.jsonl`.  The authorized runner's own
`required_outputs()` only requires `trace_v31.jsonl` when
`driver_for(model, role) == "run_pilot"`; RP01 is always `direct`, so the
runner never promised that artifact for RP01 controls.  Their raw
`prop_trace.csv.gz` (12,818 rows), `summary.json` (injection_count=0,
oracle=true) and `oracle.log` are present.  Fix: mirror the runner's rule and
require the converted trace only for `run_pilot`-driven tasks.  No other check
is relaxed.

## Verification (real commands, quoted in the commit message)

- [x] `pytest tests/test_lsu_v333_final_launch_acceptance.py tests/test_lsu_v333_synthetic.py tests/test_lsu_v333_manifest_isolation.py`
- [x] `bash audit_v3_3_3/trace_closure/final_config/02_manifest_only.sh` → must
      report `formal=120 non_formal=0` and exit 0.
- [x] `03_full_collector.sh` and `04_final_reports.sh` complete.
- [x] SP05 R01–R05 stay `QUALIFIED`; RP01 R01–R05 stay `TRACE_INCOMPLETE`.
