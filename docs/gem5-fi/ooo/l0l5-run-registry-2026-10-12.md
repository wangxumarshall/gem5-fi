# OOO L0-L5 formal 运行登记表（2026-10-12 21:11 启动）

> 任务书 §三/§四与阶段二指令的运行登记。总负责人 = 本会话 AI（唯一调度者）。
> 冻结：代码冻结点 `b257149`（campaign chaos_commit 声明值）＝准入通过面；检出提交 `7cc13f3`（仅冻结 SHA 代入，无代码差异）；gem5.opt `1a618953…0bf3`。

## RunAgent 实例表（2026-10-12 21:11:29 发射）

| RunAgent | campaign / RunID | 实例 PID | 日志 | 槽位 | NUMA |
|---|---|---|---|---|---|
| RunAgent-A | formal_D01-F0-W6-c（D01-F0-W6-c，imm_bitflip@coremark，seed 44072336） | 2187341 | `runs/ooo-l0l5/runagent-A.log` | ≤2 | worker 交替 0/1（实测 48-95 与 0-47 ✓） |
| RunAgent-B | formal_D02-F0-W6-b（D02-F0-W6-b，bitflip2_nonadj@coremark，seed 41211122） | 2187342 | `runs/ooo-l0l5/runagent-B.log` | ≤2 | 交替 1/0 |
| RunAgent-C | formal_D02-F0-W6-c（D02-F0-W6-c，bitflip2_cross@coremark，seed 47470573） | 2187343 | `runs/ooo-l0l5/runagent-C.log` | ≤2 | 交替 0/1 |
| policy-daemon | batch formal-2026-10-12（`runs/ooo-l0l5/specs/formal-batch.yaml`，frozen head=7cc13f3） | 2187344 | `runs/ooo-l0l5/scheduler-policy.log` | —（决策者，不占槽） | — |
| RunAgent-D（待升） | formal_D04-F0-W4-d（D04-F0-W4-d，dest_reg_sub@dep_chain，seed 42729898） | daemon 于 900s 稳定+门槛满足后代启（--launch） | `runs/ooo-l0l5/runagent-D.log`（代启时生成） | ≤2 | 交替 1/0 |

恢复命令（实例死亡且 claim 可回收时）：
`cd /home/sdc/gem5-fi-ding/.claude/worktrees/ooo-l0l5 && PYTHONHASHSEED=0 OOO_MAX_SLOTS=8 nohup setsid python3 tools/ooo_scheduler.py start --campaign-yaml campaigns/ooo-l0l5/<cid>.yaml --my-max-slots 2 --numa-nodes <0,1|1,0> --host-max-slots 6 --guard-dir /home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard --runs-root /home/sdc/gem5-fi-ding/runs >> runs/ooo-l0l5/runagent-X.log 2>&1 &`
（调度器自身幂等：从 results.jsonl + COMPLETE + QUARANTINE 三源扫描恢复，COMPLETE 只读跳过。）

## 启动门禁基线（21:10:58 实测）

MemAvailable 25,816,836 KiB · SwapFree 12,266,004 KiB · load 0.63/0.56/0.73 · /home 2.6T 可用 · guard 0 active/0 stale/0 claims · gem5=0。

## 资源阶梯（daemon 60s tick 自动执行）

- 初始 policy host_max_slots=6（21:11:30 已写）。
- 升 8：连续 900s（15 tick）MemAvailable≥12GiB、零换页、blocked=0、磁盘>200GiB → daemon 写 8 并代启 RunAgent-D。
- TRIP：MemAvailable<10GiB 或换页/blocked 连续 3 tick → 8→6→4，只停新派发不杀健康样本。
- 硬上限：sample_runner OOO_MAX_SLOTS=8（环境硬顶，任何情况不超 8）。

## 值守记录

- **[21:11:29]** 四实例发射；20s 后 guard n_active=5（爬坡）；A/C 各 2 worker、B rep0 于 21:12:07 完成（exit 0，38s——早期 Crash 类样本）并接力 rep2。
- **[21:12:07]** RunAgent-B 首个样本完成，调度无阻塞、无 exit 4/5。
