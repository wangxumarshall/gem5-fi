# SDC 逃逸集合分解（§8.1 机理 A–F）

| 机理 | SDC/逃逸事件数 | 占比 | 数据源 |
|---|---|---|---|
| A（无保护基线） | 3282 | — | h2-window, m1-formal-num, prf-formal, prf-readtrace-formal；L1D raw 97.7% [95.6,98.8]（n=384） |
| B（SED 对 ≥2-bit 同 parity 静默） | 384/384 静默（未消费） | — | artifacts/l1d-ecc secded-b2（n=384 全 Masked——2-bit 在 SED 下不可检，字节保持损坏直至被覆盖；行为=Latent，该 campaign 早于 PA 九类集成，标签按六类记 Masked，§8.1 语义归 B） |
| C（≥3-bit 超 SECDED 能力） | 384/384 静默（未消费） | — | artifacts/l1d-ecc secded-b3（n=384 全 Masked；同 B 的标签口径说明） |
| D（post-check escape：ECC 校验后数据通路） | 90.9% [87.6, 93.4] P_SDC | — | CHAOSL1DForward PCE formal（n=384，findings.md L1D 三层定论）：ECC 对 load 回填（fill→PRF）通路完全无效 |
| E（ECC 逻辑自身故障：漏检/误纠） | 机制对照实证（1-bit 漏检逃逸） | — | T5-1 CHAOSMem ecc_logic_fault：同 seed 同注入，secded=Corrected(0x0→0x0) vs ecc_logic_fault=Missed(0x0→0x80)；n=384 formal 待跑（机制+对照先行） |
| F（毒化传播丢失） | no formal data | — | 需 secded_poison 2-bit 档（DetectedContained 后毒化行不传播的场景注入）——如实标注 |

> All counts are gem5-proxy conditional outcomes, NOT FIT.
> B/C 的"占比"列留空：其分母应为"全部 2/3-bit 注入事件"（各 384），
> 静默率 100% 但传播率（Latent→SDC 转化）取决于后续消费——本表只记
> 逃逸集合归属，不做 FIT 换算。
> F 无数据：CHAOSCache secded_poison 档存在但 2-bit 毒化传播 formal
> 未跑——deferred（解锁：secded_poison × local_mbu campaign）。
