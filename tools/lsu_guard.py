#!/usr/bin/env python3
"""lsu_guard.py — LSU 故障注入任务资源守卫（总方针 §8 硬限制的可审计实现）。

子命令：
  gate    [--json]                启动前资源门禁采样与判定（§8.3）
  acquire --type build|experiment --desc <str> [--item ID] [--runid ID] [--log PATH]
                                  获取单实例锁（§8.2；锁含 owner/PID/PGID/日志路径）
  release [--type build|experiment]  释放锁并记录
  clear-stale --type ... --confirm-dead-pid <PID>  处置陈旧锁（须显式确认 PID 已死）
  status                          锁状态 + 当前资源快照
  run --type build --desc <str> --log <PATH> [--max-seconds N] -- <cmd...>
                                  全流程守卫执行：gate → acquire → 新 PGID 派生 →
                                  60 秒采样 → WARNING/TRIP 熔断 → release → 总结
  sample --pgid N --log PATH [--interval 60] [--max-seconds N]
                                  独立采样器（run 内部亦使用）

阈值（总方针 §8.3/§8.4，GiB=2^30）：
  GATE 阻断: MemAvailable < 12 或 SwapFree < 4 或存在编译进程或锁被占
  WARNING  : MemAvailable < 10
  TRIP     : MemAvailable < 8 连续两次，或任一次 < 6，或 SwapFree < 2
  TRIP 处置: 仅对锁内记录、经存活性核实的本任务 PGID 先 TERM 后 KILL（§8.4）

锁目录: runs/lsu/guard/（build.lock / experiment.lock / guard_events.log）
纯标准库实现，直接读 /proc，不依赖 psutil。
"""
import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import time

GUARD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "runs", "lsu", "guard")
GIB = 1024 * 1024 * 1024.0
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


def _lock_path(task_type):
    return os.path.join(GUARD_DIR, f"{task_type}.lock")


def _read_lock(task_type):
    p = _lock_path(task_type)
    if not os.path.exists(p):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"corrupt": True, "path": p}


def _pid_alive(pid):
    return os.path.exists(f"/proc/{pid}")


def cmd_gate(args):
    snap = snapshot()
    build_lock = _read_lock("build")
    exp_lock = _read_lock("experiment")
    reasons = []
    if snap["mem_available_gib"] < GATE_MEM_MIN_GIB:
        reasons.append(f"MemAvailable {snap['mem_available_gib']} GiB < {GATE_MEM_MIN_GIB} GiB")
    if snap["swap_free_gib"] < GATE_SWAP_MIN_GIB:
        reasons.append(f"SwapFree {snap['swap_free_gib']} GiB < {GATE_SWAP_MIN_GIB} GiB")
    if snap["compile_processes"]:
        reasons.append(f"存在编译进程: {snap['compile_processes']}")
    if len(snap["blocked"]) >= 8:
        reasons.append(f"blocked 进程过多: {snap['blocked']}")
    if build_lock and not build_lock.get("corrupt"):
        reasons.append(f"build 锁被占: pid={build_lock.get('pid')}")
    result = {"action": "gate", "ok": not reasons, "reasons": reasons, "snapshot": snap}
    _log_event(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not reasons else 1


def cmd_acquire(args):
    os.makedirs(GUARD_DIR, exist_ok=True)
    path = _lock_path(args.type)
    old = _read_lock(args.type)
    if old is not None:
        if old.get("corrupt"):
            print(f"REFUSED: 锁文件损坏 {path}，用 clear-stale 处置", file=sys.stderr)
            return 2
        if _pid_alive(old.get("pid", -1)):
            print(f"REFUSED: {args.type} 锁被 pid={old['pid']} pgid={old.get('pgid')} "
                  f"({old.get('desc','?')}) 持有", file=sys.stderr)
            return 2
        print(f"REFUSED: 陈旧锁（pid={old.get('pid')} 已退出但未记录处置）；"
              f"先 clear-stale 显式处置", file=sys.stderr)
        return 3
    lock = {
        "owner": os.environ.get("USER")
        or (os.getlogin() if hasattr(os, "getlogin") else "unknown"),
        "pid": os.getpid(),
        "pgid": os.getpgid(0),
        "task_type": args.type,
        "desc": args.desc,
        "item": args.item,
        "runid": args.runid,
        "log": os.path.abspath(args.log) if args.log else None,
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "acquire_host_pid_tree_note": "run 子命令会在派生子进程后更新 pid/pgid",
    }
    # O_EXCL 原子创建，防并发双取
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    with os.fdopen(fd, "w") as f:
        json.dump(lock, f, ensure_ascii=False, indent=2)
    _log_event({"action": "acquire", **lock})
    print(json.dumps(lock, ensure_ascii=False))
    return 0


def cmd_release(args):
    path = _lock_path(args.type)
    lock = _read_lock(args.type)
    if lock is None:
        print(f"NOTE: {args.type} 锁不存在，无需释放")
        return 0
    os.unlink(path)
    _log_event({"action": "release", "released_lock": lock,
                "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    print(f"RELEASED: {path}")
    return 0


def cmd_clear_stale(args):
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
    out = {"build_lock": _read_lock("build"), "experiment_lock": _read_lock("experiment"),
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
        if snap["swap_free_gib"] < TRIP_SWAP_GIB:
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
    # 1) 启动门禁
    gate = subprocess.run([sys.executable, __file__, "gate"], capture_output=True, text=True)
    if gate.returncode != 0:
        print("GATE BLOCKED:\n" + gate.stdout, file=sys.stderr)
        return 1
    # 2) 获取锁
    acq = subprocess.run([sys.executable, __file__, "acquire", "--type", args.type,
                          "--desc", args.desc, "--log", args.log] +
                         (["--item", args.item] if args.item else []) +
                         (["--runid", args.runid] if args.runid else []),
                         capture_output=True, text=True)
    if acq.returncode != 0:
        print("ACQUIRE REFUSED:\n" + acq.stderr, file=sys.stderr)
        return 2
    try:
        # 3) 新进程组派生命令
        proc = subprocess.Popen(args.command, start_new_session=True)
        pgid = os.getpgid(proc.pid)
        # 锁内更新真实 pid/pgid
        lock = _read_lock(args.type)
        lock["pid"], lock["pgid"], lock["cmd"] = proc.pid, pgid, args.command
        with open(_lock_path(args.type), "w") as f:
            json.dump(lock, f, ensure_ascii=False, indent=2)
        _log_event({"action": "spawn", "pid": proc.pid, "pgid": pgid, "cmd": args.cmd})
        print(f"SPAWNED pid={proc.pid} pgid={pgid} log={args.log}")
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
        rel = subprocess.run([sys.executable, __file__, "release", "--type", args.type],
                             capture_output=True, text=True)
        if rel.returncode != 0:
            print(f"WARNING: 锁释放异常: {rel.stderr}", file=sys.stderr)


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
