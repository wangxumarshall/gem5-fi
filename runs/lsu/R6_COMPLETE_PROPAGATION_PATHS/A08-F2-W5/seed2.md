# A08-F2-W5 seed2 — N/A (SPEC_EXCLUDED)

## 1. 最终口径（权威）

| 字段 | 值 |
|---|---|
| status | `N/A` |
| classification | `SPEC_EXCLUDED` |
| reason | `A08-b structurally unreachable under F2` |
| RunID | `A08-F2-W5` |
| seed | 2（even seed 选择 A08-b pair_swap 子模型） |
| 负载 | W5=sq_forward |
| admitted | 空（**不是** True） |
| certified | 空（**不是** True） |
| terminal | 空（**不是** full / detected_contained） |
| 传播链 | 不存在（未注入，未生成 prop_evt/chain_report） |

本样本**不是 PASS，也不是 FAIL**；它不计入 88 个可执行样本（applicable）
的分母，不再要求补跑。

## 2. 结构性原因（真实 census 证据）

A08-b 的合格流只统计**同 tick、store 先/load 后、同 4 KiB 页**的配对事件
（`CHAOSAddrPath::maybePairA08` 的 a08_pair_swap 分支）。实测（未注入流，
repeat=1/5/10）：

- W3：E1=E5=E10=**21**，repeat 增量 delta=**0**
- W5：E1=E5=E10=**21**，repeat 增量 delta=**0**
- F2 在 seed2 的确定性首火位置 = eligible 序数 **99,417**
  （seed1=106,412 / seed2=99,417 / seed3=140,806，由 `chaosSampleLCG`
  与 `chaos_lsu_trigger.hh` 的 `warmup + 50000 + rng%100000` 独立重算）

重复同一 workload 不会增加合格的同 tick store-first/load-after 配对事件
（首个冷启动迭代产生 21 次，热迭代为 0），因此 **21 ≪ 99,417**，F2 的
首火位永远不可达，**不存在合法的实际注入机会**。

## 3. 没有做什么（诚实边界）

- 没有启动 gem5、没有注入、没有生成任何传播链；
- 没有换 seed、没有换 workload、没有改成 A08-a、
  没有修改 F2 的频率定义/随机算法；
- 没有写成 PASS/admitted/certified；
- 原始 BLOCKED 证据完整保留（见 §4），未被删除或改写。

## 4. 原始 BLOCKED / census 证据（保留）

| 证据 | 路径 |
|---|---|
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W5_s2/manifest.json` |
| cell_results（outcome=Blocked） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W5_s2/A08-F2-W5/cell_results.json` |
| resolver 拒绝日志 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A08-F2-W5_s2.log` |
| census summary（A08-b 键 blocked=delta<=0） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a4_census_r6a4/summary.json` |
| 同源 census（新二进制） | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a4_census_newbin/summary.json` |

## 5. 裁决依据

用户裁决（2026-10-29）：接受 A08-b 两个结构性不可达样本按规格不适用项
收口；A 单元最终口径为 88/88 applicable qualified、2 个 SPEC_EXCLUDED、
0 个 applicable failure、`unit_status=COMPLETE_WITH_SPEC_EXCLUSIONS`。
