# FSU-FP04-F0-W4-DECODE-GATE seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F0-W4-DECODE-GATE` |
| 模型/子模型 | FP04 / FP04-a |
| 单元/频率/负载 | FSU Pipe / F0 / W4 |
| workload identity | W4-short |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel`（SHA-256 `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97`） |
| manifest | `runs/fsu-gates/F0-W4-DECODE-gate/FSU-FP04-F0-W4-DECODE-GATE/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `62f2f55a75fa1f8c9097ede2d6dfaae4a649c521b1609787d903e838a993740e`） |
| 源码 HEAD | `1514c95126e7d0452a25212d7936b8965dcea2f7` |
| 分析工具 SHA-256 | `26dbdbde2decf55573f3aabbaee0b7bc9c1eff6190c179ffb64e0909f579a47e` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F0-W4-DECODE-gate/FSU-FP04-F0-W4-DECODE-GATE/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F0 --fsu_load W4 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_decode_guard --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F0-W4-DECODE-gate/FSU-FP04-F0-W4-DECODE-GATE/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F0 --fsu_load W4 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_decode_guard --fpu_events_to_skip 22063 --chaos_propagation --prop_run_id FSU-FP04-F0-W4-DECODE-GATE --prop_sample_run_id s1 --fsu_eligible_total 32771` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 32771 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 78970815 / 205119 |
| sn / PC / opcode | 275645 / 0x00000000004005f4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 64@0 |
| precision / reg_class | fp64 / vec |
| instruction_bits / decoded_kind | 0x1f431000 / scalar_vfp |
| decoded precision / element width / lanes | fp64 / 64 / 1 |
| manifest precision / lane width / offset | fp64 / 64 / 0 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 63..63 |
| fault bit（绝对）/ bit_in_lane | 63 / 63 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x8000000000000000 / 0x00000000000000008000000000000000 |
| eligible ordinal / total | — / 32771 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 78970815, Site: dyn_inst_execute, opClass=8, sn=275645, bitseg=sign, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
CHAOS_DECODE_REJECTS=22062
CHAOS_DECODE_REJECT_REASON undecoded:fcvt/int-convert=22062
CHAOS_DECODE_KIND scalar_vfp=22064
CHAOS_DECODE_KIND unreliable=22068
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0xbfc47ae147ae147b → 0x3fc47ae147ae147b |
| full 128-bit old/new | 0x0000000000000000bfc47ae147ae147b → 0x00000000000000003fc47ae147ae147b |
| old/new hash | 0x50de6d96e90fbf45 → 0x50deed96e91098c5 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc47ae147ae147b / 0x3fc47ae147ae147b |
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
| fault_applied | 0 | — | 78970815 | 1 | 275645 | 0x00000000004005f4 | fmadd | —/— | 46 | — | 64@0 | 0xbfc47ae147ae147b→0x3fc47ae147ae147b | — | — | origin |
| carrier_state | 1 | 0 | 78970815 | 1 | 275645 | 0x00000000004005f4 | fmadd | —/— | 46 | — | 64@0 | 0xbfc47ae147ae147b→0x3fc47ae147ae147b | — | — | fsu_taint |
| operand_read | 2 | 1 | 78986215 | 1 | 275715 | 0x00000000004005ec | fmadd | 275645/275715 | 46 | 3 | 64@0 | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 78986215 | 1 | 275715 | 0x00000000004005ec | fmadd | 275645/275715 | 46 | 3 | 64@0 | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 78986215 | 1 | 275715 | 0x00000000004005ec | fmadd | 275645/275715 | 46 | 3 | 64@0 | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 78986985 | 1 | 275715 | 0x00000000004005ec | fmadd | —/275715 | — | — | 64@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 232548855 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH ced113fdd122842d91a79059d75e2a24f55f78de0e043ff7010902964c3accee != golden ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7 — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 32771 / 1

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
| `manifest.json` | `eabb7d1e6276197b24ea8f82a65954c6676082e9b06c12bcb2788d7f39bdc6be` |
| `run.out` | `3cc614fd2333c5b774e835a6f217ffb475ce84a953dc18205832b8f13e96e073` |
| `run.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `stats.txt` | `ef73c26f8069217d3a9c301d689ffb97657603b6006d2c45c863645dcd36972b` |
| `oracle.json` | `3a2965097f8c3d471af8044fcbab4d11f9068eae7a0a7b43d92a0f3d59d76466` |
| `chain_report.json` | `a566588605aabf6ea1a23f10b82235e2583ca38c5150427874275c26f18de6c6` |
| `census/fpu_injections.log` | `388541df920fdcf616e28cefac5220ed9ce20208fbc1188a7b1c6f65f9cf779a` |
| `inject/fpu_injections.log` | `050bc36915792662170b65b602fc71ed53555c9f1c0a81266e7817f64b583330` |
| `inject/prop_evt.txt.gz` | `a7652bb0ec0cbec2fcbce2e06f77c984f8a80d688f86a8ccb99b16a88a5d5361` |
| `inject/stats.txt` | `ef73c26f8069217d3a9c301d689ffb97657603b6006d2c45c863645dcd36972b` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `62f2f55a75fa1f8c9097ede2d6dfaae4a649c521b1609787d903e838a993740e` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel` | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
