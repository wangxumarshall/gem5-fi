# LSU Platform v3.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and prove the LSU v3.2 common injection platform (Gate 1), then repair W1-W8 and run the A01/F0, A03/F5, FW02/F6 pilots (Gate 2), with real build logs, run logs, JSONL traces, and oracle results.

**Architecture:** Keep all platform logic in `docs/gem5-fi/lsu/implementation_v3_2/platform/` as stdlib-first Python; keep gem5 hooks inside the vendored tree (`CHAOS/gem5/src/`); convert the existing `CHAOSPropagation` CSV trace to Trace v3.1 JSONL without inventing absent fields. Every gate is verified by commands whose stdout is copied into the gate report.

**Tech Stack:** Python 3.11 (`openpyxl`, `unittest`, stdlib JSON), gem5 v25.1.0.1 vendored tree, SCons 4.5.2, host `gcc 12.3.1`, native AArch64.

**Spec:** Task prompt "LSU v3.2" plus `docs/gem5-fi/lsu/final_paper_audit_v3_1/LSU_12Model_Source_Audit_Report_v3.1.md` and `LSU_Trace_Hook_Design_v3.1.md`.

## Global Constraints

- Frozen scope: 12 models, 5 samples each, 60 SampleRunIDs, 12 SubTaskIDs. Never regenerate seeds or overwrite the original Excel.
- Delivery root: `docs/gem5-fi/lsu/implementation_v3_2/`.
- No accepted result may be "assumed": every check runs a real command and quotes its output.
- Trace incompleteness must never be reported as `MASKED`.
- One patch per unit; do not `git add -A`; stage explicit paths.
- Work only on branch `lsu-platform-v3.2` in `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2`.
- The 2026-11-06 09:43-09:45 pre-existing artifacts are preserved under `preexisting_rejected/` and are not accepted: A01 was injected at `sendFragmentToTranslation`, which the audit explicitly rejects, and A03 recorded `injected=0`.

## Review Focus

1. `SampleRunID`/`SubTaskID`/`RunID` parent mismatch or duplicate seed — parser must reject, never coerce.
2. `WorkloadPath == ABSENT` — parser reports every missing sample and exits non-zero; no default path.
3. A01/A03 op filtering — a store address must never be eligible; a stuck-at application whose bit is already 0 is counted and logged as `nochange`, not silently dropped.
4. Trace orphan edges / missing terminal evidence — validator and completeness checker must fail closed and never emit `MASKED`.
5. W6/W8 out-of-bounds — recompiled binary SHA, fresh golden, and ASan/UBSan clean baseline must agree before any pilot uses them.

---

## Gate 1 — Common Base

### Task 1: Environment snapshot and pre-existing-artifact quarantine

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/environment.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/preexisting_rejected/README.md`
- Copy: `/home/sdc/gem5-fi-ding/docs/gem5-fi/lsu/implementation_v3_2/{platform,pilots,baselines,workloads,patches}` → `preexisting_rejected/`

- [x] **Step 1: Capture environment facts**

Run:
```bash
git rev-parse HEAD
git status --porcelain=v1
uname -a
gcc --version | head -1
python3 --version
cd CHAOS/gem5 && scons --version | head -2
sha256sum build/ARM/gem5.opt 2>/dev/null || echo "worktree build absent"
```
Expected: real values recorded in `environment.md`; no fabricated values.

- [x] **Step 2: Quarantine pre-existing artifacts**

Run:
```bash
mkdir -p docs/gem5-fi/lsu/implementation_v3_2/preexisting_rejected
cp -a /home/sdc/gem5-fi-ding/docs/gem5-fi/lsu/implementation_v3_2/platform \
      docs/gem5-fi/lsu/implementation_v3_2/preexisting_rejected/
# repeat for pilots, baselines, workloads, patches if present
```
Write `preexisting_rejected/README.md` stating the two audit defects and that none of these artifacts are accepted.

- [x] **Step 3: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/environment.md \
        docs/gem5-fi/lsu/implementation_v3_2/preexisting_rejected
git commit -m "[LSU][V3.2][ENV] isolate v3.2 worktree and quarantine rejected artifacts"
git push origin lsu-platform-v3.2
```

### Task 2: Strict Excel config parser

**Files:**
- Rewrite: `docs/gem5-fi/lsu/implementation_v3_2/platform/config_parser.py`
- Test: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_config_parser.py`

**Interfaces:**
- Produces: `load_config(path: Path, *, require_complete: bool = True) -> dict`; raises `ConfigError` with every validation error; returns `{"source","models","samples","validation"}`.
- Produces: `normalize_sample(row: dict) -> dict` with keys `model_id, run_id, sub_task_id, sample_run_id, seed, fault_location, target_field, target_bit, normal_value, fault_value, injection_mode, injection_timing, fault_duration, target_instruction, target_event, event_ordinal, workload_path, binary_sha256, oracle, warmup, roi, output_dir, fault_config_id, context_difference_rule`.

- [x] **Step 1: Write failing tests**

```python
def test_real_excel_has_60_samples_12_models_5_each():
    cfg = load_config(EXCEL, require_complete=False)
    assert len(cfg["samples"]) == 60
    assert len(cfg["models"]) == 12
    assert all(v == 5 for v in Counter(s["model_id"] for s in cfg["samples"]).values())

def test_absent_workload_is_reported_not_defaulted():
    cfg = load_config(EXCEL, require_complete=False)
    absent = [s for s in cfg["samples"] if s["workload_path"] == "ABSENT"]
    assert absent
    with pytest.raises(ConfigError) as e:
        load_config(EXCEL, require_complete=True)
    assert any(s["sample_run_id"] in str(e.value) for s in absent)

def test_duplicate_seed_rejected():
    rows = [make_row(sample="S-R01", seed=1), make_row(sample="S-R02", seed=1)]
    with pytest.raises(ConfigError, match="duplicate Seed"):
        validate_samples(rows)

def test_parent_mismatch_rejected():
    with pytest.raises(ConfigError, match="parent mismatch"):
        validate_samples([make_row(sample="A01-F0-W1-S02-R01", sub="A01-F0-W1-S01")])
```

- [x] **Step 2: Run tests to verify RED**

Run: `cd docs/gem5-fi/lsu/implementation_v3_2/platform && python3 -m pytest tests/test_config_parser.py -v`
Expected: FAIL (`load_config` / `validate_samples` missing or incomplete).

- [x] **Step 3: Implement**

Read sheet `5.60个样本执行矩阵`; require all 30 columns; normalize every row; validate 60/12/5, unique IDs/seeds, parent prefixes, mode ∈ {F0,F5,F6}, `Seed` int > 0, `WorkloadPath` existence when not `ABSENT`, and binary SHA when provided. Collect all errors, sort by SampleRunID, raise one `ConfigError`. No defaults.

- [x] **Step 4: Run GREEN and save parser output**

Run:
```bash
python3 -m pytest tests/test_config_parser.py -v
python3 config_parser.py <excel> ../../logs/config_v31.json; echo "exit=$?"
```
Expected: all tests PASS; exit=2 while 45 `ABSENT` rows remain, with all 45 IDs listed.

- [x] **Step 5: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/platform/config_parser.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_config_parser.py
git commit -m "[LSU][V3.2][PLATFORM] strict Excel config parser with no defaulted seeds/paths"
git push origin lsu-platform-v3.2
```

### Task 3: Run manifest and oracle interface

**Files:**
- Rewrite: `docs/gem5-fi/lsu/implementation_v3_2/platform/manifest.py`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/platform/oracle.py`
- Test: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_manifest_oracle.py`

- [x] **Step 1: Write failing tests**

```python
def test_manifest_uses_excel_seed_and_hashes_binary(tmp_path):
    m = build_manifest(cfg, "A01-F0-W1-S01-R01", gem5, cfg_script)
    assert m["seed"] == 2108120075
    assert m["seed_source"].startswith("excel:")
    assert len(m["gem5"]["binary_sha256"]) == 64

def test_manifest_rejects_absent_workload(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_manifest(cfg, "LQ04-F0-W2-S01-R01", gem5, cfg_script)

def test_oracle_pass_fail_missing(tmp_path):
    assert check_oracle("728e604ffcec539d", "x checksum=0x728e604ffcec539d\n")["status"] == "PASS"
    assert check_oracle("728e604ffcec539d", "x checksum=0x0000000000000000\n")["status"] == "FAIL"
    assert check_oracle("728e604ffcec539d", "no checksum\n")["status"] == "MISSING"
```

- [x] **Step 2: RED then implement then GREEN**

Run: `python3 -m pytest tests/test_manifest_oracle.py -v`
Implement `build_manifest` (resolve sample, reject `ABSENT`/missing/hash mismatch, include command + env + output dir + canonical `manifest_sha256`) and `check_oracle` (last `checksum=0x...` line). Re-run to GREEN.

- [x] **Step 3: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/platform/manifest.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/oracle.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_manifest_oracle.py
git commit -m "[LSU][V3.2][PLATFORM] run manifest from frozen Excel and oracle checker"
git push origin lsu-platform-v3.2
```

### Task 4: F0/F5/F6 fault manager

**Files:**
- Rewrite: `docs/gem5-fi/lsu/implementation_v3_2/platform/fault_manager.py`
- Test: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_fault_manager.py`

**Interfaces:**
- `FaultManager(mode, warmup_events=0, span_events=1, max_faults=1, rng_seed=1, target_event=None, event_ordinal=0)`
- `on_eligible(is_target=True, value_changed=True) -> bool`
- `on_f6_event(event_name, is_target=True) -> bool`
- `summary() -> dict` with `attempted, eligible, injected, value_changed, nochange, trigger_events, spent`.

- [x] **Step 1: Write failing tests**

```python
def test_f0_fires_exactly_once():
    fm = FaultManager("F0", max_faults=1, rng_seed=7)
    assert sum(fm.on_eligible() for _ in range(100)) == 1

def test_f5_applies_to_every_post_warmup_eligible():
    fm = FaultManager("F5", warmup_events=2, max_faults=0)
    assert [fm.on_eligible() for _ in range(6)] == [False, False, True, True, True, True]

def test_f5_counts_nochange_as_applied():
    fm = FaultManager("F5", max_faults=0)
    fm.on_eligible(value_changed=False)
    s = fm.summary()
    assert s["injected"] == 1 and s["nochange"] == 1

def test_f6_requires_named_trigger_then_once():
    fm = FaultManager("F6", target_event="store_load_forward")
    assert fm.on_eligible() is False
    assert fm.on_f6_event("tlb_hit") is False
    assert fm.on_f6_event("store_load_forward") is True
    assert fm.on_f6_event("store_load_forward") is False
```

- [x] **Step 2: RED → implement → GREEN**

Run: `python3 -m pytest tests/test_fault_manager.py -v`

- [x] **Step 3: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/platform/fault_manager.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_fault_manager.py
git commit -m "[LSU][V3.2][PLATFORM] explicit F0/F5/F6 state machines with nochange accounting"
git push origin lsu-platform-v3.2
```

### Task 5: Trace v3.1 schema, writer, validator, completeness, summary

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_Trace_Schema_v3.2.json`
- Rewrite: `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_writer.py`
- Rewrite: `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_validator.py`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_completeness.py`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/platform/trace_summary.py`
- Test: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_trace.py`

**Interfaces:**
- `TraceWriter(path, sample_run_id, run_id, sub_task_id, fault_id, fault_model_id)`
- `event(event_type, **fields) -> int` writes every schema field (null when unknown)
- `edge(source_event_id, destination_event_id, **fields) -> int` writes a separate `propagation_edge` record and rejects unknown endpoints
- `validate(path) -> list[str]`; `check_completeness(path) -> dict`; `summarize(path) -> dict`

- [x] **Step 1: Write failing tests**

```python
REQUIRED = {"dyn_inst_seq","execution_attempt_id","replay_generation","commit_seq",
            "fault_id","sample_run_id","injection_event_id","fault_model_id",
            "event_id","parent_event_id","propagation_edge_id","source_event_id",
            "destination_event_id","producer_inst_seq","consumer_inst_seq",
            "request_id","response_id","fragment_id","va","pa","lq_entry_id",
            "sq_entry_id","entry_generation","old_value","new_value",
            "injection_status","activation_status","commit_status","squash_status",
            "terminal_state","trace_completeness"}

def test_writer_emits_every_v31_field(tmp_path):
    p = tmp_path/"t.jsonl"; w = TraceWriter(p, "S-R01", "R", "S", "F1", "A01")
    eid = w.event("injection", unit="AGU", dyn_inst_seq=10, old_value="0x1000", new_value="0x1008")
    rec = json.loads(p.read_text().splitlines()[0])
    assert REQUIRED <= rec.keys() and rec["event_id"] == eid

def test_orphan_edge_rejected(tmp_path):
    w = TraceWriter(tmp_path/"t.jsonl", "S-R01", "R", "S", "F1", "A01")
    with pytest.raises(ValueError):
        w.edge(1, 2)

def test_incomplete_trace_never_masked(tmp_path):
    p = tmp_path/"t.jsonl"; w = TraceWriter(p, "S-R01", "R", "S", "F1", "A01")
    w.event("injection", dyn_inst_seq=1)
    w.close(run_status="COMPLETED", activation="TRIGGERED", terminal="MASKED", completeness="INCOMPLETE")
    rep = check_completeness(p)
    assert rep["trace_completeness"] == "INCOMPLETE"
    assert rep["terminal_state"] != "MASKED"
```

- [x] **Step 2: RED → implement → GREEN**

Write the JSON Schema (draft-07, `$defs.event/edge/summary`) and the stdlib validator. Validator must reject missing required keys, bad enums, duplicate event IDs, and edges whose endpoints are absent. Completeness reports missing injection/terminal/summary and downgrades `MASKED` to `HANG` only when a hang is evidenced; otherwise it reports `INCOMPLETE` with reasons and `terminal_state="CRASH"` only for simulator errors. Summary counts events/edges/terminal states.

Run: `python3 -m pytest tests/test_trace.py -v`

- [x] **Step 3: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/LSU_Trace_Schema_v3.2.json \
        docs/gem5-fi/lsu/implementation_v3_2/platform/trace_*.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_trace.py
git commit -m "[LSU][V3.2][TRACE] Trace v3.1 JSONL schema, writer, validator, completeness, summary"
git push origin lsu-platform-v3.2
```

### Task 6: Terminal classification

**Files:**
- Rewrite: `docs/gem5-fi/lsu/implementation_v3_2/platform/terminal.py`
- Test: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_terminal.py`

- [x] **Step 1: Write failing tests**

```python
def test_four_dimensions_are_independent():
    r = classify(timed_out=False, simulator_error=False, exit_code=0, eligible=3,
                 injected=1, oracle_match=True, trace_complete=True,
                 squashed=False, detected=False, arch_state_bad=False)
    assert r == {"run_status":"COMPLETED","fault_activation_status":"TRIGGERED",
                 "terminal_state":"MASKED","trace_completeness":"COMPLETE"}

def test_no_eligible_keeps_not_triggered():
    r = classify(timed_out=False, simulator_error=False, exit_code=0, eligible=0,
                 injected=0, oracle_match=None, trace_complete=True)
    assert r["run_status"] == "NO_ELIGIBLE_EVENT"
    assert r["fault_activation_status"] == "NOT_TRIGGERED"

def test_incomplete_trace_is_never_masked():
    r = classify(timed_out=False, simulator_error=False, exit_code=0, eligible=3,
                 injected=1, oracle_match=True, trace_complete=False)
    assert r["terminal_state"] != "MASKED"
    assert r["trace_completeness"] == "INCOMPLETE"
```

- [x] **Step 2: RED → implement → GREEN; commit**

Run: `python3 -m pytest tests/test_terminal.py -v`

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/platform/terminal.py \
        docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_terminal.py
git commit -m "[LSU][V3.2][PLATFORM] independent RunStatus/Activation/Terminal/Completeness"
git push origin lsu-platform-v3.2
```

### Task 7: Gate 1 verification package

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/logs/gate1_tests.log`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/logs/gate1_config_validation.log`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_Implementation_Status_v3.2.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_gate1.sh`

- [x] **Step 1: Run the whole Gate 1 suite and capture stdout/stderr**

```bash
cd docs/gem5-fi/lsu/implementation_v3_2/platform
python3 -m unittest discover -s tests -v 2>&1 | tee ../logs/gate1_tests.log
python3 config_parser.py <excel> ../logs/config_v31.json 2>&1 | tee ../logs/gate1_config_validation.log
```
Expected: all unit tests pass; config validation exits 2 with exactly the missing workload IDs listed.

- [x] **Step 2: Write status with real counts and known gaps**

The status file must state: Gate 1 PASS/FAIL per component, the 45 `ABSENT` rows, and that Gate 2 is not yet accepted. No predicted values.

- [x] **Step 3: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/logs docs/gem5-fi/lsu/implementation_v3_2/LSU_Implementation_Status_v3.2.md \
        docs/gem5-fi/lsu/implementation_v3_2/platform/run_gate1.sh
git commit -m "[LSU][V3.2][GATE1] verified common-base test and config-validation logs"
git push origin lsu-platform-v3.2
```

---

## Gate 2 — Workloads and Pilots

### Task 8: W1/W4 recovery and W2/W3/W5/W7 packaging

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/workloads/{agu_addrmodes,sq_forward,lq_lifetime,sq_drain,load_response,replay_dependency}.c`
- Create: per workload `compile.sh`, `run.sh`, `<name>.golden`, `oracle_check.py` (shared copy)
- Create: `docs/gem5-fi/lsu/implementation_v3_2/workloads/SHA256SUMS.txt`

- [x] **Step 1: Recover W1/W4 sources and verify existing binary hashes**

`agu_addrmodes` SHA must equal `90a190...b49b`; `sq_forward` SHA must equal `132a84...f297`. If a rebuilt binary differs, record the rebuild provenance and do not overwrite the original binary without a `_rebuilt` suffix.

- [x] **Step 2: Compile all six with the documented command and run each host-side**

```bash
gcc -O2 -static -o <name> <name>.c
./<name> | tee <name>.host.out
```
Compare to the frozen golden; record exit code and SHA.

- [x] **Step 3: Run each under gem5 with the current commit and save the full baseline bundle**

```bash
build/ARM/gem5.opt --outdir=... configs/se/lsu_proxy.py --cmd=<bin> --cpu O3 --variant B0
```
Save command, gem5 version, git commit, gcc version, `config.ini`, `stats.txt`, stdout, stderr, exit code, `Exiting @ tick`, binary SHA, oracle result.

- [x] **Step 4: Prove the target microarchitectural event**

Use `--debug-flags=LSQUnit` (forwarding / store completion / replay) and a diagnostic counter; grep the debug log for the concrete event and store the excerpt in `baselines/<name>/event_proof.log`.

- [x] **Step 5: Commit per workload group**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/workloads docs/gem5-fi/lsu/implementation_v3_2/baselines
git commit -m "[LSU][V3.2][W1-W7] package sources, binaries, goldens, gem5 baselines and event proofs"
git push origin lsu-platform-v3.2
```

### Task 9: Fix W6 store_path and W8 alignment OOB

**Files:**
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/workloads/store_path.c`
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/workloads/alignment.c`
- Preserve: `docs/gem5-fi/lsu/implementation_v3_2/workloads/_original_v31/{store_path.c,alignment.c}`

- [x] **Step 1: Write the failing address-sanitizer baselines**

Compile the original sources with `-fsanitize=address,undefined` and run:
```bash
gcc -O1 -g -fsanitize=address,undefined -static -o /tmp/store_path_asan store_path.c && /tmp/store_path_asan
gcc -O1 -g -fsanitize=address,undefined -static -o /tmp/alignment_asan alignment.c && /tmp/alignment_asan
```
Expected: ASan/UBSan reports the tail OOB for both.

- [x] **Step 2: Fix the sources**

`store_path.c`: rewrite the four store-width regions as non-overlapping in-bounds ranges; use `memcpy` for every unaligned width store; assert `sizeof(a)==32768`; last 8-byte write ends at `&a[32768]`.
`alignment.c`: reduce the unaligned loop bound so the last 4-byte `memcpy` ends at `&a[4096]`; keep the subsequent read in bounds.

- [x] **Step 3: Recompile, regenerate golden, recompute SHA, rerun baseline**

```bash
gcc -O2 -static -o store_path store_path.c && ./store_path > store_path.golden
gcc -O2 -static -o alignment alignment.c && ./alignment > alignment.golden
sha256sum store_path alignment > SHA256SUMS.txt
```
Run both under gem5 and save new baseline bundles. Old binaries/goldens stay under `_original_v31/` and are not valid post-fix baselines.

- [x] **Step 4: Commit**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2/workloads docs/gem5-fi/lsu/implementation_v3_2/baselines
git commit -m "[LSU][V3.2][W6-W8] fix tail OOB and unaligned overlapping stores; regenerate baselines"
git push origin lsu-platform-v3.2
```

### Task 10: A01 F0 hook at pushRequest

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{hh,cc,py}`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq.cc` (pass `inst->seqNum` to the PRE hook)
- Modify: `configs/se/lsu_proxy.py` (add `a01_bit3_load` to `--agu_pre_mode` choices)
- Test: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/` unit test or host-side Python harness

- [x] **Step 1: Add `a01_bit3_load`**

At `maybeCorruptPre`, before the trigger decision: reject `!isLoad`; after trigger fire, apply `addr ^= 0x8`; record `old_addr/new_addr/dyn_seq`; count `nochange` if unchanged. F0 uses `lsuTier=F0`, `maxFaults=1`; exactly one eligible load fires.

- [x] **Step 2: Build clean**

```bash
cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt 2>&1 | tee ../../logs/build_a01.log
```
Expected: zero new warnings/errors. Copy `gem5.opt` to repo-root `build/ARM/gem5.opt` only if the build is clean.

- [x] **Step 3: Run baseline + pilot on W1**

Baseline must match golden. Pilot command includes `--agu_pre_mode a01_bit3_load --addrpath_lsu_tier F0 --addrpath_max_faults 1 --addrpath_rng_seed 2108120075 --chaos_propagation`.

- [x] **Step 4: Verify real evidence**

- `addrpath_injections.log` has exactly one `Site: lsq_pushRequest_PRE` line with `new_addr == old_addr ^ 0x8`.
- propagated trace includes `inj`, `addr_form`, `mem_req`, `resp`, `taint_reg`, `consumer`/`errant_commit` or an honest stop.
- oracle result recorded; exit code recorded.
- Convert CSV to JSONL via `tools/prop_trace_to_v31.py`; validator returns VALID; completeness result recorded.

- [x] **Step 5: Commit**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSAddrPath CHAOS/gem5/src/cpu/o3/lsq.cc configs/se/lsu_proxy.py \
        docs/gem5-fi/lsu/implementation_v3_2/pilots/A01F0 docs/gem5-fi/lsu/implementation_v3_2/logs/build_a01.log
git commit -m "[LSU][V3.2][A01] real pushRequest bit3 Load-only F0 hook and pilot evidence"
git push origin lsu-platform-v3.2
```

### Task 11: A03 F5 hook

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{hh,cc,py}`
- Modify: `configs/se/lsu_proxy.py`

- [x] **Step 1: Add `a03_bit3_stuck0_load`**

Load-only; every post-warmup eligible load gets `addr &= ~0x8`; count the condition as applied even when the bit was already 0; log `nochange` for those. F5 uses `--addrpath_lsu_tier F5 --addrpath_max_faults 0`.

- [x] **Step 2: Build, baseline, pilot**

Same procedure as Task 10 with seed `663646247`; verify `injected > 0`, `nochange` reported honestly, and at least one downstream event when a corrupted address is consumed.

- [x] **Step 3: Commit**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSAddrPath configs/se/lsu_proxy.py \
        docs/gem5-fi/lsu/implementation_v3_2/pilots/A03F5 docs/gem5-fi/lsu/implementation_v3_2/logs/build_a03.log
git commit -m "[LSU][V3.2][A03] load-only bit3 stuck-at-0 F5 reapplication with nochange accounting"
git push origin lsu-platform-v3.2
```

### Task 12: FW02 F6 forwarding false-miss hook

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.{hh,cc,py}`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` (full-coverage decision point)
- Modify: `configs/se/lsu_proxy.py`

- [x] **Step 1: Add `f6_fw02` mode and `maybeSuppressForwarding`**

Method receives `(load_seq, store_seq, vaddr, size)`, fires exactly once when a real full-coverage older store is present (the F6 trigger), logs the trigger pair, and returns true so `lsq_unit.cc` skips the forward branch and falls through to a memory access. F6 state must not fire without a real store-load pair.

- [x] **Step 2: Build, baseline, pilot on W4**

Baseline must match `1f4cbf14327717df`. Pilot includes `--chaos_lsqfwd --lsqfwd_struct_mode f6_fw02 --lsqfwd_lsu_tier F6` plus the Excel seed `2941542370`.

- [x] **Step 3: Verify real evidence**

- `CHAOS_LSU_F6_EVENTS`/injection log shows `SqForward` observed and exactly one suppression with the load/store seq pair.
- The target Load executes (trace has its seq) and, if the memory value differs, the oracle changes; if not, record `no_effect` honestly.
- JSONL validator/completeness output saved.

- [x] **Step 4: Commit**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd CHAOS/gem5/src/cpu/o3/lsq_unit.cc configs/se/lsu_proxy.py \
        docs/gem5-fi/lsu/implementation_v3_2/pilots/FW02F6 docs/gem5-fi/lsu/implementation_v3_2/logs/build_fw02.log
git commit -m "[LSU][V3.2][FW02] F6 conditional forwarding false-miss with real store-load trigger"
git push origin lsu-platform-v3.2
```

### Task 13: Gate 2 acceptance package

**Files:**
- Create: `docs/gem5-fi/lsu/implementation_v3_2/pilots/GATE2_REPORT.md`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_Pilot_Results_v3.2.zip`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_Baseline_Results_v3.2.zip`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_Workload_Package_v3.2.zip`
- Create: `docs/gem5-fi/lsu/implementation_v3_2/LSU_Build_and_Run_Logs_v3.2.zip`

- [x] **Step 1: Verify all eight baselines and all three pilots from saved artifacts**

Run the validator/completeness/oracle checks again from disk; quote exit codes. No pilot may be marked PASS if `injected==0` or the trigger was absent.

- [x] **Step 2: Package deliverables with SHA256SUMS**

- [x] **Step 3: Commit and push**

```bash
git add docs/gem5-fi/lsu/implementation_v3_2
git commit -m "[LSU][V3.2][GATE2] verified workload baselines and A01/A03/FW02 pilot package"
git push origin lsu-platform-v3.2
```

---

## Deferred Until After Gate 2

- Gate 3 (remaining nine models LQ04, SQ01, SQ03, LP01, SP05, FW05, MD04, RP01, DA04) gets a follow-up plan addendum after Gate 2 evidence is accepted.
- Gate 4 (60 formal samples) starts only after Gate 1-3 pass and the researcher confirms.
- Excel v3.2 repair is a separate patch after Gate 2 because workload paths/goldens must exist first.

## Self-Review

- Spec coverage: Gate 1 covers config parser, manifest, FaultManager, Trace schema/writer/validator/completeness/summary, oracle, TerminalState, unit tests. Gate 2 covers W1-W8 and the three pilots. Remaining gates are explicitly deferred, not silently dropped.
- Placeholder scan: every task names exact files, commands, and expected outcomes; no "TBD".
- Type consistency: `load_config`, `build_manifest`, `FaultManager`, `TraceWriter`, `validate`, `check_completeness`, `classify` names are used consistently across tasks.
- Review Focus items each have a test in Tasks 2, 4, 5, 6, 9.
