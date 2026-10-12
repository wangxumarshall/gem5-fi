#!/usr/bin/env python3
"""test_lsu_hostmon.py — hostmon 决策纯函数 + 单拍实跑测试（stdlib 自断言）。

覆盖（OBS 计划 T4 / 用户指令 2026-10-12 三.2-3）：
  1  decide_cap 五条必测路径：升 8 通过 / 窗口不足否决 / TRIP 降档 /
     降档下限 4 / 永不超过 8
  2  附加路径（独立构造，不复用 lsu_hostmon._self_test_cases，防同源假通过）：
     RAMP6（连续 ≥3 拍槽闲置+mem≥12，OBS-4c 收紧：单拍闪断=换样间隙不触发）/
     槽全忙否决 / TRIP 优先级高于 RAMP6 /
     si-so 连续>5 拍否决 / home 10 分钟增量否决 / blocked 否决 / cap 钳制
  3  真跑一次 --once --out <tmp>（隔离 LSU_GUARD_DIR：伪造 4 个活锁在高位槽
     4..7 + 1 个死锁在槽 0）→ JSONL 首拍字段齐全、差分字段首拍 null（诚实
     缺测）、slots_held=4（glob 覆盖 >3 高位槽 + _lock_live 过滤死锁）、
     slot_policy.json 产出且 evidence 字段齐全
  4  --self-test 子进程退出码 0

用法：python3 tests/test_lsu_hostmon.py   （退出码 0=全 PASS）
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parent / "tools"
sys.path.insert(0, str(TOOLS))
import lsu_hostmon as HM  # noqa: E402

REQUIRED_KEYS = {"t", "gem5_procs", "mem_available_gib", "swap_free_gib",
                 "committed_as_gib", "si_ps", "so_ps", "load_1", "blocked_n",
                 "gem5_n", "home_free_gib", "tmp_free_gib", "obs_growth_gib",
                 "slots_held"}
PROC_KEYS = {"pid", "rss_gib", "cpu_pct", "etime_s"}


def mk(**kw):
    d = {"mem_available_gib": 20.0, "swap_free_gib": 10.0, "si_ps": 0.0,
         "so_ps": 0.0, "blocked_n": 0, "slots_held": 4, "home_free_gib": 150.0}
    d.update(kw)
    return d


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name,
               "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    good = [mk() for _ in range(30)]

    # ---- 1) 五条必测路径 ----
    got = HM.decide_cap(good, 6)
    check("decide_ramp8_pass", (got[0], got[1]) == (8, "RAMP8"), f"got={got}")
    got = HM.decide_cap(good[:-1], 6)
    check("decide_ramp8_window_short",
          (got[0], got[1]) == (6, "HOLD6"), f"got={got}")
    got = HM.decide_cap(good[:-2] + [mk(mem_available_gib=7.5),
                                     mk(mem_available_gib=7.5)], 6)
    check("decide_trip_down_mem2",
          (got[0], got[1]) == (4, "TRIP_DOWN"), f"got={got}")
    got = HM.decide_cap([mk(mem_available_gib=5.5)], 4)
    check("decide_trip_floor_4",
          (got[0], got[1]) == (4, "TRIP_DOWN"), f"got={got}")
    got = HM.decide_cap(good, 8)
    check("decide_never_above_8",
          (got[0], got[1]) == (8, "HOLD8"), f"got={got}")

    # ---- 2) 附加路径（独立构造） ----
    # RAMP6（OBS-4c 收紧：连续 ≥3 拍 slots_held<cap 才升；生产换样间隙 <60s
    # 单拍闪断不允许触发——2026-10-12 17:35:29 实测误触发 cap4→6 的回归防御）
    got = HM.decide_cap([mk(slots_held=4), mk(slots_held=3)], 4)
    check("decide_ramp6_transient_dip_no_trigger",
          (got[0], got[1]) == (4, "HOLD4"), f"got={got}")
    got = HM.decide_cap([mk(slots_held=4), mk(slots_held=3), mk(slots_held=4)], 4)
    check("decide_ramp6_dip_recovered_no_trigger",
          (got[0], got[1]) == (4, "HOLD4"), f"got={got}")
    got = HM.decide_cap([mk(slots_held=3) for _ in range(15)], 4)
    check("decide_ramp6_sustained_15ticks_trigger",
          (got[0], got[1]) == (6, "RAMP6"), f"got={got}")
    # OBS-4e（2026-10-13 05:56-05:58 实测）：存活 driver 的换样/item 边界
    # 间隙可被 60s 采样连拍 3-5 拍 slots_held=3——不得升档（真退出=永久闲置，
    # 15 拍连续才可信）
    got = HM.decide_cap([mk(slots_held=3) for _ in range(5)], 4)
    check("decide_ramp6_item_gap_5ticks_no_trigger",
          (got[0], got[1]) == (4, "HOLD4"), f"got={got}")
    got = HM.decide_cap([mk(slots_held=4), mk(slots_held=3), mk(slots_held=3)], 4)
    check("decide_ramp6_two_idle_ticks_not_enough",
          (got[0], got[1]) == (4, "HOLD4"), f"got={got}")
    got = HM.decide_cap([mk(slots_held=4)], 4)
    check("decide_ramp6_no_idle_slot",
          (got[0], got[1]) == (4, "HOLD4"), f"got={got}")
    got = HM.decide_cap([mk(swap_free_gib=1.5, slots_held=3)], 4)
    check("decide_trip_priority_over_ramp6",
          (got[0], got[1]) == (4, "TRIP_DOWN"), f"got={got}")
    # OBS-4d（2026-10-12 空载空真实证）：全机空闲（slots_held=0）连续多拍
    # 不得升档——"释放槽"语义要求有在跑工作（1≤slots_held<cap）
    got = HM.decide_cap([mk(slots_held=0) for _ in range(30)], 4)
    check("decide_ramp6_idle_host_no_trigger",
          (got[0], got[1]) == (4, "HOLD4") and "空载" in got[2], f"got={got}")
    streak = [mk() for _ in range(12)] + [mk(si_ps=2.0) for _ in range(6)] \
        + [mk() for _ in range(12)]
    got = HM.decide_cap(streak, 6)
    check("decide_ramp8_swap_streak_veto",
          (got[0], got[1]) == (6, "HOLD6"), f"got={got}")
    grow = [mk(home_free_gib=150.0 - 0.2 * i) for i in range(30)]
    got = HM.decide_cap(grow, 6)
    check("decide_ramp8_home_growth_veto",
          (got[0], got[1]) == (6, "HOLD6"), f"got={got}")
    got = HM.decide_cap(good[:-1] + [mk(blocked_n=3)], 6)
    check("decide_ramp8_blocked_veto",
          (got[0], got[1]) == (6, "HOLD6"), f"got={got}")
    got = HM.decide_cap(good, 99)
    check("decide_cap_clamp_high",
          (got[0], got[1]) == (8, "HOLD8"), f"got={got}")
    got = HM.decide_cap([mk()], 1)
    check("decide_cap_clamp_low",
          (got[0], got[1]) == (4, "HOLD4"), f"got={got}")

    # ---- 3) 真跑 --once（隔离 LSU_GUARD_DIR；槽 4..7 伪造活锁、槽 0 死锁） ----
    tmp = tempfile.mkdtemp(prefix="hostmon_once_")
    gdir = tempfile.mkdtemp(prefix="hostmon_guard_")
    try:
        os.environ["LSU_GUARD_DIR"] = gdir  # 先于 import lsu_guard（模块常量读 env）
        import lsu_guard as G
        my_start = G._pid_start_ticks(os.getpid())
        for slot in (4, 5, 6, 7):   # 全部 > 默认 4 槽范围：glob 覆盖高位槽的证据
            Path(gdir, f"experiment_slot_{slot}.lock").write_text(json.dumps({
                "owner": "test", "pid": os.getpid(), "pgid": os.getpgid(0),
                "pid_start": my_start, "task_type": "experiment",
                "desc": f"live-high-slot-{slot}",
                "started": "2026-10-12 00:00:00", "slot": slot}))
        Path(gdir, "experiment_slot_0.lock").write_text(json.dumps({
            "owner": "test", "pid": 999999, "pgid": 999999, "pid_start": 1,
            "task_type": "experiment", "desc": "dead-holder",
            "started": "2026-10-12 00:00:00", "slot": 0}))

        r = subprocess.run(
            [sys.executable, str(TOOLS / "lsu_hostmon.py"),
             "--interval", "60", "--out", tmp, "--once"],
            capture_output=True, text=True,
            env={**os.environ, "LSU_GUARD_DIR": gdir}, timeout=180)
        check("once_rc0", r.returncode == 0,
              f"rc={r.returncode} err={r.stderr[-500:]!r}")
        jl = sorted(Path(tmp).glob("hostmon_*.jsonl"))
        check("once_jsonl_created", len(jl) == 1, str(jl))
        lines = jl[0].read_text().strip().splitlines()
        check("once_single_tick", len(lines) == 1, f"{len(lines)} 行")
        tick = json.loads(lines[0])
        check("once_required_keys", REQUIRED_KEYS <= set(tick),
              f"缺 {sorted(REQUIRED_KEYS - set(tick))}")
        check("once_first_tick_diff_null",
              tick["si_ps"] is None and tick["so_ps"] is None
              and tick["obs_growth_gib"] is None,
              json.dumps({k: tick.get(k)
                          for k in ("si_ps", "so_ps", "obs_growth_gib")}))
        check("once_mem_positive",
              isinstance(tick["mem_available_gib"], (int, float))
              and tick["mem_available_gib"] > 0,
              str(tick.get("mem_available_gib")))
        check("once_slots_held_4_high_slots",
              tick["slots_held"] == 4,
              f"slots_held={tick['slots_held']}（期望 4：槽 4..7 活 + 槽 0 死）")
        check("once_gem5_procs_schema",
              isinstance(tick["gem5_procs"], list)
              and all(set(p) == PROC_KEYS for p in tick["gem5_procs"]),
              json.dumps(tick["gem5_procs"])[:200])
        check("once_gem5_n_consistent",
              tick["gem5_n"] == len(tick["gem5_procs"]),
              f"gem5_n={tick['gem5_n']} vs {len(tick['gem5_procs'])}")
        pol_p = Path(tmp, "slot_policy.json")
        check("once_policy_exists", pol_p.exists())
        pol = json.loads(pol_p.read_text())
        check("once_policy_fields",
              {"cap", "state", "reason", "updated", "evidence"} <= set(pol)
              and {"window_ticks", "mem_min_gib", "swap_min_gib",
                   "sustained_swap", "blocked_events",
                   "home_delta_gib_10min"} <= set(pol.get("evidence", {})),
              json.dumps(pol)[:400])
        check("once_policy_hold4",
              pol["cap"] == 4 and pol["state"] == "HOLD4",
              f"cap={pol['cap']} state={pol['state']} reason={pol['reason']!r}"
              f"（若 TRIP_DOWN：主机当前 mem/swap 已触红线，非测试缺陷）")
        leftovers = [p.name for p in Path(tmp).iterdir()
                     if ".tmp." in p.name]
        check("once_no_tmp_leftover", not leftovers, str(leftovers))

        # 真实首拍内容摘录（提交信息/报告引用用）
        print("\n--once 首拍 JSONL（真实输出）--")
        print(lines[0][:600])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(gdir, ignore_errors=True)

    # ---- 4) --self-test 子进程 ----
    r2 = subprocess.run([sys.executable, str(TOOLS / "lsu_hostmon.py"),
                         "--self-test"], capture_output=True, text=True,
                        timeout=60)
    check("selftest_rc0", r2.returncode == 0,
          f"rc={r2.returncode} out_tail={r2.stdout[-300:]!r}")
    check("selftest_all_pass", "SELF-TEST: ALL PASS" in r2.stdout,
          r2.stdout[-300:])

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
