# Phase 2 验收：RL Mutator + 功耗应力（2026-11-15）

本文逐条对照 `sdcfuzz/sdcfuzz-v1.2.md` §5.2（RL 引导的 SDC 定向变异）、
§5.3（功耗应力分类学与 SDC 相关性）与 §7 的 Phase 2 交付物，给出**本仓库
真实运行**的实现、测试、证据与边界。所有数字来自 `m5out/phase2-*` 与
`m5out/phase2-gate/`；一键闸门为 `scripts/test-phase2.sh`。

**一句话结论**：五个里程碑全部落地并通过闸门；逻辑屏蔽惩罚与 RL 管道是
可复用的主成果，功耗三模式与 McPAT 闭环可用；但 §5.3 的 H1–H3 在本次
FP 累加流上没有获得支持（详见 §5），RL 代理与真实 FI 的差距也已定位并
部分修正（详见 §3）。

---

## 0. 文档条款 → 实现 → 证据

| 条款 | 要求 | 实现 | 证据 |
|---|---|---|---|
| §5.2 状态 | 指令序列编码（Transformer）、覆盖向量（ACE/IBR/SAD）、功耗特征、逻辑屏蔽 | `sdcfuzz/rl.py`：1 层 2 头 Transformer（d=16）+ 9 维覆盖 + 4 维功耗 + 3 维屏蔽/长度/熵 = 32 维；覆盖对 19 个种子取 Phase 1 实测 ACE/IBR/SAD 矩阵，变异后回退静态映射 | `m5out/phase2-rl/policy.json`（state_dim=32）；`tests/test_sdcfuzz_rl.py` |
| §5.2 动作 | 指令替换、操作数变异、功耗应力注入、序列重组 | `Action(kind, position, param, donor)`；四类均在 200 轮训练中被采样 | `training.json.action_counts` |
| §5.2 奖励 | ΔSFI、Δ覆盖、Δ功耗、屏蔽惩罚、冗余惩罚 | `R = 2.0ΔSFI + 0.5ΔCov + 0.5ΔPower − 1.0·mask − 0.3·redundancy`；ΔSFI 用雪崩代理，最终用真实 FI 验证 | `sdcfuzz/rl.py`；`validation.json` |
| §5.2 目标 | RL 全流程变异，覆盖 FP/LSU | 200 轮 REINFORCE；FP 流已真实 FI 验证；LSU 受注入器限制未验证（见 §7） | `m5out/phase2-rl/*` |
| §5.3 Type-I | 持续高功耗 | `power.type1_continuous`：重复该结构最高功耗指令 | `m5out/phase2-power/streams.json` |
| §5.3 Type-II | 功耗跳变/振荡 | `power.type2_oscillation(period, duty)`：低功耗/高功耗交替 | 同上 |
| §5.3 Type-III | 单结构热点 | `power.type3_hotspot`：同一结构指令连续窗口 | 同上 |
| §5.3 McPAT | gem5 + McPAT + SDC，Pearson/Spearman | `power.mcpat_power` 调 `pypat`+McPAT（arm64-kunpeng920）；9/9 ok；`power_sdc.py` 计算相关与置换检验 | `power_measurements.json`、`correlation.json` |
| §5.3 H1–H3 | 高功耗→高 SDC；跳变>持续；定向>全局 | 三项均检验；H1 代理 peak 正相关但 McPAT 不相关；H2/H3 无差异（见 §5） | `correlation.md` |
| §7 Phase 2 | RL 训练管道 + 三类功耗模式生成工具 | `sdcfuzz/rl.py` + `sdcfuzz/power.py` + `sdcfuzz/phase2.py` CLI | `phase2_gate.json` |

---

## 1. 逻辑屏蔽惩罚（p2-mask）

### 1.1 方法

`sdcfuzz/avalanche.py` 在同一 AArch64 子集（`sdcfuzz.isa`）上做 1-bit
扰动，比较**被写输出字**（GPR/FPR/内存字）是否变化：

- **输入扰动模式**（默认）：setup 后翻转一个源寄存器的 1 位，跑完整个流；
- **瞬态模式**（`transient=True`）：在第 p 条 body 指令后翻转，让剩余指令
  传播，贴近 CHAOSFPU 的“源读处瞬态故障”；
- **稳态 pre-roll**（`pre_roll=100`）：先跑 100 次迭代到稳态，再翻转；
  避免 `fdiv` 下溢/`fmul` 上溢把初始扰动“吸收”成假阳性。

指标：`word_flip_ratio`（有输出字变化的试验比例）、
`avalanche_bit_ratio`（Hamming/64）、`masking_penalty = 1 − word_flip_ratio`、
`breadth`。惩罚只看架构输出字，不看 FNV 哈希，避免哈希雪崩把 1 位差异
放大成 32 位。

### 1.2 19 模板结果（iterations=40，bit 0–63）

| target | 模板数 | 平均 masking_penalty | 平均 word_flip_ratio |
|---|---:|---:|---:|
| alu | 6 | 0.205 | 0.795 |
| mult | 3 | 0.226 | 0.774 |
| div | 2 | 0.996 | 0.004 |
| l1d | 4 | 0.625 | 0.375 |
| l1i | 1 | 0.000 | 1.000 |
| fpadd | 1 | 0.078 | 0.922 |
| fpmul | 1 | 0.031 | 0.969 |

- 19 条中 **5 条 penalty > 0.5、11 条 < 0.5**，指标有区分度。
- 典型：`div32` 1.000、`l1d-load-hot` 1.000（load 覆盖目的寄存器）、
  `l1d-store-hot` 0.000（store 直接把源写入内存）、`dep-chain` 0.000、
  `fp-add` 0.078。
- 证据：`m5out/phase2-avalanche/avalanche.json`。
- 单测：`tests/test_sdcfuzz_avalanche.py`（7 项：AND 屏蔽、XOR 传播、
  死写、确定性、19 模板边界、store 输出、非法参数）。

**它回答什么**：这条流是否把输入扰动传到输出；**不回答**真实瞬态故障
在任意微架构位置的传播。后者由 §3 的真实 FI 验证补上。

---

## 2. RL 训练管道（p2-rl-pipeline）

### 2.1 状态、动作、奖励

- **状态（32 维）**：`TransformerEncoder`（1 层、2 头、d=16）对 body 的
  指令 token 编码（类别 one-hot 9 + popcount/进位链/宽度/访存/FP/功耗权重/
  位置/偏移 8，共 17 维 token 特征）→ 16 维；9 维覆盖向量；4 维功耗
  （average/peak/variance/slope）；3 维（masking、长度、类别熵）。
  - 覆盖向量的 19 个种子直接读 Phase 1 实测矩阵
    `m5out/phase1-gate-final/coverage/coverage_matrix.json`（ACE/IBR/SAD），
    变异后的流回退到静态指令→结构映射；这是“实测覆盖 + 代理覆盖”的混合，
    完整逐候选 gem5 覆盖测量列为后续工作。
- **动作（4 类）**：`replace`（同组指令替换，保持操作数）、`operand`
  （XOR mask/+1/ROL/取反，D13 风格）、`power`（插入 Type-II 片段）、
  `recombine`（与另一种子流交叉）。
- **奖励**：
  `R = 2.0·ΔSFI + 0.5·ΔCoverage + 0.5·ΔPower − 1.0·masking − 0.3·redundancy`。
  ΔSFI 用瞬态雪崩 + 稳态 pre-roll 的 `word_flip_ratio`；ΔCoverage 用 L1；
  ΔPower 用 `power.stress`；冗余用类别 Jaccard。
- **策略**：`Policy` 为 32×10 的线性 contextual bandit，REINFORCE +
  滑动基线；`updates=1200`。Transformer 编码器是固定种子权重的状态编码器，
  端到端训练 Transformer 属后续工作。

### 2.2 训练结果（200 轮，seed=20260825）

| 指标 | 值 |
|---|---:|
| episodes | 200 |
| steps/episode | 6 |
| policy updates | 1200 |
| trained mean reward | **−3.027** |
| random baseline mean reward | **−5.011** |
| trained best SFI proxy | 1.000 |
| 动作采样 | replace 738 / operand 365 / power 71 / recombine 26 |

- 训练曲线在 `m5out/phase2-rl/training.json`；策略在 `policy.json`；
  最优流在 `best_stream.json` / `best_fp_stream.json`。
- 200 轮内四类动作全部被采样；`replace` 占比最高，`power`/`recombine` 较低，
  与动作目录大小一致（replace/operand 目录更大）。
- 单测：`tests/test_sdcfuzz_rl.py`（6 项：编码器形状/确定性、四类动作、
  动作合法性、measure/state 有限、env 奖励项、策略更新、训练 smoke）。

---

## 3. RL 变异器与真实 FI 验证（p2-rl-mutator）

### 3.1 代理与真实的差距：一次可复现的修正

第一版 RL（输入扰动雪崩）选出的“最优 FP 流”是单条 `fdiv`：代理 SFI=1.0，
但 CHAOSFPU 真实注入只有 **1/20 SDC**（16 Masked，3 Hang），而手写
`fp-add` 基线是 **17/20**（Fisher p=4.1e-7）。原因是：

- 代理翻转 setup 后的初值，跑 160 次除法（d0≈1e-28），扰动可见；
- 真实 FI 在 1600 次除法后 d0 已下溢到 0，低 mantissa 的翻转被舍入/
  下溢吸收；`fmul` 上溢到 inf 同理。
- 代理被策略“钻空子”：选了在代理里可见、在真实稳态里被吸收的算子。

修正分两步：

1. **瞬态模式**：在第 p 条 body 指令后翻转，让剩余指令传播；
2. **稳态 pre-roll=100**：先跑到稳态再翻转，避免饱和/下溢吸收初值。

修正后重训 200 轮，最优 FP 流变为单条 **`fadd`**；真实 FI 为
**14/20 SDC**（6 Masked），对手写 `fp-add` 基线 **17/20**，
Fisher **p=0.451**、Δ=−0.15。即：修正后的 RL 流与手写基线**统计上不可区分**，
不再出现“代理 1.0、真实 1/20”的反向选择。

| 版本 | 代理 | 最优 FP 流 | 真实 SDC | 基线 SDC | Fisher p |
|---|---|---|---:|---:|---:|
| v1 输入扰动 | word_flip | `fdiv` | 1/20 | 17/20 | 4.1e-7 |
| v2 瞬态（无 pre-roll） | word_flip | `fdiv` | 1/20 | 17/20 | 4.1e-7 |
| v3 瞬态 + pre-roll=100 | word_flip | `fadd` | **14/20** | 17/20 | **0.451** |

这是 Phase 2 最重要的方法学结果：**代理必须建模稳态与瞬态位置，否则 RL
会优化到“代理可见、真实被吸收”的算子**。证据：
`m5out/phase2-rl/validation.json`、`best_fp_stream.json`。

### 3.2 McPAT 候选反馈

`python3 -m sdcfuzz.phase2 mcpat-select` 把 RL 最优 FP 流与 9 条功耗模式
一起按 `0.5·SDC_rate + 0.5·(McPAT_power/peak)` 排序，选中
`type2-fpmul`（SDC 0.85，McPAT 33.93 W，score 0.865），写入
`m5out/phase2-rl/mcpat_selection.json`。这是**候选级** McPAT 反馈：McPAT
结果参与“生成哪条流”的选择；逐步调用 McPAT 的实时闭环成本过高，列为
Phase 3（见 §7）。

---

## 4. Type-I/II/III 功耗模式与 McPAT（p2-power3）

### 4.1 三类模式

| 类型 | 生成器 | 结构 | 说明 |
|---|---|---|---|
| Type-I | `type1_continuous` | div/fpadd/fpmul | 重复该结构最高功耗指令 |
| Type-II | `type2_oscillation(period=8, duty=0.5)` | div/fpadd/fpmul | 低功耗 `mov` 与高功耗指令交替 |
| Type-III | `type3_hotspot(copies=32)` | fpadd/fpmul/l1d | 同一结构 32 条连续窗口 |

每条流都由 `sdcfuzz.generator` 渲染成自校验 guest，在 gem5 O3+kp920_proxy
下运行，再用 `pypat`（McPAT 2015 fork，`arm64-kunpeng920` 模板）取动态功耗。

### 4.2 实测（9/9 McPAT status=ok）

| 流 | 类型 | 结构 | proxy avg | proxy peak | proxy var | McPAT 动态功耗 (W) | SDC |
|---|---|---|---:|---:|---:|---:|---:|
| type1-udiv | I | div | 4.00 | 4.00 | 0.00 | 31.14 | — |
| type1-fpadd | I | fpadd | 1.00 | 1.00 | 0.00 | 34.33 | 15/20 |
| type1-fpmul | I | fpmul | 1.50 | 1.50 | 0.00 | 32.57 | 17/20 |
| type2-udiv | II | div | 2.10 | 4.00 | 3.61 | 31.43 | — |
| type2-fpadd | II | fpadd | 0.60 | 1.00 | 0.16 | 36.73 | 15/20 |
| type2-fpmul | II | fpmul | 0.85 | 1.50 | 0.42 | 33.93 | 17/20 |
| type3-fpadd | III | fpadd | 1.00 | 1.00 | 0.00 | 32.96 | 14/20 |
| type3-fpmul | III | fpmul | 1.50 | 1.50 | 0.00 | 32.18 | 17/20 |
| type3-l1d | III | l1d | 1.20 | 1.20 | 0.00 | 38.55 | — |

- McPAT 动态功耗范围 **31.14–38.55 W**，9/9 成功；`out.ptrace` 的 21 个
  部件列求和，`out.area` 同源。
- Type-II 的 McPAT 功耗高于同结构 Type-I（fpadd 36.73 vs 34.33；
  fpmul 33.93 vs 32.57），说明“跳变”确实改变了功耗轨迹。
- 证据：`m5out/phase2-power/{streams.json,power_measurements.json}`；
  源码 `m5out/phase2-power/src/*.c`。
- 单测：`tests/test_sdcfuzz_power.py`（6 项：Type-I 恒定、Type-II 方差/
  参数校验、Type-III 热点、9 流覆盖、generator 往返、McPAT 缺路径降级）。

---

## 5. 功耗-SDC 相关性（p2-power-corr）

### 5.1 数据

6 条 FP 流（type1/2/3 × fpadd/fpmul）× 20 次 CHAOSFPU 单比特瞬态注入，
`probability=0.001`、`max_faults=1`、`first_clock=1000`。全部 120 次有效
（无 Inactive/SimulatorError）。

### 5.2 H1：功耗越高 → SDC 越强

| 特征 | Pearson | Spearman | 置换 p |
|---|---:|---:|---:|
| proxy average | +0.554 | +0.397 | 0.281 |
| proxy peak | **+0.962** | +0.949 | 0.098 |
| proxy variance | +0.315 | +0.201 | 0.699 |
| proxy slope | 0.000 | 0.000 | 1.000 |
| proxy stress | +0.849 | +0.810 | 0.082 |
| **McPAT 动态功耗** | **−0.412** | **−0.494** | **0.461** |

- **代理 peak** 与 SDC 强正相关，但它是“FP 指令密度”的代理：峰值越高
  通常 FP 操作越密，累加器越活跃；这不是功耗因果。
- **McPAT 真实功耗与 SDC 负相关且不显著**（n=6，p=0.46）。H1 在物理功耗
  口径下**未获支持**。

### 5.3 H2 / H3

| 假设 | 配对 | 平均 Δ SDC | 正向配对 | 置换 p | Fisher p |
|---|---|---:|---:|---:|---:|
| H2：Type-II > Type-I | fpadd, fpmul | 0.000 | 0/2 | 1.000 | 1.000 |
| H3：Type-III > Type-I | fpadd, fpmul | +0.025 | 1/2 | 1.000 | 1.000 |

- H2/H3 均**未获支持**。原因有两层：
  1. **天花板效应**：6 条流的 SDC 已 0.70–0.85，FP 累加器始终活跃，
     功耗模式只改指令混合，不改“故障是否留在输出”；
  2. **gem5 没有功耗→时序耦合**：Type-II 的 di/dt 电压跌落无法在 O3 模型
     中变成时序违例；McPAT 只给功耗，不给“功耗导致错误”的通路。
- 因此本文把 H2/H3 记为“在 gem5+McPAT 观测层不成立”，而不是“物理上
  不成立”；真正的因果验证需要 RTL/硅片或带电压-时序模型的仿真器。

### 5.4 证据

- `m5out/phase2-power/correlation.json`、`correlation.md`；
- `m5out/phase2-power/fi_results.json`（6 流 × 20 次的分类）。

---

## 6. 闸门与证据

`bash scripts/test-phase2.sh` 依次执行 10 步，全部通过：

1. `unit-tests`：26 项 Phase 2 单测；
2. `avalanche`：19 模板 × 40 迭代；
3. `rl`：200 轮训练；
4. `rl-validate`：最优 FP 流 × 20 次 CHAOSFPU；
5. `power-gen`：9 条流源码；
6. `power-run`：9 次 gem5 + 9 次 McPAT；
7. `fi`：6 条 FP 流 × 20 次；
8. `mcpat-select`：候选级 McPAT 反馈；
9. `correlate`：Pearson/Spearman + H1–H3；
10. `audit`：`scripts/verify-phase2.py` 五里程碑审计。

证据：`m5out/phase2-gate/phase2_gate.json`（10/10 PASS）、
`phase2_milestones.json`（5/5 PASS）；归档副本在
`docs/sdcfuzz/phase2-evidence/`（见该目录 README）。

---

## 7. 诚实边界

1. **仿真，不是硅片**：gem5 O3 + `--kp920_proxy`，非 cycle-accurate；
   McPAT 是 2015 fork + ARM64 模板，绝对功耗只在同配置内可比。
2. **FP 数据通路为主**：整数/LSU 的寄存器注入在 O3 上被重命名旁路
   （Phase 2 之前已记录 12/12、8/8 Masked），所以 RL 的真实 FI 验证与
   功耗-SDC 相关性都聚焦 FP；LSU 的 §5.2 目标未完成，需新的源读/写回
   注入点。
3. **RL 策略是线性 contextual bandit**，Transformer 是固定编码器；端到端
   训练 Transformer、PPO/actor-critic 属后续工作。
4. **代理与真实 FI 仍有差距**：v3 的代理修正把“fdiv 反向选择”修掉，但
   RL 流只是与手写基线持平（14/20 vs 17/20，p=0.45），没有超越；真正的
   FI-in-the-loop 奖励是 Phase 3 输入。
5. **McPAT 是候选级反馈**，不是每个 RL 步骤的实时调用；逐步 McPAT 成本高，
   本文用 9 点校准/候选排序替代，完整实时闭环列为 Phase 3。
6. **H1–H3 的样本量小**（6 流 × 20 次），H1 的代理 peak p=0.098、McPAT
   p=0.461；H2/H3 为 null。结论是“在本仿真口径下未获支持”，不是“物理上
   不存在”。
7. **功耗模式只覆盖 div/fpadd/fpmul/l1d**；`type1-udiv`/`type2-udiv`/
   `type3-l1d` 没有 FP SDC 数据（注入器不适用），只参与 McPAT/代理对照。
8. **`fpmul` 的饱和问题**：默认 1.5×2.25 会溢出到 inf；Phase 2 的功耗流
   在 `power-gen` 里通过 `generator.render_guest(memory=...)` 把 d1 设为
   1+2⁻⁵²，避免饱和；`fp-mul` 模板本身的默认操作数仍是 1.5/2.25（Phase 1
   的结构探针语义不变）。

---

## 8. 复现

```bash
cd ~/sdc-mhw
bash scripts/test-phase2.sh                 # 全量（约 10 分钟）
EPISODES=120 FI_RUNS=12 JOBS=4 bash scripts/test-phase2.sh   # 快速
python3 scripts/verify-phase2.py             # 只跑审计
```

- 代码：`sdcfuzz/avalanche.py`、`sdcfuzz/power.py`、`sdcfuzz/rl.py`、
  `sdcfuzz/power_sdc.py`、`sdcfuzz/phase2.py`、`scripts/test-phase2.sh`、
  `scripts/verify-phase2.py`；测试 `tests/test_sdcfuzz_{avalanche,power,rl,power_sdc}.py`。
- 产物：`m5out/phase2-avalanche/`、`m5out/phase2-rl/`、`m5out/phase2-power/`、
  `m5out/phase2-gate/`；归档副本 `docs/sdcfuzz/phase2-evidence/`。
- 对 `sdcfuzz/isa.py`/`generator.py` 的唯一改动是新增可选 `memory=` 参数
  （默认行为不变，Phase 1 测试保持通过），用于非饱和 `fpmul` 功耗流。

---

## 9. 对 Phase 3 的输入

1. **FI-in-the-loop 奖励**：把 v3 的瞬态/稳态代理换成“候选流跑 N 次
   CHAOSFPU 的 SDC 率”，或学习一个从代理到真实 FI 的校准模型；当前 v3
   已证明代理必须建模稳态，下一步是把真实 FI 纳入训练。
2. **整数/LSU 源读注入器**：当前只有 CHAOSFPU 能稳定到达在飞值；整数
   通路需要类似 `CHAOSExec` 的“源读/写回结果”钩子，且不能挂死。
3. **逐候选 McPAT**：把 `pypat` 调用做成缓存/批处理，降低单次成本，
   支持每个 RL 候选的实时功耗反馈。
4. **功耗→时序模型**：H2/H3 需要电压跌落→时序违例的模型（或 RTL/硅片）；
   gem5 O3 本身不提供。
