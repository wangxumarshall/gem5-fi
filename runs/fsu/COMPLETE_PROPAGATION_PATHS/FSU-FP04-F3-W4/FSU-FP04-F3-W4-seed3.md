# FSU-FP04-F3-W4 seed3 完整传播链

> 本文只使用本 seed（sample_run_id=`s3`）的原始证据自动生成；未观测字段写 N/A，缺事件写 Unknown，不跨 seed 复制。

## 1. 实验身份与复现信息

| 项 | 值 |
|---|---|
| RunID | `FSU-FP04-F3-W4` |
| 模型/子模型 | FP04 / FP04-c |
| 单元/频率/负载 | FSU Pipe / F3 / W4 |
| workload identity | W4-rate-v1 |
| seed / sample_run_id | 3 / `s3` |
| selection seed / injection seed | 3 / 3 |
| 实际 workload | `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1`（SHA-256 `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784`） |
| manifest | `runs/fsu/FSU-FP04-F3-W4/seed3/attempt-1/manifest.json` |
| gem5 二进制 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt`（SHA-256 `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c`） |
| 源码 HEAD | `3ee06a496531ffd39c4924aa182cb0114f6fcd27` |
| 分析工具 SHA-256 | `a9f7e2b00569a9dc3d2d104a245888624b5d2c51b637f72ab6cb1ee969b2fe76` |
| census 命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F3-W4/seed3/attempt-1/census /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 1 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 1 --fpu_fault_mask 0 --fpu_rng_seed 3 --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_count_only` |
| 注入命令 | `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt --quiet -d runs/fsu/FSU-FP04-F3-W4/seed3/attempt-1/inject /home/sdc/gem5-fi-fsu/configs/se/ooo_proxy.py --cmd /home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1 --cpu O3 --first_clock 0 --max_faults 210 --rng_seed 3 --chaos_fpu --fpu_first_clock 0 --fpu_max_faults 210 --fpu_fault_mask 0 --fpu_rng_seed 3 --fsu_model FP04 --fsu_freq F3 --fsu_load W4 --fsu_submodel FP04-c --fpu_bitseg mant_lo --fpu_events_to_skip 0 --fpu_rate_ordinals 5409,14633,21938,27464,38722,45247,51403,65272,77246,90282,95774,101792,108814,114196,125212,134939,149882,158467,168627,180613,189330,199232,213444,225835,240425,253212,265805,275226,281363,292598,302098,315053,320243,333496,340474,348574,358912,365098,379867,389769,397846,404833,410634,417907,430791,439487,449104,456492,471178,483282,489923,500748,510881,519818,533735,542683,556940,568664,578501,592188,598526,606757,615243,620589,628528,642701,653366,664935,677751,689763,696707,710366,716559,731176,736532,748239,760467,771247,778777,787442,800967,813363,825042,832129,839803,846633,856525,862974,870924,883654,892952,899031,905043,910303,920335,934718,941997,950847,964243,975993,983581,989081,994101,1002556,1015151,1022282,1033782,1043838,1049095,1061527,1076339,1084934,1099596,1112246,1118049,1131214,1142345,1157008,1168920,1178683,1186345,1194287,1208697,1221166,1233028,1240618,1253821,1267710,1273076,1279110,1285893,1300754,1310637,1320628,1328414,1340746,1347505,1361321,1371570,1382170,1391747,1402120,1410093,1416151,1427311,1439979,1450555,1457310,1466120,1480671,1492364,1505405,1518279,1532135,1538728,1544004,1554242,1565436,1578111,1589799,1598306,1607974,1618542,1623592,1629922,1643319,1652670,1661817,1667468,1679639,1684710,1696333,1707712,1718566,1727428,1740955,1752164,1760040,1769944,1781118,1794295,1799820,1806132,1812117,1821073,1827459,1832564,1846880,1859433,1873304,1883997,1892771,1902834,1910308,1917710,1931690,1937724,1947158,1955573,1961025,1975131,1989648,2002602,2016627,2026683,2036137,2049332,2063525,2078091,2088070 --fpu_rate_warmup 0 --fsu_rate_divisor 10000 --fsu_jitter_pct 50 --chaos_propagation --prop_run_id FSU-FP04-F3-W4 --prop_sample_run_id s3 --fsu_eligible_total 2097155` |
| rate（divisor/jitter/warmup） | 10000 / ±50% / 0 |
| eligible_total | 2097155 |
| ordinals（index: ordinal） | 0:5409, 1:14633, 2:21938, 3:27464, 4:38722, 5:45247, 6:51403, 7:65272, 8:77246, 9:90282, 10:95774, 11:101792, 12:108814, 13:114196, 14:125212, 15:134939, 16:149882, 17:158467, 18:168627, 19:180613, 20:189330, 21:199232, 22:213444, 23:225835, 24:240425, 25:253212, 26:265805, 27:275226, 28:281363, 29:292598, 30:302098, 31:315053, 32:320243, 33:333496, 34:340474, 35:348574, 36:358912, 37:365098, 38:379867, 39:389769, 40:397846, 41:404833, 42:410634, 43:417907, 44:430791, 45:439487, 46:449104, 47:456492, 48:471178, 49:483282, 50:489923, 51:500748, 52:510881, 53:519818, 54:533735, 55:542683, 56:556940, 57:568664, 58:578501, 59:592188, 60:598526, 61:606757, 62:615243, 63:620589, 64:628528, 65:642701, 66:653366, 67:664935, 68:677751, 69:689763, 70:696707, 71:710366, 72:716559, 73:731176, 74:736532, 75:748239, 76:760467, 77:771247, 78:778777, 79:787442, 80:800967, 81:813363, 82:825042, 83:832129, 84:839803, 85:846633, 86:856525, 87:862974, 88:870924, 89:883654, 90:892952, 91:899031, 92:905043, 93:910303, 94:920335, 95:934718, 96:941997, 97:950847, 98:964243, 99:975993, 100:983581, 101:989081, 102:994101, 103:1002556, 104:1015151, 105:1022282, 106:1033782, 107:1043838, 108:1049095, 109:1061527, 110:1076339, 111:1084934, 112:1099596, 113:1112246, 114:1118049, 115:1131214, 116:1142345, 117:1157008, 118:1168920, 119:1178683, 120:1186345, 121:1194287, 122:1208697, 123:1221166, 124:1233028, 125:1240618, 126:1253821, 127:1267710, 128:1273076, 129:1279110, 130:1285893, 131:1300754, 132:1310637, 133:1320628, 134:1328414, 135:1340746, 136:1347505, 137:1361321, 138:1371570, 139:1382170, 140:1391747, 141:1402120, 142:1410093, 143:1416151, 144:1427311, 145:1439979, 146:1450555, 147:1457310, 148:1466120, 149:1480671, 150:1492364, 151:1505405, 152:1518279, 153:1532135, 154:1538728, 155:1544004, 156:1554242, 157:1565436, 158:1578111, 159:1589799, 160:1598306, 161:1607974, 162:1618542, 163:1623592, 164:1629922, 165:1643319, 166:1652670, 167:1661817, 168:1667468, 169:1679639, 170:1684710, 171:1696333, 172:1707712, 173:1718566, 174:1727428, 175:1740955, 176:1752164, 177:1760040, 178:1769944, 179:1781118, 180:1794295, 181:1799820, 182:1806132, 183:1812117, 184:1821073, 185:1827459, 186:1832564, 187:1846880, 188:1859433, 189:1873304, 190:1883997, 191:1892771, 192:1902834, 193:1910308, 194:1917710, 195:1931690, 196:1937724, 197:1947158, 198:1955573, 199:1961025, 200:1975131, 201:1989648, 202:2002602, 203:2016627, 204:2026683, 205:2036137, 206:2049332, 207:2063525, 208:2078091, 209:2088070 |
| ordinals SHA-256 | `15d4a409c3d807aab196116acf1b7a7b027fc1959075d07b70db4bcb502d99ca` |
| 注入数（actual/expected） | 210 / 210 |
| fault 数（事件流/injection log） | 210 / 210 |

## 2. 故障注入发生在哪里

### fault 1

| 字段 | 值 |
|---|---|
| 根 event_id | `0` |
| tick / cycle | 21019460 / 54596 |
| sn / PC / opcode | 45327 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 5409 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5409 / 0 |
| terminal | full |

### fault 10

| 字段 | 值 |
|---|---|
| 根 event_id | `54` |
| tick / cycle | 149977520 / 389552 |
| sn / PC / opcode | 554581 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 90282 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13036 / 9 |
| terminal | full |

### fault 100

| 字段 | 值 |
|---|---|
| 根 event_id | `594` |
| tick / cycle | 1496905025 / 3888065 |
| sn / PC / opcode | 5868831 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 975993 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11750 / 99 |
| terminal | full |

### fault 101

| 字段 | 值 |
|---|---|
| 根 event_id | `600` |
| tick / cycle | 1508549350 / 3918310 |
| sn / PC / opcode | 5914370 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 983581 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7588 / 100 |
| terminal | full |

### fault 102

| 字段 | 值 |
|---|---|
| 根 event_id | `606` |
| tick / cycle | 1516796820 / 3939732 |
| sn / PC / opcode | 5947379 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 989081 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5500 / 101 |
| terminal | full |

### fault 103

| 字段 | 值 |
|---|---|
| 根 event_id | `612` |
| tick / cycle | 1524420975 / 3959535 |
| sn / PC / opcode | 5977479 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 994101 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5020 / 102 |
| terminal | full |

### fault 104

| 字段 | 值 |
|---|---|
| 根 event_id | `618` |
| tick / cycle | 1537380075 / 3993195 |
| sn / PC / opcode | 6028236 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1002556 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8455 / 103 |
| terminal | full |

### fault 105

| 字段 | 值 |
|---|---|
| 根 event_id | `624` |
| tick / cycle | 1556509570 / 4042882 |
| sn / PC / opcode | 6103799 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1015151 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12595 / 104 |
| terminal | full |

### fault 106

| 字段 | 值 |
|---|---|
| 根 event_id | `630` |
| tick / cycle | 1567278405 / 4070853 |
| sn / PC / opcode | 6146572 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1022282 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7131 / 105 |
| terminal | full |

### fault 107

| 字段 | 值 |
|---|---|
| 根 event_id | `636` |
| tick / cycle | 1584826320 / 4116432 |
| sn / PC / opcode | 6215581 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1033782 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11500 / 106 |
| terminal | full |

### fault 108

| 字段 | 值 |
|---|---|
| 根 event_id | `642` |
| tick / cycle | 1600132380 / 4156188 |
| sn / PC / opcode | 6275917 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1043838 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10056 / 107 |
| terminal | full |

### fault 109

| 字段 | 值 |
|---|---|
| 根 event_id | `648` |
| tick / cycle | 1608108040 / 4176904 |
| sn / PC / opcode | 6307454 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1049095 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5257 / 108 |
| terminal | full |

### fault 11

| 字段 | 值 |
|---|---|
| 根 event_id | `60` |
| tick / cycle | 158328555 / 411243 |
| sn / PC / opcode | 587524 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 95774 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5492 / 10 |
| terminal | full |

### fault 110

| 字段 | 值 |
|---|---|
| 根 event_id | `654` |
| tick / cycle | 1627036180 / 4226068 |
| sn / PC / opcode | 6382046 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1061527 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12432 / 109 |
| terminal | full |

### fault 111

| 字段 | 值 |
|---|---|
| 根 event_id | `660` |
| tick / cycle | 1649587170 / 4284642 |
| sn / PC / opcode | 6470927 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1076339 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14812 / 110 |
| terminal | full |

### fault 112

| 字段 | 值 |
|---|---|
| 根 event_id | `666` |
| tick / cycle | 1662645985 / 4318561 |
| sn / PC / opcode | 6522484 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1084934 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8595 / 111 |
| terminal | full |

### fault 113

| 字段 | 值 |
|---|---|
| 根 event_id | `672` |
| tick / cycle | 1684876655 / 4376303 |
| sn / PC / opcode | 6610465 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1099596 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14662 / 112 |
| terminal | full |

### fault 114

| 字段 | 值 |
|---|---|
| 根 event_id | `678` |
| tick / cycle | 1704207890 / 4426514 |
| sn / PC / opcode | 6686356 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1112246 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12650 / 113 |
| terminal | full |

### fault 115

| 字段 | 值 |
|---|---|
| 根 event_id | `684` |
| tick / cycle | 1712900035 / 4449091 |
| sn / PC / opcode | 6721167 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1118049 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5803 / 114 |
| terminal | full |

### fault 116

| 字段 | 值 |
|---|---|
| 根 event_id | `690` |
| tick / cycle | 1733020905 / 4501353 |
| sn / PC / opcode | 6800184 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1131214 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13165 / 115 |
| terminal | full |

### fault 117

| 字段 | 值 |
|---|---|
| 根 event_id | `696` |
| tick / cycle | 1749895840 / 4545184 |
| sn / PC / opcode | 6866963 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1142345 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11131 / 116 |
| terminal | full |

### fault 118

| 字段 | 值 |
|---|---|
| 根 event_id | `702` |
| tick / cycle | 1772224685 / 4603181 |
| sn / PC / opcode | 6954948 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1157008 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14663 / 117 |
| terminal | full |

### fault 119

| 字段 | 值 |
|---|---|
| 根 event_id | `708` |
| tick / cycle | 1790378590 / 4650334 |
| sn / PC / opcode | 7026409 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1168920 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11912 / 118 |
| terminal | full |

### fault 12

| 字段 | 值 |
|---|---|
| 根 event_id | `66` |
| tick / cycle | 167454980 / 434948 |
| sn / PC / opcode | 623632 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 101792 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6018 / 11 |
| terminal | full |

### fault 120

| 字段 | 值 |
|---|---|
| 根 event_id | `714` |
| tick / cycle | 1805161435 / 4688731 |
| sn / PC / opcode | 7084982 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1178683 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9763 / 119 |
| terminal | full |

### fault 121

| 字段 | 值 |
|---|---|
| 根 event_id | `720` |
| tick / cycle | 1816887380 / 4719188 |
| sn / PC / opcode | 7130954 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1186345 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7662 / 120 |
| terminal | full |

### fault 122

| 字段 | 值 |
|---|---|
| 根 event_id | `726` |
| tick / cycle | 1828854335 / 4750271 |
| sn / PC / opcode | 7178615 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1194287 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7942 / 121 |
| terminal | full |

### fault 123

| 字段 | 值 |
|---|---|
| 根 event_id | `732` |
| tick / cycle | 1850757755 / 4807163 |
| sn / PC / opcode | 7265055 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1208697 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14410 / 122 |
| terminal | full |

### fault 124

| 字段 | 值 |
|---|---|
| 根 event_id | `738` |
| tick / cycle | 1869780990 / 4856574 |
| sn / PC / opcode | 7339896 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1221166 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12469 / 123 |
| terminal | full |

### fault 125

| 字段 | 值 |
|---|---|
| 根 event_id | `744` |
| tick / cycle | 1887881765 / 4903589 |
| sn / PC / opcode | 7411068 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1233028 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11862 / 124 |
| terminal | full |

### fault 126

| 字段 | 值 |
|---|---|
| 根 event_id | `750` |
| tick / cycle | 1899328200 / 4933320 |
| sn / PC / opcode | 7456608 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1240618 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7590 / 125 |
| terminal | full |

### fault 127

| 字段 | 值 |
|---|---|
| 根 event_id | `756` |
| tick / cycle | 1919514520 / 4985752 |
| sn / PC / opcode | 7535810 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1253821 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13203 / 126 |
| terminal | full |

### fault 128

| 字段 | 值 |
|---|---|
| 根 event_id | `762` |
| tick / cycle | 1940527820 / 5040332 |
| sn / PC / opcode | 7619149 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1267710 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13889 / 127 |
| terminal | full |

### fault 129

| 字段 | 值 |
|---|---|
| 根 event_id | `768` |
| tick / cycle | 1948796080 / 5061808 |
| sn / PC / opcode | 7651336 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1273076 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5366 / 128 |
| terminal | full |

### fault 13

| 字段 | 值 |
|---|---|
| 根 event_id | `72` |
| tick / cycle | 178149510 / 462726 |
| sn / PC / opcode | 665784 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 108814 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7022 / 12 |
| terminal | full |

### fault 130

| 字段 | 值 |
|---|---|
| 根 event_id | `774` |
| tick / cycle | 1957945220 / 5085572 |
| sn / PC / opcode | 7687549 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1279110 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6034 / 129 |
| terminal | full |

### fault 131

| 字段 | 值 |
|---|---|
| 根 event_id | `780` |
| tick / cycle | 1968200080 / 5112208 |
| sn / PC / opcode | 7728231 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1285893 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6783 / 130 |
| terminal | full |

### fault 132

| 字段 | 值 |
|---|---|
| 根 event_id | `786` |
| tick / cycle | 1990798425 / 5170905 |
| sn / PC / opcode | 7817404 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1300754 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14861 / 131 |
| terminal | full |

### fault 133

| 字段 | 值 |
|---|---|
| 根 event_id | `792` |
| tick / cycle | 2005833830 / 5209958 |
| sn / PC / opcode | 7876695 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1310637 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9883 / 132 |
| terminal | full |

### fault 134

| 字段 | 值 |
|---|---|
| 根 event_id | `798` |
| tick / cycle | 2021030935 / 5249431 |
| sn / PC / opcode | 7936668 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1320628 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9991 / 133 |
| terminal | full |

### fault 135

| 字段 | 值 |
|---|---|
| 根 event_id | `804` |
| tick / cycle | 2032880465 / 5280209 |
| sn / PC / opcode | 7983364 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1328414 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7786 / 134 |
| terminal | full |

### fault 136

| 字段 | 值 |
|---|---|
| 根 event_id | `810` |
| tick / cycle | 2051661150 / 5328990 |
| sn / PC / opcode | 8057376 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1340746 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12332 / 135 |
| terminal | full |

### fault 137

| 字段 | 值 |
|---|---|
| 根 event_id | `816` |
| tick / cycle | 2061878665 / 5355529 |
| sn / PC / opcode | 8097914 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1347505 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6759 / 136 |
| terminal | full |

### fault 138

| 字段 | 值 |
|---|---|
| 根 event_id | `822` |
| tick / cycle | 2082995915 / 5410379 |
| sn / PC / opcode | 8180819 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1361321 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13816 / 137 |
| terminal | full |

### fault 139

| 字段 | 值 |
|---|---|
| 根 event_id | `828` |
| tick / cycle | 2098530665 / 5450729 |
| sn / PC / opcode | 8242309 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1371570 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10249 / 138 |
| terminal | full |

### fault 14

| 字段 | 值 |
|---|---|
| 根 event_id | `78` |
| tick / cycle | 186337305 / 483993 |
| sn / PC / opcode | 698076 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 114196 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5382 / 13 |
| terminal | full |

### fault 140

| 字段 | 值 |
|---|---|
| 根 event_id | `834` |
| tick / cycle | 2114647150 / 5492590 |
| sn / PC / opcode | 8305920 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1382170 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10600 / 139 |
| terminal | full |

### fault 141

| 字段 | 值 |
|---|---|
| 根 event_id | `840` |
| tick / cycle | 2129140090 / 5530234 |
| sn / PC / opcode | 8363375 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1391747 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9577 / 140 |
| terminal | full |

### fault 142

| 字段 | 值 |
|---|---|
| 根 event_id | `846` |
| tick / cycle | 2145002090 / 5571434 |
| sn / PC / opcode | 8425620 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1402120 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10373 / 141 |
| terminal | full |

### fault 143

| 字段 | 值 |
|---|---|
| 根 event_id | `852` |
| tick / cycle | 2157010625 / 5602625 |
| sn / PC / opcode | 8473431 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1410093 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7973 / 142 |
| terminal | full |

### fault 144

| 字段 | 值 |
|---|---|
| 根 event_id | `858` |
| tick / cycle | 2166261405 / 5626653 |
| sn / PC / opcode | 8509790 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1416151 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6058 / 143 |
| terminal | full |

### fault 145

| 字段 | 值 |
|---|---|
| 根 event_id | `864` |
| tick / cycle | 2183316135 / 5670951 |
| sn / PC / opcode | 8576750 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1427311 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11160 / 144 |
| terminal | full |

### fault 146

| 字段 | 值 |
|---|---|
| 根 event_id | `870` |
| tick / cycle | 2202501070 / 5720782 |
| sn / PC / opcode | 8652747 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1439979 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12668 / 145 |
| terminal | full |

### fault 147

| 字段 | 值 |
|---|---|
| 根 event_id | `876` |
| tick / cycle | 2218680310 / 5762806 |
| sn / PC / opcode | 8716214 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1450555 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10576 / 146 |
| terminal | full |

### fault 148

| 字段 | 值 |
|---|---|
| 根 event_id | `882` |
| tick / cycle | 2229001390 / 5789614 |
| sn / PC / opcode | 8756749 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1457310 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6755 / 147 |
| terminal | full |

### fault 149

| 字段 | 值 |
|---|---|
| 根 event_id | `888` |
| tick / cycle | 2242378600 / 5824360 |
| sn / PC / opcode | 8809600 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1466120 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8810 / 148 |
| terminal | full |

### fault 15

| 字段 | 值 |
|---|---|
| 根 event_id | `84` |
| tick / cycle | 203026285 / 527341 |
| sn / PC / opcode | 764172 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 125212 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11016 / 14 |
| terminal | full |

### fault 150

| 字段 | 值 |
|---|---|
| 根 event_id | `894` |
| tick / cycle | 2264414845 / 5881597 |
| sn / PC / opcode | 8896899 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1480671 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14551 / 149 |
| terminal | full |

### fault 151

| 字段 | 值 |
|---|---|
| 根 event_id | `900` |
| tick / cycle | 2282313110 / 5928086 |
| sn / PC / opcode | 8967064 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1492364 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11693 / 150 |
| terminal | full |

### fault 152

| 字段 | 值 |
|---|---|
| 根 event_id | `906` |
| tick / cycle | 2302058990 / 5979374 |
| sn / PC / opcode | 9045323 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1505405 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13041 / 151 |
| terminal | full |

### fault 153

| 字段 | 值 |
|---|---|
| 根 event_id | `912` |
| tick / cycle | 2321713240 / 6030424 |
| sn / PC / opcode | 9122547 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1518279 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12874 / 152 |
| terminal | full |

### fault 154

| 字段 | 值 |
|---|---|
| 根 event_id | `918` |
| tick / cycle | 2342653775 / 6084815 |
| sn / PC / opcode | 9205703 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1532135 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13856 / 153 |
| terminal | full |

### fault 155

| 字段 | 值 |
|---|---|
| 根 event_id | `924` |
| tick / cycle | 2352707280 / 6110928 |
| sn / PC / opcode | 9245268 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1538728 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6593 / 154 |
| terminal | full |

### fault 156

| 字段 | 值 |
|---|---|
| 根 event_id | `930` |
| tick / cycle | 2360708350 / 6131710 |
| sn / PC / opcode | 9276913 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1544004 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5276 / 155 |
| terminal | full |

### fault 157

| 字段 | 值 |
|---|---|
| 根 event_id | `936` |
| tick / cycle | 2376278905 / 6172153 |
| sn / PC / opcode | 9338332 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1554242 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10238 / 156 |
| terminal | full |

### fault 158

| 字段 | 值 |
|---|---|
| 根 event_id | `942` |
| tick / cycle | 2393374060 / 6216556 |
| sn / PC / opcode | 9405505 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1565436 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11194 / 157 |
| terminal | full |

### fault 159

| 字段 | 值 |
|---|---|
| 根 event_id | `948` |
| tick / cycle | 2448681235 / 6360211 |
| sn / PC / opcode | 9492110 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1578111 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12675 / 158 |
| terminal | full |

### fault 16

| 字段 | 值 |
|---|---|
| 根 event_id | `90` |
| tick / cycle | 217756770 / 565602 |
| sn / PC / opcode | 822527 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 134939 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9727 / 15 |
| terminal | full |

### fault 160

| 字段 | 值 |
|---|---|
| 根 event_id | `954` |
| tick / cycle | 2513770105 / 6529273 |
| sn / PC / opcode | 9586347 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1589799 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11688 / 159 |
| terminal | full |

### fault 161

| 字段 | 值 |
|---|---|
| 根 event_id | `960` |
| tick / cycle | 2586922030 / 6719278 |
| sn / PC / opcode | 9654757 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 1598306 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8507 / 160 |
| terminal | full |

### fault 162

| 字段 | 值 |
|---|---|
| 根 event_id | `966` |
| tick / cycle | 2633629075 / 6840595 |
| sn / PC / opcode | 9732153 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 1607974 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9668 / 161 |
| terminal | full |

### fault 163

| 字段 | 值 |
|---|---|
| 根 event_id | `972` |
| tick / cycle | 2696835680 / 7004768 |
| sn / PC / opcode | 9816743 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1618542 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10568 / 162 |
| terminal | full |

### fault 164

| 字段 | 值 |
|---|---|
| 根 event_id | `978` |
| tick / cycle | 2721870690 / 7069794 |
| sn / PC / opcode | 9857195 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1623592 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5050 / 163 |
| terminal | full |

### fault 165

| 字段 | 值 |
|---|---|
| 根 event_id | `984` |
| tick / cycle | 2767314550 / 7187830 |
| sn / PC / opcode | 9907835 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1629922 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6330 / 164 |
| terminal | full |

### fault 166

| 字段 | 值 |
|---|---|
| 根 event_id | `990` |
| tick / cycle | 2837348745 / 7369737 |
| sn / PC / opcode | 10015109 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1643319 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13397 / 165 |
| terminal | full |

### fault 167

| 字段 | 值 |
|---|---|
| 根 event_id | `996` |
| tick / cycle | 2888222645 / 7501877 |
| sn / PC / opcode | 10089963 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1652670 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9351 / 166 |
| terminal | full |

### fault 168

| 字段 | 值 |
|---|---|
| 根 event_id | `1002` |
| tick / cycle | 2946621370 / 7653562 |
| sn / PC / opcode | 10163191 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1661817 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9147 / 167 |
| terminal | full |

### fault 169

| 字段 | 值 |
|---|---|
| 根 event_id | `1008` |
| tick / cycle | 2974584305 / 7726193 |
| sn / PC / opcode | 10208445 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1667468 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5651 / 168 |
| terminal | full |

### fault 17

| 字段 | 值 |
|---|---|
| 根 event_id | `96` |
| tick / cycle | 240534525 / 624765 |
| sn / PC / opcode | 912172 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 149882 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14943 / 16 |
| terminal | full |

### fault 170

| 字段 | 值 |
|---|---|
| 根 event_id | `1014` |
| tick / cycle | 3050027750 / 7922150 |
| sn / PC / opcode | 10305911 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1679639 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12171 / 169 |
| terminal | full |

### fault 171

| 字段 | 值 |
|---|---|
| 根 event_id | `1020` |
| tick / cycle | 3071553485 / 7978061 |
| sn / PC / opcode | 10346479 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1684710 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5071 / 170 |
| terminal | full |

### fault 172

| 字段 | 值 |
|---|---|
| 根 event_id | `1026` |
| tick / cycle | 3144428210 / 8167346 |
| sn / PC / opcode | 10439561 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 1696333 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11623 / 171 |
| terminal | full |

### fault 173

| 字段 | 值 |
|---|---|
| 根 event_id | `1032` |
| tick / cycle | 3201445940 / 8315444 |
| sn / PC / opcode | 10530645 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1707712 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11379 / 172 |
| terminal | full |

### fault 174

| 字段 | 值 |
|---|---|
| 根 event_id | `1038` |
| tick / cycle | 3261958315 / 8472619 |
| sn / PC / opcode | 10617523 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1718566 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10854 / 173 |
| terminal | full |

### fault 175

| 字段 | 值 |
|---|---|
| 根 event_id | `1044` |
| tick / cycle | 3319721020 / 8622652 |
| sn / PC / opcode | 10688471 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1727428 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8862 / 174 |
| terminal | full |

### fault 176

| 字段 | 值 |
|---|---|
| 根 event_id | `1050` |
| tick / cycle | 3390684990 / 8806974 |
| sn / PC / opcode | 10796785 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1740955 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13527 / 175 |
| terminal | full |

### fault 177

| 字段 | 值 |
|---|---|
| 根 event_id | `1056` |
| tick / cycle | 3451802200 / 8965720 |
| sn / PC / opcode | 10886503 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1752164 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11209 / 176 |
| terminal | full |

### fault 178

| 字段 | 值 |
|---|---|
| 根 event_id | `1062` |
| tick / cycle | 3504924500 / 9103700 |
| sn / PC / opcode | 10949563 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 1760040 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7876 / 177 |
| terminal | full |

### fault 179

| 字段 | 值 |
|---|---|
| 根 event_id | `1068` |
| tick / cycle | 3552153605 / 9226373 |
| sn / PC / opcode | 11028893 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1769944 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9904 / 178 |
| terminal | full |

### fault 18

| 字段 | 值 |
|---|---|
| 根 event_id | `102` |
| tick / cycle | 253697675 / 658955 |
| sn / PC / opcode | 963686 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 158467 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8585 / 17 |
| terminal | full |

### fault 180

| 字段 | 值 |
|---|---|
| 根 event_id | `1074` |
| tick / cycle | 3622018015 / 9407839 |
| sn / PC / opcode | 11118331 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 1781118 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11174 / 179 |
| terminal | full |

### fault 181

| 字段 | 值 |
|---|---|
| 根 event_id | `1080` |
| tick / cycle | 3701743430 / 9614918 |
| sn / PC / opcode | 11223845 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1794295 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13177 / 180 |
| terminal | full |

### fault 182

| 字段 | 值 |
|---|---|
| 根 event_id | `1086` |
| tick / cycle | 3725196860 / 9675836 |
| sn / PC / opcode | 11268045 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1799820 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5525 / 181 |
| terminal | full |

### fault 183

| 字段 | 值 |
|---|---|
| 根 event_id | `1092` |
| tick / cycle | 3760703870 / 9768062 |
| sn / PC / opcode | 11318593 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 1806132 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6312 / 182 |
| terminal | full |

### fault 184

| 字段 | 值 |
|---|---|
| 根 event_id | `1098` |
| tick / cycle | 3800713070 / 9871982 |
| sn / PC / opcode | 11366519 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1812117 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5985 / 183 |
| terminal | full |

### fault 185

| 字段 | 值 |
|---|---|
| 根 event_id | `1104` |
| tick / cycle | 3844519140 / 9985764 |
| sn / PC / opcode | 11438219 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 1821073 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8956 / 184 |
| terminal | full |

### fault 186

| 字段 | 值 |
|---|---|
| 根 event_id | `1110` |
| tick / cycle | 3889827095 / 10103447 |
| sn / PC / opcode | 11489353 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1827459 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6386 / 185 |
| terminal | full |

### fault 187

| 字段 | 值 |
|---|---|
| 根 event_id | `1116` |
| tick / cycle | 3911516070 / 10159782 |
| sn / PC / opcode | 11530193 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1832564 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5105 / 186 |
| terminal | full |

### fault 188

| 字段 | 值 |
|---|---|
| 根 event_id | `1122` |
| tick / cycle | 3995871880 / 10378888 |
| sn / PC / opcode | 11644819 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1846880 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14316 / 187 |
| terminal | full |

### fault 189

| 字段 | 值 |
|---|---|
| 根 event_id | `1128` |
| tick / cycle | 4071691085 / 10575821 |
| sn / PC / opcode | 11745295 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1859433 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12553 / 188 |
| terminal | full |

### fault 19

| 字段 | 值 |
|---|---|
| 根 event_id | `108` |
| tick / cycle | 269147725 / 699085 |
| sn / PC / opcode | 1024635 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 168627 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10160 / 18 |
| terminal | full |

### fault 190

| 字段 | 值 |
|---|---|
| 根 event_id | `1134` |
| tick / cycle | 4145427055 / 10767343 |
| sn / PC / opcode | 11856361 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 1873304 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13871 / 189 |
| terminal | full |

### fault 191

| 字段 | 值 |
|---|---|
| 根 event_id | `1140` |
| tick / cycle | 4199956915 / 10908979 |
| sn / PC / opcode | 11941951 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1883997 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10693 / 190 |
| terminal | full |

### fault 192

| 字段 | 值 |
|---|---|
| 根 event_id | `1146` |
| tick / cycle | 4260100460 / 11065196 |
| sn / PC / opcode | 12012241 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 1892771 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8774 / 191 |
| terminal | full |

### fault 193

| 字段 | 值 |
|---|---|
| 根 event_id | `1152` |
| tick / cycle | 4308087630 / 11189838 |
| sn / PC / opcode | 12092797 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 1902834 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10063 / 192 |
| terminal | full |

### fault 194

| 字段 | 值 |
|---|---|
| 根 event_id | `1158` |
| tick / cycle | 4357364935 / 11317831 |
| sn / PC / opcode | 12152635 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 1910308 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7474 / 193 |
| terminal | full |

### fault 195

| 字段 | 值 |
|---|---|
| 根 event_id | `1164` |
| tick / cycle | 4390499190 / 11403894 |
| sn / PC / opcode | 12211903 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 1917710 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7402 / 194 |
| terminal | full |

### fault 196

| 字段 | 值 |
|---|---|
| 根 event_id | `1170` |
| tick / cycle | 4471865090 / 11615234 |
| sn / PC / opcode | 12323789 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1931690 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13980 / 195 |
| terminal | full |

### fault 197

| 字段 | 值 |
|---|---|
| 根 event_id | `1176` |
| tick / cycle | 4508211785 / 11709641 |
| sn / PC / opcode | 12372113 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 1937724 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6034 / 196 |
| terminal | full |

### fault 198

| 字段 | 值 |
|---|---|
| 根 event_id | `1182` |
| tick / cycle | 4561377975 / 11847735 |
| sn / PC / opcode | 12447631 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 1947158 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9434 / 197 |
| terminal | full |

### fault 199

| 字段 | 值 |
|---|---|
| 根 event_id | `1188` |
| tick / cycle | 4612264580 / 11979908 |
| sn / PC / opcode | 12515003 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 1955573 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8415 / 198 |
| terminal | full |

### fault 2

| 字段 | 值 |
|---|---|
| 根 event_id | `6` |
| tick / cycle | 34994575 / 90895 |
| sn / PC / opcode | 100691 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 14633 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9224 / 1 |
| terminal | full |

### fault 20

| 字段 | 值 |
|---|---|
| 根 event_id | `114` |
| tick / cycle | 287327425 / 746305 |
| sn / PC / opcode | 1096562 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 180613 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11986 / 19 |
| terminal | full |

### fault 200

| 字段 | 值 |
|---|---|
| 根 event_id | `1194` |
| tick / cycle | 4643394910 / 12060766 |
| sn / PC / opcode | 12558665 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 1961025 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5452 / 199 |
| terminal | full |

### fault 201

| 字段 | 值 |
|---|---|
| 根 event_id | `1200` |
| tick / cycle | 4726861755 / 12277563 |
| sn / PC / opcode | 12671611 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 1975131 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14106 / 200 |
| terminal | full |

### fault 202

| 字段 | 值 |
|---|---|
| 根 event_id | `1206` |
| tick / cycle | 4808764345 / 12490297 |
| sn / PC / opcode | 12787799 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 1989648 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14517 / 201 |
| terminal | full |

### fault 203

| 字段 | 值 |
|---|---|
| 根 event_id | `1212` |
| tick / cycle | 4875959550 / 12664830 |
| sn / PC / opcode | 12891529 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 2002602 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12954 / 202 |
| terminal | full |

### fault 204

| 字段 | 值 |
|---|---|
| 根 event_id | `1218` |
| tick / cycle | 4953489695 / 12866207 |
| sn / PC / opcode | 13003827 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 2016627 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14025 / 203 |
| terminal | full |

### fault 205

| 字段 | 值 |
|---|---|
| 根 event_id | `1224` |
| tick / cycle | 5016754050 / 13030530 |
| sn / PC / opcode | 13084321 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 2026683 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10056 / 204 |
| terminal | full |

### fault 206

| 字段 | 值 |
|---|---|
| 根 event_id | `1230` |
| tick / cycle | 5068097265 / 13163889 |
| sn / PC / opcode | 13160005 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 2036137 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9454 / 205 |
| terminal | full |

### fault 207

| 字段 | 值 |
|---|---|
| 根 event_id | `1236` |
| tick / cycle | 5139755775 / 13350015 |
| sn / PC / opcode | 13265663 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 2049332 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13195 / 206 |
| terminal | full |

### fault 208

| 字段 | 值 |
|---|---|
| 根 event_id | `1242` |
| tick / cycle | 5220375160 / 13559416 |
| sn / PC / opcode | 13379253 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 2063525 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14193 / 207 |
| terminal | full |

### fault 209

| 字段 | 值 |
|---|---|
| 根 event_id | `1248` |
| tick / cycle | 5306131600 / 13782160 |
| sn / PC / opcode | 13495879 / 0x00000000004006cc / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 2078091 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14566 / 208 |
| terminal | full |

### fault 21

| 字段 | 值 |
|---|---|
| 根 event_id | `120` |
| tick / cycle | 300613390 / 780814 |
| sn / PC / opcode | 1148869 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 189330 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8717 / 20 |
| terminal | full |

### fault 210

| 字段 | 值 |
|---|---|
| 根 event_id | `1254` |
| tick / cycle | 5369103740 / 13945724 |
| sn / PC / opcode | 13575763 / 0x00000000004006a4 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 2088070 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9979 / 209 |
| terminal | full |

### fault 22

| 字段 | 值 |
|---|---|
| 根 event_id | `126` |
| tick / cycle | 315676515 / 819939 |
| sn / PC / opcode | 1208272 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 199232 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9902 / 21 |
| terminal | full |

### fault 23

| 字段 | 值 |
|---|---|
| 根 event_id | `132` |
| tick / cycle | 337381275 / 876315 |
| sn / PC / opcode | 1293553 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 213444 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14212 / 22 |
| terminal | full |

### fault 24

| 字段 | 值 |
|---|---|
| 根 event_id | `138` |
| tick / cycle | 356158110 / 925086 |
| sn / PC / opcode | 1367894 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 225835 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12391 / 23 |
| terminal | full |

### fault 25

| 字段 | 值 |
|---|---|
| 根 event_id | `144` |
| tick / cycle | 378328720 / 982672 |
| sn / PC / opcode | 1455443 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 240425 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14590 / 24 |
| terminal | full |

### fault 26

| 字段 | 值 |
|---|---|
| 根 event_id | `150` |
| tick / cycle | 397763520 / 1033152 |
| sn / PC / opcode | 1532161 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 253212 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12787 / 25 |
| terminal | full |

### fault 27

| 字段 | 值 |
|---|---|
| 根 event_id | `156` |
| tick / cycle | 416940370 / 1082962 |
| sn / PC / opcode | 1607723 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 265805 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12593 / 26 |
| terminal | full |

### fault 28

| 字段 | 值 |
|---|---|
| 根 event_id | `162` |
| tick / cycle | 431269300 / 1120180 |
| sn / PC / opcode | 1664245 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 275226 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9421 / 27 |
| terminal | full |

### fault 29

| 字段 | 值 |
|---|---|
| 根 event_id | `168` |
| tick / cycle | 440572440 / 1144344 |
| sn / PC / opcode | 1701071 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 281363 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6137 / 28 |
| terminal | full |

### fault 3

| 字段 | 值 |
|---|---|
| 根 event_id | `12` |
| tick / cycle | 46149565 / 119869 |
| sn / PC / opcode | 144508 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 21938 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7305 / 2 |
| terminal | full |

### fault 30

| 字段 | 值 |
|---|---|
| 根 event_id | `174` |
| tick / cycle | 457782325 / 1189045 |
| sn / PC / opcode | 1768468 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 292598 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11235 / 29 |
| terminal | full |

### fault 31

| 字段 | 值 |
|---|---|
| 根 event_id | `180` |
| tick / cycle | 472164770 / 1226402 |
| sn / PC / opcode | 1825488 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 302098 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9500 / 30 |
| terminal | full |

### fault 32

| 字段 | 值 |
|---|---|
| 根 event_id | `186` |
| tick / cycle | 491785525 / 1277365 |
| sn / PC / opcode | 1903211 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 315053 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12955 / 31 |
| terminal | full |

### fault 33

| 字段 | 值 |
|---|---|
| 根 event_id | `192` |
| tick / cycle | 499798145 / 1298177 |
| sn / PC / opcode | 1934351 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 320243 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5190 / 32 |
| terminal | full |

### fault 34

| 字段 | 值 |
|---|---|
| 根 event_id | `198` |
| tick / cycle | 519848560 / 1350256 |
| sn / PC / opcode | 2013876 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 333496 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13253 / 33 |
| terminal | full |

### fault 35

| 字段 | 值 |
|---|---|
| 根 event_id | `204` |
| tick / cycle | 530443760 / 1377776 |
| sn / PC / opcode | 2055744 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 340474 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6978 / 34 |
| terminal | full |

### fault 36

| 字段 | 值 |
|---|---|
| 根 event_id | `210` |
| tick / cycle | 542772230 / 1409798 |
| sn / PC / opcode | 2104344 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 348574 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8100 / 35 |
| terminal | full |

### fault 37

| 字段 | 值 |
|---|---|
| 根 event_id | `216` |
| tick / cycle | 558490625 / 1450625 |
| sn / PC / opcode | 2166372 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 358912 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10338 / 36 |
| terminal | full |

### fault 38

| 字段 | 值 |
|---|---|
| 根 event_id | `222` |
| tick / cycle | 567864990 / 1474974 |
| sn / PC / opcode | 2203488 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 365098 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6186 / 37 |
| terminal | full |

### fault 39

| 字段 | 值 |
|---|---|
| 根 event_id | `228` |
| tick / cycle | 590348990 / 1533374 |
| sn / PC / opcode | 2292086 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 379867 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14769 / 38 |
| terminal | full |

### fault 4

| 字段 | 值 |
|---|---|
| 根 event_id | `18` |
| tick / cycle | 54420520 / 141352 |
| sn / PC / opcode | 177664 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 27464 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5526 / 3 |
| terminal | full |

### fault 40

| 字段 | 值 |
|---|---|
| 根 event_id | `234` |
| tick / cycle | 605399410 / 1572466 |
| sn / PC / opcode | 2351487 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 389769 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9902 / 39 |
| terminal | full |

### fault 41

| 字段 | 值 |
|---|---|
| 根 event_id | `240` |
| tick / cycle | 617760220 / 1604572 |
| sn / PC / opcode | 2399976 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 397846 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8077 / 40 |
| terminal | full |

### fault 42

| 字段 | 值 |
|---|---|
| 根 event_id | `246` |
| tick / cycle | 628286505 / 1631913 |
| sn / PC / opcode | 2441882 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 404833 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6987 / 41 |
| terminal | full |

### fault 43

| 字段 | 值 |
|---|---|
| 根 event_id | `252` |
| tick / cycle | 637092610 / 1654786 |
| sn / PC / opcode | 2476693 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 410634 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5801 / 42 |
| terminal | full |

### fault 44

| 字段 | 值 |
|---|---|
| 根 event_id | `258` |
| tick / cycle | 648185615 / 1683599 |
| sn / PC / opcode | 2520326 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 417907 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7273 / 43 |
| terminal | full |

### fault 45

| 字段 | 值 |
|---|---|
| 根 event_id | `264` |
| tick / cycle | 667884525 / 1734765 |
| sn / PC / opcode | 2597619 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 430791 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12884 / 44 |
| terminal | full |

### fault 46

| 字段 | 值 |
|---|---|
| 根 event_id | `270` |
| tick / cycle | 681094260 / 1769076 |
| sn / PC / opcode | 2649815 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 439487 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8696 / 45 |
| terminal | full |

### fault 47

| 字段 | 值 |
|---|---|
| 根 event_id | `276` |
| tick / cycle | 695753905 / 1807153 |
| sn / PC / opcode | 2707524 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 16 / 0x0000000000010000 |
| eligible ordinal / total | 449104 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9617 / 46 |
| terminal | full |

### fault 48

| 字段 | 值 |
|---|---|
| 根 event_id | `282` |
| tick / cycle | 706899655 / 1836103 |
| sn / PC / opcode | 2751841 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 456492 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7388 / 47 |
| terminal | full |

### fault 49

| 字段 | 值 |
|---|---|
| 根 event_id | `288` |
| tick / cycle | 729238510 / 1894126 |
| sn / PC / opcode | 2839968 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 471178 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14686 / 48 |
| terminal | full |

### fault 5

| 字段 | 值 |
|---|---|
| 根 event_id | `24` |
| tick / cycle | 71512980 / 185748 |
| sn / PC / opcode | 245232 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 38722 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11258 / 4 |
| terminal | full |

### fault 50

| 字段 | 值 |
|---|---|
| 根 event_id | `294` |
| tick / cycle | 747668845 / 1941997 |
| sn / PC / opcode | 2912581 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 483282 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12104 / 49 |
| terminal | full |

### fault 51

| 字段 | 值 |
|---|---|
| 根 event_id | `300` |
| tick / cycle | 757795500 / 1968300 |
| sn / PC / opcode | 2952431 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 489923 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6641 / 50 |
| terminal | full |

### fault 52

| 字段 | 值 |
|---|---|
| 根 event_id | `306` |
| tick / cycle | 774130665 / 2010729 |
| sn / PC / opcode | 3017377 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 500748 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10825 / 51 |
| terminal | full |

### fault 53

| 字段 | 值 |
|---|---|
| 根 event_id | `312` |
| tick / cycle | 789700835 / 2051171 |
| sn / PC / opcode | 3078179 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 510881 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10133 / 52 |
| terminal | full |

### fault 54

| 字段 | 值 |
|---|---|
| 根 event_id | `318` |
| tick / cycle | 803341385 / 2086601 |
| sn / PC / opcode | 3131788 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 519818 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8937 / 53 |
| terminal | full |

### fault 55

| 字段 | 值 |
|---|---|
| 根 event_id | `324` |
| tick / cycle | 824370470 / 2141222 |
| sn / PC / opcode | 3215303 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 533735 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13917 / 54 |
| terminal | full |

### fault 56

| 字段 | 值 |
|---|---|
| 根 event_id | `330` |
| tick / cycle | 837977525 / 2176565 |
| sn / PC / opcode | 3268982 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 542683 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8948 / 55 |
| terminal | full |

### fault 57

| 字段 | 值 |
|---|---|
| 根 event_id | `336` |
| tick / cycle | 859686520 / 2232952 |
| sn / PC / opcode | 3354520 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 15 / 0x0000000000008000 |
| eligible ordinal / total | 556940 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14257 / 56 |
| terminal | full |

### fault 58

| 字段 | 值 |
|---|---|
| 根 event_id | `342` |
| tick / cycle | 877573620 / 2279412 |
| sn / PC / opcode | 3424864 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 568664 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11724 / 57 |
| terminal | full |

### fault 59

| 字段 | 值 |
|---|---|
| 根 event_id | `348` |
| tick / cycle | 892451945 / 2318057 |
| sn / PC / opcode | 3483899 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 10 / 0x0000000000000400 |
| eligible ordinal / total | 578501 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9837 / 58 |
| terminal | full |

### fault 6

| 字段 | 值 |
|---|---|
| 根 event_id | `30` |
| tick / cycle | 81443670 / 211542 |
| sn / PC / opcode | 284366 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 12 / 0x0000000000001000 |
| eligible ordinal / total | 45247 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6525 / 5 |
| terminal | full |

### fault 60

| 字段 | 值 |
|---|---|
| 根 event_id | `354` |
| tick / cycle | 913245025 / 2372065 |
| sn / PC / opcode | 3566017 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 592188 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13687 / 59 |
| terminal | full |

### fault 61

| 字段 | 值 |
|---|---|
| 根 event_id | `360` |
| tick / cycle | 922916610 / 2397186 |
| sn / PC / opcode | 3604036 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 598526 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6338 / 60 |
| terminal | full |

### fault 62

| 字段 | 值 |
|---|---|
| 根 event_id | `366` |
| tick / cycle | 935448360 / 2429736 |
| sn / PC / opcode | 3653426 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 606757 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8231 / 61 |
| terminal | full |

### fault 63

| 字段 | 值 |
|---|---|
| 根 event_id | `372` |
| tick / cycle | 948391675 / 2463355 |
| sn / PC / opcode | 3704331 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 615243 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8486 / 62 |
| terminal | full |

### fault 64

| 字段 | 值 |
|---|---|
| 根 event_id | `378` |
| tick / cycle | 956410840 / 2484184 |
| sn / PC / opcode | 3736407 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 620589 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5346 / 63 |
| terminal | full |

### fault 65

| 字段 | 值 |
|---|---|
| 根 event_id | `384` |
| tick / cycle | 968598015 / 2515839 |
| sn / PC / opcode | 3784068 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 628528 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7939 / 64 |
| terminal | full |

### fault 66

| 字段 | 值 |
|---|---|
| 根 event_id | `390` |
| tick / cycle | 990229625 / 2572025 |
| sn / PC / opcode | 3869099 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 642701 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14173 / 65 |
| terminal | full |

### fault 67

| 字段 | 值 |
|---|---|
| 根 event_id | `396` |
| tick / cycle | 1006329555 / 2613843 |
| sn / PC / opcode | 3933076 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 653366 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10665 / 66 |
| terminal | full |

### fault 68

| 字段 | 值 |
|---|---|
| 根 event_id | `402` |
| tick / cycle | 1024039555 / 2659843 |
| sn / PC / opcode | 4002483 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 664935 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11569 / 67 |
| terminal | full |

### fault 69

| 字段 | 值 |
|---|---|
| 根 event_id | `408` |
| tick / cycle | 1043454335 / 2710271 |
| sn / PC / opcode | 4079379 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 677751 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12816 / 68 |
| terminal | full |

### fault 7

| 字段 | 值 |
|---|---|
| 根 event_id | `36` |
| tick / cycle | 90773760 / 235776 |
| sn / PC / opcode | 321302 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 51403 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6156 / 6 |
| terminal | full |

### fault 70

| 字段 | 值 |
|---|---|
| 根 event_id | `414` |
| tick / cycle | 1061692555 / 2757643 |
| sn / PC / opcode | 4151451 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 689763 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12012 / 69 |
| terminal | full |

### fault 71

| 字段 | 值 |
|---|---|
| 根 event_id | `420` |
| tick / cycle | 1072187270 / 2784902 |
| sn / PC / opcode | 4193135 / 0x0000000000400648 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 696707 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6944 / 70 |
| terminal | full |

### fault 72

| 字段 | 值 |
|---|---|
| 根 event_id | `426` |
| tick / cycle | 1093053885 / 2839101 |
| sn / PC / opcode | 4275076 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 710366 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13659 / 71 |
| terminal | full |

### fault 73

| 字段 | 值 |
|---|---|
| 根 event_id | `432` |
| tick / cycle | 1102437105 / 2863473 |
| sn / PC / opcode | 4312227 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 716559 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6193 / 72 |
| terminal | full |

### fault 74

| 字段 | 值 |
|---|---|
| 根 event_id | `438` |
| tick / cycle | 1124568060 / 2920956 |
| sn / PC / opcode | 4399956 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 731176 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14617 / 73 |
| terminal | full |

### fault 75

| 字段 | 值 |
|---|---|
| 根 event_id | `444` |
| tick / cycle | 1132713505 / 2942113 |
| sn / PC / opcode | 4432072 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 736532 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5356 / 74 |
| terminal | full |

### fault 76

| 字段 | 值 |
|---|---|
| 根 event_id | `450` |
| tick / cycle | 1150479330 / 2988258 |
| sn / PC / opcode | 4502307 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 748239 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11707 / 75 |
| terminal | full |

### fault 77

| 字段 | 值 |
|---|---|
| 根 event_id | `456` |
| tick / cycle | 1169187635 / 3036851 |
| sn / PC / opcode | 4575675 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 760467 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12228 / 76 |
| terminal | full |

### fault 78

| 字段 | 值 |
|---|---|
| 根 event_id | `462` |
| tick / cycle | 1185687195 / 3079707 |
| sn / PC / opcode | 4640366 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 771247 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10780 / 77 |
| terminal | full |

### fault 79

| 字段 | 值 |
|---|---|
| 根 event_id | `468` |
| tick / cycle | 1197045080 / 3109208 |
| sn / PC / opcode | 4685546 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 1 / 0x0000000000000002 |
| eligible ordinal / total | 778777 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7530 / 78 |
| terminal | full |

### fault 8

| 字段 | 值 |
|---|---|
| 根 event_id | `42` |
| tick / cycle | 111934515 / 290739 |
| sn / PC / opcode | 404532 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 65272 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13869 / 7 |
| terminal | full |

### fault 80

| 字段 | 值 |
|---|---|
| 根 event_id | `474` |
| tick / cycle | 1210262515 / 3143539 |
| sn / PC / opcode | 4737532 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 787442 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8665 / 79 |
| terminal | full |

### fault 81

| 字段 | 值 |
|---|---|
| 根 event_id | `480` |
| tick / cycle | 1230807270 / 3196902 |
| sn / PC / opcode | 4818675 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 800967 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13525 / 80 |
| terminal | full |

### fault 82

| 字段 | 值 |
|---|---|
| 根 event_id | `486` |
| tick / cycle | 1249624915 / 3245779 |
| sn / PC / opcode | 4893051 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 9 / 0x0000000000000200 |
| eligible ordinal / total | 813363 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12396 / 81 |
| terminal | full |

### fault 83

| 字段 | 值 |
|---|---|
| 根 event_id | `492` |
| tick / cycle | 1267351470 / 3291822 |
| sn / PC / opcode | 4963141 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 0 / 0x0000000000000001 |
| eligible ordinal / total | 825042 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11679 / 82 |
| terminal | full |

### fault 84

| 字段 | 值 |
|---|---|
| 根 event_id | `498` |
| tick / cycle | 1278130315 / 3319819 |
| sn / PC / opcode | 5005658 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 17 / 0x0000000000020000 |
| eligible ordinal / total | 832129 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7087 / 83 |
| terminal | full |

### fault 85

| 字段 | 值 |
|---|---|
| 根 event_id | `504` |
| tick / cycle | 1289830080 / 3350208 |
| sn / PC / opcode | 5051702 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 14 / 0x0000000000004000 |
| eligible ordinal / total | 839803 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7674 / 84 |
| terminal | full |

### fault 86

| 字段 | 值 |
|---|---|
| 根 event_id | `510` |
| tick / cycle | 1300266275 / 3377315 |
| sn / PC / opcode | 5092671 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 846633 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6830 / 85 |
| terminal | full |

### fault 87

| 字段 | 值 |
|---|---|
| 根 event_id | `516` |
| tick / cycle | 1315226220 / 3416172 |
| sn / PC / opcode | 5152034 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 13 / 0x0000000000002000 |
| eligible ordinal / total | 856525 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9892 / 86 |
| terminal | full |

### fault 88

| 字段 | 值 |
|---|---|
| 根 event_id | `522` |
| tick / cycle | 1325005605 / 3441573 |
| sn / PC / opcode | 5190733 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 11 / 0x0000000000000800 |
| eligible ordinal / total | 862974 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6449 / 87 |
| terminal | full |

### fault 89

| 字段 | 值 |
|---|---|
| 根 event_id | `528` |
| tick / cycle | 1337112700 / 3473020 |
| sn / PC / opcode | 5238433 / 0x0000000000400650 / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 8 / 0x0000000000000100 |
| eligible ordinal / total | 870924 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7950 / 88 |
| terminal | full |

### fault 9

| 字段 | 值 |
|---|---|
| 根 event_id | `48` |
| tick / cycle | 130165035 / 338091 |
| sn / PC / opcode | 476356 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 77246 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 11974 / 8 |
| terminal | full |

### fault 90

| 字段 | 值 |
|---|---|
| 根 event_id | `534` |
| tick / cycle | 1356490520 / 3523352 |
| sn / PC / opcode | 5314824 / 0x000000000040064c / scvtf |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 883654 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 12730 / 89 |
| terminal | full |

### fault 91

| 字段 | 值 |
|---|---|
| 根 event_id | `540` |
| tick / cycle | 1370661215 / 3560159 |
| sn / PC / opcode | 5370592 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 892952 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 9298 / 90 |
| terminal | full |

### fault 92

| 字段 | 值 |
|---|---|
| 根 event_id | `546` |
| tick / cycle | 1379876190 / 3584094 |
| sn / PC / opcode | 5407059 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 899031 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6079 / 91 |
| terminal | full |

### fault 93

| 字段 | 值 |
|---|---|
| 根 event_id | `552` |
| tick / cycle | 1389079615 / 3607999 |
| sn / PC / opcode | 5443131 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 2 / 0x0000000000000004 |
| eligible ordinal / total | 905043 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 6012 / 92 |
| terminal | full |

### fault 94

| 字段 | 值 |
|---|---|
| 根 event_id | `558` |
| tick / cycle | 1397088000 / 3628800 |
| sn / PC / opcode | 5474702 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 4 / 0x0000000000000010 |
| eligible ordinal / total | 910303 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 5260 / 93 |
| terminal | full |

### fault 95

| 字段 | 值 |
|---|---|
| 根 event_id | `564` |
| tick / cycle | 1412332460 / 3668396 |
| sn / PC / opcode | 5534894 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 920335 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 10032 / 94 |
| terminal | full |

### fault 96

| 字段 | 值 |
|---|---|
| 根 event_id | `570` |
| tick / cycle | 1434237420 / 3725292 |
| sn / PC / opcode | 5621188 / 0x000000000040065c / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 7 / 0x0000000000000080 |
| eligible ordinal / total | 934718 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 14383 / 95 |
| terminal | full |

### fault 97

| 字段 | 值 |
|---|---|
| 根 event_id | `576` |
| tick / cycle | 1445223395 / 3753827 |
| sn / PC / opcode | 5664855 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 5 / 0x0000000000000020 |
| eligible ordinal / total | 941997 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 7279 / 96 |
| terminal | full |

### fault 98

| 字段 | 值 |
|---|---|
| 根 event_id | `582` |
| tick / cycle | 1458764615 / 3788999 |
| sn / PC / opcode | 5717955 / 0x0000000000400658 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 6 / 0x0000000000000040 |
| eligible ordinal / total | 950847 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 8850 / 97 |
| terminal | full |

### fault 99

| 字段 | 值 |
|---|---|
| 根 event_id | `588` |
| tick / cycle | 1478997520 / 3841552 |
| sn / PC / opcode | 5798342 / 0x0000000000400654 / fmadd |
| 单元/结构/slot/port/lane | FSU_Pipe / mant_lo / — / — / 64@0 |
| fault bit / mask | 3 / 0x0000000000000008 |
| eligible ordinal / total | 964243 / 2097155 |
| rate divisor / jitter / interval / ordinal_index | 10000 / 50 / 13396 / 98 |
| terminal | full |

注入日志原文（本 seed `fpu_injections.log` 最后 5 行）：

```
Tick: 5139755775, Site: dyn_inst_execute, opClass=8, sn=13265663, bitseg=mant_lo, mask=0x4000, faults_injected: 207
Tick: 5220375160, Site: dyn_inst_execute, opClass=8, sn=13379253, bitseg=mant_lo, mask=0x80, faults_injected: 208
Tick: 5306131600, Site: dyn_inst_execute, opClass=8, sn=13495879, bitseg=mant_lo, mask=0x100, faults_injected: 209
Tick: 5369103740, Site: dyn_inst_execute, opClass=8, sn=13575763, bitseg=mant_lo, mask=0x1, faults_injected: 210
CHAOS_RATE_COMPLETE=210
```

## 3. 注入前后状态

### fault 1

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe75c28f5c28f5c → 0x3fe75c28f5c28f4c |
| old/new hash | 0x062cb92512563e25 → 0x7d48dcf641740175 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe75c28f5c28f5c / 0x3fe75c28f5c28f4c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 10

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4082400000000000 → 0x4082400000000002 |
| old/new hash | 0x70a2c17fe8163511 → 0xddfdcb6b5e44b173 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4082400000000000 / 0x4082400000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 100

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feed0e560418937 → 0x3feed0e560418935 |
| old/new hash | 0x408f6a6fa08cf018 → 0x4ae7309b52edbf12 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feed0e560418937 / 0x3feed0e560418935 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 101

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe8189374bc6a7f → 0x3fe8189374bc6a5f |
| old/new hash | 0x4ad4213fc57e178c → 0x13495fa61d61ddac |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe8189374bc6a7f / 0x3fe8189374bc6a5f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 102

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407e400000000000 → 0x407e400000004000 |
| old/new hash | 0x7138c97fe896199d → 0x72ccac11eafc35dd |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407e400000000000 / 0x407e400000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 103

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe5374bc6a7ef9e → 0x3fe5374bc6a6ef9e |
| old/new hash | 0xbfa56df848cfd0ff → 0x96d8d23d36acd82a |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe5374bc6a7ef9e / 0x3fe5374bc6a6ef9e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 104

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x405cc00000000000 → 0x405cc00000000080 |
| old/new hash | 0x1cee557d74f8160f → 0x4905d0fce551b08f |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x405cc00000000000 / 0x405cc00000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 105

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4086180000000000 → 0x4086180000000080 |
| old/new hash | 0x8b9df17ed562e5cd → 0x11a06cf960a0fe4d |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4086180000000000 / 0x4086180000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 106

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc5c28f5c28f5c2 → 0xbfc5c28f5c28f1c2 |
| old/new hash | 0x94a0ea363691eb1f → 0x4025fd9ea7aa5633 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc5c28f5c28f5c2 / 0xbfc5c28f5c28f1c2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 107

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408c280000000000 → 0x408c280000008000 |
| old/new hash | 0xef5edd7dece32e57 → 0x42bb1855001697d7 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408c280000000000 / 0x408c280000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 108

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4044000000000000 → 0x4044000000000400 |
| old/new hash | 0x48e5657eb0531587 → 0x5e13a3a7f78a6e2b |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4044000000000000 / 0x4044000000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 109

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff795810624dd2f → 0x3ff7958106249d2f |
| old/new hash | 0xde35ab1c9f19a8e5 → 0x84408dac27baf725 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff795810624dd2f / 0x3ff7958106249d2f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 11

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd74bc6a7ef9db2 → 0x3fd74bc6a7ee9db2 |
| old/new hash | 0x64dd97bd3a314bd9 → 0x1f358d06e3dcc968 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd74bc6a7ef9db2 / 0x3fd74bc6a7ee9db2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 110

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fed810624dd2f1b → 0x3fed810624dd2e1b |
| old/new hash | 0xc560c2dd20e1fba5 → 0x48a7b9ae5da2bdb6 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fed810624dd2f1b / 0x3fed810624dd2e1b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 111

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408e880000000000 → 0x408e880000000040 |
| old/new hash | 0xafc9717c15dd0e65 → 0x17f6b3c3b9af1b25 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408e880000000000 / 0x408e880000000040 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 112

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fca1cac083126ea → 0x3fca1cac083126ee |
| old/new hash | 0x830b0e6a85e38ba9 → 0x8350b8213ad38cbd |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fca1cac083126ea / 0x3fca1cac083126ee |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 113

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408e280000000000 → 0x408e280000010000 |
| old/new hash | 0xef58117decdd6805 → 0x0f5b2d4afc079f4c |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408e280000000000 / 0x408e280000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 114

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd3333333333333 → 0xbfd3333333323333 |
| old/new hash | 0x2401a34a260d90df → 0x2637b8d7d68d09ae |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd3333333333333 / 0xbfd3333333323333 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 115

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe54fdf3b645a1d → 0x3fe54fdf3b645a19 |
| old/new hash | 0xe2dcaa3753335d57 → 0xe4d2b7a0be35426b |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe54fdf3b645a1d / 0x3fe54fdf3b645a19 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 116

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4085600000000000 → 0x4085600000000400 |
| old/new hash | 0x5b845f7f4b24cf7e → 0x1bf61da61e5e85a2 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4085600000000000 / 0x4085600000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 117

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408d600000000000 → 0x408d600000000080 |
| old/new hash | 0x5b69af7f4b0e8fb6 → 0xe16c2af9d64ca836 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408d600000000000 / 0x408d600000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 118

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4074500000000000 → 0x4074500000010000 |
| old/new hash | 0xfe1235803900dd87 → 0xb722314a39b3874e |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4074500000000000 / 0x4074500000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 119

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4082400000000000 → 0x4082400000004000 |
| old/new hash | 0x70a2c17fe8163511 → 0x73eaa411ebef98d1 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4082400000000000 / 0x4082400000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 12

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc24dd2f1a9fbe7 → 0xbfc24dd2f1a9f9e7 |
| old/new hash | 0xcad45983ee3a2361 → 0x26ea614fced09fa7 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc24dd2f1a9fbe7 / 0xbfc24dd2f1a9f9e7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 120

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff2d0e560418937 → 0x3ff2d0e560418977 |
| old/new hash | 0x409d6a6fa0992d74 → 0x9f492cbd1d4a6e34 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff2d0e560418937 / 0x3ff2d0e560418977 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 121

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea353f7ced9169 → 0x3fea353f7ced8169 |
| old/new hash | 0x3655740075519b47 → 0x96c36cd38cbff937 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea353f7ced9169 / 0x3fea353f7ced8169 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 122

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4074b00000000000 → 0x4074b00000000020 |
| old/new hash | 0x6739957bebd6cfa7 → 0x1b45b6a36c7733c7 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4074b00000000000 / 0x4074b00000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 123

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe578d4fdf3b646 → 0x3fe578d4fdf3b666 |
| old/new hash | 0x05c643df75ab601f → 0x613613be0159de3f |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe578d4fdf3b646 / 0x3fe578d4fdf3b666 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 124

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4084d80000000000 → 0x4084d80000000008 |
| old/new hash | 0x64ab7d7d9e4b50df → 0x925be5c3d0463717 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4084d80000000000 / 0x4084d80000000008 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 125

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4068200000000000 → 0x4068200000008000 |
| old/new hash | 0x32467d7e121a915b → 0x8908b855283123db |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4068200000000000 / 0x4068200000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 126

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4073f00000000000 → 0x4073f00000010000 |
| old/new hash | 0x93338b7d2733d8c8 → 0x4c4a534727ec48e1 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4073f00000000000 / 0x4073f00000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 127

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feaa7ef9db22d0e → 0x3feaa7ef9db22d0f |
| old/new hash | 0x8cd04743a4680d1a → 0x95ba94417ceede33 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feaa7ef9db22d0e / 0x3feaa7ef9db22d0f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 128

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407b700000000000 → 0x407b700000008000 |
| old/new hash | 0xe7d5db7f9b1c1500 → 0x3e981656b132a780 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407b700000000000 / 0x407b700000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 129

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd4dd2f1a9fbe77 → 0x3fd4dd2f1a9f9e77 |
| old/new hash | 0x75c0ede3645ecf36 → 0x6162ed78ea391c56 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd4dd2f1a9fbe77 / 0x3fd4dd2f1a9f9e77 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 13

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4085780000000000 → 0x4085780000000800 |
| old/new hash | 0xa436b77f7548c756 → 0x043a0b2d352941ae |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4085780000000000 / 0x4085780000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 130

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407e000000000000 → 0x407e000000001000 |
| old/new hash | 0x488c897eb00729dd → 0xf14510d990fc028d |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407e000000000000 / 0x407e000000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 131

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff347ae147ae148 → 0x3ff347ae147af148 |
| old/new hash | 0x51f7f3bc17a592b7 → 0x4a47516a4fc2b287 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff347ae147ae148 / 0x3ff347ae147af148 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 132

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc24dd2f1a9fbe8 → 0x3fc24dd2f1a9fb68 |
| old/new hash | 0x34e0f09ada4ed3fe → 0x1b50ff57bc0aa37e |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc24dd2f1a9fbe8 / 0x3fc24dd2f1a9fb68 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 133

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feea7ef9db22d0e → 0x3feea7ef9db22d2e |
| old/new hash | 0x8cddc743a47370f6 → 0xb80b1d324cdbd416 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feea7ef9db22d0e / 0x3feea7ef9db22d2e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 134

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4087900000000000 → 0x4087900000000200 |
| old/new hash | 0x7c28637c889fc8fc → 0x06db72912c53d4d6 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4087900000000000 / 0x4087900000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 135

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfdc28f5c28f5c29 → 0xbfdc28f5c28f5c2b |
| old/new hash | 0xf4421e699e872db3 → 0xcf8e294d33ee8bcd |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfdc28f5c28f5c29 / 0xbfdc28f5c28f5c2b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 136

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4077c00000000000 → 0x4077c00000010000 |
| old/new hash | 0x1c93137d74aafa3c → 0xebb23b48131b3075 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4077c00000000000 / 0x4077c00000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 137

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe7c6a7ef9db22d → 0x3fe7c6a7ef9cb22d |
| old/new hash | 0x2dab5e2d80cec5df → 0xce4731fe03e44d32 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe7c6a7ef9db22d / 0x3fe7c6a7ef9cb22d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 138

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083a00000000000 → 0x4083a00000008000 |
| old/new hash | 0xdfb9bb7b9ff7a548 → 0xdc90f6579b29b9c8 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083a00000000000 / 0x4083a00000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 139

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x406b600000000000 → 0x406b600000008000 |
| old/new hash | 0x5e4e8b7f4d8400a0 → 0xb510c656639a9320 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x406b600000000000 / 0x406b600000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 14

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408c900000000000 → 0x408c900000000800 |
| old/new hash | 0x7c17657c8891592f → 0xfb35692ee2207967 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408c900000000000 / 0x408c900000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 140

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4074200000000000 → 0x4074200000010000 |
| old/new hash | 0x32a6257e126c4357 → 0x567c814b24d6e23e |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4074200000000000 / 0x4074200000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 141

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4063200000000000 → 0x4063200000000400 |
| old/new hash | 0x32577b7e12290128 → 0x47a169a759784c94 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4063200000000000 / 0x4063200000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 142

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408cb80000000000 → 0x408cb80000000100 |
| old/new hash | 0x21d30d7bc4809a87 → 0x1b2af1f6f7ab480c |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408cb80000000000 / 0x408cb80000000100 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 143

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fda3d70a3d70a3e → 0x3fda3d70a3d60a3e |
| old/new hash | 0xc5cfa051c69d8295 → 0x17e0685088d8dae8 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fda3d70a3d70a3e / 0x3fda3d70a3d60a3e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 144

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff5eb851eb851ec → 0x3ff5eb851eb851e8 |
| old/new hash | 0xc0b5d28936ea11ea → 0xc977d9de9ca90f36 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff5eb851eb851ec / 0x3ff5eb851eb851e8 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 145

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff204189374bc6b → 0x3ff204189374bd6b |
| old/new hash | 0x440e7c53d1113f36 → 0x9f938b2041d48325 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff204189374bc6b / 0x3ff204189374bd6b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 146

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdced916872b021 → 0x3fdced916872b025 |
| old/new hash | 0xfbbd7550568b133f → 0xfe90e300dba943eb |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdced916872b021 / 0x3fdced916872b025 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 147

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe851eb851eb852 → 0x3fe851eb851eb856 |
| old/new hash | 0x01283ef34de8e00d → 0xaef415a9c60bcd69 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe851eb851eb852 / 0x3fe851eb851eb856 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 148

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4076400000000000 → 0x4076400000002000 |
| old/new hash | 0x7153797fe8ac5965 → 0xc7bf6ac7afe10305 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4076400000000000 / 0x4076400000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 149

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfb53f7ced916872 → 0xbfb53f7ced91e872 |
| old/new hash | 0x1f024d3a1bd68db6 → 0x33e42aa5f3a16036 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfb53f7ced916872 / 0xbfb53f7ced91e872 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 15

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4028000000000000 → 0x4028000000000001 |
| old/new hash | 0x47765d7eaf1b403b → 0x28b17675a4594f2a |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4028000000000000 / 0x4028000000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 150

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3a9fbe76c8b44 → 0x3ff3a9fbe76c8f44 |
| old/new hash | 0x19e3b6add104d051 → 0xc043a53934a244ed |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3a9fbe76c8b44 / 0x3ff3a9fbe76c8f44 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 151

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc45a1cac083127 → 0xbfc45a1cac082127 |
| old/new hash | 0xc3d93981f240c414 → 0x075bea4ebf4380c4 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc45a1cac083127 / 0xbfc45a1cac082127 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 152

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4089900000000000 → 0x4089900000000040 |
| old/new hash | 0x7c06677c8882e962 → 0xe799a9c42f381f22 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4089900000000000 / 0x4089900000000040 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 153

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fec6a7ef9db22d1 → 0x3fec6a7ef9db2251 |
| old/new hash | 0x35eaeffebe07295d → 0x716d1718f75ec6dd |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fec6a7ef9db22d1 / 0x3fec6a7ef9db2251 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 154

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4077f00000000000 → 0x4077f00000000001 |
| old/new hash | 0x9341a37d27403eec → 0xf2fd2877c9f9563d |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4077f00000000000 / 0x4077f00000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 155

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088700000000000 → 0x4088700000020000 |
| old/new hash | 0xe5f72d7f9985d0eb → 0xf0a24517e985ed59 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088700000000000 / 0x4088700000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 156

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083400000000000 → 0x4083400000000002 |
| old/new hash | 0x709fdb7fe8142b68 → 0xddf9e56b5e40f4ca |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083400000000000 / 0x4083400000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 157

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd083126e978d50 → 0x3fd083126e978d70 |
| old/new hash | 0xfb945e2ad7c8c493 → 0x5d2ac9e6a18d89b3 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd083126e978d50 / 0x3fd083126e978d70 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 158

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4084a00000000000 → 0x4084a00000001000 |
| old/new hash | 0xdfd2057ba00cb4e7 → 0xb1a28cd7b9eb2f77 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4084a00000000000 / 0x4084a00000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 159

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe6c3f3e0370cdc → 0x3fe6c3f3e0360cdc |
| old/new hash | 0x537ffdc56fc55129 → 0x5eca082a0baac568 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe6c3f3e0370cdc / 0x3fe6c3f3e0360cdc |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 16

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408b680000000000 → 0x408b680000002000 |
| old/new hash | 0x163f537f23eaa078 → 0x963004c824655118 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408b680000000000 / 0x408b680000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 160

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x40010713f077ccc0 → 0x40010713f077ecc0 |
| old/new hash | 0xb91e8af162431deb → 0x56f8fe9bce3400cb |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x40010713f077ccc0 / 0x40010713f077ecc0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 161

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe1938151a43782 → 0x3fe1938151a43682 |
| old/new hash | 0xa3f198cd1774b0a7 → 0x6f8bf763b1608df4 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe1938151a43782 / 0x3fe1938151a43682 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 162

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff5c78e9f6a93f3 → 0x3ff5c78e9f6ab3f3 |
| old/new hash | 0xe600dd7bf07aa1e1 → 0xb32223d7df4de801 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff5c78e9f6a93f3 / 0x3ff5c78e9f6ab3f3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 163

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe3b7f1737542a3 → 0x3fe3b7f1737542a2 |
| old/new hash | 0x3e72e4197219bab8 → 0xe0c6022b68de1c5d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe3b7f1737542a3 / 0x3fe3b7f1737542a2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 164

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea59d99029ae50 → 0x3fea59d99029a650 |
| old/new hash | 0x1b8aeb881788f7f5 → 0xd9160945dfda861d |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea59d99029ae50 / 0x3fea59d99029a650 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 165

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fc3ac929aa1d758 → 0x3fc3ac929aa15758 |
| old/new hash | 0xcd0fa08786a05b89 → 0xee85ca9caf805b09 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fc3ac929aa1d758 / 0x3fc3ac929aa15758 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 166

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feac5564b662fe0 → 0x3feac5564b662fe1 |
| old/new hash | 0xb45f81aafa7a97ef → 0xc66c7eb94b4316c2 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feac5564b662fe0 / 0x3feac5564b662fe1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 167

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe0c32a8c9b8456 → 0x3fe0c32a8c9b8452 |
| old/new hash | 0x913b221d9ed87250 → 0x8420866c64cac404 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe0c32a8c9b8456 / 0x3fe0c32a8c9b8452 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 168

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff24b524399b2c4 → 0x3ff24b52439932c4 |
| old/new hash | 0xd0df1fb5658a9e85 → 0xe052b1f05acaaa05 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff24b524399b2c4 / 0x3ff24b52439932c4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 169

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3f742917507e9dc9 → 0x3f742917507e9dcd |
| old/new hash | 0xc53b7561c284bcce → 0xaad7d8d3a276964a |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3f742917507e9dc9 / 0x3f742917507e9dcd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 17

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc45a1cac083127 → 0xbfc45a1cac08312f |
| old/new hash | 0xc3d93981f240c414 → 0x34c40dcf50a7446c |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc45a1cac083127 / 0xbfc45a1cac08312f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 170

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fb21dfb9389b525 → 0x3fb21dfb9389b521 |
| old/new hash | 0x79faa50ac2d3430e → 0xd7ee77b59e7006d2 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fb21dfb9389b525 / 0x3fb21dfb9389b521 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 171

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe3b7e0ac7da1ed → 0x3fe3b7e0ac7da16d |
| old/new hash | 0x286c2c2572124e0f → 0x973318d0b8fa938f |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe3b7e0ac7da1ed / 0x3fe3b7e0ac7da16d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 172

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff33aa582dbe7f3 → 0x3ff33aa582dbeff3 |
| old/new hash | 0x18ae6e1790412d19 → 0x90e93eb799d5a021 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff33aa582dbe7f3 / 0x3ff33aa582dbeff3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 173

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe87564302b40f6 → 0x3fe87564302b42f6 |
| old/new hash | 0xcbad2d00c8cdde34 → 0x69edb3bb438aa1f6 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe87564302b40f6 / 0x3fe87564302b42f6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 174

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff2393682730c67 → 0x3ff2393682730c47 |
| old/new hash | 0x988639cab4daedf7 → 0x06f6677b9a18d017 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff2393682730c67 / 0x3ff2393682730c47 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 175

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd72c7b890d5a5c → 0x3fd72c7b890d5a54 |
| old/new hash | 0x4a86b6d8359014ea → 0xb00e36f566bf20c2 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd72c7b890d5a5c / 0x3fd72c7b890d5a54 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 176

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdaffe2a3cea6c2 → 0x3fdaffe2a3cee6c2 |
| old/new hash | 0x4eff158f7e1adb14 → 0xe76ef2d748a83454 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdaffe2a3cea6c2 / 0x3fdaffe2a3cee6c2 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 177

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fcbb56b87379746 → 0x3fcbb56b87379346 |
| old/new hash | 0x1ef53f2ef5e7abb0 → 0x8e3e51ec396156ac |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fcbb56b87379746 / 0x3fcbb56b87379346 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 178

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fa27179bfdf7e82 → 0x3fa27179bfdf7e86 |
| old/new hash | 0x8572dd21d4c624a8 → 0x2842736f3765e70c |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fa27179bfdf7e82 / 0x3fa27179bfdf7e86 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 179

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe36540cc78e9f6 → 0x3fe36540cc78a9f6 |
| old/new hash | 0x4cbae37d5abfd517 → 0x015fc6070ed5d357 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe36540cc78e9f6 / 0x3fe36540cc78a9f6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 18

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff27ef9db22d0e5 → 0x3ff27ef9db22d0a5 |
| old/new hash | 0x8f15d32aa9066231 → 0x749810309c7a0a71 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff27ef9db22d0e5 / 0x3ff27ef9db22d0a5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 180

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3f54c660a201472c → 0x3f54c660a201072c |
| old/new hash | 0x77e0d2637e62245e → 0xcf2963a2d310709e |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3f54c660a201472c / 0x3f54c660a201072c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 181

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff07ed527e52158 → 0x3ff07ed527e5a158 |
| old/new hash | 0x82ea426934da6e4a → 0x9e7dcc4dfa243aca |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff07ed527e52158 / 0x3ff07ed527e5a158 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 182

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff0189df1172ef1 → 0x3ff0189df117aef1 |
| old/new hash | 0xa1f131df4ec607ac → 0x528a39e2e298cf2c |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff0189df1172ef1 / 0x3ff0189df117aef1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 183

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef51eb851eb852 → 0x3fef51eb851eb85a |
| old/new hash | 0x013fbef34dfc986e → 0xdf8f8c05bc90fe26 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef51eb851eb852 / 0x3fef51eb851eb85a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 184

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff0b4b407032980 → 0x3ff0b4b407033980 |
| old/new hash | 0x2c2f53ae57e3fce3 → 0x70a9da02c2e634b3 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff0b4b407032980 / 0x3ff0b4b407033980 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 185

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff0270f3882278d → 0x3ff0270f388227cd |
| old/new hash | 0x1b050936d3d858ba → 0xd803cb798e394c7a |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff0270f3882278d / 0x3ff0270f388227cd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 186

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd757afea3df6dd → 0x3fd757afea3df6cd |
| old/new hash | 0xe8b7d8a45b17e59f → 0x79ba17c920c04b2f |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd757afea3df6dd / 0x3fd757afea3df6cd |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 187

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe3663c74fb549f → 0x3fe3663c74fb548f |
| old/new hash | 0xe9e01748a8efd17f → 0x86622caa215a69cf |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe3663c74fb549f / 0x3fe3663c74fb548f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 188

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe2cf95d4e8fb01 → 0x3fe2cf95d4e9fb01 |
| old/new hash | 0x90d7e54b8ff04c58 → 0x09df5dd717fa4359 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe2cf95d4e8fb01 / 0x3fe2cf95d4e9fb01 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 189

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe5a96d4c33b539 → 0x3fe5a96d4c33b139 |
| old/new hash | 0xf2d5588d59b77030 → 0xa0c26ed1ace93ecc |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe5a96d4c33b539 / 0x3fe5a96d4c33b139 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 19

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea666666666667 → 0x3fea666666666767 |
| old/new hash | 0x931c8c7900ef0861 → 0x152ee8aae162420a |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea666666666667 / 0x3fea666666666767 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 190

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fef35daad601ffc → 0x3fef35daad609ffc |
| old/new hash | 0x2ef41defe806d4d6 → 0xd8c125f376134a56 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fef35daad601ffc / 0x3fef35daad609ffc |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 191

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe85ea24cc68230 → 0x3fe85ea24cc68220 |
| old/new hash | 0x867b5fa942341ffe → 0x3f78354a297a4b6e |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe85ea24cc68230 / 0x3fe85ea24cc68220 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 192

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff0f6577531db45 → 0x3ff0f6577531d945 |
| old/new hash | 0xaae872739d34aec1 → 0x4e211b8eb2cd91f3 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff0f6577531db45 / 0x3ff0f6577531d945 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 193

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdbb645a1cac084 → 0x3fdbb645a1cbc084 |
| old/new hash | 0x5c259c882e030553 → 0xf0d0a4876767e26a |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdbb645a1cac084 / 0x3fdbb645a1cbc084 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 194

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe4c43b2dd377e1 → 0x3fe4c43b2dd377e0 |
| old/new hash | 0x09d88692c84198f9 → 0x8d83fc8b1b08ddfc |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe4c43b2dd377e1 / 0x3fe4c43b2dd377e0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 195

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea94ff0025bfae → 0x3fea94ff0025afae |
| old/new hash | 0x0dc98d3c45f2bb69 → 0x47e0cb16a59b5939 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea94ff0025bfae / 0x3fea94ff0025afae |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 196

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff27a5b0ff10ecc → 0x3ff27a5b0ff10eec |
| old/new hash | 0x1aa420b33faef5ab → 0xa92b7517e66dc9cb |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff27a5b0ff10ecc / 0x3ff27a5b0ff10eec |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 197

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff65a07b352a843 → 0x3ff65a07b352ac43 |
| old/new hash | 0x94e0b8dec35fae45 → 0x32e9405920547eb9 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff65a07b352a843 / 0x3ff65a07b352ac43 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 198

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff624894c447c31 → 0x3ff624894c447c11 |
| old/new hash | 0x43e3025e17a59198 → 0x293c4d312d9ebff8 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff624894c447c31 / 0x3ff624894c447c11 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 199

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd76a0dbad3a603 → 0x3fd76a0dbad3a601 |
| old/new hash | 0x2f565ac2a7460fd6 → 0xfefc43655e26af60 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd76a0dbad3a603 / 0x3fd76a0dbad3a601 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 2

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408d600000000000 → 0x408d600000004000 |
| old/new hash | 0x5b69af7f4b0e8fb6 → 0x5b4a92114c031776 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408d600000000000 / 0x408d600000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 20

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fed99999999999a → 0x3fed99999999989a |
| old/new hash | 0x80ed9d568165d1b6 → 0x3bac813ec9d2496d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fed99999999999a / 0x3fed99999999989a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 200

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdec6c97d8cf399 → 0x3fdec6c97d8ef399 |
| old/new hash | 0xdfe5c06024106328 → 0x89fab3d303c6f5ea |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdec6c97d8cf399 / 0x3fdec6c97d8ef399 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 201

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fedad4f5903a754 → 0x3fedad4f5903a744 |
| old/new hash | 0x54571f536e508ed2 → 0x7e8c82b3870d6c02 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fedad4f5903a754 / 0x3fedad4f5903a744 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 202

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe978a6dacabc53 → 0x3fe978a6dacabcd3 |
| old/new hash | 0x43bb7960b142f00e → 0xb069d04ad9d5088e |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe978a6dacabc53 / 0x3fe978a6dacabcd3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 203

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe359ddc1e7967d → 0x3fe359ddc1e5967d |
| old/new hash | 0x65b9e6d445f800c4 → 0xcdc53c798d2f2e5a |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe359ddc1e7967d / 0x3fe359ddc1e5967d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 204

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff26550870110a1 → 0x3ff26550870111a1 |
| old/new hash | 0xa13fe4101b478542 → 0x3ea6dd12f35a3d4d |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff26550870110a1 / 0x3ff26550870111a1 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 205

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd1d65a14488c61 → 0x3fd1d65a14480c61 |
| old/new hash | 0x1d58adf9676f194a → 0xce05e8cb986a29ca |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd1d65a14488c61 / 0x3fd1d65a14480c61 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 206

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc057d9dba908a3 → 0xbfc057d9dba908e3 |
| old/new hash | 0x74a7ab4456a27331 → 0x38f17641f1398d71 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc057d9dba908a3 / 0xbfc057d9dba908e3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 207

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3feb36eb4e981388 → 0x3feb36eb4e985388 |
| old/new hash | 0x3558e82539bdaecb → 0x36e3314fed90800b |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3feb36eb4e981388 / 0x3feb36eb4e985388 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 208

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fce039abf338716 → 0x3fce039abf338796 |
| old/new hash | 0x686dc05b04d7a20e → 0xeb997eb03155998e |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fce039abf338716 / 0x3fce039abf338796 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 209

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfa5a1cac083126b → 0xbfa5a1cac083136b |
| old/new hash | 0xf00c5f603062f894 → 0x87f389ab2773fbff |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfa5a1cac083126b / 0xbfa5a1cac083136b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 21

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408ea80000000000 → 0x408ea80000000001 |
| old/new hash | 0x9734917b75fae985 → 0xd9da5a78de3dfcc4 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408ea80000000000 / 0x408ea80000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 210

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe59231c64ba94c → 0x3fe59231c64ba94d |
| old/new hash | 0x77519265e47a4cca → 0x564e13e00849bcc7 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe59231c64ba94c / 0x3fe59231c64ba94d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 22

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbf889374bc6a7ef4 → 0xbf889374bc6a7ed4 |
| old/new hash | 0x8890f577cce88ad7 → 0x4c5e607950b14cf7 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbf889374bc6a7ef4 / 0xbf889374bc6a7ed4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 23

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088480000000000 → 0x4088480000008000 |
| old/new hash | 0x2edf657fc3d721d3 → 0x823ba056d70a8b53 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088480000000000 / 0x4088480000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 24

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff70a3d70a3d70a → 0x3ff70a3d70a3d30a |
| old/new hash | 0x82a786134ec89be2 → 0x0bebad66aeab635e |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff70a3d70a3d70a / 0x3ff70a3d70a3d30a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 25

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4053000000000000 → 0x4053000000000001 |
| old/new hash | 0x49037b7eb06c3878 → 0x27f04075a3b59489 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4053000000000000 / 0x4053000000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 26

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407ce00000000000 → 0x407ce00000004000 |
| old/new hash | 0x09df357cd9c713cf → 0x080d180ed94a070f |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407ce00000000000 / 0x407ce00000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 27

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408d900000000000 → 0x408d900000000020 |
| old/new hash | 0x7c147f7c888f4f86 → 0x04e860a2ce773ea6 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408d900000000000 / 0x408d900000000020 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 28

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408d600000000000 → 0x408d600000001000 |
| old/new hash | 0x5b69af7f4b0e8fb6 → 0x340636db6ab35c46 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408d600000000000 / 0x408d600000001000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 29

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407d900000000000 → 0x407d900000000010 |
| old/new hash | 0x7d245f7c89764c56 → 0x59c1300c9d3912a6 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407d900000000000 / 0x407d900000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 3

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdfbe76c8b43958 → 0x3fdfbe76c8b4395a |
| old/new hash | 0xaabe6dc58079665e → 0x0c6a10ab0af0ca34 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdfbe76c8b43958 / 0x3fdfbe76c8b4395a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 30

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc78d4fdf3b645a → 0xbfc78d4fdf3b655a |
| old/new hash | 0xf8fd7234a457a245 → 0x70ba849f7a305ca2 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc78d4fdf3b645a / 0xbfc78d4fdf3b655a |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 31

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408e200000000000 → 0x408e200000000040 |
| old/new hash | 0x3107897e110c01cd → 0xf31ecbc0cfc0d98d |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408e200000000000 / 0x408e200000000040 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 32

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4082500000000000 → 0x4082500000000002 |
| old/new hash | 0xfea07180397948c1 → 0x6bfb7b6bafa7c523 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4082500000000000 / 0x4082500000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 33

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4080c80000000000 → 0x4080c80000000010 |
| old/new hash | 0xd6a0b57d4cdd8a0b → 0x718fa60b87d2d69b |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4080c80000000000 / 0x4080c80000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 34

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4046800000000000 → 0x4046800000002000 |
| old/new hash | 0xf421197c3c4df9b5 → 0x9e700ac676c77b95 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4046800000000000 / 0x4046800000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 35

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4084800000000000 → 0x4084800000008000 |
| old/new hash | 0xf19ae57c3a2887c7 → 0xf53e20583b20ee47 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4084800000000000 / 0x4084800000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 36

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x406d600000000000 → 0x406d600000004000 |
| old/new hash | 0x5e626f7f4d947a16 → 0x5c9152114d192056 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x406d600000000000 / 0x406d600000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 37

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4085380000000000 → 0x4085380000020000 |
| old/new hash | 0x79d7777e3b484316 → 0x5d0c3f1948022734 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4085380000000000 / 0x4085380000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 38

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4089200000000000 → 0x4089200000010000 |
| old/new hash | 0x30fd577e11035852 → 0x57d3bf4b25fa816b |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4089200000000000 / 0x4089200000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 39

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff7ef9db22d0e56 → 0x3ff7ef9db22d0f56 |
| old/new hash | 0xadee6c83e4a86e4e → 0x066ca57c2f128c31 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff7ef9db22d0e56 / 0x3ff7ef9db22d0f56 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 4

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fddb22d0e560419 → 0x3fddb22d0e560411 |
| old/new hash | 0xab182417a3bbbb6d → 0x63c4c97b37b1fbe5 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fddb22d0e560419 / 0x3fddb22d0e560411 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 40

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe37ced916872b0 → 0x3fe37ced916870b0 |
| old/new hash | 0x11f589e366c07171 → 0xc6b3cf4f8e007de3 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe37ced916872b0 / 0x3fe37ced916870b0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 41

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4073600000000000 → 0x4073600000002000 |
| old/new hash | 0x5e9f9b7f4dc872f8 → 0xddb74cc84d8b32d8 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4073600000000000 / 0x4073600000002000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 42

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe2e978d4fdf3b6 → 0x3fe2e978d4fdf3b7 |
| old/new hash | 0x2bbc4b4267a4fe7d → 0x155c4e84fe1a8728 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe2e978d4fdf3b6 / 0x3fe2e978d4fdf3b7 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 43

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4089680000000000 → 0x4089680000004000 |
| old/new hash | 0x16461f7f23f066ca → 0x198e021127c9ca8a |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4089680000000000 / 0x4089680000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 44

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3c6a7ef9db22d → 0x3ff3c6a7ef9db02d |
| old/new hash | 0x2d675e2d8094f913 → 0x08dcdfef815301f5 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3c6a7ef9db22d / 0x3ff3c6a7ef9db02d |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 45

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdbb645a1cac083 → 0x3fdbb645a1cbc083 |
| old/new hash | 0xca471c3024a66694 → 0xa1c98c8e2caed9cd |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdbb645a1cac083 / 0x3fdbb645a1cbc083 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 46

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4086580000000000 → 0x4086580000008000 |
| old/new hash | 0xb5fc31800f61b70d → 0x10246c57285b728d |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4086580000000000 / 0x4086580000008000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 47

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4062800000000000 → 0x4062800000010000 |
| old/new hash | 0xf3a6c17c3be607f1 → 0x17e95d494eac3278 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4062800000000000 / 0x4062800000010000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 48

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4070800000000000 → 0x4070800000020000 |
| old/new hash | 0xf3e3ed7c3c1a00d3 → 0xe50ba51b48ede9a1 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4070800000000000 / 0x4070800000020000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 49

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4081480000000000 → 0x4081480000000200 |
| old/new hash | 0x2ec04f7fc3bc4be2 → 0x6141c691f0817318 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4081480000000000 / 0x4081480000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 5

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407ff00000000000 → 0x407ff00000000400 |
| old/new hash | 0x9326737d272925a4 → 0x536151a3fa33cfb8 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407ff00000000000 / 0x407ff00000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 50

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083180000000000 → 0x4083180000000200 |
| old/new hash | 0x8b8c737ed5539c80 → 0x163f02937906ceda |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083180000000000 / 0x4083180000000200 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 51

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x405e400000000000 → 0x405e400000000800 |
| old/new hash | 0x71a5897fe8f27ebd → 0x46db4d2d5a25b555 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x405e400000000000 / 0x405e400000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 52

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088600000000000 → 0x4088600000000010 |
| old/new hash | 0x5b5f7d7f4b05e63b → 0x24132e0ec2de068b |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088600000000000 / 0x4088600000000010 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 53

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408b400000000000 → 0x408b400000000002 |
| old/new hash | 0x7084ab7fe7fd1220 → 0xdddf356b5e2ab502 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408b400000000000 / 0x408b400000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 54

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbf86872b020c49b4 → 0xbf86872b020c59b4 |
| old/new hash | 0x2b4d12e5fcbf01bf → 0xd414782b4f2fbd2f |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbf86872b020c49b4 / 0xbf86872b020c59b4 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 55

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4086380000000000 → 0x4086380000000004 |
| old/new hash | 0x79d4917e3b46396d → 0x6b0c4da2186b8479 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4086380000000000 / 0x4086380000000004 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 56

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fedb22d0e560419 → 0x3fedb22d0e562419 |
| old/new hash | 0xaae1a417a38d527d → 0x82adb4df4aade69d |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fedb22d0e560419 / 0x3fedb22d0e562419 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 57

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfbd70a3d70a3d70 → 0xbfbd70a3d70abd70 |
| old/new hash | 0x542dffe210b6eca4 → 0x57e46d8caed5e924 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfbd70a3d70a3d70 / 0xbfbd70a3d70abd70 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 58

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fde45a1cac08313 → 0x3fde45a1cac08393 |
| old/new hash | 0x29243d7b4ad46b7e → 0xdd03540e7c3773fe |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fde45a1cac08313 / 0x3fde45a1cac08393 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 59

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088300000000000 → 0x4088300000000400 |
| old/new hash | 0xbb97ed7e5f854cab → 0xd1183ba7a702caa7 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088300000000000 / 0x4088300000000400 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 6

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff1e353f7ced917 → 0x3ff1e353f7cec917 |
| old/new hash | 0xf51e5acf007444aa → 0x91a5b5b97a834d5a |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff1e353f7ced917 / 0x3ff1e353f7cec917 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 60

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4062800000000000 → 0x4062800000004000 |
| old/new hash | 0xf3a6c17c3be607f1 → 0x46922410af6850b1 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4062800000000000 / 0x4062800000004000 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 61

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc26e978d4fdf3b → 0xbfc26e978d4fdf2b |
| old/new hash | 0x543705dacefe2f2f → 0x220928666be50aff |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc26e978d4fdf3b / 0xbfc26e978d4fdf2b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 62

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff076c8b4395810 → 0x3ff076c8b4395830 |
| old/new hash | 0xc250d3f0e1a25b11 → 0x1b4c55bd6758d971 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff076c8b4395810 / 0x3ff076c8b4395830 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 63

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff1645a1cac0831 → 0x3ff1645a1cac0830 |
| old/new hash | 0xeba0286673718008 → 0x2252c561531a5331 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff1645a1cac0831 / 0x3ff1645a1cac0830 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 64

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe010624dd2f1aa → 0x3fe010624dd2f1ea |
| old/new hash | 0xdaff273cdbd56cd4 → 0xe8016189415cb694 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe010624dd2f1aa / 0x3fe010624dd2f1ea |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 65

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x405c800000000000 → 0x405c800000000001 |
| old/new hash | 0xf443157c3c6ad94f → 0x7cd9ee7817da731e |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x405c800000000000 / 0x405c800000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 66

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407da00000000000 → 0x407da00000000080 |
| old/new hash | 0xddc98f7b9e5217e6 → 0x09e10afb0eabb266 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407da00000000000 / 0x407da00000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 67

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fcd916872b020c5 → 0x3fcd916872b060c5 |
| old/new hash | 0x6bea7f97e75fd497 → 0xaa3f69600d51e757 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fcd916872b020c5 / 0x3fcd916872b060c5 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 68

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe970a3d70a3d71 → 0x3fe970a3d70a3c71 |
| old/new hash | 0x4a4296e01e1c1b9d → 0x2ca3865d2cd2abda |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe970a3d70a3d71 / 0x3fe970a3d70a3c71 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 69

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fec3126e978d4fe → 0x3fec3126e978d47e |
| old/new hash | 0x1a0d3d4c7a05b0fe → 0xf73e61fd7025727e |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fec3126e978d4fe / 0x3fec3126e978d47e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 7

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe374bc6a7ef9db → 0x3fe374bc6a7ef99b |
| old/new hash | 0x5b1c1eb54c5065b1 → 0xa595930edd1271f1 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe374bc6a7ef9db / 0x3fe374bc6a7ef99b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 70

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff16c8b43958106 → 0x3ff16c8b43958186 |
| old/new hash | 0xa790433a267b96e1 → 0xe4561e6ec982e261 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff16c8b43958106 / 0x3ff16c8b43958186 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 71

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4073900000000000 → 0x4073900000000001 |
| old/new hash | 0x7d2aab7c897b3928 → 0x08f8707867a66939 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4073900000000000 / 0x4073900000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 72

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fbb22d0e560418a → 0x3fbb22d0e560418e |
| old/new hash | 0x5a192ce0f74a35e9 → 0xea8e565b1bd381bd |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fbb22d0e560418a / 0x3fbb22d0e560418e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 73

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe8395810624dd3 → 0x3fe8395810624df3 |
| old/new hash | 0xefeba2948860e763 → 0xd086fb26bdfe3303 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe8395810624dd3 / 0x3fe8395810624df3 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 74

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4088a80000000000 → 0x4088a80000000002 |
| old/new hash | 0x972d457b75f449b3 → 0xe735e769b179a2a1 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4088a80000000000 / 0x4088a80000000002 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 75

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd3020c49ba5e35 → 0xbfd3020c49b85e35 |
| old/new hash | 0x89c8f4cd6f702e29 → 0x66a08a1386259213 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd3020c49ba5e35 / 0xbfd3020c49b85e35 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 76

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fdb95810624dd2f → 0x3fdb95810624dc2f |
| old/new hash | 0xddbbab1c9eb24ca9 → 0x3ec0d808a94b1e6a |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fdb95810624dd2f / 0x3fdb95810624dc2f |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 77

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fea04189374bc6b → 0x3fea04189376bc6b |
| old/new hash | 0x43bcfc53d0cc0e8e → 0xd6cac19241743a64 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fea04189374bc6b / 0x3fea04189376bc6b |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 78

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff410624dd2f1aa → 0x3ff410624dd2d1aa |
| old/new hash | 0xdad6273cdbb267c0 → 0x779922c942254660 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff410624dd2f1aa / 0x3ff410624dd2d1aa |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 79

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff56c8b43958106 → 0x3ff56c8b43958104 |
| old/new hash | 0xa782c33a26703305 → 0x2a085d1b553e2ec3 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff56c8b43958106 / 0x3ff56c8b43958104 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 8

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4077900000000000 → 0x4077900000000800 |
| old/new hash | 0x7d38437c8986c5cc → 0xfc8c272ee3433f14 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4077900000000000 / 0x4077900000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 80

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfd6e978d4fdf3b6 → 0xbfd6e978d4fdf396 |
| old/new hash | 0x2c00cb4267dfa4c9 → 0x015b9d184393d769 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfd6e978d4fdf3b6 / 0xbfd6e978d4fdf396 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 81

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff17ced916872b0 → 0x3ff17ced916870b0 |
| old/new hash | 0x11c609e36698272f → 0xc676cf4f8dcccfc5 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff17ced916872b0 / 0x3ff17ced916870b0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 82

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff072b020c49ba6 → 0x3ff072b020c499a6 |
| old/new hash | 0x49709f87459ab69f → 0xf0d071259c8ef1ad |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff072b020c49ba6 / 0x3ff072b020c499a6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 83

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4083100000000000 → 0x4083100000000001 |
| old/new hash | 0xd43ecb7eff779458 → 0xb54ad075f48e1089 |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4083100000000000 / 0x4083100000000001 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 84

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fec20c49ba5e354 → 0x3fec20c49ba7e354 |
| old/new hash | 0xe3500f7b87b2b99b → 0x414b99050bf66fa9 |
| source/destination phys tag | src=— / dest=45 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fec20c49ba5e354 / 0x3fec20c49ba7e354 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 85

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3333333333333 → 0x3ff3333333337333 |
| old/new hash | 0x2395234a25b1987f → 0x731b05de965191bf |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3333333333333 / 0x3ff3333333337333 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 86

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe947ae147ae148 → 0x3fe947ae147ae158 |
| old/new hash | 0x524273bc17e4a4b1 → 0x928b30a6533e88e1 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe947ae147ae148 / 0x3fe947ae147ae158 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 87

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff272b020c49ba6 → 0x3ff272b020c4bba6 |
| old/new hash | 0x49699f87459497f1 → 0x4e533725bea81411 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff272b020c49ba6 / 0x3ff272b020c4bba6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 88

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x4049000000000000 → 0x4049000000000800 |
| old/new hash | 0x48b9377eb02d8c72 → 0x1e5b3b2c21bc4eaa |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x4049000000000000 / 0x4049000000000800 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 89

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x408c680000000000 → 0x408c680000000100 |
| old/new hash | 0x16571d7f23fed697 → 0x7ec961f60f0dd77c |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x408c680000000000 / 0x408c680000000100 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 9

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfb2b020c49ba5e3 → 0xbfb2b020c49ba563 |
| old/new hash | 0x9397db6f0e671263 → 0x5db133090e4caee3 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfb2b020c49ba5e3 / 0xbfb2b020c49ba563 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 90

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x407e800000000000 → 0x407e800000000080 |
| old/new hash | 0xf3cf097c3c07d45d → 0x1fe684fbac616edd |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | scvtf / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x407e800000000000 / 0x407e800000000080 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 91

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfc8b4395810624e → 0xbfc8b4395810620e |
| old/new hash | 0x2c8af922c345a673 → 0xc15866ca4b18eeb3 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfc8b4395810624e / 0xbfc8b4395810620e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 92

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff2a7ef9db22d0e → 0x3ff2a7ef9db22d1e |
| old/new hash | 0x8c7e4743a42202f2 → 0xb40b25dffebbcf02 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff2a7ef9db22d0e / 0x3ff2a7ef9db22d1e |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 93

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fee147ae147ae15 → 0x3fee147ae147ae11 |
| old/new hash | 0xb1c2aa7e4140f2a5 → 0x1dfac88a65ba7bd9 |
| source/destination phys tag | src=— / dest=6 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fee147ae147ae15 / 0x3fee147ae147ae11 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 94

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff3ae147ae147ae → 0x3ff3ae147ae147be |
| old/new hash | 0x0b2ceb1bf9e41983 → 0x0c27effc1dbb9153 |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff3ae147ae147ae / 0x3ff3ae147ae147be |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 95

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fe989374bc6a7f0 → 0x3fe989374bc6a7b0 |
| old/new hash | 0x4c4496fa04335471 → 0x5a4768bcfba253b1 |
| source/destination phys tag | src=— / dest=44 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fe989374bc6a7f0 / 0x3fe989374bc6a7b0 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 96

| 项 | 观测值 |
|---|---|
| old/new 值 | 0xbfb3f7ced916872a → 0xbfb3f7ced91687aa |
| old/new hash | 0x6b264432fc5bc39c → 0x93f013398216271c |
| source/destination phys tag | src=— / dest=4 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0xbfb3f7ced916872a / 0xbfb3f7ced91687aa |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 97

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fead916872b020c → 0x3fead916872b022c |
| old/new hash | 0x33ba710dc319d0e1 → 0x95f5daf16de1afc1 |
| source/destination phys tag | src=— / dest=1 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fead916872b020c / 0x3fead916872b022c |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 98

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3fd072b020c49ba6 → 0x3fd072b020c49be6 |
| old/new hash | 0x49039f87453de4bf → 0x6cdec8509882b87f |
| source/destination phys tag | src=— / dest=5 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3fd072b020c49ba6 / 0x3fd072b020c49be6 |
| ready/valid/issued/completion | N/A（本 seed 事件未携带该状态） |

### fault 99

| 项 | 观测值 |
|---|---|
| old/new 值 | 0x3ff1db22d0e56042 → 0x3ff1db22d0e5604a |
| old/new hash | 0xb1900e67ac22f79b → 0x3209dc049b07c223 |
| source/destination phys tag | src=— / dest=46 |
| operand role / lane / width | — / 0 / 64 |
| opClass / FU / FPCR / FPSR | fmadd / — / mant_lo / N/A（事件未携带则不为推测） |
| correct/fault result | 0x3ff1db22d0e56042 / 0x3ff1db22d0e5604a |
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
| 7 | chain_end | — | 1260 | 5 |

### fault 10（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 54 | — |
| 2 | carrier_state | L1 | 55 | 54 |
| 3 | operand_read | L2 | 56 | 55 |
| 4 | execute | L3 | 57 | 56 |
| 5 | prf_writeback | L4 | 58 | 57 |
| 6 | commit | L5 | 59 | 58 |
| 7 | chain_end | — | 1269 | 59 |

### fault 100（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 594 | — |
| 2 | carrier_state | L1 | 595 | 594 |
| 3 | operand_read | L2 | 596 | 595 |
| 4 | execute | L3 | 597 | 596 |
| 5 | prf_writeback | L4 | 598 | 597 |
| 6 | commit | L5 | 599 | 598 |
| 7 | chain_end | — | 1359 | 599 |

### fault 101（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 600 | — |
| 2 | carrier_state | L1 | 601 | 600 |
| 3 | operand_read | L2 | 602 | 601 |
| 4 | execute | L3 | 603 | 602 |
| 5 | prf_writeback | L4 | 604 | 603 |
| 6 | commit | L5 | 605 | 604 |
| 7 | chain_end | — | 1360 | 605 |

### fault 102（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 606 | — |
| 2 | carrier_state | L1 | 607 | 606 |
| 3 | operand_read | L2 | 608 | 607 |
| 4 | execute | L3 | 609 | 608 |
| 5 | prf_writeback | L4 | 610 | 609 |
| 6 | commit | L5 | 611 | 610 |
| 7 | chain_end | — | 1361 | 611 |

### fault 103（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 612 | — |
| 2 | carrier_state | L1 | 613 | 612 |
| 3 | operand_read | L2 | 614 | 613 |
| 4 | execute | L3 | 615 | 614 |
| 5 | prf_writeback | L4 | 616 | 615 |
| 6 | commit | L5 | 617 | 616 |
| 7 | chain_end | — | 1362 | 617 |

### fault 104（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 618 | — |
| 2 | carrier_state | L1 | 619 | 618 |
| 3 | operand_read | L2 | 620 | 619 |
| 4 | execute | L3 | 621 | 620 |
| 5 | prf_writeback | L4 | 622 | 621 |
| 6 | commit | L5 | 623 | 622 |
| 7 | chain_end | — | 1363 | 623 |

### fault 105（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 624 | — |
| 2 | carrier_state | L1 | 625 | 624 |
| 3 | operand_read | L2 | 626 | 625 |
| 4 | execute | L3 | 627 | 626 |
| 5 | prf_writeback | L4 | 628 | 627 |
| 6 | commit | L5 | 629 | 628 |
| 7 | chain_end | — | 1364 | 629 |

### fault 106（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 630 | — |
| 2 | carrier_state | L1 | 631 | 630 |
| 3 | operand_read | L2 | 632 | 631 |
| 4 | execute | L3 | 633 | 632 |
| 5 | prf_writeback | L4 | 634 | 633 |
| 6 | commit | L5 | 635 | 634 |
| 7 | chain_end | — | 1365 | 635 |

### fault 107（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 636 | — |
| 2 | carrier_state | L1 | 637 | 636 |
| 3 | operand_read | L2 | 638 | 637 |
| 4 | execute | L3 | 639 | 638 |
| 5 | prf_writeback | L4 | 640 | 639 |
| 6 | commit | L5 | 641 | 640 |
| 7 | chain_end | — | 1366 | 641 |

### fault 108（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 642 | — |
| 2 | carrier_state | L1 | 643 | 642 |
| 3 | operand_read | L2 | 644 | 643 |
| 4 | execute | L3 | 645 | 644 |
| 5 | prf_writeback | L4 | 646 | 645 |
| 6 | commit | L5 | 647 | 646 |
| 7 | chain_end | — | 1367 | 647 |

### fault 109（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 648 | — |
| 2 | carrier_state | L1 | 649 | 648 |
| 3 | operand_read | L2 | 650 | 649 |
| 4 | execute | L3 | 651 | 650 |
| 5 | prf_writeback | L4 | 652 | 651 |
| 6 | commit | L5 | 653 | 652 |
| 7 | chain_end | — | 1368 | 653 |

### fault 11（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 60 | — |
| 2 | carrier_state | L1 | 61 | 60 |
| 3 | operand_read | L2 | 62 | 61 |
| 4 | execute | L3 | 63 | 62 |
| 5 | prf_writeback | L4 | 64 | 63 |
| 6 | commit | L5 | 65 | 64 |
| 7 | chain_end | — | 1270 | 65 |

### fault 110（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 654 | — |
| 2 | carrier_state | L1 | 655 | 654 |
| 3 | operand_read | L2 | 656 | 655 |
| 4 | execute | L3 | 657 | 656 |
| 5 | prf_writeback | L4 | 658 | 657 |
| 6 | commit | L5 | 659 | 658 |
| 7 | chain_end | — | 1369 | 659 |

### fault 111（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 660 | — |
| 2 | carrier_state | L1 | 661 | 660 |
| 3 | operand_read | L2 | 662 | 661 |
| 4 | execute | L3 | 663 | 662 |
| 5 | prf_writeback | L4 | 664 | 663 |
| 6 | commit | L5 | 665 | 664 |
| 7 | chain_end | — | 1370 | 665 |

### fault 112（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 666 | — |
| 2 | carrier_state | L1 | 667 | 666 |
| 3 | operand_read | L2 | 668 | 667 |
| 4 | execute | L3 | 669 | 668 |
| 5 | prf_writeback | L4 | 670 | 669 |
| 6 | commit | L5 | 671 | 670 |
| 7 | chain_end | — | 1371 | 671 |

### fault 113（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 672 | — |
| 2 | carrier_state | L1 | 673 | 672 |
| 3 | operand_read | L2 | 674 | 673 |
| 4 | execute | L3 | 675 | 674 |
| 5 | prf_writeback | L4 | 676 | 675 |
| 6 | commit | L5 | 677 | 676 |
| 7 | chain_end | — | 1372 | 677 |

### fault 114（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 678 | — |
| 2 | carrier_state | L1 | 679 | 678 |
| 3 | operand_read | L2 | 680 | 679 |
| 4 | execute | L3 | 681 | 680 |
| 5 | prf_writeback | L4 | 682 | 681 |
| 6 | commit | L5 | 683 | 682 |
| 7 | chain_end | — | 1373 | 683 |

### fault 115（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 684 | — |
| 2 | carrier_state | L1 | 685 | 684 |
| 3 | operand_read | L2 | 686 | 685 |
| 4 | execute | L3 | 687 | 686 |
| 5 | prf_writeback | L4 | 688 | 687 |
| 6 | commit | L5 | 689 | 688 |
| 7 | chain_end | — | 1374 | 689 |

### fault 116（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 690 | — |
| 2 | carrier_state | L1 | 691 | 690 |
| 3 | operand_read | L2 | 692 | 691 |
| 4 | execute | L3 | 693 | 692 |
| 5 | prf_writeback | L4 | 694 | 693 |
| 6 | commit | L5 | 695 | 694 |
| 7 | chain_end | — | 1375 | 695 |

### fault 117（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 696 | — |
| 2 | carrier_state | L1 | 697 | 696 |
| 3 | operand_read | L2 | 698 | 697 |
| 4 | execute | L3 | 699 | 698 |
| 5 | prf_writeback | L4 | 700 | 699 |
| 6 | commit | L5 | 701 | 700 |
| 7 | chain_end | — | 1376 | 701 |

### fault 118（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 702 | — |
| 2 | carrier_state | L1 | 703 | 702 |
| 3 | operand_read | L2 | 704 | 703 |
| 4 | execute | L3 | 705 | 704 |
| 5 | prf_writeback | L4 | 706 | 705 |
| 6 | commit | L5 | 707 | 706 |
| 7 | chain_end | — | 1377 | 707 |

### fault 119（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 708 | — |
| 2 | carrier_state | L1 | 709 | 708 |
| 3 | operand_read | L2 | 710 | 709 |
| 4 | execute | L3 | 711 | 710 |
| 5 | prf_writeback | L4 | 712 | 711 |
| 6 | commit | L5 | 713 | 712 |
| 7 | chain_end | — | 1378 | 713 |

### fault 12（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 66 | — |
| 2 | carrier_state | L1 | 67 | 66 |
| 3 | operand_read | L2 | 68 | 67 |
| 4 | execute | L3 | 69 | 68 |
| 5 | prf_writeback | L4 | 70 | 69 |
| 6 | commit | L5 | 71 | 70 |
| 7 | chain_end | — | 1271 | 71 |

### fault 120（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 714 | — |
| 2 | carrier_state | L1 | 715 | 714 |
| 3 | operand_read | L2 | 716 | 715 |
| 4 | execute | L3 | 717 | 716 |
| 5 | prf_writeback | L4 | 718 | 717 |
| 6 | commit | L5 | 719 | 718 |
| 7 | chain_end | — | 1379 | 719 |

### fault 121（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 720 | — |
| 2 | carrier_state | L1 | 721 | 720 |
| 3 | operand_read | L2 | 722 | 721 |
| 4 | execute | L3 | 723 | 722 |
| 5 | prf_writeback | L4 | 724 | 723 |
| 6 | commit | L5 | 725 | 724 |
| 7 | chain_end | — | 1380 | 725 |

### fault 122（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 726 | — |
| 2 | carrier_state | L1 | 727 | 726 |
| 3 | operand_read | L2 | 728 | 727 |
| 4 | execute | L3 | 729 | 728 |
| 5 | prf_writeback | L4 | 730 | 729 |
| 6 | commit | L5 | 731 | 730 |
| 7 | chain_end | — | 1381 | 731 |

### fault 123（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 732 | — |
| 2 | carrier_state | L1 | 733 | 732 |
| 3 | operand_read | L2 | 734 | 733 |
| 4 | execute | L3 | 735 | 734 |
| 5 | prf_writeback | L4 | 736 | 735 |
| 6 | commit | L5 | 737 | 736 |
| 7 | chain_end | — | 1382 | 737 |

### fault 124（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 738 | — |
| 2 | carrier_state | L1 | 739 | 738 |
| 3 | operand_read | L2 | 740 | 739 |
| 4 | execute | L3 | 741 | 740 |
| 5 | prf_writeback | L4 | 742 | 741 |
| 6 | commit | L5 | 743 | 742 |
| 7 | chain_end | — | 1383 | 743 |

### fault 125（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 744 | — |
| 2 | carrier_state | L1 | 745 | 744 |
| 3 | operand_read | L2 | 746 | 745 |
| 4 | execute | L3 | 747 | 746 |
| 5 | prf_writeback | L4 | 748 | 747 |
| 6 | commit | L5 | 749 | 748 |
| 7 | chain_end | — | 1384 | 749 |

### fault 126（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 750 | — |
| 2 | carrier_state | L1 | 751 | 750 |
| 3 | operand_read | L2 | 752 | 751 |
| 4 | execute | L3 | 753 | 752 |
| 5 | prf_writeback | L4 | 754 | 753 |
| 6 | commit | L5 | 755 | 754 |
| 7 | chain_end | — | 1385 | 755 |

### fault 127（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 756 | — |
| 2 | carrier_state | L1 | 757 | 756 |
| 3 | operand_read | L2 | 758 | 757 |
| 4 | execute | L3 | 759 | 758 |
| 5 | prf_writeback | L4 | 760 | 759 |
| 6 | commit | L5 | 761 | 760 |
| 7 | chain_end | — | 1386 | 761 |

### fault 128（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 762 | — |
| 2 | carrier_state | L1 | 763 | 762 |
| 3 | operand_read | L2 | 764 | 763 |
| 4 | execute | L3 | 765 | 764 |
| 5 | prf_writeback | L4 | 766 | 765 |
| 6 | commit | L5 | 767 | 766 |
| 7 | chain_end | — | 1387 | 767 |

### fault 129（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 768 | — |
| 2 | carrier_state | L1 | 769 | 768 |
| 3 | operand_read | L2 | 770 | 769 |
| 4 | execute | L3 | 771 | 770 |
| 5 | prf_writeback | L4 | 772 | 771 |
| 6 | commit | L5 | 773 | 772 |
| 7 | chain_end | — | 1388 | 773 |

### fault 13（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 72 | — |
| 2 | carrier_state | L1 | 73 | 72 |
| 3 | operand_read | L2 | 74 | 73 |
| 4 | execute | L3 | 75 | 74 |
| 5 | prf_writeback | L4 | 76 | 75 |
| 6 | commit | L5 | 77 | 76 |
| 7 | chain_end | — | 1272 | 77 |

### fault 130（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 774 | — |
| 2 | carrier_state | L1 | 775 | 774 |
| 3 | operand_read | L2 | 776 | 775 |
| 4 | execute | L3 | 777 | 776 |
| 5 | prf_writeback | L4 | 778 | 777 |
| 6 | commit | L5 | 779 | 778 |
| 7 | chain_end | — | 1389 | 779 |

### fault 131（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 780 | — |
| 2 | carrier_state | L1 | 781 | 780 |
| 3 | operand_read | L2 | 782 | 781 |
| 4 | execute | L3 | 783 | 782 |
| 5 | prf_writeback | L4 | 784 | 783 |
| 6 | commit | L5 | 785 | 784 |
| 7 | chain_end | — | 1390 | 785 |

### fault 132（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 786 | — |
| 2 | carrier_state | L1 | 787 | 786 |
| 3 | operand_read | L2 | 788 | 787 |
| 4 | execute | L3 | 789 | 788 |
| 5 | prf_writeback | L4 | 790 | 789 |
| 6 | commit | L5 | 791 | 790 |
| 7 | chain_end | — | 1391 | 791 |

### fault 133（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 792 | — |
| 2 | carrier_state | L1 | 793 | 792 |
| 3 | operand_read | L2 | 794 | 793 |
| 4 | execute | L3 | 795 | 794 |
| 5 | prf_writeback | L4 | 796 | 795 |
| 6 | commit | L5 | 797 | 796 |
| 7 | chain_end | — | 1392 | 797 |

### fault 134（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 798 | — |
| 2 | carrier_state | L1 | 799 | 798 |
| 3 | operand_read | L2 | 800 | 799 |
| 4 | execute | L3 | 801 | 800 |
| 5 | prf_writeback | L4 | 802 | 801 |
| 6 | commit | L5 | 803 | 802 |
| 7 | chain_end | — | 1393 | 803 |

### fault 135（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 804 | — |
| 2 | carrier_state | L1 | 805 | 804 |
| 3 | operand_read | L2 | 806 | 805 |
| 4 | execute | L3 | 807 | 806 |
| 5 | prf_writeback | L4 | 808 | 807 |
| 6 | commit | L5 | 809 | 808 |
| 7 | chain_end | — | 1394 | 809 |

### fault 136（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 810 | — |
| 2 | carrier_state | L1 | 811 | 810 |
| 3 | operand_read | L2 | 812 | 811 |
| 4 | execute | L3 | 813 | 812 |
| 5 | prf_writeback | L4 | 814 | 813 |
| 6 | commit | L5 | 815 | 814 |
| 7 | chain_end | — | 1395 | 815 |

### fault 137（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 816 | — |
| 2 | carrier_state | L1 | 817 | 816 |
| 3 | operand_read | L2 | 818 | 817 |
| 4 | execute | L3 | 819 | 818 |
| 5 | prf_writeback | L4 | 820 | 819 |
| 6 | commit | L5 | 821 | 820 |
| 7 | chain_end | — | 1396 | 821 |

### fault 138（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 822 | — |
| 2 | carrier_state | L1 | 823 | 822 |
| 3 | operand_read | L2 | 824 | 823 |
| 4 | execute | L3 | 825 | 824 |
| 5 | prf_writeback | L4 | 826 | 825 |
| 6 | commit | L5 | 827 | 826 |
| 7 | chain_end | — | 1397 | 827 |

### fault 139（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 828 | — |
| 2 | carrier_state | L1 | 829 | 828 |
| 3 | operand_read | L2 | 830 | 829 |
| 4 | execute | L3 | 831 | 830 |
| 5 | prf_writeback | L4 | 832 | 831 |
| 6 | commit | L5 | 833 | 832 |
| 7 | chain_end | — | 1398 | 833 |

### fault 14（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 78 | — |
| 2 | carrier_state | L1 | 79 | 78 |
| 3 | operand_read | L2 | 80 | 79 |
| 4 | execute | L3 | 81 | 80 |
| 5 | prf_writeback | L4 | 82 | 81 |
| 6 | commit | L5 | 83 | 82 |
| 7 | chain_end | — | 1273 | 83 |

### fault 140（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 834 | — |
| 2 | carrier_state | L1 | 835 | 834 |
| 3 | operand_read | L2 | 836 | 835 |
| 4 | execute | L3 | 837 | 836 |
| 5 | prf_writeback | L4 | 838 | 837 |
| 6 | commit | L5 | 839 | 838 |
| 7 | chain_end | — | 1399 | 839 |

### fault 141（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 840 | — |
| 2 | carrier_state | L1 | 841 | 840 |
| 3 | operand_read | L2 | 842 | 841 |
| 4 | execute | L3 | 843 | 842 |
| 5 | prf_writeback | L4 | 844 | 843 |
| 6 | commit | L5 | 845 | 844 |
| 7 | chain_end | — | 1400 | 845 |

### fault 142（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 846 | — |
| 2 | carrier_state | L1 | 847 | 846 |
| 3 | operand_read | L2 | 848 | 847 |
| 4 | execute | L3 | 849 | 848 |
| 5 | prf_writeback | L4 | 850 | 849 |
| 6 | commit | L5 | 851 | 850 |
| 7 | chain_end | — | 1401 | 851 |

### fault 143（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 852 | — |
| 2 | carrier_state | L1 | 853 | 852 |
| 3 | operand_read | L2 | 854 | 853 |
| 4 | execute | L3 | 855 | 854 |
| 5 | prf_writeback | L4 | 856 | 855 |
| 6 | commit | L5 | 857 | 856 |
| 7 | chain_end | — | 1402 | 857 |

### fault 144（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 858 | — |
| 2 | carrier_state | L1 | 859 | 858 |
| 3 | operand_read | L2 | 860 | 859 |
| 4 | execute | L3 | 861 | 860 |
| 5 | prf_writeback | L4 | 862 | 861 |
| 6 | commit | L5 | 863 | 862 |
| 7 | chain_end | — | 1403 | 863 |

### fault 145（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 864 | — |
| 2 | carrier_state | L1 | 865 | 864 |
| 3 | operand_read | L2 | 866 | 865 |
| 4 | execute | L3 | 867 | 866 |
| 5 | prf_writeback | L4 | 868 | 867 |
| 6 | commit | L5 | 869 | 868 |
| 7 | chain_end | — | 1404 | 869 |

### fault 146（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 870 | — |
| 2 | carrier_state | L1 | 871 | 870 |
| 3 | operand_read | L2 | 872 | 871 |
| 4 | execute | L3 | 873 | 872 |
| 5 | prf_writeback | L4 | 874 | 873 |
| 6 | commit | L5 | 875 | 874 |
| 7 | chain_end | — | 1405 | 875 |

### fault 147（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 876 | — |
| 2 | carrier_state | L1 | 877 | 876 |
| 3 | operand_read | L2 | 878 | 877 |
| 4 | execute | L3 | 879 | 878 |
| 5 | prf_writeback | L4 | 880 | 879 |
| 6 | commit | L5 | 881 | 880 |
| 7 | chain_end | — | 1406 | 881 |

### fault 148（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 882 | — |
| 2 | carrier_state | L1 | 883 | 882 |
| 3 | operand_read | L2 | 884 | 883 |
| 4 | execute | L3 | 885 | 884 |
| 5 | prf_writeback | L4 | 886 | 885 |
| 6 | commit | L5 | 887 | 886 |
| 7 | chain_end | — | 1407 | 887 |

### fault 149（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 888 | — |
| 2 | carrier_state | L1 | 889 | 888 |
| 3 | operand_read | L2 | 890 | 889 |
| 4 | execute | L3 | 891 | 890 |
| 5 | prf_writeback | L4 | 892 | 891 |
| 6 | commit | L5 | 893 | 892 |
| 7 | chain_end | — | 1408 | 893 |

### fault 15（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 84 | — |
| 2 | carrier_state | L1 | 85 | 84 |
| 3 | operand_read | L2 | 86 | 85 |
| 4 | execute | L3 | 87 | 86 |
| 5 | prf_writeback | L4 | 88 | 87 |
| 6 | commit | L5 | 89 | 88 |
| 7 | chain_end | — | 1274 | 89 |

### fault 150（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 894 | — |
| 2 | carrier_state | L1 | 895 | 894 |
| 3 | operand_read | L2 | 896 | 895 |
| 4 | execute | L3 | 897 | 896 |
| 5 | prf_writeback | L4 | 898 | 897 |
| 6 | commit | L5 | 899 | 898 |
| 7 | chain_end | — | 1409 | 899 |

### fault 151（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 900 | — |
| 2 | carrier_state | L1 | 901 | 900 |
| 3 | operand_read | L2 | 902 | 901 |
| 4 | execute | L3 | 903 | 902 |
| 5 | prf_writeback | L4 | 904 | 903 |
| 6 | commit | L5 | 905 | 904 |
| 7 | chain_end | — | 1410 | 905 |

### fault 152（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 906 | — |
| 2 | carrier_state | L1 | 907 | 906 |
| 3 | operand_read | L2 | 908 | 907 |
| 4 | execute | L3 | 909 | 908 |
| 5 | prf_writeback | L4 | 910 | 909 |
| 6 | commit | L5 | 911 | 910 |
| 7 | chain_end | — | 1411 | 911 |

### fault 153（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 912 | — |
| 2 | carrier_state | L1 | 913 | 912 |
| 3 | operand_read | L2 | 914 | 913 |
| 4 | execute | L3 | 915 | 914 |
| 5 | prf_writeback | L4 | 916 | 915 |
| 6 | commit | L5 | 917 | 916 |
| 7 | chain_end | — | 1412 | 917 |

### fault 154（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 918 | — |
| 2 | carrier_state | L1 | 919 | 918 |
| 3 | operand_read | L2 | 920 | 919 |
| 4 | execute | L3 | 921 | 920 |
| 5 | prf_writeback | L4 | 922 | 921 |
| 6 | commit | L5 | 923 | 922 |
| 7 | chain_end | — | 1413 | 923 |

### fault 155（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 924 | — |
| 2 | carrier_state | L1 | 925 | 924 |
| 3 | operand_read | L2 | 926 | 925 |
| 4 | execute | L3 | 927 | 926 |
| 5 | prf_writeback | L4 | 928 | 927 |
| 6 | commit | L5 | 929 | 928 |
| 7 | chain_end | — | 1414 | 929 |

### fault 156（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 930 | — |
| 2 | carrier_state | L1 | 931 | 930 |
| 3 | operand_read | L2 | 932 | 931 |
| 4 | execute | L3 | 933 | 932 |
| 5 | prf_writeback | L4 | 934 | 933 |
| 6 | commit | L5 | 935 | 934 |
| 7 | chain_end | — | 1415 | 935 |

### fault 157（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 936 | — |
| 2 | carrier_state | L1 | 937 | 936 |
| 3 | operand_read | L2 | 938 | 937 |
| 4 | execute | L3 | 939 | 938 |
| 5 | prf_writeback | L4 | 940 | 939 |
| 6 | commit | L5 | 941 | 940 |
| 7 | chain_end | — | 1416 | 941 |

### fault 158（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 942 | — |
| 2 | carrier_state | L1 | 943 | 942 |
| 3 | operand_read | L2 | 944 | 943 |
| 4 | execute | L3 | 945 | 944 |
| 5 | prf_writeback | L4 | 946 | 945 |
| 6 | commit | L5 | 947 | 946 |
| 7 | chain_end | — | 1417 | 947 |

### fault 159（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 948 | — |
| 2 | carrier_state | L1 | 949 | 948 |
| 3 | operand_read | L2 | 950 | 949 |
| 4 | execute | L3 | 951 | 950 |
| 5 | prf_writeback | L4 | 952 | 951 |
| 6 | commit | L5 | 953 | 952 |
| 7 | chain_end | — | 1418 | 953 |

### fault 16（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 90 | — |
| 2 | carrier_state | L1 | 91 | 90 |
| 3 | operand_read | L2 | 92 | 91 |
| 4 | execute | L3 | 93 | 92 |
| 5 | prf_writeback | L4 | 94 | 93 |
| 6 | commit | L5 | 95 | 94 |
| 7 | chain_end | — | 1275 | 95 |

### fault 160（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 954 | — |
| 2 | carrier_state | L1 | 955 | 954 |
| 3 | operand_read | L2 | 956 | 955 |
| 4 | execute | L3 | 957 | 956 |
| 5 | prf_writeback | L4 | 958 | 957 |
| 6 | commit | L5 | 959 | 958 |
| 7 | chain_end | — | 1419 | 959 |

### fault 161（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 960 | — |
| 2 | carrier_state | L1 | 961 | 960 |
| 3 | operand_read | L2 | 962 | 961 |
| 4 | execute | L3 | 963 | 962 |
| 5 | prf_writeback | L4 | 964 | 963 |
| 6 | commit | L5 | 965 | 964 |
| 7 | chain_end | — | 1420 | 965 |

### fault 162（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 966 | — |
| 2 | carrier_state | L1 | 967 | 966 |
| 3 | operand_read | L2 | 968 | 967 |
| 4 | execute | L3 | 969 | 968 |
| 5 | prf_writeback | L4 | 970 | 969 |
| 6 | commit | L5 | 971 | 970 |
| 7 | chain_end | — | 1421 | 971 |

### fault 163（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 972 | — |
| 2 | carrier_state | L1 | 973 | 972 |
| 3 | operand_read | L2 | 974 | 973 |
| 4 | execute | L3 | 975 | 974 |
| 5 | prf_writeback | L4 | 976 | 975 |
| 6 | commit | L5 | 977 | 976 |
| 7 | chain_end | — | 1422 | 977 |

### fault 164（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 978 | — |
| 2 | carrier_state | L1 | 979 | 978 |
| 3 | operand_read | L2 | 980 | 979 |
| 4 | execute | L3 | 981 | 980 |
| 5 | prf_writeback | L4 | 982 | 981 |
| 6 | commit | L5 | 983 | 982 |
| 7 | chain_end | — | 1423 | 983 |

### fault 165（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 984 | — |
| 2 | carrier_state | L1 | 985 | 984 |
| 3 | operand_read | L2 | 986 | 985 |
| 4 | execute | L3 | 987 | 986 |
| 5 | prf_writeback | L4 | 988 | 987 |
| 6 | commit | L5 | 989 | 988 |
| 7 | chain_end | — | 1424 | 989 |

### fault 166（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 990 | — |
| 2 | carrier_state | L1 | 991 | 990 |
| 3 | operand_read | L2 | 992 | 991 |
| 4 | execute | L3 | 993 | 992 |
| 5 | prf_writeback | L4 | 994 | 993 |
| 6 | commit | L5 | 995 | 994 |
| 7 | chain_end | — | 1425 | 995 |

### fault 167（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 996 | — |
| 2 | carrier_state | L1 | 997 | 996 |
| 3 | operand_read | L2 | 998 | 997 |
| 4 | execute | L3 | 999 | 998 |
| 5 | prf_writeback | L4 | 1000 | 999 |
| 6 | commit | L5 | 1001 | 1000 |
| 7 | chain_end | — | 1426 | 1001 |

### fault 168（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1002 | — |
| 2 | carrier_state | L1 | 1003 | 1002 |
| 3 | operand_read | L2 | 1004 | 1003 |
| 4 | execute | L3 | 1005 | 1004 |
| 5 | prf_writeback | L4 | 1006 | 1005 |
| 6 | commit | L5 | 1007 | 1006 |
| 7 | chain_end | — | 1427 | 1007 |

### fault 169（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1008 | — |
| 2 | carrier_state | L1 | 1009 | 1008 |
| 3 | operand_read | L2 | 1010 | 1009 |
| 4 | execute | L3 | 1011 | 1010 |
| 5 | prf_writeback | L4 | 1012 | 1011 |
| 6 | commit | L5 | 1013 | 1012 |
| 7 | chain_end | — | 1428 | 1013 |

### fault 17（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 96 | — |
| 2 | carrier_state | L1 | 97 | 96 |
| 3 | operand_read | L2 | 98 | 97 |
| 4 | execute | L3 | 99 | 98 |
| 5 | prf_writeback | L4 | 100 | 99 |
| 6 | commit | L5 | 101 | 100 |
| 7 | chain_end | — | 1276 | 101 |

### fault 170（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1014 | — |
| 2 | carrier_state | L1 | 1015 | 1014 |
| 3 | operand_read | L2 | 1016 | 1015 |
| 4 | execute | L3 | 1017 | 1016 |
| 5 | prf_writeback | L4 | 1018 | 1017 |
| 6 | commit | L5 | 1019 | 1018 |
| 7 | chain_end | — | 1429 | 1019 |

### fault 171（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1020 | — |
| 2 | carrier_state | L1 | 1021 | 1020 |
| 3 | operand_read | L2 | 1022 | 1021 |
| 4 | execute | L3 | 1023 | 1022 |
| 5 | prf_writeback | L4 | 1024 | 1023 |
| 6 | commit | L5 | 1025 | 1024 |
| 7 | chain_end | — | 1430 | 1025 |

### fault 172（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1026 | — |
| 2 | carrier_state | L1 | 1027 | 1026 |
| 3 | operand_read | L2 | 1028 | 1027 |
| 4 | execute | L3 | 1029 | 1028 |
| 5 | prf_writeback | L4 | 1030 | 1029 |
| 6 | commit | L5 | 1031 | 1030 |
| 7 | chain_end | — | 1431 | 1031 |

### fault 173（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1032 | — |
| 2 | carrier_state | L1 | 1033 | 1032 |
| 3 | operand_read | L2 | 1034 | 1033 |
| 4 | execute | L3 | 1035 | 1034 |
| 5 | prf_writeback | L4 | 1036 | 1035 |
| 6 | commit | L5 | 1037 | 1036 |
| 7 | chain_end | — | 1432 | 1037 |

### fault 174（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1038 | — |
| 2 | carrier_state | L1 | 1039 | 1038 |
| 3 | operand_read | L2 | 1040 | 1039 |
| 4 | execute | L3 | 1041 | 1040 |
| 5 | prf_writeback | L4 | 1042 | 1041 |
| 6 | commit | L5 | 1043 | 1042 |
| 7 | chain_end | — | 1433 | 1043 |

### fault 175（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1044 | — |
| 2 | carrier_state | L1 | 1045 | 1044 |
| 3 | operand_read | L2 | 1046 | 1045 |
| 4 | execute | L3 | 1047 | 1046 |
| 5 | prf_writeback | L4 | 1048 | 1047 |
| 6 | commit | L5 | 1049 | 1048 |
| 7 | chain_end | — | 1434 | 1049 |

### fault 176（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1050 | — |
| 2 | carrier_state | L1 | 1051 | 1050 |
| 3 | operand_read | L2 | 1052 | 1051 |
| 4 | execute | L3 | 1053 | 1052 |
| 5 | prf_writeback | L4 | 1054 | 1053 |
| 6 | commit | L5 | 1055 | 1054 |
| 7 | chain_end | — | 1435 | 1055 |

### fault 177（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1056 | — |
| 2 | carrier_state | L1 | 1057 | 1056 |
| 3 | operand_read | L2 | 1058 | 1057 |
| 4 | execute | L3 | 1059 | 1058 |
| 5 | prf_writeback | L4 | 1060 | 1059 |
| 6 | commit | L5 | 1061 | 1060 |
| 7 | chain_end | — | 1436 | 1061 |

### fault 178（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1062 | — |
| 2 | carrier_state | L1 | 1063 | 1062 |
| 3 | operand_read | L2 | 1064 | 1063 |
| 4 | execute | L3 | 1065 | 1064 |
| 5 | prf_writeback | L4 | 1066 | 1065 |
| 6 | commit | L5 | 1067 | 1066 |
| 7 | chain_end | — | 1437 | 1067 |

### fault 179（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1068 | — |
| 2 | carrier_state | L1 | 1069 | 1068 |
| 3 | operand_read | L2 | 1070 | 1069 |
| 4 | execute | L3 | 1071 | 1070 |
| 5 | prf_writeback | L4 | 1072 | 1071 |
| 6 | commit | L5 | 1073 | 1072 |
| 7 | chain_end | — | 1438 | 1073 |

### fault 18（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 102 | — |
| 2 | carrier_state | L1 | 103 | 102 |
| 3 | operand_read | L2 | 104 | 103 |
| 4 | execute | L3 | 105 | 104 |
| 5 | prf_writeback | L4 | 106 | 105 |
| 6 | commit | L5 | 107 | 106 |
| 7 | chain_end | — | 1277 | 107 |

### fault 180（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1074 | — |
| 2 | carrier_state | L1 | 1075 | 1074 |
| 3 | operand_read | L2 | 1076 | 1075 |
| 4 | execute | L3 | 1077 | 1076 |
| 5 | prf_writeback | L4 | 1078 | 1077 |
| 6 | commit | L5 | 1079 | 1078 |
| 7 | chain_end | — | 1439 | 1079 |

### fault 181（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1080 | — |
| 2 | carrier_state | L1 | 1081 | 1080 |
| 3 | operand_read | L2 | 1082 | 1081 |
| 4 | execute | L3 | 1083 | 1082 |
| 5 | prf_writeback | L4 | 1084 | 1083 |
| 6 | commit | L5 | 1085 | 1084 |
| 7 | chain_end | — | 1440 | 1085 |

### fault 182（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1086 | — |
| 2 | carrier_state | L1 | 1087 | 1086 |
| 3 | operand_read | L2 | 1088 | 1087 |
| 4 | execute | L3 | 1089 | 1088 |
| 5 | prf_writeback | L4 | 1090 | 1089 |
| 6 | commit | L5 | 1091 | 1090 |
| 7 | chain_end | — | 1441 | 1091 |

### fault 183（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1092 | — |
| 2 | carrier_state | L1 | 1093 | 1092 |
| 3 | operand_read | L2 | 1094 | 1093 |
| 4 | execute | L3 | 1095 | 1094 |
| 5 | prf_writeback | L4 | 1096 | 1095 |
| 6 | commit | L5 | 1097 | 1096 |
| 7 | chain_end | — | 1442 | 1097 |

### fault 184（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1098 | — |
| 2 | carrier_state | L1 | 1099 | 1098 |
| 3 | operand_read | L2 | 1100 | 1099 |
| 4 | execute | L3 | 1101 | 1100 |
| 5 | prf_writeback | L4 | 1102 | 1101 |
| 6 | commit | L5 | 1103 | 1102 |
| 7 | chain_end | — | 1443 | 1103 |

### fault 185（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1104 | — |
| 2 | carrier_state | L1 | 1105 | 1104 |
| 3 | operand_read | L2 | 1106 | 1105 |
| 4 | execute | L3 | 1107 | 1106 |
| 5 | prf_writeback | L4 | 1108 | 1107 |
| 6 | commit | L5 | 1109 | 1108 |
| 7 | chain_end | — | 1444 | 1109 |

### fault 186（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1110 | — |
| 2 | carrier_state | L1 | 1111 | 1110 |
| 3 | operand_read | L2 | 1112 | 1111 |
| 4 | execute | L3 | 1113 | 1112 |
| 5 | prf_writeback | L4 | 1114 | 1113 |
| 6 | commit | L5 | 1115 | 1114 |
| 7 | chain_end | — | 1445 | 1115 |

### fault 187（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1116 | — |
| 2 | carrier_state | L1 | 1117 | 1116 |
| 3 | operand_read | L2 | 1118 | 1117 |
| 4 | execute | L3 | 1119 | 1118 |
| 5 | prf_writeback | L4 | 1120 | 1119 |
| 6 | commit | L5 | 1121 | 1120 |
| 7 | chain_end | — | 1446 | 1121 |

### fault 188（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1122 | — |
| 2 | carrier_state | L1 | 1123 | 1122 |
| 3 | operand_read | L2 | 1124 | 1123 |
| 4 | execute | L3 | 1125 | 1124 |
| 5 | prf_writeback | L4 | 1126 | 1125 |
| 6 | commit | L5 | 1127 | 1126 |
| 7 | chain_end | — | 1447 | 1127 |

### fault 189（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1128 | — |
| 2 | carrier_state | L1 | 1129 | 1128 |
| 3 | operand_read | L2 | 1130 | 1129 |
| 4 | execute | L3 | 1131 | 1130 |
| 5 | prf_writeback | L4 | 1132 | 1131 |
| 6 | commit | L5 | 1133 | 1132 |
| 7 | chain_end | — | 1448 | 1133 |

### fault 19（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 108 | — |
| 2 | carrier_state | L1 | 109 | 108 |
| 3 | operand_read | L2 | 110 | 109 |
| 4 | execute | L3 | 111 | 110 |
| 5 | prf_writeback | L4 | 112 | 111 |
| 6 | commit | L5 | 113 | 112 |
| 7 | chain_end | — | 1278 | 113 |

### fault 190（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1134 | — |
| 2 | carrier_state | L1 | 1135 | 1134 |
| 3 | operand_read | L2 | 1136 | 1135 |
| 4 | execute | L3 | 1137 | 1136 |
| 5 | prf_writeback | L4 | 1138 | 1137 |
| 6 | commit | L5 | 1139 | 1138 |
| 7 | chain_end | — | 1449 | 1139 |

### fault 191（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1140 | — |
| 2 | carrier_state | L1 | 1141 | 1140 |
| 3 | operand_read | L2 | 1142 | 1141 |
| 4 | execute | L3 | 1143 | 1142 |
| 5 | prf_writeback | L4 | 1144 | 1143 |
| 6 | commit | L5 | 1145 | 1144 |
| 7 | chain_end | — | 1450 | 1145 |

### fault 192（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1146 | — |
| 2 | carrier_state | L1 | 1147 | 1146 |
| 3 | operand_read | L2 | 1148 | 1147 |
| 4 | execute | L3 | 1149 | 1148 |
| 5 | prf_writeback | L4 | 1150 | 1149 |
| 6 | commit | L5 | 1151 | 1150 |
| 7 | chain_end | — | 1451 | 1151 |

### fault 193（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1152 | — |
| 2 | carrier_state | L1 | 1153 | 1152 |
| 3 | operand_read | L2 | 1154 | 1153 |
| 4 | execute | L3 | 1155 | 1154 |
| 5 | prf_writeback | L4 | 1156 | 1155 |
| 6 | commit | L5 | 1157 | 1156 |
| 7 | chain_end | — | 1452 | 1157 |

### fault 194（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1158 | — |
| 2 | carrier_state | L1 | 1159 | 1158 |
| 3 | operand_read | L2 | 1160 | 1159 |
| 4 | execute | L3 | 1161 | 1160 |
| 5 | prf_writeback | L4 | 1162 | 1161 |
| 6 | commit | L5 | 1163 | 1162 |
| 7 | chain_end | — | 1453 | 1163 |

### fault 195（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1164 | — |
| 2 | carrier_state | L1 | 1165 | 1164 |
| 3 | operand_read | L2 | 1166 | 1165 |
| 4 | execute | L3 | 1167 | 1166 |
| 5 | prf_writeback | L4 | 1168 | 1167 |
| 6 | commit | L5 | 1169 | 1168 |
| 7 | chain_end | — | 1454 | 1169 |

### fault 196（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1170 | — |
| 2 | carrier_state | L1 | 1171 | 1170 |
| 3 | operand_read | L2 | 1172 | 1171 |
| 4 | execute | L3 | 1173 | 1172 |
| 5 | prf_writeback | L4 | 1174 | 1173 |
| 6 | commit | L5 | 1175 | 1174 |
| 7 | chain_end | — | 1455 | 1175 |

### fault 197（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1176 | — |
| 2 | carrier_state | L1 | 1177 | 1176 |
| 3 | operand_read | L2 | 1178 | 1177 |
| 4 | execute | L3 | 1179 | 1178 |
| 5 | prf_writeback | L4 | 1180 | 1179 |
| 6 | commit | L5 | 1181 | 1180 |
| 7 | chain_end | — | 1456 | 1181 |

### fault 198（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1182 | — |
| 2 | carrier_state | L1 | 1183 | 1182 |
| 3 | operand_read | L2 | 1184 | 1183 |
| 4 | execute | L3 | 1185 | 1184 |
| 5 | prf_writeback | L4 | 1186 | 1185 |
| 6 | commit | L5 | 1187 | 1186 |
| 7 | chain_end | — | 1457 | 1187 |

### fault 199（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1188 | — |
| 2 | carrier_state | L1 | 1189 | 1188 |
| 3 | operand_read | L2 | 1190 | 1189 |
| 4 | execute | L3 | 1191 | 1190 |
| 5 | prf_writeback | L4 | 1192 | 1191 |
| 6 | commit | L5 | 1193 | 1192 |
| 7 | chain_end | — | 1458 | 1193 |

### fault 2（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 6 | — |
| 2 | carrier_state | L1 | 7 | 6 |
| 3 | operand_read | L2 | 8 | 7 |
| 4 | execute | L3 | 9 | 8 |
| 5 | prf_writeback | L4 | 10 | 9 |
| 6 | commit | L5 | 11 | 10 |
| 7 | chain_end | — | 1261 | 11 |

### fault 20（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 114 | — |
| 2 | carrier_state | L1 | 115 | 114 |
| 3 | operand_read | L2 | 116 | 115 |
| 4 | execute | L3 | 117 | 116 |
| 5 | prf_writeback | L4 | 118 | 117 |
| 6 | commit | L5 | 119 | 118 |
| 7 | chain_end | — | 1279 | 119 |

### fault 200（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1194 | — |
| 2 | carrier_state | L1 | 1195 | 1194 |
| 3 | operand_read | L2 | 1196 | 1195 |
| 4 | execute | L3 | 1197 | 1196 |
| 5 | prf_writeback | L4 | 1198 | 1197 |
| 6 | commit | L5 | 1199 | 1198 |
| 7 | chain_end | — | 1459 | 1199 |

### fault 201（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1200 | — |
| 2 | carrier_state | L1 | 1201 | 1200 |
| 3 | operand_read | L2 | 1202 | 1201 |
| 4 | execute | L3 | 1203 | 1202 |
| 5 | prf_writeback | L4 | 1204 | 1203 |
| 6 | commit | L5 | 1205 | 1204 |
| 7 | chain_end | — | 1460 | 1205 |

### fault 202（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1206 | — |
| 2 | carrier_state | L1 | 1207 | 1206 |
| 3 | operand_read | L2 | 1208 | 1207 |
| 4 | execute | L3 | 1209 | 1208 |
| 5 | prf_writeback | L4 | 1210 | 1209 |
| 6 | commit | L5 | 1211 | 1210 |
| 7 | chain_end | — | 1461 | 1211 |

### fault 203（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1212 | — |
| 2 | carrier_state | L1 | 1213 | 1212 |
| 3 | operand_read | L2 | 1214 | 1213 |
| 4 | execute | L3 | 1215 | 1214 |
| 5 | prf_writeback | L4 | 1216 | 1215 |
| 6 | commit | L5 | 1217 | 1216 |
| 7 | chain_end | — | 1462 | 1217 |

### fault 204（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1218 | — |
| 2 | carrier_state | L1 | 1219 | 1218 |
| 3 | operand_read | L2 | 1220 | 1219 |
| 4 | execute | L3 | 1221 | 1220 |
| 5 | prf_writeback | L4 | 1222 | 1221 |
| 6 | commit | L5 | 1223 | 1222 |
| 7 | chain_end | — | 1463 | 1223 |

### fault 205（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1224 | — |
| 2 | carrier_state | L1 | 1225 | 1224 |
| 3 | operand_read | L2 | 1226 | 1225 |
| 4 | execute | L3 | 1227 | 1226 |
| 5 | prf_writeback | L4 | 1228 | 1227 |
| 6 | commit | L5 | 1229 | 1228 |
| 7 | chain_end | — | 1464 | 1229 |

### fault 206（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1230 | — |
| 2 | carrier_state | L1 | 1231 | 1230 |
| 3 | operand_read | L2 | 1232 | 1231 |
| 4 | execute | L3 | 1233 | 1232 |
| 5 | prf_writeback | L4 | 1234 | 1233 |
| 6 | commit | L5 | 1235 | 1234 |
| 7 | chain_end | — | 1465 | 1235 |

### fault 207（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1236 | — |
| 2 | carrier_state | L1 | 1237 | 1236 |
| 3 | operand_read | L2 | 1238 | 1237 |
| 4 | execute | L3 | 1239 | 1238 |
| 5 | prf_writeback | L4 | 1240 | 1239 |
| 6 | commit | L5 | 1241 | 1240 |
| 7 | chain_end | — | 1466 | 1241 |

### fault 208（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1242 | — |
| 2 | carrier_state | L1 | 1243 | 1242 |
| 3 | operand_read | L2 | 1244 | 1243 |
| 4 | execute | L3 | 1245 | 1244 |
| 5 | prf_writeback | L4 | 1246 | 1245 |
| 6 | commit | L5 | 1247 | 1246 |
| 7 | chain_end | — | 1467 | 1247 |

### fault 209（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1248 | — |
| 2 | carrier_state | L1 | 1249 | 1248 |
| 3 | operand_read | L2 | 1250 | 1249 |
| 4 | execute | L3 | 1251 | 1250 |
| 5 | prf_writeback | L4 | 1252 | 1251 |
| 6 | commit | L5 | 1253 | 1252 |
| 7 | chain_end | — | 1468 | 1253 |

### fault 21（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 120 | — |
| 2 | carrier_state | L1 | 121 | 120 |
| 3 | operand_read | L2 | 122 | 121 |
| 4 | execute | L3 | 123 | 122 |
| 5 | prf_writeback | L4 | 124 | 123 |
| 6 | commit | L5 | 125 | 124 |
| 7 | chain_end | — | 1280 | 125 |

### fault 210（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 1254 | — |
| 2 | carrier_state | L1 | 1255 | 1254 |
| 3 | operand_read | L2 | 1256 | 1255 |
| 4 | execute | L3 | 1257 | 1256 |
| 5 | prf_writeback | L4 | 1258 | 1257 |
| 6 | commit | L5 | 1259 | 1258 |
| 7 | chain_end | — | 1469 | 1259 |

### fault 22（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 126 | — |
| 2 | carrier_state | L1 | 127 | 126 |
| 3 | operand_read | L2 | 128 | 127 |
| 4 | execute | L3 | 129 | 128 |
| 5 | prf_writeback | L4 | 130 | 129 |
| 6 | commit | L5 | 131 | 130 |
| 7 | chain_end | — | 1281 | 131 |

### fault 23（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 132 | — |
| 2 | carrier_state | L1 | 133 | 132 |
| 3 | operand_read | L2 | 134 | 133 |
| 4 | execute | L3 | 135 | 134 |
| 5 | prf_writeback | L4 | 136 | 135 |
| 6 | commit | L5 | 137 | 136 |
| 7 | chain_end | — | 1282 | 137 |

### fault 24（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 138 | — |
| 2 | carrier_state | L1 | 139 | 138 |
| 3 | operand_read | L2 | 140 | 139 |
| 4 | execute | L3 | 141 | 140 |
| 5 | prf_writeback | L4 | 142 | 141 |
| 6 | commit | L5 | 143 | 142 |
| 7 | chain_end | — | 1283 | 143 |

### fault 25（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 144 | — |
| 2 | carrier_state | L1 | 145 | 144 |
| 3 | operand_read | L2 | 146 | 145 |
| 4 | execute | L3 | 147 | 146 |
| 5 | prf_writeback | L4 | 148 | 147 |
| 6 | commit | L5 | 149 | 148 |
| 7 | chain_end | — | 1284 | 149 |

### fault 26（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 150 | — |
| 2 | carrier_state | L1 | 151 | 150 |
| 3 | operand_read | L2 | 152 | 151 |
| 4 | execute | L3 | 153 | 152 |
| 5 | prf_writeback | L4 | 154 | 153 |
| 6 | commit | L5 | 155 | 154 |
| 7 | chain_end | — | 1285 | 155 |

### fault 27（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 156 | — |
| 2 | carrier_state | L1 | 157 | 156 |
| 3 | operand_read | L2 | 158 | 157 |
| 4 | execute | L3 | 159 | 158 |
| 5 | prf_writeback | L4 | 160 | 159 |
| 6 | commit | L5 | 161 | 160 |
| 7 | chain_end | — | 1286 | 161 |

### fault 28（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 162 | — |
| 2 | carrier_state | L1 | 163 | 162 |
| 3 | operand_read | L2 | 164 | 163 |
| 4 | execute | L3 | 165 | 164 |
| 5 | prf_writeback | L4 | 166 | 165 |
| 6 | commit | L5 | 167 | 166 |
| 7 | chain_end | — | 1287 | 167 |

### fault 29（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 168 | — |
| 2 | carrier_state | L1 | 169 | 168 |
| 3 | operand_read | L2 | 170 | 169 |
| 4 | execute | L3 | 171 | 170 |
| 5 | prf_writeback | L4 | 172 | 171 |
| 6 | commit | L5 | 173 | 172 |
| 7 | chain_end | — | 1288 | 173 |

### fault 3（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 12 | — |
| 2 | carrier_state | L1 | 13 | 12 |
| 3 | operand_read | L2 | 14 | 13 |
| 4 | execute | L3 | 15 | 14 |
| 5 | prf_writeback | L4 | 16 | 15 |
| 6 | commit | L5 | 17 | 16 |
| 7 | chain_end | — | 1262 | 17 |

### fault 30（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 174 | — |
| 2 | carrier_state | L1 | 175 | 174 |
| 3 | operand_read | L2 | 176 | 175 |
| 4 | execute | L3 | 177 | 176 |
| 5 | prf_writeback | L4 | 178 | 177 |
| 6 | commit | L5 | 179 | 178 |
| 7 | chain_end | — | 1289 | 179 |

### fault 31（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 180 | — |
| 2 | carrier_state | L1 | 181 | 180 |
| 3 | operand_read | L2 | 182 | 181 |
| 4 | execute | L3 | 183 | 182 |
| 5 | prf_writeback | L4 | 184 | 183 |
| 6 | commit | L5 | 185 | 184 |
| 7 | chain_end | — | 1290 | 185 |

### fault 32（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 186 | — |
| 2 | carrier_state | L1 | 187 | 186 |
| 3 | operand_read | L2 | 188 | 187 |
| 4 | execute | L3 | 189 | 188 |
| 5 | prf_writeback | L4 | 190 | 189 |
| 6 | commit | L5 | 191 | 190 |
| 7 | chain_end | — | 1291 | 191 |

### fault 33（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 192 | — |
| 2 | carrier_state | L1 | 193 | 192 |
| 3 | operand_read | L2 | 194 | 193 |
| 4 | execute | L3 | 195 | 194 |
| 5 | prf_writeback | L4 | 196 | 195 |
| 6 | commit | L5 | 197 | 196 |
| 7 | chain_end | — | 1292 | 197 |

### fault 34（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 198 | — |
| 2 | carrier_state | L1 | 199 | 198 |
| 3 | operand_read | L2 | 200 | 199 |
| 4 | execute | L3 | 201 | 200 |
| 5 | prf_writeback | L4 | 202 | 201 |
| 6 | commit | L5 | 203 | 202 |
| 7 | chain_end | — | 1293 | 203 |

### fault 35（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 204 | — |
| 2 | carrier_state | L1 | 205 | 204 |
| 3 | operand_read | L2 | 206 | 205 |
| 4 | execute | L3 | 207 | 206 |
| 5 | prf_writeback | L4 | 208 | 207 |
| 6 | commit | L5 | 209 | 208 |
| 7 | chain_end | — | 1294 | 209 |

### fault 36（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 210 | — |
| 2 | carrier_state | L1 | 211 | 210 |
| 3 | operand_read | L2 | 212 | 211 |
| 4 | execute | L3 | 213 | 212 |
| 5 | prf_writeback | L4 | 214 | 213 |
| 6 | commit | L5 | 215 | 214 |
| 7 | chain_end | — | 1295 | 215 |

### fault 37（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 216 | — |
| 2 | carrier_state | L1 | 217 | 216 |
| 3 | operand_read | L2 | 218 | 217 |
| 4 | execute | L3 | 219 | 218 |
| 5 | prf_writeback | L4 | 220 | 219 |
| 6 | commit | L5 | 221 | 220 |
| 7 | chain_end | — | 1296 | 221 |

### fault 38（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 222 | — |
| 2 | carrier_state | L1 | 223 | 222 |
| 3 | operand_read | L2 | 224 | 223 |
| 4 | execute | L3 | 225 | 224 |
| 5 | prf_writeback | L4 | 226 | 225 |
| 6 | commit | L5 | 227 | 226 |
| 7 | chain_end | — | 1297 | 227 |

### fault 39（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 228 | — |
| 2 | carrier_state | L1 | 229 | 228 |
| 3 | operand_read | L2 | 230 | 229 |
| 4 | execute | L3 | 231 | 230 |
| 5 | prf_writeback | L4 | 232 | 231 |
| 6 | commit | L5 | 233 | 232 |
| 7 | chain_end | — | 1298 | 233 |

### fault 4（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 18 | — |
| 2 | carrier_state | L1 | 19 | 18 |
| 3 | operand_read | L2 | 20 | 19 |
| 4 | execute | L3 | 21 | 20 |
| 5 | prf_writeback | L4 | 22 | 21 |
| 6 | commit | L5 | 23 | 22 |
| 7 | chain_end | — | 1263 | 23 |

### fault 40（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 234 | — |
| 2 | carrier_state | L1 | 235 | 234 |
| 3 | operand_read | L2 | 236 | 235 |
| 4 | execute | L3 | 237 | 236 |
| 5 | prf_writeback | L4 | 238 | 237 |
| 6 | commit | L5 | 239 | 238 |
| 7 | chain_end | — | 1299 | 239 |

### fault 41（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 240 | — |
| 2 | carrier_state | L1 | 241 | 240 |
| 3 | operand_read | L2 | 242 | 241 |
| 4 | execute | L3 | 243 | 242 |
| 5 | prf_writeback | L4 | 244 | 243 |
| 6 | commit | L5 | 245 | 244 |
| 7 | chain_end | — | 1300 | 245 |

### fault 42（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 246 | — |
| 2 | carrier_state | L1 | 247 | 246 |
| 3 | operand_read | L2 | 248 | 247 |
| 4 | execute | L3 | 249 | 248 |
| 5 | prf_writeback | L4 | 250 | 249 |
| 6 | commit | L5 | 251 | 250 |
| 7 | chain_end | — | 1301 | 251 |

### fault 43（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 252 | — |
| 2 | carrier_state | L1 | 253 | 252 |
| 3 | operand_read | L2 | 254 | 253 |
| 4 | execute | L3 | 255 | 254 |
| 5 | prf_writeback | L4 | 256 | 255 |
| 6 | commit | L5 | 257 | 256 |
| 7 | chain_end | — | 1302 | 257 |

### fault 44（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 258 | — |
| 2 | carrier_state | L1 | 259 | 258 |
| 3 | operand_read | L2 | 260 | 259 |
| 4 | execute | L3 | 261 | 260 |
| 5 | prf_writeback | L4 | 262 | 261 |
| 6 | commit | L5 | 263 | 262 |
| 7 | chain_end | — | 1303 | 263 |

### fault 45（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 264 | — |
| 2 | carrier_state | L1 | 265 | 264 |
| 3 | operand_read | L2 | 266 | 265 |
| 4 | execute | L3 | 267 | 266 |
| 5 | prf_writeback | L4 | 268 | 267 |
| 6 | commit | L5 | 269 | 268 |
| 7 | chain_end | — | 1304 | 269 |

### fault 46（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 270 | — |
| 2 | carrier_state | L1 | 271 | 270 |
| 3 | operand_read | L2 | 272 | 271 |
| 4 | execute | L3 | 273 | 272 |
| 5 | prf_writeback | L4 | 274 | 273 |
| 6 | commit | L5 | 275 | 274 |
| 7 | chain_end | — | 1305 | 275 |

### fault 47（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 276 | — |
| 2 | carrier_state | L1 | 277 | 276 |
| 3 | operand_read | L2 | 278 | 277 |
| 4 | execute | L3 | 279 | 278 |
| 5 | prf_writeback | L4 | 280 | 279 |
| 6 | commit | L5 | 281 | 280 |
| 7 | chain_end | — | 1306 | 281 |

### fault 48（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 282 | — |
| 2 | carrier_state | L1 | 283 | 282 |
| 3 | operand_read | L2 | 284 | 283 |
| 4 | execute | L3 | 285 | 284 |
| 5 | prf_writeback | L4 | 286 | 285 |
| 6 | commit | L5 | 287 | 286 |
| 7 | chain_end | — | 1307 | 287 |

### fault 49（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 288 | — |
| 2 | carrier_state | L1 | 289 | 288 |
| 3 | operand_read | L2 | 290 | 289 |
| 4 | execute | L3 | 291 | 290 |
| 5 | prf_writeback | L4 | 292 | 291 |
| 6 | commit | L5 | 293 | 292 |
| 7 | chain_end | — | 1308 | 293 |

### fault 5（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 24 | — |
| 2 | carrier_state | L1 | 25 | 24 |
| 3 | operand_read | L2 | 26 | 25 |
| 4 | execute | L3 | 27 | 26 |
| 5 | prf_writeback | L4 | 28 | 27 |
| 6 | commit | L5 | 29 | 28 |
| 7 | chain_end | — | 1264 | 29 |

### fault 50（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 294 | — |
| 2 | carrier_state | L1 | 295 | 294 |
| 3 | operand_read | L2 | 296 | 295 |
| 4 | execute | L3 | 297 | 296 |
| 5 | prf_writeback | L4 | 298 | 297 |
| 6 | commit | L5 | 299 | 298 |
| 7 | chain_end | — | 1309 | 299 |

### fault 51（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 300 | — |
| 2 | carrier_state | L1 | 301 | 300 |
| 3 | operand_read | L2 | 302 | 301 |
| 4 | execute | L3 | 303 | 302 |
| 5 | prf_writeback | L4 | 304 | 303 |
| 6 | commit | L5 | 305 | 304 |
| 7 | chain_end | — | 1310 | 305 |

### fault 52（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 306 | — |
| 2 | carrier_state | L1 | 307 | 306 |
| 3 | operand_read | L2 | 308 | 307 |
| 4 | execute | L3 | 309 | 308 |
| 5 | prf_writeback | L4 | 310 | 309 |
| 6 | commit | L5 | 311 | 310 |
| 7 | chain_end | — | 1311 | 311 |

### fault 53（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 312 | — |
| 2 | carrier_state | L1 | 313 | 312 |
| 3 | operand_read | L2 | 314 | 313 |
| 4 | execute | L3 | 315 | 314 |
| 5 | prf_writeback | L4 | 316 | 315 |
| 6 | commit | L5 | 317 | 316 |
| 7 | chain_end | — | 1312 | 317 |

### fault 54（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 318 | — |
| 2 | carrier_state | L1 | 319 | 318 |
| 3 | operand_read | L2 | 320 | 319 |
| 4 | execute | L3 | 321 | 320 |
| 5 | prf_writeback | L4 | 322 | 321 |
| 6 | commit | L5 | 323 | 322 |
| 7 | chain_end | — | 1313 | 323 |

### fault 55（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 324 | — |
| 2 | carrier_state | L1 | 325 | 324 |
| 3 | operand_read | L2 | 326 | 325 |
| 4 | execute | L3 | 327 | 326 |
| 5 | prf_writeback | L4 | 328 | 327 |
| 6 | commit | L5 | 329 | 328 |
| 7 | chain_end | — | 1314 | 329 |

### fault 56（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 330 | — |
| 2 | carrier_state | L1 | 331 | 330 |
| 3 | operand_read | L2 | 332 | 331 |
| 4 | execute | L3 | 333 | 332 |
| 5 | prf_writeback | L4 | 334 | 333 |
| 6 | commit | L5 | 335 | 334 |
| 7 | chain_end | — | 1315 | 335 |

### fault 57（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 336 | — |
| 2 | carrier_state | L1 | 337 | 336 |
| 3 | operand_read | L2 | 338 | 337 |
| 4 | execute | L3 | 339 | 338 |
| 5 | prf_writeback | L4 | 340 | 339 |
| 6 | commit | L5 | 341 | 340 |
| 7 | chain_end | — | 1316 | 341 |

### fault 58（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 342 | — |
| 2 | carrier_state | L1 | 343 | 342 |
| 3 | operand_read | L2 | 344 | 343 |
| 4 | execute | L3 | 345 | 344 |
| 5 | prf_writeback | L4 | 346 | 345 |
| 6 | commit | L5 | 347 | 346 |
| 7 | chain_end | — | 1317 | 347 |

### fault 59（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 348 | — |
| 2 | carrier_state | L1 | 349 | 348 |
| 3 | operand_read | L2 | 350 | 349 |
| 4 | execute | L3 | 351 | 350 |
| 5 | prf_writeback | L4 | 352 | 351 |
| 6 | commit | L5 | 353 | 352 |
| 7 | chain_end | — | 1318 | 353 |

### fault 6（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 30 | — |
| 2 | carrier_state | L1 | 31 | 30 |
| 3 | operand_read | L2 | 32 | 31 |
| 4 | execute | L3 | 33 | 32 |
| 5 | prf_writeback | L4 | 34 | 33 |
| 6 | commit | L5 | 35 | 34 |
| 7 | chain_end | — | 1265 | 35 |

### fault 60（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 354 | — |
| 2 | carrier_state | L1 | 355 | 354 |
| 3 | operand_read | L2 | 356 | 355 |
| 4 | execute | L3 | 357 | 356 |
| 5 | prf_writeback | L4 | 358 | 357 |
| 6 | commit | L5 | 359 | 358 |
| 7 | chain_end | — | 1319 | 359 |

### fault 61（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 360 | — |
| 2 | carrier_state | L1 | 361 | 360 |
| 3 | operand_read | L2 | 362 | 361 |
| 4 | execute | L3 | 363 | 362 |
| 5 | prf_writeback | L4 | 364 | 363 |
| 6 | commit | L5 | 365 | 364 |
| 7 | chain_end | — | 1320 | 365 |

### fault 62（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 366 | — |
| 2 | carrier_state | L1 | 367 | 366 |
| 3 | operand_read | L2 | 368 | 367 |
| 4 | execute | L3 | 369 | 368 |
| 5 | prf_writeback | L4 | 370 | 369 |
| 6 | commit | L5 | 371 | 370 |
| 7 | chain_end | — | 1321 | 371 |

### fault 63（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 372 | — |
| 2 | carrier_state | L1 | 373 | 372 |
| 3 | operand_read | L2 | 374 | 373 |
| 4 | execute | L3 | 375 | 374 |
| 5 | prf_writeback | L4 | 376 | 375 |
| 6 | commit | L5 | 377 | 376 |
| 7 | chain_end | — | 1322 | 377 |

### fault 64（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 378 | — |
| 2 | carrier_state | L1 | 379 | 378 |
| 3 | operand_read | L2 | 380 | 379 |
| 4 | execute | L3 | 381 | 380 |
| 5 | prf_writeback | L4 | 382 | 381 |
| 6 | commit | L5 | 383 | 382 |
| 7 | chain_end | — | 1323 | 383 |

### fault 65（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 384 | — |
| 2 | carrier_state | L1 | 385 | 384 |
| 3 | operand_read | L2 | 386 | 385 |
| 4 | execute | L3 | 387 | 386 |
| 5 | prf_writeback | L4 | 388 | 387 |
| 6 | commit | L5 | 389 | 388 |
| 7 | chain_end | — | 1324 | 389 |

### fault 66（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 390 | — |
| 2 | carrier_state | L1 | 391 | 390 |
| 3 | operand_read | L2 | 392 | 391 |
| 4 | execute | L3 | 393 | 392 |
| 5 | prf_writeback | L4 | 394 | 393 |
| 6 | commit | L5 | 395 | 394 |
| 7 | chain_end | — | 1325 | 395 |

### fault 67（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 396 | — |
| 2 | carrier_state | L1 | 397 | 396 |
| 3 | operand_read | L2 | 398 | 397 |
| 4 | execute | L3 | 399 | 398 |
| 5 | prf_writeback | L4 | 400 | 399 |
| 6 | commit | L5 | 401 | 400 |
| 7 | chain_end | — | 1326 | 401 |

### fault 68（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 402 | — |
| 2 | carrier_state | L1 | 403 | 402 |
| 3 | operand_read | L2 | 404 | 403 |
| 4 | execute | L3 | 405 | 404 |
| 5 | prf_writeback | L4 | 406 | 405 |
| 6 | commit | L5 | 407 | 406 |
| 7 | chain_end | — | 1327 | 407 |

### fault 69（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 408 | — |
| 2 | carrier_state | L1 | 409 | 408 |
| 3 | operand_read | L2 | 410 | 409 |
| 4 | execute | L3 | 411 | 410 |
| 5 | prf_writeback | L4 | 412 | 411 |
| 6 | commit | L5 | 413 | 412 |
| 7 | chain_end | — | 1328 | 413 |

### fault 7（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 36 | — |
| 2 | carrier_state | L1 | 37 | 36 |
| 3 | operand_read | L2 | 38 | 37 |
| 4 | execute | L3 | 39 | 38 |
| 5 | prf_writeback | L4 | 40 | 39 |
| 6 | commit | L5 | 41 | 40 |
| 7 | chain_end | — | 1266 | 41 |

### fault 70（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 414 | — |
| 2 | carrier_state | L1 | 415 | 414 |
| 3 | operand_read | L2 | 416 | 415 |
| 4 | execute | L3 | 417 | 416 |
| 5 | prf_writeback | L4 | 418 | 417 |
| 6 | commit | L5 | 419 | 418 |
| 7 | chain_end | — | 1329 | 419 |

### fault 71（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 420 | — |
| 2 | carrier_state | L1 | 421 | 420 |
| 3 | operand_read | L2 | 422 | 421 |
| 4 | execute | L3 | 423 | 422 |
| 5 | prf_writeback | L4 | 424 | 423 |
| 6 | commit | L5 | 425 | 424 |
| 7 | chain_end | — | 1330 | 425 |

### fault 72（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 426 | — |
| 2 | carrier_state | L1 | 427 | 426 |
| 3 | operand_read | L2 | 428 | 427 |
| 4 | execute | L3 | 429 | 428 |
| 5 | prf_writeback | L4 | 430 | 429 |
| 6 | commit | L5 | 431 | 430 |
| 7 | chain_end | — | 1331 | 431 |

### fault 73（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 432 | — |
| 2 | carrier_state | L1 | 433 | 432 |
| 3 | operand_read | L2 | 434 | 433 |
| 4 | execute | L3 | 435 | 434 |
| 5 | prf_writeback | L4 | 436 | 435 |
| 6 | commit | L5 | 437 | 436 |
| 7 | chain_end | — | 1332 | 437 |

### fault 74（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 438 | — |
| 2 | carrier_state | L1 | 439 | 438 |
| 3 | operand_read | L2 | 440 | 439 |
| 4 | execute | L3 | 441 | 440 |
| 5 | prf_writeback | L4 | 442 | 441 |
| 6 | commit | L5 | 443 | 442 |
| 7 | chain_end | — | 1333 | 443 |

### fault 75（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 444 | — |
| 2 | carrier_state | L1 | 445 | 444 |
| 3 | operand_read | L2 | 446 | 445 |
| 4 | execute | L3 | 447 | 446 |
| 5 | prf_writeback | L4 | 448 | 447 |
| 6 | commit | L5 | 449 | 448 |
| 7 | chain_end | — | 1334 | 449 |

### fault 76（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 450 | — |
| 2 | carrier_state | L1 | 451 | 450 |
| 3 | operand_read | L2 | 452 | 451 |
| 4 | execute | L3 | 453 | 452 |
| 5 | prf_writeback | L4 | 454 | 453 |
| 6 | commit | L5 | 455 | 454 |
| 7 | chain_end | — | 1335 | 455 |

### fault 77（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 456 | — |
| 2 | carrier_state | L1 | 457 | 456 |
| 3 | operand_read | L2 | 458 | 457 |
| 4 | execute | L3 | 459 | 458 |
| 5 | prf_writeback | L4 | 460 | 459 |
| 6 | commit | L5 | 461 | 460 |
| 7 | chain_end | — | 1336 | 461 |

### fault 78（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 462 | — |
| 2 | carrier_state | L1 | 463 | 462 |
| 3 | operand_read | L2 | 464 | 463 |
| 4 | execute | L3 | 465 | 464 |
| 5 | prf_writeback | L4 | 466 | 465 |
| 6 | commit | L5 | 467 | 466 |
| 7 | chain_end | — | 1337 | 467 |

### fault 79（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 468 | — |
| 2 | carrier_state | L1 | 469 | 468 |
| 3 | operand_read | L2 | 470 | 469 |
| 4 | execute | L3 | 471 | 470 |
| 5 | prf_writeback | L4 | 472 | 471 |
| 6 | commit | L5 | 473 | 472 |
| 7 | chain_end | — | 1338 | 473 |

### fault 8（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 42 | — |
| 2 | carrier_state | L1 | 43 | 42 |
| 3 | operand_read | L2 | 44 | 43 |
| 4 | execute | L3 | 45 | 44 |
| 5 | prf_writeback | L4 | 46 | 45 |
| 6 | commit | L5 | 47 | 46 |
| 7 | chain_end | — | 1267 | 47 |

### fault 80（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 474 | — |
| 2 | carrier_state | L1 | 475 | 474 |
| 3 | operand_read | L2 | 476 | 475 |
| 4 | execute | L3 | 477 | 476 |
| 5 | prf_writeback | L4 | 478 | 477 |
| 6 | commit | L5 | 479 | 478 |
| 7 | chain_end | — | 1339 | 479 |

### fault 81（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 480 | — |
| 2 | carrier_state | L1 | 481 | 480 |
| 3 | operand_read | L2 | 482 | 481 |
| 4 | execute | L3 | 483 | 482 |
| 5 | prf_writeback | L4 | 484 | 483 |
| 6 | commit | L5 | 485 | 484 |
| 7 | chain_end | — | 1340 | 485 |

### fault 82（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 486 | — |
| 2 | carrier_state | L1 | 487 | 486 |
| 3 | operand_read | L2 | 488 | 487 |
| 4 | execute | L3 | 489 | 488 |
| 5 | prf_writeback | L4 | 490 | 489 |
| 6 | commit | L5 | 491 | 490 |
| 7 | chain_end | — | 1341 | 491 |

### fault 83（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 492 | — |
| 2 | carrier_state | L1 | 493 | 492 |
| 3 | operand_read | L2 | 494 | 493 |
| 4 | execute | L3 | 495 | 494 |
| 5 | prf_writeback | L4 | 496 | 495 |
| 6 | commit | L5 | 497 | 496 |
| 7 | chain_end | — | 1342 | 497 |

### fault 84（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 498 | — |
| 2 | carrier_state | L1 | 499 | 498 |
| 3 | operand_read | L2 | 500 | 499 |
| 4 | execute | L3 | 501 | 500 |
| 5 | prf_writeback | L4 | 502 | 501 |
| 6 | commit | L5 | 503 | 502 |
| 7 | chain_end | — | 1343 | 503 |

### fault 85（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 504 | — |
| 2 | carrier_state | L1 | 505 | 504 |
| 3 | operand_read | L2 | 506 | 505 |
| 4 | execute | L3 | 507 | 506 |
| 5 | prf_writeback | L4 | 508 | 507 |
| 6 | commit | L5 | 509 | 508 |
| 7 | chain_end | — | 1344 | 509 |

### fault 86（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 510 | — |
| 2 | carrier_state | L1 | 511 | 510 |
| 3 | operand_read | L2 | 512 | 511 |
| 4 | execute | L3 | 513 | 512 |
| 5 | prf_writeback | L4 | 514 | 513 |
| 6 | commit | L5 | 515 | 514 |
| 7 | chain_end | — | 1345 | 515 |

### fault 87（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 516 | — |
| 2 | carrier_state | L1 | 517 | 516 |
| 3 | operand_read | L2 | 518 | 517 |
| 4 | execute | L3 | 519 | 518 |
| 5 | prf_writeback | L4 | 520 | 519 |
| 6 | commit | L5 | 521 | 520 |
| 7 | chain_end | — | 1346 | 521 |

### fault 88（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 522 | — |
| 2 | carrier_state | L1 | 523 | 522 |
| 3 | operand_read | L2 | 524 | 523 |
| 4 | execute | L3 | 525 | 524 |
| 5 | prf_writeback | L4 | 526 | 525 |
| 6 | commit | L5 | 527 | 526 |
| 7 | chain_end | — | 1347 | 527 |

### fault 89（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 528 | — |
| 2 | carrier_state | L1 | 529 | 528 |
| 3 | operand_read | L2 | 530 | 529 |
| 4 | execute | L3 | 531 | 530 |
| 5 | prf_writeback | L4 | 532 | 531 |
| 6 | commit | L5 | 533 | 532 |
| 7 | chain_end | — | 1348 | 533 |

### fault 9（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 48 | — |
| 2 | carrier_state | L1 | 49 | 48 |
| 3 | operand_read | L2 | 50 | 49 |
| 4 | execute | L3 | 51 | 50 |
| 5 | prf_writeback | L4 | 52 | 51 |
| 6 | commit | L5 | 53 | 52 |
| 7 | chain_end | — | 1268 | 53 |

### fault 90（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 534 | — |
| 2 | carrier_state | L1 | 535 | 534 |
| 3 | operand_read | L2 | 536 | 535 |
| 4 | execute | L3 | 537 | 536 |
| 5 | prf_writeback | L4 | 538 | 537 |
| 6 | commit | L5 | 539 | 538 |
| 7 | chain_end | — | 1349 | 539 |

### fault 91（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 540 | — |
| 2 | carrier_state | L1 | 541 | 540 |
| 3 | operand_read | L2 | 542 | 541 |
| 4 | execute | L3 | 543 | 542 |
| 5 | prf_writeback | L4 | 544 | 543 |
| 6 | commit | L5 | 545 | 544 |
| 7 | chain_end | — | 1350 | 545 |

### fault 92（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 546 | — |
| 2 | carrier_state | L1 | 547 | 546 |
| 3 | operand_read | L2 | 548 | 547 |
| 4 | execute | L3 | 549 | 548 |
| 5 | prf_writeback | L4 | 550 | 549 |
| 6 | commit | L5 | 551 | 550 |
| 7 | chain_end | — | 1351 | 551 |

### fault 93（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 552 | — |
| 2 | carrier_state | L1 | 553 | 552 |
| 3 | operand_read | L2 | 554 | 553 |
| 4 | execute | L3 | 555 | 554 |
| 5 | prf_writeback | L4 | 556 | 555 |
| 6 | commit | L5 | 557 | 556 |
| 7 | chain_end | — | 1352 | 557 |

### fault 94（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 558 | — |
| 2 | carrier_state | L1 | 559 | 558 |
| 3 | operand_read | L2 | 560 | 559 |
| 4 | execute | L3 | 561 | 560 |
| 5 | prf_writeback | L4 | 562 | 561 |
| 6 | commit | L5 | 563 | 562 |
| 7 | chain_end | — | 1353 | 563 |

### fault 95（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 564 | — |
| 2 | carrier_state | L1 | 565 | 564 |
| 3 | operand_read | L2 | 566 | 565 |
| 4 | execute | L3 | 567 | 566 |
| 5 | prf_writeback | L4 | 568 | 567 |
| 6 | commit | L5 | 569 | 568 |
| 7 | chain_end | — | 1354 | 569 |

### fault 96（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 570 | — |
| 2 | carrier_state | L1 | 571 | 570 |
| 3 | operand_read | L2 | 572 | 571 |
| 4 | execute | L3 | 573 | 572 |
| 5 | prf_writeback | L4 | 574 | 573 |
| 6 | commit | L5 | 575 | 574 |
| 7 | chain_end | — | 1355 | 575 |

### fault 97（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 576 | — |
| 2 | carrier_state | L1 | 577 | 576 |
| 3 | operand_read | L2 | 578 | 577 |
| 4 | execute | L3 | 579 | 578 |
| 5 | prf_writeback | L4 | 580 | 579 |
| 6 | commit | L5 | 581 | 580 |
| 7 | chain_end | — | 1356 | 581 |

### fault 98（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 582 | — |
| 2 | carrier_state | L1 | 583 | 582 |
| 3 | operand_read | L2 | 584 | 583 |
| 4 | execute | L3 | 585 | 584 |
| 5 | prf_writeback | L4 | 586 | 585 |
| 6 | commit | L5 | 587 | 586 |
| 7 | chain_end | — | 1357 | 587 |

### fault 99（terminal=full）

| 顺序 | kind | 层级 | event_id | parent_event_id |
|---|---|---|---|---|
| 1 | fault_applied | L0 | 588 | — |
| 2 | carrier_state | L1 | 589 | 588 |
| 3 | operand_read | L2 | 590 | 589 |
| 4 | execute | L3 | 591 | 590 |
| 5 | prf_writeback | L4 | 592 | 591 |
| 6 | commit | L5 | 593 | 592 |
| 7 | chain_end | — | 1358 | 593 |

## 5. 完整主链事件表

| kind | event_id | parent_event_id | tick | fault_id | sn | PC | opcode | producer/consumer | phys tag | src_slot | lane | before→after | detection_layer | outcome | corr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fault_applied | 0 | — | 21019460 | 1 | 45327 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe75c28f5c28f5c→0x3fe75c28f5c28f4c | — | — | origin |
| carrier_state | 1 | 0 | 21019460 | 1 | 45327 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe75c28f5c28f5c→0x3fe75c28f5c28f4c | — | — | fsu_taint |
| operand_read | 2 | 1 | 21043715 | 1 | 45434 | 0x0000000000400654 | fmadd | 45327/45434 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 3 | 2 | 21043715 | 1 | 45434 | 0x0000000000400654 | fmadd | 45327/45434 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 4 | 3 | 21043715 | 1 | 45434 | 0x0000000000400654 | fmadd | 45327/45434 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 5 | 4 | 21044485 | 1 | 45434 | 0x0000000000400654 | fmadd | —/45434 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1260 | 5 | 9405606595 | 1 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 54 | — | 149977520 | 10 | 554581 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4082400000000000→0x4082400000000002 | — | — | origin |
| carrier_state | 55 | 54 | 149977520 | 10 | 554581 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4082400000000000→0x4082400000000002 | — | — | fsu_taint |
| operand_read | 56 | 55 | 149981370 | 10 | 554584 | 0x000000000040065c | fmadd | 554581/554584 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 57 | 56 | 149981370 | 10 | 554584 | 0x000000000040065c | fmadd | 554581/554584 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 58 | 57 | 149981370 | 10 | 554584 | 0x000000000040065c | fmadd | 554581/554584 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 59 | 58 | 149982140 | 10 | 554584 | 0x000000000040065c | fmadd | —/554584 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1269 | 59 | 9405606595 | 10 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 594 | — | 1496905025 | 100 | 5868831 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3feed0e560418937→0x3feed0e560418935 | — | — | origin |
| carrier_state | 595 | 594 | 1496905025 | 100 | 5868831 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3feed0e560418937→0x3feed0e560418935 | — | — | fsu_taint |
| operand_read | 596 | 595 | 1496929280 | 100 | 5868938 | 0x0000000000400654 | fmadd | 5868831/5868938 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 597 | 596 | 1496929280 | 100 | 5868938 | 0x0000000000400654 | fmadd | 5868831/5868938 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 598 | 597 | 1496929280 | 100 | 5868938 | 0x0000000000400654 | fmadd | 5868831/5868938 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 599 | 598 | 1496930050 | 100 | 5868938 | 0x0000000000400654 | fmadd | —/5868938 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1359 | 599 | 9405606595 | 100 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 600 | — | 1508549350 | 101 | 5914370 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fe8189374bc6a7f→0x3fe8189374bc6a5f | — | — | origin |
| carrier_state | 601 | 600 | 1508549350 | 101 | 5914370 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fe8189374bc6a7f→0x3fe8189374bc6a5f | — | — | fsu_taint |
| operand_read | 602 | 601 | 1508584770 | 101 | 5914514 | 0x0000000000400654 | fmadd | 5914370/5914514 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 603 | 602 | 1508584770 | 101 | 5914514 | 0x0000000000400654 | fmadd | 5914370/5914514 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 604 | 603 | 1508584770 | 101 | 5914514 | 0x0000000000400654 | fmadd | 5914370/5914514 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 605 | 604 | 1508585540 | 101 | 5914514 | 0x0000000000400654 | fmadd | —/5914514 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1360 | 605 | 9405606595 | 101 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 606 | — | 1516796820 | 102 | 5947379 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x407e400000000000→0x407e400000004000 | — | — | origin |
| carrier_state | 607 | 606 | 1516796820 | 102 | 5947379 | 0x0000000000400648 | scvtf | —/— | 5 | — | 64@0 | 0x407e400000000000→0x407e400000004000 | — | — | fsu_taint |
| operand_read | 608 | 607 | 1516798745 | 102 | 5947382 | 0x0000000000400654 | fmadd | 5947379/5947382 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 609 | 608 | 1516798745 | 102 | 5947382 | 0x0000000000400654 | fmadd | 5947379/5947382 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 610 | 609 | 1516798745 | 102 | 5947382 | 0x0000000000400654 | fmadd | 5947379/5947382 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 611 | 610 | 1516799515 | 102 | 5947382 | 0x0000000000400654 | fmadd | —/5947382 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1361 | 611 | 9405606595 | 102 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 612 | — | 1524420975 | 103 | 5977479 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fe5374bc6a7ef9e→0x3fe5374bc6a6ef9e | — | — | origin |
| carrier_state | 613 | 612 | 1524420975 | 103 | 5977479 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3fe5374bc6a7ef9e→0x3fe5374bc6a6ef9e | — | — | fsu_taint |
| operand_read | 614 | 613 | 1524445230 | 103 | 5977586 | 0x0000000000400654 | fmadd | 5977479/5977586 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 615 | 614 | 1524445230 | 103 | 5977586 | 0x0000000000400654 | fmadd | 5977479/5977586 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 616 | 615 | 1524445230 | 103 | 5977586 | 0x0000000000400654 | fmadd | 5977479/5977586 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 617 | 616 | 1524446000 | 103 | 5977586 | 0x0000000000400654 | fmadd | —/5977586 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1362 | 617 | 9405606595 | 103 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 618 | — | 1537380075 | 104 | 6028236 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x405cc00000000000→0x405cc00000000080 | — | — | origin |
| carrier_state | 619 | 618 | 1537380075 | 104 | 6028236 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x405cc00000000000→0x405cc00000000080 | — | — | fsu_taint |
| operand_read | 620 | 619 | 1537384310 | 104 | 6028239 | 0x0000000000400658 | fmadd | 6028236/6028239 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 621 | 620 | 1537384310 | 104 | 6028239 | 0x0000000000400658 | fmadd | 6028236/6028239 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 622 | 621 | 1537384310 | 104 | 6028239 | 0x0000000000400658 | fmadd | 6028236/6028239 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 623 | 622 | 1537385080 | 104 | 6028239 | 0x0000000000400658 | fmadd | —/6028239 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1363 | 623 | 9405606595 | 104 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 624 | — | 1556509570 | 105 | 6103799 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4086180000000000→0x4086180000000080 | — | — | origin |
| carrier_state | 625 | 624 | 1556509570 | 105 | 6103799 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4086180000000000→0x4086180000000080 | — | — | fsu_taint |
| operand_read | 626 | 625 | 1556511495 | 105 | 6103802 | 0x0000000000400654 | fmadd | 6103799/6103802 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 627 | 626 | 1556511495 | 105 | 6103802 | 0x0000000000400654 | fmadd | 6103799/6103802 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 628 | 627 | 1556511495 | 105 | 6103802 | 0x0000000000400654 | fmadd | 6103799/6103802 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 629 | 628 | 1556512265 | 105 | 6103802 | 0x0000000000400654 | fmadd | —/6103802 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1364 | 629 | 9405606595 | 105 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 630 | — | 1567278405 | 106 | 6146572 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0xbfc5c28f5c28f5c2→0xbfc5c28f5c28f1c2 | — | — | origin |
| carrier_state | 631 | 630 | 1567278405 | 106 | 6146572 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0xbfc5c28f5c28f5c2→0xbfc5c28f5c28f1c2 | — | — | fsu_taint |
| operand_read | 632 | 631 | 1567293805 | 106 | 6146642 | 0x0000000000400654 | fmadd | 6146572/6146642 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 633 | 632 | 1567293805 | 106 | 6146642 | 0x0000000000400654 | fmadd | 6146572/6146642 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 634 | 633 | 1567293805 | 106 | 6146642 | 0x0000000000400654 | fmadd | 6146572/6146642 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 635 | 634 | 1567294575 | 106 | 6146642 | 0x0000000000400654 | fmadd | —/6146642 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1365 | 635 | 9405606595 | 106 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 636 | — | 1584826320 | 107 | 6215581 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x408c280000000000→0x408c280000008000 | — | — | origin |
| carrier_state | 637 | 636 | 1584826320 | 107 | 6215581 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x408c280000000000→0x408c280000008000 | — | — | fsu_taint |
| operand_read | 638 | 637 | 1584830170 | 107 | 6215584 | 0x000000000040065c | fmadd | 6215581/6215584 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 639 | 638 | 1584830170 | 107 | 6215584 | 0x000000000040065c | fmadd | 6215581/6215584 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 640 | 639 | 1584830170 | 107 | 6215584 | 0x000000000040065c | fmadd | 6215581/6215584 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 641 | 640 | 1584830940 | 107 | 6215584 | 0x000000000040065c | fmadd | —/6215584 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1366 | 641 | 9405606595 | 107 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 642 | — | 1600132380 | 108 | 6275917 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4044000000000000→0x4044000000000400 | — | — | origin |
| carrier_state | 643 | 642 | 1600132380 | 108 | 6275917 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4044000000000000→0x4044000000000400 | — | — | fsu_taint |
| operand_read | 644 | 643 | 1600136230 | 108 | 6275920 | 0x000000000040065c | fmadd | 6275917/6275920 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 645 | 644 | 1600136230 | 108 | 6275920 | 0x000000000040065c | fmadd | 6275917/6275920 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 646 | 645 | 1600136230 | 108 | 6275920 | 0x000000000040065c | fmadd | 6275917/6275920 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 647 | 646 | 1600137000 | 108 | 6275920 | 0x000000000040065c | fmadd | —/6275920 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1367 | 647 | 9405606595 | 108 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 648 | — | 1608108040 | 109 | 6307454 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff795810624dd2f→0x3ff7958106249d2f | — | — | origin |
| carrier_state | 649 | 648 | 1608108040 | 109 | 6307454 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff795810624dd2f→0x3ff7958106249d2f | — | — | fsu_taint |
| operand_read | 650 | 649 | 1608143460 | 109 | 6307598 | 0x0000000000400654 | fmadd | 6307454/6307598 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 651 | 650 | 1608143460 | 109 | 6307598 | 0x0000000000400654 | fmadd | 6307454/6307598 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 652 | 651 | 1608143460 | 109 | 6307598 | 0x0000000000400654 | fmadd | 6307454/6307598 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 653 | 652 | 1608144230 | 109 | 6307598 | 0x0000000000400654 | fmadd | —/6307598 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1368 | 653 | 9405606595 | 109 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 60 | — | 158328555 | 11 | 587524 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd74bc6a7ef9db2→0x3fd74bc6a7ee9db2 | — | — | origin |
| carrier_state | 61 | 60 | 158328555 | 11 | 587524 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd74bc6a7ef9db2→0x3fd74bc6a7ee9db2 | — | — | fsu_taint |
| operand_read | 62 | 61 | 158343955 | 11 | 587594 | 0x0000000000400654 | fmadd | 587524/587594 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 63 | 62 | 158343955 | 11 | 587594 | 0x0000000000400654 | fmadd | 587524/587594 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 64 | 63 | 158343955 | 11 | 587594 | 0x0000000000400654 | fmadd | 587524/587594 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 65 | 64 | 158344725 | 11 | 587594 | 0x0000000000400654 | fmadd | —/587594 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1270 | 65 | 9405606595 | 11 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 654 | — | 1627036180 | 110 | 6382046 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fed810624dd2f1b→0x3fed810624dd2e1b | — | — | origin |
| carrier_state | 655 | 654 | 1627036180 | 110 | 6382046 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fed810624dd2f1b→0x3fed810624dd2e1b | — | — | fsu_taint |
| operand_read | 656 | 655 | 1627071600 | 110 | 6382190 | 0x0000000000400654 | fmadd | 6382046/6382190 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 657 | 656 | 1627071600 | 110 | 6382190 | 0x0000000000400654 | fmadd | 6382046/6382190 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 658 | 657 | 1627071600 | 110 | 6382190 | 0x0000000000400654 | fmadd | 6382046/6382190 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 659 | 658 | 1627072370 | 110 | 6382190 | 0x0000000000400654 | fmadd | —/6382190 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1369 | 659 | 9405606595 | 110 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 660 | — | 1649587170 | 111 | 6470927 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x408e880000000000→0x408e880000000040 | — | — | origin |
| carrier_state | 661 | 660 | 1649587170 | 111 | 6470927 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x408e880000000000→0x408e880000000040 | — | — | fsu_taint |
| operand_read | 662 | 661 | 1649589095 | 111 | 6470930 | 0x0000000000400654 | fmadd | 6470927/6470930 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 663 | 662 | 1649589095 | 111 | 6470930 | 0x0000000000400654 | fmadd | 6470927/6470930 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 664 | 663 | 1649589095 | 111 | 6470930 | 0x0000000000400654 | fmadd | 6470927/6470930 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 665 | 664 | 1649589865 | 111 | 6470930 | 0x0000000000400654 | fmadd | —/6470930 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1370 | 665 | 9405606595 | 111 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 666 | — | 1662645985 | 112 | 6522484 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0x3fca1cac083126ea→0x3fca1cac083126ee | — | — | origin |
| carrier_state | 667 | 666 | 1662645985 | 112 | 6522484 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0x3fca1cac083126ea→0x3fca1cac083126ee | — | — | fsu_taint |
| operand_read | 668 | 667 | 1662661385 | 112 | 6522554 | 0x0000000000400654 | fmadd | 6522484/6522554 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 669 | 668 | 1662661385 | 112 | 6522554 | 0x0000000000400654 | fmadd | 6522484/6522554 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 670 | 669 | 1662661385 | 112 | 6522554 | 0x0000000000400654 | fmadd | 6522484/6522554 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 671 | 670 | 1662662155 | 112 | 6522554 | 0x0000000000400654 | fmadd | —/6522554 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1371 | 671 | 9405606595 | 112 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 672 | — | 1684876655 | 113 | 6610465 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x408e280000000000→0x408e280000010000 | — | — | origin |
| carrier_state | 673 | 672 | 1684876655 | 113 | 6610465 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x408e280000000000→0x408e280000010000 | — | — | fsu_taint |
| operand_read | 674 | 673 | 1684880505 | 113 | 6610468 | 0x000000000040065c | fmadd | 6610465/6610468 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 675 | 674 | 1684880505 | 113 | 6610468 | 0x000000000040065c | fmadd | 6610465/6610468 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 676 | 675 | 1684880505 | 113 | 6610468 | 0x000000000040065c | fmadd | 6610465/6610468 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 677 | 676 | 1684881275 | 113 | 6610468 | 0x000000000040065c | fmadd | —/6610468 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1372 | 677 | 9405606595 | 113 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 678 | — | 1704207890 | 114 | 6686356 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0xbfd3333333333333→0xbfd3333333323333 | — | — | origin |
| carrier_state | 679 | 678 | 1704207890 | 114 | 6686356 | 0x000000000040065c | fmadd | —/— | 44 | — | 64@0 | 0xbfd3333333333333→0xbfd3333333323333 | — | — | fsu_taint |
| operand_read | 680 | 679 | 1704223290 | 114 | 6686426 | 0x0000000000400654 | fmadd | 6686356/6686426 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 681 | 680 | 1704223290 | 114 | 6686426 | 0x0000000000400654 | fmadd | 6686356/6686426 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 682 | 681 | 1704223290 | 114 | 6686426 | 0x0000000000400654 | fmadd | 6686356/6686426 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 683 | 682 | 1704224060 | 114 | 6686426 | 0x0000000000400654 | fmadd | —/6686426 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1373 | 683 | 9405606595 | 114 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 684 | — | 1712900035 | 115 | 6721167 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fe54fdf3b645a1d→0x3fe54fdf3b645a19 | — | — | origin |
| carrier_state | 685 | 684 | 1712900035 | 115 | 6721167 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fe54fdf3b645a1d→0x3fe54fdf3b645a19 | — | — | fsu_taint |
| operand_read | 686 | 685 | 1712924290 | 115 | 6721274 | 0x0000000000400654 | fmadd | 6721167/6721274 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 687 | 686 | 1712924290 | 115 | 6721274 | 0x0000000000400654 | fmadd | 6721167/6721274 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 688 | 687 | 1712924290 | 115 | 6721274 | 0x0000000000400654 | fmadd | 6721167/6721274 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 689 | 688 | 1712925060 | 115 | 6721274 | 0x0000000000400654 | fmadd | —/6721274 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1374 | 689 | 9405606595 | 115 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 690 | — | 1733020905 | 116 | 6800184 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4085600000000000→0x4085600000000400 | — | — | origin |
| carrier_state | 691 | 690 | 1733020905 | 116 | 6800184 | 0x000000000040064c | scvtf | —/— | 5 | — | 64@0 | 0x4085600000000000→0x4085600000000400 | — | — | fsu_taint |
| operand_read | 692 | 691 | 1733025140 | 116 | 6800187 | 0x0000000000400658 | fmadd | 6800184/6800187 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 693 | 692 | 1733025140 | 116 | 6800187 | 0x0000000000400658 | fmadd | 6800184/6800187 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 694 | 693 | 1733025140 | 116 | 6800187 | 0x0000000000400658 | fmadd | 6800184/6800187 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 695 | 694 | 1733025910 | 116 | 6800187 | 0x0000000000400658 | fmadd | —/6800187 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1375 | 695 | 9405606595 | 116 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 696 | — | 1749895840 | 117 | 6866963 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x408d600000000000→0x408d600000000080 | — | — | origin |
| carrier_state | 697 | 696 | 1749895840 | 117 | 6866963 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x408d600000000000→0x408d600000000080 | — | — | fsu_taint |
| operand_read | 698 | 697 | 1749897765 | 117 | 6866966 | 0x0000000000400654 | fmadd | 6866963/6866966 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 699 | 698 | 1749897765 | 117 | 6866966 | 0x0000000000400654 | fmadd | 6866963/6866966 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 700 | 699 | 1749897765 | 117 | 6866966 | 0x0000000000400654 | fmadd | 6866963/6866966 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 701 | 700 | 1749898535 | 117 | 6866966 | 0x0000000000400654 | fmadd | —/6866966 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1376 | 701 | 9405606595 | 117 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 702 | — | 1772224685 | 118 | 6954948 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4074500000000000→0x4074500000010000 | — | — | origin |
| carrier_state | 703 | 702 | 1772224685 | 118 | 6954948 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4074500000000000→0x4074500000010000 | — | — | fsu_taint |
| operand_read | 704 | 703 | 1772228920 | 118 | 6954951 | 0x0000000000400658 | fmadd | 6954948/6954951 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 705 | 704 | 1772228920 | 118 | 6954951 | 0x0000000000400658 | fmadd | 6954948/6954951 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 706 | 705 | 1772228920 | 118 | 6954951 | 0x0000000000400658 | fmadd | 6954948/6954951 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 707 | 706 | 1772229690 | 118 | 6954951 | 0x0000000000400658 | fmadd | —/6954951 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1377 | 707 | 9405606595 | 118 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 708 | — | 1790378590 | 119 | 7026409 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x4082400000000000→0x4082400000004000 | — | — | origin |
| carrier_state | 709 | 708 | 1790378590 | 119 | 7026409 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x4082400000000000→0x4082400000004000 | — | — | fsu_taint |
| operand_read | 710 | 709 | 1790382440 | 119 | 7026412 | 0x000000000040065c | fmadd | 7026409/7026412 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 711 | 710 | 1790382440 | 119 | 7026412 | 0x000000000040065c | fmadd | 7026409/7026412 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 712 | 711 | 1790382440 | 119 | 7026412 | 0x000000000040065c | fmadd | 7026409/7026412 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 713 | 712 | 1790383210 | 119 | 7026412 | 0x000000000040065c | fmadd | —/7026412 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1378 | 713 | 9405606595 | 119 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 66 | — | 167454980 | 12 | 623632 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfc24dd2f1a9fbe7→0xbfc24dd2f1a9f9e7 | — | — | origin |
| carrier_state | 67 | 66 | 167454980 | 12 | 623632 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfc24dd2f1a9fbe7→0xbfc24dd2f1a9f9e7 | — | — | fsu_taint |
| operand_read | 68 | 67 | 167470380 | 12 | 623702 | 0x0000000000400654 | fmadd | 623632/623702 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 69 | 68 | 167470380 | 12 | 623702 | 0x0000000000400654 | fmadd | 623632/623702 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 70 | 69 | 167470380 | 12 | 623702 | 0x0000000000400654 | fmadd | 623632/623702 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 71 | 70 | 167471150 | 12 | 623702 | 0x0000000000400654 | fmadd | —/623702 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1271 | 71 | 9405606595 | 12 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 714 | — | 1805161435 | 120 | 7084982 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff2d0e560418937→0x3ff2d0e560418977 | — | — | origin |
| carrier_state | 715 | 714 | 1805161435 | 120 | 7084982 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff2d0e560418937→0x3ff2d0e560418977 | — | — | fsu_taint |
| operand_read | 716 | 715 | 1805196855 | 120 | 7085126 | 0x0000000000400654 | fmadd | 7084982/7085126 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 717 | 716 | 1805196855 | 120 | 7085126 | 0x0000000000400654 | fmadd | 7084982/7085126 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 718 | 717 | 1805196855 | 120 | 7085126 | 0x0000000000400654 | fmadd | 7084982/7085126 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 719 | 718 | 1805197625 | 120 | 7085126 | 0x0000000000400654 | fmadd | —/7085126 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1379 | 719 | 9405606595 | 120 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 720 | — | 1816887380 | 121 | 7130954 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fea353f7ced9169→0x3fea353f7ced8169 | — | — | origin |
| carrier_state | 721 | 720 | 1816887380 | 121 | 7130954 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fea353f7ced9169→0x3fea353f7ced8169 | — | — | fsu_taint |
| operand_read | 722 | 721 | 1816922800 | 121 | 7131098 | 0x0000000000400654 | fmadd | 7130954/7131098 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 723 | 722 | 1816922800 | 121 | 7131098 | 0x0000000000400654 | fmadd | 7130954/7131098 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 724 | 723 | 1816922800 | 121 | 7131098 | 0x0000000000400654 | fmadd | 7130954/7131098 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 725 | 724 | 1816923570 | 121 | 7131098 | 0x0000000000400654 | fmadd | —/7131098 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1380 | 725 | 9405606595 | 121 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 726 | — | 1828854335 | 122 | 7178615 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4074b00000000000→0x4074b00000000020 | — | — | origin |
| carrier_state | 727 | 726 | 1828854335 | 122 | 7178615 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4074b00000000000→0x4074b00000000020 | — | — | fsu_taint |
| operand_read | 728 | 727 | 1828856260 | 122 | 7178618 | 0x0000000000400654 | fmadd | 7178615/7178618 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 729 | 728 | 1828856260 | 122 | 7178618 | 0x0000000000400654 | fmadd | 7178615/7178618 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 730 | 729 | 1828856260 | 122 | 7178618 | 0x0000000000400654 | fmadd | 7178615/7178618 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 731 | 730 | 1828857030 | 122 | 7178618 | 0x0000000000400654 | fmadd | —/7178618 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1381 | 731 | 9405606595 | 122 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 732 | — | 1850757755 | 123 | 7265055 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fe578d4fdf3b646→0x3fe578d4fdf3b666 | — | — | origin |
| carrier_state | 733 | 732 | 1850757755 | 123 | 7265055 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fe578d4fdf3b646→0x3fe578d4fdf3b666 | — | — | fsu_taint |
| operand_read | 734 | 733 | 1850782010 | 123 | 7265162 | 0x0000000000400654 | fmadd | 7265055/7265162 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 735 | 734 | 1850782010 | 123 | 7265162 | 0x0000000000400654 | fmadd | 7265055/7265162 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 736 | 735 | 1850782010 | 123 | 7265162 | 0x0000000000400654 | fmadd | 7265055/7265162 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 737 | 736 | 1850782780 | 123 | 7265162 | 0x0000000000400654 | fmadd | —/7265162 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1382 | 737 | 9405606595 | 123 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 738 | — | 1869780990 | 124 | 7339896 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4084d80000000000→0x4084d80000000008 | — | — | origin |
| carrier_state | 739 | 738 | 1869780990 | 124 | 7339896 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4084d80000000000→0x4084d80000000008 | — | — | fsu_taint |
| operand_read | 740 | 739 | 1869785225 | 124 | 7339899 | 0x0000000000400658 | fmadd | 7339896/7339899 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 741 | 740 | 1869785225 | 124 | 7339899 | 0x0000000000400658 | fmadd | 7339896/7339899 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 742 | 741 | 1869785225 | 124 | 7339899 | 0x0000000000400658 | fmadd | 7339896/7339899 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 743 | 742 | 1869785995 | 124 | 7339899 | 0x0000000000400658 | fmadd | —/7339899 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1383 | 743 | 9405606595 | 124 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 744 | — | 1887881765 | 125 | 7411068 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4068200000000000→0x4068200000008000 | — | — | origin |
| carrier_state | 745 | 744 | 1887881765 | 125 | 7411068 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4068200000000000→0x4068200000008000 | — | — | fsu_taint |
| operand_read | 746 | 745 | 1887886000 | 125 | 7411071 | 0x0000000000400658 | fmadd | 7411068/7411071 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 747 | 746 | 1887886000 | 125 | 7411071 | 0x0000000000400658 | fmadd | 7411068/7411071 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 748 | 747 | 1887886000 | 125 | 7411071 | 0x0000000000400658 | fmadd | 7411068/7411071 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 749 | 748 | 1887886770 | 125 | 7411071 | 0x0000000000400658 | fmadd | —/7411071 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1384 | 749 | 9405606595 | 125 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 750 | — | 1899328200 | 126 | 7456608 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4073f00000000000→0x4073f00000010000 | — | — | origin |
| carrier_state | 751 | 750 | 1899328200 | 126 | 7456608 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4073f00000000000→0x4073f00000010000 | — | — | fsu_taint |
| operand_read | 752 | 751 | 1899332435 | 126 | 7456611 | 0x0000000000400658 | fmadd | 7456608/7456611 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 753 | 752 | 1899332435 | 126 | 7456611 | 0x0000000000400658 | fmadd | 7456608/7456611 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 754 | 753 | 1899332435 | 126 | 7456611 | 0x0000000000400658 | fmadd | 7456608/7456611 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 755 | 754 | 1899333205 | 126 | 7456611 | 0x0000000000400658 | fmadd | —/7456611 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1385 | 755 | 9405606595 | 126 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 756 | — | 1919514520 | 127 | 7535810 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3feaa7ef9db22d0e→0x3feaa7ef9db22d0f | — | — | origin |
| carrier_state | 757 | 756 | 1919514520 | 127 | 7535810 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3feaa7ef9db22d0e→0x3feaa7ef9db22d0f | — | — | fsu_taint |
| operand_read | 758 | 757 | 1919549940 | 127 | 7535954 | 0x0000000000400654 | fmadd | 7535810/7535954 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 759 | 758 | 1919549940 | 127 | 7535954 | 0x0000000000400654 | fmadd | 7535810/7535954 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 760 | 759 | 1919549940 | 127 | 7535954 | 0x0000000000400654 | fmadd | 7535810/7535954 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 761 | 760 | 1919550710 | 127 | 7535954 | 0x0000000000400654 | fmadd | —/7535954 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1386 | 761 | 9405606595 | 127 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 762 | — | 1940527820 | 128 | 7619149 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x407b700000000000→0x407b700000008000 | — | — | origin |
| carrier_state | 763 | 762 | 1940527820 | 128 | 7619149 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x407b700000000000→0x407b700000008000 | — | — | fsu_taint |
| operand_read | 764 | 763 | 1940531670 | 128 | 7619152 | 0x000000000040065c | fmadd | 7619149/7619152 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 765 | 764 | 1940531670 | 128 | 7619152 | 0x000000000040065c | fmadd | 7619149/7619152 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 766 | 765 | 1940531670 | 128 | 7619152 | 0x000000000040065c | fmadd | 7619149/7619152 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 767 | 766 | 1940532440 | 128 | 7619152 | 0x000000000040065c | fmadd | —/7619152 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1387 | 767 | 9405606595 | 128 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 768 | — | 1948796080 | 129 | 7651336 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd4dd2f1a9fbe77→0x3fd4dd2f1a9f9e77 | — | — | origin |
| carrier_state | 769 | 768 | 1948796080 | 129 | 7651336 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fd4dd2f1a9fbe77→0x3fd4dd2f1a9f9e77 | — | — | fsu_taint |
| operand_read | 770 | 769 | 1948811480 | 129 | 7651406 | 0x0000000000400654 | fmadd | 7651336/7651406 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 771 | 770 | 1948811480 | 129 | 7651406 | 0x0000000000400654 | fmadd | 7651336/7651406 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 772 | 771 | 1948811480 | 129 | 7651406 | 0x0000000000400654 | fmadd | 7651336/7651406 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 773 | 772 | 1948812250 | 129 | 7651406 | 0x0000000000400654 | fmadd | —/7651406 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1388 | 773 | 9405606595 | 129 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 72 | — | 178149510 | 13 | 665784 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4085780000000000→0x4085780000000800 | — | — | origin |
| carrier_state | 73 | 72 | 178149510 | 13 | 665784 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4085780000000000→0x4085780000000800 | — | — | fsu_taint |
| operand_read | 74 | 73 | 178153745 | 13 | 665787 | 0x0000000000400658 | fmadd | 665784/665787 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 75 | 74 | 178153745 | 13 | 665787 | 0x0000000000400658 | fmadd | 665784/665787 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 76 | 75 | 178153745 | 13 | 665787 | 0x0000000000400658 | fmadd | 665784/665787 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 77 | 76 | 178154515 | 13 | 665787 | 0x0000000000400658 | fmadd | —/665787 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1272 | 77 | 9405606595 | 13 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 774 | — | 1957945220 | 130 | 7687549 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x407e000000000000→0x407e000000001000 | — | — | origin |
| carrier_state | 775 | 774 | 1957945220 | 130 | 7687549 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x407e000000000000→0x407e000000001000 | — | — | fsu_taint |
| operand_read | 776 | 775 | 1957949070 | 130 | 7687552 | 0x000000000040065c | fmadd | 7687549/7687552 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 777 | 776 | 1957949070 | 130 | 7687552 | 0x000000000040065c | fmadd | 7687549/7687552 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 778 | 777 | 1957949070 | 130 | 7687552 | 0x000000000040065c | fmadd | 7687549/7687552 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 779 | 778 | 1957949840 | 130 | 7687552 | 0x000000000040065c | fmadd | —/7687552 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1389 | 779 | 9405606595 | 130 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 780 | — | 1968200080 | 131 | 7728231 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff347ae147ae148→0x3ff347ae147af148 | — | — | origin |
| carrier_state | 781 | 780 | 1968200080 | 131 | 7728231 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff347ae147ae148→0x3ff347ae147af148 | — | — | fsu_taint |
| operand_read | 782 | 781 | 1968224335 | 131 | 7728338 | 0x0000000000400654 | fmadd | 7728231/7728338 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 783 | 782 | 1968224335 | 131 | 7728338 | 0x0000000000400654 | fmadd | 7728231/7728338 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 784 | 783 | 1968224335 | 131 | 7728338 | 0x0000000000400654 | fmadd | 7728231/7728338 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 785 | 784 | 1968225105 | 131 | 7728338 | 0x0000000000400654 | fmadd | —/7728338 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1390 | 785 | 9405606595 | 131 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 786 | — | 1990798425 | 132 | 7817404 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fc24dd2f1a9fbe8→0x3fc24dd2f1a9fb68 | — | — | origin |
| carrier_state | 787 | 786 | 1990798425 | 132 | 7817404 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fc24dd2f1a9fbe8→0x3fc24dd2f1a9fb68 | — | — | fsu_taint |
| operand_read | 788 | 787 | 1990813825 | 132 | 7817474 | 0x0000000000400654 | fmadd | 7817404/7817474 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 789 | 788 | 1990813825 | 132 | 7817474 | 0x0000000000400654 | fmadd | 7817404/7817474 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 790 | 789 | 1990813825 | 132 | 7817474 | 0x0000000000400654 | fmadd | 7817404/7817474 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 791 | 790 | 1990814595 | 132 | 7817474 | 0x0000000000400654 | fmadd | —/7817474 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1391 | 791 | 9405606595 | 132 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 792 | — | 2005833830 | 133 | 7876695 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3feea7ef9db22d0e→0x3feea7ef9db22d2e | — | — | origin |
| carrier_state | 793 | 792 | 2005833830 | 133 | 7876695 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3feea7ef9db22d0e→0x3feea7ef9db22d2e | — | — | fsu_taint |
| operand_read | 794 | 793 | 2005858085 | 133 | 7876802 | 0x0000000000400654 | fmadd | 7876695/7876802 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 795 | 794 | 2005858085 | 133 | 7876802 | 0x0000000000400654 | fmadd | 7876695/7876802 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 796 | 795 | 2005858085 | 133 | 7876802 | 0x0000000000400654 | fmadd | 7876695/7876802 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 797 | 796 | 2005858855 | 133 | 7876802 | 0x0000000000400654 | fmadd | —/7876802 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1392 | 797 | 9405606595 | 133 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 798 | — | 2021030935 | 134 | 7936668 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4087900000000000→0x4087900000000200 | — | — | origin |
| carrier_state | 799 | 798 | 2021030935 | 134 | 7936668 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4087900000000000→0x4087900000000200 | — | — | fsu_taint |
| operand_read | 800 | 799 | 2021035170 | 134 | 7936671 | 0x0000000000400658 | fmadd | 7936668/7936671 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 801 | 800 | 2021035170 | 134 | 7936671 | 0x0000000000400658 | fmadd | 7936668/7936671 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 802 | 801 | 2021035170 | 134 | 7936671 | 0x0000000000400658 | fmadd | 7936668/7936671 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 803 | 802 | 2021035940 | 134 | 7936671 | 0x0000000000400658 | fmadd | —/7936671 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1393 | 803 | 9405606595 | 134 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 804 | — | 2032880465 | 135 | 7983364 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfdc28f5c28f5c29→0xbfdc28f5c28f5c2b | — | — | origin |
| carrier_state | 805 | 804 | 2032880465 | 135 | 7983364 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0xbfdc28f5c28f5c29→0xbfdc28f5c28f5c2b | — | — | fsu_taint |
| operand_read | 806 | 805 | 2032895865 | 135 | 7983434 | 0x0000000000400654 | fmadd | 7983364/7983434 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 807 | 806 | 2032895865 | 135 | 7983434 | 0x0000000000400654 | fmadd | 7983364/7983434 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 808 | 807 | 2032895865 | 135 | 7983434 | 0x0000000000400654 | fmadd | 7983364/7983434 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 809 | 808 | 2032896635 | 135 | 7983434 | 0x0000000000400654 | fmadd | —/7983434 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1394 | 809 | 9405606595 | 135 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 810 | — | 2051661150 | 136 | 8057376 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4077c00000000000→0x4077c00000010000 | — | — | origin |
| carrier_state | 811 | 810 | 2051661150 | 136 | 8057376 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4077c00000000000→0x4077c00000010000 | — | — | fsu_taint |
| operand_read | 812 | 811 | 2051665385 | 136 | 8057379 | 0x0000000000400658 | fmadd | 8057376/8057379 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 813 | 812 | 2051665385 | 136 | 8057379 | 0x0000000000400658 | fmadd | 8057376/8057379 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 814 | 813 | 2051665385 | 136 | 8057379 | 0x0000000000400658 | fmadd | 8057376/8057379 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 815 | 814 | 2051666155 | 136 | 8057379 | 0x0000000000400658 | fmadd | —/8057379 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1395 | 815 | 9405606595 | 136 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 816 | — | 2061878665 | 137 | 8097914 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fe7c6a7ef9db22d→0x3fe7c6a7ef9cb22d | — | — | origin |
| carrier_state | 817 | 816 | 2061878665 | 137 | 8097914 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3fe7c6a7ef9db22d→0x3fe7c6a7ef9cb22d | — | — | fsu_taint |
| operand_read | 818 | 817 | 2061914085 | 137 | 8098058 | 0x0000000000400654 | fmadd | 8097914/8098058 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 819 | 818 | 2061914085 | 137 | 8098058 | 0x0000000000400654 | fmadd | 8097914/8098058 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 820 | 819 | 2061914085 | 137 | 8098058 | 0x0000000000400654 | fmadd | 8097914/8098058 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 821 | 820 | 2061914855 | 137 | 8098058 | 0x0000000000400654 | fmadd | —/8098058 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1396 | 821 | 9405606595 | 137 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 822 | — | 2082995915 | 138 | 8180819 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4083a00000000000→0x4083a00000008000 | — | — | origin |
| carrier_state | 823 | 822 | 2082995915 | 138 | 8180819 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4083a00000000000→0x4083a00000008000 | — | — | fsu_taint |
| operand_read | 824 | 823 | 2082997840 | 138 | 8180822 | 0x0000000000400654 | fmadd | 8180819/8180822 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 825 | 824 | 2082997840 | 138 | 8180822 | 0x0000000000400654 | fmadd | 8180819/8180822 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 826 | 825 | 2082997840 | 138 | 8180822 | 0x0000000000400654 | fmadd | 8180819/8180822 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 827 | 826 | 2082998610 | 138 | 8180822 | 0x0000000000400654 | fmadd | —/8180822 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1397 | 827 | 9405606595 | 138 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 828 | — | 2098530665 | 139 | 8242309 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x406b600000000000→0x406b600000008000 | — | — | origin |
| carrier_state | 829 | 828 | 2098530665 | 139 | 8242309 | 0x0000000000400650 | scvtf | —/— | 45 | — | 64@0 | 0x406b600000000000→0x406b600000008000 | — | — | fsu_taint |
| operand_read | 830 | 829 | 2098534515 | 139 | 8242312 | 0x000000000040065c | fmadd | 8242309/8242312 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 831 | 830 | 2098534515 | 139 | 8242312 | 0x000000000040065c | fmadd | 8242309/8242312 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 832 | 831 | 2098534515 | 139 | 8242312 | 0x000000000040065c | fmadd | 8242309/8242312 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 833 | 832 | 2098535285 | 139 | 8242312 | 0x000000000040065c | fmadd | —/8242312 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1398 | 833 | 9405606595 | 139 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 78 | — | 186337305 | 14 | 698076 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x408c900000000000→0x408c900000000800 | — | — | origin |
| carrier_state | 79 | 78 | 186337305 | 14 | 698076 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x408c900000000000→0x408c900000000800 | — | — | fsu_taint |
| operand_read | 80 | 79 | 186341540 | 14 | 698079 | 0x0000000000400658 | fmadd | 698076/698079 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 81 | 80 | 186341540 | 14 | 698079 | 0x0000000000400658 | fmadd | 698076/698079 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 82 | 81 | 186341540 | 14 | 698079 | 0x0000000000400658 | fmadd | 698076/698079 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 83 | 82 | 186342310 | 14 | 698079 | 0x0000000000400658 | fmadd | —/698079 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1273 | 83 | 9405606595 | 14 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 834 | — | 2114647150 | 140 | 8305920 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4074200000000000→0x4074200000010000 | — | — | origin |
| carrier_state | 835 | 834 | 2114647150 | 140 | 8305920 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4074200000000000→0x4074200000010000 | — | — | fsu_taint |
| operand_read | 836 | 835 | 2114651385 | 140 | 8305923 | 0x0000000000400658 | fmadd | 8305920/8305923 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 837 | 836 | 2114651385 | 140 | 8305923 | 0x0000000000400658 | fmadd | 8305920/8305923 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 838 | 837 | 2114651385 | 140 | 8305923 | 0x0000000000400658 | fmadd | 8305920/8305923 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 839 | 838 | 2114652155 | 140 | 8305923 | 0x0000000000400658 | fmadd | —/8305923 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1399 | 839 | 9405606595 | 140 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 840 | — | 2129140090 | 141 | 8363375 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4063200000000000→0x4063200000000400 | — | — | origin |
| carrier_state | 841 | 840 | 2129140090 | 141 | 8363375 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4063200000000000→0x4063200000000400 | — | — | fsu_taint |
| operand_read | 842 | 841 | 2129142015 | 141 | 8363378 | 0x0000000000400654 | fmadd | 8363375/8363378 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 843 | 842 | 2129142015 | 141 | 8363378 | 0x0000000000400654 | fmadd | 8363375/8363378 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 844 | 843 | 2129142015 | 141 | 8363378 | 0x0000000000400654 | fmadd | 8363375/8363378 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 845 | 844 | 2129142785 | 141 | 8363378 | 0x0000000000400654 | fmadd | —/8363378 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1400 | 845 | 9405606595 | 141 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 846 | — | 2145002090 | 142 | 8425620 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x408cb80000000000→0x408cb80000000100 | — | — | origin |
| carrier_state | 847 | 846 | 2145002090 | 142 | 8425620 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x408cb80000000000→0x408cb80000000100 | — | — | fsu_taint |
| operand_read | 848 | 847 | 2145006325 | 142 | 8425623 | 0x0000000000400658 | fmadd | 8425620/8425623 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 849 | 848 | 2145006325 | 142 | 8425623 | 0x0000000000400658 | fmadd | 8425620/8425623 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 850 | 849 | 2145006325 | 142 | 8425623 | 0x0000000000400658 | fmadd | 8425620/8425623 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 851 | 850 | 2145007095 | 142 | 8425623 | 0x0000000000400658 | fmadd | —/8425623 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1401 | 851 | 9405606595 | 142 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 852 | — | 2157010625 | 143 | 8473431 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fda3d70a3d70a3e→0x3fda3d70a3d60a3e | — | — | origin |
| carrier_state | 853 | 852 | 2157010625 | 143 | 8473431 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fda3d70a3d70a3e→0x3fda3d70a3d60a3e | — | — | fsu_taint |
| operand_read | 854 | 853 | 2157034880 | 143 | 8473538 | 0x0000000000400654 | fmadd | 8473431/8473538 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 855 | 854 | 2157034880 | 143 | 8473538 | 0x0000000000400654 | fmadd | 8473431/8473538 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 856 | 855 | 2157034880 | 143 | 8473538 | 0x0000000000400654 | fmadd | 8473431/8473538 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 857 | 856 | 2157035650 | 143 | 8473538 | 0x0000000000400654 | fmadd | —/8473538 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1402 | 857 | 9405606595 | 143 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 858 | — | 2166261405 | 144 | 8509790 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff5eb851eb851ec→0x3ff5eb851eb851e8 | — | — | origin |
| carrier_state | 859 | 858 | 2166261405 | 144 | 8509790 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff5eb851eb851ec→0x3ff5eb851eb851e8 | — | — | fsu_taint |
| operand_read | 860 | 859 | 2166296825 | 144 | 8509934 | 0x0000000000400654 | fmadd | 8509790/8509934 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 861 | 860 | 2166296825 | 144 | 8509934 | 0x0000000000400654 | fmadd | 8509790/8509934 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 862 | 861 | 2166296825 | 144 | 8509934 | 0x0000000000400654 | fmadd | 8509790/8509934 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 863 | 862 | 2166297595 | 144 | 8509934 | 0x0000000000400654 | fmadd | —/8509934 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1403 | 863 | 9405606595 | 144 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 864 | — | 2183316135 | 145 | 8576750 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff204189374bc6b→0x3ff204189374bd6b | — | — | origin |
| carrier_state | 865 | 864 | 2183316135 | 145 | 8576750 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff204189374bc6b→0x3ff204189374bd6b | — | — | fsu_taint |
| operand_read | 866 | 865 | 2183351555 | 145 | 8576894 | 0x0000000000400654 | fmadd | 8576750/8576894 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 867 | 866 | 2183351555 | 145 | 8576894 | 0x0000000000400654 | fmadd | 8576750/8576894 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 868 | 867 | 2183351555 | 145 | 8576894 | 0x0000000000400654 | fmadd | 8576750/8576894 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 869 | 868 | 2183352325 | 145 | 8576894 | 0x0000000000400654 | fmadd | —/8576894 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1404 | 869 | 9405606595 | 145 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 870 | — | 2202501070 | 146 | 8652747 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fdced916872b021→0x3fdced916872b025 | — | — | origin |
| carrier_state | 871 | 870 | 2202501070 | 146 | 8652747 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fdced916872b021→0x3fdced916872b025 | — | — | fsu_taint |
| operand_read | 872 | 871 | 2202525325 | 146 | 8652854 | 0x0000000000400654 | fmadd | 8652747/8652854 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 873 | 872 | 2202525325 | 146 | 8652854 | 0x0000000000400654 | fmadd | 8652747/8652854 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 874 | 873 | 2202525325 | 146 | 8652854 | 0x0000000000400654 | fmadd | 8652747/8652854 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 875 | 874 | 2202526095 | 146 | 8652854 | 0x0000000000400654 | fmadd | —/8652854 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1405 | 875 | 9405606595 | 146 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 876 | — | 2218680310 | 147 | 8716214 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3fe851eb851eb852→0x3fe851eb851eb856 | — | — | origin |
| carrier_state | 877 | 876 | 2218680310 | 147 | 8716214 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3fe851eb851eb852→0x3fe851eb851eb856 | — | — | fsu_taint |
| operand_read | 878 | 877 | 2218715730 | 147 | 8716358 | 0x0000000000400654 | fmadd | 8716214/8716358 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 879 | 878 | 2218715730 | 147 | 8716358 | 0x0000000000400654 | fmadd | 8716214/8716358 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 880 | 879 | 2218715730 | 147 | 8716358 | 0x0000000000400654 | fmadd | 8716214/8716358 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 881 | 880 | 2218716500 | 147 | 8716358 | 0x0000000000400654 | fmadd | —/8716358 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1406 | 881 | 9405606595 | 147 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 882 | — | 2229001390 | 148 | 8756749 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4076400000000000→0x4076400000002000 | — | — | origin |
| carrier_state | 883 | 882 | 2229001390 | 148 | 8756749 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4076400000000000→0x4076400000002000 | — | — | fsu_taint |
| operand_read | 884 | 883 | 2229005240 | 148 | 8756752 | 0x000000000040065c | fmadd | 8756749/8756752 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 885 | 884 | 2229005240 | 148 | 8756752 | 0x000000000040065c | fmadd | 8756749/8756752 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 886 | 885 | 2229005240 | 148 | 8756752 | 0x000000000040065c | fmadd | 8756749/8756752 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 887 | 886 | 2229006010 | 148 | 8756752 | 0x000000000040065c | fmadd | —/8756752 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1407 | 887 | 9405606595 | 148 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 888 | — | 2242378600 | 149 | 8809600 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfb53f7ced916872→0xbfb53f7ced91e872 | — | — | origin |
| carrier_state | 889 | 888 | 2242378600 | 149 | 8809600 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfb53f7ced916872→0xbfb53f7ced91e872 | — | — | fsu_taint |
| operand_read | 890 | 889 | 2242394000 | 149 | 8809670 | 0x0000000000400654 | fmadd | 8809600/8809670 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 891 | 890 | 2242394000 | 149 | 8809670 | 0x0000000000400654 | fmadd | 8809600/8809670 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 892 | 891 | 2242394000 | 149 | 8809670 | 0x0000000000400654 | fmadd | 8809600/8809670 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 893 | 892 | 2242394770 | 149 | 8809670 | 0x0000000000400654 | fmadd | —/8809670 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1408 | 893 | 9405606595 | 149 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 84 | — | 203026285 | 15 | 764172 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4028000000000000→0x4028000000000001 | — | — | origin |
| carrier_state | 85 | 84 | 203026285 | 15 | 764172 | 0x000000000040064c | scvtf | —/— | 45 | — | 64@0 | 0x4028000000000000→0x4028000000000001 | — | — | fsu_taint |
| operand_read | 86 | 85 | 203030520 | 15 | 764175 | 0x0000000000400658 | fmadd | 764172/764175 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 87 | 86 | 203030520 | 15 | 764175 | 0x0000000000400658 | fmadd | 764172/764175 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 88 | 87 | 203030520 | 15 | 764175 | 0x0000000000400658 | fmadd | 764172/764175 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 89 | 88 | 203031290 | 15 | 764175 | 0x0000000000400658 | fmadd | —/764175 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1274 | 89 | 9405606595 | 15 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 894 | — | 2264414845 | 150 | 8896899 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3ff3a9fbe76c8b44→0x3ff3a9fbe76c8f44 | — | — | origin |
| carrier_state | 895 | 894 | 2264414845 | 150 | 8896899 | 0x0000000000400658 | fmadd | —/— | 4 | — | 64@0 | 0x3ff3a9fbe76c8b44→0x3ff3a9fbe76c8f44 | — | — | fsu_taint |
| operand_read | 896 | 895 | 2264439100 | 150 | 8897006 | 0x0000000000400654 | fmadd | 8896899/8897006 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 897 | 896 | 2264439100 | 150 | 8897006 | 0x0000000000400654 | fmadd | 8896899/8897006 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 898 | 897 | 2264439100 | 150 | 8897006 | 0x0000000000400654 | fmadd | 8896899/8897006 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 899 | 898 | 2264439870 | 150 | 8897006 | 0x0000000000400654 | fmadd | —/8897006 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1409 | 899 | 9405606595 | 150 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 900 | — | 2282313110 | 151 | 8967064 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfc45a1cac083127→0xbfc45a1cac082127 | — | — | origin |
| carrier_state | 901 | 900 | 2282313110 | 151 | 8967064 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfc45a1cac083127→0xbfc45a1cac082127 | — | — | fsu_taint |
| operand_read | 902 | 901 | 2282328510 | 151 | 8967134 | 0x0000000000400654 | fmadd | 8967064/8967134 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 903 | 902 | 2282328510 | 151 | 8967134 | 0x0000000000400654 | fmadd | 8967064/8967134 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 904 | 903 | 2282328510 | 151 | 8967134 | 0x0000000000400654 | fmadd | 8967064/8967134 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 905 | 904 | 2282329280 | 151 | 8967134 | 0x0000000000400654 | fmadd | —/8967134 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1410 | 905 | 9405606595 | 151 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 906 | — | 2302058990 | 152 | 9045323 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4089900000000000→0x4089900000000040 | — | — | origin |
| carrier_state | 907 | 906 | 2302058990 | 152 | 9045323 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4089900000000000→0x4089900000000040 | — | — | fsu_taint |
| operand_read | 908 | 907 | 2302060915 | 152 | 9045326 | 0x0000000000400654 | fmadd | 9045323/9045326 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 909 | 908 | 2302060915 | 152 | 9045326 | 0x0000000000400654 | fmadd | 9045323/9045326 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 910 | 909 | 2302060915 | 152 | 9045326 | 0x0000000000400654 | fmadd | 9045323/9045326 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 911 | 910 | 2302061685 | 152 | 9045326 | 0x0000000000400654 | fmadd | —/9045326 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1411 | 911 | 9405606595 | 152 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 912 | — | 2321713240 | 153 | 9122547 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fec6a7ef9db22d1→0x3fec6a7ef9db2251 | — | — | origin |
| carrier_state | 913 | 912 | 2321713240 | 153 | 9122547 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fec6a7ef9db22d1→0x3fec6a7ef9db2251 | — | — | fsu_taint |
| operand_read | 914 | 913 | 2321737495 | 153 | 9122654 | 0x0000000000400654 | fmadd | 9122547/9122654 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 915 | 914 | 2321737495 | 153 | 9122654 | 0x0000000000400654 | fmadd | 9122547/9122654 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 916 | 915 | 2321737495 | 153 | 9122654 | 0x0000000000400654 | fmadd | 9122547/9122654 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 917 | 916 | 2321738265 | 153 | 9122654 | 0x0000000000400654 | fmadd | —/9122654 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1412 | 917 | 9405606595 | 153 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 918 | — | 2342653775 | 154 | 9205703 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4077f00000000000→0x4077f00000000001 | — | — | origin |
| carrier_state | 919 | 918 | 2342653775 | 154 | 9205703 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4077f00000000000→0x4077f00000000001 | — | — | fsu_taint |
| operand_read | 920 | 919 | 2342655700 | 154 | 9205706 | 0x0000000000400654 | fmadd | 9205703/9205706 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 921 | 920 | 2342655700 | 154 | 9205706 | 0x0000000000400654 | fmadd | 9205703/9205706 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 922 | 921 | 2342655700 | 154 | 9205706 | 0x0000000000400654 | fmadd | 9205703/9205706 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 923 | 922 | 2342656470 | 154 | 9205706 | 0x0000000000400654 | fmadd | —/9205706 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1413 | 923 | 9405606595 | 154 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 924 | — | 2352707280 | 155 | 9245268 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4088700000000000→0x4088700000020000 | — | — | origin |
| carrier_state | 925 | 924 | 2352707280 | 155 | 9245268 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4088700000000000→0x4088700000020000 | — | — | fsu_taint |
| operand_read | 926 | 925 | 2352711515 | 155 | 9245271 | 0x0000000000400658 | fmadd | 9245268/9245271 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 927 | 926 | 2352711515 | 155 | 9245271 | 0x0000000000400658 | fmadd | 9245268/9245271 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 928 | 927 | 2352711515 | 155 | 9245271 | 0x0000000000400658 | fmadd | 9245268/9245271 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 929 | 928 | 2352712285 | 155 | 9245271 | 0x0000000000400658 | fmadd | —/9245271 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1414 | 929 | 9405606595 | 155 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 930 | — | 2360708350 | 156 | 9276913 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4083400000000000→0x4083400000000002 | — | — | origin |
| carrier_state | 931 | 930 | 2360708350 | 156 | 9276913 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4083400000000000→0x4083400000000002 | — | — | fsu_taint |
| operand_read | 932 | 931 | 2360712200 | 156 | 9276916 | 0x000000000040065c | fmadd | 9276913/9276916 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 933 | 932 | 2360712200 | 156 | 9276916 | 0x000000000040065c | fmadd | 9276913/9276916 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 934 | 933 | 2360712200 | 156 | 9276916 | 0x000000000040065c | fmadd | 9276913/9276916 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 935 | 934 | 2360712970 | 156 | 9276916 | 0x000000000040065c | fmadd | —/9276916 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1415 | 935 | 9405606595 | 156 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 936 | — | 2376278905 | 157 | 9338332 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0x3fd083126e978d50→0x3fd083126e978d70 | — | — | origin |
| carrier_state | 937 | 936 | 2376278905 | 157 | 9338332 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0x3fd083126e978d50→0x3fd083126e978d70 | — | — | fsu_taint |
| operand_read | 938 | 937 | 2376294305 | 157 | 9338402 | 0x0000000000400654 | fmadd | 9338332/9338402 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 939 | 938 | 2376294305 | 157 | 9338402 | 0x0000000000400654 | fmadd | 9338332/9338402 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 940 | 939 | 2376294305 | 157 | 9338402 | 0x0000000000400654 | fmadd | 9338332/9338402 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 941 | 940 | 2376295075 | 157 | 9338402 | 0x0000000000400654 | fmadd | —/9338402 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1416 | 941 | 9405606595 | 157 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 942 | — | 2393374060 | 158 | 9405505 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4084a00000000000→0x4084a00000001000 | — | — | origin |
| carrier_state | 943 | 942 | 2393374060 | 158 | 9405505 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x4084a00000000000→0x4084a00000001000 | — | — | fsu_taint |
| operand_read | 944 | 943 | 2393377910 | 158 | 9405508 | 0x000000000040065c | fmadd | 9405505/9405508 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 945 | 944 | 2393377910 | 158 | 9405508 | 0x000000000040065c | fmadd | 9405505/9405508 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 946 | 945 | 2393377910 | 158 | 9405508 | 0x000000000040065c | fmadd | 9405505/9405508 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 947 | 946 | 2393378680 | 158 | 9405508 | 0x000000000040065c | fmadd | —/9405508 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1417 | 947 | 9405606595 | 158 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 948 | — | 2448681235 | 159 | 9492110 | 0x00000000004006a4 | fmadd | —/— | 4 | — | 64@0 | 0x3fe6c3f3e0370cdc→0x3fe6c3f3e0360cdc | — | — | origin |
| carrier_state | 949 | 948 | 2448681235 | 159 | 9492110 | 0x00000000004006a4 | fmadd | —/— | 4 | — | 64@0 | 0x3fe6c3f3e0370cdc→0x3fe6c3f3e0360cdc | — | — | fsu_taint |
| operand_read | 950 | 949 | 2448689705 | 159 | 9492126 | 0x00000000004006a4 | fmadd | 9492110/9492126 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 951 | 950 | 2448689705 | 159 | 9492126 | 0x00000000004006a4 | fmadd | 9492110/9492126 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 952 | 951 | 2448689705 | 159 | 9492126 | 0x00000000004006a4 | fmadd | 9492110/9492126 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 953 | 952 | 2448690475 | 159 | 9492126 | 0x00000000004006a4 | fmadd | —/9492126 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1418 | 953 | 9405606595 | 159 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 90 | — | 217756770 | 16 | 822527 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x408b680000000000→0x408b680000002000 | — | — | origin |
| carrier_state | 91 | 90 | 217756770 | 16 | 822527 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x408b680000000000→0x408b680000002000 | — | — | fsu_taint |
| operand_read | 92 | 91 | 217758695 | 16 | 822530 | 0x0000000000400654 | fmadd | 822527/822530 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 93 | 92 | 217758695 | 16 | 822530 | 0x0000000000400654 | fmadd | 822527/822530 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 94 | 93 | 217758695 | 16 | 822530 | 0x0000000000400654 | fmadd | 822527/822530 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 95 | 94 | 217759465 | 16 | 822530 | 0x0000000000400654 | fmadd | —/822530 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1275 | 95 | 9405606595 | 16 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 954 | — | 2513770105 | 160 | 9586347 | 0x00000000004006a4 | fmadd | —/— | 4 | — | 64@0 | 0x40010713f077ccc0→0x40010713f077ecc0 | — | — | origin |
| carrier_state | 955 | 954 | 2513770105 | 160 | 9586347 | 0x00000000004006a4 | fmadd | —/— | 4 | — | 64@0 | 0x40010713f077ccc0→0x40010713f077ecc0 | — | — | fsu_taint |
| operand_read | 956 | 955 | 2513778575 | 160 | 9586363 | 0x00000000004006a4 | fmadd | 9586347/9586363 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 957 | 956 | 2513778575 | 160 | 9586363 | 0x00000000004006a4 | fmadd | 9586347/9586363 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 958 | 957 | 2513778575 | 160 | 9586363 | 0x00000000004006a4 | fmadd | 9586347/9586363 | 4 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 959 | 958 | 2513779345 | 160 | 9586363 | 0x00000000004006a4 | fmadd | —/9586363 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1419 | 959 | 9405606595 | 160 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 960 | — | 2586922030 | 161 | 9654757 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe1938151a43782→0x3fe1938151a43682 | — | — | origin |
| carrier_state | 961 | 960 | 2586922030 | 161 | 9654757 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe1938151a43782→0x3fe1938151a43682 | — | — | fsu_taint |
| operand_read | 962 | 961 | 2586930500 | 161 | 9654773 | 0x00000000004006cc | fmadd | 9654757/9654773 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 963 | 962 | 2586930500 | 161 | 9654773 | 0x00000000004006cc | fmadd | 9654757/9654773 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 964 | 963 | 2586930500 | 161 | 9654773 | 0x00000000004006cc | fmadd | 9654757/9654773 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 965 | 964 | 2586931270 | 161 | 9654773 | 0x00000000004006cc | fmadd | —/9654773 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1420 | 965 | 9405606595 | 161 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 966 | — | 2633629075 | 162 | 9732153 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff5c78e9f6a93f3→0x3ff5c78e9f6ab3f3 | — | — | origin |
| carrier_state | 967 | 966 | 2633629075 | 162 | 9732153 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff5c78e9f6a93f3→0x3ff5c78e9f6ab3f3 | — | — | fsu_taint |
| operand_read | 968 | 967 | 2633658335 | 162 | 9732169 | 0x00000000004006a4 | fmadd | 9732153/9732169 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 969 | 968 | 2633658335 | 162 | 9732169 | 0x00000000004006a4 | fmadd | 9732153/9732169 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 970 | 969 | 2633658335 | 162 | 9732169 | 0x00000000004006a4 | fmadd | 9732153/9732169 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 971 | 970 | 2633659105 | 162 | 9732169 | 0x00000000004006a4 | fmadd | —/9732169 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1421 | 971 | 9405606595 | 162 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 972 | — | 2696835680 | 163 | 9816743 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe3b7f1737542a3→0x3fe3b7f1737542a2 | — | — | origin |
| carrier_state | 973 | 972 | 2696835680 | 163 | 9816743 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe3b7f1737542a3→0x3fe3b7f1737542a2 | — | — | fsu_taint |
| operand_read | 974 | 973 | 2696844150 | 163 | 9816759 | 0x00000000004006cc | fmadd | 9816743/9816759 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 975 | 974 | 2696844150 | 163 | 9816759 | 0x00000000004006cc | fmadd | 9816743/9816759 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 976 | 975 | 2696844150 | 163 | 9816759 | 0x00000000004006cc | fmadd | 9816743/9816759 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 977 | 976 | 2696844920 | 163 | 9816759 | 0x00000000004006cc | fmadd | —/9816759 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1422 | 977 | 9405606595 | 163 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 978 | — | 2721870690 | 164 | 9857195 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fea59d99029ae50→0x3fea59d99029a650 | — | — | origin |
| carrier_state | 979 | 978 | 2721870690 | 164 | 9857195 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fea59d99029ae50→0x3fea59d99029a650 | — | — | fsu_taint |
| operand_read | 980 | 979 | 2721879160 | 164 | 9857211 | 0x00000000004006a4 | fmadd | 9857195/9857211 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 981 | 980 | 2721879160 | 164 | 9857211 | 0x00000000004006a4 | fmadd | 9857195/9857211 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 982 | 981 | 2721879160 | 164 | 9857211 | 0x00000000004006a4 | fmadd | 9857195/9857211 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 983 | 982 | 2721879930 | 164 | 9857211 | 0x00000000004006a4 | fmadd | —/9857211 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1423 | 983 | 9405606595 | 164 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 984 | — | 2767314550 | 165 | 9907835 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fc3ac929aa1d758→0x3fc3ac929aa15758 | — | — | origin |
| carrier_state | 985 | 984 | 2767314550 | 165 | 9907835 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fc3ac929aa1d758→0x3fc3ac929aa15758 | — | — | fsu_taint |
| operand_read | 986 | 985 | 2767323020 | 165 | 9907851 | 0x00000000004006a4 | fmadd | 9907835/9907851 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 987 | 986 | 2767323020 | 165 | 9907851 | 0x00000000004006a4 | fmadd | 9907835/9907851 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 988 | 987 | 2767323020 | 165 | 9907851 | 0x00000000004006a4 | fmadd | 9907835/9907851 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 989 | 988 | 2767323790 | 165 | 9907851 | 0x00000000004006a4 | fmadd | —/9907851 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1424 | 989 | 9405606595 | 165 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 990 | — | 2837348745 | 166 | 10015109 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3feac5564b662fe0→0x3feac5564b662fe1 | — | — | origin |
| carrier_state | 991 | 990 | 2837348745 | 166 | 10015109 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3feac5564b662fe0→0x3feac5564b662fe1 | — | — | fsu_taint |
| operand_read | 992 | 991 | 2837357215 | 166 | 10015125 | 0x00000000004006a4 | fmadd | 10015109/10015125 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 993 | 992 | 2837357215 | 166 | 10015125 | 0x00000000004006a4 | fmadd | 10015109/10015125 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 994 | 993 | 2837357215 | 166 | 10015125 | 0x00000000004006a4 | fmadd | 10015109/10015125 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 995 | 994 | 2837357985 | 166 | 10015125 | 0x00000000004006a4 | fmadd | —/10015125 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1425 | 995 | 9405606595 | 166 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 996 | — | 2888222645 | 167 | 10089963 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fe0c32a8c9b8456→0x3fe0c32a8c9b8452 | — | — | origin |
| carrier_state | 997 | 996 | 2888222645 | 167 | 10089963 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fe0c32a8c9b8456→0x3fe0c32a8c9b8452 | — | — | fsu_taint |
| operand_read | 998 | 997 | 2888231115 | 167 | 10089979 | 0x00000000004006cc | fmadd | 10089963/10089979 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 999 | 998 | 2888231115 | 167 | 10089979 | 0x00000000004006cc | fmadd | 10089963/10089979 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1000 | 999 | 2888231115 | 167 | 10089979 | 0x00000000004006cc | fmadd | 10089963/10089979 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1001 | 1000 | 2888231885 | 167 | 10089979 | 0x00000000004006cc | fmadd | —/10089979 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1426 | 1001 | 9405606595 | 167 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1002 | — | 2946621370 | 168 | 10163191 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff24b524399b2c4→0x3ff24b52439932c4 | — | — | origin |
| carrier_state | 1003 | 1002 | 2946621370 | 168 | 10163191 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff24b524399b2c4→0x3ff24b52439932c4 | — | — | fsu_taint |
| operand_read | 1004 | 1003 | 2946629840 | 168 | 10163207 | 0x00000000004006a4 | fmadd | 10163191/10163207 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1005 | 1004 | 2946629840 | 168 | 10163207 | 0x00000000004006a4 | fmadd | 10163191/10163207 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1006 | 1005 | 2946629840 | 168 | 10163207 | 0x00000000004006a4 | fmadd | 10163191/10163207 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1007 | 1006 | 2946630610 | 168 | 10163207 | 0x00000000004006a4 | fmadd | —/10163207 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1427 | 1007 | 9405606595 | 168 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1008 | — | 2974584305 | 169 | 10208445 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3f742917507e9dc9→0x3f742917507e9dcd | — | — | origin |
| carrier_state | 1009 | 1008 | 2974584305 | 169 | 10208445 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3f742917507e9dc9→0x3f742917507e9dcd | — | — | fsu_taint |
| operand_read | 1010 | 1009 | 2974592775 | 169 | 10208461 | 0x00000000004006cc | fmadd | 10208445/10208461 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1011 | 1010 | 2974592775 | 169 | 10208461 | 0x00000000004006cc | fmadd | 10208445/10208461 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1012 | 1011 | 2974592775 | 169 | 10208461 | 0x00000000004006cc | fmadd | 10208445/10208461 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1013 | 1012 | 2974593545 | 169 | 10208461 | 0x00000000004006cc | fmadd | —/10208461 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1428 | 1013 | 9405606595 | 169 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 96 | — | 240534525 | 17 | 912172 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfc45a1cac083127→0xbfc45a1cac08312f | — | — | origin |
| carrier_state | 97 | 96 | 240534525 | 17 | 912172 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfc45a1cac083127→0xbfc45a1cac08312f | — | — | fsu_taint |
| operand_read | 98 | 97 | 240549925 | 17 | 912242 | 0x0000000000400654 | fmadd | 912172/912242 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 99 | 98 | 240549925 | 17 | 912242 | 0x0000000000400654 | fmadd | 912172/912242 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 100 | 99 | 240549925 | 17 | 912242 | 0x0000000000400654 | fmadd | 912172/912242 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 101 | 100 | 240550695 | 17 | 912242 | 0x0000000000400654 | fmadd | —/912242 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1276 | 101 | 9405606595 | 17 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1014 | — | 3050027750 | 170 | 10305911 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fb21dfb9389b525→0x3fb21dfb9389b521 | — | — | origin |
| carrier_state | 1015 | 1014 | 3050027750 | 170 | 10305911 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fb21dfb9389b525→0x3fb21dfb9389b521 | — | — | fsu_taint |
| operand_read | 1016 | 1015 | 3050036220 | 170 | 10305927 | 0x00000000004006cc | fmadd | 10305911/10305927 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1017 | 1016 | 3050036220 | 170 | 10305927 | 0x00000000004006cc | fmadd | 10305911/10305927 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1018 | 1017 | 3050036220 | 170 | 10305927 | 0x00000000004006cc | fmadd | 10305911/10305927 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1019 | 1018 | 3050036990 | 170 | 10305927 | 0x00000000004006cc | fmadd | —/10305927 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1429 | 1019 | 9405606595 | 170 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1020 | — | 3071553485 | 171 | 10346479 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe3b7e0ac7da1ed→0x3fe3b7e0ac7da16d | — | — | origin |
| carrier_state | 1021 | 1020 | 3071553485 | 171 | 10346479 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe3b7e0ac7da1ed→0x3fe3b7e0ac7da16d | — | — | fsu_taint |
| operand_read | 1022 | 1021 | 3071561955 | 171 | 10346495 | 0x00000000004006cc | fmadd | 10346479/10346495 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1023 | 1022 | 3071561955 | 171 | 10346495 | 0x00000000004006cc | fmadd | 10346479/10346495 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1024 | 1023 | 3071561955 | 171 | 10346495 | 0x00000000004006cc | fmadd | 10346479/10346495 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1025 | 1024 | 3071562725 | 171 | 10346495 | 0x00000000004006cc | fmadd | —/10346495 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1430 | 1025 | 9405606595 | 171 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1026 | — | 3144428210 | 172 | 10439561 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff33aa582dbe7f3→0x3ff33aa582dbeff3 | — | — | origin |
| carrier_state | 1027 | 1026 | 3144428210 | 172 | 10439561 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff33aa582dbe7f3→0x3ff33aa582dbeff3 | — | — | fsu_taint |
| operand_read | 1028 | 1027 | 3144436680 | 172 | 10439577 | 0x00000000004006cc | fmadd | 10439561/10439577 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1029 | 1028 | 3144436680 | 172 | 10439577 | 0x00000000004006cc | fmadd | 10439561/10439577 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1030 | 1029 | 3144436680 | 172 | 10439577 | 0x00000000004006cc | fmadd | 10439561/10439577 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1031 | 1030 | 3144437450 | 172 | 10439577 | 0x00000000004006cc | fmadd | —/10439577 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1431 | 1031 | 9405606595 | 172 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1032 | — | 3201445940 | 173 | 10530645 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe87564302b40f6→0x3fe87564302b42f6 | — | — | origin |
| carrier_state | 1033 | 1032 | 3201445940 | 173 | 10530645 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe87564302b40f6→0x3fe87564302b42f6 | — | — | fsu_taint |
| operand_read | 1034 | 1033 | 3201454410 | 173 | 10530661 | 0x00000000004006a4 | fmadd | 10530645/10530661 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1035 | 1034 | 3201454410 | 173 | 10530661 | 0x00000000004006a4 | fmadd | 10530645/10530661 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1036 | 1035 | 3201454410 | 173 | 10530661 | 0x00000000004006a4 | fmadd | 10530645/10530661 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1037 | 1036 | 3201455180 | 173 | 10530661 | 0x00000000004006a4 | fmadd | —/10530661 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1432 | 1037 | 9405606595 | 173 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1038 | — | 3261958315 | 174 | 10617523 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3ff2393682730c67→0x3ff2393682730c47 | — | — | origin |
| carrier_state | 1039 | 1038 | 3261958315 | 174 | 10617523 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3ff2393682730c67→0x3ff2393682730c47 | — | — | fsu_taint |
| operand_read | 1040 | 1039 | 3261966785 | 174 | 10617539 | 0x00000000004006cc | fmadd | 10617523/10617539 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1041 | 1040 | 3261966785 | 174 | 10617539 | 0x00000000004006cc | fmadd | 10617523/10617539 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1042 | 1041 | 3261966785 | 174 | 10617539 | 0x00000000004006cc | fmadd | 10617523/10617539 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1043 | 1042 | 3261967555 | 174 | 10617539 | 0x00000000004006cc | fmadd | —/10617539 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1433 | 1043 | 9405606595 | 174 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1044 | — | 3319721020 | 175 | 10688471 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fd72c7b890d5a5c→0x3fd72c7b890d5a54 | — | — | origin |
| carrier_state | 1045 | 1044 | 3319721020 | 175 | 10688471 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fd72c7b890d5a5c→0x3fd72c7b890d5a54 | — | — | fsu_taint |
| operand_read | 1046 | 1045 | 3319729490 | 175 | 10688487 | 0x00000000004006a4 | fmadd | 10688471/10688487 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1047 | 1046 | 3319729490 | 175 | 10688487 | 0x00000000004006a4 | fmadd | 10688471/10688487 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1048 | 1047 | 3319729490 | 175 | 10688487 | 0x00000000004006a4 | fmadd | 10688471/10688487 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1049 | 1048 | 3319730260 | 175 | 10688487 | 0x00000000004006a4 | fmadd | —/10688487 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1434 | 1049 | 9405606595 | 175 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1050 | — | 3390684990 | 176 | 10796785 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3fdaffe2a3cea6c2→0x3fdaffe2a3cee6c2 | — | — | origin |
| carrier_state | 1051 | 1050 | 3390684990 | 176 | 10796785 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0x3fdaffe2a3cea6c2→0x3fdaffe2a3cee6c2 | — | — | fsu_taint |
| operand_read | 1052 | 1051 | 3390693460 | 176 | 10796801 | 0x00000000004006a4 | fmadd | 10796785/10796801 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1053 | 1052 | 3390693460 | 176 | 10796801 | 0x00000000004006a4 | fmadd | 10796785/10796801 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1054 | 1053 | 3390693460 | 176 | 10796801 | 0x00000000004006a4 | fmadd | 10796785/10796801 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1055 | 1054 | 3390694230 | 176 | 10796801 | 0x00000000004006a4 | fmadd | —/10796801 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1435 | 1055 | 9405606595 | 176 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1056 | — | 3451802200 | 177 | 10886503 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fcbb56b87379746→0x3fcbb56b87379346 | — | — | origin |
| carrier_state | 1057 | 1056 | 3451802200 | 177 | 10886503 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fcbb56b87379746→0x3fcbb56b87379346 | — | — | fsu_taint |
| operand_read | 1058 | 1057 | 3451810670 | 177 | 10886519 | 0x00000000004006cc | fmadd | 10886503/10886519 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1059 | 1058 | 3451810670 | 177 | 10886519 | 0x00000000004006cc | fmadd | 10886503/10886519 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1060 | 1059 | 3451810670 | 177 | 10886519 | 0x00000000004006cc | fmadd | 10886503/10886519 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1061 | 1060 | 3451811440 | 177 | 10886519 | 0x00000000004006cc | fmadd | —/10886519 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1436 | 1061 | 9405606595 | 177 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1062 | — | 3504924500 | 178 | 10949563 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fa27179bfdf7e82→0x3fa27179bfdf7e86 | — | — | origin |
| carrier_state | 1063 | 1062 | 3504924500 | 178 | 10949563 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fa27179bfdf7e82→0x3fa27179bfdf7e86 | — | — | fsu_taint |
| operand_read | 1064 | 1063 | 3504932970 | 178 | 10949579 | 0x00000000004006a4 | fmadd | 10949563/10949579 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1065 | 1064 | 3504932970 | 178 | 10949579 | 0x00000000004006a4 | fmadd | 10949563/10949579 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1066 | 1065 | 3504932970 | 178 | 10949579 | 0x00000000004006a4 | fmadd | 10949563/10949579 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1067 | 1066 | 3504933740 | 178 | 10949579 | 0x00000000004006a4 | fmadd | —/10949579 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1437 | 1067 | 9405606595 | 178 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1068 | — | 3552153605 | 179 | 11028893 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe36540cc78e9f6→0x3fe36540cc78a9f6 | — | — | origin |
| carrier_state | 1069 | 1068 | 3552153605 | 179 | 11028893 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe36540cc78e9f6→0x3fe36540cc78a9f6 | — | — | fsu_taint |
| operand_read | 1070 | 1069 | 3552162075 | 179 | 11028909 | 0x00000000004006a4 | fmadd | 11028893/11028909 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1071 | 1070 | 3552162075 | 179 | 11028909 | 0x00000000004006a4 | fmadd | 11028893/11028909 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1072 | 1071 | 3552162075 | 179 | 11028909 | 0x00000000004006a4 | fmadd | 11028893/11028909 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1073 | 1072 | 3552162845 | 179 | 11028909 | 0x00000000004006a4 | fmadd | —/11028909 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1438 | 1073 | 9405606595 | 179 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 102 | — | 253697675 | 18 | 963686 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff27ef9db22d0e5→0x3ff27ef9db22d0a5 | — | — | origin |
| carrier_state | 103 | 102 | 253697675 | 18 | 963686 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff27ef9db22d0e5→0x3ff27ef9db22d0a5 | — | — | fsu_taint |
| operand_read | 104 | 103 | 253733095 | 18 | 963830 | 0x0000000000400654 | fmadd | 963686/963830 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 105 | 104 | 253733095 | 18 | 963830 | 0x0000000000400654 | fmadd | 963686/963830 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 106 | 105 | 253733095 | 18 | 963830 | 0x0000000000400654 | fmadd | 963686/963830 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 107 | 106 | 253733865 | 18 | 963830 | 0x0000000000400654 | fmadd | —/963830 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1277 | 107 | 9405606595 | 18 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1074 | — | 3622018015 | 180 | 11118331 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3f54c660a201472c→0x3f54c660a201072c | — | — | origin |
| carrier_state | 1075 | 1074 | 3622018015 | 180 | 11118331 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3f54c660a201472c→0x3f54c660a201072c | — | — | fsu_taint |
| operand_read | 1076 | 1075 | 3622026485 | 180 | 11118347 | 0x00000000004006cc | fmadd | 11118331/11118347 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1077 | 1076 | 3622026485 | 180 | 11118347 | 0x00000000004006cc | fmadd | 11118331/11118347 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1078 | 1077 | 3622026485 | 180 | 11118347 | 0x00000000004006cc | fmadd | 11118331/11118347 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1079 | 1078 | 3622027255 | 180 | 11118347 | 0x00000000004006cc | fmadd | —/11118347 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1439 | 1079 | 9405606595 | 180 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1080 | — | 3701743430 | 181 | 11223845 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff07ed527e52158→0x3ff07ed527e5a158 | — | — | origin |
| carrier_state | 1081 | 1080 | 3701743430 | 181 | 11223845 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff07ed527e52158→0x3ff07ed527e5a158 | — | — | fsu_taint |
| operand_read | 1082 | 1081 | 3701751900 | 181 | 11223861 | 0x00000000004006cc | fmadd | 11223845/11223861 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1083 | 1082 | 3701751900 | 181 | 11223861 | 0x00000000004006cc | fmadd | 11223845/11223861 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1084 | 1083 | 3701751900 | 181 | 11223861 | 0x00000000004006cc | fmadd | 11223845/11223861 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1085 | 1084 | 3701752670 | 181 | 11223861 | 0x00000000004006cc | fmadd | —/11223861 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1440 | 1085 | 9405606595 | 181 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1086 | — | 3725196860 | 182 | 11268045 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff0189df1172ef1→0x3ff0189df117aef1 | — | — | origin |
| carrier_state | 1087 | 1086 | 3725196860 | 182 | 11268045 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff0189df1172ef1→0x3ff0189df117aef1 | — | — | fsu_taint |
| operand_read | 1088 | 1087 | 3725205330 | 182 | 11268061 | 0x00000000004006cc | fmadd | 11268045/11268061 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1089 | 1088 | 3725205330 | 182 | 11268061 | 0x00000000004006cc | fmadd | 11268045/11268061 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1090 | 1089 | 3725205330 | 182 | 11268061 | 0x00000000004006cc | fmadd | 11268045/11268061 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1091 | 1090 | 3725206100 | 182 | 11268061 | 0x00000000004006cc | fmadd | —/11268061 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1441 | 1091 | 9405606595 | 182 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1092 | — | 3760703870 | 183 | 11318593 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fef51eb851eb852→0x3fef51eb851eb85a | — | — | origin |
| carrier_state | 1093 | 1092 | 3760703870 | 183 | 11318593 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fef51eb851eb852→0x3fef51eb851eb85a | — | — | fsu_taint |
| operand_read | 1094 | 1093 | 3760712340 | 183 | 11318609 | 0x00000000004006a4 | fmadd | 11318593/11318609 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1095 | 1094 | 3760712340 | 183 | 11318609 | 0x00000000004006a4 | fmadd | 11318593/11318609 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1096 | 1095 | 3760712340 | 183 | 11318609 | 0x00000000004006a4 | fmadd | 11318593/11318609 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1097 | 1096 | 3760713110 | 183 | 11318609 | 0x00000000004006a4 | fmadd | —/11318609 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1442 | 1097 | 9405606595 | 183 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1098 | — | 3800713070 | 184 | 11366519 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff0b4b407032980→0x3ff0b4b407033980 | — | — | origin |
| carrier_state | 1099 | 1098 | 3800713070 | 184 | 11366519 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff0b4b407032980→0x3ff0b4b407033980 | — | — | fsu_taint |
| operand_read | 1100 | 1099 | 3800721540 | 184 | 11366535 | 0x00000000004006cc | fmadd | 11366519/11366535 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1101 | 1100 | 3800721540 | 184 | 11366535 | 0x00000000004006cc | fmadd | 11366519/11366535 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1102 | 1101 | 3800721540 | 184 | 11366535 | 0x00000000004006cc | fmadd | 11366519/11366535 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1103 | 1102 | 3800722310 | 184 | 11366535 | 0x00000000004006cc | fmadd | —/11366535 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1443 | 1103 | 9405606595 | 184 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1104 | — | 3844519140 | 185 | 11438219 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff0270f3882278d→0x3ff0270f388227cd | — | — | origin |
| carrier_state | 1105 | 1104 | 3844519140 | 185 | 11438219 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff0270f3882278d→0x3ff0270f388227cd | — | — | fsu_taint |
| operand_read | 1106 | 1105 | 3844527610 | 185 | 11438235 | 0x00000000004006a4 | fmadd | 11438219/11438235 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1107 | 1106 | 3844527610 | 185 | 11438235 | 0x00000000004006a4 | fmadd | 11438219/11438235 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1108 | 1107 | 3844527610 | 185 | 11438235 | 0x00000000004006a4 | fmadd | 11438219/11438235 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1109 | 1108 | 3844528380 | 185 | 11438235 | 0x00000000004006a4 | fmadd | —/11438235 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1444 | 1109 | 9405606595 | 185 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1110 | — | 3889827095 | 186 | 11489353 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fd757afea3df6dd→0x3fd757afea3df6cd | — | — | origin |
| carrier_state | 1111 | 1110 | 3889827095 | 186 | 11489353 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fd757afea3df6dd→0x3fd757afea3df6cd | — | — | fsu_taint |
| operand_read | 1112 | 1111 | 3889835565 | 186 | 11489369 | 0x00000000004006cc | fmadd | 11489353/11489369 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1113 | 1112 | 3889835565 | 186 | 11489369 | 0x00000000004006cc | fmadd | 11489353/11489369 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1114 | 1113 | 3889835565 | 186 | 11489369 | 0x00000000004006cc | fmadd | 11489353/11489369 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1115 | 1114 | 3889836335 | 186 | 11489369 | 0x00000000004006cc | fmadd | —/11489369 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1445 | 1115 | 9405606595 | 186 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1116 | — | 3911516070 | 187 | 11530193 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe3663c74fb549f→0x3fe3663c74fb548f | — | — | origin |
| carrier_state | 1117 | 1116 | 3911516070 | 187 | 11530193 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3fe3663c74fb549f→0x3fe3663c74fb548f | — | — | fsu_taint |
| operand_read | 1118 | 1117 | 3911524540 | 187 | 11530209 | 0x00000000004006cc | fmadd | 11530193/11530209 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1119 | 1118 | 3911524540 | 187 | 11530209 | 0x00000000004006cc | fmadd | 11530193/11530209 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1120 | 1119 | 3911524540 | 187 | 11530209 | 0x00000000004006cc | fmadd | 11530193/11530209 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1121 | 1120 | 3911525310 | 187 | 11530209 | 0x00000000004006cc | fmadd | —/11530209 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1446 | 1121 | 9405606595 | 187 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1122 | — | 3995871880 | 188 | 11644819 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe2cf95d4e8fb01→0x3fe2cf95d4e9fb01 | — | — | origin |
| carrier_state | 1123 | 1122 | 3995871880 | 188 | 11644819 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fe2cf95d4e8fb01→0x3fe2cf95d4e9fb01 | — | — | fsu_taint |
| operand_read | 1124 | 1123 | 3995880350 | 188 | 11644835 | 0x00000000004006cc | fmadd | 11644819/11644835 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1125 | 1124 | 3995880350 | 188 | 11644835 | 0x00000000004006cc | fmadd | 11644819/11644835 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1126 | 1125 | 3995880350 | 188 | 11644835 | 0x00000000004006cc | fmadd | 11644819/11644835 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1127 | 1126 | 3995881120 | 188 | 11644835 | 0x00000000004006cc | fmadd | —/11644835 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1447 | 1127 | 9405606595 | 188 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1128 | — | 4071691085 | 189 | 11745295 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe5a96d4c33b539→0x3fe5a96d4c33b139 | — | — | origin |
| carrier_state | 1129 | 1128 | 4071691085 | 189 | 11745295 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fe5a96d4c33b539→0x3fe5a96d4c33b139 | — | — | fsu_taint |
| operand_read | 1130 | 1129 | 4071699555 | 189 | 11745311 | 0x00000000004006a4 | fmadd | 11745295/11745311 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1131 | 1130 | 4071699555 | 189 | 11745311 | 0x00000000004006a4 | fmadd | 11745295/11745311 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1132 | 1131 | 4071699555 | 189 | 11745311 | 0x00000000004006a4 | fmadd | 11745295/11745311 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1133 | 1132 | 4071700325 | 189 | 11745311 | 0x00000000004006a4 | fmadd | —/11745311 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1448 | 1133 | 9405606595 | 189 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 108 | — | 269147725 | 19 | 1024635 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fea666666666667→0x3fea666666666767 | — | — | origin |
| carrier_state | 109 | 108 | 269147725 | 19 | 1024635 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fea666666666667→0x3fea666666666767 | — | — | fsu_taint |
| operand_read | 110 | 109 | 269171980 | 19 | 1024742 | 0x0000000000400654 | fmadd | 1024635/1024742 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 111 | 110 | 269171980 | 19 | 1024742 | 0x0000000000400654 | fmadd | 1024635/1024742 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 112 | 111 | 269171980 | 19 | 1024742 | 0x0000000000400654 | fmadd | 1024635/1024742 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 113 | 112 | 269172750 | 19 | 1024742 | 0x0000000000400654 | fmadd | —/1024742 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1278 | 113 | 9405606595 | 19 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1134 | — | 4145427055 | 190 | 11856361 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fef35daad601ffc→0x3fef35daad609ffc | — | — | origin |
| carrier_state | 1135 | 1134 | 4145427055 | 190 | 11856361 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3fef35daad601ffc→0x3fef35daad609ffc | — | — | fsu_taint |
| operand_read | 1136 | 1135 | 4145435525 | 190 | 11856377 | 0x00000000004006a4 | fmadd | 11856361/11856377 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1137 | 1136 | 4145435525 | 190 | 11856377 | 0x00000000004006a4 | fmadd | 11856361/11856377 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1138 | 1137 | 4145435525 | 190 | 11856377 | 0x00000000004006a4 | fmadd | 11856361/11856377 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1139 | 1138 | 4145436295 | 190 | 11856377 | 0x00000000004006a4 | fmadd | —/11856377 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1449 | 1139 | 9405606595 | 190 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1140 | — | 4199956915 | 191 | 11941951 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe85ea24cc68230→0x3fe85ea24cc68220 | — | — | origin |
| carrier_state | 1141 | 1140 | 4199956915 | 191 | 11941951 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fe85ea24cc68230→0x3fe85ea24cc68220 | — | — | fsu_taint |
| operand_read | 1142 | 1141 | 4199965385 | 191 | 11941967 | 0x00000000004006cc | fmadd | 11941951/11941967 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1143 | 1142 | 4199965385 | 191 | 11941967 | 0x00000000004006cc | fmadd | 11941951/11941967 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1144 | 1143 | 4199965385 | 191 | 11941967 | 0x00000000004006cc | fmadd | 11941951/11941967 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1145 | 1144 | 4199966155 | 191 | 11941967 | 0x00000000004006cc | fmadd | —/11941967 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1450 | 1145 | 9405606595 | 191 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1146 | — | 4260100460 | 192 | 12012241 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff0f6577531db45→0x3ff0f6577531d945 | — | — | origin |
| carrier_state | 1147 | 1146 | 4260100460 | 192 | 12012241 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3ff0f6577531db45→0x3ff0f6577531d945 | — | — | fsu_taint |
| operand_read | 1148 | 1147 | 4260108930 | 192 | 12012257 | 0x00000000004006cc | fmadd | 12012241/12012257 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1149 | 1148 | 4260108930 | 192 | 12012257 | 0x00000000004006cc | fmadd | 12012241/12012257 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1150 | 1149 | 4260108930 | 192 | 12012257 | 0x00000000004006cc | fmadd | 12012241/12012257 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1151 | 1150 | 4260109700 | 192 | 12012257 | 0x00000000004006cc | fmadd | —/12012257 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1451 | 1151 | 9405606595 | 192 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1152 | — | 4308087630 | 193 | 12092797 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fdbb645a1cac084→0x3fdbb645a1cbc084 | — | — | origin |
| carrier_state | 1153 | 1152 | 4308087630 | 193 | 12092797 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fdbb645a1cac084→0x3fdbb645a1cbc084 | — | — | fsu_taint |
| operand_read | 1154 | 1153 | 4308096100 | 193 | 12092813 | 0x00000000004006a4 | fmadd | 12092797/12092813 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1155 | 1154 | 4308096100 | 193 | 12092813 | 0x00000000004006a4 | fmadd | 12092797/12092813 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1156 | 1155 | 4308096100 | 193 | 12092813 | 0x00000000004006a4 | fmadd | 12092797/12092813 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1157 | 1156 | 4308096870 | 193 | 12092813 | 0x00000000004006a4 | fmadd | —/12092813 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1452 | 1157 | 9405606595 | 193 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1158 | — | 4357364935 | 194 | 12152635 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fe4c43b2dd377e1→0x3fe4c43b2dd377e0 | — | — | origin |
| carrier_state | 1159 | 1158 | 4357364935 | 194 | 12152635 | 0x00000000004006cc | fmadd | —/— | 45 | — | 64@0 | 0x3fe4c43b2dd377e1→0x3fe4c43b2dd377e0 | — | — | fsu_taint |
| operand_read | 1160 | 1159 | 4357373405 | 194 | 12152651 | 0x00000000004006cc | fmadd | 12152635/12152651 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1161 | 1160 | 4357373405 | 194 | 12152651 | 0x00000000004006cc | fmadd | 12152635/12152651 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1162 | 1161 | 4357373405 | 194 | 12152651 | 0x00000000004006cc | fmadd | 12152635/12152651 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1163 | 1162 | 4357374175 | 194 | 12152651 | 0x00000000004006cc | fmadd | —/12152651 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1453 | 1163 | 9405606595 | 194 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1164 | — | 4390499190 | 195 | 12211903 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fea94ff0025bfae→0x3fea94ff0025afae | — | — | origin |
| carrier_state | 1165 | 1164 | 4390499190 | 195 | 12211903 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fea94ff0025bfae→0x3fea94ff0025afae | — | — | fsu_taint |
| operand_read | 1166 | 1165 | 4390507660 | 195 | 12211919 | 0x00000000004006a4 | fmadd | 12211903/12211919 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1167 | 1166 | 4390507660 | 195 | 12211919 | 0x00000000004006a4 | fmadd | 12211903/12211919 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1168 | 1167 | 4390507660 | 195 | 12211919 | 0x00000000004006a4 | fmadd | 12211903/12211919 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1169 | 1168 | 4390508430 | 195 | 12211919 | 0x00000000004006a4 | fmadd | —/12211919 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1454 | 1169 | 9405606595 | 195 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1170 | — | 4471865090 | 196 | 12323789 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff27a5b0ff10ecc→0x3ff27a5b0ff10eec | — | — | origin |
| carrier_state | 1171 | 1170 | 4471865090 | 196 | 12323789 | 0x00000000004006cc | fmadd | —/— | 5 | — | 64@0 | 0x3ff27a5b0ff10ecc→0x3ff27a5b0ff10eec | — | — | fsu_taint |
| operand_read | 1172 | 1171 | 4471873560 | 196 | 12323805 | 0x00000000004006cc | fmadd | 12323789/12323805 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1173 | 1172 | 4471873560 | 196 | 12323805 | 0x00000000004006cc | fmadd | 12323789/12323805 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1174 | 1173 | 4471873560 | 196 | 12323805 | 0x00000000004006cc | fmadd | 12323789/12323805 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1175 | 1174 | 4471874330 | 196 | 12323805 | 0x00000000004006cc | fmadd | —/12323805 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1455 | 1175 | 9405606595 | 196 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1176 | — | 4508211785 | 197 | 12372113 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff65a07b352a843→0x3ff65a07b352ac43 | — | — | origin |
| carrier_state | 1177 | 1176 | 4508211785 | 197 | 12372113 | 0x00000000004006a4 | fmadd | —/— | 45 | — | 64@0 | 0x3ff65a07b352a843→0x3ff65a07b352ac43 | — | — | fsu_taint |
| operand_read | 1178 | 1177 | 4508220255 | 197 | 12372129 | 0x00000000004006a4 | fmadd | 12372113/12372129 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1179 | 1178 | 4508220255 | 197 | 12372129 | 0x00000000004006a4 | fmadd | 12372113/12372129 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1180 | 1179 | 4508220255 | 197 | 12372129 | 0x00000000004006a4 | fmadd | 12372113/12372129 | 45 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1181 | 1180 | 4508221025 | 197 | 12372129 | 0x00000000004006a4 | fmadd | —/12372129 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1456 | 1181 | 9405606595 | 197 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1182 | — | 4561377975 | 198 | 12447631 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff624894c447c31→0x3ff624894c447c11 | — | — | origin |
| carrier_state | 1183 | 1182 | 4561377975 | 198 | 12447631 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3ff624894c447c31→0x3ff624894c447c11 | — | — | fsu_taint |
| operand_read | 1184 | 1183 | 4561386445 | 198 | 12447647 | 0x00000000004006cc | fmadd | 12447631/12447647 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1185 | 1184 | 4561386445 | 198 | 12447647 | 0x00000000004006cc | fmadd | 12447631/12447647 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1186 | 1185 | 4561386445 | 198 | 12447647 | 0x00000000004006cc | fmadd | 12447631/12447647 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1187 | 1186 | 4561387215 | 198 | 12447647 | 0x00000000004006cc | fmadd | —/12447647 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1457 | 1187 | 9405606595 | 198 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1188 | — | 4612264580 | 199 | 12515003 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fd76a0dbad3a603→0x3fd76a0dbad3a601 | — | — | origin |
| carrier_state | 1189 | 1188 | 4612264580 | 199 | 12515003 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fd76a0dbad3a603→0x3fd76a0dbad3a601 | — | — | fsu_taint |
| operand_read | 1190 | 1189 | 4612273050 | 199 | 12515019 | 0x00000000004006a4 | fmadd | 12515003/12515019 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1191 | 1190 | 4612273050 | 199 | 12515019 | 0x00000000004006a4 | fmadd | 12515003/12515019 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1192 | 1191 | 4612273050 | 199 | 12515019 | 0x00000000004006a4 | fmadd | 12515003/12515019 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1193 | 1192 | 4612273820 | 199 | 12515019 | 0x00000000004006a4 | fmadd | —/12515019 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1458 | 1193 | 9405606595 | 199 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 6 | — | 34994575 | 2 | 100691 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x408d600000000000→0x408d600000004000 | — | — | origin |
| carrier_state | 7 | 6 | 34994575 | 2 | 100691 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x408d600000000000→0x408d600000004000 | — | — | fsu_taint |
| operand_read | 8 | 7 | 34996500 | 2 | 100694 | 0x0000000000400654 | fmadd | 100691/100694 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 9 | 8 | 34996500 | 2 | 100694 | 0x0000000000400654 | fmadd | 100691/100694 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 10 | 9 | 34996500 | 2 | 100694 | 0x0000000000400654 | fmadd | 100691/100694 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 11 | 10 | 34997270 | 2 | 100694 | 0x0000000000400654 | fmadd | —/100694 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1261 | 11 | 9405606595 | 2 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 114 | — | 287327425 | 20 | 1096562 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fed99999999999a→0x3fed99999999989a | — | — | origin |
| carrier_state | 115 | 114 | 287327425 | 20 | 1096562 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3fed99999999999a→0x3fed99999999989a | — | — | fsu_taint |
| operand_read | 116 | 115 | 287362845 | 20 | 1096706 | 0x0000000000400654 | fmadd | 1096562/1096706 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 117 | 116 | 287362845 | 20 | 1096706 | 0x0000000000400654 | fmadd | 1096562/1096706 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 118 | 117 | 287362845 | 20 | 1096706 | 0x0000000000400654 | fmadd | 1096562/1096706 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 119 | 118 | 287363615 | 20 | 1096706 | 0x0000000000400654 | fmadd | —/1096706 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1279 | 119 | 9405606595 | 20 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1194 | — | 4643394910 | 200 | 12558665 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fdec6c97d8cf399→0x3fdec6c97d8ef399 | — | — | origin |
| carrier_state | 1195 | 1194 | 4643394910 | 200 | 12558665 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fdec6c97d8cf399→0x3fdec6c97d8ef399 | — | — | fsu_taint |
| operand_read | 1196 | 1195 | 4643403380 | 200 | 12558681 | 0x00000000004006cc | fmadd | 12558665/12558681 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1197 | 1196 | 4643403380 | 200 | 12558681 | 0x00000000004006cc | fmadd | 12558665/12558681 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1198 | 1197 | 4643403380 | 200 | 12558681 | 0x00000000004006cc | fmadd | 12558665/12558681 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1199 | 1198 | 4643404150 | 200 | 12558681 | 0x00000000004006cc | fmadd | —/12558681 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1459 | 1199 | 9405606595 | 200 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1200 | — | 4726861755 | 201 | 12671611 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fedad4f5903a754→0x3fedad4f5903a744 | — | — | origin |
| carrier_state | 1201 | 1200 | 4726861755 | 201 | 12671611 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0x3fedad4f5903a754→0x3fedad4f5903a744 | — | — | fsu_taint |
| operand_read | 1202 | 1201 | 4726870225 | 201 | 12671627 | 0x00000000004006cc | fmadd | 12671611/12671627 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1203 | 1202 | 4726870225 | 201 | 12671627 | 0x00000000004006cc | fmadd | 12671611/12671627 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1204 | 1203 | 4726870225 | 201 | 12671627 | 0x00000000004006cc | fmadd | 12671611/12671627 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1205 | 1204 | 4726870995 | 201 | 12671627 | 0x00000000004006cc | fmadd | —/12671627 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1460 | 1205 | 9405606595 | 201 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1206 | — | 4808764345 | 202 | 12787799 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe978a6dacabc53→0x3fe978a6dacabcd3 | — | — | origin |
| carrier_state | 1207 | 1206 | 4808764345 | 202 | 12787799 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe978a6dacabc53→0x3fe978a6dacabcd3 | — | — | fsu_taint |
| operand_read | 1208 | 1207 | 4808772815 | 202 | 12787815 | 0x00000000004006a4 | fmadd | 12787799/12787815 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1209 | 1208 | 4808772815 | 202 | 12787815 | 0x00000000004006a4 | fmadd | 12787799/12787815 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1210 | 1209 | 4808772815 | 202 | 12787815 | 0x00000000004006a4 | fmadd | 12787799/12787815 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1211 | 1210 | 4808773585 | 202 | 12787815 | 0x00000000004006a4 | fmadd | —/12787815 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1461 | 1211 | 9405606595 | 202 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1212 | — | 4875959550 | 203 | 12891529 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe359ddc1e7967d→0x3fe359ddc1e5967d | — | — | origin |
| carrier_state | 1213 | 1212 | 4875959550 | 203 | 12891529 | 0x00000000004006a4 | fmadd | —/— | 5 | — | 64@0 | 0x3fe359ddc1e7967d→0x3fe359ddc1e5967d | — | — | fsu_taint |
| operand_read | 1214 | 1213 | 4875968020 | 203 | 12891545 | 0x00000000004006a4 | fmadd | 12891529/12891545 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1215 | 1214 | 4875968020 | 203 | 12891545 | 0x00000000004006a4 | fmadd | 12891529/12891545 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1216 | 1215 | 4875968020 | 203 | 12891545 | 0x00000000004006a4 | fmadd | 12891529/12891545 | 5 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1217 | 1216 | 4875968790 | 203 | 12891545 | 0x00000000004006a4 | fmadd | —/12891545 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1462 | 1217 | 9405606595 | 203 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1218 | — | 4953489695 | 204 | 13003827 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3ff26550870110a1→0x3ff26550870111a1 | — | — | origin |
| carrier_state | 1219 | 1218 | 4953489695 | 204 | 13003827 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3ff26550870110a1→0x3ff26550870111a1 | — | — | fsu_taint |
| operand_read | 1220 | 1219 | 4953498165 | 204 | 13003843 | 0x00000000004006a4 | fmadd | 13003827/13003843 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1221 | 1220 | 4953498165 | 204 | 13003843 | 0x00000000004006a4 | fmadd | 13003827/13003843 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1222 | 1221 | 4953498165 | 204 | 13003843 | 0x00000000004006a4 | fmadd | 13003827/13003843 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1223 | 1222 | 4953498935 | 204 | 13003843 | 0x00000000004006a4 | fmadd | —/13003843 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1463 | 1223 | 9405606595 | 204 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1224 | — | 5016754050 | 205 | 13084321 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fd1d65a14488c61→0x3fd1d65a14480c61 | — | — | origin |
| carrier_state | 1225 | 1224 | 5016754050 | 205 | 13084321 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fd1d65a14488c61→0x3fd1d65a14480c61 | — | — | fsu_taint |
| operand_read | 1226 | 1225 | 5016762520 | 205 | 13084337 | 0x00000000004006cc | fmadd | 13084321/13084337 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1227 | 1226 | 5016762520 | 205 | 13084337 | 0x00000000004006cc | fmadd | 13084321/13084337 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1228 | 1227 | 5016762520 | 205 | 13084337 | 0x00000000004006cc | fmadd | 13084321/13084337 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1229 | 1228 | 5016763290 | 205 | 13084337 | 0x00000000004006cc | fmadd | —/13084337 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1464 | 1229 | 9405606595 | 205 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1230 | — | 5068097265 | 206 | 13160005 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0xbfc057d9dba908a3→0xbfc057d9dba908e3 | — | — | origin |
| carrier_state | 1231 | 1230 | 5068097265 | 206 | 13160005 | 0x00000000004006a4 | fmadd | —/— | 46 | — | 64@0 | 0xbfc057d9dba908a3→0xbfc057d9dba908e3 | — | — | fsu_taint |
| operand_read | 1232 | 1231 | 5068105735 | 206 | 13160021 | 0x00000000004006a4 | fmadd | 13160005/13160021 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1233 | 1232 | 5068105735 | 206 | 13160021 | 0x00000000004006a4 | fmadd | 13160005/13160021 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1234 | 1233 | 5068105735 | 206 | 13160021 | 0x00000000004006a4 | fmadd | 13160005/13160021 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1235 | 1234 | 5068106505 | 206 | 13160021 | 0x00000000004006a4 | fmadd | —/13160021 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1465 | 1235 | 9405606595 | 206 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1236 | — | 5139755775 | 207 | 13265663 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3feb36eb4e981388→0x3feb36eb4e985388 | — | — | origin |
| carrier_state | 1237 | 1236 | 5139755775 | 207 | 13265663 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3feb36eb4e981388→0x3feb36eb4e985388 | — | — | fsu_taint |
| operand_read | 1238 | 1237 | 5139764245 | 207 | 13265679 | 0x00000000004006a4 | fmadd | 13265663/13265679 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1239 | 1238 | 5139764245 | 207 | 13265679 | 0x00000000004006a4 | fmadd | 13265663/13265679 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1240 | 1239 | 5139764245 | 207 | 13265679 | 0x00000000004006a4 | fmadd | 13265663/13265679 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1241 | 1240 | 5139765015 | 207 | 13265679 | 0x00000000004006a4 | fmadd | —/13265679 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1466 | 1241 | 9405606595 | 207 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1242 | — | 5220375160 | 208 | 13379253 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fce039abf338716→0x3fce039abf338796 | — | — | origin |
| carrier_state | 1243 | 1242 | 5220375160 | 208 | 13379253 | 0x00000000004006cc | fmadd | —/— | 1 | — | 64@0 | 0x3fce039abf338716→0x3fce039abf338796 | — | — | fsu_taint |
| operand_read | 1244 | 1243 | 5220383630 | 208 | 13379269 | 0x00000000004006cc | fmadd | 13379253/13379269 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1245 | 1244 | 5220383630 | 208 | 13379269 | 0x00000000004006cc | fmadd | 13379253/13379269 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1246 | 1245 | 5220383630 | 208 | 13379269 | 0x00000000004006cc | fmadd | 13379253/13379269 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1247 | 1246 | 5220384400 | 208 | 13379269 | 0x00000000004006cc | fmadd | —/13379269 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1467 | 1247 | 9405606595 | 208 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1248 | — | 5306131600 | 209 | 13495879 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0xbfa5a1cac083126b→0xbfa5a1cac083136b | — | — | origin |
| carrier_state | 1249 | 1248 | 5306131600 | 209 | 13495879 | 0x00000000004006cc | fmadd | —/— | 46 | — | 64@0 | 0xbfa5a1cac083126b→0xbfa5a1cac083136b | — | — | fsu_taint |
| operand_read | 1250 | 1249 | 5306140070 | 209 | 13495895 | 0x00000000004006cc | fmadd | 13495879/13495895 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1251 | 1250 | 5306140070 | 209 | 13495895 | 0x00000000004006cc | fmadd | 13495879/13495895 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1252 | 1251 | 5306140070 | 209 | 13495895 | 0x00000000004006cc | fmadd | 13495879/13495895 | 46 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1253 | 1252 | 5306140840 | 209 | 13495895 | 0x00000000004006cc | fmadd | —/13495895 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1468 | 1253 | 9405606595 | 209 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 120 | — | 300613390 | 21 | 1148869 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x408ea80000000000→0x408ea80000000001 | — | — | origin |
| carrier_state | 121 | 120 | 300613390 | 21 | 1148869 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x408ea80000000000→0x408ea80000000001 | — | — | fsu_taint |
| operand_read | 122 | 121 | 300617240 | 21 | 1148872 | 0x000000000040065c | fmadd | 1148869/1148872 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 123 | 122 | 300617240 | 21 | 1148872 | 0x000000000040065c | fmadd | 1148869/1148872 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 124 | 123 | 300617240 | 21 | 1148872 | 0x000000000040065c | fmadd | 1148869/1148872 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 125 | 124 | 300618010 | 21 | 1148872 | 0x000000000040065c | fmadd | —/1148872 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1280 | 125 | 9405606595 | 21 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 1254 | — | 5369103740 | 210 | 13575763 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fe59231c64ba94c→0x3fe59231c64ba94d | — | — | origin |
| carrier_state | 1255 | 1254 | 5369103740 | 210 | 13575763 | 0x00000000004006a4 | fmadd | —/— | 1 | — | 64@0 | 0x3fe59231c64ba94c→0x3fe59231c64ba94d | — | — | fsu_taint |
| operand_read | 1256 | 1255 | 5369185360 | 210 | 13575779 | 0x00000000004006a4 | fmadd | 13575763/13575779 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| execute | 1257 | 1256 | 5369185360 | 210 | 13575779 | 0x00000000004006a4 | fmadd | 13575763/13575779 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 1258 | 1257 | 5369185360 | 210 | 13575779 | 0x00000000004006a4 | fmadd | 13575763/13575779 | 1 | 5 | —@— | —→— | — | — | fsu_taint |
| commit | 1259 | 1258 | 5369186130 | 210 | 13575779 | 0x00000000004006a4 | fmadd | —/13575779 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1469 | 1259 | 9405606595 | 210 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 126 | — | 315676515 | 22 | 1208272 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbf889374bc6a7ef4→0xbf889374bc6a7ed4 | — | — | origin |
| carrier_state | 127 | 126 | 315676515 | 22 | 1208272 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbf889374bc6a7ef4→0xbf889374bc6a7ed4 | — | — | fsu_taint |
| operand_read | 128 | 127 | 315691915 | 22 | 1208342 | 0x0000000000400654 | fmadd | 1208272/1208342 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 129 | 128 | 315691915 | 22 | 1208342 | 0x0000000000400654 | fmadd | 1208272/1208342 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 130 | 129 | 315691915 | 22 | 1208342 | 0x0000000000400654 | fmadd | 1208272/1208342 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 131 | 130 | 315692685 | 22 | 1208342 | 0x0000000000400654 | fmadd | —/1208342 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1281 | 131 | 9405606595 | 22 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 132 | — | 337381275 | 23 | 1293553 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4088480000000000→0x4088480000008000 | — | — | origin |
| carrier_state | 133 | 132 | 337381275 | 23 | 1293553 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4088480000000000→0x4088480000008000 | — | — | fsu_taint |
| operand_read | 134 | 133 | 337385125 | 23 | 1293556 | 0x000000000040065c | fmadd | 1293553/1293556 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 135 | 134 | 337385125 | 23 | 1293556 | 0x000000000040065c | fmadd | 1293553/1293556 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 136 | 135 | 337385125 | 23 | 1293556 | 0x000000000040065c | fmadd | 1293553/1293556 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 137 | 136 | 337385895 | 23 | 1293556 | 0x000000000040065c | fmadd | —/1293556 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1282 | 137 | 9405606595 | 23 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 138 | — | 356158110 | 24 | 1367894 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff70a3d70a3d70a→0x3ff70a3d70a3d30a | — | — | origin |
| carrier_state | 139 | 138 | 356158110 | 24 | 1367894 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff70a3d70a3d70a→0x3ff70a3d70a3d30a | — | — | fsu_taint |
| operand_read | 140 | 139 | 356193530 | 24 | 1368038 | 0x0000000000400654 | fmadd | 1367894/1368038 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 141 | 140 | 356193530 | 24 | 1368038 | 0x0000000000400654 | fmadd | 1367894/1368038 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 142 | 141 | 356193530 | 24 | 1368038 | 0x0000000000400654 | fmadd | 1367894/1368038 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 143 | 142 | 356194300 | 24 | 1368038 | 0x0000000000400654 | fmadd | —/1368038 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1283 | 143 | 9405606595 | 24 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 144 | — | 378328720 | 25 | 1455443 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4053000000000000→0x4053000000000001 | — | — | origin |
| carrier_state | 145 | 144 | 378328720 | 25 | 1455443 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x4053000000000000→0x4053000000000001 | — | — | fsu_taint |
| operand_read | 146 | 145 | 378330645 | 25 | 1455446 | 0x0000000000400654 | fmadd | 1455443/1455446 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 147 | 146 | 378330645 | 25 | 1455446 | 0x0000000000400654 | fmadd | 1455443/1455446 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 148 | 147 | 378330645 | 25 | 1455446 | 0x0000000000400654 | fmadd | 1455443/1455446 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 149 | 148 | 378331415 | 25 | 1455446 | 0x0000000000400654 | fmadd | —/1455446 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1284 | 149 | 9405606595 | 25 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 150 | — | 397763520 | 26 | 1532161 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x407ce00000000000→0x407ce00000004000 | — | — | origin |
| carrier_state | 151 | 150 | 397763520 | 26 | 1532161 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x407ce00000000000→0x407ce00000004000 | — | — | fsu_taint |
| operand_read | 152 | 151 | 397767370 | 26 | 1532164 | 0x000000000040065c | fmadd | 1532161/1532164 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 153 | 152 | 397767370 | 26 | 1532164 | 0x000000000040065c | fmadd | 1532161/1532164 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 154 | 153 | 397767370 | 26 | 1532164 | 0x000000000040065c | fmadd | 1532161/1532164 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 155 | 154 | 397768140 | 26 | 1532164 | 0x000000000040065c | fmadd | —/1532164 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1285 | 155 | 9405606595 | 26 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 156 | — | 416940370 | 27 | 1607723 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x408d900000000000→0x408d900000000020 | — | — | origin |
| carrier_state | 157 | 156 | 416940370 | 27 | 1607723 | 0x0000000000400648 | scvtf | —/— | 46 | — | 64@0 | 0x408d900000000000→0x408d900000000020 | — | — | fsu_taint |
| operand_read | 158 | 157 | 416942295 | 27 | 1607726 | 0x0000000000400654 | fmadd | 1607723/1607726 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 159 | 158 | 416942295 | 27 | 1607726 | 0x0000000000400654 | fmadd | 1607723/1607726 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 160 | 159 | 416942295 | 27 | 1607726 | 0x0000000000400654 | fmadd | 1607723/1607726 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 161 | 160 | 416943065 | 27 | 1607726 | 0x0000000000400654 | fmadd | —/1607726 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1286 | 161 | 9405606595 | 27 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 162 | — | 431269300 | 28 | 1664245 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x408d600000000000→0x408d600000001000 | — | — | origin |
| carrier_state | 163 | 162 | 431269300 | 28 | 1664245 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x408d600000000000→0x408d600000001000 | — | — | fsu_taint |
| operand_read | 164 | 163 | 431273150 | 28 | 1664248 | 0x000000000040065c | fmadd | 1664245/1664248 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 165 | 164 | 431273150 | 28 | 1664248 | 0x000000000040065c | fmadd | 1664245/1664248 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 166 | 165 | 431273150 | 28 | 1664248 | 0x000000000040065c | fmadd | 1664245/1664248 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 167 | 166 | 431273920 | 28 | 1664248 | 0x000000000040065c | fmadd | —/1664248 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1287 | 167 | 9405606595 | 28 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 168 | — | 440572440 | 29 | 1701071 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x407d900000000000→0x407d900000000010 | — | — | origin |
| carrier_state | 169 | 168 | 440572440 | 29 | 1701071 | 0x0000000000400648 | scvtf | —/— | 45 | — | 64@0 | 0x407d900000000000→0x407d900000000010 | — | — | fsu_taint |
| operand_read | 170 | 169 | 440574365 | 29 | 1701074 | 0x0000000000400654 | fmadd | 1701071/1701074 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 171 | 170 | 440574365 | 29 | 1701074 | 0x0000000000400654 | fmadd | 1701071/1701074 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 172 | 171 | 440574365 | 29 | 1701074 | 0x0000000000400654 | fmadd | 1701071/1701074 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 173 | 172 | 440575135 | 29 | 1701074 | 0x0000000000400654 | fmadd | —/1701074 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1288 | 173 | 9405606595 | 29 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 12 | — | 46149565 | 3 | 144508 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fdfbe76c8b43958→0x3fdfbe76c8b4395a | — | — | origin |
| carrier_state | 13 | 12 | 46149565 | 3 | 144508 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fdfbe76c8b43958→0x3fdfbe76c8b4395a | — | — | fsu_taint |
| operand_read | 14 | 13 | 46164965 | 3 | 144578 | 0x0000000000400654 | fmadd | 144508/144578 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 15 | 14 | 46164965 | 3 | 144578 | 0x0000000000400654 | fmadd | 144508/144578 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 16 | 15 | 46164965 | 3 | 144578 | 0x0000000000400654 | fmadd | 144508/144578 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 17 | 16 | 46165735 | 3 | 144578 | 0x0000000000400654 | fmadd | —/144578 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1262 | 17 | 9405606595 | 3 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 174 | — | 457782325 | 30 | 1768468 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfc78d4fdf3b645a→0xbfc78d4fdf3b655a | — | — | origin |
| carrier_state | 175 | 174 | 457782325 | 30 | 1768468 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfc78d4fdf3b645a→0xbfc78d4fdf3b655a | — | — | fsu_taint |
| operand_read | 176 | 175 | 457797725 | 30 | 1768538 | 0x0000000000400654 | fmadd | 1768468/1768538 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 177 | 176 | 457797725 | 30 | 1768538 | 0x0000000000400654 | fmadd | 1768468/1768538 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 178 | 177 | 457797725 | 30 | 1768538 | 0x0000000000400654 | fmadd | 1768468/1768538 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 179 | 178 | 457798495 | 30 | 1768538 | 0x0000000000400654 | fmadd | —/1768538 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1289 | 179 | 9405606595 | 30 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 180 | — | 472164770 | 31 | 1825488 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x408e200000000000→0x408e200000000040 | — | — | origin |
| carrier_state | 181 | 180 | 472164770 | 31 | 1825488 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x408e200000000000→0x408e200000000040 | — | — | fsu_taint |
| operand_read | 182 | 181 | 472169005 | 31 | 1825491 | 0x0000000000400658 | fmadd | 1825488/1825491 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 183 | 182 | 472169005 | 31 | 1825491 | 0x0000000000400658 | fmadd | 1825488/1825491 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 184 | 183 | 472169005 | 31 | 1825491 | 0x0000000000400658 | fmadd | 1825488/1825491 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 185 | 184 | 472169775 | 31 | 1825491 | 0x0000000000400658 | fmadd | —/1825491 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1290 | 185 | 9405606595 | 31 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 186 | — | 491785525 | 32 | 1903211 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4082500000000000→0x4082500000000002 | — | — | origin |
| carrier_state | 187 | 186 | 491785525 | 32 | 1903211 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4082500000000000→0x4082500000000002 | — | — | fsu_taint |
| operand_read | 188 | 187 | 491787450 | 32 | 1903214 | 0x0000000000400654 | fmadd | 1903211/1903214 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 189 | 188 | 491787450 | 32 | 1903214 | 0x0000000000400654 | fmadd | 1903211/1903214 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 190 | 189 | 491787450 | 32 | 1903214 | 0x0000000000400654 | fmadd | 1903211/1903214 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 191 | 190 | 491788220 | 32 | 1903214 | 0x0000000000400654 | fmadd | —/1903214 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1291 | 191 | 9405606595 | 32 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 192 | — | 499798145 | 33 | 1934351 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4080c80000000000→0x4080c80000000010 | — | — | origin |
| carrier_state | 193 | 192 | 499798145 | 33 | 1934351 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4080c80000000000→0x4080c80000000010 | — | — | fsu_taint |
| operand_read | 194 | 193 | 499800070 | 33 | 1934354 | 0x0000000000400654 | fmadd | 1934351/1934354 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 195 | 194 | 499800070 | 33 | 1934354 | 0x0000000000400654 | fmadd | 1934351/1934354 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 196 | 195 | 499800070 | 33 | 1934354 | 0x0000000000400654 | fmadd | 1934351/1934354 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 197 | 196 | 499800840 | 33 | 1934354 | 0x0000000000400654 | fmadd | —/1934354 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1292 | 197 | 9405606595 | 33 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 198 | — | 519848560 | 34 | 2013876 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4046800000000000→0x4046800000002000 | — | — | origin |
| carrier_state | 199 | 198 | 519848560 | 34 | 2013876 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x4046800000000000→0x4046800000002000 | — | — | fsu_taint |
| operand_read | 200 | 199 | 519852795 | 34 | 2013879 | 0x0000000000400658 | fmadd | 2013876/2013879 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 201 | 200 | 519852795 | 34 | 2013879 | 0x0000000000400658 | fmadd | 2013876/2013879 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 202 | 201 | 519852795 | 34 | 2013879 | 0x0000000000400658 | fmadd | 2013876/2013879 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 203 | 202 | 519853565 | 34 | 2013879 | 0x0000000000400658 | fmadd | —/2013879 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1293 | 203 | 9405606595 | 34 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 204 | — | 530443760 | 35 | 2055744 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4084800000000000→0x4084800000008000 | — | — | origin |
| carrier_state | 205 | 204 | 530443760 | 35 | 2055744 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4084800000000000→0x4084800000008000 | — | — | fsu_taint |
| operand_read | 206 | 205 | 530447995 | 35 | 2055747 | 0x0000000000400658 | fmadd | 2055744/2055747 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 207 | 206 | 530447995 | 35 | 2055747 | 0x0000000000400658 | fmadd | 2055744/2055747 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 208 | 207 | 530447995 | 35 | 2055747 | 0x0000000000400658 | fmadd | 2055744/2055747 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 209 | 208 | 530448765 | 35 | 2055747 | 0x0000000000400658 | fmadd | —/2055747 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1294 | 209 | 9405606595 | 35 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 210 | — | 542772230 | 36 | 2104344 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x406d600000000000→0x406d600000004000 | — | — | origin |
| carrier_state | 211 | 210 | 542772230 | 36 | 2104344 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x406d600000000000→0x406d600000004000 | — | — | fsu_taint |
| operand_read | 212 | 211 | 542776465 | 36 | 2104347 | 0x0000000000400658 | fmadd | 2104344/2104347 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 213 | 212 | 542776465 | 36 | 2104347 | 0x0000000000400658 | fmadd | 2104344/2104347 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 214 | 213 | 542776465 | 36 | 2104347 | 0x0000000000400658 | fmadd | 2104344/2104347 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 215 | 214 | 542777235 | 36 | 2104347 | 0x0000000000400658 | fmadd | —/2104347 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1295 | 215 | 9405606595 | 36 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 216 | — | 558490625 | 37 | 2166372 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4085380000000000→0x4085380000020000 | — | — | origin |
| carrier_state | 217 | 216 | 558490625 | 37 | 2166372 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4085380000000000→0x4085380000020000 | — | — | fsu_taint |
| operand_read | 218 | 217 | 558494860 | 37 | 2166375 | 0x0000000000400658 | fmadd | 2166372/2166375 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 219 | 218 | 558494860 | 37 | 2166375 | 0x0000000000400658 | fmadd | 2166372/2166375 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 220 | 219 | 558494860 | 37 | 2166375 | 0x0000000000400658 | fmadd | 2166372/2166375 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 221 | 220 | 558495630 | 37 | 2166375 | 0x0000000000400658 | fmadd | —/2166375 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1296 | 221 | 9405606595 | 37 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 222 | — | 567864990 | 38 | 2203488 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4089200000000000→0x4089200000010000 | — | — | origin |
| carrier_state | 223 | 222 | 567864990 | 38 | 2203488 | 0x000000000040064c | scvtf | —/— | 46 | — | 64@0 | 0x4089200000000000→0x4089200000010000 | — | — | fsu_taint |
| operand_read | 224 | 223 | 567869225 | 38 | 2203491 | 0x0000000000400658 | fmadd | 2203488/2203491 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 225 | 224 | 567869225 | 38 | 2203491 | 0x0000000000400658 | fmadd | 2203488/2203491 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 226 | 225 | 567869225 | 38 | 2203491 | 0x0000000000400658 | fmadd | 2203488/2203491 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 227 | 226 | 567869995 | 38 | 2203491 | 0x0000000000400658 | fmadd | —/2203491 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1297 | 227 | 9405606595 | 38 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 228 | — | 590348990 | 39 | 2292086 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff7ef9db22d0e56→0x3ff7ef9db22d0f56 | — | — | origin |
| carrier_state | 229 | 228 | 590348990 | 39 | 2292086 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff7ef9db22d0e56→0x3ff7ef9db22d0f56 | — | — | fsu_taint |
| operand_read | 230 | 229 | 590384410 | 39 | 2292230 | 0x0000000000400654 | fmadd | 2292086/2292230 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 231 | 230 | 590384410 | 39 | 2292230 | 0x0000000000400654 | fmadd | 2292086/2292230 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 232 | 231 | 590384410 | 39 | 2292230 | 0x0000000000400654 | fmadd | 2292086/2292230 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 233 | 232 | 590385180 | 39 | 2292230 | 0x0000000000400654 | fmadd | —/2292230 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1298 | 233 | 9405606595 | 39 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 18 | — | 54420520 | 4 | 177664 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0x3fddb22d0e560419→0x3fddb22d0e560411 | — | — | origin |
| carrier_state | 19 | 18 | 54420520 | 4 | 177664 | 0x000000000040065c | fmadd | —/— | 45 | — | 64@0 | 0x3fddb22d0e560419→0x3fddb22d0e560411 | — | — | fsu_taint |
| operand_read | 20 | 19 | 54435920 | 4 | 177734 | 0x0000000000400654 | fmadd | 177664/177734 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 21 | 20 | 54435920 | 4 | 177734 | 0x0000000000400654 | fmadd | 177664/177734 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 22 | 21 | 54435920 | 4 | 177734 | 0x0000000000400654 | fmadd | 177664/177734 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 23 | 22 | 54436690 | 4 | 177734 | 0x0000000000400654 | fmadd | —/177734 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1263 | 23 | 9405606595 | 4 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 234 | — | 605399410 | 40 | 2351487 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fe37ced916872b0→0x3fe37ced916870b0 | — | — | origin |
| carrier_state | 235 | 234 | 605399410 | 40 | 2351487 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fe37ced916872b0→0x3fe37ced916870b0 | — | — | fsu_taint |
| operand_read | 236 | 235 | 605423665 | 40 | 2351594 | 0x0000000000400654 | fmadd | 2351487/2351594 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 237 | 236 | 605423665 | 40 | 2351594 | 0x0000000000400654 | fmadd | 2351487/2351594 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 238 | 237 | 605423665 | 40 | 2351594 | 0x0000000000400654 | fmadd | 2351487/2351594 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 239 | 238 | 605424435 | 40 | 2351594 | 0x0000000000400654 | fmadd | —/2351594 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1299 | 239 | 9405606595 | 40 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 240 | — | 617760220 | 41 | 2399976 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4073600000000000→0x4073600000002000 | — | — | origin |
| carrier_state | 241 | 240 | 617760220 | 41 | 2399976 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4073600000000000→0x4073600000002000 | — | — | fsu_taint |
| operand_read | 242 | 241 | 617764455 | 41 | 2399979 | 0x0000000000400658 | fmadd | 2399976/2399979 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 243 | 242 | 617764455 | 41 | 2399979 | 0x0000000000400658 | fmadd | 2399976/2399979 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 244 | 243 | 617764455 | 41 | 2399979 | 0x0000000000400658 | fmadd | 2399976/2399979 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 245 | 244 | 617765225 | 41 | 2399979 | 0x0000000000400658 | fmadd | —/2399979 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1300 | 245 | 9405606595 | 41 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 246 | — | 628286505 | 42 | 2441882 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3fe2e978d4fdf3b6→0x3fe2e978d4fdf3b7 | — | — | origin |
| carrier_state | 247 | 246 | 628286505 | 42 | 2441882 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3fe2e978d4fdf3b6→0x3fe2e978d4fdf3b7 | — | — | fsu_taint |
| operand_read | 248 | 247 | 628321925 | 42 | 2442026 | 0x0000000000400654 | fmadd | 2441882/2442026 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 249 | 248 | 628321925 | 42 | 2442026 | 0x0000000000400654 | fmadd | 2441882/2442026 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 250 | 249 | 628321925 | 42 | 2442026 | 0x0000000000400654 | fmadd | 2441882/2442026 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 251 | 250 | 628322695 | 42 | 2442026 | 0x0000000000400654 | fmadd | —/2442026 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1301 | 251 | 9405606595 | 42 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 252 | — | 637092610 | 43 | 2476693 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4089680000000000→0x4089680000004000 | — | — | origin |
| carrier_state | 253 | 252 | 637092610 | 43 | 2476693 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4089680000000000→0x4089680000004000 | — | — | fsu_taint |
| operand_read | 254 | 253 | 637096460 | 43 | 2476696 | 0x000000000040065c | fmadd | 2476693/2476696 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 255 | 254 | 637096460 | 43 | 2476696 | 0x000000000040065c | fmadd | 2476693/2476696 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 256 | 255 | 637096460 | 43 | 2476696 | 0x000000000040065c | fmadd | 2476693/2476696 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 257 | 256 | 637097230 | 43 | 2476696 | 0x000000000040065c | fmadd | —/2476696 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1302 | 257 | 9405606595 | 43 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 258 | — | 648185615 | 44 | 2520326 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff3c6a7ef9db22d→0x3ff3c6a7ef9db02d | — | — | origin |
| carrier_state | 259 | 258 | 648185615 | 44 | 2520326 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff3c6a7ef9db22d→0x3ff3c6a7ef9db02d | — | — | fsu_taint |
| operand_read | 260 | 259 | 648229120 | 44 | 2520470 | 0x0000000000400654 | fmadd | 2520326/2520470 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 261 | 260 | 648229120 | 44 | 2520470 | 0x0000000000400654 | fmadd | 2520326/2520470 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 262 | 261 | 648229120 | 44 | 2520470 | 0x0000000000400654 | fmadd | 2520326/2520470 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 263 | 262 | 648229890 | 44 | 2520470 | 0x0000000000400654 | fmadd | —/2520470 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1303 | 263 | 9405606595 | 44 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 264 | — | 667884525 | 45 | 2597619 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fdbb645a1cac083→0x3fdbb645a1cbc083 | — | — | origin |
| carrier_state | 265 | 264 | 667884525 | 45 | 2597619 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fdbb645a1cac083→0x3fdbb645a1cbc083 | — | — | fsu_taint |
| operand_read | 266 | 265 | 667908780 | 45 | 2597726 | 0x0000000000400654 | fmadd | 2597619/2597726 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 267 | 266 | 667908780 | 45 | 2597726 | 0x0000000000400654 | fmadd | 2597619/2597726 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 268 | 267 | 667908780 | 45 | 2597726 | 0x0000000000400654 | fmadd | 2597619/2597726 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 269 | 268 | 667909550 | 45 | 2597726 | 0x0000000000400654 | fmadd | —/2597726 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1304 | 269 | 9405606595 | 45 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 270 | — | 681094260 | 46 | 2649815 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4086580000000000→0x4086580000008000 | — | — | origin |
| carrier_state | 271 | 270 | 681094260 | 46 | 2649815 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4086580000000000→0x4086580000008000 | — | — | fsu_taint |
| operand_read | 272 | 271 | 681096185 | 46 | 2649818 | 0x0000000000400654 | fmadd | 2649815/2649818 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 273 | 272 | 681096185 | 46 | 2649818 | 0x0000000000400654 | fmadd | 2649815/2649818 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 274 | 273 | 681096185 | 46 | 2649818 | 0x0000000000400654 | fmadd | 2649815/2649818 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 275 | 274 | 681096955 | 46 | 2649818 | 0x0000000000400654 | fmadd | —/2649818 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1305 | 275 | 9405606595 | 46 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 276 | — | 695753905 | 47 | 2707524 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4062800000000000→0x4062800000010000 | — | — | origin |
| carrier_state | 277 | 276 | 695753905 | 47 | 2707524 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4062800000000000→0x4062800000010000 | — | — | fsu_taint |
| operand_read | 278 | 277 | 695758140 | 47 | 2707527 | 0x0000000000400658 | fmadd | 2707524/2707527 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 279 | 278 | 695758140 | 47 | 2707527 | 0x0000000000400658 | fmadd | 2707524/2707527 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 280 | 279 | 695758140 | 47 | 2707527 | 0x0000000000400658 | fmadd | 2707524/2707527 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 281 | 280 | 695758910 | 47 | 2707527 | 0x0000000000400658 | fmadd | —/2707527 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1306 | 281 | 9405606595 | 47 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 282 | — | 706899655 | 48 | 2751841 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4070800000000000→0x4070800000020000 | — | — | origin |
| carrier_state | 283 | 282 | 706899655 | 48 | 2751841 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4070800000000000→0x4070800000020000 | — | — | fsu_taint |
| operand_read | 284 | 283 | 706903505 | 48 | 2751844 | 0x000000000040065c | fmadd | 2751841/2751844 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 285 | 284 | 706903505 | 48 | 2751844 | 0x000000000040065c | fmadd | 2751841/2751844 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 286 | 285 | 706903505 | 48 | 2751844 | 0x000000000040065c | fmadd | 2751841/2751844 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 287 | 286 | 706904275 | 48 | 2751844 | 0x000000000040065c | fmadd | —/2751844 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1307 | 287 | 9405606595 | 48 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 288 | — | 729238510 | 49 | 2839968 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4081480000000000→0x4081480000000200 | — | — | origin |
| carrier_state | 289 | 288 | 729238510 | 49 | 2839968 | 0x000000000040064c | scvtf | —/— | 4 | — | 64@0 | 0x4081480000000000→0x4081480000000200 | — | — | fsu_taint |
| operand_read | 290 | 289 | 729242745 | 49 | 2839971 | 0x0000000000400658 | fmadd | 2839968/2839971 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 291 | 290 | 729242745 | 49 | 2839971 | 0x0000000000400658 | fmadd | 2839968/2839971 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 292 | 291 | 729242745 | 49 | 2839971 | 0x0000000000400658 | fmadd | 2839968/2839971 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 293 | 292 | 729243515 | 49 | 2839971 | 0x0000000000400658 | fmadd | —/2839971 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1308 | 293 | 9405606595 | 49 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 24 | — | 71512980 | 5 | 245232 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x407ff00000000000→0x407ff00000000400 | — | — | origin |
| carrier_state | 25 | 24 | 71512980 | 5 | 245232 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x407ff00000000000→0x407ff00000000400 | — | — | fsu_taint |
| operand_read | 26 | 25 | 71517215 | 5 | 245235 | 0x0000000000400658 | fmadd | 245232/245235 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 27 | 26 | 71517215 | 5 | 245235 | 0x0000000000400658 | fmadd | 245232/245235 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 28 | 27 | 71517215 | 5 | 245235 | 0x0000000000400658 | fmadd | 245232/245235 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 29 | 28 | 71517985 | 5 | 245235 | 0x0000000000400658 | fmadd | —/245235 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1264 | 29 | 9405606595 | 5 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 294 | — | 747668845 | 50 | 2912581 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4083180000000000→0x4083180000000200 | — | — | origin |
| carrier_state | 295 | 294 | 747668845 | 50 | 2912581 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4083180000000000→0x4083180000000200 | — | — | fsu_taint |
| operand_read | 296 | 295 | 747672695 | 50 | 2912584 | 0x000000000040065c | fmadd | 2912581/2912584 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 297 | 296 | 747672695 | 50 | 2912584 | 0x000000000040065c | fmadd | 2912581/2912584 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 298 | 297 | 747672695 | 50 | 2912584 | 0x000000000040065c | fmadd | 2912581/2912584 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 299 | 298 | 747673465 | 50 | 2912584 | 0x000000000040065c | fmadd | —/2912584 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1309 | 299 | 9405606595 | 50 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 300 | — | 757795500 | 51 | 2952431 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x405e400000000000→0x405e400000000800 | — | — | origin |
| carrier_state | 301 | 300 | 757795500 | 51 | 2952431 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x405e400000000000→0x405e400000000800 | — | — | fsu_taint |
| operand_read | 302 | 301 | 757797425 | 51 | 2952434 | 0x0000000000400654 | fmadd | 2952431/2952434 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 303 | 302 | 757797425 | 51 | 2952434 | 0x0000000000400654 | fmadd | 2952431/2952434 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 304 | 303 | 757797425 | 51 | 2952434 | 0x0000000000400654 | fmadd | 2952431/2952434 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 305 | 304 | 757798195 | 51 | 2952434 | 0x0000000000400654 | fmadd | —/2952434 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1310 | 305 | 9405606595 | 51 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 306 | — | 774130665 | 52 | 3017377 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4088600000000000→0x4088600000000010 | — | — | origin |
| carrier_state | 307 | 306 | 774130665 | 52 | 3017377 | 0x0000000000400650 | scvtf | —/— | 44 | — | 64@0 | 0x4088600000000000→0x4088600000000010 | — | — | fsu_taint |
| operand_read | 308 | 307 | 774134515 | 52 | 3017380 | 0x000000000040065c | fmadd | 3017377/3017380 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 309 | 308 | 774134515 | 52 | 3017380 | 0x000000000040065c | fmadd | 3017377/3017380 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 310 | 309 | 774134515 | 52 | 3017380 | 0x000000000040065c | fmadd | 3017377/3017380 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 311 | 310 | 774135285 | 52 | 3017380 | 0x000000000040065c | fmadd | —/3017380 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1311 | 311 | 9405606595 | 52 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 312 | — | 789700835 | 53 | 3078179 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x408b400000000000→0x408b400000000002 | — | — | origin |
| carrier_state | 313 | 312 | 789700835 | 53 | 3078179 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x408b400000000000→0x408b400000000002 | — | — | fsu_taint |
| operand_read | 314 | 313 | 789702760 | 53 | 3078182 | 0x0000000000400654 | fmadd | 3078179/3078182 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 315 | 314 | 789702760 | 53 | 3078182 | 0x0000000000400654 | fmadd | 3078179/3078182 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 316 | 315 | 789702760 | 53 | 3078182 | 0x0000000000400654 | fmadd | 3078179/3078182 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 317 | 316 | 789703530 | 53 | 3078182 | 0x0000000000400654 | fmadd | —/3078182 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1312 | 317 | 9405606595 | 53 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 318 | — | 803341385 | 54 | 3131788 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbf86872b020c49b4→0xbf86872b020c59b4 | — | — | origin |
| carrier_state | 319 | 318 | 803341385 | 54 | 3131788 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbf86872b020c49b4→0xbf86872b020c59b4 | — | — | fsu_taint |
| operand_read | 320 | 319 | 803356785 | 54 | 3131858 | 0x0000000000400654 | fmadd | 3131788/3131858 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 321 | 320 | 803356785 | 54 | 3131858 | 0x0000000000400654 | fmadd | 3131788/3131858 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 322 | 321 | 803356785 | 54 | 3131858 | 0x0000000000400654 | fmadd | 3131788/3131858 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 323 | 322 | 803357555 | 54 | 3131858 | 0x0000000000400654 | fmadd | —/3131858 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1313 | 323 | 9405606595 | 54 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 324 | — | 824370470 | 55 | 3215303 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4086380000000000→0x4086380000000004 | — | — | origin |
| carrier_state | 325 | 324 | 824370470 | 55 | 3215303 | 0x0000000000400648 | scvtf | —/— | 6 | — | 64@0 | 0x4086380000000000→0x4086380000000004 | — | — | fsu_taint |
| operand_read | 326 | 325 | 824372395 | 55 | 3215306 | 0x0000000000400654 | fmadd | 3215303/3215306 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 327 | 326 | 824372395 | 55 | 3215306 | 0x0000000000400654 | fmadd | 3215303/3215306 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 328 | 327 | 824372395 | 55 | 3215306 | 0x0000000000400654 | fmadd | 3215303/3215306 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 329 | 328 | 824373165 | 55 | 3215306 | 0x0000000000400654 | fmadd | —/3215306 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1314 | 329 | 9405606595 | 55 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 330 | — | 837977525 | 56 | 3268982 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3fedb22d0e560419→0x3fedb22d0e562419 | — | — | origin |
| carrier_state | 331 | 330 | 837977525 | 56 | 3268982 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3fedb22d0e560419→0x3fedb22d0e562419 | — | — | fsu_taint |
| operand_read | 332 | 331 | 838012945 | 56 | 3269126 | 0x0000000000400654 | fmadd | 3268982/3269126 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 333 | 332 | 838012945 | 56 | 3269126 | 0x0000000000400654 | fmadd | 3268982/3269126 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 334 | 333 | 838012945 | 56 | 3269126 | 0x0000000000400654 | fmadd | 3268982/3269126 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 335 | 334 | 838013715 | 56 | 3269126 | 0x0000000000400654 | fmadd | —/3269126 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1315 | 335 | 9405606595 | 56 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 336 | — | 859686520 | 57 | 3354520 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfbd70a3d70a3d70→0xbfbd70a3d70abd70 | — | — | origin |
| carrier_state | 337 | 336 | 859686520 | 57 | 3354520 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfbd70a3d70a3d70→0xbfbd70a3d70abd70 | — | — | fsu_taint |
| operand_read | 338 | 337 | 859701920 | 57 | 3354590 | 0x0000000000400654 | fmadd | 3354520/3354590 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 339 | 338 | 859701920 | 57 | 3354590 | 0x0000000000400654 | fmadd | 3354520/3354590 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 340 | 339 | 859701920 | 57 | 3354590 | 0x0000000000400654 | fmadd | 3354520/3354590 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 341 | 340 | 859702690 | 57 | 3354590 | 0x0000000000400654 | fmadd | —/3354590 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1316 | 341 | 9405606595 | 57 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 342 | — | 877573620 | 58 | 3424864 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fde45a1cac08313→0x3fde45a1cac08393 | — | — | origin |
| carrier_state | 343 | 342 | 877573620 | 58 | 3424864 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0x3fde45a1cac08313→0x3fde45a1cac08393 | — | — | fsu_taint |
| operand_read | 344 | 343 | 877589020 | 58 | 3424934 | 0x0000000000400654 | fmadd | 3424864/3424934 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 345 | 344 | 877589020 | 58 | 3424934 | 0x0000000000400654 | fmadd | 3424864/3424934 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 346 | 345 | 877589020 | 58 | 3424934 | 0x0000000000400654 | fmadd | 3424864/3424934 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 347 | 346 | 877589790 | 58 | 3424934 | 0x0000000000400654 | fmadd | —/3424934 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1317 | 347 | 9405606595 | 58 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 348 | — | 892451945 | 59 | 3483899 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4088300000000000→0x4088300000000400 | — | — | origin |
| carrier_state | 349 | 348 | 892451945 | 59 | 3483899 | 0x0000000000400648 | scvtf | —/— | 1 | — | 64@0 | 0x4088300000000000→0x4088300000000400 | — | — | fsu_taint |
| operand_read | 350 | 349 | 892453870 | 59 | 3483902 | 0x0000000000400654 | fmadd | 3483899/3483902 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 351 | 350 | 892453870 | 59 | 3483902 | 0x0000000000400654 | fmadd | 3483899/3483902 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 352 | 351 | 892453870 | 59 | 3483902 | 0x0000000000400654 | fmadd | 3483899/3483902 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 353 | 352 | 892454640 | 59 | 3483902 | 0x0000000000400654 | fmadd | —/3483902 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1318 | 353 | 9405606595 | 59 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 30 | — | 81443670 | 6 | 284366 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff1e353f7ced917→0x3ff1e353f7cec917 | — | — | origin |
| carrier_state | 31 | 30 | 81443670 | 6 | 284366 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff1e353f7ced917→0x3ff1e353f7cec917 | — | — | fsu_taint |
| operand_read | 32 | 31 | 81479090 | 6 | 284510 | 0x0000000000400654 | fmadd | 284366/284510 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 33 | 32 | 81479090 | 6 | 284510 | 0x0000000000400654 | fmadd | 284366/284510 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 34 | 33 | 81479090 | 6 | 284510 | 0x0000000000400654 | fmadd | 284366/284510 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 35 | 34 | 81479860 | 6 | 284510 | 0x0000000000400654 | fmadd | —/284510 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1265 | 35 | 9405606595 | 6 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 354 | — | 913245025 | 60 | 3566017 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4062800000000000→0x4062800000004000 | — | — | origin |
| carrier_state | 355 | 354 | 913245025 | 60 | 3566017 | 0x0000000000400650 | scvtf | —/— | 4 | — | 64@0 | 0x4062800000000000→0x4062800000004000 | — | — | fsu_taint |
| operand_read | 356 | 355 | 913248875 | 60 | 3566020 | 0x000000000040065c | fmadd | 3566017/3566020 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 357 | 356 | 913248875 | 60 | 3566020 | 0x000000000040065c | fmadd | 3566017/3566020 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 358 | 357 | 913248875 | 60 | 3566020 | 0x000000000040065c | fmadd | 3566017/3566020 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 359 | 358 | 913249645 | 60 | 3566020 | 0x000000000040065c | fmadd | —/3566020 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1319 | 359 | 9405606595 | 60 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 360 | — | 922916610 | 61 | 3604036 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfc26e978d4fdf3b→0xbfc26e978d4fdf2b | — | — | origin |
| carrier_state | 361 | 360 | 922916610 | 61 | 3604036 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfc26e978d4fdf3b→0xbfc26e978d4fdf2b | — | — | fsu_taint |
| operand_read | 362 | 361 | 922932010 | 61 | 3604106 | 0x0000000000400654 | fmadd | 3604036/3604106 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 363 | 362 | 922932010 | 61 | 3604106 | 0x0000000000400654 | fmadd | 3604036/3604106 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 364 | 363 | 922932010 | 61 | 3604106 | 0x0000000000400654 | fmadd | 3604036/3604106 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 365 | 364 | 922932780 | 61 | 3604106 | 0x0000000000400654 | fmadd | —/3604106 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1320 | 365 | 9405606595 | 61 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 366 | — | 935448360 | 62 | 3653426 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff076c8b4395810→0x3ff076c8b4395830 | — | — | origin |
| carrier_state | 367 | 366 | 935448360 | 62 | 3653426 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3ff076c8b4395810→0x3ff076c8b4395830 | — | — | fsu_taint |
| operand_read | 368 | 367 | 935483780 | 62 | 3653570 | 0x0000000000400654 | fmadd | 3653426/3653570 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 369 | 368 | 935483780 | 62 | 3653570 | 0x0000000000400654 | fmadd | 3653426/3653570 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 370 | 369 | 935483780 | 62 | 3653570 | 0x0000000000400654 | fmadd | 3653426/3653570 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 371 | 370 | 935484550 | 62 | 3653570 | 0x0000000000400654 | fmadd | —/3653570 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1321 | 371 | 9405606595 | 62 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 372 | — | 948391675 | 63 | 3704331 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff1645a1cac0831→0x3ff1645a1cac0830 | — | — | origin |
| carrier_state | 373 | 372 | 948391675 | 63 | 3704331 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff1645a1cac0831→0x3ff1645a1cac0830 | — | — | fsu_taint |
| operand_read | 374 | 373 | 948415930 | 63 | 3704438 | 0x0000000000400654 | fmadd | 3704331/3704438 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 375 | 374 | 948415930 | 63 | 3704438 | 0x0000000000400654 | fmadd | 3704331/3704438 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 376 | 375 | 948415930 | 63 | 3704438 | 0x0000000000400654 | fmadd | 3704331/3704438 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 377 | 376 | 948416700 | 63 | 3704438 | 0x0000000000400654 | fmadd | —/3704438 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1322 | 377 | 9405606595 | 63 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 378 | — | 956410840 | 64 | 3736407 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe010624dd2f1aa→0x3fe010624dd2f1ea | — | — | origin |
| carrier_state | 379 | 378 | 956410840 | 64 | 3736407 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe010624dd2f1aa→0x3fe010624dd2f1ea | — | — | fsu_taint |
| operand_read | 380 | 379 | 956435095 | 64 | 3736514 | 0x0000000000400654 | fmadd | 3736407/3736514 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 381 | 380 | 956435095 | 64 | 3736514 | 0x0000000000400654 | fmadd | 3736407/3736514 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 382 | 381 | 956435095 | 64 | 3736514 | 0x0000000000400654 | fmadd | 3736407/3736514 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 383 | 382 | 956435865 | 64 | 3736514 | 0x0000000000400654 | fmadd | —/3736514 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1323 | 383 | 9405606595 | 64 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 384 | — | 968598015 | 65 | 3784068 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x405c800000000000→0x405c800000000001 | — | — | origin |
| carrier_state | 385 | 384 | 968598015 | 65 | 3784068 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x405c800000000000→0x405c800000000001 | — | — | fsu_taint |
| operand_read | 386 | 385 | 968602250 | 65 | 3784071 | 0x0000000000400658 | fmadd | 3784068/3784071 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 387 | 386 | 968602250 | 65 | 3784071 | 0x0000000000400658 | fmadd | 3784068/3784071 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 388 | 387 | 968602250 | 65 | 3784071 | 0x0000000000400658 | fmadd | 3784068/3784071 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 389 | 388 | 968603020 | 65 | 3784071 | 0x0000000000400658 | fmadd | —/3784071 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1324 | 389 | 9405606595 | 65 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 390 | — | 990229625 | 66 | 3869099 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x407da00000000000→0x407da00000000080 | — | — | origin |
| carrier_state | 391 | 390 | 990229625 | 66 | 3869099 | 0x0000000000400648 | scvtf | —/— | 4 | — | 64@0 | 0x407da00000000000→0x407da00000000080 | — | — | fsu_taint |
| operand_read | 392 | 391 | 990231550 | 66 | 3869102 | 0x0000000000400654 | fmadd | 3869099/3869102 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 393 | 392 | 990231550 | 66 | 3869102 | 0x0000000000400654 | fmadd | 3869099/3869102 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 394 | 393 | 990231550 | 66 | 3869102 | 0x0000000000400654 | fmadd | 3869099/3869102 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 395 | 394 | 990232320 | 66 | 3869102 | 0x0000000000400654 | fmadd | —/3869102 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1325 | 395 | 9405606595 | 66 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 396 | — | 1006329555 | 67 | 3933076 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fcd916872b020c5→0x3fcd916872b060c5 | — | — | origin |
| carrier_state | 397 | 396 | 1006329555 | 67 | 3933076 | 0x000000000040065c | fmadd | —/— | 5 | — | 64@0 | 0x3fcd916872b020c5→0x3fcd916872b060c5 | — | — | fsu_taint |
| operand_read | 398 | 397 | 1006344955 | 67 | 3933146 | 0x0000000000400654 | fmadd | 3933076/3933146 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 399 | 398 | 1006344955 | 67 | 3933146 | 0x0000000000400654 | fmadd | 3933076/3933146 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 400 | 399 | 1006344955 | 67 | 3933146 | 0x0000000000400654 | fmadd | 3933076/3933146 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 401 | 400 | 1006345725 | 67 | 3933146 | 0x0000000000400654 | fmadd | —/3933146 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1326 | 401 | 9405606595 | 67 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 402 | — | 1024039555 | 68 | 4002483 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe970a3d70a3d71→0x3fe970a3d70a3c71 | — | — | origin |
| carrier_state | 403 | 402 | 1024039555 | 68 | 4002483 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3fe970a3d70a3d71→0x3fe970a3d70a3c71 | — | — | fsu_taint |
| operand_read | 404 | 403 | 1024063810 | 68 | 4002590 | 0x0000000000400654 | fmadd | 4002483/4002590 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 405 | 404 | 1024063810 | 68 | 4002590 | 0x0000000000400654 | fmadd | 4002483/4002590 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 406 | 405 | 1024063810 | 68 | 4002590 | 0x0000000000400654 | fmadd | 4002483/4002590 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 407 | 406 | 1024064580 | 68 | 4002590 | 0x0000000000400654 | fmadd | —/4002590 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1327 | 407 | 9405606595 | 68 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 408 | — | 1043454335 | 69 | 4079379 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fec3126e978d4fe→0x3fec3126e978d47e | — | — | origin |
| carrier_state | 409 | 408 | 1043454335 | 69 | 4079379 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fec3126e978d4fe→0x3fec3126e978d47e | — | — | fsu_taint |
| operand_read | 410 | 409 | 1043478590 | 69 | 4079486 | 0x0000000000400654 | fmadd | 4079379/4079486 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 411 | 410 | 1043478590 | 69 | 4079486 | 0x0000000000400654 | fmadd | 4079379/4079486 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 412 | 411 | 1043478590 | 69 | 4079486 | 0x0000000000400654 | fmadd | 4079379/4079486 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 413 | 412 | 1043479360 | 69 | 4079486 | 0x0000000000400654 | fmadd | —/4079486 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1328 | 413 | 9405606595 | 69 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 36 | — | 90773760 | 7 | 321302 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3fe374bc6a7ef9db→0x3fe374bc6a7ef99b | — | — | origin |
| carrier_state | 37 | 36 | 90773760 | 7 | 321302 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3fe374bc6a7ef9db→0x3fe374bc6a7ef99b | — | — | fsu_taint |
| operand_read | 38 | 37 | 90809180 | 7 | 321446 | 0x0000000000400654 | fmadd | 321302/321446 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 39 | 38 | 90809180 | 7 | 321446 | 0x0000000000400654 | fmadd | 321302/321446 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 40 | 39 | 90809180 | 7 | 321446 | 0x0000000000400654 | fmadd | 321302/321446 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 41 | 40 | 90809950 | 7 | 321446 | 0x0000000000400654 | fmadd | —/321446 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1266 | 41 | 9405606595 | 7 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 414 | — | 1061692555 | 70 | 4151451 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3ff16c8b43958106→0x3ff16c8b43958186 | — | — | origin |
| carrier_state | 415 | 414 | 1061692555 | 70 | 4151451 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3ff16c8b43958106→0x3ff16c8b43958186 | — | — | fsu_taint |
| operand_read | 416 | 415 | 1061716810 | 70 | 4151558 | 0x0000000000400654 | fmadd | 4151451/4151558 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 417 | 416 | 1061716810 | 70 | 4151558 | 0x0000000000400654 | fmadd | 4151451/4151558 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 418 | 417 | 1061716810 | 70 | 4151558 | 0x0000000000400654 | fmadd | 4151451/4151558 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 419 | 418 | 1061717580 | 70 | 4151558 | 0x0000000000400654 | fmadd | —/4151558 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1329 | 419 | 9405606595 | 70 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 420 | — | 1072187270 | 71 | 4193135 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4073900000000000→0x4073900000000001 | — | — | origin |
| carrier_state | 421 | 420 | 1072187270 | 71 | 4193135 | 0x0000000000400648 | scvtf | —/— | 44 | — | 64@0 | 0x4073900000000000→0x4073900000000001 | — | — | fsu_taint |
| operand_read | 422 | 421 | 1072189195 | 71 | 4193138 | 0x0000000000400654 | fmadd | 4193135/4193138 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 423 | 422 | 1072189195 | 71 | 4193138 | 0x0000000000400654 | fmadd | 4193135/4193138 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 424 | 423 | 1072189195 | 71 | 4193138 | 0x0000000000400654 | fmadd | 4193135/4193138 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 425 | 424 | 1072189965 | 71 | 4193138 | 0x0000000000400654 | fmadd | —/4193138 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1330 | 425 | 9405606595 | 71 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 426 | — | 1093053885 | 72 | 4275076 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fbb22d0e560418a→0x3fbb22d0e560418e | — | — | origin |
| carrier_state | 427 | 426 | 1093053885 | 72 | 4275076 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0x3fbb22d0e560418a→0x3fbb22d0e560418e | — | — | fsu_taint |
| operand_read | 428 | 427 | 1093069285 | 72 | 4275146 | 0x0000000000400654 | fmadd | 4275076/4275146 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 429 | 428 | 1093069285 | 72 | 4275146 | 0x0000000000400654 | fmadd | 4275076/4275146 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 430 | 429 | 1093069285 | 72 | 4275146 | 0x0000000000400654 | fmadd | 4275076/4275146 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 431 | 430 | 1093070055 | 72 | 4275146 | 0x0000000000400654 | fmadd | —/4275146 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1331 | 431 | 9405606595 | 72 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 432 | — | 1102437105 | 73 | 4312227 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe8395810624dd3→0x3fe8395810624df3 | — | — | origin |
| carrier_state | 433 | 432 | 1102437105 | 73 | 4312227 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe8395810624dd3→0x3fe8395810624df3 | — | — | fsu_taint |
| operand_read | 434 | 433 | 1102461360 | 73 | 4312334 | 0x0000000000400654 | fmadd | 4312227/4312334 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 435 | 434 | 1102461360 | 73 | 4312334 | 0x0000000000400654 | fmadd | 4312227/4312334 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 436 | 435 | 1102461360 | 73 | 4312334 | 0x0000000000400654 | fmadd | 4312227/4312334 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 437 | 436 | 1102462130 | 73 | 4312334 | 0x0000000000400654 | fmadd | —/4312334 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1332 | 437 | 9405606595 | 73 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 438 | — | 1124568060 | 74 | 4399956 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4088a80000000000→0x4088a80000000002 | — | — | origin |
| carrier_state | 439 | 438 | 1124568060 | 74 | 4399956 | 0x000000000040064c | scvtf | —/— | 1 | — | 64@0 | 0x4088a80000000000→0x4088a80000000002 | — | — | fsu_taint |
| operand_read | 440 | 439 | 1124572295 | 74 | 4399959 | 0x0000000000400658 | fmadd | 4399956/4399959 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 441 | 440 | 1124572295 | 74 | 4399959 | 0x0000000000400658 | fmadd | 4399956/4399959 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 442 | 441 | 1124572295 | 74 | 4399959 | 0x0000000000400658 | fmadd | 4399956/4399959 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 443 | 442 | 1124573065 | 74 | 4399959 | 0x0000000000400658 | fmadd | —/4399959 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1333 | 443 | 9405606595 | 74 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 444 | — | 1132713505 | 75 | 4432072 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfd3020c49ba5e35→0xbfd3020c49b85e35 | — | — | origin |
| carrier_state | 445 | 444 | 1132713505 | 75 | 4432072 | 0x000000000040065c | fmadd | —/— | 46 | — | 64@0 | 0xbfd3020c49ba5e35→0xbfd3020c49b85e35 | — | — | fsu_taint |
| operand_read | 446 | 445 | 1132728905 | 75 | 4432142 | 0x0000000000400654 | fmadd | 4432072/4432142 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 447 | 446 | 1132728905 | 75 | 4432142 | 0x0000000000400654 | fmadd | 4432072/4432142 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 448 | 447 | 1132728905 | 75 | 4432142 | 0x0000000000400654 | fmadd | 4432072/4432142 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 449 | 448 | 1132729675 | 75 | 4432142 | 0x0000000000400654 | fmadd | —/4432142 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1334 | 449 | 9405606595 | 75 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 450 | — | 1150479330 | 76 | 4502307 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fdb95810624dd2f→0x3fdb95810624dc2f | — | — | origin |
| carrier_state | 451 | 450 | 1150479330 | 76 | 4502307 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fdb95810624dd2f→0x3fdb95810624dc2f | — | — | fsu_taint |
| operand_read | 452 | 451 | 1150503585 | 76 | 4502414 | 0x0000000000400654 | fmadd | 4502307/4502414 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 453 | 452 | 1150503585 | 76 | 4502414 | 0x0000000000400654 | fmadd | 4502307/4502414 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 454 | 453 | 1150503585 | 76 | 4502414 | 0x0000000000400654 | fmadd | 4502307/4502414 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 455 | 454 | 1150504355 | 76 | 4502414 | 0x0000000000400654 | fmadd | —/4502414 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1335 | 455 | 9405606595 | 76 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 456 | — | 1169187635 | 77 | 4575675 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fea04189374bc6b→0x3fea04189376bc6b | — | — | origin |
| carrier_state | 457 | 456 | 1169187635 | 77 | 4575675 | 0x0000000000400658 | fmadd | —/— | 46 | — | 64@0 | 0x3fea04189374bc6b→0x3fea04189376bc6b | — | — | fsu_taint |
| operand_read | 458 | 457 | 1169211890 | 77 | 4575782 | 0x0000000000400654 | fmadd | 4575675/4575782 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 459 | 458 | 1169211890 | 77 | 4575782 | 0x0000000000400654 | fmadd | 4575675/4575782 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 460 | 459 | 1169211890 | 77 | 4575782 | 0x0000000000400654 | fmadd | 4575675/4575782 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 461 | 460 | 1169212660 | 77 | 4575782 | 0x0000000000400654 | fmadd | —/4575782 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1336 | 461 | 9405606595 | 77 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 462 | — | 1185687195 | 78 | 4640366 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff410624dd2f1aa→0x3ff410624dd2d1aa | — | — | origin |
| carrier_state | 463 | 462 | 1185687195 | 78 | 4640366 | 0x0000000000400654 | fmadd | —/— | 5 | — | 64@0 | 0x3ff410624dd2f1aa→0x3ff410624dd2d1aa | — | — | fsu_taint |
| operand_read | 464 | 463 | 1185722615 | 78 | 4640510 | 0x0000000000400654 | fmadd | 4640366/4640510 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 465 | 464 | 1185722615 | 78 | 4640510 | 0x0000000000400654 | fmadd | 4640366/4640510 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 466 | 465 | 1185722615 | 78 | 4640510 | 0x0000000000400654 | fmadd | 4640366/4640510 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 467 | 466 | 1185723385 | 78 | 4640510 | 0x0000000000400654 | fmadd | —/4640510 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1337 | 467 | 9405606595 | 78 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 468 | — | 1197045080 | 79 | 4685546 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff56c8b43958106→0x3ff56c8b43958104 | — | — | origin |
| carrier_state | 469 | 468 | 1197045080 | 79 | 4685546 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff56c8b43958106→0x3ff56c8b43958104 | — | — | fsu_taint |
| operand_read | 470 | 469 | 1197080500 | 79 | 4685690 | 0x0000000000400654 | fmadd | 4685546/4685690 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 471 | 470 | 1197080500 | 79 | 4685690 | 0x0000000000400654 | fmadd | 4685546/4685690 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 472 | 471 | 1197080500 | 79 | 4685690 | 0x0000000000400654 | fmadd | 4685546/4685690 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 473 | 472 | 1197081270 | 79 | 4685690 | 0x0000000000400654 | fmadd | —/4685690 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1338 | 473 | 9405606595 | 79 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 42 | — | 111934515 | 8 | 404532 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4077900000000000→0x4077900000000800 | — | — | origin |
| carrier_state | 43 | 42 | 111934515 | 8 | 404532 | 0x000000000040064c | scvtf | —/— | 6 | — | 64@0 | 0x4077900000000000→0x4077900000000800 | — | — | fsu_taint |
| operand_read | 44 | 43 | 111938750 | 8 | 404535 | 0x0000000000400658 | fmadd | 404532/404535 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 45 | 44 | 111938750 | 8 | 404535 | 0x0000000000400658 | fmadd | 404532/404535 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 46 | 45 | 111938750 | 8 | 404535 | 0x0000000000400658 | fmadd | 404532/404535 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 47 | 46 | 111939520 | 8 | 404535 | 0x0000000000400658 | fmadd | —/404535 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1267 | 47 | 9405606595 | 8 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 474 | — | 1210262515 | 80 | 4737532 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd6e978d4fdf3b6→0xbfd6e978d4fdf396 | — | — | origin |
| carrier_state | 475 | 474 | 1210262515 | 80 | 4737532 | 0x000000000040065c | fmadd | —/— | 1 | — | 64@0 | 0xbfd6e978d4fdf3b6→0xbfd6e978d4fdf396 | — | — | fsu_taint |
| operand_read | 476 | 475 | 1210277915 | 80 | 4737602 | 0x0000000000400654 | fmadd | 4737532/4737602 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 477 | 476 | 1210277915 | 80 | 4737602 | 0x0000000000400654 | fmadd | 4737532/4737602 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 478 | 477 | 1210277915 | 80 | 4737602 | 0x0000000000400654 | fmadd | 4737532/4737602 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 479 | 478 | 1210278685 | 80 | 4737602 | 0x0000000000400654 | fmadd | —/4737602 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1339 | 479 | 9405606595 | 80 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 480 | — | 1230807270 | 81 | 4818675 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff17ced916872b0→0x3ff17ced916870b0 | — | — | origin |
| carrier_state | 481 | 480 | 1230807270 | 81 | 4818675 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3ff17ced916872b0→0x3ff17ced916870b0 | — | — | fsu_taint |
| operand_read | 482 | 481 | 1230831525 | 81 | 4818782 | 0x0000000000400654 | fmadd | 4818675/4818782 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 483 | 482 | 1230831525 | 81 | 4818782 | 0x0000000000400654 | fmadd | 4818675/4818782 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 484 | 483 | 1230831525 | 81 | 4818782 | 0x0000000000400654 | fmadd | 4818675/4818782 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 485 | 484 | 1230832295 | 81 | 4818782 | 0x0000000000400654 | fmadd | —/4818782 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1340 | 485 | 9405606595 | 81 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 486 | — | 1249624915 | 82 | 4893051 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3ff072b020c49ba6→0x3ff072b020c499a6 | — | — | origin |
| carrier_state | 487 | 486 | 1249624915 | 82 | 4893051 | 0x0000000000400658 | fmadd | —/— | 45 | — | 64@0 | 0x3ff072b020c49ba6→0x3ff072b020c499a6 | — | — | fsu_taint |
| operand_read | 488 | 487 | 1249649170 | 82 | 4893158 | 0x0000000000400654 | fmadd | 4893051/4893158 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 489 | 488 | 1249649170 | 82 | 4893158 | 0x0000000000400654 | fmadd | 4893051/4893158 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 490 | 489 | 1249649170 | 82 | 4893158 | 0x0000000000400654 | fmadd | 4893051/4893158 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 491 | 490 | 1249649940 | 82 | 4893158 | 0x0000000000400654 | fmadd | —/4893158 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1341 | 491 | 9405606595 | 82 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 492 | — | 1267351470 | 83 | 4963141 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4083100000000000→0x4083100000000001 | — | — | origin |
| carrier_state | 493 | 492 | 1267351470 | 83 | 4963141 | 0x0000000000400650 | scvtf | —/— | 5 | — | 64@0 | 0x4083100000000000→0x4083100000000001 | — | — | fsu_taint |
| operand_read | 494 | 493 | 1267355320 | 83 | 4963144 | 0x000000000040065c | fmadd | 4963141/4963144 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 495 | 494 | 1267355320 | 83 | 4963144 | 0x000000000040065c | fmadd | 4963141/4963144 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 496 | 495 | 1267355320 | 83 | 4963144 | 0x000000000040065c | fmadd | 4963141/4963144 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 497 | 496 | 1267356090 | 83 | 4963144 | 0x000000000040065c | fmadd | —/4963144 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1342 | 497 | 9405606595 | 83 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 498 | — | 1278130315 | 84 | 5005658 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fec20c49ba5e354→0x3fec20c49ba7e354 | — | — | origin |
| carrier_state | 499 | 498 | 1278130315 | 84 | 5005658 | 0x0000000000400654 | fmadd | —/— | 45 | — | 64@0 | 0x3fec20c49ba5e354→0x3fec20c49ba7e354 | — | — | fsu_taint |
| operand_read | 500 | 499 | 1278165735 | 84 | 5005802 | 0x0000000000400654 | fmadd | 5005658/5005802 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 501 | 500 | 1278165735 | 84 | 5005802 | 0x0000000000400654 | fmadd | 5005658/5005802 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 502 | 501 | 1278165735 | 84 | 5005802 | 0x0000000000400654 | fmadd | 5005658/5005802 | 45 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 503 | 502 | 1278166505 | 84 | 5005802 | 0x0000000000400654 | fmadd | —/5005802 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1343 | 503 | 9405606595 | 84 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 504 | — | 1289830080 | 85 | 5051702 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff3333333333333→0x3ff3333333337333 | — | — | origin |
| carrier_state | 505 | 504 | 1289830080 | 85 | 5051702 | 0x0000000000400654 | fmadd | —/— | 1 | — | 64@0 | 0x3ff3333333333333→0x3ff3333333337333 | — | — | fsu_taint |
| operand_read | 506 | 505 | 1289865500 | 85 | 5051846 | 0x0000000000400654 | fmadd | 5051702/5051846 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 507 | 506 | 1289865500 | 85 | 5051846 | 0x0000000000400654 | fmadd | 5051702/5051846 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 508 | 507 | 1289865500 | 85 | 5051846 | 0x0000000000400654 | fmadd | 5051702/5051846 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 509 | 508 | 1289866270 | 85 | 5051846 | 0x0000000000400654 | fmadd | —/5051846 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1344 | 509 | 9405606595 | 85 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 510 | — | 1300266275 | 86 | 5092671 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe947ae147ae148→0x3fe947ae147ae158 | — | — | origin |
| carrier_state | 511 | 510 | 1300266275 | 86 | 5092671 | 0x0000000000400658 | fmadd | —/— | 44 | — | 64@0 | 0x3fe947ae147ae148→0x3fe947ae147ae158 | — | — | fsu_taint |
| operand_read | 512 | 511 | 1300290530 | 86 | 5092778 | 0x0000000000400654 | fmadd | 5092671/5092778 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 513 | 512 | 1300290530 | 86 | 5092778 | 0x0000000000400654 | fmadd | 5092671/5092778 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 514 | 513 | 1300290530 | 86 | 5092778 | 0x0000000000400654 | fmadd | 5092671/5092778 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 515 | 514 | 1300291300 | 86 | 5092778 | 0x0000000000400654 | fmadd | —/5092778 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1345 | 515 | 9405606595 | 86 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 516 | — | 1315226220 | 87 | 5152034 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff272b020c49ba6→0x3ff272b020c4bba6 | — | — | origin |
| carrier_state | 517 | 516 | 1315226220 | 87 | 5152034 | 0x0000000000400654 | fmadd | —/— | 6 | — | 64@0 | 0x3ff272b020c49ba6→0x3ff272b020c4bba6 | — | — | fsu_taint |
| operand_read | 518 | 517 | 1315261640 | 87 | 5152178 | 0x0000000000400654 | fmadd | 5152034/5152178 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 519 | 518 | 1315261640 | 87 | 5152178 | 0x0000000000400654 | fmadd | 5152034/5152178 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 520 | 519 | 1315261640 | 87 | 5152178 | 0x0000000000400654 | fmadd | 5152034/5152178 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 521 | 520 | 1315262410 | 87 | 5152178 | 0x0000000000400654 | fmadd | —/5152178 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1346 | 521 | 9405606595 | 87 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 522 | — | 1325005605 | 88 | 5190733 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4049000000000000→0x4049000000000800 | — | — | origin |
| carrier_state | 523 | 522 | 1325005605 | 88 | 5190733 | 0x0000000000400650 | scvtf | —/— | 46 | — | 64@0 | 0x4049000000000000→0x4049000000000800 | — | — | fsu_taint |
| operand_read | 524 | 523 | 1325009455 | 88 | 5190736 | 0x000000000040065c | fmadd | 5190733/5190736 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 525 | 524 | 1325009455 | 88 | 5190736 | 0x000000000040065c | fmadd | 5190733/5190736 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 526 | 525 | 1325009455 | 88 | 5190736 | 0x000000000040065c | fmadd | 5190733/5190736 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 527 | 526 | 1325010225 | 88 | 5190736 | 0x000000000040065c | fmadd | —/5190736 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1347 | 527 | 9405606595 | 88 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 528 | — | 1337112700 | 89 | 5238433 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x408c680000000000→0x408c680000000100 | — | — | origin |
| carrier_state | 529 | 528 | 1337112700 | 89 | 5238433 | 0x0000000000400650 | scvtf | —/— | 6 | — | 64@0 | 0x408c680000000000→0x408c680000000100 | — | — | fsu_taint |
| operand_read | 530 | 529 | 1337116550 | 89 | 5238436 | 0x000000000040065c | fmadd | 5238433/5238436 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 531 | 530 | 1337116550 | 89 | 5238436 | 0x000000000040065c | fmadd | 5238433/5238436 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 532 | 531 | 1337116550 | 89 | 5238436 | 0x000000000040065c | fmadd | 5238433/5238436 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 533 | 532 | 1337117320 | 89 | 5238436 | 0x000000000040065c | fmadd | —/5238436 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1348 | 533 | 9405606595 | 89 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 48 | — | 130165035 | 9 | 476356 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfb2b020c49ba5e3→0xbfb2b020c49ba563 | — | — | origin |
| carrier_state | 49 | 48 | 130165035 | 9 | 476356 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfb2b020c49ba5e3→0xbfb2b020c49ba563 | — | — | fsu_taint |
| operand_read | 50 | 49 | 130180435 | 9 | 476426 | 0x0000000000400654 | fmadd | 476356/476426 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 51 | 50 | 130180435 | 9 | 476426 | 0x0000000000400654 | fmadd | 476356/476426 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 52 | 51 | 130180435 | 9 | 476426 | 0x0000000000400654 | fmadd | 476356/476426 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 53 | 52 | 130181205 | 9 | 476426 | 0x0000000000400654 | fmadd | —/476426 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1268 | 53 | 9405606595 | 9 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 534 | — | 1356490520 | 90 | 5314824 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x407e800000000000→0x407e800000000080 | — | — | origin |
| carrier_state | 535 | 534 | 1356490520 | 90 | 5314824 | 0x000000000040064c | scvtf | —/— | 44 | — | 64@0 | 0x407e800000000000→0x407e800000000080 | — | — | fsu_taint |
| operand_read | 536 | 535 | 1356494755 | 90 | 5314827 | 0x0000000000400658 | fmadd | 5314824/5314827 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 537 | 536 | 1356494755 | 90 | 5314827 | 0x0000000000400658 | fmadd | 5314824/5314827 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 538 | 537 | 1356494755 | 90 | 5314827 | 0x0000000000400658 | fmadd | 5314824/5314827 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 539 | 538 | 1356495525 | 90 | 5314827 | 0x0000000000400658 | fmadd | —/5314827 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1349 | 539 | 9405606595 | 90 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 540 | — | 1370661215 | 91 | 5370592 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfc8b4395810624e→0xbfc8b4395810620e | — | — | origin |
| carrier_state | 541 | 540 | 1370661215 | 91 | 5370592 | 0x000000000040065c | fmadd | —/— | 6 | — | 64@0 | 0xbfc8b4395810624e→0xbfc8b4395810620e | — | — | fsu_taint |
| operand_read | 542 | 541 | 1370676615 | 91 | 5370662 | 0x0000000000400654 | fmadd | 5370592/5370662 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 543 | 542 | 1370676615 | 91 | 5370662 | 0x0000000000400654 | fmadd | 5370592/5370662 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 544 | 543 | 1370676615 | 91 | 5370662 | 0x0000000000400654 | fmadd | 5370592/5370662 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 545 | 544 | 1370677385 | 91 | 5370662 | 0x0000000000400654 | fmadd | —/5370662 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1350 | 545 | 9405606595 | 91 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 546 | — | 1379876190 | 92 | 5407059 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff2a7ef9db22d0e→0x3ff2a7ef9db22d1e | — | — | origin |
| carrier_state | 547 | 546 | 1379876190 | 92 | 5407059 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3ff2a7ef9db22d0e→0x3ff2a7ef9db22d1e | — | — | fsu_taint |
| operand_read | 548 | 547 | 1379900445 | 92 | 5407166 | 0x0000000000400654 | fmadd | 5407059/5407166 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 549 | 548 | 1379900445 | 92 | 5407166 | 0x0000000000400654 | fmadd | 5407059/5407166 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 550 | 549 | 1379900445 | 92 | 5407166 | 0x0000000000400654 | fmadd | 5407059/5407166 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 551 | 550 | 1379901215 | 92 | 5407166 | 0x0000000000400654 | fmadd | —/5407166 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1351 | 551 | 9405606595 | 92 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 552 | — | 1389079615 | 93 | 5443131 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fee147ae147ae15→0x3fee147ae147ae11 | — | — | origin |
| carrier_state | 553 | 552 | 1389079615 | 93 | 5443131 | 0x0000000000400658 | fmadd | —/— | 6 | — | 64@0 | 0x3fee147ae147ae15→0x3fee147ae147ae11 | — | — | fsu_taint |
| operand_read | 554 | 553 | 1389103870 | 93 | 5443238 | 0x0000000000400654 | fmadd | 5443131/5443238 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 555 | 554 | 1389103870 | 93 | 5443238 | 0x0000000000400654 | fmadd | 5443131/5443238 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 556 | 555 | 1389103870 | 93 | 5443238 | 0x0000000000400654 | fmadd | 5443131/5443238 | 6 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 557 | 556 | 1389104640 | 93 | 5443238 | 0x0000000000400654 | fmadd | —/5443238 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1352 | 557 | 9405606595 | 93 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 558 | — | 1397088000 | 94 | 5474702 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff3ae147ae147ae→0x3ff3ae147ae147be | — | — | origin |
| carrier_state | 559 | 558 | 1397088000 | 94 | 5474702 | 0x0000000000400654 | fmadd | —/— | 4 | — | 64@0 | 0x3ff3ae147ae147ae→0x3ff3ae147ae147be | — | — | fsu_taint |
| operand_read | 560 | 559 | 1397123420 | 94 | 5474846 | 0x0000000000400654 | fmadd | 5474702/5474846 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 561 | 560 | 1397123420 | 94 | 5474846 | 0x0000000000400654 | fmadd | 5474702/5474846 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 562 | 561 | 1397123420 | 94 | 5474846 | 0x0000000000400654 | fmadd | 5474702/5474846 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 563 | 562 | 1397124190 | 94 | 5474846 | 0x0000000000400654 | fmadd | —/5474846 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1353 | 563 | 9405606595 | 94 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 564 | — | 1412332460 | 95 | 5534894 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3fe989374bc6a7f0→0x3fe989374bc6a7b0 | — | — | origin |
| carrier_state | 565 | 564 | 1412332460 | 95 | 5534894 | 0x0000000000400654 | fmadd | —/— | 44 | — | 64@0 | 0x3fe989374bc6a7f0→0x3fe989374bc6a7b0 | — | — | fsu_taint |
| operand_read | 566 | 565 | 1412367880 | 95 | 5535038 | 0x0000000000400654 | fmadd | 5534894/5535038 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 567 | 566 | 1412367880 | 95 | 5535038 | 0x0000000000400654 | fmadd | 5534894/5535038 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 568 | 567 | 1412367880 | 95 | 5535038 | 0x0000000000400654 | fmadd | 5534894/5535038 | 44 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 569 | 568 | 1412368650 | 95 | 5535038 | 0x0000000000400654 | fmadd | —/5535038 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1354 | 569 | 9405606595 | 95 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 570 | — | 1434237420 | 96 | 5621188 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfb3f7ced916872a→0xbfb3f7ced91687aa | — | — | origin |
| carrier_state | 571 | 570 | 1434237420 | 96 | 5621188 | 0x000000000040065c | fmadd | —/— | 4 | — | 64@0 | 0xbfb3f7ced916872a→0xbfb3f7ced91687aa | — | — | fsu_taint |
| operand_read | 572 | 571 | 1434252820 | 96 | 5621258 | 0x0000000000400654 | fmadd | 5621188/5621258 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 573 | 572 | 1434252820 | 96 | 5621258 | 0x0000000000400654 | fmadd | 5621188/5621258 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 574 | 573 | 1434252820 | 96 | 5621258 | 0x0000000000400654 | fmadd | 5621188/5621258 | 4 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 575 | 574 | 1434253590 | 96 | 5621258 | 0x0000000000400654 | fmadd | —/5621258 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1355 | 575 | 9405606595 | 96 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 576 | — | 1445223395 | 97 | 5664855 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fead916872b020c→0x3fead916872b022c | — | — | origin |
| carrier_state | 577 | 576 | 1445223395 | 97 | 5664855 | 0x0000000000400658 | fmadd | —/— | 1 | — | 64@0 | 0x3fead916872b020c→0x3fead916872b022c | — | — | fsu_taint |
| operand_read | 578 | 577 | 1445247650 | 97 | 5664962 | 0x0000000000400654 | fmadd | 5664855/5664962 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 579 | 578 | 1445247650 | 97 | 5664962 | 0x0000000000400654 | fmadd | 5664855/5664962 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 580 | 579 | 1445247650 | 97 | 5664962 | 0x0000000000400654 | fmadd | 5664855/5664962 | 1 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 581 | 580 | 1445248420 | 97 | 5664962 | 0x0000000000400654 | fmadd | —/5664962 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1356 | 581 | 9405606595 | 97 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 582 | — | 1458764615 | 98 | 5717955 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fd072b020c49ba6→0x3fd072b020c49be6 | — | — | origin |
| carrier_state | 583 | 582 | 1458764615 | 98 | 5717955 | 0x0000000000400658 | fmadd | —/— | 5 | — | 64@0 | 0x3fd072b020c49ba6→0x3fd072b020c49be6 | — | — | fsu_taint |
| operand_read | 584 | 583 | 1458788870 | 98 | 5718062 | 0x0000000000400654 | fmadd | 5717955/5718062 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 585 | 584 | 1458788870 | 98 | 5718062 | 0x0000000000400654 | fmadd | 5717955/5718062 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 586 | 585 | 1458788870 | 98 | 5718062 | 0x0000000000400654 | fmadd | 5717955/5718062 | 5 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 587 | 586 | 1458789640 | 98 | 5718062 | 0x0000000000400654 | fmadd | —/5718062 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1357 | 587 | 9405606595 | 98 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |
| fault_applied | 588 | — | 1478997520 | 99 | 5798342 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff1db22d0e56042→0x3ff1db22d0e5604a | — | — | origin |
| carrier_state | 589 | 588 | 1478997520 | 99 | 5798342 | 0x0000000000400654 | fmadd | —/— | 46 | — | 64@0 | 0x3ff1db22d0e56042→0x3ff1db22d0e5604a | — | — | fsu_taint |
| operand_read | 590 | 589 | 1479032940 | 99 | 5798486 | 0x0000000000400654 | fmadd | 5798342/5798486 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| execute | 591 | 590 | 1479032940 | 99 | 5798486 | 0x0000000000400654 | fmadd | 5798342/5798486 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| prf_writeback | 592 | 591 | 1479032940 | 99 | 5798486 | 0x0000000000400654 | fmadd | 5798342/5798486 | 46 | 3 | —@— | —→— | — | — | fsu_taint |
| commit | 593 | 592 | 1479033710 | 99 | 5798486 | 0x0000000000400654 | fmadd | —/5798486 | — | — | —@— | —→— | L5 | errant_commit | fsu_taint |
| chain_end | 1358 | 593 | 9405606595 | 99 | — | — | — | —/— | — | — | —@— | —→— | — | run_end | none |

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

### fault 207

- **L0**：fault_applied#1236（本 seed 真实事件）。
- **L1**：carrier_state#1237（本 seed 真实事件）。
- **L2**：operand_read#1238（本 seed 真实事件）。
- **L3**：execute#1239（本 seed 真实事件）。
- **L4**：prf_writeback#1240（本 seed 真实事件）。
- **L5**：commit#1241（本 seed 真实事件）。

### fault 208

- **L0**：fault_applied#1242（本 seed 真实事件）。
- **L1**：carrier_state#1243（本 seed 真实事件）。
- **L2**：operand_read#1244（本 seed 真实事件）。
- **L3**：execute#1245（本 seed 真实事件）。
- **L4**：prf_writeback#1246（本 seed 真实事件）。
- **L5**：commit#1247（本 seed 真实事件）。

### fault 209

- **L0**：fault_applied#1248（本 seed 真实事件）。
- **L1**：carrier_state#1249（本 seed 真实事件）。
- **L2**：operand_read#1250（本 seed 真实事件）。
- **L3**：execute#1251（本 seed 真实事件）。
- **L4**：prf_writeback#1252（本 seed 真实事件）。
- **L5**：commit#1253（本 seed 真实事件）。

### fault 21

- **L0**：fault_applied#120（本 seed 真实事件）。
- **L1**：carrier_state#121（本 seed 真实事件）。
- **L2**：operand_read#122（本 seed 真实事件）。
- **L3**：execute#123（本 seed 真实事件）。
- **L4**：prf_writeback#124（本 seed 真实事件）。
- **L5**：commit#125（本 seed 真实事件）。

### fault 210

- **L0**：fault_applied#1254（本 seed 真实事件）。
- **L1**：carrier_state#1255（本 seed 真实事件）。
- **L2**：operand_read#1256（本 seed 真实事件）。
- **L3**：execute#1257（本 seed 真实事件）。
- **L4**：prf_writeback#1258（本 seed 真实事件）。
- **L5**：commit#1259（本 seed 真实事件）。

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

- run-level 程序 oracle：**SDC**（completed exit=0, ARRAYHASH 789afeae8e9653a6d8a9f3979a4d034b8465f3d6ac4845c69179a0f36f7c4b00 != golden e563e3e1bb7ee0e1b42c1ef7c7a11bc8d5029c6ea462cbd46b62a74a7b525aba — silent data corruption）
- run-level oracle 与 chain terminal 分开记录，互不替代。
- run-level 注入数（actual/expected）：210 / 210
- 全部 injected fault 出现在事件流：True
- 传播链 terminal：**full**
- admitted / certified：True / True
- violations（主 fault）：[]
- truncated / evidence_truncated：False / False
- 事件数：1470
- attempted / eligible / activated：210 / 2097155 / 210

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
| 207 | full | L5 | True | True | [] | 1241 | N/A / N/A |
| 208 | full | L5 | True | True | [] | 1247 | N/A / N/A |
| 209 | full | L5 | True | True | [] | 1253 | N/A / N/A |
| 21 | full | L5 | True | True | [] | 125 | N/A / N/A |
| 210 | full | L5 | True | True | [] | 1259 | N/A / N/A |
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
- `5` (commit) → `1260` (chain_end)；child.parent=5 ✓

- L5 真实见证：`5` kind=commit outcome=errant_commit oracle_diff=—

### fault 10

主链每一条边均验证为直接 parent：

- `54` (fault_applied) → `55` (carrier_state)；child.parent=54 ✓
- `55` (carrier_state) → `56` (operand_read)；child.parent=55 ✓
- `56` (operand_read) → `57` (execute)；child.parent=56 ✓
- `57` (execute) → `58` (prf_writeback)；child.parent=57 ✓
- `58` (prf_writeback) → `59` (commit)；child.parent=58 ✓
- `59` (commit) → `1269` (chain_end)；child.parent=59 ✓

- L5 真实见证：`59` kind=commit outcome=errant_commit oracle_diff=—

### fault 100

主链每一条边均验证为直接 parent：

- `594` (fault_applied) → `595` (carrier_state)；child.parent=594 ✓
- `595` (carrier_state) → `596` (operand_read)；child.parent=595 ✓
- `596` (operand_read) → `597` (execute)；child.parent=596 ✓
- `597` (execute) → `598` (prf_writeback)；child.parent=597 ✓
- `598` (prf_writeback) → `599` (commit)；child.parent=598 ✓
- `599` (commit) → `1359` (chain_end)；child.parent=599 ✓

- L5 真实见证：`599` kind=commit outcome=errant_commit oracle_diff=—

### fault 101

主链每一条边均验证为直接 parent：

- `600` (fault_applied) → `601` (carrier_state)；child.parent=600 ✓
- `601` (carrier_state) → `602` (operand_read)；child.parent=601 ✓
- `602` (operand_read) → `603` (execute)；child.parent=602 ✓
- `603` (execute) → `604` (prf_writeback)；child.parent=603 ✓
- `604` (prf_writeback) → `605` (commit)；child.parent=604 ✓
- `605` (commit) → `1360` (chain_end)；child.parent=605 ✓

- L5 真实见证：`605` kind=commit outcome=errant_commit oracle_diff=—

### fault 102

主链每一条边均验证为直接 parent：

- `606` (fault_applied) → `607` (carrier_state)；child.parent=606 ✓
- `607` (carrier_state) → `608` (operand_read)；child.parent=607 ✓
- `608` (operand_read) → `609` (execute)；child.parent=608 ✓
- `609` (execute) → `610` (prf_writeback)；child.parent=609 ✓
- `610` (prf_writeback) → `611` (commit)；child.parent=610 ✓
- `611` (commit) → `1361` (chain_end)；child.parent=611 ✓

- L5 真实见证：`611` kind=commit outcome=errant_commit oracle_diff=—

### fault 103

主链每一条边均验证为直接 parent：

- `612` (fault_applied) → `613` (carrier_state)；child.parent=612 ✓
- `613` (carrier_state) → `614` (operand_read)；child.parent=613 ✓
- `614` (operand_read) → `615` (execute)；child.parent=614 ✓
- `615` (execute) → `616` (prf_writeback)；child.parent=615 ✓
- `616` (prf_writeback) → `617` (commit)；child.parent=616 ✓
- `617` (commit) → `1362` (chain_end)；child.parent=617 ✓

- L5 真实见证：`617` kind=commit outcome=errant_commit oracle_diff=—

### fault 104

主链每一条边均验证为直接 parent：

- `618` (fault_applied) → `619` (carrier_state)；child.parent=618 ✓
- `619` (carrier_state) → `620` (operand_read)；child.parent=619 ✓
- `620` (operand_read) → `621` (execute)；child.parent=620 ✓
- `621` (execute) → `622` (prf_writeback)；child.parent=621 ✓
- `622` (prf_writeback) → `623` (commit)；child.parent=622 ✓
- `623` (commit) → `1363` (chain_end)；child.parent=623 ✓

- L5 真实见证：`623` kind=commit outcome=errant_commit oracle_diff=—

### fault 105

主链每一条边均验证为直接 parent：

- `624` (fault_applied) → `625` (carrier_state)；child.parent=624 ✓
- `625` (carrier_state) → `626` (operand_read)；child.parent=625 ✓
- `626` (operand_read) → `627` (execute)；child.parent=626 ✓
- `627` (execute) → `628` (prf_writeback)；child.parent=627 ✓
- `628` (prf_writeback) → `629` (commit)；child.parent=628 ✓
- `629` (commit) → `1364` (chain_end)；child.parent=629 ✓

- L5 真实见证：`629` kind=commit outcome=errant_commit oracle_diff=—

### fault 106

主链每一条边均验证为直接 parent：

- `630` (fault_applied) → `631` (carrier_state)；child.parent=630 ✓
- `631` (carrier_state) → `632` (operand_read)；child.parent=631 ✓
- `632` (operand_read) → `633` (execute)；child.parent=632 ✓
- `633` (execute) → `634` (prf_writeback)；child.parent=633 ✓
- `634` (prf_writeback) → `635` (commit)；child.parent=634 ✓
- `635` (commit) → `1365` (chain_end)；child.parent=635 ✓

- L5 真实见证：`635` kind=commit outcome=errant_commit oracle_diff=—

### fault 107

主链每一条边均验证为直接 parent：

- `636` (fault_applied) → `637` (carrier_state)；child.parent=636 ✓
- `637` (carrier_state) → `638` (operand_read)；child.parent=637 ✓
- `638` (operand_read) → `639` (execute)；child.parent=638 ✓
- `639` (execute) → `640` (prf_writeback)；child.parent=639 ✓
- `640` (prf_writeback) → `641` (commit)；child.parent=640 ✓
- `641` (commit) → `1366` (chain_end)；child.parent=641 ✓

- L5 真实见证：`641` kind=commit outcome=errant_commit oracle_diff=—

### fault 108

主链每一条边均验证为直接 parent：

- `642` (fault_applied) → `643` (carrier_state)；child.parent=642 ✓
- `643` (carrier_state) → `644` (operand_read)；child.parent=643 ✓
- `644` (operand_read) → `645` (execute)；child.parent=644 ✓
- `645` (execute) → `646` (prf_writeback)；child.parent=645 ✓
- `646` (prf_writeback) → `647` (commit)；child.parent=646 ✓
- `647` (commit) → `1367` (chain_end)；child.parent=647 ✓

- L5 真实见证：`647` kind=commit outcome=errant_commit oracle_diff=—

### fault 109

主链每一条边均验证为直接 parent：

- `648` (fault_applied) → `649` (carrier_state)；child.parent=648 ✓
- `649` (carrier_state) → `650` (operand_read)；child.parent=649 ✓
- `650` (operand_read) → `651` (execute)；child.parent=650 ✓
- `651` (execute) → `652` (prf_writeback)；child.parent=651 ✓
- `652` (prf_writeback) → `653` (commit)；child.parent=652 ✓
- `653` (commit) → `1368` (chain_end)；child.parent=653 ✓

- L5 真实见证：`653` kind=commit outcome=errant_commit oracle_diff=—

### fault 11

主链每一条边均验证为直接 parent：

- `60` (fault_applied) → `61` (carrier_state)；child.parent=60 ✓
- `61` (carrier_state) → `62` (operand_read)；child.parent=61 ✓
- `62` (operand_read) → `63` (execute)；child.parent=62 ✓
- `63` (execute) → `64` (prf_writeback)；child.parent=63 ✓
- `64` (prf_writeback) → `65` (commit)；child.parent=64 ✓
- `65` (commit) → `1270` (chain_end)；child.parent=65 ✓

- L5 真实见证：`65` kind=commit outcome=errant_commit oracle_diff=—

### fault 110

主链每一条边均验证为直接 parent：

- `654` (fault_applied) → `655` (carrier_state)；child.parent=654 ✓
- `655` (carrier_state) → `656` (operand_read)；child.parent=655 ✓
- `656` (operand_read) → `657` (execute)；child.parent=656 ✓
- `657` (execute) → `658` (prf_writeback)；child.parent=657 ✓
- `658` (prf_writeback) → `659` (commit)；child.parent=658 ✓
- `659` (commit) → `1369` (chain_end)；child.parent=659 ✓

- L5 真实见证：`659` kind=commit outcome=errant_commit oracle_diff=—

### fault 111

主链每一条边均验证为直接 parent：

- `660` (fault_applied) → `661` (carrier_state)；child.parent=660 ✓
- `661` (carrier_state) → `662` (operand_read)；child.parent=661 ✓
- `662` (operand_read) → `663` (execute)；child.parent=662 ✓
- `663` (execute) → `664` (prf_writeback)；child.parent=663 ✓
- `664` (prf_writeback) → `665` (commit)；child.parent=664 ✓
- `665` (commit) → `1370` (chain_end)；child.parent=665 ✓

- L5 真实见证：`665` kind=commit outcome=errant_commit oracle_diff=—

### fault 112

主链每一条边均验证为直接 parent：

- `666` (fault_applied) → `667` (carrier_state)；child.parent=666 ✓
- `667` (carrier_state) → `668` (operand_read)；child.parent=667 ✓
- `668` (operand_read) → `669` (execute)；child.parent=668 ✓
- `669` (execute) → `670` (prf_writeback)；child.parent=669 ✓
- `670` (prf_writeback) → `671` (commit)；child.parent=670 ✓
- `671` (commit) → `1371` (chain_end)；child.parent=671 ✓

- L5 真实见证：`671` kind=commit outcome=errant_commit oracle_diff=—

### fault 113

主链每一条边均验证为直接 parent：

- `672` (fault_applied) → `673` (carrier_state)；child.parent=672 ✓
- `673` (carrier_state) → `674` (operand_read)；child.parent=673 ✓
- `674` (operand_read) → `675` (execute)；child.parent=674 ✓
- `675` (execute) → `676` (prf_writeback)；child.parent=675 ✓
- `676` (prf_writeback) → `677` (commit)；child.parent=676 ✓
- `677` (commit) → `1372` (chain_end)；child.parent=677 ✓

- L5 真实见证：`677` kind=commit outcome=errant_commit oracle_diff=—

### fault 114

主链每一条边均验证为直接 parent：

- `678` (fault_applied) → `679` (carrier_state)；child.parent=678 ✓
- `679` (carrier_state) → `680` (operand_read)；child.parent=679 ✓
- `680` (operand_read) → `681` (execute)；child.parent=680 ✓
- `681` (execute) → `682` (prf_writeback)；child.parent=681 ✓
- `682` (prf_writeback) → `683` (commit)；child.parent=682 ✓
- `683` (commit) → `1373` (chain_end)；child.parent=683 ✓

- L5 真实见证：`683` kind=commit outcome=errant_commit oracle_diff=—

### fault 115

主链每一条边均验证为直接 parent：

- `684` (fault_applied) → `685` (carrier_state)；child.parent=684 ✓
- `685` (carrier_state) → `686` (operand_read)；child.parent=685 ✓
- `686` (operand_read) → `687` (execute)；child.parent=686 ✓
- `687` (execute) → `688` (prf_writeback)；child.parent=687 ✓
- `688` (prf_writeback) → `689` (commit)；child.parent=688 ✓
- `689` (commit) → `1374` (chain_end)；child.parent=689 ✓

- L5 真实见证：`689` kind=commit outcome=errant_commit oracle_diff=—

### fault 116

主链每一条边均验证为直接 parent：

- `690` (fault_applied) → `691` (carrier_state)；child.parent=690 ✓
- `691` (carrier_state) → `692` (operand_read)；child.parent=691 ✓
- `692` (operand_read) → `693` (execute)；child.parent=692 ✓
- `693` (execute) → `694` (prf_writeback)；child.parent=693 ✓
- `694` (prf_writeback) → `695` (commit)；child.parent=694 ✓
- `695` (commit) → `1375` (chain_end)；child.parent=695 ✓

- L5 真实见证：`695` kind=commit outcome=errant_commit oracle_diff=—

### fault 117

主链每一条边均验证为直接 parent：

- `696` (fault_applied) → `697` (carrier_state)；child.parent=696 ✓
- `697` (carrier_state) → `698` (operand_read)；child.parent=697 ✓
- `698` (operand_read) → `699` (execute)；child.parent=698 ✓
- `699` (execute) → `700` (prf_writeback)；child.parent=699 ✓
- `700` (prf_writeback) → `701` (commit)；child.parent=700 ✓
- `701` (commit) → `1376` (chain_end)；child.parent=701 ✓

- L5 真实见证：`701` kind=commit outcome=errant_commit oracle_diff=—

### fault 118

主链每一条边均验证为直接 parent：

- `702` (fault_applied) → `703` (carrier_state)；child.parent=702 ✓
- `703` (carrier_state) → `704` (operand_read)；child.parent=703 ✓
- `704` (operand_read) → `705` (execute)；child.parent=704 ✓
- `705` (execute) → `706` (prf_writeback)；child.parent=705 ✓
- `706` (prf_writeback) → `707` (commit)；child.parent=706 ✓
- `707` (commit) → `1377` (chain_end)；child.parent=707 ✓

- L5 真实见证：`707` kind=commit outcome=errant_commit oracle_diff=—

### fault 119

主链每一条边均验证为直接 parent：

- `708` (fault_applied) → `709` (carrier_state)；child.parent=708 ✓
- `709` (carrier_state) → `710` (operand_read)；child.parent=709 ✓
- `710` (operand_read) → `711` (execute)；child.parent=710 ✓
- `711` (execute) → `712` (prf_writeback)；child.parent=711 ✓
- `712` (prf_writeback) → `713` (commit)；child.parent=712 ✓
- `713` (commit) → `1378` (chain_end)；child.parent=713 ✓

- L5 真实见证：`713` kind=commit outcome=errant_commit oracle_diff=—

### fault 12

主链每一条边均验证为直接 parent：

- `66` (fault_applied) → `67` (carrier_state)；child.parent=66 ✓
- `67` (carrier_state) → `68` (operand_read)；child.parent=67 ✓
- `68` (operand_read) → `69` (execute)；child.parent=68 ✓
- `69` (execute) → `70` (prf_writeback)；child.parent=69 ✓
- `70` (prf_writeback) → `71` (commit)；child.parent=70 ✓
- `71` (commit) → `1271` (chain_end)；child.parent=71 ✓

- L5 真实见证：`71` kind=commit outcome=errant_commit oracle_diff=—

### fault 120

主链每一条边均验证为直接 parent：

- `714` (fault_applied) → `715` (carrier_state)；child.parent=714 ✓
- `715` (carrier_state) → `716` (operand_read)；child.parent=715 ✓
- `716` (operand_read) → `717` (execute)；child.parent=716 ✓
- `717` (execute) → `718` (prf_writeback)；child.parent=717 ✓
- `718` (prf_writeback) → `719` (commit)；child.parent=718 ✓
- `719` (commit) → `1379` (chain_end)；child.parent=719 ✓

- L5 真实见证：`719` kind=commit outcome=errant_commit oracle_diff=—

### fault 121

主链每一条边均验证为直接 parent：

- `720` (fault_applied) → `721` (carrier_state)；child.parent=720 ✓
- `721` (carrier_state) → `722` (operand_read)；child.parent=721 ✓
- `722` (operand_read) → `723` (execute)；child.parent=722 ✓
- `723` (execute) → `724` (prf_writeback)；child.parent=723 ✓
- `724` (prf_writeback) → `725` (commit)；child.parent=724 ✓
- `725` (commit) → `1380` (chain_end)；child.parent=725 ✓

- L5 真实见证：`725` kind=commit outcome=errant_commit oracle_diff=—

### fault 122

主链每一条边均验证为直接 parent：

- `726` (fault_applied) → `727` (carrier_state)；child.parent=726 ✓
- `727` (carrier_state) → `728` (operand_read)；child.parent=727 ✓
- `728` (operand_read) → `729` (execute)；child.parent=728 ✓
- `729` (execute) → `730` (prf_writeback)；child.parent=729 ✓
- `730` (prf_writeback) → `731` (commit)；child.parent=730 ✓
- `731` (commit) → `1381` (chain_end)；child.parent=731 ✓

- L5 真实见证：`731` kind=commit outcome=errant_commit oracle_diff=—

### fault 123

主链每一条边均验证为直接 parent：

- `732` (fault_applied) → `733` (carrier_state)；child.parent=732 ✓
- `733` (carrier_state) → `734` (operand_read)；child.parent=733 ✓
- `734` (operand_read) → `735` (execute)；child.parent=734 ✓
- `735` (execute) → `736` (prf_writeback)；child.parent=735 ✓
- `736` (prf_writeback) → `737` (commit)；child.parent=736 ✓
- `737` (commit) → `1382` (chain_end)；child.parent=737 ✓

- L5 真实见证：`737` kind=commit outcome=errant_commit oracle_diff=—

### fault 124

主链每一条边均验证为直接 parent：

- `738` (fault_applied) → `739` (carrier_state)；child.parent=738 ✓
- `739` (carrier_state) → `740` (operand_read)；child.parent=739 ✓
- `740` (operand_read) → `741` (execute)；child.parent=740 ✓
- `741` (execute) → `742` (prf_writeback)；child.parent=741 ✓
- `742` (prf_writeback) → `743` (commit)；child.parent=742 ✓
- `743` (commit) → `1383` (chain_end)；child.parent=743 ✓

- L5 真实见证：`743` kind=commit outcome=errant_commit oracle_diff=—

### fault 125

主链每一条边均验证为直接 parent：

- `744` (fault_applied) → `745` (carrier_state)；child.parent=744 ✓
- `745` (carrier_state) → `746` (operand_read)；child.parent=745 ✓
- `746` (operand_read) → `747` (execute)；child.parent=746 ✓
- `747` (execute) → `748` (prf_writeback)；child.parent=747 ✓
- `748` (prf_writeback) → `749` (commit)；child.parent=748 ✓
- `749` (commit) → `1384` (chain_end)；child.parent=749 ✓

- L5 真实见证：`749` kind=commit outcome=errant_commit oracle_diff=—

### fault 126

主链每一条边均验证为直接 parent：

- `750` (fault_applied) → `751` (carrier_state)；child.parent=750 ✓
- `751` (carrier_state) → `752` (operand_read)；child.parent=751 ✓
- `752` (operand_read) → `753` (execute)；child.parent=752 ✓
- `753` (execute) → `754` (prf_writeback)；child.parent=753 ✓
- `754` (prf_writeback) → `755` (commit)；child.parent=754 ✓
- `755` (commit) → `1385` (chain_end)；child.parent=755 ✓

- L5 真实见证：`755` kind=commit outcome=errant_commit oracle_diff=—

### fault 127

主链每一条边均验证为直接 parent：

- `756` (fault_applied) → `757` (carrier_state)；child.parent=756 ✓
- `757` (carrier_state) → `758` (operand_read)；child.parent=757 ✓
- `758` (operand_read) → `759` (execute)；child.parent=758 ✓
- `759` (execute) → `760` (prf_writeback)；child.parent=759 ✓
- `760` (prf_writeback) → `761` (commit)；child.parent=760 ✓
- `761` (commit) → `1386` (chain_end)；child.parent=761 ✓

- L5 真实见证：`761` kind=commit outcome=errant_commit oracle_diff=—

### fault 128

主链每一条边均验证为直接 parent：

- `762` (fault_applied) → `763` (carrier_state)；child.parent=762 ✓
- `763` (carrier_state) → `764` (operand_read)；child.parent=763 ✓
- `764` (operand_read) → `765` (execute)；child.parent=764 ✓
- `765` (execute) → `766` (prf_writeback)；child.parent=765 ✓
- `766` (prf_writeback) → `767` (commit)；child.parent=766 ✓
- `767` (commit) → `1387` (chain_end)；child.parent=767 ✓

- L5 真实见证：`767` kind=commit outcome=errant_commit oracle_diff=—

### fault 129

主链每一条边均验证为直接 parent：

- `768` (fault_applied) → `769` (carrier_state)；child.parent=768 ✓
- `769` (carrier_state) → `770` (operand_read)；child.parent=769 ✓
- `770` (operand_read) → `771` (execute)；child.parent=770 ✓
- `771` (execute) → `772` (prf_writeback)；child.parent=771 ✓
- `772` (prf_writeback) → `773` (commit)；child.parent=772 ✓
- `773` (commit) → `1388` (chain_end)；child.parent=773 ✓

- L5 真实见证：`773` kind=commit outcome=errant_commit oracle_diff=—

### fault 13

主链每一条边均验证为直接 parent：

- `72` (fault_applied) → `73` (carrier_state)；child.parent=72 ✓
- `73` (carrier_state) → `74` (operand_read)；child.parent=73 ✓
- `74` (operand_read) → `75` (execute)；child.parent=74 ✓
- `75` (execute) → `76` (prf_writeback)；child.parent=75 ✓
- `76` (prf_writeback) → `77` (commit)；child.parent=76 ✓
- `77` (commit) → `1272` (chain_end)；child.parent=77 ✓

- L5 真实见证：`77` kind=commit outcome=errant_commit oracle_diff=—

### fault 130

主链每一条边均验证为直接 parent：

- `774` (fault_applied) → `775` (carrier_state)；child.parent=774 ✓
- `775` (carrier_state) → `776` (operand_read)；child.parent=775 ✓
- `776` (operand_read) → `777` (execute)；child.parent=776 ✓
- `777` (execute) → `778` (prf_writeback)；child.parent=777 ✓
- `778` (prf_writeback) → `779` (commit)；child.parent=778 ✓
- `779` (commit) → `1389` (chain_end)；child.parent=779 ✓

- L5 真实见证：`779` kind=commit outcome=errant_commit oracle_diff=—

### fault 131

主链每一条边均验证为直接 parent：

- `780` (fault_applied) → `781` (carrier_state)；child.parent=780 ✓
- `781` (carrier_state) → `782` (operand_read)；child.parent=781 ✓
- `782` (operand_read) → `783` (execute)；child.parent=782 ✓
- `783` (execute) → `784` (prf_writeback)；child.parent=783 ✓
- `784` (prf_writeback) → `785` (commit)；child.parent=784 ✓
- `785` (commit) → `1390` (chain_end)；child.parent=785 ✓

- L5 真实见证：`785` kind=commit outcome=errant_commit oracle_diff=—

### fault 132

主链每一条边均验证为直接 parent：

- `786` (fault_applied) → `787` (carrier_state)；child.parent=786 ✓
- `787` (carrier_state) → `788` (operand_read)；child.parent=787 ✓
- `788` (operand_read) → `789` (execute)；child.parent=788 ✓
- `789` (execute) → `790` (prf_writeback)；child.parent=789 ✓
- `790` (prf_writeback) → `791` (commit)；child.parent=790 ✓
- `791` (commit) → `1391` (chain_end)；child.parent=791 ✓

- L5 真实见证：`791` kind=commit outcome=errant_commit oracle_diff=—

### fault 133

主链每一条边均验证为直接 parent：

- `792` (fault_applied) → `793` (carrier_state)；child.parent=792 ✓
- `793` (carrier_state) → `794` (operand_read)；child.parent=793 ✓
- `794` (operand_read) → `795` (execute)；child.parent=794 ✓
- `795` (execute) → `796` (prf_writeback)；child.parent=795 ✓
- `796` (prf_writeback) → `797` (commit)；child.parent=796 ✓
- `797` (commit) → `1392` (chain_end)；child.parent=797 ✓

- L5 真实见证：`797` kind=commit outcome=errant_commit oracle_diff=—

### fault 134

主链每一条边均验证为直接 parent：

- `798` (fault_applied) → `799` (carrier_state)；child.parent=798 ✓
- `799` (carrier_state) → `800` (operand_read)；child.parent=799 ✓
- `800` (operand_read) → `801` (execute)；child.parent=800 ✓
- `801` (execute) → `802` (prf_writeback)；child.parent=801 ✓
- `802` (prf_writeback) → `803` (commit)；child.parent=802 ✓
- `803` (commit) → `1393` (chain_end)；child.parent=803 ✓

- L5 真实见证：`803` kind=commit outcome=errant_commit oracle_diff=—

### fault 135

主链每一条边均验证为直接 parent：

- `804` (fault_applied) → `805` (carrier_state)；child.parent=804 ✓
- `805` (carrier_state) → `806` (operand_read)；child.parent=805 ✓
- `806` (operand_read) → `807` (execute)；child.parent=806 ✓
- `807` (execute) → `808` (prf_writeback)；child.parent=807 ✓
- `808` (prf_writeback) → `809` (commit)；child.parent=808 ✓
- `809` (commit) → `1394` (chain_end)；child.parent=809 ✓

- L5 真实见证：`809` kind=commit outcome=errant_commit oracle_diff=—

### fault 136

主链每一条边均验证为直接 parent：

- `810` (fault_applied) → `811` (carrier_state)；child.parent=810 ✓
- `811` (carrier_state) → `812` (operand_read)；child.parent=811 ✓
- `812` (operand_read) → `813` (execute)；child.parent=812 ✓
- `813` (execute) → `814` (prf_writeback)；child.parent=813 ✓
- `814` (prf_writeback) → `815` (commit)；child.parent=814 ✓
- `815` (commit) → `1395` (chain_end)；child.parent=815 ✓

- L5 真实见证：`815` kind=commit outcome=errant_commit oracle_diff=—

### fault 137

主链每一条边均验证为直接 parent：

- `816` (fault_applied) → `817` (carrier_state)；child.parent=816 ✓
- `817` (carrier_state) → `818` (operand_read)；child.parent=817 ✓
- `818` (operand_read) → `819` (execute)；child.parent=818 ✓
- `819` (execute) → `820` (prf_writeback)；child.parent=819 ✓
- `820` (prf_writeback) → `821` (commit)；child.parent=820 ✓
- `821` (commit) → `1396` (chain_end)；child.parent=821 ✓

- L5 真实见证：`821` kind=commit outcome=errant_commit oracle_diff=—

### fault 138

主链每一条边均验证为直接 parent：

- `822` (fault_applied) → `823` (carrier_state)；child.parent=822 ✓
- `823` (carrier_state) → `824` (operand_read)；child.parent=823 ✓
- `824` (operand_read) → `825` (execute)；child.parent=824 ✓
- `825` (execute) → `826` (prf_writeback)；child.parent=825 ✓
- `826` (prf_writeback) → `827` (commit)；child.parent=826 ✓
- `827` (commit) → `1397` (chain_end)；child.parent=827 ✓

- L5 真实见证：`827` kind=commit outcome=errant_commit oracle_diff=—

### fault 139

主链每一条边均验证为直接 parent：

- `828` (fault_applied) → `829` (carrier_state)；child.parent=828 ✓
- `829` (carrier_state) → `830` (operand_read)；child.parent=829 ✓
- `830` (operand_read) → `831` (execute)；child.parent=830 ✓
- `831` (execute) → `832` (prf_writeback)；child.parent=831 ✓
- `832` (prf_writeback) → `833` (commit)；child.parent=832 ✓
- `833` (commit) → `1398` (chain_end)；child.parent=833 ✓

- L5 真实见证：`833` kind=commit outcome=errant_commit oracle_diff=—

### fault 14

主链每一条边均验证为直接 parent：

- `78` (fault_applied) → `79` (carrier_state)；child.parent=78 ✓
- `79` (carrier_state) → `80` (operand_read)；child.parent=79 ✓
- `80` (operand_read) → `81` (execute)；child.parent=80 ✓
- `81` (execute) → `82` (prf_writeback)；child.parent=81 ✓
- `82` (prf_writeback) → `83` (commit)；child.parent=82 ✓
- `83` (commit) → `1273` (chain_end)；child.parent=83 ✓

- L5 真实见证：`83` kind=commit outcome=errant_commit oracle_diff=—

### fault 140

主链每一条边均验证为直接 parent：

- `834` (fault_applied) → `835` (carrier_state)；child.parent=834 ✓
- `835` (carrier_state) → `836` (operand_read)；child.parent=835 ✓
- `836` (operand_read) → `837` (execute)；child.parent=836 ✓
- `837` (execute) → `838` (prf_writeback)；child.parent=837 ✓
- `838` (prf_writeback) → `839` (commit)；child.parent=838 ✓
- `839` (commit) → `1399` (chain_end)；child.parent=839 ✓

- L5 真实见证：`839` kind=commit outcome=errant_commit oracle_diff=—

### fault 141

主链每一条边均验证为直接 parent：

- `840` (fault_applied) → `841` (carrier_state)；child.parent=840 ✓
- `841` (carrier_state) → `842` (operand_read)；child.parent=841 ✓
- `842` (operand_read) → `843` (execute)；child.parent=842 ✓
- `843` (execute) → `844` (prf_writeback)；child.parent=843 ✓
- `844` (prf_writeback) → `845` (commit)；child.parent=844 ✓
- `845` (commit) → `1400` (chain_end)；child.parent=845 ✓

- L5 真实见证：`845` kind=commit outcome=errant_commit oracle_diff=—

### fault 142

主链每一条边均验证为直接 parent：

- `846` (fault_applied) → `847` (carrier_state)；child.parent=846 ✓
- `847` (carrier_state) → `848` (operand_read)；child.parent=847 ✓
- `848` (operand_read) → `849` (execute)；child.parent=848 ✓
- `849` (execute) → `850` (prf_writeback)；child.parent=849 ✓
- `850` (prf_writeback) → `851` (commit)；child.parent=850 ✓
- `851` (commit) → `1401` (chain_end)；child.parent=851 ✓

- L5 真实见证：`851` kind=commit outcome=errant_commit oracle_diff=—

### fault 143

主链每一条边均验证为直接 parent：

- `852` (fault_applied) → `853` (carrier_state)；child.parent=852 ✓
- `853` (carrier_state) → `854` (operand_read)；child.parent=853 ✓
- `854` (operand_read) → `855` (execute)；child.parent=854 ✓
- `855` (execute) → `856` (prf_writeback)；child.parent=855 ✓
- `856` (prf_writeback) → `857` (commit)；child.parent=856 ✓
- `857` (commit) → `1402` (chain_end)；child.parent=857 ✓

- L5 真实见证：`857` kind=commit outcome=errant_commit oracle_diff=—

### fault 144

主链每一条边均验证为直接 parent：

- `858` (fault_applied) → `859` (carrier_state)；child.parent=858 ✓
- `859` (carrier_state) → `860` (operand_read)；child.parent=859 ✓
- `860` (operand_read) → `861` (execute)；child.parent=860 ✓
- `861` (execute) → `862` (prf_writeback)；child.parent=861 ✓
- `862` (prf_writeback) → `863` (commit)；child.parent=862 ✓
- `863` (commit) → `1403` (chain_end)；child.parent=863 ✓

- L5 真实见证：`863` kind=commit outcome=errant_commit oracle_diff=—

### fault 145

主链每一条边均验证为直接 parent：

- `864` (fault_applied) → `865` (carrier_state)；child.parent=864 ✓
- `865` (carrier_state) → `866` (operand_read)；child.parent=865 ✓
- `866` (operand_read) → `867` (execute)；child.parent=866 ✓
- `867` (execute) → `868` (prf_writeback)；child.parent=867 ✓
- `868` (prf_writeback) → `869` (commit)；child.parent=868 ✓
- `869` (commit) → `1404` (chain_end)；child.parent=869 ✓

- L5 真实见证：`869` kind=commit outcome=errant_commit oracle_diff=—

### fault 146

主链每一条边均验证为直接 parent：

- `870` (fault_applied) → `871` (carrier_state)；child.parent=870 ✓
- `871` (carrier_state) → `872` (operand_read)；child.parent=871 ✓
- `872` (operand_read) → `873` (execute)；child.parent=872 ✓
- `873` (execute) → `874` (prf_writeback)；child.parent=873 ✓
- `874` (prf_writeback) → `875` (commit)；child.parent=874 ✓
- `875` (commit) → `1405` (chain_end)；child.parent=875 ✓

- L5 真实见证：`875` kind=commit outcome=errant_commit oracle_diff=—

### fault 147

主链每一条边均验证为直接 parent：

- `876` (fault_applied) → `877` (carrier_state)；child.parent=876 ✓
- `877` (carrier_state) → `878` (operand_read)；child.parent=877 ✓
- `878` (operand_read) → `879` (execute)；child.parent=878 ✓
- `879` (execute) → `880` (prf_writeback)；child.parent=879 ✓
- `880` (prf_writeback) → `881` (commit)；child.parent=880 ✓
- `881` (commit) → `1406` (chain_end)；child.parent=881 ✓

- L5 真实见证：`881` kind=commit outcome=errant_commit oracle_diff=—

### fault 148

主链每一条边均验证为直接 parent：

- `882` (fault_applied) → `883` (carrier_state)；child.parent=882 ✓
- `883` (carrier_state) → `884` (operand_read)；child.parent=883 ✓
- `884` (operand_read) → `885` (execute)；child.parent=884 ✓
- `885` (execute) → `886` (prf_writeback)；child.parent=885 ✓
- `886` (prf_writeback) → `887` (commit)；child.parent=886 ✓
- `887` (commit) → `1407` (chain_end)；child.parent=887 ✓

- L5 真实见证：`887` kind=commit outcome=errant_commit oracle_diff=—

### fault 149

主链每一条边均验证为直接 parent：

- `888` (fault_applied) → `889` (carrier_state)；child.parent=888 ✓
- `889` (carrier_state) → `890` (operand_read)；child.parent=889 ✓
- `890` (operand_read) → `891` (execute)；child.parent=890 ✓
- `891` (execute) → `892` (prf_writeback)；child.parent=891 ✓
- `892` (prf_writeback) → `893` (commit)；child.parent=892 ✓
- `893` (commit) → `1408` (chain_end)；child.parent=893 ✓

- L5 真实见证：`893` kind=commit outcome=errant_commit oracle_diff=—

### fault 15

主链每一条边均验证为直接 parent：

- `84` (fault_applied) → `85` (carrier_state)；child.parent=84 ✓
- `85` (carrier_state) → `86` (operand_read)；child.parent=85 ✓
- `86` (operand_read) → `87` (execute)；child.parent=86 ✓
- `87` (execute) → `88` (prf_writeback)；child.parent=87 ✓
- `88` (prf_writeback) → `89` (commit)；child.parent=88 ✓
- `89` (commit) → `1274` (chain_end)；child.parent=89 ✓

- L5 真实见证：`89` kind=commit outcome=errant_commit oracle_diff=—

### fault 150

主链每一条边均验证为直接 parent：

- `894` (fault_applied) → `895` (carrier_state)；child.parent=894 ✓
- `895` (carrier_state) → `896` (operand_read)；child.parent=895 ✓
- `896` (operand_read) → `897` (execute)；child.parent=896 ✓
- `897` (execute) → `898` (prf_writeback)；child.parent=897 ✓
- `898` (prf_writeback) → `899` (commit)；child.parent=898 ✓
- `899` (commit) → `1409` (chain_end)；child.parent=899 ✓

- L5 真实见证：`899` kind=commit outcome=errant_commit oracle_diff=—

### fault 151

主链每一条边均验证为直接 parent：

- `900` (fault_applied) → `901` (carrier_state)；child.parent=900 ✓
- `901` (carrier_state) → `902` (operand_read)；child.parent=901 ✓
- `902` (operand_read) → `903` (execute)；child.parent=902 ✓
- `903` (execute) → `904` (prf_writeback)；child.parent=903 ✓
- `904` (prf_writeback) → `905` (commit)；child.parent=904 ✓
- `905` (commit) → `1410` (chain_end)；child.parent=905 ✓

- L5 真实见证：`905` kind=commit outcome=errant_commit oracle_diff=—

### fault 152

主链每一条边均验证为直接 parent：

- `906` (fault_applied) → `907` (carrier_state)；child.parent=906 ✓
- `907` (carrier_state) → `908` (operand_read)；child.parent=907 ✓
- `908` (operand_read) → `909` (execute)；child.parent=908 ✓
- `909` (execute) → `910` (prf_writeback)；child.parent=909 ✓
- `910` (prf_writeback) → `911` (commit)；child.parent=910 ✓
- `911` (commit) → `1411` (chain_end)；child.parent=911 ✓

- L5 真实见证：`911` kind=commit outcome=errant_commit oracle_diff=—

### fault 153

主链每一条边均验证为直接 parent：

- `912` (fault_applied) → `913` (carrier_state)；child.parent=912 ✓
- `913` (carrier_state) → `914` (operand_read)；child.parent=913 ✓
- `914` (operand_read) → `915` (execute)；child.parent=914 ✓
- `915` (execute) → `916` (prf_writeback)；child.parent=915 ✓
- `916` (prf_writeback) → `917` (commit)；child.parent=916 ✓
- `917` (commit) → `1412` (chain_end)；child.parent=917 ✓

- L5 真实见证：`917` kind=commit outcome=errant_commit oracle_diff=—

### fault 154

主链每一条边均验证为直接 parent：

- `918` (fault_applied) → `919` (carrier_state)；child.parent=918 ✓
- `919` (carrier_state) → `920` (operand_read)；child.parent=919 ✓
- `920` (operand_read) → `921` (execute)；child.parent=920 ✓
- `921` (execute) → `922` (prf_writeback)；child.parent=921 ✓
- `922` (prf_writeback) → `923` (commit)；child.parent=922 ✓
- `923` (commit) → `1413` (chain_end)；child.parent=923 ✓

- L5 真实见证：`923` kind=commit outcome=errant_commit oracle_diff=—

### fault 155

主链每一条边均验证为直接 parent：

- `924` (fault_applied) → `925` (carrier_state)；child.parent=924 ✓
- `925` (carrier_state) → `926` (operand_read)；child.parent=925 ✓
- `926` (operand_read) → `927` (execute)；child.parent=926 ✓
- `927` (execute) → `928` (prf_writeback)；child.parent=927 ✓
- `928` (prf_writeback) → `929` (commit)；child.parent=928 ✓
- `929` (commit) → `1414` (chain_end)；child.parent=929 ✓

- L5 真实见证：`929` kind=commit outcome=errant_commit oracle_diff=—

### fault 156

主链每一条边均验证为直接 parent：

- `930` (fault_applied) → `931` (carrier_state)；child.parent=930 ✓
- `931` (carrier_state) → `932` (operand_read)；child.parent=931 ✓
- `932` (operand_read) → `933` (execute)；child.parent=932 ✓
- `933` (execute) → `934` (prf_writeback)；child.parent=933 ✓
- `934` (prf_writeback) → `935` (commit)；child.parent=934 ✓
- `935` (commit) → `1415` (chain_end)；child.parent=935 ✓

- L5 真实见证：`935` kind=commit outcome=errant_commit oracle_diff=—

### fault 157

主链每一条边均验证为直接 parent：

- `936` (fault_applied) → `937` (carrier_state)；child.parent=936 ✓
- `937` (carrier_state) → `938` (operand_read)；child.parent=937 ✓
- `938` (operand_read) → `939` (execute)；child.parent=938 ✓
- `939` (execute) → `940` (prf_writeback)；child.parent=939 ✓
- `940` (prf_writeback) → `941` (commit)；child.parent=940 ✓
- `941` (commit) → `1416` (chain_end)；child.parent=941 ✓

- L5 真实见证：`941` kind=commit outcome=errant_commit oracle_diff=—

### fault 158

主链每一条边均验证为直接 parent：

- `942` (fault_applied) → `943` (carrier_state)；child.parent=942 ✓
- `943` (carrier_state) → `944` (operand_read)；child.parent=943 ✓
- `944` (operand_read) → `945` (execute)；child.parent=944 ✓
- `945` (execute) → `946` (prf_writeback)；child.parent=945 ✓
- `946` (prf_writeback) → `947` (commit)；child.parent=946 ✓
- `947` (commit) → `1417` (chain_end)；child.parent=947 ✓

- L5 真实见证：`947` kind=commit outcome=errant_commit oracle_diff=—

### fault 159

主链每一条边均验证为直接 parent：

- `948` (fault_applied) → `949` (carrier_state)；child.parent=948 ✓
- `949` (carrier_state) → `950` (operand_read)；child.parent=949 ✓
- `950` (operand_read) → `951` (execute)；child.parent=950 ✓
- `951` (execute) → `952` (prf_writeback)；child.parent=951 ✓
- `952` (prf_writeback) → `953` (commit)；child.parent=952 ✓
- `953` (commit) → `1418` (chain_end)；child.parent=953 ✓

- L5 真实见证：`953` kind=commit outcome=errant_commit oracle_diff=—

### fault 16

主链每一条边均验证为直接 parent：

- `90` (fault_applied) → `91` (carrier_state)；child.parent=90 ✓
- `91` (carrier_state) → `92` (operand_read)；child.parent=91 ✓
- `92` (operand_read) → `93` (execute)；child.parent=92 ✓
- `93` (execute) → `94` (prf_writeback)；child.parent=93 ✓
- `94` (prf_writeback) → `95` (commit)；child.parent=94 ✓
- `95` (commit) → `1275` (chain_end)；child.parent=95 ✓

- L5 真实见证：`95` kind=commit outcome=errant_commit oracle_diff=—

### fault 160

主链每一条边均验证为直接 parent：

- `954` (fault_applied) → `955` (carrier_state)；child.parent=954 ✓
- `955` (carrier_state) → `956` (operand_read)；child.parent=955 ✓
- `956` (operand_read) → `957` (execute)；child.parent=956 ✓
- `957` (execute) → `958` (prf_writeback)；child.parent=957 ✓
- `958` (prf_writeback) → `959` (commit)；child.parent=958 ✓
- `959` (commit) → `1419` (chain_end)；child.parent=959 ✓

- L5 真实见证：`959` kind=commit outcome=errant_commit oracle_diff=—

### fault 161

主链每一条边均验证为直接 parent：

- `960` (fault_applied) → `961` (carrier_state)；child.parent=960 ✓
- `961` (carrier_state) → `962` (operand_read)；child.parent=961 ✓
- `962` (operand_read) → `963` (execute)；child.parent=962 ✓
- `963` (execute) → `964` (prf_writeback)；child.parent=963 ✓
- `964` (prf_writeback) → `965` (commit)；child.parent=964 ✓
- `965` (commit) → `1420` (chain_end)；child.parent=965 ✓

- L5 真实见证：`965` kind=commit outcome=errant_commit oracle_diff=—

### fault 162

主链每一条边均验证为直接 parent：

- `966` (fault_applied) → `967` (carrier_state)；child.parent=966 ✓
- `967` (carrier_state) → `968` (operand_read)；child.parent=967 ✓
- `968` (operand_read) → `969` (execute)；child.parent=968 ✓
- `969` (execute) → `970` (prf_writeback)；child.parent=969 ✓
- `970` (prf_writeback) → `971` (commit)；child.parent=970 ✓
- `971` (commit) → `1421` (chain_end)；child.parent=971 ✓

- L5 真实见证：`971` kind=commit outcome=errant_commit oracle_diff=—

### fault 163

主链每一条边均验证为直接 parent：

- `972` (fault_applied) → `973` (carrier_state)；child.parent=972 ✓
- `973` (carrier_state) → `974` (operand_read)；child.parent=973 ✓
- `974` (operand_read) → `975` (execute)；child.parent=974 ✓
- `975` (execute) → `976` (prf_writeback)；child.parent=975 ✓
- `976` (prf_writeback) → `977` (commit)；child.parent=976 ✓
- `977` (commit) → `1422` (chain_end)；child.parent=977 ✓

- L5 真实见证：`977` kind=commit outcome=errant_commit oracle_diff=—

### fault 164

主链每一条边均验证为直接 parent：

- `978` (fault_applied) → `979` (carrier_state)；child.parent=978 ✓
- `979` (carrier_state) → `980` (operand_read)；child.parent=979 ✓
- `980` (operand_read) → `981` (execute)；child.parent=980 ✓
- `981` (execute) → `982` (prf_writeback)；child.parent=981 ✓
- `982` (prf_writeback) → `983` (commit)；child.parent=982 ✓
- `983` (commit) → `1423` (chain_end)；child.parent=983 ✓

- L5 真实见证：`983` kind=commit outcome=errant_commit oracle_diff=—

### fault 165

主链每一条边均验证为直接 parent：

- `984` (fault_applied) → `985` (carrier_state)；child.parent=984 ✓
- `985` (carrier_state) → `986` (operand_read)；child.parent=985 ✓
- `986` (operand_read) → `987` (execute)；child.parent=986 ✓
- `987` (execute) → `988` (prf_writeback)；child.parent=987 ✓
- `988` (prf_writeback) → `989` (commit)；child.parent=988 ✓
- `989` (commit) → `1424` (chain_end)；child.parent=989 ✓

- L5 真实见证：`989` kind=commit outcome=errant_commit oracle_diff=—

### fault 166

主链每一条边均验证为直接 parent：

- `990` (fault_applied) → `991` (carrier_state)；child.parent=990 ✓
- `991` (carrier_state) → `992` (operand_read)；child.parent=991 ✓
- `992` (operand_read) → `993` (execute)；child.parent=992 ✓
- `993` (execute) → `994` (prf_writeback)；child.parent=993 ✓
- `994` (prf_writeback) → `995` (commit)；child.parent=994 ✓
- `995` (commit) → `1425` (chain_end)；child.parent=995 ✓

- L5 真实见证：`995` kind=commit outcome=errant_commit oracle_diff=—

### fault 167

主链每一条边均验证为直接 parent：

- `996` (fault_applied) → `997` (carrier_state)；child.parent=996 ✓
- `997` (carrier_state) → `998` (operand_read)；child.parent=997 ✓
- `998` (operand_read) → `999` (execute)；child.parent=998 ✓
- `999` (execute) → `1000` (prf_writeback)；child.parent=999 ✓
- `1000` (prf_writeback) → `1001` (commit)；child.parent=1000 ✓
- `1001` (commit) → `1426` (chain_end)；child.parent=1001 ✓

- L5 真实见证：`1001` kind=commit outcome=errant_commit oracle_diff=—

### fault 168

主链每一条边均验证为直接 parent：

- `1002` (fault_applied) → `1003` (carrier_state)；child.parent=1002 ✓
- `1003` (carrier_state) → `1004` (operand_read)；child.parent=1003 ✓
- `1004` (operand_read) → `1005` (execute)；child.parent=1004 ✓
- `1005` (execute) → `1006` (prf_writeback)；child.parent=1005 ✓
- `1006` (prf_writeback) → `1007` (commit)；child.parent=1006 ✓
- `1007` (commit) → `1427` (chain_end)；child.parent=1007 ✓

- L5 真实见证：`1007` kind=commit outcome=errant_commit oracle_diff=—

### fault 169

主链每一条边均验证为直接 parent：

- `1008` (fault_applied) → `1009` (carrier_state)；child.parent=1008 ✓
- `1009` (carrier_state) → `1010` (operand_read)；child.parent=1009 ✓
- `1010` (operand_read) → `1011` (execute)；child.parent=1010 ✓
- `1011` (execute) → `1012` (prf_writeback)；child.parent=1011 ✓
- `1012` (prf_writeback) → `1013` (commit)；child.parent=1012 ✓
- `1013` (commit) → `1428` (chain_end)；child.parent=1013 ✓

- L5 真实见证：`1013` kind=commit outcome=errant_commit oracle_diff=—

### fault 17

主链每一条边均验证为直接 parent：

- `96` (fault_applied) → `97` (carrier_state)；child.parent=96 ✓
- `97` (carrier_state) → `98` (operand_read)；child.parent=97 ✓
- `98` (operand_read) → `99` (execute)；child.parent=98 ✓
- `99` (execute) → `100` (prf_writeback)；child.parent=99 ✓
- `100` (prf_writeback) → `101` (commit)；child.parent=100 ✓
- `101` (commit) → `1276` (chain_end)；child.parent=101 ✓

- L5 真实见证：`101` kind=commit outcome=errant_commit oracle_diff=—

### fault 170

主链每一条边均验证为直接 parent：

- `1014` (fault_applied) → `1015` (carrier_state)；child.parent=1014 ✓
- `1015` (carrier_state) → `1016` (operand_read)；child.parent=1015 ✓
- `1016` (operand_read) → `1017` (execute)；child.parent=1016 ✓
- `1017` (execute) → `1018` (prf_writeback)；child.parent=1017 ✓
- `1018` (prf_writeback) → `1019` (commit)；child.parent=1018 ✓
- `1019` (commit) → `1429` (chain_end)；child.parent=1019 ✓

- L5 真实见证：`1019` kind=commit outcome=errant_commit oracle_diff=—

### fault 171

主链每一条边均验证为直接 parent：

- `1020` (fault_applied) → `1021` (carrier_state)；child.parent=1020 ✓
- `1021` (carrier_state) → `1022` (operand_read)；child.parent=1021 ✓
- `1022` (operand_read) → `1023` (execute)；child.parent=1022 ✓
- `1023` (execute) → `1024` (prf_writeback)；child.parent=1023 ✓
- `1024` (prf_writeback) → `1025` (commit)；child.parent=1024 ✓
- `1025` (commit) → `1430` (chain_end)；child.parent=1025 ✓

- L5 真实见证：`1025` kind=commit outcome=errant_commit oracle_diff=—

### fault 172

主链每一条边均验证为直接 parent：

- `1026` (fault_applied) → `1027` (carrier_state)；child.parent=1026 ✓
- `1027` (carrier_state) → `1028` (operand_read)；child.parent=1027 ✓
- `1028` (operand_read) → `1029` (execute)；child.parent=1028 ✓
- `1029` (execute) → `1030` (prf_writeback)；child.parent=1029 ✓
- `1030` (prf_writeback) → `1031` (commit)；child.parent=1030 ✓
- `1031` (commit) → `1431` (chain_end)；child.parent=1031 ✓

- L5 真实见证：`1031` kind=commit outcome=errant_commit oracle_diff=—

### fault 173

主链每一条边均验证为直接 parent：

- `1032` (fault_applied) → `1033` (carrier_state)；child.parent=1032 ✓
- `1033` (carrier_state) → `1034` (operand_read)；child.parent=1033 ✓
- `1034` (operand_read) → `1035` (execute)；child.parent=1034 ✓
- `1035` (execute) → `1036` (prf_writeback)；child.parent=1035 ✓
- `1036` (prf_writeback) → `1037` (commit)；child.parent=1036 ✓
- `1037` (commit) → `1432` (chain_end)；child.parent=1037 ✓

- L5 真实见证：`1037` kind=commit outcome=errant_commit oracle_diff=—

### fault 174

主链每一条边均验证为直接 parent：

- `1038` (fault_applied) → `1039` (carrier_state)；child.parent=1038 ✓
- `1039` (carrier_state) → `1040` (operand_read)；child.parent=1039 ✓
- `1040` (operand_read) → `1041` (execute)；child.parent=1040 ✓
- `1041` (execute) → `1042` (prf_writeback)；child.parent=1041 ✓
- `1042` (prf_writeback) → `1043` (commit)；child.parent=1042 ✓
- `1043` (commit) → `1433` (chain_end)；child.parent=1043 ✓

- L5 真实见证：`1043` kind=commit outcome=errant_commit oracle_diff=—

### fault 175

主链每一条边均验证为直接 parent：

- `1044` (fault_applied) → `1045` (carrier_state)；child.parent=1044 ✓
- `1045` (carrier_state) → `1046` (operand_read)；child.parent=1045 ✓
- `1046` (operand_read) → `1047` (execute)；child.parent=1046 ✓
- `1047` (execute) → `1048` (prf_writeback)；child.parent=1047 ✓
- `1048` (prf_writeback) → `1049` (commit)；child.parent=1048 ✓
- `1049` (commit) → `1434` (chain_end)；child.parent=1049 ✓

- L5 真实见证：`1049` kind=commit outcome=errant_commit oracle_diff=—

### fault 176

主链每一条边均验证为直接 parent：

- `1050` (fault_applied) → `1051` (carrier_state)；child.parent=1050 ✓
- `1051` (carrier_state) → `1052` (operand_read)；child.parent=1051 ✓
- `1052` (operand_read) → `1053` (execute)；child.parent=1052 ✓
- `1053` (execute) → `1054` (prf_writeback)；child.parent=1053 ✓
- `1054` (prf_writeback) → `1055` (commit)；child.parent=1054 ✓
- `1055` (commit) → `1435` (chain_end)；child.parent=1055 ✓

- L5 真实见证：`1055` kind=commit outcome=errant_commit oracle_diff=—

### fault 177

主链每一条边均验证为直接 parent：

- `1056` (fault_applied) → `1057` (carrier_state)；child.parent=1056 ✓
- `1057` (carrier_state) → `1058` (operand_read)；child.parent=1057 ✓
- `1058` (operand_read) → `1059` (execute)；child.parent=1058 ✓
- `1059` (execute) → `1060` (prf_writeback)；child.parent=1059 ✓
- `1060` (prf_writeback) → `1061` (commit)；child.parent=1060 ✓
- `1061` (commit) → `1436` (chain_end)；child.parent=1061 ✓

- L5 真实见证：`1061` kind=commit outcome=errant_commit oracle_diff=—

### fault 178

主链每一条边均验证为直接 parent：

- `1062` (fault_applied) → `1063` (carrier_state)；child.parent=1062 ✓
- `1063` (carrier_state) → `1064` (operand_read)；child.parent=1063 ✓
- `1064` (operand_read) → `1065` (execute)；child.parent=1064 ✓
- `1065` (execute) → `1066` (prf_writeback)；child.parent=1065 ✓
- `1066` (prf_writeback) → `1067` (commit)；child.parent=1066 ✓
- `1067` (commit) → `1437` (chain_end)；child.parent=1067 ✓

- L5 真实见证：`1067` kind=commit outcome=errant_commit oracle_diff=—

### fault 179

主链每一条边均验证为直接 parent：

- `1068` (fault_applied) → `1069` (carrier_state)；child.parent=1068 ✓
- `1069` (carrier_state) → `1070` (operand_read)；child.parent=1069 ✓
- `1070` (operand_read) → `1071` (execute)；child.parent=1070 ✓
- `1071` (execute) → `1072` (prf_writeback)；child.parent=1071 ✓
- `1072` (prf_writeback) → `1073` (commit)；child.parent=1072 ✓
- `1073` (commit) → `1438` (chain_end)；child.parent=1073 ✓

- L5 真实见证：`1073` kind=commit outcome=errant_commit oracle_diff=—

### fault 18

主链每一条边均验证为直接 parent：

- `102` (fault_applied) → `103` (carrier_state)；child.parent=102 ✓
- `103` (carrier_state) → `104` (operand_read)；child.parent=103 ✓
- `104` (operand_read) → `105` (execute)；child.parent=104 ✓
- `105` (execute) → `106` (prf_writeback)；child.parent=105 ✓
- `106` (prf_writeback) → `107` (commit)；child.parent=106 ✓
- `107` (commit) → `1277` (chain_end)；child.parent=107 ✓

- L5 真实见证：`107` kind=commit outcome=errant_commit oracle_diff=—

### fault 180

主链每一条边均验证为直接 parent：

- `1074` (fault_applied) → `1075` (carrier_state)；child.parent=1074 ✓
- `1075` (carrier_state) → `1076` (operand_read)；child.parent=1075 ✓
- `1076` (operand_read) → `1077` (execute)；child.parent=1076 ✓
- `1077` (execute) → `1078` (prf_writeback)；child.parent=1077 ✓
- `1078` (prf_writeback) → `1079` (commit)；child.parent=1078 ✓
- `1079` (commit) → `1439` (chain_end)；child.parent=1079 ✓

- L5 真实见证：`1079` kind=commit outcome=errant_commit oracle_diff=—

### fault 181

主链每一条边均验证为直接 parent：

- `1080` (fault_applied) → `1081` (carrier_state)；child.parent=1080 ✓
- `1081` (carrier_state) → `1082` (operand_read)；child.parent=1081 ✓
- `1082` (operand_read) → `1083` (execute)；child.parent=1082 ✓
- `1083` (execute) → `1084` (prf_writeback)；child.parent=1083 ✓
- `1084` (prf_writeback) → `1085` (commit)；child.parent=1084 ✓
- `1085` (commit) → `1440` (chain_end)；child.parent=1085 ✓

- L5 真实见证：`1085` kind=commit outcome=errant_commit oracle_diff=—

### fault 182

主链每一条边均验证为直接 parent：

- `1086` (fault_applied) → `1087` (carrier_state)；child.parent=1086 ✓
- `1087` (carrier_state) → `1088` (operand_read)；child.parent=1087 ✓
- `1088` (operand_read) → `1089` (execute)；child.parent=1088 ✓
- `1089` (execute) → `1090` (prf_writeback)；child.parent=1089 ✓
- `1090` (prf_writeback) → `1091` (commit)；child.parent=1090 ✓
- `1091` (commit) → `1441` (chain_end)；child.parent=1091 ✓

- L5 真实见证：`1091` kind=commit outcome=errant_commit oracle_diff=—

### fault 183

主链每一条边均验证为直接 parent：

- `1092` (fault_applied) → `1093` (carrier_state)；child.parent=1092 ✓
- `1093` (carrier_state) → `1094` (operand_read)；child.parent=1093 ✓
- `1094` (operand_read) → `1095` (execute)；child.parent=1094 ✓
- `1095` (execute) → `1096` (prf_writeback)；child.parent=1095 ✓
- `1096` (prf_writeback) → `1097` (commit)；child.parent=1096 ✓
- `1097` (commit) → `1442` (chain_end)；child.parent=1097 ✓

- L5 真实见证：`1097` kind=commit outcome=errant_commit oracle_diff=—

### fault 184

主链每一条边均验证为直接 parent：

- `1098` (fault_applied) → `1099` (carrier_state)；child.parent=1098 ✓
- `1099` (carrier_state) → `1100` (operand_read)；child.parent=1099 ✓
- `1100` (operand_read) → `1101` (execute)；child.parent=1100 ✓
- `1101` (execute) → `1102` (prf_writeback)；child.parent=1101 ✓
- `1102` (prf_writeback) → `1103` (commit)；child.parent=1102 ✓
- `1103` (commit) → `1443` (chain_end)；child.parent=1103 ✓

- L5 真实见证：`1103` kind=commit outcome=errant_commit oracle_diff=—

### fault 185

主链每一条边均验证为直接 parent：

- `1104` (fault_applied) → `1105` (carrier_state)；child.parent=1104 ✓
- `1105` (carrier_state) → `1106` (operand_read)；child.parent=1105 ✓
- `1106` (operand_read) → `1107` (execute)；child.parent=1106 ✓
- `1107` (execute) → `1108` (prf_writeback)；child.parent=1107 ✓
- `1108` (prf_writeback) → `1109` (commit)；child.parent=1108 ✓
- `1109` (commit) → `1444` (chain_end)；child.parent=1109 ✓

- L5 真实见证：`1109` kind=commit outcome=errant_commit oracle_diff=—

### fault 186

主链每一条边均验证为直接 parent：

- `1110` (fault_applied) → `1111` (carrier_state)；child.parent=1110 ✓
- `1111` (carrier_state) → `1112` (operand_read)；child.parent=1111 ✓
- `1112` (operand_read) → `1113` (execute)；child.parent=1112 ✓
- `1113` (execute) → `1114` (prf_writeback)；child.parent=1113 ✓
- `1114` (prf_writeback) → `1115` (commit)；child.parent=1114 ✓
- `1115` (commit) → `1445` (chain_end)；child.parent=1115 ✓

- L5 真实见证：`1115` kind=commit outcome=errant_commit oracle_diff=—

### fault 187

主链每一条边均验证为直接 parent：

- `1116` (fault_applied) → `1117` (carrier_state)；child.parent=1116 ✓
- `1117` (carrier_state) → `1118` (operand_read)；child.parent=1117 ✓
- `1118` (operand_read) → `1119` (execute)；child.parent=1118 ✓
- `1119` (execute) → `1120` (prf_writeback)；child.parent=1119 ✓
- `1120` (prf_writeback) → `1121` (commit)；child.parent=1120 ✓
- `1121` (commit) → `1446` (chain_end)；child.parent=1121 ✓

- L5 真实见证：`1121` kind=commit outcome=errant_commit oracle_diff=—

### fault 188

主链每一条边均验证为直接 parent：

- `1122` (fault_applied) → `1123` (carrier_state)；child.parent=1122 ✓
- `1123` (carrier_state) → `1124` (operand_read)；child.parent=1123 ✓
- `1124` (operand_read) → `1125` (execute)；child.parent=1124 ✓
- `1125` (execute) → `1126` (prf_writeback)；child.parent=1125 ✓
- `1126` (prf_writeback) → `1127` (commit)；child.parent=1126 ✓
- `1127` (commit) → `1447` (chain_end)；child.parent=1127 ✓

- L5 真实见证：`1127` kind=commit outcome=errant_commit oracle_diff=—

### fault 189

主链每一条边均验证为直接 parent：

- `1128` (fault_applied) → `1129` (carrier_state)；child.parent=1128 ✓
- `1129` (carrier_state) → `1130` (operand_read)；child.parent=1129 ✓
- `1130` (operand_read) → `1131` (execute)；child.parent=1130 ✓
- `1131` (execute) → `1132` (prf_writeback)；child.parent=1131 ✓
- `1132` (prf_writeback) → `1133` (commit)；child.parent=1132 ✓
- `1133` (commit) → `1448` (chain_end)；child.parent=1133 ✓

- L5 真实见证：`1133` kind=commit outcome=errant_commit oracle_diff=—

### fault 19

主链每一条边均验证为直接 parent：

- `108` (fault_applied) → `109` (carrier_state)；child.parent=108 ✓
- `109` (carrier_state) → `110` (operand_read)；child.parent=109 ✓
- `110` (operand_read) → `111` (execute)；child.parent=110 ✓
- `111` (execute) → `112` (prf_writeback)；child.parent=111 ✓
- `112` (prf_writeback) → `113` (commit)；child.parent=112 ✓
- `113` (commit) → `1278` (chain_end)；child.parent=113 ✓

- L5 真实见证：`113` kind=commit outcome=errant_commit oracle_diff=—

### fault 190

主链每一条边均验证为直接 parent：

- `1134` (fault_applied) → `1135` (carrier_state)；child.parent=1134 ✓
- `1135` (carrier_state) → `1136` (operand_read)；child.parent=1135 ✓
- `1136` (operand_read) → `1137` (execute)；child.parent=1136 ✓
- `1137` (execute) → `1138` (prf_writeback)；child.parent=1137 ✓
- `1138` (prf_writeback) → `1139` (commit)；child.parent=1138 ✓
- `1139` (commit) → `1449` (chain_end)；child.parent=1139 ✓

- L5 真实见证：`1139` kind=commit outcome=errant_commit oracle_diff=—

### fault 191

主链每一条边均验证为直接 parent：

- `1140` (fault_applied) → `1141` (carrier_state)；child.parent=1140 ✓
- `1141` (carrier_state) → `1142` (operand_read)；child.parent=1141 ✓
- `1142` (operand_read) → `1143` (execute)；child.parent=1142 ✓
- `1143` (execute) → `1144` (prf_writeback)；child.parent=1143 ✓
- `1144` (prf_writeback) → `1145` (commit)；child.parent=1144 ✓
- `1145` (commit) → `1450` (chain_end)；child.parent=1145 ✓

- L5 真实见证：`1145` kind=commit outcome=errant_commit oracle_diff=—

### fault 192

主链每一条边均验证为直接 parent：

- `1146` (fault_applied) → `1147` (carrier_state)；child.parent=1146 ✓
- `1147` (carrier_state) → `1148` (operand_read)；child.parent=1147 ✓
- `1148` (operand_read) → `1149` (execute)；child.parent=1148 ✓
- `1149` (execute) → `1150` (prf_writeback)；child.parent=1149 ✓
- `1150` (prf_writeback) → `1151` (commit)；child.parent=1150 ✓
- `1151` (commit) → `1451` (chain_end)；child.parent=1151 ✓

- L5 真实见证：`1151` kind=commit outcome=errant_commit oracle_diff=—

### fault 193

主链每一条边均验证为直接 parent：

- `1152` (fault_applied) → `1153` (carrier_state)；child.parent=1152 ✓
- `1153` (carrier_state) → `1154` (operand_read)；child.parent=1153 ✓
- `1154` (operand_read) → `1155` (execute)；child.parent=1154 ✓
- `1155` (execute) → `1156` (prf_writeback)；child.parent=1155 ✓
- `1156` (prf_writeback) → `1157` (commit)；child.parent=1156 ✓
- `1157` (commit) → `1452` (chain_end)；child.parent=1157 ✓

- L5 真实见证：`1157` kind=commit outcome=errant_commit oracle_diff=—

### fault 194

主链每一条边均验证为直接 parent：

- `1158` (fault_applied) → `1159` (carrier_state)；child.parent=1158 ✓
- `1159` (carrier_state) → `1160` (operand_read)；child.parent=1159 ✓
- `1160` (operand_read) → `1161` (execute)；child.parent=1160 ✓
- `1161` (execute) → `1162` (prf_writeback)；child.parent=1161 ✓
- `1162` (prf_writeback) → `1163` (commit)；child.parent=1162 ✓
- `1163` (commit) → `1453` (chain_end)；child.parent=1163 ✓

- L5 真实见证：`1163` kind=commit outcome=errant_commit oracle_diff=—

### fault 195

主链每一条边均验证为直接 parent：

- `1164` (fault_applied) → `1165` (carrier_state)；child.parent=1164 ✓
- `1165` (carrier_state) → `1166` (operand_read)；child.parent=1165 ✓
- `1166` (operand_read) → `1167` (execute)；child.parent=1166 ✓
- `1167` (execute) → `1168` (prf_writeback)；child.parent=1167 ✓
- `1168` (prf_writeback) → `1169` (commit)；child.parent=1168 ✓
- `1169` (commit) → `1454` (chain_end)；child.parent=1169 ✓

- L5 真实见证：`1169` kind=commit outcome=errant_commit oracle_diff=—

### fault 196

主链每一条边均验证为直接 parent：

- `1170` (fault_applied) → `1171` (carrier_state)；child.parent=1170 ✓
- `1171` (carrier_state) → `1172` (operand_read)；child.parent=1171 ✓
- `1172` (operand_read) → `1173` (execute)；child.parent=1172 ✓
- `1173` (execute) → `1174` (prf_writeback)；child.parent=1173 ✓
- `1174` (prf_writeback) → `1175` (commit)；child.parent=1174 ✓
- `1175` (commit) → `1455` (chain_end)；child.parent=1175 ✓

- L5 真实见证：`1175` kind=commit outcome=errant_commit oracle_diff=—

### fault 197

主链每一条边均验证为直接 parent：

- `1176` (fault_applied) → `1177` (carrier_state)；child.parent=1176 ✓
- `1177` (carrier_state) → `1178` (operand_read)；child.parent=1177 ✓
- `1178` (operand_read) → `1179` (execute)；child.parent=1178 ✓
- `1179` (execute) → `1180` (prf_writeback)；child.parent=1179 ✓
- `1180` (prf_writeback) → `1181` (commit)；child.parent=1180 ✓
- `1181` (commit) → `1456` (chain_end)；child.parent=1181 ✓

- L5 真实见证：`1181` kind=commit outcome=errant_commit oracle_diff=—

### fault 198

主链每一条边均验证为直接 parent：

- `1182` (fault_applied) → `1183` (carrier_state)；child.parent=1182 ✓
- `1183` (carrier_state) → `1184` (operand_read)；child.parent=1183 ✓
- `1184` (operand_read) → `1185` (execute)；child.parent=1184 ✓
- `1185` (execute) → `1186` (prf_writeback)；child.parent=1185 ✓
- `1186` (prf_writeback) → `1187` (commit)；child.parent=1186 ✓
- `1187` (commit) → `1457` (chain_end)；child.parent=1187 ✓

- L5 真实见证：`1187` kind=commit outcome=errant_commit oracle_diff=—

### fault 199

主链每一条边均验证为直接 parent：

- `1188` (fault_applied) → `1189` (carrier_state)；child.parent=1188 ✓
- `1189` (carrier_state) → `1190` (operand_read)；child.parent=1189 ✓
- `1190` (operand_read) → `1191` (execute)；child.parent=1190 ✓
- `1191` (execute) → `1192` (prf_writeback)；child.parent=1191 ✓
- `1192` (prf_writeback) → `1193` (commit)；child.parent=1192 ✓
- `1193` (commit) → `1458` (chain_end)；child.parent=1193 ✓

- L5 真实见证：`1193` kind=commit outcome=errant_commit oracle_diff=—

### fault 2

主链每一条边均验证为直接 parent：

- `6` (fault_applied) → `7` (carrier_state)；child.parent=6 ✓
- `7` (carrier_state) → `8` (operand_read)；child.parent=7 ✓
- `8` (operand_read) → `9` (execute)；child.parent=8 ✓
- `9` (execute) → `10` (prf_writeback)；child.parent=9 ✓
- `10` (prf_writeback) → `11` (commit)；child.parent=10 ✓
- `11` (commit) → `1261` (chain_end)；child.parent=11 ✓

- L5 真实见证：`11` kind=commit outcome=errant_commit oracle_diff=—

### fault 20

主链每一条边均验证为直接 parent：

- `114` (fault_applied) → `115` (carrier_state)；child.parent=114 ✓
- `115` (carrier_state) → `116` (operand_read)；child.parent=115 ✓
- `116` (operand_read) → `117` (execute)；child.parent=116 ✓
- `117` (execute) → `118` (prf_writeback)；child.parent=117 ✓
- `118` (prf_writeback) → `119` (commit)；child.parent=118 ✓
- `119` (commit) → `1279` (chain_end)；child.parent=119 ✓

- L5 真实见证：`119` kind=commit outcome=errant_commit oracle_diff=—

### fault 200

主链每一条边均验证为直接 parent：

- `1194` (fault_applied) → `1195` (carrier_state)；child.parent=1194 ✓
- `1195` (carrier_state) → `1196` (operand_read)；child.parent=1195 ✓
- `1196` (operand_read) → `1197` (execute)；child.parent=1196 ✓
- `1197` (execute) → `1198` (prf_writeback)；child.parent=1197 ✓
- `1198` (prf_writeback) → `1199` (commit)；child.parent=1198 ✓
- `1199` (commit) → `1459` (chain_end)；child.parent=1199 ✓

- L5 真实见证：`1199` kind=commit outcome=errant_commit oracle_diff=—

### fault 201

主链每一条边均验证为直接 parent：

- `1200` (fault_applied) → `1201` (carrier_state)；child.parent=1200 ✓
- `1201` (carrier_state) → `1202` (operand_read)；child.parent=1201 ✓
- `1202` (operand_read) → `1203` (execute)；child.parent=1202 ✓
- `1203` (execute) → `1204` (prf_writeback)；child.parent=1203 ✓
- `1204` (prf_writeback) → `1205` (commit)；child.parent=1204 ✓
- `1205` (commit) → `1460` (chain_end)；child.parent=1205 ✓

- L5 真实见证：`1205` kind=commit outcome=errant_commit oracle_diff=—

### fault 202

主链每一条边均验证为直接 parent：

- `1206` (fault_applied) → `1207` (carrier_state)；child.parent=1206 ✓
- `1207` (carrier_state) → `1208` (operand_read)；child.parent=1207 ✓
- `1208` (operand_read) → `1209` (execute)；child.parent=1208 ✓
- `1209` (execute) → `1210` (prf_writeback)；child.parent=1209 ✓
- `1210` (prf_writeback) → `1211` (commit)；child.parent=1210 ✓
- `1211` (commit) → `1461` (chain_end)；child.parent=1211 ✓

- L5 真实见证：`1211` kind=commit outcome=errant_commit oracle_diff=—

### fault 203

主链每一条边均验证为直接 parent：

- `1212` (fault_applied) → `1213` (carrier_state)；child.parent=1212 ✓
- `1213` (carrier_state) → `1214` (operand_read)；child.parent=1213 ✓
- `1214` (operand_read) → `1215` (execute)；child.parent=1214 ✓
- `1215` (execute) → `1216` (prf_writeback)；child.parent=1215 ✓
- `1216` (prf_writeback) → `1217` (commit)；child.parent=1216 ✓
- `1217` (commit) → `1462` (chain_end)；child.parent=1217 ✓

- L5 真实见证：`1217` kind=commit outcome=errant_commit oracle_diff=—

### fault 204

主链每一条边均验证为直接 parent：

- `1218` (fault_applied) → `1219` (carrier_state)；child.parent=1218 ✓
- `1219` (carrier_state) → `1220` (operand_read)；child.parent=1219 ✓
- `1220` (operand_read) → `1221` (execute)；child.parent=1220 ✓
- `1221` (execute) → `1222` (prf_writeback)；child.parent=1221 ✓
- `1222` (prf_writeback) → `1223` (commit)；child.parent=1222 ✓
- `1223` (commit) → `1463` (chain_end)；child.parent=1223 ✓

- L5 真实见证：`1223` kind=commit outcome=errant_commit oracle_diff=—

### fault 205

主链每一条边均验证为直接 parent：

- `1224` (fault_applied) → `1225` (carrier_state)；child.parent=1224 ✓
- `1225` (carrier_state) → `1226` (operand_read)；child.parent=1225 ✓
- `1226` (operand_read) → `1227` (execute)；child.parent=1226 ✓
- `1227` (execute) → `1228` (prf_writeback)；child.parent=1227 ✓
- `1228` (prf_writeback) → `1229` (commit)；child.parent=1228 ✓
- `1229` (commit) → `1464` (chain_end)；child.parent=1229 ✓

- L5 真实见证：`1229` kind=commit outcome=errant_commit oracle_diff=—

### fault 206

主链每一条边均验证为直接 parent：

- `1230` (fault_applied) → `1231` (carrier_state)；child.parent=1230 ✓
- `1231` (carrier_state) → `1232` (operand_read)；child.parent=1231 ✓
- `1232` (operand_read) → `1233` (execute)；child.parent=1232 ✓
- `1233` (execute) → `1234` (prf_writeback)；child.parent=1233 ✓
- `1234` (prf_writeback) → `1235` (commit)；child.parent=1234 ✓
- `1235` (commit) → `1465` (chain_end)；child.parent=1235 ✓

- L5 真实见证：`1235` kind=commit outcome=errant_commit oracle_diff=—

### fault 207

主链每一条边均验证为直接 parent：

- `1236` (fault_applied) → `1237` (carrier_state)；child.parent=1236 ✓
- `1237` (carrier_state) → `1238` (operand_read)；child.parent=1237 ✓
- `1238` (operand_read) → `1239` (execute)；child.parent=1238 ✓
- `1239` (execute) → `1240` (prf_writeback)；child.parent=1239 ✓
- `1240` (prf_writeback) → `1241` (commit)；child.parent=1240 ✓
- `1241` (commit) → `1466` (chain_end)；child.parent=1241 ✓

- L5 真实见证：`1241` kind=commit outcome=errant_commit oracle_diff=—

### fault 208

主链每一条边均验证为直接 parent：

- `1242` (fault_applied) → `1243` (carrier_state)；child.parent=1242 ✓
- `1243` (carrier_state) → `1244` (operand_read)；child.parent=1243 ✓
- `1244` (operand_read) → `1245` (execute)；child.parent=1244 ✓
- `1245` (execute) → `1246` (prf_writeback)；child.parent=1245 ✓
- `1246` (prf_writeback) → `1247` (commit)；child.parent=1246 ✓
- `1247` (commit) → `1467` (chain_end)；child.parent=1247 ✓

- L5 真实见证：`1247` kind=commit outcome=errant_commit oracle_diff=—

### fault 209

主链每一条边均验证为直接 parent：

- `1248` (fault_applied) → `1249` (carrier_state)；child.parent=1248 ✓
- `1249` (carrier_state) → `1250` (operand_read)；child.parent=1249 ✓
- `1250` (operand_read) → `1251` (execute)；child.parent=1250 ✓
- `1251` (execute) → `1252` (prf_writeback)；child.parent=1251 ✓
- `1252` (prf_writeback) → `1253` (commit)；child.parent=1252 ✓
- `1253` (commit) → `1468` (chain_end)；child.parent=1253 ✓

- L5 真实见证：`1253` kind=commit outcome=errant_commit oracle_diff=—

### fault 21

主链每一条边均验证为直接 parent：

- `120` (fault_applied) → `121` (carrier_state)；child.parent=120 ✓
- `121` (carrier_state) → `122` (operand_read)；child.parent=121 ✓
- `122` (operand_read) → `123` (execute)；child.parent=122 ✓
- `123` (execute) → `124` (prf_writeback)；child.parent=123 ✓
- `124` (prf_writeback) → `125` (commit)；child.parent=124 ✓
- `125` (commit) → `1280` (chain_end)；child.parent=125 ✓

- L5 真实见证：`125` kind=commit outcome=errant_commit oracle_diff=—

### fault 210

主链每一条边均验证为直接 parent：

- `1254` (fault_applied) → `1255` (carrier_state)；child.parent=1254 ✓
- `1255` (carrier_state) → `1256` (operand_read)；child.parent=1255 ✓
- `1256` (operand_read) → `1257` (execute)；child.parent=1256 ✓
- `1257` (execute) → `1258` (prf_writeback)；child.parent=1257 ✓
- `1258` (prf_writeback) → `1259` (commit)；child.parent=1258 ✓
- `1259` (commit) → `1469` (chain_end)；child.parent=1259 ✓

- L5 真实见证：`1259` kind=commit outcome=errant_commit oracle_diff=—

### fault 22

主链每一条边均验证为直接 parent：

- `126` (fault_applied) → `127` (carrier_state)；child.parent=126 ✓
- `127` (carrier_state) → `128` (operand_read)；child.parent=127 ✓
- `128` (operand_read) → `129` (execute)；child.parent=128 ✓
- `129` (execute) → `130` (prf_writeback)；child.parent=129 ✓
- `130` (prf_writeback) → `131` (commit)；child.parent=130 ✓
- `131` (commit) → `1281` (chain_end)；child.parent=131 ✓

- L5 真实见证：`131` kind=commit outcome=errant_commit oracle_diff=—

### fault 23

主链每一条边均验证为直接 parent：

- `132` (fault_applied) → `133` (carrier_state)；child.parent=132 ✓
- `133` (carrier_state) → `134` (operand_read)；child.parent=133 ✓
- `134` (operand_read) → `135` (execute)；child.parent=134 ✓
- `135` (execute) → `136` (prf_writeback)；child.parent=135 ✓
- `136` (prf_writeback) → `137` (commit)；child.parent=136 ✓
- `137` (commit) → `1282` (chain_end)；child.parent=137 ✓

- L5 真实见证：`137` kind=commit outcome=errant_commit oracle_diff=—

### fault 24

主链每一条边均验证为直接 parent：

- `138` (fault_applied) → `139` (carrier_state)；child.parent=138 ✓
- `139` (carrier_state) → `140` (operand_read)；child.parent=139 ✓
- `140` (operand_read) → `141` (execute)；child.parent=140 ✓
- `141` (execute) → `142` (prf_writeback)；child.parent=141 ✓
- `142` (prf_writeback) → `143` (commit)；child.parent=142 ✓
- `143` (commit) → `1283` (chain_end)；child.parent=143 ✓

- L5 真实见证：`143` kind=commit outcome=errant_commit oracle_diff=—

### fault 25

主链每一条边均验证为直接 parent：

- `144` (fault_applied) → `145` (carrier_state)；child.parent=144 ✓
- `145` (carrier_state) → `146` (operand_read)；child.parent=145 ✓
- `146` (operand_read) → `147` (execute)；child.parent=146 ✓
- `147` (execute) → `148` (prf_writeback)；child.parent=147 ✓
- `148` (prf_writeback) → `149` (commit)；child.parent=148 ✓
- `149` (commit) → `1284` (chain_end)；child.parent=149 ✓

- L5 真实见证：`149` kind=commit outcome=errant_commit oracle_diff=—

### fault 26

主链每一条边均验证为直接 parent：

- `150` (fault_applied) → `151` (carrier_state)；child.parent=150 ✓
- `151` (carrier_state) → `152` (operand_read)；child.parent=151 ✓
- `152` (operand_read) → `153` (execute)；child.parent=152 ✓
- `153` (execute) → `154` (prf_writeback)；child.parent=153 ✓
- `154` (prf_writeback) → `155` (commit)；child.parent=154 ✓
- `155` (commit) → `1285` (chain_end)；child.parent=155 ✓

- L5 真实见证：`155` kind=commit outcome=errant_commit oracle_diff=—

### fault 27

主链每一条边均验证为直接 parent：

- `156` (fault_applied) → `157` (carrier_state)；child.parent=156 ✓
- `157` (carrier_state) → `158` (operand_read)；child.parent=157 ✓
- `158` (operand_read) → `159` (execute)；child.parent=158 ✓
- `159` (execute) → `160` (prf_writeback)；child.parent=159 ✓
- `160` (prf_writeback) → `161` (commit)；child.parent=160 ✓
- `161` (commit) → `1286` (chain_end)；child.parent=161 ✓

- L5 真实见证：`161` kind=commit outcome=errant_commit oracle_diff=—

### fault 28

主链每一条边均验证为直接 parent：

- `162` (fault_applied) → `163` (carrier_state)；child.parent=162 ✓
- `163` (carrier_state) → `164` (operand_read)；child.parent=163 ✓
- `164` (operand_read) → `165` (execute)；child.parent=164 ✓
- `165` (execute) → `166` (prf_writeback)；child.parent=165 ✓
- `166` (prf_writeback) → `167` (commit)；child.parent=166 ✓
- `167` (commit) → `1287` (chain_end)；child.parent=167 ✓

- L5 真实见证：`167` kind=commit outcome=errant_commit oracle_diff=—

### fault 29

主链每一条边均验证为直接 parent：

- `168` (fault_applied) → `169` (carrier_state)；child.parent=168 ✓
- `169` (carrier_state) → `170` (operand_read)；child.parent=169 ✓
- `170` (operand_read) → `171` (execute)；child.parent=170 ✓
- `171` (execute) → `172` (prf_writeback)；child.parent=171 ✓
- `172` (prf_writeback) → `173` (commit)；child.parent=172 ✓
- `173` (commit) → `1288` (chain_end)；child.parent=173 ✓

- L5 真实见证：`173` kind=commit outcome=errant_commit oracle_diff=—

### fault 3

主链每一条边均验证为直接 parent：

- `12` (fault_applied) → `13` (carrier_state)；child.parent=12 ✓
- `13` (carrier_state) → `14` (operand_read)；child.parent=13 ✓
- `14` (operand_read) → `15` (execute)；child.parent=14 ✓
- `15` (execute) → `16` (prf_writeback)；child.parent=15 ✓
- `16` (prf_writeback) → `17` (commit)；child.parent=16 ✓
- `17` (commit) → `1262` (chain_end)；child.parent=17 ✓

- L5 真实见证：`17` kind=commit outcome=errant_commit oracle_diff=—

### fault 30

主链每一条边均验证为直接 parent：

- `174` (fault_applied) → `175` (carrier_state)；child.parent=174 ✓
- `175` (carrier_state) → `176` (operand_read)；child.parent=175 ✓
- `176` (operand_read) → `177` (execute)；child.parent=176 ✓
- `177` (execute) → `178` (prf_writeback)；child.parent=177 ✓
- `178` (prf_writeback) → `179` (commit)；child.parent=178 ✓
- `179` (commit) → `1289` (chain_end)；child.parent=179 ✓

- L5 真实见证：`179` kind=commit outcome=errant_commit oracle_diff=—

### fault 31

主链每一条边均验证为直接 parent：

- `180` (fault_applied) → `181` (carrier_state)；child.parent=180 ✓
- `181` (carrier_state) → `182` (operand_read)；child.parent=181 ✓
- `182` (operand_read) → `183` (execute)；child.parent=182 ✓
- `183` (execute) → `184` (prf_writeback)；child.parent=183 ✓
- `184` (prf_writeback) → `185` (commit)；child.parent=184 ✓
- `185` (commit) → `1290` (chain_end)；child.parent=185 ✓

- L5 真实见证：`185` kind=commit outcome=errant_commit oracle_diff=—

### fault 32

主链每一条边均验证为直接 parent：

- `186` (fault_applied) → `187` (carrier_state)；child.parent=186 ✓
- `187` (carrier_state) → `188` (operand_read)；child.parent=187 ✓
- `188` (operand_read) → `189` (execute)；child.parent=188 ✓
- `189` (execute) → `190` (prf_writeback)；child.parent=189 ✓
- `190` (prf_writeback) → `191` (commit)；child.parent=190 ✓
- `191` (commit) → `1291` (chain_end)；child.parent=191 ✓

- L5 真实见证：`191` kind=commit outcome=errant_commit oracle_diff=—

### fault 33

主链每一条边均验证为直接 parent：

- `192` (fault_applied) → `193` (carrier_state)；child.parent=192 ✓
- `193` (carrier_state) → `194` (operand_read)；child.parent=193 ✓
- `194` (operand_read) → `195` (execute)；child.parent=194 ✓
- `195` (execute) → `196` (prf_writeback)；child.parent=195 ✓
- `196` (prf_writeback) → `197` (commit)；child.parent=196 ✓
- `197` (commit) → `1292` (chain_end)；child.parent=197 ✓

- L5 真实见证：`197` kind=commit outcome=errant_commit oracle_diff=—

### fault 34

主链每一条边均验证为直接 parent：

- `198` (fault_applied) → `199` (carrier_state)；child.parent=198 ✓
- `199` (carrier_state) → `200` (operand_read)；child.parent=199 ✓
- `200` (operand_read) → `201` (execute)；child.parent=200 ✓
- `201` (execute) → `202` (prf_writeback)；child.parent=201 ✓
- `202` (prf_writeback) → `203` (commit)；child.parent=202 ✓
- `203` (commit) → `1293` (chain_end)；child.parent=203 ✓

- L5 真实见证：`203` kind=commit outcome=errant_commit oracle_diff=—

### fault 35

主链每一条边均验证为直接 parent：

- `204` (fault_applied) → `205` (carrier_state)；child.parent=204 ✓
- `205` (carrier_state) → `206` (operand_read)；child.parent=205 ✓
- `206` (operand_read) → `207` (execute)；child.parent=206 ✓
- `207` (execute) → `208` (prf_writeback)；child.parent=207 ✓
- `208` (prf_writeback) → `209` (commit)；child.parent=208 ✓
- `209` (commit) → `1294` (chain_end)；child.parent=209 ✓

- L5 真实见证：`209` kind=commit outcome=errant_commit oracle_diff=—

### fault 36

主链每一条边均验证为直接 parent：

- `210` (fault_applied) → `211` (carrier_state)；child.parent=210 ✓
- `211` (carrier_state) → `212` (operand_read)；child.parent=211 ✓
- `212` (operand_read) → `213` (execute)；child.parent=212 ✓
- `213` (execute) → `214` (prf_writeback)；child.parent=213 ✓
- `214` (prf_writeback) → `215` (commit)；child.parent=214 ✓
- `215` (commit) → `1295` (chain_end)；child.parent=215 ✓

- L5 真实见证：`215` kind=commit outcome=errant_commit oracle_diff=—

### fault 37

主链每一条边均验证为直接 parent：

- `216` (fault_applied) → `217` (carrier_state)；child.parent=216 ✓
- `217` (carrier_state) → `218` (operand_read)；child.parent=217 ✓
- `218` (operand_read) → `219` (execute)；child.parent=218 ✓
- `219` (execute) → `220` (prf_writeback)；child.parent=219 ✓
- `220` (prf_writeback) → `221` (commit)；child.parent=220 ✓
- `221` (commit) → `1296` (chain_end)；child.parent=221 ✓

- L5 真实见证：`221` kind=commit outcome=errant_commit oracle_diff=—

### fault 38

主链每一条边均验证为直接 parent：

- `222` (fault_applied) → `223` (carrier_state)；child.parent=222 ✓
- `223` (carrier_state) → `224` (operand_read)；child.parent=223 ✓
- `224` (operand_read) → `225` (execute)；child.parent=224 ✓
- `225` (execute) → `226` (prf_writeback)；child.parent=225 ✓
- `226` (prf_writeback) → `227` (commit)；child.parent=226 ✓
- `227` (commit) → `1297` (chain_end)；child.parent=227 ✓

- L5 真实见证：`227` kind=commit outcome=errant_commit oracle_diff=—

### fault 39

主链每一条边均验证为直接 parent：

- `228` (fault_applied) → `229` (carrier_state)；child.parent=228 ✓
- `229` (carrier_state) → `230` (operand_read)；child.parent=229 ✓
- `230` (operand_read) → `231` (execute)；child.parent=230 ✓
- `231` (execute) → `232` (prf_writeback)；child.parent=231 ✓
- `232` (prf_writeback) → `233` (commit)；child.parent=232 ✓
- `233` (commit) → `1298` (chain_end)；child.parent=233 ✓

- L5 真实见证：`233` kind=commit outcome=errant_commit oracle_diff=—

### fault 4

主链每一条边均验证为直接 parent：

- `18` (fault_applied) → `19` (carrier_state)；child.parent=18 ✓
- `19` (carrier_state) → `20` (operand_read)；child.parent=19 ✓
- `20` (operand_read) → `21` (execute)；child.parent=20 ✓
- `21` (execute) → `22` (prf_writeback)；child.parent=21 ✓
- `22` (prf_writeback) → `23` (commit)；child.parent=22 ✓
- `23` (commit) → `1263` (chain_end)；child.parent=23 ✓

- L5 真实见证：`23` kind=commit outcome=errant_commit oracle_diff=—

### fault 40

主链每一条边均验证为直接 parent：

- `234` (fault_applied) → `235` (carrier_state)；child.parent=234 ✓
- `235` (carrier_state) → `236` (operand_read)；child.parent=235 ✓
- `236` (operand_read) → `237` (execute)；child.parent=236 ✓
- `237` (execute) → `238` (prf_writeback)；child.parent=237 ✓
- `238` (prf_writeback) → `239` (commit)；child.parent=238 ✓
- `239` (commit) → `1299` (chain_end)；child.parent=239 ✓

- L5 真实见证：`239` kind=commit outcome=errant_commit oracle_diff=—

### fault 41

主链每一条边均验证为直接 parent：

- `240` (fault_applied) → `241` (carrier_state)；child.parent=240 ✓
- `241` (carrier_state) → `242` (operand_read)；child.parent=241 ✓
- `242` (operand_read) → `243` (execute)；child.parent=242 ✓
- `243` (execute) → `244` (prf_writeback)；child.parent=243 ✓
- `244` (prf_writeback) → `245` (commit)；child.parent=244 ✓
- `245` (commit) → `1300` (chain_end)；child.parent=245 ✓

- L5 真实见证：`245` kind=commit outcome=errant_commit oracle_diff=—

### fault 42

主链每一条边均验证为直接 parent：

- `246` (fault_applied) → `247` (carrier_state)；child.parent=246 ✓
- `247` (carrier_state) → `248` (operand_read)；child.parent=247 ✓
- `248` (operand_read) → `249` (execute)；child.parent=248 ✓
- `249` (execute) → `250` (prf_writeback)；child.parent=249 ✓
- `250` (prf_writeback) → `251` (commit)；child.parent=250 ✓
- `251` (commit) → `1301` (chain_end)；child.parent=251 ✓

- L5 真实见证：`251` kind=commit outcome=errant_commit oracle_diff=—

### fault 43

主链每一条边均验证为直接 parent：

- `252` (fault_applied) → `253` (carrier_state)；child.parent=252 ✓
- `253` (carrier_state) → `254` (operand_read)；child.parent=253 ✓
- `254` (operand_read) → `255` (execute)；child.parent=254 ✓
- `255` (execute) → `256` (prf_writeback)；child.parent=255 ✓
- `256` (prf_writeback) → `257` (commit)；child.parent=256 ✓
- `257` (commit) → `1302` (chain_end)；child.parent=257 ✓

- L5 真实见证：`257` kind=commit outcome=errant_commit oracle_diff=—

### fault 44

主链每一条边均验证为直接 parent：

- `258` (fault_applied) → `259` (carrier_state)；child.parent=258 ✓
- `259` (carrier_state) → `260` (operand_read)；child.parent=259 ✓
- `260` (operand_read) → `261` (execute)；child.parent=260 ✓
- `261` (execute) → `262` (prf_writeback)；child.parent=261 ✓
- `262` (prf_writeback) → `263` (commit)；child.parent=262 ✓
- `263` (commit) → `1303` (chain_end)；child.parent=263 ✓

- L5 真实见证：`263` kind=commit outcome=errant_commit oracle_diff=—

### fault 45

主链每一条边均验证为直接 parent：

- `264` (fault_applied) → `265` (carrier_state)；child.parent=264 ✓
- `265` (carrier_state) → `266` (operand_read)；child.parent=265 ✓
- `266` (operand_read) → `267` (execute)；child.parent=266 ✓
- `267` (execute) → `268` (prf_writeback)；child.parent=267 ✓
- `268` (prf_writeback) → `269` (commit)；child.parent=268 ✓
- `269` (commit) → `1304` (chain_end)；child.parent=269 ✓

- L5 真实见证：`269` kind=commit outcome=errant_commit oracle_diff=—

### fault 46

主链每一条边均验证为直接 parent：

- `270` (fault_applied) → `271` (carrier_state)；child.parent=270 ✓
- `271` (carrier_state) → `272` (operand_read)；child.parent=271 ✓
- `272` (operand_read) → `273` (execute)；child.parent=272 ✓
- `273` (execute) → `274` (prf_writeback)；child.parent=273 ✓
- `274` (prf_writeback) → `275` (commit)；child.parent=274 ✓
- `275` (commit) → `1305` (chain_end)；child.parent=275 ✓

- L5 真实见证：`275` kind=commit outcome=errant_commit oracle_diff=—

### fault 47

主链每一条边均验证为直接 parent：

- `276` (fault_applied) → `277` (carrier_state)；child.parent=276 ✓
- `277` (carrier_state) → `278` (operand_read)；child.parent=277 ✓
- `278` (operand_read) → `279` (execute)；child.parent=278 ✓
- `279` (execute) → `280` (prf_writeback)；child.parent=279 ✓
- `280` (prf_writeback) → `281` (commit)；child.parent=280 ✓
- `281` (commit) → `1306` (chain_end)；child.parent=281 ✓

- L5 真实见证：`281` kind=commit outcome=errant_commit oracle_diff=—

### fault 48

主链每一条边均验证为直接 parent：

- `282` (fault_applied) → `283` (carrier_state)；child.parent=282 ✓
- `283` (carrier_state) → `284` (operand_read)；child.parent=283 ✓
- `284` (operand_read) → `285` (execute)；child.parent=284 ✓
- `285` (execute) → `286` (prf_writeback)；child.parent=285 ✓
- `286` (prf_writeback) → `287` (commit)；child.parent=286 ✓
- `287` (commit) → `1307` (chain_end)；child.parent=287 ✓

- L5 真实见证：`287` kind=commit outcome=errant_commit oracle_diff=—

### fault 49

主链每一条边均验证为直接 parent：

- `288` (fault_applied) → `289` (carrier_state)；child.parent=288 ✓
- `289` (carrier_state) → `290` (operand_read)；child.parent=289 ✓
- `290` (operand_read) → `291` (execute)；child.parent=290 ✓
- `291` (execute) → `292` (prf_writeback)；child.parent=291 ✓
- `292` (prf_writeback) → `293` (commit)；child.parent=292 ✓
- `293` (commit) → `1308` (chain_end)；child.parent=293 ✓

- L5 真实见证：`293` kind=commit outcome=errant_commit oracle_diff=—

### fault 5

主链每一条边均验证为直接 parent：

- `24` (fault_applied) → `25` (carrier_state)；child.parent=24 ✓
- `25` (carrier_state) → `26` (operand_read)；child.parent=25 ✓
- `26` (operand_read) → `27` (execute)；child.parent=26 ✓
- `27` (execute) → `28` (prf_writeback)；child.parent=27 ✓
- `28` (prf_writeback) → `29` (commit)；child.parent=28 ✓
- `29` (commit) → `1264` (chain_end)；child.parent=29 ✓

- L5 真实见证：`29` kind=commit outcome=errant_commit oracle_diff=—

### fault 50

主链每一条边均验证为直接 parent：

- `294` (fault_applied) → `295` (carrier_state)；child.parent=294 ✓
- `295` (carrier_state) → `296` (operand_read)；child.parent=295 ✓
- `296` (operand_read) → `297` (execute)；child.parent=296 ✓
- `297` (execute) → `298` (prf_writeback)；child.parent=297 ✓
- `298` (prf_writeback) → `299` (commit)；child.parent=298 ✓
- `299` (commit) → `1309` (chain_end)；child.parent=299 ✓

- L5 真实见证：`299` kind=commit outcome=errant_commit oracle_diff=—

### fault 51

主链每一条边均验证为直接 parent：

- `300` (fault_applied) → `301` (carrier_state)；child.parent=300 ✓
- `301` (carrier_state) → `302` (operand_read)；child.parent=301 ✓
- `302` (operand_read) → `303` (execute)；child.parent=302 ✓
- `303` (execute) → `304` (prf_writeback)；child.parent=303 ✓
- `304` (prf_writeback) → `305` (commit)；child.parent=304 ✓
- `305` (commit) → `1310` (chain_end)；child.parent=305 ✓

- L5 真实见证：`305` kind=commit outcome=errant_commit oracle_diff=—

### fault 52

主链每一条边均验证为直接 parent：

- `306` (fault_applied) → `307` (carrier_state)；child.parent=306 ✓
- `307` (carrier_state) → `308` (operand_read)；child.parent=307 ✓
- `308` (operand_read) → `309` (execute)；child.parent=308 ✓
- `309` (execute) → `310` (prf_writeback)；child.parent=309 ✓
- `310` (prf_writeback) → `311` (commit)；child.parent=310 ✓
- `311` (commit) → `1311` (chain_end)；child.parent=311 ✓

- L5 真实见证：`311` kind=commit outcome=errant_commit oracle_diff=—

### fault 53

主链每一条边均验证为直接 parent：

- `312` (fault_applied) → `313` (carrier_state)；child.parent=312 ✓
- `313` (carrier_state) → `314` (operand_read)；child.parent=313 ✓
- `314` (operand_read) → `315` (execute)；child.parent=314 ✓
- `315` (execute) → `316` (prf_writeback)；child.parent=315 ✓
- `316` (prf_writeback) → `317` (commit)；child.parent=316 ✓
- `317` (commit) → `1312` (chain_end)；child.parent=317 ✓

- L5 真实见证：`317` kind=commit outcome=errant_commit oracle_diff=—

### fault 54

主链每一条边均验证为直接 parent：

- `318` (fault_applied) → `319` (carrier_state)；child.parent=318 ✓
- `319` (carrier_state) → `320` (operand_read)；child.parent=319 ✓
- `320` (operand_read) → `321` (execute)；child.parent=320 ✓
- `321` (execute) → `322` (prf_writeback)；child.parent=321 ✓
- `322` (prf_writeback) → `323` (commit)；child.parent=322 ✓
- `323` (commit) → `1313` (chain_end)；child.parent=323 ✓

- L5 真实见证：`323` kind=commit outcome=errant_commit oracle_diff=—

### fault 55

主链每一条边均验证为直接 parent：

- `324` (fault_applied) → `325` (carrier_state)；child.parent=324 ✓
- `325` (carrier_state) → `326` (operand_read)；child.parent=325 ✓
- `326` (operand_read) → `327` (execute)；child.parent=326 ✓
- `327` (execute) → `328` (prf_writeback)；child.parent=327 ✓
- `328` (prf_writeback) → `329` (commit)；child.parent=328 ✓
- `329` (commit) → `1314` (chain_end)；child.parent=329 ✓

- L5 真实见证：`329` kind=commit outcome=errant_commit oracle_diff=—

### fault 56

主链每一条边均验证为直接 parent：

- `330` (fault_applied) → `331` (carrier_state)；child.parent=330 ✓
- `331` (carrier_state) → `332` (operand_read)；child.parent=331 ✓
- `332` (operand_read) → `333` (execute)；child.parent=332 ✓
- `333` (execute) → `334` (prf_writeback)；child.parent=333 ✓
- `334` (prf_writeback) → `335` (commit)；child.parent=334 ✓
- `335` (commit) → `1315` (chain_end)；child.parent=335 ✓

- L5 真实见证：`335` kind=commit outcome=errant_commit oracle_diff=—

### fault 57

主链每一条边均验证为直接 parent：

- `336` (fault_applied) → `337` (carrier_state)；child.parent=336 ✓
- `337` (carrier_state) → `338` (operand_read)；child.parent=337 ✓
- `338` (operand_read) → `339` (execute)；child.parent=338 ✓
- `339` (execute) → `340` (prf_writeback)；child.parent=339 ✓
- `340` (prf_writeback) → `341` (commit)；child.parent=340 ✓
- `341` (commit) → `1316` (chain_end)；child.parent=341 ✓

- L5 真实见证：`341` kind=commit outcome=errant_commit oracle_diff=—

### fault 58

主链每一条边均验证为直接 parent：

- `342` (fault_applied) → `343` (carrier_state)；child.parent=342 ✓
- `343` (carrier_state) → `344` (operand_read)；child.parent=343 ✓
- `344` (operand_read) → `345` (execute)；child.parent=344 ✓
- `345` (execute) → `346` (prf_writeback)；child.parent=345 ✓
- `346` (prf_writeback) → `347` (commit)；child.parent=346 ✓
- `347` (commit) → `1317` (chain_end)；child.parent=347 ✓

- L5 真实见证：`347` kind=commit outcome=errant_commit oracle_diff=—

### fault 59

主链每一条边均验证为直接 parent：

- `348` (fault_applied) → `349` (carrier_state)；child.parent=348 ✓
- `349` (carrier_state) → `350` (operand_read)；child.parent=349 ✓
- `350` (operand_read) → `351` (execute)；child.parent=350 ✓
- `351` (execute) → `352` (prf_writeback)；child.parent=351 ✓
- `352` (prf_writeback) → `353` (commit)；child.parent=352 ✓
- `353` (commit) → `1318` (chain_end)；child.parent=353 ✓

- L5 真实见证：`353` kind=commit outcome=errant_commit oracle_diff=—

### fault 6

主链每一条边均验证为直接 parent：

- `30` (fault_applied) → `31` (carrier_state)；child.parent=30 ✓
- `31` (carrier_state) → `32` (operand_read)；child.parent=31 ✓
- `32` (operand_read) → `33` (execute)；child.parent=32 ✓
- `33` (execute) → `34` (prf_writeback)；child.parent=33 ✓
- `34` (prf_writeback) → `35` (commit)；child.parent=34 ✓
- `35` (commit) → `1265` (chain_end)；child.parent=35 ✓

- L5 真实见证：`35` kind=commit outcome=errant_commit oracle_diff=—

### fault 60

主链每一条边均验证为直接 parent：

- `354` (fault_applied) → `355` (carrier_state)；child.parent=354 ✓
- `355` (carrier_state) → `356` (operand_read)；child.parent=355 ✓
- `356` (operand_read) → `357` (execute)；child.parent=356 ✓
- `357` (execute) → `358` (prf_writeback)；child.parent=357 ✓
- `358` (prf_writeback) → `359` (commit)；child.parent=358 ✓
- `359` (commit) → `1319` (chain_end)；child.parent=359 ✓

- L5 真实见证：`359` kind=commit outcome=errant_commit oracle_diff=—

### fault 61

主链每一条边均验证为直接 parent：

- `360` (fault_applied) → `361` (carrier_state)；child.parent=360 ✓
- `361` (carrier_state) → `362` (operand_read)；child.parent=361 ✓
- `362` (operand_read) → `363` (execute)；child.parent=362 ✓
- `363` (execute) → `364` (prf_writeback)；child.parent=363 ✓
- `364` (prf_writeback) → `365` (commit)；child.parent=364 ✓
- `365` (commit) → `1320` (chain_end)；child.parent=365 ✓

- L5 真实见证：`365` kind=commit outcome=errant_commit oracle_diff=—

### fault 62

主链每一条边均验证为直接 parent：

- `366` (fault_applied) → `367` (carrier_state)；child.parent=366 ✓
- `367` (carrier_state) → `368` (operand_read)；child.parent=367 ✓
- `368` (operand_read) → `369` (execute)；child.parent=368 ✓
- `369` (execute) → `370` (prf_writeback)；child.parent=369 ✓
- `370` (prf_writeback) → `371` (commit)；child.parent=370 ✓
- `371` (commit) → `1321` (chain_end)；child.parent=371 ✓

- L5 真实见证：`371` kind=commit outcome=errant_commit oracle_diff=—

### fault 63

主链每一条边均验证为直接 parent：

- `372` (fault_applied) → `373` (carrier_state)；child.parent=372 ✓
- `373` (carrier_state) → `374` (operand_read)；child.parent=373 ✓
- `374` (operand_read) → `375` (execute)；child.parent=374 ✓
- `375` (execute) → `376` (prf_writeback)；child.parent=375 ✓
- `376` (prf_writeback) → `377` (commit)；child.parent=376 ✓
- `377` (commit) → `1322` (chain_end)；child.parent=377 ✓

- L5 真实见证：`377` kind=commit outcome=errant_commit oracle_diff=—

### fault 64

主链每一条边均验证为直接 parent：

- `378` (fault_applied) → `379` (carrier_state)；child.parent=378 ✓
- `379` (carrier_state) → `380` (operand_read)；child.parent=379 ✓
- `380` (operand_read) → `381` (execute)；child.parent=380 ✓
- `381` (execute) → `382` (prf_writeback)；child.parent=381 ✓
- `382` (prf_writeback) → `383` (commit)；child.parent=382 ✓
- `383` (commit) → `1323` (chain_end)；child.parent=383 ✓

- L5 真实见证：`383` kind=commit outcome=errant_commit oracle_diff=—

### fault 65

主链每一条边均验证为直接 parent：

- `384` (fault_applied) → `385` (carrier_state)；child.parent=384 ✓
- `385` (carrier_state) → `386` (operand_read)；child.parent=385 ✓
- `386` (operand_read) → `387` (execute)；child.parent=386 ✓
- `387` (execute) → `388` (prf_writeback)；child.parent=387 ✓
- `388` (prf_writeback) → `389` (commit)；child.parent=388 ✓
- `389` (commit) → `1324` (chain_end)；child.parent=389 ✓

- L5 真实见证：`389` kind=commit outcome=errant_commit oracle_diff=—

### fault 66

主链每一条边均验证为直接 parent：

- `390` (fault_applied) → `391` (carrier_state)；child.parent=390 ✓
- `391` (carrier_state) → `392` (operand_read)；child.parent=391 ✓
- `392` (operand_read) → `393` (execute)；child.parent=392 ✓
- `393` (execute) → `394` (prf_writeback)；child.parent=393 ✓
- `394` (prf_writeback) → `395` (commit)；child.parent=394 ✓
- `395` (commit) → `1325` (chain_end)；child.parent=395 ✓

- L5 真实见证：`395` kind=commit outcome=errant_commit oracle_diff=—

### fault 67

主链每一条边均验证为直接 parent：

- `396` (fault_applied) → `397` (carrier_state)；child.parent=396 ✓
- `397` (carrier_state) → `398` (operand_read)；child.parent=397 ✓
- `398` (operand_read) → `399` (execute)；child.parent=398 ✓
- `399` (execute) → `400` (prf_writeback)；child.parent=399 ✓
- `400` (prf_writeback) → `401` (commit)；child.parent=400 ✓
- `401` (commit) → `1326` (chain_end)；child.parent=401 ✓

- L5 真实见证：`401` kind=commit outcome=errant_commit oracle_diff=—

### fault 68

主链每一条边均验证为直接 parent：

- `402` (fault_applied) → `403` (carrier_state)；child.parent=402 ✓
- `403` (carrier_state) → `404` (operand_read)；child.parent=403 ✓
- `404` (operand_read) → `405` (execute)；child.parent=404 ✓
- `405` (execute) → `406` (prf_writeback)；child.parent=405 ✓
- `406` (prf_writeback) → `407` (commit)；child.parent=406 ✓
- `407` (commit) → `1327` (chain_end)；child.parent=407 ✓

- L5 真实见证：`407` kind=commit outcome=errant_commit oracle_diff=—

### fault 69

主链每一条边均验证为直接 parent：

- `408` (fault_applied) → `409` (carrier_state)；child.parent=408 ✓
- `409` (carrier_state) → `410` (operand_read)；child.parent=409 ✓
- `410` (operand_read) → `411` (execute)；child.parent=410 ✓
- `411` (execute) → `412` (prf_writeback)；child.parent=411 ✓
- `412` (prf_writeback) → `413` (commit)；child.parent=412 ✓
- `413` (commit) → `1328` (chain_end)；child.parent=413 ✓

- L5 真实见证：`413` kind=commit outcome=errant_commit oracle_diff=—

### fault 7

主链每一条边均验证为直接 parent：

- `36` (fault_applied) → `37` (carrier_state)；child.parent=36 ✓
- `37` (carrier_state) → `38` (operand_read)；child.parent=37 ✓
- `38` (operand_read) → `39` (execute)；child.parent=38 ✓
- `39` (execute) → `40` (prf_writeback)；child.parent=39 ✓
- `40` (prf_writeback) → `41` (commit)；child.parent=40 ✓
- `41` (commit) → `1266` (chain_end)；child.parent=41 ✓

- L5 真实见证：`41` kind=commit outcome=errant_commit oracle_diff=—

### fault 70

主链每一条边均验证为直接 parent：

- `414` (fault_applied) → `415` (carrier_state)；child.parent=414 ✓
- `415` (carrier_state) → `416` (operand_read)；child.parent=415 ✓
- `416` (operand_read) → `417` (execute)；child.parent=416 ✓
- `417` (execute) → `418` (prf_writeback)；child.parent=417 ✓
- `418` (prf_writeback) → `419` (commit)；child.parent=418 ✓
- `419` (commit) → `1329` (chain_end)；child.parent=419 ✓

- L5 真实见证：`419` kind=commit outcome=errant_commit oracle_diff=—

### fault 71

主链每一条边均验证为直接 parent：

- `420` (fault_applied) → `421` (carrier_state)；child.parent=420 ✓
- `421` (carrier_state) → `422` (operand_read)；child.parent=421 ✓
- `422` (operand_read) → `423` (execute)；child.parent=422 ✓
- `423` (execute) → `424` (prf_writeback)；child.parent=423 ✓
- `424` (prf_writeback) → `425` (commit)；child.parent=424 ✓
- `425` (commit) → `1330` (chain_end)；child.parent=425 ✓

- L5 真实见证：`425` kind=commit outcome=errant_commit oracle_diff=—

### fault 72

主链每一条边均验证为直接 parent：

- `426` (fault_applied) → `427` (carrier_state)；child.parent=426 ✓
- `427` (carrier_state) → `428` (operand_read)；child.parent=427 ✓
- `428` (operand_read) → `429` (execute)；child.parent=428 ✓
- `429` (execute) → `430` (prf_writeback)；child.parent=429 ✓
- `430` (prf_writeback) → `431` (commit)；child.parent=430 ✓
- `431` (commit) → `1331` (chain_end)；child.parent=431 ✓

- L5 真实见证：`431` kind=commit outcome=errant_commit oracle_diff=—

### fault 73

主链每一条边均验证为直接 parent：

- `432` (fault_applied) → `433` (carrier_state)；child.parent=432 ✓
- `433` (carrier_state) → `434` (operand_read)；child.parent=433 ✓
- `434` (operand_read) → `435` (execute)；child.parent=434 ✓
- `435` (execute) → `436` (prf_writeback)；child.parent=435 ✓
- `436` (prf_writeback) → `437` (commit)；child.parent=436 ✓
- `437` (commit) → `1332` (chain_end)；child.parent=437 ✓

- L5 真实见证：`437` kind=commit outcome=errant_commit oracle_diff=—

### fault 74

主链每一条边均验证为直接 parent：

- `438` (fault_applied) → `439` (carrier_state)；child.parent=438 ✓
- `439` (carrier_state) → `440` (operand_read)；child.parent=439 ✓
- `440` (operand_read) → `441` (execute)；child.parent=440 ✓
- `441` (execute) → `442` (prf_writeback)；child.parent=441 ✓
- `442` (prf_writeback) → `443` (commit)；child.parent=442 ✓
- `443` (commit) → `1333` (chain_end)；child.parent=443 ✓

- L5 真实见证：`443` kind=commit outcome=errant_commit oracle_diff=—

### fault 75

主链每一条边均验证为直接 parent：

- `444` (fault_applied) → `445` (carrier_state)；child.parent=444 ✓
- `445` (carrier_state) → `446` (operand_read)；child.parent=445 ✓
- `446` (operand_read) → `447` (execute)；child.parent=446 ✓
- `447` (execute) → `448` (prf_writeback)；child.parent=447 ✓
- `448` (prf_writeback) → `449` (commit)；child.parent=448 ✓
- `449` (commit) → `1334` (chain_end)；child.parent=449 ✓

- L5 真实见证：`449` kind=commit outcome=errant_commit oracle_diff=—

### fault 76

主链每一条边均验证为直接 parent：

- `450` (fault_applied) → `451` (carrier_state)；child.parent=450 ✓
- `451` (carrier_state) → `452` (operand_read)；child.parent=451 ✓
- `452` (operand_read) → `453` (execute)；child.parent=452 ✓
- `453` (execute) → `454` (prf_writeback)；child.parent=453 ✓
- `454` (prf_writeback) → `455` (commit)；child.parent=454 ✓
- `455` (commit) → `1335` (chain_end)；child.parent=455 ✓

- L5 真实见证：`455` kind=commit outcome=errant_commit oracle_diff=—

### fault 77

主链每一条边均验证为直接 parent：

- `456` (fault_applied) → `457` (carrier_state)；child.parent=456 ✓
- `457` (carrier_state) → `458` (operand_read)；child.parent=457 ✓
- `458` (operand_read) → `459` (execute)；child.parent=458 ✓
- `459` (execute) → `460` (prf_writeback)；child.parent=459 ✓
- `460` (prf_writeback) → `461` (commit)；child.parent=460 ✓
- `461` (commit) → `1336` (chain_end)；child.parent=461 ✓

- L5 真实见证：`461` kind=commit outcome=errant_commit oracle_diff=—

### fault 78

主链每一条边均验证为直接 parent：

- `462` (fault_applied) → `463` (carrier_state)；child.parent=462 ✓
- `463` (carrier_state) → `464` (operand_read)；child.parent=463 ✓
- `464` (operand_read) → `465` (execute)；child.parent=464 ✓
- `465` (execute) → `466` (prf_writeback)；child.parent=465 ✓
- `466` (prf_writeback) → `467` (commit)；child.parent=466 ✓
- `467` (commit) → `1337` (chain_end)；child.parent=467 ✓

- L5 真实见证：`467` kind=commit outcome=errant_commit oracle_diff=—

### fault 79

主链每一条边均验证为直接 parent：

- `468` (fault_applied) → `469` (carrier_state)；child.parent=468 ✓
- `469` (carrier_state) → `470` (operand_read)；child.parent=469 ✓
- `470` (operand_read) → `471` (execute)；child.parent=470 ✓
- `471` (execute) → `472` (prf_writeback)；child.parent=471 ✓
- `472` (prf_writeback) → `473` (commit)；child.parent=472 ✓
- `473` (commit) → `1338` (chain_end)；child.parent=473 ✓

- L5 真实见证：`473` kind=commit outcome=errant_commit oracle_diff=—

### fault 8

主链每一条边均验证为直接 parent：

- `42` (fault_applied) → `43` (carrier_state)；child.parent=42 ✓
- `43` (carrier_state) → `44` (operand_read)；child.parent=43 ✓
- `44` (operand_read) → `45` (execute)；child.parent=44 ✓
- `45` (execute) → `46` (prf_writeback)；child.parent=45 ✓
- `46` (prf_writeback) → `47` (commit)；child.parent=46 ✓
- `47` (commit) → `1267` (chain_end)；child.parent=47 ✓

- L5 真实见证：`47` kind=commit outcome=errant_commit oracle_diff=—

### fault 80

主链每一条边均验证为直接 parent：

- `474` (fault_applied) → `475` (carrier_state)；child.parent=474 ✓
- `475` (carrier_state) → `476` (operand_read)；child.parent=475 ✓
- `476` (operand_read) → `477` (execute)；child.parent=476 ✓
- `477` (execute) → `478` (prf_writeback)；child.parent=477 ✓
- `478` (prf_writeback) → `479` (commit)；child.parent=478 ✓
- `479` (commit) → `1339` (chain_end)；child.parent=479 ✓

- L5 真实见证：`479` kind=commit outcome=errant_commit oracle_diff=—

### fault 81

主链每一条边均验证为直接 parent：

- `480` (fault_applied) → `481` (carrier_state)；child.parent=480 ✓
- `481` (carrier_state) → `482` (operand_read)；child.parent=481 ✓
- `482` (operand_read) → `483` (execute)；child.parent=482 ✓
- `483` (execute) → `484` (prf_writeback)；child.parent=483 ✓
- `484` (prf_writeback) → `485` (commit)；child.parent=484 ✓
- `485` (commit) → `1340` (chain_end)；child.parent=485 ✓

- L5 真实见证：`485` kind=commit outcome=errant_commit oracle_diff=—

### fault 82

主链每一条边均验证为直接 parent：

- `486` (fault_applied) → `487` (carrier_state)；child.parent=486 ✓
- `487` (carrier_state) → `488` (operand_read)；child.parent=487 ✓
- `488` (operand_read) → `489` (execute)；child.parent=488 ✓
- `489` (execute) → `490` (prf_writeback)；child.parent=489 ✓
- `490` (prf_writeback) → `491` (commit)；child.parent=490 ✓
- `491` (commit) → `1341` (chain_end)；child.parent=491 ✓

- L5 真实见证：`491` kind=commit outcome=errant_commit oracle_diff=—

### fault 83

主链每一条边均验证为直接 parent：

- `492` (fault_applied) → `493` (carrier_state)；child.parent=492 ✓
- `493` (carrier_state) → `494` (operand_read)；child.parent=493 ✓
- `494` (operand_read) → `495` (execute)；child.parent=494 ✓
- `495` (execute) → `496` (prf_writeback)；child.parent=495 ✓
- `496` (prf_writeback) → `497` (commit)；child.parent=496 ✓
- `497` (commit) → `1342` (chain_end)；child.parent=497 ✓

- L5 真实见证：`497` kind=commit outcome=errant_commit oracle_diff=—

### fault 84

主链每一条边均验证为直接 parent：

- `498` (fault_applied) → `499` (carrier_state)；child.parent=498 ✓
- `499` (carrier_state) → `500` (operand_read)；child.parent=499 ✓
- `500` (operand_read) → `501` (execute)；child.parent=500 ✓
- `501` (execute) → `502` (prf_writeback)；child.parent=501 ✓
- `502` (prf_writeback) → `503` (commit)；child.parent=502 ✓
- `503` (commit) → `1343` (chain_end)；child.parent=503 ✓

- L5 真实见证：`503` kind=commit outcome=errant_commit oracle_diff=—

### fault 85

主链每一条边均验证为直接 parent：

- `504` (fault_applied) → `505` (carrier_state)；child.parent=504 ✓
- `505` (carrier_state) → `506` (operand_read)；child.parent=505 ✓
- `506` (operand_read) → `507` (execute)；child.parent=506 ✓
- `507` (execute) → `508` (prf_writeback)；child.parent=507 ✓
- `508` (prf_writeback) → `509` (commit)；child.parent=508 ✓
- `509` (commit) → `1344` (chain_end)；child.parent=509 ✓

- L5 真实见证：`509` kind=commit outcome=errant_commit oracle_diff=—

### fault 86

主链每一条边均验证为直接 parent：

- `510` (fault_applied) → `511` (carrier_state)；child.parent=510 ✓
- `511` (carrier_state) → `512` (operand_read)；child.parent=511 ✓
- `512` (operand_read) → `513` (execute)；child.parent=512 ✓
- `513` (execute) → `514` (prf_writeback)；child.parent=513 ✓
- `514` (prf_writeback) → `515` (commit)；child.parent=514 ✓
- `515` (commit) → `1345` (chain_end)；child.parent=515 ✓

- L5 真实见证：`515` kind=commit outcome=errant_commit oracle_diff=—

### fault 87

主链每一条边均验证为直接 parent：

- `516` (fault_applied) → `517` (carrier_state)；child.parent=516 ✓
- `517` (carrier_state) → `518` (operand_read)；child.parent=517 ✓
- `518` (operand_read) → `519` (execute)；child.parent=518 ✓
- `519` (execute) → `520` (prf_writeback)；child.parent=519 ✓
- `520` (prf_writeback) → `521` (commit)；child.parent=520 ✓
- `521` (commit) → `1346` (chain_end)；child.parent=521 ✓

- L5 真实见证：`521` kind=commit outcome=errant_commit oracle_diff=—

### fault 88

主链每一条边均验证为直接 parent：

- `522` (fault_applied) → `523` (carrier_state)；child.parent=522 ✓
- `523` (carrier_state) → `524` (operand_read)；child.parent=523 ✓
- `524` (operand_read) → `525` (execute)；child.parent=524 ✓
- `525` (execute) → `526` (prf_writeback)；child.parent=525 ✓
- `526` (prf_writeback) → `527` (commit)；child.parent=526 ✓
- `527` (commit) → `1347` (chain_end)；child.parent=527 ✓

- L5 真实见证：`527` kind=commit outcome=errant_commit oracle_diff=—

### fault 89

主链每一条边均验证为直接 parent：

- `528` (fault_applied) → `529` (carrier_state)；child.parent=528 ✓
- `529` (carrier_state) → `530` (operand_read)；child.parent=529 ✓
- `530` (operand_read) → `531` (execute)；child.parent=530 ✓
- `531` (execute) → `532` (prf_writeback)；child.parent=531 ✓
- `532` (prf_writeback) → `533` (commit)；child.parent=532 ✓
- `533` (commit) → `1348` (chain_end)；child.parent=533 ✓

- L5 真实见证：`533` kind=commit outcome=errant_commit oracle_diff=—

### fault 9

主链每一条边均验证为直接 parent：

- `48` (fault_applied) → `49` (carrier_state)；child.parent=48 ✓
- `49` (carrier_state) → `50` (operand_read)；child.parent=49 ✓
- `50` (operand_read) → `51` (execute)；child.parent=50 ✓
- `51` (execute) → `52` (prf_writeback)；child.parent=51 ✓
- `52` (prf_writeback) → `53` (commit)；child.parent=52 ✓
- `53` (commit) → `1268` (chain_end)；child.parent=53 ✓

- L5 真实见证：`53` kind=commit outcome=errant_commit oracle_diff=—

### fault 90

主链每一条边均验证为直接 parent：

- `534` (fault_applied) → `535` (carrier_state)；child.parent=534 ✓
- `535` (carrier_state) → `536` (operand_read)；child.parent=535 ✓
- `536` (operand_read) → `537` (execute)；child.parent=536 ✓
- `537` (execute) → `538` (prf_writeback)；child.parent=537 ✓
- `538` (prf_writeback) → `539` (commit)；child.parent=538 ✓
- `539` (commit) → `1349` (chain_end)；child.parent=539 ✓

- L5 真实见证：`539` kind=commit outcome=errant_commit oracle_diff=—

### fault 91

主链每一条边均验证为直接 parent：

- `540` (fault_applied) → `541` (carrier_state)；child.parent=540 ✓
- `541` (carrier_state) → `542` (operand_read)；child.parent=541 ✓
- `542` (operand_read) → `543` (execute)；child.parent=542 ✓
- `543` (execute) → `544` (prf_writeback)；child.parent=543 ✓
- `544` (prf_writeback) → `545` (commit)；child.parent=544 ✓
- `545` (commit) → `1350` (chain_end)；child.parent=545 ✓

- L5 真实见证：`545` kind=commit outcome=errant_commit oracle_diff=—

### fault 92

主链每一条边均验证为直接 parent：

- `546` (fault_applied) → `547` (carrier_state)；child.parent=546 ✓
- `547` (carrier_state) → `548` (operand_read)；child.parent=547 ✓
- `548` (operand_read) → `549` (execute)；child.parent=548 ✓
- `549` (execute) → `550` (prf_writeback)；child.parent=549 ✓
- `550` (prf_writeback) → `551` (commit)；child.parent=550 ✓
- `551` (commit) → `1351` (chain_end)；child.parent=551 ✓

- L5 真实见证：`551` kind=commit outcome=errant_commit oracle_diff=—

### fault 93

主链每一条边均验证为直接 parent：

- `552` (fault_applied) → `553` (carrier_state)；child.parent=552 ✓
- `553` (carrier_state) → `554` (operand_read)；child.parent=553 ✓
- `554` (operand_read) → `555` (execute)；child.parent=554 ✓
- `555` (execute) → `556` (prf_writeback)；child.parent=555 ✓
- `556` (prf_writeback) → `557` (commit)；child.parent=556 ✓
- `557` (commit) → `1352` (chain_end)；child.parent=557 ✓

- L5 真实见证：`557` kind=commit outcome=errant_commit oracle_diff=—

### fault 94

主链每一条边均验证为直接 parent：

- `558` (fault_applied) → `559` (carrier_state)；child.parent=558 ✓
- `559` (carrier_state) → `560` (operand_read)；child.parent=559 ✓
- `560` (operand_read) → `561` (execute)；child.parent=560 ✓
- `561` (execute) → `562` (prf_writeback)；child.parent=561 ✓
- `562` (prf_writeback) → `563` (commit)；child.parent=562 ✓
- `563` (commit) → `1353` (chain_end)；child.parent=563 ✓

- L5 真实见证：`563` kind=commit outcome=errant_commit oracle_diff=—

### fault 95

主链每一条边均验证为直接 parent：

- `564` (fault_applied) → `565` (carrier_state)；child.parent=564 ✓
- `565` (carrier_state) → `566` (operand_read)；child.parent=565 ✓
- `566` (operand_read) → `567` (execute)；child.parent=566 ✓
- `567` (execute) → `568` (prf_writeback)；child.parent=567 ✓
- `568` (prf_writeback) → `569` (commit)；child.parent=568 ✓
- `569` (commit) → `1354` (chain_end)；child.parent=569 ✓

- L5 真实见证：`569` kind=commit outcome=errant_commit oracle_diff=—

### fault 96

主链每一条边均验证为直接 parent：

- `570` (fault_applied) → `571` (carrier_state)；child.parent=570 ✓
- `571` (carrier_state) → `572` (operand_read)；child.parent=571 ✓
- `572` (operand_read) → `573` (execute)；child.parent=572 ✓
- `573` (execute) → `574` (prf_writeback)；child.parent=573 ✓
- `574` (prf_writeback) → `575` (commit)；child.parent=574 ✓
- `575` (commit) → `1355` (chain_end)；child.parent=575 ✓

- L5 真实见证：`575` kind=commit outcome=errant_commit oracle_diff=—

### fault 97

主链每一条边均验证为直接 parent：

- `576` (fault_applied) → `577` (carrier_state)；child.parent=576 ✓
- `577` (carrier_state) → `578` (operand_read)；child.parent=577 ✓
- `578` (operand_read) → `579` (execute)；child.parent=578 ✓
- `579` (execute) → `580` (prf_writeback)；child.parent=579 ✓
- `580` (prf_writeback) → `581` (commit)；child.parent=580 ✓
- `581` (commit) → `1356` (chain_end)；child.parent=581 ✓

- L5 真实见证：`581` kind=commit outcome=errant_commit oracle_diff=—

### fault 98

主链每一条边均验证为直接 parent：

- `582` (fault_applied) → `583` (carrier_state)；child.parent=582 ✓
- `583` (carrier_state) → `584` (operand_read)；child.parent=583 ✓
- `584` (operand_read) → `585` (execute)；child.parent=584 ✓
- `585` (execute) → `586` (prf_writeback)；child.parent=585 ✓
- `586` (prf_writeback) → `587` (commit)；child.parent=586 ✓
- `587` (commit) → `1357` (chain_end)；child.parent=587 ✓

- L5 真实见证：`587` kind=commit outcome=errant_commit oracle_diff=—

### fault 99

主链每一条边均验证为直接 parent：

- `588` (fault_applied) → `589` (carrier_state)；child.parent=588 ✓
- `589` (carrier_state) → `590` (operand_read)；child.parent=589 ✓
- `590` (operand_read) → `591` (execute)；child.parent=590 ✓
- `591` (execute) → `592` (prf_writeback)；child.parent=591 ✓
- `592` (prf_writeback) → `593` (commit)；child.parent=592 ✓
- `593` (commit) → `1358` (chain_end)；child.parent=593 ✓

- L5 真实见证：`593` kind=commit outcome=errant_commit oracle_diff=—

- 每个 fault 的传播链结局与 run-level 程序 oracle 结局分别陈述；若二者存在张力，本文并列保留，不强行调和。
- 一个 fault 达到 L5 不会自动认证其他 fault；seed certified 要求所有 injected fault 的链均 closed 且无违规。

## 9. 原始证据位置与 SHA-256

| 文件 | SHA-256 |
|---|---|
| `manifest.json` | `525d0869ea13fb814fc1e8342381a11798c448dc8aa9b27596dd8f31415d8a3c` |
| `run.out` | `122d57334a895db386ae933b13bca3aa4c39d2517b9dc5b83d931cabb7ec6ee1` |
| `run.err` | `11cf41d26ff737354f40df9a5d20b0db719a35e36cc767a8ee4fc7134e9850c8` |
| `stats.txt` | `8712d6345e116e8cb9c796526b2b2a8e5ac1cfe945e341d9223cb823c82db278` |
| `oracle.json` | `d9fb294f0c32c1944500c430c5da26561f478140e78e7a6971f08b2bdbb3ed50` |
| `chain_report.json` | `10f937e57b2a6f02fec02e10a1d8c524a5a556adced45004f976e2b3e9adf69c` |
| `ordinals.json` | `15d4a409c3d807aab196116acf1b7a7b027fc1959075d07b70db4bcb502d99ca` |
| `census/fpu_injections.log` | `d153ffcef9b24d6300f5e45cc845ff6f57d519c1226cad280a84cfcae023a2c2` |
| `inject/fpu_injections.log` | `b244465fc1af94ae6c909de7ccc11a33cb33acd0564ad8856710d09d86b0de0b` |
| `inject/prop_evt.txt.gz` | `4bf2ad5cf6ca124b63703d3db9834975258484343bae0c17cc1145c7d52c1384` |
| `inject/stats.txt` | `8712d6345e116e8cb9c796526b2b2a8e5ac1cfe945e341d9223cb823c82db278` |
| gem5 二进制 `/home/sdc/gem5-fi-fsu/CHAOS/gem5/build/ARM/gem5.opt` | `e1ee610d774d88b0ae23a89b9ce2620ce9d2cf3f59bad85f23a013af5117280c` |
| workload `/home/sdc/gem5-fi-fsu/workloads/directed/elemwise_fma_kernel_rate_v1` | `c698cd698e7339930ec4087f134fad0bde71b4a960cf83022c2996d34ac37784` |

## 10. 诚实边界

- 本文只使用本 seed 的原始证据；没有跨 seed、跨 RunID 复制。
- 未观测到的字段写作 N/A/Unknown，不推测；缺事件不推断 Masked。
- gem5 是功能级模型；本实验不是门级或商用硅的精确复刻。
- `chain_end` 只是生命周期收口，不是 L5；本文的 L5 只认真实commit/arch_state/oracle_diff 见证。
- 本 seed 含 210 个 fault；每个 fault 的 root/主链/终局独立，run-level oracle 单独记录。
