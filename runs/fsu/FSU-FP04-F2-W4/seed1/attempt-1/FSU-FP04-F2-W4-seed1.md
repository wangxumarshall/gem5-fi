# FSU-FP04-F2-W4 seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F2-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F2 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F2-W4/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `daf8ab06763a23987ea7f9226cd299e2cd56617a` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F2-W4/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F2 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F2-W4/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 21 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 21 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F2 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 91644,170263,274042,355938,418958,548049,690141,778985,831878,968934,1080299,1191475,1250848,1393150,1457548,1569070,1698730,1792874,1876764,1989400,2094621 --fpu_rate_warmup 0 --fsu_rate_divisor 100000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F2-W4 --prop_sample_run_id s1 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 100000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:91644, 1:170263, 2:274042, 3:355938, 4:418958, 5:548049, 6:690141, 7:778985, 8:831878, 9:968934, 10:1080299, 11:1191475, 12:1250848, 13:1393150, 14:1457548, 15:1569070, 16:1698730, 17:1792874, 18:1876764, 19:1989400, 20:2094621 |
| ordinals SHA-256 | `1ef3a0a61e16a6e086a5788f3f6ef2e86e6cc0abe0dca98794e18ef2cf80a1a2` |
| 注入数（actual/expected） | 21 / 21 |
| fault 数（事件流/injection log） | 21 / 21 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 151987605 / 394773 |
| sn / PC / opcode | 562753 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 91644 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 91644 / 0 |
| terminal | full |

### fault 10

| 字段 | 值 |
|---|---|
| 根 event_id | `54` |
| tick / cycle | 1486242835 / 3860371 |
| sn / PC / opcode | 5826493 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 968934 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 137056 / 9 |
| terminal | full |

### fault 11

| 字段 | 值 |
|---|---|
| 根 event_id | `60` |
| tick / cycle | 1655560830 / 4300158 |
| sn / PC / opcode | 6494687 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1080299 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 111365 / 10 |
| terminal | full |

### fault 12

| 字段 | 值 |
|---|---|
| 根 event_id | `66` |
| tick / cycle | 1824587765 / 4739189 |
| sn / PC / opcode | 7161734 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1191475 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 111176 / 11 |
| terminal | full |

### fault 13

| 字段 | 值 |
|---|---|
| 根 event_id | `72` |
| tick / cycle | 1915013870 / 4974062 |
| sn / PC / opcode | 7517988 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1250848 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 59373 / 12 |
| terminal | full |

### fault 14

| 字段 | 值 |
|---|---|
| 根 event_id | `78` |
| tick / cycle | 2131341520 / 5535952 |
| sn / PC / opcode | 8371800 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1393150 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 142302 / 13 |
| terminal | full |

### fault 15

| 字段 | 值 |
|---|---|
| 根 event_id | `84` |
| tick / cycle | 2229355205 / 5790533 |
| sn / PC / opcode | 8758188 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1457548 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 64398 / 14 |
| terminal | full |

### fault 16

| 字段 | 值 |
|---|---|
| 根 event_id | `90` |
| tick / cycle | 2398855305 / 6230793 |
| sn / PC / opcode | 9427320 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1569070 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 111522 / 15 |
| terminal | full |

### fault 17

| 字段 | 值 |
|---|---|
| 根 event_id | `96` |
| tick / cycle | 3154599525 / 8193765 |
| sn / PC / opcode | 10458737 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1698730 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 129660 / 16 |
| terminal | full |

### fault 18

| 字段 | 值 |
|---|---|
| 根 event_id | `102` |
| tick / cycle | 3691763460 / 9588996 |
| sn / PC / opcode | 11212431 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1792874 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 94144 / 17 |
| terminal | full |

### fault 19

| 字段 | 值 |
|---|---|
| 根 event_id | `108` |
| tick / cycle | 4169255090 / 10829234 |
| sn / PC / opcode | 11884087 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1876764 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 83890 / 18 |
| terminal | full |

### fault 2

| 字段 | 值 |
|---|---|
| 根 event_id | `6` |
| tick / cycle | 271692190 / 705694 |
| sn / PC / opcode | 1034462 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 170263 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 78619 / 1 |
| terminal | full |

### fault 20

| 字段 | 值 |
|---|---|
| 根 event_id | `114` |
| tick / cycle | 4806649925 / 12484805 |
| sn / PC / opcode | 12785815 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1989400 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 112636 / 19 |
| terminal | full |

### fault 21

| 字段 | 值 |
|---|---|
| 根 event_id | `120` |
| tick / cycle | 5400149370 / 14026362 |
| sn / PC / opcode | 13628217 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 2094621 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 105221 / 20 |
| terminal | full |

### fault 3

| 字段 | 值 |
|---|---|
| 根 event_id | `12` |
| tick / cycle | 429524480 / 1115648 |
| sn / PC / opcode | 1657152 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 274042 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 103779 / 2 |
| terminal | full |

### fault 4

| 字段 | 值 |
|---|---|
| 根 event_id | `18` |
| tick / cycle | 553983430 / 1438918 |
| sn / PC / opcode | 2148517 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 355938 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 81896 / 3 |
| terminal | full |

### fault 5

| 字段 | 值 |
|---|---|
| 根 event_id | `24` |
| tick / cycle | 649853050 / 1687930 |
| sn / PC / opcode | 2526628 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 418958 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 63020 / 4 |
| terminal | full |

### fault 6

| 字段 | 值 |
|---|---|
| 根 event_id | `30` |
| tick / cycle | 846141065 / 2197769 |
| sn / PC / opcode | 3301167 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 548049 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 129091 / 5 |
| terminal | full |

### fault 7

| 字段 | 值 |
|---|---|
| 根 event_id | `36` |
| tick / cycle | 1062250420 / 2759092 |
| sn / PC / opcode | 4153719 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 690141 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 142092 / 6 |
| terminal | full |

### fault 8

| 字段 | 值 |
|---|---|
| 根 event_id | `42` |
| tick / cycle | 1197353080 / 3110008 |
| sn / PC / opcode | 4686803 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 778985 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 88844 / 7 |
| terminal | full |

### fault 9

| 字段 | 值 |
|---|---|
| 根 event_id | `48` |
| tick / cycle | 1277760715 / 3318859 |
| sn / PC / opcode | 5004148 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 831878 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 52893 / 8 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 3691763460, Site: dyn_inst_execute, opClass=8, sn=11212431, bitseg=mant_lo, mask=0x8000, faults_injected: 18
Tick: 4169255090, Site: dyn_inst_execute, opClass=8, sn=11884087, bitseg=mant_lo, mask=0x4, faults_injected: 19
Tick: 4806649925, Site: dyn_inst_execute, opClass=8, sn=12785815, bitseg=mant_lo, mask=0x10000, faults_injected: 20
Tick: 5400149370, Site: dyn_inst_execute, opClass=8, sn=13628217, bitseg=mant_lo, mask=0x40, faults_injected: 21
CHAOS_RATE_COMPLETE=21
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4086700000000000 → 0x4086700000002000 |
| old/new hash | 0xe619297f99a2b085 → 0x696fdac89d008a25 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4086700000000000 / 0x4086700000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 10

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408aa00000000000 → 0x408aa00000000001 |
| old/new hash | 0xdfa1f17b9fe36f29 → 0x9151ca78b43e5dd8 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408aa00000000000 / 0x408aa00000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 11

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4082e80000000000 → 0x4082e80000000004 |
| old/new hash | 0xc4d0897cb2bb1759 → 0x7167d5a61212d30d |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4082e80000000000 / 0x4082e80000000004 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 12

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff6353f7ced9169 → 0x3ff6353f7ced9161 |
| old/new hash | 0x362c7400752e9633 → 0x6d4679a132d2b34b |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff6353f7ced9169 / 0x3ff6353f7ced9161 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 13

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4063a00000000000 → 0x4063a00000000400 |
| old/new hash | 0xdd99fb7b9e29aba8 → 0xf2e3e9a4e578f714 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4063a00000000000 / 0x4063a00000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 14

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4086d80000000000 → 0x4086d80000020000 |
| old/new hash | 0x64a4b17d9e458a8d → 0x75ab5119e7ecf58f |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4086d80000000000 / 0x4086d80000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 15

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087f00000000000 → 0x4087f00000002000 |
| old/new hash | 0x94bdc37d2882c75c → 0x114874c6261a4efc |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087f00000000000 / 0x4087f00000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 16

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080800000000000 → 0x4080800000000001 |
| old/new hash | 0xf18dcd7c3a1dd4a3 → 0x7f7406781a105e82 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080800000000000 / 0x4080800000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 17

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff235b4edb2f662 → 0x3ff235b4edb2e662 |
| old/new hash | 0x7d3f461d2d40b642 → 0xb4c49126ae87b192 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff235b4edb2f662 / 0x3ff235b4edb2e662 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 18

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff289f40a2877ee → 0x3ff289f40a28f7ee |
| old/new hash | 0xe44e2b9b54a8c6c6 → 0xdb56f915896cf146 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff289f40a2877ee / 0x3ff289f40a28f7ee |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 19

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe7112ba16e7a32 → 0x3fe7112ba16e7a36 |
| old/new hash | 0x1189d835d2d7b2c4 → 0x145957cc5e4f6a40 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe7112ba16e7a32 / 0x3fe7112ba16e7a36 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 2

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feaf1a9fbe76c8b → 0x3feaf1a9fbe76cab |
| old/new hash | 0xedba9048f153f727 → 0x47d6746c4ba94007 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feaf1a9fbe76c8b / 0x3feaf1a9fbe76cab |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 20

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc40639d5e4a384 → 0x3fc40639d5e5a384 |
| old/new hash | 0xad719335d8f064bb → 0x29fe28dff0df1592 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc40639d5e4a384 / 0x3fc40639d5e5a384 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 21

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff24e8fb00bcbe6 → 0x3ff24e8fb00bcba6 |
| old/new hash | 0x100a73642d419e05 → 0x55106bf614f7e745 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff24e8fb00bcbe6 / 0x3ff24e8fb00bcba6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 3

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407f600000000000 → 0x407f600000000001 |
| old/new hash | 0x5e92837f4dbdbfd4 → 0x1509687508a65eb5 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407f600000000000 / 0x407f600000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 4

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408b080000000000 → 0x408b080000004000 |
| old/new hash | 0x010ff37e86eacb18 → 0x59155612fec38458 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408b080000000000 / 0x408b080000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 5

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd0624dd2f1a9fc → 0x3fd0624dd2f1a97c |
| old/new hash | 0x6b279e0db66d9a71 → 0x1f21b555a15e32f1 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd0624dd2f1a9fc / 0x3fd0624dd2f1a97c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 6

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdc083126e978d5 → 0x3fdc083126e978d7 |
| old/new hash | 0x61e89d0d38234561 → 0x1ffc50218c4cc49f |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdc083126e978d5 / 0x3fdc083126e978d7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 7

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdfdf3b645a1cac → 0x3fdfdf3b645a14ac |
| old/new hash | 0x81b36ee00c2daf65 → 0xe207c965dba4018d |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdfdf3b645a1cac / 0x3fdfdf3b645a14ac |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 8

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087e00000000000 → 0x4087e00000000020 |
| old/new hash | 0x0a26137cda02dcac → 0xb9f334a45708270c |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087e00000000000 / 0x4087e00000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 9

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfbcac083126e978 → 0xbfbcac083124e978 |
| old/new hash | 0x6bd9dc816de72f5c → 0xce40523a9262d84e |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfbcac083126e978 / 0xbfbcac083124e978 |
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
| 7 | chain_end | — | 126 | 5 |

### fault 10（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 54 | — |
| 2 | carrier_state | L1 | 55 | 54 |
| 3 | operand_read | L2 | 56 | 55 |
| 4 | execute | L3 | 57 | 56 |
| 5 | prf_writeback | L4 | 58 | 57 |
| 6 | commit | L5 | 59 | 58 |
| 7 | chain_end | — | 135 | 59 |

### fault 11（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 60 | — |
| 2 | carrier_state | L1 | 61 | 60 |
| 3 | operand_read | L2 | 62 | 61 |
| 4 | execute | L3 | 63 | 62 |
| 5 | prf_writeback | L4 | 64 | 63 |
| 6 | commit | L5 | 65 | 64 |
| 7 | chain_end | — | 136 | 65 |

### fault 12（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 66 | — |
| 2 | carrier_state | L1 | 67 | 66 |
| 3 | operand_read | L2 | 68 | 67 |
| 4 | execute | L3 | 69 | 68 |
| 5 | prf_writeback | L4 | 70 | 69 |
| 6 | commit | L5 | 71 | 70 |
| 7 | chain_end | — | 137 | 71 |

### fault 13（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 72 | — |
| 2 | carrier_state | L1 | 73 | 72 |
| 3 | operand_read | L2 | 74 | 73 |
| 4 | execute | L3 | 75 | 74 |
| 5 | prf_writeback | L4 | 76 | 75 |
| 6 | commit | L5 | 77 | 76 |
| 7 | chain_end | — | 138 | 77 |

### fault 14（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 78 | — |
| 2 | carrier_state | L1 | 79 | 78 |
| 3 | operand_read | L2 | 80 | 79 |
| 4 | execute | L3 | 81 | 80 |
| 5 | prf_writeback | L4 | 82 | 81 |
| 6 | commit | L5 | 83 | 82 |
| 7 | chain_end | — | 139 | 83 |

### fault 15（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 84 | — |
| 2 | carrier_state | L1 | 85 | 84 |
| 3 | operand_read | L2 | 86 | 85 |
| 4 | execute | L3 | 87 | 86 |
| 5 | prf_writeback | L4 | 88 | 87 |
| 6 | commit | L5 | 89 | 88 |
| 7 | chain_end | — | 140 | 89 |

### fault 16（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 90 | — |
| 2 | carrier_state | L1 | 91 | 90 |
| 3 | operand_read | L2 | 92 | 91 |
| 4 | execute | L3 | 93 | 92 |
| 5 | prf_writeback | L4 | 94 | 93 |
| 6 | commit | L5 | 95 | 94 |
| 7 | chain_end | — | 141 | 95 |

### fault 17（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 96 | — |
| 2 | carrier_state | L1 | 97 | 96 |
| 3 | operand_read | L2 | 98 | 97 |
| 4 | execute | L3 | 99 | 98 |
| 5 | prf_writeback | L4 | 100 | 99 |
| 6 | commit | L5 | 101 | 100 |
| 7 | chain_end | — | 142 | 101 |

### fault 18（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 102 | — |
| 2 | carrier_state | L1 | 103 | 102 |
| 3 | operand_read | L2 | 104 | 103 |
| 4 | execute | L3 | 105 | 104 |
| 5 | prf_writeback | L4 | 106 | 105 |
| 6 | commit | L5 | 107 | 106 |
| 7 | chain_end | — | 143 | 107 |

### fault 19（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 108 | — |
| 2 | carrier_state | L1 | 109 | 108 |
| 3 | operand_read | L2 | 110 | 109 |
| 4 | execute | L3 | 111 | 110 |
| 5 | prf_writeback | L4 | 112 | 111 |
| 6 | commit | L5 | 113 | 112 |
| 7 | chain_end | — | 144 | 113 |

### fault 2（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 6 | — |
| 2 | carrier_state | L1 | 7 | 6 |
| 3 | operand_read | L2 | 8 | 7 |
| 4 | execute | L3 | 9 | 8 |
| 5 | prf_writeback | L4 | 10 | 9 |
| 6 | commit | L5 | 11 | 10 |
| 7 | chain_end | — | 127 | 11 |

### fault 20（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 114 | — |
| 2 | carrier_state | L1 | 115 | 114 |
| 3 | operand_read | L2 | 116 | 115 |
| 4 | execute | L3 | 117 | 116 |
| 5 | prf_writeback | L4 | 118 | 117 |
| 6 | commit | L5 | 119 | 118 |
| 7 | chain_end | — | 145 | 119 |

### fault 21（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 120 | — |
| 2 | carrier_state | L1 | 121 | 120 |
| 3 | operand_read | L2 | 122 | 121 |
| 4 | execute | L3 | 123 | 122 |
| 5 | prf_writeback | L4 | 124 | 123 |
| 6 | commit | L5 | 125 | 124 |
| 7 | chain_end | — | 146 | 125 |

### fault 3（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 12 | — |
| 2 | carrier_state | L1 | 13 | 12 |
| 3 | operand_read | L2 | 14 | 13 |
| 4 | execute | L3 | 15 | 14 |
| 5 | prf_writeback | L4 | 16 | 15 |
| 6 | commit | L5 | 17 | 16 |
| 7 | chain_end | — | 128 | 17 |

### fault 4（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 18 | — |
| 2 | carrier_state | L1 | 19 | 18 |
| 3 | operand_read | L2 | 20 | 19 |
| 4 | execute | L3 | 21 | 20 |
| 5 | prf_writeback | L4 | 22 | 21 |
| 6 | commit | L5 | 23 | 22 |
| 7 | chain_end | — | 129 | 23 |

### fault 5（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 24 | — |
| 2 | carrier_state | L1 | 25 | 24 |
| 3 | operand_read | L2 | 26 | 25 |
| 4 | execute | L3 | 27 | 26 |
| 5 | prf_writeback | L4 | 28 | 27 |
| 6 | commit | L5 | 29 | 28 |
| 7 | chain_end | — | 130 | 29 |

### fault 6（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 30 | — |
| 2 | carrier_state | L1 | 31 | 30 |
| 3 | operand_read | L2 | 32 | 31 |
| 4 | execute | L3 | 33 | 32 |
| 5 | prf_writeback | L4 | 34 | 33 |
| 6 | commit | L5 | 35 | 34 |
| 7 | chain_end | — | 131 | 35 |

### fault 7（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 36 | — |
| 2 | carrier_state | L1 | 37 | 36 |
| 3 | operand_read | L2 | 38 | 37 |
| 4 | execute | L3 | 39 | 38 |
| 5 | prf_writeback | L4 | 40 | 39 |
| 6 | commit | L5 | 41 | 40 |
| 7 | chain_end | — | 132 | 41 |

### fault 8（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 42 | — |
| 2 | carrier_state | L1 | 43 | 42 |
| 3 | operand_read | L2 | 44 | 43 |
| 4 | execute | L3 | 45 | 44 |
| 5 | prf_writeback | L4 | 46 | 45 |
| 6 | commit | L5 | 47 | 46 |
| 7 | chain_end | — | 133 | 47 |

### fault 9（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 48 | — |
| 2 | carrier_state | L1 | 49 | 48 |
| 3 | operand_read | L2 | 50 | 49 |
| 4 | execute | L3 | 51 | 50 |
| 5 | prf_writeback | L4 | 52 | 51 |
| 6 | commit | L5 | 53 | 52 |
| 7 | chain_end | — | 134 | 53 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 151987605 | 1 | 562753 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4086700000000000→0x4086700000002000 | — | — | origin |
| carrier_state | 1 | 0 | 151987605 | 1 | 562753 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4086700000000000→0x4086700000002000 | — | — | fsu_taint |
| operand_read | 2 | 1 | 151991455 | 1 | 562756 | 0x000000000040065c | fmadd | 562753/562756 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 151991455 | 1 | 562756 | 0x000000000040065c | fmadd | 562753/562756 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 151991455 | 1 | 562756 | 0x000000000040065c | fmadd | 562753/562756 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 151992225 | 1 | 562756 | 0x000000000040065c | fmadd | —/562756 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 126 | 5 | 9406475925 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 54 | — | 1486242835 | 10 | 5826493 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x408aa00000000000→0x408aa00000000001 | — | — | origin |
| carrier_state | 55 | 54 | 1486242835 | 10 | 5826493 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x408aa00000000000→0x408aa00000000001 | — | — | fsu_taint |
| operand_read | 56 | 55 | 1486246685 | 10 | 5826496 | 0x000000000040065c | fmadd | 5826493/5826496 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 57 | 56 | 1486246685 | 10 | 5826496 | 0x000000000040065c | fmadd | 5826493/5826496 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 58 | 57 | 1486246685 | 10 | 5826496 | 0x000000000040065c | fmadd | 5826493/5826496 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 59 | 58 | 1486247455 | 10 | 5826496 | 0x000000000040065c | fmadd | —/5826496 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 135 | 59 | 9406475925 | 10 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 60 | — | 1655560830 | 11 | 6494687 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4082e80000000000→0x4082e80000000004 | — | — | origin |
| carrier_state | 61 | 60 | 1655560830 | 11 | 6494687 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4082e80000000000→0x4082e80000000004 | — | — | fsu_taint |
| operand_read | 62 | 61 | 1655562755 | 11 | 6494690 | 0x0000000000400654 | fmadd | 6494687/6494690 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 63 | 62 | 1655562755 | 11 | 6494690 | 0x0000000000400654 | fmadd | 6494687/6494690 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 64 | 63 | 1655562755 | 11 | 6494690 | 0x0000000000400654 | fmadd | 6494687/6494690 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 65 | 64 | 1655563525 | 11 | 6494690 | 0x0000000000400654 | fmadd | —/6494690 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 136 | 65 | 9406475925 | 11 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 66 | — | 1824587765 | 12 | 7161734 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff6353f7ced9169→0x3ff6353f7ced9161 | — | — | origin |
| carrier_state | 67 | 66 | 1824587765 | 12 | 7161734 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff6353f7ced9169→0x3ff6353f7ced9161 | — | — | fsu_taint |
| operand_read | 68 | 67 | 1824623185 | 12 | 7161878 | 0x0000000000400654 | fmadd | 7161734/7161878 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 69 | 68 | 1824623185 | 12 | 7161878 | 0x0000000000400654 | fmadd | 7161734/7161878 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 70 | 69 | 1824623185 | 12 | 7161878 | 0x0000000000400654 | fmadd | 7161734/7161878 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 71 | 70 | 1824623955 | 12 | 7161878 | 0x0000000000400654 | fmadd | —/7161878 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 137 | 71 | 9406475925 | 12 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 72 | — | 1915013870 | 13 | 7517988 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4063a00000000000→0x4063a00000000400 | — | — | origin |
| carrier_state | 73 | 72 | 1915013870 | 13 | 7517988 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4063a00000000000→0x4063a00000000400 | — | — | fsu_taint |
| operand_read | 74 | 73 | 1915018105 | 13 | 7517991 | 0x0000000000400658 | fmadd | 7517988/7517991 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 75 | 74 | 1915018105 | 13 | 7517991 | 0x0000000000400658 | fmadd | 7517988/7517991 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 76 | 75 | 1915018105 | 13 | 7517991 | 0x0000000000400658 | fmadd | 7517988/7517991 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 77 | 76 | 1915018875 | 13 | 7517991 | 0x0000000000400658 | fmadd | —/7517991 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 138 | 77 | 9406475925 | 13 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 78 | — | 2131341520 | 14 | 8371800 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4086d80000000000→0x4086d80000020000 | — | — | origin |
| carrier_state | 79 | 78 | 2131341520 | 14 | 8371800 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4086d80000000000→0x4086d80000020000 | — | — | fsu_taint |
| operand_read | 80 | 79 | 2131345755 | 14 | 8371803 | 0x0000000000400658 | fmadd | 8371800/8371803 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 81 | 80 | 2131345755 | 14 | 8371803 | 0x0000000000400658 | fmadd | 8371800/8371803 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 82 | 81 | 2131345755 | 14 | 8371803 | 0x0000000000400658 | fmadd | 8371800/8371803 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 83 | 82 | 2131346525 | 14 | 8371803 | 0x0000000000400658 | fmadd | —/8371803 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 139 | 83 | 9406475925 | 14 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 84 | — | 2229355205 | 15 | 8758188 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4087f00000000000→0x4087f00000002000 | — | — | origin |
| carrier_state | 85 | 84 | 2229355205 | 15 | 8758188 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4087f00000000000→0x4087f00000002000 | — | — | fsu_taint |
| operand_read | 86 | 85 | 2229359440 | 15 | 8758191 | 0x0000000000400658 | fmadd | 8758188/8758191 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 87 | 86 | 2229359440 | 15 | 8758191 | 0x0000000000400658 | fmadd | 8758188/8758191 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 88 | 87 | 2229359440 | 15 | 8758191 | 0x0000000000400658 | fmadd | 8758188/8758191 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 89 | 88 | 2229360210 | 15 | 8758191 | 0x0000000000400658 | fmadd | —/8758191 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 140 | 89 | 9406475925 | 15 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 90 | — | 2398855305 | 16 | 9427320 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4080800000000000→0x4080800000000001 | — | — | origin |
| carrier_state | 91 | 90 | 2398855305 | 16 | 9427320 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4080800000000000→0x4080800000000001 | — | — | fsu_taint |
| operand_read | 92 | 91 | 2398859540 | 16 | 9427323 | 0x0000000000400658 | fmadd | 9427320/9427323 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 93 | 92 | 2398859540 | 16 | 9427323 | 0x0000000000400658 | fmadd | 9427320/9427323 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 94 | 93 | 2398859540 | 16 | 9427323 | 0x0000000000400658 | fmadd | 9427320/9427323 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 95 | 94 | 2398860310 | 16 | 9427323 | 0x0000000000400658 | fmadd | —/9427323 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 141 | 95 | 9406475925 | 16 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 96 | — | 3154599525 | 17 | 10458737 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff235b4edb2f662→0x3ff235b4edb2e662 | — | — | origin |
| carrier_state | 97 | 96 | 3154599525 | 17 | 10458737 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff235b4edb2f662→0x3ff235b4edb2e662 | — | — | fsu_taint |
| operand_read | 98 | 97 | 3154607995 | 17 | 10458753 | 0x00000000004006cc | fmadd | 10458737/10458753 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 99 | 98 | 3154607995 | 17 | 10458753 | 0x00000000004006cc | fmadd | 10458737/10458753 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 100 | 99 | 3154607995 | 17 | 10458753 | 0x00000000004006cc | fmadd | 10458737/10458753 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 101 | 100 | 3154608765 | 17 | 10458753 | 0x00000000004006cc | fmadd | —/10458753 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 142 | 101 | 9406475925 | 17 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 102 | — | 3691763460 | 18 | 11212431 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff289f40a2877ee→0x3ff289f40a28f7ee | — | — | origin |
| carrier_state | 103 | 102 | 3691763460 | 18 | 11212431 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff289f40a2877ee→0x3ff289f40a28f7ee | — | — | fsu_taint |
| operand_read | 104 | 103 | 3691771930 | 18 | 11212447 | 0x00000000004006a4 | fmadd | 11212431/11212447 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 105 | 104 | 3691771930 | 18 | 11212447 | 0x00000000004006a4 | fmadd | 11212431/11212447 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 106 | 105 | 3691771930 | 18 | 11212447 | 0x00000000004006a4 | fmadd | 11212431/11212447 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 107 | 106 | 3691772700 | 18 | 11212447 | 0x00000000004006a4 | fmadd | —/11212447 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 143 | 107 | 9406475925 | 18 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 108 | — | 4169255090 | 19 | 11884087 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe7112ba16e7a32→0x3fe7112ba16e7a36 | — | — | origin |
| carrier_state | 109 | 108 | 4169255090 | 19 | 11884087 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe7112ba16e7a32→0x3fe7112ba16e7a36 | — | — | fsu_taint |
| operand_read | 110 | 109 | 4169263560 | 19 | 11884103 | 0x00000000004006cc | fmadd | 11884087/11884103 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 111 | 110 | 4169263560 | 19 | 11884103 | 0x00000000004006cc | fmadd | 11884087/11884103 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 112 | 111 | 4169263560 | 19 | 11884103 | 0x00000000004006cc | fmadd | 11884087/11884103 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 113 | 112 | 4169264330 | 19 | 11884103 | 0x00000000004006cc | fmadd | —/11884103 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 144 | 113 | 9406475925 | 19 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 6 | — | 271692190 | 2 | 1034462 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3feaf1a9fbe76c8b→0x3feaf1a9fbe76cab | — | — | origin |
| carrier_state | 7 | 6 | 271692190 | 2 | 1034462 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3feaf1a9fbe76c8b→0x3feaf1a9fbe76cab | — | — | fsu_taint |
| operand_read | 8 | 7 | 271727610 | 2 | 1034606 | 0x0000000000400654 | fmadd | 1034462/1034606 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 271727610 | 2 | 1034606 | 0x0000000000400654 | fmadd | 1034462/1034606 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 271727610 | 2 | 1034606 | 0x0000000000400654 | fmadd | 1034462/1034606 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 271728380 | 2 | 1034606 | 0x0000000000400654 | fmadd | —/1034606 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 127 | 11 | 9406475925 | 2 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 114 | — | 4806649925 | 20 | 12785815 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fc40639d5e4a384→0x3fc40639d5e5a384 | — | — | origin |
| carrier_state | 115 | 114 | 4806649925 | 20 | 12785815 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fc40639d5e4a384→0x3fc40639d5e5a384 | — | — | fsu_taint |
| operand_read | 116 | 115 | 4806658395 | 20 | 12785831 | 0x00000000004006a4 | fmadd | 12785815/12785831 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 117 | 116 | 4806658395 | 20 | 12785831 | 0x00000000004006a4 | fmadd | 12785815/12785831 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 118 | 117 | 4806658395 | 20 | 12785831 | 0x00000000004006a4 | fmadd | 12785815/12785831 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 119 | 118 | 4806659165 | 20 | 12785831 | 0x00000000004006a4 | fmadd | —/12785831 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 145 | 119 | 9406475925 | 20 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 120 | — | 5400149370 | 21 | 13628217 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff24e8fb00bcbe6→0x3ff24e8fb00bcba6 | — | — | origin |
| carrier_state | 121 | 120 | 5400149370 | 21 | 13628217 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff24e8fb00bcbe6→0x3ff24e8fb00bcba6 | — | — | fsu_taint |
| operand_read | 122 | 121 | 5400157840 | 21 | 13628233 | 0x00000000004006cc | fmadd | 13628217/13628233 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 123 | 122 | 5400157840 | 21 | 13628233 | 0x00000000004006cc | fmadd | 13628217/13628233 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 124 | 123 | 5400157840 | 21 | 13628233 | 0x00000000004006cc | fmadd | 13628217/13628233 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 125 | 124 | 5400158610 | 21 | 13628233 | 0x00000000004006cc | fmadd | —/13628233 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 146 | 125 | 9406475925 | 21 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 12 | — | 429524480 | 3 | 1657152 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x407f600000000000→0x407f600000000001 | — | — | origin |
| carrier_state | 13 | 12 | 429524480 | 3 | 1657152 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x407f600000000000→0x407f600000000001 | — | — | fsu_taint |
| operand_read | 14 | 13 | 429528715 | 3 | 1657155 | 0x0000000000400658 | fmadd | 1657152/1657155 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 15 | 14 | 429528715 | 3 | 1657155 | 0x0000000000400658 | fmadd | 1657152/1657155 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 16 | 15 | 429528715 | 3 | 1657155 | 0x0000000000400658 | fmadd | 1657152/1657155 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 17 | 16 | 429529485 | 3 | 1657155 | 0x0000000000400658 | fmadd | —/1657155 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 128 | 17 | 9406475925 | 3 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 18 | — | 553983430 | 4 | 2148517 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x408b080000000000→0x408b080000004000 | — | — | origin |
| carrier_state | 19 | 18 | 553983430 | 4 | 2148517 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x408b080000000000→0x408b080000004000 | — | — | fsu_taint |
| operand_read | 20 | 19 | 553987280 | 4 | 2148520 | 0x000000000040065c | fmadd | 2148517/2148520 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 21 | 20 | 553987280 | 4 | 2148520 | 0x000000000040065c | fmadd | 2148517/2148520 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 22 | 21 | 553987280 | 4 | 2148520 | 0x000000000040065c | fmadd | 2148517/2148520 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 23 | 22 | 553988050 | 4 | 2148520 | 0x000000000040065c | fmadd | —/2148520 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 129 | 23 | 9406475925 | 4 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 24 | — | 649853050 | 5 | 2526628 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0x3fd0624dd2f1a9fc→0x3fd0624dd2f1a97c | — | — | origin |
| carrier_state | 25 | 24 | 649853050 | 5 | 2526628 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0x3fd0624dd2f1a9fc→0x3fd0624dd2f1a97c | — | — | fsu_taint |
| operand_read | 26 | 25 | 649868450 | 5 | 2526698 | 0x0000000000400654 | fmadd | 2526628/2526698 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 27 | 26 | 649868450 | 5 | 2526698 | 0x0000000000400654 | fmadd | 2526628/2526698 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 28 | 27 | 649868450 | 5 | 2526698 | 0x0000000000400654 | fmadd | 2526628/2526698 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 29 | 28 | 649869220 | 5 | 2526698 | 0x0000000000400654 | fmadd | —/2526698 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 130 | 29 | 9406475925 | 5 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 30 | — | 846141065 | 6 | 3301167 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fdc083126e978d5→0x3fdc083126e978d7 | — | — | origin |
| carrier_state | 31 | 30 | 846141065 | 6 | 3301167 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fdc083126e978d5→0x3fdc083126e978d7 | — | — | fsu_taint |
| operand_read | 32 | 31 | 846165320 | 6 | 3301274 | 0x0000000000400654 | fmadd | 3301167/3301274 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 33 | 32 | 846165320 | 6 | 3301274 | 0x0000000000400654 | fmadd | 3301167/3301274 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 34 | 33 | 846165320 | 6 | 3301274 | 0x0000000000400654 | fmadd | 3301167/3301274 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 35 | 34 | 846166090 | 6 | 3301274 | 0x0000000000400654 | fmadd | —/3301274 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 131 | 35 | 9406475925 | 6 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 36 | — | 1062250420 | 7 | 4153719 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fdfdf3b645a1cac→0x3fdfdf3b645a14ac | — | — | origin |
| carrier_state | 37 | 36 | 1062250420 | 7 | 4153719 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fdfdf3b645a1cac→0x3fdfdf3b645a14ac | — | — | fsu_taint |
| operand_read | 38 | 37 | 1062274675 | 7 | 4153826 | 0x0000000000400654 | fmadd | 4153719/4153826 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 39 | 38 | 1062274675 | 7 | 4153826 | 0x0000000000400654 | fmadd | 4153719/4153826 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 40 | 39 | 1062274675 | 7 | 4153826 | 0x0000000000400654 | fmadd | 4153719/4153826 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 41 | 40 | 1062275445 | 7 | 4153826 | 0x0000000000400654 | fmadd | —/4153826 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 132 | 41 | 9406475925 | 7 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 42 | — | 1197353080 | 8 | 4686803 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4087e00000000000→0x4087e00000000020 | — | — | origin |
| carrier_state | 43 | 42 | 1197353080 | 8 | 4686803 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4087e00000000000→0x4087e00000000020 | — | — | fsu_taint |
| operand_read | 44 | 43 | 1197355005 | 8 | 4686806 | 0x0000000000400654 | fmadd | 4686803/4686806 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 45 | 44 | 1197355005 | 8 | 4686806 | 0x0000000000400654 | fmadd | 4686803/4686806 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 46 | 45 | 1197355005 | 8 | 4686806 | 0x0000000000400654 | fmadd | 4686803/4686806 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 47 | 46 | 1197355775 | 8 | 4686806 | 0x0000000000400654 | fmadd | —/4686806 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 133 | 47 | 9406475925 | 8 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 48 | — | 1277760715 | 9 | 5004148 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfbcac083126e978→0xbfbcac083124e978 | — | — | origin |
| carrier_state | 49 | 48 | 1277760715 | 9 | 5004148 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfbcac083126e978→0xbfbcac083124e978 | — | — | fsu_taint |
| operand_read | 50 | 49 | 1277776115 | 9 | 5004218 | 0x0000000000400654 | fmadd | 5004148/5004218 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 51 | 50 | 1277776115 | 9 | 5004218 | 0x0000000000400654 | fmadd | 5004148/5004218 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 52 | 51 | 1277776115 | 9 | 5004218 | 0x0000000000400654 | fmadd | 5004148/5004218 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 53 | 52 | 1277776885 | 9 | 5004218 | 0x0000000000400654 | fmadd | —/5004218 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 134 | 53 | 9406475925 | 9 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

## 6. 数据、控制和污点在各层如何变化

### fault 1

- **L0**：fault_applied#0（本 seed 真实事件）。
- **L1**：carrier_state#1（本 seed 真实事件）。
- **L2**：operand_read#2（本 seed 真实事件）。
- **L3**：execute#3（本 seed 真实事件）。
- **L4**：prf_writeback#4（本 seed 真实事件）。
- **L5**：commit#5（本 seed 真实事件）。

### fault 10

- **L0**：fault_applied#54（本 seed 真实事件）。
- **L1**：carrier_state#55（本 seed 真实事件）。
- **L2**：operand_read#56（本 seed 真实事件）。
- **L3**：execute#57（本 seed 真实事件）。
- **L4**：prf_writeback#58（本 seed 真实事件）。
- **L5**：commit#59（本 seed 真实事件）。

### fault 11

- **L0**：fault_applied#60（本 seed 真实事件）。
- **L1**：carrier_state#61（本 seed 真实事件）。
- **L2**：operand_read#62（本 seed 真实事件）。
- **L3**：execute#63（本 seed 真实事件）。
- **L4**：prf_writeback#64（本 seed 真实事件）。
- **L5**：commit#65（本 seed 真实事件）。

### fault 12

- **L0**：fault_applied#66（本 seed 真实事件）。
- **L1**：carrier_state#67（本 seed 真实事件）。
- **L2**：operand_read#68（本 seed 真实事件）。
- **L3**：execute#69（本 seed 真实事件）。
- **L4**：prf_writeback#70（本 seed 真实事件）。
- **L5**：commit#71（本 seed 真实事件）。

### fault 13

- **L0**：fault_applied#72（本 seed 真实事件）。
- **L1**：carrier_state#73（本 seed 真实事件）。
- **L2**：operand_read#74（本 seed 真实事件）。
- **L3**：execute#75（本 seed 真实事件）。
- **L4**：prf_writeback#76（本 seed 真实事件）。
- **L5**：commit#77（本 seed 真实事件）。

### fault 14

- **L0**：fault_applied#78（本 seed 真实事件）。
- **L1**：carrier_state#79（本 seed 真实事件）。
- **L2**：operand_read#80（本 seed 真实事件）。
- **L3**：execute#81（本 seed 真实事件）。
- **L4**：prf_writeback#82（本 seed 真实事件）。
- **L5**：commit#83（本 seed 真实事件）。

### fault 15

- **L0**：fault_applied#84（本 seed 真实事件）。
- **L1**：carrier_state#85（本 seed 真实事件）。
- **L2**：operand_read#86（本 seed 真实事件）。
- **L3**：execute#87（本 seed 真实事件）。
- **L4**：prf_writeback#88（本 seed 真实事件）。
- **L5**：commit#89（本 seed 真实事件）。

### fault 16

- **L0**：fault_applied#90（本 seed 真实事件）。
- **L1**：carrier_state#91（本 seed 真实事件）。
- **L2**：operand_read#92（本 seed 真实事件）。
- **L3**：execute#93（本 seed 真实事件）。
- **L4**：prf_writeback#94（本 seed 真实事件）。
- **L5**：commit#95（本 seed 真实事件）。

### fault 17

- **L0**：fault_applied#96（本 seed 真实事件）。
- **L1**：carrier_state#97（本 seed 真实事件）。
- **L2**：operand_read#98（本 seed 真实事件）。
- **L3**：execute#99（本 seed 真实事件）。
- **L4**：prf_writeback#100（本 seed 真实事件）。
- **L5**：commit#101（本 seed 真实事件）。

### fault 18

- **L0**：fault_applied#102（本 seed 真实事件）。
- **L1**：carrier_state#103（本 seed 真实事件）。
- **L2**：operand_read#104（本 seed 真实事件）。
- **L3**：execute#105（本 seed 真实事件）。
- **L4**：prf_writeback#106（本 seed 真实事件）。
- **L5**：commit#107（本 seed 真实事件）。

### fault 19

- **L0**：fault_applied#108（本 seed 真实事件）。
- **L1**：carrier_state#109（本 seed 真实事件）。
- **L2**：operand_read#110（本 seed 真实事件）。
- **L3**：execute#111（本 seed 真实事件）。
- **L4**：prf_writeback#112（本 seed 真实事件）。
- **L5**：commit#113（本 seed 真实事件）。

### fault 2

- **L0**：fault_applied#6（本 seed 真实事件）。
- **L1**：carrier_state#7（本 seed 真实事件）。
- **L2**：operand_read#8（本 seed 真实事件）。
- **L3**：execute#9（本 seed 真实事件）。
- **L4**：prf_writeback#10（本 seed 真实事件）。
- **L5**：commit#11（本 seed 真实事件）。

### fault 20

- **L0**：fault_applied#114（本 seed 真实事件）。
- **L1**：carrier_state#115（本 seed 真实事件）。
- **L2**：operand_read#116（本 seed 真实事件）。
- **L3**：execute#117（本 seed 真实事件）。
- **L4**：prf_writeback#118（本 seed 真实事件）。
- **L5**：commit#119（本 seed 真实事件）。

### fault 21

- **L0**：fault_applied#120（本 seed 真实事件）。
- **L1**：carrier_state#121（本 seed 真实事件）。
- **L2**：operand_read#122（本 seed 真实事件）。
- **L3**：execute#123（本 seed 真实事件）。
- **L4**：prf_writeback#124（本 seed 真实事件）。
- **L5**：commit#125（本 seed 真实事件）。

### fault 3

- **L0**：fault_applied#12（本 seed 真实事件）。
- **L1**：carrier_state#13（本 seed 真实事件）。
- **L2**：operand_read#14（本 seed 真实事件）。
- **L3**：execute#15（本 seed 真实事件）。
- **L4**：prf_writeback#16（本 seed 真实事件）。
- **L5**：commit#17（本 seed 真实事件）。

### fault 4

- **L0**：fault_applied#18（本 seed 真实事件）。
- **L1**：carrier_state#19（本 seed 真实事件）。
- **L2**：operand_read#20（本 seed 真实事件）。
- **L3**：execute#21（本 seed 真实事件）。
- **L4**：prf_writeback#22（本 seed 真实事件）。
- **L5**：commit#23（本 seed 真实事件）。

### fault 5

- **L0**：fault_applied#24（本 seed 真实事件）。
- **L1**：carrier_state#25（本 seed 真实事件）。
- **L2**：operand_read#26（本 seed 真实事件）。
- **L3**：execute#27（本 seed 真实事件）。
- **L4**：prf_writeback#28（本 seed 真实事件）。
- **L5**：commit#29（本 seed 真实事件）。

### fault 6

- **L0**：fault_applied#30（本 seed 真实事件）。
- **L1**：carrier_state#31（本 seed 真实事件）。
- **L2**：operand_read#32（本 seed 真实事件）。
- **L3**：execute#33（本 seed 真实事件）。
- **L4**：prf_writeback#34（本 seed 真实事件）。
- **L5**：commit#35（本 seed 真实事件）。

### fault 7

- **L0**：fault_applied#36（本 seed 真实事件）。
- **L1**：carrier_state#37（本 seed 真实事件）。
- **L2**：operand_read#38（本 seed 真实事件）。
- **L3**：execute#39（本 seed 真实事件）。
- **L4**：prf_writeback#40（本 seed 真实事件）。
- **L5**：commit#41（本 seed 真实事件）。

### fault 8

- **L0**：fault_applied#42（本 seed 真实事件）。
- **L1**：carrier_state#43（本 seed 真实事件）。
- **L2**：operand_read#44（本 seed 真实事件）。
- **L3**：execute#45（本 seed 真实事件）。
- **L4**：prf_writeback#46（本 seed 真实事件）。
- **L5**：commit#47（本 seed 真实事件）。

### fault 9

- **L0**：fault_applied#48（本 seed 真实事件）。
- **L1**：carrier_state#49（本 seed 真实事件）。
- **L2**：operand_read#50（本 seed 真实事件）。
- **L3**：execute#51（本 seed 真实事件）。
- **L4**：prf_writeback#52（本 seed 真实事件）。
- **L5**：commit#53（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 755626416b804782b79ed092df1f8f5c68e1d01249956b5ee70b3eb324493b55 != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：21 / 21
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：147
- attempted / eligible / activated：21 / 2097155 / 21

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 5 | N/A / N/A |
| 10 | full | L5 | True | True | [] | 59 | N/A / N/A |
| 11 | full | L5 | True | True | [] | 65 | N/A / N/A |
| 12 | full | L5 | True | True | [] | 71 | N/A / N/A |
| 13 | full | L5 | True | True | [] | 77 | N/A / N/A |
| 14 | full | L5 | True | True | [] | 83 | N/A / N/A |
| 15 | full | L5 | True | True | [] | 89 | N/A / N/A |
| 16 | full | L5 | True | True | [] | 95 | N/A / N/A |
| 17 | full | L5 | True | True | [] | 101 | N/A / N/A |
| 18 | full | L5 | True | True | [] | 107 | N/A / N/A |
| 19 | full | L5 | True | True | [] | 113 | N/A / N/A |
| 2 | full | L5 | True | True | [] | 11 | N/A / N/A |
| 20 | full | L5 | True | True | [] | 119 | N/A / N/A |
| 21 | full | L5 | True | True | [] | 125 | N/A / N/A |
| 3 | full | L5 | True | True | [] | 17 | N/A / N/A |
| 4 | full | L5 | True | True | [] | 23 | N/A / N/A |
| 5 | full | L5 | True | True | [] | 29 | N/A / N/A |
| 6 | full | L5 | True | True | [] | 35 | N/A / N/A |
| 7 | full | L5 | True | True | [] | 41 | N/A / N/A |
| 8 | full | L5 | True | True | [] | 47 | N/A / N/A |
| 9 | full | L5 | True | True | [] | 53 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_applied) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `2` (operand_read)；child.parent=1 ✓
- `2` (operand_read) → `3` (execute)；child.parent=2 ✓
- `3` (execute) → `4` (prf_writeback)；child.parent=3 ✓
- `4` (prf_writeback) → `5` (commit)；child.parent=4 ✓
- `5` (commit) → `126` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

### fault 10

主链每一条边均验证为直接 parent：

- `54` (fault_applied) → `55` (carrier_state)；child.parent=54 ✓
- `55` (carrier_state) → `56` (operand_read)；child.parent=55 ✓
- `56` (operand_read) → `57` (execute)；child.parent=56 ✓
- `57` (execute) → `58` (prf_writeback)；child.parent=57 ✓
- `58` (prf_writeback) → `59` (commit)；child.parent=58 ✓
- `59` (commit) → `135` (chain_end)；child.parent=59 ✓

- L5 真实见证：`59` kind=commit outcome=errant_commit oracle_diff=—

### fault 11

主链每一条边均验证为直接 parent：

- `60` (fault_applied) → `61` (carrier_state)；child.parent=60 ✓
- `61` (carrier_state) → `62` (operand_read)；child.parent=61 ✓
- `62` (operand_read) → `63` (execute)；child.parent=62 ✓
- `63` (execute) → `64` (prf_writeback)；child.parent=63 ✓
- `64` (prf_writeback) → `65` (commit)；child.parent=64 ✓
- `65` (commit) → `136` (chain_end)；child.parent=65 ✓

- L5 真实见证：`65` kind=commit outcome=errant_commit oracle_diff=—

### fault 12

主链每一条边均验证为直接 parent：

- `66` (fault_applied) → `67` (carrier_state)；child.parent=66 ✓
- `67` (carrier_state) → `68` (operand_read)；child.parent=67 ✓
- `68` (operand_read) → `69` (execute)；child.parent=68 ✓
- `69` (execute) → `70` (prf_writeback)；child.parent=69 ✓
- `70` (prf_writeback) → `71` (commit)；child.parent=70 ✓
- `71` (commit) → `137` (chain_end)；child.parent=71 ✓

- L5 真实见证：`71` kind=commit outcome=errant_commit oracle_diff=—

### fault 13

主链每一条边均验证为直接 parent：

- `72` (fault_applied) → `73` (carrier_state)；child.parent=72 ✓
- `73` (carrier_state) → `74` (operand_read)；child.parent=73 ✓
- `74` (operand_read) → `75` (execute)；child.parent=74 ✓
- `75` (execute) → `76` (prf_writeback)；child.parent=75 ✓
- `76` (prf_writeback) → `77` (commit)；child.parent=76 ✓
- `77` (commit) → `138` (chain_end)；child.parent=77 ✓

- L5 真实见证：`77` kind=commit outcome=errant_commit oracle_diff=—

### fault 14

主链每一条边均验证为直接 parent：

- `78` (fault_applied) → `79` (carrier_state)；child.parent=78 ✓
- `79` (carrier_state) → `80` (operand_read)；child.parent=79 ✓
- `80` (operand_read) → `81` (execute)；child.parent=80 ✓
- `81` (execute) → `82` (prf_writeback)；child.parent=81 ✓
- `82` (prf_writeback) → `83` (commit)；child.parent=82 ✓
- `83` (commit) → `139` (chain_end)；child.parent=83 ✓

- L5 真实见证：`83` kind=commit outcome=errant_commit oracle_diff=—

### fault 15

主链每一条边均验证为直接 parent：

- `84` (fault_applied) → `85` (carrier_state)；child.parent=84 ✓
- `85` (carrier_state) → `86` (operand_read)；child.parent=85 ✓
- `86` (operand_read) → `87` (execute)；child.parent=86 ✓
- `87` (execute) → `88` (prf_writeback)；child.parent=87 ✓
- `88` (prf_writeback) → `89` (commit)；child.parent=88 ✓
- `89` (commit) → `140` (chain_end)；child.parent=89 ✓

- L5 真实见证：`89` kind=commit outcome=errant_commit oracle_diff=—

### fault 16

主链每一条边均验证为直接 parent：

- `90` (fault_applied) → `91` (carrier_state)；child.parent=90 ✓
- `91` (carrier_state) → `92` (operand_read)；child.parent=91 ✓
- `92` (operand_read) → `93` (execute)；child.parent=92 ✓
- `93` (execute) → `94` (prf_writeback)；child.parent=93 ✓
- `94` (prf_writeback) → `95` (commit)；child.parent=94 ✓
- `95` (commit) → `141` (chain_end)；child.parent=95 ✓

- L5 真实见证：`95` kind=commit outcome=errant_commit oracle_diff=—

### fault 17

主链每一条边均验证为直接 parent：

- `96` (fault_applied) → `97` (carrier_state)；child.parent=96 ✓
- `97` (carrier_state) → `98` (operand_read)；child.parent=97 ✓
- `98` (operand_read) → `99` (execute)；child.parent=98 ✓
- `99` (execute) → `100` (prf_writeback)；child.parent=99 ✓
- `100` (prf_writeback) → `101` (commit)；child.parent=100 ✓
- `101` (commit) → `142` (chain_end)；child.parent=101 ✓

- L5 真实见证：`101` kind=commit outcome=errant_commit oracle_diff=—

### fault 18

主链每一条边均验证为直接 parent：

- `102` (fault_applied) → `103` (carrier_state)；child.parent=102 ✓
- `103` (carrier_state) → `104` (operand_read)；child.parent=103 ✓
- `104` (operand_read) → `105` (execute)；child.parent=104 ✓
- `105` (execute) → `106` (prf_writeback)；child.parent=105 ✓
- `106` (prf_writeback) → `107` (commit)；child.parent=106 ✓
- `107` (commit) → `143` (chain_end)；child.parent=107 ✓

- L5 真实见证：`107` kind=commit outcome=errant_commit oracle_diff=—

### fault 19

主链每一条边均验证为直接 parent：

- `108` (fault_applied) → `109` (carrier_state)；child.parent=108 ✓
- `109` (carrier_state) → `110` (operand_read)；child.parent=109 ✓
- `110` (operand_read) → `111` (execute)；child.parent=110 ✓
- `111` (execute) → `112` (prf_writeback)；child.parent=111 ✓
- `112` (prf_writeback) → `113` (commit)；child.parent=112 ✓
- `113` (commit) → `144` (chain_end)；child.parent=113 ✓

- L5 真实见证：`113` kind=commit outcome=errant_commit oracle_diff=—

### fault 2

主链每一条边均验证为直接 parent：

- `6` (fault_applied) → `7` (carrier_state)；child.parent=6 ✓
- `7` (carrier_state) → `8` (operand_read)；child.parent=7 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `127` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

### fault 20

主链每一条边均验证为直接 parent：

- `114` (fault_applied) → `115` (carrier_state)；child.parent=114 ✓
- `115` (carrier_state) → `116` (operand_read)；child.parent=115 ✓
- `116` (operand_read) → `117` (execute)；child.parent=116 ✓
- `117` (execute) → `118` (prf_writeback)；child.parent=117 ✓
- `118` (prf_writeback) → `119` (commit)；child.parent=118 ✓
- `119` (commit) → `145` (chain_end)；child.parent=119 ✓

- L5 真实见证：`119` kind=commit outcome=errant_commit oracle_diff=—

### fault 21

主链每一条边均验证为直接 parent：

- `120` (fault_applied) → `121` (carrier_state)；child.parent=120 ✓
- `121` (carrier_state) → `122` (operand_read)；child.parent=121 ✓
- `122` (operand_read) → `123` (execute)；child.parent=122 ✓
- `123` (execute) → `124` (prf_writeback)；child.parent=123 ✓
- `124` (prf_writeback) → `125` (commit)；child.parent=124 ✓
- `125` (commit) → `146` (chain_end)；child.parent=125 ✓

- L5 真实见证：`125` kind=commit outcome=errant_commit oracle_diff=—

### fault 3

主链每一条边均验证为直接 parent：

- `12` (fault_applied) → `13` (carrier_state)；child.parent=12 ✓
- `13` (carrier_state) → `14` (operand_read)；child.parent=13 ✓
- `14` (operand_read) → `15` (execute)；child.parent=14 ✓
- `15` (execute) → `16` (prf_writeback)；child.parent=15 ✓
- `16` (prf_writeback) → `17` (commit)；child.parent=16 ✓
- `17` (commit) → `128` (chain_end)；child.parent=17 ✓

- L5 真实见证：`17` kind=commit outcome=errant_commit oracle_diff=—

### fault 4

主链每一条边均验证为直接 parent：

- `18` (fault_applied) → `19` (carrier_state)；child.parent=18 ✓
- `19` (carrier_state) → `20` (operand_read)；child.parent=19 ✓
- `20` (operand_read) → `21` (execute)；child.parent=20 ✓
- `21` (execute) → `22` (prf_writeback)；child.parent=21 ✓
- `22` (prf_writeback) → `23` (commit)；child.parent=22 ✓
- `23` (commit) → `129` (chain_end)；child.parent=23 ✓

- L5 真实见证：`23` kind=commit outcome=errant_commit oracle_diff=—

### fault 5

主链每一条边均验证为直接 parent：

- `24` (fault_applied) → `25` (carrier_state)；child.parent=24 ✓
- `25` (carrier_state) → `26` (operand_read)；child.parent=25 ✓
- `26` (operand_read) → `27` (execute)；child.parent=26 ✓
- `27` (execute) → `28` (prf_writeback)；child.parent=27 ✓
- `28` (prf_writeback) → `29` (commit)；child.parent=28 ✓
- `29` (commit) → `130` (chain_end)；child.parent=29 ✓

- L5 真实见证：`29` kind=commit outcome=errant_commit oracle_diff=—

### fault 6

主链每一条边均验证为直接 parent：

- `30` (fault_applied) → `31` (carrier_state)；child.parent=30 ✓
- `31` (carrier_state) → `32` (operand_read)；child.parent=31 ✓
- `32` (operand_read) → `33` (execute)；child.parent=32 ✓
- `33` (execute) → `34` (prf_writeback)；child.parent=33 ✓
- `34` (prf_writeback) → `35` (commit)；child.parent=34 ✓
- `35` (commit) → `131` (chain_end)；child.parent=35 ✓

- L5 真实见证：`35` kind=commit outcome=errant_commit oracle_diff=—

### fault 7

主链每一条边均验证为直接 parent：

- `36` (fault_applied) → `37` (carrier_state)；child.parent=36 ✓
- `37` (carrier_state) → `38` (operand_read)；child.parent=37 ✓
- `38` (operand_read) → `39` (execute)；child.parent=38 ✓
- `39` (execute) → `40` (prf_writeback)；child.parent=39 ✓
- `40` (prf_writeback) → `41` (commit)；child.parent=40 ✓
- `41` (commit) → `132` (chain_end)；child.parent=41 ✓

- L5 真实见证：`41` kind=commit outcome=errant_commit oracle_diff=—

### fault 8

主链每一条边均验证为直接 parent：

- `42` (fault_applied) → `43` (carrier_state)；child.parent=42 ✓
- `43` (carrier_state) → `44` (operand_read)；child.parent=43 ✓
- `44` (operand_read) → `45` (execute)；child.parent=44 ✓
- `45` (execute) → `46` (prf_writeback)；child.parent=45 ✓
- `46` (prf_writeback) → `47` (commit)；child.parent=46 ✓
- `47` (commit) → `133` (chain_end)；child.parent=47 ✓

- L5 真实见证：`47` kind=commit outcome=errant_commit oracle_diff=—

### fault 9

主链每一条边均验证为直接 parent：

- `48` (fault_applied) → `49` (carrier_state)；child.parent=48 ✓
- `49` (carrier_state) → `50` (operand_read)；child.parent=49 ✓
- `50` (operand_read) → `51` (execute)；child.parent=50 ✓
- `51` (execute) → `52` (prf_writeback)；child.parent=51 ✓
- `52` (prf_writeback) → `53` (commit)；child.parent=52 ✓
- `53` (commit) → `134` (chain_end)；child.parent=53 ✓

- L5 真实见证：`53` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `dbc72847296067f07fba5ef84b5489e07c975efb22e75d9ce4e900148a5d6380` |
| `run.out` | `74887c83202c3634fa58d9e0515e80e769dbe29e5fc432d55dd4bfa3385534a2` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `0d3aafa4e35fb7ea85d3eddd69d92cde793a2ab79f132266998e64900c6f1197` |
| `oracle.json` | `b6d2d9c487bae5a448007d0b8e5077ac6028092a09ddcfa726186ee720d920e7` |
| `chain_report.json` | `cb8e29e40136a4bbd913aa9539a98305d99a8e9dacc16619acb0ca0ff8cb0e05` |
| `ordinals.json` | `1ef3a0a61e16a6e086a5788f3f6ef2e86e6cc0abe0dca98794e18ef2cf80a1a2` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `88a267b8d4e92e58be3b7351e36ebf35de98da4383c0c63eb3c0ef5ad8cd5164` |
| `inject/prop_evt.txt.gz` | `f7c175be5460bf82008c6af9195dda05184cb55e0ffd3cbd3e2510d8af63208d` |
| `inject/stats.txt` | `0d3aafa4e35fb7ea85d3eddd69d92cde793a2ab79f132266998e64900c6f1197` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 21 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
