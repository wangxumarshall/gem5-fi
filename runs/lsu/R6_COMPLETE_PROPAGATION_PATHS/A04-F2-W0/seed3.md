# A04-F2-W0 seed3 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A04-F2-W0` |
| 模型 | A04（AGU 对象/同页替换） |
| 频率档 | F2 |
| 负载 | W0 |
| seed | 3（sample_run_id=s3） |
| 子模型/注入参数 | Tick: 409159135, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x491ae0, new_addr=0x491ae8, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=data, object_base=0x4919a0, object_size=512, source_offset=320, target_offset=328 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046` |
| 源码 HEAD | `167a23ee59b3a2383cdd1eaeeca418b263666a56` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s3 --cells A04-F2-W0 --phase trial --seed-start 3 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 1200` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=409159135，request_id=，corr=origin，注入前地址 `before=491ae0`，注入后地址 `after=491ae8`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 409159135, Site: lsq_pushRequest_PRE, mode=a04_same_object, old_addr=0x491ae0, new_addr=0x491ae8, old_size=8, new_size=8, faults_injected: 1, isLoad=1, isStore=0, fault_field=addr, be_len=8, be_ones=8, be_subst=0, submodel=a04a, old_be=0xff, new_be=0xff, object_id=data, object_base=0x4919a0, object_size=512, source_offset=320, target_offset=328
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`491ae0` → `491ae8`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0xff`
- `submodel` = `a04a`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → lq_read → resp → lq_complete → taint_reg → errant_commit → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → consumer → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，lq_read=L3，resp=L3，lq_complete=L3，taint_reg=L4，errant_commit=L5，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，consumer=?，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 409159135 |  | 491ae0 |  |  |  | origin |
| addr_form | 2 | 1 | 409159135 |  | 491ae8 |  |  |  | origin |
| lsq_push | 3 | 2 | 409159135 |  | 491ae8 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 409159135 | 1302173 | 491ae8 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 409159135 | 1302173 | 491ae8 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 409159135 | 1302173 | 491ae8 |  |  |  | seq_primary |
| lq_read | 7 | 6 | 409159135 | 1302173 | 491ae8 |  |  |  | seq_primary |
| resp | 8 | 7 | 409159905 | 1302173 | 77ae8 |  |  |  | seq_primary |
| lq_complete | 9 | 8 | 409159905 | 1302173 | 491ae8 | 77ae8 |  |  | seq_primary |
| taint_reg | 10 | 9 | 409159905 | 1302173 | 77ae8 |  |  |  | seq_primary |
| errant_commit | 11 | 10 | 409167605 |  |  |  | L5 | errant_commit | taint_prop |
| consumer | 12 | 10 | 409167990 |  |  |  |  |  | taint_prop |
| consumer | 13 | 12 | 409169145 |  |  |  |  |  | taint_prop |
| consumer | 14 | 13 | 409169530 |  |  |  |  |  | taint_prop |
| consumer | 15 | 14 | 409170685 |  |  |  |  |  | taint_prop |
| consumer | 16 | 15 | 409171070 |  |  |  |  |  | taint_prop |
| consumer | 17 | 16 | 409172225 |  |  |  |  |  | taint_prop |
| consumer | 18 | 17 | 409172610 |  |  |  |  |  | taint_prop |
| consumer | 19 | 18 | 409173765 |  |  |  |  |  | taint_prop |
| consumer | 20 | 19 | 409174150 |  |  |  |  |  | taint_prop |
| consumer | 21 | 20 | 409175305 |  |  |  |  |  | taint_prop |
| consumer | 22 | 21 | 409175690 |  |  |  |  |  | taint_prop |
| consumer | 23 | 22 | 409176845 |  |  |  |  |  | taint_prop |
| consumer | 24 | 23 | 409177230 |  |  |  |  |  | taint_prop |
| consumer | 25 | 24 | 409178385 |  |  |  |  |  | taint_prop |
| consumer | 26 | 25 | 409178770 |  |  |  |  |  | taint_prop |
| consumer | 27 | 26 | 409179925 |  |  |  |  |  | taint_prop |
| consumer | 28 | 27 | 409180310 |  |  |  |  |  | taint_prop |
| consumer | 29 | 28 | 409181465 |  |  |  |  |  | taint_prop |
| consumer | 30 | 29 | 409181850 |  |  |  |  |  | taint_prop |
| consumer | 31 | 30 | 409183005 |  |  |  |  |  | taint_prop |
| consumer | 32 | 31 | 409183390 |  |  |  |  |  | taint_prop |
| consumer | 33 | 32 | 409184545 |  |  |  |  |  | taint_prop |
| consumer | 34 | 33 | 409184930 |  |  |  |  |  | taint_prop |
| consumer | 35 | 34 | 409186085 |  |  |  |  |  | taint_prop |
| consumer | 36 | 35 | 409186470 |  |  |  |  |  | taint_prop |
| consumer | 37 | 36 | 409187625 |  |  |  |  |  | taint_prop |
| consumer | 38 | 37 | 409188010 |  |  |  |  |  | taint_prop |
| consumer | 39 | 38 | 409189165 |  |  |  |  |  | taint_prop |
| consumer | 40 | 39 | 409189550 |  |  |  |  |  | taint_prop |
| consumer | 41 | 40 | 409190705 |  |  |  |  |  | taint_prop |
| consumer | 42 | 41 | 409191090 |  |  |  |  |  | taint_prop |
| consumer | 43 | 42 | 409192245 |  |  |  |  |  | taint_prop |
| consumer | 44 | 43 | 409192630 |  |  |  |  |  | taint_prop |
| consumer | 45 | 44 | 409193785 |  |  |  |  |  | taint_prop |
| consumer | 46 | 45 | 409194170 |  |  |  |  |  | taint_prop |
| consumer | 47 | 46 | 409195325 |  |  |  |  |  | taint_prop |
| consumer | 48 | 47 | 409195710 |  |  |  |  |  | taint_prop |
| consumer | 49 | 48 | 409196865 |  |  |  |  |  | taint_prop |
| consumer | 50 | 49 | 409197250 |  |  |  |  |  | taint_prop |
| consumer | 51 | 50 | 409198405 |  |  |  |  |  | taint_prop |
| consumer | 52 | 51 | 409198790 |  |  |  |  |  | taint_prop |
| consumer | 53 | 52 | 409199945 |  |  |  |  |  | taint_prop |
| consumer | 54 | 53 | 409200330 |  |  |  |  |  | taint_prop |
| consumer | 55 | 54 | 409201485 |  |  |  |  |  | taint_prop |
| consumer | 56 | 55 | 409201870 |  |  |  |  |  | taint_prop |
| consumer | 57 | 13 | 409203410 |  |  |  |  |  | taint_prop |
| consumer | 58 | 15 | 409435950 |  |  |  |  |  | taint_prop |
| consumer | 59 | 44 | 409437875 |  |  |  |  |  | taint_prop |
| consumer | 60 | 47 | 409439800 |  |  |  |  |  | taint_prop |
| consumer | 61 | 60 | 409440955 |  |  |  |  |  | taint_prop |
| consumer | 62 | 50 | 409443650 |  |  |  |  |  | taint_prop |
| consumer | 63 | 53 | 409445575 |  |  |  |  |  | taint_prop |
| consumer | 64 | 63 | 409446730 |  |  |  |  |  | taint_prop |
| consumer | 65 | 56 | 409448655 |  |  |  |  |  | taint_prop |
| consumer | 66 | 24 | 409456355 |  |  |  |  |  | taint_prop |
| consumer | 67 | 26 | 409458280 |  |  |  |  |  | taint_prop |
| consumer | 68 | 28 | 409460205 |  |  |  |  |  | taint_prop |
| consumer | 69 | 68 | 409460975 |  |  |  |  |  | taint_prop |
| consumer | 70 | 69 | 409462130 |  |  |  |  |  | taint_prop |
| consumer | 71 | 70 | 409462900 |  |  |  |  |  | taint_prop |
| consumer | 72 | 71 | 409464055 |  |  |  |  |  | taint_prop |
| consumer | 73 | 72 | 409464825 |  |  |  |  |  | taint_prop |
| consumer | 74 | 73 | 409465980 |  |  |  |  |  | taint_prop |
| consumer | 75 | 74 | 409466750 |  |  |  |  |  | taint_prop |
| consumer | 76 | 42 | 409470600 |  |  |  |  |  | taint_prop |
| consumer | 77 | 76 | 409471755 |  |  |  |  |  | taint_prop |
| consumer | 78 | 77 | 409472525 |  |  |  |  |  | taint_prop |
| consumer | 79 | 16 | 409476375 |  |  |  |  |  | taint_prop |
| consumer | 80 | 79 | 409477530 |  |  |  |  |  | taint_prop |
| consumer | 81 | 80 | 409478300 |  |  |  |  |  | taint_prop |
| consumer | 82 | 13 | 409483305 |  |  |  |  |  | taint_prop |
| consumer | 83 | 82 | 409484075 |  |  |  |  |  | taint_prop |
| consumer | 84 | 83 | 409485230 |  |  |  |  |  | taint_prop |
| consumer | 85 | 84 | 409486000 |  |  |  |  |  | taint_prop |
| consumer | 86 | 85 | 409487155 |  |  |  |  |  | taint_prop |
| consumer | 87 | 86 | 409487925 |  |  |  |  |  | taint_prop |
| consumer | 88 | 23 | 409489850 |  |  |  |  |  | taint_prop |
| consumer | 89 | 25 | 409491775 |  |  |  |  |  | taint_prop |
| consumer | 90 | 27 | 409493700 |  |  |  |  |  | taint_prop |
| consumer | 91 | 30 | 409495625 |  |  |  |  |  | taint_prop |
| consumer | 92 | 37 | 409500630 |  |  |  |  |  | taint_prop |
| consumer | 93 | 39 | 409502555 |  |  |  |  |  | taint_prop |
| consumer | 94 | 93 | 409503325 |  |  |  |  |  | taint_prop |
| consumer | 95 | 47 | 409508330 |  |  |  |  |  | taint_prop |
| consumer | 96 | 53 | 409514105 |  |  |  |  |  | taint_prop |
| consumer | 97 | 18 | 409519880 |  |  |  |  |  | taint_prop |
| consumer | 98 | 20 | 409521805 |  |  |  |  |  | taint_prop |
| consumer | 99 | 22 | 409523730 |  |  |  |  |  | taint_prop |
| consumer | 100 | 66 | 409525655 |  |  |  |  |  | taint_prop |
| consumer | 101 | 14 | 409666565 |  |  |  |  |  | taint_prop |
| consumer | 102 | 73 | 410055030 |  |  |  |  |  | taint_prop |
| consumer | 103 | 41 | 410057725 |  |  |  |  |  | taint_prop |
| consumer | 104 | 77 | 410061575 |  |  |  |  |  | taint_prop |
| consumer | 105 | 42 | 410086600 |  |  |  |  |  | taint_prop |
| consumer | 106 | 35 | 410111625 |  |  |  |  |  | taint_prop |
| consumer | 107 | 106 | 410112780 |  |  |  |  |  | taint_prop |
| consumer | 108 | 107 | 410113550 |  |  |  |  |  | taint_prop |
| chain_end | 109 | 108 | 488009060 |  |  |  | L5 | errant_commit_seen | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=491ae8 pa=
- L2 `lsq_sendfrag`：va=491ae8 pa=
- L2 `tlb_translate`：va=491ae8 pa=
- L3 `resp`：va=77ae8 pa=（响应回到 LSQ）
- L3 `lq_complete`：state=
- L4 `taint_reg`：clean → tainted

## 7. 最终结局

- oracle：`Masked`；chain terminal：`full`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=109。
- 事件数：本 seed 流共 109 条，其中 fault_id=1 链 109 条；最后一条为 `chain_end`（event_id=109, tick=488009060）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局见证事件（本 seed 自己的流）：kind=`chain_end`，event_id=109，parent_event_id=108，tick=488009060，detection_layer=L5，outcome=errant_commit_seen，contained=1，corr=none。
该事件带真实 detection_layer/outcome/contained/corr，且其 parent 前缀由同一 fault 链逐级可证（见上表）；门禁据此接受为 `full`——它不是 `chain_end` 推断，也不是 oracle 推断。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s3/A04-F2-W0/seed3/prop_evt.txt.gz` | `2881f25f24aa7218496e2f6dfd535c9054cbb5a7d25c8239ef8b10581694c930` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s3/A04-F2-W0/seed3/stats.txt` | `e3a58442e81475f5fe16b12a127261b31e865230dffe8b9fb7ac3813b5c811f7` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s3/A04-F2-W0/seed3/run.out` | `257f75de64a53466758a6f723f418e40dbee2e4faff9289677efa8de7408c584` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s3/A04-F2-W0/seed3/run.err` | `00cfdbd7e5c6bed454738d0a109ea8335c4cf6c681f79e6d16a10f6cfaa16357` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s3/A04-F2-W0/chain_report.json` | `58fa23a0b4997967728f2efae3c257dff7135c409acb1e7c3a47307b6a4a1cff` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a4_A04-F2-W0_s3/manifest.json` | `6ce4c6d6b8e40d961d00249b501908ed8dbcd32b485e4a93fc4cb5424093c2d1` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

