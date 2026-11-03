# FSU-FP04-F0-W5-2MM-DECODE-GATE seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F0-W5-2MM-DECODE-GATE` |
| 模型/子模型 | FP04 / FP04-a |
| 单元/频率/负载 | FSU Pipe / F0 / W5 |
| workload identity | W5-polybench-2mm-72-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/ooo/polybench/2mm/2mm`（SHA-256 `996168f090560f98a9c1698bdc5663ff95535173861f96db91517c1fac6ee6f3`） |
| manifest | `runs/fsu-gates/F0-W5-2MM-DECODE-gate/FSU-FP04-F0-W5-2MM-DECODE-GATE/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `62f2f55a75fa1f8c9097ede2d6dfaae4a649c521b1609787d903e838a993740e`） |
| 源码 HEAD | `68f1127488d909ab4ce74a98d7270f894ad861da` |
| 分析工具 SHA-256 | `fe2fe930cb85198d8c55f5e13d2165e86857223cf05a955252aafef4213a6bc3` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F0-W5-2MM-DECODE-gate/FSU-FP04-F0-W5-2MM-DECODE-GATE/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/ooo/polybench/2mm/2mm --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F0 --fsu_load W5 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F0-W5-2MM-DECODE-gate/FSU-FP04-F0-W5-2MM-DECODE-GATE/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/ooo/polybench/2mm/2mm --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F0 --fsu_load W5 --fsu_submodel FP04-a --fpu_bitseg sign --fpu_precision fp32 --fpu_lane_width 32 --fpu_lane_offset 0 --fpu_decode_guard --config_profile B0 --fpu_events_to_skip 698409 --chaos_propagation --prop_run_id FSU-FP04-F0-W5-2MM-DECODE-GATE --prop_sample_run_id s1 --fsu_eligible_total 1145697` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 1145697 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 1550758055 / 4027943 |
| sn / PC / opcode | 3549471 / 0x0000000000400768 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 32@0 |
| precision / reg_class | fp32 / vec |
| instruction_bits / decoded_kind | 0x1f020401 / scalar_vfp |
| decoded precision / element width / lanes | fp32 / 32 / 1 |
| manifest precision / lane width / offset | fp32 / 32 / 0 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 31..31 |
| fault bit（绝对）/ bit_in_lane | 31 / 31 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x0000000080000000 / 0x00000000000000000000000080000000 |
| eligible ordinal / total | — / 1145697 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 1550758055, Site: dyn_inst_execute, opClass=8, sn=3549471, bitseg=sign, precision=fp32, lane_width=32, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x80000000, faults_injected: 1
CHAOS_DECODE_REJECTS=20774
CHAOS_DECODE_REJECT_REASON undecoded:fcvt/int-convert=20774
CHAOS_DECODE_KIND scalar_vfp=698410
CHAOS_DECODE_KIND unreliable=20780
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x41b717b3 → 0xc1b717b3 |
| full 128-bit old/new | 0x00000000000000000000000041b717b3 → 0x000000000000000000000000c1b717b3 |
| old/new hash | 0x19c7efedbced1765 → 0xc2565aaf1537e5e5 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 32 |
| opClass / FU / FPCR / FPSR | fmadd / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x41b717b3 / 0xc1b717b3 |
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
| fault_applied | 0 | — | 1550758055 | 1 | 3549471 | 0x0000000000400768 | fmadd | —/— | 45 | — | 32@0 | 0x41b717b3→0xc1b717b3 | — | — | origin |
| carrier_state | 1 | 0 | 1550758055 | 1 | 3549471 | 0x0000000000400768 | fmadd | —/— | 45 | — | 32@0 | 0x41b717b3→0xc1b717b3 | — | — | fsu_taint |
| operand_read | 2 | 1 | 1550762290 | 1 | 3549480 | 0x0000000000400768 | fmadd | 3549471/3549480 | 45 | 5 | 32@0 | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 1550762290 | 1 | 3549480 | 0x0000000000400768 | fmadd | 3549471/3549480 | 45 | 5 | 32@0 | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 1550762290 | 1 | 3549480 | 0x0000000000400768 | fmadd | 3549471/3549480 | 45 | 5 | 32@0 | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 1550763060 | 1 | 3549480 | 0x0000000000400768 | fmadd | —/3549480 | — | — | 32@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 2796094840 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, checksum 2684d4fb3fad8484 != golden 41ebd3d0a77ab3d2 — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 1145697 / 1

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
| `manifest.json` | `a402880526e01fcfbb638bcc693e2947d550929864345f05cabbfc22e36e1e38` |
| `run.out` | `1488f77bef30c5d8f8935efe7046e8d779d7abc2be8f8283ceb8e71490fa547c` |
| `run.err` | `18a80f4e783c90c9cbdf08583487ac2f29f40e9c980ec20ed79816cdf5ec472d` |
| `stats.txt` | `b2610438d14ce7e52617d5190690f40147d214aa44c270bc3fd5f46088fb4666` |
| `oracle.json` | `01a2e93cc4b748ee880b3fd4ea59ec398fdfea9f119ffee7134baac0af8b99e1` |
| `chain_report.json` | `3dec6f326a842481f934735d1599b7b0a7253009d4e962ca7315689ba392c5fd` |
| `census/fpu_injections.log` | `2f6133b16ba65b0e693d416d630b18dae5c2d3f081e613e9ac53970a803798b7` |
| `inject/fpu_injections.log` | `dc64d6d40c339e7a7e90f6167d24fffde930a08359d7ea8f934e74d817806fe8` |
| `inject/prop_evt.txt.gz` | `008cdaa9e6272e46f257787ed62dbc4a343f4fbdb94fc006fb6cc04bf4e3d400` |
| `inject/stats.txt` | `b2610438d14ce7e52617d5190690f40147d214aa44c270bc3fd5f46088fb4666` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `62f2f55a75fa1f8c9097ede2d6dfaae4a649c521b1609787d903e838a993740e` |
| workload `/home/sdc/gem5-fi-fsu/workloads/ooo/polybench/2mm/2mm` | `996168f090560f98a9c1698bdc5663ff95535173861f96db91517c1fac6ee6f3` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
