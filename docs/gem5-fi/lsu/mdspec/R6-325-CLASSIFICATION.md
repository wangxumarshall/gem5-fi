# R6 — 325 RunID 证据分级（L31 独立审计）

- Lane **L31**（READ-ONLY audit）。Worktree `.claude/worktrees/r6-audit`（branch `r6-audit`, base `lsu-mdspec-20261019` @ `040688f2`）。
- 权威契约：`r6-gate` worktree 的 `docs/gem5-fi/lsu/mdspec/ready_contract.json`（2026-10-23 12:45，最新）。
- 独立测量工具：`tools/lsu_l31_bucket_audit.py`（L31 新写；`check_admission` 逐字 import 自 `origin/r6-gate` 的 `tools/lsu_chain_check.py`，未改一行）。
- 证据发现：对全主机 `find / -name 'prop_evt*.gz'`（448 条，列表 `/tmp/prop_evt_host.txt`），按 `<RunID>` 正则归属；每条流做 **完整 gzip 顺序解压到 EOF** + 兄弟 `stats.txt` 非空判定。
- 严格判定用契约自己的 `event_cap = 4000`。

> ## ⚠️ 诚实前提（用户明令）
> **"没有事件流" ≠ "没有传播"，更 ≠ "Masked"。** 缺流只意味着**未被测量**。
> 本文件 bucket 1 一律记为 **`never-run / 无 prop_evt`（未测量）**，绝不写成"无传播""被掩盖"。
> `check_admission` 在缺事件处只报 `provable_to_Ln_then_unknown`，契约明令不得外推 Masked —— 本审计遵守该纪律。

---

## 一、五个 bucket（主分区，互斥，Σ = 325）

**优先级（主分区，一个 RunID 只落一格）：4 规格裁决 > 5 外部/基础设施 > 3 完整链/containment > 2 已执行未闭合 > 1 未执行。**

| # | bucket | COUNT |
|---|---|---|
| 1 | 尚未执行、无 prop_evt（never-run / no prop_evt） | **195** |
| 2 | 已执行但传播链不完整（executed, chain incomplete） | **46** |
| 3 | 已形成完整链或显式 containment | **0** |
| 4 | 规格决策阻塞（spec-ruling blocked） | **10** |
| 5 | 外部资源/基础设施阻塞（external resource / infra blocked） | **74** |
| | **Σ** | **325** |

### Bucket 4 — 规格决策阻塞（10）
契约 `RULING`(6) ∪ `UNRESOLVED`(4)。A06 = AGU load 侧定宽契约 + load SHRINK **源码实证结构性不可达**；S10-F2 = F2 首抽下界 ≫ 实测流长（规格级拒绝）。S01/S02-F0-W1 = span census 未收敛（用 `UNRESOLVED` 归此格）。

`A06-F0-W3, A06-F0-W5, A06-F2-W3, A06-F2-W5, A06-F6-W3, A06-F6-W5, S01-F0-W1, S02-F0-W1, S10-F2-W5, S10-F2-W9`

### Bucket 5 — 外部资源/基础设施阻塞（74）
契约 `LICENSE`(12) + `FS-MULTICORE`(35) + `FS-INFRA`(24) + `MODE-UNIMPL`(3)。
- LICENSE = SPEC CPU2017 授权缺失（W11 负载不可得）。
- FS-MULTICORE = 多核 FS（litmus MP/SB/LB/IRIW、PARSEC 共享队列）语义。
- FS-INFRA = TLB 翻译负载的 FS checkpoint 流水线未逐格 pilot（载体已就绪，见 `blockers_for_approval.md`）。
- MODE-UNIMPL = 规格表 10 标注"先实现"的 T08 新模式未实现。

`C08-F0-W7, C08-F2-W7, C08-F5-W7, C08-F6-W7, C15-F0-W11, C15-F4-W11, C15-F6-W11, L04-F0-W11, L04-F2-W11, L04-F6-W11, O01-F0-W7, O01-F2-W7, O01-F6-W7, O02-F0-W7, O02-F2-W7, O02-F5-W7, O02-F6-W7, O03-F0-W7, O03-F2-W7, O03-F6-W7, O04-F0-W7, O04-F2-W7, O04-F6-W7, O05-F0-W7, O05-F4-W7, O05-F6-W7, O06-F0-W7, O06-F4-W7, O06-F6-W7, O07-F0-W7, O07-F2-W7, O07-F6-W7, O09-F0-W13, O09-F0-W7, O09-F1-W13, O09-F1-W7, O09-F2-W13, O09-F2-W7, P09-F0-W13, P09-F4-W13, P09-F6-W13, S13-F0-W11, S13-F1-W11, S13-F2-W11, T01-F0-W4, T01-F1-W4, T01-F2-W4, T02-F0-W4, T02-F2-W4, T03-F5-W4, T04-F0-W4, T04-F2-W4, T04-F6-W4, T05-F0-W4, T05-F2-W4, T05-F6-W4, T06-F0-W4, T06-F2-W4, T06-F6-W4, T07-F0-W4, T07-F4-W4, T07-F6-W4, T08-F0-W4, T08-F0-W9, T08-F4-W4, T08-F4-W9, T08-F6-W4, T08-F6-W9, T10-F0-W11, T10-F0-W4, T10-F1-W11, T10-F1-W4, T10-F2-W11, T10-F2-W4`

### Bucket 3 — 完整链 / 显式 containment（主分区 0）
**0。** 见 §三：`admitted = 0/325`（两个契约变体与本独立复算一致）。唯一"显式 containment 可被直接调用承认"的 RunID 是 **T08-F0-W4**（`T08-F0-W4/seed1`，L2 `tlb_translate_result`/`walk_refill_lost`/`translation_blocked`），但其流 gz 截断、且它在上游就是 FS-INFRA，被 bucket 5 吸收 —— 故主分区 bucket 3 为空。

### Bucket 2 — 已执行但传播链不完整（46）
= `CHAIN-UNPROVEN`(43) ∪ `CHAIN-EVIDENCE-MISSING`(198) 中**有流**者（含截断流）。每条独立复算的 terminal 见 §四。

`A01-F0-W3, A04-F0-W3, A07-F0-W3, A07-F0-W5, A07-F4-W3, A07-F4-W5, A07-F6-W3, A07-F6-W5, C01-F0-W1, C01-F0-W6, C09-F0-W10, C09-F0-W6, C11-F0-W6, C11-F6-W6, C12-F0-W6, C12-F6-W6, C14-F5-W10, C14-F5-W6, C15-F0-W10, C15-F0-W6, C15-F4-W10, C15-F4-W6, C15-F6-W10, C15-F6-W6, L01-F0-W5, L04-F0-W12, L04-F0-W5, L04-F2-W12, L04-F2-W5, L04-F6-W12, L04-F6-W5, P01-F0-W8, P06-F0-W6, P06-F0-W8, P06-F2-W6, P06-F2-W8, P06-F6-W6, P06-F6-W8, S01-F0-W5, S02-F0-W5, S04-F0-W5, S05-F0-W5, S10-F0-W5, S10-F0-W9, S10-F5-W5, S10-F5-W9`

### Bucket 1 — 尚未执行、无 prop_evt（195）
= `CHAIN-*` 中主机上**任何位置都找不到 `prop_evt`** 者。**注意：这是"未测量"，不是"无传播"。**

`A01-F0-W9, A01-F1-W3, A01-F1-W9, A01-F2-W3, A01-F2-W9, A02-F0-W3, A02-F0-W9, A02-F2-W3, A02-F2-W9, A03-F5-W10, A03-F5-W3, A04-F0-W0, A04-F2-W0, A04-F2-W3, A04-F6-W0, A04-F6-W3, A05-F0-W3, A05-F2-W3, A05-F6-W3, A08-F0-W3, A08-F0-W5, A08-F2-W3, A08-F2-W5, A08-F6-W3, A08-F6-W5, C01-F1-W1, C01-F1-W6, C01-F2-W1, C01-F2-W6, C02-F0-W1, C02-F0-W6, C02-F2-W1, C02-F2-W6, C03-F5-W10, C03-F5-W6, C04-F0-W1, C04-F0-W6, C04-F1-W1, C04-F1-W6, C04-F2-W1, C04-F2-W6, C05-F0-W6, C05-F2-W6, C05-F6-W6, C06-F0-W6, C06-F2-W6, C06-F5-W6, C07-F0-W6, C07-F2-W6, C07-F5-W6, C07-F6-W6, C08-F0-W6, C08-F2-W6, C08-F5-W6, C08-F6-W6, C09-F2-W10, C09-F2-W6, C09-F6-W10, C09-F6-W6, C10-F0-W10, C10-F0-W6, C10-F3-W10, C10-F3-W6, C10-F5-W10, C10-F5-W6, C11-F0-W10, C11-F2-W10, C11-F2-W6, C11-F4-W10, C11-F4-W6, C11-F6-W10, C12-F0-W10, C12-F4-W10, C12-F4-W6, C12-F6-W10, L01-F0-W1, L01-F0-W12, L01-F1-W1, L01-F1-W12, L01-F1-W5, L01-F2-W1, L01-F2-W12, L01-F2-W5, L02-F0-W12, L02-F0-W5, L02-F2-W12, L02-F2-W5, L02-F6-W12, L02-F6-W5, L03-F0-W12, L03-F0-W5, L03-F4-W12, L03-F4-W5, L03-F6-W12, L03-F6-W5, P01-F0-W2, P01-F1-W2, P01-F1-W8, P01-F2-W2, P01-F2-W8, P02-F0-W10, P02-F0-W8, P02-F3-W10, P02-F3-W8, P02-F5-W10, P02-F5-W8, P03-F0-W8, P03-F0-W9, P03-F2-W8, P03-F2-W9, P03-F6-W8, P03-F6-W9, P04-F0-W2, P04-F0-W8, P04-F4-W2, P04-F4-W8, P04-F5-W2, P04-F5-W8, P05-F0-W10, P05-F0-W8, P05-F4-W10, P05-F4-W8, P05-F6-W10, P05-F6-W8, P07-F0-W6, P07-F0-W8, P07-F2-W6, P07-F2-W8, P07-F6-W6, P07-F6-W8, P08-F5-W10, P08-F5-W8, P09-F0-W6, P09-F0-W8, P09-F4-W6, P09-F4-W8, P09-F6-W6, P09-F6-W8, S01-F1-W1, S01-F1-W5, S01-F2-W1, S01-F2-W5, S02-F2-W1, S02-F2-W5, S03-F5-W10, S03-F5-W5, S04-F0-W0, S04-F2-W0, S04-F2-W5, S04-F6-W0, S04-F6-W5, S05-F0-W3, S05-F2-W3, S05-F2-W5, S05-F6-W3, S05-F6-W5, S06-F0-W5, S06-F0-W6, S06-F2-W5, S06-F2-W6, S06-F6-W5, S06-F6-W6, S07-F0-W5, S07-F4-W5, S07-F6-W5, S08-F0-W5, S08-F2-W5, S08-F6-W5, S09-F0-W5, S09-F2-W5, S09-F6-W5, S11-F0-W5, S11-F0-W6, S11-F4-W5, S11-F4-W6, S11-F6-W5, S11-F6-W6, S13-F0-W1, S13-F0-W12, S13-F0-W5, S13-F1-W1, S13-F1-W12, S13-F1-W5, S13-F2-W1, S13-F2-W12, S13-F2-W5, T01-F0-W1, T01-F1-W1, T01-F2-W1, T02-F0-W1, T02-F2-W1, T03-F5-W9, T10-F0-W1, T10-F1-W1, T10-F2-W1`

---

## 二、纯证据视图（bucket 1/2/3 的字面定义，Σ = 325）

用户对 bucket 1–3 的定义是**纯测量态**（与 4/5 的阻塞因正交）。此视图不做阻塞优先级：

| 证据态 | COUNT | 说明 |
|---|---|---|
| 无流（never-run / no prop_evt anywhere on host） | **252** | 同上 bucket 1 之外，还含被 4/5 吸收的 57 个有阻塞因、但同样无流的 RunID |
| 有流、链未闭合（executed, chain incomplete） | **73** | 73 个有流者中 72 个未承认（见 §三） |
| 完整链或显式 containment | **1** | 仅 `T08-F0-W4`（见 §三，gz 截断） |
| **Σ** | **325** | 252 + 72 + 1 |

- 有流 **73** = 至少一条完整流（gz 到 EOF 且 `stats.txt` 非空）**58** + 流全截断 **15**。
- 无流 252 的类别分布：`CHAIN-EVIDENCE-MISSING` 195、`FS-MULTICORE` 31、`LICENSE` 12、`FS-INFRA` 8、`RULING` 4、`UNRESOLVED` 2。

### 5×3 交叉矩阵（类别 × 证据态）

| 契约 category | 无流 | 有完整流 | 仅截断流 | Σ |
|---|---|---|---|---|
| CHAIN-EVIDENCE-MISSING | 195 | 2 | 1 | 198 |
| CHAIN-UNPROVEN | 0 | 36 | 7 | 43 |
| FS-INFRA | 8 | 13 | 3 | 24 |
| FS-MULTICORE | 31 | 3 | 1 | 35 |
| LICENSE | 12 | 0 | 0 | 12 |
| RULING | 4 | 2 | 0 | 6 |
| UNRESOLVED | 2 | 2 | 0 | 4 |
| MODE-UNIMPL | 0 | 0 | 3 | 3 |
| **Σ** | **252** | **58** | **15** | **325** |

> 口径提示：契约 `CHAIN-EVIDENCE-MISSING` 里 **`L01-F0-W5`** 与 **`S10-F5-W9`** 在主机上**确有完整流**（`runs/lsu/r6_lq_L01-F0-W5_s6/L01-F0-W5/seed1..6`、`.../S10-F5-W9/seed1..3`），与契约"该 RunID 无 pilot 证据"的判定**直接冲突**（见 §五）。

---

## 三、admitted / unproven / evidence_missing / truncated

| 指标 | L31 独立复算（全主机流） | 契约 `r6-gate`（root=worktree） | 契约 `r6-final`（root=主机） |
|---|---|---|---|
| **admitted** | **0 / 325** | 0 | 0 |
| **unproven** | 73（有流但未承认；未含阻碍因） | 43 | 45 |
| **evidence_missing** | 252（全主机无流） | 198 | 196 |
| **truncated** | **15 RunID**（全部流 gz 不读至 EOF 和/或兄弟 `stats.txt` 为空） | —（契约按 pilot 计 19） | — |

- `admitted = 0`：L31 对 73 个有流 RunID 各取**最小完整流**跑 `check_admission`（`event_cap=4000`），**无一条承认**。
  terminal 分布：`provable_to_L0_then_unknown` 17、`provable_to_L4_then_unknown` 15、`provable_to_L3_then_unknown` 6、`detected_translation_outcome_pending` 3、`provable_to_L2_then_unknown` 3、`provable_to_L1_then_unknown` 3、`detected_contained` 1（T05-F0-W4，仍 `admitted=False`）、无 verdict 25。
  唯一"显式 containment"是 **T08-F0-W4**（L28 直接调用 `containment_from_events()` 承认；其 gz 截断、无完整流，故不在上式 73 条 verdict 内）。
- **truncated（15 个 RunID）**：
`A01-F0-W3, C01-F0-W1, C14-F5-W10, C14-F5-W6, C15-F0-W10, C15-F0-W6, C15-F6-W10, C15-F6-W6, O03-F0-W7, T06-F0-W4, T07-F0-W4, T08-F0-W4, T08-F0-W9, T08-F4-W9, T08-F6-W9`

  逐条实证例：`runs/lsu/r6_mc_O03-F0-W7/O03-F0-W7/seed1/prop_evt.txt.gz` = 249 B，`EOFError: Compressed file ended before the end-of-stream marker`，兄弟 `stats.txt` 0 B。
- **完整流 RunID（58）**：
`A04-F0-W3, A06-F0-W3, A06-F0-W5, A07-F0-W3, A07-F0-W5, A07-F4-W3, A07-F4-W5, A07-F6-W3, A07-F6-W5, C01-F0-W6, C09-F0-W10, C09-F0-W6, C11-F0-W6, C11-F6-W6, C12-F0-W6, C12-F6-W6, C15-F4-W10, C15-F4-W6, L01-F0-W5, L04-F0-W12, L04-F0-W5, L04-F2-W12, L04-F2-W5, L04-F6-W12, L04-F6-W5, O01-F0-W7, O02-F0-W7, O02-F5-W7, P01-F0-W8, P06-F0-W6, P06-F0-W8, P06-F2-W6, P06-F2-W8, P06-F6-W6, P06-F6-W8, S01-F0-W5, S02-F0-W5, S04-F0-W5, S05-F0-W5, S10-F0-W5, S10-F0-W9, S10-F2-W5, S10-F2-W9, S10-F5-W5, S10-F5-W9, T01-F0-W4, T01-F1-W4, T01-F2-W4, T02-F0-W4, T02-F2-W4, T03-F5-W4, T04-F0-W4, T04-F2-W4, T04-F6-W4, T05-F0-W4, T10-F0-W4, T10-F1-W4, T10-F2-W4`

---

## 四、与契约自身 `blocked_by_category` / `chain_gate` 的交叉核对 —— 发现的不一致（照实报告）

1. **`chain_gate` 的 unproven / evidence_missing 命名与内容相反（标签缺陷）。**
   `r6-gate` 的 `chain_gate = {admitted:0, unproven:43, evidence_missing:198}`，`blocked_by_category = {CHAIN-UNPROVEN:43, CHAIN-EVIDENCE-MISSING:198}` —— 二者自洽，但语义**与字面相反**：
   - 43 条 = `pilot_evidence.json` 里**有**样本(`n_samples>0`)但文件路径在该 root 下**解析不到** → 逐条违反 `chain_evidence_missing`（字面"证据缺失"），却被标为 `CHAIN-UNPROVEN`。
   - 198 条 = `n_samples=0`，`note="无 … pilot 证据…链不可证"`（字面"无证据"），却被标为 `CHAIN-EVIDENCE-MISSING`。
   即：`unproven` 那一格其实是"有路径但文件缺"，`evidence_missing` 那一格其实是"无证据"。同一份契约里 category 名与 chain_gate 键名一致、但两者都**与事件内容反向**。

2. **两个 `chain_gate` 变体只因 `evidence_root` 不同而数字不同，证据本身零变化。**
   `r6-final`（root=`/home/sdc/gem5-fi-ding`）→ `unproven=45, evidence_missing=196`；`r6-gate`（root=`.claude/worktrees/r6-gate`）→ `unproven=43, evidence_missing=198`。后者 root 下**根本没有 `runs/lsu/`**（`ls` 报 No such file），故 2 条本来能解析的路径变成违反。**这是 root 选择的人工产物，不是证据变化。**

3. **契约登记的证据与主机实际流不符（双向）。**
   - 契约 `chain_gate.unproven`（43/45）≤ L31 实测有流 RunID（73）。契约把 241 条 `CHAIN-*` 判为"链不可证/证据缺"，其中 195 条主机上**确无流**（一致），但另有 **46 条本来有流**（36 完整 + 8 截断 + `L01-F0-W5`/`S10-F5-W9`），契约对它们的"无证据"判定不成立于主机。
   - 更直接：`CHAIN-EVIDENCE-MISSING` 之 `L01-F0-W5`、`S10-F5-W9` 主机上有**完整流**（seed1..6 / seed1..3），契约却记 `n_samples=0`。

4. **旧的 pre-gate 契约与最新 gate 契约对同一 325 个 RunID 判定完全相反。**
   `docs/gem5-fi/lsu/mdspec/ready_contract.json`（12:33，无 `chain_gate` 键）:`status = {READY:241, BLOCKED:84}`；最新 gate 契约:`status = {BLOCKED:325}`（READY=0, PARTIAL=0）。同一份 325 名单，一边说 241 READY、一边说 325 BLOCKED。`blockers_for_approval.md`（引用 241/84 版）与最新 gate 契约**不可同时为真**。

5. **`chain_gate` 只在 READY/PARTIAL 行上求值，而 READY=0** → 24 条 T-series（FS-INFRA）`chain=null`，containment 路径结构性到不了（L28 已记），故"T08 containment 成立"永远进不了契约的 `admitted`。

---

## 五、复算命令（可重放）

```
find / -name 'prop_evt*.gz' -not -path '*/proc/*' 2>/dev/null | sort > /tmp/prop_evt_host.txt   # 448 条
python3 <r6-gate>/tools/lsu_chain_check.py <stream> --run-id <RunID>                              # 单流严格判定
python3 tools/lsu_l31_bucket_audit.py /tmp/l31_audit.jsonl                                        # 全 325 逐 RunID
```

**No file under version control was modified by this lane.**
