# R6-A3 状态（2026-10-28）

- 冻结二进制 `CHAOS/gem5/build/ARM/gem5.opt` sha256 `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e`
- 源码 HEAD `ddc81a7b074d0dae2505dc85c8fec5aef6293f66`
- 目标样本 90（30 非 F6 RunID × seed1/2/3），合格 65。

| RunID | s1 | s2 | s3 | 合格 |
|---|---|---|---|---|
| A01-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A01-F0-W9 | ✅ | ✅ | ✅ | 3/3 |
| A01-F1-W3 | ✅ | ❌(Masked/provable_to_L2_then_unknown) | ✅ | 2/3 |
| A01-F1-W9 | ✅ | ✅ | ✅ | 3/3 |
| A01-F2-W3 | ✅ | ❌(Masked/provable_to_L2_then_unknown) | ✅ | 2/3 |
| A01-F2-W9 | ❌(None/None) | ❌(None/None) | ❌(None/None) | 0/3 |
| A02-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A02-F0-W9 | ✅ | ✅ | ✅ | 3/3 |
| A02-F2-W3 | ✅ | ✅ | ✅ | 3/3 |
| A02-F2-W9 | ❌(None/None) | ❌(None/None) | ❌(None/None) | 0/3 |
| A03-F5-W3 | ✅ | ✅ | ✅ | 3/3 |
| A03-F5-W10 | ✅ | ✅ | ✅ | 3/3 |
| A04-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A04-F0-W0 | ✅ | ✅ | ✅ | 3/3 |
| A04-F2-W3 | ❌(Masked/None) | ✅ | ❌(Masked/None) | 1/3 |
| A04-F2-W0 | ❌(Masked/None) | ✅ | ❌(Masked/None) | 1/3 |
| A05-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A05-F2-W3 | ❌(Masked/None) | ❌(Masked/None) | ❌(Masked/None) | 0/3 |
| A06-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A06-F0-W5 | ✅ | ✅ | ✅ | 3/3 |
| A06-F2-W3 | ✅ | ✅ | ❌(Masked/None) | 2/3 |
| A06-F2-W5 | ✅ | ✅ | ❌(Masked/None) | 2/3 |
| A07-F0-W3 | ❌(Masked/provable_to_L0_then_unknown) | ❌(Masked/provable_to_L0_then_unknown) | ✅ | 1/3 |
| A07-F0-W5 | ✅ | ✅ | ✅ | 3/3 |
| A07-F4-W3 | ✅ | ✅ | ✅ | 3/3 |
| A07-F4-W5 | ✅ | ✅ | ✅ | 3/3 |
| A08-F0-W3 | ✅ | ✅ | ✅ | 3/3 |
| A08-F0-W5 | ✅ | ✅ | ✅ | 3/3 |
| A08-F2-W3 | ❌(Masked/None) | ❌(Masked/None) | ❌(Masked/None) | 0/3 |
| A08-F2-W5 | ❌(Masked/None) | ❌(Masked/None) | ❌(Masked/None) | 0/3 |

未合格样本的真实原因见 `R6-A3-STATUS.json` 的 samples 与逐 seed 文档。
