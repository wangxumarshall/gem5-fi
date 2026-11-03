# FSU-FP06-F5-W1-FP32-MANT-GATE seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP06-F5-W1-FP32-MANT-GATE` |
| 模型/子模型 | FP06 / FP06-c |
| 单元/频率/负载 | FSU Pipe / F5 / W1 |
| workload identity | W1-fp-scalar-probe-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe`（SHA-256 `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754`） |
| manifest | `runs/fsu-gates/F5-FP06-W1-v3/FP32-MANT/runs/FSU-FP06-F5-W1-FP32-MANT-GATE/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `3a087f34b59912518e37c410689175d1d4923d4271cab453730bf574bfd75a62`） |
| 源码 HEAD | `52fece882d56985bdd32560aaef6cd9fc363482e` |
| 分析工具 SHA-256 | `f1a139d8e3777cc0b30c28f1e138574dc74ea5acfd3f4a341e09d20f5a2c932a` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F5-FP06-W1-v3/FP32-MANT/runs/FSU-FP06-F5-W1-FP32-MANT-GATE/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 8355840 --fpu_rng_seed 1 --fpu_permanent_stuck --fpu_stuck_polarity 0 --fpu_f5_warmup 64 --fpu_f5_sample_limit 64 --fpu_f5_keep_first_last_n 8 --fsu_model FP06 --fsu_freq F5 --fsu_load W1 --fsu_submodel FP06-c --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --fpu_op_classes FloatAdd,FloatMult,FloatMultAcc,FloatDiv,FloatSqrt --fpu_reg_class vec --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F5-FP06-W1-v3/FP32-MANT/runs/FSU-FP06-F5-W1-FP32-MANT-GATE/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 8355840 --fpu_rng_seed 1 --fpu_permanent_stuck --fpu_stuck_polarity 0 --fpu_f5_warmup 64 --fpu_f5_sample_limit 64 --fpu_f5_keep_first_last_n 8 --fsu_model FP06 --fsu_freq F5 --fsu_load W1 --fsu_submodel FP06-c --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --fpu_op_classes FloatAdd,FloatMult,FloatMultAcc,FloatDiv,FloatSqrt --fpu_reg_class vec --config_profile B0 --chaos_propagation --prop_run_id FSU-FP06-F5-W1-FP32-MANT-GATE --prop_sample_run_id s1 --fsu_eligible_total 41216` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 41216 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

### F5 永久故障计数（一个 fault，多次 exposure）

| 项 | 值 |
|---|---|
| 安装次数（fault_installed） | 1 |
| 安装 fault_id / mask / polarity | 1 / 0x00000000007f8000 / 0 |
| 已记录 exposure 事件 | 17 |
| 已记录 activated exposure | 15 |
| 全程 exposures_total | 41152 |
| sampled / dropped | 17 / 41135 |
| 全程 activated_exposure_count | 30142 |
| sample policy | `bounded_first_last(limit=64,first=8,last=8)` |
| terminal | committed |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 17616060 / 45756 |
| sn / PC / opcode | 12953 / 0x0000000000400d64 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / permanent_stuck / — / — / 32@0 |
| precision / reg_class | fp32 / vec |
| instruction_bits / decoded_kind | 0x1f010040 / scalar_vfp |
| decoded precision / element width / lanes | fp32 / 32 / 1 |
| manifest precision / lane width / offset | fp32 / 32 / 0 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 15..22 |
| fault bit（绝对）/ bit_in_lane | 15 / 15 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x00000000007f8000 / 0x000000000000000000000000007f8000 |
| eligible ordinal / total | — / 41216 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 3293195675, Site: dyn_inst_execute, opClass=8, sn=11136321, mode=permanent_stuck, polarity=0, exposure=41151, activated_exposures=30141, precision=fp32, lane_width=32, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x7f8000, faults_injected: 1
Tick: 3293565660, Site: dyn_inst_execute, opClass=11, sn=11137860, mode=permanent_stuck, polarity=0, exposure=41152, activated_exposures=30142, precision=fp32, lane_width=32, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x7f8000, faults_injected: 1
CHAOS_DECODE_REJECTS=41216
CHAOS_DECODE_REJECT_REASON precision_mismatch=41216
CHAOS_DECODE_KIND scalar_vfp=82432
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x7fc00000 → 0x7f800000 |
| full 128-bit old/new | 0x0000000000000000000000007fc00000 → 0x0000000000000000000000007f800000 |
| old/new hash | 0xb1263dccc24b67fa → 0x2e30dfc6e67227ba |
| source/destination phys tag | src=— / dest=0 |
| operand role / lane / width | — / 0 / 32 |
| opClass / FU / FPCR / FPSR | fmadd / — / permanent_stuck / N/A（事件未携带则不为推测） |
| correct/fault result | 0x7fc00000 / 0x7f800000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

### fault 1（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_installed | L0 | 0 | — |
| 2 | carrier_state | L1 | 1 | 0 |
| 3 | exposure | — | 2 | 1 |
| 4 | operand_read | L2 | 3 | 2 |
| 5 | execute | L3 | 4 | 3 |
| 6 | prf_writeback | L4 | 5 | 4 |
| 7 | commit | L5 | 6 | 5 |
| 8 | chain_end | — | 24 | 6 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_installed | 0 | — | 17616060 | 1 | 12953 | 0x0000000000400d64 | fmadd | —/— | 0 | — | 32@0 | 0x7fc00000→0x7f800000 | — | — | origin |
| carrier_state | 1 | 0 | 17616060 | 1 | 12953 | 0x0000000000400d64 | fmadd | —/— | 0 | — | 32@0 | 0x7fc00000→0x7f800000 | — | — | fsu_taint |
| exposure | 2 | 1 | 17616060 | 1 | 12953 | 0x0000000000400d64 | fmadd | —/— | 0 | — | 32@0 | 0x7fc00000→0x7f800000 | — | — | fsu_taint |
| operand_read | 3 | 2 | 17631075 | 1 | 12970 | 0x0000000000400da8 | fmov | 12953/12970 | 0 | 2 | 32@0 | —→— | — | — | fsu_taint |
| execute | 4 | 3 | 17631075 | 1 | 12970 | 0x0000000000400da8 | fmov | 12953/12970 | 0 | 2 | 32@0 | —→— | — | — | fsu_taint |
| prf_writeback | 5 | 4 | 17631075 | 1 | 12970 | 0x0000000000400da8 | fmov | 12953/12970 | 0 | 2 | 32@0 | —→— | — | — | fsu_taint |
| commit | 6 | 5 | 17631845 | 1 | 12970 | 0x0000000000400da8 | fmov | —/12970 | — | — | 32@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 24 | 6 | 3298653435 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | committed | fsu_taint |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_installed#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#3（本 seed 真实事件）。
- **L3**：execute#4（本 seed 真实事件）。
- **L4**：prf_writeback#5（本 seed 真实事件）。
- **L5**：commit#6（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 8e8aa18c8954bec99b0aad0f5e03901874d3440506066d93ede75820f2eba183 != golden ffe18c8279bf419d9b0aad0f5e03901874d3440506066d93ede75820f2eba183 — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：25
- attempted / eligible / activated：1 / 41216 / 1

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 6 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_installed) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `2` (exposure)；child.parent=1 ✓
- `2` (exposure) → `3` (operand_read)；child.parent=2 ✓
- `3` (operand_read) → `4` (execute)；child.parent=3 ✓
- `4` (execute) → `5` (prf_writeback)；child.parent=4 ✓
- `5` (prf_writeback) → `6` (commit)；child.parent=5 ✓
- `6` (commit) → `24` (chain_end)；child.parent=6 ✓

- L5 真实见证：`6` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `7de7a6e130097cd6c951564aac5ab765be7231aad6406bae8a40f90c8cc0f881` |
| `run.out` | `46142e4c545f042d4334aa461e04c2afd6da1babf0c4199ba3fd20ac80c05122` |
| `run.err` | `70c903c6b501403db8b5162ced9bbf43f40b13e120d7c1df4354edaa225c9f68` |
| `stats.txt` | `86cc649203205c8d2c70eaa76e96540c50150fffc6935e2d86484019b9c1f29d` |
| `oracle.json` | `19ab2b329aae900b674029485a2b6a8877399d5c97a791e6df154e7a86d039ee` |
| `chain_report.json` | `79923e070e578cb032d764ef5ea5caa0ed43812a3f521d4506b40f8cd5b628d4` |
| `census/fpu_injections.log` | `2b19dc8502ca5832c97dc669a6441c91dbe3fdddd1e53b729d2e449b6b86c45d` |
| `inject/fpu_injections.log` | `325fff283219626e2f64beb17c02a6e7c66a768cfdd85eeadec18c2ed0710cf3` |
| `inject/prop_evt.txt.gz` | `a7216510a090747041e352c9d7110395a191d598cd13ef76d7bf0e16ce3c3fe6` |
| `inject/stats.txt` | `86cc649203205c8d2c70eaa76e96540c50150fffc6935e2d86484019b9c1f29d` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `3a087f34b59912518e37c410689175d1d4923d4271cab453730bf574bfd75a62` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe` | `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
