# Harpocrates 微架构覆盖指标 100% 复现与超越实施计划

> **For agentic workers:** 用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实施。所有步骤用 `- [ ]` checkbox 跟踪。
> **纪律（CLAUDE.md）**：一补丁一单元 → 真机三步自验证（干净构建 + 功能验证引用真实输出 + 不相关回归）→ commit（无 Co-Authored-By 尾注）→ push `feat/harp-coverage`。

**Goal:** 对任意给定的 AArch64 指令流序列，(1) 单次 gem5 仿真内测出 7 个微架构结构的硬件覆盖量化值（bit-array 结构用 ACE lifetime 分析、功能单元用 IBR，与雅典大学 Harpocrates（ISCA'24 + IEEE Micro'26）的指标定义、数据采集方式、评估与计算公式逐项对齐）；(2) 生成有证据、有预期收益的指令流变异改进建议；(3) 用 SFI 检测能力评估闭环验证 coverage↑⇒detection↑（论文核心主张），并复现论文的关键对照实验。可超越论文（结构面更宽、建议可解释、advice-driven vs 盲变异对比），不允许弱于论文（7 结构、2 覆盖指标、SFI 闭环、种子敏感性、子序列截断实验全覆盖）。

**Architecture:** 在 `CHAOS/gem5`（upstream v25.1.0.1+6，TaiShan v110 O3 SE 模型）内新增 `CHAOSCov` 分析 SimObject，按仓库既有 CHAOS hook 模式（regfile.hh 内联守卫 hook、SimObject robAccess 直访）在 regfile / classic cache / LSQ / issue 路径埋采集点，单次仿真输出 ACE/IBR；外层 Python 工具链（`tools/harp_*.py`）负责：指令序列包装编译（wrapper 生成器）、覆盖+SFI 一键评估、变异建议生成、论文对齐实验。SFI 复用现有 19 个 CHAOS 注入器与 campaign/runner Wilson CI 基础设施。

**Tech Stack:** C++（gem5 SimObject，SCons）、Python 3（工具链）、AArch64 原生 gcc（host 即 aarch64，`gcc -static -O2`）、gem5.opt（`CHAOS/gem5/build/ARM/gem5.opt`）。

**Spec:** 用户目标（2026-09-16）："深度理解两篇 Harpocrates 论文，研究 SDC 检测用例覆盖指标的定义、数据采集、评估和计算，结合本项目 gem5 源码，设计 100% 复现的方案。对于我给定的指令流序列，评估出该指令流序列的微架构覆盖量化值，并给出指令流变异的改进建议使得达成更好的微架构覆盖。可以超越雅典大学的方案，但不能比他们弱。"

---

## 一、论文指标 → 本仓库实现的精确映射（指标定义，100% 对齐）

### 1.1 两篇论文的指标定义（已深读，全文摘录见 `.planning/2026-09-16-harpocrates-coverage-reproduction/findings.md`）

| 指标 | 论文定义 | 适用结构 | 性质 |
|---|---|---|---|
| **ACE lifetime（=AVF）** | 对结构中每个 bit，ACE 周期数 / 程序总周期数，对全部 bits 汇总（0~100%）。ACE 区间 = write→read 与 read→read；un-ACE = read→evict、write→write（覆写未读）、fill 后未读即逐出 | bit-array：IRF、L1D、LSQ(SQ data) | transient 检测能力的**上界**（software masking 造成 gap） |
| **IBR（Input Bit Ratio）** | 程序执行中输入到单元的总有效 bit 数 / 理论最大输入 bit 数（假设每周期输入全饱和）。有效 = 单元实际被用的周期里实际传入的操作数位宽 | FU：IntAdd、IntMul、FP Add、FP Mul | 非上界，但与检测能力强相关；fast toggle-count-like 测量 |
| **检测能力（SFI）** | N 次注入中 n 次故障运行偏离 fault-free 运行（SDC+Crash+Detected 计为检出），detection = n/N | 全部 | 最终 golden 评估；注入协议：bit-array=transient 单 bit flip（bit、cycle 均匀随机），FU=permanent gate-level stuck-at |

### 1.2 本仓库 7 结构映射（ISA 换为 ARM64/鲲鹏920 TaiShan v110，方法 ISA-agnostic）

| # | 论文结构 | 本仓库对应 | 规模（two_level_taishan.py 实配） | SFI 注入器 |
|---|---|---|---|---|
| 1 | IRF | 整数物理寄存器堆 | 125 × 64b（numPhysIntRegs=125）| CHAOSPhysReg（phys 模式） |
| 2 | L1D | L1 数据缓存 | `smoke_test/configs/caches.py` L1DCache（任务 3.1 核实容量并设等大访问区域） | CHAOSCache（data 字段，transient） |
| 3 | LSQ | Store Queue data 字段 | SQEntries=47 | CHAOSLSQFwd + 新 SQ-data 注入点 |
| 4 | IntAdd | IntAlu ×3 | fu_pool.py FUDesc count=3 | CHAOSExec 扩展（见 §1.4） |
| 5 | IntMul | IntMult（opLat=3）×1 | 同上 | 同上 |
| 6 | FP Add（论文 SSE FP adder）| NEON/FP 加法（FloatAdd opLat=2、SimdFloatAdd，FPU×2） | 同上 | 同上 |
| 7 | FP Mul（论文 SSE FP mul）| FloatMult/MultAcc（opLat=4/5）、Simd 同类 | 同上 | 同上 |

### 1.3 覆盖计算公式（写入代码注释与 docs/harpocrates/method.md，逐条与论文对齐）

```
IRF AVF   = Σ_{r∈int phys regs} width(r) × ACE_cycles(r) / (Σ_r width(r) × T_ROI)
            ACE_cycles(r) = Σ 区间 [write(r), last_confirmed_read(r))，write 覆写未读区间计 0，
            free-list 驻留期计 0。squash 回退：读事件由 commit 确认（精确模式）或执行时即计（乐观模式），双模式都报告。
L1D AVF   = Σ_{b∈blocks, byte∈64} ACE_cycles(b,byte) / (numBytes × T_ROI)
            byte 级区间：read→(下一 write|evict) 为 ACE；fill/store 写入→read 之前 un-ACE；write→write un-ACE。
LSQ AVF   = Σ_{e∈SQ entries, slot} ACE_cycles(e,slot) / (numSlots × T_ROI)
            区间 = [store execute 写入 data, 写回内存/前转消费) ；squash 未写回计 0。
IBR(FU类) = Σ_{op→该类FU} effective_input_bits(op) / (full_input_width × T_ROI × 实例数)
            effective_input_bits(op) = Σ 源寄存器操作数位宽（Int 64b、FP 64b、NEON 128b）
            full_input_width：IntAdd=128b（2×64）、IntMul=128b、FP Add=256b（2×128 NEON lane 对）、FP Mul=256b。
            同时输出 per-instance 与 aggregate 两种口径（论文未明示实例数口径，我们双报，公式写死在文档）。
检测能力  = n/N，N 次均匀随机 (bit,cycle) 注入（bit-array）或随机 gate stuck-at（FU），Wilson 95% CI（复用 tools/campaign.py wilson()）。
```

T_ROI = 感兴趣区间周期数：由 workload wrapper 的 m5ops workbegin/workend 划定（任务 0.2 spike 验证；不可用则回退 `--roi-begin-cycle/--roi-end-cycle` 参数，默认 20%~80%，与 gem5_ace_scanner.py 现状一致并在报告中注明）。

### 1.4 诚实边界声明（gate-level 近似，写入文档，不允许隐瞒）

论文对 FU 用 **gate-level** stuck-at（GeFIN 的门级 FU 模型扩展）。gem5 无 RTL，本方案两层实现：
- **L1（任务 5.2）**：execution-level permanent stuck-at —— 目标 OpClass 的每次执行结果按固定 bit-mask 永久篡改（微架构级 permanent 代理）。
- **L2（任务 5.3/5.4）**：合成门级网表模型 —— IntAdd（64b Kogge-Stone）、IntMul（64×64 移位加法阵列/Wallace）、FP Add/Mul（IEEE double：对阶/尾码加或尾码乘[复用整数网表]/规格化，NEON 按 lane 分解），stuck-at 注入在网表节点上，结果回填写回路径。这是方法级 100% 对齐（论文自己声明"any fault model can be used"，指标定义/采集/计算不变）；gate 网表是合成模型而非真实 RTL，此差异在 docs/harpocrates/method.md 显式声明。

### 1.5 超越点（显式交付，证明不弱于论文）

1. 结构面更宽：分析器注册机制可插拔，首批 7 结构 + 框架（仓库 19 个注入器天然支持后续扩展：BPU/ROB/IQ/TLB…）。
2. 变异建议可解释：论文只有标量 fitness + 均匀随机指令替换；我们输出 per-structure 证据链建议（见 §四）。
3. advice-driven vs 盲变异收敛对比实验（任务 6.2）：同预算下建议驱动 ≥ 随机替换（论文策略），定量证明。
4. ACE 双模式（乐观/commit-confirmed）量化 wrong-path 读对 AVF 的影响（论文未报告）。
5. 检测能力评估带 Wilson CI 与六类细分（Benign/Masked/SDC/Crash/…，复用 classify.py），比论文二分更细。

---

## 二、File Structure

```
CHAOS/gem5/src/CHAOSCov/          # 新增：CHAOSCov.py / .hh / .cc / SConscript（SimObject，ROI 门控，stats）
CHAOS/gem5/src/cpu/o3/regfile.hh  # 修改：ACE 采集 hook（仿 read-trace 内联守卫模式）
CHAOS/gem5/src/cpu/o3/lsq_unit.{hh,cc}  # 修改：SQ data ACE + 注入点 hook
CHAOS/gem5/src/cpu/o3/inst_queue.cc     # 修改：issue 路径 IBR 采集 hook（getUnit 成功点 :924 附近）
CHAOS/gem5/src/mem/cache/{cache.cc,tags/*}  # 修改：L1D fill/read/write/evict hook（守卫指针，默认 null 零开销）
CHAOS/gem5/src/CHAOSExec/         # 修改：op-class 定向 permanent stuck-at 扩展
CHAOS/gem5/src/CHAOSGateFU/       # 新增：合成门级网表 FU 故障模型（L2）
smoke_test/configs/two_level_taishan.py  # 修改：--cov-* 默认关闭的挂载旗标（回归保证默认路径不变）
tools/harp_wrap.py                # 新增：指令序列 → wrapper（init/ROI marker/epilogue 签名）→ 原生静态 ELF
tools/harp_eval.py                # 新增：一键评估（覆盖 run + SFI campaign 并行 + Wilson CI 报告）
tools/harp_advice.py              # 新增：覆盖报告 → 排序变异建议（证据+预期收益+具体操作）
tools/harp_report.py              # 新增：单命令端到端报告（输入序列→量化值+建议 markdown）
workloads/harp/                   # 新增：生成的被测序列、基线（随机序列/MiBench-arm 子集/directed 现有）
artifacts/harp-*/                 # 新增：实验产物（cells.csv/summary.md，与现有 campaign 产物同构）
docs/harpocrates/method.md        # 新增：指标定义/采集点/公式/与论文差异表（含 1.4 诚实边界）
docs/harpocrates/reproduction-report.md  # 新增：复现实验结果（Fig.4/10/11 等价数据）
docs/superpowers/plans/2026-09-16-harpocrates-coverage-reproduction.md  # 本计划
```

---

## 三、任务分解（一任务一 commit）

### Phase 0 — 计划与 spike

- [x] **Task 0.1 提交本计划**（commit ce0767cb1）
  Files: `docs/superpowers/plans/2026-09-16-harpocrates-coverage-reproduction.md`
  验证：`git show --stat` 含本文件；分支 `feat/harp-coverage`（自 `fi-fuzz` 创建）。

- [x] **Task 0.2 Spike**（commit 5529350ea；实测 workbegin@tick16698220/workend@16700530，编码 func 必须 bits 23:16）
  写 20 行测试 workload（inline asm 发 aarch64 m5ops workbegin/workend magic instruction），在 gem5.opt 跑通并证明事件可见（Python 侧能捕获到 workbegin/workend 时点，或在 stats/trace 中可见）。结论二选一写回本计划 §1.3：m5ops ROI 或 cycle-param ROI。
  验证：真实 gem5 运行输出引用（事件时点 tick）。

### Phase 1 — 输入管线：指令序列 → 被测 ELF

- [x] **Task 1.1 harp_wrap.py**（commit 28996dd45；确定性 3 连跑一致 + gem5 同输出）
  接受三种输入：(a) 现成 aarch64 静态 ELF（直接用）；(b) `.S` 汇编片段；(c) 每行一条指令的文本序列。生成 wrapper C：寄存器/内存确定性初始化 + ROI 标记 + 核心序列（inline asm，volatile 保序）+ epilogue（全部 X/V 寄存器终态 + 内存区域 CRC 签名打印，即论文的 deterministic output：寄存器终态+内存签名），`gcc -static -O2` 原生编译。参照论文 §V-D 参数：线性单基本块、寄存器分配最大化依赖距离、内存操作数 round-robin 固定 stride（L1D 专用变体：32KB 区域 stride 8B）。
  验证：从 10 条样例序列生成 ELF；连续两次运行输出 SUM/CRC 完全一致（确定性）；`file` 确认 aarch64 static。

- [x] **Task 1.2 CHAOSCov 骨架**（commit 8d567fad9；ROI 钩子链实证 + 回归 golden 一致）
  Files: `CHAOS/gem5/src/CHAOSCov/*`、`two_level_taishan.py`（`--cov-*` 旗标，默认关闭）。
  内容：参数（target cpu/cache、roi 模式、输出文件）、ROI begin/end 状态机、gem5 stats 注册（各结构 AVF/IBR 占位）、detail dump OutputStream（仿 CHAOS writeLog 模式）。
  验证：(a) `scons build/ARM/gem5.opt` 零新警告；(b) 挂载后 baseline run 正常结束、stats.txt 出现 `harp.` 前缀占位项；(c) **回归**：不挂载时 `test_workload` baseline 输出 SUM/CRC 与改动前逐字节一致。

### Phase 2 — ACE：IRF（结构 1）

- [x] **Task 2.1 IRF ACE 乐观**（commit ccf2b4b3a；三空间 + getWritableReg 路径实测定位）
  Files: `regfile.hh`（write/read hook，仿 :247 read-trace 内联守卫）、`free_list.hh`（alloc/free 事件）、`CHAOSCov.cc`（区间状态机：write 开区间、read 延伸 last-read、free/覆写关闭）。
  验证：(a) `workloads/directed/reg_chain` 类负载跑出 AVF∈(0,1) 且数值合理（长活值多→高）；(b) 反例负载（快速覆写）AVF 显著更低；两例真实输出引用。

- [x] **Task 2.2 commit-confirmed**（commit a52a1ae15；branchy 双口径差 14.8%，preDumpStats 修复 roi=all）
  IEW squash 钩子回退未确认读；commit 确认。双模式 stats（`harp.irf.avf_opt` / `harp.irf.avf_commit`）。
  验证：分支密集负载上两模式差异非零且 commit 模式 ≤ 乐观模式（真实输出）；文档记录 wrong-path 差值。

### Phase 3 — ACE：L1D（结构 2）与 LSQ（结构 3）

- [x] **Task 3.1 L1D 块级 ACE**（commit 30634881a；byte→block 粒度近似已声明）
  先研读 CHAOSCache 挂载模式（`src/mem/cache/CHAOSCache/`）确定 hook 风格；在 classic cache 路径（access/fill/evict/writeback，含 packet 的 size+byte-enable mask）埋守卫 hook；per (set,way,byte) 区间；输出 AVF + set/way 驻留热图 dump 文件。
  验证：(a) 32KB 顺序 stride-8 读负载：AVF 应高（fill→read→read 模式）；(b) 纯流式写未读负载：AVF 低；真实数字引用；(c) 与 `gem5_ace_scanner.py` 的 L1D SFI diverge 率交叉校验同号（N≥100，Wilson CI 重叠或差值方向一致——ACE 是上界）。

- [x] **Task 3.2 LSQ SQ-data ACE**（commit d26f84afc；聚合账本）
  Files: `lsq_unit.{hh,cc}`（store execute 写入点、writeback-to-memory 消费点、squash 点）。
  验证：store 后立刻写回的负载 AVF 低；store→load 前转密集负载 AVF 高；两例真实输出。

### Phase 4 — IBR（结构 4-7）

- [x] **Task 4.1 IBR**（commit 3e527ad24；256b/issue 验证）
  Files: `inst_queue.cc`（:924 getUnit 成功点后按 OpClass 记 Σ 源操作数位宽）、`CHAOSCov`（per-FU 类计数器）。
  验证：构造已知混合序列（如恰好 1000 条 64b 加法）断言分子 = 1000×128b（报告数值精确对上）；per-instance 与 aggregate 双口径输出。

### Phase 5 — SFI 检测能力评估（golden 闭环）

- [x] **Task 5.1 harp_eval bit-array**（commit bb008b677；N=50 全流程 + 上界性质成立）
  IRF/L1D/LSQ transient 协议：N 次均匀随机 (bit,cycle)（复用 CHAOSPhysReg/CHAOSCache 定向参数 + 并行 N 进程；Wilson CI；六类分类复用 classify.py；与 1 次 coverage run 合并出报告：coverage vs detection 并列）。
  验证：小负载 N=50 全流程真实输出（含 CI）；ACE ≥ detection（上界性质成立，论文 Fig.4 同构结论）。

- [x] **Task 5.2 FU permanent L1**（commit 5cfd1bc06；负/正对照通过）
  Files: `CHAOSExec` 扩展：`--target-opclass` + permanent mask（对该 OpClass 每次执行结果永久篡改）。
  验证：负对照（未被用到的 OpClass mask → 全 Masked）；正对照（IntAlu mask → SUM 改变）真实输出。

- [x] **Task 5.3 门级网表**（commit 23199502e；1700 万向量穷举 + gem5 等值）
  Files: `CHAOS/gem5/src/CHAOSGateFU/`。64b Kogge-Stone 加法器与 64×64 移位加阵列乘法器的可注入网表（节点表 + stuck-at 求值器）；注入点：目标 FU 执行经网表求值。
  验证：无故障时网表输出 == 原执行结果（全对，逐条断言）；随机 20 个 gate stuck-at → 结果差异可复现（固定 seed 两次运行一致）。

- [x] **Task 5.4 FU 协议整合**（commit baed98edc；FP L2 按降级预案延后，CHAOSFPU 位级交付）
  IEEE double 对阶/尾码加/规格化（加法）、尾码乘（复用 5.3 整数网表）+ 阶码加（乘法）；NEON 按 lane 分解。整合进 `harp_eval.py`：FU permanent gate stuck-at 随机 gate 注入协议。
  验证：无故障等值断言；N=20 gate 注入真实运行输出 + detection 报告。

### Phase 6 — 变异建议引擎（用户目标 ②）

- [x] **Task 6.1 harp_advice**（commit 90611d2a8；对照负载建议互补验证）
  输入 coverage detail dump（per-reg 占用直方图、per-OpClass issue mix、L1D set/way 热图、LSQ 占用、FU per-unit IBR、ACE-detection gap），输出排序建议，每条含：结构、证据数字、具体变异操作（如"把序列中 SUB_X_X 出现的 34% 替换为 ADD_X_X 以提升 IntAlu IBR；预期 +X%[由 mix 缺口数据推出]"）、置信度。规则集按 §1.3 公式逆推（低 AVF→何种指令模式缺失）。
  验证：两个对照负载（无 FP 的 vs FP 密集的）建议列表显著不同且方向正确（真实输出引用）。

- [x] **Task 6.2 advice vs blind**（commit c9757c72a；FU 目标 18.8 倍）
  对 2 个结构（如 IntMul、L1D）：(a) 应用建议→重测覆盖，20 步迭代曲线单调上升（advice-driven）；(b) 同预算均匀随机指令替换（论文策略）对照曲线。产出对比图数据 CSV。
  验证：advice 曲线 ≥ 随机曲线（同迭代数覆盖值），真实数据落盘 `artifacts/harp-advice-vs-random/`；再各抽 1 点跑 SFI（N≥100）验证 coverage↑⇒detection↑。

### Phase 7 — 端到端与论文对齐实验

- [x] **Task 7.1 harp_report**（commit fb824cfa0；两份真实报告）
  `harp_report.py --seq <ELF|.S|文本> [--sfi N]` → markdown 报告：7 结构覆盖量化值表（含公式口径）、（可选）SFI detection+CI、变异建议 Top-K。这是用户目标的最终交付形态。
  验证：对 `smoke_test/sdc_probe/sdc_probe_workload_evolved` 与一个新生成序列各出一份真实报告。

- [x] **Task 7.2 基线对比**（commit c09c2acbf；Fig.4 同构 mix 分化）
  基线：(a) 随机序列生成器（论文 Generator 第 0 代，`harp_wrap.py --random`）；(b) MiBench-arm 子集（≥6 个，原生编译）；(c) 现有 `workloads/directed/*`（≥4 个）。每基线 × 7 结构：coverage（1 run）+ detection（N≥200）。
  验证：数据表落盘；结论与论文同构（通用负载 IRF 检测低、FU 高；我们的 evolved/建议序列显著优于随机基线）。

- [x] **Task 7.3 Micro'26 实验**（commit 57a88aeb0；结构性差异诚实记录）
  (a) 种子敏感性：最优序列 × 50 seeds（重采立即数+初值）→ 检测能力方差（论文：多数 <1%，int-mul 最大 ~17%）；(b) 子序列截断：0.01/0.1/0.25/0.5/1/2× 前缀重包装 → FU permanent 检测率曲线（论文：0.1× 即几乎不降）。
  验证：两组数据落盘 + 与论文量级对比陈述（ARM64 上数值不必逐点相等，趋势与量级对齐即方法复现成功；差异诚实讨论）。

- [x] **Task 7.4 文档**（commit a33e74a29；method.md + reproduction-report.md）
  `docs/harpocrates/method.md`（指标定义、采集点 file:line、公式、双口径、1.4 诚实边界、与论文逐项差异表）+ `reproduction-report.md`（7.2/7.3/6.2 数据与结论）。
  验证：文档内全部 file:line 用 `sed -n 'Np'` 抽查 100% 命中；无未经验证数字。

### Phase 8 — 收尾

- [x] **Task 8.1 回归收尾**（干净构建 0 错误；baseline/inject 全绿；19 commit push）
  (a) 干净重建零警告；(b) 默认路径回归：`two_level_taishan.py` 无 `--cov` 旗标跑 `test_workload` baseline 输出与 Phase 1 前基线一致；(c) 本计划所有 checkbox 勾选且每个已勾任务的验证输出可溯源；(d) push `feat/harp-coverage`。

---

## 四、变异建议规则集（Task 6.1 的设计基线，按 §1.3 公式逆推）

| 症状（coverage detail 证据） | 建议（具体到指令/操作数级） |
|---|---|
| IRF AVF 低 + 占用直方图集中在低水位 | 提高寄存器依赖距离/并发活值数：插入更多独立目的寄存器链，减少串行覆写（write→write un-ACE） |
| IRF AVF 低 + avf_opt 与 avf_commit 差大 | wrong-path 读多：降低序列分支密度，或让分支两侧都消费同一寄存器组 |
| L1D AVF 低 + fill→evict 未读占比高 | 增加对已 fill 块的重复读（读密集 stride-8 顺序扫 32KB），减少一次性流式写 |
| L1D AVF 低 + dirty 未回写占比高 | 增加 store→load 同址对（write→read 转 ACE） |
| LSQ AVF 低 | 增加 store→load 前转对与 store 在飞时间（execute→writeback 间隔拉长：store 后插长依赖链再触发写回） |
| IntAdd/IntMul IBR 低 | 指令 mix 缺口：把低价值指令（出现频率高但对目标 FU 无贡献者）替换为目标 OpClass；操作数用全宽 64b（W 寄存器 32b 只计 32b） |
| FP Add/Mul IBR 低 | 补 NEON 128b 全宽操作（论文：XMM 类似物访问指令少→检测方差大） |
| ACE 高但 SFI detection 低（gap 大） | software masking：epilogue 强化——把更多寄存器/内存并入输出签名（论文靠 generator 参数化最小化此 gap） |

每条建议的预期收益由 detail 数据边界推出（如 IBR mix 缺口的上界 = 替换全部低价值指令后的分子增量），报告中给区间而非点估计，置信度标注推导链长度。

---

## 五、运行预算与降级预案

- 单次 coverage run：5K-30K 指令 SE O3 仿真，秒-分钟级；SFI N=1000（headline）/200（对比实验）可并行（host 核数于 Task 0.2 一并记录 `nproc`）。
- 若 7.3 的 50 seeds × N 全量不可承受：N 降至 200（Wilson CI ±~7%），实验目标是与论文比较方差量级而非逐点，CI 内结论仍成立；在报告中写明实际 N。
- 若 m5ops ROI spike 失败：回退 cycle-param ROI（20-80%），报告口径注明。
- 若 FP 门级网表（5.4）超期：先交付 L1 execution-level（5.2 已覆盖 FU permanent 协议），L2 作为后续补丁继续，不阻塞 Phase 6/7——但 7.3(b) 截断实验用 L1 模型并在报告注明（论文用 gate-level）。

## 六、Errors Encountered

| Error | Attempt | Resolution |
|-------|---------|------------|
| （暂无） | | |
