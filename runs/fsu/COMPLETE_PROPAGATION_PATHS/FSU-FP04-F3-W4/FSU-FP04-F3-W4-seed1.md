# FSU-FP04-F3-W4 seed1 完整传播链

> 本文只使用本 seed（sample_run_id=`s1`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F3-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F3 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 1 / `s1` |
| selection seed / injection seed | 1 / 1 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F3-W4/seed1/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `db21e798ad154fe7983d937640943190e5d21ee8` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F3-W4/seed1/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F3-W4/seed1/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 206 --rng_seed 1 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 206 --fpu_fault_mask 0 --fpu_rng_seed 1 --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 11004,24122,34278,48713,57731,70845,82777,97584,110009,123909,136566,144683,157330,171623,184741,192437,200494,207981,218123,224714,231661,238337,244995,259697,266253,277919,284090,292155,306417,316599,324306,329893,341571,354856,362564,372300,378155,388990,396874,407572,418517,424470,438586,447847,458883,469522,480819,492463,502937,512350,525705,539239,552530,564333,574521,585576,591012,599590,609106,615934,627760,634809,645621,659095,670791,683743,690309,704892,716759,725369,731350,736460,750769,759508,773430,784776,795744,806875,814751,825035,832243,838670,845725,851409,864661,870804,878552,891296,899006,906238,917592,928708,939401,948516,956625,970100,984011,997629,1002717,1015882,1028846,1038765,1052286,1064588,1076863,1089427,1102135,1114271,1120562,1128529,1141808,1149135,1163369,1171800,1183263,1190293,1200865,1213581,1221642,1227735,1242257,1253139,1258607,1269432,1276443,1286897,1295523,1310043,1324202,1339086,1349688,1364018,1373510,1383330,1397957,1404820,1411071,1418535,1424950,1438971,1447001,1458053,1470427,1484599,1496630,1506638,1521545,1529007,1540854,1553560,1562760,1571143,1583962,1592403,1600649,1609909,1619781,1633670,1642535,1651952,1664016,1675697,1682512,1687825,1696070,1709477,1720807,1727109,1735901,1749459,1763083,1772475,1780053,1788569,1795812,1806561,1814207,1826801,1835732,1849992,1856131,1870823,1881790,1887300,1897428,1905085,1917498,1923600,1938125,1948224,1957054,1968569,1974994,1980340,1989133,1997675,2011017,2018660,2027204,2034206,2042518,2052817,2064245,2078392,2085679,2091182 --fpu_rate_warmup 0 --fsu_rate_divisor 10000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F3-W4 --prop_sample_run_id s1 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 10000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:11004, 1:24122, 2:34278, 3:48713, 4:57731, 5:70845, 6:82777, 7:97584, 8:110009, 9:123909, 10:136566, 11:144683, 12:157330, 13:171623, 14:184741, 15:192437, 16:200494, 17:207981, 18:218123, 19:224714, 20:231661, 21:238337, 22:244995, 23:259697, 24:266253, 25:277919, 26:284090, 27:292155, 28:306417, 29:316599, 30:324306, 31:329893, 32:341571, 33:354856, 34:362564, 35:372300, 36:378155, 37:388990, 38:396874, 39:407572, 40:418517, 41:424470, 42:438586, 43:447847, 44:458883, 45:469522, 46:480819, 47:492463, 48:502937, 49:512350, 50:525705, 51:539239, 52:552530, 53:564333, 54:574521, 55:585576, 56:591012, 57:599590, 58:609106, 59:615934, 60:627760, 61:634809, 62:645621, 63:659095, 64:670791, 65:683743, 66:690309, 67:704892, 68:716759, 69:725369, 70:731350, 71:736460, 72:750769, 73:759508, 74:773430, 75:784776, 76:795744, 77:806875, 78:814751, 79:825035, 80:832243, 81:838670, 82:845725, 83:851409, 84:864661, 85:870804, 86:878552, 87:891296, 88:899006, 89:906238, 90:917592, 91:928708, 92:939401, 93:948516, 94:956625, 95:970100, 96:984011, 97:997629, 98:1002717, 99:1015882, 100:1028846, 101:1038765, 102:1052286, 103:1064588, 104:1076863, 105:1089427, 106:1102135, 107:1114271, 108:1120562, 109:1128529, 110:1141808, 111:1149135, 112:1163369, 113:1171800, 114:1183263, 115:1190293, 116:1200865, 117:1213581, 118:1221642, 119:1227735, 120:1242257, 121:1253139, 122:1258607, 123:1269432, 124:1276443, 125:1286897, 126:1295523, 127:1310043, 128:1324202, 129:1339086, 130:1349688, 131:1364018, 132:1373510, 133:1383330, 134:1397957, 135:1404820, 136:1411071, 137:1418535, 138:1424950, 139:1438971, 140:1447001, 141:1458053, 142:1470427, 143:1484599, 144:1496630, 145:1506638, 146:1521545, 147:1529007, 148:1540854, 149:1553560, 150:1562760, 151:1571143, 152:1583962, 153:1592403, 154:1600649, 155:1609909, 156:1619781, 157:1633670, 158:1642535, 159:1651952, 160:1664016, 161:1675697, 162:1682512, 163:1687825, 164:1696070, 165:1709477, 166:1720807, 167:1727109, 168:1735901, 169:1749459, 170:1763083, 171:1772475, 172:1780053, 173:1788569, 174:1795812, 175:1806561, 176:1814207, 177:1826801, 178:1835732, 179:1849992, 180:1856131, 181:1870823, 182:1881790, 183:1887300, 184:1897428, 185:1905085, 186:1917498, 187:1923600, 188:1938125, 189:1948224, 190:1957054, 191:1968569, 192:1974994, 193:1980340, 194:1989133, 195:1997675, 196:2011017, 197:2018660, 198:2027204, 199:2034206, 200:2042518, 201:2052817, 202:2064245, 203:2078392, 204:2085679, 205:2091182 |
| ordinals SHA-256 | `5ed393fc2e10184bf912e82c33ec762680aab236cb33288cb0e2d59753b15397` |
| 注入数（actual/expected） | 206 / 206 |
| fault 数（事件流/injection log） | 206 / 206 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 29522185 / 76681 |
| sn / PC / opcode | 78913 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 11004 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11004 / 0 |
| terminal | full |

### fault 10

| 字段 | 值 |
|---|---|
| 根 event_id | `54` |
| tick / cycle | 201100130 / 522338 |
| sn / PC / opcode | 756327 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 123909 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13900 / 9 |
| terminal | full |

### fault 100

| 字段 | 值 |
|---|---|
| 根 event_id | `594` |
| tick / cycle | 1557589880 / 4045688 |
| sn / PC / opcode | 6108192 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1015882 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13165 / 99 |
| terminal | full |

### fault 101

| 字段 | 值 |
|---|---|
| 根 event_id | `600` |
| tick / cycle | 1577297645 / 4096877 |
| sn / PC / opcode | 6185956 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1028846 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12964 / 100 |
| terminal | full |

### fault 102

| 字段 | 值 |
|---|---|
| 根 event_id | `606` |
| tick / cycle | 1592424680 / 4136168 |
| sn / PC / opcode | 6245463 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1038765 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9919 / 101 |
| terminal | full |

### fault 103

| 字段 | 值 |
|---|---|
| 根 event_id | `612` |
| tick / cycle | 1612932860 / 4189436 |
| sn / PC / opcode | 6326605 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1052286 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13521 / 102 |
| terminal | full |

### fault 104

| 字段 | 值 |
|---|---|
| 根 event_id | `618` |
| tick / cycle | 1631670040 / 4238104 |
| sn / PC / opcode | 6400408 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1064588 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12302 / 103 |
| terminal | full |

### fault 105

| 字段 | 值 |
|---|---|
| 根 event_id | `624` |
| tick / cycle | 1650359480 / 4286648 |
| sn / PC / opcode | 6474062 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1076863 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12275 / 104 |
| terminal | full |

### fault 106

| 字段 | 值 |
|---|---|
| 根 event_id | `630` |
| tick / cycle | 1669494750 / 4336350 |
| sn / PC / opcode | 6549446 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1089427 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12564 / 105 |
| terminal | full |

### fault 107

| 字段 | 值 |
|---|---|
| 根 event_id | `636` |
| tick / cycle | 1688739360 / 4386336 |
| sn / PC / opcode | 6625694 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1102135 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12708 / 106 |
| terminal | full |

### fault 108

| 字段 | 值 |
|---|---|
| 根 event_id | `642` |
| tick / cycle | 1707196645 / 4434277 |
| sn / PC / opcode | 6698519 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1114271 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12136 / 107 |
| terminal | full |

### fault 109

| 字段 | 值 |
|---|---|
| 根 event_id | `648` |
| tick / cycle | 1716808940 / 4459244 |
| sn / PC / opcode | 6736252 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1120562 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6291 / 108 |
| terminal | full |

### fault 11

| 字段 | 值 |
|---|---|
| 根 event_id | `60` |
| tick / cycle | 220419430 / 572518 |
| sn / PC / opcode | 832285 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 136566 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12657 / 10 |
| terminal | full |

### fault 110

| 字段 | 值 |
|---|---|
| 根 event_id | `654` |
| tick / cycle | 1728940290 / 4490754 |
| sn / PC / opcode | 6784058 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1128529 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7967 / 109 |
| terminal | full |

### fault 111

| 字段 | 值 |
|---|---|
| 根 event_id | `660` |
| tick / cycle | 1749103125 / 4543125 |
| sn / PC / opcode | 6863728 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1141808 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13279 / 110 |
| terminal | full |

### fault 112

| 字段 | 值 |
|---|---|
| 根 event_id | `666` |
| tick / cycle | 1760357445 / 4572357 |
| sn / PC / opcode | 6907683 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1149135 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7327 / 111 |
| terminal | full |

### fault 113

| 字段 | 值 |
|---|---|
| 根 event_id | `672` |
| tick / cycle | 1781856615 / 4628199 |
| sn / PC / opcode | 6993107 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1163369 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14234 / 112 |
| terminal | full |

### fault 114

| 字段 | 值 |
|---|---|
| 根 event_id | `678` |
| tick / cycle | 1794758350 / 4661710 |
| sn / PC / opcode | 7043689 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1171800 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8431 / 113 |
| terminal | full |

### fault 115

| 字段 | 值 |
|---|---|
| 根 event_id | `684` |
| tick / cycle | 1812214635 / 4707051 |
| sn / PC / opcode | 7112451 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1183263 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11463 / 114 |
| terminal | full |

### fault 116

| 字段 | 值 |
|---|---|
| 根 event_id | `690` |
| tick / cycle | 1822843330 / 4734658 |
| sn / PC / opcode | 7154642 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1190293 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7030 / 115 |
| terminal | full |

### fault 117

| 字段 | 值 |
|---|---|
| 根 event_id | `696` |
| tick / cycle | 1838853170 / 4776242 |
| sn / PC / opcode | 7218074 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1200865 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10572 / 116 |
| terminal | full |

### fault 118

| 字段 | 值 |
|---|---|
| 根 event_id | `702` |
| tick / cycle | 1858230990 / 4826574 |
| sn / PC / opcode | 7294359 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1213581 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12716 / 117 |
| terminal | full |

### fault 119

| 字段 | 值 |
|---|---|
| 根 event_id | `708` |
| tick / cycle | 1870480920 / 4858392 |
| sn / PC / opcode | 7342741 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1221642 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8061 / 118 |
| terminal | full |

### fault 12

| 字段 | 值 |
|---|---|
| 根 event_id | `66` |
| tick / cycle | 232746360 / 604536 |
| sn / PC / opcode | 880991 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 144683 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8117 / 11 |
| terminal | full |

### fault 120

| 字段 | 值 |
|---|---|
| 根 event_id | `714` |
| tick / cycle | 1879822175 / 4882655 |
| sn / PC / opcode | 7379283 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1227735 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6093 / 119 |
| terminal | full |

### fault 121

| 字段 | 值 |
|---|---|
| 根 event_id | `720` |
| tick / cycle | 1901959290 / 4940154 |
| sn / PC / opcode | 7466435 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1242257 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14522 / 120 |
| terminal | full |

### fault 122

| 字段 | 值 |
|---|---|
| 根 event_id | `726` |
| tick / cycle | 1918391860 / 4982836 |
| sn / PC / opcode | 7531707 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1253139 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10882 / 121 |
| terminal | full |

### fault 123

| 字段 | 值 |
|---|---|
| 根 event_id | `732` |
| tick / cycle | 1926734040 / 5004504 |
| sn / PC / opcode | 7564535 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1258607 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5468 / 122 |
| terminal | full |

### fault 124

| 字段 | 值 |
|---|---|
| 根 event_id | `738` |
| tick / cycle | 1943198565 / 5047269 |
| sn / PC / opcode | 7629481 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1269432 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10825 / 123 |
| terminal | full |

### fault 125

| 字段 | 值 |
|---|---|
| 根 event_id | `744` |
| tick / cycle | 1953893095 / 5075047 |
| sn / PC / opcode | 7671531 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1276443 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7011 / 124 |
| terminal | full |

### fault 126

| 字段 | 值 |
|---|---|
| 根 event_id | `750` |
| tick / cycle | 1969683485 / 5116061 |
| sn / PC / opcode | 7734275 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1286897 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10454 / 125 |
| terminal | full |

### fault 127

| 字段 | 值 |
|---|---|
| 根 event_id | `756` |
| tick / cycle | 1982832005 / 5150213 |
| sn / PC / opcode | 7786011 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1295523 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8626 / 126 |
| terminal | full |

### fault 128

| 字段 | 值 |
|---|---|
| 根 event_id | `762` |
| tick / cycle | 2004957185 / 5207681 |
| sn / PC / opcode | 7873131 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1310043 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14520 / 127 |
| terminal | full |

### fault 129

| 字段 | 值 |
|---|---|
| 根 event_id | `768` |
| tick / cycle | 2026548755 / 5263763 |
| sn / PC / opcode | 7958092 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1324202 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14159 / 128 |
| terminal | full |

### fault 13

| 字段 | 值 |
|---|---|
| 根 event_id | `72` |
| tick / cycle | 252022155 / 654603 |
| sn / PC / opcode | 956880 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 157330 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12647 / 12 |
| terminal | full |

### fault 130

| 字段 | 值 |
|---|---|
| 根 event_id | `774` |
| tick / cycle | 2049093200 / 5322320 |
| sn / PC / opcode | 8047405 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1339086 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14884 / 129 |
| terminal | full |

### fault 131

| 字段 | 值 |
|---|---|
| 根 event_id | `780` |
| tick / cycle | 2065336735 / 5364511 |
| sn / PC / opcode | 8111017 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1349688 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10602 / 130 |
| terminal | full |

### fault 132

| 字段 | 值 |
|---|---|
| 根 event_id | `786` |
| tick / cycle | 2086976045 / 5420717 |
| sn / PC / opcode | 8196988 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1364018 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14330 / 131 |
| terminal | full |

### fault 133

| 字段 | 值 |
|---|---|
| 根 event_id | `792` |
| tick / cycle | 2101524040 / 5458504 |
| sn / PC / opcode | 8253940 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1373510 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9492 / 132 |
| terminal | full |

### fault 134

| 字段 | 值 |
|---|---|
| 根 event_id | `798` |
| tick / cycle | 2116472050 / 5497330 |
| sn / PC / opcode | 8312869 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1383330 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9820 / 133 |
| terminal | full |

### fault 135

| 字段 | 值 |
|---|---|
| 根 event_id | `804` |
| tick / cycle | 2138741220 / 5555172 |
| sn / PC / opcode | 8400635 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1397957 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14627 / 134 |
| terminal | full |

### fault 136

| 字段 | 值 |
|---|---|
| 根 event_id | `810` |
| tick / cycle | 2149116200 / 5582120 |
| sn / PC / opcode | 8441820 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1404820 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6863 / 135 |
| terminal | full |

### fault 137

| 字段 | 值 |
|---|---|
| 根 event_id | `816` |
| tick / cycle | 2158648030 / 5606878 |
| sn / PC / opcode | 8479299 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1411071 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6251 / 136 |
| terminal | full |

### fault 138

| 字段 | 值 |
|---|---|
| 根 event_id | `822` |
| tick / cycle | 2169908510 / 5636126 |
| sn / PC / opcode | 8524083 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1418535 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7464 / 137 |
| terminal | full |

### fault 139

| 字段 | 值 |
|---|---|
| 根 event_id | `828` |
| tick / cycle | 2179623985 / 5661361 |
| sn / PC / opcode | 8562600 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1424950 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6415 / 138 |
| terminal | full |

### fault 14

| 字段 | 值 |
|---|---|
| 根 event_id | `78` |
| tick / cycle | 273700350 / 710910 |
| sn / PC / opcode | 1042631 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 171623 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14293 / 13 |
| terminal | full |

### fault 140

| 字段 | 值 |
|---|---|
| 根 event_id | `834` |
| tick / cycle | 2201013430 / 5716918 |
| sn / PC / opcode | 8646699 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1438971 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14021 / 139 |
| terminal | full |

### fault 141

| 字段 | 值 |
|---|---|
| 根 event_id | `840` |
| tick / cycle | 2213219085 / 5748621 |
| sn / PC / opcode | 8694899 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1447001 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8030 / 140 |
| terminal | full |

### fault 142

| 字段 | 值 |
|---|---|
| 根 event_id | `846` |
| tick / cycle | 2230099025 / 5792465 |
| sn / PC / opcode | 8761211 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1458053 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11052 / 141 |
| terminal | full |

### fault 143

| 字段 | 值 |
|---|---|
| 根 event_id | `852` |
| tick / cycle | 2248849680 / 5841168 |
| sn / PC / opcode | 8835446 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1470427 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12374 / 142 |
| terminal | full |

### fault 144

| 字段 | 值 |
|---|---|
| 根 event_id | `858` |
| tick / cycle | 2270457420 / 5897292 |
| sn / PC / opcode | 8920478 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1484599 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14172 / 143 |
| terminal | full |

### fault 145

| 字段 | 值 |
|---|---|
| 根 event_id | `864` |
| tick / cycle | 2288853875 / 5945075 |
| sn / PC / opcode | 8992660 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1496630 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12031 / 144 |
| terminal | full |

### fault 146

| 字段 | 值 |
|---|---|
| 根 event_id | `870` |
| tick / cycle | 2303994000 / 5984400 |
| sn / PC / opcode | 9052708 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1506638 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10008 / 145 |
| terminal | full |

### fault 147

| 字段 | 值 |
|---|---|
| 根 event_id | `876` |
| tick / cycle | 2326664340 / 6043284 |
| sn / PC / opcode | 9142163 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1521545 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14907 / 146 |
| terminal | full |

### fault 148

| 字段 | 值 |
|---|---|
| 根 event_id | `882` |
| tick / cycle | 2337920200 / 6072520 |
| sn / PC / opcode | 9186915 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1529007 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7462 / 147 |
| terminal | full |

### fault 149

| 字段 | 值 |
|---|---|
| 根 event_id | `888` |
| tick / cycle | 2355943975 / 6119335 |
| sn / PC / opcode | 9258013 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1540854 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11847 / 148 |
| terminal | full |

### fault 15

| 字段 | 值 |
|---|---|
| 根 event_id | `84` |
| tick / cycle | 293711495 / 762887 |
| sn / PC / opcode | 1121330 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 184741 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13118 / 14 |
| terminal | full |

### fault 150

| 字段 | 值 |
|---|---|
| 根 event_id | `894` |
| tick / cycle | 2375274055 / 6169543 |
| sn / PC / opcode | 9334260 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1553560 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12706 / 149 |
| terminal | full |

### fault 151

| 字段 | 值 |
|---|---|
| 根 event_id | `900` |
| tick / cycle | 2389209515 / 6205739 |
| sn / PC / opcode | 9389449 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1562760 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9200 / 150 |
| terminal | full |

### fault 152

| 字段 | 值 |
|---|---|
| 根 event_id | `906` |
| tick / cycle | 2402041565 / 6239069 |
| sn / PC / opcode | 9439742 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1571143 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8383 / 151 |
| terminal | full |

### fault 153

| 字段 | 值 |
|---|---|
| 根 event_id | `912` |
| tick / cycle | 2486353870 / 6458062 |
| sn / PC / opcode | 9539260 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1583962 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12819 / 152 |
| terminal | full |

### fault 154

| 字段 | 值 |
|---|---|
| 根 event_id | `918` |
| tick / cycle | 2537763305 / 6591593 |
| sn / PC / opcode | 9607179 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1592403 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8441 / 153 |
| terminal | full |

### fault 155

| 字段 | 值 |
|---|---|
| 根 event_id | `924` |
| tick / cycle | 2596869660 / 6745116 |
| sn / PC / opcode | 9673501 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1600649 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8246 / 154 |
| terminal | full |

### fault 156

| 字段 | 值 |
|---|---|
| 根 event_id | `930` |
| tick / cycle | 2646612430 / 6874318 |
| sn / PC / opcode | 9747633 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1609909 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9260 / 155 |
| terminal | full |

### fault 157

| 字段 | 值 |
|---|---|
| 根 event_id | `936` |
| tick / cycle | 2702092855 / 7018423 |
| sn / PC / opcode | 9826655 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1619781 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9872 / 156 |
| terminal | full |

### fault 158

| 字段 | 值 |
|---|---|
| 根 event_id | `942` |
| tick / cycle | 2784214895 / 7231727 |
| sn / PC / opcode | 9937865 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1633670 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13889 / 157 |
| terminal | full |

### fault 159

| 字段 | 值 |
|---|---|
| 根 event_id | `948` |
| tick / cycle | 2831365075 / 7354195 |
| sn / PC / opcode | 10008837 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1642535 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8865 / 158 |
| terminal | full |

### fault 16

| 字段 | 值 |
|---|---|
| 根 event_id | `90` |
| tick / cycle | 305315395 / 793027 |
| sn / PC / opcode | 1167515 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 192437 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7696 / 15 |
| terminal | full |

### fault 160

| 字段 | 值 |
|---|---|
| 根 event_id | `954` |
| tick / cycle | 2885176910 / 7493966 |
| sn / PC / opcode | 10084219 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1651952 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9417 / 159 |
| terminal | full |

### fault 161

| 字段 | 值 |
|---|---|
| 根 event_id | `960` |
| tick / cycle | 2959935055 / 7688143 |
| sn / PC / opcode | 10180829 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1664016 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12064 / 160 |
| terminal | full |

### fault 162

| 字段 | 值 |
|---|---|
| 根 event_id | `966` |
| tick / cycle | 3020553690 / 7845594 |
| sn / PC / opcode | 10274329 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1675697 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11681 / 161 |
| terminal | full |

### fault 163

| 字段 | 值 |
|---|---|
| 根 event_id | `972` |
| tick / cycle | 3062224935 / 7953831 |
| sn / PC / opcode | 10328895 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1682512 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6815 / 162 |
| terminal | full |

### fault 164

| 字段 | 值 |
|---|---|
| 根 event_id | `978` |
| tick / cycle | 3085187875 / 8013475 |
| sn / PC / opcode | 10371451 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1687825 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5313 / 163 |
| terminal | full |

### fault 165

| 字段 | 值 |
|---|---|
| 根 event_id | `984` |
| tick / cycle | 3143309400 / 8164440 |
| sn / PC / opcode | 10437457 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1696070 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8245 / 164 |
| terminal | full |

### fault 166

| 字段 | 值 |
|---|---|
| 根 event_id | `990` |
| tick / cycle | 3214264130 / 8348738 |
| sn / PC / opcode | 10544765 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1709477 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13407 / 165 |
| terminal | full |

### fault 167

| 字段 | 值 |
|---|---|
| 根 event_id | `996` |
| tick / cycle | 3272716370 / 8500562 |
| sn / PC / opcode | 10635503 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1720807 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11330 / 166 |
| terminal | full |

### fault 168

| 字段 | 值 |
|---|---|
| 根 event_id | `1002` |
| tick / cycle | 3317046425 / 8615705 |
| sn / PC / opcode | 10685919 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1727109 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6302 / 167 |
| terminal | full |

### fault 169

| 字段 | 值 |
|---|---|
| 根 event_id | `1008` |
| tick / cycle | 3359359465 / 8725609 |
| sn / PC / opcode | 10756301 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1735901 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8792 / 168 |
| terminal | full |

### fault 17

| 字段 | 值 |
|---|---|
| 根 event_id | `96` |
| tick / cycle | 317670045 / 825117 |
| sn / PC / opcode | 1215864 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 200494 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8057 / 16 |
| terminal | full |

### fault 170

| 字段 | 值 |
|---|---|
| 根 event_id | `1014` |
| tick / cycle | 3440316495 / 8935887 |
| sn / PC / opcode | 10864863 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1749459 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13558 / 169 |
| terminal | full |

### fault 171

| 字段 | 值 |
|---|---|
| 根 event_id | `1020` |
| tick / cycle | 3522018500 / 9148100 |
| sn / PC / opcode | 10973953 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1763083 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13624 / 170 |
| terminal | full |

### fault 172

| 字段 | 值 |
|---|---|
| 根 event_id | `1026` |
| tick / cycle | 3568657785 / 9269241 |
| sn / PC / opcode | 11049141 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1772475 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9392 / 171 |
| terminal | full |

### fault 173

| 字段 | 值 |
|---|---|
| 根 event_id | `1032` |
| tick / cycle | 3617497730 / 9396098 |
| sn / PC / opcode | 11109811 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1780053 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7578 / 172 |
| terminal | full |

### fault 174

| 字段 | 值 |
|---|---|
| 根 event_id | `1038` |
| tick / cycle | 3660494530 / 9507778 |
| sn / PC / opcode | 11177991 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1788569 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8516 / 173 |
| terminal | full |

### fault 175

| 字段 | 值 |
|---|---|
| 根 event_id | `1044` |
| tick / cycle | 3708182940 / 9631644 |
| sn / PC / opcode | 11235981 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1795812 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7243 / 174 |
| terminal | full |

### fault 176

| 字段 | 值 |
|---|---|
| 根 event_id | `1050` |
| tick / cycle | 3763769240 / 9776024 |
| sn / PC / opcode | 11322025 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1806561 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10749 / 175 |
| terminal | full |

### fault 177

| 字段 | 值 |
|---|---|
| 根 event_id | `1056` |
| tick / cycle | 3809584240 / 9895024 |
| sn / PC / opcode | 11383239 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1814207 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7646 / 176 |
| terminal | full |

### fault 178

| 字段 | 值 |
|---|---|
| 根 event_id | `1062` |
| tick / cycle | 3886970010 / 10096026 |
| sn / PC / opcode | 11484043 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1826801 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12594 / 177 |
| terminal | full |

### fault 179

| 字段 | 值 |
|---|---|
| 根 event_id | `1068` |
| tick / cycle | 3926653500 / 10199100 |
| sn / PC / opcode | 11555589 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1835732 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8931 / 178 |
| terminal | full |

### fault 18

| 字段 | 值 |
|---|---|
| 根 event_id | `102` |
| tick / cycle | 328961325 / 854445 |
| sn / PC / opcode | 1260759 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 207981 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7487 / 17 |
| terminal | full |

### fault 180

| 字段 | 值 |
|---|---|
| 根 event_id | `1074` |
| tick / cycle | 4009081230 / 10413198 |
| sn / PC / opcode | 11669715 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1849992 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14260 / 179 |
| terminal | full |

### fault 181

| 字段 | 值 |
|---|---|
| 根 event_id | `1080` |
| tick / cycle | 4046483210 / 10510346 |
| sn / PC / opcode | 11718879 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1856131 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6139 / 180 |
| terminal | full |

### fault 182

| 字段 | 值 |
|---|---|
| 根 event_id | `1086` |
| tick / cycle | 4127821005 / 10721613 |
| sn / PC / opcode | 11836513 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1870823 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14692 / 181 |
| terminal | full |

### fault 183

| 字段 | 值 |
|---|---|
| 根 event_id | `1092` |
| tick / cycle | 4190590250 / 10884650 |
| sn / PC / opcode | 11924295 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1881790 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10967 / 182 |
| terminal | full |

### fault 184

| 字段 | 值 |
|---|---|
| 根 event_id | `1098` |
| tick / cycle | 4221226625 / 10964225 |
| sn / PC / opcode | 11968427 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1887300 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5510 / 183 |
| terminal | full |

### fault 185

| 字段 | 值 |
|---|---|
| 根 event_id | `1104` |
| tick / cycle | 4279881375 / 11116575 |
| sn / PC / opcode | 12049497 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1897428 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10128 / 184 |
| terminal | full |

### fault 186

| 字段 | 值 |
|---|---|
| 根 event_id | `1110` |
| tick / cycle | 4323277035 / 11229291 |
| sn / PC / opcode | 12110805 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1905085 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7657 / 185 |
| terminal | full |

### fault 187

| 字段 | 值 |
|---|---|
| 根 event_id | `1116` |
| tick / cycle | 4389435050 / 11401130 |
| sn / PC / opcode | 12210207 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1917498 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12413 / 186 |
| terminal | full |

### fault 188

| 字段 | 值 |
|---|---|
| 根 event_id | `1122` |
| tick / cycle | 4432711360 / 11513536 |
| sn / PC / opcode | 12259023 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1923600 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6102 / 187 |
| terminal | full |

### fault 189

| 字段 | 值 |
|---|---|
| 根 event_id | `1128` |
| tick / cycle | 4511498530 / 11718178 |
| sn / PC / opcode | 12375321 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1938125 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14525 / 188 |
| terminal | full |

### fault 19

| 字段 | 值 |
|---|---|
| 根 event_id | `108` |
| tick / cycle | 344403290 / 894554 |
| sn / PC / opcode | 1321631 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 218123 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10142 / 18 |
| terminal | full |

### fault 190

| 字段 | 值 |
|---|---|
| 根 event_id | `1134` |
| tick / cycle | 4565902495 / 11859487 |
| sn / PC / opcode | 12456159 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1948224 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10099 / 189 |
| terminal | full |

### fault 191

| 字段 | 值 |
|---|---|
| 根 event_id | `1140` |
| tick / cycle | 4623627085 / 12009421 |
| sn / PC / opcode | 12526851 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1957054 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8830 / 190 |
| terminal | full |

### fault 192

| 字段 | 值 |
|---|---|
| 根 event_id | `1146` |
| tick / cycle | 4681159175 / 12158855 |
| sn / PC / opcode | 12619069 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1968569 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11515 / 191 |
| terminal | full |

### fault 193

| 字段 | 值 |
|---|---|
| 根 event_id | `1152` |
| tick / cycle | 4726281560 / 12276056 |
| sn / PC / opcode | 12670515 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1974994 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6425 / 192 |
| terminal | full |

### fault 194

| 字段 | 值 |
|---|---|
| 根 event_id | `1158` |
| tick / cycle | 4749080490 / 12335274 |
| sn / PC / opcode | 12713283 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1980340 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5346 / 193 |
| terminal | full |

### fault 195

| 字段 | 值 |
|---|---|
| 根 event_id | `1164` |
| tick / cycle | 4804599800 / 12479480 |
| sn / PC / opcode | 12783679 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1989133 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8793 / 194 |
| terminal | full |

### fault 196

| 字段 | 值 |
|---|---|
| 根 event_id | `1170` |
| tick / cycle | 4846286060 / 12587756 |
| sn / PC / opcode | 12852061 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1997675 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8542 / 195 |
| terminal | full |

### fault 197

| 字段 | 值 |
|---|---|
| 根 event_id | `1176` |
| tick / cycle | 4926555480 / 12796248 |
| sn / PC / opcode | 12958895 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 2011017 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13342 / 196 |
| terminal | full |

### fault 198

| 字段 | 值 |
|---|---|
| 根 event_id | `1182` |
| tick / cycle | 4966910025 / 12901065 |
| sn / PC / opcode | 13020091 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 2018660 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7643 / 197 |
| terminal | full |

### fault 199

| 字段 | 值 |
|---|---|
| 根 event_id | `1188` |
| tick / cycle | 5018965490 / 13036274 |
| sn / PC / opcode | 13088489 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 2027204 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8544 / 198 |
| terminal | full |

### fault 2

| 字段 | 值 |
|---|---|
| 根 event_id | `6` |
| tick / cycle | 49372785 / 128241 |
| sn / PC / opcode | 157612 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 24122 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13118 / 1 |
| terminal | full |

### fault 20

| 字段 | 值 |
|---|---|
| 根 event_id | `114` |
| tick / cycle | 354504535 / 920791 |
| sn / PC / opcode | 1361164 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 224714 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6591 / 19 |
| terminal | full |

### fault 200

| 字段 | 值 |
|---|---|
| 根 event_id | `1194` |
| tick / cycle | 5055274455 / 13130583 |
| sn / PC / opcode | 13144557 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 2034206 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7002 / 199 |
| terminal | full |

### fault 201

| 字段 | 值 |
|---|---|
| 根 event_id | `1200` |
| tick / cycle | 5107651395 / 13266627 |
| sn / PC / opcode | 13211099 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 2042518 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8312 / 200 |
| terminal | full |

### fault 202

| 字段 | 值 |
|---|---|
| 根 event_id | `1206` |
| tick / cycle | 5163400935 / 13411431 |
| sn / PC / opcode | 13293543 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 2052817 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10299 / 201 |
| terminal | full |

### fault 203

| 字段 | 值 |
|---|---|
| 根 event_id | `1212` |
| tick / cycle | 5223429365 / 13567349 |
| sn / PC / opcode | 13385013 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 2064245 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11428 / 202 |
| terminal | full |

### fault 204

| 字段 | 值 |
|---|---|
| 根 event_id | `1218` |
| tick / cycle | 5307411340 / 13785484 |
| sn / PC / opcode | 13498287 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 2078392 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14147 / 203 |
| terminal | full |

### fault 205

| 字段 | 值 |
|---|---|
| 根 event_id | `1224` |
| tick / cycle | 5351062255 / 13898863 |
| sn / PC / opcode | 13556635 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 2085679 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7287 / 204 |
| terminal | full |

### fault 206

| 字段 | 值 |
|---|---|
| 根 event_id | `1230` |
| tick / cycle | 5385550170 / 13988442 |
| sn / PC / opcode | 13600705 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 2091182 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5503 / 205 |
| terminal | full |

### fault 21

| 字段 | 值 |
|---|---|
| 根 event_id | `120` |
| tick / cycle | 365033130 / 948138 |
| sn / PC / opcode | 1402850 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 231661 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6947 / 20 |
| terminal | full |

### fault 22

| 字段 | 值 |
|---|---|
| 根 event_id | `126` |
| tick / cycle | 375131680 / 974368 |
| sn / PC / opcode | 1442915 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 238337 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6676 / 21 |
| terminal | full |

### fault 23

| 字段 | 值 |
|---|---|
| 根 event_id | `132` |
| tick / cycle | 385275660 / 1000716 |
| sn / PC / opcode | 1482843 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 244995 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6658 / 22 |
| terminal | full |

### fault 24

| 字段 | 值 |
|---|---|
| 根 event_id | `138` |
| tick / cycle | 407681120 / 1058912 |
| sn / PC / opcode | 1571075 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 259697 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14702 / 23 |
| terminal | full |

### fault 25

| 字段 | 值 |
|---|---|
| 根 event_id | `144` |
| tick / cycle | 417599875 / 1084675 |
| sn / PC / opcode | 1610391 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 266253 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6556 / 24 |
| terminal | full |

### fault 26

| 字段 | 值 |
|---|---|
| 根 event_id | `150` |
| tick / cycle | 435360310 / 1130806 |
| sn / PC / opcode | 1680407 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 277919 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11666 / 25 |
| terminal | full |

### fault 27

| 字段 | 值 |
|---|---|
| 根 event_id | `156` |
| tick / cycle | 444712345 / 1155097 |
| sn / PC / opcode | 1717420 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 284090 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6171 / 26 |
| terminal | full |

### fault 28

| 字段 | 值 |
|---|---|
| 根 event_id | `162` |
| tick / cycle | 457127055 / 1187343 |
| sn / PC / opcode | 1765803 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 292155 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8065 / 27 |
| terminal | full |

### fault 29

| 字段 | 值 |
|---|---|
| 根 event_id | `168` |
| tick / cycle | 478705920 / 1243392 |
| sn / PC / opcode | 1851375 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 306417 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14262 / 28 |
| terminal | full |

### fault 3

| 字段 | 值 |
|---|---|
| 根 event_id | `12` |
| tick / cycle | 64836310 / 168406 |
| sn / PC / opcode | 218557 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 34278 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10156 / 2 |
| terminal | full |

### fault 30

| 字段 | 值 |
|---|---|
| 根 event_id | `174` |
| tick / cycle | 494194855 / 1283623 |
| sn / PC / opcode | 1912467 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 316599 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10182 / 29 |
| terminal | full |

### fault 31

| 字段 | 值 |
|---|---|
| 根 event_id | `180` |
| tick / cycle | 505922725 / 1314085 |
| sn / PC / opcode | 1958725 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 324306 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7707 / 30 |
| terminal | full |

### fault 32

| 字段 | 值 |
|---|---|
| 根 event_id | `186` |
| tick / cycle | 514413130 / 1336138 |
| sn / PC / opcode | 1992242 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 329893 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5587 / 31 |
| terminal | full |

### fault 33

| 字段 | 值 |
|---|---|
| 根 event_id | `192` |
| tick / cycle | 532188965 / 1382309 |
| sn / PC / opcode | 2062299 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 341571 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11678 / 32 |
| terminal | full |

### fault 34

| 字段 | 值 |
|---|---|
| 根 event_id | `198` |
| tick / cycle | 552389145 / 1434777 |
| sn / PC / opcode | 2142036 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 354856 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13285 / 33 |
| terminal | full |

### fault 35

| 字段 | 值 |
|---|---|
| 根 event_id | `204` |
| tick / cycle | 564008060 / 1464956 |
| sn / PC / opcode | 2188264 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 362564 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7708 / 34 |
| terminal | full |

### fault 36

| 字段 | 值 |
|---|---|
| 根 event_id | `210` |
| tick / cycle | 578936435 / 1503731 |
| sn / PC / opcode | 2246689 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 372300 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9736 / 35 |
| terminal | full |

### fault 37

| 字段 | 值 |
|---|---|
| 根 event_id | `216` |
| tick / cycle | 587823390 / 1526814 |
| sn / PC / opcode | 2281823 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 378155 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5855 / 36 |
| terminal | full |

### fault 38

| 字段 | 值 |
|---|---|
| 根 event_id | `222` |
| tick / cycle | 604252880 / 1569488 |
| sn / PC / opcode | 2346840 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 388990 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10835 / 37 |
| terminal | full |

### fault 39

| 字段 | 值 |
|---|---|
| 根 event_id | `228` |
| tick / cycle | 616325710 / 1600846 |
| sn / PC / opcode | 2394144 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 396874 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7884 / 38 |
| terminal | full |

### fault 4

| 字段 | 值 |
|---|---|
| 根 event_id | `18` |
| tick / cycle | 86689295 / 225167 |
| sn / PC / opcode | 305171 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 48713 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14435 / 3 |
| terminal | full |

### fault 40

| 字段 | 值 |
|---|---|
| 根 event_id | `234` |
| tick / cycle | 632446815 / 1642719 |
| sn / PC / opcode | 2458332 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 407572 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10698 / 39 |
| terminal | full |

### fault 41

| 字段 | 值 |
|---|---|
| 根 event_id | `240` |
| tick / cycle | 649202400 / 1686240 |
| sn / PC / opcode | 2523995 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 418517 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10945 / 40 |
| terminal | full |

### fault 42

| 字段 | 值 |
|---|---|
| 根 event_id | `246` |
| tick / cycle | 658231805 / 1709693 |
| sn / PC / opcode | 2559709 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 424470 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5953 / 41 |
| terminal | full |

### fault 43

| 字段 | 值 |
|---|---|
| 根 event_id | `252` |
| tick / cycle | 679636650 / 1765290 |
| sn / PC / opcode | 2644416 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 438586 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14116 / 42 |
| terminal | full |

### fault 44

| 字段 | 值 |
|---|---|
| 根 event_id | `258` |
| tick / cycle | 693780780 / 1802028 |
| sn / PC / opcode | 2699966 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 447847 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9261 / 43 |
| terminal | full |

### fault 45

| 字段 | 值 |
|---|---|
| 根 event_id | `264` |
| tick / cycle | 710627995 / 1845787 |
| sn / PC / opcode | 2766171 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 458883 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11036 / 44 |
| terminal | full |

### fault 46

| 字段 | 值 |
|---|---|
| 根 event_id | `270` |
| tick / cycle | 726665170 / 1887442 |
| sn / PC / opcode | 2830032 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 469522 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10639 / 45 |
| terminal | full |

### fault 47

| 字段 | 值 |
|---|---|
| 根 event_id | `276` |
| tick / cycle | 743903930 / 1932218 |
| sn / PC / opcode | 2897787 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 480819 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11297 / 46 |
| terminal | full |

### fault 48

| 字段 | 值 |
|---|---|
| 根 event_id | `282` |
| tick / cycle | 761658590 / 1978334 |
| sn / PC / opcode | 2967662 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 492463 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11644 / 47 |
| terminal | full |

### fault 49

| 字段 | 值 |
|---|---|
| 根 event_id | `288` |
| tick / cycle | 777491715 / 2019459 |
| sn / PC / opcode | 3030515 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 502937 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10474 / 48 |
| terminal | full |

### fault 5

| 字段 | 值 |
|---|---|
| 根 event_id | `24` |
| tick / cycle | 100358720 / 260672 |
| sn / PC / opcode | 359279 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 57731 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9018 / 4 |
| terminal | full |

### fault 50

| 字段 | 值 |
|---|---|
| 根 event_id | `294` |
| tick / cycle | 791870310 / 2056806 |
| sn / PC / opcode | 3087000 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 512350 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9413 / 49 |
| terminal | full |

### fault 51

| 字段 | 值 |
|---|---|
| 根 event_id | `300` |
| tick / cycle | 812273000 / 2109800 |
| sn / PC / opcode | 3167103 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 525705 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13355 / 50 |
| terminal | full |

### fault 52

| 字段 | 值 |
|---|---|
| 根 event_id | `306` |
| tick / cycle | 832779255 / 2163063 |
| sn / PC / opcode | 3248318 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 539239 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13534 / 51 |
| terminal | full |

### fault 53

| 字段 | 值 |
|---|---|
| 根 event_id | `312` |
| tick / cycle | 852960955 / 2215483 |
| sn / PC / opcode | 3328060 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 552530 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13291 / 52 |
| terminal | full |

### fault 54

| 字段 | 值 |
|---|---|
| 根 event_id | `318` |
| tick / cycle | 870840740 / 2261924 |
| sn / PC / opcode | 3398871 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 564333 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11803 / 53 |
| terminal | full |

### fault 55

| 字段 | 值 |
|---|---|
| 根 event_id | `324` |
| tick / cycle | 886331600 / 2302160 |
| sn / PC / opcode | 3459999 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 574521 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10188 / 54 |
| terminal | full |

### fault 56

| 字段 | 值 |
|---|---|
| 根 event_id | `330` |
| tick / cycle | 903241955 / 2346083 |
| sn / PC / opcode | 3526345 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 585576 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11055 / 55 |
| terminal | full |

### fault 57

| 字段 | 值 |
|---|---|
| 根 event_id | `336` |
| tick / cycle | 911509445 / 2367557 |
| sn / PC / opcode | 3558961 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 591012 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5436 / 56 |
| terminal | full |

### fault 58

| 字段 | 值 |
|---|---|
| 根 event_id | `342` |
| tick / cycle | 924617925 / 2401605 |
| sn / PC / opcode | 3610440 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 599590 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8578 / 57 |
| terminal | full |

### fault 59

| 字段 | 值 |
|---|---|
| 根 event_id | `348` |
| tick / cycle | 939033095 / 2439047 |
| sn / PC / opcode | 3667536 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 609106 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9516 / 58 |
| terminal | full |

### fault 6

| 字段 | 值 |
|---|---|
| 根 event_id | `30` |
| tick / cycle | 120401050 / 312730 |
| sn / PC / opcode | 437943 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 70845 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13114 / 5 |
| terminal | full |

### fault 60

| 字段 | 值 |
|---|---|
| 根 event_id | `354` |
| tick / cycle | 949414620 / 2466012 |
| sn / PC / opcode | 3708504 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 615934 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6828 / 59 |
| terminal | full |

### fault 61

| 字段 | 值 |
|---|---|
| 根 event_id | `360` |
| tick / cycle | 967464575 / 2512895 |
| sn / PC / opcode | 3779460 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 627760 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11826 / 60 |
| terminal | full |

### fault 62

| 字段 | 值 |
|---|---|
| 根 event_id | `366` |
| tick / cycle | 978109440 / 2540544 |
| sn / PC / opcode | 3821727 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 634809 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7049 / 61 |
| terminal | full |

### fault 63

| 字段 | 值 |
|---|---|
| 根 event_id | `372` |
| tick / cycle | 994652890 / 2583514 |
| sn / PC / opcode | 3886599 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 645621 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10812 / 62 |
| terminal | full |

### fault 64

| 字段 | 值 |
|---|---|
| 根 event_id | `378` |
| tick / cycle | 1015164535 / 2636791 |
| sn / PC / opcode | 3967454 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 659095 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13474 / 63 |
| terminal | full |

### fault 65

| 字段 | 值 |
|---|---|
| 根 event_id | `384` |
| tick / cycle | 1032926895 / 2682927 |
| sn / PC / opcode | 4037619 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 670791 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11696 / 64 |
| terminal | full |

### fault 66

| 字段 | 值 |
|---|---|
| 根 event_id | `390` |
| tick / cycle | 1052543030 / 2733878 |
| sn / PC / opcode | 4115342 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 683743 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12952 / 65 |
| terminal | full |

### fault 67

| 字段 | 值 |
|---|---|
| 根 event_id | `396` |
| tick / cycle | 1062498360 / 2759736 |
| sn / PC / opcode | 4154727 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 690309 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6566 / 66 |
| terminal | full |

### fault 68

| 字段 | 值 |
|---|---|
| 根 event_id | `402` |
| tick / cycle | 1084757135 / 2817551 |
| sn / PC / opcode | 4242241 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 704892 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14583 / 67 |
| terminal | full |

### fault 69

| 字段 | 值 |
|---|---|
| 根 event_id | `408` |
| tick / cycle | 1102733940 / 2864244 |
| sn / PC / opcode | 4313447 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 716759 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11867 / 68 |
| terminal | full |

### fault 7

| 字段 | 值 |
|---|---|
| 根 event_id | `36` |
| tick / cycle | 138442535 / 359591 |
| sn / PC / opcode | 509546 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 82777 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11932 / 6 |
| terminal | full |

### fault 70

| 字段 | 值 |
|---|---|
| 根 event_id | `414` |
| tick / cycle | 1115867060 / 2898356 |
| sn / PC / opcode | 4365107 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 725369 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8610 / 69 |
| terminal | full |

### fault 71

| 字段 | 值 |
|---|---|
| 根 event_id | `420` |
| tick / cycle | 1124940355 / 2921923 |
| sn / PC / opcode | 4401000 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 731350 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5981 / 70 |
| terminal | full |

### fault 72

| 字段 | 值 |
|---|---|
| 根 event_id | `426` |
| tick / cycle | 1132607245 / 2941837 |
| sn / PC / opcode | 4431640 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 736460 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5110 / 71 |
| terminal | full |

### fault 73

| 字段 | 值 |
|---|---|
| 根 event_id | `432` |
| tick / cycle | 1154501425 / 2998705 |
| sn / PC / opcode | 4517498 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 750769 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14309 / 72 |
| terminal | full |

### fault 74

| 字段 | 值 |
|---|---|
| 根 event_id | `438` |
| tick / cycle | 1167775455 / 3033183 |
| sn / PC / opcode | 4569948 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 759508 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8739 / 73 |
| terminal | full |

### fault 75

| 字段 | 值 |
|---|---|
| 根 event_id | `444` |
| tick / cycle | 1188908875 / 3088075 |
| sn / PC / opcode | 4653469 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 773430 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13922 / 74 |
| terminal | full |

### fault 76

| 字段 | 值 |
|---|---|
| 根 event_id | `450` |
| tick / cycle | 1206211545 / 3133017 |
| sn / PC / opcode | 4721545 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 784776 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11346 / 75 |
| terminal | full |

### fault 77

| 字段 | 值 |
|---|---|
| 根 event_id | `456` |
| tick / cycle | 1222758845 / 3175997 |
| sn / PC / opcode | 4787353 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 795744 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10968 / 76 |
| terminal | full |

### fault 78

| 字段 | 值 |
|---|---|
| 根 event_id | `462` |
| tick / cycle | 1239771995 / 3220187 |
| sn / PC / opcode | 4854134 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 806875 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11131 / 77 |
| terminal | full |

### fault 79

| 字段 | 值 |
|---|---|
| 根 event_id | `468` |
| tick / cycle | 1251804400 / 3251440 |
| sn / PC / opcode | 4901399 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 814751 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7876 / 78 |
| terminal | full |

### fault 8

| 字段 | 值 |
|---|---|
| 根 event_id | `42` |
| tick / cycle | 160998915 / 418179 |
| sn / PC / opcode | 598393 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 97584 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14807 / 7 |
| terminal | full |

### fault 80

| 字段 | 值 |
|---|---|
| 根 event_id | `474` |
| tick / cycle | 1267342230 / 3291798 |
| sn / PC / opcode | 4963103 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 825035 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10284 / 79 |
| terminal | full |

### fault 81

| 字段 | 值 |
|---|---|
| 根 event_id | `480` |
| tick / cycle | 1278298560 / 3320256 |
| sn / PC / opcode | 5006342 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 832243 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7208 / 80 |
| terminal | full |

### fault 82

| 字段 | 值 |
|---|---|
| 根 event_id | `486` |
| tick / cycle | 1288029435 / 3345531 |
| sn / PC / opcode | 5044900 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 838670 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6427 / 81 |
| terminal | full |

### fault 83

| 字段 | 值 |
|---|---|
| 根 event_id | `492` |
| tick / cycle | 1298926860 / 3373836 |
| sn / PC / opcode | 5087234 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 845725 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7055 / 82 |
| terminal | full |

### fault 84

| 字段 | 值 |
|---|---|
| 根 event_id | `498` |
| tick / cycle | 1307559715 / 3396259 |
| sn / PC / opcode | 5121327 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 851409 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5684 / 83 |
| terminal | full |

### fault 85

| 字段 | 值 |
|---|---|
| 根 event_id | `504` |
| tick / cycle | 1327624760 / 3448376 |
| sn / PC / opcode | 5200850 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 864661 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13252 / 84 |
| terminal | full |

### fault 86

| 字段 | 值 |
|---|---|
| 根 event_id | `510` |
| tick / cycle | 1336935600 / 3472560 |
| sn / PC / opcode | 5237713 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 870804 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6143 / 85 |
| terminal | full |

### fault 87

| 字段 | 值 |
|---|---|
| 根 event_id | `516` |
| tick / cycle | 1348714290 / 3503154 |
| sn / PC / opcode | 5284192 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 878552 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7748 / 86 |
| terminal | full |

### fault 88

| 字段 | 值 |
|---|---|
| 根 event_id | `522` |
| tick / cycle | 1368217235 / 3553811 |
| sn / PC / opcode | 5360656 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 891296 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12744 / 87 |
| terminal | full |

### fault 89

| 字段 | 值 |
|---|---|
| 根 event_id | `528` |
| tick / cycle | 1379840770 / 3584002 |
| sn / PC / opcode | 5406916 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 899006 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7710 / 88 |
| terminal | full |

### fault 9

| 字段 | 值 |
|---|---|
| 根 event_id | `48` |
| tick / cycle | 179911655 / 467303 |
| sn / PC / opcode | 672947 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 110009 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12425 / 8 |
| terminal | full |

### fault 90

| 字段 | 值 |
|---|---|
| 根 event_id | `534` |
| tick / cycle | 1390846380 / 3612588 |
| sn / PC / opcode | 5450328 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 906238 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7232 / 89 |
| terminal | full |

### fault 91

| 字段 | 值 |
|---|---|
| 根 event_id | `540` |
| tick / cycle | 1408090145 / 3657377 |
| sn / PC / opcode | 5518441 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 917592 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11354 / 90 |
| terminal | full |

### fault 92

| 字段 | 值 |
|---|---|
| 根 event_id | `546` |
| tick / cycle | 1425052475 / 3701435 |
| sn / PC / opcode | 5585148 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 928708 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11116 / 91 |
| terminal | full |

### fault 93

| 字段 | 值 |
|---|---|
| 根 event_id | `552` |
| tick / cycle | 1441278300 / 3743580 |
| sn / PC / opcode | 5649299 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 939401 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10693 / 92 |
| terminal | full |

### fault 94

| 字段 | 值 |
|---|---|
| 根 event_id | `558` |
| tick / cycle | 1455089790 / 3779454 |
| sn / PC / opcode | 5703985 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 948516 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9115 / 93 |
| terminal | full |

### fault 95

| 字段 | 值 |
|---|---|
| 根 event_id | `564` |
| tick / cycle | 1467536840 / 3811784 |
| sn / PC / opcode | 5752623 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 956625 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8109 / 94 |
| terminal | full |

### fault 96

| 字段 | 值 |
|---|---|
| 根 event_id | `570` |
| tick / cycle | 1487964555 / 3864843 |
| sn / PC / opcode | 5833480 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 970100 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13475 / 95 |
| terminal | full |

### fault 97

| 字段 | 值 |
|---|---|
| 根 event_id | `576` |
| tick / cycle | 1509184985 / 3919961 |
| sn / PC / opcode | 5916959 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 984011 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13911 / 96 |
| terminal | full |

### fault 98

| 字段 | 值 |
|---|---|
| 根 event_id | `582` |
| tick / cycle | 1529860640 / 3973664 |
| sn / PC / opcode | 5998647 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 997629 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13618 / 97 |
| terminal | full |

### fault 99

| 字段 | 值 |
|---|---|
| 根 event_id | `588` |
| tick / cycle | 1537614540 / 3993804 |
| sn / PC / opcode | 6029175 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1002717 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5088 / 98 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 5223429365, Site: dyn_inst_execute, opClass=8, sn=13385013, bitseg=mant_lo, mask=0x1000, faults_injected: 203
Tick: 5307411340, Site: dyn_inst_execute, opClass=8, sn=13498287, bitseg=mant_lo, mask=0x100, faults_injected: 204
Tick: 5351062255, Site: dyn_inst_execute, opClass=8, sn=13556635, bitseg=mant_lo, mask=0x2, faults_injected: 205
Tick: 5385550170, Site: dyn_inst_execute, opClass=8, sn=13600705, bitseg=mant_lo, mask=0x8000, faults_injected: 206
CHAOS_RATE_COMPLETE=206
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4075a00000000000 → 0x4075a00000002000 |
| old/new hash | 0xdde4bf7b9e69312e → 0xb1b970c7122a6d0e |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4075a00000000000 / 0x4075a00000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 10

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff0a3d70a3d70a4 → 0x3ff0a3d70a3d70a5 |
| old/new hash | 0x42cdf33f00dda57f → 0x58e188605491c8e2 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff0a3d70a3d70a4 / 0x3ff0a3d70a3d70a5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 100

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407f300000000000 → 0x407f300000000080 |
| old/new hash | 0xbbd1b37e5fb66264 → 0x3e6e2ef8e81151e4 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407f300000000000 / 0x407f300000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 101

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd8000000000000 → 0xbfd8000000000020 |
| old/new hash | 0x4aa52a7eb1ced022 → 0x284b4ba00e46ec82 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd8000000000000 / 0xbfd8000000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 102

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feb0a3d70a3d70a → 0x3feb0a3d70a3d72a |
| old/new hash | 0x829a06134ebd3806 → 0x5125fed5696ebb66 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feb0a3d70a3d70a / 0x3feb0a3d70a3d72a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 103

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408a680000000000 → 0x408a680000008000 |
| old/new hash | 0x1643397f23ee5d21 → 0x706b74563ce818a1 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408a680000000000 / 0x408a680000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 104

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd4395810624dd3 → 0xbfd4395810634dd3 |
| old/new hash | 0xf01522948884c5f7 → 0x57c69062b84dd282 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd4395810624dd3 / 0xbfd4395810634dd3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 105

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feda1cac083126f → 0x3feda1cac083127f |
| old/new hash | 0x1b0c8561a8cd8c00 → 0xefaf4f91db70b350 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feda1cac083126f / 0x3feda1cac083127f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 106

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff4ed916872b021 → 0x3ff4ed916872b061 |
| old/new hash | 0xfc0f755056d11d67 → 0x1d71335d36e6a4a7 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff4ed916872b021 / 0x3ff4ed916872b061 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 107

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff0ac083126e979 → 0x3ff0ac083126ed79 |
| old/new hash | 0x5f748907c1653689 → 0x2ea04595764fae35 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff0ac083126e979 / 0x3ff0ac083126ed79 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 108

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4070300000000000 → 0x4070300000004000 |
| old/new hash | 0xbbe9fd7e5fcb7203 → 0x123b6012d630e3c3 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4070300000000000 / 0x4070300000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 109

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fa810624dd2f1ac → 0x3fa810624dd271ac |
| old/new hash | 0x04aa73d607a40d46 → 0x47b26bece636dcc6 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fa810624dd2f1ac / 0x3fa810624dd271ac |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 11

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4074000000000000 → 0x4074000000000004 |
| old/new hash | 0x48ae857eb0240977 → 0xc55871a2dc83bc73 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4074000000000000 / 0x4074000000000004 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 110

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff2ed916872b021 → 0x3ff2ed916872b0a1 |
| old/new hash | 0xfbfaf55056bf9add → 0x848ede1deaa94a5d |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff2ed916872b021 / 0x3ff2ed916872b0a1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 111

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd79db22d0e5604 → 0xbfd79db22d0e5606 |
| old/new hash | 0xe4b279b5b1c8a06f → 0x42e5bc9bd4bfba79 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd79db22d0e5604 / 0xbfd79db22d0e5606 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 112

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd916872b020c4a → 0x3fd916872b022c4a |
| old/new hash | 0x8be5d9460576e373 → 0x0c6ab79ab37758d3 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd916872b020c4a / 0x3fd916872b022c4a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 113

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4086a00000000000 → 0x4086a00000020000 |
| old/new hash | 0xdfcab97ba0061515 → 0xf71fc91be34a1b87 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4086a00000000000 / 0x4086a00000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 114

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081400000000000 → 0x4081400000008000 |
| old/new hash | 0x70a6a77fe819f1ba → 0xcacee2570113ad3a |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081400000000000 / 0x4081400000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 115

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe604189374bc6b → 0x3fe604189374bc69 |
| old/new hash | 0x43ca7c53d0d7726a → 0x4e2c16cc0a382d10 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe604189374bc6b / 0x3fe604189374bc69 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 116

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe2978d4fdf3b64 → 0x3fe2978d4fdf3a64 |
| old/new hash | 0xa3c3009a6deb57ab → 0x1329df850b3129b8 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe2978d4fdf3b64 / 0x3fe2978d4fdf3a64 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 117

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff70624dd2f1aa0 → 0x3ff70624dd2f1ae0 |
| old/new hash | 0xb8b23b9a0334f78d → 0xd088931b682e45cd |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff70624dd2f1aa0 / 0x3ff70624dd2f1ae0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 118

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd6666666666666 → 0x3fd6666666666266 |
| old/new hash | 0xb3bc3a404c2afb68 → 0x9f01bac5d22491c4 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd6666666666666 / 0x3fd6666666666266 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 119

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408a500000000000 → 0x408a500000004000 |
| old/new hash | 0xfe85418039622f79 → 0xfe6724123a586a39 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408a500000000000 / 0x408a500000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 12

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081680000000000 → 0x4081680000000008 |
| old/new hash | 0x162b6f7f23da2702 → 0x71a017c692b7077a |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081680000000000 / 0x4081680000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 120

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe7020c49ba5e35 → 0x3fe7020c49ba4e35 |
| old/new hash | 0x8a5df4cd6fee521d → 0x33b4c8b881e9a26d |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe7020c49ba5e35 / 0x3fe7020c49ba4e35 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 121

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4020000000000000 → 0x4020000000000010 |
| old/new hash | 0x47918d7eaf325983 → 0x373d7e0f5e262213 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4020000000000000 / 0x4020000000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 122

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff2c49ba5e353f8 → 0x3ff2c49ba5e35378 |
| old/new hash | 0xae1d5f767d3723a2 → 0xef68d33a01df4f22 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff2c49ba5e353f8 / 0x3ff2c49ba5e35378 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 123

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4064600000000000 → 0x4064600000000800 |
| old/new hash | 0x5e81857f4daf5007 → 0x3161292cbce65a6f |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4064600000000000 / 0x4064600000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 124

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4075700000000000 → 0x4075700000000800 |
| old/new hash | 0xe805ef7f9b455abe → 0xbdded32d0d032906 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4075700000000000 / 0x4075700000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 125

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd7ae147ae147ae → 0x3fd7ae147ae14fae |
| old/new hash | 0x0acd6b1bf992ab7f → 0x8dd75c0576552b87 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd7ae147ae147ae / 0x3fd7ae147ae14fae |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 126

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083800000000000 → 0x4083800000000800 |
| old/new hash | 0xf1831b7c3a1451a8 → 0x706abf2e93753f50 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083800000000000 / 0x4083800000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 127

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe2b020c49ba5e3 → 0x3fe2b020c49ba563 |
| old/new hash | 0x943a5b6f0ef09a33 → 0x5e54b3090ed7e9b3 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe2b020c49ba5e3 / 0x3fe2b020c49ba563 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 128

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff14bc6a7ef9db2 → 0x3ff14bc6a7efddb2 |
| old/new hash | 0x654397bd3a87ff0b → 0xc81c4a5cac69c14b |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff14bc6a7ef9db2 / 0x3ff14bc6a7efddb2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 129

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3f90624dd2f1a9ff → 0x3f90624dd2f1adff |
| old/new hash | 0x5995b43084d3c446 → 0x23aa2131c6bd191a |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3f90624dd2f1a9ff / 0x3f90624dd2f1adff |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 13

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088c00000000000 → 0x4088c00000000400 |
| old/new hash | 0x1f375d7d76e98f1b → 0xdff9aba44a66de17 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088c00000000000 / 0x4088c00000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 130

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408e000000000000 → 0x408e000000000008 |
| old/new hash | 0x499c697eb0ee26ad → 0x3e4301c705b38145 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408e000000000000 / 0x408e000000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 131

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408bb80000000000 → 0x408bb80000008000 |
| old/new hash | 0x21bb437bc46c6468 → 0x255e7e57c564cae8 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408bb80000000000 / 0x408bb80000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 132

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdbc6a7ef9db22d → 0x3fdbc6a7ef9db32d |
| old/new hash | 0x2cdf5e2d80215f7b → 0xe0c0e7cd4099e1fc |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdbc6a7ef9db22d / 0x3fdbc6a7ef9db32d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 133

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd3d70a3d70a3d7 → 0xbfd3d70a3d70b3d7 |
| old/new hash | 0x381b9fae4e63e10b → 0xae3b61e6a6c287bb |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd3d70a3d70a3d7 / 0xbfd3d70a3d70b3d7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 134

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408a900000000000 → 0x408a900000000008 |
| old/new hash | 0x7c03817c8880dfb9 → 0x741019c4e0296351 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408a900000000000 / 0x408a900000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 135

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080300000000000 → 0x4080300000000400 |
| old/new hash | 0xbbb39d7e5f9d3f73 → 0xd0fd0ba7a6ebb15f |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080300000000000 / 0x4080300000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 136

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407fc00000000000 → 0x407fc00000004000 |
| old/new hash | 0x1c77637d74930774 → 0x1e0c460f76fad6b4 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407fc00000000000 / 0x407fc00000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 137

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3febbe76c8b43958 → 0x3febbe76c8b42958 |
| old/new hash | 0xaae6edc5809b91f2 → 0x81d6d66445916382 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3febbe76c8b43958 / 0x3febbe76c8b42958 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 138

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feb0a3d70a3d70a → 0x3feb0a3d70a3d50a |
| old/new hash | 0x829a06134ebd3806 → 0xf2df5da791ecf9a4 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feb0a3d70a3d70a / 0x3feb0a3d70a3d50a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 139

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407b200000000000 → 0x407b200000008000 |
| old/new hash | 0x32732b7e1240f3f0 → 0x8935665528578670 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407b200000000000 / 0x407b200000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 14

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4047800000000000 → 0x4047800000020000 |
| old/new hash | 0xf41db37c3c4b168c → 0xe479831b4871c1be |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4047800000000000 / 0x4047800000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 140

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe5810624dd2f1b → 0x3fe5810624dd2d1b |
| old/new hash | 0xc545c2dd20cb33ed → 0xded2a73e3d7fe227 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe5810624dd2f1b / 0x3fe5810624dd2d1b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 141

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4076c00000000000 → 0x4076c00000008000 |
| old/new hash | 0x1c95f97d74ad03e5 → 0x1cd3345972c24165 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4076c00000000000 / 0x4076c00000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 142

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408eb00000000000 → 0x408eb00000002000 |
| old/new hash | 0x6a47397bee6ee67d → 0x3b8feac760069d1d |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408eb00000000000 / 0x408eb00000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 143

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff26e978d4fdf3b → 0x3ff26e978d4f9f3b |
| old/new hash | 0x540005daceceecbf → 0xb5a75f4fa1e21e7f |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff26e978d4fdf3b / 0x3ff26e978d4f9f3b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 144

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff795810624dd2f → 0x3ff795810624dd0f |
| old/new hash | 0xde35ab1c9f19a8e5 → 0x27a60c6001180f85 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff795810624dd2f / 0x3ff795810624dd0f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 145

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd570a3d70a3d71 → 0x3fd570a3d70a3d70 |
| old/new hash | 0x49c816e01db3e5e1 → 0x53dbffe21070e27c |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd570a3d70a3d71 / 0x3fd570a3d70a3d70 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 146

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfdb74bc6a7ef9db → 0xbfdb74bc6a7cf9db |
| old/new hash | 0x5a5e9eb54bb01629 → 0xabc850712cbb4b57 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfdb74bc6a7ef9db / 0xbfdb74bc6a7cf9db |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 147

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4082200000000000 → 0x4082200000000001 |
| old/new hash | 0x3115217e11178e71 → 0x3fde9a76430a3e90 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4082200000000000 / 0x4082200000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 148

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe60c49ba5e3540 → 0x3fe60c49ba5e3544 |
| old/new hash | 0x0c3c79ea53344876 → 0x9a66e58884865ae2 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe60c49ba5e3540 / 0x3fe60c49ba5e3544 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 149

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x406d200000000000 → 0x406d200000001000 |
| old/new hash | 0x32512f7e12241456 → 0x0787b6da2ee5b7e6 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x406d200000000000 / 0x406d200000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 15

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe25604189374bc → 0x3fe25604189354bc |
| old/new hash | 0x42560d5851642261 → 0x824f0efe7bf6f801 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe25604189374bc / 0x3fe25604189354bc |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 150

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407fb00000000000 → 0x407fb00000000080 |
| old/new hash | 0x6714337bebb70ce4 → 0x932baefb5c10a764 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407fb00000000000 / 0x407fb00000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 151

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407e700000000000 → 0x407e700000000200 |
| old/new hash | 0xe7e7597f9b2b5e4d → 0x4804c89304b0b357 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407e700000000000 / 0x407e700000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 152

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe449ba5e353f7d → 0x3fe449ba5e373f7d |
| old/new hash | 0xa624515460f4e0e4 → 0x5d4f89c2bb7d368e |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe449ba5e353f7d / 0x3fe449ba5e373f7d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 153

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd706b37867f0aa → 0x3fd706b37867f0ea |
| old/new hash | 0xa73a246d0aaef3f9 → 0x165027a05ae84139 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd706b37867f0aa / 0x3fd706b37867f0ea |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 154

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe48060780fdc17 → 0x3fe48060780f5c17 |
| old/new hash | 0xe834ff9de3ebfc62 → 0x92163a700f20bae2 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe48060780fdc17 / 0x3fe48060780f5c17 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 155

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff01f0f5a1016ce → 0x3ff01f0f5a1016de |
| old/new hash | 0x226bdf648d56f47e → 0x749d57ad96f8138e |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff01f0f5a1016ce / 0x3ff01f0f5a1016de |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 156

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdd6eb4e981387a → 0x3fdd6eb4e981387b |
| old/new hash | 0xd79a7a211f7748c1 → 0xe72506f417fc8c38 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdd6eb4e981387a / 0x3fdd6eb4e981387b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 157

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff21143bf727137 → 0x3ff21143bf737137 |
| old/new hash | 0x9b32e27671b5ab93 → 0x484c0b9e1a9ad366 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff21143bf727137 / 0x3ff21143bf737137 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 158

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe8949a5657fb6a → 0x3fe8949a5657fb6b |
| old/new hash | 0xaca7b724c18a95c6 → 0xfeb136982151f5eb |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe8949a5657fb6a / 0x3fe8949a5657fb6b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 159

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fefb38d60a63305 → 0x3fefb38d60a63385 |
| old/new hash | 0xbb7cefb070177e07 → 0x06f42fe1ebd42187 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fefb38d60a63305 / 0x3fefb38d60a63385 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 16

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4086f00000000000 → 0x4086f00000000001 |
| old/new hash | 0x94c1a97d28868405 → 0xf4e32277cb963a24 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4086f00000000000 / 0x4086f00000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 160

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff715b573eab368 → 0x3ff715b573eab768 |
| old/new hash | 0x19daf6cd36522775 → 0xc6db86e8b948d291 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff715b573eab368 / 0x3ff715b573eab768 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 161

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff983f2d3c792d1 → 0x3ff983f2d3c792d3 |
| old/new hash | 0xa51c42184a907259 → 0x5430e7fe2a08cb47 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff983f2d3c792d1 / 0x3ff983f2d3c792d3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 162

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ffb60d887ebf22c → 0x3ffb60d887ebf22d |
| old/new hash | 0x3de54bf1d3161d89 → 0xc3c37f61739482dc |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ffb60d887ebf22c / 0x3ffb60d887ebf22d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 163

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff4d20afa2f05a6 → 0x3ff4d20afa2d05a6 |
| old/new hash | 0x05e385d4a1dd7a0e → 0x0041f0858ff53290 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff4d20afa2f05a6 / 0x3ff4d20afa2d05a6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 164

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3cc55432873bd → 0x3ff3cc55432873b5 |
| old/new hash | 0x9d379bc1fe7ea389 → 0x5da0d28f9d854f51 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3cc55432873bd / 0x3ff3cc55432873b5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 165

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe2dc011d3671ac → 0x3fe2dc011d3471ac |
| old/new hash | 0x830826572a5adc37 → 0x47da1345d8c9c9d5 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe2dc011d3671ac / 0x3fe2dc011d3471ac |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 166

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd099e94ab1d4fa → 0x3fd099e94ab0d4fa |
| old/new hash | 0x55be9f7755ec177d → 0x3f53f6c9e4681cec |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd099e94ab1d4fa / 0x3fd099e94ab0d4fa |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 167

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe99ae0c1765777 → 0x3fe99ae0c1765737 |
| old/new hash | 0x2d54df22770707e2 → 0xbd82d7c4090c4922 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe99ae0c1765777 / 0x3fe99ae0c1765737 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 168

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdf358298cc1442 → 0x3fdf358298cc1446 |
| old/new hash | 0x4e98d5bb013b97c2 → 0x2efed2232b16098e |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdf358298cc1442 / 0x3fdf358298cc1446 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 169

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff07d1dcd7060bc → 0x3ff07d1dcd7060ac |
| old/new hash | 0xde236c65e7b9ace7 → 0x6f6668d5930f11b7 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff07d1dcd7060bc / 0x3ff07d1dcd7060ac |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 17

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4073600000000000 → 0x4073600000001000 |
| old/new hash | 0x5e9f9b7f4dc872f8 → 0x336a62db6a2f6468 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4073600000000000 / 0x4073600000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 170

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ffc8bda9435ac8a → 0x3ffc8bda9435acca |
| old/new hash | 0xb63073aeb0924dde → 0x73d7074deb8c6a1e |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ffc8bda9435ac8a / 0x3ffc8bda9435acca |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 171

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc48909289dadfd → 0x3fc48909289da9fd |
| old/new hash | 0xda8373c252bc9a2b → 0x3af93f6740c89ac7 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc48909289dadfd / 0x3fc48909289da9fd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 172

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fa138bcdfefbf3f → 0x3fa138bcdfedbf3f |
| old/new hash | 0x7ac37324b5e0ce2b → 0x628bc105a7fa83f1 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fa138bcdfefbf3f / 0x3fa138bcdfedbf3f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 173

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe0ef0ae536501e → 0x3fe0ef0ae536101e |
| old/new hash | 0xb708afe92e2d1ee6 → 0x61a0d23c09ec0226 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe0ef0ae536501e / 0x3fe0ef0ae536101e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 174

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe31ca9ef5232d3 → 0x3fe31ca9ef5272d3 |
| old/new hash | 0x27108b631285853e → 0x336ef1c2c5ca5afe |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe31ca9ef5232d3 / 0x3fe31ca9ef5272d3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 175

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc00ee06d938150 → 0xbfc00ee06d938158 |
| old/new hash | 0xd7e59f7ecad70807 → 0x1eeee09087a2bddf |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc00ee06d938150 / 0xbfc00ee06d938158 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 176

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe5ea400fba8825 → 0x3fe5ea400fba8835 |
| old/new hash | 0x452e9f026b936e07 → 0x3a3a1c1bf2174b17 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe5ea400fba8825 / 0x3fe5ea400fba8835 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 177

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdbc4a83b1d0c80 → 0x3fdbc4a83b1d1c80 |
| old/new hash | 0xa40e73b9456673fd → 0x75de0ae60cc6e60d |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdbc4a83b1d0c80 / 0x3fdbc4a83b1d1c80 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 178

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff5e14cec41dd1b → 0x3ff5e14cec41df1b |
| old/new hash | 0x44d3e7060d602c79 → 0x49746c4f0bffff23 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff5e14cec41dd1b / 0x3ff5e14cec41df1b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 179

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ffca253111f0c35 → 0x3ffca253111d0c35 |
| old/new hash | 0xa40034d501fd425e → 0x983ac9114792f064 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ffca253111f0c35 / 0x3ffca253111d0c35 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 18

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe25e353f7ced91 → 0x3fe25e353f7c6d91 |
| old/new hash | 0xcaede4d38f19a4ac → 0x7791a9fc7be63b2c |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe25e353f7ced91 / 0x3fe25e353f7c6d91 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 180

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe4603925bb7b6c → 0x3fe4603925bb6b6c |
| old/new hash | 0xff2a685134cfcf46 → 0x25d39df83578a716 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe4603925bb7b6c / 0x3fe4603925bb6b6c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 181

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdd8d2a1f8e3ac1 → 0x3fdd8d2a1f8f3ac1 |
| old/new hash | 0xa1864f44ee79f826 → 0x646a8d438bb063e3 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdd8d2a1f8e3ac1 / 0x3fdd8d2a1f8f3ac1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 182

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff47e90ff972474 → 0x3ff47e90ff976474 |
| old/new hash | 0x1a54012d878625ba → 0xc476ce80e237e9fa |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff47e90ff972474 / 0x3ff47e90ff976474 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 183

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe838b8ae31d713 → 0x3fe838b8ae31d71b |
| old/new hash | 0xdbc584a069f3dbff → 0xaaccc90ff7947cf7 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe838b8ae31d713 / 0x3fe838b8ae31d71b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 184

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe35696e58a32f4 → 0x3fe35696e58a22f4 |
| old/new hash | 0x524a3326f341702e → 0xd29abd8dd080babe |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe35696e58a32f4 / 0x3fe35696e58a22f4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 185

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff0db9628cbd124 → 0x3ff0db9628cbd524 |
| old/new hash | 0x61711b74e458f9f5 → 0x7a689fc3e2ddf0a9 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff0db9628cbd124 / 0x3ff0db9628cbd524 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 186

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe89e2de8709742 → 0x3fe89e2de8709743 |
| old/new hash | 0xd8c07c23c76de67e → 0x6417ebd9c21eb173 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe89e2de8709742 / 0x3fe89e2de8709743 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 187

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc366d7a56de331 → 0x3fc366d7a56de330 |
| old/new hash | 0x4cbedaaf6a33072e → 0xd99536fb9cca7a3f |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc366d7a56de331 / 0x3fc366d7a56de330 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 188

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fce6bf8769ec2d0 → 0x3fce6bf8769ec250 |
| old/new hash | 0x8c1a28920621034f → 0x56204d5d68e009cf |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fce6bf8769ec2d0 / 0x3fce6bf8769ec250 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 189

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fca12d77318fc53 → 0x3fca12d77318bc53 |
| old/new hash | 0x51bcfa9c0273c037 → 0x534743c6b6469177 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fca12d77318fc53 / 0x3fca12d77318bc53 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 19

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4062a00000000000 → 0x4062a00000000004 |
| old/new hash | 0xdd9de17b9e2d6851 → 0x03dcfda4b2a12c95 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4062a00000000000 / 0x4062a00000000004 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 190

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc3cd78c436fc17 → 0x3fc3cd78c436fc16 |
| old/new hash | 0x6ee7ae14b5c2e1d3 → 0x03d1ef96ee985e46 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc3cd78c436fc17 / 0x3fc3cd78c436fc16 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 191

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3bcf91a32b12e → 0x3ff3bcf91a32b02e |
| old/new hash | 0xcc3f88b899257875 → 0xa17b4efca9659072 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3bcf91a32b12e / 0x3ff3bcf91a32b02e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 192

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe07f737da61e0c → 0x3fe07f737da65e0c |
| old/new hash | 0x3954707fa7a7e10b → 0x378f7cd5334e804b |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe07f737da61e0c / 0x3fe07f737da65e0c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 193

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea1f3a57eaa2a1 → 0x3fea1f3a57ea22a1 |
| old/new hash | 0x0a7af604d2e01dd3 → 0x4d82ee1bb172ed53 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea1f3a57eaa2a1 / 0x3fea1f3a57ea22a1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 194

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd8ec41dd1a21ea → 0x3fd8ec41dd1a21ca |
| old/new hash | 0x4ccd8ed858d4c3b7 → 0xe90c104ca6fc4b57 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd8ec41dd1a21ea / 0x3fd8ec41dd1a21ca |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 195

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff786b59146e4c2 → 0x3ff786b59146a4c2 |
| old/new hash | 0x21917fc2c5e1bcc9 → 0xd2da7bb3c5a8b689 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff786b59146e4c2 / 0x3ff786b59146a4c2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 196

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff6ee84ad794a6f → 0x3ff6ee84ad794a2f |
| old/new hash | 0xafb57d638c3bfa79 → 0x4fb28f51fd52f239 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff6ee84ad794a6f / 0x3ff6ee84ad794a2f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 197

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef39f127f5e850 → 0x3fef39f127f5e858 |
| old/new hash | 0x7a72ba8c199f4287 → 0x16d9d0f5c5ad154f |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef39f127f5e850 / 0x3fef39f127f5e858 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 198

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feb2599ed7c6fbe → 0x3feb2599ed7c67be |
| old/new hash | 0x7a2000a028af08d3 → 0x21e6fabe03478fab |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feb2599ed7c6fbe / 0x3feb2599ed7c67be |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 199

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff499eb6390c910 → 0x3ff499eb6392c910 |
| old/new hash | 0x3dea88a2fc9359cc → 0x92911eb65d96ea5a |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff499eb6390c910 / 0x3ff499eb6392c910 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 2

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfda6e978d4fdf3b → 0xbfda6e978d4fdf1b |
| old/new hash | 0x545185dacf141d67 → 0xfadf618aeccae5c7 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfda6e978d4fdf3b / 0xbfda6e978d4fdf1b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 20

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc0a3d70a3d70a4 → 0xbfc0a3d70a3c70a4 |
| old/new hash | 0x4304f33f010ce7ef → 0xe254a9299dc568ca |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc0a3d70a3d70a4 / 0xbfc0a3d70a3c70a4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 200

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fed5ad96a6a0125 → 0x3fed5ad96a6a0124 |
| old/new hash | 0xd1f1bc19458c2e22 → 0xa474d85e294cc147 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fed5ad96a6a0125 / 0x3fed5ad96a6a0124 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 201

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd7bd9cae21101c → 0x3fd7bd9cae21141c |
| old/new hash | 0xbea495198a3d83c5 → 0x8ac12bf6d90e83d1 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd7bd9cae21101c / 0x3fd7bd9cae21141c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 202

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff31e6eeb702602 → 0x3ff31e6eeb702606 |
| old/new hash | 0xbbc349ca80040838 → 0xa39d651ee5f9e7dc |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff31e6eeb702602 / 0x3ff31e6eeb702606 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 203

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe39b4784230fcf → 0x3fe39b4784231fcf |
| old/new hash | 0x286e3fe771cdc02a → 0x19a4b465c3806eda |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe39b4784230fcf / 0x3fe39b4784231fcf |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 204

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fedd7c6fbd273d7 → 0x3fedd7c6fbd272d7 |
| old/new hash | 0x2323c09b74d39231 → 0x3a5f87793e109182 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fedd7c6fbd273d7 / 0x3fedd7c6fbd272d7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 205

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff2997b30f8c650 → 0x3ff2997b30f8c652 |
| old/new hash | 0x24aa8a2fd2f11fb2 → 0xf94f281a89483878 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff2997b30f8c650 / 0x3ff2997b30f8c652 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 206

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff4793dd97f62b7 → 0x3ff4793dd97fe2b7 |
| old/new hash | 0x343728c920d8ed15 → 0x8fbe186f5d0fe695 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff4793dd97f62b7 / 0x3ff4793dd97fe2b7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 21

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe89ba5e353f7cf → 0x3fe89ba5e353f78f |
| old/new hash | 0x19e517111a9a58d6 → 0x0d9ee0efd2d48096 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe89ba5e353f7cf / 0x3fe89ba5e353f78f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 22

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080000000000000 → 0x4080000000008000 |
| old/new hash | 0x49b14d7eb1005323 → 0x9d0d8855c433bca3 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080000000000000 / 0x4080000000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 23

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd09374bc6a7efa → 0x3fd09374bc6a7ffa |
| old/new hash | 0xf0fa067fedee8e41 → 0x42be5a2de759c67a |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd09374bc6a7efa / 0x3fd09374bc6a7ffa |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 24

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081800000000000 → 0x4081800000010000 |
| old/new hash | 0xf189e77c3a1a17fa → 0x18604f494f114113 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081800000000000 / 0x4081800000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 25

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff10624dd2f1aa0 → 0x3ff10624dd2f9aa0 |
| old/new hash | 0xb8c63b9a0345a097 → 0xafbad6459ae18217 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff10624dd2f1aa0 / 0x3ff10624dd2f9aa0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 26

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4072300000000000 → 0x4072300000000001 |
| old/new hash | 0xbbe2b17e5fc4d231 → 0xca3fea76915bf6b0 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4072300000000000 / 0x4072300000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 27

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfa4fdf3b645a1c9 → 0xbfa4fdf3b644a1c9 |
| old/new hash | 0xd6dc1d34303c69e7 → 0x98f413a75d931b7e |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfa4fdf3b645a1c9 / 0xbfa4fdf3b644a1c9 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 28

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe78d4fdf3b645a → 0x3fe78d4fdf3b655a |
| old/new hash | 0xf96a7234a4b47425 → 0x704d849f79d38ac2 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe78d4fdf3b645a / 0x3fe78d4fdf3b655a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 29

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd1374bc6a7ef9e → 0x3fd1374bc6a5ef9e |
| old/new hash | 0xbfce6df848f2d613 → 0x167551dae70da131 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd1374bc6a7ef9e / 0x3fd1374bc6a5ef9e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 3

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4075300000000000 → 0x4075300000000001 |
| old/new hash | 0xbbf3af7e5fd341fe → 0xca5834769171064f |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4075300000000000 / 0x4075300000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 30

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe34395810624dd → 0x3fe34395810624cd |
| old/new hash | 0xa4a3dee8dc722599 → 0x6c4712068393b9c9 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe34395810624dd / 0x3fe34395810624cd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 31

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087880000000000 → 0x4087880000004000 |
| old/new hash | 0xafaadb7c15c311f4 → 0x00e43e1087d57934 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087880000000000 / 0x4087880000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 32

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff17ced916872b0 → 0x3ff17ced916872b4 |
| old/new hash | 0x11c609e36698272f → 0x49769f6e01e10dab |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff17ced916872b0 / 0x3ff17ced916872b4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 33

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdc395810624dd3 → 0x3fdc39581062cdd3 |
| old/new hash | 0xf02fa294889ab42f → 0x438bdd6b9bce1daf |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdc395810624dd3 / 0x3fdc39581062cdd3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 34

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4063200000000000 → 0x4063200000008000 |
| old/new hash | 0x32577b7e12290128 → 0x8919b655283f93a8 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4063200000000000 / 0x4063200000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 35

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfa26e978d4fdf3a → 0xbfa26e978d4fdfba |
| old/new hash | 0x602b680f7efcce06 → 0xe3562664ab791286 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfa26e978d4fdf3a / 0xbfa26e978d4fdfba |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 36

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4060a00000000000 → 0x4060a00000008000 |
| old/new hash | 0xdda4ad7b9e332ea3 → 0xdde1e8579c486c23 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4060a00000000000 / 0x4060a00000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 37

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4035000000000000 → 0x4035000000020000 |
| old/new hash | 0x47d19f7eaf685c0e → 0x8f7e5718d43d99dc |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4035000000000000 / 0x4035000000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 38

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x404b800000000000 → 0x404b800000000040 |
| old/new hash | 0xf3f4eb7c3c2870a0 → 0x5a6e2dc3de8735e0 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x404b800000000000 / 0x404b800000000040 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 39

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408ba00000000000 → 0x408ba00000000004 |
| old/new hash | 0xdf9e8b7b9fe08c00 → 0x050527a4b39d3904 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408ba00000000000 / 0x408ba00000000004 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 4

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088200000000000 → 0x4088200000004000 |
| old/new hash | 0x31003d7e110561fb → 0x859fa01285faf23b |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088200000000000 / 0x4088200000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 40

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087d00000000000 → 0x4087d00000000004 |
| old/new hash | 0xa687a37dc2a04d3c → 0xba08afa63c278198 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087d00000000000 / 0x4087d00000000004 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 41

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4062c00000000000 → 0x4062c00000008000 |
| old/new hash | 0x1c52017d747344b1 → 0x1c8f3c5972888231 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4062c00000000000 / 0x4062c00000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 42

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4034000000000000 → 0x4034000000000020 |
| old/new hash | 0x47d5857eaf6c18b7 → 0x280766a00e0d4d97 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4034000000000000 / 0x4034000000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 43

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408ab00000000000 → 0x408ab00000000020 |
| old/new hash | 0x6a3a217bee643359 → 0x1d6cc2a36e4bcd39 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408ab00000000000 / 0x408ab00000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 44

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff14fdf3b645a1d → 0x3ff14fdf3b645a3d |
| old/new hash | 0xe305aa375356626b → 0xb483a2be4322e38b |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff14fdf3b645a1d / 0x3ff14fdf3b645a3d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 45

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3e353f7ced917 → 0x3ff3e353f7cedb17 |
| old/new hash | 0xf5175acf006e25fc → 0x1cbfe4ecf4620072 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3e353f7ced917 / 0x3ff3e353f7cedb17 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 46

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4061000000000000 → 0x4061000000008000 |
| old/new hash | 0x4867a77eafe8409a → 0x9f29e255c5fed31a |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4061000000000000 / 0x4061000000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 47

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fee978d4fdf3b64 → 0x3fee978d4fdf3b65 |
| old/new hash | 0xa3eb809a6e0d833f → 0x64ba2de99a932da6 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fee978d4fdf3b64 / 0x3fee978d4fdf3b65 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 48

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff49374bc6a7efa → 0x3ff49374bc6afefa |
| old/new hash | 0xf07f867fed865885 → 0x4943ebcf68257a05 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff49374bc6a7efa / 0x3ff49374bc6afefa |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 49

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4089e00000000000 → 0x4089e00000000800 |
| old/new hash | 0x0a04177cd9e5fd12 → 0x85bb9b2f30911aca |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4089e00000000000 / 0x4089e00000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 5

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4031000000000000 → 0x4031000000000080 |
| old/new hash | 0x47c4877eaf5da8ea → 0xca6102f937b8986a |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4031000000000000 / 0x4031000000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 50

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4072b00000000000 → 0x4072b00000000010 |
| old/new hash | 0x6725317bebc57cb1 → 0x6c6dc20d38165941 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4072b00000000000 / 0x4072b00000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 51

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fde45a1cac08313 → 0x3fde45a1cac09313 |
| old/new hash | 0x29243d7b4ad46b7e → 0x6c1ac4903f88318e |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fde45a1cac08313 / 0x3fde45a1cac09313 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 52

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe50e5604189375 → 0x3fe50e560418937d |
| old/new hash | 0x5b9422757fd15043 → 0x144d201e52871ebb |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe50e5604189375 / 0x3fe50e560418937d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 53

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfddd2f1a9fbe76d → 0xbfddd2f1a9fbe77d |
| old/new hash | 0x74b947ac61424f88 → 0x86cad875a21edff8 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfddd2f1a9fbe76d / 0xbfddd2f1a9fbe77d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 54

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff004189374bc6b → 0x3ff004189374bc2b |
| old/new hash | 0x44077c53d10b2088 → 0x1ff1a90abd3fbd48 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff004189374bc6b / 0x3ff004189374bc2b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 55

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe526e978d4fdf4 → 0x3fe526e978d4fff4 |
| old/new hash | 0x215b2335d51a5287 → 0x62aee0d4cc9d922d |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe526e978d4fdf4 / 0x3fe526e978d4fff4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 56

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083800000000000 → 0x4083800000000080 |
| old/new hash | 0xf1831b7c3a1451a8 → 0x210096fbad511528 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083800000000000 / 0x4083800000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 57

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4085880000000000 → 0x4085880000000020 |
| old/new hash | 0xafb1a77c15c8d846 → 0x388588a25bb0c766 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4085880000000000 / 0x4085880000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 58

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407dd00000000000 → 0x407dd00000000100 |
| old/new hash | 0xa9359f7dc4e6b216 → 0x76828ff7bca5e6ad |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407dd00000000000 / 0x407dd00000000100 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 59

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081900000000000 → 0x4081900000000008 |
| old/new hash | 0x7c21977c889a02aa → 0x73f7cfc4e01453b2 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081900000000000 / 0x4081900000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 6

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea8f5c28f5c28f → 0x3fea8f5c28f5c28d |
| old/new hash | 0xdf7b8e7b72b2887d → 0xd193c3359585a4cf |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea8f5c28f5c28f / 0x3fea8f5c28f5c28d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 60

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4086300000000000 → 0x4086300000001000 |
| old/new hash | 0xbbb9e97e5fa22c45 → 0x7f2790d9e247fcf5 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4086300000000000 / 0x4086300000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 61

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4069000000000000 → 0x4069000000000010 |
| old/new hash | 0x484c777eafd12752 → 0x37f8680f5ec4efe2 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4069000000000000 / 0x4069000000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 62

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe3645a1cac0831 → 0x3fe3645a1cac08b1 |
| old/new hash | 0xeb70a866734935c6 → 0xd442f0f306fac346 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe3645a1cac0831 / 0x3fe3645a1cac08b1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 63

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe5810624dd2f1b → 0x3fe5810624dd2f13 |
| old/new hash | 0xc545c2dd20cb33ed → 0x012c0d768f99b215 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe5810624dd2f1b / 0x3fe5810624dd2f13 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 64

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe0f5c28f5c28f6 → 0x3fe0f5c28f5c68f6 |
| old/new hash | 0xb8b0376c5f2409e8 → 0x6ca5bf8e819b6928 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe0f5c28f5c28f6 / 0x3fe0f5c28f5c68f6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 65

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe589374bc6a7f0 → 0x3fe589374bc6a7f8 |
| old/new hash | 0x4c1c16fa041128dd → 0x5b427d19be0b93d5 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe589374bc6a7f0 / 0x3fe589374bc6a7f8 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 66

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea8f5c28f5c28f → 0x3fea8f5c28f5c287 |
| old/new hash | 0xdf7b8e7b72b2887d → 0xf4cbf2ac97342145 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea8f5c28f5c28f / 0x3fea8f5c28f5c287 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 67

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd3126e978d4fdf → 0x3fd3126e978d4f5f |
| old/new hash | 0x905e562ea0397617 → 0x566f381f5bf24b97 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd3126e978d4fdf / 0x3fd3126e978d4f5f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 68

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081c80000000000 → 0x4081c80000000020 |
| old/new hash | 0xd69ccf7d4cd9cd62 → 0x5f7130a392c29602 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081c80000000000 / 0x4081c80000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 69

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407b700000000000 → 0x407b700000000400 |
| old/new hash | 0xe7d5db7f9b1c1500 → 0xa82be9a66e3dd85c |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407b700000000000 / 0x407b700000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 7

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff1b645a1cac083 → 0x3ff1b645a1cac883 |
| old/new hash | 0xcad61c3025201eda → 0x8f85b284360d0232 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff1b645a1cac083 / 0x3ff1b645a1cac883 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 70

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4028000000000000 → 0x4028000000010000 |
| old/new hash | 0x47765d7eaf1b403b → 0x6bb8f94bc1e16ac2 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4028000000000000 / 0x4028000000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 71

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088d80000000000 → 0x4088d80000002000 |
| old/new hash | 0x64b9957d9e57b703 → 0xb6e506c561eeba63 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088d80000000000 / 0x4088d80000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 72

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfdd916872b020c5 → 0xbfdd916872b028c5 |
| old/new hash | 0x6c207f97e78d6407 → 0xc31ba4aa26077e6f |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfdd916872b020c5 / 0xbfdd916872b028c5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 73

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff7cac083126e98 → 0x3ff7cac083126e9c |
| old/new hash | 0xfbed883d375b1bda → 0x23ddc0be05e9b806 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff7cac083126e98 / 0x3ff7cac083126e9c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 74

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408a180000000000 → 0x408a180000000100 |
| old/new hash | 0x8bab897ed56e7271 → 0xb49cc5f3e988a65a |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408a180000000000 / 0x408a180000000100 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 75

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x406bc00000000000 → 0x406bc00000010000 |
| old/new hash | 0x1c33eb7d745a21c0 → 0xebbfd3481326bd19 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x406bc00000000000 / 0x406bc00000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 76

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4084b00000000000 → 0x4084b00000001000 |
| old/new hash | 0x6a69357bee8bc617 → 0x270adcd76b6b44c7 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4084b00000000000 / 0x4084b00000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 77

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4075700000000000 → 0x4075700000000800 |
| old/new hash | 0xe805ef7f9b455abe → 0xbdded32d0d032906 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4075700000000000 / 0x4075700000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 78

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff624dd2f1a9fbf → 0x3ff624dd2f1a9fb7 |
| old/new hash | 0x091eea40c770d9e0 → 0x7b0f09fcb6c3bf88 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff624dd2f1a9fbf / 0x3ff624dd2f1a9fb7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 79

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408b980000000000 → 0x408b980000020000 |
| old/new hash | 0x3a50237c644e8948 → 0x9cae431b1f1220ca |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408b980000000000 / 0x408b980000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 8

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4051400000000000 → 0x4051400000000020 |
| old/new hash | 0x71b6877fe900ee8a → 0x52c1e8a1485aedaa |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4051400000000000 / 0x4051400000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 80

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087680000000000 → 0x4087680000010000 |
| old/new hash | 0x16323b7f23dfed54 → 0xe4e52349c1f497ed |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087680000000000 / 0x4087680000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 81

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe2d0e560418937 → 0x3fe2d0e56041893f |
| old/new hash | 0x4066ea6fa06ac484 → 0xb0d460532131e6cc |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe2d0e560418937 / 0x3fe2d0e56041893f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 82

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd21cac083126ea → 0x3fd21cac083126eb |
| old/new hash | 0x835c8e6a8628bc51 → 0xfa315d368ce9b1ec |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd21cac083126ea / 0x3fd21cac083126eb |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 83

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fed374bc6a7ef9e → 0x3fed374bc6a7ee9e |
| old/new hash | 0xbf8a6df848b90947 → 0x1e71e015d18ad6f8 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fed374bc6a7ef9e / 0x3fed374bc6a7ee9e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 84

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3febae147ae147ae → 0x3febae147ae145ae |
| old/new hash | 0x0adb6b1bf99ee8db → 0x0b4feb170c450179 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3febae147ae147ae / 0x3febae147ae145ae |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 85

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe35c28f5c28f5c → 0x3fe35c28f5c28f5e |
| old/new hash | 0x063ab92512627b81 → 0xfbc580ec67847967 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe35c28f5c28f5c / 0x3fe35c28f5c28f5e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 86

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4076a00000000000 → 0x4076a00000000040 |
| old/new hash | 0xdde1d97b9e672785 → 0x47c11bc343a915c5 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4076a00000000000 / 0x4076a00000000040 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 87

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdfced916872b02 → 0x3fdfced916872b82 |
| old/new hash | 0xdfeb19b89b1dc8c8 → 0xa454bfcfc49de248 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdfced916872b02 / 0x3fdfced916872b82 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 88

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd3d70a3d70a3d7 → 0x3fd3d70a3d7083d7 |
| old/new hash | 0x381c1fae4e64ba8b → 0x85c713199975232b |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd3d70a3d70a3d7 / 0x3fd3d70a3d7083d7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 89

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfb9db22d0e56041 → 0xbfb9db22d0e46041 |
| old/new hash | 0x201c3cfe05a97058 → 0x67dff4ddbd52d271 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfb9db22d0e56041 / 0xbfb9db22d0e46041 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 9

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4070400000000000 → 0x4070400000020000 |
| old/new hash | 0x714cad7fe8a69313 → 0x643be517997c7b61 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4070400000000000 / 0x4070400000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 90

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407b100000000000 → 0x407b100000008000 |
| old/new hash | 0xd1ccfb7efd637560 → 0x288f3656137a07e0 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407b100000000000 / 0x407b100000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 91

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x404e800000000000 → 0x404e800000004000 |
| old/new hash | 0xf405e97c3c36e06d → 0x46f14c10afb9292d |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x404e800000000000 / 0x404e800000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 92

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4089c80000000000 → 0x4089c80000000010 |
| old/new hash | 0xd6b7ff7d4cf0e6aa → 0x71a7700b87e70cba |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4089c80000000000 / 0x4089c80000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 93

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4059000000000000 → 0x4059000000000002 |
| old/new hash | 0x48ef977eb05bbf02 → 0x0a8d496c9a20c5a0 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4059000000000000 / 0x4059000000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 94

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4020000000000000 → 0x4020000000008000 |
| old/new hash | 0x47918d7eaf325983 → 0x9e53c855c548ec03 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4020000000000000 / 0x4020000000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 95

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef1a9fbe76c8b4 → 0x3fef1a9fbe76cab4 |
| old/new hash | 0x1516f78ceb5c87ac → 0x6a0c230da07466ca |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef1a9fbe76c8b4 / 0x3fef1a9fbe76cab4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 96

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd49ba5e353f7cf → 0xbfd49ba5e353f7ce |
| old/new hash | 0x19f217111aa4e332 → 0xde017cacb1fc7fe3 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd49ba5e353f7cf / 0xbfd49ba5e353f7ce |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 97

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4084280000000000 → 0x4084280000000200 |
| old/new hash | 0xef432d7deccb3b8f → 0xa0e16493c7903c85 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4084280000000000 / 0x4084280000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 98

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdcfdf3b645a1cb → 0x3fdcfdf3b645a9cb |
| old/new hash | 0xb197c88209e68289 → 0x14d9bcf038907261 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdcfdf3b645a1cb / 0x3fdcfdf3b645a9cb |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 99

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd3851eb851eb85 → 0x3fd3851eb851eb81 |
| old/new hash | 0x3c94928a21b4a60d → 0x59e3b2ffdb1db661 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd3851eb851eb85 / 0x3fd3851eb851eb81 |
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
| 7 | chain_end | — | 1236 | 5 |

### fault 10（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 54 | — |
| 2 | carrier_state | L1 | 55 | 54 |
| 3 | operand_read | L2 | 56 | 55 |
| 4 | execute | L3 | 57 | 56 |
| 5 | prf_writeback | L4 | 58 | 57 |
| 6 | commit | L5 | 59 | 58 |
| 7 | chain_end | — | 1245 | 59 |

### fault 100（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 594 | — |
| 2 | carrier_state | L1 | 595 | 594 |
| 3 | operand_read | L2 | 596 | 595 |
| 4 | execute | L3 | 597 | 596 |
| 5 | prf_writeback | L4 | 598 | 597 |
| 6 | commit | L5 | 599 | 598 |
| 7 | chain_end | — | 1335 | 599 |

### fault 101（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 600 | — |
| 2 | carrier_state | L1 | 601 | 600 |
| 3 | operand_read | L2 | 602 | 601 |
| 4 | execute | L3 | 603 | 602 |
| 5 | prf_writeback | L4 | 604 | 603 |
| 6 | commit | L5 | 605 | 604 |
| 7 | chain_end | — | 1336 | 605 |

### fault 102（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 606 | — |
| 2 | carrier_state | L1 | 607 | 606 |
| 3 | operand_read | L2 | 608 | 607 |
| 4 | execute | L3 | 609 | 608 |
| 5 | prf_writeback | L4 | 610 | 609 |
| 6 | commit | L5 | 611 | 610 |
| 7 | chain_end | — | 1337 | 611 |

### fault 103（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 612 | — |
| 2 | carrier_state | L1 | 613 | 612 |
| 3 | operand_read | L2 | 614 | 613 |
| 4 | execute | L3 | 615 | 614 |
| 5 | prf_writeback | L4 | 616 | 615 |
| 6 | commit | L5 | 617 | 616 |
| 7 | chain_end | — | 1338 | 617 |

### fault 104（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 618 | — |
| 2 | carrier_state | L1 | 619 | 618 |
| 3 | operand_read | L2 | 620 | 619 |
| 4 | execute | L3 | 621 | 620 |
| 5 | prf_writeback | L4 | 622 | 621 |
| 6 | commit | L5 | 623 | 622 |
| 7 | chain_end | — | 1339 | 623 |

### fault 105（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 624 | — |
| 2 | carrier_state | L1 | 625 | 624 |
| 3 | operand_read | L2 | 626 | 625 |
| 4 | execute | L3 | 627 | 626 |
| 5 | prf_writeback | L4 | 628 | 627 |
| 6 | commit | L5 | 629 | 628 |
| 7 | chain_end | — | 1340 | 629 |

### fault 106（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 630 | — |
| 2 | carrier_state | L1 | 631 | 630 |
| 3 | operand_read | L2 | 632 | 631 |
| 4 | execute | L3 | 633 | 632 |
| 5 | prf_writeback | L4 | 634 | 633 |
| 6 | commit | L5 | 635 | 634 |
| 7 | chain_end | — | 1341 | 635 |

### fault 107（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 636 | — |
| 2 | carrier_state | L1 | 637 | 636 |
| 3 | operand_read | L2 | 638 | 637 |
| 4 | execute | L3 | 639 | 638 |
| 5 | prf_writeback | L4 | 640 | 639 |
| 6 | commit | L5 | 641 | 640 |
| 7 | chain_end | — | 1342 | 641 |

### fault 108（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 642 | — |
| 2 | carrier_state | L1 | 643 | 642 |
| 3 | operand_read | L2 | 644 | 643 |
| 4 | execute | L3 | 645 | 644 |
| 5 | prf_writeback | L4 | 646 | 645 |
| 6 | commit | L5 | 647 | 646 |
| 7 | chain_end | — | 1343 | 647 |

### fault 109（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 648 | — |
| 2 | carrier_state | L1 | 649 | 648 |
| 3 | operand_read | L2 | 650 | 649 |
| 4 | execute | L3 | 651 | 650 |
| 5 | prf_writeback | L4 | 652 | 651 |
| 6 | commit | L5 | 653 | 652 |
| 7 | chain_end | — | 1344 | 653 |

### fault 11（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 60 | — |
| 2 | carrier_state | L1 | 61 | 60 |
| 3 | operand_read | L2 | 62 | 61 |
| 4 | execute | L3 | 63 | 62 |
| 5 | prf_writeback | L4 | 64 | 63 |
| 6 | commit | L5 | 65 | 64 |
| 7 | chain_end | — | 1246 | 65 |

### fault 110（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 654 | — |
| 2 | carrier_state | L1 | 655 | 654 |
| 3 | operand_read | L2 | 656 | 655 |
| 4 | execute | L3 | 657 | 656 |
| 5 | prf_writeback | L4 | 658 | 657 |
| 6 | commit | L5 | 659 | 658 |
| 7 | chain_end | — | 1345 | 659 |

### fault 111（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 660 | — |
| 2 | carrier_state | L1 | 661 | 660 |
| 3 | operand_read | L2 | 662 | 661 |
| 4 | execute | L3 | 663 | 662 |
| 5 | prf_writeback | L4 | 664 | 663 |
| 6 | commit | L5 | 665 | 664 |
| 7 | chain_end | — | 1346 | 665 |

### fault 112（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 666 | — |
| 2 | carrier_state | L1 | 667 | 666 |
| 3 | operand_read | L2 | 668 | 667 |
| 4 | execute | L3 | 669 | 668 |
| 5 | prf_writeback | L4 | 670 | 669 |
| 6 | commit | L5 | 671 | 670 |
| 7 | chain_end | — | 1347 | 671 |

### fault 113（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 672 | — |
| 2 | carrier_state | L1 | 673 | 672 |
| 3 | operand_read | L2 | 674 | 673 |
| 4 | execute | L3 | 675 | 674 |
| 5 | prf_writeback | L4 | 676 | 675 |
| 6 | commit | L5 | 677 | 676 |
| 7 | chain_end | — | 1348 | 677 |

### fault 114（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 678 | — |
| 2 | carrier_state | L1 | 679 | 678 |
| 3 | operand_read | L2 | 680 | 679 |
| 4 | execute | L3 | 681 | 680 |
| 5 | prf_writeback | L4 | 682 | 681 |
| 6 | commit | L5 | 683 | 682 |
| 7 | chain_end | — | 1349 | 683 |

### fault 115（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 684 | — |
| 2 | carrier_state | L1 | 685 | 684 |
| 3 | operand_read | L2 | 686 | 685 |
| 4 | execute | L3 | 687 | 686 |
| 5 | prf_writeback | L4 | 688 | 687 |
| 6 | commit | L5 | 689 | 688 |
| 7 | chain_end | — | 1350 | 689 |

### fault 116（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 690 | — |
| 2 | carrier_state | L1 | 691 | 690 |
| 3 | operand_read | L2 | 692 | 691 |
| 4 | execute | L3 | 693 | 692 |
| 5 | prf_writeback | L4 | 694 | 693 |
| 6 | commit | L5 | 695 | 694 |
| 7 | chain_end | — | 1351 | 695 |

### fault 117（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 696 | — |
| 2 | carrier_state | L1 | 697 | 696 |
| 3 | operand_read | L2 | 698 | 697 |
| 4 | execute | L3 | 699 | 698 |
| 5 | prf_writeback | L4 | 700 | 699 |
| 6 | commit | L5 | 701 | 700 |
| 7 | chain_end | — | 1352 | 701 |

### fault 118（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 702 | — |
| 2 | carrier_state | L1 | 703 | 702 |
| 3 | operand_read | L2 | 704 | 703 |
| 4 | execute | L3 | 705 | 704 |
| 5 | prf_writeback | L4 | 706 | 705 |
| 6 | commit | L5 | 707 | 706 |
| 7 | chain_end | — | 1353 | 707 |

### fault 119（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 708 | — |
| 2 | carrier_state | L1 | 709 | 708 |
| 3 | operand_read | L2 | 710 | 709 |
| 4 | execute | L3 | 711 | 710 |
| 5 | prf_writeback | L4 | 712 | 711 |
| 6 | commit | L5 | 713 | 712 |
| 7 | chain_end | — | 1354 | 713 |

### fault 12（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 66 | — |
| 2 | carrier_state | L1 | 67 | 66 |
| 3 | operand_read | L2 | 68 | 67 |
| 4 | execute | L3 | 69 | 68 |
| 5 | prf_writeback | L4 | 70 | 69 |
| 6 | commit | L5 | 71 | 70 |
| 7 | chain_end | — | 1247 | 71 |

### fault 120（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 714 | — |
| 2 | carrier_state | L1 | 715 | 714 |
| 3 | operand_read | L2 | 716 | 715 |
| 4 | execute | L3 | 717 | 716 |
| 5 | prf_writeback | L4 | 718 | 717 |
| 6 | commit | L5 | 719 | 718 |
| 7 | chain_end | — | 1355 | 719 |

### fault 121（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 720 | — |
| 2 | carrier_state | L1 | 721 | 720 |
| 3 | operand_read | L2 | 722 | 721 |
| 4 | execute | L3 | 723 | 722 |
| 5 | prf_writeback | L4 | 724 | 723 |
| 6 | commit | L5 | 725 | 724 |
| 7 | chain_end | — | 1356 | 725 |

### fault 122（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 726 | — |
| 2 | carrier_state | L1 | 727 | 726 |
| 3 | operand_read | L2 | 728 | 727 |
| 4 | execute | L3 | 729 | 728 |
| 5 | prf_writeback | L4 | 730 | 729 |
| 6 | commit | L5 | 731 | 730 |
| 7 | chain_end | — | 1357 | 731 |

### fault 123（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 732 | — |
| 2 | carrier_state | L1 | 733 | 732 |
| 3 | operand_read | L2 | 734 | 733 |
| 4 | execute | L3 | 735 | 734 |
| 5 | prf_writeback | L4 | 736 | 735 |
| 6 | commit | L5 | 737 | 736 |
| 7 | chain_end | — | 1358 | 737 |

### fault 124（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 738 | — |
| 2 | carrier_state | L1 | 739 | 738 |
| 3 | operand_read | L2 | 740 | 739 |
| 4 | execute | L3 | 741 | 740 |
| 5 | prf_writeback | L4 | 742 | 741 |
| 6 | commit | L5 | 743 | 742 |
| 7 | chain_end | — | 1359 | 743 |

### fault 125（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 744 | — |
| 2 | carrier_state | L1 | 745 | 744 |
| 3 | operand_read | L2 | 746 | 745 |
| 4 | execute | L3 | 747 | 746 |
| 5 | prf_writeback | L4 | 748 | 747 |
| 6 | commit | L5 | 749 | 748 |
| 7 | chain_end | — | 1360 | 749 |

### fault 126（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 750 | — |
| 2 | carrier_state | L1 | 751 | 750 |
| 3 | operand_read | L2 | 752 | 751 |
| 4 | execute | L3 | 753 | 752 |
| 5 | prf_writeback | L4 | 754 | 753 |
| 6 | commit | L5 | 755 | 754 |
| 7 | chain_end | — | 1361 | 755 |

### fault 127（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 756 | — |
| 2 | carrier_state | L1 | 757 | 756 |
| 3 | operand_read | L2 | 758 | 757 |
| 4 | execute | L3 | 759 | 758 |
| 5 | prf_writeback | L4 | 760 | 759 |
| 6 | commit | L5 | 761 | 760 |
| 7 | chain_end | — | 1362 | 761 |

### fault 128（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 762 | — |
| 2 | carrier_state | L1 | 763 | 762 |
| 3 | operand_read | L2 | 764 | 763 |
| 4 | execute | L3 | 765 | 764 |
| 5 | prf_writeback | L4 | 766 | 765 |
| 6 | commit | L5 | 767 | 766 |
| 7 | chain_end | — | 1363 | 767 |

### fault 129（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 768 | — |
| 2 | carrier_state | L1 | 769 | 768 |
| 3 | operand_read | L2 | 770 | 769 |
| 4 | execute | L3 | 771 | 770 |
| 5 | prf_writeback | L4 | 772 | 771 |
| 6 | commit | L5 | 773 | 772 |
| 7 | chain_end | — | 1364 | 773 |

### fault 13（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 72 | — |
| 2 | carrier_state | L1 | 73 | 72 |
| 3 | operand_read | L2 | 74 | 73 |
| 4 | execute | L3 | 75 | 74 |
| 5 | prf_writeback | L4 | 76 | 75 |
| 6 | commit | L5 | 77 | 76 |
| 7 | chain_end | — | 1248 | 77 |

### fault 130（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 774 | — |
| 2 | carrier_state | L1 | 775 | 774 |
| 3 | operand_read | L2 | 776 | 775 |
| 4 | execute | L3 | 777 | 776 |
| 5 | prf_writeback | L4 | 778 | 777 |
| 6 | commit | L5 | 779 | 778 |
| 7 | chain_end | — | 1365 | 779 |

### fault 131（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 780 | — |
| 2 | carrier_state | L1 | 781 | 780 |
| 3 | operand_read | L2 | 782 | 781 |
| 4 | execute | L3 | 783 | 782 |
| 5 | prf_writeback | L4 | 784 | 783 |
| 6 | commit | L5 | 785 | 784 |
| 7 | chain_end | — | 1366 | 785 |

### fault 132（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 786 | — |
| 2 | carrier_state | L1 | 787 | 786 |
| 3 | operand_read | L2 | 788 | 787 |
| 4 | execute | L3 | 789 | 788 |
| 5 | prf_writeback | L4 | 790 | 789 |
| 6 | commit | L5 | 791 | 790 |
| 7 | chain_end | — | 1367 | 791 |

### fault 133（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 792 | — |
| 2 | carrier_state | L1 | 793 | 792 |
| 3 | operand_read | L2 | 794 | 793 |
| 4 | execute | L3 | 795 | 794 |
| 5 | prf_writeback | L4 | 796 | 795 |
| 6 | commit | L5 | 797 | 796 |
| 7 | chain_end | — | 1368 | 797 |

### fault 134（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 798 | — |
| 2 | carrier_state | L1 | 799 | 798 |
| 3 | operand_read | L2 | 800 | 799 |
| 4 | execute | L3 | 801 | 800 |
| 5 | prf_writeback | L4 | 802 | 801 |
| 6 | commit | L5 | 803 | 802 |
| 7 | chain_end | — | 1369 | 803 |

### fault 135（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 804 | — |
| 2 | carrier_state | L1 | 805 | 804 |
| 3 | operand_read | L2 | 806 | 805 |
| 4 | execute | L3 | 807 | 806 |
| 5 | prf_writeback | L4 | 808 | 807 |
| 6 | commit | L5 | 809 | 808 |
| 7 | chain_end | — | 1370 | 809 |

### fault 136（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 810 | — |
| 2 | carrier_state | L1 | 811 | 810 |
| 3 | operand_read | L2 | 812 | 811 |
| 4 | execute | L3 | 813 | 812 |
| 5 | prf_writeback | L4 | 814 | 813 |
| 6 | commit | L5 | 815 | 814 |
| 7 | chain_end | — | 1371 | 815 |

### fault 137（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 816 | — |
| 2 | carrier_state | L1 | 817 | 816 |
| 3 | operand_read | L2 | 818 | 817 |
| 4 | execute | L3 | 819 | 818 |
| 5 | prf_writeback | L4 | 820 | 819 |
| 6 | commit | L5 | 821 | 820 |
| 7 | chain_end | — | 1372 | 821 |

### fault 138（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 822 | — |
| 2 | carrier_state | L1 | 823 | 822 |
| 3 | operand_read | L2 | 824 | 823 |
| 4 | execute | L3 | 825 | 824 |
| 5 | prf_writeback | L4 | 826 | 825 |
| 6 | commit | L5 | 827 | 826 |
| 7 | chain_end | — | 1373 | 827 |

### fault 139（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 828 | — |
| 2 | carrier_state | L1 | 829 | 828 |
| 3 | operand_read | L2 | 830 | 829 |
| 4 | execute | L3 | 831 | 830 |
| 5 | prf_writeback | L4 | 832 | 831 |
| 6 | commit | L5 | 833 | 832 |
| 7 | chain_end | — | 1374 | 833 |

### fault 14（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 78 | — |
| 2 | carrier_state | L1 | 79 | 78 |
| 3 | operand_read | L2 | 80 | 79 |
| 4 | execute | L3 | 81 | 80 |
| 5 | prf_writeback | L4 | 82 | 81 |
| 6 | commit | L5 | 83 | 82 |
| 7 | chain_end | — | 1249 | 83 |

### fault 140（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 834 | — |
| 2 | carrier_state | L1 | 835 | 834 |
| 3 | operand_read | L2 | 836 | 835 |
| 4 | execute | L3 | 837 | 836 |
| 5 | prf_writeback | L4 | 838 | 837 |
| 6 | commit | L5 | 839 | 838 |
| 7 | chain_end | — | 1375 | 839 |

### fault 141（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 840 | — |
| 2 | carrier_state | L1 | 841 | 840 |
| 3 | operand_read | L2 | 842 | 841 |
| 4 | execute | L3 | 843 | 842 |
| 5 | prf_writeback | L4 | 844 | 843 |
| 6 | commit | L5 | 845 | 844 |
| 7 | chain_end | — | 1376 | 845 |

### fault 142（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 846 | — |
| 2 | carrier_state | L1 | 847 | 846 |
| 3 | operand_read | L2 | 848 | 847 |
| 4 | execute | L3 | 849 | 848 |
| 5 | prf_writeback | L4 | 850 | 849 |
| 6 | commit | L5 | 851 | 850 |
| 7 | chain_end | — | 1377 | 851 |

### fault 143（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 852 | — |
| 2 | carrier_state | L1 | 853 | 852 |
| 3 | operand_read | L2 | 854 | 853 |
| 4 | execute | L3 | 855 | 854 |
| 5 | prf_writeback | L4 | 856 | 855 |
| 6 | commit | L5 | 857 | 856 |
| 7 | chain_end | — | 1378 | 857 |

### fault 144（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 858 | — |
| 2 | carrier_state | L1 | 859 | 858 |
| 3 | operand_read | L2 | 860 | 859 |
| 4 | execute | L3 | 861 | 860 |
| 5 | prf_writeback | L4 | 862 | 861 |
| 6 | commit | L5 | 863 | 862 |
| 7 | chain_end | — | 1379 | 863 |

### fault 145（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 864 | — |
| 2 | carrier_state | L1 | 865 | 864 |
| 3 | operand_read | L2 | 866 | 865 |
| 4 | execute | L3 | 867 | 866 |
| 5 | prf_writeback | L4 | 868 | 867 |
| 6 | commit | L5 | 869 | 868 |
| 7 | chain_end | — | 1380 | 869 |

### fault 146（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 870 | — |
| 2 | carrier_state | L1 | 871 | 870 |
| 3 | operand_read | L2 | 872 | 871 |
| 4 | execute | L3 | 873 | 872 |
| 5 | prf_writeback | L4 | 874 | 873 |
| 6 | commit | L5 | 875 | 874 |
| 7 | chain_end | — | 1381 | 875 |

### fault 147（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 876 | — |
| 2 | carrier_state | L1 | 877 | 876 |
| 3 | operand_read | L2 | 878 | 877 |
| 4 | execute | L3 | 879 | 878 |
| 5 | prf_writeback | L4 | 880 | 879 |
| 6 | commit | L5 | 881 | 880 |
| 7 | chain_end | — | 1382 | 881 |

### fault 148（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 882 | — |
| 2 | carrier_state | L1 | 883 | 882 |
| 3 | operand_read | L2 | 884 | 883 |
| 4 | execute | L3 | 885 | 884 |
| 5 | prf_writeback | L4 | 886 | 885 |
| 6 | commit | L5 | 887 | 886 |
| 7 | chain_end | — | 1383 | 887 |

### fault 149（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 888 | — |
| 2 | carrier_state | L1 | 889 | 888 |
| 3 | operand_read | L2 | 890 | 889 |
| 4 | execute | L3 | 891 | 890 |
| 5 | prf_writeback | L4 | 892 | 891 |
| 6 | commit | L5 | 893 | 892 |
| 7 | chain_end | — | 1384 | 893 |

### fault 15（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 84 | — |
| 2 | carrier_state | L1 | 85 | 84 |
| 3 | operand_read | L2 | 86 | 85 |
| 4 | execute | L3 | 87 | 86 |
| 5 | prf_writeback | L4 | 88 | 87 |
| 6 | commit | L5 | 89 | 88 |
| 7 | chain_end | — | 1250 | 89 |

### fault 150（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 894 | — |
| 2 | carrier_state | L1 | 895 | 894 |
| 3 | operand_read | L2 | 896 | 895 |
| 4 | execute | L3 | 897 | 896 |
| 5 | prf_writeback | L4 | 898 | 897 |
| 6 | commit | L5 | 899 | 898 |
| 7 | chain_end | — | 1385 | 899 |

### fault 151（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 900 | — |
| 2 | carrier_state | L1 | 901 | 900 |
| 3 | operand_read | L2 | 902 | 901 |
| 4 | execute | L3 | 903 | 902 |
| 5 | prf_writeback | L4 | 904 | 903 |
| 6 | commit | L5 | 905 | 904 |
| 7 | chain_end | — | 1386 | 905 |

### fault 152（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 906 | — |
| 2 | carrier_state | L1 | 907 | 906 |
| 3 | operand_read | L2 | 908 | 907 |
| 4 | execute | L3 | 909 | 908 |
| 5 | prf_writeback | L4 | 910 | 909 |
| 6 | commit | L5 | 911 | 910 |
| 7 | chain_end | — | 1387 | 911 |

### fault 153（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 912 | — |
| 2 | carrier_state | L1 | 913 | 912 |
| 3 | operand_read | L2 | 914 | 913 |
| 4 | execute | L3 | 915 | 914 |
| 5 | prf_writeback | L4 | 916 | 915 |
| 6 | commit | L5 | 917 | 916 |
| 7 | chain_end | — | 1388 | 917 |

### fault 154（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 918 | — |
| 2 | carrier_state | L1 | 919 | 918 |
| 3 | operand_read | L2 | 920 | 919 |
| 4 | execute | L3 | 921 | 920 |
| 5 | prf_writeback | L4 | 922 | 921 |
| 6 | commit | L5 | 923 | 922 |
| 7 | chain_end | — | 1389 | 923 |

### fault 155（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 924 | — |
| 2 | carrier_state | L1 | 925 | 924 |
| 3 | operand_read | L2 | 926 | 925 |
| 4 | execute | L3 | 927 | 926 |
| 5 | prf_writeback | L4 | 928 | 927 |
| 6 | commit | L5 | 929 | 928 |
| 7 | chain_end | — | 1390 | 929 |

### fault 156（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 930 | — |
| 2 | carrier_state | L1 | 931 | 930 |
| 3 | operand_read | L2 | 932 | 931 |
| 4 | execute | L3 | 933 | 932 |
| 5 | prf_writeback | L4 | 934 | 933 |
| 6 | commit | L5 | 935 | 934 |
| 7 | chain_end | — | 1391 | 935 |

### fault 157（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 936 | — |
| 2 | carrier_state | L1 | 937 | 936 |
| 3 | operand_read | L2 | 938 | 937 |
| 4 | execute | L3 | 939 | 938 |
| 5 | prf_writeback | L4 | 940 | 939 |
| 6 | commit | L5 | 941 | 940 |
| 7 | chain_end | — | 1392 | 941 |

### fault 158（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 942 | — |
| 2 | carrier_state | L1 | 943 | 942 |
| 3 | operand_read | L2 | 944 | 943 |
| 4 | execute | L3 | 945 | 944 |
| 5 | prf_writeback | L4 | 946 | 945 |
| 6 | commit | L5 | 947 | 946 |
| 7 | chain_end | — | 1393 | 947 |

### fault 159（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 948 | — |
| 2 | carrier_state | L1 | 949 | 948 |
| 3 | operand_read | L2 | 950 | 949 |
| 4 | execute | L3 | 951 | 950 |
| 5 | prf_writeback | L4 | 952 | 951 |
| 6 | commit | L5 | 953 | 952 |
| 7 | chain_end | — | 1394 | 953 |

### fault 16（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 90 | — |
| 2 | carrier_state | L1 | 91 | 90 |
| 3 | operand_read | L2 | 92 | 91 |
| 4 | execute | L3 | 93 | 92 |
| 5 | prf_writeback | L4 | 94 | 93 |
| 6 | commit | L5 | 95 | 94 |
| 7 | chain_end | — | 1251 | 95 |

### fault 160（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 954 | — |
| 2 | carrier_state | L1 | 955 | 954 |
| 3 | operand_read | L2 | 956 | 955 |
| 4 | execute | L3 | 957 | 956 |
| 5 | prf_writeback | L4 | 958 | 957 |
| 6 | commit | L5 | 959 | 958 |
| 7 | chain_end | — | 1395 | 959 |

### fault 161（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 960 | — |
| 2 | carrier_state | L1 | 961 | 960 |
| 3 | operand_read | L2 | 962 | 961 |
| 4 | execute | L3 | 963 | 962 |
| 5 | prf_writeback | L4 | 964 | 963 |
| 6 | commit | L5 | 965 | 964 |
| 7 | chain_end | — | 1396 | 965 |

### fault 162（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 966 | — |
| 2 | carrier_state | L1 | 967 | 966 |
| 3 | operand_read | L2 | 968 | 967 |
| 4 | execute | L3 | 969 | 968 |
| 5 | prf_writeback | L4 | 970 | 969 |
| 6 | commit | L5 | 971 | 970 |
| 7 | chain_end | — | 1397 | 971 |

### fault 163（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 972 | — |
| 2 | carrier_state | L1 | 973 | 972 |
| 3 | operand_read | L2 | 974 | 973 |
| 4 | execute | L3 | 975 | 974 |
| 5 | prf_writeback | L4 | 976 | 975 |
| 6 | commit | L5 | 977 | 976 |
| 7 | chain_end | — | 1398 | 977 |

### fault 164（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 978 | — |
| 2 | carrier_state | L1 | 979 | 978 |
| 3 | operand_read | L2 | 980 | 979 |
| 4 | execute | L3 | 981 | 980 |
| 5 | prf_writeback | L4 | 982 | 981 |
| 6 | commit | L5 | 983 | 982 |
| 7 | chain_end | — | 1399 | 983 |

### fault 165（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 984 | — |
| 2 | carrier_state | L1 | 985 | 984 |
| 3 | operand_read | L2 | 986 | 985 |
| 4 | execute | L3 | 987 | 986 |
| 5 | prf_writeback | L4 | 988 | 987 |
| 6 | commit | L5 | 989 | 988 |
| 7 | chain_end | — | 1400 | 989 |

### fault 166（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 990 | — |
| 2 | carrier_state | L1 | 991 | 990 |
| 3 | operand_read | L2 | 992 | 991 |
| 4 | execute | L3 | 993 | 992 |
| 5 | prf_writeback | L4 | 994 | 993 |
| 6 | commit | L5 | 995 | 994 |
| 7 | chain_end | — | 1401 | 995 |

### fault 167（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 996 | — |
| 2 | carrier_state | L1 | 997 | 996 |
| 3 | operand_read | L2 | 998 | 997 |
| 4 | execute | L3 | 999 | 998 |
| 5 | prf_writeback | L4 | 1000 | 999 |
| 6 | commit | L5 | 1001 | 1000 |
| 7 | chain_end | — | 1402 | 1001 |

### fault 168（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1002 | — |
| 2 | carrier_state | L1 | 1003 | 1002 |
| 3 | operand_read | L2 | 1004 | 1003 |
| 4 | execute | L3 | 1005 | 1004 |
| 5 | prf_writeback | L4 | 1006 | 1005 |
| 6 | commit | L5 | 1007 | 1006 |
| 7 | chain_end | — | 1403 | 1007 |

### fault 169（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1008 | — |
| 2 | carrier_state | L1 | 1009 | 1008 |
| 3 | operand_read | L2 | 1010 | 1009 |
| 4 | execute | L3 | 1011 | 1010 |
| 5 | prf_writeback | L4 | 1012 | 1011 |
| 6 | commit | L5 | 1013 | 1012 |
| 7 | chain_end | — | 1404 | 1013 |

### fault 17（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 96 | — |
| 2 | carrier_state | L1 | 97 | 96 |
| 3 | operand_read | L2 | 98 | 97 |
| 4 | execute | L3 | 99 | 98 |
| 5 | prf_writeback | L4 | 100 | 99 |
| 6 | commit | L5 | 101 | 100 |
| 7 | chain_end | — | 1252 | 101 |

### fault 170（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1014 | — |
| 2 | carrier_state | L1 | 1015 | 1014 |
| 3 | operand_read | L2 | 1016 | 1015 |
| 4 | execute | L3 | 1017 | 1016 |
| 5 | prf_writeback | L4 | 1018 | 1017 |
| 6 | commit | L5 | 1019 | 1018 |
| 7 | chain_end | — | 1405 | 1019 |

### fault 171（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1020 | — |
| 2 | carrier_state | L1 | 1021 | 1020 |
| 3 | operand_read | L2 | 1022 | 1021 |
| 4 | execute | L3 | 1023 | 1022 |
| 5 | prf_writeback | L4 | 1024 | 1023 |
| 6 | commit | L5 | 1025 | 1024 |
| 7 | chain_end | — | 1406 | 1025 |

### fault 172（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1026 | — |
| 2 | carrier_state | L1 | 1027 | 1026 |
| 3 | operand_read | L2 | 1028 | 1027 |
| 4 | execute | L3 | 1029 | 1028 |
| 5 | prf_writeback | L4 | 1030 | 1029 |
| 6 | commit | L5 | 1031 | 1030 |
| 7 | chain_end | — | 1407 | 1031 |

### fault 173（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1032 | — |
| 2 | carrier_state | L1 | 1033 | 1032 |
| 3 | operand_read | L2 | 1034 | 1033 |
| 4 | execute | L3 | 1035 | 1034 |
| 5 | prf_writeback | L4 | 1036 | 1035 |
| 6 | commit | L5 | 1037 | 1036 |
| 7 | chain_end | — | 1408 | 1037 |

### fault 174（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1038 | — |
| 2 | carrier_state | L1 | 1039 | 1038 |
| 3 | operand_read | L2 | 1040 | 1039 |
| 4 | execute | L3 | 1041 | 1040 |
| 5 | prf_writeback | L4 | 1042 | 1041 |
| 6 | commit | L5 | 1043 | 1042 |
| 7 | chain_end | — | 1409 | 1043 |

### fault 175（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1044 | — |
| 2 | carrier_state | L1 | 1045 | 1044 |
| 3 | operand_read | L2 | 1046 | 1045 |
| 4 | execute | L3 | 1047 | 1046 |
| 5 | prf_writeback | L4 | 1048 | 1047 |
| 6 | commit | L5 | 1049 | 1048 |
| 7 | chain_end | — | 1410 | 1049 |

### fault 176（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1050 | — |
| 2 | carrier_state | L1 | 1051 | 1050 |
| 3 | operand_read | L2 | 1052 | 1051 |
| 4 | execute | L3 | 1053 | 1052 |
| 5 | prf_writeback | L4 | 1054 | 1053 |
| 6 | commit | L5 | 1055 | 1054 |
| 7 | chain_end | — | 1411 | 1055 |

### fault 177（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1056 | — |
| 2 | carrier_state | L1 | 1057 | 1056 |
| 3 | operand_read | L2 | 1058 | 1057 |
| 4 | execute | L3 | 1059 | 1058 |
| 5 | prf_writeback | L4 | 1060 | 1059 |
| 6 | commit | L5 | 1061 | 1060 |
| 7 | chain_end | — | 1412 | 1061 |

### fault 178（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1062 | — |
| 2 | carrier_state | L1 | 1063 | 1062 |
| 3 | operand_read | L2 | 1064 | 1063 |
| 4 | execute | L3 | 1065 | 1064 |
| 5 | prf_writeback | L4 | 1066 | 1065 |
| 6 | commit | L5 | 1067 | 1066 |
| 7 | chain_end | — | 1413 | 1067 |

### fault 179（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1068 | — |
| 2 | carrier_state | L1 | 1069 | 1068 |
| 3 | operand_read | L2 | 1070 | 1069 |
| 4 | execute | L3 | 1071 | 1070 |
| 5 | prf_writeback | L4 | 1072 | 1071 |
| 6 | commit | L5 | 1073 | 1072 |
| 7 | chain_end | — | 1414 | 1073 |

### fault 18（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 102 | — |
| 2 | carrier_state | L1 | 103 | 102 |
| 3 | operand_read | L2 | 104 | 103 |
| 4 | execute | L3 | 105 | 104 |
| 5 | prf_writeback | L4 | 106 | 105 |
| 6 | commit | L5 | 107 | 106 |
| 7 | chain_end | — | 1253 | 107 |

### fault 180（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1074 | — |
| 2 | carrier_state | L1 | 1075 | 1074 |
| 3 | operand_read | L2 | 1076 | 1075 |
| 4 | execute | L3 | 1077 | 1076 |
| 5 | prf_writeback | L4 | 1078 | 1077 |
| 6 | commit | L5 | 1079 | 1078 |
| 7 | chain_end | — | 1415 | 1079 |

### fault 181（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1080 | — |
| 2 | carrier_state | L1 | 1081 | 1080 |
| 3 | operand_read | L2 | 1082 | 1081 |
| 4 | execute | L3 | 1083 | 1082 |
| 5 | prf_writeback | L4 | 1084 | 1083 |
| 6 | commit | L5 | 1085 | 1084 |
| 7 | chain_end | — | 1416 | 1085 |

### fault 182（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1086 | — |
| 2 | carrier_state | L1 | 1087 | 1086 |
| 3 | operand_read | L2 | 1088 | 1087 |
| 4 | execute | L3 | 1089 | 1088 |
| 5 | prf_writeback | L4 | 1090 | 1089 |
| 6 | commit | L5 | 1091 | 1090 |
| 7 | chain_end | — | 1417 | 1091 |

### fault 183（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1092 | — |
| 2 | carrier_state | L1 | 1093 | 1092 |
| 3 | operand_read | L2 | 1094 | 1093 |
| 4 | execute | L3 | 1095 | 1094 |
| 5 | prf_writeback | L4 | 1096 | 1095 |
| 6 | commit | L5 | 1097 | 1096 |
| 7 | chain_end | — | 1418 | 1097 |

### fault 184（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1098 | — |
| 2 | carrier_state | L1 | 1099 | 1098 |
| 3 | operand_read | L2 | 1100 | 1099 |
| 4 | execute | L3 | 1101 | 1100 |
| 5 | prf_writeback | L4 | 1102 | 1101 |
| 6 | commit | L5 | 1103 | 1102 |
| 7 | chain_end | — | 1419 | 1103 |

### fault 185（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1104 | — |
| 2 | carrier_state | L1 | 1105 | 1104 |
| 3 | operand_read | L2 | 1106 | 1105 |
| 4 | execute | L3 | 1107 | 1106 |
| 5 | prf_writeback | L4 | 1108 | 1107 |
| 6 | commit | L5 | 1109 | 1108 |
| 7 | chain_end | — | 1420 | 1109 |

### fault 186（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1110 | — |
| 2 | carrier_state | L1 | 1111 | 1110 |
| 3 | operand_read | L2 | 1112 | 1111 |
| 4 | execute | L3 | 1113 | 1112 |
| 5 | prf_writeback | L4 | 1114 | 1113 |
| 6 | commit | L5 | 1115 | 1114 |
| 7 | chain_end | — | 1421 | 1115 |

### fault 187（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1116 | — |
| 2 | carrier_state | L1 | 1117 | 1116 |
| 3 | operand_read | L2 | 1118 | 1117 |
| 4 | execute | L3 | 1119 | 1118 |
| 5 | prf_writeback | L4 | 1120 | 1119 |
| 6 | commit | L5 | 1121 | 1120 |
| 7 | chain_end | — | 1422 | 1121 |

### fault 188（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1122 | — |
| 2 | carrier_state | L1 | 1123 | 1122 |
| 3 | operand_read | L2 | 1124 | 1123 |
| 4 | execute | L3 | 1125 | 1124 |
| 5 | prf_writeback | L4 | 1126 | 1125 |
| 6 | commit | L5 | 1127 | 1126 |
| 7 | chain_end | — | 1423 | 1127 |

### fault 189（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1128 | — |
| 2 | carrier_state | L1 | 1129 | 1128 |
| 3 | operand_read | L2 | 1130 | 1129 |
| 4 | execute | L3 | 1131 | 1130 |
| 5 | prf_writeback | L4 | 1132 | 1131 |
| 6 | commit | L5 | 1133 | 1132 |
| 7 | chain_end | — | 1424 | 1133 |

### fault 19（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 108 | — |
| 2 | carrier_state | L1 | 109 | 108 |
| 3 | operand_read | L2 | 110 | 109 |
| 4 | execute | L3 | 111 | 110 |
| 5 | prf_writeback | L4 | 112 | 111 |
| 6 | commit | L5 | 113 | 112 |
| 7 | chain_end | — | 1254 | 113 |

### fault 190（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1134 | — |
| 2 | carrier_state | L1 | 1135 | 1134 |
| 3 | operand_read | L2 | 1136 | 1135 |
| 4 | execute | L3 | 1137 | 1136 |
| 5 | prf_writeback | L4 | 1138 | 1137 |
| 6 | commit | L5 | 1139 | 1138 |
| 7 | chain_end | — | 1425 | 1139 |

### fault 191（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1140 | — |
| 2 | carrier_state | L1 | 1141 | 1140 |
| 3 | operand_read | L2 | 1142 | 1141 |
| 4 | execute | L3 | 1143 | 1142 |
| 5 | prf_writeback | L4 | 1144 | 1143 |
| 6 | commit | L5 | 1145 | 1144 |
| 7 | chain_end | — | 1426 | 1145 |

### fault 192（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1146 | — |
| 2 | carrier_state | L1 | 1147 | 1146 |
| 3 | operand_read | L2 | 1148 | 1147 |
| 4 | execute | L3 | 1149 | 1148 |
| 5 | prf_writeback | L4 | 1150 | 1149 |
| 6 | commit | L5 | 1151 | 1150 |
| 7 | chain_end | — | 1427 | 1151 |

### fault 193（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1152 | — |
| 2 | carrier_state | L1 | 1153 | 1152 |
| 3 | operand_read | L2 | 1154 | 1153 |
| 4 | execute | L3 | 1155 | 1154 |
| 5 | prf_writeback | L4 | 1156 | 1155 |
| 6 | commit | L5 | 1157 | 1156 |
| 7 | chain_end | — | 1428 | 1157 |

### fault 194（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1158 | — |
| 2 | carrier_state | L1 | 1159 | 1158 |
| 3 | operand_read | L2 | 1160 | 1159 |
| 4 | execute | L3 | 1161 | 1160 |
| 5 | prf_writeback | L4 | 1162 | 1161 |
| 6 | commit | L5 | 1163 | 1162 |
| 7 | chain_end | — | 1429 | 1163 |

### fault 195（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1164 | — |
| 2 | carrier_state | L1 | 1165 | 1164 |
| 3 | operand_read | L2 | 1166 | 1165 |
| 4 | execute | L3 | 1167 | 1166 |
| 5 | prf_writeback | L4 | 1168 | 1167 |
| 6 | commit | L5 | 1169 | 1168 |
| 7 | chain_end | — | 1430 | 1169 |

### fault 196（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1170 | — |
| 2 | carrier_state | L1 | 1171 | 1170 |
| 3 | operand_read | L2 | 1172 | 1171 |
| 4 | execute | L3 | 1173 | 1172 |
| 5 | prf_writeback | L4 | 1174 | 1173 |
| 6 | commit | L5 | 1175 | 1174 |
| 7 | chain_end | — | 1431 | 1175 |

### fault 197（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1176 | — |
| 2 | carrier_state | L1 | 1177 | 1176 |
| 3 | operand_read | L2 | 1178 | 1177 |
| 4 | execute | L3 | 1179 | 1178 |
| 5 | prf_writeback | L4 | 1180 | 1179 |
| 6 | commit | L5 | 1181 | 1180 |
| 7 | chain_end | — | 1432 | 1181 |

### fault 198（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1182 | — |
| 2 | carrier_state | L1 | 1183 | 1182 |
| 3 | operand_read | L2 | 1184 | 1183 |
| 4 | execute | L3 | 1185 | 1184 |
| 5 | prf_writeback | L4 | 1186 | 1185 |
| 6 | commit | L5 | 1187 | 1186 |
| 7 | chain_end | — | 1433 | 1187 |

### fault 199（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1188 | — |
| 2 | carrier_state | L1 | 1189 | 1188 |
| 3 | operand_read | L2 | 1190 | 1189 |
| 4 | execute | L3 | 1191 | 1190 |
| 5 | prf_writeback | L4 | 1192 | 1191 |
| 6 | commit | L5 | 1193 | 1192 |
| 7 | chain_end | — | 1434 | 1193 |

### fault 2（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 6 | — |
| 2 | carrier_state | L1 | 7 | 6 |
| 3 | operand_read | L2 | 8 | 7 |
| 4 | execute | L3 | 9 | 8 |
| 5 | prf_writeback | L4 | 10 | 9 |
| 6 | commit | L5 | 11 | 10 |
| 7 | chain_end | — | 1237 | 11 |

### fault 20（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 114 | — |
| 2 | carrier_state | L1 | 115 | 114 |
| 3 | operand_read | L2 | 116 | 115 |
| 4 | execute | L3 | 117 | 116 |
| 5 | prf_writeback | L4 | 118 | 117 |
| 6 | commit | L5 | 119 | 118 |
| 7 | chain_end | — | 1255 | 119 |

### fault 200（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1194 | — |
| 2 | carrier_state | L1 | 1195 | 1194 |
| 3 | operand_read | L2 | 1196 | 1195 |
| 4 | execute | L3 | 1197 | 1196 |
| 5 | prf_writeback | L4 | 1198 | 1197 |
| 6 | commit | L5 | 1199 | 1198 |
| 7 | chain_end | — | 1435 | 1199 |

### fault 201（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1200 | — |
| 2 | carrier_state | L1 | 1201 | 1200 |
| 3 | operand_read | L2 | 1202 | 1201 |
| 4 | execute | L3 | 1203 | 1202 |
| 5 | prf_writeback | L4 | 1204 | 1203 |
| 6 | commit | L5 | 1205 | 1204 |
| 7 | chain_end | — | 1436 | 1205 |

### fault 202（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1206 | — |
| 2 | carrier_state | L1 | 1207 | 1206 |
| 3 | operand_read | L2 | 1208 | 1207 |
| 4 | execute | L3 | 1209 | 1208 |
| 5 | prf_writeback | L4 | 1210 | 1209 |
| 6 | commit | L5 | 1211 | 1210 |
| 7 | chain_end | — | 1437 | 1211 |

### fault 203（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1212 | — |
| 2 | carrier_state | L1 | 1213 | 1212 |
| 3 | operand_read | L2 | 1214 | 1213 |
| 4 | execute | L3 | 1215 | 1214 |
| 5 | prf_writeback | L4 | 1216 | 1215 |
| 6 | commit | L5 | 1217 | 1216 |
| 7 | chain_end | — | 1438 | 1217 |

### fault 204（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1218 | — |
| 2 | carrier_state | L1 | 1219 | 1218 |
| 3 | operand_read | L2 | 1220 | 1219 |
| 4 | execute | L3 | 1221 | 1220 |
| 5 | prf_writeback | L4 | 1222 | 1221 |
| 6 | commit | L5 | 1223 | 1222 |
| 7 | chain_end | — | 1439 | 1223 |

### fault 205（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1224 | — |
| 2 | carrier_state | L1 | 1225 | 1224 |
| 3 | operand_read | L2 | 1226 | 1225 |
| 4 | execute | L3 | 1227 | 1226 |
| 5 | prf_writeback | L4 | 1228 | 1227 |
| 6 | commit | L5 | 1229 | 1228 |
| 7 | chain_end | — | 1440 | 1229 |

### fault 206（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1230 | — |
| 2 | carrier_state | L1 | 1231 | 1230 |
| 3 | operand_read | L2 | 1232 | 1231 |
| 4 | execute | L3 | 1233 | 1232 |
| 5 | prf_writeback | L4 | 1234 | 1233 |
| 6 | commit | L5 | 1235 | 1234 |
| 7 | chain_end | — | 1441 | 1235 |

### fault 21（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 120 | — |
| 2 | carrier_state | L1 | 121 | 120 |
| 3 | operand_read | L2 | 122 | 121 |
| 4 | execute | L3 | 123 | 122 |
| 5 | prf_writeback | L4 | 124 | 123 |
| 6 | commit | L5 | 125 | 124 |
| 7 | chain_end | — | 1256 | 125 |

### fault 22（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 126 | — |
| 2 | carrier_state | L1 | 127 | 126 |
| 3 | operand_read | L2 | 128 | 127 |
| 4 | execute | L3 | 129 | 128 |
| 5 | prf_writeback | L4 | 130 | 129 |
| 6 | commit | L5 | 131 | 130 |
| 7 | chain_end | — | 1257 | 131 |

### fault 23（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 132 | — |
| 2 | carrier_state | L1 | 133 | 132 |
| 3 | operand_read | L2 | 134 | 133 |
| 4 | execute | L3 | 135 | 134 |
| 5 | prf_writeback | L4 | 136 | 135 |
| 6 | commit | L5 | 137 | 136 |
| 7 | chain_end | — | 1258 | 137 |

### fault 24（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 138 | — |
| 2 | carrier_state | L1 | 139 | 138 |
| 3 | operand_read | L2 | 140 | 139 |
| 4 | execute | L3 | 141 | 140 |
| 5 | prf_writeback | L4 | 142 | 141 |
| 6 | commit | L5 | 143 | 142 |
| 7 | chain_end | — | 1259 | 143 |

### fault 25（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 144 | — |
| 2 | carrier_state | L1 | 145 | 144 |
| 3 | operand_read | L2 | 146 | 145 |
| 4 | execute | L3 | 147 | 146 |
| 5 | prf_writeback | L4 | 148 | 147 |
| 6 | commit | L5 | 149 | 148 |
| 7 | chain_end | — | 1260 | 149 |

### fault 26（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 150 | — |
| 2 | carrier_state | L1 | 151 | 150 |
| 3 | operand_read | L2 | 152 | 151 |
| 4 | execute | L3 | 153 | 152 |
| 5 | prf_writeback | L4 | 154 | 153 |
| 6 | commit | L5 | 155 | 154 |
| 7 | chain_end | — | 1261 | 155 |

### fault 27（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 156 | — |
| 2 | carrier_state | L1 | 157 | 156 |
| 3 | operand_read | L2 | 158 | 157 |
| 4 | execute | L3 | 159 | 158 |
| 5 | prf_writeback | L4 | 160 | 159 |
| 6 | commit | L5 | 161 | 160 |
| 7 | chain_end | — | 1262 | 161 |

### fault 28（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 162 | — |
| 2 | carrier_state | L1 | 163 | 162 |
| 3 | operand_read | L2 | 164 | 163 |
| 4 | execute | L3 | 165 | 164 |
| 5 | prf_writeback | L4 | 166 | 165 |
| 6 | commit | L5 | 167 | 166 |
| 7 | chain_end | — | 1263 | 167 |

### fault 29（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 168 | — |
| 2 | carrier_state | L1 | 169 | 168 |
| 3 | operand_read | L2 | 170 | 169 |
| 4 | execute | L3 | 171 | 170 |
| 5 | prf_writeback | L4 | 172 | 171 |
| 6 | commit | L5 | 173 | 172 |
| 7 | chain_end | — | 1264 | 173 |

### fault 3（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 12 | — |
| 2 | carrier_state | L1 | 13 | 12 |
| 3 | operand_read | L2 | 14 | 13 |
| 4 | execute | L3 | 15 | 14 |
| 5 | prf_writeback | L4 | 16 | 15 |
| 6 | commit | L5 | 17 | 16 |
| 7 | chain_end | — | 1238 | 17 |

### fault 30（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 174 | — |
| 2 | carrier_state | L1 | 175 | 174 |
| 3 | operand_read | L2 | 176 | 175 |
| 4 | execute | L3 | 177 | 176 |
| 5 | prf_writeback | L4 | 178 | 177 |
| 6 | commit | L5 | 179 | 178 |
| 7 | chain_end | — | 1265 | 179 |

### fault 31（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 180 | — |
| 2 | carrier_state | L1 | 181 | 180 |
| 3 | operand_read | L2 | 182 | 181 |
| 4 | execute | L3 | 183 | 182 |
| 5 | prf_writeback | L4 | 184 | 183 |
| 6 | commit | L5 | 185 | 184 |
| 7 | chain_end | — | 1266 | 185 |

### fault 32（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 186 | — |
| 2 | carrier_state | L1 | 187 | 186 |
| 3 | operand_read | L2 | 188 | 187 |
| 4 | execute | L3 | 189 | 188 |
| 5 | prf_writeback | L4 | 190 | 189 |
| 6 | commit | L5 | 191 | 190 |
| 7 | chain_end | — | 1267 | 191 |

### fault 33（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 192 | — |
| 2 | carrier_state | L1 | 193 | 192 |
| 3 | operand_read | L2 | 194 | 193 |
| 4 | execute | L3 | 195 | 194 |
| 5 | prf_writeback | L4 | 196 | 195 |
| 6 | commit | L5 | 197 | 196 |
| 7 | chain_end | — | 1268 | 197 |

### fault 34（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 198 | — |
| 2 | carrier_state | L1 | 199 | 198 |
| 3 | operand_read | L2 | 200 | 199 |
| 4 | execute | L3 | 201 | 200 |
| 5 | prf_writeback | L4 | 202 | 201 |
| 6 | commit | L5 | 203 | 202 |
| 7 | chain_end | — | 1269 | 203 |

### fault 35（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 204 | — |
| 2 | carrier_state | L1 | 205 | 204 |
| 3 | operand_read | L2 | 206 | 205 |
| 4 | execute | L3 | 207 | 206 |
| 5 | prf_writeback | L4 | 208 | 207 |
| 6 | commit | L5 | 209 | 208 |
| 7 | chain_end | — | 1270 | 209 |

### fault 36（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 210 | — |
| 2 | carrier_state | L1 | 211 | 210 |
| 3 | operand_read | L2 | 212 | 211 |
| 4 | execute | L3 | 213 | 212 |
| 5 | prf_writeback | L4 | 214 | 213 |
| 6 | commit | L5 | 215 | 214 |
| 7 | chain_end | — | 1271 | 215 |

### fault 37（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 216 | — |
| 2 | carrier_state | L1 | 217 | 216 |
| 3 | operand_read | L2 | 218 | 217 |
| 4 | execute | L3 | 219 | 218 |
| 5 | prf_writeback | L4 | 220 | 219 |
| 6 | commit | L5 | 221 | 220 |
| 7 | chain_end | — | 1272 | 221 |

### fault 38（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 222 | — |
| 2 | carrier_state | L1 | 223 | 222 |
| 3 | operand_read | L2 | 224 | 223 |
| 4 | execute | L3 | 225 | 224 |
| 5 | prf_writeback | L4 | 226 | 225 |
| 6 | commit | L5 | 227 | 226 |
| 7 | chain_end | — | 1273 | 227 |

### fault 39（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 228 | — |
| 2 | carrier_state | L1 | 229 | 228 |
| 3 | operand_read | L2 | 230 | 229 |
| 4 | execute | L3 | 231 | 230 |
| 5 | prf_writeback | L4 | 232 | 231 |
| 6 | commit | L5 | 233 | 232 |
| 7 | chain_end | — | 1274 | 233 |

### fault 4（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 18 | — |
| 2 | carrier_state | L1 | 19 | 18 |
| 3 | operand_read | L2 | 20 | 19 |
| 4 | execute | L3 | 21 | 20 |
| 5 | prf_writeback | L4 | 22 | 21 |
| 6 | commit | L5 | 23 | 22 |
| 7 | chain_end | — | 1239 | 23 |

### fault 40（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 234 | — |
| 2 | carrier_state | L1 | 235 | 234 |
| 3 | operand_read | L2 | 236 | 235 |
| 4 | execute | L3 | 237 | 236 |
| 5 | prf_writeback | L4 | 238 | 237 |
| 6 | commit | L5 | 239 | 238 |
| 7 | chain_end | — | 1275 | 239 |

### fault 41（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 240 | — |
| 2 | carrier_state | L1 | 241 | 240 |
| 3 | operand_read | L2 | 242 | 241 |
| 4 | execute | L3 | 243 | 242 |
| 5 | prf_writeback | L4 | 244 | 243 |
| 6 | commit | L5 | 245 | 244 |
| 7 | chain_end | — | 1276 | 245 |

### fault 42（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 246 | — |
| 2 | carrier_state | L1 | 247 | 246 |
| 3 | operand_read | L2 | 248 | 247 |
| 4 | execute | L3 | 249 | 248 |
| 5 | prf_writeback | L4 | 250 | 249 |
| 6 | commit | L5 | 251 | 250 |
| 7 | chain_end | — | 1277 | 251 |

### fault 43（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 252 | — |
| 2 | carrier_state | L1 | 253 | 252 |
| 3 | operand_read | L2 | 254 | 253 |
| 4 | execute | L3 | 255 | 254 |
| 5 | prf_writeback | L4 | 256 | 255 |
| 6 | commit | L5 | 257 | 256 |
| 7 | chain_end | — | 1278 | 257 |

### fault 44（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 258 | — |
| 2 | carrier_state | L1 | 259 | 258 |
| 3 | operand_read | L2 | 260 | 259 |
| 4 | execute | L3 | 261 | 260 |
| 5 | prf_writeback | L4 | 262 | 261 |
| 6 | commit | L5 | 263 | 262 |
| 7 | chain_end | — | 1279 | 263 |

### fault 45（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 264 | — |
| 2 | carrier_state | L1 | 265 | 264 |
| 3 | operand_read | L2 | 266 | 265 |
| 4 | execute | L3 | 267 | 266 |
| 5 | prf_writeback | L4 | 268 | 267 |
| 6 | commit | L5 | 269 | 268 |
| 7 | chain_end | — | 1280 | 269 |

### fault 46（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 270 | — |
| 2 | carrier_state | L1 | 271 | 270 |
| 3 | operand_read | L2 | 272 | 271 |
| 4 | execute | L3 | 273 | 272 |
| 5 | prf_writeback | L4 | 274 | 273 |
| 6 | commit | L5 | 275 | 274 |
| 7 | chain_end | — | 1281 | 275 |

### fault 47（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 276 | — |
| 2 | carrier_state | L1 | 277 | 276 |
| 3 | operand_read | L2 | 278 | 277 |
| 4 | execute | L3 | 279 | 278 |
| 5 | prf_writeback | L4 | 280 | 279 |
| 6 | commit | L5 | 281 | 280 |
| 7 | chain_end | — | 1282 | 281 |

### fault 48（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 282 | — |
| 2 | carrier_state | L1 | 283 | 282 |
| 3 | operand_read | L2 | 284 | 283 |
| 4 | execute | L3 | 285 | 284 |
| 5 | prf_writeback | L4 | 286 | 285 |
| 6 | commit | L5 | 287 | 286 |
| 7 | chain_end | — | 1283 | 287 |

### fault 49（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 288 | — |
| 2 | carrier_state | L1 | 289 | 288 |
| 3 | operand_read | L2 | 290 | 289 |
| 4 | execute | L3 | 291 | 290 |
| 5 | prf_writeback | L4 | 292 | 291 |
| 6 | commit | L5 | 293 | 292 |
| 7 | chain_end | — | 1284 | 293 |

### fault 5（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 24 | — |
| 2 | carrier_state | L1 | 25 | 24 |
| 3 | operand_read | L2 | 26 | 25 |
| 4 | execute | L3 | 27 | 26 |
| 5 | prf_writeback | L4 | 28 | 27 |
| 6 | commit | L5 | 29 | 28 |
| 7 | chain_end | — | 1240 | 29 |

### fault 50（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 294 | — |
| 2 | carrier_state | L1 | 295 | 294 |
| 3 | operand_read | L2 | 296 | 295 |
| 4 | execute | L3 | 297 | 296 |
| 5 | prf_writeback | L4 | 298 | 297 |
| 6 | commit | L5 | 299 | 298 |
| 7 | chain_end | — | 1285 | 299 |

### fault 51（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 300 | — |
| 2 | carrier_state | L1 | 301 | 300 |
| 3 | operand_read | L2 | 302 | 301 |
| 4 | execute | L3 | 303 | 302 |
| 5 | prf_writeback | L4 | 304 | 303 |
| 6 | commit | L5 | 305 | 304 |
| 7 | chain_end | — | 1286 | 305 |

### fault 52（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 306 | — |
| 2 | carrier_state | L1 | 307 | 306 |
| 3 | operand_read | L2 | 308 | 307 |
| 4 | execute | L3 | 309 | 308 |
| 5 | prf_writeback | L4 | 310 | 309 |
| 6 | commit | L5 | 311 | 310 |
| 7 | chain_end | — | 1287 | 311 |

### fault 53（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 312 | — |
| 2 | carrier_state | L1 | 313 | 312 |
| 3 | operand_read | L2 | 314 | 313 |
| 4 | execute | L3 | 315 | 314 |
| 5 | prf_writeback | L4 | 316 | 315 |
| 6 | commit | L5 | 317 | 316 |
| 7 | chain_end | — | 1288 | 317 |

### fault 54（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 318 | — |
| 2 | carrier_state | L1 | 319 | 318 |
| 3 | operand_read | L2 | 320 | 319 |
| 4 | execute | L3 | 321 | 320 |
| 5 | prf_writeback | L4 | 322 | 321 |
| 6 | commit | L5 | 323 | 322 |
| 7 | chain_end | — | 1289 | 323 |

### fault 55（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 324 | — |
| 2 | carrier_state | L1 | 325 | 324 |
| 3 | operand_read | L2 | 326 | 325 |
| 4 | execute | L3 | 327 | 326 |
| 5 | prf_writeback | L4 | 328 | 327 |
| 6 | commit | L5 | 329 | 328 |
| 7 | chain_end | — | 1290 | 329 |

### fault 56（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 330 | — |
| 2 | carrier_state | L1 | 331 | 330 |
| 3 | operand_read | L2 | 332 | 331 |
| 4 | execute | L3 | 333 | 332 |
| 5 | prf_writeback | L4 | 334 | 333 |
| 6 | commit | L5 | 335 | 334 |
| 7 | chain_end | — | 1291 | 335 |

### fault 57（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 336 | — |
| 2 | carrier_state | L1 | 337 | 336 |
| 3 | operand_read | L2 | 338 | 337 |
| 4 | execute | L3 | 339 | 338 |
| 5 | prf_writeback | L4 | 340 | 339 |
| 6 | commit | L5 | 341 | 340 |
| 7 | chain_end | — | 1292 | 341 |

### fault 58（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 342 | — |
| 2 | carrier_state | L1 | 343 | 342 |
| 3 | operand_read | L2 | 344 | 343 |
| 4 | execute | L3 | 345 | 344 |
| 5 | prf_writeback | L4 | 346 | 345 |
| 6 | commit | L5 | 347 | 346 |
| 7 | chain_end | — | 1293 | 347 |

### fault 59（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 348 | — |
| 2 | carrier_state | L1 | 349 | 348 |
| 3 | operand_read | L2 | 350 | 349 |
| 4 | execute | L3 | 351 | 350 |
| 5 | prf_writeback | L4 | 352 | 351 |
| 6 | commit | L5 | 353 | 352 |
| 7 | chain_end | — | 1294 | 353 |

### fault 6（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 30 | — |
| 2 | carrier_state | L1 | 31 | 30 |
| 3 | operand_read | L2 | 32 | 31 |
| 4 | execute | L3 | 33 | 32 |
| 5 | prf_writeback | L4 | 34 | 33 |
| 6 | commit | L5 | 35 | 34 |
| 7 | chain_end | — | 1241 | 35 |

### fault 60（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 354 | — |
| 2 | carrier_state | L1 | 355 | 354 |
| 3 | operand_read | L2 | 356 | 355 |
| 4 | execute | L3 | 357 | 356 |
| 5 | prf_writeback | L4 | 358 | 357 |
| 6 | commit | L5 | 359 | 358 |
| 7 | chain_end | — | 1295 | 359 |

### fault 61（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 360 | — |
| 2 | carrier_state | L1 | 361 | 360 |
| 3 | operand_read | L2 | 362 | 361 |
| 4 | execute | L3 | 363 | 362 |
| 5 | prf_writeback | L4 | 364 | 363 |
| 6 | commit | L5 | 365 | 364 |
| 7 | chain_end | — | 1296 | 365 |

### fault 62（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 366 | — |
| 2 | carrier_state | L1 | 367 | 366 |
| 3 | operand_read | L2 | 368 | 367 |
| 4 | execute | L3 | 369 | 368 |
| 5 | prf_writeback | L4 | 370 | 369 |
| 6 | commit | L5 | 371 | 370 |
| 7 | chain_end | — | 1297 | 371 |

### fault 63（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 372 | — |
| 2 | carrier_state | L1 | 373 | 372 |
| 3 | operand_read | L2 | 374 | 373 |
| 4 | execute | L3 | 375 | 374 |
| 5 | prf_writeback | L4 | 376 | 375 |
| 6 | commit | L5 | 377 | 376 |
| 7 | chain_end | — | 1298 | 377 |

### fault 64（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 378 | — |
| 2 | carrier_state | L1 | 379 | 378 |
| 3 | operand_read | L2 | 380 | 379 |
| 4 | execute | L3 | 381 | 380 |
| 5 | prf_writeback | L4 | 382 | 381 |
| 6 | commit | L5 | 383 | 382 |
| 7 | chain_end | — | 1299 | 383 |

### fault 65（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 384 | — |
| 2 | carrier_state | L1 | 385 | 384 |
| 3 | operand_read | L2 | 386 | 385 |
| 4 | execute | L3 | 387 | 386 |
| 5 | prf_writeback | L4 | 388 | 387 |
| 6 | commit | L5 | 389 | 388 |
| 7 | chain_end | — | 1300 | 389 |

### fault 66（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 390 | — |
| 2 | carrier_state | L1 | 391 | 390 |
| 3 | operand_read | L2 | 392 | 391 |
| 4 | execute | L3 | 393 | 392 |
| 5 | prf_writeback | L4 | 394 | 393 |
| 6 | commit | L5 | 395 | 394 |
| 7 | chain_end | — | 1301 | 395 |

### fault 67（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 396 | — |
| 2 | carrier_state | L1 | 397 | 396 |
| 3 | operand_read | L2 | 398 | 397 |
| 4 | execute | L3 | 399 | 398 |
| 5 | prf_writeback | L4 | 400 | 399 |
| 6 | commit | L5 | 401 | 400 |
| 7 | chain_end | — | 1302 | 401 |

### fault 68（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 402 | — |
| 2 | carrier_state | L1 | 403 | 402 |
| 3 | operand_read | L2 | 404 | 403 |
| 4 | execute | L3 | 405 | 404 |
| 5 | prf_writeback | L4 | 406 | 405 |
| 6 | commit | L5 | 407 | 406 |
| 7 | chain_end | — | 1303 | 407 |

### fault 69（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 408 | — |
| 2 | carrier_state | L1 | 409 | 408 |
| 3 | operand_read | L2 | 410 | 409 |
| 4 | execute | L3 | 411 | 410 |
| 5 | prf_writeback | L4 | 412 | 411 |
| 6 | commit | L5 | 413 | 412 |
| 7 | chain_end | — | 1304 | 413 |

### fault 7（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 36 | — |
| 2 | carrier_state | L1 | 37 | 36 |
| 3 | operand_read | L2 | 38 | 37 |
| 4 | execute | L3 | 39 | 38 |
| 5 | prf_writeback | L4 | 40 | 39 |
| 6 | commit | L5 | 41 | 40 |
| 7 | chain_end | — | 1242 | 41 |

### fault 70（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 414 | — |
| 2 | carrier_state | L1 | 415 | 414 |
| 3 | operand_read | L2 | 416 | 415 |
| 4 | execute | L3 | 417 | 416 |
| 5 | prf_writeback | L4 | 418 | 417 |
| 6 | commit | L5 | 419 | 418 |
| 7 | chain_end | — | 1305 | 419 |

### fault 71（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 420 | — |
| 2 | carrier_state | L1 | 421 | 420 |
| 3 | operand_read | L2 | 422 | 421 |
| 4 | execute | L3 | 423 | 422 |
| 5 | prf_writeback | L4 | 424 | 423 |
| 6 | commit | L5 | 425 | 424 |
| 7 | chain_end | — | 1306 | 425 |

### fault 72（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 426 | — |
| 2 | carrier_state | L1 | 427 | 426 |
| 3 | operand_read | L2 | 428 | 427 |
| 4 | execute | L3 | 429 | 428 |
| 5 | prf_writeback | L4 | 430 | 429 |
| 6 | commit | L5 | 431 | 430 |
| 7 | chain_end | — | 1307 | 431 |

### fault 73（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 432 | — |
| 2 | carrier_state | L1 | 433 | 432 |
| 3 | operand_read | L2 | 434 | 433 |
| 4 | execute | L3 | 435 | 434 |
| 5 | prf_writeback | L4 | 436 | 435 |
| 6 | commit | L5 | 437 | 436 |
| 7 | chain_end | — | 1308 | 437 |

### fault 74（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 438 | — |
| 2 | carrier_state | L1 | 439 | 438 |
| 3 | operand_read | L2 | 440 | 439 |
| 4 | execute | L3 | 441 | 440 |
| 5 | prf_writeback | L4 | 442 | 441 |
| 6 | commit | L5 | 443 | 442 |
| 7 | chain_end | — | 1309 | 443 |

### fault 75（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 444 | — |
| 2 | carrier_state | L1 | 445 | 444 |
| 3 | operand_read | L2 | 446 | 445 |
| 4 | execute | L3 | 447 | 446 |
| 5 | prf_writeback | L4 | 448 | 447 |
| 6 | commit | L5 | 449 | 448 |
| 7 | chain_end | — | 1310 | 449 |

### fault 76（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 450 | — |
| 2 | carrier_state | L1 | 451 | 450 |
| 3 | operand_read | L2 | 452 | 451 |
| 4 | execute | L3 | 453 | 452 |
| 5 | prf_writeback | L4 | 454 | 453 |
| 6 | commit | L5 | 455 | 454 |
| 7 | chain_end | — | 1311 | 455 |

### fault 77（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 456 | — |
| 2 | carrier_state | L1 | 457 | 456 |
| 3 | operand_read | L2 | 458 | 457 |
| 4 | execute | L3 | 459 | 458 |
| 5 | prf_writeback | L4 | 460 | 459 |
| 6 | commit | L5 | 461 | 460 |
| 7 | chain_end | — | 1312 | 461 |

### fault 78（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 462 | — |
| 2 | carrier_state | L1 | 463 | 462 |
| 3 | operand_read | L2 | 464 | 463 |
| 4 | execute | L3 | 465 | 464 |
| 5 | prf_writeback | L4 | 466 | 465 |
| 6 | commit | L5 | 467 | 466 |
| 7 | chain_end | — | 1313 | 467 |

### fault 79（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 468 | — |
| 2 | carrier_state | L1 | 469 | 468 |
| 3 | operand_read | L2 | 470 | 469 |
| 4 | execute | L3 | 471 | 470 |
| 5 | prf_writeback | L4 | 472 | 471 |
| 6 | commit | L5 | 473 | 472 |
| 7 | chain_end | — | 1314 | 473 |

### fault 8（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 42 | — |
| 2 | carrier_state | L1 | 43 | 42 |
| 3 | operand_read | L2 | 44 | 43 |
| 4 | execute | L3 | 45 | 44 |
| 5 | prf_writeback | L4 | 46 | 45 |
| 6 | commit | L5 | 47 | 46 |
| 7 | chain_end | — | 1243 | 47 |

### fault 80（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 474 | — |
| 2 | carrier_state | L1 | 475 | 474 |
| 3 | operand_read | L2 | 476 | 475 |
| 4 | execute | L3 | 477 | 476 |
| 5 | prf_writeback | L4 | 478 | 477 |
| 6 | commit | L5 | 479 | 478 |
| 7 | chain_end | — | 1315 | 479 |

### fault 81（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 480 | — |
| 2 | carrier_state | L1 | 481 | 480 |
| 3 | operand_read | L2 | 482 | 481 |
| 4 | execute | L3 | 483 | 482 |
| 5 | prf_writeback | L4 | 484 | 483 |
| 6 | commit | L5 | 485 | 484 |
| 7 | chain_end | — | 1316 | 485 |

### fault 82（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 486 | — |
| 2 | carrier_state | L1 | 487 | 486 |
| 3 | operand_read | L2 | 488 | 487 |
| 4 | execute | L3 | 489 | 488 |
| 5 | prf_writeback | L4 | 490 | 489 |
| 6 | commit | L5 | 491 | 490 |
| 7 | chain_end | — | 1317 | 491 |

### fault 83（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 492 | — |
| 2 | carrier_state | L1 | 493 | 492 |
| 3 | operand_read | L2 | 494 | 493 |
| 4 | execute | L3 | 495 | 494 |
| 5 | prf_writeback | L4 | 496 | 495 |
| 6 | commit | L5 | 497 | 496 |
| 7 | chain_end | — | 1318 | 497 |

### fault 84（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 498 | — |
| 2 | carrier_state | L1 | 499 | 498 |
| 3 | operand_read | L2 | 500 | 499 |
| 4 | execute | L3 | 501 | 500 |
| 5 | prf_writeback | L4 | 502 | 501 |
| 6 | commit | L5 | 503 | 502 |
| 7 | chain_end | — | 1319 | 503 |

### fault 85（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 504 | — |
| 2 | carrier_state | L1 | 505 | 504 |
| 3 | operand_read | L2 | 506 | 505 |
| 4 | execute | L3 | 507 | 506 |
| 5 | prf_writeback | L4 | 508 | 507 |
| 6 | commit | L5 | 509 | 508 |
| 7 | chain_end | — | 1320 | 509 |

### fault 86（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 510 | — |
| 2 | carrier_state | L1 | 511 | 510 |
| 3 | operand_read | L2 | 512 | 511 |
| 4 | execute | L3 | 513 | 512 |
| 5 | prf_writeback | L4 | 514 | 513 |
| 6 | commit | L5 | 515 | 514 |
| 7 | chain_end | — | 1321 | 515 |

### fault 87（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 516 | — |
| 2 | carrier_state | L1 | 517 | 516 |
| 3 | operand_read | L2 | 518 | 517 |
| 4 | execute | L3 | 519 | 518 |
| 5 | prf_writeback | L4 | 520 | 519 |
| 6 | commit | L5 | 521 | 520 |
| 7 | chain_end | — | 1322 | 521 |

### fault 88（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 522 | — |
| 2 | carrier_state | L1 | 523 | 522 |
| 3 | operand_read | L2 | 524 | 523 |
| 4 | execute | L3 | 525 | 524 |
| 5 | prf_writeback | L4 | 526 | 525 |
| 6 | commit | L5 | 527 | 526 |
| 7 | chain_end | — | 1323 | 527 |

### fault 89（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 528 | — |
| 2 | carrier_state | L1 | 529 | 528 |
| 3 | operand_read | L2 | 530 | 529 |
| 4 | execute | L3 | 531 | 530 |
| 5 | prf_writeback | L4 | 532 | 531 |
| 6 | commit | L5 | 533 | 532 |
| 7 | chain_end | — | 1324 | 533 |

### fault 9（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 48 | — |
| 2 | carrier_state | L1 | 49 | 48 |
| 3 | operand_read | L2 | 50 | 49 |
| 4 | execute | L3 | 51 | 50 |
| 5 | prf_writeback | L4 | 52 | 51 |
| 6 | commit | L5 | 53 | 52 |
| 7 | chain_end | — | 1244 | 53 |

### fault 90（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 534 | — |
| 2 | carrier_state | L1 | 535 | 534 |
| 3 | operand_read | L2 | 536 | 535 |
| 4 | execute | L3 | 537 | 536 |
| 5 | prf_writeback | L4 | 538 | 537 |
| 6 | commit | L5 | 539 | 538 |
| 7 | chain_end | — | 1325 | 539 |

### fault 91（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 540 | — |
| 2 | carrier_state | L1 | 541 | 540 |
| 3 | operand_read | L2 | 542 | 541 |
| 4 | execute | L3 | 543 | 542 |
| 5 | prf_writeback | L4 | 544 | 543 |
| 6 | commit | L5 | 545 | 544 |
| 7 | chain_end | — | 1326 | 545 |

### fault 92（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 546 | — |
| 2 | carrier_state | L1 | 547 | 546 |
| 3 | operand_read | L2 | 548 | 547 |
| 4 | execute | L3 | 549 | 548 |
| 5 | prf_writeback | L4 | 550 | 549 |
| 6 | commit | L5 | 551 | 550 |
| 7 | chain_end | — | 1327 | 551 |

### fault 93（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 552 | — |
| 2 | carrier_state | L1 | 553 | 552 |
| 3 | operand_read | L2 | 554 | 553 |
| 4 | execute | L3 | 555 | 554 |
| 5 | prf_writeback | L4 | 556 | 555 |
| 6 | commit | L5 | 557 | 556 |
| 7 | chain_end | — | 1328 | 557 |

### fault 94（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 558 | — |
| 2 | carrier_state | L1 | 559 | 558 |
| 3 | operand_read | L2 | 560 | 559 |
| 4 | execute | L3 | 561 | 560 |
| 5 | prf_writeback | L4 | 562 | 561 |
| 6 | commit | L5 | 563 | 562 |
| 7 | chain_end | — | 1329 | 563 |

### fault 95（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 564 | — |
| 2 | carrier_state | L1 | 565 | 564 |
| 3 | operand_read | L2 | 566 | 565 |
| 4 | execute | L3 | 567 | 566 |
| 5 | prf_writeback | L4 | 568 | 567 |
| 6 | commit | L5 | 569 | 568 |
| 7 | chain_end | — | 1330 | 569 |

### fault 96（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 570 | — |
| 2 | carrier_state | L1 | 571 | 570 |
| 3 | operand_read | L2 | 572 | 571 |
| 4 | execute | L3 | 573 | 572 |
| 5 | prf_writeback | L4 | 574 | 573 |
| 6 | commit | L5 | 575 | 574 |
| 7 | chain_end | — | 1331 | 575 |

### fault 97（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 576 | — |
| 2 | carrier_state | L1 | 577 | 576 |
| 3 | operand_read | L2 | 578 | 577 |
| 4 | execute | L3 | 579 | 578 |
| 5 | prf_writeback | L4 | 580 | 579 |
| 6 | commit | L5 | 581 | 580 |
| 7 | chain_end | — | 1332 | 581 |

### fault 98（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 582 | — |
| 2 | carrier_state | L1 | 583 | 582 |
| 3 | operand_read | L2 | 584 | 583 |
| 4 | execute | L3 | 585 | 584 |
| 5 | prf_writeback | L4 | 586 | 585 |
| 6 | commit | L5 | 587 | 586 |
| 7 | chain_end | — | 1333 | 587 |

### fault 99（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 588 | — |
| 2 | carrier_state | L1 | 589 | 588 |
| 3 | operand_read | L2 | 590 | 589 |
| 4 | execute | L3 | 591 | 590 |
| 5 | prf_writeback | L4 | 592 | 591 |
| 6 | commit | L5 | 593 | 592 |
| 7 | chain_end | — | 1334 | 593 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 29522185 | 1 | 78913 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4075a00000000000→0x4075a00000002000 | — | — | origin |
| carrier_state | 1 | 0 | 29522185 | 1 | 78913 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4075a00000000000→0x4075a00000002000 | — | — | fsu_taint |
| operand_read | 2 | 1 | 29526035 | 1 | 78916 | 0x000000000040065c | fmadd | 78913/78916 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 29526035 | 1 | 78916 | 0x000000000040065c | fmadd | 78913/78916 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 29526035 | 1 | 78916 | 0x000000000040065c | fmadd | 78913/78916 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 29526805 | 1 | 78916 | 0x000000000040065c | fmadd | —/78916 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1236 | 5 | 9405415250 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 54 | — | 201100130 | 10 | 756327 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3ff0a3d70a3d70a4→0x3ff0a3d70a3d70a5 | — | — | origin |
| carrier_state | 55 | 54 | 201100130 | 10 | 756327 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3ff0a3d70a3d70a4→0x3ff0a3d70a3d70a5 | — | — | fsu_taint |
| operand_read | 56 | 55 | 201124385 | 10 | 756434 | 0x0000000000400654 | fmadd | 756327/756434 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 57 | 56 | 201124385 | 10 | 756434 | 0x0000000000400654 | fmadd | 756327/756434 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 58 | 57 | 201124385 | 10 | 756434 | 0x0000000000400654 | fmadd | 756327/756434 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 59 | 58 | 201125155 | 10 | 756434 | 0x0000000000400654 | fmadd | —/756434 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1245 | 59 | 9405415250 | 10 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 594 | — | 1557589880 | 100 | 6108192 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x407f300000000000→0x407f300000000080 | — | — | origin |
| carrier_state | 595 | 594 | 1557589880 | 100 | 6108192 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x407f300000000000→0x407f300000000080 | — | — | fsu_taint |
| operand_read | 596 | 595 | 1557594115 | 100 | 6108195 | 0x0000000000400658 | fmadd | 6108192/6108195 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 597 | 596 | 1557594115 | 100 | 6108195 | 0x0000000000400658 | fmadd | 6108192/6108195 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 598 | 597 | 1557594115 | 100 | 6108195 | 0x0000000000400658 | fmadd | 6108192/6108195 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 599 | 598 | 1557594885 | 100 | 6108195 | 0x0000000000400658 | fmadd | —/6108195 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1335 | 599 | 9405415250 | 100 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 600 | — | 1577297645 | 101 | 6185956 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfd8000000000000→0xbfd8000000000020 | — | — | origin |
| carrier_state | 601 | 600 | 1577297645 | 101 | 6185956 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfd8000000000000→0xbfd8000000000020 | — | — | fsu_taint |
| operand_read | 602 | 601 | 1577313045 | 101 | 6186026 | 0x0000000000400654 | fmadd | 6185956/6186026 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 603 | 602 | 1577313045 | 101 | 6186026 | 0x0000000000400654 | fmadd | 6185956/6186026 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 604 | 603 | 1577313045 | 101 | 6186026 | 0x0000000000400654 | fmadd | 6185956/6186026 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 605 | 604 | 1577313815 | 101 | 6186026 | 0x0000000000400654 | fmadd | —/6186026 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1336 | 605 | 9405415250 | 101 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 606 | — | 1592424680 | 102 | 6245463 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3feb0a3d70a3d70a→0x3feb0a3d70a3d72a | — | — | origin |
| carrier_state | 607 | 606 | 1592424680 | 102 | 6245463 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3feb0a3d70a3d70a→0x3feb0a3d70a3d72a | — | — | fsu_taint |
| operand_read | 608 | 607 | 1592448935 | 102 | 6245570 | 0x0000000000400654 | fmadd | 6245463/6245570 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 609 | 608 | 1592448935 | 102 | 6245570 | 0x0000000000400654 | fmadd | 6245463/6245570 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 610 | 609 | 1592448935 | 102 | 6245570 | 0x0000000000400654 | fmadd | 6245463/6245570 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 611 | 610 | 1592449705 | 102 | 6245570 | 0x0000000000400654 | fmadd | —/6245570 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1337 | 611 | 9405415250 | 102 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 612 | — | 1612932860 | 103 | 6326605 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x408a680000000000→0x408a680000008000 | — | — | origin |
| carrier_state | 613 | 612 | 1612932860 | 103 | 6326605 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x408a680000000000→0x408a680000008000 | — | — | fsu_taint |
| operand_read | 614 | 613 | 1612936710 | 103 | 6326608 | 0x000000000040065c | fmadd | 6326605/6326608 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 615 | 614 | 1612936710 | 103 | 6326608 | 0x000000000040065c | fmadd | 6326605/6326608 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 616 | 615 | 1612936710 | 103 | 6326608 | 0x000000000040065c | fmadd | 6326605/6326608 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 617 | 616 | 1612937480 | 103 | 6326608 | 0x000000000040065c | fmadd | —/6326608 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1338 | 617 | 9405415250 | 103 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 618 | — | 1631670040 | 104 | 6400408 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfd4395810624dd3→0xbfd4395810634dd3 | — | — | origin |
| carrier_state | 619 | 618 | 1631670040 | 104 | 6400408 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfd4395810624dd3→0xbfd4395810634dd3 | — | — | fsu_taint |
| operand_read | 620 | 619 | 1631685440 | 104 | 6400478 | 0x0000000000400654 | fmadd | 6400408/6400478 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 621 | 620 | 1631685440 | 104 | 6400478 | 0x0000000000400654 | fmadd | 6400408/6400478 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 622 | 621 | 1631685440 | 104 | 6400478 | 0x0000000000400654 | fmadd | 6400408/6400478 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 623 | 622 | 1631686210 | 104 | 6400478 | 0x0000000000400654 | fmadd | —/6400478 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1339 | 623 | 9405415250 | 104 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 624 | — | 1650359480 | 105 | 6474062 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3feda1cac083126f→0x3feda1cac083127f | — | — | origin |
| carrier_state | 625 | 624 | 1650359480 | 105 | 6474062 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3feda1cac083126f→0x3feda1cac083127f | — | — | fsu_taint |
| operand_read | 626 | 625 | 1650394900 | 105 | 6474206 | 0x0000000000400654 | fmadd | 6474062/6474206 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 627 | 626 | 1650394900 | 105 | 6474206 | 0x0000000000400654 | fmadd | 6474062/6474206 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 628 | 627 | 1650394900 | 105 | 6474206 | 0x0000000000400654 | fmadd | 6474062/6474206 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 629 | 628 | 1650395670 | 105 | 6474206 | 0x0000000000400654 | fmadd | —/6474206 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1340 | 629 | 9405415250 | 105 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 630 | — | 1669494750 | 106 | 6549446 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff4ed916872b021→0x3ff4ed916872b061 | — | — | origin |
| carrier_state | 631 | 630 | 1669494750 | 106 | 6549446 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff4ed916872b021→0x3ff4ed916872b061 | — | — | fsu_taint |
| operand_read | 632 | 631 | 1669530170 | 106 | 6549590 | 0x0000000000400654 | fmadd | 6549446/6549590 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 633 | 632 | 1669530170 | 106 | 6549590 | 0x0000000000400654 | fmadd | 6549446/6549590 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 634 | 633 | 1669530170 | 106 | 6549590 | 0x0000000000400654 | fmadd | 6549446/6549590 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 635 | 634 | 1669530940 | 106 | 6549590 | 0x0000000000400654 | fmadd | —/6549590 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1341 | 635 | 9405415250 | 106 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 636 | — | 1688739360 | 107 | 6625694 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff0ac083126e979→0x3ff0ac083126ed79 | — | — | origin |
| carrier_state | 637 | 636 | 1688739360 | 107 | 6625694 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff0ac083126e979→0x3ff0ac083126ed79 | — | — | fsu_taint |
| operand_read | 638 | 637 | 1688774780 | 107 | 6625838 | 0x0000000000400654 | fmadd | 6625694/6625838 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 639 | 638 | 1688774780 | 107 | 6625838 | 0x0000000000400654 | fmadd | 6625694/6625838 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 640 | 639 | 1688774780 | 107 | 6625838 | 0x0000000000400654 | fmadd | 6625694/6625838 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 641 | 640 | 1688775550 | 107 | 6625838 | 0x0000000000400654 | fmadd | —/6625838 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1342 | 641 | 9405415250 | 107 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 642 | — | 1707196645 | 108 | 6698519 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4070300000000000→0x4070300000004000 | — | — | origin |
| carrier_state | 643 | 642 | 1707196645 | 108 | 6698519 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4070300000000000→0x4070300000004000 | — | — | fsu_taint |
| operand_read | 644 | 643 | 1707198570 | 108 | 6698522 | 0x0000000000400654 | fmadd | 6698519/6698522 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 645 | 644 | 1707198570 | 108 | 6698522 | 0x0000000000400654 | fmadd | 6698519/6698522 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 646 | 645 | 1707198570 | 108 | 6698522 | 0x0000000000400654 | fmadd | 6698519/6698522 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 647 | 646 | 1707199340 | 108 | 6698522 | 0x0000000000400654 | fmadd | —/6698522 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1343 | 647 | 9405415250 | 108 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 648 | — | 1716808940 | 109 | 6736252 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fa810624dd2f1ac→0x3fa810624dd271ac | — | — | origin |
| carrier_state | 649 | 648 | 1716808940 | 109 | 6736252 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fa810624dd2f1ac→0x3fa810624dd271ac | — | — | fsu_taint |
| operand_read | 650 | 649 | 1716824340 | 109 | 6736322 | 0x0000000000400654 | fmadd | 6736252/6736322 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 651 | 650 | 1716824340 | 109 | 6736322 | 0x0000000000400654 | fmadd | 6736252/6736322 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 652 | 651 | 1716824340 | 109 | 6736322 | 0x0000000000400654 | fmadd | 6736252/6736322 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 653 | 652 | 1716825110 | 109 | 6736322 | 0x0000000000400654 | fmadd | —/6736322 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1344 | 653 | 9405415250 | 109 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 60 | — | 220419430 | 11 | 832285 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4074000000000000→0x4074000000000004 | — | — | origin |
| carrier_state | 61 | 60 | 220419430 | 11 | 832285 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4074000000000000→0x4074000000000004 | — | — | fsu_taint |
| operand_read | 62 | 61 | 220423280 | 11 | 832288 | 0x000000000040065c | fmadd | 832285/832288 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 63 | 62 | 220423280 | 11 | 832288 | 0x000000000040065c | fmadd | 832285/832288 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 64 | 63 | 220423280 | 11 | 832288 | 0x000000000040065c | fmadd | 832285/832288 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 65 | 64 | 220424050 | 11 | 832288 | 0x000000000040065c | fmadd | —/832288 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1246 | 65 | 9405415250 | 11 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 654 | — | 1728940290 | 110 | 6784058 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff2ed916872b021→0x3ff2ed916872b0a1 | — | — | origin |
| carrier_state | 655 | 654 | 1728940290 | 110 | 6784058 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff2ed916872b021→0x3ff2ed916872b0a1 | — | — | fsu_taint |
| operand_read | 656 | 655 | 1728975710 | 110 | 6784202 | 0x0000000000400654 | fmadd | 6784058/6784202 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 657 | 656 | 1728975710 | 110 | 6784202 | 0x0000000000400654 | fmadd | 6784058/6784202 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 658 | 657 | 1728975710 | 110 | 6784202 | 0x0000000000400654 | fmadd | 6784058/6784202 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 659 | 658 | 1728976480 | 110 | 6784202 | 0x0000000000400654 | fmadd | —/6784202 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1345 | 659 | 9405415250 | 110 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 660 | — | 1749103125 | 111 | 6863728 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfd79db22d0e5604→0xbfd79db22d0e5606 | — | — | origin |
| carrier_state | 661 | 660 | 1749103125 | 111 | 6863728 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfd79db22d0e5604→0xbfd79db22d0e5606 | — | — | fsu_taint |
| operand_read | 662 | 661 | 1749118525 | 111 | 6863798 | 0x0000000000400654 | fmadd | 6863728/6863798 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 663 | 662 | 1749118525 | 111 | 6863798 | 0x0000000000400654 | fmadd | 6863728/6863798 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 664 | 663 | 1749118525 | 111 | 6863798 | 0x0000000000400654 | fmadd | 6863728/6863798 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 665 | 664 | 1749119295 | 111 | 6863798 | 0x0000000000400654 | fmadd | —/6863798 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1346 | 665 | 9405415250 | 111 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 666 | — | 1760357445 | 112 | 6907683 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fd916872b020c4a→0x3fd916872b022c4a | — | — | origin |
| carrier_state | 667 | 666 | 1760357445 | 112 | 6907683 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fd916872b020c4a→0x3fd916872b022c4a | — | — | fsu_taint |
| operand_read | 668 | 667 | 1760381700 | 112 | 6907790 | 0x0000000000400654 | fmadd | 6907683/6907790 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 669 | 668 | 1760381700 | 112 | 6907790 | 0x0000000000400654 | fmadd | 6907683/6907790 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 670 | 669 | 1760381700 | 112 | 6907790 | 0x0000000000400654 | fmadd | 6907683/6907790 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 671 | 670 | 1760382470 | 112 | 6907790 | 0x0000000000400654 | fmadd | —/6907790 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1347 | 671 | 9405415250 | 112 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 672 | — | 1781856615 | 113 | 6993107 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4086a00000000000→0x4086a00000020000 | — | — | origin |
| carrier_state | 673 | 672 | 1781856615 | 113 | 6993107 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4086a00000000000→0x4086a00000020000 | — | — | fsu_taint |
| operand_read | 674 | 673 | 1781858540 | 113 | 6993110 | 0x0000000000400654 | fmadd | 6993107/6993110 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 675 | 674 | 1781858540 | 113 | 6993110 | 0x0000000000400654 | fmadd | 6993107/6993110 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 676 | 675 | 1781858540 | 113 | 6993110 | 0x0000000000400654 | fmadd | 6993107/6993110 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 677 | 676 | 1781859310 | 113 | 6993110 | 0x0000000000400654 | fmadd | —/6993110 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1348 | 677 | 9405415250 | 113 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 678 | — | 1794758350 | 114 | 7043689 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4081400000000000→0x4081400000008000 | — | — | origin |
| carrier_state | 679 | 678 | 1794758350 | 114 | 7043689 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4081400000000000→0x4081400000008000 | — | — | fsu_taint |
| operand_read | 680 | 679 | 1794762200 | 114 | 7043692 | 0x000000000040065c | fmadd | 7043689/7043692 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 681 | 680 | 1794762200 | 114 | 7043692 | 0x000000000040065c | fmadd | 7043689/7043692 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 682 | 681 | 1794762200 | 114 | 7043692 | 0x000000000040065c | fmadd | 7043689/7043692 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 683 | 682 | 1794762970 | 114 | 7043692 | 0x000000000040065c | fmadd | —/7043692 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1349 | 683 | 9405415250 | 114 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 684 | — | 1812214635 | 115 | 7112451 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe604189374bc6b→0x3fe604189374bc69 | — | — | origin |
| carrier_state | 685 | 684 | 1812214635 | 115 | 7112451 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe604189374bc6b→0x3fe604189374bc69 | — | — | fsu_taint |
| operand_read | 686 | 685 | 1812238890 | 115 | 7112558 | 0x0000000000400654 | fmadd | 7112451/7112558 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 687 | 686 | 1812238890 | 115 | 7112558 | 0x0000000000400654 | fmadd | 7112451/7112558 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 688 | 687 | 1812238890 | 115 | 7112558 | 0x0000000000400654 | fmadd | 7112451/7112558 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 689 | 688 | 1812239660 | 115 | 7112558 | 0x0000000000400654 | fmadd | —/7112558 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1350 | 689 | 9405415250 | 115 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 690 | — | 1822843330 | 116 | 7154642 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fe2978d4fdf3b64→0x3fe2978d4fdf3a64 | — | — | origin |
| carrier_state | 691 | 690 | 1822843330 | 116 | 7154642 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fe2978d4fdf3b64→0x3fe2978d4fdf3a64 | — | — | fsu_taint |
| operand_read | 692 | 691 | 1822878750 | 116 | 7154786 | 0x0000000000400654 | fmadd | 7154642/7154786 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 693 | 692 | 1822878750 | 116 | 7154786 | 0x0000000000400654 | fmadd | 7154642/7154786 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 694 | 693 | 1822878750 | 116 | 7154786 | 0x0000000000400654 | fmadd | 7154642/7154786 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 695 | 694 | 1822879520 | 116 | 7154786 | 0x0000000000400654 | fmadd | —/7154786 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1351 | 695 | 9405415250 | 116 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 696 | — | 1838853170 | 117 | 7218074 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff70624dd2f1aa0→0x3ff70624dd2f1ae0 | — | — | origin |
| carrier_state | 697 | 696 | 1838853170 | 117 | 7218074 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff70624dd2f1aa0→0x3ff70624dd2f1ae0 | — | — | fsu_taint |
| operand_read | 698 | 697 | 1838888590 | 117 | 7218218 | 0x0000000000400654 | fmadd | 7218074/7218218 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 699 | 698 | 1838888590 | 117 | 7218218 | 0x0000000000400654 | fmadd | 7218074/7218218 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 700 | 699 | 1838888590 | 117 | 7218218 | 0x0000000000400654 | fmadd | 7218074/7218218 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 701 | 700 | 1838889360 | 117 | 7218218 | 0x0000000000400654 | fmadd | —/7218218 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1352 | 701 | 9405415250 | 117 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 702 | — | 1858230990 | 118 | 7294359 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fd6666666666666→0x3fd6666666666266 | — | — | origin |
| carrier_state | 703 | 702 | 1858230990 | 118 | 7294359 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fd6666666666666→0x3fd6666666666266 | — | — | fsu_taint |
| operand_read | 704 | 703 | 1858363045 | 118 | 7294466 | 0x0000000000400654 | fmadd | 7294359/7294466 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 705 | 704 | 1858363045 | 118 | 7294466 | 0x0000000000400654 | fmadd | 7294359/7294466 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 706 | 705 | 1858363045 | 118 | 7294466 | 0x0000000000400654 | fmadd | 7294359/7294466 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 707 | 706 | 1858363815 | 118 | 7294466 | 0x0000000000400654 | fmadd | —/7294466 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1353 | 707 | 9405415250 | 118 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 708 | — | 1870480920 | 119 | 7342741 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x408a500000000000→0x408a500000004000 | — | — | origin |
| carrier_state | 709 | 708 | 1870480920 | 119 | 7342741 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x408a500000000000→0x408a500000004000 | — | — | fsu_taint |
| operand_read | 710 | 709 | 1870484770 | 119 | 7342744 | 0x000000000040065c | fmadd | 7342741/7342744 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 711 | 710 | 1870484770 | 119 | 7342744 | 0x000000000040065c | fmadd | 7342741/7342744 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 712 | 711 | 1870484770 | 119 | 7342744 | 0x000000000040065c | fmadd | 7342741/7342744 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 713 | 712 | 1870485540 | 119 | 7342744 | 0x000000000040065c | fmadd | —/7342744 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1354 | 713 | 9405415250 | 119 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 66 | — | 232746360 | 12 | 880991 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4081680000000000→0x4081680000000008 | — | — | origin |
| carrier_state | 67 | 66 | 232746360 | 12 | 880991 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4081680000000000→0x4081680000000008 | — | — | fsu_taint |
| operand_read | 68 | 67 | 232748285 | 12 | 880994 | 0x0000000000400654 | fmadd | 880991/880994 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 69 | 68 | 232748285 | 12 | 880994 | 0x0000000000400654 | fmadd | 880991/880994 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 70 | 69 | 232748285 | 12 | 880994 | 0x0000000000400654 | fmadd | 880991/880994 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 71 | 70 | 232749055 | 12 | 880994 | 0x0000000000400654 | fmadd | —/880994 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1247 | 71 | 9405415250 | 12 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 714 | — | 1879822175 | 120 | 7379283 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe7020c49ba5e35→0x3fe7020c49ba4e35 | — | — | origin |
| carrier_state | 715 | 714 | 1879822175 | 120 | 7379283 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe7020c49ba5e35→0x3fe7020c49ba4e35 | — | — | fsu_taint |
| operand_read | 716 | 715 | 1879846430 | 120 | 7379390 | 0x0000000000400654 | fmadd | 7379283/7379390 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 717 | 716 | 1879846430 | 120 | 7379390 | 0x0000000000400654 | fmadd | 7379283/7379390 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 718 | 717 | 1879846430 | 120 | 7379390 | 0x0000000000400654 | fmadd | 7379283/7379390 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 719 | 718 | 1879847200 | 120 | 7379390 | 0x0000000000400654 | fmadd | —/7379390 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1355 | 719 | 9405415250 | 120 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 720 | — | 1901959290 | 121 | 7466435 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x4020000000000000→0x4020000000000010 | — | — | origin |
| carrier_state | 721 | 720 | 1901959290 | 121 | 7466435 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x4020000000000000→0x4020000000000010 | — | — | fsu_taint |
| operand_read | 722 | 721 | 1901961215 | 121 | 7466438 | 0x0000000000400654 | fmadd | 7466435/7466438 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 723 | 722 | 1901961215 | 121 | 7466438 | 0x0000000000400654 | fmadd | 7466435/7466438 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 724 | 723 | 1901961215 | 121 | 7466438 | 0x0000000000400654 | fmadd | 7466435/7466438 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 725 | 724 | 1901961985 | 121 | 7466438 | 0x0000000000400654 | fmadd | —/7466438 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1356 | 725 | 9405415250 | 121 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 726 | — | 1918391860 | 122 | 7531707 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff2c49ba5e353f8→0x3ff2c49ba5e35378 | — | — | origin |
| carrier_state | 727 | 726 | 1918391860 | 122 | 7531707 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff2c49ba5e353f8→0x3ff2c49ba5e35378 | — | — | fsu_taint |
| operand_read | 728 | 727 | 1918416115 | 122 | 7531814 | 0x0000000000400654 | fmadd | 7531707/7531814 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 729 | 728 | 1918416115 | 122 | 7531814 | 0x0000000000400654 | fmadd | 7531707/7531814 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 730 | 729 | 1918416115 | 122 | 7531814 | 0x0000000000400654 | fmadd | 7531707/7531814 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 731 | 730 | 1918416885 | 122 | 7531814 | 0x0000000000400654 | fmadd | —/7531814 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1357 | 731 | 9405415250 | 122 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 732 | — | 1926734040 | 123 | 7564535 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4064600000000000→0x4064600000000800 | — | — | origin |
| carrier_state | 733 | 732 | 1926734040 | 123 | 7564535 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4064600000000000→0x4064600000000800 | — | — | fsu_taint |
| operand_read | 734 | 733 | 1926735965 | 123 | 7564538 | 0x0000000000400654 | fmadd | 7564535/7564538 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 735 | 734 | 1926735965 | 123 | 7564538 | 0x0000000000400654 | fmadd | 7564535/7564538 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 736 | 735 | 1926735965 | 123 | 7564538 | 0x0000000000400654 | fmadd | 7564535/7564538 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 737 | 736 | 1926736735 | 123 | 7564538 | 0x0000000000400654 | fmadd | —/7564538 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1358 | 737 | 9405415250 | 123 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 738 | — | 1943198565 | 124 | 7629481 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4075700000000000→0x4075700000000800 | — | — | origin |
| carrier_state | 739 | 738 | 1943198565 | 124 | 7629481 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4075700000000000→0x4075700000000800 | — | — | fsu_taint |
| operand_read | 740 | 739 | 1943202415 | 124 | 7629484 | 0x000000000040065c | fmadd | 7629481/7629484 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 741 | 740 | 1943202415 | 124 | 7629484 | 0x000000000040065c | fmadd | 7629481/7629484 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 742 | 741 | 1943202415 | 124 | 7629484 | 0x000000000040065c | fmadd | 7629481/7629484 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 743 | 742 | 1943203185 | 124 | 7629484 | 0x000000000040065c | fmadd | —/7629484 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1359 | 743 | 9405415250 | 124 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 744 | — | 1953893095 | 125 | 7671531 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fd7ae147ae147ae→0x3fd7ae147ae14fae | — | — | origin |
| carrier_state | 745 | 744 | 1953893095 | 125 | 7671531 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fd7ae147ae147ae→0x3fd7ae147ae14fae | — | — | fsu_taint |
| operand_read | 746 | 745 | 1953917350 | 125 | 7671638 | 0x0000000000400654 | fmadd | 7671531/7671638 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 747 | 746 | 1953917350 | 125 | 7671638 | 0x0000000000400654 | fmadd | 7671531/7671638 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 748 | 747 | 1953917350 | 125 | 7671638 | 0x0000000000400654 | fmadd | 7671531/7671638 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 749 | 748 | 1953918120 | 125 | 7671638 | 0x0000000000400654 | fmadd | —/7671638 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1360 | 749 | 9405415250 | 125 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 750 | — | 1969683485 | 126 | 7734275 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4083800000000000→0x4083800000000800 | — | — | origin |
| carrier_state | 751 | 750 | 1969683485 | 126 | 7734275 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4083800000000000→0x4083800000000800 | — | — | fsu_taint |
| operand_read | 752 | 751 | 1969685410 | 126 | 7734278 | 0x0000000000400654 | fmadd | 7734275/7734278 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 753 | 752 | 1969685410 | 126 | 7734278 | 0x0000000000400654 | fmadd | 7734275/7734278 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 754 | 753 | 1969685410 | 126 | 7734278 | 0x0000000000400654 | fmadd | 7734275/7734278 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 755 | 754 | 1969686180 | 126 | 7734278 | 0x0000000000400654 | fmadd | —/7734278 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1361 | 755 | 9405415250 | 126 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 756 | — | 1982832005 | 127 | 7786011 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe2b020c49ba5e3→0x3fe2b020c49ba563 | — | — | origin |
| carrier_state | 757 | 756 | 1982832005 | 127 | 7786011 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe2b020c49ba5e3→0x3fe2b020c49ba563 | — | — | fsu_taint |
| operand_read | 758 | 757 | 1982856260 | 127 | 7786118 | 0x0000000000400654 | fmadd | 7786011/7786118 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 759 | 758 | 1982856260 | 127 | 7786118 | 0x0000000000400654 | fmadd | 7786011/7786118 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 760 | 759 | 1982856260 | 127 | 7786118 | 0x0000000000400654 | fmadd | 7786011/7786118 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 761 | 760 | 1982857030 | 127 | 7786118 | 0x0000000000400654 | fmadd | —/7786118 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1362 | 761 | 9405415250 | 127 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 762 | — | 2004957185 | 128 | 7873131 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff14bc6a7ef9db2→0x3ff14bc6a7efddb2 | — | — | origin |
| carrier_state | 763 | 762 | 2004957185 | 128 | 7873131 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff14bc6a7ef9db2→0x3ff14bc6a7efddb2 | — | — | fsu_taint |
| operand_read | 764 | 763 | 2004981440 | 128 | 7873238 | 0x0000000000400654 | fmadd | 7873131/7873238 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 765 | 764 | 2004981440 | 128 | 7873238 | 0x0000000000400654 | fmadd | 7873131/7873238 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 766 | 765 | 2004981440 | 128 | 7873238 | 0x0000000000400654 | fmadd | 7873131/7873238 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 767 | 766 | 2004982210 | 128 | 7873238 | 0x0000000000400654 | fmadd | —/7873238 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1363 | 767 | 9405415250 | 128 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 768 | — | 2026548755 | 129 | 7958092 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3f90624dd2f1a9ff→0x3f90624dd2f1adff | — | — | origin |
| carrier_state | 769 | 768 | 2026548755 | 129 | 7958092 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3f90624dd2f1a9ff→0x3f90624dd2f1adff | — | — | fsu_taint |
| operand_read | 770 | 769 | 2026564155 | 129 | 7958162 | 0x0000000000400654 | fmadd | 7958092/7958162 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 771 | 770 | 2026564155 | 129 | 7958162 | 0x0000000000400654 | fmadd | 7958092/7958162 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 772 | 771 | 2026564155 | 129 | 7958162 | 0x0000000000400654 | fmadd | 7958092/7958162 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 773 | 772 | 2026564925 | 129 | 7958162 | 0x0000000000400654 | fmadd | —/7958162 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1364 | 773 | 9405415250 | 129 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 72 | — | 252022155 | 13 | 956880 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4088c00000000000→0x4088c00000000400 | — | — | origin |
| carrier_state | 73 | 72 | 252022155 | 13 | 956880 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4088c00000000000→0x4088c00000000400 | — | — | fsu_taint |
| operand_read | 74 | 73 | 252026390 | 13 | 956883 | 0x0000000000400658 | fmadd | 956880/956883 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 75 | 74 | 252026390 | 13 | 956883 | 0x0000000000400658 | fmadd | 956880/956883 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 76 | 75 | 252026390 | 13 | 956883 | 0x0000000000400658 | fmadd | 956880/956883 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 77 | 76 | 252027160 | 13 | 956883 | 0x0000000000400658 | fmadd | —/956883 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1248 | 77 | 9405415250 | 13 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 774 | — | 2049093200 | 130 | 8047405 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x408e000000000000→0x408e000000000008 | — | — | origin |
| carrier_state | 775 | 774 | 2049093200 | 130 | 8047405 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x408e000000000000→0x408e000000000008 | — | — | fsu_taint |
| operand_read | 776 | 775 | 2049097050 | 130 | 8047408 | 0x000000000040065c | fmadd | 8047405/8047408 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 777 | 776 | 2049097050 | 130 | 8047408 | 0x000000000040065c | fmadd | 8047405/8047408 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 778 | 777 | 2049097050 | 130 | 8047408 | 0x000000000040065c | fmadd | 8047405/8047408 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 779 | 778 | 2049097820 | 130 | 8047408 | 0x000000000040065c | fmadd | —/8047408 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1365 | 779 | 9405415250 | 130 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 780 | — | 2065336735 | 131 | 8111017 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x408bb80000000000→0x408bb80000008000 | — | — | origin |
| carrier_state | 781 | 780 | 2065336735 | 131 | 8111017 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x408bb80000000000→0x408bb80000008000 | — | — | fsu_taint |
| operand_read | 782 | 781 | 2065340585 | 131 | 8111020 | 0x000000000040065c | fmadd | 8111017/8111020 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 783 | 782 | 2065340585 | 131 | 8111020 | 0x000000000040065c | fmadd | 8111017/8111020 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 784 | 783 | 2065340585 | 131 | 8111020 | 0x000000000040065c | fmadd | 8111017/8111020 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 785 | 784 | 2065341355 | 131 | 8111020 | 0x000000000040065c | fmadd | —/8111020 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1366 | 785 | 9405415250 | 131 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 786 | — | 2086976045 | 132 | 8196988 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fdbc6a7ef9db22d→0x3fdbc6a7ef9db32d | — | — | origin |
| carrier_state | 787 | 786 | 2086976045 | 132 | 8196988 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fdbc6a7ef9db22d→0x3fdbc6a7ef9db32d | — | — | fsu_taint |
| operand_read | 788 | 787 | 2086991445 | 132 | 8197058 | 0x0000000000400654 | fmadd | 8196988/8197058 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 789 | 788 | 2086991445 | 132 | 8197058 | 0x0000000000400654 | fmadd | 8196988/8197058 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 790 | 789 | 2086991445 | 132 | 8197058 | 0x0000000000400654 | fmadd | 8196988/8197058 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 791 | 790 | 2086992215 | 132 | 8197058 | 0x0000000000400654 | fmadd | —/8197058 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1367 | 791 | 9405415250 | 132 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 792 | — | 2101524040 | 133 | 8253940 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd3d70a3d70a3d7→0xbfd3d70a3d70b3d7 | — | — | origin |
| carrier_state | 793 | 792 | 2101524040 | 133 | 8253940 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd3d70a3d70a3d7→0xbfd3d70a3d70b3d7 | — | — | fsu_taint |
| operand_read | 794 | 793 | 2101539440 | 133 | 8254010 | 0x0000000000400654 | fmadd | 8253940/8254010 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 795 | 794 | 2101539440 | 133 | 8254010 | 0x0000000000400654 | fmadd | 8253940/8254010 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 796 | 795 | 2101539440 | 133 | 8254010 | 0x0000000000400654 | fmadd | 8253940/8254010 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 797 | 796 | 2101540210 | 133 | 8254010 | 0x0000000000400654 | fmadd | —/8254010 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1368 | 797 | 9405415250 | 133 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 798 | — | 2116472050 | 134 | 8312869 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x408a900000000000→0x408a900000000008 | — | — | origin |
| carrier_state | 799 | 798 | 2116472050 | 134 | 8312869 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x408a900000000000→0x408a900000000008 | — | — | fsu_taint |
| operand_read | 800 | 799 | 2116475900 | 134 | 8312872 | 0x000000000040065c | fmadd | 8312869/8312872 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 801 | 800 | 2116475900 | 134 | 8312872 | 0x000000000040065c | fmadd | 8312869/8312872 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 802 | 801 | 2116475900 | 134 | 8312872 | 0x000000000040065c | fmadd | 8312869/8312872 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 803 | 802 | 2116476670 | 134 | 8312872 | 0x000000000040065c | fmadd | —/8312872 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1369 | 803 | 9405415250 | 134 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 804 | — | 2138741220 | 135 | 8400635 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4080300000000000→0x4080300000000400 | — | — | origin |
| carrier_state | 805 | 804 | 2138741220 | 135 | 8400635 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4080300000000000→0x4080300000000400 | — | — | fsu_taint |
| operand_read | 806 | 805 | 2138743145 | 135 | 8400638 | 0x0000000000400654 | fmadd | 8400635/8400638 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 807 | 806 | 2138743145 | 135 | 8400638 | 0x0000000000400654 | fmadd | 8400635/8400638 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 808 | 807 | 2138743145 | 135 | 8400638 | 0x0000000000400654 | fmadd | 8400635/8400638 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 809 | 808 | 2138743915 | 135 | 8400638 | 0x0000000000400654 | fmadd | —/8400638 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1370 | 809 | 9405415250 | 135 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 810 | — | 2149116200 | 136 | 8441820 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x407fc00000000000→0x407fc00000004000 | — | — | origin |
| carrier_state | 811 | 810 | 2149116200 | 136 | 8441820 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x407fc00000000000→0x407fc00000004000 | — | — | fsu_taint |
| operand_read | 812 | 811 | 2149120435 | 136 | 8441823 | 0x0000000000400658 | fmadd | 8441820/8441823 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 813 | 812 | 2149120435 | 136 | 8441823 | 0x0000000000400658 | fmadd | 8441820/8441823 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 814 | 813 | 2149120435 | 136 | 8441823 | 0x0000000000400658 | fmadd | 8441820/8441823 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 815 | 814 | 2149121205 | 136 | 8441823 | 0x0000000000400658 | fmadd | —/8441823 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1371 | 815 | 9405415250 | 136 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 816 | — | 2158648030 | 137 | 8479299 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3febbe76c8b43958→0x3febbe76c8b42958 | — | — | origin |
| carrier_state | 817 | 816 | 2158648030 | 137 | 8479299 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3febbe76c8b43958→0x3febbe76c8b42958 | — | — | fsu_taint |
| operand_read | 818 | 817 | 2158672285 | 137 | 8479406 | 0x0000000000400654 | fmadd | 8479299/8479406 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 819 | 818 | 2158672285 | 137 | 8479406 | 0x0000000000400654 | fmadd | 8479299/8479406 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 820 | 819 | 2158672285 | 137 | 8479406 | 0x0000000000400654 | fmadd | 8479299/8479406 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 821 | 820 | 2158673055 | 137 | 8479406 | 0x0000000000400654 | fmadd | —/8479406 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1372 | 821 | 9405415250 | 137 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 822 | — | 2169908510 | 138 | 8524083 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3feb0a3d70a3d70a→0x3feb0a3d70a3d50a | — | — | origin |
| carrier_state | 823 | 822 | 2169908510 | 138 | 8524083 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3feb0a3d70a3d70a→0x3feb0a3d70a3d50a | — | — | fsu_taint |
| operand_read | 824 | 823 | 2169932765 | 138 | 8524190 | 0x0000000000400654 | fmadd | 8524083/8524190 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 825 | 824 | 2169932765 | 138 | 8524190 | 0x0000000000400654 | fmadd | 8524083/8524190 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 826 | 825 | 2169932765 | 138 | 8524190 | 0x0000000000400654 | fmadd | 8524083/8524190 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 827 | 826 | 2169933535 | 138 | 8524190 | 0x0000000000400654 | fmadd | —/8524190 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1373 | 827 | 9405415250 | 138 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 828 | — | 2179623985 | 139 | 8562600 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x407b200000000000→0x407b200000008000 | — | — | origin |
| carrier_state | 829 | 828 | 2179623985 | 139 | 8562600 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x407b200000000000→0x407b200000008000 | — | — | fsu_taint |
| operand_read | 830 | 829 | 2179628220 | 139 | 8562603 | 0x0000000000400658 | fmadd | 8562600/8562603 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 831 | 830 | 2179628220 | 139 | 8562603 | 0x0000000000400658 | fmadd | 8562600/8562603 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 832 | 831 | 2179628220 | 139 | 8562603 | 0x0000000000400658 | fmadd | 8562600/8562603 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 833 | 832 | 2179628990 | 139 | 8562603 | 0x0000000000400658 | fmadd | —/8562603 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1374 | 833 | 9405415250 | 139 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 78 | — | 273700350 | 14 | 1042631 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4047800000000000→0x4047800000020000 | — | — | origin |
| carrier_state | 79 | 78 | 273700350 | 14 | 1042631 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4047800000000000→0x4047800000020000 | — | — | fsu_taint |
| operand_read | 80 | 79 | 273702275 | 14 | 1042634 | 0x0000000000400654 | fmadd | 1042631/1042634 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 81 | 80 | 273702275 | 14 | 1042634 | 0x0000000000400654 | fmadd | 1042631/1042634 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 82 | 81 | 273702275 | 14 | 1042634 | 0x0000000000400654 | fmadd | 1042631/1042634 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 83 | 82 | 273703045 | 14 | 1042634 | 0x0000000000400654 | fmadd | —/1042634 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1249 | 83 | 9405415250 | 14 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 834 | — | 2201013430 | 140 | 8646699 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fe5810624dd2f1b→0x3fe5810624dd2d1b | — | — | origin |
| carrier_state | 835 | 834 | 2201013430 | 140 | 8646699 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fe5810624dd2f1b→0x3fe5810624dd2d1b | — | — | fsu_taint |
| operand_read | 836 | 835 | 2201037685 | 140 | 8646806 | 0x0000000000400654 | fmadd | 8646699/8646806 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 837 | 836 | 2201037685 | 140 | 8646806 | 0x0000000000400654 | fmadd | 8646699/8646806 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 838 | 837 | 2201037685 | 140 | 8646806 | 0x0000000000400654 | fmadd | 8646699/8646806 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 839 | 838 | 2201038455 | 140 | 8646806 | 0x0000000000400654 | fmadd | —/8646806 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1375 | 839 | 9405415250 | 140 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 840 | — | 2213219085 | 141 | 8694899 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4076c00000000000→0x4076c00000008000 | — | — | origin |
| carrier_state | 841 | 840 | 2213219085 | 141 | 8694899 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4076c00000000000→0x4076c00000008000 | — | — | fsu_taint |
| operand_read | 842 | 841 | 2213221010 | 141 | 8694902 | 0x0000000000400654 | fmadd | 8694899/8694902 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 843 | 842 | 2213221010 | 141 | 8694902 | 0x0000000000400654 | fmadd | 8694899/8694902 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 844 | 843 | 2213221010 | 141 | 8694902 | 0x0000000000400654 | fmadd | 8694899/8694902 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 845 | 844 | 2213221780 | 141 | 8694902 | 0x0000000000400654 | fmadd | —/8694902 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1376 | 845 | 9405415250 | 141 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 846 | — | 2230099025 | 142 | 8761211 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x408eb00000000000→0x408eb00000002000 | — | — | origin |
| carrier_state | 847 | 846 | 2230099025 | 142 | 8761211 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x408eb00000000000→0x408eb00000002000 | — | — | fsu_taint |
| operand_read | 848 | 847 | 2230100950 | 142 | 8761214 | 0x0000000000400654 | fmadd | 8761211/8761214 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 849 | 848 | 2230100950 | 142 | 8761214 | 0x0000000000400654 | fmadd | 8761211/8761214 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 850 | 849 | 2230100950 | 142 | 8761214 | 0x0000000000400654 | fmadd | 8761211/8761214 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 851 | 850 | 2230101720 | 142 | 8761214 | 0x0000000000400654 | fmadd | —/8761214 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1377 | 851 | 9405415250 | 142 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 852 | — | 2248849680 | 143 | 8835446 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff26e978d4fdf3b→0x3ff26e978d4f9f3b | — | — | origin |
| carrier_state | 853 | 852 | 2248849680 | 143 | 8835446 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff26e978d4fdf3b→0x3ff26e978d4f9f3b | — | — | fsu_taint |
| operand_read | 854 | 853 | 2248885100 | 143 | 8835590 | 0x0000000000400654 | fmadd | 8835446/8835590 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 855 | 854 | 2248885100 | 143 | 8835590 | 0x0000000000400654 | fmadd | 8835446/8835590 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 856 | 855 | 2248885100 | 143 | 8835590 | 0x0000000000400654 | fmadd | 8835446/8835590 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 857 | 856 | 2248885870 | 143 | 8835590 | 0x0000000000400654 | fmadd | —/8835590 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1378 | 857 | 9405415250 | 143 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 858 | — | 2270457420 | 144 | 8920478 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff795810624dd2f→0x3ff795810624dd0f | — | — | origin |
| carrier_state | 859 | 858 | 2270457420 | 144 | 8920478 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff795810624dd2f→0x3ff795810624dd0f | — | — | fsu_taint |
| operand_read | 860 | 859 | 2270492840 | 144 | 8920622 | 0x0000000000400654 | fmadd | 8920478/8920622 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 861 | 860 | 2270492840 | 144 | 8920622 | 0x0000000000400654 | fmadd | 8920478/8920622 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 862 | 861 | 2270492840 | 144 | 8920622 | 0x0000000000400654 | fmadd | 8920478/8920622 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 863 | 862 | 2270493610 | 144 | 8920622 | 0x0000000000400654 | fmadd | —/8920622 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1379 | 863 | 9405415250 | 144 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 864 | — | 2288853875 | 145 | 8992660 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fd570a3d70a3d71→0x3fd570a3d70a3d70 | — | — | origin |
| carrier_state | 865 | 864 | 2288853875 | 145 | 8992660 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fd570a3d70a3d71→0x3fd570a3d70a3d70 | — | — | fsu_taint |
| operand_read | 866 | 865 | 2288869275 | 145 | 8992730 | 0x0000000000400654 | fmadd | 8992660/8992730 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 867 | 866 | 2288869275 | 145 | 8992730 | 0x0000000000400654 | fmadd | 8992660/8992730 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 868 | 867 | 2288869275 | 145 | 8992730 | 0x0000000000400654 | fmadd | 8992660/8992730 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 869 | 868 | 2288870045 | 145 | 8992730 | 0x0000000000400654 | fmadd | —/8992730 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1380 | 869 | 9405415250 | 145 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 870 | — | 2303994000 | 146 | 9052708 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfdb74bc6a7ef9db→0xbfdb74bc6a7cf9db | — | — | origin |
| carrier_state | 871 | 870 | 2303994000 | 146 | 9052708 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfdb74bc6a7ef9db→0xbfdb74bc6a7cf9db | — | — | fsu_taint |
| operand_read | 872 | 871 | 2304009400 | 146 | 9052778 | 0x0000000000400654 | fmadd | 9052708/9052778 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 873 | 872 | 2304009400 | 146 | 9052778 | 0x0000000000400654 | fmadd | 9052708/9052778 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 874 | 873 | 2304009400 | 146 | 9052778 | 0x0000000000400654 | fmadd | 9052708/9052778 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 875 | 874 | 2304010170 | 146 | 9052778 | 0x0000000000400654 | fmadd | —/9052778 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1381 | 875 | 9405415250 | 146 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 876 | — | 2326664340 | 147 | 9142163 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4082200000000000→0x4082200000000001 | — | — | origin |
| carrier_state | 877 | 876 | 2326664340 | 147 | 9142163 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4082200000000000→0x4082200000000001 | — | — | fsu_taint |
| operand_read | 878 | 877 | 2326666265 | 147 | 9142166 | 0x0000000000400654 | fmadd | 9142163/9142166 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 879 | 878 | 2326666265 | 147 | 9142166 | 0x0000000000400654 | fmadd | 9142163/9142166 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 880 | 879 | 2326666265 | 147 | 9142166 | 0x0000000000400654 | fmadd | 9142163/9142166 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 881 | 880 | 2326667035 | 147 | 9142166 | 0x0000000000400654 | fmadd | —/9142166 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1382 | 881 | 9405415250 | 147 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 882 | — | 2337920200 | 148 | 9186915 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe60c49ba5e3540→0x3fe60c49ba5e3544 | — | — | origin |
| carrier_state | 883 | 882 | 2337920200 | 148 | 9186915 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe60c49ba5e3540→0x3fe60c49ba5e3544 | — | — | fsu_taint |
| operand_read | 884 | 883 | 2337944455 | 148 | 9187022 | 0x0000000000400654 | fmadd | 9186915/9187022 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 885 | 884 | 2337944455 | 148 | 9187022 | 0x0000000000400654 | fmadd | 9186915/9187022 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 886 | 885 | 2337944455 | 148 | 9187022 | 0x0000000000400654 | fmadd | 9186915/9187022 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 887 | 886 | 2337945225 | 148 | 9187022 | 0x0000000000400654 | fmadd | —/9187022 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1383 | 887 | 9405415250 | 148 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 888 | — | 2355943975 | 149 | 9258013 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x406d200000000000→0x406d200000001000 | — | — | origin |
| carrier_state | 889 | 888 | 2355943975 | 149 | 9258013 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x406d200000000000→0x406d200000001000 | — | — | fsu_taint |
| operand_read | 890 | 889 | 2355947825 | 149 | 9258016 | 0x000000000040065c | fmadd | 9258013/9258016 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 891 | 890 | 2355947825 | 149 | 9258016 | 0x000000000040065c | fmadd | 9258013/9258016 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 892 | 891 | 2355947825 | 149 | 9258016 | 0x000000000040065c | fmadd | 9258013/9258016 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 893 | 892 | 2355948595 | 149 | 9258016 | 0x000000000040065c | fmadd | —/9258016 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1384 | 893 | 9405415250 | 149 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 84 | — | 293711495 | 15 | 1121330 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fe25604189374bc→0x3fe25604189354bc | — | — | origin |
| carrier_state | 85 | 84 | 293711495 | 15 | 1121330 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fe25604189374bc→0x3fe25604189354bc | — | — | fsu_taint |
| operand_read | 86 | 85 | 293746915 | 15 | 1121474 | 0x0000000000400654 | fmadd | 1121330/1121474 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 87 | 86 | 293746915 | 15 | 1121474 | 0x0000000000400654 | fmadd | 1121330/1121474 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 88 | 87 | 293746915 | 15 | 1121474 | 0x0000000000400654 | fmadd | 1121330/1121474 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 89 | 88 | 293747685 | 15 | 1121474 | 0x0000000000400654 | fmadd | —/1121474 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1250 | 89 | 9405415250 | 15 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 894 | — | 2375274055 | 150 | 9334260 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x407fb00000000000→0x407fb00000000080 | — | — | origin |
| carrier_state | 895 | 894 | 2375274055 | 150 | 9334260 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x407fb00000000000→0x407fb00000000080 | — | — | fsu_taint |
| operand_read | 896 | 895 | 2375278290 | 150 | 9334263 | 0x0000000000400658 | fmadd | 9334260/9334263 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 897 | 896 | 2375278290 | 150 | 9334263 | 0x0000000000400658 | fmadd | 9334260/9334263 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 898 | 897 | 2375278290 | 150 | 9334263 | 0x0000000000400658 | fmadd | 9334260/9334263 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 899 | 898 | 2375279060 | 150 | 9334263 | 0x0000000000400658 | fmadd | —/9334263 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1385 | 899 | 9405415250 | 150 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 900 | — | 2389209515 | 151 | 9389449 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x407e700000000000→0x407e700000000200 | — | — | origin |
| carrier_state | 901 | 900 | 2389209515 | 151 | 9389449 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x407e700000000000→0x407e700000000200 | — | — | fsu_taint |
| operand_read | 902 | 901 | 2389213365 | 151 | 9389452 | 0x000000000040065c | fmadd | 9389449/9389452 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 903 | 902 | 2389213365 | 151 | 9389452 | 0x000000000040065c | fmadd | 9389449/9389452 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 904 | 903 | 2389213365 | 151 | 9389452 | 0x000000000040065c | fmadd | 9389449/9389452 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 905 | 904 | 2389214135 | 151 | 9389452 | 0x000000000040065c | fmadd | —/9389452 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1386 | 905 | 9405415250 | 151 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 906 | — | 2402041565 | 152 | 9439742 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fe449ba5e353f7d→0x3fe449ba5e373f7d | — | — | origin |
| carrier_state | 907 | 906 | 2402041565 | 152 | 9439742 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fe449ba5e353f7d→0x3fe449ba5e373f7d | — | — | fsu_taint |
| operand_read | 908 | 907 | 2402076985 | 152 | 9439886 | 0x0000000000400654 | fmadd | 9439742/9439886 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 909 | 908 | 2402076985 | 152 | 9439886 | 0x0000000000400654 | fmadd | 9439742/9439886 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 910 | 909 | 2402076985 | 152 | 9439886 | 0x0000000000400654 | fmadd | 9439742/9439886 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 911 | 910 | 2402077755 | 152 | 9439886 | 0x0000000000400654 | fmadd | —/9439886 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1387 | 911 | 9405415250 | 152 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 912 | — | 2486353870 | 153 | 9539260 | 0x00000000004006cc | fmadd | —/— | 44 | — | 64@0 | 0x3fd706b37867f0aa→0x3fd706b37867f0ea | — | — | origin |
| carrier_state | 913 | 912 | 2486353870 | 153 | 9539260 | 0x00000000004006cc | fmadd | —/— | 44 | — | 64@0 | 0x3fd706b37867f0aa→0x3fd706b37867f0ea | — | — | fsu_taint |
| operand_read | 914 | 913 | 2486362340 | 153 | 9539276 | 0x00000000004006cc | fmadd | 9539260/9539276 | 44 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 915 | 914 | 2486362340 | 153 | 9539276 | 0x00000000004006cc | fmadd | 9539260/9539276 | 44 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 916 | 915 | 2486362340 | 153 | 9539276 | 0x00000000004006cc | fmadd | 9539260/9539276 | 44 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 917 | 916 | 2486363110 | 153 | 9539276 | 0x00000000004006cc | fmadd | —/9539276 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1388 | 917 | 9405415250 | 153 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 918 | — | 2537763305 | 154 | 9607179 | 0x00000000004006a4 | fmadd | —/— | 4 | — | 64@0 | 0x3fe48060780fdc17→0x3fe48060780f5c17 | — | — | origin |
| carrier_state | 919 | 918 | 2537763305 | 154 | 9607179 | 0x00000000004006a4 | fmadd | —/— | 4 | — | 64@0 | 0x3fe48060780fdc17→0x3fe48060780f5c17 | — | — | fsu_taint |
| operand_read | 920 | 919 | 2537771775 | 154 | 9607195 | 0x00000000004006a4 | fmadd | 9607179/9607195 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 921 | 920 | 2537771775 | 154 | 9607195 | 0x00000000004006a4 | fmadd | 9607179/9607195 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 922 | 921 | 2537771775 | 154 | 9607195 | 0x00000000004006a4 | fmadd | 9607179/9607195 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 923 | 922 | 2537772545 | 154 | 9607195 | 0x00000000004006a4 | fmadd | —/9607195 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1389 | 923 | 9405415250 | 154 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 924 | — | 2596869660 | 155 | 9673501 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff01f0f5a1016ce→0x3ff01f0f5a1016de | — | — | origin |
| carrier_state | 925 | 924 | 2596869660 | 155 | 9673501 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff01f0f5a1016ce→0x3ff01f0f5a1016de | — | — | fsu_taint |
| operand_read | 926 | 925 | 2596878130 | 155 | 9673517 | 0x00000000004006cc | fmadd | 9673501/9673517 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 927 | 926 | 2596878130 | 155 | 9673517 | 0x00000000004006cc | fmadd | 9673501/9673517 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 928 | 927 | 2596878130 | 155 | 9673517 | 0x00000000004006cc | fmadd | 9673501/9673517 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 929 | 928 | 2596878900 | 155 | 9673517 | 0x00000000004006cc | fmadd | —/9673517 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1390 | 929 | 9405415250 | 155 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 930 | — | 2646612430 | 156 | 9747633 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fdd6eb4e981387a→0x3fdd6eb4e981387b | — | — | origin |
| carrier_state | 931 | 930 | 2646612430 | 156 | 9747633 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fdd6eb4e981387a→0x3fdd6eb4e981387b | — | — | fsu_taint |
| operand_read | 932 | 931 | 2646736785 | 156 | 9747649 | 0x00000000004006a4 | fmadd | 9747633/9747649 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 933 | 932 | 2646736785 | 156 | 9747649 | 0x00000000004006a4 | fmadd | 9747633/9747649 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 934 | 933 | 2646736785 | 156 | 9747649 | 0x00000000004006a4 | fmadd | 9747633/9747649 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 935 | 934 | 2646737555 | 156 | 9747649 | 0x00000000004006a4 | fmadd | —/9747649 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1391 | 935 | 9405415250 | 156 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 936 | — | 2702092855 | 157 | 9826655 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff21143bf727137→0x3ff21143bf737137 | — | — | origin |
| carrier_state | 937 | 936 | 2702092855 | 157 | 9826655 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff21143bf727137→0x3ff21143bf737137 | — | — | fsu_taint |
| operand_read | 938 | 937 | 2702101325 | 157 | 9826671 | 0x00000000004006cc | fmadd | 9826655/9826671 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 939 | 938 | 2702101325 | 157 | 9826671 | 0x00000000004006cc | fmadd | 9826655/9826671 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 940 | 939 | 2702101325 | 157 | 9826671 | 0x00000000004006cc | fmadd | 9826655/9826671 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 941 | 940 | 2702102095 | 157 | 9826671 | 0x00000000004006cc | fmadd | —/9826671 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1392 | 941 | 9405415250 | 157 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 942 | — | 2784214895 | 158 | 9937865 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe8949a5657fb6a→0x3fe8949a5657fb6b | — | — | origin |
| carrier_state | 943 | 942 | 2784214895 | 158 | 9937865 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe8949a5657fb6a→0x3fe8949a5657fb6b | — | — | fsu_taint |
| operand_read | 944 | 943 | 2784223365 | 158 | 9937881 | 0x00000000004006cc | fmadd | 9937865/9937881 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 945 | 944 | 2784223365 | 158 | 9937881 | 0x00000000004006cc | fmadd | 9937865/9937881 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 946 | 945 | 2784223365 | 158 | 9937881 | 0x00000000004006cc | fmadd | 9937865/9937881 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 947 | 946 | 2784224135 | 158 | 9937881 | 0x00000000004006cc | fmadd | —/9937881 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1393 | 947 | 9405415250 | 158 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 948 | — | 2831365075 | 159 | 10008837 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fefb38d60a63305→0x3fefb38d60a63385 | — | — | origin |
| carrier_state | 949 | 948 | 2831365075 | 159 | 10008837 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fefb38d60a63305→0x3fefb38d60a63385 | — | — | fsu_taint |
| operand_read | 950 | 949 | 2831373545 | 159 | 10008853 | 0x00000000004006a4 | fmadd | 10008837/10008853 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 951 | 950 | 2831373545 | 159 | 10008853 | 0x00000000004006a4 | fmadd | 10008837/10008853 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 952 | 951 | 2831373545 | 159 | 10008853 | 0x00000000004006a4 | fmadd | 10008837/10008853 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 953 | 952 | 2831374315 | 159 | 10008853 | 0x00000000004006a4 | fmadd | —/10008853 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1394 | 953 | 9405415250 | 159 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 90 | — | 305315395 | 16 | 1167515 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4086f00000000000→0x4086f00000000001 | — | — | origin |
| carrier_state | 91 | 90 | 305315395 | 16 | 1167515 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4086f00000000000→0x4086f00000000001 | — | — | fsu_taint |
| operand_read | 92 | 91 | 305317320 | 16 | 1167518 | 0x0000000000400654 | fmadd | 1167515/1167518 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 93 | 92 | 305317320 | 16 | 1167518 | 0x0000000000400654 | fmadd | 1167515/1167518 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 94 | 93 | 305317320 | 16 | 1167518 | 0x0000000000400654 | fmadd | 1167515/1167518 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 95 | 94 | 305318090 | 16 | 1167518 | 0x0000000000400654 | fmadd | —/1167518 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1251 | 95 | 9405415250 | 16 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 954 | — | 2885176910 | 160 | 10084219 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff715b573eab368→0x3ff715b573eab768 | — | — | origin |
| carrier_state | 955 | 954 | 2885176910 | 160 | 10084219 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff715b573eab368→0x3ff715b573eab768 | — | — | fsu_taint |
| operand_read | 956 | 955 | 2885185380 | 160 | 10084235 | 0x00000000004006cc | fmadd | 10084219/10084235 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 957 | 956 | 2885185380 | 160 | 10084235 | 0x00000000004006cc | fmadd | 10084219/10084235 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 958 | 957 | 2885185380 | 160 | 10084235 | 0x00000000004006cc | fmadd | 10084219/10084235 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 959 | 958 | 2885186150 | 160 | 10084235 | 0x00000000004006cc | fmadd | —/10084235 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1395 | 959 | 9405415250 | 160 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 960 | — | 2959935055 | 161 | 10180829 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff983f2d3c792d1→0x3ff983f2d3c792d3 | — | — | origin |
| carrier_state | 961 | 960 | 2959935055 | 161 | 10180829 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff983f2d3c792d1→0x3ff983f2d3c792d3 | — | — | fsu_taint |
| operand_read | 962 | 961 | 2959943525 | 161 | 10180845 | 0x00000000004006cc | fmadd | 10180829/10180845 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 963 | 962 | 2959943525 | 161 | 10180845 | 0x00000000004006cc | fmadd | 10180829/10180845 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 964 | 963 | 2959943525 | 161 | 10180845 | 0x00000000004006cc | fmadd | 10180829/10180845 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 965 | 964 | 2959944295 | 161 | 10180845 | 0x00000000004006cc | fmadd | —/10180845 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1396 | 965 | 9405415250 | 161 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 966 | — | 3020553690 | 162 | 10274329 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ffb60d887ebf22c→0x3ffb60d887ebf22d | — | — | origin |
| carrier_state | 967 | 966 | 3020553690 | 162 | 10274329 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ffb60d887ebf22c→0x3ffb60d887ebf22d | — | — | fsu_taint |
| operand_read | 968 | 967 | 3020562160 | 162 | 10274345 | 0x00000000004006a4 | fmadd | 10274329/10274345 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 969 | 968 | 3020562160 | 162 | 10274345 | 0x00000000004006a4 | fmadd | 10274329/10274345 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 970 | 969 | 3020562160 | 162 | 10274345 | 0x00000000004006a4 | fmadd | 10274329/10274345 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 971 | 970 | 3020562930 | 162 | 10274345 | 0x00000000004006a4 | fmadd | —/10274345 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1397 | 971 | 9405415250 | 162 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 972 | — | 3062224935 | 163 | 10328895 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff4d20afa2f05a6→0x3ff4d20afa2d05a6 | — | — | origin |
| carrier_state | 973 | 972 | 3062224935 | 163 | 10328895 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff4d20afa2f05a6→0x3ff4d20afa2d05a6 | — | — | fsu_taint |
| operand_read | 974 | 973 | 3062233405 | 163 | 10328911 | 0x00000000004006cc | fmadd | 10328895/10328911 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 975 | 974 | 3062233405 | 163 | 10328911 | 0x00000000004006cc | fmadd | 10328895/10328911 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 976 | 975 | 3062233405 | 163 | 10328911 | 0x00000000004006cc | fmadd | 10328895/10328911 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 977 | 976 | 3062234175 | 163 | 10328911 | 0x00000000004006cc | fmadd | —/10328911 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1398 | 977 | 9405415250 | 163 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 978 | — | 3085187875 | 164 | 10371451 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3ff3cc55432873bd→0x3ff3cc55432873b5 | — | — | origin |
| carrier_state | 979 | 978 | 3085187875 | 164 | 10371451 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3ff3cc55432873bd→0x3ff3cc55432873b5 | — | — | fsu_taint |
| operand_read | 980 | 979 | 3085196345 | 164 | 10371467 | 0x00000000004006a4 | fmadd | 10371451/10371467 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 981 | 980 | 3085196345 | 164 | 10371467 | 0x00000000004006a4 | fmadd | 10371451/10371467 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 982 | 981 | 3085196345 | 164 | 10371467 | 0x00000000004006a4 | fmadd | 10371451/10371467 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 983 | 982 | 3085197115 | 164 | 10371467 | 0x00000000004006a4 | fmadd | —/10371467 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1399 | 983 | 9405415250 | 164 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 984 | — | 3143309400 | 165 | 10437457 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe2dc011d3671ac→0x3fe2dc011d3471ac | — | — | origin |
| carrier_state | 985 | 984 | 3143309400 | 165 | 10437457 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe2dc011d3671ac→0x3fe2dc011d3471ac | — | — | fsu_taint |
| operand_read | 986 | 985 | 3143317870 | 165 | 10437473 | 0x00000000004006cc | fmadd | 10437457/10437473 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 987 | 986 | 3143317870 | 165 | 10437473 | 0x00000000004006cc | fmadd | 10437457/10437473 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 988 | 987 | 3143317870 | 165 | 10437473 | 0x00000000004006cc | fmadd | 10437457/10437473 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 989 | 988 | 3143318640 | 165 | 10437473 | 0x00000000004006cc | fmadd | —/10437473 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1400 | 989 | 9405415250 | 165 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 990 | — | 3214264130 | 166 | 10544765 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3fd099e94ab1d4fa→0x3fd099e94ab0d4fa | — | — | origin |
| carrier_state | 991 | 990 | 3214264130 | 166 | 10544765 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3fd099e94ab1d4fa→0x3fd099e94ab0d4fa | — | — | fsu_taint |
| operand_read | 992 | 991 | 3214298780 | 166 | 10544781 | 0x00000000004006a4 | fmadd | 10544765/10544781 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 993 | 992 | 3214298780 | 166 | 10544781 | 0x00000000004006a4 | fmadd | 10544765/10544781 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 994 | 993 | 3214298780 | 166 | 10544781 | 0x00000000004006a4 | fmadd | 10544765/10544781 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 995 | 994 | 3214299550 | 166 | 10544781 | 0x00000000004006a4 | fmadd | —/10544781 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1401 | 995 | 9405415250 | 166 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 996 | — | 3272716370 | 167 | 10635503 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe99ae0c1765777→0x3fe99ae0c1765737 | — | — | origin |
| carrier_state | 997 | 996 | 3272716370 | 167 | 10635503 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe99ae0c1765777→0x3fe99ae0c1765737 | — | — | fsu_taint |
| operand_read | 998 | 997 | 3272724840 | 167 | 10635519 | 0x00000000004006a4 | fmadd | 10635503/10635519 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 999 | 998 | 3272724840 | 167 | 10635519 | 0x00000000004006a4 | fmadd | 10635503/10635519 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1000 | 999 | 3272724840 | 167 | 10635519 | 0x00000000004006a4 | fmadd | 10635503/10635519 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1001 | 1000 | 3272725610 | 167 | 10635519 | 0x00000000004006a4 | fmadd | —/10635519 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1402 | 1001 | 9405415250 | 167 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1002 | — | 3317046425 | 168 | 10685919 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fdf358298cc1442→0x3fdf358298cc1446 | — | — | origin |
| carrier_state | 1003 | 1002 | 3317046425 | 168 | 10685919 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fdf358298cc1442→0x3fdf358298cc1446 | — | — | fsu_taint |
| operand_read | 1004 | 1003 | 3317439895 | 168 | 10685935 | 0x00000000004006a4 | fmadd | 10685919/10685935 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1005 | 1004 | 3317439895 | 168 | 10685935 | 0x00000000004006a4 | fmadd | 10685919/10685935 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1006 | 1005 | 3317439895 | 168 | 10685935 | 0x00000000004006a4 | fmadd | 10685919/10685935 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1007 | 1006 | 3317440665 | 168 | 10685935 | 0x00000000004006a4 | fmadd | —/10685935 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1403 | 1007 | 9405415250 | 168 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1008 | — | 3359359465 | 169 | 10756301 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff07d1dcd7060bc→0x3ff07d1dcd7060ac | — | — | origin |
| carrier_state | 1009 | 1008 | 3359359465 | 169 | 10756301 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff07d1dcd7060bc→0x3ff07d1dcd7060ac | — | — | fsu_taint |
| operand_read | 1010 | 1009 | 3359367935 | 169 | 10756317 | 0x00000000004006cc | fmadd | 10756301/10756317 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1011 | 1010 | 3359367935 | 169 | 10756317 | 0x00000000004006cc | fmadd | 10756301/10756317 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1012 | 1011 | 3359367935 | 169 | 10756317 | 0x00000000004006cc | fmadd | 10756301/10756317 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1013 | 1012 | 3359368705 | 169 | 10756317 | 0x00000000004006cc | fmadd | —/10756317 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1404 | 1013 | 9405415250 | 169 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 96 | — | 317670045 | 17 | 1215864 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4073600000000000→0x4073600000001000 | — | — | origin |
| carrier_state | 97 | 96 | 317670045 | 17 | 1215864 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4073600000000000→0x4073600000001000 | — | — | fsu_taint |
| operand_read | 98 | 97 | 317674280 | 17 | 1215867 | 0x0000000000400658 | fmadd | 1215864/1215867 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 99 | 98 | 317674280 | 17 | 1215867 | 0x0000000000400658 | fmadd | 1215864/1215867 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 100 | 99 | 317674280 | 17 | 1215867 | 0x0000000000400658 | fmadd | 1215864/1215867 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 101 | 100 | 317675050 | 17 | 1215867 | 0x0000000000400658 | fmadd | —/1215867 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1252 | 101 | 9405415250 | 17 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1014 | — | 3440316495 | 170 | 10864863 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3ffc8bda9435ac8a→0x3ffc8bda9435acca | — | — | origin |
| carrier_state | 1015 | 1014 | 3440316495 | 170 | 10864863 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3ffc8bda9435ac8a→0x3ffc8bda9435acca | — | — | fsu_taint |
| operand_read | 1016 | 1015 | 3440324965 | 170 | 10864879 | 0x00000000004006cc | fmadd | 10864863/10864879 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1017 | 1016 | 3440324965 | 170 | 10864879 | 0x00000000004006cc | fmadd | 10864863/10864879 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1018 | 1017 | 3440324965 | 170 | 10864879 | 0x00000000004006cc | fmadd | 10864863/10864879 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1019 | 1018 | 3440325735 | 170 | 10864879 | 0x00000000004006cc | fmadd | —/10864879 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1405 | 1019 | 9405415250 | 170 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1020 | — | 3522018500 | 171 | 10973953 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fc48909289dadfd→0x3fc48909289da9fd | — | — | origin |
| carrier_state | 1021 | 1020 | 3522018500 | 171 | 10973953 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fc48909289dadfd→0x3fc48909289da9fd | — | — | fsu_taint |
| operand_read | 1022 | 1021 | 3522026970 | 171 | 10973969 | 0x00000000004006cc | fmadd | 10973953/10973969 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1023 | 1022 | 3522026970 | 171 | 10973969 | 0x00000000004006cc | fmadd | 10973953/10973969 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1024 | 1023 | 3522026970 | 171 | 10973969 | 0x00000000004006cc | fmadd | 10973953/10973969 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1025 | 1024 | 3522027740 | 171 | 10973969 | 0x00000000004006cc | fmadd | —/10973969 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1406 | 1025 | 9405415250 | 171 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1026 | — | 3568657785 | 172 | 11049141 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3fa138bcdfefbf3f→0x3fa138bcdfedbf3f | — | — | origin |
| carrier_state | 1027 | 1026 | 3568657785 | 172 | 11049141 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3fa138bcdfefbf3f→0x3fa138bcdfedbf3f | — | — | fsu_taint |
| operand_read | 1028 | 1027 | 3568666255 | 172 | 11049157 | 0x00000000004006a4 | fmadd | 11049141/11049157 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1029 | 1028 | 3568666255 | 172 | 11049157 | 0x00000000004006a4 | fmadd | 11049141/11049157 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1030 | 1029 | 3568666255 | 172 | 11049157 | 0x00000000004006a4 | fmadd | 11049141/11049157 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1031 | 1030 | 3568667025 | 172 | 11049157 | 0x00000000004006a4 | fmadd | —/11049157 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1407 | 1031 | 9405415250 | 172 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1032 | — | 3617497730 | 173 | 11109811 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe0ef0ae536501e→0x3fe0ef0ae536101e | — | — | origin |
| carrier_state | 1033 | 1032 | 3617497730 | 173 | 11109811 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe0ef0ae536501e→0x3fe0ef0ae536101e | — | — | fsu_taint |
| operand_read | 1034 | 1033 | 3617506200 | 173 | 11109827 | 0x00000000004006cc | fmadd | 11109811/11109827 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1035 | 1034 | 3617506200 | 173 | 11109827 | 0x00000000004006cc | fmadd | 11109811/11109827 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1036 | 1035 | 3617506200 | 173 | 11109827 | 0x00000000004006cc | fmadd | 11109811/11109827 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1037 | 1036 | 3617506970 | 173 | 11109827 | 0x00000000004006cc | fmadd | —/11109827 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1408 | 1037 | 9405415250 | 173 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1038 | — | 3660494530 | 174 | 11177991 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe31ca9ef5232d3→0x3fe31ca9ef5272d3 | — | — | origin |
| carrier_state | 1039 | 1038 | 3660494530 | 174 | 11177991 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe31ca9ef5232d3→0x3fe31ca9ef5272d3 | — | — | fsu_taint |
| operand_read | 1040 | 1039 | 3660503000 | 174 | 11178007 | 0x00000000004006a4 | fmadd | 11177991/11178007 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1041 | 1040 | 3660503000 | 174 | 11178007 | 0x00000000004006a4 | fmadd | 11177991/11178007 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1042 | 1041 | 3660503000 | 174 | 11178007 | 0x00000000004006a4 | fmadd | 11177991/11178007 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1043 | 1042 | 3660503770 | 174 | 11178007 | 0x00000000004006a4 | fmadd | —/11178007 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1409 | 1043 | 9405415250 | 174 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1044 | — | 3708182940 | 175 | 11235981 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0xbfc00ee06d938150→0xbfc00ee06d938158 | — | — | origin |
| carrier_state | 1045 | 1044 | 3708182940 | 175 | 11235981 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0xbfc00ee06d938150→0xbfc00ee06d938158 | — | — | fsu_taint |
| operand_read | 1046 | 1045 | 3708191410 | 175 | 11235997 | 0x00000000004006cc | fmadd | 11235981/11235997 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1047 | 1046 | 3708191410 | 175 | 11235997 | 0x00000000004006cc | fmadd | 11235981/11235997 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1048 | 1047 | 3708191410 | 175 | 11235997 | 0x00000000004006cc | fmadd | 11235981/11235997 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1049 | 1048 | 3708192180 | 175 | 11235997 | 0x00000000004006cc | fmadd | —/11235997 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1410 | 1049 | 9405415250 | 175 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1050 | — | 3763769240 | 176 | 11322025 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe5ea400fba8825→0x3fe5ea400fba8835 | — | — | origin |
| carrier_state | 1051 | 1050 | 3763769240 | 176 | 11322025 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe5ea400fba8825→0x3fe5ea400fba8835 | — | — | fsu_taint |
| operand_read | 1052 | 1051 | 3763777710 | 176 | 11322041 | 0x00000000004006a4 | fmadd | 11322025/11322041 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1053 | 1052 | 3763777710 | 176 | 11322041 | 0x00000000004006a4 | fmadd | 11322025/11322041 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1054 | 1053 | 3763777710 | 176 | 11322041 | 0x00000000004006a4 | fmadd | 11322025/11322041 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1055 | 1054 | 3763778480 | 176 | 11322041 | 0x00000000004006a4 | fmadd | —/11322041 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1411 | 1055 | 9405415250 | 176 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1056 | — | 3809584240 | 177 | 11383239 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fdbc4a83b1d0c80→0x3fdbc4a83b1d1c80 | — | — | origin |
| carrier_state | 1057 | 1056 | 3809584240 | 177 | 11383239 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fdbc4a83b1d0c80→0x3fdbc4a83b1d1c80 | — | — | fsu_taint |
| operand_read | 1058 | 1057 | 3809592710 | 177 | 11383255 | 0x00000000004006cc | fmadd | 11383239/11383255 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1059 | 1058 | 3809592710 | 177 | 11383255 | 0x00000000004006cc | fmadd | 11383239/11383255 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1060 | 1059 | 3809592710 | 177 | 11383255 | 0x00000000004006cc | fmadd | 11383239/11383255 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1061 | 1060 | 3809593480 | 177 | 11383255 | 0x00000000004006cc | fmadd | —/11383255 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1412 | 1061 | 9405415250 | 177 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1062 | — | 3886970010 | 178 | 11484043 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ff5e14cec41dd1b→0x3ff5e14cec41df1b | — | — | origin |
| carrier_state | 1063 | 1062 | 3886970010 | 178 | 11484043 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ff5e14cec41dd1b→0x3ff5e14cec41df1b | — | — | fsu_taint |
| operand_read | 1064 | 1063 | 3886978480 | 178 | 11484059 | 0x00000000004006a4 | fmadd | 11484043/11484059 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1065 | 1064 | 3886978480 | 178 | 11484059 | 0x00000000004006a4 | fmadd | 11484043/11484059 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1066 | 1065 | 3886978480 | 178 | 11484059 | 0x00000000004006a4 | fmadd | 11484043/11484059 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1067 | 1066 | 3886979250 | 178 | 11484059 | 0x00000000004006a4 | fmadd | —/11484059 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1413 | 1067 | 9405415250 | 178 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1068 | — | 3926653500 | 179 | 11555589 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ffca253111f0c35→0x3ffca253111d0c35 | — | — | origin |
| carrier_state | 1069 | 1068 | 3926653500 | 179 | 11555589 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ffca253111f0c35→0x3ffca253111d0c35 | — | — | fsu_taint |
| operand_read | 1070 | 1069 | 3926661970 | 179 | 11555605 | 0x00000000004006a4 | fmadd | 11555589/11555605 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1071 | 1070 | 3926661970 | 179 | 11555605 | 0x00000000004006a4 | fmadd | 11555589/11555605 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1072 | 1071 | 3926661970 | 179 | 11555605 | 0x00000000004006a4 | fmadd | 11555589/11555605 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1073 | 1072 | 3926662740 | 179 | 11555605 | 0x00000000004006a4 | fmadd | —/11555605 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1414 | 1073 | 9405415250 | 179 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 102 | — | 328961325 | 18 | 1260759 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe25e353f7ced91→0x3fe25e353f7c6d91 | — | — | origin |
| carrier_state | 103 | 102 | 328961325 | 18 | 1260759 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe25e353f7ced91→0x3fe25e353f7c6d91 | — | — | fsu_taint |
| operand_read | 104 | 103 | 328985580 | 18 | 1260866 | 0x0000000000400654 | fmadd | 1260759/1260866 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 105 | 104 | 328985580 | 18 | 1260866 | 0x0000000000400654 | fmadd | 1260759/1260866 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 106 | 105 | 328985580 | 18 | 1260866 | 0x0000000000400654 | fmadd | 1260759/1260866 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 107 | 106 | 328986350 | 18 | 1260866 | 0x0000000000400654 | fmadd | —/1260866 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1253 | 107 | 9405415250 | 18 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1074 | — | 4009081230 | 180 | 11669715 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fe4603925bb7b6c→0x3fe4603925bb6b6c | — | — | origin |
| carrier_state | 1075 | 1074 | 4009081230 | 180 | 11669715 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fe4603925bb7b6c→0x3fe4603925bb6b6c | — | — | fsu_taint |
| operand_read | 1076 | 1075 | 4009089700 | 180 | 11669731 | 0x00000000004006cc | fmadd | 11669715/11669731 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1077 | 1076 | 4009089700 | 180 | 11669731 | 0x00000000004006cc | fmadd | 11669715/11669731 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1078 | 1077 | 4009089700 | 180 | 11669731 | 0x00000000004006cc | fmadd | 11669715/11669731 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1079 | 1078 | 4009090470 | 180 | 11669731 | 0x00000000004006cc | fmadd | —/11669731 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1415 | 1079 | 9405415250 | 180 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1080 | — | 4046483210 | 181 | 11718879 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fdd8d2a1f8e3ac1→0x3fdd8d2a1f8f3ac1 | — | — | origin |
| carrier_state | 1081 | 1080 | 4046483210 | 181 | 11718879 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fdd8d2a1f8e3ac1→0x3fdd8d2a1f8f3ac1 | — | — | fsu_taint |
| operand_read | 1082 | 1081 | 4046491680 | 181 | 11718895 | 0x00000000004006a4 | fmadd | 11718879/11718895 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1083 | 1082 | 4046491680 | 181 | 11718895 | 0x00000000004006a4 | fmadd | 11718879/11718895 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1084 | 1083 | 4046491680 | 181 | 11718895 | 0x00000000004006a4 | fmadd | 11718879/11718895 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1085 | 1084 | 4046492450 | 181 | 11718895 | 0x00000000004006a4 | fmadd | —/11718895 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1416 | 1085 | 9405415250 | 181 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1086 | — | 4127821005 | 182 | 11836513 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff47e90ff972474→0x3ff47e90ff976474 | — | — | origin |
| carrier_state | 1087 | 1086 | 4127821005 | 182 | 11836513 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff47e90ff972474→0x3ff47e90ff976474 | — | — | fsu_taint |
| operand_read | 1088 | 1087 | 4127829475 | 182 | 11836529 | 0x00000000004006a4 | fmadd | 11836513/11836529 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1089 | 1088 | 4127829475 | 182 | 11836529 | 0x00000000004006a4 | fmadd | 11836513/11836529 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1090 | 1089 | 4127829475 | 182 | 11836529 | 0x00000000004006a4 | fmadd | 11836513/11836529 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1091 | 1090 | 4127830245 | 182 | 11836529 | 0x00000000004006a4 | fmadd | —/11836529 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1417 | 1091 | 9405415250 | 182 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1092 | — | 4190590250 | 183 | 11924295 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe838b8ae31d713→0x3fe838b8ae31d71b | — | — | origin |
| carrier_state | 1093 | 1092 | 4190590250 | 183 | 11924295 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe838b8ae31d713→0x3fe838b8ae31d71b | — | — | fsu_taint |
| operand_read | 1094 | 1093 | 4190598720 | 183 | 11924311 | 0x00000000004006cc | fmadd | 11924295/11924311 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1095 | 1094 | 4190598720 | 183 | 11924311 | 0x00000000004006cc | fmadd | 11924295/11924311 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1096 | 1095 | 4190598720 | 183 | 11924311 | 0x00000000004006cc | fmadd | 11924295/11924311 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1097 | 1096 | 4190599490 | 183 | 11924311 | 0x00000000004006cc | fmadd | —/11924311 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1418 | 1097 | 9405415250 | 183 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1098 | — | 4221226625 | 184 | 11968427 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe35696e58a32f4→0x3fe35696e58a22f4 | — | — | origin |
| carrier_state | 1099 | 1098 | 4221226625 | 184 | 11968427 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe35696e58a32f4→0x3fe35696e58a22f4 | — | — | fsu_taint |
| operand_read | 1100 | 1099 | 4221235095 | 184 | 11968443 | 0x00000000004006a4 | fmadd | 11968427/11968443 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1101 | 1100 | 4221235095 | 184 | 11968443 | 0x00000000004006a4 | fmadd | 11968427/11968443 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1102 | 1101 | 4221235095 | 184 | 11968443 | 0x00000000004006a4 | fmadd | 11968427/11968443 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1103 | 1102 | 4221235865 | 184 | 11968443 | 0x00000000004006a4 | fmadd | —/11968443 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1419 | 1103 | 9405415250 | 184 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1104 | — | 4279881375 | 185 | 12049497 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff0db9628cbd124→0x3ff0db9628cbd524 | — | — | origin |
| carrier_state | 1105 | 1104 | 4279881375 | 185 | 12049497 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff0db9628cbd124→0x3ff0db9628cbd524 | — | — | fsu_taint |
| operand_read | 1106 | 1105 | 4279889845 | 185 | 12049513 | 0x00000000004006cc | fmadd | 12049497/12049513 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1107 | 1106 | 4279889845 | 185 | 12049513 | 0x00000000004006cc | fmadd | 12049497/12049513 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1108 | 1107 | 4279889845 | 185 | 12049513 | 0x00000000004006cc | fmadd | 12049497/12049513 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1109 | 1108 | 4279890615 | 185 | 12049513 | 0x00000000004006cc | fmadd | —/12049513 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1420 | 1109 | 9405415250 | 185 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1110 | — | 4323277035 | 186 | 12110805 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe89e2de8709742→0x3fe89e2de8709743 | — | — | origin |
| carrier_state | 1111 | 1110 | 4323277035 | 186 | 12110805 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe89e2de8709742→0x3fe89e2de8709743 | — | — | fsu_taint |
| operand_read | 1112 | 1111 | 4323372515 | 186 | 12110821 | 0x00000000004006a4 | fmadd | 12110805/12110821 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1113 | 1112 | 4323372515 | 186 | 12110821 | 0x00000000004006a4 | fmadd | 12110805/12110821 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1114 | 1113 | 4323372515 | 186 | 12110821 | 0x00000000004006a4 | fmadd | 12110805/12110821 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1115 | 1114 | 4323373285 | 186 | 12110821 | 0x00000000004006a4 | fmadd | —/12110821 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1421 | 1115 | 9405415250 | 186 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1116 | — | 4389435050 | 187 | 12210207 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fc366d7a56de331→0x3fc366d7a56de330 | — | — | origin |
| carrier_state | 1117 | 1116 | 4389435050 | 187 | 12210207 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fc366d7a56de331→0x3fc366d7a56de330 | — | — | fsu_taint |
| operand_read | 1118 | 1117 | 4389443520 | 187 | 12210223 | 0x00000000004006a4 | fmadd | 12210207/12210223 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1119 | 1118 | 4389443520 | 187 | 12210223 | 0x00000000004006a4 | fmadd | 12210207/12210223 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1120 | 1119 | 4389443520 | 187 | 12210223 | 0x00000000004006a4 | fmadd | 12210207/12210223 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1121 | 1120 | 4389444290 | 187 | 12210223 | 0x00000000004006a4 | fmadd | —/12210223 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1422 | 1121 | 9405415250 | 187 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1122 | — | 4432711360 | 188 | 12259023 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fce6bf8769ec2d0→0x3fce6bf8769ec250 | — | — | origin |
| carrier_state | 1123 | 1122 | 4432711360 | 188 | 12259023 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fce6bf8769ec2d0→0x3fce6bf8769ec250 | — | — | fsu_taint |
| operand_read | 1124 | 1123 | 4432719830 | 188 | 12259039 | 0x00000000004006a4 | fmadd | 12259023/12259039 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1125 | 1124 | 4432719830 | 188 | 12259039 | 0x00000000004006a4 | fmadd | 12259023/12259039 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1126 | 1125 | 4432719830 | 188 | 12259039 | 0x00000000004006a4 | fmadd | 12259023/12259039 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1127 | 1126 | 4432720600 | 188 | 12259039 | 0x00000000004006a4 | fmadd | —/12259039 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1423 | 1127 | 9405415250 | 188 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1128 | — | 4511498530 | 189 | 12375321 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fca12d77318fc53→0x3fca12d77318bc53 | — | — | origin |
| carrier_state | 1129 | 1128 | 4511498530 | 189 | 12375321 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fca12d77318fc53→0x3fca12d77318bc53 | — | — | fsu_taint |
| operand_read | 1130 | 1129 | 4511507000 | 189 | 12375337 | 0x00000000004006a4 | fmadd | 12375321/12375337 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1131 | 1130 | 4511507000 | 189 | 12375337 | 0x00000000004006a4 | fmadd | 12375321/12375337 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1132 | 1131 | 4511507000 | 189 | 12375337 | 0x00000000004006a4 | fmadd | 12375321/12375337 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1133 | 1132 | 4511507770 | 189 | 12375337 | 0x00000000004006a4 | fmadd | —/12375337 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1424 | 1133 | 9405415250 | 189 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 108 | — | 344403290 | 19 | 1321631 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4062a00000000000→0x4062a00000000004 | — | — | origin |
| carrier_state | 109 | 108 | 344403290 | 19 | 1321631 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4062a00000000000→0x4062a00000000004 | — | — | fsu_taint |
| operand_read | 110 | 109 | 344405215 | 19 | 1321634 | 0x0000000000400654 | fmadd | 1321631/1321634 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 111 | 110 | 344405215 | 19 | 1321634 | 0x0000000000400654 | fmadd | 1321631/1321634 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 112 | 111 | 344405215 | 19 | 1321634 | 0x0000000000400654 | fmadd | 1321631/1321634 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 113 | 112 | 344405985 | 19 | 1321634 | 0x0000000000400654 | fmadd | —/1321634 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1254 | 113 | 9405415250 | 19 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1134 | — | 4565902495 | 190 | 12456159 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fc3cd78c436fc17→0x3fc3cd78c436fc16 | — | — | origin |
| carrier_state | 1135 | 1134 | 4565902495 | 190 | 12456159 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fc3cd78c436fc17→0x3fc3cd78c436fc16 | — | — | fsu_taint |
| operand_read | 1136 | 1135 | 4565910965 | 190 | 12456175 | 0x00000000004006cc | fmadd | 12456159/12456175 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1137 | 1136 | 4565910965 | 190 | 12456175 | 0x00000000004006cc | fmadd | 12456159/12456175 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1138 | 1137 | 4565910965 | 190 | 12456175 | 0x00000000004006cc | fmadd | 12456159/12456175 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1139 | 1138 | 4565911735 | 190 | 12456175 | 0x00000000004006cc | fmadd | —/12456175 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1425 | 1139 | 9405415250 | 190 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1140 | — | 4623627085 | 191 | 12526851 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ff3bcf91a32b12e→0x3ff3bcf91a32b02e | — | — | origin |
| carrier_state | 1141 | 1140 | 4623627085 | 191 | 12526851 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ff3bcf91a32b12e→0x3ff3bcf91a32b02e | — | — | fsu_taint |
| operand_read | 1142 | 1141 | 4623635555 | 191 | 12526867 | 0x00000000004006a4 | fmadd | 12526851/12526867 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1143 | 1142 | 4623635555 | 191 | 12526867 | 0x00000000004006a4 | fmadd | 12526851/12526867 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1144 | 1143 | 4623635555 | 191 | 12526867 | 0x00000000004006a4 | fmadd | 12526851/12526867 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1145 | 1144 | 4623636325 | 191 | 12526867 | 0x00000000004006a4 | fmadd | —/12526867 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1426 | 1145 | 9405415250 | 191 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1146 | — | 4681159175 | 192 | 12619069 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe07f737da61e0c→0x3fe07f737da65e0c | — | — | origin |
| carrier_state | 1147 | 1146 | 4681159175 | 192 | 12619069 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe07f737da61e0c→0x3fe07f737da65e0c | — | — | fsu_taint |
| operand_read | 1148 | 1147 | 4681167645 | 192 | 12619085 | 0x00000000004006a4 | fmadd | 12619069/12619085 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1149 | 1148 | 4681167645 | 192 | 12619085 | 0x00000000004006a4 | fmadd | 12619069/12619085 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1150 | 1149 | 4681167645 | 192 | 12619085 | 0x00000000004006a4 | fmadd | 12619069/12619085 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1151 | 1150 | 4681168415 | 192 | 12619085 | 0x00000000004006a4 | fmadd | —/12619085 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1427 | 1151 | 9405415250 | 192 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1152 | — | 4726281560 | 193 | 12670515 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fea1f3a57eaa2a1→0x3fea1f3a57ea22a1 | — | — | origin |
| carrier_state | 1153 | 1152 | 4726281560 | 193 | 12670515 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fea1f3a57eaa2a1→0x3fea1f3a57ea22a1 | — | — | fsu_taint |
| operand_read | 1154 | 1153 | 4726290030 | 193 | 12670531 | 0x00000000004006cc | fmadd | 12670515/12670531 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1155 | 1154 | 4726290030 | 193 | 12670531 | 0x00000000004006cc | fmadd | 12670515/12670531 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1156 | 1155 | 4726290030 | 193 | 12670531 | 0x00000000004006cc | fmadd | 12670515/12670531 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1157 | 1156 | 4726290800 | 193 | 12670531 | 0x00000000004006cc | fmadd | —/12670531 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1428 | 1157 | 9405415250 | 193 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1158 | — | 4749080490 | 194 | 12713283 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fd8ec41dd1a21ea→0x3fd8ec41dd1a21ca | — | — | origin |
| carrier_state | 1159 | 1158 | 4749080490 | 194 | 12713283 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fd8ec41dd1a21ea→0x3fd8ec41dd1a21ca | — | — | fsu_taint |
| operand_read | 1160 | 1159 | 4749088960 | 194 | 12713299 | 0x00000000004006cc | fmadd | 12713283/12713299 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1161 | 1160 | 4749088960 | 194 | 12713299 | 0x00000000004006cc | fmadd | 12713283/12713299 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1162 | 1161 | 4749088960 | 194 | 12713299 | 0x00000000004006cc | fmadd | 12713283/12713299 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1163 | 1162 | 4749089730 | 194 | 12713299 | 0x00000000004006cc | fmadd | —/12713299 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1429 | 1163 | 9405415250 | 194 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1164 | — | 4804599800 | 195 | 12783679 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3ff786b59146e4c2→0x3ff786b59146a4c2 | — | — | origin |
| carrier_state | 1165 | 1164 | 4804599800 | 195 | 12783679 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3ff786b59146e4c2→0x3ff786b59146a4c2 | — | — | fsu_taint |
| operand_read | 1166 | 1165 | 4804891245 | 195 | 12783695 | 0x00000000004006a4 | fmadd | 12783679/12783695 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1167 | 1166 | 4804891245 | 195 | 12783695 | 0x00000000004006a4 | fmadd | 12783679/12783695 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1168 | 1167 | 4804891245 | 195 | 12783695 | 0x00000000004006a4 | fmadd | 12783679/12783695 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1169 | 1168 | 4804892015 | 195 | 12783695 | 0x00000000004006a4 | fmadd | —/12783695 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1430 | 1169 | 9405415250 | 195 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1170 | — | 4846286060 | 196 | 12852061 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff6ee84ad794a6f→0x3ff6ee84ad794a2f | — | — | origin |
| carrier_state | 1171 | 1170 | 4846286060 | 196 | 12852061 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff6ee84ad794a6f→0x3ff6ee84ad794a2f | — | — | fsu_taint |
| operand_read | 1172 | 1171 | 4846294530 | 196 | 12852077 | 0x00000000004006cc | fmadd | 12852061/12852077 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1173 | 1172 | 4846294530 | 196 | 12852077 | 0x00000000004006cc | fmadd | 12852061/12852077 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1174 | 1173 | 4846294530 | 196 | 12852077 | 0x00000000004006cc | fmadd | 12852061/12852077 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1175 | 1174 | 4846295300 | 196 | 12852077 | 0x00000000004006cc | fmadd | —/12852077 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1431 | 1175 | 9405415250 | 196 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1176 | — | 4926555480 | 197 | 12958895 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fef39f127f5e850→0x3fef39f127f5e858 | — | — | origin |
| carrier_state | 1177 | 1176 | 4926555480 | 197 | 12958895 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fef39f127f5e850→0x3fef39f127f5e858 | — | — | fsu_taint |
| operand_read | 1178 | 1177 | 4926563950 | 197 | 12958911 | 0x00000000004006cc | fmadd | 12958895/12958911 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1179 | 1178 | 4926563950 | 197 | 12958911 | 0x00000000004006cc | fmadd | 12958895/12958911 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1180 | 1179 | 4926563950 | 197 | 12958911 | 0x00000000004006cc | fmadd | 12958895/12958911 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1181 | 1180 | 4926564720 | 197 | 12958911 | 0x00000000004006cc | fmadd | —/12958911 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1432 | 1181 | 9405415250 | 197 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1182 | — | 4966910025 | 198 | 13020091 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3feb2599ed7c6fbe→0x3feb2599ed7c67be | — | — | origin |
| carrier_state | 1183 | 1182 | 4966910025 | 198 | 13020091 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3feb2599ed7c6fbe→0x3feb2599ed7c67be | — | — | fsu_taint |
| operand_read | 1184 | 1183 | 4966918495 | 198 | 13020107 | 0x00000000004006a4 | fmadd | 13020091/13020107 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1185 | 1184 | 4966918495 | 198 | 13020107 | 0x00000000004006a4 | fmadd | 13020091/13020107 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1186 | 1185 | 4966918495 | 198 | 13020107 | 0x00000000004006a4 | fmadd | 13020091/13020107 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1187 | 1186 | 4966919265 | 198 | 13020107 | 0x00000000004006a4 | fmadd | —/13020107 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1433 | 1187 | 9405415250 | 198 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1188 | — | 5018965490 | 199 | 13088489 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff499eb6390c910→0x3ff499eb6392c910 | — | — | origin |
| carrier_state | 1189 | 1188 | 5018965490 | 199 | 13088489 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff499eb6390c910→0x3ff499eb6392c910 | — | — | fsu_taint |
| operand_read | 1190 | 1189 | 5018973960 | 199 | 13088505 | 0x00000000004006cc | fmadd | 13088489/13088505 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1191 | 1190 | 5018973960 | 199 | 13088505 | 0x00000000004006cc | fmadd | 13088489/13088505 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1192 | 1191 | 5018973960 | 199 | 13088505 | 0x00000000004006cc | fmadd | 13088489/13088505 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1193 | 1192 | 5018974730 | 199 | 13088505 | 0x00000000004006cc | fmadd | —/13088505 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1434 | 1193 | 9405415250 | 199 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 6 | — | 49372785 | 2 | 157612 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfda6e978d4fdf3b→0xbfda6e978d4fdf1b | — | — | origin |
| carrier_state | 7 | 6 | 49372785 | 2 | 157612 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfda6e978d4fdf3b→0xbfda6e978d4fdf1b | — | — | fsu_taint |
| operand_read | 8 | 7 | 49388185 | 2 | 157682 | 0x0000000000400654 | fmadd | 157612/157682 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 49388185 | 2 | 157682 | 0x0000000000400654 | fmadd | 157612/157682 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 49388185 | 2 | 157682 | 0x0000000000400654 | fmadd | 157612/157682 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 49388955 | 2 | 157682 | 0x0000000000400654 | fmadd | —/157682 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1237 | 11 | 9405415250 | 2 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 114 | — | 354504535 | 20 | 1361164 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfc0a3d70a3d70a4→0xbfc0a3d70a3c70a4 | — | — | origin |
| carrier_state | 115 | 114 | 354504535 | 20 | 1361164 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0xbfc0a3d70a3d70a4→0xbfc0a3d70a3c70a4 | — | — | fsu_taint |
| operand_read | 116 | 115 | 354519935 | 20 | 1361234 | 0x0000000000400654 | fmadd | 1361164/1361234 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 117 | 116 | 354519935 | 20 | 1361234 | 0x0000000000400654 | fmadd | 1361164/1361234 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 118 | 117 | 354519935 | 20 | 1361234 | 0x0000000000400654 | fmadd | 1361164/1361234 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 119 | 118 | 354520705 | 20 | 1361234 | 0x0000000000400654 | fmadd | —/1361234 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1255 | 119 | 9405415250 | 20 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1194 | — | 5055274455 | 200 | 13144557 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fed5ad96a6a0125→0x3fed5ad96a6a0124 | — | — | origin |
| carrier_state | 1195 | 1194 | 5055274455 | 200 | 13144557 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fed5ad96a6a0125→0x3fed5ad96a6a0124 | — | — | fsu_taint |
| operand_read | 1196 | 1195 | 5055282925 | 200 | 13144573 | 0x00000000004006a4 | fmadd | 13144557/13144573 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1197 | 1196 | 5055282925 | 200 | 13144573 | 0x00000000004006a4 | fmadd | 13144557/13144573 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1198 | 1197 | 5055282925 | 200 | 13144573 | 0x00000000004006a4 | fmadd | 13144557/13144573 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1199 | 1198 | 5055283695 | 200 | 13144573 | 0x00000000004006a4 | fmadd | —/13144573 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1435 | 1199 | 9405415250 | 200 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1200 | — | 5107651395 | 201 | 13211099 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fd7bd9cae21101c→0x3fd7bd9cae21141c | — | — | origin |
| carrier_state | 1201 | 1200 | 5107651395 | 201 | 13211099 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fd7bd9cae21101c→0x3fd7bd9cae21141c | — | — | fsu_taint |
| operand_read | 1202 | 1201 | 5107659865 | 201 | 13211115 | 0x00000000004006cc | fmadd | 13211099/13211115 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1203 | 1202 | 5107659865 | 201 | 13211115 | 0x00000000004006cc | fmadd | 13211099/13211115 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1204 | 1203 | 5107659865 | 201 | 13211115 | 0x00000000004006cc | fmadd | 13211099/13211115 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1205 | 1204 | 5107660635 | 201 | 13211115 | 0x00000000004006cc | fmadd | —/13211115 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1436 | 1205 | 9405415250 | 201 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1206 | — | 5163400935 | 202 | 13293543 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ff31e6eeb702602→0x3ff31e6eeb702606 | — | — | origin |
| carrier_state | 1207 | 1206 | 5163400935 | 202 | 13293543 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ff31e6eeb702602→0x3ff31e6eeb702606 | — | — | fsu_taint |
| operand_read | 1208 | 1207 | 5163409405 | 202 | 13293559 | 0x00000000004006a4 | fmadd | 13293543/13293559 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1209 | 1208 | 5163409405 | 202 | 13293559 | 0x00000000004006a4 | fmadd | 13293543/13293559 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1210 | 1209 | 5163409405 | 202 | 13293559 | 0x00000000004006a4 | fmadd | 13293543/13293559 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1211 | 1210 | 5163410175 | 202 | 13293559 | 0x00000000004006a4 | fmadd | —/13293559 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1437 | 1211 | 9405415250 | 202 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1212 | — | 5223429365 | 203 | 13385013 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe39b4784230fcf→0x3fe39b4784231fcf | — | — | origin |
| carrier_state | 1213 | 1212 | 5223429365 | 203 | 13385013 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe39b4784230fcf→0x3fe39b4784231fcf | — | — | fsu_taint |
| operand_read | 1214 | 1213 | 5223437835 | 203 | 13385029 | 0x00000000004006cc | fmadd | 13385013/13385029 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1215 | 1214 | 5223437835 | 203 | 13385029 | 0x00000000004006cc | fmadd | 13385013/13385029 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1216 | 1215 | 5223437835 | 203 | 13385029 | 0x00000000004006cc | fmadd | 13385013/13385029 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1217 | 1216 | 5223438605 | 203 | 13385029 | 0x00000000004006cc | fmadd | —/13385029 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1438 | 1217 | 9405415250 | 203 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1218 | — | 5307411340 | 204 | 13498287 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fedd7c6fbd273d7→0x3fedd7c6fbd272d7 | — | — | origin |
| carrier_state | 1219 | 1218 | 5307411340 | 204 | 13498287 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fedd7c6fbd273d7→0x3fedd7c6fbd272d7 | — | — | fsu_taint |
| operand_read | 1220 | 1219 | 5307419810 | 204 | 13498303 | 0x00000000004006cc | fmadd | 13498287/13498303 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1221 | 1220 | 5307419810 | 204 | 13498303 | 0x00000000004006cc | fmadd | 13498287/13498303 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1222 | 1221 | 5307419810 | 204 | 13498303 | 0x00000000004006cc | fmadd | 13498287/13498303 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1223 | 1222 | 5307420580 | 204 | 13498303 | 0x00000000004006cc | fmadd | —/13498303 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1439 | 1223 | 9405415250 | 204 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1224 | — | 5351062255 | 205 | 13556635 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3ff2997b30f8c650→0x3ff2997b30f8c652 | — | — | origin |
| carrier_state | 1225 | 1224 | 5351062255 | 205 | 13556635 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3ff2997b30f8c650→0x3ff2997b30f8c652 | — | — | fsu_taint |
| operand_read | 1226 | 1225 | 5351070725 | 205 | 13556651 | 0x00000000004006a4 | fmadd | 13556635/13556651 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1227 | 1226 | 5351070725 | 205 | 13556651 | 0x00000000004006a4 | fmadd | 13556635/13556651 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1228 | 1227 | 5351070725 | 205 | 13556651 | 0x00000000004006a4 | fmadd | 13556635/13556651 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1229 | 1228 | 5351071495 | 205 | 13556651 | 0x00000000004006a4 | fmadd | —/13556651 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1440 | 1229 | 9405415250 | 205 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1230 | — | 5385550170 | 206 | 13600705 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff4793dd97f62b7→0x3ff4793dd97fe2b7 | — | — | origin |
| carrier_state | 1231 | 1230 | 5385550170 | 206 | 13600705 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff4793dd97f62b7→0x3ff4793dd97fe2b7 | — | — | fsu_taint |
| operand_read | 1232 | 1231 | 5385558640 | 206 | 13600721 | 0x00000000004006cc | fmadd | 13600705/13600721 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1233 | 1232 | 5385558640 | 206 | 13600721 | 0x00000000004006cc | fmadd | 13600705/13600721 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1234 | 1233 | 5385558640 | 206 | 13600721 | 0x00000000004006cc | fmadd | 13600705/13600721 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1235 | 1234 | 5385559410 | 206 | 13600721 | 0x00000000004006cc | fmadd | —/13600721 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1441 | 1235 | 9405415250 | 206 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 120 | — | 365033130 | 21 | 1402850 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3fe89ba5e353f7cf→0x3fe89ba5e353f78f | — | — | origin |
| carrier_state | 121 | 120 | 365033130 | 21 | 1402850 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3fe89ba5e353f7cf→0x3fe89ba5e353f78f | — | — | fsu_taint |
| operand_read | 122 | 121 | 365068550 | 21 | 1402994 | 0x0000000000400654 | fmadd | 1402850/1402994 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 123 | 122 | 365068550 | 21 | 1402994 | 0x0000000000400654 | fmadd | 1402850/1402994 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 124 | 123 | 365068550 | 21 | 1402994 | 0x0000000000400654 | fmadd | 1402850/1402994 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 125 | 124 | 365069320 | 21 | 1402994 | 0x0000000000400654 | fmadd | —/1402994 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1256 | 125 | 9405415250 | 21 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 126 | — | 375131680 | 22 | 1442915 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4080000000000000→0x4080000000008000 | — | — | origin |
| carrier_state | 127 | 126 | 375131680 | 22 | 1442915 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4080000000000000→0x4080000000008000 | — | — | fsu_taint |
| operand_read | 128 | 127 | 375133605 | 22 | 1442918 | 0x0000000000400654 | fmadd | 1442915/1442918 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 129 | 128 | 375133605 | 22 | 1442918 | 0x0000000000400654 | fmadd | 1442915/1442918 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 130 | 129 | 375133605 | 22 | 1442918 | 0x0000000000400654 | fmadd | 1442915/1442918 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 131 | 130 | 375134375 | 22 | 1442918 | 0x0000000000400654 | fmadd | —/1442918 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1257 | 131 | 9405415250 | 22 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 132 | — | 385275660 | 23 | 1482843 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fd09374bc6a7efa→0x3fd09374bc6a7ffa | — | — | origin |
| carrier_state | 133 | 132 | 385275660 | 23 | 1482843 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fd09374bc6a7efa→0x3fd09374bc6a7ffa | — | — | fsu_taint |
| operand_read | 134 | 133 | 385299915 | 23 | 1482950 | 0x0000000000400654 | fmadd | 1482843/1482950 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 135 | 134 | 385299915 | 23 | 1482950 | 0x0000000000400654 | fmadd | 1482843/1482950 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 136 | 135 | 385299915 | 23 | 1482950 | 0x0000000000400654 | fmadd | 1482843/1482950 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 137 | 136 | 385300685 | 23 | 1482950 | 0x0000000000400654 | fmadd | —/1482950 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1258 | 137 | 9405415250 | 23 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 138 | — | 407681120 | 24 | 1571075 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4081800000000000→0x4081800000010000 | — | — | origin |
| carrier_state | 139 | 138 | 407681120 | 24 | 1571075 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4081800000000000→0x4081800000010000 | — | — | fsu_taint |
| operand_read | 140 | 139 | 407683045 | 24 | 1571078 | 0x0000000000400654 | fmadd | 1571075/1571078 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 141 | 140 | 407683045 | 24 | 1571078 | 0x0000000000400654 | fmadd | 1571075/1571078 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 142 | 141 | 407683045 | 24 | 1571078 | 0x0000000000400654 | fmadd | 1571075/1571078 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 143 | 142 | 407683815 | 24 | 1571078 | 0x0000000000400654 | fmadd | —/1571078 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1259 | 143 | 9405415250 | 24 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 144 | — | 417599875 | 25 | 1610391 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3ff10624dd2f1aa0→0x3ff10624dd2f9aa0 | — | — | origin |
| carrier_state | 145 | 144 | 417599875 | 25 | 1610391 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3ff10624dd2f1aa0→0x3ff10624dd2f9aa0 | — | — | fsu_taint |
| operand_read | 146 | 145 | 417624130 | 25 | 1610498 | 0x0000000000400654 | fmadd | 1610391/1610498 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 147 | 146 | 417624130 | 25 | 1610498 | 0x0000000000400654 | fmadd | 1610391/1610498 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 148 | 147 | 417624130 | 25 | 1610498 | 0x0000000000400654 | fmadd | 1610391/1610498 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 149 | 148 | 417624900 | 25 | 1610498 | 0x0000000000400654 | fmadd | —/1610498 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1260 | 149 | 9405415250 | 25 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 150 | — | 435360310 | 26 | 1680407 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x4072300000000000→0x4072300000000001 | — | — | origin |
| carrier_state | 151 | 150 | 435360310 | 26 | 1680407 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x4072300000000000→0x4072300000000001 | — | — | fsu_taint |
| operand_read | 152 | 151 | 435362235 | 26 | 1680410 | 0x0000000000400654 | fmadd | 1680407/1680410 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 153 | 152 | 435362235 | 26 | 1680410 | 0x0000000000400654 | fmadd | 1680407/1680410 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 154 | 153 | 435362235 | 26 | 1680410 | 0x0000000000400654 | fmadd | 1680407/1680410 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 155 | 154 | 435363005 | 26 | 1680410 | 0x0000000000400654 | fmadd | —/1680410 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1261 | 155 | 9405415250 | 26 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 156 | — | 444712345 | 27 | 1717420 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0xbfa4fdf3b645a1c9→0xbfa4fdf3b644a1c9 | — | — | origin |
| carrier_state | 157 | 156 | 444712345 | 27 | 1717420 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0xbfa4fdf3b645a1c9→0xbfa4fdf3b644a1c9 | — | — | fsu_taint |
| operand_read | 158 | 157 | 444727745 | 27 | 1717490 | 0x0000000000400654 | fmadd | 1717420/1717490 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 159 | 158 | 444727745 | 27 | 1717490 | 0x0000000000400654 | fmadd | 1717420/1717490 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 160 | 159 | 444727745 | 27 | 1717490 | 0x0000000000400654 | fmadd | 1717420/1717490 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 161 | 160 | 444728515 | 27 | 1717490 | 0x0000000000400654 | fmadd | —/1717490 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1262 | 161 | 9405415250 | 27 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 162 | — | 457127055 | 28 | 1765803 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fe78d4fdf3b645a→0x3fe78d4fdf3b655a | — | — | origin |
| carrier_state | 163 | 162 | 457127055 | 28 | 1765803 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fe78d4fdf3b645a→0x3fe78d4fdf3b655a | — | — | fsu_taint |
| operand_read | 164 | 163 | 457151310 | 28 | 1765910 | 0x0000000000400654 | fmadd | 1765803/1765910 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 165 | 164 | 457151310 | 28 | 1765910 | 0x0000000000400654 | fmadd | 1765803/1765910 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 166 | 165 | 457151310 | 28 | 1765910 | 0x0000000000400654 | fmadd | 1765803/1765910 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 167 | 166 | 457152080 | 28 | 1765910 | 0x0000000000400654 | fmadd | —/1765910 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1263 | 167 | 9405415250 | 28 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 168 | — | 478705920 | 29 | 1851375 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fd1374bc6a7ef9e→0x3fd1374bc6a5ef9e | — | — | origin |
| carrier_state | 169 | 168 | 478705920 | 29 | 1851375 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fd1374bc6a7ef9e→0x3fd1374bc6a5ef9e | — | — | fsu_taint |
| operand_read | 170 | 169 | 478730175 | 29 | 1851482 | 0x0000000000400654 | fmadd | 1851375/1851482 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 171 | 170 | 478730175 | 29 | 1851482 | 0x0000000000400654 | fmadd | 1851375/1851482 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 172 | 171 | 478730175 | 29 | 1851482 | 0x0000000000400654 | fmadd | 1851375/1851482 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 173 | 172 | 478730945 | 29 | 1851482 | 0x0000000000400654 | fmadd | —/1851482 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1264 | 173 | 9405415250 | 29 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 12 | — | 64836310 | 3 | 218557 | 0x0000000000400650 | scvtf | —/— | 1 | — | 64@0 | 0x4075300000000000→0x4075300000000001 | — | — | origin |
| carrier_state | 13 | 12 | 64836310 | 3 | 218557 | 0x0000000000400650 | scvtf | —/— | 1 | — | 64@0 | 0x4075300000000000→0x4075300000000001 | — | — | fsu_taint |
| operand_read | 14 | 13 | 64840160 | 3 | 218560 | 0x000000000040065c | fmadd | 218557/218560 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 15 | 14 | 64840160 | 3 | 218560 | 0x000000000040065c | fmadd | 218557/218560 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 16 | 15 | 64840160 | 3 | 218560 | 0x000000000040065c | fmadd | 218557/218560 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 17 | 16 | 64840930 | 3 | 218560 | 0x000000000040065c | fmadd | —/218560 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1238 | 17 | 9405415250 | 3 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 174 | — | 494194855 | 30 | 1912467 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fe34395810624dd→0x3fe34395810624cd | — | — | origin |
| carrier_state | 175 | 174 | 494194855 | 30 | 1912467 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fe34395810624dd→0x3fe34395810624cd | — | — | fsu_taint |
| operand_read | 176 | 175 | 494219110 | 30 | 1912574 | 0x0000000000400654 | fmadd | 1912467/1912574 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 177 | 176 | 494219110 | 30 | 1912574 | 0x0000000000400654 | fmadd | 1912467/1912574 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 178 | 177 | 494219110 | 30 | 1912574 | 0x0000000000400654 | fmadd | 1912467/1912574 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 179 | 178 | 494219880 | 30 | 1912574 | 0x0000000000400654 | fmadd | —/1912574 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1265 | 179 | 9405415250 | 30 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 180 | — | 505922725 | 31 | 1958725 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4087880000000000→0x4087880000004000 | — | — | origin |
| carrier_state | 181 | 180 | 505922725 | 31 | 1958725 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4087880000000000→0x4087880000004000 | — | — | fsu_taint |
| operand_read | 182 | 181 | 505926575 | 31 | 1958728 | 0x000000000040065c | fmadd | 1958725/1958728 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 183 | 182 | 505926575 | 31 | 1958728 | 0x000000000040065c | fmadd | 1958725/1958728 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 184 | 183 | 505926575 | 31 | 1958728 | 0x000000000040065c | fmadd | 1958725/1958728 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 185 | 184 | 505927345 | 31 | 1958728 | 0x000000000040065c | fmadd | —/1958728 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1266 | 185 | 9405415250 | 31 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 186 | — | 514413130 | 32 | 1992242 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff17ced916872b0→0x3ff17ced916872b4 | — | — | origin |
| carrier_state | 187 | 186 | 514413130 | 32 | 1992242 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff17ced916872b0→0x3ff17ced916872b4 | — | — | fsu_taint |
| operand_read | 188 | 187 | 514448550 | 32 | 1992386 | 0x0000000000400654 | fmadd | 1992242/1992386 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 189 | 188 | 514448550 | 32 | 1992386 | 0x0000000000400654 | fmadd | 1992242/1992386 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 190 | 189 | 514448550 | 32 | 1992386 | 0x0000000000400654 | fmadd | 1992242/1992386 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 191 | 190 | 514449320 | 32 | 1992386 | 0x0000000000400654 | fmadd | —/1992386 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1267 | 191 | 9405415250 | 32 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 192 | — | 532188965 | 33 | 2062299 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fdc395810624dd3→0x3fdc39581062cdd3 | — | — | origin |
| carrier_state | 193 | 192 | 532188965 | 33 | 2062299 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fdc395810624dd3→0x3fdc39581062cdd3 | — | — | fsu_taint |
| operand_read | 194 | 193 | 532213220 | 33 | 2062406 | 0x0000000000400654 | fmadd | 2062299/2062406 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 195 | 194 | 532213220 | 33 | 2062406 | 0x0000000000400654 | fmadd | 2062299/2062406 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 196 | 195 | 532213220 | 33 | 2062406 | 0x0000000000400654 | fmadd | 2062299/2062406 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 197 | 196 | 532213990 | 33 | 2062406 | 0x0000000000400654 | fmadd | —/2062406 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1268 | 197 | 9405415250 | 33 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 198 | — | 552389145 | 34 | 2142036 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4063200000000000→0x4063200000008000 | — | — | origin |
| carrier_state | 199 | 198 | 552389145 | 34 | 2142036 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4063200000000000→0x4063200000008000 | — | — | fsu_taint |
| operand_read | 200 | 199 | 552393380 | 34 | 2142039 | 0x0000000000400658 | fmadd | 2142036/2142039 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 201 | 200 | 552393380 | 34 | 2142039 | 0x0000000000400658 | fmadd | 2142036/2142039 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 202 | 201 | 552393380 | 34 | 2142039 | 0x0000000000400658 | fmadd | 2142036/2142039 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 203 | 202 | 552394150 | 34 | 2142039 | 0x0000000000400658 | fmadd | —/2142039 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1269 | 203 | 9405415250 | 34 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 204 | — | 564008060 | 35 | 2188264 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfa26e978d4fdf3a→0xbfa26e978d4fdfba | — | — | origin |
| carrier_state | 205 | 204 | 564008060 | 35 | 2188264 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfa26e978d4fdf3a→0xbfa26e978d4fdfba | — | — | fsu_taint |
| operand_read | 206 | 205 | 564023460 | 35 | 2188334 | 0x0000000000400654 | fmadd | 2188264/2188334 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 207 | 206 | 564023460 | 35 | 2188334 | 0x0000000000400654 | fmadd | 2188264/2188334 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 208 | 207 | 564023460 | 35 | 2188334 | 0x0000000000400654 | fmadd | 2188264/2188334 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 209 | 208 | 564024230 | 35 | 2188334 | 0x0000000000400654 | fmadd | —/2188334 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1270 | 209 | 9405415250 | 35 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 210 | — | 578936435 | 36 | 2246689 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4060a00000000000→0x4060a00000008000 | — | — | origin |
| carrier_state | 211 | 210 | 578936435 | 36 | 2246689 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4060a00000000000→0x4060a00000008000 | — | — | fsu_taint |
| operand_read | 212 | 211 | 578940285 | 36 | 2246692 | 0x000000000040065c | fmadd | 2246689/2246692 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 213 | 212 | 578940285 | 36 | 2246692 | 0x000000000040065c | fmadd | 2246689/2246692 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 214 | 213 | 578940285 | 36 | 2246692 | 0x000000000040065c | fmadd | 2246689/2246692 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 215 | 214 | 578941055 | 36 | 2246692 | 0x000000000040065c | fmadd | —/2246692 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1271 | 215 | 9405415250 | 36 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 216 | — | 587823390 | 37 | 2281823 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4035000000000000→0x4035000000020000 | — | — | origin |
| carrier_state | 217 | 216 | 587823390 | 37 | 2281823 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4035000000000000→0x4035000000020000 | — | — | fsu_taint |
| operand_read | 218 | 217 | 587825315 | 37 | 2281826 | 0x0000000000400654 | fmadd | 2281823/2281826 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 219 | 218 | 587825315 | 37 | 2281826 | 0x0000000000400654 | fmadd | 2281823/2281826 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 220 | 219 | 587825315 | 37 | 2281826 | 0x0000000000400654 | fmadd | 2281823/2281826 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 221 | 220 | 587826085 | 37 | 2281826 | 0x0000000000400654 | fmadd | —/2281826 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1272 | 221 | 9405415250 | 37 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 222 | — | 604252880 | 38 | 2346840 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x404b800000000000→0x404b800000000040 | — | — | origin |
| carrier_state | 223 | 222 | 604252880 | 38 | 2346840 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x404b800000000000→0x404b800000000040 | — | — | fsu_taint |
| operand_read | 224 | 223 | 604257115 | 38 | 2346843 | 0x0000000000400658 | fmadd | 2346840/2346843 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 225 | 224 | 604257115 | 38 | 2346843 | 0x0000000000400658 | fmadd | 2346840/2346843 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 226 | 225 | 604257115 | 38 | 2346843 | 0x0000000000400658 | fmadd | 2346840/2346843 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 227 | 226 | 604257885 | 38 | 2346843 | 0x0000000000400658 | fmadd | —/2346843 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1273 | 227 | 9405415250 | 38 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 228 | — | 616325710 | 39 | 2394144 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x408ba00000000000→0x408ba00000000004 | — | — | origin |
| carrier_state | 229 | 228 | 616325710 | 39 | 2394144 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x408ba00000000000→0x408ba00000000004 | — | — | fsu_taint |
| operand_read | 230 | 229 | 616329945 | 39 | 2394147 | 0x0000000000400658 | fmadd | 2394144/2394147 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 231 | 230 | 616329945 | 39 | 2394147 | 0x0000000000400658 | fmadd | 2394144/2394147 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 232 | 231 | 616329945 | 39 | 2394147 | 0x0000000000400658 | fmadd | 2394144/2394147 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 233 | 232 | 616330715 | 39 | 2394147 | 0x0000000000400658 | fmadd | —/2394147 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1274 | 233 | 9405415250 | 39 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 18 | — | 86689295 | 4 | 305171 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4088200000000000→0x4088200000004000 | — | — | origin |
| carrier_state | 19 | 18 | 86689295 | 4 | 305171 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4088200000000000→0x4088200000004000 | — | — | fsu_taint |
| operand_read | 20 | 19 | 86691220 | 4 | 305174 | 0x0000000000400654 | fmadd | 305171/305174 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 21 | 20 | 86691220 | 4 | 305174 | 0x0000000000400654 | fmadd | 305171/305174 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 22 | 21 | 86691220 | 4 | 305174 | 0x0000000000400654 | fmadd | 305171/305174 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 23 | 22 | 86691990 | 4 | 305174 | 0x0000000000400654 | fmadd | —/305174 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1239 | 23 | 9405415250 | 4 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 234 | — | 632446815 | 40 | 2458332 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4087d00000000000→0x4087d00000000004 | — | — | origin |
| carrier_state | 235 | 234 | 632446815 | 40 | 2458332 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4087d00000000000→0x4087d00000000004 | — | — | fsu_taint |
| operand_read | 236 | 235 | 632451050 | 40 | 2458335 | 0x0000000000400658 | fmadd | 2458332/2458335 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 237 | 236 | 632451050 | 40 | 2458335 | 0x0000000000400658 | fmadd | 2458332/2458335 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 238 | 237 | 632451050 | 40 | 2458335 | 0x0000000000400658 | fmadd | 2458332/2458335 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 239 | 238 | 632451820 | 40 | 2458335 | 0x0000000000400658 | fmadd | —/2458335 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1275 | 239 | 9405415250 | 40 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 240 | — | 649202400 | 41 | 2523995 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4062c00000000000→0x4062c00000008000 | — | — | origin |
| carrier_state | 241 | 240 | 649202400 | 41 | 2523995 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4062c00000000000→0x4062c00000008000 | — | — | fsu_taint |
| operand_read | 242 | 241 | 649204325 | 41 | 2523998 | 0x0000000000400654 | fmadd | 2523995/2523998 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 243 | 242 | 649204325 | 41 | 2523998 | 0x0000000000400654 | fmadd | 2523995/2523998 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 244 | 243 | 649204325 | 41 | 2523998 | 0x0000000000400654 | fmadd | 2523995/2523998 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 245 | 244 | 649205095 | 41 | 2523998 | 0x0000000000400654 | fmadd | —/2523998 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1276 | 245 | 9405415250 | 41 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 246 | — | 658231805 | 42 | 2559709 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x4034000000000000→0x4034000000000020 | — | — | origin |
| carrier_state | 247 | 246 | 658231805 | 42 | 2559709 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x4034000000000000→0x4034000000000020 | — | — | fsu_taint |
| operand_read | 248 | 247 | 658235655 | 42 | 2559712 | 0x000000000040065c | fmadd | 2559709/2559712 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 249 | 248 | 658235655 | 42 | 2559712 | 0x000000000040065c | fmadd | 2559709/2559712 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 250 | 249 | 658235655 | 42 | 2559712 | 0x000000000040065c | fmadd | 2559709/2559712 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 251 | 250 | 658236425 | 42 | 2559712 | 0x000000000040065c | fmadd | —/2559712 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1277 | 251 | 9405415250 | 42 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 252 | — | 679636650 | 43 | 2644416 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x408ab00000000000→0x408ab00000000020 | — | — | origin |
| carrier_state | 253 | 252 | 679636650 | 43 | 2644416 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x408ab00000000000→0x408ab00000000020 | — | — | fsu_taint |
| operand_read | 254 | 253 | 679640885 | 43 | 2644419 | 0x0000000000400658 | fmadd | 2644416/2644419 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 255 | 254 | 679640885 | 43 | 2644419 | 0x0000000000400658 | fmadd | 2644416/2644419 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 256 | 255 | 679640885 | 43 | 2644419 | 0x0000000000400658 | fmadd | 2644416/2644419 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 257 | 256 | 679641655 | 43 | 2644419 | 0x0000000000400658 | fmadd | —/2644419 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1278 | 257 | 9405415250 | 43 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 258 | — | 693780780 | 44 | 2699966 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff14fdf3b645a1d→0x3ff14fdf3b645a3d | — | — | origin |
| carrier_state | 259 | 258 | 693780780 | 44 | 2699966 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff14fdf3b645a1d→0x3ff14fdf3b645a3d | — | — | fsu_taint |
| operand_read | 260 | 259 | 693816200 | 44 | 2700110 | 0x0000000000400654 | fmadd | 2699966/2700110 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 261 | 260 | 693816200 | 44 | 2700110 | 0x0000000000400654 | fmadd | 2699966/2700110 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 262 | 261 | 693816200 | 44 | 2700110 | 0x0000000000400654 | fmadd | 2699966/2700110 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 263 | 262 | 693816970 | 44 | 2700110 | 0x0000000000400654 | fmadd | —/2700110 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1279 | 263 | 9405415250 | 44 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 264 | — | 710627995 | 45 | 2766171 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3ff3e353f7ced917→0x3ff3e353f7cedb17 | — | — | origin |
| carrier_state | 265 | 264 | 710627995 | 45 | 2766171 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3ff3e353f7ced917→0x3ff3e353f7cedb17 | — | — | fsu_taint |
| operand_read | 266 | 265 | 710652250 | 45 | 2766278 | 0x0000000000400654 | fmadd | 2766171/2766278 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 267 | 266 | 710652250 | 45 | 2766278 | 0x0000000000400654 | fmadd | 2766171/2766278 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 268 | 267 | 710652250 | 45 | 2766278 | 0x0000000000400654 | fmadd | 2766171/2766278 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 269 | 268 | 710653020 | 45 | 2766278 | 0x0000000000400654 | fmadd | —/2766278 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1280 | 269 | 9405415250 | 45 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 270 | — | 726665170 | 46 | 2830032 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4061000000000000→0x4061000000008000 | — | — | origin |
| carrier_state | 271 | 270 | 726665170 | 46 | 2830032 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4061000000000000→0x4061000000008000 | — | — | fsu_taint |
| operand_read | 272 | 271 | 726669405 | 46 | 2830035 | 0x0000000000400658 | fmadd | 2830032/2830035 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 273 | 272 | 726669405 | 46 | 2830035 | 0x0000000000400658 | fmadd | 2830032/2830035 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 274 | 273 | 726669405 | 46 | 2830035 | 0x0000000000400658 | fmadd | 2830032/2830035 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 275 | 274 | 726670175 | 46 | 2830035 | 0x0000000000400658 | fmadd | —/2830035 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1281 | 275 | 9405415250 | 46 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 276 | — | 743903930 | 47 | 2897787 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fee978d4fdf3b64→0x3fee978d4fdf3b65 | — | — | origin |
| carrier_state | 277 | 276 | 743903930 | 47 | 2897787 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fee978d4fdf3b64→0x3fee978d4fdf3b65 | — | — | fsu_taint |
| operand_read | 278 | 277 | 743928185 | 47 | 2897894 | 0x0000000000400654 | fmadd | 2897787/2897894 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 279 | 278 | 743928185 | 47 | 2897894 | 0x0000000000400654 | fmadd | 2897787/2897894 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 280 | 279 | 743928185 | 47 | 2897894 | 0x0000000000400654 | fmadd | 2897787/2897894 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 281 | 280 | 743928955 | 47 | 2897894 | 0x0000000000400654 | fmadd | —/2897894 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1282 | 281 | 9405415250 | 47 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 282 | — | 761658590 | 48 | 2967662 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff49374bc6a7efa→0x3ff49374bc6afefa | — | — | origin |
| carrier_state | 283 | 282 | 761658590 | 48 | 2967662 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff49374bc6a7efa→0x3ff49374bc6afefa | — | — | fsu_taint |
| operand_read | 284 | 283 | 761694010 | 48 | 2967806 | 0x0000000000400654 | fmadd | 2967662/2967806 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 285 | 284 | 761694010 | 48 | 2967806 | 0x0000000000400654 | fmadd | 2967662/2967806 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 286 | 285 | 761694010 | 48 | 2967806 | 0x0000000000400654 | fmadd | 2967662/2967806 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 287 | 286 | 761694780 | 48 | 2967806 | 0x0000000000400654 | fmadd | —/2967806 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1283 | 287 | 9405415250 | 48 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 288 | — | 777491715 | 49 | 3030515 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4089e00000000000→0x4089e00000000800 | — | — | origin |
| carrier_state | 289 | 288 | 777491715 | 49 | 3030515 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4089e00000000000→0x4089e00000000800 | — | — | fsu_taint |
| operand_read | 290 | 289 | 777493640 | 49 | 3030518 | 0x0000000000400654 | fmadd | 3030515/3030518 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 291 | 290 | 777493640 | 49 | 3030518 | 0x0000000000400654 | fmadd | 3030515/3030518 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 292 | 291 | 777493640 | 49 | 3030518 | 0x0000000000400654 | fmadd | 3030515/3030518 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 293 | 292 | 777494410 | 49 | 3030518 | 0x0000000000400654 | fmadd | —/3030518 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1284 | 293 | 9405415250 | 49 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 24 | — | 100358720 | 5 | 359279 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x4031000000000000→0x4031000000000080 | — | — | origin |
| carrier_state | 25 | 24 | 100358720 | 5 | 359279 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x4031000000000000→0x4031000000000080 | — | — | fsu_taint |
| operand_read | 26 | 25 | 100360645 | 5 | 359282 | 0x0000000000400654 | fmadd | 359279/359282 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 27 | 26 | 100360645 | 5 | 359282 | 0x0000000000400654 | fmadd | 359279/359282 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 28 | 27 | 100360645 | 5 | 359282 | 0x0000000000400654 | fmadd | 359279/359282 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 29 | 28 | 100361415 | 5 | 359282 | 0x0000000000400654 | fmadd | —/359282 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1240 | 29 | 9405415250 | 5 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 294 | — | 791870310 | 50 | 3087000 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4072b00000000000→0x4072b00000000010 | — | — | origin |
| carrier_state | 295 | 294 | 791870310 | 50 | 3087000 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4072b00000000000→0x4072b00000000010 | — | — | fsu_taint |
| operand_read | 296 | 295 | 791874545 | 50 | 3087003 | 0x0000000000400658 | fmadd | 3087000/3087003 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 297 | 296 | 791874545 | 50 | 3087003 | 0x0000000000400658 | fmadd | 3087000/3087003 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 298 | 297 | 791874545 | 50 | 3087003 | 0x0000000000400658 | fmadd | 3087000/3087003 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 299 | 298 | 791875315 | 50 | 3087003 | 0x0000000000400658 | fmadd | —/3087003 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1285 | 299 | 9405415250 | 50 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 300 | — | 812273000 | 51 | 3167103 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fde45a1cac08313→0x3fde45a1cac09313 | — | — | origin |
| carrier_state | 301 | 300 | 812273000 | 51 | 3167103 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fde45a1cac08313→0x3fde45a1cac09313 | — | — | fsu_taint |
| operand_read | 302 | 301 | 812297255 | 51 | 3167210 | 0x0000000000400654 | fmadd | 3167103/3167210 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 303 | 302 | 812297255 | 51 | 3167210 | 0x0000000000400654 | fmadd | 3167103/3167210 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 304 | 303 | 812297255 | 51 | 3167210 | 0x0000000000400654 | fmadd | 3167103/3167210 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 305 | 304 | 812298025 | 51 | 3167210 | 0x0000000000400654 | fmadd | —/3167210 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1286 | 305 | 9405415250 | 51 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 306 | — | 832779255 | 52 | 3248318 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3fe50e5604189375→0x3fe50e560418937d | — | — | origin |
| carrier_state | 307 | 306 | 832779255 | 52 | 3248318 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3fe50e5604189375→0x3fe50e560418937d | — | — | fsu_taint |
| operand_read | 308 | 307 | 832814675 | 52 | 3248462 | 0x0000000000400654 | fmadd | 3248318/3248462 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 309 | 308 | 832814675 | 52 | 3248462 | 0x0000000000400654 | fmadd | 3248318/3248462 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 310 | 309 | 832814675 | 52 | 3248462 | 0x0000000000400654 | fmadd | 3248318/3248462 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 311 | 310 | 832815445 | 52 | 3248462 | 0x0000000000400654 | fmadd | —/3248462 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1287 | 311 | 9405415250 | 52 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 312 | — | 852960955 | 53 | 3328060 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfddd2f1a9fbe76d→0xbfddd2f1a9fbe77d | — | — | origin |
| carrier_state | 313 | 312 | 852960955 | 53 | 3328060 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfddd2f1a9fbe76d→0xbfddd2f1a9fbe77d | — | — | fsu_taint |
| operand_read | 314 | 313 | 852976355 | 53 | 3328130 | 0x0000000000400654 | fmadd | 3328060/3328130 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 315 | 314 | 852976355 | 53 | 3328130 | 0x0000000000400654 | fmadd | 3328060/3328130 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 316 | 315 | 852976355 | 53 | 3328130 | 0x0000000000400654 | fmadd | 3328060/3328130 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 317 | 316 | 852977125 | 53 | 3328130 | 0x0000000000400654 | fmadd | —/3328130 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1288 | 317 | 9405415250 | 53 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 318 | — | 870840740 | 54 | 3398871 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff004189374bc6b→0x3ff004189374bc2b | — | — | origin |
| carrier_state | 319 | 318 | 870840740 | 54 | 3398871 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff004189374bc6b→0x3ff004189374bc2b | — | — | fsu_taint |
| operand_read | 320 | 319 | 870864995 | 54 | 3398978 | 0x0000000000400654 | fmadd | 3398871/3398978 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 321 | 320 | 870864995 | 54 | 3398978 | 0x0000000000400654 | fmadd | 3398871/3398978 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 322 | 321 | 870864995 | 54 | 3398978 | 0x0000000000400654 | fmadd | 3398871/3398978 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 323 | 322 | 870865765 | 54 | 3398978 | 0x0000000000400654 | fmadd | —/3398978 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1289 | 323 | 9405415250 | 54 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 324 | — | 886331600 | 55 | 3459999 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fe526e978d4fdf4→0x3fe526e978d4fff4 | — | — | origin |
| carrier_state | 325 | 324 | 886331600 | 55 | 3459999 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fe526e978d4fdf4→0x3fe526e978d4fff4 | — | — | fsu_taint |
| operand_read | 326 | 325 | 886355855 | 55 | 3460106 | 0x0000000000400654 | fmadd | 3459999/3460106 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 327 | 326 | 886355855 | 55 | 3460106 | 0x0000000000400654 | fmadd | 3459999/3460106 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 328 | 327 | 886355855 | 55 | 3460106 | 0x0000000000400654 | fmadd | 3459999/3460106 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 329 | 328 | 886356625 | 55 | 3460106 | 0x0000000000400654 | fmadd | —/3460106 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1290 | 329 | 9405415250 | 55 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 330 | — | 903241955 | 56 | 3526345 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4083800000000000→0x4083800000000080 | — | — | origin |
| carrier_state | 331 | 330 | 903241955 | 56 | 3526345 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4083800000000000→0x4083800000000080 | — | — | fsu_taint |
| operand_read | 332 | 331 | 903245805 | 56 | 3526348 | 0x000000000040065c | fmadd | 3526345/3526348 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 333 | 332 | 903245805 | 56 | 3526348 | 0x000000000040065c | fmadd | 3526345/3526348 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 334 | 333 | 903245805 | 56 | 3526348 | 0x000000000040065c | fmadd | 3526345/3526348 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 335 | 334 | 903246575 | 56 | 3526348 | 0x000000000040065c | fmadd | —/3526348 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1291 | 335 | 9405415250 | 56 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 336 | — | 911509445 | 57 | 3558961 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4085880000000000→0x4085880000000020 | — | — | origin |
| carrier_state | 337 | 336 | 911509445 | 57 | 3558961 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4085880000000000→0x4085880000000020 | — | — | fsu_taint |
| operand_read | 338 | 337 | 911513295 | 57 | 3558964 | 0x000000000040065c | fmadd | 3558961/3558964 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 339 | 338 | 911513295 | 57 | 3558964 | 0x000000000040065c | fmadd | 3558961/3558964 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 340 | 339 | 911513295 | 57 | 3558964 | 0x000000000040065c | fmadd | 3558961/3558964 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 341 | 340 | 911514065 | 57 | 3558964 | 0x000000000040065c | fmadd | —/3558964 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1292 | 341 | 9405415250 | 57 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 342 | — | 924617925 | 58 | 3610440 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x407dd00000000000→0x407dd00000000100 | — | — | origin |
| carrier_state | 343 | 342 | 924617925 | 58 | 3610440 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x407dd00000000000→0x407dd00000000100 | — | — | fsu_taint |
| operand_read | 344 | 343 | 924622160 | 58 | 3610443 | 0x0000000000400658 | fmadd | 3610440/3610443 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 345 | 344 | 924622160 | 58 | 3610443 | 0x0000000000400658 | fmadd | 3610440/3610443 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 346 | 345 | 924622160 | 58 | 3610443 | 0x0000000000400658 | fmadd | 3610440/3610443 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 347 | 346 | 924622930 | 58 | 3610443 | 0x0000000000400658 | fmadd | —/3610443 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1293 | 347 | 9405415250 | 58 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 348 | — | 939033095 | 59 | 3667536 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4081900000000000→0x4081900000000008 | — | — | origin |
| carrier_state | 349 | 348 | 939033095 | 59 | 3667536 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4081900000000000→0x4081900000000008 | — | — | fsu_taint |
| operand_read | 350 | 349 | 939037330 | 59 | 3667539 | 0x0000000000400658 | fmadd | 3667536/3667539 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 351 | 350 | 939037330 | 59 | 3667539 | 0x0000000000400658 | fmadd | 3667536/3667539 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 352 | 351 | 939037330 | 59 | 3667539 | 0x0000000000400658 | fmadd | 3667536/3667539 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 353 | 352 | 939038100 | 59 | 3667539 | 0x0000000000400658 | fmadd | —/3667539 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1294 | 353 | 9405415250 | 59 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 30 | — | 120401050 | 6 | 437943 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fea8f5c28f5c28f→0x3fea8f5c28f5c28d | — | — | origin |
| carrier_state | 31 | 30 | 120401050 | 6 | 437943 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fea8f5c28f5c28f→0x3fea8f5c28f5c28d | — | — | fsu_taint |
| operand_read | 32 | 31 | 120425305 | 6 | 438050 | 0x0000000000400654 | fmadd | 437943/438050 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 33 | 32 | 120425305 | 6 | 438050 | 0x0000000000400654 | fmadd | 437943/438050 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 34 | 33 | 120425305 | 6 | 438050 | 0x0000000000400654 | fmadd | 437943/438050 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 35 | 34 | 120426075 | 6 | 438050 | 0x0000000000400654 | fmadd | —/438050 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1241 | 35 | 9405415250 | 6 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 354 | — | 949414620 | 60 | 3708504 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4086300000000000→0x4086300000001000 | — | — | origin |
| carrier_state | 355 | 354 | 949414620 | 60 | 3708504 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4086300000000000→0x4086300000001000 | — | — | fsu_taint |
| operand_read | 356 | 355 | 949418855 | 60 | 3708507 | 0x0000000000400658 | fmadd | 3708504/3708507 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 357 | 356 | 949418855 | 60 | 3708507 | 0x0000000000400658 | fmadd | 3708504/3708507 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 358 | 357 | 949418855 | 60 | 3708507 | 0x0000000000400658 | fmadd | 3708504/3708507 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 359 | 358 | 949419625 | 60 | 3708507 | 0x0000000000400658 | fmadd | —/3708507 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1295 | 359 | 9405415250 | 60 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 360 | — | 967464575 | 61 | 3779460 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4069000000000000→0x4069000000000010 | — | — | origin |
| carrier_state | 361 | 360 | 967464575 | 61 | 3779460 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4069000000000000→0x4069000000000010 | — | — | fsu_taint |
| operand_read | 362 | 361 | 967468810 | 61 | 3779463 | 0x0000000000400658 | fmadd | 3779460/3779463 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 363 | 362 | 967468810 | 61 | 3779463 | 0x0000000000400658 | fmadd | 3779460/3779463 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 364 | 363 | 967468810 | 61 | 3779463 | 0x0000000000400658 | fmadd | 3779460/3779463 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 365 | 364 | 967469580 | 61 | 3779463 | 0x0000000000400658 | fmadd | —/3779463 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1296 | 365 | 9405415250 | 61 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 366 | — | 978109440 | 62 | 3821727 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fe3645a1cac0831→0x3fe3645a1cac08b1 | — | — | origin |
| carrier_state | 367 | 366 | 978109440 | 62 | 3821727 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fe3645a1cac0831→0x3fe3645a1cac08b1 | — | — | fsu_taint |
| operand_read | 368 | 367 | 978133695 | 62 | 3821834 | 0x0000000000400654 | fmadd | 3821727/3821834 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 369 | 368 | 978133695 | 62 | 3821834 | 0x0000000000400654 | fmadd | 3821727/3821834 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 370 | 369 | 978133695 | 62 | 3821834 | 0x0000000000400654 | fmadd | 3821727/3821834 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 371 | 370 | 978134465 | 62 | 3821834 | 0x0000000000400654 | fmadd | —/3821834 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1297 | 371 | 9405415250 | 62 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 372 | — | 994652890 | 63 | 3886599 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe5810624dd2f1b→0x3fe5810624dd2f13 | — | — | origin |
| carrier_state | 373 | 372 | 994652890 | 63 | 3886599 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe5810624dd2f1b→0x3fe5810624dd2f13 | — | — | fsu_taint |
| operand_read | 374 | 373 | 994677145 | 63 | 3886706 | 0x0000000000400654 | fmadd | 3886599/3886706 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 375 | 374 | 994677145 | 63 | 3886706 | 0x0000000000400654 | fmadd | 3886599/3886706 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 376 | 375 | 994677145 | 63 | 3886706 | 0x0000000000400654 | fmadd | 3886599/3886706 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 377 | 376 | 994677915 | 63 | 3886706 | 0x0000000000400654 | fmadd | —/3886706 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1298 | 377 | 9405415250 | 63 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 378 | — | 1015164535 | 64 | 3967454 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3fe0f5c28f5c28f6→0x3fe0f5c28f5c68f6 | — | — | origin |
| carrier_state | 379 | 378 | 1015164535 | 64 | 3967454 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3fe0f5c28f5c28f6→0x3fe0f5c28f5c68f6 | — | — | fsu_taint |
| operand_read | 380 | 379 | 1015199955 | 64 | 3967598 | 0x0000000000400654 | fmadd | 3967454/3967598 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 381 | 380 | 1015199955 | 64 | 3967598 | 0x0000000000400654 | fmadd | 3967454/3967598 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 382 | 381 | 1015199955 | 64 | 3967598 | 0x0000000000400654 | fmadd | 3967454/3967598 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 383 | 382 | 1015200725 | 64 | 3967598 | 0x0000000000400654 | fmadd | —/3967598 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1299 | 383 | 9405415250 | 64 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 384 | — | 1032926895 | 65 | 4037619 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fe589374bc6a7f0→0x3fe589374bc6a7f8 | — | — | origin |
| carrier_state | 385 | 384 | 1032926895 | 65 | 4037619 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fe589374bc6a7f0→0x3fe589374bc6a7f8 | — | — | fsu_taint |
| operand_read | 386 | 385 | 1032951150 | 65 | 4037726 | 0x0000000000400654 | fmadd | 4037619/4037726 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 387 | 386 | 1032951150 | 65 | 4037726 | 0x0000000000400654 | fmadd | 4037619/4037726 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 388 | 387 | 1032951150 | 65 | 4037726 | 0x0000000000400654 | fmadd | 4037619/4037726 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 389 | 388 | 1032951920 | 65 | 4037726 | 0x0000000000400654 | fmadd | —/4037726 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1300 | 389 | 9405415250 | 65 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 390 | — | 1052543030 | 66 | 4115342 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fea8f5c28f5c28f→0x3fea8f5c28f5c287 | — | — | origin |
| carrier_state | 391 | 390 | 1052543030 | 66 | 4115342 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fea8f5c28f5c28f→0x3fea8f5c28f5c287 | — | — | fsu_taint |
| operand_read | 392 | 391 | 1052578450 | 66 | 4115486 | 0x0000000000400654 | fmadd | 4115342/4115486 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 393 | 392 | 1052578450 | 66 | 4115486 | 0x0000000000400654 | fmadd | 4115342/4115486 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 394 | 393 | 1052578450 | 66 | 4115486 | 0x0000000000400654 | fmadd | 4115342/4115486 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 395 | 394 | 1052579220 | 66 | 4115486 | 0x0000000000400654 | fmadd | —/4115486 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1301 | 395 | 9405415250 | 66 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 396 | — | 1062498360 | 67 | 4154727 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fd3126e978d4fdf→0x3fd3126e978d4f5f | — | — | origin |
| carrier_state | 397 | 396 | 1062498360 | 67 | 4154727 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fd3126e978d4fdf→0x3fd3126e978d4f5f | — | — | fsu_taint |
| operand_read | 398 | 397 | 1062522615 | 67 | 4154834 | 0x0000000000400654 | fmadd | 4154727/4154834 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 399 | 398 | 1062522615 | 67 | 4154834 | 0x0000000000400654 | fmadd | 4154727/4154834 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 400 | 399 | 1062522615 | 67 | 4154834 | 0x0000000000400654 | fmadd | 4154727/4154834 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 401 | 400 | 1062523385 | 67 | 4154834 | 0x0000000000400654 | fmadd | —/4154834 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1302 | 401 | 9405415250 | 67 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 402 | — | 1084757135 | 68 | 4242241 | 0x0000000000400650 | scvtf | —/— | 1 | — | 64@0 | 0x4081c80000000000→0x4081c80000000020 | — | — | origin |
| carrier_state | 403 | 402 | 1084757135 | 68 | 4242241 | 0x0000000000400650 | scvtf | —/— | 1 | — | 64@0 | 0x4081c80000000000→0x4081c80000000020 | — | — | fsu_taint |
| operand_read | 404 | 403 | 1084760985 | 68 | 4242244 | 0x000000000040065c | fmadd | 4242241/4242244 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 405 | 404 | 1084760985 | 68 | 4242244 | 0x000000000040065c | fmadd | 4242241/4242244 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 406 | 405 | 1084760985 | 68 | 4242244 | 0x000000000040065c | fmadd | 4242241/4242244 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 407 | 406 | 1084761755 | 68 | 4242244 | 0x000000000040065c | fmadd | —/4242244 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1303 | 407 | 9405415250 | 68 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 408 | — | 1102733940 | 69 | 4313447 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x407b700000000000→0x407b700000000400 | — | — | origin |
| carrier_state | 409 | 408 | 1102733940 | 69 | 4313447 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x407b700000000000→0x407b700000000400 | — | — | fsu_taint |
| operand_read | 410 | 409 | 1102735865 | 69 | 4313450 | 0x0000000000400654 | fmadd | 4313447/4313450 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 411 | 410 | 1102735865 | 69 | 4313450 | 0x0000000000400654 | fmadd | 4313447/4313450 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 412 | 411 | 1102735865 | 69 | 4313450 | 0x0000000000400654 | fmadd | 4313447/4313450 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 413 | 412 | 1102736635 | 69 | 4313450 | 0x0000000000400654 | fmadd | —/4313450 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1304 | 413 | 9405415250 | 69 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 36 | — | 138442535 | 7 | 509546 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff1b645a1cac083→0x3ff1b645a1cac883 | — | — | origin |
| carrier_state | 37 | 36 | 138442535 | 7 | 509546 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff1b645a1cac083→0x3ff1b645a1cac883 | — | — | fsu_taint |
| operand_read | 38 | 37 | 138477955 | 7 | 509690 | 0x0000000000400654 | fmadd | 509546/509690 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 39 | 38 | 138477955 | 7 | 509690 | 0x0000000000400654 | fmadd | 509546/509690 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 40 | 39 | 138477955 | 7 | 509690 | 0x0000000000400654 | fmadd | 509546/509690 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 41 | 40 | 138478725 | 7 | 509690 | 0x0000000000400654 | fmadd | —/509690 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1242 | 41 | 9405415250 | 7 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 414 | — | 1115867060 | 70 | 4365107 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4028000000000000→0x4028000000010000 | — | — | origin |
| carrier_state | 415 | 414 | 1115867060 | 70 | 4365107 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4028000000000000→0x4028000000010000 | — | — | fsu_taint |
| operand_read | 416 | 415 | 1115868985 | 70 | 4365110 | 0x0000000000400654 | fmadd | 4365107/4365110 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 417 | 416 | 1115868985 | 70 | 4365110 | 0x0000000000400654 | fmadd | 4365107/4365110 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 418 | 417 | 1115868985 | 70 | 4365110 | 0x0000000000400654 | fmadd | 4365107/4365110 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 419 | 418 | 1115869755 | 70 | 4365110 | 0x0000000000400654 | fmadd | —/4365110 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1305 | 419 | 9405415250 | 70 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 420 | — | 1124940355 | 71 | 4401000 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4088d80000000000→0x4088d80000002000 | — | — | origin |
| carrier_state | 421 | 420 | 1124940355 | 71 | 4401000 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4088d80000000000→0x4088d80000002000 | — | — | fsu_taint |
| operand_read | 422 | 421 | 1124944590 | 71 | 4401003 | 0x0000000000400658 | fmadd | 4401000/4401003 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 423 | 422 | 1124944590 | 71 | 4401003 | 0x0000000000400658 | fmadd | 4401000/4401003 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 424 | 423 | 1124944590 | 71 | 4401003 | 0x0000000000400658 | fmadd | 4401000/4401003 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 425 | 424 | 1124945360 | 71 | 4401003 | 0x0000000000400658 | fmadd | —/4401003 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1306 | 425 | 9405415250 | 71 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 426 | — | 1132607245 | 72 | 4431640 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfdd916872b020c5→0xbfdd916872b028c5 | — | — | origin |
| carrier_state | 427 | 426 | 1132607245 | 72 | 4431640 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfdd916872b020c5→0xbfdd916872b028c5 | — | — | fsu_taint |
| operand_read | 428 | 427 | 1132622645 | 72 | 4431710 | 0x0000000000400654 | fmadd | 4431640/4431710 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 429 | 428 | 1132622645 | 72 | 4431710 | 0x0000000000400654 | fmadd | 4431640/4431710 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 430 | 429 | 1132622645 | 72 | 4431710 | 0x0000000000400654 | fmadd | 4431640/4431710 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 431 | 430 | 1132623415 | 72 | 4431710 | 0x0000000000400654 | fmadd | —/4431710 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1307 | 431 | 9405415250 | 72 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 432 | — | 1154501425 | 73 | 4517498 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff7cac083126e98→0x3ff7cac083126e9c | — | — | origin |
| carrier_state | 433 | 432 | 1154501425 | 73 | 4517498 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff7cac083126e98→0x3ff7cac083126e9c | — | — | fsu_taint |
| operand_read | 434 | 433 | 1154536845 | 73 | 4517642 | 0x0000000000400654 | fmadd | 4517498/4517642 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 435 | 434 | 1154536845 | 73 | 4517642 | 0x0000000000400654 | fmadd | 4517498/4517642 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 436 | 435 | 1154536845 | 73 | 4517642 | 0x0000000000400654 | fmadd | 4517498/4517642 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 437 | 436 | 1154537615 | 73 | 4517642 | 0x0000000000400654 | fmadd | —/4517642 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1308 | 437 | 9405415250 | 73 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 438 | — | 1167775455 | 74 | 4569948 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x408a180000000000→0x408a180000000100 | — | — | origin |
| carrier_state | 439 | 438 | 1167775455 | 74 | 4569948 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x408a180000000000→0x408a180000000100 | — | — | fsu_taint |
| operand_read | 440 | 439 | 1167779690 | 74 | 4569951 | 0x0000000000400658 | fmadd | 4569948/4569951 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 441 | 440 | 1167779690 | 74 | 4569951 | 0x0000000000400658 | fmadd | 4569948/4569951 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 442 | 441 | 1167779690 | 74 | 4569951 | 0x0000000000400658 | fmadd | 4569948/4569951 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 443 | 442 | 1167780460 | 74 | 4569951 | 0x0000000000400658 | fmadd | —/4569951 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1309 | 443 | 9405415250 | 74 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 444 | — | 1188908875 | 75 | 4653469 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x406bc00000000000→0x406bc00000010000 | — | — | origin |
| carrier_state | 445 | 444 | 1188908875 | 75 | 4653469 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x406bc00000000000→0x406bc00000010000 | — | — | fsu_taint |
| operand_read | 446 | 445 | 1188912725 | 75 | 4653472 | 0x000000000040065c | fmadd | 4653469/4653472 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 447 | 446 | 1188912725 | 75 | 4653472 | 0x000000000040065c | fmadd | 4653469/4653472 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 448 | 447 | 1188912725 | 75 | 4653472 | 0x000000000040065c | fmadd | 4653469/4653472 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 449 | 448 | 1188913495 | 75 | 4653472 | 0x000000000040065c | fmadd | —/4653472 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1310 | 449 | 9405415250 | 75 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 450 | — | 1206211545 | 76 | 4721545 | 0x0000000000400650 | scvtf | —/— | 1 | — | 64@0 | 0x4084b00000000000→0x4084b00000001000 | — | — | origin |
| carrier_state | 451 | 450 | 1206211545 | 76 | 4721545 | 0x0000000000400650 | scvtf | —/— | 1 | — | 64@0 | 0x4084b00000000000→0x4084b00000001000 | — | — | fsu_taint |
| operand_read | 452 | 451 | 1206215395 | 76 | 4721548 | 0x000000000040065c | fmadd | 4721545/4721548 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 453 | 452 | 1206215395 | 76 | 4721548 | 0x000000000040065c | fmadd | 4721545/4721548 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 454 | 453 | 1206215395 | 76 | 4721548 | 0x000000000040065c | fmadd | 4721545/4721548 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 455 | 454 | 1206216165 | 76 | 4721548 | 0x000000000040065c | fmadd | —/4721548 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1311 | 455 | 9405415250 | 76 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 456 | — | 1222758845 | 77 | 4787353 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4075700000000000→0x4075700000000800 | — | — | origin |
| carrier_state | 457 | 456 | 1222758845 | 77 | 4787353 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4075700000000000→0x4075700000000800 | — | — | fsu_taint |
| operand_read | 458 | 457 | 1222762695 | 77 | 4787356 | 0x000000000040065c | fmadd | 4787353/4787356 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 459 | 458 | 1222762695 | 77 | 4787356 | 0x000000000040065c | fmadd | 4787353/4787356 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 460 | 459 | 1222762695 | 77 | 4787356 | 0x000000000040065c | fmadd | 4787353/4787356 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 461 | 460 | 1222763465 | 77 | 4787356 | 0x000000000040065c | fmadd | —/4787356 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1312 | 461 | 9405415250 | 77 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 462 | — | 1239771995 | 78 | 4854134 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff624dd2f1a9fbf→0x3ff624dd2f1a9fb7 | — | — | origin |
| carrier_state | 463 | 462 | 1239771995 | 78 | 4854134 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff624dd2f1a9fbf→0x3ff624dd2f1a9fb7 | — | — | fsu_taint |
| operand_read | 464 | 463 | 1239807415 | 78 | 4854278 | 0x0000000000400654 | fmadd | 4854134/4854278 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 465 | 464 | 1239807415 | 78 | 4854278 | 0x0000000000400654 | fmadd | 4854134/4854278 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 466 | 465 | 1239807415 | 78 | 4854278 | 0x0000000000400654 | fmadd | 4854134/4854278 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 467 | 466 | 1239808185 | 78 | 4854278 | 0x0000000000400654 | fmadd | —/4854278 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1313 | 467 | 9405415250 | 78 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 468 | — | 1251804400 | 79 | 4901399 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x408b980000000000→0x408b980000020000 | — | — | origin |
| carrier_state | 469 | 468 | 1251804400 | 79 | 4901399 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x408b980000000000→0x408b980000020000 | — | — | fsu_taint |
| operand_read | 470 | 469 | 1251806325 | 79 | 4901402 | 0x0000000000400654 | fmadd | 4901399/4901402 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 471 | 470 | 1251806325 | 79 | 4901402 | 0x0000000000400654 | fmadd | 4901399/4901402 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 472 | 471 | 1251806325 | 79 | 4901402 | 0x0000000000400654 | fmadd | 4901399/4901402 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 473 | 472 | 1251807095 | 79 | 4901402 | 0x0000000000400654 | fmadd | —/4901402 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1314 | 473 | 9405415250 | 79 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 42 | — | 160998915 | 8 | 598393 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x4051400000000000→0x4051400000000020 | — | — | origin |
| carrier_state | 43 | 42 | 160998915 | 8 | 598393 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x4051400000000000→0x4051400000000020 | — | — | fsu_taint |
| operand_read | 44 | 43 | 161002765 | 8 | 598396 | 0x000000000040065c | fmadd | 598393/598396 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 45 | 44 | 161002765 | 8 | 598396 | 0x000000000040065c | fmadd | 598393/598396 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 46 | 45 | 161002765 | 8 | 598396 | 0x000000000040065c | fmadd | 598393/598396 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 47 | 46 | 161003535 | 8 | 598396 | 0x000000000040065c | fmadd | —/598396 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1243 | 47 | 9405415250 | 8 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 474 | — | 1267342230 | 80 | 4963103 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4087680000000000→0x4087680000010000 | — | — | origin |
| carrier_state | 475 | 474 | 1267342230 | 80 | 4963103 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4087680000000000→0x4087680000010000 | — | — | fsu_taint |
| operand_read | 476 | 475 | 1267344155 | 80 | 4963106 | 0x0000000000400654 | fmadd | 4963103/4963106 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 477 | 476 | 1267344155 | 80 | 4963106 | 0x0000000000400654 | fmadd | 4963103/4963106 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 478 | 477 | 1267344155 | 80 | 4963106 | 0x0000000000400654 | fmadd | 4963103/4963106 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 479 | 478 | 1267344925 | 80 | 4963106 | 0x0000000000400654 | fmadd | —/4963106 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1315 | 479 | 9405415250 | 80 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 480 | — | 1278298560 | 81 | 5006342 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fe2d0e560418937→0x3fe2d0e56041893f | — | — | origin |
| carrier_state | 481 | 480 | 1278298560 | 81 | 5006342 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fe2d0e560418937→0x3fe2d0e56041893f | — | — | fsu_taint |
| operand_read | 482 | 481 | 1278333980 | 81 | 5006486 | 0x0000000000400654 | fmadd | 5006342/5006486 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 483 | 482 | 1278333980 | 81 | 5006486 | 0x0000000000400654 | fmadd | 5006342/5006486 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 484 | 483 | 1278333980 | 81 | 5006486 | 0x0000000000400654 | fmadd | 5006342/5006486 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 485 | 484 | 1278334750 | 81 | 5006486 | 0x0000000000400654 | fmadd | —/5006486 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1316 | 485 | 9405415250 | 81 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 486 | — | 1288029435 | 82 | 5044900 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd21cac083126ea→0x3fd21cac083126eb | — | — | origin |
| carrier_state | 487 | 486 | 1288029435 | 82 | 5044900 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd21cac083126ea→0x3fd21cac083126eb | — | — | fsu_taint |
| operand_read | 488 | 487 | 1288044835 | 82 | 5044970 | 0x0000000000400654 | fmadd | 5044900/5044970 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 489 | 488 | 1288044835 | 82 | 5044970 | 0x0000000000400654 | fmadd | 5044900/5044970 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 490 | 489 | 1288044835 | 82 | 5044970 | 0x0000000000400654 | fmadd | 5044900/5044970 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 491 | 490 | 1288045605 | 82 | 5044970 | 0x0000000000400654 | fmadd | —/5044970 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1317 | 491 | 9405415250 | 82 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 492 | — | 1298926860 | 83 | 5087234 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fed374bc6a7ef9e→0x3fed374bc6a7ee9e | — | — | origin |
| carrier_state | 493 | 492 | 1298926860 | 83 | 5087234 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fed374bc6a7ef9e→0x3fed374bc6a7ee9e | — | — | fsu_taint |
| operand_read | 494 | 493 | 1298962280 | 83 | 5087378 | 0x0000000000400654 | fmadd | 5087234/5087378 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 495 | 494 | 1298962280 | 83 | 5087378 | 0x0000000000400654 | fmadd | 5087234/5087378 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 496 | 495 | 1298962280 | 83 | 5087378 | 0x0000000000400654 | fmadd | 5087234/5087378 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 497 | 496 | 1298963050 | 83 | 5087378 | 0x0000000000400654 | fmadd | —/5087378 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1318 | 497 | 9405415250 | 83 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 498 | — | 1307559715 | 84 | 5121327 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3febae147ae147ae→0x3febae147ae145ae | — | — | origin |
| carrier_state | 499 | 498 | 1307559715 | 84 | 5121327 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3febae147ae147ae→0x3febae147ae145ae | — | — | fsu_taint |
| operand_read | 500 | 499 | 1307583970 | 84 | 5121434 | 0x0000000000400654 | fmadd | 5121327/5121434 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 501 | 500 | 1307583970 | 84 | 5121434 | 0x0000000000400654 | fmadd | 5121327/5121434 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 502 | 501 | 1307583970 | 84 | 5121434 | 0x0000000000400654 | fmadd | 5121327/5121434 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 503 | 502 | 1307584740 | 84 | 5121434 | 0x0000000000400654 | fmadd | —/5121434 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1319 | 503 | 9405415250 | 84 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 504 | — | 1327624760 | 85 | 5200850 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fe35c28f5c28f5c→0x3fe35c28f5c28f5e | — | — | origin |
| carrier_state | 505 | 504 | 1327624760 | 85 | 5200850 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fe35c28f5c28f5c→0x3fe35c28f5c28f5e | — | — | fsu_taint |
| operand_read | 506 | 505 | 1327660180 | 85 | 5200994 | 0x0000000000400654 | fmadd | 5200850/5200994 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 507 | 506 | 1327660180 | 85 | 5200994 | 0x0000000000400654 | fmadd | 5200850/5200994 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 508 | 507 | 1327660180 | 85 | 5200994 | 0x0000000000400654 | fmadd | 5200850/5200994 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 509 | 508 | 1327660950 | 85 | 5200994 | 0x0000000000400654 | fmadd | —/5200994 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1320 | 509 | 9405415250 | 85 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 510 | — | 1336935600 | 86 | 5237713 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x4076a00000000000→0x4076a00000000040 | — | — | origin |
| carrier_state | 511 | 510 | 1336935600 | 86 | 5237713 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x4076a00000000000→0x4076a00000000040 | — | — | fsu_taint |
| operand_read | 512 | 511 | 1336939450 | 86 | 5237716 | 0x000000000040065c | fmadd | 5237713/5237716 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 513 | 512 | 1336939450 | 86 | 5237716 | 0x000000000040065c | fmadd | 5237713/5237716 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 514 | 513 | 1336939450 | 86 | 5237716 | 0x000000000040065c | fmadd | 5237713/5237716 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 515 | 514 | 1336940220 | 86 | 5237716 | 0x000000000040065c | fmadd | —/5237716 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1321 | 515 | 9405415250 | 86 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 516 | — | 1348714290 | 87 | 5284192 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0x3fdfced916872b02→0x3fdfced916872b82 | — | — | origin |
| carrier_state | 517 | 516 | 1348714290 | 87 | 5284192 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0x3fdfced916872b02→0x3fdfced916872b82 | — | — | fsu_taint |
| operand_read | 518 | 517 | 1348729690 | 87 | 5284262 | 0x0000000000400654 | fmadd | 5284192/5284262 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 519 | 518 | 1348729690 | 87 | 5284262 | 0x0000000000400654 | fmadd | 5284192/5284262 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 520 | 519 | 1348729690 | 87 | 5284262 | 0x0000000000400654 | fmadd | 5284192/5284262 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 521 | 520 | 1348730460 | 87 | 5284262 | 0x0000000000400654 | fmadd | —/5284262 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1322 | 521 | 9405415250 | 87 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 522 | — | 1368217235 | 88 | 5360656 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd3d70a3d70a3d7→0x3fd3d70a3d7083d7 | — | — | origin |
| carrier_state | 523 | 522 | 1368217235 | 88 | 5360656 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd3d70a3d70a3d7→0x3fd3d70a3d7083d7 | — | — | fsu_taint |
| operand_read | 524 | 523 | 1368232635 | 88 | 5360726 | 0x0000000000400654 | fmadd | 5360656/5360726 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 525 | 524 | 1368232635 | 88 | 5360726 | 0x0000000000400654 | fmadd | 5360656/5360726 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 526 | 525 | 1368232635 | 88 | 5360726 | 0x0000000000400654 | fmadd | 5360656/5360726 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 527 | 526 | 1368233405 | 88 | 5360726 | 0x0000000000400654 | fmadd | —/5360726 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1323 | 527 | 9405415250 | 88 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 528 | — | 1379840770 | 89 | 5406916 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfb9db22d0e56041→0xbfb9db22d0e46041 | — | — | origin |
| carrier_state | 529 | 528 | 1379840770 | 89 | 5406916 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfb9db22d0e56041→0xbfb9db22d0e46041 | — | — | fsu_taint |
| operand_read | 530 | 529 | 1379856170 | 89 | 5406986 | 0x0000000000400654 | fmadd | 5406916/5406986 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 531 | 530 | 1379856170 | 89 | 5406986 | 0x0000000000400654 | fmadd | 5406916/5406986 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 532 | 531 | 1379856170 | 89 | 5406986 | 0x0000000000400654 | fmadd | 5406916/5406986 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 533 | 532 | 1379856940 | 89 | 5406986 | 0x0000000000400654 | fmadd | —/5406986 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1324 | 533 | 9405415250 | 89 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 48 | — | 179911655 | 9 | 672947 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4070400000000000→0x4070400000020000 | — | — | origin |
| carrier_state | 49 | 48 | 179911655 | 9 | 672947 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4070400000000000→0x4070400000020000 | — | — | fsu_taint |
| operand_read | 50 | 49 | 179913580 | 9 | 672950 | 0x0000000000400654 | fmadd | 672947/672950 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 51 | 50 | 179913580 | 9 | 672950 | 0x0000000000400654 | fmadd | 672947/672950 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 52 | 51 | 179913580 | 9 | 672950 | 0x0000000000400654 | fmadd | 672947/672950 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 53 | 52 | 179914350 | 9 | 672950 | 0x0000000000400654 | fmadd | —/672950 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1244 | 53 | 9405415250 | 9 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 534 | — | 1390846380 | 90 | 5450328 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x407b100000000000→0x407b100000008000 | — | — | origin |
| carrier_state | 535 | 534 | 1390846380 | 90 | 5450328 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x407b100000000000→0x407b100000008000 | — | — | fsu_taint |
| operand_read | 536 | 535 | 1390850615 | 90 | 5450331 | 0x0000000000400658 | fmadd | 5450328/5450331 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 537 | 536 | 1390850615 | 90 | 5450331 | 0x0000000000400658 | fmadd | 5450328/5450331 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 538 | 537 | 1390850615 | 90 | 5450331 | 0x0000000000400658 | fmadd | 5450328/5450331 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 539 | 538 | 1390851385 | 90 | 5450331 | 0x0000000000400658 | fmadd | —/5450331 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1325 | 539 | 9405415250 | 90 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 540 | — | 1408090145 | 91 | 5518441 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x404e800000000000→0x404e800000004000 | — | — | origin |
| carrier_state | 541 | 540 | 1408090145 | 91 | 5518441 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x404e800000000000→0x404e800000004000 | — | — | fsu_taint |
| operand_read | 542 | 541 | 1408093995 | 91 | 5518444 | 0x000000000040065c | fmadd | 5518441/5518444 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 543 | 542 | 1408093995 | 91 | 5518444 | 0x000000000040065c | fmadd | 5518441/5518444 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 544 | 543 | 1408093995 | 91 | 5518444 | 0x000000000040065c | fmadd | 5518441/5518444 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 545 | 544 | 1408094765 | 91 | 5518444 | 0x000000000040065c | fmadd | —/5518444 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1326 | 545 | 9405415250 | 91 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 546 | — | 1425052475 | 92 | 5585148 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4089c80000000000→0x4089c80000000010 | — | — | origin |
| carrier_state | 547 | 546 | 1425052475 | 92 | 5585148 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4089c80000000000→0x4089c80000000010 | — | — | fsu_taint |
| operand_read | 548 | 547 | 1425056710 | 92 | 5585151 | 0x0000000000400658 | fmadd | 5585148/5585151 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 549 | 548 | 1425056710 | 92 | 5585151 | 0x0000000000400658 | fmadd | 5585148/5585151 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 550 | 549 | 1425056710 | 92 | 5585151 | 0x0000000000400658 | fmadd | 5585148/5585151 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 551 | 550 | 1425057480 | 92 | 5585151 | 0x0000000000400658 | fmadd | —/5585151 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1327 | 551 | 9405415250 | 92 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 552 | — | 1441278300 | 93 | 5649299 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4059000000000000→0x4059000000000002 | — | — | origin |
| carrier_state | 553 | 552 | 1441278300 | 93 | 5649299 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4059000000000000→0x4059000000000002 | — | — | fsu_taint |
| operand_read | 554 | 553 | 1441280225 | 93 | 5649302 | 0x0000000000400654 | fmadd | 5649299/5649302 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 555 | 554 | 1441280225 | 93 | 5649302 | 0x0000000000400654 | fmadd | 5649299/5649302 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 556 | 555 | 1441280225 | 93 | 5649302 | 0x0000000000400654 | fmadd | 5649299/5649302 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 557 | 556 | 1441280995 | 93 | 5649302 | 0x0000000000400654 | fmadd | —/5649302 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1328 | 557 | 9405415250 | 93 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 558 | — | 1455089790 | 94 | 5703985 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4020000000000000→0x4020000000008000 | — | — | origin |
| carrier_state | 559 | 558 | 1455089790 | 94 | 5703985 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4020000000000000→0x4020000000008000 | — | — | fsu_taint |
| operand_read | 560 | 559 | 1455093640 | 94 | 5703988 | 0x000000000040065c | fmadd | 5703985/5703988 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 561 | 560 | 1455093640 | 94 | 5703988 | 0x000000000040065c | fmadd | 5703985/5703988 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 562 | 561 | 1455093640 | 94 | 5703988 | 0x000000000040065c | fmadd | 5703985/5703988 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 563 | 562 | 1455094410 | 94 | 5703988 | 0x000000000040065c | fmadd | —/5703988 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1329 | 563 | 9405415250 | 94 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 564 | — | 1467536840 | 95 | 5752623 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fef1a9fbe76c8b4→0x3fef1a9fbe76cab4 | — | — | origin |
| carrier_state | 565 | 564 | 1467536840 | 95 | 5752623 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fef1a9fbe76c8b4→0x3fef1a9fbe76cab4 | — | — | fsu_taint |
| operand_read | 566 | 565 | 1467561095 | 95 | 5752730 | 0x0000000000400654 | fmadd | 5752623/5752730 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 567 | 566 | 1467561095 | 95 | 5752730 | 0x0000000000400654 | fmadd | 5752623/5752730 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 568 | 567 | 1467561095 | 95 | 5752730 | 0x0000000000400654 | fmadd | 5752623/5752730 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 569 | 568 | 1467561865 | 95 | 5752730 | 0x0000000000400654 | fmadd | —/5752730 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1330 | 569 | 9405415250 | 95 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 570 | — | 1487964555 | 96 | 5833480 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd49ba5e353f7cf→0xbfd49ba5e353f7ce | — | — | origin |
| carrier_state | 571 | 570 | 1487964555 | 96 | 5833480 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd49ba5e353f7cf→0xbfd49ba5e353f7ce | — | — | fsu_taint |
| operand_read | 572 | 571 | 1487979955 | 96 | 5833550 | 0x0000000000400654 | fmadd | 5833480/5833550 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 573 | 572 | 1487979955 | 96 | 5833550 | 0x0000000000400654 | fmadd | 5833480/5833550 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 574 | 573 | 1487979955 | 96 | 5833550 | 0x0000000000400654 | fmadd | 5833480/5833550 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 575 | 574 | 1487980725 | 96 | 5833550 | 0x0000000000400654 | fmadd | —/5833550 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1331 | 575 | 9405415250 | 96 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 576 | — | 1509184985 | 97 | 5916959 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4084280000000000→0x4084280000000200 | — | — | origin |
| carrier_state | 577 | 576 | 1509184985 | 97 | 5916959 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4084280000000000→0x4084280000000200 | — | — | fsu_taint |
| operand_read | 578 | 577 | 1509186910 | 97 | 5916962 | 0x0000000000400654 | fmadd | 5916959/5916962 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 579 | 578 | 1509186910 | 97 | 5916962 | 0x0000000000400654 | fmadd | 5916959/5916962 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 580 | 579 | 1509186910 | 97 | 5916962 | 0x0000000000400654 | fmadd | 5916959/5916962 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 581 | 580 | 1509187680 | 97 | 5916962 | 0x0000000000400654 | fmadd | —/5916962 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1332 | 581 | 9405415250 | 97 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 582 | — | 1529860640 | 98 | 5998647 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fdcfdf3b645a1cb→0x3fdcfdf3b645a9cb | — | — | origin |
| carrier_state | 583 | 582 | 1529860640 | 98 | 5998647 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fdcfdf3b645a1cb→0x3fdcfdf3b645a9cb | — | — | fsu_taint |
| operand_read | 584 | 583 | 1529884895 | 98 | 5998754 | 0x0000000000400654 | fmadd | 5998647/5998754 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 585 | 584 | 1529884895 | 98 | 5998754 | 0x0000000000400654 | fmadd | 5998647/5998754 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 586 | 585 | 1529884895 | 98 | 5998754 | 0x0000000000400654 | fmadd | 5998647/5998754 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 587 | 586 | 1529885665 | 98 | 5998754 | 0x0000000000400654 | fmadd | —/5998754 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1333 | 587 | 9405415250 | 98 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 588 | — | 1537614540 | 99 | 6029175 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fd3851eb851eb85→0x3fd3851eb851eb81 | — | — | origin |
| carrier_state | 589 | 588 | 1537614540 | 99 | 6029175 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fd3851eb851eb85→0x3fd3851eb851eb81 | — | — | fsu_taint |
| operand_read | 590 | 589 | 1537638795 | 99 | 6029282 | 0x0000000000400654 | fmadd | 6029175/6029282 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 591 | 590 | 1537638795 | 99 | 6029282 | 0x0000000000400654 | fmadd | 6029175/6029282 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 592 | 591 | 1537638795 | 99 | 6029282 | 0x0000000000400654 | fmadd | 6029175/6029282 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 593 | 592 | 1537639565 | 99 | 6029282 | 0x0000000000400654 | fmadd | —/6029282 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1334 | 593 | 9405415250 | 99 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

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

### fault 100

- **L0**：fault_applied#594（本 seed 真实事件）。
- **L1**：carrier_state#595（本 seed 真实事件）。
- **L2**：operand_read#596（本 seed 真实事件）。
- **L3**：execute#597（本 seed 真实事件）。
- **L4**：prf_writeback#598（本 seed 真实事件）。
- **L5**：commit#599（本 seed 真实事件）。

### fault 101

- **L0**：fault_applied#600（本 seed 真实事件）。
- **L1**：carrier_state#601（本 seed 真实事件）。
- **L2**：operand_read#602（本 seed 真实事件）。
- **L3**：execute#603（本 seed 真实事件）。
- **L4**：prf_writeback#604（本 seed 真实事件）。
- **L5**：commit#605（本 seed 真实事件）。

### fault 102

- **L0**：fault_applied#606（本 seed 真实事件）。
- **L1**：carrier_state#607（本 seed 真实事件）。
- **L2**：operand_read#608（本 seed 真实事件）。
- **L3**：execute#609（本 seed 真实事件）。
- **L4**：prf_writeback#610（本 seed 真实事件）。
- **L5**：commit#611（本 seed 真实事件）。

### fault 103

- **L0**：fault_applied#612（本 seed 真实事件）。
- **L1**：carrier_state#613（本 seed 真实事件）。
- **L2**：operand_read#614（本 seed 真实事件）。
- **L3**：execute#615（本 seed 真实事件）。
- **L4**：prf_writeback#616（本 seed 真实事件）。
- **L5**：commit#617（本 seed 真实事件）。

### fault 104

- **L0**：fault_applied#618（本 seed 真实事件）。
- **L1**：carrier_state#619（本 seed 真实事件）。
- **L2**：operand_read#620（本 seed 真实事件）。
- **L3**：execute#621（本 seed 真实事件）。
- **L4**：prf_writeback#622（本 seed 真实事件）。
- **L5**：commit#623（本 seed 真实事件）。

### fault 105

- **L0**：fault_applied#624（本 seed 真实事件）。
- **L1**：carrier_state#625（本 seed 真实事件）。
- **L2**：operand_read#626（本 seed 真实事件）。
- **L3**：execute#627（本 seed 真实事件）。
- **L4**：prf_writeback#628（本 seed 真实事件）。
- **L5**：commit#629（本 seed 真实事件）。

### fault 106

- **L0**：fault_applied#630（本 seed 真实事件）。
- **L1**：carrier_state#631（本 seed 真实事件）。
- **L2**：operand_read#632（本 seed 真实事件）。
- **L3**：execute#633（本 seed 真实事件）。
- **L4**：prf_writeback#634（本 seed 真实事件）。
- **L5**：commit#635（本 seed 真实事件）。

### fault 107

- **L0**：fault_applied#636（本 seed 真实事件）。
- **L1**：carrier_state#637（本 seed 真实事件）。
- **L2**：operand_read#638（本 seed 真实事件）。
- **L3**：execute#639（本 seed 真实事件）。
- **L4**：prf_writeback#640（本 seed 真实事件）。
- **L5**：commit#641（本 seed 真实事件）。

### fault 108

- **L0**：fault_applied#642（本 seed 真实事件）。
- **L1**：carrier_state#643（本 seed 真实事件）。
- **L2**：operand_read#644（本 seed 真实事件）。
- **L3**：execute#645（本 seed 真实事件）。
- **L4**：prf_writeback#646（本 seed 真实事件）。
- **L5**：commit#647（本 seed 真实事件）。

### fault 109

- **L0**：fault_applied#648（本 seed 真实事件）。
- **L1**：carrier_state#649（本 seed 真实事件）。
- **L2**：operand_read#650（本 seed 真实事件）。
- **L3**：execute#651（本 seed 真实事件）。
- **L4**：prf_writeback#652（本 seed 真实事件）。
- **L5**：commit#653（本 seed 真实事件）。

### fault 11

- **L0**：fault_applied#60（本 seed 真实事件）。
- **L1**：carrier_state#61（本 seed 真实事件）。
- **L2**：operand_read#62（本 seed 真实事件）。
- **L3**：execute#63（本 seed 真实事件）。
- **L4**：prf_writeback#64（本 seed 真实事件）。
- **L5**：commit#65（本 seed 真实事件）。

### fault 110

- **L0**：fault_applied#654（本 seed 真实事件）。
- **L1**：carrier_state#655（本 seed 真实事件）。
- **L2**：operand_read#656（本 seed 真实事件）。
- **L3**：execute#657（本 seed 真实事件）。
- **L4**：prf_writeback#658（本 seed 真实事件）。
- **L5**：commit#659（本 seed 真实事件）。

### fault 111

- **L0**：fault_applied#660（本 seed 真实事件）。
- **L1**：carrier_state#661（本 seed 真实事件）。
- **L2**：operand_read#662（本 seed 真实事件）。
- **L3**：execute#663（本 seed 真实事件）。
- **L4**：prf_writeback#664（本 seed 真实事件）。
- **L5**：commit#665（本 seed 真实事件）。

### fault 112

- **L0**：fault_applied#666（本 seed 真实事件）。
- **L1**：carrier_state#667（本 seed 真实事件）。
- **L2**：operand_read#668（本 seed 真实事件）。
- **L3**：execute#669（本 seed 真实事件）。
- **L4**：prf_writeback#670（本 seed 真实事件）。
- **L5**：commit#671（本 seed 真实事件）。

### fault 113

- **L0**：fault_applied#672（本 seed 真实事件）。
- **L1**：carrier_state#673（本 seed 真实事件）。
- **L2**：operand_read#674（本 seed 真实事件）。
- **L3**：execute#675（本 seed 真实事件）。
- **L4**：prf_writeback#676（本 seed 真实事件）。
- **L5**：commit#677（本 seed 真实事件）。

### fault 114

- **L0**：fault_applied#678（本 seed 真实事件）。
- **L1**：carrier_state#679（本 seed 真实事件）。
- **L2**：operand_read#680（本 seed 真实事件）。
- **L3**：execute#681（本 seed 真实事件）。
- **L4**：prf_writeback#682（本 seed 真实事件）。
- **L5**：commit#683（本 seed 真实事件）。

### fault 115

- **L0**：fault_applied#684（本 seed 真实事件）。
- **L1**：carrier_state#685（本 seed 真实事件）。
- **L2**：operand_read#686（本 seed 真实事件）。
- **L3**：execute#687（本 seed 真实事件）。
- **L4**：prf_writeback#688（本 seed 真实事件）。
- **L5**：commit#689（本 seed 真实事件）。

### fault 116

- **L0**：fault_applied#690（本 seed 真实事件）。
- **L1**：carrier_state#691（本 seed 真实事件）。
- **L2**：operand_read#692（本 seed 真实事件）。
- **L3**：execute#693（本 seed 真实事件）。
- **L4**：prf_writeback#694（本 seed 真实事件）。
- **L5**：commit#695（本 seed 真实事件）。

### fault 117

- **L0**：fault_applied#696（本 seed 真实事件）。
- **L1**：carrier_state#697（本 seed 真实事件）。
- **L2**：operand_read#698（本 seed 真实事件）。
- **L3**：execute#699（本 seed 真实事件）。
- **L4**：prf_writeback#700（本 seed 真实事件）。
- **L5**：commit#701（本 seed 真实事件）。

### fault 118

- **L0**：fault_applied#702（本 seed 真实事件）。
- **L1**：carrier_state#703（本 seed 真实事件）。
- **L2**：operand_read#704（本 seed 真实事件）。
- **L3**：execute#705（本 seed 真实事件）。
- **L4**：prf_writeback#706（本 seed 真实事件）。
- **L5**：commit#707（本 seed 真实事件）。

### fault 119

- **L0**：fault_applied#708（本 seed 真实事件）。
- **L1**：carrier_state#709（本 seed 真实事件）。
- **L2**：operand_read#710（本 seed 真实事件）。
- **L3**：execute#711（本 seed 真实事件）。
- **L4**：prf_writeback#712（本 seed 真实事件）。
- **L5**：commit#713（本 seed 真实事件）。

### fault 12

- **L0**：fault_applied#66（本 seed 真实事件）。
- **L1**：carrier_state#67（本 seed 真实事件）。
- **L2**：operand_read#68（本 seed 真实事件）。
- **L3**：execute#69（本 seed 真实事件）。
- **L4**：prf_writeback#70（本 seed 真实事件）。
- **L5**：commit#71（本 seed 真实事件）。

### fault 120

- **L0**：fault_applied#714（本 seed 真实事件）。
- **L1**：carrier_state#715（本 seed 真实事件）。
- **L2**：operand_read#716（本 seed 真实事件）。
- **L3**：execute#717（本 seed 真实事件）。
- **L4**：prf_writeback#718（本 seed 真实事件）。
- **L5**：commit#719（本 seed 真实事件）。

### fault 121

- **L0**：fault_applied#720（本 seed 真实事件）。
- **L1**：carrier_state#721（本 seed 真实事件）。
- **L2**：operand_read#722（本 seed 真实事件）。
- **L3**：execute#723（本 seed 真实事件）。
- **L4**：prf_writeback#724（本 seed 真实事件）。
- **L5**：commit#725（本 seed 真实事件）。

### fault 122

- **L0**：fault_applied#726（本 seed 真实事件）。
- **L1**：carrier_state#727（本 seed 真实事件）。
- **L2**：operand_read#728（本 seed 真实事件）。
- **L3**：execute#729（本 seed 真实事件）。
- **L4**：prf_writeback#730（本 seed 真实事件）。
- **L5**：commit#731（本 seed 真实事件）。

### fault 123

- **L0**：fault_applied#732（本 seed 真实事件）。
- **L1**：carrier_state#733（本 seed 真实事件）。
- **L2**：operand_read#734（本 seed 真实事件）。
- **L3**：execute#735（本 seed 真实事件）。
- **L4**：prf_writeback#736（本 seed 真实事件）。
- **L5**：commit#737（本 seed 真实事件）。

### fault 124

- **L0**：fault_applied#738（本 seed 真实事件）。
- **L1**：carrier_state#739（本 seed 真实事件）。
- **L2**：operand_read#740（本 seed 真实事件）。
- **L3**：execute#741（本 seed 真实事件）。
- **L4**：prf_writeback#742（本 seed 真实事件）。
- **L5**：commit#743（本 seed 真实事件）。

### fault 125

- **L0**：fault_applied#744（本 seed 真实事件）。
- **L1**：carrier_state#745（本 seed 真实事件）。
- **L2**：operand_read#746（本 seed 真实事件）。
- **L3**：execute#747（本 seed 真实事件）。
- **L4**：prf_writeback#748（本 seed 真实事件）。
- **L5**：commit#749（本 seed 真实事件）。

### fault 126

- **L0**：fault_applied#750（本 seed 真实事件）。
- **L1**：carrier_state#751（本 seed 真实事件）。
- **L2**：operand_read#752（本 seed 真实事件）。
- **L3**：execute#753（本 seed 真实事件）。
- **L4**：prf_writeback#754（本 seed 真实事件）。
- **L5**：commit#755（本 seed 真实事件）。

### fault 127

- **L0**：fault_applied#756（本 seed 真实事件）。
- **L1**：carrier_state#757（本 seed 真实事件）。
- **L2**：operand_read#758（本 seed 真实事件）。
- **L3**：execute#759（本 seed 真实事件）。
- **L4**：prf_writeback#760（本 seed 真实事件）。
- **L5**：commit#761（本 seed 真实事件）。

### fault 128

- **L0**：fault_applied#762（本 seed 真实事件）。
- **L1**：carrier_state#763（本 seed 真实事件）。
- **L2**：operand_read#764（本 seed 真实事件）。
- **L3**：execute#765（本 seed 真实事件）。
- **L4**：prf_writeback#766（本 seed 真实事件）。
- **L5**：commit#767（本 seed 真实事件）。

### fault 129

- **L0**：fault_applied#768（本 seed 真实事件）。
- **L1**：carrier_state#769（本 seed 真实事件）。
- **L2**：operand_read#770（本 seed 真实事件）。
- **L3**：execute#771（本 seed 真实事件）。
- **L4**：prf_writeback#772（本 seed 真实事件）。
- **L5**：commit#773（本 seed 真实事件）。

### fault 13

- **L0**：fault_applied#72（本 seed 真实事件）。
- **L1**：carrier_state#73（本 seed 真实事件）。
- **L2**：operand_read#74（本 seed 真实事件）。
- **L3**：execute#75（本 seed 真实事件）。
- **L4**：prf_writeback#76（本 seed 真实事件）。
- **L5**：commit#77（本 seed 真实事件）。

### fault 130

- **L0**：fault_applied#774（本 seed 真实事件）。
- **L1**：carrier_state#775（本 seed 真实事件）。
- **L2**：operand_read#776（本 seed 真实事件）。
- **L3**：execute#777（本 seed 真实事件）。
- **L4**：prf_writeback#778（本 seed 真实事件）。
- **L5**：commit#779（本 seed 真实事件）。

### fault 131

- **L0**：fault_applied#780（本 seed 真实事件）。
- **L1**：carrier_state#781（本 seed 真实事件）。
- **L2**：operand_read#782（本 seed 真实事件）。
- **L3**：execute#783（本 seed 真实事件）。
- **L4**：prf_writeback#784（本 seed 真实事件）。
- **L5**：commit#785（本 seed 真实事件）。

### fault 132

- **L0**：fault_applied#786（本 seed 真实事件）。
- **L1**：carrier_state#787（本 seed 真实事件）。
- **L2**：operand_read#788（本 seed 真实事件）。
- **L3**：execute#789（本 seed 真实事件）。
- **L4**：prf_writeback#790（本 seed 真实事件）。
- **L5**：commit#791（本 seed 真实事件）。

### fault 133

- **L0**：fault_applied#792（本 seed 真实事件）。
- **L1**：carrier_state#793（本 seed 真实事件）。
- **L2**：operand_read#794（本 seed 真实事件）。
- **L3**：execute#795（本 seed 真实事件）。
- **L4**：prf_writeback#796（本 seed 真实事件）。
- **L5**：commit#797（本 seed 真实事件）。

### fault 134

- **L0**：fault_applied#798（本 seed 真实事件）。
- **L1**：carrier_state#799（本 seed 真实事件）。
- **L2**：operand_read#800（本 seed 真实事件）。
- **L3**：execute#801（本 seed 真实事件）。
- **L4**：prf_writeback#802（本 seed 真实事件）。
- **L5**：commit#803（本 seed 真实事件）。

### fault 135

- **L0**：fault_applied#804（本 seed 真实事件）。
- **L1**：carrier_state#805（本 seed 真实事件）。
- **L2**：operand_read#806（本 seed 真实事件）。
- **L3**：execute#807（本 seed 真实事件）。
- **L4**：prf_writeback#808（本 seed 真实事件）。
- **L5**：commit#809（本 seed 真实事件）。

### fault 136

- **L0**：fault_applied#810（本 seed 真实事件）。
- **L1**：carrier_state#811（本 seed 真实事件）。
- **L2**：operand_read#812（本 seed 真实事件）。
- **L3**：execute#813（本 seed 真实事件）。
- **L4**：prf_writeback#814（本 seed 真实事件）。
- **L5**：commit#815（本 seed 真实事件）。

### fault 137

- **L0**：fault_applied#816（本 seed 真实事件）。
- **L1**：carrier_state#817（本 seed 真实事件）。
- **L2**：operand_read#818（本 seed 真实事件）。
- **L3**：execute#819（本 seed 真实事件）。
- **L4**：prf_writeback#820（本 seed 真实事件）。
- **L5**：commit#821（本 seed 真实事件）。

### fault 138

- **L0**：fault_applied#822（本 seed 真实事件）。
- **L1**：carrier_state#823（本 seed 真实事件）。
- **L2**：operand_read#824（本 seed 真实事件）。
- **L3**：execute#825（本 seed 真实事件）。
- **L4**：prf_writeback#826（本 seed 真实事件）。
- **L5**：commit#827（本 seed 真实事件）。

### fault 139

- **L0**：fault_applied#828（本 seed 真实事件）。
- **L1**：carrier_state#829（本 seed 真实事件）。
- **L2**：operand_read#830（本 seed 真实事件）。
- **L3**：execute#831（本 seed 真实事件）。
- **L4**：prf_writeback#832（本 seed 真实事件）。
- **L5**：commit#833（本 seed 真实事件）。

### fault 14

- **L0**：fault_applied#78（本 seed 真实事件）。
- **L1**：carrier_state#79（本 seed 真实事件）。
- **L2**：operand_read#80（本 seed 真实事件）。
- **L3**：execute#81（本 seed 真实事件）。
- **L4**：prf_writeback#82（本 seed 真实事件）。
- **L5**：commit#83（本 seed 真实事件）。

### fault 140

- **L0**：fault_applied#834（本 seed 真实事件）。
- **L1**：carrier_state#835（本 seed 真实事件）。
- **L2**：operand_read#836（本 seed 真实事件）。
- **L3**：execute#837（本 seed 真实事件）。
- **L4**：prf_writeback#838（本 seed 真实事件）。
- **L5**：commit#839（本 seed 真实事件）。

### fault 141

- **L0**：fault_applied#840（本 seed 真实事件）。
- **L1**：carrier_state#841（本 seed 真实事件）。
- **L2**：operand_read#842（本 seed 真实事件）。
- **L3**：execute#843（本 seed 真实事件）。
- **L4**：prf_writeback#844（本 seed 真实事件）。
- **L5**：commit#845（本 seed 真实事件）。

### fault 142

- **L0**：fault_applied#846（本 seed 真实事件）。
- **L1**：carrier_state#847（本 seed 真实事件）。
- **L2**：operand_read#848（本 seed 真实事件）。
- **L3**：execute#849（本 seed 真实事件）。
- **L4**：prf_writeback#850（本 seed 真实事件）。
- **L5**：commit#851（本 seed 真实事件）。

### fault 143

- **L0**：fault_applied#852（本 seed 真实事件）。
- **L1**：carrier_state#853（本 seed 真实事件）。
- **L2**：operand_read#854（本 seed 真实事件）。
- **L3**：execute#855（本 seed 真实事件）。
- **L4**：prf_writeback#856（本 seed 真实事件）。
- **L5**：commit#857（本 seed 真实事件）。

### fault 144

- **L0**：fault_applied#858（本 seed 真实事件）。
- **L1**：carrier_state#859（本 seed 真实事件）。
- **L2**：operand_read#860（本 seed 真实事件）。
- **L3**：execute#861（本 seed 真实事件）。
- **L4**：prf_writeback#862（本 seed 真实事件）。
- **L5**：commit#863（本 seed 真实事件）。

### fault 145

- **L0**：fault_applied#864（本 seed 真实事件）。
- **L1**：carrier_state#865（本 seed 真实事件）。
- **L2**：operand_read#866（本 seed 真实事件）。
- **L3**：execute#867（本 seed 真实事件）。
- **L4**：prf_writeback#868（本 seed 真实事件）。
- **L5**：commit#869（本 seed 真实事件）。

### fault 146

- **L0**：fault_applied#870（本 seed 真实事件）。
- **L1**：carrier_state#871（本 seed 真实事件）。
- **L2**：operand_read#872（本 seed 真实事件）。
- **L3**：execute#873（本 seed 真实事件）。
- **L4**：prf_writeback#874（本 seed 真实事件）。
- **L5**：commit#875（本 seed 真实事件）。

### fault 147

- **L0**：fault_applied#876（本 seed 真实事件）。
- **L1**：carrier_state#877（本 seed 真实事件）。
- **L2**：operand_read#878（本 seed 真实事件）。
- **L3**：execute#879（本 seed 真实事件）。
- **L4**：prf_writeback#880（本 seed 真实事件）。
- **L5**：commit#881（本 seed 真实事件）。

### fault 148

- **L0**：fault_applied#882（本 seed 真实事件）。
- **L1**：carrier_state#883（本 seed 真实事件）。
- **L2**：operand_read#884（本 seed 真实事件）。
- **L3**：execute#885（本 seed 真实事件）。
- **L4**：prf_writeback#886（本 seed 真实事件）。
- **L5**：commit#887（本 seed 真实事件）。

### fault 149

- **L0**：fault_applied#888（本 seed 真实事件）。
- **L1**：carrier_state#889（本 seed 真实事件）。
- **L2**：operand_read#890（本 seed 真实事件）。
- **L3**：execute#891（本 seed 真实事件）。
- **L4**：prf_writeback#892（本 seed 真实事件）。
- **L5**：commit#893（本 seed 真实事件）。

### fault 15

- **L0**：fault_applied#84（本 seed 真实事件）。
- **L1**：carrier_state#85（本 seed 真实事件）。
- **L2**：operand_read#86（本 seed 真实事件）。
- **L3**：execute#87（本 seed 真实事件）。
- **L4**：prf_writeback#88（本 seed 真实事件）。
- **L5**：commit#89（本 seed 真实事件）。

### fault 150

- **L0**：fault_applied#894（本 seed 真实事件）。
- **L1**：carrier_state#895（本 seed 真实事件）。
- **L2**：operand_read#896（本 seed 真实事件）。
- **L3**：execute#897（本 seed 真实事件）。
- **L4**：prf_writeback#898（本 seed 真实事件）。
- **L5**：commit#899（本 seed 真实事件）。

### fault 151

- **L0**：fault_applied#900（本 seed 真实事件）。
- **L1**：carrier_state#901（本 seed 真实事件）。
- **L2**：operand_read#902（本 seed 真实事件）。
- **L3**：execute#903（本 seed 真实事件）。
- **L4**：prf_writeback#904（本 seed 真实事件）。
- **L5**：commit#905（本 seed 真实事件）。

### fault 152

- **L0**：fault_applied#906（本 seed 真实事件）。
- **L1**：carrier_state#907（本 seed 真实事件）。
- **L2**：operand_read#908（本 seed 真实事件）。
- **L3**：execute#909（本 seed 真实事件）。
- **L4**：prf_writeback#910（本 seed 真实事件）。
- **L5**：commit#911（本 seed 真实事件）。

### fault 153

- **L0**：fault_applied#912（本 seed 真实事件）。
- **L1**：carrier_state#913（本 seed 真实事件）。
- **L2**：operand_read#914（本 seed 真实事件）。
- **L3**：execute#915（本 seed 真实事件）。
- **L4**：prf_writeback#916（本 seed 真实事件）。
- **L5**：commit#917（本 seed 真实事件）。

### fault 154

- **L0**：fault_applied#918（本 seed 真实事件）。
- **L1**：carrier_state#919（本 seed 真实事件）。
- **L2**：operand_read#920（本 seed 真实事件）。
- **L3**：execute#921（本 seed 真实事件）。
- **L4**：prf_writeback#922（本 seed 真实事件）。
- **L5**：commit#923（本 seed 真实事件）。

### fault 155

- **L0**：fault_applied#924（本 seed 真实事件）。
- **L1**：carrier_state#925（本 seed 真实事件）。
- **L2**：operand_read#926（本 seed 真实事件）。
- **L3**：execute#927（本 seed 真实事件）。
- **L4**：prf_writeback#928（本 seed 真实事件）。
- **L5**：commit#929（本 seed 真实事件）。

### fault 156

- **L0**：fault_applied#930（本 seed 真实事件）。
- **L1**：carrier_state#931（本 seed 真实事件）。
- **L2**：operand_read#932（本 seed 真实事件）。
- **L3**：execute#933（本 seed 真实事件）。
- **L4**：prf_writeback#934（本 seed 真实事件）。
- **L5**：commit#935（本 seed 真实事件）。

### fault 157

- **L0**：fault_applied#936（本 seed 真实事件）。
- **L1**：carrier_state#937（本 seed 真实事件）。
- **L2**：operand_read#938（本 seed 真实事件）。
- **L3**：execute#939（本 seed 真实事件）。
- **L4**：prf_writeback#940（本 seed 真实事件）。
- **L5**：commit#941（本 seed 真实事件）。

### fault 158

- **L0**：fault_applied#942（本 seed 真实事件）。
- **L1**：carrier_state#943（本 seed 真实事件）。
- **L2**：operand_read#944（本 seed 真实事件）。
- **L3**：execute#945（本 seed 真实事件）。
- **L4**：prf_writeback#946（本 seed 真实事件）。
- **L5**：commit#947（本 seed 真实事件）。

### fault 159

- **L0**：fault_applied#948（本 seed 真实事件）。
- **L1**：carrier_state#949（本 seed 真实事件）。
- **L2**：operand_read#950（本 seed 真实事件）。
- **L3**：execute#951（本 seed 真实事件）。
- **L4**：prf_writeback#952（本 seed 真实事件）。
- **L5**：commit#953（本 seed 真实事件）。

### fault 16

- **L0**：fault_applied#90（本 seed 真实事件）。
- **L1**：carrier_state#91（本 seed 真实事件）。
- **L2**：operand_read#92（本 seed 真实事件）。
- **L3**：execute#93（本 seed 真实事件）。
- **L4**：prf_writeback#94（本 seed 真实事件）。
- **L5**：commit#95（本 seed 真实事件）。

### fault 160

- **L0**：fault_applied#954（本 seed 真实事件）。
- **L1**：carrier_state#955（本 seed 真实事件）。
- **L2**：operand_read#956（本 seed 真实事件）。
- **L3**：execute#957（本 seed 真实事件）。
- **L4**：prf_writeback#958（本 seed 真实事件）。
- **L5**：commit#959（本 seed 真实事件）。

### fault 161

- **L0**：fault_applied#960（本 seed 真实事件）。
- **L1**：carrier_state#961（本 seed 真实事件）。
- **L2**：operand_read#962（本 seed 真实事件）。
- **L3**：execute#963（本 seed 真实事件）。
- **L4**：prf_writeback#964（本 seed 真实事件）。
- **L5**：commit#965（本 seed 真实事件）。

### fault 162

- **L0**：fault_applied#966（本 seed 真实事件）。
- **L1**：carrier_state#967（本 seed 真实事件）。
- **L2**：operand_read#968（本 seed 真实事件）。
- **L3**：execute#969（本 seed 真实事件）。
- **L4**：prf_writeback#970（本 seed 真实事件）。
- **L5**：commit#971（本 seed 真实事件）。

### fault 163

- **L0**：fault_applied#972（本 seed 真实事件）。
- **L1**：carrier_state#973（本 seed 真实事件）。
- **L2**：operand_read#974（本 seed 真实事件）。
- **L3**：execute#975（本 seed 真实事件）。
- **L4**：prf_writeback#976（本 seed 真实事件）。
- **L5**：commit#977（本 seed 真实事件）。

### fault 164

- **L0**：fault_applied#978（本 seed 真实事件）。
- **L1**：carrier_state#979（本 seed 真实事件）。
- **L2**：operand_read#980（本 seed 真实事件）。
- **L3**：execute#981（本 seed 真实事件）。
- **L4**：prf_writeback#982（本 seed 真实事件）。
- **L5**：commit#983（本 seed 真实事件）。

### fault 165

- **L0**：fault_applied#984（本 seed 真实事件）。
- **L1**：carrier_state#985（本 seed 真实事件）。
- **L2**：operand_read#986（本 seed 真实事件）。
- **L3**：execute#987（本 seed 真实事件）。
- **L4**：prf_writeback#988（本 seed 真实事件）。
- **L5**：commit#989（本 seed 真实事件）。

### fault 166

- **L0**：fault_applied#990（本 seed 真实事件）。
- **L1**：carrier_state#991（本 seed 真实事件）。
- **L2**：operand_read#992（本 seed 真实事件）。
- **L3**：execute#993（本 seed 真实事件）。
- **L4**：prf_writeback#994（本 seed 真实事件）。
- **L5**：commit#995（本 seed 真实事件）。

### fault 167

- **L0**：fault_applied#996（本 seed 真实事件）。
- **L1**：carrier_state#997（本 seed 真实事件）。
- **L2**：operand_read#998（本 seed 真实事件）。
- **L3**：execute#999（本 seed 真实事件）。
- **L4**：prf_writeback#1000（本 seed 真实事件）。
- **L5**：commit#1001（本 seed 真实事件）。

### fault 168

- **L0**：fault_applied#1002（本 seed 真实事件）。
- **L1**：carrier_state#1003（本 seed 真实事件）。
- **L2**：operand_read#1004（本 seed 真实事件）。
- **L3**：execute#1005（本 seed 真实事件）。
- **L4**：prf_writeback#1006（本 seed 真实事件）。
- **L5**：commit#1007（本 seed 真实事件）。

### fault 169

- **L0**：fault_applied#1008（本 seed 真实事件）。
- **L1**：carrier_state#1009（本 seed 真实事件）。
- **L2**：operand_read#1010（本 seed 真实事件）。
- **L3**：execute#1011（本 seed 真实事件）。
- **L4**：prf_writeback#1012（本 seed 真实事件）。
- **L5**：commit#1013（本 seed 真实事件）。

### fault 17

- **L0**：fault_applied#96（本 seed 真实事件）。
- **L1**：carrier_state#97（本 seed 真实事件）。
- **L2**：operand_read#98（本 seed 真实事件）。
- **L3**：execute#99（本 seed 真实事件）。
- **L4**：prf_writeback#100（本 seed 真实事件）。
- **L5**：commit#101（本 seed 真实事件）。

### fault 170

- **L0**：fault_applied#1014（本 seed 真实事件）。
- **L1**：carrier_state#1015（本 seed 真实事件）。
- **L2**：operand_read#1016（本 seed 真实事件）。
- **L3**：execute#1017（本 seed 真实事件）。
- **L4**：prf_writeback#1018（本 seed 真实事件）。
- **L5**：commit#1019（本 seed 真实事件）。

### fault 171

- **L0**：fault_applied#1020（本 seed 真实事件）。
- **L1**：carrier_state#1021（本 seed 真实事件）。
- **L2**：operand_read#1022（本 seed 真实事件）。
- **L3**：execute#1023（本 seed 真实事件）。
- **L4**：prf_writeback#1024（本 seed 真实事件）。
- **L5**：commit#1025（本 seed 真实事件）。

### fault 172

- **L0**：fault_applied#1026（本 seed 真实事件）。
- **L1**：carrier_state#1027（本 seed 真实事件）。
- **L2**：operand_read#1028（本 seed 真实事件）。
- **L3**：execute#1029（本 seed 真实事件）。
- **L4**：prf_writeback#1030（本 seed 真实事件）。
- **L5**：commit#1031（本 seed 真实事件）。

### fault 173

- **L0**：fault_applied#1032（本 seed 真实事件）。
- **L1**：carrier_state#1033（本 seed 真实事件）。
- **L2**：operand_read#1034（本 seed 真实事件）。
- **L3**：execute#1035（本 seed 真实事件）。
- **L4**：prf_writeback#1036（本 seed 真实事件）。
- **L5**：commit#1037（本 seed 真实事件）。

### fault 174

- **L0**：fault_applied#1038（本 seed 真实事件）。
- **L1**：carrier_state#1039（本 seed 真实事件）。
- **L2**：operand_read#1040（本 seed 真实事件）。
- **L3**：execute#1041（本 seed 真实事件）。
- **L4**：prf_writeback#1042（本 seed 真实事件）。
- **L5**：commit#1043（本 seed 真实事件）。

### fault 175

- **L0**：fault_applied#1044（本 seed 真实事件）。
- **L1**：carrier_state#1045（本 seed 真实事件）。
- **L2**：operand_read#1046（本 seed 真实事件）。
- **L3**：execute#1047（本 seed 真实事件）。
- **L4**：prf_writeback#1048（本 seed 真实事件）。
- **L5**：commit#1049（本 seed 真实事件）。

### fault 176

- **L0**：fault_applied#1050（本 seed 真实事件）。
- **L1**：carrier_state#1051（本 seed 真实事件）。
- **L2**：operand_read#1052（本 seed 真实事件）。
- **L3**：execute#1053（本 seed 真实事件）。
- **L4**：prf_writeback#1054（本 seed 真实事件）。
- **L5**：commit#1055（本 seed 真实事件）。

### fault 177

- **L0**：fault_applied#1056（本 seed 真实事件）。
- **L1**：carrier_state#1057（本 seed 真实事件）。
- **L2**：operand_read#1058（本 seed 真实事件）。
- **L3**：execute#1059（本 seed 真实事件）。
- **L4**：prf_writeback#1060（本 seed 真实事件）。
- **L5**：commit#1061（本 seed 真实事件）。

### fault 178

- **L0**：fault_applied#1062（本 seed 真实事件）。
- **L1**：carrier_state#1063（本 seed 真实事件）。
- **L2**：operand_read#1064（本 seed 真实事件）。
- **L3**：execute#1065（本 seed 真实事件）。
- **L4**：prf_writeback#1066（本 seed 真实事件）。
- **L5**：commit#1067（本 seed 真实事件）。

### fault 179

- **L0**：fault_applied#1068（本 seed 真实事件）。
- **L1**：carrier_state#1069（本 seed 真实事件）。
- **L2**：operand_read#1070（本 seed 真实事件）。
- **L3**：execute#1071（本 seed 真实事件）。
- **L4**：prf_writeback#1072（本 seed 真实事件）。
- **L5**：commit#1073（本 seed 真实事件）。

### fault 18

- **L0**：fault_applied#102（本 seed 真实事件）。
- **L1**：carrier_state#103（本 seed 真实事件）。
- **L2**：operand_read#104（本 seed 真实事件）。
- **L3**：execute#105（本 seed 真实事件）。
- **L4**：prf_writeback#106（本 seed 真实事件）。
- **L5**：commit#107（本 seed 真实事件）。

### fault 180

- **L0**：fault_applied#1074（本 seed 真实事件）。
- **L1**：carrier_state#1075（本 seed 真实事件）。
- **L2**：operand_read#1076（本 seed 真实事件）。
- **L3**：execute#1077（本 seed 真实事件）。
- **L4**：prf_writeback#1078（本 seed 真实事件）。
- **L5**：commit#1079（本 seed 真实事件）。

### fault 181

- **L0**：fault_applied#1080（本 seed 真实事件）。
- **L1**：carrier_state#1081（本 seed 真实事件）。
- **L2**：operand_read#1082（本 seed 真实事件）。
- **L3**：execute#1083（本 seed 真实事件）。
- **L4**：prf_writeback#1084（本 seed 真实事件）。
- **L5**：commit#1085（本 seed 真实事件）。

### fault 182

- **L0**：fault_applied#1086（本 seed 真实事件）。
- **L1**：carrier_state#1087（本 seed 真实事件）。
- **L2**：operand_read#1088（本 seed 真实事件）。
- **L3**：execute#1089（本 seed 真实事件）。
- **L4**：prf_writeback#1090（本 seed 真实事件）。
- **L5**：commit#1091（本 seed 真实事件）。

### fault 183

- **L0**：fault_applied#1092（本 seed 真实事件）。
- **L1**：carrier_state#1093（本 seed 真实事件）。
- **L2**：operand_read#1094（本 seed 真实事件）。
- **L3**：execute#1095（本 seed 真实事件）。
- **L4**：prf_writeback#1096（本 seed 真实事件）。
- **L5**：commit#1097（本 seed 真实事件）。

### fault 184

- **L0**：fault_applied#1098（本 seed 真实事件）。
- **L1**：carrier_state#1099（本 seed 真实事件）。
- **L2**：operand_read#1100（本 seed 真实事件）。
- **L3**：execute#1101（本 seed 真实事件）。
- **L4**：prf_writeback#1102（本 seed 真实事件）。
- **L5**：commit#1103（本 seed 真实事件）。

### fault 185

- **L0**：fault_applied#1104（本 seed 真实事件）。
- **L1**：carrier_state#1105（本 seed 真实事件）。
- **L2**：operand_read#1106（本 seed 真实事件）。
- **L3**：execute#1107（本 seed 真实事件）。
- **L4**：prf_writeback#1108（本 seed 真实事件）。
- **L5**：commit#1109（本 seed 真实事件）。

### fault 186

- **L0**：fault_applied#1110（本 seed 真实事件）。
- **L1**：carrier_state#1111（本 seed 真实事件）。
- **L2**：operand_read#1112（本 seed 真实事件）。
- **L3**：execute#1113（本 seed 真实事件）。
- **L4**：prf_writeback#1114（本 seed 真实事件）。
- **L5**：commit#1115（本 seed 真实事件）。

### fault 187

- **L0**：fault_applied#1116（本 seed 真实事件）。
- **L1**：carrier_state#1117（本 seed 真实事件）。
- **L2**：operand_read#1118（本 seed 真实事件）。
- **L3**：execute#1119（本 seed 真实事件）。
- **L4**：prf_writeback#1120（本 seed 真实事件）。
- **L5**：commit#1121（本 seed 真实事件）。

### fault 188

- **L0**：fault_applied#1122（本 seed 真实事件）。
- **L1**：carrier_state#1123（本 seed 真实事件）。
- **L2**：operand_read#1124（本 seed 真实事件）。
- **L3**：execute#1125（本 seed 真实事件）。
- **L4**：prf_writeback#1126（本 seed 真实事件）。
- **L5**：commit#1127（本 seed 真实事件）。

### fault 189

- **L0**：fault_applied#1128（本 seed 真实事件）。
- **L1**：carrier_state#1129（本 seed 真实事件）。
- **L2**：operand_read#1130（本 seed 真实事件）。
- **L3**：execute#1131（本 seed 真实事件）。
- **L4**：prf_writeback#1132（本 seed 真实事件）。
- **L5**：commit#1133（本 seed 真实事件）。

### fault 19

- **L0**：fault_applied#108（本 seed 真实事件）。
- **L1**：carrier_state#109（本 seed 真实事件）。
- **L2**：operand_read#110（本 seed 真实事件）。
- **L3**：execute#111（本 seed 真实事件）。
- **L4**：prf_writeback#112（本 seed 真实事件）。
- **L5**：commit#113（本 seed 真实事件）。

### fault 190

- **L0**：fault_applied#1134（本 seed 真实事件）。
- **L1**：carrier_state#1135（本 seed 真实事件）。
- **L2**：operand_read#1136（本 seed 真实事件）。
- **L3**：execute#1137（本 seed 真实事件）。
- **L4**：prf_writeback#1138（本 seed 真实事件）。
- **L5**：commit#1139（本 seed 真实事件）。

### fault 191

- **L0**：fault_applied#1140（本 seed 真实事件）。
- **L1**：carrier_state#1141（本 seed 真实事件）。
- **L2**：operand_read#1142（本 seed 真实事件）。
- **L3**：execute#1143（本 seed 真实事件）。
- **L4**：prf_writeback#1144（本 seed 真实事件）。
- **L5**：commit#1145（本 seed 真实事件）。

### fault 192

- **L0**：fault_applied#1146（本 seed 真实事件）。
- **L1**：carrier_state#1147（本 seed 真实事件）。
- **L2**：operand_read#1148（本 seed 真实事件）。
- **L3**：execute#1149（本 seed 真实事件）。
- **L4**：prf_writeback#1150（本 seed 真实事件）。
- **L5**：commit#1151（本 seed 真实事件）。

### fault 193

- **L0**：fault_applied#1152（本 seed 真实事件）。
- **L1**：carrier_state#1153（本 seed 真实事件）。
- **L2**：operand_read#1154（本 seed 真实事件）。
- **L3**：execute#1155（本 seed 真实事件）。
- **L4**：prf_writeback#1156（本 seed 真实事件）。
- **L5**：commit#1157（本 seed 真实事件）。

### fault 194

- **L0**：fault_applied#1158（本 seed 真实事件）。
- **L1**：carrier_state#1159（本 seed 真实事件）。
- **L2**：operand_read#1160（本 seed 真实事件）。
- **L3**：execute#1161（本 seed 真实事件）。
- **L4**：prf_writeback#1162（本 seed 真实事件）。
- **L5**：commit#1163（本 seed 真实事件）。

### fault 195

- **L0**：fault_applied#1164（本 seed 真实事件）。
- **L1**：carrier_state#1165（本 seed 真实事件）。
- **L2**：operand_read#1166（本 seed 真实事件）。
- **L3**：execute#1167（本 seed 真实事件）。
- **L4**：prf_writeback#1168（本 seed 真实事件）。
- **L5**：commit#1169（本 seed 真实事件）。

### fault 196

- **L0**：fault_applied#1170（本 seed 真实事件）。
- **L1**：carrier_state#1171（本 seed 真实事件）。
- **L2**：operand_read#1172（本 seed 真实事件）。
- **L3**：execute#1173（本 seed 真实事件）。
- **L4**：prf_writeback#1174（本 seed 真实事件）。
- **L5**：commit#1175（本 seed 真实事件）。

### fault 197

- **L0**：fault_applied#1176（本 seed 真实事件）。
- **L1**：carrier_state#1177（本 seed 真实事件）。
- **L2**：operand_read#1178（本 seed 真实事件）。
- **L3**：execute#1179（本 seed 真实事件）。
- **L4**：prf_writeback#1180（本 seed 真实事件）。
- **L5**：commit#1181（本 seed 真实事件）。

### fault 198

- **L0**：fault_applied#1182（本 seed 真实事件）。
- **L1**：carrier_state#1183（本 seed 真实事件）。
- **L2**：operand_read#1184（本 seed 真实事件）。
- **L3**：execute#1185（本 seed 真实事件）。
- **L4**：prf_writeback#1186（本 seed 真实事件）。
- **L5**：commit#1187（本 seed 真实事件）。

### fault 199

- **L0**：fault_applied#1188（本 seed 真实事件）。
- **L1**：carrier_state#1189（本 seed 真实事件）。
- **L2**：operand_read#1190（本 seed 真实事件）。
- **L3**：execute#1191（本 seed 真实事件）。
- **L4**：prf_writeback#1192（本 seed 真实事件）。
- **L5**：commit#1193（本 seed 真实事件）。

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

### fault 200

- **L0**：fault_applied#1194（本 seed 真实事件）。
- **L1**：carrier_state#1195（本 seed 真实事件）。
- **L2**：operand_read#1196（本 seed 真实事件）。
- **L3**：execute#1197（本 seed 真实事件）。
- **L4**：prf_writeback#1198（本 seed 真实事件）。
- **L5**：commit#1199（本 seed 真实事件）。

### fault 201

- **L0**：fault_applied#1200（本 seed 真实事件）。
- **L1**：carrier_state#1201（本 seed 真实事件）。
- **L2**：operand_read#1202（本 seed 真实事件）。
- **L3**：execute#1203（本 seed 真实事件）。
- **L4**：prf_writeback#1204（本 seed 真实事件）。
- **L5**：commit#1205（本 seed 真实事件）。

### fault 202

- **L0**：fault_applied#1206（本 seed 真实事件）。
- **L1**：carrier_state#1207（本 seed 真实事件）。
- **L2**：operand_read#1208（本 seed 真实事件）。
- **L3**：execute#1209（本 seed 真实事件）。
- **L4**：prf_writeback#1210（本 seed 真实事件）。
- **L5**：commit#1211（本 seed 真实事件）。

### fault 203

- **L0**：fault_applied#1212（本 seed 真实事件）。
- **L1**：carrier_state#1213（本 seed 真实事件）。
- **L2**：operand_read#1214（本 seed 真实事件）。
- **L3**：execute#1215（本 seed 真实事件）。
- **L4**：prf_writeback#1216（本 seed 真实事件）。
- **L5**：commit#1217（本 seed 真实事件）。

### fault 204

- **L0**：fault_applied#1218（本 seed 真实事件）。
- **L1**：carrier_state#1219（本 seed 真实事件）。
- **L2**：operand_read#1220（本 seed 真实事件）。
- **L3**：execute#1221（本 seed 真实事件）。
- **L4**：prf_writeback#1222（本 seed 真实事件）。
- **L5**：commit#1223（本 seed 真实事件）。

### fault 205

- **L0**：fault_applied#1224（本 seed 真实事件）。
- **L1**：carrier_state#1225（本 seed 真实事件）。
- **L2**：operand_read#1226（本 seed 真实事件）。
- **L3**：execute#1227（本 seed 真实事件）。
- **L4**：prf_writeback#1228（本 seed 真实事件）。
- **L5**：commit#1229（本 seed 真实事件）。

### fault 206

- **L0**：fault_applied#1230（本 seed 真实事件）。
- **L1**：carrier_state#1231（本 seed 真实事件）。
- **L2**：operand_read#1232（本 seed 真实事件）。
- **L3**：execute#1233（本 seed 真实事件）。
- **L4**：prf_writeback#1234（本 seed 真实事件）。
- **L5**：commit#1235（本 seed 真实事件）。

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

### fault 23

- **L0**：fault_applied#132（本 seed 真实事件）。
- **L1**：carrier_state#133（本 seed 真实事件）。
- **L2**：operand_read#134（本 seed 真实事件）。
- **L3**：execute#135（本 seed 真实事件）。
- **L4**：prf_writeback#136（本 seed 真实事件）。
- **L5**：commit#137（本 seed 真实事件）。

### fault 24

- **L0**：fault_applied#138（本 seed 真实事件）。
- **L1**：carrier_state#139（本 seed 真实事件）。
- **L2**：operand_read#140（本 seed 真实事件）。
- **L3**：execute#141（本 seed 真实事件）。
- **L4**：prf_writeback#142（本 seed 真实事件）。
- **L5**：commit#143（本 seed 真实事件）。

### fault 25

- **L0**：fault_applied#144（本 seed 真实事件）。
- **L1**：carrier_state#145（本 seed 真实事件）。
- **L2**：operand_read#146（本 seed 真实事件）。
- **L3**：execute#147（本 seed 真实事件）。
- **L4**：prf_writeback#148（本 seed 真实事件）。
- **L5**：commit#149（本 seed 真实事件）。

### fault 26

- **L0**：fault_applied#150（本 seed 真实事件）。
- **L1**：carrier_state#151（本 seed 真实事件）。
- **L2**：operand_read#152（本 seed 真实事件）。
- **L3**：execute#153（本 seed 真实事件）。
- **L4**：prf_writeback#154（本 seed 真实事件）。
- **L5**：commit#155（本 seed 真实事件）。

### fault 27

- **L0**：fault_applied#156（本 seed 真实事件）。
- **L1**：carrier_state#157（本 seed 真实事件）。
- **L2**：operand_read#158（本 seed 真实事件）。
- **L3**：execute#159（本 seed 真实事件）。
- **L4**：prf_writeback#160（本 seed 真实事件）。
- **L5**：commit#161（本 seed 真实事件）。

### fault 28

- **L0**：fault_applied#162（本 seed 真实事件）。
- **L1**：carrier_state#163（本 seed 真实事件）。
- **L2**：operand_read#164（本 seed 真实事件）。
- **L3**：execute#165（本 seed 真实事件）。
- **L4**：prf_writeback#166（本 seed 真实事件）。
- **L5**：commit#167（本 seed 真实事件）。

### fault 29

- **L0**：fault_applied#168（本 seed 真实事件）。
- **L1**：carrier_state#169（本 seed 真实事件）。
- **L2**：operand_read#170（本 seed 真实事件）。
- **L3**：execute#171（本 seed 真实事件）。
- **L4**：prf_writeback#172（本 seed 真实事件）。
- **L5**：commit#173（本 seed 真实事件）。

### fault 3

- **L0**：fault_applied#12（本 seed 真实事件）。
- **L1**：carrier_state#13（本 seed 真实事件）。
- **L2**：operand_read#14（本 seed 真实事件）。
- **L3**：execute#15（本 seed 真实事件）。
- **L4**：prf_writeback#16（本 seed 真实事件）。
- **L5**：commit#17（本 seed 真实事件）。

### fault 30

- **L0**：fault_applied#174（本 seed 真实事件）。
- **L1**：carrier_state#175（本 seed 真实事件）。
- **L2**：operand_read#176（本 seed 真实事件）。
- **L3**：execute#177（本 seed 真实事件）。
- **L4**：prf_writeback#178（本 seed 真实事件）。
- **L5**：commit#179（本 seed 真实事件）。

### fault 31

- **L0**：fault_applied#180（本 seed 真实事件）。
- **L1**：carrier_state#181（本 seed 真实事件）。
- **L2**：operand_read#182（本 seed 真实事件）。
- **L3**：execute#183（本 seed 真实事件）。
- **L4**：prf_writeback#184（本 seed 真实事件）。
- **L5**：commit#185（本 seed 真实事件）。

### fault 32

- **L0**：fault_applied#186（本 seed 真实事件）。
- **L1**：carrier_state#187（本 seed 真实事件）。
- **L2**：operand_read#188（本 seed 真实事件）。
- **L3**：execute#189（本 seed 真实事件）。
- **L4**：prf_writeback#190（本 seed 真实事件）。
- **L5**：commit#191（本 seed 真实事件）。

### fault 33

- **L0**：fault_applied#192（本 seed 真实事件）。
- **L1**：carrier_state#193（本 seed 真实事件）。
- **L2**：operand_read#194（本 seed 真实事件）。
- **L3**：execute#195（本 seed 真实事件）。
- **L4**：prf_writeback#196（本 seed 真实事件）。
- **L5**：commit#197（本 seed 真实事件）。

### fault 34

- **L0**：fault_applied#198（本 seed 真实事件）。
- **L1**：carrier_state#199（本 seed 真实事件）。
- **L2**：operand_read#200（本 seed 真实事件）。
- **L3**：execute#201（本 seed 真实事件）。
- **L4**：prf_writeback#202（本 seed 真实事件）。
- **L5**：commit#203（本 seed 真实事件）。

### fault 35

- **L0**：fault_applied#204（本 seed 真实事件）。
- **L1**：carrier_state#205（本 seed 真实事件）。
- **L2**：operand_read#206（本 seed 真实事件）。
- **L3**：execute#207（本 seed 真实事件）。
- **L4**：prf_writeback#208（本 seed 真实事件）。
- **L5**：commit#209（本 seed 真实事件）。

### fault 36

- **L0**：fault_applied#210（本 seed 真实事件）。
- **L1**：carrier_state#211（本 seed 真实事件）。
- **L2**：operand_read#212（本 seed 真实事件）。
- **L3**：execute#213（本 seed 真实事件）。
- **L4**：prf_writeback#214（本 seed 真实事件）。
- **L5**：commit#215（本 seed 真实事件）。

### fault 37

- **L0**：fault_applied#216（本 seed 真实事件）。
- **L1**：carrier_state#217（本 seed 真实事件）。
- **L2**：operand_read#218（本 seed 真实事件）。
- **L3**：execute#219（本 seed 真实事件）。
- **L4**：prf_writeback#220（本 seed 真实事件）。
- **L5**：commit#221（本 seed 真实事件）。

### fault 38

- **L0**：fault_applied#222（本 seed 真实事件）。
- **L1**：carrier_state#223（本 seed 真实事件）。
- **L2**：operand_read#224（本 seed 真实事件）。
- **L3**：execute#225（本 seed 真实事件）。
- **L4**：prf_writeback#226（本 seed 真实事件）。
- **L5**：commit#227（本 seed 真实事件）。

### fault 39

- **L0**：fault_applied#228（本 seed 真实事件）。
- **L1**：carrier_state#229（本 seed 真实事件）。
- **L2**：operand_read#230（本 seed 真实事件）。
- **L3**：execute#231（本 seed 真实事件）。
- **L4**：prf_writeback#232（本 seed 真实事件）。
- **L5**：commit#233（本 seed 真实事件）。

### fault 4

- **L0**：fault_applied#18（本 seed 真实事件）。
- **L1**：carrier_state#19（本 seed 真实事件）。
- **L2**：operand_read#20（本 seed 真实事件）。
- **L3**：execute#21（本 seed 真实事件）。
- **L4**：prf_writeback#22（本 seed 真实事件）。
- **L5**：commit#23（本 seed 真实事件）。

### fault 40

- **L0**：fault_applied#234（本 seed 真实事件）。
- **L1**：carrier_state#235（本 seed 真实事件）。
- **L2**：operand_read#236（本 seed 真实事件）。
- **L3**：execute#237（本 seed 真实事件）。
- **L4**：prf_writeback#238（本 seed 真实事件）。
- **L5**：commit#239（本 seed 真实事件）。

### fault 41

- **L0**：fault_applied#240（本 seed 真实事件）。
- **L1**：carrier_state#241（本 seed 真实事件）。
- **L2**：operand_read#242（本 seed 真实事件）。
- **L3**：execute#243（本 seed 真实事件）。
- **L4**：prf_writeback#244（本 seed 真实事件）。
- **L5**：commit#245（本 seed 真实事件）。

### fault 42

- **L0**：fault_applied#246（本 seed 真实事件）。
- **L1**：carrier_state#247（本 seed 真实事件）。
- **L2**：operand_read#248（本 seed 真实事件）。
- **L3**：execute#249（本 seed 真实事件）。
- **L4**：prf_writeback#250（本 seed 真实事件）。
- **L5**：commit#251（本 seed 真实事件）。

### fault 43

- **L0**：fault_applied#252（本 seed 真实事件）。
- **L1**：carrier_state#253（本 seed 真实事件）。
- **L2**：operand_read#254（本 seed 真实事件）。
- **L3**：execute#255（本 seed 真实事件）。
- **L4**：prf_writeback#256（本 seed 真实事件）。
- **L5**：commit#257（本 seed 真实事件）。

### fault 44

- **L0**：fault_applied#258（本 seed 真实事件）。
- **L1**：carrier_state#259（本 seed 真实事件）。
- **L2**：operand_read#260（本 seed 真实事件）。
- **L3**：execute#261（本 seed 真实事件）。
- **L4**：prf_writeback#262（本 seed 真实事件）。
- **L5**：commit#263（本 seed 真实事件）。

### fault 45

- **L0**：fault_applied#264（本 seed 真实事件）。
- **L1**：carrier_state#265（本 seed 真实事件）。
- **L2**：operand_read#266（本 seed 真实事件）。
- **L3**：execute#267（本 seed 真实事件）。
- **L4**：prf_writeback#268（本 seed 真实事件）。
- **L5**：commit#269（本 seed 真实事件）。

### fault 46

- **L0**：fault_applied#270（本 seed 真实事件）。
- **L1**：carrier_state#271（本 seed 真实事件）。
- **L2**：operand_read#272（本 seed 真实事件）。
- **L3**：execute#273（本 seed 真实事件）。
- **L4**：prf_writeback#274（本 seed 真实事件）。
- **L5**：commit#275（本 seed 真实事件）。

### fault 47

- **L0**：fault_applied#276（本 seed 真实事件）。
- **L1**：carrier_state#277（本 seed 真实事件）。
- **L2**：operand_read#278（本 seed 真实事件）。
- **L3**：execute#279（本 seed 真实事件）。
- **L4**：prf_writeback#280（本 seed 真实事件）。
- **L5**：commit#281（本 seed 真实事件）。

### fault 48

- **L0**：fault_applied#282（本 seed 真实事件）。
- **L1**：carrier_state#283（本 seed 真实事件）。
- **L2**：operand_read#284（本 seed 真实事件）。
- **L3**：execute#285（本 seed 真实事件）。
- **L4**：prf_writeback#286（本 seed 真实事件）。
- **L5**：commit#287（本 seed 真实事件）。

### fault 49

- **L0**：fault_applied#288（本 seed 真实事件）。
- **L1**：carrier_state#289（本 seed 真实事件）。
- **L2**：operand_read#290（本 seed 真实事件）。
- **L3**：execute#291（本 seed 真实事件）。
- **L4**：prf_writeback#292（本 seed 真实事件）。
- **L5**：commit#293（本 seed 真实事件）。

### fault 5

- **L0**：fault_applied#24（本 seed 真实事件）。
- **L1**：carrier_state#25（本 seed 真实事件）。
- **L2**：operand_read#26（本 seed 真实事件）。
- **L3**：execute#27（本 seed 真实事件）。
- **L4**：prf_writeback#28（本 seed 真实事件）。
- **L5**：commit#29（本 seed 真实事件）。

### fault 50

- **L0**：fault_applied#294（本 seed 真实事件）。
- **L1**：carrier_state#295（本 seed 真实事件）。
- **L2**：operand_read#296（本 seed 真实事件）。
- **L3**：execute#297（本 seed 真实事件）。
- **L4**：prf_writeback#298（本 seed 真实事件）。
- **L5**：commit#299（本 seed 真实事件）。

### fault 51

- **L0**：fault_applied#300（本 seed 真实事件）。
- **L1**：carrier_state#301（本 seed 真实事件）。
- **L2**：operand_read#302（本 seed 真实事件）。
- **L3**：execute#303（本 seed 真实事件）。
- **L4**：prf_writeback#304（本 seed 真实事件）。
- **L5**：commit#305（本 seed 真实事件）。

### fault 52

- **L0**：fault_applied#306（本 seed 真实事件）。
- **L1**：carrier_state#307（本 seed 真实事件）。
- **L2**：operand_read#308（本 seed 真实事件）。
- **L3**：execute#309（本 seed 真实事件）。
- **L4**：prf_writeback#310（本 seed 真实事件）。
- **L5**：commit#311（本 seed 真实事件）。

### fault 53

- **L0**：fault_applied#312（本 seed 真实事件）。
- **L1**：carrier_state#313（本 seed 真实事件）。
- **L2**：operand_read#314（本 seed 真实事件）。
- **L3**：execute#315（本 seed 真实事件）。
- **L4**：prf_writeback#316（本 seed 真实事件）。
- **L5**：commit#317（本 seed 真实事件）。

### fault 54

- **L0**：fault_applied#318（本 seed 真实事件）。
- **L1**：carrier_state#319（本 seed 真实事件）。
- **L2**：operand_read#320（本 seed 真实事件）。
- **L3**：execute#321（本 seed 真实事件）。
- **L4**：prf_writeback#322（本 seed 真实事件）。
- **L5**：commit#323（本 seed 真实事件）。

### fault 55

- **L0**：fault_applied#324（本 seed 真实事件）。
- **L1**：carrier_state#325（本 seed 真实事件）。
- **L2**：operand_read#326（本 seed 真实事件）。
- **L3**：execute#327（本 seed 真实事件）。
- **L4**：prf_writeback#328（本 seed 真实事件）。
- **L5**：commit#329（本 seed 真实事件）。

### fault 56

- **L0**：fault_applied#330（本 seed 真实事件）。
- **L1**：carrier_state#331（本 seed 真实事件）。
- **L2**：operand_read#332（本 seed 真实事件）。
- **L3**：execute#333（本 seed 真实事件）。
- **L4**：prf_writeback#334（本 seed 真实事件）。
- **L5**：commit#335（本 seed 真实事件）。

### fault 57

- **L0**：fault_applied#336（本 seed 真实事件）。
- **L1**：carrier_state#337（本 seed 真实事件）。
- **L2**：operand_read#338（本 seed 真实事件）。
- **L3**：execute#339（本 seed 真实事件）。
- **L4**：prf_writeback#340（本 seed 真实事件）。
- **L5**：commit#341（本 seed 真实事件）。

### fault 58

- **L0**：fault_applied#342（本 seed 真实事件）。
- **L1**：carrier_state#343（本 seed 真实事件）。
- **L2**：operand_read#344（本 seed 真实事件）。
- **L3**：execute#345（本 seed 真实事件）。
- **L4**：prf_writeback#346（本 seed 真实事件）。
- **L5**：commit#347（本 seed 真实事件）。

### fault 59

- **L0**：fault_applied#348（本 seed 真实事件）。
- **L1**：carrier_state#349（本 seed 真实事件）。
- **L2**：operand_read#350（本 seed 真实事件）。
- **L3**：execute#351（本 seed 真实事件）。
- **L4**：prf_writeback#352（本 seed 真实事件）。
- **L5**：commit#353（本 seed 真实事件）。

### fault 6

- **L0**：fault_applied#30（本 seed 真实事件）。
- **L1**：carrier_state#31（本 seed 真实事件）。
- **L2**：operand_read#32（本 seed 真实事件）。
- **L3**：execute#33（本 seed 真实事件）。
- **L4**：prf_writeback#34（本 seed 真实事件）。
- **L5**：commit#35（本 seed 真实事件）。

### fault 60

- **L0**：fault_applied#354（本 seed 真实事件）。
- **L1**：carrier_state#355（本 seed 真实事件）。
- **L2**：operand_read#356（本 seed 真实事件）。
- **L3**：execute#357（本 seed 真实事件）。
- **L4**：prf_writeback#358（本 seed 真实事件）。
- **L5**：commit#359（本 seed 真实事件）。

### fault 61

- **L0**：fault_applied#360（本 seed 真实事件）。
- **L1**：carrier_state#361（本 seed 真实事件）。
- **L2**：operand_read#362（本 seed 真实事件）。
- **L3**：execute#363（本 seed 真实事件）。
- **L4**：prf_writeback#364（本 seed 真实事件）。
- **L5**：commit#365（本 seed 真实事件）。

### fault 62

- **L0**：fault_applied#366（本 seed 真实事件）。
- **L1**：carrier_state#367（本 seed 真实事件）。
- **L2**：operand_read#368（本 seed 真实事件）。
- **L3**：execute#369（本 seed 真实事件）。
- **L4**：prf_writeback#370（本 seed 真实事件）。
- **L5**：commit#371（本 seed 真实事件）。

### fault 63

- **L0**：fault_applied#372（本 seed 真实事件）。
- **L1**：carrier_state#373（本 seed 真实事件）。
- **L2**：operand_read#374（本 seed 真实事件）。
- **L3**：execute#375（本 seed 真实事件）。
- **L4**：prf_writeback#376（本 seed 真实事件）。
- **L5**：commit#377（本 seed 真实事件）。

### fault 64

- **L0**：fault_applied#378（本 seed 真实事件）。
- **L1**：carrier_state#379（本 seed 真实事件）。
- **L2**：operand_read#380（本 seed 真实事件）。
- **L3**：execute#381（本 seed 真实事件）。
- **L4**：prf_writeback#382（本 seed 真实事件）。
- **L5**：commit#383（本 seed 真实事件）。

### fault 65

- **L0**：fault_applied#384（本 seed 真实事件）。
- **L1**：carrier_state#385（本 seed 真实事件）。
- **L2**：operand_read#386（本 seed 真实事件）。
- **L3**：execute#387（本 seed 真实事件）。
- **L4**：prf_writeback#388（本 seed 真实事件）。
- **L5**：commit#389（本 seed 真实事件）。

### fault 66

- **L0**：fault_applied#390（本 seed 真实事件）。
- **L1**：carrier_state#391（本 seed 真实事件）。
- **L2**：operand_read#392（本 seed 真实事件）。
- **L3**：execute#393（本 seed 真实事件）。
- **L4**：prf_writeback#394（本 seed 真实事件）。
- **L5**：commit#395（本 seed 真实事件）。

### fault 67

- **L0**：fault_applied#396（本 seed 真实事件）。
- **L1**：carrier_state#397（本 seed 真实事件）。
- **L2**：operand_read#398（本 seed 真实事件）。
- **L3**：execute#399（本 seed 真实事件）。
- **L4**：prf_writeback#400（本 seed 真实事件）。
- **L5**：commit#401（本 seed 真实事件）。

### fault 68

- **L0**：fault_applied#402（本 seed 真实事件）。
- **L1**：carrier_state#403（本 seed 真实事件）。
- **L2**：operand_read#404（本 seed 真实事件）。
- **L3**：execute#405（本 seed 真实事件）。
- **L4**：prf_writeback#406（本 seed 真实事件）。
- **L5**：commit#407（本 seed 真实事件）。

### fault 69

- **L0**：fault_applied#408（本 seed 真实事件）。
- **L1**：carrier_state#409（本 seed 真实事件）。
- **L2**：operand_read#410（本 seed 真实事件）。
- **L3**：execute#411（本 seed 真实事件）。
- **L4**：prf_writeback#412（本 seed 真实事件）。
- **L5**：commit#413（本 seed 真实事件）。

### fault 7

- **L0**：fault_applied#36（本 seed 真实事件）。
- **L1**：carrier_state#37（本 seed 真实事件）。
- **L2**：operand_read#38（本 seed 真实事件）。
- **L3**：execute#39（本 seed 真实事件）。
- **L4**：prf_writeback#40（本 seed 真实事件）。
- **L5**：commit#41（本 seed 真实事件）。

### fault 70

- **L0**：fault_applied#414（本 seed 真实事件）。
- **L1**：carrier_state#415（本 seed 真实事件）。
- **L2**：operand_read#416（本 seed 真实事件）。
- **L3**：execute#417（本 seed 真实事件）。
- **L4**：prf_writeback#418（本 seed 真实事件）。
- **L5**：commit#419（本 seed 真实事件）。

### fault 71

- **L0**：fault_applied#420（本 seed 真实事件）。
- **L1**：carrier_state#421（本 seed 真实事件）。
- **L2**：operand_read#422（本 seed 真实事件）。
- **L3**：execute#423（本 seed 真实事件）。
- **L4**：prf_writeback#424（本 seed 真实事件）。
- **L5**：commit#425（本 seed 真实事件）。

### fault 72

- **L0**：fault_applied#426（本 seed 真实事件）。
- **L1**：carrier_state#427（本 seed 真实事件）。
- **L2**：operand_read#428（本 seed 真实事件）。
- **L3**：execute#429（本 seed 真实事件）。
- **L4**：prf_writeback#430（本 seed 真实事件）。
- **L5**：commit#431（本 seed 真实事件）。

### fault 73

- **L0**：fault_applied#432（本 seed 真实事件）。
- **L1**：carrier_state#433（本 seed 真实事件）。
- **L2**：operand_read#434（本 seed 真实事件）。
- **L3**：execute#435（本 seed 真实事件）。
- **L4**：prf_writeback#436（本 seed 真实事件）。
- **L5**：commit#437（本 seed 真实事件）。

### fault 74

- **L0**：fault_applied#438（本 seed 真实事件）。
- **L1**：carrier_state#439（本 seed 真实事件）。
- **L2**：operand_read#440（本 seed 真实事件）。
- **L3**：execute#441（本 seed 真实事件）。
- **L4**：prf_writeback#442（本 seed 真实事件）。
- **L5**：commit#443（本 seed 真实事件）。

### fault 75

- **L0**：fault_applied#444（本 seed 真实事件）。
- **L1**：carrier_state#445（本 seed 真实事件）。
- **L2**：operand_read#446（本 seed 真实事件）。
- **L3**：execute#447（本 seed 真实事件）。
- **L4**：prf_writeback#448（本 seed 真实事件）。
- **L5**：commit#449（本 seed 真实事件）。

### fault 76

- **L0**：fault_applied#450（本 seed 真实事件）。
- **L1**：carrier_state#451（本 seed 真实事件）。
- **L2**：operand_read#452（本 seed 真实事件）。
- **L3**：execute#453（本 seed 真实事件）。
- **L4**：prf_writeback#454（本 seed 真实事件）。
- **L5**：commit#455（本 seed 真实事件）。

### fault 77

- **L0**：fault_applied#456（本 seed 真实事件）。
- **L1**：carrier_state#457（本 seed 真实事件）。
- **L2**：operand_read#458（本 seed 真实事件）。
- **L3**：execute#459（本 seed 真实事件）。
- **L4**：prf_writeback#460（本 seed 真实事件）。
- **L5**：commit#461（本 seed 真实事件）。

### fault 78

- **L0**：fault_applied#462（本 seed 真实事件）。
- **L1**：carrier_state#463（本 seed 真实事件）。
- **L2**：operand_read#464（本 seed 真实事件）。
- **L3**：execute#465（本 seed 真实事件）。
- **L4**：prf_writeback#466（本 seed 真实事件）。
- **L5**：commit#467（本 seed 真实事件）。

### fault 79

- **L0**：fault_applied#468（本 seed 真实事件）。
- **L1**：carrier_state#469（本 seed 真实事件）。
- **L2**：operand_read#470（本 seed 真实事件）。
- **L3**：execute#471（本 seed 真实事件）。
- **L4**：prf_writeback#472（本 seed 真实事件）。
- **L5**：commit#473（本 seed 真实事件）。

### fault 8

- **L0**：fault_applied#42（本 seed 真实事件）。
- **L1**：carrier_state#43（本 seed 真实事件）。
- **L2**：operand_read#44（本 seed 真实事件）。
- **L3**：execute#45（本 seed 真实事件）。
- **L4**：prf_writeback#46（本 seed 真实事件）。
- **L5**：commit#47（本 seed 真实事件）。

### fault 80

- **L0**：fault_applied#474（本 seed 真实事件）。
- **L1**：carrier_state#475（本 seed 真实事件）。
- **L2**：operand_read#476（本 seed 真实事件）。
- **L3**：execute#477（本 seed 真实事件）。
- **L4**：prf_writeback#478（本 seed 真实事件）。
- **L5**：commit#479（本 seed 真实事件）。

### fault 81

- **L0**：fault_applied#480（本 seed 真实事件）。
- **L1**：carrier_state#481（本 seed 真实事件）。
- **L2**：operand_read#482（本 seed 真实事件）。
- **L3**：execute#483（本 seed 真实事件）。
- **L4**：prf_writeback#484（本 seed 真实事件）。
- **L5**：commit#485（本 seed 真实事件）。

### fault 82

- **L0**：fault_applied#486（本 seed 真实事件）。
- **L1**：carrier_state#487（本 seed 真实事件）。
- **L2**：operand_read#488（本 seed 真实事件）。
- **L3**：execute#489（本 seed 真实事件）。
- **L4**：prf_writeback#490（本 seed 真实事件）。
- **L5**：commit#491（本 seed 真实事件）。

### fault 83

- **L0**：fault_applied#492（本 seed 真实事件）。
- **L1**：carrier_state#493（本 seed 真实事件）。
- **L2**：operand_read#494（本 seed 真实事件）。
- **L3**：execute#495（本 seed 真实事件）。
- **L4**：prf_writeback#496（本 seed 真实事件）。
- **L5**：commit#497（本 seed 真实事件）。

### fault 84

- **L0**：fault_applied#498（本 seed 真实事件）。
- **L1**：carrier_state#499（本 seed 真实事件）。
- **L2**：operand_read#500（本 seed 真实事件）。
- **L3**：execute#501（本 seed 真实事件）。
- **L4**：prf_writeback#502（本 seed 真实事件）。
- **L5**：commit#503（本 seed 真实事件）。

### fault 85

- **L0**：fault_applied#504（本 seed 真实事件）。
- **L1**：carrier_state#505（本 seed 真实事件）。
- **L2**：operand_read#506（本 seed 真实事件）。
- **L3**：execute#507（本 seed 真实事件）。
- **L4**：prf_writeback#508（本 seed 真实事件）。
- **L5**：commit#509（本 seed 真实事件）。

### fault 86

- **L0**：fault_applied#510（本 seed 真实事件）。
- **L1**：carrier_state#511（本 seed 真实事件）。
- **L2**：operand_read#512（本 seed 真实事件）。
- **L3**：execute#513（本 seed 真实事件）。
- **L4**：prf_writeback#514（本 seed 真实事件）。
- **L5**：commit#515（本 seed 真实事件）。

### fault 87

- **L0**：fault_applied#516（本 seed 真实事件）。
- **L1**：carrier_state#517（本 seed 真实事件）。
- **L2**：operand_read#518（本 seed 真实事件）。
- **L3**：execute#519（本 seed 真实事件）。
- **L4**：prf_writeback#520（本 seed 真实事件）。
- **L5**：commit#521（本 seed 真实事件）。

### fault 88

- **L0**：fault_applied#522（本 seed 真实事件）。
- **L1**：carrier_state#523（本 seed 真实事件）。
- **L2**：operand_read#524（本 seed 真实事件）。
- **L3**：execute#525（本 seed 真实事件）。
- **L4**：prf_writeback#526（本 seed 真实事件）。
- **L5**：commit#527（本 seed 真实事件）。

### fault 89

- **L0**：fault_applied#528（本 seed 真实事件）。
- **L1**：carrier_state#529（本 seed 真实事件）。
- **L2**：operand_read#530（本 seed 真实事件）。
- **L3**：execute#531（本 seed 真实事件）。
- **L4**：prf_writeback#532（本 seed 真实事件）。
- **L5**：commit#533（本 seed 真实事件）。

### fault 9

- **L0**：fault_applied#48（本 seed 真实事件）。
- **L1**：carrier_state#49（本 seed 真实事件）。
- **L2**：operand_read#50（本 seed 真实事件）。
- **L3**：execute#51（本 seed 真实事件）。
- **L4**：prf_writeback#52（本 seed 真实事件）。
- **L5**：commit#53（本 seed 真实事件）。

### fault 90

- **L0**：fault_applied#534（本 seed 真实事件）。
- **L1**：carrier_state#535（本 seed 真实事件）。
- **L2**：operand_read#536（本 seed 真实事件）。
- **L3**：execute#537（本 seed 真实事件）。
- **L4**：prf_writeback#538（本 seed 真实事件）。
- **L5**：commit#539（本 seed 真实事件）。

### fault 91

- **L0**：fault_applied#540（本 seed 真实事件）。
- **L1**：carrier_state#541（本 seed 真实事件）。
- **L2**：operand_read#542（本 seed 真实事件）。
- **L3**：execute#543（本 seed 真实事件）。
- **L4**：prf_writeback#544（本 seed 真实事件）。
- **L5**：commit#545（本 seed 真实事件）。

### fault 92

- **L0**：fault_applied#546（本 seed 真实事件）。
- **L1**：carrier_state#547（本 seed 真实事件）。
- **L2**：operand_read#548（本 seed 真实事件）。
- **L3**：execute#549（本 seed 真实事件）。
- **L4**：prf_writeback#550（本 seed 真实事件）。
- **L5**：commit#551（本 seed 真实事件）。

### fault 93

- **L0**：fault_applied#552（本 seed 真实事件）。
- **L1**：carrier_state#553（本 seed 真实事件）。
- **L2**：operand_read#554（本 seed 真实事件）。
- **L3**：execute#555（本 seed 真实事件）。
- **L4**：prf_writeback#556（本 seed 真实事件）。
- **L5**：commit#557（本 seed 真实事件）。

### fault 94

- **L0**：fault_applied#558（本 seed 真实事件）。
- **L1**：carrier_state#559（本 seed 真实事件）。
- **L2**：operand_read#560（本 seed 真实事件）。
- **L3**：execute#561（本 seed 真实事件）。
- **L4**：prf_writeback#562（本 seed 真实事件）。
- **L5**：commit#563（本 seed 真实事件）。

### fault 95

- **L0**：fault_applied#564（本 seed 真实事件）。
- **L1**：carrier_state#565（本 seed 真实事件）。
- **L2**：operand_read#566（本 seed 真实事件）。
- **L3**：execute#567（本 seed 真实事件）。
- **L4**：prf_writeback#568（本 seed 真实事件）。
- **L5**：commit#569（本 seed 真实事件）。

### fault 96

- **L0**：fault_applied#570（本 seed 真实事件）。
- **L1**：carrier_state#571（本 seed 真实事件）。
- **L2**：operand_read#572（本 seed 真实事件）。
- **L3**：execute#573（本 seed 真实事件）。
- **L4**：prf_writeback#574（本 seed 真实事件）。
- **L5**：commit#575（本 seed 真实事件）。

### fault 97

- **L0**：fault_applied#576（本 seed 真实事件）。
- **L1**：carrier_state#577（本 seed 真实事件）。
- **L2**：operand_read#578（本 seed 真实事件）。
- **L3**：execute#579（本 seed 真实事件）。
- **L4**：prf_writeback#580（本 seed 真实事件）。
- **L5**：commit#581（本 seed 真实事件）。

### fault 98

- **L0**：fault_applied#582（本 seed 真实事件）。
- **L1**：carrier_state#583（本 seed 真实事件）。
- **L2**：operand_read#584（本 seed 真实事件）。
- **L3**：execute#585（本 seed 真实事件）。
- **L4**：prf_writeback#586（本 seed 真实事件）。
- **L5**：commit#587（本 seed 真实事件）。

### fault 99

- **L0**：fault_applied#588（本 seed 真实事件）。
- **L1**：carrier_state#589（本 seed 真实事件）。
- **L2**：operand_read#590（本 seed 真实事件）。
- **L3**：execute#591（本 seed 真实事件）。
- **L4**：prf_writeback#592（本 seed 真实事件）。
- **L5**：commit#593（本 seed 真实事件）。

## 7. 最终结局

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH c5080ad28ef46fe60492c150411c5db4158eaf60ded81fefcb145f90b0241ccd != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：206 / 206
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：1442
- attempted / eligible / activated：206 / 2097155 / 206

### 逐 fault 终局

| fault | terminal | deepest | admitted | certified | violations | L5 witness | containment |
|---|---|---|---|---|---|---|---|
| 1 | full | L5 | True | True | [] | 5 | N/A / N/A |
| 10 | full | L5 | True | True | [] | 59 | N/A / N/A |
| 100 | full | L5 | True | True | [] | 599 | N/A / N/A |
| 101 | full | L5 | True | True | [] | 605 | N/A / N/A |
| 102 | full | L5 | True | True | [] | 611 | N/A / N/A |
| 103 | full | L5 | True | True | [] | 617 | N/A / N/A |
| 104 | full | L5 | True | True | [] | 623 | N/A / N/A |
| 105 | full | L5 | True | True | [] | 629 | N/A / N/A |
| 106 | full | L5 | True | True | [] | 635 | N/A / N/A |
| 107 | full | L5 | True | True | [] | 641 | N/A / N/A |
| 108 | full | L5 | True | True | [] | 647 | N/A / N/A |
| 109 | full | L5 | True | True | [] | 653 | N/A / N/A |
| 11 | full | L5 | True | True | [] | 65 | N/A / N/A |
| 110 | full | L5 | True | True | [] | 659 | N/A / N/A |
| 111 | full | L5 | True | True | [] | 665 | N/A / N/A |
| 112 | full | L5 | True | True | [] | 671 | N/A / N/A |
| 113 | full | L5 | True | True | [] | 677 | N/A / N/A |
| 114 | full | L5 | True | True | [] | 683 | N/A / N/A |
| 115 | full | L5 | True | True | [] | 689 | N/A / N/A |
| 116 | full | L5 | True | True | [] | 695 | N/A / N/A |
| 117 | full | L5 | True | True | [] | 701 | N/A / N/A |
| 118 | full | L5 | True | True | [] | 707 | N/A / N/A |
| 119 | full | L5 | True | True | [] | 713 | N/A / N/A |
| 12 | full | L5 | True | True | [] | 71 | N/A / N/A |
| 120 | full | L5 | True | True | [] | 719 | N/A / N/A |
| 121 | full | L5 | True | True | [] | 725 | N/A / N/A |
| 122 | full | L5 | True | True | [] | 731 | N/A / N/A |
| 123 | full | L5 | True | True | [] | 737 | N/A / N/A |
| 124 | full | L5 | True | True | [] | 743 | N/A / N/A |
| 125 | full | L5 | True | True | [] | 749 | N/A / N/A |
| 126 | full | L5 | True | True | [] | 755 | N/A / N/A |
| 127 | full | L5 | True | True | [] | 761 | N/A / N/A |
| 128 | full | L5 | True | True | [] | 767 | N/A / N/A |
| 129 | full | L5 | True | True | [] | 773 | N/A / N/A |
| 13 | full | L5 | True | True | [] | 77 | N/A / N/A |
| 130 | full | L5 | True | True | [] | 779 | N/A / N/A |
| 131 | full | L5 | True | True | [] | 785 | N/A / N/A |
| 132 | full | L5 | True | True | [] | 791 | N/A / N/A |
| 133 | full | L5 | True | True | [] | 797 | N/A / N/A |
| 134 | full | L5 | True | True | [] | 803 | N/A / N/A |
| 135 | full | L5 | True | True | [] | 809 | N/A / N/A |
| 136 | full | L5 | True | True | [] | 815 | N/A / N/A |
| 137 | full | L5 | True | True | [] | 821 | N/A / N/A |
| 138 | full | L5 | True | True | [] | 827 | N/A / N/A |
| 139 | full | L5 | True | True | [] | 833 | N/A / N/A |
| 14 | full | L5 | True | True | [] | 83 | N/A / N/A |
| 140 | full | L5 | True | True | [] | 839 | N/A / N/A |
| 141 | full | L5 | True | True | [] | 845 | N/A / N/A |
| 142 | full | L5 | True | True | [] | 851 | N/A / N/A |
| 143 | full | L5 | True | True | [] | 857 | N/A / N/A |
| 144 | full | L5 | True | True | [] | 863 | N/A / N/A |
| 145 | full | L5 | True | True | [] | 869 | N/A / N/A |
| 146 | full | L5 | True | True | [] | 875 | N/A / N/A |
| 147 | full | L5 | True | True | [] | 881 | N/A / N/A |
| 148 | full | L5 | True | True | [] | 887 | N/A / N/A |
| 149 | full | L5 | True | True | [] | 893 | N/A / N/A |
| 15 | full | L5 | True | True | [] | 89 | N/A / N/A |
| 150 | full | L5 | True | True | [] | 899 | N/A / N/A |
| 151 | full | L5 | True | True | [] | 905 | N/A / N/A |
| 152 | full | L5 | True | True | [] | 911 | N/A / N/A |
| 153 | full | L5 | True | True | [] | 917 | N/A / N/A |
| 154 | full | L5 | True | True | [] | 923 | N/A / N/A |
| 155 | full | L5 | True | True | [] | 929 | N/A / N/A |
| 156 | full | L5 | True | True | [] | 935 | N/A / N/A |
| 157 | full | L5 | True | True | [] | 941 | N/A / N/A |
| 158 | full | L5 | True | True | [] | 947 | N/A / N/A |
| 159 | full | L5 | True | True | [] | 953 | N/A / N/A |
| 16 | full | L5 | True | True | [] | 95 | N/A / N/A |
| 160 | full | L5 | True | True | [] | 959 | N/A / N/A |
| 161 | full | L5 | True | True | [] | 965 | N/A / N/A |
| 162 | full | L5 | True | True | [] | 971 | N/A / N/A |
| 163 | full | L5 | True | True | [] | 977 | N/A / N/A |
| 164 | full | L5 | True | True | [] | 983 | N/A / N/A |
| 165 | full | L5 | True | True | [] | 989 | N/A / N/A |
| 166 | full | L5 | True | True | [] | 995 | N/A / N/A |
| 167 | full | L5 | True | True | [] | 1001 | N/A / N/A |
| 168 | full | L5 | True | True | [] | 1007 | N/A / N/A |
| 169 | full | L5 | True | True | [] | 1013 | N/A / N/A |
| 17 | full | L5 | True | True | [] | 101 | N/A / N/A |
| 170 | full | L5 | True | True | [] | 1019 | N/A / N/A |
| 171 | full | L5 | True | True | [] | 1025 | N/A / N/A |
| 172 | full | L5 | True | True | [] | 1031 | N/A / N/A |
| 173 | full | L5 | True | True | [] | 1037 | N/A / N/A |
| 174 | full | L5 | True | True | [] | 1043 | N/A / N/A |
| 175 | full | L5 | True | True | [] | 1049 | N/A / N/A |
| 176 | full | L5 | True | True | [] | 1055 | N/A / N/A |
| 177 | full | L5 | True | True | [] | 1061 | N/A / N/A |
| 178 | full | L5 | True | True | [] | 1067 | N/A / N/A |
| 179 | full | L5 | True | True | [] | 1073 | N/A / N/A |
| 18 | full | L5 | True | True | [] | 107 | N/A / N/A |
| 180 | full | L5 | True | True | [] | 1079 | N/A / N/A |
| 181 | full | L5 | True | True | [] | 1085 | N/A / N/A |
| 182 | full | L5 | True | True | [] | 1091 | N/A / N/A |
| 183 | full | L5 | True | True | [] | 1097 | N/A / N/A |
| 184 | full | L5 | True | True | [] | 1103 | N/A / N/A |
| 185 | full | L5 | True | True | [] | 1109 | N/A / N/A |
| 186 | full | L5 | True | True | [] | 1115 | N/A / N/A |
| 187 | full | L5 | True | True | [] | 1121 | N/A / N/A |
| 188 | full | L5 | True | True | [] | 1127 | N/A / N/A |
| 189 | full | L5 | True | True | [] | 1133 | N/A / N/A |
| 19 | full | L5 | True | True | [] | 113 | N/A / N/A |
| 190 | full | L5 | True | True | [] | 1139 | N/A / N/A |
| 191 | full | L5 | True | True | [] | 1145 | N/A / N/A |
| 192 | full | L5 | True | True | [] | 1151 | N/A / N/A |
| 193 | full | L5 | True | True | [] | 1157 | N/A / N/A |
| 194 | full | L5 | True | True | [] | 1163 | N/A / N/A |
| 195 | full | L5 | True | True | [] | 1169 | N/A / N/A |
| 196 | full | L5 | True | True | [] | 1175 | N/A / N/A |
| 197 | full | L5 | True | True | [] | 1181 | N/A / N/A |
| 198 | full | L5 | True | True | [] | 1187 | N/A / N/A |
| 199 | full | L5 | True | True | [] | 1193 | N/A / N/A |
| 2 | full | L5 | True | True | [] | 11 | N/A / N/A |
| 20 | full | L5 | True | True | [] | 119 | N/A / N/A |
| 200 | full | L5 | True | True | [] | 1199 | N/A / N/A |
| 201 | full | L5 | True | True | [] | 1205 | N/A / N/A |
| 202 | full | L5 | True | True | [] | 1211 | N/A / N/A |
| 203 | full | L5 | True | True | [] | 1217 | N/A / N/A |
| 204 | full | L5 | True | True | [] | 1223 | N/A / N/A |
| 205 | full | L5 | True | True | [] | 1229 | N/A / N/A |
| 206 | full | L5 | True | True | [] | 1235 | N/A / N/A |
| 21 | full | L5 | True | True | [] | 125 | N/A / N/A |
| 22 | full | L5 | True | True | [] | 131 | N/A / N/A |
| 23 | full | L5 | True | True | [] | 137 | N/A / N/A |
| 24 | full | L5 | True | True | [] | 143 | N/A / N/A |
| 25 | full | L5 | True | True | [] | 149 | N/A / N/A |
| 26 | full | L5 | True | True | [] | 155 | N/A / N/A |
| 27 | full | L5 | True | True | [] | 161 | N/A / N/A |
| 28 | full | L5 | True | True | [] | 167 | N/A / N/A |
| 29 | full | L5 | True | True | [] | 173 | N/A / N/A |
| 3 | full | L5 | True | True | [] | 17 | N/A / N/A |
| 30 | full | L5 | True | True | [] | 179 | N/A / N/A |
| 31 | full | L5 | True | True | [] | 185 | N/A / N/A |
| 32 | full | L5 | True | True | [] | 191 | N/A / N/A |
| 33 | full | L5 | True | True | [] | 197 | N/A / N/A |
| 34 | full | L5 | True | True | [] | 203 | N/A / N/A |
| 35 | full | L5 | True | True | [] | 209 | N/A / N/A |
| 36 | full | L5 | True | True | [] | 215 | N/A / N/A |
| 37 | full | L5 | True | True | [] | 221 | N/A / N/A |
| 38 | full | L5 | True | True | [] | 227 | N/A / N/A |
| 39 | full | L5 | True | True | [] | 233 | N/A / N/A |
| 4 | full | L5 | True | True | [] | 23 | N/A / N/A |
| 40 | full | L5 | True | True | [] | 239 | N/A / N/A |
| 41 | full | L5 | True | True | [] | 245 | N/A / N/A |
| 42 | full | L5 | True | True | [] | 251 | N/A / N/A |
| 43 | full | L5 | True | True | [] | 257 | N/A / N/A |
| 44 | full | L5 | True | True | [] | 263 | N/A / N/A |
| 45 | full | L5 | True | True | [] | 269 | N/A / N/A |
| 46 | full | L5 | True | True | [] | 275 | N/A / N/A |
| 47 | full | L5 | True | True | [] | 281 | N/A / N/A |
| 48 | full | L5 | True | True | [] | 287 | N/A / N/A |
| 49 | full | L5 | True | True | [] | 293 | N/A / N/A |
| 5 | full | L5 | True | True | [] | 29 | N/A / N/A |
| 50 | full | L5 | True | True | [] | 299 | N/A / N/A |
| 51 | full | L5 | True | True | [] | 305 | N/A / N/A |
| 52 | full | L5 | True | True | [] | 311 | N/A / N/A |
| 53 | full | L5 | True | True | [] | 317 | N/A / N/A |
| 54 | full | L5 | True | True | [] | 323 | N/A / N/A |
| 55 | full | L5 | True | True | [] | 329 | N/A / N/A |
| 56 | full | L5 | True | True | [] | 335 | N/A / N/A |
| 57 | full | L5 | True | True | [] | 341 | N/A / N/A |
| 58 | full | L5 | True | True | [] | 347 | N/A / N/A |
| 59 | full | L5 | True | True | [] | 353 | N/A / N/A |
| 6 | full | L5 | True | True | [] | 35 | N/A / N/A |
| 60 | full | L5 | True | True | [] | 359 | N/A / N/A |
| 61 | full | L5 | True | True | [] | 365 | N/A / N/A |
| 62 | full | L5 | True | True | [] | 371 | N/A / N/A |
| 63 | full | L5 | True | True | [] | 377 | N/A / N/A |
| 64 | full | L5 | True | True | [] | 383 | N/A / N/A |
| 65 | full | L5 | True | True | [] | 389 | N/A / N/A |
| 66 | full | L5 | True | True | [] | 395 | N/A / N/A |
| 67 | full | L5 | True | True | [] | 401 | N/A / N/A |
| 68 | full | L5 | True | True | [] | 407 | N/A / N/A |
| 69 | full | L5 | True | True | [] | 413 | N/A / N/A |
| 7 | full | L5 | True | True | [] | 41 | N/A / N/A |
| 70 | full | L5 | True | True | [] | 419 | N/A / N/A |
| 71 | full | L5 | True | True | [] | 425 | N/A / N/A |
| 72 | full | L5 | True | True | [] | 431 | N/A / N/A |
| 73 | full | L5 | True | True | [] | 437 | N/A / N/A |
| 74 | full | L5 | True | True | [] | 443 | N/A / N/A |
| 75 | full | L5 | True | True | [] | 449 | N/A / N/A |
| 76 | full | L5 | True | True | [] | 455 | N/A / N/A |
| 77 | full | L5 | True | True | [] | 461 | N/A / N/A |
| 78 | full | L5 | True | True | [] | 467 | N/A / N/A |
| 79 | full | L5 | True | True | [] | 473 | N/A / N/A |
| 8 | full | L5 | True | True | [] | 47 | N/A / N/A |
| 80 | full | L5 | True | True | [] | 479 | N/A / N/A |
| 81 | full | L5 | True | True | [] | 485 | N/A / N/A |
| 82 | full | L5 | True | True | [] | 491 | N/A / N/A |
| 83 | full | L5 | True | True | [] | 497 | N/A / N/A |
| 84 | full | L5 | True | True | [] | 503 | N/A / N/A |
| 85 | full | L5 | True | True | [] | 509 | N/A / N/A |
| 86 | full | L5 | True | True | [] | 515 | N/A / N/A |
| 87 | full | L5 | True | True | [] | 521 | N/A / N/A |
| 88 | full | L5 | True | True | [] | 527 | N/A / N/A |
| 89 | full | L5 | True | True | [] | 533 | N/A / N/A |
| 9 | full | L5 | True | True | [] | 53 | N/A / N/A |
| 90 | full | L5 | True | True | [] | 539 | N/A / N/A |
| 91 | full | L5 | True | True | [] | 545 | N/A / N/A |
| 92 | full | L5 | True | True | [] | 551 | N/A / N/A |
| 93 | full | L5 | True | True | [] | 557 | N/A / N/A |
| 94 | full | L5 | True | True | [] | 563 | N/A / N/A |
| 95 | full | L5 | True | True | [] | 569 | N/A / N/A |
| 96 | full | L5 | True | True | [] | 575 | N/A / N/A |
| 97 | full | L5 | True | True | [] | 581 | N/A / N/A |
| 98 | full | L5 | True | True | [] | 587 | N/A / N/A |
| 99 | full | L5 | True | True | [] | 593 | N/A / N/A |

- 结局标签（run-level oracle）：SDC

## 8. 为什么该结局成立

### fault 1

主链每一条边均验证为直接 parent：

- `0` (fault_applied) → `1` (carrier_state)；child.parent=0 ✓
- `1` (carrier_state) → `2` (operand_read)；child.parent=1 ✓
- `2` (operand_read) → `3` (execute)；child.parent=2 ✓
- `3` (execute) → `4` (prf_writeback)；child.parent=3 ✓
- `4` (prf_writeback) → `5` (commit)；child.parent=4 ✓
- `5` (commit) → `1236` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

### fault 10

主链每一条边均验证为直接 parent：

- `54` (fault_applied) → `55` (carrier_state)；child.parent=54 ✓
- `55` (carrier_state) → `56` (operand_read)；child.parent=55 ✓
- `56` (operand_read) → `57` (execute)；child.parent=56 ✓
- `57` (execute) → `58` (prf_writeback)；child.parent=57 ✓
- `58` (prf_writeback) → `59` (commit)；child.parent=58 ✓
- `59` (commit) → `1245` (chain_end)；child.parent=59 ✓

- L5 真实见证：`59` kind=commit outcome=errant_commit oracle_diff=—

### fault 100

主链每一条边均验证为直接 parent：

- `594` (fault_applied) → `595` (carrier_state)；child.parent=594 ✓
- `595` (carrier_state) → `596` (operand_read)；child.parent=595 ✓
- `596` (operand_read) → `597` (execute)；child.parent=596 ✓
- `597` (execute) → `598` (prf_writeback)；child.parent=597 ✓
- `598` (prf_writeback) → `599` (commit)；child.parent=598 ✓
- `599` (commit) → `1335` (chain_end)；child.parent=599 ✓

- L5 真实见证：`599` kind=commit outcome=errant_commit oracle_diff=—

### fault 101

主链每一条边均验证为直接 parent：

- `600` (fault_applied) → `601` (carrier_state)；child.parent=600 ✓
- `601` (carrier_state) → `602` (operand_read)；child.parent=601 ✓
- `602` (operand_read) → `603` (execute)；child.parent=602 ✓
- `603` (execute) → `604` (prf_writeback)；child.parent=603 ✓
- `604` (prf_writeback) → `605` (commit)；child.parent=604 ✓
- `605` (commit) → `1336` (chain_end)；child.parent=605 ✓

- L5 真实见证：`605` kind=commit outcome=errant_commit oracle_diff=—

### fault 102

主链每一条边均验证为直接 parent：

- `606` (fault_applied) → `607` (carrier_state)；child.parent=606 ✓
- `607` (carrier_state) → `608` (operand_read)；child.parent=607 ✓
- `608` (operand_read) → `609` (execute)；child.parent=608 ✓
- `609` (execute) → `610` (prf_writeback)；child.parent=609 ✓
- `610` (prf_writeback) → `611` (commit)；child.parent=610 ✓
- `611` (commit) → `1337` (chain_end)；child.parent=611 ✓

- L5 真实见证：`611` kind=commit outcome=errant_commit oracle_diff=—

### fault 103

主链每一条边均验证为直接 parent：

- `612` (fault_applied) → `613` (carrier_state)；child.parent=612 ✓
- `613` (carrier_state) → `614` (operand_read)；child.parent=613 ✓
- `614` (operand_read) → `615` (execute)；child.parent=614 ✓
- `615` (execute) → `616` (prf_writeback)；child.parent=615 ✓
- `616` (prf_writeback) → `617` (commit)；child.parent=616 ✓
- `617` (commit) → `1338` (chain_end)；child.parent=617 ✓

- L5 真实见证：`617` kind=commit outcome=errant_commit oracle_diff=—

### fault 104

主链每一条边均验证为直接 parent：

- `618` (fault_applied) → `619` (carrier_state)；child.parent=618 ✓
- `619` (carrier_state) → `620` (operand_read)；child.parent=619 ✓
- `620` (operand_read) → `621` (execute)；child.parent=620 ✓
- `621` (execute) → `622` (prf_writeback)；child.parent=621 ✓
- `622` (prf_writeback) → `623` (commit)；child.parent=622 ✓
- `623` (commit) → `1339` (chain_end)；child.parent=623 ✓

- L5 真实见证：`623` kind=commit outcome=errant_commit oracle_diff=—

### fault 105

主链每一条边均验证为直接 parent：

- `624` (fault_applied) → `625` (carrier_state)；child.parent=624 ✓
- `625` (carrier_state) → `626` (operand_read)；child.parent=625 ✓
- `626` (operand_read) → `627` (execute)；child.parent=626 ✓
- `627` (execute) → `628` (prf_writeback)；child.parent=627 ✓
- `628` (prf_writeback) → `629` (commit)；child.parent=628 ✓
- `629` (commit) → `1340` (chain_end)；child.parent=629 ✓

- L5 真实见证：`629` kind=commit outcome=errant_commit oracle_diff=—

### fault 106

主链每一条边均验证为直接 parent：

- `630` (fault_applied) → `631` (carrier_state)；child.parent=630 ✓
- `631` (carrier_state) → `632` (operand_read)；child.parent=631 ✓
- `632` (operand_read) → `633` (execute)；child.parent=632 ✓
- `633` (execute) → `634` (prf_writeback)；child.parent=633 ✓
- `634` (prf_writeback) → `635` (commit)；child.parent=634 ✓
- `635` (commit) → `1341` (chain_end)；child.parent=635 ✓

- L5 真实见证：`635` kind=commit outcome=errant_commit oracle_diff=—

### fault 107

主链每一条边均验证为直接 parent：

- `636` (fault_applied) → `637` (carrier_state)；child.parent=636 ✓
- `637` (carrier_state) → `638` (operand_read)；child.parent=637 ✓
- `638` (operand_read) → `639` (execute)；child.parent=638 ✓
- `639` (execute) → `640` (prf_writeback)；child.parent=639 ✓
- `640` (prf_writeback) → `641` (commit)；child.parent=640 ✓
- `641` (commit) → `1342` (chain_end)；child.parent=641 ✓

- L5 真实见证：`641` kind=commit outcome=errant_commit oracle_diff=—

### fault 108

主链每一条边均验证为直接 parent：

- `642` (fault_applied) → `643` (carrier_state)；child.parent=642 ✓
- `643` (carrier_state) → `644` (operand_read)；child.parent=643 ✓
- `644` (operand_read) → `645` (execute)；child.parent=644 ✓
- `645` (execute) → `646` (prf_writeback)；child.parent=645 ✓
- `646` (prf_writeback) → `647` (commit)；child.parent=646 ✓
- `647` (commit) → `1343` (chain_end)；child.parent=647 ✓

- L5 真实见证：`647` kind=commit outcome=errant_commit oracle_diff=—

### fault 109

主链每一条边均验证为直接 parent：

- `648` (fault_applied) → `649` (carrier_state)；child.parent=648 ✓
- `649` (carrier_state) → `650` (operand_read)；child.parent=649 ✓
- `650` (operand_read) → `651` (execute)；child.parent=650 ✓
- `651` (execute) → `652` (prf_writeback)；child.parent=651 ✓
- `652` (prf_writeback) → `653` (commit)；child.parent=652 ✓
- `653` (commit) → `1344` (chain_end)；child.parent=653 ✓

- L5 真实见证：`653` kind=commit outcome=errant_commit oracle_diff=—

### fault 11

主链每一条边均验证为直接 parent：

- `60` (fault_applied) → `61` (carrier_state)；child.parent=60 ✓
- `61` (carrier_state) → `62` (operand_read)；child.parent=61 ✓
- `62` (operand_read) → `63` (execute)；child.parent=62 ✓
- `63` (execute) → `64` (prf_writeback)；child.parent=63 ✓
- `64` (prf_writeback) → `65` (commit)；child.parent=64 ✓
- `65` (commit) → `1246` (chain_end)；child.parent=65 ✓

- L5 真实见证：`65` kind=commit outcome=errant_commit oracle_diff=—

### fault 110

主链每一条边均验证为直接 parent：

- `654` (fault_applied) → `655` (carrier_state)；child.parent=654 ✓
- `655` (carrier_state) → `656` (operand_read)；child.parent=655 ✓
- `656` (operand_read) → `657` (execute)；child.parent=656 ✓
- `657` (execute) → `658` (prf_writeback)；child.parent=657 ✓
- `658` (prf_writeback) → `659` (commit)；child.parent=658 ✓
- `659` (commit) → `1345` (chain_end)；child.parent=659 ✓

- L5 真实见证：`659` kind=commit outcome=errant_commit oracle_diff=—

### fault 111

主链每一条边均验证为直接 parent：

- `660` (fault_applied) → `661` (carrier_state)；child.parent=660 ✓
- `661` (carrier_state) → `662` (operand_read)；child.parent=661 ✓
- `662` (operand_read) → `663` (execute)；child.parent=662 ✓
- `663` (execute) → `664` (prf_writeback)；child.parent=663 ✓
- `664` (prf_writeback) → `665` (commit)；child.parent=664 ✓
- `665` (commit) → `1346` (chain_end)；child.parent=665 ✓

- L5 真实见证：`665` kind=commit outcome=errant_commit oracle_diff=—

### fault 112

主链每一条边均验证为直接 parent：

- `666` (fault_applied) → `667` (carrier_state)；child.parent=666 ✓
- `667` (carrier_state) → `668` (operand_read)；child.parent=667 ✓
- `668` (operand_read) → `669` (execute)；child.parent=668 ✓
- `669` (execute) → `670` (prf_writeback)；child.parent=669 ✓
- `670` (prf_writeback) → `671` (commit)；child.parent=670 ✓
- `671` (commit) → `1347` (chain_end)；child.parent=671 ✓

- L5 真实见证：`671` kind=commit outcome=errant_commit oracle_diff=—

### fault 113

主链每一条边均验证为直接 parent：

- `672` (fault_applied) → `673` (carrier_state)；child.parent=672 ✓
- `673` (carrier_state) → `674` (operand_read)；child.parent=673 ✓
- `674` (operand_read) → `675` (execute)；child.parent=674 ✓
- `675` (execute) → `676` (prf_writeback)；child.parent=675 ✓
- `676` (prf_writeback) → `677` (commit)；child.parent=676 ✓
- `677` (commit) → `1348` (chain_end)；child.parent=677 ✓

- L5 真实见证：`677` kind=commit outcome=errant_commit oracle_diff=—

### fault 114

主链每一条边均验证为直接 parent：

- `678` (fault_applied) → `679` (carrier_state)；child.parent=678 ✓
- `679` (carrier_state) → `680` (operand_read)；child.parent=679 ✓
- `680` (operand_read) → `681` (execute)；child.parent=680 ✓
- `681` (execute) → `682` (prf_writeback)；child.parent=681 ✓
- `682` (prf_writeback) → `683` (commit)；child.parent=682 ✓
- `683` (commit) → `1349` (chain_end)；child.parent=683 ✓

- L5 真实见证：`683` kind=commit outcome=errant_commit oracle_diff=—

### fault 115

主链每一条边均验证为直接 parent：

- `684` (fault_applied) → `685` (carrier_state)；child.parent=684 ✓
- `685` (carrier_state) → `686` (operand_read)；child.parent=685 ✓
- `686` (operand_read) → `687` (execute)；child.parent=686 ✓
- `687` (execute) → `688` (prf_writeback)；child.parent=687 ✓
- `688` (prf_writeback) → `689` (commit)；child.parent=688 ✓
- `689` (commit) → `1350` (chain_end)；child.parent=689 ✓

- L5 真实见证：`689` kind=commit outcome=errant_commit oracle_diff=—

### fault 116

主链每一条边均验证为直接 parent：

- `690` (fault_applied) → `691` (carrier_state)；child.parent=690 ✓
- `691` (carrier_state) → `692` (operand_read)；child.parent=691 ✓
- `692` (operand_read) → `693` (execute)；child.parent=692 ✓
- `693` (execute) → `694` (prf_writeback)；child.parent=693 ✓
- `694` (prf_writeback) → `695` (commit)；child.parent=694 ✓
- `695` (commit) → `1351` (chain_end)；child.parent=695 ✓

- L5 真实见证：`695` kind=commit outcome=errant_commit oracle_diff=—

### fault 117

主链每一条边均验证为直接 parent：

- `696` (fault_applied) → `697` (carrier_state)；child.parent=696 ✓
- `697` (carrier_state) → `698` (operand_read)；child.parent=697 ✓
- `698` (operand_read) → `699` (execute)；child.parent=698 ✓
- `699` (execute) → `700` (prf_writeback)；child.parent=699 ✓
- `700` (prf_writeback) → `701` (commit)；child.parent=700 ✓
- `701` (commit) → `1352` (chain_end)；child.parent=701 ✓

- L5 真实见证：`701` kind=commit outcome=errant_commit oracle_diff=—

### fault 118

主链每一条边均验证为直接 parent：

- `702` (fault_applied) → `703` (carrier_state)；child.parent=702 ✓
- `703` (carrier_state) → `704` (operand_read)；child.parent=703 ✓
- `704` (operand_read) → `705` (execute)；child.parent=704 ✓
- `705` (execute) → `706` (prf_writeback)；child.parent=705 ✓
- `706` (prf_writeback) → `707` (commit)；child.parent=706 ✓
- `707` (commit) → `1353` (chain_end)；child.parent=707 ✓

- L5 真实见证：`707` kind=commit outcome=errant_commit oracle_diff=—

### fault 119

主链每一条边均验证为直接 parent：

- `708` (fault_applied) → `709` (carrier_state)；child.parent=708 ✓
- `709` (carrier_state) → `710` (operand_read)；child.parent=709 ✓
- `710` (operand_read) → `711` (execute)；child.parent=710 ✓
- `711` (execute) → `712` (prf_writeback)；child.parent=711 ✓
- `712` (prf_writeback) → `713` (commit)；child.parent=712 ✓
- `713` (commit) → `1354` (chain_end)；child.parent=713 ✓

- L5 真实见证：`713` kind=commit outcome=errant_commit oracle_diff=—

### fault 12

主链每一条边均验证为直接 parent：

- `66` (fault_applied) → `67` (carrier_state)；child.parent=66 ✓
- `67` (carrier_state) → `68` (operand_read)；child.parent=67 ✓
- `68` (operand_read) → `69` (execute)；child.parent=68 ✓
- `69` (execute) → `70` (prf_writeback)；child.parent=69 ✓
- `70` (prf_writeback) → `71` (commit)；child.parent=70 ✓
- `71` (commit) → `1247` (chain_end)；child.parent=71 ✓

- L5 真实见证：`71` kind=commit outcome=errant_commit oracle_diff=—

### fault 120

主链每一条边均验证为直接 parent：

- `714` (fault_applied) → `715` (carrier_state)；child.parent=714 ✓
- `715` (carrier_state) → `716` (operand_read)；child.parent=715 ✓
- `716` (operand_read) → `717` (execute)；child.parent=716 ✓
- `717` (execute) → `718` (prf_writeback)；child.parent=717 ✓
- `718` (prf_writeback) → `719` (commit)；child.parent=718 ✓
- `719` (commit) → `1355` (chain_end)；child.parent=719 ✓

- L5 真实见证：`719` kind=commit outcome=errant_commit oracle_diff=—

### fault 121

主链每一条边均验证为直接 parent：

- `720` (fault_applied) → `721` (carrier_state)；child.parent=720 ✓
- `721` (carrier_state) → `722` (operand_read)；child.parent=721 ✓
- `722` (operand_read) → `723` (execute)；child.parent=722 ✓
- `723` (execute) → `724` (prf_writeback)；child.parent=723 ✓
- `724` (prf_writeback) → `725` (commit)；child.parent=724 ✓
- `725` (commit) → `1356` (chain_end)；child.parent=725 ✓

- L5 真实见证：`725` kind=commit outcome=errant_commit oracle_diff=—

### fault 122

主链每一条边均验证为直接 parent：

- `726` (fault_applied) → `727` (carrier_state)；child.parent=726 ✓
- `727` (carrier_state) → `728` (operand_read)；child.parent=727 ✓
- `728` (operand_read) → `729` (execute)；child.parent=728 ✓
- `729` (execute) → `730` (prf_writeback)；child.parent=729 ✓
- `730` (prf_writeback) → `731` (commit)；child.parent=730 ✓
- `731` (commit) → `1357` (chain_end)；child.parent=731 ✓

- L5 真实见证：`731` kind=commit outcome=errant_commit oracle_diff=—

### fault 123

主链每一条边均验证为直接 parent：

- `732` (fault_applied) → `733` (carrier_state)；child.parent=732 ✓
- `733` (carrier_state) → `734` (operand_read)；child.parent=733 ✓
- `734` (operand_read) → `735` (execute)；child.parent=734 ✓
- `735` (execute) → `736` (prf_writeback)；child.parent=735 ✓
- `736` (prf_writeback) → `737` (commit)；child.parent=736 ✓
- `737` (commit) → `1358` (chain_end)；child.parent=737 ✓

- L5 真实见证：`737` kind=commit outcome=errant_commit oracle_diff=—

### fault 124

主链每一条边均验证为直接 parent：

- `738` (fault_applied) → `739` (carrier_state)；child.parent=738 ✓
- `739` (carrier_state) → `740` (operand_read)；child.parent=739 ✓
- `740` (operand_read) → `741` (execute)；child.parent=740 ✓
- `741` (execute) → `742` (prf_writeback)；child.parent=741 ✓
- `742` (prf_writeback) → `743` (commit)；child.parent=742 ✓
- `743` (commit) → `1359` (chain_end)；child.parent=743 ✓

- L5 真实见证：`743` kind=commit outcome=errant_commit oracle_diff=—

### fault 125

主链每一条边均验证为直接 parent：

- `744` (fault_applied) → `745` (carrier_state)；child.parent=744 ✓
- `745` (carrier_state) → `746` (operand_read)；child.parent=745 ✓
- `746` (operand_read) → `747` (execute)；child.parent=746 ✓
- `747` (execute) → `748` (prf_writeback)；child.parent=747 ✓
- `748` (prf_writeback) → `749` (commit)；child.parent=748 ✓
- `749` (commit) → `1360` (chain_end)；child.parent=749 ✓

- L5 真实见证：`749` kind=commit outcome=errant_commit oracle_diff=—

### fault 126

主链每一条边均验证为直接 parent：

- `750` (fault_applied) → `751` (carrier_state)；child.parent=750 ✓
- `751` (carrier_state) → `752` (operand_read)；child.parent=751 ✓
- `752` (operand_read) → `753` (execute)；child.parent=752 ✓
- `753` (execute) → `754` (prf_writeback)；child.parent=753 ✓
- `754` (prf_writeback) → `755` (commit)；child.parent=754 ✓
- `755` (commit) → `1361` (chain_end)；child.parent=755 ✓

- L5 真实见证：`755` kind=commit outcome=errant_commit oracle_diff=—

### fault 127

主链每一条边均验证为直接 parent：

- `756` (fault_applied) → `757` (carrier_state)；child.parent=756 ✓
- `757` (carrier_state) → `758` (operand_read)；child.parent=757 ✓
- `758` (operand_read) → `759` (execute)；child.parent=758 ✓
- `759` (execute) → `760` (prf_writeback)；child.parent=759 ✓
- `760` (prf_writeback) → `761` (commit)；child.parent=760 ✓
- `761` (commit) → `1362` (chain_end)；child.parent=761 ✓

- L5 真实见证：`761` kind=commit outcome=errant_commit oracle_diff=—

### fault 128

主链每一条边均验证为直接 parent：

- `762` (fault_applied) → `763` (carrier_state)；child.parent=762 ✓
- `763` (carrier_state) → `764` (operand_read)；child.parent=763 ✓
- `764` (operand_read) → `765` (execute)；child.parent=764 ✓
- `765` (execute) → `766` (prf_writeback)；child.parent=765 ✓
- `766` (prf_writeback) → `767` (commit)；child.parent=766 ✓
- `767` (commit) → `1363` (chain_end)；child.parent=767 ✓

- L5 真实见证：`767` kind=commit outcome=errant_commit oracle_diff=—

### fault 129

主链每一条边均验证为直接 parent：

- `768` (fault_applied) → `769` (carrier_state)；child.parent=768 ✓
- `769` (carrier_state) → `770` (operand_read)；child.parent=769 ✓
- `770` (operand_read) → `771` (execute)；child.parent=770 ✓
- `771` (execute) → `772` (prf_writeback)；child.parent=771 ✓
- `772` (prf_writeback) → `773` (commit)；child.parent=772 ✓
- `773` (commit) → `1364` (chain_end)；child.parent=773 ✓

- L5 真实见证：`773` kind=commit outcome=errant_commit oracle_diff=—

### fault 13

主链每一条边均验证为直接 parent：

- `72` (fault_applied) → `73` (carrier_state)；child.parent=72 ✓
- `73` (carrier_state) → `74` (operand_read)；child.parent=73 ✓
- `74` (operand_read) → `75` (execute)；child.parent=74 ✓
- `75` (execute) → `76` (prf_writeback)；child.parent=75 ✓
- `76` (prf_writeback) → `77` (commit)；child.parent=76 ✓
- `77` (commit) → `1248` (chain_end)；child.parent=77 ✓

- L5 真实见证：`77` kind=commit outcome=errant_commit oracle_diff=—

### fault 130

主链每一条边均验证为直接 parent：

- `774` (fault_applied) → `775` (carrier_state)；child.parent=774 ✓
- `775` (carrier_state) → `776` (operand_read)；child.parent=775 ✓
- `776` (operand_read) → `777` (execute)；child.parent=776 ✓
- `777` (execute) → `778` (prf_writeback)；child.parent=777 ✓
- `778` (prf_writeback) → `779` (commit)；child.parent=778 ✓
- `779` (commit) → `1365` (chain_end)；child.parent=779 ✓

- L5 真实见证：`779` kind=commit outcome=errant_commit oracle_diff=—

### fault 131

主链每一条边均验证为直接 parent：

- `780` (fault_applied) → `781` (carrier_state)；child.parent=780 ✓
- `781` (carrier_state) → `782` (operand_read)；child.parent=781 ✓
- `782` (operand_read) → `783` (execute)；child.parent=782 ✓
- `783` (execute) → `784` (prf_writeback)；child.parent=783 ✓
- `784` (prf_writeback) → `785` (commit)；child.parent=784 ✓
- `785` (commit) → `1366` (chain_end)；child.parent=785 ✓

- L5 真实见证：`785` kind=commit outcome=errant_commit oracle_diff=—

### fault 132

主链每一条边均验证为直接 parent：

- `786` (fault_applied) → `787` (carrier_state)；child.parent=786 ✓
- `787` (carrier_state) → `788` (operand_read)；child.parent=787 ✓
- `788` (operand_read) → `789` (execute)；child.parent=788 ✓
- `789` (execute) → `790` (prf_writeback)；child.parent=789 ✓
- `790` (prf_writeback) → `791` (commit)；child.parent=790 ✓
- `791` (commit) → `1367` (chain_end)；child.parent=791 ✓

- L5 真实见证：`791` kind=commit outcome=errant_commit oracle_diff=—

### fault 133

主链每一条边均验证为直接 parent：

- `792` (fault_applied) → `793` (carrier_state)；child.parent=792 ✓
- `793` (carrier_state) → `794` (operand_read)；child.parent=793 ✓
- `794` (operand_read) → `795` (execute)；child.parent=794 ✓
- `795` (execute) → `796` (prf_writeback)；child.parent=795 ✓
- `796` (prf_writeback) → `797` (commit)；child.parent=796 ✓
- `797` (commit) → `1368` (chain_end)；child.parent=797 ✓

- L5 真实见证：`797` kind=commit outcome=errant_commit oracle_diff=—

### fault 134

主链每一条边均验证为直接 parent：

- `798` (fault_applied) → `799` (carrier_state)；child.parent=798 ✓
- `799` (carrier_state) → `800` (operand_read)；child.parent=799 ✓
- `800` (operand_read) → `801` (execute)；child.parent=800 ✓
- `801` (execute) → `802` (prf_writeback)；child.parent=801 ✓
- `802` (prf_writeback) → `803` (commit)；child.parent=802 ✓
- `803` (commit) → `1369` (chain_end)；child.parent=803 ✓

- L5 真实见证：`803` kind=commit outcome=errant_commit oracle_diff=—

### fault 135

主链每一条边均验证为直接 parent：

- `804` (fault_applied) → `805` (carrier_state)；child.parent=804 ✓
- `805` (carrier_state) → `806` (operand_read)；child.parent=805 ✓
- `806` (operand_read) → `807` (execute)；child.parent=806 ✓
- `807` (execute) → `808` (prf_writeback)；child.parent=807 ✓
- `808` (prf_writeback) → `809` (commit)；child.parent=808 ✓
- `809` (commit) → `1370` (chain_end)；child.parent=809 ✓

- L5 真实见证：`809` kind=commit outcome=errant_commit oracle_diff=—

### fault 136

主链每一条边均验证为直接 parent：

- `810` (fault_applied) → `811` (carrier_state)；child.parent=810 ✓
- `811` (carrier_state) → `812` (operand_read)；child.parent=811 ✓
- `812` (operand_read) → `813` (execute)；child.parent=812 ✓
- `813` (execute) → `814` (prf_writeback)；child.parent=813 ✓
- `814` (prf_writeback) → `815` (commit)；child.parent=814 ✓
- `815` (commit) → `1371` (chain_end)；child.parent=815 ✓

- L5 真实见证：`815` kind=commit outcome=errant_commit oracle_diff=—

### fault 137

主链每一条边均验证为直接 parent：

- `816` (fault_applied) → `817` (carrier_state)；child.parent=816 ✓
- `817` (carrier_state) → `818` (operand_read)；child.parent=817 ✓
- `818` (operand_read) → `819` (execute)；child.parent=818 ✓
- `819` (execute) → `820` (prf_writeback)；child.parent=819 ✓
- `820` (prf_writeback) → `821` (commit)；child.parent=820 ✓
- `821` (commit) → `1372` (chain_end)；child.parent=821 ✓

- L5 真实见证：`821` kind=commit outcome=errant_commit oracle_diff=—

### fault 138

主链每一条边均验证为直接 parent：

- `822` (fault_applied) → `823` (carrier_state)；child.parent=822 ✓
- `823` (carrier_state) → `824` (operand_read)；child.parent=823 ✓
- `824` (operand_read) → `825` (execute)；child.parent=824 ✓
- `825` (execute) → `826` (prf_writeback)；child.parent=825 ✓
- `826` (prf_writeback) → `827` (commit)；child.parent=826 ✓
- `827` (commit) → `1373` (chain_end)；child.parent=827 ✓

- L5 真实见证：`827` kind=commit outcome=errant_commit oracle_diff=—

### fault 139

主链每一条边均验证为直接 parent：

- `828` (fault_applied) → `829` (carrier_state)；child.parent=828 ✓
- `829` (carrier_state) → `830` (operand_read)；child.parent=829 ✓
- `830` (operand_read) → `831` (execute)；child.parent=830 ✓
- `831` (execute) → `832` (prf_writeback)；child.parent=831 ✓
- `832` (prf_writeback) → `833` (commit)；child.parent=832 ✓
- `833` (commit) → `1374` (chain_end)；child.parent=833 ✓

- L5 真实见证：`833` kind=commit outcome=errant_commit oracle_diff=—

### fault 14

主链每一条边均验证为直接 parent：

- `78` (fault_applied) → `79` (carrier_state)；child.parent=78 ✓
- `79` (carrier_state) → `80` (operand_read)；child.parent=79 ✓
- `80` (operand_read) → `81` (execute)；child.parent=80 ✓
- `81` (execute) → `82` (prf_writeback)；child.parent=81 ✓
- `82` (prf_writeback) → `83` (commit)；child.parent=82 ✓
- `83` (commit) → `1249` (chain_end)；child.parent=83 ✓

- L5 真实见证：`83` kind=commit outcome=errant_commit oracle_diff=—

### fault 140

主链每一条边均验证为直接 parent：

- `834` (fault_applied) → `835` (carrier_state)；child.parent=834 ✓
- `835` (carrier_state) → `836` (operand_read)；child.parent=835 ✓
- `836` (operand_read) → `837` (execute)；child.parent=836 ✓
- `837` (execute) → `838` (prf_writeback)；child.parent=837 ✓
- `838` (prf_writeback) → `839` (commit)；child.parent=838 ✓
- `839` (commit) → `1375` (chain_end)；child.parent=839 ✓

- L5 真实见证：`839` kind=commit outcome=errant_commit oracle_diff=—

### fault 141

主链每一条边均验证为直接 parent：

- `840` (fault_applied) → `841` (carrier_state)；child.parent=840 ✓
- `841` (carrier_state) → `842` (operand_read)；child.parent=841 ✓
- `842` (operand_read) → `843` (execute)；child.parent=842 ✓
- `843` (execute) → `844` (prf_writeback)；child.parent=843 ✓
- `844` (prf_writeback) → `845` (commit)；child.parent=844 ✓
- `845` (commit) → `1376` (chain_end)；child.parent=845 ✓

- L5 真实见证：`845` kind=commit outcome=errant_commit oracle_diff=—

### fault 142

主链每一条边均验证为直接 parent：

- `846` (fault_applied) → `847` (carrier_state)；child.parent=846 ✓
- `847` (carrier_state) → `848` (operand_read)；child.parent=847 ✓
- `848` (operand_read) → `849` (execute)；child.parent=848 ✓
- `849` (execute) → `850` (prf_writeback)；child.parent=849 ✓
- `850` (prf_writeback) → `851` (commit)；child.parent=850 ✓
- `851` (commit) → `1377` (chain_end)；child.parent=851 ✓

- L5 真实见证：`851` kind=commit outcome=errant_commit oracle_diff=—

### fault 143

主链每一条边均验证为直接 parent：

- `852` (fault_applied) → `853` (carrier_state)；child.parent=852 ✓
- `853` (carrier_state) → `854` (operand_read)；child.parent=853 ✓
- `854` (operand_read) → `855` (execute)；child.parent=854 ✓
- `855` (execute) → `856` (prf_writeback)；child.parent=855 ✓
- `856` (prf_writeback) → `857` (commit)；child.parent=856 ✓
- `857` (commit) → `1378` (chain_end)；child.parent=857 ✓

- L5 真实见证：`857` kind=commit outcome=errant_commit oracle_diff=—

### fault 144

主链每一条边均验证为直接 parent：

- `858` (fault_applied) → `859` (carrier_state)；child.parent=858 ✓
- `859` (carrier_state) → `860` (operand_read)；child.parent=859 ✓
- `860` (operand_read) → `861` (execute)；child.parent=860 ✓
- `861` (execute) → `862` (prf_writeback)；child.parent=861 ✓
- `862` (prf_writeback) → `863` (commit)；child.parent=862 ✓
- `863` (commit) → `1379` (chain_end)；child.parent=863 ✓

- L5 真实见证：`863` kind=commit outcome=errant_commit oracle_diff=—

### fault 145

主链每一条边均验证为直接 parent：

- `864` (fault_applied) → `865` (carrier_state)；child.parent=864 ✓
- `865` (carrier_state) → `866` (operand_read)；child.parent=865 ✓
- `866` (operand_read) → `867` (execute)；child.parent=866 ✓
- `867` (execute) → `868` (prf_writeback)；child.parent=867 ✓
- `868` (prf_writeback) → `869` (commit)；child.parent=868 ✓
- `869` (commit) → `1380` (chain_end)；child.parent=869 ✓

- L5 真实见证：`869` kind=commit outcome=errant_commit oracle_diff=—

### fault 146

主链每一条边均验证为直接 parent：

- `870` (fault_applied) → `871` (carrier_state)；child.parent=870 ✓
- `871` (carrier_state) → `872` (operand_read)；child.parent=871 ✓
- `872` (operand_read) → `873` (execute)；child.parent=872 ✓
- `873` (execute) → `874` (prf_writeback)；child.parent=873 ✓
- `874` (prf_writeback) → `875` (commit)；child.parent=874 ✓
- `875` (commit) → `1381` (chain_end)；child.parent=875 ✓

- L5 真实见证：`875` kind=commit outcome=errant_commit oracle_diff=—

### fault 147

主链每一条边均验证为直接 parent：

- `876` (fault_applied) → `877` (carrier_state)；child.parent=876 ✓
- `877` (carrier_state) → `878` (operand_read)；child.parent=877 ✓
- `878` (operand_read) → `879` (execute)；child.parent=878 ✓
- `879` (execute) → `880` (prf_writeback)；child.parent=879 ✓
- `880` (prf_writeback) → `881` (commit)；child.parent=880 ✓
- `881` (commit) → `1382` (chain_end)；child.parent=881 ✓

- L5 真实见证：`881` kind=commit outcome=errant_commit oracle_diff=—

### fault 148

主链每一条边均验证为直接 parent：

- `882` (fault_applied) → `883` (carrier_state)；child.parent=882 ✓
- `883` (carrier_state) → `884` (operand_read)；child.parent=883 ✓
- `884` (operand_read) → `885` (execute)；child.parent=884 ✓
- `885` (execute) → `886` (prf_writeback)；child.parent=885 ✓
- `886` (prf_writeback) → `887` (commit)；child.parent=886 ✓
- `887` (commit) → `1383` (chain_end)；child.parent=887 ✓

- L5 真实见证：`887` kind=commit outcome=errant_commit oracle_diff=—

### fault 149

主链每一条边均验证为直接 parent：

- `888` (fault_applied) → `889` (carrier_state)；child.parent=888 ✓
- `889` (carrier_state) → `890` (operand_read)；child.parent=889 ✓
- `890` (operand_read) → `891` (execute)；child.parent=890 ✓
- `891` (execute) → `892` (prf_writeback)；child.parent=891 ✓
- `892` (prf_writeback) → `893` (commit)；child.parent=892 ✓
- `893` (commit) → `1384` (chain_end)；child.parent=893 ✓

- L5 真实见证：`893` kind=commit outcome=errant_commit oracle_diff=—

### fault 15

主链每一条边均验证为直接 parent：

- `84` (fault_applied) → `85` (carrier_state)；child.parent=84 ✓
- `85` (carrier_state) → `86` (operand_read)；child.parent=85 ✓
- `86` (operand_read) → `87` (execute)；child.parent=86 ✓
- `87` (execute) → `88` (prf_writeback)；child.parent=87 ✓
- `88` (prf_writeback) → `89` (commit)；child.parent=88 ✓
- `89` (commit) → `1250` (chain_end)；child.parent=89 ✓

- L5 真实见证：`89` kind=commit outcome=errant_commit oracle_diff=—

### fault 150

主链每一条边均验证为直接 parent：

- `894` (fault_applied) → `895` (carrier_state)；child.parent=894 ✓
- `895` (carrier_state) → `896` (operand_read)；child.parent=895 ✓
- `896` (operand_read) → `897` (execute)；child.parent=896 ✓
- `897` (execute) → `898` (prf_writeback)；child.parent=897 ✓
- `898` (prf_writeback) → `899` (commit)；child.parent=898 ✓
- `899` (commit) → `1385` (chain_end)；child.parent=899 ✓

- L5 真实见证：`899` kind=commit outcome=errant_commit oracle_diff=—

### fault 151

主链每一条边均验证为直接 parent：

- `900` (fault_applied) → `901` (carrier_state)；child.parent=900 ✓
- `901` (carrier_state) → `902` (operand_read)；child.parent=901 ✓
- `902` (operand_read) → `903` (execute)；child.parent=902 ✓
- `903` (execute) → `904` (prf_writeback)；child.parent=903 ✓
- `904` (prf_writeback) → `905` (commit)；child.parent=904 ✓
- `905` (commit) → `1386` (chain_end)；child.parent=905 ✓

- L5 真实见证：`905` kind=commit outcome=errant_commit oracle_diff=—

### fault 152

主链每一条边均验证为直接 parent：

- `906` (fault_applied) → `907` (carrier_state)；child.parent=906 ✓
- `907` (carrier_state) → `908` (operand_read)；child.parent=907 ✓
- `908` (operand_read) → `909` (execute)；child.parent=908 ✓
- `909` (execute) → `910` (prf_writeback)；child.parent=909 ✓
- `910` (prf_writeback) → `911` (commit)；child.parent=910 ✓
- `911` (commit) → `1387` (chain_end)；child.parent=911 ✓

- L5 真实见证：`911` kind=commit outcome=errant_commit oracle_diff=—

### fault 153

主链每一条边均验证为直接 parent：

- `912` (fault_applied) → `913` (carrier_state)；child.parent=912 ✓
- `913` (carrier_state) → `914` (operand_read)；child.parent=913 ✓
- `914` (operand_read) → `915` (execute)；child.parent=914 ✓
- `915` (execute) → `916` (prf_writeback)；child.parent=915 ✓
- `916` (prf_writeback) → `917` (commit)；child.parent=916 ✓
- `917` (commit) → `1388` (chain_end)；child.parent=917 ✓

- L5 真实见证：`917` kind=commit outcome=errant_commit oracle_diff=—

### fault 154

主链每一条边均验证为直接 parent：

- `918` (fault_applied) → `919` (carrier_state)；child.parent=918 ✓
- `919` (carrier_state) → `920` (operand_read)；child.parent=919 ✓
- `920` (operand_read) → `921` (execute)；child.parent=920 ✓
- `921` (execute) → `922` (prf_writeback)；child.parent=921 ✓
- `922` (prf_writeback) → `923` (commit)；child.parent=922 ✓
- `923` (commit) → `1389` (chain_end)；child.parent=923 ✓

- L5 真实见证：`923` kind=commit outcome=errant_commit oracle_diff=—

### fault 155

主链每一条边均验证为直接 parent：

- `924` (fault_applied) → `925` (carrier_state)；child.parent=924 ✓
- `925` (carrier_state) → `926` (operand_read)；child.parent=925 ✓
- `926` (operand_read) → `927` (execute)；child.parent=926 ✓
- `927` (execute) → `928` (prf_writeback)；child.parent=927 ✓
- `928` (prf_writeback) → `929` (commit)；child.parent=928 ✓
- `929` (commit) → `1390` (chain_end)；child.parent=929 ✓

- L5 真实见证：`929` kind=commit outcome=errant_commit oracle_diff=—

### fault 156

主链每一条边均验证为直接 parent：

- `930` (fault_applied) → `931` (carrier_state)；child.parent=930 ✓
- `931` (carrier_state) → `932` (operand_read)；child.parent=931 ✓
- `932` (operand_read) → `933` (execute)；child.parent=932 ✓
- `933` (execute) → `934` (prf_writeback)；child.parent=933 ✓
- `934` (prf_writeback) → `935` (commit)；child.parent=934 ✓
- `935` (commit) → `1391` (chain_end)；child.parent=935 ✓

- L5 真实见证：`935` kind=commit outcome=errant_commit oracle_diff=—

### fault 157

主链每一条边均验证为直接 parent：

- `936` (fault_applied) → `937` (carrier_state)；child.parent=936 ✓
- `937` (carrier_state) → `938` (operand_read)；child.parent=937 ✓
- `938` (operand_read) → `939` (execute)；child.parent=938 ✓
- `939` (execute) → `940` (prf_writeback)；child.parent=939 ✓
- `940` (prf_writeback) → `941` (commit)；child.parent=940 ✓
- `941` (commit) → `1392` (chain_end)；child.parent=941 ✓

- L5 真实见证：`941` kind=commit outcome=errant_commit oracle_diff=—

### fault 158

主链每一条边均验证为直接 parent：

- `942` (fault_applied) → `943` (carrier_state)；child.parent=942 ✓
- `943` (carrier_state) → `944` (operand_read)；child.parent=943 ✓
- `944` (operand_read) → `945` (execute)；child.parent=944 ✓
- `945` (execute) → `946` (prf_writeback)；child.parent=945 ✓
- `946` (prf_writeback) → `947` (commit)；child.parent=946 ✓
- `947` (commit) → `1393` (chain_end)；child.parent=947 ✓

- L5 真实见证：`947` kind=commit outcome=errant_commit oracle_diff=—

### fault 159

主链每一条边均验证为直接 parent：

- `948` (fault_applied) → `949` (carrier_state)；child.parent=948 ✓
- `949` (carrier_state) → `950` (operand_read)；child.parent=949 ✓
- `950` (operand_read) → `951` (execute)；child.parent=950 ✓
- `951` (execute) → `952` (prf_writeback)；child.parent=951 ✓
- `952` (prf_writeback) → `953` (commit)；child.parent=952 ✓
- `953` (commit) → `1394` (chain_end)；child.parent=953 ✓

- L5 真实见证：`953` kind=commit outcome=errant_commit oracle_diff=—

### fault 16

主链每一条边均验证为直接 parent：

- `90` (fault_applied) → `91` (carrier_state)；child.parent=90 ✓
- `91` (carrier_state) → `92` (operand_read)；child.parent=91 ✓
- `92` (operand_read) → `93` (execute)；child.parent=92 ✓
- `93` (execute) → `94` (prf_writeback)；child.parent=93 ✓
- `94` (prf_writeback) → `95` (commit)；child.parent=94 ✓
- `95` (commit) → `1251` (chain_end)；child.parent=95 ✓

- L5 真实见证：`95` kind=commit outcome=errant_commit oracle_diff=—

### fault 160

主链每一条边均验证为直接 parent：

- `954` (fault_applied) → `955` (carrier_state)；child.parent=954 ✓
- `955` (carrier_state) → `956` (operand_read)；child.parent=955 ✓
- `956` (operand_read) → `957` (execute)；child.parent=956 ✓
- `957` (execute) → `958` (prf_writeback)；child.parent=957 ✓
- `958` (prf_writeback) → `959` (commit)；child.parent=958 ✓
- `959` (commit) → `1395` (chain_end)；child.parent=959 ✓

- L5 真实见证：`959` kind=commit outcome=errant_commit oracle_diff=—

### fault 161

主链每一条边均验证为直接 parent：

- `960` (fault_applied) → `961` (carrier_state)；child.parent=960 ✓
- `961` (carrier_state) → `962` (operand_read)；child.parent=961 ✓
- `962` (operand_read) → `963` (execute)；child.parent=962 ✓
- `963` (execute) → `964` (prf_writeback)；child.parent=963 ✓
- `964` (prf_writeback) → `965` (commit)；child.parent=964 ✓
- `965` (commit) → `1396` (chain_end)；child.parent=965 ✓

- L5 真实见证：`965` kind=commit outcome=errant_commit oracle_diff=—

### fault 162

主链每一条边均验证为直接 parent：

- `966` (fault_applied) → `967` (carrier_state)；child.parent=966 ✓
- `967` (carrier_state) → `968` (operand_read)；child.parent=967 ✓
- `968` (operand_read) → `969` (execute)；child.parent=968 ✓
- `969` (execute) → `970` (prf_writeback)；child.parent=969 ✓
- `970` (prf_writeback) → `971` (commit)；child.parent=970 ✓
- `971` (commit) → `1397` (chain_end)；child.parent=971 ✓

- L5 真实见证：`971` kind=commit outcome=errant_commit oracle_diff=—

### fault 163

主链每一条边均验证为直接 parent：

- `972` (fault_applied) → `973` (carrier_state)；child.parent=972 ✓
- `973` (carrier_state) → `974` (operand_read)；child.parent=973 ✓
- `974` (operand_read) → `975` (execute)；child.parent=974 ✓
- `975` (execute) → `976` (prf_writeback)；child.parent=975 ✓
- `976` (prf_writeback) → `977` (commit)；child.parent=976 ✓
- `977` (commit) → `1398` (chain_end)；child.parent=977 ✓

- L5 真实见证：`977` kind=commit outcome=errant_commit oracle_diff=—

### fault 164

主链每一条边均验证为直接 parent：

- `978` (fault_applied) → `979` (carrier_state)；child.parent=978 ✓
- `979` (carrier_state) → `980` (operand_read)；child.parent=979 ✓
- `980` (operand_read) → `981` (execute)；child.parent=980 ✓
- `981` (execute) → `982` (prf_writeback)；child.parent=981 ✓
- `982` (prf_writeback) → `983` (commit)；child.parent=982 ✓
- `983` (commit) → `1399` (chain_end)；child.parent=983 ✓

- L5 真实见证：`983` kind=commit outcome=errant_commit oracle_diff=—

### fault 165

主链每一条边均验证为直接 parent：

- `984` (fault_applied) → `985` (carrier_state)；child.parent=984 ✓
- `985` (carrier_state) → `986` (operand_read)；child.parent=985 ✓
- `986` (operand_read) → `987` (execute)；child.parent=986 ✓
- `987` (execute) → `988` (prf_writeback)；child.parent=987 ✓
- `988` (prf_writeback) → `989` (commit)；child.parent=988 ✓
- `989` (commit) → `1400` (chain_end)；child.parent=989 ✓

- L5 真实见证：`989` kind=commit outcome=errant_commit oracle_diff=—

### fault 166

主链每一条边均验证为直接 parent：

- `990` (fault_applied) → `991` (carrier_state)；child.parent=990 ✓
- `991` (carrier_state) → `992` (operand_read)；child.parent=991 ✓
- `992` (operand_read) → `993` (execute)；child.parent=992 ✓
- `993` (execute) → `994` (prf_writeback)；child.parent=993 ✓
- `994` (prf_writeback) → `995` (commit)；child.parent=994 ✓
- `995` (commit) → `1401` (chain_end)；child.parent=995 ✓

- L5 真实见证：`995` kind=commit outcome=errant_commit oracle_diff=—

### fault 167

主链每一条边均验证为直接 parent：

- `996` (fault_applied) → `997` (carrier_state)；child.parent=996 ✓
- `997` (carrier_state) → `998` (operand_read)；child.parent=997 ✓
- `998` (operand_read) → `999` (execute)；child.parent=998 ✓
- `999` (execute) → `1000` (prf_writeback)；child.parent=999 ✓
- `1000` (prf_writeback) → `1001` (commit)；child.parent=1000 ✓
- `1001` (commit) → `1402` (chain_end)；child.parent=1001 ✓

- L5 真实见证：`1001` kind=commit outcome=errant_commit oracle_diff=—

### fault 168

主链每一条边均验证为直接 parent：

- `1002` (fault_applied) → `1003` (carrier_state)；child.parent=1002 ✓
- `1003` (carrier_state) → `1004` (operand_read)；child.parent=1003 ✓
- `1004` (operand_read) → `1005` (execute)；child.parent=1004 ✓
- `1005` (execute) → `1006` (prf_writeback)；child.parent=1005 ✓
- `1006` (prf_writeback) → `1007` (commit)；child.parent=1006 ✓
- `1007` (commit) → `1403` (chain_end)；child.parent=1007 ✓

- L5 真实见证：`1007` kind=commit outcome=errant_commit oracle_diff=—

### fault 169

主链每一条边均验证为直接 parent：

- `1008` (fault_applied) → `1009` (carrier_state)；child.parent=1008 ✓
- `1009` (carrier_state) → `1010` (operand_read)；child.parent=1009 ✓
- `1010` (operand_read) → `1011` (execute)；child.parent=1010 ✓
- `1011` (execute) → `1012` (prf_writeback)；child.parent=1011 ✓
- `1012` (prf_writeback) → `1013` (commit)；child.parent=1012 ✓
- `1013` (commit) → `1404` (chain_end)；child.parent=1013 ✓

- L5 真实见证：`1013` kind=commit outcome=errant_commit oracle_diff=—

### fault 17

主链每一条边均验证为直接 parent：

- `96` (fault_applied) → `97` (carrier_state)；child.parent=96 ✓
- `97` (carrier_state) → `98` (operand_read)；child.parent=97 ✓
- `98` (operand_read) → `99` (execute)；child.parent=98 ✓
- `99` (execute) → `100` (prf_writeback)；child.parent=99 ✓
- `100` (prf_writeback) → `101` (commit)；child.parent=100 ✓
- `101` (commit) → `1252` (chain_end)；child.parent=101 ✓

- L5 真实见证：`101` kind=commit outcome=errant_commit oracle_diff=—

### fault 170

主链每一条边均验证为直接 parent：

- `1014` (fault_applied) → `1015` (carrier_state)；child.parent=1014 ✓
- `1015` (carrier_state) → `1016` (operand_read)；child.parent=1015 ✓
- `1016` (operand_read) → `1017` (execute)；child.parent=1016 ✓
- `1017` (execute) → `1018` (prf_writeback)；child.parent=1017 ✓
- `1018` (prf_writeback) → `1019` (commit)；child.parent=1018 ✓
- `1019` (commit) → `1405` (chain_end)；child.parent=1019 ✓

- L5 真实见证：`1019` kind=commit outcome=errant_commit oracle_diff=—

### fault 171

主链每一条边均验证为直接 parent：

- `1020` (fault_applied) → `1021` (carrier_state)；child.parent=1020 ✓
- `1021` (carrier_state) → `1022` (operand_read)；child.parent=1021 ✓
- `1022` (operand_read) → `1023` (execute)；child.parent=1022 ✓
- `1023` (execute) → `1024` (prf_writeback)；child.parent=1023 ✓
- `1024` (prf_writeback) → `1025` (commit)；child.parent=1024 ✓
- `1025` (commit) → `1406` (chain_end)；child.parent=1025 ✓

- L5 真实见证：`1025` kind=commit outcome=errant_commit oracle_diff=—

### fault 172

主链每一条边均验证为直接 parent：

- `1026` (fault_applied) → `1027` (carrier_state)；child.parent=1026 ✓
- `1027` (carrier_state) → `1028` (operand_read)；child.parent=1027 ✓
- `1028` (operand_read) → `1029` (execute)；child.parent=1028 ✓
- `1029` (execute) → `1030` (prf_writeback)；child.parent=1029 ✓
- `1030` (prf_writeback) → `1031` (commit)；child.parent=1030 ✓
- `1031` (commit) → `1407` (chain_end)；child.parent=1031 ✓

- L5 真实见证：`1031` kind=commit outcome=errant_commit oracle_diff=—

### fault 173

主链每一条边均验证为直接 parent：

- `1032` (fault_applied) → `1033` (carrier_state)；child.parent=1032 ✓
- `1033` (carrier_state) → `1034` (operand_read)；child.parent=1033 ✓
- `1034` (operand_read) → `1035` (execute)；child.parent=1034 ✓
- `1035` (execute) → `1036` (prf_writeback)；child.parent=1035 ✓
- `1036` (prf_writeback) → `1037` (commit)；child.parent=1036 ✓
- `1037` (commit) → `1408` (chain_end)；child.parent=1037 ✓

- L5 真实见证：`1037` kind=commit outcome=errant_commit oracle_diff=—

### fault 174

主链每一条边均验证为直接 parent：

- `1038` (fault_applied) → `1039` (carrier_state)；child.parent=1038 ✓
- `1039` (carrier_state) → `1040` (operand_read)；child.parent=1039 ✓
- `1040` (operand_read) → `1041` (execute)；child.parent=1040 ✓
- `1041` (execute) → `1042` (prf_writeback)；child.parent=1041 ✓
- `1042` (prf_writeback) → `1043` (commit)；child.parent=1042 ✓
- `1043` (commit) → `1409` (chain_end)；child.parent=1043 ✓

- L5 真实见证：`1043` kind=commit outcome=errant_commit oracle_diff=—

### fault 175

主链每一条边均验证为直接 parent：

- `1044` (fault_applied) → `1045` (carrier_state)；child.parent=1044 ✓
- `1045` (carrier_state) → `1046` (operand_read)；child.parent=1045 ✓
- `1046` (operand_read) → `1047` (execute)；child.parent=1046 ✓
- `1047` (execute) → `1048` (prf_writeback)；child.parent=1047 ✓
- `1048` (prf_writeback) → `1049` (commit)；child.parent=1048 ✓
- `1049` (commit) → `1410` (chain_end)；child.parent=1049 ✓

- L5 真实见证：`1049` kind=commit outcome=errant_commit oracle_diff=—

### fault 176

主链每一条边均验证为直接 parent：

- `1050` (fault_applied) → `1051` (carrier_state)；child.parent=1050 ✓
- `1051` (carrier_state) → `1052` (operand_read)；child.parent=1051 ✓
- `1052` (operand_read) → `1053` (execute)；child.parent=1052 ✓
- `1053` (execute) → `1054` (prf_writeback)；child.parent=1053 ✓
- `1054` (prf_writeback) → `1055` (commit)；child.parent=1054 ✓
- `1055` (commit) → `1411` (chain_end)；child.parent=1055 ✓

- L5 真实见证：`1055` kind=commit outcome=errant_commit oracle_diff=—

### fault 177

主链每一条边均验证为直接 parent：

- `1056` (fault_applied) → `1057` (carrier_state)；child.parent=1056 ✓
- `1057` (carrier_state) → `1058` (operand_read)；child.parent=1057 ✓
- `1058` (operand_read) → `1059` (execute)；child.parent=1058 ✓
- `1059` (execute) → `1060` (prf_writeback)；child.parent=1059 ✓
- `1060` (prf_writeback) → `1061` (commit)；child.parent=1060 ✓
- `1061` (commit) → `1412` (chain_end)；child.parent=1061 ✓

- L5 真实见证：`1061` kind=commit outcome=errant_commit oracle_diff=—

### fault 178

主链每一条边均验证为直接 parent：

- `1062` (fault_applied) → `1063` (carrier_state)；child.parent=1062 ✓
- `1063` (carrier_state) → `1064` (operand_read)；child.parent=1063 ✓
- `1064` (operand_read) → `1065` (execute)；child.parent=1064 ✓
- `1065` (execute) → `1066` (prf_writeback)；child.parent=1065 ✓
- `1066` (prf_writeback) → `1067` (commit)；child.parent=1066 ✓
- `1067` (commit) → `1413` (chain_end)；child.parent=1067 ✓

- L5 真实见证：`1067` kind=commit outcome=errant_commit oracle_diff=—

### fault 179

主链每一条边均验证为直接 parent：

- `1068` (fault_applied) → `1069` (carrier_state)；child.parent=1068 ✓
- `1069` (carrier_state) → `1070` (operand_read)；child.parent=1069 ✓
- `1070` (operand_read) → `1071` (execute)；child.parent=1070 ✓
- `1071` (execute) → `1072` (prf_writeback)；child.parent=1071 ✓
- `1072` (prf_writeback) → `1073` (commit)；child.parent=1072 ✓
- `1073` (commit) → `1414` (chain_end)；child.parent=1073 ✓

- L5 真实见证：`1073` kind=commit outcome=errant_commit oracle_diff=—

### fault 18

主链每一条边均验证为直接 parent：

- `102` (fault_applied) → `103` (carrier_state)；child.parent=102 ✓
- `103` (carrier_state) → `104` (operand_read)；child.parent=103 ✓
- `104` (operand_read) → `105` (execute)；child.parent=104 ✓
- `105` (execute) → `106` (prf_writeback)；child.parent=105 ✓
- `106` (prf_writeback) → `107` (commit)；child.parent=106 ✓
- `107` (commit) → `1253` (chain_end)；child.parent=107 ✓

- L5 真实见证：`107` kind=commit outcome=errant_commit oracle_diff=—

### fault 180

主链每一条边均验证为直接 parent：

- `1074` (fault_applied) → `1075` (carrier_state)；child.parent=1074 ✓
- `1075` (carrier_state) → `1076` (operand_read)；child.parent=1075 ✓
- `1076` (operand_read) → `1077` (execute)；child.parent=1076 ✓
- `1077` (execute) → `1078` (prf_writeback)；child.parent=1077 ✓
- `1078` (prf_writeback) → `1079` (commit)；child.parent=1078 ✓
- `1079` (commit) → `1415` (chain_end)；child.parent=1079 ✓

- L5 真实见证：`1079` kind=commit outcome=errant_commit oracle_diff=—

### fault 181

主链每一条边均验证为直接 parent：

- `1080` (fault_applied) → `1081` (carrier_state)；child.parent=1080 ✓
- `1081` (carrier_state) → `1082` (operand_read)；child.parent=1081 ✓
- `1082` (operand_read) → `1083` (execute)；child.parent=1082 ✓
- `1083` (execute) → `1084` (prf_writeback)；child.parent=1083 ✓
- `1084` (prf_writeback) → `1085` (commit)；child.parent=1084 ✓
- `1085` (commit) → `1416` (chain_end)；child.parent=1085 ✓

- L5 真实见证：`1085` kind=commit outcome=errant_commit oracle_diff=—

### fault 182

主链每一条边均验证为直接 parent：

- `1086` (fault_applied) → `1087` (carrier_state)；child.parent=1086 ✓
- `1087` (carrier_state) → `1088` (operand_read)；child.parent=1087 ✓
- `1088` (operand_read) → `1089` (execute)；child.parent=1088 ✓
- `1089` (execute) → `1090` (prf_writeback)；child.parent=1089 ✓
- `1090` (prf_writeback) → `1091` (commit)；child.parent=1090 ✓
- `1091` (commit) → `1417` (chain_end)；child.parent=1091 ✓

- L5 真实见证：`1091` kind=commit outcome=errant_commit oracle_diff=—

### fault 183

主链每一条边均验证为直接 parent：

- `1092` (fault_applied) → `1093` (carrier_state)；child.parent=1092 ✓
- `1093` (carrier_state) → `1094` (operand_read)；child.parent=1093 ✓
- `1094` (operand_read) → `1095` (execute)；child.parent=1094 ✓
- `1095` (execute) → `1096` (prf_writeback)；child.parent=1095 ✓
- `1096` (prf_writeback) → `1097` (commit)；child.parent=1096 ✓
- `1097` (commit) → `1418` (chain_end)；child.parent=1097 ✓

- L5 真实见证：`1097` kind=commit outcome=errant_commit oracle_diff=—

### fault 184

主链每一条边均验证为直接 parent：

- `1098` (fault_applied) → `1099` (carrier_state)；child.parent=1098 ✓
- `1099` (carrier_state) → `1100` (operand_read)；child.parent=1099 ✓
- `1100` (operand_read) → `1101` (execute)；child.parent=1100 ✓
- `1101` (execute) → `1102` (prf_writeback)；child.parent=1101 ✓
- `1102` (prf_writeback) → `1103` (commit)；child.parent=1102 ✓
- `1103` (commit) → `1419` (chain_end)；child.parent=1103 ✓

- L5 真实见证：`1103` kind=commit outcome=errant_commit oracle_diff=—

### fault 185

主链每一条边均验证为直接 parent：

- `1104` (fault_applied) → `1105` (carrier_state)；child.parent=1104 ✓
- `1105` (carrier_state) → `1106` (operand_read)；child.parent=1105 ✓
- `1106` (operand_read) → `1107` (execute)；child.parent=1106 ✓
- `1107` (execute) → `1108` (prf_writeback)；child.parent=1107 ✓
- `1108` (prf_writeback) → `1109` (commit)；child.parent=1108 ✓
- `1109` (commit) → `1420` (chain_end)；child.parent=1109 ✓

- L5 真实见证：`1109` kind=commit outcome=errant_commit oracle_diff=—

### fault 186

主链每一条边均验证为直接 parent：

- `1110` (fault_applied) → `1111` (carrier_state)；child.parent=1110 ✓
- `1111` (carrier_state) → `1112` (operand_read)；child.parent=1111 ✓
- `1112` (operand_read) → `1113` (execute)；child.parent=1112 ✓
- `1113` (execute) → `1114` (prf_writeback)；child.parent=1113 ✓
- `1114` (prf_writeback) → `1115` (commit)；child.parent=1114 ✓
- `1115` (commit) → `1421` (chain_end)；child.parent=1115 ✓

- L5 真实见证：`1115` kind=commit outcome=errant_commit oracle_diff=—

### fault 187

主链每一条边均验证为直接 parent：

- `1116` (fault_applied) → `1117` (carrier_state)；child.parent=1116 ✓
- `1117` (carrier_state) → `1118` (operand_read)；child.parent=1117 ✓
- `1118` (operand_read) → `1119` (execute)；child.parent=1118 ✓
- `1119` (execute) → `1120` (prf_writeback)；child.parent=1119 ✓
- `1120` (prf_writeback) → `1121` (commit)；child.parent=1120 ✓
- `1121` (commit) → `1422` (chain_end)；child.parent=1121 ✓

- L5 真实见证：`1121` kind=commit outcome=errant_commit oracle_diff=—

### fault 188

主链每一条边均验证为直接 parent：

- `1122` (fault_applied) → `1123` (carrier_state)；child.parent=1122 ✓
- `1123` (carrier_state) → `1124` (operand_read)；child.parent=1123 ✓
- `1124` (operand_read) → `1125` (execute)；child.parent=1124 ✓
- `1125` (execute) → `1126` (prf_writeback)；child.parent=1125 ✓
- `1126` (prf_writeback) → `1127` (commit)；child.parent=1126 ✓
- `1127` (commit) → `1423` (chain_end)；child.parent=1127 ✓

- L5 真实见证：`1127` kind=commit outcome=errant_commit oracle_diff=—

### fault 189

主链每一条边均验证为直接 parent：

- `1128` (fault_applied) → `1129` (carrier_state)；child.parent=1128 ✓
- `1129` (carrier_state) → `1130` (operand_read)；child.parent=1129 ✓
- `1130` (operand_read) → `1131` (execute)；child.parent=1130 ✓
- `1131` (execute) → `1132` (prf_writeback)；child.parent=1131 ✓
- `1132` (prf_writeback) → `1133` (commit)；child.parent=1132 ✓
- `1133` (commit) → `1424` (chain_end)；child.parent=1133 ✓

- L5 真实见证：`1133` kind=commit outcome=errant_commit oracle_diff=—

### fault 19

主链每一条边均验证为直接 parent：

- `108` (fault_applied) → `109` (carrier_state)；child.parent=108 ✓
- `109` (carrier_state) → `110` (operand_read)；child.parent=109 ✓
- `110` (operand_read) → `111` (execute)；child.parent=110 ✓
- `111` (execute) → `112` (prf_writeback)；child.parent=111 ✓
- `112` (prf_writeback) → `113` (commit)；child.parent=112 ✓
- `113` (commit) → `1254` (chain_end)；child.parent=113 ✓

- L5 真实见证：`113` kind=commit outcome=errant_commit oracle_diff=—

### fault 190

主链每一条边均验证为直接 parent：

- `1134` (fault_applied) → `1135` (carrier_state)；child.parent=1134 ✓
- `1135` (carrier_state) → `1136` (operand_read)；child.parent=1135 ✓
- `1136` (operand_read) → `1137` (execute)；child.parent=1136 ✓
- `1137` (execute) → `1138` (prf_writeback)；child.parent=1137 ✓
- `1138` (prf_writeback) → `1139` (commit)；child.parent=1138 ✓
- `1139` (commit) → `1425` (chain_end)；child.parent=1139 ✓

- L5 真实见证：`1139` kind=commit outcome=errant_commit oracle_diff=—

### fault 191

主链每一条边均验证为直接 parent：

- `1140` (fault_applied) → `1141` (carrier_state)；child.parent=1140 ✓
- `1141` (carrier_state) → `1142` (operand_read)；child.parent=1141 ✓
- `1142` (operand_read) → `1143` (execute)；child.parent=1142 ✓
- `1143` (execute) → `1144` (prf_writeback)；child.parent=1143 ✓
- `1144` (prf_writeback) → `1145` (commit)；child.parent=1144 ✓
- `1145` (commit) → `1426` (chain_end)；child.parent=1145 ✓

- L5 真实见证：`1145` kind=commit outcome=errant_commit oracle_diff=—

### fault 192

主链每一条边均验证为直接 parent：

- `1146` (fault_applied) → `1147` (carrier_state)；child.parent=1146 ✓
- `1147` (carrier_state) → `1148` (operand_read)；child.parent=1147 ✓
- `1148` (operand_read) → `1149` (execute)；child.parent=1148 ✓
- `1149` (execute) → `1150` (prf_writeback)；child.parent=1149 ✓
- `1150` (prf_writeback) → `1151` (commit)；child.parent=1150 ✓
- `1151` (commit) → `1427` (chain_end)；child.parent=1151 ✓

- L5 真实见证：`1151` kind=commit outcome=errant_commit oracle_diff=—

### fault 193

主链每一条边均验证为直接 parent：

- `1152` (fault_applied) → `1153` (carrier_state)；child.parent=1152 ✓
- `1153` (carrier_state) → `1154` (operand_read)；child.parent=1153 ✓
- `1154` (operand_read) → `1155` (execute)；child.parent=1154 ✓
- `1155` (execute) → `1156` (prf_writeback)；child.parent=1155 ✓
- `1156` (prf_writeback) → `1157` (commit)；child.parent=1156 ✓
- `1157` (commit) → `1428` (chain_end)；child.parent=1157 ✓

- L5 真实见证：`1157` kind=commit outcome=errant_commit oracle_diff=—

### fault 194

主链每一条边均验证为直接 parent：

- `1158` (fault_applied) → `1159` (carrier_state)；child.parent=1158 ✓
- `1159` (carrier_state) → `1160` (operand_read)；child.parent=1159 ✓
- `1160` (operand_read) → `1161` (execute)；child.parent=1160 ✓
- `1161` (execute) → `1162` (prf_writeback)；child.parent=1161 ✓
- `1162` (prf_writeback) → `1163` (commit)；child.parent=1162 ✓
- `1163` (commit) → `1429` (chain_end)；child.parent=1163 ✓

- L5 真实见证：`1163` kind=commit outcome=errant_commit oracle_diff=—

### fault 195

主链每一条边均验证为直接 parent：

- `1164` (fault_applied) → `1165` (carrier_state)；child.parent=1164 ✓
- `1165` (carrier_state) → `1166` (operand_read)；child.parent=1165 ✓
- `1166` (operand_read) → `1167` (execute)；child.parent=1166 ✓
- `1167` (execute) → `1168` (prf_writeback)；child.parent=1167 ✓
- `1168` (prf_writeback) → `1169` (commit)；child.parent=1168 ✓
- `1169` (commit) → `1430` (chain_end)；child.parent=1169 ✓

- L5 真实见证：`1169` kind=commit outcome=errant_commit oracle_diff=—

### fault 196

主链每一条边均验证为直接 parent：

- `1170` (fault_applied) → `1171` (carrier_state)；child.parent=1170 ✓
- `1171` (carrier_state) → `1172` (operand_read)；child.parent=1171 ✓
- `1172` (operand_read) → `1173` (execute)；child.parent=1172 ✓
- `1173` (execute) → `1174` (prf_writeback)；child.parent=1173 ✓
- `1174` (prf_writeback) → `1175` (commit)；child.parent=1174 ✓
- `1175` (commit) → `1431` (chain_end)；child.parent=1175 ✓

- L5 真实见证：`1175` kind=commit outcome=errant_commit oracle_diff=—

### fault 197

主链每一条边均验证为直接 parent：

- `1176` (fault_applied) → `1177` (carrier_state)；child.parent=1176 ✓
- `1177` (carrier_state) → `1178` (operand_read)；child.parent=1177 ✓
- `1178` (operand_read) → `1179` (execute)；child.parent=1178 ✓
- `1179` (execute) → `1180` (prf_writeback)；child.parent=1179 ✓
- `1180` (prf_writeback) → `1181` (commit)；child.parent=1180 ✓
- `1181` (commit) → `1432` (chain_end)；child.parent=1181 ✓

- L5 真实见证：`1181` kind=commit outcome=errant_commit oracle_diff=—

### fault 198

主链每一条边均验证为直接 parent：

- `1182` (fault_applied) → `1183` (carrier_state)；child.parent=1182 ✓
- `1183` (carrier_state) → `1184` (operand_read)；child.parent=1183 ✓
- `1184` (operand_read) → `1185` (execute)；child.parent=1184 ✓
- `1185` (execute) → `1186` (prf_writeback)；child.parent=1185 ✓
- `1186` (prf_writeback) → `1187` (commit)；child.parent=1186 ✓
- `1187` (commit) → `1433` (chain_end)；child.parent=1187 ✓

- L5 真实见证：`1187` kind=commit outcome=errant_commit oracle_diff=—

### fault 199

主链每一条边均验证为直接 parent：

- `1188` (fault_applied) → `1189` (carrier_state)；child.parent=1188 ✓
- `1189` (carrier_state) → `1190` (operand_read)；child.parent=1189 ✓
- `1190` (operand_read) → `1191` (execute)；child.parent=1190 ✓
- `1191` (execute) → `1192` (prf_writeback)；child.parent=1191 ✓
- `1192` (prf_writeback) → `1193` (commit)；child.parent=1192 ✓
- `1193` (commit) → `1434` (chain_end)；child.parent=1193 ✓

- L5 真实见证：`1193` kind=commit outcome=errant_commit oracle_diff=—

### fault 2

主链每一条边均验证为直接 parent：

- `6` (fault_applied) → `7` (carrier_state)；child.parent=6 ✓
- `7` (carrier_state) → `8` (operand_read)；child.parent=7 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `1237` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

### fault 20

主链每一条边均验证为直接 parent：

- `114` (fault_applied) → `115` (carrier_state)；child.parent=114 ✓
- `115` (carrier_state) → `116` (operand_read)；child.parent=115 ✓
- `116` (operand_read) → `117` (execute)；child.parent=116 ✓
- `117` (execute) → `118` (prf_writeback)；child.parent=117 ✓
- `118` (prf_writeback) → `119` (commit)；child.parent=118 ✓
- `119` (commit) → `1255` (chain_end)；child.parent=119 ✓

- L5 真实见证：`119` kind=commit outcome=errant_commit oracle_diff=—

### fault 200

主链每一条边均验证为直接 parent：

- `1194` (fault_applied) → `1195` (carrier_state)；child.parent=1194 ✓
- `1195` (carrier_state) → `1196` (operand_read)；child.parent=1195 ✓
- `1196` (operand_read) → `1197` (execute)；child.parent=1196 ✓
- `1197` (execute) → `1198` (prf_writeback)；child.parent=1197 ✓
- `1198` (prf_writeback) → `1199` (commit)；child.parent=1198 ✓
- `1199` (commit) → `1435` (chain_end)；child.parent=1199 ✓

- L5 真实见证：`1199` kind=commit outcome=errant_commit oracle_diff=—

### fault 201

主链每一条边均验证为直接 parent：

- `1200` (fault_applied) → `1201` (carrier_state)；child.parent=1200 ✓
- `1201` (carrier_state) → `1202` (operand_read)；child.parent=1201 ✓
- `1202` (operand_read) → `1203` (execute)；child.parent=1202 ✓
- `1203` (execute) → `1204` (prf_writeback)；child.parent=1203 ✓
- `1204` (prf_writeback) → `1205` (commit)；child.parent=1204 ✓
- `1205` (commit) → `1436` (chain_end)；child.parent=1205 ✓

- L5 真实见证：`1205` kind=commit outcome=errant_commit oracle_diff=—

### fault 202

主链每一条边均验证为直接 parent：

- `1206` (fault_applied) → `1207` (carrier_state)；child.parent=1206 ✓
- `1207` (carrier_state) → `1208` (operand_read)；child.parent=1207 ✓
- `1208` (operand_read) → `1209` (execute)；child.parent=1208 ✓
- `1209` (execute) → `1210` (prf_writeback)；child.parent=1209 ✓
- `1210` (prf_writeback) → `1211` (commit)；child.parent=1210 ✓
- `1211` (commit) → `1437` (chain_end)；child.parent=1211 ✓

- L5 真实见证：`1211` kind=commit outcome=errant_commit oracle_diff=—

### fault 203

主链每一条边均验证为直接 parent：

- `1212` (fault_applied) → `1213` (carrier_state)；child.parent=1212 ✓
- `1213` (carrier_state) → `1214` (operand_read)；child.parent=1213 ✓
- `1214` (operand_read) → `1215` (execute)；child.parent=1214 ✓
- `1215` (execute) → `1216` (prf_writeback)；child.parent=1215 ✓
- `1216` (prf_writeback) → `1217` (commit)；child.parent=1216 ✓
- `1217` (commit) → `1438` (chain_end)；child.parent=1217 ✓

- L5 真实见证：`1217` kind=commit outcome=errant_commit oracle_diff=—

### fault 204

主链每一条边均验证为直接 parent：

- `1218` (fault_applied) → `1219` (carrier_state)；child.parent=1218 ✓
- `1219` (carrier_state) → `1220` (operand_read)；child.parent=1219 ✓
- `1220` (operand_read) → `1221` (execute)；child.parent=1220 ✓
- `1221` (execute) → `1222` (prf_writeback)；child.parent=1221 ✓
- `1222` (prf_writeback) → `1223` (commit)；child.parent=1222 ✓
- `1223` (commit) → `1439` (chain_end)；child.parent=1223 ✓

- L5 真实见证：`1223` kind=commit outcome=errant_commit oracle_diff=—

### fault 205

主链每一条边均验证为直接 parent：

- `1224` (fault_applied) → `1225` (carrier_state)；child.parent=1224 ✓
- `1225` (carrier_state) → `1226` (operand_read)；child.parent=1225 ✓
- `1226` (operand_read) → `1227` (execute)；child.parent=1226 ✓
- `1227` (execute) → `1228` (prf_writeback)；child.parent=1227 ✓
- `1228` (prf_writeback) → `1229` (commit)；child.parent=1228 ✓
- `1229` (commit) → `1440` (chain_end)；child.parent=1229 ✓

- L5 真实见证：`1229` kind=commit outcome=errant_commit oracle_diff=—

### fault 206

主链每一条边均验证为直接 parent：

- `1230` (fault_applied) → `1231` (carrier_state)；child.parent=1230 ✓
- `1231` (carrier_state) → `1232` (operand_read)；child.parent=1231 ✓
- `1232` (operand_read) → `1233` (execute)；child.parent=1232 ✓
- `1233` (execute) → `1234` (prf_writeback)；child.parent=1233 ✓
- `1234` (prf_writeback) → `1235` (commit)；child.parent=1234 ✓
- `1235` (commit) → `1441` (chain_end)；child.parent=1235 ✓

- L5 真实见证：`1235` kind=commit outcome=errant_commit oracle_diff=—

### fault 21

主链每一条边均验证为直接 parent：

- `120` (fault_applied) → `121` (carrier_state)；child.parent=120 ✓
- `121` (carrier_state) → `122` (operand_read)；child.parent=121 ✓
- `122` (operand_read) → `123` (execute)；child.parent=122 ✓
- `123` (execute) → `124` (prf_writeback)；child.parent=123 ✓
- `124` (prf_writeback) → `125` (commit)；child.parent=124 ✓
- `125` (commit) → `1256` (chain_end)；child.parent=125 ✓

- L5 真实见证：`125` kind=commit outcome=errant_commit oracle_diff=—

### fault 22

主链每一条边均验证为直接 parent：

- `126` (fault_applied) → `127` (carrier_state)；child.parent=126 ✓
- `127` (carrier_state) → `128` (operand_read)；child.parent=127 ✓
- `128` (operand_read) → `129` (execute)；child.parent=128 ✓
- `129` (execute) → `130` (prf_writeback)；child.parent=129 ✓
- `130` (prf_writeback) → `131` (commit)；child.parent=130 ✓
- `131` (commit) → `1257` (chain_end)；child.parent=131 ✓

- L5 真实见证：`131` kind=commit outcome=errant_commit oracle_diff=—

### fault 23

主链每一条边均验证为直接 parent：

- `132` (fault_applied) → `133` (carrier_state)；child.parent=132 ✓
- `133` (carrier_state) → `134` (operand_read)；child.parent=133 ✓
- `134` (operand_read) → `135` (execute)；child.parent=134 ✓
- `135` (execute) → `136` (prf_writeback)；child.parent=135 ✓
- `136` (prf_writeback) → `137` (commit)；child.parent=136 ✓
- `137` (commit) → `1258` (chain_end)；child.parent=137 ✓

- L5 真实见证：`137` kind=commit outcome=errant_commit oracle_diff=—

### fault 24

主链每一条边均验证为直接 parent：

- `138` (fault_applied) → `139` (carrier_state)；child.parent=138 ✓
- `139` (carrier_state) → `140` (operand_read)；child.parent=139 ✓
- `140` (operand_read) → `141` (execute)；child.parent=140 ✓
- `141` (execute) → `142` (prf_writeback)；child.parent=141 ✓
- `142` (prf_writeback) → `143` (commit)；child.parent=142 ✓
- `143` (commit) → `1259` (chain_end)；child.parent=143 ✓

- L5 真实见证：`143` kind=commit outcome=errant_commit oracle_diff=—

### fault 25

主链每一条边均验证为直接 parent：

- `144` (fault_applied) → `145` (carrier_state)；child.parent=144 ✓
- `145` (carrier_state) → `146` (operand_read)；child.parent=145 ✓
- `146` (operand_read) → `147` (execute)；child.parent=146 ✓
- `147` (execute) → `148` (prf_writeback)；child.parent=147 ✓
- `148` (prf_writeback) → `149` (commit)；child.parent=148 ✓
- `149` (commit) → `1260` (chain_end)；child.parent=149 ✓

- L5 真实见证：`149` kind=commit outcome=errant_commit oracle_diff=—

### fault 26

主链每一条边均验证为直接 parent：

- `150` (fault_applied) → `151` (carrier_state)；child.parent=150 ✓
- `151` (carrier_state) → `152` (operand_read)；child.parent=151 ✓
- `152` (operand_read) → `153` (execute)；child.parent=152 ✓
- `153` (execute) → `154` (prf_writeback)；child.parent=153 ✓
- `154` (prf_writeback) → `155` (commit)；child.parent=154 ✓
- `155` (commit) → `1261` (chain_end)；child.parent=155 ✓

- L5 真实见证：`155` kind=commit outcome=errant_commit oracle_diff=—

### fault 27

主链每一条边均验证为直接 parent：

- `156` (fault_applied) → `157` (carrier_state)；child.parent=156 ✓
- `157` (carrier_state) → `158` (operand_read)；child.parent=157 ✓
- `158` (operand_read) → `159` (execute)；child.parent=158 ✓
- `159` (execute) → `160` (prf_writeback)；child.parent=159 ✓
- `160` (prf_writeback) → `161` (commit)；child.parent=160 ✓
- `161` (commit) → `1262` (chain_end)；child.parent=161 ✓

- L5 真实见证：`161` kind=commit outcome=errant_commit oracle_diff=—

### fault 28

主链每一条边均验证为直接 parent：

- `162` (fault_applied) → `163` (carrier_state)；child.parent=162 ✓
- `163` (carrier_state) → `164` (operand_read)；child.parent=163 ✓
- `164` (operand_read) → `165` (execute)；child.parent=164 ✓
- `165` (execute) → `166` (prf_writeback)；child.parent=165 ✓
- `166` (prf_writeback) → `167` (commit)；child.parent=166 ✓
- `167` (commit) → `1263` (chain_end)；child.parent=167 ✓

- L5 真实见证：`167` kind=commit outcome=errant_commit oracle_diff=—

### fault 29

主链每一条边均验证为直接 parent：

- `168` (fault_applied) → `169` (carrier_state)；child.parent=168 ✓
- `169` (carrier_state) → `170` (operand_read)；child.parent=169 ✓
- `170` (operand_read) → `171` (execute)；child.parent=170 ✓
- `171` (execute) → `172` (prf_writeback)；child.parent=171 ✓
- `172` (prf_writeback) → `173` (commit)；child.parent=172 ✓
- `173` (commit) → `1264` (chain_end)；child.parent=173 ✓

- L5 真实见证：`173` kind=commit outcome=errant_commit oracle_diff=—

### fault 3

主链每一条边均验证为直接 parent：

- `12` (fault_applied) → `13` (carrier_state)；child.parent=12 ✓
- `13` (carrier_state) → `14` (operand_read)；child.parent=13 ✓
- `14` (operand_read) → `15` (execute)；child.parent=14 ✓
- `15` (execute) → `16` (prf_writeback)；child.parent=15 ✓
- `16` (prf_writeback) → `17` (commit)；child.parent=16 ✓
- `17` (commit) → `1238` (chain_end)；child.parent=17 ✓

- L5 真实见证：`17` kind=commit outcome=errant_commit oracle_diff=—

### fault 30

主链每一条边均验证为直接 parent：

- `174` (fault_applied) → `175` (carrier_state)；child.parent=174 ✓
- `175` (carrier_state) → `176` (operand_read)；child.parent=175 ✓
- `176` (operand_read) → `177` (execute)；child.parent=176 ✓
- `177` (execute) → `178` (prf_writeback)；child.parent=177 ✓
- `178` (prf_writeback) → `179` (commit)；child.parent=178 ✓
- `179` (commit) → `1265` (chain_end)；child.parent=179 ✓

- L5 真实见证：`179` kind=commit outcome=errant_commit oracle_diff=—

### fault 31

主链每一条边均验证为直接 parent：

- `180` (fault_applied) → `181` (carrier_state)；child.parent=180 ✓
- `181` (carrier_state) → `182` (operand_read)；child.parent=181 ✓
- `182` (operand_read) → `183` (execute)；child.parent=182 ✓
- `183` (execute) → `184` (prf_writeback)；child.parent=183 ✓
- `184` (prf_writeback) → `185` (commit)；child.parent=184 ✓
- `185` (commit) → `1266` (chain_end)；child.parent=185 ✓

- L5 真实见证：`185` kind=commit outcome=errant_commit oracle_diff=—

### fault 32

主链每一条边均验证为直接 parent：

- `186` (fault_applied) → `187` (carrier_state)；child.parent=186 ✓
- `187` (carrier_state) → `188` (operand_read)；child.parent=187 ✓
- `188` (operand_read) → `189` (execute)；child.parent=188 ✓
- `189` (execute) → `190` (prf_writeback)；child.parent=189 ✓
- `190` (prf_writeback) → `191` (commit)；child.parent=190 ✓
- `191` (commit) → `1267` (chain_end)；child.parent=191 ✓

- L5 真实见证：`191` kind=commit outcome=errant_commit oracle_diff=—

### fault 33

主链每一条边均验证为直接 parent：

- `192` (fault_applied) → `193` (carrier_state)；child.parent=192 ✓
- `193` (carrier_state) → `194` (operand_read)；child.parent=193 ✓
- `194` (operand_read) → `195` (execute)；child.parent=194 ✓
- `195` (execute) → `196` (prf_writeback)；child.parent=195 ✓
- `196` (prf_writeback) → `197` (commit)；child.parent=196 ✓
- `197` (commit) → `1268` (chain_end)；child.parent=197 ✓

- L5 真实见证：`197` kind=commit outcome=errant_commit oracle_diff=—

### fault 34

主链每一条边均验证为直接 parent：

- `198` (fault_applied) → `199` (carrier_state)；child.parent=198 ✓
- `199` (carrier_state) → `200` (operand_read)；child.parent=199 ✓
- `200` (operand_read) → `201` (execute)；child.parent=200 ✓
- `201` (execute) → `202` (prf_writeback)；child.parent=201 ✓
- `202` (prf_writeback) → `203` (commit)；child.parent=202 ✓
- `203` (commit) → `1269` (chain_end)；child.parent=203 ✓

- L5 真实见证：`203` kind=commit outcome=errant_commit oracle_diff=—

### fault 35

主链每一条边均验证为直接 parent：

- `204` (fault_applied) → `205` (carrier_state)；child.parent=204 ✓
- `205` (carrier_state) → `206` (operand_read)；child.parent=205 ✓
- `206` (operand_read) → `207` (execute)；child.parent=206 ✓
- `207` (execute) → `208` (prf_writeback)；child.parent=207 ✓
- `208` (prf_writeback) → `209` (commit)；child.parent=208 ✓
- `209` (commit) → `1270` (chain_end)；child.parent=209 ✓

- L5 真实见证：`209` kind=commit outcome=errant_commit oracle_diff=—

### fault 36

主链每一条边均验证为直接 parent：

- `210` (fault_applied) → `211` (carrier_state)；child.parent=210 ✓
- `211` (carrier_state) → `212` (operand_read)；child.parent=211 ✓
- `212` (operand_read) → `213` (execute)；child.parent=212 ✓
- `213` (execute) → `214` (prf_writeback)；child.parent=213 ✓
- `214` (prf_writeback) → `215` (commit)；child.parent=214 ✓
- `215` (commit) → `1271` (chain_end)；child.parent=215 ✓

- L5 真实见证：`215` kind=commit outcome=errant_commit oracle_diff=—

### fault 37

主链每一条边均验证为直接 parent：

- `216` (fault_applied) → `217` (carrier_state)；child.parent=216 ✓
- `217` (carrier_state) → `218` (operand_read)；child.parent=217 ✓
- `218` (operand_read) → `219` (execute)；child.parent=218 ✓
- `219` (execute) → `220` (prf_writeback)；child.parent=219 ✓
- `220` (prf_writeback) → `221` (commit)；child.parent=220 ✓
- `221` (commit) → `1272` (chain_end)；child.parent=221 ✓

- L5 真实见证：`221` kind=commit outcome=errant_commit oracle_diff=—

### fault 38

主链每一条边均验证为直接 parent：

- `222` (fault_applied) → `223` (carrier_state)；child.parent=222 ✓
- `223` (carrier_state) → `224` (operand_read)；child.parent=223 ✓
- `224` (operand_read) → `225` (execute)；child.parent=224 ✓
- `225` (execute) → `226` (prf_writeback)；child.parent=225 ✓
- `226` (prf_writeback) → `227` (commit)；child.parent=226 ✓
- `227` (commit) → `1273` (chain_end)；child.parent=227 ✓

- L5 真实见证：`227` kind=commit outcome=errant_commit oracle_diff=—

### fault 39

主链每一条边均验证为直接 parent：

- `228` (fault_applied) → `229` (carrier_state)；child.parent=228 ✓
- `229` (carrier_state) → `230` (operand_read)；child.parent=229 ✓
- `230` (operand_read) → `231` (execute)；child.parent=230 ✓
- `231` (execute) → `232` (prf_writeback)；child.parent=231 ✓
- `232` (prf_writeback) → `233` (commit)；child.parent=232 ✓
- `233` (commit) → `1274` (chain_end)；child.parent=233 ✓

- L5 真实见证：`233` kind=commit outcome=errant_commit oracle_diff=—

### fault 4

主链每一条边均验证为直接 parent：

- `18` (fault_applied) → `19` (carrier_state)；child.parent=18 ✓
- `19` (carrier_state) → `20` (operand_read)；child.parent=19 ✓
- `20` (operand_read) → `21` (execute)；child.parent=20 ✓
- `21` (execute) → `22` (prf_writeback)；child.parent=21 ✓
- `22` (prf_writeback) → `23` (commit)；child.parent=22 ✓
- `23` (commit) → `1239` (chain_end)；child.parent=23 ✓

- L5 真实见证：`23` kind=commit outcome=errant_commit oracle_diff=—

### fault 40

主链每一条边均验证为直接 parent：

- `234` (fault_applied) → `235` (carrier_state)；child.parent=234 ✓
- `235` (carrier_state) → `236` (operand_read)；child.parent=235 ✓
- `236` (operand_read) → `237` (execute)；child.parent=236 ✓
- `237` (execute) → `238` (prf_writeback)；child.parent=237 ✓
- `238` (prf_writeback) → `239` (commit)；child.parent=238 ✓
- `239` (commit) → `1275` (chain_end)；child.parent=239 ✓

- L5 真实见证：`239` kind=commit outcome=errant_commit oracle_diff=—

### fault 41

主链每一条边均验证为直接 parent：

- `240` (fault_applied) → `241` (carrier_state)；child.parent=240 ✓
- `241` (carrier_state) → `242` (operand_read)；child.parent=241 ✓
- `242` (operand_read) → `243` (execute)；child.parent=242 ✓
- `243` (execute) → `244` (prf_writeback)；child.parent=243 ✓
- `244` (prf_writeback) → `245` (commit)；child.parent=244 ✓
- `245` (commit) → `1276` (chain_end)；child.parent=245 ✓

- L5 真实见证：`245` kind=commit outcome=errant_commit oracle_diff=—

### fault 42

主链每一条边均验证为直接 parent：

- `246` (fault_applied) → `247` (carrier_state)；child.parent=246 ✓
- `247` (carrier_state) → `248` (operand_read)；child.parent=247 ✓
- `248` (operand_read) → `249` (execute)；child.parent=248 ✓
- `249` (execute) → `250` (prf_writeback)；child.parent=249 ✓
- `250` (prf_writeback) → `251` (commit)；child.parent=250 ✓
- `251` (commit) → `1277` (chain_end)；child.parent=251 ✓

- L5 真实见证：`251` kind=commit outcome=errant_commit oracle_diff=—

### fault 43

主链每一条边均验证为直接 parent：

- `252` (fault_applied) → `253` (carrier_state)；child.parent=252 ✓
- `253` (carrier_state) → `254` (operand_read)；child.parent=253 ✓
- `254` (operand_read) → `255` (execute)；child.parent=254 ✓
- `255` (execute) → `256` (prf_writeback)；child.parent=255 ✓
- `256` (prf_writeback) → `257` (commit)；child.parent=256 ✓
- `257` (commit) → `1278` (chain_end)；child.parent=257 ✓

- L5 真实见证：`257` kind=commit outcome=errant_commit oracle_diff=—

### fault 44

主链每一条边均验证为直接 parent：

- `258` (fault_applied) → `259` (carrier_state)；child.parent=258 ✓
- `259` (carrier_state) → `260` (operand_read)；child.parent=259 ✓
- `260` (operand_read) → `261` (execute)；child.parent=260 ✓
- `261` (execute) → `262` (prf_writeback)；child.parent=261 ✓
- `262` (prf_writeback) → `263` (commit)；child.parent=262 ✓
- `263` (commit) → `1279` (chain_end)；child.parent=263 ✓

- L5 真实见证：`263` kind=commit outcome=errant_commit oracle_diff=—

### fault 45

主链每一条边均验证为直接 parent：

- `264` (fault_applied) → `265` (carrier_state)；child.parent=264 ✓
- `265` (carrier_state) → `266` (operand_read)；child.parent=265 ✓
- `266` (operand_read) → `267` (execute)；child.parent=266 ✓
- `267` (execute) → `268` (prf_writeback)；child.parent=267 ✓
- `268` (prf_writeback) → `269` (commit)；child.parent=268 ✓
- `269` (commit) → `1280` (chain_end)；child.parent=269 ✓

- L5 真实见证：`269` kind=commit outcome=errant_commit oracle_diff=—

### fault 46

主链每一条边均验证为直接 parent：

- `270` (fault_applied) → `271` (carrier_state)；child.parent=270 ✓
- `271` (carrier_state) → `272` (operand_read)；child.parent=271 ✓
- `272` (operand_read) → `273` (execute)；child.parent=272 ✓
- `273` (execute) → `274` (prf_writeback)；child.parent=273 ✓
- `274` (prf_writeback) → `275` (commit)；child.parent=274 ✓
- `275` (commit) → `1281` (chain_end)；child.parent=275 ✓

- L5 真实见证：`275` kind=commit outcome=errant_commit oracle_diff=—

### fault 47

主链每一条边均验证为直接 parent：

- `276` (fault_applied) → `277` (carrier_state)；child.parent=276 ✓
- `277` (carrier_state) → `278` (operand_read)；child.parent=277 ✓
- `278` (operand_read) → `279` (execute)；child.parent=278 ✓
- `279` (execute) → `280` (prf_writeback)；child.parent=279 ✓
- `280` (prf_writeback) → `281` (commit)；child.parent=280 ✓
- `281` (commit) → `1282` (chain_end)；child.parent=281 ✓

- L5 真实见证：`281` kind=commit outcome=errant_commit oracle_diff=—

### fault 48

主链每一条边均验证为直接 parent：

- `282` (fault_applied) → `283` (carrier_state)；child.parent=282 ✓
- `283` (carrier_state) → `284` (operand_read)；child.parent=283 ✓
- `284` (operand_read) → `285` (execute)；child.parent=284 ✓
- `285` (execute) → `286` (prf_writeback)；child.parent=285 ✓
- `286` (prf_writeback) → `287` (commit)；child.parent=286 ✓
- `287` (commit) → `1283` (chain_end)；child.parent=287 ✓

- L5 真实见证：`287` kind=commit outcome=errant_commit oracle_diff=—

### fault 49

主链每一条边均验证为直接 parent：

- `288` (fault_applied) → `289` (carrier_state)；child.parent=288 ✓
- `289` (carrier_state) → `290` (operand_read)；child.parent=289 ✓
- `290` (operand_read) → `291` (execute)；child.parent=290 ✓
- `291` (execute) → `292` (prf_writeback)；child.parent=291 ✓
- `292` (prf_writeback) → `293` (commit)；child.parent=292 ✓
- `293` (commit) → `1284` (chain_end)；child.parent=293 ✓

- L5 真实见证：`293` kind=commit outcome=errant_commit oracle_diff=—

### fault 5

主链每一条边均验证为直接 parent：

- `24` (fault_applied) → `25` (carrier_state)；child.parent=24 ✓
- `25` (carrier_state) → `26` (operand_read)；child.parent=25 ✓
- `26` (operand_read) → `27` (execute)；child.parent=26 ✓
- `27` (execute) → `28` (prf_writeback)；child.parent=27 ✓
- `28` (prf_writeback) → `29` (commit)；child.parent=28 ✓
- `29` (commit) → `1240` (chain_end)；child.parent=29 ✓

- L5 真实见证：`29` kind=commit outcome=errant_commit oracle_diff=—

### fault 50

主链每一条边均验证为直接 parent：

- `294` (fault_applied) → `295` (carrier_state)；child.parent=294 ✓
- `295` (carrier_state) → `296` (operand_read)；child.parent=295 ✓
- `296` (operand_read) → `297` (execute)；child.parent=296 ✓
- `297` (execute) → `298` (prf_writeback)；child.parent=297 ✓
- `298` (prf_writeback) → `299` (commit)；child.parent=298 ✓
- `299` (commit) → `1285` (chain_end)；child.parent=299 ✓

- L5 真实见证：`299` kind=commit outcome=errant_commit oracle_diff=—

### fault 51

主链每一条边均验证为直接 parent：

- `300` (fault_applied) → `301` (carrier_state)；child.parent=300 ✓
- `301` (carrier_state) → `302` (operand_read)；child.parent=301 ✓
- `302` (operand_read) → `303` (execute)；child.parent=302 ✓
- `303` (execute) → `304` (prf_writeback)；child.parent=303 ✓
- `304` (prf_writeback) → `305` (commit)；child.parent=304 ✓
- `305` (commit) → `1286` (chain_end)；child.parent=305 ✓

- L5 真实见证：`305` kind=commit outcome=errant_commit oracle_diff=—

### fault 52

主链每一条边均验证为直接 parent：

- `306` (fault_applied) → `307` (carrier_state)；child.parent=306 ✓
- `307` (carrier_state) → `308` (operand_read)；child.parent=307 ✓
- `308` (operand_read) → `309` (execute)；child.parent=308 ✓
- `309` (execute) → `310` (prf_writeback)；child.parent=309 ✓
- `310` (prf_writeback) → `311` (commit)；child.parent=310 ✓
- `311` (commit) → `1287` (chain_end)；child.parent=311 ✓

- L5 真实见证：`311` kind=commit outcome=errant_commit oracle_diff=—

### fault 53

主链每一条边均验证为直接 parent：

- `312` (fault_applied) → `313` (carrier_state)；child.parent=312 ✓
- `313` (carrier_state) → `314` (operand_read)；child.parent=313 ✓
- `314` (operand_read) → `315` (execute)；child.parent=314 ✓
- `315` (execute) → `316` (prf_writeback)；child.parent=315 ✓
- `316` (prf_writeback) → `317` (commit)；child.parent=316 ✓
- `317` (commit) → `1288` (chain_end)；child.parent=317 ✓

- L5 真实见证：`317` kind=commit outcome=errant_commit oracle_diff=—

### fault 54

主链每一条边均验证为直接 parent：

- `318` (fault_applied) → `319` (carrier_state)；child.parent=318 ✓
- `319` (carrier_state) → `320` (operand_read)；child.parent=319 ✓
- `320` (operand_read) → `321` (execute)；child.parent=320 ✓
- `321` (execute) → `322` (prf_writeback)；child.parent=321 ✓
- `322` (prf_writeback) → `323` (commit)；child.parent=322 ✓
- `323` (commit) → `1289` (chain_end)；child.parent=323 ✓

- L5 真实见证：`323` kind=commit outcome=errant_commit oracle_diff=—

### fault 55

主链每一条边均验证为直接 parent：

- `324` (fault_applied) → `325` (carrier_state)；child.parent=324 ✓
- `325` (carrier_state) → `326` (operand_read)；child.parent=325 ✓
- `326` (operand_read) → `327` (execute)；child.parent=326 ✓
- `327` (execute) → `328` (prf_writeback)；child.parent=327 ✓
- `328` (prf_writeback) → `329` (commit)；child.parent=328 ✓
- `329` (commit) → `1290` (chain_end)；child.parent=329 ✓

- L5 真实见证：`329` kind=commit outcome=errant_commit oracle_diff=—

### fault 56

主链每一条边均验证为直接 parent：

- `330` (fault_applied) → `331` (carrier_state)；child.parent=330 ✓
- `331` (carrier_state) → `332` (operand_read)；child.parent=331 ✓
- `332` (operand_read) → `333` (execute)；child.parent=332 ✓
- `333` (execute) → `334` (prf_writeback)；child.parent=333 ✓
- `334` (prf_writeback) → `335` (commit)；child.parent=334 ✓
- `335` (commit) → `1291` (chain_end)；child.parent=335 ✓

- L5 真实见证：`335` kind=commit outcome=errant_commit oracle_diff=—

### fault 57

主链每一条边均验证为直接 parent：

- `336` (fault_applied) → `337` (carrier_state)；child.parent=336 ✓
- `337` (carrier_state) → `338` (operand_read)；child.parent=337 ✓
- `338` (operand_read) → `339` (execute)；child.parent=338 ✓
- `339` (execute) → `340` (prf_writeback)；child.parent=339 ✓
- `340` (prf_writeback) → `341` (commit)；child.parent=340 ✓
- `341` (commit) → `1292` (chain_end)；child.parent=341 ✓

- L5 真实见证：`341` kind=commit outcome=errant_commit oracle_diff=—

### fault 58

主链每一条边均验证为直接 parent：

- `342` (fault_applied) → `343` (carrier_state)；child.parent=342 ✓
- `343` (carrier_state) → `344` (operand_read)；child.parent=343 ✓
- `344` (operand_read) → `345` (execute)；child.parent=344 ✓
- `345` (execute) → `346` (prf_writeback)；child.parent=345 ✓
- `346` (prf_writeback) → `347` (commit)；child.parent=346 ✓
- `347` (commit) → `1293` (chain_end)；child.parent=347 ✓

- L5 真实见证：`347` kind=commit outcome=errant_commit oracle_diff=—

### fault 59

主链每一条边均验证为直接 parent：

- `348` (fault_applied) → `349` (carrier_state)；child.parent=348 ✓
- `349` (carrier_state) → `350` (operand_read)；child.parent=349 ✓
- `350` (operand_read) → `351` (execute)；child.parent=350 ✓
- `351` (execute) → `352` (prf_writeback)；child.parent=351 ✓
- `352` (prf_writeback) → `353` (commit)；child.parent=352 ✓
- `353` (commit) → `1294` (chain_end)；child.parent=353 ✓

- L5 真实见证：`353` kind=commit outcome=errant_commit oracle_diff=—

### fault 6

主链每一条边均验证为直接 parent：

- `30` (fault_applied) → `31` (carrier_state)；child.parent=30 ✓
- `31` (carrier_state) → `32` (operand_read)；child.parent=31 ✓
- `32` (operand_read) → `33` (execute)；child.parent=32 ✓
- `33` (execute) → `34` (prf_writeback)；child.parent=33 ✓
- `34` (prf_writeback) → `35` (commit)；child.parent=34 ✓
- `35` (commit) → `1241` (chain_end)；child.parent=35 ✓

- L5 真实见证：`35` kind=commit outcome=errant_commit oracle_diff=—

### fault 60

主链每一条边均验证为直接 parent：

- `354` (fault_applied) → `355` (carrier_state)；child.parent=354 ✓
- `355` (carrier_state) → `356` (operand_read)；child.parent=355 ✓
- `356` (operand_read) → `357` (execute)；child.parent=356 ✓
- `357` (execute) → `358` (prf_writeback)；child.parent=357 ✓
- `358` (prf_writeback) → `359` (commit)；child.parent=358 ✓
- `359` (commit) → `1295` (chain_end)；child.parent=359 ✓

- L5 真实见证：`359` kind=commit outcome=errant_commit oracle_diff=—

### fault 61

主链每一条边均验证为直接 parent：

- `360` (fault_applied) → `361` (carrier_state)；child.parent=360 ✓
- `361` (carrier_state) → `362` (operand_read)；child.parent=361 ✓
- `362` (operand_read) → `363` (execute)；child.parent=362 ✓
- `363` (execute) → `364` (prf_writeback)；child.parent=363 ✓
- `364` (prf_writeback) → `365` (commit)；child.parent=364 ✓
- `365` (commit) → `1296` (chain_end)；child.parent=365 ✓

- L5 真实见证：`365` kind=commit outcome=errant_commit oracle_diff=—

### fault 62

主链每一条边均验证为直接 parent：

- `366` (fault_applied) → `367` (carrier_state)；child.parent=366 ✓
- `367` (carrier_state) → `368` (operand_read)；child.parent=367 ✓
- `368` (operand_read) → `369` (execute)；child.parent=368 ✓
- `369` (execute) → `370` (prf_writeback)；child.parent=369 ✓
- `370` (prf_writeback) → `371` (commit)；child.parent=370 ✓
- `371` (commit) → `1297` (chain_end)；child.parent=371 ✓

- L5 真实见证：`371` kind=commit outcome=errant_commit oracle_diff=—

### fault 63

主链每一条边均验证为直接 parent：

- `372` (fault_applied) → `373` (carrier_state)；child.parent=372 ✓
- `373` (carrier_state) → `374` (operand_read)；child.parent=373 ✓
- `374` (operand_read) → `375` (execute)；child.parent=374 ✓
- `375` (execute) → `376` (prf_writeback)；child.parent=375 ✓
- `376` (prf_writeback) → `377` (commit)；child.parent=376 ✓
- `377` (commit) → `1298` (chain_end)；child.parent=377 ✓

- L5 真实见证：`377` kind=commit outcome=errant_commit oracle_diff=—

### fault 64

主链每一条边均验证为直接 parent：

- `378` (fault_applied) → `379` (carrier_state)；child.parent=378 ✓
- `379` (carrier_state) → `380` (operand_read)；child.parent=379 ✓
- `380` (operand_read) → `381` (execute)；child.parent=380 ✓
- `381` (execute) → `382` (prf_writeback)；child.parent=381 ✓
- `382` (prf_writeback) → `383` (commit)；child.parent=382 ✓
- `383` (commit) → `1299` (chain_end)；child.parent=383 ✓

- L5 真实见证：`383` kind=commit outcome=errant_commit oracle_diff=—

### fault 65

主链每一条边均验证为直接 parent：

- `384` (fault_applied) → `385` (carrier_state)；child.parent=384 ✓
- `385` (carrier_state) → `386` (operand_read)；child.parent=385 ✓
- `386` (operand_read) → `387` (execute)；child.parent=386 ✓
- `387` (execute) → `388` (prf_writeback)；child.parent=387 ✓
- `388` (prf_writeback) → `389` (commit)；child.parent=388 ✓
- `389` (commit) → `1300` (chain_end)；child.parent=389 ✓

- L5 真实见证：`389` kind=commit outcome=errant_commit oracle_diff=—

### fault 66

主链每一条边均验证为直接 parent：

- `390` (fault_applied) → `391` (carrier_state)；child.parent=390 ✓
- `391` (carrier_state) → `392` (operand_read)；child.parent=391 ✓
- `392` (operand_read) → `393` (execute)；child.parent=392 ✓
- `393` (execute) → `394` (prf_writeback)；child.parent=393 ✓
- `394` (prf_writeback) → `395` (commit)；child.parent=394 ✓
- `395` (commit) → `1301` (chain_end)；child.parent=395 ✓

- L5 真实见证：`395` kind=commit outcome=errant_commit oracle_diff=—

### fault 67

主链每一条边均验证为直接 parent：

- `396` (fault_applied) → `397` (carrier_state)；child.parent=396 ✓
- `397` (carrier_state) → `398` (operand_read)；child.parent=397 ✓
- `398` (operand_read) → `399` (execute)；child.parent=398 ✓
- `399` (execute) → `400` (prf_writeback)；child.parent=399 ✓
- `400` (prf_writeback) → `401` (commit)；child.parent=400 ✓
- `401` (commit) → `1302` (chain_end)；child.parent=401 ✓

- L5 真实见证：`401` kind=commit outcome=errant_commit oracle_diff=—

### fault 68

主链每一条边均验证为直接 parent：

- `402` (fault_applied) → `403` (carrier_state)；child.parent=402 ✓
- `403` (carrier_state) → `404` (operand_read)；child.parent=403 ✓
- `404` (operand_read) → `405` (execute)；child.parent=404 ✓
- `405` (execute) → `406` (prf_writeback)；child.parent=405 ✓
- `406` (prf_writeback) → `407` (commit)；child.parent=406 ✓
- `407` (commit) → `1303` (chain_end)；child.parent=407 ✓

- L5 真实见证：`407` kind=commit outcome=errant_commit oracle_diff=—

### fault 69

主链每一条边均验证为直接 parent：

- `408` (fault_applied) → `409` (carrier_state)；child.parent=408 ✓
- `409` (carrier_state) → `410` (operand_read)；child.parent=409 ✓
- `410` (operand_read) → `411` (execute)；child.parent=410 ✓
- `411` (execute) → `412` (prf_writeback)；child.parent=411 ✓
- `412` (prf_writeback) → `413` (commit)；child.parent=412 ✓
- `413` (commit) → `1304` (chain_end)；child.parent=413 ✓

- L5 真实见证：`413` kind=commit outcome=errant_commit oracle_diff=—

### fault 7

主链每一条边均验证为直接 parent：

- `36` (fault_applied) → `37` (carrier_state)；child.parent=36 ✓
- `37` (carrier_state) → `38` (operand_read)；child.parent=37 ✓
- `38` (operand_read) → `39` (execute)；child.parent=38 ✓
- `39` (execute) → `40` (prf_writeback)；child.parent=39 ✓
- `40` (prf_writeback) → `41` (commit)；child.parent=40 ✓
- `41` (commit) → `1242` (chain_end)；child.parent=41 ✓

- L5 真实见证：`41` kind=commit outcome=errant_commit oracle_diff=—

### fault 70

主链每一条边均验证为直接 parent：

- `414` (fault_applied) → `415` (carrier_state)；child.parent=414 ✓
- `415` (carrier_state) → `416` (operand_read)；child.parent=415 ✓
- `416` (operand_read) → `417` (execute)；child.parent=416 ✓
- `417` (execute) → `418` (prf_writeback)；child.parent=417 ✓
- `418` (prf_writeback) → `419` (commit)；child.parent=418 ✓
- `419` (commit) → `1305` (chain_end)；child.parent=419 ✓

- L5 真实见证：`419` kind=commit outcome=errant_commit oracle_diff=—

### fault 71

主链每一条边均验证为直接 parent：

- `420` (fault_applied) → `421` (carrier_state)；child.parent=420 ✓
- `421` (carrier_state) → `422` (operand_read)；child.parent=421 ✓
- `422` (operand_read) → `423` (execute)；child.parent=422 ✓
- `423` (execute) → `424` (prf_writeback)；child.parent=423 ✓
- `424` (prf_writeback) → `425` (commit)；child.parent=424 ✓
- `425` (commit) → `1306` (chain_end)；child.parent=425 ✓

- L5 真实见证：`425` kind=commit outcome=errant_commit oracle_diff=—

### fault 72

主链每一条边均验证为直接 parent：

- `426` (fault_applied) → `427` (carrier_state)；child.parent=426 ✓
- `427` (carrier_state) → `428` (operand_read)；child.parent=427 ✓
- `428` (operand_read) → `429` (execute)；child.parent=428 ✓
- `429` (execute) → `430` (prf_writeback)；child.parent=429 ✓
- `430` (prf_writeback) → `431` (commit)；child.parent=430 ✓
- `431` (commit) → `1307` (chain_end)；child.parent=431 ✓

- L5 真实见证：`431` kind=commit outcome=errant_commit oracle_diff=—

### fault 73

主链每一条边均验证为直接 parent：

- `432` (fault_applied) → `433` (carrier_state)；child.parent=432 ✓
- `433` (carrier_state) → `434` (operand_read)；child.parent=433 ✓
- `434` (operand_read) → `435` (execute)；child.parent=434 ✓
- `435` (execute) → `436` (prf_writeback)；child.parent=435 ✓
- `436` (prf_writeback) → `437` (commit)；child.parent=436 ✓
- `437` (commit) → `1308` (chain_end)；child.parent=437 ✓

- L5 真实见证：`437` kind=commit outcome=errant_commit oracle_diff=—

### fault 74

主链每一条边均验证为直接 parent：

- `438` (fault_applied) → `439` (carrier_state)；child.parent=438 ✓
- `439` (carrier_state) → `440` (operand_read)；child.parent=439 ✓
- `440` (operand_read) → `441` (execute)；child.parent=440 ✓
- `441` (execute) → `442` (prf_writeback)；child.parent=441 ✓
- `442` (prf_writeback) → `443` (commit)；child.parent=442 ✓
- `443` (commit) → `1309` (chain_end)；child.parent=443 ✓

- L5 真实见证：`443` kind=commit outcome=errant_commit oracle_diff=—

### fault 75

主链每一条边均验证为直接 parent：

- `444` (fault_applied) → `445` (carrier_state)；child.parent=444 ✓
- `445` (carrier_state) → `446` (operand_read)；child.parent=445 ✓
- `446` (operand_read) → `447` (execute)；child.parent=446 ✓
- `447` (execute) → `448` (prf_writeback)；child.parent=447 ✓
- `448` (prf_writeback) → `449` (commit)；child.parent=448 ✓
- `449` (commit) → `1310` (chain_end)；child.parent=449 ✓

- L5 真实见证：`449` kind=commit outcome=errant_commit oracle_diff=—

### fault 76

主链每一条边均验证为直接 parent：

- `450` (fault_applied) → `451` (carrier_state)；child.parent=450 ✓
- `451` (carrier_state) → `452` (operand_read)；child.parent=451 ✓
- `452` (operand_read) → `453` (execute)；child.parent=452 ✓
- `453` (execute) → `454` (prf_writeback)；child.parent=453 ✓
- `454` (prf_writeback) → `455` (commit)；child.parent=454 ✓
- `455` (commit) → `1311` (chain_end)；child.parent=455 ✓

- L5 真实见证：`455` kind=commit outcome=errant_commit oracle_diff=—

### fault 77

主链每一条边均验证为直接 parent：

- `456` (fault_applied) → `457` (carrier_state)；child.parent=456 ✓
- `457` (carrier_state) → `458` (operand_read)；child.parent=457 ✓
- `458` (operand_read) → `459` (execute)；child.parent=458 ✓
- `459` (execute) → `460` (prf_writeback)；child.parent=459 ✓
- `460` (prf_writeback) → `461` (commit)；child.parent=460 ✓
- `461` (commit) → `1312` (chain_end)；child.parent=461 ✓

- L5 真实见证：`461` kind=commit outcome=errant_commit oracle_diff=—

### fault 78

主链每一条边均验证为直接 parent：

- `462` (fault_applied) → `463` (carrier_state)；child.parent=462 ✓
- `463` (carrier_state) → `464` (operand_read)；child.parent=463 ✓
- `464` (operand_read) → `465` (execute)；child.parent=464 ✓
- `465` (execute) → `466` (prf_writeback)；child.parent=465 ✓
- `466` (prf_writeback) → `467` (commit)；child.parent=466 ✓
- `467` (commit) → `1313` (chain_end)；child.parent=467 ✓

- L5 真实见证：`467` kind=commit outcome=errant_commit oracle_diff=—

### fault 79

主链每一条边均验证为直接 parent：

- `468` (fault_applied) → `469` (carrier_state)；child.parent=468 ✓
- `469` (carrier_state) → `470` (operand_read)；child.parent=469 ✓
- `470` (operand_read) → `471` (execute)；child.parent=470 ✓
- `471` (execute) → `472` (prf_writeback)；child.parent=471 ✓
- `472` (prf_writeback) → `473` (commit)；child.parent=472 ✓
- `473` (commit) → `1314` (chain_end)；child.parent=473 ✓

- L5 真实见证：`473` kind=commit outcome=errant_commit oracle_diff=—

### fault 8

主链每一条边均验证为直接 parent：

- `42` (fault_applied) → `43` (carrier_state)；child.parent=42 ✓
- `43` (carrier_state) → `44` (operand_read)；child.parent=43 ✓
- `44` (operand_read) → `45` (execute)；child.parent=44 ✓
- `45` (execute) → `46` (prf_writeback)；child.parent=45 ✓
- `46` (prf_writeback) → `47` (commit)；child.parent=46 ✓
- `47` (commit) → `1243` (chain_end)；child.parent=47 ✓

- L5 真实见证：`47` kind=commit outcome=errant_commit oracle_diff=—

### fault 80

主链每一条边均验证为直接 parent：

- `474` (fault_applied) → `475` (carrier_state)；child.parent=474 ✓
- `475` (carrier_state) → `476` (operand_read)；child.parent=475 ✓
- `476` (operand_read) → `477` (execute)；child.parent=476 ✓
- `477` (execute) → `478` (prf_writeback)；child.parent=477 ✓
- `478` (prf_writeback) → `479` (commit)；child.parent=478 ✓
- `479` (commit) → `1315` (chain_end)；child.parent=479 ✓

- L5 真实见证：`479` kind=commit outcome=errant_commit oracle_diff=—

### fault 81

主链每一条边均验证为直接 parent：

- `480` (fault_applied) → `481` (carrier_state)；child.parent=480 ✓
- `481` (carrier_state) → `482` (operand_read)；child.parent=481 ✓
- `482` (operand_read) → `483` (execute)；child.parent=482 ✓
- `483` (execute) → `484` (prf_writeback)；child.parent=483 ✓
- `484` (prf_writeback) → `485` (commit)；child.parent=484 ✓
- `485` (commit) → `1316` (chain_end)；child.parent=485 ✓

- L5 真实见证：`485` kind=commit outcome=errant_commit oracle_diff=—

### fault 82

主链每一条边均验证为直接 parent：

- `486` (fault_applied) → `487` (carrier_state)；child.parent=486 ✓
- `487` (carrier_state) → `488` (operand_read)；child.parent=487 ✓
- `488` (operand_read) → `489` (execute)；child.parent=488 ✓
- `489` (execute) → `490` (prf_writeback)；child.parent=489 ✓
- `490` (prf_writeback) → `491` (commit)；child.parent=490 ✓
- `491` (commit) → `1317` (chain_end)；child.parent=491 ✓

- L5 真实见证：`491` kind=commit outcome=errant_commit oracle_diff=—

### fault 83

主链每一条边均验证为直接 parent：

- `492` (fault_applied) → `493` (carrier_state)；child.parent=492 ✓
- `493` (carrier_state) → `494` (operand_read)；child.parent=493 ✓
- `494` (operand_read) → `495` (execute)；child.parent=494 ✓
- `495` (execute) → `496` (prf_writeback)；child.parent=495 ✓
- `496` (prf_writeback) → `497` (commit)；child.parent=496 ✓
- `497` (commit) → `1318` (chain_end)；child.parent=497 ✓

- L5 真实见证：`497` kind=commit outcome=errant_commit oracle_diff=—

### fault 84

主链每一条边均验证为直接 parent：

- `498` (fault_applied) → `499` (carrier_state)；child.parent=498 ✓
- `499` (carrier_state) → `500` (operand_read)；child.parent=499 ✓
- `500` (operand_read) → `501` (execute)；child.parent=500 ✓
- `501` (execute) → `502` (prf_writeback)；child.parent=501 ✓
- `502` (prf_writeback) → `503` (commit)；child.parent=502 ✓
- `503` (commit) → `1319` (chain_end)；child.parent=503 ✓

- L5 真实见证：`503` kind=commit outcome=errant_commit oracle_diff=—

### fault 85

主链每一条边均验证为直接 parent：

- `504` (fault_applied) → `505` (carrier_state)；child.parent=504 ✓
- `505` (carrier_state) → `506` (operand_read)；child.parent=505 ✓
- `506` (operand_read) → `507` (execute)；child.parent=506 ✓
- `507` (execute) → `508` (prf_writeback)；child.parent=507 ✓
- `508` (prf_writeback) → `509` (commit)；child.parent=508 ✓
- `509` (commit) → `1320` (chain_end)；child.parent=509 ✓

- L5 真实见证：`509` kind=commit outcome=errant_commit oracle_diff=—

### fault 86

主链每一条边均验证为直接 parent：

- `510` (fault_applied) → `511` (carrier_state)；child.parent=510 ✓
- `511` (carrier_state) → `512` (operand_read)；child.parent=511 ✓
- `512` (operand_read) → `513` (execute)；child.parent=512 ✓
- `513` (execute) → `514` (prf_writeback)；child.parent=513 ✓
- `514` (prf_writeback) → `515` (commit)；child.parent=514 ✓
- `515` (commit) → `1321` (chain_end)；child.parent=515 ✓

- L5 真实见证：`515` kind=commit outcome=errant_commit oracle_diff=—

### fault 87

主链每一条边均验证为直接 parent：

- `516` (fault_applied) → `517` (carrier_state)；child.parent=516 ✓
- `517` (carrier_state) → `518` (operand_read)；child.parent=517 ✓
- `518` (operand_read) → `519` (execute)；child.parent=518 ✓
- `519` (execute) → `520` (prf_writeback)；child.parent=519 ✓
- `520` (prf_writeback) → `521` (commit)；child.parent=520 ✓
- `521` (commit) → `1322` (chain_end)；child.parent=521 ✓

- L5 真实见证：`521` kind=commit outcome=errant_commit oracle_diff=—

### fault 88

主链每一条边均验证为直接 parent：

- `522` (fault_applied) → `523` (carrier_state)；child.parent=522 ✓
- `523` (carrier_state) → `524` (operand_read)；child.parent=523 ✓
- `524` (operand_read) → `525` (execute)；child.parent=524 ✓
- `525` (execute) → `526` (prf_writeback)；child.parent=525 ✓
- `526` (prf_writeback) → `527` (commit)；child.parent=526 ✓
- `527` (commit) → `1323` (chain_end)；child.parent=527 ✓

- L5 真实见证：`527` kind=commit outcome=errant_commit oracle_diff=—

### fault 89

主链每一条边均验证为直接 parent：

- `528` (fault_applied) → `529` (carrier_state)；child.parent=528 ✓
- `529` (carrier_state) → `530` (operand_read)；child.parent=529 ✓
- `530` (operand_read) → `531` (execute)；child.parent=530 ✓
- `531` (execute) → `532` (prf_writeback)；child.parent=531 ✓
- `532` (prf_writeback) → `533` (commit)；child.parent=532 ✓
- `533` (commit) → `1324` (chain_end)；child.parent=533 ✓

- L5 真实见证：`533` kind=commit outcome=errant_commit oracle_diff=—

### fault 9

主链每一条边均验证为直接 parent：

- `48` (fault_applied) → `49` (carrier_state)；child.parent=48 ✓
- `49` (carrier_state) → `50` (operand_read)；child.parent=49 ✓
- `50` (operand_read) → `51` (execute)；child.parent=50 ✓
- `51` (execute) → `52` (prf_writeback)；child.parent=51 ✓
- `52` (prf_writeback) → `53` (commit)；child.parent=52 ✓
- `53` (commit) → `1244` (chain_end)；child.parent=53 ✓

- L5 真实见证：`53` kind=commit outcome=errant_commit oracle_diff=—

### fault 90

主链每一条边均验证为直接 parent：

- `534` (fault_applied) → `535` (carrier_state)；child.parent=534 ✓
- `535` (carrier_state) → `536` (operand_read)；child.parent=535 ✓
- `536` (operand_read) → `537` (execute)；child.parent=536 ✓
- `537` (execute) → `538` (prf_writeback)；child.parent=537 ✓
- `538` (prf_writeback) → `539` (commit)；child.parent=538 ✓
- `539` (commit) → `1325` (chain_end)；child.parent=539 ✓

- L5 真实见证：`539` kind=commit outcome=errant_commit oracle_diff=—

### fault 91

主链每一条边均验证为直接 parent：

- `540` (fault_applied) → `541` (carrier_state)；child.parent=540 ✓
- `541` (carrier_state) → `542` (operand_read)；child.parent=541 ✓
- `542` (operand_read) → `543` (execute)；child.parent=542 ✓
- `543` (execute) → `544` (prf_writeback)；child.parent=543 ✓
- `544` (prf_writeback) → `545` (commit)；child.parent=544 ✓
- `545` (commit) → `1326` (chain_end)；child.parent=545 ✓

- L5 真实见证：`545` kind=commit outcome=errant_commit oracle_diff=—

### fault 92

主链每一条边均验证为直接 parent：

- `546` (fault_applied) → `547` (carrier_state)；child.parent=546 ✓
- `547` (carrier_state) → `548` (operand_read)；child.parent=547 ✓
- `548` (operand_read) → `549` (execute)；child.parent=548 ✓
- `549` (execute) → `550` (prf_writeback)；child.parent=549 ✓
- `550` (prf_writeback) → `551` (commit)；child.parent=550 ✓
- `551` (commit) → `1327` (chain_end)；child.parent=551 ✓

- L5 真实见证：`551` kind=commit outcome=errant_commit oracle_diff=—

### fault 93

主链每一条边均验证为直接 parent：

- `552` (fault_applied) → `553` (carrier_state)；child.parent=552 ✓
- `553` (carrier_state) → `554` (operand_read)；child.parent=553 ✓
- `554` (operand_read) → `555` (execute)；child.parent=554 ✓
- `555` (execute) → `556` (prf_writeback)；child.parent=555 ✓
- `556` (prf_writeback) → `557` (commit)；child.parent=556 ✓
- `557` (commit) → `1328` (chain_end)；child.parent=557 ✓

- L5 真实见证：`557` kind=commit outcome=errant_commit oracle_diff=—

### fault 94

主链每一条边均验证为直接 parent：

- `558` (fault_applied) → `559` (carrier_state)；child.parent=558 ✓
- `559` (carrier_state) → `560` (operand_read)；child.parent=559 ✓
- `560` (operand_read) → `561` (execute)；child.parent=560 ✓
- `561` (execute) → `562` (prf_writeback)；child.parent=561 ✓
- `562` (prf_writeback) → `563` (commit)；child.parent=562 ✓
- `563` (commit) → `1329` (chain_end)；child.parent=563 ✓

- L5 真实见证：`563` kind=commit outcome=errant_commit oracle_diff=—

### fault 95

主链每一条边均验证为直接 parent：

- `564` (fault_applied) → `565` (carrier_state)；child.parent=564 ✓
- `565` (carrier_state) → `566` (operand_read)；child.parent=565 ✓
- `566` (operand_read) → `567` (execute)；child.parent=566 ✓
- `567` (execute) → `568` (prf_writeback)；child.parent=567 ✓
- `568` (prf_writeback) → `569` (commit)；child.parent=568 ✓
- `569` (commit) → `1330` (chain_end)；child.parent=569 ✓

- L5 真实见证：`569` kind=commit outcome=errant_commit oracle_diff=—

### fault 96

主链每一条边均验证为直接 parent：

- `570` (fault_applied) → `571` (carrier_state)；child.parent=570 ✓
- `571` (carrier_state) → `572` (operand_read)；child.parent=571 ✓
- `572` (operand_read) → `573` (execute)；child.parent=572 ✓
- `573` (execute) → `574` (prf_writeback)；child.parent=573 ✓
- `574` (prf_writeback) → `575` (commit)；child.parent=574 ✓
- `575` (commit) → `1331` (chain_end)；child.parent=575 ✓

- L5 真实见证：`575` kind=commit outcome=errant_commit oracle_diff=—

### fault 97

主链每一条边均验证为直接 parent：

- `576` (fault_applied) → `577` (carrier_state)；child.parent=576 ✓
- `577` (carrier_state) → `578` (operand_read)；child.parent=577 ✓
- `578` (operand_read) → `579` (execute)；child.parent=578 ✓
- `579` (execute) → `580` (prf_writeback)；child.parent=579 ✓
- `580` (prf_writeback) → `581` (commit)；child.parent=580 ✓
- `581` (commit) → `1332` (chain_end)；child.parent=581 ✓

- L5 真实见证：`581` kind=commit outcome=errant_commit oracle_diff=—

### fault 98

主链每一条边均验证为直接 parent：

- `582` (fault_applied) → `583` (carrier_state)；child.parent=582 ✓
- `583` (carrier_state) → `584` (operand_read)；child.parent=583 ✓
- `584` (operand_read) → `585` (execute)；child.parent=584 ✓
- `585` (execute) → `586` (prf_writeback)；child.parent=585 ✓
- `586` (prf_writeback) → `587` (commit)；child.parent=586 ✓
- `587` (commit) → `1333` (chain_end)；child.parent=587 ✓

- L5 真实见证：`587` kind=commit outcome=errant_commit oracle_diff=—

### fault 99

主链每一条边均验证为直接 parent：

- `588` (fault_applied) → `589` (carrier_state)；child.parent=588 ✓
- `589` (carrier_state) → `590` (operand_read)；child.parent=589 ✓
- `590` (operand_read) → `591` (execute)；child.parent=590 ✓
- `591` (execute) → `592` (prf_writeback)；child.parent=591 ✓
- `592` (prf_writeback) → `593` (commit)；child.parent=592 ✓
- `593` (commit) → `1334` (chain_end)；child.parent=593 ✓

- L5 真实见证：`593` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `90a35ddd092c2b68beafe58c451769b2d66a509b47c65b819aed7ac99b81f88a` |
| `run.out` | `a7fc6d54e3e7ec1853a595a0997f8d3638bd28c1f7cbc4497ee67bfa3ec59335` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `0afb1b38a7a0007f7cc22ffcb12f5d0ad87ca7bafba45f822187b7c2002cd953` |
| `oracle.json` | `3b41f5b4810355eab398356fb26ae592e357975291109412522fc4e32b24b3b6` |
| `chain_report.json` | `851f00d5310d1111f552ee81d2f5d9f6d85a73edc13a2430565ac566a9b035b9` |
| `ordinals.json` | `5ed393fc2e10184bf912e82c33ec762680aab236cb33288cb0e2d59753b15397` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `92fe4edddb69046dc6709252477f28469a2ec3409d8a78a4265a24c8bcab0b29` |
| `inject/prop_evt.txt.gz` | `e266a9da450d1fc4627e041e23aed38e4456ed96117abe7ae80df5aed578ddd5` |
| `inject/stats.txt` | `0afb1b38a7a0007f7cc22ffcb12f5d0ad87ca7bafba45f822187b7c2002cd953` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 206 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
