#!/usr/bin/env python3
"""lsu_unit_pilot.py — 单元级连续 pilot 引擎（P3，前三个单元 AGU/L1d-TLB/Load Queue）。

用户指令（2026-09-29 晚）的实现：
  准入（每 ITEM 独立判定，BLOCKED 不阻塞同单元其他 ITEM）：
    - 17 缺口模型（lsu_campaign.MODEL_BLOCKED）→ BLOCKED
    - DR-002 近似映射 10 模型 → BLOCKED
    - armtlb 家族（FS-only）：清单 workload 为 W1(MiBench)→DR-001；W4/W9 载体
      替换需用户批准（"不得自行替换 workload"）→ BLOCKED
    - workload 无 SE golden 二进制（W1/W11/W13 缺失；W12 近似口径待 DR）→ BLOCKED
    - 其余（SE golden 验证过的家族×负载）→ 入选
  执行（严格串行，守卫 experiment 锁，一个重任务）：
    - 每 ITEM 目标 30 个独立 activated runs；attempted runs 达 300 仍不足 → BLOCKED
    - F0 两遍法：计数 pass 每 ITEM 一次（N 与 seed 无关），30 个 sample 复用
    - 每 run 后 L5 分类（runner 同款集成）；crash_kind=simulator_assert 单列
  审计（每 ITEM）：五类 + post_activation_simulator_failure + injected_not_activated
    守恒：五类之和 + sim_failure = activated_runs；activated + not_activated = attempted

用法：
  python3 tools/lsu_unit_pilot.py --unit AGU --dry-run     # 准入判定 + unit manifest
  python3 tools/lsu_unit_pilot.py --unit AGU               # 执行（可断点续跑）
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_campaign as LC
import lsu_runner as LR

UNIT_MODELS = {"AGU": "A", "L1d-TLB": "T", "Load Queue": "L"}
APPROX_MODELS = {"A03", "S03", "S09", "C05", "C10", "P04", "P07", "P09", "T10", "O03"}
SAMPLES_TARGET = 30
ATTEMPTED_CAP = 300


def eligible(item_id, run_id, fields):
    """准入判定 → (ok, reason)。"""
    model = run_id.split("-")[0]
    if model in LC.MODEL_BLOCKED:
        return False, f"缺口模型: {LC.MODEL_BLOCKED[model]}"
    if model in APPROX_MODELS:
        return False, "DR-002 近似映射（PENDING，不得进正式统计）"
    if model not in LC.MODEL_FLAGS:
        return False, "NOT-MAPPED"
    family = LC.MODEL_FLAGS[model][0]
    if family == "armtlb":
        return False, ("FS-only 家族：清单 workload 为 W1(MiBench)→DR-001 缺失 / "
                       "W4(TLB-AliasPerm) 自设负载未建；tlb_probe 载体替换需用户批准"
                       "（'不得自行替换 workload'）")
    wl = fields.get("负载", "") + " " + fields.get("负载/oracle", "")
    for key in ("MiBench", "SPEC CPU2017", "PARSEC"):
        if key in wl:
            return False, f"DR-001 缺失 workload（{key}）"
    if "SQLite" in wl:
        return False, "W12 近似口径待 DR-002 确认"
    for key, binary in LC.WL_BINARY.items():
        if key in wl:
            if binary in LC.GOLDENS:
                return True, f"se:{binary} golden={LC.GOLDENS[binary]}"
            return False, f"workload {binary} 无 golden"
    return False, f"workload 未映射: {wl[:40]}"


def classify_run(outdir, guard_out, golden, gem5_exit):
    gtxt = Path(guard_out).read_text(errors="replace")
    r = subprocess.run(["python3", str(LR.L5), "--run-dir", str(outdir),
                        "--stdout", str(guard_out), "--stderr", str(guard_out),
                        "--golden", str(golden), "--exit", str(gem5_exit)],
                       capture_output=True, text=True)
    m = re.search(r"LSU_L5: (\{.*\})", r.stdout)
    return json.loads(m.group(1)) if m else {"error": f"cls: {r.stderr[-200:]}"}


def run_one(manifest, outdir, span):
    """单 run：守卫执行 + L5 分类。返回 (verdict, gem5_exit)。"""
    cfg, args = LR.build_guard_cmd(manifest, outdir, span=span)
    guard_out = outdir.parent / (outdir.name + "_guard.out")
    with open(guard_out, "w") as gf:
        r = subprocess.run(["python3", str(LR.GUARD), "run", "--type", "experiment",
                            "--desc", f"PILOT {manifest['run_id']} s{manifest['sample_index']}",
                            "--log", str(outdir.parent / (outdir.name + "_rsrc.log")),
                            "--interval", "60", "--max-seconds", str(manifest["timeout_seconds"]),
                            "--", str(REPO / "build/ARM/gem5.opt"),
                            "--outdir", str(outdir), cfg] + args,
                           stdout=gf, stderr=subprocess.STDOUT)
    gtxt = guard_out.read_text(errors="replace")
    ec = re.search(r'"exit_code": (-?\d+)', gtxt)
    gem5_exit = int(ec.group(1)) if ec else r.returncode
    v = classify_run(outdir, guard_out, manifest["golden"], gem5_exit)
    v["gem5_exit"] = gem5_exit
    (outdir / "l5_verdict.json").write_text(json.dumps(v, ensure_ascii=False, indent=1))
    return v, gem5_exit


def census(manifest, cnt_dir):
    """F0 计数 pass（每 ITEM 一次）。返回 N。"""
    cfg, args = LR.build_guard_cmd(manifest, cnt_dir, span=2**63 - 1)
    g_out = cnt_dir.parent / (cnt_dir.name + "_guard.out")
    with open(g_out, "w") as gf:
        subprocess.run(["python3", str(LR.GUARD), "run", "--type", "experiment",
                        "--desc", f"CENSUS {manifest['run_id']}",
                        "--log", str(cnt_dir.parent / (cnt_dir.name + "_rsrc.log")),
                        "--interval", "60", "--max-seconds", str(manifest["timeout_seconds"]),
                        "--", str(REPO / "build/ARM/gem5.opt"),
                        "--outdir", str(cnt_dir), cfg] + args,
                       stdout=gf, stderr=subprocess.STDOUT)
    n = re.search(r"CHAOS_LSU_TRIGGER: .*?eligible=(\d+)", g_out.read_text(errors="replace"))
    return int(n.group(1)) if n else 0


def audit(runs):
    """ITEM 级聚合 + 守恒。"""
    five = {"Masked": 0, "Detected/Contained": 0, "SDC": 0, "Crash": 0, "Timeout": 0}
    sim_fail = not_act = cls_fail = 0
    for v in runs:
        if v.get("error") or v.get("outcome") == "INCONCLUSIVE":
            cls_fail += 1
            continue
        if v.get("activated", 0) >= 1:
            if v.get("crash_kind") == "simulator_assert" and v["outcome"] == "Crash":
                sim_fail += 1          # 总方针：post_activation_simulator_failure 单列
            else:
                five[v["outcome"]] += 1
        else:
            not_act += 1
    act = sum(five.values()) + sim_fail
    attempted = len(runs)
    conservation = ("OK" if act + not_act + cls_fail == attempted
                    else f"VIOLATION act+na+cf={act+not_act+cls_fail} attempted={attempted}")
    return {"attempted_runs": attempted, "activated_runs": act,
            "five_class": five, "post_activation_simulator_failure": sim_fail,
            "injected_not_activated_runs": not_act, "classifier_failures": cls_fail,
            "conservation": conservation}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", required=True, choices=list(UNIT_MODELS))
    ap.add_argument("--phase", default="pilot")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    prefix = UNIT_MODELS[args.unit]
    items = []
    for item_id, run_id, fields in LR.parse_items():
        if run_id.split("-")[0].startswith(prefix):
            ok, reason = eligible(item_id, run_id, fields)
            items.append({"item": item_id, "run_id": run_id,
                          "status": "ELIGIBLE" if ok else "BLOCKED", "reason": reason})
    elig = [i for i in items if i["status"] == "ELIGIBLE"]
    print(f"[{args.unit}] ITEM 总数 {len(items)}：ELIGIBLE {len(elig)} / BLOCKED {len(items)-len(elig)}")

    udir = REPO / "runs/lsu/pilot" / args.unit.replace(" ", "_")
    udir.mkdir(parents=True, exist_ok=True)
    um = {"unit": args.unit, "phase": args.phase, "frozen": True,
          "samples_target": SAMPLES_TARGET, "attempted_cap": ATTEMPTED_CAP,
          "admission": items,
          "identity": {"git_commit": LR._sha.__self__ if False else subprocess.run(
              ["git", "-C", str(REPO), "rev-parse", "HEAD"],
              capture_output=True, text=True).stdout.strip()}}
    (udir / "unit_manifest.json").write_text(json.dumps(um, ensure_ascii=False, indent=1))
    if args.dry_run:
        for i in items:
            print(f"  {i['item']} {i['run_id']:<14} {i['status']:<10} {i['reason'][:70]}")
        return

    status_path = udir / "unit_status.json"
    status = {"unit": args.unit, "phase": args.phase, "started": time.strftime("%F %T"),
              "items": {}, "updated": time.strftime("%F %T")}
    if status_path.exists():  # 断点续跑
        status = json.loads(status_path.read_text())

    for e in elig:
        it = e["item"]
        if status["items"].get(it, {}).get("status") in ("COMPLETE", "BLOCKED"):
            continue
        runs = []
        span = None
        m0 = LR.build_manifest(it, args.phase, 0)
        if m0["frequency"] == "F0" and m0["family"] in ("addrpath", "lsqfwd", "prefetch"):
            cnt = udir / (it + "_census")
            cnt.mkdir(parents=True, exist_ok=True)
            span = census(m0, cnt)
            print(f"[{it}] F0 census N={span}")
            if span <= 0:
                status["items"][it] = {"status": "BLOCKED", "reason": "census=0（无 eligible 事件）"}
                status["updated"] = time.strftime("%F %T")
                status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1))
                continue
        for s in range(ATTEMPTED_CAP):
            if len([r for r in runs if not r.get("error")
                    and r.get("activated", 0) >= 1]) >= SAMPLES_TARGET:
                break
            m = LR.build_manifest(it, args.phase, s)
            od = udir / f"{it}_s{s}"
            od.mkdir(parents=True, exist_ok=True)
            v, _ = run_one(m, od, span)
            runs.append(v)
            if s % 5 == 0 or v.get("activated", 0) >= 1:
                print(f"[{it}] s{s}: {v.get('outcome')}/{v.get('crash_kind','-')} "
                      f"act={v.get('activated')}")
        res = audit(runs)
        res.update({"status": "COMPLETE" if res["activated_runs"] >= SAMPLES_TARGET
                    else "BLOCKED",
                    "reason": ("" if res["activated_runs"] >= SAMPLES_TARGET
                               else f"attempted {res['attempted_runs']} < {SAMPLES_TARGET} activated"),
                    "runs": runs})
        status["items"][it] = {k: res[k] for k in
                               ("status", "reason", "attempted_runs", "activated_runs",
                                "five_class", "post_activation_simulator_failure",
                                "injected_not_activated_runs", "classifier_failures",
                                "conservation")}
        status["updated"] = time.strftime("%F %T")
        status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1))
        (udir / f"{it}_result.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
        print(f"[{it}] {res['status']} act={res['activated_runs']}/{res['attempted_runs']} "
              f"{res['five_class']} simfail={res['post_activation_simulator_failure']} "
              f"cons={res['conservation']}")
    print(f"[{args.unit}] 单元完成（全部 ITEM 有终态）")


if __name__ == "__main__":
    main()
