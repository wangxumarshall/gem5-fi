# R6-A2 基线（defb3e0d，2026-10-28）

## 固定现场

- HEAD = origin/fix/r6-a-unit-20261028 = `defb3e0d`；origin/fi-ding = `659fa4cf`；工作树干净。
- 二进制 `CHAOS/gem5/build/ARM/gem5.opt`，sha256
  `37c9ec362595c4631a85b78f67c2d05bbc6b126bfcc0dfda7007bdb568c4699f`。
- gem5 / scons / campaign / pytest 进程 = 0（开工时）。

## 完整 pytest 基线

命令：`python3 -m pytest tests -q`（后台任务 bxkygyu9o）

```
........................................................................ [ 67%]
...................................                                      [100%]
107 passed in 244.87s (0:04:04)
EXIT=0
```

说明：用户工作令提到的两个既有失败
（`test_lsu_campaign_propagation` oracle-join 夹具、`test_lsu_freq_policy`
runid_map 旧 pin）在当前 `defb3e0d` 上**未复现**；基线为 107 passed / 0 failed。
后续回归按同一命令逐套件比较，NEW FAIL 必须为空。

## 同源 repeat census（current repeat binary，2026-10-28）

| model | workload | repeat=1 eligible | repeat=5 eligible | delta/iter |
|---|---|---|---|---|
| A01/A02 | agu_addrmodes | 2789 | 4327 | 384.5 |
| A04/A05/A07/A08 | agu_addrmodes | 2819 | 4356 | 384.25 |
| A04 | mini_check | 3187 | 6321 | 783.5 |
| A07/A08 | sq_forward | 2568 | 3282 | 178.5 |
| A01 | gap_bfs | 264751 | 526660 (r2) | 261909 |
| A06 | agu_addrmodes | 1685 | 2515 | 207.5 |
| A06 | sq_forward | 1627 | 2286 | 164.75 |

关键事实：eligible **不是**整次运行流长的线性倍数——首趟含静态 libc
启动流，后续每趟只增加探针体增量。因此 repeat 因子按
`R = 1 + ceil((1.2*max_first_fire - E1) / delta_per_iter)` 计算
（F1 max=1,290,806；F2/F4 max=140,806）。

## 首火可达性 canary（真实运行）

A01-F2-W3 seed1，`agu_addrmodes`，`--chaos_repeat 434`：

```
CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F2 attempted=106412
  eligible=106412 injected=1 first_eligible_tick=80080
  last_eligible_tick=148881425
CHAOS_L0_FUNNEL: CHAOSAddrPath attempted=106412 eligible=106412
  injected=1 activated=1
WALL=4.21s
```

首火位置（seed1=106,412 eligible，落在第 293 趟）真实到达并注入；
修复前同一 cell 三 seed 全 NO_FIRE。证据目录 `/tmp/r6a2_f2_canary`
（临时 canary，正式 seed 将写入 `runs/lsu/r6_a2_*`）。
