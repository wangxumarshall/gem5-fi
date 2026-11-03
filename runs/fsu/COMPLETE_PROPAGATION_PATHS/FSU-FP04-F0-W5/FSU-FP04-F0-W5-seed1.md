# FSU-FP04-F0-W5 seed1 正式 suite seed

> 本文件是 **formal suite seed** 级记录，不是单个 PolyBench 程序。
> 一次 formal suite seed 固定包含 **5 个 component run**；
> 正式计数只 **+1 seed**，绝不把 component 数当 seed 数。

## 身份

| 项 | 值 |
|---|---|
| suite_id / version | `polybench-fp-v1` / `1` |
| suite_hash | `7282decf461243a8fdff38b6f99f66112c18027ee9a9b0a7dd057c4e2a0a7493` |
| suite seed | 1 |
| program_order | gemm → 2mm → lu → cholesky → jacobi-2d |
| component seed policy | `w5-component-seed-v1` |
| 正式 seed 计数 | +1（component run 不算 seed） |

## Component runs

| # | program | component seed | attempt | eligible | activated | fault | terminal | oracle | audit.ok | certified | 链接 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gemm | 12860380394881460486 | 2 | 1393944 | 1 | 1 | full | SDC | True | True | [attempt](components/gemm/FSU-FP04-F0-W5/seed12860380394881460486/attempt-2) |
| 2 | 2mm | 11459609017687405773 | 2 | 1145697 | 1 | 1 | full | SDC | True | True | [attempt](components/2mm/FSU-FP04-F0-W5/seed11459609017687405773/attempt-2) |
| 3 | lu | 17763049110757693680 | 2 | 800982 | 1 | 1 | full | SDC | True | True | [attempt](components/lu/FSU-FP04-F0-W5/seed17763049110757693680/attempt-2) |
| 4 | cholesky | 664471552991680598 | 2 | 810725 | 1 | 1 | full | MASKED | True | True | [attempt](components/cholesky/FSU-FP04-F0-W5/seed664471552991680598/attempt-2) |
| 5 | jacobi-2d | 933615570083433162 | 2 | 2099624 | 1 | 1 | full | SDC | True | True | [attempt](components/jacobi-2d/FSU-FP04-F0-W5/seed933615570083433162/attempt-2) |

## 计数规则

- 本 suite seed：**1** 个 formal suite seed。
- 本 suite seed 含 **5** 个 component run、**5** 次 component fault。
- component run / component fault 数量不进入 `admitted_seeds_total`；
  3 个 suite seed = 15 个 component run，但正式计数只 +3。

## 认证条件

- 5/5 component 均 admitted、独立 `audit.ok=true`、`certified=true`、oracle 非 SimulatorError/Inactive。
- 任一 component 失败 → 整个 suite seed 不认证；失败 attempt 保留，重试新建 attempt，不覆盖。
