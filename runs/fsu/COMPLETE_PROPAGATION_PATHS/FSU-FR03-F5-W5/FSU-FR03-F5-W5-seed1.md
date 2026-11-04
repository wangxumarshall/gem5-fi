# FSU-FR03-F5-W5 seed1 — FR03 formal suite seed

> 一个 suite seed 固定包含 5 个 component run（FR03 永久物理 cell）；component 不进入 seed 计数。

- suite_hash: `864c71cbb3a0c69275a0d8d36a09db2dd98eb21c446533e3ff26c703c90c8ee7`
- program_order: gemm → 2mm → lu → cholesky → jacobi-2d
- result: **PASS**

| # | program | phys | lane(w/off) | mask | polarity | oracle | audit.ok | certified | attempt |
|---|---|---|---|---|---|---|---|---|---|
| 1 | gemm | 46 | 32/0 | `0x007f8000` | 0 | SDC | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed1/components/gemm/FSU-FR03-F5-W5/seed13308999090817465172/attempt-1` |
| 2 | 2mm | 47 | 32/0 | `0x007f8000` | 0 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed1/components/2mm/FSU-FR03-F5-W5/seed18144183937250453399/attempt-1` |
| 3 | lu | 46 | 32/0 | `0x007f8000` | 0 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed1/components/lu/FSU-FR03-F5-W5/seed8444189732774129999/attempt-1` |
| 4 | cholesky | 46 | 32/0 | `0x007f8000` | 0 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed1/components/cholesky/FSU-FR03-F5-W5/seed16497714004944453208/attempt-1` |
| 5 | jacobi-2d | 46 | 32/0 | `0x007f8000` | 0 | SDC | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W5/seed1/components/jacobi-2d/FSU-FR03-F5-W5/seed5087231819706720640/attempt-1` |

## 计数规则

- 本 suite seed = **1** 个正式 seed。
- 5 个 component run / fault 不进入 seed 总数。
