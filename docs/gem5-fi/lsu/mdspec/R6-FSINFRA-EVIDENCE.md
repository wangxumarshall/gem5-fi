# R6-FSINFRA — FS-INFRA 24 行逐行证据清单（2026-10-23，lane L33 / branch `r6-fsinfra`）

本文件是 `tools/lsu_runid_map.py` 更正陈旧键 `workload:workload-level:blocked(fs-infra:
TLB workload needs FS)` 时逐行引用的**证据锚点**。`runid_map` 每个 T 系列 W4 行的
`fs_workload.evidence` 指向本文件 `#<RunID>` 段，`fs_workload.run_artifact` 给出该段
依据的真机产物路径（`runs/lsu/...`，属运行时产物、可能随轮转失效；本文件为**耐久**锚点）。

## 判据（引用，不自立口径）

- **被反驳的旧键**（`tools/lsu_campaign.py:237` → `WL_BLOCKED["TLB-AliasPerm"]`）：
  `blocked(fs-infra: TLB workload needs FS)`。该键由 `lsu_runid_map._resolve_workload`
  以**负载级、模型无关**方式发出——它对 `resolve_cell` 的 armtlb FS 特例（T 系列走
  `fs:tlb_probe` 载体）一无所知。已被真机运行反驳：
  `docs/gem5-fi/lsu/mdspec/R5-FS-PILOT-EVIDENCE.md`（T01/T04-F0-W4 在 FS 上
  `activated=1`；T04-F0-W4 链 L0→L5 full）；`R5-ADMISSION-CLOSEOUT.md` §4.3 / §6；
  `blockers_for_approval.md` §FS-INFRA（"并非缺 FS 基础设施…该旧措辞已被本轮真机证据反驳"）。
- **真正的残余阻塞**（`blockers_for_approval.md` §FS-INFRA 解除条件）："逐格（含
  T05–T08 新模式）真机 30 activated pilot 后，解除 TLB-AliasPerm 键并重生成
  runid_map → 契约"。**无任何一格**达到该条件——本清单中全部试点均为 **1 seed**
  （`n_runs=1`、`stop_reason=seed-cap(1)`）。故 24 行**不由本 lane 解锁**（未放宽任何
  阈值、未改分母、未动分类）。
- **T05–T08 另有独立模型级阻塞**：`lsu_campaign.MODEL_BLOCKED`（T05/T06/T07 = 模式已落地
  但缺真机覆盖广度；T08 = walk 子模型 b/c/d 无真机覆盖）。该阻塞**不经 runid_map**，
  本 lane 不动（属 campaign / 集成裁决）。

## 有真机 pilot 证据的行（16）

### T01-F0-W4
- run artifact：`runs/lsu/r6_tlb_F_T01-F0-W4`（`cell_results.json`：activated=1，
  classes Masked=1；`chain_report.json` terminal=`provable_to_L0_then_unknown`）
- 另见 `R5-FS-PILOT-EVIDENCE.md` 正文（`arm_tlb_lookup_hit`，pfn 0x81d75→0x100000000081d75）

### T01-F1-W4
- run artifact：`R5-FS-PILOT-EVIDENCE.md` §1 批跑表（activated=1，outcome Masked）
- 注：链流未留存（L29 §6.3 记 T01-F1-W4 无 prop-evt 流）

### T01-F2-W4
- run artifact：`R5-FS-PILOT-EVIDENCE.md` §1 批跑表（activated=1，outcome Masked）
- 注：链流未留存（L29 §6.3）

### T02-F0-W4
- run artifact：`runs/lsu/r6_tlb_pilot2`（activated=1，Crash=1；terminal=`full`）

### T02-F2-W4
- run artifact：`R5-FS-PILOT-EVIDENCE.md` §1 批跑表（activated=1，Crash，链 full，L5）
- 注：链流未留存（L29 §6.3）

### T03-F5-W4
- run artifact：`runs/lsu/r6_tlb_I_T03-F5-W4`（activated=1，Masked=1；
  terminal=`detected_contained`）

### T04-F0-W4
- run artifact：`runs/lsu/r6_tlb_pilot2`（activated=1，Crash=1；terminal=`full` L0→L5，
  1572 事件）——与 `R5-FS-PILOT-EVIDENCE.md` 正文一致

### T04-F2-W4
- run artifact：`runs/lsu/r6_tlb_G_T04-F2-W4`（activated=1，Crash=1；terminal=`full` L0→L5）

### T04-F6-W4
- run artifact：`runs/lsu/r6_tlb_G_T04-F6-W4`（activated=1，Crash=1；terminal=`full` L0→L5）

### T05-F0-W4
- run artifact：`runs/lsu/r6_tlb_pilot2`（activated=1，Masked=1；
  terminal=`provable_to_L0_then_unknown`）
- 链准入：`L29.md` §3 记 T05-F0-W4 `chain.admitted=False`（`no_closed_chain_and_no_containment`）

### T06-F0-W4
- run artifact：`runs/lsu/r6_tlb_D_T06-F0-W4`（activated=1，Timeout=1；
  本目录 `chain_report.json` terminal=`provable_to_L0_then_unknown`）
- 链准入：`L29.md` §3 在修复后的门禁下记 T06-F0-W4 `admitted=True`,
  `terminal=detected_contained`, 零违规（依赖 L28 的 `pilot_evidence_r6final.json`）

### T07-F0-W4
- run artifact：`runs/lsu/r6_tlb_pilot2`（activated=1，Timeout=1；
  terminal=`provable_to_L0_then_unknown`）

### T08-F0-W4
- run artifact：`runs/lsu/r6_tlb_C_T08-F0-W4`（activated=1，Timeout=1；
  terminal=`provable_to_L0_then_unknown`）
- 链准入：`L29.md` §3 记 T08-F0-W4 `admitted=True`, `terminal=detected_contained`, 零违规
- 另有 `docs/gem5-fi/lsu/mdspec/R4-8-FS-W1-report.md` §4.3（walk_id 配对、field=lost）

### T10-F0-W4
- run artifact：`runs/lsu/r6_tlb_E_T10-F0-W4`（activated=1，Timeout=1；
  terminal=`provable_to_L0_then_unknown`）
- 另见 `R5-FS-PILOT-EVIDENCE.md` §1（activated=1，Masked）

### T10-F1-W4
- run artifact：`R5-FS-PILOT-EVIDENCE.md` §1 批跑表（activated=1，Masked）
- 注：链流未留存（L29 §6.3）

### T10-F2-W4
- run artifact：`R5-FS-PILOT-EVIDENCE.md` §1 批跑表（activated=1，Masked）
- 注：链流未留存（L29 §6.3）

## 无逐格 FS pilot 产物的行（8）

以下 8 格**没有任何**逐格 FS pilot 产物（盘上无 `cell_results.json`，R5 §1 批跑表亦未列）：
`T05-F2-W4`、`T05-F6-W4`、`T06-F2-W4`、`T06-F6-W4`、`T07-F4-W4`、`T07-F6-W4`、
`T08-F4-W4`、`T08-F6-W4`。其 corrected 键如实写明"无逐格 pilot"（`run_artifact` 为空）。

## 复现

```bash
# 逐格真机产物（activated/outcome）
find runs/lsu/r6_tlb_* -name cell_results.json -exec python3 -c \
  'import json,sys; d=json.load(open(sys.argv[1])); print(d["runid"], d["activated"], d["classes"])' {} \;
# 链 terminal
find runs/lsu/r6_tlb_* -name chain_report.json
# 被反驳的旧键来源
python3 -c "import sys; sys.path.insert(0,'tools'); import lsu_campaign as lc; print(lc.WL_BLOCKED['TLB-AliasPerm'])"
```
