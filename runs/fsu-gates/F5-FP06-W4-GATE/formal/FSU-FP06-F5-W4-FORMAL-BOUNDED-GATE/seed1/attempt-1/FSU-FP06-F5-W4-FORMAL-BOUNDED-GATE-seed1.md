# FSU-FP06-F5-W4-FORMAL-BOUNDED-GATE seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP06-F5-W4-FORMAL-BOUNDED-GATE` |
| 模型/子模型 | FP06 / FP06-a |
| 单元/频率/负载 | FSU Pipe / F5 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu-gates/F5-FP06-W4-GATE/formal/FSU-FP06-F5-W4-FORMAL-BOUNDED-GATE/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `d6aa580b80bcd021953ad73c10bb769c32900de6525768a9eb0bef5ddd6261b6`） |
| 源码 HEAD | `f7473c545c2483f5cc74c720405a8188725f7d11` |
| 分析工具 SHA-256 | `654072132a67485b81dacb73ac11b3d55ef19a4288a0427291f28b1e8f29a6c5` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F5-FP06-W4-GATE/formal/FSU-FP06-F5-W4-FORMAL-BOUNDED-GATE/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 9223372036854775808 --fpu_rng_seed 1 --fpu_permanent_stuck --fpu_stuck_polarity 0 --fpu_f5_warmup 1024 --fpu_f5_sample_limit 1024 --fpu_f5_keep_first_last_n 256 --fsu_model FP06 --fsu_freq F5 --fsu_load W4 --fsu_submodel FP06-a --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_decode_guard --config_profile B0 --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu-gates/F5-FP06-W4-GATE/formal/FSU-FP06-F5-W4-FORMAL-BOUNDED-GATE/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 9223372036854775808 --fpu_rng_seed 1 --fpu_permanent_stuck --fpu_stuck_polarity 0 --fpu_f5_warmup 1024 --fpu_f5_sample_limit 1024 --fpu_f5_keep_first_last_n 256 --fsu_model FP06 --fsu_freq F5 --fsu_load W4 --fsu_submodel FP06-a --fpu_precision fp64 --fpu_lane_width 64 --fpu_lane_offset 0 --fpu_decode_guard --config_profile B0 --chaos_propagation --prop_run_id FSU-FP06-F5-W4-FORMAL-BOUNDED-GATE --prop_sample_run_id s1 --fsu_eligible_total 1310723` |
| rate（divisor/jitter/warmup） | N/A / ±N/A% / N/A |
| eligible_total | 1310723 |
| ordinals（index: ordinal） | N/A |
| ordinals SHA-256 | `N/A` |
| 注入数（actual/expected） | 1 / None |
| fault 数（事件流/injection log） | 1 / 1 |

### 1.1 永久故障安装与存续

| 项 | 值 |
|---|---|
| 安装次数（fault_installed） | 1 |
| install event_id / fault_id | `0` / `1` |
| install eligible ordinal / install_is_exposure | 1025 / 1 |
| warm-up configured / eligible skipped | 1024 / 1024 |
| fixed mask / polarity | 0x8000000000000000 / 0 |
| 存续起点（first_eligible_sn） | 23138 |
| 最近 exposure sn / 终局 sn | 13645843 / 23208 |

安装事件本身是 **exposure #1**；安装后每个匹配 eligible event 都重新施加同一固定 mask/polarity，直到运行结束。

### 1.2 全量 exposure 计数

| 项 | 值 |
|---|---|
| fault-run eligible_seen_total | 1310723 |
| warm-up skipped + post-install eligible | 1024 + 1309699 |
| eligible_without_writable_dest | 0 |
| exposures_total（含安装当次） | 1309699 |
| activated_exposure_count | 130814 |
| selected_eligible_total（census 参考） | 1310723 |
| eligible_delta_vs_census | 0 |
| census_reference | pre_registered_countOnly |

fault-run eligible 与预注册 census **不要求相等**；`eligible_delta_vs_census` 只作算术记录，不是错误。

### 1.3 采样策略

| 项 | 值 |
|---|---|
| sample policy | `bounded_first_last(limit=1024,first=256,last=256)` |
| sampled / dropped | 513 / 1309186 |
| sampled_unique / omitted | 513 / 1309186 |
| applied_to_all_exposures / sampled_is_observation_only | 1 / 1 |
| cell_sources_overflow | 0 |

**sampled / dropped 只是事件流观测采样统计，不表示故障未施加。** `applied_to_all_exposures=1` 表示每个 eligible event 都真实施加了同一永久极性；采样只决定保留多少条可读 exposure 事件。

### 1.4 已完整观测的路径

- 主 fault `1` 的完整观测路径（直接 parent 链）：`0` → `1` → `2` → `8` → `9` → `10` → `11` → `520`
- 该路径的 chain terminal：**full**；路径 admitted/certified 标记：True / True。
- `fsu_chain_check` 的 certified 只认证这条**已记录、已完整观测**的路径；它不声称所有 exposure 都被逐条展开或逐条认证。

### 1.5 未逐条展开的 exposure

- 未采样 exposure（omitted / exposures_dropped）：1309186 条，只保留精确计数，不保留逐条值。
- 同一物理 cell 的多来源摘要：merged_activated_exposures=1，observed_exposure_ids=`1:1`，sources_expanded=1，sources_unexpanded=0，observation_scope=first_activated_chain。
- 同一 consumer 受同一 phys cell 的多次 activated exposure 影响时，L2 `operand_read` 携带上述**有界摘要**：第一条来源（first activated chain）被展开为真实 L2–L5 链，其余来源只计数、不逐条展开；绝不静默只保留第一条来源。

### 1.6 run-level oracle（与 fault chain terminal 分开）

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH fef314ec94d903940706ae210475aa3104f40fbffe9114c2971dde7b6f7cf0fe != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）。
- fault chain terminal：**full**。
- 二者是不同层级的事实：run-level oracle 是程序最终结果，chain terminal 是这条已观测故障路径的结局；本文并列保留，不互相替代（详见第 7 节）。

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 17174850 / 44610 |
| sn / PC / opcode | 23138 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / sign / — / — / 64@0 |
| precision / reg_class | fp64 / vec |
| instruction_bits / decoded_kind | 0x1f431000 / scalar_vfp |
| decoded precision / element width / lanes | fp64 / 64 / 1 |
| manifest precision / lane width / offset | fp64 / 64 / 0 |
| decoded reliable / precision_match / lane_match | 1 / 1 / 1 |
| field 范围（lane 内） | 63..63 |
| fault bit（绝对）/ bit_in_lane | 63 / 63 |
| fault mask（lane 内）/ lane_mask（128-bit 绝对） | 0x8000000000000000 / 0x00000000000000008000000000000000 |
| eligible ordinal / total | — / 1310723 |
| rate divisor / jitter / interval / ordinal_index | — / — / — / — |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 5474283430, Site: dyn_inst_execute, opClass=8, sn=13645843, mode=permanent_stuck, polarity=0, exposure=1309699, activated_exposures=130814, precision=fp64, lane_width=64, lane_offset=0, decoded_kind=scalar_vfp, precision_match=1, lane_match=1, mask=0x8000000000000000, faults_injected: 1
CHAOS_DECODE_REJECTS=786432
CHAOS_DECODE_REJECT_REASON undecoded:fcvt/int-convert=786432
CHAOS_DECODE_KIND scalar_vfp=1572868
CHAOS_DECODE_KIND unreliable=1310729
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值（lane 内） | 0xbfdfced916872b02 → 0x3fdfced916872b02 |
| full 128-bit old/new | 0x0000000000000000bfdfced916872b02 → 0x00000000000000003fdfced916872b02 |
| old/new hash | 0xdfeb99b89b1ea248 → 0xdfeb19b89b1dc8c8 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / sign / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfdfced916872b02 / 0x3fdfced916872b02 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

## 4. 之后依次经过哪些真实部件

主链完全由本 seed `parent_event_id` 的直接 parent 边构成；旁支不混入（见 chain_report.off_chain_event_ids）。

### fault 1（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_installed | L0 | 0 | — |
| 2 | carrier_state | L1 | 1 | 0 |
| 3 | exposure | — | 2 | 1 |
| 4 | operand_read | L2 | 8 | 2 |
| 5 | execute | L3 | 9 | 8 |
| 6 | prf_writeback | L4 | 10 | 9 |
| 7 | commit | L5 | 11 | 10 |
| 8 | chain_end | — | 520 | 11 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_installed | 0 | — | 17174850 | 1 | 23138 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfdfced916872b02→0x3fdfced916872b02 | — | — | origin |
| carrier_state | 1 | 0 | 17174850 | 1 | 23138 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfdfced916872b02→0x3fdfced916872b02 | — | — | fsu_taint |
| exposure | 2 | 1 | 17174850 | 1 | 23138 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfdfced916872b02→0x3fdfced916872b02 | — | — | fsu_taint |
| operand_read | 8 | 2 | 17190250 | 1 | 23208 | 0x0000000000400654 | fmadd | 23138/23208 | 6 | 3 | 64@0 | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 17190250 | 1 | 23208 | 0x0000000000400654 | fmadd | 23138/23208 | 6 | 3 | 64@0 | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 17190250 | 1 | 23208 | 0x0000000000400654 | fmadd | 23138/23208 | 6 | 3 | 64@0 | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 17191020 | 1 | 23208 | 0x0000000000400654 | fmadd | —/23208 | — | — | 64@0 | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 520 | 11 | 9500820175 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | committed | fsu_taint |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_installed#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#8（本 seed 真实事件）。
- **L3**：execute#9（本 seed 真实事件）。
- **L4**：prf_writeback#10（本 seed 真实事件）。
- **L5**：commit#11（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH fef314ec94d903940706ae210475aa3104f40fbffe9114c2971dde7b6f7cf0fe != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：1 / None
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：521
- attempted / eligible / activated：1 / 1310723 / 1

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 11 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_installed) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `2` (exposure)；child.parent=1 ✓
- `2` (exposure) → `8` (operand_read)；child.parent=2 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `520` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `b947b3359bee14a22ae2a911625945b7824f392a7ebc12d756da586fc4a4247a` |
| `run.out` | `b3ddd94dddefe05ba88f1238ee46f73892e1c824305df4456b75342606b84584` |
| `run.err` | `279ad18c40c7f2a5d4dc8a3457ee13f80f0a4de3b1539c0601a810b6329e1eab` |
| `stats.txt` | `8ee00c4eec8f83b14a0737c1479963399b3abc9fe818979f316b8793dab9acde` |
| `oracle.json` | `bd1c1410ae8658a892549c6656e7989b3bc7ca8492d9c192975f02b6f8ea1b86` |
| `chain_report.json` | `aedd2ae06276470a0309207ca8b6fe5db0338c49362984365e678e82638eb785` |
| `census/fpu_injections.log` | `bae2f3430d2fe1401d106ccf14c2b63359fe8bd4cd9163da50479c41a706506d` |
| `inject/fpu_injections.log` | `263f690f51ff4caf4658739dac2a1744eee2b37cc1b35392772780f92def8af3` |
| `inject/prop_evt.txt.gz` | `fb98fcd1e2a389d5a5660d64c839f7d5317facd8b51509c513c065bf44540c3f` |
| `inject/stats.txt` | `8ee00c4eec8f83b14a0737c1479963399b3abc9fe818979f316b8793dab9acde` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `d6aa580b80bcd021953ad73c10bb769c32900de6525768a9eb0bef5ddd6261b6` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 1 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
