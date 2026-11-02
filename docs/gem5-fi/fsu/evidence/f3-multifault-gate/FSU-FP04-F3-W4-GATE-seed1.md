# FSU-FP04-F3-W4-GATE seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F3-W4-GATE` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F3 / W4 |
| workload identity | N/A |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel`（SHA-256 `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97`） |
| manifest | `runs/fsu-gates/F3-multifault-gate-final/FSU-FP04-F3-W4-GATE/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `60b6c6f3646d5cb658b0db96c325e50e90361f47` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F3-multifault-gate-final/FSU-FP04-F3-W4-GATE/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F3-multifault-gate-final/FSU-FP04-F3-W4-GATE/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 4 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 4 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 11004,24122,34278,48713 --fpu_rate_warmup 0 --fsu_rate_divisor 10000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F3-W4-GATE --prop_sample_run_id s1 --fsu_eligible_total 57347` |
| rate（divisor/jitter/warmup） | 10000 / ±50% / 0 |
| eligible_total | 57347 |
| ordinals（index: ordinal） | 0:11004, 1:24122, 2:34278, 3:48713 |
| ordinals SHA-256 | `2e5b7546da9616a5d99b0160a483607bcf172bfd580ccd6ecb630b988f1ae122` |
| 注入数（actual/expected） | 4 / 4 |
| fault 数（事件流/injection log） | 4 / 4 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 29435945 / 76457 |
| sn / PC / opcode | 76922 / 0x00000000004005e8 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 11004 / 57347 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11004 / 0 |
| terminal | full |

### fault 2

| 字段 | 值 |
|---|---|
| 根 event_id | `6` |
| tick / cycle | 49079800 / 127480 |
| sn / PC / opcode | 155621 / 0x00000000004005f4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 24122 / 57347 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13118 / 1 |
| terminal | full |

### fault 3

| 字段 | 值 |
|---|---|
| 根 event_id | `12` |
| tick / cycle | 64271515 / 166939 |
| sn / PC / opcode | 216566 / 0x00000000004005e8 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 34278 / 57347 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10156 / 2 |
| terminal | full |

### fault 4

| 字段 | 值 |
|---|---|
| 根 event_id | `18` |
| tick / cycle | 85845760 / 222976 |
| sn / PC / opcode | 303180 / 0x00000000004005e0 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 48713 / 57347 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14435 / 3 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 29435945, Site: dyn_inst_execute, opClass=6, sn=76922, bitseg=mant_lo, mask=0x2000, faults_injected: 1
Tick: 49079800, Site: dyn_inst_execute, opClass=8, sn=155621, bitseg=mant_lo, mask=0x20, faults_injected: 2
Tick: 64271515, Site: dyn_inst_execute, opClass=6, sn=216566, bitseg=mant_lo, mask=0x1, faults_injected: 3
Tick: 85845760, Site: dyn_inst_execute, opClass=6, sn=303180, bitseg=mant_lo, mask=0x4000, faults_injected: 4
CHAOS_RATE_COMPLETE=4
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4075a00000000000 → 0x4075a00000002000 |
| old/new hash | 0xdde4bf7b9e69312e → 0xb1b970c7122a6d0e |
| source/destination phys tag | src=— / dest=32 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4075a00000000000 / 0x4075a00000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 2

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfda6e978d4fdf3b → 0xbfda6e978d4fdf1b |
| old/new hash | 0x545185dacf141d67 → 0xfadf618aeccae5c7 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfda6e978d4fdf3b / 0xbfda6e978d4fdf1b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 3

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4075300000000000 → 0x4075300000000001 |
| old/new hash | 0xbbf3af7e5fd341fe → 0xca5834769171064f |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4075300000000000 / 0x4075300000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 4

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088200000000000 → 0x4088200000004000 |
| old/new hash | 0x31003d7e110561fb → 0x859fa01285faf23b |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088200000000000 / 0x4088200000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

### fault 1（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 0 | — |
| 2 | carrier_state | L1 | 1 | 0 |
| 3 | operand_read | L2 | 2 | 1 |
| 4 | execute | L3 | 3 | 2 |
| 5 | prf_writeback | L4 | 4 | 3 |
| 6 | commit | L5 | 5 | 4 |
| 7 | chain_end | — | 24 | 5 |

### fault 2（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 6 | — |
| 2 | carrier_state | L1 | 7 | 6 |
| 3 | operand_read | L2 | 8 | 7 |
| 4 | execute | L3 | 9 | 8 |
| 5 | prf_writeback | L4 | 10 | 9 |
| 6 | commit | L5 | 11 | 10 |
| 7 | chain_end | — | 25 | 11 |

### fault 3（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 12 | — |
| 2 | carrier_state | L1 | 13 | 12 |
| 3 | operand_read | L2 | 14 | 13 |
| 4 | execute | L3 | 15 | 14 |
| 5 | prf_writeback | L4 | 16 | 15 |
| 6 | commit | L5 | 17 | 16 |
| 7 | chain_end | — | 26 | 17 |

### fault 4（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 18 | — |
| 2 | carrier_state | L1 | 19 | 18 |
| 3 | operand_read | L2 | 20 | 19 |
| 4 | execute | L3 | 21 | 20 |
| 5 | prf_writeback | L4 | 22 | 21 |
| 6 | commit | L5 | 23 | 22 |
| 7 | chain_end | — | 27 | 23 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 29435945 | 1 | 76922 | 0x00000000004005e8 | scvtf | —/— | 32 | — | 64@0 | 0x4075a00000000000→0x4075a00000002000 | — | — | origin |
| carrier_state | 1 | 0 | 29435945 | 1 | 76922 | 0x00000000004005e8 | scvtf | —/— | 32 | — | 64@0 | 0x4075a00000000000→0x4075a00000002000 | — | — | fsu_taint |
| operand_read | 2 | 1 | 29439795 | 1 | 76925 | 0x00000000004005f4 | fmadd | 76922/76925 | 32 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 29439795 | 1 | 76925 | 0x00000000004005f4 | fmadd | 76922/76925 | 32 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 29439795 | 1 | 76925 | 0x00000000004005f4 | fmadd | 76922/76925 | 32 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 29440565 | 1 | 76925 | 0x00000000004005f4 | fmadd | —/76925 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 24 | 5 | 232548855 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 6 | — | 49079800 | 2 | 155621 | 0x00000000004005f4 | fmadd | —/— | 45 | — | 64@0 | 0xbfda6e978d4fdf3b→0xbfda6e978d4fdf1b | — | — | origin |
| carrier_state | 7 | 6 | 49079800 | 2 | 155621 | 0x00000000004005f4 | fmadd | —/— | 45 | — | 64@0 | 0xbfda6e978d4fdf3b→0xbfda6e978d4fdf1b | — | — | fsu_taint |
| operand_read | 8 | 7 | 49095200 | 2 | 155691 | 0x00000000004005ec | fmadd | 155621/155691 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 49095200 | 2 | 155691 | 0x00000000004005ec | fmadd | 155621/155691 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 49095200 | 2 | 155691 | 0x00000000004005ec | fmadd | 155621/155691 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 49095970 | 2 | 155691 | 0x00000000004005ec | fmadd | —/155691 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 25 | 11 | 232548855 | 2 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 12 | — | 64271515 | 3 | 216566 | 0x00000000004005e8 | scvtf | —/— | 46 | — | 64@0 | 0x4075300000000000→0x4075300000000001 | — | — | origin |
| carrier_state | 13 | 12 | 64271515 | 3 | 216566 | 0x00000000004005e8 | scvtf | —/— | 46 | — | 64@0 | 0x4075300000000000→0x4075300000000001 | — | — | fsu_taint |
| operand_read | 14 | 13 | 64275365 | 3 | 216569 | 0x00000000004005f4 | fmadd | 216566/216569 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 15 | 14 | 64275365 | 3 | 216569 | 0x00000000004005f4 | fmadd | 216566/216569 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 16 | 15 | 64275365 | 3 | 216569 | 0x00000000004005f4 | fmadd | 216566/216569 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 17 | 16 | 64276135 | 3 | 216569 | 0x00000000004005f4 | fmadd | —/216569 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 26 | 17 | 232548855 | 3 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 18 | — | 85845760 | 4 | 303180 | 0x00000000004005e0 | scvtf | —/— | 46 | — | 64@0 | 0x4088200000000000→0x4088200000004000 | — | — | origin |
| carrier_state | 19 | 18 | 85845760 | 4 | 303180 | 0x00000000004005e0 | scvtf | —/— | 46 | — | 64@0 | 0x4088200000000000→0x4088200000004000 | — | — | fsu_taint |
| operand_read | 20 | 19 | 85847685 | 4 | 303183 | 0x00000000004005ec | fmadd | 303180/303183 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 21 | 20 | 85847685 | 4 | 303183 | 0x00000000004005ec | fmadd | 303180/303183 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 22 | 21 | 85847685 | 4 | 303183 | 0x00000000004005ec | fmadd | 303180/303183 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 23 | 22 | 85848455 | 4 | 303183 | 0x00000000004005ec | fmadd | —/303183 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 27 | 23 | 232548855 | 4 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

### fault 2

- **L0**：fault_applied#6（本 seed 真实事件）。
- **L1**：carrier_state#7（本 seed 真实事件）。
- **L2**：operand_read#8（本 seed 真实事件）。
- **L3**：execute#9（本 seed 真实事件）。
- **L4**：prf_writeback#10（本 seed 真实事件）。
- **L5**：commit#11（本 seed 真实事件）。

### fault 3

- **L0**：fault_applied#12（本 seed 真实事件）。
- **L1**：carrier_state#13（本 seed 真实事件）。
- **L2**：operand_read#14（本 seed 真实事件）。
- **L3**：execute#15（本 seed 真实事件）。
- **L4**：prf_writeback#16（本 seed 真实事件）。
- **L5**：commit#17（本 seed 真实事件）。

### fault 4

- **L0**：fault_applied#18（本 seed 真实事件）。
- **L1**：carrier_state#19（本 seed 真实事件）。
- **L2**：operand_read#20（本 seed 真实事件）。
- **L3**：execute#21（本 seed 真实事件）。
- **L4**：prf_writeback#22（本 seed 真实事件）。
- **L5**：commit#23（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH db3b3dfa483d3d93c47b30482674fb5165cdf7698590069bccd18dbd520b3fab != golden ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7 — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：4 / 4
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：28
- attempted / eligible / activated：4 / 57347 / 4

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 5 | N/A / N/A |
| 2 | full | L5 | True | True | [] | 11 | N/A / N/A |
| 3 | full | L5 | True | True | [] | 17 | N/A / N/A |
| 4 | full | L5 | True | True | [] | 23 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_applied) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `2` (operand_read)；child.parent=1 ✓
- `2` (operand_read) → `3` (execute)；child.parent=2 ✓
- `3` (execute) → `4` (prf_writeback)；child.parent=3 ✓
- `4` (prf_writeback) → `5` (commit)；child.parent=4 ✓
- `5` (commit) → `24` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

### fault 2

主链每一条边均验证为直接 parent：

- `6` (fault_applied) → `7` (carrier_state)；child.parent=6 ✓
- `7` (carrier_state) → `8` (operand_read)；child.parent=7 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `25` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

### fault 3

主链每一条边均验证为直接 parent：

- `12` (fault_applied) → `13` (carrier_state)；child.parent=12 ✓
- `13` (carrier_state) → `14` (operand_read)；child.parent=13 ✓
- `14` (operand_read) → `15` (execute)；child.parent=14 ✓
- `15` (execute) → `16` (prf_writeback)；child.parent=15 ✓
- `16` (prf_writeback) → `17` (commit)；child.parent=16 ✓
- `17` (commit) → `26` (chain_end)；child.parent=17 ✓

- L5 真实见证：`17` kind=commit outcome=errant_commit oracle_diff=—

### fault 4

主链每一条边均验证为直接 parent：

- `18` (fault_applied) → `19` (carrier_state)；child.parent=18 ✓
- `19` (carrier_state) → `20` (operand_read)；child.parent=19 ✓
- `20` (operand_read) → `21` (execute)；child.parent=20 ✓
- `21` (execute) → `22` (prf_writeback)；child.parent=21 ✓
- `22` (prf_writeback) → `23` (commit)；child.parent=22 ✓
- `23` (commit) → `27` (chain_end)；child.parent=23 ✓

- L5 真实见证：`23` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `c28e3768c5d5f48e54cbde15c2f090c788441cfaca1b2eaf8a259e8ca024d3d4` |
| `run.out` | `f0381346ac62cd0f57698ebcaf8603fc1dc025ea9b9c84166b69c9eedfedae0b` |
| `run.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `stats.txt` | `d5890184d75166599738e3763bb64cdf533b81e3d069152d2f4470ad0447eecf` |
| `oracle.json` | `c6a156b55f0b02f6445c5941a0b8a47c8b0ddcb8ff220831e4550a425c431c59` |
| `chain_report.json` | `57aabc59766cb1737cf16399aabea0a625f244072b072e0648fa5b9edcfc3e21` |
| `ordinals.json` | `2e5b7546da9616a5d99b0160a483607bcf172bfd580ccd6ecb630b988f1ae122` |
| `census/fpu_injections.log` | `7bc8726ba761e237b918a253b4aa17afe92f63b6fb33bcdbe3233ab77f314a00` |
| `inject/fpu_injections.log` | `fffbc5da680dd958176a126d744702d746737f376f95337677756d7ed94d915c` |
| `inject/prop_evt.txt.gz` | `80e855a72e6bcc52f8943c13212e872a64af3bba94a0967110674c0007332063` |
| `inject/stats.txt` | `d5890184d75166599738e3763bb64cdf533b81e3d069152d2f4470ad0447eecf` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel` | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 4 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
