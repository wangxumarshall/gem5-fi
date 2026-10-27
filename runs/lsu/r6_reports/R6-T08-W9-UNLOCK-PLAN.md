# T08-F0-W9 / T08-F4-W9 后续解锁计划（本轮保持 BLOCKED_WORKLOAD_GAP）

裁决（2026-10-27）：本轮**不修复** W9，也不允许用 `tlb_probe.rcS` 或 T08-W4 结果冒充 W9。
`T08-F0-W9`、`T08-F4-W9` 状态固定为 **BLOCKED_WORKLOAD_GAP**。

## 固定原因（实测）

1. W9 定义要求 **GAP/Graph500** workload。
2. 当前 GAP 可执行体仅有 SE 版本：`workloads/directed/gap_bfs`。
3. T08 的 page-walk 注入点需要 **FS**（`resolve_cell` 返回 fs 载体）。
4. 当前 FS 镜像（`gem5-fs/ubuntu.img`）内没有 GAP/Graph500。
5. campaign 对 `armtlb` **忽略 workload 字段**、恒用 `configs/fs/tlb_probe.rcS`
   （`tools/lsu_campaign.py:1604-1641`），因此 W9 的启动命令与 W4 字节相同，**无法诚实表达 W9**。

## 真正解锁所需工作（按序，全部完成后才允许解除）

1. **取得合法可执行的 AArch64 GAP/Graph500**（BFS/SSSP/PageRank 至少一项），记录来源与构建方式。
2. **装入 FS 镜像**或以不改变实验语义的方式提供 FS 可访问载体（不得换成别的 workload）。
3. **新增专用 FS 启动脚本**（不复用 `tlb_probe.rcS`），并让 campaign 能按 workload 选择载体
   （即修复 `resolve_cell` 对 workload 的忽略行为）。
4. **验证 guest 实际执行 BFS/SSSP/PageRank**：以 `board.workload.dmesg` / guest 输出 / 程序自报
   为证，排除仍跑 `tlb_probe`。
5. **验证 T08 page-walk hook 在此 workload 下有 eligible event**（`walk_issue_probe`/`walk_id` 可观测）。
6. **验证 workload 输出与结果哈希**（oracle 基线）。
7. 完成后才将 `BLOCKED_WORKLOAD_GAP` 解除，并进入 seed1→seed3 流程。

## 停点

上述任一步无法在不改变实验语义的前提下完成 ⇒ 保持 BLOCKED 并汇报，不得以替代 workload 蒙混。
