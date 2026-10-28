# A08-F2-W3 seed2 — BLOCKED（结构性不可达；未注入、未生成样本）

## 1. 实验身份

| 项 | 值 |
|---|---|
| RunID | `A08-F2-W3` |
| 模型 | A08（同周期 load/store 配对） |
| 子模型 | A08-b（even seed：store 先/load 后，同 4KiB 页；EA 互换） |
| 频率档 | F2（mean 100,000 eligible 事件，±50% jitter） |
| 负载 | W3=agu_addrmodes |
| seed | 2 |
| 结局 | `Blocked`（resolver 响亮拒绝，未启动 gem5） |

## 2. 为什么 BLOCKED（真实 census 证据）

A08-b 的“合格流”只统计**同 tick、store 先/load 后、同 4KiB 页**的配对事件
（`CHAOSAddrPath::maybePairA08` 的 a08_pair_swap 分支）。实测：

- W3：E1=E5=E10=21（repeat 完全不增加配对 eligible，delta=0）
- W5：E1=E5=E10=21（同上）

证据：`/home/sdc/gem5-fi-ding/runs/lsu/r6_a4_census_r6a4/summary.json`
（键 `A08-b-W3`/`A08-b-W5`，`blocked='delta<=0'`；同源未注入测量，
census-only 工具 `tools/lsu_repeat_census.py`）。

F2 的确定性首火位在 eligible 序数空间（seed 由 `chaosSampleLCG` 决定）：
seed1=106,412 / seed2=**99,417** / seed3=140,806。A08-b 的整条流只有 21 个
eligible，**永远到不了** 99,417；repeat 只重复同一 workload，不改变
“同 tick + store 先/load 后 + 同页”的发生条件（首个冷启动迭代 21 次，
热迭代 0 次）。

## 3. 没有做什么（诚实边界）

- 没有启动 gem5、没有注入、没有生成 prop_evt/chain_report；
- 没有用 A08-a 冒充 even seed（不换注入模型）；
- 没有改 F2 的平均间隔/随机算法/seed；
- 没有改 workload 身份或输入；
- 没有用 oracle 正常推断“合格”。

## 4. 原始证据位置

| 证据 | 路径 |
|---|---|
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s2/manifest.json` |
| cell_results | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s2/A08-F2-W3/cell_results.json` |
| census summary | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a4_census_r6a4/summary.json` |
| resolver 拒绝日志 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W3_s2.log` |

## 5. 需要裁决才能改变结局

见 `runs/lsu/r6_reports/R6-A4-FINAL-REPORT.md` §8（F2-not-applicable / 事件触发档 /
更换 workload / 换子模型），本轮严格按原规格执行，未选择任何一项。
