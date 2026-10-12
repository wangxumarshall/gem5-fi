#!/usr/bin/env python3
"""lsu_hostmon.py — LSU 60 秒主机资源采样器 + 槽位策略状态机（OBS 计划 T4）。

只读采样（不占实验槽、不 kill 任何进程、不写主锁目录），纯标准库直读 /proc：
  * 每拍一行 JSONL：<out>/hostmon_YYYYMMDD.jsonl
    {"t", "gem5_procs":[{"pid","rss_gib","cpu_pct","etime_s"}], "mem_available_gib",
     "swap_free_gib", "committed_as_gib", "si_ps", "so_ps", "load_1", "blocked_n",
     "gem5_n", "home_free_gib", "tmp_free_gib", "obs_growth_gib", "slots_held"}
    - si_ps/so_ps = /proc/vmstat pswpin/pswpout 每拍差分 ÷ 实际间隔秒（页/秒）；
      启动后首拍无基线 → null（诚实缺测，不写假 0；重启同理，原始计数器不在
      JSONL 里，无法跨重启差分）。
    - obs_growth_gib = /home free 相对窗口首拍的下降量（首拍 null）；重启后从
      JSONL 历史的首拍 home_free_gib 重新播种基线。
    - gem5_procs 扫 /proc（comm 含 gem5.opt）逐进程 {pid, rss_gib, cpu_pct,
      etime_s}；cpu_pct 需相邻两拍 utime+stime 差分，首见进程为 null。
    - slots_held = 锁目录（LSU_GUARD_DIR，默认主树 runs/lsu/guard——host-global，
      与 obs_driver 同款默认）内 experiment_slot_*.lock 中持有者存活
      （lsu_guard._lock_live：PID+pid_start 双核验）的数量；glob 覆盖 >3 的
      高位槽。不可读 → null。
  * 决策纯函数 decide_cap(history, current_cap)（用户指令 2026-10-12 三.2-3）：
      TRIP   : MemAvailable<8 连续 2 拍，或任一拍 <6，或任一拍 SwapFree<2
               → cap = max(4, cap-2)，state=TRIP_DOWN
      RAMP8  : cap==6 且最近连续 ≥30 拍 mem≥16、swap≥8、无连续 >5 拍
               (si_ps>0 或 so_ps>0)、blocked_n 全 0、/home 任意 10 拍（60s
               拍距=10 分钟）增量 <1GiB → cap=8
      RAMP6  : cap==4 且连续 ≥3 拍 slots_held<cap（持续闲置=driver 退出；
               换样间隙 <60s 单拍闪断不触发，OBS-4c 误触发修复）且最新拍
               mem≥12 → cap=6
      HOLD   : 其余 → HOLD{cap}；cap 恒 ∈ [4,8]（本阶段硬上限 8）
    评估窗口 = 传入 history 全体（时间升序 旧→新）：TRIP 扫全窗（保守，事件
    滚出窗口前持续压制）；RAMP8 只看尾部 30 拍；RAMP6 看尾部连续闲置拍数
    （从最新拍往回数，null 缺测断链；≥3 拍才升）。
  * 每拍后原子写 <out>/slot_policy.json（tmp+os.replace）：
    {"cap","state","reason","updated","evidence":{"window_ticks","mem_min_gib",
     "swap_min_gib","sustained_swap","blocked_events","home_delta_gib_10min"}}
    hostmon 启动时读它播种 current_cap（这是手动 seed 的合规接口：停 hostmon →
    改 cap/reason → 重启），并从最新 hostmon_*.jsonl 尾部续历史（30 分钟窗口
    跨重启不重置）。

用法：
  python3 tools/lsu_hostmon.py --interval 60 --out runs/lsu/obs/hostmon  # 常驻
  python3 tools/lsu_hostmon.py --interval 60 --out /tmp/hm --once        # 单拍
  python3 tools/lsu_hostmon.py --self-test                              # 决策用例
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

GIB = 1024 * 1024 * 1024.0
CAP_MIN, CAP_MAX = 4, 8
RAMP8_WINDOW_TICKS = 30
RAMP8_MEM_GIB = 16.0
RAMP8_SWAP_GIB = 8.0
RAMP8_SWAP_STREAK_MAX = 5      # 连续 >5 拍 (si_ps>0 或 so_ps>0) → 否决升 8
RAMP8_HOME_10MIN_GIB = 1.0     # 任意 10 分钟 /home 增量 ≥1GiB → 否决升 8
RAMP8_HOME_WINDOW_TICKS = 10   # 60s 拍距下 10 拍 = 10 分钟
RAMP6_MEM_GIB = 12.0
RAMP6_IDLE_STREAK = 3           # 连续 ≥3 拍 slots_held<cap 才升 6（单拍闪断=换样间隙）
TRIP_MEM_GIB = 8.0
TRIP_MEM_HARD_GIB = 6.0
TRIP_SWAP_GIB = 2.0
HISTORY_MAX = 60               # 常驻保留拍数（≥30 分钟判据窗口 + 余量）
MAIN_GUARD_DIR = "/home/sdc/gem5-fi-ding/runs/lsu/guard"  # host-global（obs_driver 同款默认）
CLK = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
PAGE = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096


# ---------------------------------------------------------------- /proc 读取

def _meminfo():
    out = {}
    with open("/proc/meminfo") as f:
        for line in f:
            k, _, v = line.partition(":")
            out[k.strip()] = int(v.split()[0]) * 1024  # kB -> B
    return out


def _vmstat_swap():
    """(pswpin, pswpout) 累计页数；不可读 → None。"""
    pswpin = pswpout = None
    try:
        with open("/proc/vmstat") as f:
            for line in f:
                if line.startswith("pswpin "):
                    pswpin = int(line.split()[1])
                elif line.startswith("pswpout "):
                    pswpout = int(line.split()[1])
    except (OSError, ValueError):
        return None
    return (pswpin, pswpout) if pswpin is not None and pswpout is not None else None


def _loadavg1():
    try:
        with open("/proc/loadavg") as f:
            return float(f.read().split()[0])
    except (OSError, ValueError):
        return None


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 决策纯函数

def _max_swap_streak(ticks):
    """连续 (si_ps>0 或 so_ps>0) 的最长拍数（null 视为无证据=断链）。"""
    best = run = 0
    for t in ticks:
        si, so = _f(t.get("si_ps")), _f(t.get("so_ps"))
        if (si is not None and si > 0) or (so is not None and so > 0):
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def _home_10min_max(ticks):
    """任意 10 拍窗口内 /home 消耗量最大值（GiB，正=占用增长）；不可评估→None。"""
    hf = [_f(t.get("home_free_gib")) for t in ticks]
    best = None
    for i in range(len(hf) - RAMP8_HOME_WINDOW_TICKS):
        a, b = hf[i], hf[i + RAMP8_HOME_WINDOW_TICKS]
        if a is None or b is None:
            continue
        d = a - b
        if best is None or d > best:
            best = d
    return best


def _trailing_idle_streak(history, cap):
    """从最新拍往回数连续 slots_held<cap 的拍数（OBS-4c）。

    null（缺测）或 ≥cap（占用）即断链：换样间隙的单拍闪断最多数到 1，
    真 driver 退出的持续闲置才会累积 ≥3。"""
    n = 0
    for t in reversed(history):
        sh = _f(t.get("slots_held"))
        if sh is None or sh >= cap:
            break
        n += 1
    return n


def _trip_reason(mems, swaps):
    for i in range(len(mems) - 1):
        if (mems[i] is not None and mems[i] < TRIP_MEM_GIB
                and mems[i + 1] is not None and mems[i + 1] < TRIP_MEM_GIB):
            return (f"MemAvailable<8GiB 连续 2 拍（拍 {i}/{i+1}: "
                    f"{mems[i]:g}/{mems[i+1]:g} GiB）")
    hard = [m for m in mems if m is not None and m < TRIP_MEM_HARD_GIB]
    if hard:
        return f"任一拍 MemAvailable<6GiB（min={min(hard):g} GiB）"
    low = [s for s in swaps if s is not None and s < TRIP_SWAP_GIB]
    if low:
        return f"任一拍 SwapFree<2GiB（min={min(low):g} GiB）"
    return None


def _ramp8_blockers(history):
    """升 8 的否决理由列表（空列表 = 可升）。窗口 = history 全体（调用方已保证
    ≥30 拍时才可能为空）。"""
    if len(history) < RAMP8_WINDOW_TICKS:
        return [f"窗口不足（{len(history)}<{RAMP8_WINDOW_TICKS} 拍）"]
    tail = history[-RAMP8_WINDOW_TICKS:]
    mems = [_f(t.get("mem_available_gib")) for t in tail]
    swaps = [_f(t.get("swap_free_gib")) for t in tail]
    blockers = []
    lo_m = [m for m in mems if m is not None]
    if len(lo_m) < len(mems):
        blockers.append("mem 缺测")
    elif min(lo_m) < RAMP8_MEM_GIB:
        blockers.append(f"mem 最低 {min(lo_m):g}<{RAMP8_MEM_GIB:g} GiB")
    lo_s = [s for s in swaps if s is not None]
    if len(lo_s) < len(swaps):
        blockers.append("swap 缺测")
    elif min(lo_s) < RAMP8_SWAP_GIB:
        blockers.append(f"swap 最低 {min(lo_s):g}<{RAMP8_SWAP_GIB:g} GiB")
    streak = _max_swap_streak(tail)
    if streak > RAMP8_SWAP_STREAK_MAX:
        blockers.append(f"si/so>0 连续 {streak} 拍（>{RAMP8_SWAP_STREAK_MAX}）")
    if any((_f(t.get("blocked_n")) or 0) > 0 for t in tail):
        blockers.append("存在 blocked（D 态）进程拍")
    hd = _home_10min_max(tail)
    if hd is None:
        blockers.append("home 10 分钟增量不可评估")
    elif hd >= RAMP8_HOME_10MIN_GIB:
        blockers.append(f"home 10 分钟增量 {hd:.2f}≥{RAMP8_HOME_10MIN_GIB:g} GiB")
    return blockers


def decide_cap(history, current_cap):
    """槽位策略决策（纯函数，单测/self-test 覆盖）。

    history：时间升序（旧→新）的拍 dict 列表；current_cap：当前槽上限。
    返回 (new_cap:int, state:str, reason:str)；cap 恒 ∈ [4,8]。
    """
    cap = min(CAP_MAX, max(CAP_MIN, int(current_cap)))
    h = [t for t in (history or []) if isinstance(t, dict)]
    mems = [_f(t.get("mem_available_gib")) for t in h]
    swaps = [_f(t.get("swap_free_gib")) for t in h]

    # ---- TRIP（最高优先级；扫描整个传入窗口，保守） ----
    trip = _trip_reason(mems, swaps)
    if trip:
        return max(CAP_MIN, cap - 2), "TRIP_DOWN", "TRIP: " + trip

    # ---- RAMP8（cap==6；尾部 30 拍全绿才升） ----
    if cap == 6:
        blockers = _ramp8_blockers(h)
        if not blockers:
            return 8, "RAMP8", (f"cap6→8：连续 {RAMP8_WINDOW_TICKS} 拍 "
                                f"mem≥{RAMP8_MEM_GIB:g}/swap≥{RAMP8_SWAP_GIB:g} GiB、"
                                f"无持续 si/so、blocked 全 0、home 10 分钟增量"
                                f"<{RAMP8_HOME_10MIN_GIB:g} GiB")
        return cap, "HOLD6", "RAMP8 否决：" + "；".join(blockers)

    # ---- RAMP6（cap==4；连续 ≥3 拍槽闲置且最新拍 mem≥12，OBS-4c 收紧） ----
    if cap == 4 and h:
        last = h[-1]
        sh, m = _f(last.get("slots_held")), _f(last.get("mem_available_gib"))
        streak = _trailing_idle_streak(h, cap)
        if streak >= RAMP6_IDLE_STREAK and m is not None and m >= RAMP6_MEM_GIB:
            return 6, "RAMP6", (f"cap4→6：连续 {streak} 拍 slots_held<cap={cap}"
                                f"（≥{RAMP6_IDLE_STREAK}，持续闲置=driver 退出）"
                                f"且 mem={m:g}≥{RAMP6_MEM_GIB:g} GiB")
        why = []
        if sh is None:
            why.append("slots_held 缺测")
        elif streak == 0:
            why.append(f"槽全忙（最新拍 slots_held={int(sh)}≥cap={cap}，无 driver 退出证据）")
        else:
            why.append(f"槽闲置不连续（尾部仅 {streak}<{RAMP6_IDLE_STREAK} 拍，"
                       f"疑似换样间隙闪断，不升）")
        if m is None:
            why.append("mem 缺测")
        elif m < RAMP6_MEM_GIB:
            why.append(f"mem={m:g}<{RAMP6_MEM_GIB:g} GiB")
        return cap, "HOLD4", "RAMP6 否决：" + "；".join(why)
    if cap == 4:
        return cap, "HOLD4", "RAMP6 否决：窗口无拍"

    # ---- HOLD ----
    if cap == CAP_MAX:
        return cap, "HOLD8", "已在上限 8（本阶段硬上限，用户指令 2026-10-12 三.3）"
    return cap, f"HOLD{cap}", "保持（非 4/6/8 的钳制值）"


def evidence(history):
    """slot_policy.json 的 evidence 字段（窗口统计，供审计）。"""
    h = [t for t in (history or []) if isinstance(t, dict)]
    mems = [m for m in (_f(t.get("mem_available_gib")) for t in h)
            if m is not None]
    swaps = [s for s in (_f(t.get("swap_free_gib")) for t in h)
             if s is not None]
    hd = _home_10min_max(h)
    return {
        "window_ticks": len(h),
        "mem_min_gib": round(min(mems), 2) if mems else None,
        "swap_min_gib": round(min(swaps), 2) if swaps else None,
        "sustained_swap": _max_swap_streak(h) > RAMP8_SWAP_STREAK_MAX,
        "blocked_events": sum(1 for t in h if (_f(t.get("blocked_n")) or 0) > 0),
        "home_delta_gib_10min": round(hd, 3) if hd is not None else None,
    }


# ---------------------------------------------------------------- 采样器

class Sampler:
    def __init__(self, out_dir, interval):
        self.out = Path(out_dir)
        self.interval = interval
        self.prev_swap = None    # (pswpin, pswpout, t)
        self.prev_cpu = {}       # pid -> (utime+stime, t)
        self.home_free0 = None
        self.history = []
        self.cap = CAP_MIN
        self.guard = self._load_guard()

    # ---- lsu_guard（env LSU_GUARD_DIR 必须先于 import 设定：模块常量读 env） ----
    @staticmethod
    def _load_guard():
        gd = os.environ.get("LSU_GUARD_DIR") or MAIN_GUARD_DIR
        os.environ["LSU_GUARD_DIR"] = gd
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        try:
            import lsu_guard
            return lsu_guard
        except Exception as exc:  # 导入失败不致命：slots_held 缺测 null
            print(f"WARNING: lsu_guard 导入失败（slots_held 将为 null）: {exc}",
                  file=sys.stderr, flush=True)
            return None

    def slots_held(self):
        G = self.guard
        if G is None:
            return None
        try:
            locks = G._all_slot_locks_on_disk()
        except Exception:
            return None
        n = 0
        for lock in locks.values():
            if not lock or lock.get("corrupt"):
                continue
            try:
                if G._lock_live(lock):
                    n += 1
            except Exception:
                continue
        return n

    # ---- /proc 扫描 ----
    def _scan_procs(self, now):
        try:
            with open("/proc/uptime") as f:
                uptime = float(f.read().split()[0])
        except (OSError, ValueError):
            uptime = None
        gem5, blocked, cur = [], 0, {}
        for pid in os.listdir("/proc"):
            if not pid.isdigit():
                continue
            try:
                with open(f"/proc/{pid}/stat") as f:
                    data = f.read()
            except OSError:
                continue
            rp = data.rpartition(")")
            if not rp[1]:
                continue
            comm = rp[0].partition("(")[2]
            tail = rp[2].split()
            try:
                state = tail[0]
                utime, stime = int(tail[11]), int(tail[12])   # 字段14/15
                starttime = int(tail[19])                     # 字段22
                rss_pages = int(tail[21])                     # 字段24
            except (IndexError, ValueError):
                continue
            if state == "D":
                blocked += 1
            # Z（僵尸）= 已退出待收割，不占资源（实测 PILOT 换样间隙全是 Z 态
            # gem5，rss=0）；排除之，gem5_n 才可与 slots_held 对账
            if state == "Z" or "gem5.opt" not in comm:
                continue
            cpu_total = utime + stime
            prev = self.prev_cpu.get(int(pid))
            cpu_pct = None
            if prev is not None:
                dt = max(now - prev[1], 1e-6)
                cpu_pct = round(100.0 * (cpu_total - prev[0]) / (CLK * dt), 1)
            cur[int(pid)] = (cpu_total, now)
            etime = (round(uptime - starttime / CLK, 1)
                     if uptime is not None else None)
            gem5.append({"pid": int(pid),
                         "rss_gib": round(rss_pages * PAGE / GIB, 2),
                         "cpu_pct": cpu_pct,
                         "etime_s": etime})
        gem5.sort(key=lambda d: d["pid"])
        return gem5, blocked, cur

    def collect(self):
        now = time.time()
        mi = _meminfo()
        sw = _vmstat_swap()
        si = so = None
        if self.prev_swap is not None and sw is not None:
            dt = max(now - self.prev_swap[2], 1e-6)
            si = round((sw[0] - self.prev_swap[0]) / dt, 3)
            so = round((sw[1] - self.prev_swap[1]) / dt, 3)
        if sw is not None:
            self.prev_swap = (sw[0], sw[1], now)
        gem5_procs, blocked_n, cur_cpu = self._scan_procs(now)
        self.prev_cpu = cur_cpu
        home_free = shutil.disk_usage("/home").free / GIB
        tmp_free = shutil.disk_usage("/tmp").free / GIB
        if self.home_free0 is None:
            obs_growth = None
            self.home_free0 = home_free
        else:
            obs_growth = round(self.home_free0 - home_free, 3)
        return {
            "t": time.strftime("%Y-%m-%d %H:%M:%S"),
            "gem5_procs": gem5_procs,
            "mem_available_gib": round(mi.get("MemAvailable", 0) / GIB, 2),
            "swap_free_gib": round(mi.get("SwapFree", 0) / GIB, 2),
            "committed_as_gib": round(mi.get("Committed_AS", 0) / GIB, 2),
            "si_ps": si,
            "so_ps": so,
            "load_1": _loadavg1(),
            "blocked_n": blocked_n,
            "gem5_n": len(gem5_procs),
            "home_free_gib": round(home_free, 2),
            "tmp_free_gib": round(tmp_free, 2),
            "obs_growth_gib": obs_growth,
            "slots_held": self.slots_held(),
        }

    # ---- 落盘 ----
    def append_tick(self, tick):
        path = self.out / f"hostmon_{time.strftime('%Y%m%d')}.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps(tick, ensure_ascii=False) + "\n")

    def write_policy(self, cap, state, reason):
        pol = {"cap": cap, "state": state, "reason": reason,
               "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
               "evidence": evidence(self.history)}
        tmp = self.out / f".slot_policy.json.tmp.{os.getpid()}"
        with open(tmp, "w") as f:
            json.dump(pol, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.out / "slot_policy.json")
        return pol

    # ---- 启动播种（手动 seed 合规接口 + 历史跨重启续窗） ----
    def seed_from_out(self):
        pol = self.out / "slot_policy.json"
        if pol.exists():
            try:
                c = json.loads(pol.read_text()).get("cap")
                if isinstance(c, int) and CAP_MIN <= c <= CAP_MAX:
                    self.cap = c
            except (json.JSONDecodeError, OSError, ValueError):
                pass
        files = sorted(self.out.glob("hostmon_*.jsonl"))
        lines = []
        if files:
            try:
                raw = files[-1].read_text(errors="replace").splitlines()
            except OSError:
                raw = []
            for ln in raw:
                try:
                    d = json.loads(ln)
                except json.JSONDecodeError:
                    continue
                if isinstance(d, dict) and "mem_available_gib" in d:
                    lines.append(d)
        self.history = lines[-HISTORY_MAX:]
        if self.history:
            hf = _f(self.history[0].get("home_free_gib"))
            if hf is not None:
                self.home_free0 = hf

    def run(self, once=False):
        self.out.mkdir(parents=True, exist_ok=True)
        self.seed_from_out()
        while True:
            t0 = time.time()
            tick = self.collect()
            self.history.append(tick)
            if len(self.history) > HISTORY_MAX:
                self.history = self.history[-HISTORY_MAX:]
            cap, state, reason = decide_cap(self.history, self.cap)
            self.cap = cap
            self.append_tick(tick)
            self.write_policy(cap, state, reason)
            print(f"[{tick['t']}] mem={tick['mem_available_gib']} "
                  f"swap={tick['swap_free_gib']} si_ps={tick['si_ps']} "
                  f"so_ps={tick['so_ps']} gem5_n={tick['gem5_n']} "
                  f"blocked_n={tick['blocked_n']} "
                  f"slots_held={tick['slots_held']} "
                  f"home_free={tick['home_free_gib']} → cap={cap} {state}",
                  flush=True)
            if once:
                return 0
            time.sleep(max(0.0, self.interval - (time.time() - t0)))


# ---------------------------------------------------------------- self-test

def _mk(mem=20.0, swap=10.0, si=0.0, so=0.0, blocked=0, slots=4, home=150.0):
    return {"mem_available_gib": mem, "swap_free_gib": swap, "si_ps": si,
            "so_ps": so, "blocked_n": blocked, "slots_held": slots,
            "home_free_gib": home}


def _self_test_cases():
    """(名称, current_cap, history, 期望 (new_cap, state))。"""
    ok30 = [_mk() for _ in range(30)]
    return [
        ("ramp8_pass", 6, ok30, (8, "RAMP8")),
        ("ramp8_window_short", 6, ok30[:-1], (6, "HOLD6")),
        ("ramp8_swap_streak_veto", 6,
         [_mk() for _ in range(12)] + [_mk(si=1.0) for _ in range(6)]
         + [_mk() for _ in range(12)], (6, "HOLD6")),
        ("ramp8_blocked_veto", 6,
         [_mk() for _ in range(29)] + [_mk(blocked=2)], (6, "HOLD6")),
        ("ramp8_home_growth_veto", 6,
         [_mk(home=150.0 - 0.2 * i) for i in range(30)], (6, "HOLD6")),
        ("trip_mem2", 6,
         [_mk() for _ in range(28)] + [_mk(mem=7.9), _mk(mem=7.9)],
         (4, "TRIP_DOWN")),
        ("trip_hard", 6,
         [_mk() for _ in range(29)] + [_mk(mem=5.9)], (4, "TRIP_DOWN")),
        ("trip_swap", 6,
         [_mk() for _ in range(29)] + [_mk(swap=1.9)], (4, "TRIP_DOWN")),
        ("trip_floor_4", 4, [_mk(mem=7.9), _mk(mem=7.9)], (4, "TRIP_DOWN")),
        ("never_above_8", 8, ok30, (8, "HOLD8")),
        ("ramp6_sustained_3ticks", 4, [_mk(slots=3) for _ in range(3)],
         (6, "RAMP6")),
        ("ramp6_transient_dip", 4, [_mk(slots=4), _mk(slots=3)], (4, "HOLD4")),
        ("ramp6_dip_recovered", 4,
         [_mk(slots=4), _mk(slots=3), _mk(slots=4)], (4, "HOLD4")),
        ("ramp6_two_idle_not_enough", 4,
         [_mk(slots=4), _mk(slots=3), _mk(slots=3)], (4, "HOLD4")),
        ("ramp6_no_idle_slot", 4, [_mk(slots=4)], (4, "HOLD4")),
        ("trip_priority_over_ramp6", 4, [_mk(swap=1.9, slots=3)],
         (4, "TRIP_DOWN")),
        ("cap_clamp_high", 99, ok30, (8, "HOLD8")),
        ("cap_clamp_low", 1, [_mk()], (4, "HOLD4")),
    ]


def self_test():
    fails = []
    for name, cap, hist, want in _self_test_cases():
        got = decide_cap(hist, cap)
        ok = (got[0], got[1]) == want
        print(("PASS" if ok else "FAIL"), name, "->",
              (got[0], got[1]), "" if ok else f"(期望 {want}; reason={got[2]})")
        if not ok:
            fails.append(name)
    print(f"\nSELF-TEST: {'ALL PASS' if not fails else 'FAILURES: ' + str(fails)}")
    return 0 if not fails else 1


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--interval", type=int, default=60,
                    help="采样间隔秒（默认 60）")
    ap.add_argument("--out", default=None, help="输出目录（JSONL + slot_policy.json）")
    ap.add_argument("--once", action="store_true", help="只采一拍即退出")
    ap.add_argument("--self-test", dest="self_test", action="store_true",
                    help="跑 decide_cap 内置用例后退出")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("需要 --out DIR（或 --self-test）")
    if args.interval < 1:
        ap.error("--interval 须 ≥1 秒")
    return Sampler(args.out, args.interval).run(once=args.once)


if __name__ == "__main__":
    sys.exit(main())
