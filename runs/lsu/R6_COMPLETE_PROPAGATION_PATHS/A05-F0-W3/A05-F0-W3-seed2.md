# A05-F0-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A05-F0-W3` |
| 模型 | A05（AGU 操作数级寻址） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 16693600, Site: lsq_pushRequest_PRE, mode=a05_prepost, old_addr=0x493208, new_addr=0x493210, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a05d, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s2 --cells A05-F0-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=16693600，request_id=，corr=origin，注入前地址 `before=493208`，注入后地址 `after=493210`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 16693600, Site: lsq_pushRequest_PRE, mode=a05_prepost, old_addr=0x493208, new_addr=0x493210, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a05d, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`493208` → `493210`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a05d`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 16693600 |  | 493208 |  |  |  | origin |
| addr_form | 2 | 1 | 16693600 |  | 493210 |  |  |  | origin |
| lsq_push | 3 | 2 | 16693600 |  | 493210 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 16693600 | 14628 | 493210 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 16693600 | 14628 | 493210 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 16693600 | 14628 | 493210 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 16693600 | 14628 | 493210 |  |  |  | seq_primary |
| resp | 8 | 7 | 16694370 | 14628 | 79210 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 16694370 | 14628 | 493210 | 79210 |  |  | seq_primary |
| taint_reg | 10 | 9 | 16694370 | 14628 | 79210 |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 16695140 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 16695525 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 16696680 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 16700530 |  |  |  |  |  | taint_prop |
| consumer | 15 | 14 | 16701685 |  |  |  |  |  | taint_prop |
| consumer | 16 | 15 | 16705535 |  |  |  |  |  | taint_prop |
| consumer | 17 | 16 | 16706690 |  |  |  |  |  | taint_prop |
| consumer | 18 | 17 | 16710540 |  |  |  |  |  | taint_prop |
| consumer | 19 | 18 | 16711695 |  |  |  |  |  | taint_prop |
| consumer | 20 | 19 | 16715545 |  |  |  |  |  | taint_prop |
| consumer | 21 | 20 | 16716700 |  |  |  |  |  | taint_prop |
| consumer | 22 | 21 | 16720550 |  |  |  |  |  | taint_prop |
| consumer | 23 | 22 | 16721705 |  |  |  |  |  | taint_prop |
| consumer | 24 | 23 | 16725555 |  |  |  |  |  | taint_prop |
| consumer | 25 | 24 | 16726710 |  |  |  |  |  | taint_prop |
| consumer | 26 | 25 | 16730560 |  |  |  |  |  | taint_prop |
| consumer | 27 | 26 | 16731715 |  |  |  |  |  | taint_prop |
| consumer | 28 | 27 | 16735565 |  |  |  |  |  | taint_prop |
| consumer | 29 | 28 | 16736720 |  |  |  |  |  | taint_prop |
| consumer | 30 | 29 | 16740570 |  |  |  |  |  | taint_prop |
| consumer | 31 | 30 | 16741725 |  |  |  |  |  | taint_prop |
| consumer | 32 | 31 | 16745575 |  |  |  |  |  | taint_prop |
| consumer | 33 | 32 | 16746730 |  |  |  |  |  | taint_prop |
| consumer | 34 | 33 | 16750580 |  |  |  |  |  | taint_prop |
| consumer | 35 | 34 | 16751735 |  |  |  |  |  | taint_prop |
| consumer | 36 | 35 | 16755585 |  |  |  |  |  | taint_prop |
| consumer | 37 | 36 | 16756740 |  |  |  |  |  | taint_prop |
| consumer | 38 | 37 | 16760590 |  |  |  |  |  | taint_prop |
| consumer | 39 | 38 | 16761745 |  |  |  |  |  | taint_prop |
| consumer | 40 | 39 | 16765595 |  |  |  |  |  | taint_prop |
| consumer | 41 | 40 | 16766750 |  |  |  |  |  | taint_prop |
| consumer | 42 | 41 | 16770600 |  |  |  |  |  | taint_prop |
| consumer | 43 | 42 | 16771755 |  |  |  |  |  | taint_prop |
| consumer | 44 | 43 | 16772140 |  |  |  |  |  | taint_prop |
| consumer | 45 | 44 | 16773295 |  |  |  |  |  | taint_prop |
| consumer | 46 | 45 | 16773680 |  |  |  |  |  | taint_prop |
| consumer | 47 | 46 | 16774835 |  |  |  |  |  | taint_prop |
| consumer | 48 | 47 | 16775220 |  |  |  |  |  | taint_prop |
| consumer | 49 | 48 | 16776375 |  |  |  |  |  | taint_prop |
| consumer | 50 | 20 | 16777915 |  |  |  |  |  | taint_prop |
| consumer | 51 | 22 | 16779840 |  |  |  |  |  | taint_prop |
| consumer | 52 | 23 | 16781380 |  |  |  |  |  | taint_prop |
| consumer | 53 | 52 | 16782535 |  |  |  |  |  | taint_prop |
| consumer | 54 | 53 | 16782920 |  |  |  |  |  | taint_prop |
| consumer | 55 | 54 | 16784075 |  |  |  |  |  | taint_prop |
| consumer | 56 | 55 | 16784460 |  |  |  |  |  | taint_prop |
| consumer | 57 | 56 | 16785615 |  |  |  |  |  | taint_prop |
| consumer | 58 | 57 | 16786000 |  |  |  |  |  | taint_prop |
| consumer | 59 | 58 | 16787155 |  |  |  |  |  | taint_prop |
| consumer | 60 | 28 | 16788695 |  |  |  |  |  | taint_prop |
| consumer | 61 | 30 | 16790620 |  |  |  |  |  | taint_prop |
| consumer | 62 | 31 | 16792160 |  |  |  |  |  | taint_prop |
| consumer | 63 | 62 | 16793315 |  |  |  |  |  | taint_prop |
| consumer | 64 | 63 | 16793700 |  |  |  |  |  | taint_prop |
| consumer | 65 | 64 | 16794855 |  |  |  |  |  | taint_prop |
| consumer | 66 | 65 | 16795240 |  |  |  |  |  | taint_prop |
| consumer | 67 | 66 | 16796395 |  |  |  |  |  | taint_prop |
| consumer | 68 | 67 | 16796780 |  |  |  |  |  | taint_prop |
| consumer | 69 | 68 | 16797935 |  |  |  |  |  | taint_prop |
| consumer | 70 | 36 | 16799475 |  |  |  |  |  | taint_prop |
| consumer | 71 | 38 | 16801400 |  |  |  |  |  | taint_prop |
| consumer | 72 | 39 | 16802940 |  |  |  |  |  | taint_prop |
| consumer | 73 | 47 | 16809100 |  |  |  |  |  | taint_prop |
| consumer | 74 | 49 | 16810640 |  |  |  |  |  | taint_prop |
| consumer | 75 | 50 | 16812180 |  |  |  |  |  | taint_prop |
| consumer | 76 | 22 | 16813720 |  |  |  |  |  | taint_prop |
| consumer | 77 | 23 | 16815260 |  |  |  |  |  | taint_prop |
| consumer | 78 | 57 | 16819880 |  |  |  |  |  | taint_prop |
| consumer | 79 | 59 | 16821420 |  |  |  |  |  | taint_prop |
| consumer | 80 | 60 | 16822960 |  |  |  |  |  | taint_prop |
| consumer | 81 | 30 | 16824500 |  |  |  |  |  | taint_prop |
| consumer | 82 | 31 | 16826040 |  |  |  |  |  | taint_prop |
| consumer | 83 | 67 | 16830660 |  |  |  |  |  | taint_prop |
| consumer | 84 | 69 | 16832200 |  |  |  |  |  | taint_prop |
| consumer | 85 | 39 | 16836820 |  |  |  |  |  | taint_prop |
| consumer | 86 | 75 | 16845675 |  |  |  |  |  | taint_prop |
| consumer | 87 | 75 | 16845675 |  |  |  |  |  | taint_prop |
| consumer | 88 | 21 | 16845675 |  |  |  |  |  | taint_prop |
| consumer | 89 | 48 | 16847985 |  |  |  |  |  | taint_prop |
| consumer | 90 | 55 | 16849525 |  |  |  |  |  | taint_prop |
| consumer | 91 | 28 | 16856070 |  |  |  |  |  | taint_prop |
| consumer | 92 | 28 | 16856070 |  |  |  |  |  | taint_prop |
| consumer | 93 | 29 | 16856840 |  |  |  |  |  | taint_prop |
| consumer | 94 | 31 | 16861460 |  |  |  |  |  | taint_prop |
| consumer | 95 | 94 | 16862615 |  |  |  |  |  | taint_prop |
| consumer | 96 | 94 | 16862615 |  |  |  |  |  | taint_prop |
| consumer | 97 | 84 | 16869160 |  |  |  |  |  | taint_prop |
| consumer | 98 | 84 | 16869160 |  |  |  |  |  | taint_prop |
| consumer | 99 | 36 | 16869160 |  |  |  |  |  | taint_prop |
| consumer | 100 | 71 | 16875705 |  |  |  |  |  | taint_prop |
| consumer | 101 | 71 | 16875705 |  |  |  |  |  | taint_prop |
| consumer | 102 | 72 | 16876475 |  |  |  |  |  | taint_prop |
| consumer | 103 | 18 | 16882250 |  |  |  |  |  | taint_prop |
| consumer | 104 | 18 | 16882250 |  |  |  |  |  | taint_prop |
| consumer | 105 | 18 | 16882250 |  |  |  |  |  | taint_prop |
| consumer | 106 | 19 | 16883020 |  |  |  |  |  | taint_prop |
| consumer | 107 | 73 | 16888795 |  |  |  |  |  | taint_prop |
| consumer | 108 | 73 | 16888795 |  |  |  |  |  | taint_prop |
| consumer | 109 | 53 | 16913820 |  |  |  |  |  | taint_prop |
| consumer | 110 | 25 | 16914590 |  |  |  |  |  | taint_prop |
| consumer | 111 | 25 | 16915360 |  |  |  |  |  | taint_prop |
| consumer | 112 | 25 | 16915360 |  |  |  |  |  | taint_prop |
| consumer | 113 | 25 | 16915360 |  |  |  |  |  | taint_prop |
| consumer | 114 | 61 | 16921905 |  |  |  |  |  | taint_prop |
| consumer | 115 | 61 | 16921905 |  |  |  |  |  | taint_prop |
| consumer | 116 | 61 | 16921905 |  |  |  |  |  | taint_prop |
| consumer | 117 | 34 | 16928450 |  |  |  |  |  | taint_prop |
| consumer | 118 | 34 | 16928450 |  |  |  |  |  | taint_prop |
| consumer | 119 | 34 | 16928450 |  |  |  |  |  | taint_prop |
| consumer | 120 | 65 | 16933455 |  |  |  |  |  | taint_prop |
| consumer | 121 | 71 | 16934995 |  |  |  |  |  | taint_prop |
| consumer | 122 | 71 | 16934995 |  |  |  |  |  | taint_prop |
| consumer | 123 | 71 | 16934995 |  |  |  |  |  | taint_prop |
| consumer | 124 | 71 | 16934995 |  |  |  |  |  | taint_prop |
| consumer | 125 | 46 | 16941540 |  |  |  |  |  | taint_prop |
| consumer | 126 | 46 | 16941540 |  |  |  |  |  | taint_prop |
| consumer | 127 | 46 | 16941540 |  |  |  |  |  | taint_prop |
| consumer | 128 | 106 | 16946930 |  |  |  |  |  | taint_prop |
| consumer | 129 | 128 | 16948085 |  |  |  |  |  | taint_prop |
| consumer | 130 | 128 | 16948085 |  |  |  |  |  | taint_prop |
| consumer | 131 | 128 | 16948085 |  |  |  |  |  | taint_prop |
| consumer | 132 | 55 | 16954630 |  |  |  |  |  | taint_prop |
| consumer | 133 | 55 | 16954630 |  |  |  |  |  | taint_prop |
| consumer | 134 | 55 | 16954630 |  |  |  |  |  | taint_prop |
| consumer | 135 | 35 | 16956940 |  |  |  |  |  | taint_prop |
| consumer | 136 | 35 | 16956940 |  |  |  |  |  | taint_prop |
| consumer | 137 | 35 | 16956940 |  |  |  |  |  | taint_prop |
| chain_end | 138 | 137 | 19928370 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=493210 pa=
- L2 `lsq_sendfrag`：va=493210 pa=
- L2 `tlb_translate`：va=493210 pa=
- L3 `resp`：va=79210 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`SDC`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=138。
- 事件数：本 seed 流共 138 条，其中 fault_id=1 链 138 条；最后一条为 `chain_end`（event_id=138, tick=19928370）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s2/A05-F0-W3/seed2/prop_evt.txt.gz` | `3ab6d092287407dce303f726a3f94bf1e3d5fcf90eddd14da0cb7fdaa5d5178a` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s2/A05-F0-W3/seed2/stats.txt` | `5517556fe54521e843be714d1e40f0fc09dec95a06307d8649ca5e1faf79131a` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s2/A05-F0-W3/seed2/run.out` | `962ef3504e5488055d9985fc525e0a331720d2f2c62801028c89483c06c056ce` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s2/A05-F0-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s2/A05-F0-W3/chain_report.json` | `cd1e3207a7e87e95cfadb3a2656864f30cccd70be7a866c5acf4645ea865085d` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s2/manifest.json` | `5d70ebf7f19b2b56f0d291ad473ce0cfe669408b46a85ec2621df9a2ab2c1bc8` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

