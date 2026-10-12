# LSU L0-L5 观测管线 + host-global 调度锁 + 并发提升 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不打断 4 个运行中的 AGU P4 driver 的前提下，补齐 LSU 轨道可审计的 L0-L5 观测管线（ctrace/msnap/commit_diff/micro_diff/fanout 接入 + 每样本 observation.json + golden 缓存 + staging 原子落盘）与防重调度（host-global 槽锁 + claim 锁 + 心跳 + PID+starttime 双核验），再用实测数据把全局并发从 4 提到 6（达标后最多 8）。

**Architecture:** 全部代码开发在独立 worktree 分支 `lsu-obs-20261012`（基于 3a5e96d5）上小步提交；主工作树在 AGU 批次结束前 HEAD 一动不动。新实验由 worktree 代码驱动、输出落主树 `runs/lsu/obs/`（证据持久化），guard 锁目录共享主树 `runs/lsu/guard/`（host-global 语义），gem5 二进制用主树绝对路径（冻结 sha256，绝不重编）。短流（checklist）载体 Phase A 全量 ctrace；长流（W1）观测必须等 Phase B 的 C++ 激活窗口（重编须等全部实验进程结束）。

**Tech Stack:** Python 3 标准库（guard/观测/监控全部 stdlib，无 psutil）；gem5 v25.1.0.1 vendored（CHAOSCommitTrace / CHAOSMicroSnap 已在当前二进制内，`grep -ac` 实证 5/7 处符号）；已有 diff 工具 `tools/commit_diff.py` / `tools/micro_diff.py` / `tools/fanout.py`。

**Spec:** 用户指令 2026-10-12（huawei0101 LSU 轨道执行负责人提示语，一~四节）+ `docs/gem5-fi/lsu/总方针.md` §8 + `docs/gem5-fi/lsu/progress.md` §7 持续运行协议。

## 已核验状态（2026-10-12 15:51-16:00，全部只读命令实测）

- host `localhost0101`；主树 `/home/sdc/gem5-fi-ding`，分支 `fi-ding`，HEAD `3a5e96d51c2e6e728a950733f253d617bffe1e7c`（领先 origin/fi-ding 43），工作树 175 条脏/未跟踪（含 LSU Excel 修改，禁止 reset/clean）。
- `build/ARM/gem5.opt` sha256 `10590f6295bc4dec09fc51c538dd857abaf2efb92fb3c373422a24e1aaf1e36c`（1.14GB，10-11 02:19），与 P4 冻结 manifest `docs/gem5-fi/lsu/evidence/P4/p4_freeze_agu_formal_20261012.json` 记录一致。注意 `CHAOS/gem5/build/ARM/gem5.opt` 存在陈旧副本——一切命令只用 repo 根路径。
- 4 个 driver（PGID=PIDs 1995570/1995598/1995622/1995696，10:59-11:00 启动）占满 `runs/lsu/guard/experiment_slot_{0..3}.lock`，覆盖 31 AGU RunID（A=18 checklist / B=6+C=5 w1 / D=2×2401），进度（16:00 实测）：A 在 ITEM-002 s322（act 323/385）、B ITEM-003 s313（act 314/385）、C ITEM-020 s322（act 323/385）、D ITEM-001 s322（act 323/2401），节奏 ~55s/样本。**绝不干扰**。
- 资源：MemTotal 29Gi / MemAvailable ~22.3GiB / SwapFree ~14.8GiB / Committed_AS ~10.4GiB；`/home` 354G 已用 181G **余 155G（54%）**；load 1.44；**NUMA：仅 node1 有内存（30640MB，CPUs 32-63），node0/2/3 size=0** —— 新 gem5 进程绑 node1。
- 现有产物布局：每样本 `<item>_s{n}/`（`addrpath_injections.log`、`l5_verdict.json`、`stats.txt`、`config.ini/json`）+ 姊妹 `<item>_s{n}_guard.out`（gem5 合并 stdout/stderr，L5 分类输入）+ `_rsrc.log`。无 ctrace/msnap（正式命令未启用）→ **现有样本只能标记"结局完成、完整链待补跑"**。
- ctrace/msnap 参数已在 `configs/se/lsu_proxy.py:544-547/556-561`（`--chaos_ctrace/--ctrace_file`、`--chaos_msnap/--msnap_every/--msnap_file`），C++ 在 `CHAOS/gem5/src/cpu/o3/CHAOSCommitTrace|CHAOSMicroSnap/`（gzflush-per-row，崩溃保前缀）。generic campaign 的 C3-only 限制在 `tools/campaign.py:1417-1419`（已过时——lsu_proxy 也定义了这些旗标），runner 侧 `tools/runner.py:464` 已允许 C3/C4-LSU。
- 九分类 = 五类结局（Masked / Detected-Contained / SDC / Crash / Timeout，`tools/lsu_l5_classify.py`）+ 首检四类（**Hardware RAS / OS / Application / None**，总方针.md:32"首检来源必须且只能是…中的一项"）。
- **不存在**：observation.json 构建器、baseline_key/golden 缓存、claim 锁、心跳、handoff 生成器、NUMA 绑定、PYTHONHASHSEED 设置 —— 全部是本计划新建。

## Global Constraints（每个任务隐含遵守）

1. **绝不干扰 4 个 driver**（PIDs 见上）及其输出目录 `runs/lsu/pilot/AGU/`、`runs/lsu/pilot_w1/`；不停止/不重复认领/不改写。
2. 主树 `fi-ding` HEAD 在 AGU 批次结束前**不得移动**；一切代码改动在 worktree `.claude/worktrees/lsu-obs/`（已被 .gitignore+exclude 覆盖）分支 `lsu-obs-20261012`。
3. **不 push / 不 pull / 不 fetch / 不 rebase / 不改 Excel / 不清理 artifacts**；本地小提交，逐任务汇报父提交+SHA+diff+推荐集成顺序；commit message 不得带 Co-Authored-By 尾注。
4. gem5.opt 冻结 `10590f62…`：运行中不得编译/替换；若必须重编（仅 Phase B），须等全部实验进程结束 + `build.lock` 单实例。
5. 每次运行冻结源码 commit + 二进制哈希；fault/ref 运行环境 `PYTHONHASHSEED=0`；新 gem5 进程 `numactl --cpunodebind=1 --membind=1`（内存全在 node1）。
6. 磁盘红线：0101 始终保留 `/home` **≥50GiB 且 ≥20%**（354G×20%=70.8GiB，取大者）→ 新派发停止条件写进 guard gate；`.gz` 全部在线压缩；长流（W1）ctrace/msnap 必须先有激活窗口（Phase B），Phase A 只对短流 checklist 载体开全量观测，且带单载体体积门禁（防单个 trace 撑爆盘）。
7. 并发：当前 4 槽保持不动；新 guard `LSU_GUARD_SLOTS` 默认 4（向后兼容），升 6 须 driver 释放槽 + hostmon 30-60 分钟实测；升 8 须连续 ≥30 分钟 MemAvailable≥16GiB、SwapFree≥8GiB、无持续 swap-in/out、无 blocked/timeout/guard warning、磁盘增速可控；**本阶段硬上限 8**。MemAvailable<10GiB 停止新派发；<8GiB×2 / <6GiB×1 / SwapFree<2GiB → TRIP 降档。
8. 完整链诚实规则：fanout 仅 PRF 可用且必须 `method=proxy` + caveat；非 PRF 家族 L3=`unsupported` + `chain_complete=false`（辅助 commit 足迹单列，不冒充）；LSU Detected/Contained 必须来自真实 detector 信号，`detected_na=true` 永不算 Detected；activated=0 时 L1-L4=`N/A(inactive_no_activation)`；Crash 在首次错误提交前终止 → `not_observed_before_crash`；截断必须 `truncated=true` 且验证 gzip 前缀可读。
9. 输出协议：先写 `<sample>.staging/`，全部校验（gz 可读、identity 一致、无 violation）后 `os.rename` 成正式目录再写 `COMPLETE`；目录已有 `COMPLETE` → 只读核验并跳过，绝不覆盖；无 COMPLETE 的残留 → 隔离改名 `.quarantine.<ts>` 保留证据。
10. One patch per unit：每任务一提交；提交前自验证 = `python3 -m py_compile` 全部触碰文件 + 本任务单测真跑（引用真实输出）+ 一个不受影响的回归（`python3 tools/lsu_guard.py status`（只读）与 `lsu_runner.py --item ... --dry-run`）。未过不得提交。
11. Excel/共享计划文件只有主协调者写；子 agent 不得写共享文件、不得绕过全局锁。

## Review Focus（最可能咬人的五类输入/失败模式）

1. **陈旧锁被 PID 复用骗过** —— 锁内存活判定只查 `/proc/<pid>` 存在，PID 回收后旧锁会被当"存活"。→ T1 测试：写一个 pid=活进程但 starttime 不匹配的锁，断言判陈旧。
2. **staging 半成品被当作完成样本** —— gem5 崩溃后 `.staging/` 残留，重启 driver 误复活。→ T2 测试：staging 无 COMPLETE 不得 rename；resume 只认 `COMPLETE`；残留进 quarantine。
3. **截断 gz 被误报为 no divergence** —— crash 样本 ctrace 中断在半行。→ T2 测试：截断 gz 必须标 `truncated=true` 且 prefix 行数可数，commit_diff 结果必须带 `fault_trace_truncated` 语境，不得输出裸 "identical"。
4. **golden 缓存身份漂移** —— 二进制/配置/负载变了但复用旧 golden。→ T2/T3 测试：baseline_key 任一 hash 变化必须 miss；golden 目录 identity.json 不匹配必须拒用。
5. **新 guard 与旧 driver 抢槽** —— 新代码 6 槽升序抢 0-3 会与旧 driver 竞争。→ T1 设计：新代码 experiment 降序抢占（5→0），旧 driver 升序不变；测试断言降序且锁文件名/字段向后兼容（旧代码只读 pid/desc/corrupt）。

---

### Task 0: worktree 与基线快照

**Files:**
- Create: `.claude/worktrees/lsu-obs/`（git worktree，分支 `lsu-obs-20261012`，基点 `3a5e96d5`）
- Create: `docs/superpowers/plans/2026-10-12-lsu-l0l5-observation-pipeline.md`（本文件，主树一份 + worktree 提交一份）

**Interfaces:**
- Produces: `WT=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-obs`；主树绝对路径 `MT=/home/sdc/gem5-fi-ding`；所有后续任务的文件路径以 WT 为根（运行产物以 MT/runs/lsu/obs/ 为根）。

- [ ] **Step 1: 建 worktree + 分支**

```bash
cd /home/sdc/gem5-fi-ding && git worktree add .claude/worktrees/lsu-obs -b lsu-obs-20261012 3a5e96d5
git -C .claude/worktrees/lsu-obs status --short | head   # 期望：干净
git -C .claude/worktrees/lsu-obs rev-parse HEAD           # 期望 3a5e96d5...
```

- [ ] **Step 2: 验证 worktree 内运行要素齐备（tracked-only 自洽）**

```bash
ls $WT/configs/se/lsu_proxy.py $WT/workloads/directed/gap_bfs $WT/workloads/mibench/bin/w1_all $WT/docs/gem5-fi/lsu/完整任务执行清单.md
sha256sum $WT/build/ARM/gem5.opt 2>/dev/null || echo "预期缺失——用 LSU_GEM5_BIN=$MT/build/ARM/gem5.opt"
```

- [ ] **Step 3: 把本计划提交为分支第一个 commit（计划入 repo，CLAUDE.md 规定）**

```bash
cp docs/superpowers/plans/2026-10-12-lsu-l0l5-observation-pipeline.md $WT/docs/superpowers/plans/
git -C $WT add docs/superpowers/plans/2026-10-12-lsu-l0l5-observation-pipeline.md
git -C $WT commit -m "[LSU][OBS] 计划入档：L0-L5 观测管线 + host-global 调度 + 并发提升（基于用户指令 2026-10-12）"
```

- [ ] **Step 4: 确认主树零扰动**：`git -C /home/sdc/gem5-fi-ding rev-parse HEAD` 仍为 `3a5e96d5`，`git worktree list` 显示新 worktree；4 个 driver 进程仍存活（`ps -p 1995570,1995598,1995622,1995696`）。

### Task 1: guard v2 —— host-global 槽锁 + claim 锁 + 心跳 + PID/starttime 双核验

**Files:**
- Modify: `tools/lsu_guard.py`（worktree 副本；主树副本不动，运行中 driver 继续用旧码）
- Create: `tests/test_lsu_guard_v2.py`（独立 stdlib 测试脚本）

**Interfaces:**
- Consumes: 现有 `GUARD_DIR`（`LSU_GUARD_DIR` 可覆盖）、`_try_acquire/_release/clear-stale/monitor`。
- Produces（后续任务依赖的精确签名）:
  - `EXPERIMENT_SLOTS = int(os.environ.get("LSU_GUARD_SLOTS", "4"))`
  - `_pid_start_ticks(pid) -> int|None`（/proc/pid/stat 字段22）
  - `_lock_live(lock) -> bool`（pid 活 **且** starttime 一致）
  - 锁 JSON 新增字段：`pid_start`、`heartbeat`（monitor 每 60s 重写）、`campaign`、`sample`（沿用现有 `--item/--runid` 参数，新增 `--campaign/--sample`）
  - claim 锁：`$GUARD_DIR/claims/<campaign>/<runid>/<sample>.claim`（O_EXCL；字段 owner/pid/pgid/pid_start/started/campaign/runid/sample/desc）；子命令 `claim-acquire --campaign C --runid R --sample S --desc D`、`claim-release --campaign C --runid R --sample S --confirm-pid PID`、claim 状态并入 `status` 与 `clear-stale`（claims 用同一 PID+starttime 双核验）
  - gate 新增：`/home`（GUARD_DIR 所在盘）free < **max(50GiB, 20%×total)** → 阻断；`MemAvailable < 10GiB` → 拒绝**新** acquire（STOP_DISPATCH，不影响已持锁运行）
  - experiment 候选槽**降序**（`range(N-1,-1,-1)`），旧码升序不变 → 旧 driver 恒占 0-3，新代码先占高位槽

- [ ] **Step 1: 写失败测试** `tests/test_lsu_guard_v2.py`（核心断言，完整脚本实现时照此扩展）：

```python
#!/usr/bin/env python3
"""test_lsu_guard_v2.py — guard v2 语义单测（隔离 GUARD_DIR，不碰主锁目录）。"""
import json, os, subprocess, sys, tempfile, time
from pathlib import Path

GUARD = Path(__file__).resolve().parent.parent / "tools" / "lsu_guard.py"

def run(env_extra, *argv):
    env = {**os.environ, **env_extra}
    r = subprocess.run([sys.executable, str(GUARD), *argv],
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr

def main():
    tmp = tempfile.mkdtemp(prefix="guard_v2_test_")
    env = {"LSU_GUARD_DIR": tmp, "LSU_GUARD_SLOTS": "6"}
    fails = []
    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name, detail if not cond else "")
        if not cond: fails.append(name)

    # 1) 六槽 + 降序抢占：第一个 acquire 应拿 slot 5
    rc, out, _ = run(env, "acquire", "--type", "experiment", "--desc", "t1")
    lock = json.loads(out) if rc == 0 else {}
    check("slots_env_and_descending", rc == 0 and lock.get("slot") == 5, out)
    check("pid_start_recorded", isinstance(lock.get("pid_start"), int), out)
    rc2, out2, _ = run(env, "acquire", "--type", "experiment", "--desc", "t2")
    check("second_takes_slot4", json.loads(out2).get("slot") == 4, out2)

    # 2) PID 复用免疫：伪造 pid=自身(活) 但 starttime 错误的锁 → 必须判陈旧并拒绝
    p = Path(tmp, "experiment_slot_0.lock")
    p.write_text(json.dumps({"owner": "x", "pid": os.getpid(), "pgid": os.getpgid(0),
                             "task_type": "experiment", "desc": "forged",
                             "started": "2026-01-01 00:00:00", "slot": 0,
                             "pid_start": 1}))  # starttime=1 不可能等于本进程
    rc3, _, err3 = run(env, "acquire", "--type", "experiment", "--desc", "t3")
    check("recycled_pid_detected", rc3 != 0 and "陈旧" in err3, err3)

    # 3) claim 锁：O_EXCL 唯一 + 释放确认 + status 可见
    rc4, _, _ = run(env, "claim-acquire", "--campaign", "c", "--runid", "R", "--sample", "s0", "--desc", "d")
    rc5, _, err5 = run(env, "claim-acquire", "--campaign", "c", "--runid", "R", "--sample", "s0", "--desc", "d2")
    check("claim_exclusive", rc4 == 0 and rc5 != 0, err5)
    rc6, out6, _ = run(env, "status")
    check("claim_in_status", rc6 == 0 and "claims" in out6, out6[:200])

    # 4) STOP_DISPATCH：<10GiB 时拒绝新 acquire（monkeypatch 不可行于子进程——用注入伪造 meminfo 的方式：guard 读 /proc/meminfo，测试通过 LSMU_FAKE_MEMINFO 环境变量? —— 不引入测试后门；改为直接单测 _try_acquire 的判定函数（import guard 模块）：
    sys.path.insert(0, str(GUARD.parent))
    os.environ.update(env)
    import lsu_guard as G
    snap = {"mem_available_gib": 9.5, "swap_free_gib": 14.0, "compile_processes": [],
            "blocked": [], "disk_free_gib": 100.0}
    check("stop_dispatch_threshold", G._stop_dispatch(snap) is True)
    snap["mem_available_gib"] = 16.0
    check("stop_dispatch_ok_at_16", G._stop_dispatch(snap) is False)

    # 5) 磁盘红线：free < max(50, 20%*total) → gate 阻断
    reason = G._disk_guard_reason(free_gib=60.0, total_gib=354.0)   # 20%*354=70.8
    check("disk_guard_20pct", reason is not None)
    reason2 = G._disk_guard_reason(free_gib=90.0, total_gib=354.0)
    check("disk_guard_pass", reason2 is None)

    # 6) 向后兼容：旧字段锁（无 pid_start）仍被旧语义读取
    p.write_text(json.dumps({"owner": "x", "pid": -1, "pgid": -1, "task_type": "experiment",
                             "desc": "oldstyle", "started": "x", "slot": 0}))
    check("old_lock_parses", G._read_lock("experiment", 0).get("desc") == "oldstyle")

    print("FAILURES:", fails)
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 跑测试确认失败**：`cd $WT && python3 tests/test_lsu_guard_v2.py` → 期望 FAIL（LSU_GUARD_SLOTS/claim/pid_start/`_stop_dispatch`/`_disk_guard_reason` 尚不存在，AttributeError/行为不符）。
- [ ] **Step 3: 实现 guard v2**（要点，全部落在 `tools/lsu_guard.py`）：
  - `EXPERIMENT_SLOTS` 改环境变量读取；experiment 候选改降序 `range(EXPERIMENT_SLOTS-1, -1, -1)`。
  - acquire 时记录 `pid_start=_pid_start_ticks(os.getpid())`；`_lock_live(lock)` 双核验；`_try_acquire`/`_gate_result`/`clear-stale` 全部改用 `_lock_live`（clear-stale 处置条件 = pid 死 **或** starttime 不符，且 `--confirm-dead-pid` 匹配）。
  - `monitor()` 每轮采样后重写本锁文件加 `heartbeat` 字段（只重写自己 slot 的锁）。
  - `run`/`acquire` 子命令新增 `--campaign/--sample` 透传进锁 JSON。
  - 新增 `_stop_dispatch(snap)`（MemAvailable<10GiB → True；在 `_try_acquire` 的 experiment 分支入口拒绝，理由串 `STOP_DISPATCH: MemAvailable<10GiB`）与 `_disk_guard_reason(free_gib,total_gib)`（`free < max(50.0, 0.20*total)` → 理由串），后者并入 `_gate_result` reasons。
  - claim 子命令三件套 + `status` 输出 claims + `clear-stale --type claim`（同双核验）；claim 文件同锁格式。
  - 文档字符串更新阈值说明（引用用户指令 2026-10-12 三节）。
- [ ] **Step 4: 跑测试至全 PASS**（引用真实输出）。
- [ ] **Step 5: 回归**：`LSU_GUARD_DIR=$MT/runs/lsu/guard python3 $WT/tools/lsu_guard.py status`（只读，应显示 4 槽被占 + claims 空）——**绝不能**在主锁目录 acquire。
- [ ] **Step 6: Commit**（worktree）: `git add tools/lsu_guard.py tests/test_lsu_guard_v2.py && git commit -m "[LSU][OBS-1] guard v2：LSU_GUARD_SLOTS 槽位数化+降序抢占+PID/starttime 双核验+心跳+claim 锁+磁盘红线+STOP_DISPATCH"`。

### Task 2: 观测核心 —— baseline_key / golden 缓存 / observation.json / staging 协议

**Files:**
- Create: `tools/lsu_obs_core.py`（纯函数库：无 gem5 依赖，可完全单测）
- Create: `schemas/observation.schema.json`（observation.json v1 结构约束）
- Create: `tests/test_lsu_obs_core.py`
- Create: `tests/fixtures/obs/`（合成小 trace 对 + 截断 gz + 空 gz）

**Interfaces:**
- Consumes: `tools/commit_diff.py compare(ref,run,json,tick_tol)`、`tools/micro_diff.py diff(ref,run,json,ipc_hide_pct)`、`lsu_l5_classify` 输出结构（`attempted/eligible/injected/activated/outcome/classes/checksum/crash_kind/detected_na`）、注入日志行格式 `Tick: <t>, Site: <s>, mode=<m>, old_vaddr=<o>, new_vaddr=<n>, faults_injected: <k>`。
- Produces:
  - `sha256_file(p) -> hex`
  - `baseline_key(ident: dict) -> hex32`：`sha256(json.dumps(ident, sort_keys=True))[:32]`，ident 至少含 `gem5_opt_sha256, lsu_proxy_sha256, workload, workload_sha256, cpu, variant, maxinsts, obs_flags(argv 观测旗标), env{"PYTHONHASHSEED":"0"}, checkpoint`
  - `gz_probe(path) -> {"readable": bool, "rows": int, "truncated": bool, "bytes": int}`（流式 gzip 解码，捕获 EOFError/坏 CRC → truncated=True 且 prefix 行数可数）
  - `parse_l0(stdout_text, injections_log_text) -> dict`（funnel 三元组 + 注入明细表；stdout 缺失 → `violations` 记录，绝不猜）
  - `build_observation(...) -> dict`（完整 v1 schema，见下）
  - `finalize_sample(staging: Path, final: Path) -> Path|None`：校验 staging 内 observation.json 可解析、`violations==[]`、所有 files 的 sha256 复核 → `os.rename` → 写 `COMPLETE`；任何失败返回 None 并保留 staging
  - `verify_complete(d: Path, ident) -> (ok, reason)`：COMPLETE 目录只读核验（observation.json 可解析 + identity 关键字段匹配 + 抽样 1 个 file sha256）
  - 常量 `NINE = {"outcome": ["Masked","Detected/Contained","SDC","Crash","Timeout"], "first_detection_source": ["Hardware RAS","OS","Application","None"]}`

**observation.json v1 骨架（TDD 的对照物）：**

```json
{
  "schema": "lsu-observation-v1",
  "identity": {"campaign": "...", "item": "...", "runid": "...", "sample": "s3", "seed": 123,
               "phase": "screening", "git_commit": "...", "gem5_opt_sha256": "10590f62...",
               "lsu_proxy_sha256": "...", "workload": "...", "workload_sha256": "...",
               "config_family": "C4-LSU", "argv_hash": "...", "pythonhashseed": 0,
               "numa_binding": "node1", "baseline_key": "<hex32>", "created": "..."},
  "L0": {"attempted": 1, "eligible": 265143, "injected": 1, "activated": 1, "funnel_source": "stdout",
         "injections": [{"tick": 887040, "site": "lsq_sendFragmentToTranslation",
                         "mode": "low_bit_flip", "old": "0x7ffffefd00", "new": "0x87ffffefd00",
                         "dynamic_target": "vaddr", "raw": "...原行..."}]},
  "L1": {"status": "complete", "ref": {"path": "...", "sha256": "...", "rows": 1204, "truncated": false},
         "fault": {"path": "...", "sha256": "...", "rows": 1204, "truncated": false},
         "micro_diff": {"first_divergence_snap_seq": 118, "fields": ["rat_hash"], "ipc_dev_pct": 0.0}},
  "L2": {"status": "complete", "ref": {...}, "fault": {...},
         "commit_diff": {"first_errant_commit": {"seq": 100041, "tick": 902114, "pc": "0x...", "op": "..."},
                         "n_errant_commits": 812, "tick_tol": 0, "fault_trace_truncated": false}},
  "L3": {"status": "unsupported", "method": null, "caveat": "PRF-only proxy fanout; source-read/dynamic-instruction-association/propagation-tag not implemented (Phase B)",
         "auxiliary_commit_footprint": {"n_errant_commits": 812, "distinct_pcs": 37, "seq_span": [100041, 100852]}},
  "L4": {"detector": "none_wired", "detected_na": true, "detected": false,
         "first_anomaly": {"source": "L2", "tick": 902114, "seq": 100041,
                           "latency_ticks_from_first_injection": 15074, "latency_commits": 41}},
  "L5": {"outcome": "SDC", "crash_kind": null, "classes": {"Masked":0,"Detected/Contained":0,"SDC":1,"Crash":0,"Timeout":0},
         "first_detection_source": "None", "checksum": "...", "checksum_source": "...", "golden": "...",
         "exit": 0, "timed_out": false, "detected_na": true, "conservation": "OK"},
  "replay_determinism": {"policy": "per_runid_first", "verified": true,
                         "evidence": {"metric": "L0+L5", "ref_run": "<path>", "identical": true}},
  "violations": [], "files": [{"name": "commit_trace.csv.gz", "path": "...", "sha256": "...", "bytes": 0}],
  "chain_complete": false,
  "chain_status_reason": "L3 unsupported (non-PRF); L0/L1/L2/L4/L5 complete"
}
```

**chain_complete 判定（精确规则，测试逐条覆盖）：**
```python
def chain_complete(o):
    if o["violations"]:
        return False
    l0, l5 = o["L0"], o["L5"]
    if l0["injected"] is None or l5["outcome"] in (None, "INCONCLUSIVE"):
        return False
    if not o["replay_determinism"]["verified"]:
        return False
    if l0["activated"] == 0:
        return all(o[lv]["status"] == "N/A(inactive_no_activation)" for lv in ("L1", "L2", "L3", "L4"))
    return all(o[lv]["status"] == "complete" for lv in ("L1", "L2", "L3", "L4"))
```
（activated=0 且 L0/L5 完整 → chain_complete=true；activated>0 的 LSU 家族样本在 Phase B 落地前恒 false——L3 unsupported，诚实标注。）

- [ ] **Step 1: 写 fixtures**：合成 `ref.csv.gz`/`fault_div.csv.gz`（>1处分歧）/`fault_same.csv.gz`（无分歧）/`fault_trunc.csv.gz`（截断半行）/msnap 对应物；固定内容使断言可复演。
- [ ] **Step 2: 写失败测试**：覆盖 (a) baseline_key 任一 hash 变化→miss；(b) gz_probe 对截断件 `truncated=True` 且 rows>0、对完整件 rows 精确；(c) parse_l0 对真实注入行（用上面 s319 原行）产出正确字段、stdout 缺 funnel→violation；(d) build_observation 的 activated=0 → L1-L4 全 N/A(inactive) 且 chain_complete=true；(e) activated>0 + L3 unsupported → chain_complete=false 且 reason 含 "L3 unsupported"；(f) finalize_sample：violations 非空 → 不 rename； COMPLETE 目录 verify_complete 通过/身份漂移拒绝；(g) crash-before-divergence → L2.status=`not_observed_before_crash`。
- [ ] **Step 3: 实现 `tools/lsu_obs_core.py` + schema**；跑测试至全 PASS。
- [ ] **Step 4: Commit**: `[LSU][OBS-2] 观测核心：baseline_key/golden 缓存协议/gz 探针/L0 解析/observation.json v1+schema/staging 原子落盘/chain_complete 判定`。

### Task 3: 观测 runner —— ctrace/msnap 接入 LSU 专用驱动 + gem5 路径覆盖

**Files:**
- Create: `tools/lsu_obs_driver.py`（新 driver；**不改** `lsu_w1_rerun.py` 语义）
- Modify: `tools/lsu_runner.py`（仅一处：`G5 = REPO/"build/ARM/gem5.opt"` 旁加 `def g5_path(): return Path(os.environ.get("LSU_GEM5_BIN", str(G5)))`，`build_manifest` identity 与 `main` 的执行路径改用它）
- Create: `tests/test_lsu_obs_driver_cli.py`（dry-run 命令构造断言，不起 gem5）

**Interfaces:**
- Consumes: `LR.build_manifest/build_guard_cmd`（旗标复用，no drift）、`UP._valid_resumed/_activated_count/audit/classify_run/GuardFailure`、T1 guard（`LSU_GUARD_SLOTS/LSU_GUARD_DIR/claims`）、T2 core。
- Produces:
  - CLI：`python3 tools/lsu_obs_driver.py --items ITEM-XXX [--phase screening] [--campaign NAME] [--samples N] [--obs-mode full|l0l5] [--trace-budget-gib 40] [--dry-run]`
  - `run_obs_one(manifest, staging: Path, obs: dict) -> (verdict, gem5_exit)`：构造 `gem5.opt --outdir staging <lsu_proxy.py> [原旗标] --chaos_ctrace --ctrace_file staging/commit_trace.csv.gz --chaos_msnap --msnap_every 1000 --msnap_file staging/micro_snap.csv.gz`，经 guard `run --type experiment --campaign ... --sample ...` 执行，env `PYTHONHASHSEED=0`，命令前缀 `numactl --cpunodebind=1 --membind=1`（存在 numactl 时）；stdout/stderr 落 `staging/gem5.out`
  - `ensure_golden(ident, args_ref) -> golden_dir`：`runs/lsu/obs/golden/<baseline_key>/`，无 COMPLETE → 跑一次 no-fault ref（同观测旗标、无注入 mount）→ finalize；有 → verify_complete 只读复用；identity 漂移 → 拒用重跑（新 key）
  - 样本流程：`claim-acquire` → COMPLETE 检查（有→verify+skip）→ staging 新建（残留→quarantine）→ ref 确保 → fault run → L5 分类 → diff 池（`ThreadPoolExecutor(max_workers=2)`，commit_diff+micro_diff，与 gem5 槽位分离）→ observation.json → finalize → `claim-release`
  - 体积门禁：ref ctrace gz 单件 > `--trace-budget-gib`（默认 40）→ 该载体标 `carrier_over_budget`，obs 降级 `l0l5` 并在 observation.json `violations` 记录 `"trace_budget_exceeded"`（诚实，不假造链）
  - 长流（W1）载体在 Phase A 一律 `l0l5`（`coverage_scope: "none_full_run_forbidden_pending_phaseB_window"`）

- [ ] **Step 1: 失败测试**：`--dry-run` 断言构造出的命令含 ctrace/msnap 旗标、`PYTHONHASHSEED=0`、numactl 前缀、`LSU_GEM5_BIN` 覆盖生效（`LSU_GEM5_BIN=/x/gem5.opt` → 命令首元素为 `/x/gem5.opt`）；断言 W1 载体 obs-mode 强制 l0l5；断言 claim 冲突时样本被跳过。
- [ ] **Step 2: 实现**（含 lsu_runner.py 的 `g5_path()` 最小改动）；测试 PASS。
- [ ] **Step 3: 回归**：`python3 $WT/tools/lsu_runner.py --manifest <既有 manifest> --dry-run`（不执行）+ `python3 $WT/tools/lsu_w1_rerun.py --items ITEM-003 --phase pilot --target 30 --dry-run` 不存在则跳过（该 driver 无 dry-run；改用 py_compile + import 烟测：`python3 -c "import sys; sys.path.insert(0,'$WT/tools'); import lsu_w1_rerun"` 需防执行——只 py_compile）。
- [ ] **Step 4: Commit**: `[LSU][OBS-3] 观测 runner：ctrace/msnap 全链接入 LSU 专用驱动（golden 缓存/claim/staging/diff 池/NUMA 绑定/PYTHONHASHSEED/gem5 路径覆盖）`。

### Task 3b: 解除 generic campaign 的 C3-only 限制（保留能力检查）

**Files:**
- Modify: `tools/campaign.py:1417-1419`（worktree 副本）

- [ ] **Step 1: 改限制**：`if campaign.get("config","C0") != "C3":` → `if campaign.get("config","C0") not in ("C3","C4-LSU"):`，报错文案改为"only configs/se/ooo_proxy.py and configs/se/lsu_proxy.py define --chaos_ctrace/--chaos_msnap"。`trace_ref_mode != "once"` 与 `replay_for` 校验保留（能力检查不放松）。
- [ ] **Step 2: 验证**：`python3 -c` 内联构造 campaign dict 走该 gate（或 grep 确认 + `python3 tools/campaign.py --help` 正常）+ py_compile。
- [ ] **Step 3: Commit**: `[LSU][OBS-3b] generic campaign trace 门放开 C4-LSU（能力检查保留：config_family 白名单 + trace_ref_mode + replay_for）`。

### Task 4: host 资源监控 + 槽位策略（hostmon）

**Files:**
- Create: `tools/lsu_hostmon.py`
- Create: `tests/test_lsu_hostmon.py`（阈值决策函数单测）

**Interfaces:**
- Produces:
  - `python3 tools/lsu_hostmon.py --interval 60 --out runs/lsu/obs/hostmon/`（常驻，主树输出）
  - 每拍 JSONL：`{"t", "gem5_procs": [{"pid","rss_gib","cpu_pct","etime_s"}], "mem_available_gib", "swap_free_gib", "si_ps", "so_ps", "committed_as_gib", "load", "blocked_n", "gem5_n", "home_free_gib", "tmp_free_gib", "obs_growth_gib", "slots_held"}`（si/so = /proc/vmstat pswpin/pswpout 差分/秒；obs_growth = df 差分）
  - `slot_policy.json`：`{"cap": 4|6|8, "state": "HOLD4|RAMP6|HOLD6|RAMP8|TRIP_DOWN", "reason", "updated", "evidence": {"window_min": 30, "mem_min_gib": ..., "swap_min_gib": ..., "sustained_swap": false, "blocked_events": 0, "guard_warnings": 0}}`
  - 决策函数 `decide_cap(history, current_cap) -> (new_cap, state, reason)`（纯函数，单测）：RAMP6 需 `slots_held < cap`（有 driver 退出）且 MemAvailable≥12；升 8 需连续 ≥30 拍（30 分钟）MemAvailable≥16、SwapFree≥8、无持续 si/so（>0 连续 5 拍）、无 blocked/timeout/guard warning、home_free 增速 <1GiB/10min；TRIP 规则同 guard（<8×2/<6/SwapFree<2）→ cap 降 2（下限 4）。
- [ ] **Step 1: 失败测试**（decide_cap 三条路径：升 8 通过/否决/TRIP 降档，构造 30 拍历史）。
- [ ] **Step 2: 实现**；测试 PASS；`python3 tools/lsu_hostmon.py --interval 60 --out /tmp/hostmon_test --once` 实跑一拍（真实输出引用）。
- [ ] **Step 3: 启动常驻 hostmon**（nohup，主树 `runs/lsu/obs/hostmon/`，PID 记入 handoff；这是只读采样进程，不占实验槽）。
- [ ] **Step 4: Commit**: `[LSU][OBS-4] hostmon：60s 主机资源采样 + si/so 差分 + 槽位策略状态机（RAMP6/RAMP8/TRIP_DOWN 判据实现化）`。

### Task 5: E2E 最小验证 + driver 退出 watcher

**Files:**
- Create: `tools/lsu_obs_e2e.py`
- Create: `runs/lsu/obs/e2e_<date>/`（输出，主树）

**Interfaces:**
- Produces: `--select`（扫描既有 l5_verdict.json，从 checklist 载体选出：1×activated=0 正常完成、1×Masked 或 SDC、1×Crash/simulator_assert abort，打印 (item,s,outcome) 清单）；`--run [--watch-pids P1,P2,...]`（等待任一 driver PID 退出 → 确认 guard 槽确已空 → 依 slot_policy 用新 guard 逐个跑三样本 + 每样本 replay 重跑一次（per_sample 确定性）+ 三样本共享 1 个 golden ref）；`--validate`（断言：正常样本 checksum==golden 且 L1-L4 N/A 或 complete；Masked 样本 commit_diff 无分歧 或 truncated 标记正确；Crash 样本 l5=Crash、gz 前缀可读、`not_observed_before_crash` 或 complete、staging 残留不复活、COMPLETE 只读核验通过、crash durability=崩溃后 observation.json 仍完整落盘）；`--report`（写 `handoff_e2e.json/md` 交中央）。
- E2E PASS 判据（写死在 --validate）：三样本全部 `finalize` 成功 + replay determinism identical + 无 violations（除 L3 unsupported 与可能的 trace_budget 诚实标注）+ integrity checker 拒绝注入的坏样本（自检：故意伪造 violations 非空样本必须被 finalize 拒绝）。

- [ ] **Step 1: 实现 select/run/validate/report**（复用 T2/T3；watcher 用 `/proc/<pid>` 存在性轮询 30s）。
- [ ] **Step 2: 单测**：select 对真实 runs/lsu/pilot/AGU 扫描出 ≥1 候选每类（真实输出引用）；validate 对合成坏样本拒绝。
- [ ] **Step 3: 挂 watcher 常驻**（nohup，等待 driver 释放槽后自动执行 E2E；期间不占槽）。
- [ ] **Step 4: Commit**: `[LSU][OBS-5] E2E kit：三样本选择器/driver 退出 watcher/crash durability 与完整性自检/中央报告`。

### Task 6: 既有结果链路标记 ledger + handoff 生成器

**Files:**
- Create: `tools/lsu_handoff.py`
- Create: `runs/lsu/obs/chain_ledger_p4_agu_formal_20261012.json`（生成物）

**Interfaces:**
- Produces: `--ledger --campaign p4_agu_formal_20261012`（扫描 31 RunID 的 `{it}_result.json`/l5_verdict，生成 per-RunID：`{"runid", "item", "outcome_summary", "attempted", "activated", "status", "chain": "outcome_complete_chain_pending", "missing_levels": ["L1","L2","L3","L4"], "evidence_root": "<abs path>"}`——只读扫描，不写任何既有目录）；`--campaign-handoff <dir>`（读 obs campaign 输出 → handoff.json + handoff.md：RunID、代码/二进制/config/workload hashes、seed 与尝试数、九分类计数与守恒、完整链数量/缺失层级、证据索引、首次分歧/传播摘要、重试、资源峰值（读 hostmon）、wall time、绝对路径、git 提交——按用户指令第四节全字段）。
- [ ] **Step 1: 实现 + 对当前 AGU 批次跑一次 ledger 生成（真实输出引用，31 RunID 全列）**。
- [ ] **Step 2: handoff 对 e2e campaign 试生成一次（若 E2E 未跑则对空集生成骨架并标注 pending）**。
- [ ] **Step 3: Commit**: `[LSU][OBS-6] 链路 ledger（结局完成/链待补跑 标记，不改 Excel 不写既有目录）+ handoff.json/md 生成器`。

### Task 7: 下一批 RunID 清单（只报告，不启动）

**Files:**
- Create: `tools/lsu_next_batch.py`
- Create: `runs/lsu/obs/next_batch_proposal_<date>.json/md`

- [ ] **Step 1: 实现**：`parse_items()` 全量 → 复用 `lsu_unit_pilot.eligible()` 准入 + 扫 `runs/lsu/pilot*/**/{it}_result.json`、unit_status、p4 freeze manifest 排除已完成/在跑 → 输出唯一、未完成、能力检查过的 RunID 清单（含 carrier/severity/预估时长/是否需 Phase B 窗口）。
- [ ] **Step 2: 生成提案并交中央**（handoff 附带；明确"未获中央 PASS 不启动 formal"）。
- [ ] **Step 3: Commit**: `[LSU][OBS-7] 下一批 RunID 提案生成器（能力检查+完成度扫描，report-only）`。

### Task 8: 并发提升 4→6（→8）执行规程

**Files:**
- Create: `docs/gem5-fi/lsu/evidence/P4/obs_ramp_runbook_20261012.md`

- [ ] **Step 1: 写 runbook**（前置条件：≥1 driver 退出且 E2E PASS 已交中央；执行：`LSU_GUARD_SLOTS=6` 起 obs/admission 负载，含 ≥1 个代表性长 Masked 样本——优先既有 W1 Masked 种子重放，无则 no-fault W1 golden 重跑（工程运行，双份用作 Phase B baseline 预热），无 ctrace；hostmon 持续 30-60 分钟逐拍记录；判据与降档按 Global Constraint 7）。
- [ ] **Step 2: obs_driver 接 slot_policy**（每样本派发前读 `runs/lsu/obs/hostmon/slot_policy.json` 的 cap 设置 `LSU_GUARD_SLOTS`；policy 缺失 → 保守 4）——代码小改 + 测试。
- [ ] **Step 3: 执行 ramp 并把 30-60 分钟实测摘要写入 handoff**（在 E2E PASS + 槽释放后；期间每 60s 记录齐全）。
- [ ] **Step 4: Commit**: `[LSU][OBS-8] 并发提升规程 + obs_driver 槽位策略接入（实测驱动，TRIP 自动降档）`。

### Task 9: Phase B 设计文档（激活窗口 ctrace/msnap + 传播 tag，不实现）

**Files:**
- Create: `docs/gem5-fi/lsu/evidence/P4/obs_phaseB_window_design.md`

- [ ] **Step 1: 写设计**：CHAOSCommitTrace/CHAOSMicroSnap 增加 `startTick/stopTick`（或注入器回调激活后开窗）参数的接口草案、ring-buffer 备选、重编前置条件（全部实验进程结束 + build.lock 单实例 + -j16）、传播 tag（addrpath 注入地址的 source-read 关联）草案、`coverage_scope` 字段语义（`full_run|window[actTick,actTick+W]|ring`）、验收口径（W1 单样本 trace ≤ 预算）。
- [ ] **Step 2: Commit**: `[LSU][OBS-9] Phase B 设计：激活窗口观测与传播 tag（重编前置条件与验收口径入档）`。

## 集成顺序建议（给主协调者）

1. `lsu-obs-20261012` 分支按 T0→T9 顺序 cherry-pick/merge 到 fi-ding（每个 commit 独立可回退；T1 guard 与 T3 lsu_runner 改动需同时上线才能跑观测驱动）。
2. AGU 批次结束前主树不集成运行时改动也无风险——新代码只在 worktree 被执行。
3. Phase B（C++ 窗口）是独立后续计划，须单独走 one-patch-per-unit + 重编纪律。

## 执行方法

用户已指定：服务器 AI 自行实现/调度/运行（native 执行，本会话内逐任务实施，子 agent 只做只读侦察），计划为唯一工作清单，每任务自验证后本地提交（不 push），阶段产物经 handoff 交主协调者。
