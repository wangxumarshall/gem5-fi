# FSU-FP06-F5-W4-SAMPLED-GATE seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP06-F5-W4-SAMPLED-GATE` |
| 模型/子模型 | FP06 / FP06-a |
| 单元/频率/负载 | FSU Pipe / F5 / W4 |
| workload identity | W4-short |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel`（SHA-256 `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97`） |
| manifest | `runs/fsu-gates/F5-FP06-W4-GATE/early/FSU-FP06-F5-W4-SAMPLED-GATE/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `d6aa580b80bcd021953ad73c10bb769c32900de6525768a9eb0bef5ddd6261b6`） |
| 源码 HEAD | `f7473c545c2483f5cc74c720405a8188725f7d11` |
| 分析工具 SHA-256 | `654072132a67485b81dacb73ac11b3d55ef19a4288a0427291f28b1e8f29a6c5` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F5-FP06-W4-GATE/early/FSU-FP06-F5-W4-SAMPLED-GATE/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 9223372036854775808 --fpu_rng_seed 1 --fpu_permanent_stuck --fpu_stuck_polarity 0 --fpu_f5_warmup 128 --fpu_f5_sample_limit 1024 --fpu_f5_keep_first_last_n 256 --fsu_model FP06 --fsu_freq F5 --fsu_load W4 --fsu_submodel FP06-a --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_decode_guard --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F5-FP06-W4-GATE/early/FSU-FP06-F5-W4-SAMPLED-GATE/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 9223372036854775808 --fpu_rng_seed 1 --fpu_permanent_stuck --fpu_stuck_polarity 0 --fpu_f5_warmup 128 --fpu_f5_sample_limit 1024 --fpu_f5_keep_first_last_n 256 --fsu_model FP06 --fsu_freq F5 --fsu_load W4 --fsu_submodel FP06-a --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_decode_guard --config_profile B0 --chaos_propagation --prop_run_id FSU-FP06-F5-W4-SAMPLED-GATE --prop_sample_run_id s1 --fsu_eligible_total 32771` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 32771 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

### 1.1 永久故障安装与存续

| 项 | 值 |
|---|---|
| 安装次数（fault_installed） | 1 |
| install event_id / fault_id | `0` / `1` |
| install eligible ordinal / install_is_exposure | 129 / 1 |
| warm-up configured / eligible skipped | 128 / 128 |
| fixed mask / polarity | 0x8000000000000000 / 0 |
| 存续起点（first_eligible_sn） | 10806 |
| 最近 exposure sn / 终局 sn | — / — |

安装事件本身是 **exposure #1**；安装后每个匹配 eligible event 都重新施加同一固定 mask/polarity，直到运行结束。

### 1.2 全量 exposure 计数

| 项 | 值 |
|---|---|
| fault-run eligible_seen_total | — |
| warm-up skipped + post-install eligible | — + — |
| eligible_without_writable_dest | — |
| exposures_total（含安装当次） | — |
| activated_exposure_count | — |
| selected_eligible_total（census 参考） | — |
| eligible_delta_vs_census | — |
| census_reference | — |

fault-run eligible 与预注册 census **不要求相等**；`eligible_delta_vs_census` 只作算术记录，不是错误。

### 1.3 采样策略

| 项 | 值 |
|---|---|
| sample policy | `—` |
| sampled / dropped | — / — |
| sampled_unique / omitted | — / — |
| applied_to_all_exposures / sampled_is_observation_only | — / — |
| cell_sources_overflow | — |

**sampled / dropped 只是事件流观测采样统计，不表示故障未施加。** `applied_to_all_exposures=1` 表示每个 eligible event 都真实施加了同一永久极性；采样只决定保留多少条可读 exposure 事件。

### 1.4 已完整观测的路径

- 主 fault `1` 的完整观测路径（直接 parent 链）：`0` → `1` → `7` → `13` → `14` → `15` → `16`
- 该路径的 chain terminal：**full**；路径 admitted/certified 标记：False / False。
- `fsu_chain_check` 的 certified 只认证这条**已记录、已完整观测**的路径；它不声称所有 exposure 都被逐条展开或逐条认证。

### 1.5 未逐条展开的 exposure

- 未采样 exposure（omitted / exposures_dropped）：— 条，只保留精确计数，不保留逐条值。
- 同一物理 cell 的多来源摘要：merged_activated_exposures=1，observed_exposure_ids=`6:6`，sources_expanded=1，sources_unexpanded=0，observation_scope=first_activated_chain。
- 同一 consumer 受同一 phys cell 的多次 activated exposure 影响时，L2 `operand_read` 携带上述**有界摘要**：第一条来源（first activated chain）被展开为真实 L2–L5 链，其余来源只计数、不逐条展开；绝不静默只保留第一条来源。

### 1.6 run-level oracle（与 fault chain terminal 分开）

- run-level 程序 oracle：**Hang**（exceeded Hang timeout with no program checksum (control-flow corruption: never completed)）。
- fault chain terminal：**full**。
- 二者是不同层级的事实：run-level oracle 是程序最终结果，chain terminal 是这条已观测故障路径的结局；本文并列保留，不互相替代（详见第 7 节）。

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 14562625 / 37825 |
| sn / PC / opcode | 10806 / 0x00000000004005f0 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 64@0 |
| precision / reg_class | fp64 / vec |
| instruction_bits / decoded_kind | 0x1f431421 / scalar_vfp |
| decoded precision / element width / lanes | fp64 / 64 / 1 |
| manifest precision / lane width / offset | fp64 / 64 / 0 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 63..63 |
| fault bit（绝对）/ bit_in_lane | 63 / 63 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x8000000000000000 / 0x00000000000000008000000000000000 |
| eligible ordinal / total | — / 32771 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 31092985, Site: dyn_inst_execute, opClass=8, sn=73951, mode=permanent_stuck, polarity=0, exposure=5262, activated_exposures=906, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
Tick: 31092985, Site: dyn_inst_execute, opClass=8, sn=73950, mode=permanent_stuck, polarity=0, exposure=5263, activated_exposures=906, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
Tick: 31099915, Site: dyn_inst_execute, opClass=8, sn=73985, mode=permanent_stuck, polarity=0, exposure=5264, activated_exposures=906, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
Tick: 31102225, Site: dyn_inst_execute, opClass=8, sn=73987, mode=permanent_stuck, polarity=0, exposure=5265, activated_exposures=906, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
Tick: 31102225, Site: dyn_inst_execute, opClass=8, sn=73986, mode=permanent_stuck, polarity=0, exposure=5266, activated_exposures=906, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0x3ff36c8b43958106 → 0x3ff36c8b43958106 |
| full 128-bit old/new | 0x00000000000000003ff36c8b43958106 → 0x00000000000000003ff36c8b43958106 |
| old/new hash | 0xa797433a2681b58f → 0xa797433a2681b58f |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff36c8b43958106 / 0x3ff36c8b43958106 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

### fault 1（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_installed | L0 | 0 | — |
| 2 | carrier_state | L1 | 1 | 0 |
| 3 | exposure | — | 7 | 1 |
| 4 | operand_read | L2 | 13 | 7 |
| 5 | execute | L3 | 14 | 13 |
| 6 | prf_writeback | L4 | 15 | 14 |
| 7 | commit | L5 | 16 | 15 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_installed | 0 | — | 14562625 | 1 | 10806 | 0x00000000004005f0 | fmadd | —/— | 5 | — | 64@0 | 0x3ff36c8b43958106→0x3ff36c8b43958106 | — | — | origin |
| carrier_state | 1 | 0 | 14562625 | 1 | 10806 | 0x00000000004005f0 | fmadd | —/— | 5 | — | 64@0 | 0x3ff36c8b43958106→0x3ff36c8b43958106 | — | — | fsu_taint |
| exposure | 7 | 1 | 14581105 | 1 | 10879 | 0x00000000004005f4 | fmadd | —/— | 45 | — | 64@0 | 0xbfcf5c28f5c28f5c→0x3fcf5c28f5c28f5c | — | — | fsu_taint |
| operand_read | 13 | 7 | 14597275 | 1 | 10949 | 0x00000000004005ec | fmadd | 10879/10949 | 45 | 3 | 64@0 | —→— | — | — | fsu_taint |
| execute | 14 | 13 | 14597275 | 1 | 10949 | 0x00000000004005ec | fmadd | 10879/10949 | 45 | 3 | 64@0 | —→— | — | — | fsu_taint |
| prf_writeback | 15 | 14 | 14597275 | 1 | 10949 | 0x00000000004005ec | fmadd | 10879/10949 | 45 | 3 | 64@0 | —→— | — | — | fsu_taint |
| commit | 16 | 15 | 14598045 | 1 | 10949 | 0x00000000004005ec | fmadd | —/10949 | — | — | 64@0 | —→— | L5 | errant_commit | fsu_taint |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_installed#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#13（本 seed 真实事件）。
- **L3**：execute#14（本 seed 真实事件）。
- **L4**：prf_writeback#15（本 seed 真实事件）。
- **L5**：commit#16（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**Hang**（exceeded Hang timeout with no program checksum (control-flow corruption: never completed)）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：False / False
- violations（主 fault）：['missing_f5_chain_end', 'truncated_stream']
- truncated / evidence_truncated：True / True
- 事件数：264
- attempted / eligible / activated：1 / 32771 / 1

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | False | False | ['missing_f5_chain_end', 'truncated_stream'] | 16 | N/A / N/A |

- 结局标签（run-level oracle）：Timeout

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_installed) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `7` (exposure)；child.parent=1 ✓
- `7` (exposure) → `13` (operand_read)；child.parent=7 ✓
- `13` (operand_read) → `14` (execute)；child.parent=13 ✓
- `14` (execute) → `15` (prf_writeback)；child.parent=14 ✓
- `15` (prf_writeback) → `16` (commit)；child.parent=15 ✓

- L5 真实见证：`16` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `cb365154f598b4a3042dbe5ce318b9d5e897adb9726d0a0de6728d9a89adff09` |
| `run.out` | `9084bc692dae0035b78154e05128757fb1f230c7f439c2fa562791c1b7072b43` |
| `run.err` | `f32dc759c1a2e7bb63c726cab9c10d30263e837a9aa422db218c1e54d63d5134` |
| `stats.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `oracle.json` | `8e38ed1e0b00c3fa4a7c0ef3901798285228ad7b894dae67e5017f082033b071` |
| `chain_report.json` | `a573f4cbfc4246a1e394b56491b302c4d480295f9ef043ac14cb61515c7ea367` |
| `census/fpu_injections.log` | `078c8d3c8067ea1d531cb994258af50c8fb4f89c28e932c258b511f18505ac54` |
| `inject/fpu_injections.log` | `216b131e0ba36932447b187e62bdea53ff5e39daf1b10365e5129cc575fd978f` |
| `inject/prop_evt.txt.gz` | `bf92cbce74a45e6d351d6b2ab52894d99851edd978a3fd59676f3fb231117202` |
| `inject/stats.txt` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `d6aa580b80bcd021953ad73c10bb769c32900de6525768a9eb0bef5ddd6261b6` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel` | `80e633a0cd4b8f64bdfa09f4bf8b1683f79cefd8140f8fe74bf4c973d1941c97` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
