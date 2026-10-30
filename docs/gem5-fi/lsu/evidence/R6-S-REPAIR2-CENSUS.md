# R6-S 第二轮 F0 无偏 census（2026-10-30）

方法：修复轮二进制 `686458c3…`，与 campaign **完全同形的绝对路径命令**
（`--cmd $REPO/workloads/directed/sq_forward`），`--lsqfwd_lsu_tier F0
--lsqfwd_warmup_events 1 --lsqfwd_span_events 1000000000`（draw 永不落地，
纯计数），seed 不参与（不注入）。

实测（`runs/lsu/r6_s_repair2/census_abs/*.out`，teardown `eligible=`）：

| model | workload | eligible |
|---|---|---|
| S01 | directed/sq_forward | 6 |
| S02 | directed/sq_forward | 6 |
| S08 | directed/sq_forward | 1 |
| S09 | directed/sq_forward | 6 |

重要发现：guest 的 `argv[0]` 字符串长度会改变栈/缓存放置并影响 O3 时序，
因而改变 forwarding eligible 数（相对路径 census 得 7/7/2/7，绝对路径得
6/6/1/6，各自内部可复现）。span 必须以 campaign 的同形命令标定。

W1（mibench/bin/w1_all）census 单次约 7.5 h，尚未完成；F0 W1 两格
（S01-F0-W1、S02-F0-W1）在取得该 census 前保持 BLOCKED(F0-span-unmeasured)。
