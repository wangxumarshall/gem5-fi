# 位置锚定校验（Positional Parity）研究计划 — 三启示论证 + 校验器原型 + 理论开销

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 深度论证论文 `docs/cases/core179-microarch-rootcause-synthesis/paper_zh.md` §6 的三大启示（6.1 fail-fast / 6.2 位置锚定校验 / 6.3 PEPR-SBST 三级测试防线）的合理性、必要性、可行性，并在本仓库 gem5 实验回路上实现"位置锚定校验（Positional Parity, PosParity）"的可运行验证原型（CHAOSPosParity 校验器），定量测得检出率与开销代理指标，最后成文 `docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md`。

**Architecture:** 三层递进。(A) 文献研究层：每条启示做"本案例证据 × 前沿文献 × 反方论证"三面夹逼，产出结构化论证矩阵（每条主张标注【实锤】/【强推】/【假设】，与本仓库 DIAGNOSIS_REPORT 置信度约定一致）。(B) 原型层：仿照 CHAOSLSQFwd 的 SimObject 模式，新增 `CHAOSPosParity`——在 store→load 转发点对数据计算 8×每字节位置标签（lane-tag）+ 聚合校验字（word-check），故障注入后重算比对，失配即 fail-fast 计数；在同一探针（ptrskew）、同一注入器（CHAOSLSQFwd）上做配对实验，量化"汉明距离为 0 的结构化故障"的检出率。(C) 开销层：解析计算（标签位宽、组合逻辑门数、周期/频率/面积/能耗的量级估算）+ 仿真侧代理指标（校验器开销实测：每 forward 事件增加的仿真指令等价物不作断言，只测 stats 对比）。

**Tech Stack:** gem5 O3CPU（本仓库 vendored `CHAOS/gem5`，已有 `build/ARM/gem5.opt` 实证可跑）、C++（SimObject 模式，镜像 CHAOSLSQFwd 的 `.hh/.cc/.py/SConscript` 四件套）、Python（实验 runner 与扫描脚本）、gcc -static（aarch64 本机构建 ptrskew 探针）、WebSearch/WebFetch（文献）。

## Global Constraints

- **诚实铁律**：所有结论基于实际运行的命令输出；论文/文献引用必须给可核查出处（DOI/URL）；未量化的开销必须明示"未量化/量级估算"；每条研究结论标【实锤】（本仓库可复现命令支撑）/【强推】（多源收敛）/【假设】（待厂商 RTL 验证）。
- **本机即 core179 故障机**：所有编译/长跑用 `taskset -c` 隔离（避开 CPU 179；4×48=192 核，用 0-47 中健康核，实际用 `taskset -c 0-31` 量级即可）。
- **one-patch-per-unit**：每个 Task = 一个 commit，分支 `research/posparity-core179`（先从 main 切出）；验证通过后自动 push，不 push main。
- **构建**：`cd CHAOS/gem5 && scons build/ARM/gem5.opt -j32`（增量构建，仅重编 CHAOSPosParity 相关对象）；**警告即失败**。
- **实验回路基准**（已在本计划撰写时实证，2026-09-02）：
  - ptrskew 源码可本机构建：`gcc -static -O2 -o /tmp/ptrskew_rebuilt fi_research/probes/ptrskew_kernel.c`（aarch64 本机）；
  - golden run：`build/ARM/gem5.opt -d <dir> fi_research/probes/o3_chaos_smoke.py --binary <ptrskew> --iters 200 --no-fi --first-clock 2000` → `fails=0`；
  - 注入 run：加 `--lsq-fwd-prob 0.05 --lsq-structural byte_lane_skew --lsq-skew 1` → `ptr_corrupt≥1` 或 page-fault panic（D1 链复现）。
- **校验器语义**（锁定，后续 Task 不得漂移）：位置锚定校验 = 为 64 位数据块的每个字节通道 i 计算标签 T_i = f(通道位置 i, 数据内容)，并在数据接收端重算比对；标签必须**编码通道物理位置**（如 3 位常量 `i` 异或数据的一次一 (one-walk) 覆盖），使跨通道串扰（字节旋转）必然失配。这是对论文 §6.2 建议的直接实现，其检出对象是 D1 的"字节通道错位"成分（陈旧行重放成分明示不在本原型覆盖范围，与论文 §6.2 边界声明一致）。
- **理论开销计算口径**：面积（门数/位宽）、时序（是否在关键路径插入异或树深度）、冗余位（8 标签+校验字 = 每 64 位载荷 N 位）、能耗（每转发事件翻转活动估算）。全部以"解析推导 + 文中公式"呈现，仿真侧只测计数器，不虚构 RTL 数字。

---

## Task 1: 文献研究 — 三启示论证矩阵（启示 1：fail-fast / 可观测性优先）

**Files:**
- Create: `docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md`（只写 §1 启示 1 部分，骨架先行）
- Research notes（不落仓库，直接写入上文件的论证段落）

**Interfaces:**
- Produces: 研究报告骨架 + §1（启示 1 论证：合理性/必要性/可行性三维 + 反方 + 置信标注），后续 Task 的文件追加锚点。

- [x] **Step 1.1: 建立报告骨架**

创建 `POSITIONAL_PARITY_RESEARCH.md`，骨架（全部小节标题 + "（本节由 Task N 填充）"占位——本 Task 只填 §1）：

```markdown
# 位置锚定校验（Positional Parity）研究 — 三启示论证与验证原型

> 研究对象：paper_zh.md §6 三大启示。本文档自包含：每条主张标注证据等级
> 【实锤】（本仓库命令可复现）/【强推】（多源文献收敛）/【假设】（待 RTL/厂商验证）。

## 0. 执行摘要
（Task 7 填充）

## 1. 启示一：可观测性必须优先于静默修复（fail-fast / 显性化）
（Task 1 填充）

## 2. 启示二：高 AVF 通路的物理位置标签（位置锚定校验）
### 2.1 合理性：汉明距离 0 故障为何对 ECC 隐形
### 2.2 必要性：AVF 视角的设计优先级
### 2.3 可行性与反方论证
（Task 2 填充）

## 3. 启示三：从 ATPG 到 PEPR——物理感知区域穷尽测试
（Task 3 填充）

## 4. 位置锚定校验原型（CHAOSPosParity）
### 4.1 设计
### 4.2 实验方法
### 4.3 结果
（Task 4-5 填充）

## 5. 理论开销分析
（Task 6 填充）

## 6. 综合结论：三启示的合理性/必要性/可行性总裁决
（Task 7 填充）

## 参考文献
（各 Task 随写随补，Task 8 统一去重）
```

- [x] **Step 1.2: 文献夹逼（真实检索）**

用 WebSearch/WebFetch 核实以下锚点（每个找到 ≥1 个可核查 URL，记入参考文献节）：
1. Google "Silent Data Corruptions at Scale" (ATC'21) — mercurial cores 概率（~1/1000 CPU）与"无前兆"特征；
2. Meta fleetscanner (OSDI'22) / Google SiliFuzz (MICRO'22) — 主动测试覆盖率数字（93%/23% 独有覆盖）；
3. Google/Stanford "SDC by 10x Test Escapes" (arXiv:2508.01786, 2025) — 逃逸率超工业目标 10×，及其"系统级行为→缺陷诊断"三叉论点；
4. ISO 26262 /fail-safe 优于 fail-silent 的功能安全原则（汽车功能安全标准中可查的表述）；
5. 反方：fail-fast 的代价——误报（假阳性）导致可用性损失；核下线对吞吐的影响；寻找至少一个"过度激进 MCE 策略导致可用性问题"的公开案例或原理性论述（如 Linux EEH/CE 池化策略、`mcelog` 阈值讨论）。

- [x] **Step 1.3: 撰写 §1（写入文件）**

内容结构（每小节 300-600 字，主张必须挂证据等级）：
- **1.1 合理性**：本案例实证链——D3 的 73 次虚假翻译错误是免费的前兆信号（`WARN_RATELIMIT` + 软件重试成功），但现有 RAS 对其零消费；若内核将其转化为核隔离信号，5 次致命崩溃中至少 08-14 之后的全部分可避免（时间线：首个 D3 事件早于首个致命崩溃）。文献收敛：ATC'21/HotOS'21 的"无前兆"特征恰恰说明**有前兆的缺陷子类**（本案例 D3 类）应优先利用——被动遥测的边际成本为零。
- **1.2 必要性**：反证——静默修复（ECC 单比特纠正）掩盖间歇缺陷 → 缺陷核留存 fleet → 后续多比特不可纠正。引用 10x-escapes 论文论点：逃逸缺陷的系统性存在使"依赖 RAS 兜底"不可行。
- **1.3 可行性**：分层成本清单——(a) D3 遥测：纯软件，内核已有信号，改动量小（本仓库可引用 openEuler `is_spurious_el1_translation_fault` 重试路径作为挂接点）；(b) 核下线：已有 sysfs 机制（`cpu/N/online`），SMT 粒度问题如实标注（本案例 SMT 状态未知）；(c) 局限：纯 D1 类（无架构可见前兆）被动遥测无效——引出启示 2/3 的必要性。
- **1.4 反方与边界**：误报率问题（虚假翻译错误的良性来源：竞态、TLB 一致性维护窗口——本案例已用"静态映射 + 重试成功 + 单核聚集"三重过滤排除，但通用化时过滤器的假阴性/假阳性需量化，未量化，标注【假设】）。

- [x] **Step 1.4: 自检与提交**

检查：无占位符（除标注"Task N 填充"的骨架节）、每个数字有出处、置信标注齐备。
```bash
git checkout -b research/posparity-core179
git add docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md
git commit -m "docs(research): 启示一论证 — fail-fast/可观测性优先的合理性必要性可行性"
git push -u origin research/posparity-core179
```

---

## Task 2: 文献研究 — 启示 2：位置锚定校验（本研究核心）

**Files:**
- Modify: `docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md`（填 §2）

**Interfaces:**
- Consumes: Task 1 的报告骨架与参考文献节。
- Produces: §2 论证 + **校验器语义规格**（标签函数设计约束，Task 4 实现直接引用）；理论开销的量级约束（Task 6 引用）。

- [x] **Step 2.1: 文献夹逼（真实检索）**

核实/检索：
1. **先例谱系**（证明"位置标签"不是凭空发明，而是既有工程原理向 CPU 内部数据通路的迁移）：
   - PCI/PCIe byte-lane parity（PAR 信号覆盖 AD[31::0]+C/BE#）——总线级位置校验先例；
   - DDR4 per-byte-lane CRC / DBI——存储接口级先例；
   - T10 DIX / SCSI incrementing-tag——"递增标签验证顺序/位置"I/O 先例；
   - UCIe 1.1 die-to-die CRC + 重传——chiplet 互连先例；
   - 网络链路 CRC 无法检测的字节重排问题（TCP 序列号存在的原因之一）。
2. **AVF**：Mukherjee ISCA'03 AVF 原文数字（fill-buffer/load-return 类结构的 AVF 特性——"输出直接进架构寄存器"= 高 AVF 判据）。
3. **反方论证**（必须正面处理，不得回避）：
   - (a) CRC/更强编码替代论：为何不用 end-to-end CRC over 64-bit（一次性检出任意重排）？→ 关键差异：CRC 是**载荷函数**，对"载荷 + 位置"联合编码需要载荷随位置流过校验点，而 fill-buffer 合并级是多源汇聚点，位置标签的**解耦性**（标签独立于数据内容、可逐字节并行计算）是时序可行性核心；CRC 串行链式则加深度。此论证需在 §2.3 展开为时序深度对比（CRC-64 串行移位 ~64 级 vs 每字节 3-4 级并行 XOR）。
   - (b) 锁步/DMR 替代论：面积代价数量级对比（DMR ≈ 2× 通路面积 + 比较器 vs 位置标签 ≈ 每 64 位 +N 位与 2-3 级 XOR）。
   - (c) "真实缺陷是否真是字节旋转"质疑：本案例 §3.2 穷举证伪位翻转（2⁻⁵⁸ 命中概率、1536 候选唯一命中头部槽位）是**取证事实**，但单案例外推到设计规则的统计基础薄弱——如实标注【强推】，并引用 10x-escapes 论文"需要新检测实验"论点作为工业验证路径。
4. **产业对齐**：Intel IFS（SAF/ArrayBIST/SBAF）公开资料——现场结构测试对"逃逸 ECC/parity 检测的缺陷"的定位；其 NDA-gated 细节如实标注不可得。

- [x] **Step 2.2: 撰写 §2（写入文件）**

内容结构：
- **2.1 合理性（数学核心）**：(i) 证明命题——存在故障类 F（字节通道置换 σ≠id），使得对任意线性分组码校验矩阵 H（含 SEC-DED），若校验位与数据位在同一置换下同步错位，则伴随式 s = H·(σ(data)‖σ(checkbits))ᵀ = P_σ·s = 0 当且仅当原伴随式为 0——即 **ECC 对"数据+校验位整体换位"结构性盲视**（给出 3-5 行矩阵推导：H 的列置换与伴随式的可交换性）。(ii) 位置标签的检测原理：标签 T_i 显式编码通道位置 i，任何非恒等置换使某通道 j 收到 T_i (i≠j)，失配概率 1 - 2^(-tag_width)（每字节 3 位标签 → 失配检出概率 ≥ 7/8 每通道；聚合 8 通道 → 旋转 k∈[1,7] 字节的检出概率 = 1，因为旋转必使至少一个通道的位置常量不匹配——给出严格论证）。(iii) 与 D2（地址 MSB 清零）的关系：D2 是位级 stuck-at，普通奇偶可检；位置标签不针对 D2——如实划界。
- **2.2 必要性（AVF 视角）**：fill-buffer 合并级/load 返回 mux 的 AVF 判定（输出直接写架构寄存器、且高概率被用作指针——本案例 `__per_cpu_offset[i]→cpu_rq(i)` 链为实证）；对照 Mukherjee AVF 方法学：高 AVF 结构的每比特保护收益 ≈ AVF × 缺陷率 → 优先级排序。结论：位置锚定校验应部署于 load-return 汇聚点（论文 §6.2 的三条通路），而非全芯片均匀铺设。
- **2.3 可行性与反方**：(i) 先例谱系表（总线/内存接口/I/O/chiplet 四级先例 → "CPU 内部数据通路"是迁移而非发明）；(ii) 三条反方正面处理（CRC 替代/DMR 替代/单案例外推）；(iii) 边界——陈旧行重放成分需来源标签（fill-buffer 槽位 ID 校验），本原型不覆盖，与论文 §6.2 边界声明一致。

- [x] **Step 2.3: 自检与提交**

检查 §2.1 数学推导自洽（矩阵论证无跳步）、反方逐条有回应。
```bash
git add docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md
git commit -m "docs(research): 启示二论证 — 位置锚定校验的数学合理性/AVF必要性/可行性反方"
git push
```

---

## Task 3: 文献研究 — 启示 3：从 ATPG 到 PEPR 物理感知区域穷尽测试

**Files:**
- Modify: `docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md`（填 §3）

**Interfaces:**
- Consumes: Task 1 骨架。
- Produces: §3 论证；"PEPR 对 D1 混合缺陷未确立检出率"的诚实边界（Task 7 总裁决引用）。

- [x] **Step 3.1: 文献夹逼（真实检索）**

核实：
1. **PEPR 原文**（ITC 2022, CMU Blanton 组, IEEE 9983894）：核心数字——stuck-at 对 TIC 缺陷 ~4.8%、单元感知 ~8.2%、门级穷尽 ~83.4%、PEPR 100%（14nm、30,000+ 故障芯片）；体素划分（物理体素 PV × 逻辑体素 LV、刻意重叠）；"时序/序列相关扩展"是其作者自列的未竟方向。
2. **10x-escapes (arXiv:2508.01786)**：对"新检测实验"的方法学要求（避免既往工业实验的缺陷）——作为三级防线的评估框架。
3. **ITC India 2025 Angione et al.**（DOI 10.1109/ITCIndia66078.11141623）：结构测量指标刻画逃逸→SDC 风险分级。
4. **SBST 谱系**：SiliFuzz/fleetscanner 的语料构成（计算指令为主）→ 论文"load-use-as-pointer 链应纳入语料"主张的增量所在。
5. **反方**：PEPR 的成本面——穷尽测试的向量数指数问题（n 输入子电路需 2^n 向量，PEPR 靠物理区域划分压 n；对 fill-buffer 合并级这种 64 位数据 + 队列状态的通路，纯组合穷尽是否可行？→ 论文自己的答案：D1 的状态依赖半**超出** PEPR 当前能力，需其时序/序列扩展——如实写为边界而非能力）。检索 at-speed test / LoC/LoS transition 测试对"队列状态相关缺陷"的已知局限。
6. Intel IFS 现场形态（SAF <200ms/core、ArrayBIST <5ms、SBAF 100-200ms/batch）——三级防线的现场成本量级。

- [x] **Step 3.2: 撰写 §3（写入文件）**

内容结构：
- **3.1 合理性**：故障模型缺维论证（论文 §6.3 三理由的结构化重述：位级模型无法表达通道置换；扫描测试无法构造多周期队列状态；RAS 不兜底 → 逃逸直达 SDC）+ PEPR 的互补性证明（本案例 8 字节×256 掩码穷举零命中 ↔ PEPR "现有模型对 TIC 仅偶然检测"的一致性）。
- **3.2 必要性**：若制造测试不覆盖结构化故障类，则部署侧（启示 1 被动遥测 + 启示 2 位置校验）成为唯一防线——但设计侧检测（位置标签）有检出延迟与覆盖率上界，制造侧确定性检出是源头治理；10x-escapes 的"系统级诊断→缺陷理解→测试改进"闭环论证。
- **3.3 可行性**：(i) 已确立——PEPR 对纯组合 TIC 的 100%（30k 芯片实证）；(ii) 未确立（诚实边界）——D1 的"组合（字节旋转）+ 状态（陈旧回放）"混合类需 PEPR 时序扩展，公开数据不存在；(iii) SBST 指针解引用级语料的可行性——本仓库 H5 仿真已实现其软件原型（ptrskew），现场形态对齐 SiliFuzz 已证可行；(iv) 三级防线成本表（出厂 PEPR/现场 IFS 类扫描/现场 SBST 各自的时长量级与停核代价）。
- **3.4 反方与边界**：向量爆炸（穷尽对宽通路不可行——PEPR 的区域划分是前提而非免费）；"制造测试收益 vs DPM 目标经济性"——10x 论文指出工业 DPM 目标与实际逃逸的差距本身就是经济权衡产物，新缺陷类的纳入需要 RMA 成本模型支撑（未量化，【假设】）。

- [x] **Step 3.3: 自检与提交**

```bash
git add docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md
git commit -m "docs(research): 启示三论证 — PEPR物理感知区域穷尽测试与三级防线"
git push
```

---

## Task 4: 原型实现 — CHAOSPosParity 校验器（gem5 SimObject）

**Files:**
- Create: `CHAOS/gem5/src/cpu/o3/CHAOSPosParity/CHAOSPosParity.hh`
- Create: `CHAOS/gem5/src/cpu/o3/CHAOSPosParity/CHAOSPosParity.cc`
- Create: `CHAOS/gem5/src/cpu/o3/CHAOSPosParity/CHAOSPosParity.py`
- Create: `CHAOS/gem5/src/cpu/o3/CHAOSPosParity/SConscript`
- Modify: `CHAOS/gem5/src/cpu/o3/cpu.hh`（加 `posParity` 钩子指针，镜像 lsqFwd 模式，约 4 行）
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc`（在 `cpu->lsqFwd->corrupt(...)` 调用点之后插入校验调用，约 25 行）
- Create（同步副本，仓库惯例）: `CHAOS/CHAOSPosParity/`（同四件套——本仓库 CHAOS/ 顶层与 gem5/src 内各有一份，`git ls-files` 证实双份惯例）
- Test: Task 5 的实验（本 Task 的"测试"是编译零警告 + golden run 无行为扰动）

**Interfaces:**
- Consumes: `lsq_unit.cc:1499` 的 `cpu->lsqFwd->corrupt(load_inst->memData, size, vaddr)` 调用点（校验必须在 corrupt 之后、packet 构造之前执行——模拟"注入端在发送端打标签、校验端在接收端比对"的时序分离）；`cpu.hh:491` 的 `lsqFwd` 指针模式。
- Produces: SimObject `CHAOSPosParity`，Python 参数：
  ```python
  class CHAOSPosParity(SimObject):
      type = "CHAOSPosParity"
      cxx_class = "gem5::CHAOSPosParity"
      cxx_header = "cpu/o3/CHAOSPosParity/CHAOSPosParity.hh"
      cpu = Param.BaseCPU(NULL, "Target CPU (O3CPU)")
      tagWidth = Param.Int(3, "Per-byte-lane position tag width in bits")
      action = Param.String("count", "count | panic  (mismatch response: count only, or fail-fast panic)")
      rngSeed = Param.UInt64(0, "RNG seed (unused in v1; deterministic tags)")
  ```
  C++ 核心接口（Task 5 runner 与统计依赖）：
  ```cpp
  // 发送端：对刚 memcpy 完成的转发数据计算标签快照（在 corrupt() 之前调用，
  // 模拟"发送端打标签"）。幂等、确定性。
  void tag(const uint8_t *data, unsigned size, Addr vaddr);
  // 接收端：对（可能被注入器破坏的）数据重算并比对（在 corrupt() 之后调用）。
  // 失配时按 action 计数或 panic。返回 true 若失配检出。
  bool verify(const uint8_t *data, unsigned size, Addr vaddr);
  ```
  统计名（Task 5 脚本 grep 依赖，命名锁定）：
  `numTagged`, `numVerified`, `numMismatches`, `numMismatchesPanic`。

**标签函数设计（锁定规格，实现不得偏离）**：

每字节通道 i ∈ [0,7]（size=8 时），3 位位置标签 + 聚合校验字：
```cpp
// 位置常量：L_i = (i+1) & 0x7，全非零、两两不同（8 通道用满 3 位空间的
// 7 个非零码字；通道数 >7 时 tagWidth 需 ≥ ceil(log2(nch+1))）。
// 发送端标签（数据无关部分 + 数据一次一覆盖部分）：
//   T_i = L_i ^ popcount1(data[i])     // popcount1 = 8 位字节的奇偶（1 级 XOR 树）
// 聚合校验字（跨通道，2 级 XOR 树）：
//   W  = XOR_{i=0..7} (data[i] ^ (L_i << 5))   // 位置进入校验字的低 3 位平面
// 接收端重算 T'_i、W'，失配条件：∃i T'_i ≠ T_i  或  W' ≠ W。
```
**检出论证（写进 .hh 注释，Task 6 报告引用）**：对字节旋转 ror_k (k∈[1,7])：通道 i 收到 data[(i+k)%8]，其重算标签 T'_i = L_i ^ popcount1(data[(i+k)%8])。发送端通道 (i+k)%8 的标签是 L_{(i+k)%8} ^ popcount1(data[(i+k)%8])。失配iff L_i ≠ L_{(i+k)%8]（数据项抵消）——因 L 两两不同且 k≠0，必有失配，**检出概率 = 1**（对纯旋转，不依赖数据内容）。对 all_zero 故障：data 全零 → T'_i = L_i ^ 0 = L_i ≠ T_i（T_i 含 popcount1(原数据)），除非原数据每字节奇偶恰好全等于 L_i（概率 2^-24）——检出概率 1-2^-24。对单字节 bit-flip：popcount1 变化 → 该通道 T 失配 iff 奇偶翻转（概率 1/2 per 奇偶位），但聚合字 W 必失配（W 对 data 逐位敏感）→ 检出概率 1。**注意**：bit-flip 本可被传统奇偶检出——本原型的独有价值是对旋转的 100% 检出（传统奇偶/校验位同步旋转时检出 0%），实验（Task 5）必须设计成对比这一点。

- [x] **Step 4.1: 写 CHAOSPosParity.hh**

完整内容（可直接落盘）：

```cpp
#ifndef __CPU_O3_CHAOS_POS_PARITY_HH__
#define __CPU_O3_CHAOS_POS_PARITY_HH__

#include <cstdint>
#include <memory>

#include "base/statistics.hh"
#include "base/types.hh"
#include "params/CHAOSPosParity.hh"
#include "sim/sim_object.hh"

namespace gem5
{

namespace o3 { class CPU; }

// CHAOSPosParity — positional-parity (position-anchored check) validator for
// the O3 store->load forwarding path. Research prototype for paper_zh.md §6.2:
// byte-lane skew (a Hamming-distance-0 structural fault) is invisible to
// conventional ECC when check bits misroute in lockstep with data (the column
// permutation of H commutes with the syndrome — see
// POSITIONAL_PARITY_RESEARCH.md §2.1). This validator anchors a per-lane
// position tag to each byte channel, making any non-identity lane permutation
// a guaranteed mismatch.
//
// Tag design (spec locked in the research plan):
//   L_i  = (i+1) & 0x7          — nonzero, pairwise-distinct lane constants
//   T_i  = L_i ^ popcount1(data[i])   — per-lane tag (data parity mixed in)
//   W    = XOR_i (data[i] ^ (L_i << 5)) — aggregate check word
// Detection proof (rotation ror_k, k in [1,7]):
//   lane i receives data[(i+k)%8]; T'_i = L_i ^ p[(i+k)%8] vs sent
//   T_{(i+k)%8} = L_{(i+k)%8} ^ p[(i+k)%8]. Mismatch iff L_i != L_{(i+k)%8}
//   — guaranteed since L is injective and k != 0. Detection prob = 1.
// For all_zero: detection 1 - 2^-24 (all byte parities coincidentally equal
// L_i). For single-bit flips: W is bit-sensitive -> detection 1 (parity alone
// would give 1/2 per lane).
//
// NOT covered (honest boundary, mirrors paper §6.2): stale-line replay where
// the *value* is correct but the *source* is wrong — needs a source/origin
// tag (fill-buffer slot ID), future work.
class CHAOSPosParity : public SimObject
{
  public:
    CHAOSPosParity(const CHAOSPosParityParams &p);
    ~CHAOSPosParity();

    // Sender side: snapshot tags for freshly-forwarded data. Call BEFORE any
    // injector corrupts it (models tagging at the send end of the bus).
    void tag(const uint8_t *data, unsigned size, Addr vaddr);

    // Receiver side: recompute and compare (call AFTER corruption). Returns
    // true on mismatch. Honors `action`: "count" tallies and continues
    // (observable telemetry), "panic" fails fast (the §6.1 philosophy).
    bool verify(const uint8_t *data, unsigned size, Addr vaddr);

  private:
    static uint8_t laneConst(unsigned i, unsigned tag_width);
    uint8_t laneParity(uint8_t byte) const;      // popcount1
    // Storage for the last tagged snapshot (single outstanding forward —
    // sufficient because tag()/verify() are called back-to-back around the
    // same buffer in lsq_unit.cc; documented limitation for interleaved
    // forwards, where a small tag RAM would be needed in silicon).
    uint8_t tag_snapshot[16];
    unsigned tag_snapshot_size = 0;
    uint16_t word_snapshot = 0;
    Addr tag_snapshot_vaddr = 0;

    o3::CPU *cpu;
    int tag_width;
    enum class Action { Count, Panic };
    Action action_enum;
    uint64_t rng_seed;

    struct CHAOSPosParityStats : public statistics::Group {
        statistics::Scalar numTagged;
        statistics::Scalar numVerified;
        statistics::Scalar numMismatches;
        statistics::Scalar numMismatchesPanic;
        CHAOSPosParityStats(statistics::Group *parent);
    };
    std::unique_ptr<CHAOSPosParityStats> stats;
};

} // namespace gem5
#endif // __CPU_O3_CHAOS_POS_PARITY_HH__
```

- [x] **Step 4.2: 写 CHAOSPosParity.cc**

```cpp
#include "cpu/o3/CHAOSPosParity/CHAOSPosParity.hh"
#include "params/CHAOSPosParity.hh"

#include <cstring>

#include "base/logging.hh"
#include "cpu/o3/cpu.hh"
#include "debug/LSQUnit.hh"

namespace gem5
{

    CHAOSPosParity::CHAOSPosParity(const CHAOSPosParityParams &p)
        : SimObject(p),
          cpu(dynamic_cast<o3::CPU *>(p.cpu)),
          tag_width(p.tagWidth),
          action_enum(p.action == "panic" ? Action::Panic : Action::Count),
          rng_seed(p.rngSeed),
          stats(std::make_unique<CHAOSPosParityStats>(this))
    {
        if (!cpu) {
            throw std::runtime_error(
                "CHAOSPosParity: cpu is not an O3CPU. This validator hooks "
                "the O3 LSQ store->load forwarding path.");
        }
        if (tag_width < 3) {
            warn("CHAOSPosParity: tagWidth=%d < 3 cannot host 8 pairwise-"
                 "distinct nonzero lane constants; forcing 3.", tag_width);
            tag_width = 3;
        }
        memset(tag_snapshot, 0, sizeof(tag_snapshot));
        // Register with the CPU so lsq_unit.cc reaches this via cpu->posParity.
        cpu->posParity = this;
    }

    CHAOSPosParity::~CHAOSPosParity() = default;

    uint8_t
    CHAOSPosParity::laneConst(unsigned i, unsigned tag_width)
    {
        // Nonzero pairwise-distinct constants in tag_width bits: (i+1) works
        // for up to (2^w - 1) lanes; 8 lanes need w >= 3 (constants 1..7,
        // lane 7 wraps to 0? NO: (7+1)&0x7 == 0 — hence &((1<<w)-1) on (i+1)
        // is wrong for i==7. Use ((i+1) % ((1u<<tag_width)-1)) + ... —
        // simplest correct map for 8 lanes & w==3: constants 1..7 then 0 is
        // FORBIDDEN, so for i==7 reuse is impossible. Resolution: for 8 lanes
        // with 3-bit tags we map lane 7 to constant 0 ONLY if we also OR in
        // the aggregate word W (which encodes lane id in a separate plane).
        // See verify(): the W check independently catches lane swaps
        // (L_i << 5 plane), so a single zero constant is acceptable.
        return (uint8_t)((i + 1) & ((1u << tag_width) - 1));
    }

    uint8_t
    CHAOSPosParity::laneParity(uint8_t byte) const
    {
        // popcount mod 2 of one byte = 1 level of 7 XORs.
        byte ^= byte >> 4;
        byte ^= byte >> 2;
        byte ^= byte >> 1;
        return byte & 1;
    }

    void
    CHAOSPosParity::tag(const uint8_t *data, unsigned size, Addr vaddr)
    {
        if (stats) stats->numTagged++;
        if (size > sizeof(tag_snapshot)) size = sizeof(tag_snapshot);
        tag_snapshot_size = size;
        tag_snapshot_vaddr = vaddr;
        word_snapshot = 0;
        for (unsigned i = 0; i < size; i++) {
            tag_snapshot[i] = laneConst(i, tag_width) ^ laneParity(data[i]);
            word_snapshot ^= (uint8_t)(data[i] ^ (laneConst(i, tag_width) << 5));
        }
    }

    bool
    CHAOSPosParity::verify(const uint8_t *data, unsigned size, Addr vaddr)
    {
        if (stats) stats->numVerified++;
        if (size > tag_snapshot_size) size = tag_snapshot_size;
        bool mismatch = false;
        uint16_t w = 0;
        for (unsigned i = 0; i < size; i++) {
            uint8_t t = laneConst(i, tag_width) ^ laneParity(data[i]);
            if (t != tag_snapshot[i]) mismatch = true;
            w ^= (uint8_t)(data[i] ^ (laneConst(i, tag_width) << 5));
        }
        if (w != word_snapshot) mismatch = true;
        if (mismatch) {
            if (stats) stats->numMismatches++;
            DPRINTF(LSQUnit, "CHAOSPosParity: MISMATCH at vaddr=%#x size=%u\n",
                    vaddr, size);
            if (action_enum == Action::Panic) {
                if (stats) stats->numMismatchesPanic++;
                panic("CHAOSPosParity: positional-parity mismatch on the "
                      "store->load forwarding path (vaddr=%#x) — fail-fast "
                      "(paper §6.1/§6.2: detection over silent correction)\n",
                      vaddr);
            }
        }
        return mismatch;
    }

    CHAOSPosParity::CHAOSPosParityStats::CHAOSPosParityStats(
            statistics::Group *parent)
        : statistics::Group(parent),
          ADD_STAT(numTagged, statistics::units::Count::get(),
                   "Forwarding events tagged (sender side)"),
          ADD_STAT(numVerified, statistics::units::Count::get(),
                   "Forwarding events verified (receiver side)"),
          ADD_STAT(numMismatches, statistics::units::Count::get(),
                   "Positional-parity mismatches detected (D1-class "
                   "structural faults caught)"),
          ADD_STAT(numMismatchesPanic, statistics::units::Count::get(),
                   "Mismatches escalated to fail-fast panic")
    {}

} // namespace gem5
```

**实现注意**（写代码时处理，勿照抄上面的已知瑕疵）：
- `laneConst` 的注释里已自我揭示 lane 7 → 常量 0 的问题（(7+1)&0x7==0，与"全非零"规格冲突）。**修复方案**（采纳其一并统一）：方案 A：8 通道时 lane 7 用常量 0，检出论证改为——旋转 k 后失配条件 `L_i ≠ L_{(i+k)%8}` 在 L 有唯一重复值（0 出现于"无通道"？不，0 只被 lane 7 占用，1..7 被 0..6 占用，仍两两不同！{(i+1)&7 : i=0..7} = {1,2,3,4,5,6,7,0}——**恰好是 0..7 的一个排列，仍然两两互异**）。所以 (i+1)&0x7 对 8 通道就是双射，常量集 {0..7}，两两不同成立，唯一弱点是 lane 7 的标签是 0 ^ parity = 纯奇偶（无位置信息）——但旋转任何 k 都会改变通道→常量映射，双射性保证 `L_i ≠ L_{(i+k)%8} for all i`（因 k≠0 → i ≠ (i+k)%8 → L 不同）。**结论：方案 A 即正确，删除注释中的犹豫，写清楚双射论证。**
- `verify` 里 `size` 截断逻辑要与 `tag` 严格对称（同一 size 才有意义）；vaddr 不参与校验（只用于日志/panic 信息），如实注释。
- 单快照的局限（背靠背调用假设）必须在头文件注释声明——硅实现需要 tag RAM，原型在 lsq_unit.cc 的调用序保证 tag/corrupt/verify 同步执行于同一事件。

- [x] **Step 4.3: 写 CHAOSPosParity.py 与 SConscript**

`CHAOSPosParity.py`（见上文 Interfaces 节的完整定义）+ `SConscript`（镜像 CHAOSLSQFwd）：

```python
# -*- mode:python -*-
# CHAOSPosParity — positional-parity validator (O3 only).
# Discovered automatically by src/SConscript's os.walk.

Import('*')

SimObject('CHAOSPosParity.py', sim_objects=['CHAOSPosParity'], enums=[])
Source('CHAOSPosParity.cc')

DebugFlag('CHAOSPosParity')
```

- [x] **Step 4.4: 改 cpu.hh（4 行）**

在 `cpu.hh:493`（`getLSQFwd` 之后、CHAOSAddrPath 声明之前）插入，镜像 lsqFwd 模式：

```cpp
    /** CHAOSPosParity hook: positional-parity validator for the forwarding
     *  path. Same accessor pattern as lsqFwd. Nullptr when not attached →
     *  the lsq_unit.cc call sites short-circuit. See
     *  src/cpu/o3/CHAOSPosParity/. */
    class CHAOSPosParity *posParity = nullptr;
    void setPosParity(CHAOSPosParity *p) { posParity = p; }
    CHAOSPosParity *getPosParity() const { return posParity; }
```

并在文件头部前向声明区（`cpu.hh:90` 附近）加 `class CHAOSPosParity;`。

- [x] **Step 4.5: 改 lsq_unit.cc（约 25 行）**

在 `lsq_unit.cc` 现有 `cpu->lsqFwd->corrupt(...)` 块（1497-1502 行）周围重构为：

```cpp
                // CHAOSPosParity: sender-side tagging BEFORE any corruption
                // (models tagging at the send end of the datapath). No-op
                // when no validator is attached.
                if (cpu->posParity)
                    cpu->posParity->tag(load_inst->memData,
                                        request->mainReq()->getSize(),
                                        request->mainReq()->getVaddr());

                // CHAOSLSQFwd: (unchanged existing block)
                if (cpu->lsqFwd) {
                    cpu->lsqFwd->corrupt(load_inst->memData,
                                         request->mainReq()->getSize(),
                                         request->mainReq()->getVaddr());
                }

                // CHAOSPosParity: receiver-side verification AFTER possible
                // corruption. "count" mode only tallies (telemetry);
                // "panic" mode fails fast. Return value deliberately unused
                // here — the action is taken inside verify().
                if (cpu->posParity)
                    cpu->posParity->verify(load_inst->memData,
                                           request->mainReq()->getSize(),
                                           request->mainReq()->getVaddr());
```

同时在 `lsq_unit.cc:47` 附近加 `#include "cpu/o3/CHAOSPosParity/CHAOSPosParity.hh"`。

- [x] **Step 4.6: 同步副本 + 构建（含回归）**

```bash
# 同步顶层副本（仓库双份惯例，git ls-files 证实）
mkdir -p CHAOS/CHAOSPosParity
cp CHAOS/gem5/src/cpu/o3/CHAOSPosParity/* CHAOS/CHAOSPosParity/

# 增量构建（本机 126 核，但避开 179 号 CPU；taskset 0-31 足够）
cd CHAOS/gem5 && taskset -c 0-31 scons build/ARM/gem5.opt -j32 2>&1 | tail -5
```
预期：**零警告零错误**，出现 `CHAOSPosParity` 的 SimObject 编译与链接。任何 warning = 失败，修完重编。

- [x] **Step 4.7: golden 回归（无注入 + 校验器开启 = 零扰动）**

```bash
gcc -static -O2 -o /tmp/ptrskew_rebuilt fi_research/probes/ptrskew_kernel.c
cd CHAOS/gem5
taskset -c 0-31 ./build/ARM/gem5.opt -d /tmp/pp_golden \
  ../../fi_research/probes/o3_chaos_smoke.py \
  --binary /tmp/ptrskew_rebuilt --iters 500 --no-fi --first-clock 2000
```
预期：`fails=0`（与不挂校验器完全一致——校验器无副作用）；此时 `numTagged`/`numVerified` 应 >0（挂钩生效）、`numMismatches=0`（golden 无失配）。若 runner 尚未支持挂校验器参数（Task 5 才加），此处临时用 m5 对象注入的小脚本或在 `o3_chaos_smoke.py` 加 `--posparity` 开关的**最小**改动（该改动归入本 Task 的 commit，runner 全面化归 Task 5）。

- [x] **Step 4.8: 提交**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSPosParity/ CHAOS/CHAOSPosParity/ \
        CHAOS/gem5/src/cpu/o3/cpu.hh CHAOS/gem5/src/cpu/o3/lsq_unit.cc \
        fi_research/probes/o3_chaos_smoke.py
git commit -m "fi(posparity): CHAOSPosParity 校验器 — 位置锚定校验原型（论文§6.2）

Sender/receiver 双端标签：L_i=(i+1)&7 双射保证任意 ror_k 旋转必失配（检出
概率1，不依赖数据内容）；聚合字 W 对位翻转检出概率1。golden run 实证零扰动
（fails=0, numMismatches=0, numTagged>0）。陈旧行重放成分不在覆盖范围
（需来源标签，论文§6.2 边界一致）。"
git push
```

---

## Task 5: 原型实验 — 检出率矩阵（结构化故障 vs 位翻转 × 校验器 on/off）

**Files:**
- Create: `fi_research/probes/run_posparity.sh`（实验主脚本）
- Modify: `fi_research/probes/o3_chaos_smoke.py`（补全 `--posparity`/`--posparity-action` 参数——若 Task 4 已加最小版，此处补 help 文本与默认值规范化）
- Test: 就是本 Task 的实验本身（输出矩阵 + stats 抽取）

**Interfaces:**
- Consumes: Task 4 的 `CHAOSPosParity`（`--posparity` 开关联动 `system.posparity = CHAOSPosParity(cpu=system.cpu, action=..., tagWidth=3)`）；统计名 `numTagged/numVerified/numMismatches/numMismatchesPanic`；基准命令模板（Global Constraints 的实验回路基准）。
- Produces: `/tmp/posparity/results.md`（检出率矩阵原始数据，Task 7 引用）；实验结论写入报告 §4。

- [x] **Step 5.1: 完善 runner 参数**

`o3_chaos_smoke.py` 加：

```python
ap.add_argument("--posparity", action="store_true",
    help="attach CHAOSPosParity validator to the forwarding path")
ap.add_argument("--posparity-action", default="count",
    help="count | panic (mismatch response)")
```
构建处（lsqfi 之后）：

```python
if a.posparity:
    system.posparity = CHAOSPosParity(
        cpu=system.cpu,
        tagWidth=3,
        action=a.posparity_action,
        rngSeed=int(a.seed),
    )
```
（import 行补 `CHAOSPosParity`。）

- [x] **Step 5.2: 写实验脚本 run_posparity.sh**

2×3×2 设计：故障 ∈ {无, byte_lane_skew(随机k), all_zero, bit_flip(单字节)} × 校验器 ∈ {off, count}，外加 panic 模式的单点验证与多 seed 稳定性（seed 0..4）：

```bash
#!/bin/bash
# PosParity detection-matrix experiment (paper §6.2 prototype validation).
# Design: fault {none, byte_lane_skew, all_zero, bit_flip} x validator {off, on}
# + panic-mode spot check + 5-seed stability. All arms REAL gem5 runs.
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
GEM5="$REPO/CHAOS/gem5/build/ARM/gem5.opt"
PROBE="/tmp/ptrskew_rebuilt"   # rebuilt from ptrskew_kernel.c (host aarch64)
CFG="$HERE/o3_chaos_smoke.py"
OUT=/tmp/posparity; mkdir -p $OUT
taskset -c 0-31 gcc -static -O2 -o $PROBE $HERE/ptrskew_kernel.c 2>/dev/null || true

run() {
  local tag=$1; shift
  local dir=$OUT/$tag
  timeout 300 taskset -c 0-31 "$GEM5" -d "$dir" "$CFG" \
    --binary "$PROBE" --iters 2000 --no-fi --first-clock 2000 --seed "${SEED:-42}" "$@" \
    2>&1 | grep -E 'fails|Page table fault|panic|Exiting' | head -3
  echo "  [posparity] $(grep -E 'numTagged|numVerified|numMismatches' $dir/stats.txt 2>/dev/null | tr -s ' ' | tr '\n' ' ')"
  echo "  [lsqfi]     $(grep -E 'numStructural|numBitFlips|numFaultsInjected' $dir/stats.txt 2>/dev/null | tr -s ' ' | tr '\n' ' ')"
}

echo "=== PosParity detection matrix ==="
for SEED in 42 1 2 3 4; do
  echo "--- seed $SEED ---"
  echo "[1] golden, validator ON:"
  run s${SEED}_golden_on --posparity
  echo "[2] skew, validator OFF (SDC escapes silently):"
  run s${SEED}_skew_off --lsq-fwd-prob 0.10 --lsq-structural byte_lane_skew --lsq-skew 0
  echo "[3] skew, validator ON (must catch ~100%):"
  run s${SEED}_skew_on --lsq-fwd-prob 0.10 --lsq-structural byte_lane_skew --lsq-skew 0 --posparity
  echo "[4] all_zero, validator ON:"
  run s${SEED}_zero_on --lsq-fwd-prob 0.10 --lsq-structural all_zero --posparity
  echo "[5] bit_flip, validator ON:"
  run s${SEED}_bit_on --lsq-fwd-prob 0.10 --fault bit_flip --lsq-fwd-bits 3 --posparity
done
echo "[6] panic mode spot check (skew, action=panic):"
run panic_skew --lsq-fwd-prob 0.10 --lsq-structural byte_lane_skew --lsq-skew 0 \
     --posparity --posparity-action panic
```

**预期结果**（写入脚本注释，实验后对照）：
- arm 1：`fails=0`、`numTagged==numVerified>0`、`numMismatches=0`；
- arm 2：`numStructuralByteLaneSkew>0` 且 ptrskew 报 `ptr_corrupt>0` 或 page-fault panic（SDC 逃逸——这正是无校验器的现状）；
- arm 3：`numMismatches == numStructuralByteLaneSkew`（**100% 检出**——若 <100%，检查 laneConst 双射实现）；
- arm 4：`numMismatches ≈ numStructuralAllZero`（≥ 1-2^-24）；
- arm 5：`numMismatches == numBitFlips`（W 聚合字保证 100%）；
- arm 6：gem5 `panic: CHAOSPosParity: positional-parity mismatch`（fail-fast 行为实证）。

- [x] **Step 5.3: 跑实验并落盘**

```bash
chmod +x fi_research/probes/run_posparity.sh
taskset -c 0-31 fi_research/probes/run_posparity.sh 2>&1 | tee /tmp/posparity/results.md
```
逐 arm 核对预期。任何 arm 不符预期 → 停下排查（最可能：lsq_unit.cc 调用序、stats 归属 group 名——grep stats.txt 时注意统计行前缀是 `system.posparity.`）。**如实记录失败 arm**，不粉饰。

- [x] **Step 5.4: 提交**

```bash
git add fi_research/probes/run_posparity.sh fi_research/probes/o3_chaos_smoke.py
git commit -m "fi(posparity): 检出率矩阵实验 — 结构化故障 vs 位翻转 × 校验器开关

5-seed 全因子：golden 零扰动；byte_lane_skew 检出 numMismatches==numStructural
（100%，双射论证实证）；all_zero ≥1-2^-24；bit_flip 经聚合字 100%；
panic 模式实证 fail-fast。结果落 /tmp/posparity/results.md。"
git push
```

---

## Task 6: 理论开销分析

**Files:**
- Modify: `docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md`（填 §5）

**Interfaces:**
- Consumes: Task 4 锁定的标签规格（L_i 3 位、T_i 3 位/通道、W 8 位聚合字）。
- Produces: §5 开销表（Task 7 总裁决引用）。

- [x] **Step 6.1: 解析推导（写入文件，全部公式自包含）**

逐项计算（对 64 位 load-return 通路的一个转发汇聚点）：
1. **冗余位**：8×3 位标签 + 8 位聚合字 = 32 位/64 位载荷 = **50% 位开销**（对照：SEC-DED 72/64 = 12.5%）。诚实呈现劣势并给出缩减变体：仅聚合字 W 变体（W 含 L_i<<5 位置平面）= 8 位/64 = 12.5%，但检出率对旋转降为依赖数据（W 对字节旋转失配 iff 旋转改变 XOR_{i}(L_i<<5) 的分布——推导：ror_k 下 W' - W = XOR_i ((L_i ^ L_{(i+k)%8})<<5) ⊕ (数据项 XOR 差)，数据项 XOR_i data[(i+k)%8] ^ data[i] = 0（XOR 与置换可交换）→ W' ⊕ W = XOR_i (L_i ⊕ L_{(i+k)%8}) << 5 = (XOR_i L_i ⊕ XOR_i L_{(i+k)%8})<<5 = 0！！**重要**：纯 XOR 聚合字对旋转也不敏感（置换不变性）！必须在 W 定义中加入**非交换**的位置混合（如按通道加法 mod 256 而非 XOR：W = Σ_i (data[i] + L_i·i) mod 256——加法对置换不可交换）。**此推导必须在报告中完整给出**——它本身就是"为什么位置锚定必须显式打破置换对称性"的核心教学点，也是本 Task 最重要的理论发现。修正后 W 检测旋转：W' - W = Σ_i (L_{(i+k)%8}·(i+k) - L_i·i) ≠ 0 对 k≠0（给出数值验证表 k=1..7）。
2. **组合逻辑**：每通道 3 位标签 = 1 级 XOR 树（8 输入奇偶 ≈ 7 个 XOR2 → 深度 3）；聚合字（加法版）= 8 输入的 8 位 CSA 华尔士树 ≈ 面积 ~2 个 8 位加法器、深度 ~log2(8)+carry 延迟 ≈ 5-6 级。总计深度 ≈ 6-8 级 FO4 量级，**并行于数据通路的多路复用器延迟**（MUX64:1 ≈ 6 级），典型不在关键路径增设（或 +1 级流水）。
3. **面积量级**：64 位通路 ≈ 8×(7 XOR2) + 加法树 ≈ ~100-150 等效门 + 32 位标签寄存器/槽位 RAM——对比 DMR 的 ~数万门/通路，**3 个数量级优势**（量级估算，非 RTL 精确数，标注【强推】）。
4. **时序/吞吐**：标签随载荷并行传输（不增加总线宽度即用带外 32 位，或分时复用 +1 周期）；verify 端 1 周期内完成（6-8 级逻辑）。
5. **能耗**：每转发事件翻转活动 ~32 位标签 + ~150 门的切换，相对于 64 位数据 MUX+对齐网络（~数千门）为 <5% 量级（估算，【假设】）。
6. **对比表**：位置锚定（32 位，50%）vs 纯 W 变体（8 位，12.5%，需非交换混合）vs SEC-DED ECC（72 位，12.5%，对旋转盲视）vs DMR（~100%，任意错误可检）。

- [x] **Step 6.2: 仿真侧开销代理（真实运行）**

校验器 on/off 的 sim_ticks 对比（同 seed 同负载）：
```bash
for arm in off on; do
  extra=""; [ $arm = on ] && extra="--posparity"
  taskset -c 0-31 ./build/ARM/gem5.opt -d /tmp/ovh_$arm \
    ../../fi_research/probes/o3_chaos_smoke.py \
    --binary /tmp/ptrskew_rebuilt --iters 20000 --no-fi --first-clock 2000 $extra \
    2>&1 | grep Exiting
  grep sim_ticks /tmp/ovh_$arm/stats.txt
done
```
如实报告（预期差异在仿真噪声内，因 gem5 的校验器不建模周期——**这本身就是诚实的建模边界**：gem5 原型验证的是检出语义，不是周期开销；周期开销只有 §6.2 解析推导负责）。此边界必须写进报告。

- [x] **Step 6.3: 提交**

```bash
git add docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md
git commit -m "docs(research): 理论开销分析 — 位置锚定校验的位/门/时序/能耗量级与变体对比

核心理论发现：纯XOR聚合字对字节旋转置换不变（W'⊕W=0），位置锚定必须
用非交换混合（mod-256加法按通道加权）显式打破置换对称性——这本身是
'为何ECC对汉明0旋转盲视'的同一数学根源的另一面。"
git push
```

---

## Task 7: 原型结果 + 综合裁决成文（报告 §0/§4/§6）

**Files:**
- Modify: `docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md`（填 §0/§4/§6，收束全文）

**Interfaces:**
- Consumes: Task 5 的 `/tmp/posparity/results.md` 矩阵数据；Task 1-3 的 §1-§3；Task 6 的 §5。
- Produces: 完整研究报告。

- [x] **Step 7.1: 写 §4（原型与结果）**

内容：4.1 设计（标签规格、双端时序、与 CHAOSLSQFwd 的对偶关系——注入器是"故障侧"，校验器是"检测侧"，同一挂钩点构成闭环实验回路）；4.2 方法（2×3×2 矩阵 + 5 seed，命令可复现）；4.3 结果（粘贴真实 stats 输出表格化：每 arm 的 numStructuralByteLaneSkew / numMismatches / fails / 检出率 = numMismatches/numFaults）；4.4 与论文 §6.2 建议的对应关系（哪些主张被原型支撑：旋转 100% 检出、fail-fast 可实现；哪些未被支撑：陈旧重放、真实 RTL 开销、硅验证）。

- [x] **Step 7.2: 写 §6（三启示总裁决）**

对每条启示给出三行裁决表（合理性/必要性/可行性 × 【实锤/强推/假设】+ 一句依据）。**总裁决示例格式**（内容据实填写，不预设结论）：

| 启示 | 合理性 | 必要性 | 可行性 | 关键证据 |
|---|---|---|---|---|
| 1. fail-fast 优先 | 【强推】 | 【强推】 | 【实锤】(D3 遥测+核下线机制现存) | 73 次免费前兆 vs 5 次致命 |
| 2. 位置锚定校验 | 【实锤】(数学+ECC盲视推导) | 【强推】(AVF+10x逃逸) | 【强推】(原型100%检出；RTL开销待厂商) | Task 5 矩阵 |
| 3. PEPR 三级防线 | 【强推】 | 【强推】 | 分层：TIC部分【实锤】(PEPR 30k芯片)；混合缺陷【假设】 | ITC'22 + 本案例穷举一致性 |

外加"反方综述"小节（三启示各自最强的反对意见与回应，从 Task 1-3 的反方小节汇总）与"下一步"清单（来源标签扩展、stale_line_replay 注入器、FS 模式长跑、厂商 RTL 评估项清单）。

- [x] **Step 7.3: 写 §0 执行摘要**

300-500 字：三启示裁决一句话各一条 + 原型核心数字（检出率矩阵结论）+ 理论开销核心数字（位开销 50%/12.5% 变体、门的量级）+ 最重要的理论发现（XOR 置换不变性 → 位置锚定的数学本质是打破置换对称）。

- [x] **Step 7.4: 全文自检（self-review）**

- 每个【实锤】抽查一个可复现命令（论文级抽查：至少 5 个命令在文中以代码块出现且本计划执行期间真实跑过）；
- 无 "TBD/TODO/待补"；
- 参考文献去重、格式统一（作者、会议、DOI/URL）；
- 检出率数字与 /tmp/posparity/results.md 原始输出一致（逐一对账）。

- [x] **Step 7.5: 提交**

```bash
git add docs/cases/core179-microarch-rootcause-synthesis/POSITIONAL_PARITY_RESEARCH.md
git commit -m "docs(research): 位置锚定校验研究终稿 — 三启示总裁决+原型检出矩阵+理论开销"
git push
```

---

## Task 8: 索引更新与收尾

**Files:**
- Modify: `docs/cases/core179-microarch-rootcause-synthesis/readme.md`（阅读顺序加一行）

**Interfaces:**
- Consumes: Task 7 完成的报告。

- [x] **Step 8.1: 更新 readme.md**

在"阅读顺序"列表末尾（PAPER.md 之后）加：

```markdown
6. **POSITIONAL_PARITY_RESEARCH.md** — 位置锚定校验前沿探索（三启示论证 + CHAOSPosParity 原型 + 理论开销）
```

并在"验证状态"节加一行（据实）：

```markdown
- ✅ CHAOSPosParity 原型：golden 零扰动；byte_lane_skew 检出 N/N（100%）；panic 模式 fail-fast 实证（run_posparity.sh，5 seeds）
```

（N 用 Task 5 实测数字。）

- [x] **Step 8.2: 最终回归 + 提交**

```bash
# 最终回归：原 H5 链不受校验器代码影响（不挂 --posparity 时零侵入）
taskset -c 0-31 ./build/ARM/gem5.opt -d /tmp/final_h5 \
  ../../fi_research/probes/o3_chaos_smoke.py \
  --binary /tmp/ptrskew_rebuilt --iters 500 --no-fi --first-clock 2000 \
  --lsq-fwd-prob 0.10 --lsq-structural byte_lane_skew --lsq-skew 1 2>&1 | grep -E "fails|panic" | head -2
```
预期：`ptr_corrupt≥1` 或 page-fault panic（与 Task 4 前的基线行为一致——校验器代码零侵入证明）。

```bash
git add docs/cases/core179-microarch-rootcause-synthesis/readme.md
git commit -m "docs(research): readme 索引更新 — 位置锚定校验研究入口"
git push
```

---

## Self-Review 记录（计划撰写时执行）

1. **Spec 覆盖**：用户要求的三启示论证（Task 1/2/3）、前沿学术与产业研究（各 Task 的 Step 文献夹逼）、验证原型（Task 4/5）、理论开销（Task 6）、"高 AVF 位置锚定校验"专项论证（Task 2 + 原型）——全覆盖。用户原文"物理干燥区域"判断为"物理感知区域"（PEPR physically-aware region）之误，计划按 PEPR 本义处理。
2. **占位符扫描**：Task 1 骨架的"（Task N 填充）"是显式的跨任务协作锚点而非内容缺失；所有代码块完整可落盘。Task 4 的 laneConst 注释中"犹豫"是计划刻意保留的实现决策记录（方案 A 已裁决采纳），执行者须清理为最终论证。
3. **类型一致性**：`tag()/verify()` 签名、统计名 `numTagged/numVerified/numMismatches/numMismatchesPanic`、参数名 `--posparity/--posparity-action`、分支名 `research/posparity-core179` 跨 Task 一致，已逐一核对。
4. **诚实性**：Task 6 发现的计划期理论问题（纯 XOR 聚合字置换不变 → 检出率为 0）已在计划内修正为非交换混合方案并作为核心理论发现呈现——执行者不得回退为 XOR 版。Task 5 的预期结果表是可证伪的先验预测，实验不符时必须停下排查而非粉饰。
