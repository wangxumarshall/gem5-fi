# A02-F2-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A02-F2-W3` |
| 模型 | A02（AGU EA 双bit翻转） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s1 --cells A02-F2-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=149330720，request_id=，corr=origin，注入前地址 `before=4932b0`，注入后地址 `after=4932b6`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 149330720, Site: lsq_sendFragmentToTranslation, mode=a02_2bit, old_vaddr=0x4932b0, new_vaddr=0x4932b6, faults_injected: 1, geom_candidates=1, geom_rejects=0, geom_bitmask=0x6 (NOTE: SE-inert — byte7 zero lands in SE 512MiB range)
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4932b0` → `4932b6`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 149330720 |  | 4932b0 |  |  |  | origin |
| addr_form | 2 | 1 | 149330720 |  | 4932b6 |  |  |  | origin |
| mem_req | 3 | 2 | 149330720 | 625711 | 4932b6 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 149330720 | 625711 | 4932b6 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 149330720 | 625711 | 4932b6 |  |  |  | seq_primary |
| lq_read | 6 | 5 | 149330720 | 625711 | 4932b6 |  |  |  | seq_primary |
| resp | 7 | 6 | 149331490 | 625711 | 792b6 |  |  |  | seq_primary |
| lq_complete | 8 | 7 | 149331490 | 625711 | 4932b6 | 792b6 |  |  | seq_primary |
| taint_reg | 9 | 8 | 149331490 | 625711 | 792b6 |  |  |  | seq_primary |
| errant_commit | 10 | 9 | 149339190 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 11 | 9 | 149339575 |  |  |  |  |  | taint_prop |
| consumer | 12 | 11 | 149340730 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 149341115 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 149342270 |  |  |  |  |  | taint_prop |
| consumer | 15 | 14 | 149342655 |  |  |  |  |  | taint_prop |
| consumer | 16 | 15 | 149343810 |  |  |  |  |  | taint_prop |
| consumer | 17 | 16 | 149344195 |  |  |  |  |  | taint_prop |
| consumer | 18 | 17 | 149345350 |  |  |  |  |  | taint_prop |
| consumer | 19 | 18 | 149345735 |  |  |  |  |  | taint_prop |
| consumer | 20 | 19 | 149346890 |  |  |  |  |  | taint_prop |
| consumer | 21 | 20 | 149347275 |  |  |  |  |  | taint_prop |
| consumer | 22 | 21 | 149348430 |  |  |  |  |  | taint_prop |
| consumer | 23 | 22 | 149348815 |  |  |  |  |  | taint_prop |
| consumer | 24 | 23 | 149349970 |  |  |  |  |  | taint_prop |
| consumer | 25 | 24 | 149350355 |  |  |  |  |  | taint_prop |
| consumer | 26 | 25 | 149351510 |  |  |  |  |  | taint_prop |
| consumer | 27 | 26 | 149351895 |  |  |  |  |  | taint_prop |
| consumer | 28 | 27 | 149353050 |  |  |  |  |  | taint_prop |
| consumer | 29 | 28 | 149353435 |  |  |  |  |  | taint_prop |
| consumer | 30 | 29 | 149354590 |  |  |  |  |  | taint_prop |
| consumer | 31 | 30 | 149354975 |  |  |  |  |  | taint_prop |
| consumer | 32 | 31 | 149356130 |  |  |  |  |  | taint_prop |
| consumer | 33 | 32 | 149356515 |  |  |  |  |  | taint_prop |
| consumer | 34 | 33 | 149357670 |  |  |  |  |  | taint_prop |
| consumer | 35 | 34 | 149358055 |  |  |  |  |  | taint_prop |
| consumer | 36 | 35 | 149359210 |  |  |  |  |  | taint_prop |
| consumer | 37 | 36 | 149359595 |  |  |  |  |  | taint_prop |
| consumer | 38 | 37 | 149360750 |  |  |  |  |  | taint_prop |
| consumer | 39 | 38 | 149361135 |  |  |  |  |  | taint_prop |
| consumer | 40 | 39 | 149362290 |  |  |  |  |  | taint_prop |
| consumer | 41 | 40 | 149362675 |  |  |  |  |  | taint_prop |
| consumer | 42 | 41 | 149363830 |  |  |  |  |  | taint_prop |
| consumer | 43 | 42 | 149364215 |  |  |  |  |  | taint_prop |
| consumer | 44 | 43 | 149365370 |  |  |  |  |  | taint_prop |
| consumer | 45 | 44 | 149365755 |  |  |  |  |  | taint_prop |
| consumer | 46 | 45 | 149366910 |  |  |  |  |  | taint_prop |
| consumer | 47 | 46 | 149367295 |  |  |  |  |  | taint_prop |
| consumer | 48 | 47 | 149368450 |  |  |  |  |  | taint_prop |
| consumer | 49 | 48 | 149368835 |  |  |  |  |  | taint_prop |
| consumer | 50 | 49 | 149369990 |  |  |  |  |  | taint_prop |
| consumer | 51 | 50 | 149370375 |  |  |  |  |  | taint_prop |
| consumer | 52 | 51 | 149371530 |  |  |  |  |  | taint_prop |
| consumer | 53 | 52 | 149371915 |  |  |  |  |  | taint_prop |
| consumer | 54 | 53 | 149373070 |  |  |  |  |  | taint_prop |
| consumer | 55 | 54 | 149373455 |  |  |  |  |  | taint_prop |
| consumer | 56 | 12 | 149374995 |  |  |  |  |  | taint_prop |
| consumer | 57 | 14 | 149376535 |  |  |  |  |  | taint_prop |
| consumer | 58 | 16 | 149378075 |  |  |  |  |  | taint_prop |
| consumer | 59 | 18 | 149379615 |  |  |  |  |  | taint_prop |
| consumer | 60 | 20 | 149381155 |  |  |  |  |  | taint_prop |
| consumer | 61 | 22 | 149382695 |  |  |  |  |  | taint_prop |
| consumer | 62 | 24 | 149384235 |  |  |  |  |  | taint_prop |
| consumer | 63 | 26 | 149385775 |  |  |  |  |  | taint_prop |
| consumer | 64 | 28 | 149387315 |  |  |  |  |  | taint_prop |
| consumer | 65 | 30 | 149388855 |  |  |  |  |  | taint_prop |
| consumer | 66 | 32 | 149390395 |  |  |  |  |  | taint_prop |
| consumer | 67 | 34 | 149391935 |  |  |  |  |  | taint_prop |
| consumer | 68 | 36 | 149393475 |  |  |  |  |  | taint_prop |
| consumer | 69 | 38 | 149395015 |  |  |  |  |  | taint_prop |
| consumer | 70 | 40 | 149396555 |  |  |  |  |  | taint_prop |
| consumer | 71 | 42 | 149398095 |  |  |  |  |  | taint_prop |
| consumer | 72 | 44 | 149399635 |  |  |  |  |  | taint_prop |
| consumer | 73 | 46 | 149401175 |  |  |  |  |  | taint_prop |
| consumer | 74 | 48 | 149402715 |  |  |  |  |  | taint_prop |
| consumer | 75 | 50 | 149429280 |  |  |  |  |  | taint_prop |
| consumer | 76 | 51 | 149430435 |  |  |  |  |  | taint_prop |
| consumer | 77 | 51 | 149430435 |  |  |  |  |  | taint_prop |
| consumer | 78 | 51 | 149430435 |  |  |  |  |  | taint_prop |
| consumer | 79 | 39 | 149431205 |  |  |  |  |  | taint_prop |
| consumer | 80 | 42 | 149431975 |  |  |  |  |  | taint_prop |
| consumer | 81 | 80 | 149432745 |  |  |  |  |  | taint_prop |
| consumer | 82 | 80 | 149432745 |  |  |  |  |  | taint_prop |
| consumer | 83 | 80 | 149432745 |  |  |  |  |  | taint_prop |
| consumer | 84 | 80 | 149432745 |  |  |  |  |  | taint_prop |
| consumer | 85 | 73 | 149435055 |  |  |  |  |  | taint_prop |
| consumer | 86 | 73 | 149435055 |  |  |  |  |  | taint_prop |
| consumer | 87 | 73 | 149435055 |  |  |  |  |  | taint_prop |
| consumer | 88 | 47 | 149435055 |  |  |  |  |  | taint_prop |
| consumer | 89 | 45 | 149436210 |  |  |  |  |  | taint_prop |
| consumer | 90 | 54 | 149436980 |  |  |  |  |  | taint_prop |
| consumer | 91 | 54 | 149437365 |  |  |  |  |  | taint_prop |
| consumer | 92 | 54 | 149437365 |  |  |  |  |  | taint_prop |
| consumer | 93 | 54 | 149437365 |  |  |  |  |  | taint_prop |
| consumer | 94 | 54 | 149437365 |  |  |  |  |  | taint_prop |
| consumer | 95 | 89 | 149438520 |  |  |  |  |  | taint_prop |
| consumer | 96 | 56 | 149439675 |  |  |  |  |  | taint_prop |
| consumer | 97 | 56 | 149439675 |  |  |  |  |  | taint_prop |
| consumer | 98 | 56 | 149439675 |  |  |  |  |  | taint_prop |
| consumer | 99 | 15 | 149440445 |  |  |  |  |  | taint_prop |
| consumer | 100 | 95 | 149440830 |  |  |  |  |  | taint_prop |
| consumer | 101 | 100 | 149441215 |  |  |  |  |  | taint_prop |
| consumer | 102 | 101 | 149441600 |  |  |  |  |  | taint_prop |
| consumer | 103 | 101 | 149441985 |  |  |  |  |  | taint_prop |
| consumer | 104 | 101 | 149441985 |  |  |  |  |  | taint_prop |
| consumer | 105 | 101 | 149441985 |  |  |  |  |  | taint_prop |
| consumer | 106 | 101 | 149441985 |  |  |  |  |  | taint_prop |
| consumer | 107 | 13 | 149443525 |  |  |  |  |  | taint_prop |
| consumer | 108 | 107 | 149443910 |  |  |  |  |  | taint_prop |
| consumer | 109 | 107 | 149444295 |  |  |  |  |  | taint_prop |
| consumer | 110 | 107 | 149444295 |  |  |  |  |  | taint_prop |
| consumer | 111 | 107 | 149444295 |  |  |  |  |  | taint_prop |
| consumer | 112 | 13 | 149445450 |  |  |  |  |  | taint_prop |
| consumer | 113 | 112 | 149445835 |  |  |  |  |  | taint_prop |
| consumer | 114 | 113 | 149446220 |  |  |  |  |  | taint_prop |
| consumer | 115 | 113 | 149446605 |  |  |  |  |  | taint_prop |
| consumer | 116 | 113 | 149446605 |  |  |  |  |  | taint_prop |
| consumer | 117 | 113 | 149446605 |  |  |  |  |  | taint_prop |
| consumer | 118 | 113 | 149446605 |  |  |  |  |  | taint_prop |
| consumer | 119 | 23 | 149448145 |  |  |  |  |  | taint_prop |
| consumer | 120 | 119 | 149448915 |  |  |  |  |  | taint_prop |
| consumer | 121 | 119 | 149448915 |  |  |  |  |  | taint_prop |
| consumer | 122 | 119 | 149448915 |  |  |  |  |  | taint_prop |
| consumer | 123 | 31 | 149448915 |  |  |  |  |  | taint_prop |
| consumer | 124 | 66 | 149449685 |  |  |  |  |  | taint_prop |
| consumer | 125 | 33 | 149451225 |  |  |  |  |  | taint_prop |
| consumer | 126 | 33 | 149451225 |  |  |  |  |  | taint_prop |
| consumer | 127 | 33 | 149451225 |  |  |  |  |  | taint_prop |
| consumer | 128 | 17 | 149451995 |  |  |  |  |  | taint_prop |
| consumer | 129 | 51 | 149453150 |  |  |  |  |  | taint_prop |
| consumer | 130 | 51 | 149453535 |  |  |  |  |  | taint_prop |
| consumer | 131 | 51 | 149453535 |  |  |  |  |  | taint_prop |
| consumer | 132 | 51 | 149453535 |  |  |  |  |  | taint_prop |
| consumer | 133 | 51 | 149453535 |  |  |  |  |  | taint_prop |
| consumer | 134 | 80 | 149455845 |  |  |  |  |  | taint_prop |
| consumer | 135 | 80 | 149455845 |  |  |  |  |  | taint_prop |
| consumer | 136 | 80 | 149455845 |  |  |  |  |  | taint_prop |
| consumer | 137 | 73 | 149458155 |  |  |  |  |  | taint_prop |
| consumer | 138 | 73 | 149458155 |  |  |  |  |  | taint_prop |
| consumer | 139 | 73 | 149458155 |  |  |  |  |  | taint_prop |
| consumer | 140 | 73 | 149458155 |  |  |  |  |  | taint_prop |
| consumer | 141 | 54 | 149460465 |  |  |  |  |  | taint_prop |
| consumer | 142 | 54 | 149460465 |  |  |  |  |  | taint_prop |
| consumer | 143 | 54 | 149460465 |  |  |  |  |  | taint_prop |
| consumer | 144 | 54 | 149460465 |  |  |  |  |  | taint_prop |
| consumer | 145 | 56 | 149462775 |  |  |  |  |  | taint_prop |
| consumer | 146 | 56 | 149462775 |  |  |  |  |  | taint_prop |
| consumer | 147 | 56 | 149462775 |  |  |  |  |  | taint_prop |
| consumer | 148 | 56 | 149462775 |  |  |  |  |  | taint_prop |
| consumer | 149 | 101 | 149465085 |  |  |  |  |  | taint_prop |
| consumer | 150 | 101 | 149465085 |  |  |  |  |  | taint_prop |
| consumer | 151 | 101 | 149465085 |  |  |  |  |  | taint_prop |
| chain_end | 152 | 151 | 214469640 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4932b6 pa=
- L2 `lsq_sendfrag`：va=4932b6 pa=
- L2 `tlb_translate`：va=4932b6 pa=
- L3 `resp`：va=792b6 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=152。
- 事件数：本 seed 流共 152 条，其中 fault_id=1 链 152 条；最后一条为 `chain_end`（event_id=152, tick=214469640）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s1/A02-F2-W3/seed1/prop_evt.txt.gz` | `ed4d716e4151762ec7dfe84e7d06a0bcbcb7c98c90d4a52a2772ef345324c9b4` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s1/A02-F2-W3/seed1/stats.txt` | `da2f222db3e0d102a5f057acb493a41509f6422697411da9362837fa21097548` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s1/A02-F2-W3/seed1/run.out` | `6efd580d325c4783ae7dcc1bb2db2da51b4a94509f1283d1653f8b34d3e94abc` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s1/A02-F2-W3/seed1/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s1/A02-F2-W3/chain_report.json` | `403fabaf3b3373b721f5fe6e5dee95a81a294f212ecb6f6613edfd7af3e713dc` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A02-F2-W3_s1/manifest.json` | `479784a99c2911b76ce9cb2a2d2b3bb39c8e7dc1c9758d4fbfda7a9f58e3799d` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

