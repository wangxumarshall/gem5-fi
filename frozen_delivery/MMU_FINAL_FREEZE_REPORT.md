# MMU WHEN-5X3 — 最终冻结报告 (final freeze report)

冻结时间：2026-11-19（含 W5X3-OBS-0222 定向补全）
冻结范围：MMU E2E WHEN-5X3 研究（`/home/sdc/gem5-fi-mmu-when5x3`）
冻结性质：只读归档。后续不再主动扩大 MMU 实验范围，不再修改冻结故障模型，不执行任何
Git add / commit / push / 远程仓库操作。

## 1. 冻结项

| # | 冻结对象 | 冻结内容 |
|---|---|---|
| 1 | 实验设计 | 8 模型 × 5 上下文 × 3 时机 = 120 条件；冻结 Where（M01–M08 定义）、When（时机选择 `ceil(p·N)`）、Context（C01–C05）语义 |
| 2 | M01–M08 故障模型 | M01 TLBI/entry 保留、M02 PFN 置换、M03 ASID 错配、M04 decoy-PFN 替换、M05 partial→DTB 毒化、M06 local descriptor 降级、M07 权限 grant 反转、M08 request-PA XOR 0x1000 |
| 3 | C01–C05 上下文 | C01/C02/C04/C05 = 冻结 R01/R05/R04/R03；C03 weak-consumer 变体 |
| 4 | T01–T03 动态注入时机 | 每个 (Model,Context) 三档 `ceil(p·N)` 时机（p=0.1/0.5/0.9） |
| 5 | 最终实验结论 | **120 条件 · 117 Fault 执行 · 117 FULL · 0 PARTIAL · 3 N/A（M06-C05）** |
| 6 | 源码 Patch | `Frozen_Source.patch` + `gem5_observational_changes.diff` + `0202c_source_diff.md` + `0222_lsq_translation_lifecycle.patch` |
| 7 | 复现入口 | `resume.sh` → `campaign/finalize.py`；0222 定向复跑 `python3 work/rerun_m07_c02_obs.py`；`scons -j<N> build/ARM/gem5.opt`（25.1.0.1） |
| 8 | 只读归档 | 本目录 `exports/MMU_FINAL_FROZEN_DELIVERY/` 设为只读（`chmod -R a-w`） |

## 2. 两轮关键修正

### 0202c-final-close（证据一致性修复，不重跑实验）

1. M07-C02-T01 EventID 修正（translation_start=319、Pre-activation Squash=325、
   mmu_fault_activate=345、translation_result=346、lsu_request=347、chain_end parent=347）。
2. Pre-activation Squash 与 `faulting_inst_squashed=0` 的区分。
3. Guest SIGSEGV 审慎表述（不归因于故障动态指令）。
4. A21 引用修正（`blocked_tasks.md` → `M06_C05_PILOT_EVIDENCE.md`）。
5. 源码快照从 5 → 19 个关键文件 + 完整 `Frozen_Source.patch`。
6. 历史原始 Trace 归档（117 条 + Control，SHA256 核验）。

### W5X3-OBS-0222（M07-C02-T01/T02 定向补全，运行时证明）

1. **新增纯观测埋点**：LSQ 翻译生命周期观测（`mmuNoteLsqTranslationFinish`），发射
   `translation_response_received` / `squash_translation_decision` /
   `squash_translation_invoked` / `translation_request_discarded` /
   `cache_dispatch_decision` 五类事件。
2. **新 Build**：`ce80a9c983b31f77c9b4a6626012505fd3484d5c00df5b9399a9d6975ab2b73d`。
3. **定向复跑**：T01/T02 Fault + 匹配 Control（`runs/W5X3_OBS/`），不改 Where/Context/
   Timing/注入语义（Control N=6 复现，Guest SIGSEGV 字节一致）。
4. **结论**：M07-C02-T01/T02 从 REQUEST_PENDING_AT_ROI_END（PARTIAL）升级为
   **SQUASHED_BEFORE_MEMORY_ACCESS（FULL）** —— 运行时证明故障请求被
   `squashTranslation()` 丢弃、未进入 Cache（dec=discard_due_to_prior_squash,
   released=1 → terminal_reason=prior_squash_before_translation_completion →
   cache_dispatch_blocked_by_squash）。
5. 终态 **117 FULL / 0 PARTIAL / 3 N/A**。

## 3. 冻结交付目录内容

| 文件 | 说明 |
|---|---|
| `MMU_FINAL_REPORT.zip` | 报告 + 统计（21 文件） |
| `MMU_FINAL_CAUSAL_EVIDENCE.zip` | 因果 DAG + 逐样本路径（141 文件） |
| `MMU_FINAL_RAW_AND_SOURCE.zip` | 原始数据 + 源码快照 + 0222 复跑（400 文件） |
| `M07_C02_T01_COMPLETE_PROPAGATION.md` | T01 完整传播链证据（在 ZIP1 内） |
| `M07_C02_T02_COMPLETE_PROPAGATION.md` | T02 完整传播链证据（在 ZIP1 内） |
| `MMU_FINAL_DELIVERY_MANIFEST.md` | 交付清单 |
| `SOURCE_SNAPSHOT.md` | 源码溯源索引（含 0222 附录 A） |
| `MMU_FINAL_FREEZE_REPORT.md` | 本冻结报告 |
| `MMU_Propagation_Traces.tar.zst` | 历史 117 条原始 Trace（SHA256 已核验） |
| `MMU_When_Golden_Evidence.tar.gz` | Control / Golden 证据（SHA256 已核验） |

## 4. 终态

MMU WHEN-5X3 研究已进入只读冻结状态（**117 FULL / 0 PARTIAL / 3 N/A**）。全部文档、
原始数据、源码、SHA256、验收报告与交付包逐项校验通过（`unzip -t` 三包无错、完整解压
21/141/400 文件成功、117/117 Trace SHA256 一致、836 因果边 0 dangling、T01/T02 完整
fault→squash-discard 链运行时证明）。

后续需要与其他微架构单元的最终方案统一整理后，再决定 Git 入库；本次不做任何 Git 操作。