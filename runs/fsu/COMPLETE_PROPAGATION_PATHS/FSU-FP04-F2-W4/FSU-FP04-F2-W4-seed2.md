# FSU-FP04-F2-W4 seed2 完整传播链

> 本文只使用本 seed（sample_run_id=`s2`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F2-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F2 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 2 / `s2` |
| selection seed / injection seed | 2 / 2 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F2-W4/seed2/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `c44191fd4351cc1635f52765cf0867dcc2ce846c` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F2-W4/seed2/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F2 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F2-W4/seed2/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 22 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 22 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F2 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 82214,202662,294538,353270,446917,529646,641990,704958,792846,851661,974416,1065147,1131198,1231961,1348566,1408575,1489110,1604180,1746423,1875343,1975890,2058002 --fpu_rate_warmup 0 --fsu_rate_divisor 100000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F2-W4 --prop_sample_run_id s2 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 100000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:82214, 1:202662, 2:294538, 3:353270, 4:446917, 5:529646, 6:641990, 7:704958, 8:792846, 9:851661, 10:974416, 11:1065147, 12:1131198, 13:1231961, 14:1348566, 15:1408575, 16:1489110, 17:1604180, 18:1746423, 19:1875343, 20:1975890, 21:2058002 |
| ordinals SHA-256 | `783007882a6f784e997d4a738226baf681326427b0312d2192e8286b0ea6c01c` |
| 注入数（actual/expected） | 22 / 22 |
| fault 数（事件流/injection log） | 22 / 22 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 137612475 / 357435 |
| sn / PC / opcode | 506164 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 82214 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 82214 / 0 |
| terminal | full |

### fault 10

| 字段 | 值 |
|---|---|
| 根 event_id | `54` |
| tick / cycle | 1307931625 / 3397225 |
| sn / PC / opcode | 5122839 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 851661 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 58815 / 9 |
| terminal | full |

### fault 11

| 字段 | 值 |
|---|---|
| 根 event_id | `60` |
| tick / cycle | 1494580780 / 3882028 |
| sn / PC / opcode | 5859396 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 974416 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 122755 / 10 |
| terminal | full |

### fault 12

| 字段 | 值 |
|---|---|
| 根 event_id | `66` |
| tick / cycle | 1632493555 / 4240243 |
| sn / PC / opcode | 6403755 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1065147 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 90731 / 11 |
| terminal | full |

### fault 13

| 字段 | 值 |
|---|---|
| 根 event_id | `72` |
| tick / cycle | 1732994725 / 4501285 |
| sn / PC / opcode | 6800077 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1131198 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 66051 / 12 |
| terminal | full |

### fault 14

| 字段 | 值 |
|---|---|
| 根 event_id | `78` |
| tick / cycle | 1886176215 / 4899159 |
| sn / PC / opcode | 7404659 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1231961 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 100763 / 13 |
| terminal | full |

### fault 15

| 字段 | 值 |
|---|---|
| 根 event_id | `84` |
| tick / cycle | 2063444460 / 5359596 |
| sn / PC / opcode | 8104285 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1348566 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 116605 / 14 |
| terminal | full |

### fault 16

| 字段 | 值 |
|---|---|
| 根 event_id | `90` |
| tick / cycle | 2154770310 / 5596806 |
| sn / PC / opcode | 8464323 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1408575 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 60009 / 15 |
| terminal | full |

### fault 17

| 字段 | 值 |
|---|---|
| 根 event_id | `96` |
| tick / cycle | 2277311190 / 5915094 |
| sn / PC / opcode | 8947549 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1489110 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 80535 / 16 |
| terminal | full |

### fault 18

| 字段 | 值 |
|---|---|
| 根 event_id | `102` |
| tick / cycle | 2611983990 / 6784374 |
| sn / PC / opcode | 9701749 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1604180 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 115070 / 17 |
| terminal | full |

### fault 19

| 字段 | 值 |
|---|---|
| 根 event_id | `108` |
| tick / cycle | 3427429005 / 8902413 |
| sn / PC / opcode | 10840575 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1746423 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 142243 / 18 |
| terminal | full |

### fault 2

| 字段 | 值 |
|---|---|
| 根 event_id | `6` |
| tick / cycle | 320867085 / 833421 |
| sn / PC / opcode | 1228861 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 202662 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 120448 / 1 |
| terminal | full |

### fault 20

| 字段 | 值 |
|---|---|
| 根 event_id | `114` |
| tick / cycle | 4160961420 / 10807692 |
| sn / PC / opcode | 11872673 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1875343 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 128920 / 19 |
| terminal | full |

### fault 21

| 字段 | 值 |
|---|---|
| 根 event_id | `120` |
| tick / cycle | 4730086130 / 12285938 |
| sn / PC / opcode | 12677683 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1975890 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 100547 / 20 |
| terminal | full |

### fault 22

| 字段 | 值 |
|---|---|
| 根 event_id | `126` |
| tick / cycle | 5196930200 / 13498520 |
| sn / PC / opcode | 13335069 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 2058002 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 82112 / 21 |
| terminal | full |

### fault 3

| 字段 | 值 |
|---|---|
| 根 event_id | `12` |
| tick / cycle | 460647110 / 1196486 |
| sn / PC / opcode | 1780128 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 294538 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 91876 / 2 |
| terminal | full |

### fault 4

| 字段 | 值 |
|---|---|
| 根 event_id | `18` |
| tick / cycle | 549917445 / 1428357 |
| sn / PC / opcode | 2132500 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 353270 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 58732 / 3 |
| terminal | full |

### fault 5

| 字段 | 值 |
|---|---|
| 根 event_id | `24` |
| tick / cycle | 692408255 / 1798463 |
| sn / PC / opcode | 2694386 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 446917 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 93647 / 4 |
| terminal | full |

### fault 6

| 字段 | 值 |
|---|---|
| 根 event_id | `30` |
| tick / cycle | 818206235 / 2125211 |
| sn / PC / opcode | 3190756 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 529646 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 82729 / 5 |
| terminal | full |

### fault 7

| 字段 | 值 |
|---|---|
| 根 event_id | `36` |
| tick / cycle | 988926015 / 2568639 |
| sn / PC / opcode | 3864820 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 641990 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 112344 / 6 |
| terminal | full |

### fault 8

| 字段 | 值 |
|---|---|
| 根 event_id | `42` |
| tick / cycle | 1084854540 / 2817804 |
| sn / PC / opcode | 4242637 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 704958 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 62968 / 7 |
| terminal | full |

### fault 9

| 字段 | 值 |
|---|---|
| 根 event_id | `48` |
| tick / cycle | 1218481880 / 3164888 |
| sn / PC / opcode | 4769965 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 792846 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 87888 / 8 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 3427429005, Site: dyn_inst_execute, opClass=8, sn=10840575, bitseg=mant_lo, mask=0x4, faults_injected: 19
Tick: 4160961420, Site: dyn_inst_execute, opClass=8, sn=11872673, bitseg=mant_lo, mask=0x40, faults_injected: 20
Tick: 4730086130, Site: dyn_inst_execute, opClass=8, sn=12677683, bitseg=mant_lo, mask=0x400, faults_injected: 21
Tick: 5196930200, Site: dyn_inst_execute, opClass=8, sn=13335069, bitseg=mant_lo, mask=0x1000, faults_injected: 22
CHAOS_RATE_COMPLETE=22
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc3b645a1cac084 → 0x3fc3b645a1cac085 |
| old/new hash | 0x5c409c882e19cd0b → 0x1b02fb3dbfdf7c9a |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc3b645a1cac084 / 0x3fc3b645a1cac085 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 10

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe9cac083126e98 → 0x3fe9cac08312ee98 |
| old/new hash | 0xfba2883d371b3060 → 0xfbf4903bdd28fae0 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe9cac083126e98 / 0x3fe9cac08312ee98 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 11

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4084a80000000000 → 0x4084a80000000040 |
| old/new hash | 0x971fad7b75e8bd0f → 0xff4cefc319bac9cf |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4084a80000000000 / 0x4084a80000000040 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 12

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3a1cac083126f → 0x3ff3a1cac083126d |
| old/new hash | 0x1b578561a90d777a → 0x1ace6508d4e059f8 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3a1cac083126f / 0x3ff3a1cac083126d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 13

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081380000000000 → 0x4081380000000800 |
| old/new hash | 0x79ca5f7e3b3d8ff2 → 0xd9cdb32bfb1e0a4a |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081380000000000 / 0x4081380000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 14

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087e00000000000 → 0x4087e00000000002 |
| old/new hash | 0x0a26137cda02dcac → 0x77809d6850307f8e |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087e00000000000 / 0x4087e00000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 15

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4036000000000000 → 0x4036000000000008 |
| old/new hash | 0x47ce397eaf6578e5 → 0x3f3831c706843e4d |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4036000000000000 / 0x4036000000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 16

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd989374bc6a7f0 → 0x3fd989374bc6aff0 |
| old/new hash | 0x4ba196fa03a8f321 → 0x3c2a194a4c5b7089 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd989374bc6a7f0 / 0x3fd989374bc6aff0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 17

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081a00000000000 → 0x4081a00000000002 |
| old/new hash | 0xdfc1077b9ffe451a → 0x9e657969873c87d8 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081a00000000000 / 0x4081a00000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 18

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd33a92a3055327 → 0x3fd33a92a3055b27 |
| old/new hash | 0xb3a61dfc87cef843 → 0x0ca2ea007bfb2d6b |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd33a92a3055327 / 0x3fd33a92a3055b27 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 19

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef5a1a93293d10 → 0x3fef5a1a93293d14 |
| old/new hash | 0x80b1b3faef2decd6 → 0x41c7666b5558e552 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef5a1a93293d10 / 0x3fef5a1a93293d14 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 2

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4062800000000000 → 0x4062800000008000 |
| old/new hash | 0xf3a6c17c3be607f1 → 0xf3e3fc5839fb4571 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4062800000000000 / 0x4062800000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 20

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd31b21c475e636 → 0x3fd31b21c475e676 |
| old/new hash | 0xdbac3b48aeb98208 → 0xe1267169f0b90848 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd31b21c475e636 / 0x3fd31b21c475e676 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 21

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea3854046412d0 → 0x3fea3854046416d0 |
| old/new hash | 0x8fc3284ac088a676 → 0x744b8a2ee835a872 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea3854046412d0 / 0x3fea3854046416d0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 22

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe6a64c2f837b4a → 0x3fe6a64c2f836b4a |
| old/new hash | 0x26ba75f773c4344b → 0xfb8592ae19f52efb |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe6a64c2f837b4a / 0x3fe6a64c2f836b4a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 3

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4075b00000000000 → 0x4075b00000020000 |
| old/new hash | 0x67362f7bebd3ec7e → 0x6e67471b96614e6c |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4075b00000000000 / 0x4075b00000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 4

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc83126e978d4fe → 0xbfc83126e978d4ff |
| old/new hash | 0x1993bd4c799f2e42 → 0xdb2cb3a3db199b6b |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc83126e978d4fe / 0xbfc83126e978d4ff |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 5

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe0083126e978d5 → 0x3fe0083126e979d5 |
| old/new hash | 0x62631d0d388b7b1d → 0xdc5176dbbd91f8ba |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe0083126e978d5 / 0x3fe0083126e979d5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 6

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd16872b020c49c → 0xbfd16872b020c494 |
| old/new hash | 0x442ea96c782f381d → 0x4006ab4ade5b8ef5 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd16872b020c49c / 0xbfd16872b020c494 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 7

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfcc083126e978d5 → 0xbfcc083126e978d4 |
| old/new hash | 0x621e9d0d3850d4d1 → 0x04f9f1bb389b68cc |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfcc083126e978d5 / 0xbfcc083126e978d4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 8

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407a300000000000 → 0x407a300000002000 |
| old/new hash | 0xbbc8017e5fae9269 → 0x930232c9d6521dc9 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407a300000000000 / 0x407a300000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 9

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408e800000000000 → 0x408e800000000100 |
| old/new hash | 0xf178e97c3a0ba82d → 0xd91505f6d32535f6 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408e800000000000 / 0x408e800000000100 |
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
| 7 | chain_end | — | 132 | 5 |

### fault 10（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 54 | — |
| 2 | carrier_state | L1 | 55 | 54 |
| 3 | operand_read | L2 | 56 | 55 |
| 4 | execute | L3 | 57 | 56 |
| 5 | prf_writeback | L4 | 58 | 57 |
| 6 | commit | L5 | 59 | 58 |
| 7 | chain_end | — | 141 | 59 |

### fault 11（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 60 | — |
| 2 | carrier_state | L1 | 61 | 60 |
| 3 | operand_read | L2 | 62 | 61 |
| 4 | execute | L3 | 63 | 62 |
| 5 | prf_writeback | L4 | 64 | 63 |
| 6 | commit | L5 | 65 | 64 |
| 7 | chain_end | — | 142 | 65 |

### fault 12（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 66 | — |
| 2 | carrier_state | L1 | 67 | 66 |
| 3 | operand_read | L2 | 68 | 67 |
| 4 | execute | L3 | 69 | 68 |
| 5 | prf_writeback | L4 | 70 | 69 |
| 6 | commit | L5 | 71 | 70 |
| 7 | chain_end | — | 143 | 71 |

### fault 13（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 72 | — |
| 2 | carrier_state | L1 | 73 | 72 |
| 3 | operand_read | L2 | 74 | 73 |
| 4 | execute | L3 | 75 | 74 |
| 5 | prf_writeback | L4 | 76 | 75 |
| 6 | commit | L5 | 77 | 76 |
| 7 | chain_end | — | 144 | 77 |

### fault 14（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 78 | — |
| 2 | carrier_state | L1 | 79 | 78 |
| 3 | operand_read | L2 | 80 | 79 |
| 4 | execute | L3 | 81 | 80 |
| 5 | prf_writeback | L4 | 82 | 81 |
| 6 | commit | L5 | 83 | 82 |
| 7 | chain_end | — | 145 | 83 |

### fault 15（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 84 | — |
| 2 | carrier_state | L1 | 85 | 84 |
| 3 | operand_read | L2 | 86 | 85 |
| 4 | execute | L3 | 87 | 86 |
| 5 | prf_writeback | L4 | 88 | 87 |
| 6 | commit | L5 | 89 | 88 |
| 7 | chain_end | — | 146 | 89 |

### fault 16（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 90 | — |
| 2 | carrier_state | L1 | 91 | 90 |
| 3 | operand_read | L2 | 92 | 91 |
| 4 | execute | L3 | 93 | 92 |
| 5 | prf_writeback | L4 | 94 | 93 |
| 6 | commit | L5 | 95 | 94 |
| 7 | chain_end | — | 147 | 95 |

### fault 17（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 96 | — |
| 2 | carrier_state | L1 | 97 | 96 |
| 3 | operand_read | L2 | 98 | 97 |
| 4 | execute | L3 | 99 | 98 |
| 5 | prf_writeback | L4 | 100 | 99 |
| 6 | commit | L5 | 101 | 100 |
| 7 | chain_end | — | 148 | 101 |

### fault 18（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 102 | — |
| 2 | carrier_state | L1 | 103 | 102 |
| 3 | operand_read | L2 | 104 | 103 |
| 4 | execute | L3 | 105 | 104 |
| 5 | prf_writeback | L4 | 106 | 105 |
| 6 | commit | L5 | 107 | 106 |
| 7 | chain_end | — | 149 | 107 |

### fault 19（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 108 | — |
| 2 | carrier_state | L1 | 109 | 108 |
| 3 | operand_read | L2 | 110 | 109 |
| 4 | execute | L3 | 111 | 110 |
| 5 | prf_writeback | L4 | 112 | 111 |
| 6 | commit | L5 | 113 | 112 |
| 7 | chain_end | — | 150 | 113 |

### fault 2（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 6 | — |
| 2 | carrier_state | L1 | 7 | 6 |
| 3 | operand_read | L2 | 8 | 7 |
| 4 | execute | L3 | 9 | 8 |
| 5 | prf_writeback | L4 | 10 | 9 |
| 6 | commit | L5 | 11 | 10 |
| 7 | chain_end | — | 133 | 11 |

### fault 20（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 114 | — |
| 2 | carrier_state | L1 | 115 | 114 |
| 3 | operand_read | L2 | 116 | 115 |
| 4 | execute | L3 | 117 | 116 |
| 5 | prf_writeback | L4 | 118 | 117 |
| 6 | commit | L5 | 119 | 118 |
| 7 | chain_end | — | 151 | 119 |

### fault 21（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 120 | — |
| 2 | carrier_state | L1 | 121 | 120 |
| 3 | operand_read | L2 | 122 | 121 |
| 4 | execute | L3 | 123 | 122 |
| 5 | prf_writeback | L4 | 124 | 123 |
| 6 | commit | L5 | 125 | 124 |
| 7 | chain_end | — | 152 | 125 |

### fault 22（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 126 | — |
| 2 | carrier_state | L1 | 127 | 126 |
| 3 | operand_read | L2 | 128 | 127 |
| 4 | execute | L3 | 129 | 128 |
| 5 | prf_writeback | L4 | 130 | 129 |
| 6 | commit | L5 | 131 | 130 |
| 7 | chain_end | — | 153 | 131 |

### fault 3（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 12 | — |
| 2 | carrier_state | L1 | 13 | 12 |
| 3 | operand_read | L2 | 14 | 13 |
| 4 | execute | L3 | 15 | 14 |
| 5 | prf_writeback | L4 | 16 | 15 |
| 6 | commit | L5 | 17 | 16 |
| 7 | chain_end | — | 134 | 17 |

### fault 4（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 18 | — |
| 2 | carrier_state | L1 | 19 | 18 |
| 3 | operand_read | L2 | 20 | 19 |
| 4 | execute | L3 | 21 | 20 |
| 5 | prf_writeback | L4 | 22 | 21 |
| 6 | commit | L5 | 23 | 22 |
| 7 | chain_end | — | 135 | 23 |

### fault 5（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 24 | — |
| 2 | carrier_state | L1 | 25 | 24 |
| 3 | operand_read | L2 | 26 | 25 |
| 4 | execute | L3 | 27 | 26 |
| 5 | prf_writeback | L4 | 28 | 27 |
| 6 | commit | L5 | 29 | 28 |
| 7 | chain_end | — | 136 | 29 |

### fault 6（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 30 | — |
| 2 | carrier_state | L1 | 31 | 30 |
| 3 | operand_read | L2 | 32 | 31 |
| 4 | execute | L3 | 33 | 32 |
| 5 | prf_writeback | L4 | 34 | 33 |
| 6 | commit | L5 | 35 | 34 |
| 7 | chain_end | — | 137 | 35 |

### fault 7（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 36 | — |
| 2 | carrier_state | L1 | 37 | 36 |
| 3 | operand_read | L2 | 38 | 37 |
| 4 | execute | L3 | 39 | 38 |
| 5 | prf_writeback | L4 | 40 | 39 |
| 6 | commit | L5 | 41 | 40 |
| 7 | chain_end | — | 138 | 41 |

### fault 8（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 42 | — |
| 2 | carrier_state | L1 | 43 | 42 |
| 3 | operand_read | L2 | 44 | 43 |
| 4 | execute | L3 | 45 | 44 |
| 5 | prf_writeback | L4 | 46 | 45 |
| 6 | commit | L5 | 47 | 46 |
| 7 | chain_end | — | 139 | 47 |

### fault 9（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 48 | — |
| 2 | carrier_state | L1 | 49 | 48 |
| 3 | operand_read | L2 | 50 | 49 |
| 4 | execute | L3 | 51 | 50 |
| 5 | prf_writeback | L4 | 52 | 51 |
| 6 | commit | L5 | 53 | 52 |
| 7 | chain_end | — | 140 | 53 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 137612475 | 1 | 506164 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fc3b645a1cac084→0x3fc3b645a1cac085 | — | — | origin |
| carrier_state | 1 | 0 | 137612475 | 1 | 506164 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fc3b645a1cac084→0x3fc3b645a1cac085 | — | — | fsu_taint |
| operand_read | 2 | 1 | 137627875 | 1 | 506234 | 0x0000000000400654 | fmadd | 506164/506234 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 137627875 | 1 | 506234 | 0x0000000000400654 | fmadd | 506164/506234 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 137627875 | 1 | 506234 | 0x0000000000400654 | fmadd | 506164/506234 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 137628645 | 1 | 506234 | 0x0000000000400654 | fmadd | —/506234 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 132 | 5 | 9405448360 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 54 | — | 1307931625 | 10 | 5122839 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fe9cac083126e98→0x3fe9cac08312ee98 | — | — | origin |
| carrier_state | 55 | 54 | 1307931625 | 10 | 5122839 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fe9cac083126e98→0x3fe9cac08312ee98 | — | — | fsu_taint |
| operand_read | 56 | 55 | 1307955880 | 10 | 5122946 | 0x0000000000400654 | fmadd | 5122839/5122946 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 57 | 56 | 1307955880 | 10 | 5122946 | 0x0000000000400654 | fmadd | 5122839/5122946 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 58 | 57 | 1307955880 | 10 | 5122946 | 0x0000000000400654 | fmadd | 5122839/5122946 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 59 | 58 | 1307956650 | 10 | 5122946 | 0x0000000000400654 | fmadd | —/5122946 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 141 | 59 | 9405448360 | 10 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 60 | — | 1494580780 | 11 | 5859396 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4084a80000000000→0x4084a80000000040 | — | — | origin |
| carrier_state | 61 | 60 | 1494580780 | 11 | 5859396 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4084a80000000000→0x4084a80000000040 | — | — | fsu_taint |
| operand_read | 62 | 61 | 1494585015 | 11 | 5859399 | 0x0000000000400658 | fmadd | 5859396/5859399 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 63 | 62 | 1494585015 | 11 | 5859399 | 0x0000000000400658 | fmadd | 5859396/5859399 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 64 | 63 | 1494585015 | 11 | 5859399 | 0x0000000000400658 | fmadd | 5859396/5859399 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 65 | 64 | 1494585785 | 11 | 5859399 | 0x0000000000400658 | fmadd | —/5859399 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 142 | 65 | 9405448360 | 11 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 66 | — | 1632493555 | 12 | 6403755 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff3a1cac083126f→0x3ff3a1cac083126d | — | — | origin |
| carrier_state | 67 | 66 | 1632493555 | 12 | 6403755 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff3a1cac083126f→0x3ff3a1cac083126d | — | — | fsu_taint |
| operand_read | 68 | 67 | 1632517810 | 12 | 6403862 | 0x0000000000400654 | fmadd | 6403755/6403862 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 69 | 68 | 1632517810 | 12 | 6403862 | 0x0000000000400654 | fmadd | 6403755/6403862 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 70 | 69 | 1632517810 | 12 | 6403862 | 0x0000000000400654 | fmadd | 6403755/6403862 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 71 | 70 | 1632518580 | 12 | 6403862 | 0x0000000000400654 | fmadd | —/6403862 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 143 | 71 | 9405448360 | 12 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 72 | — | 1732994725 | 13 | 6800077 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4081380000000000→0x4081380000000800 | — | — | origin |
| carrier_state | 73 | 72 | 1732994725 | 13 | 6800077 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4081380000000000→0x4081380000000800 | — | — | fsu_taint |
| operand_read | 74 | 73 | 1732998575 | 13 | 6800080 | 0x000000000040065c | fmadd | 6800077/6800080 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 75 | 74 | 1732998575 | 13 | 6800080 | 0x000000000040065c | fmadd | 6800077/6800080 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 76 | 75 | 1732998575 | 13 | 6800080 | 0x000000000040065c | fmadd | 6800077/6800080 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 77 | 76 | 1732999345 | 13 | 6800080 | 0x000000000040065c | fmadd | —/6800080 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 144 | 77 | 9405448360 | 13 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 78 | — | 1886176215 | 14 | 7404659 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4087e00000000000→0x4087e00000000002 | — | — | origin |
| carrier_state | 79 | 78 | 1886176215 | 14 | 7404659 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4087e00000000000→0x4087e00000000002 | — | — | fsu_taint |
| operand_read | 80 | 79 | 1886178140 | 14 | 7404662 | 0x0000000000400654 | fmadd | 7404659/7404662 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 81 | 80 | 1886178140 | 14 | 7404662 | 0x0000000000400654 | fmadd | 7404659/7404662 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 82 | 81 | 1886178140 | 14 | 7404662 | 0x0000000000400654 | fmadd | 7404659/7404662 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 83 | 82 | 1886178910 | 14 | 7404662 | 0x0000000000400654 | fmadd | —/7404662 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 145 | 83 | 9405448360 | 14 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 84 | — | 2063444460 | 15 | 8104285 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4036000000000000→0x4036000000000008 | — | — | origin |
| carrier_state | 85 | 84 | 2063444460 | 15 | 8104285 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4036000000000000→0x4036000000000008 | — | — | fsu_taint |
| operand_read | 86 | 85 | 2063448310 | 15 | 8104288 | 0x000000000040065c | fmadd | 8104285/8104288 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 87 | 86 | 2063448310 | 15 | 8104288 | 0x000000000040065c | fmadd | 8104285/8104288 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 88 | 87 | 2063448310 | 15 | 8104288 | 0x000000000040065c | fmadd | 8104285/8104288 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 89 | 88 | 2063449080 | 15 | 8104288 | 0x000000000040065c | fmadd | —/8104288 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 146 | 89 | 9405448360 | 15 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 90 | — | 2154770310 | 16 | 8464323 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fd989374bc6a7f0→0x3fd989374bc6aff0 | — | — | origin |
| carrier_state | 91 | 90 | 2154770310 | 16 | 8464323 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fd989374bc6a7f0→0x3fd989374bc6aff0 | — | — | fsu_taint |
| operand_read | 92 | 91 | 2154794565 | 16 | 8464430 | 0x0000000000400654 | fmadd | 8464323/8464430 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 93 | 92 | 2154794565 | 16 | 8464430 | 0x0000000000400654 | fmadd | 8464323/8464430 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 94 | 93 | 2154794565 | 16 | 8464430 | 0x0000000000400654 | fmadd | 8464323/8464430 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 95 | 94 | 2154795335 | 16 | 8464430 | 0x0000000000400654 | fmadd | —/8464430 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 147 | 95 | 9405448360 | 16 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 96 | — | 2277311190 | 17 | 8947549 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4081a00000000000→0x4081a00000000002 | — | — | origin |
| carrier_state | 97 | 96 | 2277311190 | 17 | 8947549 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4081a00000000000→0x4081a00000000002 | — | — | fsu_taint |
| operand_read | 98 | 97 | 2277315040 | 17 | 8947552 | 0x000000000040065c | fmadd | 8947549/8947552 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 99 | 98 | 2277315040 | 17 | 8947552 | 0x000000000040065c | fmadd | 8947549/8947552 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 100 | 99 | 2277315040 | 17 | 8947552 | 0x000000000040065c | fmadd | 8947549/8947552 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 101 | 100 | 2277315810 | 17 | 8947552 | 0x000000000040065c | fmadd | —/8947552 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 148 | 101 | 9405448360 | 17 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 102 | — | 2611983990 | 18 | 9701749 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fd33a92a3055327→0x3fd33a92a3055b27 | — | — | origin |
| carrier_state | 103 | 102 | 2611983990 | 18 | 9701749 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fd33a92a3055327→0x3fd33a92a3055b27 | — | — | fsu_taint |
| operand_read | 104 | 103 | 2611992460 | 18 | 9701765 | 0x00000000004006cc | fmadd | 9701749/9701765 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 105 | 104 | 2611992460 | 18 | 9701765 | 0x00000000004006cc | fmadd | 9701749/9701765 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 106 | 105 | 2611992460 | 18 | 9701765 | 0x00000000004006cc | fmadd | 9701749/9701765 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 107 | 106 | 2611993230 | 18 | 9701765 | 0x00000000004006cc | fmadd | —/9701765 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 149 | 107 | 9405448360 | 18 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 108 | — | 3427429005 | 19 | 10840575 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fef5a1a93293d10→0x3fef5a1a93293d14 | — | — | origin |
| carrier_state | 109 | 108 | 3427429005 | 19 | 10840575 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fef5a1a93293d10→0x3fef5a1a93293d14 | — | — | fsu_taint |
| operand_read | 110 | 109 | 3427437475 | 19 | 10840591 | 0x00000000004006cc | fmadd | 10840575/10840591 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 111 | 110 | 3427437475 | 19 | 10840591 | 0x00000000004006cc | fmadd | 10840575/10840591 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 112 | 111 | 3427437475 | 19 | 10840591 | 0x00000000004006cc | fmadd | 10840575/10840591 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 113 | 112 | 3427438245 | 19 | 10840591 | 0x00000000004006cc | fmadd | —/10840591 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 150 | 113 | 9405448360 | 19 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 6 | — | 320867085 | 2 | 1228861 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4062800000000000→0x4062800000008000 | — | — | origin |
| carrier_state | 7 | 6 | 320867085 | 2 | 1228861 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4062800000000000→0x4062800000008000 | — | — | fsu_taint |
| operand_read | 8 | 7 | 320870935 | 2 | 1228864 | 0x000000000040065c | fmadd | 1228861/1228864 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 320870935 | 2 | 1228864 | 0x000000000040065c | fmadd | 1228861/1228864 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 320870935 | 2 | 1228864 | 0x000000000040065c | fmadd | 1228861/1228864 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 320871705 | 2 | 1228864 | 0x000000000040065c | fmadd | —/1228864 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 133 | 11 | 9405448360 | 2 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 114 | — | 4160961420 | 20 | 11872673 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fd31b21c475e636→0x3fd31b21c475e676 | — | — | origin |
| carrier_state | 115 | 114 | 4160961420 | 20 | 11872673 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fd31b21c475e636→0x3fd31b21c475e676 | — | — | fsu_taint |
| operand_read | 116 | 115 | 4160969890 | 20 | 11872689 | 0x00000000004006a4 | fmadd | 11872673/11872689 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 117 | 116 | 4160969890 | 20 | 11872689 | 0x00000000004006a4 | fmadd | 11872673/11872689 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 118 | 117 | 4160969890 | 20 | 11872689 | 0x00000000004006a4 | fmadd | 11872673/11872689 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 119 | 118 | 4160970660 | 20 | 11872689 | 0x00000000004006a4 | fmadd | —/11872689 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 151 | 119 | 9405448360 | 20 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 120 | — | 4730086130 | 21 | 12677683 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fea3854046412d0→0x3fea3854046416d0 | — | — | origin |
| carrier_state | 121 | 120 | 4730086130 | 21 | 12677683 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fea3854046412d0→0x3fea3854046416d0 | — | — | fsu_taint |
| operand_read | 122 | 121 | 4730094600 | 21 | 12677699 | 0x00000000004006cc | fmadd | 12677683/12677699 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 123 | 122 | 4730094600 | 21 | 12677699 | 0x00000000004006cc | fmadd | 12677683/12677699 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 124 | 123 | 4730094600 | 21 | 12677699 | 0x00000000004006cc | fmadd | 12677683/12677699 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 125 | 124 | 4730095370 | 21 | 12677699 | 0x00000000004006cc | fmadd | —/12677699 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 152 | 125 | 9405448360 | 21 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 126 | — | 5196930200 | 22 | 13335069 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe6a64c2f837b4a→0x3fe6a64c2f836b4a | — | — | origin |
| carrier_state | 127 | 126 | 5196930200 | 22 | 13335069 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe6a64c2f837b4a→0x3fe6a64c2f836b4a | — | — | fsu_taint |
| operand_read | 128 | 127 | 5196938670 | 22 | 13335085 | 0x00000000004006cc | fmadd | 13335069/13335085 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 129 | 128 | 5196938670 | 22 | 13335085 | 0x00000000004006cc | fmadd | 13335069/13335085 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 130 | 129 | 5196938670 | 22 | 13335085 | 0x00000000004006cc | fmadd | 13335069/13335085 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 131 | 130 | 5196939440 | 22 | 13335085 | 0x00000000004006cc | fmadd | —/13335085 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 153 | 131 | 9405448360 | 22 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 12 | — | 460647110 | 3 | 1780128 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4075b00000000000→0x4075b00000020000 | — | — | origin |
| carrier_state | 13 | 12 | 460647110 | 3 | 1780128 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4075b00000000000→0x4075b00000020000 | — | — | fsu_taint |
| operand_read | 14 | 13 | 460651345 | 3 | 1780131 | 0x0000000000400658 | fmadd | 1780128/1780131 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 15 | 14 | 460651345 | 3 | 1780131 | 0x0000000000400658 | fmadd | 1780128/1780131 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 16 | 15 | 460651345 | 3 | 1780131 | 0x0000000000400658 | fmadd | 1780128/1780131 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 17 | 16 | 460652115 | 3 | 1780131 | 0x0000000000400658 | fmadd | —/1780131 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 134 | 17 | 9405448360 | 3 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 18 | — | 549917445 | 4 | 2132500 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfc83126e978d4fe→0xbfc83126e978d4ff | — | — | origin |
| carrier_state | 19 | 18 | 549917445 | 4 | 2132500 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfc83126e978d4fe→0xbfc83126e978d4ff | — | — | fsu_taint |
| operand_read | 20 | 19 | 549932845 | 4 | 2132570 | 0x0000000000400654 | fmadd | 2132500/2132570 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 21 | 20 | 549932845 | 4 | 2132570 | 0x0000000000400654 | fmadd | 2132500/2132570 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 22 | 21 | 549932845 | 4 | 2132570 | 0x0000000000400654 | fmadd | 2132500/2132570 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 23 | 22 | 549933615 | 4 | 2132570 | 0x0000000000400654 | fmadd | —/2132570 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 135 | 23 | 9405448360 | 4 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 24 | — | 692408255 | 5 | 2694386 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3fe0083126e978d5→0x3fe0083126e979d5 | — | — | origin |
| carrier_state | 25 | 24 | 692408255 | 5 | 2694386 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3fe0083126e978d5→0x3fe0083126e979d5 | — | — | fsu_taint |
| operand_read | 26 | 25 | 692443675 | 5 | 2694530 | 0x0000000000400654 | fmadd | 2694386/2694530 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 27 | 26 | 692443675 | 5 | 2694530 | 0x0000000000400654 | fmadd | 2694386/2694530 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 28 | 27 | 692443675 | 5 | 2694530 | 0x0000000000400654 | fmadd | 2694386/2694530 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 29 | 28 | 692444445 | 5 | 2694530 | 0x0000000000400654 | fmadd | —/2694530 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 136 | 29 | 9405448360 | 5 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 30 | — | 818206235 | 6 | 3190756 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd16872b020c49c→0xbfd16872b020c494 | — | — | origin |
| carrier_state | 31 | 30 | 818206235 | 6 | 3190756 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd16872b020c49c→0xbfd16872b020c494 | — | — | fsu_taint |
| operand_read | 32 | 31 | 818221635 | 6 | 3190826 | 0x0000000000400654 | fmadd | 3190756/3190826 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 33 | 32 | 818221635 | 6 | 3190826 | 0x0000000000400654 | fmadd | 3190756/3190826 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 34 | 33 | 818221635 | 6 | 3190826 | 0x0000000000400654 | fmadd | 3190756/3190826 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 35 | 34 | 818222405 | 6 | 3190826 | 0x0000000000400654 | fmadd | —/3190826 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 137 | 35 | 9405448360 | 6 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 36 | — | 988926015 | 7 | 3864820 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfcc083126e978d5→0xbfcc083126e978d4 | — | — | origin |
| carrier_state | 37 | 36 | 988926015 | 7 | 3864820 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfcc083126e978d5→0xbfcc083126e978d4 | — | — | fsu_taint |
| operand_read | 38 | 37 | 988941415 | 7 | 3864890 | 0x0000000000400654 | fmadd | 3864820/3864890 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 39 | 38 | 988941415 | 7 | 3864890 | 0x0000000000400654 | fmadd | 3864820/3864890 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 40 | 39 | 988941415 | 7 | 3864890 | 0x0000000000400654 | fmadd | 3864820/3864890 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 41 | 40 | 988942185 | 7 | 3864890 | 0x0000000000400654 | fmadd | —/3864890 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 138 | 41 | 9405448360 | 7 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 42 | — | 1084854540 | 8 | 4242637 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x407a300000000000→0x407a300000002000 | — | — | origin |
| carrier_state | 43 | 42 | 1084854540 | 8 | 4242637 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x407a300000000000→0x407a300000002000 | — | — | fsu_taint |
| operand_read | 44 | 43 | 1084858390 | 8 | 4242640 | 0x000000000040065c | fmadd | 4242637/4242640 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 45 | 44 | 1084858390 | 8 | 4242640 | 0x000000000040065c | fmadd | 4242637/4242640 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 46 | 45 | 1084858390 | 8 | 4242640 | 0x000000000040065c | fmadd | 4242637/4242640 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 47 | 46 | 1084859160 | 8 | 4242640 | 0x000000000040065c | fmadd | —/4242640 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 139 | 47 | 9405448360 | 8 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 48 | — | 1218481880 | 9 | 4769965 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x408e800000000000→0x408e800000000100 | — | — | origin |
| carrier_state | 49 | 48 | 1218481880 | 9 | 4769965 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x408e800000000000→0x408e800000000100 | — | — | fsu_taint |
| operand_read | 50 | 49 | 1218485730 | 9 | 4769968 | 0x000000000040065c | fmadd | 4769965/4769968 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 51 | 50 | 1218485730 | 9 | 4769968 | 0x000000000040065c | fmadd | 4769965/4769968 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 52 | 51 | 1218485730 | 9 | 4769968 | 0x000000000040065c | fmadd | 4769965/4769968 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 53 | 52 | 1218486500 | 9 | 4769968 | 0x000000000040065c | fmadd | —/4769968 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 140 | 53 | 9405448360 | 9 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

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

### fault 22

- **L0**：fault_applied#126（本 seed 真实事件）。
- **L1**：carrier_state#127（本 seed 真实事件）。
- **L2**：operand_read#128（本 seed 真实事件）。
- **L3**：execute#129（本 seed 真实事件）。
- **L4**：prf_writeback#130（本 seed 真实事件）。
- **L5**：commit#131（本 seed 真实事件）。

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

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 9ca60bf91e8c7b822cc886d2835cc06628f57f2c2baab6f3497ad0afbaf80d1d != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：22 / 22
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：154
- attempted / eligible / activated：22 / 2097155 / 22

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
| 22 | full | L5 | True | True | [] | 131 | N/A / N/A |
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
- `5` (commit) → `132` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

### fault 10

主链每一条边均验证为直接 parent：

- `54` (fault_applied) → `55` (carrier_state)；child.parent=54 ✓
- `55` (carrier_state) → `56` (operand_read)；child.parent=55 ✓
- `56` (operand_read) → `57` (execute)；child.parent=56 ✓
- `57` (execute) → `58` (prf_writeback)；child.parent=57 ✓
- `58` (prf_writeback) → `59` (commit)；child.parent=58 ✓
- `59` (commit) → `141` (chain_end)；child.parent=59 ✓

- L5 真实见证：`59` kind=commit outcome=errant_commit oracle_diff=—

### fault 11

主链每一条边均验证为直接 parent：

- `60` (fault_applied) → `61` (carrier_state)；child.parent=60 ✓
- `61` (carrier_state) → `62` (operand_read)；child.parent=61 ✓
- `62` (operand_read) → `63` (execute)；child.parent=62 ✓
- `63` (execute) → `64` (prf_writeback)；child.parent=63 ✓
- `64` (prf_writeback) → `65` (commit)；child.parent=64 ✓
- `65` (commit) → `142` (chain_end)；child.parent=65 ✓

- L5 真实见证：`65` kind=commit outcome=errant_commit oracle_diff=—

### fault 12

主链每一条边均验证为直接 parent：

- `66` (fault_applied) → `67` (carrier_state)；child.parent=66 ✓
- `67` (carrier_state) → `68` (operand_read)；child.parent=67 ✓
- `68` (operand_read) → `69` (execute)；child.parent=68 ✓
- `69` (execute) → `70` (prf_writeback)；child.parent=69 ✓
- `70` (prf_writeback) → `71` (commit)；child.parent=70 ✓
- `71` (commit) → `143` (chain_end)；child.parent=71 ✓

- L5 真实见证：`71` kind=commit outcome=errant_commit oracle_diff=—

### fault 13

主链每一条边均验证为直接 parent：

- `72` (fault_applied) → `73` (carrier_state)；child.parent=72 ✓
- `73` (carrier_state) → `74` (operand_read)；child.parent=73 ✓
- `74` (operand_read) → `75` (execute)；child.parent=74 ✓
- `75` (execute) → `76` (prf_writeback)；child.parent=75 ✓
- `76` (prf_writeback) → `77` (commit)；child.parent=76 ✓
- `77` (commit) → `144` (chain_end)；child.parent=77 ✓

- L5 真实见证：`77` kind=commit outcome=errant_commit oracle_diff=—

### fault 14

主链每一条边均验证为直接 parent：

- `78` (fault_applied) → `79` (carrier_state)；child.parent=78 ✓
- `79` (carrier_state) → `80` (operand_read)；child.parent=79 ✓
- `80` (operand_read) → `81` (execute)；child.parent=80 ✓
- `81` (execute) → `82` (prf_writeback)；child.parent=81 ✓
- `82` (prf_writeback) → `83` (commit)；child.parent=82 ✓
- `83` (commit) → `145` (chain_end)；child.parent=83 ✓

- L5 真实见证：`83` kind=commit outcome=errant_commit oracle_diff=—

### fault 15

主链每一条边均验证为直接 parent：

- `84` (fault_applied) → `85` (carrier_state)；child.parent=84 ✓
- `85` (carrier_state) → `86` (operand_read)；child.parent=85 ✓
- `86` (operand_read) → `87` (execute)；child.parent=86 ✓
- `87` (execute) → `88` (prf_writeback)；child.parent=87 ✓
- `88` (prf_writeback) → `89` (commit)；child.parent=88 ✓
- `89` (commit) → `146` (chain_end)；child.parent=89 ✓

- L5 真实见证：`89` kind=commit outcome=errant_commit oracle_diff=—

### fault 16

主链每一条边均验证为直接 parent：

- `90` (fault_applied) → `91` (carrier_state)；child.parent=90 ✓
- `91` (carrier_state) → `92` (operand_read)；child.parent=91 ✓
- `92` (operand_read) → `93` (execute)；child.parent=92 ✓
- `93` (execute) → `94` (prf_writeback)；child.parent=93 ✓
- `94` (prf_writeback) → `95` (commit)；child.parent=94 ✓
- `95` (commit) → `147` (chain_end)；child.parent=95 ✓

- L5 真实见证：`95` kind=commit outcome=errant_commit oracle_diff=—

### fault 17

主链每一条边均验证为直接 parent：

- `96` (fault_applied) → `97` (carrier_state)；child.parent=96 ✓
- `97` (carrier_state) → `98` (operand_read)；child.parent=97 ✓
- `98` (operand_read) → `99` (execute)；child.parent=98 ✓
- `99` (execute) → `100` (prf_writeback)；child.parent=99 ✓
- `100` (prf_writeback) → `101` (commit)；child.parent=100 ✓
- `101` (commit) → `148` (chain_end)；child.parent=101 ✓

- L5 真实见证：`101` kind=commit outcome=errant_commit oracle_diff=—

### fault 18

主链每一条边均验证为直接 parent：

- `102` (fault_applied) → `103` (carrier_state)；child.parent=102 ✓
- `103` (carrier_state) → `104` (operand_read)；child.parent=103 ✓
- `104` (operand_read) → `105` (execute)；child.parent=104 ✓
- `105` (execute) → `106` (prf_writeback)；child.parent=105 ✓
- `106` (prf_writeback) → `107` (commit)；child.parent=106 ✓
- `107` (commit) → `149` (chain_end)；child.parent=107 ✓

- L5 真实见证：`107` kind=commit outcome=errant_commit oracle_diff=—

### fault 19

主链每一条边均验证为直接 parent：

- `108` (fault_applied) → `109` (carrier_state)；child.parent=108 ✓
- `109` (carrier_state) → `110` (operand_read)；child.parent=109 ✓
- `110` (operand_read) → `111` (execute)；child.parent=110 ✓
- `111` (execute) → `112` (prf_writeback)；child.parent=111 ✓
- `112` (prf_writeback) → `113` (commit)；child.parent=112 ✓
- `113` (commit) → `150` (chain_end)；child.parent=113 ✓

- L5 真实见证：`113` kind=commit outcome=errant_commit oracle_diff=—

### fault 2

主链每一条边均验证为直接 parent：

- `6` (fault_applied) → `7` (carrier_state)；child.parent=6 ✓
- `7` (carrier_state) → `8` (operand_read)；child.parent=7 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `133` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

### fault 20

主链每一条边均验证为直接 parent：

- `114` (fault_applied) → `115` (carrier_state)；child.parent=114 ✓
- `115` (carrier_state) → `116` (operand_read)；child.parent=115 ✓
- `116` (operand_read) → `117` (execute)；child.parent=116 ✓
- `117` (execute) → `118` (prf_writeback)；child.parent=117 ✓
- `118` (prf_writeback) → `119` (commit)；child.parent=118 ✓
- `119` (commit) → `151` (chain_end)；child.parent=119 ✓

- L5 真实见证：`119` kind=commit outcome=errant_commit oracle_diff=—

### fault 21

主链每一条边均验证为直接 parent：

- `120` (fault_applied) → `121` (carrier_state)；child.parent=120 ✓
- `121` (carrier_state) → `122` (operand_read)；child.parent=121 ✓
- `122` (operand_read) → `123` (execute)；child.parent=122 ✓
- `123` (execute) → `124` (prf_writeback)；child.parent=123 ✓
- `124` (prf_writeback) → `125` (commit)；child.parent=124 ✓
- `125` (commit) → `152` (chain_end)；child.parent=125 ✓

- L5 真实见证：`125` kind=commit outcome=errant_commit oracle_diff=—

### fault 22

主链每一条边均验证为直接 parent：

- `126` (fault_applied) → `127` (carrier_state)；child.parent=126 ✓
- `127` (carrier_state) → `128` (operand_read)；child.parent=127 ✓
- `128` (operand_read) → `129` (execute)；child.parent=128 ✓
- `129` (execute) → `130` (prf_writeback)；child.parent=129 ✓
- `130` (prf_writeback) → `131` (commit)；child.parent=130 ✓
- `131` (commit) → `153` (chain_end)；child.parent=131 ✓

- L5 真实见证：`131` kind=commit outcome=errant_commit oracle_diff=—

### fault 3

主链每一条边均验证为直接 parent：

- `12` (fault_applied) → `13` (carrier_state)；child.parent=12 ✓
- `13` (carrier_state) → `14` (operand_read)；child.parent=13 ✓
- `14` (operand_read) → `15` (execute)；child.parent=14 ✓
- `15` (execute) → `16` (prf_writeback)；child.parent=15 ✓
- `16` (prf_writeback) → `17` (commit)；child.parent=16 ✓
- `17` (commit) → `134` (chain_end)；child.parent=17 ✓

- L5 真实见证：`17` kind=commit outcome=errant_commit oracle_diff=—

### fault 4

主链每一条边均验证为直接 parent：

- `18` (fault_applied) → `19` (carrier_state)；child.parent=18 ✓
- `19` (carrier_state) → `20` (operand_read)；child.parent=19 ✓
- `20` (operand_read) → `21` (execute)；child.parent=20 ✓
- `21` (execute) → `22` (prf_writeback)；child.parent=21 ✓
- `22` (prf_writeback) → `23` (commit)；child.parent=22 ✓
- `23` (commit) → `135` (chain_end)；child.parent=23 ✓

- L5 真实见证：`23` kind=commit outcome=errant_commit oracle_diff=—

### fault 5

主链每一条边均验证为直接 parent：

- `24` (fault_applied) → `25` (carrier_state)；child.parent=24 ✓
- `25` (carrier_state) → `26` (operand_read)；child.parent=25 ✓
- `26` (operand_read) → `27` (execute)；child.parent=26 ✓
- `27` (execute) → `28` (prf_writeback)；child.parent=27 ✓
- `28` (prf_writeback) → `29` (commit)；child.parent=28 ✓
- `29` (commit) → `136` (chain_end)；child.parent=29 ✓

- L5 真实见证：`29` kind=commit outcome=errant_commit oracle_diff=—

### fault 6

主链每一条边均验证为直接 parent：

- `30` (fault_applied) → `31` (carrier_state)；child.parent=30 ✓
- `31` (carrier_state) → `32` (operand_read)；child.parent=31 ✓
- `32` (operand_read) → `33` (execute)；child.parent=32 ✓
- `33` (execute) → `34` (prf_writeback)；child.parent=33 ✓
- `34` (prf_writeback) → `35` (commit)；child.parent=34 ✓
- `35` (commit) → `137` (chain_end)；child.parent=35 ✓

- L5 真实见证：`35` kind=commit outcome=errant_commit oracle_diff=—

### fault 7

主链每一条边均验证为直接 parent：

- `36` (fault_applied) → `37` (carrier_state)；child.parent=36 ✓
- `37` (carrier_state) → `38` (operand_read)；child.parent=37 ✓
- `38` (operand_read) → `39` (execute)；child.parent=38 ✓
- `39` (execute) → `40` (prf_writeback)；child.parent=39 ✓
- `40` (prf_writeback) → `41` (commit)；child.parent=40 ✓
- `41` (commit) → `138` (chain_end)；child.parent=41 ✓

- L5 真实见证：`41` kind=commit outcome=errant_commit oracle_diff=—

### fault 8

主链每一条边均验证为直接 parent：

- `42` (fault_applied) → `43` (carrier_state)；child.parent=42 ✓
- `43` (carrier_state) → `44` (operand_read)；child.parent=43 ✓
- `44` (operand_read) → `45` (execute)；child.parent=44 ✓
- `45` (execute) → `46` (prf_writeback)；child.parent=45 ✓
- `46` (prf_writeback) → `47` (commit)；child.parent=46 ✓
- `47` (commit) → `139` (chain_end)；child.parent=47 ✓

- L5 真实见证：`47` kind=commit outcome=errant_commit oracle_diff=—

### fault 9

主链每一条边均验证为直接 parent：

- `48` (fault_applied) → `49` (carrier_state)；child.parent=48 ✓
- `49` (carrier_state) → `50` (operand_read)；child.parent=49 ✓
- `50` (operand_read) → `51` (execute)；child.parent=50 ✓
- `51` (execute) → `52` (prf_writeback)；child.parent=51 ✓
- `52` (prf_writeback) → `53` (commit)；child.parent=52 ✓
- `53` (commit) → `140` (chain_end)；child.parent=53 ✓

- L5 真实见证：`53` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `01d6845c929f6f643aa52c3b417e0cdf4ae78037b3830edf5ee50a266637537f` |
| `run.out` | `b2b5820e9d25850ef99f43bc5e61afb7ff8b9f53455264c7275f222ff29dd0a3` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `b3ef7c1a27a8d130e5f1af2526881916ebb8407624a5f271c48cf884424e3457` |
| `oracle.json` | `4528a9f60c1e33ab5bba1f38e2ee946ca33458e25641dac2c15daaaac514a670` |
| `chain_report.json` | `5ea2b2b34bae0cbfa56fc90f99a343762f4272afd6e98fe938432e1c0ac31412` |
| `ordinals.json` | `783007882a6f784e997d4a738226baf681326427b0312d2192e8286b0ea6c01c` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `bbf06c3353eabef5eca462f58f89682c852bc24ba8ee36218b3002e3d69a7ad1` |
| `inject/prop_evt.txt.gz` | `f735970ed7725e1ee44f7bd4763f9b14277fbc433bbf7e6cb786b7f2d09e8b5c` |
| `inject/stats.txt` | `b3ef7c1a27a8d130e5f1af2526881916ebb8407624a5f271c48cf884424e3457` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 22 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
