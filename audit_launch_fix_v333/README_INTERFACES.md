# LSU v3.3.3 Launch-Critical Fix — Interfaces & Ownership

**Baseline:** HEAD 58d77b34; source b5031bf7; binary 1126e0fd; config 8309da72.
**Scope:** Python only. No C++/gem5 rebuild, no seed/ID/ROI/workload change, no
re-run of the 120 pre-formal runs.

## Campaign root and evidence isolation

- The formal campaign root is the explicit `--runs <CampaignRoot>` passed to the
  collector. Every evidence read (summary.json, trace_v31.jsonl, prop_trace,
  oracle.log, model logs, command.txt, campaign.json) MUST be under this root.
- Design sources (frozen `60_SAMPLE_MATRIX.csv` and the v3.3.3 ROI mapping) are
  separate `--design-matrix` / `--design-mapping` inputs; they define identity,
  seed, ROI, percentile and ordinal only, never run evidence.
- Historical `audit_v3_3_3/...` evidence MUST NOT be read by the formal
  collector. If the collector cannot derive a value from the campaign root, it
  writes an INCOMPLETE status; it never defaults to 0/PASS.
- Each formal run dir must contain `campaign.json` written by the runner:
  `{campaign_id, model, context, role, sample_run_id, seed, status, binary_sha,
  config_sha, elf_sha, started_at, ended_at, exit_code, timed_out}`.
  A run without a matching `campaign.json` is NON_FORMAL/INCOMPLETE.

## Status vocabulary (runner + collector)

`PENDING, RUNNING, COMPLETED, FAILED, TIMEOUT, OUTPUT_INCOMPLETE,
HASH_MISMATCH, ORACLE_FAIL, CONTROL_PROOF_INCOMPLETE`

- `ORACLE_FAIL` is a valid measured experimental terminal (SDC), not a runner
  failure. It is recorded; it does not by itself make the campaign exit nonzero.
- Execution/integrity failures (`FAILED`, `TIMEOUT`, `OUTPUT_INCOMPLETE`,
  `HASH_MISMATCH`, `CONTROL_PROOF_INCOMPLETE`) make the campaign exit nonzero.

## Module interfaces

- `tools/lsu_v333_control_proof.py`
  `classify_control_run(run_dir: Path) -> dict`:
  keys `injector_mounted, fault_enabled, suppression_reason,
  injection_attempt_count, injection_applied_count, proof_class, status,
  evidence`; `proof_class` in `INJECTOR_ABSENT`,
  `MOUNTED_BUT_DISABLED`, `MOUNTED_BUT_SUPPRESSED`,
  `CONTROL_PROOF_INCOMPLETE`; `status` in `PASS`, `FAIL`,
  `CONTROL_PROOF_INCOMPLETE`. Missing summary/count => INCOMPLETE (never 0/PASS);
  `injection_applied_count > 0` => FAIL.

- `tools/lsu_v333_qualified.py`
  `qualified_evidence(model: str, run_dir: Path) -> dict`:
  keys `model, required_fields, found, missing, status, terminal_rule, evidence`;
  `status` in `PASS`, `QUALIFIED`, `TRACE_INCOMPLETE`. Only A03/SP05/RP01 have
  extra rules; other models return PASS with `required_fields=[]`.
  Never upgrade QUALIFIED/TRACE_INCOMPLETE to PASS.

- Collector `tools/lsu_v333_launch.py` (owned by Agent B):
  CLI `--runs <CampaignRoot> --campaign-id <id> --design-matrix ... --design-mapping ... --out ... --manifest-only`.
  It imports the two modules above. Missing summary/trace/oracle/SHA/ID/seed =>
  INCOMPLETE record, never PASS; EvidenceKind `FORMAL` only for a run under
  CampaignRoot with matching campaign_id; otherwise `NON_FORMAL`.

## File ownership (disjoint)

- Agent A: `tools/lsu_v332_matrix.py`, `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`, `tests/test_lsu_v333_runner_errors.py`.
- Agent B: `tools/lsu_v333_launch.py`, `tests/test_lsu_v333_manifest_isolation.py`.
- Agent C: `tools/lsu_v333_control_proof.py`, `tests/test_lsu_v333_control_proof.py`.
- Agent D: `tools/lsu_v333_qualified.py`, `tests/test_lsu_v333_qualified.py`, `audit_launch_fix_v333/artifacts/LSU_QUALIFIED_Context_Handling.md`.
- Agent E: `tests/fixtures/lsu_v333_synthetic/`, `tests/test_lsu_v333_synthetic.py`, `audit_launch_fix_v333/reports/Agent_E_Independent_Acceptance.md`.

No agent may edit another agent's files; the main agent integrates and commits.
