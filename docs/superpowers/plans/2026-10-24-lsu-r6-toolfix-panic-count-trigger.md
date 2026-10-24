# R6 工具层三缺陷修复（T02-F2-W4 canary 复判）

- 日期：2026-10-24
- 分支/工作树：`lsu-mdspec-20261019` @ `/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019`
- 范围：**仅 `tools/**` 与 `tests/**`**。禁止改 C++、禁止重建 gem5、禁止改原始证据、禁止放宽 admission/conservation。
- 冻结身份（不得改变）：
  - `binary_source_head = 5ab37bc8ce9d8ee8c005e17025cf7bd068f696c9`
  - `binary_sha256      = 3b9a43a4fd54233bcc49a80df6ec6a7ab8535dd5771f1efff1af6fe245cdcb88`
  - 冻结二进制路径 = `.claude/worktrees/lsu-mdspec-20261019/CHAOS/gem5/build/ARM/gem5.opt`（**非** repo-root）
  - `analysis_tool_head = <本轮工具修复后的提交>`（与 binary_source_head 明确区分）

## 背景：已确认的原始事实（T02-F2-W4 / seed1）

| 事实 | 值 | 来源 |
|---|---|---|
| exit_code | 0 | `seed1/run.out` |
| CHAOS_LSU_TRIGGER | `attempted=110149 eligible=110149 injected=1` | `seed1/run.out:22` |
| stats | `board.chaos_armtlb.numFaultsInjected 1` | `seed1/stats.txt` |
| armtlb_injections.log | 1 条 `Site: arm_tlb_lookup_tier`（诊断）+ 1 条 `Site: arm_tlb_lookup_hit`（真注入，带 VA/old_pfn/new_pfn） | `seed1/armtlb_injections.log` |
| 受控退出 | `[arm_chaos_fs] KERNEL PANIC under fault — exiting (classify: Crash/DUE per fs_mode)` | `seed1/run.out:24` |
| 观测链 | event_count=1100, terminal=full, provable_to=L5, L0→L5 全 proven, errant_commit, admitted=True, violations=[], consumer summary conservation=ok | `chain_report.json` |
| 当前 cell_results.json | `attempted=0, activated=2, outcome=Unclassified, conservation=VIOLATION, count_contradiction=true` | 工具错 |

**结论：这是 campaign 工具层错误，不是传播链失败。**

## 三缺陷根因（已实证，非推测）

1. **注入计数** — `count_armtlb_injections` 只排除 `arm_tlb_walk_issue_probe` / `arm_tlb_lookup_hit_skipped`，未排除档位诊断 `arm_tlb_lookup_tier`（该行只出现在 F1–F6 档位运行里；F0 无此行，故 T02-F0 计数正确=1，T02-F2=2）。→ `activated=2`。
2. **TRIGGER 摘要** — FS 分类路径 `classify_fs_run` **从不解析** `CHAOS_LSU_TRIGGER`（同仓库 `lsu_l5_classify.py:60`、`lsu_obs_core.py:177` 都有该正则，唯独 FS 路径没有），`attempted/eligible` 恒为 `None`；单格汇总 `attempted += int(r.get("attempted", 0) or 0)`（`lsu_campaign.py:2609`）把 `None` 静默转 `0`。→ `attempted=0`。
3. **退出分类** — `classify_fs_run` 只认旧口径 `"Oops" in terminal` / `"Kernel oops in guest"`，未识别 2026-10-24 新增的受控 `[arm_chaos_fs] KERNEL PANIC under fault — exiting`。→ `outcome=Unclassified` → `classes` 全零 → `conservation=VIOLATION`。**注**：`configs/fs/lsu_multicore_fs.py` 用 `[lsu_multicore_fs]` 前缀，`classify_fsmc_run` 必须匹配自己的配置文本，不能复用 arm_chaos_fs 字面量。

---

## 提交 1 — [R6-FIXEXIT2] 受控 KERNEL PANIC/OOPS 精确分类

文件：`tools/lsu_campaign.py`（`classify_fs_run`、`classify_fsmc_run`）、`tests/test_lsu_campaign_fs_exit_class.py`

- [x] 保留工作树既有的精确字面匹配改动（不加宽泛 panic/Oops 子串）。
- [x] 用具名正则精确匹配**两种配置**的受控标记行：
      `^\[\s*(arm_chaos_fs|lsu_multicore_fs)\s*\] KERNEL (PANIC|OOPS) under fault — exiting \(classify: Crash/DUE per fs_mode\)\s*$`
      （锚定整行；em-dash U+2014 精确；PANIC→`crash_kind=kernel_panic`，OOPS→`kernel_oops`）。
- [x] 两函数各自先试精确标记；未命中再走既有 OOPS 回退（`"Oops" in terminal` / `"Kernel oops in guest"`），未知退出保持 `Unclassified`。
- [x] 测试：受控 PANIC 行 + exit_code=0 → `Crash/kernel_panic`；受控 OOPS 行 → `Crash/kernel_oops`；两种前缀各一例；普通日志含 "panic" 单词但**无**受控标记行 → 仍 `Unclassified`；未知正常退出 → `Unclassified`。
- [x] 验证：`python3 tests/test_lsu_campaign_fs_exit_class.py`（rc=0，逐条 PASS）。

## 提交 2 — [R6-FIXCOUNT] armtlb 应用注入计数 + 三源交叉核对

文件：`tools/lsu_campaign.py`（`_ARMTLB_DIAG_SITES` / `count_armtlb_injections` / 新 `armtlb_count_sources`）、`tests/test_lsu_campaign_armtlb_count.py`

- [x] `_ARMTLB_DIAG_SITES` 增加 `arm_tlb_lookup_tier`（能力/档位诊断，非注入）。
- [x] `count_armtlb_injections` 只计**已应用**注入；对 `Site: arm_tlb_lookup_hit` 要求同时出现 `VA:`、`old_pfn:`、`new_pfn:` 应用字段，缺字段的行不计（并计入一个「malformed」计数）。
- [x] 新增 `armtlb_count_sources(outdir, stdout_text)`：返回
      `{"log": n1, "trigger": n2|None, "stats": n3|None, "contradiction": bool, "detail": {...}}`；
      `n2` 取自 stdout `CHAOS_LSU_TRIGGER ... injected=`；`n3` 取自 `stats.txt` 的 `...armtlb.numFaultsInjected`。
      三者在**可用**来源间必须完全一致；不一致 → `contradiction=True`（响亮，绝不静默选一个）。
- [x] `classify_fs_run` 用 `armtlb_count_sources` 决定 `injected/activated`，并把 `count_sources` / `count_contradiction` 写进返回字典。
- [x] 测试：tier 诊断行 + 1 条真实 hit → `activated=1`；真实 hit 缺 `old_pfn` → 不计入且报 malformed；三源一致 → 无 contradiction；人为造三源不一致 → `contradiction=True`（响亮）；T07 `arm_tlb_lookup` false_hit 与 T08 `arm_tlb_walk_issue_drop` 仍照旧计数（回归）。
- [x] 验证：`python3 tests/test_lsu_campaign_armtlb_count.py`（rc=0）。

## 提交 3 — [R6-FIXTRIGGER] FS 路径接入权威漏斗摘要

文件：`tools/lsu_campaign.py`（`classify_fs_run` 与新解析助手；`run_cell_adaptive` 汇总）、`tests/test_lsu_campaign_fs_trigger.py`

- [ ] 复用既有正则解析 `run_stdout` 的 `CHAOS_LSU_TRIGGER: ... attempted= eligible= injected=`，回填 `attempted/eligible`（`injected` 由提交 2 的计数提供，两者须一致，否则 contradiction）。
- [ ] stdout 无 TRIGGER 行时回退注入日志 `FUNNEL:` 最后一行（与 `lsu_obs_core.parse_l0` 同款）；两者皆无 → **不默认 0**：置 `funnel_missing=True` 且 `attempted=None`。
- [ ] 单格汇总（`lsu_campaign.py:2609` 一带）：任何样本 `attempted is None` 或 `count_contradiction` 或 `funnel_missing` → cell 级 `count_contradiction=True` + 响亮 note，**不静默把 None 变 0**；不影响 SE 家族既有语义（SE 走 `lsu_l5_classify.py`，行为不变）。
- [ ] 测试：本格解析 `attempted=110149/eligible=110149/injected=1`；缺失 TRIGGER → `attempted is None` 且 `funnel_missing=True`（非 0）；整格集成（模拟本格三缺陷叠加）得
      `attempted=110149, activated=1, classes.Crash=1, conservation=OK, count_contradiction=False`。
- [ ] 验证：`python3 tests/test_lsu_campaign_fs_trigger.py`（rc=0）。

## 提交后（非代码提交）

- [ ] **完整回归**：`python3 -m pytest tests/ -q` + 独立脚本套件（`tools/lsu_ready_contract.py --gate` 口径），确认 **NEW FAIL=0**。出现新增失败立即停止汇报。
- [ ] **T02-F2-W4 离线复判**（不跑 gem5、不覆盖旧报告）：以 `runs/lsu/r6_c5_T02-F2-W4/T02-F2-W4/seed1` 原始证据重生成报告到独立目录（如 `runs/lsu/r6_rejudge_T02-F2-W4_toolfix/`），产出字段级旧/新 diff。核验 §五 全部判据；传播链/admission/violations 意外变化 → 停止汇报。
- [ ] **剩余四格 canary**（仅在复判全过后）：T01-F0-W4、T04-F0-W4、T04-F2-W4、T04-F6-W4 各 1 seed，全新目录，并发 ≤3，启动/结束各核二进制 SHA。
