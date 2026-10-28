#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-A4] F2 repeat census —— 子模型过滤后 eligible 流的真实标定。

问题（已实证）：F2 首火位是 eligible 计数的序号
（chaos_lsu_trigger.hh:224/291 -> next_fire = warmup + 50000 + lcg(seed)%100000，
lcg = chaos_event_sample.hh:49 的 chaosSampleLCG），而旧 REPEAT_FACTOR 按
**裸访存流**标定。A04/A05-d/A06/A08 的 eligible 是子模型过滤后的流，
实测 A05-F2-W3 s1（R=434）attempted=156129 eligible=91623 injected=0 ——
91623 < 140806。本工具用**真实 campaign 命令路径**（lsu_campaign.resolve_cell
+ apply_seed_variant_flags + 同一 seed 旗标/propagation 旗标）跑
repeat=1/5/10，解析 teardown 的 `CHAOS_LSU_TRIGGER:` 行，得到
  E1 = eligible(repeat=1)
  delta = (eligible(repeat=5) - E1) / 4      （稳定性检查用 repeat=10）
  R = 1 + ceil((1.2*max_first_eligible - E1) / delta)，下限 1
其中 max_first_eligible 由 chaosSampleLCG 对 seed1/2/3 独立重算（不抄报告）。
随后（--verify）以 R 真实重跑一次，断言 injected=1 并做三方计数一致性检查
（run.out / addrpath_injections.log FUNNEL / campaign 的 L5 分类）。

证据落盘：每趟一个全新目录
  <RUNS_ROOT>/r6_a4_census_r6a4/r6_a4_census_<key>_r<repeat>/
含 manifest.json（命令、二进制 SHA、HEAD、PID/PGID、起止时间、exit_code）
与 run.out/run.err + gem5 原生证据；批次级 summary.json / summary.md。

并发上限 2（用户工作令）；单趟超时默认 900 s，>5 min 的批次自动后台运行
本工具即可（工具本身不 tail -f）。

用法：
  python3 tools/lsu_repeat_census.py --verify            # 全量 15 键
  python3 tools/lsu_repeat_census.py --keys A05-d-W3 --verify
"""
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
REPO = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import lsu_campaign as LC  # noqa: E402

# 证据根（不是 worktree 的 runs/）
RUNS_ROOT = Path(os.environ.get("LSU_RUNS_ROOT",
                                "/home/sdc/gem5-fi-ding/runs/lsu"))
BATCH_DIRNAME = "r6_a4_census_r6a4"
FROZEN_SHA = os.environ.get(
    "LSU_FROZEN_SHA",
    "c52ef2257bb9dad6ddf593a1dbca51d5096e52ac790ec901c46ebf9c7114c71e")

# chaos_lsu_trigger.hh intervalEvents()
TIER_INTERVAL = {"F1": 1000000, "F2": 100000, "F3": 10000, "F4": 100000}
# 用户工作令：R 覆盖 1.2 × 三个 seed 首火位的最大值
COVER = 1.2
SEEDS = (1, 2, 3)

# 判定阈值（自定并记录）：repeat=10 的 delta 与 repeat=5 的 delta 之差
# 超过 max(2.0, 2% * delta5) 视为不稳定 -> 取两者较小 delta（更保守的大 R）。
DELTA_STABLE_ABS = 2.0
DELTA_STABLE_REL = 0.02

# [census-only measurement knob] 当 F2 首火位落在流内部（gap_bfs：seed1 的
# 106412 < 未注入流 264751）时，repeat=1 的 eligible 会被注入改变执行路径后
# 的截断流污染（实测 A01-F2-W9 r1：eligible=106414，而未注入流是 264751）。
# E1/delta 必须是**未注入**流，所以若普通测量里出现过 injected>0，就用同一
# tier/同一 seed/同一 repeat 再测一遍，仅把 warmup 抬高到永远不会触发
# （tier/interval/LCG 序列不变，只是不 fire）。真实样本仍用 warmup=0。
NO_FIRE_WARMUP = 10_000_000

LCG_MUL = 6364136223846793005
LCG_ADD = 1442695040888963407
_U64 = (1 << 64) - 1


# --------------------------------------------------------------------- LCG
def lcg(x):
    """chaosSampleLCG(x) —— 与 chaos_event_sample.hh:49 逐位一致。"""
    return (int(x) * LCG_MUL + LCG_ADD) & _U64


def first_fire(tier, seed, warmup_events=0):
    """eligible 序数空间的首火位（chaos_lsu_trigger.hh scheduleNext）：
    next_fire = warmup + iv/2 + lcg(seed)%iv。"""
    if tier not in TIER_INTERVAL:
        raise ValueError("interval tier required, got %r" % (tier,))
    iv = TIER_INTERVAL[tier]
    return int(warmup_events) + iv // 2 + lcg(int(seed)) % iv


def first_fire_positions(tier, seeds=SEEDS, warmup_events=0):
    return [first_fire(tier, s, warmup_events) for s in seeds]


def max_first_fire(tier, seeds=SEEDS, warmup_events=0):
    return max(first_fire_positions(tier, seeds, warmup_events))


# ------------------------------------------------------------------ 解析
_TRIGGER_RE = re.compile(
    r"^CHAOS_LSU_TRIGGER: injector=(\S+) tier=(\S+) attempted=(\d+) "
    r"eligible=(\d+) injected=(\d+)", re.M)
_FUNNEL_RE = re.compile(
    r"FUNNEL: attempted=(\d+) eligible=(\d+) injected=(\d+)")
_ITER_RE = re.compile(r"^ITER:\d+:[0-9a-f]{16}\s*$", re.M)


def parse_trigger_summary(text):
    """最后一个 CHAOS_LSU_TRIGGER teardown 行 -> dict（None = 缺行）。"""
    ms = list(_TRIGGER_RE.finditer(text or ""))
    if not ms:
        return None
    m = ms[-1]
    return {"injector": m.group(1), "tier": m.group(2),
            "attempted": int(m.group(3)), "eligible": int(m.group(4)),
            "injected": int(m.group(5))}


def parse_funnel(text):
    """最后一个 FUNNEL 行 -> (attempted, eligible, injected)（None = 缺行）。"""
    ms = _FUNNEL_RE.findall(text or "")
    if not ms:
        return None
    return tuple(int(x) for x in ms[-1])


def count_iter_lines(text):
    return len(_ITER_RE.findall(text or ""))


# ------------------------------------------------------------------ 公式
def compute_repeat(E1, delta, max_ff, cover=COVER):
    """R = max(1, 1 + ceil((cover*max_ff - E1)/delta))。

    delta <= 0 means the eligible stream does not grow with repeat — the
    linear model is invalid; refuse loudly instead of dividing by zero or
    inventing a factor.
    """
    if delta is None or float(delta) <= 0:
        raise ValueError("delta must be > 0 (eligible stream does not grow "
                         "with repeat): %r" % (delta,))
    need = float(cover) * float(max_ff) - float(E1)
    if need <= 0:
        return 1
    return 1 + int(math.ceil(need / float(delta)))


# ---------------------------------------------------------------- 键定义
def _k(key, runid, model, workload, binary, seed):
    return {"key": key, "runid": runid, "model": model,
            "workload": workload, "binary": binary, "seed": int(seed),
            "submodel": LC.submodel_for(model, seed)}


# 用户工作令 §5 必测键（A01/A02 的 F2-agu 已有合格样本，不重测）。
CENSUS_KEYS = [
    _k("A04-a-W3", "A04-F2-W3", "A04", "AGU-AddrModes", "agu_addrmodes", 1),
    _k("A04-a-W0", "A04-F2-W0", "A04", "MiniCheck", "mini_check", 1),
    _k("A04-b-W3", "A04-F2-W3", "A04", "AGU-AddrModes", "agu_addrmodes", 2),
    _k("A04-b-W0", "A04-F2-W0", "A04", "MiniCheck", "mini_check", 2),
    _k("A05-d-W3", "A05-F2-W3", "A05", "AGU-AddrModes", "agu_addrmodes", 1),
    _k("A06-a-W3", "A06-F2-W3", "A06", "AGU-AddrModes", "agu_addrmodes", 1),
    _k("A06-a-W5", "A06-F2-W5", "A06", "SQ-Forward", "sq_forward", 1),
    _k("A06-b-W3", "A06-F2-W3", "A06", "AGU-AddrModes", "agu_addrmodes", 2),
    _k("A06-b-W5", "A06-F2-W5", "A06", "SQ-Forward", "sq_forward", 2),
    _k("A08-a-W3", "A08-F2-W3", "A08", "AGU-AddrModes", "agu_addrmodes", 1),
    _k("A08-a-W5", "A08-F2-W5", "A08", "SQ-Forward", "sq_forward", 1),
    _k("A08-b-W3", "A08-F2-W3", "A08", "AGU-AddrModes", "agu_addrmodes", 2),
    _k("A08-b-W5", "A08-F2-W5", "A08", "SQ-Forward", "sq_forward", 2),
    _k("A01-F2-W9", "A01-F2-W9", "A01", "GAP/Graph500", "gap_bfs", 1),
    _k("A02-F2-W9", "A02-F2-W9", "A02", "GAP/Graph500", "gap_bfs", 1),
]
KEYS_BY_ID = {k["key"]: k for k in CENSUS_KEYS}


def default_outroot():
    return Path(os.environ.get("LSU_CENSUS_OUTROOT", RUNS_ROOT / BATCH_DIRNAME))


def load_census_summary(outroot=None):
    p = Path(outroot or default_outroot()) / "summary.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


# ------------------------------------------------------------- 命令构造
class CensusBlocked(RuntimeError):
    pass


def config_proxy(outroot):
    """The lsu_proxy.py that MATCHES the frozen binary.

    多 session 并发工作在同一 worktree：configs/se/lsu_proxy.py 可能已被
    后续 lane 改成"未来重建后才成立"的形态（实测 2026-10-28：measureEligible
    参数 + repeat cap 131072 先于重建落地，冻结二进制加载即 AttributeError）。
    census 必须与**冻结二进制**同源，所以默认把 HEAD 版本 pin 到 census 目录，
    并响亮拒绝任何带 measureEligible 的 config（那需要重建的新二进制）。
    """
    env = os.environ.get("LSU_PROXY_CONFIG")
    if env:
        p = Path(env)
    else:
        h = os.environ.get("LSU_PIN_HEAD", "HEAD")
        dst = Path(outroot) / "pinned_configs" / "lsu_proxy.py"
        r = subprocess.run(["git", "-C", str(REPO), "show",
                            "%s:configs/se/lsu_proxy.py" % h],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise SystemExit("[census] cannot pin %s:configs/se/lsu_proxy.py: "
                             "%s" % (h, r.stderr.strip()))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(r.stdout)
        p = dst
    text = p.read_text(errors="replace")
    if "measureEligible" in text:
        raise SystemExit(
            "[census] REFUSED: %s uses measureEligible, which the frozen "
            "binary does not have (config/binary mismatch; that config needs "
            "the R6-A4 rebuild). Pin an older config with LSU_PROXY_CONFIG."
            % p)
    return p


def workload_bin(rec, outroot):
    """Pin the workload ELF so 'same workload' survives concurrent rebuilds.

    多 session 并发：workloads/directed/* 可能在 census 中途被重新编译（实测
    2026-10-28 23:33）。把当次 ELF 复制进 census 目录并只用这份副本，manifest
    记录 sha —— 否则"同一 workload"只是口头承诺。
    """
    src = LC.wl_binary_path(rec["binary"])
    dst = Path(outroot) / "pinned_workloads" / rec["binary"]
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        dst.chmod(0o755)
    return dst


def census_config_with_cap(outroot, cap):
    """HEAD-pinned lsu_proxy.py with ONLY the repeat validation ceiling raised.

    repeat>4096（A08-a 实测需要 15,706 / 84,418）会被 HEAD config 的
    p.error 拒绝；把 cap 抬到实测上限即可发命令，trigger/seed/propagation
    路径逐字节不变（冻结二进制不读这个数字，它只做 argparse 校验）。
    """
    base = config_proxy(outroot)
    text = base.read_text()
    for a, b in (("chaos_repeat > 4096", "chaos_repeat > %d" % cap),
                 ("must be in 1..4096", "must be in 1..%d" % cap)):
        if a in text:
            text = text.replace(a, b)
    dst = Path(outroot) / "pinned_configs" / ("lsu_proxy_cap%d.py" % cap)
    dst.write_text(text)
    return dst


def gem5_bin():
    env = os.environ.get("LSU_GEM5_BIN")
    if env:
        return Path(env)
    p = REPO / "CHAOS/gem5/build/ARM/gem5.opt"
    if p.exists():
        return p
    return Path(LC.resolve_g5())


def sha256_of(path, _cache={}):
    path = str(path)
    if path not in _cache:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        _cache[path] = h.hexdigest()
    return _cache[path]


def head_rev():
    try:
        return subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                              capture_output=True, text=True,
                              timeout=20).stdout.strip()
    except Exception:
        return ""


def cell_for(rec):
    """矩阵行形状的 cell（COL_RUNID/COL_MODEL/COL_UNIT/COL_FREQ/COL_WORKLOAD）。"""
    cell = [""] * 12
    cell[LC.COL_RUNID] = rec["runid"]
    cell[LC.COL_MODEL] = rec["model"]
    cell[LC.COL_UNIT] = "AGU"
    cell[LC.COL_FREQ] = "F2"
    cell[LC.COL_WORKLOAD] = rec["workload"]
    return cell


def build_command(rec, repeat, outdir, no_fire=False, config=None):
    """严格复用 campaign 的命令构造：resolve_cell + apply_seed_variant_flags
    + 同一 seed 旗标 / propagation 旗标。只把 repeat 作为显式 override。

    no_fire=True 是 census 专用的**未注入流测量**：仅把 warmup 抬高到永不
    触发，tier/interval/seed/LCG 序列逐字节不变（见 NO_FIRE_WARMUP 注释）。
    config = 与冻结二进制同源的 lsu_proxy.py（默认 HEAD pin，见 config_proxy）。
    """
    flags, golden, binary = LC.resolve_cell(
        cell_for(rec), seed=rec["seed"], repeat_override=int(repeat))
    if flags is None:
        raise CensusBlocked(golden)
    flags = LC.apply_seed_variant_flags(rec["model"], "F2", rec["seed"],
                                        binary, flags)
    if no_fire:
        i = flags.index("--addrpath_warmup_events")
        flags[i + 1] = str(NO_FIRE_WARMUP)
    family = LC.MODEL_FLAGS[rec["model"]][0]
    cmd = [str(gem5_bin()), "--outdir", str(outdir),
           str(config or LC.LSU_PROXY)]
    cmd += flags
    cmd += [LC.FAMILY_SEED[family], str(rec["seed"])]
    cmd += LC.propagation_flags(rec["runid"], rec["seed"])
    return cmd, golden, binary


def _iso():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def run_key_once(key, repeat, outroot=None, timeout=900, no_fire=False,
                 config=None):
    """真实跑一趟 (key, repeat)，落盘 manifest.json / run.out / run.err。

    返回记录 dict（含 trigger/funnel/campaign/秒数/iter_count/binary_sha256）。
    """
    rec = KEYS_BY_ID[key]
    outroot = Path(outroot or default_outroot())
    outroot.mkdir(parents=True, exist_ok=True)
    slug = "%s_r%d%s" % (key, int(repeat), "_nofire" if no_fire else "")
    outdir = outroot / ("r6_a4_census_%s" % slug)
    outdir.mkdir(parents=True, exist_ok=True)

    cfg = Path(config) if config else config_proxy(outroot)
    cmd, golden, binary = build_command(rec, repeat, outdir,
                                        no_fire=no_fire, config=cfg)
    # pin the workload ELF (concurrent rebuilds must not change the stream)
    wl = workload_bin(rec, outroot)
    i = cmd.index("--cmd")
    cmd[i + 1] = str(wl)
    g5 = gem5_bin()
    g5_sha = sha256_of(g5)
    if g5_sha != FROZEN_SHA:
        raise SystemExit(
            "[census] REFUSED: gem5 binary %s sha256=%s != frozen %s — the "
            "census must run on the same binary as the campaign (no rebuild "
            "in this lane)" % (g5, g5_sha, FROZEN_SHA))

    start, t0 = _iso(), time.time()
    r = LC.run_gem5(cmd, timeout, outdir / "run.out", outdir / "run.err",
                    sigint_grace=LC.FS_SIGINT_GRACE)
    seconds = round(time.time() - t0, 3)
    end = _iso()
    out_text = (outdir / "run.out").read_text(errors="replace")
    err_text = (outdir / "run.err").read_text(errors="replace")
    trig = parse_trigger_summary(out_text)
    ilog = outdir / "addrpath_injections.log"
    funnel = parse_funnel(ilog.read_text(errors="replace")
                          if ilog.exists() else "")
    # [R6-A4] classify even on a non-zero exit: an injected address fault can
    # make the GUEST segfault (real case: gap_bfs F2 -> chaos_guest_segv,
    # gem5 rc=1 AFTER the teardown line). Dropping the classifier there would
    # hide the campaign's Crash verdict and its injection count.
    campaign = LC.classify_run(outdir, outdir / "run.out", golden,
                               r["exit_code"], outdir / "run.err")
    iters = count_iter_lines(out_text)

    manifest = {
        "key": key, "runid": rec["runid"], "model": rec["model"],
        "submodel": rec["submodel"], "seed": rec["seed"],
        "workload": rec["workload"], "binary": binary, "repeat": int(repeat),
        "workload_path": str(wl), "workload_sha256": sha256_of(wl),
        "no_fire_warmup": NO_FIRE_WARMUP if no_fire else None,
        "cmd": cmd, "binary_path": str(g5), "binary_sha256": g5_sha,
        "config_proxy_path": str(cfg),
        "config_proxy_sha256": sha256_of(cfg),
        "head": head_rev(),
        "pid": r["pid"], "process_group_id": r["pid"],
        "start_time": start, "end_time": end, "seconds": seconds,
        "exit_code": r["exit_code"], "timed_out": r["timed_out"],
        "signal": r["signal"],
        "run_out": str(outdir / "run.out"),
        "trigger": trig, "funnel": funnel,
        "iter_lines": iters, "iter_expected": int(repeat) if repeat > 1 else 0,
        "campaign_outcome": campaign.get("outcome"),
        "campaign_injected": campaign.get("injected"),
    }
    (outdir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1) + "\n")
    return {"outdir": outdir, "exit_code": r["exit_code"],
            "timed_out": r["timed_out"], "signal": r["signal"],
            "seconds": seconds, "start_time": start, "end_time": end,
            "cmd": cmd, "pid": r["pid"], "binary_sha256": g5_sha,
            "trigger": trig, "funnel": funnel, "campaign": campaign,
            "iter_count": iters, "stdout": out_text, "stderr": err_text,
            "manifest": manifest}


def _eligible(run):
    return None if not run or not run.get("trigger") else \
        run["trigger"]["eligible"]


def analyse_key(rec, runs):
    """runs: {repeat: run_key_once(...) or {"blocked": reason}} -> summary."""
    out = {"key": rec["key"], "runid": rec["runid"], "model": rec["model"],
           "submodel": rec["submodel"], "seed": rec["seed"],
           "workload": rec["workload"], "binary": rec["binary"],
           "first_fire": {str(s): first_fire("F2", s) for s in SEEDS},
           "max_first_fire": max_first_fire("F2"),
           "cover_1.2max": round(COVER * max_first_fire("F2"), 1),
           "eligible": {}, "seconds": {}, "blocked": None, "R": None}
    for rep, run in sorted(runs.items()):
        if isinstance(run, dict) and run.get("blocked"):
            out["eligible"][str(rep)] = None
            if run["blocked"] == "census-blocked":
                out["blocked"] = run.get("reason") or out["blocked"]
            continue
        e = _eligible(run)
        out["eligible"][str(rep)] = e
        out["seconds"][str(rep)] = run.get("seconds")
    E1, E5, E10 = (out["eligible"].get("1"), out["eligible"].get("5"),
                   out["eligible"].get("10"))
    out["E1"] = E1
    out["eligible@5"] = E5
    if E1 is None or E5 is None:
        out["blocked"] = out["blocked"] or "no-trigger-line"
        return out
    delta5 = (E5 - E1) / 4.0
    out["delta5"] = round(delta5, 3)
    delta_used, source = delta5, "repeat=5"
    if E10 is not None:
        delta10 = (E10 - E1) / 9.0
        out["delta10"] = round(delta10, 3)
        tol = max(DELTA_STABLE_ABS, DELTA_STABLE_REL * abs(delta5))
        out["delta_stable"] = abs(delta10 - delta5) <= tol
        out["delta_tolerance"] = round(tol, 3)
        if not out["delta_stable"]:
            # 线性模型漂移：取更小 delta -> 更大的（更保守的）R
            delta_used = min(delta5, delta10)
            source = "min(repeat=5,repeat=10)"
    if delta_used <= 0:
        out["blocked"] = ("delta<=0: eligible stream does not grow with "
                          "repeat (E1=%s E5=%s)" % (E1, E5))
        return out
    out["delta"] = round(delta_used, 6)
    out["delta_source"] = source
    try:
        R = compute_repeat(E1, delta_used, out["max_first_fire"])
    except ValueError as exc:
        out["blocked"] = str(exc)
        return out
    out["R"] = R
    out["R_within_cap"] = R <= LC.REPEAT_MAX
    if not out["R_within_cap"]:
        out["blocked"] = ("repeat-factor-over-cap: R=%d > REPEAT_MAX=%d "
                          "(the frozen binary clamps at 4096 — "
                          "chaos_repeat.h CHAOS_REPEAT_MAX / lsu_proxy.py)"
                          % (R, LC.REPEAT_MAX))
    return out


def census(keys=None, repeats=(1, 5, 10), outroot=None, verify=False,
           jobs=2, timeout=900, log=print):
    outroot = Path(outroot or default_outroot())
    recs = [KEYS_BY_ID[k] for k in (keys or [k["key"] for k in CENSUS_KEYS])]
    jobs = max(1, min(2, int(jobs)))     # 用户工作令：gem5 并发 <= 2
    results = {}
    jobs_list = [(rec, int(r)) for rec in recs for r in repeats
                 if int(r) >= 1]
    log("[census] %d keys x repeats=%s, jobs=%d, outroot=%s"
        % (len(recs), list(repeats), jobs, outroot))

    def _one(rec, repeat):
        try:
            run = run_key_once(rec["key"], repeat, outroot, timeout)
            log("[census] %-12s r%-5d exit=%s eligible=%s injected=%s %.2fs"
                % (rec["key"], repeat, run["exit_code"],
                   _eligible(run),
                   run["trigger"]["injected"] if run["trigger"] else None,
                   run["seconds"]))
            return rec["key"], repeat, run
        except CensusBlocked as exc:
            log("[census] %-12s r%-5d BLOCKED: %s"
                % (rec["key"], repeat, exc))
            return rec["key"], repeat, {"blocked": "census-blocked",
                                        "reason": str(exc)}
        except Exception as exc:            # noqa: BLE001 — recorded, not hidden
            log("[census] %-12s r%-5d ERROR: %r" % (rec["key"], repeat, exc))
            return rec["key"], repeat, {"blocked": "census-error",
                                        "reason": repr(exc)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futs = [pool.submit(_one, rec, r) for rec, r in jobs_list]
        for f in concurrent.futures.as_completed(futs):
            k, rep, run = f.result()
            results.setdefault(k, {})[rep] = run

    # [未注入流] 若普通 repeat 测量里出现过 injected>0，首火已经落在流内部，
    # eligible 已被注入后的执行路径污染 —— 用 no-fire warmup 重测同一
    # repeat 集合，E1/delta 取未注入流。真实样本（verify）仍用 warmup=0。
    polluted = []
    for rec in recs:
        for rep, run in results.get(rec["key"], {}).items():
            t = (run or {}).get("trigger")
            if t and t.get("injected", 0) > 0:
                polluted.append(rec)
                break

    def _one_nofire(rec, repeat):
        try:
            run = run_key_once(rec["key"], repeat, outroot, timeout,
                               no_fire=True)
            log("[census] %-12s r%-5d NO-FIRE eligible=%s injected=%s %.2fs"
                % (rec["key"], repeat, _eligible(run),
                   run["trigger"]["injected"] if run["trigger"] else None,
                   run["seconds"]))
            return rec["key"], repeat, run
        except Exception as exc:            # noqa: BLE001
            log("[census] %-12s r%-5d NO-FIRE ERROR: %r"
                % (rec["key"], repeat, exc))
            return rec["key"], repeat, {"blocked": "census-error",
                                        "reason": repr(exc)}

    if polluted:
        log("[census] injected>0 during repeat measurement for %s -> "
            "re-measuring E1/delta on the UNINJECTED stream (warmup=%d)"
            % ([r["key"] for r in polluted], NO_FIRE_WARMUP))
        nf_jobs = [(rec, int(r)) for rec in polluted for r in repeats
                   if int(r) >= 1]
        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            futs = [pool.submit(_one_nofire, rec, r) for rec, r in nf_jobs]
            for f in concurrent.futures.as_completed(futs):
                k, rep, run = f.result()
                results.setdefault(k, {})["nf:%d" % rep] = run

    summary = {}
    for rec in recs:
        per = results.get(rec["key"], {})
        s = analyse_key(rec, {r: v for r, v in per.items()
                              if isinstance(r, int)})
        nf = {int(r.split(":")[1]): v for r, v in per.items()
              if isinstance(r, str) and r.startswith("nf:")}
        if nf:
            s["stream_mode"] = ("uninjected (census-only warmup=%d; tier/seed/"
                                "LCG unchanged)" % NO_FIRE_WARMUP)
            s["eligible_injected_runs"] = dict(s["eligible"])
            s_nf = analyse_key(rec, nf)
            for k2 in ("E1", "eligible@5", "delta5", "delta10",
                       "delta_stable", "delta_tolerance", "delta",
                       "delta_source", "R", "R_within_cap", "blocked",
                       "eligible", "seconds"):
                if k2 in s_nf:
                    s[k2] = s_nf[k2]
            s["blocked"] = s_nf.get("blocked")
        summary[rec["key"]] = s

    if verify:
        vlist = [(rec, summary[rec["key"]]["R"]) for rec in recs
                 if summary[rec["key"]].get("R")
                 and summary[rec["key"]]["R"] <= LC.REPEAT_MAX]
        log("[census] verify: %d keys at computed R (jobs=%d)"
            % (len(vlist), jobs))

        def _verify(rec, R):
            try:
                run = run_key_once(rec["key"], R, outroot, timeout)
                s = summary[rec["key"]]
                s["verify"] = {
                    "repeat": R, "seconds": run["seconds"],
                    "eligible": _eligible(run),
                    "injected": (run["trigger"] or {}).get("injected"),
                    "campaign_injected": run["campaign"].get("injected"),
                    "log_funnel": run["funnel"],
                    "iter_count": run["iter_count"],
                    "exit_code": run["exit_code"],
                    "outdir": str(run["outdir"]),
                }
                log("[census] verify %-12s R=%-5d injected=%s eligible=%s "
                    "%.2fs" % (rec["key"], R,
                               s["verify"]["injected"], s["verify"]["eligible"],
                               run["seconds"]))
                return rec["key"], s["verify"]
            except Exception as exc:        # noqa: BLE001
                summary[rec["key"]]["verify_error"] = repr(exc)
                log("[census] verify %-12s ERROR %r" % (rec["key"], exc))
                return rec["key"], None

        with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
            list(pool.map(lambda a: _verify(*a), vlist))

    outroot.mkdir(parents=True, exist_ok=True)
    (outroot / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    (outroot / "summary.md").write_text(render_summary_md(summary))
    (outroot / "batch_manifest.json").write_text(json.dumps({
        "tool": "tools/lsu_repeat_census.py", "argv": sys.argv,
        "head": head_rev(), "binary_sha256": sha256_of(gem5_bin()),
        "workloads_sha256": {
            b: sha256_of(Path(outroot) / "pinned_workloads" / b)
            for b in sorted({r["binary"] for r in recs})
            if (Path(outroot) / "pinned_workloads" / b).exists()},
        "started_at": _iso(), "outroot": str(outroot),
        "keys": [r["key"] for r in recs], "repeats": list(repeats),
        "verify": bool(verify), "jobs": jobs,
    }, ensure_ascii=False, indent=1) + "\n")
    return summary


def render_summary_md(summary):
    lines = [
        "# R6-A4 repeat census（真实 gem5；冻结二进制 c52ef225…）",
        "",
        ("首火位 = warmup(0) + 50000 + lcg(seed)%%100000；"
         "max = max(seed1,2,3) = %d；1.2×max = %.1f。"
         % (max_first_fire("F2"), COVER * max_first_fire("F2"))),
        "R = 1 + ceil((1.2*max - E1)/delta)，下限 1；delta = "
        "(E(repeat=5)-E1)/4（repeat=10 稳定性检查）。",
        "",
        "| key | model | submodel | seed | E1 | E@5 | delta | max_ff | "
        "1.2*max | R | within cap | verify injected | secs(verify) | blocked |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for key, s in summary.items():
        v = s.get("verify") or {}
        lines.append("| %s | %s | %s | %d | %s | %s | %s | %s | %.1f | %s | "
                     "%s | %s | %s | %s |" % (
                         key, s["model"], s["submodel"] or "-", s["seed"],
                         s.get("E1"), s.get("eligible@5"), s.get("delta"),
                         s.get("max_first_fire"), s.get("cover_1.2max", 0),
                         s.get("R"),
                         s.get("R_within_cap"), v.get("injected"),
                         v.get("seconds"), s.get("blocked") or "-"))
    lines += ["", "## 首火位（eligible 序数）", ""]
    for key, s in summary.items():
        lines.append("- %s: %s -> max=%d" % (
            key, ", ".join("s%s=%d" % (k, x)
                           for k, x in s["first_fire"].items()),
            s["max_first_fire"]))
        break
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="R6-A4 F2 repeat census")
    ap.add_argument("--keys", default=None,
                    help="comma list of key ids (default: all)")
    ap.add_argument("--repeats", default="1,5,10")
    ap.add_argument("--outroot", default=None)
    ap.add_argument("--verify", action="store_true",
                    help="also run at the computed R and record injected")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args(argv)
    keys = [k.strip() for k in a.keys.split(",")] if a.keys else None
    if keys:
        bad = [k for k in keys if k not in KEYS_BY_ID]
        if bad:
            ap.error("unknown key(s): %s; known: %s"
                     % (bad, sorted(KEYS_BY_ID)))
    repeats = [int(x) for x in a.repeats.split(",") if x.strip()]
    summary = census(keys=keys, repeats=repeats, outroot=a.outroot,
                     verify=a.verify, jobs=a.jobs, timeout=a.timeout)
    blocked = {k: s["blocked"] for k, s in summary.items() if s.get("blocked")}
    print("[census] summary -> %s" % (Path(a.outroot or default_outroot())
                                      / "summary.json"))
    if blocked:
        print("[census] BLOCKED keys (%d): %s" % (len(blocked), blocked))
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
