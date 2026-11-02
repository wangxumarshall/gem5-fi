# FSU-FP04-F2-W4 seed3 完整传播链

> 本文只使用本 seed（sample_run_id=`s3`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F2-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F2 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 3 / `s3` |
| selection seed / injection seed | 3 / 3 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F2-W4/seed3/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `dd5089867a48fe6b492f7205803a5e935fd9c573` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F2-W4/seed3/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 3 --fsu_model FP04 --fsu_freq F2 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F2-W4/seed3/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 19 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 19 --fpu_fault_mask 0 --fpu_rng_seed 3 --fsu_model FP04 --fsu_freq F2 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 115872,260767,349889,452442,519162,613677,732681,846473,993341,1069381,1172812,1315819,1406882,1548679,1622438,1748744,1813964,1942027,2028008 --fpu_rate_warmup 0 --fsu_rate_divisor 100000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F2-W4 --prop_sample_run_id s3 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 100000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:115872, 1:260767, 2:349889, 3:452442, 4:519162, 5:613677, 6:732681, 7:846473, 8:993341, 9:1069381, 10:1172812, 11:1315819, 12:1406882, 13:1548679, 14:1622438, 15:1748744, 16:1813964, 17:1942027, 18:2028008 |
| ordinals SHA-256 | `097afed3c24e7d8d23913ed61faa968d3628fa76b6c4bedb41a3f774456629f3` |
| 注入数（actual/expected） | 19 / 19 |
| fault 数（事件流/injection log） | 19 / 19 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 188808235 / 490411 |
| sn / PC / opcode | 708121 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 115872 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 115872 / 0 |
| terminal | full |

### fault 10

| 字段 | 值 |
|---|---|
| 根 event_id | `54` |
| tick / cycle | 1638987735 / 4257111 |
| sn / PC / opcode | 6429170 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1069381 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 76040 / 9 |
| terminal | full |

### fault 11

| 字段 | 值 |
|---|---|
| 根 event_id | `60` |
| tick / cycle | 1796254460 / 4665596 |
| sn / PC / opcode | 7049772 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1172812 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 103431 / 10 |
| terminal | full |

### fault 12

| 字段 | 值 |
|---|---|
| 根 event_id | `66` |
| tick / cycle | 2013727100 / 5230460 |
| sn / PC / opcode | 7907798 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1315819 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 143007 / 11 |
| terminal | full |

### fault 13

| 字段 | 值 |
|---|---|
| 根 event_id | `72` |
| tick / cycle | 2152157700 / 5590020 |
| sn / PC / opcode | 8454172 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1406882 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 91063 / 12 |
| terminal | full |

### fault 14

| 字段 | 值 |
|---|---|
| 根 event_id | `78` |
| tick / cycle | 2367938650 / 6150490 |
| sn / PC / opcode | 9304958 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1548679 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 141797 / 13 |
| terminal | full |

### fault 15

| 字段 | 值 |
|---|---|
| 根 event_id | `84` |
| tick / cycle | 2714143740 / 7049724 |
| sn / PC / opcode | 9847963 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1622438 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 73759 / 14 |
| terminal | full |

### fault 16

| 字段 | 值 |
|---|---|
| 根 event_id | `90` |
| tick / cycle | 3437283465 / 8928009 |
| sn / PC / opcode | 10859143 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1748744 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 126306 / 15 |
| terminal | full |

### fault 17

| 字段 | 值 |
|---|---|
| 根 event_id | `96` |
| tick / cycle | 3808550130 / 9892338 |
| sn / PC / opcode | 11381295 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1813964 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 65220 / 16 |
| terminal | full |

### fault 18

| 字段 | 值 |
|---|---|
| 根 event_id | `102` |
| tick / cycle | 4539543085 / 11791021 |
| sn / PC / opcode | 12406583 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1942027 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 128063 / 17 |
| terminal | full |

### fault 19

| 字段 | 值 |
|---|---|
| 根 event_id | `108` |
| tick / cycle | 5022375435 / 13045131 |
| sn / PC / opcode | 13094921 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 2028008 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 85981 / 18 |
| terminal | full |

### fault 2

| 字段 | 值 |
|---|---|
| 根 event_id | `6` |
| tick / cycle | 409259235 / 1063011 |
| sn / PC / opcode | 1577486 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 260767 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 144895 / 1 |
| terminal | full |

### fault 3

| 字段 | 值 |
|---|---|
| 根 event_id | `12` |
| tick / cycle | 544711475 / 1414835 |
| sn / PC / opcode | 2112227 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 349889 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 89122 / 2 |
| terminal | full |

### fault 4

| 字段 | 值 |
|---|---|
| 根 event_id | `18` |
| tick / cycle | 700807030 / 1820278 |
| sn / PC / opcode | 2727541 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 452442 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 102553 / 3 |
| terminal | full |

### fault 5

| 字段 | 值 |
|---|---|
| 根 event_id | `24` |
| tick / cycle | 802165980 / 2083548 |
| sn / PC / opcode | 3127861 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 519162 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 66720 / 4 |
| terminal | full |

### fault 6

| 字段 | 值 |
|---|---|
| 根 event_id | `30` |
| tick / cycle | 945965020 / 2457052 |
| sn / PC / opcode | 3694935 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 613677 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 94515 / 5 |
| terminal | full |

### fault 7

| 字段 | 值 |
|---|---|
| 根 event_id | `36` |
| tick / cycle | 1126901545 / 2927017 |
| sn / PC / opcode | 4408959 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 732681 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 119004 / 6 |
| terminal | full |

### fault 8

| 字段 | 值 |
|---|---|
| 根 event_id | `42` |
| tick / cycle | 1300031810 / 3376706 |
| sn / PC / opcode | 5091731 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 846473 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 113792 / 7 |
| terminal | full |

### fault 9

| 字段 | 值 |
|---|---|
| 根 event_id | `48` |
| tick / cycle | 1523301010 / 3956626 |
| sn / PC / opcode | 5972939 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 993341 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 100000 / 50 / 146868 / 8 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 3437283465, Site: dyn_inst_execute, opClass=8, sn=10859143, bitseg=mant_lo, mask=0x2000, faults_injected: 16
Tick: 3808550130, Site: dyn_inst_execute, opClass=8, sn=11381295, bitseg=mant_lo, mask=0x8, faults_injected: 17
Tick: 4539543085, Site: dyn_inst_execute, opClass=8, sn=12406583, bitseg=mant_lo, mask=0x40, faults_injected: 18
Tick: 5022375435, Site: dyn_inst_execute, opClass=8, sn=13094921, bitseg=mant_lo, mask=0x100, faults_injected: 19
CHAOS_RATE_COMPLETE=19
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407e100000000000 → 0x407e100000000010 |
| old/new hash | 0xd1ddf97efd71e52d → 0xae7aca0f1134ab7d |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407e100000000000 / 0x407e100000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 10

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea872b020c49ba → 0x3fea872b020c49b8 |
| old/new hash | 0x806af44fcd404129 → 0x08ee2d72e12025b7 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea872b020c49ba / 0x3fea872b020c49b8 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 11

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083200000000000 → 0x4083200000010000 |
| old/new hash | 0x31113b7e1113d1c8 → 0x57e7a34b260afae1 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083200000000000 / 0x4083200000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 12

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff74bc6a7ef9db2 → 0x3ff74bc6a7ef9fb2 |
| old/new hash | 0x654a97bd3a8e1db9 → 0x8bd8f605540a643b |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff74bc6a7ef9db2 / 0x3ff74bc6a7ef9fb2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 13

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd9db22d0e56042 → 0xbfd9db22d0e56842 |
| old/new hash | 0xb13e8e67abddc6f3 → 0x9b845d791bfedb1b |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd9db22d0e56042 / 0xbfd9db22d0e56842 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 14

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe1ba5e353f7cee → 0x3fe1ba5e353f74ee |
| old/new hash | 0x54da0fa178976205 → 0xfbae78153ead438d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe1ba5e353f7cee / 0x3fe1ba5e353f74ee |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 15

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe649129888f862 → 0x3fe649129888f863 |
| old/new hash | 0xe7542f4cdb29976f → 0x384f7fa1553a58f2 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe649129888f862 / 0x3fe649129888f863 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 16

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdfb3d07c84b5de → 0x3fdfb3d07c8495de |
| old/new hash | 0x6f491eeb0d8d1c09 → 0xbd85809c7d371869 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdfb3d07c84b5de / 0x3fdfb3d07c8495de |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 17

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe519a415f45e0c → 0x3fe519a415f45e04 |
| old/new hash | 0x4de7d8da4173ae65 → 0x9fbc0d80f6d2c1ad |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe519a415f45e0c / 0x3fe519a415f45e04 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 18

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3febb76f6d762521 → 0x3febb76f6d762561 |
| old/new hash | 0x590f7a28d5ca4b00 → 0x742691e10d546240 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3febb76f6d762521 / 0x3febb76f6d762561 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 19

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ffd3ad3a604e1e7 → 0x3ffd3ad3a604e0e7 |
| old/new hash | 0x50d6256ef3f95d98 → 0x98350cde1ba15207 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ffd3ad3a604e1e7 / 0x3ffd3ad3a604e0e7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 2

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff74395810624dd → 0x3ff74395810664dd |
| old/new hash | 0xa4605ee8dc39324d → 0xa7e2b924a6006e0d |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff74395810624dd / 0x3ff74395810664dd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 3

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408e000000000000 → 0x408e000000000002 |
| old/new hash | 0x499c697eb0ee26ad → 0x084e736c9837f60f |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408e000000000000 / 0x408e000000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 4

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x405e000000000000 → 0x405e000000000008 |
| old/new hash | 0x48f9497eb0638efd → 0x3ee621c7063e18f5 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x405e000000000000 / 0x405e000000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 5

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4085280000000000 → 0x4085280000000400 |
| old/new hash | 0xef3fc77decc85866 → 0x010905a7311e3b0a |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4085280000000000 / 0x4085280000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 6

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe4ed916872b021 → 0x3fe4ed916872a021 |
| old/new hash | 0xfbd8f55056a2b477 → 0xf27671277e476f27 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe4ed916872b021 / 0x3fe4ed916872a021 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 7

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe147ae147ae148 → 0x3fe147ae147ae108 |
| old/new hash | 0x522773bc17cddcf9 → 0x9707677f936241b9 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe147ae147ae148 / 0x3fe147ae147ae108 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 8

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4077c00000000000 → 0x4077c00000000800 |
| old/new hash | 0x1c93137d74aafa3c → 0x9be6f72fce677384 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4077c00000000000 / 0x4077c00000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 9

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408a500000000000 → 0x408a500000000080 |
| old/new hash | 0xfe85418039622f79 → 0x7dbbbcfabed9f5f9 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408a500000000000 / 0x408a500000000080 |
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
| 7 | chain_end | — | 114 | 5 |

### fault 10（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 54 | — |
| 2 | carrier_state | L1 | 55 | 54 |
| 3 | operand_read | L2 | 56 | 55 |
| 4 | execute | L3 | 57 | 56 |
| 5 | prf_writeback | L4 | 58 | 57 |
| 6 | commit | L5 | 59 | 58 |
| 7 | chain_end | — | 123 | 59 |

### fault 11（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 60 | — |
| 2 | carrier_state | L1 | 61 | 60 |
| 3 | operand_read | L2 | 62 | 61 |
| 4 | execute | L3 | 63 | 62 |
| 5 | prf_writeback | L4 | 64 | 63 |
| 6 | commit | L5 | 65 | 64 |
| 7 | chain_end | — | 124 | 65 |

### fault 12（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 66 | — |
| 2 | carrier_state | L1 | 67 | 66 |
| 3 | operand_read | L2 | 68 | 67 |
| 4 | execute | L3 | 69 | 68 |
| 5 | prf_writeback | L4 | 70 | 69 |
| 6 | commit | L5 | 71 | 70 |
| 7 | chain_end | — | 125 | 71 |

### fault 13（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 72 | — |
| 2 | carrier_state | L1 | 73 | 72 |
| 3 | operand_read | L2 | 74 | 73 |
| 4 | execute | L3 | 75 | 74 |
| 5 | prf_writeback | L4 | 76 | 75 |
| 6 | commit | L5 | 77 | 76 |
| 7 | chain_end | — | 126 | 77 |

### fault 14（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 78 | — |
| 2 | carrier_state | L1 | 79 | 78 |
| 3 | operand_read | L2 | 80 | 79 |
| 4 | execute | L3 | 81 | 80 |
| 5 | prf_writeback | L4 | 82 | 81 |
| 6 | commit | L5 | 83 | 82 |
| 7 | chain_end | — | 127 | 83 |

### fault 15（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 84 | — |
| 2 | carrier_state | L1 | 85 | 84 |
| 3 | operand_read | L2 | 86 | 85 |
| 4 | execute | L3 | 87 | 86 |
| 5 | prf_writeback | L4 | 88 | 87 |
| 6 | commit | L5 | 89 | 88 |
| 7 | chain_end | — | 128 | 89 |

### fault 16（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 90 | — |
| 2 | carrier_state | L1 | 91 | 90 |
| 3 | operand_read | L2 | 92 | 91 |
| 4 | execute | L3 | 93 | 92 |
| 5 | prf_writeback | L4 | 94 | 93 |
| 6 | commit | L5 | 95 | 94 |
| 7 | chain_end | — | 129 | 95 |

### fault 17（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 96 | — |
| 2 | carrier_state | L1 | 97 | 96 |
| 3 | operand_read | L2 | 98 | 97 |
| 4 | execute | L3 | 99 | 98 |
| 5 | prf_writeback | L4 | 100 | 99 |
| 6 | commit | L5 | 101 | 100 |
| 7 | chain_end | — | 130 | 101 |

### fault 18（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 102 | — |
| 2 | carrier_state | L1 | 103 | 102 |
| 3 | operand_read | L2 | 104 | 103 |
| 4 | execute | L3 | 105 | 104 |
| 5 | prf_writeback | L4 | 106 | 105 |
| 6 | commit | L5 | 107 | 106 |
| 7 | chain_end | — | 131 | 107 |

### fault 19（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 108 | — |
| 2 | carrier_state | L1 | 109 | 108 |
| 3 | operand_read | L2 | 110 | 109 |
| 4 | execute | L3 | 111 | 110 |
| 5 | prf_writeback | L4 | 112 | 111 |
| 6 | commit | L5 | 113 | 112 |
| 7 | chain_end | — | 132 | 113 |

### fault 2（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 6 | — |
| 2 | carrier_state | L1 | 7 | 6 |
| 3 | operand_read | L2 | 8 | 7 |
| 4 | execute | L3 | 9 | 8 |
| 5 | prf_writeback | L4 | 10 | 9 |
| 6 | commit | L5 | 11 | 10 |
| 7 | chain_end | — | 115 | 11 |

### fault 3（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 12 | — |
| 2 | carrier_state | L1 | 13 | 12 |
| 3 | operand_read | L2 | 14 | 13 |
| 4 | execute | L3 | 15 | 14 |
| 5 | prf_writeback | L4 | 16 | 15 |
| 6 | commit | L5 | 17 | 16 |
| 7 | chain_end | — | 116 | 17 |

### fault 4（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 18 | — |
| 2 | carrier_state | L1 | 19 | 18 |
| 3 | operand_read | L2 | 20 | 19 |
| 4 | execute | L3 | 21 | 20 |
| 5 | prf_writeback | L4 | 22 | 21 |
| 6 | commit | L5 | 23 | 22 |
| 7 | chain_end | — | 117 | 23 |

### fault 5（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 24 | — |
| 2 | carrier_state | L1 | 25 | 24 |
| 3 | operand_read | L2 | 26 | 25 |
| 4 | execute | L3 | 27 | 26 |
| 5 | prf_writeback | L4 | 28 | 27 |
| 6 | commit | L5 | 29 | 28 |
| 7 | chain_end | — | 118 | 29 |

### fault 6（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 30 | — |
| 2 | carrier_state | L1 | 31 | 30 |
| 3 | operand_read | L2 | 32 | 31 |
| 4 | execute | L3 | 33 | 32 |
| 5 | prf_writeback | L4 | 34 | 33 |
| 6 | commit | L5 | 35 | 34 |
| 7 | chain_end | — | 119 | 35 |

### fault 7（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 36 | — |
| 2 | carrier_state | L1 | 37 | 36 |
| 3 | operand_read | L2 | 38 | 37 |
| 4 | execute | L3 | 39 | 38 |
| 5 | prf_writeback | L4 | 40 | 39 |
| 6 | commit | L5 | 41 | 40 |
| 7 | chain_end | — | 120 | 41 |

### fault 8（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 42 | — |
| 2 | carrier_state | L1 | 43 | 42 |
| 3 | operand_read | L2 | 44 | 43 |
| 4 | execute | L3 | 45 | 44 |
| 5 | prf_writeback | L4 | 46 | 45 |
| 6 | commit | L5 | 47 | 46 |
| 7 | chain_end | — | 121 | 47 |

### fault 9（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 48 | — |
| 2 | carrier_state | L1 | 49 | 48 |
| 3 | operand_read | L2 | 50 | 49 |
| 4 | execute | L3 | 51 | 50 |
| 5 | prf_writeback | L4 | 52 | 51 |
| 6 | commit | L5 | 53 | 52 |
| 7 | chain_end | — | 122 | 53 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 188808235 | 1 | 708121 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x407e100000000000→0x407e100000000010 | — | — | origin |
| carrier_state | 1 | 0 | 188808235 | 1 | 708121 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x407e100000000000→0x407e100000000010 | — | — | fsu_taint |
| operand_read | 2 | 1 | 188812085 | 1 | 708124 | 0x000000000040065c | fmadd | 708121/708124 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 188812085 | 1 | 708124 | 0x000000000040065c | fmadd | 708121/708124 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 188812085 | 1 | 708124 | 0x000000000040065c | fmadd | 708121/708124 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 188812855 | 1 | 708124 | 0x000000000040065c | fmadd | —/708124 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 114 | 5 | 9406531365 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 54 | — | 1638987735 | 10 | 6429170 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fea872b020c49ba→0x3fea872b020c49b8 | — | — | origin |
| carrier_state | 55 | 54 | 1638987735 | 10 | 6429170 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fea872b020c49ba→0x3fea872b020c49b8 | — | — | fsu_taint |
| operand_read | 56 | 55 | 1639023155 | 10 | 6429314 | 0x0000000000400654 | fmadd | 6429170/6429314 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 57 | 56 | 1639023155 | 10 | 6429314 | 0x0000000000400654 | fmadd | 6429170/6429314 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 58 | 57 | 1639023155 | 10 | 6429314 | 0x0000000000400654 | fmadd | 6429170/6429314 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 59 | 58 | 1639023925 | 10 | 6429314 | 0x0000000000400654 | fmadd | —/6429314 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 123 | 59 | 9406531365 | 10 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 60 | — | 1796254460 | 11 | 7049772 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4083200000000000→0x4083200000010000 | — | — | origin |
| carrier_state | 61 | 60 | 1796254460 | 11 | 7049772 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4083200000000000→0x4083200000010000 | — | — | fsu_taint |
| operand_read | 62 | 61 | 1796258695 | 11 | 7049775 | 0x0000000000400658 | fmadd | 7049772/7049775 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 63 | 62 | 1796258695 | 11 | 7049775 | 0x0000000000400658 | fmadd | 7049772/7049775 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 64 | 63 | 1796258695 | 11 | 7049775 | 0x0000000000400658 | fmadd | 7049772/7049775 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 65 | 64 | 1796259465 | 11 | 7049775 | 0x0000000000400658 | fmadd | —/7049775 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 124 | 65 | 9406531365 | 11 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 66 | — | 2013727100 | 12 | 7907798 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff74bc6a7ef9db2→0x3ff74bc6a7ef9fb2 | — | — | origin |
| carrier_state | 67 | 66 | 2013727100 | 12 | 7907798 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff74bc6a7ef9db2→0x3ff74bc6a7ef9fb2 | — | — | fsu_taint |
| operand_read | 68 | 67 | 2013762520 | 12 | 7907942 | 0x0000000000400654 | fmadd | 7907798/7907942 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 69 | 68 | 2013762520 | 12 | 7907942 | 0x0000000000400654 | fmadd | 7907798/7907942 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 70 | 69 | 2013762520 | 12 | 7907942 | 0x0000000000400654 | fmadd | 7907798/7907942 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 71 | 70 | 2013763290 | 12 | 7907942 | 0x0000000000400654 | fmadd | —/7907942 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 125 | 71 | 9406531365 | 12 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 72 | — | 2152157700 | 13 | 8454172 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfd9db22d0e56042→0xbfd9db22d0e56842 | — | — | origin |
| carrier_state | 73 | 72 | 2152157700 | 13 | 8454172 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfd9db22d0e56042→0xbfd9db22d0e56842 | — | — | fsu_taint |
| operand_read | 74 | 73 | 2152173100 | 13 | 8454242 | 0x0000000000400654 | fmadd | 8454172/8454242 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 75 | 74 | 2152173100 | 13 | 8454242 | 0x0000000000400654 | fmadd | 8454172/8454242 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 76 | 75 | 2152173100 | 13 | 8454242 | 0x0000000000400654 | fmadd | 8454172/8454242 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 77 | 76 | 2152173870 | 13 | 8454242 | 0x0000000000400654 | fmadd | —/8454242 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 126 | 77 | 9406531365 | 13 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 78 | — | 2367938650 | 14 | 9304958 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fe1ba5e353f7cee→0x3fe1ba5e353f74ee | — | — | origin |
| carrier_state | 79 | 78 | 2367938650 | 14 | 9304958 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fe1ba5e353f7cee→0x3fe1ba5e353f74ee | — | — | fsu_taint |
| operand_read | 80 | 79 | 2367974070 | 14 | 9305102 | 0x0000000000400654 | fmadd | 9304958/9305102 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 81 | 80 | 2367974070 | 14 | 9305102 | 0x0000000000400654 | fmadd | 9304958/9305102 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 82 | 81 | 2367974070 | 14 | 9305102 | 0x0000000000400654 | fmadd | 9304958/9305102 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 83 | 82 | 2367974840 | 14 | 9305102 | 0x0000000000400654 | fmadd | —/9305102 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 127 | 83 | 9406531365 | 14 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 84 | — | 2714143740 | 15 | 9847963 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe649129888f862→0x3fe649129888f863 | — | — | origin |
| carrier_state | 85 | 84 | 2714143740 | 15 | 9847963 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe649129888f862→0x3fe649129888f863 | — | — | fsu_taint |
| operand_read | 86 | 85 | 2714152210 | 15 | 9847979 | 0x00000000004006a4 | fmadd | 9847963/9847979 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 87 | 86 | 2714152210 | 15 | 9847979 | 0x00000000004006a4 | fmadd | 9847963/9847979 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 88 | 87 | 2714152210 | 15 | 9847979 | 0x00000000004006a4 | fmadd | 9847963/9847979 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 89 | 88 | 2714152980 | 15 | 9847979 | 0x00000000004006a4 | fmadd | —/9847979 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 128 | 89 | 9406531365 | 15 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 90 | — | 3437283465 | 16 | 10859143 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fdfb3d07c84b5de→0x3fdfb3d07c8495de | — | — | origin |
| carrier_state | 91 | 90 | 3437283465 | 16 | 10859143 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fdfb3d07c84b5de→0x3fdfb3d07c8495de | — | — | fsu_taint |
| operand_read | 92 | 91 | 3437291935 | 16 | 10859159 | 0x00000000004006cc | fmadd | 10859143/10859159 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 93 | 92 | 3437291935 | 16 | 10859159 | 0x00000000004006cc | fmadd | 10859143/10859159 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 94 | 93 | 3437291935 | 16 | 10859159 | 0x00000000004006cc | fmadd | 10859143/10859159 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 95 | 94 | 3437292705 | 16 | 10859159 | 0x00000000004006cc | fmadd | —/10859159 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 129 | 95 | 9406531365 | 16 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 96 | — | 3808550130 | 17 | 11381295 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe519a415f45e0c→0x3fe519a415f45e04 | — | — | origin |
| carrier_state | 97 | 96 | 3808550130 | 17 | 11381295 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe519a415f45e0c→0x3fe519a415f45e04 | — | — | fsu_taint |
| operand_read | 98 | 97 | 3808558600 | 17 | 11381311 | 0x00000000004006cc | fmadd | 11381295/11381311 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 99 | 98 | 3808558600 | 17 | 11381311 | 0x00000000004006cc | fmadd | 11381295/11381311 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 100 | 99 | 3808558600 | 17 | 11381311 | 0x00000000004006cc | fmadd | 11381295/11381311 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 101 | 100 | 3808559370 | 17 | 11381311 | 0x00000000004006cc | fmadd | —/11381311 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 130 | 101 | 9406531365 | 17 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 102 | — | 4539543085 | 18 | 12406583 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3febb76f6d762521→0x3febb76f6d762561 | — | — | origin |
| carrier_state | 103 | 102 | 4539543085 | 18 | 12406583 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3febb76f6d762521→0x3febb76f6d762561 | — | — | fsu_taint |
| operand_read | 104 | 103 | 4539551555 | 18 | 12406599 | 0x00000000004006cc | fmadd | 12406583/12406599 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 105 | 104 | 4539551555 | 18 | 12406599 | 0x00000000004006cc | fmadd | 12406583/12406599 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 106 | 105 | 4539551555 | 18 | 12406599 | 0x00000000004006cc | fmadd | 12406583/12406599 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 107 | 106 | 4539552325 | 18 | 12406599 | 0x00000000004006cc | fmadd | —/12406599 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 131 | 107 | 9406531365 | 18 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 108 | — | 5022375435 | 19 | 13094921 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ffd3ad3a604e1e7→0x3ffd3ad3a604e0e7 | — | — | origin |
| carrier_state | 109 | 108 | 5022375435 | 19 | 13094921 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ffd3ad3a604e1e7→0x3ffd3ad3a604e0e7 | — | — | fsu_taint |
| operand_read | 110 | 109 | 5022383905 | 19 | 13094937 | 0x00000000004006cc | fmadd | 13094921/13094937 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 111 | 110 | 5022383905 | 19 | 13094937 | 0x00000000004006cc | fmadd | 13094921/13094937 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 112 | 111 | 5022383905 | 19 | 13094937 | 0x00000000004006cc | fmadd | 13094921/13094937 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 113 | 112 | 5022384675 | 19 | 13094937 | 0x00000000004006cc | fmadd | —/13094937 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 132 | 113 | 9406531365 | 19 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 6 | — | 409259235 | 2 | 1577486 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff74395810624dd→0x3ff74395810664dd | — | — | origin |
| carrier_state | 7 | 6 | 409259235 | 2 | 1577486 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff74395810624dd→0x3ff74395810664dd | — | — | fsu_taint |
| operand_read | 8 | 7 | 409294655 | 2 | 1577630 | 0x0000000000400654 | fmadd | 1577486/1577630 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 409294655 | 2 | 1577630 | 0x0000000000400654 | fmadd | 1577486/1577630 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 409294655 | 2 | 1577630 | 0x0000000000400654 | fmadd | 1577486/1577630 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 409295425 | 2 | 1577630 | 0x0000000000400654 | fmadd | —/1577630 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 115 | 11 | 9406531365 | 2 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 12 | — | 544711475 | 3 | 2112227 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x408e000000000000→0x408e000000000002 | — | — | origin |
| carrier_state | 13 | 12 | 544711475 | 3 | 2112227 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x408e000000000000→0x408e000000000002 | — | — | fsu_taint |
| operand_read | 14 | 13 | 544713400 | 3 | 2112230 | 0x0000000000400654 | fmadd | 2112227/2112230 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 15 | 14 | 544713400 | 3 | 2112230 | 0x0000000000400654 | fmadd | 2112227/2112230 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 16 | 15 | 544713400 | 3 | 2112230 | 0x0000000000400654 | fmadd | 2112227/2112230 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 17 | 16 | 544714170 | 3 | 2112230 | 0x0000000000400654 | fmadd | —/2112230 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 116 | 17 | 9406531365 | 3 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 18 | — | 700807030 | 4 | 2727541 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x405e000000000000→0x405e000000000008 | — | — | origin |
| carrier_state | 19 | 18 | 700807030 | 4 | 2727541 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x405e000000000000→0x405e000000000008 | — | — | fsu_taint |
| operand_read | 20 | 19 | 700810880 | 4 | 2727544 | 0x000000000040065c | fmadd | 2727541/2727544 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 21 | 20 | 700810880 | 4 | 2727544 | 0x000000000040065c | fmadd | 2727541/2727544 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 22 | 21 | 700810880 | 4 | 2727544 | 0x000000000040065c | fmadd | 2727541/2727544 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 23 | 22 | 700811650 | 4 | 2727544 | 0x000000000040065c | fmadd | —/2727544 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 117 | 23 | 9406531365 | 4 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 24 | — | 802165980 | 5 | 3127861 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4085280000000000→0x4085280000000400 | — | — | origin |
| carrier_state | 25 | 24 | 802165980 | 5 | 3127861 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4085280000000000→0x4085280000000400 | — | — | fsu_taint |
| operand_read | 26 | 25 | 802169830 | 5 | 3127864 | 0x000000000040065c | fmadd | 3127861/3127864 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 27 | 26 | 802169830 | 5 | 3127864 | 0x000000000040065c | fmadd | 3127861/3127864 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 28 | 27 | 802169830 | 5 | 3127864 | 0x000000000040065c | fmadd | 3127861/3127864 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 29 | 28 | 802170600 | 5 | 3127864 | 0x000000000040065c | fmadd | —/3127864 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 118 | 29 | 9406531365 | 5 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 30 | — | 945965020 | 6 | 3694935 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fe4ed916872b021→0x3fe4ed916872a021 | — | — | origin |
| carrier_state | 31 | 30 | 945965020 | 6 | 3694935 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fe4ed916872b021→0x3fe4ed916872a021 | — | — | fsu_taint |
| operand_read | 32 | 31 | 945989275 | 6 | 3695042 | 0x0000000000400654 | fmadd | 3694935/3695042 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 33 | 32 | 945989275 | 6 | 3695042 | 0x0000000000400654 | fmadd | 3694935/3695042 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 34 | 33 | 945989275 | 6 | 3695042 | 0x0000000000400654 | fmadd | 3694935/3695042 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 35 | 34 | 945990045 | 6 | 3695042 | 0x0000000000400654 | fmadd | —/3695042 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 119 | 35 | 9406531365 | 6 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 36 | — | 1126901545 | 7 | 4408959 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe147ae147ae148→0x3fe147ae147ae108 | — | — | origin |
| carrier_state | 37 | 36 | 1126901545 | 7 | 4408959 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe147ae147ae148→0x3fe147ae147ae108 | — | — | fsu_taint |
| operand_read | 38 | 37 | 1126925800 | 7 | 4409066 | 0x0000000000400654 | fmadd | 4408959/4409066 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 39 | 38 | 1126925800 | 7 | 4409066 | 0x0000000000400654 | fmadd | 4408959/4409066 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 40 | 39 | 1126925800 | 7 | 4409066 | 0x0000000000400654 | fmadd | 4408959/4409066 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 41 | 40 | 1126926570 | 7 | 4409066 | 0x0000000000400654 | fmadd | —/4409066 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 120 | 41 | 9406531365 | 7 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 42 | — | 1300031810 | 8 | 5091731 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x4077c00000000000→0x4077c00000000800 | — | — | origin |
| carrier_state | 43 | 42 | 1300031810 | 8 | 5091731 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x4077c00000000000→0x4077c00000000800 | — | — | fsu_taint |
| operand_read | 44 | 43 | 1300033735 | 8 | 5091734 | 0x0000000000400654 | fmadd | 5091731/5091734 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 45 | 44 | 1300033735 | 8 | 5091734 | 0x0000000000400654 | fmadd | 5091731/5091734 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 46 | 45 | 1300033735 | 8 | 5091734 | 0x0000000000400654 | fmadd | 5091731/5091734 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 47 | 46 | 1300034505 | 8 | 5091734 | 0x0000000000400654 | fmadd | —/5091734 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 121 | 47 | 9406531365 | 8 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 48 | — | 1523301010 | 9 | 5972939 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x408a500000000000→0x408a500000000080 | — | — | origin |
| carrier_state | 49 | 48 | 1523301010 | 9 | 5972939 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x408a500000000000→0x408a500000000080 | — | — | fsu_taint |
| operand_read | 50 | 49 | 1523302935 | 9 | 5972942 | 0x0000000000400654 | fmadd | 5972939/5972942 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 51 | 50 | 1523302935 | 9 | 5972942 | 0x0000000000400654 | fmadd | 5972939/5972942 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 52 | 51 | 1523302935 | 9 | 5972942 | 0x0000000000400654 | fmadd | 5972939/5972942 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 53 | 52 | 1523303705 | 9 | 5972942 | 0x0000000000400654 | fmadd | —/5972942 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 122 | 53 | 9406531365 | 9 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

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

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 32e9009b60144ac020a167b4b80a46382ec9b5059445ff793980b7e806e65b10 != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：19 / 19
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：133
- attempted / eligible / activated：19 / 2097155 / 19

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
- `5` (commit) → `114` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

### fault 10

主链每一条边均验证为直接 parent：

- `54` (fault_applied) → `55` (carrier_state)；child.parent=54 ✓
- `55` (carrier_state) → `56` (operand_read)；child.parent=55 ✓
- `56` (operand_read) → `57` (execute)；child.parent=56 ✓
- `57` (execute) → `58` (prf_writeback)；child.parent=57 ✓
- `58` (prf_writeback) → `59` (commit)；child.parent=58 ✓
- `59` (commit) → `123` (chain_end)；child.parent=59 ✓

- L5 真实见证：`59` kind=commit outcome=errant_commit oracle_diff=—

### fault 11

主链每一条边均验证为直接 parent：

- `60` (fault_applied) → `61` (carrier_state)；child.parent=60 ✓
- `61` (carrier_state) → `62` (operand_read)；child.parent=61 ✓
- `62` (operand_read) → `63` (execute)；child.parent=62 ✓
- `63` (execute) → `64` (prf_writeback)；child.parent=63 ✓
- `64` (prf_writeback) → `65` (commit)；child.parent=64 ✓
- `65` (commit) → `124` (chain_end)；child.parent=65 ✓

- L5 真实见证：`65` kind=commit outcome=errant_commit oracle_diff=—

### fault 12

主链每一条边均验证为直接 parent：

- `66` (fault_applied) → `67` (carrier_state)；child.parent=66 ✓
- `67` (carrier_state) → `68` (operand_read)；child.parent=67 ✓
- `68` (operand_read) → `69` (execute)；child.parent=68 ✓
- `69` (execute) → `70` (prf_writeback)；child.parent=69 ✓
- `70` (prf_writeback) → `71` (commit)；child.parent=70 ✓
- `71` (commit) → `125` (chain_end)；child.parent=71 ✓

- L5 真实见证：`71` kind=commit outcome=errant_commit oracle_diff=—

### fault 13

主链每一条边均验证为直接 parent：

- `72` (fault_applied) → `73` (carrier_state)；child.parent=72 ✓
- `73` (carrier_state) → `74` (operand_read)；child.parent=73 ✓
- `74` (operand_read) → `75` (execute)；child.parent=74 ✓
- `75` (execute) → `76` (prf_writeback)；child.parent=75 ✓
- `76` (prf_writeback) → `77` (commit)；child.parent=76 ✓
- `77` (commit) → `126` (chain_end)；child.parent=77 ✓

- L5 真实见证：`77` kind=commit outcome=errant_commit oracle_diff=—

### fault 14

主链每一条边均验证为直接 parent：

- `78` (fault_applied) → `79` (carrier_state)；child.parent=78 ✓
- `79` (carrier_state) → `80` (operand_read)；child.parent=79 ✓
- `80` (operand_read) → `81` (execute)；child.parent=80 ✓
- `81` (execute) → `82` (prf_writeback)；child.parent=81 ✓
- `82` (prf_writeback) → `83` (commit)；child.parent=82 ✓
- `83` (commit) → `127` (chain_end)；child.parent=83 ✓

- L5 真实见证：`83` kind=commit outcome=errant_commit oracle_diff=—

### fault 15

主链每一条边均验证为直接 parent：

- `84` (fault_applied) → `85` (carrier_state)；child.parent=84 ✓
- `85` (carrier_state) → `86` (operand_read)；child.parent=85 ✓
- `86` (operand_read) → `87` (execute)；child.parent=86 ✓
- `87` (execute) → `88` (prf_writeback)；child.parent=87 ✓
- `88` (prf_writeback) → `89` (commit)；child.parent=88 ✓
- `89` (commit) → `128` (chain_end)；child.parent=89 ✓

- L5 真实见证：`89` kind=commit outcome=errant_commit oracle_diff=—

### fault 16

主链每一条边均验证为直接 parent：

- `90` (fault_applied) → `91` (carrier_state)；child.parent=90 ✓
- `91` (carrier_state) → `92` (operand_read)；child.parent=91 ✓
- `92` (operand_read) → `93` (execute)；child.parent=92 ✓
- `93` (execute) → `94` (prf_writeback)；child.parent=93 ✓
- `94` (prf_writeback) → `95` (commit)；child.parent=94 ✓
- `95` (commit) → `129` (chain_end)；child.parent=95 ✓

- L5 真实见证：`95` kind=commit outcome=errant_commit oracle_diff=—

### fault 17

主链每一条边均验证为直接 parent：

- `96` (fault_applied) → `97` (carrier_state)；child.parent=96 ✓
- `97` (carrier_state) → `98` (operand_read)；child.parent=97 ✓
- `98` (operand_read) → `99` (execute)；child.parent=98 ✓
- `99` (execute) → `100` (prf_writeback)；child.parent=99 ✓
- `100` (prf_writeback) → `101` (commit)；child.parent=100 ✓
- `101` (commit) → `130` (chain_end)；child.parent=101 ✓

- L5 真实见证：`101` kind=commit outcome=errant_commit oracle_diff=—

### fault 18

主链每一条边均验证为直接 parent：

- `102` (fault_applied) → `103` (carrier_state)；child.parent=102 ✓
- `103` (carrier_state) → `104` (operand_read)；child.parent=103 ✓
- `104` (operand_read) → `105` (execute)；child.parent=104 ✓
- `105` (execute) → `106` (prf_writeback)；child.parent=105 ✓
- `106` (prf_writeback) → `107` (commit)；child.parent=106 ✓
- `107` (commit) → `131` (chain_end)；child.parent=107 ✓

- L5 真实见证：`107` kind=commit outcome=errant_commit oracle_diff=—

### fault 19

主链每一条边均验证为直接 parent：

- `108` (fault_applied) → `109` (carrier_state)；child.parent=108 ✓
- `109` (carrier_state) → `110` (operand_read)；child.parent=109 ✓
- `110` (operand_read) → `111` (execute)；child.parent=110 ✓
- `111` (execute) → `112` (prf_writeback)；child.parent=111 ✓
- `112` (prf_writeback) → `113` (commit)；child.parent=112 ✓
- `113` (commit) → `132` (chain_end)；child.parent=113 ✓

- L5 真实见证：`113` kind=commit outcome=errant_commit oracle_diff=—

### fault 2

主链每一条边均验证为直接 parent：

- `6` (fault_applied) → `7` (carrier_state)；child.parent=6 ✓
- `7` (carrier_state) → `8` (operand_read)；child.parent=7 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `115` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

### fault 3

主链每一条边均验证为直接 parent：

- `12` (fault_applied) → `13` (carrier_state)；child.parent=12 ✓
- `13` (carrier_state) → `14` (operand_read)；child.parent=13 ✓
- `14` (operand_read) → `15` (execute)；child.parent=14 ✓
- `15` (execute) → `16` (prf_writeback)；child.parent=15 ✓
- `16` (prf_writeback) → `17` (commit)；child.parent=16 ✓
- `17` (commit) → `116` (chain_end)；child.parent=17 ✓

- L5 真实见证：`17` kind=commit outcome=errant_commit oracle_diff=—

### fault 4

主链每一条边均验证为直接 parent：

- `18` (fault_applied) → `19` (carrier_state)；child.parent=18 ✓
- `19` (carrier_state) → `20` (operand_read)；child.parent=19 ✓
- `20` (operand_read) → `21` (execute)；child.parent=20 ✓
- `21` (execute) → `22` (prf_writeback)；child.parent=21 ✓
- `22` (prf_writeback) → `23` (commit)；child.parent=22 ✓
- `23` (commit) → `117` (chain_end)；child.parent=23 ✓

- L5 真实见证：`23` kind=commit outcome=errant_commit oracle_diff=—

### fault 5

主链每一条边均验证为直接 parent：

- `24` (fault_applied) → `25` (carrier_state)；child.parent=24 ✓
- `25` (carrier_state) → `26` (operand_read)；child.parent=25 ✓
- `26` (operand_read) → `27` (execute)；child.parent=26 ✓
- `27` (execute) → `28` (prf_writeback)；child.parent=27 ✓
- `28` (prf_writeback) → `29` (commit)；child.parent=28 ✓
- `29` (commit) → `118` (chain_end)；child.parent=29 ✓

- L5 真实见证：`29` kind=commit outcome=errant_commit oracle_diff=—

### fault 6

主链每一条边均验证为直接 parent：

- `30` (fault_applied) → `31` (carrier_state)；child.parent=30 ✓
- `31` (carrier_state) → `32` (operand_read)；child.parent=31 ✓
- `32` (operand_read) → `33` (execute)；child.parent=32 ✓
- `33` (execute) → `34` (prf_writeback)；child.parent=33 ✓
- `34` (prf_writeback) → `35` (commit)；child.parent=34 ✓
- `35` (commit) → `119` (chain_end)；child.parent=35 ✓

- L5 真实见证：`35` kind=commit outcome=errant_commit oracle_diff=—

### fault 7

主链每一条边均验证为直接 parent：

- `36` (fault_applied) → `37` (carrier_state)；child.parent=36 ✓
- `37` (carrier_state) → `38` (operand_read)；child.parent=37 ✓
- `38` (operand_read) → `39` (execute)；child.parent=38 ✓
- `39` (execute) → `40` (prf_writeback)；child.parent=39 ✓
- `40` (prf_writeback) → `41` (commit)；child.parent=40 ✓
- `41` (commit) → `120` (chain_end)；child.parent=41 ✓

- L5 真实见证：`41` kind=commit outcome=errant_commit oracle_diff=—

### fault 8

主链每一条边均验证为直接 parent：

- `42` (fault_applied) → `43` (carrier_state)；child.parent=42 ✓
- `43` (carrier_state) → `44` (operand_read)；child.parent=43 ✓
- `44` (operand_read) → `45` (execute)；child.parent=44 ✓
- `45` (execute) → `46` (prf_writeback)；child.parent=45 ✓
- `46` (prf_writeback) → `47` (commit)；child.parent=46 ✓
- `47` (commit) → `121` (chain_end)；child.parent=47 ✓

- L5 真实见证：`47` kind=commit outcome=errant_commit oracle_diff=—

### fault 9

主链每一条边均验证为直接 parent：

- `48` (fault_applied) → `49` (carrier_state)；child.parent=48 ✓
- `49` (carrier_state) → `50` (operand_read)；child.parent=49 ✓
- `50` (operand_read) → `51` (execute)；child.parent=50 ✓
- `51` (execute) → `52` (prf_writeback)；child.parent=51 ✓
- `52` (prf_writeback) → `53` (commit)；child.parent=52 ✓
- `53` (commit) → `122` (chain_end)；child.parent=53 ✓

- L5 真实见证：`53` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `d30f58db1afc0ebd563843569542ebd25c68428ae9a33273a4e3102ff84f2a93` |
| `run.out` | `d0107a905ad26489e4f73e526e2c16c19e7d8376cb873147a1e79048056b2718` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `ec5393f3a6bc6d67db857d8a975dbe44c79d3d3e4eb0f066f27e611d992ca870` |
| `oracle.json` | `25fe582adac336903a17d6e2c120dc3feb10f096a1bf3942b8ae2d73c6e7fc98` |
| `chain_report.json` | `c5c920b5583878dd881f13e11db8ec82d91342113bf4f21bc84736c5d96df0c2` |
| `ordinals.json` | `097afed3c24e7d8d23913ed61faa968d3628fa76b6c4bedb41a3f774456629f3` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `b89f1cd605d635b92e9c2c7509e58579797a0725ce557468ce2902dd0ddd2a63` |
| `inject/prop_evt.txt.gz` | `ba06e2f5480dee1898c514bcc08fecaa92b657592460cb0fbebb094a22b4c685` |
| `inject/stats.txt` | `ec5393f3a6bc6d67db857d8a975dbe44c79d3d3e4eb0f066f27e611d992ca870` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 19 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
