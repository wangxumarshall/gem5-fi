# LSU v3.3.3 — Qualified Evidence Disclosure (A03 / SP05 / RP01)

**Date:** 2026-11-12  
**Scope:** disclosure only. No model, trace, summary, oracle log or
C++ source was modified. No `QUALIFIED` / `TRACE_INCOMPLETE` state is
upgraded to `PASS`.

## 1. 状态总表（pre-formal 证据）

| Model | R01 | R02 | R03 | R04 | R05 |
|---|---|---|---|---|---|
| A03 | PASS | QUALIFIED | PASS | PASS | PASS |
| SP05 | QUALIFIED | QUALIFIED | QUALIFIED | QUALIFIED | QUALIFIED |
| RP01 | TRACE_INCOMPLETE | TRACE_INCOMPLETE | TRACE_INCOMPLETE | TRACE_INCOMPLETE | TRACE_INCOMPLETE |

来源：`audit_launch_fix_v333/artifacts/LSU_QUALIFIED_Context_Handling.md`
（由 `tools/lsu_v333_qualified.py` 对每个 run dir 直接调用生成）。

全 60 上下文的 trace 完整度：**50 `COMPLETE` + 5 `COMPLETE_PROP_TRACE`
(A03) + 5 `PARTIAL_WATCHDOG` (RP01)**。

## 2. A03 — persistent stuck-at address

### 2.1 已证明的事实

- 五个 fault 都打印了最终应用校验和，且全部 ≠ golden `728e604ffcec539d`；
  实测 checksum：R01 `1cf7a5a9f11dab7e`、R02 `d48b947fc08d5a75`、
  R03 `bfccf156021968dd`、R04 `e413c2be501846bc`、R05 `d5529b13a7c739dc`。
- 五个 control 全部打印 golden。
- 终态为 `SDC` / `ORACLE_FAIL`，限定词 `POST_ORACLE_SIM_HANG`。
- R01/R03/R04/R05 的 first affected load 具备 `resp` → `taint_reg` →
  `prop_edge` → `consumer` 的完整 downstream 链（PASS）。
- 必须区分三个事件：`stuck_at_active`（stuck 状态激活）、
  `selected_event_first_activated`（选中事件首次激活）、
  `first_downstream_instruction_affected`（首个受影响下游指令）。
  collector 只有在三者是不同记录时才判 PASS。

### 2.2 尚未证明的传播环节

- **R02：** first `STUCK_APPLIED` load（dyn seq 13718）在产生 response 前
  被 squash（`squash_cause=unrelated`），因此没有该 dyn seq 的 `resp`、
  `taint_reg`、`consumer` 节点。R02 的 load result / register writeback /
  consumer 三个必填字段缺失 → `QUALIFIED`。
- 这说明「stuck 激活」与「下游消费者可观测」之间并非每个上下文都能闭合；
  不能宣称 5/5 的 A03 传播链完整。

### 2.3 正式实验能补充什么

- 正式 run 会重新采集 `summary.json.a03`、`addrpath_injections.log`、
  完整 `prop_trace`、`oracle.log`、`stdout.log`。
- 若正式 run 中 R02 的 first affected load 仍被 squash，则仍为 QUALIFIED；
  collector 不会因为「正式」而升级状态。
- 可选（需研究者批准，本阶段未做）：选择 non-squashed first affected load
  属于上下文设计决定，不是 collector 默认行为。

### 2.4 论文表述建议（若仍缺失）

> A03 的五个上下文中，四个可观测到 stuck-at 激活 → 首个受影响 load →
> 寄存器回写 → 消费者的完整下游链，并产生与 golden 不同的最终校验和；
> 第五个上下文（R02）的首个受影响 load 在写回前被无关 squash，
> 下游链不可观测，按 QUALIFIED 披露，不计入完整链统计。

### 2.5 对有效性与贡献的影响

- 不影响 A03 终端结论（SDC）的有效性：校验和差异是直接的架构证据。
- 影响「完整传播链」计数：A03 只能计 4/5 完整链。

## 3. SP05 — store premature completion / lost writeback

### 3.1 已证明的事实

- 5/5 fault：`completeStore` 触发，`storesToWB 1→0`，`mem_sent=0`，
  `write_skipped=1`，无 `store_mem_write`。
- reload 读到零值（`a8c7f832281a39c5`），consumer 可见，oracle FAIL 5/5。
- `store_data_fnv` 已在 `summary.json` 与 `trace_v31.jsonl` 中出现
  （R01 `b6180e0c195fd2e9`、R02 `9f995d89be67e92d`、
  R03 `fde383c67ac034f1`、R04 `aa2be3d3d60e3c9d`、
  R05 `c7d78aff5e06edf9`），即批准条件中的 store-data 绑定已满足。
- trace 完整度为 `COMPLETE`，记录完整性 `VALID`。

### 3.2 尚未证明的传播环节

- **没有独立的 store commit 事件。** 唯一的 commit 时间是
  `commit_tick_source=caller_supplied`，`commit_status=UNKNOWN`；
  这是注入调用时间，不是 commit 观测。
- **没有独立的 store writeback / memory-write 事件。**
  `sp05_write_skipped` 只能证明 writeback 没有发生，
  不能作为「writeback 发生了」的正向证据。
- 因此 commit → writeback → visibility → reload → consumer 的链条中，
  前两个环节缺失 → 5/5 `QUALIFIED`。

### 3.3 正式实验能补充什么

- 正式 run 会重新采集同一组字段；但当前 C++ 记录路径没有 store-commit
  与 store-writeback 观测 hook，因此正式 run **不会自动**补齐这两个字段。
- 若要补齐，需要新增两个观测 hook（需研究者批准）：
  (a) `commitStores` observer → `store_commit` 节点；
  (b) drain/writeback observer → `store_writeback` / memory-write 节点。
- 本阶段按用户要求不修改 C++，也不把 QUALIFIED 升级为 PASS。

### 3.4 论文表述建议

> SP05 的五个上下文均观测到 completeStore 的写跳过与 reload 读取零值，
> 并以应用 oracle FAIL 终结；store 数据值可绑定，但记录路径缺少独立的
> commit 与 writeback 事件，故其传播链按 QUALIFIED 披露，
> 不作为「commit→writeback 完整链」的证据。

### 3.5 对有效性与贡献的影响

- 不影响 SDC 终端结论的有效性（reload 零值与 oracle FAIL 可复现）。
- 影响「完整传播链」贡献：SP05 的 5 个上下文不计入完整链。

## 4. RP01 — replay suppression

### 4.1 已证明的事实

- 五个 fault 都在目标 ordinal 触发一次 skip；九项必填字段全部找到：
  eligibility、decision、faulty replay state、skip、dyn seq、
  LQ/SQ entry、internal watchdog、external timeout、final progress。
- 终态为 `HANG_WATCHDOG`，`TerminalReason=RP01_WATCHDOG_EXPIRED`，
  `checksum=None`；这是模型内 watchdog，不是应用 oracle FAIL。
- `summary.timed_out=false`：**内部 watchdog 与外部 timeout 已严格区分**。
- 五个 control 完成并打印 golden `f3b1c554273d23f7`。

### 4.2 尚未证明的传播环节

- watchdog 通过 `m5_fail` 退出，`prop_trace.csv.gz` 被 gzip 截断
  （`unexpected end of file`），trace 为 `PARTIAL_WATCHDOG`。
- 因此即使九项字段齐全，也不能宣称完整的 post-skip 传播链；
  5/5 为 `TRACE_INCOMPLETE`。
- 五个上下文共享静态 PC/几何，动态执行不同；该「同静态 PC、异动态执行」
  必须在论文中声明。

### 4.3 正式实验能补充什么

- 正式 run 会重新采集 `summary.rp01`、`lsq_fwd_injections.log`、
  `prop_trace`、`summary.timed_out`。
- 若 watchdog 退出路径仍不 flush/snapshot trace，正式 run 仍为
  `TRACE_INCOMPLETE`。
- 要变成 PASS，需要 (a) watchdog 退出前 flush/snapshot，或
  (b) runner 侧在退出前抽取 trace。两者都属于新 hook/工具改动，
  需研究者批准，本阶段未做。

### 4.4 论文表述建议

> RP01 的五个上下文均在目标 ordinal 抑制一次 replay，并由模型内 watchdog
> 终止；`timed_out=false` 证明这不是外部超时。由于 watchdog 退出前 trace
> 被截断，post-skip 传播链按 TRACE_INCOMPLETE 披露，
> 不宣称 hang 之后的完整数据流。

### 4.5 对有效性与贡献的影响

- 不影响「抑制 replay 导致 hang」这一终态的有效性。
- 影响「完整传播链」贡献：RP01 的 5 个上下文不计入完整链。

## 5. 对 60 个正式上下文的总影响

- **60/60** 具备有效配置（SampleRunID、Seed、ROI、ordinal、Fault/Control 配对）。
- **49/60** 的记录完整度不受本披露影响；**11/60** 有明确限制：
  A03-R02（QUALIFIED）、SP05 全部 5 个（QUALIFIED）、
  RP01 全部 5 个（TRACE_INCOMPLETE）。
- 正式 Campaign 的数据仍然有效；但论文的「完整传播链」论证必须：
  (a) 只统计 49 个可完整闭合的上下文，或
  (b) 明确把 11 个作为限定样本单独披露。
- 不得把 QUALIFIED/TRACE_INCOMPLETE 写成 PASS，也不得静默丢弃这 11 个上下文。

## 6. 需要研究者决定的事项（非启动阻塞）

1. 是否接受以 QUALIFIED/TRACE_INCOMPLETE 原样进入正式数据与论文限定。
2. 是否在正式 Campaign 之后授权 SP05 的两个观测 hook 与 RP01 的
   watchdog-trace flush（均需 C++ 改动）。

