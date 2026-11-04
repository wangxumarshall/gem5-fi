# FSU-FR03-F5-W5 — FR03 gate（非正式，不计 seed）

- suite：`polybench-fp-v1-fr03` v1 （W5，F5）
- suite_hash：`864c71cbb3a0c69275a0d8d36a09db2dd98eb21c446533e3ff26c703c90c8ee7`
- suite seed：1
- component runs：5；PASS：5/5
- 正式 seed 计数：**+0**（gate 不计 519/240）
- 结论：**PASS**

| # | program | target phys | lane(w/off) | mask | polarity | oracle | terminal | 结论 |
|---|---|---|---|---|---|---|---|---|
| 1 | gemm | 46 | 32/0 | `0x007f8000` | 0 | SDC | full | PASS |
| 2 | 2mm | 47 | 32/0 | `0x007f8000` | 0 | MASKED | full | PASS |
| 3 | lu | 46 | 32/0 | `0x007f8000` | 0 | MASKED | full | PASS |
| 4 | cholesky | 46 | 32/0 | `0x007f8000` | 0 | MASKED | full | PASS |
| 5 | jacobi-2d | 46 | 32/0 | `0x007f8000` | 0 | SDC | full | PASS |

## 计数与语义

- 一个 component run 不是 seed；本 gate 正式计数 **+0**。
- 永久 key = reg_class + phys_index + lane/mask + polarity；generation 仅是暴露/传播身份，free/realloc/squash 不清除。
- gate 只写 `runs/fsu-gates/`，拒绝 `runs/fsu/`。

### gemm

| 检查 | 结果 |
|---|---|

### 2mm

| 检查 | 结果 |
|---|---|

### lu

| 检查 | 结果 |
|---|---|

### cholesky

| 检查 | 结果 |
|---|---|

### jacobi-2d

| 检查 | 结果 |
|---|---|

