# A04-F0-W0 seed1 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F0-W0` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F0 |
| 负载 | W0 |
| seed | 1（sample_run_id=s1） |
| 子模型/注入参数 | Tick: 15691060, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x491b90, new_addr=0x491b28, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=data, object_base=0x4919a0, object_size=512, source_offset=496, target_offset=392 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s1 --cells A04-F0-W0 --phase trial --seed-start 1 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=15691060，request_id=，corr=origin，注入前地址 `before=491b90`，注入后地址 `after=491b28`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 15691060, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x491b90, new_addr=0x491b28, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=data, object_base=0x4919a0, object_size=512, source_offset=496, target_offset=392
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`491b90` → `491b28`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a04a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 15691060 |  | 491b90 |  |  |  | origin |
| addr_form | 2 | 1 | 15691060 |  | 491b28 |  |  |  | origin |
| lsq_push | 3 | 2 | 15691060 |  | 491b28 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 15691060 | 13219 | 491b28 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 15691060 | 13219 | 491b28 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 15691060 | 13219 | 491b28 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 15691060 | 13219 | 491b28 |  |  |  | seq_primary |
| resp | 8 | 7 | 15691830 | 13219 | 77b28 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 15691830 | 13219 | 491b28 | 77b28 |  |  | seq_primary |
| taint_reg | 10 | 9 | 15691830 | 13219 | 77b28 |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 15699530 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 15699915 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 15701070 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 15701455 |  |  |  |  |  | taint_prop |
| consumer | 15 | 14 | 15702610 |  |  |  |  |  | taint_prop |
| consumer | 16 | 15 | 16194640 |  |  |  |  |  | taint_prop |
| consumer | 17 | 16 | 16195795 |  |  |  |  |  | taint_prop |
| consumer | 18 | 17 | 16199645 |  |  |  |  |  | taint_prop |
| consumer | 19 | 18 | 16200800 |  |  |  |  |  | taint_prop |
| consumer | 20 | 19 | 16204650 |  |  |  |  |  | taint_prop |
| consumer | 21 | 20 | 16205805 |  |  |  |  |  | taint_prop |
| consumer | 22 | 21 | 16209655 |  |  |  |  |  | taint_prop |
| consumer | 23 | 22 | 16210810 |  |  |  |  |  | taint_prop |
| consumer | 24 | 23 | 16214660 |  |  |  |  |  | taint_prop |
| consumer | 25 | 24 | 16215815 |  |  |  |  |  | taint_prop |
| consumer | 26 | 25 | 16219665 |  |  |  |  |  | taint_prop |
| consumer | 27 | 26 | 16220820 |  |  |  |  |  | taint_prop |
| consumer | 28 | 27 | 16224670 |  |  |  |  |  | taint_prop |
| consumer | 29 | 28 | 16225825 |  |  |  |  |  | taint_prop |
| consumer | 30 | 15 | 16230830 |  |  |  |  |  | taint_prop |
| consumer | 31 | 30 | 16234680 |  |  |  |  |  | taint_prop |
| consumer | 32 | 31 | 16235835 |  |  |  |  |  | taint_prop |
| consumer | 33 | 32 | 16239685 |  |  |  |  |  | taint_prop |
| consumer | 34 | 33 | 16240840 |  |  |  |  |  | taint_prop |
| consumer | 35 | 34 | 16244690 |  |  |  |  |  | taint_prop |
| consumer | 36 | 35 | 16245845 |  |  |  |  |  | taint_prop |
| consumer | 37 | 36 | 16249695 |  |  |  |  |  | taint_prop |
| consumer | 38 | 37 | 16250850 |  |  |  |  |  | taint_prop |
| consumer | 39 | 38 | 16254700 |  |  |  |  |  | taint_prop |
| consumer | 40 | 39 | 16255855 |  |  |  |  |  | taint_prop |
| consumer | 41 | 40 | 16259705 |  |  |  |  |  | taint_prop |
| consumer | 42 | 41 | 16260860 |  |  |  |  |  | taint_prop |
| consumer | 43 | 42 | 16264710 |  |  |  |  |  | taint_prop |
| consumer | 44 | 43 | 16265865 |  |  |  |  |  | taint_prop |
| consumer | 45 | 44 | 16269715 |  |  |  |  |  | taint_prop |
| consumer | 46 | 45 | 16270870 |  |  |  |  |  | taint_prop |
| consumer | 47 | 46 | 16274720 |  |  |  |  |  | taint_prop |
| consumer | 48 | 13 | 16276645 |  |  |  |  |  | taint_prop |
| consumer | 49 | 48 | 16277800 |  |  |  |  |  | taint_prop |
| consumer | 50 | 49 | 16278570 |  |  |  |  |  | taint_prop |
| consumer | 51 | 50 | 16279725 |  |  |  |  |  | taint_prop |
| consumer | 52 | 51 | 16280495 |  |  |  |  |  | taint_prop |
| consumer | 53 | 52 | 16281650 |  |  |  |  |  | taint_prop |
| consumer | 54 | 29 | 16284345 |  |  |  |  |  | taint_prop |
| consumer | 55 | 30 | 16287425 |  |  |  |  |  | taint_prop |
| consumer | 56 | 31 | 16289350 |  |  |  |  |  | taint_prop |
| consumer | 57 | 56 | 16290120 |  |  |  |  |  | taint_prop |
| consumer | 58 | 57 | 16291275 |  |  |  |  |  | taint_prop |
| consumer | 59 | 58 | 16292045 |  |  |  |  |  | taint_prop |
| consumer | 60 | 59 | 16293200 |  |  |  |  |  | taint_prop |
| consumer | 61 | 60 | 16293970 |  |  |  |  |  | taint_prop |
| consumer | 62 | 61 | 16295125 |  |  |  |  |  | taint_prop |
| consumer | 63 | 62 | 16295895 |  |  |  |  |  | taint_prop |
| consumer | 64 | 38 | 16297820 |  |  |  |  |  | taint_prop |
| consumer | 65 | 40 | 16300900 |  |  |  |  |  | taint_prop |
| consumer | 66 | 20 | 16303595 |  |  |  |  |  | taint_prop |
| consumer | 67 | 66 | 16304750 |  |  |  |  |  | taint_prop |
| consumer | 68 | 19 | 16307445 |  |  |  |  |  | taint_prop |
| consumer | 69 | 21 | 16309370 |  |  |  |  |  | taint_prop |
| consumer | 70 | 23 | 16311295 |  |  |  |  |  | taint_prop |
| consumer | 71 | 24 | 16313220 |  |  |  |  |  | taint_prop |
| consumer | 72 | 71 | 16314375 |  |  |  |  |  | taint_prop |
| consumer | 73 | 27 | 16316300 |  |  |  |  |  | taint_prop |
| consumer | 74 | 28 | 16318225 |  |  |  |  |  | taint_prop |
| consumer | 75 | 74 | 16318995 |  |  |  |  |  | taint_prop |
| consumer | 76 | 75 | 16320150 |  |  |  |  |  | taint_prop |
| consumer | 77 | 76 | 16320920 |  |  |  |  |  | taint_prop |
| consumer | 78 | 77 | 16322075 |  |  |  |  |  | taint_prop |
| consumer | 79 | 78 | 16322845 |  |  |  |  |  | taint_prop |
| consumer | 80 | 32 | 16324770 |  |  |  |  |  | taint_prop |
| consumer | 81 | 33 | 16326695 |  |  |  |  |  | taint_prop |
| consumer | 82 | 81 | 16327850 |  |  |  |  |  | taint_prop |
| consumer | 83 | 36 | 16329775 |  |  |  |  |  | taint_prop |
| consumer | 84 | 37 | 16331700 |  |  |  |  |  | taint_prop |
| consumer | 85 | 84 | 16332470 |  |  |  |  |  | taint_prop |
| consumer | 86 | 85 | 16333625 |  |  |  |  |  | taint_prop |
| consumer | 87 | 18 | 16335550 |  |  |  |  |  | taint_prop |
| consumer | 88 | 87 | 16336320 |  |  |  |  |  | taint_prop |
| consumer | 89 | 43 | 16340170 |  |  |  |  |  | taint_prop |
| consumer | 90 | 89 | 16341325 |  |  |  |  |  | taint_prop |
| consumer | 91 | 46 | 16343250 |  |  |  |  |  | taint_prop |
| consumer | 92 | 13 | 16345175 |  |  |  |  |  | taint_prop |
| consumer | 93 | 53 | 16350950 |  |  |  |  |  | taint_prop |
| consumer | 94 | 15 | 16355185 |  |  |  |  |  | taint_prop |
| consumer | 95 | 55 | 16356725 |  |  |  |  |  | taint_prop |
| consumer | 96 | 56 | 16358650 |  |  |  |  |  | taint_prop |
| consumer | 97 | 62 | 16364425 |  |  |  |  |  | taint_prop |
| consumer | 98 | 85 | 16571555 |  |  |  |  |  | taint_prop |
| consumer | 99 | 95 | 16620065 |  |  |  |  |  | taint_prop |
| consumer | 100 | 88 | 16658950 |  |  |  |  |  | taint_prop |
| consumer | 101 | 98 | 16665110 |  |  |  |  |  | taint_prop |
| consumer | 102 | 62 | 17104395 |  |  |  |  |  | taint_prop |
| consumer | 103 | 60 | 17106320 |  |  |  |  |  | taint_prop |
| consumer | 104 | 103 | 17107090 |  |  |  |  |  | taint_prop |
| consumer | 105 | 103 | 17167150 |  |  |  |  |  | taint_prop |
| consumer | 106 | 88 | 17218740 |  |  |  |  |  | taint_prop |
| consumer | 107 | 16 | 17225285 |  |  |  |  |  | taint_prop |
| consumer | 108 | 48 | 17247615 |  |  |  |  |  | taint_prop |
| consumer | 109 | 94 | 17398920 |  |  |  |  |  | taint_prop |
| consumer | 110 | 76 | 17456285 |  |  |  |  |  | taint_prop |
| consumer | 111 | 97 | 17469375 |  |  |  |  |  | taint_prop |
| consumer | 112 | 18 | 17482465 |  |  |  |  |  | taint_prop |
| consumer | 113 | 18 | 17482465 |  |  |  |  |  | taint_prop |
| consumer | 114 | 23 | 17487470 |  |  |  |  |  | taint_prop |
| consumer | 115 | 100 | 17489010 |  |  |  |  |  | taint_prop |
| consumer | 116 | 29 | 17495555 |  |  |  |  |  | taint_prop |
| consumer | 117 | 29 | 17495555 |  |  |  |  |  | taint_prop |
| consumer | 118 | 29 | 17495555 |  |  |  |  |  | taint_prop |
| consumer | 119 | 83 | 17502100 |  |  |  |  |  | taint_prop |
| consumer | 120 | 83 | 17502100 |  |  |  |  |  | taint_prop |
| consumer | 121 | 83 | 17502100 |  |  |  |  |  | taint_prop |
| consumer | 122 | 20 | 17508645 |  |  |  |  |  | taint_prop |
| consumer | 123 | 20 | 17508645 |  |  |  |  |  | taint_prop |
| consumer | 124 | 20 | 17508645 |  |  |  |  |  | taint_prop |
| consumer | 125 | 58 | 17520965 |  |  |  |  |  | taint_prop |
| consumer | 126 | 58 | 17520965 |  |  |  |  |  | taint_prop |
| consumer | 127 | 58 | 17520965 |  |  |  |  |  | taint_prop |
| consumer | 128 | 59 | 17527510 |  |  |  |  |  | taint_prop |
| consumer | 129 | 59 | 17527510 |  |  |  |  |  | taint_prop |
| consumer | 130 | 59 | 17527510 |  |  |  |  |  | taint_prop |
| consumer | 131 | 63 | 17534055 |  |  |  |  |  | taint_prop |
| consumer | 132 | 63 | 17534055 |  |  |  |  |  | taint_prop |
| consumer | 133 | 63 | 17534055 |  |  |  |  |  | taint_prop |
| consumer | 134 | 48 | 17536365 |  |  |  |  |  | taint_prop |
| consumer | 135 | 48 | 17536365 |  |  |  |  |  | taint_prop |
| consumer | 136 | 48 | 17536365 |  |  |  |  |  | taint_prop |
| consumer | 137 | 32 | 17538675 |  |  |  |  |  | taint_prop |
| consumer | 138 | 32 | 17538675 |  |  |  |  |  | taint_prop |
| consumer | 139 | 32 | 17538675 |  |  |  |  |  | taint_prop |
| consumer | 140 | 78 | 17540985 |  |  |  |  |  | taint_prop |
| consumer | 141 | 78 | 17540985 |  |  |  |  |  | taint_prop |
| consumer | 142 | 78 | 17540985 |  |  |  |  |  | taint_prop |
| chain_end | 143 | 142 | 20430025 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=491b28 pa=
- L2 `lsq_sendfrag`：va=491b28 pa=
- L2 `tlb_translate`：va=491b28 pa=
- L3 `resp`：va=77b28 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`SDC`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=143。
- 事件数：本 seed 流共 143 条，其中 fault_id=1 链 143 条；最后一条为 `chain_end`（event_id=143, tick=20430025）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L5、outcome=errant_commit_seen、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `full`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s1/A04-F0-W0/seed1/prop_evt.txt.gz` | `fd30c4458e4aa4b35ea8bdd7a571c1391169807ae16812eda02c595b21d288bf` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s1/A04-F0-W0/seed1/stats.txt` | `7e7733d07fe05692bea5118e210895d13f6c7e390a1ff6eb0429778d0653a468` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s1/A04-F0-W0/seed1/run.out` | `2a47bc1695227d5968f79edcb89d8c552092996901cf315add548e2117a806ff` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s1/A04-F0-W0/seed1/run.err` | `6a37888cc97b5c9a4f5f9a2b8b139c7727e622cdd19640036d76440d3b90ad34` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s1/A04-F0-W0/chain_report.json` | `58185137a9a36100f15aea7fae35b2ab2570ef86d42538eb26487bf91649f5cc` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A04-F0-W0_s1/manifest.json` | `ca8bbd714e3e58df3858953bd8628b926b72433106cb34d0dd6e0f7dcdc84a6b` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

