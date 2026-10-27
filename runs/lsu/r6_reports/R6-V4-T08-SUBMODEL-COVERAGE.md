# T08 复合模型四子模型动态覆盖（R6-V4 辅助 canary）

> 辅助证据，**不冒充**官方 T08 正式 seed。官方 `T08-F0-W4` / `T08-F4-W4` 的 3 seed
> 仍以 `walk_pairing`（矩阵默认子模型）运行；本文件的 canary 只用来证明 b/c/d
> 三个子模型在冻结实现里**确实可被动态触发**，从而让 `--t08-submodels-proven`
> 证据包有据可依（`tools/lsu_campaign.py::t08_submodel_evidence_ok`）。
> Bundle：`runs/lsu/r6_reports/R6-T08-SUBMODEL-COVERAGE.json`。

## 覆盖矩阵

| 子模型 | fault_type | 证据目录（seed1） | 触发签名（真实事件） | 覆盖判定 | 说明 |
|---|---|---|---|---|---|
| T08-a walk_pairing | `walk_pairing` | `runs/lsu/r6_v3_T08-F0-W4_s1/T08-F0-W4/seed1` | `inj(walk_id=703)`→`tlb_walk`→`tlb_refill field=lost outcome=lost`→`tlb_translate_result` | **covered** | 上一轮代表 canary（二进制 `20fda699…`）；本轮官方 seed1 在 `e379cc5b…` 上复现（`r6_v4_T08-F0-W4_s1`，见其传播文档） |
| T08-b walk_fill_dup | `walk_fill_dup` | `runs/lsu/r6_v4_canary_T08b-fill-dup/seed1` | `inj walk_id=703`→`tlb_walk`→`tlb_refill field=walk_fill_dup outcome=duplicated`→`tlb_translate_result` | **covered（弱效应）** | 第二次 `mmu->insert` 未单独打点；效果是重复占用/重复插入，不产生错误翻译。oracle 通过（`rounds ok=10/10`）。 |
| T08-c walk_done_early | `walk_done_early` | `runs/lsu/r6_v4_canary_T08c-done-early/seed1` | `inj walk_id=703`→`tlb_walk`→`tlb_refill field=walk_done_early outcome=early_done`（refill tick := walk start tick）→`tlb_translate_result` | **covered（仅注解）** | **该子模型不改任何模拟状态**：只把 trace 里的 `refill_tick` 标成 `walk_start_tick`。覆盖判定只能写“变体被执行、按设计零硬件效应”，不得写成“故障发生了传播”。 |
| T08-d walk_stale_result | `walk_stale_result` | `runs/lsu/r6_v4_canary_T08d-stale-result/seed1` | `inj walk_id=703`→`tlb_walk`→`tlb_refill_stale old_pfn=0x8001e stale_pfn=0x8002f outcome=stale`→`tlb_translate_result pa=0x8002f240` | **covered（真实错 PA）** | 把上一条 walk 的 PFN 写进当前表项；下游翻译拿到 stale PA。 |

- 三次 canary 均为**直接 gem5 CLI**、独立新目录、`--tlb_max_faults 1`、F0 一次性、
  `--tlb_rng_seed 1`、同一 checkpoint/`tlb_probe.rcS`。
- 二进制：T08-b / T08-c canary 跑在 `b13a60ab…`（首轮统一构建）；T08-d canary 跑在
  `e379cc5b…`（归因修复后的第二轮统一构建）。每个目录的 `*.log` 首行记录实测 SHA；
  三者均为 rc=0、`rounds ok=10/10`。walk 模型不经 attrib 门（该门只作用于
  state/attr/CAM），因此 b/c 在两版二进制上的行为一致。
- canary 不使用 campaign（campaign 的 T08 门只服务官方 RunID）；它们不是第 4 个
  正式 seed，也不解锁 W9。

## 诚实边界

1. **T08-c 没有硬件效应**：这是模型设计（timing-only 注解），不是覆盖缺口；若项目要求
   它扰动时序，需要单独立项改模型，而不是宣称“已传播”。
2. **T08-b 的重复插入未单独打点**：证据是注入器自己的 `duplicated` 标注与
   `tlb_refill` 事件，不是第二次 `insert` 的独立事件。
3. **T08-d 的 stale pfn 来源**是 refill 时刻的 `last_walk_pfn`；证据记录 old/stale 两个
   pfn 值，可复核。
4. 三个 canary 的 oracle 均为 `rounds ok=10/10`（Masked）；没有把它们计入 SDC/崩溃统计。
