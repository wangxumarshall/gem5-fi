# RP01 Task 15 Evidence — v3.2.12 (five skip pilots + five matched controls)

Executed 2026-11-10/11 by the RP01 Task 15 executor (one gem5 slot, sequential
runs; `pgrep -a gem5` checked before every run; `df -h /home` 67 GiB free at
every gate). Worktree `lsu-platform-v3.2.12` @ `eec513e5`; binary pinned by
SHA in every manifest. No scons, no C++ change, no commit (files left
uncommitted for the main agent's evidence commit).

## 1. Provenance

| Item | Value |
|---|---|
| Binary | repo-root `build/ARM/gem5.opt`, SHA `68c6ce737a95747e5f35be06fea160b4f461baead2c0b4d85cf900c4d047e4e8` (the skip-mode binary; every pilot + control ran the identical binary — never mixed) |
| Workload | `replay_dependency` (frozen W7), SHA `ca15390f1a797c55074703dc3fe10d1e07f7704794a9abca96b2761c41d838f4` |
| Golden checksum | `0x59fc61c040618747` |
| Watchdog | `--rp01_watchdog_cycles 20000000` (in-sim `fatal`); external `timeout 1800` backstop |
| RP01 flags | `--chaos_lsqfwd --lsq_struct_mode rp01_skip_replay --rp01_event_ordinal <N> --rng_seed <S>` + `--chaos_propagation --prop_replay_all` |
| Preconditions | P1 binary SHA ✓; P2 `--help` shows `rp01_event_ordinal` ✓; P4 workload SHA ✓; P5 67 GiB ≥ 20 GiB ✓; P6 zero competing gem5 ✓; P7 host selector test unchanged since its green run (selector not touched) |

## 2. The bridge (Task 15 item 1)

Known gap being closed: binary `68c6ce73` prints `RP01_SKIP_REPLAY` to the
run log only — the prop trace carries the skipped load's `replay` marker
(`noteReplay` fires before the guarded call) but **no injection record**, so
the closure tool would grade `NO_INJECTION_EVENT`.

Implementation (Python-only, no rebuild): `--rp01-skip-log` on
`docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py`.
It parses the **single real** `RP01_SKIP_REPLAY` line and emits it as the
trace injection record. Nothing is fabricated — every field (ordinal,
load_seq, load_pc, lq_idx, lq_gen, store_seq, replay_gen pre/post,
in_instsToReplay pre/post, tick) is taken from the line; the record carries
the raw line, the log path and the log SHA256 as provenance and has
`source_node_id=None, ptag=0` (chain identity is the load's `dyn_inst_seq`,
shared with the call-site `replay` marker). The bridge **refuses**: a
control log (zero skip lines), multiple skip lines (RP01 is one-shot), a
line missing required fields, and a trace that already carries an injection
record (forward-compatible with a future `inj_rp01` C++ record). The CLI
additionally gained `--observed-terminal` (exposes the existing
`convert()` parameter; needed to record an external-cut run as
`observed_terminal=TIMEOUT` with trace terminal `HANG` — "TIMEOUT" is a
run_status, not a TERMINAL enum value).

Test with a synthetic log sample in the exact C++ line format:
`platform/tests/test_rp01_skip_bridge.py` (11 tests) — parse fidelity over
every field, the end-to-end closure record (bridged HANG → PROVEN, no
`NO_INJECTION_EVENT`), the truncated-HANG honest cap (RecordIntegrity
TRUNCATED → UNRESOLVED while ObservedTerminal stays HANG), the external
TIMEOUT shape (never MASKED), and the four refusals.

Real output (suitites, run after the change):

```
$ python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_rp01_skip_bridge.py -q
...........                                                             [100%]
11 passed in 0.12s

$ python3 -m pytest docs/gem5-fi/lsu/implementation_v3_2/platform/tests/ -q
........................................................................ [ 67%]
...................................                                    [100%]
107 passed in 3.43s

$ python3 -m pytest tests/test_lsu_12model_closure.py tests/test_lq04_platform.py tests/test_fault_effect_coverage.py tests/test_v328_consistency.py tests/test_run_pilot_control.py -q
......................................................................   [100%]
70 passed in 1.26s
```

Real bridged record from pilot RP01-R01 (`trace_v31.jsonl` event 25780):

```
dyn_inst_seq: 69341          timestamp: 31072965       unit/sub_unit: LSQ / partial_replay_reschedule
lq_entry_id: 9201            entry_generation: 9693    replay_generation: 1
injection_status: INJECTED   activation_status: TRIGGERED
event_ordinal: 1             store_seq: 69334           rp01_load_pc: 4199932 (0x4015fc)
source_node_id: None         ptag: 0
source_log: .../pilots_v3_2_12/RP01-R01/stdout.log
source_log_sha256: 00bd3e673cc5c42d6b823b35f8f405ff59a5eca74a0ebd6f483ff7f8b96009a9
rp01_skip_replay_line: RP01_SKIP_REPLAY ordinal=1 load_seq=69341 load_pc=4199932 lq_idx=9201 lq_gen=9693 store_seq=69334 replay_gen_pre=0 replay_gen_post=1 in_instsToReplay_pre=0 in_instsToReplay_post=0 tick=31072965
```

## 3. The five skip pilots (Task 15 item 2/3)

Every pilot produced **exactly one** `RP01_SKIP_REPLAY` line, byte-matching
the frozen preflight context for its ordinal; `config.ini` recorded
`rp01EventOrdinal=<N>`, `rp01WatchdogCycles=20000000`, `rngSeed=<S>`,
`structMode=rp01_skip_replay`.

| Pilot | Ordinal/Seed | Skip identity (real line) | Exit | Terminal |
|---|---|---|---:|---|
| RP01-R01 | 1 / 3135797961 | seq 69341, pc 0x4015fc, lq 9201/9693, store 69334, tick 31072965 | 1 | **HANG** |
| RP01-R02 | 2 / 226489823 | seq 71013, pc 0x42a6d8, lq 9349/9915, store 71007, tick 35427700 | 0 | **SQUASHED** |
| RP01-R03 | 3 / 1735144973 | seq 71014, pc 0x42a6dc, lq 9350/9916, store 71003, tick 35428085 | 0 | **SQUASHED** |
| RP01-R04 | 4 / 2455796178 | seq 72018, pc 0x422a58, lq 9427/10049, store 72000, tick 36564990 | 1 | **HANG** |
| RP01-R05 | 5 / 3984724524 | seq 72350, pc 0x44e2ec, lq 9467/10096, store 72346, tick 37424310 | 1 | **HANG** |

**HANG evidence (R01/R04/R05)** — the in-simulator watchdog fired
(`20,000,000 cycles × 385 ticks/cycle = tick 7,700,000,000`), `fatal`
aborted the run (exit 1), and no checksum exists — that absence is the
expected HANG shape:

```
RP01-R01/lsq_fwd_injections.log: CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 eligible=1 tick=7700000000
RP01-R01/stdout.log: src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:620: fatal: CHAOS_RP01_WATCHDOG_EXPIRED tick=7700000000 injected=1 eligible=1
RP01-R04/lsq_fwd_injections.log: CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 eligible=4 tick=7700000000
RP01-R05/lsq_fwd_injections.log: CHAOS_RP01_WATCHDOG=EXPIRED fired=1 injected=1 eligible=5 tick=7700000000
```

(The `fatal` path preempts gem5 exit callbacks, so the `CHAOS_RP01_STATUS`
exit-callback line is absent on HANG runs by construction; the watchdog
lines carry the identical injector status. Completed runs do print it, e.g.
R02: `CHAOS_RP01_STATUS: fired=1 injected=1 eligible=5 load_seq=71013
load_pc=4368088 lq_idx=9349 lq_gen=9915 store_seq=71007 replay_gen=1`.)

**Retained partial trace (watchdog-fatal HANG)** — the per-node
crash-durability flush kept every completed node readable, but the gz
stream lacks its trailer, so the converter honestly declares INCOMPLETE
(prep concern C2):

```
RP01-R01: readable rows 25779, EOFError "Compressed file ended before the end-of-stream marker" -> truncated
RP01-R04: readable rows 27213, truncated
RP01-R05: readable rows 27385, truncated
```

**SQUASHED investigation (R02/R03, runbook §5.3)** — both pilots exited 0
with the golden checksum `0x59fc61c040618747`; per §5.3 this triggered the
investigate-never-celebrate branch BEFORE any grading. The trace proves the
skip was NOT recovered: the skipped load was **discarded by an older,
unrelated LSQ squash** — task-14 audit P5, the pre-declared alternative
terminal. Real rows for the skipped load (R02, dyn_seq 71013):

```
26673,35426930,0,lq_lifecycle,71013,... queue=LQ;action=alloc;index=9349;generation=9915;reason=insert
26676,35427700,0,replay,71013,... reason=partial_forward_mismatch;pc=42a6d8;replay_generation=1;lq_entry_id=9349
26690,35429240,0,squash,71013,... record=squash_reason;dyn_inst_seq=71013;reason=lsq_squash;triggering_seq=0;...squash_cause=unrelated;fault_caused=0
26691,35429240,0,lq_lifecycle,71013,... queue=LQ;action=free;index=9349;generation=9915;reason=squash
```

No execution, no response, no writeback, no commit node for the skipped
instance — the golden checksum comes from the correct-path re-execution
after the discard. R03 shows the identical shape (seq 71014, same squash at
tick 35429240). The design's no-recovery proof stands; no MASKED/SDC/PASS
was recorded.

## 4. The five matched controls (Task 15 item 2)

`RP01-CONTROL-R01..R05` — same seed/workload, no `--chaos_lsqfwd`. All five:
`exit=0`, `checksum=0x59fc61c040618747`, **zero** `RP01_` lines, no
`lsq_fwd_injections.log` (no injector exists — hence no injector RNG is
drawn anywhere and the control config.ini carries no injector lines; the
five different seeds still produce the identical golden checksum). A
control is a determinism replication, never an independent sample.

## 5. Closure records (Task 15 item 4)

```
$ python3 tools/lsu_12model_closure.py record --model RP01 --binary-sha 68c6ce73... \
    --json .../audit_v3_2_12/RP01_records_v3.2.12.binary-68c6ce73.json --pilot-dir <10 dirs>
model=RP01 pilots=10
  RP01-R01: FinalClassification=UNRESOLVED ObservedTerminal=HANG ... missing=[ORACLE_FILE_MISSING;TRACE_INCOMPLETE;NO_INTERMEDIATE_PROPAGATION_EVENT;NO_REGISTER_WRITEBACK_EVENT;NO_CONSUMER_EDGE;NO_COMMIT_EVENT]
  RP01-R02: FinalClassification=PARTIAL ObservedTerminal=SQUASHED ...
  RP01-R03: FinalClassification=PARTIAL ObservedTerminal=SQUASHED ...
  RP01-R04: FinalClassification=UNRESOLVED ObservedTerminal=HANG ...
  RP01-R05: FinalClassification=UNRESOLVED ObservedTerminal=HANG ...
  RP01-CONTROL-R01..R05: FinalClassification=UNRESOLVED ObservedTerminal=NO_INJECTION ...
```

Per-pilot detail (the eight standard fields):

| Pilot | ObservedTerminal | TerminalReason | Causality | Structural | Integrity | TraceCompl | Oracle | FinalClassification |
|---|---|---|---|---|---|---|---|---|
| RP01-R01 | HANG | — | **PROVEN** | COMPLETE | TRUNCATED | INCOMPLETE | NOT_APPLICABLE | UNRESOLVED (honest C2 cap) |
| RP01-R02 | SQUASHED | TARGET_SQUASHED_NO_COMMIT | PARTIAL | COMPLETE | VALID | COMPLETE | PASS | PARTIAL (frozen v3.2.11 line) |
| RP01-R03 | SQUASHED | TARGET_SQUASHED_NO_COMMIT | PARTIAL | COMPLETE | VALID | COMPLETE | PASS | PARTIAL |
| RP01-R04 | HANG | — | **PROVEN** | COMPLETE | TRUNCATED | INCOMPLETE | NOT_APPLICABLE | UNRESOLVED |
| RP01-R05 | HANG | — | **PROVEN** | COMPLETE | TRUNCATED | INCOMPLETE | NOT_APPLICABLE | UNRESOLVED |
| C01..C05 | NO_INJECTION | NO_INJECTION_EVENT | UNPROVEN | n/a | VALID | COMPLETE | PASS | UNRESOLVED (control) |

Reading of the record fields:

- **The bridge removed `NO_INJECTION_EVENT` from all five pilots** — the
  records now carry `InjectionVerified=yes`, `ActivationVerified=yes`, the
  real `InjectionSeq/PC/Tick` identity, and chain kinds
  `['injection','lq_lifecycle','replay']` (HANG) /
  `['injection','lq_lifecycle','replay','squash']` (SQUASHED).
- **HANG is proven and never MASKED**: the identity-linked `replay` marker
  on the fault's own chain (a `_HANG_EVIDENCE_KINDS` member) yields
  `FaultCausality=PROVEN`; the watchdog event, the external-timeout
  possibility and the retained partial trace are all recorded. The
  FinalClassification caps at UNRESOLVED **only** because
  `RecordIntegrity=TRUNCATED` (the gz stream ends without its trailer after
  the `fatal`) — the prep report's pre-declared concern C2, recorded here,
  not papered over. `ObservedTerminal` stays HANG; no chain state can
  relabel it (the merged RP01 TIMEOUT guard + hard-HANG rule).
- **The stage gaps are true statements about the mechanism**:
  `NO_INTERMEDIATE_PROPAGATION_EVENT`, `NO_REGISTER_WRITEBACK_EVENT`,
  `NO_CONSUMER_EDGE`, `NO_COMMIT_EVENT` — the task-14 audit's conclusion
  (the skipped load is never re-issued: no further propagation, no
  writeback, no consumer, no commit) is exactly what the chains show.
- **SQUASHED stays below a complete verdict**: the squash node sits on the
  fault's own chain but is recorded `fault_caused=0` (squash_cause
  unrelated), so causality is PARTIAL and the classification is PARTIAL per
  the frozen v3.2.11 line — never MASKED, never a complete verdict.

## 6. Design-gate outcome

- Condition 4 (HANG/TIMEOUT classification, never MASKED): **CONFIRMED** —
  zero MASKED, zero SDC, zero PASS-MASKED records across all ten runs.
- No recovery of the skipped load in any pilot: **CONFIRMED** — the only
  completions are P5 discards (unrelated `lsq_squash`), proven by the
  squash + `lq_lifecycle free;reason=squash` nodes on the skipped loads'
  own chains and the absence of any commit node for the skipped instances.
- Wake-up-audit agreement: ordinals 1/4/5 (no later in-window squash) HANG;
  ordinals 2/3 (both inside the tick-35429240 `lsq_squash` window) were
  discarded by that squash — exactly the P1–P6/P5 dichotomy task 14 proved.

## 7. Files (all uncommitted; the main agent stages them with the evidence commit)

- Pilots/controls: `docs/gem5-fi/lsu/implementation_v3_2/pilots_v3_2_12/RP01-R01..R05`, `RP01-CONTROL-R01..R05` (stdout.log, exit_code.txt, config.ini, lsq_fwd_injections.log, prop_trace.csv.gz, pilot_meta.json, manifest.json, oracle.log [SQUASHED + controls], trace_v31.jsonl, trace_v31.jsonl.sha256)
- Records: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/RP01_records_v3.2.12.binary-68c6ce73.json`
- Verdict: `docs/gem5-fi/lsu/implementation_v3_2/audit_v3_2_12/RP01_verdict_v3.2.12.json`
- Bridge source: `docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py` (additive: `--rp01-skip-log`, `--observed-terminal`)
- Bridge test: `docs/gem5-fi/lsu/implementation_v3_2/platform/tests/test_rp01_skip_bridge.py`

## 8. Concerns carried forward

1. **C2 remains open by design**: HANG pilots cap at UNRESOLVED
   (RecordIntegrity=TRUNCATED) despite PROVEN causality and COMPLETE
   structural chains. If the researcher wants complete verdicts on HANG,
   the options remain the SQ03/SP05-style `exitSimLoop(...,1)` FAIL-event
   watchdog contract (clean exit, closed trace) or a converter truncation
   policy for HANG — both C++/design decisions outside Task 15's scope.
2. **The C++ trace-injection record (prep C1's full fix) is still open**:
   the bridge covers binary `68c6ce73` honestly from the real log line; a
   future binary emitting `inj_rp01` nodes would make the converter refuse
   the bridge (dedup guard) and use the real record instead.
3. **R02/R03's squashes record `triggering_seq=0`** (the lsq_squash call
   site does not record the boundary), so the squash's own trigger cannot
   be identity-linked — the PARTIAL cap is the honest consequence.
4. **The completed-pilot falsification branch was exercised and resolved**
   (§3): golden checksum + proven P5 discard. No re-run was needed to
   distinguish flake vs mechanism because the trace carries the discard
   proof, not a recovery.
