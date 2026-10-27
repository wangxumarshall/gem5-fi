# R6-V4 T 单元收口计划（unattended continuation, 2026-10-28）

> 接手现场：工作树 `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`，
> HEAD/branch/origin-fi-ding 三者同为 `2848cd98e9cdc0256a437e94b0432b0cd93ffef1`，工作树干净。
> 冻结二进制 `<WT>/CHAOS/gem5/build/ARM/gem5.opt`，
> sha256 `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`（1,145,680,944 B，
> mtime 2026-10-27 13:09），`binary_source_head=d1543872e155943893fdd6d18a489ff7c372d97d` —— 与任务书一致。
> 现场差异：`/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_batch_monitor.sh`（只读采样器）仍在运行，
> 属上一轮遗留的只读监控；不写证据、不占 gem5 槽位，本轮保留不动（结束条件前统一收尾）。
> 截止接手时 gem5/scons/pytest/campaign 均为 0。

## 目标（只做 T 单元，不启动其他单元正式实验）

T 单元共 **39** 个 RunID。排除：

- **F6（6 格，政策排除，本轮禁跑）**：T04-F6-W4、T05-F6-W4、T06-F6-W4、T07-F6-W4、T08-F6-W4、T08-F6-W9。
- **已 COMPLETE_3_OF_3（17 格，证据合格，不因二进制版本重跑）**：
  T01-F0-W1/F0-W4/F1-W1/F1-W4/F2-W1/F2-W4、T02-F0-W1/F0-W4/F2-W1/F2-W4、
  T03-F5-W4、T03-F5-W9、T04-F0-W4、T04-F2-W4、T10-F0-W1/F1-W1/F2-W1。
- **BLOCKED_SPEC（3 格）**：T10-F0/F1/F2-W11（SPEC CPU2017 许可）。
- **BLOCKED_WORKLOAD_GAP（2 格，待 Lane C 复核）**：T08-F0-W9、T08-F4-W9。

**本轮可执行 = 11 格**：

| RunID | 子模型（矩阵默认） | 现状 |
|---|---|---|
| T05-F0-W4 | valid_clear | seed1 FAIL_NO_ACTIVATION |
| T05-F2-W4 | valid_clear | 未运行 |
| T06-F0-W4 | perm_subst | seed1 FAIL_NO_ACTIVATION |
| T06-F2-W4 | perm_subst | 未运行 |
| T07-F0-W4 | false_hit | seed1 FAIL_TIMEOUT_OPEN_CHAIN |
| T07-F4-W4 | false_hit | 未运行 |
| T08-F0-W4 | a/b/c/d 复合 | T08-a 仅 canary；整体 PARTIAL |
| T08-F4-W4 | a/b/c/d 复合 | 未运行 |
| T10-F0-W4 | bit_flip | seed1 PASS，缺 seed2/3 |
| T10-F1-W4 | bit_flip | seed1 PASS，缺 seed2/3 |
| T10-F2-W4 | bit_flip | seed1 PASS，缺 seed2/3 |

需要新 seed：T05/T06/T07/T08 × 各 3 = 24；T10 × 各 2 = 6；合计 **30 个合格 seed**。

## 合格 seed 判据（全部满足才算数）

正确 RunID/负载/故障类型/频率档；二进制 SHA 与 manifest 一致；真实注入；activated 与触发摘要、stats、注入日志三者一致（`count_contradiction=false`）；正常 EOF；prop_evt 未截断；stats 非空；terminal 为 `full` 且 L0→L5 ancestry 真实（不得用 `chain_end` 冒充 L5），或真实 `detected_contained`（有 detection layer/reason/outcome/闭合对象）；`admitted=True`、`certified=True`、`violations=[]`、conservation=OK；campaign 与 checker 一致。

## 纪律

- 一 patch 一单元；每根因独立提交；每个提交前必须真实构建/测试并引用真实输出。
- 预计 >5 分钟的构建/gem5/campaign 一律 detached tmux；gem5 并发 ≤2；每 (RunID,seed) 独立新目录 + flock；
  原子 manifest；不覆盖任何旧证据；F6 不运行。
- 不改原始 `prop_evt*`、不手改 `chain_report` 结论、不把 SKIP/XFAIL 当通过、不放宽 admission/conservation/完整链判据。

## Task 1 — Lane 诊断收口（只读，无提交）**DONE**

Lane A（T05/T06）、Lane B（T07）、Lane C（T08 + W9）各自写报告：
`runs/lsu/r6_reports/R6-DIAG-{A-T05-T06,B-T07,C-T08}.md`。

- [x] 三份报告落盘并复述关键事实（R6-DIAG-{A,B,C}.md）
- [x] 建立文件所有权表：CHAOSArmTLB.cc / CHAOSPropagation.* / lsu_campaign.py 均由主 agent 唯一修改
- [x] 逐条判定根因类别：T05/T06=统计遗漏+真实 L2 含住；T07=CAM 计数缺口+无关联臂；T08=双计数+armed 行误计

**验收**：每格根因有 file:line + 真实命令输出支撑；无法判定的明确写 "unknown" 及缺口。

## Task 2 — 根因修复 1：T05/T06/T07 `numFaultsInjected` 计数链路 **DONE**

- [x] 先写失败测试（tests/test_lsu_hook_t05_state.py [8]，先红后绿）
- [x] 最小修复（applyEntryFieldFault + maybeCorruptLookup 各补一次递增）
- [x] 定向测试通过；完整回归在 Task 8 统一执行
- [x] 独立提交 a0250d51

**验收**：真实命令输出证明 count_contradiction 归零，且没有把"日志存在"当作 activated。

## Task 3 — 根因修复 2：T07 false_hit 终局/计数（按 Lane B 结论）**DONE**

- [x] 失败测试（[8]/[10] 源码契约）→ 最小修复（CAM 计数 + 关联臂）→ 定向测试通过；完整回归见 Task 8
- [x] 独立提交 a0250d51

**验收**：注入后第一处真实分歧可定位；终止/分类逻辑自洽；不得把超时强杀算 PASS。

## Task 4 — T08 子模型覆盖（按 Lane C 结论）**DONE**

- [x] T08-b/c/d 各取得 1 次真实动态覆盖（runs/lsu/r6_v4_canary_T08{b,c,d}-*；签名见 R6-V4-T08-SUBMODEL-COVERAGE.md）
- [x] 四子模型均可动态触达；T08-c 如实记为“变体执行、按设计零硬件效应”
- [x] W9：Lane C 用 debugfs 证据复核 FS 镜像无 GAP/Graph500，BLOCKED_WORKLOAD_GAP 成立；拒绝用 W4 替代

**验收**：每子模型给出事件签名（event_id/kind/字段）作为覆盖证据。

## Task 5 — 统一构建（仅当 Task 2–4 改了 C++）**DONE（两次）**

- [x] 第一次统一构建（b13a60ab…，source head e2eccdec）覆盖 Task 2–4 的首次 C++ 修复；第二轮（e379cc5b…，source head 0501a00f）覆盖运行中发现的 R6-V4-ATTRIB 修复；第二次首建因 `field` 作用域错误 BUILD_EXIT=2，修正后 0 error/0 warning 通过
- [x] 记录在 runs/lsu/r6_v4_bin_identity.txt 与各 manifest（含构建日志、exit、告警=0）
- [ ] 若只改 tools：不重建，明确区分 binary_source_head / binary_sha256 / analysis_tool_head

## Task 6 — 受影响 RunID 的 seed 运行（30 个 seed）

顺序：先 seed1（修复验证）→ 合格后 seed2、seed3；已有合格 seed1 的只补缺。

- [ ] T10-F0/F1/F2-W4 seed2、seed3（若修复不触及 T10 语义则直接补；否则先做影响审计）
- [ ] T05-F0-W4 seed1→2→3；T05-F2-W4 seed1→2→3
- [ ] T06-F0-W4 seed1→2→3；T06-F2-W4 seed1→2→3
- [ ] T07-F0-W4 seed1→2→3；T07-F4-W4 seed1→2→3
- [ ] T08-F0-W4 seed1→2→3；T08-F4-W4 seed1→2→3；另跑 b/c/d canary
- [ ] 每 seed：新目录 + flock + 原子 manifest（run/seed/命令/binary SHA/source head/analysis head/PID/PGID/日志/时间/exit/.done）
- [ ] 每 seed 过合格判据逐项核验

**验收**：11 格 × 3 seed 全部有逐项核验输出；失败格立即停该格、保存现场、回到诊断。

## Task 7 — 传播文档（每个新通过 seed 一份）

- [ ] 在 `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/` 新增 `<RunID>-seed<N>.md`，九章齐全
- [ ] 更新 README/INDEX（数量、两轴状态、二进制身份）
- [ ] 更新 R6-EVIDENCE-DEDUP、R6-T-SUBMODEL-STATUS、runid_map/coverage_matrix/ready_contract
- [ ] 生成 T 单元最终汇总报告

**验收**：文档计数与磁盘证据逐一对得上；叙事能回答"注入在哪里、什么值怎么变、经过哪些单元、为何形成该结局"。

## Task 8 — 收尾

- [ ] 完整回归 NEW FAIL=0（真实输出）
- [ ] 无 gem5/scons/campaign/pytest 残留；工作树干净
- [ ] 推送当前分支与 origin/fi-ding（先核对远端无未知提交）

## 最终汇报（模板）

修改文件与提交 / T05/T06/T07/T08 真实根因与修复 / 测试与回归与构建结果 / 最终二进制 SHA 与 analysis head /
11 格逐 seed 状态（terminal、provable_to、admitted、certified、violations、结局）/ T08 四子模型覆盖 /
仍 BLOCKED 的格与不可执行证据 / 新传播文档目录与索引 / 是否达到 T 单元可执行格全部完成。
