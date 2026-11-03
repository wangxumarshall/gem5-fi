# FSU-FP04-F0-W5 seed2 正式 suite seed

> 本文件是 **formal suite seed** 级记录，不是单个 PolyBench 程序。
> 一次 formal suite seed 固定包含 **5 个 component run**；
> 正式计数只 **+1 seed**，绝不把 component 数当 seed 数。

## 身份

| 项 | 值 |
|---|---|
| suite_id / version | `polybench-fp-v1` / `1` |
| suite_hash | `7282decf461243a8fdff38b6f99f66112c18027ee9a9b0a7dd057c4e2a0a7493` |
| suite seed | 2 |
| program_order | gemm → 2mm → lu → cholesky → jacobi-2d |
| component seed policy | `w5-component-seed-v1` |
| 正式 seed 计数 | +1（component run 不算 seed） |

## Component runs

| # | program | component seed | attempt | eligible | activated | fault | terminal | oracle | audit.ok | certified | 链接 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gemm | 12508894761670525649 | 1 | 1393944 | 1 | 1 | full | SDC | True | True | [attempt](components/gemm/FSU-FP04-F0-W5/seed12508894761670525649/attempt-1) |
| 2 | 2mm | 6553109338398911507 | 1 | 1145697 | 1 | 1 | full | SDC | True | True | [attempt](components/2mm/FSU-FP04-F0-W5/seed6553109338398911507/attempt-1) |
| 3 | lu | 9460439000491905388 | 1 | 800982 | 1 | 1 | full | SDC | True | True | [attempt](components/lu/FSU-FP04-F0-W5/seed9460439000491905388/attempt-1) |
| 4 | cholesky | 17653356909170313410 | 1 | 810725 | 1 | 1 | full | SDC | True | True | [attempt](components/cholesky/FSU-FP04-F0-W5/seed17653356909170313410/attempt-1) |
| 5 | jacobi-2d | 7539855237097253108 | 1 | 2099624 | 1 | 1 | full | SDC | True | True | [attempt](components/jacobi-2d/FSU-FP04-F0-W5/seed7539855237097253108/attempt-1) |

## 计数规则

- 本 suite seed：**1** 个 formal suite seed。
- 本 suite seed 含 **5** 个 component run、**5** 次 component fault。
- component run / component fault 数量不进入 `admitted_seeds_total`；
  3 个 suite seed = 15 个 component run，但正式计数只 +3。

## 认证条件

- 5/5 component 均 admitted、独立 `audit.ok=true`、`certified=true`、oracle 非 SimulatorError/Inactive。
- 任一 component 失败 → 整个 suite seed 不认证；失败 attempt 保留，重试新建 attempt，不覆盖。
