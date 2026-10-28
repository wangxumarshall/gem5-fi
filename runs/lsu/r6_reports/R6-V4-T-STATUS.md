# T 单元逐 RunID 3-seed 状态（R6-V4）

## 可执行格（11）

| RunID | seed1 | seed2 | seed3 | 3/3 |
|---|---|---|---|---|
| T05-F0-W4 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | 3/3 |
| T05-F2-W4 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | 3/3 |
| T06-F0-W4 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | 3/3 |
| T06-F2-W4 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | 3/3 |
| T07-F0-W4 | **PASS** full/L5 | **PASS** full/L5 | **PASS** full/L5 | 3/3 |
| T07-F4-W4 | **PASS** full/L5 | **PASS** detected_contained/L5 | **PASS** detected_contained/L5 | 3/3 |
| T08-F0-W4 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | 3/3 |
| T08-F4-W4 | **PASS** detected_contained/L2 | **PASS** detected_contained/L2 | NO_FIRE（频率模型无发射，非样本） | 2/3 |
| T10-F0-W4 | **PASS** full/L5 | **PASS** full/L5 | **PASS** full/L5 | 3/3 |
| T10-F1-W4 | **PASS** full/L5 | **PASS** full/L5 | **PASS** full/L5 | 3/3 |
| T10-F2-W4 | **PASS** full/L5 | **PASS** detected_contained/L5 | **PASS** full/L5 | 3/3 |

**COMPLETE_3_OF_3（本轮口径）: 10/11**

## 既有 COMPLETE_3_OF_3（17，不重跑）

| RunID | 证据根 | 二进制 SHA 前缀 |
|---|---|---|
| T01-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T01-F0-W4_s3` | `e8052842…` |
| T02-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F0-W4_s3` | `e8052842…` |
| T02-F2-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T02-F2-W4_s3` | `e8052842…` |
| T04-F0-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F0-W4_s3` | `e8052842…` |
| T04-F2-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_c9_T04-F2-W4_s3` | `e8052842…` |
| T01-F1-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F1-W4_s3` | `8a229009…` |
| T01-F2-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T01-F2-W4_s3` | `8a229009…` |
| T03-F5-W4 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s3` | `8a229009…` |
| T01-F0-W1 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F0-W1_s3` | `20fda699…` |
| T01-F1-W1 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F1-W1_s3` | `20fda699…` |
| T01-F2-W1 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T01-F2-W1_s3` | `20fda699…` |
| T02-F0-W1 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F0-W1_s3` | `20fda699…` |
| T02-F2-W1 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T02-F2-W1_s3` | `20fda699…` |
| T03-F5-W9 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T03-F5-W9_s3` | `20fda699…` |
| T10-F0-W1 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F0-W1_s3` | `20fda699…` |
| T10-F1-W1 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F1-W1_s3` | `20fda699…` |
| T10-F2-W1 | `/home/sdc/gem5-fi-ding/runs/lsu/r6_n8_T10-F2-W1_s3` | `20fda699…` |

## 排除格

| RunID | 原因 |
|---|---|
| T04-F6-W4 | F6 policy-excluded |
| T05-F6-W4 | F6 policy-excluded |
| T06-F6-W4 | F6 policy-excluded |
| T07-F6-W4 | F6 policy-excluded |
| T08-F6-W4 | F6 policy-excluded |
| T08-F6-W9 | F6 policy-excluded |
| T10-F0-W11 | BLOCKED_SPEC (SPEC CPU2017 license) |
| T10-F1-W11 | BLOCKED_SPEC (SPEC CPU2017 license) |
| T10-F2-W11 | BLOCKED_SPEC (SPEC CPU2017 license) |
| T08-F0-W9 | BLOCKED_WORKLOAD_GAP (no GAP/Graph500 FS carrier) |
| T08-F4-W9 | BLOCKED_WORKLOAD_GAP (no GAP/Graph500 FS carrier) |

## 逐 seed 明细（可执行格）

### T05-F0-W4 seed1 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `5`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s1`

### T05-F0-W4 seed2 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `5`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s2`

### T05-F0-W4 seed3 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `5`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F0-W4_s3`

### T05-F2-W4 seed1 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `649`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `3245`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `51cdb116ae3279b79a1819cf3c6b3220b3eb9716`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s1`

### T05-F2-W4 seed2 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `665`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `3325`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `9ef2a09c3645fb8dcb26b546337b7e37c2fffba4`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s2`

### T05-F2-W4 seed3 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `666`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `3330`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `9ef2a09c3645fb8dcb26b546337b7e37c2fffba4`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T05-F2-W4_s3`

### T06-F0-W4 seed1 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `5`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s1`

### T06-F0-W4 seed2 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `5`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `f11eb1c4b00ccf6fb14a4b2714905b8ee71f0c73`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s2`

### T06-F0-W4 seed3 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `5`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `ad1a47115d778cce6283e8ffd4d0796787f546cc`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F0-W4_s3`

### T06-F2-W4 seed1 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `8`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `40`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `ad1a47115d778cce6283e8ffd4d0796787f546cc`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s1`

### T06-F2-W4 seed2 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `7`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `35`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `ad1a47115d778cce6283e8ffd4d0796787f546cc`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s2`

### T06-F2-W4 seed3 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `4`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `20`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `ad1a47115d778cce6283e8ffd4d0796787f546cc`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T06-F2-W4_s3`

### T07-F0-W4 seed1 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Timeout`
- events: `4610`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s1`

### T07-F0-W4 seed2 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Timeout`
- events: `4610`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `d2c98585987bca136c071ec660d554666f1e4585`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s2`

### T07-F0-W4 seed3 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Timeout`
- events: `4610`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `ed8a08ca5bf61f4e8f0895c95e591015da8fe92f`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F0-W4_s3`

### T07-F4-W4 seed1 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `4`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `2289`
- binary_sha256: `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`
- binary_source_head: `1f344a5b66da30267c578536e00a1ad4ad56bb31`
- analysis_tool_head: `e30aa29d6867bbd9dd1839592baa69592dc2b50c`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s1`

### T07-F4-W4 seed2 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `8`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `4807`
- binary_sha256: `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`
- binary_source_head: `1f344a5b66da30267c578536e00a1ad4ad56bb31`
- analysis_tool_head: `e30aa29d6867bbd9dd1839592baa69592dc2b50c`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s2`

### T07-F4-W4 seed3 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `15`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `9312`
- binary_sha256: `3db54541b7fbafa47d27ab7a3f71b8c777c2893501078f3eb36fddb91cd866c2`
- binary_source_head: `1f344a5b66da30267c578536e00a1ad4ad56bb31`
- analysis_tool_head: `e30aa29d6867bbd9dd1839592baa69592dc2b50c`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T07-F4-W4_s3`

### T08-F0-W4 seed1 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `6`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F0-W4_s1`

### T08-F0-W4 seed2 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Timeout`
- events: `6`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `ad1a47115d778cce6283e8ffd4d0796787f546cc`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F0-W4_s2`

### T08-F0-W4 seed3 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Timeout`
- events: `6`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `98ea5cf8f2170d49c47d0bf5beaa7733f04e8efd`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F0-W4_s3`

### T08-F4-W4 seed1 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `6`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `f6263a6f6b403b0d8d87a49559b7b0a7e59a00e8`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s1`

### T08-F4-W4 seed2 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L2`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Masked`
- events: `6`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `ed8a08ca5bf61f4e8f0895c95e591015da8fe92f`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s2`

### T08-F4-W4 seed3 — NO_FIRE

- terminal: `None`
- provable_to: `None`
- admitted: `None`
- certified: `None`
- violations: `[]`
- events: `0`
- binary_sha256: `e379cc5bb14b16d525d24325d30029a9d4630df2b317e506e354e39e7d4efe4b`
- binary_source_head: `0501a00f3a4b20b6023a9249821c4b1c62bc8fad`
- analysis_tool_head: `51cdb116ae3279b79a1819cf3c6b3220b3eb9716`
- reasons: `['frequency model produced no fire in this run (no injection -> not a sample)']`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T08-F4-W4_s3`

### T10-F0-W4 seed1 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `238`
- binary_sha256: `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- binary_source_head: `d1543872e155943893fdd6d18a489ff7c372d97d`
- analysis_tool_head: `9391fa8f`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F0-W4_s1`

### T10-F0-W4 seed2 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `433`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s2`

### T10-F0-W4 seed3 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `444`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F0-W4_s3`

### T10-F1-W4 seed1 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `1`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `9884`
- binary_sha256: `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- binary_source_head: `d1543872e155943893fdd6d18a489ff7c372d97d`
- analysis_tool_head: `9391fa8f`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F1-W4_s1`

### T10-F1-W4 seed2 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `2`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `2279`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s2`

### T10-F1-W4 seed3 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `3`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `25388`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F1-W4_s3`

### T10-F2-W4 seed1 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `5`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `6121`
- binary_sha256: `20fda6994ee257e60a6d99c4b4abc7232732c302aaccfeeee4661c448ea7390d`
- binary_source_head: `d1543872e155943893fdd6d18a489ff7c372d97d`
- analysis_tool_head: `9391fa8f`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v3_T10-F2-W4_s1`

### T10-F2-W4 seed2 — QUALIFIED

- terminal: `detected_contained`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `4`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `9450`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s2`

### T10-F2-W4 seed3 — QUALIFIED

- terminal: `full`
- provable_to: `L5`
- admitted: `True`
- certified: `True`
- violations: `[]`
- injected: `None`
- activated: `3`
- stats_injected: `None`
- count_contradiction: `False`
- outcome: `Crash`
- events: `12752`
- binary_sha256: `b13a60abbdd3768b95ff15308e9dc8df94ba3784ddc5c7ae3ca0092fecb63117`
- binary_source_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- analysis_tool_head: `e2eccdecb31b0e71fa0a12294978e2b8003c7172`
- reasons: `[]`
- dir: `/home/sdc/gem5-fi-ding/runs/lsu/r6_v4_T10-F2-W4_s3`

