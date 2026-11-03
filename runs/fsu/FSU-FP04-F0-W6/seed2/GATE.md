# FSU-FP04-F0-W6 — W6 gate（非正式，不计 seed）

- suite：`w6-fp-v1` v1 （freq F0）
- suite_hash：`7af52ddcbc1ad03d71e7f683fe87c804a7ddbc0a9ed73a0a5d06e18dc43adf1a`
- suite seed：2
- component runs：3；PASS：3/3
- 正式 seed 计数：**+0**（gate 不计 519/240）
- 结论：**PASS**

| # | program | precision | lane | mask | oracle | 结论 |
|---|---|---|---|---|---|---|
| 1 | svd | fp64 | 64 | `None` | SDC | PASS |
| 2 | fft | fp32 | 32 | `None` | MASKED | PASS |
| 3 | sparse-cg | fp32 | 32 | `None` | SDC | PASS |

## 逐 component 检查

### svd

| 检查 | 结果 |
|---|---|

### fft

| 检查 | 结果 |
|---|---|

### sparse-cg

| 检查 | 结果 |
|---|---|

