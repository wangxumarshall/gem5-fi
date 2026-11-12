# LSU v3.3.3 Launch-Critical Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the two formal-campaign launch blockers (runner failure/timeout exit semantics; formal collector reading historical PRE_FORMAL evidence) and produce the launch-readiness package, without changing models, SampleRunIDs, seeds, ROI, workloads, C++, or the frozen binary.

**Architecture:** The work lives in the existing LSU worktree `lsu-platform-v3.2.12` (branch `lsu-v3.3.1-context-workload-20261111`, HEAD `58d77b34`, source `b5031bf7`, binary `1126e0fd…`). The runner (`tools/lsu_v332_matrix.py`) already carries the v3.3.3 status vocabulary, preflight SHA gates, process-group timeout kill and per-run `campaign.json`. The missing unit is the formal collector `tools/lsu_v333_launch.py`: it must be rewritten to derive **every** evidence value from `--runs <CampaignRoot>` (+ explicit design-only inputs), import `lsu_v333_control_proof` and `lsu_v333_qualified`, refuse to default missing fields to 0/PASS, and mark `EvidenceKind=FORMAL` only for a run whose `campaign.json` matches `--campaign-id` and sits under the campaign root.

**Tech Stack:** Python 3.11, pytest, stdlib only (csv/json/hashlib/pathlib); no gem5/scons invocation in tests.

**Spec:** This round's task brief (`LSU v3.3.3 — Launch-Critical Fix & Final Formal Campaign Readiness`, tasks A–E) + `audit_launch_fix_v333/README_INTERFACES.md` (frozen interfaces/ownership) + `audit_launch_fix_v333/reports/Agent_E_Independent_Acceptance.md` (current evidence and findings F-E1…F-E6).

## Global Constraints

- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`; branch `lsu-v3.3.1-context-workload-20261111`. Do not create another worktree.
- Python-only changes. No C++ edit, no `scons`, no gem5 run, no re-execution of the 120 pre-formal runs.
- Frozen identity: 12 models, 60 `SampleRunID`, 60 seeds, 60 ROI percentiles, approved workloads — read-only.
- Binary SHA256 `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`; config SHA256 `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`.
- Evidence isolation: the formal collector must never read `audit_v3_3_3/**`, `audit_v3_3_2/**` or any historical run dir. Design CSVs (`60_SAMPLE_MATRIX.csv`, ROI mapping) are identity-only inputs.
- Status vocabulary: `PENDING, RUNNING, COMPLETED, FAILED, TIMEOUT, OUTPUT_INCOMPLETE, HASH_MISMATCH, ORACLE_FAIL, CONTROL_PROOF_INCOMPLETE`. `ORACLE_FAIL` (SDC) and `QUALIFIED`/`TRACE_INCOMPLETE` for A03/SP05/RP01 are measured terminals; `FAILED/TIMEOUT/OUTPUT_INCOMPLETE/HASH_MISMATCH/CONTROL_PROOF_INCOMPLETE` force campaign exit ≠ 0.
- Never upgrade `QUALIFIED`/`TRACE_INCOMPLETE` to `PASS`; never turn an external timeout into an internal `HANG_WATCHDOG`.
- One patch per unit: each task below is exactly one commit; stage explicit paths only (`git add <paths>`), never `git add -A`.
- Commit messages: `[LSU][V3.3.3][LAUNCH-FIX] <unit>`; no `Co-Authored-By` trailer.

## Review Focus

- A run whose `summary.json` says COMPLETED but whose `timed_out`/`exit_code` says otherwise (fixture `campaign_partial/A01-R02-control`); the collector must trust the stricter evidence, never `campaign.json.status` alone.
- A control with no injection counts anywhere (fixture `A01-R05-control`); the result must be `CONTROL_PROOF_INCOMPLETE`/`UNKNOWN`, never a silent `0`.
- A historical run root whose `campaign.json` is complete but carries a different `campaign_id` (fixture `historical_evidence/`); it must be `NON_FORMAL` and never satisfy a formal gate.
- A run dir that does not exist under the campaign root; the collector must emit an `OUTPUT_INCOMPLETE` record, not skip the task.
- A fault run whose model log/trace was cut by an internal watchdog (A03/RP01); it is a measured terminal (`HANG_WATCHDOG`), never `TIMEOUT`, and its missing causal fields stay `QUALIFIED`/`TRACE_INCOMPLETE`.

---

### Task 1: Land Agent A — runner error/timeout/exit status

**Files:**
- Modify: `tools/lsu_v332_matrix.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`
- Test: `tests/test_lsu_v333_runner_errors.py`

**Interfaces:**
- Consumes: nothing from later tasks.
- Produces: `preflight_task(...)`, `validate_outputs(...)`, `measured_status(...)`, `terminal_source(...)`, `campaign_record(...)`, `campaign_exit_code(rows)`, `planned_command(model, ctx_idx, role, outdir)`, `main(argv)`; per-run `campaign.json` fields `campaign_id, model, context, role, sample_run_id, seed, status, binary_sha, config_sha, elf_sha, started_at, ended_at, exit_code, timed_out, terminal_source`.

- [x] **Step 1: Review the uncommitted diff for scope**

Run: `git diff --stat tools/lsu_v332_matrix.py docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`
Expected: only runner/status/timeout/preflight concerns; no model/seed/ROI/workload edits.

- [x] **Step 2: Run the runner suite**

Run: `python3 -m pytest tests/test_lsu_v333_runner_errors.py -q -p no:cacheprovider`
Expected: `32 passed`.

- [x] **Step 3: Dry-run proves 120 commands and no writes**

Run: `python3 tools/lsu_v332_matrix.py --dry-run --out-base /tmp/lsu_dryrun_t1`
Expected: last line `dry-run: 120 commands; no run dirs written`; `/tmp/lsu_dryrun_t1` does not exist.

- [x] **Step 4: Commit**

```bash
git add tools/lsu_v332_matrix.py docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py tests/test_lsu_v333_runner_errors.py
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] harden runner exit, timeout and per-task status"
```

---

### Task 2: Land Agent C — control zero-injection proof

**Files:**
- Create: `tools/lsu_v333_control_proof.py`
- Create: `tests/test_lsu_v333_control_proof.py`
- Create: `audit_launch_fix_v333/artifacts/LSU_Control_Zero_Proof_Final.csv`

**Interfaces:**
- Consumes: per-run `summary.json`, `pilot_meta.json`, `command.txt`, `trace_v31.jsonl`, model logs.
- Produces: `classify_control_run(run_dir: Path) -> dict` with keys `injector_mounted, fault_enabled, suppression_reason, injection_attempt_count, injection_applied_count, proof_class, status, evidence`; `proof_class ∈ {INJECTOR_ABSENT, MOUNTED_BUT_DISABLED, MOUNTED_BUT_SUPPRESSED, CONTROL_PROOF_INCOMPLETE}`; `status ∈ {PASS, FAIL, CONTROL_PROOF_INCOMPLETE}`.

- [x] **Step 1: Run the control suite**

Run: `python3 -m pytest tests/test_lsu_v333_control_proof.py -q -p no:cacheprovider`
Expected: all pass (part of the 41 passed in the prior combined run).

- [x] **Step 2: Verify the 60-row pre-formal proof CSV is labeled PRE_FORMAL**

Run: `wc -l audit_launch_fix_v333/artifacts/LSU_Control_Zero_Proof_Final.csv && head -1 audit_launch_fix_v333/artifacts/LSU_Control_Zero_Proof_Final.csv | tr ',' '\n' | grep -c EvidenceKind`
Expected: `61` rows (header + 60), header contains `EvidenceKind`.

- [x] **Step 3: Commit**

```bash
git add tools/lsu_v333_control_proof.py tests/test_lsu_v333_control_proof.py audit_launch_fix_v333/artifacts/LSU_Control_Zero_Proof_Final.csv
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] classify control zero-injection proof from run evidence"
```

---

### Task 3: Land Agent D — A03/SP05/RP01 qualified evidence rules

**Files:**
- Create: `tools/lsu_v333_qualified.py`
- Create: `tests/test_lsu_v333_qualified.py`
- Create: `audit_launch_fix_v333/artifacts/LSU_QUALIFIED_Context_Handling.md`

**Interfaces:**
- Consumes: run dir only (`summary.json`, `oracle.log`, model logs, `trace_v31.jsonl`, `prop_trace.csv[.gz]`).
- Produces: `qualified_evidence(model: str, run_dir: Path) -> dict` with keys `model, required_fields, found, missing, status, terminal_rule, evidence`; `status ∈ {PASS, QUALIFIED, TRACE_INCOMPLETE}`; non-A03/SP05/RP01 models return `PASS` with empty `required_fields`.

- [x] **Step 1: Run the qualified suite**

Run: `python3 -m pytest tests/test_lsu_v333_qualified.py -q -p no:cacheprovider`
Expected: all pass.

- [x] **Step 2: Verify never-upgrade behavior on the truncated RP01 fixture**

Run: `python3 -c "import importlib.util as u;from pathlib import Path;s=u.spec_from_file_location('q','tools/lsu_v333_qualified.py');m=u.module_from_spec(s);s.loader.exec_module(m);print(m.qualified_evidence('RP01',Path('tests/fixtures/lsu_v333_synthetic/campaign/RP01-R01-fault'))['status'])"`
Expected: `TRACE_INCOMPLETE`.

- [x] **Step 3: Commit**

```bash
git add tools/lsu_v333_qualified.py tests/test_lsu_v333_qualified.py audit_launch_fix_v333/artifacts/LSU_QUALIFIED_Context_Handling.md
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] enforce A03/SP05/RP01 qualified evidence rules"
```

---

### Task 4: Land Agent E — synthetic fixtures and runner integration tests

**Files:**
- Create: `tests/fixtures/lsu_v333_synthetic/**` (generator + payload + design + campaign roots)
- Create: `tests/test_lsu_v333_synthetic.py`
- Create: `audit_launch_fix_v333/reports/Agent_E_Independent_Acceptance.md`

**Interfaces:**
- Consumes: runner, control, qualified modules; collector CLI per README.
- Produces: module-scope fixtures `campaign_out, clean_out, partial_out, historical_out`; 12 collector tests currently skipped with `PENDING (Agent B)`.

- [x] **Step 1: Run the synthetic suite**

Run: `python3 -m pytest tests/test_lsu_v333_synthetic.py -q -p no:cacheprovider`
Expected: `24 passed, 12 skipped`; skips say `PENDING (Agent B)`.

- [x] **Step 2: Verify fixture regeneration is deterministic**

Run: `python3 tests/fixtures/lsu_v333_synthetic/build_fixtures.py --check`
Expected: exit 0 / "identical" report (per builder CLI).

- [x] **Step 3: Commit**

```bash
git add tests/fixtures/lsu_v333_synthetic tests/test_lsu_v333_synthetic.py audit_launch_fix_v333/reports/Agent_E_Independent_Acceptance.md
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] add synthetic fixtures and runner integration checks"
```

---

### Task 5: Agent B — rewrite the formal collector for campaign-root isolation

**Files:**
- Modify: `tools/lsu_v333_launch.py` (full rewrite of evidence layer; keep artifact/XLSX export helpers)
- Create: `tests/test_lsu_v333_manifest_isolation.py`

**Interfaces:**
- Consumes: `classify_control_run`, `qualified_evidence`, design matrix CSV (`SampleRunID, FaultModelID, Seed, WorkloadPath, BinarySHA256`), ROI mapping CSV (`ModelID, ContextID, SampleRunID, Seed, ROI_*, InjectionIdentity`), campaign root (`campaign_identity.json`, per-run `campaign.json`).
- Produces: CLI `--runs --campaign-id --design-matrix --design-mapping --out --manifest-only --expected-binary-sha --expected-config-sha`; `main(argv) -> int`; records with at least `RunID, ModelID, ContextID, SampleRunID, Seed, Role, Status, EvidenceKind, Evidence, TerminalState, OracleResult, InjectionCount, ControlZeroProof, QualifiedStatus, MissingEvidence, Reason, Binary_SHA256, Config_SHA256, ELF_SHA256`.

- [x] **Step 1: Write the failing isolation test file**

`tests/test_lsu_v333_manifest_isolation.py` must assert, using temp roots built from the synthetic fixtures:
1. a record's `Evidence` value always starts with the `--runs` root (`Path(record["Evidence"]).resolve().is_relative_to(Path(runs).resolve())`);
2. changing `--runs` to `historical_evidence` yields zero `EvidenceKind=FORMAL` records;
3. `campaign.json` with no summary yields `Status=OUTPUT_INCOMPLETE` and no numeric `InjectionCount`;
4. a matching-campaign complete run yields `EvidenceKind=FORMAL`.

- [x] **Step 2: Run it to verify it fails**

Run: `python3 -m pytest tests/test_lsu_v333_manifest_isolation.py -q -p no:cacheprovider`
Expected: FAIL (old CLI lacks `--campaign-id`; no `Status` column).

- [x] **Step 3: Implement the collector**

Required behavior, in order:
1. Load design matrix → expected `(model, context, role)` task list (60 pairs → 120 records). Nothing else is scheduled.
2. For each task, `run_dir = Path(args.runs)/f"{model}-{ctx}-{role}"`.
3. Read `campaign.json`; require `campaign_id == args.campaign_id`, matching `model/context/role/sample_run_id/seed`, and non-empty `binary_sha/config_sha/elf_sha`. Any failure ⇒ `EvidenceKind=NON_FORMAL` and `Status=OUTPUT_INCOMPLETE` (or `HASH_MISMATCH` for SHA disagreement), with `Reason` naming the exact defect. Never read a fallback directory.
4. Read `summary.json`; missing ⇒ `OUTPUT_INCOMPLETE`. Cross-check its `seed/model/context/role` and SHAs against `campaign.json`; disagreement ⇒ `HASH_MISMATCH`.
5. SHA gate: `campaign.json` SHAs must equal `--expected-binary-sha/--expected-config-sha` and, when present, `campaign_identity.json` SHAs. ELF SHA must equal `campaign_identity.json.elf_sha[workload basename]` (or the design matrix `InputHash` when the identity map is absent). Disagreement ⇒ `HASH_MISMATCH`.
6. Status resolution (strictest evidence wins): `timed_out`/`exit_code==124` in campaign or summary ⇒ `TIMEOUT`; model watchdog marker with terminal `HANG_WATCHDOG` and no timeout ⇒ `COMPLETED`; missing required outputs (`summary.json`, `trace_v31.jsonl`, `oracle.log`; fault also model log unless A03/RP01 partial set) ⇒ `OUTPUT_INCOMPLETE`; control runs call `classify_control_run` and adopt `FAIL`/`CONTROL_PROOF_INCOMPLETE`; fault runs with terminal `SDC` ⇒ `ORACLE_FAIL`; other measured terminals ⇒ `COMPLETED`; else `FAILED`.
7. Identity fields (`DynInstSeq/PC/VA/PA/LQEntry/SQEntry`) come from the design mapping `InjectionIdentity`, never from a historical causal CSV. `TraceCompleteness` comes from `summary.trace_completeness.trace_completeness`, else `qualified_evidence(...).status`.
8. EvidenceKind `FORMAL` iff the run dir is under `--runs`, `campaign.json.campaign_id` matches, and identity matches; otherwise `NON_FORMAL`.
9. Write `LSU_120Run_Campaign_Manifest.csv`, `LSU_60Fault_60Control_Pair_Map.csv`, `LSU_Control_Zero_Proof_Final.csv`, and `per_run/<dir>/campaign_manifest.json` under `--out`. Do not write into the campaign run dirs.
10. Return 0 iff every scheduled record has `EvidenceKind=FORMAL` and `Status ∈ {COMPLETED, ORACLE_FAIL, QUALIFIED, TRACE_INCOMPLETE(qualified models only)}`; otherwise return 1.

- [x] **Step 4: Run the isolation tests and the collector half of the synthetic suite**

Run: `python3 -m pytest tests/test_lsu_v333_manifest_isolation.py tests/test_lsu_v333_synthetic.py -q -p no:cacheprovider`
Expected: all pass, 0 skipped; `campaign_clean` exit 0, `campaign`/`campaign_partial`/`historical_evidence` exit ≠ 0.

- [x] **Step 5: Commit**

```bash
git add tools/lsu_v333_launch.py tests/test_lsu_v333_manifest_isolation.py
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] isolate formal manifest collection to the campaign root"
```

---

### Task 6: Runner diagnostics and campaign identity gaps found by Agent E

**Files:**
- Modify: `tools/lsu_v332_matrix.py`
- Test: `tests/test_lsu_v333_runner_errors.py`

**Interfaces:**
- Consumes: Task 1 runner.
- Produces: `parse_error` present in `summary.json` and the RAW CSV; `campaign_identity.json` at `--out-base` with `{campaign_id, binary_sha, config_sha, elf_sha:{workload: sha}}`; RP01 control command carries `--rng_seed`.

- [x] **Step 1: Add failing assertions to the runner suite**

Tests: (a) a run with an injected parse error has `summary["parse_error"]` and a `parse_error` column in the RAW CSV; (b) `main(--dry-run)`-adjacent `write_campaign_identity(...)` writes all four keys; (c) `planned_command("RP01", 1, "control", out)` contains the frozen seed.

- [x] **Step 2: Run to verify failure**

Run: `python3 -m pytest tests/test_lsu_v333_runner_errors.py -q -p no:cacheprovider`
Expected: 3 new failures.

- [x] **Step 3: Implement**

Add `parse_error` to the final `summary.update(...)` and to `write_csv` keys; add `write_campaign_identity(out_base, campaign_id)` called from `main` before the task loop; pass `--rng_seed` in `build_rp01_cmd` for both roles.

- [x] **Step 4: Run to verify pass + regression**

Run: `python3 -m pytest tests/test_lsu_v333_runner_errors.py tests/test_lsu_v333_synthetic.py -q -p no:cacheprovider`
Expected: all pass.

- [x] **Step 5: Commit**

```bash
git add tools/lsu_v332_matrix.py tests/test_lsu_v333_runner_errors.py
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] record parse errors, campaign identity and paired RP01 seed"
```

---

### Task 7: Full-suite verification, 120-task dry-run, collision and resource checks

**Files:**
- Create: `audit_launch_fix_v333/reports/LSU_120Run_Dryrun_Report.md`
- Create: `audit_launch_fix_v333/reports/LSU_Launch_Critical_Fix_Unit_Test_Report.md`

- [x] **Step 1: Run every LSU v3.3.3 suite**

Run: `python3 -m pytest tests/test_lsu_v333_runner_errors.py tests/test_lsu_v333_control_proof.py tests/test_lsu_v333_qualified.py tests/test_lsu_v333_manifest_isolation.py tests/test_lsu_v333_synthetic.py -q -p no:cacheprovider`
Expected: all pass, 0 skipped, 0 failed.

- [x] **Step 2: Capture the 120-task dry-run**

Run: `python3 tools/lsu_v332_matrix.py --dry-run --out-base /tmp/lsu_v333_dryrun > /tmp/lsu_v333_dryrun.log 2>&1; echo EXIT=$?; grep -c '^DRY-RUN ' /tmp/lsu_v333_dryrun.log; grep '^dry-run:' /tmp/lsu_v333_dryrun.log`
Expected: `EXIT=0`, `120`, `dry-run: 120 commands; no run dirs written`.

- [x] **Step 3: Prove uniqueness, pairing and non-collision from the dry-run text**

Run: `python3 - <<'PY'` … parse `/tmp/lsu_v333_dryrun.log`, assert 120 unique `(model,ctx,role)` triplets, 60 fault/control pairs with identical seed and ordinal, 120 unique `--outdir=` values, and print counts. `PY`
Expected: `tasks=120 unique=120 pairs=60 collision=0`.

- [x] **Step 4: Resource check**

Run: `nproc; free -g | head -2; ls -lh /home/sdc/gem5-fi-ding/build/ARM/gem5.opt; sha256sum /home/sdc/gem5-fi-ding/build/ARM/gem5.opt docs/gem5-fi/lsu/implementation_v3_2/lsu_proxy.py 2>/dev/null || true`
Expected: SHA line equals `1126e0fd…`; host has ≥29 GB RAM; ≤4 concurrent gem5 is the documented cap.

- [x] **Step 5: Write both reports with the real command output pasted in**

- [x] **Step 6: Commit**

```bash
git add audit_launch_fix_v333/reports/LSU_120Run_Dryrun_Report.md audit_launch_fix_v333/reports/LSU_Launch_Critical_Fix_Unit_Test_Report.md
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] record full-suite and 120-task dry-run evidence"
```

---

### Task 8: Reconcile stale status reports and freeze the authoritative causal CSV

**Files:**
- Create: `audit_launch_fix_v333/artifacts/LSU_60Context_Causal_Propagation_Final.csv` (copy of the authoritative source)
- Create: `audit_launch_fix_v333/artifacts/LSU_ARCHIVED_Propagation_Versions.csv`
- Create: `audit_launch_fix_v333/reports/LSU_Stale_Status_Reconciliation.md`

- [x] **Step 1: Locate every causal-propagation CSV and diff A01/RP01 labels**

Run: `find . -name 'LSU_60Context_Causal_Propagation*.csv' -not -path './.git/*' -exec sha256sum {} \;`
Expected: one authoritative 16-column file, older copies under `audit_v3_3_2/`/`audit_v3_3_3/propagation/`.

- [x] **Step 2: Verify A01 and RP01 rows against current Excel/manifest**

Confirm A01 terminal is `SDC` (not the old unclosed status) and RP01 is `HANG_WATCHDOG`/`NO_CHECKSUM` with `QUALIFIED`, never `PASS`. Record mismatches in the reconciliation report. Do not edit historical raw traces/summaries/oracles.

- [x] **Step 3: Mark archives**

Write `LSU_ARCHIVED_Propagation_Versions.csv` with `Path,SHA256,Status=ARCHIVED` for every non-authoritative copy.

- [x] **Step 4: Commit**

```bash
git add audit_launch_fix_v333/artifacts/LSU_60Context_Causal_Propagation_Final.csv audit_launch_fix_v333/artifacts/LSU_ARCHIVED_Propagation_Versions.csv audit_launch_fix_v333/reports/LSU_Stale_Status_Reconciliation.md
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] freeze authoritative causal CSV and reconcile stale labels"
```

---

### Task 9: Build the launch-critical fix package

**Files:**
- Create: `audit_launch_fix_v333/reports/{LSU_Launch_Critical_Fix_Report.md,LSU_Runner_Error_Handling_Audit.md,LSU_Formal_Manifest_Data_Isolation_Audit.md,LSU_Final_Binary_Provenance.md,LSU_Final_Launch_Readiness_Report.md,LSU_Independent_Acceptance.md}`
- Create: `audit_launch_fix_v333/artifacts/LSU_120Run_Formal_Manifest_Schema.csv`
- Create: `LSU_v3.3.3_Launch_Critical_Fix_Package.zip`

- [x] **Step 1: Derive the manifest schema CSV from the collector's `MANIFEST_COLS` and record types**

Include one row per column with `Column,Type,RequiredForPASS,Source`; every evidence column's `Source` must be `CampaignRoot` or `DesignMatrix/DesignMapping`.

- [x] **Step 2: Write the reports with exact command output** (runner audit, isolation audit, binary provenance, qualified handling, unit-test report, dry-run report, readiness report, independent acceptance). The readiness verdict must state one of `READY_TO_LAUNCH_FORMAL_CAMPAIGN / PARTIALLY_READY / NOT_READY` and list A03/SP05/RP01 QUALIFIED limits without upgrading them.

- [x] **Step 3: Build and hash the package**

Run: `cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12 && zip -qr LSU_v3.3.3_Launch_Critical_Fix_Package.zip audit_launch_fix_v333 tools/lsu_v332_matrix.py tools/lsu_v333_launch.py tools/lsu_v333_control_proof.py tools/lsu_v333_qualified.py tests/test_lsu_v333_*.py tests/fixtures/lsu_v333_synthetic && sha256sum LSU_v3.3.3_Launch_Critical_Fix_Package.zip`
Expected: package exists; SHA256 printed.

- [x] **Step 4: Commit package inputs (not the zip binary) and push**

```bash
git add audit_launch_fix_v333/reports audit_launch_fix_v333/artifacts/LSU_120Run_Formal_Manifest_Schema.csv
git commit -m "[LSU][V3.3.3][LAUNCH-FIX] publish launch readiness and acceptance reports"
git push origin lsu-v3.3.1-context-workload-20261111
```

- [x] **Step 5: Final self-verification**

Run: `git status --short; git log --oneline -10; sha256sum LSU_v3.3.3_Launch_Critical_Fix_Package.zip`
Expected: clean tree (except the zip and pre-existing untracked run artifacts), 9 new commits, package SHA recorded in the readiness report.

---

## Self-Review

**Spec coverage:** Task A → Task 1 + Task 6; Task B → Task 5; Task C → Task 3 + Task 5 step 6 (qualified integration); Task D → Task 5 + Task 4 + Task 7; Task E → Task 8; deliverables → Task 9. Launch gate table → Tasks 5/7/9.

**No silent defaults:** the collector's step 3–6 explicitly forbid defaulting missing `InjectionCount`/`Oracle`/`TerminalState`; the control classifier returns `UNKNOWN`/`CONTROL_PROOF_INCOMPLETE` (already verified).

**Type consistency:** `classify_control_run` keys and `qualified_evidence` keys are taken from the frozen README and verified by direct probes (`QUALIFIED` for clean SP05, `TRACE_INCOMPLETE` for RP01, `CONTROL_PROOF_INCOMPLETE` for A01-R05).

**Known limits stated, not hidden:** A03/SP05/RP01 remain QUALIFIED/TRACE_INCOMPLETE where the run evidence lacks a causal field; the readiness report must carry that limitation verbatim.
