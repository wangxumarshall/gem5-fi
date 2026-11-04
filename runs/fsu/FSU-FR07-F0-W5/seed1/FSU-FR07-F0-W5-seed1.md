# FSU-FR07-F0-W5 seed1 正式 suite seed

> 本文件是 **formal suite seed** 级记录，不是单个 PolyBench 程序。
> 一次 formal suite seed 固定包含 **5 个 component run**；
> 正式计数只 **+1 seed**，绝不把 component 数当 seed 数。

## 身份

| 项 | 值 |
|---|---|
| suite_id / version | `polybench-fp-v1-fr07-hook` / `1` |
| suite_hash | `cddba2cccf3ca90cb40695ea242bf8688ff178f505b3c48cf76b8e1143b0aa29` |
| suite seed | 1 |
| program_order | gemm → 2mm → lu → cholesky → jacobi-2d |
| component seed policy | `w5-component-seed-v1` |
| 正式 seed 计数 | +1（component run 不算 seed） |

## Component runs

| # | program | component seed | attempt | eligible | activated | fault | terminal | oracle | audit.ok | certified | 链接 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | gemm | 18312622370766522177 | 1 | 1393939 | 1 | 1 | full | SDC | True | True | [attempt](components/gemm/FSU-FR07-F0-W5/seed18312622370766522177/attempt-1) |
| 2 | 2mm | 1401221098083992335 | 1 | 1145691 | 1 | 1 | full | SDC | True | True | [attempt](components/2mm/FSU-FR07-F0-W5/seed1401221098083992335/attempt-1) |
| 3 | lu | 9933197546841919374 | 1 | 797385 | 1 | 1 | full | SDC | True | True | [attempt](components/lu/FSU-FR07-F0-W5/seed9933197546841919374/attempt-1) |
| 4 | cholesky | 10343971370867151644 | 1 | 806786 | 1 | 1 | full | SDC | True | True | [attempt](components/cholesky/FSU-FR07-F0-W5/seed10343971370867151644/attempt-1) |
| 5 | jacobi-2d | 14728238211833791645 | 1 | 2099620 | 1 | 1 | full | SDC | True | True | [attempt](components/jacobi-2d/FSU-FR07-F0-W5/seed14728238211833791645/attempt-1) |

## 计数规则

- 本 suite seed：**1** 个 formal suite seed。
- 本 suite seed 含 **5** 个 component run、**5** 次 component fault。
- component run / component fault 数量不进入 `admitted_seeds_total`；
  3 个 suite seed = 15 个 component run，但正式计数只 +3。

## 认证条件

- 5/5 component 均 admitted、独立 `audit.ok=true`、`certified=true`、oracle 非 SimulatorError/Inactive。
- 任一 component 失败 → 整个 suite seed 不认证；失败 attempt 保留，重试新建 attempt，不覆盖。
