# FSU-FP04-F0-W4-GATE seed2 完整传播链

> 本文只使用本 seed（sample_run_id=`s2`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F0-W4-GATE` |
| 模型/子模型 | FP04 / FP04-a |
| 单元/频率/负载 | FSU Pipe / F0 / W4 |
| workload identity | W4-short |
| seed / sample_run_id | 2 / `s2` |
| selection seed / injection seed | 2 / 2 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel`（SHA-256 `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97`） |
| manifest | `runs/fsu-gates/F0-W4-SIGN-gate/FSU-FP04-F0-W4-GATE/seed2/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `5647208d1fdf9ea131bcae60e0479fc5a0d477dce2fee0930bc8d04d40f47e73`） |
| 源码 HEAD | `2dbfb5964978ba0cb92b8bc2b166b8b8c6379029` |
| 分析工具 SHA-256 | `e19d8bbf12f45d8857416a92332997f9e610534d13b0cb3b718bb5dc92a82a2c` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F0-W4-SIGN-gate/FSU-FP04-F0-W4-GATE/seed2/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F0 --fsu_load W4 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F0-W4-SIGN-gate/FSU-FP04-F0-W4-GATE/seed2/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F0 --fsu_load W4 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_events_to_skip 13908 --chaos_propagation --prop_run_id FSU-FP04-F0-W4-GATE --prop_sample_run_id s2 --fsu_eligible_total 57347` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 57347 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 33769120 / 87712 |
| sn / PC / opcode | 94347 / 0x00000000004005ec / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 64@0 |
| precision / reg_class | fp64 / vec |
| field 范围（lane 内） | 63..63 |
| fault bit（绝对）/ bit_in_lane | 63 / 63 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x8000000000000000 / 0x00000000000000008000000000000000 |
| eligible ordinal / total | — / 57347 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 33769120, Site: dyn_inst_execute, opClass=8, sn=94347, bitseg=sign, precision=fp64, lane_width=64, lane_offset=0, mask=0x8000000000000000, faults_injected: 1
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x3fe25604189374bc → 0xbfe25604189374bc |
| full 128-bit old/new | 0x00000000000000003fe25604189374bc → 0x0000000000000000bfe25604189374bc |
| old/new hash | 0x42560d5851642261 → 0x42558d58516348e1 |
| source/destination phys tag | src=— / dest=32 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe25604189374bc / 0xbfe25604189374bc |
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
| fault_applied | 0 | — | 33769120 | 1 | 94347 | 0x00000000004005ec | fmadd | —/— | 32 | — | 64@0 | 0x3fe25604189374bc→0xbfe25604189374bc | — | — | origin |
| carrier_state | 1 | 0 | 33769120 | 1 | 94347 | 0x00000000004005ec | fmadd | —/— | 32 | — | 64@0 | 0x3fe25604189374bc→0xbfe25604189374bc | — | — | fsu_taint |
| operand_read | 2 | 1 | 33804540 | 1 | 94491 | 0x00000000004005ec | fmadd | 94347/94491 | 32 | 3 | 64@0 | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 33804540 | 1 | 94491 | 0x00000000004005ec | fmadd | 94347/94491 | 32 | 3 | 64@0 | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 33804540 | 1 | 94491 | 0x00000000004005ec | fmadd | 94347/94491 | 32 | 3 | 64@0 | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 33805310 | 1 | 94491 | 0x00000000004005ec | fmadd | —/94491 | — | — | 64@0 | —→— | L5 | errant_commit | fsu_taint |
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

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH ced113fdd122842d658d24a1683f240af55f78de0e043ff761239d5d989f43e7 != golden ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7 — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 57347 / 1

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
| `manifest.json` | `309fae2e23e5272c340bc85d8dc7e63d786bb4f978d2b0cecd04e1b0376cb975` |
| `run.out` | `9c47b5672c97451eb9d486cf9ebcf24ff134bd77dac2151fe7c9b4fe3036ed28` |
| `run.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `stats.txt` | `c11b82319c13d1c46f21a4f865db521388c613cc72ac981f283bea97828b1100` |
| `oracle.json` | `8b9a33f43199668dde5637324834c337e202978f7aa02e20f2552732a508a53d` |
| `chain_report.json` | `ea4055aa4d7f3c3600e1b0c35e700aae77a491e37354429b1195e065fb04d1ce` |
| `census/fpu_injections.log` | `7bc8726ba761e237b918a253b4aa17afe92f63b6fb33bcdbe3233ab77f314a00` |
| `inject/fpu_injections.log` | `c18bf896a814be4d948477270ae922cf7f232cefa87105e687fe91354a884436` |
| `inject/prop_evt.txt.gz` | `3a5d9c41627cec20c4e8dc29aae6f16012e6270728646935632b363de22398ad` |
| `inject/stats.txt` | `c11b82319c13d1c46f21a4f865db521388c613cc72ac981f283bea97828b1100` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `5647208d1fdf9ea131bcae60e0479fc5a0d477dce2fee0930bc8d04d40f47e73` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel` | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
