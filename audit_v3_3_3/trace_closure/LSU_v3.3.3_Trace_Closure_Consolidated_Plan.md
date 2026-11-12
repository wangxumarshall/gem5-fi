# LSU v3.3.3 — Final Trace Closure & Formal Readiness（统一执行计划）

- 日期：2026-11-12
- Worktree：`/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-platform-v3.2.12`
- 分支：`lsu-v3.3.1-context-workload-20261111`
- 基线 HEAD：`78ac9ba730afb5bf9a5714568a8b8fa197cf0bbb`
- 冻结二进制：`build/ARM/gem5.opt` = `1126e0fd1fea8e123f78d17559f10f51ce52025f75350f7b45ea310960b4f338`
- 冻结 config：`configs/se/lsu_proxy.py` = `8309da72e9fd97e8eb3271c680bb0da5fc22f8d65188502076996b81992cb225`
- 三份根因报告：`audit_v3_3_3/trace_closure/{A03_R02_Trace_Closure_Analysis.md, SP05_Trace_Hook_Design.md, RP01_Watchdog_Trace_Flush_Design.md}`

## 0. 冻结不变量（本轮不得改变）

12 个 Fault Model；60 个 SampleRunID；60 个 Seed；R01–R05 的 10/30/50/70/90% ROI；60 个 EventOrdinal；
已批准的 12 个模型 Workload 映射；30 个 Workload Override；Fault-Control 配对；注入位置与故障语义。
禁止改 Verdict、禁止 QUALIFIED→PASS 硬升级、禁止覆盖历史 Trace、禁止混用主仓库旧 Binary。

## 1. 统一根因与修复方案

| # | Model | Context | Root Cause | Source File | Function | Source Anchor | Required Hook | Behavior Impact | Binary Impact | Validation |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | A03 | R02 | 解析器把"模型首个 affected"（13718，投机实例，被无关 squash）当作因果锚点；其 trace 无 resp/taint/consumer。真实首个进入架构态的是 13772（ordinal 1099，errant_commit），其 resp→taint_reg→consumer→commit 全在现有 trace 中。 | `tools/lsu_v333_qualified.py` | `_a03()` / `_scan_prop_trace()` | `_a03` 约 341 行 `target_seq=seq`；`_PROP_KINDS` 约 165 行 | 无 C++ Hook；解析层：保留 13718 作为 "first affected (squashed)" provenance，因果链改用 `errant_commit.dyn_inst_seq`（本 run=13772）为锚点 | 无（分析工具） | 无 | 重跑 `qualified_evidence("A03", A03-R02-fault)`，`load_result/register_writeback/consumer` 均 found；status=PASS；checksum 链仍为 `d48b947f…`（已由 Agent A 离线重算精确复现） |
| T2 | SP05 | R01–R05 | `commit_event`：真实 commit 发生在注入之前（`Commit::commitHead`），但目标身份在注入时才登记，`noteCommit` 未捕获；现有 `commit_tick` 是 `caller_supplied` 的注入 tick。`writeback_event`：SP05 语义为"跳过 cache write"，真实写回**不存在**，`sp05_write_skipped` 被规则正确拒绝冒充。 | `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`, `lsq_unit.cc` | `noteCommit`, `noteSP05Injection`, `noteSP05WritebackSuppressed`, `LSQUnit::writebackStores` | `commit.cc:1318`；`CHAOSPropagation.cc:2510-2553, 1809-1920`；`lsq_unit.cc:1072-1101` | H1 在 `noteCommit` 捕获目标 store 的真实 commit tick/seq；H2 在注入时以同一 ptag 先写 `store_commit`（`commit_tick_source=commit_stage_capture`）；H3 在 `completeStore` 后写 `store_writeback_suppressed`（`request_sent=0;mem_sent=0;drain_tick=0;visibility_state=NEVER_WRITTEN`），不冒充 writeback；H4 删除 `caller_supplied` 回退 | 只读；不改 LSU 调度/commit/replay/注入 | 有（新 Binary SHA） | 5 Fault + 5 Control；断言 commit_tick<inject_tick、commit 身份一致、suppressed 负证据齐全、reload 旧值 `a8c7f832281a39c5`、oracle 逐字节不变 |
| T3 | RP01 | R01–R05 | watchdog 走 `fatal()`→`::exit(1)`，跳过 Python atexit/C++ exit callback：终止记录与 gzip trailer 未写。终止前历史节点并未丢失（逐节点 `Z_SYNC_FLUSH`）。 | `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc`, `CHAOSPropagation.cc/.hh` | `rp01Watchdog`, `flushWatchdogTerminal`, `maybeSkipPartialReplay` | `CHAOSLSQFwd.cc:612-629`（fatal 在 627）；`CHAOSPropagation.cc:66,190-220` | 在 `fatal()` 前调用幂等 `flushWatchdogTerminal(info)`：写 `trace_flush_start` / `watchdog_terminal` / `trace_flush_complete`，记录 trigger/reason/fault_id/last event id/last dyn inst/replay eligibility/decision/skip/LQ-SQ 状态/progress；随后 `gzflush` + `gzclose`（保证容器完整）；保留 `TRACE_INCOMPLETE` 语义 | 只读快照；不改 replay 决策/调度/注入；无锁 | 有（新 Binary SHA） | 5 Fault + 5 Control；断言三类节点各 1 条、顺序正确、prev_last_event_id=5282/5486/5690/5894/6098、terminal_source=MODEL_INTERNAL_WATCHDOG、exit=1/timed_out=false、TRACE_INCOMPLETE 不升级 |
| T4 | A03/SP05/RP01 | 全部 | 新事件未被最终 CSV/Readiness 汇总正确解析；QUALIFIED/TRACE_INCOMPLETE 语义可能被误升级。 | `tools/lsu_v333_qualified.py`, `tools/lsu_v333_propagation.py`, `tools/lsu_v333_launch.py`, 新 `tools/lsu_v333_trace_closure.py` | `_a03/_sp05/_rp01`, `trace_row/a03_row/rp01_row`, `collect_task` | 见各文件 | Collector 解析新 kind；最终 CSV 区分 `COMPLETE_CAUSAL_CHAIN` / `VALID_TERMINAL_CHAIN` / `QUALIFIED` / `TRACE_INCOMPLETE`；SP05 的 writeback 负证据只作为"机制已证明"，不自动升级 PASS | 无（分析工具） | 无 | 60 Context 重算；11 个受限 Context 逐项人工核对；统计数与原始证据一致 |

### 关键判定（诚实边界）

- **A03-R02 不改判 SQUASHED**：squash 只截断 13718 等 10 个投机实例；13772 的错误字节 `0xab` 已提交并进入最终 checksum。终态为 `SDC`，链为 `COMPLETE_CAUSAL_CHAIN`（以 13772 为锚），同时保留 13718 的 squash provenance。
- **SP05 不伪造 writeback**：五个 Context 会获得真实 commit + "写回被抑制"的独立负证据 + reload 旧值 + consumer commit + oracle。按冻结规则，`writeback_event` 仍缺，状态仍为 `QUALIFIED`；最终分类为 `VALID_TERMINAL_CHAIN`（机制型完整链），不得写成 `COMPLETE_CAUSAL_CHAIN` 或 `PASS`。
- **RP01 仍为 `TRACE_INCOMPLETE`**：flush 补齐的是"终止记录集"，不是"完整正常 trace"。终态为 `HANG_WATCHDOG`；链分类为 `VALID_TERMINAL_CHAIN`，`TraceCompleteness=PARTIAL_WATCHDOG`，不得升级。
- 其余 49 个 Context 沿用历史 Pre-Formal 证据，但最终 CSV 必须逐行标注 BinarySHA 与 EvidencePath；正式 Campaign 将全部 120 次用新 Binary 重跑，不与旧 Pilot 混合。

## 2. 实施单元（一次性批量，单次编译）

- [x] U1（C++/SP05）：`CHAOSPropagation.hh/.cc` 增加 `StoreCommitObs`、`store_commit_obs`、`noteSP05WritebackSuppressed`、H1/H2/H4。
- [x] U2（C++/SP05）：`lsq_unit.cc` SP05 分支在 `completeStore` 后调用 suppressed 记录。
- [x] U3（C++/RP01）：`CHAOSPropagation.hh/.cc` 增加 `WatchdogTerminalInfo`、`flushWatchdogTerminal`、`last_node_tick`/`last_commit_*` 只读簿记。
- [x] U4（C++/RP01）：`CHAOSLSQFwd.hh/.cc` 在 `rp01Watchdog` 的 `fatal` 前调用 flush；`maybeSkipPartialReplay` 记录 last eligible；构造期记录 armed tick/cycles。
- [x] U5（Python/A03）：`_scan_prop_trace` 保留 `errant_commit`；`_a03` 锚点回退；保留 13718 provenance。
- [x] U6（Python/SP05）：解析 `store_commit` / `store_writeback_suppressed`；`commit_event` 接受真实 commit；新增 `writeback_suppressed` 证据；不升级 PASS。
- [x] U7（Python/RP01）：解析 flush 三节点；新增 `trace_flush_start/complete`、`watchdog_terminal`、`last_valid_event_id` 证据；保持 TRACE_INCOMPLETE。
- [x] U8（Python/最终汇总）：新 `tools/lsu_v333_trace_closure.py` 生成两份最终 CSV 与验证 CSV。
- [ ] U9（文档/交付）：最终报告、provenance、独立验收、ZIP。

## 3. 编译与冻结（只编译一次）

编译前保存：HEAD、`git diff`、旧 Binary SHA、旧 Config SHA、Workload ELF SHA。
命令：`cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`（clean 必须 -j16）。
编译后保存：新 HEAD、完整 build log、新 Binary SHA、Config SHA、Workload ELF SHA。
新 Binary 成为后续正式实验唯一候选；不得与旧 Binary 正式结果混批。

## 4. 定向验证（40 次）

| 组 | 内容 | 运行数 |
|---|---|---:|
| G1 | A03-R02 Fault + Control | 2 |
| G2 | SP05 R01–R05 Fault + Control | 10 |
| G3 | RP01 R01–R05 Fault + Control | 10 |
| G4 | 其余 9 模型（A01/FW02/FW05/MD04/SQ01/SQ03/LP01/LQ04/DA04）各 R03 Fault + Control | 18 |
| 合计 | | 40 |

- 全部使用冻结命令（`command.txt`/`summary.json.fault_command`），仅替换 `--outdir` 到 `audit_v3_3_3/trace_closure/runs/<RunID>`。
- 不覆盖 `audit_v3_3_3/runs/**`；不重跑已有 120 次 Pre-Formal。
- 每组断言：exit/status、oracle、injection_count、Control 零注入、新事件字段、无重复/丢失、无 SIGSEGV。

## 5. 最终验收分类

- `COMPLETE_CAUSAL_CHAIN`：从故障激活到应用层终态的完整数据消费者链（A03-R02 = 是）。
- `VALID_TERMINAL_CHAIN`：终态真实可解释、但机制型/终止型（SQUASHED、HANG、MASKED、lost-writeback suppressed）。
- `QUALIFIED`：证据可读但冻结必填字段仍缺（SP05 的 `writeback_event`）。
- `TRACE_INCOMPLETE`：watchdog/截断（RP01）。

最终必须回答 §11 的 9 个问题，并给出 `READY_FOR_FORMAL_EXPERIMENT` / `READY_WITH_DOCUMENTED_LIMITATIONS` / `NOT_READY`。
若 SP05 的 `writeback_event` 语义不获研究者修订，最终状态只能为 `READY_WITH_DOCUMENTED_LIMITATIONS`，不得伪造 PASS。
