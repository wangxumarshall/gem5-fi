# R6-FIXCPP 续作：lookup-tier 运行时能力标记 + consumer_summary 真实发射

日期：2026-10-24 · 分支 `r6-fixcpp` · worktree `.claude/worktrees/r6-fixcpp`
基线：`6ec7c5aa`（含 `ca334efb` T01 含住链 + `6ec7c5aa` lookup-tier C++）
Lane FIX-CPP 唯一拥有：`CHAOS/**`（C++）。**不得**改 `tools/**`（FIX-TOOLS 定稿）、
不得改 `tools/lsu_test_runner.py` 或 `tests/test_lsu_obs_driver_workers.py`（DIAG-RUNNER）。
**不合入集成分支**。只 push 自己的 `r6-fixcpp`。

工具侧契约冻结在 `r6-fixtools`
（`docs/superpowers/plans/2026-10-24-r6-fixtools-lookup-tier-consumer-summary.md`，
提交 `ea17e3c9` + `4c74e3ac`）。本 lane 只补 C++ 半边。

## 目标 1：`CHAOS_LSU_TIER_CAP` 运行时能力标记（字段契约已冻结）
启动时向 stdout 打印**一次**：
`CHAOS_LSU_TIER_CAP: requested=<F0..F6|off> effective=<F0..F6|off> lookup_tier_enabled=<0|1>`
- `requested` = 命令行请求的 tier；`effective` = 运行时实际生效的 tier；
  `lookup_tier_enabled` = lookup 路径是否真挂了 tier 门。
- 工具 `lookup_tier_capability_gate`（`tools/lsu_campaign.py`）核对
  `effective==requested==请求值` 且 `enabled==1`；缺字段 ⇒ `capability-malformed`、
  旧二进制 ⇒ `capability-missing`、不一致 ⇒ `capability-mismatch`、
  `enabled=0` ⇒ `capability-disabled`，一律 `blocked=True, admitted=False`。
- F0 legacy 路径也打印；**绝不**在未挂载时谎报 `enabled=1`。

## 目标 2：`consumer_summary` 真实发射（聚合规则 = 用户裁决 2026-10-24）
向 PROP-EVT **流**发射独立记录类型（**不是** PROP-EVT，无 kind、不进链）：
```
CONSUMER-SUMMARY: schema=1 version=1 run_id=… sample_run_id=… fault_id=… source_id=…
  suppressed_consumer_count=… distinct_dyn_seq_count=… emitted_consumer_count=…
  first_tick=… last_tick=… min_dyn_seq=… max_dyn_seq=…
  by_kind=<k:n,…> by_outcome=<k:n,…> total_before=… total_after=…
```
- **永远逐条保留**：inj、TLB 事件、Cache/MSHR 状态变化、taint 状态变化、
  request_fork bridge、errant_commit、squash_masked、显式 containment、chain_end。
- **只聚合**：未产生新状态变化、非层级唯一见证、非检测/终局的**重复 consumer**。
- 至少保留第一条代表 consumer；真实终局 / `chain_end` 前 flush。
- 不设可被误认为完整证据的静默硬上限；内部资源上限触发 ⇒ `resource_abort` +
  `truncated` 且拒绝准入。
- 守恒：`total_before==total_after==emitted+suppressed`、
  `sum(by_kind)==sum(by_outcome)==total_before`、`total>0⇒emitted≥1`。

---

## 任务分解（每任务 = 一提交）

### T1 `[LSU][MDSPEC][R6-FIXCPP]` lookup-tier 运行时能力标记
- [x] 新共享头 `CHAOS/gem5/src/cpu/o3/chaos_lsu_tier_cap.hh`：把
      (requested, effective, enabled) 解析 + 标记行格式化做成依赖无关的纯函数，
      CHAOSArmTLB.cc 与独立单测共用（"测的就是跑的"）。
- [x] `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc`：构造期打印一次标记
      （`off`/未知拼写 → requested 按实情；`off` 即 legacy F0 ⇒ F0/F0/0），
      `fflush(stdout)` 保证 abort 样本也带着标记。
- [x] 新 C++ 单测 `tests/chaos_lsu_tier_cap_test.cc`：F0/F2/F6 + 未知档 +
      一致性/禁用逐字钉死标记行。
- [x] 新 Python 驱动 `tests/test_lsu_r6_fixcpp_tier_cap.py`：真编译真运行该单测 +
      防漂移守卫（CHAOSArmTLB.cc 真调用共享标记函数）+ 与工具 gate 口径一致。
- [x] 验证：单测 ALL PASS（23 PASS）；`scons -j16 build/ARM/gem5.opt`
      `scons: done building targets.` 零告警；reg_chain golden
      `f247ef3fe6f02cfd` rc=0 无 SIGSEGV。
- 说明（诚实）：gem5-fs 镜像缺失（空 submodule），FS armtlb 跑不起来，因此标记
      **真实二进制运行样例**不可得；标记由「同一函数」的独立单测真编译真运行取证 +
      源码防漂移守卫。不声称跑过 FS。

### T2 `[LSU][MDSPEC][R6-FIXCPP]` consumer_summary 聚合逻辑（共享头 + 单测）
- [x] 新共享头
      `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/chaos_consumer_summary.hh`：
      聚合器纯逻辑（分组键 =(ptag, source_id)；首条代表必出，其后同一 source 的
      重复消费折叠并精确累计；非 `consumer` kind 一律不聚合；守恒；resource 上限
      触发时拒聚合且响亮标记）。
- [x] 新 C++ 单测 `tests/chaos_consumer_summary_test.cc`：
      ① 主 L0–L5 链不变；② L5（errant_commit/chain_end）绝不聚合；
      ③ consumer 数量守恒；④ summary 字段与契约逐字一致；
      ⑤ 大量重复 consumer 下输出规模显著下降（1000 → 2 行 = 500x）。
- [x] 新 Python 驱动 `tests/test_lsu_r6_fixcpp_consumer_summary.py`：真编译真运行 +
      用冻结契约校验器复核真实 summary 行（本 worktree tools/ 尚无 FIX-TOOLS 件，
      用逐条对齐的本地移植并打印来源）。
- [x] 验证：单测 ALL PASS（30 PASS）。

### T3 `[LSU][MDSPEC][R6-FIXCPP]` consumer_summary 接入 CHAOSPropagation 发射
- [x] `CHAOSPropagation.hh/.cc`：noteCommit 的 consumer 发射走聚合器
      （抑制项不写 PROP-EVT、计入 summary；代表项 event_id 作为被抑制项的重污染
      parent，DAG 不断）；exit 回调在 chain_end **之前** flush 每个 summary；
      resource_abort 时 printf + 落盘响亮标记。
- [x] 验证：真跑 SE `lsu_proxy.py --chaos_l1d --chaos_propagation`：
      reg_chain 62 逻辑 consumer → 44 事件 + 11 summary（守恒 em11+su18=tb29=ta29）；
      mini_check 17 → 8 + 6（su9）；gap_bfs 2 → 2（su0）；非 consumer 事件
      逐字不变（75/75），errant_commit L5 字段完整；golden 回归；套件 NEW FAIL=0。

## 验证命令
- `g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/chaos_lsu_tier_cap_test.cc -o /tmp/t1 && /tmp/t1`
- `g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/chaos_consumer_summary_test.cc -o /tmp/t2 && /tmp/t2`
- `pgrep -a scons`（>1 个则停）→ `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`
- `build/ARM/gem5.opt --outdir=/tmp/regchain configs/se/arm_chaos.py --cmd workloads/directed/reg_chain --cpu O3`
- `python3 tests/test_lsu_r6_fixcpp_tier_cap.py`
- `python3 tests/test_lsu_r6_fixcpp_consumer_summary.py`
- `python3 tools/lsu_test_runner.py --json /tmp/r6fixcpp_after.json`（NEW FAIL=0）
