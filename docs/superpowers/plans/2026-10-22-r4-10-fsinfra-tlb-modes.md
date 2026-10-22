# R4-10 FS-INFRA + T-系残余：T05/T06/T07 模式实现 + T08-b/c/d 配对 + 24 项分类

> 执行者：R4-10-FSINFRA 子代理（worktree `.claude/worktrees/r4-10-fsinfra`，
> 分支 `r4-10-fsinfra`，基线 `lsu-mdspec-20261019` @ `d63a5dd8`）。
> 上位：`blocked_triage.md`（FS-INFRA 24 / MODE-UNIMPL 含 T08-W9 3 项）、
> `round4_findings.md` §R4-6.0 / §R4-6-T08 / §R4-5.9 / §R4-8-FS-W1。
> 硬约束：**本 worktree 禁止构建 gem5、禁止跑正式 campaign、禁止改共享证据**。
> 故所有 C++ 改动为 **COMPILE-UNVERIFIED**，真机验证由主 agent 在构建后执行。

## 目标

1. **T05/T06/T07 缺失模式**：在 `CHAOSArmTLB` 真实实现（源码 + 契约测试），
   不得只改阻塞文字。
2. **T08-b/c/d**：完成 walk/refill 配对（walk_id 关联、refill field 标注）的模型
   实现与契约测试。
3. 逐 RunID 对 FS-INFRA 24 项 + T08-W9 3 项 + T05/T06/T07 缺失模式分类并给证据。
4. 交付"待主 agent 构建"清单（文件 + 改动点 + 建议验证命令）。

## 关键事实（继承，勿推翻）

- `walker=None` 配置 bug 已修（R4-6.0），T01-F0-W4 / T04-F0-W4 真机 activated=1
  → 24 项 FS-INFRA 中 lookup 系（T01/T02/T03/T04/T10）**已可跑**，旧理由失效。
- T08-a（walk_pairing, lost walk）已真机证（T08-F0-W4/W9、T08-F6-W9）。
- T08-F4-W9 为**结构性诚实零**（F4 burst interval 1e5 ≫ walk-issue 流 ~1e3）。
- T05/T06/T07 模式在 `CHAOSArmTLB` 中**不存在**（`FaultType` 无对应值）。

## 阶段分解（每项一个 commit → 立即 push）

- [ ] **C1 — T05**：`CHAOSArmTLB` 增 `valid_clear` / `valid_set` / `global_flip` /
      `asid_subst` 四个 faultType；新增 `tlb_state` 传播节点（L2）；config choices +
      campaign `MODEL_FLAGS` + 从 `MODEL_BLOCKED` 删除 T05；契约测试。
- [ ] **C2 — T06**：增 `perm_subst` / `memtype_subst` / `pagesize_subst`（从同 TLB
      另一条 live 表项取合法值）；同上接线；契约测试。
- [ ] **C3 — T07**：增 `false_hit` / `double_hit` / `wrong_way`；同上接线；契约测试。
- [ ] **C4 — T08-b/c/d**：增 refill 完成钩子 + `walk_fill_dup` / `walk_done_early` /
      `walk_stale_result`；walk_id 配对节点（field/outcome 逐子模型标注）；接线；契约测试。
- [ ] **C5 — 分类与交付**：逐 RunID 四类分类表 + `blocked_triage.md` 订正记录 +
      构建清单报告（`docs/gem5-fi/lsu/mdspec/R4-10-FSINFRA-agent-report.md`）。

## 每阶段验证（真实命令）

- 契约测试：`python3 tests/test_lsu_hook_t05_state.py`（退出码 0 = 全 PASS）。
- 回归：`python3 tools/lsu_campaign.py --list-cells --matrix
  artifacts/lsu-trial/07-expanded-matrix-backfilled.csv` 的 Resolution 计数不退化；
  既存契约测试（`test_lsu_hook_tlb.py`、`test_lsu_hook_t08_walk.py`、
  `test_lsu_coverage_matrix.py`）全绿。
- C++ 编译与真机：**不做**（禁构建）→ 交主 agent。

## 建模边界（诚实声明）

- T05/T06/T07 落在 lookup-hit 钩子（`maybeCorrupt`），与 T01-T04 同路径；变异
  字段不同（valid/global/asid/ap/mtype/tg），传播节点为 `tlb_state`
  （pfn/PA 不变时 `tlb_pfn` 不适用）。
- T08-b/c/d 落在 `WalkUnit::insertTableEntry`（refill 写表点）新增钩子；三者都在
  issue 点经 tier 门选中后**不丢弃** walk（与 T08-a 相反），在 refill 点施加。
