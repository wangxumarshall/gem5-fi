# A06-F2-W3 seed2 — 完整传播路径（真实事件时间顺序）

## 1. 实验身份与子模型

| 项 | 值 |
|---|---|
| RunID | `A06-F2-W3` |
| 模型 | A06（AGU 访问尺寸/掩码） |
| 频率档 | F2 |
| 负载 | W3 |
| seed | 2（sample_run_id=s2） |
| 子模型/注入参数 | Tick: 318175550, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x4933a0, new_addr=0x4933a0, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=none, be_len=8, be_ones=8, be_subst=1, submodel=a06b, old_be=0xff, new_be=0x7f, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0 |
| 二进制 | `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt` |
| 二进制 SHA-256 | `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e` |
| 源码 HEAD | `ddc81a7b074d0dae2505dc85c8fec5aef6293f66` |
| 命令 | `LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt python3 tools/lsu_campaign.py --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W3_s2 --cells A06-F2-W3 --phase trial --seed-start 2 --max-seeds-per-cell 1 --max-parallel 1 --allow-blocked-models --timeout 300` |

## 2. 故障注入发生在哪里

第一次（也是本样本被选中的）注入事件：`event_id=1`，tick=318175550，request_id=，corr=origin，注入前地址 `before=4933a0`，注入后地址 `after=4933a0`。

注入器日志中该样本的注入行（真实原文，按日志顺序）：

```
Tick: 318175550, Site: lsq_pushRequest_PRE, mode=a06_size, old_addr=0x4933a0, new_addr=0x4933a0, old_size=8, new_size=8, faults_injected: 1, isLoad=0, isStore=1, fault_field=none, be_len=8, be_ones=8, be_subst=1, submodel=a06b, old_be=0xff, new_be=0x7f, object_id=, object_base=0x0, object_size=0, source_offset=0, target_offset=0
```

## 3. 注入前后的地址/操作数/大小/掩码/通道/状态变化

- 地址：`4933a0` → `4933a0`（来自 inj/addr_form 节点，本 seed 自己的值）。
- `old_size` = `8`
- `new_size` = `8`
- `old_be` = `0xff`
- `new_be` = `0x7f`
- `submodel` = `a06b`

## 4. 之后依次经过哪些真实部件

事件种类序列（本 seed，fault_id=1）：`inj → addr_form → lsq_push → mem_req → lsq_sendfrag → tlb_translate → sq_execute → sq_writeback → resp → taint_reg → sq_complete → store_not_retired → chain_end`。
按证据层映射：inj=L0，addr_form=L1，lsq_push=L1，mem_req=L2，lsq_sendfrag=L2，tlb_translate=L2，sq_execute=L3，sq_writeback=L3，resp=L3，taint_reg=L4，sq_complete=L3，store_not_retired=L4，chain_end=L5。

## 5. 每一步关键 event_id / parent_event_id / tick / request_id / corr

| kind | event_id | parent | tick | request_id | va | pa | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|
| inj | 1 |  | 318175550 |  | 4933a0 |  |  |  | origin |
| addr_form | 2 | 1 | 318175550 |  | 4933a0 |  |  |  | origin |
| lsq_push | 3 | 2 | 318175550 |  | 4933a0 |  |  |  | seq_primary |
| mem_req | 4 | 3 | 318175550 | 1408114 | 4933a0 |  |  |  | seq_primary |
| lsq_sendfrag | 5 | 4 | 318175550 | 1408114 | 4933a0 |  |  |  | seq_primary |
| tlb_translate | 6 | 5 | 318175550 | 1408114 | 4933a0 |  |  |  | seq_primary |
| sq_execute | 7 | 6 | 318175550 |  | 4933a0 |  |  |  | seq_primary |
| sq_writeback | 8 | 7 | 318177090 |  |  | 793a0 |  |  | seq_primary |
| resp | 9 | 8 | 318177860 | 1408114 | 793a0 |  |  |  | seq_primary |
| taint_reg | 10 | 9 | 318177860 | 1408114 | 793a0 |  |  |  | seq_primary |
| sq_complete | 11 | 10 | 318177860 |  | 4933a0 |  |  |  | seq_primary |
| store_not_retired | 12 | 11 | 381128440 | 1408114 |  |  | L4 | contained | taint_prop |
| chain_end | 13 | 12 | 381128440 |  |  |  | L4 | detected_contained | none |

## 6. 地址/数据/污点在每层如何变化

- L2 `mem_req`：va=4933a0 pa=
- L2 `lsq_sendfrag`：va=4933a0 pa=
- L2 `tlb_translate`：va=4933a0 pa=
- L3 `resp`：va=793a0 pa=（响应回到 LSQ）
- L4 `taint_reg`：clean → tainted
- L3 `sq_complete`：state=completed

## 7. 最终结局

- oracle：`Masked`；chain terminal：`detected_contained`；provable_to：`L5`；beyond：`—`。
- admitted=True，certified=True，violations=[]，truncated=False，evidence_truncated=False，事件数=13。
- 事件数：本 seed 流共 13 条，其中 fault_id=1 链 13 条；最后一条为 `chain_end`（event_id=13, tick=381128440）。

## 8. 为什么该结局成立

链边证明（本 seed 自己的 fault 1）：已证 `L0->L1`, `L1->L2`, `L2->L3`, `L3->L4`, `L4->L5`。
终局事件的 detection_layer=L4、outcome=detected_contained、corr=none，且该事件的 parent 前缀由 inj/addr_form 逐级可证（见上表），因此门禁接受为 `detected_contained`——它不是 `chain_end` 推断，而是链上真实检测/逃逸事件。

## 9. 原始证据位置与 SHA-256

| 证据 | 路径 | SHA-256 |
|---|---|---|
| prop_evt | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W3_s2/A06-F2-W3/seed2/prop_evt.txt.gz` | `b9a27d4e1944c92be7b50b80d7e3189851672380e4643a5d39f2c894a0c7deb5` |
| stats | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W3_s2/A06-F2-W3/seed2/stats.txt` | `8536c12a254212495ccfcf0befe98984d5d7ae724a82871e695418f32706e28d` |
| run.out | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W3_s2/A06-F2-W3/seed2/run.out` | `ac39faf1738085b0c390299ae1e95bc65f197df2edee61461e0920bd372daf77` |
| run.err | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W3_s2/A06-F2-W3/seed2/run.err` | `82790b1e6fc9fb5cadb88f2ebcce5f73fa48a90b613ea160375cbfe7991ef2b9` |
| chain_report | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W3_s2/A06-F2-W3/chain_report.json` | `4822751da091b699467a3f8ae11ddcdf0053ad877fdc21b4bb1fa34887d9cd02` |
| manifest | `/home/sdc/gem5-fi-ding/runs/lsu/r6_a_r6a3_A06-F2-W3_s2/manifest.json` | `d1ebb1331011fb51089598d42f8830e4dd7e15523088dbffd218cb87a195dde1` |

## 10. 诚实边界

- 本文所有数值均来自本 seed 自己的证据文件；没有跨 seed 取值、没有模板替代路径。

