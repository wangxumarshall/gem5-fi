# LSU v3.2.9 — SP05 implementation, SQ03 propagation probe, FW05 closure

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the frozen SP05 premature-store-completion hook and run its five pilots, probe whether SQ03's early `_canWB` can ever be observed by a later load, and close the FW05 archive/baseline/Excel gaps.

**Architecture:** Work on branch `lsu-platform-v3.2.9` in the existing `lsu-platform-v3.2` worktree (base `d5c15309`). SP05 gets a new `CHAOSLSQFwd` struct mode and a two-site hook: target selection at `commitStores` (when a store earns `canWB`) and premature completion at `writebackStores` (calling the real `completeStore` before the cache write is sent). SQ03 work is read-only trace analysis plus one independent probe workload; the SQ03 fault hook is not touched. FW05 work is archive-script repair, matched no-fault baselines, and a new workbook.

**Tech Stack:** gem5 v25.1.0.1 AArch64 vendored tree, scons, C++17, Python 3.11, openpyxl, JSONL Trace v3.1, gzip CSV.

**Spec:** Researcher's v3.2.9 work order, copied verbatim to `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.9_Work_Order.md`; plus `SP05_Definition_Freeze_v3.2.8.md`, `SQ03_Definition_Freeze_v3.2.7.md`, `SQ03_Propagation_Chain_Report_v3.2.8.md`.

## Global Constraints

- Base v3.2.8 (`d5c15309`); do not modify v3.2.8 branch, package or history.
- No 60-sample formal run. Do not change the 12 models, or any of the 60 SampleRunID/RunID/SubTaskID/Seed.
- `ConfigFrozen` stays `NO` for all 60.
- SQ03's frozen fault definition and its five v3.2.8 pilots/traces are not modified or deleted.
- SP05 and SQ03 are distinct: SQ03 = `_canWB` in `executeStore`; SP05 = `_completed` in `completeStore`.
- Never `git clean -fd`; never `git add -A`; stage explicit paths; one patch per unit.
- Report `n/a`, `NOT_INJECTED`, `HANG`, `TIMEOUT`, `MASKED`, `SDC` honestly; never a silent zero or fabricated pass.
- Trace interface is changed once, in Task 5; SQ03 tasks read traces only.

## Review Focus

1. **Premature vs suppressed completion.** The legacy v3.2.2 Excel text says "suppress one completeStore update; entry cannot be released; HANG". The frozen v3.2.8 definition and the v3.2.9 order say "premature completion". The implemented state change must be the frozen premature one; the conflict is documented and the legacy text is corrected only in the new workbook's revision record.
2. **Double completion / counter underflow.** Completing a store before its cache write must not later produce a second `completeStore` from a response, and `storesToWB` must decrement exactly once. The hook requires `!request->isSent()` and asserts the delta.
3. **SKU state and entry lifetime.** `completeStore` clears the SQ head entry and calls `freeLSQEntry`; the hook must handle `storeWBIt` exactly like the existing store-conditional path and must not touch a sent request.
4. **One-shot and ordinal identity.** The target is entry-keyed by SQ index + generation; a second call, a reused entry, or `max_faults=0` must not inject again.
5. **Baseline equivalence.** The FW05 strict baseline must differ from the fault run only in `probability` (0.0 vs 1.0) with the same binary, mode, seed and ordinal; the injector must still be attached at probability 0.
6. **Probe honesty.** If SQ03's early `_canWB` cannot change a later load's data, the probe reports that with real traces; it does not invent a consumer edge or SDC.

---

### Task 1: v3.2.9 branch, work-order copy, baseline

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.9_Work_Order.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/GIT_BASELINE_v329.txt`
- Modify: this plan file.

- [x] **Step 1: Create branch and baseline**

```bash
git checkout -b lsu-platform-v3.2.9
{ echo "base: d5c15309"; git rev-parse HEAD; sha256sum build/ARM/gem5.opt; } \
  > docs/gem5-fi/lsu/implementation_v3_2/GIT_BASELINE_v329.txt
```

- [x] **Step 2: Copy the work order verbatim** into `LSU_v3.2.9_Work_Order.md` with a one-line provenance note.

- [x] **Step 3: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.9_Work_Order.md \
        docs/gem5-fi/lsu/implementation_v3_2/GIT_BASELINE_v329.txt \
        docs/superpowers/plans/2026-11-08-lsu-v329-sp05-sq03probe-fw05closure.md
git commit -m "[LSU][MDSPEC][V3.2.9][DOCS] start v3.2.9 from v3.2.8 and record work order"
git push -u origin lsu-platform-v3.2.9
```

---

### Task 2: SP05 source audit and semantics reconciliation

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/SP05_Source_Audit_v3.2.9.md`
- Modify: this plan file (step checkboxes).

- [x] **Step 1: Record the observed lifecycle with line anchors.** `commitStores` (`lsq_unit.cc:896-925`) sets `canWB` and `++storesToWB`; `writebackStores` (`lsq_unit.cc:932-1070`) sends the packet only after the target is selected; `completeDataAccess` (`lsq_unit.cc:221/229`) and the instant paths (`959/1045/1063`) call `completeStore`; `completeStore` (`lsq_unit.cc:1325-1380`) does `_completed=true; --storesToWB`, pops completed head entries and calls `setCompleted()`.

- [x] **Step 2: Pin the frozen state change.** "Premature" means `_completed=true` and the `storesToWB` decrement happen before the store's cache write is sent. The minimal hook is: at the first time the target entry is selected as `storeWBIt` with `!request->isSent()`, call `completeStore(storeWBIt)` and skip the send; the decrement is the real completeStore one.

- [x] **Step 3: Record the conflict.** Quote `LSU_Model4_Design_and_Safety_v3.2.2.md` §SP05 ("suppress one completeStore/`_completed` update"; "SQ entry never pops; backpressure can fill the 16-entry queue and hang") against `SP05_Definition_Freeze_v3.2.8.md` ("marks one selected live store complete early"). State the resolution: implement the frozen premature semantic; do not implement suppression; correct only the `FaultDuration` wording in the v3.2.4 revision sheet; keep the legacy statement in history.

- [x] **Step 4: Enumerate invariants the hook must check** (write them verbatim in the doc): `!request->isSent()`, `storesToWB > 0`, `!entry.completed()`, target identity `(sqIdx, sqEntryGeneration)` matches, after the call `completed()==true` and `storesToWB_new == storesToWB_old - 1`, and no second `completeStore` for the same DynInst. Also state explicitly: completion-before-write cannot make data visible earlier; if anything it drops the write.

- [x] **Step 5: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/SP05_Source_Audit_v3.2.9.md
git commit -m "[LSU][MDSPEC][V3.2.9][SP05] audit completeStore lifecycle and reconcile premature-vs-suppressed wording"
```

---

### Task 3: SP05 rules extension and unit test

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/sp05_rules.hh`
- Modify: `tests/test_sp05_rules.cc`

**Interfaces:**
- Produces: `chaos_sp05::shouldSelect(uint64_t eligible_count, uint64_t ordinal) -> bool`; existing `shouldComplete(sq_idx, sq_gen, target_idx, target_gen, injected, max_faults) -> bool` unchanged.

- [x] **Step 1: Extend the test first**

```cpp
assert(shouldSelect(2, 2));
assert(!shouldSelect(2, 0));       // ordinal 0 = not selected
assert(!shouldSelect(1, 2));       // not yet
assert(!shouldSelect(2, 1));       // wrong ordinal
```

- [x] **Step 2: Run it to verify failure**

`g++ -std=c++17 -I CHAOS/gem5/src tests/test_sp05_rules.cc -o /tmp/test_sp05_rules && /tmp/test_sp05_rules`
Expected: compile error, `shouldSelect` not declared.

- [x] **Step 3: Implement `shouldSelect`** as `return ordinal != 0 && eligible_count == ordinal;` and keep `shouldComplete` byte-identical.

- [x] **Step 4: Rebuild and run**

`g++ -std=c++17 -I CHAOS/gem5/src tests/test_sp05_rules.cc -o /tmp/test_sp05_rules && /tmp/test_sp05_rules`
Expected: `SP05 completion rules: PASS`.

- [x] **Step 5: Commit**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/sp05_rules.hh tests/test_sp05_rules.cc
git commit -m "[LSU][MDSPEC][V3.2.9][SP05] add ordinal target-selection rule and test"
```

---

### Task 4: SP05 config plumbing (mode, params, runner)

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.py`
- Modify: `configs/se/lsu_proxy.py`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py`

**Interfaces:**
- Produces: `StructMode::Sp05Complete`; `bool CHAOSLSQFwd::maybeSelectSP05(uint64_t seq, uint64_t sq_idx, uint64_t sq_gen)`; `bool CHAOSLSQFwd::maybeCompleteSP05(uint64_t seq, uint64_t sq_idx, uint64_t sq_gen, bool request_sent)`; `void CHAOSLSQFwd::sp05Watchdog()`; params `sp05EventOrdinal`, `sp05WatchdogCycles`.

- [x] **Step 1: Add the enum, include and declarations.** Include `sp05_rules.hh`; add `Sp05Complete` to `StructMode`; declare the three methods and fields `sp05_target_idx`, `sp05_target_gen`, `sp05_target_seq`, `sp05_selected`, `sp05_fired`, `EventFunctionWrapper *sp05_watchdog_event`.

- [x] **Step 2: Parse the mode and params.** `stringToStructMode("sp05_complete")`; add `.py` params `sp05EventOrdinal = Param.UInt64(0, ...)` and `sp05WatchdogCycles = Param.UInt64(500000000, ...)`; in the constructor clamp `max_faults==0` to 1, attach `cpu->lsqFwd = this`, schedule `sp05Watchdog` at `cpu->clockEdge(Cycles(p.sp05WatchdogCycles))`, and register an exit summary `CHAOS_SP05_STATUS: selected=... fired=... injected=... eligible=...`.

- [x] **Step 3: Add `--sp05_event_ordinal` and `--sp05_watchdog_cycles`** to `lsu_proxy.py` and pass them into the SimObject (`sp05EventOrdinal=args.sp05_event_ordinal`, `sp05WatchdogCycles=args.sp05_watchdog_cycles`).

- [x] **Step 4: Add the runner dispatch.** In `run_pilot.py`, add `elif args.model == "SP05":` with `--chaos_lsqfwd --lsq_struct_mode sp05_complete --max_faults 1 --rng_seed <seed> --sp05_event_ordinal <ordinal> --sp05_watchdog_cycles 500000000`, plus `--timeout` handling already present.

- [x] **Step 5: Attach the FW05 injector at probability 0** (strict-baseline fidelity): extend the constructor attach condition with `struct_mode == StructMode::Fw05OlderSrc`. Behaviour at `probability==0` is unchanged (the hook returns false).

- [x] **Step 6: Build and commit**

`scons -j16 build/ARM/gem5.opt` (first configure is slow; do not abort). Expected: exit 0.
`git commit -m "[LSU][MDSPEC][V3.2.9][SP05] add sp05_complete mode, params and runner dispatch"`.

---

### Task 5: SP05 hook, trace node and watchdog

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`

**Interfaces:**
- Consumes: `maybeSelectSP05`, `maybeCompleteSP05` from Task 4.
- Produces: trace event `sp05_complete` with `dyn_inst_seq`, `sq_entry_id`, `entry_generation`, `old_value` (`canWB,completed,storesToWB,mem_sent`) and `new_value` (`completed,storesToWB`).

- [x] **Step 1: Selection at commitStores.** After `x.canWB() = true; ++storesToWB;`:

```cpp
if (cpu->lsqFwd)
    cpu->lsqFwd->maybeSelectSP05(x.instruction()->seqNum, x.instruction()->sqIdx,
                                 x.instruction()->sqEntryGeneration);
```

- [x] **Step 2: Premature completion at writebackStores.** After `DynInstPtr inst` / `LSQRequest* request` are available and after the size/prefetch checks, before the store-conditional branch:

```cpp
if (cpu->lsqFwd &&
    cpu->lsqFwd->maybeCompleteSP05(inst->seqNum, inst->sqIdx,
                                   inst->sqEntryGeneration, request->isSent())) {
    completeStore(storeWBIt);
    if (!storeQueue.empty()) storeWBIt++; else storeWBIt = storeQueue.end();
    continue;
}
```

- [x] **Step 3: Injector methods.** `maybeSelectSP05` counts newly-canWB stores, stores `(seq, idx, gen)` when `chaos_sp05::shouldSelect(eligible_count, sp05_event_ordinal)`. `maybeCompleteSP05` requires `struct_mode==Sp05Complete`, `probability>0`, `!request_sent`, `sp05_selected && !sp05_fired`, identity match, `chaos_sp05::shouldComplete(...)`, `storesToWB` not available to the injector so the caller logs it; sets `sp05_fired=true; ++faults_injected_count; assert(faults_injected_count==1)`, writes the log line `Cycle, Site: writebackStores_prematureComplete, store_seq, sq_idx, sq_gen, canwb, completed_before, mem_sent, eligible_ordinal`.

- [x] **Step 4: Trace node.** Add `CHAOSPropagation::noteSP05Complete(seq, sq_idx, sq_gen, canwb, completed, stores_to_wb, mem_sent, tick)` emitting `event_type="sp05_complete"`; call it from `completeStore` after the real state change, only when `cpu->lsqFwd->sp05Mode()`.

- [x] **Step 5: Watchdog.** `sp05Watchdog()` logs `CHAOS_SP05_WATCHDOG=EXPIRED` and calls `fatal("CHAOS_SP05_WATCHDOG_EXPIRED ...")`, so expiry is exit 1 and cannot be MASKED.

- [x] **Step 6: Build and commit**

`scons -j16 build/ARM/gem5.opt`; expect exit 0.
Commit message: `[LSU][MDSPEC][V3.2.9][SP05] premature completion hook, trace node and watchdog`.

---

### Task 6: SP05 hook tests (safety and non-target)

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/SP05_safety/` (logs)
- Modify: `tests/test_sp05_rules.cc` (only if a rule case is missing)

- [x] **Step 1: One-shot and clamp smoke.** Run `store_path` with `--lsq_struct_mode sp05_complete --max_faults 0 --sp05_event_ordinal 1 --rng_seed 1489155957 --sp05_watchdog_cycles 500000000 --chaos_propagation`. Expected: exit 0, one `writebackStores_prematureComplete` line, `faults_injected: 1`, `CHAOS_SP05_STATUS: fired=1 injected=1`.

- [x] **Step 2: Non-target integrity.** Run with `--sp05_event_ordinal 2`. Expected: target is a different `(sq_idx, sq_gen)`; exactly one `sp05_complete` event; all other stores' completion count equals the no-fault run (compare stats `system.cpu.numStoreInsts`/`iew.storeInsts` unchanged).

- [x] **Step 3: Counter consistency.** In both smokes, assert from the log/trace: `storesToWB_before - storesToWB_after == 1`, `_completed` false→true, and no second `sp05_complete` for the same seq. If the assert fails, stop and report; do not weaken it.

- [x] **Step 4: Watchdog.** Run with `--sp05_watchdog_cycles 1`. Expected: exit 1, `CHAOS_SP05_WATCHDOG=EXPIRED`, no MASKED classification.

- [x] **Step 5: Commit** the logs and the (unchanged or extended) test.

`git commit -m "[LSU][MDSPEC][V3.2.9][SP05] one-shot, non-target and watchdog tests"`.

---

### Task 7: SP05 five pilots and no-fault controls

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_9/SP05-R01..R05/`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/SP05_v329_EVIDENCE.csv`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/SP05_Implementation_v3.2.9.md`

- [x] **Step 1: Run the five Excel samples** with `run_pilot.py --model SP05` (seeds `1489155957, 1290498198, 2768710389, 2741073922, 4098160626`, ordinals 1–5, workload `store_path`, `--timeout 300`). Capture stdout/stderr/exit, injection log, trace JSONL, oracle log.

- [x] **Step 2: Run five matched no-fault controls** with the same command and `--probability 0.0`; record checksums.

- [x] **Step 3: Build the evidence CSV** with columns: `pilot,sample_run_id,seed,event_ordinal,injected,seq,pc,addr,size,sq_idx,sq_gen,canwb_before,completed_before,completed_after,stores_to_wb_before,stores_to_wb_after,mem_sent,inject_tick,store_commit_tick,target_squashed,consumer_instructions,terminal,oracle,hang,timeout`.

- [x] **Step 4: Write the implementation doc.** State for each pilot whether injection happened, whether the target store was real and eligible, the exact state delta, whether a later load/consumer exists, and the terminal/oracle. Do not claim propagation without a consumer edge.

- [x] **Step 5: Commit**

`git commit -m "[LSU][MDSPEC][V3.2.9][SP05] five pilots, matched no-fault controls and evidence"`.

---

### Task 8: SQ03 original-trace propagation re-analysis

**Files:**
- Create: `tools/analyze_sq03_propagation.py`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/SQ03_propagation_v328.csv`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/SQ03_Propagation_Analysis_v3.2.9.md`

- [x] **Step 1: Parse the five v3.2.8 fault traces and the five baselines** (`pilots_v3_2_8/SQ03-R0*/trace_v31.jsonl`, `evidence_v3_2_8/SQ03_baselines/R0*/prop_trace.csv.gz`), keyed by the target store seq.
- [x] **Step 2: Emit per pilot**: `inj_tick` (canWB), `store_writeback_tick`, `store_mem_write_tick`, `sq03_complete_tick`, and the same fields for the baseline; compute deltas. Do not treat `_canWB` as data visibility.
- [x] **Step 3: Conclude** separately: permission granted early? writeback events? actual cache/memory update tick? later load reads? consumer? State where the chain stops.
- [x] **Step 4: Commit** the tool, CSV and document.

---

### Task 9: SQ03_Propagation_Probe

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/workloads/sq03_probe.c`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/workloads/compile_sq03_probe.sh`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/workloads/sq03_probe` and `sq03_probe.golden`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_9/SQ03-PROBE-F0-P00`, `...P01`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/SQ03_Probe_Report_v3.2.9.md`

**Interfaces:** independent SampleIDs `SQ03-PROBE-F0-P00` (control) and `SQ03-PROBE-F0-P01` (fault); not in the 60.

- [x] **Step 1: Write the workload.** A deterministic loop that writes distinct values to an array, then loads them back in program order, consumes each load (accumulate, branch on a derived value) and prints `checksum=0x<16 hex>`.
- [x] **Step 2: Compile and record the golden** on the host (`gcc -O2 -static`), then verify host and gem5 agree without injection.
- [x] **Step 3: Run fault and control** with `--lsq_struct_mode sq03_canwb --max_faults 1 --probability 1.0` vs `--probability 0.0`, same seed and ordinal, with trace enabled. Record load request/response, register writeback, consumer commit and checksum.
- [x] **Step 4: Write the conclusion.** If the load forwards from the SQ, the data is identical by construction; early `_canWB` can move the store's cache write but not the forwarded value. If a real consumer observes a changed value, record SDC with the edge; otherwise record MASKED and the microarchitectural reason.
- [x] **Step 5: Commit.**

---

### Task 10: FW05 archive run script repair

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/run_pilot.sh`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/FW05_Workload_Archive/README.md` (usage)
- Regenerate: `FW05_Workload_Archive/SHA256SUMS`

- [x] **Step 1: Rewrite the script** to locate the repo root with `ROOT="${GEM5_ROOT:-$(git -C "$(dirname "$0")" rev-parse --show-toplevel)}"`, resolve `HERE` as the archive directory, and run `--cmd="$HERE/bin/fw05_forward"`; fail loudly if the binary or config is missing.
- [x] **Step 2: Test from an isolated temp dir** by copying the archive to `/tmp/fw05_archive_test`, running it with `GEM5_ROOT` set to the worktree, and checking `checksum=0x67afad307642983e` and exit 0.
- [x] **Step 3: Verify the archived binary SHA is unchanged** (`0cf40509…`), regenerate `SHA256SUMS`, and commit.

---

### Task 11: FW05 strict matched baselines

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines/R01..R05/`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/evidence_v3_2_9/FW05_strict_baselines.csv`
- Modify: `FW05_Workload_Archive/baselines/README.md` (or `FW05_No_Fault_Baselines_v3.2.8.md` addendum)

- [x] **Step 1: Run the five strict baselines** with the final binary: `--chaos_lsqfwd --lsq_struct_mode fw05_older_src --probability 0.0 --max_faults 1 --rng_seed <seed> --lsqfwd_event_ordinal <ordinal>`, same workload/SHA. Record exit, checksum, stdout.
- [x] **Step 2: Pair them** with the v3.2.8 final-binary fault-on recheck (`evidence_v3_2_8/recheck_final_binary/`) row by row; the only difference is `probability`. Record both checksums.
- [x] **Step 3: Verify** all five controls are `0x67afad307642983e` and the four SDC checksums still match; commit.

---

### Task 12: Excel v3.2.4

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/excel/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.4.xlsx`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/excel/FW05_CONFIG_v3.2.4.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/excel/FW05_OLD_NEW_DIFF_v3.2.4.md`
- Create: `tools/build_lsu_v324_workbook.py`
- Create: `tests/test_lsu_v324_workbook.py`

- [x] **Step 1: Write the failing test** asserting: workbook loads; FW05 rows 42–46 have `WorkloadPath` ending in `FW05_Workload_Archive/bin/fw05_forward`, the SHA `0cf40509…`, Oracle `67afad307642983e`; SQ03 rows are `PILOT_RUN_ACCEPTED/MASKED`; SP05 rows reflect the real pilot terminal; all SampleRunID/RunID/SubTaskID/Seed unchanged; `ConfigFrozen` all `NO`; only FW05/SQ03/SP05 status and FW05 path/SHA cells differ from v3.2.3.
- [x] **Step 2: Verify RED** (`FileNotFoundError`).
- [x] **Step 3: Implement the builder** by copying v3.2.3 and changing only those cells, plus a revision sheet row: W8 alignment → fw05_forward (researcher-approved), archive path fix, strict baseline note, SP05/SQ03 status sync, ConfigFrozen stays NO.
- [x] **Step 4: Generate, update `60_SAMPLE_MATRIX.csv`**, run the test (4 passed).
- [x] **Step 5: Commit.**

---

### Task 13: Test dependency and full suite

**Files:**
- Create: `requirements-test.txt`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/logs_v3_2_9/pytest_full.log`

- [x] **Step 1: Install the missing plugin** with `python3 -m pip install --index-url https://pypi.org/simple pytest-check`; record the installed version (`python3 -m pip show pytest-check`). If installation fails, record the exact error and stop the claim of a passing suite.
- [x] **Step 2: Write `requirements-test.txt`** with `pytest==9.1.1`, `pytest-check==<installed>`, `openpyxl==3.1.5`.
- [x] **Step 3: Run the full suite** `python3 -m pytest tests -q`; save output to `logs_v3_2_9/pytest_full.log`. Expected: all tests pass (36+).
- [x] **Step 4: Commit.**

---

### Task 14: Status matrix, consistency and status report

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/MODEL_STATUS_MATRIX.csv`
- Create: `tools/check_v329_consistency.py`
- Create: `tests/test_v329_consistency.py`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.9_Status_Report.md`

- [x] **Step 1: Update the matrix from evidence.** FW05 unchanged (1s). SQ03 keeps `PILOT_RUN=1`; `PROPAGATION_VERIFIED` follows the probe result (0 if no consumer). SP05 gets `IMPLEMENTED/COMPILED/UNIT_TESTED/PILOT_RUN=1` only after Tasks 5–7; `PROPAGATION_VERIFIED` only with a real consumer edge.
- [x] **Step 2: Consistency check** across v3.2.4 Excel, CSV, manifests, archive SHA and traces; assert identities unchanged, only the allowed rows differ, `ConfigFrozen=NO`.
- [x] **Step 3: Write the status report** and run all tests; commit.

---

### Task 15: Package and final report

**Files:**
- Create: `LSU_v3.2.9_SP05_Implementation_SQ03_Propagation_FW05_Closure_Package.zip` + `.sha256`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_v3.2.9_Final_Report.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/OPEN_ISSUES_v3.2.9.md`
- Create: `GIT_COMMIT_v329.txt`, `GIT_LOG_v329.txt`, `GIT_STATUS_v329.txt`, `GIT_DIFF_STAT_v329.txt`, `GIT_DIFF_CODE_v329.txt`

- [x] **Step 1: Provenance** (branch, full 40-char HEAD, status, diff, final binary SHA).
- [x] **Step 2: Stage A/B/C/D contents** per the work order, including full SP05 traces, SQ03 original traces and probe traces, FW05 archive, strict baselines, Excel v3.2.4, test logs, open issues.
- [x] **Step 3: SHA256 list and zip**; verify `testzip` and member count.
- [x] **Step 4: Final report answers** the SP05/SQ03/FW05 questions explicitly; commit and push.

---

## Self-Review

- **Spec coverage:** SP05 audit (Task 2), hook/params (Tasks 3–5), safety tests (Task 6), five pilots (Task 7), SQ03 analysis (Task 8) and probe (Task 9), FW05 script/baseline/Excel (Tasks 10–12), dependencies (Task 13), matrix/report (Task 14), package (Task 15).
- **Semantics:** the plan implements premature completion, not the legacy suppressed-completion wording; the conflict is documented before code.
- **Placeholders:** none; each step names the file, command and expected result.
- **Type consistency:** `sp05_complete`, `sp05EventOrdinal`, `sp05WatchdogCycles`, `maybeSelectSP05`, `maybeCompleteSP05`, `sp05_complete` are used consistently.
- **Review Focus** items each have a test: premature/double-completion (Task 6), one-shot/ordinal (Tasks 3,6), baseline equivalence (Task 11), probe honesty (Task 9).
