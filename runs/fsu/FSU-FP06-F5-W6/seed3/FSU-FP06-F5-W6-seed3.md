# FSU-FP06-F5-W6 seed3 — W6 formal suite seed

> 一个 suite seed 固定包含 3 个 component run（SVD/FFT/sparse-CG）；
> component 不进入 seed 计数，本文件只代表 **1 个正式 seed**。

- suite_hash: `2d1a8f9d84d502996724d97adc96b811f81b657fbcbdd0d1026fd34f3c406804`
- program_order: svd → fft → sparse-cg
- suite_seed: 3
- result: **PASS**

| # | program | precision | lane | oracle | audit.ok | certified | attempt |
|---|---|---|---|---|---|---|---|
| 1 | svd | fp64 | 64 | SDC | None | None | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W6/seed3/components/svd/FSU-FP06-F5-W6/seed7533103792189625731/attempt-1` |
| 2 | fft | fp32 | 32 | SDC | None | None | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W6/seed3/components/fft/FSU-FP06-F5-W6/seed2233063448526590541/attempt-1` |
| 3 | sparse-cg | fp32 | 32 | SDC | None | None | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FP06-F5-W6/seed3/components/sparse-cg/FSU-FP06-F5-W6/seed13519425898416439123/attempt-1` |

## 计数规则

- 本 suite seed = **1** 个正式 seed。
- 3 个 component run / fault 不进入 `admitted_seeds_total`。
