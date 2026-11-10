# LSU v3.2.12 — 12-Model Propagation Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Each task is one commit and one pushed unit.

**Goal:** Close the remaining eight LSU fault models to a real, traceable propagation chain (or an honest LIFECYCLE_ONLY/PARTIAL verdict), implement RP01, and produce the 12-model audit matrix, diagnostic-feature dataset and formal-experiment preflight package — without rerunning already-sufficient pilots or changing any seed/SampleRunID.

**Architecture:** Re-derive every verdict from raw per-pilot artifacts (`trace_v31.jsonl`, `pilot_meta.json`, `manifest.json`, `oracle.log`) with a new closure tool that reuses `tools/lsu_propagation_audit.audit_pilot`. Add read-only trace fields to existing injectors (`CHAOSAddrPath`, `CHAOSLSQFwd`, `CHAOSPropagation`) and one new workload; add RP01 as a new `StructMode` of the already-wired `CHAOSLSQFwd` SimObject. Each model's verdict is decided by the tool's deterministic rules, never hand-edited.

**Tech Stack:** Python 3.11 (pytest, csv/json), gem5 v25 (vendored at `CHAOS/gem5`), SCons 4.5.2, host `gcc -O2 -static` AArch64 workloads.

**Spec:** The frozen v3.2.12 brief (researcher message, 2026-11-10) plus the v3.2.11 audit inputs it builds on:
- `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/LSU_11Model_Propagation_Audit_Summary_v3.2.11.md`
- `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_11/SUPPLEMENTARY_PILOT_PLAN_v3.2.11.md`
- `docs/gem5-fi/lsu/implementation_v3_2/rp01_design_v3_2_11/RP01_Final_Design_Gate_v3.2.11.md`
- `docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv`

## Baseline (verified 2026-11-10, before this plan)

- Branch `lsu-platform-v3.2.11`, HEAD `c02976b27696edd83ff2719b6abf1937714ddbdb`, clean tree.
- Final binary `build/ARM/gem5.opt` SHA256 `3dccaa10ec5073ca90f2622bd37d5adac1b705bd9faf2497c2d13e46beadd4ed`.
- Latest workbook: `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.6.xlsx`.
- New worktree already created: `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`, branch `lsu-platform-v3.2.12`, at `c02976b2`.
- Disk at plan time: 74.94 GiB free on `/home` (78% used). Historical safety threshold: **70.6 GiB free**.
- SCons object tree to seed an incremental build: `lsu-platform-v3.2.11/CHAOS/gem5/build` (6.9 GB, includes a 1.1 GB `gem5.opt`).

## Global Constraints

- Base is v3.2.11 `c02976b2`; never rebase onto `main`, never `git reset --hard`, never `git clean -fd`.
- Never delete or overwrite a historical trace, pilot directory, ZIP, or report; new outputs go to new `*_v3_2_12` namespaces.
- Never modify a frozen SampleRunID or Seed. Supplementary runs use `SUPP-<MODEL>-<Rxx>` pilot IDs with a sidecar recording `supplementary_of` (original SampleRunID) and the original seed.
- Never change an Oracle or a golden value to obtain PASS. A wrong application result is recorded as FAIL/SDC.
- Every run records its own `BinarySHA256` and `WorkloadSHA256`. Traces from two binaries are never merged into one verdict.
- Disk gate: **no Pilot may start while `/home` free space < 70.6 GiB**. Static analysis and document work may continue below the threshold.
- Build: `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` for the first build in this worktree; `-j126` for incremental rebuilds. After a successful link, copy `CHAOS/gem5/build/ARM/gem5.opt` to the repo-root `build/ARM/gem5.opt` and record both SHAs.
- Every commit message: `[LSU][MDSPEC][V3.2.12][<AREA>] <imperative sentence>`. No `Co-Authored-By` trailer. Stage explicit paths only; never `git add -A`.
- Per-task verification is mandatory and quoted from real command output: build clean, functional smoke on the affected behavior, one unaffected regression, then commit and push to `lsu-platform-v3.2.12`.
- Verdicts are computed by `tools/lsu_12model_closure.py`; a status matrix or Excel cell may never be hand-set to PASS. `ConfigFrozen` stays `NO`; formal `ExecutionStatus` stays `NOT_STARTED`.

## Review Focus

1. **Mixed-binary evidence** — a pilot from the v3.2.11 binary silently merged with a v3.2.12-binary pilot would look like one chain. The tool must split by `BinarySHA256`; test in Task 3.
2. **Zero-injection pilots counted as chains** — `InjectionVerified=no` or `ActivationVerified=no` must force `PARTIAL`/`UNRESOLVED`, never `COMPLETE_CAUSAL_CHAIN`; test in Task 3.
3. **Time adjacency treated as causality** — an event at a later tick that shares neither `ptag` nor `dyn_inst_seq` with the injection must not create a propagation edge; test in Task 3.
4. **HANG/TIMEOUT relabeled MASKED** — `terminal_rules.adjudicate` hard terminals must win over a passing oracle; regression test in Task 3 and Task 15.
5. **A new workload changes a golden without a frozen SHA** — `sq_reload_v3212` must be built deterministically, double-run on host, and frozen with SHA before any pilot; test in Task 10.

---

### Task 1: Worktree baseline freeze and build bootstrap

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/GIT_BASELINE_v3212.txt`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v3212.txt`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_12/baseline_inventory.txt`
- Copy: `CHAOS/gem5/build/` and `build/` from the v3.2.11 worktree

**Interfaces:**
- Produces: the v3.2.12 worktree's first binary SHA, workload SHA inventory, and disk-gate record consumed by every later task.

- [x] **Step 1: Confirm the worktree and record git identity**

Run:
```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12
git branch --show-current && git rev-parse HEAD && git status --porcelain
```
Expected: `lsu-platform-v3.2.12`, `c02976b27696edd83ff2719b6abf1937714ddbdb`, empty status.

- [x] **Step 2: Write the baseline files**

Record in `GIT_BASELINE_v3212.txt`: branch, full 40-char HEAD, parent baseline `c02976b2`, date, host, and `git worktree list` entry. Record in `baseline_inventory.txt`: `df -h /home`, `sha256sum build/ARM/gem5.opt`, `sha256sum` of the v3.2.6 workbook and `MODEL_STATUS_MATRIX.csv`, and the SHA256 of every file in `docs/gem5-fi/lsu/implementation_v3_2/workloads/` that has a `.golden`.

- [x] **Step 3: Bootstrap the build tree**

```bash
cp -a /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.11/CHAOS/gem5/build ./CHAOS/gem5/
cp -a /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.11/build ./build
df -h /home | tail -1
```
Expected: ~68 GiB free (below the pilot gate; no pilot runs in this task).

- [x] **Step 4: Force configure and build the unchanged baseline**

```bash
cd CHAOS/gem5
scons -j16 --config=force build/ARM/gem5.opt 2>&1 | tee ../../docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_12/build_baseline_v3212.log | tail -5
```
If SCons skips the final link because the copied `sconsign.dblite` vouches for the stale binary, remove `build/ARM/gem5.opt` and rerun. Expected tail: `[ LINK] -> ARM/gem5.opt` and `scons: done building targets.`; no new warnings.

- [x] **Step 5: Publish the binary to the repo-root path and record SHA**

```bash
cp CHAOS/gem5/build/ARM/gem5.opt ../../build/ARM/gem5.opt   # run from repo root: cp CHAOS/gem5/build/ARM/gem5.opt build/ARM/gem5.opt
sha256sum CHAOS/gem5/build/ARM/gem5.opt build/ARM/gem5.opt
```
Expected: two identical SHAs. Append them to `GIT_COMMIT_v3212.txt`.

- [x] **Step 6: Regression on the unaffected canonical workload**

```bash
build/ARM/gem5.opt --outdir=/tmp/v3212_reg configs/se/arm_chaos.py --cmd workloads/directed/reg_chain --cpu O3 2>&1 | tail -3
```
Expected: golden checksum `f247ef3fe6f02cfd`, exit 0, no SIGSEGV.

- [x] **Step 7: Commit only the baseline records**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/GIT_BASELINE_v3212.txt docs/gem5-fi/lsu/implementation_v3_2/GIT_COMMIT_v3212.txt docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_12/build_baseline_v3212.log docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_12/baseline_inventory.txt docs/superpowers/plans/2026-11-10-lsu-v3-2-12-propagation-closure.md
git commit -m "[LSU][MDSPEC][V3.2.12][BASELINE] freeze the v3.2.11 baseline and publish the closure plan"
git push origin lsu-platform-v3.2.12
```

### Task 2: Unified acceptance standard and pilot-record schema

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_Propagation_Acceptance_Standard_v3.2.12.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/pilot_record.schema.md`

**Interfaces:**
- Produces: the eight per-pilot fields and five final classifications that Task 3's tool must emit; later tasks cite this document instead of redefining verdicts.

- [ ] **Step 1: Write the standard**

The document must state, verbatim as enumerations:
- `RecordIntegrity ∈ {VALID, INVALID, TRUNCATED}`
- `TraceCompleteness ∈ {COMPLETE, INCOMPLETE, MISSING}`
- `StructuralChainCompleteness ∈ {COMPLETE, PARTIAL, NONE}`
- `FaultEffectPropagationCoverage ∈ {COMPLETE, LIFECYCLE_ONLY, NONE, NOT_APPLICABLE}`
- `FaultCausality ∈ {PROVEN, PARTIAL, UNPROVEN}`
- `ObservedTerminal ∈ {SDC, MASKED, SQUASHED, CRASH, HANG, TIMEOUT, NO_INJECTION, INCOMPLETE, UNRESOLVED}`
- `ApplicationOracle ∈ {PASS, FAIL, MISSING, NOT_APPLICABLE}`
- `FinalClassification ∈ {COMPLETE_CAUSAL_CHAIN, VERIFIED_SINGLE_CONTEXT, LIFECYCLE_ONLY, PARTIAL, UNRESOLVED}`

State the five identity rules for a causal edge: `ptag`; `dyn_inst_seq`; `(lq_entry_id, generation)`; `(sq_entry_id, generation)`; `(execution_attempt_id, replay_generation)`. State the data rule: a consumer edge requires the consumer's input hash to equal the producer's writeback hash. State the single-context rule: one complete chain → `VERIFIED_SINGLE_CONTEXT`, not `COMPLETE_CAUSAL_CHAIN`. State the terminal rule: `HANG`/`TIMEOUT`/`SQUASHED` are valid terminals; a missing injection is never a terminal.

- [ ] **Step 2: Write the schema table**

One row per field: name, allowed values, source artifact, required evidence, and the rule that maps it to the final classification.

- [ ] **Step 3: Verify the document's enums against the existing platform**

```bash
grep -n "HARD_TERMINALS" docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py
grep -n "LIFECYCLE_ONLY\|PARTIAL\|COMPLETE" docs/gem5-fi/lsu/implementation_v3_2/platform/fault_effect_coverage.py | head
```
Expected: the enums in the new document are a superset that does not contradict either module.

- [ ] **Step 4: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/LSU_Propagation_Acceptance_Standard_v3.2.12.md docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/pilot_record.schema.md
git commit -m "[LSU][MDSPEC][V3.2.12][AUDIT] freeze the unified 12-model acceptance standard"
git push origin lsu-platform-v3.2.12
```

### Task 3: Closure tool — per-pilot record, missing-evidence matrix, closure matrix, feature dataset

**Files:**
- Create: `tools/lsu_12model_closure.py`
- Create: `tests/test_lsu_12model_closure.py`
- Modify: `tools/lsu_propagation_audit.py` only if a reusable extraction helper must be exported; do not fork its classifier.

**Interfaces:**
- Consumes: `tools.lsu_propagation_audit.audit_pilot(pilot_dir: Path, model: str, binary_sha: str | None = None) -> dict` with keys `identity, stages, evidence, terminal, oracle, missing, classification`.
- Produces:
  - `build_pilot_record(pilot_dir: Path, model: str, supplementary_of: str | None = None) -> dict` — the eight fields plus `ModelID, PilotID, SampleRunID, Seed, EventOrdinal, BinarySHA256, WorkloadSHA256, EvidencePath, MissingEvidence`.
  - `final_classification(record: dict) -> str` — deterministic mapping.
  - `write_missing_matrix(records: list[dict], out: Path) -> None` — columns `ModelID, PilotID, MissingStage, MissingEvent, MissingCausalEdge, RootCause, RequiredHook, RequiredWorkloadChange, RequiredRunCount, ExpectedEvidence`.
  - `write_closure_matrix(records: list[dict], out: Path) -> None` — all 24 brief-mandated columns.
  - `write_feature_dataset(records: list[dict], out: Path) -> None` — the five feature groups, one row per pilot or path fragment.

- [ ] **Step 1: Write failing tests**

Tests must use synthetic pilot directories under `tmp_path`:
```python
def test_zero_injection_is_never_complete(tmp_path): ...          # InjectionVerified=no -> PARTIAL
def test_time_adjacent_off_chain_event_is_not_an_edge(tmp_path): ...  # different ptag+seq -> no edge
def test_hang_beats_passing_oracle(tmp_path): ...                 # HANG + oracle PASS -> HANG
def test_mixed_binary_splits_verdicts(tmp_path): ...              # two SHAs -> two rows
def test_missing_matrix_has_no_blank_cell(tmp_path): ...          # every missing stage has root cause + run count
def test_feature_dataset_keeps_event_order(tmp_path): ...         # event_ordinal monotonic per pilot
```
Run `pytest tests/test_lsu_12model_closure.py -v`; expected FAIL (module absent).

- [ ] **Step 2: Implement the record builder**

Reuse `audit_pilot`; do not re-parse traces independently. Map `stages` to the three completeness fields and `classification` to `FaultEffectPropagationCoverage`, then apply `final_classification` in this fixed order: missing injection → `UNRESOLVED`; `HANG/TIMEOUT/SQUASHED` with a proven trigger → `COMPLETE_CAUSAL_CHAIN` (or `VERIFIED_SINGLE_CONTEXT` if only one context in the model); complete effect with consumer → `COMPLETE_CAUSAL_CHAIN`; internal-only change → `LIFECYCLE_ONLY`; otherwise `PARTIAL`.

- [ ] **Step 3: Implement the three writers**

Every CSV cell is a value or the literal `NULL`/`NOT_APPLICABLE`; the writer raises on an empty string, a bare `PASS`, or a row whose `FinalClassification` is `COMPLETE_CAUSAL_CHAIN` while `InjectionVerified` is `no`.

- [ ] **Step 4: Run the tests**

`pytest tests/test_lsu_12model_closure.py -v` → all PASS.

- [ ] **Step 5: Regression**

`pytest tests/test_lsu_propagation_audit.py -v` → all PASS (the shared extractor is unchanged).

- [ ] **Step 6: Commit**

```bash
git add tools/lsu_12model_closure.py tests/test_lsu_12model_closure.py
git commit -m "[LSU][MDSPEC][V3.2.12][TOOLS] add the deterministic 12-model closure tool"
git push origin lsu-platform-v3.2.12
```

### Task 4: LQ04 re-adjudication — the packet-senderState masking path

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LQ04_Propagation_Audit_v3.2.12.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LQ04_verdict_v3.2.12.json`
- Read-only inputs: `pilots_v3_2_10/LQ04-R01..R05`, `LQ04-CONTROL-R01..R05`

**Interfaces:**
- Produces: `FinalClassification` for LQ04, either `COMPLETE_CAUSAL_CHAIN` with `TerminalState=MASKED` and `MaskingMechanism=RESPONSE_ASSOCIATED_VIA_PACKET_SENDERSTATE`, or `LIFECYCLE_ONLY` with the missing link named.

- [ ] **Step 1: Prove the source mechanism**

Quote with `file:line` from `CHAOS/gem5/src/cpu/lsq.cc`, `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`, and the response path that the packet's `senderState` (not `LQEntry::_request`) resolves the response to the original request after `_request=nullptr`. Record the exact functions.

- [ ] **Step 2: Prove the runtime facts from the existing traces**

From each LQ04 pilot, extract: LQ entry invalid after `executeLoad`; the response's request identity; the writeback data; the first consumer input hash; the entry free tick/generation; the final checksum. Cite event ids and ticks.

- [ ] **Step 3: Adjudicate**

Run:
```bash
python3 tools/lsu_12model_closure.py record --model LQ04 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R01 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R02 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R03 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R04 \
  --pilot-dir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10/LQ04-R05 \
  --json docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LQ04_verdict_v3.2.12.json
```
Expected: five records. If the LQ-invalid event or the senderState association is absent from the trace, write `SUPPLEMENTARY_PILOT_REQUIRED` in the verdict and add exactly one supplementary run in Task 6 with a new pilot ID; do not upgrade on inference alone.

- [ ] **Step 4: Write the audit report**

Report the five per-pilot records, the source quotes, and the verdict. If the chain is proven, state the masking mechanism explicitly; otherwise state `LIFECYCLE_ONLY` and the missing runtime link.

- [ ] **Step 5: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LQ04_Propagation_Audit_v3.2.12.md docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LQ04_verdict_v3.2.12.json
git commit -m "[LSU][MDSPEC][V3.2.12][LQ04] re-adjudicate the senderState masking chain"
git push origin lsu-platform-v3.2.12
```

### Task 5: Raw-Oracle supplementary runs for the 14 verified chain pilots

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-DA04-R04/`, `SUPP-DA04-R05/`
- Create: `.../SUPP-LP01-R01..R05/`
- Create: `.../SUPP-MD04-R02/`, `SUPP-MD04-R03/`, `SUPP-MD04-R05/`
- Create: `.../SUPP-FW05-R02..R05/`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/SUPPLEMENTARY_ORACLE_MANIFEST_v3.2.12.csv`

**Interfaces:**
- Consumes: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py` (`--model`, `--context-index`, `--pilot-id`, `--outdir`, `--gem5`).
- Produces: per-pilot `oracle.log` + `stdout.log` + `pilot_meta.json` under new SUPP directories, and a manifest mapping `SUPP-*` → original `SampleRunID`/`Seed`.

- [ ] **Step 1: Run the 14 pilots with preserved context seeds**

For each `(model, context, original_pilot)` run:
```bash
python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py \
  --model LP01 --context-index 1 --pilot-id SUPP-LP01-R01 \
  --outdir docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-LP01-R01 \
  --gem5 build/ARM/gem5.opt
```
Same pattern for DA04 contexts 4,5; LP01 1–5; MD04 2,3,5; FW05 2–5. Expected each: exit 0, injection ≥1, `oracle.log` present, checksum equals the golden value recorded in the original pilot's meta.

- [ ] **Step 2: Write the supplementary manifest**

Columns: `SuppPilotID, ModelID, OriginalPilot, OriginalSampleRunID, Seed, EventOrdinal, BinarySHA256, WorkloadSHA256, OraclePath, GoldenChecksum, ActualChecksum, OracleResult`.

- [ ] **Step 3: Verify raw oracle presence and values**

```bash
for d in docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-*; do
  test -s "$d/oracle.log" || echo "MISSING $d"; done
grep -h "checksum" docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-LP01-R01/{stdout.log,oracle.log}
```
Expected: no `MISSING`; DA04/FW05 show FAIL checksums, LP01/MD04 show PASS, matching the frozen terminals.

- [ ] **Step 4: Confirm no historical directory was touched**

```bash
git status --porcelain docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6
```
Expected: empty.

- [ ] **Step 5: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-DA04-R04 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-DA04-R05 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-LP01-R01 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-LP01-R02 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-LP01-R03 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-LP01-R04 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-LP01-R05 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-MD04-R02 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-MD04-R03 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-MD04-R05 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-FW05-R02 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-FW05-R03 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-FW05-R04 docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/SUPP-FW05-R05 docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/SUPPLEMENTARY_ORACLE_MANIFEST_v3.2.12.csv
git commit -m "[LSU][MDSPEC][V3.2.12][ORACLE] archive raw oracle evidence for the 14 verified chains"
git push origin lsu-platform-v3.2.12
```

### Task 6: MissingEvidenceMatrix for all 12 models

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/MissingEvidenceMatrix.csv`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/MissingEvidenceMatrix_v3.2.12.md`

**Interfaces:**
- Consumes: `build_pilot_record` over all 55 historical pilots, the 14 SUPP pilots, and the LQ04 verdict.
- Produces: one row per missing item with the ten brief-mandated columns.

- [ ] **Step 1: Generate**

```bash
python3 tools/lsu_12model_closure.py missing \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_1 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_2 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_3 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_4 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_5 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_6 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_7 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_8 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_9 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_10 \
  --pilots-root docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12 \
  --out docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/MissingEvidenceMatrix.csv
```

- [ ] **Step 2: Audit the output**

Check: every row has a `RootCause`; every `RequiredRunCount` is an integer ≥0; no `MissingStage` is blank; A01/A03/FW02/SQ01/SQ03/SP05 have at least one row; DA04/LP01/MD04/FW05 have zero `ORACLE_FILE_MISSING` rows after Task 5.

- [ ] **Step 3: Write the narrative report and commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/MissingEvidenceMatrix.csv docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/MissingEvidenceMatrix_v3.2.12.md
git commit -m "[LSU][MDSPEC][V3.2.12][AUDIT] derive the per-model missing-evidence matrix"
git push origin lsu-platform-v3.2.12
```

### Task 7: A01 — golden/actual EA reference and crash attribution

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh`, `CHAOSAddrPath.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` only for the read-only trace call
- Test: `tests/test_addrpath_a01_coords.cc` (new host unit test)
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/A01_Propagation_Audit_v3.2.12.md`
- Create: `pilots_v3_2_12/SUPP-A01-R01..R05` and matched controls

**Interfaces:**
- Produces trace events `a01_ea` with `{fault_id, dyn_inst_seq, pc, golden_ea, actual_ea, xor_delta, bit, access_size}` and `a01_consumed` with `{dyn_inst_seq, consumer_seq, consumer_kind, input_hash}`; plus the corrupted request VA and the raised fault VA in the same record.
- Consumes: `CHAOSAddrPath::sendFragment`-side hook; `CHAOSPropagation` consumer events.

- [ ] **Step 1: Source audit, quoted**

Read `CHAOSAddrPath.cc` around the `sendFragment`/`pushRequest` hook and record the exact function and the three coordinate points where `golden_ea`, `actual_ea`, and the downstream request origin can be observed. Do not add a value read at the wrong layer.

- [ ] **Step 2: Write the failing host test**

Assert the coordinate rule: for a bit-3 flip, `actual_ea == golden_ea ^ (1<<3)`, `bit == 3`, and `xor_delta != 0`; for a masked (no-op) event, `xor_delta == 0` and `affected=0`.

- [ ] **Step 3: Implement the trace fields**

Emit `a01_ea` at EA formation and `a01_consumed` at the first consumer. Record the fault VA only when a fault is raised while the corrupted request is in flight; otherwise emit `fault_va=NOT_APPLICABLE`. No data-path change.

- [ ] **Step 4: Build and unit-test**

```bash
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt 2>&1 | tee ../../docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_12/build_a01.log | tail -3
g++ -O2 -std=c++17 tests/test_addrpath_a01_coords.cc -o /tmp/test_a01 && /tmp/test_a01
```
Expected: link line, no new warnings, test prints `A01_COORDS_OK`.

- [ ] **Step 5: Run 5 fault pilots + 2 matched controls**

Use `run_pilot.py --model A01 --context-index N --pilot-id SUPP-A01-RNN`. Baseline numeric comparison uses the control run at the same context: the control's response value at the golden EA is the reference; compare it with the fault run's response value at the actual EA for the same `dyn_inst_seq`. Expected: at least two contexts with a non-zero `DataDelta` and a consumer edge; crash contexts carry a `fault_va` that either equals the actual EA or is shown to be derived from the corrupted value's consumer.

- [ ] **Step 6: Audit, classify, commit**

Run `tools/lsu_12model_closure.py record --model A01 ...`. If only one context forms a full chain, record `VERIFIED_SINGLE_CONTEXT`; do not upgrade. Commit the source change and the pilot/audit evidence as two separate commits:
```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc CHAOS/gem5/src/cpu/o3/lsq_unit.cc tests/test_addrpath_a01_coords.cc
git commit -m "[LSU][MDSPEC][V3.2.12][A01] trace golden/actual EA coordinates and fault VA"
git push origin lsu-platform-v3.2.12
```

### Task 8: A03 — F5 persistent stuck-at eligibility stream

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{hh,cc}`
- Test: `tests/test_addrpath_a03_stream.cc`
- Create: `audit_v3_2_12/A03_Propagation_Audit_v3.2.12.md`, `pilots_v3_2_12/SUPP-A03-R01..R05` + controls

**Interfaces:**
- Produces `a03_stream` events: `{event_ordinal, dyn_inst_seq, pc, eligible, affected, golden_ea, actual_ea, bit, reason}` for every eligible load after activation; `a03_activation` with the start tick.
- Consumes: the same hook as Task 7; A03's F5 persistent semantics are unchanged.

- [ ] **Step 1: Source audit the F5 activation rule**

Quote the activation-time selection and the "applied on every event" branch. Confirm the five contexts R01–R05 are five activation start positions, not five independent single injections.

- [ ] **Step 2: Write the failing test**

Assert that after activation every eligible load is recorded exactly once, that `affected=1` iff the bit changes, and that an already-stuck address yields `affected=0, reason=ALREADY_STUCK` (this is the masking path, not a missing event).

- [ ] **Step 3: Implement, build, unit-test**

Same build command as Task 7; expected `A03_STREAM_OK`.

- [ ] **Step 4: Run 5 fault pilots + 2 controls**

Expected: a continuous eligible stream after activation; at least two contexts reach response + writeback + consumer; crash contexts carry an attributable VA. If 5/6 pilots lack writeback/consumer even with the stream, record `PARTIAL` and state the missing stage.

- [ ] **Step 5: Audit and commit** (source commit then evidence commit, as in Task 7)

### Task 9: FW02 — forwarding-decision chain and squash causality

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.{hh,cc}` (FW02 decision record)
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.{hh,cc}` (squash reason)
- Test: `tests/test_fw02_decision.cc`
- Create: `audit_v3_2_12/FW02_Propagation_Audit_v3.2.12.md`, `pilots_v3_2_12/SUPP-FW02-R01..R05` + controls

**Interfaces:**
- Produces `fw02_decision` `{load_seq, store_seq, normal_decision, fault_decision, memory_path, replay_count}` and `squash_reason` `{dyn_inst_seq, reason, triggering_seq}`.
- Consumes: existing forwarding decision hook; the memory-path response.

- [ ] **Step 1: Define the data comparison**

Record the forwardable store data hash and the memory response data hash in the same pilot. The chain is complete when the load's writeback hash equals the memory response hash and the consumer input hash equals it. A correct-data outcome is `MASKED` only with this evidence.

- [ ] **Step 2: Add the events (read-only), build, unit-test**

Expected: `FW02_DECISION_OK`; no new warnings.

- [ ] **Step 3: Re-run R01/R05 plus 3 more contexts**

Expected: at least two contexts with `decision=suppressed, memory_path=1, consumer edge`; any squash has a recorded `squash_reason` and, if fault-caused, is classified `SQUASHED` rather than `PARTIAL`.

- [ ] **Step 4: Audit and commit** (source then evidence)

### Task 10: `sq_reload_v3212` — minimal same-address reload workload (shared by SQ01/SQ03/SP05)

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212.c`
- Create: `compile_sq_reload_v3212.sh`, `sq_reload_v3212` (binary), `.golden`, `.host.out`
- Modify: `workloads/SHA256SUMS.txt`, `workloads/WORKLOADS.md`

**Interfaces:**
- Produces: a deterministic AArch64 static binary whose store is followed by a `dmb ish` and a same-address load consumed in a checksum and a dependent branch; golden checksum frozen by double-run.

- [ ] **Step 1: Write the workload**

Structure: `volatile uint64_t buf[256]`; for each of 128 iterations: store a distinct value, `asm volatile("dmb ish" ::: "memory")`, load the same address, accumulate `fnv1a` and a dependent `path` branch on equality; print `checksum=0x%016llx`. The `dmb` forces the store to drain before the load, giving SQ01/SQ03/SP05 a real memory-visibility consumer; the dependent branch gives control-path evidence.

- [ ] **Step 2: Build and double-run on the host**

```bash
gcc -O2 -static -o docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212 docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212.c
docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212 | tee .host.out
docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212
sha256sum docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212
```
Expected: both runs print the same checksum; write it to `.golden`; record the binary SHA in `SHA256SUMS.txt`.

- [ ] **Step 3: Fault-free gem5 baseline on the v3.2.12 binary**

```bash
build/ARM/gem5.opt --outdir=/tmp/sq_reload_bl configs/se/lsu_proxy.py --cpu O3 \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212 2>&1 | tail -3
```
Expected: the same checksum, exit 0.

- [ ] **Step 4: Check the workload actually exposes a same-address load after drain**

Run a `--chaos_propagation` trace (no fault) and confirm each store has a later load of the same address, not a pure forward from the SQ. Quote the trace lines.

- [ ] **Step 5: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212.c docs/gem5-fi/lsu/implementation_v3_2/workloads/compile_sq_reload_v3212.sh docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212 docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212.golden docs/gem5-fi/lsu/implementation_v3_2/workloads/sq_reload_v3212.host.out docs/gem5-fi/lsu/implementation_v3_2/workloads/SHA256SUMS.txt docs/gem5-fi/lsu/implementation_v3_2/workloads/WORKLOADS.md
git commit -m "[LSU][MDSPEC][V3.2.12][WORKLOAD] add the same-address reload workload for store-side models"
git push origin lsu-platform-v3.2.12
```

### Task 11: SQ01 — store-data chain to the reload consumer

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.{hh,cc}` (store drain + consumer trace)
- Test: `tests/test_sq01_chain.cc`
- Create: `audit_v3_2_12/SQ01_Propagation_Audit_v3.2.12.md`, `pilots_v3_2_12/SUPP-SQ01-R01..R05`

**Interfaces:**
- Produces `sq01_chain` `{store_seq, sq_idx, gen, data_before, data_after, mem_write_hash, reload_seq, reload_data_hash, consumer_hash}`.
- Consumes: the frozen SQ01 fault definition; the new workload via `run_pilot.py --workload .../sq_reload_v3212`.

- [ ] **Step 1: Write the failing test** — assert `data_after != data_before`, `mem_write_hash == hash(data_after)`, `reload_data_hash == mem_write_hash`, `consumer_hash == reload_data_hash` for a complete chain; assert `STORE_COMMITTED_LANE_NOT_READ` when no reload exists.

- [ ] **Step 2: Implement trace additions, build, unit-test** — expected `SQ01_CHAIN_OK`.

- [ ] **Step 3: Run 5 pilots on the new workload** with preserved context seeds; record the new WorkloadSHA256. Expected: at least two contexts with a full store→drain→reload→consumer chain; terminals SDC or MASKED depending on the checksum.

- [ ] **Step 4: Audit and commit** (source then evidence). Do not modify the SQ01 fault definition to manufacture a different error.

### Task 12: SQ03 — state-fault downstream effect

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/{CHAOSLSQFwd.hh,CHAOSLSQFwd.cc,sq03_rules.hh}` only for trace
- Test: `tests/test_sq03_effect.cc`
- Create: `audit_v3_2_12/SQ03_Propagation_Audit_v3.2.12.md`, `pilots_v3_2_12/SUPP-SQ03-R01..R05`

**Interfaces:**
- Produces `sq03_effect` `{sq_idx, gen, canwb_before, canwb_after, writeback_tick, drain_tick, reload_seq, reload_data_hash, resource_reuse_tick}`.

- [ ] **Step 1: Source-audit what early `_canWB` changes** — quote the writeback/drain scheduling path and the resource-release path. State explicitly which downstream events are possible and which are not.

- [ ] **Step 2: Write the failing test** — assert that a state change with no downstream difference yields `LIFECYCLE_ONLY` with `reason=NO_DOWNSTREAM_EFFECT`, and a state change that moves the drain/visibility yields a chain.

- [ ] **Step 3: Implement, build, unit-test** — expected `SQ03_EFFECT_OK`.

- [ ] **Step 4: Run 5 pilots on `sq_reload_v3212`** — expected: either a real drain/visibility difference with a reload consumer, or an honest `LIFECYCLE_ONLY` with the source-proved reason. Never record a field change alone as propagation.

- [ ] **Step 5: Audit and commit** (source then evidence)

### Task 13: SP05 — store pipeline stage vs memory visibility

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/{CHAOSLSQFwd.hh,CHAOSLSQFwd.cc,sp05_rules.hh}` for trace only
- Test: `tests/test_sp05_stage.cc`
- Create: `audit_v3_2_12/SP05_Propagation_Audit_v3.2.12.md`, `pilots_v3_2_12/SUPP-SP05-R01..R05`

**Interfaces:**
- Produces `sp05_stage` `{store_seq, completion_tick, commit_tick, writeback_tick, drain_tick, reload_seq, reload_data_hash, data_correct}`.

- [ ] **Step 1: Separate the three stages** — execution complete, commit, and data visible to a later access. Define the expected observation for each.

- [ ] **Step 2: Write the failing test** — a premature completion with correct data must classify `MASKED` with `MaskingMechanism=DATA_WRITTEN_CORRECTLY`; a visibility change with a reload consumer must produce a data chain.

- [ ] **Step 3: Implement, build, unit-test** — expected `SP05_STAGE_OK`.

- [ ] **Step 4: Run 5 pilots on `sq_reload_v3212`; audit and commit** (source then evidence). Commit ≠ visibility; record both ticks.

### Task 14: RP01 count-only preflight on the five frozen seeds

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/{CHAOSLSQFwd.hh,CHAOSLSQFwd.cc}`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` (read-only call site)
- Modify: `configs/se/lsu_proxy.py` (flags)
- Test: `tests/test_rp01_selector.cc`
- Create: `audit_v3_2_12/RP01_CountOnly_Preflight_v3.2.12.csv`

**Interfaces:**
- Produces `bool CHAOSLSQFwd::maybeSkipPartialReplay(uint64_t load_seq, uint64_t lq_idx, uint64_t lq_gen, uint64_t store_seq, uint64_t replay_gen)`; in count-only mode it records `rp01_eligible` and returns `false`.
- Produces config flags `--lsq_struct_mode rp01_count_only` (count-only) and `rp01_skip_replay` (fault), plus `--rp01_event_ordinal`, `--rp01_watchdog_cycles`.
- Consumes: `LSQUnit::read()` `PartialAddrRangeCoverage` branch, the call at `lsq_unit.cc:2016` (`iewStage->rescheduleMemInst(load_inst)`).

- [ ] **Step 1: Implement the selector and the read-only call site**

The hook is consulted immediately before the reschedule call; it records `{event_ordinal, dyn_inst_seq, pc, tick, lq_idx, lq_gen, store_seq, coverage, pre_replay_generation, post_replay_generation}` and returns whether to skip.

- [ ] **Step 2: Unit test the ordinal rule** — ordinal N selects exactly the Nth eligible event; ordinal 999 selects none; count-only never skips.

- [ ] **Step 3: Build and smoke**

```bash
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt 2>&1 | tail -3
cd .. && build/ARM/gem5.opt --outdir=/tmp/rp01_count configs/se/lsu_proxy.py --cpu O3 \
  --chaos_lsqfwd --lsq_struct_mode rp01_count_only --rp01_event_ordinal 0 \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency 2>&1 | grep -c RP01_ELIGIBLE
```
Expected: link line, no new warnings, a non-zero eligible count.

- [ ] **Step 4: Run the five frozen seeds**

Seeds: `3135797961, 226489823, 1735144973, 2455796178, 3984724524` (R01–R05). For each, record the first five eligible events with identity. Expected: five distinct `(seq, pc, lq_gen, store_seq)` tuples per seed. If a seed cannot supply five, write `WORKLOAD_INSUFFICIENT_FOR_FIVE_CONTEXTS` for that seed; do not change the seed.

- [ ] **Step 5: Publish the preflight CSV and commit** the source + CSV as two commits.

### Task 15: RP01 implementation — skip one replay trigger; five Pilot + five Control

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/{CHAOSLSQFwd.hh,CHAOSLSQFwd.cc}` (skip mode + watchdog + trace)
- Modify: `configs/se/lsu_proxy.py` (watchdog/exit wiring already present; add RP01 flags)
- Test: `tests/test_rp01_skip.cc`
- Create: `audit_v3_2_12/RP01_Propagation_Audit_v3.2.12.md`, `pilots_v3_2_12/RP01-R01..R05`, `RP01-CONTROL-R01..R05`

**Interfaces:**
- Produces `rp01_skip` `{event_ordinal, dyn_inst_seq, pc, lq_idx, lq_gen, pre_replay_generation, post_replay_generation, insts_to_replay_before, insts_to_replay_after, skipped=1}` and a watchdog line `CHAOS_RP01_WATCHDOG_EXPIRED`.
- Consumes: Task 14's selector; `terminal_rules.adjudicate` for classification.

- [ ] **Step 1: Implement the skip** — exactly one `rescheduleMemInst` call skipped for the selected ordinal; the stall record, `++replayGeneration`, `clearIssued`, `effAddrValid(false)`, `request->discard()`, `setRequest(nullptr)`, and `return NoFault` remain unchanged. One-shot only.

- [ ] **Step 2: Prove no other wake-up path recovers the load**

Read `MemDepUnit::instsToReplay`, `replayMemInst`, and the store-completion path; quote why a load absent from `instsToReplay` is never re-issued. If a wake-up path exists, stop and revise the design — do not proceed.

- [ ] **Step 3: Unit test and build** — expected `RP01_SKIP_OK`; build clean.

- [ ] **Step 4: Smoke with ordinal 1**

```bash
build/ARM/gem5.opt --outdir=/tmp/rp01_smoke configs/se/lsu_proxy.py --cpu O3 \
  --chaos_lsqfwd --lsq_struct_mode rp01_skip_replay --rp01_event_ordinal 1 \
  --rp01_watchdog_cycles 20000000 \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/replay_dependency 2>&1 | tail -5
echo "exit=$?"
```
Expected: `exit=1`, `CHAOS_RP01_WATCHDOG_EXPIRED`, trace retained, no `NotImplementedError`.

- [ ] **Step 5: Run five Pilots + five Controls**

Expected: each Pilot is `HANG` or `TIMEOUT` (or `SQUASHED` with a recorded fault-caused squash); each Control completes with the golden checksum `59fc61c040618747`. A Pilot that completes MASKED must be investigated, not celebrated.

- [ ] **Step 6: Audit and commit** — source commit, then evidence commit. Record `DecisionStatus=APPROVED_BY_RESEARCHER_V3.2.12` with the brief's §7 as authority.

### Task 16: Unified 12-model closure matrix and per-model summaries

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LSU_12Model_Propagation_Closure_Matrix.csv`
- Create: `.../LSU_12Model_Propagation_Closure_Summary_v3.2.12.md`

**Interfaces:**
- Consumes: all per-pilot records from Tasks 4–15.
- Produces: the 24 columns named in the brief §11, one row per model, plus `SupplementaryPilotRequired` and `EvidencePath`.

- [ ] **Step 1: Generate** — `python3 tools/lsu_12model_closure.py matrix --records ... --out ...`.
- [ ] **Step 2: Verify the acceptance arithmetic** — count models with ≥2 complete contexts; list the terminal distribution; flag any model whose only chain is single-context.
- [ ] **Step 3: Write one model-level summary paragraph per model** — earliest anomaly, intermediate edge, final terminal, and what would move it up a class.
- [ ] **Step 4: Commit**

### Task 17: Diagnostic feature dataset

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/LSU_12Model_Diagnostic_Feature_Dataset.csv`

**Interfaces:**
- Consumes: per-pilot records and on-chain events.
- Produces: one row per pilot or path fragment with the five feature groups from brief §12; explicit `NULL`/`NOT_APPLICABLE`; `event_ordinal` monotonic per pilot.

- [ ] **Step 1: Generate** — `python3 tools/lsu_12model_closure.py features ...`.
- [ ] **Step 2: Verify** — no blank cells; every row has `ModelID, PrimaryFaultModel, InjectionTick, ObservedTerminal`; rows for `LIFECYCLE_ONLY` carry `NOT_APPLICABLE` for consumer/commit, not zeros.
- [ ] **Step 3: Commit**

### Task 18: W1–W8 no-fault baselines and the full test suite on the final binary

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_12/baselines_w1_w8/`
- Create: `.../baselines_w1_w8/BASELINE_SUMMARY.csv`

**Interfaces:**
- Consumes: the authoritative workbook's W1–W8 workload mapping (read from the frozen Excel sample rows), the final binary SHA.
- Produces: one no-fault run per W1–W8 workload with golden checksum comparison.

- [ ] **Step 1: Enumerate W1–W8** from the workbook's SampleRunIDs/Workload column and record the exact binary path and workload path per row.
- [ ] **Step 2: Run each baseline**; expected: oracle PASS and the frozen golden checksum; record exit code, binary SHA, workload SHA.
- [ ] **Step 3: Run the full suite** — `pytest tests/ -q` plus the platform tests under `docs/.../platform/tests/`; expected 0 failures.
- [ ] **Step 4: Commit logs and summary**

### Task 19: Excel v3.2.7, MODEL_STATUS_MATRIX and 60-sample freeze audit

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv`
- Modify: `tools/update_lsu_v326_audit.py` or add `tools/update_lsu_v327_audit.py`
- Test: `tests/test_lsu_v327_workbook.py`

**Interfaces:**
- Produces: a workbook whose per-model verdict columns equal the closure matrix, `ConfigFrozen=NO`, formal `ExecutionStatus=NOT_STARTED`, and 60 SampleRunIDs/Seeds unchanged.

- [ ] **Step 1: Write the failing workbook test** — assert the v3.2.6 invariants still hold (sheet count, 43 columns, highlighted cells) and the new audit rows match the CSV byte-for-byte by key.
- [ ] **Step 2: Build the workbook** from the v3.2.6 baseline, adding the v3.2.12 audit sheet and updating model statuses.
- [ ] **Step 3: Run the test and the consistency script** — `pytest tests/test_lsu_v327_workbook.py -v` and `python3 tools/check_v329_consistency.py` (or its successor).
- [ ] **Step 4: Commit**

### Task 20: Package, final acceptance report, blockers

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.12_Final_Acceptance_Report.md`
- Create: `LSU_v3.2.12_12Model_Propagation_Closure_Package.zip`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/DELIVERABLES_SHA256_v3212.txt`

**Interfaces:**
- Produces: the 20-item ZIP required by the brief §15 and the 13-question report required by §16.

- [ ] **Step 1: Write the report** answering the 13 questions directly, each number derived from the closure matrix. State honestly any model that remains below `COMPLETE_CAUSAL_CHAIN`, with the minimal fix.
- [ ] **Step 2: Build the ZIP** with the 20 items; do not include `build/`, `.git/`, or superseded packages.
- [ ] **Step 3: Verify the ZIP** — `unzip -t`, file count, `sha256sum`, and that no historical file is overwritten.
- [ ] **Step 4: Record the final git state** — branch, HEAD, status, binary SHA, disk free; append to the report.
- [ ] **Step 5: Commit and push; do not start the 60 formal runs.**

---

## Plan self-review

- **Spec coverage:** Task 0/1 (baseline, disk, worktree, matrix/Excel consistency) → Tasks 1, 6, 19. Four-model re-verification → Task 5. A01/A03 → Tasks 7–8. FW02 → Task 9. SQ01/SQ03/SP05 → Tasks 10–13. LQ04 → Task 4. RP01 → Tasks 14–15. Missing-evidence minimization → Task 6. Closure matrix → Task 16. Diagnostic dataset → Task 17. Preflight → Tasks 18–19. Package/report → Task 20.
- **Step scan:** every step names a file, a command, or an exact assertion; discovery steps quote the source instead of guessing.
- **Type consistency:** the eight record fields and five classifications are defined once in Task 2 and consumed verbatim by Tasks 3–20; the RP01 hook name `maybeSkipPartialReplay` is used consistently in Tasks 14–15.
- **Review Focus:** five failure modes, each pinned to a test in Task 3, Task 10 or Task 15.
- **Proportion:** the plan is long because the brief has 17 sections and 12 models; no task transcribes an implementation body that the interfaces and tests already determine.
