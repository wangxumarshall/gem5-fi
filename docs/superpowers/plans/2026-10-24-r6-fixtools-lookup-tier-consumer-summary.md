# R6-FIXTOOLS：lookup-tier 工具侧补完 + T04 consumer_summary 契约

日期：2026-10-24 · 分支 `r6-fixtools` · 基线 `848d803a`
Lane FIX-TOOLS 唯一拥有：`tools/lsu_campaign.py`、`tools/lsu_ready_contract.py`、
`tools/lsu_chain_check.py`、`tools/lsu_prop_fields.py` + 直接对应的**新增**测试。
**不得**改 C++（`CHAOS/**` 归 r6-fixcpp）、不得改 `tools/lsu_test_runner.py` /
`tests/test_lsu_obs_driver_workers.py`（归 DIAG-RUNNER）。**不跑 gem5 pilot**。

## 目标 A：lookup-mode F-tier 工具侧
C++ `6ec7c5aa`（origin/r6-fixcpp）已提供真实 lookup-tier 触发（F0 legacy；F2/F6 经
`chaos_lsu_trigger.hh` 既有语义）。工具侧须：传真实 `--tlb_lsu_tier F2/F6`、
更新 `ARMTLB_LOOKUP_TIERS` + ready contract 分类 + pin 测试、F0 保持 legacy、
并增加**运行时能力证明**（新二进制启动标记 requested/effective/lookup_tier_enabled；
campaign 核对一致性；缺标记/不一致/旧二进制**响亮拒绝**）。

## 目标 B：T04 `consumer_summary` 契约
口径：语义状态变化完整保留，重复 consumer 有账聚合；禁止简单截断。
定义明确的 summary 记录 + 8 条规则（不映射 L0–L5 / 非 L5·containment·terminal /
非伪造 parent / malformed·负计数·不守恒响亮拒绝 / 小流与聚合流 checker 输出一致 /
campaign 报告展示 emitted·suppressed·logical total·conservation /
truncated·resource_abort 仍 admitted=False / 无 summary 流兼容）。

---

## 任务分解（每任务 = 一提交）

### T1 `[LSU][MDSPEC][R6-FIXTOOLS]` lookup-tier：真实传参 + ARMTLB_LOOKUP_TIERS
- [x] `tools/lsu_campaign.py`：`ARMTLB_LOOKUP_TIERS` → `{F0..F6}`；新增
      `ARMTLB_LOOKUP_LEGACY_TIERS={F0}`、`ARMTLB_LOOKUP_TIERED_TIERS={F1..F6}`；
      armtlb lookup 分支：F0 → legacy（无 `--tlb_lsu_tier`）；F1–F6 → 追加
      `--tlb_lsu_tier <F>`；未知档位 → loud BLOCKED（保留 `_armtlb_lookup_tier_block_reason`）。
- [x] 新测试 `tests/test_lsu_r6_lookup_ftier_tooling.py`：RED（F2/F6 仍 BLOCKED）→
      GREEN（F0/F2/F6 命令互异；F0 legacy 保留；F2/F6 带 `--tlb_lsu_tier`）。
- [x] 更新 pin 测试：`tests/test_lsu_ftier_armtlb_lookup.py`（[2][4] 段）、
      `tests/test_lsu_ready_contract_category.py`（TIER-UNIMPL 6→?）、
      `tests/test_lsu_r6_reconcile_realroot.py`（计数）。
- [x] 验证：新测 + 三个 pin 测试真实跑通，套件 NEW FAIL=0。

### T2 `[LSU][MDSPEC][R6-FIXTOOLS]` lookup-tier 运行时能力门
- [x] `tools/lsu_campaign.py`：`parse_lsu_tier_capability(text)` +
      `lookup_tier_capability_gate(requested, text)`；标记契约
      `CHAOS_LSU_TIER_CAP: requested=<F|off> effective=<F|off> lookup_tier_enabled=<0|1>`。
      核对 effective==requested 且 enabled==1 且 requested==请求值；
      缺标记（旧二进制）/不一致/禁用 → 响亮拒绝。
- [x] 新测试：present+consistent → ok；missing → reject；mismatch → reject；
      disabled → reject；旧二进制（无标记）→ reject。
- [x] **C++ 契约**：不得改 C++；字段契约写入报告交 r6-fixcpp。

### T3 `[LSU][MDSPEC][R6-FIXTOOLS]` consumer_summary 解析 + 校验契约（RED→GREEN）
- [x] `tools/lsu_prop_fields.py`：`SUMMARY_PREFIX="CONSUMER-SUMMARY:"`、
      `parse_consumer_summary`、`validate_consumer_summary`、`read_stream`。
- [x] 新测试 `tests/test_lsu_r6_consumer_summary.py`：malformed/负计数/不守恒/
      简单截断 → 拒绝；守恒 → ok；summary 不产生 PROP-EVT 事件、不占层。
- [x] **C++ 契约**：字段契约写入报告交 r6-fixcpp。

### T4 `[LSU][MDSPEC][R6-FIXTOOLS]` checker 一致性 + campaign 报告 + 截断不掩盖
- [x] `tools/lsu_chain_check.py`：`check_admission` 接 `summaries`/`summary_issues`，
      malformed 响亮违规；新增 `GATE_VIOLATIONS` token；summary 永不参与链/终局。
- [x] `tools/lsu_campaign.py`：`write_chain_report` 展示 emitted/suppressed/logical
      total/conservation；截断流仍 admitted=False。
- [x] 新测试：小流 vs 聚合流 `path_event_ids/terminal/admitted/violations` 一致；
      truncated 聚合流仍不准入；无 summary 流兼容。

## 验证命令
- `python3 tests/test_lsu_r6_lookup_ftier_tooling.py`
- `python3 tests/test_lsu_r6_consumer_summary.py`
- `python3 tools/lsu_test_runner.py --quiet --json /tmp/r6fixtools_after.json`（NEW FAIL=0）

## 结果（2026-10-24 完成）
- T1+T2 合并为提交 ea17e3c9：hold 住 F0 legacy，F1-F6 传真实 tier；新增 CHAOS_LSU_TIER_CAP 运行时能力门（missing/mismatch/disabled ⇒ 响亮拒绝）。
- T3+T4 合并为提交 4c74e3ac：consumer_summary 解析/校验/门禁/报告 + 8 条规则测试。
- 套件：baseline FAIL=15/PASS=47 → after FAIL=13/PASS=51，**NEW FAIL=0**；两个基线 FAIL 套件转绿，新增 2 套件全 PASS。
- 停点：均未触碰（无 C++ 改动、未改 DIAG-RUNNER 文件、F-tier 身份一致、summary 守恒、小流/聚合流 checker 一致、旧二进制被响亮拒绝）。
- C++ 待办（交 r6-fixcpp）：CHAOS_LSU_TIER_CAP 启动标记；consumer_summary 发射。
