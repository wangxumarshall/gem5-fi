# F-022 引擎升级计划：守卫 4 槽位实验锁 + unit_pilot 并行样本 + 样本级 resume

日期：2026-09-30　作者：服务器执行 AI（会话 002）
依据：用户指令 2026-09-30 14:30（findings.md F-022 / task_plan D-2026-09-30-并发）——
gem5 实验并发硬上限由 1 调整为 4；不同 ITEM/RunID/sample 允许并行；每个并行实验
独立 run_key/manifest/输出目录/日志/worker lease/PID-PGID/心跳；不得为满足上限杀死健康实验。

## 背景

- P3 波次 3 已恢复（单实例引擎，commit 4e16c701 F-023 加固版）。AGU 剩余
  ITEM-009..039 中 ELIGIBLE 23 项，多数为 300-attempted F2/F6 项（~45-60s/run），
  单实例预估 20-40 小时；4 并发可压缩至 ~1/4。
- F-023 教训（必须遵守）：lsu_guard.py 被 pilot 每 run 重新加载（子进程），
  lsu_unit_pilot.py 被 bash 链逐单元重新加载——**波次运行期间严禁编辑这两个
  文件**；升级一律在 tools/draft/ 隔离副本开发，验证后停波次一次性切换。

## 现状协议（读码确认）

- 锁：`runs/lsu/guard/{build,experiment}.lock`，acquire 用 O_EXCL 原子创建，
  release 删除文件；cmd_run = gate(子进程) → acquire(子进程) → spawn(新会话)
  → monitor(60s 采样+WARNING/TRIP) → release(子进程，按 type 定位)。
- 引擎（lsu_unit_pilot.py）：单线程逐样本 run_one；F0 两遍法 census 每 ITEM 一次
  （span 内存态，重启即丢）；断点续跑只跳过 COMPLETE/BLOCKED 的 ITEM，
  无样本级 resume（ITEM 重跑从 s0 覆盖）。

## 设计

### Patch A — tools/lsu_guard.py：experiment 4 槽位锁

- 锁文件：`experiment_slot_{0..3}.lock`（build.lock 不变，仍单实例）。
- `acquire --type experiment`：按 slot 0→3 顺序找空槽，O_EXCL 创建；EEXIST
  （并发撞槽）自动试下一槽；全部占用 → REFUSED（列出现持锁 pid/desc）。
  锁 JSON 增加 `"slot": N`；acquire 成功 stdout 输出锁 JSON（含 slot）。
- 陈旧槽（pid 死）：与现状一致 REFUSED 并提示 clear-stale（不得自动清）。
- `release --type experiment --slot N`：校验锁内存 pid 与调用者传 `--confirm-pid`
  （cmd_run 内传 spawn 后记录的 pid）一致才删，防并行误删他人槽；不匹配 → REFUSED。
- `clear-stale --type experiment --confirm-dead-pid M`：扫描全部槽，删除 pid==M
  且已死的槽；报告其余槽状态。
- `status`：列出 4 槽各自状态 + build 锁 + 资源快照。
- `gate`：资源逻辑不变（全局水位对 4 并发同样生效）；增加"实验槽占满"提示
  （不作为 gate 失败理由——acquire 自会拒绝；gate 只管资源与环境安全）。
- `GUARD_DIR` 支持环境变量 `LSU_GUARD_DIR` 覆盖（默认不变）——隔离测试必需，
  避免测试污染真实锁目录与 guard_events.log。
- monitor/TRIP 逻辑零改动（每 run 独立 monitor 自己的 pgid，天然多实例安全）。

### Patch B — tools/lsu_unit_pilot.py：并行样本 + 样本级 resume

- `--workers N`（默认 1 = 现行为）；ThreadPoolExecutor 派发 run_one。
- F0 两遍法：census 串行先行（一个实验槽），span 持久化到
  unit_status.items[it]["census_n"]；resume 时复用（F-013 已证 N 与 seed 无关）。
- 样本级 resume：ITEM 开始时扫描 `{it}_s{N}/l5_verdict.json` 存在、无 "error"、
  且配对 `_guard.out` 含 run-finish → 该样本复用（verdict 计入 runs），新样本
  从已完成的最大 s+1 派发。attempted 计数含 resumed（真实 attempted）。
- 派发停止：activated ≥ 30 停止派发新样本；在飞样本跑完计入（audit 诚实记录
  attempted/activated；COMPLETE 判定 activated ≥ 30，统计口径不变——超采的
  activated 同为真实独立样本）。
- GuardFailure（F-023 语义保持）：任一 future 抛出 → 停止派发 + 等待在飞
  futures 完成（其 verdict 有效保留）→ ITEM 记 GUARD_FAILURE → 单元中止。
- 每 run 独立 outdir/manifest/seed/guard 锁槽/日志（F-022 逐实验独立性要求）。

## 验证（draft 目录 + LSU_GUARD_DIR=/tmp/f022_guard_test，不碰真实锁）

- [ ] A-T1 语法 + `status` 新格式
- [ ] A-T2 4 并发 acquire 全成功；第 5 个 REFUSED 并列出占槽者
- [ ] A-T3 release --slot 正确；--confirm-pid 不匹配 → REFUSED
- [ ] A-T4 伪造 stale 槽 → clear-stale 清除；存活 pid 槽拒绝清
- [ ] A-T5 并发撞槽（两个 acquire 同时）O_EXCL 无双取
- [ ] B-T1 py_compile + --dry-run 与现行为一致
- [ ] B-T2 resume：构造带有效 verdict 的假样本目录 → 复用、不重跑（mock run_one 计数）
- [ ] B-T3 派发停止：activated 达 30 后不再派发（mock run_one 返回 activated=1）
- [ ] B-T4 GuardFailure 中止语义（mock run_one 抛 GuardFailure → GUARD_FAILURE + 单元 return）
- [ ] 切换后实机验证：4 并发真实 run（4 槽占用、guard_events 交错 acquire/
      run-finish/release、ITEM-009 resume 跳过已完成样本）；资源首 30 分钟
      密切采样（4×gem5 RSS、MemAvailable 水位，须远高于 WARNING 10 GiB）

## 切换流程（一次停机窗口）

1. draft 全部测试 PASS →
2. 停波次：TERM bash 链 + unit_pilot（在飞 run 的 guard 独立进程跑完自释放；
   等待 4 槽空 + 无 gem5 进程，最多等 10 分钟）→
3. 资源门禁采样 → 替换 tools/ 两文件 →
4. commit（Patch A、Patch B 各一个 commit，one-patch-per-unit）→ push →
5. 重启波次 4（--workers 4）→ 实机验证 → G0-10 复验记录（task_plan 门禁表
   + findings F-024）→ progress 更定 + 文档 commit。

## 明确不做（防范围蔓延）

- 不改 gate 资源阈值、不改 WARNING/TRIP 逻辑、不改统计口径/audit 守恒。
- 不做跨 ITEM 并行（单 unit_pilot 内 ITEM 仍串行、样本级并行——波次 bash 链
  的单元顺序保持）。
- 不做 build 锁多实例（编译仍 -j8 单实例，用户指令明确编译规则不变）。
