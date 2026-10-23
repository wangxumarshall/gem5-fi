# R6-FIXA — 发射器父边按请求域（消除 addr_fallback 跨请求父子边）

> 依据：用户 2026-10-23 Lane A 指令（5 lane 复现、冻结二进制 `6469bad2…`）。
> worktree `.claude/worktrees/r6-fixa`（分支 `r6-fixa`），集成分支 `lsu-mdspec-20261019`（**不 push 集成分支**）。
> **独占文件**：`CHAOS/gem5/src/cpu/o3/CHAOSPropagation/*`、`tests/test_lsu_campaign_propagation.py`、
> `tests/test_lsu_hook_sq.py`。**不得**改 `tools/**`、`src/arch/arm/CHAOSArmTLB/*`（Lane C 独占）。
> 最小构建单元（one patch per unit）→ 单 commit `[LSU][MDSPEC][R6-FIXA]`。

## 根因（真实数据复现，非推测）

`CHAOSPropagation::emitPropEvt` 用单一 `ptag_last_event[fault_id]` 游标作 `parent_event_id`，
于是同一 fault 下**任何**事件都挂到上一个事件之下——包括 `addr_fallback` 广播（一条被污染 line/PA
被多请求读到）产生的、`request_id` 完全不同的访问。实测（`tools/lsu_chain_check.py` 的
`check_admission`，**门禁一行未改**）：

| 真实流（冻结二进制产物） | terminal | path_layers | cross_request_edge |
|---|---|---|---|
| `runs/lsu/r6_p1_T04-F0-W4/T04-F0-W4/seed1` | detected_contained | L0..L5 | 30 处（首例 event 8:mshr_alloc req=301 → event 9:cache_access req=303）|
| `runs/lsu/r6_p1_T02-F0-W4/T02-F0-W4/seed1` | detected_contained | L0..L5 | 31 处 |
| `runs/lsu/r6_p1_T04-F2-W4`, `..._T04-F6-W4` seed1..3 | detected_contained | L0..L5 | 同形 |

即：这些格**已经有完整 L0→L5 + containment**，仅因跨请求拼接被硬门禁拒绝。

## 选路：发射器侧请求域父边（保留广播，改为同 fault 下的兄弟子链）

选 (a)+(b) 的合体而非“删除广播”：广播在物理上真实存在（一条污染 line 被多请求读），
删除它会伪造证据；因此**保留**广播事件，但把它们表达为**同一 `fault_id` 下、各自在自身请求首现处
生根的兄弟子链**，而不是挂在别的请求事件之下的父子边。

- 分支键 `branch_key` = 事件自身盖戳的 `request_id`；未盖戳的生命周期事件（lsq_push / sq_* /
  taint_reg(部分) / resp(部分) / errant_commit / chain_end / consumer）归属**链的 owner 请求**
  （= 该 fault 首个盖戳请求，即故障请求）。
- owner 记录在 `ptag_owner_request`；游标改为 `ptag_branch_last[{ptag, request}]`。
- 未盖戳 L0（inj）在 owner 确立前累积在 branch 0，owner 确立时**结转**到 owner 分支 →
  单请求链与旧实现逐字节等价。
- 调用方显式给的 `parent_event_id`（R6/A6 consumer→taint 源覆盖）优先级不变。

## 步骤（TDD，全部实测）

- [x] T1 RED：HEAD 发射器源码 + 新契约测试 → `tests/test_lsu_hook_sq.py` §7 **4 条 FAIL**
      （实测：`FAIL emitPropEvt 用请求域游标 ptag_branch_last` / `记录 owner 请求` / `hh 声明` /
      `不再用 ptag_last_event 作 parent`；同源基线 8 FAIL 中含既有 4 条 store 链 FAIL）。
- [x] T1b RED（真机数据）：冻结二进制流 `runs/lsu/r6_p1_{T04-F0-W4,T02-F0-W4}/.../seed1` →
      `check_admission` = `admitted=False`，`cross_request_edge` **30 / 31 处**
      （首例 `event 8:mshr_alloc req='301' → event 9:cache_access req='303'`）。
- [x] T2 实现（复核保留）：`CHAOSPropagation.{cc,hh}` 请求域游标（见上“选路”）。
- [x] T3 GREEN：工作树源码 → §7 4 条全 PASS；`test_lsu_campaign_propagation.py` §6 6 条全 PASS。
- [x] T4 构建：`scons -j16 build/ARM/gem5.opt`（删 `CHAOSPropagation.o` 强制重编该 TU）
      → `[CXX] .../CHAOSPropagation.cc`，**warning: 0 / error: 0**；binary sha256 `4a3e8a12e4890d10…`。
- [x] T5 回归：`lsu_test_runner.py` 61 套件 —— 与基线同为 **FAIL=13**（NEW FAIL=0）。
- [x] T6 真机定向（同一 cell/同一 flag，仅换二进制）：
      T04-F0-W4 seed1 1593 事件：`detected_contained/False/30 断裂` → **`full/full_chain/True/0 断裂`**；
      T02-F0-W4 seed1 204 事件：`False/31 断裂` → **`full/full_chain/True/0 断裂`**。
- [x] T7 commit `[LSU][MDSPEC][R6-FIXA]` + `git push -u origin r6-fixa`。

## 不得做

- 不得放宽/删除 `cross_request_edge`（工具链一行不改，由 `test_lsu_campaign_propagation.py §6(2)` 钉死）。
- 不得跑 pilot；不得 push 集成分支。
