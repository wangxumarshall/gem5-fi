# MMU WHEN-5X3 — 最终实验（120 条件）

本仓库为 MMU（TLB/页表/权限）故障注入与传播追踪的**最终正式实验**归档。

## 最终实验结果（权威基线）

| 维度 | 数量 |
|---|---|
| 计划条件 | **120**（8 模型 M01–M08 × 5 上下文 C01–C05 × 3 时机 T01/T02/T03） |
| 已执行 Fault | **117** |
| 严格 FULL | **117** |
| PARTIAL | **0** |
| N/A | **3**（M06-C05，`INFEASIBLE_SPECULATIVE`） |

终态汇总：SDC 74 · ACTIVATED_MASKED 15 · PROPAGATED_BUT_SQUASHED 9 ·
DETECTED_DELIVERED 9 · ACTIVATED_UNCONSUMED 5 · DETECTED_LOCALLY 3 · N/A 3 ·
SQUASHED_BEFORE_MEMORY_ACCESS 2。

M07-C02-T01/T02 由 0222 轮运行时 LSQ squash-discard 证明升级为
`SQUASHED_BEFORE_MEMORY_ACCESS`（FULL），详见
`frozen_delivery/M07_C02_T01_COMPLETE_PROPAGATION.md` 与
`M07_C02_T02_COMPLETE_PROPAGATION.md`。

## 八个故障模型（Where）

| 模型 | 故障点（trace 事件） | 终端 |
|---|---|---|
| M01 | L2/Unified TLB 失效抑制 | SDC |
| M02 | PTW 重填 PFN 破坏（XOR bit0） | SDC |
| M03 | ASID 标签误匹配 | 多数 SQUASHED |
| M04 | Resident TLB PFN 替换 | SDC |
| M05 | Partial walk-cache next-table 指针毒化 | SDC |
| M06 | Leaf descriptor valid-bit 降级 | DETECTED |
| M07 | 权限 grant 反转（授权绕过） | SDC |
| M08 | 最终 PA 物化破坏（XOR 0x1000） | SDC |

注入时机（When）：每 (Model, Context) 三档 `ceil(p·N)`（p=0.1/0.5/0.9）。

## 目录结构

```
CHAOS/gem5/                gem5 25.1.0.1 源码树（含全部 MMU 故障注入 + 观测埋点）
frozen_delivery/           权威只读冻结交付（3 ZIP + 2 tar + 冻结报告/清单/源码快照）
campaign/                  执行器 when5x3_runner.py + finalize.py + conditions.json(120)
                           + context_map.json + rcs/（逐上下文脚本）
work/                      0222/0223/0224 脚本 + 19/20/21 配置 JSON + REPRODUCTION_V3.md
configs/                   gem5 配置 lsu_b0_fs.py + mmu_*.rcS
workloads/mmu/             W9–W14 源码 + build_all.sh
workloads/mmu_w5x3/        guest 二进制 mmu_w9..mmu_w15 + *.dyn
analysis/                  机器可读结果：per_condition.json(120)、timing_map.csv、
                           control_map.json、fault_control_compare.csv、completeness.csv
runs/                      原始 Trace（git 忽略；已归档于 frozen_delivery）
gem5-fs/                   运行时资产 kernel/disk（git 忽略，EXTERNAL）
resume.sh                  复现入口
```

## 复现入口

```bash
# 1. 重建 gem5（build/ 未入库，需重建）
cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt && cd ../..

# 2. 完整重跑（仅重跑缺失 manifest 的 control/fault）
./resume.sh            # -> campaign/when5x3_runner.py --all -> campaign/finalize.py

# 3. 0222 定向复跑（M07-C02-T01/T02 squash-discard 运行时证明）
python3 work/rerun_m07_c02_obs.py
```

完整说明见 `work/REPRODUCTION_V3.md` 与 `frozen_delivery/SOURCE_SNAPSHOT.md`。

## 参与实验的四个构建（BuildHash 见 control_map.json / authoritative_trace_index.csv）

| BuildHash（前 16） | 用途 |
|---|---|
| `741cdc567f489444` | 原构建（117 条原始 Trace） |
| `eb327197c073dddf` | 0202c + IFU 埋点 + masked_reason |
| `fb1b6f010034f273` | 0202c + MMU_CONSUMER_REUSE_CAP=16 |
| `ce80a9c983b31f77` | 0222 LSQ 翻译生命周期观测（M07-C02-T01/T02 + Control） |

## 源码 Patch（完整故障注入实现 + 观测埋点）

见 `frozen_delivery/MMU_FINAL_RAW_AND_SOURCE.zip` 内 `source_patches/`：
`Frozen_Source.patch`（M01–M08 + 传播追踪，92 文件）、
`gem5_observational_changes.diff`（0202b）、`0202c_source_diff.md`（0202c）、
`0222_lsq_translation_lifecycle.patch`（0222）。

## 外部资产（诚实声明）

`gem5-fs/vmlinux`（227 MB）与 `runs/disks/mmu_template.img`（2.36 GB）为
`EXTERNAL_ASSET_NOT_YET_DISTRIBUTED`，未入库且无公开下载。外部独立复现可在
不持有这两者的情况下完成源码构建与归档校验，但无法执行全系统样本。详见
`frozen_delivery/MMU_FINAL_DELIVERY_MANIFEST.md`。
