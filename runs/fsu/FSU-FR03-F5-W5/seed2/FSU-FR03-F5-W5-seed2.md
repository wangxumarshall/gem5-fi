# FSU-FR03-F5-W5 seed2 — FR03 formal suite seed

> 一个 suite seed 固定包含 5 个 component run（FR03 永久物理 cell）；component 不进入 seed 计数。

- suite_hash: `98d88154edeac9992aa73e103cf76d835510cccf03c130c8590d208804a64d17`
- program_order: gemm → 2mm → lu → cholesky → jacobi-2d
- result: **PASS**

| # | program | phys | lane(w/off) | mask | polarity | oracle | audit.ok | certified | attempt |
|---|---|---|---|---|---|---|---|---|---|
| 1 | gemm | 46 | 32/1 | `0x80000000` | 1 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed2/components/gemm/FSU-FR03-F5-W5/seed10540722455272373253/attempt-1` |
| 2 | 2mm | 47 | 32/1 | `0x80000000` | 1 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed2/components/2mm/FSU-FR03-F5-W5/seed11463918361351675697/attempt-1` |
| 3 | lu | 46 | 32/1 | `0x80000000` | 1 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed2/components/lu/FSU-FR03-F5-W5/seed13028059462037197217/attempt-1` |
| 4 | cholesky | 46 | 32/1 | `0x80000000` | 1 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed2/components/cholesky/FSU-FR03-F5-W5/seed821049075403484347/attempt-1` |
| 5 | jacobi-2d | 46 | 32/1 | `0x80000000` | 1 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed2/components/jacobi-2d/FSU-FR03-F5-W5/seed16241230152303806820/attempt-1` |

## 计数规则

- 本 suite seed = **1** 个正式 seed。
- 5 个 component run / fault 不进入 seed 总数。
