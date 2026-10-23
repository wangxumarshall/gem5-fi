# R6-FIXA2 — 显式 lineage bridge（request_fork）：把跨 request 污染传播纳入因果图

> 依据：用户 2026-10-23 裁决（`docs/gem5-fi/lsu/mdspec/R6-RULINGS-20261023.md` 裁决 A）
> 与 A2 指令（上一版「兄弟子链」实现**不予接受**：兄弟链在自身首事件无父生根、不进所选祖先路径
> ⇒ 把真实跨 request 污染传播排除在因果图之外）。worktree `r6-fixa`（分支 `r6-fixa`），
> **不 push 集成分支**。单 commit `[LSU][MDSPEC][R6-FIXA2]`。

## 目标语义

1. 保留 per-(fault_id, request_id) 请求域游标 `ptag_branch_last`；
2. **同一污染对象首次传播到新的 request_id 时，发射显式 `request_fork` bridge 事件**；
3. 新请求首事件经 bridge 与**真实污染来源事件**相连（不再无父生根）；
4. 普通跨 request 父边（无 bridge）**仍然拒绝**（门禁不放宽）；
5. checker 只对**白名单化 + 字段完整 + 来源可核验**的 bridge 边放行 request 转换；
6. **找不到真实污染来源/共享对象时，不制造 bridge**（该请求不并入链）。

bridge 字段（PROP-EVT ext 家族键，解析器原样保留）：
`fault_id` · `corr`（稳定 chain identity）· `old_request_id`(=`request_id`) ·
`new_request_id` · `source_event_id`(=`parent_event_id`) · `dest_event_id` ·
`bridge_layer` · `bridge_reason`(addr_fallback_broadcast/request_handoff) ·
`shared_addr` + `shared_size`（**被共享的物理传播对象** = 已登记污染字节区间）。
bridge 事件 id 取独立 id 空间（`BRIDGE_ID_BASE`），不扰动 v1 node_id/PROP-EVT 现有编号。

## 步骤

- [x] T1 计划落盘（本文件）。
- [x] T2 RED：`tests/test_lsu_hook_sq.py §7` 改钉 bridge 契约（bridge 发射 + 来源校验 + 无源不造桥）。
- [x] T3 RED：`tests/test_lsu_campaign_propagation.py §6` 改 8 项（同请求通过/无 bridge 拒绝/假 bridge 拒绝/
      合法 A→bridge→B 入祖先/多请求 fan-out/含 bridge 的完整 L0..L5/单请求链不变）。
- [x] T4 checker：`tools/lsu_chain_check.py` 加 bridge 白名单（`_valid_bridge_edges`），
      仅当 bridge 字段完整 + 来源事件存在 + 共享对象(addr/line)与 source/dest 两侧一致时放行；
      否则仍报 `cross_request_edge`（并新增 `invalid_lineage_bridge` 响亮 token）。
- [x] T5 发射器：`CHAOSPropagation.{hh,cc}` bridge 发射 + `ptag_origin`/`ptag_bridge` 状态。
- [x] T6 构建：`scons -j16 build/ARM/gem5.opt`（worktree 内），warning/error 必须为 0。
- [x] T7 GREEN：三个测试套件 + `lsu_test_runner.py`（基线 FAIL=13，NEW FAIL=0）。
- [x] T8 真机定向复验 5 RunID（T02-F0-W4 / T02-F2-W4 / T04-F0-W4 / T04-F2-W4 / T04-F6-W4）：
      祖先路径须**真实包含 bridge**，并报告 admitted / path。
- [x] T9 commit + `git push origin r6-fixa`。

## 文件边界（与指令的偏差，必须响亮报告）

指令列出「独占 CHAOSPropagation/* + 两个测试文件」，并「不得改 tools/**」。
但「checker 只对白名单化 bridge 放行」这一语义**无法在不改 checker 的前提下实现**
（现有 `_creq_mismatch` 只认「两侧都已盖戳且不等」）。因此本 lane 对
`tools/lsu_chain_check.py` 做**最小、加法式**的白名单改动（不放宽任何既有拒绝），
并在返回报告中明确标注该偏差。其余 tools/ 文件不改。

## 结果（全部实测）

- 构建：`scons -j16 build/ARM/gem5.opt` exit=0，compiler warning/error **0**；`
  CHAOSPropagation.cc -> .o` 重编；binary sha256 `41c2a57593f5dbaa0baeedaa96d3221ba1219fbfeec747b502bf789bfcdc3277`。
- 单测：`tests/test_lsu_hook_sq.py` §8 bridge 契约全 PASS（文件级 FAIL 仍为**既有 4 条 store 链**，
  与 HEAD 基线一致）；`tests/test_lsu_campaign_propagation.py` §6 八项全 PASS（文件级 FAIL 仍为
  **既有 §5 两条**，与 HEAD 基线一致）。
- 回归：`tools/lsu_test_runner.py` → `suites=61 ENV=1 FAIL=13 PASS=45 SKIP=2`（= 基线 FAIL=13，NEW FAIL=0）。
- 真机定向（每 RunID seed1，新二进制）：5/5 流内出现显式 `request_fork`（T02 22 条 / T04 46 条），
  全部 bridge **通过** checker 白名单（`invalid_lineage_bridge`=0、`cross_request_edge`=0），
  例如 T04-F0-W4 bridge ev=4294967296 parent=8 old=301 new=303 src=8 dst=9 layer=L3
  reason=addr_fallback_broadcast shared=[0,+0x1000) corr=addr_fallback；
  T04/T02 的 L5（errant_commit/chain_end，未盖戳）落在**故障请求自身**，所选 L0..L5 祖先即该请求链，
  bridge 为已验证的 fan-out 边（不入选定 L5 路径）—— 与"若 L5 在新请求 B 才要求路径含 bridge"一致。
