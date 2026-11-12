# LSU v3.3.3 — One-Pass Final Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Turn the 12-model / 60-context LSU fault-injection study from `PARTIALLY_READY` into a reproducible, causally-complete `READY_FOR_FORMAL_EXPERIMENT` design on one final binary.

**Architecture:** Fix the three root-cause source defects first (PRE-hook retry injection, A03 persistent-fault observation, SP05 store-data binding), harden the runner/control/classification tooling, build once, re-census the two affected models, rerun the 60 fault + 60 matched control pairs on that single binary, regenerate all tables and the final workbook from authoritative SampleRunID/Seed values, then run a fresh independent acceptance. No formal campaign is started.

**Tech Stack:** gem5 v25.1.0.1 (vendored, C++/SCons), ARM SE O3 proxy (`configs/se/lsu_proxy.py`, B0), Python 3 tooling (`tools/lsu_v332_*.py`, `platform/run_pilot.py`, `terminal_rules.py`), openpyxl, pytest.

**Spec:** `audit_v3_3_3/README_GROUND_TRUTH.md` + the six Phase-1 reports in `audit_v3_3_3/reports/` (A–F). The frozen identity source is `docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv` and `gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.7.xlsx`.

## Global Constraints

- Scope is fixed: A01, A03, FW02, FW05, SQ01, SQ03, SP05, DA04, LP01, MD04, LQ04, RP01; R01–R05 = 10/30/50/70/90 percentiles of the model's own eligible-event ROI.
- Authoritative `SampleRunID` and `Seed` are immutable; never invent, hash-substitute, merge or delete them. The frozen workbook is never overwritten.
- `EventOrdinal` in the v3.3.3 workbook is the measured percentile ordinal; the frozen matrix's `EventOrdinal` 1–5 is design metadata (its own provenance text says the C++ tiers select by seed, not ordinal). Both columns must be carried, clearly separated.
- One patch per defect unit = one commit. No `git add -A`; stage explicit paths. Push each verified commit to the feature branch `lsu-v3.3.1-context-workload-20261111` (never `main`).
- Exactly one integrated gem5 build (`scons` in `CHAOS/gem5`, install to repo-root `build/ARM/gem5.opt`). Every run in the final matrix must carry that binary's SHA256.
- gem5 hard cap 4 concurrent processes. Keep ≥20 GiB free on `/home`.
- Honesty: report `n/a`, never a silent zero; never relabel a terminal to make a gate pass; never patch a CSV to hide a source defect.
- No formal campaign start. Ready Gate is the deliverable.

## Review Focus

1. **PRE-hook retries** — a `pushRequest` re-entry with `inst->translationStarted()` is not a new dynamic event; counting it as eligible injects into a discarded by-value copy. The fix must exclude it and re-census A01/A03, not reuse the old ordinals.
2. **A03 post-oracle hang** — all five fault runs already print a divergent final checksum. The watchdog/terminal path must preserve that oracle verdict as SDC and must not silently turn it into HANG.
3. **Control mount semantics** — `--probability 0.0` must actually disable every injector; MD04's separate `--md04_probability` (default 1.0) and DA04/LQ04/RP01's missing global gate are latent misfires.
4. **Chain-scoped propagation** — Activation/Downstream/Consumer evidence must be on the fault's own ptag/seq and must include the real consumer fan-out; an injection-only chain is not `COMPLETE`.
5. **Frozen identity** — 30 candidate contexts reuse frozen SampleRunID/Seed with a different ELF; the workbook must state the workload override explicitly without changing the IDs or seeds.

---

### Task 0: Freeze the diagnosis artifacts and the one-shot decision packet

**Files:**
- Create: `audit_v3_3_3/LSU_v3.3.3_Master_Defect_Ledger.csv`
- Create: `audit_v3_3_3/LSU_v3.3.3_Consolidated_Repair_Plan.md`
- Create: `audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md`
- Keep: `audit_v3_3_3/README_GROUND_TRUTH.md`, `audit_v3_3_3/reports/Agent_{A..F}_*.md`

**Interfaces:**
- Produces: the IssueID namespace (`L-A01`…, `L-B01`…, `L-C01`…, `L-D01`…) used by every later task and by the workbook's Readiness sheet.

- [x] **Step 1: Write the ledger**

Every row has `IssueID,ModelID,ContextID,Category,RootCause,Evidence,AffectedFiles,AffectedContexts,ProposedFix,Validation,ApprovalRequired,RegressionRisk,FinalStatus`. Categories: A code/hook, B workload/context, C trace/propagation/oracle, D Excel/seed/control/binary/runner. Merge symptoms of one root cause.

- [x] **Step 2: Write the consolidated repair plan**

For each IssueID answer: (1) root cause, (2) why it survived earlier rounds, (3) correct source layer, (4) affected models/contexts, (5) does it change fault semantics, (6) rebuild required, (7) which pilots to rerun, (8) one-shot validation, (9) researcher approval needed.

- [x] **Step 3: Write the decision packet**

Cover FW02 W4-v2, RP01 `replay_partial_v332`, MD04 `md04_violations_v332`, SQ01/SQ03/SP05 `sq_reload_v3212`, the SQ03 MASKED/visibility label, the A01/A03 PRE-retry fix + ordinal re-census, the A03 SDC/post-oracle-hang classification, the A01-R02 SQUASHED qualifier, and the config freeze (Warm-up=0, measured ROI, final binary). Each item: original problem, candidate evidence, semantics, five-context feasibility, chain closure, golden/oracle, impact on SampleRunID/Seed/Excel, recommendation, risk.

- [x] **Step 4: Verify the artifacts are internally consistent**

Run:
```bash
python3 - <<'EOF'
import csv
rows=list(csv.DictReader(open('audit_v3_3_3/LSU_v3.3.3_Master_Defect_Ledger.csv')))
assert rows, 'empty ledger'
assert len({r['IssueID'] for r in rows})==len(rows), 'duplicate IssueID'
print('ledger rows',len(rows),'unique IDs OK')
EOF
```
Expected: `ledger rows <N> unique IDs OK`.

- [x] **Step 5: Commit the diagnosis artifacts**

```bash
git add audit_v3_3_3/README_GROUND_TRUTH.md audit_v3_3_3/reports audit_v3_3_3/LSU_v3.3.3_Master_Defect_Ledger.csv audit_v3_3_3/LSU_v3.3.3_Consolidated_Repair_Plan.md audit_v3_3_3/LSU_v3.3.3_Researcher_Decision_Packet.md docs/superpowers/plans/2026-11-12-lsu-v333-final-closure.md
git commit -m "[LSU][V3.3.3][DIAG] complete A-F diagnosis, defect ledger and repair plan"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 1: Researcher approval gate

**Files:** none (decision record goes into `audit_v3_3_3/decisions/`).

**Interfaces:**
- Produces: `audit_v3_3_3/decisions/LSU_v3.3.3_Researcher_Approval.md` recording ADOPT/CONDITIONAL/REJECT per workload and approval of the A01/A03 fix + config freeze.

- [x] **Step 1: Ask once**, with the packet as the evidence. Do not ask per-model questions.
- [x] **Step 2: Record the answer verbatim** in the decisions file, including any conditions.
- [x] **Step 3: If a workload is rejected**, stop that model's context freeze and report it; continue all approval-independent work (Tasks 3–6).
- [x] **Step 4: Commit the decision record** (explicit path, feature branch).

---

### Task 2: PRE-hook retry eligibility fix (A01/A03 root cause)

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/lsq.cc` (PRE hook block at the top of `LSQ::pushRequest`, around the `if (cpu->chaosAddrPathPre)` block and the later `if (inst->translationStarted())` reuse branch)
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{hh,cc}` (add a retry-skip counter/last-verdict for provenance)
- Test: a post-build count-only/fault run (no unit-test framework for this hook)

**Interfaces:**
- Consumes: `DynInstPtr inst` (`translationStarted()`, `seqNum`, `pcState().instAddr()`), `CHAOSAddrPathPre::maybeCorruptPre`.
- Produces: one eligible event per unique dynamic instruction; no `a01_ea_discarded` records caused by `saved_request_reuse`.

- [x] **Step 1: Write the failing static assertion**

Add to `tools/lsu_v332_supplement.py` (or a small checker) a function `assert_pre_retry_guard()` that greps `lsq.cc` for the guard `if (cpu->chaosAddrPathPre && !inst->translationStarted())`. Run it; expected `AssertionError` before the edit.

- [x] **Step 2: Implement the guard**

Wrap the PRE block:
```cpp
if (cpu->chaosAddrPathPre && !inst->translationStarted()) {
    ... existing maybeCorruptPre / registerInjection / noteA01EA ...
}
```
Keep the A03/A01 staging exactly as-is for the first pass. On the retry branch, increment `obs_pre_retry_skipped` (new counter) and emit one `CHAOS_L0_DECLINE: pre_retry_skipped=N` line at exit; never fabricate an injection.

- [x] **Step 3: Static verification**

Run the checker; expected PASS. Run `grep -n "translationStarted()" CHAOS/gem5/src/cpu/o3/lsq.cc` and confirm the PRE block is before the request-reuse branch and guarded.

- [x] **Step 4: Build once (deferred to Task 7) and run the targeted A01 test**

On the new binary, run A01 at one context (count-only or fault) and assert:
```bash
grep -c "a01_ea_discarded" <outdir>/trace_v31.jsonl   # expected 0
grep -c "register_writeback" <outdir>/trace_v31.jsonl # expected >=1 for a fault run
```
Also assert the A01 control still prints golden `728e604ffcec539d`.

- [x] **Step 5: Commit (after Task 7 build verification)**

```bash
git add CHAOS/gem5/src/cpu/o3/lsq.cc CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc tools/lsu_v332_supplement.py
git commit -m "[LSU][V3.3.3][A01] exclude translation retries from the PRE eligible stream"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 3: A03 in-simulator watchdog, lifecycle and honest count

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py` (add `watchdogCycles = Param.UInt64(0, ...)`)
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh` (add `EventFunctionWrapper *a03_watchdog_event`, `a03Watchdog()`, `watchdog_cycles`)
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc` (schedule at activation, emit lifecycle + funnel, graceful `exitSimLoop`; parse/emit `A03_WATCHDOG_EXPIRED`)
- Modify: `configs/se/lsu_proxy.py` (add `--addrpath_watchdog_cycles`, pass to `CHAOSAddrPath`)
- Modify: `tools/lsu_v332_matrix.py` (A03 parser: real injected count from the last `FUNNEL`/`A03_STREAM` rows; cap kept separate; terminal from stdout checksum + watchdog marker)

**Interfaces:**
- Consumes: `chaos_a03::streamEvent`, `activationDetail`, `lifecycleDetail`, `writeA03LogLine`, `notifyFunnelAtInjection`.
- Produces: `A03_WATCHDOG_EXPIRED` marker, `A03_STUCK_LIFECYCLE` line, `a03_injected_applications` count, terminal `SDC/POST_ORACLE_SIM_HANG` or `HANG_WATCHDOG`.

- [x] **Step 1: Add the parameter**

In `CHAOSAddrPath.py`:
```python
watchdogCycles = Param.UInt64(0,
    "A03: in-simulator watchdog clock cycles after activation (0 = disabled)")
```
In `lsu_proxy.py`, `--addrpath_watchdog_cycles` default 0; pass `watchdogCycles=args.addrpath_watchdog_cycles` in the `CHAOSAddrPath(...)` construction.

- [x] **Step 2: Schedule the watchdog at activation**

In `a03NoteEligibleLoad`, after `a03_stream_rec.activate(act)` succeeds:
```cpp
if (watchdog_cycles && !a03_watchdog_event) {
    a03_watchdog_event = new EventFunctionWrapper(
        [this]() { this->a03Watchdog(); }, "A03 watchdog", true);
    schedule(a03_watchdog_event, clockEdge(Cycles(watchdog_cycles)));
}
```

- [x] **Step 3: Implement `a03Watchdog()`**

Emit `A03_STUCK_LIFECYCLE` (via `a03_stream_rec.lifecycle(...)`), the final `CHAOS_L0_DECLINE`/funnel lines, then `A03_WATCHDOG_EXPIRED: tick=... activated=1 stream_rows=...`, flush the addrpath log, and call `exitSimLoop("CHAOS_A03_WATCHDOG_EXPIRED", 0)` so exit callbacks (and the gzip trailer) run. Do not use `fatal` here; the runner classifies the marker.

- [x] **Step 4: Fix the A03 parser in `tools/lsu_v332_matrix.py`**

`parse_addrpath_log` must report:
- `stream_rows` = count of `A03_STREAM:` rows,
- `injected_applications` = last `FUNNEL: ... injected=N` (fallback: count of `affected=1` rows),
- `capped` = presence of `A03_LOG_CAPPED` (separate from the count),
- `watchdog_expired` = presence of `A03_WATCHDOG_EXPIRED`.
Write these into `summary.json.a03` and never use the log-cap line as `injection_count`.

- [x] **Step 5: A03 oracle parser**

Accept the workload's bare 16-hex final line (no `0x`, no `checksum=`); compare to golden `728e604ffcec539d`. If present and different → `oracle=FAIL`, `terminal=SDC`, `qualifier=POST_ORACLE_SIM_HANG` (when the watchdog fired); if absent → `terminal=HANG_WATCHDOG`. If `A03_LOG_CAPPED` is set but the checksum is present, keep `capped=true` as a logging fact, not a terminal.

- [x] **Step 6: Static verification**

```bash
grep -n "watchdogCycles\|a03Watchdog\|A03_WATCHDOG_EXPIRED" CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{py,hh,cc}
python3 -m py_compile tools/lsu_v332_matrix.py
```
Expected: all symbols found; compile OK.

- [x] **Step 7: Commit (after Task 7 build verification)**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc configs/se/lsu_proxy.py tools/lsu_v332_matrix.py
git commit -m "[LSU][V3.3.3][A03] add an in-simulator watchdog and honest application count"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 4: SP05 store-data binding, write-skipped event and commit tick

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh` (`noteSP05Injection` gains `const uint8_t *store_data, unsigned data_len, Tick commit_tick`)
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc` (compute FNV-1a into `FaultStoreEntry.data_fnv`; emit `sp05_write_skipped`; set `store_commit_tick`)
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` (SP05 branch passes `storeWBIt->data()`, `request->_size`, and the store's commit tick)

**Interfaces:**
- Consumes: `storeWBIt->data()`, `request->_size`, `inst->sqIdx`, `inst->sqEntryGeneration`, `curTick()`.
- Produces: `sp05_stage;store_data_fnv=<16hex>;data_correct=0;stage_outcome=CHAIN_VISIBILITY_LOST` plus an `sp05_write_skipped` node.

- [x] **Step 1: Write the failing test**

Add `test_sp05_store_data_is_recorded` to `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_prop_converter.py` that parses a synthetic `sp05_stage` line and asserts a 16-hex `store_data_fnv` and `data_correct=0`/`CHAIN_VISIBILITY_LOST`. Run `pytest ... -k sp05_store_data -v`; expected FAIL before the change.

- [x] **Step 2: Extend the API and record the hash**

Use the existing `fnv1a64`/hex helper. In `noteSP05Injection`, when `store_data && data_len`, set `fe.data_fnv = hex(fnv1a64(store_data, data_len))` and `fe.data_hex`; set `fe.store_commit_tick = commit_tick`. Emit a chain node `sp05_write_skipped` with `write_skipped=1;mem_sent=0`.

- [x] **Step 3: Pass the real bytes at the call site**

In the SP05 branch of `lsq_unit.cc`, pass `storeWBIt->data()` and `request->_size`; derive `commit_tick` from the SQ entry/instruction commit state (if unavailable, pass `curTick()` and record `commit_tick_source=injection_bound` rather than 0).

- [x] **Step 4: Verification**

```bash
pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_prop_converter.py -k sp05_store_data -v
```
Expected: PASS. After Task 7, one SP05 run must show `store_data_fnv=<16hex>`, `data_correct=0`, `stage_outcome=CHAIN_VISIBILITY_LOST`, and a `sp05_write_skipped` record; the reload hash must equal the zero-word hash `a8c7f832281a39c5`.

- [x] **Step 5: Commit (after Task 7 build verification)**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc CHAOS/gem5/src/cpu/o3/lsq_unit.cc docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_prop_converter.py
git commit -m "[LSU][V3.3.3][SP05] bind the skipped store data and emit the early anomaly"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 5: Runner, control and classification hardening

**Files:**
- Modify: `configs/se/lsu_proxy.py` (MD04 `md04_probability` follows `--probability` unless explicitly overridden; add a global mount gate for DA04/LQ04/RP01/SQ01/SQ03/SP05; disable watchdogs when probability<=0)
- Modify: `tools/lsu_v332_matrix.py` (control classification from `command.txt`; seed/terminal/workload fields; RP01 watchdog parse from `lsq_fwd_injections.log`; A03 count; distinct CSV paths; file lock; dry-run RP01)
- Modify: `tools/lsu_v332_report.py` (control classification; A03 terminal; `FaultCommand`; `Rank_k`; A03 seed)
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py` (RP01 support; injector mount/attach/gate fields; manifest/oracle for direct runs)
- Modify: `docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py` (`a01_ea_discarded` → `INJECTION_NOT_ACTIVATED`; SP05 qualifier; RP01 raw fatal map)

**Interfaces:**
- Consumes: `command.txt`, `summary.json`, `pilot_meta.json`, `lsq_fwd_injections.log`, `stdout.log`.
- Produces: `ControlZeroProof` ∈ {INJECTOR_ABSENT, MOUNTED_BUT_DISABLED, MOUNTED_BUT_SUPPRESSED}; non-null `seed`, `terminal`, `workload`, `fault_command`; `MT-*.csv` distinct outputs.

- [x] **Step 1: Write failing unit tests**

In `tests/test_lsu_v333_control.py` add:
```python
def test_control_classification_counts():
    # parse the 60 v3.3.2 command.txt files
    counts = classify_controls(RUNS)
    assert counts == {"INJECTOR_ABSENT": 25,
                      "MOUNTED_BUT_DISABLED": 35,
                      "MOUNTED_BUT_SUPPRESSED": 0}
```
and `test_md04_probability_default_follows_global()`; `test_a03_bare_hex_oracle()`; `test_rp01_watchdog_from_log()`. Run them; expected FAIL.

- [x] **Step 2: Implement the classification helpers**

Read the executed `command.txt` (not the run_pilot argv); treat `--chaos_lsqfwd`, `--chaos_addrpath`, `--chaos_l1dfwd`, `--chaos_lq04`, `--chaos_md04` as mounts; `probability==0.0` → `MOUNTED_BUT_DISABLED`; explicit suppression → `MOUNTED_BUT_SUPPRESSED`; no mount → `INJECTOR_ABSENT`. Keep a per-run `mount_evidence` field.

- [x] **Step 3: Harden MD04/DA04/LQ04/RP01/SQ01/SQ03/SP05 controls**

MD04: `md04_probability = args.probability if args.md04_probability is None else args.md04_probability`, default `None`. Add an `enabled` gate in each injector consulted before any injection; `probability<=0` must short-circuit before watchdog scheduling and before any log open. Keep fault semantics unchanged.

- [x] **Step 4: Fix the parsers and fields**

A03: bare-hex checksum; real injected count; cap separate. RP01: watchdog marker from `lsq_fwd_injections.log`, `terminal=HANG_WATCHDOG`, `watchdog=internal`, `deadline_cycles`, `no_checksum`. Seed/terminal/workload/fault_command populated from `pilot_meta`/command. Separate matrix/report CSV paths (`..._RAW.csv`, `..._FINAL.csv`). Add a file lock.

- [x] **Step 5: Verification**

```bash
pytest tests/test_lsu_v333_control.py -v
python3 tools/lsu_v332_matrix.py --models all --roles fault,control --dry-run | tail -5
```
Expected: all tests PASS; dry-run prints commands for all 12 models incl. RP01, no writes.

- [x] **Step 6: Commit**

```bash
git add configs/se/lsu_proxy.py tools/lsu_v332_matrix.py tools/lsu_v332_report.py docs/gem5-fi/lsu/implementation_v3_2/platform/run_pilot.py docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py tests/test_lsu_v333_control.py
git commit -m "[LSU][V3.3.3][RUNNER] harden controls, parsers and provenance fields"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 6: Chain-scoped propagation and causal-table generator

**Files:**
- Create: `tools/lsu_v333_propagation.py` (or extend `tools/lsu_v332_report.py`)
- Modify: `tools/lsu_v332_report.py` (fault/control rows)
- Test: `tests/test_lsu_v333_propagation.py`

**Interfaces:**
- Consumes: `trace_v31.jsonl`, `prop_trace.csv.gz`, model logs, `summary.json`.
- Produces: 60-row `LSU_60Context_Causal_Propagation.csv` with per-stage evidence paths, chain-closure verdict, terminal reason, and masking mechanism.

- [x] **Step 1: Write failing tests for the known corrections**

```python
def test_a03_is_sdc_not_hang(): ...
def test_a01_r03_is_injection_not_activated(): ...
def test_rp01_activation_is_target_ordinal(): ...
def test_a01_r02_squash_is_unrelated_but_valid(): ...
```
Run; expected FAIL on the v3.3.2 inputs.

- [x] **Step 2: Implement chain scoping**

Chain = injection ptag plus the fault instruction's `dyn_inst_seq`; downstream/consumer edges must include different-seq `consumer_commit`/`errant_commit` records bound to the chain ptag, not only same-seq events. `Activation` must be the target ordinal/activation record, never the tautology `injection seq=N`. Carry PC, VA/PA, SQ/LQ entry, generation, tick, and the model-record mechanism.

- [x] **Step 3: Terminal adjudication**

Use `terminal_rules.py` plus explicit model rules:
- A01-R03: `INJECTION_NOT_ACTIVATED` / `NO_EFFECTIVE_INJECTION` (discard reason).
- A01-R02: `SQUASHED` with `squash_cause=unrelated; fault_caused=0` and a note that the faulty instruction did not enter architectural state.
- A03: `SDC` / `ORACLE_FAIL` with `POST_ORACLE_SIM_HANG` when the checksum is present and the watchdog fired; otherwise `HANG_WATCHDOG`.
- SQ03: `MASKED` / `VISIBILITY_TIMING_SHIFT`, with 4/5 moved + 1/5 lifecycle-only.
- SP05: `SDC` with `store_data_fnv` now present; otherwise `RELOAD_UNVERIFIABLE`.
- LQ04/MD04-R01: `MASKED` with the measured mechanism (not a generic label).
- FW02-R03: `MASKED` with `normal_decision=forwarded; fault_decision=suppressed; replay_count=0`.

- [x] **Step 4: Trace completeness**

`COMPLETE` requires injection + activation + divergence + (consumer or terminal-type witness) + commit/squash/hang evidence; an injection-only chain is `INCOMPLETE`. Never let `COMPLETE` pass on structure alone.

- [x] **Step 5: Verification**

```bash
pytest tests/test_lsu_v333_propagation.py -v
python3 tools/lsu_v333_propagation.py --runs audit_v3_3_2/runs --out /tmp/causal.csv
python3 - <<'EOF'
import csv
r=list(csv.DictReader(open('/tmp/causal.csv')))
assert len(r)==60
from collections import Counter
print(Counter(x['Terminal'] for x in r))
EOF
```
Expected: tests PASS; 60 rows; A03 shows SDC 5 on the v3.3.2 inputs once the checksum parser is used.

- [x] **Step 6: Commit**

```bash
git add tools/lsu_v333_propagation.py tools/lsu_v332_report.py tests/test_lsu_v333_propagation.py
git commit -m "[LSU][V3.3.3][PROP] chain-scoped propagation and honest terminal adjudication"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 7: Single unified build and provenance

**Files:**
- Create: `audit_v3_3_3/build/v333_build.log`
- Create: `audit_v3_3_3/build/PROVENANCE.md`
- Create: `audit_v3_3_3/build/BINARY_SHA256.txt`
- Copy: `audit_v3_3_3/binary/gem5.opt.v333-<sha>` + sidecar

**Interfaces:**
- Produces: `GIT_HEAD`, `SOURCE_DIFF_SHA`, `BINARY_SHA256`, `CONFIG_SHA`, `ELF_SHA` map for every later table.

- [x] **Step 1: Check the diff and freeze HEAD**

```bash
git status --short
git diff --stat
git rev-parse HEAD
```
Expected: only the planned files changed; no unrelated files staged.

- [x] **Step 2: Build once**

```bash
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt 2>&1 | tee /home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12/audit_v3_3_3/build/v333_build.log
```
(If the host OOMs or the build is clean-from-scratch, use `-j16`; do not abort during the slow configure phase.) Expected: `scons: done building targets.` and `grep -c "error:"` = 0.

- [x] **Step 3: Install and hash**

```bash
cp CHAOS/gem5/build/ARM/gem5.opt build/ARM/gem5.opt
sha256sum build/ARM/gem5.opt | tee audit_v3_3_3/build/BINARY_SHA256.txt
sha256sum configs/se/lsu_proxy.py
for f in workloads/directed/sq_forward_w4v2 workloads/directed/replay_partial_v332 workloads/directed/md04_violations_v332 docs/gem5-fi/lsu/implementation_v3_2/workloads/{agu_addrmodes,fw05_forward,sq_reload_v3212,alignment,load_response,lq_lifetime_ordinal}; do sha256sum "$f"; done
```
Expected: binary SHA recorded; all ELF SHAs recorded.

- [x] **Step 4: Verify source/binary consistency**

```bash
git diff --stat HEAD -- CHAOS/gem5/src
```
Expected: empty (the built source equals HEAD after the fix commits). If not, commit the source first.

- [x] **Step 5: Write PROVENANCE.md**

`Git HEAD → build log → binary SHA → config SHA → workload SHA` in one table, with the exact build command and timestamp.

- [x] **Step 6: Commit**

```bash
git add audit_v3_3_3/build audit_v3_3_3/binary
git commit -m "[LSU][V3.3.3][BUILD] record the single final build and provenance"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 8: Re-census A01/A03 and rerun the 60 fault + 60 control matrix

**Files:**
- Create: `audit_v3_3_3/roi/LSU_60Context_ROI_Percentile_Mapping.csv`
- Create: `audit_v3_3_3/roi/LSU_60Context_Distinctness_Audit.csv`
- Create: `audit_v3_3_3/runs/<MODEL>-R<NN>-{fault,control}/`
- Create: `audit_v3_3_3/controls/MT_RAW.csv`, `MT_FINAL.csv`

**Interfaces:**
- Consumes: the Task-7 binary and SHA.
- Produces: 120 run dirs, all carrying the Task-7 SHA; the 60-context mapping.

- [ ] **Step 1: Re-census A01/A03**

Run a count-only sweep on the new binary for A01 (F0, span) and A03 (F5, count-only) over the main-loop eligible stream. Record ROI start/end/N, verify `N=end-start+1`, and compute `start + ceil(p*N) − 1`. Do not reuse the old 1040–1234 window if the retry exclusion changed it. Write the new mapping with the frozen SampleRunID/Seed unchanged.

- [ ] **Step 2: Verify all other models' ROI is unchanged**

Compare the new and old eligible counts for FW02/FW05/SQ/DA04/LP01/MD04/LQ04/RP01; where the hook did not change, reuse the measured ROI but re-run on the new binary.

- [ ] **Step 3: Run the 120 pairs**

```bash
python3 tools/lsu_v332_matrix.py --models all --roles fault,control --jobs 4
```
(Use the hardened driver from Task 5; never exceed 4 concurrent gem5 processes.) Expected: 120 summaries, all with the Task-7 binary SHA; every fault injects; every control injects 0.

- [ ] **Step 4: Verify the matrix**

```bash
python3 - <<'EOF'
import json,glob
from collections import Counter
c=Counter(); bad=[]
for p in glob.glob('audit_v3_3_3/runs/*/summary.json'):
    d=json.load(open(p))
    role=p.split('-')[-2]
    n=d.get('injection_count')
    if role=='fault' and (n or 0)<=0: bad.append((p,'fault-zero'))
    if role=='control' and (n or 0)!=0: bad.append((p,'control-nonzero'))
    c[d.get('binary_sha')]+=1
print(c); print('bad',bad[:10],len(bad))
EOF
```
Expected: one SHA across 120 runs; `bad 0`.

- [ ] **Step 5: Commit the runs and mapping**

Stage the new `audit_v3_3_3/runs`, `roi`, `controls` explicitly; do not touch `audit_v3_3_2/`.

```bash
git add audit_v3_3_3/runs audit_v3_3_3/roi audit_v3_3_3/controls
git commit -m "[LSU][V3.3.3][RESULTS] 60-context fault/control matrix on the final binary"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 9: Final Excel and required CSV deliverables

**Files:**
- Create: `audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx`
- Create: `tools/lsu_v333_workbook.py`
- Create: `audit_v3_3_3/LSU_60Context_Final_Readiness.csv`
- Create: `audit_v3_3_3/LSU_60Context_Causal_Propagation.csv`
- Create: `audit_v3_3_3/LSU_Fault_Control_Final_Audit.csv`
- Create: `audit_v3_3_3/LSU_12Model_Workload_Oracle_Audit.csv`

**Interfaces:**
- Consumes: authoritative `60_SAMPLE_MATRIX.csv`/v3.2.7 workbook for SampleRunID/Seed; Task-8 results for measured ordinals/terminals.
- Produces: 8 sheets with no blank PASS fields; `Readiness_Gate` per model/context.

- [ ] **Step 1: Build the workbook with openpyxl**

Sheets: `Model_Design`, `Fault_Sample_Manifest`, `Control_Manifest`, `ROI_Context_Mapping`, `Causal_Propagation`, `Workload_Oracle`, `Binary_Config`, `Readiness_Gate`. Never overwrite the v3.2.7 workbook. Verify W6/W8 `ExpectedGolden` (v3.2.7 already carries the correct `2543a2a60de01795`/`3f89eab79392ce69`) and add the six candidate workload rows (including `sq_reload_v3212`).

- [ ] **Step 2: Preserve identity and add the executed ordinal**

For each of the 60 rows, carry the frozen `SampleRunID`, `Seed`, `FaultModelID`, `ContextDifferenceRule`, and add `Executed_EventOrdinal`, `ROI_Start`, `ROI_N`, `Percentile`, `EligibleEventOrdinal`, `DynInstSeq`, `PC`, `VA/PA`, `InstructionType`, `LQ/SQEntry`, `DynamicState`, `InjectionEligibility`. The frozen `EventOrdinal` 1–5 stays as `Design_EventOrdinal`.

- [ ] **Step 3: Cross-check**

```bash
python3 - <<'EOF'
import openpyxl,csv
wb=openpyxl.load_workbook('audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx',data_only=True)
frozen=list(csv.DictReader(open('docs/gem5-fi/lsu/implementation_v3_2/excel/60_SAMPLE_MATRIX.csv')))
# assert 60 IDs/seeds match 1:1 and no PASS row has a blank critical field
EOF
```
Expected: 60/60 IDs/seeds match; 0 blank critical PASS fields.

- [ ] **Step 4: Commit**

```bash
git add tools/lsu_v333_workbook.py audit_v3_3_3/gem5-fi-LSU-Formal-Experiment-Design-v3.3.3.xlsx audit_v3_3_3/LSU_60Context_Final_Readiness.csv audit_v3_3_3/LSU_60Context_Causal_Propagation.csv audit_v3_3_3/LSU_Fault_Control_Final_Audit.csv audit_v3_3_3/LSU_12Model_Workload_Oracle_Audit.csv
git commit -m "[LSU][V3.3.3][EXCEL] publish the formal experiment design workbook and audit CSVs"
git push origin lsu-v3.3.1-context-workload-20261111
```

---

### Task 10: Regression, independent acceptance and Ready package

**Files:**
- Create: `audit_v3_3_3/reports/Agent_F_Final_Independent_Acceptance.md`
- Create: `audit_v3_3_3/LSU_v3.3.3_Final_Acceptance_Report.md`
- Create: `audit_v3_3_3/LSU_Independent_Acceptance.md`
- Create: `audit_v3_3_3/LSU_Final_Binary_Provenance.md`
- Create: `audit_v3_3_3/LSU_Final_Source_Diff.patch`
- Create: `LSU_v3.3.3_Formal_Experiment_Ready_Package.zip` (+ `.sha256`)

**Interfaces:**
- Consumes: all prior tasks.
- Produces: the final verdict (only `READY_FOR_FORMAL_EXPERIMENT`, `PARTIALLY_READY`, or `NOT_READY`) and the package.

- [ ] **Step 1: Regression**

```bash
pytest tests/ -q
pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests -q
```
Expected: the prior 180 + 120 pass (or a documented, justified change). Capture the real output in the report.

- [ ] **Step 2: Runner dry-run and readiness checks**

```bash
python3 tools/lsu_v332_matrix.py --models all --roles fault,control --dry-run
```
Then check the 60-context eligibility matrix, 60 control zero proofs, and 12-model smoke (one fault/control each).

- [ ] **Step 3: Fresh independent Agent F**

Dispatch a NEW general-purpose agent (not one of A–E) with read-only scope and the Ready Gate table; it must verify raw artifacts, not the summaries, and may return `NOT_READY`.

- [ ] **Step 4: Assemble the 14 package items**

1 Final_Acceptance_Report, 2 Master_Defect_Ledger, 3 Consolidated_Repair_Plan, 4 Researcher_Decision_Packet, 5 workbook, 6 60Context_Final_Readiness, 7 Causal_Propagation, 8 Fault_Control_Final_Audit, 9 Workload_Oracle_Audit, 10 Final_Binary_Provenance, 11 Final_Source_Diff.patch, 12 Independent_Acceptance, 13 raw pilot traces/logs/oracles/tests, 14 exact commands and runner config.

- [ ] **Step 5: Zip and verify**

```bash
zip -r LSU_v3.3.3_Formal_Experiment_Ready_Package.zip <items>
unzip -t LSU_v3.3.3_Formal_Experiment_Ready_Package.zip
sha256sum LSU_v3.3.3_Formal_Experiment_Ready_Package.zip | tee LSU_v3.3.3_Formal_Experiment_Ready_Package.zip.sha256
```
Expected: `No errors detected`; SHA recorded.

- [ ] **Step 6: Final commit and push**

```bash
git add <explicit package paths>
git commit -m "[LSU][V3.3.3][PACKAGE] publish the formal experiment ready package"
git push origin lsu-v3.3.1-context-workload-20261111
```

- [ ] **Step 7: Stop**

Do not start the formal campaign. Report the verdict and, if READY, the exact campaign command, task mapping, resources and estimated runtime; wait for explicit authorization.
