# sdcfuzz / gem5-CHAOS 长期任务路线与进度

> 依据 sdcfuzz-v1.2.md 实施路线图；状态区分“本仓库实测”“外部证据”“部分完成”“未开始”“环境门控”

- 更新日期：2026-11-10
- 总进度：**61.8%**（完成 22/38，其中本仓库实测 18；部分 3，未开始 11，门控 2）

![路线进度图](roadmap.svg)

## 状态图例

- `done-local` — 完成（本仓库实测）
- `done-external` — 完成（外部证据，未本机复验）
- `partial` — 部分完成
- `todo` — 未开始
- `gated` — 环境门控（缺硬件/工具链）

## 里程碑明细

### 技术路线（sdcfuzz-v1.2.md §7）

#### Phase 0 · 基线完善（M0，100%）

| 里程碑 | 状态 | 证据 / 缺口 |
|---|---|---|
| D13 操作数启发式（上游 sdcfuzz 实现） | `done-external` | 上游 707db35d 原样同步到 sdcfuzz/upstream/d13/（sha256 4143a4…/fb461f…）；本地 golden、确定性、gem5 基线与单次 FI 冒烟通过；完整 4×100 复现见 docs/sdcfuzz/d13-baseline-reproduction.md |
| 上游 seeds/*.S 微架构模板（方案写 19，实测 20） | `done-external` | 上游 seeds/*.S 实际 20 个、覆盖 8 个模块（E/V/M/C/O/I/L/F）；上游 2026-09-03 合规评估已指出 scheme 的 19/7 口径过时；本仓库无副本，未逐条复验 |
| gem5-CHAOS 注入底座 + 生成→注入闭环 | `done-local` | 19 注入器；CHAOSReg 注入 1 次并分类 Masked（m5out/sdcfuzz-baseline） |
| 4 板 446 核 Kunpeng 920 真机部署 | `done-external` | sdcfuzz-v1.2.md §4.2 历史证据；本机无该硬件，未复验 |
| sdcfuzz 论文 p2 草稿 | `done-external` | 外部 sdcfuzz 仓库；本仓库无副本，未复验 |

#### Phase 1 · AutoµSens + ACE/IBR（M1–M3，100%）

| 里程碑 | 状态 | 证据 / 缺口 |
|---|---|---|
| RF ACE 与 L1 cache ACE 量化 | `done-local` | CHAOS/gem5/src/cpu/o3/rf_ace.*（整数 + 向量/FP 低 64 位）、mem/cache/l1_ace.*；test-rf/l1-ace.sh；19 模板覆盖矩阵 |
| FU IBR 输入位覆盖率 | `done-local` | CHAOS/gem5/src/cpu/o3/fu_ibr.*（intAlu/intMult/intDiv + fpAdd/fpMult/fpDiv）；test-fu-ibr.sh；19 模板覆盖矩阵 |
| AutoµSens 指令→结构映射与逆向靶向原型 | `done-local` | tools/autousens.py；scripts/test-autousens.py |
| 结构覆盖度评估工具 | `done-local` | tools/autousens.py evaluate + sdcfuzz/coverage.py；scripts/test-template-coverage.py；coverage_matrix.json |
| 本地 19 条结构语料（支撑件，非上游 19 模板） | `done-local` | sdcfuzz/templates.py；19/19 PASS；fp-add/fp-mul 已由 fpadd/fpmul IBR + 向量 ACE 测量；docs/sdcfuzz/phase0-baseline.md 明示非对等复刻 |
| 本地操作数启发式（非上游 D13，仅作可选对照） | `done-local` | sdcfuzz/operand_heuristic.py；tests/test_sdcfuzz_operand_heuristic.py（15 项单测） |
| 跨结构加权聚合靶向（归一化 + 贪心组合） | `done-local` | tools/autousens.py target --structure l1d,alu；scripts/test-autousens.py |
| NSGA-II 多目标序列集生成 | `done-local` | tools/nsga2.py（确定性 NSGA-II）+ tools/autousens.py pareto；scripts/test-autousens.py 真实 gem5 knee 验证 |
| SAD 结构激活深度指标 | `done-local` | CHAOS/gem5/src/cpu/o3/sad.*（ROB/IQ/LQ/SQ/intPrf/vecPrf/FU/issue）；scripts/test-sad.sh |

#### Phase 2 · RL Mutator + 功耗应力（M4–M6，10%）

| 里程碑 | 状态 | 证据 / 缺口 |
|---|---|---|
| 逻辑屏蔽惩罚（雪崩测试） | `partial` | D13 已用翻转密度/进位链近似屏蔽风险；雪崩测试未实现 |
| RL 训练管道 | `todo` |  |
| RL 引导的指令/操作数/序列变异 | `todo` |  |
| Type-I/II/III 功耗应力模式生成 | `todo` |  |
| 功耗-SDC 相关性（Pearson/Spearman） | `todo` |  |

#### Phase 3 · 仿真→硬件闭环（M7–M9，17%）

| 里程碑 | 状态 | 证据 / 缺口 |
|---|---|---|
| gem5 故障注入验证闭环（多注入器 × 语料） | `partial` | 19 注入器 + classify.py + 1 次闭环冒烟；语料级批量 campaign 未做 |
| Vault 持久库 + 血缘 | `todo` |  |
| 仿真预测与实机 SDC 的统计关联 | `todo` | 需实机数据；本机不可得（见 gated 项） |

#### Phase 4 · 自适应调度与集成（M10–M12，0%）

| 里程碑 | 状态 | 证据 / 缺口 |
|---|---|---|
| PMU 采集 + SDC 风险评分 | `todo` |  |
| 负载感知的自适应调度 | `todo` |  |
| 四层系统集成 | `todo` |  |

#### Phase 5 · 论文与投稿（M13–M15，0%）

| 里程碑 | 状态 | 证据 / 缺口 |
|---|---|---|
| 论文撰写（三项创新点） | `todo` |  |
| 投稿准备与提交 | `todo` |  |

### 仓库基线闸门（task_plan.md / AGENT_TASKS.md）

#### G0–G7 正确性闸门（2026-08，81%）

| 里程碑 | 状态 | 证据 / 缺口 |
|---|---|---|
| 可复现 RNG（20/20 重放一致） | `done-local` | commit 3b8c33c |
| 64 位掩码 / 合法域 | `done-local` | commit 54f31cd |
| 永久/间歇语义（stuck 掩码） | `done-local` | commit e5eecbb |
| cache 安全访问接口 | `done-local` | commit ea6b192 |
| CHAOSMem 权重与边界正确性 | `done-local` | commit 9870e9f |
| 单故障 + 证据日志（maxFaults） | `done-local` | commit d44982f |
| 触发间隔与多触发模式 | `partial` | ≥1 cycle 间隔已做；pc/committedInst/event 多触发未做（D9） |
| ASan/UBSan 工具构建 | `gated` | scons socket configure 受阻（D10）；解锁：CI 层修复 |

#### 注入器与 formal 实验（2026-09，67%）

| 里程碑 | 状态 | 证据 / 缺口 |
|---|---|---|
| 19 个 CHAOS 注入器 | `done-local` | AGENT_TASKS.md S1-* 全 done |
| n=384 批量 formal 实验（10 任务） | `done-local` | task_plan.md Phase 3（853133cb…） |
| S4/S6/S7/ExMon/Decode/O3-switch 登记 | `gated` | task_plan.md Phase 7（deferred，含解锁条件） |

## 维护方式

1. 修改 `docs/roadmap/roadmap.yaml`（状态取值见文件头注释）。
2. 重新生成：`python3 tools/render_roadmap.py`。
3. 需要 PNG 时：

```bash
inkscape docs/roadmap/roadmap.svg --export-type=png \
  --export-filename=docs/roadmap/roadmap.png
```
