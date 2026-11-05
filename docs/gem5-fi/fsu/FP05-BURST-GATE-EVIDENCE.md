# FP05 burst 真实 gate 证据（2026-11-05）

构建：`CHAOS/gem5/build/ARM/gem5.opt`（含 burst 发射端）。
workload：`workloads/directed/neon_fp32_lane_kernel`（FP32 NEON MultAcc）。
census：`CHAOS_ELIGIBLE_COUNT=16384`（`SimdFloatMultAcc`），
fixed uniform skip = `chaos_pick_skip(seed=1, 16384) = 15571`。

| gate | 目录 | 结果 |
|---|---|---|
| same_lane len=3 | `runs/fsu-gates/FP05-BURST-GATE/inject` | **PASS**，3 events，ordinal 0/1/2，`completed`，accounting_ok=1 |
| same_lane len=2 | `.../len2` | **PASS**，2 events |
| same_lane len=4 | `.../len4` | **PASS**，4 events |
| lane_mask len=3 (0x00010001) | `.../mask3` | **PASS** |
| adjacent_lane len=3 step=1 | `.../adj3` | **PASS** |
| cross_lane_mbu len=2, 32-bit lane | `.../mbu2-32` | **PASS**，ULP=1024（真实传播） |
| cross_lane_mbu len=2, 64-bit lane | `.../mbu2` | 无注入：`lane_mismatch=16384`（fail closed，与 fp32 元素宽度不符） |
| tail short（skip=16382, len=3） | `.../short3` | 显式 `EPISODES_SHORT=1`、`burst_end_reason=run_exit`、`burst_episode_events=2`；strict gate **FAIL**（不把截断当完成） |

## 已验证的 gate 判据

- `eligible_ordinal_consecutive`：15572/15573/15574，连续无重复；
- `burst_end_completed` + `burst_end_length_matches` + `burst_end_event_count`；
- `burst_accounting_ok=1`（attempted/applied/activated/short/lane_rejected 守恒）；
- 每个事件 `value_hash` 与 `event_attempted_applied`；
- 每个 fault 有 terminal（operand_read/execute/prf_writeback/commit 链）；
- recurring/permanent 事件不带 burst 字段；
- 单 run 单 episode（`maxFaults==1` 构造期强制）。

## 未覆盖 / 诚实缺口

- 多来源 consumer 汇合 `merged>1` 未在该 workload 出现；gate 对 >0 的
  merge 会校验 source id，本次观察到 merged=1 的单源标记。
- F4 burst 起点间隔语义未实现（构造期 fail closed）。
- squash 不终止 episode（预注册语义），本次无 squash 样本。
- 正式试点（FP05-F0 RunID）尚未开始；先补这四项。
