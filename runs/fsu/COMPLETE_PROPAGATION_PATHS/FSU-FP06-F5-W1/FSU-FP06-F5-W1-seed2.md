# FSU-FP06-F5-W1 seed2 完整传播链

> 本文只使用本 seed（sample_run_id=`s2`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP06-F5-W1` |
| 模型/子模型 | FP06 / FP06-b |
| 单元/频率/负载 | FSU Pipe / F5 / W1 |
| workload identity | W1-fp-scalar-probe-v1 |
| seed / sample_run_id | 2 / `s2` |
| selection seed / injection seed | 2 / 2 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe`（SHA-256 `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754`） |
| manifest | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W1/seed2/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `3a087f34b59912518e37c410689175d1d4923d4271cab453730bf574bfd75a62`） |
| 源码 HEAD | `52fece882d56985bdd32560aaef6cd9fc363482e` |
| 分析工具 SHA-256 | `f1a139d8e3777cc0b30c28f1e138574dc74ea5acfd3f4a341e09d20f5a2c932a` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W1/seed2/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 9223372036854775808 --fpu_rng_seed 2 --fpu_permanent_stuck --fpu_stuck_polarity 1 --fpu_f5_warmup 1024 --fpu_f5_sample_limit 1024 --fpu_f5_keep_first_last_n 256 --fsu_model FP06 --fsu_freq F5 --fsu_load W1 --fsu_submodel FP06-b --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_decode_guard --fpu_op_classes FloatAdd,FloatMult,FloatMultAcc,FloatDiv,FloatSqrt --fpu_reg_class vec --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W1/seed2/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 9223372036854775808 --fpu_rng_seed 2 --fpu_permanent_stuck --fpu_stuck_polarity 1 --fpu_f5_warmup 1024 --fpu_f5_sample_limit 1024 --fpu_f5_keep_first_last_n 256 --fsu_model FP06 --fsu_freq F5 --fsu_load W1 --fsu_submodel FP06-b --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_decode_guard --fpu_op_classes FloatAdd,FloatMult,FloatMultAcc,FloatDiv,FloatSqrt --fpu_reg_class vec --config_profile B0 --chaos_propagation --prop_run_id FSU-FP06-F5-W1 --prop_sample_run_id s2 --fsu_eligible_total 41216` |
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
| 安装 fault_id / mask / polarity | 1 / 0x8000000000000000 / 1 |
| 已记录 exposure 事件 | 514 |
| 已记录 activated exposure | 333 |
| 全程 exposures_total | 40192 |
| sampled / dropped | 514 / 39678 |
| 全程 activated_exposure_count | 25543 |
| sample policy | `bounded_first_last(limit=1024,first=256,last=256)` |
| terminal | committed |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 53823000 / 139800 |
| sn / PC / opcode | 42400 / 0x0000000000400e20 / fdiv |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 64@0 |
| precision / reg_class | fp64 / vec |
| instruction_bits / decoded_kind | 0x1e611800 / scalar_vfp |
| decoded precision / element width / lanes | fp64 / 64 / 1 |
| manifest precision / lane width / offset | fp64 / 64 / 0 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 63..63 |
| fault bit（绝对）/ bit_in_lane | 63 / 63 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x8000000000000000 / 0x00000000000000008000000000000000 |
| eligible ordinal / total | — / 41216 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 3297799120, Site: dyn_inst_execute, opClass=8, sn=11165301, mode=permanent_stuck, polarity=1, exposure=40191, activated_exposures=25542, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
Tick: 3297937335, Site: dyn_inst_execute, opClass=11, sn=11165852, mode=permanent_stuck, polarity=1, exposure=40192, activated_exposures=25543, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
CHAOS_DECODE_REJECTS=41216
CHAOS_DECODE_REJECT_REASON precision_mismatch=41216
CHAOS_DECODE_KIND scalar_vfp=82432
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x8000000000000000 → 0x8000000000000000 |
| full 128-bit old/new | 0x00000000000000008000000000000000 → 0x00000000000000008000000000000000 |
| old/new hash | 0x47fe8d7eaf8f2b63 → 0x47fe8d7eaf8f2b63 |
| source/destination phys tag | src=— / dest=3 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fdiv / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x8000000000000000 / 0x8000000000000000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

### fault 1（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_installed | L0 | 0 | — |
| 2 | carrier_state | L1 | 1 | 0 |
| 3 | exposure | — | 3 | 1 |
| 4 | operand_read | L2 | 4 | 3 |
| 5 | execute | L3 | 5 | 4 |
| 6 | prf_writeback | L4 | 6 | 5 |
| 7 | commit | L5 | 7 | 6 |
| 8 | chain_end | — | 521 | 7 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_installed | 0 | — | 53823000 | 1 | 42400 | 0x0000000000400e20 | fdiv | —/— | 3 | — | 64@0 | 0x8000000000000000→0x8000000000000000 | — | — | origin |
| carrier_state | 1 | 0 | 53823000 | 1 | 42400 | 0x0000000000400e20 | fdiv | —/— | 3 | — | 64@0 | 0x8000000000000000→0x8000000000000000 | — | — | fsu_taint |
| exposure | 3 | 1 | 53836475 | 1 | 42412 | 0x0000000000400e50 | fmadd | —/— | 3 | — | 64@0 | 0x0010000000000000→0x8010000000000000 | — | — | fsu_taint |
| operand_read | 4 | 3 | 53921945 | 1 | 42459 | 0x0000000000400f0c | fmov | 42412/42459 | 3 | 2 | 64@0 | —→— | — | — | fsu_taint |
| execute | 5 | 4 | 53921945 | 1 | 42459 | 0x0000000000400f0c | fmov | 42412/42459 | 3 | 2 | 64@0 | —→— | — | — | fsu_taint |
| prf_writeback | 6 | 5 | 53921945 | 1 | 42459 | 0x0000000000400f0c | fmov | 42412/42459 | 3 | 2 | 64@0 | —→— | — | — | fsu_taint |
| commit | 7 | 6 | 53922715 | 1 | 42459 | 0x0000000000400f0c | fmov | —/42459 | — | — | 64@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 521 | 7 | 3303126365 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | committed | fsu_taint |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_installed#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#4（本 seed 真实事件）。
- **L3**：execute#5（本 seed 真实事件）。
- **L4**：prf_writeback#6（本 seed 真实事件）。
- **L5**：commit#7（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH ffe18c8279bf419d7a543c9532aa579874d3440506066d93ede75820f2eba183 != golden ffe18c8279bf419d9b0aad0f5e03901874d3440506066d93ede75820f2eba183 — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：522
- attempted / eligible / activated：1 / 41216 / 1

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 7 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_installed) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `3` (exposure)；child.parent=1 ✓
- `3` (exposure) → `4` (operand_read)；child.parent=3 ✓
- `4` (operand_read) → `5` (execute)；child.parent=4 ✓
- `5` (execute) → `6` (prf_writeback)；child.parent=5 ✓
- `6` (prf_writeback) → `7` (commit)；child.parent=6 ✓
- `7` (commit) → `521` (chain_end)；child.parent=7 ✓

- L5 真实见证：`7` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `7a77b406f225c73d1e12e173d2f6dbd8cb4b39af22b716a450fd5c0eeb75b4ed` |
| `run.out` | `7995a79ce50fc80444542445981c3d1df4edf9c09d76bd7d76cc0f451a51daa1` |
| `run.err` | `70c903c6b501403db8b5162ced9bbf43f40b13e120d7c1df4354edaa225c9f68` |
| `stats.txt` | `38c590fa31dba32f99f9b1020b0b9da7f88ba0b9a9e3c0d7ef8ce322f4b5ef06` |
| `oracle.json` | `afd507e3e5fb65ee059996b1088849418349bb78f6bb3e8b027ec0bc951517c4` |
| `chain_report.json` | `36fdbe524f7ea6f622f68869f7a757c05559d4ba0deec0ecabdc8062638ac3ba` |
| `census/fpu_injections.log` | `d67017f3f31c70fbc2701f1c9beba3218141f12e8cabfe43558cc4a2997c42f1` |
| `inject/fpu_injections.log` | `ed40bdfe5a17fad6073a603a50b7bde7416fe1ab6d3e953b729825d673d622e0` |
| `inject/prop_evt.txt.gz` | `ea847507353aa0d4da588eba2858bd19dad400da8a9ef52bc892fd229ba3af90` |
| `inject/stats.txt` | `38c590fa31dba32f99f9b1020b0b9da7f88ba0b9a9e3c0d7ef8ce322f4b5ef06` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `3a087f34b59912518e37c410689175d1d4923d4271cab453730bf574bfd75a62` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/w1_fp_scalar_probe` | `c2b8a553bd44c87faaa3d8130d8a897097dc53c4e1627cb2b09b32a59e914754` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
