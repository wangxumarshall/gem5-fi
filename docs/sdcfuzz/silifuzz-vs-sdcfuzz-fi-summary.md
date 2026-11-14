# sdcfuzz vs SiliFuzz 随机故障注入实验结果

- 日期：2026-11-14T21:07:34；主机：sdc-0103；gem5：`/home/sdc/sdc-mhw/CHAOS/gem5/build/ARM/gem5.opt`
- 协议：CHAOSFPU，单次瞬态 bit flip，`probability=0.001`，`max_faults=1`；每条流 3600 条指令；每流 n=40

## 汇总

| 组 | 有效注入 | SDC | SDC 率 | Wilson 95% CI |
|---|---:|---:|---:|---|
| sdcfuzz | 240 | 178 | 0.7417 | [0.6828, 0.7929] |
| silifuzz | 240 | 0 | 0.0000 | [0.0000, 0.0158] |

Fisher 精确检验 p = 3.83e-78；SDC 率比 = inf。

## 逐流

| 流 | 组 | FP 指令 | 有效 | SDC | Masked | Hang | Crash | 其他 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| fp-add-v1 | sdcfuzz | 3200 | 40 | 28 | 12 | 0 | 0 | 0 |
| fp-add-v2 | sdcfuzz | 3200 | 40 | 28 | 12 | 0 | 0 | 0 |
| fp-add-v3 | sdcfuzz | 3200 | 40 | 26 | 14 | 0 | 0 | 0 |
| fp-mul-v1 | sdcfuzz | 3200 | 40 | 32 | 8 | 0 | 0 | 0 |
| fp-mul-v2 | sdcfuzz | 3200 | 40 | 32 | 8 | 0 | 0 | 0 |
| fp-mul-v3 | sdcfuzz | 3200 | 40 | 32 | 8 | 0 | 0 | 0 |
| snap-1 | silifuzz | 2323 | 40 | 0 | 40 | 0 | 0 | 0 |
| snap-2 | silifuzz | 2349 | 40 | 0 | 40 | 0 | 0 | 0 |
| snap-3 | silifuzz | 2349 | 40 | 0 | 40 | 0 | 0 | 0 |
| snap-4 | silifuzz | 2330 | 40 | 0 | 40 | 0 | 0 | 0 |
| snap-5 | silifuzz | 2350 | 40 | 0 | 40 | 0 | 0 | 0 |
| snap-6 | silifuzz | 2336 | 40 | 0 | 40 | 0 | 0 | 0 |
