#!/usr/bin/env python3
"""test_claim_concurrency.py — guard v2 并发竞争真实验收（LSU OBS 阶段一验收 G）。

全部子测试用真实进程 + 真实输出；LSU_GUARD_DIR 一律指向隔离临时目录，
绝不指向主树 runs/lsu/guard（只读 status 不在此测试范围内）。

**隔离目录为什么在 worktree 下而不在 /tmp**：guard v2 的 gate 磁盘红线
free < max(50GiB, 20%×total)（冻结语义）在 /tmp（tmpfs 总 15GiB、余 ~12GiB）
上恒阻断 `run` 子命令——不可绕过、也不应绕过；worktree 在 /home
（354GiB 总量、余 ~153GiB > 红线 70.8GiB）可通过。目录在 .tmp_lsu_conc/
下、测试结束即删、不入 git。

子测试（用户指令 2026-10-12，OBS 计划验收 G）：
  (a) claim 唯一性：8 进程同时 claim-acquire 同一 (campaign,runid,sample)
      → 恰好 1 个 rc=0，其余 7 个 REFUSED（rc 2"已被持有"或 3"陈旧"——
      短命 CLI 持有者退出后按 v2 语义判陈旧，两种都是合法 REFUSED）
  (b) 不同 sample 无互斥：8 进程 8 个不同 sample → 全部 rc=0 且文件落盘
  (c) 槽竞争：LSU_GUARD_SLOTS=2，6 进程同时 acquire --type experiment
      → 恰好 2 个 rc=0（槽集合 {0,1}，降序抢占先占高位），其余 4 个
      REFUSED"全部被占"。持有者用 linger 包装（acquire 后存活 3s 再退出）：
      纯 CLI acquire 进程在锁创建后数毫秒即退出，并发竞争者会把刚创建的
      锁判"陈旧"而拒绝在先（guard docstring 自述的 acquire 短命竞态，真实
      场景中 acquirer 是长驻 driver 进程）——linger 包装消除该测试伪影，
      锁持有者在竞争窗口内全程存活。
  (d) 真实 run 并发上限：LSU_GUARD_SLOTS=3，6 个 `guard run -- sleep 3`
      （--interval 1）同时发起；被"全部被占"拒绝者重试（driver 语义）→
      同时存活 sleep 进程峰值 ≤3（锁文件 cmd==["sleep","3"] 且 pid 存活
      计数，0.1s 轮询）、全部 6 个 run-finish 且 exit_code=0、
      monitor_reason=target-exited（无 TRIP）、锁全释放、首轮拒绝 ≥3
      （竞争真实发生）。
      已知释放竞态（如实记录，非测试失败）：run 的目标进程退出到锁 unlink
      之间（monitor 的 /proc 存活扫描耗时，~10-100ms）锁文件存在但 pid 已
      死，并发 acquire 会瞬时判"陈旧"——1s 后复核锁已消失则按瞬态重试，
      仅持续存在的死锁才判失败。
  (e) 心跳：`guard run -- sleep 65 --interval 5` 期间锁文件 heartbeat 字段
      出现且值更新（≥2 个不同值、字符串时间戳递增）；结束后 run-finish
      且锁释放。

环境前置：MemAvailable≥11GiB（gate 12GiB/STOP_DISPATCH 10GiB 余量）且
SwapFree≥4GiB（gate 红线）；不满足 → (c)(d)(e) 跳过并判失败（环境不可
验收=响亮失败，不静默通过）。当前主机 2026-10-12 实测 22GiB/14.8GiB。

用法：python3 tests/test_claim_concurrency.py   （退出码 0=全 PASS）
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "tools"
GUARD = TOOLS / "lsu_guard.py"
TMP_ROOT = HERE.parent / ".tmp_lsu_conc"   # 在 /home 上：gate 磁盘红线要求

# (c) linger 包装：跑真实 cmd_acquire（argparse→_try_acquire 全路径），仅延长
# 进程寿命以模拟长驻 driver（锁持有者在竞争窗口内存活）
LINGER_ACQUIRE = (
    "import sys, time\n"
    "sys.path.insert(0, {tools!r})\n"
    "import lsu_guard\n"
    "sys.argv = ['lsu_guard.py'] + sys.argv[1:]\n"
    "rc = 0\n"
    "try:\n"
    "    lsu_guard.main()\n"
    "except SystemExit as e:\n"
    "    rc = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)\n"
    "time.sleep({linger})\n"
    "sys.exit(rc)\n")


def new_guard_dir():
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.mkdtemp(prefix="gd_", dir=str(TMP_ROOT))


def env_for(gd, slots=None):
    env = {**os.environ, "LSU_GUARD_DIR": str(gd)}
    if slots is not None:
        env["LSU_GUARD_SLOTS"] = str(slots)
    return env


def read_locks(gd):
    out = []
    for p in Path(gd).glob("experiment_slot_*.lock"):
        try:
            out.append(json.loads(p.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return out


def live_sleeps(gd):
    return sum(1 for d in read_locks(gd)
               if d.get("cmd") == ["sleep", "3"]
               and os.path.exists(f"/proc/{d.get('pid')}"))


def dead_locks(gd):
    return [d for d in read_locks(gd)
            if not os.path.exists(f"/proc/{d.get('pid')}")]


# ---------------------------------------------------------------- 子测试

def test_a_claim_uniqueness(check):
    gd = new_guard_dir()
    env = env_for(gd)
    argv = ["claim-acquire", "--campaign", "concA", "--runid", "A01-F0-W9",
            "--sample", "s42", "--desc", "conc-a"]
    procs = [subprocess.Popen([sys.executable, str(GUARD), *argv],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, env=env) for _ in range(8)]
    res = [(p.wait(), p.stdout.read(), p.stderr.read()) for p in procs]
    rcs = [r[0] for r in res]
    check("a_exactly_one_success", rcs.count(0) == 1, f"rcs={rcs}")
    refusals = [(rc, err) for rc, _out, err in res if rc != 0]
    check("a_seven_refused",
          len(refusals) == 7 and all(rc in (2, 3) and "REFUSED" in o
                                     for rc, o in refusals),
          "; ".join(f"rc={rc}:{o.strip()[:90]}" for rc, o in refusals[:2]))


def test_b_different_samples(check):
    gd = new_guard_dir()
    env = env_for(gd)
    procs = [subprocess.Popen(
        [sys.executable, str(GUARD), "claim-acquire", "--campaign", "concB",
         "--runid", "A01-F1-W3", "--sample", f"s{i}", "--desc", f"conc-b-{i}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        for i in range(8)]
    res = [(p.wait(), p.stderr.read()) for p in procs]
    check("b_all_eight_success",
          all(rc == 0 for rc, _ in res),
          "; ".join(f"rc={rc}:{e.strip()[:80]}" for rc, e in res if rc != 0))
    files = sorted(Path(gd, "claims", "concB", "A01-F1-W3").glob("*.claim"))
    check("b_eight_claim_files", len(files) == 8, str(files))


def test_c_slot_race(check):
    gd = new_guard_dir()
    env = env_for(gd, slots=2)
    wrapper = LINGER_ACQUIRE.format(tools=str(TOOLS), linger=3)
    procs = [subprocess.Popen(
        [sys.executable, "-c", wrapper, "acquire", "--type", "experiment",
         "--desc", f"conc-c-{i}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
        for i in range(6)]
    res = [(p.wait(), p.stdout.read(), p.stderr.read()) for p in procs]
    rcs = [r[0] for r in res]
    succ = [json.loads(o) for rc, o, _ in res if rc == 0]
    check("c_exactly_two_success", len(succ) == 2, f"rcs={rcs}")
    slots = sorted(d.get("slot") for d in succ)
    check("c_slots_are_0_and_1_descending", slots == [0, 1], f"slots={slots}")
    refusals = [(rc, e) for rc, _, e in res if rc != 0]
    check("c_four_refused_all_occupied",
          len(refusals) == 4 and all(rc == 2 and "REFUSED" in e
                                     and "全部被占" in e for rc, e in refusals),
          "; ".join(f"rc={rc}:{e.strip()[:90]}" for rc, e in refusals[:2]))


def test_d_run_concurrency_cap(check):
    gd = new_guard_dir()
    env = env_for(gd, slots=3)
    ntask = 6
    deadline = time.time() + 240
    pending = list(range(ntask))
    retry_at = {}        # tid -> 重试最早时刻（退避，降低 hammer 强度）
    active = {}          # tid -> (Popen, out_path, fileobj)
    done, fatal = {}, None
    refusals = transient_stale = transient_gate_stale = 0
    peak = peak_locks = 0

    def launch(tid):
        out = Path(gd) / f"task{tid}_guard.out"
        f = open(out, "w")
        p = subprocess.Popen(
            [sys.executable, str(GUARD), "run", "--type", "experiment",
             "--desc", f"conc-d-{tid}",
             "--log", str(Path(gd) / f"task{tid}_rsrc.log"),
             "--interval", "1", "--", "sleep", "3"],
            stdout=f, stderr=subprocess.STDOUT, env=env)
        active[tid] = (p, out, f)

    def requeue(tid, delay=0.5):
        retry_at[tid] = time.time() + delay
        pending.append(tid)

    def stale_is_transient():
        """1s 后复核：锁已消失=释放竞态瞬态（True）；死锁持续=真陈旧（False）。"""
        time.sleep(1.0)
        return not dead_locks(gd)

    try:
        while (pending or active) and time.time() < deadline:
            now = time.time()
            for tid in list(pending):
                if retry_at.get(tid, 0) <= now:
                    pending.remove(tid)
                    launch(tid)
            time.sleep(0.1)
            locks = read_locks(gd)
            peak_locks = max(peak_locks, len(locks))
            peak = max(peak, live_sleeps(gd))
            for tid in list(active):
                p, out, f = active[tid]
                rc = p.poll()
                if rc is None:
                    continue
                f.close()
                active.pop(tid)
                txt = out.read_text(errors="replace")
                if (rc == 0 and '"action": "run-finish"' in txt
                        and '"exit_code": 0' in txt
                        and '"monitor_reason": "target-exited"' in txt):
                    done[tid] = rc
                elif rc == 2 and "全部被占" in txt:
                    refusals += 1
                    requeue(tid)
                elif rc == 2 and "陈旧" in txt:
                    # 释放竞态路径一（见模块 docstring）：acquire 判陈旧
                    if stale_is_transient():
                        transient_stale += 1
                        requeue(tid)
                    else:
                        fatal = f"持续陈旧锁（非瞬态释放竞态）: {dead_locks(gd)}"
                        break
                elif rc == 1 and "陈旧槽" in txt:
                    # 释放竞态路径二：重试进程的 gate 撞上同一窗口
                    # （目标 sleep 已退出、锁尚未 unlink 的 ~0.1-0.5s）
                    if stale_is_transient():
                        transient_gate_stale += 1
                        requeue(tid)
                    else:
                        fatal = f"gate 持续报陈旧槽: {txt[-400:]!r}"
                        break
                else:
                    fatal = f"task{tid} 异常退出 rc={rc}: {txt[-400:]!r}"
                    break
            if fatal:
                break
    finally:
        for tid in list(active):
            p, out, f = active.pop(tid)
            try:
                p.wait(timeout=30)   # sleep 3 自终；只等不杀
            except subprocess.TimeoutExpired:
                fatal = fatal or f"task{tid} 30s 未退出"
            f.close()

    check("d_no_fatal", fatal is None, str(fatal))
    check("d_all_six_run_finish", len(done) == ntask, f"done={sorted(done)}")
    check("d_peak_live_sleeps_le_3", peak <= 3, f"peak={peak}")
    check("d_contention_refusals_ge_3", refusals >= 3, f"refusals={refusals}")
    leftovers = list(Path(gd).glob("experiment_slot_*.lock"))
    check("d_all_locks_released", not leftovers, str(leftovers))
    print(f"    [d] peak_live_sleeps={peak} peak_lock_files={peak_locks} "
          f"refusals={refusals} transient_stale_refusals={transient_stale} "
          f"transient_gate_stale_refusals={transient_gate_stale}")


def test_e_heartbeat(check):
    gd = new_guard_dir()
    env = env_for(gd, slots=4)
    out = Path(gd) / "e_guard.out"
    f = open(out, "w")
    p = subprocess.Popen(
        [sys.executable, str(GUARD), "run", "--type", "experiment",
         "--desc", "conc-e-heartbeat", "--log", str(Path(gd) / "e_rsrc.log"),
         "--interval", "5", "--", "sleep", "65"],
        stdout=f, stderr=subprocess.STDOUT, env=env)
    beats = []
    t0 = time.time()
    try:
        while p.poll() is None and time.time() - t0 < 120:
            for d in read_locks(gd):
                hb = d.get("heartbeat")
                if hb and (not beats or hb != beats[-1]):
                    beats.append(hb)
            if len(beats) >= 4:
                break
            time.sleep(2)
    finally:
        rc = p.wait(timeout=150)
        f.close()
    txt = out.read_text(errors="replace")
    check("e_run_finish",
          rc == 0 and '"action": "run-finish"' in txt
          and '"exit_code": 0' in txt,
          f"rc={rc} tail={txt[-300:]!r}")
    check("e_heartbeat_seen_and_updated", len(beats) >= 2, f"beats={beats}")
    check("e_heartbeat_monotonic", beats == sorted(beats), f"beats={beats}")
    leftovers = list(Path(gd).glob("experiment_slot_*.lock"))
    check("e_lock_released", not leftovers, str(leftovers))
    print(f"    [e] heartbeats observed: {beats}")


def env_precheck(check):
    mi = {}
    with open("/proc/meminfo") as fh:
        for line in fh:
            k, _, v = line.partition(":")
            mi[k.strip()] = int(v.split()[0]) / 1048576.0  # kB -> GiB
    mem, swap = mi.get("MemAvailable", 0.0), mi.get("SwapFree", 0.0)
    ok = mem >= 11.0 and swap >= 4.0
    check("env_mem_available_ge_11gib", mem >= 11.0, f"{mem:.2f} GiB")
    check("env_swap_free_ge_4gib", swap >= 4.0, f"{swap:.2f} GiB")
    if not ok:
        print("ENV-FAIL: 内存/swap 低于 gate 阈值余量，(c)(d)(e) 无法真实执行"
              "（拒绝静默跳过：环境不可验收=失败）")
    return ok


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name,
               "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    try:
        test_a_claim_uniqueness(check)
        test_b_different_samples(check)
        env_ok = env_precheck(check)
        if env_ok:
            test_c_slot_race(check)
            test_d_run_concurrency_cap(check)
            test_e_heartbeat(check)
    finally:
        shutil.rmtree(TMP_ROOT, ignore_errors=True)

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
