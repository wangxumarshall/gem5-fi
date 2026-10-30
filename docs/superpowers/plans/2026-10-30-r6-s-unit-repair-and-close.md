# R6 S 单元修复与收口（2026-10-30）

依据：`docs/gem5-fi/lsu/evidence/R6-S-UNIT-DIAGNOSIS.md`（5b550954） × 用户 2026-10-30 工作令
（授权实施已查明修复；严格 crash 终局；B2/B3 正式阻塞；21 个 PASS seed 冻结）。

基线：worktree `.claude/worktrees/r6-s-unit-20261029`，分支 `run/r6-s-unit-20261029`，
HEAD `5b550954`，origin/fi-ding `a92f9f6d`。冻结二进制 `a1632e0f…`（source head 2498573f）。

## 不变量

- 7 RunID × 3 seed = 21 份已 PASS 文档与证据 **不重跑、不覆盖**；基线 SHA-256：
  `/home/sdc/gem5-fi-ding-cleanup-20261029/R6-S-UNIT-BASELINE-{DOCS,SHA256}.tsv`。
- 不降低 admission / EOF / truncation / conservation 任何门禁；不用 chain_end 伪造 L5。
- 唯一 C++ owner：本轮全部 `CHAOS/gem5/src/**` 修改由一个主会话完成，串行审查。

## 任务（每项 = 一个 commit）

1. **test(lsu): pin S-unit forwarding and crash terminal semantics**
   - `tests/test_lsu_s_forward_repair.py`：层映射（sq_entry=L1、lsq_fwd=L2）、
     L0→L5 正向链、部分字节/同地址/source_sub/load squash/一源多消费、
     parent 非空、错 corr/request 拒绝、不相关 load 不继承 taint、addrpath 不变。
   - `tests/test_lsu_crash_translation_terminal.py`：正/负 18 项严格门禁。
   - `tests/test_lsu_s10_trigger_reporting.py`：S10 三方计数 + cap + noteOutcome 源码合同。
   - `tests/test_lsu_s_unit_blocked.py`：B2 15 格证据字段 + F4 规格阻塞合同。
   - 先运行确认 **全部失败**（红），再进入实现。
   - 说明：不单独提交“红测试”commit（违反本仓库“提交前测试必须通过”）；
     测试与对应实现同 commit，名称沿用工作令的逻辑顺序。

2. **fix(lsu): complete LSQ forwarding propagation and S08 tracing**
   - `CHAOSPropagation.{hh,cc}`：load-seq 注册表（seq-primary）、`noteForwardedLoad`
     发射真实 L1 `sq_entry` → L2 `lsq_fwd` → L3 `resp` → L4 `taint_reg`，
     目的物理寄存器入 `taint_set`；squash/commit 清理。
   - `CHAOSLSQFwd.{hh,cc}`：`corrupt()` 返回 ptag 并携带 load DynInst；
     `maybeSubstituteSource` 接收 keys/DynInst/alt store 身份，注入后走同一注册路径；
     F5 `noteOutcome(true)`。
   - `lsq_unit.cc`：转发点传递 keys / alt 身份 / load DynInst。
   - `tools/lsu_prop_fields.py`：`sq_entry`=L1、`lsq_fwd`=L2、必录字段；
     `store_set.cc` 不变（S10 cap 改动在任务 4）。
   - 验证：C++ 源合同测试 + 合成链 checker 测试 + 旧 21 文档不变。

3. **fix(lsu): classify translation-fault crash terminals**
   - `tools/lsu_chain_check.py`：新增终局 `crash_translation_fault`
     （provable_to=L3、L4/L5=N/A、独立 admission 路径），严格 16 正条件 /
     16 负条件；每类拒绝有命名 violation。
   - `tools/lsu_campaign.py`：`admission_gate` 传 rc；crash 样本 certified 接线；
     离线复判 6 个 S13 样本（不满足条件者不得放行）。
   - 负条件：无关 crash、无 fault_id、无 corr、无 parent、异常不在 ancestry、
     oracle 非 Crash、exit 不支持、contained=1、truncated、gzip 不完整、
     chain_end 伪造、time reversal、cross-request、campaign/checker 不一致。

4. **fix(lsu): reconcile S10 trigger reporting**
   - `CHAOSLSQFwd.cc` S10 注入点：maxFaults 在 subst 点同样生效（修 3 次注入
     违反 maxFaults=1）；成功注入 `lsuTrigger->noteOutcome(true)`（F5），
     cap 后不再 `onEligible()`。
   - 三方一致：`CHAOS_LSU_TRIGGER.injected` == 注入日志成功行 ==
     `stats.numFaultsInjected`；`fires == injected + no_effect`。
   - `tools/r6_s_trigger_census.py`：数据源矛盾响亮失败；阻塞记录字段补全。
   - 离线复判 S10-F5-W5/W9；证据不足才重跑。

5. **fix(lsu): resolve F4 tier semantics**
   - 检索权威规范（LSX 派生矩阵、frequency policy、docs/gem5-fi/lsu/）。
   - 有权威定义 → 实现 + 确定性单测（同 seed 逐位可复现、与 F0/F1/F2/F5/F6 可区分）。
   - 无定义 → 正式 `BLOCKED_SPEC_FREQUENCY_UNDEFINED`，不运行、不记 PASS。

6. **docs(lsu): close repaired S-unit propagation evidence**
   - B2 15 格 `BLOCKED_TRIGGER_REACHABILITY` 完整证据（RunID、simTicks、tier、
     首火下界、eligible、为何不可达、解除条件）。
   - 新增合格 seed 的 8 章传播文档（沿用 21 份格式，不生成顶层 seed 文档）。
   - 更新 INDEX/CATALOG/INTERNAL-CATALOG/EVIDENCE/STATUS/FINAL-REPORT；
     T=83/A=90 与 21 份 S 文档 SHA 不变；断链=0。
   - 合并前提：NEW FAIL=0、工作树干净、阻塞严格、链接有效、远端无分叉；
     主工作树只做原子部署，不执行 merge/reset/clean。

## 验证命令（每阶段）

```bash
# 定向（示例）
python3 tests/test_lsu_s_forward_repair.py
python3 tests/test_lsu_crash_translation_terminal.py
python3 tests/test_lsu_s10_trigger_reporting.py
python3 tests/test_lsu_s_unit_blocked.py
python3 tests/test_lsu_chain_check.py
python3 tests/test_lsu_campaign_admission.py
python3 tests/test_lsu_prop_fields.py
# 头文件 C++ 单测
g++ -std=c++17 -I CHAOS/gem5/src tests/chaos_lsu_trigger_test.cc -o /tmp/lsu_trig && /tmp/lsu_trig
# 完整非慢速回归（冻结二进制显式指定）
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt \
  pytest tests/ -q -m "not slow"
```

## 构建（单次，detached tmux）

- gem5 进程=0；`scons -j16 build/ARM/gem5.opt`（首次）→ 日志落盘；
- 记录 source HEAD、binary SHA-256、build_time、warning delta；
- 旧二进制保留，新二进制独立归档（`build/ARM/gem5.opt` + sha 文件）；
- 构建后才重跑受影响格：A(6+S08) → Crash(6) → S10(2) → F4(若实现)。

## 停止条件

见工作令 §十七；一般修复/测试/构建/重跑/文档/提交/推送已授权。
