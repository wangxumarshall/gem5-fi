# FSU-FP04-F0-W1 seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F0-W1` |
| 模型/子模型 | FP04 / FP04-a |
| 单元/频率/负载 | FSU Pipe / F0 / W1 |
| workload identity | W1-fp-scalar-probe-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe`（SHA-256 `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754`） |
| manifest | `runs/fsu/FSU-FP04-F0-W1/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `62f2f55a75fa1f8c9097ede2d6dfaae4a649c521b1609787d903e838a993740e`） |
| 源码 HEAD | `33e3b0cc5fd68e58eb75b40cfa7fbce5404ef5f1` |
| 分析工具 SHA-256 | `572e92ccd9b4732d3a6dededdb5bd9d5977e864ca9465ead744235a6d67f178b` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F0-W1/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F0 --fsu_load W1 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F0-W1/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F0 --fsu_load W1 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --fpu_events_to_skip 9427 --chaos_propagation --prop_run_id FSU-FP04-F0-W1 --prop_sample_run_id s1 --fsu_eligible_total 49664` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 49664 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 303637180 / 788668 |
| sn / PC / opcode | 251299 / 0x0000000000400ea0 / fmov |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 32@0 |
| precision / reg_class | fp32 / vec |
| instruction_bits / decoded_kind | 0x1e270060 / scalar_vfp |
| decoded precision / element width / lanes | fp32 / 32 / 1 |
| manifest precision / lane width / offset | fp32 / 32 / 0 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 31..31 |
| fault bit（绝对）/ bit_in_lane | 31 / 31 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x0000000080000000 / 0x00000000000000000000000080000000 |
| eligible ordinal / total | — / 49664 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 303637180, Site: dyn_inst_execute, opClass=10, sn=251299, bitseg=sign, precision=fp32, lane_width=32, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x80000000, faults_injected: 1
CHAOS_DECODE_REJECTS=7823
CHAOS_DECODE_REJECT_REASON precision_mismatch=7823
CHAOS_DECODE_KIND scalar_vfp=25220
CHAOS_DECODE_KIND unreliable=7834
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x4b000000 → 0xcb000000 |
| full 128-bit old/new | 0x0000000000000000000000004b000000 → 0x000000000000000000000000cb000000 |
| old/new hash | 0xe5dcd49c6b33a81e → 0x8e6b3f5dc37e769e |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 32 |
| opClass / FU / FPCR / FPSR | fmov / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4b000000 / 0xcb000000 |
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
| fault_applied | 0 | — | 303637180 | 1 | 251299 | 0x0000000000400ea0 | fmov | —/— | 4 | — | 32@0 | 0x4b000000→0xcb000000 | — | — | origin |
| carrier_state | 1 | 0 | 303637180 | 1 | 251299 | 0x0000000000400ea0 | fmov | —/— | 4 | — | 32@0 | 0x4b000000→0xcb000000 | — | — | fsu_taint |
| operand_read | 2 | 1 | 303658740 | 1 | 251323 | 0x0000000000400f00 | fsub | 251299/251323 | 4 | 3 | 32@0 | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 303658740 | 1 | 251323 | 0x0000000000400f00 | fsub | 251299/251323 | 4 | 3 | 32@0 | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 303658740 | 1 | 251323 | 0x0000000000400f00 | fsub | 251299/251323 | 4 | 3 | 32@0 | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 303659510 | 1 | 251323 | 0x0000000000400f00 | fsub | —/251323 | — | — | 32@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 2922403715 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**Masked**（completed exit=0, ARRAYHASH==golden (ffe18c8279bf419d...) — fault did not propagate）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 49664 / 1

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 5 | N/A / N/A |

- 结局标签（run-level oracle）：Masked/contained

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
| `manifest.json` | `8e110ee04e330c22b659166e405180f891c53efa845ac18b751db1672ad95e12` |
| `run.out` | `555c3bf578c4aea043be7e6217986a71fee7702027dd5995633cc15a5c31a90d` |
| `run.err` | `70c903c6b501403db8b5162ced9bbf43f40b13e120d7c1df4354edaa225c9f68` |
| `stats.txt` | `524c66493624c1ba2a10ca6412768e669da29b38fcb0af40750757fa7ded0933` |
| `oracle.json` | `60dda9a7bbbd4b296d51faa07c2f4e7a1f362c779bdde3b0d56519206acb709e` |
| `chain_report.json` | `f8bd7cc42dc1842a2ab64c64c72da59b09339726efd19ea851be4effaf4ee329` |
| `census/fpu_injections.log` | `545c8160670460c586e0a83594ae51e3c5a1c86097aad4a8d250cf6be86bedfb` |
| `inject/fpu_injections.log` | `6ecc7736f396f0beb1cf2e98d96f3f9365927e67856b129286cf06c07ed2173a` |
| `inject/prop_evt.txt.gz` | `47c0821be2e4ccd4cc699b48930f83f0bc53f9c7335a88c175ac76cb458b8163` |
| `inject/stats.txt` | `524c66493624c1ba2a10ca6412768e669da29b38fcb0af40750757fa7ded0933` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `62f2f55a75fa1f8c9097ede2d6dfaae4a649c521b1609787d903e838a993740e` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe` | `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
