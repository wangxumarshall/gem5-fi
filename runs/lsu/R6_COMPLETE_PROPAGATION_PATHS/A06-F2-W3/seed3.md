# A06-F2-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A06-F2-W3` |
| 模型 | A06（AGU 访问尺寸/掩码） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 444451700, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x4931d8, new_addr=0x4931d8, old_size=8, new_size=4, faults_injected: 1, isLoad=0, isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A06-F2-W3_s3 --cells A06-F2-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 1200` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=444451700，request_id=，corr=origin，注入前地址 `before=4931d8`，注入后地址 `after=4931d8`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 444451700, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x4931d8, new_addr=0x4931d8, old_size=8, new_size=4, faults_injected: 1, isLoad=0, isStore=1, fault_field=size, be_len=8, be_ones=8, be_subst=0, submodel=a06a, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4931d8` → `4931d8`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `4`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a06a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 444451700 |  | 4931d8 |  |  |  | origin |
| addr_form | 2 | 1 | 444451700 |  | 4931d8 |  |  |  | origin |
| lsq_push | 3 | 2 | 444451700 |  | 4931d8 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 444451700 | 1993976 | 4931d8 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 444451700 | 1993976 | 4931d8 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 444451700 | 1993976 | 4931d8 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 444451700 |  | 4931d8 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 444453240 |  |  | 791d8 |  |  | seq_primary |
| resp | 9 | 8 | 444454010 | 1993976 | 791d8 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 444454010 | 1993976 | 791d8 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 444454010 |  | 4931d8 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 521393565 | 1993976 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 521393565 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4931d8 pa=
- L2 `lsq_sendfrag`：va=4931d8 pa=
- L2 `tlb_translate`：va=4931d8 pa=
- L3 `resp`：va=791d8 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=521393565）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局见证事件（本 seed 自己的流）：kind=`store_not_retired`，event_id=12，parent_event_id=11，tick=521393565，detection_layer=L4，outcome=contained，contained=1，corr=taint_prop。
该事件带真实 detection_layer/outcome/contained/corr，且其 parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 `detected_contained`——它不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A06-F2-W3_s3/A06-F2-W3/seed3/prop_evt.txt.gz` | `77ac4026b62221929f49b59b26fa53d0131e61965bf7e0b04fe8fcbead64c550` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A06-F2-W3_s3/A06-F2-W3/seed3/stats.txt` | `c090965e8bae9899053cf3ccccf8d5ff605545f584d581ab2403e541c15c4a06` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A06-F2-W3_s3/A06-F2-W3/seed3/run.out` | `619564e645fbe8a05a16f7cc6137d197f5e9a0c75c8d64bfca8e687bd1d4edfd` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A06-F2-W3_s3/A06-F2-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A06-F2-W3_s3/A06-F2-W3/chain_report.json` | `20726f160c98a92cd656a7380bbc091e3d69971fb882fa7f8488ced121680cd9` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A06-F2-W3_s3/manifest.json` | `df459c118fc7b9fffd9fc8b581e13ee90fb6e3440008d580f8bb06b1a3d95c68` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

