# FSU-FP06-F5-W3 seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP06-F5-W3` |
| 模型/子模型 | FP06 / FP06-a |
| 单元/频率/负载 | FSU Pipe / F5 / W3 |
| workload identity | W3-neon-fp32-lane-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel`（SHA-256 `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92`） |
| manifest | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W3/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `8b1080971957cd47f395e62f2e56f85cd0eeeab451777bd4a7bb0dcd49f5dda6`） |
| 源码 HEAD | `9681b260daebf2b7ebf3ac99e65db4f944d74d8c` |
| 分析工具 SHA-256 | `5495363ff5d0e5052e63dbb5a8480b8d8dd3ecc40636e86bcb056af693979594` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W3/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 2147483648 --fpu_rng_seed 1 --fpu_permanent_stuck --fpu_stuck_polarity 0 --fpu_f5_warmup 0 --fpu_f5_sample_limit 1024 --fpu_f5_keep_first_last_n 256 --fsu_model FP06 --fsu_freq F5 --fsu_load W3 --fsu_submodel FP06-a --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 2 --fpu_decode_guard --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W3/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 2147483648 --fpu_rng_seed 1 --fpu_permanent_stuck --fpu_stuck_polarity 0 --fpu_f5_warmup 0 --fpu_f5_sample_limit 1024 --fpu_f5_keep_first_last_n 256 --fsu_model FP06 --fsu_freq F5 --fsu_load W3 --fsu_submodel FP06-a --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 2 --fpu_decode_guard --config_profile B0 --chaos_propagation --prop_run_id FSU-FP06-F5-W3 --prop_sample_run_id s1 --fsu_eligible_total 16384` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 16384 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

### F5 永久故障计数（一个 fault，多次 exposure）

| 项 | 值 |
|---|---|
| 安装次数（fault_installed） | 1 |
| 安装 fault_id / mask / polarity | 1 / 0x0000000080000000 / 0 |
| 已记录 exposure 事件 | 514 |
| 已记录 activated exposure | 26 |
| 全程 exposures_total | 16384 |
| sampled / dropped | 514 / 15870 |
| 全程 activated_exposure_count | 764 |
| sample policy | `bounded_first_last(limit=1024,first=256,last=256)` |
| terminal | committed |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 934334170 / 2426842 |
| sn / PC / opcode | 2893949 / 0x0000000000400694 / fmla |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 32@2 |
| precision / reg_class | fp32 / vec |
| instruction_bits / decoded_kind | 0x4e21cc40 / neon_vector |
| decoded precision / element width / lanes | fp32 / 32 / 4 |
| manifest precision / lane width / offset | fp32 / 32 / 2 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 31..31 |
| fault bit（绝对）/ bit_in_lane | 95 / 31 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x0000000080000000 / 0x00000000800000000000000000000000 |
| eligible ordinal / total | — / 16384 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
CHAOS_DECODE_REJECT_REASON lane_mismatch=262148
CHAOS_DECODE_REJECT_REASON undecoded:fcvt/int-convert=196608
CHAOS_DECODE_KIND neon_vector=16384
CHAOS_DECODE_KIND scalar_vfp=458758
CHAOS_DECODE_KIND unreliable=196614
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x3f08bc18 → 0x3f08bc18 |
| full 128-bit old/new | 0x3d96cbda3f08bc183eb33bdb3e4337a9 → 0x3d96cbda3f08bc183eb33bdb3e4337a9 |
| old/new hash | 0xbbd95423e6d81406 → 0xbbd95423e6d81406 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 2 / 32 |
| opClass / FU / FPCR / FPSR | fmla / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3f08bc18 / 0x3f08bc18 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

### fault 1（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_installed | L0 | 0 | — |
| 2 | carrier_state | L1 | 1 | 0 |
| 3 | exposure | — | 55 | 1 |
| 4 | operand_read | L2 | 58 | 55 |
| 5 | execute | L3 | 59 | 58 |
| 6 | prf_writeback | L4 | 60 | 59 |
| 7 | commit | L5 | 61 | 60 |
| 8 | chain_end | — | 521 | 61 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_installed | 0 | — | 934334170 | 1 | 2893949 | 0x0000000000400694 | fmla | —/— | 45 | — | 32@2 | 0x3f08bc18→0x3f08bc18 | — | — | origin |
| carrier_state | 1 | 0 | 934334170 | 1 | 2893949 | 0x0000000000400694 | fmla | —/— | 45 | — | 32@2 | 0x3f08bc18→0x3f08bc18 | — | — | fsu_taint |
| exposure | 55 | 1 | 935363660 | 1 | 2894592 | 0x0000000000400694 | fmla | —/— | 6 | — | 32@2 | 0xbe27ed83→0x3e27ed83 | — | — | fsu_taint |
| operand_read | 58 | 55 | 935404470 | 1 | 2894616 | 0x0000000000400694 | fmla | 2894592/2894616 | 6 | 4 | 32@2 | —→— | — | — | fsu_taint |
| execute | 59 | 58 | 935404470 | 1 | 2894616 | 0x0000000000400694 | fmla | 2894592/2894616 | 6 | 4 | 32@2 | —→— | — | — | fsu_taint |
| prf_writeback | 60 | 59 | 935404470 | 1 | 2894616 | 0x0000000000400694 | fmla | 2894592/2894616 | 6 | 4 | 32@2 | —→— | — | — | fsu_taint |
| commit | 61 | 60 | 935405240 | 1 | 2894616 | 0x0000000000400694 | fmla | —/2894616 | — | — | 32@2 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 521 | 61 | 2173365810 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | committed | fsu_taint |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_installed#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#58（本 seed 真实事件）。
- **L3**：execute#59（本 seed 真实事件）。
- **L4**：prf_writeback#60（本 seed 真实事件）。
- **L5**：commit#61（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH ecc623040618196b9c060a70153f976ab7b54ccf989944574678758db546872e != golden cb66197d92c7656b9359b312e93180eaaf3c1e774d9264d7d0b595189bce8c2e — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：522
- attempted / eligible / activated：1 / 16384 / 1

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 61 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_installed) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `55` (exposure)；child.parent=1 ✓
- `55` (exposure) → `58` (operand_read)；child.parent=55 ✓
- `58` (operand_read) → `59` (execute)；child.parent=58 ✓
- `59` (execute) → `60` (prf_writeback)；child.parent=59 ✓
- `60` (prf_writeback) → `61` (commit)；child.parent=60 ✓
- `61` (commit) → `521` (chain_end)；child.parent=61 ✓

- L5 真实见证：`61` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `340d82788834532b708dfbd17bd10437370094ee6190c9ba01e3c056094bc1f2` |
| `run.out` | `48e0d74000ced26bcd7635dea8460c805a6f48497f6af6d67e68a876e5a5d784` |
| `run.err` | `dec72566590bdc5e161de8212087044774786c74f89964911cc196ef6b1ff992` |
| `stats.txt` | `cc01892726f4eec93578d3ff4ef0a9fdc03dd201211f23bcee5861698b41006b` |
| `oracle.json` | `df505893b08a706795ea253bb8bf7e1efdaee4977ca3dfcd858be920b943df9f` |
| `chain_report.json` | `1acd3a168fd68ac7cb97da6a607939dc0246ed035e894f3fa97c22020c8e8c64` |
| `census/fpu_injections.log` | `a11af940ae5abd172a9256c3b0d49a82356f9814c3ed2922e7b15ba6f78f4b1a` |
| `inject/fpu_injections.log` | `c88a3449553bd48a3d104322aacdbbe971b6f91877d6ad2c4c47e272ef48a8b8` |
| `inject/prop_evt.txt.gz` | `6658d30f0e181f89eadb072398513b64109811baa091d0266f1c3823aec4f1eb` |
| `inject/stats.txt` | `cc01892726f4eec93578d3ff4ef0a9fdc03dd201211f23bcee5861698b41006b` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `8b1080971957cd47f395e62f2e56f85cd0eeeab451777bd4a7bb0dcd49f5dda6` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel` | `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
