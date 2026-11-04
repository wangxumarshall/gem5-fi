# FSU-FR07-F0-W1 seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FR07-F0-W1` |
| 模型/子模型 | FR07 / FR07-a |
| 单元/频率/负载 | FSU Pipe / F0 / W1 |
| workload identity | W1-fp-scalar-probe-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe`（SHA-256 `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754`） |
| manifest | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR07-F0-W1/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `9457531948999dd8241e6c6ad6fb85d0e529d5b7017f238d23c36b3d2302e28d`） |
| 源码 HEAD | `68dbd4bef5a582261092cb3f0af0928d542a1a8a` |
| 分析工具 SHA-256 | `150453e70b937c226e871f0c3218c0d625307db31af6ca887d82203ef7c4aa72` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR07-F0-W1/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 2147483648 --fpu_rng_seed 1 --fsu_model FR07 --fsu_freq F0 --fsu_load W1 --fsu_submodel FR07-a --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --fpu_op_classes FloatAdd,FloatMult,FloatMultAcc,FloatDiv,FloatSqrt --fpu_reg_class vec --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR07-F0-W1/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 2147483648 --fpu_rng_seed 1 --fsu_model FR07 --fsu_freq F0 --fsu_load W1 --fsu_submodel FR07-a --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --fpu_op_classes FloatAdd,FloatMult,FloatMultAcc,FloatDiv,FloatSqrt --fpu_reg_class vec --config_profile B0 --fpu_events_to_skip 467 --chaos_propagation --prop_run_id FSU-FR07-F0-W1 --prop_sample_run_id s1 --fsu_eligible_total 41216` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 41216 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 33392975 / 86735 |
| sn / PC / opcode | 25308 / 0x0000000000400ec8 / fadd |
| 单元/结构/slot/port/lane | FSU_Pipe / uniform / — / — / 32@0 |
| precision / reg_class | fp32 / vec |
| instruction_bits / decoded_kind | 0x1e212800 / scalar_vfp |
| decoded precision / element width / lanes | fp32 / 32 / 1 |
| manifest precision / lane width / offset | fp32 / 32 / 0 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 31..31 |
| fault bit（绝对）/ bit_in_lane | 31 / 31 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x0000000080000000 / 0x00000000000000000000000080000000 |
| eligible ordinal / total | — / 41216 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 15928990, Site: dyn_inst_execute, sn=11635, pc=0x400d9c, decode_reject=precision_mismatch, enc=0x1e612800, decoded_kind=scalar_vfp, decoded_precision=fp64, decoded_width=64, decoded_lanes=1, manifest_precision=fp32, manifest_lane_width=32, manifest_lane_offset=0
Tick: 33392975, Site: dyn_inst_execute, opClass=4, sn=25308, precision=fp32, lane_width=32, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x80000000, faults_injected: 1
CHAOS_DECODE_REJECTS=467
CHAOS_DECODE_REJECT_REASON precision_mismatch=467
CHAOS_DECODE_KIND scalar_vfp=935
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x7fc00001 → 0xffc00001 |
| full 128-bit old/new | 0x0000000000000000000000007fc00001 → 0x000000000000000000000000ffc00001 |
| old/new hash | 0xd4ebc709d009db1b → 0x7d7a31cb2854a99b |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 32 |
| opClass / FU / FPCR / FPSR | fadd / — / uniform / N/A（事件未携带则不为推测） |
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
| fault_applied | 0 | — | 33392975 | 1 | 25308 | 0x0000000000400ec8 | fadd | —/— | 45 | — | 32@0 | 0x7fc00001→0xffc00001 | — | — | origin |
| carrier_state | 1 | 0 | 33392975 | 1 | 25308 | 0x0000000000400ec8 | fadd | —/— | 45 | — | 32@0 | 0x7fc00001→0xffc00001 | — | — | fsu_taint |
| operand_read | 2 | 1 | 33408375 | 1 | 25325 | 0x0000000000400f0c | fmov | 25308/25325 | 45 | 2 | 32@0 | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 33408375 | 1 | 25325 | 0x0000000000400f0c | fmov | 25308/25325 | 45 | 2 | 32@0 | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 33408375 | 1 | 25325 | 0x0000000000400f0c | fmov | 25308/25325 | 45 | 2 | 32@0 | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 33409145 | 1 | 25325 | 0x0000000000400f0c | fmov | —/25325 | — | — | 32@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 3298338120 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 8c15f601cfe6b71d9b0aad0f5e03901874d3440506066d93ede75820f2eba183 != golden ffe18c8279bf419d9b0aad0f5e03901874d3440506066d93ede75820f2eba183 — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 41216 / 1

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
| `manifest.json` | `bf0800fdfca749e26cd1f470372cf0426dd9fdf28f9274edb014e5ea4e567b4b` |
| `run.out` | `b544e84bf3cc57bfb3e443f951e46523e8bd553dcaeb79867f6a5bc49f86f0b8` |
| `run.err` | `d0903335a494a11f367331e8ebf85f0386bced2f2cc85a825bb6415899e45a03` |
| `stats.txt` | `ded8be0d3662ee3849e4753094d69468188600bc8498040c61bbee6b81fecaaf` |
| `oracle.json` | `068b1fe97a479bacb47c215d2bbf334895661d7d463d2dba1034c9ebbd2a34f6` |
| `chain_report.json` | `9164f4c7b84b752467580bd30a0a6fac6b9f7c37fc785f11ac54043690f03cfb` |
| `census/fpu_injections.log` | `2b19dc8502ca5832c97dc669a6441c91dbe3fdddd1e53b729d2e449b6b86c45d` |
| `inject/fpu_injections.log` | `7c3d8d2077d2f07ff6975a7140293fcd2dcc4259f02c76801effe53010eb6c2a` |
| `inject/prop_evt.txt.gz` | `7aa45e984e1b43eee3955d4bcb6e4bb917db76d2361b5903913b5cc7f9d67512` |
| `inject/stats.txt` | `ded8be0d3662ee3849e4753094d69468188600bc8498040c61bbee6b81fecaaf` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `9457531948999dd8241e6c6ad6fb85d0e529d5b7017f238d23c36b3d2302e28d` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe` | `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
