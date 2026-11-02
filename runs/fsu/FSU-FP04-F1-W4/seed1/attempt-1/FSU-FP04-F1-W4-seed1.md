# FSU-FP04-F1-W4 seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F1-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F1 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F1-W4/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `d0cad4ee1d3aedc1ded9bc56eafdbab8c5a0cf49` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F1-W4/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F1 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F1-W4/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F1 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 1394471 --fpu_rate_warmup 0 --fsu_rate_divisor 1000000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F1-W4 --prop_sample_run_id s1 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 1000000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:1394471 |
| ordinals SHA-256 | `b8e80e065b4cbe2352f85fc0ca092e625ddb190aa44e5b1d0e2f67f7fc3ef892` |
| 注入数（actual/expected） | 1 / 1 |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 2133289620 / 5541012 |
| sn / PC / opcode | 8379719 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1394471 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 1000000 / 50 / 1394471 / 0 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 2133289620, Site: dyn_inst_execute, opClass=6, sn=8379719, bitseg=mant_lo, mask=0x2000, faults_injected: 1
CHAOS_RATE_COMPLETE=1
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081b80000000000 → 0x4081b80000002000 |
| old/new hash | 0x21a6df7bc45b1172 → 0xf9ba90c73bb76712 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081b80000000000 / 0x4081b80000002000 |
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
| fault_applied | 0 | — | 2133289620 | 1 | 8379719 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4081b80000000000→0x4081b80000002000 | — | — | origin |
| carrier_state | 1 | 0 | 2133289620 | 1 | 8379719 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4081b80000000000→0x4081b80000002000 | — | — | fsu_taint |
| operand_read | 2 | 1 | 2133291545 | 1 | 8379722 | 0x0000000000400654 | fmadd | 8379719/8379722 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 2133291545 | 1 | 8379722 | 0x0000000000400654 | fmadd | 8379719/8379722 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 2133291545 | 1 | 8379722 | 0x0000000000400654 | fmadd | 8379719/8379722 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 2133292315 | 1 | 8379722 | 0x0000000000400654 | fmadd | —/8379722 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
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

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd4943007695efdb64c != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
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
| `manifest.json` | `80a90826f33401fe254557be266749288c1fb99cd96bb09ba6f99fb775981cc1` |
| `run.out` | `fddadba105b0f167f3c7eb9d22e1352745d9d6259df0a6ef641545dbc5270b23` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `43ee881bfac6ce88b0dfc397f39ef9993828cdd5ef6fafaf1f54f73f90f0e871` |
| `oracle.json` | `748817ade9d580d2f51504c8899e6df14db71a40a5ef126d017095d5cc752e2a` |
| `chain_report.json` | `e388bd6b2982e750022ef227d670f9d685c1d619667e1903cc5b8b1817406f55` |
| `ordinals.json` | `b8e80e065b4cbe2352f85fc0ca092e625ddb190aa44e5b1d0e2f67f7fc3ef892` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `5198600acf12a013616c7c6dddb47d11801a04125c3ced50d9af0cae4d71a0fa` |
| `inject/prop_evt.txt.gz` | `45b0de25c72ace63d6160d8b6aac823d6b26793232ef54ef60153351c2a85056` |
| `inject/stats.txt` | `43ee881bfac6ce88b0dfc397f39ef9993828cdd5ef6fafaf1f54f73f90f0e871` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
