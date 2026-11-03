# FSU-FR03-F5-W3 seed3 完整传播链

> 本文只使用本 seed（sample_run_id=`s3`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FR03-F5-W3` |
| 模型/子模型 | FR03 / FR03 |
| 单元/频率/负载 | FSU Pipe / F5 / None |
| workload identity | W3-neon-fp32-lane-v1 |
| seed / sample_run_id | 3 / `s3` |
| selection seed / injection seed | 3 / 3 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel`（SHA-256 `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92`） |
| manifest | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W3/seed3/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `04be57c3a2383fb53b1beff2b4358abe1c8c589baae7808228ed593db5344dda`） |
| 源码 HEAD | `f7473c545c2483f5cc74c720405a8188725f7d11` |
| 分析工具 SHA-256 | `3417b6abebea8a683f348584cf87cfc34d56863fbd004813bfa929fd10bbc6b9` |
| census 命令 | `` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d /home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W3/seed3/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_phys --phys_mode phys --phys_target_idx 0 --phys_reg_class vector --vec_lane_width 32 --vec_lane_offset 0 --fault_mask 8355840 --fault_type stuck_at_zero --phys_require_allocated --bits_to_change 1 --phys_semantic_role FR03 --config_profile B0 --chaos_propagation --prop_run_id FSU-FR03-F5-W3 --prop_sample_run_id s3 --fsu_eligible_total 0` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 0 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

### 1.1 永久故障安装与存续

| 项 | 值 |
|---|---|
| 安装次数（fault_installed） | 1 |
| install event_id / fault_id | `0` / `1` |
| install eligible ordinal / install_is_exposure | — / 1 |
| warm-up configured / eligible skipped | — / — |
| fixed mask / polarity | 0x7f8000 / 0 |
| 存续起点（first_eligible_sn） | — |
| 最近 exposure sn / 终局 sn | 10196 / 10196 |

安装事件本身是 **exposure #1**；安装后每个匹配 eligible event 都重新施加同一固定 mask/polarity，直到运行结束。

### 1.2 全量 exposure 计数

| 项 | 值 |
|---|---|
| fault-run eligible_seen_total | — |
| warm-up skipped + post-install eligible | — + — |
| eligible_without_writable_dest | — |
| exposures_total（含安装当次） | 8 |
| activated_exposure_count | 2 |
| selected_eligible_total（census 参考） | — |
| eligible_delta_vs_census | — |
| census_reference | — |

fault-run eligible 与预注册 census **不要求相等**；`eligible_delta_vs_census` 只作算术记录，不是错误。

### 1.3 采样策略

| 项 | 值 |
|---|---|
| sample policy | `first_of_generation+first_activated+cap` |
| sampled / dropped | 8 / 0 |
| sampled_unique / omitted | — / — |
| applied_to_all_exposures / sampled_is_observation_only | — / — |
| cell_sources_overflow | — |

**sampled / dropped 只是事件流观测采样统计，不表示故障未施加。** `applied_to_all_exposures=1` 表示每个 eligible event 都真实施加了同一永久极性；采样只决定保留多少条可读 exposure 事件。

### 1.4 已完整观测的路径

- 主 fault `1` 的完整观测路径（直接 parent 链）：`0` → `1` → `2` → `3` → `8` → `23` → `38` → `53` → `65` → `77` → `6169` → `6170` → `6171`
- 该路径的 chain terminal：**full**；路径 admitted/certified 标记：False / False。
- `fsu_chain_check` 的 certified 只认证这条**已记录、已完整观测**的路径；它不声称所有 exposure 都被逐条展开或逐条认证。

### 1.5 未逐条展开的 exposure

- 未采样 exposure（omitted / exposures_dropped）：— 条，只保留精确计数，不保留逐条值。
- 同一物理 cell 的多来源摘要：merged_activated_exposures=N/A，observed_exposure_ids=`N/A`，sources_expanded=N/A，sources_unexpanded=N/A，observation_scope=N/A。
- 同一 consumer 受同一 phys cell 的多次 activated exposure 影响时，L2 `operand_read` 携带上述**有界摘要**：第一条来源（first activated chain）被展开为真实 L2–L5 链，其余来源只计数、不逐条展开；绝不静默只保留第一条来源。

### 1.6 run-level oracle（与 fault chain terminal 分开）

- run-level 程序 oracle：**Masked**（completed exit=0, ARRAYHASH==golden (cb66197d92c7656b...) — fault did not propagate）。
- fault chain terminal：**full**。
- 二者是不同层级的事实：run-level oracle 是程序最终结果，chain terminal 是这条已观测故障路径的结局；本文并列保留，不互相替代（详见第 7 节）。

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 0 / 0 |
| sn / PC / opcode | — / — / — |
| 单元/结构/slot/port/lane | PRF_Vec / permanent_stuck / — / — / 32@0 |
| precision / reg_class | fp32 / vec |
| instruction_bits / decoded_kind | — / — |
| decoded precision / element width / lanes | — / — / — |
| manifest precision / lane width / offset | — / — / — |
| decoded reliable / precision_match / lane_match | — / — / — |
| field 范围（lane 内） | —..— |
| fault bit（绝对）/ bit_in_lane | 15 / 15 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x7f8000 / 0x7f8000 |
| eligible ordinal / total | — / — |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
（无）
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x0 → 0x0 |
| full 128-bit old/new | — → — |
| old/new hash | — → — |
| source/destination phys tag | src=— / dest=0 |
| operand role / lane / width | — / 0 / 32 |
| opClass / FU / FPCR / FPSR | — / — / permanent_stuck / N/A（事件未携带则不为推测） |
| correct/fault result | 0x0 / 0x0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

### fault 1（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_installed | L0 | 0 | — |
| 2 | exposure | — | 1 | 0 |
| 3 | carrier_state | L1 | 2 | 1 |
| 4 | generation_change | — | 3 | 2 |
| 5 | generation_change | — | 8 | 3 |
| 6 | generation_change | — | 23 | 8 |
| 7 | generation_change | — | 38 | 23 |
| 8 | generation_change | — | 53 | 38 |
| 9 | generation_change | — | 65 | 53 |
| 10 | generation_change | — | 77 | 65 |
| 11 | carrier_state | L1 | 6169 | 77 |
| 12 | operand_read | L2 | 6170 | 6169 |
| 13 | commit | L5 | 6171 | 6170 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_installed | 0 | — | 0 | 1 | — | — | — | —/— | 0 | — | 32@0 | 0x0→0x0 | — | — | origin |
| exposure | 1 | 0 | 0 | 1 | — | — | — | —/— | 0 | — | 32@0 | 0x0→0x0 | — | — | fsu_taint |
| carrier_state | 2 | 1 | 0 | 1 | — | — | — | —/— | 0 | — | 32@0 | 0x0→0x0 | — | — | fsu_taint |
| generation_change | 3 | 2 | 8813805 | 1 | — | — | — | —/— | 0 | — | 32@0 | —→— | — | — | fsu_taint |
| generation_change | 8 | 3 | 11642785 | 1 | — | — | — | —/— | 0 | — | 32@0 | —→— | — | — | fsu_taint |
| generation_change | 23 | 8 | 11748275 | 1 | — | — | — | —/— | 0 | — | 32@0 | —→— | — | — | fsu_taint |
| generation_change | 38 | 23 | 11757900 | 1 | — | — | — | —/— | 0 | — | 32@0 | —→— | — | — | fsu_taint |
| generation_change | 53 | 38 | 11767525 | 1 | — | — | — | —/— | 0 | — | 32@0 | —→— | — | — | fsu_taint |
| generation_change | 65 | 53 | 11772915 | 1 | — | — | — | —/— | 0 | — | 32@0 | —→— | — | — | fsu_taint |
| generation_change | 77 | 65 | 11781000 | 1 | — | — | — | —/— | 0 | — | 32@0 | —→— | — | — | fsu_taint |
| carrier_state | 6169 | 77 | 32870530 | 1 | — | — | — | —/— | 0 | — | 32@0 | 0x3e800000→0x3e800000 | — | — | fsu_taint |
| operand_read | 6170 | 6169 | 32870530 | 1 | 83313 | 0x400620 | fmadd | —/83313 | 0 | — | 32@0 | 0x3e800000→0x3e800000 | — | — | fsu_taint |
| commit | 6171 | 6170 | 32871300 | 1 | 83313 | 0x400620 | fmadd | —/83313 | 0 | — | 32@0 | 0x3e800000→0x3e800000 | L5 | errant_commit | fsu_taint |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_installed#0（本 seed 真实事件）。
- **L1**：carrier_state#2；carrier_state#6169（本 seed 真实事件）。
- **L2**：operand_read#6170（本 seed 真实事件）。
- **L3**：N/A（本 seed 真实未到达；chain.layers_na 显式记录）。
- **L4**：N/A（本 seed 真实未到达；chain.layers_na 显式记录）。
- **L5**：commit#6171（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**Masked**（completed exit=0, ARRAYHASH==golden (cb66197d92c7656b...) — fault did not propagate）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：False / False
- violations（主 fault）：['activation_chain_not_through_first_activated']
- truncated / evidence_truncated：False / False
- 事件数：6179
- attempted / eligible / activated：1 / 0 / 0

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | False | False | ['activation_chain_not_through_first_activated'] | 6171 | N/A / N/A |

- 结局标签（run-level oracle）：Masked/contained

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_installed) → `1` (exposure)；child.parent=0 ✓
- `1` (exposure) → `2` (carrier_state)；child.parent=1 ✓
- `2` (carrier_state) → `3` (generation_change)；child.parent=2 ✓
- `3` (generation_change) → `8` (generation_change)；child.parent=3 ✓
- `8` (generation_change) → `23` (generation_change)；child.parent=8 ✓
- `23` (generation_change) → `38` (generation_change)；child.parent=23 ✓
- `38` (generation_change) → `53` (generation_change)；child.parent=38 ✓
- `53` (generation_change) → `65` (generation_change)；child.parent=53 ✓
- `65` (generation_change) → `77` (generation_change)；child.parent=65 ✓
- `77` (generation_change) → `6169` (carrier_state)；child.parent=77 ✓
- `6169` (carrier_state) → `6170` (operand_read)；child.parent=6169 ✓
- `6170` (operand_read) → `6171` (commit)；child.parent=6170 ✓

- L5 真实见证：`6171` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `0cb15abfe2c84e4dd76f8fe82ed3083c01f036846969fcbccea306e2ba98c4a7` |
| `run.out` | `d3cba48917d5f160bca4165c296d79f48535ce1ffba450b069d4b284bb58a4a9` |
| `run.err` | `dec72566590bdc5e161de8212087044774786c74f89964911cc196ef6b1ff992` |
| `stats.txt` | `579f08beed85c01aad450d6c114f67501f287d87c7f1fa2da1a319c43eadcd52` |
| `oracle.json` | `a6e6801385d7a8b77d6399cecb0bd584c149e9b691c16d36a6b870c46ad2b769` |
| `chain_report.json` | `45222fac0898fd906b000b8964bee2f7ed7e5d3c3c2b3c1c918f7586f7ca8052` |
| `inject/prop_evt.txt.gz` | `0e7642fc3ab6ef1590d957ddd8bd36d1626b0b25d55ba97d658b976cf83acd47` |
| `inject/stats.txt` | `579f08beed85c01aad450d6c114f67501f287d87c7f1fa2da1a319c43eadcd52` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `04be57c3a2383fb53b1beff2b4358abe1c8c589baae7808228ed593db5344dda` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/neon_fp32_lane_kernel` | `d8b01bc0ac140f43c4f7462e1f3b376802e75dfeaca40a0257b4cad5ede92a92` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
