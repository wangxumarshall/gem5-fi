# R6-L NO_INJECTION 诊断（只读）

> 数据来自每个 seed 自己的 `run.out` teardown 行、`manifest.json` 与 run.out 的完整命令行；未运行 gem5、未修改证据。

| RunID | seed | tier | attempted | eligible | 首火位 | 差距 | mount | tier flag | 结论 |
|---|---|---|---|---|---|---|---|---|---|
| L01-F1-W12 | 1 | F1 | 35773 | 11306 | 1256412 | 1245106 | True | True | workload-supply-insufficient |
| L01-F1-W12 | 2 | F1 | 35773 | 11306 | 1049417 | 1038111 | True | True | workload-supply-insufficient |
| L01-F1-W12 | 3 | F1 | 35773 | 11306 | 1290806 | 1279500 | True | True | workload-supply-insufficient |
| L01-F1-W5 | 1 | F1 | 2572 | 1262 | 1256412 | 1255150 | True | True | workload-supply-insufficient |
| L01-F1-W5 | 2 | F1 | 2572 | 1262 | 1049417 | 1048155 | True | True | workload-supply-insufficient |
| L01-F1-W5 | 3 | F1 | 2572 | 1262 | 1290806 | 1289544 | True | True | workload-supply-insufficient |
| L01-F2-W12 | 1 | F2 | 35773 | 11306 | 106412 | 95106 | True | True | workload-supply-insufficient |
| L01-F2-W12 | 2 | F2 | 35773 | 11306 | 99417 | 88111 | True | True | workload-supply-insufficient |
| L01-F2-W12 | 3 | F2 | 35773 | 11306 | 140806 | 129500 | True | True | workload-supply-insufficient |
| L01-F2-W5 | 1 | F2 | 2572 | 1262 | 106412 | 105150 | True | True | workload-supply-insufficient |
| L01-F2-W5 | 2 | F2 | 2572 | 1262 | 99417 | 98155 | True | True | workload-supply-insufficient |
| L01-F2-W5 | 3 | F2 | 2572 | 1262 | 140806 | 139544 | True | True | workload-supply-insufficient |
| L02-F2-W12 | 1 | F2 | 35773 | 11306 | 106412 | 95106 | True | True | workload-supply-insufficient |
| L02-F2-W12 | 2 | F2 | 35773 | 11306 | 99417 | 88111 | True | True | workload-supply-insufficient |
| L02-F2-W12 | 3 | F2 | 35773 | 11306 | 140806 | 129500 | True | True | workload-supply-insufficient |
| L02-F2-W5 | 1 | F2 | 2572 | 1262 | 106412 | 105150 | True | True | workload-supply-insufficient |
| L02-F2-W5 | 2 | F2 | 2572 | 1262 | 99417 | 98155 | True | True | workload-supply-insufficient |
| L02-F2-W5 | 3 | F2 | 2572 | 1262 | 140806 | 139544 | True | True | workload-supply-insufficient |
| L03-F0-W5 | 3 | F0 | 540 | 540 | 561 | 21 | True | True | workload-supply-insufficient |
| L03-F4-W12 | 1 | F4 | 18681 | 18681 | 106412 | 87731 | True | True | workload-supply-insufficient |
| L03-F4-W12 | 2 | F4 | 18681 | 18681 | 99417 | 80736 | True | True | workload-supply-insufficient |
| L03-F4-W12 | 3 | F4 | 18681 | 18681 | 140806 | 122125 | True | True | workload-supply-insufficient |
| L03-F4-W5 | 1 | F4 | 540 | 540 | 106412 | 105872 | True | True | workload-supply-insufficient |
| L03-F4-W5 | 2 | F4 | 540 | 540 | 99417 | 98877 | True | True | workload-supply-insufficient |
| L03-F4-W5 | 3 | F4 | 540 | 540 | 140806 | 140266 | True | True | workload-supply-insufficient |

所有 injected=0 的样本均满足：hook 真实触发（attempted>0）、eligible 计数前进、注入器与 tier 已挂载；首火位严格大于本次负载提供的 eligible 数。因此零注入是**事件供给不足**，不是路由/计数/挂载缺陷。
