#!/usr/bin/env python3
"""test_lsu_guard_v2.py — guard v2 语义单测（隔离 LSU_GUARD_DIR，绝不碰主锁目录）。

覆盖（LSU OBS 计划 T1，用户指令 2026-10-12 三.1）：
  1  LSU_GUARD_SLOTS 槽位数化 + experiment 降序抢占（先占高位槽）
  2  锁记录 pid_start；PID 复用（活 PID + 错误 starttime）必须判陈旧并拒绝
  3  clear-stale 可处置 pid_start 不符的"复用 PID"锁（--confirm-dead-pid 匹配）
  4  claim 锁 O_EXCL 唯一 + 拒绝他人释放 + status 可见
  5  STOP_DISPATCH 阈值（<10GiB 停止加任务）
  6  磁盘红线 max(50GiB, 20%×total)
  7  心跳原子重写（tmp+replace，读者永见完整 JSON）
  8  向后兼容：v1 旧格式锁（无 pid_start）可解析、存活判定退化为纯 PID

用法：python3 tests/test_lsu_guard_v2.py   （退出码 0=全 PASS）
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUARD = HERE.parent / "tools" / "lsu_guard.py"


def run_guard(env, *argv):
    r = subprocess.run([sys.executable, str(GUARD), *argv],
                       capture_output=True, text=True, env={**os.environ, **env})
    return r.returncode, r.stdout, r.stderr


def forge_lock(path, pid, pid_start, slot, desc="forged"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "owner": "test", "pid": pid, "pgid": pid, "pid_start": pid_start,
        "task_type": "experiment", "desc": desc,
        "started": "2026-01-01 00:00:00", "slot": slot}))


def main():
    tmp = tempfile.mkdtemp(prefix="guard_v2_test_")
    env = {"LSU_GUARD_DIR": tmp, "LSU_GUARD_SLOTS": "6"}
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name, "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # ---- 1) 槽位数化 + 降序抢占：空目录首取应拿 slot 5，其次 4 ----
    rc, out, err = run_guard(env, "acquire", "--type", "experiment", "--desc", "t1")
    lock = json.loads(out) if rc == 0 else {}
    check("slots_env_and_descending_first_takes_5",
          rc == 0 and lock.get("slot") == 5, f"rc={rc} out={out!r} err={err!r}")
    check("pid_start_recorded", isinstance(lock.get("pid_start"), int), out)
    check("campaign_sample_fields",
          lock.get("campaign") is None and lock.get("sample") is None, out)
    # acquire 子进程已退出 -> 该槽为陈旧锁：先按 F-023 语义确认拒绝，再显式处置
    rc_stale, _, err_stale = run_guard(env, "acquire", "--type", "experiment", "--desc", "t1b")
    check("dead_pid_slot_is_stale_refusal",
          rc_stale != 0 and "陈旧" in err_stale, err_stale)
    rc_cs, out_cs, _ = run_guard(env, "clear-stale", "--type", "experiment",
                                 "--confirm-dead-pid", str(lock.get("pid")))
    check("clear_stale_dead_pid", rc_cs == 0 and "CLEARED" in out_cs, out_cs)

    # 伪造"活"锁（pid=本测试进程 + 正确 pid_start）占 slot 5 -> 下一个应拿 slot 4
    sys.path.insert(0, str(GUARD.parent))
    os.environ.update(env)
    import lsu_guard as G  # noqa: E402  （env 已设，模块常量按 v2 语义加载）
    my_start = G._pid_start_ticks(os.getpid())
    forge_lock(Path(tmp, "experiment_slot_5.lock"), os.getpid(), my_start, 5, "live5")
    rc2, out2, err2 = run_guard(env, "acquire", "--type", "experiment", "--desc", "t2")
    check("live_lock_skipped_next_takes_4",
          rc2 == 0 and json.loads(out2).get("slot") == 4, f"rc={rc2} err={err2!r}")
    # live5 的使命（验证活锁被跳过）已完成，移除测试产物——否则后续 clear-stale
    # 会因它仍存活而 rc=2（正确行为，但会干扰下述断言）
    Path(tmp, "experiment_slot_5.lock").unlink()
    # t2 的 acquire 子进程已退出 -> slot 4 留下陈旧锁，先显式处置，
    # 保证后续"复用 PID 拒绝"测试指向 slot 0 而非 slot 4
    rc_cs_t2, out_cs_t2, _ = run_guard(env, "clear-stale", "--type", "experiment",
                                       "--confirm-dead-pid",
                                       str(json.loads(out2).get("pid")))
    check("clear_stale_t2", rc_cs_t2 == 0 and "CLEARED" in out_cs_t2, out_cs_t2)

    # ---- 2) PID 复用免疫：活 PID + 错误 starttime -> 陈旧 ----
    forge_lock(Path(tmp, "experiment_slot_0.lock"), os.getpid(), 1, 0, "recycled")
    check("lock_live_rejects_recycled_pid",
          G._lock_live(json.loads(Path(tmp, "experiment_slot_0.lock").read_text())) is False)
    check("lock_live_accepts_genuine",
          G._lock_live({"pid": os.getpid(), "pid_start": my_start}) is True)
    check("lock_live_v1_compat_no_pid_start",
          G._lock_live({"pid": os.getpid()}) is True)
    rc3, _, err3 = run_guard(env, "acquire", "--type", "experiment", "--desc", "t3")
    check("recycled_pid_slot_refused_on_acquire",
          rc3 != 0 and "陈旧" in err3 and "slot 0" in err3, err3)

    # ---- 3) clear-stale 处置复用 PID 锁（pid 活但 pid_start 不符） ----
    rc_cs2, out_cs2, _ = run_guard(env, "clear-stale", "--type", "experiment",
                                   "--confirm-dead-pid", str(os.getpid()))
    check("clear_stale_recycled_pid",
          rc_cs2 == 0 and "CLEARED" in out_cs2, f"rc={rc_cs2} out={out_cs2!r}")

    # ---- 4) claim 锁：进程内 acquire 唯一性 + 他人释放拒绝 + status 可见 ----
    c1, r1 = G._claim_acquire("campX", "A01-F0-W9", "s322", "driver-A")
    c2, r2 = G._claim_acquire("campX", "A01-F0-W9", "s322", "driver-B")
    check("claim_exclusive_inproc", c1 is not None and c2 is None and "REFUSED" in r2, r2)
    ok, msg, _ = G._claim_release("campX", "A01-F0-W9", "s322", confirm_pid=999999)
    check("claim_release_wrong_pid_refused", ok is False, msg)
    ok2, msg2, _ = G._claim_release("campX", "A01-F0-W9", "s322",
                                    confirm_pid=os.getpid())
    check("claim_release_ok", ok2 is True, msg2)
    rc_ca, out_ca, err_ca = run_guard(env, "claim-acquire", "--campaign", "campCLI",
                                      "--runid", "R", "--sample", "s0", "--desc", "d")
    check("claim_cli_creates_file",
          rc_ca == 0 and Path(tmp, "claims/campCLI/R/s0.claim").exists(), err_ca)
    rc_st, out_st, _ = run_guard(env, "status")
    check("claims_in_status", rc_st == 0 and "campCLI" in out_st, out_st[:300])
    check("status_shows_beyond_configured_slots", "slot_5" in out_st, out_st[:300])
    check("status_shows_configured_cap",
          '"experiment_slots_configured": 6' in out_st, out_st[:300])

    # ---- 5) STOP_DISPATCH ----
    snap = {"mem_available_gib": 9.5, "swap_free_gib": 14.0}
    check("stop_dispatch_below_10", G._stop_dispatch(snap) is True)
    snap["mem_available_gib"] = 16.0
    check("stop_dispatch_ok_at_16", G._stop_dispatch(snap) is False)

    # ---- 6) 磁盘红线 ----
    # 2026-10-23 用户裁决：「去掉 /home 存储的约束」——仅去百分比判据，保留 50 GiB 绝对下限。
    # 本检查改指向**当前**口径：60 GiB 在 354 GiB 盘上高于绝对下限 → 放行（旧口径会因 20% 而拒绝）。
    check("disk_guard_pct_waived_20261023",
          G._disk_guard_reason(free_gib=60.0, total_gib=354.0) is None)
    check("disk_guard_50gib_floor",
          G._disk_guard_reason(free_gib=45.0, total_gib=100.0) is not None)
    check("disk_guard_pass", G._disk_guard_reason(free_gib=90.0, total_gib=354.0) is None)

    # ---- 7) 心跳原子重写 ----
    lp = Path(tmp, "experiment_slot_2.lock")
    lp.write_text(json.dumps({"pid": 1, "desc": "hb"}))
    G._write_lock_atomic(str(lp), {"pid": 1, "desc": "hb", "heartbeat": "T1"})
    time.sleep(0.01)
    G._write_lock_atomic(str(lp), {"pid": 1, "desc": "hb", "heartbeat": "T2"})
    check("heartbeat_atomic_valid_json",
          json.loads(lp.read_text())["heartbeat"] == "T2")
    leftovers = list(Path(tmp).glob("*.tmp.*"))
    check("heartbeat_no_tmp_leftover", not leftovers, str(leftovers))

    # ---- 8) 旧格式锁（v1，无 pid_start）可解析 + 槽上限校验 ----
    p0 = Path(tmp, "experiment_slot_3.lock")
    p0.write_text(json.dumps({"owner": "x", "pid": -1, "pgid": -1,
                              "task_type": "experiment", "desc": "oldstyle",
                              "started": "x", "slot": 3}))
    check("v1_lock_parses", G._read_lock("experiment", 3).get("desc") == "oldstyle")
    rc_over, _, err_over = run_guard({"LSU_GUARD_DIR": tmp, "LSU_GUARD_SLOTS": "9"},
                                      "status")
    check("slots_cap_enforced_at_8",
          rc_over != 0 and "LSU_GUARD_SLOTS" in err_over, err_over)

    # ---- 9) 创建原子性（OBS-FIX-4）：窗口内读者永不见空/半锁文件 ----
    # 根因（今日 5 次进程死亡：D 11:55/13:01、C02 12:46/15:07、claim 测试
    # 14:44）：旧创建路径 O_CREAT|O_EXCL 先落空文件、json.dump 后才有
    # 内容——并发读者读到空/半文件即判"锁文件损坏"（F-023 立即失败）。
    # 修复 = tmp 写全内容 + os.link 原子发布（读者只见"不存在"或完整）。
    import threading
    gd2 = Path(tempfile.mkdtemp(prefix="guard_atomic_"))
    old_gd = G.GUARD_DIR
    G.GUARD_DIR = str(gd2)
    orig_dump = G.json.dump
    torn_seen = []
    acquired = {}

    def slow_dump(obj, fh, **kw):
        fh.write('{"torn": ')          # 模拟 dump 写入中（半文件）
        fh.flush()
        time.sleep(0.5)                # 窗口确定性放大
        fh.seek(0)
        fh.truncate()
        orig_dump(obj, fh, **kw)

    def writer():
        G.json.dump = slow_dump
        try:
            acquired["lock"], acquired["err"] = G._try_acquire(
                "experiment", "atomic-window-test")
        finally:
            G.json.dump = orig_dump

    th = threading.Thread(target=writer)
    th.start()
    deadline = time.time() + 1.2
    while time.time() < deadline and th.is_alive():
        p5 = gd2 / "experiment_slot_5.lock"
        if p5.exists():
            raw = p5.read_bytes()
            if raw:
                try:
                    json.loads(raw)
                    torn_seen.append(("ok", len(raw)))
                except Exception:
                    torn_seen.append(("TORN", len(raw)))
        time.sleep(0.02)
    th.join()
    G.GUARD_DIR = old_gd
    check("r1_no_torn_lock_visible",
          not torn_seen and acquired.get("lock") is not None,
          f"torn={torn_seen[:4]} lock={acquired.get('lock')} "
          f"err={acquired.get('err')}")

    # ---- 10) 并发抢占：16 进程 × 6 槽恰 6 成功，锁全可解析，无 tmp 残留 ----
    gd3 = Path(tempfile.mkdtemp(prefix="guard_race_"))
    env3 = {"LSU_GUARD_DIR": str(gd3), "LSU_GUARD_SLOTS": "6"}
    procs = [subprocess.Popen(
        [sys.executable, str(GUARD), "acquire", "--type", "experiment",
         "--desc", f"race{i}"], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, env={**os.environ, **env3})
        for i in range(16)]
    rcs = [p.wait() for p in procs]
    n_ok = sum(1 for rc in rcs if rc == 0)
    parsed = []
    for s in range(6):
        f = gd3 / f"experiment_slot_{s}.lock"
        if f.exists():
            json.loads(f.read_text())      # 不可解析即抛异常 = 失败
            parsed.append(s)
    leftovers = list(gd3.glob("*.tmp.*"))
    check("r2_race_exactly_6_win",
          n_ok == 6 and len(parsed) == 6,
          f"n_ok={n_ok} parsed={parsed} rcs={rcs}")
    check("r2_no_tmp_leftover", not leftovers, str(leftovers))

    # 清场：处置测试进程写下的 claim（陈旧：子进程已退出）
    run_guard(env, "clear-stale", "--type", "claim", "--confirm-dead-pid", "0")
    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
