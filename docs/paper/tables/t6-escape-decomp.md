# SDC 逃逸集合分解（§8.1 机理 A–F）

| 机理 | SDC 事件数 | 占比 | 数据源 |
|---|---|---|---|
| A | 3282 | 100.0% | h2-window,m1-formal-num,prf-formal,prf-readtrace-formal |
| B | no data | — | SED-only ≥2-bit 静默 |
| C | no data | — | ≥3-bit 超 SECDED |
| D | no data | — | post-check escape（ECC 后数据通路） |
| E | no data | — | ECC 逻辑自身故障（漏检/误纠） |
| F | no data | — | 毒化传播丢失 |

> All counts are gem5-proxy conditional outcomes, NOT FIT.
> D/E/F 无 formal 数据（CHAOSL1DForward/CHAOSRAS 未跑 formal）——如实标注 no data。
