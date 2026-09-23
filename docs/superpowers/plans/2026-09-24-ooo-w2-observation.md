# OoO W2 观测层三大件 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建成 L2 commit 级 TC'23 五分类观测（CHAOSCommitTrace + commit_diff.py + 两遍法编排）与 L1 微架构快照比对（CHAOSMicroSnap + micro_diff.py），以及 L0 生命周期接口与 L3 扇出/stats 消费。

**Architecture:** 两个新只读 SimObject（骨架整段抄 CHAOSProbe 四件套）+ commit.cc 单一钩点（1274 后，setter 模式照抄 CHAOSRAS@commit.hh:356-363）+ 纯 python 离线比对器。**设计事实全部来自 W2 spike（findings.md「W2 观测层设计 spike 结论」，行号证据在案）**。

**Tech Stack:** gem5 C++ SimObject（simout.create .gz 自动 gzip；zlib 硬依赖）/ python3 stdlib-only 工具。

**Spec:** `docs/gem5-fi/ooo/06-implementation-plan.md` §4 W2 + `01-observation-points.md`（L0-L4 定义，冲突以 01 为准）。

## Global Constraints（继承 W0/W1 全部纪律）

- 并发 subagent ≤2；共享文件（commit.cc/commit.hh/ooo_proxy.py/Makefile/README）改动最小化并经编排者 diff 竞争审查。
- **trace 钩子必须纯读零事件**——带 trace 运行的 FINAL 必须与无 trace 逐字节一致（CHAOSProbe 先例）；这是 W2.1/W2.4 的共同硬门。
- 增量构建 `-j126`（产物=仓库根 build/ARM/gem5.opt）；每 patch 三件套验证 + 回归（smoke golden `45737cc9a76c0dce`）。
- **钉死的 trace 行格式**（W2.1 产出、W2.2 消费，双方按此并行）：
  `seq,tid,tick,pc,op,ndest[,class,arch,phys,val]*`（CSV，gzip；seq=自持全局提交序号 0 起；pc=十六进制无前缀；op=staticInst->getName()；每个目的寄存器四元组：class=RegClass 值、arch=架构索引、phys=物理索引、val=16 位十六进制——标量直接零填充，向量=vecRegBytes() blob 的 FNV-1a-64）。

---

### Task 1: W2.1 — CHAOSCommitTrace（L2 commit 逐指令 trace）

**Files:**
- Create: `CHAOS/gem5/src/cpu/o3/CHAOSCommitTrace/{CHAOSCommitTrace.hh,.cc,.py,SConscript}`（骨架抄 CHAOSProbe 四件套）
- Modify: `CHAOS/gem5/src/cpu/o3/commit.cc`（1274 后加钩：`if (chaosCommitTrace) chaosCommitTrace->traceCommit(tid, head_inst.get());`）+ `commit.hh`（成员/setter，照抄 CHAOSRAS@:356-363 模式 + 前置声明/include）
- Modify: `configs/se/ooo_proxy.py`（`--chaos_ctrace` + 文件名参数）

**Interfaces:**
- SimObject：`CHAOSCommitTrace(cpu=, traceFile="commit_trace.csv.gz", writeLog=True)`；self-attach 不行——需 commit.cc 钩子（spike 结论 7）；钩内自持 `uint64_t seq` 计数器。
- 每条提交指令按钉死格式写一行（simout.create 自动 gzip；纯读：只调 pcState/getName/destRegIdx/renamedDestIdx/physRegFile().getReg，不产生任何事件）。

- [ ] Step 1: 四件套 + commit 钩子（spike 事实 1/2/3/4 全部行号在案）
- [ ] Step 2: 增量构建零新告警
- [ ] Step 3: 挂载 ooo_proxy（--chaos_ctrace）
- [ ] Step 4: 验证：①纯读证明——smoke + branch_mispred 带 trace 跑 FINAL 与无 trace 逐字节一致；②行数自洽——trace 行数 == stats committedInsts（自持计数器交叉验证）；③内容抽查——前 100 行的 PC/op 与 `--debug-flags=Commit` 抽样一致；④减速实测——smoke（308K insts）与 branch_mispred（8.6M）两档 hostSeconds 比值入档；⑤gz 可解（zcat | head）。
- [ ] Step 5: Commit + push

### Task 2: W2.2 — tools/commit_diff.py（TC'23 五分类 + 潜伏期）

**Files:** Create `tools/commit_diff.py`（stdlib-only，含 gzip 读取）
**Interfaces:** `python3 tools/commit_diff.py --ref A.csv.gz --run B.csv.gz [--json OUT] [--tick-tol T]`；输出：主分类 + 潜伏期（首次分歧 seq）+ 首分歧明细 + 各类计数。
**五分类映射（钉死）**：首分歧指令处按字段优先级——pc 异同→②指令流改变；同 pc 不同 op→③指令替换；同 op 但 dest arch id 不同→④操作数强制切换；同 arch 但 val 不同→⑤数据损坏；全程字段全同但 tick 漂移超阈→①执行时间错。单侧缺失 seq 也算②。

- [x] Step 1: 写解析器（钉死格式）+ 五分类对齐比对。〔执行注 2026-09-24：507 行 stdlib-only；流式 merge-join 按 seq 对齐 O(1) 内存；dest arch id 严格解释=(RegClass,arch) 二元组；①执行时间错两段式（全程字段全同才判①，前置漂移降级为辅助诊断——计划原文语义）；phys/tid 不参与五分类仅辅助诊断（供 W2.4 交叉）；严格校验 seq 从 0 起且严格递增/val 恰 16 位 hex/gzip 按 magic 识别。〕
- [x] Step 2: 验证。〔执行注：**40/40 断言全 PASS**（编排者亲测重跑）——五类各一例+变体（ndest 数量变体判④）+ 多分歧主类=首个 + 自比对 9 例零分歧 + tick 容差三档语义 + 100 行伪 trace 预演 3 对 + 阴性 6 例（编排者亲测 REAL_EXIT=1，注意编排者首次检查时又踩 `| head` 管道陷阱取错退出码——findings 已有前科记录，无管道复测确认）。**②真实无注入对延期**：trace 生成器是并行 W2.1 产物尚不可用——列入 W2.1 落地后的编排者集成验收（smoke 两跑 trace → 零分歧），W2.3 前置。〕〔**契约修订（2026-09-24，W2.1 集成验收发现的真实缺口）**：W2.1 对 XZR/WZR 目的寄存器输出 class=-1（gem5 哨兵 PhysRegId 的 InvalidRegClass，phys=65535，bm 中占 5.9%）——原 `_uint` 校验拒绝。修订：class 字段接受非负整数或 **-1 哨兵**（CLASS_RE + `_cls`）；哨兵案例（class=-1,arch=31,phys=65535）通过 + 40/40 套件回归通过。真实双 trace 集成验收见 Task 1 执行注。〕
- [x] Step 3: Commit + push

### Task 3: W2.3 — 两遍法编排（campaign/runner）

- [ ] runner/campaign 支持 trace 重放遍：对 classify 为 SDC/Crash/Hang 的 rep 同 seed 重跑 + `--chaos_ctrace`，参照 run 名命名 trace 文件（cell/rep 可追溯）；无故障参照遍每 cell 一次。
- [ ] 验证：玩具 campaign 端到端（1 cell × 小 n，含一次已知 SDC 定向注入）→ L2 列可回填。
- [ ] Commit + push

### Task 4: W2.4 — CHAOSMicroSnap + micro_diff.py（L1 影子快照）

- [ ] 四件套（self-attach 零源码钩子 + rename_map.hh:204 加 map(RegClassType) accessor 最小 patch）+ commit 侧采样（与 Task 1 同一钩点每 N 条调 sample()：RAT 三类表快照 + freelist/ROB head-tail/IQ 占用 + tick）+ tools/micro_diff.py（按 commit 序号对齐快照序列 → 分歧项数/占用偏差/停顿差/IPC 偏差 + **隐蔽样本标记**：Masked/SDC 但 IPC 偏差>50%）。
- [ ] 验证：纯读证明（FINAL 不变）+ 定向：一次已知 RAT 注入的快照分歧>0 且随 commit 演化 + micro_diff 输出合理。
- [ ] Commit + push

### Task 5: W2.5 — L0 注入项生命周期接口

- [ ] 接口规范文档（reads_before_overwrite/overwritten/overwritten_at_cycle 三字段 + 注入器登记/读取/覆写钩点模板）+ 第一个接线示范（选 CHAOSPhysReg 现有 readTrace 对齐接口）。
- [ ] Commit + push

### Task 6: W2.6 — L3 扇出 + stats 消费

- [ ] 污染 PRF 读踪计数复用（rat/rob/iq 换值类注入记录目标 phys id）；runner 从 stats.txt 提取 IPC/占用摘要进 results.jsonl。
- [ ] 验证：定向注入后扇出数>0；results.jsonl 含 stats 块。
- [ ] Commit + push

## 执行序与并发
- **Task 1 + Task 2 并行**（文件集不相交：gem5 src+config vs tools/；格式已钉死）。
- Task 3 依赖 Task 1+2 落地；Task 4 独立（可与 Task 3 并行，但 commit.cc 钩与 Task 1 冲突——**Task 4 的 commit 侧采样必须排在 Task 1 合入之后**，其 self-attach 主体可先行）；Task 5/6 随后。

## Self-Review
- 格式钉死使 Task 1/2 可并行（类型一致性由双方共守本文件 Interface 块保证）。
- 五分类映射覆盖 01-observation-points.md 全部五类，无遗漏；潜伏期=首分歧 seq（01 的「提交指令数」口径）。
- 纯读零事件是两个 SimObject 的共同硬门（CHAOSProbe 先例模式）。
