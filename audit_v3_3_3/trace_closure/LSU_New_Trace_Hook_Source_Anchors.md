# New Trace Hook — Real Source Locations

**Binary:** `62e1b1be0a01f852579293a4db372d6634ec44763c1439520c77b7581467a6cd`
**Build:** `CHAOS/gem5/build/ARM/gem5.opt` installed to repo-root `build/ARM/gem5.opt`
**Diff:** `LSU_Final_Source_Diff.patch` (baseline `78ac9ba7`)

## SP05 — real architectural commit

| Item | File:line | Function | Purpose |
|---|---|---|---|
| H1 capture | `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc:2679` (capture at `:2698`) | `CHAOSPropagation::noteCommit` | While `CHAOSLSQFwd::sp05Mode()`, store the real commit tick/seq/PC/SQ identity for every committing store. |
| H2 `store_commit` | `CHAOSPropagation.cc:1813` (`noteSP05Injection`) | emission before `inj_sp05`, same ptag; `commit_tick_source=commit_stage_capture` | Independent commit event; node timestamp = real commit tick. |
| H3 `store_writeback_suppressed` | `CHAOSPropagation.cc:1980`; call site `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:1109` | `noteSP05WritebackSuppressed` | Negative evidence: request present but not sent (`request_sent_after=0;mem_sent=0;drain_tick=0;visibility_state=NEVER_WRITTEN`). Not a writeback event. |
| H4 honest tick | `CHAOSPropagation.cc:1813` | removed caller-supplied fallback; missing capture records `commit_tick=0;commit_tick_source=unavailable` | No fabricated commit tick. |

## RP01 — internal-watchdog terminal flush

| Item | File:line | Function | Purpose |
|---|---|---|---|
| Terminal snapshot | `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:634` | `CHAOSLSQFwd::rp01Watchdog` | Builds `WatchdogTerminalInfo` (trigger/reason/fault/eligible/last eligible/replay/LQ-SQ/progress/commit). |
| Flush call | `CHAOSLSQFwd.cc:672` | before `fatal()` | Idempotent `flushWatchdogTerminal(info)`; preserves `exit(1)` semantics. |
| Flush implementation | `CHAOSPropagation.cc:2027` | `CHAOSPropagation::flushWatchdogTerminal` | Writes `trace_flush_start` → `watchdog_terminal` → `trace_flush_complete`; `gzflush` + `gzclose`. |
| Last eligible bookkeeping | `CHAOSLSQFwd.cc:709` | `maybeSkipPartialReplay` | Read-only last eligible seq/PC/LQ/SQ/replay generation; never feeds `shouldSkip`. |
| LQ/SQ snapshot access | `CHAOS/gem5/src/cpu/o3/lsq.hh:929-930`; `lsq.cc:1802,1808` | `LSQ::getLSQUnit`, `LSQ::numLSQUnits` | Read-only per-thread LSQ accessor for the terminal snapshot. |

## Shared tracer bookkeeping

- `CHAOSPropagation::writeNode` / `writeEdgeRow`: update `last_node_tick` after each row.
- `CHAOSPropagation::noteCommit`: update `last_commit_dyn_seq` / `last_commit_tick`.
- Public read-only getters: `traceCommitSeq()`, `lastCommitDynSeq()`, `lastCommitTick()`, `traceLastNodeTick()`, `traceNextNodeId()`.

## Event format

All new rows go through the existing `writeNode()` CSV contract
(`node_id,tick,ptag,kind,dyn_inst_seq,request_id,addr,phys_reg,arch_reg,detail`) and the
existing `fault_id/event_id/parent_event_id` conversion (`prop_trace_to_v31.py`). No separate
per-model ID system exists.

## Behavior

Read-only observation only. No change to instruction order, LSU scheduling, store/load
decisions, forwarding, replay, commit decisions, injection time/probability/state/duration,
or RNG consumption. Single-threaded, no locks, no new scheduled events.

## Tool locations

- `tools/lsu_v333_qualified.py` — A03 anchor fallback, SP05 new events, RP01 flush parsing.
- `tools/lsu_v333_propagation.py` — final row enrichment.
- `tools/lsu_v333_trace_closure.py` — final 60-context readiness + 11-context repair validation.
