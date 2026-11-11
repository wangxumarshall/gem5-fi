# LSU v3.3.2 — Final Implementation & Formal Readiness Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the v3.3.1 `PARTIALLY_READY` state into the strongest evidence-backed readiness verdict achievable for the frozen 12 models × R01–R05, fixing the five P0 defects and producing the v3.3.2 package.

**Architecture:** Observation-only C++ hook fixes (LP01 PC/VA, A03 PC + stuck lifecycle) plus candidate workload ELFs (W4 real store→load pair; RP01 partial-overlap; MD04 ≥5 violations) are integrated into one final binary. All 60 contexts are then re-measured on that binary by the eligible-event census, followed by 60 zero-injection controls, 60 fault pilots, causal-chain extraction, independent acceptance, and the package.

**Tech Stack:** gem5 v25.1.0.1 vendored tree (C++/scons), Python 3 platform (`run_pilot.py`, `lsu_v331_census.py`), AArch64 host `gcc -O2 -static`, pytest.

**Spec:** This plan implements the user's 2026-11-11 LSU v3.3.2 directive and the v3.3.1 evidence package at `LSU_v3.3.1_Context_Workload_Finalization_Package.zip` (extracted under `audit_v3_3_1/`).

## Global Constraints

- Scope is exactly 12 models × R01–R05 = 60 fault contexts + 60 matched controls; no 74-model work.
- Never change SampleRunIDs, authoritative seeds, or frozen verdicts; never merge chains across binary SHAs.
- No formal campaign; only count-only/census and pre-formal pilots. Campaign launch waits for researcher authorization.
- Workload mapping changes (W4/RP01/MD04/SQ) remain **candidate** until researcher approval; report them as approval items, never write them into the frozen workbook.
- At most 4 concurrent gem5 processes; one 1.1 GB `build/ARM/gem5.opt` is shared; no per-agent worktree copy.
- One commit per coherent unit; stage explicit paths only (never `git add -A`); auto-push to the feature branch after verification.
- Every claim in a commit/report must cite a command actually run and its real output; `n/a` is never written as zero.
- Build only with `scons -j16 build/ARM/gem5.opt` (29 GB RAM host); never the nested CHAOS build.

## Review Focus

- A candidate workload that still has zero eligible events in `main` under `-O2` (same failure class as v3.3.1 W4) — each workload task must prove the event in the final ELF disassembly and in a real gem5 trace, not in the C source.
- A control that still injects because the model selector ignores `--probability` (DA04 attaches at p=0; MD04 is bound from `--md04_probability`) — each control must show a real `injected=0`/injector-absent artifact.
- A percentile context that collapses onto the same dynamic event (MD04 v3.3.1 N_ROI=1; A03 ALREADY_STUCK) — the mapping must record distinct dynamic identities, and the report must state when the difference is only the observation point of one persistent fault.
- A "consumer" claim inferred from a shared PC or a physical address — LP01 and RP01 chains must carry PC/VA/request identity and explicit consumer or terminal evidence.
- A final binary whose SHA does not match the committed source HEAD — the build log, `git rev-parse HEAD`, and `sha256sum build/ARM/gem5.opt` must be recorded together.

---

### Task 1: Freeze provenance and baseline facts

**Files:**
- Modify/Create: `audit_v3_3_2/report/PROVENANCE.md`, `audit_v3_3_2/report/ROUND_LOG.md`

**Interfaces:**
- Produces: `BASE_HEAD`, `BASE_BINARY_SHA`, `BASE_ELF_SHAS` recorded for every later task.

- [ ] **Step 1: Record git/binary/workload hashes**

Run: `git rev-parse HEAD; sha256sum build/ARM/gem5.opt workloads/directed/* docs/gem5-fi/lsu/implementation_v3_2/workloads/* 2>/dev/null | sort`

Expected: HEAD `3504ec2373ad1de550554693a8e10c87a3a81ad`; binary `d3807fbe…e37e2b2`.

- [ ] **Step 2: Record resource gate**

Run: `df -h .; free -g; nproc`

Expected: ≥20 GiB free on `/home`; build uses `-j16`.

- [ ] **Step 3: Commit**

```bash
git add audit_v3_3_2/report/PROVENANCE.md audit_v3_3_2/report/ROUND_LOG.md
git commit -m "[LSU][V3.3.2][PROV] record baseline HEAD, binary, ELF and resource gate"
```

### Task 2: Close the DA04/MD04 control-misfire hazards in the pilot runner

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py:563-583`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_replay_pilot.py` (RP01 control branch)
- Test: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py`

**Interfaces:**
- Produces: `extra` list for DA04 at `--probability 0.0` contains no `--chaos_lsqfwd`; MD04 at `0.0` contains no `--chaos_md04`; a `--dry-run` flag printing the command without executing gem5.

- [ ] **Step 1: Write the failing tests**

```python
def test_da04_control_omits_injector():
    extra = build_model_extra("DA04", probability=0.0, seed=1, ordinal=1)
    assert "--chaos_lsqfwd" not in extra

def test_md04_control_omits_injector():
    extra = build_model_extra("MD04", probability=0.0, seed=1, ordinal=1)
    assert "--chaos_md04" not in extra
    assert "--md04_probability" not in extra

def test_da04_fault_keeps_injector():
    assert "--chaos_lsqfwd" in build_model_extra("DA04", probability=1.0, seed=1, ordinal=1)
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py -q`

Expected: FAIL (function/guard absent).

- [ ] **Step 3: Extract `build_model_extra(model, probability, seed, ordinal)` from the inline `if/elif` chain and add the p=0 omit branches for DA04 and MD04 (copy the FW02/LQ04 pattern); add `--dry-run` that prints `command.txt` and exits 0.**

- [ ] **Step 4: Run the tests and the dry-run**

Run: `python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py -q; python3 docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py --model DA04 --probability 0.0 --pilot-id V332-DRY-DA04 --context-index 1 --outdir /tmp/v332_dry_da04 --dry-run`

Expected: PASS; command printed contains no `--chaos_lsqfwd`.

- [ ] **Step 5: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py docs/gem5-fi/lsu/implementation_v3_2/platform/run_replay_pilot.py docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_v332_control_guards.py
git commit -m "[LSU][V3.3.2][RUNNER] close DA04/MD04 control misfire paths and add dry-run"
```

### Task 3: LP01 observation hook — record PC, VA, dyn-inst and data identity

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.hh:34`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSL1DForward/CHAOSL1DForward.cc:69-130`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:210-224`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc:1344-1375`
- Test: `tests/test_lp01_identity.cc` (extend)

**Interfaces:**
- Produces: `maybeCorrupt(PacketPtr pkt, bool is_load, DynInst *inst, ...)`; log line gains `pc=`, `va=`, `dyn_inst_seq=`, `lq_entry_id=`, `entry_generation=`, `request_id=`; propagation `inj_l1dfwd` detail gains `pc=`, `vaddr=`, `dyn_inst_seq=`.

- [ ] **Step 1: Extend the LP01 unit test** to assert the record builder emits `pc`, `vaddr`, `dyn_inst_seq` (use a fake `Request`/`DynInst` identity struct, not a live CPU).
- [ ] **Step 2: Run it and confirm failure.**
- [ ] **Step 3: Implement the signature/log change; keep the fault (byte0 XOR) untouched.**
- [ ] **Step 4: Build** `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` (first invocation may be slow; do not abort), then `cd ../.. && cp CHAOS/gem5/build/ARM/gem5.opt build/ARM/gem5.opt` is **not** allowed — build at repo root if configured; otherwise record the actual output path and keep one binary.
- [ ] **Step 5: Run one LP01 pilot** and quote a log line containing `pc=` and `va=`.
- [ ] **Step 6: Commit.**

### Task 4: A03 — record the real PC and a stuck-state lifecycle

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc:400-455, 560-585`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh:48-54,100`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq.cc` (pass `inst->pcState().instAddr()` into the PRE hook)
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/a03_stream.hh`
- Test: `tests/test_addrpath_a03_stream.cc`

**Interfaces:**
- Produces: `A03_STREAM` rows with real `pc`; a `A03_STUCK_LIFECYCLE` line at exit with `fault_id`, `activation_seq/pc/ea`, `applications`, `already_stuck`, `affected_loads`, `first_affected_seq`.

- [ ] **Step 1: Extend the A03 stream test** to require `pc != 0` propagation and lifecycle counters.
- [ ] **Step 2: Run it and confirm failure.**
- [ ] **Step 3: Implement `a03NoteEligibleLoad(..., pc)` and the lifecycle counters; do not change the stuck-0 semantics.**
- [ ] **Step 4: Rebuild; run one A03 fault pilot; quote `pc=0x400…` in `A03_STREAM`.**
- [ ] **Step 5: Commit.**

### Task 5: W4 candidate — real store→load forwarding pair (FW02)

**Files:**
- Create: `workloads/directed/sq_forward_w4v2.c` (copy of `sq_forward_v33.c`, same seven phases, `volatile` array)
- Create: `workloads/directed/compile_sq_forward_w4v2.sh`
- Create: `workloads/directed/sq_forward_w4v2.golden`
- Create: `audit_v3_3_2/workloads/W4_v2_evidence.md`

**Interfaces:**
- Produces: ELF `workloads/directed/sq_forward_w4v2` + SHA256 + host/gem5 oracle.

- [ ] **Step 1: Build** `gcc -O2 -static -o workloads/directed/sq_forward_w4v2 workloads/directed/sq_forward_w4v2.c`.
- [ ] **Step 2: Prove the pair in the final ELF** with `objdump -d --disassemble=main` — quote the `str` then `ldr` at the full-overlap site and the `str`/`ldur w` at the partial-overlap site.
- [ ] **Step 3: Host oracle** — run the ELF; expected `checksum=0x1f4cbf14327717df` (same as frozen W4).
- [ ] **Step 4: gem5 baseline** on the current binary (`configs/se/lsu_proxy.py --cmd … --cpu O3 --variant B0`); quote exit 0 and the same checksum.
- [ ] **Step 5: FW02 count-only** — `run_pilot.py --model FW02 --probability 0.0` twice, with `CHAOS_FW02_SUMMARY observed>0`; record the first five `main` loads.
- [ ] **Step 6: Commit** (candidate only; frozen workbook untouched).

### Task 6: RP01 candidate — partial-overlap store→load workload

**Files:**
- Create: `workloads/directed/replay_partial_v332.c` (+ compile script, golden)
- Create: `audit_v3_3_2/workloads/RP01_evidence.md`

**Interfaces:**
- Produces: five distinct `RP01_ELIGIBLE` events in `main` under count-only, with `(load_seq, load_pc, lq_idx, lq_gen, store_seq)` distinct.

- [ ] **Step 1: Write** a loop that stores 8 B to `buf[i]`, then loads 4 B at `buf[i]+2` (partial coverage), with a long-latency dependency so the load can reach the partial branch; keep the oracle a checksum over all bytes.
- [ ] **Step 2: Build, host oracle, objdump proof** (store size 8, load size 4, overlap 2 bytes).
- [ ] **Step 3: gem5 count-only preflight** with `--lsq_struct_mode rp01_count_only`, collect `RP01_ELIGIBLE` lines; require ≥5 distinct identities in `main`.
- [ ] **Step 4: If <5, iterate the workload (more iterations / varied offsets / multiple PCs) until ≥5 or document the blocker honestly.**
- [ ] **Step 5: Commit** (candidate only).

### Task 7: MD04 candidate — ≥5 in-loop violation pairs

**Files:**
- Create: `workloads/directed/md04_violations_v332.c` (+ compile script, golden)
- Create: `audit_v3_3_2/workloads/MD04_evidence.md`

**Interfaces:**
- Produces: `md04_injections.log` count-only `CHAOS_ELIGIBLE_COUNT >= 5`, all in `main`.

- [ ] **Step 1: Write** a loop with 8 B stores and 8 B (or 16 B) loads that overlap dynamically but are not trivially forwarded: compute the load address through an independent dependency chain so the load issues before the older store resolves; repeat with ≥64 varied addresses.
- [ ] **Step 2: Build, host oracle, objdump proof** of store/load PCs in `main`.
- [ ] **Step 3: gem5 count-only** `--model MD04 --probability 0.0`; quote `CHAOS_ELIGIBLE_COUNT` and `MD04_TARGET_STATUS`; require ≥5.
- [ ] **Step 4: Iterate or document the blocker honestly.**
- [ ] **Step 5: Commit** (candidate only).

### Task 8: Integrate source changes and build the final binary

**Files:**
- Modify: `audit_v3_3_2/report/PROVENANCE.md`, `audit_v3_3_2/report/BUILD_LOG.txt`

**Interfaces:**
- Produces: `FINAL_HEAD`, `FINAL_BINARY_SHA`, one binary at `build/ARM/gem5.opt`.

- [ ] **Step 1: Review the combined diff** `git diff --stat HEAD` and reject any unrelated change.
- [ ] **Step 2: Build** `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt` (capture full log); if the repo-root binary is produced by a different target, record it.
- [ ] **Step 3: Copy/produce the repo-root binary once**, then `sha256sum build/ARM/gem5.opt`.
- [ ] **Step 4: Regression** `pytest tests/ -q` and `pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests -q`; quote pass counts.
- [ ] **Step 5: Commit** source + provenance (binary is not tracked; record its SHA).

### Task 9: Final 60-context census and percentile mapping

**Files:**
- Create: `audit_v3_3_2/roi/LSU_60Context_ROI_Percentile_Mapping.csv`
- Create: `audit_v3_3_2/roi/LSU_60Context_Distinctness_Audit.csv`
- Create: `audit_v3_3_2/roi/LSU_ROI_Boundaries.csv`
- Modify: `tools/lsu_v332_census.py` (copy of v331; candidate workload paths + A03 LP01 fields)

- [ ] **Step 1: Run coarse + boundary + percentile census per model on `FINAL_BINARY_SHA`**; preserve every command.txt and JSONL.
- [ ] **Step 2: Compute N_ROI and `k(p)=ceil(p·N)`** with a recorded script; write all 60 rows; every field observed or explicitly `n/a`.
- [ ] **Step 3: Distinctness audit** — seq/PC/VA/entry/generation/state; flag any collapse.
- [ ] **Step 4: Commit** the CSVs, census JSONL, and script.

### Task 10: 60 matched controls on the final binary

**Files:**
- Create: `audit_v3_3_2/controls/LSU_60Context_Control_Pair_Final.csv`

- [ ] **Step 1: Run one control per context** with the Task 2 guards; same seed/ELF/ROI/config as its fault; concurrency ≤4.
- [ ] **Step 2: Gate each control** on injector-absent `config.ini` or `injected=0`/`injection_count=0` + `pilot_meta.injection.events == []`; reject/flag anything else.
- [ ] **Step 3: Commit** the CSV + raw control dirs.

### Task 11: 60 fault pilots and causal-chain closure

**Files:**
- Create: `audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv`
- Create: `audit_v3_3_2/propagation/LSU_Workload_Oracle_Final_Audit.csv`

- [ ] **Step 1: Run the 60 faults** at their mapped ordinals on the final binary.
- [ ] **Step 2: Extract injection → activation → first divergence → downstream → consumer → commit/squash/replay → architecture → oracle** for each; classify terminal honestly (SDC/MASKED/SQUASHED/CRASH/HANG/INJECTION_NOT_ACTIVATED/TRACE_INCOMPLETE).
- [ ] **Step 3: For RP01 HANG**, require watchdog + stalled-progress evidence; for SQUASHED, require fault identity causality.
- [ ] **Step 4: Commit** CSVs + raw evidence.

### Task 12: SQ approval record, independent acceptance, and package

**Files:**
- Create: `LSU_v3.3.2_Formal_Experiment_Readiness_Package.zip`
- Create: `audit_v3_3_2/report/LSU_v3.3.2_Final_Acceptance_Report.md`
- Create: `audit_v3_3_2/report/LSU_Final_Blockers.md`
- Create: `audit_v3_3_2/report/LSU_Independent_Acceptance_Report.md`
- Create: `audit_v3_3_2/sq_workload/LSU_SQ_Workload_Decision.md`
- Create: `audit_v3_3_2/LSU_Formal_Experiment_Config.xlsx`

- [ ] **Step 1: Update the SQ01/SQ03/SP05 comparison** with final dynamic evidence and a single recommendation per model.
- [ ] **Step 2: Dispatch an independent read-only verifier** (Agent F) over the package; record findings and corrections.
- [ ] **Step 3: Write the 15-question report** and the gate table; final status ∈ {READY_FOR_FORMAL_EXPERIMENT, PARTIALLY_READY, NOT_READY}.
- [ ] **Step 4: Package** all required CSVs, logs, traces, SHA256, git diff, workbook; verify `unzip -t`.
- [ ] **Step 5: Commit and push.**

## Self-review notes

- Spec coverage: P0-1→Task 5, P0-2→Task 6, P0-3→Task 7, P0-4→Task 3, P0-5→Task 4; controls→Tasks 2/10; propagation→Task 11; binary freeze→Task 8; package→Task 12.
- Approval items (W4/RP01/MD04/SQ mapping, ROI/Warm-up freeze, config freeze) remain explicitly pending researcher approval; the final verdict cannot be `READY` for unapproved workload changes.

## Execution status (2026-11-11)

- [x] Task 1 baseline provenance
- [x] Task 2 runner control guards (13 tests; DA04/MD04/RP01 omit injector at p=0; dry-run)
- [x] Task 3 LP01 PC/VA identity (real pilot: pc/va/seq/lq in the record; parser fixed)
- [x] Task 4 A03 real PC + stuck lifecycle (pc 0x400598; lifecycle line; log cap)
- [x] Task 5 W4 candidate (in-main forward; observed=67; ordinal-50 SDC)
- [x] Task 6 RP01 candidate (255 in-main events; five distinct; watchdog HANG)
- [x] Task 7 MD04 candidate (8 in-main violations; five contexts; R01 MASKED + 4 SDC)
- [x] Task 8 final build (070d68a6…, 0 errors; 180 + 120 tests passed)
- [x] Task 9 60-context census/mapping (all arithmetic validated; FW02 offset fixed)
- [x] Task 10 60 controls (60/60 zero-injection)
- [x] Task 11 60 faults + causal rows (36 SDC, 12 MASKED, 1 SQUASHED, 10 HANG, 1 UNRESOLVED)
- [x] Task 12 independent acceptance + package (Agent F found FW02 offset/stale provenance; fixed)
- [ ] Researcher approval for 30 candidate contexts and config freeze (blocker B1/B6)
