# P0 证据：G0-04 参数基线对照 + G0-05 负载资产映射

生成：2026-09-29 15:20（Session 001）
方法：Excel `2.LSU参数基线` 表（`evidence/P0/xlsx_param_baseline.out`，stdlib 解析器 `xlsx_dump.py`）
与 `configs/se/lsu_proxy.py` 实现（V1.0 轨道资产，commit af8f5cf3 前系列）逐行代码级对照；
负载映射基于 `ls workloads/directed/`（43 个 ELF）与清单 `负载：` 字段统计（`grep -c`，总和=325 校验）。

## G0-04：B0 19 参数 + S1–S4 逐项对照（静态代码级）

| Excel行 | 参数 | Excel B0 值 | lsu_proxy.py 实现 | 一致 |
|---:|---|---|---|---|
| R2 | LQEntries | 16 | `:580 cpu0.LQEntries = 16` | ✓ |
| R3 | SQEntries | 16 | `:581 cpu0.SQEntries = 16` | ✓ |
| R4 | Load FU | 1个；MemRead/FloatMemRead opLat=2 | `:63-66 LSU_Load count=1` | ✓ |
| R5 | Store FU | 1个；MemWrite/FloatMemWrite opLat=2 | `:68-71 LSU_Store count=1` | ✓ |
| R6 | LSQDepCheckShift | 0（S3=4） | `:582 =0`；`:589-590 S3→4` | ✓ |
| R7 | LSQCheckLoads | 1 | `:583 True` | ✓ |
| R8 | SSIT/LFST | 1024/1024 | `:584-585` | ✓ |
| R9 | store_set_clear_period | 250000 | `:586` | ✓ |
| R10 | cacheLoad/StorePorts | 200/200 | `:587-588` | ✓ |
| R11 | L1 DTLB | 32项全相联LRU（S1=64） | `:593 =32（S1→64）` | ✓ |
| R12 | L2 TLB | 1280项 5-way | `:594-595` | ✓ |
| R13 | L1D | 32KiB/2-way（S2=64KiB/4-way） | `:646`；`:662-663` | ✓ |
| R14 | Cache line | 64B | 未显式设置（gem5 System 默认 cache_line_size=64） | ✓* |
| R15 | L1D latency | 2/2/2 | `:647` | ✓ |
| R16 | L1D MSHR/targets | 6/8 | `:648` | ✓ |
| R17 | L1D write buffers | 16 | `:648` | ✓ |
| R18 | 预取器 | L2 Stride degree=8, latency=1, prefetch_on_access=True（S4 挂 L1D） | `:668-670 B0@L2`；`:664-667 S4@L1D`；`:650/:655` L1D/L1I 置 NULL（stdlib 默认纠偏） | ✓ |
| R19 | 时钟 | 2.6GHz 仅用于换算 | `:47/:621` | ✓ |
| 附录 | L1I | 32KiB/2-way/1-1-1/MSHR2 | `:652-654` | ✓ |
| 附录 | L2 | 1MiB/16-way/12-12-12/MSHR16 | `:657-659` | ✓ |

S1–S4 敏感性（每次只改一个因素）：S1 仅 DTLB=64（`:593`）✓；S2 仅 L1D=64KiB/4-way（`:662-663`）✓；
S3 仅 LSQDepCheckShift=4（`:589-590`）✓；S4 仅预取器搬 L1D（`:664-667`）✓。

**结论：19/19 一致（含 L1I/L2 几何 21 项全对）。**
\* R14 依赖 gem5 默认值未显式固化——建议 P1 显式设置 `cache_line_size=64`（不改变行为，仅消除默认依赖）。
限制：本对照为静态代码级；运行时实例化参数 dump 复核待 G0-01 重建后补强（注入 sim-object 参数打印即可复核）。

## G0-05：W0–W13 负载资产映射（主负载 ITEM 统计，总和 325 ✓）

| W | 名称 | 模式 | ITEM数 | 服务器资产（workloads/directed/） | 状态 |
|---|---|---|---:|---|---|
| W0 | MiniCheck | SE | 6 | `mini_check` | SE 可用 |
| W1 | MiBench-TC23 | FS 优先 | 27 | **无** | 缺失 → DR-001 |
| W2 | BEEBS-DelayAVF | SE | 6 | `beebs_kernels` | SE 可用 |
| W3 | AGU-AddrModes | SE | 24 | `agu_addrmodes` | SE 可用 |
| W4 | TLB-AliasPerm | FS | 24 | **无现成**（FS 自设负载待建；TLB FS 路由已入库 af03fa67） | 待建（P2） |
| W5 | SQ-Forward | SE | 54 | `sq_forward` | SE 可用 |
| W6 | Cache-DirtyEvict | SE+多核FS | 55 | `cache_dirtyevict`（SE）；多核 FS 子集待 | SE 可用 |
| W7 | Atomic-Litmus | 多核FS | 29 | `atomics_probe`（SE 单核近似）；litmus 多核 FS 待 | 部分 |
| W8 | Prefetch-Stride | SE | 25 | `prefetch_stride` | SE 可用 |
| W9 | GAP/Graph500 | FS/SE | 15 | `gap_bfs` | SE 可用 |
| W10 | STREAM+PointerChase | SE | 27 | `stream_chase` / `stream_triad_kernel` | SE 可用 |
| W11 | SPEC CPU2017 | FS/SE | 12 | **无**（需许可证） | 缺失 → DR-001 |
| W12 | SQLite-Speedtest1 | SE/FS | 15 | `sqlite_like`（自设近似，非真实 speedtest1） | 近似（口径需 DR 确认） |
| W13 | PARSEC-Selected | 多核FS | 6 | **无** | 缺失 → DR-001 |

量化：完全缺失影响 **W1(27) + W11(12) + W13(6) = 45 ITEM（13.8%）**；W4/W7 的 FS/多核部分（24+29）依赖 FS 管线与自设负载建设（P2 范围）；W12 为近似探针需口径裁决。SE 可立即覆盖的负载合计 212 ITEM（65.2%）。

注意：ITEM 的"推荐负载"字段常含多负载（如 A01 同时列 W3+W9），上表按主`负载：`字段统计，一 ITEM 一票，总和恰为 325。
