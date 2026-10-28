# A05-F0-W3 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A05-F0-W3` |
| 模型 | A05（AGU 操作数级寻址） |
| 频率档 | F0 |
| 负载 | W3 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | Tick: 16786000, Site: lsq_pushRequest_PRE, mode=a05_prepost, old_addr=0x4932f8, new_addr=0x493300, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a05d, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s1 --cells A05-F0-W3 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=16786000，request_id=，corr=origin，注入前地址 `before=4932f8`，注入后地址 `after=493300`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 16786000, Site: lsq_pushRequest_PRE, mode=a05_prepost, old_addr=0x4932f8, new_addr=0x493300, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a05d, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4932f8` → `493300`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a05d`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 16786000 |  | 4932f8 |  |  |  | origin |
| addr_form | 2 | 1 | 16786000 |  | 493300 |  |  |  | origin |
| lsq_push | 3 | 2 | 16786000 |  | 493300 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 16786000 | 15078 | 493300 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 16786000 | 15078 | 493300 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 16786000 | 15078 | 493300 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 16786000 | 15078 | 493300 |  |  |  | seq_primary |
| resp | 8 | 7 | 16786770 | 15078 | 79300 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 16786770 | 15078 | 493300 | 79300 |  |  | seq_primary |
| taint_reg | 10 | 9 | 16786770 | 15078 | 79300 |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 16793315 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 16793700 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 16794855 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 16795240 |  |  |  |  |  | taint_prop |
| consumer | 15 | 14 | 16796395 |  |  |  |  |  | taint_prop |
| consumer | 16 | 15 | 16796780 |  |  |  |  |  | taint_prop |
| consumer | 17 | 16 | 16797935 |  |  |  |  |  | taint_prop |
| consumer | 18 | 17 | 16798320 |  |  |  |  |  | taint_prop |
| consumer | 19 | 18 | 16799475 |  |  |  |  |  | taint_prop |
| consumer | 20 | 19 | 16799860 |  |  |  |  |  | taint_prop |
| consumer | 21 | 20 | 16801015 |  |  |  |  |  | taint_prop |
| consumer | 22 | 21 | 16801400 |  |  |  |  |  | taint_prop |
| consumer | 23 | 22 | 16802555 |  |  |  |  |  | taint_prop |
| consumer | 24 | 23 | 16802940 |  |  |  |  |  | taint_prop |
| consumer | 25 | 24 | 16804095 |  |  |  |  |  | taint_prop |
| consumer | 26 | 25 | 16804480 |  |  |  |  |  | taint_prop |
| consumer | 27 | 26 | 16805635 |  |  |  |  |  | taint_prop |
| consumer | 28 | 27 | 16806020 |  |  |  |  |  | taint_prop |
| consumer | 29 | 28 | 16807175 |  |  |  |  |  | taint_prop |
| consumer | 30 | 29 | 16807560 |  |  |  |  |  | taint_prop |
| consumer | 31 | 30 | 16808715 |  |  |  |  |  | taint_prop |
| consumer | 32 | 31 | 16809100 |  |  |  |  |  | taint_prop |
| consumer | 33 | 32 | 16810255 |  |  |  |  |  | taint_prop |
| consumer | 34 | 33 | 16810640 |  |  |  |  |  | taint_prop |
| consumer | 35 | 34 | 16811795 |  |  |  |  |  | taint_prop |
| consumer | 36 | 35 | 16812180 |  |  |  |  |  | taint_prop |
| consumer | 37 | 36 | 16813335 |  |  |  |  |  | taint_prop |
| consumer | 38 | 37 | 16813720 |  |  |  |  |  | taint_prop |
| consumer | 39 | 38 | 16814875 |  |  |  |  |  | taint_prop |
| consumer | 40 | 39 | 16815260 |  |  |  |  |  | taint_prop |
| consumer | 41 | 40 | 16816415 |  |  |  |  |  | taint_prop |
| consumer | 42 | 41 | 16816800 |  |  |  |  |  | taint_prop |
| consumer | 43 | 42 | 16817955 |  |  |  |  |  | taint_prop |
| consumer | 44 | 43 | 16818340 |  |  |  |  |  | taint_prop |
| consumer | 45 | 44 | 16819495 |  |  |  |  |  | taint_prop |
| consumer | 46 | 45 | 16819880 |  |  |  |  |  | taint_prop |
| consumer | 47 | 46 | 16821035 |  |  |  |  |  | taint_prop |
| consumer | 48 | 47 | 16821420 |  |  |  |  |  | taint_prop |
| consumer | 49 | 48 | 16822575 |  |  |  |  |  | taint_prop |
| consumer | 50 | 49 | 16822960 |  |  |  |  |  | taint_prop |
| consumer | 51 | 50 | 16824115 |  |  |  |  |  | taint_prop |
| consumer | 52 | 51 | 16824500 |  |  |  |  |  | taint_prop |
| consumer | 53 | 52 | 16825655 |  |  |  |  |  | taint_prop |
| consumer | 54 | 53 | 16826040 |  |  |  |  |  | taint_prop |
| consumer | 55 | 54 | 16827195 |  |  |  |  |  | taint_prop |
| consumer | 56 | 55 | 16827580 |  |  |  |  |  | taint_prop |
| consumer | 57 | 13 | 16829120 |  |  |  |  |  | taint_prop |
| consumer | 58 | 15 | 16830660 |  |  |  |  |  | taint_prop |
| consumer | 59 | 17 | 16832200 |  |  |  |  |  | taint_prop |
| consumer | 60 | 19 | 16833740 |  |  |  |  |  | taint_prop |
| consumer | 61 | 21 | 16835280 |  |  |  |  |  | taint_prop |
| consumer | 62 | 23 | 16836820 |  |  |  |  |  | taint_prop |
| consumer | 63 | 25 | 16838360 |  |  |  |  |  | taint_prop |
| consumer | 64 | 27 | 16839900 |  |  |  |  |  | taint_prop |
| consumer | 65 | 29 | 16841440 |  |  |  |  |  | taint_prop |
| consumer | 66 | 31 | 16842980 |  |  |  |  |  | taint_prop |
| consumer | 67 | 33 | 16844520 |  |  |  |  |  | taint_prop |
| consumer | 68 | 36 | 16845290 |  |  |  |  |  | taint_prop |
| consumer | 69 | 36 | 16845675 |  |  |  |  |  | taint_prop |
| consumer | 70 | 36 | 16845675 |  |  |  |  |  | taint_prop |
| consumer | 71 | 68 | 16845675 |  |  |  |  |  | taint_prop |
| consumer | 72 | 67 | 16847985 |  |  |  |  |  | taint_prop |
| consumer | 73 | 43 | 16848755 |  |  |  |  |  | taint_prop |
| consumer | 74 | 43 | 16849525 |  |  |  |  |  | taint_prop |
| consumer | 75 | 43 | 16849525 |  |  |  |  |  | taint_prop |
| consumer | 76 | 45 | 16850295 |  |  |  |  |  | taint_prop |
| consumer | 77 | 46 | 16854915 |  |  |  |  |  | taint_prop |
| consumer | 78 | 77 | 16856070 |  |  |  |  |  | taint_prop |
| consumer | 79 | 77 | 16856070 |  |  |  |  |  | taint_prop |
| consumer | 80 | 77 | 16856070 |  |  |  |  |  | taint_prop |
| consumer | 81 | 77 | 16856070 |  |  |  |  |  | taint_prop |
| consumer | 82 | 81 | 16856840 |  |  |  |  |  | taint_prop |
| consumer | 83 | 12 | 16862615 |  |  |  |  |  | taint_prop |
| consumer | 84 | 12 | 16862615 |  |  |  |  |  | taint_prop |
| consumer | 85 | 13 | 16862615 |  |  |  |  |  | taint_prop |
| consumer | 86 | 12 | 16862615 |  |  |  |  |  | taint_prop |
| consumer | 87 | 59 | 16869160 |  |  |  |  |  | taint_prop |
| consumer | 88 | 59 | 16869160 |  |  |  |  |  | taint_prop |
| consumer | 89 | 18 | 16869160 |  |  |  |  |  | taint_prop |
| consumer | 90 | 14 | 16874165 |  |  |  |  |  | taint_prop |
| consumer | 91 | 22 | 16875705 |  |  |  |  |  | taint_prop |
| consumer | 92 | 22 | 16875705 |  |  |  |  |  | taint_prop |
| consumer | 93 | 24 | 16876475 |  |  |  |  |  | taint_prop |
| consumer | 94 | 27 | 16881095 |  |  |  |  |  | taint_prop |
| consumer | 95 | 94 | 16882250 |  |  |  |  |  | taint_prop |
| consumer | 96 | 94 | 16882250 |  |  |  |  |  | taint_prop |
| consumer | 97 | 94 | 16882250 |  |  |  |  |  | taint_prop |
| consumer | 98 | 94 | 16882250 |  |  |  |  |  | taint_prop |
| consumer | 99 | 98 | 16883020 |  |  |  |  |  | taint_prop |
| consumer | 100 | 32 | 16888795 |  |  |  |  |  | taint_prop |
| consumer | 101 | 32 | 16888795 |  |  |  |  |  | taint_prop |
| consumer | 102 | 41 | 16913820 |  |  |  |  |  | taint_prop |
| consumer | 103 | 44 | 16914590 |  |  |  |  |  | taint_prop |
| consumer | 104 | 44 | 16915360 |  |  |  |  |  | taint_prop |
| consumer | 105 | 44 | 16915360 |  |  |  |  |  | taint_prop |
| consumer | 106 | 44 | 16915360 |  |  |  |  |  | taint_prop |
| consumer | 107 | 47 | 16916130 |  |  |  |  |  | taint_prop |
| consumer | 108 | 42 | 16920750 |  |  |  |  |  | taint_prop |
| consumer | 109 | 108 | 16921905 |  |  |  |  |  | taint_prop |
| consumer | 110 | 108 | 16921905 |  |  |  |  |  | taint_prop |
| consumer | 111 | 108 | 16921905 |  |  |  |  |  | taint_prop |
| consumer | 112 | 86 | 16928450 |  |  |  |  |  | taint_prop |
| consumer | 113 | 86 | 16928450 |  |  |  |  |  | taint_prop |
| consumer | 114 | 86 | 16928450 |  |  |  |  |  | taint_prop |
| consumer | 115 | 13 | 16933455 |  |  |  |  |  | taint_prop |
| consumer | 116 | 22 | 16934995 |  |  |  |  |  | taint_prop |
| consumer | 117 | 22 | 16934995 |  |  |  |  |  | taint_prop |
| consumer | 118 | 22 | 16934995 |  |  |  |  |  | taint_prop |
| consumer | 119 | 22 | 16934995 |  |  |  |  |  | taint_prop |
| consumer | 120 | 66 | 16941540 |  |  |  |  |  | taint_prop |
| consumer | 121 | 66 | 16941540 |  |  |  |  |  | taint_prop |
| consumer | 122 | 66 | 16941540 |  |  |  |  |  | taint_prop |
| consumer | 123 | 99 | 16946930 |  |  |  |  |  | taint_prop |
| consumer | 124 | 123 | 16948085 |  |  |  |  |  | taint_prop |
| consumer | 125 | 123 | 16948085 |  |  |  |  |  | taint_prop |
| consumer | 126 | 123 | 16948085 |  |  |  |  |  | taint_prop |
| consumer | 127 | 43 | 16954630 |  |  |  |  |  | taint_prop |
| consumer | 128 | 43 | 16954630 |  |  |  |  |  | taint_prop |
| consumer | 129 | 43 | 16954630 |  |  |  |  |  | taint_prop |
| consumer | 130 | 53 | 16956170 |  |  |  |  |  | taint_prop |
| consumer | 131 | 130 | 16956940 |  |  |  |  |  | taint_prop |
| consumer | 132 | 130 | 16956940 |  |  |  |  |  | taint_prop |
| consumer | 133 | 130 | 16956940 |  |  |  |  |  | taint_prop |
| chain_end | 134 | 133 | 19928370 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=493300 pa=
- L2 `lsq_sendfrag`：va=493300 pa=
- L2 `tlb_translate`：va=493300 pa=
- L3 `resp`：va=79300 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`SDC`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=134。
- 事件数：本 seed 流共 134 条，其中 fault_id=1 链 134 条；最后一条为 `chain_end`（event_id=134, tick=19928370）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s1/A05-F0-W3/seed1/prop_evt.txt.gz` | `22761011cb8f92e2d68c6b8c4dd0d64c981fce5d953002a89d2822e15b4a6147` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s1/A05-F0-W3/seed1/stats.txt` | `7d439a1f4532bcf5ef44d508ddfb0cd29a80de5b1b68ee08e3baabb0ccedba7a` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s1/A05-F0-W3/seed1/run.out` | `77cb6954b1425eeb33040b796080ce83e6ddf2c3f7042210bff9ee679a12ac37` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s1/A05-F0-W3/seed1/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s1/A05-F0-W3/chain_report.json` | `d0cff63f9eaf915c62336b0c8c8dc962a4b63a5d6516b95fde42892450ac71db` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A05-F0-W3_s1/manifest.json` | `2af3b458c5db89b378c7d8b1f5fdf3a02bc56d24e176827f56eae8e88a8d6d1b` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

