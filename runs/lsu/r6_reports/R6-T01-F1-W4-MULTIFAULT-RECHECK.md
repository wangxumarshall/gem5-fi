# R6 T01-F1-W4 seed2/seed3 多 fault 只读复核

> 生成：2026-10-27。复核对象：`runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/T01-F1-W4-seed2.md`、`-seed3.md`。
> 交叉复核：`T01-F1-W1` seed2/seed3（同类的多 fault + run 级计数口径）。
> 原始 `prop_evt.txt.gz`、`chain_report.json`、`cell_results.json`、`stats.txt` 均未修改；未运行 gem5 / campaign。
> 机器可读版：`R6-T01-F1-W4-MULTIFAULT-RECHECK.json`。

## 1. 逐 fault 终局（权威 checker）

### T01-F1-W4 seed2

| fault_id | terminal | provable_to | 事件数 | 是否闭合 |
|---|---|---|---|---|
| 1 | `full` | L5 | 370 | 是（唯一 L5 完整链，escape-first 代表故障） |
| 2 | `detected_contained` | L2 | 5 | 是（L2 含住） |
| 3 | `provable_to_L4_then_unknown` | L4 | 26735 | 否（开放 L4） |
| 4 | `detected_contained` | L2 | 5 | 是（L2 含住） |
| 5 | `provable_to_L4_then_unknown` | L4 | 2425 | 否（开放 L4） |

汇总：**1 full + 2 contained + 2 open**。代表故障 = fault 1（唯一 `full`，escape-first 规则选中）。

### T01-F1-W4 seed3

| fault_id | terminal | provable_to | 事件数 | 是否闭合 |
|---|---|---|---|---|
| 1 | `full` | L5 | 1353 | 是（唯一 L5 完整链，代表故障） |
| 2 | `detected_contained` | L2 | 5 | 是（L2 含住） |
| 3 | `provable_to_L4_then_unknown` | L4 | 2087 | 否（开放 L4） |

汇总：**1 full + 1 contained + 1 open**。代表故障 = fault 1。

### T01-F1-W1 seed2/seed3（交叉复核）

| RunID/seed | faults | 逐 fault 汇总 | 代表故障 |
|---|---|---|---|
| T01-F1-W1 seed2 | 2 | 1 full + 1 open L4 | fault 1（full） |
| T01-F1-W1 seed3 | 3 | 1 full + 2 contained (provable_to L5) | fault 1（full） |

## 2. `cell_results.json` 的实际语义

| 项 | seed2 | seed3 |
|---|---|---|
| `n_runs` | 1 | 1 |
| `attempted` | 5530941 | 3527639 |
| `activated` | 5 | 3 |
| `classes` | Masked=0, Detected/Contained=0, SDC=0, **Crash=5**, Timeout=0 | Masked=0, Detected/Contained=0, SDC=0, **Crash=3**, Timeout=0 |
| `runs[0].outcome` | Crash | Crash |
| `count_contradiction` | false | false |
| `conservation` | OK | OK |
| `stats.numFaultsInjected` | 5 | 3 |

## 3. 两套口径（不是数据矛盾）

- **campaign 是 run 级口径**：`tools/lsu_campaign.py` 的 `classify_fs_run()`（约 346–395 行）把整次运行判定为 `Crash`，然后 `classes[oc] = injected`；聚合时 `classes[oc] += act`（约 640 行）。因此 `classes.Crash=5/3` 的含义是
  **“本次运行（run-level oracle = Crash）中有 5/3 个 activated fault”**，
  不是“5/3 条链都走到 L5”。
- **checker 是 per-fault 口径**：`chain_report.faults[fid].terminal / provable_to` 逐 fault 给出
  seed2 = `1 full + 2 L2 contained + 2 open L4`，seed3 = `1 full + 1 L2 contained + 1 open L4`。
- 两者统计单元不同，**样本级结论一致**（该次运行总结果为 Crash；代表故障确实到 L5），不存在同一量上的自相矛盾。
- `count_contradiction=false` 的依据成立：`attempted > 0` 且 `injected == stats.board.chaos_armtlb.numFaultsInjected`（5=5、3=3）。

## 4. `taint_reg` 字段覆盖

- 代表故障 fault 1 的主链 `taint_reg` 在两个 seed 都带 `arch_reg`/`phys_reg`：
  - seed2 event 19：`arch_reg=12`、`phys_reg=110`；
  - seed3 event 37：`arch_reg=4`、`phys_reg=68`。
- 原始流仍存在 `taint_reg` 行缺这两个字段：seed2 274/3214，seed3 41/138；其中包含 sibling fault 5 的主链事件 24870。
- 结论：这是**字段覆盖缺口**，不是链一致性错误；不得伪造成有值，也不影响代表故障的完整链。

## 5. 判定

1. 未发现工具输出在 fault 级语义上的自相矛盾；无需生成“工具缺陷”改判。
2. 文档此前把 “campaign 逐 activated 计数” 与 “checker 逐 fault 终局” 混称为“部分不一致”；现修正为并列两套口径。
3. 代表故障 = fault 1（唯一 `full`）；sibling fault 全部保留，未删除、未并入主链。
4. 原始流零修改，未运行 gem5；证据 SHA 不变。
5. 文档判定：`chain_evidence_status=PASS`（admitted/certified/violations=[] + 真实 L5 见证）；`experiment_identity_status=MATCH`（W4 载体 `tlb_probe.rcS` 与矩阵一致）；`overall_experiment_status=PASS`，并保留 `taint_reg` 覆盖缺口与矩阵“VPN tag vs PFN”字段口径记录。
