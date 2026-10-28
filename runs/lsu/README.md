# runs/lsu 目录入口

| 入口 | 路径 |
|---|---|
| **完整传播路径**（每 RunID×seed 一份人可读 MD） | `R6_COMPLETE_PROPAGATION_PATHS/`（README/INDEX.md/INDEX.json） |
| **权威证据索引** | `R6-AUTHORITATIVE-EVIDENCE.md` / `.json` |
| **最终报告** | `r6_reports/` |
| **当前实验** | 见权威索引中的 `KEEP_ACTIVE`（本轮已全部结束） |
| **FS checkpoint** | `fs_cpt_boot/` |
| **结果 Excel** | `../../docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-R6实验结果.xlsx` |
| **当前矩阵** | `r6_matrix_325.csv` |
| **清理计划/结果** | `r6_reports/R6-RUNS-CLEANUP-PLAN.*`、`R6-RUNS-CLEANUP-RESULT.*` |

> 不要凭 `r6_*` 目录名猜权威性；一律以 `R6-AUTHORITATIVE-EVIDENCE.json` 为准。

## R6 A 单元（AGU）— 2026-10-28

- 状态：`r6_reports/R6-A-STATUS.md` / `.json`；最终报告：`r6_reports/R6-A-FINAL-REPORT.md`
- 传播文档：`R6_COMPLETE_PROPAGATION_PATHS/INDEX-A.md`（9 个合格 seed）
- 证据目录：`r6_a_<RunID>_s<seed>`（初版）、`r6_a_spanfix_*`（F0 span 修复后）、`r6_a_segv_*`/`r6_a_segv2_*`（guest-SEGV 证据修复后）、`r6_a_fix2_*`（A08-W5/A03-W10 收尾）
- 每个 RunID+seed 的权威副本选择规则：`fix2 > segv2 > segv > spanfix > 初版`（二进制更新优先），见 `r6_reports/R6-A-STATUS.json`。
