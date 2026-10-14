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

OBS-8a（样本级并行 + slot_policy + acquire 重试，用户指令 2026-10-12）：
  * --workers 1..2：ThreadPoolExecutor 样本级并行（仿 lsu_unit_pilot
    F-022 模式）；派发条件 = activated<target 且 在飞+完成<cap 且
    在飞<workers（--samples 清单模式跑全清单）；任一线程 GuardFailure →
    停止派发、在飞样本自然完成（verdict 落盘，resume 可复活）
  * 每次派发前读 hostmon slot_policy.json 的 cap（--slots 优先；缺失/
    损坏/非法→4；合法 int clamp [1,8]）作为 guard 子进程 LSU_GUARD_SLOTS
    ——显式传子进程 env，不写 os.environ（多线程竞态）
  * guard ACQUIRE REFUSED 且原因非"陈旧/损坏"（槽满/STOP_DISPATCH）→
    自动重试（默认 5 次 × 60s，等槽位/内存回升）；陈旧/损坏仍立即
    GuardFailure（F-023 语义不变）

用法：
  # 观测 campaign（screening 语义，activated 目标）
  python3 tools/lsu_obs_driver.py --items ITEM-002 --phase screening \
      --campaign obs_smoke_20261012 --target 2 --outdir-root runs/lsu/obs
  # 指定样本（E2E/n=2 准入）
  python3 tools/lsu_obs_driver.py --items ITEM-002 --phase screening \
      --campaign e2e --samples 315 321 --replay-policy per_sample
  # 样本级并行（OBS-8a；本阶段上限 2 worker；--samples 清单模式同样支持）
  ... --workers 2 --target 8 --cap 40
  # 命令构造检查（不起 gem5）
  ... --dry-run
"""
import argparse
import hashlib
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_runner as LR
import lsu_obs_core as OC
import lsu_l3_propagation as LP   # [LSU][OBS-L3] COVERED_FAMILIES + parser
import lsu_unit_pilot as UP

GIB = 1024 ** 3
MS_EVERY = 1000           # CHAOSMicroSnap snapEvery（与 lsu_proxy 默认一致）
DIFF_WORKERS = 2          # 后处理池上限（与 gem5 槽位分离，用户指令 三.4）

# ---- OBS-8a：样本级并行 + slot_policy + acquire 重试 ------------------------
DEFAULT_SLOTS = 4         # slot_policy 缺失/损坏/非法的回退（= guard v2 默认）
SLOTS_MIN, SLOTS_MAX = 1, 8
ACQUIRE_RETRIES = 5       # ACQUIRE REFUSED（槽满/STOP_DISPATCH）重试上限
ACQUIRE_RETRY_SLEEP_S = 60.0   # 重试间隔：等槽位/内存回升


def read_slot_cap():
    """hostmon slot_policy.json 的 cap（每次派发样本前读，OBS-8a）。

    路径 = Path(LSU_GUARD_DIR).parent / "obs" / "hostmon" / "slot_policy.json"。
    缺失/损坏/非法（无 cap 键 / 非 int，含 bool）→ 回退 DEFAULT_SLOTS；
    合法 int → clamp 到 [SLOTS_MIN, SLOTS_MAX]（cap=99 → 8）。
    """
    try:
        gd = os.environ["LSU_GUARD_DIR"]
        policy = json.loads(
            (Path(gd).parent / "obs" / "hostmon" / "slot_policy.json")
            .read_text(encoding="utf-8"))
        cap = policy["cap"]
        if not isinstance(cap, int) or isinstance(cap, bool):
            return DEFAULT_SLOTS
    except (KeyError, TypeError, OSError, ValueError):
        return DEFAULT_SLOTS
    return max(SLOTS_MIN, min(SLOTS_MAX, cap))


def _numactl_prefix():
    """NUMA 实测：内存全在 node1（numactl --hardware 2026-10-12）→ 绑 node1。"""
    if shutil.which("numactl"):
        return ["numactl", "--cpunodebind=1", "--membind=1"]
    return []


def _obs_args(ctrace_file, msnap_file, family=None, prop_trace_file=None):
    """OBS 观测旗标：ctrace(L2)/msnap(L1) + [LSU][OBS-L3] 覆盖家族的
    prop_trace(L3)。

    [LSU][OBS-L3] family ∈ LP.COVERED_FAMILIES（addrpath/cache）且
    prop_trace_file 给出时追加 --chaos_propagation/--prop_trace_file。
    golden 不加（无故障 → 空 trace；golden obs_flags 保持稳定）；
    未覆盖家族（lsqfwd/prefetch/exmon）不加 → obs_core 走 unsupported
    （如实）。
    """
    args = ["--chaos_ctrace", "--ctrace_file", str(ctrace_file),
            "--chaos_msnap", "--msnap_every", str(MS_EVERY),
            "--msnap_file", str(msnap_file)]
    if family in LP.COVERED_FAMILIES and prop_trace_file is not None:
        args += ["--chaos_propagation",
                 "--prop_trace_file", str(prop_trace_file)]
    return args


def _guard_env(slots=None):
    """guard 子进程 env：PYTHONHASHSEED=0 固定 + LSU_GUARD_SLOTS 显式注入。

    OBS-8a：绝不写 os.environ（多 worker 线程竞态）；slots=None → 继承
    调用方环境（--slots 在 main() 启动时已落 os.environ，或 guard 默认 4）。
    """
    env = {**os.environ, "PYTHONHASHSEED": "0"}
    if slots is not None:
        env["LSU_GUARD_SLOTS"] = str(slots)
    return env


def _guard_run(cmd_argv, desc, log, max_seconds, campaign, runid, sample,
               out_path, slots=None, acquire_retries=None, retry_sleep=None):
    """guard v2 run 包装：env 固定 PYTHONHASHSEED=0；输出落 out_path。

    OBS-8a acquire 重试：guard 输出含 ACQUIRE REFUSED 且原因非"陈旧/损坏"
    （槽满 / STOP_DISPATCH）→ 至多 acquire_retries 次（默认 5）、间隔
    retry_sleep 秒（默认 60s，等槽位/内存回升）后重试；"陈旧锁/损坏"仍
    立即 GuardFailure（F-023 语义不变）。run-finish 判定先行（防 gem5
    自身输出偶含拒绝字样被误判为 acquire 失败）。
    """
    retries = ACQUIRE_RETRIES if acquire_retries is None else acquire_retries
    sleep_s = ACQUIRE_RETRY_SLEEP_S if retry_sleep is None else retry_sleep
    env = _guard_env(slots)
    attempt = 0
    while True:
        with open(out_path, "w") as gf:
            subprocess.run(
                ["python3", str(LR.GUARD), "run", "--type", "experiment",
                 "--desc", desc, "--log", log, "--interval", "60",
                 "--max-seconds", str(max_seconds),
                 "--campaign", campaign, "--runid", runid, "--sample", sample,
                 "--"] + cmd_argv,
                stdout=gf, stderr=subprocess.STDOUT, env=env)
        gtxt = Path(out_path).read_text(errors="replace")
        ec = re.search(r'"exit_code": (-?\d+)', gtxt)
        if '"action": "run-finish"' in gtxt and ec is not None:
            return int(ec.group(1)), gtxt
        if "ACQUIRE REFUSED" in gtxt:
            if "陈旧" in gtxt or "损坏" in gtxt:
                raise UP.GuardFailure(
                    f"guard acquire 拒绝（陈旧/损坏，F-023 立即失败）；"
                    f"guard_out={out_path}; tail={gtxt[-200:]!r}")
            if attempt < retries:
                attempt += 1
                print(f"[guard] ACQUIRE REFUSED（槽满/STOP_DISPATCH）→ "
                      f"{sleep_s}s 后重试 {attempt}/{retries}: {desc}",
                      flush=True)
                time.sleep(sleep_s)
                continue
            raise UP.GuardFailure(
                f"guard acquire 重试 {retries} 次仍被拒（槽满/STOP_DISPATCH，"
                f"共 {retries + 1} 次尝试）；guard_out={out_path}; "
                f"tail={gtxt[-200:]!r}")
        raise UP.GuardFailure(
            f"guard 周期未完成（F-023 同款）；guard_out={out_path}; "
            f"tail={gtxt[-200:]!r}")


class ObsDriver:
    # OBS-8a 修复：模块级 _guard_run 此前从未绑定到类——self._guard_run 是
    # 潜在 AttributeError（任何非 dry 运行在 ensure_golden/run_fault 即崩）。
    # staticmethod 绑定后模块函数 / self. 两种调用形态都可用（签名不含 self）。
    _guard_run = staticmethod(_guard_run)

    def __init__(self, args):
        self.args = args
        self.root = Path(args.outdir_root).resolve()
        self.golden_root = self.root / "golden"
        # OBS-8a：并行/重试参数（CLI 之外直接构造 Namespace 时取默认）
        self.workers = int(getattr(args, "workers", 1) or 1)
        self.acquire_retries = getattr(args, "acquire_retries", None)
        self.acquire_retry_sleep = getattr(args, "acquire_retry_sleep", None)
        # OBS-8a：并发 worker 同 baseline_key 的 golden 双跑防护（per-key 锁）
        self._golden_mu = threading.Lock()
        self._golden_locks = {}
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

    def ensure_golden(self, m, dry=False, slots=None):
        """no-fault golden：每 baseline_key 一次，缓存只读复用；漂移拒用。

        OBS-8a：并发 worker 同 key 双跑防护——per-key 串行锁 + 双检（后到
        线程等待后直接复用先到线程产物，绝不隔离他人进行中的 staging）。
        """
        ident = self.baseline_ident(m)
        key = OC.baseline_key(ident)
        gdir = self.golden_root / key
        ctr, msn = gdir / "commit_trace.csv.gz", gdir / "micro_snap.csv.gz"

        def _cached():
            ok, reason = OC.verify_complete(
                gdir, {"gem5_opt_sha256": ident["gem5_opt_sha256"],
                       "baseline_key": key})
            if ok:
                return True
            print(f"[golden] {key} 身份漂移/核验失败（{reason}）→ 新 key 重跑",
                  flush=True)
            OC.quarantine(gdir)
            return False

        if (gdir / OC.COMPLETE).exists() and _cached():
            return key, gdir, ident, True   # 缓存复用
        if dry:
            # dry 零副作用（OBS-3 契约）：不建锁文件/不建目录/不隔离残留
            print(f"[golden-dry] {key} → {gdir}")
            return key, gdir, ident, False
        with self._golden_mu:
            glock = self._golden_locks.setdefault(key, threading.Lock())
        # 跨进程互斥（Subagent-A 上抛 → 主负责人实现）：多 driver 进程共享
        # golden 根目录时，进程内锁不够；flock 覆盖"运行+finalize"全程
        with glock, OC.file_lock(self.golden_root / f"{key}.golden.lock"):
            # 双检：并行 worker 或另一 driver 进程可能已在此期间完成 golden
            if (gdir / OC.COMPLETE).exists() and _cached():
                return key, gdir, ident, True
            staging = Path(str(gdir) + ".staging")
            if staging.exists():
                OC.quarantine(staging)
            staging.mkdir(parents=True, exist_ok=True)
            wl = LR._wl_path(m["carrier"].split(":")[1])
            cmd = _numactl_prefix() + [str(LR.g5_path()), "--outdir", str(staging),
                  str(LR.LSU_PROXY), "--cmd", str(wl), "--cpu", "O3",
                  "--variant", "B0"] + _obs_args(staging / "commit_trace.csv.gz",
                                                 staging / "micro_snap.csv.gz")
            self._guard_run(cmd, f"OBSREF {m['run_id']} {key[:8]}",
                            str(staging.parent / f"golden_{key[:8]}_rsrc.log"),
                            m["timeout_seconds"], self.args.campaign,
                            m["run_id"], "golden", staging / "gem5.out",
                            slots=slots,
                            acquire_retries=self.acquire_retries,
                            retry_sleep=self.acquire_retry_sleep)
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

    def run_fault(self, m, s, staging, mode, slots=None):
        cfg, args = LR.build_guard_cmd(m, staging, span=None)
        cmd = [str(LR.g5_path()), "--outdir", str(staging), cfg] + args
        if mode == "full":
            # [LSU][OBS-L3] 覆盖家族（addrpath/cache）追加 prop_trace 旗标
            cmd += _obs_args(staging / "commit_trace.csv.gz",
                             staging / "micro_snap.csv.gz",
                             family=m["family"],
                             prop_trace_file=staging / "prop_trace.csv.gz")
        cmd = _numactl_prefix() + cmd
        sample = f"s{s}"
        gem5_exit, gtxt = self._guard_run(
            cmd, f"OBS {m['run_id']} {sample}",
            str(staging.parent / f"{m['item']}_{sample}_rsrc.log"),
            m["timeout_seconds"], self.args.campaign, m["run_id"], sample,
            staging / "gem5.out", slots=slots,
            acquire_retries=self.acquire_retries,
            retry_sleep=self.acquire_retry_sleep)
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
        # BUG-2 修复（Subagent-C 发现）：fault 侧探针路径在 staging→正式目录
        # 原子改名后失效——改记样本目录内相对名（ref 侧 golden 目录稳定，
        # 绝对路径保留）
        for entry in (l1, l2):
            fprobe = entry.get("fault")
            if isinstance(fprobe, dict) and fprobe.get("path"):
                fprobe["path"] = Path(fprobe["path"]).name
                fprobe["path_note"] = "样本目录内相对名（staging 改名后仍有效）"
        l3 = OC.build_l3(m["family"], l2, inactive=inactive)
        # [LSU][OBS-L3] 真实传播链 L3（纠偏指令 2026-10-13）：覆盖家族
        #（addrpath/cache）+ full 模式 + prop_trace 存在 → 传播链解析。
        # obs_core 已接 prop_trace_path 委托（B 侧）时走 OC.build_l3；
        # 否则直连 LP.build_l3（同一实现，B 侧接线前的兼容回退——绝不
        # 因 obs_core 未合入而退回 unsupported 假象）。未覆盖家族/未收集
        # → obs_core 原路径（unsupported / N/A 如实）。
        prop_path = staging / "prop_trace.csv.gz"
        prop_collected = (mode == "full"
                          and m["family"] in LP.COVERED_FAMILIES
                          and prop_path.exists())
        if prop_collected:
            if "prop_trace_path" in inspect.signature(
                    OC.build_l3).parameters:
                l3 = OC.build_l3(m["family"], l2, inactive=inactive,
                                 prop_trace_path=prop_path)
            else:
                l3 = LP.build_l3(m["family"], l2, prop_path,
                                 inactive=inactive)
        l4 = OC.build_l4(l0, l1, l2, l5,
                         fault_msnap_path=staging / "micro_snap.csv.gz",
                         inactive=inactive) \
            if mode == "full" else \
            {"status": "not_collected(l0l5_mode)",
             "reason": self.obs_mode_for(m)[1]}
        files = []
        # [LSU][OBS-L3] prop_trace.csv.gz 入 files（sha256/bytes 溯源）；
        # cache_injections.log = cache 家族（新覆盖）注入日志（FUNNEL 行
        # 在此，best-effort；abort 存活副本在 prop_trace funnel 节点）。
        for name in ("addrpath_injections.log", "prop_trace.csv.gz",
                     "cache_injections.log", "commit_trace.csv.gz",
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
            # [LSU][OBS-L3] 该样本是否收集了传播链 trace（覆盖家族+full）
            "prop_traced": bool(prop_collected),
        }
        # [LSU][OBS-L3] obs_core 已接 prop_trace_path（B 侧）时透传；
        # 未接时按原签名调用（兼容回退，见上方 l3 分支注释）。
        if prop_collected and "prop_trace_path" in inspect.signature(
                OC.build_observation).parameters:
            obs = OC.build_observation(identity, l0, l1, l2, l3, l4, l5,
                                       replay_ev, files, degradations=degr,
                                       prop_trace_path=prop_path)
        else:
            obs = OC.build_observation(identity, l0, l1, l2, l3, l4, l5,
                                       replay_ev, files, degradations=degr)
        (staging / "observation.json").write_text(
            json.dumps(obs, ensure_ascii=False, indent=1))
        return obs

    # ------------------------------------------------------------- replay
    def replay_check(self, m, s, mode, slots=None, first_staging=None):
        """同 seed 重跑一次，比对 L0 注入明细 + L5 结局 + （full 时）ctrace sha。

        BUG-3 修复（E2E 重跑实测发现）：首跑此刻仍在 staging（finalize 在
        replay 之后才发生）——比对必须读 first_staging，绝不能读最终目录。
        """
        staging = Path(str(self._sample_dir(m, s)) + ".replay")
        if staging.exists():
            OC.quarantine(staging)
        staging.mkdir(parents=True, exist_ok=True)
        v, _ = self.run_fault(m, s, staging, mode, slots=slots)
        inj = sorted(staging.glob("*injections.log"))
        inj_text = inj[0].read_text(errors="replace") if inj else ""
        l0 = OC.parse_l0((staging / "gem5.out").read_text(errors="replace"),
                         inj_text)
        # 与首跑比对（首跑产物在 first_staging；不传则回退最终目录=已完成
        # 样本的补验场景）
        first = Path(first_staging) if first_staging else self._sample_dir(m, s)
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
    def run_sample(self, m, s, slots=None):
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
        key, gdir, _ident, cached = self.ensure_golden(
            m, self.args.dry_run, slots=slots)
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
                                 staging / "micro_snap.csv.gz",
                                 family=m["family"],
                                 prop_trace_file=staging / "prop_trace.csv.gz")
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
            v, _cmd = self.run_fault(m, s, staging, mode, slots=slots)
            # replay 策略
            if self.args.replay_policy == "per_sample":
                ev = self.replay_check(m, s, mode, slots=slots,
                                       first_staging=staging)
            elif (self.args.replay_policy == "per_runid_first"
                  and m["run_id"] not in self.replay_done):
                ev = self.replay_check(m, s, mode, slots=slots,
                                       first_staging=staging)
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
    def _dispatch_slots(self):
        """每次派发样本前的有效槽位数（OBS-8a）：--slots 优先，否则读
        hostmon slot_policy.json 的 cap（缺失/损坏/非法→4；clamp [1,8]）。"""
        if self.args.slots:
            return self.args.slots
        return read_slot_cap()

    def _manifest_for(self, it, s):
        """每样本独立 manifest（seed = lsu_seed(RunID, phase, s)）。

        OBS-8a 修复：OBS-3 的 run_item 曾对全部样本复用 sample_index=0 的
        manifest——所有样本同 seed（同故障配置），screening 序贯与
        --samples resume 语义双双失效。lsu_unit_pilot.run_item_samples 的
        per-sample build_manifest 才是既定口径。
        """
        return LR.build_manifest(it, self.args.phase, s)

    def run_item(self, it):
        if self.args.samples:
            plan = list(self.args.samples)
        else:
            plan = list(range(0, self.args.cap))
        # dry-run 走串行（零副作用打印，无需并行）；workers>1 走并行路径
        if self.workers > 1 and not self.args.dry_run:
            return self._run_item_parallel(it, plan)
        done = activated = 0
        for s in plan:
            if (not self.args.samples) and activated >= self.args.target:
                break
            m = self._manifest_for(it, s)
            try:
                r = self.run_sample(m, s, slots=self._dispatch_slots())
            except UP.GuardFailure as gf:
                print(f"[{it}] s{s}: GUARD_FAILURE {gf}"[:300], flush=True)
                return "GUARD_FAILURE"
            if r in ("complete", "skipped"):
                # OBS-FIX-2（2026-10-14，C02-F0-W6 续跑根因）：skipped =
                # COMPLETE 已存在（只读核验通过）——resume 遍必须计入既有
                # activated，否则漏计导致 target 模式续跑超采总数。
                done += 1
                v = json.loads((self._sample_dir(m, s) / "l5_verdict.json")
                               .read_text())
                activated += 1 if (v.get("activated") or 0) else 0
            elif r == "verify_refused":
                return "VERIFY_REFUSED"
        status = ("COMPLETE" if (self.args.samples or activated >= self.args.target)
                  else "BLOCKED_ATTEMPT_CAP")
        return status

    def _run_item_parallel(self, it, plan):
        """OBS-8a：样本级并行（F-022 模式，仿 lsu_unit_pilot.run_item_samples）。

        派发条件 = activated+在飞<target（OBS-FIX-1，2026-10-14：在飞按最坏
        情况全激活计——旧门只看已完成 activated，C01-F0-W6 target=385 实采
        386 超采 1）且 在飞+完成<cap 且 在飞<workers（--samples 显式清单
        模式不受 target/cap 门限，跑全清单）。不变式：任一派发点
        activated+在飞 ≤ target → 终态 activated 精确 == target（target 附近
        最后 ≤ workers-1 个样本退化为串行，代价可忽略）。
        每样本完整跑 run_sample（claim 防同样本双跑；golden per-key 锁防
        并发双建）。manifest 构建在 worker 内做（build_manifest 含 gem5.opt
        sha256 ~秒级——放派发循环会让 Python 3.11 的 idle-permit 复用把
        池退化成单线程；放 worker 内还顺带并行化了这笔开销）。
        任一线程 GuardFailure → 停止派发，在飞样本由 executor 退出时自然
        完成（verdict 落盘可被 resume 复活）；verify_refused 同理（串行
        路径是立即返回，此处是停止派发+等在飞）。
        """
        workers = self.workers
        activated = dispatched = 0
        guard_failure = None
        verify_refused = False

        def _run_one(s, slots):
            m = self._manifest_for(it, s)
            return self.run_sample(m, s, slots=slots)

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures, nxt = {}, 0   # future -> sample 号
            while True:
                # 派发（dispatched = 在飞 + 已完成，即 attempt 计数；
                # OBS-FIX-1：target 门计入在飞 len(futures)——见 docstring）
                while (guard_failure is None and not verify_refused
                       and len(futures) < workers
                       and nxt < len(plan)
                       and (self.args.samples
                            or (activated + len(futures) < self.args.target
                                and dispatched < self.args.cap))):
                    s = plan[nxt]
                    nxt += 1
                    dispatched += 1
                    fut = ex.submit(_run_one, s, self._dispatch_slots())
                    futures[fut] = s
                if not futures:
                    break
                fin, _ = wait(set(futures), return_when=FIRST_COMPLETED)
                for f in fin:
                    s = futures.pop(f)
                    try:
                        r = f.result()
                    except UP.GuardFailure as gf:
                        # 停止派发；在飞样本自然完成——verdict 有效落盘，
                        # 断点续跑经 resume 复活，不浪费
                        guard_failure = gf
                        print(f"[{it}] s{s}: GUARD_FAILURE {gf}"[:300],
                              flush=True)
                        continue
                    if r in ("complete", "skipped"):
                        # OBS-FIX-2：skipped 计入既有 activated（同串行路径，
                        # C02-F0-W6 续跑根因——漏计导致超采总数）
                        # 同 _sample_dir 的路径公式（m["item"] == it）
                        od = self.root / self.args.campaign / it / f"{it}_s{s}"
                        v = json.loads((od / "l5_verdict.json").read_text())
                        activated += 1 if (v.get("activated") or 0) else 0
                    elif r == "verify_refused":
                        verify_refused = True
            # executor.__exit__ 等待全部在飞样本完成
        if guard_failure is not None:
            return "GUARD_FAILURE"
        if verify_refused:
            return "VERIFY_REFUSED"
        status = ("COMPLETE" if (self.args.samples or activated >= self.args.target)
                  else "BLOCKED_ATTEMPT_CAP")
        return status

    def main(self):
        args = self.args
        if not args.dry_run:
            self.root.mkdir(parents=True, exist_ok=True)
        slots_hdr = (f"slots={args.slots}" if args.slots else
                     "slots=slot_policy(每次派发读取，缺失/损坏回退 4)")
        print(f"OBS campaign start {time.strftime('%F %T')} campaign={args.campaign} "
              f"items={args.items} phase={args.phase} mode={args.obs_mode} "
              f"replay={args.replay_policy} outdir={self.root} "
              f"guard_dir={os.environ['LSU_GUARD_DIR']} workers={self.workers} "
              f"{slots_hdr} "
              f"acquire_retries={self.acquire_retries if self.acquire_retries is not None else ACQUIRE_RETRIES}"
              f"x{self.acquire_retry_sleep if self.acquire_retry_sleep is not None else ACQUIRE_RETRY_SLEEP_S}s",
              flush=True)
        results = {}
        for it in args.items:
            results[it] = self.run_item(it)
            print(f"[{it}] => {results[it]}", flush=True)
        if not args.dry_run:
            (self.root / args.campaign / "driver_summary.json").write_text(
                json.dumps({"campaign": args.campaign, "items": results,
                            "workers": self.workers,
                            "acquire_retries": (self.acquire_retries
                                                if self.acquire_retries is not None
                                                else ACQUIRE_RETRIES),
                            "acquire_retry_sleep_s": (self.acquire_retry_sleep
                                                      if self.acquire_retry_sleep is not None
                                                      else ACQUIRE_RETRY_SLEEP_S),
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
    ap.add_argument("--workers", type=int, choices=[1, 2], default=1,
                    help="样本级并行 worker 数（OBS-8a；本阶段上限 2；"
                         "--samples 清单模式同样支持；dry-run 恒串行打印）")
    ap.add_argument("--acquire-retries", type=int, default=None,
                    help="guard ACQUIRE REFUSED（槽满/STOP_DISPATCH）重试次数"
                         "（默认 5；陈旧/损坏不重试，F-023 立即失败）")
    ap.add_argument("--acquire-retry-sleep", type=float, default=None,
                    help="acquire 重试间隔秒（默认 60；等槽位/内存回升）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.slots:
        os.environ["LSU_GUARD_SLOTS"] = str(args.slots)
    return ObsDriver(args).main()


if __name__ == "__main__":
    sys.exit(main())
