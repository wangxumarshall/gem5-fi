# LSU v3.3.1 — Context & Workload Finalization (Round Plan)

Date: 2026-11-11. Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
Branch: `lsu-v3.3.1-context-workload-20261111` (base `lsu-preformal-v3.3.0-20261111` @ `8f7a1354`).
Baseline binary: `build/ARM/gem5.opt` = `d3807fbef631354a41d9d6d8cf14c11020e396439f80bdd516225c6b5e37e2b2`.

Scope is the researcher's 2026-11-11 decision: **12 models × R01–R05 = 60 contexts only**.
This round is pre-formal context/workload correctness convergence; **no formal campaign**.

## Decision inputs (approved by researcher)

- **Decision A (approved):** R01–R05 = 10/30/50/70/90 % of the model-specific
  *eligible-event* stream inside the ROI, `k(p)=ceil(p*N)`, nearest-rank.
- **Decision B (pending approval):** compare original W3/W6 vs `sq_reload_v3212`
  for SQ01/SQ03/SP05; recommend only, never switch the formal workload.

## Hard constraints

- Do not change SampleRunIDs, authoritative seeds, fault semantics, or frozen verdicts.
- Do not overwrite or regrade historical pilots; never merge chains across binary SHAs.
- Do not launch a formal campaign. Count-only / census probes are permitted.
- At most 4 concurrent gem5 processes (hard cap), one probe per model in flight.
- Never `git add -A`; stage explicit paths. One commit per coherent unit.

## Tasks (one commit per completed unit)

### Phase 0 — provenance and scaffolding

- [x] T0.1 Record git state, binary SHA, resource gate, v3.3.0 package SHA in
  `audit_v3_3_1/report/PROVENANCE.md`.
- [x] T0.2 Write `audit_v3_3_1/report/ROUND_LOG.md` (append-only command/result log).

### Phase 1 — ROI boundaries (static, no gem5)

- [x] T1.1 For each of the 10 distinct workload ELFs (W1–W8b + `sq_reload_v3212`),
  extract `main`/helper symbol ranges, buffer symbols, and the designed event
  instructions from `objdump -d` and `readelf -sW`. → `audit_v3_3_1/roi/LSU_ROI_Boundaries.csv`.
- [x] T1.2 Record why each ROI excludes `_start`/libc: symbol evidence + the
  v3.3.0 Agent B injection-PC map (`0/4` main for W1, `0/5` W4/W5/W6, etc.).
- [x] T1.3 Flag workloads with no explicit phase marker; propose a lightweight
  marker scheme (no workload modification without approval).

### Phase 2 — per-model eligible-event census (gem5 probes)

- [x] T2.1 Build `tools/lsu_v331_census.py`: invokes `platform/run_pilot.py`
  once per requested ordinal with the model's own flags, then extracts
  `dyn_inst_seq`, `pc`, address/entry identity, and eligible totals from the
  model log. Census output only; no grading, oracle ignored.
- [x] T2.2 Coarse census per model (ordinal 1, 10, 50, 100, 200, 400, 800,
  1200, 1600, … until the workload ends), one probe at a time.
- [x] T2.3 Locate ROI entry/exit ordinals by PC/address membership in the
  designed workload range; binary-search the boundary.
- [x] T2.4 Compute N_ROI and `k(p)` for p = 0.1/0.3/0.5/0.7/0.9; run the 5
  percentile probes; record DynInstSeq/PC/entry/state.
  → `audit_v3_3_1/roi/census/*.json`, `audit_v3_3_1/roi/percentile/*.json`.

### Phase 3 — 60-context mapping and distinctness

- [x] T3.1 `LSU_60Context_ROI_Percentile_Mapping.csv` (60 rows; every field
  either observed or explicitly `n/a`/`INSUFFICIENT_EVENTS`).
- [x] T3.2 `LSU_60Context_Distinctness_Audit.csv` (instruction identity, type,
  data dependence, LQ/SQ state, address/data, forwarding, replay/squash,
  propagation condition).
- [x] T3.3 Report where N_ROI < 5 or events repeat; never substitute seeds/events.

### Phase 4 — workload comparison (approval input only)

- [x] T4.1 `SQ01_Workload_Comparison.md`, `SQ03_Workload_Comparison.md`,
  `SP05_Workload_Comparison.md`: W3/W6 vs `sq_reload_v3212`, answering the
  ten required questions with real evidence.
- [x] T4.2 `LSU_12Model_Workload_Readiness.csv`.
- [x] T4.3 No workload mapping change; recommendation awaits researcher approval.

### Phase 5 — causal re-audit and controls

- [x] T5.1 `LSU_60Context_Causal_Chain_Reaudit.csv`: injection → activation →
  first divergence → downstream → consumer → commit/squash/replay → oracle,
  keyed by binary SHA; list missing edges.
- [x] T5.2 `LSU_60Context_Control_Readiness.csv`: per-context control pairing,
  seed/ELF/ROI/config equality, and an actual `injected=0` artifact.
- [x] T5.3 Identify controls that must be redone; no regrade of history.

### Phase 6 — finalization

- [x] T6.1 `LSU_v3.3.1_Finalization_Report.md` answering the 11 questions;
  status ∈ {CONTEXT_WORKLOAD_READY, PARTIALLY_READY, NOT_READY}.
- [x] T6.2 `LSU_Researcher_Approval_Required.md`.
- [x] T6.3 Subagent independent audit reports (A–F).
- [x] T6.4 `LSU_v3.3.1_Context_Workload_Finalization_Package.zip` + SHA256,
  including git state, binary SHA, source diffs, raw census records.
- [x] T6.5 Regression: `pytest tests/ -q` and platform tests; quote real output.

## Outcome (2026-11-11)

Final status: `PARTIALLY_READY`, `12_MODEL_FORMAL_READY=NO`. 40/60 contexts
mapped (25 on formal workloads, 15 on the recommended SQ workload); 20/60
blocked by workload/observability gaps (FW02, MD04, RP01, LP01). No formal
campaign, no frozen-design change, no workbook edit.

## Verification rules

- Every claim cites a real path or a command actually run this round.
- Census probes are never graded; percentile selection uses eligibility only.
- Historical chains keep their BinarySHA256; no cross-binary stitching.
- Final status is evidence-based; `n/a` is never silently written as zero.
