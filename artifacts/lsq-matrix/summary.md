# LSQ 转发故障模式矩阵（fp_fwd_kernel，n=64/cell，O3，first_clock=1e6，max_faults=1）

> 判据：fail_count oracle（fails>0→SDC）。7 几何轴（fwd_7case）已诚实废弃：其 volatile-no-barrier C 模式在 -O2 下不触达转发路径（注入日志 0 字节，输出==golden）。

| 故障模式 | SDC | Masked | Hang | P_SDC |
|---|---|---|---|---|
| bitflip | 64 | 0 | 0 | 1.000 |
| structural | 64 | 0 | 0 | 1.000 |
| fwdsrc | 0 | 64 | 0 | 0.000 |
| stale | 0 | 64 | 0 | 0.000 |
| phase | 64 | 0 | 0 | 1.000 |

> 模式说明：bitflip=单 bit 翻转（F1）；structural=byte_lane_skew rol1（core179 D1 撕裂移位）；fwdsrc=fwd_source_sub（F5 错源）；stale=stale_line_replay（陈旧行回放）；phase=phase_offset=2（F6 相位偏移）。
> fwdsrc/stale 的 Masked 阴性（注入确认发生，numFwdSourceSub/numStaleLineReplay=1）机制：fp_fwd_kernel 同址反复转发，替换源后 ring buffer 内仍是同 vaddr 的等值数据。
> All P_SDC are gem5-proxy conditional probabilities, NOT product FIT.
