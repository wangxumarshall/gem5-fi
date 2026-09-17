# Harpocrates 微架构覆盖指标复现：工程总结

> 本文总结 `feat/harp-coverage` 分支（2026-09-16/17，20 commit，`ce0767cb1..96e31e41e`）对
> Harpocrates 两篇论文（ISCA'24 [1] + IEEE Micro'26 [2]）SDC 检测用例覆盖指标的完整复现工程。
> 指标定义/公式/采集点索引/与论文差异表见 `docs/harpocrates/method.md`；
> 全部实验数据见 `docs/harpocrates/reproduction-report.md`；
> 实施计划（19 任务逐项验证记录）见 `docs/superpowers/plans/2026-09-16-harpocrates-coverage-reproduction.md`。
> 本文聚焦：系统结构、关键工程发现、与仓库既有 CHAOS 体系的关系、可复现入口。

[1] Karystinos et al., "Harpocrates: Breaking the Silence of CPU Faults through
    Hardware-in-the-Loop Program Generation", ISCA 2024.
[2] Karystinos et al., "Harpocrates++", IEEE Micro, Jan/Feb 2026.

## 0. 一句话概括

给定任意 AArch64 指令流序列，一次 gem5 仿真同时测出 **7 个微架构结构的硬件覆盖量化值**
（IRF/L1D/LSQ 的 ACE lifetime 分析 + IntAdd/IntMul/FPAdd/FPMul 的 IBR），并给出**证据驱动的
变异改进建议**；SFI 检测能力评估（Wilson 95% CI）闭环验证 coverage↑⇒detection↑——
建议驱动优化在 FU 目标上达到论文盲变异策略的 **18.8 倍**收敛效率。

## 1. 与仓库既有体系的关系

本工程不改动 CHAOS 的 19 个注入器语义，只做**叠加**：

```
                      ┌─────────────────────────────────────────────┐
   指令序列 (.S/ELF)  │  tools/harp_wrap.py                          │
   ─────────────────> │  确定性 wrapper：xorshift64 初始化 + m5ops    │
                      │  ROI 标记 + X9-X28 经 g_reg[] 内存进出 asm 块  │
                      └──────────────┬──────────────────────────────┘
                                     v  静态 aarch64 ELF
   ┌──────────────────────────────────────────────────────────────────┐
   │ CHAOSCov（新 SimObject，src/CHAOSCov/）                           │
   │  单次 --cov run 内测出全部覆盖指标：                               │
   │  ACE  ← regfile.hh / free_list.hh / commit.cc / base.cc /        │
   │         lsq_unit.cc 的守卫 hook（harp_enabled 全局开关）           │
   │  IBR  ← inst_queue.cc issue 点的 OpClass×源位宽计数               │
   └──────────────┬───────────────────────────────────────────────────┘
                  v
   ┌──────────────────────────┐    ┌────────────────────────────────┐
   │ harp_advice.py 规则引擎   │    │ harp_eval.py SFI 检测能力       │
   │ 覆盖证据→变异建议         │    │ 复用 CHAOSPhysReg/CHAOSCache/   │
   │ （超越点：advice-driven） │    │ CHAOSLSQFwd/CHAOSFPU + 新增     │
   └──────────────┬───────────┘    │ CHAOSFUPerm/CHAOSGateFU        │
                  v                └───────────────┬────────────────┘
   ┌────────────────────────────────────┐           v
   │ harp_report.py 端到端（最终交付）    │  coverage vs detection 并列
   └────────────────────────────────────┘  （论文 Fig.4 形态）
```

## 2. 指标实现要点（7 结构）

### 2.1 ACE lifetime（bit-array：IRF/L1D/LSQ）

论文 Fig.3 的区间语义适配到 gem5 O3：

| 结构 | 账本粒度 | 关键事件 | 实测对照 |
|------|----------|----------|----------|
| IRF | 三物理寄存器空间（int 125×64b / float 96×64b / vec 96×128b）独立区间 | write 开区间（setReg/getWritableReg）、read 延伸（getReg）、alloc/free 关闭（free_list） | readwrite 链 0.0891 > 死写链 0.0804 |
| L1D | 64B 块 | satisfyRequest 读 / updateBlockData+handleFill 写 / evictBlock 逐出 | mem 序列 0.00136 vs 无访存 0.00025（5.4×） |
| LSQ | SQ data 聚合 | insertStore 写入 / writebackStores 消费 / completeStore 释放 | store 序列 0.0170 vs 0.0141 |

IRF 双口径（超越点）：乐观（execute 时读即计）+ commit-confirmed（每条已提交指令的每个
物理源寄存器单独累计，squash 的读永不进入）。branchy 负载实测口径差 14.8%——
两口径是 execute 视角 vs 提交视角，**非上下界关系**（commit 读更晚，单值区间更长）。

### 2.2 IBR（4 FU 类）

分子 = issue 事件的源操作数有效位宽之和（Int/Float 64b、Vec 128b、VecElem 64b）；
分母 = 满宽（IntAdd/Mul 128b、FPAdd/Mul 256b=SSE-FP 对应 NEON）× TaiShan FU 实例数
（3/1/2/2）× T_ROI。实测 rand_fp 的 FPAdd 32768b/128 issue = 256b/issue 精确对上
2×128b NEON 全宽。

### 2.3 SFI 检测能力

detection = (SDC + Crash)/N + Wilson 95% CI，四类细分（比论文二分更细）。
注入协议：bit-array 用 transient 单 bit flip（位点×周期均匀随机）；FU 用 permanent
两级故障模型——L1 execution-level（CHAOSFUPerm：目标 OpClass 每次结果固定位 XOR）+
L2 合成门级网表（CHAOSGateFU：Kogge-Stone 加法器 1154 门 / 移位加乘法器 44418 门，
结构性差值注入，即同一输入过干净网与故障网取 XOR delta 应用到架构结果）。

## 3. 关键工程发现（全部实测定位，代码注释留档）

### 3.1 gem5 内部路径类

1. **AArch64 FP 结果绕过 `setRegOperand`**：FP/SIMD 寄存器写回走 vector regfile 的
   `getWritableReg` 可写指针路径与 blob 路径（`arch/arm/isa/operands.isa` 的
   `FpDest = VectorElem` 决定），挂在 RegVal 重载上匹配恒 0——CHAOSFPU 的
   `getRegOperand blob hook` 才是 FP 数据路径正确挂点。IRF 的 vec 空间采集同理。
2. **`instResult` 队列是 checker-only**：首版 FU 注入挂 iew.cc writebackInsts 对
   instResult 做 XOR，篡改 954649 次输出毫无变化——该队列受 RecordResult 旗标控制，
   O3 无 checker 时为空；真实写回路径是 `dyn_inst.hh setRegOperand → cpu->setReg`。
3. **ROI 门控的三段语法**：gem5 stats 的 `"memory"` clobber 必须在 extended asm 的
   第三冒号段（GCC 12 实测 T5/T10/T11 最小用例对照）；且单条 asm 最多 30 操作数，
   20 个 `"+r"` 输出超限——wrapper 改用"全局数组内存进出 + 寄存器全列 clobber"。
4. **m5ops 编码**：AArch64 m5op 的 func 字段在 bits 23:16（`0xff000110|(func<<16)`）；
   误放 bits 15:8 时 gem5 仍解码为 Gem5Op64 但 func 读出 0，静默 dispatch 成 M5OP_ARM，
   ROI 标记丢失且无任何告警。
5. **`preDumpStats()` 钩子**：roi=all/cycles 模式（无 m5ops 标记）下 stats 在
   workbegin/workend 永不触发，需 override `statistics::Group::preDumpStats` 在
   dump 前自动 finalize（Python 侧调 C++ 方法会 AttributeError——SimObject 不暴露
   任意方法）。

### 3.2 故障模型类

6. **permanent 故障必须 firstClock 门控**：从 cycle 0 起效的 FU permanent 会破坏
   C 库启动代码的地址计算（实测 cycle 7529 即 Page fault，远早于 ROI），须从
   ROI 起生效——这是对论文"整个程序期间 permanent"的窗口化偏差（method.md §四.6）。
7. **Kogge-Stone sum 位 bug**：`sum[i] = p0[i] XOR carry[i-1]` 的 p0 是预处理位而非
   最终前缀位——独立穷举测试（W=4/8/12，约 1700 万向量）捕获，gem5 全程序等值复验。
8. **网表哨兵冲突**：乘法器首版用 `-1` 哨兵表示"常数零位"，与 PI 负索引编码
   （`in0<0 → PI[-in-1]`）冲突使网表错值——改为常量门（`a0 AND NOT a0`）。
9. **ARM64 无 x86 MUL quirk**：Micro'26 论文的 int-mul 种子方差（~17%）源于 MUL 隐式
   写 RAX 被覆写掩蔽；ARM64 三操作数 MUL 无此机制，实验证实种子方差≈0——结构性差异，
   比论文更稳定（method.md 差异表预判，实验证实）。

### 3.3 工具链类

10. **ARM 汇编注释剥离**：`split("#")` 会把内存操作数 `[x8, #24]` 的立即数前缀当
    注释截断（盲变异第 7 步 gcc 报 invalid expression）——改为括号深度感知剥离。
11. **共享 m5out 的残档陷阱**：批量 run 复用同一 `-d` 目录时，失败的 run 读到上一
    负载的残档 stats（四组基线数值完全相同的假象）——每次独立目录 + rc 检查。
12. **ROI 口径一致性**：随机序列组误用 roi=all（整程序 1.38M 周期进 ROI，FP 占比
    稀释到 0）——wrapped 序列必须显式 roi=m5ops。

### 3.4 构建类

13. **内存约束**：本机 29GB/126 核，`-j126` 编译 OOM 被 kill——`-j16` 安全。
14. **namespace 嵌套**：`pseudo_inst.cc` 的 `namespace gem5{namespace pseudo_inst{...}}`
    内再开 `namespace gem5{}` 会解析成 `gem5::pseudo_inst::gem5::`（ld undefined）；
    `void ::gem5::f();` 限定声明 GCC 拒绝——正确形态是在外层 gem5 作用域声明。

## 4. 核心实验结论（数据见 reproduction-report.md）

| 论文主张 | 复现结果 |
|----------|----------|
| ACE 是 bit-array 检测上界（Fig.4） | ✓ 两负载实证：irfAvfInt=0.0891 ≥ detection=0.0400（N=50）；gap=software masking |
| coverage↑⇒detection↑（Fig.10 核心） | ✓ advice 曲线 0.115→1.089 单调饱和；同预算盲变异 0.115→0.058（**18.8×**） |
| FU permanent 检测 ~100%（Fig.11） | ✓ 位级 0.6333（饱和）；门级 numDiffs 262173/262189（99.99% 显形） |
| FP 平均检测低（§III-C） | ✓ CHAOSFPU N=20 全 Masked（FP 软件掩蔽真实测量） |
| 通用/随机负载结构覆盖分化（Fig.4） | ✓ 基线套件：int 组 ibrFpMul=0 / fp 组 ibrIntAdd≈0.001（mix 分化清晰） |
| 种子方差 <1%~17%（Micro'26 Fig.5） | 结构性差异：ARM64 方差 0（无 RAX quirk） |
| 0.1× 前缀保持检测（Micro'26 Fig.6） | ✓ 更强：1 条 mul × 200 iters 即 1.00 |

**如实记录的负/中性结果**：IRF 目标 12 步小预算下 advice≈blind（论文 IRF 需 ~5000
迭代；8 指令序列被 wrapper 每迭代 40 条 ldr/str 循环开销主导）；intmul permanent
SFI 下基线与 evolved 均 0.6333（注入饱和，不可区分——错误必破坏 wrapper 载入存回链）。

## 5. 工具清单与复现入口

| 工具 | 用途 | 典型命令 |
|------|------|----------|
| `tools/harp_wrap.py` | 序列→确定性 ELF（ROI 标记+签名） | `--seq x.S --out x --iters 200` |
| `tools/harp_eval.py` | SFI 检测能力（7 结构协议） | `--seq x --structure irf --n 50` |
| `tools/harp_advice.py` | 变异建议规则引擎 | `--seq x --top-k 6` |
| `tools/harp_evolve.py` | advice vs 盲变异对比 | `--seq x.S --target fu-intmul --steps 12` |
| `tools/harp_report.py` | **端到端单命令报告** | `--seq x.S --sfi 30` |
| `tools/harp_baselines.py` | 基线对比套件 | `--n-random 2` |
| `tools/harp_micro26.py` | Micro'26 两实验 | `--seq x.S --k-seeds 6 --n-sfi 8` |

复现口径注意：SFI 类实验含随机采样（detection 小数随 seed 波动，Wilson CI 为此设计）；
结构性结论（上界关系、正负对照、mix 分化、18.8×量级）在固定 seed 下确定性重现。
`artifacts/` 在 .gitignore（仓库惯例），克隆后须重跑生成。

## 6. 回归保证与遗留

所有采集器/注入器默认关闭（`harp_enabled`/`fu_perm_enabled`/`gatefu_enabled` 全局
守卫，未挂载时单分支零开销），默认路径 golden 输出与改动前逐字节一致
（`SUM=75555881316236 CRC=f1c0b5de`，每个 commit 的 message 引用真实验证输出）。

遗留（reproduction-report.md §七）：FP 门级网表（IEEE754 分解，现用 CHAOSFPU 位级）、
L1D byte 级（现块级）、SQ per-slot 精确账本（现聚合）、IRF advice 规则在大预算下的
收敛性、MiBench-arm 基线（现 directed 10 负载替代）。
