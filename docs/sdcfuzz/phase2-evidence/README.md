# Phase 2 归档证据（2026-11-15）

这些文件是 `docs/sdcfuzz/phase2-verification.md` 的机器可读证据，
由 `scripts/test-phase2.sh` 生成，原路径在 `m5out/phase2-*`。

| 文件 | 内容 |
|---|---|
| `avalanche.json` | 19 模板雪崩/屏蔽惩罚（iterations=40） |
| `training.json` | RL 200 轮曲线、动作分布、奖励 |
| `policy.json` | 32×10 策略权重 |
| `best_stream.json` / `best_fp_stream.json` | 最优整数/FP 流 |
| `validation.json` | 最优 FP 流 ×20 次 CHAOSFPU vs fp-add 基线 |
| `mcpat_selection.json` | McPAT 候选级反馈排序 |
| `streams.json` | 9 条 Type-I/II/III 功耗流定义 |
| `power_measurements.json` | 9 次 gem5 + McPAT 结果 |
| `fi_results.json` | 6 条 FP 流 ×20 次 FI 分类 |
| `correlation.json` / `correlation.md` | Pearson/Spearman + H1–H3 |
| `phase2_gate.json` / `phase2_milestones.json` | 10 步闸门 + 5 里程碑审计 |

闸门结果：10/10 步 PASS，5/5 里程碑 PASS。
