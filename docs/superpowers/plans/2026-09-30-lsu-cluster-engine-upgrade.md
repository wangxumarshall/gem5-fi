# 计划：LSU 引擎集群化升级（4 槽位并行 + 样本续跑 + 兼容运行时接线）

> **2026-09-30 18:10 修订（范围变更，先改计划再执行）：** 推送时发现旧会话失联前已在
> origin 交付 F-022 引擎升级（4e16c701..f0a5b249）：Patch A 守卫 4 槽位、Patch B 并行
> 样本 + resume + census 持久化、G0-10 复验（隔离/mock 测试齐全，实机波次 4 刚启动即
> 失联）。本计划 **U2/U4/U5 被其覆盖（superseded）**，不再实施；U1 改为"移植到 4 槽
> 守卫"；U3/U6 保留。合并经 rebase，F 编号让位：本会话发现重编为 F-026/027/028。
> superseded 证据：docs/gem5-fi/lsu/evidence/P3/f022_patch_{a,b}_test.txt。

- **日期：** 2026-09-30
- **背景（为什么）：** 平台已迁移至集群节点 cn23423（keeper job 1773102）。gem5 二进制在
  glibc-2.38 主机上构建，集群为 Kylin glibc-2.34，经 compat loader 运行时（F-023）冒烟
  PASS。用户指令（F-022，2026-09-30 14:30）要求：实验并发硬上限 4（不同 ITEM/RunID/sample
  允许并行）、升级路线 = 守卫 4 槽位实验锁 + unit_pilot 并行样本(≤4) + 样本级 resume →
  G0-10 复验。另发现：集群节点无 swap（swap_total=0），现守卫 SwapFree<4 门禁将永久阻断
  一切实验（F-024）——需按资源指令意图（swap 是内存压力信号）实现 N/A 语义。
- **范围：** tools/lsu_guard.py、tools/lsu_runner.py、tools/lsu_unit_pilot.py 及验证证据。
  不改注入器 C++、不改配置、不改清单/Excel、不改 seed 规则（并行不改变单样本确定性：
  seed 由 RunID|phase|sample_index 决定，与执行顺序无关）。

## 单元分解（one patch per unit）

### U1 守卫无 swap N/A 语义
- 文件：`tools/lsu_guard.py`
- 改动：`snapshot()` 增加 `swap_na`（swap_total_gib==0）；`cmd_gate()` 与 `monitor()`
  在 swap_na 时跳过 SwapFree 门禁/TRIP 判据（原因字段记录 swap_na 而非静默）。
  MemAvailable 门禁（12 GiB）与 TRIP（8/6 GiB）不变。
- 验证（真实命令）：
  - [x] `python3 tools/lsu_guard.py gate` 于 cn23423（真实无 swap 节点）→ `ok:true`，notes=['swap_na: SwapTotal=0，SwapFree 门禁 N/A（F-024）']，mem_avail=526.11（evidence/P3/u1_gate_cn23423.out）
  - [x] `python3 -m py_compile tools/lsu_guard.py` → RC 0
  - 补充事实：login01 亦无 swap（全集群无 swap）；login01 回归 = 编译进程门禁照常拦截（evidence/P3/u1_gate_login01.out）；"有 swap 正路径" 无真机可验，以代码路径审查覆盖（if/elif 分支，正路径未变）
- 回归：login01（有 swap）gate 行为不变（SwapFree 判据仍生效）。

### U2 守卫 4 槽位实验锁
- 文件：`tools/lsu_guard.py`
- 设计：实验锁池 = `experiment.lock`（槽 0，兼容旧名）+ `experiment_slot{1,2,3}.lock`；
  槽数上限硬编码 4（用户指令硬上限）；`acquire/run` 支持 `--slots N`（默认 4，1..4）。
  - acquire：找第一个空闲槽（无文件或死 pid 拒绝该槽并试下一槽；全忙→REFUSED）；
    O_EXCL 冲突（并发双取）捕获 FileExistsError 重试下一槽。
  - release：默认释放"pid 属于自己或 --slot 指定"的槽；run 子命令在锁内记录 slot。
  - status：列出全部实验槽。
  - `_log_event` 加 fcntl.flock（多进程并发追加防交错）。
  - build 锁语义完全不变（单实例，-j8 规则不受影响）。
- 验证：
  - [ ] 槽测试脚本 `evidence/P3/guard_slots_verify.sh` 全 PASS：T1 4 槽并发 `guard run sleep 5`
        全成功且槽互异、完成后全释放；T2 第 5 个并发 acquire REFUSED；T3 伪造死 pid 陈旧槽
        → 其他槽可用、clear-stale 按槽处置；T4 --slots 2 时第 3 个 REFUSED。
  - [ ] `python3 -m py_compile tools/lsu_guard.py` → RC 0
- 回归：单槽（--slots 1）行为与旧版一致（串行双跑语义）。

### U3 gem5 调用路径可配置（compat 运行时接线）
- 文件：`tools/lsu_runner.py`、`tools/lsu_unit_pilot.py`
- 改动：`lsu_runner.gem5_bin()` = env `LSU_GEM5_BIN`（默认 `REPO/build/ARM/gem5.opt`）；
  替换 5 处直接引用（runner 2 处、unit_pilot run_one/census 2 处 + 文档串）。manifest 的
  `gem5_opt_sha256` 仍对真实二进制计算，另增 `gem5_invocation` 字段记录实际调用路径
  （审计：wrapper 与二进制分离可见）。
- 验证：
  - [ ] `LSU_GEM5_BIN=/home/share/suke/wangxu/lsu_keeper/gem5.sh` 下于 cn23423 真实跑
        `guard run --type experiment -- lsu_keeper/gem5.sh ... hello` 冒烟 exit 0
  - [ ] 不设 env 时 dry-run 命令串不变（默认路径）→ `python3 tools/lsu_runner.py ... --dry-run`
- 回归：py_compile 两文件 RC 0；dry-run 输出与改前逐字节一致（除新增字段）。

### U4 unit_pilot 样本级 resume + census 持久化
- 文件：`tools/lsu_unit_pilot.py`
- 改动：样本 s 开始前若 `{it}_s{s}/l5_verdict.json` 存在且可解析且无 `error` 键 → 直接
  载入计数（日志标 `resume`），不重跑（确定性 seed 保证与重跑等价，省算力）；census 结果
  写 `{it}_census/census.json`，重入时复用。ITEM 终态跳过逻辑不变。
- 验证：
  - [ ] 构造真实场景：首个 ITEM 正式跑若干样本后中断 → 重启 unit_pilot → 日志显示
        已有样本 `resume` 载入（guard_events.log 无对应新 spawn），新样本继续
  - [ ] py_compile RC 0
- 回归：无既有样本目录时行为与旧版一致。

### U5 unit_pilot 并行样本（≤4）
- 文件：`tools/lsu_unit_pilot.py`
- 改动：`--parallel N`（默认 4；1..4；同时受守卫 `--slots` 约束，实际并发 = min）。
  ThreadPoolExecutor（subprocess 释放 GIL）调度 run_one；单 ITEM 内样本并行，ITEM 间仍
  串行（单元波次语义不变）。停止规则：activated ≥ 30 时不再提交新样本，已在途样本自然
  完成并全部入账（可能小幅超出 30，如实记录——不丢弃数据）；attempted 上限 300 不变。
  每 sample 独立 outdir/rsrc.log/guard.out/槽位租约（U2）。
- 验证：
  - [ ] `--parallel 4` 真实跑一个 F0 ITEM（如 ITEM-001 A01-F0-W3）→ 30 activated，
        守恒 OK，`guard status` 过程中可见 ≤4 实验槽同时占用
  - [ ] `--parallel 1` 与升级前串行结果逐样本一致（确定性：l5_verdict outcome 序列相同）
  - [ ] py_compile RC 0
- 回归：`--dry-run` 准入输出与改前一致。

### U6 G0-10 复验 + 文档
- 文件：`evidence/P3/*`、`docs/gem5-fi/lsu/{findings,progress,task_plan}.md`
- 改动：汇总 U1-U5 证据，G0-10 门禁重验记录（守卫升级后资源防护仍成立），更新
  findings（F-023..F-026）与 progress Session 002。
- 验证：
  - [ ] evidence/P3/guard_slots_verify.out 全 PASS
  - [ ] task_plan G0-10 行更新且有证据路径
  - [ ] git log 每单元一 commit、均已推送 origin/fi-ding

## 提交与推送
- 每单元：实现 → 自验证（真实命令+引用输出）→ commit（[LSU][P3] 前缀，不含
  Co-Authored-By: Claude 结尾）→ 经 Windows 中继推送 origin/fi-ding。
- 中继：cluster 无外网；Windows 侧 `git fetch nscc:repo fi-ding` → 本地快进 →
  `git push origin fi-ding`（github 走 ssh.github.com:443）。
