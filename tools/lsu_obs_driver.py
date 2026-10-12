#!/usr/bin/env python3
"""lsu_obs_driver.py — LSU L0-L5 观测驱动（OBS 计划 T3，用户指令 2026-10-12 二.1）。

把 ctrace（L2）/msnap（L1）接入 LSU 专用执行链：每个 fault 样本与同
baseline_key 的 no-fault golden ref 比对（commit_diff/micro_diff 直接导入，
W2.2/W2.4 契约零漂移），产出 observation.json v1，staging→原子落盘→COMPLETE。

与 lsu_w1_rerun.py 的关系：不改其语义；本驱动是新实验（观测 campaign）的
专用执行器。防重调度：guard v2 claim 锁 (campaign,RunID,sample) + COMPLETE
目录只读核验跳过（绝不覆盖）。

诚实降级（不阻断、记录 degradations；违反则 violations 阻断 finalize）：
  * W1（w1_all）长流载体 Phase A 强制 l0l5（全量 ctrace 体积不可行，等
    Phase B 激活窗口；coverage_scope 记 none_full_run_forbidden_pending_phaseB）
  * 载体 ctrace 体积 > --trace-budget-gib → 该载体降级 l0l5
  * L3 非 PRF 家族 unsupported（lsu_obs_core 规则）

运行要素：LSU_GUARD_DIR 指主树共享锁目录（host-global）；LSU_GEM5_BIN 指主树
冻结二进制；fault/ref 一律 PYTHONHASHSEED=0；numactl --cpunodebind=1
--membind=1（内存全在 node1，实测拓扑 2026-10-12）。

用法：
  # 观测 campaign（screening 语义，activated 目标）
  python3 tools/lsu_obs_driver.py --items ITEM-002 --phase screening \
      --campaign obs_smoke_20261012 --target 2 --outdir-root runs/lsu/obs
  # 指定样本（E2E/n=2 准入）
  python3 tools/lsu_obs_driver.py --items ITEM-002 --phase screening \
      --campaign e2e --samples 315 321 --replay-policy per_sample
  # 命令构造检查（不起 gem5）
  ... --dry-run
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_runner as LR
import lsu_obs_core as OC
import lsu_unit_pilot as UP

GIB = 1024 ** 3
MS_EVERY = 1000           # CHAOSMicroSnap snapEvery（与 lsu_proxy 默认一致）
DIFF_WORKERS = 2          # 后处理池上限（与 gem5 槽位分离，用户指令 三.4）


def _numactl_prefix():
    """NUMA 实测：内存全在 node1（numactl --hardware 2026-10-12）→ 绑 node1。"""
    if shutil.which("numactl"):
        return ["numactl", "--cpunodebind=1", "--membind=1"]
    return []


def _obs_args(ctrace_file, msnap_file):
    return ["--chaos_ctrace", "--ctrace_file", str(ctrace_file),
            "--chaos_msnap", "--msnap_every", str(MS_EVERY),
            "--msnap_file", str(msnap_file)]


def _guard_run(cmd_argv, desc, log, max_seconds, campaign, runid, sample,
               out_path):
    """guard v2 run 包装：env 固定 PYTHONHASHSEED=0；输出落 out_path。"""
    env = {**os.environ, "PYTHONHASHSEED": "0"}
    with open(out_path, "w") as gf:
        r = subprocess.run(
            ["python3", str(LR.GUARD), "run", "--type", "experiment",
             "--desc", desc, "--log", log, "--interval", "60",
             "--max-seconds", str(max_seconds),
             "--campaign", campaign, "--runid", runid, "--sample", sample,
             "--"] + cmd_argv,
            stdout=gf, stderr=subprocess.STDOUT, env=env)
    gtxt = Path(out_path).read_text(errors="replace")
    ec = re.search(r'"exit_code": (-?\d+)', gtxt)
    if '"action": "run-finish"' not in gtxt or ec is None:
        raise UP.GuardFailure(
            f"guard 周期未完成（F-023 同款）；guard_out={out_path}; "
            f"tail={gtxt[-200:]!r}")
    return int(ec.group(1)), gtxt


class ObsDriver:
    def __init__(self, args):
        self.args = args
        self.root = Path(args.outdir_root).resolve()
        self.golden_root = self.root / "golden"
        # 环境先于 import lsu_guard（模块常量在 import 时读 env）
        os.environ.setdefault("LSU_GUARD_DIR", "")
        self.guard_env = {
            "LSU_GUARD_DIR": args.guard_dir or str(
                Path("/home/sdc/gem5-fi-ding/runs/lsu/guard")),
            "LSU_GEM5_BIN": args.gem5_bin or str(
                Path("/home/sdc/gem5-fi-ding/build/ARM/gem5.opt")),
            "PYTHONHASHSEED": "0",
        }
        os.environ.update(self.guard_env)
        if args.slots:
            os.environ["LSU_GUARD_SLOTS"] = str(args.slots)
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import lsu_guard as G
        self.G = G
        self.degraded_carriers = {}   # carrier -> reason（l0l5 降级）
        self.replay_done = {}         # runid -> evidence（per_runid_first）

    # ------------------------------------------------------------- golden
    def baseline_ident(self, m):
        return {
            "gem5_opt_sha256": m["identity"]["gem5_opt_sha256"],
            "lsu_proxy_sha256": m["identity"]["lsu_proxy_sha256"],
            "workload": m["carrier"], "workload_sha256": m["identity"]["workload_sha256"],
            "cpu": m["config"]["cpu"], "variant": m["config"]["variant"],
            "maxinsts": m["config"]["maxinsts"],
            "obs_flags": ["--chaos_ctrace", "--chaos_msnap",
                          f"--msnap_every={MS_EVERY}"],
            "env": {"PYTHONHASHSEED": "0"},
            "checkpoint": m["identity"]["checkpoint"],
        }

    def ensure_golden(self, m, dry=False):
        """no-fault golden：每 baseline_key 一次，缓存只读复用；漂移拒用。"""
        ident = self.baseline_ident(m)
        key = OC.baseline_key(ident)
        gdir = self.golden_root / key
        ctr, msn = gdir / "commit_trace.csv.gz", gdir / "micro_snap.csv.gz"
        if (gdir / OC.COMPLETE).exists():
            ok, reason = OC.verify_complete(
                gdir, {"gem5_opt_sha256": ident["gem5_opt_sha256"],
                       "baseline_key": key})
            if ok:
                return key, gdir, ident, True   # 缓存复用
            print(f"[golden] {key} 身份漂移/核验失败（{reason}）→ 新 key 重跑",
                  flush=True)
            OC.quarantine(gdir)
        staging = Path(str(gdir) + ".staging")
        if staging.exists():
            OC.quarantine(staging)
        if dry:
            print(f"[golden-dry] {key} → {gdir}")
            return key, gdir, ident, False
        staging.mkdir(parents=True, exist_ok=True)
        wl = LR._wl_path(m["carrier"].split(":")[1])
        cmd = _numactl_prefix() + [str(LR.g5_path()), "--outdir", str(staging),
              str(LR.LSU_PROXY), "--cmd", str(wl), "--cpu", "O3",
              "--variant", "B0"] + _obs_args(staging / "commit_trace.csv.gz",
                                             staging / "micro_snap.csv.gz")
        self._guard_run(cmd, f"OBSREF {m['run_id']} {key[:8]}",
                        str(staging.parent / f"golden_{key[:8]}_rsrc.log"),
                        m["timeout_seconds"], self.args.campaign,
                        m["run_id"], "golden", staging / "gem5.out")
        files = []
        for name in ("commit_trace.csv.gz", "micro_snap.csv.gz", "gem5.out"):
            p = staging / name
            if p.exists():
                files.append({"name": name, "path": name,
                              "sha256": OC.sha256_file(p),
                              "bytes": p.stat().st_size})
        obs = {"schema": OC.SCHEMA,
               "identity": {**ident, "baseline_key": key,
                            "kind": "no_fault_golden",
                            "campaign": self.args.campaign,
                            "git_commit": m["identity"]["git_commit"]},
               "files": files, "violations": [], "degradations": [],
               "note": "no-fault golden ref（L1/L2 比对基线）"}
        (staging / "observation.json").write_text(
            json.dumps(obs, ensure_ascii=False, indent=1))
        OC.finalize_sample(staging, gdir)
        return key, gdir, ident, False

    # ------------------------------------------------------------- one run
    def obs_mode_for(self, m):
        """full / l0l5（诚实降级并记录）。"""
        if self.args.obs_mode == "l0l5":
            return "l0l5", "cli(l0l5)"
        carrier = m["carrier"]
        if carrier.endswith("w1_all"):
            return ("l0l5",
                    "w1_long_stream: full-run ctrace infeasible; pending "
                    "PhaseB activation window (coverage_scope=none_full_run"
                    "_forbidden_pending_phaseB)")
        if carrier in self.degraded_carriers:
            return "l0l5", self.degraded_carriers[carrier]
        return "full", None

    def run_fault(self, m, s, staging, mode):
        cfg, args = LR.build_guard_cmd(m, staging, span=None)
        cmd = [str(LR.g5_path()), "--outdir", str(staging), cfg] + args
        if mode == "full":
            cmd += _obs_args(staging / "commit_trace.csv.gz",
                             staging / "micro_snap.csv.gz")
        cmd = _numactl_prefix() + cmd
        sample = f"s{s}"
        gem5_exit, gtxt = self._guard_run(
            cmd, f"OBS {m['run_id']} {sample}",
            str(staging.parent / f"{m['item']}_{sample}_rsrc.log"),
            m["timeout_seconds"], self.args.campaign, m["run_id"], sample,
            staging / "gem5.out")
        # L5 分类（与 run_one 同口径：guard 合并流同时作 stdout/stderr）
        v = UP.classify_run(staging, staging / "gem5.out", m["golden"],
                            gem5_exit)
        v["gem5_exit"] = gem5_exit
        (staging / "l5_verdict.json").write_text(
            json.dumps(v, ensure_ascii=False, indent=1))
        return v, cmd

    def post_process(self, m, s, staging, mode, golden_dir, replay_ev):
        """diff + observation.json + finalize（后处理池内执行）。"""
        gtxt = (staging / "gem5.out").read_text(errors="replace")
        inj_logs = sorted(staging.glob("*injections.log"))
        inj_text = inj_logs[0].read_text(errors="replace") if inj_logs else ""
        l0 = OC.parse_l0(gtxt, inj_text)
        l5 = json.loads((staging / "l5_verdict.json").read_text())
        inactive = not (l5.get("activated") or 0)
        degr = []
        if mode != "full":
            degr.append(f"obs_mode={mode}（{self.obs_mode_for(m)[1]}）")
        l1 = OC.build_l1(golden_dir / "micro_snap.csv.gz",
                         staging / "micro_snap.csv.gz", inactive=inactive) \
            if mode == "full" else \
            {"status": "not_collected(l0l5_mode)",
             "reason": self.obs_mode_for(m)[1]}
        l2 = OC.build_l2(golden_dir / "commit_trace.csv.gz",
                         staging / "commit_trace.csv.gz", l5=l5,
                         inactive=inactive) \
            if mode == "full" else \
            {"status": "not_collected(l0l5_mode)",
             "reason": self.obs_mode_for(m)[1]}
        l3 = OC.build_l3(m["family"], l2, inactive=inactive)
        l4 = OC.build_l4(l0, l1, l2, l5,
                         fault_msnap_path=staging / "micro_snap.csv.gz",
                         inactive=inactive) \
            if mode == "full" else \
            {"status": "not_collected(l0l5_mode)",
             "reason": self.obs_mode_for(m)[1]}
        files = []
        for name in ("addrpath_injections.log", "commit_trace.csv.gz",
                     "micro_snap.csv.gz", "gem5.out", "l5_verdict.json"):
            p = staging / name
            if p.exists():
                files.append({"name": name, "path": name,
                              "sha256": OC.sha256_file(p),
                              "bytes": p.stat().st_size})
        identity = {
            "campaign": self.args.campaign, "item": m["item"],
            "runid": m["run_id"], "sample": f"s{s}", "seed": m["seed"],
            "phase": m["phase"], "git_commit": m["identity"]["git_commit"],
            "gem5_opt_sha256": m["identity"]["gem5_opt_sha256"],
            "lsu_proxy_sha256": m["identity"]["lsu_proxy_sha256"],
            "workload": m["carrier"],
            "workload_sha256": m["identity"]["workload_sha256"],
            "config_family": "C4-LSU", "pythonhashseed": 0,
            "numa_binding": "node1" if _numactl_prefix() else None,
            "baseline_key": OC.baseline_key(self.baseline_ident(m)),
            "obs_mode": mode,
            "coverage_scope": ("full_run" if mode == "full"
                               else "none_full_run_forbidden_pending_phaseB"),
        }
        obs = OC.build_observation(identity, l0, l1, l2, l3, l4, l5,
                                   replay_ev, files, degradations=degr)
        (staging / "observation.json").write_text(
            json.dumps(obs, ensure_ascii=False, indent=1))
        return obs

    # ------------------------------------------------------------- replay
    def replay_check(self, m, s, mode):
        """同 seed 重跑一次，比对 L0 注入明细 + L5 结局 + （full 时）ctrace sha。"""
        staging = Path(str(self._sample_dir(m, s)) + ".replay")
        if staging.exists():
            OC.quarantine(staging)
        staging.mkdir(parents=True, exist_ok=True)
        v, _ = self.run_fault(m, s, staging, mode)
        inj = sorted(staging.glob("*injections.log"))
        inj_text = inj[0].read_text(errors="replace") if inj else ""
        l0 = OC.parse_l0((staging / "gem5.out").read_text(errors="replace"),
                         inj_text)
        # 与首跑比对
        first = self._sample_dir(m, s)
        f_inj = sorted(first.glob("*injections.log"))
        f_text = f_inj[0].read_text(errors="replace") if f_inj else ""
        f_l0 = OC.parse_l0((first / "gem5.out").read_text(errors="replace"),
                           f_text)
        f_l5 = json.loads((first / "l5_verdict.json").read_text())
        same_inj = ([i["raw"] for i in l0["injections"]]
                    == [i["raw"] for i in f_l0["injections"]])
        same_outcome = (v.get("outcome") == f_l5.get("outcome")
                        and v.get("crash_kind") == f_l5.get("crash_kind"))
        same_trace = True
        if mode == "full":
            a, b = (first / "commit_trace.csv.gz"), \
                (staging / "commit_trace.csv.gz")
            same_trace = (a.exists() and b.exists()
                          and OC.sha256_file(a) == OC.sha256_file(b))
        ev = {"policy": self.args.replay_policy, "verified": bool(
                  same_inj and same_outcome and same_trace),
              "evidence": {"injection_lines_identical": same_inj,
                           "outcome_identical": same_outcome,
                           "commit_trace_sha_identical": same_trace,
                           "replay_dir": str(staging)}}
        # replay 产物保留为证据（.replay 目录，不 finalize——不是正式样本）
        (staging / "replay_verdict.json").write_text(
            json.dumps(ev, ensure_ascii=False, indent=1))
        return ev

    def _sample_dir(self, m, s):
        return self.root / self.args.campaign / m["item"] / f"{m['item']}_s{s}"

    # ------------------------------------------------------------- sample
    def run_sample(self, m, s):
        od = self._sample_dir(m, s)
        sample = f"s{s}"
        if (od / OC.COMPLETE).exists():
            ok, reason = OC.verify_complete(
                od, {"git_commit": m["identity"]["git_commit"],
                     "gem5_opt_sha256": m["identity"]["gem5_opt_sha256"]})
            print(f"[{m['item']} {sample}] COMPLETE 已存在 → 只读核验 "
                  f"{'OK' if ok else 'REFUSED: ' + reason}，跳过", flush=True)
            return ("skipped" if ok else "verify_refused")
        mode, mode_reason = self.obs_mode_for(m)
        key, gdir, _ident, cached = self.ensure_golden(m, self.args.dry_run)
        if mode == "full" and (gdir / "commit_trace.csv.gz").exists():
            gb = (gdir / "commit_trace.csv.gz").stat().st_size / GIB
            if gb > self.args.trace_budget_gib:
                self.degraded_carriers[m["carrier"]] = (
                    f"carrier_over_budget: ref ctrace {gb:.1f}GiB > "
                    f"{self.args.trace_budget_gib}GiB")
                mode, mode_reason = self.obs_mode_for(m)
        if self.args.dry_run:
            # dry：零副作用（不 claim、不建目录、不起 gem5），只打印计划
            staging = Path(str(od) + ".staging")
            cfg, args = LR.build_guard_cmd(m, staging, span=None)
            cmd = _numactl_prefix() + [str(LR.g5_path()), "--outdir",
                                       str(staging), cfg] + args
            if mode == "full":
                cmd += _obs_args(staging / "commit_trace.csv.gz",
                                 staging / "micro_snap.csv.gz")
            print(f"[dry] {m['item']} s{s} mode={mode}"
                  f"{f' reason={mode_reason}' if mode_reason else ''} "
                  f"golden={key[:8]}{'(cached)' if cached else '(new)'}")
            print(f"[dry] cmd: {' '.join(str(c) for c in cmd)}")
            return "dry"
        # claim（防重调度；stale → 中止本项保现场）
        claim, reason = self.G._claim_acquire(
            self.args.campaign, m["run_id"], sample,
            f"obs-driver pid={os.getpid()}")
        if claim is None:
            if "陈旧" in reason:
                raise UP.GuardFailure(f"claim stale: {reason}")
            print(f"[{m['item']} {sample}] claim 被持有 → 跳过（{reason[:80]}）",
                  flush=True)
            return "claimed_elsewhere"
        try:
            staging = Path(str(od) + ".staging")
            if staging.exists():
                q = OC.quarantine(staging)
                print(f"[{m['item']} {sample}] staging 残留 → 隔离 {q.name}",
                      flush=True)
            od.parent.mkdir(parents=True, exist_ok=True)
            staging.mkdir(parents=True, exist_ok=True)
            v, _cmd = self.run_fault(m, s, staging, mode)
            # replay 策略
            if self.args.replay_policy == "per_sample":
                ev = self.replay_check(m, s, mode)
            elif (self.args.replay_policy == "per_runid_first"
                  and m["run_id"] not in self.replay_done):
                ev = self.replay_check(m, s, mode)
                self.replay_done[m["run_id"]] = ev
            elif self.args.replay_policy == "per_runid_first":
                ev = {"policy": "per_runid_first", "verified": True,
                      "evidence": {"reused_from": "本 RunID 首样本重放",
                                   **(self.replay_done.get(m["run_id"], {})
                                      .get("evidence", {}))}}
            else:
                ev = {"policy": "none", "verified": False,
                      "evidence": {"reason": "--replay-policy none"}}
            obs = self.post_process(m, s, staging, mode, gdir, ev)
            OC.finalize_sample(staging, od)
            print(f"[{m['item']} {sample}] {v.get('outcome')}/"
                  f"{v.get('crash_kind', '-')} mode={mode} "
                  f"chain_complete={obs['chain_complete']} "
                  f"({obs['chain_status_reason'][:80]})", flush=True)
            return "complete"
        finally:
            ok, msg, _p = self.G._claim_release(
                self.args.campaign, m["run_id"], sample, os.getpid())
            if not ok:
                print(f"WARNING: claim 释放异常: {msg}", file=sys.stderr)

    # ------------------------------------------------------------- items
    def run_item(self, it):
        m0 = LR.build_manifest(it, self.args.phase, 0)
        if self.args.samples:
            plan = list(self.args.samples)
        else:
            plan = list(range(0, self.args.cap))
        done = activated = 0
        for s in plan:
            if (not self.args.samples) and activated >= self.args.target:
                break
            try:
                r = self.run_sample(m0, s)
            except UP.GuardFailure as gf:
                print(f"[{it}] s{s}: GUARD_FAILURE {gf}"[:300], flush=True)
                return "GUARD_FAILURE"
            if r == "complete":
                done += 1
                v = json.loads((self._sample_dir(m0, s) / "l5_verdict.json")
                               .read_text())
                activated += 1 if (v.get("activated") or 0) else 0
            elif r == "verify_refused":
                return "VERIFY_REFUSED"
        status = ("COMPLETE" if (self.args.samples or activated >= self.args.target)
                  else "BLOCKED_ATTEMPT_CAP")
        return status

    def main(self):
        args = self.args
        if not args.dry_run:
            self.root.mkdir(parents=True, exist_ok=True)
        print(f"OBS campaign start {time.strftime('%F %T')} campaign={args.campaign} "
              f"items={args.items} phase={args.phase} mode={args.obs_mode} "
              f"replay={args.replay_policy} outdir={self.root} "
              f"guard_dir={os.environ['LSU_GUARD_DIR']} "
              f"slots={os.environ.get('LSU_GUARD_SLOTS', '4(默认)')}", flush=True)
        results = {}
        for it in args.items:
            results[it] = self.run_item(it)
            print(f"[{it}] => {results[it]}", flush=True)
        if not args.dry_run:
            (self.root / args.campaign / "driver_summary.json").write_text(
                json.dumps({"campaign": args.campaign, "items": results,
                            "started_env": {k: os.environ.get(k)
                                            for k in ("LSU_GUARD_DIR",
                                                      "LSU_GUARD_SLOTS",
                                                      "LSU_GEM5_BIN",
                                                      "PYTHONHASHSEED")},
                            "time": time.strftime("%F %T")},
                           ensure_ascii=False, indent=1))
        print(f"OBS campaign end {time.strftime('%F %T')} {results}", flush=True)
        return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--items", nargs="+", required=True)
    ap.add_argument("--phase", default="screening")
    ap.add_argument("--campaign", required=True)
    ap.add_argument("--samples", nargs="+", type=int, default=None,
                    help="显式样本号（E2E/n=2 准入）；缺省按 target/cap 顺序")
    ap.add_argument("--target", type=int, default=30,
                    help="activated 目标（非 --samples 模式）")
    ap.add_argument("--cap", type=int, default=300)
    ap.add_argument("--obs-mode", choices=["full", "l0l5"], default="full")
    ap.add_argument("--trace-budget-gib", type=float, default=40.0)
    ap.add_argument("--replay-policy",
                    choices=["per_sample", "per_runid_first", "none"],
                    default="per_runid_first")
    ap.add_argument("--outdir-root", default="runs/lsu/obs")
    ap.add_argument("--guard-dir", default=None,
                    help="host-global 锁目录（默认主树 runs/lsu/guard）")
    ap.add_argument("--gem5-bin", default=None,
                    help="冻结 gem5.opt 绝对路径（默认主树 repo 根）")
    ap.add_argument("--slots", type=int, default=None,
                    help="LSU_GUARD_SLOTS 覆盖（≤8；默认 4 或 slot_policy）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.slots:
        os.environ["LSU_GUARD_SLOTS"] = str(args.slots)
    return ObsDriver(args).main()


if __name__ == "__main__":
    sys.exit(main())
