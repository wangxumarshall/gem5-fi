# 07 · L0 注入项生命周期接口（规范）

> **文档地位**：实施层规范（gem5-fi W2.5 交付物），实现 `01-observation-points.md` 的 **L0 层**。
> 冲突裁决：与 `01-observation-points.md` 冲突时以 01 为准。
> 参考实现：`CHAOS/gem5/src/cpu/o3/chaos_l0.hh`（header-only 契约）+ CHAOSPhysReg 接线（W2.5）。
> 日期：2026-09-24 · 分支 fi-ding。

## 1. L0 的问题（01 原文意图）

被注入的那一项/那个字段，在被覆盖或运行结束前，**有没有被后续逻辑真正读取过**？
未命中（reads==0）=「无效注入」——**不计入 SDC 统计分母**（这是统计口径问题，不是故障效果）。

## 2. 三字段契约（每个被注入项）

| 字段 | 类型 | 语义 |
|---|---|---|
| `reads_before_overwrite` | uint64 | 注入后、被覆盖/运行结束前，该项目的**真实读取**次数 |
| `overwritten` | bool | 该项目是否被覆盖 |
| `overwritten_at_cycle` | uint64 | 覆盖被**检测到**的周期；0=从未覆盖 |

约定：每注入器实例只跟踪一项（campaign 的 maxFaults=1 纪律）；重复注册以最后一次为准。

## 3. 挂点模板（注入器侧三钩，chaos_l0.hh inline 契约）

```cpp
chaosL0Register(st, key)            // 注入时：登记目标（key=容器自身编号）
chaosL0CountRead(st, key)           // 读侧：容器每次真实读取时调用；
                                    //   只数匹配 key，覆盖后停止计数
                                    //   （覆盖后的读取属于新值——不是我们的）
chaosL0Overwrite(st, key, cycle)    // 写侧：容器每次写入时调用；
                                    //   首个匹配 key 的写=覆盖标记
```

**容器归属原则**：读/写计数钩子归**容器**（PhysRegFile::getReg/setReg、RAT lookup、ROB 槽位写等），注入器只登记与汇总。CHAOSPhysReg 是第一个实例：容器侧计数在 `regfile.hh`（readTrace 机制，reads_before_overwrite/overwritten），注入器经 `chaosL0Sync` 镜像并在退出时打终行。

## 3.3 输出口径与时机

- 终行格式：`CHAOS_L0: <injector>: target=<id> reads=<n> overwritten=<0/1> at=<cycle> hit=<0/1>`（`hit = reads>0`——有效注入判定）。
- **时机 = exit callback**（`registerExitCallback`，CHAOSProbe/CHAOSMicroSnap 先例）。**不要用周期轮询打终行**：短负载会在轮询间隔内 halt，轮询不再触发（smoke 上实测 ReadTraceFinal 不打印——W2.5 代理的实测发现）。
- 覆盖时刻 `at=` 是**观测粒度**：轮询看到翻转用轮询周期，否则用退出周期（诚实上界）。
- **Crash/abort 路径没有 exit callback** → Crash 运行合法地无 CHAOS_L0 行（与 W2.1 commit trace 截断同族的已知边界；Crash 的 L0 判定走存活部分或记 missing）。
- 无注入落地（触发未命中）→ 不打行（不是 0 读，是没有注入）。

## 4. 统计口径（campaign 侧）

- `hit=1` 的 rep 才进入 SDC/Crash 等比率的分母；`hit=0` 归入「无效注入」单独计数（01 的 L0 定义）。
- CHAOSPhysReg 的既有 `ReadTracePoll/ReadTraceFinal` 行**保留不动**（鲲鹏轨道既有依赖）；CHAOS_L0 行是**新增**对齐口径。

## 5. W4-W7 新注入器接线清单

每实现一个注入器（W4 RAT 换值、W5 done 位、W6 opcode、W7 向量族……）：
1. 容器侧加读/写计数钩（若容器已有则复用）；
2. 注入器 `chaosL0Register` 登记 + exit callback 打 `CHAOS_L0:` 终行；
3. campaign 消费 `hit` 字段进无效注入口径。

## 6. 验证记录（W2.5，2026-09-24）

- 基线前置发现（真机）：smoke 上 readTrace 轮询在 halt 后不再触发 → ReadTraceFinal 不打印 → 终行必须走 exit callback（本规范 §3.3 的来源）。
- 接线后验证：见 W2 执行计划 Task 5 执行注（reads>0 案例 + overwritten 案例 + golden 回归）。
