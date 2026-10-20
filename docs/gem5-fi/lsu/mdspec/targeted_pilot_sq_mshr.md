# 定向 pilot：Store Queue 节点补证 + Cache mshr_alloc 追证（真实运行）

> 目的：让 98 个 PARTIAL 按**真实证据**重判——此前 Store Queue 只观测到
> `lq_*`/部分节点，Cache 缺 `mshr_alloc`。

## 1. Store Queue：`sq_writeback` / `sq_complete` 已取得真实证据

关键发现（实测）：`sq_execute/sq_writeback/sq_complete` 三个钩子都靠
`correlateRequestBySeq(dyn_seq)` 关联**由某个注入器开设的链**。
**`CHAOSLSQFwd`（S01/S02/S03/S08/S09）从不注册链**（`CHAOSLSQFwd.cc` 里
没有 `registerInjection`/`notePropEvt` 调用）——所以用 S01-F0-W5 跑，PRPO-EVT
流**恒为空**（实测 activated=0 且 prop_evt 无内容），这不是钩子问题而是
S 系注入器未接入追踪器。

而 S04–S07/S11/S13 走 `--agu_pre_mode`（PRE 家族），其路径**会在
`lsq.cc::pushRequest` 注册链**，因此能观测 SQ 节点。实测（正式 campaign 入口）：

| RunID | 载体 | 事件（种类） | SQ 节点 |
|---|---|---|---|
| S04-F0-W5 | sq_forward | inj, addr_form, lsq_push, lsq_sendfrag, mem_req, tlb_translate, resp, **sq_writeback, sq_complete**, chain_end | 2/3 |
| S05-F0-W5 | sq_forward | 同上 | 2/3 |

→ **Store Queue 单元能力 4/7 → 6/7**（新增 `sq_writeback`、`sq_complete`）。

## 2. `sq_execute` 仍未观测（如实记录，未伪装）

`sq_execute` 位于 `lsq_unit.cc::executeStore`。S04/S05 两次真实运行均**未出现**。
可能原因（未定论，需专项排查）：store 执行与该 chain 的注册**时序**——注册发生在
`pushRequest`（PRE 钩子），而 `executeStore` 若在同一拍或注册可见前触发，
`correlateRequestBySeq` 取不到条目即不发事件。**这是待查项，不是已完成项。**

## 3. Cache：`mshr_alloc` 仍未观测（含机理说明）

尝试矩阵（全部真实运行，均为直驱 + propagation）：

| 配置 | 注入数 | 观测到的 cache 节点 | mshr_alloc |
|---|---|---|---|
| C09-F0-W10（campaign, stream_chase） | 4 | cache_access/return/evict/writeback/lq_complete/resp/taint | ✗ |
| cache_dirtyevict @first_clock=100 | 0 | （窗口未开，无有效行） | ✗ |
| stream_chase @first_clock=100 | 0 | 同上 | ✗ |
| cache_dirtyevict @5000 / 20000 周期 | 2 / 2 | cache_access/return/evict/writeback | ✗ |
| stream_chase @5000 / 20000 周期 | 2 / 2 | 同上 | ✗ |

**机理（实测得出，非猜测）**：CHAOSCache 的故障注入点是**已存在的 valid line**
（规格 "L1D 存在 valid line"），因此**被注入那一行本身不会 miss** → 不会为该行
分配 MSHR。要在同一行上观测 `mshr_alloc`，必须让该行**先被驱逐、再被重新取回**
（evict→refill）；本次多次尝试的样本里驱逐后没有再次取回同一行。
> 注：`first_clock` 单位是**周期**（1000 → tick 1e6），先前用 5e5/2e6 当 tick
> 导致窗口跑到运行结束之外（inj=0），已纠正后确认注入正常。

**结论**：`mshr_alloc` 事件已实现且曾在他处出现，但**在 C 系定向样本中仍未取得
观测证据** → 覆盖矩阵如实保留 `unobserved:mshr_alloc`，90 项 PARTIAL 因此不升级。
建议下一步：用 W6(2×L1D working set) 或打通 FS 的长样本，构造"故障行被驱逐后再取回"。

## 4. 覆盖矩阵变化（证据化口径）

| 单元 | 需要节点 | 已观测（本轮前 → 本轮后） | 仍缺 |
|---|---|---|---|
| Store Queue | 7 | 4/7 → **6/7** | `sq_execute` |
| L1d-Cache | 11 | 10/11 → 10/11 | `mshr_alloc` |
| 其余 5 单元 | — | 不变 | AGU/TLB/LQ/P 全观测；原子与同步缺 `atomic_op` |

PASS/PARTIAL/BLOCKED 计数不变（101/98/126）——**因为单元 PASS 要求该单元
全部节点均有证据**；本轮把 Store Queue 的缺口从 3 个减到 1 个，但未归零，
故仍如实标 PARTIAL（不因"大部分节点已证"就判完成）。
