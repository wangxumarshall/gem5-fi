# FSU-FP04-F0-W4 seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F0-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F0 / W4 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel`（SHA-256 `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97`） |
| manifest | `runs/fsu/FSU-FP04-F0-W4/seed1/attempt-2/manifest.json` |
| gem5 二进制 | `CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `f9a7cd9b4de6a47dbaceaa4dac0b58bbf8ba5bbbe8f1c8241a9e71be7af98c32`） |
| 源码 HEAD | `8e86d1ba0421741f96bd5986da7a4cdb9dae48a7` |
| 分析工具 SHA-256 | `b3a087a059ee22082d3a21c00916f24642f7e5148f340d8c3d305ca75a1e26ab` |
| census 命令 | `CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed1/attempt-2/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F0 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W4/seed1/attempt-2/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F0 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 45070 --chaos_propagation --prop_run_id FSU-FP04-F0-W4 --prop_sample_run_id s1 --fsu_eligible_total 57347` |

## 2. 故障注入发生在哪里

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 80411485 / 208861 |
| sn / PC / opcode | 281328 / 0x00000000004005e0 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| attempted / eligible / activated | 1 / 57347 / 1 |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 80411485, Site: dyn_inst_execute, opClass=6, sn=281328, bitseg=mant_lo, mask=0x20, faults_injected: 1
```

## 3. 注入前后状态

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080580000000000 → 0x4080580000000020 |
| old/new hash | 0xb5f5e5800f5cca3b → 0x954e46a16d4534db |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080580000000000 / 0x4080580000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

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
| fault_applied | 0 | — | 80411485 | 1 | 281328 | 0x00000000004005e0 | scvtf | —/— | 6 | — | 64@0 | 0x4080580000000000→0x4080580000000020 | — | — | origin |
| carrier_state | 1 | 0 | 80411485 | 1 | 281328 | 0x00000000004005e0 | scvtf | —/— | 6 | — | 64@0 | 0x4080580000000000→0x4080580000000020 | — | — | fsu_taint |
| operand_read | 2 | 1 | 80413410 | 1 | 281331 | 0x00000000004005ec | fmadd | 281328/281331 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 80413410 | 1 | 281331 | 0x00000000004005ec | fmadd | 281328/281331 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 80413410 | 1 | 281331 | 0x00000000004005ec | fmadd | 281328/281331 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 80414180 | 1 | 281331 | 0x00000000004005ec | fmadd | —/281331 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 6 | 5 | 232548855 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

## 7. 最终结局

- 程序 oracle：**SDC**（completed exit=0, ARRAYHASH ced113fdd122842d91a79059d75e2a24f55f78de0e043ff75540c666a1cc6e6f != golden ced113fdd122842d91a79059d75e2a24f55f78de0e043ff761239d5d989f43e7 — silent data corruption）
- 传播链 terminal：**full**
- provable_to：L5
- admitted / certified：True / True
- violations：[]
- truncated / evidence_truncated：False / False
- 事件数：7
- attempted / eligible / activated：1 / 57347 / 1
- L5 见证事件：5
- 含住事件/层级：N/A / N/A
- 结局标签：SDC

## 8. 为什么该结局成立

主链每一条边均验证为直接 parent：

- `0` (fault_applied) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `2` (operand_read)；child.parent=1 ✓
- `2` (operand_read) → `3` (execute)；child.parent=2 ✓
- `3` (execute) → `4` (prf_writeback)；child.parent=3 ✓
- `4` (prf_writeback) → `5` (commit)；child.parent=4 ✓
- `5` (commit) → `6` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—
- 传播链结局与程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `64928159edf575aa63d00267d5941c3e4628c6c315caea36881362fde00e071b` |
| `run.out` | `4e6de5b1b6d7f9dad6fa6c2ab0350c14ba85dbcd125768d69f56bcca5a1d07aa` |
| `run.err` | `89736f20b2030718beca99e4246b7e20e1e59dfcdbda8d07067bff6783a4a5dc` |
| `stats.txt` | `e0578a07d69abbc86917951a260c913bd1a30dad9ef2d11478f363c2a2dce8ca` |
| `oracle.json` | `7e3ec8cd111aeaa35bc40bd43218ae1855891bef8cea63c51652df500b849b86` |
| `chain_report.json` | `be543d6990cdf710d0f6de17f3aed344a2abfd4718149b9ec5a09dd2377b0009` |
| `census/fpu_injections.log` | `7bc8726ba761e237b918a253b4aa17afe92f63b6fb33bcdbe3233ab77f314a00` |
| `inject/fpu_injections.log` | `0d5775df20677dcf9a9e9ae411d04d96ae5b842f928b419a08f582761a609dcd` |
| `inject/prop_evt.txt.gz` | `18fab2087555ee3260ce76dc9226aebaa9c5089b3a4e28791478514dc536c706` |
| `inject/stats.txt` | `e0578a07d69abbc86917951a260c913bd1a30dad9ef2d11478f363c2a2dce8ca` |
| gem5 二进制 `CHAOS/gem5/build/ARM/gem5.opt` | `f9a7cd9b4de6a47dbaceaa4dac0b58bbf8ba5bbbe8f1c8241a9e71be7af98c32` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel` | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
