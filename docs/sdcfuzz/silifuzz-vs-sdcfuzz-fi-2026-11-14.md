# sdcfuzz vs SiliFuzz：随机故障注入下的 SDC 发生率对照（2026-11-14）

本文把**当前 sdcfuzz 自动生成指令流的能力**与 **SiliFuzz（ifuzz + 固定语料）**
放在同一套 gem5-CHAOS 故障注入协议下做对照，检验一个可证伪的预期：

> 在等长、同 oracle、同注入器的仿真随机故障注入中，sdcfuzz 生成的指令流
> 应比 SiliFuzz 的随机指令流产生更高的 SDC 发生率。

结论：**在该协议覆盖的 FP 数据通路上，预期成立，且差异极大**——
sdcfuzz 6 条流 178/240 = **74.17%**（Wilson 95% CI 68.28–79.29%），
SiliFuzz 6 条流 0/240 = **0%**（95% CI 0–1.58%），Fisher 精确检验
**p = 3.8e-78**；流级 6/6 vs 0/6，p = 0.00216。

同时必须明确边界：这不是“全指令集”的结论。整数寄存器注入在 O3 上被
重命名旁路，当前 CHAOSReg / CHAOSPhysReg(arch_*) 在这两条流上 12/12 全部
Masked；只有 CHAOSFPU 的**源读钩子**能稳定到达在飞指令的值。因此本文测的是
**FP 数据通路的故障传播能力**，不是整数通路的胜负。

---

## 1. 一张表：两种“自动生成指令流”的能力面

| 维度 | sdcfuzz（当前主线） | SiliFuzz（本仓库复现） |
|---|---|---|
| 生成单元 | 19 条微架构模板 + `generator.py` 渲染为自校验 guest；`operand_heuristic.py` 自动选操作数 | `tools/ifuzzgen`（syzkaller arm64 ifuzz 模型）生成 1–24 条随机合法指令序列；`sf_fix` 在真机上执行、补页、记录端态 |
| 生成策略 | 结构定向：每条模板声明 target（alu/mult/div/l1d/l1i/fpadd/fpmul）与 CHAOS 注入器；AutoµSens 做指令→结构映射与逆向靶向；NSGA-II 做多目标序列集 | 覆盖率无关的随机合法序列；代理覆盖（Capstone 解码器、Unicorn 模拟器）只用于“生成更多路径”，不含微架构结构信息 |
| ISA 合法性 | 17 条已验证片段的组合，天然合法但表达力受限；**没有** Microprobe 式约束求解器（Phase 1 审计 PARTIAL） | ifuzz 模型生成 + `sf_fix` 硬件执行验证；非法编码会作为 SIGILL 端态被接受/修复 |
| 寄存器活跃性 | 模板把结果写回**同一个累加寄存器**，下一条指令读它：长 ACE、长依赖链 | 随机指令的目的寄存器大多被后续指令覆盖；每 3600 条指令对 31 个向量寄存器约 100 次写/寄存器 |
| Oracle | 自校验 checksum（FNV over GPR/FP/内存）；`tools/classify.py` 六分类 | 端态逐位比较：寄存器 + 页 FNV 校验和 + signal/addr；跨核/跨机差分 |
| 故障模型 | 19 个 CHAOS 注入器 + golden/faulty 差分；D13 操作数启发式 | **没有故障模型**；只检测已存在的硬件缺陷（合成注入只用于闭环验证） |
| 规模（本仓库证据） | 19 模板 × 9 结构；AutoµSens 8 个可靶向结构；NSGA-II Pareto 8–14；Phase 1 闸门 9/9 | 95,402 条基线语料 / 505,020 条规模语料；64,642,560 次 128 核 sweep；55 项测试；0 不匹配 |
| 优化目标 | 让故障**传播**到可观测输出（SDC 测试生成） | 让 CPU 的**端态偏离参考核**（缺陷检出），不优化单故障传播率 |

两者共享“生成 → 执行 → 反馈”的宏观思路，但测试单元、oracle、故障模型不同。
这也是为什么本文要做**统一 harness**：不统一就无法比较 SDC 率。

---

## 2. 实验设计

### 2.1 两条臂的流

**sdcfuzz 臂（6 条流）**

- `fp-add`、`fp-mul` 两条模板，各 3 组非饱和操作数：
  - fp-add: (1.5, 2.25)、(3.0, 1.25)、(0.1, 0.2)
  - fp-mul: (1.5, 1+2⁻⁵²)、(1.25, 1−2⁻⁵³)、(3.0, 1+2⁻⁵¹)
- 每条流 200 次迭代 × 16 次模板体 = **3200 条 FP 指令**，加循环开销
  共 3600 条指令；模板体由 `sdcfuzz/generator.py` 的同一渲染路径生成。
- fp-mul 的操作数刻意选在 1 附近：默认 1.5×2.25 在 200 次迭代后溢出到
  inf，任何位翻转都被“inf 吸收”，SDC 被系统性屏蔽（预试 0–1/10）。
  这是生成器的操作数选择问题，不是测量问题；正式实验用非饱和操作数。

**SiliFuzz 臂（6 条流）**

- 语料：`silifuzz/work/corpus/ifuzz` 的 95,402 条固定 snapshot。
- 每条 snapshot 取**实际执行前缀**：从 `pc` 到 `sig_addr`（端态信号地址）
  之间的指令；这正是 SiliFuzz 在真机上执行到 trap 的那一段。
- 过滤为**寄存器-only**：遇到第一条访存/分支/系统/PC 相对/保留寄存器
  （x28/sp）指令即停止；把各前缀拼接成 3600 条指令的直线块。
- 每块 2323–2350 条 FP/SIMD 指令（65% 左右），其余为整数/逻辑/空转。
- 这不是“逐条 snapshot 原生回放”，而是**流级**对照：保留 ifuzz 的指令
  分布，去掉无法在 gem5 SE 公共沙箱里安全执行的部分。

### 2.2 统一 harness（只让流不同）

两臂使用**同一个 guest 骨架**，只有中间的指令块不同：

- 2.25 MiB 沙箱映射在 `0x20000`；31 个 GPR 初始化为沙箱内指针，SP 指向
  沙箱栈；x27 固定为数据缓冲基址（模板的 `ldr/str` 用）。
- 指令块在 `m5_work_begin(7,0)` / `m5_work_end(7,0)` 之间执行；块后保存
  **x0–x30 + q0–q31 + 128 字数据**，用 FNV-1a 折叠成 16-hex checksum。
- 汇编入口保存/恢复全部 callee-saved 寄存器（x18–x30、SP、LR），避免
  ABI 污染 oracle——这是本轮调试中发现的第一个关键坑：早期版本没恢复
  x28/x19–x27，导致 C 侧读到错误地址、所有注入都“Masked”。
- 两臂都是 3600 条指令；oracle、沙箱、m5 窗口、gem5 配置完全相同。

### 2.3 故障模型

- **注入器**：`CHAOSFPU`，在每次 FP 源读按 Bernoulli(p) 注入一次瞬态
  bit flip；`p=0.001`、`max_faults=1`、`bit_segment=all`、`first_clock=1000`。
- 每条流 40 次，`rng_seed=10000..10039`；两臂共 480 次。
- 每次运行解析 `fpu_injections.log` 的 `Site:` 行确认恰好一次注入；
  无注入记 `Inactive` 并剔除（本轮 0 次）。
- 判据：程序正常结束且 checksum ≠ golden → **SDC**；checksum = golden →
  **Masked**；无 checksum → Hang/Crash/SimulatorError 单独计。
- 本轮 480/480 全部有效，无 Hang/Crash/SimulatorError/Inactive。

**为什么不用 CHAOSReg / CHAOSPhysReg 测整数？**
在本 harness 上做了对照：`alu-add-carry` 模板用 CHAOSReg（x8/x12 × 6 个
周期）和 CHAOSPhysReg（arch_frontend/arch_commit × x8/x12 × 6 个周期），
**12/12 全部 Masked**；snapshot 块用 CHAOSPhysReg(phys/arch_frontend) 8/8
Masked。原因是 O3 的重命名：arch_frontend 命中的是“最新一次重命名、尚未
写回”的目的物理寄存器，写回时把注入值覆盖；CHAOSReg 改的是已提交的架构
寄存器，在飞指令已经从重命名链读走旧值。**源读钩子**（CHAOSFPU）是当前
工具集中唯一能稳定把故障放进“被消费的值”的注入点。因此整数通路的对照
在本协议下**不可测**，本文不外推。

### 2.4 统计

- 聚合：Wilson 95% CI + 两臂 2×2 Fisher 精确检验（SDC vs 非 SDC）。
- 逐流：每流 40 次的 SDC 率与 Wilson CI。
- 流级保守检验：6 条 sdcfuzz 流 vs 6 条 SiliFuzz 流，按“流是否有 SDC”
  做 2×2 Fisher（6/6 vs 0/6），避免把同一条流的 40 次当成 40 个独立生成器。

---

## 3. 结果

### 3.1 汇总

| 组 | 有效注入 | SDC | Masked | SDC 率 | Wilson 95% CI |
|---|---:|---:|---:|---:|---|
| sdcfuzz | 240 | **178** | 62 | **0.7417** | [0.6828, 0.7929] |
| silifuzz | 240 | **0** | 240 | **0.0000** | [0.0000, 0.0158] |

- Fisher 精确检验 **p = 3.83e-78**；SDC 率比 → ∞（分母为 0，按 rule of 3
  给出 SiliFuzz 的 95% 上界 1.58%）。
- 流级 6/6 vs 0/6，Fisher **p = 0.00216**。

### 3.2 逐流

| 流 | 组 | FP 指令 | n | SDC | Masked | SDC 率 | Wilson 95% CI |
|---|---|---:|---:|---:|---:|---:|---|
| fp-add-v1 | sdcfuzz | 3200 | 40 | 28 | 12 | 0.700 | [0.546, 0.819] |
| fp-add-v2 | sdcfuzz | 3200 | 40 | 28 | 12 | 0.700 | [0.546, 0.819] |
| fp-add-v3 | sdcfuzz | 3200 | 40 | 26 | 14 | 0.650 | [0.495, 0.779] |
| fp-mul-v1 | sdcfuzz | 3200 | 40 | 32 | 8 | 0.800 | [0.652, 0.895] |
| fp-mul-v2 | sdcfuzz | 3200 | 40 | 32 | 8 | 0.800 | [0.652, 0.895] |
| fp-mul-v3 | sdcfuzz | 3200 | 40 | 32 | 8 | 0.800 | [0.652, 0.895] |
| snap-1 | silifuzz | 2323 | 40 | 0 | 40 | 0.000 | [0.000, 0.088] |
| snap-2 | silifuzz | 2349 | 40 | 0 | 40 | 0.000 | [0.000, 0.088] |
| snap-3 | silifuzz | 2349 | 40 | 0 | 40 | 0.000 | [0.000, 0.088] |
| snap-4 | silifuzz | 2330 | 40 | 0 | 40 | 0.000 | [0.000, 0.088] |
| snap-5 | silifuzz | 2350 | 40 | 0 | 40 | 0.000 | [0.000, 0.088] |
| snap-6 | silifuzz | 2336 | 40 | 0 | 40 | 0.000 | [0.000, 0.088] |

### 3.3 机制：不是“谁更随机”，而是“故障留在谁身上”

- **sdcfuzz 模板**：`fadd d0,d0,d1` / `fmul d0,d0,d1`，目的寄存器就是
  下一轮的源寄存器；d1 是常量，也从不被写。任一位翻转要么留在 d0 的
  累加链上，要么留在 d1 的不变值里，直到块结束；checksum 包含 q0–q3，
  所以必然 SDC。这是**长 ACE + 长依赖链**的直接结果。
- **SiliFuzz 随机流**：3600 条指令、31 个向量寄存器，平均每个寄存器被
  写约 100 次；一条指令的源被翻转后，它的结果通常在几十条指令内被同一
  寄存器的下一次写覆盖（dead write）。到块结束时，翻转值已经不在任何
  被 checksum 覆盖的寄存器里 → Masked。
- 换句话说：SiliFuzz 的随机流优化的是**解码/执行路径多样性**，不是
  单故障的**传播概率**；sdcfuzz 的模板则天然是“故障传播放大器”。两者
  的 SDC 率差异 74% vs 0% 是这一设计差异的直接体现，而不是随机种子
  或测量噪声（6 条流各自 40 次，全部同向）。

### 3.4 敏感性：不依赖调过的乘法算子

- 只用**默认操作数**的 `fp-add` 三条流（1.5/2.25、3.0/1.25、0.1/0.2）：
  82/120 = **68.3%**，仍与 SiliFuzz 的 0/240 形成同向差异；结论不依赖
  fp-mul 的 1±ε 选择。
- `fp-mul` 默认 1.5×2.25 在 200 次迭代后溢出到 inf，预试只有 0–1/10 SDC；
  这是**生成器操作数选择**的缺陷（饱和链把故障吸收掉），不是测量偏差。
  正式实验把它改成非饱和乘数后为 32/40；报告保留这一修正过程。
- 6 条 sdcfuzz 流全部 SDC > 0（26–32/40），6 条 SiliFuzz 流全部为 0；
  没有“某条流反向”的个例。

### 3.5 与既有 D13 结果的关系

`docs/sdcfuzz/d13-repro/summary.json` 的 D13 vs B 是**同骨架、只换操作数**
的对照（bit: 17% vs 6%，2.833×；struct: 64% vs 5%，12.8×）。本文是
**换指令流**的对照，注入器（CHAOSFPU）、oracle、流长都不同，不能把
74% vs 0% 与 17% vs 6% 相加或直接比较；两者回答的是不同问题。

---

## 4. 诚实边界

1. **仿真，不是硅片**：gem5 O3 + `--kp920_proxy`，非 cycle-accurate；
   绝对 SDC 率是模型条件概率，不是产品 FIT。
2. **FP 数据通路，不是全指令集**：整数寄存器注入在 O3 上被重命名旁路
   （12/12 Masked 对照），本文不声称 sdcfuzz 的整数模板优于 SiliFuzz 的
   整数流。要测整数通路，需要新的“源读/写回结果”注入点（如 CHAOSExec
   的可控版本），这是后续工作。
3. **SiliFuzz 臂是派生流**：取 snapshot 的执行前缀、过滤为寄存器-only、
   拼接成 3600 条；这不是逐条 snapshot 的原生 checker 回放。它保留了
   ifuzz 的指令分布，但改变了端态语义；结论只对“流级 SDC 传播”成立。
4. **sdcfuzz 臂是 2 条模板 × 3 组操作数**：6 条流不是 6 个独立生成器；
   运行级 Fisher 有聚类效应，因此同时给出更保守的流级 6/6 vs 0/6
   （p=0.00216）。
5. **fp-mul 操作数是刻意选的**：默认 1.5×2.25 会溢出到 inf，SDC 被
   “inf 吸收”；正式实验用 1±ε 的非饱和乘数。这是生成器的操作数选择，
   不是对 SiliFuzz 不公平——SiliFuzz 臂也使用同一 harness 与同一 oracle。
6. **无真机**：本机没有 4 板 446 核环境，也没有已知坏芯片；所有结论
   限于 gem5 模型。
7. **快照前缀过滤**：访存/分支/系统指令被剔除；每块 2323–2350/3600 条
   是 FP/SIMD，其余为整数/逻辑/空转。这个比例已在表中给出，读者可自行
   判断 FP 密度差异（3200/3600 vs 2323–2350/3600）。

---

## 5. 复现

```bash
cd ~/sdc-mhw
python3 fi_research/sdcfuzz_vs_silifuzz/fi_campaign.py --n 40 --jobs 8
```

- 脚本：`fi_research/sdcfuzz_vs_silifuzz/fi_campaign.py`
- 汇总：`m5out/silifuzz-vs-sdcfuzz-fi/summary.json`、`summary.md`
- 逐次证据：`m5out/silifuzz-vs-sdcfuzz-fi/runs/<stream>/rNNN/`
  （`gem5.log` + `fpu_injections.log`；stats/config 已清理）
- 归档汇总：`docs/sdcfuzz/silifuzz-vs-sdcfuzz-fi-summary.json`、
  `docs/sdcfuzz/silifuzz-vs-sdcfuzz-fi-summary.md`（与 m5out 同一份）
- 快照前缀缓存：`fi_research/sdcfuzz_vs_silifuzz/work/snapshot_prefixes.json`
- 环境：`sdc-0103`（aarch64，128 核，openEuler 24.03），
  `CHAOS/gem5/build/ARM/gem5.opt`（2026-11-10 构建），
  `configs/se/arm_chaos.py --cpu O3 --kp920_proxy`。

### 关键调试记录（可复现性的一部分）

- 早期 harness 没恢复 callee-saved 寄存器，C 侧 `g_out` 读到的地址被
  x28 污染，所有注入都显示 Masked；修复后同一模板的 `eor x8,#1` 正对照
  能把 checksum 从 `9c091a6a5e0a7535` 变为 `5ed713e214b243bb`，证明 GPR
  oracle 通路正确。Q 寄存器正对照：snap-1 块末尾插入 `movi v0.16b,#0xff`
  后 checksum 从 `18ecd7c0020a8086` 变为 `fbba5c7b911943a5`，证明 q0–q31
  确实参与 oracle。
- 注入日志样例（证明两臂的注入点同类，只是流不同）：
  - sdcfuzz fp-add：`Site: fp_source_read ... PhysReg[140] ... Old: 0x4002000000000000,
    New: 0x4002000000800000, Mask: 0x800000`（翻转常量 d1=2.25 的 bit 23）。
  - silifuzz snap-1：`Site: fp_source_read ... PhysReg[76] ... Old: 0x0,
    New: 0x800000, Mask: 0x800000`（翻转一个零值向量源，结果被后续写覆盖）。
- 早期用 CHAOSReg/CHAOSPhysReg(arch_frontend) 测整数模板，12/12 Masked；
  换 CHAOSFPU 源读钩子后 fp-add 立即出现 SDC。这不是 workload 的问题，
  是注入点能否到达在飞值的问题。
- raw ifuzz 的指令字约 13% 非法，22% 的序列含分支、16% 的序列含系统指令；在 gem5 SE 中
  会 panic 或页故障。最终采用 snapshot 的**执行前缀**（硬件已验证）而不是
  raw ifuzz 字节，避免把“生成器合法性”混进“故障传播”结论。

---

## 6. 附：能力对照的量化数字（摘自既有证据）

| 指标 | sdcfuzz | SiliFuzz |
|---|---|---|
| 结构模板 / 语料 | 19 条模板，9 类结构，8 类可逐指令靶向 | 95,402 条基线 / 505,020 条规模语料 |
| 生成/验证 | `generator.py` + `operand_heuristic.py`；Phase 1 闸门 9/9 | `ifuzzgen` + `sf_fix`（真机执行、补页、端态）；55 项测试 |
| 执行规模 | 19 模板 × 200 迭代；AutoµSens 16 探针 | 64,642,560 次 128 核 sweep；4 核/2 分钟 5,168,126 次 |
| 故障注入 | 19 个 CHAOS 注入器；D13 2.833×/12.800× | 无故障模型；合成注入 211,837/211,837 仅验证闭环 |
| Oracle | checksum + 六分类 | 跨核端态逐位比较（signal/addr/寄存器/页校验和） |

**一句话总结**：SiliFuzz 更擅长“用海量随机合法序列覆盖 CPU 行为空间”，
sdcfuzz 更擅长“把单个故障保持在活跃依赖链上并推到输出”；在本文的
FP 流、单比特源读注入、等长同 oracle 条件下，后者的 SDC 率是 74.17%，
前者是 0%，差异在统计上不可忽略，但只对 FP 数据通路成立。
