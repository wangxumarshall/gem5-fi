# OBS Phase B 设计：激活窗口 ctrace/msnap + 传播 tag（设计文档，不实现）

> 状态：**设计入档，未实现**（OBS 计划 T9）。任何 C++ 改动与重编受用户指令
> 2026-10-12 一.3 硬约束：**必须等现有全部实验进程结束、无 gem5 在跑**，
> `build.lock` 单实例，`scons -j16`（-j126 会 OOM-kill 29GB 主机）。
> 基线：CHAOS/gem5/src/cpu/o3/CHAOSCommitTrace/ 与 CHAOSMicroSnap/（v25.1.0.1
> vendored，已编译入冻结二进制 10590f62…）。

## 1. 问题（Phase A 已实证的边界）

- W1（w1_all）golden 全程 7.44–7.51h；全量 ctrace 一行/提交指令，体积不可行
  （估算 10^10+ 指令 → 数百 GB gz）。Phase A 观测驱动对 W1 载体强制
  `l0l5`（`coverage_scope=none_full_run_forbidden_pending_phaseB`）。
- msnap snapEvery=1000，W1 全程 ~10^7 行，同样超预算。
- 短流 checklist 载体（golden ≤61s）全量可行（Phase A 已开 full 模式，
  带单载体 --trace-budget-gib 门禁）。

## 2. 激活窗口设计（推荐 A 案：注入器回调开窗）

### A 案：注入器 → 观测器回调开窗（首选）
`CHAOSAddrPath/CHAOSLSQFwd/...` 首次真实注入（`faults_injected` 0→1）时调用
两个观测器的 `activate(curTick)`；观测器自此才开始 dump。

- `CHAOSCommitTrace.hh/.py` 新参数：
  - `startTick`（uint64，默认 0=从头）——静态窗口下界（B 案兼容面）
  - `windowTicks`（uint64，默认 0=无界）——激活后覆盖宽度
  - `activatedMode`（bool，默认 false）——true 时由注入器回调开窗
- dump 条件：`activated && tick ∈ [actTick, actTick+windowTicks)`；
  `actTick` 由 `activate()` 设置并随 trace 头行写出（前缀可解码不变——
  W2.1 契约行格式不动，仅新增一条 `# window act=<tick> span=<n>` 头注释，
  commit_diff/micro_diff 对 `#` 行已忽略）。
- `CHAOSMicroSnap` 同参数同语义（snap 行按 commit_seq 对齐窗口）。
- 注入器侧：`chaos_l0.hh` 生命周期结构里已有首次注入点；加一个
  `setChaosObservationWindow` 反向指针（同 `setChaosCommitTrace` 自挂模式）。
- **风险**：注入前指令无 trace → L2 对齐仍可用（commit_diff 按 seq 对齐，
  ref 侧全量、fault 侧窗口；`fault_trace_truncated` 语义扩展为
  `windowed`，绝不冒充全量）。observation.json 的
  `coverage_scope="window[actTick,actTick+windowTicks]"`。

### B 案：ring buffer（备选，不推荐首期）
观测器全量入内存环形缓冲（N 行），abort 时 dump 尾部 N 行。优点：无注入器
耦合；缺点：常驻内存 × 并发 8 槽、N 的选取与"首分歧在环外"的漏检风险。
仅当 A 案注入器耦合在实测中不可行时启用。

## 3. 传播 tag（L3 真实证据，取代 PRF-proxy/unsupported）

目标：addrpath 家族注入的**损坏 vaddr** 能被追踪到"哪些动态指令消费了它"。
- `CHAOSCommitTrace` 行格式扩展（**v2 行格式，文件头注明**）：
  `seq,tid,tick,pc,op,ndest[,class,arch,phys,val]*[,tagn]`——LSU 指令在
  地址生成/访存阶段读到被 tag 的 vaddr 时，该提交行追加 `tagn`（tag 编号）。
- tag 生命周期：注入器创建 tag（fault vaddr + 世代号）；比较器在 LSQ
  sendFragmentToTranslation / AGU 输出处比对（已有 hook 点，W4/W5 系注入
  器本就改写这些数据通路）；tag 随 vaddr 被覆写而消亡（与 L0
  overwritten 生命周期对齐）。
- L3 语义升级：`method="propagation_tag"`，`evidence={n_tagged_commits,
  first_tagged_seq, distinct_pcs}`；`chain_complete` 对 activated>0 样本方可
  为 true（OBS 计划 T2 规则同步修订）。
- fanout.py 保留为 PRF 专用 proxy 工具，不在 LSU 轨道使用。

## 4. 重编与验收纪律（硬约束）
1. 前置：`pgrep -f gem5.opt` 为空且 4 个 AGU driver 已全部退出（PID
   1995570/1995598/1995622/1995696 终态）；`lsu_guard.py acquire --type build`
   拿单实例 build 锁。
2. `cd CHAOS/gem5 && scons -j16 build/ARM/gem5.opt`（增量；全量同理 -j16）。
   构建零新警告（CLAUDE.md patch 纪律）。
3. 新二进制 sha256 记录并**更新全部观测身份**（baseline_key 变化 → golden
   全部重跑；Phase A golden 缓存自动失效——这正是 baseline_key 设计目的）。
4. 旧冻结二进制的在途结果不受影响（目录身份记录各自 sha256）。
5. 验收口径：
   - W1 单样本窗口 ctrace gz ≤ 2GiB、msnap ≤ 512MiB（预算内）；
   - 窗口头行存在且可解码；commit_diff 对窗口前缀正常（截断语义扩展测试）；
   - `coverage_scope` 写入 observation.json 并通过 lsu_audit；
   - 短流载体回归：full 模式结果与 Phase A 同 seed 逐字节一致（窗口参数
     关闭时行为不变——`activatedMode=false, startTick=0` 必须是严格 no-op）。
6. 传播 tag 落地后：E2E 增补一个"SDC 样本 L3=propagation_tag 且
   chain_complete=true"用例，全链准入才算对 activated>0 样本开放。

## 5. 排期依赖
- Phase B-1（窗口）：C++ 4 文件 ×2 观测器 + 注入器回调 + 配置旗标 + 单测；
  依赖 AGU 批次全部结束（当前 ETA 2026-10-15 前后，以实际为准）。
- Phase B-2（传播 tag）：独立后续计划（one-patch-per-unit 拆分），
  依赖 B-1 验收 + 用户对 chain_complete 规则修订的确认（涉及验收口径
  语义变化 → 按协议请求中央决策）。
