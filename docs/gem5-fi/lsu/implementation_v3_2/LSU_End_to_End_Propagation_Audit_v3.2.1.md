# LSU v3.2.1 — End-to-End Propagation Audit

**Date:** 2026-11-06
**Branch:** `lsu-platform-v3.2.1`
**Base:** `6f98088a7144d7f6fb22d985be3023ac5658e71b`
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2`
**gem5 binary:** rebuilt for this branch, SHA256 recorded in `GIT_COMMIT.txt`

## 0. Direct answers

1. **实际数据值是否记录？**
   **是，但只覆盖已观测的 A01/A03/FW02 路径。** `memory_response.new_value`
   写实际 packet 数据的 hex（≤32B；更大时只写 hash），并写 `data_len` /
   `data_fnv` / `pa`。`register_writeback.new_value` 写 packet 数据在
   writeback 前的值，并写 `phys_reg` / `arch_reg` / `source_event_id` /
   `source_value_hash`。这不是 `completeAcc` 之后从寄存器文件回读的值；
   A01/A03 没有 L1DForward，因此该 packet 数据就是实际写回值。

2. **是否记录真实 Producer-Consumer 数据依赖？**
   **是。** consumer 边来自 trace 的 taint set（load 的目标物理寄存器 ->
   消费者源物理寄存器），不是 ptag 顺序。`prop_edge` 行携带
   `source_event_id`、`destination_event_id`、`producer_inst_seq`、
   `consumer_inst_seq`、`source_value_hash`、`destination_value_hash`、
   `edge_type=register_dataflow`。

3. **是否实现 Replay/Squash？**
   **Hook 已实现；本轮观测到 Squash，未观测到 Replay。**
   `noteReplay`/`noteSquash` 在真实 LSQ `rescheduleMemInst` / `squash` 路径
   调用，且只记录 fault sequence 的指令。A03 R01 记录 **31 个 squash 节点**，
   **0 个 replay 节点**；A01/FW02 本轮无 replay。

4. **是否实现 R01-R05 精确 EventOrdinal？**
   **已接入 C++ 触发逻辑。** F0 在 `warmup + event_ordinal` 处触发，
   F5 从该序号开始持续施加，F6 用 `f6_observed == ordinal` 选择配对。
   A01/A03 的 5 个 context 均产生不同的目标 seq/address；FW02 的
   R02/R03 未成功触发，见未解决问题。

5. **三个 Pilot 是否具备完整传播记录？**
   - A01 R02/R04/R05：injection -> response(data) -> writeback(value) ->
     errant commit -> consumer，带显式 dataflow 边。
   - A01 R01：真实注入后 Page-table CRASH；Trace 完整到崩溃终态，但
     崩溃地址与注入地址不一致，只能记为 `crash_after_injection_no_address_match`。
   - A03 R01-R05：真实注入、data value、consumer、31 个 squash、CRASH；
     无应用 checksum。
   - FW02 R01/R04/R05：F6 触发、suppression、store/load pair、response/
     writeback、Oracle PASS；Trace 仍无 Commit 节点。
   - FW02 R02/R03：未通过（R02 无注入，R03 trace INVALID/PARTIAL）。

6. **Gate 3 剩余 9 个模型进度：0/9。** 未开始；未虚报。

## 1. 源码实现

| 组件 | 文件 | 状态 |
|---|---|---|
| CHAOSPropagation 全量 | `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/{hh,cc,py,SConscript}` | 已修改、已编译、Pilot 验证 |
| request/response/fragment ID | `CHAOSPropagation.cc` (`req_meta`, counters) | 已实现 |
| packet data / hash | `CHAOSPropagation.cc` (`noteMemResponse`) | 已实现 |
| writeback value / phys reg | `CHAOSPropagation.cc` (`taint_reg`) | 已实现 |
| explicit dataflow edge | `CHAOSPropagation.cc` (`writeEdgeRow`) | 已实现 |
| LQ/SQ generation | `lsq_unit.hh`, `lsq_unit.cc` (`lqEntryGeneration`, `sqEntryGeneration`) | 已实现 |
| execution/replay attempt | `dyn_inst.hh`, `lsq_unit.cc` | 已实现 |
| real replay hook | `lsq_unit.cc` (`noteReplay` call sites) | 已实现，未观测 |
| real squash hook | `lsq_unit.cc::squash` (`noteSquash`) | 已实现，A03 观测到 |
| forwarding decision | `lsq_unit.cc` + `CHAOSPropagation::noteForwarding` | 已实现 |
| FW02 ptag linkage | `CHAOSLSQFwd::lastFwdPtag` | 已实现 |
| EventOrdinal | `chaos_lsu_trigger.hh`, `CHAOSAddrPath`, `CHAOSLSQFwd`, `lsu_proxy.py` | 已实现 |
| Trace schema/writer/validator/completeness | `platform/` + `LSU_Trace_Schema_v3.2.json` | 已修改、35 tests PASS |

## 2. 真实 JSONL 样例

文件：`pilots_v3_2_1/A01-R02/trace_v31.jsonl`
`sample_run_id=PILOT-A01-R02`, `fault_id=A01-CFG01`。

关键实际记录（未改写）：

```json
{"event_id":2,"event_type":"injection","dyn_inst_seq":48,
 "old_value":"0x7ffffefdb8","new_value":"0x7ffffefdb0",
 "injection_status":"INJECTED"}
{"event_id":5,"event_type":"memory_response","request_id":14,"response_id":1,
 "fragment_id":15,"lq_entry_id":2,"entry_generation":2,
 "execution_attempt_id":1,"replay_generation":0,"pa":"0x7edb0",
 "new_value":"0000000000000000","data_len":8,
 "data_fnv":"a8c7f832281a39c5","data_hex":"0000000000000000"}
{"event_id":6,"event_type":"register_writeback","phys_reg":68,"arch_reg":3,
 "new_value":"0000000000000000","source_event_id":4,
 "source_value_hash":"a8c7f832281a39c5","response_id":1}
{"event_id":8,"event_type":"consumer_commit","dyn_inst_seq":50,
 "commit_seq":46,"consumer_value_hash":"a8c7f832281a39c5"}
{"record_type":"propagation_edge","source_event_id":6,"destination_event_id":8,
 "producer_inst_seq":48,"consumer_inst_seq":50,
 "source_value_hash":"a8c7f832281a39c5",
 "destination_value_hash":"a8c7f832281a39c5",
 "edge_type":"register_dataflow"}
{"record_type":"summary","run_status":"COMPLETED",
 "fault_activation_status":"TRIGGERED","terminal_state":"MASKED",
 "trace_completeness":"COMPLETE","counts":{"events":14,"edges":6,"injections":1}}
```

The consumer edge is **not** ptag-order: it connects the taint_reg event to the
consumer because the consumer's source physical register is in the taint set.

## 3. R01-R05 contexts

Actual command-line ordinals and seeds are in
`pilots_v3_2_1/context_sweep_summary.json`. Summary:

| Model | Context | Seed | Ordinal | Injected | Terminal | Coverage | Oracle |
|---|---|---:|---:|---|---|---|---|
| A01 | R01 | 2108120075 | 1 | 1 | CRASH | COMPLETE | FAIL (crash) |
| A01 | R02 | 1113826800 | 2 | 1 | MASKED | COMPLETE | PASS |
| A01 | R03 | 1302709433 | 3 | 1 | UNRESOLVED | COMPLETE | PASS |
| A01 | R04 | 2194451614 | 4 | 1 | MASKED | COMPLETE | PASS |
| A01 | R05 | 3228552887 | 5 | 1 | MASKED | COMPLETE | PASS |
| A03 | R01 | 663646247 | 1 | 146 | CRASH | COMPLETE | FAIL |
| A03 | R02 | 1626885462 | 2 | 145 | CRASH | COMPLETE | FAIL |
| A03 | R03 | 110775855 | 3 | 144 | CRASH | COMPLETE | FAIL |
| A03 | R04 | 2766846323 | 4 | 143 | CRASH | COMPLETE | FAIL |
| A03 | R05 | 1156093484 | 5 | 142 | CRASH | COMPLETE | FAIL |
| FW02 | R01 | 2941542370 | 1 | 1 | MASKED | COMPLETE | PASS |
| FW02 | R02 | 2129071279 | 2 | 0 | CRASH | INCOMPLETE | FAIL |
| FW02 | R03 | 1336081385 | 3 | 1 | CRASH | PARTIAL | FAIL |
| FW02 | R04 | 527667424 | 4 | 1 | MASKED | COMPLETE | PASS |
| FW02 | R05 | 3622278636 | 5 | 1 | MASKED | COMPLETE | PASS |

A01 R01 / R03 show that a different EventOrdinal is not merely a different
seed: the target dynamic event changes, and the terminal outcome changes
(CRASH vs MASKED/UNRESOLVED).

## 4. Store-to-load forwarding record (FW02)

`pilots_v3_2_1/FW02-R01/trace_v31.jsonl` contains:

```json
{"event_type":"forwarding_decision","unit":"LSU",
 "sub_unit":"Store-to-Load Forwarding","store_seq":383,"load_seq":397,
 "byte_begin":"0x7ffffefc28","byte_end":"0x7ffffefc30",
 "forward_decision":"suppressed","memory_path":1,
 "store_data_fnv":"a8c7f832281a39c5","forward_data_fnv":"0000000000000000"}
```

The JSONL now carries the store seq, load seq, byte range, decision and memory
path. For normal forwarding, `forward_decision=forwarded` and
`memory_path=0`.

## 5. Replay/Squash

A03-R01 actual event counts:

```text
injection=73  address_formed=73  memory_request=72  memory_response=66
register_writeback=69  consumer_commit=63  squash=31  errant_commit=1
simulator_abort=1  replay=0
```

Squash nodes come from `LSQUnit::squash`, filtered to dynamic instructions
that received the fault. Replay nodes are implemented at
`rescheduleMemInst` sites but were not observed in these runs.

## 6. Workloads

W1-W8 baselines remain 8/8 exit 0 + 8/8 Oracle PASS under the v3.2.1 binary;
see `baselines/` and `logs/v321_baseline.log`. W6/W8 repaired versions and
SHA256 are unchanged from v3.2.

## 7. Workbook v3.2.1

`gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.1.xlsx` preserves all 60
SampleRunIDs, SubTaskIDs, RunIDs and seeds. **Formal WarmUp/ROI are marked
`NEEDS_RESEARCHER_CONFIRMATION`**; the pilot `WarmUp=0/full` is not frozen as
the formal authority. 60 formal samples remain `NOT_RUN`.

## 8. Unresolved / caveats

1. FW02 R02 did not inject; FW02 R03 trace is INVALID/PARTIAL. Both are
   recorded as failures, not passes.
2. A01 R01 CRASH evidence is `page_table_fault_after_injection_no_address_match`;
   the crash address is not the injected address, so causality is not proven.
   A01 R03 has no data-value evidence and terminal is `UNRESOLVED`, not MASKED.
3. FW02 trace still has no Commit/consumer node; the trigger pair is in the
   forwarding event, but the commit-side closure is missing.
4. Replay is implemented but not observed; no replay event is claimed.
5. `request_id`, `response_id`, `fragment_id`, `entry_generation` and
   `commit_seq` are tracer-assigned real counters (gem5 v25 has no such
   built-in IDs); they are stable within a trace, not global gem5 IDs.
6. `register_writeback.new_value` is the packet value at the pre-writeback
   hook, not a post-`completeAcc` register-file read. A01/A03 have no
   L1DForward so this equals the actual writeback value; FW02 has no
   writeback data corruption.
7. Raw data hex is recorded only for ≤32 bytes; larger packets record length
   and FNV hash.
8. Squash recording is limited to dynamic instructions that received a fault;
   unrelated pipeline squashes are not recorded (to keep the trace bounded).
9. Gate 3: **0/9** remaining models implemented.
10. Gate 4: **not started**; no formal SampleRunID was executed.

These limitations are not filled with defaults or fabricated edges.
