# R6-L 有界重复 census（2026-11-03）

> 工具：`tools/r6_l_repeat_census.py`；二进制：`deecd9e3b58d493271afc93b67126128c31ecba082163dcaecf5bb958c3d848b`（源与 L 工作树 C++ 逐字节一致）；证据根：`/home/sdc/gem5-fi-ding/runs/lsu/r6_l_census_20261103/`。
> 每趟均为真实 gem5 运行，含独立目录、manifest、PID/PGID、SHA、起止时间与 exit code。未修改任何原始证据。

## 方法

- 频率定义不变：F1 平均 1,000,000 eligible events、F2/F4 100,000（±50% 抖动，`chaos_lsu_trigger.hh::scheduleNext`）。
- 首火位：`first_fire = warmup + iv/2 + lcg(seed)%iv`；F1 三 seed 最大 1,290,806；F2/F4 最大 140,806。
- L03-F0-W5 seed3 的首火位是 `draw_next_fire=561`（warmup=1, span=571）。
- 每键跑 repeat=1/5/10（F0 为 1/2/5），得到 `E1` 与 `delta=(E5-E1)/4`；不稳定时取更保守的较小 delta。
- `R = 1 + ceil((1.2*max_first_fire - E1)/delta)`；F0 用 `1.2*draw_next_fire`。
- 若测量期间发生注入，则用 warmup=10,000,000 重测未注入流；tier/seed/LCG 序列不变。

## 结果（真实 summary.json）

| key | tier | E1 | delta | delta 来源 | 目标 | R | 上限内 |
|---|---|---|---|---|---|---|---|
| L01-F1-W5 | F1 | 1262 | 16.333333 | min(5,10) | 1290806 | **94759** | 是 |
| L01-F1-W12 | F1 | 13193 | 11867.75 | repeat=5 | 1290806 | **131** | 是 |
| L01-F2-W5 | F2 | 1262 | 16.333333 | min(5,10) | 140806 | **10269** | 是 |
| L01-F2-W12 | F2 | 13193 | 11867.75 | repeat=5 | 140806 | **15** | 是 |
| L02-F2-W5 | F2 | 1262 | 16.333333 | min(5,10) | 140806 | **10269** | 是 |
| L02-F2-W12 | F2 | 13193 | 11867.75 | repeat=5 | 140806 | **15** | 是 |
| L03-F4-W5 | F4 | 540 | 6.111111 | min(5,10) | 140806 | **27562** | 是 |
| L03-F4-W12 | F4 | 20432 | 19872.75 | repeat=5 | 140806 | **9** | 是 |
| L03-F0-W5-s3 | F0 | 540 | 12.0 | min(2,5) | draw=561 | **13** | 是 |

最大 R=94,759 < `CHAOS_REPEAT_MAX=131072`。实测每趟边际墙钟：W5 addrpath ≈4.6 ms、W5 lsqfwd ≈7.2 ms、W12 addrpath ≈0.80 s、W12 lsqfwd ≈0.76 s；对应单样本最坏约 7–8 分钟，低于 3600 s 预算。

## 科学边界

- 不改变频率定义、warmup/span、seed、注入字段/注入点或 RunID 身份。
- 重复的是**同一 workload 的核心操作序列**：`sq_forward` 与 `sqlite_like` 在 repeat=1 时输出与旧二进制逐字节一致；`ITER` 行全部等于冻结 golden。
- `sqlite_like` 为新编译的 repeat 载体（repeat=1 golden 仍为 `33f836327a416d35`）；代码布局变化会轻微改变 eligible 流，因此上表 E1 由**新二进制实际运行**测得，而不是沿用旧一次跑的数字。
- 原始 42 个 seed 目录保持不变；新运行使用独立目录。
