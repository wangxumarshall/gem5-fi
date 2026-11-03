# FSU-FP04-F0-W1-GATE seed2 完整传播链

> 本文只使用本 seed（sample_run_id=`s2`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F0-W1-GATE` |
| 模型/子模型 | FP04 / FP04-a |
| 单元/频率/负载 | FSU Pipe / F0 / W1 |
| workload identity | W1-fp32-scalar-v1 |
| seed / sample_run_id | 2 / `s2` |
| selection seed / injection seed | 2 / 2 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/fp32_fma_kernel`（SHA-256 `bf3d26a4a2bcdd53b6a5dd1b04d540056b60e73108ff01e7fe01ece106c98eaf`） |
| manifest | `runs/fsu-gates/F0-W1-FP32-SIGN-gate/FSU-FP04-F0-W1-GATE/seed2/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `5647208d1fdf9ea131bcae60e0479fc5a0d477dce2fee0930bc8d04d40f47e73`） |
| 源码 HEAD | `2dbfb5964978ba0cb92b8bc2b166b8b8c6379029` |
| 分析工具 SHA-256 | `e19d8bbf12f45d8857416a92332997f9e610534d13b0cb3b718bb5dc92a82a2c` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F0-W1-FP32-SIGN-gate/FSU-FP04-F0-W1-GATE/seed2/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/fp32_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F0 --fsu_load W1 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F0-W1-FP32-SIGN-gate/FSU-FP04-F0-W1-GATE/seed2/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/fp32_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F0 --fsu_load W1 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_events_to_skip 469010 --chaos_propagation --prop_run_id FSU-FP04-F0-W1-GATE --prop_sample_run_id s2 --fsu_eligible_total 524292` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 524292 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 949396525 / 2465965 |
| sn / PC / opcode | 2977777 / 0x000000000040068c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 32@0 |
| precision / reg_class | fp32 / vec |
| field 范围（lane 内） | 31..31 |
| fault bit（绝对）/ bit_in_lane | 31 / 31 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x0000000080000000 / 0x00000000000000000000000080000000 |
| eligible ordinal / total | — / 524292 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 949396525, Site: dyn_inst_execute, opClass=8, sn=2977777, bitseg=sign, precision=fp32, lane_width=32, lane_offset=0, mask=0x80000000, faults_injected: 1
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x3c76ad9d → 0xbc76ad9d |
| full 128-bit old/new | 0x0000000000000000000000003c76ad9d → 0x000000000000000000000000bc76ad9d |
| old/new hash | 0xc2a3274757ec7e2f → 0x6b319208b0374caf |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 32 |
| opClass / FU / FPCR / FPSR | fmadd / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3c76ad9d / 0xbc76ad9d |
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
| fault_applied | 0 | — | 949396525 | 1 | 2977777 | 0x000000000040068c | fmadd | —/— | 45 | — | 32@0 | 0x3c76ad9d→0xbc76ad9d | — | — | origin |
| carrier_state | 1 | 0 | 949396525 | 1 | 2977777 | 0x000000000040068c | fmadd | —/— | 45 | — | 32@0 | 0x3c76ad9d→0xbc76ad9d | — | — | fsu_taint |
| operand_read | 2 | 1 | 949404995 | 1 | 2977793 | 0x000000000040068c | fmadd | 2977777/2977793 | 45 | 5 | 32@0 | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 949404995 | 1 | 2977793 | 0x000000000040068c | fmadd | 2977777/2977793 | 45 | 5 | 32@0 | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 949404995 | 1 | 2977793 | 0x000000000040068c | fmadd | 2977777/2977793 | 45 | 5 | 32@0 | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 949405765 | 1 | 2977793 | 0x000000000040068c | fmadd | —/2977793 | — | — | 32@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 1734137020 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 20d006b6f41191eb9359b312e93180eaaf3c1e774d9264d7d0b595189bce8c2e != golden cb66197d92c7656b9359b312e93180eaaf3c1e774d9264d7d0b595189bce8c2e — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 524292 / 1

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
| `manifest.json` | `737e8949b90032981a721e6a8ccd3d183cfe068d3866b0ef5250db2a56cf59e9` |
| `run.out` | `63c5adcff777536c4f34df69494bbcad59fe593261482757aa377b658493afd1` |
| `run.err` | `0417ff9982266f3b600e35fbd8fe02d81e37399ffa90930ea5d638b8a649c218` |
| `stats.txt` | `4905c617908864fc331619efe5d0065c36bc40aadc752ef4852e5718c7ab5e5c` |
| `oracle.json` | `bbd2da0b9d0d70e9ef01241bc2e7bfd577d5a8205cb5c17af9696cff17c38c31` |
| `chain_report.json` | `2f6818245ae6f0fc596e27c5eea229bd9e5aca9405a2342863ddd81cc38525e9` |
| `census/fpu_injections.log` | `79b6fba93055242c4fcaebb79021ed59efdaf7b1d80bb5425945394d0edad996` |
| `inject/fpu_injections.log` | `6e2d0624e069b68b0566c984e41e0ab8e377457a1cd43ebb998c05369dbc3e2c` |
| `inject/prop_evt.txt.gz` | `7cdc77dbbd96d0ac346a1dee815a4f99b3333fa378b59c18124669c9f0ecaed3` |
| `inject/stats.txt` | `4905c617908864fc331619efe5d0065c36bc40aadc752ef4852e5718c7ab5e5c` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `5647208d1fdf9ea131bcae60e0479fc5a0d477dce2fee0930bc8d04d40f47e73` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/fp32_fma_kernel` | `bf3d26a4a2bcdd53b6a5dd1b04d540056b60e73108ff01e7fe01ece106c98eaf` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
