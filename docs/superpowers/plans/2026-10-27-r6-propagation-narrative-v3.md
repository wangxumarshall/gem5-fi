# 2026-10-27 R6 传播叙事 V3 收口 + 11 格工具解锁计划

> 续接任务。基线 worktree：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`，
> 起点 HEAD `7065459cb635fac5e51cc0a04884d40d78524db6`（= origin/fi-ding），工作树干净。
> 冻结二进制：`binary_source_head=d1543872e155943893fdd6d18a489ff7c372d97d`，
> `binary_sha256=20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`。
> 本计划只改 docs / tools / tests，不修改 C++ 或构建输入，因此**不重建 gem5**。
> 一任务 = 一提交；每任务完成后勾选并引用真实命令输出。

## 已完成的前置事实（只读核验，2026-10-27）

- [x] 无 gem5/campaign/scons/pytest 长任务（仅遗留只读监控脚本 `r6_n8_batch_monitor.sh`，非 gem5）。
- [x] worktree HEAD=`7065459c`，工作树干净，origin/fi-ding=`7065459c`。
- [x] 51 份文档全部存在，均含七个 `##` 一级章节；12 份第 7 章标题为 `## 7. 原始证据与哈希`（语义等价变体，不是结构失败）。
- [x] 旧 `30 秒结论` / `一行传播图`：0 份。
- [x] 旧审计 `structural_failures=12` 的根因 = 第 7 章标题变体 + 全文 REVIEW_REQUIRED 字符串启发式，均不可靠。
- [x] 二进制 SHA-256 与冻结值一致。

## Task 1 — 精确叙事审计工具（TDD）

**文件**
- `tests/test_lsu_prop_doc_audit.py`（先写，预期失败）
- `tools/lsu_prop_doc_audit.py`

**测试先行断言**
1. `T03-F5-W4-seed1` 判定为 `PASS`：第 7 章提到 stale 目录 `REVIEW_REQUIRED` 不得影响 seed verdict。
2. `T01-F1-W4-seed2` 判定 `REVIEW_REQUIRED`，且原因来自第 6 章 verdict 字段。
3. `## 7. 原始证据与哈希` 与 `## 7. 原始证据与文件哈希` 均计为七章齐备。
4. W1（矩阵标签 MiBench + 实际 `tlb_probe.rcS`）→ `experiment_identity_status=WORKLOAD_IDENTITY_MISMATCH`。
5. 第 2 章祖先链、第 4 章事件存在性、哈希匹配由原始证据独立重算。

**实现要点**
- verdict 只读第 6 章首个 `verdict|判定|结论` 行里的首个加粗 token。
- 结构检查按七个语义章节名匹配，允许编号/标题变体；containment seed 的 N/A 小节不算缺失。
- 第 2 章：解析 ancestry 链，按 `parent_event_id` 校验相邻关系；禁止子先于父（tick 单调）。
- 第 4 章：逐 event_id 回查 prop_evt；parent/tick 与原始流一致。
- 哈希：对权威目录文件重算 SHA-256 并与第 7 章表格比对。
- `chain_evidence_status` 依据 chain_report 的 terminal/admitted/certified/violations + 本地一致性检查。
- `experiment_identity_status` 依据矩阵标签（第 1 章）与实际 readfile（run.out 命令行）。
- 输出逐文件明细，不允许只给汇总数字。

**验证**
```bash
python3 -m pytest tests/test_lsu_prop_doc_audit.py -q
```

## Task 2 — T01-F1-W4 seed2/seed3 多 fault 只读复核

**文件**
- `runs/lsu/r6_reports/R6-T01-F1-W4-MULTIFAULT-RECHECK.md`
- `runs/lsu/r6_reports/R6-T01-F1-W4-MULTIFAULT-RECHECK.json`

**只读复核项**
1. 逐 `fault_id`：terminal / provable_to / containment 层 / 事件数 / 是否闭合。
2. escape-first 代表故障确认为 fault 1（唯一 `full`）。
3. `cell_results.json` 的 `activated` 与 `classes` 逐项对照。
4. `count_contradiction=false` 的判定依据。
5. campaign 的统计单元（`lsu_campaign.py:2990-3006`：`classes[run_outcome] += activated`，**按 run 级 outcome 加权到每个 activated fault**）vs checker 的 per-fault 单元。
6. `taint_reg` 的 `arch_reg/phys_reg` 字段：两 seed 原始流均存在该列；seed3 主链事件的值为空——记录为证据缺口，不伪造。
7. 不改原始流、不运行 gem5。

**判定规则**
- 若仅文档口径混淆 → 修正文档并并列两套口径。
- 若工具输出在 fault 级语义上自相矛盾 → 保留 `REVIEW_REQUIRED`，出缺陷报告，**不得改判 PASS**。
- 初步证据：campaign 的 `classes.Crash=5/3` 是把 run 级 Crash 乘以 activated 数，与 checker 的 per-fault 1 full + 2/1 contained + 2/1 open 不同单元；按规则保留 `REVIEW_REQUIRED` 并记录为工具级缺陷（待用户裁决是否修 campaign 聚合语义）。

**验证**：复核脚本输出与报告表格逐项一致；原始证据哈希不变。

## Task 3 — W1 双轴状态统一（全部 51 份扫描）

**对象**：矩阵标签含 `MiBench` 且 run.out readfile=`tlb_probe.rcS` 的所有样本
（预期 8 RunID × 3 seed = 24 份：T01-F0/F1/F2-W1、T02-F0/F2-W1、T10-F0/F1/F2-W1）。

**每份文档**
- 第 1 章新增：`chain_evidence_status`、`experiment_identity_status`、`overall_experiment_status`、`WORKLOAD_GAP` 记录。
- 第 6 章 verdict 改为两轴：链证据判定 + 实验身份判定，不再用单一 PASS 掩盖。
- 明确：证据只能证明 `tlb_probe.rcS` 载波下的传播链，不能证明 MiBench-TC23 条件下的结果。
- 不修改矩阵标签、不重跑、不把“实际载体为准”当作等价。

**验证**：审计工具确认 24 份 identity mismatch；其余 27 份 identity 一致。

## Task 4 — README / INDEX / 权威证据索引更新

**文件**
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/README.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.md`
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.json`
- `runs/lsu/R6-AUTHORITATIVE-EVIDENCE.md`
- `runs/lsu/R6-AUTHORITATIVE-EVIDENCE.json`

**要求**
- 删除旧“30 秒摘要/一行图”结构说明。
- 分栏：propagation terminal vs run outcome；chain status vs experiment identity。
- containment seed 的 L5=`N/A`；T02-F2-W4 seed2 与 T10-F2-W1 seed2 使用 event_id=68 的权威 L4 squash containment；`chain_end` 不作 L5。
- 索引与 51 份新版文档逐项一致；analysis tool head 写本轮最终提交 SHA。

**验证**：审计工具重跑；INDEX 行数=51；冲突项为 0。

## Task 5 — 生成最终审计并同步提交

**产物**：`runs/lsu/r6_reports/R6-PROPAGATION-PATHS-NARRATIVE-AUDIT.{md,json}`

**同步清单**（只同步这些路径到 worktree）
- `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/*`
- `runs/lsu/R6-AUTHORITATIVE-EVIDENCE.{md,json}`
- `runs/lsu/r6_reports/R6-PROPAGATION-PATHS-NARRATIVE-AUDIT.{md,json}`
- `runs/lsu/r6_reports/R6-T-BLOCKED-REVALIDATION.{md,json}`
- `runs/lsu/r6_reports/R6-T08-W9-UNLOCK-PLAN.md`
- `runs/lsu/r6_reports/R6-T-SUBMODEL-STATUS.md`
- `runs/lsu/r6_reports/R6-T01-F1-W4-MULTIFAULT-RECHECK.{md,json}`
- 必要的 `runs/lsu/README.md`

**验证**
```bash
git -C <worktree> status --porcelain    # 只允许上述路径
git -C <worktree> diff --stat
```
提交信息主题：`[LSU][MDSPEC][R6-PROPAGATION-NARRATIVE-V3] ...`；push 当前分支；仅当 origin/fi-ding 仍为祖先且可 fast-forward 时更新；禁止强推。

## Task 6 — campaign 门控最小修复（TDD）

**文件**：`tests/test_lsu_campaign_t08_gates.py`（新）、`tools/lsu_campaign.py`

**失败测试**
1. T05/T06/T07 的 W4 cell 不再因陈旧 `MODEL_BLOCKED` 被拒（当前二进制已实现）。
2. T08-F0-W4 / T08-F4-W4 只允许明确 `t08a` 代表路径；未指定或非 t08a → 仍拒。
3. T08-F0-W9 / T08-F4-W9 → 恒定 `BLOCKED_WORKLOAD_GAP`，且不得落到 `tlb_probe.rcS`。
4. screening/formal 不能用通用 `--allow-blocked-models` 绕过上述门。
5. T09、F6、W11 SPEC 仍被拒。

**实现**：显式 RunID/能力门表；`--allow-blocked-models` 仅限 trial，或改为精确白名单；错误信息响亮。

**验证**：定向 pytest + 完整回归，NEW FAIL=0。

## Task 7 — 台账生成器修复与重生成（TDD）

**文件**：对应生成器（`tools/lsu_runid_map.py` / `lsu_coverage_matrix.py` / `lsu_ready_contract.py` 及其数据源）、测试、生成产物。

**要求**
- T10-W4 三格：去掉陈旧 FS-INFRA。
- T05/T06/T07：runnable / evidence pending。
- T08-W4：`T08-a canary allowed`，整模型 `PARTIAL`。
- T08-W9：`BLOCKED_WORKLOAD_GAP`。
- T09×3：`OUT_OF_SCOPE_BACKFILL_ARTIFACT`。
- W11 SPEC：`BLOCKED_SPEC`；F6：政策排除。

**验证**：重生成后 diff 只含预期格；定向测试 + 完整回归。

## Task 8 — 5 个代表 canary（工具回归通过后）

顺序与配置（最多并发 2，全新目录，detached tmux）：
1. `T10-F0-W4` seed1
2. `T05-F0-W4` seed1（子模型：valid_clear，代表）
3. `T06-F0-W4` seed1（perm_subst，代表）
4. `T07-F0-W4` seed1（false_hit，代表）
5. `T08-F0-W4` seed1（T08-a walk_pairing，仅代表）

**统一环境**：`LSU_FS_DIR=/home/sdc/gem5-fi-ding/gem5-fs`；二进制冻结 SHA；`LSU_GEM5_BIN=<worktree>/CHAOS/gem5/build/ARM/gem5.opt`。
**manifest 必须记录**：run_id、seed、fault_submodel、workload、readfile、完整命令、binary path/SHA、binary source head、analysis tool head、PID/PGID、日志、状态、`.done`、exit_code。
**逐格核验**：workload/submodel 身份、requested/effective tier、tier enabled、before/after、attempted/eligible/injected、stats.numFaultsInjected、EOF、stats 非零、prop_evt 未截断、terminal、provable_to、admitted、certified、violations、conservation、campaign/checker 一致、完整链或真实 containment。

**边界**
- T08-a 通过只能记 `PARTIAL_SUBMODEL_PROVEN`。
- T08-W9 不运行。
- 11 格 seed1 全部达到各自允许状态前，不补 seed2/seed3、不启动正式实验、不进入下一个 LSU 单元。
- 某组失败只停该组，如实报告。

## 最终汇报清单

51 份精确审计；结构失败具体文件名；两轴状态；W1 mismatch 完整清单；T01-F1-W4 复核结论；索引更新；文档提交 SHA；工具修复文件与提交；定向/完整回归；二进制 provenance；5 canary 状态；11 格逐格状态；W9 阻塞原因；T08-W4 是否仅 PARTIAL；待裁决事项。
