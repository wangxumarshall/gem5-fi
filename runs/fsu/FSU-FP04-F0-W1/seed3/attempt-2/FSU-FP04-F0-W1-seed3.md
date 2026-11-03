# FSU-FP04-F0-W1 seed3 完整传播链

> 本文只使用本 seed（sample_run_id=`s3`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F0-W1` |
| 模型/子模型 | FP04 / FP04-a |
| 单元/频率/负载 | FSU Pipe / F0 / W1 |
| workload identity | W1-fp-scalar-probe-v1 |
| seed / sample_run_id | 3 / `s3` |
| selection seed / injection seed | 3 / 3 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe`（SHA-256 `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754`） |
| manifest | `runs/fsu/FSU-FP04-F0-W1/seed3/attempt-2/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `62f2f55a75fa1f8c9097ede2d6dfaae4a649c521b1609787d903e838a993740e`） |
| 源码 HEAD | `a7b129b4b39e481923e7673db4d46a3dac7a61ca` |
| 分析工具 SHA-256 | `26dbdbde2decf55573f3aabbaee0b7bc9c1eff6190c179ffb64e0909f579a47e` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F0-W1/seed3/attempt-2/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 3 --fsu_model FP04 --fsu_freq F0 --fsu_load W1 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F0-W1/seed3/attempt-2/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 3 --fsu_model FP04 --fsu_freq F0 --fsu_load W1 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --config_profile B0 --fpu_events_to_skip 37677 --chaos_propagation --prop_run_id FSU-FP04-F0-W1 --prop_sample_run_id s3 --fsu_eligible_total 49664` |
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
| tick / cycle | 2079636020 / 5401652 |
| sn / PC / opcode | 6066644 / 0x0000000000400d24 / fdiv |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 32@0 |
| precision / reg_class | fp32 / vec |
| instruction_bits / decoded_kind | 0x1e211800 / scalar_vfp |
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
Tick: 2079636020, Site: dyn_inst_execute, opClass=9, sn=6066644, bitseg=sign, precision=fp32, lane_width=32, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x80000000, faults_injected: 1
CHAOS_DECODE_REJECTS=31264
CHAOS_DECODE_REJECT_REASON precision_mismatch=31264
CHAOS_DECODE_KIND scalar_vfp=100746
CHAOS_DECODE_KIND unreliable=31274
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x7fc00001 → 0xffc00001 |
| full 128-bit old/new | 0x0000000000000000000000007fc00001 → 0x000000000000000000000000ffc00001 |
| old/new hash | 0xd4ebc709d009db1b → 0x7d7a31cb2854a99b |
| source/destination phys tag | src=— / dest=32 |
| operand role / lane / width | — / 0 / 32 |
| opClass / FU / FPCR / FPSR | fdiv / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x7fc00001 / 0xffc00001 |
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
| fault_applied | 0 | — | 2079636020 | 1 | 6066644 | 0x0000000000400d24 | fdiv | —/— | 32 | — | 32@0 | 0x7fc00001→0xffc00001 | — | — | origin |
| carrier_state | 1 | 0 | 2079636020 | 1 | 6066644 | 0x0000000000400d24 | fdiv | —/— | 32 | — | 32@0 | 0x7fc00001→0xffc00001 | — | — | fsu_taint |
| operand_read | 2 | 1 | 2079839685 | 1 | 6067272 | 0x0000000000400da8 | fmov | 6066644/6067272 | 32 | 2 | 32@0 | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 2079839685 | 1 | 6067272 | 0x0000000000400da8 | fmov | 6066644/6067272 | 32 | 2 | 32@0 | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 2079839685 | 1 | 6067272 | 0x0000000000400da8 | fmov | 6066644/6067272 | 32 | 2 | 32@0 | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 2079840455 | 1 | 6067272 | 0x0000000000400da8 | fmov | —/6067272 | — | — | 32@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 3298347745 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 57952e62f3b4781d9b0aad0f5e03901874d3440506066d93ede75820f2eba183 != golden ffe18c8279bf419d9b0aad0f5e03901874d3440506066d93ede75820f2eba183 — silent data corruption）
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
| `manifest.json` | `807d0f7333a33c1a5bfac552a1110e8cba08c8640f03120f9ad38febb499cc95` |
| `run.out` | `55bac7345e339c9bcc35db6971b151600d52f2df34c5b90b213274fde82f7672` |
| `run.err` | `70c903c6b501403db8b5162ced9bbf43f40b13e120d7c1df4354edaa225c9f68` |
| `stats.txt` | `9e24fe3cc7748d8fbf5f8d813b9425d6628040a711a4b574f8f61fcffcf49986` |
| `oracle.json` | `15479cef06a451142853f4fd733d5dd4a7b03a75f1ec74fc854ce23694c3cf76` |
| `chain_report.json` | `df9027ca37d6dc901522e8dbd4d1de87664fee50569a5e01a832a90055bed485` |
| `census/fpu_injections.log` | `79dd5620fc033243feb8c1f3723113b9390eec5fe81ae57da6ca3a4347ff957e` |
| `inject/fpu_injections.log` | `4f1c2553e951f643753ceb491e4fd2d1c4091e5710ab7563d9d14588527483f3` |
| `inject/prop_evt.txt.gz` | `6f336e8c8c29cbbf70fb936bbeeace09fd72b0eb4f395ad222b4689228f4bc47` |
| `inject/stats.txt` | `9e24fe3cc7748d8fbf5f8d813b9425d6628040a711a4b574f8f61fcffcf49986` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `62f2f55a75fa1f8c9097ede2d6dfaae4a649c521b1609787d903e838a993740e` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe` | `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
