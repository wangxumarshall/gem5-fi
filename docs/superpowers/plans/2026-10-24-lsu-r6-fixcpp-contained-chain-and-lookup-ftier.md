# R6-FIXCPP — 含住链注册门控 + lookup 路径 F 档位（Lane FIX-CPP，唯一 C++ 所有者）

分支 `r6-fixcpp`（worktree `.claude/worktrees/r6-fixcpp`，基线 `848d803a`）。
范围：`CHAOS/gem5/src/cpu/o3/CHAOSPropagation/**`、`CHAOS/gem5/src/arch/arm/CHAOSArmTLB/**`、
相关 C++ 头文件与对应 C++ 测试。**不改 `tools/**`**（LINCHECK/FTIER 已定稿）。

## 任务 A — T01 含住后错误继续传播（根因已确认）

根因（实测 T01-F0-W4/seed1，契约钉子 `tests/test_lsu_r6_contained_chain_contract.py`）：
注入翻转 pfn bit 56，`pfn<<12` 在 64 位 Addr 回绕 ⇒ 有效 PA 未变
（`0x81d75fa8 == 0x81d75fa8`），注入点自判 `pa_changed=0`；但 `registerTlbFault` 的
seq-primary 臂对任何 `req_seq != 0` **无条件**注册 ⇒ 同一请求后续干净事件
（sq_execute/sq_writeback/resp/taint_reg）仍并入本链 ⇒ 一条链同时断言"L2 已含住"
与"已传播到 L4"。

- [x] A1 共享决策头 `CHAOSPropagation/chaos_tlb_chain.hh`（注册臂门控 +
      含住撤销裁决 + 行为模型），C++ 单测 `tests/chaos_tlb_chain_containment_test.cc`
- [x] A2 `registerTlbFault` 用 `chaos_chain::tlbRegistrationArms` 门控（PA 未变 ⇒ 无臂）
- [x] A3 `noteTlbTranslationResult` 含住时 `revokeChainArms`（防残留映射）+ 用共享
      `translationContained` 裁决
- [x] A4 测试驱动 `tests/test_lsu_r6_tlb_chain_containment.py`（真编译+真运行 + 防漂移守卫
      + 契约测试保持全绿）
- 验证：RED（pre-fix 源，6 项防漂移守卫 FAIL，rc=1）→ GREEN（ALL PASS）
- 目标：`effective PA unchanged → L2 显式含住`；L3/L4/L5 = N/A(contained)；
  `parent.tick ≤ child.tick`；checker option-2 `admitted=True`

## 任务 B — lookup-mode F-tier

- [x] B1 `CHAOSArmTLB::lookupTierMounted()` / `lookupTierAllowsInjection()`：lookup 命中
      路径真正 poll `lsuTrigger`（此前只出现在 ctor 与 maybeDropWalkFill）
- [x] B2 两个 hook（maybeCorrupt / maybeCorruptLookup）各接一次 gate；**F0 保持 legacy**
      （maxFaults/probability/events_to_skip 原样）
- [x] B3 F2/F6 使用既有 tier 语义（`chaos_lsu_trigger.hh`：F2 = 100,000 eligible events
      ±50% 抖动；F6 = 首个 TlbHit 事件一次）——不自行发明频率
- [x] B4 固定 seed 触发序列测试 `tests/chaos_armtlb_lookup_ftier_test.cc` +
      `tests/test_lsu_r6_lookup_ftier_trigger.py`：F0/F2/F6 触发位置互不相同且可复现
- [ ] B5 `T02-F2`/`T04-F2`/`T04-F6` 不再 `TIER-UNIMPL` —— **BLOCKED（停点）**：
      该分类由**冻结的** `tools/lsu_campaign.py`（`ARMTLB_LOOKUP_TIERS = {"F0"}`）与
      `tools/lsu_ready_contract.py`（TIER-UNIMPL 计数 6）决定，本 lane 不得修改
      `tools/**`；工具侧解锁需改 tools + 三个 pin 住该计数/分类的测试。C++ 半边
      （根因）已落地并验证，工具侧仍明确 BLOCKED（不得伪装已运行）。
- 未做资源：无 FS 资产（缺 `gem5-fs/`）⇒ 无法端到端跑 FS；只做独立单测 + 构建验证。

## 任务 C — T04 consumer 聚合

- [ ] C1 **未实现（停点：需要改 `tools/**`）**。用户口径要求「聚合记录必须保留
      `suppressed_consumer_count`/`distinct_dyn_seq_count`/聚合规则版本 …」且
      「**checker/campaign 必须能识别该记录**」「不得改变已选完整 ancestry」：
      识别与守恒校验的落点是 `tools/lsu_chain_check.py` + `tools/lsu_prop_fields.py`
      （字段注册表），二者已定稿冻结；把聚合只做在 C++ 发射器侧会使 checker 无法识别
      该记录（不满足口径），而按 checker 的层见证规则决定"哪些 consumer 可丢"需要
      跨模块耦合。按停点规则：**停止并上报，不擅自改 tools/**，不做出无法验证的
      半个聚合（禁止"简单截断"）。

## 构建与回归

- [ ] 构建 `scons -j16 build/ARM/gem5.opt`（全机唯一构建，先 `pgrep -a scons`），
      新增告警 = 失败
- [ ] 回归 `python3 tools/lsu_test_runner.py`（本 worktree），NEW FAIL = 0
- [ ] 提交（按单元）：`[LSU][MDSPEC][R6-FIXCPP] …`，push 分支 `r6-fixcpp`
