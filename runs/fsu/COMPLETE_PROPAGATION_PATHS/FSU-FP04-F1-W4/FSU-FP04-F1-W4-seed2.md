# FSU-FP04-F1-W4 seed2 完整传播链

> 本文只使用本 seed（sample_run_id=`s2`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F1-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F1 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 2 / `s2` |
| selection seed / injection seed | 2 / 2 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F1-W4/seed2/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `2c9f6ab0ccd3842d445c968c6d146ba6eefee753` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F1-W4/seed2/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F1 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F1-W4/seed2/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 2 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 2 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F1 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 1027869,1716133 --fpu_rate_warmup 0 --fsu_rate_divisor 1000000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F1-W4 --prop_sample_run_id s2 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 1000000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:1027869, 1:1716133 |
| ordinals SHA-256 | `b751d246742d462a57fed2e6f8f897783babdbe153761aae87bba2691b10e2dc` |
| 注入数（actual/expected） | 2 / 2 |
| fault 数（事件流/injection log） | 2 / 2 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 1575854280 / 4093128 |
| sn / PC / opcode | 6180087 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1027869 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 1000000 / 50 / 1027869 / 0 |
| terminal | full |

### fault 2

| 字段 | 值 |
|---|---|
| 根 event_id | `6` |
| tick / cycle | 3251629535 / 8445791 |
| sn / PC / opcode | 10598059 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1716133 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 1000000 / 50 / 688264 / 1 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 1575854280, Site: dyn_inst_execute, opClass=8, sn=6180087, bitseg=mant_lo, mask=0x1, faults_injected: 1
Tick: 3251629535, Site: dyn_inst_execute, opClass=8, sn=10598059, bitseg=mant_lo, mask=0x8000, faults_injected: 2
CHAOS_RATE_COMPLETE=2
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fec20c49ba5e354 → 0x3fec20c49ba5e355 |
| old/new hash | 0xe3500f7b87b2b99b → 0x17d4b828ec06ba5a |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fec20c49ba5e354 / 0x3fec20c49ba5e355 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 2

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfb4637bd05af6c4 → 0xbfb4637bd05a76c4 |
| old/new hash | 0x082dd479a3c17a38 → 0xff216f253b5ba8b8 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfb4637bd05af6c4 / 0xbfb4637bd05a76c4 |
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
| 7 | chain_end | — | 12 | 5 |

### fault 2（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 6 | — |
| 2 | carrier_state | L1 | 7 | 6 |
| 3 | operand_read | L2 | 8 | 7 |
| 4 | execute | L3 | 9 | 8 |
| 5 | prf_writeback | L4 | 10 | 9 |
| 6 | commit | L5 | 11 | 10 |
| 7 | chain_end | — | 13 | 11 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 1575854280 | 1 | 6180087 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fec20c49ba5e354→0x3fec20c49ba5e355 | — | — | origin |
| carrier_state | 1 | 0 | 1575854280 | 1 | 6180087 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fec20c49ba5e354→0x3fec20c49ba5e355 | — | — | fsu_taint |
| operand_read | 2 | 1 | 1575878535 | 1 | 6180194 | 0x0000000000400654 | fmadd | 6180087/6180194 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 1575878535 | 1 | 6180194 | 0x0000000000400654 | fmadd | 6180087/6180194 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 1575878535 | 1 | 6180194 | 0x0000000000400654 | fmadd | 6180087/6180194 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 1575879305 | 1 | 6180194 | 0x0000000000400654 | fmadd | —/6180194 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 12 | 5 | 9406331165 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 6 | — | 3251629535 | 2 | 10598059 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0xbfb4637bd05af6c4→0xbfb4637bd05a76c4 | — | — | origin |
| carrier_state | 7 | 6 | 3251629535 | 2 | 10598059 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0xbfb4637bd05af6c4→0xbfb4637bd05a76c4 | — | — | fsu_taint |
| operand_read | 8 | 7 | 3251638005 | 2 | 10598075 | 0x00000000004006cc | fmadd | 10598059/10598075 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 3251638005 | 2 | 10598075 | 0x00000000004006cc | fmadd | 10598059/10598075 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 3251638005 | 2 | 10598075 | 0x00000000004006cc | fmadd | 10598059/10598075 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 3251638775 | 2 | 10598075 | 0x00000000004006cc | fmadd | —/10598075 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 13 | 11 | 9406331165 | 2 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

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

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH e563e3e1bb7ee0e1fd2655fb2e8ec248a7345a2627f04c456b62a74a7b525aba != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：2 / 2
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：14
- attempted / eligible / activated：2 / 2097155 / 2

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 5 | N/A / N/A |
| 2 | full | L5 | True | True | [] | 11 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_applied) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `2` (operand_read)；child.parent=1 ✓
- `2` (operand_read) → `3` (execute)；child.parent=2 ✓
- `3` (execute) → `4` (prf_writeback)；child.parent=3 ✓
- `4` (prf_writeback) → `5` (commit)；child.parent=4 ✓
- `5` (commit) → `12` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

### fault 2

主链每一条边均验证为直接 parent：

- `6` (fault_applied) → `7` (carrier_state)；child.parent=6 ✓
- `7` (carrier_state) → `8` (operand_read)；child.parent=7 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `13` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `3377f07dd1643ee0857d595db557b8d4e73ed085bc721e060ad00dba782a1adb` |
| `run.out` | `9a62dbea004c512bac88d344726142cd1077aed2d18fe427b8984e376d202067` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `b468fa4df061801d30bac18b501a9a93c6569f51fb8b792c7c67f1d9dde002a9` |
| `oracle.json` | `472f534c079cb09ba510e237db8f0c34d02acafceb57e624ab6d1aaf53cbdc50` |
| `chain_report.json` | `7516bcb3a2d14d4901eab84a94adf0118eef6f6aabc8eba2155a46bfc7e728b8` |
| `ordinals.json` | `b751d246742d462a57fed2e6f8f897783babdbe153761aae87bba2691b10e2dc` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `b36c84a18420548aab3f6a8cc8e6550ff3f561cbf77954eae72a2d6e7f08f940` |
| `inject/prop_evt.txt.gz` | `d4afd32159856e396ee887ce490c83c1791d750dceab651f4d29505d58867459` |
| `inject/stats.txt` | `b468fa4df061801d30bac18b501a9a93c6569f51fb8b792c7c67f1d9dde002a9` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 2 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
