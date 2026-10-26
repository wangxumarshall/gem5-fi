# R6-LINCHECK — 把 O(n) 最佳有序路径并入权威 checker

**日期**: 2026-10-24 · **Lane**: FIX-LINCHECK · **分支**: `r6-lincheck`（base `8f70d163`）
**独占**: `tools/lsu_chain_check.py`、`tests/test_lsu_chain_check.py`、`tests/test_lsu_r6_reconcile_realroot.py`
**禁止**: 改 `tools/lsu_campaign.py`（Lane1）、C++（Lane3）、跑 gem5、push 集成分支。

## 问题（真实缺陷）

`lsu_chain_check._best_ordered_path` 对**每个事件**各做一次祖先遍历（`_ancestry`）
+ 贪心前缀（`_ordered_prefix`）⇒ Θ(n·depth)。`runs/lsu/r6_w1b_T04-{F0,F2,F6}-W4/.../seed1`
各 568,093 事件、祖先深度 ≈12,800 ⇒ 原版 checker **跑不完**（20k 前缀实测 25.5 s，
整文件 >16 CPU-分钟未完成）。目前只有 `lsu_campaign.py` 的临时替换
（`_LinearPathSwap`）绕开，**权威 checker 本身仍是 Θ(n·depth)**。

## 任务分解（一 patch = 一 commit）

- [x] **T1** `tools/lsu_chain_check.py`：把已由 Lane1 验证过的 O(n) 线性搜索
      **正式并入权威 checker**：
      * 原实现更名 `_walk_best_ordered_path`（**逐字节保留**，作为等价参考与回退）；
      * 新增 `_linear_best_ordered_path`（记忆化前缀状态，O(n)）；
      * `_best_ordered_path` = 线性入口，仅在**可证不等价**的两种输入上
        回退到 `_walk_best_ordered_path`（重复非空 event_id、父图有环）。
      不改任何规则：`chain_end` 仍不充当 L5、截断流不准入、bridge 完整核验、
      `cross_request_edge`/`invalid_lineage_bridge`/`time_reversed_edge` 仍严格拒绝。

- [x] **T2** `tests/test_lsu_chain_check.py`：新增等价性 + 规模套件
      （合成多形状 + 全部现存小流 + 3 条 T04 seed1），断言
      `terminal`/`provable_to`/`path_event_ids`/`admitted`/`violations` 逐条一致。

- [x] **T3** `tests/test_lsu_r6_reconcile_realroot.py`：确认其
      `CC._best_ordered_path` 用法在新入口下仍绿（若需，仅加等价性断言）。
      结论：**无需改动** —— 其 `CC._best_ordered_path(_ch04, _fam04)` 调用在新入口下
      逐字段一致，套件保持 `ALL PASS`。

## 验证命令（真实输出为准）

1. `python3 tests/test_lsu_chain_check.py` → `ALL PASS`
2. 等价性：新 checker vs base commit(`8f70d163`) checker，在**全部小流**上
   `terminal/provable_to/path_event_ids/admitted/violations` 全等（N/N）。
3. 正式结果：新权威 CLI 对 3 条 T04 seed1 跑出 terminal/admitted/violations + 耗时。
4. `python3 tools/lsu_test_runner.py` → **NEW FAIL=0**（基线 66/12/53/1）。
5. `python3 tests/test_lsu_campaign_large_stream.py` → `ALL PASS`（未改动 campaign）。

## 停点

任一不一致 ⇒ 立即停止汇报（用户列明停点）。
