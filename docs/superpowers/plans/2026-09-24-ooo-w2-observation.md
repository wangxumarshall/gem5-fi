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

- [x] Step 1: 四件套 + commit 钩子（spike 事实 1/2/3/4 全部行号在案）。〔执行注 2026-09-24：commit.hh +12（前置声明/成员/setter 照抄 CHAOSRAS@356-363 模式）；commit.cc +14（钩在 setEntry 循环后=读到注入后 RAT、retireHead 前）；ooo_proxy +25（--chaos_ctrace/--ctrace_file 默认 commit_trace.csv.gz）。**过程中发现并修复真实格式 bug**（首版 MiscReg 分支 phys/val 间漏逗号——被自加的列数契约检查当场抓出，修复后全量重跑 5 个验证运行）。诚实偏差：XZR 目的输出 class=-1/phys=65535（gem5 哨兵，bm 占 5.9%）；MiscReg 目的不读 physRegFile（getReg 会 panic）val 记零；VecPred/Mat 宽度走 regClass().regBytes()（无公开 vecPredRegBytes）；行数按 commitHead 逐 DynInst 含微码 op（309387>simInsts 308057——钉死格式用 committedInstType_0::total 交叉验证正因此）；无 stdout 汇总行（刻意——保 stdout 可逐字节比对）。〕
- [x] Step 2: 增量构建零新告警（新编译单元零警告；全量构建 4 行既有告警均在未触碰文件）
- [x] Step 3: 挂载 ooo_proxy（--chaos_ctrace）
- [x] Step 4: 验证五关全过。〔执行注：①**纯读证明（硬门）**——smoke/branch_mispred 带 trace FINAL 逐字节一致（45737cc9a76c0dce/06e84f119c258fa7）+ simInsts 不变 + 默认关闭回归干净；②行数自洽——trace 行数==committedInstType_0::total（309387/8612678 双 MATCH）；③内容抽查——**与 --debug-flags=Commit 全流 309,387 行 TICK+PC 全等** + op 与 objdump 反汇编一致 + 值语义抽查（adrp→0x400000、bl→x30=返回地址）✓；④减速实测——smoke 2.09×/branch_mispred 1.56×；gz 体积 5.1MB/97.9MB（spike 估计 60-130MB 带内）；⑤格式自检全过（val=16hex/列数契约/seq 单调）。**编排者集成验收（2026-09-24）**：真实双 smoke trace（各 309,387 条）→ commit_diff **no_divergence**（tick-tol=0 全程字段+tick 全同，五类计数全 0，INTEG_EXIT=0 无管道直测）——W2.2 延期集成项闭环；发现并修复 class=-1 哨兵契约缺口（d0b372c3）。〕
- [x] Step 5: Commit + push

### Task 2: W2.2 — tools/commit_diff.py（TC'23 五分类 + 潜伏期）

**Files:** Create `tools/commit_diff.py`（stdlib-only，含 gzip 读取）
**Interfaces:** `python3 tools/commit_diff.py --ref A.csv.gz --run B.csv.gz [--json OUT] [--tick-tol T]`；输出：主分类 + 潜伏期（首次分歧 seq）+ 首分歧明细 + 各类计数。
**五分类映射（钉死）**：首分歧指令处按字段优先级——pc 异同→②指令流改变；同 pc 不同 op→③指令替换；同 op 但 dest arch id 不同→④操作数强制切换；同 arch 但 val 不同→⑤数据损坏；全程字段全同但 tick 漂移超阈→①执行时间错。单侧缺失 seq 也算②。

- [x] Step 1: 写解析器（钉死格式）+ 五分类对齐比对。〔执行注 2026-09-24：507 行 stdlib-only；流式 merge-join 按 seq 对齐 O(1) 内存；dest arch id 严格解释=(RegClass,arch) 二元组；①执行时间错两段式（全程字段全同才判①，前置漂移降级为辅助诊断——计划原文语义）；phys/tid 不参与五分类仅辅助诊断（供 W2.4 交叉）；严格校验 seq 从 0 起且严格递增/val 恰 16 位 hex/gzip 按 magic 识别。〕
- [x] Step 2: 验证。〔执行注：**40/40 断言全 PASS**（编排者亲测重跑）——五类各一例+变体（ndest 数量变体判④）+ 多分歧主类=首个 + 自比对 9 例零分歧 + tick 容差三档语义 + 100 行伪 trace 预演 3 对 + 阴性 6 例（编排者亲测 REAL_EXIT=1，注意编排者首次检查时又踩 `| head` 管道陷阱取错退出码——findings 已有前科记录，无管道复测确认）。**②真实无注入对延期**：trace 生成器是并行 W2.1 产物尚不可用——列入 W2.1 落地后的编排者集成验收（smoke 两跑 trace → 零分歧），W2.3 前置。〕〔**契约修订（2026-09-24，W2.1 集成验收发现的真实缺口）**：W2.1 对 XZR/WZR 目的寄存器输出 class=-1（gem5 哨兵 PhysRegId 的 InvalidRegClass，phys=65535，bm 中占 5.9%）——原 `_uint` 校验拒绝。修订：class 字段接受非负整数或 **-1 哨兵**（CLASS_RE + `_cls`）；哨兵案例（class=-1,arch=31,phys=65535）通过 + 40/40 套件回归通过。真实双 trace 集成验收见 Task 1 执行注。〕
- [x] Step 3: Commit + push

### Task 3: W2.3 — 两遍法编排（campaign/runner）

- [x] runner/campaign 支持 trace 重放遍。〔执行注 2026-09-24：runner 加 --ctrace/--ctrace-ref/--no-inject（C3-only 早期校验；L2RESULT 单行 JSON 输出含诚实 l2_error 失败路径）+ PYTHONHASHSEED=0 子进程 env（/proc 实证）+ smoke-golden-v1 注册；campaign 加 trace: 节（参照遍每 cell 一次 --no-inject --ctrace + sidecar 溯源 sha256；重放遍对 replay_for 类同 seed 重跑 + commit_diff 结果并入 results.jsonl 的 l2 块含 replay_determinism）。**实测竞态催生守卫**（并行 W2.4 重建 gem5.opt 撞出 PermissionError——非确定性假象的铁证）：参照复用 sha 校验 + 重放前二进制 sha 守卫（跨二进制 diff=垃圾则跳过记 l2_error）。**真 bug 发现并修复**：Crash rep 的截断 gzip 使 count_trace_lines 抛 EOFError 丢 L2RESULT——catch 修复 + 真实截断文件单测。〕
- [x] 验证：三臂玩具 campaign 端到端。〔执行注：A 臂（smoke，Masked 不触发重放 + ref 幂等复用）；B 臂（replay_for 加 Masked 验证机制，3/3 determinism=match + no_divergence）；**C3 臂（branch_mispred+rat map_bitflip，真实回填）**：rep0 SDC → verdict=diverged **primary_class=data_corruption、latency_seq=210665**（首分歧 3ca26881→1eb1，两次构建的二进制上逐字段复现=确定性铁证）+ divergence_counts 全量；rep1 Crash → **诚实 l2_error**（trace 截断——见发现）。编排者亲测：py_compile + results.jsonl 的 l2 块逐字段核验。回归：无 trace campaign 1200/1200 manifests 逐字节同形。**发现（W2.1 后续）**：gem5 abort 不 flush gzip——Crash rep trace 截断（本例 2.3MB 幸存），Crash 类 L2 五分类暂得 l2_error；CHAOSCommitTrace 需周期 flush（与 W2.4 micro-snap 的 gzflush 同族修复，列入待办）。〕
- [x] Commit + push

### Task 4: W2.4 — CHAOSMicroSnap + micro_diff.py（L1 影子快照）

- [x] 四件套 + commit 侧采样 + micro_diff.py。〔执行注 2026-09-24：**快照目标修正为 front rename map（真 RAT）**——机制发现：CHAOSRenameMap 只挂 frontRenameMap[0]、SimpleRenameMap::rename() 直写不走 setEntry（注入经 squash 回滚落 front 表；commit map 只收 per-inst dest id 永远干净——快照 commit map 定向验收会恒 0）。**崩溃持久化实测驱动修正**：simout gz 流裸 gzwrite 数据滞留 zlib——abort 后快照 0 字节（实测）；改自管 gzFile+每快照 gzflush(Z_SYNC_FLUSH)，abort 后 309 行全抢救（micro_diff 截断流抢救路径+truncated 如实标记；正常退出 trailer 由 exit callback 写）。CSV：hash+全表（表内分隔符 `;`——自测抓出逗号破坏列契约）+rob_head/tail；每快照 gzflush 减速 1.037×、体积 18KB/1.05MB。**发现 W2.1 注释失准**（未改动仅报告）：「钩后读到注入后 RAT」表述不成立——注入钩在 front map，commit.cc:1273 的 setEntry 不含注入；W2.1 trace 读 inst 字段故不受影响（phys 经 inst 自身 rename 已携带注入映射）。〕
- [x] 验证全过。〔执行注：纯读硬门（编排者亲测 smoke+msnap FINAL=45737cc9a76c0dce/simInsts 不变/默认关闭回归）；快照自洽（309/8612==预期、单调）；micro_diff 自测 11/11（编排者亲测重跑）+自比对/干净双跑 no_divergence；**定向验收（--msnap_every 10，编排者从产物 JSON 复核）**：int RAT 分歧 max=1 first_snap=30867（tick 89981430==注入 tick 精确对上）、nonzero_snaps=2、愈合 final=0；下游分歧 arch1 随快照传播；fp/vec=0 与注入器 int-only 一致；占用/IPC 全零=**教科书隐蔽样本（只有 L1 能看见）**；abort 抢救路径实证。**已知边界（诚实记录）**：默认 snapEvery=1000 采漏 <1000 commit 的愈合窗口（R2f/R6f 全零反向印证）——W2.3 量产时按需调 --msnap_every。〕
- [x] Commit + push

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
