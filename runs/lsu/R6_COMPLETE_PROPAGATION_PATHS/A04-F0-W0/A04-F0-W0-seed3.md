# A04-F0-W0 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F0-W0` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F0 |
| 负载 | W0 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 16647015, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x491ae0, new_addr=0x491ae8, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=data, object_base=0x4919a0, object_size=512, source_offset=320, target_offset=328 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s3 --cells A04-F0-W0 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=16647015，request_id=，corr=origin，注入前地址 `before=491ae0`，注入后地址 `after=491ae8`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 16647015, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x491ae0, new_addr=0x491ae8, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=data, object_base=0x4919a0, object_size=512, source_offset=320, target_offset=328
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`491ae0` → `491ae8`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a04a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 16647015 |  | 491ae0 |  |  |  | origin |
| addr_form | 2 | 1 | 16647015 |  | 491ae8 |  |  |  | origin |
| lsq_push | 3 | 2 | 16647015 |  | 491ae8 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 16647015 | 16010 | 491ae8 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 16647015 | 16010 | 491ae8 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 16647015 | 16010 | 491ae8 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 16647015 | 16010 | 491ae8 |  |  |  | seq_primary |
| resp | 8 | 7 | 16647785 | 16010 | 77ae8 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 16647785 | 16010 | 491ae8 | 77ae8 |  |  | seq_primary |
| taint_reg | 10 | 9 | 16647785 | 16010 | 77ae8 |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 16655485 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 16655870 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 16657025 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 16657410 |  |  |  |  |  | taint_prop |
| consumer | 15 | 14 | 16658565 |  |  |  |  |  | taint_prop |
| consumer | 16 | 15 | 16658950 |  |  |  |  |  | taint_prop |
| consumer | 17 | 16 | 16660105 |  |  |  |  |  | taint_prop |
| consumer | 18 | 17 | 16660490 |  |  |  |  |  | taint_prop |
| consumer | 19 | 18 | 16661645 |  |  |  |  |  | taint_prop |
| consumer | 20 | 19 | 16662030 |  |  |  |  |  | taint_prop |
| consumer | 21 | 20 | 16663185 |  |  |  |  |  | taint_prop |
| consumer | 22 | 21 | 16663570 |  |  |  |  |  | taint_prop |
| consumer | 23 | 22 | 16664725 |  |  |  |  |  | taint_prop |
| consumer | 24 | 23 | 16665110 |  |  |  |  |  | taint_prop |
| consumer | 25 | 24 | 16666265 |  |  |  |  |  | taint_prop |
| consumer | 26 | 25 | 16666650 |  |  |  |  |  | taint_prop |
| consumer | 27 | 26 | 16667805 |  |  |  |  |  | taint_prop |
| consumer | 28 | 27 | 16668190 |  |  |  |  |  | taint_prop |
| consumer | 29 | 28 | 16669345 |  |  |  |  |  | taint_prop |
| consumer | 30 | 29 | 16669730 |  |  |  |  |  | taint_prop |
| consumer | 31 | 30 | 16670885 |  |  |  |  |  | taint_prop |
| consumer | 32 | 31 | 16671270 |  |  |  |  |  | taint_prop |
| consumer | 33 | 32 | 16672425 |  |  |  |  |  | taint_prop |
| consumer | 34 | 33 | 16672810 |  |  |  |  |  | taint_prop |
| consumer | 35 | 34 | 16673965 |  |  |  |  |  | taint_prop |
| consumer | 36 | 35 | 16674350 |  |  |  |  |  | taint_prop |
| consumer | 37 | 36 | 16675505 |  |  |  |  |  | taint_prop |
| consumer | 38 | 37 | 16675890 |  |  |  |  |  | taint_prop |
| consumer | 39 | 38 | 16677045 |  |  |  |  |  | taint_prop |
| consumer | 40 | 39 | 16677430 |  |  |  |  |  | taint_prop |
| consumer | 41 | 40 | 16678585 |  |  |  |  |  | taint_prop |
| consumer | 42 | 41 | 16678970 |  |  |  |  |  | taint_prop |
| consumer | 43 | 42 | 16680125 |  |  |  |  |  | taint_prop |
| consumer | 44 | 43 | 16680510 |  |  |  |  |  | taint_prop |
| consumer | 45 | 44 | 16681665 |  |  |  |  |  | taint_prop |
| consumer | 46 | 45 | 16682050 |  |  |  |  |  | taint_prop |
| consumer | 47 | 46 | 16683205 |  |  |  |  |  | taint_prop |
| consumer | 48 | 47 | 16683590 |  |  |  |  |  | taint_prop |
| consumer | 49 | 48 | 16684745 |  |  |  |  |  | taint_prop |
| consumer | 50 | 49 | 16685130 |  |  |  |  |  | taint_prop |
| consumer | 51 | 50 | 16686285 |  |  |  |  |  | taint_prop |
| consumer | 52 | 51 | 16686670 |  |  |  |  |  | taint_prop |
| consumer | 53 | 52 | 16687825 |  |  |  |  |  | taint_prop |
| consumer | 54 | 53 | 16688210 |  |  |  |  |  | taint_prop |
| consumer | 55 | 54 | 16689365 |  |  |  |  |  | taint_prop |
| consumer | 56 | 55 | 16689750 |  |  |  |  |  | taint_prop |
| consumer | 57 | 13 | 16691290 |  |  |  |  |  | taint_prop |
| consumer | 58 | 15 | 17102855 |  |  |  |  |  | taint_prop |
| consumer | 59 | 18 | 17104395 |  |  |  |  |  | taint_prop |
| consumer | 60 | 59 | 17105550 |  |  |  |  |  | taint_prop |
| consumer | 61 | 60 | 17106320 |  |  |  |  |  | taint_prop |
| consumer | 62 | 61 | 17107090 |  |  |  |  |  | taint_prop |
| consumer | 63 | 22 | 17112095 |  |  |  |  |  | taint_prop |
| consumer | 64 | 31 | 17117100 |  |  |  |  |  | taint_prop |
| consumer | 65 | 64 | 17118255 |  |  |  |  |  | taint_prop |
| consumer | 66 | 65 | 17122105 |  |  |  |  |  | taint_prop |
| consumer | 67 | 39 | 17127110 |  |  |  |  |  | taint_prop |
| consumer | 68 | 67 | 17128265 |  |  |  |  |  | taint_prop |
| consumer | 69 | 68 | 17132115 |  |  |  |  |  | taint_prop |
| consumer | 70 | 40 | 17137120 |  |  |  |  |  | taint_prop |
| consumer | 71 | 52 | 17142125 |  |  |  |  |  | taint_prop |
| consumer | 72 | 53 | 17147130 |  |  |  |  |  | taint_prop |
| consumer | 73 | 61 | 17167150 |  |  |  |  |  | taint_prop |
| consumer | 74 | 36 | 17171385 |  |  |  |  |  | taint_prop |
| consumer | 75 | 31 | 17174465 |  |  |  |  |  | taint_prop |
| consumer | 76 | 43 | 17179085 |  |  |  |  |  | taint_prop |
| consumer | 77 | 40 | 17182935 |  |  |  |  |  | taint_prop |
| consumer | 78 | 53 | 17187940 |  |  |  |  |  | taint_prop |
| consumer | 79 | 78 | 17188710 |  |  |  |  |  | taint_prop |
| consumer | 80 | 79 | 17189865 |  |  |  |  |  | taint_prop |
| consumer | 81 | 62 | 17196410 |  |  |  |  |  | taint_prop |
| consumer | 82 | 26 | 17198335 |  |  |  |  |  | taint_prop |
| consumer | 83 | 35 | 17202185 |  |  |  |  |  | taint_prop |
| consumer | 84 | 67 | 17209115 |  |  |  |  |  | taint_prop |
| consumer | 85 | 84 | 17209885 |  |  |  |  |  | taint_prop |
| consumer | 86 | 52 | 17213735 |  |  |  |  |  | taint_prop |
| consumer | 87 | 86 | 17214890 |  |  |  |  |  | taint_prop |
| consumer | 88 | 15 | 17218740 |  |  |  |  |  | taint_prop |
| consumer | 89 | 18 | 17222590 |  |  |  |  |  | taint_prop |
| consumer | 90 | 89 | 17223360 |  |  |  |  |  | taint_prop |
| consumer | 91 | 90 | 17224515 |  |  |  |  |  | taint_prop |
| consumer | 92 | 91 | 17225285 |  |  |  |  |  | taint_prop |
| consumer | 93 | 14 | 17227210 |  |  |  |  |  | taint_prop |
| consumer | 94 | 32 | 17230290 |  |  |  |  |  | taint_prop |
| consumer | 95 | 94 | 17231060 |  |  |  |  |  | taint_prop |
| consumer | 96 | 37 | 17232985 |  |  |  |  |  | taint_prop |
| consumer | 97 | 96 | 17234140 |  |  |  |  |  | taint_prop |
| consumer | 98 | 38 | 17236835 |  |  |  |  |  | taint_prop |
| consumer | 99 | 70 | 17242610 |  |  |  |  |  | taint_prop |
| consumer | 100 | 54 | 17244535 |  |  |  |  |  | taint_prop |
| consumer | 101 | 100 | 17245690 |  |  |  |  |  | taint_prop |
| consumer | 102 | 101 | 17246460 |  |  |  |  |  | taint_prop |
| consumer | 103 | 102 | 17247615 |  |  |  |  |  | taint_prop |
| consumer | 104 | 58 | 17250695 |  |  |  |  |  | taint_prop |
| consumer | 105 | 45 | 17398920 |  |  |  |  |  | taint_prop |
| consumer | 106 | 49 | 17456285 |  |  |  |  |  | taint_prop |
| consumer | 107 | 13 | 17469375 |  |  |  |  |  | taint_prop |
| consumer | 108 | 27 | 17482465 |  |  |  |  |  | taint_prop |
| consumer | 109 | 27 | 17482465 |  |  |  |  |  | taint_prop |
| consumer | 110 | 65 | 17487470 |  |  |  |  |  | taint_prop |
| consumer | 111 | 16 | 17489010 |  |  |  |  |  | taint_prop |
| consumer | 112 | 40 | 17495555 |  |  |  |  |  | taint_prop |
| consumer | 113 | 40 | 17495555 |  |  |  |  |  | taint_prop |
| consumer | 114 | 40 | 17495555 |  |  |  |  |  | taint_prop |
| consumer | 115 | 71 | 17502100 |  |  |  |  |  | taint_prop |
| consumer | 116 | 71 | 17502100 |  |  |  |  |  | taint_prop |
| consumer | 117 | 71 | 17502100 |  |  |  |  |  | taint_prop |
| consumer | 118 | 58 | 17508645 |  |  |  |  |  | taint_prop |
| consumer | 119 | 58 | 17508645 |  |  |  |  |  | taint_prop |
| consumer | 120 | 58 | 17508645 |  |  |  |  |  | taint_prop |
| consumer | 121 | 19 | 17520965 |  |  |  |  |  | taint_prop |
| consumer | 122 | 19 | 17520965 |  |  |  |  |  | taint_prop |
| consumer | 123 | 19 | 17520965 |  |  |  |  |  | taint_prop |
| consumer | 124 | 22 | 17526740 |  |  |  |  |  | taint_prop |
| consumer | 125 | 22 | 17527510 |  |  |  |  |  | taint_prop |
| consumer | 126 | 22 | 17527510 |  |  |  |  |  | taint_prop |
| consumer | 127 | 22 | 17527510 |  |  |  |  |  | taint_prop |
| consumer | 128 | 98 | 17534055 |  |  |  |  |  | taint_prop |
| consumer | 129 | 98 | 17534055 |  |  |  |  |  | taint_prop |
| consumer | 130 | 98 | 17534055 |  |  |  |  |  | taint_prop |
| consumer | 131 | 102 | 17536365 |  |  |  |  |  | taint_prop |
| consumer | 132 | 102 | 17536365 |  |  |  |  |  | taint_prop |
| consumer | 133 | 102 | 17536365 |  |  |  |  |  | taint_prop |
| consumer | 134 | 55 | 17538675 |  |  |  |  |  | taint_prop |
| consumer | 135 | 55 | 17538675 |  |  |  |  |  | taint_prop |
| consumer | 136 | 55 | 17538675 |  |  |  |  |  | taint_prop |
| consumer | 137 | 104 | 17540985 |  |  |  |  |  | taint_prop |
| consumer | 138 | 104 | 17540985 |  |  |  |  |  | taint_prop |
| consumer | 139 | 104 | 17540985 |  |  |  |  |  | taint_prop |
| chain_end | 140 | 139 | 20430025 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=491ae8 pa=
- L2 `lsq_sendfrag`：va=491ae8 pa=
- L2 `tlb_translate`：va=491ae8 pa=
- L3 `resp`：va=77ae8 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`SDC`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=140。
- 事件数：本 seed 流共 140 条，其中 fault_id=1 链 140 条；最后一条为 `chain_end`（event_id=140, tick=20430025）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s3/A04-F0-W0/seed3/prop_evt.txt.gz` | `a1edee42b88f121f08afc3855b3eb901473efc41bd2e1ccb2ce1202906d6fefa` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s3/A04-F0-W0/seed3/stats.txt` | `78a01c531d4a2ffef0543e6b9e201ae12593edb9a8b830409b5010ed771a9fae` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s3/A04-F0-W0/seed3/run.out` | `622d6d41f27dabedeab4e7e52cf4ac771b1feec391b02fc524bc9eec5cb5fb95` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s3/A04-F0-W0/seed3/run.err` | `6a37888cc97b5c9a4f5f9a2b8b139c7727e622cdd19640036d76440d3b90ad34` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s3/A04-F0-W0/chain_report.json` | `d9775c8e25109acce26702494d7d55399c11d67e63ea9bb3009bab7cfbc93cbc` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s3/manifest.json` | `d144d375dd435d374fa9e3dec4572e02e88126786e1b1908f5f77df6a91c1235` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

