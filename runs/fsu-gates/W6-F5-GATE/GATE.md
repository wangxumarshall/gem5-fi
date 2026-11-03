# FSU-FP06-F5-W6-GATE — W6 gate（非正式，不计 seed）

- suite：`w6-fp-v1-f5` v1 （freq F5）
- suite_hash：`2d1a8f9d84d502996724d97adc96b811f81b657fbcbdd0d1026fd34f3c406804`
- suite seed：1 / `FP06-a`
- component runs：3；PASS：3/3
- 正式 seed 计数：**+0**（gate 不计 519/240）
- 结论：**PASS**

| # | program | precision | lane | mask | oracle | 结论 |
|---|---|---|---|---|---|---|
| 1 | svd | fp64 | 64 | `0x8000000000000000` | SDC | PASS |
| 2 | fft | fp32 | 32 | `0x80000000` | SDC | PASS |
| 3 | sparse-cg | fp32 | 32 | `0x80000000` | SDC | PASS |

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

