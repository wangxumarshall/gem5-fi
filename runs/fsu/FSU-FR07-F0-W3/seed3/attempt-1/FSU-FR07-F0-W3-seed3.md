# FSU-FR07-F0-W3 seed3 完整传播链

> 本文只使用本 seed（sample_run_id=`s3`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FR07-F0-W3` |
| 模型/子模型 | FR07 / FR07-d |
| 单元/频率/负载 | FSU Pipe / F0 / W3 |
| workload identity | W3-neon-fp32-lane-v1 |
| seed / sample_run_id | 3 / `s3` |
| selection seed / injection seed | 3 / 3 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel`（SHA-256 `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92`） |
| manifest | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR07-F0-W3/seed3/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `b494ad64badc406343ff1f6c7d7a397cb9bf97f166eefb5753d825b1033c74ca`） |
| 源码 HEAD | `aac1750e704f8eb1a626be25fb06beb318b49399` |
| 分析工具 SHA-256 | `0a10a67b6bac15dc997b22c640c9db8a06f78a015f4e1a9144201d01d1c92785` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR07-F0-W3/seed3/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 8355840 --fpu_rng_seed 3 --fsu_model FR07 --fsu_freq F0 --fsu_load W3 --fsu_submodel FR07-d --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 2 --fpu_decode_guard --fpu_op_classes SimdFloatAdd,SimdFloatMult,SimdFloatMultAcc,SimdFloatDiv,SimdFloatSqrt --fpu_reg_class vec --fpu_prf_wb_hook --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR07-F0-W3/seed3/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 8355840 --fpu_rng_seed 3 --fsu_model FR07 --fsu_freq F0 --fsu_load W3 --fsu_submodel FR07-d --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 2 --fpu_decode_guard --fpu_op_classes SimdFloatAdd,SimdFloatMult,SimdFloatMultAcc,SimdFloatDiv,SimdFloatSqrt --fpu_reg_class vec --fpu_prf_wb_hook --config_profile B0 --fpu_events_to_skip 15149 --chaos_propagation --prop_run_id FSU-FR07-F0-W3 --prop_sample_run_id s3 --fsu_eligible_total 16384` |
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
| tick / cycle | 1129928030 / 2934878 |
| sn / PC / opcode | 3075744 / 0x0000000000400694 / fmla |
| 单元/结构/slot/port/lane | FSU_Pipe / uniform / — / — / 32@2 |
| precision / reg_class | fp32 / vec |
| instruction_bits / decoded_kind | 0x4e21cc40 / neon_vector |
| decoded precision / element width / lanes | fp32 / 32 / 4 |
| manifest precision / lane width / offset | fp32 / 32 / 2 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 15..22 |
| fault bit（绝对）/ bit_in_lane | 79 / 15 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x00000000007f8000 / 0x00000000007f80000000000000000000 |
| eligible ordinal / total | — / 16384 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 1129928030, Site: prf_wb_data, hook_version=2, opClass=SimdFloatMultAcc, sn=3075744, phys_reg=6, mask=0x7f8000, faults_injected: 1
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x3f3c9b42 → 0x3f431b42 |
| full 128-bit old/new | 0x3dba4df63f3c9b423f5596543f2caaba → 0x3dba4df63f431b423f5596543f2caaba |
| old/new hash | 0xc5096eb5a97bba79 → 0x0f374d31f39b70fa |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 2 / 32 |
| opClass / FU / FPCR / FPSR | fmla / — / uniform / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3f3c9b42 / 0x3f431b42 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

### fault 1（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 0 | — |
| 2 | carrier_state | L1 | 1 | 0 |
| 3 | operand_read | L2 | 3 | 1 |
| 4 | execute | L3 | 4 | 3 |
| 5 | prf_writeback | L4 | 5 | 4 |
| 6 | commit | L5 | 6 | 5 |
| 7 | chain_end | — | 7 | 6 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 1129928030 | 1 | 3075744 | 0x0000000000400694 | fmla | 3075744/— | 6 | — | 32@2 | 0x3f3c9b42→0x3f431b42 | — | — | origin |
| carrier_state | 1 | 0 | 1129928030 | 1 | 3075744 | 0x0000000000400694 | fmla | 3075744/— | 6 | — | 32@2 | 0x3f3c9b42→0x3f431b42 | — | — | fsu_taint |
| operand_read | 3 | 1 | 1129934190 | 1 | 3075768 | 0x0000000000400694 | fmla | 3075744/3075768 | 6 | 4 | 32@2 | —→— | — | — | fsu_taint |
| execute | 4 | 3 | 1129934190 | 1 | 3075768 | 0x0000000000400694 | fmla | 3075744/3075768 | 6 | 4 | 32@2 | —→— | — | — | fsu_taint |
| prf_writeback | 5 | 4 | 1129934190 | 1 | 3075768 | 0x0000000000400694 | fmla | 3075744/3075768 | 6 | 4 | 32@2 | —→— | — | — | fsu_taint |
| commit | 6 | 5 | 1129934960 | 1 | 3075768 | 0x0000000000400694 | fmla | —/3075768 | — | — | 32@2 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 7 | 6 | 2168676895 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#3（本 seed 真实事件）。
- **L3**：execute#4（本 seed 真实事件）。
- **L4**：prf_writeback#5（本 seed 真实事件）。
- **L5**：commit#6（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH cb66197d92c7656b9359b312e93180eaaf3c1e774d9264d791126311613e0959 != golden cb66197d92c7656b9359b312e93180eaaf3c1e774d9264d7d0b595189bce8c2e — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：8
- attempted / eligible / activated：1 / 16384 / 1

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 6 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_applied) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `3` (operand_read)；child.parent=1 ✓
- `3` (operand_read) → `4` (execute)；child.parent=3 ✓
- `4` (execute) → `5` (prf_writeback)；child.parent=4 ✓
- `5` (prf_writeback) → `6` (commit)；child.parent=5 ✓
- `6` (commit) → `7` (chain_end)；child.parent=6 ✓

- L5 真实见证：`6` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `4c0e315367d82b29d37664945f61d575c63bd021dda372de5bbd74a34625b11f` |
| `run.out` | `c33929bdef46114a8a8785e2fb0fb590aaac23ab59d6eb3accf92ae8a7f71022` |
| `run.err` | `dec72566590bdc5e161de8212087044774786c74f89964911cc196ef6b1ff992` |
| `stats.txt` | `0aaa6fde25111af088c98db0bf22bf914e35cd6fb3ff7bd0c30a74540e446d76` |
| `oracle.json` | `82cca1e772e381fdf35abfadf69433c8dd5db0104d7117d97af8e0d972a8eca6` |
| `chain_report.json` | `411b0d9794fe0337e7ee79e30b87e14607043d5fdcd4c7249581256448b3c1ee` |
| `census/fpu_injections.log` | `f2dbf29d15d86cd9e86121391197a6e6f93eddfc5f2a17b9b97a2079f9d3d3a0` |
| `inject/fpu_injections.log` | `f75e7034b365e46dd2c28ef588045733358c85b8a0e1e479b57d4f8d21bde493` |
| `inject/prop_evt.txt.gz` | `796a8674c12d49ed25beb1f7d9dc030c8f91954a9495863176a9c08673f55585` |
| `inject/stats.txt` | `0aaa6fde25111af088c98db0bf22bf914e35cd6fb3ff7bd0c30a74540e446d76` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `b494ad64badc406343ff1f6c7d7a397cb9bf97f166eefb5753d825b1033c74ca` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel` | `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
