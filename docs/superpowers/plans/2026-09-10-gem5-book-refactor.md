# 《深入理解 gem5 及 CHAOS 架构设计与源码实现》重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 `docs/gem5/gem5-architecture-and-chaos-internals.md`（1444 行），使全书由浅入深、通俗易懂、关键处深入源码、所有重要内容配图示。

**Architecture:** 全书保持 7 章 + 2 附录骨架不变（该骨架本身是正确的），对每一章做"渐进式重构"：每章一个 commit（一补丁一单元），重构前先做该章涉及的 LSP 源码验证（documentSymbol/goToDefinition/行号抽查），重构中执行统一的写作规约（下文 Global Constraints），重构后做行号引用与事实核对再提交。

**Tech Stack:** Markdown（GFM）、mermaid 不用（仓库惯例是 ASCII 图，与现有总览图一致）、LSP（clangd，对 `.cc` 可用；`.hh` 用 grep+Read 验证）。

**Spec:** 用户目标（2026-09-10 /goal）："使用lsp深度理解项目源码，对 docs/gem5/gem5-architecture-and-chaos-internals.md 重构，使得本书由浅入深、通俗易懂，又能再需要的地方深入源码十分深刻。所有重要内容都要增加图示"。

## Global Constraints（全书写作规约，每个任务隐含遵守）

1. **事实纪律（最高优先）**：重构只改组织与表达，不改事实。所有定量数字、行号、踩坑史、"诚实边界"声明原样保留（除非 LSP/grep 复核发现错误——发现错误时改事实并加注）。CLAUDE.md："必须诚实、不能说谎、100%服从事实"。
2. **行号引用规范**：保留 `file:line` 形式；每个 commit 前用 `sed -n 'Np'` 抽查该章全部行号引用（抽查率 100%，一条命令批量完成）。
3. **图示规范**：ASCII 框线图（`┌─┐│└┘◄►▲▼` 与现有总览图一致），每图必须有图号与标题（`图 N-M：...`）。"重要内容"的判据：新概念首次出现处、空间结构（流水线/层级/拓扑）、时序关系（生命周期/门控次序）、多对象关系（挂载模式/分类次序）——四类必配图。
4. **由浅入深模板**：每章开头加"本章导览"（3-5 行：本章解决什么问题、先讲什么后讲什么、读到哪节需要什么背景）；每节内部遵循"直觉 → 机制 → 源码 → 深入"四层推进，源码引用在直觉与机制建立之后出现。
5. **通俗化手法**：微架构概念（RAT/ROB/LSQ 转发/重命名）先用一句话生活化类比或"为什么需要它"的动机开场，再进源码。禁止删掉已有的好类比（如"相当于 Linux 内核里的调度器"），只增不减。
6. **中文技术写作**：术语首次出现给英文原文（如"重排序缓冲（ROB, Reorder Buffer）"），之后用中文。全书中英混排空格规约与现有文档一致。
7. **不新增事实**：不为"通俗"而虚构未验证的类比或数字；新增的过渡性文字只重组已有信息。
8. **每任务一 commit**：commit message 格式 `docs(gem5): 重构第N章<章名>——<本单元要点>`，无 Co-Authored-By 尾注，commit 后 push 到 `fi-fuzz`。
9. **验证命令**：每任务的功能验证 = (a) 行号抽查命令输出；(b) `grep -c '^\`\`\`'` 图表/代码块配对检查（偶数）；(c) markdown 结构检查（标题层级 `grep -n '^#'` 无跳级）。回归检查 = 姊妹篇 `docs/gem5/project-understanding.md` 未被改动（`git diff --stat` 确认）。

## File Structure

- Modify: `docs/gem5/gem5-architecture-and-chaos-internals.md`（唯一修改文件，逐章重构）
- Create: `docs/superpowers/plans/2026-09-10-gem5-book-refactor.md`（本计划）
- 勘察产物不落盘：LSP 验证结果直接进入 commit message 佐证。

全书目标结构（重构后，估算行数 ~1800±200）：

| 章 | 重构要点 | 新增图示 |
|---|---|---|
| 第一章 仿真内核 | 加"从一次仿真说起"入门导览；1.1-1.6 保持骨架，每节补机制图 | 图1-1 总览（已有）、图1-2 事件队列 bin-of-bins、图1-3 SimObject 六遍扫描时间线、图1-4 双语言架构分层 |
| 第二章 O3CPU | 章首加"一条指令的旅程"全流程图；2.4 rename 先讲动机再进源码（已部分做到，强化） | 图2-1 指令旅程全流水线、图2-2 TimeBuffer 环形滑窗、图2-3 两张 RAT 与 squash 回滚、图2-4 LSQ 转发判定决策树 |
| 第三章 内存系统 | 3.2 Port 三模式加对照图；3.5 翻译栈加三级走查图 | 图3-1 Request→Packet→Port 三层抽象、图3-2 内存层级拓扑（已有简版，扩展标注 hook 位点）、图3-3 ARM 翻译栈与 SE/FS 分流 |
| 第四章 CHAOS 框架 | 4.2 四种挂载模式每模式一小图；4.3 五层门画门控漏斗 | 图4-1 19 注入器微架构分布图（复用总览图局部放大）、图4-2 四种挂载模式对照、图4-3 五层门控漏斗、图4-4 三层故障轴 |
| 第五章 注入器深读 | 19 节按"前端→执行→提交→LSU→内存→系统"重组为 6 组，组首给组内关系图；每节保持"定位/参数/攻击/Stats/踩坑"五段 | 图5-1..5-6 六组分组图（每组 1 张组内靶点图） |
| 第六章 实验基础设施 | 6.1-6.8 已有总图；补 manifest 生命周期图与 classify 漏斗图 | 图6-1 三层机器总图（已有，微调）、图6-2 单次 run 生命周期、图6-3 classify 六类漏斗（文字流程图已有，转标准图框） |
| 第七章 方法论 | 八条定律每条加"一句话+图示"提要框 | 图7-1 双时间轴对照、图7-2 SE/FS 有效性边界（可选，若文字已够则不加） |
| 附录 | 保持，速查卡补挂载模式列 | 无 |

---

### Task 1: 重构第一章（仿真内核）

**Files:**
- Modify: `docs/gem5/gem5-architecture-and-chaos-internals.md:1-239`（第一章范围）

**Interfaces:**
- Consumes: 无（首任务）
- Produces: 全书开篇导览段（第二章重构时不再重写总览）、图号命名规约 `图 1-N`

- [x] **Step 1: LSP/行号验证第一章引用**

对第一章全部行号引用做批量抽查（simulate.cc:190/195/205/213/238/292、eventq.cc:224、eventq.hh:259/615/756、sim_object.hh:146、simulate.py:147/220/254、SConscript:565、BaseO3CPU.py 各行、mmu.cc:1212/323）。命令：

```bash
cd /home/sdc/wangxu/gem5-fi-fuzz/CHAOS/gem5
for ref in "src/sim/simulate.cc:190" "src/sim/simulate.cc:292" "src/sim/eventq.cc:224"; do
  f=${ref%:*}; l=${ref#*:}; echo "== $ref =="; sed -n "${l}p" $f
done
```

Expected: 每行输出与文档描述一致（doSimLoop 定义、serviceOne 定义等）。不一致则修正文档行号。

- [x] **Step 2: 写"本章导览"+ 入门铺垫**

第一章开头（总论段之前）插入：读者画像（想改 gem5/做故障注入研究的人）、本章学习路径（先跑起来一次仿真→理解事件循环→理解对象树→理解双语言）。总论段后新增 §1.0"从一次 `m5.simulate()` 说起"：用 20 行以内讲清"配置脚本→instantiate→simulate→事件循环→退出"全流程（纯文字+一张流程图），为 1.1 的源码深读搭桥。

- [x] **Step 3: 新增三张图**

图 1-2（事件队列 bin-of-bins 结构）：画 nextBin 外层串 + nextInBin 内层栈，标注 (when, priority) bin 语义与 LIFO。
图 1-3（instantiate 六遍扫描时间线）：横轴为 createCCObject→connectPorts→init→regStats→regProbePoints→regProbeListeners→initState→startup，标注注入器 self-attach 落点。
图 1-4（双语言架构）：Python 配置面（.py→Params 结构体）与 C++ 行为面（.hh/.cc→SimObject）经 SCons os.walk 连接的分层图。

- [x] **Step 4: 结构与配对检查**

```bash
f=docs/gem5/gem5-architecture-and-chaos-internals.md
grep -c '^```' $f   # 必须为偶数
grep -n '^#' $f | head -20   # 标题无跳级
```

- [x] **Step 5: Commit + push**

```bash
git add docs/gem5/gem5-architecture-and-chaos-internals.md
git commit -m "docs(gem5): 重构第一章仿真内核——加导览与§1.0入门铺垫，新增事件队列/六遍扫描/双语言三图"
git push origin fi-fuzz
```

### Task 2: 重构第二章（O3CPU）

**Files:**
- Modify: `docs/gem5/gem5-architecture-and-chaos-internals.md`（第二章范围）

**Interfaces:**
- Consumes: 图号规约（Task 1）
- Produces: "一条指令的旅程"叙事主线（第五章重组时引用它）

- [x] **Step 1: LSP/行号验证第二章引用**

抽查 cpu.hh:431/556、cpu.cc:76/149/367、timebuf.hh:178、comm.hh:112、bac.cc:578、rename.cc:934/958、free_list.hh:83/109、regfile.hh:167/185/211、inst_queue.cc:1077/1172、lsq_unit.cc:1440/1489、commit.cc:599、dyn_inst.hh:705/1177/1217。方法同 Task 1（批量 sed 循环）。.hh 文件 LSP 不可用时用 sed 直接核对。

- [x] **Step 2: 章首加"一条指令的旅程"**

第二章开头插入全流水线旅程图（图 2-1）：一条 ADD 指令从取指到提交的完整路径，六阶段+TimeBuffer+PRF/FreeList/RAT/ROB 全部标出，并把 19 个注入器靶点用 `◆` 标注在旅程图上（此图即全书最重要的单图，后续章节回指它）。

- [x] **Step 3: 逐节由浅入深改造**

2.1 补 TimeBuffer 环形滑窗图（图 2-2：base 指针轮转、wire[0]/wire[-1] 槽位、placement new 重建"未来"槽）。
2.4 在两张 RAT 讲解前加"为什么需要重命名"的动机段（现有开头已有补景句，扩展为完整段落：WAR/WAW 冒险→物理寄存器解耦），加 squash 回滚数据流图（图 2-3：renameMap 回滚 + freeingInProgress 延迟归还 + spec_leak hook 位点）。
2.6 保留现有机制开场（已达标）。
2.7 LSQ 转发判定画决策树图（图 2-4：循环入口门槛→ AddrRangeCoverage 三分支→ FullAddrRangeCoverage 走 memcpy + 双 hook 位点）。
2.9 保留 hook 迁移史（已是全书最佳实践段落）。

- [x] **Step 4: 结构与配对检查**（同 Task 1 Step 4）

- [x] **Step 5: Commit + push**

```bash
git add docs/gem5/gem5-architecture-and-chaos-internals.md
git commit -m "docs(gem5): 重构第二章O3CPU——新增指令旅程总图与TimeBuffer/RAT回滚/LSQ转发判定三图，补重命名动机段"
git push origin fi-fuzz
```

### Task 3: 重构第三章（内存系统）

**Files:**
- Modify: `docs/gem5/gem5-architecture-and-chaos-internals.md`（第三章范围）

**Interfaces:**
- Consumes: 图号规约
- Produces: 翻译栈分流图（第五章 ArmTLB/PTW/SysReg/AddrPath 组引用）

- [x] **Step 1: LSP/行号验证第三章引用**

抽查 request.hh:858、port.hh:134/347、base.hh:103、tags/base.hh:81、base.cc:83/1795、CHAOSMem.cc:206-382、mmu.cc:323/1005/1203-1221、tlb.cc:164、table_walker.cc:1944、isa.cc:458/1930。

- [x] **Step 2: 三层抽象与拓扑图**

3.1 加图 3-1（Request→Packet→Port 三层抽象：谁/哪个地址/什么语义 → MemCmd+数据缓冲 → 协议交互，标注 CHAOSAddrPath 的 setVaddr 落点）。
3.2 现有单行拓扑图升级为图 3-2（完整层级图：CPU→L1D/L1I→XBar→L2→XBar→MemCtrl→DRAM，每级标注 CHAOS 双 hook 位点与 functional 通道）。
3.2 补 timing/atomic/functional 三模式对照小表（现有文字提及三重协议继承，加一张 3 列小表：模式/用途/CHAOS 谁在用）。

- [x] **Step 3: ARM 翻译栈图**

3.5 加图 3-3（MMU→TLB→PTW 三级走查图 + SE/FS 分流：translateSe 软件页表支路 vs sctlr.m=1 硬件通路支路，四个 FS-only 注入器挂点全标注）。该图是理解"为什么 SE 下四个注入器恒零注入"的钥匙。

- [x] **Step 4: 结构与配对检查**（同 Task 1 Step 4）

- [x] **Step 5: Commit + push**

```bash
git add docs/gem5/gem5-architecture-and-chaos-internals.md
git commit -m "docs(gem5): 重构第三章内存系统——新增三层抽象/内存拓扑/ARM翻译栈分流三图，Port三模式对照表"
git push origin fi-fuzz
```

### Task 4: 重构第四章（CHAOS 框架总览）

**Files:**
- Modify: `docs/gem5/gem5-architecture-and-chaos-internals.md`（第四章范围）

**Interfaces:**
- Consumes: 图号规约
- Produces: 四种挂载模式图、五层门漏斗图、三轴故障模型图（第五章每节引用，替代重复叙述）

- [x] **Step 1: LSP/行号验证第四章引用**

抽查 CHAOSLSQFwd.cc:37/60、CHAOSFPU.cc:47、CHAOSIQ.cc:55、CHAOSROB.cc:53/104、CHAOSArmTLB.cc:52、CHAOSArmSysReg.cc:45/59、CHAOSPTW.cc:45、CHAOSCache.cc:56/94/101、cpu.hh:483-538、CHAOSExMon.cc:12/69、CHAOSAddrPath.cc:28、CHAOSLSQFwd.cc:281。

- [x] **Step 2: 图 4-1 微架构分布图**

从第一章总览图提炼"19 注入器×微架构位置"矩阵图（图 4-1）：行=流水级（BAC/Fetch/Rename/IEW/Commit/LSQ/Cache/Mem/TLB-PTW/ISA），列=挂载模式，格内=注入器名。一图回答"每个注入器在哪、怎么挂"。

- [x] **Step 3: 挂载模式与门控图**

4.2 每种挂载模式配一张 6-8 行小图（图 4-2a/b/c/d）：模式 A 画注入器构造→宿主指针→热路径判空三步；模式 B 画 private 状态→访问器通道→注入器；模式 C 画 attackEvent 自循环；模式 D 画宿主代码内 hook 行。模式 D 特例（全局指针）并入 4-2d。
4.3 画五层门漏斗图（图 4-3）：probability→时间窗下界→上界→maxFaults→Bernoulli 五层递减，每层标"卡住会怎样"（引 §4.3 现有踩坑说明）。

- [x] **Step 4: 三轴故障模型图**

4.4 加图 4-4（三条正交轴的坐标式呈现：轴一位级→结构化、轴二对→错源、轴三数据→协议不变量，每轴标代表注入器与代表故障模式）。

- [x] **Step 5: 结构与配对检查 + Commit + push**

```bash
git add docs/gem5/gem5-architecture-and-chaos-internals.md
git commit -m "docs(gem5): 重构第四章CHAOS框架——新增注入器分布矩阵/四种挂载模式/五层门漏斗/三轴故障模型图"
git push origin fi-fuzz
```

### Task 5: 重构第五章（19 注入器深读）

**Files:**
- Modify: `docs/gem5/gem5-architecture-and-chaos-internals.md`（第五章范围，全书最大改造单元）

**Interfaces:**
- Consumes: 图 2-1 指令旅程图、图 4-1/4-2/4-3/4-4（第五章不再重复共性叙述，直接回指）
- Produces: 六组分组图（图 5-1..5-6）

**重组方案**（保持 19 节内容五段式不动，只重排顺序+组首导航）：按数据流分六组——G1 前端与重命名（BPU/RenameMap/FreeList/PhysReg）、G2 发射与执行（IQ/Exec/FPU/L1DForward）、G3 提交与恢复（ROB/RAS）、G4 LSU 与地址通路（LSQFwd/AddrPath）、G5 内存与缓存（Cache/Mem/ExMon）、G6 翻译栈与系统（ArmTLB/PTW/ArmSysReg/Reg）。每组开头 5-8 行组导航：这组攻击流水线哪一段、组内注入器共享什么共性、与相邻组的关系。原 §5.1-5.19 编号相应调整，交叉引用同步更新。

- [x] **Step 1: LSP/行号验证第五章引用（抽查量最大）**

19 个注入器的关键行号全部抽查（重点：各注入器 .cc 的 processFault/hook 函数定义行、挂载行、Stats 定义行）。命令模式同前，分 3 批执行。

- [x] **Step 2: 重组结构 + 写六个组导航**

按上述 G1-G6 重排 19 节。每节内部保持"定位/参数面/攻击路径/故障模型/Stats/踩坑史"五段。删除各节中与第四章重复的共性内容（如重复的门控叙述），改为"共性见 §4.3"引用。

- [x] **Step 3: 六张组图**

每组一张"组内靶点图"（图 5-1..5-6），例：G1 图画 Rename→FreeList→PhysRegFile 三个数据结构与三个注入器的攻击向量（映射替换/分配破坏/cell 毁值）；G4 图复用图 2-4 局部放大标注 LSQFwd 双 hook 与 AddrPath hook。图要小（≤15 行），信息密度靠标注。

- [x] **Step 4: 交叉引用一致性检查**

```bash
f=docs/gem5/gem5-architecture-and-chaos-internals.md
grep -n '§5\.' $f   # 所有第五章交叉引用与新编号一致
grep -n '§[0-9]\.[0-9]' $f | head -40   # 全书交叉引用抽查
```

- [x] **Step 5: 结构与配对检查 + Commit + push**

```bash
git add docs/gem5/gem5-architecture-and-chaos-internals.md
git commit -m "docs(gem5): 重构第五章注入器深读——19节按数据流重组为6组，组导航+6张组内靶点图，去共性重复"
git push origin fi-fuzz
```

### Task 6: 重构第六章（实验基础设施）

**Files:**
- Modify: `docs/gem5/gem5-architecture-and-chaos-internals.md`（第六章范围）

**Interfaces:**
- Consumes: 图号规约
- Produces: run 生命周期图、classify 漏斗图（第七章引用）

- [x] **Step 1: 行号验证第六章引用**（tools/*.py 行号抽查，python 无 LSP 也用 sed 核对）

抽查 campaign.py:9/55/70/86/166/229/348/355、runner.py:43/92/141/205/232/243/289/320/358/429/468/499、classify.py:4/54/84/229、escape_decomp.py:37/97、sdc_fingerprint.py:21/30/48、loo_validate.py、fisher_test.py。manifests 实例文件核对（artifacts/prf-formal/manifests/prf_x3_formal-c000-r0.yaml:5-6）。

- [x] **Step 2: 现有文字流程图标准化 + 新图**

章首总图（campaigns→manifests→runner→gem5→classify）从纯文字符号图升级为标准框线图（图 6-1）。
6.1-6.2 之间加"单次 run 生命周期图"（图 6-2）：manifest 读入→三重前置校验→gem5.opt 运行→faults 日志解析→G5 断言→oracle 三路分派→RESULT 行，标注每步的失败出口（exit/skip/VIOLATION 标记）。
6.4 classify 六类判定次序转为漏斗图（图 6-3）：SimulatorError→Hang→Crash→Inactive→歧义→Masked→SDC 七层，每层标判据关键词，与"由外到内漏斗"的设计哲学呼应。

- [x] **Step 3: 表格与结论保留核对**

6.6 campaign 全景表、6.7 kernel 表、6.8 配置差异清单原样保留（这些是事实载体，不动）。

- [x] **Step 4: 结构与配对检查 + Commit + push**

```bash
git add docs/gem5/gem5-architecture-and-chaos-internals.md
git commit -m "docs(gem5): 重构第六章实验基础设施——总图标准化，新增run生命周期图与classify七层漏斗图"
git push origin fi-fuzz
```

### Task 7: 重构第七章（方法论）+ 全书终检

**Files:**
- Modify: `docs/gem5/gem5-architecture-and-chaos-internals.md`（第七章 + 全书终检）

**Interfaces:**
- Consumes: 前六章全部图号
- Produces: 终版全书

- [x] **Step 1: 七章导览与双时间轴图**

章首加导览（八条定律的依赖关系：7.1 hook 选择是最底层，其余各条独立）。7.6 加双时间轴对照图（图 7-1）：上半 CPU cycle 域下半 sim tick 域，标注各注入器归属与 CHAOSMem 换算事故位置。

- [x] **Step 2: 每条定律加提要框**

7.1-7.8 每节开头加一行"**一句话**：..."加粗提要 + 本条定律配图回指（如 7.3 回指图 2-4、7.7 回指图 3-3）。不新增图，靠回指前六章。

- [x] **Step 3: 全书终检**

```bash
f=docs/gem5/gem5-architecture-and-chaos-internals.md
grep -c '^```' $f          # 偶数
grep -n '图 [0-9]-[0-9]' $f | wc -l   # 图总数统计，目标 ≥20
grep -n '^#' $f             # 章节结构完整无跳级
grep -n 'TBD\|TODO\|待补\|占位' $f    # 无计划残留（注意：§6.2 的 no-op 占位是事实描述，允许保留"占位"一词于该上下文）
wc -l $f                    # 行数记录
git diff --stat             # 确认只改了目标文件
```

- [x] **Step 4: 姊妹篇回归检查**

`git diff origin/fi-fuzz -- docs/gem5/project-understanding.md` 为空（未误改姊妹篇）。

- [x] **Step 5: Commit + push**

```bash
git add docs/gem5/gem5-architecture-and-chaos-internals.md
git commit -m "docs(gem5): 重构第七章方法论并终检——八条定律提要框、双时间轴图、全书图示/行号/结构终检"
git push origin fi-fuzz
```

## Self-Review 结论

1. **Spec 覆盖**：目标四个要求——"由浅入深"（每章导览+四层推进，Task 1-7 全覆盖）、"通俗易懂"（动机先行+类比保留，Task 2/5 重点）、"深入源码"（LSP/行号验证步骤贯穿每任务）、"图示"（Global Constraint 3 定义四类必配图，各任务产出 ~21 张图）。
2. **占位符扫描**：无 TBD/TODO；每个 Step 有具体命令或具体内容要求。
3. **一致性**：图号规约 `图 N-M` 全任务统一；第五章重组的 G1-G6 与 Task 5 Step 4 的交叉引用检查闭环。
