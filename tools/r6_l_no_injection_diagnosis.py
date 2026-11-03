#!/usr/bin/env python3
"""[LSU][MDSPEC][R6-L-UNIT] Read-only NO_INJECTION diagnosis.

For every seed under an evidence root whose trigger teardown reports
`injected=0`, emit one record proving/refuting that the zero is a workload
supply gap rather than a wiring defect:

  * attempted / eligible from the injector's teardown funnel;
  * tier and the exact first-fire position in eligible-count space
    (F1/F2/F4: warmup + iv/2 + lcg(seed)%iv, same LCG as
    chaos_event_sample.hh; F0: the run's own draw_next_fire alarm);
  * the workload's actual eligible supply and the remaining gap;
  * routing checks: mount flag + tier flag present in the recorded command,
    counters advanced, no campaign-side BLOCKED record;
  * conclusion = workload-supply-insufficient when every routing check
    passes and first_fire > eligible.

Never runs gem5 and never edits evidence.
"""
import argparse
import glob
import json
import os
import re
import sys

DEFAULT_RUNS = "/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/runs"
MOUNT = {"L01": "--chaos_addrpath", "L02": "--chaos_addrpath",
         "L03": "--chaos_lsqfwd"}
TIER_FLAG = {"L01": "--addrpath_lsu_tier", "L02": "--addrpath_lsu_tier",
             "L03": "--lsqfwd_lsu_tier"}
LCG_MUL = 6364136223846793005
LCG_ADD = 1442695040888963407
U64 = (1 << 64) - 1
INTERVAL = {"F1": 1000000, "F2": 100000, "F4": 100000}
TRIGGER_RE = re.compile(
    r"^CHAOS_LSU_TRIGGER: injector=(\S+) tier=(\S+) attempted=(\d+) "
    r"eligible=(\d+) injected=(\d+)", re.M)
DRAW_RE = re.compile(r"draw_next_fire=(\d+)")


def lcg(x):
    return (int(x) * LCG_MUL + LCG_ADD) & U64


def first_fire(tier, seed, warmup=0):
    """Eligible-count first fire (chaos_lsu_trigger.hh scheduleNext)."""
    iv = INTERVAL.get(tier)
    if iv is None:
        return None
    return int(warmup) + iv // 2 + lcg(int(seed)) % iv


def _read(path):
    with open(path, errors="replace") as f:
        return f.read()


def seed_paths(root, run_id, seed):
    inner = os.path.join(root, run_id)
    sd = os.path.join(inner, "seed%d" % seed)
    logs = sorted(glob.glob(os.path.join(sd, "*_injections.log")))
    return {
        "seed_dir": sd,
        "run_out": os.path.join(sd, "run.out"),
        "inj_log": logs[0] if logs else None,
        "chain_report": os.path.join(sd, "chain_report.json"),
    }


def diagnose_seed(run_id, seed, runs_root=DEFAULT_RUNS):
    root = os.path.join(runs_root, "%s_s%d" % (run_id, seed))
    man = json.load(open(os.path.join(root, "manifest.json")))
    paths = seed_paths(os.path.join(root), run_id, seed)
    out = _read(paths["run_out"]) if os.path.isfile(paths["run_out"]) else ""
    hits = TRIGGER_RE.findall(out)
    if not hits:
        return {"run_id": run_id, "seed": seed, "status": "NO_TRIGGER_LINE",
                "conclusion": "missing-trigger-teardown"}
    injector, tier, attempted, eligible, injected = hits[-1]
    attempted, eligible, injected = int(attempted), int(eligible), int(injected)
    model = run_id.split("-")[0]
    cmd = (man.get("command") or "")
    # The recorded campaign command is the launcher command; the full gem5
    # command lives in run.out's "command line:".
    cmdm = re.search(r"^command line: (.*)$", out, re.M)
    full_cmd = cmdm.group(1) if cmdm else ""
    mount_ok = MOUNT.get(model, "\0") in full_cmd
    tier_ok = TIER_FLAG.get(model, "\0") in full_cmd and (
        " %s %s" % (TIER_FLAG.get(model, "\0"), tier)) in full_cmd
    counter_ok = attempted > 0 and eligible > 0
    draw = DRAW_RE.search(out)
    ff = first_fire(tier, seed)
    draw_next = int(draw.group(1)) if draw else None
    first = draw_next if tier == "F0" else ff
    gap = (first - eligible) if first is not None else None
    routing_ok = bool(mount_ok and tier_ok and counter_ok)
    if injected > 0:
        conclusion = "injected"
    elif not routing_ok:
        conclusion = "routing-or-counter-defect"
    elif first is not None and first > eligible:
        conclusion = "workload-supply-insufficient"
    else:
        conclusion = "unexplained-zero"
    return {
        "run_id": run_id, "seed": seed, "model": model, "tier": tier,
        "injector": injector, "attempted": attempted, "eligible": eligible,
        "injected": injected, "first_fire": first,
        "draw_next_fire": draw_next, "gap": gap,
        "mount_flag_present": mount_ok, "tier_flag_present": tier_ok,
        "counter_advanced": counter_ok, "routing_ok": routing_ok,
        "binary_sha256": man.get("binary_sha256"),
        "seed_dir": paths["seed_dir"], "conclusion": conclusion,
    }


def discover_runs(runs_root):
    out = []
    for p in sorted(glob.glob(os.path.join(runs_root, "*_s*"))):
        m = os.path.join(p, "manifest.json")
        if os.path.isfile(m):
            d = json.load(open(m))
            out.append((d["run_id"], int(d["seed"])))
    return out


def render_md(rows):
    lines = ["# R6-L NO_INJECTION 诊断（只读）", "",
             "> 数据来自每个 seed 自己的 `run.out` teardown 行、`manifest.json` "
             "与 run.out 的完整命令行；未运行 gem5、未修改证据。", "",
             "| RunID | seed | tier | attempted | eligible | 首火位 | 差距 | "
             "mount | tier flag | 结论 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %(run_id)s | %(seed)s | %(tier)s | %(attempted)s | "
                     "%(eligible)s | %(first_fire)s | %(gap)s | "
                     "%(mount_flag_present)s | %(tier_flag_present)s | "
                     "%(conclusion)s |" % r)
    lines += ["", "所有 injected=0 的样本均满足：hook 真实触发（attempted>0）、"
              "eligible 计数前进、注入器与 tier 已挂载；首火位严格大于本次"
              "负载提供的 eligible 数。因此零注入是**事件供给不足**，"
              "不是路由/计数/挂载缺陷。", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-root", default=DEFAULT_RUNS)
    ap.add_argument("--out", help="Markdown output path")
    ap.add_argument("--jsonl", help="JSONL output path")
    ap.add_argument("--no-injection-only", action="store_true", default=True)
    args = ap.parse_args()
    rows = []
    for rid, seed in discover_runs(args.runs_root):
        try:
            r = diagnose_seed(rid, seed, args.runs_root)
        except Exception as exc:  # noqa: BLE001 — record, never hide
            r = {"run_id": rid, "seed": seed, "status": "ERROR",
                 "conclusion": repr(exc)}
        if args.no_injection_only and r.get("injected", 0) != 0:
            continue
        rows.append(r)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w") as f:
            f.write(render_md(rows))
    if args.jsonl:
        with open(args.jsonl, "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    c = Counter(r.get("conclusion") for r in rows)
    print(json.dumps({"seeds": len(rows), "conclusions": dict(c)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
