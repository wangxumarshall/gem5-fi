#!/usr/bin/env python3
"""test_lsu_obs_driver_workers.py — OBS-8a 单测：样本级并行/slot_policy/acquire 重试。

绝不启动 gem5：fault run 用 monkeypatch 假 run_fault（合成最小产物走真
post_process / finalize / claim 全流程）；guard 集成用 /bin/true 与 sleep
假命令 + 隔离 LSU_GUARD_DIR（真 guard 子进程，非 gem5；绝不动主树
runs/lsu/guard）。覆盖：
  (a) --workers 2 并行派发唯一性：每样本恰好 finalize 一次、真 claim 无冲突、
      两个 worker 线程都被使用
  (b) GuardFailure 停止派发：第 2 个派发样本抛 GuardFailure → 后续样本不再
      派发（s2+ 无目录），在飞 s0 自然完成
  (c) slot_policy 解析：{cap:6}→6 / 缺失→4 / cap=99→8 / 损坏→4 / 非 int→4 /
      cap=0→clamp 1 / 无 cap 键→4；--slots 优先；_guard_run 子进程 env 显式
      含 LSU_GUARD_SLOTS=6 且不写 os.environ（subprocess spy + 假 guard）
  (d) acquire 重试：假 guard 分支逻辑（槽满/STOP_DISPATCH 拒绝→重试成功；
      重试耗尽→GuardFailure；陈旧/损坏→立即 GuardFailure 不重试；无
      run-finish→F-023 周期未完成）+ 真 guard 1 槽 2 并发（其一重试后成功，
      gate 事件数 ≥3 证明确实发生了重试）
  (e) --workers 3 拒绝（argparse choices 1..2）
  (f) --workers 2 --dry-run 零副作用（不 claim、不建目录）
"""
import argparse
import gzip
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import contextlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parent
DRIVER = WT / "tools" / "lsu_obs_driver.py"
GUARD = WT / "tools" / "lsu_guard.py"
MT = Path("/home/sdc/gem5-fi-ding")

FUNNEL = "CHAOS_LSU_TRIGGER: cycle=123 attempted=1 eligible=1 injected=1"
INJLINE = ("Tick: 887040, Site: lsq_sendFragmentToTranslation, mode=low_bit_flip, "
           "old_vaddr=0x7ffffefd00, new_vaddr=0x87ffffefd00, faults_injected: 1")

# 真 guard 集成（(d) 并发）的 GUARD_DIR 必须在 /home：/tmp 是 tmpfs（15G 总量
# 12G 空闲），guard 磁盘红线 free < max(50GiB, 20%×total) 恒触发 → gate 恒
# BLOCKED。worktree 本身在 /home 分区，用后即删。
REAL_TMP_DIRS = []


def make_ns(**over):
    ns = dict(campaign="wk", obs_mode="l0l5", trace_budget_gib=40.0,
              outdir_root="/tmp/obs_wk_unused", guard_dir=None, gem5_bin=None,
              slots=None, dry_run=False, phase="screening",
              items=["ITEM-002"], samples=None, target=30, cap=300,
              replay_policy="none", workers=1, acquire_retries=None,
              acquire_retry_sleep=None)
    ns.update(over)
    return argparse.Namespace(**ns)


def seed_golden(drv, m):
    """预置 no-fault golden COMPLETE 目录 → ensure_golden 走真缓存复用路径
    （verify_complete 全通过），不起 guard/gem5。"""
    import lsu_obs_core as OC
    ident = drv.baseline_ident(m)
    key = OC.baseline_key(ident)
    gdir = drv.golden_root / key
    gdir.mkdir(parents=True, exist_ok=True)
    (gdir / "commit_trace.csv.gz").write_bytes(
        gzip.compress(b"tick,seq,physreg,value\n"))
    obs = {"schema": OC.SCHEMA,
           "identity": {"gem5_opt_sha256": ident["gem5_opt_sha256"],
                        "baseline_key": key},
           "files": [{"name": "commit_trace.csv.gz",
                      "path": "commit_trace.csv.gz",
                      "sha256": OC.sha256_file(gdir / "commit_trace.csv.gz"),
                      "bytes": (gdir / "commit_trace.csv.gz").stat().st_size}],
           "violations": [], "degradations": []}
    (gdir / "observation.json").write_text(json.dumps(obs, ensure_ascii=False))
    (gdir / OC.COMPLETE).write_text(
        json.dumps({"finalized_at": "seeded", "schema": OC.SCHEMA}))
    return key, gdir


def install_fake_run_fault(state, delay=0.25, fail_at=None):
    """monkeypatch ObsDriver.run_fault：合成最小 L0/L5 产物到 staging。
    fail_at 指定样本号立即抛 GuardFailure（不落产物）。"""
    import lsu_unit_pilot as UP

    def fake(self, m, s, staging, mode, slots=None):
        state["calls"][s] = state["calls"].get(s, 0) + 1
        state["threads"].add(threading.current_thread().name)
        if fail_at is not None and s == fail_at:
            raise UP.GuardFailure(f"fake guard infra failure at s{s}")
        time.sleep(delay)
        v = {"outcome": "Masked", "crash_kind": None, "activated": 1,
             "error": None, "source": "fake_unit_test"}
        (staging / "gem5.out").write_text(FUNNEL + "\n")
        (staging / "addrpath_injections.log").write_text(INJLINE + "\n")
        (staging / "l5_verdict.json").write_text(
            json.dumps(v, ensure_ascii=False))
        return v, ["fake-cmd"]
    import lsu_obs_driver as OD
    orig = OD.ObsDriver.run_fault
    OD.ObsDriver.run_fault = fake
    return OD, orig


def fake_guard_script(tmp, name, stateful):
    """假 guard：无状态版直接打 run-finish；有状态版按 behavior 文件逐次
    拒绝（full/stale/stop/corrupt）或成功（ok）。"""
    fg = tmp / name
    if stateful:
        fg.write_text(
            "import json, os, sys\n"
            "here = os.path.dirname(os.path.abspath(__file__))\n"
            "cnt = os.path.join(here, 'cnt')\n"
            "n = 0\n"
            "if os.path.exists(cnt):\n"
            "    n = int(open(cnt).read().strip() or '0')\n"
            "open(cnt, 'w').write(str(n + 1))\n"
            "spec = open(os.path.join(here, 'behavior')).read().strip().split(',')\n"
            "mode = spec[n] if n < len(spec) else spec[-1]\n"
            "refuse = {\n"
            "  'full': 'REFUSED: experiment 锁全部被占（experiment 上限 4 槽）：\\n"
            "  slot 3: pid=1 (other)',\n"
            "  'stale': 'REFUSED: experiment slot 3 陈旧锁（pid=99999 已退出或 "
            "pid_start 不符但未记录处置）；先 clear-stale 显式处置',\n"
            "  'stop': 'REFUSED: STOP_DISPATCH MemAvailable 5.0 GiB < 10.0 GiB"
            "（停止加任务；已持锁运行不受影响）',\n"
            "  'corrupt': 'REFUSED: 锁文件损坏 /x/experiment_slot_2.lock，"
            "用 clear-stale 处置',\n"
            "}\n"
            "if mode in refuse:\n"
            "    print('ACQUIRE REFUSED:\\n' + refuse[mode], file=sys.stderr)\n"
            "    sys.exit(2)\n"
            "if mode == 'silent':\n"
            "    print('SPAWNED pid=1 pgid=1')\n"
            "    print('garbage line, no run-finish marker')\n"
            "    sys.exit(0)\n"
            "print('SPAWNED pid=1 pgid=1')\n"
            "print(json.dumps({'action': 'run-finish', 'cmd': [], 'pgid': 1, "
            "'exit_code': 0, 'monitor_reason': 'target-exited', 'time': 't'}))\n")
    else:
        fg.write_text(
            "import json\n"
            "print('SPAWNED pid=1 pgid=1')\n"
            "print(json.dumps({'action': 'run-finish', 'cmd': [], 'pgid': 1, "
            "'exit_code': 0, 'monitor_reason': 'target-exited', 'time': 't'}))\n")
    return fg


def cli_env(guard_dir):
    return {**os.environ,
            "LSU_GEM5_BIN": str(MT / "build/ARM/gem5.opt"),
            "LSU_GUARD_DIR": guard_dir,
            "PYTHONHASHSEED": "0"}


def main():
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name,
              "" if cond else f"  <- {detail}"[:400], flush=True)
        if not cond:
            fails.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="obs_workers_test_"))
    tmp_wt = Path(tempfile.mkdtemp(prefix="obs_workers_wt_", dir=str(WT)))
    try:
        # 环境（进程内所有 in-process 阶段共用一个隔离 guard dir——claims 用；
        # lsu_guard.GUARD_DIR 在 import 时冻结）
        gd_main = tmp / "guard"
        os.environ["LSU_GUARD_DIR"] = str(gd_main)
        os.environ["LSU_GEM5_BIN"] = str(MT / "build/ARM/gem5.opt")
        os.environ["PYTHONHASHSEED"] = "0"
        sys.path.insert(0, str(WT / "tools"))
        import lsu_obs_driver as OD
        import lsu_obs_core as OC

        # ------------------------------------------------ (e) --workers 3
        r = subprocess.run(
            [sys.executable, str(DRIVER), "--items", "ITEM-002", "--phase",
             "screening", "--campaign", "wk_cli", "--workers", "3", "--dry-run",
             "--outdir-root", str(tmp / "e")],
            capture_output=True, text=True, env=cli_env(str(gd_main)),
            cwd=str(WT))
        out = r.stdout + r.stderr
        check("workers3_rejected", r.returncode == 2 and "invalid choice" in out
              and "--workers" in out, f"rc={r.returncode} out={out[-300:]}")

        # ------------------------------------------------ (f) --workers 2 --dry-run
        outf = tmp / "f"
        r = subprocess.run(
            [sys.executable, str(DRIVER), "--items", "ITEM-002", "--phase",
             "screening", "--campaign", "wk_cli", "--workers", "2",
             "--samples", "0", "1", "2", "--dry-run", "--outdir-root", str(outf)],
            capture_output=True, text=True, env=cli_env(str(gd_main)),
            cwd=str(WT))
        out = r.stdout + r.stderr
        check("workers2_dry_rc0", r.returncode == 0, out[-300:])
        check("workers2_dry_header", "workers=2" in out, out[:300])
        check("workers2_dry_3samples",
              all(f"s{s} mode=" in out for s in (0, 1, 2)), out)
        check("workers2_dry_no_side_effects",
              not any(outf.rglob("*")) if outf.exists() else True,
              str(list(outf.rglob("*"))[:5]) if outf.exists() else "")
        check("workers2_dry_no_claims",
              not (gd_main / "claims").exists()
              or not any((gd_main / "claims").rglob("*.claim")),
              str(list((gd_main / "claims").rglob("*.claim"))[:5]
                  if (gd_main / "claims").exists() else ""))

        # ------------------------------------------------ (a) 并行唯一性
        outa = tmp / "a"
        ns = make_ns(campaign="wk_a", outdir_root=str(outa), samples=[0, 1, 2, 3, 4, 5],
                     workers=2, replay_policy="none", obs_mode="l0l5")
        drv = OD.ObsDriver(ns)
        m_seed = drv._manifest_for("ITEM-002", 0)
        seed_golden(drv, m_seed)
        state = {"calls": {}, "threads": set()}
        ODm, orig_rf = install_fake_run_fault(state, delay=0.25)
        finalize_log = []
        orig_fin = OC.finalize_sample

        def counting_fin(staging, final):
            res = orig_fin(staging, final)
            finalize_log.append((str(final), res))
            return res
        OC.finalize_sample = counting_fin
        cap_out = io.StringIO()
        try:
            with contextlib.redirect_stdout(cap_out):
                st = drv.run_item("ITEM-002")
        finally:
            OC.finalize_sample = orig_fin
            ODm.ObsDriver.run_fault = orig_rf
        aout = cap_out.getvalue()
        check("a_status_complete", st == "COMPLETE", st)
        check("a_six_finalized_once",
              len(finalize_log) == 6
              and all(r is not None for _, r in finalize_log),
              str(finalize_log))
        check("a_each_sample_once",
              state["calls"] == {s: 1 for s in range(6)}, str(state["calls"]))
        check("a_two_threads_used", len(state["threads"]) == 2,
              str(state["threads"]))
        camp = outa / "wk_a" / "ITEM-002"
        check("a_all_complete_dirs",
              all((camp / f"ITEM-002_s{s}" / OC.COMPLETE).exists()
                  and (camp / f"ITEM-002_s{s}" / "observation.json").exists()
                  for s in range(6)),
              str(sorted(p.name for p in camp.iterdir())) if camp.exists() else "")
        check("a_no_staging_left",
              not list(camp.rglob("*.staging")),
              str([str(p) for p in camp.rglob('*.staging')]))
        check("a_no_quarantine",
              not list(outa.rglob("*.quarantine.*")),
              str([str(p) for p in outa.rglob('*.quarantine.*')][:3]))
        claims_a = gd_main / "claims" / "wk_a"
        check("a_claims_all_released",
              not claims_a.exists() or not any(claims_a.rglob("*.claim")),
              str(list(claims_a.rglob("*.claim"))[:5]
                  if claims_a.exists() else ""))
        check("a_no_claim_conflict",
              "claim 被持有" not in aout and "GUARD_FAILURE" not in aout,
              aout[-300:])

        # ------------------------------------------------ (b) GuardFailure 停止派发
        # delay=1.5s：s0（manifest ~0.9s + 1.5s sleep）必然晚于 s1
        # （manifest ~0.9s 后立即抛）失败 → 失败先被 wait 收割，s2+ 不派发
        outb = tmp / "b"
        ns = make_ns(campaign="wk_b", outdir_root=str(outb),
                     samples=list(range(8)), workers=2, replay_policy="none",
                     obs_mode="l0l5")
        drv = OD.ObsDriver(ns)
        seed_golden(drv, drv._manifest_for("ITEM-002", 0))
        state = {"calls": {}, "threads": set()}
        ODm, orig_rf = install_fake_run_fault(state, delay=1.5, fail_at=1)
        try:
            st = drv.run_item("ITEM-002")
        finally:
            ODm.ObsDriver.run_fault = orig_rf
        campb = outb / "wk_b" / "ITEM-002"
        check("b_returns_guard_failure", st == "GUARD_FAILURE", st)
        check("b_inflight_s0_completed",
              (campb / "ITEM-002_s0" / OC.COMPLETE).exists(),
              str(sorted(p.name for p in campb.iterdir())) if campb.exists() else "")
        check("b_s1_no_complete",
              not (campb / "ITEM-002_s1" / OC.COMPLETE).exists(), "")
        check("b_no_dispatch_after_failure",
              all(not (campb / f"ITEM-002_s{s}").exists()
                  and not Path(str(campb / f"ITEM-002_s{s}") + ".staging").exists()
                  for s in range(2, 8)),
              str(sorted(p.name for p in campb.iterdir())) if campb.exists() else "")
        check("b_only_two_dispatched",
              sorted(state["calls"]) == [0, 1], str(state["calls"]))
        claims_b = gd_main / "claims" / "wk_b"
        check("b_claims_all_released",
              not claims_b.exists() or not any(claims_b.rglob("*.claim")),
              str(list(claims_b.rglob("*.claim"))[:5]
                  if claims_b.exists() else ""))

        # ------------------------------------------------ (c) slot_policy 解析
        pol_root = tmp / "pol"
        gd_pol = pol_root / "guard"
        os.makedirs(gd_pol, exist_ok=True)
        policy = pol_root / "obs" / "hostmon" / "slot_policy.json"

        def set_policy(text):
            policy.parent.mkdir(parents=True, exist_ok=True)
            if text is None:
                policy.unlink(missing_ok=True)
            else:
                policy.write_text(text)

        os.environ["LSU_GUARD_DIR"] = str(gd_pol)
        set_policy('{"cap": 6}')
        check("c_policy_cap6", OD.read_slot_cap() == 6,
              str(OD.read_slot_cap()))
        set_policy(None)
        check("c_policy_missing_4", OD.read_slot_cap() == 4,
              str(OD.read_slot_cap()))
        set_policy('{"cap": 99}')
        check("c_policy_99_clamp8", OD.read_slot_cap() == 8,
              str(OD.read_slot_cap()))
        set_policy('{"cap": 0}')
        check("c_policy_0_clamp1", OD.read_slot_cap() == 1,
              str(OD.read_slot_cap()))
        set_policy("{not json")
        check("c_policy_corrupt_4", OD.read_slot_cap() == 4,
              str(OD.read_slot_cap()))
        set_policy('{"cap": "six"}')
        check("c_policy_nonint_4", OD.read_slot_cap() == 4,
              str(OD.read_slot_cap()))
        set_policy("{}")
        check("c_policy_nocapkey_4", OD.read_slot_cap() == 4,
              str(OD.read_slot_cap()))
        # --slots 优先于 slot_policy
        ns = make_ns(campaign="wk_c", outdir_root=str(tmp / "c"),
                     guard_dir=str(gd_pol), slots=3)
        drv = OD.ObsDriver(ns)
        set_policy('{"cap": 6}')
        check("c_cli_slots_priority", drv._dispatch_slots() == 3,
              str(drv._dispatch_slots()))
        ns2 = make_ns(campaign="wk_c", outdir_root=str(tmp / "c"),
                      guard_dir=str(gd_pol), slots=None)
        drv2 = OD.ObsDriver(ns2)
        check("c_policy_used_when_no_cli", drv2._dispatch_slots() == 6,
              str(drv2._dispatch_slots()))
        # _guard_run 子进程 env 显式注入（subprocess spy + 无状态假 guard；
        # 假 guard 避免真 guard 的 gate 依赖——宿主内存/磁盘状态不影响本项）
        fg = fake_guard_script(tmp, "fake_guard_ok.py", stateful=False)
        captured = {}
        real_run = subprocess.run

        def spy(cmd, **kw):
            captured["env"] = dict(kw.get("env") or {})
            return real_run(cmd, **kw)
        env_before = os.environ.get("LSU_GUARD_SLOTS")
        real_guard = OD.LR.GUARD
        OD.LR.GUARD = fg
        OD.subprocess.run = spy
        try:
            rc, gtxt = OD._guard_run(["/bin/true"], "WK c", str(tmp / "c_rsrc.log"),
                                     5, "wk_c", "R", "s0", str(tmp / "c_out"),
                                     slots=6)
        finally:
            OD.subprocess.run = real_run
            OD.LR.GUARD = real_guard
        check("c_guard_env_slots6",
              rc == 0 and captured["env"].get("LSU_GUARD_SLOTS") == "6"
              and captured["env"].get("PYTHONHASHSEED") == "0",
              f"rc={rc} env={captured.get('env', {}).get('LSU_GUARD_SLOTS')}")
        check("c_os_environ_not_mutated",
              os.environ.get("LSU_GUARD_SLOTS") == env_before,
              f"before={env_before!r} after={os.environ.get('LSU_GUARD_SLOTS')!r}")
        check("c_runfinish_parsed", '"action": "run-finish"' in gtxt, gtxt[:200])

        # ------------------------------------------------ (d) acquire 重试（假 guard 分支）
        fgs = fake_guard_script(tmp, "fake_guard_stateful.py", stateful=True)

        def run_with_fake_guard(behavior, **kw):
            (tmp / "behavior").write_text(behavior)
            if (tmp / "cnt").exists():
                (tmp / "cnt").unlink()
            real_guard = OD.LR.GUARD
            OD.LR.GUARD = fgs
            try:
                res = OD._guard_run(["/bin/true"], "WK d", str(tmp / "d_rsrc.log"),
                                    5, "wk_d", "R", "s0", str(tmp / "d_out"), **kw)
            finally:
                OD.LR.GUARD = real_guard
            n = int((tmp / "cnt").read_text().strip())
            return res, n

        res, n = run_with_fake_guard("full,ok", acquire_retries=3,
                                     retry_sleep=0.02)
        check("d_slotsfull_retry_success",
              res[0] == 0 and n == 2, f"rc={res[0]} invocations={n}")
        res, n = run_with_fake_guard("stop,ok", acquire_retries=3,
                                     retry_sleep=0.02)
        check("d_stopdispatch_retry_success",
              res[0] == 0 and n == 2, f"rc={res[0]} invocations={n}")
        try:
            run_with_fake_guard("stale", acquire_retries=3, retry_sleep=0.02)
            check("d_stale_immediate_failure", False, "no exception")
        except OD.UP.GuardFailure as gf:
            n = int((tmp / "cnt").read_text().strip())
            check("d_stale_immediate_failure",
                  n == 1 and "陈旧" in str(gf) and "立即失败" in str(gf),
                  f"invocations={n} gf={str(gf)[:200]}")
        try:
            run_with_fake_guard("corrupt", acquire_retries=3, retry_sleep=0.02)
            check("d_corrupt_immediate_failure", False, "no exception")
        except OD.UP.GuardFailure as gf:
            n = int((tmp / "cnt").read_text().strip())
            check("d_corrupt_immediate_failure",
                  n == 1 and "损坏" in str(gf),
                  f"invocations={n} gf={str(gf)[:200]}")
        try:
            run_with_fake_guard("full", acquire_retries=3, retry_sleep=0.02)
            check("d_retries_exhausted", False, "no exception")
        except OD.UP.GuardFailure as gf:
            n = int((tmp / "cnt").read_text().strip())
            check("d_retries_exhausted",
                  n == 4 and "重试 3 次仍被拒" in str(gf),
                  f"invocations={n} gf={str(gf)[:200]}")
        try:
            run_with_fake_guard("silent", acquire_retries=3, retry_sleep=0.02)
            check("d_f023_cycle_incomplete", False, "no exception")
        except OD.UP.GuardFailure as gf:
            n = int((tmp / "cnt").read_text().strip())
            check("d_f023_cycle_incomplete",
                  n == 1 and "周期未完成" in str(gf),
                  f"invocations={n} gf={str(gf)[:200]}")

        # ------------------------------------------------ (d-real) 真 guard 1 槽 2 并发
        # GUARD_DIR 必须在 /home（tmpfs 会触发 guard 磁盘红线 gate）。
        real_root = Path(tempfile.mkdtemp(prefix="obs_workers_real_", dir=str(WT)))
        REAL_TMP_DIRS.append(real_root)
        gd_real = real_root / "guard"
        gd_real.mkdir(parents=True)
        env_real = cli_env(str(gd_real))
        rgate = subprocess.run(
            [sys.executable, str(GUARD), "gate"], capture_output=True,
            text=True, env=env_real, cwd=str(WT))
        gate_ok = '"ok": true' in rgate.stdout
        if not gate_ok:
            check("d_real_gate_precondition", False,
                  f"guard gate BLOCKED（宿主内存/磁盘/编译进程状态不支持本项）: "
                  f"{rgate.stdout[-300:]}")
        else:
            os.environ["LSU_GUARD_DIR"] = str(gd_real)
            results = {}

            def call(tag):
                results[tag] = OD._guard_run(
                    ["sleep", "1"], f"WK real {tag}",
                    str(real_root / f"{tag}.rsrc.log"), 300, "wk_real", "R1",
                    f"s_{tag}", real_root / f"{tag}.out", slots=1,
                    acquire_retries=5, retry_sleep=25.0)
            t0 = time.time()
            with ThreadPoolExecutor(max_workers=2) as ex:
                fa, fb = ex.submit(call, "a"), ex.submit(call, "b")
                fa.result()
                fb.result()
            wall = time.time() - t0
            evlog = (gd_real / "guard_events.log").read_text()
            gates = sum(1 for ln in evlog.splitlines()
                        if '"action": "gate"' in ln)
            finishes = sum(1 for ln in evlog.splitlines()
                           if '"action": "run-finish"' in ln)
            check("d_real_both_succeed",
                  all(rc == 0 for rc, _ in results.values()),
                  str({k: v[0] for k, v in results.items()}))
            check("d_real_retry_happened",
                  gates >= 3 and finishes == 2,
                  f"gate_events={gates} run_finish={finishes} wall={wall:.1f}s")
            check("d_real_second_finishes_after_first",
                  # OBS-SLOT-RELEASE 后：目标退出即释放（≤4s），无需等满
                  # 60s 睡眠——两轮串行 guard 周期下限从 100s 降到 15s
                  wall >= 15, f"wall={wall:.1f}s（1 槽串行 → 两轮 guard 周期）")
            print(f"[d-real] wall={wall:.1f}s gate_events={gates} "
                  f"run_finish={finishes}", flush=True)
            os.environ["LSU_GUARD_DIR"] = str(gd_main)

        print(f"\nFAILURES: {fails if fails else '无'}")
        return 1 if fails else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(tmp_wt, ignore_errors=True)
        for d in REAL_TMP_DIRS:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
