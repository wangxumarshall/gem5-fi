# A04-F2-W0 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F2-W0` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F2 |
| 负载 | W0 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 176373120, Site: lsq_pushRequest_PRE, mode=a04_same_page, old_addr=0x491a78, new_addr=0x491a58, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04b, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s2 --cells A04-F2-W0 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=176373120，request_id=，corr=origin，注入前地址 `before=491a78`，注入后地址 `after=491a58`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 176373120, Site: lsq_pushRequest_PRE, mode=a04_same_page, old_addr=0x491a78, new_addr=0x491a58, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04b, old_be=0xff, new_be=0xff, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`491a78` → `491a58`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a04b`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 176373120 |  | 491a78 |  |  |  | origin |
| addr_form | 2 | 1 | 176373120 |  | 491a58 |  |  |  | origin |
| lsq_push | 3 | 2 | 176373120 |  | 491a58 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 176373120 | 538421 | 491a58 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 176373120 | 538421 | 491a58 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 176373120 | 538421 | 491a58 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 176373120 | 538421 | 491a58 |  |  |  | seq_primary |
| resp | 8 | 7 | 176373890 | 538421 | 77a58 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 176373890 | 538421 | 491a58 | 77a58 |  |  | seq_primary |
| taint_reg | 10 | 9 | 176373890 | 538421 | 77a58 |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 176374660 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 176375045 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 176376200 |  |  |  |  |  | taint_prop |
| consumer | 14 | 12 | 176376585 |  |  |  |  |  | taint_prop |
| consumer | 15 | 13 | 176376970 |  |  |  |  |  | taint_prop |
| consumer | 16 | 14 | 176376970 |  |  |  |  |  | taint_prop |
| consumer | 17 | 16 | 176378125 |  |  |  |  |  | taint_prop |
| consumer | 18 | 16 | 176378510 |  |  |  |  |  | taint_prop |
| consumer | 19 | 17 | 176378895 |  |  |  |  |  | taint_prop |
| consumer | 20 | 18 | 176378895 |  |  |  |  |  | taint_prop |
| consumer | 21 | 20 | 176380050 |  |  |  |  |  | taint_prop |
| consumer | 22 | 20 | 176380435 |  |  |  |  |  | taint_prop |
| consumer | 23 | 21 | 176380820 |  |  |  |  |  | taint_prop |
| consumer | 24 | 22 | 176380820 |  |  |  |  |  | taint_prop |
| consumer | 25 | 24 | 176381975 |  |  |  |  |  | taint_prop |
| consumer | 26 | 24 | 176382360 |  |  |  |  |  | taint_prop |
| consumer | 27 | 25 | 176382745 |  |  |  |  |  | taint_prop |
| consumer | 28 | 26 | 176382745 |  |  |  |  |  | taint_prop |
| consumer | 29 | 28 | 176383900 |  |  |  |  |  | taint_prop |
| consumer | 30 | 28 | 176384285 |  |  |  |  |  | taint_prop |
| consumer | 31 | 29 | 176384670 |  |  |  |  |  | taint_prop |
| consumer | 32 | 30 | 176384670 |  |  |  |  |  | taint_prop |
| consumer | 33 | 32 | 176385825 |  |  |  |  |  | taint_prop |
| consumer | 34 | 32 | 176386210 |  |  |  |  |  | taint_prop |
| consumer | 35 | 33 | 176386595 |  |  |  |  |  | taint_prop |
| consumer | 36 | 34 | 176386595 |  |  |  |  |  | taint_prop |
| consumer | 37 | 36 | 176387750 |  |  |  |  |  | taint_prop |
| consumer | 38 | 36 | 176388135 |  |  |  |  |  | taint_prop |
| consumer | 39 | 37 | 176388520 |  |  |  |  |  | taint_prop |
| consumer | 40 | 38 | 176388520 |  |  |  |  |  | taint_prop |
| consumer | 41 | 40 | 176389675 |  |  |  |  |  | taint_prop |
| consumer | 42 | 40 | 176390060 |  |  |  |  |  | taint_prop |
| consumer | 43 | 41 | 176390445 |  |  |  |  |  | taint_prop |
| consumer | 44 | 42 | 176390445 |  |  |  |  |  | taint_prop |
| consumer | 45 | 44 | 176391600 |  |  |  |  |  | taint_prop |
| consumer | 46 | 44 | 176391985 |  |  |  |  |  | taint_prop |
| consumer | 47 | 45 | 176392370 |  |  |  |  |  | taint_prop |
| consumer | 48 | 46 | 176392370 |  |  |  |  |  | taint_prop |
| consumer | 49 | 48 | 176393525 |  |  |  |  |  | taint_prop |
| consumer | 50 | 48 | 176393910 |  |  |  |  |  | taint_prop |
| consumer | 51 | 49 | 176394295 |  |  |  |  |  | taint_prop |
| consumer | 52 | 50 | 176394295 |  |  |  |  |  | taint_prop |
| consumer | 53 | 52 | 176395450 |  |  |  |  |  | taint_prop |
| consumer | 54 | 52 | 176395835 |  |  |  |  |  | taint_prop |
| consumer | 55 | 53 | 176396220 |  |  |  |  |  | taint_prop |
| consumer | 56 | 54 | 176396220 |  |  |  |  |  | taint_prop |
| consumer | 57 | 56 | 176397375 |  |  |  |  |  | taint_prop |
| consumer | 58 | 56 | 176397760 |  |  |  |  |  | taint_prop |
| consumer | 59 | 57 | 176398145 |  |  |  |  |  | taint_prop |
| consumer | 60 | 58 | 176398145 |  |  |  |  |  | taint_prop |
| consumer | 61 | 60 | 176399300 |  |  |  |  |  | taint_prop |
| consumer | 62 | 60 | 176399685 |  |  |  |  |  | taint_prop |
| consumer | 63 | 61 | 176400070 |  |  |  |  |  | taint_prop |
| consumer | 64 | 62 | 176400070 |  |  |  |  |  | taint_prop |
| consumer | 65 | 64 | 176401225 |  |  |  |  |  | taint_prop |
| consumer | 66 | 64 | 176401610 |  |  |  |  |  | taint_prop |
| consumer | 67 | 65 | 176401995 |  |  |  |  |  | taint_prop |
| consumer | 68 | 66 | 176401995 |  |  |  |  |  | taint_prop |
| consumer | 69 | 68 | 176403150 |  |  |  |  |  | taint_prop |
| consumer | 70 | 68 | 176403535 |  |  |  |  |  | taint_prop |
| consumer | 71 | 69 | 176403920 |  |  |  |  |  | taint_prop |
| consumer | 72 | 70 | 176403920 |  |  |  |  |  | taint_prop |
| consumer | 73 | 72 | 176405075 |  |  |  |  |  | taint_prop |
| consumer | 74 | 72 | 176405460 |  |  |  |  |  | taint_prop |
| consumer | 75 | 73 | 176405845 |  |  |  |  |  | taint_prop |
| consumer | 76 | 74 | 176405845 |  |  |  |  |  | taint_prop |
| consumer | 77 | 76 | 176407000 |  |  |  |  |  | taint_prop |
| consumer | 78 | 76 | 176407385 |  |  |  |  |  | taint_prop |
| consumer | 79 | 77 | 176407770 |  |  |  |  |  | taint_prop |
| consumer | 80 | 78 | 176407770 |  |  |  |  |  | taint_prop |
| consumer | 81 | 80 | 176408925 |  |  |  |  |  | taint_prop |
| consumer | 82 | 80 | 176409310 |  |  |  |  |  | taint_prop |
| consumer | 83 | 13 | 176410850 |  |  |  |  |  | taint_prop |
| consumer | 84 | 17 | 176412775 |  |  |  |  |  | taint_prop |
| consumer | 85 | 21 | 176414700 |  |  |  |  |  | taint_prop |
| consumer | 86 | 25 | 176416625 |  |  |  |  |  | taint_prop |
| consumer | 87 | 29 | 176418550 |  |  |  |  |  | taint_prop |
| consumer | 88 | 33 | 176420475 |  |  |  |  |  | taint_prop |
| consumer | 89 | 37 | 176422400 |  |  |  |  |  | taint_prop |
| consumer | 90 | 41 | 176424325 |  |  |  |  |  | taint_prop |
| consumer | 91 | 45 | 176426250 |  |  |  |  |  | taint_prop |
| consumer | 92 | 49 | 176428175 |  |  |  |  |  | taint_prop |
| consumer | 93 | 53 | 176430100 |  |  |  |  |  | taint_prop |
| consumer | 94 | 57 | 176432025 |  |  |  |  |  | taint_prop |
| consumer | 95 | 61 | 176433950 |  |  |  |  |  | taint_prop |
| consumer | 96 | 65 | 176435875 |  |  |  |  |  | taint_prop |
| consumer | 97 | 69 | 176437800 |  |  |  |  |  | taint_prop |
| consumer | 98 | 73 | 176439725 |  |  |  |  |  | taint_prop |
| consumer | 99 | 77 | 176441650 |  |  |  |  |  | taint_prop |
| consumer | 100 | 81 | 176443575 |  |  |  |  |  | taint_prop |
| consumer | 101 | 19 | 176576785 |  |  |  |  |  | taint_prop |
| consumer | 102 | 82 | 176979110 |  |  |  |  |  | taint_prop |
| consumer | 103 | 17 | 176981805 |  |  |  |  |  | taint_prop |
| consumer | 104 | 25 | 176985655 |  |  |  |  |  | taint_prop |
| consumer | 105 | 21 | 177010680 |  |  |  |  |  | taint_prop |
| consumer | 106 | 79 | 177035705 |  |  |  |  |  | taint_prop |
| consumer | 107 | 106 | 177036860 |  |  |  |  |  | taint_prop |
| consumer | 108 | 107 | 177037630 |  |  |  |  |  | taint_prop |
| chain_end | 109 | 108 | 286167420 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=491a58 pa=
- L2 `lsq_sendfrag`：va=491a58 pa=
- L2 `tlb_translate`：va=491a58 pa=
- L3 `resp`：va=77a58 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=109。
- 事件数：本 seed 流共 109 条，其中 fault_id=1 链 109 条；最后一条为 `chain_end`（event_id=109, tick=286167420）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s2/A04-F2-W0/seed2/prop_evt.txt.gz` | `872726b38664f5df2c1b42358ff8d17e7aa338c8a2b30626da59041d89a0fd3e` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s2/A04-F2-W0/seed2/stats.txt` | `3d6ffd74d29b325f06218129e4c238ef372ac4ceba8a0975f64975ce32914921` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s2/A04-F2-W0/seed2/run.out` | `82070e10348c5bd048f4c728ed3d9108b4b14f72d46b755d197de31d0e8a4782` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s2/A04-F2-W0/seed2/run.err` | `e6f78ab080a7d5ce5e2d0a89e18a125e11c5d554b13e1fedce85516303fc7db0` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s2/A04-F2-W0/chain_report.json` | `5864af0ea835c236be922423b882dcb6b7a836605998194ecd601bf9e3a683e1` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F2-W0_s2/manifest.json` | `063202aa92153e7973741bc503c711f7a9e16fed6a070410df4eec732f6b2f40` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

