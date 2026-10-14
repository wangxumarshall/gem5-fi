# OOO L0-L5 观测链 + 全局守卫调度 + 准入门 + 四 formal（D01-c/D02-b/D02-c/D04-d）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task（用户已指定：本会话自行实施，逐任务提交；不使用 subagent-driven）。Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 huawei0201 上把 OOO 故障注入轨道的四个待跑 formal RunID（`D01-F0-W6-c`、`D02-F0-W6-b`、`D02-F0-W6-c`、`D04-F0-W4-d`）以**可审计 L0-L5 全链观测**、**host 全局 6→8 槽守卫调度**、**小样本准入门**的方式跑完，每 RunID 385 个有效唯一样本，产出 handoff；不改 Excel、不动 D05-b/c、不碰已有结果。

**Architecture:** 全部为 Python/配置层改动（**零 C++ 改动，gem5.opt 冻结 `1a618953…0bf3`**）。四个新工具构成执行面：`ooo_guard.py`（host 原子槽锁 + (campaign,run,sample) claim 锁 + 60s 资源监控）、`ooo_golden.py`（baseline_key 一次生成 no-fault golden 并缓存）、`ooo_sample_runner.py`（单样本：staging→runner.py(ctrace+msnap)→离线 L0-L5 差分→observation.json→原子 rename→COMPLETE）、`ooo_scheduler.py`（6→8 槽守护调度 + 补足 + handoff）。复用既有 `runner.py`/`classify.py`/`campaign.manifest_for_cell`/`commit_diff.py`/`micro_diff.py`/`fanout.py`——一个映射器一个分类器，零漂移。

**Tech Stack:** Python 3.11 stdlib + PyYAML 6.0.3 + jsonschema（已实测可用；**pytest 不可用** → 全部测试为 plain-python 断言脚本，`python3 tools/tests/test_*.py` 直接运行，风格对齐既有 `tools/tests/test_faults_log_contract.py`）。

**Spec:** 用户指令（2026-10-12 会话，任务书全文见本计划附录 A 摘要）；`docs/gem5-fi/ooo/总方针.md`（科学规则与资源纪律，其中并发≤4 的旧上限被用户最新指令 6→8 覆盖，以用户指令为准）；`CLAUDE.md` patch discipline。

## 执行状态（2026-10-12 18:00 起实时更新；两阶段 subagent 模式）

- **模式切换**：按用户新指令改为两阶段并行。Task 1-4 的代码部分已由总负责人直接完成并提交（70eb582 计划、0f7029d guard、63be59f runner --msnap、7a06677 commit_diff --seq-range、58d26fe ooo_golden、c577d26 ooo_handoff）；Task 4 的真 golden 生成、Task 5/6（observation/sample_runner）转 Subagent-A；Task 9（scheduler+竞争/降档测试）转 Subagent-B；Task 7/8（E2E/审计）转 Subagent-C。三 subagent 各自 worktree/分支（ooo/l0l5-{A,B,C} @ .claude/worktrees/ooo-l0l5-{a,b,c}），文件所有权互斥，由总负责人审查合并。
- **Task 状态**：T0 ✅ / T1 ✅（26 检查 ALL PASS + selftest + monitor 实测）/ T2 ✅（16 检查 ALL PASS，含截断诚实路径与 no-inject 309 行×16 列完整快照；共享文件回归 PASS）/ T3 ✅（16 检查 ALL PASS；TDD 抓出生成器函数吞迭代器真 bug 并修复）/ T4 代码 ✅ 单测 ALL PASS，**四个真 golden 生成 + verify2 → Subagent-A** / T5-T9 → subagent 进行中 / campaign 规格（eng2×4+formal×4+batch）已按冻结面草拟于 runs/ooo-l0l5/specs/（chaos_commit 与 coremark l2_mode 待准入门定值）。
- 阶段一验收屏障 A-J 见用户指令；全部 PASS 后自动进入阶段二（RunAgent-A/B/C/D，6→8 槽）。



1. **binary 冻结**：全部运行使用 `build/ARM/gem5.opt` sha256 `1a618953b014514713c0ad98c7f3d69a48171d81f0463d934bccdfcfc0070bf3`；任何代码不得改 `CHAOS/gem5/src/**`（验收：`git diff f2ee885 -- CHAOS/gem5/src` 为空）。运行期间禁止替换 binary。
2. **基点**：开发分支 `ooo/l0l5-chain` 自 `f2ee885853abd19e1f05f5fa7fe094804d0640ce` 创建；运行冻结 commit = 准入门（Task 10）PASS 后的分支 HEAD，记入每样本 observation。
3. **输出路径**：所有实验输出写 `/home/sdc/gem5-fi-ding/runs/...` 与 `/home/sdc/gem5-fi-ding/artifacts/...`（绝对路径）；trace/msnap/临时文件**禁止写 /tmp**（runner 子进程用 `TMPDIR=<staging>/tmp`）。
4. **不覆盖**：绝不写/删任何既有 `runs/*`、`artifacts/*`、Excel、m5out；新目录名不得与现存目录重名（`runs/ooo-l0l5/`、`runs/eng2_*`、`runs/formal_{D01-F0-W6-c,D02-F0-W6-b,D02-F0-W6-c,D04-F0-W4-d}/` 均已核实现不存在）。
5. **种子纪律**：formal 沿用 Session 005b 预冻结 seed：D01-c=44072336、D02-b=41211122、D02-c=47470573、D04-d=42729898（manifest seed = base+rep，rep∈[0,385)）；补足 seed = base+1,000,000+round*1000+rep（rep 从 385 续）；eng2 seed = 52000000+k*1000+rep（k=0..3 按 RunID 顺序）。全部在 campaign yaml 冻结，禁止看结果换 seed。
6. **PYTHONHASHSEED=0**：fault/ref/差分全部子进程强制 `PYTHONHASHSEED=0`（`env["PYTHONHASHSEED"]="0"`，非 setdefault）。
7. **诚实规约**：未实现能力写 `n/a`/`unsupported` + 原因，绝不静默 0/假报；gzip 截断保留可读前缀并标 `truncated`；Crash 前无错误提交写 `not_observed_before_crash`；L3 fanout 仅 PRF 可用且标 `method=proxy`+caveat，decode/rat 等非 PRF 一律 `unsupported` 且 `chain_complete=false`；SimulatorError/INVALID 不计入 385 有效数。
8. **一个分类器**：分类一律经 `tools/classify.py::classify_run`（runner.py 内部已如此）；L5 九分类词汇表 = `tools/wilson.py::ALL_CLASSES`。
9. **提交纪律**：每任务一提交（`[OOO][P?] <unit>` 前缀，无 Co-Authored-By 尾行），提交前 100% 真实验证（构建零警告不适用——纯 Python；功能性验证 = 实跑命令引用真实输出）；只 `git add` 明确路径，**绝不 `git add -A`**；**不 push**（协调者做 Git 集成）。
10. **槽位纪律**：准入门 PASS 前全机 gem5 并发 ≤4；PASS 后 formal 初始 6 槽（A/B/C 各 2，NUMA 3+3），稳定 15min + MemAvailable>12GiB → 加 D 至 8（4+4）；MemAvailable<10GiB 或持续 swap/blocked → 停新派发降 6/4；**绝不超过 8**。
11. **共享文件**：不写 Excel；不改 `docs/gem5-fi/ooo/progress.md`（属主是主协调流程，本计划报告写到 `docs/gem5-fi/ooo/l0l5-*.md` 新文件）。
12. **worktree**：开发在 `.claude/worktrees/ooo-l0l5`（分支 ooo/l0l5-chain）；`build/ARM` 已符号链接到主仓物理构建目录（同 inode，sha 已复核=1a618953）；工具内一切输出路径用绝对路径参数化，不依赖 `REPO` 推导输出位置。

## Review Focus（最可能咬人的五类输入/失败模式 → 对应任务测试）

1. **Crash 样本的 gzip 截断 ctrace/msnap**（gem5 SIGABRT 跳过 gz trailer）→ 差分器必须救回可读前缀并标 truncated，绝不能假报 no divergence（Task 5 fixtures T-crash；Task 7 真 Crash E2E 复核）。
2. **stale 锁回收误杀**（PID 复用：新进程恰好拿到旧 PID）→ 只允许 PID 存在**且** `/proc/PID` starttime 与锁内记录一致才判 stale（Task 1 T-reclaim 双字段负例）。
3. **同 seed 重放不一致**（环境/哈希种子/路径泄漏）→ observation 必须记录 `replay_determinism`，MISMATCH 是发现不是噪声（Task 6 replay 子命令；Task 10 8/8 门）。
4. **路径覆盖/串写**（两 worker 写同一目录、结果覆盖旧样本）→ per-sample 独立 staging + `os.rename` 原子落位 + COMPLETE 只读核验跳过（Task 1 claim 锁；Task 6 finalize 原子性测试；Task 10 无覆盖审计）。
5. **身份漂移**（运行中 binary/HEAD 被换、golden 与 binary 不配套）→ 每样本核对 gem5 sha256 == 冻结值、golden sidecar 的 gem5 sha 必须等于当次（Task 4 golden 侧车；Task 6 漂移即 loud fail；Task 11 调度器周期核验）。

---

### Task 0: 工作区就绪 + 审计快照 + 计划入库

**Files:**
- Create: `/home/sdc/gem5-fi-ding/runs/ooo-l0l5/audit/session-2026-10-12.md`（runs/ 未跟踪，仅落盘不提交）
- Create: `docs/superpowers/plans/2026-10-12-ooo-l0l5-chain-admission-scheduling.md`（本文件）

**Interfaces:** 无代码；产出冻结基线记录（后续任务的哈希引用源）。

- [x] **Step 1: 建 worktree/分支**（已完成，实测）：`git worktree add .claude/worktrees/ooo-l0l5 -b ooo/l0l5-chain f2ee885`；`build/ARM -> /home/sdc/gem5-fi-ding/CHAOS/gem5/build/ARM`；`sha256sum build/ARM/gem5.opt` = `1a618953…0bf3` ✓。
- [x] **Step 2: 写审计快照**：hostname/HEAD/branch/status 摘要/gem5.opt sha/资源/进程/RunID 计数（本会话 15:51-16:10 实测值）→ `runs/ooo-l0l5/audit/session-2026-10-12.md`。
- [x] **Step 3: 本计划文件提交**：`git add docs/superpowers/plans/2026-10-12-ooo-l0l5-chain-admission-scheduling.md && git commit -m "[OOO][PLAN] L0-L5 chain + guard scheduler + admission + 4 formals implementation plan"`。

### Task 1: `tools/ooo_guard.py` — host 全局槽锁/claim 锁/资源监控

**Files:**
- Create: `tools/ooo_guard.py`
- Test: `tools/tests/test_ooo_guard_l0l5.py`

**Interfaces:**
- Produces（后续任务按此调用）:
  - `GUARD_DIR` 默认 `/home/sdc/gem5-fi-ding/runs/ooo-l0l5/guard`
  - `class GuardError(Exception)`
  - `proc_starttime(pid) -> int | None`（读 `/proc/<pid>/stat` 第 22 字段；进程消失返回 None）
  - `slot_acquire(guard_dir, owner, campaign, run_id, max_slots, node=None) -> SlotHandle`：原子 `os.open(path, O_CREAT|O_EXCL|O_WRONLY)` 创建 `slots/slot_<i>.lock`，写入 JSON `{owner, pid, pgid, starttime, node, campaign, run_id, acquired, heartbeat}`；全满→`GuardError("slots full")`。**先写 `slots/.tmp_<pid>_<i>` 再 `os.link` 原子占位** 或直接 O_EXCL 均可，但锁文件内容必须一次 write+fsync。
  - `slot_release(handle)`：校验锁内 pid+starttime 与当前进程一致（不一致 loud fail，防误放他人锁）→ unlink。
  - `slot_heartbeat(handle)`：锁内 JSON 原地更新 heartbeat（写临时文件 + `os.replace` 保持原子，锁身份字段不变）。
  - `slot_status(guard_dir) -> dict`：逐槽读锁 + `pid_alive = pid 存在 and starttime 一致`；不主动回收。
  - `slot_reclaim_stale(guard_dir) -> list`：仅当 `pid 不存在 OR starttime 不一致` 判 stale → 移到 `slots/stale/`（保留证据不删除）。**PID 存在且 starttime 一致 → 绝不回收**。
  - `claim_acquire(guard_dir, key) -> bool`：`claims/<key>.claim` O_EXCL 原子创建（key 格式 `<campaign>__<run_id>`）；已存在→False。`claim_release(guard_dir, key)`。
  - `golden_claim_acquire/release(guard_dir, golden_key)`：同 claim，目录 `goldens/`。
  - `sample_resources() -> dict`：`{mem_available_kib, swap_free_kib, swap_in, swap_out(自 /proc/vmstat pswpin/pswpout 累计值), load1, load5, load15, blocked, disk_free_bytes(path), gem5_pids, gem5_rss_kib, ts}`（blocked = /proc/loadavg 第 8 字段减 running；gem5 进程 = `pgrep -f build/ARM/gem5.opt` 逐个读 /proc/PID/stat RSS 之和——**用 os.listdir('/proc') 实现，不 shell out**）。
  - CLI：`status` / `monitor --interval 60 --log <path>`（追加 CSV 行）/ `reclaim-stale` / `selftest`。
- Consumes: 无。

- [x] **Step 1: 写失败测试** `tools/tests/test_ooo_guard_l0l5.py`：临时 `GUARD_DIR=tempfile.mkdtemp()`；用例：
  1. `test_slot_acquire_release`：max_slots=2，两个不同 owner 各拿 1 槽成功，第 3 个 `GuardError`；release 后可再拿。
  2. `test_slot_no_steal`：进程 A（用 subprocess 拿锁后退出）… 简化：锁文件伪造 pid=999999（不存在）→ `slot_reclaim_stale` 回收；伪造 pid=1（存在）但 starttime 不匹配 → 回收；pid=1 且 starttime=真实 /proc/1 starttime → **不回收**。
  3. `test_slot_release_foreign`：锁属 pid=1/starttime=真 → 本进程 release 必须 raise（不放他人锁）。
  4. `test_claim_exclusive`：同 key 二次 acquire=False；不同 key 互不影响。
  5. `test_resources_shape`：`sample_resources()` 返回 dict 含全部键且 `mem_available_kib>0`。
  6. `test_slot_json_fields`：锁 JSON 含 owner/pid/pgid/starttime/heartbeat/campaign/run_id。
- [x] **Step 2: 跑测试确认失败**：`python3 tools/tests/test_ooo_guard_l0l5.py` → `ModuleNotFoundError: No module named 'ooo_guard'`（实测红态）。
- [x] **Step 3: 实现 `tools/ooo_guard.py`**（~470 行；TDD 抓出 slot_release mine 分支漏 unlink 的真 bug 并修复）。
- [x] **Step 4: 跑测试通过**：`python3 tools/tests/test_ooo_guard_l0l5.py` → 实测 `ALL PASS`（26 检查项）。
- [x] **Step 5: 实机验证**：`python3 tools/ooo_guard.py selftest` → 实测 `[selftest] PASS`（MemAvail=26719MiB gem5=0）；monitor --interval 1 后台 3.2s → resources.log 实测 5 行（表头+4 采样）。
- [x] **Step 6: Commit**：`git add tools/ooo_guard.py tools/tests/test_ooo_guard_l0l5.py && git commit -m "[OOO][P1] host-global slot/claim guard with PID+starttime stale reclamation and 60s resource monitor"`。

### Task 2: `tools/runner.py` 增加 `--msnap`（L1 观测旗标，向后兼容）

**Files:**
- Modify: `tools/runner.py`（argparse 区 ~L437 后加 3 个参数；ctrace 使用段 ~L1482 与 ~L1602 加 msnap 分支；**不动其他任何行**）

**Interfaces:**
- Produces: `runner.py <manifest> --binary B --msnap <PATH> [--msnap-every N]`：`PATH` 转绝对路径 → gem5 cmd 追加 `--chaos_msnap --msnap_file <ABS> --msnap_every N`（默认 1000）；运行后打印一行证据 `[runner] MSNAP: file=<ABS> lines=<N|unreadable> bytes=<B>`（lines 用既有 `count_trace_lines`；无 `--msnap` 时**字节零新增**）。
- Consumes: `configs/se/ooo_proxy.py` 既有 `--chaos_msnap/--msnap_every/--msnap_file`（L419-423，无需改）。

- [x] **Step 1: 写失败测试** `tools/tests/test_runner_msnap_flag.py`：
  1. `test_flag_absent_no_msnap_line`：手工构造 smoke manifest（workloads/ooo/smoke/smoke, golden_id=smoke-golden-v1, config_family C3, injector decode+sub_field=imm_bitflip, trigger cycle 1000, seed 20261012, max_faults 1）→ 实跑 `python3 tools/runner.py <m.yaml> --binary workloads/ooo/smoke/smoke`，断言 stdout 有 `RESULT:` 行、classification=Masked 或 Inactive（smoke 308K insts，decode 首钟 1000 必激活→期望 Masked/Crash 之一，记录实测）、**无 `MSNAP:` 行**。
  2. `test_flag_present_msnap_line`：同 manifest 加 `--msnap /home/sdc/gem5-fi-ding/runs/ooo-l0l5/selftest/msnap.csv.gz` → 断言有 `MSNAP: file=...` 行且 `lines>=1`、文件存在、`zcat | head -2` 首行 `#` 注释 + 表头符合 micro_diff 16 列契约；**且 RESULT classification 与无旗标运行一致**（msnap 只读契约——ooo_proxy L415 注释的硬门）。
  3. `test_msnap_requires_c3`：构造 config_family C0 的 manifest（binary_sha256 留空），`--msnap` → 退出非 0 且 stderr 含 "C3/C4-LSU"（镜像 --ctrace 的早失败模式）。
- [x] **Step 2: 跑测试确认失败**：实测 run2 `unrecognized arguments: --msnap`（红态），run1 传统路径正常。
- [ ] **Step 3: 实现**：argparse 加 `--msnap/--msnap-every`；在 `if args.ctrace and cfg_family not in ("C3","C4-LSU")` 早验证旁加同款 msnap 校验；cmd 构造段（ctrace 追加点后）加：
```python
if args.msnap:
    msnap_path = os.path.abspath(args.msnap)
    cmd += ["--chaos_msnap", "--msnap_file", msnap_path,
            "--msnap_every", str(args.msnap_every)]
    print(f"[runner] msnap: {msnap_path} every={args.msnap_every}")
```
  末尾证据段（`if args.ctrace:` 块后）加：
```python
if args.msnap:
    msnap_path = os.path.abspath(args.msnap)
    if os.path.exists(msnap_path):
        n = count_trace_lines(msnap_path)
        print(f"[runner] MSNAP: file={msnap_path} "
              f"lines={n if n is not None else 'unreadable'} "
              f"bytes={os.path.getsize(msnap_path)}")
    else:
        print(f"[runner] MSNAP: file={msnap_path} MISSING")
```
- [ ] **Step 4: 跑测试通过**（两次真跑 smoke ~10-20s each）。
- [ ] **Step 5: 回归**：`git stash` 不用——直接 `git diff tools/runner.py` 人工核对只增不改；再跑 `python3 tools/tests/test_faults_log_contract.py` 确认仍 PASS（共享文件回归）。
- [ ] **Step 6: Commit**：`git add tools/runner.py tools/tests/test_runner_msnap_flag.py && git commit -m "[OOO][P1] runner.py --msnap L1 snapshot flag (read-only, byte-identical stdout when absent)"`。

### Task 3: `tools/commit_diff.py` 增加 `--seq-range`（窗口差分，默认关=字节不变）

**Files:**
- Modify: `tools/commit_diff.py`（argparse 加 `--seq-range LO:HI`；读取侧在 parse 时跳过 `seq<LO`、`seq>HI` 早停；docstring 记录窗口语义）
- Test: `tools/tests/test_commit_diff_seqrange.py`

**Interfaces:**
- Produces: `commit_diff.py --ref A --run B --seq-range 100:200 --json out.json` → JSON 额外含 `"seq_range": {"lo":100,"hi":200}`，仅比对 seq∈[lo,hi]，窗口内无分歧时 verdict 仍按原规则（tick-tol 等不受影响）；**不带旗标时行为/JSON 与旧版逐字节一致**（除无新键）。窗口截断**不是** no_divergence 的新证据——JSON 里 `coverage_note: "diff restricted to seq [lo,hi]; divergence outside window unobserved"`。
- Consumes: 既有 trace 格式与合并逻辑（`load`/`merge` 不动核心，仅在行迭代处加过滤）。

- [ ] **Step 1: 写失败测试**：fixture 两个小 CSV（手工 10 行，seq 0..9，run 在 seq 7 有 val 差异）：① 无旗标 diff → primary_class=data_corruption、divergence_counts 计 1；② `--seq-range 0:5` → 无分歧 verdict（且 coverage_note 存在）；③ `--seq-range 0:9` == ①；④ 坏范围 `5:1` → exit 2。
- [ ] **Step 2: 确认失败**（unrecognized arguments）。
- [ ] **Step 3: 实现**（在两文件迭代函数加 `lo/hi` 参数，早停 `if seq > hi: break`；gzip 流按行读，早停即停）。
- [ ] **Step 4: 通过**：`python3 tools/tests/test_commit_diff_seqrange.py` → `ALL PASS (4 tests)`。
- [ ] **Step 5: 回归**：用 Task 4 将生成的 golden 自差分（ref==run 同文件）无旗标 → verdict 无分歧、JSON 无 seq_range 键（证明默认路径零变化）。
- [ ] **Step 6: Commit**：`git add tools/commit_diff.py tools/tests/test_commit_diff_seqrange.py && git commit -m "[OOO][P1] commit_diff --seq-range windowed diff (default off, byte-identical legacy path)"`。

### Task 4: `tools/ooo_golden.py` — baseline_key + no-fault golden 一次生成缓存

**Files:**
- Create: `tools/ooo_golden.py`
- Test: `tools/tests/test_ooo_golden_key.py`

**Interfaces:**
- Produces:
  - `baseline_key(spec: dict) -> str`：`spec = {gem5_sha256, config_path, config_sha256, workload_path, workload_sha256, argv_extra(sorted list), maxinsts, msnap_every, golden_id}` → sha256(json.dumps(spec, sort_keys=True)) 前 24 hex。
  - `ensure_golden(spec, runs_root, guard_dir, hang_timeout=650, force=False) -> GoldenHandle`：
    1. key=baseline_key(spec)；dir=`<runs_root>/ooo-l0l5/goldens/<key>/`；已有 `COMPLETE.json` → **只读核验**（sidecar gem5_sha256==spec、FINAL==GOLDEN_IDS[golden_id]）后返回句柄，不重跑。
    2. `golden_claim_acquire` 全局锁（防两 worker 并发生成）；无锁时阻塞等待 + 轮询 COMPLETE。
    3. staging 子目录内跑 `runner.py <no-inject manifest> --binary <wl> --ctrace <staging>/ctrace_ref.csv.gz --msnap <staging>/micro_snap.csv.gz --stats`，`--no-inject`，`PYTHONHASHSEED=0`，`TMPDIR=<staging>/tmp`。
    4. 校验：classification ∈ {Inactive, Masked}；FINAL checksum == `runner.GOLDEN_IDS[golden_id]`（**不一致 → loud fail**，golden 登记表与实测冲突=阻断事件）；ctrace/msnap lines>0 且可解析（`count_trace_lines`/micro_diff 载入）。
    5. 产物：`ctrace_ref.csv.gz`（**全量保留**，供逐样本窗口切片）、`micro_snap_ref.csv.gz`、`stats_ref.txt`、`runner.stdout/stderr`、`provenance.json`（spec 全文 + gem5_sha256 + created + FINAL + 各文件 sha256 + manifest 副本）、`COMPLETE.json`（原子写）。
    6. GoldenHandle = `{key, dir, ctrace_path, msnap_path, final_checksum, provenance}`。
  - CLI：`ensure --spec <yaml>`（spec yaml 即上述字段）。
- Consumes: `tools/runner.py`（--no-inject/--ctrace/--msnap/--stats）、`tools/ooo_guard.py::golden_claim_*`、`runner.GOLDEN_IDS`。

- [ ] **Step 1: 失败测试** `tools/tests/test_ooo_golden_key.py`：① `baseline_key` 对字段顺序不敏感、对任一字段变化敏感；② spec yaml round-trip。
- [ ] **Step 2: 确认失败**（模块不存在）。
- [ ] **Step 3: 实现**（~260 行）。
- [ ] **Step 4: 单测通过**。
- [ ] **Step 5: 实测三个真 golden**（这一步同时是 Task 6/7 的输入）：smoke（golden_id=smoke-golden-v1）、coremark（coremark-golden-v1）、dep_chain（depchainint-golden-v1）+ 第四个 dep_chain_vec（depchainvec-golden-v1，FR02 SDC E2E 用）。命令逐个执行并记录 wall time / ctrace 行数 / 字节数 / msnap 行数（**这些实测数字直接决定 Task 6 的 L2 窗口策略，写进实现笔记**）。二次调用 `ensure` 必须命中缓存（无第二次 gem5 运行——用运行计数器/时间戳证明）。
- [ ] **Step 6: 确定性双跑**：对 smoke golden 用 `force=True` 生成第二份到 `goldens/<key>.verify2/`，sha256(ctrace_ref) 两次完全一致（W2.1 同型验证）；不一致=阻断。
- [ ] **Step 7: Commit**：`git add tools/ooo_golden.py tools/tests/test_ooo_golden_key.py && git commit -m "[OOO][P1] one-shot cached no-fault golden per baseline_key with GOLDEN_IDS cross-check"`。

### Task 5: `tools/ooo_observation.py` — L0 解析 + observation.json 组装/校验

**Files:**
- Create: `tools/ooo_observation.py`
- Test: `tools/tests/test_ooo_observation.py`

**Interfaces:**
- Produces:
  - `parse_injection_log(path, component) -> dict`：读 runner.py L1525 同名日志（`LOG_FOR_COMPONENT` 表）；逐行解析 `Tick: N, k=v, ... faults_injected: N`（逗号分割 + `k=v`；`Tick:`/`Site:` 特例）；返回 `{"injected": 最终计数, "events": [行字典+raw], "skips": [行字典], "eligible_count": N|None(CHAOS_ELIGIBLE_COUNT), "attempted": None, "truncated": bool}`。未提供 funnel 计数 → None（诚实 n/a）。
  - `build_observation(ctx: dict) -> dict`：组装完整 observation（schema 见下）；`ctx` 含 identity/l0_raw/l1_diff/l2_diff/l3/l4/l5_raw/files/replay/coverage。**所有子块缺失时写 `{status:"error", reason}`，不静默省键**。
  - `validate_observation(obs) -> (bool, list[str])`：结构校验（必填键/类型）+ 守恒校验（`activated == 五类主结局之和 + post_activation_simulator_failure`，activated=0 时五类全 0 才过）+ 一致性（Inactive⇒activated==0；SDC⇒checksum≠golden；Masked⇒checksum==golden 且 activated≥1；Crash/Hang 允许无 L0 落地）。
  - `chain_completeness(obs) -> (bool, list[str])`：规则（逐条，任一不满足即 gap）：activated==0 → L1-L4 必须 `inactive_no_activation`，此时若全部如此则 complete=true（L0+L5 满）；activated≥1 → L1.status=="ok"、L2.status=="ok"、L4.status∈{ok,none_detected}、L5 有 classification 且守恒过；**L3：component=="physreg" → status=="ok" 且 method=="proxy"（chain_complete 仍 true，proxy 有 caveat 属实记录）；非 physreg → status=="unsupported" ⇒ chain_complete=false, gap=["L3"]（任务书规定，禁止冒充）**；violations 空。
  - observation.json schema（`OBSERVATION_SCHEMA_VERSION = "ooo-observation/v1"`，顶层键）：`schema_version, identity{...}, l0{...}, l1{...}, l2{...}, l3{...}, l4{...}, l5{...}, replay{...}, coverage_scope{...}, violations[], chain_complete, chain_gaps[], files{relpath:sha256}, audit{built_at, builder_sha256}`。
- Consumes: micro_diff/commit_diff/fanout 的 JSON（由 Task 6 产出文件后 `json.load`，本模块不跑子进程）。

- [ ] **Step 1: 失败测试**（fixtures 全部手工内联字符串，不依赖 gem5）：
  1. decode 成功行解析（真实行样例，来自 /tmp/man-a70h4p0y 实测）→ injected=1、event 含 pc/orig_enc/new_enc/bits。
  2. skip-only 日志（`... skip: single_contiguous_field, faults_injected: 0`×2）→ injected=0、skips=2、activated 侧=0。
  3. 截断 gz fixture（手工构造坏尾 gzip）→ l1/l2 的 truncated 路径（`load_truncated` 行为在 diff 工具内已有，这里测 observation 把 truncated 标志**透传**且 l2.status=truncated）。
  4. 守恒正/负例：activated=1 + Masked=1 → ok；activated=1 + 五类和=0 → violation。
  5. chain_completeness：decode activated 样本 → false + gap ["L3"]；physreg activated 样本（伪造 l3 ok+proxy）→ true；inactive 样本 → true（L1-L4 均 inactive_no_activation）。
  6. validate：SDC 但 checksum==golden → violation。
- [ ] **Step 2: 确认失败**。
- [ ] **Step 3: 实现**（~520 行）。
- [ ] **Step 4: 通过**：`ALL PASS (≥8 tests)`。
- [ ] **Step 5: Commit**：`git add tools/ooo_observation.py tools/tests/test_ooo_observation.py && git commit -m "[OOO][P1] L0-L5 observation assembly with conservation, truncation and chain_completeness semantics"`。

### Task 6: `tools/ooo_sample_runner.py` — 单样本执行器（staging→原子 COMPLETE→results.jsonl）

**Files:**
- Create: `tools/ooo_sample_runner.py`
- Test: `tools/tests/test_ooo_sample_runner.py`（smoke 实跑）

**Interfaces:**
- Produces:
  - CLI：`run --campaign-yaml <y> --rep N [--topup-round R] [--guard-dir G] [--runs-root R]`、`replay --sample-dir <d>`（同 manifest 重跑一次→回写 `evidence/replay/`+observation.replay）、`finalize-audit --campaign-dir <d>`。
  - 流程（`run`）：
    1. 读 campaign yaml（新 schema：既有字段 + `trace: {enabled: true, l2_mode: full|window, window_pre_seq, window_post_seq, msnap_every}` + `workload.binary_sha256` 实测值 + `chaos_commit` 冻结 sha + `patchset_sha256`）；**用 `campaign.manifest_for_cell` 生成 manifest**（cell=grid 展开，本计划全部单 cell）——topup 时 rep≥385 且 seed 公式见 Global Constraint 5（实现为对 manifest 的 rng 两字段做 base+1_000_000+round*1000+rep 覆写并记录 topup 标记）。
    2. run_id = `<campaign_id>-c0000-r<rep:04d>`；`claim_acquire(guard, campaign__run_id)` 已被占 → 若 final COMPLETE 存在则只读核验退出 0（跳过），否则报冲突退出 3。
    3. staging = `<campaign_dir>/samples/.staging/<run_id>.p<pid>/`；`os.makedirs`；`TMPDIR=staging/tmp`。
    4. `slot_acquire`（阻塞重试 ≤600s，每 2s；owner=worker 标识）→ 拿不到槽退出 4。
    5. 跑 `runner.py <manifest> --binary <wl> --ctrace staging/ctrace.csv.gz --msnap staging/msnap.csv.gz --msnap-every <E> --stats`（`start_new_session`、`PYTHONHASHSEED=0`、超时 hang_timeout+30、killpg 模式镜像 campaign.py run_one_rep）→ **slot_release（gem5 结束即放槽，后处理不占槽）**。
    6. 证据抽取：runner stdout/stderr 存档；staging/tmp/man-*/ 里的 `{component}日志、stats.txt` 拷到 staging/evidence/；解析 RESULT/MSNAP/CTRACE/STATS 行。
    7. golden：`ensure_golden`（key 由 campaign spec 派生；golden 的 gem5_sha256 必须==冻结值，否则 loud fail=身份漂移阻断）。
    8. L1：`micro_diff.py --ref <golden msnap> --run staging/msnap.csv.gz --json staging/evidence/micro_diff.json`（子进程，PYTHONHASHSEED=0）。msnap 缺失/截断 → l1.status=truncated/error（如实）。
    9. L2：全量 ctrace 与 golden ctrace 跑 `commit_diff.py`（mode=full）；或 mode=window 时 `--seq-range <inj_seq-pre>:<inj_seq+post>`（inj_seq 从 L0 tick 不能直接得——**用 ctrace 行内 tick 匹配 L0 tick 的最近行 seq**，或首分歧前保守窗口：实现为按 `window_pre_seq/window_post_seq` 以 `inj_seq` 为锚；inj_seq 求法=流式扫 run ctrace 找首个 `tick>=l0.events[0].tick` 的 seq）。Crash 截断 trace → commit_diff 的截断救援路径产出 + `l2.status=not_observed_before_crash`（当截断前缀无分歧时）/`ok`（前缀内有分歧）。run ctrace 完全缺失 → error。
    10. L3：component=="physreg" → `fanout.py --trace <windowed run ctrace> --phys <l0 phys>` method=proxy+caveat 透传；否则 `{"status":"unsupported","reason":"commit trace records dest regs only; source-read/dynamic-instruction association not implemented for <component>; PRF liveness proxy not applicable"}`。
    11. 保留策略（coverage_scope）：mode=full → run 侧保留全量 ctrace；mode=window → 保留窗口切片（流式过滤 seq∈[lo,hi] 写 `evidence/ctrace_window.csv.gz`，**删 staging 全量**）；msnap 全量保留（实测小）。`coverage_scope={mode, seq_lo, seq_hi, full_trace_lines, kept_lines, pruned: true|false, note}`。golden ctrace 永不全量拷贝（只引用路径+sha）。
    12. `build_observation` + `validate_observation` + `chain_completeness` → violations 空*（注：观察性 violation 如 L3 unsupported 不算 violations，只在 chain_gaps）*；失败 → staging 移 `QUARANTINE/` 保留证据，退出 5（**绝不写 COMPLETE**）。
    13. finalize：`os.rename(staging, final_dir)`（同文件系统原子）→ 写 `COMPLETE.json`（含 files sha256 清单 + observation sha256）→ `results.jsonl` 追加一行（`O_APPEND` + flush + fsync）：`{manifest, run_id, rep, seed, classification, faults_injected, exit, timed_out, chain_complete, chain_gaps, observation: "samples/<run_id>/observation.json", ts}` → `claim_release`。
  - `replay --sample-dir`：读 observation.identity.manifest 路径，重跑同 manifest（新 staging、无 claim——replay 不占样本位），比对 classification + commit_diff.verdict + checksum → 回写 observation.replay={pass2_classification, determinism, verdict_pass2, checksum_pass2}（原子重写 observation.json：读-改-临时-replace）。
- Consumes: Task 1 guard、Task 2 runner、Task 3 seq-range、Task 4 golden、Task 5 observation、`campaign.manifest_for_cell`、micro_diff/commit_diff/fanout。

- [ ] **Step 1: 失败测试** `tools/tests/test_ooo_sample_runner.py`（真 smoke 跑，~30s）：
  1. 构造 campaign yaml（smoke + decode imm_bitflip + n=1 + trace.full）→ `run --rep 0` → 断言 final 目录存在、`COMPLETE.json` 存在、observation.json 可 json.load、`l0.injected≥1`（若 Inactive 则换 seed 重取 fixture——记录实测）、l1/l2 status ok、l3 unsupported+chain_complete==false+gaps==["L3"]、results.jsonl 恰 1 行、`files` 里每个 sha256 与磁盘实测一致（抽查 3 个文件）。
  2. 原子性：再次 `run --rep 0` → 命中 COMPLETE 只读核验路径，退出 0 且 observation mtime 不变、无第二条 results.jsonl。
  3. staging 残留为空：`.staging/` 下无残留目录。
  4. `replay`：对样本跑 replay → determinism=="match"（smoke 确定性）。
- [ ] **Step 2: 确认失败**（模块不存在）。
- [ ] **Step 3: 实现**（~700 行，模块级函数便于测试）。
- [ ] **Step 4: 通过** + 把 smoke 实测（wall、ctrace 行数、窗口耗时）记入 `runs/ooo-l0l5/audit/notes.md`。
- [ ] **Step 5: coremark 规模实测（决定 L2 策略）**：对 coremark golden 的 ctrace 统计总行数/字节；跑 1 个 coremark decode Masked 样本（eng2 预演，D01-c rep 0 seed 44072336）走全链，记录 sim wall vs 后处理 wall（full 模式）；若 full commit_diff > 90s/样本 → campaign yaml 采用 `l2_mode: window`（pre=10000, post=窗口按实测=黄金 ctrace 总行数 20% 上限 5,000,000 行）并在 yaml 注释里记录实测依据。**此决策写进 eng2/formal yaml 并冻结**。
- [ ] **Step 6: Commit**：`git add tools/ooo_sample_runner.py tools/tests/test_ooo_sample_runner.py && git commit -m "[OOO][P1] per-sample executor: staging->atomic COMPLETE, guard-gated slots, offline L1-L3 diffs, windowed retention"`。

### Task 7: 三类 E2E 验证（正常 / Masked / abort-Crash + SDC 链路）

**Files:**
- Create: `tools/tests/e2e/ooo_l0l5_e2e.py`（编排+断言脚本，产出报告）
- Create: `docs/gem5-fi/ooo/l0l5-e2e-2026-10-12.md`（报告，入库）

**Interfaces:**
- Produces: E2E 报告（三类样本的 observation 摘要 + 机器断言结果）；SDC 链路样本（FR02 已知 SDC seed 重跑，验证 L2 ⑤数据损坏 路径）。
- Consumes: Task 6 sample runner；`runs/formal_FR02_dcv/c0000/results.jsonl`（只读，挑 1 个 SDC 行的 manifest/seed）。

- [ ] **Step 1: 编排脚本**：① `normal`：no-inject smoke 样本（期望 classification=Inactive 或 Masked、L1/L2 零分歧、chain 完整）；② `masked`：D01-c rep0（coremark imm_bitflip，期望 Masked——eng 实测 2/2 Masked）；③ `crash`：D01-a 同 seed 复刻（opcode_bitflip，eng 实测 2/2 Crash，exit=-6 SIGABRT）→ 断言 l2.status∈{ok,not_observed_before_crash,truncated} 且 trace 前缀可读、observation 无假 no_divergence；④ `sdc`：从 FR02 results.jsonl 取首个 SDC 行的 manifest → 以其 component=rat/sub_field=map_bitflip_vec/seed 构造 E2E campaign 样本 → 断言 classification==SDC、l2.commit_diff.primary_class=="data_corruption"(⑤)、l4.first_detection.detector=="Application"、checksum≠golden 记录在案。
- [ ] **Step 2: 实跑四类**（4 个 gem5 运行 + 后处理；并发≤2）。捕获全部输出到 `runs/ooo-l0l5/e2e/`。
- [ ] **Step 3: 机器断言**：每类核心判据（上列）+ observation 可解析 + files sha 全对。任一 FAIL → 修复后重跑（不放宽判据）。
- [ ] **Step 4: 报告 + Commit**：`git add tools/tests/e2e/ooo_l0l5_e2e.py docs/gem5-fi/ooo/l0l5-e2e-2026-10-12.md && git commit -m "[OOO][P1] three-class E2E (normal/Masked/abort-Crash) + FR02-SDC chain validation: PASS"`（报告含每类 wall/trace 规模/判据输出引用）。

### Task 8: `tools/ooo_chain_audit.py` — 逐样本链路完整性审计

**Files:**
- Create: `tools/ooo_chain_audit.py`
- Test: `tools/tests/test_ooo_chain_audit.py`（fixtures：合法/缺 L1/截断/重复 run_id/身份漂移）

**Interfaces:**
- Produces: CLI `audit --campaign-dir <d> [--require-complete]` → 逐样本：observation 可解析？L0-L5 各 level status？chain_complete/gaps？files sha 复核（抽查全部）？run_id 唯一？seed 唯一？identity.gem5_sha256==冻结值？→ JSON+MD 报告（`<campaign_dir>/chain_audit.json/md`）+ 汇总（n_samples, n_complete_chains, n_gaps_by_level, n_invalid, conservation_totals）。`--require-complete` 时 chain gap（L3 unsupported 除外，任务书允许的 proxy/unsupported 如实计数不视为 invalid）以外的缺失 → exit 1。
- Consumes: Task 5 validate/chain_completeness（import 复用）。

- [ ] **Step 1-4: 测试（含负例 fixture）→ 实现 → 通过**（同前模式；负例必须 exit 1）。
- [ ] **Step 5: 对 Task 7 E2E 样本实跑审计** → 全部 PASS 输出引用。
- [ ] **Step 6: Commit**：`[OOO][P1] chain audit tool with per-sample level completeness and identity checks`。

### Task 9: `tools/ooo_scheduler.py` — 6→8 槽 campaign 调度守护

**Files:**
- Create: `tools/ooo_scheduler.py`
- Test: `tools/tests/test_ooo_scheduler_dry.py`（干跑：假 sample_runner（env 注入桩），验证派发/回收/扩缩/补足逻辑）

**Interfaces:**
- Produces:
  - CLI：`start --batch <batch.yaml> --guard-dir G --runs-root R [--max-slots 6|8]`（前台守护进程，nohup 部署）；`status --guard-dir G`；`policy-snapshot --guard-dir G`。
  - batch.yaml：`campaigns: [{id, runid_row, submodel, yaml, workers, numa_node分配表}], initial_slots: 6, scale_up: {after_s: 900, min_mem_available_kib: 12582912, add: [{id: formal_D04-F0-W4-d, workers: 2}]}, trip: {mem_below_kib: 10485760, degrade_to: [6,4]}, target_valid: 385, replay_pct: 5, topup: {rounds_max: 3}`。
  - 主循环（60s tick）：a) `sample_resources()` 记 `guard/monitor/resources.log`；b) 身份核验（HEAD==冻结 commit、gem5 sha==冻结值，漂移→**停止派发**+写 TRIP 记录+exit 2）；c) 槽位策略：MemAvailable>12GiB 持续≥900s 且 A/B/C 全在跑且无 swap/blocked → 扩到 8（加 D 2 workers，taskset 4+4）；MemAvailable<10GiB 或连续 3 tick swap_in>0 或 blocked>0 持续 → 降到 6（仍不稳再 4）；降档=停新样本派发+等 worker 自然完成（**不杀健康任务**）；d) 每 campaign 完成判定：`results.jsonl` 中 valid（classification 非 SimulatorError 且身份一致）去重计数 ≥385 → 完结；<385 且 attempt≥385 → 触发 topup round（新 seed 块，rounds_max 上限，全部证据保留）；e) worker 进程管理：`taskset -c <node cpus> python3 tools/ooo_sample_runner.py run ...` 循环派发该 campaign 的下一个未完成 rep（从 results.jsonl+COMPLETE 扫描恢复，幂等）；worker 死亡→重启（同 worker 槽）；f) 状态原子写 `guard/state.json`（tmp+os.replace）：各 campaign 进度/有效数/尝试数/seed 块/资源峰值/槽位历史；g) 全部完结 → 生成 handoff（调 Task 10 ooo_handoff）→ 退出 0。
  - replay：每 campaign 按序取 round(replay_pct%×385) 个已完样本跑 `replay` 子命令（串行队列、不占 gem5 槽——replay 也要 gem5！→ replay 同样过 slot 门，但优先级低于新样本；实现为派发队列里的低优先级任务）。
- Consumes: Task 1 guard、Task 6 sample runner、Task 10 handoff。

- [ ] **Step 1-4: 干跑测试**：桩 sample_runner（`OOO_FAKE_RUNNER=1` 时 sample_runner 直接生成合成 COMPLETE——用于测试的显式测试钩子，生产路径不受影响）验证：① 6 槽初始派发 A/B/C 各 2；② 资源序列注入（fake resources）触发扩 8/降 6；③ topup 触发与 rounds_max；④ 幂等恢复（重启后跳过已 COMPLETE）；⑤ 385 完结判定。
- [ ] **Step 5: 半真验证**：用 smoke campaign（n=4, workers=2, replay_pct=25）真跑一遍 scheduler 全周期（~几分钟）→ 4 样本 COMPLETE + 1 replay + handoff 生成。
- [ ] **Step 6: Commit**：`[OOO][P1] 6->8 slot scheduler daemon with NUMA pinning, resource TRIP ladder, topup and idempotent resume`。

### Task 10: `tools/ooo_handoff.py` + 准入门（eng2 ×4×n=2，8/8 PASS 方可 formal）

**Files:**
- Create: `tools/ooo_handoff.py`
- Create: `campaigns/ooo-l0l5/eng2_D01-F0-W6-c.yaml`、`eng2_D02-F0-W6-b.yaml`、`eng2_D02-F0-W6-c.yaml`、`eng2_D04-F0-W4-d.yaml`（字段=旧 formal yaml 同构 + `workload.binary_sha256` 实测 + `chaos_commit`（运行冻结 sha，准入门时确定）+ `trace` 块 + `patchset_sha256`；base_seed 按 Global Constraint 5）
- Create: `tools/tests/test_ooo_handoff.py`（fixtures：合成 results.jsonl/observations）
- Create: `docs/gem5-fi/ooo/l0l5-admission-2026-10-12.md`（准入报告）

**Interfaces:**
- Produces: `handoff(campaign_dir) -> handoff.json + handoff.md`（内容=任务书四：RunID/submodel、commit/status、gem5/config/workload hashes、seed 与尝试数、九分类计数与守恒、385 链路完整/缺失数（chain_complete true/false 分列 + L3 unsupported 说明）、证据索引、首次分歧/传播摘要（首个非 Masked 样本的 l2.first_divergent_commit + l1 首分歧）、错误重试、资源峰值（读 guard resources.log 区间）、wall time、绝对路径）；`master_handoff(campaign_dirs[]) -> handoff_master.json/md`。
- 准入门判据（机器断言，写进 `tools/tests/e2e/ooo_l0l5_admission.py`）：8 个 eng2 样本全部 ① 身份一致（gem5 sha==冻结、config/workload sha==yaml 声明、chaos_commit==冻结）；② 守恒过；③ trace/msnap 可读（或截断如实标记）；④ 无路径覆盖（每样本目录只含自身 run_id 文件——审计脚本扫 `.staging` 残留 + results.jsonl 无重复 run_id）；⑤ 同 seed 重放一致（replay determinism==match，Crash 样本要求 classification 一致+exit 一致）；⑥ observation 机器可解析+files sha 全对。**8/8 PASS → 写 ADMISSION PASS 报告；任一 FAIL → 不启动 formal，修复后整个 eng2 重跑**。

- [ ] **Step 1-4: handoff 单测→实现→通过**。
- [ ] **Step 5: 生成 4 个 eng2 yaml**（seed 52000000/52001000/52002000/52003000；n_per_cell=2；l2_mode 按 Task 6 Step 5 冻结决策）。
- [ ] **Step 6: 实跑 eng2**（scheduler smoke 模式或直接 sample_runner 循环，全机 ≤4 槽）→ 8 样本 + 8 replay。
- [ ] **Step 7: 准入断言脚本跑** → PASS → 报告 + Commit：`[OOO][GATE] eng2 admission 8/8 PASS (identity/conservation/traces/no-overwrite/replay-determinism)`。
- [ ] **Step 8: 冻结运行 commit**：此刻分支 HEAD 即 formal 运行冻结 commit（记 sha；若 Task 7-10 期间有任何改动，此 sha 为最终值，写入 4 个 formal yaml 的 chaos_commit/patchset_sha256 后再提交一次 `[OOO][GATE] freeze formal run commit <sha>`——注意先冻结再生成 yaml，故顺序：以准入通过时的 HEAD 作为 chaos_commit 写入 yaml，该写入提交本身即冻结声明的载体）。

### Task 11: formal 启动与值守（A/B/C 6 槽 → 稳定后 +D 8 槽）

**Files:**
- Create: `campaigns/ooo-l0l5/formal_D01-F0-W6-c.yaml`、`formal_D02-F0-W6-b.yaml`、`formal_D02-F0-W6-c.yaml`、`formal_D04-F0-W4-d.yaml`（base_seed=44072336/41211122/47470573/42729898；n_per_cell=385；其余同 eng2 冻结面）
- Create: `docs/gem5-fi/ooo/l0l5-run-registry-2026-10-12.md`（运行登记表：PID/PGID/日志/恢复命令/资源阶梯）

- [ ] **Step 1: 生成 4 个 formal yaml + batch.yaml（A/B/C workers=2，D 延迟加入）**；`--dry` 展开核对 manifest seed/run_id 唯一性（r0000-r0384 ×4 无碰撞）。
- [ ] **Step 2: 启动前门禁记录**（总方针 8.3：MemAvailable/SwapFree/load/blocked/磁盘/锁/身份五项）写入 registry。
- [ ] **Step 3: `nohup setsid python3 tools/ooo_scheduler.py start --batch ... &` 启动**（记录 PID/PGID；registry 登记）；确认 6 槽占满（guard status）、NUMA 3+3（taskset 生效核验 `taskset -pc <pid>`）。
- [ ] **Step 4: 值守**：每 ~10 分钟核对（gem5 数/Mem/swap/iowait/速率 s/rep/身份零漂移/无 bad_runs 增长/磁盘增速）；15 分钟稳定 + >12GiB → 确认自动扩 8；<10GiB 或持续 swap → 确认自动降档。值守记录追加 registry。持续 >64s/rep 或 Inactive 率异常 → 按 unattended 决策树第 6/7 条处置（隔离单模型，不掩盖）。
- [ ] **Step 5: 完结审计**：四 campaign 各 `ooo_chain_audit audit --require-complete`；385 有效/身份/守恒/无重复 seed；topup（如触发）证据完整。
- [ ] **Step 6: Commit（run registration）**：`git add campaigns/ooo-l0l5/*.yaml docs/gem5-fi/ooo/l0l5-run-registry-2026-10-12.md && git commit -m "[OOO][RUN] formal D01-c/D02-b/D02-c/D04-d launched under 6->8 slot guard (seeds frozen 44072336/41211122/47470573/42729898)"`。

### Task 12: handoff 交付 + 总审计 + 集成报告

**Files:**
- Create: `docs/gem5-fi/ooo/l0l5-final-report-2026-10-12.md`（最终报告：四 campaign 结果总表、链路完整率、首分歧/传播摘要、资源峰值、集成建议）

- [ ] **Step 1: 每 campaign handoff.json/md 生成 + master handoff**（Task 10 工具）。
- [ ] **Step 2: 总审计**：`ooo_chain_audit` ×4 汇总 + 守恒总表 + Wilson CI（复用 wilson.cell_stats）。
- [ ] **Step 3: 最终报告 + 集成顺序**：报告含——父提交 f2ee885、分支 ooo/l0l5-chain、提交清单（逐个 sha + 单元）、推荐集成顺序（guard→runner/commit_diff→golden/observation→sample_runner→audit/scheduler/handoff→yaml/报告）、未入库产物路径（runs/artifacts 绝对路径清单）、遗留事项（L3 unsupported 的 decode 链路 gap、D01-a/b 历史补链待后续）。
- [ ] **Step 4: Commit**：`[OOO][DATA] L0-L5 formal batch final report + master handoff`。

---

## 附录 A：任务书要点对照（执行时逐条自查）

| 任务书条款 | 承载任务 |
|---|---|
| 一.1 记录状态不碰 Excel | Task 0 |
| 一.2 独立 branch/worktree、小提交、不 push | Task 0 + 全部 |
| 一.3 运行冻结同一 commit+binary | Task 10 Step 8 + Task 11 Step 4 身份核验 |
| 一.4 单一调度者+全局 guard | Task 1/9 |
| 二.1 全样本贯穿 ctrace/msnap/diff + observation.json | Task 2/5/6（trace 对**所有**分类开启，非仅 SDC/Crash/Hang） |
| 二.2 observation 内容清单 | Task 5 schema |
| 二.3 fanout PRF-only proxy/unsupported | Task 5/6 L3 规则 |
| 二.4 golden per baseline_key 一次缓存 + PYTHONHASHSEED=0 + staging 原子 COMPLETE + SHA256 | Task 4/6 |
| 二.5 activated=0 N/A；Crash 前无错提交 not_observed_before_crash；截断标 truncated | Task 5/6 |
| 二.6 窗口/ring + coverage_scope + gem5/后处理分离 + 审计命令 | Task 6 Step 5（窗口实测决策）/6（槽即 gem5 期间）/8 |
| 二.7 三类 E2E + 4×n=2 工程 8/8 门 | Task 7/10 |
| 三.1 host 全局槽锁 + claim 锁 + PID/starttime 回收 + COMPLETE 只读跳过 | Task 1/6 |
| 三.2 初始 6 槽 A/B/C 各 2 | Task 11 |
| 三.3 60s 监控 + 15min 稳定升 8 + TRIP 降档 | Task 9/11 |
| 三.4 385 有效 + seed 补足 + worker 目录隔离 + 原子状态 | Task 6/9 |
| 四 handoff ×4 + 总 handoff；不动 Excel/D05 | Task 10/12 |

## 附录 B：核心既有事实（实测，供执行者免重探）

- runner.py：manifest→gem5 CLI 映射唯一入口；`--ctrace/--ctrace-ref/--no-inject/--stats/--fanout-phys` 已有；`-d tempfile.mkdtemp(prefix="man-")`（TMPDIR 敏感）；RESULT/L2RESULT/CTRACE/STATS 行协议；日志解析 L1524-1568（marker-wins）；**无清理 man-***。
- campaign.py：`manifest_for_cell(campaign, cell, ord, rep, outdir, ...)` 可 import（seed=base+ord*1000+rep）；`run_one_rep` 的 killpg 模式；CHILD_ENV PYTHONHASHSEED=0。
- commit_diff.py：seq 对齐五分类；**截断救援已有**（trunc dict/EOFError，merge 停在截断侧）；JSON 含 primary_class/latency_seq/verdict/divergence_counts。
- micro_diff.py：snap_seq 对齐；RAT 分歧/occupancy/IPC 偏差；截断救援已有。
- fanout.py：PRF liveness 上界 proxy，CAVEAT 常量，截断救援已有。
- classify.py：有序分类（SimulatorError 前置；fault-landed 非超时 panic→Crash 界定）；oracle 4 种。
- wilson.ALL_CLASSES：9 类。
- ooo_proxy.py：`--chaos_msnap/--msnap_every/--msnap_file` L419-423；`--chaos_ctrace/--ctrace_file` L407-411；挂载段 L817-842（均只读、FINAL 不变硬门）。
- decode 日志实测样例：`Tick: 423115, Site: fetch_decode, mode=reg_bitflip, pc=0x4195f0, orig_enc=0xf900dfe0, new_enc=0xf900dfe4, bits=[2], orig_mnemonic=str, new_mnemonic=str, regs_moved=1, macroop_new=0, faults_injected: 1`；skip 行契约见 test_faults_log_contract.py（每行带 faults_injected 计数）。
- GOLDEN_IDS：coremark-golden-v1=000000000000cf56、depchainint-golden-v1=98e5e31e726e383f、depchainvec-golden-v1=b1e661a247b95774、smoke-golden-v1=45737cc9a76c0dce。
- /tmp 已有 41971 个 man-* 残留 4.2G——**不清理不新增**（新运行 TMPDIR→/home）。
- 速率基线：decode formal ~40-46s/rep（coremark，jobs=2 时）；D04 dep_chain 类似；>64s/rep 持续=异常。
