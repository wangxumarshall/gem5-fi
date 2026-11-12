# Agent B — Fault Activation & Microarchitectural State (LSU v3.3.3 closure round)

**Date:** 2026-11-11
**Scope:** A01 (R01–R05), A03 (R01–R05), plus the shared LSU injection-hook machinery they depend on
(`CHAOSAddrPath`, `CHAOSPropagation`, `lsq.cc`, `CHAOSLSQFwd` trigger/watchdog templates).
**Mode:** Read-only audit. No source/config/workload/tool/Excel edits. No gem5 run. Only this report was written.

## Provenance

| Item | Value | How verified |
|---|---|---|
| Worktree | `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12` | `pwd` |
| Git HEAD | `3097ad82e7066f18fc35cf64dcb612a05c1fc021` | `git rev-parse HEAD` |
| Binary | `build/ARM/gem5.opt` | `sha256sum build/ARM/gem5.opt` → `070d68a688464fa737e6bf102f44a27e911dc29d15142d77c82ec2083115f5ca` (matches README_GROUND_TRUTH §1) |
| Source-equivalent HEAD | `fc608224...` per ground truth (HEAD adds results commits) | ground truth §1 |

**Files inspected (all absolute):**
- `audit_v3_3_2/runs/A01-R03-fault/{trace_v31.jsonl,summary.json,pilot_meta.json,addrpath_injections.log,oracle.log,stdout.log,stderr.log,manifest.json,prop_trace.csv.gz}`
- `audit_v3_3_2/runs/A01-{R01,R02,R04,R05}-fault/…` (chain comparison)
- `audit_v3_3_2/runs/A01-R03-control/…` and `A03-{R01..R05}-control/…`
- `audit_v3_3_2/runs/A03-{R01..R05}-fault/{addrpath_injections.log,summary.json,stdout.log,prop_trace.csv.gz}`
- `CHAOS/gem5/src/cpu/o3/lsq.cc`, `lsq.hh`
- `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/{CHAOSAddrPath.cc,CHAOSAddrPath.hh,CHAOSAddrPath.py,a01_coords.hh,a03_stream.hh}`
- `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/{CHAOSPropagation.cc,CHAOSPropagation.hh}`
- `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh`, `chaos_trigger.hh`
- `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.{cc,hh,py}`
- `docs/gem5-fi/lsu/implementation_v3_2/platform/{run_pilot.py,terminal_rules.py,tools/prop_trace_to_v31.py}`
- `tools/lsu_v332_matrix.py`
- `audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv`, `audit_v3_3_2/LSU_60Context_Final_Readiness_Matrix.csv`

---

## 1. A01-R03 — no register-writeback divergence

### 1.1 Raw evidence

`audit_v3_3_2/runs/A01-R03-fault/trace_v31.jsonl` has 6,707 JSONL rows. Event-type census (python3 read-only parse):

```
    3420  lq_lifecycle
    3266  sq_lifecycle
       7  forwarding_decision
       5  propagation_edge
       1  funnel
       1  injection
       1  address_formed
       1  a01_ea
       1  a01_ea_discarded
       1  a01_golden_resp
       1  memory_response
       1  commit
       1  (summary record, no event_type)
```

The fault's own 9-event chain (ptag=1, dyn_inst_seq=14049) is:

```
injection            eid=5414  seq=14049 old=0x493040 new=0x493048
address_formed       eid=5415  va=0x493048
a01_ea               eid=5416  golden_ea=493040 actual_ea=493048 pc=4006a8 bit=3
a01_ea_discarded     eid=5417  ...applied_to_request=0;discard_reason=saved_request_reuse
a01_golden_resp      eid=5425  golden_ea=493040 pa=0x78040 request_tick=15540910 response_tick=16302440
memory_response      eid=5426  pa=0x78040 data_fnv=a80414c2fc53631a execution_attempt_id=2
commit               eid=5427  commit_seq=6578 execution_attempt_id=2 COMMITTED
```

Raw line (event_id 5417) from the trace:

```
{"event_type":"a01_ea_discarded", "event_id":5417, "dyn_inst_seq":14049,
 "detail":"fault_id=1;dyn_inst_seq=14049;pc=4006a8;golden_ea=493040;actual_ea=493048;
           xor_delta=8;bit=3;access_size=16;affected=1;request_va=493048;
           fault_va=NOT_APPLICABLE;applied_to_request=0;discard_reason=saved_request_reuse"}
```

`addrpath_injections.log`:
```
A01_EA: fault_id=1;dyn_inst_seq=14049;pc=4006a8;golden_ea=493040;actual_ea=493048;xor_delta=8;bit=3;access_size=16;affected=1;request_va=493048;fault_va=NOT_APPLICABLE
FUNNEL: attempted=2242 eligible=1137 injected=1
Tick: 16301670, Site: lsq_pushRequest_PRE, mode=a01_bit3_load, old_addr=0x493040, new_addr=0x493048, ...
```

**No `register_writeback`, `consumer_commit`, `errant_commit`, `a01_consumed`, or `taint_value_mismatch` event exists.** The two events that are unique to R03 among A01 contexts are `a01_ea_discarded` and `a01_golden_resp`.

Control comparison (same ordinal, same simulated instruction):
`audit_v3_3_2/runs/A01-R03-control/prop_trace.csv.gz` contains exactly one `probe` node:
```
5412,16301670,0,probe,14049,,493040,,,site=lsq_pushRequest_PRE;family=a01_control;
     is_load=1;size=16;addr=493040;injected=0;control_only=1
```
The control selects the **same** dynamic instruction (seq 14049, addr 493040) as the fault run, so the F0 ordinal space is consistent between fault and control. The control's `summary.json` reports `exit_code=0, injection_count=0, oracle=true, trace COMPLETE`.

### 1.2 Comparison with R01/R02/R04/R05 — what evidence R03 lacks and why

| Ctx | inj seq | attempt | chain after `a01_ea` | terminal |
|---|---|---|---|---|
| R01 | 12978 | 1 | `memory_request(va=0x493008)` → `memory_response(pa=0x78008)` → `register_writeback` → `commit` → `errant_commit` → `a01_consumed` | SDC (oracle FAIL) |
| R02 | 13638 | 1 | `memory_request(va=0x493ff0)` → `squash(reason=lsq_squash, fault_caused=0)` | SQUASHED (oracle PASS) |
| R03 | 14049 | **2** | **`a01_ea_discarded(applied_to_request=0)`** → `a01_golden_resp(golden_ea=493040)` → `memory_response(pa=0x78040)` → `commit` | UNRESOLVED (oracle PASS) |
| R04 | 14719 | 1 | `memory_request` → `memory_response` → `register_writeback` → `commit` → `errant_commit` → `a01_consumed` | SDC |
| R05 | 15086 | 1 | same as R04 | SDC |

The writeback observer is **not missing**. In R01/R04/R05 the generic chain-writeback emitter produces a `taint_reg` node with `writeback_value/phys_reg/arch_reg/source_event_id` (`CHAOSPropagation.cc:1484` `noteChainWriteback`, node written at ~`:1640-1670`), and the converter maps `taint_reg → register_writeback` (`docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py:37 KIND_MAP`, `:56 "taint_reg": "register_writeback"`). R03 has no node to emit because **no corrupted request ever existed**.

### 1.3 Root cause (source-level)

1. `LSQ::pushRequest` entry calls the PRE hook **unconditionally**:
   `CHAOS/gem5/src/cpu/o3/lsq.cc:781-784`
   ```cpp
   if (cpu->chaosAddrPathPre) {
       const Addr pre_old_addr = addr;
       size = cpu->chaosAddrPathPre->maybeCorruptPre(addr, size, isLoad, ...);
   ```
   `maybeCorruptPre` (`CHAOSAddrPath.cc:243-294`) calls `lsuTrigger->onAttempt()` / `onEligible()` and then applies the bit flip to the **by-value `addr`** (`:385-399` for a01/a03). It never checks `inst->translationStarted()`.

2. Later in the same function the request is taken from the **saved request** when translation already started:
   `CHAOS/gem5/src/cpu/o3/lsq.cc:857-859`
   ```cpp
   if (inst->translationStarted()) {
       request = inst->savedRequest;
       assert(request);
   } else { ... new SingleDataRequest(..., addr, size, ...) ... }
   ```
   The faulted `addr` is therefore dead: nothing downstream consumes it.

3. The hook itself knows this and records it as `a01_ea_discarded` (`CHAOSProgress.cc:2066-2085`, `lsq.cc:808-819`). The source comment names it explicitly: *"the PRE hook injected, but this pushRequest took the savedRequest reuse branch … the injected EA never reached a Request — no memory chain at the actual EA can exist … (the SUPP-A01-R03 silent-absence root cause)"*.

4. Timing proof that the fault could not reach memory: the reused request was sent at `request_tick=15540910`, while the injection tick is `16301670` — the request was already in flight **760,760 ticks before** the injection (`a01_golden_resp` detail `request_tick=15540910`; `addrpath_injections.log` `Tick: 16301670`). The response `response_tick=16302440` (770 ticks after injection) is the golden-EA response.

Thus the exact missing binding is **not a trace observer**: it is the binding from the injected by-value EA to the `Request` actually used. On a `translationStarted()` retry there is none; the injection is a no-effect application.

### 1.4 Is this a legitimate MASKED? — proof: no

A legitimate MASKED requires (a) the fault applied to the real data path, and (b) the architectural outcome unaffected (e.g. overwritten, squashed-and-replayed correctly). R03 fails (a):

- `applied_to_request=0` (event 5417) — the corrupted EA never entered a `Request`.
- The golden-EA response is the *only* response for seq 14049 (`memory_response` pa=0x78040, `a01_golden_resp` golden_ea=493040). There is no response at the injected EA (493048 / its PA).
- The request predates the injection by 760,760 ticks (above).

This is a **fault-injection coverage / activation defect**, not a downstream mask. It must **not** be relabeled MASKED. Classification should remain non-architectural but be made explicit as `NO_EFFECTIVE_INJECTION` (currently `UNRESOLVED / UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE`, from `terminal_rules.py:59-83`).

### 1.5 Proposed minimal source-level fix

**Preferred (semantic fix):** make the F0/F5 eligible-event space exclude saved-request-reuse retries, i.e. only true EA-formation events consume an ordinal.

- File: `CHAOS/gem5/src/cpu/o3/lsq.cc`, function `LSQ::pushRequest`, line 781.
  ```cpp
  // was: if (cpu->chaosAddrPathPre) {
  if (cpu->chaosAddrPathPre && !inst->translationStarted()) {
  ```
  (or pass `inst->translationStarted()` into `maybeCorruptPre` and `return size;` **before** `lsuTrigger->onAttempt()/onEligible()`; both give identical semantics.)
- Effect: every retry/`savedRequest`-reuse `pushRequest` stops counting as an eligible event and stops injecting. `a01_ea_discarded` becomes structurally unreachable for the PRE family.
- Event emission point stays `CHAOSPropagation::noteA01EA` / `noteA01EADiscarded`; no new event type is required. Existing fields (`dyn_inst_seq`, `ptag`/chain id, `pc`, `golden_ea`, `actual_ea`, `request_va`) are already complete for the real-formation case (verified in R01/R04/R05).

**Alternative (minimal, does NOT fix the ordinal space):** leave the counter alone but re-target the rejected ordinal to the next non-reuse event; this is semantically the same as the preferred fix and is not simpler.

**Do not** mutate `inst->savedRequest`'s vaddr at the reuse branch: translation is already complete/in-flight and the PA is fixed, so a vaddr-only mutation would desynchronise VA/PA rather than fault the access (not validated in this phase; see "Could not verify").

**Ordinal re-freeze is mandatory:** excluding reuse events removes events from the eligible stream, so the k-th eligible event changes for every ordinal-derived A-model sample. The A01 and A03 R01–R05 ordinals (1059/1098/1137/1176/1215), and any other PRE-family ordinal sample (A04/A05/A06/A08/L01/L02/S04–S07/S11/S13), must be re-derived from the corrected stream and re-frozen.

**Validation command (requires rebuild + approval):**
```bash
cd CHAOS/gem5 && scons -j126 build/ARM/gem5.opt
# rerun A01-R03 with identical args (command.txt)
build/ARM/gem5.opt --outdir=/tmp/a01r03_fix configs/se/lsu_proxy.py \
  --cmd=docs/gem5-fi/lsu/implementation_v3_2/workloads/agu_addrmodes --cpu O3 --variant B0 \
  --probability 1.0 --chaos_propagation --prop_trace_file prop_trace.csv.gz --chaos_addrpath \
  --agu_pre_mode a01_bit3_load --addrpath_lsu_tier F0 --addrpath_max_faults 1 \
  --addrpath_warmup_events 0 --addrpath_span_events 10 --addrpath_rng_seed 1302709433 \
  --addrpath_event_ordinal <re-derived ordinal>
```
Acceptance: the `injection` event's `dyn_inst_seq` has `execution_attempt_id == 1` on its response/commit, a `memory_request`/`memory_response` at the injected EA, and either `register_writeback` + `errant_commit` (SDC) or `squash` (SQUASHED). Also rerun all five A01 contexts and one non-A01 PRE-family regression (canonical regression) and confirm `exit: pass`, 0 SIGSEGV.

- **Approval required:** Y (changes eligible-event semantics and every ordinal sample).
- **Regression risk:** HIGH for ordinal-position dependence (all PRE-family samples shift); LOW for fault semantics on non-reuse events (the XOR/mask lines are unchanged). Full A01/A03 re-pilot required.
- **Classification:** A (injection-hook defect), with a C consequence (current UNRESOLVED/MASKED reading).

### 1.6 Secondary fix — make the terminal explicit (separate unit)

`docs/gem5-fi/lsu/implementation_v3_2/platform/terminal_rules.py:59-83` decides `UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE` solely from the absence of `register_writeback`. It should detect the on-chain `a01_ea_discarded` event first and return a distinct terminal (e.g. `NO_EFFECTIVE_INJECTION`, non-architectural), so the absence is not presented as an unresolved normal run and can never be re-read as MASKED. This is a mechanism-honesty fix, not a relabel. Approval: Y (classification semantics). Class: C/D.

---

## 2. A03 — persistent stuck-at-0 fault

### 2.1 Lifecycle per context (from `addrpath_injections.log` + `prop_trace.csv.gz`)

`A03_ACTIVATION` is emitted once at the activation load (`a03_stream.hh:343-352`; second activation rejected/counted). The declared ordinal is the first trigger-fired eligible load (`chaos_lsu_trigger.hh:159-164`, `start = warmup_events + event_ordinal`).

| Ctx | declared ordinal = first activation | activation reason | golden_ea → actual_ea | first STUCK_APPLIED | rows (applications) | affected=1 | ALREADY_STUCK |
|---|---|---|---|---|---|---|---|
| R01 | 1059, seq 12978, pc 400598 | **ALREADY_STUCK** | 493000 → 493000 | **1060**, seq 12989, 493008→493000 | 113,377 | 113,266 | 111 |
| R02 | 1098, seq 13638, pc 40068c | **STUCK_APPLIED** | 493ff8 → 493ff0 | 1098 (same) | 114,673 | 114,584 | 89 |
| R03 | 1137, seq 14049, pc 4006a8 | **ALREADY_STUCK** | 493040 → 493040 | **1171**, seq 14594, 493208→493200 | 113,494 | 113,418 | 76 |
| R04 | 1176, seq 14719, pc 4006d0 | **ALREADY_STUCK** | 493230 → 493230 | **1177**, seq 14744, 493238→493230 | 115,067 | 115,027 | 40 |
| R05 | 1215, seq 15086, pc 4006d0 | **STUCK_APPLIED** | 493368 → 493360 | 1215 (same) | 114,998 | 114,978 | 20 |

**ALREADY_STUCK vs STUCK_APPLIED semantics verified in source and data.** `a03_stream.hh:74-94,145-162`: reason/affected are derived from `golden_ea != actual_ea`; `affected=0` (ALREADY_STUCK) means the mask line ran but bit 3 was already 0, so nothing changed; `affected=1` (STUCK_APPLIED) means the EA changed. Both paths are recorded exactly once. The logs match: R01 ordinal 1059 shows `old_addr=0x493000, new_addr=0x493000, value_changed=0`; R02 ordinal 1098 shows `new_addr=0x493ff0`.

**Is the declared target ordinal itself applied, or only armed?** It is **applied**, not merely armed. The trigger arms at the start position, and `onEligible()` returns true on that same event (`chaos_lsu_trigger.hh:159-164`); the mask line then executes on that load. For R01/R03/R04 the first application changes nothing (ALREADY_STUCK); the first effective change is later (1060 / 1171 / 1177). So "declared ordinal = first observation point" is correct; "declared ordinal = first changed EA" is false for 3 of 5 contexts.

### 2.2 "A03 PC=0" symptom — already fixed, not live

All five fault logs and all five prop traces were scanned for `pc=0`, `pc=0x0`, `None`:
- `addrpath_injections.log` (5 files): `pc0 count: 0` for every context; distinct PCs are real (400598, 4005c0, …, 401a04).
- `A03-R01-fault/prop_trace.csv.gz`: `a03_stream` detail `pc=…` values are all non-zero (`a03 pc0: 0`); sample `pc=4006a0, 4014e8, 4014f0`.

**Verdict: the former PC=0 symptom is fixed in the v3.3.2 binary.** It is not a live defect. (Ground-truth §6 suspicion confirmed.) Paths: `audit_v3_3_2/runs/A03-{R01..R05}-fault/addrpath_injections.log`; `audit_v3_3_2/runs/A03-R01-fault/prop_trace.csv.gz`.

### 2.3 In-simulator watchdog design (RP01 template)

**Existing RP01 template** (`CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`):
- schedule: `:210-216` `rp01_watchdog_event = new EventFunctionWrapper([this]{ this->rp01Watchdog(); }, ...); schedule(rp01_watchdog_event, cpu->clockEdge(Cycles(p.rp01WatchdogCycles)));`
- handler: `:605-623` writes `CHAOS_RP01_WATCHDOG=EXPIRED fired=… injected=… eligible=… tick=…` then `fatal("CHAOS_RP01_WATCHDOG_EXPIRED tick=%llu …")` (non-zero exit; runner classifies HANG, never MASKED).
- config: `configs/se/lsu_proxy.py:287` `--rp01_watchdog_cycles`; matrix uses `--rp01_watchdog_cycles 20000000` (`tools/lsu_v332_matrix.py:236`).

**Critical evidence for the A03 criterion:** the A03 runs are **not stalled** — the persistent fault drives the workload into a long but *committing* loop. From `A03-R01-fault/prop_trace.csv.gz`:
```
total rows 1479248, last tick 866774755
a03_stream  count=113377 first_tick=15691445  last_tick=866770520
commit      count=113248 first_tick=15913205  last_tick=866772060
last200k kinds: a03_stream 15385, commit 15385, mem_req 15385, resp 15385, taint_reg 15385 …
tail stream PCs: [('pc=401a04', 3846)]
```
Commits and streams continue to the last captured tick. Therefore a **stall-based** criterion ("no new A03_STREAM row / no commit progress for N cycles") **would never fire** on these five runs. A watchdog built only on that criterion would reproduce the current 30 s external timeout.

**Recommended design:** an *absolute post-activation cycle budget* watchdog (a MAX_TICK-style in-sim terminal), plus an optional progress watchdog as a secondary guard for genuinely stalled variants.

- New param in `CHAOSAddrPath.py`: `addrpathWatchdogCycles = Param.UInt64(0, "A03 post-activation cycle budget; 0 = disabled")`, mounted from `configs/se/lsu_proxy.py` (new `--addrpath_watchdog_cycles`).
- Members in `CHAOSAddrPath.hh`: `EventFunctionWrapper *a03_watchdog_event = nullptr;` plus observed state already present (`a03_stream_rec`, `a03_fault_id`).
- Schedule in `CHAOSAddrPath::startup()` (or at activation in `a03NoteEligibleLoad`, `CHAOSAddrPath.cc:540-610`): `schedule(a03_watchdog_event, cpu->clockEdge(Cycles(addrpath_watchdog_cycles)))` measured from the activation tick.
- Handler `a03Watchdog()`:
  1. emit `A03_WATCHDOG=EXPIRED tick=<t> activation_tick=<t0> activation_ordinal=<o> rows=<n> applied=<a> already_stuck=<b> first_affected_ordinal=<m>`;
  2. **emit `A03_STUCK_LIFECYCLE` before aborting** — today it is only in the exit callback (`CHAOSAddrPath.cc:700-709`), and `fatal()` does not run exit callbacks; all five current runs lack the line ("does not contain A03_STUCK_LIFECYCLE" — `grep -l` returned NONE);
  3. `fatal("CHAOS_A03_WATCHDOG_EXPIRED tick=%llu rows=%llu applied=%llu", …)`.
- Secondary progress guard (optional): if `a03_stream_rec.recorded()` and the commit count are unchanged for N*cycles, fatal with `CHAOS_A03_WATCHDOG_EXPIRED reason=no_progress`. This catches genuinely stalled derivations but is not sufficient alone (evidence above).
- Runner integration (`tools/lsu_v332_matrix.py`): classify `CHAOS_A03_WATCHDOG_EXPIRED` in `stdout/stderr` as terminal `HANG_WATCHDOG` and set `run_status=SIMULATOR_ERROR`-equivalent; stop using the 30 s `A03_TIMEOUT` (`tools/lsu_v332_matrix.py:77`) as the terminal basis (keep it only as a hard safety net above the in-sim budget).
- Validation: rerun one A03 context with a small budget, confirm the process exits non-zero with `CHAOS_A03_WATCHDOG_EXPIRED`, the lifecycle line contains exact `eligible_events/applications/already_stuck/activation_*`, and the runner reports `HANG_WATCHDOG` (not `HANG` from wall clock). Rebuild required (C++ param + member + handler).

### 2.4 The 20,000 cap — what it counts

`kA03PreLogCap = 20000` (`CHAOSAddrPath.hh:191-192`) bounds **per-application `Tick:` text lines** in `addrpath_injections.log`, not fault applications and not stream rows (`CHAOSAddrPath.cc:468-485`). One `A03_LOG_CAPPED` marker is written per run, e.g.:
```
A03_LOG_CAPPED: cap=20000 faults_injected=20000 tick=165742115
```
Each run has exactly one marker (`grep -c` = 1). The real application counts are the stream/trigger counts: **113,377 / 114,673 / 113,494 / 115,067 / 114,998** (tail `FUNNEL: … injected=113377`; `A03_STREAM` row counts; `summary.a03.stream_rows`).

The A03 `summary.json` `injection_count = 20000` is a **parser artifact**: `tools/lsu_v332_matrix.py:110-145` `parse_addrpath_log` sets `info["injections"] += 1` for every line containing `faults_injected:`, i.e. it counts the capped `Tick:` lines. This under-reports by ~5.7× and is the value `audit_v3_3_2/propagation/LSU_60Context_Causal_Propagation_Final.csv` carries. Fix: read the real count from `a03.stream_rows` (recorder) or the last `FUNNEL … injected=N` line; keep `capped` as a separate boolean/marker.

**Is a partial trace acceptable for the formal HANG terminal once a watchdog is added?** Only if all of the following hold: (a) the terminal is a genuine in-sim `HANG_WATCHDOG` (nonzero exit + marker), not an external wall-clock timeout; (b) the lifecycle line and exact activation/first-affected/rows/applied counts are emitted before the fatal (see §2.3); (c) the truncated `prop_trace.csv.gz` is explicitly flagged `truncated=true` and is not claimed COMPLETE. Today (a) and (b) fail and the gzip is truncated (`zlib.decompressobj(...).eof == False`, 1,479,248 complete rows before the cut), so the current A03 evidence is **not** acceptable as a formal terminal.

### 2.5 Fault ID ↔ dynamic-instruction identity

- Every `a03_stream` row binds `{event_ordinal, dyn_inst_seq, pc, golden_ea, actual_ea, bit, reason}` (`a03_stream.hh:185-200`). Verified non-zero PC in all rows.
- `ptag` binding: ALREADY_STUCK rows carry `ptag=0` (no chain; "not bound to one chain"), each STUCK_APPLIED row opens a chain with its own ptag. `A03-R01` samples: activation ptag=0 (ALREADY_STUCK); ordinal 1060 ptag=1. `A03-R02`: activation ptag=1; 89 ALREADY_STUCK rows share ptag=0.
- One fault, many observation points: `StreamRecorder` accepts exactly one activation (`a03_stream.hh:343-352`), and `a03_fault_id` is set once at activation (`CHAOSAddrPath.cc:594-600`); the per-run row count is ~113k applications of the *same* bit. This is confirmed to be one persistent fault with five contexts as activation-start positions, not five injections per run.
- The matrices already state this correctly: `Qualifier='PERSISTENT_STUCK: ONE FAULT, FIVE OBSERVATION POINTS; PARTIAL TRACE'` (readiness CSV, A03 rows).

### 2.6 Proposed fixes (A03)

| Unit | Change | Files | Class | Approval | Risk |
|---|---|---|---|---|---|
| B-03 | In-sim A03 watchdog (post-activation cycle budget + optional progress guard), lifecycle emitted before `fatal` | `CHAOSAddrPath.{py,hh,cc}`, `configs/se/lsu_proxy.py`, `tools/lsu_v332_matrix.py` | A | Y | Medium (C++ rebuild; must not change fault semantics; watchdog default 0 = disabled) |
| B-04 | Honest A03 injection count (stream_rows / last FUNNEL) instead of `faults_injected:` line count; keep `capped` separate | `tools/lsu_v332_matrix.py:110-145` | D | N (tooling-only, but rerun summaries) | Low |
| B-05 | Flag truncated `prop_trace.csv.gz`; either convert with `truncated=true` or mark A03 trace PARTIAL-ONLY (no COMPLETE claim) | `tools/lsu_v332_matrix.py`, `run_pilot.py` conversion path | C/D | N | Low |

---

## 3. Common LSU hook audit

### 3.1 Trigger semantics and event-ordinal counting

- `CHAOSAddrPath` routes F0–F6 through `ChaOSLsuTrigger` (`CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh`); constructed in `CHAOSAddrPath.cc:27-34`. It is a dedicated LSU F0–F6 engine that mirrors `chaos_trigger.hh` semantics; `chaos_trigger.hh` itself is only included by `chaos_l0.hh` and `chaos_lsu_trigger.hh` (`grep -rl`).
- Ordinal space is the **op-class-filtered eligible-event stream**: `maybeCorruptPre` applies the load/store filter before `onEligible()` (`CHAOSAddrPath.cc:269-286`), so a trigger fire the mode cannot write is not an injection. This is consistent for F0 (A01) and F5 (A03).
- Fault/control consistency: the A01 control probe uses the same F0 ordinal selection (`onControlProbe`, `chaos_lsu_trigger.hh:212-232`) and selected the same instruction (seq 14049, addr 493040) as the fault (`probe` node above). Controls suppress at the injector input: `maybeCorruptPre` returns at `probability <= 0.0f` **before** `onAttempt/onEligible` (`CHAOSAddrPath.cc:250-257`) for A03, and A01 only reads (`probeA01Control`) with `injected=0`. A01 and A03 controls all report `injection_count=0` and oracle PASS.
- No hand-rolled probability on the LSU trigger path: the `uniform_real_distribution` in `maybeCorruptPre` (`CHAOSAddrPath.cc:292-293`) is reachable only when `lsuTrigger == nullptr` (legacy `lsuTier=off`). All 60-context A01/A03 runs pass `--addrpath_lsu_tier F0/F5`, so the trigger path is used.

### 3.2 Provenance fields

- `a01_ea` detail carries `dyn_inst_seq, pc, golden_ea, actual_ea, xor_delta, bit, access_size, request_va` (`a01_coords.hh` formatter; verified in raw events).
- `memory_response` carries `pa`, `request_id`, `lq_entry_id`, `entry_generation`, `execution_attempt_id`; `register_writeback` carries `phys_reg`, `arch_reg`, `writeback_value`, `payload_fnv`, `source_event_id` (R01/R04/R05).
- `a03_stream` carries `event_ordinal, dyn_inst_seq, pc, golden_ea, actual_ea, bit, reason`; PC is real in every row.
- `a01_ea_discarded` adds `applied_to_request=0;discard_reason=saved_request_reuse`, which is exactly the missing provenance that made R03 look like a silent absence before v3.2.12.
- No fabricated PC/VA: the only "unknown" encoding is `fault_va=NOT_APPLICABLE` at formation (completed by `noteA01FaultVA` if a fault is raised), and `kPcUnknown` never appears in these runs.

### 3.3 Shared-hook defects and regression scope

1. **`translationStarted()` contamination of the PRE eligible space (B-01).** `maybeCorruptPre` is shared by the whole PRE family: `a01_bit3_load`, `a03_bit3_stuck0_load`, `a04_subst`, `a05_shift`, `a06_size`, `a08_subst`, `l01_load_addr`, `l02_load_state`, `s04_store_subst`, `s05_store_size`, `s06_store_state`, `s07_store_ptr`, `s11_store_lost`, `s13_store_addr` (`CHAOSAddrPath.cc:269-424`). Any ordinal-based sample in any of these can land on a retry and become a no-effect injection. **Regression scope: every PRE-hook ordinal model, not just A01.** A03 is only partially shielded because it applies to every eligible load (a retry is a no-op application, other loads still inject), but its stream/lifecycle counts include retries.
2. **A03 log-line cap is not an injection cap (B-04/B-05).** Affects A03 evidence aggregation, not other models.
3. **Control log starvation.** With `probability=0`, the constructor does not open `addrpath_injections.log` (`CHAOSAddrPath.cc:35-40`), so the `A01_CONTROL:` line (`CHAOSAddrPath.cc:638-640`) never reaches a log; the matched-control proof survives only as the prop-trace `probe` node. Controls are still safe (zero injections) but not self-documenting in the log. Low severity, Class C.
4. **A03 direct-run path bypasses the standard runner** (`tools/lsu_v332_matrix.py:246-260`): no trace conversion, no validator, no oracle, no completeness check; terminal is external wall clock. This is the structural reason A03 lacks trace_v31/oracle evidence. Class D.

---

## 4. Consolidated issue list

| ID | Model/Ctx | Root cause | Raw evidence | Affected files | Proposed one-shot fix | Validation | Approval | Risk | Class |
|---|---|---|---|---|---|---|---|---|---|
| **B-01** | A01-R03 (all PRE-family ordinals) | PRE hook mutates a by-value EA that is discarded on `savedRequest` reuse; eligibility/injection counted without checking `translationStarted()` | `a01_ea_discarded applied_to_request=0`; `lsq.cc:857-859`; `request_tick=15540910` < injection `16301670` | `CHAOS/gem5/src/cpu/o3/lsq.cc:781-819,857-859`; `CHAOSAddrPath.cc:243-294` | Skip PRE hook/eligibility when `inst->translationStarted()`; re-derive A-series ordinals | Rebuild + rerun A01-R03; expect `memory_request`@injected EA + `register_writeback`/`squash`, attempt=1 | Y | High (ordinal shift) | A |
| **B-02** | A01-R03 terminal | `terminal_rules.py` maps "no writeback" to UNRESOLVED; ignores `a01_ea_discarded` | `terminal_rules.py:59-83`; `summary.json terminal_state_reason=UNRESOLVED_NO_REGISTER_WRITEBACK_EVIDENCE` | `docs/.../platform/terminal_rules.py` | Return distinct `NO_EFFECTIVE_INJECTION` when `a01_ea_discarded` is on-chain | Unit test on R03 trace; must not return MASKED | Y | Low | C |
| **B-03** | A03-R01..R05 | No in-simulator watchdog; external 30 s timeout; exit callback (lifecycle line) never runs | `summary exit_code=124 terminal=HANG`; `A03_STUCK_LIFECYCLE` absent in all 5 logs; `CHAOSLSQFwd.cc:605-623` template; commits continue to last tick | `CHAOSAddrPath.{py,hh,cc}`; `configs/se/lsu_proxy.py`; `tools/lsu_v332_matrix.py` | Post-activation cycle-budget watchdog + progress guard; emit `A03_STUCK_LIFECYCLE` then `fatal("CHAOS_A03_WATCHDOG_EXPIRED")` | Rerun one context with small budget; nonzero exit + marker + lifecycle counts | Y | Medium | A |
| **B-04** | A03 all | `summary.injection_count=20000` counts capped `Tick:` lines, not applications | `A03_LOG_CAPPED: cap=20000 faults_injected=20000`; tail `FUNNEL … injected=113377`; `stream_rows=113377`; `lsu_v332_matrix.py:110-145` | `tools/lsu_v332_matrix.py` | Use stream_rows / last FUNNEL injected; keep `capped` separate | Re-parse existing logs; 20k → 113k+ | N | Low | D |
| **B-05** | A03 all | `prop_trace.csv.gz` truncated (process killed); no trace_v31, no oracle, no validation, no lifecycle | `zlib … eof=False`; 1,479,248 complete rows; no `trace_v31.jsonl`; `summary oracle` unset | `audit_v3_3_2/runs/A03-*-fault/`; `tools/lsu_v332_matrix.py:246-260` | Flag truncation; convert with `truncated=true`; require watchdog terminal before claiming HANG | Validate converted trace; assert truncated flag | N | Low | C/D |
| **B-06** | A01/A03 controls | Injector log not opened at `probability=0`, so `A01_CONTROL` line is dead; control proof only in prop trace | `CHAOSAddrPath.cc:35-40`; control dir has no `addrpath_injections.log`; control prop trace has 1 `probe` node | `CHAOSAddrPath.cc` | Open log for controls or emit control probe to a log; do not alter injection gating | Control run shows `A01_CONTROL` with `injected=0` | N | Low | C |

---

## 5. Bottom line

- **A01-R03 is not an observer gap and not a legitimate MASKED.** The injected bit-3 flip was applied to a by-value EA that `lsq.cc:857-859` discarded because `inst->translationStarted()` was true on a retry; the real request had been sent 760,760 ticks *before* the injection. The trace honestly records this (`a01_ea_discarded … applied_to_request=0;discard_reason=saved_request_reuse`) and the load served the golden EA. The `register_writeback` observer exists and fires in R01/R04/R05; R03 has nothing to observe. The defect is an over-broad eligible-event space in the shared PRE hook (`lsq.cc:781` + `CHAOSAddrPath.cc:243-294`).
- **A03 is a persistent stuck-at fault correctly lifecycle-split.** The declared ordinal is the first application point (ALREADY_STUCK in R01/R03/R04, STUCK_APPLIED in R02/R05); first effective changes are 1060/1171/1177. The 20,000 figure is a *log-line* cap, not an application count (real: ~113k–115k). The "PC=0" symptom is fixed; every observed PC is real. The current HANG terminal is an external 30 s timeout with no lifecycle line and a truncated trace; because the workload keeps committing to the end, a stall-based watchdog would not fire — an absolute post-activation cycle-budget watchdog is required.
- **Shared-hook risk:** the `translationStarted()` contamination affects every PRE-family ordinal model, not only A01/A03; B-01's fix forces a re-freeze of all PRE-family ordinals.

## 6. Could not verify

- Whether mutating `inst->savedRequest` (instead of excluding reuse events) could fault the *actual* in-flight access without breaking VA/PA consistency. The request is already translation-complete and was issued before injection, so this is not recommended, but it was not tested (no gem5 runs allowed).
- Whether the corrected ordinal stream (after B-01) yields a writeback at R03 specifically: that requires a rebuild and a re-derived ordinal, which this phase forbids. The claim that the fault *would* propagate if it reached a real request is supported by R01/R04/R05 (same model/site), not by an R03 rerun.
- The true workload checksum for A03: all five runs were killed before completion (`stdout` prints a partial value `1fd794b8489219e1`, not the golden `728e604ffcec539d`; the matrix oracle regex `checksum=0x…` does not even match the bare hash line). With an in-sim watchdog the run is still a HANG, so a full-program oracle cannot be obtained; this must be accepted as a documented HANG terminal, not a PASS.
- Whether `A03_STUCK_LIFECYCLE` would be byte-correct on a normal exit (it is only emitted in the exit callback and has never executed in these five runs).
