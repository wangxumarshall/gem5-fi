# R6-12RUNID-TABLE — 12-RunID 强制回归逐项表（L21，离线严格重判）

> 生成工具：`tools/lsu_r6_rejudge.py`（本表全部数字均由该工具真实运行产出；
> 命令见文末）。**未重跑 gem5**——用磁盘上保全的原始 PROP-EVT 流离线重判。

## 背景（为什么必须重判）

所有既有 pilot `chain_report.json` 由 `.claude/worktrees/r6-tlb-hooks/tools/`
内的检查器生成，而该 worktree 基于 `293b4003`，**不含** family-aware DAG 规则
（`317c71bf`）与 `check_admission`（`9a7da7cf`）。因此那些 report **非权威**：
它们把 `cache_access`/`cache_return` 当作 TLB 的 L1/L2，并把
`corr=none detection_layer=None outcome=run_end` 的 `chain_end` 当成 L5。

本表对 12 个 RunID 每个都调用严格检查器的两个公开入口：
`check_chain(events, oracle_outcome=...)` 与 `check_admission(bundle)`。
本工具不重写检查器，只 import 它（`tools.lsu_chain_check`）并补充检查器
不做的诚实记账（流完整性、sentinel 与空值区分、逐层 kind、关联键连续性、
注入值 before/after）。

### 检查器身份（可复现）

- 严格检查器 = `9a7da7cf` 的内容，以 `git cherry-pick -x 9a7da7cf` 落到本
  lane 分支（本 lane **不改写**该文件；cherry-pick 只为让本 lane 自洽可复现）。
- git blob `2191e98b3794b58f8abf5dec87e6142dcb1871c6`，文件 sha256
  `b59389487fe8afd2…`，与 `r6-gate@2b87cd9d` 的同名文件**逐字节相同**。
- 检查器自带套件在本 lane 复跑：`python3 tests/test_lsu_chain_check.py` →
  **ALL PASS**（13/13，含 `cross_request_edge` / `tlb_l1_faked_by_cache_access`
  / `ready_by_chain_end_only` / containment 路径）。

## 结论摘要（一屏）

| # | RunID | 流状态 | 检查器 verdict（本 lane 实测） | 用户硬性判据（本工具独立复检） |
|---|---|---|---|---|
| 1 | T02-F0-W4 | COMPLETE | terminal=`full` provable_to=`L5` admitted=**True** | cross_request_on_proven_path(L0:301→L1:301→L2:301→L4:391); l0_inj_before_after_empty; l5_detection_layer_sentinel:None; l5_is_chain_end_only(kind=chain_end detection_layer=None) |
| 2 | T02-F2-W4 | **MISSING** | 无流可判 | MISSING——不得造行 |
| 3 | T04-F0-W4 | COMPLETE | terminal=`full` provable_to=`L5` admitted=**True** | cross_request_on_proven_path(L0:301→L1:301→L2:301→L4:391); l0_inj_before_after_empty; l5_detection_layer_sentinel:None; l5_is_chain_end_only(kind=chain_end detection_layer=None) |
| 4 | T04-F2-W4 | COMPLETE | terminal=`full` provable_to=`L5` admitted=**True** | cross_request_on_proven_path(L0:301→L1:301→L2:301→L4:391); l0_inj_before_after_empty; l5_detection_layer_sentinel:None; l5_is_chain_end_only(kind=chain_end detection_layer=None) |
| 5 | T04-F6-W4 | COMPLETE | terminal=`full` provable_to=`L5` admitted=**True** | cross_request_on_proven_path(L0:301→L1:301→L2:301→L4:391); l0_inj_before_after_empty; l5_detection_layer_sentinel:None; l5_is_chain_end_only(kind=chain_end detection_layer=None) |
| 6 | T01-F0-W4 | COMPLETE | terminal=`detected_contained` provable_to=`L3` admitted=**False** | l0_inj_before_after_empty |
| 7 | T01-F1-W4 | **MISSING** | 无流可判 | MISSING——不得造行 |
| 8 | T01-F2-W4 | **MISSING** | 无流可判 | MISSING——不得造行 |
| 9 | T03-F5-W4 | **MISSING** | 无流可判 | MISSING——不得造行 |
| 10 | T10-F0-W4 | COMPLETE | terminal=`detected_contained` provable_to=`L3` admitted=**False** | l0_inj_before_after_empty |
| 11 | T10-F1-W4 | **MISSING** | 无流可判 | MISSING——不得造行 |
| 12 | T10-F2-W4 | **MISSING** | 无流可判 | MISSING——不得造行 |

**没有任何一个 RunID 被判为"通过"**：本表中 `admitted=True` 的样本在与
用户硬性判据冲突时仍必须判失败（见下节）。12 项中 0 项满足本 lane 的
独立复检（`MISSING` 6 项 + `admitted=False` 2 项 + `admitted=True 但违反硬性
判据` 4 项）。

## 关键发现（本 lane 独立复检，非检查器结论）

1. **MISSING 6 项**：`T02-F2-W4 · T01-F1-W4 · T01-F2-W4 · T03-F5-W4 ·
   T10-F1-W4 · T10-F2-W4` 在 `/home/sdc/gem5-fi-ding/runs/lsu/**` 下**不存在**
   任何 `<RunID>/seed*/prop_evt.txt.gz`。没有流 ⇒ 无法判定，**必须重跑**。
2. **`admitted=True` 的 4 项（T02-F0-W4 / T04-F0-W4 / T04-F2-W4 / T04-F6-W4）
   仍违反用户硬性判据**（这是本表最重要的诚实结论）：
   - `l5_is_chain_end_only`：L5 见证就是 `chain_end`，其
     `detection_layer=None`（字面 sentinel）、`contained=0`、
     `outcome=errant_commit_seen`。检查器 `_explicit_l5` 因
     `outcome != run_end` 而**认可**它 ⇒ `terminal=full`。用户裁决
     "chain_end 只能作生命周期件、不得单独充当 L5" ⇒ **应判失败**。
   - `l5_detection_layer_sentinel:None`：`detection_layer` 填的是字面
     `None` 而非空，检查器的 non-empty 必录测试因此**看不见这个缺口**。
   - `cross_request_on_proven_path(L0:301→…→L2:301→L4:391)`：已证路径上
     L2 见证 `request_id=301, dyn_inst_seq=301`，L4 见证
     `request_id=391, dyn_inst_seq=391`。检查器只在**相邻**见证且**两侧
     request_id 都已盖戳**时才报 `cross_request_edge`，而中间的 L3 见证
     （`sq_execute`）`request_id` 为空 ⇒ 跨请求跳变**被空洞见证掩盖**，
     `violations=[]`。这正是 B2-v2 要修的 "stronger cross-request guard"。
   - `l0_inj_before_after_empty`：L0 `inj` 的 `before`/`after`/
     `state_*`/`pa` **全空**；注入值只能从 L1 见证或
     `armtlb_injections.log` 读出（见下表各行的 injection 列）。
3. **T04-F0-W4 有 3 个副本流，结论不同**：`r6_tlb_pilot2`（10:31，含
   `chain_end`）判 `full/admitted=True`；`r6_tlb_pilot/out`（09:33）与
   `r6_tlb_verify/out`（10:05）**无 `chain_end` 事件**，判
   `provable_to_L4_then_unknown/admitted=False`。同一 RunID 的 3 份流
   结论不一致 ⇒ 必须明确指定权威副本。
4. **T01-F0-W4 / T10-F0-W4 判 `detected_contained` 是检查器语义缺陷**：
   二者 L2 见证 `tlb_translate_result` 自带
   `detection_layer=L2 contained=1 outcome=NoFault`，检查器的
   "显式 contained 检测"循环把**L2 事件**直接当 L5 终局 ⇒ `terminal=
   detected_contained`，而 `provable_to=L3`、`admitted=False`（由
   `no_closed_chain_and_no_containment` 兜底）。B2-v2 的 "containment
   option reachability" 正在修这一点。
5. **T01-F0-W4 / T10-F0-W4 的流此前 TRUNCATED（`stats.txt` 为 0 字节），
   本 lane 运行期间 lane L1-v2/L20-v2 完成了重跑**，现已 COMPLETE（9 事件、
   `stats.txt` 427682 B、oracle=Masked）。**本表以"最近一次 COMPLETE 副本"
   为准**；`r6_tlb_E_T10-F0-W4`（10:55，8 事件，TRUNCATED，oracle=Timeout）
   作为历史副本列在候选表内。**在最后一次重判之前，任何数字都可能再变**。

## 完成度汇总（决定谁还需要重跑）

- **有可用 COMPLETE 流（6）**：`T02-F0-W4 · T04-F0-W4 · T04-F2-W4 ·
  T04-F6-W4 · T01-F0-W4 · T10-F0-W4`。
- **TRUNCATED（0 项作为最新副本）**：`r6_tlb_E_T10-F0-W4` 的历史副本仍
  TRUNCATED；最新副本已完整。
- **MISSING（6）**：`T02-F2-W4 · T01-F1-W4 · T01-F2-W4 · T03-F5-W4 ·
  T10-F1-W4 · T10-F2-W4` —— **必须重跑才有流**。

## PROVISIONAL（必须重判）

本表在对"当前"检查器（blob `2191e98b`）判读。lane B2-v2 正在并发修改
检查器语义（**L5 = 真实检测事件；containment 选项可达性；更强的跨请求
守卫**）。B2-v2 落地后，本表**必须整表重跑**；在此之前，本表中
`admitted`/`terminal` 列以及"违反硬性判据"的判定均为 **provisional**。
`MISSING` 与流完整性（COMPLETE/TRUNCATED）两列不受检查器语义影响，
可直接采信。

## 复现命令（真实执行记录）

```
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-rejudge
python3 tools/lsu_r6_rejudge.py --json <out>/L21_rejudge.json --md <out>/L21_rejudge.md
python3 tools/lsu_r6_rejudge.py                 # 控制台逐 RunID 明细
python3 tests/test_lsu_chain_check.py           # 检查器自带套件：ALL PASS
```

JSON 全量证据：`/home/sdc/gem5-fi-ding/runs/lsu/r6_reports/L21_rejudge.json`
（含每个 RunID 的 `path_witnesses`、`field_gaps`、`correlation`、
`check_chain`、`check_admission`、全部候选流 sha256）。

---

# R6-12RUNID — offline strict re-judgement table (L21)

- checker: `tools/lsu_chain_check.py` sha256=`b59389487fe8afd2` — d32cdfe9 (cherry-pick -x of 9a7da7cf, blob 2191e98b = r6-gate strict checker)
- line format read: `PROP-EVT: kind=<k> key=value …`
- generated: 2026-10-23 11:56:46
- **CAVEAT (provisional):** Provisional: lane B2-v2 is concurrently changing checker semantics (L5 = real detection event; containment option reachability; stronger cross-request guard). This table must be RE-RUN after B2-v2 lands.

## Stream completeness (determines re-run need)

| RunID | status | events | sha256 | path |
|---|---|---|---|---|
| T02-F0-W4 | COMPLETE | 186 | a1189be7577fa7ae | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot2/T02-F0-W4/seed1/prop_evt.txt.gz` |
| T02-F2-W4 | MISSING | n/a | n/a | `-` |
| T04-F0-W4 | COMPLETE | 1574 | 2232f4de78e49a68 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1/prop_evt.txt.gz` |
| T04-F2-W4 | COMPLETE | 1574 | f195010367564d61 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_G_T04-F2-W4/T04-F2-W4/seed1/prop_evt.txt.gz` |
| T04-F6-W4 | COMPLETE | 1574 | c7cf13b8790721a8 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_G_T04-F6-W4/T04-F6-W4/seed1/prop_evt.txt.gz` |
| T01-F0-W4 | COMPLETE | 9 | de579336f26b2c6d | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_F_T01-F0-W4/T01-F0-W4/seed1/prop_evt.txt.gz` |
| T01-F1-W4 | MISSING | n/a | n/a | `-` |
| T01-F2-W4 | MISSING | n/a | n/a | `-` |
| T03-F5-W4 | MISSING | n/a | n/a | `-` |
| T10-F0-W4 | COMPLETE | 9 | d2c94fcf42d89215 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_F_T10-F0-W4/T10-F0-W4/seed1/prop_evt.txt.gz` |
| T10-F1-W4 | MISSING | n/a | n/a | `-` |
| T10-F2-W4 | MISSING | n/a | n/a | `-` |

## Per-RunID strict verdict

| RunID | stream | injected before→after | L0..L5 kinds | correlation keys | oracle | chain verdict | forbidden | evidence path |
|---|---|---|---|---|---|---|---|---|
| T02-F0-W4 | COMPLETE | L0 inj field=bit_flip before=<empty>→after=<empty> (pa=<empty>) ; L1 tlb_lookup field=post_lookup before=81d75→after=100040000081d75 ; injector_log: protection: model=none bits=2 -> Raw | L0[inj×1] L1[tlb_lookup×1] L2[tlb_pfn×1,tlb_translate_result×1] L3[cache_access×32,cache_return×32,lq_complete×3,mshr_alloc×18,mshr_merge×14,resp×21,sq_complete×1,sq_execute×1,sq_writeback×1] L4[consumer×54,errant_commit×1,taint_reg×3] L5[chain_end×1] | fault_id=1; parent_event_id(contiguous-linear); request_id=breaks/301|391; walk_id=none-nonzero; dyn_inst_seq=breaks | Crash | terminal=full; provable_to=L5; admitted=True; violations=[] | cross_request_on_proven_path(L0:301→L1:301→L2:301→L4:391); l0_inj_before_after_empty; l5_detection_layer_sentinel:None; l5_is_chain_end_only(kind=chain_end detection_layer=None) | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot2/T02-F0-W4/seed1/prop_evt.txt.gz` |
| T02-F2-W4 | MISSING | n/a | n/a | n/a | n/a | terminal=(none); provable_to=None; admitted=None; violations=['no_fault_chain'] | none | `-` |
| T04-F0-W4 | COMPLETE | L0 inj field=pfn_to_mapped_page before=<empty>→after=<empty> (pa=<empty>) ; L1 tlb_lookup field=post_lookup before=81d75→after=0 ; injector_log: Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8, old_pfn: 0x81d75, new_pfn: 0x0, FaultType: pfn_to_mapped_page, candidates: 31 | L0[inj×1] L1[tlb_lookup×1] L2[tlb_pfn×1,tlb_translate×29,tlb_translate_result×1] L3[cache_access×27,cache_fill×8,cache_return×27,lq_complete×11,lsq_sendfrag×29,mem_req×29,mshr_alloc×8,mshr_fill×8,mshr_free×8,mshr_merge×8,resp×29,sq_complete×1,sq_execute×1,sq_writeback×1] L4[consumer×1296,errant_commit×1,taint_reg×19] L5[chain_end×1] | fault_id=1; parent_event_id(contiguous-linear); request_id=breaks/301|391; walk_id=none-nonzero; dyn_inst_seq=breaks | Crash | terminal=full; provable_to=L5; admitted=True; violations=[] | cross_request_on_proven_path(L0:301→L1:301→L2:301→L4:391); l0_inj_before_after_empty; l5_detection_layer_sentinel:None; l5_is_chain_end_only(kind=chain_end detection_layer=None) | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1/prop_evt.txt.gz` |
| T04-F2-W4 | COMPLETE | L0 inj field=pfn_to_mapped_page before=<empty>→after=<empty> (pa=<empty>) ; L1 tlb_lookup field=post_lookup before=81d75→after=0 ; injector_log: Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8, old_pfn: 0x81d75, new_pfn: 0x0, FaultType: pfn_to_mapped_page, candidates: 31 | L0[inj×1] L1[tlb_lookup×1] L2[tlb_pfn×1,tlb_translate×29,tlb_translate_result×1] L3[cache_access×27,cache_fill×8,cache_return×27,lq_complete×11,lsq_sendfrag×29,mem_req×29,mshr_alloc×8,mshr_fill×8,mshr_free×8,mshr_merge×8,resp×29,sq_complete×1,sq_execute×1,sq_writeback×1] L4[consumer×1296,errant_commit×1,taint_reg×19] L5[chain_end×1] | fault_id=1; parent_event_id(contiguous-linear); request_id=breaks/301|391; walk_id=none-nonzero; dyn_inst_seq=breaks | Crash | terminal=full; provable_to=L5; admitted=True; violations=[] | cross_request_on_proven_path(L0:301→L1:301→L2:301→L4:391); l0_inj_before_after_empty; l5_detection_layer_sentinel:None; l5_is_chain_end_only(kind=chain_end detection_layer=None) | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_G_T04-F2-W4/T04-F2-W4/seed1/prop_evt.txt.gz` |
| T04-F6-W4 | COMPLETE | L0 inj field=pfn_to_mapped_page before=<empty>→after=<empty> (pa=<empty>) ; L1 tlb_lookup field=post_lookup before=81d75→after=0 ; injector_log: Tick: 237950940537, Site: arm_tlb_lookup_hit, VA: 0xffffffc009483fa8, old_pfn: 0x81d75, new_pfn: 0x0, FaultType: pfn_to_mapped_page, candidates: 31 | L0[inj×1] L1[tlb_lookup×1] L2[tlb_pfn×1,tlb_translate×29,tlb_translate_result×1] L3[cache_access×27,cache_fill×8,cache_return×27,lq_complete×11,lsq_sendfrag×29,mem_req×29,mshr_alloc×8,mshr_fill×8,mshr_free×8,mshr_merge×8,resp×29,sq_complete×1,sq_execute×1,sq_writeback×1] L4[consumer×1296,errant_commit×1,taint_reg×19] L5[chain_end×1] | fault_id=1; parent_event_id(contiguous-linear); request_id=breaks/301|391; walk_id=none-nonzero; dyn_inst_seq=breaks | Crash | terminal=full; provable_to=L5; admitted=True; violations=[] | cross_request_on_proven_path(L0:301→L1:301→L2:301→L4:391); l0_inj_before_after_empty; l5_detection_layer_sentinel:None; l5_is_chain_end_only(kind=chain_end detection_layer=None) | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_G_T04-F6-W4/T04-F6-W4/seed1/prop_evt.txt.gz` |
| T01-F0-W4 | COMPLETE | L0 inj field=bit_flip before=<empty>→after=<empty> (pa=<empty>) ; L1 tlb_lookup field=post_lookup before=81d75→after=100000000081d75 ; injector_log: protection: model=none bits=1 -> Raw | L0[inj×1] L1[tlb_lookup×1] L2[tlb_pfn×1,tlb_translate_result×1] L3[resp×1,sq_complete×1,sq_execute×1,sq_writeback×1] L4[-] L5[-] | fault_id=1; parent_event_id(contiguous-linear); request_id=contig/301; walk_id=none-nonzero; dyn_inst_seq=contig | Masked | terminal=detected_contained; provable_to=L3; admitted=False; violations=['no_closed_chain_and_no_containment: T01-F0-W4 既无 family-specific L0→L5 完整链，也无显式 containment——不得判 READY', 'ready_by_activated_only: T01-F0-W4 activated=1 本身不是 READY 依据（须完整链或 containment）', 'ready_by_chain_end_only: T01-F0-W4 仅存在 chain_end 事件，不构成 L5 结终局证据——不得据此判 READY'] | l0_inj_before_after_empty | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_F_T01-F0-W4/T01-F0-W4/seed1/prop_evt.txt.gz` |
| T01-F1-W4 | MISSING | n/a | n/a | n/a | n/a | terminal=(none); provable_to=None; admitted=None; violations=['no_fault_chain'] | none | `-` |
| T01-F2-W4 | MISSING | n/a | n/a | n/a | n/a | terminal=(none); provable_to=None; admitted=None; violations=['no_fault_chain'] | none | `-` |
| T03-F5-W4 | MISSING | n/a | n/a | n/a | n/a | terminal=(none); provable_to=None; admitted=None; violations=['no_fault_chain'] | none | `-` |
| T10-F0-W4 | COMPLETE | L0 inj field=bit_flip before=<empty>→after=<empty> (pa=<empty>) ; L1 tlb_lookup field=post_lookup before=81d75→after=100000000081d75 ; injector_log: protection: model=none bits=1 -> Raw | L0[inj×1] L1[tlb_lookup×1] L2[tlb_pfn×1,tlb_translate_result×1] L3[resp×1,sq_complete×1,sq_execute×1,sq_writeback×1] L4[-] L5[-] | fault_id=1; parent_event_id(contiguous-linear); request_id=contig/301; walk_id=none-nonzero; dyn_inst_seq=contig | Masked | terminal=detected_contained; provable_to=L3; admitted=False; violations=['no_closed_chain_and_no_containment: T10-F0-W4 既无 family-specific L0→L5 完整链，也无显式 containment——不得判 READY', 'ready_by_activated_only: T10-F0-W4 activated=1 本身不是 READY 依据（须完整链或 containment）', 'ready_by_chain_end_only: T10-F0-W4 仅存在 chain_end 事件，不构成 L5 结终局证据——不得据此判 READY'] | l0_inj_before_after_empty | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_F_T10-F0-W4/T10-F0-W4/seed1/prop_evt.txt.gz` |
| T10-F1-W4 | MISSING | n/a | n/a | n/a | n/a | terminal=(none); provable_to=None; admitted=None; violations=['no_fault_chain'] | none | `-` |
| T10-F2-W4 | MISSING | n/a | n/a | n/a | n/a | terminal=(none); provable_to=None; admitted=None; violations=['no_fault_chain'] | none | `-` |

## Per-layer mandatory-metric accounting (canonical candidate)

`empty` = family-contract field recorded blank; `sentinel:<v>` = populated with a placeholder (['-1', 'n/a', 'na', 'none', 'unknown']) that means 'not recorded'. Both fail '每层必录指标'; the strict checker's non-empty test sees neither the sentinel nor (on a non-admitted sample) the gap.

| RunID | layer | kind | field | state |
|---|---|---|---|---|
| T02-F0-W4 | L5 | chain_end | detection_layer | sentinel:None |
| T02-F0-W4 | L5 | chain_end | corr | sentinel:none |
| T04-F0-W4 | None | lsq_push | sq_idx | sentinel:-1 |
| T04-F0-W4 | L5 | chain_end | detection_layer | sentinel:None |
| T04-F0-W4 | L5 | chain_end | corr | sentinel:none |
| T04-F2-W4 | None | lsq_push | sq_idx | sentinel:-1 |
| T04-F2-W4 | L5 | chain_end | detection_layer | sentinel:None |
| T04-F2-W4 | L5 | chain_end | corr | sentinel:none |
| T04-F6-W4 | None | lsq_push | sq_idx | sentinel:-1 |
| T04-F6-W4 | L5 | chain_end | detection_layer | sentinel:None |
| T04-F6-W4 | L5 | chain_end | corr | sentinel:none |
| T01-F0-W4 | None | chain_end | detection_layer | sentinel:None |
| T01-F0-W4 | None | chain_end | corr | sentinel:none |
| T10-F0-W4 | None | chain_end | detection_layer | sentinel:None |
| T10-F0-W4 | None | chain_end | corr | sentinel:none |

## All candidate streams per RunID (multiple outdirs exist)

| RunID | candidate stream | status | events | terminal | admitted |
|---|---|---|---|---|---|
| T02-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot2/T02-F0-W4/seed1/prop_evt.txt.gz` | COMPLETE | 186 | full | True |
| T02-F2-W4 | `-` | MISSING | n/a | (none) | n/a |
| T04-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot2/T04-F0-W4/seed1/prop_evt.txt.gz` | COMPLETE | 1574 | full | True |
| T04-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_verify/out/T04-F0-W4/seed1/prop_evt.txt.gz` | COMPLETE | 1574 | provable_to_L4_then_unknown | False |
| T04-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_pilot/out/T04-F0-W4/seed1/prop_evt.txt.gz` | COMPLETE | 1574 | provable_to_L4_then_unknown | False |
| T04-F2-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_G_T04-F2-W4/T04-F2-W4/seed1/prop_evt.txt.gz` | COMPLETE | 1574 | full | True |
| T04-F6-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_G_T04-F6-W4/T04-F6-W4/seed1/prop_evt.txt.gz` | COMPLETE | 1574 | full | True |
| T01-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_F_T01-F0-W4/T01-F0-W4/seed1/prop_evt.txt.gz` | COMPLETE | 9 | detected_contained | False |
| T01-F1-W4 | `-` | MISSING | n/a | (none) | n/a |
| T01-F2-W4 | `-` | MISSING | n/a | (none) | n/a |
| T03-F5-W4 | `-` | MISSING | n/a | (none) | n/a |
| T10-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_F_T10-F0-W4/T10-F0-W4/seed1/prop_evt.txt.gz` | COMPLETE | 9 | detected_contained | False |
| T10-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_tlb_E_T10-F0-W4/T10-F0-W4/seed1/prop_evt.txt.gz` | TRUNCATED | 8 | detected_contained | False |
| T10-F1-W4 | `-` | MISSING | n/a | (none) | n/a |
| T10-F2-W4 | `-` | MISSING | n/a | (none) | n/a |

