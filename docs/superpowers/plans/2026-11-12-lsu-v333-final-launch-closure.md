# LSU v3.3.3 Final Launch Closure — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close every known formal-campaign launch defect in one pass so the only remaining step is the researcher's authorization to run the 120-task campaign.

**Architecture:** Keep the frozen simulation artifacts (binary `62e1b1be…`, config `8309da72…`, C++ sources, workloads, identities) untouched. Harden only the Python/shell launch toolchain: strict tri-state control evidence, campaign-scoped lock, attempt-isolated resume, canonical evidence selection, workload provenance, collector isolation, and an ordered shell pipeline.

**Tech Stack:** Python 3 (stdlib only), bash, pytest, gem5.opt (never invoked by tests).

**Spec:** This task brief (LSU v3.3.3 FINAL LAUNCH CLOSURE). Design baseline: `audit_v3_3_3/trace_closure/final_config/RUNBOOK_Final_Formal_Campaign.md`, `audit_launch_fix_v333/README_INTERFACES.md`, `audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md`.

## Global Constraints

- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` (HEAD verified `fadf928d`; re-verify before each commit).
- Campaign root: `runs/lsu/formal_v333_final_20261112`; Campaign ID: `LSU-V333-FINAL-20261112`.
- Frozen binary SHA256: `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd` (verified on `build/ARM/gem5.opt`).
- Frozen config SHA256: `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225` on `configs/se/lsu_proxy.py` (NOT `ooo_proxy.py`).
- C++ source diff `git diff e3293856..HEAD -- CHAOS/gem5/src` must stay empty. Never rebuild gem5. Never edit `CHAOS/gem5/src`, workloads, seeds, SampleRunIDs, ROI, or pairing.
- 12 models × 5 contexts × {fault, control} = 120 unique tasks; 60 unique SampleRunIDs; 60 unique seeds; each fault/control pair shares SampleRunID and Seed.
- Missing evidence must be fail-closed: never a silent `0`, never `PASS`.
- Tests never start gem5 and never write inside `runs/lsu/formal_v333_final_20261112` (use `tmp_path`).
- One commit per task; stage explicit paths only (repo discipline: never `git add -A`). Do not stage untracked audit/package artifacts.
- No `Co-Authored-By` trailer in commits.

## File Structure

| File | Responsibility | Owner |
|---|---|---|
| `tools/lsu_run_state.py` (new) | Attempt IDs, atomic attempt records, canonical selection, task state scan | A |
| `tools/lsu_campaign_lock.py` (new) | Campaign-scoped lock: metadata, non-blocking acquire, stale rules | A |
| `tools/lsu_v332_matrix.py` (modify) | Runner: lock wiring, attempts, resume, atomic index, dry-run validation | A |
| `tools/lsu_v333_control_proof.py` (modify) | Strict tri-state ControlInjected + control-audit CSV emitter | B |
| `tools/lsu_v333_launch.py` (modify) | Collector: canonical resolution, isolation, identity completeness | B |
| `tools/lsu_v333_provenance.py` (new) | Three workload fields, real SHA256, per-model table | C |
| `audit_v3_3_3/trace_closure/final_config/_generate.py` (modify) | Regenerate manifest template with provenance fields | C |
| `audit_v3_3_3/trace_closure/final_config/0{1,2,3,4}_*.sh` (modify) | Ordered pipeline with guards | D |
| `audit_v3_3_3/trace_closure/final_config/RUNBOOK_Final_Formal_Campaign.md` (modify) | Commands + recovery runbook | D |
| `tests/test_lsu_v333_lock_resume.py` (new) | Lock/attempt/resume unit tests | A |
| `tests/test_lsu_v333_control.py` (modify) | Tri-state tests | B |
| `tests/test_lsu_v333_manifest_isolation.py` (modify) | Canonical/isolation tests | B |
| `tests/test_lsu_v333_provenance.py` (new) | Provenance tests | C |
| `tests/test_lsu_v333_shell_pipeline.py` (new) | Shell syntax/order/guard tests | D |
| `tests/test_lsu_v333_final_launch_acceptance.py` (new) | Independent acceptance tests (no source edits) | E |
| `docs/superpowers/plans/2026-11-12-lsu-v333-final-launch-closure.md` | This plan | main |

### Frozen Interfaces (all agents must use these names)

```python
# tools/lsu_run_state.py
STATUS_PENDING = "PENDING"; STATUS_RUNNING = "RUNNING"; STATUS_COMPLETED = "COMPLETED"
STATUS_FAILED = "FAILED"; STATUS_TIMEOUT = "TIMEOUT"
STATUS_OUTPUT_INCOMPLETE = "OUTPUT_INCOMPLETE"; STATUS_HASH_MISMATCH = "HASH_MISMATCH"
STATUS_ORACLE_FAIL = "ORACLE_FAIL"
def task_tag(model: str, ctx: int, role: str) -> str            # f"{model}-R{ctx:02d}-{role}"
def attempts_root(run_dir: Path) -> Path                         # run_dir/"attempts"
def next_attempt_id(run_dir: Path) -> str                        # "attempt_001", ...
def attempt_dir(run_dir: Path, attempt_id: str) -> Path
def write_attempt_record(adir: Path, record: dict) -> None       # atomic: tmp + os.replace
def read_attempt_record(adir: Path) -> dict | None
def read_canonical(run_dir: Path) -> dict | None
def write_canonical(run_dir: Path, record: dict) -> None         # atomic; refuses overwrite
def canonical_dir(run_dir: Path) -> Path                         # attempt dir or legacy run_dir
def scan_task_state(run_dir: Path, campaign_id: str) -> dict     # {state, attempt_id, canonical, reason}

# tools/lsu_campaign_lock.py
class LockHeld(RuntimeError): ...
class StaleLockError(RuntimeError): ...
@contextmanager
def campaign_lock(out_base: Path, campaign_id: str) -> Iterator[dict]
    # non-blocking flock; JSON metadata {pid,hostname,started_at,campaign_id,out_base}
    # raises LockHeld when a live lock belongs to the same campaign on this host
    # raises LockHeld when a live lock belongs to a different campaign/host
    # reclaims a free lock whose recorded pid is dead on this host (writes .stale.json)

# tools/lsu_v333_control_proof.py
CONTROL_INJECTED_NO = "NO"; CONTROL_INJECTED_YES = "YES"
CONTROL_INJECTED_UNKNOWN = "UNKNOWN"; CONTROL_INJECTED_INVALID = "INVALID"
def classify_injection_count(value: object) -> tuple[str, str]   # (state, reason)
# CLI: --emit-control-audit --proof <csv> --out <csv>
```

---

### Task 1: Strict tri-state ControlInjected classifier

**Files:**
- Modify: `tools/lsu_v333_control_proof.py`
- Test: `tests/test_lsu_v333_control.py`

**Interfaces:**
- Produces: `classify_injection_count(value) -> (state, reason)`; states `NO|YES|UNKNOWN|INVALID`; CLI `--emit-control-audit`.

- [x] **Step 1: Write failing tests** for `classify_injection_count`: `0 → ("NO","ZERO")`; `"0" → NO`; `1/5 → YES`; `None`/missing → `("UNKNOWN","MISSING")`; `""`/`"  "` → `("UNKNOWN","EMPTY")`; `"abc"`/`"1.0"`/`"nan"` → `("UNKNOWN","UNPARSEABLE")`; `-1`/`"-3"` → `("INVALID","NEGATIVE")`. Also test that the emitted control-audit CSV never writes `NO` for missing/illegal counts and preserves `InjectionAttemptCount` and `InjectionAppliedCount` as separate columns.
- [x] **Step 2: Run tests, confirm failure** (`pytest tests/test_lsu_v333_control.py -k injection_count -v`).
- [x] **Step 3: Implement** strict parse: missing key/`None` before empty-string check; `str.strip()`; accept only `^[+-]?\d+$`; negative → INVALID; zero → NO; positive → YES. Add `--emit-control-audit` mode reading the proof CSV and writing `ModelID,ContextID,InjectionAttemptCount,InjectionAppliedCount,InjectionCount,ControlInjected,ControlInjectedReason,ControlZeroProof`.
- [x] **Step 4: Run tests, confirm pass.**
- [x] **Step 5: Commit** `[LSU][V3.3.3][LAUNCH] make ControlInjected strictly tri-state`.

### Task 2: Campaign-scoped lock with metadata and stale rules

**Files:**
- Create: `tools/lsu_campaign_lock.py`
- Modify: `tools/lsu_v332_matrix.py` (replace `matrix_lock`)
- Test: `tests/test_lsu_v333_lock_resume.py`

**Interfaces:**
- Produces: `campaign_lock(out_base, campaign_id)`; lock path `out_base/".lsu_v332_matrix.lock"` computed at call time (never a default argument).

- [x] **Step 1: Write failing tests**: acquire writes JSON with pid/hostname/started_at/campaign_id/out_base; second acquire in a child process exits nonzero with `LOCK_HELD` (same campaign); different campaign on same root refused; dead-PID lock is reclaimed and `.stale.json` written; lock path follows `--out-base` (not `runs/lsu/formal_v333`); `--force` does not bypass.
- [x] **Step 2: Run, confirm failure.**
- [x] **Step 3: Implement** `fcntl.flock(LOCK_EX|LOCK_NB)` on the campaign lock path. On `EAGAIN`, read metadata and raise `LockHeld` including campaign id/pid. When acquired, if existing metadata is a *different* campaign or foreign hostname and its pid is alive, raise `LockHeld`; if same host and pid dead, move old metadata to `.stale.json` and proceed. Always release/unlock in `finally` (covers exceptions and timeouts).
- [x] **Step 4: Wire runner** to `with campaign_lock(OUT_BASE, args.campaign_id):`; exit `3` on `LockHeld`. Delete the module-level `LOCK_FILE` default-argument usage.
- [x] **Step 5: Run tests + `pytest tests/test_lsu_v333_runner_errors.py -v`; commit** `[LSU][V3.3.3][LAUNCH] bind the matrix lock to campaign id and out-base`.

### Task 3: Attempt isolation, resume state machine, atomic index

**Files:**
- Create: `tools/lsu_run_state.py`
- Modify: `tools/lsu_v332_matrix.py`
- Test: `tests/test_lsu_v333_lock_resume.py`

**Interfaces:**
- Produces: all `lsu_run_state` symbols above. Runner gains `--resume`.

- [x] **Step 1: Write failing tests** over synthetic dirs: (a) fresh task → PENDING; (b) COMPLETED attempt with complete required outputs → COMPLETED and resume skips it; (c) FAILED/TIMEOUT/OUTPUT_INCOMPLETE → new `attempt_002` created, `attempt_001` bytes unchanged; (d) HASH_MISMATCH → resume refuses and exit nonzero; (e) ORACLE_FAIL canonical → resume does not retry/replace; (f) two COMPLETED attempts → canonical stays the first, both preserved; (g) atomic index: SIGKILL between summary write and record write leaves RUNNING/PENDING, never COMPLETED; (h) duplicate submission does not create a second dir.
- [x] **Step 2: Run, confirm failure.**
- [x] **Step 3: Implement** attempt records (`attempt.json`) written RUNNING before execution and COMPLETED only after: required outputs exist, SHA file hashes recorded, oracle parsed. Write canonical.json exactly once (atomic, `O_EXCL`). Parent run dir gets symlinks `summary.json`, `command.txt`, `pilot_meta.json`, `campaign.json`, `stats.txt`, logs → canonical attempt files (skip if target absent). Update `campaign_index.json` atomically after every task.
- [x] **Step 4: Implement `--resume`** scan: COMPLETED → skip; FAILED/TIMEOUT/OUTPUT_INCOMPLETE/PENDING → new attempt; HASH_MISMATCH → stop with nonzero; ORACLE_FAIL → skip (no replacement). Without `--resume`, refuse a non-empty campaign root.
- [x] **Step 5: Run tests + runner errors tests; commit** `[LSU][V3.3.3][LAUNCH] isolate attempts and make resume non-destructive`.

### Task 4: Dry-run 120-task validation

**Files:**
- Modify: `tools/lsu_v332_matrix.py`
- Test: `tests/test_lsu_v333_lock_resume.py`

**Interfaces:**
- Produces: `--dry-run` prints `DRY_RUN_SUMMARY` JSON and only prints `READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES` when all gates pass; exit 0/2.

- [x] **Step 1: Write failing tests**: 120 unique tasks, 60 SampleRunIDs, 60 seeds, pairing equality, 120 unique outdirs, identical binary/config SHA, per-model ELF SHA correct, zero existing outdir collisions; missing/empty campaign root is not created; no gem5 invocation (monkeypatch `subprocess.run` to raise).
- [x] **Step 2: Implement** dry-run validation computing real SHA256 of binary, config and each resolved workload; compare against frozen provenance; detect campaign-root collisions; validate `--campaign-id`.
- [x] **Step 3: Run tests; run the real dry-run** with the final args and capture output.
- [x] **Step 4: Commit** `[LSU][V3.3.3][LAUNCH] validate the full 120-task matrix in dry-run`.

### Task 5: Collector canonical resolution and isolation

**Files:**
- Modify: `tools/lsu_v333_launch.py`
- Test: `tests/test_lsu_v333_manifest_isolation.py`

**Interfaces:**
- Consumes: `lsu_run_state.canonical_dir/scan_task_state`.
- Produces: `EvidenceKind=FORMAL` only when path under `--runs`, `campaign_id` matches, identity (SampleRunID/Seed/Model/Context/Role) matches the design row, and canonical evidence is complete.

- [x] **Step 1: Write failing tests**: attempt-based run resolves to canonical; a non-canonical FAILED attempt is never FORMAL; run outside `--runs` → NON_FORMAL; missing summary/trace/oracle → not PASS; missing InjectionCount → control proof incomplete, never zero PASS; `QUALIFIED` never becomes `PASS`; historical pre-formal root → zero FORMAL.
- [x] **Step 2: Implement** canonical resolution via `canonical_dir(run_dir)`, campaign-root containment check with `Path.resolve()`, identity equality, and per-required-artifact checks.
- [x] **Step 3: Run tests; commit** `[LSU][V3.3.3][LAUNCH] resolve canonical attempts in the formal collector`.

### Task 6: Workload and binary provenance (three fields, real SHA)

**Files:**
- Create: `tools/lsu_v333_provenance.py`
- Modify: `audit_v3_3_3/trace_closure/final_config/_generate.py`
- Test: `tests/test_lsu_v333_provenance.py`

**Interfaces:**
- Produces: `provenance_table() -> list[dict]` with `ModelID, WorkloadSourcePath, FormalExecutionPath, ELF_SHA256, Exists, Readable, MatchesFrozen`; CLI prints failures and exits nonzero.

- [x] **Step 1: Write failing tests** for all 12 models: file exists, readable, real SHA matches the frozen table; `FormalExecutionPath` equals what `resolve_workload` returns; no path points at an old worktree (`v3.2`, `v3.2.10`, `archive`); duplicate basename with different content is flagged.
- [x] **Step 2: Implement** using `hashlib.sha256` on the actual files and the frozen table from `audit_launch_fix_v333/authorization/LSU_Final_Binary_Provenance.md`.
- [x] **Step 3: Update `_generate.py`** so the manifest template carries the three fields and `FormalExecutionPath` is the only execution path; regenerate the template and verify 120 rows.
- [x] **Step 4: Run tests; commit** `[LSU][V3.3.3][LAUNCH] freeze workload provenance with real ELF hashes`.

### Task 7: Ordered shell pipeline and recovery runbook

**Files:**
- Modify: `audit_v3_3_3/trace_closure/final_config/01_launch_campaign.sh`, `02_manifest_only.sh`, `03_full_collector.sh`, `04_final_reports.sh`, `launch_commands_final.sh`, `RUNBOOK_Final_Formal_Campaign.md`
- Test: `tests/test_lsu_v333_shell_pipeline.py`

**Interfaces:**
- Consumes: Task 1 CLI (`--emit-control-audit`), Task 5 collector, Task 3 `--resume`.
- Produces: 04 no longer contains inline `InjectionCount` logic; scripts declare ordered dependencies and refuse stale inputs.

- [x] **Step 1: Write failing tests**: `bash -n` every script; 04 contains no `in ("0", "")`; 04 invokes `--emit-control-audit`; each script pins Campaign ID/root/SHAs; 01 refuses non-empty root unless `--resume`; 02/03/04 write disjoint outputs and never into each other; 03 fails when any task is not complete; 04 fails when the control audit has `UNKNOWN`/`INVALID`.
- [x] **Step 2: Implement** the script changes and document the exact post-campaign command sequence plus recovery procedure in the RUNBOOK.
- [x] **Step 3: Run `bash -n` + tests; commit** `[LSU][V3.3.3][LAUNCH] order the campaign pipeline and fail closed`.

### Task 8: Independent acceptance test suite

**Files:**
- Create: `tests/test_lsu_v333_final_launch_acceptance.py` (Agent E; no edits to audited source)

- [x] **Step 1: Write acceptance tests** for every Gate in the brief: 12/12 models, 60/60 IDs/seeds/pairs, strict tri-state, frozen SHAs, lock independence, resume, manifest isolation, missing-evidence fail-closed, duplicate task rejection, output collision zero, full-collector fixture, final-report fixture, 120-task dry-run.
- [x] **Step 2: Run against the integrated tree; record real output.**
- [x] **Step 3: Commit** `[LSU][V3.3.3][LAUNCH] add independent launch acceptance tests`.

### Task 9: Full test matrix, real dry-run, package

**Files:**
- Create: `audit_launch_fix_v333/reports/LSU_Independent_Acceptance_Final.md`
- Create: `LSU_v3.3.3_FINAL_LAUNCH_READY_PACKAGE.zip`
- Modify: `audit_v3_3_3/trace_closure/final_config/SHA256SUMS.txt`

- [x] **Step 1:** Run `pytest tests/ -q`, `bash -n` on all scripts, and the 120-task dry-run; capture real logs under `audit_launch_fix_v333/reports/`.
- [x] **Step 2:** Recompute binary/config/ELF SHAs and the empty C++ diff; write the independent acceptance report with the real HEAD and real status.
- [x] **Step 3:** Build the package with config, modified sources, `git diff`, test logs, dry-run output, provenance, collector/reports commands, acceptance report and `SHA256SUMS`; verify extraction + checksum.
- [x] **Step 4: Commit** `[LSU][V3.3.3][LAUNCH] publish the final launch-ready package`.

## Review Focus

1. `InjectionCount` written as `0.0`, `" 0 "`, `"+0"` or `"0x0"` — must never become a zero-injection PASS; only canonical integer `0` is `NO`.
2. Legacy flat run dirs (pre-attempt pilots) consumed by the collector — must resolve without crashing and without becoming `FORMAL`.
3. Lock file with empty/partial/foreign metadata — must not block the new campaign and must not be deleted while a live process holds it.
4. A second COMPLETED attempt or an ORACLE_FAIL followed by a retry — canonical must not silently change; history must remain.
5. Two copies of the same ELF basename with different content — provenance must flag, not pick one.

---

## Execution Record (2026-11-13)

- All tasks 1-9 executed in one integrated pass.
- Full suite: `513 passed` (`audit_launch_fix_v333/reports/LSU_Test_Matrix_Final.log`).
- Real dry-run: 120 commands, `READY_TO_LAUNCH_FORMAL_CAMPAIGN=YES`, no campaign root created
  (`audit_launch_fix_v333/reports/LSU_120Run_Dryrun_Final.log`).
- Frozen binary `62e1b1be…`, config `8309da72…`, `git diff e3293856..HEAD -- CHAOS/gem5/src` empty.
- Independent verdict: **ACCEPT** (`audit_launch_fix_v333/reports/LSU_Independent_Acceptance_Final.md`).
