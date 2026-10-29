# R6-A4 状态（2026-10-29，A 单元收口）

- 88/88 applicable samples qualified; 2/2 structurally inapplicable samples explicitly excluded; 0 applicable failures; A unit closed as COMPLETE_WITH_SPEC_EXCLUSIONS.
- applicable_samples=88；qualified_applicable_samples=88；spec_excluded_samples=2；failed_applicable_samples=0；unit_status=COMPLETE_WITH_SPEC_EXCLUSIONS
- 候选二进制（23 个新合格样本）sha256 `a1632e0f1d24be639044d24bac8e6fd902d0a6642b276fd430927471643e7046`（HEAD `167a23ee59b3a2383cdd1eaeeca418b263666a56`）
- 上一轮冻结二进制（65 个保留样本）sha256 `c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e`（HEAD `ddc81a7b074d0dae2505dc85c8fec5aef6293f66`）
- 两个 N/A 样本没有任何二进制运行结果（resolver 响亮 BLOCKED，未启动 gem5、未注入、未生成传播链）。
- 目标样本 90（30 非 F6 RunID × seed1/2/3）；F6 RunID 属独立的F6 政策排除，与本轮两个 A08-b SPEC_EXCLUDED 互不混淆。

| RunID | s1 | s2 | s3 | applicable | qualified |
|---|---|---|---|---|---|
| A01-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A01-F0-W9 | PASS | PASS | PASS | 3 | 3 |
| A01-F1-W3 | PASS | PASS | PASS | 3 | 3 |
| A01-F1-W9 | PASS | PASS | PASS | 3 | 3 |
| A01-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A01-F2-W9 | PASS | PASS | PASS | 3 | 3 |
| A02-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A02-F0-W9 | PASS | PASS | PASS | 3 | 3 |
| A02-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A02-F2-W9 | PASS | PASS | PASS | 3 | 3 |
| A03-F5-W3 | PASS | PASS | PASS | 3 | 3 |
| A03-F5-W10 | PASS | PASS | PASS | 3 | 3 |
| A04-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A04-F0-W0 | PASS | PASS | PASS | 3 | 3 |
| A04-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A04-F2-W0 | PASS | PASS | PASS | 3 | 3 |
| A05-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A05-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A06-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A06-F0-W5 | PASS | PASS | PASS | 3 | 3 |
| A06-F2-W3 | PASS | PASS | PASS | 3 | 3 |
| A06-F2-W5 | PASS | PASS | PASS | 3 | 3 |
| A07-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A07-F0-W5 | PASS | PASS | PASS | 3 | 3 |
| A07-F4-W3 | PASS | PASS | PASS | 3 | 3 |
| A07-F4-W5 | PASS | PASS | PASS | 3 | 3 |
| A08-F0-W3 | PASS | PASS | PASS | 3 | 3 |
| A08-F0-W5 | PASS | PASS | PASS | 3 | 3 |
| A08-F2-W3 | PASS | N/A (SPEC_EXCLUDED) | PASS | 2 | 2 |
| A08-F2-W5 | PASS | N/A (SPEC_EXCLUDED) | PASS | 2 | 2 |

N/A (SPEC_EXCLUDED) = `A08-b structurally unreachable under F2`；不是 PASS、不是 FAIL，不计入 applicable 分母，admitted/certified 均为空，无传播链。其余样本的真实原因见 `R6-A4-STATUS.json` 的 samples 与逐 seed 文档。
