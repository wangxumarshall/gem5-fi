# R6-S 单元四条问题线诊断（2026-10-29）

本文件只记录**已由原始证据证明**的根因；未证实的推测明确标注。证据根目录
`/home/sdc/gem5-fi-ding/runs/lsu/r6_s_unit`，冻结二进制
`a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046`
（source head `2498573f`），analysis_tool_head `a92f9f6d`（本轮工具提交后为 `b1036566`）。

## 已交付：21 份 S seed 传播文档

`runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`，7 RunID × 3 seed，
生成器 `tools/r6_s_prop_docs.py`，审计 `tests/test_lsu_s_prop_docs.py`（13 项，
逐 seed 从自身 `prop_evt.txt.gz` 重推 event_id/parent/tick/ancestry/SHA）。

## A 线：LSQ forwarding 链不完整（6 CHAIN_INCOMPLETE + 1 相关 NO_EVIDENCE）

证据（S01-F0-W5_s1，53 事件）：链在 `L1->L2` 断开。

- 真实注入存在：`lsq_fwd_injections.log` 记录 StoreSeq=12086 / LoadSeq=12091 /
  Vaddr=0x7ffffefc30 / ByteOffset=5 / Mask=10000000。
- L0 `inj`（event 0，dyn=12091，load）与 L1 `lsq_fwd`（event 1）真实发射。
- 后续分成三条互不相连的分支：
  1. store 分支：`sq_writeback`(2) → `sq_complete`(5) → `lsq_push`(6，**dyn=13930，另一条指令**)
     —— 跨指令父边，仅靠地址/顺序拼接；
  2. fork 分支：`request_fork`(2^32…) → `mem_req`(7…) → `lsq_sendfrag` → `tlb_translate`，
     corr=`addr_fallback`，属于**后续其它 load** 的请求；
  3. 响应分支：`resp`(3) **parent 为空**（孤儿根）→ `taint_reg`(4，dyn=12086，store)。
- checker 结论：`cross_branch_edge`、`no_closed_chain_and_no_containment`，
  `provable_to=L1`（path=[0,6]），admitted=False。

根因（已证实）：

1. `CHAOSPropagation::registerLSQForwardFault` 只把**生产 store 的 seq** 写入
   `addr_registry`（`CHAOSPropagation.cc:1283-1292`）；**消费 load 的 seq 没有注册**，
   所以 load 自己的 `resp/lq_complete/taint_reg/commit` 永远不会带 fault_id。
2. `lsq_fwd` 在 `tools/lsu_prop_fields.py` 映射为 L3；该 fault 没有任何 L1（SQ 表项）
   或 L2（forward 比较/传输）见证事件 → 从 L0 直接跳到 L3，连续前缀必然断。
3. `noteMemResponse` 的 `resp` 在块匹配路径上没有写 parent_event_id（event 3 为孤儿）,
   使 store 分支的 `taint_reg` 无法被祖先前缀证明。
4. 转发 load **没有内存响应**，因此 `noteMemResponse` 的 `taint_reg`/`taint_set`
   永远不会标记它的目的物理寄存器；`noteCommit` 因而看不到消费者，无法产生
   L5 `consumer`/`errant_commit`。

修复设计（需要 C++，且是一次语义补全，不是 checker 放宽）：

- 在 forward 站点（`CHAOSLSQFwd::writeLog` 已有 store/load 双方的 seq、sq_idx、
  lq_idx、request_id）发射真实 L1 `sq_entry`（store SQ 表项观测）→ L2 `lsq_fwd`
  （转发）→ L3 `resp`（转发数据交回 load）→ L4 `taint_reg`（load 目的物理寄存器）；
- 把 load 目的物理寄存器加入 `taint_set`（等价于内存响应路径），使 `noteCommit`
  在 load 提交时自然产生真实 L5（consumer/errant_commit）；若 load 被 squash，
  则产生真实 L4/L5 containment；
- 保持 store 分支作为旁支，不再依赖跨指令父边（现 event 6 的父边应改为
  `request_fork` 桥，而非 `sq_complete`）。

## B 线：F1/F2/F4 NO_FIRE（20 格）

统一触发器是**周期区间**，不是 eligible 计数
（`chaos_trigger.hh:43-84`：F1=2.6M cycles、F2=260K、F3=26K，±50% 抖动）。
2.6 GHz + 1e12 tick/s ⇒ 385 tick/cycle ⇒ F2 首火下界 ≈100.1M ticks，F1 ≈1.00G ticks。

`tools/r6_s_trigger_census.py` 对 20 个 NO_FIRE 格逐一比对 `stats.simTicks` 与首火下界：

- **15 格 BLOCKED_TRIGGER_REACHABILITY**：整个程序在首火下界之前就结束
  （例如 S04-F2-W0 simTicks=20,429,640 < 100,100,000），加 timeout 不可能触发；
- **5 格 BLOCKED_TRIGGER_SEMANTICS**：F4 三格（枚举无 F4 档，需单独定义）+
  S10-F5-W5/W9（`CHAOS_LSU_TRIGGER_ALARM`：F5 fires=3/4 但 outcomes_recorded=0，
  是 injector 未上报每次 F5 触发，不是未触发）。
- 反证：S13-F1-W1（simTicks=1.94G > 1.0G）与 S13-F2-W1（0.228G > 0.100G）
  确实在区间之后首火 —— 与区间模型一致。

结论：在现有 workload 运行长度契约下，没有 NO_FIRE 格能在有界预算内变成 PASS；
不加无限 timeout，也不判 PASS。

## C 线：S13 Crash 未闭合（6 格）

S13-F0-W1/W5/W12、F1-W1、F2-W1 证据一致（10 事件）：

`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate →
tlb_fault(Hardware) → sq_execute → arch_translation_fault(L2, outcome=arch_exception,
contained=0) → chain_end`。

- 注入真实（`s13_store_addr`，new_addr=0x20004d2c98 等未映射地址），
  guest 因该异常的 `exit_code=1` 真实 Crash；
- 但 checker 的 6 层契约要求连续 L0→L5；`arch_translation_fault` 被 D1 规则提升为
  L5 观测点，而 L4（内存可见副作用）**结构上不存在**——翻译阻断发生在任何访存副作用之前；
  因此连续前缀停在 L3，`provable_to=L3`，admission 拒绝
  （`no_closed_chain_and_no_containment`）。

这不是“缺事件”，而是**终局语义缺口**：翻译阻断型 Crash 的 L4 是 N/A，现有 admission
没有 crash 终局类。两种处理都需要裁决：

1. 新增“translation-blocked crash”终局类（有真实 L5 异常事件 + 真实 ancestry，
   L4 记为结构化 N/A）——这会扩展准入规则；
2. 保持 BLOCKED，等待规格对 L4 N/A 的显式许可。

按用户工作令“需要放宽准入规则必须停下”，本轮**未**单方面修改 admission。

## D 线：S08-F0-W5 FAIL_OTHER（1 格）

证据：`run.out` 显示 `CHAOS_LSU_TRIGGER ... injected=1`，
`lsq_fwd_injections.log` 记录 `Site: store->load_forward_decision,
FaultType: fwd_source_sub ... faults_injected: 1`，但 `prop_evt.txt.gz` 只有表头
（event_count=0），`chain_report` 无 faults/admitted/certified。

根因（已证实）：`fwd_source_sub` 在**决策点**注入
（`CHAOSLSQFwd.cc:498-570`，`maybeSubstituteSource`），该路径自己写
`lsq_fwd_injections.log`，但**不调用** `CHAOSPropagation::registerLSQForwardFault`，
也不发射 `lsq_fwd`；`writeLog`（唯一的 tracer 汇点，`:303-350`）被该模式显式短路
（`corrupt()` 在 `FwdSourceSub` 模式直接 return，`:374`）。所以注入发生了，
事件流为空。

修复设计：把 `FwdCorrelKeys`（store/load seq、sq_idx、lq_idx、request_id）传入
`maybeSubstituteSource`，在注入成功后走与 `writeLog` 相同的注册/发射路径。
该修复与 A 线的发射器补全共用同一段代码，应在一次统一构建中完成。

## 下一步（需要一次统一 C++ 构建）

1. 失败测试先钉住：forward 注入必须产生 `inj` 起点且 chain 至少到 L2；S08 注入必须
   产生 ≥1 个 PROP-EVT；
2. 实现 A 线发射器/消费者补全 + D 线注册；
3. 统一构建一次（detached tmux、日志落盘、零新增告警、新 SHA 独立记录，旧二进制保留）；
4. 只重跑 6 个 CHAIN_INCOMPLETE（S01/S02/S09/S10-F0-W5、S11-F0-W5）与 S08-F0-W5，
   seed1 验收后补 seed2/3；
5. C 线等待规格裁决后再动 admission。
