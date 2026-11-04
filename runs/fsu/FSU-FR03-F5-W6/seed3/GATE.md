# FSU-FR03-F5-W6 — FR03 gate（非正式，不计 seed）

- suite：`w6-fp-v1-fr03` v1 （W6，F5）
- suite_hash：`3b946a51ffb67e2086ed6df32395e90cd54c2d7dcf791654fb5e0312e61c172e`
- suite seed：3
- component runs：3；PASS：3/3
- 正式 seed 计数：**+0**（gate 不计 519/240）
- 结论：**PASS**

| # | program | target phys | lane(w/off) | mask | polarity | oracle | terminal | 结论 |
|---|---|---|---|---|---|---|---|---|
| 1 | svd | 47 | 64/0 | `0x0000000000010000` | 1 | MASKED | full | PASS |
| 2 | fft | 47 | 32/0 | `0x00010000` | 1 | SDC | full | PASS |
| 3 | sparse-cg | 47 | 32/0 | `0x00010000` | 1 | SDC | full | PASS |

## 计数与语义

- 一个 component run 不是 seed；本 gate 正式计数 **+0**。
- 永久 key = reg_class + phys_index + lane/mask + polarity；generation 仅是暴露/传播身份，free/realloc/squash 不清除。
- gate 只写 `runs/fsu-gates/`，拒绝 `runs/fsu/`。

### svd

| 检查 | 结果 |
|---|---|

### fft

| 检查 | 结果 |
|---|---|

### sparse-cg

| 检查 | 结果 |
|---|---|

