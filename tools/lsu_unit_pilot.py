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
  执行（F-022 升级 2026-09-30：--workers N 样本级并行，默认 1 = 原串行行为；
  每个样本独立守卫槽位/manifest/seed/输出目录；census 串行先行并持久化）：
    - 每 ITEM 目标 30 个独立 activated runs；attempted runs 达 300 仍不足 → BLOCKED
    - F0 两遍法：计数 pass 每 ITEM 一次（N 与 seed 无关，census_n 持久化到
      unit_status，断点续跑复用），30 个 sample 复用
    - 样本级 resume：s=0 起连续有效样本（l5_verdict.json 无 error 且配对
      guard.out 含 run-finish）直接复用，断点后重跑（幂等 seed）
    - 每 run 后 L5 分类（runner 同款集成）；crash_kind=simulator_assert 单列
  审计（每 ITEM）：五类 + post_activation_simulator_failure + injected_not_activated
    守恒：五类之和 + sim_failure = activated_runs；activated + not_activated = attempted

  F-023 加固（2026-09-30）：guard 周期未完成（acquire 拒绝/脚本损坏/无 run-finish 标记）
  → GuardFailure 异常，该 run 不记账；ITEM 记 GUARD_FAILURE（非终态）并中止本单元——
  守卫基础设施失败是系统性的，继续只会空转产生伪样本（2026-09-30 14:37–15:26
  约 2,670 个空转 run 被误记为 attempted 的事故教训，见 findings.md F-023）。

用法：
  python3 tools/lsu_unit_pilot.py --unit AGU --dry-run     # 准入判定 + unit manifest
  python3 tools/lsu_unit_pilot.py --unit AGU               # 执行（可断点续跑）
  python3 tools/lsu_unit_pilot.py --unit AGU --workers 4   # F-022 并发上限 4
"""
import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))  # tools/（lsu_campaign/lsu_runner 等共享模块）
sys.path.insert(0, str(_HERE))         # 本目录（draft/ 隔离副本或 tools/ 正式位）
import lsu_campaign as LC
import lsu_runner as LR

# 引擎绑定同目录守卫（tools/ 下即 tools/lsu_guard.py；draft/ 隔离测试时即
# draft/lsu_guard.py + LSU_GUARD_DIR 环境变量——F-022 切换流程）
LR.GUARD = _HERE / "lsu_guard.py"

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


class GuardFailure(RuntimeError):
    """守卫未完成 run 周期（F-023）：acquire 拒绝 / 守卫脚本损坏 / 无 run-finish 标记。

    guard_out 无 '"action": "run-finish"' 即 gem5 从未在守卫管辖下执行完一个周期，
    该 run 不产生任何实验数据——绝不作为样本记账。
    """


def _guard_fail(gtxt, guard_out):
    if "ACQUIRE REFUSED" in gtxt:
        hint = "acquire refused (stale lock or slots full) — run lsu_guard.py clear-stale"
    elif "SyntaxError" in gtxt or "Traceback" in gtxt:
        hint = "guard script itself errored (editing guard.py while wave runs?)"
    else:
        hint = "no run-finish marker in guard output"
    return GuardFailure(f"{hint}; guard_out={guard_out}; tail={gtxt[-200:]!r}")


def run_one(manifest, outdir, span):
    """单 run：守卫执行 + L5 分类。返回 (verdict, gem5_exit)。

    F-023 加固：guard_out 必须含 run-finish 标记，否则抛 GuardFailure（不记账）。
    """
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
    if '"action": "run-finish"' not in gtxt or ec is None:
        raise _guard_fail(gtxt, guard_out)
    gem5_exit = int(ec.group(1))
    v = classify_run(outdir, guard_out, manifest["golden"], gem5_exit)
    v["gem5_exit"] = gem5_exit
    (outdir / "l5_verdict.json").write_text(json.dumps(v, ensure_ascii=False, indent=1))
    return v, gem5_exit


def census(manifest, cnt_dir):
    """F0 计数 pass（每 ITEM 一次）。返回 N。

    F-023 加固：guard 周期未完成或无 eligible 行 → GuardFailure；
    不得把基础设施失败误判为"census=0（无 eligible 事件）"。
    """
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
    gtxt = g_out.read_text(errors="replace")
    if '"action": "run-finish"' not in gtxt:
        raise _guard_fail(gtxt, g_out)
    n = re.search(r"CHAOS_LSU_TRIGGER: .*?eligible=(\d+)", gtxt)
    if n is None:
        raise GuardFailure(f"census cycle finished but no CHAOS_LSU_TRIGGER eligible line "
                           f"(injector logging broken?); guard_out={g_out}")
    return int(n.group(1))


def _valid_resumed(udir, it, s):
    """样本级 resume（F-022）：返回样本 s 的有效 verdict 或 None。

    有效 = l5_verdict.json 存在且无 error，且配对 _guard.out 含 run-finish
    （F-023 类空转残留无 run-finish，不复活）。seed 由 (ITEM, phase, s) 决定，
    复用等价于幂等重跑。
    """
    od = udir / f"{it}_s{s}"
    vj, go = od / "l5_verdict.json", udir / f"{it}_s{s}_guard.out"
    if not vj.exists() or not go.exists():
        return None
    if '"action": "run-finish"' not in go.read_text(errors="replace"):
        return None
    try:
        v = json.loads(vj.read_text())
    except json.JSONDecodeError:
        return None
    return None if v.get("error") else v


def _activated_count(runs):
    return len([r for r in runs if not r.get("error") and r.get("activated", 0) >= 1])


def run_item_samples(it, args, udir, span, status, status_path):
    """单个 ITEM 的样本执行（F-022：--workers N 并行 + 样本级 resume）。

    返回 runs 列表；守卫基础设施失败抛 GuardFailure（由调用方处置）。
    """
    runs = []
    # 样本级 resume：s=0 起连续有效前缀复用
    s_next = 0
    while True:
        v = _valid_resumed(udir, it, s_next)
        if v is None:
            break
        runs.append(v)
        s_next += 1
    if runs:
        print(f"[{it}] resume: {len(runs)} valid samples reused, next s={s_next}")
    if args.workers <= 1:
        for s in range(s_next, ATTEMPTED_CAP):
            if _activated_count(runs) >= SAMPLES_TARGET:
                break
            m = LR.build_manifest(it, args.phase, s)
            od = udir / f"{it}_s{s}"
            od.mkdir(parents=True, exist_ok=True)
            v, _ = run_one(m, od, span)
            runs.append(v)
            if s % 5 == 0 or v.get("activated", 0) >= 1:
                print(f"[{it}] s{s}: {v.get('outcome')}/{v.get('crash_kind','-')} "
                      f"act={v.get('activated')}")
        return runs
    guard_failure = None
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures, s = {}, s_next
        while True:
            # 派发：activated 达标或 attempted（含在飞）达上限即停
            while (guard_failure is None
                   and len(futures) < args.workers
                   and _activated_count(runs) < SAMPLES_TARGET
                   and len(runs) + len(futures) < ATTEMPTED_CAP):
                m = LR.build_manifest(it, args.phase, s)
                od = udir / f"{it}_s{s}"
                od.mkdir(parents=True, exist_ok=True)
                futures[ex.submit(run_one, m, od, span)] = s
                s += 1
            if not futures:
                break
            done, _ = wait(set(futures), return_when=FIRST_COMPLETED)
            for f in done:
                sn = futures.pop(f)
                try:
                    v, _ = f.result()
                except GuardFailure as gf:
                    # 停止派发；在飞样本由 executor 退出时等待完成——其 verdict
                    # 有效落盘，断点续跑时经 resume 复活，不浪费
                    guard_failure = gf
                    print(f"[{it}] s{sn}: GUARD_FAILURE {gf}"[:200])
                    continue
                runs.append(v)
                if sn % 5 == 0 or v.get("activated", 0) >= 1:
                    print(f"[{it}] s{sn}: {v.get('outcome')}/{v.get('crash_kind','-')} "
                          f"act={v.get('activated')}")
            if guard_failure is not None:
                break
    if guard_failure is not None:
        raise guard_failure
    return runs


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
    ap.add_argument("--workers", type=int, default=1,
                    help="样本级并行数（F-022 上限 4；默认 1 = 原串行行为）")
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
    um = {"unit": args.unit, "phase": args.phase, "frozen": True, "workers": args.workers,
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
    else:
        # 0-eligible 单元（如 L1d-TLB）也要有终态文件（F-018 附带修复：
        # 此前仅在 ITEM 循环内写，0 eligible 时 unit_status.json 永不生成）
        status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1))

    for e in elig:
        it = e["item"]
        if status["items"].get(it, {}).get("status") in ("COMPLETE", "BLOCKED"):
            continue
        # SystemExit 防护（F-018）：准入判定与 build_manifest 之间若出现
        # 分歧（如 workload 匹配边界），单 ITEM 记 BLOCKED 继续本单元，
        # 不得让 sys.exit 杀死整个 unit_pilot（2026-09-29 AGU 1/31 中断教训）。
        try:
            m0 = LR.build_manifest(it, args.phase, 0)
        except SystemExit as ex:
            status["items"][it] = {"status": "BLOCKED",
                                   "reason": f"build_manifest exit: {ex}"}
            status["updated"] = time.strftime("%F %T")
            status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1))
            print(f"[{it}] BLOCKED (build_manifest): {ex}")
            continue
        # GuardFailure 防护（F-023）：守卫基础设施失败（stale 锁/脚本损坏/无
        # run-finish）是系统性的——该 run 不记账，ITEM 记 GUARD_FAILURE（非
        # 终态，断点续跑自动重试），并立即中止本单元防止空转伪样本。
        try:
            span = None
            if m0["frequency"] == "F0" and m0["family"] in ("addrpath", "lsqfwd", "prefetch"):
                # census 持久化（F-022）：断点续跑复用（N 与 seed 无关——F-013）
                prev_n = status["items"].get(it, {}).get("census_n")
                if prev_n:
                    span = prev_n
                    print(f"[{it}] F0 census N={span} (persisted)")
                else:
                    cnt = udir / (it + "_census")
                    cnt.mkdir(parents=True, exist_ok=True)
                    span = census(m0, cnt)
                    print(f"[{it}] F0 census N={span}")
                    status["items"][it] = {"status": "IN_PROGRESS", "census_n": span}
                    status["updated"] = time.strftime("%F %T")
                    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1))
                if span <= 0:
                    status["items"][it] = {"status": "BLOCKED", "reason": "census=0（无 eligible 事件）"}
                    status["updated"] = time.strftime("%F %T")
                    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1))
                    continue
            runs = run_item_samples(it, args, udir, span, status, status_path)
        except GuardFailure as gf:
            status["items"][it] = {"status": "GUARD_FAILURE",
                                   "reason": f"infra: {gf}"[:500]}
            status["updated"] = time.strftime("%F %T")
            status_path.write_text(json.dumps(status, ensure_ascii=False, indent=1))
            print(f"[{it}] GUARD_FAILURE: {gf}")
            print(f"[{args.unit}] UNIT ABORTED (guard infrastructure failure, F-023 "
                  f"fail-fast; diagnose + clear-stale/fix, then resume)")
            return
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
