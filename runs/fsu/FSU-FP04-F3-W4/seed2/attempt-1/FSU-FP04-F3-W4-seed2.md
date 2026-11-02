# FSU-FP04-F3-W4 seed2 完整传播链

> 本文只使用本 seed（sample_run_id=`s2`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F3-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F3 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 2 / `s2` |
| selection seed / injection seed | 2 / 2 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F3-W4/seed2/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `219d9b7f9383ba30f9ed0f3e4c17d2c96929deff` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F3-W4/seed2/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F3-W4/seed2/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 202 --rng_seed 2 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 202 --fpu_fault_mask 0 --fpu_rng_seed 2 --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 10298,20361,33182,46711,59510,70166,79416,87728,99456,109978,121327,134236,142269,148727,163191,169406,178599,192470,201697,212979,227713,234229,239242,247421,253116,264123,278480,285823,291413,297651,310253,318861,333634,344458,359256,365853,377275,386394,393515,404018,415854,428937,443648,451193,459579,474429,488572,501904,513553,525065,539803,551287,564717,578688,593496,606562,613482,622530,629942,636470,648212,662265,675818,680945,690165,702448,711467,717774,732353,739892,752162,762383,769573,780285,785294,795907,805846,812421,817988,831871,841747,855985,866117,871284,878460,887962,894968,903866,911621,917336,923349,929591,939569,948823,954733,965039,975999,985758,999165,1009448,1019634,1033000,1042747,1048387,1059911,1067851,1082748,1090540,1101610,1109974,1121794,1134698,1143612,1149382,1154835,1165846,1180459,1191527,1206373,1212971,1227058,1241295,1250297,1265259,1279019,1289570,1302669,1316660,1327825,1335403,1344221,1350327,1356699,1370251,1376879,1390021,1395266,1406910,1421570,1434424,1443779,1457323,1467797,1480835,1495382,1508186,1522689,1536764,1544001,1555744,1566247,1576003,1584389,1594923,1603034,1608112,1623072,1637427,1650885,1663260,1670752,1683913,1693946,1699749,1713937,1728876,1742152,1749764,1761988,1776701,1785865,1790969,1801954,1810197,1817557,1826861,1838272,1850592,1863042,1869245,1882636,1892805,1905432,1920271,1931630,1941330,1946597,1960682,1966819,1975054,1981108,1989497,1997800,2005123,2017329,2023472,2028667,2037470,2048790,2062704,2076621,2085278 --fpu_rate_warmup 0 --fsu_rate_divisor 10000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F3-W4 --prop_sample_run_id s2 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 10000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:10298, 1:20361, 2:33182, 3:46711, 4:59510, 5:70166, 6:79416, 7:87728, 8:99456, 9:109978, 10:121327, 11:134236, 12:142269, 13:148727, 14:163191, 15:169406, 16:178599, 17:192470, 18:201697, 19:212979, 20:227713, 21:234229, 22:239242, 23:247421, 24:253116, 25:264123, 26:278480, 27:285823, 28:291413, 29:297651, 30:310253, 31:318861, 32:333634, 33:344458, 34:359256, 35:365853, 36:377275, 37:386394, 38:393515, 39:404018, 40:415854, 41:428937, 42:443648, 43:451193, 44:459579, 45:474429, 46:488572, 47:501904, 48:513553, 49:525065, 50:539803, 51:551287, 52:564717, 53:578688, 54:593496, 55:606562, 56:613482, 57:622530, 58:629942, 59:636470, 60:648212, 61:662265, 62:675818, 63:680945, 64:690165, 65:702448, 66:711467, 67:717774, 68:732353, 69:739892, 70:752162, 71:762383, 72:769573, 73:780285, 74:785294, 75:795907, 76:805846, 77:812421, 78:817988, 79:831871, 80:841747, 81:855985, 82:866117, 83:871284, 84:878460, 85:887962, 86:894968, 87:903866, 88:911621, 89:917336, 90:923349, 91:929591, 92:939569, 93:948823, 94:954733, 95:965039, 96:975999, 97:985758, 98:999165, 99:1009448, 100:1019634, 101:1033000, 102:1042747, 103:1048387, 104:1059911, 105:1067851, 106:1082748, 107:1090540, 108:1101610, 109:1109974, 110:1121794, 111:1134698, 112:1143612, 113:1149382, 114:1154835, 115:1165846, 116:1180459, 117:1191527, 118:1206373, 119:1212971, 120:1227058, 121:1241295, 122:1250297, 123:1265259, 124:1279019, 125:1289570, 126:1302669, 127:1316660, 128:1327825, 129:1335403, 130:1344221, 131:1350327, 132:1356699, 133:1370251, 134:1376879, 135:1390021, 136:1395266, 137:1406910, 138:1421570, 139:1434424, 140:1443779, 141:1457323, 142:1467797, 143:1480835, 144:1495382, 145:1508186, 146:1522689, 147:1536764, 148:1544001, 149:1555744, 150:1566247, 151:1576003, 152:1584389, 153:1594923, 154:1603034, 155:1608112, 156:1623072, 157:1637427, 158:1650885, 159:1663260, 160:1670752, 161:1683913, 162:1693946, 163:1699749, 164:1713937, 165:1728876, 166:1742152, 167:1749764, 168:1761988, 169:1776701, 170:1785865, 171:1790969, 172:1801954, 173:1810197, 174:1817557, 175:1826861, 176:1838272, 177:1850592, 178:1863042, 179:1869245, 180:1882636, 181:1892805, 182:1905432, 183:1920271, 184:1931630, 185:1941330, 186:1946597, 187:1960682, 188:1966819, 189:1975054, 190:1981108, 191:1989497, 192:1997800, 193:2005123, 194:2017329, 195:2023472, 196:2028667, 197:2037470, 198:2048790, 199:2062704, 200:2076621, 201:2085278 |
| ordinals SHA-256 | `8c317216bd3f6cb57a95091694427889adf7f00f83cd9b190c89429c97a9282d` |
| 注入数（actual/expected） | 202 / 202 |
| fault 数（事件流/injection log） | 202 / 202 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 28481145 / 73977 |
| sn / PC / opcode | 74668 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 10298 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10298 / 0 |
| terminal | full |

### fault 10

| 字段 | 值 |
|---|---|
| 根 event_id | `54` |
| tick / cycle | 179867380 / 467188 |
| sn / PC / opcode | 672768 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 109978 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10522 / 9 |
| terminal | full |

### fault 100

| 字段 | 值 |
|---|---|
| 根 event_id | `594` |
| tick / cycle | 1547794710 / 4020246 |
| sn / PC / opcode | 6069568 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1009448 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10283 / 99 |
| terminal | full |

### fault 101

| 字段 | 值 |
|---|---|
| 根 event_id | `600` |
| tick / cycle | 1563254000 / 4060400 |
| sn / PC / opcode | 6130693 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1019634 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10186 / 100 |
| terminal | full |

### fault 102

| 字段 | 值 |
|---|---|
| 根 event_id | `606` |
| tick / cycle | 1583674785 / 4113441 |
| sn / PC / opcode | 6210900 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1033000 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13366 / 101 |
| terminal | full |

### fault 103

| 字段 | 值 |
|---|---|
| 根 event_id | `612` |
| tick / cycle | 1598522310 / 4152006 |
| sn / PC / opcode | 6269366 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1042747 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9747 / 102 |
| terminal | full |

### fault 104

| 字段 | 值 |
|---|---|
| 根 event_id | `618` |
| tick / cycle | 1607063150 / 4174190 |
| sn / PC / opcode | 6303206 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1048387 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5640 / 103 |
| terminal | full |

### fault 105

| 字段 | 值 |
|---|---|
| 根 event_id | `624` |
| tick / cycle | 1624522900 / 4219540 |
| sn / PC / opcode | 6372359 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1059911 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11524 / 104 |
| terminal | full |

### fault 106

| 字段 | 值 |
|---|---|
| 根 event_id | `630` |
| tick / cycle | 1636614210 / 4250946 |
| sn / PC / opcode | 6419990 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1067851 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7940 / 105 |
| terminal | full |

### fault 107

| 字段 | 值 |
|---|---|
| 根 event_id | `636` |
| tick / cycle | 1659289555 / 4309843 |
| sn / PC / opcode | 6509377 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1082748 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14897 / 106 |
| terminal | full |

### fault 108

| 字段 | 值 |
|---|---|
| 根 event_id | `642` |
| tick / cycle | 1671139855 / 4340623 |
| sn / PC / opcode | 6556140 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1090540 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7792 / 107 |
| terminal | full |

### fault 109

| 字段 | 值 |
|---|---|
| 根 event_id | `648` |
| tick / cycle | 1687967050 / 4384330 |
| sn / PC / opcode | 6622560 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1101610 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11070 / 108 |
| terminal | full |

### fault 11

| 字段 | 值 |
|---|---|
| 根 event_id | `60` |
| tick / cycle | 197174670 / 512142 |
| sn / PC / opcode | 740846 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 121327 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11349 / 10 |
| terminal | full |

### fault 110

| 字段 | 值 |
|---|---|
| 根 event_id | `654` |
| tick / cycle | 1700740965 / 4417509 |
| sn / PC / opcode | 6672744 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1109974 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8364 / 109 |
| terminal | full |

### fault 111

| 字段 | 值 |
|---|---|
| 根 event_id | `660` |
| tick / cycle | 1718758195 / 4464307 |
| sn / PC / opcode | 6743664 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1121794 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11820 / 110 |
| terminal | full |

### fault 112

| 字段 | 值 |
|---|---|
| 根 event_id | `666` |
| tick / cycle | 1738365090 / 4515234 |
| sn / PC / opcode | 6821068 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1134698 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12904 / 111 |
| terminal | full |

### fault 113

| 字段 | 值 |
|---|---|
| 根 event_id | `672` |
| tick / cycle | 1751880130 / 4550338 |
| sn / PC / opcode | 6874561 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1143612 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8914 / 112 |
| terminal | full |

### fault 114

| 字段 | 值 |
|---|---|
| 根 event_id | `678` |
| tick / cycle | 1760725120 / 4573312 |
| sn / PC / opcode | 6909192 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1149382 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5770 / 113 |
| terminal | full |

### fault 115

| 字段 | 值 |
|---|---|
| 根 event_id | `684` |
| tick / cycle | 1768899055 / 4594543 |
| sn / PC / opcode | 6941883 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1154835 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5453 / 114 |
| terminal | full |

### fault 116

| 字段 | 值 |
|---|---|
| 根 event_id | `690` |
| tick / cycle | 1785728945 / 4638257 |
| sn / PC / opcode | 7007976 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1165846 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11011 / 115 |
| terminal | full |

### fault 117

| 字段 | 值 |
|---|---|
| 根 event_id | `696` |
| tick / cycle | 1807947680 / 4695968 |
| sn / PC / opcode | 7095638 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1180459 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14613 / 116 |
| terminal | full |

### fault 118

| 字段 | 值 |
|---|---|
| 根 event_id | `702` |
| tick / cycle | 1824665535 / 4739391 |
| sn / PC / opcode | 7162055 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1191527 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11068 / 117 |
| terminal | full |

### fault 119

| 字段 | 值 |
|---|---|
| 根 event_id | `708` |
| tick / cycle | 1847199200 / 4797920 |
| sn / PC / opcode | 7251122 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1206373 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14846 / 118 |
| terminal | full |

### fault 12

| 字段 | 值 |
|---|---|
| 根 event_id | `66` |
| tick / cycle | 216720735 / 562911 |
| sn / PC / opcode | 818316 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 134236 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12909 / 11 |
| terminal | full |

### fault 120

| 字段 | 值 |
|---|---|
| 根 event_id | `714` |
| tick / cycle | 1857310840 / 4824184 |
| sn / PC / opcode | 7290719 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1212971 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6598 / 119 |
| terminal | full |

### fault 121

| 字段 | 值 |
|---|---|
| 根 event_id | `720` |
| tick / cycle | 1878826180 / 4880068 |
| sn / PC / opcode | 7375248 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1227058 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14087 / 120 |
| terminal | full |

### fault 122

| 字段 | 值 |
|---|---|
| 根 event_id | `726` |
| tick / cycle | 1900537870 / 4936462 |
| sn / PC / opcode | 7460643 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1241295 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14237 / 121 |
| terminal | full |

### fault 123

| 字段 | 值 |
|---|---|
| 根 event_id | `732` |
| tick / cycle | 1914069850 / 4971610 |
| sn / PC / opcode | 7514675 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1250297 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9002 / 122 |
| terminal | full |

### fault 124

| 字段 | 值 |
|---|---|
| 根 event_id | `738` |
| tick / cycle | 1936794475 / 5030635 |
| sn / PC / opcode | 7604427 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1265259 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14962 / 123 |
| terminal | full |

### fault 125

| 字段 | 值 |
|---|---|
| 根 event_id | `744` |
| tick / cycle | 1957812010 / 5085226 |
| sn / PC / opcode | 7687007 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1279019 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13760 / 124 |
| terminal | full |

### fault 126

| 字段 | 值 |
|---|---|
| 根 event_id | `750` |
| tick / cycle | 1973830705 / 5126833 |
| sn / PC / opcode | 7750300 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1289570 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10551 / 125 |
| terminal | full |

### fault 127

| 字段 | 值 |
|---|---|
| 根 event_id | `756` |
| tick / cycle | 1993721730 / 5178498 |
| sn / PC / opcode | 7828887 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1302669 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13099 / 126 |
| terminal | full |

### fault 128

| 字段 | 值 |
|---|---|
| 根 event_id | `762` |
| tick / cycle | 2014969110 / 5233686 |
| sn / PC / opcode | 7912840 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1316660 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13991 / 127 |
| terminal | full |

### fault 129

| 字段 | 值 |
|---|---|
| 根 event_id | `768` |
| tick / cycle | 2032010365 / 5277949 |
| sn / PC / opcode | 7979834 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1327825 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11165 / 128 |
| terminal | full |

### fault 13

| 字段 | 值 |
|---|---|
| 根 event_id | `72` |
| tick / cycle | 229080390 / 595014 |
| sn / PC / opcode | 866487 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 142269 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8033 / 12 |
| terminal | full |

### fault 130

| 字段 | 值 |
|---|---|
| 根 event_id | `774` |
| tick / cycle | 2043556130 / 5307938 |
| sn / PC / opcode | 8025302 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1335403 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7578 / 129 |
| terminal | full |

### fault 131

| 字段 | 值 |
|---|---|
| 根 event_id | `780` |
| tick / cycle | 2056917555 / 5342643 |
| sn / PC / opcode | 8078219 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1344221 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8818 / 130 |
| terminal | full |

### fault 132

| 字段 | 值 |
|---|---|
| 根 event_id | `786` |
| tick / cycle | 2066279215 / 5366959 |
| sn / PC / opcode | 8114835 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1350327 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6106 / 131 |
| terminal | full |

### fault 133

| 字段 | 值 |
|---|---|
| 根 event_id | `792` |
| tick / cycle | 2075928085 / 5392021 |
| sn / PC / opcode | 8153067 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1356699 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6372 / 132 |
| terminal | full |

### fault 134

| 字段 | 值 |
|---|---|
| 根 event_id | `798` |
| tick / cycle | 2096476690 / 5445394 |
| sn / PC / opcode | 8234390 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1370251 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13552 / 133 |
| terminal | full |

### fault 135

| 字段 | 值 |
|---|---|
| 根 event_id | `804` |
| tick / cycle | 2106611815 / 5471719 |
| sn / PC / opcode | 8274167 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1376879 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6628 / 134 |
| terminal | full |

### fault 136

| 字段 | 值 |
|---|---|
| 根 event_id | `810` |
| tick / cycle | 2126591775 / 5523615 |
| sn / PC / opcode | 8353010 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1390021 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13142 / 135 |
| terminal | full |

### fault 137

| 字段 | 值 |
|---|---|
| 根 event_id | `816` |
| tick / cycle | 2134640200 / 5544520 |
| sn / PC / opcode | 8384476 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1395266 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5245 / 136 |
| terminal | full |

### fault 138

| 字段 | 值 |
|---|---|
| 根 event_id | `822` |
| tick / cycle | 2152198125 / 5590125 |
| sn / PC / opcode | 8454349 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1406910 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11644 / 137 |
| terminal | full |

### fault 139

| 字段 | 值 |
|---|---|
| 根 event_id | `828` |
| tick / cycle | 2174504640 / 5648064 |
| sn / PC / opcode | 8542300 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1421570 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14660 / 138 |
| terminal | full |

### fault 14

| 字段 | 值 |
|---|---|
| 根 event_id | `78` |
| tick / cycle | 238830130 / 620338 |
| sn / PC / opcode | 905255 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 148727 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6458 / 13 |
| terminal | full |

### fault 140

| 字段 | 值 |
|---|---|
| 根 event_id | `834` |
| tick / cycle | 2194061100 / 5698860 |
| sn / PC / opcode | 8619444 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1434424 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12854 / 139 |
| terminal | full |

### fault 141

| 字段 | 值 |
|---|---|
| 根 event_id | `840` |
| tick / cycle | 2208348450 / 5735970 |
| sn / PC / opcode | 8675567 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1443779 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9355 / 140 |
| terminal | full |

### fault 142

| 字段 | 值 |
|---|---|
| 根 event_id | `846` |
| tick / cycle | 2229020640 / 5789664 |
| sn / PC / opcode | 8756822 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1457323 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13544 / 141 |
| terminal | full |

### fault 143

| 字段 | 值 |
|---|---|
| 根 event_id | `852` |
| tick / cycle | 2244853765 / 5830789 |
| sn / PC / opcode | 8819675 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1467797 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10474 / 142 |
| terminal | full |

### fault 144

| 字段 | 值 |
|---|---|
| 根 event_id | `858` |
| tick / cycle | 2264658550 / 5882230 |
| sn / PC / opcode | 8897903 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1480835 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13038 / 143 |
| terminal | full |

### fault 145

| 字段 | 值 |
|---|---|
| 根 event_id | `864` |
| tick / cycle | 2286882675 / 5939955 |
| sn / PC / opcode | 8985172 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1495382 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14547 / 144 |
| terminal | full |

### fault 146

| 字段 | 值 |
|---|---|
| 根 event_id | `870` |
| tick / cycle | 2306278590 / 5990334 |
| sn / PC / opcode | 9061996 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1508186 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12804 / 145 |
| terminal | full |

### fault 147

| 字段 | 值 |
|---|---|
| 根 event_id | `876` |
| tick / cycle | 2328351025 / 6047665 |
| sn / PC / opcode | 9149007 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1522689 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14503 / 146 |
| terminal | full |

### fault 148

| 字段 | 值 |
|---|---|
| 根 event_id | `882` |
| tick / cycle | 2349807075 / 6103395 |
| sn / PC / opcode | 9233464 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1536764 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14075 / 147 |
| terminal | full |

### fault 149

| 字段 | 值 |
|---|---|
| 根 event_id | `888` |
| tick / cycle | 2360703345 / 6131697 |
| sn / PC / opcode | 9276879 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1544001 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7237 / 148 |
| terminal | full |

### fault 15

| 字段 | 值 |
|---|---|
| 根 event_id | `84` |
| tick / cycle | 260913730 / 677698 |
| sn / PC / opcode | 992019 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 163191 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14464 / 14 |
| terminal | full |

### fault 150

| 字段 | 值 |
|---|---|
| 根 event_id | `894` |
| tick / cycle | 2378612775 / 6178215 |
| sn / PC / opcode | 9347364 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1555744 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11743 / 149 |
| terminal | full |

### fault 151

| 字段 | 值 |
|---|---|
| 根 event_id | `900` |
| tick / cycle | 2394571025 / 6219665 |
| sn / PC / opcode | 9410366 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1566247 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10503 / 150 |
| terminal | full |

### fault 152

| 字段 | 值 |
|---|---|
| 根 event_id | `906` |
| tick / cycle | 2431136400 / 6314640 |
| sn / PC / opcode | 9475246 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1576003 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9756 / 151 |
| terminal | full |

### fault 153

| 字段 | 值 |
|---|---|
| 根 event_id | `912` |
| tick / cycle | 2488167220 / 6462772 |
| sn / PC / opcode | 9542676 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1584389 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8386 / 152 |
| terminal | full |

### fault 154

| 字段 | 值 |
|---|---|
| 根 event_id | `918` |
| tick / cycle | 2560693520 / 6651152 |
| sn / PC / opcode | 9627339 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1594923 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10534 / 153 |
| terminal | full |

### fault 155

| 字段 | 值 |
|---|---|
| 根 event_id | `924` |
| tick / cycle | 2607115665 / 6771729 |
| sn / PC / opcode | 9692581 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1603034 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8111 / 154 |
| terminal | full |

### fault 156

| 字段 | 值 |
|---|---|
| 根 event_id | `930` |
| tick / cycle | 2634521120 / 6842912 |
| sn / PC / opcode | 9733257 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1608112 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5078 / 155 |
| terminal | full |

### fault 157

| 字段 | 值 |
|---|---|
| 根 event_id | `936` |
| tick / cycle | 2718742180 / 7061668 |
| sn / PC / opcode | 9853035 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1623072 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14960 / 156 |
| terminal | full |

### fault 158

| 字段 | 值 |
|---|---|
| 根 event_id | `942` |
| tick / cycle | 2800165830 / 7273158 |
| sn / PC / opcode | 9967921 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1637427 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14355 / 157 |
| terminal | full |

### fault 159

| 字段 | 值 |
|---|---|
| 根 event_id | `948` |
| tick / cycle | 2880648155 / 7482203 |
| sn / PC / opcode | 10075683 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1650885 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13458 / 158 |
| terminal | full |

### fault 16

| 字段 | 值 |
|---|---|
| 根 event_id | `90` |
| tick / cycle | 270428235 / 702411 |
| sn / PC / opcode | 1029316 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 169406 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6215 / 15 |
| terminal | full |

### fault 160

| 字段 | 值 |
|---|---|
| 根 event_id | `954` |
| tick / cycle | 2956723385 / 7679801 |
| sn / PC / opcode | 10174781 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1663260 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12375 / 159 |
| terminal | full |

### fault 161

| 字段 | 值 |
|---|---|
| 根 event_id | `960` |
| tick / cycle | 2988527080 / 7762408 |
| sn / PC / opcode | 10234717 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1670752 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7492 / 160 |
| terminal | full |

### fault 162

| 字段 | 值 |
|---|---|
| 根 event_id | `966` |
| tick / cycle | 3068168180 / 7969268 |
| sn / PC / opcode | 10340103 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1683913 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13161 / 161 |
| terminal | full |

### fault 163

| 字段 | 值 |
|---|---|
| 根 event_id | `972` |
| tick / cycle | 3127991020 / 8124652 |
| sn / PC / opcode | 10420419 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1693946 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10033 / 162 |
| terminal | full |

### fault 164

| 字段 | 值 |
|---|---|
| 根 event_id | `978` |
| tick / cycle | 3158925000 / 8205000 |
| sn / PC / opcode | 10466889 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1699749 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5803 / 163 |
| terminal | full |

### fault 165

| 字段 | 值 |
|---|---|
| 根 event_id | `984` |
| tick / cycle | 3242309455 / 8421583 |
| sn / PC / opcode | 10580491 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1713937 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14188 / 164 |
| terminal | full |

### fault 166

| 字段 | 值 |
|---|---|
| 根 event_id | `990` |
| tick / cycle | 3329538520 / 8648152 |
| sn / PC / opcode | 10700101 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1728876 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14939 / 165 |
| terminal | full |

### fault 167

| 字段 | 值 |
|---|---|
| 根 event_id | `996` |
| tick / cycle | 3399602360 / 8830136 |
| sn / PC / opcode | 10806361 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1742152 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13276 / 166 |
| terminal | full |

### fault 168

| 字段 | 值 |
|---|---|
| 根 event_id | `1002` |
| tick / cycle | 3441613175 / 8939255 |
| sn / PC / opcode | 10867303 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1749764 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7612 / 167 |
| terminal | full |

### fault 169

| 字段 | 值 |
|---|---|
| 根 event_id | `1008` |
| tick / cycle | 3517371165 / 9136029 |
| sn / PC / opcode | 10965193 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1761988 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12224 / 168 |
| terminal | full |

### fault 17

| 字段 | 值 |
|---|---|
| 根 event_id | `96` |
| tick / cycle | 284354455 / 738583 |
| sn / PC / opcode | 1084467 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 178599 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9193 / 16 |
| terminal | full |

### fault 170

| 字段 | 值 |
|---|---|
| 根 event_id | `1014` |
| tick / cycle | 3600235485 / 9351261 |
| sn / PC / opcode | 11082949 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1776701 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14713 / 169 |
| terminal | full |

### fault 171

| 字段 | 值 |
|---|---|
| 根 event_id | `1020` |
| tick / cycle | 3642169300 / 9460180 |
| sn / PC / opcode | 11156359 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1785865 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9164 / 170 |
| terminal | full |

### fault 172

| 字段 | 值 |
|---|---|
| 根 event_id | `1026` |
| tick / cycle | 3677317875 / 9551475 |
| sn / PC / opcode | 11197191 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1790969 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5104 / 171 |
| terminal | full |

### fault 173

| 字段 | 值 |
|---|---|
| 根 event_id | `1032` |
| tick / cycle | 3734254370 / 9699362 |
| sn / PC / opcode | 11285117 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1801954 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10985 / 172 |
| terminal | full |

### fault 174

| 字段 | 值 |
|---|---|
| 根 event_id | `1038` |
| tick / cycle | 3791493090 / 9848034 |
| sn / PC / opcode | 11351113 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1810197 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8243 / 173 |
| terminal | full |

### fault 175

| 字段 | 值 |
|---|---|
| 根 event_id | `1044` |
| tick / cycle | 3823922795 / 9932267 |
| sn / PC / opcode | 11410039 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1817557 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7360 / 174 |
| terminal | full |

### fault 176

| 字段 | 值 |
|---|---|
| 根 event_id | `1050` |
| tick / cycle | 3887274930 / 10096818 |
| sn / PC / opcode | 11484569 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1826861 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9304 / 175 |
| terminal | full |

### fault 177

| 字段 | 值 |
|---|---|
| 根 event_id | `1056` |
| tick / cycle | 3943639315 / 10243219 |
| sn / PC / opcode | 11575909 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1838272 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11411 / 176 |
| terminal | full |

### fault 178

| 字段 | 值 |
|---|---|
| 根 event_id | `1062` |
| tick / cycle | 4011627235 / 10419811 |
| sn / PC / opcode | 11674515 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1850592 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12320 / 177 |
| terminal | full |

### fault 179

| 字段 | 值 |
|---|---|
| 根 event_id | `1068` |
| tick / cycle | 4087776385 / 10617601 |
| sn / PC / opcode | 11774213 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1863042 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12450 / 178 |
| terminal | full |

### fault 18

| 字段 | 值 |
|---|---|
| 根 event_id | `102` |
| tick / cycle | 305363905 / 793153 |
| sn / PC / opcode | 1167700 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 192470 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13871 / 17 |
| terminal | full |

### fault 180

| 字段 | 值 |
|---|---|
| 根 event_id | `1074` |
| tick / cycle | 4117325520 / 10694352 |
| sn / PC / opcode | 11823889 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1869245 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6203 / 179 |
| terminal | full |

### fault 181

| 字段 | 值 |
|---|---|
| 根 event_id | `1080` |
| tick / cycle | 4194178065 / 10893969 |
| sn / PC / opcode | 11931063 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1882636 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13391 / 180 |
| terminal | full |

### fault 182

| 字段 | 值 |
|---|---|
| 根 event_id | `1086` |
| tick / cycle | 4260244450 / 11065570 |
| sn / PC / opcode | 12012513 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1892805 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10169 / 181 |
| terminal | full |

### fault 183

| 字段 | 值 |
|---|---|
| 根 event_id | `1092` |
| tick / cycle | 4325881945 / 11236057 |
| sn / PC / opcode | 12113581 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1905432 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12627 / 182 |
| terminal | full |

### fault 184

| 字段 | 值 |
|---|---|
| 根 event_id | `1098` |
| tick / cycle | 4407891950 / 11449070 |
| sn / PC / opcode | 12232391 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1920271 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14839 / 183 |
| terminal | full |

### fault 185

| 字段 | 值 |
|---|---|
| 根 event_id | `1104` |
| tick / cycle | 4471610990 / 11614574 |
| sn / PC / opcode | 12323309 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1931630 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11359 / 184 |
| terminal | full |

### fault 186

| 字段 | 值 |
|---|---|
| 根 event_id | `1110` |
| tick / cycle | 4535982990 / 11781774 |
| sn / PC / opcode | 12400961 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1941330 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9700 / 185 |
| terminal | full |

### fault 187

| 字段 | 值 |
|---|---|
| 根 event_id | `1116` |
| tick / cycle | 4558992130 / 11841538 |
| sn / PC / opcode | 12443143 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1946597 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5267 / 186 |
| terminal | full |

### fault 188

| 字段 | 值 |
|---|---|
| 根 event_id | `1122` |
| tick / cycle | 4641937300 / 12056980 |
| sn / PC / opcode | 12555921 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1960682 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14085 / 187 |
| terminal | full |

### fault 189

| 字段 | 值 |
|---|---|
| 根 event_id | `1128` |
| tick / cycle | 4669512925 / 12128605 |
| sn / PC / opcode | 12605069 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1966819 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6137 / 188 |
| terminal | full |

### fault 19

| 字段 | 值 |
|---|---|
| 根 event_id | `108` |
| tick / cycle | 319442970 / 829722 |
| sn / PC / opcode | 1223066 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 201697 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9227 / 18 |
| terminal | full |

### fault 190

| 字段 | 值 |
|---|---|
| 根 event_id | `1134` |
| tick / cycle | 4726535660 / 12276716 |
| sn / PC / opcode | 12670995 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1975054 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8235 / 189 |
| terminal | full |

### fault 191

| 字段 | 值 |
|---|---|
| 根 event_id | `1140` |
| tick / cycle | 4752342980 / 12343748 |
| sn / PC / opcode | 12719427 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1981108 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6054 / 190 |
| terminal | full |

### fault 192

| 字段 | 值 |
|---|---|
| 根 event_id | `1146` |
| tick / cycle | 4807421465 / 12486809 |
| sn / PC / opcode | 12786591 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1989497 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8389 / 191 |
| terminal | full |

### fault 193

| 字段 | 值 |
|---|---|
| 根 event_id | `1152` |
| tick / cycle | 4846815435 / 12589131 |
| sn / PC / opcode | 12853061 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1997800 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8303 / 192 |
| terminal | full |

### fault 194

| 字段 | 值 |
|---|---|
| 根 event_id | `1158` |
| tick / cycle | 4894752555 / 12713643 |
| sn / PC / opcode | 12911697 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 2005123 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7323 / 193 |
| terminal | full |

### fault 195

| 字段 | 值 |
|---|---|
| 根 event_id | `1164` |
| tick / cycle | 4958445415 / 12879079 |
| sn / PC / opcode | 13009443 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 2017329 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12206 / 194 |
| terminal | full |

### fault 196

| 字段 | 值 |
|---|---|
| 根 event_id | `1170` |
| tick / cycle | 5003125435 / 12995131 |
| sn / PC / opcode | 13058633 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 2023472 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6143 / 195 |
| terminal | full |

### fault 197

| 字段 | 值 |
|---|---|
| 根 event_id | `1176` |
| tick / cycle | 5025176310 / 13052406 |
| sn / PC / opcode | 13100193 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 2028667 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5195 / 196 |
| terminal | full |

### fault 198

| 字段 | 值 |
|---|---|
| 根 event_id | `1182` |
| tick / cycle | 5078375995 / 13190587 |
| sn / PC / opcode | 13170669 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 2037470 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8803 / 197 |
| terminal | full |

### fault 199

| 字段 | 值 |
|---|---|
| 根 event_id | `1188` |
| tick / cycle | 5135961985 / 13340161 |
| sn / PC / opcode | 13261327 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 2048790 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11320 / 198 |
| terminal | full |

### fault 2

| 字段 | 值 |
|---|---|
| 根 event_id | `6` |
| tick / cycle | 43691340 / 113484 |
| sn / PC / opcode | 135039 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 20361 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10063 / 1 |
| terminal | full |

### fault 20

| 字段 | 值 |
|---|---|
| 根 event_id | `114` |
| tick / cycle | 336694435 / 874531 |
| sn / PC / opcode | 1290747 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 212979 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11282 / 19 |
| terminal | full |

### fault 200

| 字段 | 值 |
|---|---|
| 根 event_id | `1194` |
| tick / cycle | 5216888215 / 13550359 |
| sn / PC / opcode | 13372685 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 2062704 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13914 / 199 |
| terminal | full |

### fault 201

| 字段 | 值 |
|---|---|
| 根 event_id | `1200` |
| tick / cycle | 5299891135 / 13765951 |
| sn / PC / opcode | 13484119 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 2076621 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13917 / 200 |
| terminal | full |

### fault 202

| 字段 | 值 |
|---|---|
| 根 event_id | `1206` |
| tick / cycle | 5347932975 / 13890735 |
| sn / PC / opcode | 13553427 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 2085278 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8657 / 201 |
| terminal | full |

### fault 21

| 字段 | 值 |
|---|---|
| 根 event_id | `120` |
| tick / cycle | 359077180 / 932668 |
| sn / PC / opcode | 1379162 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 227713 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14734 / 20 |
| terminal | full |

### fault 22

| 字段 | 值 |
|---|---|
| 根 event_id | `126` |
| tick / cycle | 368938570 / 958282 |
| sn / PC / opcode | 1418258 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 234229 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6516 / 21 |
| terminal | full |

### fault 23

| 字段 | 值 |
|---|---|
| 根 event_id | `132` |
| tick / cycle | 376468785 / 977841 |
| sn / PC / opcode | 1448352 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 239242 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5013 / 22 |
| terminal | full |

### fault 24

| 字段 | 值 |
|---|---|
| 根 event_id | `138` |
| tick / cycle | 388973200 / 1010320 |
| sn / PC / opcode | 1497419 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 247421 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8179 / 23 |
| terminal | full |

### fault 25

| 字段 | 值 |
|---|---|
| 根 event_id | `144` |
| tick / cycle | 397621840 / 1032784 |
| sn / PC / opcode | 1531585 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 253116 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5695 / 24 |
| terminal | full |

### fault 26

| 字段 | 值 |
|---|---|
| 根 event_id | `150` |
| tick / cycle | 414340850 / 1076210 |
| sn / PC / opcode | 1597611 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 264123 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11007 / 25 |
| terminal | full |

### fault 27

| 字段 | 值 |
|---|---|
| 根 event_id | `156` |
| tick / cycle | 436188060 / 1132956 |
| sn / PC / opcode | 1683760 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 278480 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14357 / 26 |
| terminal | full |

### fault 28

| 字段 | 值 |
|---|---|
| 根 event_id | `162` |
| tick / cycle | 447269130 / 1161738 |
| sn / PC / opcode | 1727822 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 285823 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7343 / 27 |
| terminal | full |

### fault 29

| 字段 | 值 |
|---|---|
| 根 event_id | `168` |
| tick / cycle | 455904295 / 1184167 |
| sn / PC / opcode | 1761371 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 291413 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5590 / 28 |
| terminal | full |

### fault 3

| 字段 | 值 |
|---|---|
| 根 event_id | `12` |
| tick / cycle | 63090335 / 163871 |
| sn / PC / opcode | 211972 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 33182 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12821 / 2 |
| terminal | full |

### fault 30

| 字段 | 值 |
|---|---|
| 根 event_id | `174` |
| tick / cycle | 465353735 / 1208711 |
| sn / PC / opcode | 1798779 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 297651 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6238 / 29 |
| terminal | full |

### fault 31

| 字段 | 值 |
|---|---|
| 根 event_id | `180` |
| tick / cycle | 484484385 / 1258401 |
| sn / PC / opcode | 1874411 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 310253 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12602 / 30 |
| terminal | full |

### fault 32

| 字段 | 值 |
|---|---|
| 根 event_id | `186` |
| tick / cycle | 497533190 / 1292294 |
| sn / PC / opcode | 1926039 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 318861 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8608 / 31 |
| terminal | full |

### fault 33

| 字段 | 值 |
|---|---|
| 根 event_id | `192` |
| tick / cycle | 520052225 / 1350785 |
| sn / PC / opcode | 2014704 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 333634 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14773 / 32 |
| terminal | full |

### fault 34

| 字段 | 值 |
|---|---|
| 根 event_id | `198` |
| tick / cycle | 536568340 / 1393684 |
| sn / PC / opcode | 2079648 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 344458 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10824 / 33 |
| terminal | full |

### fault 35

| 字段 | 值 |
|---|---|
| 根 event_id | `204` |
| tick / cycle | 558995745 / 1451937 |
| sn / PC / opcode | 2168425 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 359256 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14798 / 34 |
| terminal | full |

### fault 36

| 字段 | 值 |
|---|---|
| 根 event_id | `210` |
| tick / cycle | 569176300 / 1478380 |
| sn / PC / opcode | 2207991 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 365853 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6597 / 35 |
| terminal | full |

### fault 37

| 字段 | 值 |
|---|---|
| 根 event_id | `216` |
| tick / cycle | 586394270 / 1523102 |
| sn / PC / opcode | 2276534 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 377275 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11422 / 36 |
| terminal | full |

### fault 38

| 字段 | 值 |
|---|---|
| 根 event_id | `222` |
| tick / cycle | 600303550 / 1559230 |
| sn / PC / opcode | 2331253 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 386394 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9119 / 37 |
| terminal | full |

### fault 39

| 字段 | 值 |
|---|---|
| 根 event_id | `228` |
| tick / cycle | 611174410 / 1587466 |
| sn / PC / opcode | 2373983 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 393515 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7121 / 38 |
| terminal | full |

### fault 4

| 字段 | 值 |
|---|---|
| 根 event_id | `18` |
| tick / cycle | 83733650 / 217490 |
| sn / PC / opcode | 293150 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 46711 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13529 / 3 |
| terminal | full |

### fault 40

| 字段 | 值 |
|---|---|
| 根 event_id | `234` |
| tick / cycle | 627084535 / 1628791 |
| sn / PC / opcode | 2436988 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 404018 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10503 / 39 |
| terminal | full |

### fault 41

| 字段 | 值 |
|---|---|
| 根 event_id | `240` |
| tick / cycle | 645155665 / 1675729 |
| sn / PC / opcode | 2508013 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 415854 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11836 / 40 |
| terminal | full |

### fault 42

| 字段 | 值 |
|---|---|
| 根 event_id | `246` |
| tick / cycle | 665032830 / 1727358 |
| sn / PC / opcode | 2586495 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 428937 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13083 / 41 |
| terminal | full |

### fault 43

| 字段 | 值 |
|---|---|
| 根 event_id | `252` |
| tick / cycle | 687455230 / 1785598 |
| sn / PC / opcode | 2674768 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 443648 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14711 / 42 |
| terminal | full |

### fault 44

| 字段 | 值 |
|---|---|
| 根 event_id | `258` |
| tick / cycle | 698835445 / 1815157 |
| sn / PC / opcode | 2720051 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 451193 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7545 / 43 |
| terminal | full |

### fault 45

| 字段 | 值 |
|---|---|
| 根 event_id | `264` |
| tick / cycle | 711655175 / 1848455 |
| sn / PC / opcode | 2770347 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 459579 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8386 / 44 |
| terminal | full |

### fault 46

| 字段 | 值 |
|---|---|
| 根 event_id | `270` |
| tick / cycle | 734228495 / 1907087 |
| sn / PC / opcode | 2859447 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 474429 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14850 / 45 |
| terminal | full |

### fault 47

| 字段 | 值 |
|---|---|
| 根 event_id | `276` |
| tick / cycle | 755594070 / 1962582 |
| sn / PC / opcode | 2944332 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 488572 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14143 / 46 |
| terminal | full |

### fault 48

| 字段 | 值 |
|---|---|
| 根 event_id | `282` |
| tick / cycle | 775968655 / 2015503 |
| sn / PC / opcode | 3024324 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 501904 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13332 / 47 |
| terminal | full |

### fault 49

| 字段 | 值 |
|---|---|
| 根 event_id | `288` |
| tick / cycle | 793772595 / 2061747 |
| sn / PC / opcode | 3094202 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 513553 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11649 / 48 |
| terminal | full |

### fault 5

| 字段 | 值 |
|---|---|
| 根 event_id | `24` |
| tick / cycle | 103184235 / 268011 |
| sn / PC / opcode | 369940 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 59510 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12799 / 4 |
| terminal | full |

### fault 50

| 字段 | 值 |
|---|---|
| 根 event_id | `294` |
| tick / cycle | 811200775 / 2107015 |
| sn / PC / opcode | 3163283 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 525065 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11512 / 49 |
| terminal | full |

### fault 51

| 字段 | 值 |
|---|---|
| 根 event_id | `300` |
| tick / cycle | 833611625 / 2165225 |
| sn / PC / opcode | 3251702 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 539803 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14738 / 50 |
| terminal | full |

### fault 52

| 字段 | 值 |
|---|---|
| 根 event_id | `306` |
| tick / cycle | 851125660 / 2210716 |
| sn / PC / opcode | 3320606 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 551287 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11484 / 51 |
| terminal | full |

### fault 53

| 字段 | 值 |
|---|---|
| 根 event_id | `312` |
| tick / cycle | 871407460 / 2263396 |
| sn / PC / opcode | 3401175 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 564717 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13430 / 52 |
| terminal | full |

### fault 54

| 字段 | 值 |
|---|---|
| 根 event_id | `318` |
| tick / cycle | 892726835 / 2318771 |
| sn / PC / opcode | 3485017 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 578688 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13971 / 53 |
| terminal | full |

### fault 55

| 字段 | 值 |
|---|---|
| 根 event_id | `324` |
| tick / cycle | 915304775 / 2377415 |
| sn / PC / opcode | 3573865 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 593496 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14808 / 54 |
| terminal | full |

### fault 56

| 字段 | 值 |
|---|---|
| 根 event_id | `330` |
| tick / cycle | 935163075 / 2428995 |
| sn / PC / opcode | 3652272 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 606562 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13066 / 55 |
| terminal | full |

### fault 57

| 字段 | 值 |
|---|---|
| 根 event_id | `336` |
| tick / cycle | 945677810 / 2456306 |
| sn / PC / opcode | 3693781 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 613482 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6920 / 56 |
| terminal | full |

### fault 58

| 字段 | 值 |
|---|---|
| 根 event_id | `342` |
| tick / cycle | 959391510 / 2491926 |
| sn / PC / opcode | 3748069 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 622530 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9048 / 57 |
| terminal | full |

### fault 59

| 字段 | 值 |
|---|---|
| 根 event_id | `348` |
| tick / cycle | 970812535 / 2521591 |
| sn / PC / opcode | 3792532 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 629942 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7412 / 58 |
| terminal | full |

### fault 6

| 字段 | 值 |
|---|---|
| 根 event_id | `30` |
| tick / cycle | 119271075 / 309795 |
| sn / PC / opcode | 433876 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 70166 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10656 / 5 |
| terminal | full |

### fault 60

| 字段 | 值 |
|---|---|
| 根 event_id | `354` |
| tick / cycle | 980663915 / 2547179 |
| sn / PC / opcode | 3831700 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 636470 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6528 / 59 |
| terminal | full |

### fault 61

| 字段 | 值 |
|---|---|
| 根 event_id | `360` |
| tick / cycle | 998478250 / 2593450 |
| sn / PC / opcode | 3902152 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 648212 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11742 / 60 |
| terminal | full |

### fault 62

| 字段 | 值 |
|---|---|
| 根 event_id | `366` |
| tick / cycle | 1019971645 / 2649277 |
| sn / PC / opcode | 3986463 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 662265 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14053 / 61 |
| terminal | full |

### fault 63

| 字段 | 值 |
|---|---|
| 根 event_id | `372` |
| tick / cycle | 1040487525 / 2702565 |
| sn / PC / opcode | 4067788 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 675818 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13553 / 62 |
| terminal | full |

### fault 64

| 字段 | 值 |
|---|---|
| 根 event_id | `378` |
| tick / cycle | 1048299175 / 2722855 |
| sn / PC / opcode | 4098563 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 680945 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5127 / 63 |
| terminal | full |

### fault 65

| 字段 | 值 |
|---|---|
| 根 event_id | `384` |
| tick / cycle | 1062285840 / 2759184 |
| sn / PC / opcode | 4153863 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 690165 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9220 / 64 |
| terminal | full |

### fault 66

| 字段 | 值 |
|---|---|
| 根 event_id | `390` |
| tick / cycle | 1080906365 / 2807549 |
| sn / PC / opcode | 4227588 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 702448 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12283 / 65 |
| terminal | full |

### fault 67

| 字段 | 值 |
|---|---|
| 根 event_id | `396` |
| tick / cycle | 1094678970 / 2843322 |
| sn / PC / opcode | 4281695 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 711467 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9019 / 66 |
| terminal | full |

### fault 68

| 字段 | 值 |
|---|---|
| 根 event_id | `402` |
| tick / cycle | 1104230820 / 2868132 |
| sn / PC / opcode | 4319533 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 717774 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6307 / 67 |
| terminal | full |

### fault 69

| 字段 | 值 |
|---|---|
| 根 event_id | `408` |
| tick / cycle | 1126419140 / 2925764 |
| sn / PC / opcode | 4407011 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 732353 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14579 / 68 |
| terminal | full |

### fault 7

| 字段 | 值 |
|---|---|
| 根 event_id | `36` |
| tick / cycle | 133366695 / 346407 |
| sn / PC / opcode | 489385 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 79416 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9250 / 6 |
| terminal | full |

### fault 70

| 字段 | 值 |
|---|---|
| 根 event_id | `414` |
| tick / cycle | 1137787805 / 2955293 |
| sn / PC / opcode | 4452232 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 739892 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7539 / 69 |
| terminal | full |

### fault 71

| 字段 | 值 |
|---|---|
| 根 event_id | `420` |
| tick / cycle | 1156558095 / 3004047 |
| sn / PC / opcode | 4525852 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 752162 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12270 / 70 |
| terminal | full |

### fault 72

| 字段 | 值 |
|---|---|
| 根 event_id | `426` |
| tick / cycle | 1172132500 / 3044500 |
| sn / PC / opcode | 4587191 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 762383 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10221 / 71 |
| terminal | full |

### fault 73

| 字段 | 值 |
|---|---|
| 根 event_id | `432` |
| tick / cycle | 1183087290 / 3072954 |
| sn / PC / opcode | 4630322 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 769573 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7190 / 72 |
| terminal | full |

### fault 74

| 字段 | 值 |
|---|---|
| 根 event_id | `438` |
| tick / cycle | 1199269995 / 3114987 |
| sn / PC / opcode | 4694583 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 780285 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10712 / 73 |
| terminal | full |

### fault 75

| 字段 | 值 |
|---|---|
| 根 event_id | `444` |
| tick / cycle | 1206976925 / 3135005 |
| sn / PC / opcode | 4724644 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 785294 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5009 / 74 |
| terminal | full |

### fault 76

| 字段 | 值 |
|---|---|
| 根 event_id | `450` |
| tick / cycle | 1223224695 / 3177207 |
| sn / PC / opcode | 4788326 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 795907 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10613 / 75 |
| terminal | full |

### fault 77

| 字段 | 值 |
|---|---|
| 根 event_id | `456` |
| tick / cycle | 1238255865 / 3216249 |
| sn / PC / opcode | 4847976 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 805846 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9939 / 76 |
| terminal | full |

### fault 78

| 字段 | 值 |
|---|---|
| 根 event_id | `462` |
| tick / cycle | 1248234680 / 3242168 |
| sn / PC / opcode | 4887399 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 812421 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6575 / 77 |
| terminal | full |

### fault 79

| 字段 | 值 |
|---|---|
| 根 event_id | `468` |
| tick / cycle | 1256696980 / 3264148 |
| sn / PC / opcode | 4920808 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 817988 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5567 / 78 |
| terminal | full |

### fault 8

| 字段 | 值 |
|---|---|
| 根 event_id | `42` |
| tick / cycle | 145995080 / 379208 |
| sn / PC / opcode | 539248 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 87728 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8312 / 7 |
| terminal | full |

### fault 80

| 字段 | 值 |
|---|---|
| 根 event_id | `474` |
| tick / cycle | 1277749550 / 3318830 |
| sn / PC / opcode | 5004110 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 831871 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13883 / 79 |
| terminal | full |

### fault 81

| 字段 | 值 |
|---|---|
| 根 event_id | `480` |
| tick / cycle | 1292699100 / 3357660 |
| sn / PC / opcode | 5063366 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 841747 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9876 / 80 |
| terminal | full |

### fault 82

| 字段 | 值 |
|---|---|
| 根 event_id | `486` |
| tick / cycle | 1314429270 / 3414102 |
| sn / PC / opcode | 5148794 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 855985 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14238 / 81 |
| terminal | full |

### fault 83

| 字段 | 值 |
|---|---|
| 根 event_id | `492` |
| tick / cycle | 1329774600 / 3453960 |
| sn / PC / opcode | 5209595 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 866117 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10132 / 82 |
| terminal | full |

### fault 84

| 字段 | 值 |
|---|---|
| 根 event_id | `498` |
| tick / cycle | 1337644000 / 3474400 |
| sn / PC / opcode | 5240593 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 871284 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5167 / 83 |
| terminal | full |

### fault 85

| 字段 | 值 |
|---|---|
| 根 event_id | `504` |
| tick / cycle | 1348577615 / 3502799 |
| sn / PC / opcode | 5283649 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 878460 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7176 / 84 |
| terminal | full |

### fault 86

| 字段 | 值 |
|---|---|
| 根 event_id | `510` |
| tick / cycle | 1363182975 / 3540735 |
| sn / PC / opcode | 5340672 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 887962 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9502 / 85 |
| terminal | full |

### fault 87

| 字段 | 值 |
|---|---|
| 根 event_id | `516` |
| tick / cycle | 1373765855 / 3568223 |
| sn / PC / opcode | 5382688 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 894968 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7006 / 86 |
| terminal | full |

### fault 88

| 字段 | 值 |
|---|---|
| 根 event_id | `522` |
| tick / cycle | 1387344035 / 3603491 |
| sn / PC / opcode | 5436076 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 903866 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8898 / 87 |
| terminal | full |

### fault 89

| 字段 | 值 |
|---|---|
| 根 event_id | `528` |
| tick / cycle | 1399034175 / 3633855 |
| sn / PC / opcode | 5482619 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 911621 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7755 / 88 |
| terminal | full |

### fault 9

| 字段 | 值 |
|---|---|
| 根 event_id | `48` |
| tick / cycle | 163877175 / 425655 |
| sn / PC / opcode | 609625 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 99456 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11728 / 8 |
| terminal | full |

### fault 90

| 字段 | 值 |
|---|---|
| 根 event_id | `534` |
| tick / cycle | 1407713230 / 3656398 |
| sn / PC / opcode | 5516896 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 917336 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5715 / 89 |
| terminal | full |

### fault 91

| 字段 | 值 |
|---|---|
| 根 event_id | `540` |
| tick / cycle | 1416895480 / 3680248 |
| sn / PC / opcode | 5552967 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 923349 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6013 / 90 |
| terminal | full |

### fault 92

| 字段 | 值 |
|---|---|
| 根 event_id | `546` |
| tick / cycle | 1426354160 / 3704816 |
| sn / PC / opcode | 5590439 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 929591 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6242 / 91 |
| terminal | full |

### fault 93

| 字段 | 值 |
|---|---|
| 根 event_id | `552` |
| tick / cycle | 1441526240 / 3744224 |
| sn / PC / opcode | 5650307 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 939569 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9978 / 92 |
| terminal | full |

### fault 94

| 字段 | 值 |
|---|---|
| 根 event_id | `558` |
| tick / cycle | 1455542935 / 3780631 |
| sn / PC / opcode | 5705822 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 948823 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9254 / 93 |
| terminal | full |

### fault 95

| 字段 | 值 |
|---|---|
| 根 event_id | `564` |
| tick / cycle | 1464615845 / 3804197 |
| sn / PC / opcode | 5741282 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 954733 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5910 / 94 |
| terminal | full |

### fault 96

| 字段 | 值 |
|---|---|
| 根 event_id | `570` |
| tick / cycle | 1480366195 / 3845107 |
| sn / PC / opcode | 5803127 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 965039 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10306 / 95 |
| terminal | full |

### fault 97

| 字段 | 值 |
|---|---|
| 根 event_id | `576` |
| tick / cycle | 1496913880 / 3888088 |
| sn / PC / opcode | 5868867 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 975999 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10960 / 96 |
| terminal | full |

### fault 98

| 字段 | 值 |
|---|---|
| 根 event_id | `582` |
| tick / cycle | 1511762175 / 3926655 |
| sn / PC / opcode | 5927437 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 985758 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9759 / 97 |
| terminal | full |

### fault 99

| 字段 | 值 |
|---|---|
| 根 event_id | `588` |
| tick / cycle | 1532256880 / 3979888 |
| sn / PC / opcode | 6007863 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 999165 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13407 / 98 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 5135961985, Site: dyn_inst_execute, opClass=8, sn=13261327, bitseg=mant_lo, mask=0x4, faults_injected: 199
Tick: 5216888215, Site: dyn_inst_execute, opClass=8, sn=13372685, bitseg=mant_lo, mask=0x2, faults_injected: 200
Tick: 5299891135, Site: dyn_inst_execute, opClass=8, sn=13484119, bitseg=mant_lo, mask=0x100, faults_injected: 201
Tick: 5347932975, Site: dyn_inst_execute, opClass=8, sn=13553427, bitseg=mant_lo, mask=0x8000, faults_injected: 202
CHAOS_RATE_COMPLETE=202
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfdb126e978d4fdf → 0xbfdb126e978d4fde |
| old/new hash | 0x9079562ea0503dcf → 0xbcc8b2326b37f09a |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfdb126e978d4fdf / 0xbfdb126e978d4fde |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 10

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4076600000000000 → 0x4076600000008000 |
| old/new hash | 0x5eb0997f4dd6e2c5 → 0xb572d45663ed7545 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4076600000000000 / 0x4076600000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 100

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd5a1cac083126f → 0xbfd5a1cac083136f |
| old/new hash | 0x1bcb8561a9706808 → 0x518d3b3761996793 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd5a1cac083126f / 0xbfd5a1cac083136f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 101

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080400000000000 → 0x4080400000010000 |
| old/new hash | 0x70a98d7fe81bfb63 → 0x3f55a94a862adfaa |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080400000000000 / 0x4080400000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 102

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x405fc00000000000 → 0x405fc00000000002 |
| old/new hash | 0x1ce4237d74ef6c94 → 0x89d26d68eac183d6 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x405fc00000000000 / 0x405fc00000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 103

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff28f5c28f5c28f → 0x3ff28f5c28f5c28b |
| old/new hash | 0xdf608e7b729bc0c5 → 0x9a41032ce4908b11 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff28f5c28f5c28f / 0x3ff28f5c28f5c28b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 104

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff6353f7ced9169 → 0x3ff6353f7cedd169 |
| old/new hash | 0x362c7400752e9633 → 0x803edacd3cc2cc73 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff6353f7ced9169 / 0x3ff6353f7cedd169 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 105

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4051c00000000000 → 0x4051c00000000200 |
| old/new hash | 0x1cf9077d7501990a → 0x5426be8fa5bf18a0 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4051c00000000000 / 0x4051c00000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 106

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe53f7ced916873 → 0x3fe53f7ced916872 |
| old/new hash | 0x096158c79b2a2783 → 0x1df2cd3a1af03406 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe53f7ced916873 / 0x3fe53f7ced916872 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 107

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x402c000000000000 → 0x402c000000004000 |
| old/new hash | 0x4783757eaf25f35f → 0x9c22d813241b839f |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x402c000000000000 / 0x402c000000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 108

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087380000000000 → 0x4087380000000020 |
| old/new hash | 0x79d0ab7e3b427cc4 → 0x8388cca0d32c4524 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087380000000000 / 0x4087380000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 109

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408e880000000000 → 0x408e880000000200 |
| old/new hash | 0xafc9717c15dd0e65 → 0x36dfa090b67ee52f |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408e880000000000 / 0x408e880000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 11

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feda1cac083126f → 0x3feda1cac083122f |
| old/new hash | 0x1b0c8561a8cd8c00 → 0xfe9e3a6197524040 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feda1cac083126f / 0x3feda1cac083122f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 110

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408ed00000000000 → 0x408ed00000001000 |
| old/new hash | 0xa66fd97dc28c171d → 0x3f7e40d80b31638d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408ed00000000000 / 0x408ed00000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 111

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4067400000000000 → 0x4067400000000080 |
| old/new hash | 0x7119b37fe87b43ac → 0xf3b62efa70d6332c |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4067400000000000 / 0x4067400000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 112

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd2d0e560418937 → 0xbfd2d0e560418b37 |
| old/new hash | 0x4030ea6fa03d3514 → 0x1830ea600ec42ffa |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd2d0e560418937 / 0xbfd2d0e560418b37 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 113

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4074000000000000 → 0x4074000000000002 |
| old/new hash | 0x48ae857eb0240977 → 0x0a4c376c99e91015 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4074000000000000 / 0x4074000000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 114

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4071c00000000000 → 0x4071c00000002000 |
| old/new hash | 0x1c8c477d74a533ea → 0x72f7b8c53bd9040a |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4071c00000000000 / 0x4071c00000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 115

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd6353f7ced9168 → 0x3fd6353f7ced9128 |
| old/new hash | 0xebbd50c4499d83ba → 0x7ee6b2e55c0202fa |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd6353f7ced9168 / 0x3fd6353f7ced9128 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 116

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407ca00000000000 → 0x407ca00000000001 |
| old/new hash | 0xddccf57b9e54fb0f → 0x92760e78b536ad9e |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407ca00000000000 / 0x407ca00000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 117

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe851eb851eb852 → 0x3fe851eb851ef852 |
| old/new hash | 0x01283ef34de8e00d → 0xaef5d02dba98814d |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe851eb851eb852 / 0x3fe851eb851ef852 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 118

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4071f00000000000 → 0x4071f00000002000 |
| old/new hash | 0x933ad77d273a789a → 0x125188c626fb857a |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4071f00000000000 / 0x4071f00000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 119

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe7b645a1cac083 → 0x3fe7b645a1cbc083 |
| old/new hash | 0xcaa61c3024f6fb18 → 0xa2950c8e2d5b66b1 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe7b645a1cac083 / 0x3fe7b645a1cbc083 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 12

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4077800000000000 → 0x4077800000000002 |
| old/new hash | 0xf3e6d37c3c1c0a7c → 0xb5929d6a25ed773e |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4077800000000000 / 0x4077800000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 120

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408d280000000000 → 0x408d280000020000 |
| old/new hash | 0xef5af77decdf71ae → 0xeb249f19997b7aac |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408d280000000000 / 0x408d280000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 121

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4089200000000000 → 0x4089200000000010 |
| old/new hash | 0x30fd577e11035852 → 0x4e6e880ffcdace22 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4089200000000000 / 0x4089200000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 122

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff01cac083126ea → 0x3ff01cac083326ea |
| old/new hash | 0x83d00e6a868ad35f → 0x44ceff06c282a549 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff01cac083126ea / 0x3ff01cac083326ea |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 123

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080200000000000 → 0x4080200000010000 |
| old/new hash | 0x311b6d7e111c7b43 → 0x57eb894b260eb78a |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080200000000000 / 0x4080200000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 124

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff34bc6a7ef9db2 → 0x3ff34bc6a7ef9cb2 |
| old/new hash | 0x653d17bd3a82b9dd → 0xace91a0e32476736 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff34bc6a7ef9db2 / 0x3ff34bc6a7ef9cb2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 125

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x406ca00000000000 → 0x406ca00000000001 |
| old/new hash | 0xdd96957b9e26c87f → 0x92abee78b56406ae |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x406ca00000000000 / 0x406ca00000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 126

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd5b22d0e560419 → 0xbfd5b22d0e560619 |
| old/new hash | 0xab32a417a3d1a9a5 → 0x7b0d41ef232433b7 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd5b22d0e560419 / 0xbfd5b22d0e560619 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 127

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe2b020c49ba5e3 → 0x3fe2b020c49ba5eb |
| old/new hash | 0x943a5b6f0ef09a33 → 0xed77d5de4b6d7c5b |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe2b020c49ba5e3 / 0x3fe2b020c49ba5eb |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 128

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc7ef9db22d0e57 → 0x3fc7ef9db22d0e17 |
| old/new hash | 0x19ac61af405e770f → 0x048a1f6a0f1b04cf |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc7ef9db22d0e57 / 0x3fc7ef9db22d0e17 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 129

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff26a7ef9db22d1 → 0x3ff26a7ef9db32d1 |
| old/new hash | 0x35e3effebe010aaf → 0xd53395ba9aaa425f |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff26a7ef9db22d1 / 0x3ff26a7ef9db32d1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 13

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff05604189374bc → 0x3ff0560418937cbc |
| old/new hash | 0x42930d585197d07f → 0x4c862cfb1fa7e8a7 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff05604189374bc / 0x3ff0560418937cbc |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 130

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff7ef9db22d0e56 → 0x3ff7ef9db22d0c56 |
| old/new hash | 0xadee6c83e4a86e4e → 0x5758bebf121a9cec |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff7ef9db22d0e56 / 0x3ff7ef9db22d0c56 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 131

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408a100000000000 → 0x408a100000020000 |
| old/new hash | 0xd427017eff635e39 → 0x0272711883a8600b |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408a100000000000 / 0x408a100000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 132

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd10624dd2f1aa0 → 0x3fd10624dd2f1aa2 |
| old/new hash | 0xb9333b9a03a27277 → 0x6df4e5bd18ff4385 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd10624dd2f1aa0 / 0x3fd10624dd2f1aa2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 133

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff122d0e5604189 → 0x3ff122d0e560c189 |
| old/new hash | 0xa2941113adab8824 → 0xb0f36e11e05315a4 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff122d0e5604189 / 0x3ff122d0e560c189 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 134

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff72b020c49ba5e → 0x3ff72b020c49ba7e |
| old/new hash | 0x29d53815d7daf4c7 → 0xde14b6a3fa16cf67 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff72b020c49ba5e / 0x3ff72b020c49ba7e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 135

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4082580000000000 → 0x4082580000000800 |
| old/new hash | 0xb5ef19800f5703e9 → 0x15f26d2dcf377e41 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4082580000000000 / 0x4082580000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 136

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3cac083126e98 → 0x3ff3cac083127e98 |
| old/new hash | 0xfbfb083d37667fb6 → 0x89abe73d9a2bc606 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3cac083126e98 / 0x3ff3cac083127e98 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 137

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfa916872b020c48 → 0xbfa916872b030c48 |
| old/new hash | 0xacd937bf362a5cd1 → 0x4e16b584c737c3cc |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfa916872b020c48 / 0xbfa916872b030c48 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 138

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4071900000000000 → 0x4071900000010000 |
| old/new hash | 0x7d31777c8980ff7a → 0x8b05bf48fe38c513 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4071900000000000 / 0x4071900000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 139

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd3f7ced916872b → 0x3fd3f7ced916862b |
| old/new hash | 0x1617f86729e8a7e1 → 0xa134f8af6866002e |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd3f7ced916872b / 0x3fd3f7ced916862b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 14

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081f80000000000 → 0x4081f80000000002 |
| old/new hash | 0x4c051f7cfe59e2b2 → 0x43ea4168c2fcbd20 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081f80000000000 / 0x4081f80000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 140

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408e000000000000 → 0x408e000000002000 |
| old/new hash | 0x499c697eb0ee26ad → 0xf085dac8e885590d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408e000000000000 / 0x408e000000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 141

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4078100000000000 → 0x4078100000000002 |
| old/new hash | 0xd1d72d7efd6c1edb → 0x9374df6ce7312579 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4078100000000000 / 0x4078100000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 142

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff6e978d4fdf3b6 → 0x3ff6e978d4fdf3b4 |
| old/new hash | 0x2b93cb426782d2e9 → 0xb20734f82d6d1487 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff6e978d4fdf3b6 / 0x3ff6e978d4fdf3b4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 143

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080300000000000 → 0x4080300000000020 |
| old/new hash | 0xbbb39d7e5f9d3f73 → 0xc56b3ea0f7862e53 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080300000000000 / 0x4080300000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 144

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4072100000000000 → 0x4072100000000010 |
| old/new hash | 0xd1ec117efd7e4b51 → 0xae88e20f114111a1 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4072100000000000 / 0x4072100000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 145

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd6353f7ced9169 → 0x3fd6353f7ced1169 |
| old/new hash | 0x36997400758b6813 → 0x4cd9063b7091c593 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd6353f7ced9169 / 0x3fd6353f7ced1169 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 146

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd947ae147ae148 → 0x3fd947ae147af148 |
| old/new hash | 0x519f73bc175a4361 → 0x4ac8516a50302d71 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd947ae147ae148 / 0x3fd947ae147af148 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 147

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd1cac083126e98 → 0x3fd1cac083126e90 |
| old/new hash | 0xfb87883d370468a8 → 0x6b9979f00c8af3d0 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd1cac083126e98 / 0x3fd1cac083126e90 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 148

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdb645a1cac0832 → 0x3fdb645a1cac0032 |
| old/new hash | 0xc91867141aab3069 → 0x1a7f883c73530e41 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdb645a1cac0832 / 0x3fdb645a1cac0032 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 149

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe2978d4fdf3b64 → 0x3fe2978d4fdf3b44 |
| old/new hash | 0xa3c3009a6deb57ab → 0xc5767cdfb2557acb |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe2978d4fdf3b64 / 0x3fe2978d4fdf3b44 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 15

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff20c49ba5e3540 → 0x3ff20c49ba5e3548 |
| old/new hash | 0x0bf879ea52fa7baa → 0xd21ce4ec8838a342 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff20c49ba5e3540 / 0x3ff20c49ba5e3548 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 150

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087880000000000 → 0x4087880000002000 |
| old/new hash | 0xafaadb7c15c311f4 → 0x59faccc6503e46d4 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087880000000000 / 0x4087880000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 151

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe8e5604189374c → 0x3fe8e5604189375c |
| old/new hash | 0xdd4d8a4a4789ee0a → 0xf3ee0c217f5e9b1a |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe8e5604189374c / 0x3fe8e5604189375c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 152

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdf8d21bc126a67 → 0x3fdf8d21bc126ae7 |
| old/new hash | 0x8b22c4e481edd3ac → 0xb8c715dcd5c2de2c |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdf8d21bc126a67 / 0x3fdf8d21bc126ae7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 153

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe3f05c896dd26d → 0x3fe3f05c896dc26d |
| old/new hash | 0x9923b447444b4d68 → 0x8889254fcb258d58 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe3f05c896dd26d / 0x3fe3f05c896dc26d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 154

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe9978d4fdf3b65 → 0x3fe9978d4fdf3965 |
| old/new hash | 0x64a2ade99a7f7545 → 0x28d699ef9acf5603 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe9978d4fdf3b65 / 0x3fe9978d4fdf3965 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 155

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x40000b417ca2120e → 0x40000b417ca2920e |
| old/new hash | 0x84098a32fe30ee59 → 0x712ff7f8060db9d9 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x40000b417ca2120e / 0x40000b417ca2920e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 156

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fcd590c0ad03d9b → 0x3fcd590c0ad03d9f |
| old/new hash | 0x8f68d915a16da2ba → 0x2a57a4a3edce139e |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fcd590c0ad03d9b / 0x3fcd590c0ad03d9f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 157

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe900713f077ccd → 0x3fe900713f073ccd |
| old/new hash | 0x350ff0a0d8806cdd → 0xdf7a12377fdb931d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe900713f077ccd / 0x3fe900713f073ccd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 158

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff88787485e3da3 → 0x3ff88787485e35a3 |
| old/new hash | 0xf60d12536bcf8e66 → 0x89663e69176cf82e |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff88787485e3da3 / 0x3ff88787485e35a3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 159

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc556c0d6f544bb → 0x3fc556c0d6f564bb |
| old/new hash | 0xe707c46721813ff9 → 0xa4c941a58f348a99 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc556c0d6f544bb / 0x3fc556c0d6f564bb |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 16

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdcfdf3b645a1cb → 0x3fdcfdf3b645a9cb |
| old/new hash | 0xb197c88209e68289 → 0x14d9bcf038907261 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdcfdf3b645a1cb / 0x3fdcfdf3b645a9cb |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 160

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fffef0281ba7fc4 → 0x3fffef0281ba7fc5 |
| old/new hash | 0xfb16d1a2fc4b6046 → 0xda1145b65aa598db |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fffef0281ba7fc4 / 0x3fffef0281ba7fc5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 161

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd65b4245f5ad96 → 0x3fd65b4245f5ad92 |
| old/new hash | 0x80c026f2d75d2ea8 → 0x0de23777528105cc |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd65b4245f5ad96 / 0x3fd65b4245f5ad92 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 162

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe4cdf8b1572581 → 0x3fe4cdf8b1572580 |
| old/new hash | 0x82de3f37e8bb5dd7 → 0x24bf5eb94badeb02 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe4cdf8b1572581 / 0x3fe4cdf8b1572580 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 163

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff8c3f3e0370cdc → 0x3ff8c3f3e0370cdd |
| old/new hash | 0x53ca7dc570046323 → 0xd4569eeea11d0b82 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff8c3f3e0370cdc / 0x3ff8c3f3e0370cdd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 164

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe5fa871a3b14aa → 0x3fe5fa871a3b16aa |
| old/new hash | 0xf2e2cbfd8e7ed18d → 0x403c52212fed0b2b |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe5fa871a3b14aa / 0x3fe5fa871a3b16aa |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 165

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fca374ff865d7cd → 0x3fca374ff865d7c9 |
| old/new hash | 0x492f4e0120fe6c7b → 0xa71a43d704f3f98f |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fca374ff865d7cd / 0x3fca374ff865d7c9 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 166

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff05269595feda6 → 0x3ff05269595fede6 |
| old/new hash | 0xcaeb5d7f7b96a288 → 0x7fb5e4facd1324c8 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff05269595feda6 / 0x3ff05269595fede6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 167

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff58eb8950763a2 → 0x3ff58eb8950761a2 |
| old/new hash | 0x5dd77d97105475ce → 0x20656f2c8e1ff930 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff58eb8950763a2 / 0x3ff58eb8950761a2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 168

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fecf22c01e68a0d → 0x3fecf22c01e6aa0d |
| old/new hash | 0x51e27c01a5887afa → 0x5e1dc5029fa3d61a |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fecf22c01e68a0d / 0x3fecf22c01e6aa0d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 169

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe11c8216c61523 → 0x3fe11c8216c61423 |
| old/new hash | 0xaad121280c883175 → 0x1cb34e161961316e |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe11c8216c61523 / 0x3fe11c8216c61423 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 17

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe9e353f7ced917 → 0x3fe9e353f7ced915 |
| old/new hash | 0xf5395acf008b0c62 → 0xb7f37977081804b0 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe9e353f7ced917 / 0x3fe9e353f7ced915 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 170

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdd536933a0407e → 0x3fdd536933a0007e |
| old/new hash | 0x77835c873f2ead74 → 0x191cc3493eac44b4 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdd536933a0407e / 0x3fdd536933a0007e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 171

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea2120e1f7d73d → 0x3fea2120e1f7d73f |
| old/new hash | 0xf00e30fecf39042b → 0x14cf3bce41fa33c1 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea2120e1f7d73d / 0x3fea2120e1f7d73f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 172

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fee9c4da9003eeb → 0x3fee9c4da90036eb |
| old/new hash | 0x2b5e577018b7b423 → 0x4ca0bb4db10ff32b |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fee9c4da9003eeb / 0x3fee9c4da90036eb |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 173

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe47faa044ae85c → 0x3fe47faa0448e85c |
| old/new hash | 0xa067411deca85d3f → 0x78b27bd0433818f5 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe47faa044ae85c / 0x3fe47faa0448e85c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 174

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fecca7935760392 → 0x3fecca7935760b92 |
| old/new hash | 0x5f66a09cd7e781b7 → 0xeddbc1b1287aa10f |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fecca7935760392 / 0x3fecca7935760b92 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 175

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef52e72da122fb → 0x3fef52e72da122fa |
| old/new hash | 0x509d1141200a6943 → 0xf01301822816ef1e |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef52e72da122fb / 0x3fef52e72da122fa |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 176

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfbfd273d5bab218 → 0xbfbfd273d5b8b218 |
| old/new hash | 0xb153edfe9a7fc973 → 0x5b9e079332d553b1 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfbfd273d5bab218 / 0xbfbfd273d5b8b218 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 177

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fec2b4d8ba40d91 → 0x3fec2b4d8ba40db1 |
| old/new hash | 0xf334b7959554cd39 → 0x8c0376b0d4f14bd9 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fec2b4d8ba40d91 / 0x3fec2b4d8ba40db1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 178

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feb727dcbddb984 → 0x3feb727dcbdd3984 |
| old/new hash | 0x9f87430203181029 → 0x64a9ffba4d88d0a9 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feb727dcbddb984 / 0x3feb727dcbdd3984 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 179

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fedc69f8c21e1d2 → 0x3fedc69f8c21e1c2 |
| old/new hash | 0xfa2bf906e51c3a92 → 0xe107a3cf9c181a02 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fedc69f8c21e1d2 / 0x3fedc69f8c21e1c2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 18

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc1a9fbe76c8b44 → 0x3fc1a9fbe76c8344 |
| old/new hash | 0x1a20b6add1387e6f → 0x7174de244a16a637 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc1a9fbe76c8b44 / 0x3fc1a9fbe76c8344 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 180

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd60cc78e9f6a95 → 0x3fd60cc78e9f7a95 |
| old/new hash | 0x453779d505122df1 → 0x2bc85d02fc7c3dc1 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd60cc78e9f6a95 / 0x3fd60cc78e9f7a95 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 181

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff25a0168b5cc00 → 0x3ff25a0168b5cc02 |
| old/new hash | 0x0820f7d13e077b3a → 0xea1c5171337eb38c |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff25a0168b5cc00 / 0x3ff25a0168b5cc02 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 182

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfcbbc1acde19fc2 → 0xbfcbbc1acde19fc0 |
| old/new hash | 0x4eb31bad3bd1f812 → 0x72d95c9251e29cb4 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfcbbc1acde19fc2 / 0xbfcbbc1acde19fc0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 183

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff33382e44b6e93 → 0x3ff33382e44b6ed3 |
| old/new hash | 0x91075fd0640cee94 → 0xb2f5d05baab6cfd4 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff33382e44b6e93 / 0x3ff33382e44b6ed3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 184

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff14ea7ce0fc2ec → 0x3ff14ea7ce0f82ec |
| old/new hash | 0x63e3373e4543ede5 → 0xb9c069eaea9229a5 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff14ea7ce0fc2ec / 0x3ff14ea7ce0f82ec |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 185

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe3c23b7952d235 → 0x3fe3c23b7952d275 |
| old/new hash | 0xb55d5fd1f36e0d72 → 0x2438b8858320cb32 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe3c23b7952d235 / 0x3fe3c23b7952d275 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 186

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd86748e4755fff → 0x3fd86748e4757fff |
| old/new hash | 0x1c0db39001472578 → 0x4917eaec2f0e4c98 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd86748e4755fff / 0x3fd86748e4757fff |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 187

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fec3dad7518b0d1 → 0x3fec3dad751830d1 |
| old/new hash | 0xa937f59ef94d436e → 0x08b4281fdc8a6dee |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fec3dad7518b0d1 / 0x3fec3dad751830d1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 188

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd78e3ac0c62e4d → 0x3fd78e3ac0c62c4d |
| old/new hash | 0xd52cff78bf53a8e8 → 0xbca55d166f5687fa |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd78e3ac0c62e4d / 0x3fd78e3ac0c62c4d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 189

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe915b1422ccb3a → 0x3fe915b1422ccb7a |
| old/new hash | 0xf48731b20fb49948 → 0x0a1e23df12101b08 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe915b1422ccb3a / 0x3fe915b1422ccb7a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 19

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fed26e978d4fdf4 → 0x3fed26e978d4fdf0 |
| old/new hash | 0x21762335d5311a3f → 0x0da5d895cc592a43 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fed26e978d4fdf4 / 0x3fed26e978d4fdf0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 190

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feba5daf07bfe7e → 0x3feba5daf07bfe7f |
| old/new hash | 0xe9e20b67662adf33 → 0x32eab651cb10c74a |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feba5daf07bfe7e / 0x3feba5daf07bfe7f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 191

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe7543f1c75818d → 0x3fe7543f1c75808d |
| old/new hash | 0x6069c3a678b9c921 → 0xdc8ea899135eb352 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe7543f1c75818d / 0x3fe7543f1c75808d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 192

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdc956c0d6f544c → 0x3fdc956c0d6d544c |
| old/new hash | 0xa797f1e45af40af9 → 0x6558e7c2fa2c242f |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdc956c0d6f544c / 0x3fdc956c0d6d544c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 193

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff21c64ba94bbe5 → 0x3ff21c64ba94bae5 |
| old/new hash | 0x48cea03632cf3b36 → 0x5e4ac2b88b669c4d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff21c64ba94bbe5 / 0x3ff21c64ba94bae5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 194

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3ed5ae1cde5d1 → 0x3ff3ed5ae1cde5d3 |
| old/new hash | 0xe8f25575604c7a08 → 0x4e976cd56f4d3322 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3ed5ae1cde5d1 / 0x3ff3ed5ae1cde5d3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 195

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd5d9c27e953155 → 0x3fd5d9c27e953154 |
| old/new hash | 0xc47f0bb2fde7ebbb → 0xed035f2798b65a46 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd5d9c27e953155 / 0x3fd5d9c27e953154 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 196

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe27f3493858362 → 0x3fe27f349385a362 |
| old/new hash | 0x3651489c884e3426 → 0x76ca04e47e4c1406 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe27f3493858362 / 0x3fe27f349385a362 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 197

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff2cdeb0fadf2ed → 0x3ff2cdeb0fadf2e5 |
| old/new hash | 0xe9d96454a9fc0427 → 0xcf971aa9ac46a26f |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff2cdeb0fadf2ed / 0x3ff2cdeb0fadf2e5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 198

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ffb4e22a2c23747 → 0x3ffb4e22a2c23647 |
| old/new hash | 0xf0bc74d3766caa0f → 0xfa40eeadd559ca04 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ffb4e22a2c23747 / 0x3ffb4e22a2c23647 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 199

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc7d41743e963df → 0x3fc7d41743e963db |
| old/new hash | 0x7f2e6eb465d59bf4 → 0xad6954b46878a1f0 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc7d41743e963df / 0x3fc7d41743e963db |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 2

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff0bc6a7ef9db23 → 0x3ff0bc6a7ef95b23 |
| old/new hash | 0x3d3962e7df4d4091 → 0xfcf3f527c2524911 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff0bc6a7ef9db23 / 0x3ff0bc6a7ef95b23 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 20

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe010624dd2f1aa → 0x3fe010624dd2f1ea |
| old/new hash | 0xdaff273cdbd56cd4 → 0xe8016189415cb694 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe010624dd2f1aa / 0x3fe010624dd2f1ea |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 200

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe0b242070b8cfc → 0x3fe0b242070b8cfe |
| old/new hash | 0xa1cf7e063d81fff8 → 0x45bd696c696c393a |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe0b242070b8cfc / 0x3fe0b242070b8cfe |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 201

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe81001d5c31594 → 0x3fe81001d5c31494 |
| old/new hash | 0xa987f49f9a31d830 → 0x86586c4eb4c85487 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe81001d5c31594 / 0x3fe81001d5c31494 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 202

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fecbb0a2ca9ac37 → 0x3fecbb0a2ca92c37 |
| old/new hash | 0x4788e475be51faef → 0x074376b5a157036f |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fecbb0a2ca9ac37 / 0x3fecbb0a2ca92c37 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 21

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe05a1cac083127 → 0x3fe05a1cac083527 |
| old/new hash | 0xc4533981f2a82050 → 0x348847aa3bcbbb0c |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe05a1cac083127 / 0x3fe05a1cac083527 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 22

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feb8d4fdf3b645a → 0x3feb8d4fdf3b745a |
| old/new hash | 0xf95cf234a4a91049 → 0x7a95720d3b95e279 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feb8d4fdf3b645a / 0x3feb8d4fdf3b745a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 23

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4076c00000000000 → 0x4076c00000002000 |
| old/new hash | 0x1c95f97d74ad03e5 → 0x7301eac53be1ad85 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4076c00000000000 / 0x4076c00000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 24

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083100000000000 → 0x4083100000000800 |
| old/new hash | 0xd43ecb7eff779458 → 0xa9aa6f2c70d82400 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083100000000000 / 0x4083100000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 25

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088700000000000 → 0x4088700000000002 |
| old/new hash | 0xe5f72d7f9985d0eb → 0x53439f6b0fa70da9 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088700000000000 / 0x4088700000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 26

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdc083126e978d5 → 0x3fdc083126e97895 |
| old/new hash | 0x61e89d0d38234561 → 0xd676620678bbe7a1 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdc083126e978d5 / 0x3fdc083126e97895 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 27

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd926e978d4fdf4 → 0x3fd926e978d4fde4 |
| old/new hash | 0x219f2335d5541f53 → 0xea45bc96a0c817e3 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd926e978d4fdf4 / 0x3fd926e978d4fde4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 28

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff1c28f5c28f5c3 → 0x3ff1c28f5c28f5c2 |
| old/new hash | 0x0b93646eb7e4738a → 0x93ef6a3635fa72f3 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff1c28f5c28f5c3 / 0x3ff1c28f5c28f5c2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 29

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4079e00000000000 → 0x4079e00000000200 |
| old/new hash | 0x09ce377cd9b8a402 → 0x69de0e9043326c68 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4079e00000000000 / 0x4079e00000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 3

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc0624dd2f1a9fc → 0x3fc0624dd2f3a9fc |
| old/new hash | 0x6af19e0db6400b01 → 0x266ae9b3d9deb9d7 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc0624dd2f1a9fc / 0x3fc0624dd2f3a9fc |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 30

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea24dd2f1a9fbf → 0x3fea24dd2f1a9fbd |
| old/new hash | 0x0962ea40c7aaa6ac → 0xeb86ce822e3aed52 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea24dd2f1a9fbf / 0x3fea24dd2f1a9fbd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 31

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408a900000000000 → 0x408a900000000020 |
| old/new hash | 0x7c03817c8880dfb9 → 0x04d762a2ce68ced9 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408a900000000000 / 0x408a900000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 32

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe0cccccccccccd → 0x3fe0cccccccc8ccd |
| old/new hash | 0x317e432ebb25af8b → 0x0f61a43f6a155e4b |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe0cccccccccccd / 0x3fe0cccccccc8ccd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 33

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408cb00000000000 → 0x408cb00000000100 |
| old/new hash | 0x6a4e857bee75864f → 0x63a669f721a033d4 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408cb00000000000 / 0x408cb00000000100 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 34

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4078300000000000 → 0x4078300000000020 |
| old/new hash | 0xbbcecd7e5fb458bb → 0xc65f6ea0f855385b |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4078300000000000 / 0x4078300000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 35

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4055800000000000 → 0x4055800000001000 |
| old/new hash | 0xf45adf7c3c7f0f6e → 0x9d1366d71d73e81e |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4055800000000000 / 0x4055800000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 36

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe604189374bc6b → 0x3fe604189374bd6b |
| old/new hash | 0x43ca7c53d0d7726a → 0x9fd78b20420e4ff1 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe604189374bc6b / 0x3fe604189374bd6b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 37

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff5c28f5c28f5c3 → 0x3ff5c28f5c2af5c3 |
| old/new hash | 0x0ba0e46eb7efd766 → 0xa7b99bdedf8d14b0 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff5c28f5c28f5c3 / 0x3ff5c28f5c2af5c3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 38

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x405e400000000000 → 0x405e400000000008 |
| old/new hash | 0x71a5897fe8f27ebd → 0x163ae1c5cdb0dc35 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x405e400000000000 / 0x405e400000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 39

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x405f400000000000 → 0x405f400000000800 |
| old/new hash | 0x71a1a37fe8eec214 → 0x46d7672d5a21f8ac |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x405f400000000000 / 0x405f400000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 4

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff420c49ba5e354 → 0x3ff420c49ba5e355 |
| old/new hash | 0xe3a18f7b87f7ea43 → 0x1782b828ebc0b032 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff420c49ba5e354 / 0x3ff420c49ba5e355 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 40

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fde24dd2f1a9fbf → 0x3fde24dd2f1a9ebf |
| old/new hash | 0x08cd6a40c72ba938 → 0xb590414c4fbf8317 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fde24dd2f1a9fbf / 0x3fde24dd2f1a9ebf |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 41

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080880000000000 → 0x4080880000001000 |
| old/new hash | 0xafa7757c15c02ecb → 0x571a3cd6f5a0b19b |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080880000000000 / 0x4080880000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 42

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fed810624dd2f1b → 0x3fed810624dd2f0b |
| old/new hash | 0xc560c2dd20e1fba5 → 0x757807dd4ef5be95 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fed810624dd2f1b / 0x3fed810624dd2f0b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 43

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd395810624dd2f → 0x3fd395810624d92f |
| old/new hash | 0xddd6ab1c9ec91461 → 0x6bbbc5681af371bd |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd395810624dd2f / 0x3fd395810624d92f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 44

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4066800000000000 → 0x4066800000020000 |
| old/new hash | 0xf3b3d97c3bf0bb15 → 0xe4e9a91b48d10a07 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4066800000000000 / 0x4066800000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 45

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fee872b020c49ba → 0x3fee872b020c499a |
| old/new hash | 0x805d744fcd34dd4d → 0xfb6ad113fc07bbed |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fee872b020c49ba / 0x3fee872b020c499a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 46

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fedf3b645a1cac1 → 0x3fedf3b645a1eac1 |
| old/new hash | 0x77823037f6113381 → 0x43d27904e2acd561 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fedf3b645a1cac1 / 0x3fedf3b645a1eac1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 47

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4089680000000000 → 0x4089680000000002 |
| old/new hash | 0x16461f7f23f066ca → 0x1191416aeb766a38 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4089680000000000 / 0x4089680000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 48

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408f000000000000 → 0x408f000000000004 |
| old/new hash | 0x4999837eb0ec1d04 → 0xc5696fa2dc922c40 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408f000000000000 / 0x408f000000000004 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 49

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe36c8b43958106 → 0x3fe36c8b43958102 |
| old/new hash | 0xa7cd433a26af44ff → 0x2578550e94c86993 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe36c8b43958106 / 0x3fe36c8b43958102 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 5

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd0000000000000 → 0xbfd0000000000100 |
| old/new hash | 0x4ac0aa7eb1e6715a → 0x805520f45bbdc935 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd0000000000000 / 0xbfd0000000000100 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 50

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4076400000000000 → 0x4076400000001000 |
| old/new hash | 0x7153797fe8ac5965 → 0x1d7200dacc845b15 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4076400000000000 / 0x4076400000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 51

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fefbe76c8b43958 → 0x3fefbe76c8b47958 |
| old/new hash | 0xaaf4edc580a7cf4e → 0xac7f36f0347aa08e |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fefbe76c8b43958 / 0x3fefbe76c8b47958 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 52

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe96872b020c49c → 0x3fe96872b020c59c |
| old/new hash | 0x43a6296c77bac505 → 0x32e518fcf351843a |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe96872b020c49c / 0x3fe96872b020c59c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 53

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe883126e978d50 → 0x3fe883126e978950 |
| old/new hash | 0xfb42de2ad78393eb → 0x79c65ed836bd8e47 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe883126e978d50 / 0x3fe883126e978950 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 54

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4073500000000000 → 0x4073500000001000 |
| old/new hash | 0xfdfa6b8038eca768 → 0x940f92da7f0b2ff8 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4073500000000000 / 0x4073500000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 55

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x406da00000000000 → 0x406da00000000040 |
| old/new hash | 0xdd93af7b9e24bed6 → 0x4772f1c34366ad16 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x406da00000000000 / 0x406da00000000040 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 56

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4078c00000000000 → 0x4078c00000020000 |
| old/new hash | 0x1c73fd7d7490244b → 0xb8de351a0d64b799 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4078c00000000000 / 0x4078c00000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 57

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4084a80000000000 → 0x4084a80000000080 |
| old/new hash | 0x971fad7b75e8bd0f → 0xc69d28fae925808f |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4084a80000000000 / 0x4084a80000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 58

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408a580000000000 → 0x408a580000000008 |
| old/new hash | 0xb609c9800f6d43b1 → 0xe38451c6413ad0d9 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408a580000000000 / 0x408a580000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 59

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd4395810624dd3 → 0xbfd4395810624dd1 |
| old/new hash | 0xf01522948884c5f7 → 0x661af8b5697b0a69 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd4395810624dd3 / 0xbfd4395810624dd1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 6

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfdf1a9fbe76c8b4 → 0xbfdf1a9fbe76c8bc |
| old/new hash | 0x1474778cead2ffdc → 0xa231ad6d1c270664 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfdf1a9fbe76c8b4 / 0xbfdf1a9fbe76c8bc |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 60

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc3f7ced916872c → 0x3fc3f7ced9168f2c |
| old/new hash | 0xe5dce89c1cad32b2 → 0x64eeca3adeabf7aa |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc3f7ced916872c / 0x3fc3f7ced9168f2c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 61

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc0e5604189374c → 0x3fc0e5604189274c |
| old/new hash | 0xdd9f0a4a47cf1eb2 → 0x19d6969673d068c2 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc0e5604189374c / 0x3fc0e5604189274c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 62

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef0a3d70a3d70a → 0x3fef0a3d70a3d70b |
| old/new hash | 0x828c86134eb1d42a → 0x4fb94367cc868837 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef0a3d70a3d70a / 0x3fef0a3d70a3d70b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 63

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfdf6c8b43958106 → 0xbfdf6c8b43958107 |
| old/new hash | 0xa7dac33a26baa8db → 0xa00938c697ac0046 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfdf6c8b43958106 / 0xbfdf6c8b43958107 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 64

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4073800000000000 → 0x4073800000002000 |
| old/new hash | 0xf3d9bb7c3c115758 → 0x9f022cc67743a378 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4073800000000000 / 0x4073800000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 65

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3ced916872b02 → 0x3ff3ced916872b03 |
| old/new hash | 0xdf5599b89a9ecb54 → 0xf3eff1a33736811d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3ced916872b02 / 0x3ff3ced916872b03 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 66

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080300000000000 → 0x4080300000020000 |
| old/new hash | 0xbbb39d7e5f9d3f73 → 0x1b1bb519239bd7e1 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080300000000000 / 0x4080300000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 67

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407ad00000000000 → 0x407ad00000000800 |
| old/new hash | 0xa924a17dc4d84249 → 0x28af65301ec3c7a1 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407ad00000000000 / 0x407ad00000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 68

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4077100000000000 → 0x4077100000008000 |
| old/new hash | 0xd1f5c37efd861b4c → 0x28b7fe56139cadcc |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4077100000000000 / 0x4077100000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 69

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081c00000000000 → 0x4081c00000000100 |
| old/new hash | 0x1f4f277d76fdc53a → 0x037df7f80d2d8a31 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081c00000000000 / 0x4081c00000000100 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 7

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088a00000000000 → 0x4088a00000000001 |
| old/new hash | 0xdfa8bd7b9fe9357b → 0x91581678b4434aaa |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088a00000000000 / 0x4088a00000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 70

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3f9999999999999d → 0x3f9999999999999f |
| old/new hash | 0xe3cfd5c3d6969219 → 0x92836865613d1d0b |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3f9999999999999d / 0x3f9999999999999f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 71

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfcc8b4395810625 → 0xbfcc8b4395810605 |
| old/new hash | 0x2cede1a85d80c9cd → 0xf8c2c08be907586d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfcc8b4395810625 / 0xbfcc8b4395810605 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 72

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408c180000000000 → 0x408c180000000400 |
| old/new hash | 0x8bbfed7ed57fc567 → 0xa41dcba81f6c147b |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408c180000000000 / 0x408c180000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 73

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef22d0e5604189 → 0x3fef22d0e5604089 |
| old/new hash | 0xa2fa1113ae023b56 → 0x84a7e583ffac53a1 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef22d0e5604189 / 0x3fef22d0e5604089 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 74

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef8d4fdf3b645a → 0x3fef8d4fdf3b745a |
| old/new hash | 0xf94f7234a49dac6d → 0x7a87f20d3b8a7e9d |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef8d4fdf3b645a / 0x3fef8d4fdf3b745a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 75

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fa999999999999b → 0x3fa999999999b99b |
| old/new hash | 0x1f8e6da556cb700f → 0x073051e268dfe3ef |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fa999999999999b / 0x3fa999999999b99b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 76

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff09374bc6a7efa → 0x3ff09374bc6a76fa |
| old/new hash | 0xf08d067fed91bc61 → 0x8960be0341f9a209 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff09374bc6a7efa / 0x3ff09374bc6a76fa |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 77

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4085b80000000000 → 0x4085b80000000008 |
| old/new hash | 0x21b3f77bc465c496 → 0xce809fc5a45fab0e |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4085b80000000000 / 0x4085b80000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 78

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe65604189374bc → 0x3fe656041893743c |
| old/new hash | 0x42488d585158be85 → 0x52aa44cbb7e0df05 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe65604189374bc / 0x3fe656041893743c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 79

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd7ef9db22d0e56 → 0xbfd7ef9db22d0e52 |
| old/new hash | 0xad80ec83e44ac2ee → 0xfe3eb7757048979a |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd7ef9db22d0e56 / 0xbfd7ef9db22d0e52 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 8

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fb3333333333334 → 0x3fb3333333331334 |
| old/new hash | 0xf7a4d9624489fea8 → 0x1fd31ff2fc996508 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fb3333333333334 / 0x3fb3333333331334 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 80

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe6b851eb851eb8 → 0x3fe6b851eb855eb8 |
| old/new hash | 0x6be7e9f13ac0a1a7 → 0xd20c1082d8979567 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe6b851eb851eb8 / 0x3fe6b851eb855eb8 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 81

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe395810624dd2f → 0x3fe395810624dd2e |
| old/new hash | 0xde79ab1c9f5375b1 → 0x0883ddfac9ddeedc |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe395810624dd2f / 0x3fe395810624dd2e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 82

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff7eb851eb851ec → 0x3ff7eb851eb855ec |
| old/new hash | 0xc0aed28936e3f33c → 0x65819e7117a6af80 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff7eb851eb851ec / 0x3ff7eb851eb855ec |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 83

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407e600000000000 → 0x407e600000008000 |
| old/new hash | 0x5e95697f4dbfc97d → 0xb557a45663d65bfd |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407e600000000000 / 0x407e600000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 84

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4077c00000000000 → 0x4077c00000000010 |
| old/new hash | 0x1c93137d74aafa3c → 0xb714c40baf43082c |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4077c00000000000 / 0x4077c00000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 85

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408d080000000000 → 0x408d080000000200 |
| old/new hash | 0x0124577e86fc1e0e → 0x8ef96e932d5993b4 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408d080000000000 / 0x408d080000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 86

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4071e00000000000 → 0x4071e00000010000 |
| old/new hash | 0x09e8e77cd9cee3ca → 0xd5a30f47755da403 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4071e00000000000 / 0x4071e00000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 87

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfdab020c49ba5e3 → 0xbfdab020c49ba4e3 |
| old/new hash | 0x94c1db6f0f635a4b → 0x16050ad9cd0bc4b4 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfdab020c49ba5e3 / 0xbfdab020c49ba4e3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 88

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fb0e5604189374d → 0x3fb0e5604189364d |
| old/new hash | 0x4f74ee5cc07d911b → 0x702357d5c802086c |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fb0e5604189374d / 0x3fb0e5604189364d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 89

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083300000000000 → 0x4083300000000001 |
| old/new hash | 0xbba8eb7e5f93bc78 → 0xc71430768eaabce9 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083300000000000 / 0x4083300000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 9

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407b800000000000 → 0x407b800000000100 |
| old/new hash | 0xf3be0b7c3bf96490 → 0xd721f3f6d17d9eeb |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407b800000000000 / 0x407b800000000100 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 90

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fce76c8b4395811 → 0x3fce76c8b4395851 |
| old/new hash | 0x7dc185b0f71fae36 → 0xe6fc06f85957fb76 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fce76c8b4395811 / 0x3fce76c8b4395851 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 91

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdaf1a9fbe76c8b → 0x3fdaf1a9fbe72c8b |
| old/new hash | 0xed171048f0c8bc57 → 0xf3fb074db66bdc97 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdaf1a9fbe76c8b / 0x3fdaf1a9fbe72c8b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 92

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081f80000000000 → 0x4081f80000001000 |
| old/new hash | 0x4c051f7cfe59e2b2 → 0x0c0cc6d87e1c8a62 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081f80000000000 / 0x4081f80000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 93

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087400000000000 → 0x4087400000000001 |
| old/new hash | 0x70ad737fe81fb80c → 0x0061f8746c1a07bd |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087400000000000 / 0x4087400000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 94

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff64dd2f1a9fbe8 → 0x3ff64dd2f1a9fbf8 |
| old/new hash | 0x3430709ad9b90ed2 → 0xa877286418d89642 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff64dd2f1a9fbe8 / 0x3ff64dd2f1a9fbf8 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 95

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff7916872b020c5 → 0x3ff7916872b060c5 |
| old/new hash | 0x6ca1ff97e7fbb871 → 0xaaf6e9600dedcb31 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff7916872b020c5 / 0x3ff7916872b060c5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 96

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407bb00000000000 → 0x407bb00000002000 |
| old/new hash | 0x67071b7bebac59c0 → 0x3e41ccc76250bea0 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407bb00000000000 / 0x407bb00000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 97

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff09fbe76c8b439 → 0x3ff09fbe76c8b039 |
| old/new hash | 0x97b31cc72d5d1b7a → 0xa51013c7fbce8f46 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff09fbe76c8b439 / 0x3ff09fbe76c8b039 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 98

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408ee80000000000 → 0x408ee80000000200 |
| old/new hash | 0xc4f8d17cb2dce3c5 → 0x2516c0901c63124f |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408ee80000000000 / 0x408ee80000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 99

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff353f7ced91687 → 0x3ff353f7ced91287 |
| old/new hash | 0xd63c7907fe724a7d → 0xee638effca4ab271 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff353f7ced91687 / 0x3ff353f7ced91287 |
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
| 7 | chain_end | — | 1212 | 5 |

### fault 10（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 54 | — |
| 2 | carrier_state | L1 | 55 | 54 |
| 3 | operand_read | L2 | 56 | 55 |
| 4 | execute | L3 | 57 | 56 |
| 5 | prf_writeback | L4 | 58 | 57 |
| 6 | commit | L5 | 59 | 58 |
| 7 | chain_end | — | 1221 | 59 |

### fault 100（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 594 | — |
| 2 | carrier_state | L1 | 595 | 594 |
| 3 | operand_read | L2 | 596 | 595 |
| 4 | execute | L3 | 597 | 596 |
| 5 | prf_writeback | L4 | 598 | 597 |
| 6 | commit | L5 | 599 | 598 |
| 7 | chain_end | — | 1311 | 599 |

### fault 101（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 600 | — |
| 2 | carrier_state | L1 | 601 | 600 |
| 3 | operand_read | L2 | 602 | 601 |
| 4 | execute | L3 | 603 | 602 |
| 5 | prf_writeback | L4 | 604 | 603 |
| 6 | commit | L5 | 605 | 604 |
| 7 | chain_end | — | 1312 | 605 |

### fault 102（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 606 | — |
| 2 | carrier_state | L1 | 607 | 606 |
| 3 | operand_read | L2 | 608 | 607 |
| 4 | execute | L3 | 609 | 608 |
| 5 | prf_writeback | L4 | 610 | 609 |
| 6 | commit | L5 | 611 | 610 |
| 7 | chain_end | — | 1313 | 611 |

### fault 103（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 612 | — |
| 2 | carrier_state | L1 | 613 | 612 |
| 3 | operand_read | L2 | 614 | 613 |
| 4 | execute | L3 | 615 | 614 |
| 5 | prf_writeback | L4 | 616 | 615 |
| 6 | commit | L5 | 617 | 616 |
| 7 | chain_end | — | 1314 | 617 |

### fault 104（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 618 | — |
| 2 | carrier_state | L1 | 619 | 618 |
| 3 | operand_read | L2 | 620 | 619 |
| 4 | execute | L3 | 621 | 620 |
| 5 | prf_writeback | L4 | 622 | 621 |
| 6 | commit | L5 | 623 | 622 |
| 7 | chain_end | — | 1315 | 623 |

### fault 105（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 624 | — |
| 2 | carrier_state | L1 | 625 | 624 |
| 3 | operand_read | L2 | 626 | 625 |
| 4 | execute | L3 | 627 | 626 |
| 5 | prf_writeback | L4 | 628 | 627 |
| 6 | commit | L5 | 629 | 628 |
| 7 | chain_end | — | 1316 | 629 |

### fault 106（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 630 | — |
| 2 | carrier_state | L1 | 631 | 630 |
| 3 | operand_read | L2 | 632 | 631 |
| 4 | execute | L3 | 633 | 632 |
| 5 | prf_writeback | L4 | 634 | 633 |
| 6 | commit | L5 | 635 | 634 |
| 7 | chain_end | — | 1317 | 635 |

### fault 107（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 636 | — |
| 2 | carrier_state | L1 | 637 | 636 |
| 3 | operand_read | L2 | 638 | 637 |
| 4 | execute | L3 | 639 | 638 |
| 5 | prf_writeback | L4 | 640 | 639 |
| 6 | commit | L5 | 641 | 640 |
| 7 | chain_end | — | 1318 | 641 |

### fault 108（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 642 | — |
| 2 | carrier_state | L1 | 643 | 642 |
| 3 | operand_read | L2 | 644 | 643 |
| 4 | execute | L3 | 645 | 644 |
| 5 | prf_writeback | L4 | 646 | 645 |
| 6 | commit | L5 | 647 | 646 |
| 7 | chain_end | — | 1319 | 647 |

### fault 109（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 648 | — |
| 2 | carrier_state | L1 | 649 | 648 |
| 3 | operand_read | L2 | 650 | 649 |
| 4 | execute | L3 | 651 | 650 |
| 5 | prf_writeback | L4 | 652 | 651 |
| 6 | commit | L5 | 653 | 652 |
| 7 | chain_end | — | 1320 | 653 |

### fault 11（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 60 | — |
| 2 | carrier_state | L1 | 61 | 60 |
| 3 | operand_read | L2 | 62 | 61 |
| 4 | execute | L3 | 63 | 62 |
| 5 | prf_writeback | L4 | 64 | 63 |
| 6 | commit | L5 | 65 | 64 |
| 7 | chain_end | — | 1222 | 65 |

### fault 110（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 654 | — |
| 2 | carrier_state | L1 | 655 | 654 |
| 3 | operand_read | L2 | 656 | 655 |
| 4 | execute | L3 | 657 | 656 |
| 5 | prf_writeback | L4 | 658 | 657 |
| 6 | commit | L5 | 659 | 658 |
| 7 | chain_end | — | 1321 | 659 |

### fault 111（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 660 | — |
| 2 | carrier_state | L1 | 661 | 660 |
| 3 | operand_read | L2 | 662 | 661 |
| 4 | execute | L3 | 663 | 662 |
| 5 | prf_writeback | L4 | 664 | 663 |
| 6 | commit | L5 | 665 | 664 |
| 7 | chain_end | — | 1322 | 665 |

### fault 112（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 666 | — |
| 2 | carrier_state | L1 | 667 | 666 |
| 3 | operand_read | L2 | 668 | 667 |
| 4 | execute | L3 | 669 | 668 |
| 5 | prf_writeback | L4 | 670 | 669 |
| 6 | commit | L5 | 671 | 670 |
| 7 | chain_end | — | 1323 | 671 |

### fault 113（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 672 | — |
| 2 | carrier_state | L1 | 673 | 672 |
| 3 | operand_read | L2 | 674 | 673 |
| 4 | execute | L3 | 675 | 674 |
| 5 | prf_writeback | L4 | 676 | 675 |
| 6 | commit | L5 | 677 | 676 |
| 7 | chain_end | — | 1324 | 677 |

### fault 114（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 678 | — |
| 2 | carrier_state | L1 | 679 | 678 |
| 3 | operand_read | L2 | 680 | 679 |
| 4 | execute | L3 | 681 | 680 |
| 5 | prf_writeback | L4 | 682 | 681 |
| 6 | commit | L5 | 683 | 682 |
| 7 | chain_end | — | 1325 | 683 |

### fault 115（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 684 | — |
| 2 | carrier_state | L1 | 685 | 684 |
| 3 | operand_read | L2 | 686 | 685 |
| 4 | execute | L3 | 687 | 686 |
| 5 | prf_writeback | L4 | 688 | 687 |
| 6 | commit | L5 | 689 | 688 |
| 7 | chain_end | — | 1326 | 689 |

### fault 116（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 690 | — |
| 2 | carrier_state | L1 | 691 | 690 |
| 3 | operand_read | L2 | 692 | 691 |
| 4 | execute | L3 | 693 | 692 |
| 5 | prf_writeback | L4 | 694 | 693 |
| 6 | commit | L5 | 695 | 694 |
| 7 | chain_end | — | 1327 | 695 |

### fault 117（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 696 | — |
| 2 | carrier_state | L1 | 697 | 696 |
| 3 | operand_read | L2 | 698 | 697 |
| 4 | execute | L3 | 699 | 698 |
| 5 | prf_writeback | L4 | 700 | 699 |
| 6 | commit | L5 | 701 | 700 |
| 7 | chain_end | — | 1328 | 701 |

### fault 118（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 702 | — |
| 2 | carrier_state | L1 | 703 | 702 |
| 3 | operand_read | L2 | 704 | 703 |
| 4 | execute | L3 | 705 | 704 |
| 5 | prf_writeback | L4 | 706 | 705 |
| 6 | commit | L5 | 707 | 706 |
| 7 | chain_end | — | 1329 | 707 |

### fault 119（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 708 | — |
| 2 | carrier_state | L1 | 709 | 708 |
| 3 | operand_read | L2 | 710 | 709 |
| 4 | execute | L3 | 711 | 710 |
| 5 | prf_writeback | L4 | 712 | 711 |
| 6 | commit | L5 | 713 | 712 |
| 7 | chain_end | — | 1330 | 713 |

### fault 12（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 66 | — |
| 2 | carrier_state | L1 | 67 | 66 |
| 3 | operand_read | L2 | 68 | 67 |
| 4 | execute | L3 | 69 | 68 |
| 5 | prf_writeback | L4 | 70 | 69 |
| 6 | commit | L5 | 71 | 70 |
| 7 | chain_end | — | 1223 | 71 |

### fault 120（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 714 | — |
| 2 | carrier_state | L1 | 715 | 714 |
| 3 | operand_read | L2 | 716 | 715 |
| 4 | execute | L3 | 717 | 716 |
| 5 | prf_writeback | L4 | 718 | 717 |
| 6 | commit | L5 | 719 | 718 |
| 7 | chain_end | — | 1331 | 719 |

### fault 121（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 720 | — |
| 2 | carrier_state | L1 | 721 | 720 |
| 3 | operand_read | L2 | 722 | 721 |
| 4 | execute | L3 | 723 | 722 |
| 5 | prf_writeback | L4 | 724 | 723 |
| 6 | commit | L5 | 725 | 724 |
| 7 | chain_end | — | 1332 | 725 |

### fault 122（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 726 | — |
| 2 | carrier_state | L1 | 727 | 726 |
| 3 | operand_read | L2 | 728 | 727 |
| 4 | execute | L3 | 729 | 728 |
| 5 | prf_writeback | L4 | 730 | 729 |
| 6 | commit | L5 | 731 | 730 |
| 7 | chain_end | — | 1333 | 731 |

### fault 123（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 732 | — |
| 2 | carrier_state | L1 | 733 | 732 |
| 3 | operand_read | L2 | 734 | 733 |
| 4 | execute | L3 | 735 | 734 |
| 5 | prf_writeback | L4 | 736 | 735 |
| 6 | commit | L5 | 737 | 736 |
| 7 | chain_end | — | 1334 | 737 |

### fault 124（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 738 | — |
| 2 | carrier_state | L1 | 739 | 738 |
| 3 | operand_read | L2 | 740 | 739 |
| 4 | execute | L3 | 741 | 740 |
| 5 | prf_writeback | L4 | 742 | 741 |
| 6 | commit | L5 | 743 | 742 |
| 7 | chain_end | — | 1335 | 743 |

### fault 125（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 744 | — |
| 2 | carrier_state | L1 | 745 | 744 |
| 3 | operand_read | L2 | 746 | 745 |
| 4 | execute | L3 | 747 | 746 |
| 5 | prf_writeback | L4 | 748 | 747 |
| 6 | commit | L5 | 749 | 748 |
| 7 | chain_end | — | 1336 | 749 |

### fault 126（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 750 | — |
| 2 | carrier_state | L1 | 751 | 750 |
| 3 | operand_read | L2 | 752 | 751 |
| 4 | execute | L3 | 753 | 752 |
| 5 | prf_writeback | L4 | 754 | 753 |
| 6 | commit | L5 | 755 | 754 |
| 7 | chain_end | — | 1337 | 755 |

### fault 127（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 756 | — |
| 2 | carrier_state | L1 | 757 | 756 |
| 3 | operand_read | L2 | 758 | 757 |
| 4 | execute | L3 | 759 | 758 |
| 5 | prf_writeback | L4 | 760 | 759 |
| 6 | commit | L5 | 761 | 760 |
| 7 | chain_end | — | 1338 | 761 |

### fault 128（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 762 | — |
| 2 | carrier_state | L1 | 763 | 762 |
| 3 | operand_read | L2 | 764 | 763 |
| 4 | execute | L3 | 765 | 764 |
| 5 | prf_writeback | L4 | 766 | 765 |
| 6 | commit | L5 | 767 | 766 |
| 7 | chain_end | — | 1339 | 767 |

### fault 129（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 768 | — |
| 2 | carrier_state | L1 | 769 | 768 |
| 3 | operand_read | L2 | 770 | 769 |
| 4 | execute | L3 | 771 | 770 |
| 5 | prf_writeback | L4 | 772 | 771 |
| 6 | commit | L5 | 773 | 772 |
| 7 | chain_end | — | 1340 | 773 |

### fault 13（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 72 | — |
| 2 | carrier_state | L1 | 73 | 72 |
| 3 | operand_read | L2 | 74 | 73 |
| 4 | execute | L3 | 75 | 74 |
| 5 | prf_writeback | L4 | 76 | 75 |
| 6 | commit | L5 | 77 | 76 |
| 7 | chain_end | — | 1224 | 77 |

### fault 130（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 774 | — |
| 2 | carrier_state | L1 | 775 | 774 |
| 3 | operand_read | L2 | 776 | 775 |
| 4 | execute | L3 | 777 | 776 |
| 5 | prf_writeback | L4 | 778 | 777 |
| 6 | commit | L5 | 779 | 778 |
| 7 | chain_end | — | 1341 | 779 |

### fault 131（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 780 | — |
| 2 | carrier_state | L1 | 781 | 780 |
| 3 | operand_read | L2 | 782 | 781 |
| 4 | execute | L3 | 783 | 782 |
| 5 | prf_writeback | L4 | 784 | 783 |
| 6 | commit | L5 | 785 | 784 |
| 7 | chain_end | — | 1342 | 785 |

### fault 132（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 786 | — |
| 2 | carrier_state | L1 | 787 | 786 |
| 3 | operand_read | L2 | 788 | 787 |
| 4 | execute | L3 | 789 | 788 |
| 5 | prf_writeback | L4 | 790 | 789 |
| 6 | commit | L5 | 791 | 790 |
| 7 | chain_end | — | 1343 | 791 |

### fault 133（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 792 | — |
| 2 | carrier_state | L1 | 793 | 792 |
| 3 | operand_read | L2 | 794 | 793 |
| 4 | execute | L3 | 795 | 794 |
| 5 | prf_writeback | L4 | 796 | 795 |
| 6 | commit | L5 | 797 | 796 |
| 7 | chain_end | — | 1344 | 797 |

### fault 134（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 798 | — |
| 2 | carrier_state | L1 | 799 | 798 |
| 3 | operand_read | L2 | 800 | 799 |
| 4 | execute | L3 | 801 | 800 |
| 5 | prf_writeback | L4 | 802 | 801 |
| 6 | commit | L5 | 803 | 802 |
| 7 | chain_end | — | 1345 | 803 |

### fault 135（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 804 | — |
| 2 | carrier_state | L1 | 805 | 804 |
| 3 | operand_read | L2 | 806 | 805 |
| 4 | execute | L3 | 807 | 806 |
| 5 | prf_writeback | L4 | 808 | 807 |
| 6 | commit | L5 | 809 | 808 |
| 7 | chain_end | — | 1346 | 809 |

### fault 136（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 810 | — |
| 2 | carrier_state | L1 | 811 | 810 |
| 3 | operand_read | L2 | 812 | 811 |
| 4 | execute | L3 | 813 | 812 |
| 5 | prf_writeback | L4 | 814 | 813 |
| 6 | commit | L5 | 815 | 814 |
| 7 | chain_end | — | 1347 | 815 |

### fault 137（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 816 | — |
| 2 | carrier_state | L1 | 817 | 816 |
| 3 | operand_read | L2 | 818 | 817 |
| 4 | execute | L3 | 819 | 818 |
| 5 | prf_writeback | L4 | 820 | 819 |
| 6 | commit | L5 | 821 | 820 |
| 7 | chain_end | — | 1348 | 821 |

### fault 138（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 822 | — |
| 2 | carrier_state | L1 | 823 | 822 |
| 3 | operand_read | L2 | 824 | 823 |
| 4 | execute | L3 | 825 | 824 |
| 5 | prf_writeback | L4 | 826 | 825 |
| 6 | commit | L5 | 827 | 826 |
| 7 | chain_end | — | 1349 | 827 |

### fault 139（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 828 | — |
| 2 | carrier_state | L1 | 829 | 828 |
| 3 | operand_read | L2 | 830 | 829 |
| 4 | execute | L3 | 831 | 830 |
| 5 | prf_writeback | L4 | 832 | 831 |
| 6 | commit | L5 | 833 | 832 |
| 7 | chain_end | — | 1350 | 833 |

### fault 14（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 78 | — |
| 2 | carrier_state | L1 | 79 | 78 |
| 3 | operand_read | L2 | 80 | 79 |
| 4 | execute | L3 | 81 | 80 |
| 5 | prf_writeback | L4 | 82 | 81 |
| 6 | commit | L5 | 83 | 82 |
| 7 | chain_end | — | 1225 | 83 |

### fault 140（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 834 | — |
| 2 | carrier_state | L1 | 835 | 834 |
| 3 | operand_read | L2 | 836 | 835 |
| 4 | execute | L3 | 837 | 836 |
| 5 | prf_writeback | L4 | 838 | 837 |
| 6 | commit | L5 | 839 | 838 |
| 7 | chain_end | — | 1351 | 839 |

### fault 141（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 840 | — |
| 2 | carrier_state | L1 | 841 | 840 |
| 3 | operand_read | L2 | 842 | 841 |
| 4 | execute | L3 | 843 | 842 |
| 5 | prf_writeback | L4 | 844 | 843 |
| 6 | commit | L5 | 845 | 844 |
| 7 | chain_end | — | 1352 | 845 |

### fault 142（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 846 | — |
| 2 | carrier_state | L1 | 847 | 846 |
| 3 | operand_read | L2 | 848 | 847 |
| 4 | execute | L3 | 849 | 848 |
| 5 | prf_writeback | L4 | 850 | 849 |
| 6 | commit | L5 | 851 | 850 |
| 7 | chain_end | — | 1353 | 851 |

### fault 143（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 852 | — |
| 2 | carrier_state | L1 | 853 | 852 |
| 3 | operand_read | L2 | 854 | 853 |
| 4 | execute | L3 | 855 | 854 |
| 5 | prf_writeback | L4 | 856 | 855 |
| 6 | commit | L5 | 857 | 856 |
| 7 | chain_end | — | 1354 | 857 |

### fault 144（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 858 | — |
| 2 | carrier_state | L1 | 859 | 858 |
| 3 | operand_read | L2 | 860 | 859 |
| 4 | execute | L3 | 861 | 860 |
| 5 | prf_writeback | L4 | 862 | 861 |
| 6 | commit | L5 | 863 | 862 |
| 7 | chain_end | — | 1355 | 863 |

### fault 145（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 864 | — |
| 2 | carrier_state | L1 | 865 | 864 |
| 3 | operand_read | L2 | 866 | 865 |
| 4 | execute | L3 | 867 | 866 |
| 5 | prf_writeback | L4 | 868 | 867 |
| 6 | commit | L5 | 869 | 868 |
| 7 | chain_end | — | 1356 | 869 |

### fault 146（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 870 | — |
| 2 | carrier_state | L1 | 871 | 870 |
| 3 | operand_read | L2 | 872 | 871 |
| 4 | execute | L3 | 873 | 872 |
| 5 | prf_writeback | L4 | 874 | 873 |
| 6 | commit | L5 | 875 | 874 |
| 7 | chain_end | — | 1357 | 875 |

### fault 147（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 876 | — |
| 2 | carrier_state | L1 | 877 | 876 |
| 3 | operand_read | L2 | 878 | 877 |
| 4 | execute | L3 | 879 | 878 |
| 5 | prf_writeback | L4 | 880 | 879 |
| 6 | commit | L5 | 881 | 880 |
| 7 | chain_end | — | 1358 | 881 |

### fault 148（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 882 | — |
| 2 | carrier_state | L1 | 883 | 882 |
| 3 | operand_read | L2 | 884 | 883 |
| 4 | execute | L3 | 885 | 884 |
| 5 | prf_writeback | L4 | 886 | 885 |
| 6 | commit | L5 | 887 | 886 |
| 7 | chain_end | — | 1359 | 887 |

### fault 149（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 888 | — |
| 2 | carrier_state | L1 | 889 | 888 |
| 3 | operand_read | L2 | 890 | 889 |
| 4 | execute | L3 | 891 | 890 |
| 5 | prf_writeback | L4 | 892 | 891 |
| 6 | commit | L5 | 893 | 892 |
| 7 | chain_end | — | 1360 | 893 |

### fault 15（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 84 | — |
| 2 | carrier_state | L1 | 85 | 84 |
| 3 | operand_read | L2 | 86 | 85 |
| 4 | execute | L3 | 87 | 86 |
| 5 | prf_writeback | L4 | 88 | 87 |
| 6 | commit | L5 | 89 | 88 |
| 7 | chain_end | — | 1226 | 89 |

### fault 150（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 894 | — |
| 2 | carrier_state | L1 | 895 | 894 |
| 3 | operand_read | L2 | 896 | 895 |
| 4 | execute | L3 | 897 | 896 |
| 5 | prf_writeback | L4 | 898 | 897 |
| 6 | commit | L5 | 899 | 898 |
| 7 | chain_end | — | 1361 | 899 |

### fault 151（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 900 | — |
| 2 | carrier_state | L1 | 901 | 900 |
| 3 | operand_read | L2 | 902 | 901 |
| 4 | execute | L3 | 903 | 902 |
| 5 | prf_writeback | L4 | 904 | 903 |
| 6 | commit | L5 | 905 | 904 |
| 7 | chain_end | — | 1362 | 905 |

### fault 152（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 906 | — |
| 2 | carrier_state | L1 | 907 | 906 |
| 3 | operand_read | L2 | 908 | 907 |
| 4 | execute | L3 | 909 | 908 |
| 5 | prf_writeback | L4 | 910 | 909 |
| 6 | commit | L5 | 911 | 910 |
| 7 | chain_end | — | 1363 | 911 |

### fault 153（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 912 | — |
| 2 | carrier_state | L1 | 913 | 912 |
| 3 | operand_read | L2 | 914 | 913 |
| 4 | execute | L3 | 915 | 914 |
| 5 | prf_writeback | L4 | 916 | 915 |
| 6 | commit | L5 | 917 | 916 |
| 7 | chain_end | — | 1364 | 917 |

### fault 154（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 918 | — |
| 2 | carrier_state | L1 | 919 | 918 |
| 3 | operand_read | L2 | 920 | 919 |
| 4 | execute | L3 | 921 | 920 |
| 5 | prf_writeback | L4 | 922 | 921 |
| 6 | commit | L5 | 923 | 922 |
| 7 | chain_end | — | 1365 | 923 |

### fault 155（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 924 | — |
| 2 | carrier_state | L1 | 925 | 924 |
| 3 | operand_read | L2 | 926 | 925 |
| 4 | execute | L3 | 927 | 926 |
| 5 | prf_writeback | L4 | 928 | 927 |
| 6 | commit | L5 | 929 | 928 |
| 7 | chain_end | — | 1366 | 929 |

### fault 156（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 930 | — |
| 2 | carrier_state | L1 | 931 | 930 |
| 3 | operand_read | L2 | 932 | 931 |
| 4 | execute | L3 | 933 | 932 |
| 5 | prf_writeback | L4 | 934 | 933 |
| 6 | commit | L5 | 935 | 934 |
| 7 | chain_end | — | 1367 | 935 |

### fault 157（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 936 | — |
| 2 | carrier_state | L1 | 937 | 936 |
| 3 | operand_read | L2 | 938 | 937 |
| 4 | execute | L3 | 939 | 938 |
| 5 | prf_writeback | L4 | 940 | 939 |
| 6 | commit | L5 | 941 | 940 |
| 7 | chain_end | — | 1368 | 941 |

### fault 158（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 942 | — |
| 2 | carrier_state | L1 | 943 | 942 |
| 3 | operand_read | L2 | 944 | 943 |
| 4 | execute | L3 | 945 | 944 |
| 5 | prf_writeback | L4 | 946 | 945 |
| 6 | commit | L5 | 947 | 946 |
| 7 | chain_end | — | 1369 | 947 |

### fault 159（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 948 | — |
| 2 | carrier_state | L1 | 949 | 948 |
| 3 | operand_read | L2 | 950 | 949 |
| 4 | execute | L3 | 951 | 950 |
| 5 | prf_writeback | L4 | 952 | 951 |
| 6 | commit | L5 | 953 | 952 |
| 7 | chain_end | — | 1370 | 953 |

### fault 16（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 90 | — |
| 2 | carrier_state | L1 | 91 | 90 |
| 3 | operand_read | L2 | 92 | 91 |
| 4 | execute | L3 | 93 | 92 |
| 5 | prf_writeback | L4 | 94 | 93 |
| 6 | commit | L5 | 95 | 94 |
| 7 | chain_end | — | 1227 | 95 |

### fault 160（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 954 | — |
| 2 | carrier_state | L1 | 955 | 954 |
| 3 | operand_read | L2 | 956 | 955 |
| 4 | execute | L3 | 957 | 956 |
| 5 | prf_writeback | L4 | 958 | 957 |
| 6 | commit | L5 | 959 | 958 |
| 7 | chain_end | — | 1371 | 959 |

### fault 161（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 960 | — |
| 2 | carrier_state | L1 | 961 | 960 |
| 3 | operand_read | L2 | 962 | 961 |
| 4 | execute | L3 | 963 | 962 |
| 5 | prf_writeback | L4 | 964 | 963 |
| 6 | commit | L5 | 965 | 964 |
| 7 | chain_end | — | 1372 | 965 |

### fault 162（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 966 | — |
| 2 | carrier_state | L1 | 967 | 966 |
| 3 | operand_read | L2 | 968 | 967 |
| 4 | execute | L3 | 969 | 968 |
| 5 | prf_writeback | L4 | 970 | 969 |
| 6 | commit | L5 | 971 | 970 |
| 7 | chain_end | — | 1373 | 971 |

### fault 163（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 972 | — |
| 2 | carrier_state | L1 | 973 | 972 |
| 3 | operand_read | L2 | 974 | 973 |
| 4 | execute | L3 | 975 | 974 |
| 5 | prf_writeback | L4 | 976 | 975 |
| 6 | commit | L5 | 977 | 976 |
| 7 | chain_end | — | 1374 | 977 |

### fault 164（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 978 | — |
| 2 | carrier_state | L1 | 979 | 978 |
| 3 | operand_read | L2 | 980 | 979 |
| 4 | execute | L3 | 981 | 980 |
| 5 | prf_writeback | L4 | 982 | 981 |
| 6 | commit | L5 | 983 | 982 |
| 7 | chain_end | — | 1375 | 983 |

### fault 165（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 984 | — |
| 2 | carrier_state | L1 | 985 | 984 |
| 3 | operand_read | L2 | 986 | 985 |
| 4 | execute | L3 | 987 | 986 |
| 5 | prf_writeback | L4 | 988 | 987 |
| 6 | commit | L5 | 989 | 988 |
| 7 | chain_end | — | 1376 | 989 |

### fault 166（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 990 | — |
| 2 | carrier_state | L1 | 991 | 990 |
| 3 | operand_read | L2 | 992 | 991 |
| 4 | execute | L3 | 993 | 992 |
| 5 | prf_writeback | L4 | 994 | 993 |
| 6 | commit | L5 | 995 | 994 |
| 7 | chain_end | — | 1377 | 995 |

### fault 167（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 996 | — |
| 2 | carrier_state | L1 | 997 | 996 |
| 3 | operand_read | L2 | 998 | 997 |
| 4 | execute | L3 | 999 | 998 |
| 5 | prf_writeback | L4 | 1000 | 999 |
| 6 | commit | L5 | 1001 | 1000 |
| 7 | chain_end | — | 1378 | 1001 |

### fault 168（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1002 | — |
| 2 | carrier_state | L1 | 1003 | 1002 |
| 3 | operand_read | L2 | 1004 | 1003 |
| 4 | execute | L3 | 1005 | 1004 |
| 5 | prf_writeback | L4 | 1006 | 1005 |
| 6 | commit | L5 | 1007 | 1006 |
| 7 | chain_end | — | 1379 | 1007 |

### fault 169（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1008 | — |
| 2 | carrier_state | L1 | 1009 | 1008 |
| 3 | operand_read | L2 | 1010 | 1009 |
| 4 | execute | L3 | 1011 | 1010 |
| 5 | prf_writeback | L4 | 1012 | 1011 |
| 6 | commit | L5 | 1013 | 1012 |
| 7 | chain_end | — | 1380 | 1013 |

### fault 17（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 96 | — |
| 2 | carrier_state | L1 | 97 | 96 |
| 3 | operand_read | L2 | 98 | 97 |
| 4 | execute | L3 | 99 | 98 |
| 5 | prf_writeback | L4 | 100 | 99 |
| 6 | commit | L5 | 101 | 100 |
| 7 | chain_end | — | 1228 | 101 |

### fault 170（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1014 | — |
| 2 | carrier_state | L1 | 1015 | 1014 |
| 3 | operand_read | L2 | 1016 | 1015 |
| 4 | execute | L3 | 1017 | 1016 |
| 5 | prf_writeback | L4 | 1018 | 1017 |
| 6 | commit | L5 | 1019 | 1018 |
| 7 | chain_end | — | 1381 | 1019 |

### fault 171（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1020 | — |
| 2 | carrier_state | L1 | 1021 | 1020 |
| 3 | operand_read | L2 | 1022 | 1021 |
| 4 | execute | L3 | 1023 | 1022 |
| 5 | prf_writeback | L4 | 1024 | 1023 |
| 6 | commit | L5 | 1025 | 1024 |
| 7 | chain_end | — | 1382 | 1025 |

### fault 172（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1026 | — |
| 2 | carrier_state | L1 | 1027 | 1026 |
| 3 | operand_read | L2 | 1028 | 1027 |
| 4 | execute | L3 | 1029 | 1028 |
| 5 | prf_writeback | L4 | 1030 | 1029 |
| 6 | commit | L5 | 1031 | 1030 |
| 7 | chain_end | — | 1383 | 1031 |

### fault 173（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1032 | — |
| 2 | carrier_state | L1 | 1033 | 1032 |
| 3 | operand_read | L2 | 1034 | 1033 |
| 4 | execute | L3 | 1035 | 1034 |
| 5 | prf_writeback | L4 | 1036 | 1035 |
| 6 | commit | L5 | 1037 | 1036 |
| 7 | chain_end | — | 1384 | 1037 |

### fault 174（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1038 | — |
| 2 | carrier_state | L1 | 1039 | 1038 |
| 3 | operand_read | L2 | 1040 | 1039 |
| 4 | execute | L3 | 1041 | 1040 |
| 5 | prf_writeback | L4 | 1042 | 1041 |
| 6 | commit | L5 | 1043 | 1042 |
| 7 | chain_end | — | 1385 | 1043 |

### fault 175（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1044 | — |
| 2 | carrier_state | L1 | 1045 | 1044 |
| 3 | operand_read | L2 | 1046 | 1045 |
| 4 | execute | L3 | 1047 | 1046 |
| 5 | prf_writeback | L4 | 1048 | 1047 |
| 6 | commit | L5 | 1049 | 1048 |
| 7 | chain_end | — | 1386 | 1049 |

### fault 176（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1050 | — |
| 2 | carrier_state | L1 | 1051 | 1050 |
| 3 | operand_read | L2 | 1052 | 1051 |
| 4 | execute | L3 | 1053 | 1052 |
| 5 | prf_writeback | L4 | 1054 | 1053 |
| 6 | commit | L5 | 1055 | 1054 |
| 7 | chain_end | — | 1387 | 1055 |

### fault 177（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1056 | — |
| 2 | carrier_state | L1 | 1057 | 1056 |
| 3 | operand_read | L2 | 1058 | 1057 |
| 4 | execute | L3 | 1059 | 1058 |
| 5 | prf_writeback | L4 | 1060 | 1059 |
| 6 | commit | L5 | 1061 | 1060 |
| 7 | chain_end | — | 1388 | 1061 |

### fault 178（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1062 | — |
| 2 | carrier_state | L1 | 1063 | 1062 |
| 3 | operand_read | L2 | 1064 | 1063 |
| 4 | execute | L3 | 1065 | 1064 |
| 5 | prf_writeback | L4 | 1066 | 1065 |
| 6 | commit | L5 | 1067 | 1066 |
| 7 | chain_end | — | 1389 | 1067 |

### fault 179（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1068 | — |
| 2 | carrier_state | L1 | 1069 | 1068 |
| 3 | operand_read | L2 | 1070 | 1069 |
| 4 | execute | L3 | 1071 | 1070 |
| 5 | prf_writeback | L4 | 1072 | 1071 |
| 6 | commit | L5 | 1073 | 1072 |
| 7 | chain_end | — | 1390 | 1073 |

### fault 18（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 102 | — |
| 2 | carrier_state | L1 | 103 | 102 |
| 3 | operand_read | L2 | 104 | 103 |
| 4 | execute | L3 | 105 | 104 |
| 5 | prf_writeback | L4 | 106 | 105 |
| 6 | commit | L5 | 107 | 106 |
| 7 | chain_end | — | 1229 | 107 |

### fault 180（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1074 | — |
| 2 | carrier_state | L1 | 1075 | 1074 |
| 3 | operand_read | L2 | 1076 | 1075 |
| 4 | execute | L3 | 1077 | 1076 |
| 5 | prf_writeback | L4 | 1078 | 1077 |
| 6 | commit | L5 | 1079 | 1078 |
| 7 | chain_end | — | 1391 | 1079 |

### fault 181（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1080 | — |
| 2 | carrier_state | L1 | 1081 | 1080 |
| 3 | operand_read | L2 | 1082 | 1081 |
| 4 | execute | L3 | 1083 | 1082 |
| 5 | prf_writeback | L4 | 1084 | 1083 |
| 6 | commit | L5 | 1085 | 1084 |
| 7 | chain_end | — | 1392 | 1085 |

### fault 182（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1086 | — |
| 2 | carrier_state | L1 | 1087 | 1086 |
| 3 | operand_read | L2 | 1088 | 1087 |
| 4 | execute | L3 | 1089 | 1088 |
| 5 | prf_writeback | L4 | 1090 | 1089 |
| 6 | commit | L5 | 1091 | 1090 |
| 7 | chain_end | — | 1393 | 1091 |

### fault 183（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1092 | — |
| 2 | carrier_state | L1 | 1093 | 1092 |
| 3 | operand_read | L2 | 1094 | 1093 |
| 4 | execute | L3 | 1095 | 1094 |
| 5 | prf_writeback | L4 | 1096 | 1095 |
| 6 | commit | L5 | 1097 | 1096 |
| 7 | chain_end | — | 1394 | 1097 |

### fault 184（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1098 | — |
| 2 | carrier_state | L1 | 1099 | 1098 |
| 3 | operand_read | L2 | 1100 | 1099 |
| 4 | execute | L3 | 1101 | 1100 |
| 5 | prf_writeback | L4 | 1102 | 1101 |
| 6 | commit | L5 | 1103 | 1102 |
| 7 | chain_end | — | 1395 | 1103 |

### fault 185（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1104 | — |
| 2 | carrier_state | L1 | 1105 | 1104 |
| 3 | operand_read | L2 | 1106 | 1105 |
| 4 | execute | L3 | 1107 | 1106 |
| 5 | prf_writeback | L4 | 1108 | 1107 |
| 6 | commit | L5 | 1109 | 1108 |
| 7 | chain_end | — | 1396 | 1109 |

### fault 186（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1110 | — |
| 2 | carrier_state | L1 | 1111 | 1110 |
| 3 | operand_read | L2 | 1112 | 1111 |
| 4 | execute | L3 | 1113 | 1112 |
| 5 | prf_writeback | L4 | 1114 | 1113 |
| 6 | commit | L5 | 1115 | 1114 |
| 7 | chain_end | — | 1397 | 1115 |

### fault 187（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1116 | — |
| 2 | carrier_state | L1 | 1117 | 1116 |
| 3 | operand_read | L2 | 1118 | 1117 |
| 4 | execute | L3 | 1119 | 1118 |
| 5 | prf_writeback | L4 | 1120 | 1119 |
| 6 | commit | L5 | 1121 | 1120 |
| 7 | chain_end | — | 1398 | 1121 |

### fault 188（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1122 | — |
| 2 | carrier_state | L1 | 1123 | 1122 |
| 3 | operand_read | L2 | 1124 | 1123 |
| 4 | execute | L3 | 1125 | 1124 |
| 5 | prf_writeback | L4 | 1126 | 1125 |
| 6 | commit | L5 | 1127 | 1126 |
| 7 | chain_end | — | 1399 | 1127 |

### fault 189（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1128 | — |
| 2 | carrier_state | L1 | 1129 | 1128 |
| 3 | operand_read | L2 | 1130 | 1129 |
| 4 | execute | L3 | 1131 | 1130 |
| 5 | prf_writeback | L4 | 1132 | 1131 |
| 6 | commit | L5 | 1133 | 1132 |
| 7 | chain_end | — | 1400 | 1133 |

### fault 19（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 108 | — |
| 2 | carrier_state | L1 | 109 | 108 |
| 3 | operand_read | L2 | 110 | 109 |
| 4 | execute | L3 | 111 | 110 |
| 5 | prf_writeback | L4 | 112 | 111 |
| 6 | commit | L5 | 113 | 112 |
| 7 | chain_end | — | 1230 | 113 |

### fault 190（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1134 | — |
| 2 | carrier_state | L1 | 1135 | 1134 |
| 3 | operand_read | L2 | 1136 | 1135 |
| 4 | execute | L3 | 1137 | 1136 |
| 5 | prf_writeback | L4 | 1138 | 1137 |
| 6 | commit | L5 | 1139 | 1138 |
| 7 | chain_end | — | 1401 | 1139 |

### fault 191（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1140 | — |
| 2 | carrier_state | L1 | 1141 | 1140 |
| 3 | operand_read | L2 | 1142 | 1141 |
| 4 | execute | L3 | 1143 | 1142 |
| 5 | prf_writeback | L4 | 1144 | 1143 |
| 6 | commit | L5 | 1145 | 1144 |
| 7 | chain_end | — | 1402 | 1145 |

### fault 192（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1146 | — |
| 2 | carrier_state | L1 | 1147 | 1146 |
| 3 | operand_read | L2 | 1148 | 1147 |
| 4 | execute | L3 | 1149 | 1148 |
| 5 | prf_writeback | L4 | 1150 | 1149 |
| 6 | commit | L5 | 1151 | 1150 |
| 7 | chain_end | — | 1403 | 1151 |

### fault 193（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1152 | — |
| 2 | carrier_state | L1 | 1153 | 1152 |
| 3 | operand_read | L2 | 1154 | 1153 |
| 4 | execute | L3 | 1155 | 1154 |
| 5 | prf_writeback | L4 | 1156 | 1155 |
| 6 | commit | L5 | 1157 | 1156 |
| 7 | chain_end | — | 1404 | 1157 |

### fault 194（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1158 | — |
| 2 | carrier_state | L1 | 1159 | 1158 |
| 3 | operand_read | L2 | 1160 | 1159 |
| 4 | execute | L3 | 1161 | 1160 |
| 5 | prf_writeback | L4 | 1162 | 1161 |
| 6 | commit | L5 | 1163 | 1162 |
| 7 | chain_end | — | 1405 | 1163 |

### fault 195（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1164 | — |
| 2 | carrier_state | L1 | 1165 | 1164 |
| 3 | operand_read | L2 | 1166 | 1165 |
| 4 | execute | L3 | 1167 | 1166 |
| 5 | prf_writeback | L4 | 1168 | 1167 |
| 6 | commit | L5 | 1169 | 1168 |
| 7 | chain_end | — | 1406 | 1169 |

### fault 196（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1170 | — |
| 2 | carrier_state | L1 | 1171 | 1170 |
| 3 | operand_read | L2 | 1172 | 1171 |
| 4 | execute | L3 | 1173 | 1172 |
| 5 | prf_writeback | L4 | 1174 | 1173 |
| 6 | commit | L5 | 1175 | 1174 |
| 7 | chain_end | — | 1407 | 1175 |

### fault 197（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1176 | — |
| 2 | carrier_state | L1 | 1177 | 1176 |
| 3 | operand_read | L2 | 1178 | 1177 |
| 4 | execute | L3 | 1179 | 1178 |
| 5 | prf_writeback | L4 | 1180 | 1179 |
| 6 | commit | L5 | 1181 | 1180 |
| 7 | chain_end | — | 1408 | 1181 |

### fault 198（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1182 | — |
| 2 | carrier_state | L1 | 1183 | 1182 |
| 3 | operand_read | L2 | 1184 | 1183 |
| 4 | execute | L3 | 1185 | 1184 |
| 5 | prf_writeback | L4 | 1186 | 1185 |
| 6 | commit | L5 | 1187 | 1186 |
| 7 | chain_end | — | 1409 | 1187 |

### fault 199（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1188 | — |
| 2 | carrier_state | L1 | 1189 | 1188 |
| 3 | operand_read | L2 | 1190 | 1189 |
| 4 | execute | L3 | 1191 | 1190 |
| 5 | prf_writeback | L4 | 1192 | 1191 |
| 6 | commit | L5 | 1193 | 1192 |
| 7 | chain_end | — | 1410 | 1193 |

### fault 2（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 6 | — |
| 2 | carrier_state | L1 | 7 | 6 |
| 3 | operand_read | L2 | 8 | 7 |
| 4 | execute | L3 | 9 | 8 |
| 5 | prf_writeback | L4 | 10 | 9 |
| 6 | commit | L5 | 11 | 10 |
| 7 | chain_end | — | 1213 | 11 |

### fault 20（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 114 | — |
| 2 | carrier_state | L1 | 115 | 114 |
| 3 | operand_read | L2 | 116 | 115 |
| 4 | execute | L3 | 117 | 116 |
| 5 | prf_writeback | L4 | 118 | 117 |
| 6 | commit | L5 | 119 | 118 |
| 7 | chain_end | — | 1231 | 119 |

### fault 200（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1194 | — |
| 2 | carrier_state | L1 | 1195 | 1194 |
| 3 | operand_read | L2 | 1196 | 1195 |
| 4 | execute | L3 | 1197 | 1196 |
| 5 | prf_writeback | L4 | 1198 | 1197 |
| 6 | commit | L5 | 1199 | 1198 |
| 7 | chain_end | — | 1411 | 1199 |

### fault 201（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1200 | — |
| 2 | carrier_state | L1 | 1201 | 1200 |
| 3 | operand_read | L2 | 1202 | 1201 |
| 4 | execute | L3 | 1203 | 1202 |
| 5 | prf_writeback | L4 | 1204 | 1203 |
| 6 | commit | L5 | 1205 | 1204 |
| 7 | chain_end | — | 1412 | 1205 |

### fault 202（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1206 | — |
| 2 | carrier_state | L1 | 1207 | 1206 |
| 3 | operand_read | L2 | 1208 | 1207 |
| 4 | execute | L3 | 1209 | 1208 |
| 5 | prf_writeback | L4 | 1210 | 1209 |
| 6 | commit | L5 | 1211 | 1210 |
| 7 | chain_end | — | 1413 | 1211 |

### fault 21（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 120 | — |
| 2 | carrier_state | L1 | 121 | 120 |
| 3 | operand_read | L2 | 122 | 121 |
| 4 | execute | L3 | 123 | 122 |
| 5 | prf_writeback | L4 | 124 | 123 |
| 6 | commit | L5 | 125 | 124 |
| 7 | chain_end | — | 1232 | 125 |

### fault 22（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 126 | — |
| 2 | carrier_state | L1 | 127 | 126 |
| 3 | operand_read | L2 | 128 | 127 |
| 4 | execute | L3 | 129 | 128 |
| 5 | prf_writeback | L4 | 130 | 129 |
| 6 | commit | L5 | 131 | 130 |
| 7 | chain_end | — | 1233 | 131 |

### fault 23（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 132 | — |
| 2 | carrier_state | L1 | 133 | 132 |
| 3 | operand_read | L2 | 134 | 133 |
| 4 | execute | L3 | 135 | 134 |
| 5 | prf_writeback | L4 | 136 | 135 |
| 6 | commit | L5 | 137 | 136 |
| 7 | chain_end | — | 1234 | 137 |

### fault 24（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 138 | — |
| 2 | carrier_state | L1 | 139 | 138 |
| 3 | operand_read | L2 | 140 | 139 |
| 4 | execute | L3 | 141 | 140 |
| 5 | prf_writeback | L4 | 142 | 141 |
| 6 | commit | L5 | 143 | 142 |
| 7 | chain_end | — | 1235 | 143 |

### fault 25（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 144 | — |
| 2 | carrier_state | L1 | 145 | 144 |
| 3 | operand_read | L2 | 146 | 145 |
| 4 | execute | L3 | 147 | 146 |
| 5 | prf_writeback | L4 | 148 | 147 |
| 6 | commit | L5 | 149 | 148 |
| 7 | chain_end | — | 1236 | 149 |

### fault 26（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 150 | — |
| 2 | carrier_state | L1 | 151 | 150 |
| 3 | operand_read | L2 | 152 | 151 |
| 4 | execute | L3 | 153 | 152 |
| 5 | prf_writeback | L4 | 154 | 153 |
| 6 | commit | L5 | 155 | 154 |
| 7 | chain_end | — | 1237 | 155 |

### fault 27（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 156 | — |
| 2 | carrier_state | L1 | 157 | 156 |
| 3 | operand_read | L2 | 158 | 157 |
| 4 | execute | L3 | 159 | 158 |
| 5 | prf_writeback | L4 | 160 | 159 |
| 6 | commit | L5 | 161 | 160 |
| 7 | chain_end | — | 1238 | 161 |

### fault 28（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 162 | — |
| 2 | carrier_state | L1 | 163 | 162 |
| 3 | operand_read | L2 | 164 | 163 |
| 4 | execute | L3 | 165 | 164 |
| 5 | prf_writeback | L4 | 166 | 165 |
| 6 | commit | L5 | 167 | 166 |
| 7 | chain_end | — | 1239 | 167 |

### fault 29（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 168 | — |
| 2 | carrier_state | L1 | 169 | 168 |
| 3 | operand_read | L2 | 170 | 169 |
| 4 | execute | L3 | 171 | 170 |
| 5 | prf_writeback | L4 | 172 | 171 |
| 6 | commit | L5 | 173 | 172 |
| 7 | chain_end | — | 1240 | 173 |

### fault 3（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 12 | — |
| 2 | carrier_state | L1 | 13 | 12 |
| 3 | operand_read | L2 | 14 | 13 |
| 4 | execute | L3 | 15 | 14 |
| 5 | prf_writeback | L4 | 16 | 15 |
| 6 | commit | L5 | 17 | 16 |
| 7 | chain_end | — | 1214 | 17 |

### fault 30（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 174 | — |
| 2 | carrier_state | L1 | 175 | 174 |
| 3 | operand_read | L2 | 176 | 175 |
| 4 | execute | L3 | 177 | 176 |
| 5 | prf_writeback | L4 | 178 | 177 |
| 6 | commit | L5 | 179 | 178 |
| 7 | chain_end | — | 1241 | 179 |

### fault 31（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 180 | — |
| 2 | carrier_state | L1 | 181 | 180 |
| 3 | operand_read | L2 | 182 | 181 |
| 4 | execute | L3 | 183 | 182 |
| 5 | prf_writeback | L4 | 184 | 183 |
| 6 | commit | L5 | 185 | 184 |
| 7 | chain_end | — | 1242 | 185 |

### fault 32（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 186 | — |
| 2 | carrier_state | L1 | 187 | 186 |
| 3 | operand_read | L2 | 188 | 187 |
| 4 | execute | L3 | 189 | 188 |
| 5 | prf_writeback | L4 | 190 | 189 |
| 6 | commit | L5 | 191 | 190 |
| 7 | chain_end | — | 1243 | 191 |

### fault 33（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 192 | — |
| 2 | carrier_state | L1 | 193 | 192 |
| 3 | operand_read | L2 | 194 | 193 |
| 4 | execute | L3 | 195 | 194 |
| 5 | prf_writeback | L4 | 196 | 195 |
| 6 | commit | L5 | 197 | 196 |
| 7 | chain_end | — | 1244 | 197 |

### fault 34（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 198 | — |
| 2 | carrier_state | L1 | 199 | 198 |
| 3 | operand_read | L2 | 200 | 199 |
| 4 | execute | L3 | 201 | 200 |
| 5 | prf_writeback | L4 | 202 | 201 |
| 6 | commit | L5 | 203 | 202 |
| 7 | chain_end | — | 1245 | 203 |

### fault 35（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 204 | — |
| 2 | carrier_state | L1 | 205 | 204 |
| 3 | operand_read | L2 | 206 | 205 |
| 4 | execute | L3 | 207 | 206 |
| 5 | prf_writeback | L4 | 208 | 207 |
| 6 | commit | L5 | 209 | 208 |
| 7 | chain_end | — | 1246 | 209 |

### fault 36（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 210 | — |
| 2 | carrier_state | L1 | 211 | 210 |
| 3 | operand_read | L2 | 212 | 211 |
| 4 | execute | L3 | 213 | 212 |
| 5 | prf_writeback | L4 | 214 | 213 |
| 6 | commit | L5 | 215 | 214 |
| 7 | chain_end | — | 1247 | 215 |

### fault 37（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 216 | — |
| 2 | carrier_state | L1 | 217 | 216 |
| 3 | operand_read | L2 | 218 | 217 |
| 4 | execute | L3 | 219 | 218 |
| 5 | prf_writeback | L4 | 220 | 219 |
| 6 | commit | L5 | 221 | 220 |
| 7 | chain_end | — | 1248 | 221 |

### fault 38（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 222 | — |
| 2 | carrier_state | L1 | 223 | 222 |
| 3 | operand_read | L2 | 224 | 223 |
| 4 | execute | L3 | 225 | 224 |
| 5 | prf_writeback | L4 | 226 | 225 |
| 6 | commit | L5 | 227 | 226 |
| 7 | chain_end | — | 1249 | 227 |

### fault 39（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 228 | — |
| 2 | carrier_state | L1 | 229 | 228 |
| 3 | operand_read | L2 | 230 | 229 |
| 4 | execute | L3 | 231 | 230 |
| 5 | prf_writeback | L4 | 232 | 231 |
| 6 | commit | L5 | 233 | 232 |
| 7 | chain_end | — | 1250 | 233 |

### fault 4（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 18 | — |
| 2 | carrier_state | L1 | 19 | 18 |
| 3 | operand_read | L2 | 20 | 19 |
| 4 | execute | L3 | 21 | 20 |
| 5 | prf_writeback | L4 | 22 | 21 |
| 6 | commit | L5 | 23 | 22 |
| 7 | chain_end | — | 1215 | 23 |

### fault 40（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 234 | — |
| 2 | carrier_state | L1 | 235 | 234 |
| 3 | operand_read | L2 | 236 | 235 |
| 4 | execute | L3 | 237 | 236 |
| 5 | prf_writeback | L4 | 238 | 237 |
| 6 | commit | L5 | 239 | 238 |
| 7 | chain_end | — | 1251 | 239 |

### fault 41（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 240 | — |
| 2 | carrier_state | L1 | 241 | 240 |
| 3 | operand_read | L2 | 242 | 241 |
| 4 | execute | L3 | 243 | 242 |
| 5 | prf_writeback | L4 | 244 | 243 |
| 6 | commit | L5 | 245 | 244 |
| 7 | chain_end | — | 1252 | 245 |

### fault 42（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 246 | — |
| 2 | carrier_state | L1 | 247 | 246 |
| 3 | operand_read | L2 | 248 | 247 |
| 4 | execute | L3 | 249 | 248 |
| 5 | prf_writeback | L4 | 250 | 249 |
| 6 | commit | L5 | 251 | 250 |
| 7 | chain_end | — | 1253 | 251 |

### fault 43（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 252 | — |
| 2 | carrier_state | L1 | 253 | 252 |
| 3 | operand_read | L2 | 254 | 253 |
| 4 | execute | L3 | 255 | 254 |
| 5 | prf_writeback | L4 | 256 | 255 |
| 6 | commit | L5 | 257 | 256 |
| 7 | chain_end | — | 1254 | 257 |

### fault 44（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 258 | — |
| 2 | carrier_state | L1 | 259 | 258 |
| 3 | operand_read | L2 | 260 | 259 |
| 4 | execute | L3 | 261 | 260 |
| 5 | prf_writeback | L4 | 262 | 261 |
| 6 | commit | L5 | 263 | 262 |
| 7 | chain_end | — | 1255 | 263 |

### fault 45（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 264 | — |
| 2 | carrier_state | L1 | 265 | 264 |
| 3 | operand_read | L2 | 266 | 265 |
| 4 | execute | L3 | 267 | 266 |
| 5 | prf_writeback | L4 | 268 | 267 |
| 6 | commit | L5 | 269 | 268 |
| 7 | chain_end | — | 1256 | 269 |

### fault 46（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 270 | — |
| 2 | carrier_state | L1 | 271 | 270 |
| 3 | operand_read | L2 | 272 | 271 |
| 4 | execute | L3 | 273 | 272 |
| 5 | prf_writeback | L4 | 274 | 273 |
| 6 | commit | L5 | 275 | 274 |
| 7 | chain_end | — | 1257 | 275 |

### fault 47（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 276 | — |
| 2 | carrier_state | L1 | 277 | 276 |
| 3 | operand_read | L2 | 278 | 277 |
| 4 | execute | L3 | 279 | 278 |
| 5 | prf_writeback | L4 | 280 | 279 |
| 6 | commit | L5 | 281 | 280 |
| 7 | chain_end | — | 1258 | 281 |

### fault 48（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 282 | — |
| 2 | carrier_state | L1 | 283 | 282 |
| 3 | operand_read | L2 | 284 | 283 |
| 4 | execute | L3 | 285 | 284 |
| 5 | prf_writeback | L4 | 286 | 285 |
| 6 | commit | L5 | 287 | 286 |
| 7 | chain_end | — | 1259 | 287 |

### fault 49（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 288 | — |
| 2 | carrier_state | L1 | 289 | 288 |
| 3 | operand_read | L2 | 290 | 289 |
| 4 | execute | L3 | 291 | 290 |
| 5 | prf_writeback | L4 | 292 | 291 |
| 6 | commit | L5 | 293 | 292 |
| 7 | chain_end | — | 1260 | 293 |

### fault 5（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 24 | — |
| 2 | carrier_state | L1 | 25 | 24 |
| 3 | operand_read | L2 | 26 | 25 |
| 4 | execute | L3 | 27 | 26 |
| 5 | prf_writeback | L4 | 28 | 27 |
| 6 | commit | L5 | 29 | 28 |
| 7 | chain_end | — | 1216 | 29 |

### fault 50（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 294 | — |
| 2 | carrier_state | L1 | 295 | 294 |
| 3 | operand_read | L2 | 296 | 295 |
| 4 | execute | L3 | 297 | 296 |
| 5 | prf_writeback | L4 | 298 | 297 |
| 6 | commit | L5 | 299 | 298 |
| 7 | chain_end | — | 1261 | 299 |

### fault 51（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 300 | — |
| 2 | carrier_state | L1 | 301 | 300 |
| 3 | operand_read | L2 | 302 | 301 |
| 4 | execute | L3 | 303 | 302 |
| 5 | prf_writeback | L4 | 304 | 303 |
| 6 | commit | L5 | 305 | 304 |
| 7 | chain_end | — | 1262 | 305 |

### fault 52（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 306 | — |
| 2 | carrier_state | L1 | 307 | 306 |
| 3 | operand_read | L2 | 308 | 307 |
| 4 | execute | L3 | 309 | 308 |
| 5 | prf_writeback | L4 | 310 | 309 |
| 6 | commit | L5 | 311 | 310 |
| 7 | chain_end | — | 1263 | 311 |

### fault 53（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 312 | — |
| 2 | carrier_state | L1 | 313 | 312 |
| 3 | operand_read | L2 | 314 | 313 |
| 4 | execute | L3 | 315 | 314 |
| 5 | prf_writeback | L4 | 316 | 315 |
| 6 | commit | L5 | 317 | 316 |
| 7 | chain_end | — | 1264 | 317 |

### fault 54（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 318 | — |
| 2 | carrier_state | L1 | 319 | 318 |
| 3 | operand_read | L2 | 320 | 319 |
| 4 | execute | L3 | 321 | 320 |
| 5 | prf_writeback | L4 | 322 | 321 |
| 6 | commit | L5 | 323 | 322 |
| 7 | chain_end | — | 1265 | 323 |

### fault 55（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 324 | — |
| 2 | carrier_state | L1 | 325 | 324 |
| 3 | operand_read | L2 | 326 | 325 |
| 4 | execute | L3 | 327 | 326 |
| 5 | prf_writeback | L4 | 328 | 327 |
| 6 | commit | L5 | 329 | 328 |
| 7 | chain_end | — | 1266 | 329 |

### fault 56（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 330 | — |
| 2 | carrier_state | L1 | 331 | 330 |
| 3 | operand_read | L2 | 332 | 331 |
| 4 | execute | L3 | 333 | 332 |
| 5 | prf_writeback | L4 | 334 | 333 |
| 6 | commit | L5 | 335 | 334 |
| 7 | chain_end | — | 1267 | 335 |

### fault 57（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 336 | — |
| 2 | carrier_state | L1 | 337 | 336 |
| 3 | operand_read | L2 | 338 | 337 |
| 4 | execute | L3 | 339 | 338 |
| 5 | prf_writeback | L4 | 340 | 339 |
| 6 | commit | L5 | 341 | 340 |
| 7 | chain_end | — | 1268 | 341 |

### fault 58（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 342 | — |
| 2 | carrier_state | L1 | 343 | 342 |
| 3 | operand_read | L2 | 344 | 343 |
| 4 | execute | L3 | 345 | 344 |
| 5 | prf_writeback | L4 | 346 | 345 |
| 6 | commit | L5 | 347 | 346 |
| 7 | chain_end | — | 1269 | 347 |

### fault 59（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 348 | — |
| 2 | carrier_state | L1 | 349 | 348 |
| 3 | operand_read | L2 | 350 | 349 |
| 4 | execute | L3 | 351 | 350 |
| 5 | prf_writeback | L4 | 352 | 351 |
| 6 | commit | L5 | 353 | 352 |
| 7 | chain_end | — | 1270 | 353 |

### fault 6（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 30 | — |
| 2 | carrier_state | L1 | 31 | 30 |
| 3 | operand_read | L2 | 32 | 31 |
| 4 | execute | L3 | 33 | 32 |
| 5 | prf_writeback | L4 | 34 | 33 |
| 6 | commit | L5 | 35 | 34 |
| 7 | chain_end | — | 1217 | 35 |

### fault 60（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 354 | — |
| 2 | carrier_state | L1 | 355 | 354 |
| 3 | operand_read | L2 | 356 | 355 |
| 4 | execute | L3 | 357 | 356 |
| 5 | prf_writeback | L4 | 358 | 357 |
| 6 | commit | L5 | 359 | 358 |
| 7 | chain_end | — | 1271 | 359 |

### fault 61（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 360 | — |
| 2 | carrier_state | L1 | 361 | 360 |
| 3 | operand_read | L2 | 362 | 361 |
| 4 | execute | L3 | 363 | 362 |
| 5 | prf_writeback | L4 | 364 | 363 |
| 6 | commit | L5 | 365 | 364 |
| 7 | chain_end | — | 1272 | 365 |

### fault 62（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 366 | — |
| 2 | carrier_state | L1 | 367 | 366 |
| 3 | operand_read | L2 | 368 | 367 |
| 4 | execute | L3 | 369 | 368 |
| 5 | prf_writeback | L4 | 370 | 369 |
| 6 | commit | L5 | 371 | 370 |
| 7 | chain_end | — | 1273 | 371 |

### fault 63（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 372 | — |
| 2 | carrier_state | L1 | 373 | 372 |
| 3 | operand_read | L2 | 374 | 373 |
| 4 | execute | L3 | 375 | 374 |
| 5 | prf_writeback | L4 | 376 | 375 |
| 6 | commit | L5 | 377 | 376 |
| 7 | chain_end | — | 1274 | 377 |

### fault 64（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 378 | — |
| 2 | carrier_state | L1 | 379 | 378 |
| 3 | operand_read | L2 | 380 | 379 |
| 4 | execute | L3 | 381 | 380 |
| 5 | prf_writeback | L4 | 382 | 381 |
| 6 | commit | L5 | 383 | 382 |
| 7 | chain_end | — | 1275 | 383 |

### fault 65（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 384 | — |
| 2 | carrier_state | L1 | 385 | 384 |
| 3 | operand_read | L2 | 386 | 385 |
| 4 | execute | L3 | 387 | 386 |
| 5 | prf_writeback | L4 | 388 | 387 |
| 6 | commit | L5 | 389 | 388 |
| 7 | chain_end | — | 1276 | 389 |

### fault 66（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 390 | — |
| 2 | carrier_state | L1 | 391 | 390 |
| 3 | operand_read | L2 | 392 | 391 |
| 4 | execute | L3 | 393 | 392 |
| 5 | prf_writeback | L4 | 394 | 393 |
| 6 | commit | L5 | 395 | 394 |
| 7 | chain_end | — | 1277 | 395 |

### fault 67（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 396 | — |
| 2 | carrier_state | L1 | 397 | 396 |
| 3 | operand_read | L2 | 398 | 397 |
| 4 | execute | L3 | 399 | 398 |
| 5 | prf_writeback | L4 | 400 | 399 |
| 6 | commit | L5 | 401 | 400 |
| 7 | chain_end | — | 1278 | 401 |

### fault 68（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 402 | — |
| 2 | carrier_state | L1 | 403 | 402 |
| 3 | operand_read | L2 | 404 | 403 |
| 4 | execute | L3 | 405 | 404 |
| 5 | prf_writeback | L4 | 406 | 405 |
| 6 | commit | L5 | 407 | 406 |
| 7 | chain_end | — | 1279 | 407 |

### fault 69（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 408 | — |
| 2 | carrier_state | L1 | 409 | 408 |
| 3 | operand_read | L2 | 410 | 409 |
| 4 | execute | L3 | 411 | 410 |
| 5 | prf_writeback | L4 | 412 | 411 |
| 6 | commit | L5 | 413 | 412 |
| 7 | chain_end | — | 1280 | 413 |

### fault 7（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 36 | — |
| 2 | carrier_state | L1 | 37 | 36 |
| 3 | operand_read | L2 | 38 | 37 |
| 4 | execute | L3 | 39 | 38 |
| 5 | prf_writeback | L4 | 40 | 39 |
| 6 | commit | L5 | 41 | 40 |
| 7 | chain_end | — | 1218 | 41 |

### fault 70（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 414 | — |
| 2 | carrier_state | L1 | 415 | 414 |
| 3 | operand_read | L2 | 416 | 415 |
| 4 | execute | L3 | 417 | 416 |
| 5 | prf_writeback | L4 | 418 | 417 |
| 6 | commit | L5 | 419 | 418 |
| 7 | chain_end | — | 1281 | 419 |

### fault 71（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 420 | — |
| 2 | carrier_state | L1 | 421 | 420 |
| 3 | operand_read | L2 | 422 | 421 |
| 4 | execute | L3 | 423 | 422 |
| 5 | prf_writeback | L4 | 424 | 423 |
| 6 | commit | L5 | 425 | 424 |
| 7 | chain_end | — | 1282 | 425 |

### fault 72（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 426 | — |
| 2 | carrier_state | L1 | 427 | 426 |
| 3 | operand_read | L2 | 428 | 427 |
| 4 | execute | L3 | 429 | 428 |
| 5 | prf_writeback | L4 | 430 | 429 |
| 6 | commit | L5 | 431 | 430 |
| 7 | chain_end | — | 1283 | 431 |

### fault 73（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 432 | — |
| 2 | carrier_state | L1 | 433 | 432 |
| 3 | operand_read | L2 | 434 | 433 |
| 4 | execute | L3 | 435 | 434 |
| 5 | prf_writeback | L4 | 436 | 435 |
| 6 | commit | L5 | 437 | 436 |
| 7 | chain_end | — | 1284 | 437 |

### fault 74（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 438 | — |
| 2 | carrier_state | L1 | 439 | 438 |
| 3 | operand_read | L2 | 440 | 439 |
| 4 | execute | L3 | 441 | 440 |
| 5 | prf_writeback | L4 | 442 | 441 |
| 6 | commit | L5 | 443 | 442 |
| 7 | chain_end | — | 1285 | 443 |

### fault 75（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 444 | — |
| 2 | carrier_state | L1 | 445 | 444 |
| 3 | operand_read | L2 | 446 | 445 |
| 4 | execute | L3 | 447 | 446 |
| 5 | prf_writeback | L4 | 448 | 447 |
| 6 | commit | L5 | 449 | 448 |
| 7 | chain_end | — | 1286 | 449 |

### fault 76（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 450 | — |
| 2 | carrier_state | L1 | 451 | 450 |
| 3 | operand_read | L2 | 452 | 451 |
| 4 | execute | L3 | 453 | 452 |
| 5 | prf_writeback | L4 | 454 | 453 |
| 6 | commit | L5 | 455 | 454 |
| 7 | chain_end | — | 1287 | 455 |

### fault 77（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 456 | — |
| 2 | carrier_state | L1 | 457 | 456 |
| 3 | operand_read | L2 | 458 | 457 |
| 4 | execute | L3 | 459 | 458 |
| 5 | prf_writeback | L4 | 460 | 459 |
| 6 | commit | L5 | 461 | 460 |
| 7 | chain_end | — | 1288 | 461 |

### fault 78（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 462 | — |
| 2 | carrier_state | L1 | 463 | 462 |
| 3 | operand_read | L2 | 464 | 463 |
| 4 | execute | L3 | 465 | 464 |
| 5 | prf_writeback | L4 | 466 | 465 |
| 6 | commit | L5 | 467 | 466 |
| 7 | chain_end | — | 1289 | 467 |

### fault 79（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 468 | — |
| 2 | carrier_state | L1 | 469 | 468 |
| 3 | operand_read | L2 | 470 | 469 |
| 4 | execute | L3 | 471 | 470 |
| 5 | prf_writeback | L4 | 472 | 471 |
| 6 | commit | L5 | 473 | 472 |
| 7 | chain_end | — | 1290 | 473 |

### fault 8（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 42 | — |
| 2 | carrier_state | L1 | 43 | 42 |
| 3 | operand_read | L2 | 44 | 43 |
| 4 | execute | L3 | 45 | 44 |
| 5 | prf_writeback | L4 | 46 | 45 |
| 6 | commit | L5 | 47 | 46 |
| 7 | chain_end | — | 1219 | 47 |

### fault 80（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 474 | — |
| 2 | carrier_state | L1 | 475 | 474 |
| 3 | operand_read | L2 | 476 | 475 |
| 4 | execute | L3 | 477 | 476 |
| 5 | prf_writeback | L4 | 478 | 477 |
| 6 | commit | L5 | 479 | 478 |
| 7 | chain_end | — | 1291 | 479 |

### fault 81（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 480 | — |
| 2 | carrier_state | L1 | 481 | 480 |
| 3 | operand_read | L2 | 482 | 481 |
| 4 | execute | L3 | 483 | 482 |
| 5 | prf_writeback | L4 | 484 | 483 |
| 6 | commit | L5 | 485 | 484 |
| 7 | chain_end | — | 1292 | 485 |

### fault 82（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 486 | — |
| 2 | carrier_state | L1 | 487 | 486 |
| 3 | operand_read | L2 | 488 | 487 |
| 4 | execute | L3 | 489 | 488 |
| 5 | prf_writeback | L4 | 490 | 489 |
| 6 | commit | L5 | 491 | 490 |
| 7 | chain_end | — | 1293 | 491 |

### fault 83（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 492 | — |
| 2 | carrier_state | L1 | 493 | 492 |
| 3 | operand_read | L2 | 494 | 493 |
| 4 | execute | L3 | 495 | 494 |
| 5 | prf_writeback | L4 | 496 | 495 |
| 6 | commit | L5 | 497 | 496 |
| 7 | chain_end | — | 1294 | 497 |

### fault 84（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 498 | — |
| 2 | carrier_state | L1 | 499 | 498 |
| 3 | operand_read | L2 | 500 | 499 |
| 4 | execute | L3 | 501 | 500 |
| 5 | prf_writeback | L4 | 502 | 501 |
| 6 | commit | L5 | 503 | 502 |
| 7 | chain_end | — | 1295 | 503 |

### fault 85（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 504 | — |
| 2 | carrier_state | L1 | 505 | 504 |
| 3 | operand_read | L2 | 506 | 505 |
| 4 | execute | L3 | 507 | 506 |
| 5 | prf_writeback | L4 | 508 | 507 |
| 6 | commit | L5 | 509 | 508 |
| 7 | chain_end | — | 1296 | 509 |

### fault 86（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 510 | — |
| 2 | carrier_state | L1 | 511 | 510 |
| 3 | operand_read | L2 | 512 | 511 |
| 4 | execute | L3 | 513 | 512 |
| 5 | prf_writeback | L4 | 514 | 513 |
| 6 | commit | L5 | 515 | 514 |
| 7 | chain_end | — | 1297 | 515 |

### fault 87（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 516 | — |
| 2 | carrier_state | L1 | 517 | 516 |
| 3 | operand_read | L2 | 518 | 517 |
| 4 | execute | L3 | 519 | 518 |
| 5 | prf_writeback | L4 | 520 | 519 |
| 6 | commit | L5 | 521 | 520 |
| 7 | chain_end | — | 1298 | 521 |

### fault 88（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 522 | — |
| 2 | carrier_state | L1 | 523 | 522 |
| 3 | operand_read | L2 | 524 | 523 |
| 4 | execute | L3 | 525 | 524 |
| 5 | prf_writeback | L4 | 526 | 525 |
| 6 | commit | L5 | 527 | 526 |
| 7 | chain_end | — | 1299 | 527 |

### fault 89（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 528 | — |
| 2 | carrier_state | L1 | 529 | 528 |
| 3 | operand_read | L2 | 530 | 529 |
| 4 | execute | L3 | 531 | 530 |
| 5 | prf_writeback | L4 | 532 | 531 |
| 6 | commit | L5 | 533 | 532 |
| 7 | chain_end | — | 1300 | 533 |

### fault 9（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 48 | — |
| 2 | carrier_state | L1 | 49 | 48 |
| 3 | operand_read | L2 | 50 | 49 |
| 4 | execute | L3 | 51 | 50 |
| 5 | prf_writeback | L4 | 52 | 51 |
| 6 | commit | L5 | 53 | 52 |
| 7 | chain_end | — | 1220 | 53 |

### fault 90（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 534 | — |
| 2 | carrier_state | L1 | 535 | 534 |
| 3 | operand_read | L2 | 536 | 535 |
| 4 | execute | L3 | 537 | 536 |
| 5 | prf_writeback | L4 | 538 | 537 |
| 6 | commit | L5 | 539 | 538 |
| 7 | chain_end | — | 1301 | 539 |

### fault 91（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 540 | — |
| 2 | carrier_state | L1 | 541 | 540 |
| 3 | operand_read | L2 | 542 | 541 |
| 4 | execute | L3 | 543 | 542 |
| 5 | prf_writeback | L4 | 544 | 543 |
| 6 | commit | L5 | 545 | 544 |
| 7 | chain_end | — | 1302 | 545 |

### fault 92（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 546 | — |
| 2 | carrier_state | L1 | 547 | 546 |
| 3 | operand_read | L2 | 548 | 547 |
| 4 | execute | L3 | 549 | 548 |
| 5 | prf_writeback | L4 | 550 | 549 |
| 6 | commit | L5 | 551 | 550 |
| 7 | chain_end | — | 1303 | 551 |

### fault 93（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 552 | — |
| 2 | carrier_state | L1 | 553 | 552 |
| 3 | operand_read | L2 | 554 | 553 |
| 4 | execute | L3 | 555 | 554 |
| 5 | prf_writeback | L4 | 556 | 555 |
| 6 | commit | L5 | 557 | 556 |
| 7 | chain_end | — | 1304 | 557 |

### fault 94（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 558 | — |
| 2 | carrier_state | L1 | 559 | 558 |
| 3 | operand_read | L2 | 560 | 559 |
| 4 | execute | L3 | 561 | 560 |
| 5 | prf_writeback | L4 | 562 | 561 |
| 6 | commit | L5 | 563 | 562 |
| 7 | chain_end | — | 1305 | 563 |

### fault 95（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 564 | — |
| 2 | carrier_state | L1 | 565 | 564 |
| 3 | operand_read | L2 | 566 | 565 |
| 4 | execute | L3 | 567 | 566 |
| 5 | prf_writeback | L4 | 568 | 567 |
| 6 | commit | L5 | 569 | 568 |
| 7 | chain_end | — | 1306 | 569 |

### fault 96（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 570 | — |
| 2 | carrier_state | L1 | 571 | 570 |
| 3 | operand_read | L2 | 572 | 571 |
| 4 | execute | L3 | 573 | 572 |
| 5 | prf_writeback | L4 | 574 | 573 |
| 6 | commit | L5 | 575 | 574 |
| 7 | chain_end | — | 1307 | 575 |

### fault 97（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 576 | — |
| 2 | carrier_state | L1 | 577 | 576 |
| 3 | operand_read | L2 | 578 | 577 |
| 4 | execute | L3 | 579 | 578 |
| 5 | prf_writeback | L4 | 580 | 579 |
| 6 | commit | L5 | 581 | 580 |
| 7 | chain_end | — | 1308 | 581 |

### fault 98（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 582 | — |
| 2 | carrier_state | L1 | 583 | 582 |
| 3 | operand_read | L2 | 584 | 583 |
| 4 | execute | L3 | 585 | 584 |
| 5 | prf_writeback | L4 | 586 | 585 |
| 6 | commit | L5 | 587 | 586 |
| 7 | chain_end | — | 1309 | 587 |

### fault 99（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 588 | — |
| 2 | carrier_state | L1 | 589 | 588 |
| 3 | operand_read | L2 | 590 | 589 |
| 4 | execute | L3 | 591 | 590 |
| 5 | prf_writeback | L4 | 592 | 591 |
| 6 | commit | L5 | 593 | 592 |
| 7 | chain_end | — | 1310 | 593 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 28481145 | 1 | 74668 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfdb126e978d4fdf→0xbfdb126e978d4fde | — | — | origin |
| carrier_state | 1 | 0 | 28481145 | 1 | 74668 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfdb126e978d4fdf→0xbfdb126e978d4fde | — | — | fsu_taint |
| operand_read | 2 | 1 | 28496545 | 1 | 74738 | 0x0000000000400654 | fmadd | 74668/74738 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 28496545 | 1 | 74738 | 0x0000000000400654 | fmadd | 74668/74738 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 28496545 | 1 | 74738 | 0x0000000000400654 | fmadd | 74668/74738 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 28497315 | 1 | 74738 | 0x0000000000400654 | fmadd | —/74738 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1212 | 5 | 9405832205 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 54 | — | 179867380 | 10 | 672768 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4076600000000000→0x4076600000008000 | — | — | origin |
| carrier_state | 55 | 54 | 179867380 | 10 | 672768 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4076600000000000→0x4076600000008000 | — | — | fsu_taint |
| operand_read | 56 | 55 | 179871615 | 10 | 672771 | 0x0000000000400658 | fmadd | 672768/672771 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 57 | 56 | 179871615 | 10 | 672771 | 0x0000000000400658 | fmadd | 672768/672771 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 58 | 57 | 179871615 | 10 | 672771 | 0x0000000000400658 | fmadd | 672768/672771 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 59 | 58 | 179872385 | 10 | 672771 | 0x0000000000400658 | fmadd | —/672771 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1221 | 59 | 9405832205 | 10 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 594 | — | 1547794710 | 100 | 6069568 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfd5a1cac083126f→0xbfd5a1cac083136f | — | — | origin |
| carrier_state | 595 | 594 | 1547794710 | 100 | 6069568 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfd5a1cac083126f→0xbfd5a1cac083136f | — | — | fsu_taint |
| operand_read | 596 | 595 | 1547810110 | 100 | 6069638 | 0x0000000000400654 | fmadd | 6069568/6069638 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 597 | 596 | 1547810110 | 100 | 6069638 | 0x0000000000400654 | fmadd | 6069568/6069638 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 598 | 597 | 1547810110 | 100 | 6069638 | 0x0000000000400654 | fmadd | 6069568/6069638 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 599 | 598 | 1547810880 | 100 | 6069638 | 0x0000000000400654 | fmadd | —/6069638 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1311 | 599 | 9405832205 | 100 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 600 | — | 1563254000 | 101 | 6130693 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4080400000000000→0x4080400000010000 | — | — | origin |
| carrier_state | 601 | 600 | 1563254000 | 101 | 6130693 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4080400000000000→0x4080400000010000 | — | — | fsu_taint |
| operand_read | 602 | 601 | 1563257850 | 101 | 6130696 | 0x000000000040065c | fmadd | 6130693/6130696 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 603 | 602 | 1563257850 | 101 | 6130696 | 0x000000000040065c | fmadd | 6130693/6130696 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 604 | 603 | 1563257850 | 101 | 6130696 | 0x000000000040065c | fmadd | 6130693/6130696 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 605 | 604 | 1563258620 | 101 | 6130696 | 0x000000000040065c | fmadd | —/6130696 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1312 | 605 | 9405832205 | 101 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 606 | — | 1583674785 | 102 | 6210900 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x405fc00000000000→0x405fc00000000002 | — | — | origin |
| carrier_state | 607 | 606 | 1583674785 | 102 | 6210900 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x405fc00000000000→0x405fc00000000002 | — | — | fsu_taint |
| operand_read | 608 | 607 | 1583679020 | 102 | 6210903 | 0x0000000000400658 | fmadd | 6210900/6210903 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 609 | 608 | 1583679020 | 102 | 6210903 | 0x0000000000400658 | fmadd | 6210900/6210903 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 610 | 609 | 1583679020 | 102 | 6210903 | 0x0000000000400658 | fmadd | 6210900/6210903 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 611 | 610 | 1583679790 | 102 | 6210903 | 0x0000000000400658 | fmadd | —/6210903 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1313 | 611 | 9405832205 | 102 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 612 | — | 1598522310 | 103 | 6269366 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff28f5c28f5c28f→0x3ff28f5c28f5c28b | — | — | origin |
| carrier_state | 613 | 612 | 1598522310 | 103 | 6269366 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff28f5c28f5c28f→0x3ff28f5c28f5c28b | — | — | fsu_taint |
| operand_read | 614 | 613 | 1598557730 | 103 | 6269510 | 0x0000000000400654 | fmadd | 6269366/6269510 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 615 | 614 | 1598557730 | 103 | 6269510 | 0x0000000000400654 | fmadd | 6269366/6269510 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 616 | 615 | 1598557730 | 103 | 6269510 | 0x0000000000400654 | fmadd | 6269366/6269510 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 617 | 616 | 1598558500 | 103 | 6269510 | 0x0000000000400654 | fmadd | —/6269510 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1314 | 617 | 9405832205 | 103 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 618 | — | 1607063150 | 104 | 6303206 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff6353f7ced9169→0x3ff6353f7cedd169 | — | — | origin |
| carrier_state | 619 | 618 | 1607063150 | 104 | 6303206 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff6353f7ced9169→0x3ff6353f7cedd169 | — | — | fsu_taint |
| operand_read | 620 | 619 | 1607098570 | 104 | 6303350 | 0x0000000000400654 | fmadd | 6303206/6303350 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 621 | 620 | 1607098570 | 104 | 6303350 | 0x0000000000400654 | fmadd | 6303206/6303350 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 622 | 621 | 1607098570 | 104 | 6303350 | 0x0000000000400654 | fmadd | 6303206/6303350 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 623 | 622 | 1607099340 | 104 | 6303350 | 0x0000000000400654 | fmadd | —/6303350 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1315 | 623 | 9405832205 | 104 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 624 | — | 1624522900 | 105 | 6372359 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4051c00000000000→0x4051c00000000200 | — | — | origin |
| carrier_state | 625 | 624 | 1624522900 | 105 | 6372359 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4051c00000000000→0x4051c00000000200 | — | — | fsu_taint |
| operand_read | 626 | 625 | 1624524825 | 105 | 6372362 | 0x0000000000400654 | fmadd | 6372359/6372362 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 627 | 626 | 1624524825 | 105 | 6372362 | 0x0000000000400654 | fmadd | 6372359/6372362 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 628 | 627 | 1624524825 | 105 | 6372362 | 0x0000000000400654 | fmadd | 6372359/6372362 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 629 | 628 | 1624525595 | 105 | 6372362 | 0x0000000000400654 | fmadd | —/6372362 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1316 | 629 | 9405832205 | 105 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 630 | — | 1636614210 | 106 | 6419990 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3fe53f7ced916873→0x3fe53f7ced916872 | — | — | origin |
| carrier_state | 631 | 630 | 1636614210 | 106 | 6419990 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3fe53f7ced916873→0x3fe53f7ced916872 | — | — | fsu_taint |
| operand_read | 632 | 631 | 1636649630 | 106 | 6420134 | 0x0000000000400654 | fmadd | 6419990/6420134 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 633 | 632 | 1636649630 | 106 | 6420134 | 0x0000000000400654 | fmadd | 6419990/6420134 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 634 | 633 | 1636649630 | 106 | 6420134 | 0x0000000000400654 | fmadd | 6419990/6420134 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 635 | 634 | 1636650400 | 106 | 6420134 | 0x0000000000400654 | fmadd | —/6420134 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1317 | 635 | 9405832205 | 106 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 636 | — | 1659289555 | 107 | 6509377 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x402c000000000000→0x402c000000004000 | — | — | origin |
| carrier_state | 637 | 636 | 1659289555 | 107 | 6509377 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x402c000000000000→0x402c000000004000 | — | — | fsu_taint |
| operand_read | 638 | 637 | 1659293405 | 107 | 6509380 | 0x000000000040065c | fmadd | 6509377/6509380 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 639 | 638 | 1659293405 | 107 | 6509380 | 0x000000000040065c | fmadd | 6509377/6509380 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 640 | 639 | 1659293405 | 107 | 6509380 | 0x000000000040065c | fmadd | 6509377/6509380 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 641 | 640 | 1659294175 | 107 | 6509380 | 0x000000000040065c | fmadd | —/6509380 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1318 | 641 | 9405832205 | 107 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 642 | — | 1671139855 | 108 | 6556140 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4087380000000000→0x4087380000000020 | — | — | origin |
| carrier_state | 643 | 642 | 1671139855 | 108 | 6556140 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4087380000000000→0x4087380000000020 | — | — | fsu_taint |
| operand_read | 644 | 643 | 1671144090 | 108 | 6556143 | 0x0000000000400658 | fmadd | 6556140/6556143 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 645 | 644 | 1671144090 | 108 | 6556143 | 0x0000000000400658 | fmadd | 6556140/6556143 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 646 | 645 | 1671144090 | 108 | 6556143 | 0x0000000000400658 | fmadd | 6556140/6556143 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 647 | 646 | 1671144860 | 108 | 6556143 | 0x0000000000400658 | fmadd | —/6556143 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1319 | 647 | 9405832205 | 108 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 648 | — | 1687967050 | 109 | 6622560 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x408e880000000000→0x408e880000000200 | — | — | origin |
| carrier_state | 649 | 648 | 1687967050 | 109 | 6622560 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x408e880000000000→0x408e880000000200 | — | — | fsu_taint |
| operand_read | 650 | 649 | 1687971285 | 109 | 6622563 | 0x0000000000400658 | fmadd | 6622560/6622563 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 651 | 650 | 1687971285 | 109 | 6622563 | 0x0000000000400658 | fmadd | 6622560/6622563 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 652 | 651 | 1687971285 | 109 | 6622563 | 0x0000000000400658 | fmadd | 6622560/6622563 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 653 | 652 | 1687972055 | 109 | 6622563 | 0x0000000000400658 | fmadd | —/6622563 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1320 | 653 | 9405832205 | 109 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 60 | — | 197174670 | 11 | 740846 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3feda1cac083126f→0x3feda1cac083122f | — | — | origin |
| carrier_state | 61 | 60 | 197174670 | 11 | 740846 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3feda1cac083126f→0x3feda1cac083122f | — | — | fsu_taint |
| operand_read | 62 | 61 | 197210090 | 11 | 740990 | 0x0000000000400654 | fmadd | 740846/740990 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 63 | 62 | 197210090 | 11 | 740990 | 0x0000000000400654 | fmadd | 740846/740990 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 64 | 63 | 197210090 | 11 | 740990 | 0x0000000000400654 | fmadd | 740846/740990 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 65 | 64 | 197210860 | 11 | 740990 | 0x0000000000400654 | fmadd | —/740990 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1222 | 65 | 9405832205 | 11 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 654 | — | 1700740965 | 110 | 6672744 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x408ed00000000000→0x408ed00000001000 | — | — | origin |
| carrier_state | 655 | 654 | 1700740965 | 110 | 6672744 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x408ed00000000000→0x408ed00000001000 | — | — | fsu_taint |
| operand_read | 656 | 655 | 1700745200 | 110 | 6672747 | 0x0000000000400658 | fmadd | 6672744/6672747 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 657 | 656 | 1700745200 | 110 | 6672747 | 0x0000000000400658 | fmadd | 6672744/6672747 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 658 | 657 | 1700745200 | 110 | 6672747 | 0x0000000000400658 | fmadd | 6672744/6672747 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 659 | 658 | 1700745970 | 110 | 6672747 | 0x0000000000400658 | fmadd | —/6672747 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1321 | 659 | 9405832205 | 110 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 660 | — | 1718758195 | 111 | 6743664 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4067400000000000→0x4067400000000080 | — | — | origin |
| carrier_state | 661 | 660 | 1718758195 | 111 | 6743664 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4067400000000000→0x4067400000000080 | — | — | fsu_taint |
| operand_read | 662 | 661 | 1718762430 | 111 | 6743667 | 0x0000000000400658 | fmadd | 6743664/6743667 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 663 | 662 | 1718762430 | 111 | 6743667 | 0x0000000000400658 | fmadd | 6743664/6743667 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 664 | 663 | 1718762430 | 111 | 6743667 | 0x0000000000400658 | fmadd | 6743664/6743667 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 665 | 664 | 1718763200 | 111 | 6743667 | 0x0000000000400658 | fmadd | —/6743667 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1322 | 665 | 9405832205 | 111 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 666 | — | 1738365090 | 112 | 6821068 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd2d0e560418937→0xbfd2d0e560418b37 | — | — | origin |
| carrier_state | 667 | 666 | 1738365090 | 112 | 6821068 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd2d0e560418937→0xbfd2d0e560418b37 | — | — | fsu_taint |
| operand_read | 668 | 667 | 1738380490 | 112 | 6821138 | 0x0000000000400654 | fmadd | 6821068/6821138 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 669 | 668 | 1738380490 | 112 | 6821138 | 0x0000000000400654 | fmadd | 6821068/6821138 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 670 | 669 | 1738380490 | 112 | 6821138 | 0x0000000000400654 | fmadd | 6821068/6821138 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 671 | 670 | 1738381260 | 112 | 6821138 | 0x0000000000400654 | fmadd | —/6821138 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1323 | 671 | 9405832205 | 112 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 672 | — | 1751880130 | 113 | 6874561 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4074000000000000→0x4074000000000002 | — | — | origin |
| carrier_state | 673 | 672 | 1751880130 | 113 | 6874561 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4074000000000000→0x4074000000000002 | — | — | fsu_taint |
| operand_read | 674 | 673 | 1751883980 | 113 | 6874564 | 0x000000000040065c | fmadd | 6874561/6874564 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 675 | 674 | 1751883980 | 113 | 6874564 | 0x000000000040065c | fmadd | 6874561/6874564 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 676 | 675 | 1751883980 | 113 | 6874564 | 0x000000000040065c | fmadd | 6874561/6874564 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 677 | 676 | 1751884750 | 113 | 6874564 | 0x000000000040065c | fmadd | —/6874564 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1324 | 677 | 9405832205 | 113 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 678 | — | 1760725120 | 114 | 6909192 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4071c00000000000→0x4071c00000002000 | — | — | origin |
| carrier_state | 679 | 678 | 1760725120 | 114 | 6909192 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4071c00000000000→0x4071c00000002000 | — | — | fsu_taint |
| operand_read | 680 | 679 | 1760729355 | 114 | 6909195 | 0x0000000000400658 | fmadd | 6909192/6909195 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 681 | 680 | 1760729355 | 114 | 6909195 | 0x0000000000400658 | fmadd | 6909192/6909195 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 682 | 681 | 1760729355 | 114 | 6909195 | 0x0000000000400658 | fmadd | 6909192/6909195 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 683 | 682 | 1760730125 | 114 | 6909195 | 0x0000000000400658 | fmadd | —/6909195 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1325 | 683 | 9405832205 | 114 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 684 | — | 1768899055 | 115 | 6941883 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fd6353f7ced9168→0x3fd6353f7ced9128 | — | — | origin |
| carrier_state | 685 | 684 | 1768899055 | 115 | 6941883 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fd6353f7ced9168→0x3fd6353f7ced9128 | — | — | fsu_taint |
| operand_read | 686 | 685 | 1768923310 | 115 | 6941990 | 0x0000000000400654 | fmadd | 6941883/6941990 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 687 | 686 | 1768923310 | 115 | 6941990 | 0x0000000000400654 | fmadd | 6941883/6941990 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 688 | 687 | 1768923310 | 115 | 6941990 | 0x0000000000400654 | fmadd | 6941883/6941990 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 689 | 688 | 1768924080 | 115 | 6941990 | 0x0000000000400654 | fmadd | —/6941990 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1326 | 689 | 9405832205 | 115 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 690 | — | 1785728945 | 116 | 7007976 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x407ca00000000000→0x407ca00000000001 | — | — | origin |
| carrier_state | 691 | 690 | 1785728945 | 116 | 7007976 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x407ca00000000000→0x407ca00000000001 | — | — | fsu_taint |
| operand_read | 692 | 691 | 1785733180 | 116 | 7007979 | 0x0000000000400658 | fmadd | 7007976/7007979 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 693 | 692 | 1785733180 | 116 | 7007979 | 0x0000000000400658 | fmadd | 7007976/7007979 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 694 | 693 | 1785733180 | 116 | 7007979 | 0x0000000000400658 | fmadd | 7007976/7007979 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 695 | 694 | 1785733950 | 116 | 7007979 | 0x0000000000400658 | fmadd | —/7007979 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1327 | 695 | 9405832205 | 116 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 696 | — | 1807947680 | 117 | 7095638 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fe851eb851eb852→0x3fe851eb851ef852 | — | — | origin |
| carrier_state | 697 | 696 | 1807947680 | 117 | 7095638 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fe851eb851eb852→0x3fe851eb851ef852 | — | — | fsu_taint |
| operand_read | 698 | 697 | 1807983100 | 117 | 7095782 | 0x0000000000400654 | fmadd | 7095638/7095782 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 699 | 698 | 1807983100 | 117 | 7095782 | 0x0000000000400654 | fmadd | 7095638/7095782 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 700 | 699 | 1807983100 | 117 | 7095782 | 0x0000000000400654 | fmadd | 7095638/7095782 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 701 | 700 | 1807983870 | 117 | 7095782 | 0x0000000000400654 | fmadd | —/7095782 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1328 | 701 | 9405832205 | 117 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 702 | — | 1824665535 | 118 | 7162055 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4071f00000000000→0x4071f00000002000 | — | — | origin |
| carrier_state | 703 | 702 | 1824665535 | 118 | 7162055 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4071f00000000000→0x4071f00000002000 | — | — | fsu_taint |
| operand_read | 704 | 703 | 1824667460 | 118 | 7162058 | 0x0000000000400654 | fmadd | 7162055/7162058 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 705 | 704 | 1824667460 | 118 | 7162058 | 0x0000000000400654 | fmadd | 7162055/7162058 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 706 | 705 | 1824667460 | 118 | 7162058 | 0x0000000000400654 | fmadd | 7162055/7162058 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 707 | 706 | 1824668230 | 118 | 7162058 | 0x0000000000400654 | fmadd | —/7162058 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1329 | 707 | 9405832205 | 118 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 708 | — | 1847199200 | 119 | 7251122 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fe7b645a1cac083→0x3fe7b645a1cbc083 | — | — | origin |
| carrier_state | 709 | 708 | 1847199200 | 119 | 7251122 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fe7b645a1cac083→0x3fe7b645a1cbc083 | — | — | fsu_taint |
| operand_read | 710 | 709 | 1847234620 | 119 | 7251266 | 0x0000000000400654 | fmadd | 7251122/7251266 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 711 | 710 | 1847234620 | 119 | 7251266 | 0x0000000000400654 | fmadd | 7251122/7251266 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 712 | 711 | 1847234620 | 119 | 7251266 | 0x0000000000400654 | fmadd | 7251122/7251266 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 713 | 712 | 1847235390 | 119 | 7251266 | 0x0000000000400654 | fmadd | —/7251266 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1330 | 713 | 9405832205 | 119 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 66 | — | 216720735 | 12 | 818316 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4077800000000000→0x4077800000000002 | — | — | origin |
| carrier_state | 67 | 66 | 216720735 | 12 | 818316 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4077800000000000→0x4077800000000002 | — | — | fsu_taint |
| operand_read | 68 | 67 | 216724970 | 12 | 818319 | 0x0000000000400658 | fmadd | 818316/818319 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 69 | 68 | 216724970 | 12 | 818319 | 0x0000000000400658 | fmadd | 818316/818319 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 70 | 69 | 216724970 | 12 | 818319 | 0x0000000000400658 | fmadd | 818316/818319 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 71 | 70 | 216725740 | 12 | 818319 | 0x0000000000400658 | fmadd | —/818319 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1223 | 71 | 9405832205 | 12 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 714 | — | 1857310840 | 120 | 7290719 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x408d280000000000→0x408d280000020000 | — | — | origin |
| carrier_state | 715 | 714 | 1857310840 | 120 | 7290719 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x408d280000000000→0x408d280000020000 | — | — | fsu_taint |
| operand_read | 716 | 715 | 1857312765 | 120 | 7290722 | 0x0000000000400654 | fmadd | 7290719/7290722 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 717 | 716 | 1857312765 | 120 | 7290722 | 0x0000000000400654 | fmadd | 7290719/7290722 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 718 | 717 | 1857312765 | 120 | 7290722 | 0x0000000000400654 | fmadd | 7290719/7290722 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 719 | 718 | 1857313535 | 120 | 7290722 | 0x0000000000400654 | fmadd | —/7290722 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1331 | 719 | 9405832205 | 120 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 720 | — | 1878826180 | 121 | 7375248 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4089200000000000→0x4089200000000010 | — | — | origin |
| carrier_state | 721 | 720 | 1878826180 | 121 | 7375248 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4089200000000000→0x4089200000000010 | — | — | fsu_taint |
| operand_read | 722 | 721 | 1878830415 | 121 | 7375251 | 0x0000000000400658 | fmadd | 7375248/7375251 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 723 | 722 | 1878830415 | 121 | 7375251 | 0x0000000000400658 | fmadd | 7375248/7375251 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 724 | 723 | 1878830415 | 121 | 7375251 | 0x0000000000400658 | fmadd | 7375248/7375251 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 725 | 724 | 1878831185 | 121 | 7375251 | 0x0000000000400658 | fmadd | —/7375251 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1332 | 725 | 9405832205 | 121 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 726 | — | 1900537870 | 122 | 7460643 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff01cac083126ea→0x3ff01cac083326ea | — | — | origin |
| carrier_state | 727 | 726 | 1900537870 | 122 | 7460643 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff01cac083126ea→0x3ff01cac083326ea | — | — | fsu_taint |
| operand_read | 728 | 727 | 1900562125 | 122 | 7460750 | 0x0000000000400654 | fmadd | 7460643/7460750 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 729 | 728 | 1900562125 | 122 | 7460750 | 0x0000000000400654 | fmadd | 7460643/7460750 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 730 | 729 | 1900562125 | 122 | 7460750 | 0x0000000000400654 | fmadd | 7460643/7460750 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 731 | 730 | 1900562895 | 122 | 7460750 | 0x0000000000400654 | fmadd | —/7460750 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1333 | 731 | 9405832205 | 122 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 732 | — | 1914069850 | 123 | 7514675 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4080200000000000→0x4080200000010000 | — | — | origin |
| carrier_state | 733 | 732 | 1914069850 | 123 | 7514675 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4080200000000000→0x4080200000010000 | — | — | fsu_taint |
| operand_read | 734 | 733 | 1914071775 | 123 | 7514678 | 0x0000000000400654 | fmadd | 7514675/7514678 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 735 | 734 | 1914071775 | 123 | 7514678 | 0x0000000000400654 | fmadd | 7514675/7514678 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 736 | 735 | 1914071775 | 123 | 7514678 | 0x0000000000400654 | fmadd | 7514675/7514678 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 737 | 736 | 1914072545 | 123 | 7514678 | 0x0000000000400654 | fmadd | —/7514678 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1334 | 737 | 9405832205 | 123 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 738 | — | 1936794475 | 124 | 7604427 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3ff34bc6a7ef9db2→0x3ff34bc6a7ef9cb2 | — | — | origin |
| carrier_state | 739 | 738 | 1936794475 | 124 | 7604427 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3ff34bc6a7ef9db2→0x3ff34bc6a7ef9cb2 | — | — | fsu_taint |
| operand_read | 740 | 739 | 1936818730 | 124 | 7604534 | 0x0000000000400654 | fmadd | 7604427/7604534 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 741 | 740 | 1936818730 | 124 | 7604534 | 0x0000000000400654 | fmadd | 7604427/7604534 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 742 | 741 | 1936818730 | 124 | 7604534 | 0x0000000000400654 | fmadd | 7604427/7604534 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 743 | 742 | 1936819500 | 124 | 7604534 | 0x0000000000400654 | fmadd | —/7604534 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1335 | 743 | 9405832205 | 124 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 744 | — | 1957812010 | 125 | 7687007 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x406ca00000000000→0x406ca00000000001 | — | — | origin |
| carrier_state | 745 | 744 | 1957812010 | 125 | 7687007 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x406ca00000000000→0x406ca00000000001 | — | — | fsu_taint |
| operand_read | 746 | 745 | 1957813935 | 125 | 7687010 | 0x0000000000400654 | fmadd | 7687007/7687010 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 747 | 746 | 1957813935 | 125 | 7687010 | 0x0000000000400654 | fmadd | 7687007/7687010 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 748 | 747 | 1957813935 | 125 | 7687010 | 0x0000000000400654 | fmadd | 7687007/7687010 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 749 | 748 | 1957814705 | 125 | 7687010 | 0x0000000000400654 | fmadd | —/7687010 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1336 | 749 | 9405832205 | 125 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 750 | — | 1973830705 | 126 | 7750300 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0xbfd5b22d0e560419→0xbfd5b22d0e560619 | — | — | origin |
| carrier_state | 751 | 750 | 1973830705 | 126 | 7750300 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0xbfd5b22d0e560419→0xbfd5b22d0e560619 | — | — | fsu_taint |
| operand_read | 752 | 751 | 1973846105 | 126 | 7750370 | 0x0000000000400654 | fmadd | 7750300/7750370 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 753 | 752 | 1973846105 | 126 | 7750370 | 0x0000000000400654 | fmadd | 7750300/7750370 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 754 | 753 | 1973846105 | 126 | 7750370 | 0x0000000000400654 | fmadd | 7750300/7750370 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 755 | 754 | 1973846875 | 126 | 7750370 | 0x0000000000400654 | fmadd | —/7750370 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1337 | 755 | 9405832205 | 126 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 756 | — | 1993721730 | 127 | 7828887 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe2b020c49ba5e3→0x3fe2b020c49ba5eb | — | — | origin |
| carrier_state | 757 | 756 | 1993721730 | 127 | 7828887 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe2b020c49ba5e3→0x3fe2b020c49ba5eb | — | — | fsu_taint |
| operand_read | 758 | 757 | 1993853785 | 127 | 7828994 | 0x0000000000400654 | fmadd | 7828887/7828994 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 759 | 758 | 1993853785 | 127 | 7828994 | 0x0000000000400654 | fmadd | 7828887/7828994 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 760 | 759 | 1993853785 | 127 | 7828994 | 0x0000000000400654 | fmadd | 7828887/7828994 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 761 | 760 | 1993854555 | 127 | 7828994 | 0x0000000000400654 | fmadd | —/7828994 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1338 | 761 | 9405832205 | 127 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 762 | — | 2014969110 | 128 | 7912840 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fc7ef9db22d0e57→0x3fc7ef9db22d0e17 | — | — | origin |
| carrier_state | 763 | 762 | 2014969110 | 128 | 7912840 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fc7ef9db22d0e57→0x3fc7ef9db22d0e17 | — | — | fsu_taint |
| operand_read | 764 | 763 | 2014984510 | 128 | 7912910 | 0x0000000000400654 | fmadd | 7912840/7912910 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 765 | 764 | 2014984510 | 128 | 7912910 | 0x0000000000400654 | fmadd | 7912840/7912910 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 766 | 765 | 2014984510 | 128 | 7912910 | 0x0000000000400654 | fmadd | 7912840/7912910 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 767 | 766 | 2014985280 | 128 | 7912910 | 0x0000000000400654 | fmadd | —/7912910 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1339 | 767 | 9405832205 | 128 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 768 | — | 2032010365 | 129 | 7979834 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff26a7ef9db22d1→0x3ff26a7ef9db32d1 | — | — | origin |
| carrier_state | 769 | 768 | 2032010365 | 129 | 7979834 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff26a7ef9db22d1→0x3ff26a7ef9db32d1 | — | — | fsu_taint |
| operand_read | 770 | 769 | 2032045785 | 129 | 7979978 | 0x0000000000400654 | fmadd | 7979834/7979978 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 771 | 770 | 2032045785 | 129 | 7979978 | 0x0000000000400654 | fmadd | 7979834/7979978 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 772 | 771 | 2032045785 | 129 | 7979978 | 0x0000000000400654 | fmadd | 7979834/7979978 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 773 | 772 | 2032046555 | 129 | 7979978 | 0x0000000000400654 | fmadd | —/7979978 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1340 | 773 | 9405832205 | 129 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 72 | — | 229080390 | 13 | 866487 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3ff05604189374bc→0x3ff0560418937cbc | — | — | origin |
| carrier_state | 73 | 72 | 229080390 | 13 | 866487 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3ff05604189374bc→0x3ff0560418937cbc | — | — | fsu_taint |
| operand_read | 74 | 73 | 229104645 | 13 | 866594 | 0x0000000000400654 | fmadd | 866487/866594 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 75 | 74 | 229104645 | 13 | 866594 | 0x0000000000400654 | fmadd | 866487/866594 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 76 | 75 | 229104645 | 13 | 866594 | 0x0000000000400654 | fmadd | 866487/866594 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 77 | 76 | 229105415 | 13 | 866594 | 0x0000000000400654 | fmadd | —/866594 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1224 | 77 | 9405832205 | 13 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 774 | — | 2043556130 | 130 | 8025302 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff7ef9db22d0e56→0x3ff7ef9db22d0c56 | — | — | origin |
| carrier_state | 775 | 774 | 2043556130 | 130 | 8025302 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff7ef9db22d0e56→0x3ff7ef9db22d0c56 | — | — | fsu_taint |
| operand_read | 776 | 775 | 2043591550 | 130 | 8025446 | 0x0000000000400654 | fmadd | 8025302/8025446 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 777 | 776 | 2043591550 | 130 | 8025446 | 0x0000000000400654 | fmadd | 8025302/8025446 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 778 | 777 | 2043591550 | 130 | 8025446 | 0x0000000000400654 | fmadd | 8025302/8025446 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 779 | 778 | 2043592320 | 130 | 8025446 | 0x0000000000400654 | fmadd | —/8025446 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1341 | 779 | 9405832205 | 130 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 780 | — | 2056917555 | 131 | 8078219 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x408a100000000000→0x408a100000020000 | — | — | origin |
| carrier_state | 781 | 780 | 2056917555 | 131 | 8078219 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x408a100000000000→0x408a100000020000 | — | — | fsu_taint |
| operand_read | 782 | 781 | 2056919480 | 131 | 8078222 | 0x0000000000400654 | fmadd | 8078219/8078222 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 783 | 782 | 2056919480 | 131 | 8078222 | 0x0000000000400654 | fmadd | 8078219/8078222 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 784 | 783 | 2056919480 | 131 | 8078222 | 0x0000000000400654 | fmadd | 8078219/8078222 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 785 | 784 | 2056920250 | 131 | 8078222 | 0x0000000000400654 | fmadd | —/8078222 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1342 | 785 | 9405832205 | 131 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 786 | — | 2066279215 | 132 | 8114835 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fd10624dd2f1aa0→0x3fd10624dd2f1aa2 | — | — | origin |
| carrier_state | 787 | 786 | 2066279215 | 132 | 8114835 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fd10624dd2f1aa0→0x3fd10624dd2f1aa2 | — | — | fsu_taint |
| operand_read | 788 | 787 | 2066303470 | 132 | 8114942 | 0x0000000000400654 | fmadd | 8114835/8114942 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 789 | 788 | 2066303470 | 132 | 8114942 | 0x0000000000400654 | fmadd | 8114835/8114942 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 790 | 789 | 2066303470 | 132 | 8114942 | 0x0000000000400654 | fmadd | 8114835/8114942 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 791 | 790 | 2066304240 | 132 | 8114942 | 0x0000000000400654 | fmadd | —/8114942 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1343 | 791 | 9405832205 | 132 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 792 | — | 2075928085 | 133 | 8153067 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3ff122d0e5604189→0x3ff122d0e560c189 | — | — | origin |
| carrier_state | 793 | 792 | 2075928085 | 133 | 8153067 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3ff122d0e5604189→0x3ff122d0e560c189 | — | — | fsu_taint |
| operand_read | 794 | 793 | 2075952340 | 133 | 8153174 | 0x0000000000400654 | fmadd | 8153067/8153174 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 795 | 794 | 2075952340 | 133 | 8153174 | 0x0000000000400654 | fmadd | 8153067/8153174 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 796 | 795 | 2075952340 | 133 | 8153174 | 0x0000000000400654 | fmadd | 8153067/8153174 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 797 | 796 | 2075953110 | 133 | 8153174 | 0x0000000000400654 | fmadd | —/8153174 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1344 | 797 | 9405832205 | 133 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 798 | — | 2096476690 | 134 | 8234390 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff72b020c49ba5e→0x3ff72b020c49ba7e | — | — | origin |
| carrier_state | 799 | 798 | 2096476690 | 134 | 8234390 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff72b020c49ba5e→0x3ff72b020c49ba7e | — | — | fsu_taint |
| operand_read | 800 | 799 | 2096619525 | 134 | 8234534 | 0x0000000000400654 | fmadd | 8234390/8234534 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 801 | 800 | 2096619525 | 134 | 8234534 | 0x0000000000400654 | fmadd | 8234390/8234534 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 802 | 801 | 2096619525 | 134 | 8234534 | 0x0000000000400654 | fmadd | 8234390/8234534 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 803 | 802 | 2096620295 | 134 | 8234534 | 0x0000000000400654 | fmadd | —/8234534 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1345 | 803 | 9405832205 | 134 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 804 | — | 2106611815 | 135 | 8274167 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4082580000000000→0x4082580000000800 | — | — | origin |
| carrier_state | 805 | 804 | 2106611815 | 135 | 8274167 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4082580000000000→0x4082580000000800 | — | — | fsu_taint |
| operand_read | 806 | 805 | 2106613740 | 135 | 8274170 | 0x0000000000400654 | fmadd | 8274167/8274170 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 807 | 806 | 2106613740 | 135 | 8274170 | 0x0000000000400654 | fmadd | 8274167/8274170 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 808 | 807 | 2106613740 | 135 | 8274170 | 0x0000000000400654 | fmadd | 8274167/8274170 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 809 | 808 | 2106614510 | 135 | 8274170 | 0x0000000000400654 | fmadd | —/8274170 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1346 | 809 | 9405832205 | 135 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 810 | — | 2126591775 | 136 | 8353010 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff3cac083126e98→0x3ff3cac083127e98 | — | — | origin |
| carrier_state | 811 | 810 | 2126591775 | 136 | 8353010 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff3cac083126e98→0x3ff3cac083127e98 | — | — | fsu_taint |
| operand_read | 812 | 811 | 2126627195 | 136 | 8353154 | 0x0000000000400654 | fmadd | 8353010/8353154 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 813 | 812 | 2126627195 | 136 | 8353154 | 0x0000000000400654 | fmadd | 8353010/8353154 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 814 | 813 | 2126627195 | 136 | 8353154 | 0x0000000000400654 | fmadd | 8353010/8353154 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 815 | 814 | 2126627965 | 136 | 8353154 | 0x0000000000400654 | fmadd | —/8353154 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1347 | 815 | 9405832205 | 136 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 816 | — | 2134640200 | 137 | 8384476 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfa916872b020c48→0xbfa916872b030c48 | — | — | origin |
| carrier_state | 817 | 816 | 2134640200 | 137 | 8384476 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfa916872b020c48→0xbfa916872b030c48 | — | — | fsu_taint |
| operand_read | 818 | 817 | 2134655600 | 137 | 8384546 | 0x0000000000400654 | fmadd | 8384476/8384546 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 819 | 818 | 2134655600 | 137 | 8384546 | 0x0000000000400654 | fmadd | 8384476/8384546 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 820 | 819 | 2134655600 | 137 | 8384546 | 0x0000000000400654 | fmadd | 8384476/8384546 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 821 | 820 | 2134656370 | 137 | 8384546 | 0x0000000000400654 | fmadd | —/8384546 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1348 | 821 | 9405832205 | 137 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 822 | — | 2152198125 | 138 | 8454349 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4071900000000000→0x4071900000010000 | — | — | origin |
| carrier_state | 823 | 822 | 2152198125 | 138 | 8454349 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4071900000000000→0x4071900000010000 | — | — | fsu_taint |
| operand_read | 824 | 823 | 2152201975 | 138 | 8454352 | 0x000000000040065c | fmadd | 8454349/8454352 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 825 | 824 | 2152201975 | 138 | 8454352 | 0x000000000040065c | fmadd | 8454349/8454352 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 826 | 825 | 2152201975 | 138 | 8454352 | 0x000000000040065c | fmadd | 8454349/8454352 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 827 | 826 | 2152202745 | 138 | 8454352 | 0x000000000040065c | fmadd | —/8454352 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1349 | 827 | 9405832205 | 138 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 828 | — | 2174504640 | 139 | 8542300 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0x3fd3f7ced916872b→0x3fd3f7ced916862b | — | — | origin |
| carrier_state | 829 | 828 | 2174504640 | 139 | 8542300 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0x3fd3f7ced916872b→0x3fd3f7ced916862b | — | — | fsu_taint |
| operand_read | 830 | 829 | 2174520040 | 139 | 8542370 | 0x0000000000400654 | fmadd | 8542300/8542370 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 831 | 830 | 2174520040 | 139 | 8542370 | 0x0000000000400654 | fmadd | 8542300/8542370 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 832 | 831 | 2174520040 | 139 | 8542370 | 0x0000000000400654 | fmadd | 8542300/8542370 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 833 | 832 | 2174520810 | 139 | 8542370 | 0x0000000000400654 | fmadd | —/8542370 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1350 | 833 | 9405832205 | 139 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 78 | — | 238830130 | 14 | 905255 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x4081f80000000000→0x4081f80000000002 | — | — | origin |
| carrier_state | 79 | 78 | 238830130 | 14 | 905255 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x4081f80000000000→0x4081f80000000002 | — | — | fsu_taint |
| operand_read | 80 | 79 | 238832055 | 14 | 905258 | 0x0000000000400654 | fmadd | 905255/905258 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 81 | 80 | 238832055 | 14 | 905258 | 0x0000000000400654 | fmadd | 905255/905258 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 82 | 81 | 238832055 | 14 | 905258 | 0x0000000000400654 | fmadd | 905255/905258 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 83 | 82 | 238832825 | 14 | 905258 | 0x0000000000400654 | fmadd | —/905258 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1225 | 83 | 9405832205 | 14 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 834 | — | 2194061100 | 140 | 8619444 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x408e000000000000→0x408e000000002000 | — | — | origin |
| carrier_state | 835 | 834 | 2194061100 | 140 | 8619444 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x408e000000000000→0x408e000000002000 | — | — | fsu_taint |
| operand_read | 836 | 835 | 2194065335 | 140 | 8619447 | 0x0000000000400658 | fmadd | 8619444/8619447 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 837 | 836 | 2194065335 | 140 | 8619447 | 0x0000000000400658 | fmadd | 8619444/8619447 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 838 | 837 | 2194065335 | 140 | 8619447 | 0x0000000000400658 | fmadd | 8619444/8619447 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 839 | 838 | 2194066105 | 140 | 8619447 | 0x0000000000400658 | fmadd | —/8619447 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1351 | 839 | 9405832205 | 140 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 840 | — | 2208348450 | 141 | 8675567 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4078100000000000→0x4078100000000002 | — | — | origin |
| carrier_state | 841 | 840 | 2208348450 | 141 | 8675567 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4078100000000000→0x4078100000000002 | — | — | fsu_taint |
| operand_read | 842 | 841 | 2208350375 | 141 | 8675570 | 0x0000000000400654 | fmadd | 8675567/8675570 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 843 | 842 | 2208350375 | 141 | 8675570 | 0x0000000000400654 | fmadd | 8675567/8675570 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 844 | 843 | 2208350375 | 141 | 8675570 | 0x0000000000400654 | fmadd | 8675567/8675570 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 845 | 844 | 2208351145 | 141 | 8675570 | 0x0000000000400654 | fmadd | —/8675570 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1352 | 845 | 9405832205 | 141 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 846 | — | 2229020640 | 142 | 8756822 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff6e978d4fdf3b6→0x3ff6e978d4fdf3b4 | — | — | origin |
| carrier_state | 847 | 846 | 2229020640 | 142 | 8756822 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff6e978d4fdf3b6→0x3ff6e978d4fdf3b4 | — | — | fsu_taint |
| operand_read | 848 | 847 | 2229056060 | 142 | 8756966 | 0x0000000000400654 | fmadd | 8756822/8756966 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 849 | 848 | 2229056060 | 142 | 8756966 | 0x0000000000400654 | fmadd | 8756822/8756966 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 850 | 849 | 2229056060 | 142 | 8756966 | 0x0000000000400654 | fmadd | 8756822/8756966 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 851 | 850 | 2229056830 | 142 | 8756966 | 0x0000000000400654 | fmadd | —/8756966 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1353 | 851 | 9405832205 | 142 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 852 | — | 2244853765 | 143 | 8819675 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x4080300000000000→0x4080300000000020 | — | — | origin |
| carrier_state | 853 | 852 | 2244853765 | 143 | 8819675 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x4080300000000000→0x4080300000000020 | — | — | fsu_taint |
| operand_read | 854 | 853 | 2244855690 | 143 | 8819678 | 0x0000000000400654 | fmadd | 8819675/8819678 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 855 | 854 | 2244855690 | 143 | 8819678 | 0x0000000000400654 | fmadd | 8819675/8819678 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 856 | 855 | 2244855690 | 143 | 8819678 | 0x0000000000400654 | fmadd | 8819675/8819678 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 857 | 856 | 2244856460 | 143 | 8819678 | 0x0000000000400654 | fmadd | —/8819678 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1354 | 857 | 9405832205 | 143 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 858 | — | 2264658550 | 144 | 8897903 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4072100000000000→0x4072100000000010 | — | — | origin |
| carrier_state | 859 | 858 | 2264658550 | 144 | 8897903 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4072100000000000→0x4072100000000010 | — | — | fsu_taint |
| operand_read | 860 | 859 | 2264660475 | 144 | 8897906 | 0x0000000000400654 | fmadd | 8897903/8897906 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 861 | 860 | 2264660475 | 144 | 8897906 | 0x0000000000400654 | fmadd | 8897903/8897906 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 862 | 861 | 2264660475 | 144 | 8897906 | 0x0000000000400654 | fmadd | 8897903/8897906 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 863 | 862 | 2264661245 | 144 | 8897906 | 0x0000000000400654 | fmadd | —/8897906 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1355 | 863 | 9405832205 | 144 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 864 | — | 2286882675 | 145 | 8985172 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd6353f7ced9169→0x3fd6353f7ced1169 | — | — | origin |
| carrier_state | 865 | 864 | 2286882675 | 145 | 8985172 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd6353f7ced9169→0x3fd6353f7ced1169 | — | — | fsu_taint |
| operand_read | 866 | 865 | 2286898075 | 145 | 8985242 | 0x0000000000400654 | fmadd | 8985172/8985242 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 867 | 866 | 2286898075 | 145 | 8985242 | 0x0000000000400654 | fmadd | 8985172/8985242 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 868 | 867 | 2286898075 | 145 | 8985242 | 0x0000000000400654 | fmadd | 8985172/8985242 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 869 | 868 | 2286898845 | 145 | 8985242 | 0x0000000000400654 | fmadd | —/8985242 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1356 | 869 | 9405832205 | 145 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 870 | — | 2306278590 | 146 | 9061996 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0x3fd947ae147ae148→0x3fd947ae147af148 | — | — | origin |
| carrier_state | 871 | 870 | 2306278590 | 146 | 9061996 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0x3fd947ae147ae148→0x3fd947ae147af148 | — | — | fsu_taint |
| operand_read | 872 | 871 | 2306293990 | 146 | 9062066 | 0x0000000000400654 | fmadd | 9061996/9062066 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 873 | 872 | 2306293990 | 146 | 9062066 | 0x0000000000400654 | fmadd | 9061996/9062066 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 874 | 873 | 2306293990 | 146 | 9062066 | 0x0000000000400654 | fmadd | 9061996/9062066 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 875 | 874 | 2306294760 | 146 | 9062066 | 0x0000000000400654 | fmadd | —/9062066 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1357 | 875 | 9405832205 | 146 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 876 | — | 2328351025 | 147 | 9149007 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fd1cac083126e98→0x3fd1cac083126e90 | — | — | origin |
| carrier_state | 877 | 876 | 2328351025 | 147 | 9149007 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fd1cac083126e98→0x3fd1cac083126e90 | — | — | fsu_taint |
| operand_read | 878 | 877 | 2328375280 | 147 | 9149114 | 0x0000000000400654 | fmadd | 9149007/9149114 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 879 | 878 | 2328375280 | 147 | 9149114 | 0x0000000000400654 | fmadd | 9149007/9149114 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 880 | 879 | 2328375280 | 147 | 9149114 | 0x0000000000400654 | fmadd | 9149007/9149114 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 881 | 880 | 2328376050 | 147 | 9149114 | 0x0000000000400654 | fmadd | —/9149114 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1358 | 881 | 9405832205 | 147 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 882 | — | 2349807075 | 148 | 9233464 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fdb645a1cac0832→0x3fdb645a1cac0032 | — | — | origin |
| carrier_state | 883 | 882 | 2349807075 | 148 | 9233464 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fdb645a1cac0832→0x3fdb645a1cac0032 | — | — | fsu_taint |
| operand_read | 884 | 883 | 2349822475 | 148 | 9233534 | 0x0000000000400654 | fmadd | 9233464/9233534 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 885 | 884 | 2349822475 | 148 | 9233534 | 0x0000000000400654 | fmadd | 9233464/9233534 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 886 | 885 | 2349822475 | 148 | 9233534 | 0x0000000000400654 | fmadd | 9233464/9233534 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 887 | 886 | 2349823245 | 148 | 9233534 | 0x0000000000400654 | fmadd | —/9233534 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1359 | 887 | 9405832205 | 148 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 888 | — | 2360703345 | 149 | 9276879 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe2978d4fdf3b64→0x3fe2978d4fdf3b44 | — | — | origin |
| carrier_state | 889 | 888 | 2360703345 | 149 | 9276879 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe2978d4fdf3b64→0x3fe2978d4fdf3b44 | — | — | fsu_taint |
| operand_read | 890 | 889 | 2360727600 | 149 | 9276986 | 0x0000000000400654 | fmadd | 9276879/9276986 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 891 | 890 | 2360727600 | 149 | 9276986 | 0x0000000000400654 | fmadd | 9276879/9276986 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 892 | 891 | 2360727600 | 149 | 9276986 | 0x0000000000400654 | fmadd | 9276879/9276986 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 893 | 892 | 2360728370 | 149 | 9276986 | 0x0000000000400654 | fmadd | —/9276986 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1360 | 893 | 9405832205 | 149 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 84 | — | 260913730 | 15 | 992019 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff20c49ba5e3540→0x3ff20c49ba5e3548 | — | — | origin |
| carrier_state | 85 | 84 | 260913730 | 15 | 992019 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff20c49ba5e3540→0x3ff20c49ba5e3548 | — | — | fsu_taint |
| operand_read | 86 | 85 | 260937985 | 15 | 992126 | 0x0000000000400654 | fmadd | 992019/992126 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 87 | 86 | 260937985 | 15 | 992126 | 0x0000000000400654 | fmadd | 992019/992126 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 88 | 87 | 260937985 | 15 | 992126 | 0x0000000000400654 | fmadd | 992019/992126 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 89 | 88 | 260938755 | 15 | 992126 | 0x0000000000400654 | fmadd | —/992126 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1226 | 89 | 9405832205 | 15 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 894 | — | 2378612775 | 150 | 9347364 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4087880000000000→0x4087880000002000 | — | — | origin |
| carrier_state | 895 | 894 | 2378612775 | 150 | 9347364 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4087880000000000→0x4087880000002000 | — | — | fsu_taint |
| operand_read | 896 | 895 | 2378617010 | 150 | 9347367 | 0x0000000000400658 | fmadd | 9347364/9347367 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 897 | 896 | 2378617010 | 150 | 9347367 | 0x0000000000400658 | fmadd | 9347364/9347367 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 898 | 897 | 2378617010 | 150 | 9347367 | 0x0000000000400658 | fmadd | 9347364/9347367 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 899 | 898 | 2378617780 | 150 | 9347367 | 0x0000000000400658 | fmadd | —/9347367 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1361 | 899 | 9405832205 | 150 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 900 | — | 2394571025 | 151 | 9410366 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fe8e5604189374c→0x3fe8e5604189375c | — | — | origin |
| carrier_state | 901 | 900 | 2394571025 | 151 | 9410366 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fe8e5604189374c→0x3fe8e5604189375c | — | — | fsu_taint |
| operand_read | 902 | 901 | 2394606445 | 151 | 9410510 | 0x0000000000400654 | fmadd | 9410366/9410510 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 903 | 902 | 2394606445 | 151 | 9410510 | 0x0000000000400654 | fmadd | 9410366/9410510 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 904 | 903 | 2394606445 | 151 | 9410510 | 0x0000000000400654 | fmadd | 9410366/9410510 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 905 | 904 | 2394607215 | 151 | 9410510 | 0x0000000000400654 | fmadd | —/9410510 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1362 | 905 | 9405832205 | 151 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 906 | — | 2431136400 | 152 | 9475246 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fdf8d21bc126a67→0x3fdf8d21bc126ae7 | — | — | origin |
| carrier_state | 907 | 906 | 2431136400 | 152 | 9475246 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fdf8d21bc126a67→0x3fdf8d21bc126ae7 | — | — | fsu_taint |
| operand_read | 908 | 907 | 2431144870 | 152 | 9475262 | 0x00000000004006a4 | fmadd | 9475246/9475262 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 909 | 908 | 2431144870 | 152 | 9475262 | 0x00000000004006a4 | fmadd | 9475246/9475262 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 910 | 909 | 2431144870 | 152 | 9475262 | 0x00000000004006a4 | fmadd | 9475246/9475262 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 911 | 910 | 2431145640 | 152 | 9475262 | 0x00000000004006a4 | fmadd | —/9475262 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1363 | 911 | 9405832205 | 152 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 912 | — | 2488167220 | 153 | 9542676 | 0x00000000004006cc | fmadd | —/— | 6 | — | 64@0 | 0x3fe3f05c896dd26d→0x3fe3f05c896dc26d | — | — | origin |
| carrier_state | 913 | 912 | 2488167220 | 153 | 9542676 | 0x00000000004006cc | fmadd | —/— | 6 | — | 64@0 | 0x3fe3f05c896dd26d→0x3fe3f05c896dc26d | — | — | fsu_taint |
| operand_read | 914 | 913 | 2488175690 | 153 | 9542692 | 0x00000000004006cc | fmadd | 9542676/9542692 | 6 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 915 | 914 | 2488175690 | 153 | 9542692 | 0x00000000004006cc | fmadd | 9542676/9542692 | 6 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 916 | 915 | 2488175690 | 153 | 9542692 | 0x00000000004006cc | fmadd | 9542676/9542692 | 6 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 917 | 916 | 2488176460 | 153 | 9542692 | 0x00000000004006cc | fmadd | —/9542692 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1364 | 917 | 9405832205 | 153 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 918 | — | 2560693520 | 154 | 9627339 | 0x00000000004006a4 | fmadd | —/— | 4 | — | 64@0 | 0x3fe9978d4fdf3b65→0x3fe9978d4fdf3965 | — | — | origin |
| carrier_state | 919 | 918 | 2560693520 | 154 | 9627339 | 0x00000000004006a4 | fmadd | —/— | 4 | — | 64@0 | 0x3fe9978d4fdf3b65→0x3fe9978d4fdf3965 | — | — | fsu_taint |
| operand_read | 920 | 919 | 2560701990 | 154 | 9627355 | 0x00000000004006a4 | fmadd | 9627339/9627355 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 921 | 920 | 2560701990 | 154 | 9627355 | 0x00000000004006a4 | fmadd | 9627339/9627355 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 922 | 921 | 2560701990 | 154 | 9627355 | 0x00000000004006a4 | fmadd | 9627339/9627355 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 923 | 922 | 2560702760 | 154 | 9627355 | 0x00000000004006a4 | fmadd | —/9627355 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1365 | 923 | 9405832205 | 154 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 924 | — | 2607115665 | 155 | 9692581 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x40000b417ca2120e→0x40000b417ca2920e | — | — | origin |
| carrier_state | 925 | 924 | 2607115665 | 155 | 9692581 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x40000b417ca2120e→0x40000b417ca2920e | — | — | fsu_taint |
| operand_read | 926 | 925 | 2607124135 | 155 | 9692597 | 0x00000000004006cc | fmadd | 9692581/9692597 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 927 | 926 | 2607124135 | 155 | 9692597 | 0x00000000004006cc | fmadd | 9692581/9692597 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 928 | 927 | 2607124135 | 155 | 9692597 | 0x00000000004006cc | fmadd | 9692581/9692597 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 929 | 928 | 2607124905 | 155 | 9692597 | 0x00000000004006cc | fmadd | —/9692597 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1366 | 929 | 9405832205 | 155 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 930 | — | 2634521120 | 156 | 9733257 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fcd590c0ad03d9b→0x3fcd590c0ad03d9f | — | — | origin |
| carrier_state | 931 | 930 | 2634521120 | 156 | 9733257 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fcd590c0ad03d9b→0x3fcd590c0ad03d9f | — | — | fsu_taint |
| operand_read | 932 | 931 | 2634529590 | 156 | 9733273 | 0x00000000004006a4 | fmadd | 9733257/9733273 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 933 | 932 | 2634529590 | 156 | 9733273 | 0x00000000004006a4 | fmadd | 9733257/9733273 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 934 | 933 | 2634529590 | 156 | 9733273 | 0x00000000004006a4 | fmadd | 9733257/9733273 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 935 | 934 | 2634530360 | 156 | 9733273 | 0x00000000004006a4 | fmadd | —/9733273 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1367 | 935 | 9405832205 | 156 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 936 | — | 2718742180 | 157 | 9853035 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fe900713f077ccd→0x3fe900713f073ccd | — | — | origin |
| carrier_state | 937 | 936 | 2718742180 | 157 | 9853035 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fe900713f077ccd→0x3fe900713f073ccd | — | — | fsu_taint |
| operand_read | 938 | 937 | 2718750650 | 157 | 9853051 | 0x00000000004006a4 | fmadd | 9853035/9853051 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 939 | 938 | 2718750650 | 157 | 9853051 | 0x00000000004006a4 | fmadd | 9853035/9853051 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 940 | 939 | 2718750650 | 157 | 9853051 | 0x00000000004006a4 | fmadd | 9853035/9853051 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 941 | 940 | 2718751420 | 157 | 9853051 | 0x00000000004006a4 | fmadd | —/9853051 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1368 | 941 | 9405832205 | 157 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 942 | — | 2800165830 | 158 | 9967921 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff88787485e3da3→0x3ff88787485e35a3 | — | — | origin |
| carrier_state | 943 | 942 | 2800165830 | 158 | 9967921 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff88787485e3da3→0x3ff88787485e35a3 | — | — | fsu_taint |
| operand_read | 944 | 943 | 2800174300 | 158 | 9967937 | 0x00000000004006cc | fmadd | 9967921/9967937 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 945 | 944 | 2800174300 | 158 | 9967937 | 0x00000000004006cc | fmadd | 9967921/9967937 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 946 | 945 | 2800174300 | 158 | 9967937 | 0x00000000004006cc | fmadd | 9967921/9967937 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 947 | 946 | 2800175070 | 158 | 9967937 | 0x00000000004006cc | fmadd | —/9967937 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1369 | 947 | 9405832205 | 158 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 948 | — | 2880648155 | 159 | 10075683 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fc556c0d6f544bb→0x3fc556c0d6f564bb | — | — | origin |
| carrier_state | 949 | 948 | 2880648155 | 159 | 10075683 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fc556c0d6f544bb→0x3fc556c0d6f564bb | — | — | fsu_taint |
| operand_read | 950 | 949 | 2880656625 | 159 | 10075699 | 0x00000000004006cc | fmadd | 10075683/10075699 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 951 | 950 | 2880656625 | 159 | 10075699 | 0x00000000004006cc | fmadd | 10075683/10075699 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 952 | 951 | 2880656625 | 159 | 10075699 | 0x00000000004006cc | fmadd | 10075683/10075699 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 953 | 952 | 2880657395 | 159 | 10075699 | 0x00000000004006cc | fmadd | —/10075699 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1370 | 953 | 9405832205 | 159 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 90 | — | 270428235 | 16 | 1029316 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fdcfdf3b645a1cb→0x3fdcfdf3b645a9cb | — | — | origin |
| carrier_state | 91 | 90 | 270428235 | 16 | 1029316 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fdcfdf3b645a1cb→0x3fdcfdf3b645a9cb | — | — | fsu_taint |
| operand_read | 92 | 91 | 270443635 | 16 | 1029386 | 0x0000000000400654 | fmadd | 1029316/1029386 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 93 | 92 | 270443635 | 16 | 1029386 | 0x0000000000400654 | fmadd | 1029316/1029386 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 94 | 93 | 270443635 | 16 | 1029386 | 0x0000000000400654 | fmadd | 1029316/1029386 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 95 | 94 | 270444405 | 16 | 1029386 | 0x0000000000400654 | fmadd | —/1029386 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1227 | 95 | 9405832205 | 16 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 954 | — | 2956723385 | 160 | 10174781 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fffef0281ba7fc4→0x3fffef0281ba7fc5 | — | — | origin |
| carrier_state | 955 | 954 | 2956723385 | 160 | 10174781 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fffef0281ba7fc4→0x3fffef0281ba7fc5 | — | — | fsu_taint |
| operand_read | 956 | 955 | 2956731855 | 160 | 10174797 | 0x00000000004006cc | fmadd | 10174781/10174797 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 957 | 956 | 2956731855 | 160 | 10174797 | 0x00000000004006cc | fmadd | 10174781/10174797 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 958 | 957 | 2956731855 | 160 | 10174797 | 0x00000000004006cc | fmadd | 10174781/10174797 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 959 | 958 | 2956732625 | 160 | 10174797 | 0x00000000004006cc | fmadd | —/10174797 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1371 | 959 | 9405832205 | 160 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 960 | — | 2988527080 | 161 | 10234717 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fd65b4245f5ad96→0x3fd65b4245f5ad92 | — | — | origin |
| carrier_state | 961 | 960 | 2988527080 | 161 | 10234717 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fd65b4245f5ad96→0x3fd65b4245f5ad92 | — | — | fsu_taint |
| operand_read | 962 | 961 | 2988535550 | 161 | 10234733 | 0x00000000004006cc | fmadd | 10234717/10234733 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 963 | 962 | 2988535550 | 161 | 10234733 | 0x00000000004006cc | fmadd | 10234717/10234733 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 964 | 963 | 2988535550 | 161 | 10234733 | 0x00000000004006cc | fmadd | 10234717/10234733 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 965 | 964 | 2988536320 | 161 | 10234733 | 0x00000000004006cc | fmadd | —/10234733 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1372 | 965 | 9405832205 | 161 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 966 | — | 3068168180 | 162 | 10340103 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe4cdf8b1572581→0x3fe4cdf8b1572580 | — | — | origin |
| carrier_state | 967 | 966 | 3068168180 | 162 | 10340103 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe4cdf8b1572581→0x3fe4cdf8b1572580 | — | — | fsu_taint |
| operand_read | 968 | 967 | 3068176650 | 162 | 10340119 | 0x00000000004006cc | fmadd | 10340103/10340119 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 969 | 968 | 3068176650 | 162 | 10340119 | 0x00000000004006cc | fmadd | 10340103/10340119 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 970 | 969 | 3068176650 | 162 | 10340119 | 0x00000000004006cc | fmadd | 10340103/10340119 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 971 | 970 | 3068177420 | 162 | 10340119 | 0x00000000004006cc | fmadd | —/10340119 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1373 | 971 | 9405832205 | 162 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 972 | — | 3127991020 | 163 | 10420419 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff8c3f3e0370cdc→0x3ff8c3f3e0370cdd | — | — | origin |
| carrier_state | 973 | 972 | 3127991020 | 163 | 10420419 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff8c3f3e0370cdc→0x3ff8c3f3e0370cdd | — | — | fsu_taint |
| operand_read | 974 | 973 | 3127999490 | 163 | 10420435 | 0x00000000004006a4 | fmadd | 10420419/10420435 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 975 | 974 | 3127999490 | 163 | 10420435 | 0x00000000004006a4 | fmadd | 10420419/10420435 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 976 | 975 | 3127999490 | 163 | 10420435 | 0x00000000004006a4 | fmadd | 10420419/10420435 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 977 | 976 | 3128000260 | 163 | 10420435 | 0x00000000004006a4 | fmadd | —/10420435 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1374 | 977 | 9405832205 | 163 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 978 | — | 3158925000 | 164 | 10466889 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe5fa871a3b14aa→0x3fe5fa871a3b16aa | — | — | origin |
| carrier_state | 979 | 978 | 3158925000 | 164 | 10466889 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe5fa871a3b14aa→0x3fe5fa871a3b16aa | — | — | fsu_taint |
| operand_read | 980 | 979 | 3158933470 | 164 | 10466905 | 0x00000000004006cc | fmadd | 10466889/10466905 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 981 | 980 | 3158933470 | 164 | 10466905 | 0x00000000004006cc | fmadd | 10466889/10466905 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 982 | 981 | 3158933470 | 164 | 10466905 | 0x00000000004006cc | fmadd | 10466889/10466905 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 983 | 982 | 3158934240 | 164 | 10466905 | 0x00000000004006cc | fmadd | —/10466905 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1375 | 983 | 9405832205 | 164 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 984 | — | 3242309455 | 165 | 10580491 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fca374ff865d7cd→0x3fca374ff865d7c9 | — | — | origin |
| carrier_state | 985 | 984 | 3242309455 | 165 | 10580491 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fca374ff865d7cd→0x3fca374ff865d7c9 | — | — | fsu_taint |
| operand_read | 986 | 985 | 3242317925 | 165 | 10580507 | 0x00000000004006cc | fmadd | 10580491/10580507 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 987 | 986 | 3242317925 | 165 | 10580507 | 0x00000000004006cc | fmadd | 10580491/10580507 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 988 | 987 | 3242317925 | 165 | 10580507 | 0x00000000004006cc | fmadd | 10580491/10580507 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 989 | 988 | 3242318695 | 165 | 10580507 | 0x00000000004006cc | fmadd | —/10580507 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1376 | 989 | 9405832205 | 165 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 990 | — | 3329538520 | 166 | 10700101 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff05269595feda6→0x3ff05269595fede6 | — | — | origin |
| carrier_state | 991 | 990 | 3329538520 | 166 | 10700101 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff05269595feda6→0x3ff05269595fede6 | — | — | fsu_taint |
| operand_read | 992 | 991 | 3329546990 | 166 | 10700117 | 0x00000000004006cc | fmadd | 10700101/10700117 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 993 | 992 | 3329546990 | 166 | 10700117 | 0x00000000004006cc | fmadd | 10700101/10700117 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 994 | 993 | 3329546990 | 166 | 10700117 | 0x00000000004006cc | fmadd | 10700101/10700117 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 995 | 994 | 3329547760 | 166 | 10700117 | 0x00000000004006cc | fmadd | —/10700117 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1377 | 995 | 9405832205 | 166 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 996 | — | 3399602360 | 167 | 10806361 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3ff58eb8950763a2→0x3ff58eb8950761a2 | — | — | origin |
| carrier_state | 997 | 996 | 3399602360 | 167 | 10806361 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3ff58eb8950763a2→0x3ff58eb8950761a2 | — | — | fsu_taint |
| operand_read | 998 | 997 | 3399610830 | 167 | 10806377 | 0x00000000004006a4 | fmadd | 10806361/10806377 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 999 | 998 | 3399610830 | 167 | 10806377 | 0x00000000004006a4 | fmadd | 10806361/10806377 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1000 | 999 | 3399610830 | 167 | 10806377 | 0x00000000004006a4 | fmadd | 10806361/10806377 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1001 | 1000 | 3399611600 | 167 | 10806377 | 0x00000000004006a4 | fmadd | —/10806377 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1378 | 1001 | 9405832205 | 167 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1002 | — | 3441613175 | 168 | 10867303 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fecf22c01e68a0d→0x3fecf22c01e6aa0d | — | — | origin |
| carrier_state | 1003 | 1002 | 3441613175 | 168 | 10867303 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fecf22c01e68a0d→0x3fecf22c01e6aa0d | — | — | fsu_taint |
| operand_read | 1004 | 1003 | 3441621645 | 168 | 10867319 | 0x00000000004006cc | fmadd | 10867303/10867319 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1005 | 1004 | 3441621645 | 168 | 10867319 | 0x00000000004006cc | fmadd | 10867303/10867319 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1006 | 1005 | 3441621645 | 168 | 10867319 | 0x00000000004006cc | fmadd | 10867303/10867319 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1007 | 1006 | 3441622415 | 168 | 10867319 | 0x00000000004006cc | fmadd | —/10867319 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1379 | 1007 | 9405832205 | 168 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1008 | — | 3517371165 | 169 | 10965193 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe11c8216c61523→0x3fe11c8216c61423 | — | — | origin |
| carrier_state | 1009 | 1008 | 3517371165 | 169 | 10965193 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe11c8216c61523→0x3fe11c8216c61423 | — | — | fsu_taint |
| operand_read | 1010 | 1009 | 3517379635 | 169 | 10965209 | 0x00000000004006cc | fmadd | 10965193/10965209 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1011 | 1010 | 3517379635 | 169 | 10965209 | 0x00000000004006cc | fmadd | 10965193/10965209 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1012 | 1011 | 3517379635 | 169 | 10965209 | 0x00000000004006cc | fmadd | 10965193/10965209 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1013 | 1012 | 3517380405 | 169 | 10965209 | 0x00000000004006cc | fmadd | —/10965209 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1380 | 1013 | 9405832205 | 169 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 96 | — | 284354455 | 17 | 1084467 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fe9e353f7ced917→0x3fe9e353f7ced915 | — | — | origin |
| carrier_state | 97 | 96 | 284354455 | 17 | 1084467 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fe9e353f7ced917→0x3fe9e353f7ced915 | — | — | fsu_taint |
| operand_read | 98 | 97 | 284378710 | 17 | 1084574 | 0x0000000000400654 | fmadd | 1084467/1084574 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 99 | 98 | 284378710 | 17 | 1084574 | 0x0000000000400654 | fmadd | 1084467/1084574 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 100 | 99 | 284378710 | 17 | 1084574 | 0x0000000000400654 | fmadd | 1084467/1084574 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 101 | 100 | 284379480 | 17 | 1084574 | 0x0000000000400654 | fmadd | —/1084574 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1228 | 101 | 9405832205 | 17 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1014 | — | 3600235485 | 170 | 11082949 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fdd536933a0407e→0x3fdd536933a0007e | — | — | origin |
| carrier_state | 1015 | 1014 | 3600235485 | 170 | 11082949 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fdd536933a0407e→0x3fdd536933a0007e | — | — | fsu_taint |
| operand_read | 1016 | 1015 | 3600243955 | 170 | 11082965 | 0x00000000004006a4 | fmadd | 11082949/11082965 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1017 | 1016 | 3600243955 | 170 | 11082965 | 0x00000000004006a4 | fmadd | 11082949/11082965 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1018 | 1017 | 3600243955 | 170 | 11082965 | 0x00000000004006a4 | fmadd | 11082949/11082965 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1019 | 1018 | 3600244725 | 170 | 11082965 | 0x00000000004006a4 | fmadd | —/11082965 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1381 | 1019 | 9405832205 | 170 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1020 | — | 3642169300 | 171 | 11156359 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fea2120e1f7d73d→0x3fea2120e1f7d73f | — | — | origin |
| carrier_state | 1021 | 1020 | 3642169300 | 171 | 11156359 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fea2120e1f7d73d→0x3fea2120e1f7d73f | — | — | fsu_taint |
| operand_read | 1022 | 1021 | 3642177770 | 171 | 11156375 | 0x00000000004006a4 | fmadd | 11156359/11156375 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1023 | 1022 | 3642177770 | 171 | 11156375 | 0x00000000004006a4 | fmadd | 11156359/11156375 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1024 | 1023 | 3642177770 | 171 | 11156375 | 0x00000000004006a4 | fmadd | 11156359/11156375 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1025 | 1024 | 3642178540 | 171 | 11156375 | 0x00000000004006a4 | fmadd | —/11156375 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1382 | 1025 | 9405832205 | 171 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1026 | — | 3677317875 | 172 | 11197191 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fee9c4da9003eeb→0x3fee9c4da90036eb | — | — | origin |
| carrier_state | 1027 | 1026 | 3677317875 | 172 | 11197191 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fee9c4da9003eeb→0x3fee9c4da90036eb | — | — | fsu_taint |
| operand_read | 1028 | 1027 | 3677326345 | 172 | 11197207 | 0x00000000004006a4 | fmadd | 11197191/11197207 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1029 | 1028 | 3677326345 | 172 | 11197207 | 0x00000000004006a4 | fmadd | 11197191/11197207 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1030 | 1029 | 3677326345 | 172 | 11197207 | 0x00000000004006a4 | fmadd | 11197191/11197207 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1031 | 1030 | 3677327115 | 172 | 11197207 | 0x00000000004006a4 | fmadd | —/11197207 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1383 | 1031 | 9405832205 | 172 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1032 | — | 3734254370 | 173 | 11285117 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe47faa044ae85c→0x3fe47faa0448e85c | — | — | origin |
| carrier_state | 1033 | 1032 | 3734254370 | 173 | 11285117 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe47faa044ae85c→0x3fe47faa0448e85c | — | — | fsu_taint |
| operand_read | 1034 | 1033 | 3734262840 | 173 | 11285133 | 0x00000000004006cc | fmadd | 11285117/11285133 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1035 | 1034 | 3734262840 | 173 | 11285133 | 0x00000000004006cc | fmadd | 11285117/11285133 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1036 | 1035 | 3734262840 | 173 | 11285133 | 0x00000000004006cc | fmadd | 11285117/11285133 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1037 | 1036 | 3734263610 | 173 | 11285133 | 0x00000000004006cc | fmadd | —/11285133 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1384 | 1037 | 9405832205 | 173 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1038 | — | 3791493090 | 174 | 11351113 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fecca7935760392→0x3fecca7935760b92 | — | — | origin |
| carrier_state | 1039 | 1038 | 3791493090 | 174 | 11351113 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fecca7935760392→0x3fecca7935760b92 | — | — | fsu_taint |
| operand_read | 1040 | 1039 | 3791582410 | 174 | 11351129 | 0x00000000004006a4 | fmadd | 11351113/11351129 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1041 | 1040 | 3791582410 | 174 | 11351129 | 0x00000000004006a4 | fmadd | 11351113/11351129 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1042 | 1041 | 3791582410 | 174 | 11351129 | 0x00000000004006a4 | fmadd | 11351113/11351129 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1043 | 1042 | 3791583180 | 174 | 11351129 | 0x00000000004006a4 | fmadd | —/11351129 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1385 | 1043 | 9405832205 | 174 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1044 | — | 3823922795 | 175 | 11410039 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fef52e72da122fb→0x3fef52e72da122fa | — | — | origin |
| carrier_state | 1045 | 1044 | 3823922795 | 175 | 11410039 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fef52e72da122fb→0x3fef52e72da122fa | — | — | fsu_taint |
| operand_read | 1046 | 1045 | 3823931265 | 175 | 11410055 | 0x00000000004006cc | fmadd | 11410039/11410055 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1047 | 1046 | 3823931265 | 175 | 11410055 | 0x00000000004006cc | fmadd | 11410039/11410055 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1048 | 1047 | 3823931265 | 175 | 11410055 | 0x00000000004006cc | fmadd | 11410039/11410055 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1049 | 1048 | 3823932035 | 175 | 11410055 | 0x00000000004006cc | fmadd | —/11410055 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1386 | 1049 | 9405832205 | 175 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1050 | — | 3887274930 | 176 | 11484569 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0xbfbfd273d5bab218→0xbfbfd273d5b8b218 | — | — | origin |
| carrier_state | 1051 | 1050 | 3887274930 | 176 | 11484569 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0xbfbfd273d5bab218→0xbfbfd273d5b8b218 | — | — | fsu_taint |
| operand_read | 1052 | 1051 | 3887283400 | 176 | 11484585 | 0x00000000004006cc | fmadd | 11484569/11484585 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1053 | 1052 | 3887283400 | 176 | 11484585 | 0x00000000004006cc | fmadd | 11484569/11484585 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1054 | 1053 | 3887283400 | 176 | 11484585 | 0x00000000004006cc | fmadd | 11484569/11484585 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1055 | 1054 | 3887284170 | 176 | 11484585 | 0x00000000004006cc | fmadd | —/11484585 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1387 | 1055 | 9405832205 | 176 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1056 | — | 3943639315 | 177 | 11575909 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3fec2b4d8ba40d91→0x3fec2b4d8ba40db1 | — | — | origin |
| carrier_state | 1057 | 1056 | 3943639315 | 177 | 11575909 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3fec2b4d8ba40d91→0x3fec2b4d8ba40db1 | — | — | fsu_taint |
| operand_read | 1058 | 1057 | 3943647785 | 177 | 11575925 | 0x00000000004006a4 | fmadd | 11575909/11575925 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1059 | 1058 | 3943647785 | 177 | 11575925 | 0x00000000004006a4 | fmadd | 11575909/11575925 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1060 | 1059 | 3943647785 | 177 | 11575925 | 0x00000000004006a4 | fmadd | 11575909/11575925 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1061 | 1060 | 3943648555 | 177 | 11575925 | 0x00000000004006a4 | fmadd | —/11575925 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1388 | 1061 | 9405832205 | 177 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1062 | — | 4011627235 | 178 | 11674515 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3feb727dcbddb984→0x3feb727dcbdd3984 | — | — | origin |
| carrier_state | 1063 | 1062 | 4011627235 | 178 | 11674515 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3feb727dcbddb984→0x3feb727dcbdd3984 | — | — | fsu_taint |
| operand_read | 1064 | 1063 | 4011635705 | 178 | 11674531 | 0x00000000004006cc | fmadd | 11674515/11674531 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1065 | 1064 | 4011635705 | 178 | 11674531 | 0x00000000004006cc | fmadd | 11674515/11674531 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1066 | 1065 | 4011635705 | 178 | 11674531 | 0x00000000004006cc | fmadd | 11674515/11674531 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1067 | 1066 | 4011636475 | 178 | 11674531 | 0x00000000004006cc | fmadd | —/11674531 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1389 | 1067 | 9405832205 | 178 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1068 | — | 4087776385 | 179 | 11774213 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fedc69f8c21e1d2→0x3fedc69f8c21e1c2 | — | — | origin |
| carrier_state | 1069 | 1068 | 4087776385 | 179 | 11774213 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fedc69f8c21e1d2→0x3fedc69f8c21e1c2 | — | — | fsu_taint |
| operand_read | 1070 | 1069 | 4087784855 | 179 | 11774229 | 0x00000000004006cc | fmadd | 11774213/11774229 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1071 | 1070 | 4087784855 | 179 | 11774229 | 0x00000000004006cc | fmadd | 11774213/11774229 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1072 | 1071 | 4087784855 | 179 | 11774229 | 0x00000000004006cc | fmadd | 11774213/11774229 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1073 | 1072 | 4087785625 | 179 | 11774229 | 0x00000000004006cc | fmadd | —/11774229 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1390 | 1073 | 9405832205 | 179 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 102 | — | 305363905 | 18 | 1167700 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fc1a9fbe76c8b44→0x3fc1a9fbe76c8344 | — | — | origin |
| carrier_state | 103 | 102 | 305363905 | 18 | 1167700 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fc1a9fbe76c8b44→0x3fc1a9fbe76c8344 | — | — | fsu_taint |
| operand_read | 104 | 103 | 305379305 | 18 | 1167770 | 0x0000000000400654 | fmadd | 1167700/1167770 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 105 | 104 | 305379305 | 18 | 1167770 | 0x0000000000400654 | fmadd | 1167700/1167770 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 106 | 105 | 305379305 | 18 | 1167770 | 0x0000000000400654 | fmadd | 1167700/1167770 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 107 | 106 | 305380075 | 18 | 1167770 | 0x0000000000400654 | fmadd | —/1167770 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1229 | 107 | 9405832205 | 18 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1074 | — | 4117325520 | 180 | 11823889 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fd60cc78e9f6a95→0x3fd60cc78e9f7a95 | — | — | origin |
| carrier_state | 1075 | 1074 | 4117325520 | 180 | 11823889 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fd60cc78e9f6a95→0x3fd60cc78e9f7a95 | — | — | fsu_taint |
| operand_read | 1076 | 1075 | 4117333990 | 180 | 11823905 | 0x00000000004006a4 | fmadd | 11823889/11823905 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1077 | 1076 | 4117333990 | 180 | 11823905 | 0x00000000004006a4 | fmadd | 11823889/11823905 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1078 | 1077 | 4117333990 | 180 | 11823905 | 0x00000000004006a4 | fmadd | 11823889/11823905 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1079 | 1078 | 4117334760 | 180 | 11823905 | 0x00000000004006a4 | fmadd | —/11823905 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1391 | 1079 | 9405832205 | 180 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1080 | — | 4194178065 | 181 | 11931063 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff25a0168b5cc00→0x3ff25a0168b5cc02 | — | — | origin |
| carrier_state | 1081 | 1080 | 4194178065 | 181 | 11931063 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff25a0168b5cc00→0x3ff25a0168b5cc02 | — | — | fsu_taint |
| operand_read | 1082 | 1081 | 4194186535 | 181 | 11931079 | 0x00000000004006cc | fmadd | 11931063/11931079 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1083 | 1082 | 4194186535 | 181 | 11931079 | 0x00000000004006cc | fmadd | 11931063/11931079 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1084 | 1083 | 4194186535 | 181 | 11931079 | 0x00000000004006cc | fmadd | 11931063/11931079 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1085 | 1084 | 4194187305 | 181 | 11931079 | 0x00000000004006cc | fmadd | —/11931079 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1392 | 1085 | 9405832205 | 181 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1086 | — | 4260244450 | 182 | 12012513 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0xbfcbbc1acde19fc2→0xbfcbbc1acde19fc0 | — | — | origin |
| carrier_state | 1087 | 1086 | 4260244450 | 182 | 12012513 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0xbfcbbc1acde19fc2→0xbfcbbc1acde19fc0 | — | — | fsu_taint |
| operand_read | 1088 | 1087 | 4260252920 | 182 | 12012529 | 0x00000000004006cc | fmadd | 12012513/12012529 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1089 | 1088 | 4260252920 | 182 | 12012529 | 0x00000000004006cc | fmadd | 12012513/12012529 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1090 | 1089 | 4260252920 | 182 | 12012529 | 0x00000000004006cc | fmadd | 12012513/12012529 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1091 | 1090 | 4260253690 | 182 | 12012529 | 0x00000000004006cc | fmadd | —/12012529 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1393 | 1091 | 9405832205 | 182 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1092 | — | 4325881945 | 183 | 12113581 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ff33382e44b6e93→0x3ff33382e44b6ed3 | — | — | origin |
| carrier_state | 1093 | 1092 | 4325881945 | 183 | 12113581 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ff33382e44b6e93→0x3ff33382e44b6ed3 | — | — | fsu_taint |
| operand_read | 1094 | 1093 | 4325890415 | 183 | 12113597 | 0x00000000004006a4 | fmadd | 12113581/12113597 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1095 | 1094 | 4325890415 | 183 | 12113597 | 0x00000000004006a4 | fmadd | 12113581/12113597 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1096 | 1095 | 4325890415 | 183 | 12113597 | 0x00000000004006a4 | fmadd | 12113581/12113597 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1097 | 1096 | 4325891185 | 183 | 12113597 | 0x00000000004006a4 | fmadd | —/12113597 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1394 | 1097 | 9405832205 | 183 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1098 | — | 4407891950 | 184 | 12232391 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff14ea7ce0fc2ec→0x3ff14ea7ce0f82ec | — | — | origin |
| carrier_state | 1099 | 1098 | 4407891950 | 184 | 12232391 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff14ea7ce0fc2ec→0x3ff14ea7ce0f82ec | — | — | fsu_taint |
| operand_read | 1100 | 1099 | 4407900420 | 184 | 12232407 | 0x00000000004006a4 | fmadd | 12232391/12232407 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1101 | 1100 | 4407900420 | 184 | 12232407 | 0x00000000004006a4 | fmadd | 12232391/12232407 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1102 | 1101 | 4407900420 | 184 | 12232407 | 0x00000000004006a4 | fmadd | 12232391/12232407 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1103 | 1102 | 4407901190 | 184 | 12232407 | 0x00000000004006a4 | fmadd | —/12232407 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1395 | 1103 | 9405832205 | 184 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1104 | — | 4471610990 | 185 | 12323309 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe3c23b7952d235→0x3fe3c23b7952d275 | — | — | origin |
| carrier_state | 1105 | 1104 | 4471610990 | 185 | 12323309 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe3c23b7952d235→0x3fe3c23b7952d275 | — | — | fsu_taint |
| operand_read | 1106 | 1105 | 4471619460 | 185 | 12323325 | 0x00000000004006cc | fmadd | 12323309/12323325 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1107 | 1106 | 4471619460 | 185 | 12323325 | 0x00000000004006cc | fmadd | 12323309/12323325 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1108 | 1107 | 4471619460 | 185 | 12323325 | 0x00000000004006cc | fmadd | 12323309/12323325 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1109 | 1108 | 4471620230 | 185 | 12323325 | 0x00000000004006cc | fmadd | —/12323325 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1396 | 1109 | 9405832205 | 185 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1110 | — | 4535982990 | 186 | 12400961 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fd86748e4755fff→0x3fd86748e4757fff | — | — | origin |
| carrier_state | 1111 | 1110 | 4535982990 | 186 | 12400961 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fd86748e4755fff→0x3fd86748e4757fff | — | — | fsu_taint |
| operand_read | 1112 | 1111 | 4535991460 | 186 | 12400977 | 0x00000000004006a4 | fmadd | 12400961/12400977 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1113 | 1112 | 4535991460 | 186 | 12400977 | 0x00000000004006a4 | fmadd | 12400961/12400977 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1114 | 1113 | 4535991460 | 186 | 12400977 | 0x00000000004006a4 | fmadd | 12400961/12400977 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1115 | 1114 | 4535992230 | 186 | 12400977 | 0x00000000004006a4 | fmadd | —/12400977 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1397 | 1115 | 9405832205 | 186 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1116 | — | 4558992130 | 187 | 12443143 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fec3dad7518b0d1→0x3fec3dad751830d1 | — | — | origin |
| carrier_state | 1117 | 1116 | 4558992130 | 187 | 12443143 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fec3dad7518b0d1→0x3fec3dad751830d1 | — | — | fsu_taint |
| operand_read | 1118 | 1117 | 4559000600 | 187 | 12443159 | 0x00000000004006cc | fmadd | 12443143/12443159 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1119 | 1118 | 4559000600 | 187 | 12443159 | 0x00000000004006cc | fmadd | 12443143/12443159 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1120 | 1119 | 4559000600 | 187 | 12443159 | 0x00000000004006cc | fmadd | 12443143/12443159 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1121 | 1120 | 4559001370 | 187 | 12443159 | 0x00000000004006cc | fmadd | —/12443159 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1398 | 1121 | 9405832205 | 187 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1122 | — | 4641937300 | 188 | 12555921 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fd78e3ac0c62e4d→0x3fd78e3ac0c62c4d | — | — | origin |
| carrier_state | 1123 | 1122 | 4641937300 | 188 | 12555921 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fd78e3ac0c62e4d→0x3fd78e3ac0c62c4d | — | — | fsu_taint |
| operand_read | 1124 | 1123 | 4641945770 | 188 | 12555937 | 0x00000000004006cc | fmadd | 12555921/12555937 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1125 | 1124 | 4641945770 | 188 | 12555937 | 0x00000000004006cc | fmadd | 12555921/12555937 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1126 | 1125 | 4641945770 | 188 | 12555937 | 0x00000000004006cc | fmadd | 12555921/12555937 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1127 | 1126 | 4641946540 | 188 | 12555937 | 0x00000000004006cc | fmadd | —/12555937 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1399 | 1127 | 9405832205 | 188 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1128 | — | 4669512925 | 189 | 12605069 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe915b1422ccb3a→0x3fe915b1422ccb7a | — | — | origin |
| carrier_state | 1129 | 1128 | 4669512925 | 189 | 12605069 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe915b1422ccb3a→0x3fe915b1422ccb7a | — | — | fsu_taint |
| operand_read | 1130 | 1129 | 4669521395 | 189 | 12605085 | 0x00000000004006a4 | fmadd | 12605069/12605085 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1131 | 1130 | 4669521395 | 189 | 12605085 | 0x00000000004006a4 | fmadd | 12605069/12605085 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1132 | 1131 | 4669521395 | 189 | 12605085 | 0x00000000004006a4 | fmadd | 12605069/12605085 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1133 | 1132 | 4669522165 | 189 | 12605085 | 0x00000000004006a4 | fmadd | —/12605085 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1400 | 1133 | 9405832205 | 189 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 108 | — | 319442970 | 19 | 1223066 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fed26e978d4fdf4→0x3fed26e978d4fdf0 | — | — | origin |
| carrier_state | 109 | 108 | 319442970 | 19 | 1223066 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fed26e978d4fdf4→0x3fed26e978d4fdf0 | — | — | fsu_taint |
| operand_read | 110 | 109 | 319478390 | 19 | 1223210 | 0x0000000000400654 | fmadd | 1223066/1223210 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 111 | 110 | 319478390 | 19 | 1223210 | 0x0000000000400654 | fmadd | 1223066/1223210 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 112 | 111 | 319478390 | 19 | 1223210 | 0x0000000000400654 | fmadd | 1223066/1223210 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 113 | 112 | 319479160 | 19 | 1223210 | 0x0000000000400654 | fmadd | —/1223210 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1230 | 113 | 9405832205 | 19 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1134 | — | 4726535660 | 190 | 12670995 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3feba5daf07bfe7e→0x3feba5daf07bfe7f | — | — | origin |
| carrier_state | 1135 | 1134 | 4726535660 | 190 | 12670995 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3feba5daf07bfe7e→0x3feba5daf07bfe7f | — | — | fsu_taint |
| operand_read | 1136 | 1135 | 4726544130 | 190 | 12671011 | 0x00000000004006cc | fmadd | 12670995/12671011 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1137 | 1136 | 4726544130 | 190 | 12671011 | 0x00000000004006cc | fmadd | 12670995/12671011 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1138 | 1137 | 4726544130 | 190 | 12671011 | 0x00000000004006cc | fmadd | 12670995/12671011 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1139 | 1138 | 4726544900 | 190 | 12671011 | 0x00000000004006cc | fmadd | —/12671011 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1401 | 1139 | 9405832205 | 190 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1140 | — | 4752342980 | 191 | 12719427 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe7543f1c75818d→0x3fe7543f1c75808d | — | — | origin |
| carrier_state | 1141 | 1140 | 4752342980 | 191 | 12719427 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe7543f1c75818d→0x3fe7543f1c75808d | — | — | fsu_taint |
| operand_read | 1142 | 1141 | 4752351450 | 191 | 12719443 | 0x00000000004006cc | fmadd | 12719427/12719443 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1143 | 1142 | 4752351450 | 191 | 12719443 | 0x00000000004006cc | fmadd | 12719427/12719443 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1144 | 1143 | 4752351450 | 191 | 12719443 | 0x00000000004006cc | fmadd | 12719427/12719443 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1145 | 1144 | 4752352220 | 191 | 12719443 | 0x00000000004006cc | fmadd | —/12719443 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1402 | 1145 | 9405832205 | 191 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1146 | — | 4807421465 | 192 | 12786591 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fdc956c0d6f544c→0x3fdc956c0d6d544c | — | — | origin |
| carrier_state | 1147 | 1146 | 4807421465 | 192 | 12786591 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fdc956c0d6f544c→0x3fdc956c0d6d544c | — | — | fsu_taint |
| operand_read | 1148 | 1147 | 4807429935 | 192 | 12786607 | 0x00000000004006a4 | fmadd | 12786591/12786607 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1149 | 1148 | 4807429935 | 192 | 12786607 | 0x00000000004006a4 | fmadd | 12786591/12786607 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1150 | 1149 | 4807429935 | 192 | 12786607 | 0x00000000004006a4 | fmadd | 12786591/12786607 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1151 | 1150 | 4807430705 | 192 | 12786607 | 0x00000000004006a4 | fmadd | —/12786607 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1403 | 1151 | 9405832205 | 192 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1152 | — | 4846815435 | 193 | 12853061 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff21c64ba94bbe5→0x3ff21c64ba94bae5 | — | — | origin |
| carrier_state | 1153 | 1152 | 4846815435 | 193 | 12853061 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff21c64ba94bbe5→0x3ff21c64ba94bae5 | — | — | fsu_taint |
| operand_read | 1154 | 1153 | 4846823905 | 193 | 12853077 | 0x00000000004006cc | fmadd | 12853061/12853077 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1155 | 1154 | 4846823905 | 193 | 12853077 | 0x00000000004006cc | fmadd | 12853061/12853077 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1156 | 1155 | 4846823905 | 193 | 12853077 | 0x00000000004006cc | fmadd | 12853061/12853077 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1157 | 1156 | 4846824675 | 193 | 12853077 | 0x00000000004006cc | fmadd | —/12853077 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1404 | 1157 | 9405832205 | 193 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1158 | — | 4894752555 | 194 | 12911697 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff3ed5ae1cde5d1→0x3ff3ed5ae1cde5d3 | — | — | origin |
| carrier_state | 1159 | 1158 | 4894752555 | 194 | 12911697 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff3ed5ae1cde5d1→0x3ff3ed5ae1cde5d3 | — | — | fsu_taint |
| operand_read | 1160 | 1159 | 4894761025 | 194 | 12911713 | 0x00000000004006a4 | fmadd | 12911697/12911713 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1161 | 1160 | 4894761025 | 194 | 12911713 | 0x00000000004006a4 | fmadd | 12911697/12911713 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1162 | 1161 | 4894761025 | 194 | 12911713 | 0x00000000004006a4 | fmadd | 12911697/12911713 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1163 | 1162 | 4894761795 | 194 | 12911713 | 0x00000000004006a4 | fmadd | —/12911713 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1405 | 1163 | 9405832205 | 194 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1164 | — | 4958445415 | 195 | 13009443 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fd5d9c27e953155→0x3fd5d9c27e953154 | — | — | origin |
| carrier_state | 1165 | 1164 | 4958445415 | 195 | 13009443 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fd5d9c27e953155→0x3fd5d9c27e953154 | — | — | fsu_taint |
| operand_read | 1166 | 1165 | 4958453885 | 195 | 13009459 | 0x00000000004006a4 | fmadd | 13009443/13009459 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1167 | 1166 | 4958453885 | 195 | 13009459 | 0x00000000004006a4 | fmadd | 13009443/13009459 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1168 | 1167 | 4958453885 | 195 | 13009459 | 0x00000000004006a4 | fmadd | 13009443/13009459 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1169 | 1168 | 4958454655 | 195 | 13009459 | 0x00000000004006a4 | fmadd | —/13009459 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1406 | 1169 | 9405832205 | 195 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1170 | — | 5003125435 | 196 | 13058633 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe27f3493858362→0x3fe27f349385a362 | — | — | origin |
| carrier_state | 1171 | 1170 | 5003125435 | 196 | 13058633 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe27f3493858362→0x3fe27f349385a362 | — | — | fsu_taint |
| operand_read | 1172 | 1171 | 5003133905 | 196 | 13058649 | 0x00000000004006cc | fmadd | 13058633/13058649 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1173 | 1172 | 5003133905 | 196 | 13058649 | 0x00000000004006cc | fmadd | 13058633/13058649 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1174 | 1173 | 5003133905 | 196 | 13058649 | 0x00000000004006cc | fmadd | 13058633/13058649 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1175 | 1174 | 5003134675 | 196 | 13058649 | 0x00000000004006cc | fmadd | —/13058649 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1407 | 1175 | 9405832205 | 196 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1176 | — | 5025176310 | 197 | 13100193 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff2cdeb0fadf2ed→0x3ff2cdeb0fadf2e5 | — | — | origin |
| carrier_state | 1177 | 1176 | 5025176310 | 197 | 13100193 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff2cdeb0fadf2ed→0x3ff2cdeb0fadf2e5 | — | — | fsu_taint |
| operand_read | 1178 | 1177 | 5025184780 | 197 | 13100209 | 0x00000000004006cc | fmadd | 13100193/13100209 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1179 | 1178 | 5025184780 | 197 | 13100209 | 0x00000000004006cc | fmadd | 13100193/13100209 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1180 | 1179 | 5025184780 | 197 | 13100209 | 0x00000000004006cc | fmadd | 13100193/13100209 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1181 | 1180 | 5025185550 | 197 | 13100209 | 0x00000000004006cc | fmadd | —/13100209 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1408 | 1181 | 9405832205 | 197 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1182 | — | 5078375995 | 198 | 13170669 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ffb4e22a2c23747→0x3ffb4e22a2c23647 | — | — | origin |
| carrier_state | 1183 | 1182 | 5078375995 | 198 | 13170669 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3ffb4e22a2c23747→0x3ffb4e22a2c23647 | — | — | fsu_taint |
| operand_read | 1184 | 1183 | 5078384465 | 198 | 13170685 | 0x00000000004006a4 | fmadd | 13170669/13170685 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1185 | 1184 | 5078384465 | 198 | 13170685 | 0x00000000004006a4 | fmadd | 13170669/13170685 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1186 | 1185 | 5078384465 | 198 | 13170685 | 0x00000000004006a4 | fmadd | 13170669/13170685 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1187 | 1186 | 5078385235 | 198 | 13170685 | 0x00000000004006a4 | fmadd | —/13170685 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1409 | 1187 | 9405832205 | 198 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1188 | — | 5135961985 | 199 | 13261327 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fc7d41743e963df→0x3fc7d41743e963db | — | — | origin |
| carrier_state | 1189 | 1188 | 5135961985 | 199 | 13261327 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fc7d41743e963df→0x3fc7d41743e963db | — | — | fsu_taint |
| operand_read | 1190 | 1189 | 5135978925 | 199 | 13261343 | 0x00000000004006a4 | fmadd | 13261327/13261343 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1191 | 1190 | 5135978925 | 199 | 13261343 | 0x00000000004006a4 | fmadd | 13261327/13261343 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1192 | 1191 | 5135978925 | 199 | 13261343 | 0x00000000004006a4 | fmadd | 13261327/13261343 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1193 | 1192 | 5135979695 | 199 | 13261343 | 0x00000000004006a4 | fmadd | —/13261343 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1410 | 1193 | 9405832205 | 199 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 6 | — | 43691340 | 2 | 135039 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3ff0bc6a7ef9db23→0x3ff0bc6a7ef95b23 | — | — | origin |
| carrier_state | 7 | 6 | 43691340 | 2 | 135039 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3ff0bc6a7ef9db23→0x3ff0bc6a7ef95b23 | — | — | fsu_taint |
| operand_read | 8 | 7 | 43715595 | 2 | 135146 | 0x0000000000400654 | fmadd | 135039/135146 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 43715595 | 2 | 135146 | 0x0000000000400654 | fmadd | 135039/135146 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 43715595 | 2 | 135146 | 0x0000000000400654 | fmadd | 135039/135146 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 43716365 | 2 | 135146 | 0x0000000000400654 | fmadd | —/135146 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1213 | 11 | 9405832205 | 2 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 114 | — | 336694435 | 20 | 1290747 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe010624dd2f1aa→0x3fe010624dd2f1ea | — | — | origin |
| carrier_state | 115 | 114 | 336694435 | 20 | 1290747 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe010624dd2f1aa→0x3fe010624dd2f1ea | — | — | fsu_taint |
| operand_read | 116 | 115 | 336718690 | 20 | 1290854 | 0x0000000000400654 | fmadd | 1290747/1290854 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 117 | 116 | 336718690 | 20 | 1290854 | 0x0000000000400654 | fmadd | 1290747/1290854 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 118 | 117 | 336718690 | 20 | 1290854 | 0x0000000000400654 | fmadd | 1290747/1290854 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 119 | 118 | 336719460 | 20 | 1290854 | 0x0000000000400654 | fmadd | —/1290854 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1231 | 119 | 9405832205 | 20 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1194 | — | 5216888215 | 200 | 13372685 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe0b242070b8cfc→0x3fe0b242070b8cfe | — | — | origin |
| carrier_state | 1195 | 1194 | 5216888215 | 200 | 13372685 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe0b242070b8cfc→0x3fe0b242070b8cfe | — | — | fsu_taint |
| operand_read | 1196 | 1195 | 5216896685 | 200 | 13372701 | 0x00000000004006cc | fmadd | 13372685/13372701 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1197 | 1196 | 5216896685 | 200 | 13372701 | 0x00000000004006cc | fmadd | 13372685/13372701 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1198 | 1197 | 5216896685 | 200 | 13372701 | 0x00000000004006cc | fmadd | 13372685/13372701 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1199 | 1198 | 5216897455 | 200 | 13372701 | 0x00000000004006cc | fmadd | —/13372701 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1411 | 1199 | 9405832205 | 200 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1200 | — | 5299891135 | 201 | 13484119 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe81001d5c31594→0x3fe81001d5c31494 | — | — | origin |
| carrier_state | 1201 | 1200 | 5299891135 | 201 | 13484119 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe81001d5c31594→0x3fe81001d5c31494 | — | — | fsu_taint |
| operand_read | 1202 | 1201 | 5299899605 | 201 | 13484135 | 0x00000000004006cc | fmadd | 13484119/13484135 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1203 | 1202 | 5299899605 | 201 | 13484135 | 0x00000000004006cc | fmadd | 13484119/13484135 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1204 | 1203 | 5299899605 | 201 | 13484135 | 0x00000000004006cc | fmadd | 13484119/13484135 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1205 | 1204 | 5299900375 | 201 | 13484135 | 0x00000000004006cc | fmadd | —/13484135 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1412 | 1205 | 9405832205 | 201 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1206 | — | 5347932975 | 202 | 13553427 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fecbb0a2ca9ac37→0x3fecbb0a2ca92c37 | — | — | origin |
| carrier_state | 1207 | 1206 | 5347932975 | 202 | 13553427 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fecbb0a2ca9ac37→0x3fecbb0a2ca92c37 | — | — | fsu_taint |
| operand_read | 1208 | 1207 | 5347967625 | 202 | 13553443 | 0x00000000004006a4 | fmadd | 13553427/13553443 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1209 | 1208 | 5347967625 | 202 | 13553443 | 0x00000000004006a4 | fmadd | 13553427/13553443 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1210 | 1209 | 5347967625 | 202 | 13553443 | 0x00000000004006a4 | fmadd | 13553427/13553443 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1211 | 1210 | 5347968395 | 202 | 13553443 | 0x00000000004006a4 | fmadd | —/13553443 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1413 | 1211 | 9405832205 | 202 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 120 | — | 359077180 | 21 | 1379162 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3fe05a1cac083127→0x3fe05a1cac083527 | — | — | origin |
| carrier_state | 121 | 120 | 359077180 | 21 | 1379162 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3fe05a1cac083127→0x3fe05a1cac083527 | — | — | fsu_taint |
| operand_read | 122 | 121 | 359112600 | 21 | 1379306 | 0x0000000000400654 | fmadd | 1379162/1379306 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 123 | 122 | 359112600 | 21 | 1379306 | 0x0000000000400654 | fmadd | 1379162/1379306 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 124 | 123 | 359112600 | 21 | 1379306 | 0x0000000000400654 | fmadd | 1379162/1379306 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 125 | 124 | 359113370 | 21 | 1379306 | 0x0000000000400654 | fmadd | —/1379306 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1232 | 125 | 9405832205 | 21 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 126 | — | 368938570 | 22 | 1418258 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3feb8d4fdf3b645a→0x3feb8d4fdf3b745a | — | — | origin |
| carrier_state | 127 | 126 | 368938570 | 22 | 1418258 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3feb8d4fdf3b645a→0x3feb8d4fdf3b745a | — | — | fsu_taint |
| operand_read | 128 | 127 | 368973990 | 22 | 1418402 | 0x0000000000400654 | fmadd | 1418258/1418402 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 129 | 128 | 368973990 | 22 | 1418402 | 0x0000000000400654 | fmadd | 1418258/1418402 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 130 | 129 | 368973990 | 22 | 1418402 | 0x0000000000400654 | fmadd | 1418258/1418402 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 131 | 130 | 368974760 | 22 | 1418402 | 0x0000000000400654 | fmadd | —/1418402 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1233 | 131 | 9405832205 | 22 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 132 | — | 376468785 | 23 | 1448352 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4076c00000000000→0x4076c00000002000 | — | — | origin |
| carrier_state | 133 | 132 | 376468785 | 23 | 1448352 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4076c00000000000→0x4076c00000002000 | — | — | fsu_taint |
| operand_read | 134 | 133 | 376473020 | 23 | 1448355 | 0x0000000000400658 | fmadd | 1448352/1448355 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 135 | 134 | 376473020 | 23 | 1448355 | 0x0000000000400658 | fmadd | 1448352/1448355 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 136 | 135 | 376473020 | 23 | 1448355 | 0x0000000000400658 | fmadd | 1448352/1448355 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 137 | 136 | 376473790 | 23 | 1448355 | 0x0000000000400658 | fmadd | —/1448355 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1234 | 137 | 9405832205 | 23 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 138 | — | 388973200 | 24 | 1497419 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4083100000000000→0x4083100000000800 | — | — | origin |
| carrier_state | 139 | 138 | 388973200 | 24 | 1497419 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4083100000000000→0x4083100000000800 | — | — | fsu_taint |
| operand_read | 140 | 139 | 388975125 | 24 | 1497422 | 0x0000000000400654 | fmadd | 1497419/1497422 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 141 | 140 | 388975125 | 24 | 1497422 | 0x0000000000400654 | fmadd | 1497419/1497422 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 142 | 141 | 388975125 | 24 | 1497422 | 0x0000000000400654 | fmadd | 1497419/1497422 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 143 | 142 | 388975895 | 24 | 1497422 | 0x0000000000400654 | fmadd | —/1497422 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1235 | 143 | 9405832205 | 24 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 144 | — | 397621840 | 25 | 1531585 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4088700000000000→0x4088700000000002 | — | — | origin |
| carrier_state | 145 | 144 | 397621840 | 25 | 1531585 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4088700000000000→0x4088700000000002 | — | — | fsu_taint |
| operand_read | 146 | 145 | 397625690 | 25 | 1531588 | 0x000000000040065c | fmadd | 1531585/1531588 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 147 | 146 | 397625690 | 25 | 1531588 | 0x000000000040065c | fmadd | 1531585/1531588 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 148 | 147 | 397625690 | 25 | 1531588 | 0x000000000040065c | fmadd | 1531585/1531588 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 149 | 148 | 397626460 | 25 | 1531588 | 0x000000000040065c | fmadd | —/1531588 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1236 | 149 | 9405832205 | 25 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 150 | — | 414340850 | 26 | 1597611 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fdc083126e978d5→0x3fdc083126e97895 | — | — | origin |
| carrier_state | 151 | 150 | 414340850 | 26 | 1597611 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fdc083126e978d5→0x3fdc083126e97895 | — | — | fsu_taint |
| operand_read | 152 | 151 | 414365105 | 26 | 1597718 | 0x0000000000400654 | fmadd | 1597611/1597718 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 153 | 152 | 414365105 | 26 | 1597718 | 0x0000000000400654 | fmadd | 1597611/1597718 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 154 | 153 | 414365105 | 26 | 1597718 | 0x0000000000400654 | fmadd | 1597611/1597718 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 155 | 154 | 414365875 | 26 | 1597718 | 0x0000000000400654 | fmadd | —/1597718 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1237 | 155 | 9405832205 | 26 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 156 | — | 436188060 | 27 | 1683760 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fd926e978d4fdf4→0x3fd926e978d4fde4 | — | — | origin |
| carrier_state | 157 | 156 | 436188060 | 27 | 1683760 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fd926e978d4fdf4→0x3fd926e978d4fde4 | — | — | fsu_taint |
| operand_read | 158 | 157 | 436203460 | 27 | 1683830 | 0x0000000000400654 | fmadd | 1683760/1683830 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 159 | 158 | 436203460 | 27 | 1683830 | 0x0000000000400654 | fmadd | 1683760/1683830 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 160 | 159 | 436203460 | 27 | 1683830 | 0x0000000000400654 | fmadd | 1683760/1683830 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 161 | 160 | 436204230 | 27 | 1683830 | 0x0000000000400654 | fmadd | —/1683830 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1238 | 161 | 9405832205 | 27 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 162 | — | 447269130 | 28 | 1727822 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff1c28f5c28f5c3→0x3ff1c28f5c28f5c2 | — | — | origin |
| carrier_state | 163 | 162 | 447269130 | 28 | 1727822 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff1c28f5c28f5c3→0x3ff1c28f5c28f5c2 | — | — | fsu_taint |
| operand_read | 164 | 163 | 447433910 | 28 | 1727966 | 0x0000000000400654 | fmadd | 1727822/1727966 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 165 | 164 | 447433910 | 28 | 1727966 | 0x0000000000400654 | fmadd | 1727822/1727966 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 166 | 165 | 447433910 | 28 | 1727966 | 0x0000000000400654 | fmadd | 1727822/1727966 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 167 | 166 | 447434680 | 28 | 1727966 | 0x0000000000400654 | fmadd | —/1727966 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1239 | 167 | 9405832205 | 28 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 168 | — | 455904295 | 29 | 1761371 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4079e00000000000→0x4079e00000000200 | — | — | origin |
| carrier_state | 169 | 168 | 455904295 | 29 | 1761371 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4079e00000000000→0x4079e00000000200 | — | — | fsu_taint |
| operand_read | 170 | 169 | 455906220 | 29 | 1761374 | 0x0000000000400654 | fmadd | 1761371/1761374 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 171 | 170 | 455906220 | 29 | 1761374 | 0x0000000000400654 | fmadd | 1761371/1761374 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 172 | 171 | 455906220 | 29 | 1761374 | 0x0000000000400654 | fmadd | 1761371/1761374 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 173 | 172 | 455906990 | 29 | 1761374 | 0x0000000000400654 | fmadd | —/1761374 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1240 | 173 | 9405832205 | 29 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 12 | — | 63090335 | 3 | 211972 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fc0624dd2f1a9fc→0x3fc0624dd2f3a9fc | — | — | origin |
| carrier_state | 13 | 12 | 63090335 | 3 | 211972 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fc0624dd2f1a9fc→0x3fc0624dd2f3a9fc | — | — | fsu_taint |
| operand_read | 14 | 13 | 63105735 | 3 | 212042 | 0x0000000000400654 | fmadd | 211972/212042 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 15 | 14 | 63105735 | 3 | 212042 | 0x0000000000400654 | fmadd | 211972/212042 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 16 | 15 | 63105735 | 3 | 212042 | 0x0000000000400654 | fmadd | 211972/212042 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 17 | 16 | 63106505 | 3 | 212042 | 0x0000000000400654 | fmadd | —/212042 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1214 | 17 | 9405832205 | 3 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 174 | — | 465353735 | 30 | 1798779 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fea24dd2f1a9fbf→0x3fea24dd2f1a9fbd | — | — | origin |
| carrier_state | 175 | 174 | 465353735 | 30 | 1798779 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fea24dd2f1a9fbf→0x3fea24dd2f1a9fbd | — | — | fsu_taint |
| operand_read | 176 | 175 | 465377990 | 30 | 1798886 | 0x0000000000400654 | fmadd | 1798779/1798886 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 177 | 176 | 465377990 | 30 | 1798886 | 0x0000000000400654 | fmadd | 1798779/1798886 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 178 | 177 | 465377990 | 30 | 1798886 | 0x0000000000400654 | fmadd | 1798779/1798886 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 179 | 178 | 465378760 | 30 | 1798886 | 0x0000000000400654 | fmadd | —/1798886 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1241 | 179 | 9405832205 | 30 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 180 | — | 484484385 | 31 | 1874411 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x408a900000000000→0x408a900000000020 | — | — | origin |
| carrier_state | 181 | 180 | 484484385 | 31 | 1874411 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x408a900000000000→0x408a900000000020 | — | — | fsu_taint |
| operand_read | 182 | 181 | 484486310 | 31 | 1874414 | 0x0000000000400654 | fmadd | 1874411/1874414 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 183 | 182 | 484486310 | 31 | 1874414 | 0x0000000000400654 | fmadd | 1874411/1874414 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 184 | 183 | 484486310 | 31 | 1874414 | 0x0000000000400654 | fmadd | 1874411/1874414 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 185 | 184 | 484487080 | 31 | 1874414 | 0x0000000000400654 | fmadd | —/1874414 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1242 | 185 | 9405832205 | 31 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 186 | — | 497533190 | 32 | 1926039 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe0cccccccccccd→0x3fe0cccccccc8ccd | — | — | origin |
| carrier_state | 187 | 186 | 497533190 | 32 | 1926039 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe0cccccccccccd→0x3fe0cccccccc8ccd | — | — | fsu_taint |
| operand_read | 188 | 187 | 497557445 | 32 | 1926146 | 0x0000000000400654 | fmadd | 1926039/1926146 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 189 | 188 | 497557445 | 32 | 1926146 | 0x0000000000400654 | fmadd | 1926039/1926146 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 190 | 189 | 497557445 | 32 | 1926146 | 0x0000000000400654 | fmadd | 1926039/1926146 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 191 | 190 | 497558215 | 32 | 1926146 | 0x0000000000400654 | fmadd | —/1926146 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1243 | 191 | 9405832205 | 32 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 192 | — | 520052225 | 33 | 2014704 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x408cb00000000000→0x408cb00000000100 | — | — | origin |
| carrier_state | 193 | 192 | 520052225 | 33 | 2014704 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x408cb00000000000→0x408cb00000000100 | — | — | fsu_taint |
| operand_read | 194 | 193 | 520056460 | 33 | 2014707 | 0x0000000000400658 | fmadd | 2014704/2014707 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 195 | 194 | 520056460 | 33 | 2014707 | 0x0000000000400658 | fmadd | 2014704/2014707 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 196 | 195 | 520056460 | 33 | 2014707 | 0x0000000000400658 | fmadd | 2014704/2014707 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 197 | 196 | 520057230 | 33 | 2014707 | 0x0000000000400658 | fmadd | —/2014707 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1244 | 197 | 9405832205 | 33 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 198 | — | 536568340 | 34 | 2079648 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4078300000000000→0x4078300000000020 | — | — | origin |
| carrier_state | 199 | 198 | 536568340 | 34 | 2079648 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4078300000000000→0x4078300000000020 | — | — | fsu_taint |
| operand_read | 200 | 199 | 536572575 | 34 | 2079651 | 0x0000000000400658 | fmadd | 2079648/2079651 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 201 | 200 | 536572575 | 34 | 2079651 | 0x0000000000400658 | fmadd | 2079648/2079651 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 202 | 201 | 536572575 | 34 | 2079651 | 0x0000000000400658 | fmadd | 2079648/2079651 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 203 | 202 | 536573345 | 34 | 2079651 | 0x0000000000400658 | fmadd | —/2079651 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1245 | 203 | 9405832205 | 34 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 204 | — | 558995745 | 35 | 2168425 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4055800000000000→0x4055800000001000 | — | — | origin |
| carrier_state | 205 | 204 | 558995745 | 35 | 2168425 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4055800000000000→0x4055800000001000 | — | — | fsu_taint |
| operand_read | 206 | 205 | 558999595 | 35 | 2168428 | 0x000000000040065c | fmadd | 2168425/2168428 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 207 | 206 | 558999595 | 35 | 2168428 | 0x000000000040065c | fmadd | 2168425/2168428 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 208 | 207 | 558999595 | 35 | 2168428 | 0x000000000040065c | fmadd | 2168425/2168428 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 209 | 208 | 559000365 | 35 | 2168428 | 0x000000000040065c | fmadd | —/2168428 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1246 | 209 | 9405832205 | 35 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 210 | — | 569176300 | 36 | 2207991 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe604189374bc6b→0x3fe604189374bd6b | — | — | origin |
| carrier_state | 211 | 210 | 569176300 | 36 | 2207991 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe604189374bc6b→0x3fe604189374bd6b | — | — | fsu_taint |
| operand_read | 212 | 211 | 569200555 | 36 | 2208098 | 0x0000000000400654 | fmadd | 2207991/2208098 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 213 | 212 | 569200555 | 36 | 2208098 | 0x0000000000400654 | fmadd | 2207991/2208098 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 214 | 213 | 569200555 | 36 | 2208098 | 0x0000000000400654 | fmadd | 2207991/2208098 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 215 | 214 | 569201325 | 36 | 2208098 | 0x0000000000400654 | fmadd | —/2208098 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1247 | 215 | 9405832205 | 36 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 216 | — | 586394270 | 37 | 2276534 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff5c28f5c28f5c3→0x3ff5c28f5c2af5c3 | — | — | origin |
| carrier_state | 217 | 216 | 586394270 | 37 | 2276534 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff5c28f5c28f5c3→0x3ff5c28f5c2af5c3 | — | — | fsu_taint |
| operand_read | 218 | 217 | 586429690 | 37 | 2276678 | 0x0000000000400654 | fmadd | 2276534/2276678 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 219 | 218 | 586429690 | 37 | 2276678 | 0x0000000000400654 | fmadd | 2276534/2276678 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 220 | 219 | 586429690 | 37 | 2276678 | 0x0000000000400654 | fmadd | 2276534/2276678 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 221 | 220 | 586430460 | 37 | 2276678 | 0x0000000000400654 | fmadd | —/2276678 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1248 | 221 | 9405832205 | 37 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 222 | — | 600303550 | 38 | 2331253 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x405e400000000000→0x405e400000000008 | — | — | origin |
| carrier_state | 223 | 222 | 600303550 | 38 | 2331253 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x405e400000000000→0x405e400000000008 | — | — | fsu_taint |
| operand_read | 224 | 223 | 600307400 | 38 | 2331256 | 0x000000000040065c | fmadd | 2331253/2331256 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 225 | 224 | 600307400 | 38 | 2331256 | 0x000000000040065c | fmadd | 2331253/2331256 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 226 | 225 | 600307400 | 38 | 2331256 | 0x000000000040065c | fmadd | 2331253/2331256 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 227 | 226 | 600308170 | 38 | 2331256 | 0x000000000040065c | fmadd | —/2331256 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1249 | 227 | 9405832205 | 38 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 228 | — | 611174410 | 39 | 2373983 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x405f400000000000→0x405f400000000800 | — | — | origin |
| carrier_state | 229 | 228 | 611174410 | 39 | 2373983 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x405f400000000000→0x405f400000000800 | — | — | fsu_taint |
| operand_read | 230 | 229 | 611176335 | 39 | 2373986 | 0x0000000000400654 | fmadd | 2373983/2373986 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 231 | 230 | 611176335 | 39 | 2373986 | 0x0000000000400654 | fmadd | 2373983/2373986 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 232 | 231 | 611176335 | 39 | 2373986 | 0x0000000000400654 | fmadd | 2373983/2373986 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 233 | 232 | 611177105 | 39 | 2373986 | 0x0000000000400654 | fmadd | —/2373986 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1250 | 233 | 9405832205 | 39 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 18 | — | 83733650 | 4 | 293150 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff420c49ba5e354→0x3ff420c49ba5e355 | — | — | origin |
| carrier_state | 19 | 18 | 83733650 | 4 | 293150 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff420c49ba5e354→0x3ff420c49ba5e355 | — | — | fsu_taint |
| operand_read | 20 | 19 | 83769070 | 4 | 293294 | 0x0000000000400654 | fmadd | 293150/293294 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 21 | 20 | 83769070 | 4 | 293294 | 0x0000000000400654 | fmadd | 293150/293294 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 22 | 21 | 83769070 | 4 | 293294 | 0x0000000000400654 | fmadd | 293150/293294 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 23 | 22 | 83769840 | 4 | 293294 | 0x0000000000400654 | fmadd | —/293294 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1215 | 23 | 9405832205 | 4 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 234 | — | 627084535 | 40 | 2436988 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fde24dd2f1a9fbf→0x3fde24dd2f1a9ebf | — | — | origin |
| carrier_state | 235 | 234 | 627084535 | 40 | 2436988 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fde24dd2f1a9fbf→0x3fde24dd2f1a9ebf | — | — | fsu_taint |
| operand_read | 236 | 235 | 627099935 | 40 | 2437058 | 0x0000000000400654 | fmadd | 2436988/2437058 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 237 | 236 | 627099935 | 40 | 2437058 | 0x0000000000400654 | fmadd | 2436988/2437058 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 238 | 237 | 627099935 | 40 | 2437058 | 0x0000000000400654 | fmadd | 2436988/2437058 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 239 | 238 | 627100705 | 40 | 2437058 | 0x0000000000400654 | fmadd | —/2437058 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1251 | 239 | 9405832205 | 40 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 240 | — | 645155665 | 41 | 2508013 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4080880000000000→0x4080880000001000 | — | — | origin |
| carrier_state | 241 | 240 | 645155665 | 41 | 2508013 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4080880000000000→0x4080880000001000 | — | — | fsu_taint |
| operand_read | 242 | 241 | 645159515 | 41 | 2508016 | 0x000000000040065c | fmadd | 2508013/2508016 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 243 | 242 | 645159515 | 41 | 2508016 | 0x000000000040065c | fmadd | 2508013/2508016 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 244 | 243 | 645159515 | 41 | 2508016 | 0x000000000040065c | fmadd | 2508013/2508016 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 245 | 244 | 645160285 | 41 | 2508016 | 0x000000000040065c | fmadd | —/2508016 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1252 | 245 | 9405832205 | 41 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 246 | — | 665032830 | 42 | 2586495 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fed810624dd2f1b→0x3fed810624dd2f0b | — | — | origin |
| carrier_state | 247 | 246 | 665032830 | 42 | 2586495 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fed810624dd2f1b→0x3fed810624dd2f0b | — | — | fsu_taint |
| operand_read | 248 | 247 | 665057085 | 42 | 2586602 | 0x0000000000400654 | fmadd | 2586495/2586602 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 249 | 248 | 665057085 | 42 | 2586602 | 0x0000000000400654 | fmadd | 2586495/2586602 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 250 | 249 | 665057085 | 42 | 2586602 | 0x0000000000400654 | fmadd | 2586495/2586602 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 251 | 250 | 665057855 | 42 | 2586602 | 0x0000000000400654 | fmadd | —/2586602 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1253 | 251 | 9405832205 | 42 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 252 | — | 687455230 | 43 | 2674768 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fd395810624dd2f→0x3fd395810624d92f | — | — | origin |
| carrier_state | 253 | 252 | 687455230 | 43 | 2674768 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fd395810624dd2f→0x3fd395810624d92f | — | — | fsu_taint |
| operand_read | 254 | 253 | 687470630 | 43 | 2674838 | 0x0000000000400654 | fmadd | 2674768/2674838 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 255 | 254 | 687470630 | 43 | 2674838 | 0x0000000000400654 | fmadd | 2674768/2674838 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 256 | 255 | 687470630 | 43 | 2674838 | 0x0000000000400654 | fmadd | 2674768/2674838 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 257 | 256 | 687471400 | 43 | 2674838 | 0x0000000000400654 | fmadd | —/2674838 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1254 | 257 | 9405832205 | 43 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 258 | — | 698835445 | 44 | 2720051 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4066800000000000→0x4066800000020000 | — | — | origin |
| carrier_state | 259 | 258 | 698835445 | 44 | 2720051 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4066800000000000→0x4066800000020000 | — | — | fsu_taint |
| operand_read | 260 | 259 | 698837370 | 44 | 2720054 | 0x0000000000400654 | fmadd | 2720051/2720054 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 261 | 260 | 698837370 | 44 | 2720054 | 0x0000000000400654 | fmadd | 2720051/2720054 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 262 | 261 | 698837370 | 44 | 2720054 | 0x0000000000400654 | fmadd | 2720051/2720054 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 263 | 262 | 698838140 | 44 | 2720054 | 0x0000000000400654 | fmadd | —/2720054 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1255 | 263 | 9405832205 | 44 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 264 | — | 711655175 | 45 | 2770347 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fee872b020c49ba→0x3fee872b020c499a | — | — | origin |
| carrier_state | 265 | 264 | 711655175 | 45 | 2770347 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fee872b020c49ba→0x3fee872b020c499a | — | — | fsu_taint |
| operand_read | 266 | 265 | 711679430 | 45 | 2770454 | 0x0000000000400654 | fmadd | 2770347/2770454 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 267 | 266 | 711679430 | 45 | 2770454 | 0x0000000000400654 | fmadd | 2770347/2770454 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 268 | 267 | 711679430 | 45 | 2770454 | 0x0000000000400654 | fmadd | 2770347/2770454 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 269 | 268 | 711680200 | 45 | 2770454 | 0x0000000000400654 | fmadd | —/2770454 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1256 | 269 | 9405832205 | 45 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 270 | — | 734228495 | 46 | 2859447 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fedf3b645a1cac1→0x3fedf3b645a1eac1 | — | — | origin |
| carrier_state | 271 | 270 | 734228495 | 46 | 2859447 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fedf3b645a1cac1→0x3fedf3b645a1eac1 | — | — | fsu_taint |
| operand_read | 272 | 271 | 734252750 | 46 | 2859554 | 0x0000000000400654 | fmadd | 2859447/2859554 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 273 | 272 | 734252750 | 46 | 2859554 | 0x0000000000400654 | fmadd | 2859447/2859554 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 274 | 273 | 734252750 | 46 | 2859554 | 0x0000000000400654 | fmadd | 2859447/2859554 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 275 | 274 | 734253520 | 46 | 2859554 | 0x0000000000400654 | fmadd | —/2859554 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1257 | 275 | 9405832205 | 46 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 276 | — | 755594070 | 47 | 2944332 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4089680000000000→0x4089680000000002 | — | — | origin |
| carrier_state | 277 | 276 | 755594070 | 47 | 2944332 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4089680000000000→0x4089680000000002 | — | — | fsu_taint |
| operand_read | 278 | 277 | 755598305 | 47 | 2944335 | 0x0000000000400658 | fmadd | 2944332/2944335 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 279 | 278 | 755598305 | 47 | 2944335 | 0x0000000000400658 | fmadd | 2944332/2944335 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 280 | 279 | 755598305 | 47 | 2944335 | 0x0000000000400658 | fmadd | 2944332/2944335 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 281 | 280 | 755599075 | 47 | 2944335 | 0x0000000000400658 | fmadd | —/2944335 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1258 | 281 | 9405832205 | 47 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 282 | — | 775968655 | 48 | 3024324 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x408f000000000000→0x408f000000000004 | — | — | origin |
| carrier_state | 283 | 282 | 775968655 | 48 | 3024324 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x408f000000000000→0x408f000000000004 | — | — | fsu_taint |
| operand_read | 284 | 283 | 775972890 | 48 | 3024327 | 0x0000000000400658 | fmadd | 3024324/3024327 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 285 | 284 | 775972890 | 48 | 3024327 | 0x0000000000400658 | fmadd | 3024324/3024327 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 286 | 285 | 775972890 | 48 | 3024327 | 0x0000000000400658 | fmadd | 3024324/3024327 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 287 | 286 | 775973660 | 48 | 3024327 | 0x0000000000400658 | fmadd | —/3024327 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1259 | 287 | 9405832205 | 48 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 288 | — | 793772595 | 49 | 3094202 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fe36c8b43958106→0x3fe36c8b43958102 | — | — | origin |
| carrier_state | 289 | 288 | 793772595 | 49 | 3094202 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fe36c8b43958106→0x3fe36c8b43958102 | — | — | fsu_taint |
| operand_read | 290 | 289 | 793808015 | 49 | 3094346 | 0x0000000000400654 | fmadd | 3094202/3094346 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 291 | 290 | 793808015 | 49 | 3094346 | 0x0000000000400654 | fmadd | 3094202/3094346 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 292 | 291 | 793808015 | 49 | 3094346 | 0x0000000000400654 | fmadd | 3094202/3094346 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 293 | 292 | 793808785 | 49 | 3094346 | 0x0000000000400654 | fmadd | —/3094346 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1260 | 293 | 9405832205 | 49 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 24 | — | 103184235 | 5 | 369940 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfd0000000000000→0xbfd0000000000100 | — | — | origin |
| carrier_state | 25 | 24 | 103184235 | 5 | 369940 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfd0000000000000→0xbfd0000000000100 | — | — | fsu_taint |
| operand_read | 26 | 25 | 103199635 | 5 | 370010 | 0x0000000000400654 | fmadd | 369940/370010 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 27 | 26 | 103199635 | 5 | 370010 | 0x0000000000400654 | fmadd | 369940/370010 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 28 | 27 | 103199635 | 5 | 370010 | 0x0000000000400654 | fmadd | 369940/370010 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 29 | 28 | 103200405 | 5 | 370010 | 0x0000000000400654 | fmadd | —/370010 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1216 | 29 | 9405832205 | 5 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 294 | — | 811200775 | 50 | 3163283 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x4076400000000000→0x4076400000001000 | — | — | origin |
| carrier_state | 295 | 294 | 811200775 | 50 | 3163283 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x4076400000000000→0x4076400000001000 | — | — | fsu_taint |
| operand_read | 296 | 295 | 811202700 | 50 | 3163286 | 0x0000000000400654 | fmadd | 3163283/3163286 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 297 | 296 | 811202700 | 50 | 3163286 | 0x0000000000400654 | fmadd | 3163283/3163286 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 298 | 297 | 811202700 | 50 | 3163286 | 0x0000000000400654 | fmadd | 3163283/3163286 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 299 | 298 | 811203470 | 50 | 3163286 | 0x0000000000400654 | fmadd | —/3163286 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1261 | 299 | 9405832205 | 50 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 300 | — | 833611625 | 51 | 3251702 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fefbe76c8b43958→0x3fefbe76c8b47958 | — | — | origin |
| carrier_state | 301 | 300 | 833611625 | 51 | 3251702 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fefbe76c8b43958→0x3fefbe76c8b47958 | — | — | fsu_taint |
| operand_read | 302 | 301 | 833647045 | 51 | 3251846 | 0x0000000000400654 | fmadd | 3251702/3251846 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 303 | 302 | 833647045 | 51 | 3251846 | 0x0000000000400654 | fmadd | 3251702/3251846 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 304 | 303 | 833647045 | 51 | 3251846 | 0x0000000000400654 | fmadd | 3251702/3251846 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 305 | 304 | 833647815 | 51 | 3251846 | 0x0000000000400654 | fmadd | —/3251846 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1262 | 305 | 9405832205 | 51 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 306 | — | 851125660 | 52 | 3320606 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3fe96872b020c49c→0x3fe96872b020c59c | — | — | origin |
| carrier_state | 307 | 306 | 851125660 | 52 | 3320606 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3fe96872b020c49c→0x3fe96872b020c59c | — | — | fsu_taint |
| operand_read | 308 | 307 | 851161080 | 52 | 3320750 | 0x0000000000400654 | fmadd | 3320606/3320750 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 309 | 308 | 851161080 | 52 | 3320750 | 0x0000000000400654 | fmadd | 3320606/3320750 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 310 | 309 | 851161080 | 52 | 3320750 | 0x0000000000400654 | fmadd | 3320606/3320750 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 311 | 310 | 851161850 | 52 | 3320750 | 0x0000000000400654 | fmadd | —/3320750 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1263 | 311 | 9405832205 | 52 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 312 | — | 871407460 | 53 | 3401175 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fe883126e978d50→0x3fe883126e978950 | — | — | origin |
| carrier_state | 313 | 312 | 871407460 | 53 | 3401175 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fe883126e978d50→0x3fe883126e978950 | — | — | fsu_taint |
| operand_read | 314 | 313 | 871431715 | 53 | 3401282 | 0x0000000000400654 | fmadd | 3401175/3401282 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 315 | 314 | 871431715 | 53 | 3401282 | 0x0000000000400654 | fmadd | 3401175/3401282 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 316 | 315 | 871431715 | 53 | 3401282 | 0x0000000000400654 | fmadd | 3401175/3401282 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 317 | 316 | 871432485 | 53 | 3401282 | 0x0000000000400654 | fmadd | —/3401282 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1264 | 317 | 9405832205 | 53 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 318 | — | 892726835 | 54 | 3485017 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4073500000000000→0x4073500000001000 | — | — | origin |
| carrier_state | 319 | 318 | 892726835 | 54 | 3485017 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4073500000000000→0x4073500000001000 | — | — | fsu_taint |
| operand_read | 320 | 319 | 892730685 | 54 | 3485020 | 0x000000000040065c | fmadd | 3485017/3485020 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 321 | 320 | 892730685 | 54 | 3485020 | 0x000000000040065c | fmadd | 3485017/3485020 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 322 | 321 | 892730685 | 54 | 3485020 | 0x000000000040065c | fmadd | 3485017/3485020 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 323 | 322 | 892731455 | 54 | 3485020 | 0x000000000040065c | fmadd | —/3485020 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1265 | 323 | 9405832205 | 54 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 324 | — | 915304775 | 55 | 3573865 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x406da00000000000→0x406da00000000040 | — | — | origin |
| carrier_state | 325 | 324 | 915304775 | 55 | 3573865 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x406da00000000000→0x406da00000000040 | — | — | fsu_taint |
| operand_read | 326 | 325 | 915308625 | 55 | 3573868 | 0x000000000040065c | fmadd | 3573865/3573868 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 327 | 326 | 915308625 | 55 | 3573868 | 0x000000000040065c | fmadd | 3573865/3573868 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 328 | 327 | 915308625 | 55 | 3573868 | 0x000000000040065c | fmadd | 3573865/3573868 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 329 | 328 | 915309395 | 55 | 3573868 | 0x000000000040065c | fmadd | —/3573868 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1266 | 329 | 9405832205 | 55 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 330 | — | 935163075 | 56 | 3652272 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4078c00000000000→0x4078c00000020000 | — | — | origin |
| carrier_state | 331 | 330 | 935163075 | 56 | 3652272 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4078c00000000000→0x4078c00000020000 | — | — | fsu_taint |
| operand_read | 332 | 331 | 935167310 | 56 | 3652275 | 0x0000000000400658 | fmadd | 3652272/3652275 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 333 | 332 | 935167310 | 56 | 3652275 | 0x0000000000400658 | fmadd | 3652272/3652275 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 334 | 333 | 935167310 | 56 | 3652275 | 0x0000000000400658 | fmadd | 3652272/3652275 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 335 | 334 | 935168080 | 56 | 3652275 | 0x0000000000400658 | fmadd | —/3652275 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1267 | 335 | 9405832205 | 56 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 336 | — | 945677810 | 57 | 3693781 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4084a80000000000→0x4084a80000000080 | — | — | origin |
| carrier_state | 337 | 336 | 945677810 | 57 | 3693781 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4084a80000000000→0x4084a80000000080 | — | — | fsu_taint |
| operand_read | 338 | 337 | 945681660 | 57 | 3693784 | 0x000000000040065c | fmadd | 3693781/3693784 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 339 | 338 | 945681660 | 57 | 3693784 | 0x000000000040065c | fmadd | 3693781/3693784 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 340 | 339 | 945681660 | 57 | 3693784 | 0x000000000040065c | fmadd | 3693781/3693784 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 341 | 340 | 945682430 | 57 | 3693784 | 0x000000000040065c | fmadd | —/3693784 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1268 | 341 | 9405832205 | 57 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 342 | — | 959391510 | 58 | 3748069 | 0x0000000000400650 | scvtf | —/— | 1 | — | 64@0 | 0x408a580000000000→0x408a580000000008 | — | — | origin |
| carrier_state | 343 | 342 | 959391510 | 58 | 3748069 | 0x0000000000400650 | scvtf | —/— | 1 | — | 64@0 | 0x408a580000000000→0x408a580000000008 | — | — | fsu_taint |
| operand_read | 344 | 343 | 959395360 | 58 | 3748072 | 0x000000000040065c | fmadd | 3748069/3748072 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 345 | 344 | 959395360 | 58 | 3748072 | 0x000000000040065c | fmadd | 3748069/3748072 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 346 | 345 | 959395360 | 58 | 3748072 | 0x000000000040065c | fmadd | 3748069/3748072 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 347 | 346 | 959396130 | 58 | 3748072 | 0x000000000040065c | fmadd | —/3748072 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1269 | 347 | 9405832205 | 58 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 348 | — | 970812535 | 59 | 3792532 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd4395810624dd3→0xbfd4395810624dd1 | — | — | origin |
| carrier_state | 349 | 348 | 970812535 | 59 | 3792532 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd4395810624dd3→0xbfd4395810624dd1 | — | — | fsu_taint |
| operand_read | 350 | 349 | 970827935 | 59 | 3792602 | 0x0000000000400654 | fmadd | 3792532/3792602 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 351 | 350 | 970827935 | 59 | 3792602 | 0x0000000000400654 | fmadd | 3792532/3792602 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 352 | 351 | 970827935 | 59 | 3792602 | 0x0000000000400654 | fmadd | 3792532/3792602 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 353 | 352 | 970828705 | 59 | 3792602 | 0x0000000000400654 | fmadd | —/3792602 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1270 | 353 | 9405832205 | 59 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 30 | — | 119271075 | 6 | 433876 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfdf1a9fbe76c8b4→0xbfdf1a9fbe76c8bc | — | — | origin |
| carrier_state | 31 | 30 | 119271075 | 6 | 433876 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfdf1a9fbe76c8b4→0xbfdf1a9fbe76c8bc | — | — | fsu_taint |
| operand_read | 32 | 31 | 119286475 | 6 | 433946 | 0x0000000000400654 | fmadd | 433876/433946 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 33 | 32 | 119286475 | 6 | 433946 | 0x0000000000400654 | fmadd | 433876/433946 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 34 | 33 | 119286475 | 6 | 433946 | 0x0000000000400654 | fmadd | 433876/433946 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 35 | 34 | 119287245 | 6 | 433946 | 0x0000000000400654 | fmadd | —/433946 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1217 | 35 | 9405832205 | 6 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 354 | — | 980663915 | 60 | 3831700 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fc3f7ced916872c→0x3fc3f7ced9168f2c | — | — | origin |
| carrier_state | 355 | 354 | 980663915 | 60 | 3831700 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0x3fc3f7ced916872c→0x3fc3f7ced9168f2c | — | — | fsu_taint |
| operand_read | 356 | 355 | 980679315 | 60 | 3831770 | 0x0000000000400654 | fmadd | 3831700/3831770 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 357 | 356 | 980679315 | 60 | 3831770 | 0x0000000000400654 | fmadd | 3831700/3831770 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 358 | 357 | 980679315 | 60 | 3831770 | 0x0000000000400654 | fmadd | 3831700/3831770 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 359 | 358 | 980680085 | 60 | 3831770 | 0x0000000000400654 | fmadd | —/3831770 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1271 | 359 | 9405832205 | 60 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 360 | — | 998478250 | 61 | 3902152 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fc0e5604189374c→0x3fc0e5604189274c | — | — | origin |
| carrier_state | 361 | 360 | 998478250 | 61 | 3902152 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fc0e5604189374c→0x3fc0e5604189274c | — | — | fsu_taint |
| operand_read | 362 | 361 | 998493650 | 61 | 3902222 | 0x0000000000400654 | fmadd | 3902152/3902222 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 363 | 362 | 998493650 | 61 | 3902222 | 0x0000000000400654 | fmadd | 3902152/3902222 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 364 | 363 | 998493650 | 61 | 3902222 | 0x0000000000400654 | fmadd | 3902152/3902222 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 365 | 364 | 998494420 | 61 | 3902222 | 0x0000000000400654 | fmadd | —/3902222 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1272 | 365 | 9405832205 | 61 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 366 | — | 1019971645 | 62 | 3986463 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fef0a3d70a3d70a→0x3fef0a3d70a3d70b | — | — | origin |
| carrier_state | 367 | 366 | 1019971645 | 62 | 3986463 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fef0a3d70a3d70a→0x3fef0a3d70a3d70b | — | — | fsu_taint |
| operand_read | 368 | 367 | 1019995900 | 62 | 3986570 | 0x0000000000400654 | fmadd | 3986463/3986570 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 369 | 368 | 1019995900 | 62 | 3986570 | 0x0000000000400654 | fmadd | 3986463/3986570 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 370 | 369 | 1019995900 | 62 | 3986570 | 0x0000000000400654 | fmadd | 3986463/3986570 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 371 | 370 | 1019996670 | 62 | 3986570 | 0x0000000000400654 | fmadd | —/3986570 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1273 | 371 | 9405832205 | 62 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 372 | — | 1040487525 | 63 | 4067788 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfdf6c8b43958106→0xbfdf6c8b43958107 | — | — | origin |
| carrier_state | 373 | 372 | 1040487525 | 63 | 4067788 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfdf6c8b43958106→0xbfdf6c8b43958107 | — | — | fsu_taint |
| operand_read | 374 | 373 | 1040502925 | 63 | 4067858 | 0x0000000000400654 | fmadd | 4067788/4067858 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 375 | 374 | 1040502925 | 63 | 4067858 | 0x0000000000400654 | fmadd | 4067788/4067858 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 376 | 375 | 1040502925 | 63 | 4067858 | 0x0000000000400654 | fmadd | 4067788/4067858 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 377 | 376 | 1040503695 | 63 | 4067858 | 0x0000000000400654 | fmadd | —/4067858 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1274 | 377 | 9405832205 | 63 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 378 | — | 1048299175 | 64 | 4098563 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4073800000000000→0x4073800000002000 | — | — | origin |
| carrier_state | 379 | 378 | 1048299175 | 64 | 4098563 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4073800000000000→0x4073800000002000 | — | — | fsu_taint |
| operand_read | 380 | 379 | 1048301100 | 64 | 4098566 | 0x0000000000400654 | fmadd | 4098563/4098566 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 381 | 380 | 1048301100 | 64 | 4098566 | 0x0000000000400654 | fmadd | 4098563/4098566 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 382 | 381 | 1048301100 | 64 | 4098566 | 0x0000000000400654 | fmadd | 4098563/4098566 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 383 | 382 | 1048301870 | 64 | 4098566 | 0x0000000000400654 | fmadd | —/4098566 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1275 | 383 | 9405832205 | 64 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 384 | — | 1062285840 | 65 | 4153863 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff3ced916872b02→0x3ff3ced916872b03 | — | — | origin |
| carrier_state | 385 | 384 | 1062285840 | 65 | 4153863 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff3ced916872b02→0x3ff3ced916872b03 | — | — | fsu_taint |
| operand_read | 386 | 385 | 1062310095 | 65 | 4153970 | 0x0000000000400654 | fmadd | 4153863/4153970 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 387 | 386 | 1062310095 | 65 | 4153970 | 0x0000000000400654 | fmadd | 4153863/4153970 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 388 | 387 | 1062310095 | 65 | 4153970 | 0x0000000000400654 | fmadd | 4153863/4153970 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 389 | 388 | 1062310865 | 65 | 4153970 | 0x0000000000400654 | fmadd | —/4153970 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1276 | 389 | 9405832205 | 65 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 390 | — | 1080906365 | 66 | 4227588 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4080300000000000→0x4080300000020000 | — | — | origin |
| carrier_state | 391 | 390 | 1080906365 | 66 | 4227588 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4080300000000000→0x4080300000020000 | — | — | fsu_taint |
| operand_read | 392 | 391 | 1080910600 | 66 | 4227591 | 0x0000000000400658 | fmadd | 4227588/4227591 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 393 | 392 | 1080910600 | 66 | 4227591 | 0x0000000000400658 | fmadd | 4227588/4227591 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 394 | 393 | 1080910600 | 66 | 4227591 | 0x0000000000400658 | fmadd | 4227588/4227591 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 395 | 394 | 1080911370 | 66 | 4227591 | 0x0000000000400658 | fmadd | —/4227591 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1277 | 395 | 9405832205 | 66 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 396 | — | 1094678970 | 67 | 4281695 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x407ad00000000000→0x407ad00000000800 | — | — | origin |
| carrier_state | 397 | 396 | 1094678970 | 67 | 4281695 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x407ad00000000000→0x407ad00000000800 | — | — | fsu_taint |
| operand_read | 398 | 397 | 1094680895 | 67 | 4281698 | 0x0000000000400654 | fmadd | 4281695/4281698 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 399 | 398 | 1094680895 | 67 | 4281698 | 0x0000000000400654 | fmadd | 4281695/4281698 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 400 | 399 | 1094680895 | 67 | 4281698 | 0x0000000000400654 | fmadd | 4281695/4281698 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 401 | 400 | 1094681665 | 67 | 4281698 | 0x0000000000400654 | fmadd | —/4281698 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1278 | 401 | 9405832205 | 67 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 402 | — | 1104230820 | 68 | 4319533 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4077100000000000→0x4077100000008000 | — | — | origin |
| carrier_state | 403 | 402 | 1104230820 | 68 | 4319533 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4077100000000000→0x4077100000008000 | — | — | fsu_taint |
| operand_read | 404 | 403 | 1104234670 | 68 | 4319536 | 0x000000000040065c | fmadd | 4319533/4319536 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 405 | 404 | 1104234670 | 68 | 4319536 | 0x000000000040065c | fmadd | 4319533/4319536 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 406 | 405 | 1104234670 | 68 | 4319536 | 0x000000000040065c | fmadd | 4319533/4319536 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 407 | 406 | 1104235440 | 68 | 4319536 | 0x000000000040065c | fmadd | —/4319536 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1279 | 407 | 9405832205 | 68 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 408 | — | 1126419140 | 69 | 4407011 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4081c00000000000→0x4081c00000000100 | — | — | origin |
| carrier_state | 409 | 408 | 1126419140 | 69 | 4407011 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4081c00000000000→0x4081c00000000100 | — | — | fsu_taint |
| operand_read | 410 | 409 | 1126421065 | 69 | 4407014 | 0x0000000000400654 | fmadd | 4407011/4407014 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 411 | 410 | 1126421065 | 69 | 4407014 | 0x0000000000400654 | fmadd | 4407011/4407014 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 412 | 411 | 1126421065 | 69 | 4407014 | 0x0000000000400654 | fmadd | 4407011/4407014 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 413 | 412 | 1126421835 | 69 | 4407014 | 0x0000000000400654 | fmadd | —/4407014 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1280 | 413 | 9405832205 | 69 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 36 | — | 133366695 | 7 | 489385 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4088a00000000000→0x4088a00000000001 | — | — | origin |
| carrier_state | 37 | 36 | 133366695 | 7 | 489385 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4088a00000000000→0x4088a00000000001 | — | — | fsu_taint |
| operand_read | 38 | 37 | 133370545 | 7 | 489388 | 0x000000000040065c | fmadd | 489385/489388 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 39 | 38 | 133370545 | 7 | 489388 | 0x000000000040065c | fmadd | 489385/489388 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 40 | 39 | 133370545 | 7 | 489388 | 0x000000000040065c | fmadd | 489385/489388 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 41 | 40 | 133371315 | 7 | 489388 | 0x000000000040065c | fmadd | —/489388 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1218 | 41 | 9405832205 | 7 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 414 | — | 1137787805 | 70 | 4452232 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3f9999999999999d→0x3f9999999999999f | — | — | origin |
| carrier_state | 415 | 414 | 1137787805 | 70 | 4452232 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3f9999999999999d→0x3f9999999999999f | — | — | fsu_taint |
| operand_read | 416 | 415 | 1137803205 | 70 | 4452302 | 0x0000000000400654 | fmadd | 4452232/4452302 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 417 | 416 | 1137803205 | 70 | 4452302 | 0x0000000000400654 | fmadd | 4452232/4452302 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 418 | 417 | 1137803205 | 70 | 4452302 | 0x0000000000400654 | fmadd | 4452232/4452302 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 419 | 418 | 1137803975 | 70 | 4452302 | 0x0000000000400654 | fmadd | —/4452302 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1281 | 419 | 9405832205 | 70 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 420 | — | 1156558095 | 71 | 4525852 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfcc8b4395810625→0xbfcc8b4395810605 | — | — | origin |
| carrier_state | 421 | 420 | 1156558095 | 71 | 4525852 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfcc8b4395810625→0xbfcc8b4395810605 | — | — | fsu_taint |
| operand_read | 422 | 421 | 1156573495 | 71 | 4525922 | 0x0000000000400654 | fmadd | 4525852/4525922 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 423 | 422 | 1156573495 | 71 | 4525922 | 0x0000000000400654 | fmadd | 4525852/4525922 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 424 | 423 | 1156573495 | 71 | 4525922 | 0x0000000000400654 | fmadd | 4525852/4525922 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 425 | 424 | 1156574265 | 71 | 4525922 | 0x0000000000400654 | fmadd | —/4525922 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1282 | 425 | 9405832205 | 71 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 426 | — | 1172132500 | 72 | 4587191 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x408c180000000000→0x408c180000000400 | — | — | origin |
| carrier_state | 427 | 426 | 1172132500 | 72 | 4587191 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x408c180000000000→0x408c180000000400 | — | — | fsu_taint |
| operand_read | 428 | 427 | 1172134425 | 72 | 4587194 | 0x0000000000400654 | fmadd | 4587191/4587194 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 429 | 428 | 1172134425 | 72 | 4587194 | 0x0000000000400654 | fmadd | 4587191/4587194 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 430 | 429 | 1172134425 | 72 | 4587194 | 0x0000000000400654 | fmadd | 4587191/4587194 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 431 | 430 | 1172135195 | 72 | 4587194 | 0x0000000000400654 | fmadd | —/4587194 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1283 | 431 | 9405832205 | 72 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 432 | — | 1183087290 | 73 | 4630322 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fef22d0e5604189→0x3fef22d0e5604089 | — | — | origin |
| carrier_state | 433 | 432 | 1183087290 | 73 | 4630322 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3fef22d0e5604189→0x3fef22d0e5604089 | — | — | fsu_taint |
| operand_read | 434 | 433 | 1183122710 | 73 | 4630466 | 0x0000000000400654 | fmadd | 4630322/4630466 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 435 | 434 | 1183122710 | 73 | 4630466 | 0x0000000000400654 | fmadd | 4630322/4630466 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 436 | 435 | 1183122710 | 73 | 4630466 | 0x0000000000400654 | fmadd | 4630322/4630466 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 437 | 436 | 1183123480 | 73 | 4630466 | 0x0000000000400654 | fmadd | —/4630466 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1284 | 437 | 9405832205 | 73 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 438 | — | 1199269995 | 74 | 4694583 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fef8d4fdf3b645a→0x3fef8d4fdf3b745a | — | — | origin |
| carrier_state | 439 | 438 | 1199269995 | 74 | 4694583 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fef8d4fdf3b645a→0x3fef8d4fdf3b745a | — | — | fsu_taint |
| operand_read | 440 | 439 | 1199294250 | 74 | 4694690 | 0x0000000000400654 | fmadd | 4694583/4694690 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 441 | 440 | 1199294250 | 74 | 4694690 | 0x0000000000400654 | fmadd | 4694583/4694690 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 442 | 441 | 1199294250 | 74 | 4694690 | 0x0000000000400654 | fmadd | 4694583/4694690 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 443 | 442 | 1199295020 | 74 | 4694690 | 0x0000000000400654 | fmadd | —/4694690 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1285 | 443 | 9405832205 | 74 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 444 | — | 1206976925 | 75 | 4724644 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fa999999999999b→0x3fa999999999b99b | — | — | origin |
| carrier_state | 445 | 444 | 1206976925 | 75 | 4724644 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fa999999999999b→0x3fa999999999b99b | — | — | fsu_taint |
| operand_read | 446 | 445 | 1206992325 | 75 | 4724714 | 0x0000000000400654 | fmadd | 4724644/4724714 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 447 | 446 | 1206992325 | 75 | 4724714 | 0x0000000000400654 | fmadd | 4724644/4724714 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 448 | 447 | 1206992325 | 75 | 4724714 | 0x0000000000400654 | fmadd | 4724644/4724714 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 449 | 448 | 1206993095 | 75 | 4724714 | 0x0000000000400654 | fmadd | —/4724714 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1286 | 449 | 9405832205 | 75 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 450 | — | 1223224695 | 76 | 4788326 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff09374bc6a7efa→0x3ff09374bc6a76fa | — | — | origin |
| carrier_state | 451 | 450 | 1223224695 | 76 | 4788326 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff09374bc6a7efa→0x3ff09374bc6a76fa | — | — | fsu_taint |
| operand_read | 452 | 451 | 1223260115 | 76 | 4788470 | 0x0000000000400654 | fmadd | 4788326/4788470 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 453 | 452 | 1223260115 | 76 | 4788470 | 0x0000000000400654 | fmadd | 4788326/4788470 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 454 | 453 | 1223260115 | 76 | 4788470 | 0x0000000000400654 | fmadd | 4788326/4788470 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 455 | 454 | 1223260885 | 76 | 4788470 | 0x0000000000400654 | fmadd | —/4788470 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1287 | 455 | 9405832205 | 76 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 456 | — | 1238255865 | 77 | 4847976 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4085b80000000000→0x4085b80000000008 | — | — | origin |
| carrier_state | 457 | 456 | 1238255865 | 77 | 4847976 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4085b80000000000→0x4085b80000000008 | — | — | fsu_taint |
| operand_read | 458 | 457 | 1238260100 | 77 | 4847979 | 0x0000000000400658 | fmadd | 4847976/4847979 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 459 | 458 | 1238260100 | 77 | 4847979 | 0x0000000000400658 | fmadd | 4847976/4847979 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 460 | 459 | 1238260100 | 77 | 4847979 | 0x0000000000400658 | fmadd | 4847976/4847979 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 461 | 460 | 1238260870 | 77 | 4847979 | 0x0000000000400658 | fmadd | —/4847979 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1288 | 461 | 9405832205 | 77 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 462 | — | 1248234680 | 78 | 4887399 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fe65604189374bc→0x3fe656041893743c | — | — | origin |
| carrier_state | 463 | 462 | 1248234680 | 78 | 4887399 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fe65604189374bc→0x3fe656041893743c | — | — | fsu_taint |
| operand_read | 464 | 463 | 1248258935 | 78 | 4887506 | 0x0000000000400654 | fmadd | 4887399/4887506 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 465 | 464 | 1248258935 | 78 | 4887506 | 0x0000000000400654 | fmadd | 4887399/4887506 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 466 | 465 | 1248258935 | 78 | 4887506 | 0x0000000000400654 | fmadd | 4887399/4887506 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 467 | 466 | 1248259705 | 78 | 4887506 | 0x0000000000400654 | fmadd | —/4887506 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1289 | 467 | 9405832205 | 78 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 468 | — | 1256696980 | 79 | 4920808 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfd7ef9db22d0e56→0xbfd7ef9db22d0e52 | — | — | origin |
| carrier_state | 469 | 468 | 1256696980 | 79 | 4920808 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfd7ef9db22d0e56→0xbfd7ef9db22d0e52 | — | — | fsu_taint |
| operand_read | 470 | 469 | 1256712380 | 79 | 4920878 | 0x0000000000400654 | fmadd | 4920808/4920878 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 471 | 470 | 1256712380 | 79 | 4920878 | 0x0000000000400654 | fmadd | 4920808/4920878 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 472 | 471 | 1256712380 | 79 | 4920878 | 0x0000000000400654 | fmadd | 4920808/4920878 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 473 | 472 | 1256713150 | 79 | 4920878 | 0x0000000000400654 | fmadd | —/4920878 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1290 | 473 | 9405832205 | 79 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 42 | — | 145995080 | 8 | 539248 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0x3fb3333333333334→0x3fb3333333331334 | — | — | origin |
| carrier_state | 43 | 42 | 145995080 | 8 | 539248 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0x3fb3333333333334→0x3fb3333333331334 | — | — | fsu_taint |
| operand_read | 44 | 43 | 146010480 | 8 | 539318 | 0x0000000000400654 | fmadd | 539248/539318 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 45 | 44 | 146010480 | 8 | 539318 | 0x0000000000400654 | fmadd | 539248/539318 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 46 | 45 | 146010480 | 8 | 539318 | 0x0000000000400654 | fmadd | 539248/539318 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 47 | 46 | 146011250 | 8 | 539318 | 0x0000000000400654 | fmadd | —/539318 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1219 | 47 | 9405832205 | 8 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 474 | — | 1277749550 | 80 | 5004110 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fe6b851eb851eb8→0x3fe6b851eb855eb8 | — | — | origin |
| carrier_state | 475 | 474 | 1277749550 | 80 | 5004110 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fe6b851eb851eb8→0x3fe6b851eb855eb8 | — | — | fsu_taint |
| operand_read | 476 | 475 | 1277784970 | 80 | 5004254 | 0x0000000000400654 | fmadd | 5004110/5004254 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 477 | 476 | 1277784970 | 80 | 5004254 | 0x0000000000400654 | fmadd | 5004110/5004254 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 478 | 477 | 1277784970 | 80 | 5004254 | 0x0000000000400654 | fmadd | 5004110/5004254 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 479 | 478 | 1277785740 | 80 | 5004254 | 0x0000000000400654 | fmadd | —/5004254 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1291 | 479 | 9405832205 | 80 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 480 | — | 1292699100 | 81 | 5063366 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fe395810624dd2f→0x3fe395810624dd2e | — | — | origin |
| carrier_state | 481 | 480 | 1292699100 | 81 | 5063366 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fe395810624dd2f→0x3fe395810624dd2e | — | — | fsu_taint |
| operand_read | 482 | 481 | 1292734520 | 81 | 5063510 | 0x0000000000400654 | fmadd | 5063366/5063510 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 483 | 482 | 1292734520 | 81 | 5063510 | 0x0000000000400654 | fmadd | 5063366/5063510 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 484 | 483 | 1292734520 | 81 | 5063510 | 0x0000000000400654 | fmadd | 5063366/5063510 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 485 | 484 | 1292735290 | 81 | 5063510 | 0x0000000000400654 | fmadd | —/5063510 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1292 | 485 | 9405832205 | 81 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 486 | — | 1314429270 | 82 | 5148794 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff7eb851eb851ec→0x3ff7eb851eb855ec | — | — | origin |
| carrier_state | 487 | 486 | 1314429270 | 82 | 5148794 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff7eb851eb851ec→0x3ff7eb851eb855ec | — | — | fsu_taint |
| operand_read | 488 | 487 | 1314464690 | 82 | 5148938 | 0x0000000000400654 | fmadd | 5148794/5148938 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 489 | 488 | 1314464690 | 82 | 5148938 | 0x0000000000400654 | fmadd | 5148794/5148938 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 490 | 489 | 1314464690 | 82 | 5148938 | 0x0000000000400654 | fmadd | 5148794/5148938 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 491 | 490 | 1314465460 | 82 | 5148938 | 0x0000000000400654 | fmadd | —/5148938 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1293 | 491 | 9405832205 | 82 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 492 | — | 1329774600 | 83 | 5209595 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x407e600000000000→0x407e600000008000 | — | — | origin |
| carrier_state | 493 | 492 | 1329774600 | 83 | 5209595 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x407e600000000000→0x407e600000008000 | — | — | fsu_taint |
| operand_read | 494 | 493 | 1329776525 | 83 | 5209598 | 0x0000000000400654 | fmadd | 5209595/5209598 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 495 | 494 | 1329776525 | 83 | 5209598 | 0x0000000000400654 | fmadd | 5209595/5209598 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 496 | 495 | 1329776525 | 83 | 5209598 | 0x0000000000400654 | fmadd | 5209595/5209598 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 497 | 496 | 1329777295 | 83 | 5209598 | 0x0000000000400654 | fmadd | —/5209598 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1294 | 497 | 9405832205 | 83 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 498 | — | 1337644000 | 84 | 5240593 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4077c00000000000→0x4077c00000000010 | — | — | origin |
| carrier_state | 499 | 498 | 1337644000 | 84 | 5240593 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4077c00000000000→0x4077c00000000010 | — | — | fsu_taint |
| operand_read | 500 | 499 | 1337647850 | 84 | 5240596 | 0x000000000040065c | fmadd | 5240593/5240596 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 501 | 500 | 1337647850 | 84 | 5240596 | 0x000000000040065c | fmadd | 5240593/5240596 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 502 | 501 | 1337647850 | 84 | 5240596 | 0x000000000040065c | fmadd | 5240593/5240596 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 503 | 502 | 1337648620 | 84 | 5240596 | 0x000000000040065c | fmadd | —/5240596 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1295 | 503 | 9405832205 | 84 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 504 | — | 1348577615 | 85 | 5283649 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x408d080000000000→0x408d080000000200 | — | — | origin |
| carrier_state | 505 | 504 | 1348577615 | 85 | 5283649 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x408d080000000000→0x408d080000000200 | — | — | fsu_taint |
| operand_read | 506 | 505 | 1348581465 | 85 | 5283652 | 0x000000000040065c | fmadd | 5283649/5283652 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 507 | 506 | 1348581465 | 85 | 5283652 | 0x000000000040065c | fmadd | 5283649/5283652 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 508 | 507 | 1348581465 | 85 | 5283652 | 0x000000000040065c | fmadd | 5283649/5283652 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 509 | 508 | 1348582235 | 85 | 5283652 | 0x000000000040065c | fmadd | —/5283652 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1296 | 509 | 9405832205 | 85 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 510 | — | 1363182975 | 86 | 5340672 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4071e00000000000→0x4071e00000010000 | — | — | origin |
| carrier_state | 511 | 510 | 1363182975 | 86 | 5340672 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4071e00000000000→0x4071e00000010000 | — | — | fsu_taint |
| operand_read | 512 | 511 | 1363187210 | 86 | 5340675 | 0x0000000000400658 | fmadd | 5340672/5340675 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 513 | 512 | 1363187210 | 86 | 5340675 | 0x0000000000400658 | fmadd | 5340672/5340675 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 514 | 513 | 1363187210 | 86 | 5340675 | 0x0000000000400658 | fmadd | 5340672/5340675 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 515 | 514 | 1363187980 | 86 | 5340675 | 0x0000000000400658 | fmadd | —/5340675 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1297 | 515 | 9405832205 | 86 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 516 | — | 1373765855 | 87 | 5382688 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfdab020c49ba5e3→0xbfdab020c49ba4e3 | — | — | origin |
| carrier_state | 517 | 516 | 1373765855 | 87 | 5382688 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfdab020c49ba5e3→0xbfdab020c49ba4e3 | — | — | fsu_taint |
| operand_read | 518 | 517 | 1373781255 | 87 | 5382758 | 0x0000000000400654 | fmadd | 5382688/5382758 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 519 | 518 | 1373781255 | 87 | 5382758 | 0x0000000000400654 | fmadd | 5382688/5382758 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 520 | 519 | 1373781255 | 87 | 5382758 | 0x0000000000400654 | fmadd | 5382688/5382758 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 521 | 520 | 1373782025 | 87 | 5382758 | 0x0000000000400654 | fmadd | —/5382758 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1298 | 521 | 9405832205 | 87 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 522 | — | 1387344035 | 88 | 5436076 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fb0e5604189374d→0x3fb0e5604189364d | — | — | origin |
| carrier_state | 523 | 522 | 1387344035 | 88 | 5436076 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fb0e5604189374d→0x3fb0e5604189364d | — | — | fsu_taint |
| operand_read | 524 | 523 | 1387359435 | 88 | 5436146 | 0x0000000000400654 | fmadd | 5436076/5436146 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 525 | 524 | 1387359435 | 88 | 5436146 | 0x0000000000400654 | fmadd | 5436076/5436146 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 526 | 525 | 1387359435 | 88 | 5436146 | 0x0000000000400654 | fmadd | 5436076/5436146 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 527 | 526 | 1387360205 | 88 | 5436146 | 0x0000000000400654 | fmadd | —/5436146 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1299 | 527 | 9405832205 | 88 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 528 | — | 1399034175 | 89 | 5482619 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4083300000000000→0x4083300000000001 | — | — | origin |
| carrier_state | 529 | 528 | 1399034175 | 89 | 5482619 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4083300000000000→0x4083300000000001 | — | — | fsu_taint |
| operand_read | 530 | 529 | 1399036100 | 89 | 5482622 | 0x0000000000400654 | fmadd | 5482619/5482622 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 531 | 530 | 1399036100 | 89 | 5482622 | 0x0000000000400654 | fmadd | 5482619/5482622 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 532 | 531 | 1399036100 | 89 | 5482622 | 0x0000000000400654 | fmadd | 5482619/5482622 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 533 | 532 | 1399036870 | 89 | 5482622 | 0x0000000000400654 | fmadd | —/5482622 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1300 | 533 | 9405832205 | 89 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 48 | — | 163877175 | 9 | 609625 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x407b800000000000→0x407b800000000100 | — | — | origin |
| carrier_state | 49 | 48 | 163877175 | 9 | 609625 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x407b800000000000→0x407b800000000100 | — | — | fsu_taint |
| operand_read | 50 | 49 | 163881025 | 9 | 609628 | 0x000000000040065c | fmadd | 609625/609628 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 51 | 50 | 163881025 | 9 | 609628 | 0x000000000040065c | fmadd | 609625/609628 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 52 | 51 | 163881025 | 9 | 609628 | 0x000000000040065c | fmadd | 609625/609628 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 53 | 52 | 163881795 | 9 | 609628 | 0x000000000040065c | fmadd | —/609628 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1220 | 53 | 9405832205 | 9 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 534 | — | 1407713230 | 90 | 5516896 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fce76c8b4395811→0x3fce76c8b4395851 | — | — | origin |
| carrier_state | 535 | 534 | 1407713230 | 90 | 5516896 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fce76c8b4395811→0x3fce76c8b4395851 | — | — | fsu_taint |
| operand_read | 536 | 535 | 1407728630 | 90 | 5516966 | 0x0000000000400654 | fmadd | 5516896/5516966 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 537 | 536 | 1407728630 | 90 | 5516966 | 0x0000000000400654 | fmadd | 5516896/5516966 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 538 | 537 | 1407728630 | 90 | 5516966 | 0x0000000000400654 | fmadd | 5516896/5516966 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 539 | 538 | 1407729400 | 90 | 5516966 | 0x0000000000400654 | fmadd | —/5516966 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1301 | 539 | 9405832205 | 90 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 540 | — | 1416895480 | 91 | 5552967 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fdaf1a9fbe76c8b→0x3fdaf1a9fbe72c8b | — | — | origin |
| carrier_state | 541 | 540 | 1416895480 | 91 | 5552967 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fdaf1a9fbe76c8b→0x3fdaf1a9fbe72c8b | — | — | fsu_taint |
| operand_read | 542 | 541 | 1416919735 | 91 | 5553074 | 0x0000000000400654 | fmadd | 5552967/5553074 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 543 | 542 | 1416919735 | 91 | 5553074 | 0x0000000000400654 | fmadd | 5552967/5553074 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 544 | 543 | 1416919735 | 91 | 5553074 | 0x0000000000400654 | fmadd | 5552967/5553074 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 545 | 544 | 1416920505 | 91 | 5553074 | 0x0000000000400654 | fmadd | —/5553074 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1302 | 545 | 9405832205 | 91 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 546 | — | 1426354160 | 92 | 5590439 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x4081f80000000000→0x4081f80000001000 | — | — | origin |
| carrier_state | 547 | 546 | 1426354160 | 92 | 5590439 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x4081f80000000000→0x4081f80000001000 | — | — | fsu_taint |
| operand_read | 548 | 547 | 1426356085 | 92 | 5590442 | 0x0000000000400654 | fmadd | 5590439/5590442 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 549 | 548 | 1426356085 | 92 | 5590442 | 0x0000000000400654 | fmadd | 5590439/5590442 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 550 | 549 | 1426356085 | 92 | 5590442 | 0x0000000000400654 | fmadd | 5590439/5590442 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 551 | 550 | 1426356855 | 92 | 5590442 | 0x0000000000400654 | fmadd | —/5590442 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1303 | 551 | 9405832205 | 92 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 552 | — | 1441526240 | 93 | 5650307 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4087400000000000→0x4087400000000001 | — | — | origin |
| carrier_state | 553 | 552 | 1441526240 | 93 | 5650307 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x4087400000000000→0x4087400000000001 | — | — | fsu_taint |
| operand_read | 554 | 553 | 1441528165 | 93 | 5650310 | 0x0000000000400654 | fmadd | 5650307/5650310 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 555 | 554 | 1441528165 | 93 | 5650310 | 0x0000000000400654 | fmadd | 5650307/5650310 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 556 | 555 | 1441528165 | 93 | 5650310 | 0x0000000000400654 | fmadd | 5650307/5650310 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 557 | 556 | 1441528935 | 93 | 5650310 | 0x0000000000400654 | fmadd | —/5650310 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1304 | 557 | 9405832205 | 93 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 558 | — | 1455542935 | 94 | 5705822 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff64dd2f1a9fbe8→0x3ff64dd2f1a9fbf8 | — | — | origin |
| carrier_state | 559 | 558 | 1455542935 | 94 | 5705822 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff64dd2f1a9fbe8→0x3ff64dd2f1a9fbf8 | — | — | fsu_taint |
| operand_read | 560 | 559 | 1455578355 | 94 | 5705966 | 0x0000000000400654 | fmadd | 5705822/5705966 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 561 | 560 | 1455578355 | 94 | 5705966 | 0x0000000000400654 | fmadd | 5705822/5705966 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 562 | 561 | 1455578355 | 94 | 5705966 | 0x0000000000400654 | fmadd | 5705822/5705966 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 563 | 562 | 1455579125 | 94 | 5705966 | 0x0000000000400654 | fmadd | —/5705966 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1305 | 563 | 9405832205 | 94 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 564 | — | 1464615845 | 95 | 5741282 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff7916872b020c5→0x3ff7916872b060c5 | — | — | origin |
| carrier_state | 565 | 564 | 1464615845 | 95 | 5741282 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3ff7916872b020c5→0x3ff7916872b060c5 | — | — | fsu_taint |
| operand_read | 566 | 565 | 1464651265 | 95 | 5741426 | 0x0000000000400654 | fmadd | 5741282/5741426 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 567 | 566 | 1464651265 | 95 | 5741426 | 0x0000000000400654 | fmadd | 5741282/5741426 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 568 | 567 | 1464651265 | 95 | 5741426 | 0x0000000000400654 | fmadd | 5741282/5741426 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 569 | 568 | 1464652035 | 95 | 5741426 | 0x0000000000400654 | fmadd | —/5741426 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1306 | 569 | 9405832205 | 95 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 570 | — | 1480366195 | 96 | 5803127 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x407bb00000000000→0x407bb00000002000 | — | — | origin |
| carrier_state | 571 | 570 | 1480366195 | 96 | 5803127 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x407bb00000000000→0x407bb00000002000 | — | — | fsu_taint |
| operand_read | 572 | 571 | 1480368120 | 96 | 5803130 | 0x0000000000400654 | fmadd | 5803127/5803130 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 573 | 572 | 1480368120 | 96 | 5803130 | 0x0000000000400654 | fmadd | 5803127/5803130 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 574 | 573 | 1480368120 | 96 | 5803130 | 0x0000000000400654 | fmadd | 5803127/5803130 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 575 | 574 | 1480368890 | 96 | 5803130 | 0x0000000000400654 | fmadd | —/5803130 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1307 | 575 | 9405832205 | 96 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 576 | — | 1496913880 | 97 | 5868867 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3ff09fbe76c8b439→0x3ff09fbe76c8b039 | — | — | origin |
| carrier_state | 577 | 576 | 1496913880 | 97 | 5868867 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3ff09fbe76c8b439→0x3ff09fbe76c8b039 | — | — | fsu_taint |
| operand_read | 578 | 577 | 1496938135 | 97 | 5868974 | 0x0000000000400654 | fmadd | 5868867/5868974 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 579 | 578 | 1496938135 | 97 | 5868974 | 0x0000000000400654 | fmadd | 5868867/5868974 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 580 | 579 | 1496938135 | 97 | 5868974 | 0x0000000000400654 | fmadd | 5868867/5868974 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 581 | 580 | 1496938905 | 97 | 5868974 | 0x0000000000400654 | fmadd | —/5868974 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1308 | 581 | 9405832205 | 97 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 582 | — | 1511762175 | 98 | 5927437 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x408ee80000000000→0x408ee80000000200 | — | — | origin |
| carrier_state | 583 | 582 | 1511762175 | 98 | 5927437 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x408ee80000000000→0x408ee80000000200 | — | — | fsu_taint |
| operand_read | 584 | 583 | 1511766025 | 98 | 5927440 | 0x000000000040065c | fmadd | 5927437/5927440 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 585 | 584 | 1511766025 | 98 | 5927440 | 0x000000000040065c | fmadd | 5927437/5927440 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 586 | 585 | 1511766025 | 98 | 5927440 | 0x000000000040065c | fmadd | 5927437/5927440 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 587 | 586 | 1511766795 | 98 | 5927440 | 0x000000000040065c | fmadd | —/5927440 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1309 | 587 | 9405832205 | 98 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 588 | — | 1532256880 | 99 | 6007863 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff353f7ced91687→0x3ff353f7ced91287 | — | — | origin |
| carrier_state | 589 | 588 | 1532256880 | 99 | 6007863 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff353f7ced91687→0x3ff353f7ced91287 | — | — | fsu_taint |
| operand_read | 590 | 589 | 1532281135 | 99 | 6007970 | 0x0000000000400654 | fmadd | 6007863/6007970 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 591 | 590 | 1532281135 | 99 | 6007970 | 0x0000000000400654 | fmadd | 6007863/6007970 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 592 | 591 | 1532281135 | 99 | 6007970 | 0x0000000000400654 | fmadd | 6007863/6007970 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 593 | 592 | 1532281905 | 99 | 6007970 | 0x0000000000400654 | fmadd | —/6007970 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1310 | 593 | 9405832205 | 99 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

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

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 682a7b93b6f655afcda2eba556aee2d3469c5b1fd5c2a9897510f0cecdb431e5 != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：202 / 202
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：1414
- attempted / eligible / activated：202 / 2097155 / 202

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
- `5` (commit) → `1212` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

### fault 10

主链每一条边均验证为直接 parent：

- `54` (fault_applied) → `55` (carrier_state)；child.parent=54 ✓
- `55` (carrier_state) → `56` (operand_read)；child.parent=55 ✓
- `56` (operand_read) → `57` (execute)；child.parent=56 ✓
- `57` (execute) → `58` (prf_writeback)；child.parent=57 ✓
- `58` (prf_writeback) → `59` (commit)；child.parent=58 ✓
- `59` (commit) → `1221` (chain_end)；child.parent=59 ✓

- L5 真实见证：`59` kind=commit outcome=errant_commit oracle_diff=—

### fault 100

主链每一条边均验证为直接 parent：

- `594` (fault_applied) → `595` (carrier_state)；child.parent=594 ✓
- `595` (carrier_state) → `596` (operand_read)；child.parent=595 ✓
- `596` (operand_read) → `597` (execute)；child.parent=596 ✓
- `597` (execute) → `598` (prf_writeback)；child.parent=597 ✓
- `598` (prf_writeback) → `599` (commit)；child.parent=598 ✓
- `599` (commit) → `1311` (chain_end)；child.parent=599 ✓

- L5 真实见证：`599` kind=commit outcome=errant_commit oracle_diff=—

### fault 101

主链每一条边均验证为直接 parent：

- `600` (fault_applied) → `601` (carrier_state)；child.parent=600 ✓
- `601` (carrier_state) → `602` (operand_read)；child.parent=601 ✓
- `602` (operand_read) → `603` (execute)；child.parent=602 ✓
- `603` (execute) → `604` (prf_writeback)；child.parent=603 ✓
- `604` (prf_writeback) → `605` (commit)；child.parent=604 ✓
- `605` (commit) → `1312` (chain_end)；child.parent=605 ✓

- L5 真实见证：`605` kind=commit outcome=errant_commit oracle_diff=—

### fault 102

主链每一条边均验证为直接 parent：

- `606` (fault_applied) → `607` (carrier_state)；child.parent=606 ✓
- `607` (carrier_state) → `608` (operand_read)；child.parent=607 ✓
- `608` (operand_read) → `609` (execute)；child.parent=608 ✓
- `609` (execute) → `610` (prf_writeback)；child.parent=609 ✓
- `610` (prf_writeback) → `611` (commit)；child.parent=610 ✓
- `611` (commit) → `1313` (chain_end)；child.parent=611 ✓

- L5 真实见证：`611` kind=commit outcome=errant_commit oracle_diff=—

### fault 103

主链每一条边均验证为直接 parent：

- `612` (fault_applied) → `613` (carrier_state)；child.parent=612 ✓
- `613` (carrier_state) → `614` (operand_read)；child.parent=613 ✓
- `614` (operand_read) → `615` (execute)；child.parent=614 ✓
- `615` (execute) → `616` (prf_writeback)；child.parent=615 ✓
- `616` (prf_writeback) → `617` (commit)；child.parent=616 ✓
- `617` (commit) → `1314` (chain_end)；child.parent=617 ✓

- L5 真实见证：`617` kind=commit outcome=errant_commit oracle_diff=—

### fault 104

主链每一条边均验证为直接 parent：

- `618` (fault_applied) → `619` (carrier_state)；child.parent=618 ✓
- `619` (carrier_state) → `620` (operand_read)；child.parent=619 ✓
- `620` (operand_read) → `621` (execute)；child.parent=620 ✓
- `621` (execute) → `622` (prf_writeback)；child.parent=621 ✓
- `622` (prf_writeback) → `623` (commit)；child.parent=622 ✓
- `623` (commit) → `1315` (chain_end)；child.parent=623 ✓

- L5 真实见证：`623` kind=commit outcome=errant_commit oracle_diff=—

### fault 105

主链每一条边均验证为直接 parent：

- `624` (fault_applied) → `625` (carrier_state)；child.parent=624 ✓
- `625` (carrier_state) → `626` (operand_read)；child.parent=625 ✓
- `626` (operand_read) → `627` (execute)；child.parent=626 ✓
- `627` (execute) → `628` (prf_writeback)；child.parent=627 ✓
- `628` (prf_writeback) → `629` (commit)；child.parent=628 ✓
- `629` (commit) → `1316` (chain_end)；child.parent=629 ✓

- L5 真实见证：`629` kind=commit outcome=errant_commit oracle_diff=—

### fault 106

主链每一条边均验证为直接 parent：

- `630` (fault_applied) → `631` (carrier_state)；child.parent=630 ✓
- `631` (carrier_state) → `632` (operand_read)；child.parent=631 ✓
- `632` (operand_read) → `633` (execute)；child.parent=632 ✓
- `633` (execute) → `634` (prf_writeback)；child.parent=633 ✓
- `634` (prf_writeback) → `635` (commit)；child.parent=634 ✓
- `635` (commit) → `1317` (chain_end)；child.parent=635 ✓

- L5 真实见证：`635` kind=commit outcome=errant_commit oracle_diff=—

### fault 107

主链每一条边均验证为直接 parent：

- `636` (fault_applied) → `637` (carrier_state)；child.parent=636 ✓
- `637` (carrier_state) → `638` (operand_read)；child.parent=637 ✓
- `638` (operand_read) → `639` (execute)；child.parent=638 ✓
- `639` (execute) → `640` (prf_writeback)；child.parent=639 ✓
- `640` (prf_writeback) → `641` (commit)；child.parent=640 ✓
- `641` (commit) → `1318` (chain_end)；child.parent=641 ✓

- L5 真实见证：`641` kind=commit outcome=errant_commit oracle_diff=—

### fault 108

主链每一条边均验证为直接 parent：

- `642` (fault_applied) → `643` (carrier_state)；child.parent=642 ✓
- `643` (carrier_state) → `644` (operand_read)；child.parent=643 ✓
- `644` (operand_read) → `645` (execute)；child.parent=644 ✓
- `645` (execute) → `646` (prf_writeback)；child.parent=645 ✓
- `646` (prf_writeback) → `647` (commit)；child.parent=646 ✓
- `647` (commit) → `1319` (chain_end)；child.parent=647 ✓

- L5 真实见证：`647` kind=commit outcome=errant_commit oracle_diff=—

### fault 109

主链每一条边均验证为直接 parent：

- `648` (fault_applied) → `649` (carrier_state)；child.parent=648 ✓
- `649` (carrier_state) → `650` (operand_read)；child.parent=649 ✓
- `650` (operand_read) → `651` (execute)；child.parent=650 ✓
- `651` (execute) → `652` (prf_writeback)；child.parent=651 ✓
- `652` (prf_writeback) → `653` (commit)；child.parent=652 ✓
- `653` (commit) → `1320` (chain_end)；child.parent=653 ✓

- L5 真实见证：`653` kind=commit outcome=errant_commit oracle_diff=—

### fault 11

主链每一条边均验证为直接 parent：

- `60` (fault_applied) → `61` (carrier_state)；child.parent=60 ✓
- `61` (carrier_state) → `62` (operand_read)；child.parent=61 ✓
- `62` (operand_read) → `63` (execute)；child.parent=62 ✓
- `63` (execute) → `64` (prf_writeback)；child.parent=63 ✓
- `64` (prf_writeback) → `65` (commit)；child.parent=64 ✓
- `65` (commit) → `1222` (chain_end)；child.parent=65 ✓

- L5 真实见证：`65` kind=commit outcome=errant_commit oracle_diff=—

### fault 110

主链每一条边均验证为直接 parent：

- `654` (fault_applied) → `655` (carrier_state)；child.parent=654 ✓
- `655` (carrier_state) → `656` (operand_read)；child.parent=655 ✓
- `656` (operand_read) → `657` (execute)；child.parent=656 ✓
- `657` (execute) → `658` (prf_writeback)；child.parent=657 ✓
- `658` (prf_writeback) → `659` (commit)；child.parent=658 ✓
- `659` (commit) → `1321` (chain_end)；child.parent=659 ✓

- L5 真实见证：`659` kind=commit outcome=errant_commit oracle_diff=—

### fault 111

主链每一条边均验证为直接 parent：

- `660` (fault_applied) → `661` (carrier_state)；child.parent=660 ✓
- `661` (carrier_state) → `662` (operand_read)；child.parent=661 ✓
- `662` (operand_read) → `663` (execute)；child.parent=662 ✓
- `663` (execute) → `664` (prf_writeback)；child.parent=663 ✓
- `664` (prf_writeback) → `665` (commit)；child.parent=664 ✓
- `665` (commit) → `1322` (chain_end)；child.parent=665 ✓

- L5 真实见证：`665` kind=commit outcome=errant_commit oracle_diff=—

### fault 112

主链每一条边均验证为直接 parent：

- `666` (fault_applied) → `667` (carrier_state)；child.parent=666 ✓
- `667` (carrier_state) → `668` (operand_read)；child.parent=667 ✓
- `668` (operand_read) → `669` (execute)；child.parent=668 ✓
- `669` (execute) → `670` (prf_writeback)；child.parent=669 ✓
- `670` (prf_writeback) → `671` (commit)；child.parent=670 ✓
- `671` (commit) → `1323` (chain_end)；child.parent=671 ✓

- L5 真实见证：`671` kind=commit outcome=errant_commit oracle_diff=—

### fault 113

主链每一条边均验证为直接 parent：

- `672` (fault_applied) → `673` (carrier_state)；child.parent=672 ✓
- `673` (carrier_state) → `674` (operand_read)；child.parent=673 ✓
- `674` (operand_read) → `675` (execute)；child.parent=674 ✓
- `675` (execute) → `676` (prf_writeback)；child.parent=675 ✓
- `676` (prf_writeback) → `677` (commit)；child.parent=676 ✓
- `677` (commit) → `1324` (chain_end)；child.parent=677 ✓

- L5 真实见证：`677` kind=commit outcome=errant_commit oracle_diff=—

### fault 114

主链每一条边均验证为直接 parent：

- `678` (fault_applied) → `679` (carrier_state)；child.parent=678 ✓
- `679` (carrier_state) → `680` (operand_read)；child.parent=679 ✓
- `680` (operand_read) → `681` (execute)；child.parent=680 ✓
- `681` (execute) → `682` (prf_writeback)；child.parent=681 ✓
- `682` (prf_writeback) → `683` (commit)；child.parent=682 ✓
- `683` (commit) → `1325` (chain_end)；child.parent=683 ✓

- L5 真实见证：`683` kind=commit outcome=errant_commit oracle_diff=—

### fault 115

主链每一条边均验证为直接 parent：

- `684` (fault_applied) → `685` (carrier_state)；child.parent=684 ✓
- `685` (carrier_state) → `686` (operand_read)；child.parent=685 ✓
- `686` (operand_read) → `687` (execute)；child.parent=686 ✓
- `687` (execute) → `688` (prf_writeback)；child.parent=687 ✓
- `688` (prf_writeback) → `689` (commit)；child.parent=688 ✓
- `689` (commit) → `1326` (chain_end)；child.parent=689 ✓

- L5 真实见证：`689` kind=commit outcome=errant_commit oracle_diff=—

### fault 116

主链每一条边均验证为直接 parent：

- `690` (fault_applied) → `691` (carrier_state)；child.parent=690 ✓
- `691` (carrier_state) → `692` (operand_read)；child.parent=691 ✓
- `692` (operand_read) → `693` (execute)；child.parent=692 ✓
- `693` (execute) → `694` (prf_writeback)；child.parent=693 ✓
- `694` (prf_writeback) → `695` (commit)；child.parent=694 ✓
- `695` (commit) → `1327` (chain_end)；child.parent=695 ✓

- L5 真实见证：`695` kind=commit outcome=errant_commit oracle_diff=—

### fault 117

主链每一条边均验证为直接 parent：

- `696` (fault_applied) → `697` (carrier_state)；child.parent=696 ✓
- `697` (carrier_state) → `698` (operand_read)；child.parent=697 ✓
- `698` (operand_read) → `699` (execute)；child.parent=698 ✓
- `699` (execute) → `700` (prf_writeback)；child.parent=699 ✓
- `700` (prf_writeback) → `701` (commit)；child.parent=700 ✓
- `701` (commit) → `1328` (chain_end)；child.parent=701 ✓

- L5 真实见证：`701` kind=commit outcome=errant_commit oracle_diff=—

### fault 118

主链每一条边均验证为直接 parent：

- `702` (fault_applied) → `703` (carrier_state)；child.parent=702 ✓
- `703` (carrier_state) → `704` (operand_read)；child.parent=703 ✓
- `704` (operand_read) → `705` (execute)；child.parent=704 ✓
- `705` (execute) → `706` (prf_writeback)；child.parent=705 ✓
- `706` (prf_writeback) → `707` (commit)；child.parent=706 ✓
- `707` (commit) → `1329` (chain_end)；child.parent=707 ✓

- L5 真实见证：`707` kind=commit outcome=errant_commit oracle_diff=—

### fault 119

主链每一条边均验证为直接 parent：

- `708` (fault_applied) → `709` (carrier_state)；child.parent=708 ✓
- `709` (carrier_state) → `710` (operand_read)；child.parent=709 ✓
- `710` (operand_read) → `711` (execute)；child.parent=710 ✓
- `711` (execute) → `712` (prf_writeback)；child.parent=711 ✓
- `712` (prf_writeback) → `713` (commit)；child.parent=712 ✓
- `713` (commit) → `1330` (chain_end)；child.parent=713 ✓

- L5 真实见证：`713` kind=commit outcome=errant_commit oracle_diff=—

### fault 12

主链每一条边均验证为直接 parent：

- `66` (fault_applied) → `67` (carrier_state)；child.parent=66 ✓
- `67` (carrier_state) → `68` (operand_read)；child.parent=67 ✓
- `68` (operand_read) → `69` (execute)；child.parent=68 ✓
- `69` (execute) → `70` (prf_writeback)；child.parent=69 ✓
- `70` (prf_writeback) → `71` (commit)；child.parent=70 ✓
- `71` (commit) → `1223` (chain_end)；child.parent=71 ✓

- L5 真实见证：`71` kind=commit outcome=errant_commit oracle_diff=—

### fault 120

主链每一条边均验证为直接 parent：

- `714` (fault_applied) → `715` (carrier_state)；child.parent=714 ✓
- `715` (carrier_state) → `716` (operand_read)；child.parent=715 ✓
- `716` (operand_read) → `717` (execute)；child.parent=716 ✓
- `717` (execute) → `718` (prf_writeback)；child.parent=717 ✓
- `718` (prf_writeback) → `719` (commit)；child.parent=718 ✓
- `719` (commit) → `1331` (chain_end)；child.parent=719 ✓

- L5 真实见证：`719` kind=commit outcome=errant_commit oracle_diff=—

### fault 121

主链每一条边均验证为直接 parent：

- `720` (fault_applied) → `721` (carrier_state)；child.parent=720 ✓
- `721` (carrier_state) → `722` (operand_read)；child.parent=721 ✓
- `722` (operand_read) → `723` (execute)；child.parent=722 ✓
- `723` (execute) → `724` (prf_writeback)；child.parent=723 ✓
- `724` (prf_writeback) → `725` (commit)；child.parent=724 ✓
- `725` (commit) → `1332` (chain_end)；child.parent=725 ✓

- L5 真实见证：`725` kind=commit outcome=errant_commit oracle_diff=—

### fault 122

主链每一条边均验证为直接 parent：

- `726` (fault_applied) → `727` (carrier_state)；child.parent=726 ✓
- `727` (carrier_state) → `728` (operand_read)；child.parent=727 ✓
- `728` (operand_read) → `729` (execute)；child.parent=728 ✓
- `729` (execute) → `730` (prf_writeback)；child.parent=729 ✓
- `730` (prf_writeback) → `731` (commit)；child.parent=730 ✓
- `731` (commit) → `1333` (chain_end)；child.parent=731 ✓

- L5 真实见证：`731` kind=commit outcome=errant_commit oracle_diff=—

### fault 123

主链每一条边均验证为直接 parent：

- `732` (fault_applied) → `733` (carrier_state)；child.parent=732 ✓
- `733` (carrier_state) → `734` (operand_read)；child.parent=733 ✓
- `734` (operand_read) → `735` (execute)；child.parent=734 ✓
- `735` (execute) → `736` (prf_writeback)；child.parent=735 ✓
- `736` (prf_writeback) → `737` (commit)；child.parent=736 ✓
- `737` (commit) → `1334` (chain_end)；child.parent=737 ✓

- L5 真实见证：`737` kind=commit outcome=errant_commit oracle_diff=—

### fault 124

主链每一条边均验证为直接 parent：

- `738` (fault_applied) → `739` (carrier_state)；child.parent=738 ✓
- `739` (carrier_state) → `740` (operand_read)；child.parent=739 ✓
- `740` (operand_read) → `741` (execute)；child.parent=740 ✓
- `741` (execute) → `742` (prf_writeback)；child.parent=741 ✓
- `742` (prf_writeback) → `743` (commit)；child.parent=742 ✓
- `743` (commit) → `1335` (chain_end)；child.parent=743 ✓

- L5 真实见证：`743` kind=commit outcome=errant_commit oracle_diff=—

### fault 125

主链每一条边均验证为直接 parent：

- `744` (fault_applied) → `745` (carrier_state)；child.parent=744 ✓
- `745` (carrier_state) → `746` (operand_read)；child.parent=745 ✓
- `746` (operand_read) → `747` (execute)；child.parent=746 ✓
- `747` (execute) → `748` (prf_writeback)；child.parent=747 ✓
- `748` (prf_writeback) → `749` (commit)；child.parent=748 ✓
- `749` (commit) → `1336` (chain_end)；child.parent=749 ✓

- L5 真实见证：`749` kind=commit outcome=errant_commit oracle_diff=—

### fault 126

主链每一条边均验证为直接 parent：

- `750` (fault_applied) → `751` (carrier_state)；child.parent=750 ✓
- `751` (carrier_state) → `752` (operand_read)；child.parent=751 ✓
- `752` (operand_read) → `753` (execute)；child.parent=752 ✓
- `753` (execute) → `754` (prf_writeback)；child.parent=753 ✓
- `754` (prf_writeback) → `755` (commit)；child.parent=754 ✓
- `755` (commit) → `1337` (chain_end)；child.parent=755 ✓

- L5 真实见证：`755` kind=commit outcome=errant_commit oracle_diff=—

### fault 127

主链每一条边均验证为直接 parent：

- `756` (fault_applied) → `757` (carrier_state)；child.parent=756 ✓
- `757` (carrier_state) → `758` (operand_read)；child.parent=757 ✓
- `758` (operand_read) → `759` (execute)；child.parent=758 ✓
- `759` (execute) → `760` (prf_writeback)；child.parent=759 ✓
- `760` (prf_writeback) → `761` (commit)；child.parent=760 ✓
- `761` (commit) → `1338` (chain_end)；child.parent=761 ✓

- L5 真实见证：`761` kind=commit outcome=errant_commit oracle_diff=—

### fault 128

主链每一条边均验证为直接 parent：

- `762` (fault_applied) → `763` (carrier_state)；child.parent=762 ✓
- `763` (carrier_state) → `764` (operand_read)；child.parent=763 ✓
- `764` (operand_read) → `765` (execute)；child.parent=764 ✓
- `765` (execute) → `766` (prf_writeback)；child.parent=765 ✓
- `766` (prf_writeback) → `767` (commit)；child.parent=766 ✓
- `767` (commit) → `1339` (chain_end)；child.parent=767 ✓

- L5 真实见证：`767` kind=commit outcome=errant_commit oracle_diff=—

### fault 129

主链每一条边均验证为直接 parent：

- `768` (fault_applied) → `769` (carrier_state)；child.parent=768 ✓
- `769` (carrier_state) → `770` (operand_read)；child.parent=769 ✓
- `770` (operand_read) → `771` (execute)；child.parent=770 ✓
- `771` (execute) → `772` (prf_writeback)；child.parent=771 ✓
- `772` (prf_writeback) → `773` (commit)；child.parent=772 ✓
- `773` (commit) → `1340` (chain_end)；child.parent=773 ✓

- L5 真实见证：`773` kind=commit outcome=errant_commit oracle_diff=—

### fault 13

主链每一条边均验证为直接 parent：

- `72` (fault_applied) → `73` (carrier_state)；child.parent=72 ✓
- `73` (carrier_state) → `74` (operand_read)；child.parent=73 ✓
- `74` (operand_read) → `75` (execute)；child.parent=74 ✓
- `75` (execute) → `76` (prf_writeback)；child.parent=75 ✓
- `76` (prf_writeback) → `77` (commit)；child.parent=76 ✓
- `77` (commit) → `1224` (chain_end)；child.parent=77 ✓

- L5 真实见证：`77` kind=commit outcome=errant_commit oracle_diff=—

### fault 130

主链每一条边均验证为直接 parent：

- `774` (fault_applied) → `775` (carrier_state)；child.parent=774 ✓
- `775` (carrier_state) → `776` (operand_read)；child.parent=775 ✓
- `776` (operand_read) → `777` (execute)；child.parent=776 ✓
- `777` (execute) → `778` (prf_writeback)；child.parent=777 ✓
- `778` (prf_writeback) → `779` (commit)；child.parent=778 ✓
- `779` (commit) → `1341` (chain_end)；child.parent=779 ✓

- L5 真实见证：`779` kind=commit outcome=errant_commit oracle_diff=—

### fault 131

主链每一条边均验证为直接 parent：

- `780` (fault_applied) → `781` (carrier_state)；child.parent=780 ✓
- `781` (carrier_state) → `782` (operand_read)；child.parent=781 ✓
- `782` (operand_read) → `783` (execute)；child.parent=782 ✓
- `783` (execute) → `784` (prf_writeback)；child.parent=783 ✓
- `784` (prf_writeback) → `785` (commit)；child.parent=784 ✓
- `785` (commit) → `1342` (chain_end)；child.parent=785 ✓

- L5 真实见证：`785` kind=commit outcome=errant_commit oracle_diff=—

### fault 132

主链每一条边均验证为直接 parent：

- `786` (fault_applied) → `787` (carrier_state)；child.parent=786 ✓
- `787` (carrier_state) → `788` (operand_read)；child.parent=787 ✓
- `788` (operand_read) → `789` (execute)；child.parent=788 ✓
- `789` (execute) → `790` (prf_writeback)；child.parent=789 ✓
- `790` (prf_writeback) → `791` (commit)；child.parent=790 ✓
- `791` (commit) → `1343` (chain_end)；child.parent=791 ✓

- L5 真实见证：`791` kind=commit outcome=errant_commit oracle_diff=—

### fault 133

主链每一条边均验证为直接 parent：

- `792` (fault_applied) → `793` (carrier_state)；child.parent=792 ✓
- `793` (carrier_state) → `794` (operand_read)；child.parent=793 ✓
- `794` (operand_read) → `795` (execute)；child.parent=794 ✓
- `795` (execute) → `796` (prf_writeback)；child.parent=795 ✓
- `796` (prf_writeback) → `797` (commit)；child.parent=796 ✓
- `797` (commit) → `1344` (chain_end)；child.parent=797 ✓

- L5 真实见证：`797` kind=commit outcome=errant_commit oracle_diff=—

### fault 134

主链每一条边均验证为直接 parent：

- `798` (fault_applied) → `799` (carrier_state)；child.parent=798 ✓
- `799` (carrier_state) → `800` (operand_read)；child.parent=799 ✓
- `800` (operand_read) → `801` (execute)；child.parent=800 ✓
- `801` (execute) → `802` (prf_writeback)；child.parent=801 ✓
- `802` (prf_writeback) → `803` (commit)；child.parent=802 ✓
- `803` (commit) → `1345` (chain_end)；child.parent=803 ✓

- L5 真实见证：`803` kind=commit outcome=errant_commit oracle_diff=—

### fault 135

主链每一条边均验证为直接 parent：

- `804` (fault_applied) → `805` (carrier_state)；child.parent=804 ✓
- `805` (carrier_state) → `806` (operand_read)；child.parent=805 ✓
- `806` (operand_read) → `807` (execute)；child.parent=806 ✓
- `807` (execute) → `808` (prf_writeback)；child.parent=807 ✓
- `808` (prf_writeback) → `809` (commit)；child.parent=808 ✓
- `809` (commit) → `1346` (chain_end)；child.parent=809 ✓

- L5 真实见证：`809` kind=commit outcome=errant_commit oracle_diff=—

### fault 136

主链每一条边均验证为直接 parent：

- `810` (fault_applied) → `811` (carrier_state)；child.parent=810 ✓
- `811` (carrier_state) → `812` (operand_read)；child.parent=811 ✓
- `812` (operand_read) → `813` (execute)；child.parent=812 ✓
- `813` (execute) → `814` (prf_writeback)；child.parent=813 ✓
- `814` (prf_writeback) → `815` (commit)；child.parent=814 ✓
- `815` (commit) → `1347` (chain_end)；child.parent=815 ✓

- L5 真实见证：`815` kind=commit outcome=errant_commit oracle_diff=—

### fault 137

主链每一条边均验证为直接 parent：

- `816` (fault_applied) → `817` (carrier_state)；child.parent=816 ✓
- `817` (carrier_state) → `818` (operand_read)；child.parent=817 ✓
- `818` (operand_read) → `819` (execute)；child.parent=818 ✓
- `819` (execute) → `820` (prf_writeback)；child.parent=819 ✓
- `820` (prf_writeback) → `821` (commit)；child.parent=820 ✓
- `821` (commit) → `1348` (chain_end)；child.parent=821 ✓

- L5 真实见证：`821` kind=commit outcome=errant_commit oracle_diff=—

### fault 138

主链每一条边均验证为直接 parent：

- `822` (fault_applied) → `823` (carrier_state)；child.parent=822 ✓
- `823` (carrier_state) → `824` (operand_read)；child.parent=823 ✓
- `824` (operand_read) → `825` (execute)；child.parent=824 ✓
- `825` (execute) → `826` (prf_writeback)；child.parent=825 ✓
- `826` (prf_writeback) → `827` (commit)；child.parent=826 ✓
- `827` (commit) → `1349` (chain_end)；child.parent=827 ✓

- L5 真实见证：`827` kind=commit outcome=errant_commit oracle_diff=—

### fault 139

主链每一条边均验证为直接 parent：

- `828` (fault_applied) → `829` (carrier_state)；child.parent=828 ✓
- `829` (carrier_state) → `830` (operand_read)；child.parent=829 ✓
- `830` (operand_read) → `831` (execute)；child.parent=830 ✓
- `831` (execute) → `832` (prf_writeback)；child.parent=831 ✓
- `832` (prf_writeback) → `833` (commit)；child.parent=832 ✓
- `833` (commit) → `1350` (chain_end)；child.parent=833 ✓

- L5 真实见证：`833` kind=commit outcome=errant_commit oracle_diff=—

### fault 14

主链每一条边均验证为直接 parent：

- `78` (fault_applied) → `79` (carrier_state)；child.parent=78 ✓
- `79` (carrier_state) → `80` (operand_read)；child.parent=79 ✓
- `80` (operand_read) → `81` (execute)；child.parent=80 ✓
- `81` (execute) → `82` (prf_writeback)；child.parent=81 ✓
- `82` (prf_writeback) → `83` (commit)；child.parent=82 ✓
- `83` (commit) → `1225` (chain_end)；child.parent=83 ✓

- L5 真实见证：`83` kind=commit outcome=errant_commit oracle_diff=—

### fault 140

主链每一条边均验证为直接 parent：

- `834` (fault_applied) → `835` (carrier_state)；child.parent=834 ✓
- `835` (carrier_state) → `836` (operand_read)；child.parent=835 ✓
- `836` (operand_read) → `837` (execute)；child.parent=836 ✓
- `837` (execute) → `838` (prf_writeback)；child.parent=837 ✓
- `838` (prf_writeback) → `839` (commit)；child.parent=838 ✓
- `839` (commit) → `1351` (chain_end)；child.parent=839 ✓

- L5 真实见证：`839` kind=commit outcome=errant_commit oracle_diff=—

### fault 141

主链每一条边均验证为直接 parent：

- `840` (fault_applied) → `841` (carrier_state)；child.parent=840 ✓
- `841` (carrier_state) → `842` (operand_read)；child.parent=841 ✓
- `842` (operand_read) → `843` (execute)；child.parent=842 ✓
- `843` (execute) → `844` (prf_writeback)；child.parent=843 ✓
- `844` (prf_writeback) → `845` (commit)；child.parent=844 ✓
- `845` (commit) → `1352` (chain_end)；child.parent=845 ✓

- L5 真实见证：`845` kind=commit outcome=errant_commit oracle_diff=—

### fault 142

主链每一条边均验证为直接 parent：

- `846` (fault_applied) → `847` (carrier_state)；child.parent=846 ✓
- `847` (carrier_state) → `848` (operand_read)；child.parent=847 ✓
- `848` (operand_read) → `849` (execute)；child.parent=848 ✓
- `849` (execute) → `850` (prf_writeback)；child.parent=849 ✓
- `850` (prf_writeback) → `851` (commit)；child.parent=850 ✓
- `851` (commit) → `1353` (chain_end)；child.parent=851 ✓

- L5 真实见证：`851` kind=commit outcome=errant_commit oracle_diff=—

### fault 143

主链每一条边均验证为直接 parent：

- `852` (fault_applied) → `853` (carrier_state)；child.parent=852 ✓
- `853` (carrier_state) → `854` (operand_read)；child.parent=853 ✓
- `854` (operand_read) → `855` (execute)；child.parent=854 ✓
- `855` (execute) → `856` (prf_writeback)；child.parent=855 ✓
- `856` (prf_writeback) → `857` (commit)；child.parent=856 ✓
- `857` (commit) → `1354` (chain_end)；child.parent=857 ✓

- L5 真实见证：`857` kind=commit outcome=errant_commit oracle_diff=—

### fault 144

主链每一条边均验证为直接 parent：

- `858` (fault_applied) → `859` (carrier_state)；child.parent=858 ✓
- `859` (carrier_state) → `860` (operand_read)；child.parent=859 ✓
- `860` (operand_read) → `861` (execute)；child.parent=860 ✓
- `861` (execute) → `862` (prf_writeback)；child.parent=861 ✓
- `862` (prf_writeback) → `863` (commit)；child.parent=862 ✓
- `863` (commit) → `1355` (chain_end)；child.parent=863 ✓

- L5 真实见证：`863` kind=commit outcome=errant_commit oracle_diff=—

### fault 145

主链每一条边均验证为直接 parent：

- `864` (fault_applied) → `865` (carrier_state)；child.parent=864 ✓
- `865` (carrier_state) → `866` (operand_read)；child.parent=865 ✓
- `866` (operand_read) → `867` (execute)；child.parent=866 ✓
- `867` (execute) → `868` (prf_writeback)；child.parent=867 ✓
- `868` (prf_writeback) → `869` (commit)；child.parent=868 ✓
- `869` (commit) → `1356` (chain_end)；child.parent=869 ✓

- L5 真实见证：`869` kind=commit outcome=errant_commit oracle_diff=—

### fault 146

主链每一条边均验证为直接 parent：

- `870` (fault_applied) → `871` (carrier_state)；child.parent=870 ✓
- `871` (carrier_state) → `872` (operand_read)；child.parent=871 ✓
- `872` (operand_read) → `873` (execute)；child.parent=872 ✓
- `873` (execute) → `874` (prf_writeback)；child.parent=873 ✓
- `874` (prf_writeback) → `875` (commit)；child.parent=874 ✓
- `875` (commit) → `1357` (chain_end)；child.parent=875 ✓

- L5 真实见证：`875` kind=commit outcome=errant_commit oracle_diff=—

### fault 147

主链每一条边均验证为直接 parent：

- `876` (fault_applied) → `877` (carrier_state)；child.parent=876 ✓
- `877` (carrier_state) → `878` (operand_read)；child.parent=877 ✓
- `878` (operand_read) → `879` (execute)；child.parent=878 ✓
- `879` (execute) → `880` (prf_writeback)；child.parent=879 ✓
- `880` (prf_writeback) → `881` (commit)；child.parent=880 ✓
- `881` (commit) → `1358` (chain_end)；child.parent=881 ✓

- L5 真实见证：`881` kind=commit outcome=errant_commit oracle_diff=—

### fault 148

主链每一条边均验证为直接 parent：

- `882` (fault_applied) → `883` (carrier_state)；child.parent=882 ✓
- `883` (carrier_state) → `884` (operand_read)；child.parent=883 ✓
- `884` (operand_read) → `885` (execute)；child.parent=884 ✓
- `885` (execute) → `886` (prf_writeback)；child.parent=885 ✓
- `886` (prf_writeback) → `887` (commit)；child.parent=886 ✓
- `887` (commit) → `1359` (chain_end)；child.parent=887 ✓

- L5 真实见证：`887` kind=commit outcome=errant_commit oracle_diff=—

### fault 149

主链每一条边均验证为直接 parent：

- `888` (fault_applied) → `889` (carrier_state)；child.parent=888 ✓
- `889` (carrier_state) → `890` (operand_read)；child.parent=889 ✓
- `890` (operand_read) → `891` (execute)；child.parent=890 ✓
- `891` (execute) → `892` (prf_writeback)；child.parent=891 ✓
- `892` (prf_writeback) → `893` (commit)；child.parent=892 ✓
- `893` (commit) → `1360` (chain_end)；child.parent=893 ✓

- L5 真实见证：`893` kind=commit outcome=errant_commit oracle_diff=—

### fault 15

主链每一条边均验证为直接 parent：

- `84` (fault_applied) → `85` (carrier_state)；child.parent=84 ✓
- `85` (carrier_state) → `86` (operand_read)；child.parent=85 ✓
- `86` (operand_read) → `87` (execute)；child.parent=86 ✓
- `87` (execute) → `88` (prf_writeback)；child.parent=87 ✓
- `88` (prf_writeback) → `89` (commit)；child.parent=88 ✓
- `89` (commit) → `1226` (chain_end)；child.parent=89 ✓

- L5 真实见证：`89` kind=commit outcome=errant_commit oracle_diff=—

### fault 150

主链每一条边均验证为直接 parent：

- `894` (fault_applied) → `895` (carrier_state)；child.parent=894 ✓
- `895` (carrier_state) → `896` (operand_read)；child.parent=895 ✓
- `896` (operand_read) → `897` (execute)；child.parent=896 ✓
- `897` (execute) → `898` (prf_writeback)；child.parent=897 ✓
- `898` (prf_writeback) → `899` (commit)；child.parent=898 ✓
- `899` (commit) → `1361` (chain_end)；child.parent=899 ✓

- L5 真实见证：`899` kind=commit outcome=errant_commit oracle_diff=—

### fault 151

主链每一条边均验证为直接 parent：

- `900` (fault_applied) → `901` (carrier_state)；child.parent=900 ✓
- `901` (carrier_state) → `902` (operand_read)；child.parent=901 ✓
- `902` (operand_read) → `903` (execute)；child.parent=902 ✓
- `903` (execute) → `904` (prf_writeback)；child.parent=903 ✓
- `904` (prf_writeback) → `905` (commit)；child.parent=904 ✓
- `905` (commit) → `1362` (chain_end)；child.parent=905 ✓

- L5 真实见证：`905` kind=commit outcome=errant_commit oracle_diff=—

### fault 152

主链每一条边均验证为直接 parent：

- `906` (fault_applied) → `907` (carrier_state)；child.parent=906 ✓
- `907` (carrier_state) → `908` (operand_read)；child.parent=907 ✓
- `908` (operand_read) → `909` (execute)；child.parent=908 ✓
- `909` (execute) → `910` (prf_writeback)；child.parent=909 ✓
- `910` (prf_writeback) → `911` (commit)；child.parent=910 ✓
- `911` (commit) → `1363` (chain_end)；child.parent=911 ✓

- L5 真实见证：`911` kind=commit outcome=errant_commit oracle_diff=—

### fault 153

主链每一条边均验证为直接 parent：

- `912` (fault_applied) → `913` (carrier_state)；child.parent=912 ✓
- `913` (carrier_state) → `914` (operand_read)；child.parent=913 ✓
- `914` (operand_read) → `915` (execute)；child.parent=914 ✓
- `915` (execute) → `916` (prf_writeback)；child.parent=915 ✓
- `916` (prf_writeback) → `917` (commit)；child.parent=916 ✓
- `917` (commit) → `1364` (chain_end)；child.parent=917 ✓

- L5 真实见证：`917` kind=commit outcome=errant_commit oracle_diff=—

### fault 154

主链每一条边均验证为直接 parent：

- `918` (fault_applied) → `919` (carrier_state)；child.parent=918 ✓
- `919` (carrier_state) → `920` (operand_read)；child.parent=919 ✓
- `920` (operand_read) → `921` (execute)；child.parent=920 ✓
- `921` (execute) → `922` (prf_writeback)；child.parent=921 ✓
- `922` (prf_writeback) → `923` (commit)；child.parent=922 ✓
- `923` (commit) → `1365` (chain_end)；child.parent=923 ✓

- L5 真实见证：`923` kind=commit outcome=errant_commit oracle_diff=—

### fault 155

主链每一条边均验证为直接 parent：

- `924` (fault_applied) → `925` (carrier_state)；child.parent=924 ✓
- `925` (carrier_state) → `926` (operand_read)；child.parent=925 ✓
- `926` (operand_read) → `927` (execute)；child.parent=926 ✓
- `927` (execute) → `928` (prf_writeback)；child.parent=927 ✓
- `928` (prf_writeback) → `929` (commit)；child.parent=928 ✓
- `929` (commit) → `1366` (chain_end)；child.parent=929 ✓

- L5 真实见证：`929` kind=commit outcome=errant_commit oracle_diff=—

### fault 156

主链每一条边均验证为直接 parent：

- `930` (fault_applied) → `931` (carrier_state)；child.parent=930 ✓
- `931` (carrier_state) → `932` (operand_read)；child.parent=931 ✓
- `932` (operand_read) → `933` (execute)；child.parent=932 ✓
- `933` (execute) → `934` (prf_writeback)；child.parent=933 ✓
- `934` (prf_writeback) → `935` (commit)；child.parent=934 ✓
- `935` (commit) → `1367` (chain_end)；child.parent=935 ✓

- L5 真实见证：`935` kind=commit outcome=errant_commit oracle_diff=—

### fault 157

主链每一条边均验证为直接 parent：

- `936` (fault_applied) → `937` (carrier_state)；child.parent=936 ✓
- `937` (carrier_state) → `938` (operand_read)；child.parent=937 ✓
- `938` (operand_read) → `939` (execute)；child.parent=938 ✓
- `939` (execute) → `940` (prf_writeback)；child.parent=939 ✓
- `940` (prf_writeback) → `941` (commit)；child.parent=940 ✓
- `941` (commit) → `1368` (chain_end)；child.parent=941 ✓

- L5 真实见证：`941` kind=commit outcome=errant_commit oracle_diff=—

### fault 158

主链每一条边均验证为直接 parent：

- `942` (fault_applied) → `943` (carrier_state)；child.parent=942 ✓
- `943` (carrier_state) → `944` (operand_read)；child.parent=943 ✓
- `944` (operand_read) → `945` (execute)；child.parent=944 ✓
- `945` (execute) → `946` (prf_writeback)；child.parent=945 ✓
- `946` (prf_writeback) → `947` (commit)；child.parent=946 ✓
- `947` (commit) → `1369` (chain_end)；child.parent=947 ✓

- L5 真实见证：`947` kind=commit outcome=errant_commit oracle_diff=—

### fault 159

主链每一条边均验证为直接 parent：

- `948` (fault_applied) → `949` (carrier_state)；child.parent=948 ✓
- `949` (carrier_state) → `950` (operand_read)；child.parent=949 ✓
- `950` (operand_read) → `951` (execute)；child.parent=950 ✓
- `951` (execute) → `952` (prf_writeback)；child.parent=951 ✓
- `952` (prf_writeback) → `953` (commit)；child.parent=952 ✓
- `953` (commit) → `1370` (chain_end)；child.parent=953 ✓

- L5 真实见证：`953` kind=commit outcome=errant_commit oracle_diff=—

### fault 16

主链每一条边均验证为直接 parent：

- `90` (fault_applied) → `91` (carrier_state)；child.parent=90 ✓
- `91` (carrier_state) → `92` (operand_read)；child.parent=91 ✓
- `92` (operand_read) → `93` (execute)；child.parent=92 ✓
- `93` (execute) → `94` (prf_writeback)；child.parent=93 ✓
- `94` (prf_writeback) → `95` (commit)；child.parent=94 ✓
- `95` (commit) → `1227` (chain_end)；child.parent=95 ✓

- L5 真实见证：`95` kind=commit outcome=errant_commit oracle_diff=—

### fault 160

主链每一条边均验证为直接 parent：

- `954` (fault_applied) → `955` (carrier_state)；child.parent=954 ✓
- `955` (carrier_state) → `956` (operand_read)；child.parent=955 ✓
- `956` (operand_read) → `957` (execute)；child.parent=956 ✓
- `957` (execute) → `958` (prf_writeback)；child.parent=957 ✓
- `958` (prf_writeback) → `959` (commit)；child.parent=958 ✓
- `959` (commit) → `1371` (chain_end)；child.parent=959 ✓

- L5 真实见证：`959` kind=commit outcome=errant_commit oracle_diff=—

### fault 161

主链每一条边均验证为直接 parent：

- `960` (fault_applied) → `961` (carrier_state)；child.parent=960 ✓
- `961` (carrier_state) → `962` (operand_read)；child.parent=961 ✓
- `962` (operand_read) → `963` (execute)；child.parent=962 ✓
- `963` (execute) → `964` (prf_writeback)；child.parent=963 ✓
- `964` (prf_writeback) → `965` (commit)；child.parent=964 ✓
- `965` (commit) → `1372` (chain_end)；child.parent=965 ✓

- L5 真实见证：`965` kind=commit outcome=errant_commit oracle_diff=—

### fault 162

主链每一条边均验证为直接 parent：

- `966` (fault_applied) → `967` (carrier_state)；child.parent=966 ✓
- `967` (carrier_state) → `968` (operand_read)；child.parent=967 ✓
- `968` (operand_read) → `969` (execute)；child.parent=968 ✓
- `969` (execute) → `970` (prf_writeback)；child.parent=969 ✓
- `970` (prf_writeback) → `971` (commit)；child.parent=970 ✓
- `971` (commit) → `1373` (chain_end)；child.parent=971 ✓

- L5 真实见证：`971` kind=commit outcome=errant_commit oracle_diff=—

### fault 163

主链每一条边均验证为直接 parent：

- `972` (fault_applied) → `973` (carrier_state)；child.parent=972 ✓
- `973` (carrier_state) → `974` (operand_read)；child.parent=973 ✓
- `974` (operand_read) → `975` (execute)；child.parent=974 ✓
- `975` (execute) → `976` (prf_writeback)；child.parent=975 ✓
- `976` (prf_writeback) → `977` (commit)；child.parent=976 ✓
- `977` (commit) → `1374` (chain_end)；child.parent=977 ✓

- L5 真实见证：`977` kind=commit outcome=errant_commit oracle_diff=—

### fault 164

主链每一条边均验证为直接 parent：

- `978` (fault_applied) → `979` (carrier_state)；child.parent=978 ✓
- `979` (carrier_state) → `980` (operand_read)；child.parent=979 ✓
- `980` (operand_read) → `981` (execute)；child.parent=980 ✓
- `981` (execute) → `982` (prf_writeback)；child.parent=981 ✓
- `982` (prf_writeback) → `983` (commit)；child.parent=982 ✓
- `983` (commit) → `1375` (chain_end)；child.parent=983 ✓

- L5 真实见证：`983` kind=commit outcome=errant_commit oracle_diff=—

### fault 165

主链每一条边均验证为直接 parent：

- `984` (fault_applied) → `985` (carrier_state)；child.parent=984 ✓
- `985` (carrier_state) → `986` (operand_read)；child.parent=985 ✓
- `986` (operand_read) → `987` (execute)；child.parent=986 ✓
- `987` (execute) → `988` (prf_writeback)；child.parent=987 ✓
- `988` (prf_writeback) → `989` (commit)；child.parent=988 ✓
- `989` (commit) → `1376` (chain_end)；child.parent=989 ✓

- L5 真实见证：`989` kind=commit outcome=errant_commit oracle_diff=—

### fault 166

主链每一条边均验证为直接 parent：

- `990` (fault_applied) → `991` (carrier_state)；child.parent=990 ✓
- `991` (carrier_state) → `992` (operand_read)；child.parent=991 ✓
- `992` (operand_read) → `993` (execute)；child.parent=992 ✓
- `993` (execute) → `994` (prf_writeback)；child.parent=993 ✓
- `994` (prf_writeback) → `995` (commit)；child.parent=994 ✓
- `995` (commit) → `1377` (chain_end)；child.parent=995 ✓

- L5 真实见证：`995` kind=commit outcome=errant_commit oracle_diff=—

### fault 167

主链每一条边均验证为直接 parent：

- `996` (fault_applied) → `997` (carrier_state)；child.parent=996 ✓
- `997` (carrier_state) → `998` (operand_read)；child.parent=997 ✓
- `998` (operand_read) → `999` (execute)；child.parent=998 ✓
- `999` (execute) → `1000` (prf_writeback)；child.parent=999 ✓
- `1000` (prf_writeback) → `1001` (commit)；child.parent=1000 ✓
- `1001` (commit) → `1378` (chain_end)；child.parent=1001 ✓

- L5 真实见证：`1001` kind=commit outcome=errant_commit oracle_diff=—

### fault 168

主链每一条边均验证为直接 parent：

- `1002` (fault_applied) → `1003` (carrier_state)；child.parent=1002 ✓
- `1003` (carrier_state) → `1004` (operand_read)；child.parent=1003 ✓
- `1004` (operand_read) → `1005` (execute)；child.parent=1004 ✓
- `1005` (execute) → `1006` (prf_writeback)；child.parent=1005 ✓
- `1006` (prf_writeback) → `1007` (commit)；child.parent=1006 ✓
- `1007` (commit) → `1379` (chain_end)；child.parent=1007 ✓

- L5 真实见证：`1007` kind=commit outcome=errant_commit oracle_diff=—

### fault 169

主链每一条边均验证为直接 parent：

- `1008` (fault_applied) → `1009` (carrier_state)；child.parent=1008 ✓
- `1009` (carrier_state) → `1010` (operand_read)；child.parent=1009 ✓
- `1010` (operand_read) → `1011` (execute)；child.parent=1010 ✓
- `1011` (execute) → `1012` (prf_writeback)；child.parent=1011 ✓
- `1012` (prf_writeback) → `1013` (commit)；child.parent=1012 ✓
- `1013` (commit) → `1380` (chain_end)；child.parent=1013 ✓

- L5 真实见证：`1013` kind=commit outcome=errant_commit oracle_diff=—

### fault 17

主链每一条边均验证为直接 parent：

- `96` (fault_applied) → `97` (carrier_state)；child.parent=96 ✓
- `97` (carrier_state) → `98` (operand_read)；child.parent=97 ✓
- `98` (operand_read) → `99` (execute)；child.parent=98 ✓
- `99` (execute) → `100` (prf_writeback)；child.parent=99 ✓
- `100` (prf_writeback) → `101` (commit)；child.parent=100 ✓
- `101` (commit) → `1228` (chain_end)；child.parent=101 ✓

- L5 真实见证：`101` kind=commit outcome=errant_commit oracle_diff=—

### fault 170

主链每一条边均验证为直接 parent：

- `1014` (fault_applied) → `1015` (carrier_state)；child.parent=1014 ✓
- `1015` (carrier_state) → `1016` (operand_read)；child.parent=1015 ✓
- `1016` (operand_read) → `1017` (execute)；child.parent=1016 ✓
- `1017` (execute) → `1018` (prf_writeback)；child.parent=1017 ✓
- `1018` (prf_writeback) → `1019` (commit)；child.parent=1018 ✓
- `1019` (commit) → `1381` (chain_end)；child.parent=1019 ✓

- L5 真实见证：`1019` kind=commit outcome=errant_commit oracle_diff=—

### fault 171

主链每一条边均验证为直接 parent：

- `1020` (fault_applied) → `1021` (carrier_state)；child.parent=1020 ✓
- `1021` (carrier_state) → `1022` (operand_read)；child.parent=1021 ✓
- `1022` (operand_read) → `1023` (execute)；child.parent=1022 ✓
- `1023` (execute) → `1024` (prf_writeback)；child.parent=1023 ✓
- `1024` (prf_writeback) → `1025` (commit)；child.parent=1024 ✓
- `1025` (commit) → `1382` (chain_end)；child.parent=1025 ✓

- L5 真实见证：`1025` kind=commit outcome=errant_commit oracle_diff=—

### fault 172

主链每一条边均验证为直接 parent：

- `1026` (fault_applied) → `1027` (carrier_state)；child.parent=1026 ✓
- `1027` (carrier_state) → `1028` (operand_read)；child.parent=1027 ✓
- `1028` (operand_read) → `1029` (execute)；child.parent=1028 ✓
- `1029` (execute) → `1030` (prf_writeback)；child.parent=1029 ✓
- `1030` (prf_writeback) → `1031` (commit)；child.parent=1030 ✓
- `1031` (commit) → `1383` (chain_end)；child.parent=1031 ✓

- L5 真实见证：`1031` kind=commit outcome=errant_commit oracle_diff=—

### fault 173

主链每一条边均验证为直接 parent：

- `1032` (fault_applied) → `1033` (carrier_state)；child.parent=1032 ✓
- `1033` (carrier_state) → `1034` (operand_read)；child.parent=1033 ✓
- `1034` (operand_read) → `1035` (execute)；child.parent=1034 ✓
- `1035` (execute) → `1036` (prf_writeback)；child.parent=1035 ✓
- `1036` (prf_writeback) → `1037` (commit)；child.parent=1036 ✓
- `1037` (commit) → `1384` (chain_end)；child.parent=1037 ✓

- L5 真实见证：`1037` kind=commit outcome=errant_commit oracle_diff=—

### fault 174

主链每一条边均验证为直接 parent：

- `1038` (fault_applied) → `1039` (carrier_state)；child.parent=1038 ✓
- `1039` (carrier_state) → `1040` (operand_read)；child.parent=1039 ✓
- `1040` (operand_read) → `1041` (execute)；child.parent=1040 ✓
- `1041` (execute) → `1042` (prf_writeback)；child.parent=1041 ✓
- `1042` (prf_writeback) → `1043` (commit)；child.parent=1042 ✓
- `1043` (commit) → `1385` (chain_end)；child.parent=1043 ✓

- L5 真实见证：`1043` kind=commit outcome=errant_commit oracle_diff=—

### fault 175

主链每一条边均验证为直接 parent：

- `1044` (fault_applied) → `1045` (carrier_state)；child.parent=1044 ✓
- `1045` (carrier_state) → `1046` (operand_read)；child.parent=1045 ✓
- `1046` (operand_read) → `1047` (execute)；child.parent=1046 ✓
- `1047` (execute) → `1048` (prf_writeback)；child.parent=1047 ✓
- `1048` (prf_writeback) → `1049` (commit)；child.parent=1048 ✓
- `1049` (commit) → `1386` (chain_end)；child.parent=1049 ✓

- L5 真实见证：`1049` kind=commit outcome=errant_commit oracle_diff=—

### fault 176

主链每一条边均验证为直接 parent：

- `1050` (fault_applied) → `1051` (carrier_state)；child.parent=1050 ✓
- `1051` (carrier_state) → `1052` (operand_read)；child.parent=1051 ✓
- `1052` (operand_read) → `1053` (execute)；child.parent=1052 ✓
- `1053` (execute) → `1054` (prf_writeback)；child.parent=1053 ✓
- `1054` (prf_writeback) → `1055` (commit)；child.parent=1054 ✓
- `1055` (commit) → `1387` (chain_end)；child.parent=1055 ✓

- L5 真实见证：`1055` kind=commit outcome=errant_commit oracle_diff=—

### fault 177

主链每一条边均验证为直接 parent：

- `1056` (fault_applied) → `1057` (carrier_state)；child.parent=1056 ✓
- `1057` (carrier_state) → `1058` (operand_read)；child.parent=1057 ✓
- `1058` (operand_read) → `1059` (execute)；child.parent=1058 ✓
- `1059` (execute) → `1060` (prf_writeback)；child.parent=1059 ✓
- `1060` (prf_writeback) → `1061` (commit)；child.parent=1060 ✓
- `1061` (commit) → `1388` (chain_end)；child.parent=1061 ✓

- L5 真实见证：`1061` kind=commit outcome=errant_commit oracle_diff=—

### fault 178

主链每一条边均验证为直接 parent：

- `1062` (fault_applied) → `1063` (carrier_state)；child.parent=1062 ✓
- `1063` (carrier_state) → `1064` (operand_read)；child.parent=1063 ✓
- `1064` (operand_read) → `1065` (execute)；child.parent=1064 ✓
- `1065` (execute) → `1066` (prf_writeback)；child.parent=1065 ✓
- `1066` (prf_writeback) → `1067` (commit)；child.parent=1066 ✓
- `1067` (commit) → `1389` (chain_end)；child.parent=1067 ✓

- L5 真实见证：`1067` kind=commit outcome=errant_commit oracle_diff=—

### fault 179

主链每一条边均验证为直接 parent：

- `1068` (fault_applied) → `1069` (carrier_state)；child.parent=1068 ✓
- `1069` (carrier_state) → `1070` (operand_read)；child.parent=1069 ✓
- `1070` (operand_read) → `1071` (execute)；child.parent=1070 ✓
- `1071` (execute) → `1072` (prf_writeback)；child.parent=1071 ✓
- `1072` (prf_writeback) → `1073` (commit)；child.parent=1072 ✓
- `1073` (commit) → `1390` (chain_end)；child.parent=1073 ✓

- L5 真实见证：`1073` kind=commit outcome=errant_commit oracle_diff=—

### fault 18

主链每一条边均验证为直接 parent：

- `102` (fault_applied) → `103` (carrier_state)；child.parent=102 ✓
- `103` (carrier_state) → `104` (operand_read)；child.parent=103 ✓
- `104` (operand_read) → `105` (execute)；child.parent=104 ✓
- `105` (execute) → `106` (prf_writeback)；child.parent=105 ✓
- `106` (prf_writeback) → `107` (commit)；child.parent=106 ✓
- `107` (commit) → `1229` (chain_end)；child.parent=107 ✓

- L5 真实见证：`107` kind=commit outcome=errant_commit oracle_diff=—

### fault 180

主链每一条边均验证为直接 parent：

- `1074` (fault_applied) → `1075` (carrier_state)；child.parent=1074 ✓
- `1075` (carrier_state) → `1076` (operand_read)；child.parent=1075 ✓
- `1076` (operand_read) → `1077` (execute)；child.parent=1076 ✓
- `1077` (execute) → `1078` (prf_writeback)；child.parent=1077 ✓
- `1078` (prf_writeback) → `1079` (commit)；child.parent=1078 ✓
- `1079` (commit) → `1391` (chain_end)；child.parent=1079 ✓

- L5 真实见证：`1079` kind=commit outcome=errant_commit oracle_diff=—

### fault 181

主链每一条边均验证为直接 parent：

- `1080` (fault_applied) → `1081` (carrier_state)；child.parent=1080 ✓
- `1081` (carrier_state) → `1082` (operand_read)；child.parent=1081 ✓
- `1082` (operand_read) → `1083` (execute)；child.parent=1082 ✓
- `1083` (execute) → `1084` (prf_writeback)；child.parent=1083 ✓
- `1084` (prf_writeback) → `1085` (commit)；child.parent=1084 ✓
- `1085` (commit) → `1392` (chain_end)；child.parent=1085 ✓

- L5 真实见证：`1085` kind=commit outcome=errant_commit oracle_diff=—

### fault 182

主链每一条边均验证为直接 parent：

- `1086` (fault_applied) → `1087` (carrier_state)；child.parent=1086 ✓
- `1087` (carrier_state) → `1088` (operand_read)；child.parent=1087 ✓
- `1088` (operand_read) → `1089` (execute)；child.parent=1088 ✓
- `1089` (execute) → `1090` (prf_writeback)；child.parent=1089 ✓
- `1090` (prf_writeback) → `1091` (commit)；child.parent=1090 ✓
- `1091` (commit) → `1393` (chain_end)；child.parent=1091 ✓

- L5 真实见证：`1091` kind=commit outcome=errant_commit oracle_diff=—

### fault 183

主链每一条边均验证为直接 parent：

- `1092` (fault_applied) → `1093` (carrier_state)；child.parent=1092 ✓
- `1093` (carrier_state) → `1094` (operand_read)；child.parent=1093 ✓
- `1094` (operand_read) → `1095` (execute)；child.parent=1094 ✓
- `1095` (execute) → `1096` (prf_writeback)；child.parent=1095 ✓
- `1096` (prf_writeback) → `1097` (commit)；child.parent=1096 ✓
- `1097` (commit) → `1394` (chain_end)；child.parent=1097 ✓

- L5 真实见证：`1097` kind=commit outcome=errant_commit oracle_diff=—

### fault 184

主链每一条边均验证为直接 parent：

- `1098` (fault_applied) → `1099` (carrier_state)；child.parent=1098 ✓
- `1099` (carrier_state) → `1100` (operand_read)；child.parent=1099 ✓
- `1100` (operand_read) → `1101` (execute)；child.parent=1100 ✓
- `1101` (execute) → `1102` (prf_writeback)；child.parent=1101 ✓
- `1102` (prf_writeback) → `1103` (commit)；child.parent=1102 ✓
- `1103` (commit) → `1395` (chain_end)；child.parent=1103 ✓

- L5 真实见证：`1103` kind=commit outcome=errant_commit oracle_diff=—

### fault 185

主链每一条边均验证为直接 parent：

- `1104` (fault_applied) → `1105` (carrier_state)；child.parent=1104 ✓
- `1105` (carrier_state) → `1106` (operand_read)；child.parent=1105 ✓
- `1106` (operand_read) → `1107` (execute)；child.parent=1106 ✓
- `1107` (execute) → `1108` (prf_writeback)；child.parent=1107 ✓
- `1108` (prf_writeback) → `1109` (commit)；child.parent=1108 ✓
- `1109` (commit) → `1396` (chain_end)；child.parent=1109 ✓

- L5 真实见证：`1109` kind=commit outcome=errant_commit oracle_diff=—

### fault 186

主链每一条边均验证为直接 parent：

- `1110` (fault_applied) → `1111` (carrier_state)；child.parent=1110 ✓
- `1111` (carrier_state) → `1112` (operand_read)；child.parent=1111 ✓
- `1112` (operand_read) → `1113` (execute)；child.parent=1112 ✓
- `1113` (execute) → `1114` (prf_writeback)；child.parent=1113 ✓
- `1114` (prf_writeback) → `1115` (commit)；child.parent=1114 ✓
- `1115` (commit) → `1397` (chain_end)；child.parent=1115 ✓

- L5 真实见证：`1115` kind=commit outcome=errant_commit oracle_diff=—

### fault 187

主链每一条边均验证为直接 parent：

- `1116` (fault_applied) → `1117` (carrier_state)；child.parent=1116 ✓
- `1117` (carrier_state) → `1118` (operand_read)；child.parent=1117 ✓
- `1118` (operand_read) → `1119` (execute)；child.parent=1118 ✓
- `1119` (execute) → `1120` (prf_writeback)；child.parent=1119 ✓
- `1120` (prf_writeback) → `1121` (commit)；child.parent=1120 ✓
- `1121` (commit) → `1398` (chain_end)；child.parent=1121 ✓

- L5 真实见证：`1121` kind=commit outcome=errant_commit oracle_diff=—

### fault 188

主链每一条边均验证为直接 parent：

- `1122` (fault_applied) → `1123` (carrier_state)；child.parent=1122 ✓
- `1123` (carrier_state) → `1124` (operand_read)；child.parent=1123 ✓
- `1124` (operand_read) → `1125` (execute)；child.parent=1124 ✓
- `1125` (execute) → `1126` (prf_writeback)；child.parent=1125 ✓
- `1126` (prf_writeback) → `1127` (commit)；child.parent=1126 ✓
- `1127` (commit) → `1399` (chain_end)；child.parent=1127 ✓

- L5 真实见证：`1127` kind=commit outcome=errant_commit oracle_diff=—

### fault 189

主链每一条边均验证为直接 parent：

- `1128` (fault_applied) → `1129` (carrier_state)；child.parent=1128 ✓
- `1129` (carrier_state) → `1130` (operand_read)；child.parent=1129 ✓
- `1130` (operand_read) → `1131` (execute)；child.parent=1130 ✓
- `1131` (execute) → `1132` (prf_writeback)；child.parent=1131 ✓
- `1132` (prf_writeback) → `1133` (commit)；child.parent=1132 ✓
- `1133` (commit) → `1400` (chain_end)；child.parent=1133 ✓

- L5 真实见证：`1133` kind=commit outcome=errant_commit oracle_diff=—

### fault 19

主链每一条边均验证为直接 parent：

- `108` (fault_applied) → `109` (carrier_state)；child.parent=108 ✓
- `109` (carrier_state) → `110` (operand_read)；child.parent=109 ✓
- `110` (operand_read) → `111` (execute)；child.parent=110 ✓
- `111` (execute) → `112` (prf_writeback)；child.parent=111 ✓
- `112` (prf_writeback) → `113` (commit)；child.parent=112 ✓
- `113` (commit) → `1230` (chain_end)；child.parent=113 ✓

- L5 真实见证：`113` kind=commit outcome=errant_commit oracle_diff=—

### fault 190

主链每一条边均验证为直接 parent：

- `1134` (fault_applied) → `1135` (carrier_state)；child.parent=1134 ✓
- `1135` (carrier_state) → `1136` (operand_read)；child.parent=1135 ✓
- `1136` (operand_read) → `1137` (execute)；child.parent=1136 ✓
- `1137` (execute) → `1138` (prf_writeback)；child.parent=1137 ✓
- `1138` (prf_writeback) → `1139` (commit)；child.parent=1138 ✓
- `1139` (commit) → `1401` (chain_end)；child.parent=1139 ✓

- L5 真实见证：`1139` kind=commit outcome=errant_commit oracle_diff=—

### fault 191

主链每一条边均验证为直接 parent：

- `1140` (fault_applied) → `1141` (carrier_state)；child.parent=1140 ✓
- `1141` (carrier_state) → `1142` (operand_read)；child.parent=1141 ✓
- `1142` (operand_read) → `1143` (execute)；child.parent=1142 ✓
- `1143` (execute) → `1144` (prf_writeback)；child.parent=1143 ✓
- `1144` (prf_writeback) → `1145` (commit)；child.parent=1144 ✓
- `1145` (commit) → `1402` (chain_end)；child.parent=1145 ✓

- L5 真实见证：`1145` kind=commit outcome=errant_commit oracle_diff=—

### fault 192

主链每一条边均验证为直接 parent：

- `1146` (fault_applied) → `1147` (carrier_state)；child.parent=1146 ✓
- `1147` (carrier_state) → `1148` (operand_read)；child.parent=1147 ✓
- `1148` (operand_read) → `1149` (execute)；child.parent=1148 ✓
- `1149` (execute) → `1150` (prf_writeback)；child.parent=1149 ✓
- `1150` (prf_writeback) → `1151` (commit)；child.parent=1150 ✓
- `1151` (commit) → `1403` (chain_end)；child.parent=1151 ✓

- L5 真实见证：`1151` kind=commit outcome=errant_commit oracle_diff=—

### fault 193

主链每一条边均验证为直接 parent：

- `1152` (fault_applied) → `1153` (carrier_state)；child.parent=1152 ✓
- `1153` (carrier_state) → `1154` (operand_read)；child.parent=1153 ✓
- `1154` (operand_read) → `1155` (execute)；child.parent=1154 ✓
- `1155` (execute) → `1156` (prf_writeback)；child.parent=1155 ✓
- `1156` (prf_writeback) → `1157` (commit)；child.parent=1156 ✓
- `1157` (commit) → `1404` (chain_end)；child.parent=1157 ✓

- L5 真实见证：`1157` kind=commit outcome=errant_commit oracle_diff=—

### fault 194

主链每一条边均验证为直接 parent：

- `1158` (fault_applied) → `1159` (carrier_state)；child.parent=1158 ✓
- `1159` (carrier_state) → `1160` (operand_read)；child.parent=1159 ✓
- `1160` (operand_read) → `1161` (execute)；child.parent=1160 ✓
- `1161` (execute) → `1162` (prf_writeback)；child.parent=1161 ✓
- `1162` (prf_writeback) → `1163` (commit)；child.parent=1162 ✓
- `1163` (commit) → `1405` (chain_end)；child.parent=1163 ✓

- L5 真实见证：`1163` kind=commit outcome=errant_commit oracle_diff=—

### fault 195

主链每一条边均验证为直接 parent：

- `1164` (fault_applied) → `1165` (carrier_state)；child.parent=1164 ✓
- `1165` (carrier_state) → `1166` (operand_read)；child.parent=1165 ✓
- `1166` (operand_read) → `1167` (execute)；child.parent=1166 ✓
- `1167` (execute) → `1168` (prf_writeback)；child.parent=1167 ✓
- `1168` (prf_writeback) → `1169` (commit)；child.parent=1168 ✓
- `1169` (commit) → `1406` (chain_end)；child.parent=1169 ✓

- L5 真实见证：`1169` kind=commit outcome=errant_commit oracle_diff=—

### fault 196

主链每一条边均验证为直接 parent：

- `1170` (fault_applied) → `1171` (carrier_state)；child.parent=1170 ✓
- `1171` (carrier_state) → `1172` (operand_read)；child.parent=1171 ✓
- `1172` (operand_read) → `1173` (execute)；child.parent=1172 ✓
- `1173` (execute) → `1174` (prf_writeback)；child.parent=1173 ✓
- `1174` (prf_writeback) → `1175` (commit)；child.parent=1174 ✓
- `1175` (commit) → `1407` (chain_end)；child.parent=1175 ✓

- L5 真实见证：`1175` kind=commit outcome=errant_commit oracle_diff=—

### fault 197

主链每一条边均验证为直接 parent：

- `1176` (fault_applied) → `1177` (carrier_state)；child.parent=1176 ✓
- `1177` (carrier_state) → `1178` (operand_read)；child.parent=1177 ✓
- `1178` (operand_read) → `1179` (execute)；child.parent=1178 ✓
- `1179` (execute) → `1180` (prf_writeback)；child.parent=1179 ✓
- `1180` (prf_writeback) → `1181` (commit)；child.parent=1180 ✓
- `1181` (commit) → `1408` (chain_end)；child.parent=1181 ✓

- L5 真实见证：`1181` kind=commit outcome=errant_commit oracle_diff=—

### fault 198

主链每一条边均验证为直接 parent：

- `1182` (fault_applied) → `1183` (carrier_state)；child.parent=1182 ✓
- `1183` (carrier_state) → `1184` (operand_read)；child.parent=1183 ✓
- `1184` (operand_read) → `1185` (execute)；child.parent=1184 ✓
- `1185` (execute) → `1186` (prf_writeback)；child.parent=1185 ✓
- `1186` (prf_writeback) → `1187` (commit)；child.parent=1186 ✓
- `1187` (commit) → `1409` (chain_end)；child.parent=1187 ✓

- L5 真实见证：`1187` kind=commit outcome=errant_commit oracle_diff=—

### fault 199

主链每一条边均验证为直接 parent：

- `1188` (fault_applied) → `1189` (carrier_state)；child.parent=1188 ✓
- `1189` (carrier_state) → `1190` (operand_read)；child.parent=1189 ✓
- `1190` (operand_read) → `1191` (execute)；child.parent=1190 ✓
- `1191` (execute) → `1192` (prf_writeback)；child.parent=1191 ✓
- `1192` (prf_writeback) → `1193` (commit)；child.parent=1192 ✓
- `1193` (commit) → `1410` (chain_end)；child.parent=1193 ✓

- L5 真实见证：`1193` kind=commit outcome=errant_commit oracle_diff=—

### fault 2

主链每一条边均验证为直接 parent：

- `6` (fault_applied) → `7` (carrier_state)；child.parent=6 ✓
- `7` (carrier_state) → `8` (operand_read)；child.parent=7 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `1213` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

### fault 20

主链每一条边均验证为直接 parent：

- `114` (fault_applied) → `115` (carrier_state)；child.parent=114 ✓
- `115` (carrier_state) → `116` (operand_read)；child.parent=115 ✓
- `116` (operand_read) → `117` (execute)；child.parent=116 ✓
- `117` (execute) → `118` (prf_writeback)；child.parent=117 ✓
- `118` (prf_writeback) → `119` (commit)；child.parent=118 ✓
- `119` (commit) → `1231` (chain_end)；child.parent=119 ✓

- L5 真实见证：`119` kind=commit outcome=errant_commit oracle_diff=—

### fault 200

主链每一条边均验证为直接 parent：

- `1194` (fault_applied) → `1195` (carrier_state)；child.parent=1194 ✓
- `1195` (carrier_state) → `1196` (operand_read)；child.parent=1195 ✓
- `1196` (operand_read) → `1197` (execute)；child.parent=1196 ✓
- `1197` (execute) → `1198` (prf_writeback)；child.parent=1197 ✓
- `1198` (prf_writeback) → `1199` (commit)；child.parent=1198 ✓
- `1199` (commit) → `1411` (chain_end)；child.parent=1199 ✓

- L5 真实见证：`1199` kind=commit outcome=errant_commit oracle_diff=—

### fault 201

主链每一条边均验证为直接 parent：

- `1200` (fault_applied) → `1201` (carrier_state)；child.parent=1200 ✓
- `1201` (carrier_state) → `1202` (operand_read)；child.parent=1201 ✓
- `1202` (operand_read) → `1203` (execute)；child.parent=1202 ✓
- `1203` (execute) → `1204` (prf_writeback)；child.parent=1203 ✓
- `1204` (prf_writeback) → `1205` (commit)；child.parent=1204 ✓
- `1205` (commit) → `1412` (chain_end)；child.parent=1205 ✓

- L5 真实见证：`1205` kind=commit outcome=errant_commit oracle_diff=—

### fault 202

主链每一条边均验证为直接 parent：

- `1206` (fault_applied) → `1207` (carrier_state)；child.parent=1206 ✓
- `1207` (carrier_state) → `1208` (operand_read)；child.parent=1207 ✓
- `1208` (operand_read) → `1209` (execute)；child.parent=1208 ✓
- `1209` (execute) → `1210` (prf_writeback)；child.parent=1209 ✓
- `1210` (prf_writeback) → `1211` (commit)；child.parent=1210 ✓
- `1211` (commit) → `1413` (chain_end)；child.parent=1211 ✓

- L5 真实见证：`1211` kind=commit outcome=errant_commit oracle_diff=—

### fault 21

主链每一条边均验证为直接 parent：

- `120` (fault_applied) → `121` (carrier_state)；child.parent=120 ✓
- `121` (carrier_state) → `122` (operand_read)；child.parent=121 ✓
- `122` (operand_read) → `123` (execute)；child.parent=122 ✓
- `123` (execute) → `124` (prf_writeback)；child.parent=123 ✓
- `124` (prf_writeback) → `125` (commit)；child.parent=124 ✓
- `125` (commit) → `1232` (chain_end)；child.parent=125 ✓

- L5 真实见证：`125` kind=commit outcome=errant_commit oracle_diff=—

### fault 22

主链每一条边均验证为直接 parent：

- `126` (fault_applied) → `127` (carrier_state)；child.parent=126 ✓
- `127` (carrier_state) → `128` (operand_read)；child.parent=127 ✓
- `128` (operand_read) → `129` (execute)；child.parent=128 ✓
- `129` (execute) → `130` (prf_writeback)；child.parent=129 ✓
- `130` (prf_writeback) → `131` (commit)；child.parent=130 ✓
- `131` (commit) → `1233` (chain_end)；child.parent=131 ✓

- L5 真实见证：`131` kind=commit outcome=errant_commit oracle_diff=—

### fault 23

主链每一条边均验证为直接 parent：

- `132` (fault_applied) → `133` (carrier_state)；child.parent=132 ✓
- `133` (carrier_state) → `134` (operand_read)；child.parent=133 ✓
- `134` (operand_read) → `135` (execute)；child.parent=134 ✓
- `135` (execute) → `136` (prf_writeback)；child.parent=135 ✓
- `136` (prf_writeback) → `137` (commit)；child.parent=136 ✓
- `137` (commit) → `1234` (chain_end)；child.parent=137 ✓

- L5 真实见证：`137` kind=commit outcome=errant_commit oracle_diff=—

### fault 24

主链每一条边均验证为直接 parent：

- `138` (fault_applied) → `139` (carrier_state)；child.parent=138 ✓
- `139` (carrier_state) → `140` (operand_read)；child.parent=139 ✓
- `140` (operand_read) → `141` (execute)；child.parent=140 ✓
- `141` (execute) → `142` (prf_writeback)；child.parent=141 ✓
- `142` (prf_writeback) → `143` (commit)；child.parent=142 ✓
- `143` (commit) → `1235` (chain_end)；child.parent=143 ✓

- L5 真实见证：`143` kind=commit outcome=errant_commit oracle_diff=—

### fault 25

主链每一条边均验证为直接 parent：

- `144` (fault_applied) → `145` (carrier_state)；child.parent=144 ✓
- `145` (carrier_state) → `146` (operand_read)；child.parent=145 ✓
- `146` (operand_read) → `147` (execute)；child.parent=146 ✓
- `147` (execute) → `148` (prf_writeback)；child.parent=147 ✓
- `148` (prf_writeback) → `149` (commit)；child.parent=148 ✓
- `149` (commit) → `1236` (chain_end)；child.parent=149 ✓

- L5 真实见证：`149` kind=commit outcome=errant_commit oracle_diff=—

### fault 26

主链每一条边均验证为直接 parent：

- `150` (fault_applied) → `151` (carrier_state)；child.parent=150 ✓
- `151` (carrier_state) → `152` (operand_read)；child.parent=151 ✓
- `152` (operand_read) → `153` (execute)；child.parent=152 ✓
- `153` (execute) → `154` (prf_writeback)；child.parent=153 ✓
- `154` (prf_writeback) → `155` (commit)；child.parent=154 ✓
- `155` (commit) → `1237` (chain_end)；child.parent=155 ✓

- L5 真实见证：`155` kind=commit outcome=errant_commit oracle_diff=—

### fault 27

主链每一条边均验证为直接 parent：

- `156` (fault_applied) → `157` (carrier_state)；child.parent=156 ✓
- `157` (carrier_state) → `158` (operand_read)；child.parent=157 ✓
- `158` (operand_read) → `159` (execute)；child.parent=158 ✓
- `159` (execute) → `160` (prf_writeback)；child.parent=159 ✓
- `160` (prf_writeback) → `161` (commit)；child.parent=160 ✓
- `161` (commit) → `1238` (chain_end)；child.parent=161 ✓

- L5 真实见证：`161` kind=commit outcome=errant_commit oracle_diff=—

### fault 28

主链每一条边均验证为直接 parent：

- `162` (fault_applied) → `163` (carrier_state)；child.parent=162 ✓
- `163` (carrier_state) → `164` (operand_read)；child.parent=163 ✓
- `164` (operand_read) → `165` (execute)；child.parent=164 ✓
- `165` (execute) → `166` (prf_writeback)；child.parent=165 ✓
- `166` (prf_writeback) → `167` (commit)；child.parent=166 ✓
- `167` (commit) → `1239` (chain_end)；child.parent=167 ✓

- L5 真实见证：`167` kind=commit outcome=errant_commit oracle_diff=—

### fault 29

主链每一条边均验证为直接 parent：

- `168` (fault_applied) → `169` (carrier_state)；child.parent=168 ✓
- `169` (carrier_state) → `170` (operand_read)；child.parent=169 ✓
- `170` (operand_read) → `171` (execute)；child.parent=170 ✓
- `171` (execute) → `172` (prf_writeback)；child.parent=171 ✓
- `172` (prf_writeback) → `173` (commit)；child.parent=172 ✓
- `173` (commit) → `1240` (chain_end)；child.parent=173 ✓

- L5 真实见证：`173` kind=commit outcome=errant_commit oracle_diff=—

### fault 3

主链每一条边均验证为直接 parent：

- `12` (fault_applied) → `13` (carrier_state)；child.parent=12 ✓
- `13` (carrier_state) → `14` (operand_read)；child.parent=13 ✓
- `14` (operand_read) → `15` (execute)；child.parent=14 ✓
- `15` (execute) → `16` (prf_writeback)；child.parent=15 ✓
- `16` (prf_writeback) → `17` (commit)；child.parent=16 ✓
- `17` (commit) → `1214` (chain_end)；child.parent=17 ✓

- L5 真实见证：`17` kind=commit outcome=errant_commit oracle_diff=—

### fault 30

主链每一条边均验证为直接 parent：

- `174` (fault_applied) → `175` (carrier_state)；child.parent=174 ✓
- `175` (carrier_state) → `176` (operand_read)；child.parent=175 ✓
- `176` (operand_read) → `177` (execute)；child.parent=176 ✓
- `177` (execute) → `178` (prf_writeback)；child.parent=177 ✓
- `178` (prf_writeback) → `179` (commit)；child.parent=178 ✓
- `179` (commit) → `1241` (chain_end)；child.parent=179 ✓

- L5 真实见证：`179` kind=commit outcome=errant_commit oracle_diff=—

### fault 31

主链每一条边均验证为直接 parent：

- `180` (fault_applied) → `181` (carrier_state)；child.parent=180 ✓
- `181` (carrier_state) → `182` (operand_read)；child.parent=181 ✓
- `182` (operand_read) → `183` (execute)；child.parent=182 ✓
- `183` (execute) → `184` (prf_writeback)；child.parent=183 ✓
- `184` (prf_writeback) → `185` (commit)；child.parent=184 ✓
- `185` (commit) → `1242` (chain_end)；child.parent=185 ✓

- L5 真实见证：`185` kind=commit outcome=errant_commit oracle_diff=—

### fault 32

主链每一条边均验证为直接 parent：

- `186` (fault_applied) → `187` (carrier_state)；child.parent=186 ✓
- `187` (carrier_state) → `188` (operand_read)；child.parent=187 ✓
- `188` (operand_read) → `189` (execute)；child.parent=188 ✓
- `189` (execute) → `190` (prf_writeback)；child.parent=189 ✓
- `190` (prf_writeback) → `191` (commit)；child.parent=190 ✓
- `191` (commit) → `1243` (chain_end)；child.parent=191 ✓

- L5 真实见证：`191` kind=commit outcome=errant_commit oracle_diff=—

### fault 33

主链每一条边均验证为直接 parent：

- `192` (fault_applied) → `193` (carrier_state)；child.parent=192 ✓
- `193` (carrier_state) → `194` (operand_read)；child.parent=193 ✓
- `194` (operand_read) → `195` (execute)；child.parent=194 ✓
- `195` (execute) → `196` (prf_writeback)；child.parent=195 ✓
- `196` (prf_writeback) → `197` (commit)；child.parent=196 ✓
- `197` (commit) → `1244` (chain_end)；child.parent=197 ✓

- L5 真实见证：`197` kind=commit outcome=errant_commit oracle_diff=—

### fault 34

主链每一条边均验证为直接 parent：

- `198` (fault_applied) → `199` (carrier_state)；child.parent=198 ✓
- `199` (carrier_state) → `200` (operand_read)；child.parent=199 ✓
- `200` (operand_read) → `201` (execute)；child.parent=200 ✓
- `201` (execute) → `202` (prf_writeback)；child.parent=201 ✓
- `202` (prf_writeback) → `203` (commit)；child.parent=202 ✓
- `203` (commit) → `1245` (chain_end)；child.parent=203 ✓

- L5 真实见证：`203` kind=commit outcome=errant_commit oracle_diff=—

### fault 35

主链每一条边均验证为直接 parent：

- `204` (fault_applied) → `205` (carrier_state)；child.parent=204 ✓
- `205` (carrier_state) → `206` (operand_read)；child.parent=205 ✓
- `206` (operand_read) → `207` (execute)；child.parent=206 ✓
- `207` (execute) → `208` (prf_writeback)；child.parent=207 ✓
- `208` (prf_writeback) → `209` (commit)；child.parent=208 ✓
- `209` (commit) → `1246` (chain_end)；child.parent=209 ✓

- L5 真实见证：`209` kind=commit outcome=errant_commit oracle_diff=—

### fault 36

主链每一条边均验证为直接 parent：

- `210` (fault_applied) → `211` (carrier_state)；child.parent=210 ✓
- `211` (carrier_state) → `212` (operand_read)；child.parent=211 ✓
- `212` (operand_read) → `213` (execute)；child.parent=212 ✓
- `213` (execute) → `214` (prf_writeback)；child.parent=213 ✓
- `214` (prf_writeback) → `215` (commit)；child.parent=214 ✓
- `215` (commit) → `1247` (chain_end)；child.parent=215 ✓

- L5 真实见证：`215` kind=commit outcome=errant_commit oracle_diff=—

### fault 37

主链每一条边均验证为直接 parent：

- `216` (fault_applied) → `217` (carrier_state)；child.parent=216 ✓
- `217` (carrier_state) → `218` (operand_read)；child.parent=217 ✓
- `218` (operand_read) → `219` (execute)；child.parent=218 ✓
- `219` (execute) → `220` (prf_writeback)；child.parent=219 ✓
- `220` (prf_writeback) → `221` (commit)；child.parent=220 ✓
- `221` (commit) → `1248` (chain_end)；child.parent=221 ✓

- L5 真实见证：`221` kind=commit outcome=errant_commit oracle_diff=—

### fault 38

主链每一条边均验证为直接 parent：

- `222` (fault_applied) → `223` (carrier_state)；child.parent=222 ✓
- `223` (carrier_state) → `224` (operand_read)；child.parent=223 ✓
- `224` (operand_read) → `225` (execute)；child.parent=224 ✓
- `225` (execute) → `226` (prf_writeback)；child.parent=225 ✓
- `226` (prf_writeback) → `227` (commit)；child.parent=226 ✓
- `227` (commit) → `1249` (chain_end)；child.parent=227 ✓

- L5 真实见证：`227` kind=commit outcome=errant_commit oracle_diff=—

### fault 39

主链每一条边均验证为直接 parent：

- `228` (fault_applied) → `229` (carrier_state)；child.parent=228 ✓
- `229` (carrier_state) → `230` (operand_read)；child.parent=229 ✓
- `230` (operand_read) → `231` (execute)；child.parent=230 ✓
- `231` (execute) → `232` (prf_writeback)；child.parent=231 ✓
- `232` (prf_writeback) → `233` (commit)；child.parent=232 ✓
- `233` (commit) → `1250` (chain_end)；child.parent=233 ✓

- L5 真实见证：`233` kind=commit outcome=errant_commit oracle_diff=—

### fault 4

主链每一条边均验证为直接 parent：

- `18` (fault_applied) → `19` (carrier_state)；child.parent=18 ✓
- `19` (carrier_state) → `20` (operand_read)；child.parent=19 ✓
- `20` (operand_read) → `21` (execute)；child.parent=20 ✓
- `21` (execute) → `22` (prf_writeback)；child.parent=21 ✓
- `22` (prf_writeback) → `23` (commit)；child.parent=22 ✓
- `23` (commit) → `1215` (chain_end)；child.parent=23 ✓

- L5 真实见证：`23` kind=commit outcome=errant_commit oracle_diff=—

### fault 40

主链每一条边均验证为直接 parent：

- `234` (fault_applied) → `235` (carrier_state)；child.parent=234 ✓
- `235` (carrier_state) → `236` (operand_read)；child.parent=235 ✓
- `236` (operand_read) → `237` (execute)；child.parent=236 ✓
- `237` (execute) → `238` (prf_writeback)；child.parent=237 ✓
- `238` (prf_writeback) → `239` (commit)；child.parent=238 ✓
- `239` (commit) → `1251` (chain_end)；child.parent=239 ✓

- L5 真实见证：`239` kind=commit outcome=errant_commit oracle_diff=—

### fault 41

主链每一条边均验证为直接 parent：

- `240` (fault_applied) → `241` (carrier_state)；child.parent=240 ✓
- `241` (carrier_state) → `242` (operand_read)；child.parent=241 ✓
- `242` (operand_read) → `243` (execute)；child.parent=242 ✓
- `243` (execute) → `244` (prf_writeback)；child.parent=243 ✓
- `244` (prf_writeback) → `245` (commit)；child.parent=244 ✓
- `245` (commit) → `1252` (chain_end)；child.parent=245 ✓

- L5 真实见证：`245` kind=commit outcome=errant_commit oracle_diff=—

### fault 42

主链每一条边均验证为直接 parent：

- `246` (fault_applied) → `247` (carrier_state)；child.parent=246 ✓
- `247` (carrier_state) → `248` (operand_read)；child.parent=247 ✓
- `248` (operand_read) → `249` (execute)；child.parent=248 ✓
- `249` (execute) → `250` (prf_writeback)；child.parent=249 ✓
- `250` (prf_writeback) → `251` (commit)；child.parent=250 ✓
- `251` (commit) → `1253` (chain_end)；child.parent=251 ✓

- L5 真实见证：`251` kind=commit outcome=errant_commit oracle_diff=—

### fault 43

主链每一条边均验证为直接 parent：

- `252` (fault_applied) → `253` (carrier_state)；child.parent=252 ✓
- `253` (carrier_state) → `254` (operand_read)；child.parent=253 ✓
- `254` (operand_read) → `255` (execute)；child.parent=254 ✓
- `255` (execute) → `256` (prf_writeback)；child.parent=255 ✓
- `256` (prf_writeback) → `257` (commit)；child.parent=256 ✓
- `257` (commit) → `1254` (chain_end)；child.parent=257 ✓

- L5 真实见证：`257` kind=commit outcome=errant_commit oracle_diff=—

### fault 44

主链每一条边均验证为直接 parent：

- `258` (fault_applied) → `259` (carrier_state)；child.parent=258 ✓
- `259` (carrier_state) → `260` (operand_read)；child.parent=259 ✓
- `260` (operand_read) → `261` (execute)；child.parent=260 ✓
- `261` (execute) → `262` (prf_writeback)；child.parent=261 ✓
- `262` (prf_writeback) → `263` (commit)；child.parent=262 ✓
- `263` (commit) → `1255` (chain_end)；child.parent=263 ✓

- L5 真实见证：`263` kind=commit outcome=errant_commit oracle_diff=—

### fault 45

主链每一条边均验证为直接 parent：

- `264` (fault_applied) → `265` (carrier_state)；child.parent=264 ✓
- `265` (carrier_state) → `266` (operand_read)；child.parent=265 ✓
- `266` (operand_read) → `267` (execute)；child.parent=266 ✓
- `267` (execute) → `268` (prf_writeback)；child.parent=267 ✓
- `268` (prf_writeback) → `269` (commit)；child.parent=268 ✓
- `269` (commit) → `1256` (chain_end)；child.parent=269 ✓

- L5 真实见证：`269` kind=commit outcome=errant_commit oracle_diff=—

### fault 46

主链每一条边均验证为直接 parent：

- `270` (fault_applied) → `271` (carrier_state)；child.parent=270 ✓
- `271` (carrier_state) → `272` (operand_read)；child.parent=271 ✓
- `272` (operand_read) → `273` (execute)；child.parent=272 ✓
- `273` (execute) → `274` (prf_writeback)；child.parent=273 ✓
- `274` (prf_writeback) → `275` (commit)；child.parent=274 ✓
- `275` (commit) → `1257` (chain_end)；child.parent=275 ✓

- L5 真实见证：`275` kind=commit outcome=errant_commit oracle_diff=—

### fault 47

主链每一条边均验证为直接 parent：

- `276` (fault_applied) → `277` (carrier_state)；child.parent=276 ✓
- `277` (carrier_state) → `278` (operand_read)；child.parent=277 ✓
- `278` (operand_read) → `279` (execute)；child.parent=278 ✓
- `279` (execute) → `280` (prf_writeback)；child.parent=279 ✓
- `280` (prf_writeback) → `281` (commit)；child.parent=280 ✓
- `281` (commit) → `1258` (chain_end)；child.parent=281 ✓

- L5 真实见证：`281` kind=commit outcome=errant_commit oracle_diff=—

### fault 48

主链每一条边均验证为直接 parent：

- `282` (fault_applied) → `283` (carrier_state)；child.parent=282 ✓
- `283` (carrier_state) → `284` (operand_read)；child.parent=283 ✓
- `284` (operand_read) → `285` (execute)；child.parent=284 ✓
- `285` (execute) → `286` (prf_writeback)；child.parent=285 ✓
- `286` (prf_writeback) → `287` (commit)；child.parent=286 ✓
- `287` (commit) → `1259` (chain_end)；child.parent=287 ✓

- L5 真实见证：`287` kind=commit outcome=errant_commit oracle_diff=—

### fault 49

主链每一条边均验证为直接 parent：

- `288` (fault_applied) → `289` (carrier_state)；child.parent=288 ✓
- `289` (carrier_state) → `290` (operand_read)；child.parent=289 ✓
- `290` (operand_read) → `291` (execute)；child.parent=290 ✓
- `291` (execute) → `292` (prf_writeback)；child.parent=291 ✓
- `292` (prf_writeback) → `293` (commit)；child.parent=292 ✓
- `293` (commit) → `1260` (chain_end)；child.parent=293 ✓

- L5 真实见证：`293` kind=commit outcome=errant_commit oracle_diff=—

### fault 5

主链每一条边均验证为直接 parent：

- `24` (fault_applied) → `25` (carrier_state)；child.parent=24 ✓
- `25` (carrier_state) → `26` (operand_read)；child.parent=25 ✓
- `26` (operand_read) → `27` (execute)；child.parent=26 ✓
- `27` (execute) → `28` (prf_writeback)；child.parent=27 ✓
- `28` (prf_writeback) → `29` (commit)；child.parent=28 ✓
- `29` (commit) → `1216` (chain_end)；child.parent=29 ✓

- L5 真实见证：`29` kind=commit outcome=errant_commit oracle_diff=—

### fault 50

主链每一条边均验证为直接 parent：

- `294` (fault_applied) → `295` (carrier_state)；child.parent=294 ✓
- `295` (carrier_state) → `296` (operand_read)；child.parent=295 ✓
- `296` (operand_read) → `297` (execute)；child.parent=296 ✓
- `297` (execute) → `298` (prf_writeback)；child.parent=297 ✓
- `298` (prf_writeback) → `299` (commit)；child.parent=298 ✓
- `299` (commit) → `1261` (chain_end)；child.parent=299 ✓

- L5 真实见证：`299` kind=commit outcome=errant_commit oracle_diff=—

### fault 51

主链每一条边均验证为直接 parent：

- `300` (fault_applied) → `301` (carrier_state)；child.parent=300 ✓
- `301` (carrier_state) → `302` (operand_read)；child.parent=301 ✓
- `302` (operand_read) → `303` (execute)；child.parent=302 ✓
- `303` (execute) → `304` (prf_writeback)；child.parent=303 ✓
- `304` (prf_writeback) → `305` (commit)；child.parent=304 ✓
- `305` (commit) → `1262` (chain_end)；child.parent=305 ✓

- L5 真实见证：`305` kind=commit outcome=errant_commit oracle_diff=—

### fault 52

主链每一条边均验证为直接 parent：

- `306` (fault_applied) → `307` (carrier_state)；child.parent=306 ✓
- `307` (carrier_state) → `308` (operand_read)；child.parent=307 ✓
- `308` (operand_read) → `309` (execute)；child.parent=308 ✓
- `309` (execute) → `310` (prf_writeback)；child.parent=309 ✓
- `310` (prf_writeback) → `311` (commit)；child.parent=310 ✓
- `311` (commit) → `1263` (chain_end)；child.parent=311 ✓

- L5 真实见证：`311` kind=commit outcome=errant_commit oracle_diff=—

### fault 53

主链每一条边均验证为直接 parent：

- `312` (fault_applied) → `313` (carrier_state)；child.parent=312 ✓
- `313` (carrier_state) → `314` (operand_read)；child.parent=313 ✓
- `314` (operand_read) → `315` (execute)；child.parent=314 ✓
- `315` (execute) → `316` (prf_writeback)；child.parent=315 ✓
- `316` (prf_writeback) → `317` (commit)；child.parent=316 ✓
- `317` (commit) → `1264` (chain_end)；child.parent=317 ✓

- L5 真实见证：`317` kind=commit outcome=errant_commit oracle_diff=—

### fault 54

主链每一条边均验证为直接 parent：

- `318` (fault_applied) → `319` (carrier_state)；child.parent=318 ✓
- `319` (carrier_state) → `320` (operand_read)；child.parent=319 ✓
- `320` (operand_read) → `321` (execute)；child.parent=320 ✓
- `321` (execute) → `322` (prf_writeback)；child.parent=321 ✓
- `322` (prf_writeback) → `323` (commit)；child.parent=322 ✓
- `323` (commit) → `1265` (chain_end)；child.parent=323 ✓

- L5 真实见证：`323` kind=commit outcome=errant_commit oracle_diff=—

### fault 55

主链每一条边均验证为直接 parent：

- `324` (fault_applied) → `325` (carrier_state)；child.parent=324 ✓
- `325` (carrier_state) → `326` (operand_read)；child.parent=325 ✓
- `326` (operand_read) → `327` (execute)；child.parent=326 ✓
- `327` (execute) → `328` (prf_writeback)；child.parent=327 ✓
- `328` (prf_writeback) → `329` (commit)；child.parent=328 ✓
- `329` (commit) → `1266` (chain_end)；child.parent=329 ✓

- L5 真实见证：`329` kind=commit outcome=errant_commit oracle_diff=—

### fault 56

主链每一条边均验证为直接 parent：

- `330` (fault_applied) → `331` (carrier_state)；child.parent=330 ✓
- `331` (carrier_state) → `332` (operand_read)；child.parent=331 ✓
- `332` (operand_read) → `333` (execute)；child.parent=332 ✓
- `333` (execute) → `334` (prf_writeback)；child.parent=333 ✓
- `334` (prf_writeback) → `335` (commit)；child.parent=334 ✓
- `335` (commit) → `1267` (chain_end)；child.parent=335 ✓

- L5 真实见证：`335` kind=commit outcome=errant_commit oracle_diff=—

### fault 57

主链每一条边均验证为直接 parent：

- `336` (fault_applied) → `337` (carrier_state)；child.parent=336 ✓
- `337` (carrier_state) → `338` (operand_read)；child.parent=337 ✓
- `338` (operand_read) → `339` (execute)；child.parent=338 ✓
- `339` (execute) → `340` (prf_writeback)；child.parent=339 ✓
- `340` (prf_writeback) → `341` (commit)；child.parent=340 ✓
- `341` (commit) → `1268` (chain_end)；child.parent=341 ✓

- L5 真实见证：`341` kind=commit outcome=errant_commit oracle_diff=—

### fault 58

主链每一条边均验证为直接 parent：

- `342` (fault_applied) → `343` (carrier_state)；child.parent=342 ✓
- `343` (carrier_state) → `344` (operand_read)；child.parent=343 ✓
- `344` (operand_read) → `345` (execute)；child.parent=344 ✓
- `345` (execute) → `346` (prf_writeback)；child.parent=345 ✓
- `346` (prf_writeback) → `347` (commit)；child.parent=346 ✓
- `347` (commit) → `1269` (chain_end)；child.parent=347 ✓

- L5 真实见证：`347` kind=commit outcome=errant_commit oracle_diff=—

### fault 59

主链每一条边均验证为直接 parent：

- `348` (fault_applied) → `349` (carrier_state)；child.parent=348 ✓
- `349` (carrier_state) → `350` (operand_read)；child.parent=349 ✓
- `350` (operand_read) → `351` (execute)；child.parent=350 ✓
- `351` (execute) → `352` (prf_writeback)；child.parent=351 ✓
- `352` (prf_writeback) → `353` (commit)；child.parent=352 ✓
- `353` (commit) → `1270` (chain_end)；child.parent=353 ✓

- L5 真实见证：`353` kind=commit outcome=errant_commit oracle_diff=—

### fault 6

主链每一条边均验证为直接 parent：

- `30` (fault_applied) → `31` (carrier_state)；child.parent=30 ✓
- `31` (carrier_state) → `32` (operand_read)；child.parent=31 ✓
- `32` (operand_read) → `33` (execute)；child.parent=32 ✓
- `33` (execute) → `34` (prf_writeback)；child.parent=33 ✓
- `34` (prf_writeback) → `35` (commit)；child.parent=34 ✓
- `35` (commit) → `1217` (chain_end)；child.parent=35 ✓

- L5 真实见证：`35` kind=commit outcome=errant_commit oracle_diff=—

### fault 60

主链每一条边均验证为直接 parent：

- `354` (fault_applied) → `355` (carrier_state)；child.parent=354 ✓
- `355` (carrier_state) → `356` (operand_read)；child.parent=355 ✓
- `356` (operand_read) → `357` (execute)；child.parent=356 ✓
- `357` (execute) → `358` (prf_writeback)；child.parent=357 ✓
- `358` (prf_writeback) → `359` (commit)；child.parent=358 ✓
- `359` (commit) → `1271` (chain_end)；child.parent=359 ✓

- L5 真实见证：`359` kind=commit outcome=errant_commit oracle_diff=—

### fault 61

主链每一条边均验证为直接 parent：

- `360` (fault_applied) → `361` (carrier_state)；child.parent=360 ✓
- `361` (carrier_state) → `362` (operand_read)；child.parent=361 ✓
- `362` (operand_read) → `363` (execute)；child.parent=362 ✓
- `363` (execute) → `364` (prf_writeback)；child.parent=363 ✓
- `364` (prf_writeback) → `365` (commit)；child.parent=364 ✓
- `365` (commit) → `1272` (chain_end)；child.parent=365 ✓

- L5 真实见证：`365` kind=commit outcome=errant_commit oracle_diff=—

### fault 62

主链每一条边均验证为直接 parent：

- `366` (fault_applied) → `367` (carrier_state)；child.parent=366 ✓
- `367` (carrier_state) → `368` (operand_read)；child.parent=367 ✓
- `368` (operand_read) → `369` (execute)；child.parent=368 ✓
- `369` (execute) → `370` (prf_writeback)；child.parent=369 ✓
- `370` (prf_writeback) → `371` (commit)；child.parent=370 ✓
- `371` (commit) → `1273` (chain_end)；child.parent=371 ✓

- L5 真实见证：`371` kind=commit outcome=errant_commit oracle_diff=—

### fault 63

主链每一条边均验证为直接 parent：

- `372` (fault_applied) → `373` (carrier_state)；child.parent=372 ✓
- `373` (carrier_state) → `374` (operand_read)；child.parent=373 ✓
- `374` (operand_read) → `375` (execute)；child.parent=374 ✓
- `375` (execute) → `376` (prf_writeback)；child.parent=375 ✓
- `376` (prf_writeback) → `377` (commit)；child.parent=376 ✓
- `377` (commit) → `1274` (chain_end)；child.parent=377 ✓

- L5 真实见证：`377` kind=commit outcome=errant_commit oracle_diff=—

### fault 64

主链每一条边均验证为直接 parent：

- `378` (fault_applied) → `379` (carrier_state)；child.parent=378 ✓
- `379` (carrier_state) → `380` (operand_read)；child.parent=379 ✓
- `380` (operand_read) → `381` (execute)；child.parent=380 ✓
- `381` (execute) → `382` (prf_writeback)；child.parent=381 ✓
- `382` (prf_writeback) → `383` (commit)；child.parent=382 ✓
- `383` (commit) → `1275` (chain_end)；child.parent=383 ✓

- L5 真实见证：`383` kind=commit outcome=errant_commit oracle_diff=—

### fault 65

主链每一条边均验证为直接 parent：

- `384` (fault_applied) → `385` (carrier_state)；child.parent=384 ✓
- `385` (carrier_state) → `386` (operand_read)；child.parent=385 ✓
- `386` (operand_read) → `387` (execute)；child.parent=386 ✓
- `387` (execute) → `388` (prf_writeback)；child.parent=387 ✓
- `388` (prf_writeback) → `389` (commit)；child.parent=388 ✓
- `389` (commit) → `1276` (chain_end)；child.parent=389 ✓

- L5 真实见证：`389` kind=commit outcome=errant_commit oracle_diff=—

### fault 66

主链每一条边均验证为直接 parent：

- `390` (fault_applied) → `391` (carrier_state)；child.parent=390 ✓
- `391` (carrier_state) → `392` (operand_read)；child.parent=391 ✓
- `392` (operand_read) → `393` (execute)；child.parent=392 ✓
- `393` (execute) → `394` (prf_writeback)；child.parent=393 ✓
- `394` (prf_writeback) → `395` (commit)；child.parent=394 ✓
- `395` (commit) → `1277` (chain_end)；child.parent=395 ✓

- L5 真实见证：`395` kind=commit outcome=errant_commit oracle_diff=—

### fault 67

主链每一条边均验证为直接 parent：

- `396` (fault_applied) → `397` (carrier_state)；child.parent=396 ✓
- `397` (carrier_state) → `398` (operand_read)；child.parent=397 ✓
- `398` (operand_read) → `399` (execute)；child.parent=398 ✓
- `399` (execute) → `400` (prf_writeback)；child.parent=399 ✓
- `400` (prf_writeback) → `401` (commit)；child.parent=400 ✓
- `401` (commit) → `1278` (chain_end)；child.parent=401 ✓

- L5 真实见证：`401` kind=commit outcome=errant_commit oracle_diff=—

### fault 68

主链每一条边均验证为直接 parent：

- `402` (fault_applied) → `403` (carrier_state)；child.parent=402 ✓
- `403` (carrier_state) → `404` (operand_read)；child.parent=403 ✓
- `404` (operand_read) → `405` (execute)；child.parent=404 ✓
- `405` (execute) → `406` (prf_writeback)；child.parent=405 ✓
- `406` (prf_writeback) → `407` (commit)；child.parent=406 ✓
- `407` (commit) → `1279` (chain_end)；child.parent=407 ✓

- L5 真实见证：`407` kind=commit outcome=errant_commit oracle_diff=—

### fault 69

主链每一条边均验证为直接 parent：

- `408` (fault_applied) → `409` (carrier_state)；child.parent=408 ✓
- `409` (carrier_state) → `410` (operand_read)；child.parent=409 ✓
- `410` (operand_read) → `411` (execute)；child.parent=410 ✓
- `411` (execute) → `412` (prf_writeback)；child.parent=411 ✓
- `412` (prf_writeback) → `413` (commit)；child.parent=412 ✓
- `413` (commit) → `1280` (chain_end)；child.parent=413 ✓

- L5 真实见证：`413` kind=commit outcome=errant_commit oracle_diff=—

### fault 7

主链每一条边均验证为直接 parent：

- `36` (fault_applied) → `37` (carrier_state)；child.parent=36 ✓
- `37` (carrier_state) → `38` (operand_read)；child.parent=37 ✓
- `38` (operand_read) → `39` (execute)；child.parent=38 ✓
- `39` (execute) → `40` (prf_writeback)；child.parent=39 ✓
- `40` (prf_writeback) → `41` (commit)；child.parent=40 ✓
- `41` (commit) → `1218` (chain_end)；child.parent=41 ✓

- L5 真实见证：`41` kind=commit outcome=errant_commit oracle_diff=—

### fault 70

主链每一条边均验证为直接 parent：

- `414` (fault_applied) → `415` (carrier_state)；child.parent=414 ✓
- `415` (carrier_state) → `416` (operand_read)；child.parent=415 ✓
- `416` (operand_read) → `417` (execute)；child.parent=416 ✓
- `417` (execute) → `418` (prf_writeback)；child.parent=417 ✓
- `418` (prf_writeback) → `419` (commit)；child.parent=418 ✓
- `419` (commit) → `1281` (chain_end)；child.parent=419 ✓

- L5 真实见证：`419` kind=commit outcome=errant_commit oracle_diff=—

### fault 71

主链每一条边均验证为直接 parent：

- `420` (fault_applied) → `421` (carrier_state)；child.parent=420 ✓
- `421` (carrier_state) → `422` (operand_read)；child.parent=421 ✓
- `422` (operand_read) → `423` (execute)；child.parent=422 ✓
- `423` (execute) → `424` (prf_writeback)；child.parent=423 ✓
- `424` (prf_writeback) → `425` (commit)；child.parent=424 ✓
- `425` (commit) → `1282` (chain_end)；child.parent=425 ✓

- L5 真实见证：`425` kind=commit outcome=errant_commit oracle_diff=—

### fault 72

主链每一条边均验证为直接 parent：

- `426` (fault_applied) → `427` (carrier_state)；child.parent=426 ✓
- `427` (carrier_state) → `428` (operand_read)；child.parent=427 ✓
- `428` (operand_read) → `429` (execute)；child.parent=428 ✓
- `429` (execute) → `430` (prf_writeback)；child.parent=429 ✓
- `430` (prf_writeback) → `431` (commit)；child.parent=430 ✓
- `431` (commit) → `1283` (chain_end)；child.parent=431 ✓

- L5 真实见证：`431` kind=commit outcome=errant_commit oracle_diff=—

### fault 73

主链每一条边均验证为直接 parent：

- `432` (fault_applied) → `433` (carrier_state)；child.parent=432 ✓
- `433` (carrier_state) → `434` (operand_read)；child.parent=433 ✓
- `434` (operand_read) → `435` (execute)；child.parent=434 ✓
- `435` (execute) → `436` (prf_writeback)；child.parent=435 ✓
- `436` (prf_writeback) → `437` (commit)；child.parent=436 ✓
- `437` (commit) → `1284` (chain_end)；child.parent=437 ✓

- L5 真实见证：`437` kind=commit outcome=errant_commit oracle_diff=—

### fault 74

主链每一条边均验证为直接 parent：

- `438` (fault_applied) → `439` (carrier_state)；child.parent=438 ✓
- `439` (carrier_state) → `440` (operand_read)；child.parent=439 ✓
- `440` (operand_read) → `441` (execute)；child.parent=440 ✓
- `441` (execute) → `442` (prf_writeback)；child.parent=441 ✓
- `442` (prf_writeback) → `443` (commit)；child.parent=442 ✓
- `443` (commit) → `1285` (chain_end)；child.parent=443 ✓

- L5 真实见证：`443` kind=commit outcome=errant_commit oracle_diff=—

### fault 75

主链每一条边均验证为直接 parent：

- `444` (fault_applied) → `445` (carrier_state)；child.parent=444 ✓
- `445` (carrier_state) → `446` (operand_read)；child.parent=445 ✓
- `446` (operand_read) → `447` (execute)；child.parent=446 ✓
- `447` (execute) → `448` (prf_writeback)；child.parent=447 ✓
- `448` (prf_writeback) → `449` (commit)；child.parent=448 ✓
- `449` (commit) → `1286` (chain_end)；child.parent=449 ✓

- L5 真实见证：`449` kind=commit outcome=errant_commit oracle_diff=—

### fault 76

主链每一条边均验证为直接 parent：

- `450` (fault_applied) → `451` (carrier_state)；child.parent=450 ✓
- `451` (carrier_state) → `452` (operand_read)；child.parent=451 ✓
- `452` (operand_read) → `453` (execute)；child.parent=452 ✓
- `453` (execute) → `454` (prf_writeback)；child.parent=453 ✓
- `454` (prf_writeback) → `455` (commit)；child.parent=454 ✓
- `455` (commit) → `1287` (chain_end)；child.parent=455 ✓

- L5 真实见证：`455` kind=commit outcome=errant_commit oracle_diff=—

### fault 77

主链每一条边均验证为直接 parent：

- `456` (fault_applied) → `457` (carrier_state)；child.parent=456 ✓
- `457` (carrier_state) → `458` (operand_read)；child.parent=457 ✓
- `458` (operand_read) → `459` (execute)；child.parent=458 ✓
- `459` (execute) → `460` (prf_writeback)；child.parent=459 ✓
- `460` (prf_writeback) → `461` (commit)；child.parent=460 ✓
- `461` (commit) → `1288` (chain_end)；child.parent=461 ✓

- L5 真实见证：`461` kind=commit outcome=errant_commit oracle_diff=—

### fault 78

主链每一条边均验证为直接 parent：

- `462` (fault_applied) → `463` (carrier_state)；child.parent=462 ✓
- `463` (carrier_state) → `464` (operand_read)；child.parent=463 ✓
- `464` (operand_read) → `465` (execute)；child.parent=464 ✓
- `465` (execute) → `466` (prf_writeback)；child.parent=465 ✓
- `466` (prf_writeback) → `467` (commit)；child.parent=466 ✓
- `467` (commit) → `1289` (chain_end)；child.parent=467 ✓

- L5 真实见证：`467` kind=commit outcome=errant_commit oracle_diff=—

### fault 79

主链每一条边均验证为直接 parent：

- `468` (fault_applied) → `469` (carrier_state)；child.parent=468 ✓
- `469` (carrier_state) → `470` (operand_read)；child.parent=469 ✓
- `470` (operand_read) → `471` (execute)；child.parent=470 ✓
- `471` (execute) → `472` (prf_writeback)；child.parent=471 ✓
- `472` (prf_writeback) → `473` (commit)；child.parent=472 ✓
- `473` (commit) → `1290` (chain_end)；child.parent=473 ✓

- L5 真实见证：`473` kind=commit outcome=errant_commit oracle_diff=—

### fault 8

主链每一条边均验证为直接 parent：

- `42` (fault_applied) → `43` (carrier_state)；child.parent=42 ✓
- `43` (carrier_state) → `44` (operand_read)；child.parent=43 ✓
- `44` (operand_read) → `45` (execute)；child.parent=44 ✓
- `45` (execute) → `46` (prf_writeback)；child.parent=45 ✓
- `46` (prf_writeback) → `47` (commit)；child.parent=46 ✓
- `47` (commit) → `1219` (chain_end)；child.parent=47 ✓

- L5 真实见证：`47` kind=commit outcome=errant_commit oracle_diff=—

### fault 80

主链每一条边均验证为直接 parent：

- `474` (fault_applied) → `475` (carrier_state)；child.parent=474 ✓
- `475` (carrier_state) → `476` (operand_read)；child.parent=475 ✓
- `476` (operand_read) → `477` (execute)；child.parent=476 ✓
- `477` (execute) → `478` (prf_writeback)；child.parent=477 ✓
- `478` (prf_writeback) → `479` (commit)；child.parent=478 ✓
- `479` (commit) → `1291` (chain_end)；child.parent=479 ✓

- L5 真实见证：`479` kind=commit outcome=errant_commit oracle_diff=—

### fault 81

主链每一条边均验证为直接 parent：

- `480` (fault_applied) → `481` (carrier_state)；child.parent=480 ✓
- `481` (carrier_state) → `482` (operand_read)；child.parent=481 ✓
- `482` (operand_read) → `483` (execute)；child.parent=482 ✓
- `483` (execute) → `484` (prf_writeback)；child.parent=483 ✓
- `484` (prf_writeback) → `485` (commit)；child.parent=484 ✓
- `485` (commit) → `1292` (chain_end)；child.parent=485 ✓

- L5 真实见证：`485` kind=commit outcome=errant_commit oracle_diff=—

### fault 82

主链每一条边均验证为直接 parent：

- `486` (fault_applied) → `487` (carrier_state)；child.parent=486 ✓
- `487` (carrier_state) → `488` (operand_read)；child.parent=487 ✓
- `488` (operand_read) → `489` (execute)；child.parent=488 ✓
- `489` (execute) → `490` (prf_writeback)；child.parent=489 ✓
- `490` (prf_writeback) → `491` (commit)；child.parent=490 ✓
- `491` (commit) → `1293` (chain_end)；child.parent=491 ✓

- L5 真实见证：`491` kind=commit outcome=errant_commit oracle_diff=—

### fault 83

主链每一条边均验证为直接 parent：

- `492` (fault_applied) → `493` (carrier_state)；child.parent=492 ✓
- `493` (carrier_state) → `494` (operand_read)；child.parent=493 ✓
- `494` (operand_read) → `495` (execute)；child.parent=494 ✓
- `495` (execute) → `496` (prf_writeback)；child.parent=495 ✓
- `496` (prf_writeback) → `497` (commit)；child.parent=496 ✓
- `497` (commit) → `1294` (chain_end)；child.parent=497 ✓

- L5 真实见证：`497` kind=commit outcome=errant_commit oracle_diff=—

### fault 84

主链每一条边均验证为直接 parent：

- `498` (fault_applied) → `499` (carrier_state)；child.parent=498 ✓
- `499` (carrier_state) → `500` (operand_read)；child.parent=499 ✓
- `500` (operand_read) → `501` (execute)；child.parent=500 ✓
- `501` (execute) → `502` (prf_writeback)；child.parent=501 ✓
- `502` (prf_writeback) → `503` (commit)；child.parent=502 ✓
- `503` (commit) → `1295` (chain_end)；child.parent=503 ✓

- L5 真实见证：`503` kind=commit outcome=errant_commit oracle_diff=—

### fault 85

主链每一条边均验证为直接 parent：

- `504` (fault_applied) → `505` (carrier_state)；child.parent=504 ✓
- `505` (carrier_state) → `506` (operand_read)；child.parent=505 ✓
- `506` (operand_read) → `507` (execute)；child.parent=506 ✓
- `507` (execute) → `508` (prf_writeback)；child.parent=507 ✓
- `508` (prf_writeback) → `509` (commit)；child.parent=508 ✓
- `509` (commit) → `1296` (chain_end)；child.parent=509 ✓

- L5 真实见证：`509` kind=commit outcome=errant_commit oracle_diff=—

### fault 86

主链每一条边均验证为直接 parent：

- `510` (fault_applied) → `511` (carrier_state)；child.parent=510 ✓
- `511` (carrier_state) → `512` (operand_read)；child.parent=511 ✓
- `512` (operand_read) → `513` (execute)；child.parent=512 ✓
- `513` (execute) → `514` (prf_writeback)；child.parent=513 ✓
- `514` (prf_writeback) → `515` (commit)；child.parent=514 ✓
- `515` (commit) → `1297` (chain_end)；child.parent=515 ✓

- L5 真实见证：`515` kind=commit outcome=errant_commit oracle_diff=—

### fault 87

主链每一条边均验证为直接 parent：

- `516` (fault_applied) → `517` (carrier_state)；child.parent=516 ✓
- `517` (carrier_state) → `518` (operand_read)；child.parent=517 ✓
- `518` (operand_read) → `519` (execute)；child.parent=518 ✓
- `519` (execute) → `520` (prf_writeback)；child.parent=519 ✓
- `520` (prf_writeback) → `521` (commit)；child.parent=520 ✓
- `521` (commit) → `1298` (chain_end)；child.parent=521 ✓

- L5 真实见证：`521` kind=commit outcome=errant_commit oracle_diff=—

### fault 88

主链每一条边均验证为直接 parent：

- `522` (fault_applied) → `523` (carrier_state)；child.parent=522 ✓
- `523` (carrier_state) → `524` (operand_read)；child.parent=523 ✓
- `524` (operand_read) → `525` (execute)；child.parent=524 ✓
- `525` (execute) → `526` (prf_writeback)；child.parent=525 ✓
- `526` (prf_writeback) → `527` (commit)；child.parent=526 ✓
- `527` (commit) → `1299` (chain_end)；child.parent=527 ✓

- L5 真实见证：`527` kind=commit outcome=errant_commit oracle_diff=—

### fault 89

主链每一条边均验证为直接 parent：

- `528` (fault_applied) → `529` (carrier_state)；child.parent=528 ✓
- `529` (carrier_state) → `530` (operand_read)；child.parent=529 ✓
- `530` (operand_read) → `531` (execute)；child.parent=530 ✓
- `531` (execute) → `532` (prf_writeback)；child.parent=531 ✓
- `532` (prf_writeback) → `533` (commit)；child.parent=532 ✓
- `533` (commit) → `1300` (chain_end)；child.parent=533 ✓

- L5 真实见证：`533` kind=commit outcome=errant_commit oracle_diff=—

### fault 9

主链每一条边均验证为直接 parent：

- `48` (fault_applied) → `49` (carrier_state)；child.parent=48 ✓
- `49` (carrier_state) → `50` (operand_read)；child.parent=49 ✓
- `50` (operand_read) → `51` (execute)；child.parent=50 ✓
- `51` (execute) → `52` (prf_writeback)；child.parent=51 ✓
- `52` (prf_writeback) → `53` (commit)；child.parent=52 ✓
- `53` (commit) → `1220` (chain_end)；child.parent=53 ✓

- L5 真实见证：`53` kind=commit outcome=errant_commit oracle_diff=—

### fault 90

主链每一条边均验证为直接 parent：

- `534` (fault_applied) → `535` (carrier_state)；child.parent=534 ✓
- `535` (carrier_state) → `536` (operand_read)；child.parent=535 ✓
- `536` (operand_read) → `537` (execute)；child.parent=536 ✓
- `537` (execute) → `538` (prf_writeback)；child.parent=537 ✓
- `538` (prf_writeback) → `539` (commit)；child.parent=538 ✓
- `539` (commit) → `1301` (chain_end)；child.parent=539 ✓

- L5 真实见证：`539` kind=commit outcome=errant_commit oracle_diff=—

### fault 91

主链每一条边均验证为直接 parent：

- `540` (fault_applied) → `541` (carrier_state)；child.parent=540 ✓
- `541` (carrier_state) → `542` (operand_read)；child.parent=541 ✓
- `542` (operand_read) → `543` (execute)；child.parent=542 ✓
- `543` (execute) → `544` (prf_writeback)；child.parent=543 ✓
- `544` (prf_writeback) → `545` (commit)；child.parent=544 ✓
- `545` (commit) → `1302` (chain_end)；child.parent=545 ✓

- L5 真实见证：`545` kind=commit outcome=errant_commit oracle_diff=—

### fault 92

主链每一条边均验证为直接 parent：

- `546` (fault_applied) → `547` (carrier_state)；child.parent=546 ✓
- `547` (carrier_state) → `548` (operand_read)；child.parent=547 ✓
- `548` (operand_read) → `549` (execute)；child.parent=548 ✓
- `549` (execute) → `550` (prf_writeback)；child.parent=549 ✓
- `550` (prf_writeback) → `551` (commit)；child.parent=550 ✓
- `551` (commit) → `1303` (chain_end)；child.parent=551 ✓

- L5 真实见证：`551` kind=commit outcome=errant_commit oracle_diff=—

### fault 93

主链每一条边均验证为直接 parent：

- `552` (fault_applied) → `553` (carrier_state)；child.parent=552 ✓
- `553` (carrier_state) → `554` (operand_read)；child.parent=553 ✓
- `554` (operand_read) → `555` (execute)；child.parent=554 ✓
- `555` (execute) → `556` (prf_writeback)；child.parent=555 ✓
- `556` (prf_writeback) → `557` (commit)；child.parent=556 ✓
- `557` (commit) → `1304` (chain_end)；child.parent=557 ✓

- L5 真实见证：`557` kind=commit outcome=errant_commit oracle_diff=—

### fault 94

主链每一条边均验证为直接 parent：

- `558` (fault_applied) → `559` (carrier_state)；child.parent=558 ✓
- `559` (carrier_state) → `560` (operand_read)；child.parent=559 ✓
- `560` (operand_read) → `561` (execute)；child.parent=560 ✓
- `561` (execute) → `562` (prf_writeback)；child.parent=561 ✓
- `562` (prf_writeback) → `563` (commit)；child.parent=562 ✓
- `563` (commit) → `1305` (chain_end)；child.parent=563 ✓

- L5 真实见证：`563` kind=commit outcome=errant_commit oracle_diff=—

### fault 95

主链每一条边均验证为直接 parent：

- `564` (fault_applied) → `565` (carrier_state)；child.parent=564 ✓
- `565` (carrier_state) → `566` (operand_read)；child.parent=565 ✓
- `566` (operand_read) → `567` (execute)；child.parent=566 ✓
- `567` (execute) → `568` (prf_writeback)；child.parent=567 ✓
- `568` (prf_writeback) → `569` (commit)；child.parent=568 ✓
- `569` (commit) → `1306` (chain_end)；child.parent=569 ✓

- L5 真实见证：`569` kind=commit outcome=errant_commit oracle_diff=—

### fault 96

主链每一条边均验证为直接 parent：

- `570` (fault_applied) → `571` (carrier_state)；child.parent=570 ✓
- `571` (carrier_state) → `572` (operand_read)；child.parent=571 ✓
- `572` (operand_read) → `573` (execute)；child.parent=572 ✓
- `573` (execute) → `574` (prf_writeback)；child.parent=573 ✓
- `574` (prf_writeback) → `575` (commit)；child.parent=574 ✓
- `575` (commit) → `1307` (chain_end)；child.parent=575 ✓

- L5 真实见证：`575` kind=commit outcome=errant_commit oracle_diff=—

### fault 97

主链每一条边均验证为直接 parent：

- `576` (fault_applied) → `577` (carrier_state)；child.parent=576 ✓
- `577` (carrier_state) → `578` (operand_read)；child.parent=577 ✓
- `578` (operand_read) → `579` (execute)；child.parent=578 ✓
- `579` (execute) → `580` (prf_writeback)；child.parent=579 ✓
- `580` (prf_writeback) → `581` (commit)；child.parent=580 ✓
- `581` (commit) → `1308` (chain_end)；child.parent=581 ✓

- L5 真实见证：`581` kind=commit outcome=errant_commit oracle_diff=—

### fault 98

主链每一条边均验证为直接 parent：

- `582` (fault_applied) → `583` (carrier_state)；child.parent=582 ✓
- `583` (carrier_state) → `584` (operand_read)；child.parent=583 ✓
- `584` (operand_read) → `585` (execute)；child.parent=584 ✓
- `585` (execute) → `586` (prf_writeback)；child.parent=585 ✓
- `586` (prf_writeback) → `587` (commit)；child.parent=586 ✓
- `587` (commit) → `1309` (chain_end)；child.parent=587 ✓

- L5 真实见证：`587` kind=commit outcome=errant_commit oracle_diff=—

### fault 99

主链每一条边均验证为直接 parent：

- `588` (fault_applied) → `589` (carrier_state)；child.parent=588 ✓
- `589` (carrier_state) → `590` (operand_read)；child.parent=589 ✓
- `590` (operand_read) → `591` (execute)；child.parent=590 ✓
- `591` (execute) → `592` (prf_writeback)；child.parent=591 ✓
- `592` (prf_writeback) → `593` (commit)；child.parent=592 ✓
- `593` (commit) → `1310` (chain_end)；child.parent=593 ✓

- L5 真实见证：`593` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `f20a1c6d1df31d16e8ca26d9da1139fe81c397e10257d8875b66fdf59fa4e929` |
| `run.out` | `6a974df7be763fefddd35426dd26d52fe9bc275c586586cc433503c53137dfc1` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `6cc5cf348d0a246fdf7caf6252eb9841abb6913c30767dab8170801502774bb5` |
| `oracle.json` | `fb7d0123420ca60f2d357b9298636ed78cc090435935aef537ac5296d1f7d1bb` |
| `chain_report.json` | `f85eb7e72c6acdfc5faaa45ee81598ee7cdbf4899d43813fe312ca253c70835c` |
| `ordinals.json` | `8c317216bd3f6cb57a95091694427889adf7f00f83cd9b190c89429c97a9282d` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `ead48c08e2a0a1c0e01c2cbc793d2d0104ad86473d5eae60aa6724c183f563cd` |
| `inject/prop_evt.txt.gz` | `3ee6468bb3547df6b464099b2e00504ad1600aee4f9a737129f3f4314eeafc6c` |
| `inject/stats.txt` | `6cc5cf348d0a246fdf7caf6252eb9841abb6913c30767dab8170801502774bb5` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 202 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
