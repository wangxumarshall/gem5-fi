#!/usr/bin/env python3
"""test_lsu_obs_driver_cli.py — 观测驱动 CLI 单测（OBS 计划 T3，不起 gem5）。

全部经 --dry-run（零副作用：不 claim、不建目录、不起 gem5）验证：
  1  命令含 ctrace/msnap 旗标（短流 checklist 载体 → mode=full）
  2  LSU_GEM5_BIN 覆盖生效（worktree 内无 build/，命令首元素=主树冻结件）
  3  numactl node1 前缀（NUMA 实测内存全在 node1）
  4  W1（w1_all）长流载体 Phase A 强制 l0l5（不出现 ctrace 旗标）
  5  dry-run 不产生任何文件副作用
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
WT = HERE.parent
DRIVER = WT / "tools" / "lsu_obs_driver.py"


def gem5_bin():
    """gem5 二进制：$LSU_GEM5_BIN 覆盖 → worktree <WT>/CHAOS/gem5/build/ARM/
    gem5.opt（与 tools/lsu_runner.g5_path / lsu_campaign.resolve_g5 同约定；主树
    repo 根 build/ 已由 R4-10 磁盘审计删除）。dry-run 首元素须与此同值。"""
    env = os.environ.get("LSU_GEM5_BIN")
    return Path(env) if env else WT / "CHAOS/gem5/build/ARM/gem5.opt"


def dry_run(outroot, item, sample):
    env = {**os.environ,
           "LSU_GEM5_BIN": str(gem5_bin()),
           "LSU_GUARD_DIR": "/tmp/obs_cli_test_guard_unused"}
    r = subprocess.run(
        [sys.executable, str(DRIVER), "--items", item, "--phase", "screening",
         "--campaign", "cli_dry", "--samples", str(sample), "--dry-run",
         "--outdir-root", str(outroot)],
        capture_output=True, text=True, env=env, cwd=str(WT))
    return r.returncode, r.stdout + r.stderr


def main():
    tmp = Path(tempfile.mkdtemp(prefix="obs_cli_test_"))
    fails = []

    def check(name, cond, detail=""):
        print(("PASS" if cond else "FAIL"), name, "" if cond else f"  <- {detail}")
        if not cond:
            fails.append(name)

    # 1-3) 短流 checklist 载体（ITEM-002 = A01-F0-W9 gap_bfs）
    rc, out = dry_run(tmp, "ITEM-002", 315)
    check("dryrun_rc0", rc == 0, out[-400:])
    check("mode_full_shortstream", "mode=full" in out, out)
    check("ctrace_flags_present", "--chaos_ctrace" in out
          and "--ctrace_file" in out, out)
    check("msnap_flags_present", "--chaos_msnap" in out
          and "--msnap_file" in out, out)
    check("gem5_bin_override", str(gem5_bin()) in out, out)
    check("numactl_node1", "--cpunodebind=1" in out and "--membind=1" in out,
          out)
    check("lsu_proxy_used", "configs/se/lsu_proxy.py" in out, out)
    check("seed_from_manifest", "--addrpath_rng_seed" in out, out)
    # 5) 零副作用
    check("dryrun_no_side_effects",
          not any(tmp.rglob("*")), str(list(tmp.rglob("*"))[:5]))

    # 4) W1 长流载体强制 l0l5：合成 manifest 单测（清单原生 W1 项在准入层
    #    BLOCKED——新 obs campaign 走清单原生载体，w1 载体仅经 carrier 覆盖
    #    进入，故此处直接测 obs_mode_for 的载体判定）
    sys.path.insert(0, str(WT / "tools"))
    os.environ["LSU_GUARD_DIR"] = "/tmp/obs_cli_test_guard_unused"
    import lsu_obs_driver as OD
    ns = argparse.Namespace(
        campaign="t", obs_mode="full", trace_budget_gib=40.0, outdir_root="/tmp",
        guard_dir=None, gem5_bin=None, slots=None, dry_run=True, phase="screening",
        items=["ITEM-002"], samples=None, target=2, cap=10,
        replay_policy="none")
    drv = OD.ObsDriver(ns)
    mode, reason = drv.obs_mode_for({"carrier": "se:mibench/bin/w1_all"})
    check("w1_forced_l0l5", mode == "l0l5" and "w1_long_stream" in reason,
          f"{mode} {reason}")
    mode2, reason2 = drv.obs_mode_for({"carrier": "se:gap_bfs"})
    check("shortstream_full", mode2 == "full" and reason2 is None,
          f"{mode2} {reason2}")
    drv.degraded_carriers["se:gap_bfs"] = "carrier_over_budget: test"
    mode3, reason3 = drv.obs_mode_for({"carrier": "se:gap_bfs"})
    check("budget_degrade", mode3 == "l0l5"
          and "carrier_over_budget" in reason3, f"{mode3} {reason3}")

    # 4b) CLI 降级路径：--obs-mode l0l5（真实清单项 dry-run，不带 ctrace 旗标）
    env = {**os.environ, "LSU_GEM5_BIN": str(gem5_bin()),
           "LSU_GUARD_DIR": "/tmp/obs_cli_test_guard_unused"}
    r2 = subprocess.run(
        [sys.executable, str(DRIVER), "--items", "ITEM-002", "--phase",
         "screening", "--campaign", "cli_dry", "--samples", "315",
         "--obs-mode", "l0l5", "--dry-run", "--outdir-root", str(tmp)],
        capture_output=True, text=True, env=env, cwd=str(WT))
    out2 = r2.stdout + r2.stderr
    check("cli_l0l5_mode", r2.returncode == 0 and "mode=l0l5" in out2, out2[-300:])
    check("cli_l0l5_no_ctrace", "--chaos_ctrace" not in out2, out2)
    check("dryrun_no_side_effects_2",
          not any(tmp.rglob("*")), str(list(tmp.rglob("*"))[:5]))

    print(f"\nFAILURES: {fails if fails else '无'}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
