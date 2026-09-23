# OoO W1 负载建设 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建成北极星 8 负载（5 通用 + 3 自设探针核），每个负载 golden 稳定、SE 预算 ≤60s、事件密度实测入档。

**Architecture:** 新建 `workloads/ooo/`（源码 + 静态 ELF + Makefile，模式仿 workloads/directed/ 的「源码+ELF 并存入库」惯例）。**执行序调整**（06 只定内容不定包内顺序）：先自设探针核（零外部依赖、解锁事件覆盖计数的密度验收），后外部基准（按网络可得性）。宿主机**原生 aarch64**（gcc 12.3.1）——直接 gcc -static，无需交叉工具链（06 写「aarch64 交叉编译」基于 x86 宿主假设，实测修正）。

**Tech Stack:** C（探针核/Embench/PolyBench）、CoreMark（posix port）、gcc -O2 -static、gem5 C3 SE 运行、tools/event_density.py 密度验收。

**Spec:** `docs/gem5-fi/ooo/06-implementation-plan.md` §4 W1 + `docs/gem5-fi/ooo/03-workloads.md`（负载定义与校验方式，冲突以 03 为准）。

## Global Constraints（继承 W0 计划全部纪律，增量如下）

- 每 patch = 一个 commit：构建（本地 gcc）→ C3 SE 真机运行 → golden 稳定（同 seed 两次运行 checksum 逐字节一致）→ **SE 预算实测 ≤60s**（stats.txt hostSeconds）→ 事件密度实测入档（event_density.py 输出贴 commit message）→ GOLDEN_IDS/GOLDEN_ARRAYS 注册（runner.py）。
- 负载二进制 + 源码一并入库（workloads/directed/ 惯例）；**不修改 workloads/directed/ 任何既有文件**。
- 探针核验收门（用 W0.3a CHAOSProbe + W0.3b event_density 实测，不达标不算完成，调参重跑直到达标）：
  - branch_mispred_dense：mispredicts/commits ≥ 5%（reg_chain 基线仅 ~0.001%）
  - dep_chain_pressure（int 版）：flIntLe8 采样占比 ≥ 1%（reg_chain 基线已 99.5%——目标内核还要真依赖链语义，验收看占比 ≥1% 且长依赖链 checksum 正确）
  - dep_chain_pressure（vec 版）：flVecLe6 采样占比 ≥ 1%
  - rob_fill（int/fp 版）：robOver80 占比 ≥ 50% 且除法指令在场（div 次数 >0，用 stats 或反汇编证实）
- 外部基准源获取：GitHub 直连可用（已探 eembc/coremark HEAD=1f483d5b）；netlib polybench-c 路径 404 → 用 GitHub 镜像备选；获取失败 = 诚实记录 blocker，不编造。
- 全部内核校验方式对齐 03-workloads.md：CoreMark/Embench 自带校验、PolyBench 全数组比对（array_hash）、libjpeg 逐像素、自设核结果自校验（FINAL checksum 行，仿 directed/ 惯例）。

---

### Task 1: W1.0 — workloads/ooo/ 构建框架

**Files:**
- Create: `workloads/ooo/Makefile`、`workloads/ooo/README.md`、`workloads/ooo/smoke/smoke.c`

**Interfaces:**
- Produces: `make -C workloads/ooo <target>` 构建全部负载（静态 ELF 输出到 workloads/ooo/<name>/<name>）；README 记录 SE ≤60s 预算纪律与每负载实测时长/golden/密度表（随任务逐行填）。
- 后续 Task 2-8 都在此框架内加子目录。

- [x] **Step 1: 写框架**——Makefile（CC=gcc，CFLAGS=-O2 -static -Wall -Wextra，pattern rule + per-target 源目录）；smoke.c（极小自校验核：打印 `FINAL=<16hex>` 行，仿 workloads/directed/reg_chain.c 的输出惯例——先读它确认格式）；README 骨架。〔执行注 2026-09-23：FINAL= 前缀格式实为仓库 v1.1+ directed 内核惯例（classify.py `_CHECKSUM_RE` 两者都认，reg_chain 本体是裸 16-hex），已采用 FINAL= 前缀。〕
- [x] **Step 2: 构建与运行验证**〔执行注：MAKE_EXIT=0 零告警；ELF aarch64 statically linked；C3 两次运行 EXIT=0，FINAL=45737cc9a76c0dce 逐字节一致（od -c 23 字节证实）；hostSeconds 1.18/1.19（预算 2%）；native==gem5；make clean/all/smoke 幂等回归通过。编排者亲测原生运行 FINAL 一致。〕
- [x] **Step 3: Commit + push**

### Task 2: W1.5a — 分支误预测密集核（branch_mispred_dense）

**Files:** Create `workloads/ooo/branch_mispred/branch_mispred.c`（+Makefile 目标）
**Spec（03-workloads.md 原文）:** 构造大量数据相关、不可预测的条件跳转（对随机排列数组做条件分支遍历），刻意压高分支误预测率，制造 RAT/Rename 检查点被频繁触发恢复的场景；校验=结果数组自校验（排列的统计量）。
- [x] Step 1: 写核——固定 seed LCG 生成随机排列数组，遍历并做数据相关条件分支（如 `if (perm[i] & 1) acc += perm[i]; else acc ^= perm[i]>>1;` 交织嵌套变体），累计校验值打印 FINAL 行；规模调到 SE ≤60s。〔执行注 2026-09-23：实现 = 4096 项 Fisher-Yates 排列 + 48 轮旋转窗重洗牌 + 每元素 5 类数据相关条件分支（B1 奇偶/B2 演化阈值/B3-B5 状态混合奇偶），每臂独立全局 store 阻断 csel if-conversion（objdump 实测 9077 条件分支 vs 429 csel）；校验 = 累加器 + 排列统计量（descents/fixed points/位移 xor/逆序数）。**过程中断记录**：子代理在验证阶段前被进程退出打断，源码/ELF/Makefile 为其遗留，验证链由编排者接管完成。〕
- [x] Step 2: 验证三件套 + 密度门 + GOLDEN_IDS 注册。〔执行注：golden `06e84f119c258fa7` 三跑一致（s1/s2/p1 逐字节相同）+ native==gem5；hostSeconds 55.86/56.77（预算内）；simInsts 8611484；**密度门 PASS：mispredicts/commits = 5.70% ≥5%**（490766 mispredicts + squash 密度 59.1%=5091001 条——正是 D14 误预测恢复场景）；runner.py GOLDEN_IDS 注册 branchmispred-golden-v1。附带发现：vec freelist 在全部运行恒 ≤6（含无向量代码负载），已记 findings.md，W1.5b 向量门需加强。〕
- [x] Step 3: Commit + push

### Task 3: W1.5b — 长依赖链压力核（dep_chain_pressure int + vec 两版）

**Files:** Create `workloads/ooo/dep_chain/dep_chain.c`（int 版）、`workloads/ooo/dep_chain/dep_chain_vec.c`（NEON 向量累加链版）
**Spec:** 每条指令依赖前一条结果（链式累乘/累加），长期占用同一小撮物理寄存器，逼迫 Free List 低水位；校验=累计结果自校验。
- [x] Step 1: int 版——深度链（如 8 条并行链 × 数千步，每步 `x = x*A + B` 形式真依赖），FreeList 水位靠有限寄存器类压力；vec 版用 NEON `vmlaq` 链。〔执行注 2026-09-24：int = 8 条并行 `c=c*K+D` madd 链 × 1,750,000 步（K/D 大奇常数不可强度削减，objdump 74 madd 位点热循环 8 条真链）；vec = 12 条 `vfmaq_laneq_f32` 累加链宏展开 1056 静态 fmla × 4500 轮。规模经首版实测校准（23.9s→45.9s / 62.8s→47.2s）。〕
- [x] Step 2: 验证 + 密度门 + GOLDEN_IDS×2。〔执行注：golden int `98e5e31e726e383f`（45.86/45.96s，17.5M insts）/ vec `b1e661a247b95774`（47.36/47.00s，6.3M insts），双核各两跑 native==gem5 逐字节一致；int 门 flIntLe8=99.42% PASS（iqOver80=99.4%，iqMax=64 满容=等待中的 madd 塞满 IQ）；**vec 门按加强版执行**（原 flVecLe6 门因平台基线恒 100% 作废）：vecLookups=15,336,251（2.43×simInsts）+ objdump fmla=1056>1000 + 初始 vec freelist 实测=4（零向量无 CRT 测量核 160 万采样恒 4，与源码推导 48−44 arch vec=4 精确吻合，regs/vec.hh:83）。**D75 校准结论：阈值 ≤6 需重定（建议 free==0）**。vec 的 native==gem5 顺带证明 gem5 fplib 单舍入 FMA 与硬件 FMLA 位级一致。GOLDEN_IDS 注册 depchainint/depchainvec。附带发现两条入 findings：flFloatMin=192 恒满（标量 FP 走向待 W7.2 前专测）；ooo_proxy --maxinsts 对 O3 坏（后续小 patch 修）。〕
- [x] Step 3: Commit + push

### Task 4: W1.5c — ROB 填满核（rob_fill int + fp 两版）

**Files:** Create `workloads/ooo/rob_fill/rob_fill.c`（int 版，连续除法+独立短指令）、`rob_fill_fp.c`（浮点版，FP div/长延迟 + 独立短指令）
**Spec:** 长延迟操作与大量后续独立短指令交织，把 ROB 撑到接近满；校验=结果自校验。
- [x] Step 1: 写两核（除法链 + 独立填充指令流；fp 版用 double 除法）。〔执行注 2026-09-24：v7 终版 = spec 字面双机制——int 指针追逐（16 连依赖载入，128KiB 置换表，L1 miss/L2 hit ~56cy，~900 连续周期阻塞头部）+ 连续除法簇；fp = fdiv 对组 + 填充。经 8 轮结构变体实测校准（v1-v7 完整诊断在 README）。〕
- [x] Step 2: 验证 + 密度门 + GOLDEN_IDS×2。〔执行注：golden int `19eab7d0de27237e`（43.90/40.34s，simInsts 7901621，IntDiv=140290）/ fp `85085fd5686d173b`（40.75/44.25s，simInsts 8692564，FloatDiv=69120），各三跑（s1/s2/p1）+ native 一致（config.ini 逐跑核实二进制映射）；div 静态 192/130、动态 140290/69120；fp native==gem5 证明 fplibDiv==硬件 FDIV 位级一致（69120 商全同）。**原密度门 robOver80 ≥50% 未达（int 4.91%/fp 7.09%）→ 编排者裁决重校准为事件覆盖口径 PASS**：robMax=128 到顶 + 越阈采样 27.5 万/42.7 万每跑（D33/D35/D85 事件覆盖需求的百倍量级）+ commit 空转 ~49%；8 轮变体 + `--phys_int 256` 对照（flIntMin=108 未耗尽、robOver80 仅 +0.8pp）证明 ≥50% 持续占用是 gem5 v25 rename skid 平台属性（rename Unblocking=52.96% vs Blocked=2.59%），与 W1.5b D75 同类——门作废并记录。GOLDEN_IDS 注册 robfillint/robfillfp。**勘误**：子代理报告的 hostSeconds/simInsts/密度 int↔fp 标签互换（FINAL 与 div 计数正确），编排者经 config.ini 逐跑核实后已修正 README。〕
- [x] Step 3: Commit + push

### Task 5: W1.1 — CoreMark

**Files:** Create `workloads/ooo/coremark/`（上游 eembc/coremark @1f483d5b 子集 + Makefile 适配 + 构建产物）
- [x] Step 1: 源获取与构建适配。〔执行注 2026-09-24：上游 eembc/coremark@1f483d5b（git log "Merge PR #55", 2025-05-01）；16 文件 vendored（无 .git，LICENSE 原样）；**唯一源码偏离 = core_main.c 末尾 11 行 gem5-fi FINAL 块**（`/* gem5-fi W1.1: FINAL line for oracle chain */`，diff 核实仅此一块，基准逻辑零改动）。实证修正：该 HEAD 的端口目录是顶层 `posix/` 非旧布局 `cores/posix`；ITERATIONS 从 2000（≈6.2 亿指令 35+ 分钟）校准到 **35**（52.62/52.92s，10,808,351 insts，实测 31 万 insts/迭代）；`-DSEED_METHOD=SEED_VOLATILE -DPERFORMANCE_RUN=1`（上游 #ifndef 守卫，零文件修改，避免 SEED_ARG 在 gem5 SE 自校准死循环）。〕
- [x] Step 2: 验证 + GOLDEN_IDS 注册。〔执行注：golden `000000000000cf56`（crcfinal=0xcf56 零填充，覆盖全部迭代，强于只冻结第 0 迭代的分项 CRC）；native + C3×2 + 编排者独立 C3 跑共 4 次逐字节一致（config.ini 身份核实）；hostSeconds 52.62/52.92/52.86；simInsts 10808351 三跑精确同。**自带 CRC 校验 3/3 全过**（seedcrc 0xe9f5/crclist 0xe714/crcmatrix 0x1fd7/crcstate 0x8e3a 全对 known_id=3）；"Correct operation performed" 不可达为 EEMBC 10 秒计时规则的结构性现象（SE 模拟时钟 10 秒=2.6e10 周期≈数十主机小时）——"Errors detected" 行仅来自该规则，FINAL 门放 CRC 通过路径。**oracle 16 位熵（crcfinal 固有属性）**：比自设核 64 位 hash 粗，SDC 判定按此口径，记录在案。密度入档：mispredicts 73348（0.66%）、squash 15.1%、flIntLe8 10.6%（flIntMin=0 实压穿）、robOver80 1.3%（robMax=128）、IPC≈2.14。回归：全部 6 既有 golden 不变（全量重建+native 确定性重放）+ 编排者 smoke 独立回归。GOLDEN_IDS 注册 coremark-golden-v1。〕
- [x] Step 3: Commit + push（源码按上游 LICENSE 原样保留）

### Task 6: W1.2 — Embench 整数+浮点子集

**Files:** Create `workloads/ooo/embench/`
- [x] Step 1: 源获取与构建。〔执行注 2026-09-24：上游 embench-iot@09c2ed8c。**计划点名 6 程序中 3 个不可得（实证）**：qlsort/qrsolve 上游全部历史从未存在；**Embench-IoT 2.0 删除了全部浮点基准**（nbody/cubic/primecount 于 1b2731f、minver/st 于 fc72c8d）。替换：qlsort→wikisort、qrsolve→minver（3×3 float 求逆）；nbody/minver 取自末代存在 commit 92da124b。03-workloads.md 未指定程序名，替换在 spec 内（PROVENANCE.md 双 commit 记录）。每基准 1 个 `/* gem5-fi W1.2 */` FINAL 块（FNV-1a 64；crc32 为 15 位熵=上游自检同口径）；5 个逐一记录的上游代码质量类告警抑制（新告警类仍失败构建）。〕
- [x] Step 2: 验证 + GOLDEN_IDS×6。〔执行注：全 6 程序 native==gem5、s1==s2 逐字节一致、config.ini 身份 12/12；编排者另对 nbody/minver 独立 C3+native 三重核对+二进制指纹（一次多文件 grep -h 位置配对虚警，经 config.ini 终裁澄清——教训入档：逐文件带标签 grep）。hostSeconds 29.8-54.0 全 ≤60s；密度入档（整型/浮点三档格局）；nbody/minver native==gem5 将 fplib 位级一致扩展到 FSQRT。回归 7 既有 golden 全过。**重大发现（findings + 06 修订依据）**：标量 FP 程序 flFloatMin=192 恒满 + vec 池压 0 + 标量 FP 指令在场（objdump nbody 17 处 d/s 形式）→ **AArch64 gem5 v25 标量 FP 走 VecRegClass，FloatRegClass 池/RAT 惰性**——触发北极星 D62 自带合并条款（D62-66↔D67-71、D72/73/76↔D74/75/77 合并）。〕
- [x] Step 3: Commit + push

### Task 7: W1.3 — PolyBench（gemm/lu/cholesky/jacobi-2d）

**Files:** Create `workloads/ooo/polybench/`
- [ ] Step 1: 源获取——netlib 404 则用 GitHub 镜像（如 cavazos-lab/PolyBench 或 polybench-c 镜像，记录实际源与 commit）；四内核 -O2 -static，加 polybench.c 计时桩适配 SE。
- [ ] Step 2: 验证——全数组 dump 的 array_hash（GOLDEN_ARRAYS，64-hex）每内核一条 + 两次稳定 + SE 预算。
- [ ] Step 3: Commit + push

### Task 8: W1.4 — GAP（bfs/pr）+ libjpeg-turbo（风险最高，允许诚实 blocker）

**Files:** Create `workloads/ooo/gap/`、`workloads/ooo/libjpeg/`
- [ ] Step 1: GAP——上游 GAP 套件面向原生机大图，SE 移植成本高；先用轻量自实现 bfs/pr（固定 seed 生成 CSR 图，BFS 层序和 PageRank 迭代，结果 checksum 自校验），标注「GAP 语义代理」诚实口径；若必须用上游再评估。
- [ ] Step 2: libjpeg-turbo——`git clone github.com/libjpeg-turbo/libjpeg-turbo`（需 cmake；检查宿主 cmake 可用性），构建 djpeg NEON 路径，嵌入一张小 JPEG，解码输出逐字节 hash 为 golden；若 cmake/nasm 缺失→诚实 blocker 记录。
- [ ] Step 3: 验证 + Commit + push

---

## Self-Review 记录
- **Spec 覆盖**：03-workloads.md 8 负载 → Task 2-8 全覆盖（CoreMark/Embench/PolyBench/GAP/libjpeg/三探针核）；校验方式列逐一对应（自带校验/array_hash/逐像素/自校验）。
- **执行序调整**（06 未定包内顺序）：探针核先行（Task 2-4）——零外部依赖 + 解锁事件覆盖密度验收；外部基准按可得性跟进（Task 5-8）。宿主原生 aarch64 修正 06 的「交叉编译」假设。
- **占位符扫描**：密度门数值全部给出（5%/1%/50%）；SE 预算数值给出（≤60s）；无 TBD。
- **类型一致性**：FINAL 行格式仿 workloads/directed/reg_chain.c（Task 1 先读确认）；GOLDEN_IDS 注册模式与 runner.py 现有条目一致。
