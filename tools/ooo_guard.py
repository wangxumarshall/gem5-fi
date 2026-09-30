#!/usr/bin/env python3
"""ooo_guard.py — OOO 故障注入任务资源守卫（总方针 §8 硬限制的可审计实现）。

适配自 LSU 轨 tools/lsu_guard.py@f0a5b249（4 槽位实验锁版，F-022/F-023 同源设计），差异：
  1) 锁目录 runs/ooo/guard/（build.lock / experiment_slot_0..3.lock / guard_events.log）；
     环境变量名 OOO_GUARD_DIR（隔离测试用）；
  2) NSCC 集群 login01 与计算节点均无 swap（SwapTotal=0，findings F-005）——
     swap 类门禁/TRIP 仅在 SwapTotal>0 时评估，无 swap 主机豁免并在输出中显式
     标注（gate 的 swap_exempt_note），MemAvailable 为权威指标。

子命令：
  gate / acquire / release / clear-stale / status / run / sample（语义同 f0a5b249 版 lsu_guard.py：
  build 单实例；experiment 4 槽位=实验并发硬上限 4；释放须 --slot+--confirm-pid；
  陈旧锁必须 clear-stale 显式处置，不静默绕过）。

阈值（总方针 §8.3/§8.4，GiB=2^30）：
  GATE 阻断: MemAvailable < 12，或（SwapTotal>0 且 SwapFree < 4），或存在编译进程或锁被占
  WARNING  : MemAvailable < 10
  TRIP     : MemAvailable < 8 连续两次，或任一次 < 6，或（SwapTotal>0 且 SwapFree < 2）
  TRIP 处置: 仅对锁内记录、经存活性核实的本任务 PGID 先 TERM 后 KILL（§8.4）

锁目录: runs/ooo/guard/。纯标准库实现，直接读 /proc，不依赖 psutil。
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time

GUARD_DIR = os.environ.get(
    "OOO_GUARD_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "runs", "ooo", "guard"))
GIB = 1024 * 1024 * 1024.0
# F-022（用户指令 2026-09-30 14:30）：gem5 实验并发硬上限 4。
# experiment 锁为 4 槽位 experiment_slot_{0..3}.lock；build 锁保持单实例。
EXPERIMENT_SLOTS = 4
GATE_MEM_MIN_GIB = 12.0
GATE_SWAP_MIN_GIB = 4.0
WARN_MEM_GIB = 10.0
TRIP_MEM_GIB = 8.0
TRIP_MEM_HARD_GIB = 6.0
TRIP_SWAP_GIB = 2.0
TRIP_TERM_GRACE_S = 30
COMPILE_COMMS = {"scons", "make", "ninja", "gcc", "g++", "gcc-12", "g++-12",
                 "clang", "clang++", "cc1plus", "cc1", "as", "ld", "ld.bfd"}


def _meminfo():
    out = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, _, v = line.partition(":")
            out[k.strip()] = int(v.split()[0]) * 1024  # kB -> B
    return out


def _loadavg():
    with open("/proc/loadavg") as f:
        p = f.read().split()
    return float(p[0]), float(p[1]), float(p[2])


def _proc_fields(pid):
    """返回 (state, pgrp, rss_pages, comm) 或 None。

    /proc/[pid]/stat: tail[0]=state(字段3), tail[2]=pgrp(字段5),
    tail[21]=rss 页数(字段24; tail[20] 是 vsize 字节，勿混用)。
    """
    try:
        with open(f"/proc/{pid}/stat") as f:
            data = f.read()
    except (FileNotFoundError, ProcessLookupError):
        return None
    rp = data.rpartition(")")
    if not rp[1]:
        return None
    tail = rp[2].split()
    try:
        state, pgrp, rss = tail[0], int(tail[2]), int(tail[21])
    except (IndexError, ValueError):
        return None
    comm = rp[0].partition("(")[2]
    return state, pgrp, rss, comm


def snapshot():
    """资源快照：内存/swap/load/blocked/编译进程/磁盘。"""
    mi = _meminfo()
    l1, l5, l15 = _loadavg()
    blocked, compile_pids = [], []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        pf = _proc_fields(pid)
        if pf is None:
            continue
        state, pgrp, rss, comm = pf
        if state == "D":
            blocked.append(int(pid))
        if comm in COMPILE_COMMS:
            compile_pids.append({"pid": int(pid), "comm": comm})
    return {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mem_available_gib": round(mi.get("MemAvailable", 0) / GIB, 2),
        "swap_free_gib": round(mi.get("SwapFree", 0) / GIB, 2),
        "swap_total_gib": round(mi.get("SwapTotal", 0) / GIB, 2),
        "swap_exempt": mi.get("SwapTotal", 0) == 0,
        "committed_as_gib": round(mi.get("Committed_AS", 0) / GIB, 2),
        "load_1_5_15": [l1, l5, l15],
        "blocked": blocked,
        "compile_processes": compile_pids,
        "disk_free_gib": round(shutil.disk_usage(GUARD_DIR).free / GIB, 1)
        if os.path.isdir(GUARD_DIR) else None,
    }


def _log_event(evt):
    os.makedirs(GUARD_DIR, exist_ok=True)
    with open(os.path.join(GUARD_DIR, "guard_events.log"), "a") as f:
        f.write(json.dumps(evt, ensure_ascii=False) + "\n")


def _lock_path(task_type, slot=None):
    """锁文件路径。experiment 为 4 槽位：slot 必须显式给定（或用 _slots_state 遍历）。"""
    if task_type == "experiment":
        if slot is None:
            raise ValueError("experiment 锁需要显式 slot（0..%d）" % (EXPERIMENT_SLOTS - 1))
        return os.path.join(GUARD_DIR, f"experiment_slot_{slot}.lock")
    return os.path.join(GUARD_DIR, f"{task_type}.lock")


def _read_lock(task_type, slot=None):
    p = _lock_path(task_type, slot)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"corrupt": True, "path": p}


def _slots_state():
    """experiment 4 槽位状态：{slot: lock|None}。"""
    return {i: _read_lock("experiment", i) for i in range(EXPERIMENT_SLOTS)}


def _slot_holders():
    """占用/异常槽摘要（诊断信息用）：[(slot, pid, desc, live)]。"""
    out = []
    for i, lock in _slots_state().items():
        if lock is None:
            continue
        if lock.get("corrupt"):
            out.append((i, None, "corrupt", False))
        else:
            out.append((i, lock.get("pid"), lock.get("desc", "?"),
                        _pid_alive(lock.get("pid", -1))))
    return out


def _pid_alive(pid):
    return os.path.exists(f"/proc/{pid}")


def _gate_result():
    """启动门禁判定（进程内，供 cmd_gate 与 cmd_run 复用）。"""
    snap = snapshot()
    build_lock = _read_lock("build")
    slots = _slots_state()
    occupied = [i for i, lk in slots.items()
                if lk is not None and not lk.get("corrupt")]
    stale = [i for i, lk in slots.items()
             if lk is not None and not lk.get("corrupt")
             and not _pid_alive(lk.get("pid", -1))]
    reasons = []
    if snap["mem_available_gib"] < GATE_MEM_MIN_GIB:
        reasons.append(f"MemAvailable {snap['mem_available_gib']} GiB < {GATE_MEM_MIN_GIB} GiB")
    if snap["swap_total_gib"] > 0 and snap["swap_free_gib"] < GATE_SWAP_MIN_GIB:
        reasons.append(f"SwapFree {snap['swap_free_gib']} GiB < {GATE_SWAP_MIN_GIB} GiB")
    if snap["compile_processes"]:
        reasons.append(f"存在编译进程: {snap['compile_processes']}")
    if len(snap["blocked"]) >= 8:
        reasons.append(f"blocked 进程过多: {snap['blocked']}")
    if build_lock and not build_lock.get("corrupt"):
        reasons.append(f"build 锁被占: pid={build_lock.get('pid')}")
    if stale:
        # 陈旧槽本身由 acquire 拒绝并提示 clear-stale；gate 一并提示便于诊断
        reasons.append(f"experiment 存在陈旧槽 {stale}（clear-stale 处置前 acquire 将拒绝）")
    return {"action": "gate", "ok": not reasons, "reasons": reasons, "snapshot": snap,
            "swap_exempt_note": ("SwapTotal=0（本集群无 swap，findings F-005）："
                                 "swap 门禁豁免，MemAvailable 为权威"
                                 if snap["swap_exempt"] else None),
            "experiment_slots_occupied": len(occupied),
            "experiment_slots_total": EXPERIMENT_SLOTS}


def cmd_gate(args):
    result = _gate_result()
    _log_event(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


def _try_acquire(task_type, desc, item=None, runid=None, log=None):
    """进程内获取锁（cmd_run 与 CLI acquire 共用）。返回 (lock, None) 或 (None, reason)。

    锁 pid = 调用进程 pid（cmd_run 进程内调用时存活至 run 结束，消除
    acquire 子进程短命 pid 被并行者误判陈旧的竞态——F-022 重构要点）。
    """
    os.makedirs(GUARD_DIR, exist_ok=True)
    base_lock = {
        "owner": os.environ.get("USER")
        or (os.getlogin() if hasattr(os, "getlogin") else "unknown"),
        "pid": os.getpid(),
        "pgid": os.getpgid(0),
        "task_type": task_type,
        "desc": desc,
        "item": item,
        "runid": runid,
        "log": os.path.abspath(log) if log else None,
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "acquire_host_pid_tree_note": "run 子命令会在派生子进程后更新 pid/pgid",
    }
    # 候选路径：build 单锁；experiment 4 槽位（F-022）
    if task_type == "build":
        candidates = [(None, _lock_path("build"))]
    else:
        candidates = [(i, _lock_path("experiment", i))
                      for i in range(EXPERIMENT_SLOTS)]
    # 诊断既有锁：corrupt 立即拒；陈旧锁须 clear-stale 显式处置（F-023 语义：
    # 不静默绕过异常中断的守卫周期）；存活占用只是跳过（并行语义）
    holders = []
    for slot, path in candidates:
        if not os.path.exists(path):
            continue
        old = _read_lock(task_type, slot)
        if old is None:
            continue
        if old.get("corrupt"):
            return None, f"REFUSED: 锁文件损坏 {path}，用 clear-stale 处置"
        if _pid_alive(old.get("pid", -1)):
            holders.append((slot, old))
        else:
            return None, (f"REFUSED: {task_type} "
                          f"{'slot ' + str(slot) + ' ' if slot is not None else ''}"
                          f"陈旧锁（pid={old.get('pid')} 已退出但未记录处置）；"
                          f"先 clear-stale 显式处置")
    # 抢空槽：O_EXCL 原子创建防并发双取；撞槽（EEXIST）自动试下一候选
    for slot, path in candidates:
        if os.path.exists(path):
            continue
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            continue
        lock = {**base_lock, "slot": slot} if slot is not None else base_lock
        with os.fdopen(fd, "w") as f:
            json.dump(lock, f, ensure_ascii=False, indent=2)
        _log_event({"action": "acquire", **lock})
        return lock, None
    detail = "\n".join(
        f"  {'slot ' + str(s) + ': ' if s is not None else ''}pid={o.get('pid')} "
        f"({o.get('desc', '?')})" for s, o in holders) or "  （锁文件在诊断后被外部创建）"
    return None, (f"REFUSED: {task_type} 锁全部被占"
                  f"（experiment 上限 {EXPERIMENT_SLOTS} 槽；资源压力下可降 3/2/1，见总方针 §8.1）：\n"
                  + detail)


def cmd_acquire(args):
    lock, reason = _try_acquire(args.type, args.desc, args.item, args.runid, args.log)
    if lock is None:
        print(reason, file=sys.stderr)
        return 3 if "陈旧锁" in reason else 2
    print(json.dumps(lock, ensure_ascii=False))
    return 0


def _release(task_type, slot=None, confirm_pid=None):
    """进程内释放锁（cmd_run 与 CLI release 共用）。返回 (ok, msg, path)。"""
    if task_type == "experiment":
        if slot is None or confirm_pid is None:
            return False, ("REFUSED: experiment 释放须 --slot N --confirm-pid PID"
                           "（防并行误删他人槽）"), None
        path = _lock_path("experiment", slot)
        lock = _read_lock("experiment", slot)
        if lock is None:
            return True, f"NOTE: experiment slot {slot} 锁不存在，无需释放", None
        if lock.get("corrupt"):
            return False, f"REFUSED: 槽 {slot} 锁损坏，用 clear-stale 处置", path
        if str(lock.get("pid")) != str(confirm_pid):
            return False, (f"REFUSED: --confirm-pid {confirm_pid} 与槽 {slot} 锁内 pid "
                           f"{lock.get('pid')} 不符（不得释放他人槽）"), path
    else:
        path = _lock_path(task_type)
        lock = _read_lock(task_type)
        if lock is None:
            return True, f"NOTE: {task_type} 锁不存在，无需释放", None
    os.unlink(path)
    _log_event({"action": "release", "released_lock": lock,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    return True, f"RELEASED: {path}", path


def cmd_release(args):
    ok, msg, _path = _release(args.type, args.slot, args.confirm_pid)
    if not ok:
        print(msg, file=sys.stderr)
        return 2
    print(msg)
    return 0


def cmd_clear_stale(args):
    if args.type == "experiment":
        # F-022：扫描全部槽，清除 pid 匹配且已死的槽；报告其余槽状态
        cleared, refused, remaining = [], [], []
        for slot in range(EXPERIMENT_SLOTS):
            path = _lock_path("experiment", slot)
            if not os.path.exists(path):
                continue
            lock = _read_lock("experiment", slot)
            if lock is None:
                continue
            if lock.get("corrupt"):
                os.unlink(path)
                _log_event({"action": "clear-stale-corrupt", "path": path})
                cleared.append((slot, "corrupt", path))
                continue
            if _pid_alive(lock.get("pid", -1)):
                refused.append((slot, lock.get("pid")))
                continue
            if str(lock.get("pid")) != str(args.confirm_dead_pid):
                remaining.append((slot, lock.get("pid")))
                continue
            os.unlink(path)
            _log_event({"action": "clear-stale", "cleared": lock,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S")})
            cleared.append((slot, lock.get("pid"), path))
        for slot, pid, path in cleared:
            print(f"CLEARED stale lock (pid {pid} confirmed dead): {path}")
        for slot, pid in refused:
            print(f"REFUSED: slot {slot} pid={pid} 仍存活，不是陈旧锁", file=sys.stderr)
        for slot, pid in remaining:
            print(f"NOTE: slot {slot} 陈旧 pid={pid} 与 --confirm-dead-pid 不符，未处置")
        if not (cleared or refused or remaining):
            print("NOTE: experiment 槽位无锁")
        return 0 if not refused else 2
    path = _lock_path(args.type)
    lock = _read_lock(args.type)
    if lock is None:
        print("NOTE: 锁不存在")
        return 0
    if lock.get("corrupt"):
        os.unlink(path)
        _log_event({"action": "clear-stale-corrupt", "path": path})
        print(f"CLEARED corrupt lock: {path}")
        return 0
    if _pid_alive(lock.get("pid", -1)):
        print(f"REFUSED: pid={lock['pid']} 仍存活，不是陈旧锁", file=sys.stderr)
        return 2
    if str(lock.get("pid")) != str(args.confirm_dead_pid):
        print(f"REFUSED: --confirm-dead-pid {args.confirm_dead_pid} 与锁内 pid "
              f"{lock.get('pid')} 不符", file=sys.stderr)
        return 2
    os.unlink(path)
    _log_event({"action": "clear-stale", "cleared": lock,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    print(f"CLEARED stale lock (pid {lock['pid']} confirmed dead): {path}")
    return 0


def cmd_status(args):
    out = {"build_lock": _read_lock("build"),
           "experiment_slots": {f"slot_{i}": _read_lock("experiment", i)
                                for i in range(EXPERIMENT_SLOTS)},
           "snapshot": snapshot()}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def _pgid_rss_gib(pgid):
    total = 0
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        pf = _proc_fields(pid)
        if pf and pf[1] == pgid:
            total += pf[2]
    return total * 4096 / GIB


def monitor(pgid, log_path, interval, max_seconds=None):
    """采样循环：写资源日志，检测 WARNING/TRIP；TRIP 时只终止锁内 PGID。

    返回 (exit_reason, last_snapshot)。exit_reason ∈ normal|target-exited|TRIP。
    """
    low_mem_streak = 0
    start = time.time()
    reason = "target-exited"
    while True:
        snap = snapshot()
        rec = {**snap, "task_rss_gib": round(_pgid_rss_gib(pgid), 2),
               "elapsed_s": round(time.time() - start, 1)}
        trip = None
        if snap["mem_available_gib"] < TRIP_MEM_GIB:
            low_mem_streak += 1
        else:
            low_mem_streak = 0
        if low_mem_streak >= 2:
            trip = f"MemAvailable<8GiB x{low_mem_streak}"
        if snap["mem_available_gib"] < TRIP_MEM_HARD_GIB:
            trip = f"MemAvailable<6GiB ({snap['mem_available_gib']})"
        if snap["swap_total_gib"] > 0 and snap["swap_free_gib"] < TRIP_SWAP_GIB:
            trip = f"SwapFree<2GiB ({snap['swap_free_gib']})"
        rec["warning"] = snap["mem_available_gib"] < WARN_MEM_GIB
        rec["trip"] = trip
        with open(log_path, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        _log_event({"action": "sample", "pgid": pgid, "warning": rec["warning"],
                    "trip": trip, "mem_available_gib": snap["mem_available_gib"]})
        if trip:
            reason = f"TRIP: {trip}"
            # 仅终止锁内记录且存活的 PGID：先 TERM，宽限后 KILL
            try:
                os.killpg(pgid, signal.SIGTERM)
                _log_event({"action": "trip-term", "pgid": pgid, "reason": reason})
                time.sleep(TRIP_TERM_GRACE_S)
                if any(_proc_fields(p) and _proc_fields(p)[1] == pgid
                       for p in os.listdir("/proc") if p.isdigit()):
                    os.killpg(pgid, signal.SIGKILL)
                    _log_event({"action": "trip-kill", "pgid": pgid, "reason": reason})
            except ProcessLookupError:
                pass
            break
        # 目标 PGID 是否仍有存活进程（僵尸 Z 不算存活：子进程退出后未收割前
        # 仍保留 pgrp 字段，会把已结束的任务误判为运行中，导致锁永不释放）
        alive = False
        for p in os.listdir("/proc"):
            if not p.isdigit():
                continue
            pf = _proc_fields(p)
            if pf and pf[1] == pgid and pf[0] != "Z":
                alive = True
                break
        if not alive:
            break
        if max_seconds and time.time() - start > max_seconds:
            reason = "max-seconds-reached"
            try:
                os.killpg(pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            break
        time.sleep(interval)
    return reason


def cmd_run(args):
    # F-022/F-023 重构：gate/acquire/release 全部进程内调用——锁 pid 即本进程 pid
    # （存活至 run 结束，消除 acquire 短命子进程 pid 被并行者误判陈旧的竞态），
    # 且 run 周期不再子进程重载本脚本（F-023 中 release 子进程撞损坏脚本的事故面根除）。
    # 1) 启动门禁
    gate = _gate_result()
    _log_event(gate)
    if not gate["ok"]:
        print("GATE BLOCKED:\n" + json.dumps(gate, ensure_ascii=False), file=sys.stderr)
        return 1
    # 2) 获取锁（experiment 返回锁含 slot）
    lock, reason = _try_acquire(args.type, args.desc, args.item, args.runid, args.log)
    if lock is None:
        print("ACQUIRE REFUSED:\n" + reason, file=sys.stderr)
        return 2
    slot = lock.get("slot")  # build 锁为 None
    proc = None
    try:
        # 3) 新进程组派生命令
        proc = subprocess.Popen(args.command, start_new_session=True)
        pgid = os.getpgid(proc.pid)
        # 锁内更新真实 pid/pgid（按 slot 定位锁文件）
        lock["pid"], lock["pgid"], lock["cmd"] = proc.pid, pgid, args.command
        with open(_lock_path(args.type, slot), "w") as f:
            json.dump(lock, f, ensure_ascii=False, indent=2)
        _log_event({"action": "spawn", "pid": proc.pid, "pgid": pgid,
                    "slot": slot, "cmd": args.cmd})
        print(f"SPAWNED pid={proc.pid} pgid={pgid}"
              f"{' slot=' + str(slot) if slot is not None else ''} log={args.log}")
        # 4) 采样监控
        reason = monitor(pgid, args.log, args.interval, args.max_seconds)
        # 5) 收割与总结
        rc = proc.wait()
        summary = {"action": "run-finish", "cmd": args.command, "pgid": pgid,
                   "exit_code": rc, "monitor_reason": reason,
                   "time": time.strftime("%Y-%m-%d %H:%M:%S")}
        _log_event(summary)
        print(json.dumps(summary, ensure_ascii=False))
        return rc
    finally:
        try:
            # experiment：按本 run 的槽位 + 派生 pid 精确释放（防并行误删他人槽）；
            # Popen 未及执行时用 acquire 记录的本进程 pid
            confirm_pid = proc.pid if proc is not None else lock.get("pid")
            ok, msg, _p = _release(args.type, slot, confirm_pid)
            if not ok:
                print(f"WARNING: 锁释放异常: {msg}", file=sys.stderr)
        except Exception as exc:  # 释放路径异常不得掩盖 run 的原始异常
            print(f"WARNING: 锁释放异常: {exc}", file=sys.stderr)


def cmd_sample(args):
    reason = monitor(args.pgid, args.log, args.interval, args.max_seconds)
    print(f"SAMPLER EXIT: {reason}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("gate")
    g.add_argument("--json", action="store_true")
    g.set_defaults(func=cmd_gate)

    a = sub.add_parser("acquire")
    a.add_argument("--type", choices=["build", "experiment"], required=True)
    a.add_argument("--desc", required=True)
    a.add_argument("--item", default=None)
    a.add_argument("--runid", default=None)
    a.add_argument("--log", default=None)
    a.set_defaults(func=cmd_acquire)

    r = sub.add_parser("release")
    r.add_argument("--type", choices=["build", "experiment"], default="build")
    r.add_argument("--slot", type=int, default=None,
                   help="experiment 槽位号（experiment 必填）")
    r.add_argument("--confirm-pid", dest="confirm_pid", default=None,
                   help="锁内记录的派生 pid（experiment 必填，防误删他人槽）")
    r.set_defaults(func=cmd_release)

    cs = sub.add_parser("clear-stale")
    cs.add_argument("--type", choices=["build", "experiment"], required=True)
    cs.add_argument("--confirm-dead-pid", required=True)
    cs.set_defaults(func=cmd_clear_stale)

    s = sub.add_parser("status")
    s.set_defaults(func=cmd_status)

    rn = sub.add_parser("run")
    rn.add_argument("--type", choices=["build", "experiment"], required=True)
    rn.add_argument("--desc", required=True)
    rn.add_argument("--log", required=True)
    rn.add_argument("--item", default=None)
    rn.add_argument("--runid", default=None)
    rn.add_argument("--interval", type=int, default=60)
    rn.add_argument("--max-seconds", type=int, default=None)
    # 注意：位置参数不能叫 cmd（与 subparsers 的 dest="cmd" 碰撞会覆盖子命令名）
    rn.add_argument("command", nargs=argparse.REMAINDER)
    rn.set_defaults(func=cmd_run)

    sm = sub.add_parser("sample")
    sm.add_argument("--pgid", type=int, required=True)
    sm.add_argument("--log", required=True)
    sm.add_argument("--interval", type=int, default=60)
    sm.add_argument("--max-seconds", type=int, default=None)
    sm.set_defaults(func=cmd_sample)

    args = ap.parse_args()
    if getattr(args, "command", None) is not None:
        cmdv = list(args.command)
        if cmdv and cmdv[0] == "--":
            cmdv = cmdv[1:]
        if not cmdv:
            ap.error("run 需要命令（推荐 '-- <command...>' 形式）")
        args.command = cmdv
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
