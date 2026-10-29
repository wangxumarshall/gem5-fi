# A07-F4-W3 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A07-F4-W3` |
| 模型 | A07（AGU ready 时序） |
| 频率档 | F4 |
| 负载 | W3 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | 见注入日志 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s3 --cells A07-F4-W3 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=0`，tick=192583160，request_id=，corr=origin，注入前地址 `before=192583160`，注入后地址 `after=192583545`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 192583160, Site: iew_memRef_AGU_ready, mode=a07b_ready_delay, dyn_inst_seq=826184, ready_tick=192583160, delayed_tick=192583545, delay_cycles=1, isLoad=1, isStore=0, faults_injected: 1
Tick: 192583545, Site: iew_memRef_AGU_ready_resume, mode=a07b_ready_delay, dyn_inst_seq=826184, consumed=1, squashed=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`192583160` → `192583545`（来自 inj/addr_form 节点，本 seed 自己的值）。

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 0 |  | 192583160 |  |  |  |  |  | origin |
| lsq_push | 2 | 0 | 192583545 |  | 493390 |  |  |  | seq_primary |
| mem_req | 3 | 2 | 192583545 | 826184 | 493390 |  |  |  | seq_primary |
| lsq_sendfrag | 4 | 3 | 192583545 | 826184 | 493390 |  |  |  | seq_primary |
| tlb_translate | 5 | 4 | 192583545 | 826184 | 493390 |  |  |  | seq_primary |
| lq_read | 6 | 5 | 192583545 | 826184 | 493390 |  |  |  | seq_primary |
| resp | 7 | 6 | 192584315 | 826184 | 79390 |  |  |  | seq_primary |
| lq_complete | 8 | 7 | 192584315 | 826184 | 493390 | 79390 |  |  | seq_primary |
| taint_reg | 9 | 8 | 192584315 | 826184 | 79390 |  |  |  | seq_primary |
| errant_commit | 10 | 9 | 192590475 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 11 | 9 | 192590860 |  |  |  |  |  | taint_prop |
| consumer | 12 | 11 | 192592015 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 192592400 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 192593555 |  |  |  |  |  | taint_prop |
| consumer | 15 | 14 | 192593940 |  |  |  |  |  | taint_prop |
| consumer | 16 | 15 | 192595095 |  |  |  |  |  | taint_prop |
| consumer | 17 | 16 | 192595480 |  |  |  |  |  | taint_prop |
| consumer | 18 | 17 | 192596635 |  |  |  |  |  | taint_prop |
| consumer | 19 | 18 | 192597020 |  |  |  |  |  | taint_prop |
| consumer | 20 | 19 | 192598175 |  |  |  |  |  | taint_prop |
| consumer | 21 | 20 | 192598560 |  |  |  |  |  | taint_prop |
| consumer | 22 | 21 | 192599715 |  |  |  |  |  | taint_prop |
| consumer | 23 | 22 | 192600100 |  |  |  |  |  | taint_prop |
| consumer | 24 | 23 | 192601255 |  |  |  |  |  | taint_prop |
| consumer | 25 | 24 | 192601640 |  |  |  |  |  | taint_prop |
| consumer | 26 | 25 | 192602795 |  |  |  |  |  | taint_prop |
| consumer | 27 | 26 | 192603180 |  |  |  |  |  | taint_prop |
| consumer | 28 | 27 | 192604335 |  |  |  |  |  | taint_prop |
| consumer | 29 | 28 | 192604720 |  |  |  |  |  | taint_prop |
| consumer | 30 | 29 | 192605875 |  |  |  |  |  | taint_prop |
| consumer | 31 | 30 | 192606260 |  |  |  |  |  | taint_prop |
| consumer | 32 | 31 | 192607415 |  |  |  |  |  | taint_prop |
| consumer | 33 | 32 | 192607800 |  |  |  |  |  | taint_prop |
| consumer | 34 | 33 | 192608955 |  |  |  |  |  | taint_prop |
| consumer | 35 | 34 | 192609340 |  |  |  |  |  | taint_prop |
| consumer | 36 | 35 | 192610495 |  |  |  |  |  | taint_prop |
| consumer | 37 | 36 | 192610880 |  |  |  |  |  | taint_prop |
| consumer | 38 | 37 | 192612035 |  |  |  |  |  | taint_prop |
| consumer | 39 | 38 | 192637445 |  |  |  |  |  | taint_prop |
| consumer | 40 | 39 | 192637445 |  |  |  |  |  | taint_prop |
| consumer | 41 | 40 | 192637830 |  |  |  |  |  | taint_prop |
| consumer | 42 | 41 | 192638600 |  |  |  |  |  | taint_prop |
| consumer | 43 | 41 | 192638600 |  |  |  |  |  | taint_prop |
| consumer | 44 | 41 | 192638600 |  |  |  |  |  | taint_prop |
| consumer | 45 | 41 | 192638600 |  |  |  |  |  | taint_prop |
| consumer | 46 | 45 | 192639370 |  |  |  |  |  | taint_prop |
| consumer | 47 | 30 | 192640140 |  |  |  |  |  | taint_prop |
| consumer | 48 | 47 | 192640910 |  |  |  |  |  | taint_prop |
| consumer | 49 | 47 | 192640910 |  |  |  |  |  | taint_prop |
| consumer | 50 | 47 | 192640910 |  |  |  |  |  | taint_prop |
| consumer | 51 | 32 | 192640910 |  |  |  |  |  | taint_prop |
| consumer | 52 | 47 | 192640910 |  |  |  |  |  | taint_prop |
| consumer | 53 | 30 | 192642065 |  |  |  |  |  | taint_prop |
| consumer | 54 | 35 | 192642835 |  |  |  |  |  | taint_prop |
| consumer | 55 | 35 | 192643220 |  |  |  |  |  | taint_prop |
| consumer | 56 | 54 | 192643220 |  |  |  |  |  | taint_prop |
| consumer | 57 | 53 | 192644375 |  |  |  |  |  | taint_prop |
| consumer | 58 | 57 | 192644760 |  |  |  |  |  | taint_prop |
| consumer | 59 | 58 | 192645145 |  |  |  |  |  | taint_prop |
| consumer | 60 | 58 | 192645530 |  |  |  |  |  | taint_prop |
| consumer | 61 | 58 | 192645530 |  |  |  |  |  | taint_prop |
| consumer | 62 | 58 | 192645530 |  |  |  |  |  | taint_prop |
| consumer | 63 | 59 | 192645530 |  |  |  |  |  | taint_prop |
| consumer | 64 | 58 | 192645530 |  |  |  |  |  | taint_prop |
| consumer | 65 | 64 | 192646300 |  |  |  |  |  | taint_prop |
| consumer | 66 | 57 | 192646685 |  |  |  |  |  | taint_prop |
| consumer | 67 | 66 | 192647070 |  |  |  |  |  | taint_prop |
| consumer | 68 | 67 | 192647455 |  |  |  |  |  | taint_prop |
| consumer | 69 | 67 | 192647840 |  |  |  |  |  | taint_prop |
| consumer | 70 | 67 | 192647840 |  |  |  |  |  | taint_prop |
| consumer | 71 | 67 | 192647840 |  |  |  |  |  | taint_prop |
| consumer | 72 | 68 | 192647840 |  |  |  |  |  | taint_prop |
| consumer | 73 | 67 | 192647840 |  |  |  |  |  | taint_prop |
| consumer | 74 | 73 | 192648610 |  |  |  |  |  | taint_prop |
| consumer | 75 | 66 | 192648995 |  |  |  |  |  | taint_prop |
| consumer | 76 | 75 | 192649380 |  |  |  |  |  | taint_prop |
| consumer | 77 | 76 | 192649765 |  |  |  |  |  | taint_prop |
| consumer | 78 | 76 | 192650150 |  |  |  |  |  | taint_prop |
| consumer | 79 | 76 | 192650150 |  |  |  |  |  | taint_prop |
| consumer | 80 | 76 | 192650150 |  |  |  |  |  | taint_prop |
| consumer | 81 | 77 | 192650150 |  |  |  |  |  | taint_prop |
| consumer | 82 | 76 | 192650150 |  |  |  |  |  | taint_prop |
| consumer | 83 | 82 | 192650920 |  |  |  |  |  | taint_prop |
| consumer | 84 | 75 | 192651305 |  |  |  |  |  | taint_prop |
| consumer | 85 | 11 | 192652075 |  |  |  |  |  | taint_prop |
| consumer | 86 | 11 | 192652460 |  |  |  |  |  | taint_prop |
| consumer | 87 | 11 | 192652460 |  |  |  |  |  | taint_prop |
| consumer | 88 | 11 | 192652460 |  |  |  |  |  | taint_prop |
| consumer | 89 | 84 | 192653615 |  |  |  |  |  | taint_prop |
| consumer | 90 | 89 | 192654000 |  |  |  |  |  | taint_prop |
| consumer | 91 | 90 | 192654385 |  |  |  |  |  | taint_prop |
| consumer | 92 | 90 | 192654770 |  |  |  |  |  | taint_prop |
| consumer | 93 | 90 | 192654770 |  |  |  |  |  | taint_prop |
| consumer | 94 | 90 | 192654770 |  |  |  |  |  | taint_prop |
| consumer | 95 | 90 | 192654770 |  |  |  |  |  | taint_prop |
| consumer | 96 | 95 | 192655540 |  |  |  |  |  | taint_prop |
| consumer | 97 | 89 | 192655925 |  |  |  |  |  | taint_prop |
| consumer | 98 | 97 | 192656310 |  |  |  |  |  | taint_prop |
| consumer | 99 | 98 | 192656695 |  |  |  |  |  | taint_prop |
| consumer | 100 | 98 | 192657080 |  |  |  |  |  | taint_prop |
| consumer | 101 | 98 | 192657080 |  |  |  |  |  | taint_prop |
| consumer | 102 | 98 | 192657080 |  |  |  |  |  | taint_prop |
| consumer | 103 | 99 | 192657080 |  |  |  |  |  | taint_prop |
| consumer | 104 | 21 | 192657850 |  |  |  |  |  | taint_prop |
| consumer | 105 | 16 | 192658620 |  |  |  |  |  | taint_prop |
| consumer | 106 | 105 | 192659390 |  |  |  |  |  | taint_prop |
| consumer | 107 | 105 | 192659390 |  |  |  |  |  | taint_prop |
| consumer | 108 | 105 | 192659390 |  |  |  |  |  | taint_prop |
| consumer | 109 | 105 | 192659390 |  |  |  |  |  | taint_prop |
| consumer | 110 | 109 | 192660160 |  |  |  |  |  | taint_prop |
| consumer | 111 | 41 | 192661315 |  |  |  |  |  | taint_prop |
| consumer | 112 | 41 | 192661700 |  |  |  |  |  | taint_prop |
| consumer | 113 | 41 | 192661700 |  |  |  |  |  | taint_prop |
| consumer | 114 | 41 | 192661700 |  |  |  |  |  | taint_prop |
| consumer | 115 | 41 | 192661700 |  |  |  |  |  | taint_prop |
| consumer | 116 | 47 | 192664010 |  |  |  |  |  | taint_prop |
| consumer | 117 | 35 | 192666320 |  |  |  |  |  | taint_prop |
| consumer | 118 | 35 | 192666320 |  |  |  |  |  | taint_prop |
| consumer | 119 | 35 | 192666320 |  |  |  |  |  | taint_prop |
| consumer | 120 | 35 | 192666320 |  |  |  |  |  | taint_prop |
| consumer | 121 | 58 | 192668245 |  |  |  |  |  | taint_prop |
| consumer | 122 | 58 | 192668630 |  |  |  |  |  | taint_prop |
| consumer | 123 | 58 | 192668630 |  |  |  |  |  | taint_prop |
| consumer | 124 | 58 | 192668630 |  |  |  |  |  | taint_prop |
| consumer | 125 | 58 | 192668630 |  |  |  |  |  | taint_prop |
| consumer | 126 | 67 | 192670555 |  |  |  |  |  | taint_prop |
| consumer | 127 | 67 | 192670940 |  |  |  |  |  | taint_prop |
| consumer | 128 | 67 | 192670940 |  |  |  |  |  | taint_prop |
| consumer | 129 | 67 | 192670940 |  |  |  |  |  | taint_prop |
| consumer | 130 | 67 | 192670940 |  |  |  |  |  | taint_prop |
| consumer | 131 | 76 | 192672865 |  |  |  |  |  | taint_prop |
| consumer | 132 | 76 | 192673250 |  |  |  |  |  | taint_prop |
| consumer | 133 | 76 | 192673250 |  |  |  |  |  | taint_prop |
| consumer | 134 | 76 | 192673250 |  |  |  |  |  | taint_prop |
| consumer | 135 | 76 | 192673250 |  |  |  |  |  | taint_prop |
| chain_end | 136 | 135 | 214469640 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=493390 pa=
- L2 `lsq_sendfrag`：va=493390 pa=
- L2 `tlb_translate`：va=493390 pa=
- L3 `resp`：va=79390 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=136。
- 事件数：本 seed 流共 136 条，其中 fault_id=1 链 136 条；最后一条为 `chain_end`（event_id=136, tick=214469640）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s3/A07-F4-W3/seed3/prop_evt.txt.gz` | `cdc23e7286f92f19aabee6e38dc37a4a495c1e8a7eb8faa5696004b76ab4d04d` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s3/A07-F4-W3/seed3/stats.txt` | `3814737eb92f745d8eecbd84d5d7fa8ff60042848545409e1ebb6f87cd02b781` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s3/A07-F4-W3/seed3/run.out` | `a22b87083b8a5a712d830bfa0b615382d5dc621dc1e5a1310b28926649014c27` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s3/A07-F4-W3/seed3/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s3/A07-F4-W3/chain_report.json` | `9f61465d1a1b557be8ae1ceb93b9839fe88b088118576ecebc6a86b67b213c81` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A07-F4-W3_s3/manifest.json` | `c9782bbd4e4197b7e1bcecc6ecaa5e2d1a6663d702dfcfe17078570425aa3ae7` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

