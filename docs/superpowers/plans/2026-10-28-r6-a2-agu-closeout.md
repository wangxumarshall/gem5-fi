# R6-A2 AGU 单元第二轮收口实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 A 单元 30 个非 F6 RunID 各取得 3 个合格 seed（共 90），所有 A 子模型至少真实动态覆盖一次，开放链由真实终局事件闭合，无结构性 NO_FIRE。

**Architecture:** 在 defb3e0d 既有 3 项修复与 9 个合格 seed 之上，按“证据层真实事件 → 同源 repeat 载体 → 缺失子模型 → canary → 90 seed”推进。所有 C++ 改动集中在 CHAOSAddrPath / lsq / lsq_unit / iew / CHAOSPropagation / faults.cc 与 ARM ISA 生成点，共享文件由主 agent 单一 owner 串行修改；每项根因独立提交，C++ 全部合并后统一构建一次。

**Tech Stack:** gem5 v25.1.0.1 (AArch64 SE, O3)、Python 工具链（lsu_campaign / lsu_chain_check / lsu_prop_fields）、pytest、tmux、scons。

**Spec:** 用户 2026-10-28 R6-A2 工作令 + `runs/lsu/r6_reports/R6-A2-DIAG-{A,B,C}.md`（本轮只读诊断，含 file:line 实证）。

## Global Constraints

- 工作树 `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`；分支 `fix/r6-a-unit-20261028`；不得操作主检出目录 `/home/sdc/gem5-fi-ding` 的 Git。
- 起点 `defb3e0d`；保留上一轮 9 个合格 seed 与提交 c5558c9e/cf224f1c/1e8e96fe/defb3e0d；T 单元不重跑、不修改。
- 不运行 F6；不改 chain_end 为 L5；不用代理实现冒充子模型；不 SKIP/XFAIL/弱化断言；不手工改原始证据。
- gem5 最大并发 2；scons 期间 gem5=0；每个 RunID+seed 新目录 + flock + 原子 manifest + `.done`；分析工具流式处理。
- 每次 commit 只含一个根因；提交信息不含 Co-Authored-By；验证必须引用真实命令输出。
- SE 默认 timeout=300s，repeat 长样本按测量值显式提高 `--timeout` 并写入 manifest；上限 `REPEAT_MAX=600`。

## Review Focus

- repeat 后首趟暖 cache 是否改变 eligible 流（每迭代 census 必须实测，不得假设恒定）。
- A06 load shrink 与 A08-a load 侧错通道会踩定宽完成契约；必须 ineligible，绝不能以 SIGABRT 当“注入”。
- A07-c 丢 ready 后 IQ 已弹出，无 watchdog 必死锁。
- 新增 containment 事件必须带真实 detection_layer/outcome/corr，且不得绕过 truncated / errant_escape / 跨祖先门禁。
- A05 只能改 EA，不得改写架构/物理寄存器；StaticInst 的 type/shift 必须复制到局部再改。

---

## Task 0: 固定现场与基线（已完成记录，待归档）

**Files:**
- Create: `runs/lsu/r6_reports/R6-A2-BASELINE.md`
- Test: `/tmp/r6a2-baseline-pytest.log`

- [x] HEAD=`defb3e0d`、origin/fix/r6-a-unit-20261028=`defb3e0d`、origin/fi-ding=`659fa4cf`；工作树干净；gem5/scons/campaign/pytest 进程=0。
- [x] 二进制 `CHAOS/gem5/build/ARM/gem5.opt` sha256 `37c9ec362595c4631a85b78f67c2d05bbc6b126bfcc0dfda7007bdb568c4699f`。
- [x] 三路只读诊断落盘 `R6-A2-DIAG-{A,B,C}.md`。
- [ ] 完整 pytest 基线（后台任务 bxkygyu9o），完成后把逐套件 pass/fail 与两个既有失败写入 `R6-A2-BASELINE.md`。
- [ ] 提交诊断 + 本计划 + 基线。

## Task 1: 证据层 P0 修复（split SIGSEGV + 假 `.done`）

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`（`noteMemResponse` data_fnv）
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc`（`a08_subst` 保持原 64B 行内偏移）
- Modify: `tools/lsu_campaign.py`（`.done` 写真实 exit/signal；`exit_code==0 && truncated` ⇒ admitted=False）
- Test: `tests/test_lsu_campaign_truncation.py`、`tests/test_lsu_chain_check.py`

- [ ] 失败测试：构造/回放 A08-F0-W5 s3 残片（898B gz、末 `sq_writeback`、stats 0B），断言 `truncated=True`、`admitted=False`、不得因 `.done exit_code=0` 通过。
- [ ] 失败测试：`a08_subst` 候选地址必须满足 `(cand & 0x3F) == (addr & 0x3F)`，禁止新增跨 64B 行切分。
- [ ] 最小实现：`data_fnv` 仅在 `pkt->isRead() && pkt->hasData() && pkt->getPtr()!=nullptr` 时计算；否则记 `data=unavailable`。
- [ ] 最小实现：campaign 写 `.done` 时以真实返回码（signal ⇒ `128+signal`）为准；classification 对 `exit_code==0 && truncated` 强制拒绝。
- [ ] 定向测试通过；提交 `[LSU][MDSPEC][R6-A2][EVID]`。

## Task 2: 同源 repeat 载体 + census

**Files:**
- Modify: `workloads/directed/agu_addrmodes.c`、`mini_check.c`、`sq_forward.c`、`gap_bfs.c`（main → `probe_once()`；外层按 `CHAOS_REPEAT` 循环；每迭代重置全局状态并打印 `ITER:<n>:<hex>`；末行保留 `<hex>`）
- Create: `workloads/directed/chaos_repeat.h`
- Modify: `tools/lsu_campaign.py`（`--repeat-factor`、manifest `repeat_factor`、逐 `ITER:` 行对 golden 校验、`--timeout` 透传、`REPEAT_MAX=600`）
- Test: `tests/test_lsu_repeat_oracle.py`（新）、`tests/test_lsu_campaign_seed_start.py`

- [ ] 失败测试：`repeat_factor=3` 时必须解析 3 条 `ITER:` 且每条 == golden；任一不等 ⇒ oracle fail；`repeat_factor>600` ⇒ 配置拒绝。
- [ ] 失败测试：同源 assert（binary 路径/源码不变，仅循环次数变化）。
- [ ] 最小实现：四个 workload 的外层 repeat；默认 1，行为/输出与旧二进制逐字节同 golden。
- [ ] 重新构建 workload（host `gcc -O2 -static`），复核 golden：W3 `728e604ffcec539d`、W0 `07568da9f3ad5665`、W5 `1f4cbf14327717df`、W9 `030921682b3731f2`。
- [ ] 只读 census：对 repeat=2 与目标 repeat 各跑一次无故障 F0，记录总 eligible、前两迭代 eligible；要求总 eligible ≥ 1.2×max_first_fire 且每迭代 eligible 稳定（偏差 ≤5%）。
- [ ] repeat 表（公式 ceil(1.2*Fmax/eligible_per_iter)）：F2/F4 短载体 53/61/66；A01-F1-W9=6；A01-F1-W3=558；A06 以当前 bin 的 A06 专属 F0 census 重算；A06-F2-W5 补 census。上限 600，超限者报 BLOCKED 并保留证据。
- [ ] 提交 `[LSU][MDSPEC][R6-A2][REPEAT]`。

## Task 3: 真实终局事件 E1–E4/E6 + 门禁

**Files:**
- Modify: `CHAOS/gem5/src/sim/faults.cc`（E1 `arch_translation_fault` / E5 `downstream_fault`）
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`（E3 `squash_discarded`，`squash()` 分支）
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc`（E4 `store_not_retired` 独立事件；E6 `oracle_diff`）
- Modify: `tools/lsu_prop_fields.py`、`tools/lsu_chain_check.py`（kind→layer、corr 白名单、terminal 判定；只收紧）
- Test: `tests/test_lsu_r6a2_gate_negatives.py`（新）、`tests/test_lsu_chain_check.py`、`tests/test_lsu_campaign_truncation.py`

- [ ] 失败测试 N1–N5（truncated / open / chain_end-only / 未知终局 / 新 containment 不绕过）先行。
- [ ] 失败测试：E1 必须带 `fault_id, dyn_inst_seq, request_id, va, exc_type, delivered, outcome, detection_layer, contained, corr`；缺任一 ⇒ 拒绝。
- [ ] 失败测试：E3 必须来自真实 `squash()` 调用；E4 必须来自退出回调观察到的 store 生命周期；chain_end 仍不得计入 L5。
- [ ] 最小实现四个事件；`corr=none` 一律不闭合；E5 lineage=unknown 时只记 Crash，不闭合。
- [ ] 定向测试通过；提交 `[LSU][MDSPEC][R6-A2][TERMINAL]`。

## Task 4: A06-a/b 真实 size/byte-enable

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc/.hh/.py`
- Modify: `tools/lsu_campaign.py`（A06 路由/解除 MODEL_BLOCKED 仅在本 task 真机证据后）
- Test: `tests/test_lsu_a06_ruling.py`、`tests/test_lsu_a06_loadsize.py`

- [ ] 失败测试：A06-a store size 8→4/4→2/2→1，`addr%orig_size==0`；load/size=1/atomic/非对齐/跨行 ⇒ ineligible 且不消费预算。
- [ ] 失败测试：A06-b 同宽掩码 `new!=old,new!=0,len==size`；全 1 清 MSB；size=1 ineligible。
- [ ] 在 `LSQ::pushRequest` PRE（`lsq.cc:800` → `maybeCorruptPre` a06 分支）实现；记录 `submodel,old_size,new_size,old_be,new_be,EA,isLoad,dyn_inst_seq,request_id`。
- [ ] A06 F0 census（当前 bin，`a06_size`）；解除 BLOCKED 前必须有真实运行断言。
- [ ] 提交 `[LSU][MDSPEC][R6-A2][A06]`。

## Task 5: A04-a 对象注册表 + A04-b 真实同页

**Files:**
- Modify: `CHAOSAddrPath.cc/.hh/.py`（`aguObjectSpec`、`a04_same_object`、`a04_same_page`、废弃 `a04_subst`）
- Modify: `tools/lsu_campaign.py`、`tools/lsu_runid_map.py`、`configs/se/lsu_proxy.py`
- Test: `tests/test_lsu_a04_object_registry.py`（新）

- [ ] 失败测试：无对象表 ⇒ 启动 fatal；符号缺失/大小不符/越界/元素不对齐 ⇒ fatal；`a04_subst` ⇒ p.error。
- [ ] 失败测试：源 EA 不在对象 ⇒ 不消费预算；target 同对象、!=source、size 对齐、不越界；记录 object_id/base/size/src_off/dst_off。
- [ ] 从 `Process::objFile->symtab()` 解析；W0 重名 `data` 用显式 `@addr:size:8` 或重命名（重命名需重验 golden）。
- [ ] A04-b 按访问宽度对齐、同 4KiB 页、`target+size<=page_end`。
- [ ] 定向 canary（W3 array 512B）；提交 `[LSU][MDSPEC][R6-A2][A04]`。

## Task 6: A05-a/b/c/d 操作数级 hook

**Files:**
- Create: `CHAOS/gem5/src/arch/arm/insts/chaos_agu_operands.{hh,cc}` + `SConscript`
- Modify: `CHAOS/gem5/src/arch/arm/isa/insts/ldr64.isa`、`str64.isa`（`buildEACode` EA 表达式前）
- Modify: `CHAOSAddrPath.cc/.hh/.py`（回调、seq 幂等、no-effect、证据）
- Create: `workloads/directed/agu_operand_modes.c`（a/b/c 定向 asm 载体）
- Test: `tests/test_lsu_a05_operands.py`（新）

- [ ] 失败测试：a 仅 shift!=0、b 仅 W-index 且 bit31=1 可见、c 仅 size>1 且另一合法 shift、d 仅 pre/post imm!=0；不满足 ⇒ no_effect 不注入。
- [ ] 实现回调：复制 `type/shiftAmt` 到局部；只改 EA，绝不写寄存器；按 `dyn_inst_seq` 幂等重放。
- [ ] 微载体覆盖 a/b/c；W3 上 d 用现成 pre/post；真实 canary 记录 old/new base/index/extend/shift/wb_mode/EA。
- [ ] 全 ARM 重新生成与构建（构建窗口独占）；提交 `[LSU][MDSPEC][R6-A2][A05]`。

## Task 7: A07-a/c ready 时序 + watchdog

**Files:**
- Modify: `CHAOSAddrPath.cc/.hh/.py`（stale EA、watchdog 事件、三出口、汇总）
- Modify: `tests/test_lsu_hook_a07.py`（新断言）

- [ ] 失败测试：无 `effAddrValid()` ⇒ 不消费预算；`translationStarted()`/savedRequest ⇒ 拒绝并计数；watchdog 必须 ∈[1,max]，越界 fatal。
- [ ] A07-a：ready 点捕获 `effAddr/physEffAddr`；PRE 点覆盖 `addr`；记录 old/current/new EA、ready/consume tick、stale_source、downstream_consumed。
- [ ] A07-c：不调度 resume，调度 watchdog；squash ⇒ E3 收口；存活 ⇒ 强制 resume + `ready_loss_watchdog`；未决 ⇒ `CHAOS_AGU_WATCHDOG_UNRESOLVED` 且不 PASS；硬上限 exitSimLoop。
- [ ] 定向 canary W3/W5；提交 `[LSU][MDSPEC][R6-A2][A07]`。

## Task 8: A08-a/b 真实请求配对

**Files:**
- Modify: `CHAOSAddrPath.cc/.hh/.py`、`lsq.cc`、`lsq_unit.cc`、`iew.cc`（只读配对登记）
- Test: `tests/test_lsu_a08_pairing.py`（新）

- [ ] 失败测试：A08-a 仅 store 侧，日志必须含 `expected_channel=store,actual_channel=load,old_cmd,new_cmd,request_id,frag_idx`；load 侧 ⇒ ineligible。
- [ ] 失败测试：A08-b 必须同 tick、恰好一 load 一 store、store 先于 load；跨页/跨周期/反序 ⇒ decline 且不注入。
- [ ] 实现 store 侧 `buildPackets()` 前通道翻转；A08-b load 侧 PRE 换 EA、store 侧同页 `setPaddr`；记录 pair_tick/两条 seq/EA/PA。
- [ ] 定向 canary W5；提交 `[LSU][MDSPEC][R6-A2][A08]`。

## Task 9: 代表 canary（每模型 seed1）

- [ ] A01-F1-W3（repeat 后真触发）、A02-F2-W3、A03-F5-W3、A04-F0-W3（a 与 b 各一次）、A05-F0-W3（四子模型辅助 canary）、A06-F0-W3（a/b）、A07-F0-W3（a/b/c）、A08-F0-W3（a/b）。
- [ ] 每个按第十节判据验收；失败停该模型、保存现场、最小修复、继续其他模型。
- [ ] detached tmux；gem5 并发 ≤2；新目录+flock；记录命令/SHA/PID/PGID/日志/exit。

## Task 10: 30 RunID × 3 seed 正式收口

- [ ] 先保留上一轮 9 个合格 seed（受影响者做影响审计后重跑）。
- [ ] 按 canary 放行顺序补齐 90 seed；每 seed 三源一致（注入日志/trigger/stats）、gzip 完整、prop_evt 非截断、stats 非空、admitted/certified、violations=[]、conservation=OK。
- [ ] 失败 seed 不用 replacement seed；重跑同 seed 前先修根因。

## Task 11: 传播文档与索引

- [ ] 每个新合格 seed 生成 `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/Axx-Fx-Wx-seedN.md`（13 项内容）。
- [ ] 更新 `INDEX-A2.md`、证据去重表、STATUS。

## Task 12: 最终回归与收尾

- [ ] 完整 pytest，逐套件 NEW FAIL=0；构建一次并记录 SHA/source head/日志/告警差集。
- [ ] 生成 `R6-A2-FINAL-REPORT.md`、`R6-A2-STATUS.{md,json}`、`INDEX-A2.md`。
- [ ] 工作树干净、进程=0、推送 `fix/r6-a-unit-20261028`；不合入 origin/fi-ding。
