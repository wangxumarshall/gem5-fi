# FSU-FP04-F0-W6 seed3 — W6 formal suite seed

> 一个 suite seed 固定包含 3 个 component run（SVD/FFT/sparse-CG）；
> component 不进入 seed 计数，本文件只代表 **1 个正式 seed**。

- suite_hash: `7af52ddcbc1ad03d71e7f683fe87c804a7ddbc0a9ed73a0a5d06e18dc43adf1a`
- program_order: svd → fft → sparse-cg
- suite_seed: 3
- result: **PASS**

| # | program | precision | lane | oracle | audit.ok | certified | attempt |
|---|---|---|---|---|---|---|---|
| 1 | svd | fp64 | 64 | SDC | None | None | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W6/seed3/components/svd/FSU-FP04-F0-W6/seed9543147912694745727/attempt-1` |
| 2 | fft | fp32 | 32 | SDC | None | None | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W6/seed3/components/fft/FSU-FP04-F0-W6/seed10706550756726622601/attempt-1` |
| 3 | sparse-cg | fp32 | 32 | SDC | None | None | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP04-F0-W6/seed3/components/sparse-cg/FSU-FP04-F0-W6/seed7246570377758487670/attempt-1` |

## 计数规则

- 本 suite seed = **1** 个正式 seed。
- 3 个 component run / fault 不进入 `admitted_seeds_total`。
