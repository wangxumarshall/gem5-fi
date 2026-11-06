# LSU v3.2 — End-to-End Propagation Audit

**Audit date:** 2026-11-06
**Branch:** `lsu-platform-v3.2`
**HEAD:** `1622d7de37a23d1d0a65672cf429c3378853a72f` (package source snapshot `dad1681d`)
**Base:** `6f98088a7144d7f6fb22d985be3023ac5658e71b`
**Worktree:** `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2`
**gem5:** v25.1.0.1, branch-root binary SHA256
`b233a4cbb1085887c1a8533a77a9fa0885dcb36aa34608f7a90245b7395eaabe`

## 0. 结论先行

平台已经具备：

1. 从真实 gem5 Hook 注入故障；
2. 用独立 JSONL 记录故障身份、动态指令身份、请求/响应、寄存器写回、Commit/Consumer；
3. 用 PropagationEdge 关联相邻事件；
4. 把最终软件 checksum 与冻结 Golden 对比，得到 Oracle PASS/FAIL；
5. 把 RunStatus / FaultActivationStatus / TerminalState / TraceCompleteness 分开记录。

目前**尚未具备**的部分：

- 真实 Replay/Squash 事件：schema 有字段，但实际 trace 中
  `execution_attempt_id`、`replay_generation` 为 `null`，`squash_status` 为
  `UNKNOWN`；没有观测到 replay/squash 节点。
- **没有 SDC 端到端样例**：A01、FW02 的软件输出仍与 Golden 一致
  （`MASKED`）；A03 在应用输出前崩溃（`CRASH`），因此没有
  “故障改变应用输出且 Oracle 失败”的完整 SDC 证据。
- 9 个正式模型尚未实现，60 个正式样本未运行。

因此，对“从注入位置一直追踪到应用层反馈”的能力，准确表述是：

> **A01 已实现注入→激活→LSU/L1D/RF→Commit→应用 checksum→Oracle 的完整链；
> A03 实现到 Commit/Consumer 后以真实 Page-table fault 崩溃；
> FW02 实现到响应/写回并用 Oracle 关联应用输出，但 trace 中没有 Commit 节点。**

## 1. 平台实际实现情况

### 1.1 Fault Injection Manager

| 文件 | 状态 | 证据 |
|---|---|---|
| `platform/fault_manager.py` | 已实现、已测试 | 134 行；`tests/test_fault_manager.py` 7/7 PASS；覆盖 F0 单次、F5 持续/nochange、F6 命名触发 |
| `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh` | 已存在、已编译、集成验证 | F0/F5/F6 真实 gem5 触发层；A01/A03 使用 |
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc` | 已实现、已编译、Pilot 验证 | `a01_bit3_load`、`a03_bit3_stuck0_load` 分支（约 341–348 行） |
| `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc` | 已实现、已编译、Pilot 验证 | `maybeSuppressForwarding`（约 428 行）、F6 模式 |
| `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` | 已修改、已编译、Pilot 验证 | full-coverage forwarding 决策点调用抑制（约 1517 行） |

区分：

- **已实现**：F0、F5、F6 的三种触发逻辑均有真实源码。
- **已编译**：上述 C++ 已进入 `build/ARM/gem5.opt`（见 `logs/build_v32_hooks_incremental2.log`，最终 `scons: done building targets`）。
- **已测试**：平台状态机有 35 个 Python 单元测试；C++ Hook 由三个 Pilot 集成验证，**尚无 C++ 单元测试**。
- **仍在开发**：LQ04、SQ01、SQ03、LP01、SP05、FW05、MD04、RP01、DA04。

### 1.2 配置解析器与 Run Manifest

- `platform/config_parser.py`：348 行；严格读取 Sheet `5.60个样本执行矩阵`，校验 60/12/5、SampleRunID/SubTaskID/RunID 父子关系、Seed 唯一性、WorkloadPath 存在性、BinarySHA256、Oracle；缺失即报错，不使用默认值。
- v3.1 输入真实结果：255 个缺陷（45 ABSENT、45 N/A SHA、45 N/A Oracle、60 unresolved WarmUp、60 unresolved ROI）。
- v3.2 workbook 真实结果：`CONFIG_OK samples=60 models=12 seeds=60 workloads_present=60`，严格 exit 0。
- `platform/manifest.py`：165 行；Seed 来自 Excel；Pilot Manifest 现在记录**真实注入命令**（已修复 review 发现的问题）。

证据：

```text
logs/config_v31.json                 v3.1 error_count = 255
logs/config_v32.json                 v3.2 error_count = 0
logs/config_v32_validation.log       CONFIG_OK samples=60 models=12 seeds=60 workloads_present=60
pilots/A01F0/manifest.json           command 含 --chaos_addrpath/--agu_pre_mode/--addrpath...
```

### 1.3 F0 / F5 / F6 实际实现

| 模式 | 实际 Hook | 实际触发证据 | 状态 |
|---|---|---|---|
| F0 | `LSQ::pushRequest` 入口，`a01_bit3_load` | A01：`attempted=2785 eligible=1466 injected=1`，`0x7ffffefdc0 → 0x7ffffefdc8` | 已实现/已编译/已运行 |
| F5 | 同上，逐 eligible Load 重施加 `a03_bit3_stuck0_load` | A03：`injected=146`；73 次改值、73 次 nochange；最终 Page-table fault | 已实现/已编译/已运行 |
| F6 | `LSQUnit::read` full-coverage forwarding 决策点，`maybeSuppressForwarding` | FW02：6 个真实 Store→Load 对，1 次抑制，`load_seq=397 store_seq=383` | 已实现/已编译/已运行 |

### 1.4 Trace v3.1 源码与工具

| 组件 | 文件 | 行数/状态 |
|---|---|---:|
| Schema | `LSU_Trace_Schema_v3.2.json` | 已发布 |
| JSONL Writer | `platform/trace_writer.py` | 204 行，已测试 |
| Validator | `platform/trace_validator.py` | 178 行，已测试 |
| Completeness | `platform/trace_completeness.py` | 80 行，已测试 |
| Summary | `platform/trace_summary.py` | 49 行，已测试 |
| CSV→JSONL 桥 | `platform/tools/prop_trace_to_v31.py` | 208 行，已测试 |
| Terminal 分类 | `platform/terminal.py` | 66 行，已测试 |

`trace_writer.py` 对每个 event 写全 39 个 v3.1 字段；未知字段写 `null`，不猜测。Trace v3.1 的字段语义：

- 指令身份：`dyn_inst_seq`、`execution_attempt_id`、`replay_generation`、`commit_seq`
- 故障身份：`fault_id`、`sample_run_id`、`injection_event_id`、`fault_model_id`
- 传播：`event_id`、`parent_event_id`、`propagation_edge_id`、`source_event_id`、`destination_event_id`
- 请求：`request_id`、`response_id`、`fragment_id`、`va`、`pa`、`lq_entry_id`、`sq_entry_id`、`entry_generation`
- 状态：`injection_status`、`activation_status`、`commit_status`、`squash_status`、`terminal_state`、`trace_completeness`

### 1.5 TerminalState 分类

`platform/terminal.py` 独立输出四个字段：

```text
RunStatus: COMPLETED / NO_ELIGIBLE_EVENT / TIMEOUT / SIMULATOR_ERROR
FaultActivationStatus: NOT_TRIGGERED / TRIGGERED / UNKNOWN
TerminalState: MASKED / SQUASHED / DETECTED_CONTAINED /
               ARCH_STATE_CORRUPTION / SDC / CRASH / HANG
TraceCompleteness: COMPLETE / INCOMPLETE
```

未完成 Trace 不会被判为 `MASKED`。三个 Pilot 的最终分类来自 `pilot_meta.json`：

| Pilot | RunStatus | Activation | Terminal | Completeness |
|---|---|---|---|---|
| A01 | COMPLETED | TRIGGERED | MASKED | COMPLETE |
| A03 | SIMULATOR_ERROR | TRIGGERED | CRASH | COMPLETE (to crash terminal) |
| FW02 | COMPLETED | TRIGGERED | MASKED | COMPLETE |

## 2. Trace 真实运行样例

以下是 **A01 Pilot 实际生成**的 `trace_v31.jsonl`（不是人工构造的样例）。完整文件在 `traces/A01F0.trace_v31.jsonl`。

### 2.1 关键字段

- `sample_run_id`: `PILOT-A01-F0-W1-R01`
- `fault_id`: `A01-CFG01`
- `fault_model_id`: `A01`
- 注入事件：`event_id=2`，`injection_event_id=1`，`dyn_inst_seq=272`
- 故障前地址：`0x7ffffefdc0`
- 故障后地址：`0x7ffffefdc8`（bit3 XOR）
- 目标动态指令：`dyn_inst_seq=272`（Load，`pushRequest` 入口）
- 响应物理地址：`pa=0x7edc8`
- Commit：`event_id=7`，`event_type=errant_commit`，`commit_status=COMMITTED`，`pc=40c0f0`
- 后续 Consumer：`dyn_inst_seq=277、278、279`，`commit_status=COMMITTED`
- 终态：`MASKED`；TraceCompleteness：`COMPLETE`

### 2.2 事件链（实际 JSONL）

```text
event 2  injection         AGU       dyn_inst_seq=272  old=0x7ffffefdc0 new=0x7ffffefdc8  INJECTED  TRIGGERED
event 3  address_formed    AGU       dyn_inst_seq=272  va=0x7ffffefdc8
edge 1   2 -> 3            addr_form
event 4  memory_request    LSQ       dyn_inst_seq=272  request_id=272 va=0x7ffffefdc8
edge 2   3 -> 4            mem_req
event 5  memory_response   L1D       dyn_inst_seq=272  request_id=272 pa=0x7edc8
edge 3   4 -> 5            resp
event 6  register_writeback RF       dyn_inst_seq=272  dest_idx=0
edge 4   5 -> 6            taint_reg
event 7  errant_commit     Commit    dyn_inst_seq=272  COMMITTED  pc=40c0f0
edge 5   6 -> 7            errant_commit
event 8  consumer_commit   Commit    dyn_inst_seq=277  COMMITTED  pc=40c104
edge 6   7 -> 8            consumer
event 9  consumer_commit   Commit    dyn_inst_seq=278  COMMITTED  pc=40c108
edge 7   8 -> 9            consumer
event 10 consumer_commit   Commit    dyn_inst_seq=279  COMMITTED  pc=40c10c
edge 8   9 -> 10           consumer
event 11 consumer_commit   Commit    dyn_inst_seq=279  COMMITTED  pc=40c10c
edge 9   10 -> 11          consumer
event 12 consumer_commit   Commit    dyn_inst_seq=279  COMMITTED  pc=40c10c
edge 10  11 -> 12          consumer
```

实际 JSONL 中的对应字段（节选，未改写）：

```json
{"record_type":"event","sample_run_id":"PILOT-A01-F0-W1-R01","fault_id":"A01-CFG01","fault_model_id":"A01","injection_event_id":1,"event_id":2,"parent_event_id":null,"event_type":"injection","unit":"AGU","dyn_inst_seq":272,"old_value":"0x7ffffefdc0","new_value":"0x7ffffefdc8","injection_status":"INJECTED","activation_status":"TRIGGERED","trace_completeness":"COMPLETE","detail":"site=lsq_pushRequest_PRE;...;is_load=1;..."}
{"record_type":"propagation_edge","sample_run_id":"PILOT-A01-F0-W1-R01","fault_id":"A01-CFG01","propagation_edge_id":1,"source_event_id":2,"destination_event_id":3,"producer_inst_seq":272,"consumer_inst_seq":272,"edge_kind":"addr_form","trace_completeness":"COMPLETE"}
{"record_type":"event","event_id":7,"parent_event_id":6,"event_type":"errant_commit","unit":"Commit","dyn_inst_seq":272,"commit_status":"COMMITTED","terminal_state":null,"trace_completeness":"COMPLETE","detail":"trigger=faulting_load_commit;pc=40c0f0"}
{"record_type":"summary","run_status":"COMPLETED","fault_activation_status":"TRIGGERED","terminal_state":"MASKED","trace_completeness":"COMPLETE","counts":{"events":12,"edges":10,"injections":1,"activations":11}}
```

### 2.3 Replay / Commit / Squash 实际状态

- Commit：A01 有 `errant_commit` + 5 个 `consumer_commit`，均为 `COMMITTED`。
- A03 有 63 个 `consumer_commit`、1 个 `errant_commit`，最终 `simulator_abort`。
- **Replay**：未观测到；`execution_attempt_id`、`replay_generation` 为 `null`。
- **Squash**：未观测到；`squash_status` 为 `UNKNOWN`。
- 这不是“已完成 Replay/Squash 追踪”；是 schema 已支持、当前实现未产生真实记录。

## 3. 端到端传播链验证

### 3.1 A01：注入 → 激活 → LSU/L1D/RF → Commit → 应用 checksum → Oracle

| 环节 | 真实证据 |
|---|---|
| 故障注入 | `CHAOSAddrPath` `a01_bit3_load`，`lsq_pushRequest_PRE`，`injected=1` |
| 故障激活 | `address_formed`（event 3）与 `memory_request`（event 4）均为同一 `dyn_inst_seq=272` |
| 微架构内部传播 | `memory_response` L1D `pa=0x7edc8`；`register_writeback` dest_idx=0 |
| 跨单元传播 | AGU → LSQ → L1D → RF → Commit |
| 架构状态 | `errant_commit` at PC `40c0f0`；consumer commits 277/278/279 |
| 应用层输出 | `stdout.log` 实际输出 `728e604ffcec539d` |
| Golden | `agu_addrmodes.golden` = `728e604ffcec539d` |
| Oracle | `expected=728e604ffcec539d got=728e604ffcec539d` / `ORACLE_PASS` |
| 终态 | `MASKED`；TraceCompleteness `COMPLETE` |

结论：**A01 具备从注入到 Commit 再到应用 Oracle 的完整可复核链**。

### 3.2 A03：注入 → 持续激活 → 多次 LSU/L1D/RF → Commit → Page-table CRASH

| 环节 | 真实证据 |
|---|---|
| 故障注入 | `a03_bit3_stuck0_load`，`attempted=284 eligible=146 injected=146` |
| 故障激活 | 146 次条件施加；73 次改值、73 次 nochange（`value_changed=0`） |
| 首次改值 | `0x7ffffefdb8 → 0x7ffffefdb0` |
| 传播 | 72 个 `memory_request`、66 个 `memory_response`、69 个 `register_writeback` |
| 架构状态 | 63 个 `consumer_commit`、1 个 `errant_commit` |
| 应用层输出 | **无 checksum**；进程 abort |
| 异常 | `src/sim/faults.cc:103: panic ... Page table fault when accessing virtual address 0xffffffffffb73c50`，`Program aborted at tick 1648955` |
| Oracle | `ORACLE_FAIL: no checksum line` |
| 终态 | `SIMULATOR_ERROR` / `TRIGGERED` / `CRASH`；trace 564 events / 489 edges，`COMPLETE` 到崩溃终态 |

结论：**A03 的故障真实触发并传播到 Commit/Consumer，但它在应用 checksum 之前崩溃；没有应用层 PASS/FAIL 可谈。**

### 3.3 FW02：F6 条件触发 → 抑制 Forwarding → 内存响应/写回 → 应用 checksum → Oracle

| 环节 | 真实证据 |
|---|---|
| 故障注入 | `f6_fw02`，`observed=6` 个真实 full-coverage pair，`suppressed=1` |
| 触发对 | `load_seq=397`，`store_seq=383`，`Vaddr=0x7ffffefc28` |
| 传播 | `memory_response` `pa=0x7cc28`；`register_writeback` dest_idx=0 |
| 架构状态 | trace 中没有 Commit 节点（4 events / 3 edges） |
| 应用层输出 | `stdout.log` 实际输出 `1f4cbf14327717df` |
| Golden | `sq_forward.golden` = `1f4cbf14327717df` |
| Oracle | `expected=1f4cbf14327717df got=1f4cbf14327717df` / `ORACLE_PASS` |
| 终态 | `MASKED`；TraceCompleteness `COMPLETE` |

结论：**FW02 的 F6 触发和抑制是真实的，应用输出与 Golden 一致；但 JSONL 没有 Commit 节点，F6 触发对只记录在 `lsq_fwd_injections.log` 和 `pilot_meta.json`。**

## 4. Pilot 结果总表

| 检查项 | A01 / F0 | A03 / F5 | FW02 / F6 |
|---|---|---|---|
| Hook 已实现 | 是 | 是 | 是 |
| 已编译进 gem5 | 是 | 是 | 是 |
| 实际运行 | 是 | 是 | 是 |
| 真正触发故障 | 是，`injected=1` | 是，`injected=146` | 是，`suppressed=1` |
| 完整传播 Trace | 12 events/10 edges，到 Commit/Consumer | 564 events/489 edges，到 CRASH | 4 events/3 edges，到 RF writeback |
| 应用层反馈 | checksum `728e…` | 无（崩溃） | checksum `1f4c…` |
| Oracle | PASS | FAIL: no checksum | PASS |
| 终态 | MASKED | CRASH | MASKED |
| 结论 | Pilot 通过 | Pilot 触发通过，终态 CRASH | Pilot 通过 |

## 5. 工作负载 W1–W8

| 工作负载 | 源码 | 二进制 | Golden | Binary SHA256 | 基线 | 目标事件证明 |
|---|---|---|---|---|---|---|
| W1 AGU-AddrModes | `workloads/agu_addrmodes.c` | `workloads/agu_addrmodes` | `728e604ffcec539d` | `90a19003…b49b` | exit0, tick 19544525 | 6 `Read called` + memory access |
| W2 LQ-Lifetime | `lq_lifetime.c` | `lq_lifetime` | `1624d44faff77183` | `7c69fd27…156d` | exit0, tick 37983715 | 6232 load insert, 756 squashed |
| W3 SQ-Drain | `sq_drain.c` | `sq_drain` | `ba3b3185e541ad03` | `d423539c…188f` | exit0, tick 149995615 | 31092 writeback + complete |
| W4 SQ-Forward | `sq_forward.c` | `sq_forward` | `1f4cbf14327717df` | `132a84f7…f297` | exit0, tick 19112940 | 6 forwarding, 1 mis-match |
| W5 Load-Response | `load_response.c` | `load_response` | `99c106541150be0e` | `3779e8ce…e711` | exit0, tick 55153560 | 18269 Read called |
| W6 Store-Path | `store_path.c` | `store_path` | `2543a2a60de01795` | `906b3798…fbcf` | exit0, tick 92581720 | 10609 store complete; OOB fixed |
| W7 Replay-Dependency | `replay_dependency.c` | `replay_dependency` | `59fc61c040618747` | `ca15390f…38f4` | exit0, tick 40653690 | 267 forwLoads, 5 rescheduled, 7 violations |
| W8 Alignment | `alignment.c` | `alignment` | `3f89eab79392ce69` | `89ff937a…18c0` | exit0, tick 34556445 | unaligned addresses; OOB fixed |

完整 SHA256、编译脚本、运行脚本、Golden、`host.out`、gem5 基线、`config.ini`、`stats.txt`、`stdout/stderr`、`oracle.log`、`event_proof.log` 均在 `workloads/` 与 `baselines/`。

W6/W8 修复证据：`logs/probe_results.txt` 与 `logs/probe_*.log`：

```text
mode=store_path exit=139
mode=alignment exit=139
mode=store_path_fixed exit=0
mode=alignment_fixed exit=0
```

## 6. 源码版本

```text
branch: lsu-platform-v3.2
head:   1622d7de37a23d1d0a65672cf429c3378853a72f
base:   6f98088a7144d7f6fb22d985be3023ac5658e71b
status: worktree clean
```

变更规模（相对 base）：

```text
334 files changed, 112998 insertions(+), 9 deletions(-)
326 added, 8 modified
```

完整源码补丁：`LSU_Platform_Source_Code_v3.2.patch`（约 179 KB）。
完整 `git diff --name-status` 在审计包 `git/GIT_NAME_STATUS.txt`。
新增/修改的核心文件：

```text
CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.{hh,cc,py}
CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.{hh,cc,py}
CHAOS/gem5/src/cpu/o3/lsq_unit.cc
configs/se/lsu_proxy.py
docs/gem5-fi/lsu/implementation_v3_2/platform/*.py
docs/gem5-fi/lsu/implementation_v3_2/platform/tools/prop_trace_to_v31.py
docs/gem5-fi/lsu/implementation_v3_2/workloads/*
docs/gem5-fi/lsu/implementation_v3_2/pilots/*
docs/gem5-fi/lsu/implementation_v3_2/baselines/*
docs/gem5-fi/lsu/implementation_v3_2/gem5-fi-LSU-Final-Paper-Experiment-Plan-v3.2.xlsx
```

说明：主仓库 `/home/sdc/gem5-fi-ding` 仍有与本轮无关的既有工作树删除项；本审计只读取独立 worktree，没有触碰、恢复或重跑主仓库状态。

## 7. 明确未完成项

1. Gate 3：剩余 9 个模型未实现。
2. Gate 4：60 个正式样本未运行。
3. Replay/Squash：schema 已支持，真实事件未观测；`execution_attempt_id`、`replay_generation` 为 null，`squash_status=UNKNOWN`。
4. SDC：尚无“应用输出改变且 Oracle 失败”的 Pilot；A01/FW02 为 MASKED，A03 为 CRASH。
5. C++ Hook 目前只有 Pilot 集成测试，没有 C++ 单元测试。
6. FW02 的 F6 触发对只存在日志/manifest，JSONL 节点没有 `store_seq` 字段。

以上未完成项没有用推测或默认值补齐。
