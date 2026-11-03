# FSU-FP04-F0-W3 seed2 完整传播链

> 本文只使用本 seed（sample_run_id=`s2`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F0-W3` |
| 模型/子模型 | FP04 / FP04-d |
| 单元/频率/负载 | FSU Pipe / F0 / W3 |
| workload identity | W3-neon-fp32-lane-v1 |
| seed / sample_run_id | 2 / `s2` |
| selection seed / injection seed | 2 / 2 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel`（SHA-256 `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92`） |
| manifest | `runs/fsu/FSU-FP04-F0-W3/seed2/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `5647208d1fdf9ea131bcae60e0479fc5a0d477dce2fee0930bc8d04d40f47e73`） |
| 源码 HEAD | `36fc8e06073c13323e49cadba7c98aaadbd2c6f6` |
| 分析工具 SHA-256 | `e19d8bbf12f45d8857416a92332997f9e610534d13b0cb3b718bb5dc92a82a2c` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F0-W3/seed2/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F0 --fsu_load W3 --fsu_submodel FP04-d --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 2 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F0-W3/seed2/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F0 --fsu_load W3 --fsu_submodel FP04-d --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 2 --fpu_events_to_skip 14938 --chaos_propagation --prop_run_id FSU-FP04-F0-W3 --prop_sample_run_id s2 --fsu_eligible_total 16384` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 16384 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 1093924370 / 2841362 |
| sn / PC / opcode | 3075139 / 0x0000000000400694 / fmla |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 32@2 |
| precision / reg_class | fp32 / vec |
| field 范围（lane 内） | 31..31 |
| fault bit（绝对）/ bit_in_lane | 95 / 31 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x0000000080000000 / 0x00000000800000000000000000000000 |
| eligible ordinal / total | — / 16384 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 1093924370, Site: dyn_inst_execute, opClass=32, sn=3075139, bitseg=sign, precision=fp32, lane_width=32, lane_offset=2, mask=0x80000000, faults_injected: 1
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x3f455a3b → 0xbf455a3b |
| full 128-bit old/new | 0x3fecff983f455a3b3f801630bd7aaab9 → 0x3fecff98bf455a3b3f801630bd7aaab9 |
| old/new hash | 0x5a9bfc55000af442 → 0xb20d9193a7c025c2 |
| source/destination phys tag | src=— / dest=3 |
| operand role / lane / width | — / 2 / 32 |
| opClass / FU / FPCR / FPSR | fmla / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3f455a3b / 0xbf455a3b |
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
| 7 | chain_end | — | 6 | 5 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 1093924370 | 1 | 3075139 | 0x0000000000400694 | fmla | —/— | 3 | — | 32@2 | 0x3f455a3b→0xbf455a3b | — | — | origin |
| carrier_state | 1 | 0 | 1093924370 | 1 | 3075139 | 0x0000000000400694 | fmla | —/— | 3 | — | 32@2 | 0x3f455a3b→0xbf455a3b | — | — | fsu_taint |
| operand_read | 2 | 1 | 1093930530 | 1 | 3075163 | 0x0000000000400694 | fmla | 3075139/3075163 | 3 | 4 | 32@2 | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 1093930530 | 1 | 3075163 | 0x0000000000400694 | fmla | 3075139/3075163 | 3 | 4 | 32@2 | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 1093930530 | 1 | 3075163 | 0x0000000000400694 | fmla | 3075139/3075163 | 3 | 4 | 32@2 | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 1093931300 | 1 | 3075163 | 0x0000000000400694 | fmla | —/3075163 | — | — | 32@2 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 2053425990 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH cb66197d92c7656b9359b312e93180eaaf3c1e774d9264d7146fa1635439a8ae != golden cb66197d92c7656b9359b312e93180eaaf3c1e774d9264d7d0b595189bce8c2e — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 16384 / 1

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 5 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_applied) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `2` (operand_read)；child.parent=1 ✓
- `2` (operand_read) → `3` (execute)；child.parent=2 ✓
- `3` (execute) → `4` (prf_writeback)；child.parent=3 ✓
- `4` (prf_writeback) → `5` (commit)；child.parent=4 ✓
- `5` (commit) → `6` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `8808e7ecd8112b81857903d45bb386b077a2e023af399f6b97a9405dde68ced0` |
| `run.out` | `7389666ab9a7fb328bb4d2f5c7d4b011b88e77216c2523e91ab1e8c57133d64d` |
| `run.err` | `3b94bc39600d81ebe273ced2f04543d363c1f8965959df54c0ee05789173dbaf` |
| `stats.txt` | `b47a321e0a19209856d6336e7d0ee0ea86eb6748b303072bcadce974bd960bb1` |
| `oracle.json` | `4b12b1863be506e2f3740edc149e7fe944d3b52373a911079d552e83134fd960` |
| `chain_report.json` | `9b967be56276460814bcce1f7f7666ba5b0f807c2dd1217381ac298b222432a0` |
| `census/fpu_injections.log` | `d00d38340db51de7c1c6fb62f1bb636a1d50ee3b76ed17e3e40a2db17bb3130f` |
| `inject/fpu_injections.log` | `5ddcf8cca58a338d14ca3d26dd7442016fe8621eb463be5757dbf70e3885a9ad` |
| `inject/prop_evt.txt.gz` | `b87a881711f3f6f0250370d2f31019717aaa481518320fc59ebdb77a31b67202` |
| `inject/stats.txt` | `b47a321e0a19209856d6336e7d0ee0ea86eb6748b303072bcadce974bd960bb1` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `5647208d1fdf9ea131bcae60e0479fc5a0d477dce2fee0930bc8d04d40f47e73` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel` | `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
