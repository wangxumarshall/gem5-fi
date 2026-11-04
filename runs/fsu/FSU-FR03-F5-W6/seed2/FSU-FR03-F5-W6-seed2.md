# FSU-FR03-F5-W6 seed2 — FR03 formal suite seed

> 一个 suite seed 固定包含 3 个 component run（FR03 永久物理 cell）；component 不进入 seed 计数。

- suite_hash: `3b946a51ffb67e2086ed6df32395e90cd54c2d7dcf791654fb5e0312e61c172e`
- program_order: svd → fft → sparse-cg
- result: **PASS**

| # | program | phys | lane(w/off) | mask | polarity | oracle | audit.ok | certified | attempt |
|---|---|---|---|---|---|---|---|---|---|
| 1 | svd | 47 | 64/1 | `0x0000000080000000` | 1 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W6/seed2/components/svd/FSU-FR03-F5-W6/seed12133283597546251436/attempt-1` |
| 2 | fft | 47 | 32/1 | `0x80000000` | 1 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W6/seed2/components/fft/FSU-FR03-F5-W6/seed16265701575622021501/attempt-1` |
| 3 | sparse-cg | 47 | 32/1 | `0x80000000` | 1 | MASKED | True | True | `/home/sdc/gem5-fi-fsu/runs/fsu/FSU-FR03-F5-W6/seed2/components/sparse-cg/FSU-FR03-F5-W6/seed17527292261993683735/attempt-1` |

## 计数规则

- 本 suite seed = **1** 个正式 seed。
- 3 个 component run / fault 不进入 seed 总数。
