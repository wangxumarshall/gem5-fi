# FSU-FP04-F1-W4 seed3 完整传播链

> 本文只使用本 seed（sample_run_id=`s3`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F1-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F1 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 3 / `s3` |
| selection seed / injection seed | 3 / 3 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F1-W4/seed3/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `cf637b9ac690a66c8c04dd57d5dfd38f5a2034b2` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F1-W4/seed3/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 3 --fsu_model FP04 --fsu_freq F1 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F1-W4/seed3/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 3 --fsu_model FP04 --fsu_freq F1 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 1306838 --fpu_rate_warmup 0 --fsu_rate_divisor 1000000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F1-W4 --prop_sample_run_id s3 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 1000000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:1306838 |
| ordinals SHA-256 | `39e0b89571c30645f0ee14a5f53a3a59230f2422480007513230a67de8e2ccaa` |
| 注入数（actual/expected） | 1 / 1 |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 2000113115 / 5195099 |
| sn / PC / opcode | 7853908 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1306838 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 1000000 / 50 / 1306838 / 0 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 2000113115, Site: dyn_inst_execute, opClass=8, sn=7853908, bitseg=mant_lo, mask=0x10, faults_injected: 1
CHAOS_RATE_COMPLETE=1
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfce978d4fdf3b64 → 0xbfce978d4fdf3b74 |
| old/new hash | 0xa458009a6e697b9f → 0x536df42777d45eef |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfce978d4fdf3b64 / 0xbfce978d4fdf3b74 |
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
| fault_applied | 0 | — | 2000113115 | 1 | 7853908 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfce978d4fdf3b64→0xbfce978d4fdf3b74 | — | — | origin |
| carrier_state | 1 | 0 | 2000113115 | 1 | 7853908 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfce978d4fdf3b64→0xbfce978d4fdf3b74 | — | — | fsu_taint |
| operand_read | 2 | 1 | 2000128515 | 1 | 7853978 | 0x0000000000400654 | fmadd | 7853908/7853978 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 2000128515 | 1 | 7853978 | 0x0000000000400654 | fmadd | 7853908/7853978 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 2000128515 | 1 | 7853978 | 0x0000000000400654 | fmadd | 7853908/7853978 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 2000129285 | 1 | 7853978 | 0x0000000000400654 | fmadd | —/7853978 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 9406573715 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd47568e284bb21b75a != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / 1
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 2097155 / 1

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
| `manifest.json` | `ed8b17f5ec63f2c911acee30c7d308b209dfcfc252dd04c0730e59f114bc9892` |
| `run.out` | `61c0840dfaf1845ef9ef6816baf3a2b3e4a41b19b1284d474aca2871184e90d1` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `06318bb50a52b05328a6ddeb0d770c41db5aba9c2f4da11791602906f98bead3` |
| `oracle.json` | `c3d31e16ba05e490a32b98b8dbd1a5519b12567ef73a02d8ea8407b5b7651550` |
| `chain_report.json` | `272afc76827fca77b2e9ebabcacaaabd1763fa1f9457b8a8bf61b242ea47db22` |
| `ordinals.json` | `39e0b89571c30645f0ee14a5f53a3a59230f2422480007513230a67de8e2ccaa` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `35e1fa08e8a487397fbc7c4e9a86bc65caa2dd1c2ef0494afbee3c19c9832cf7` |
| `inject/prop_evt.txt.gz` | `acaf6707576b7b0f13b9d96947d5d4c57ce77443b59c3c1f3acd610037af3f25` |
| `inject/stats.txt` | `06318bb50a52b05328a6ddeb0d770c41db5aba9c2f4da11791602906f98bead3` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
