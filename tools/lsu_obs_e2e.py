#!/usr/bin/env python3
"""lsu_obs_e2e.py — LSU 观测链 E2E kit（OBS 计划 T5a，Subagent-C；
v2 适配 2026-10-13：observation v2 契约——顶层四状态/L3 委托
propagation_trace/L4 detector=not_present，审计器默认规则集 v2）。

阶段一验收 B/D/E/F 的选择器、watcher、机器判定与 handoff 报告：
  B 正常（no-fault golden）：golden COMPLETE + verify_complete OK +
    ctrace/msnap gz_probe 可读（截断 golden 拒收——会污染全部比对）
  D Masked/SDC：COMPLETE + L1/L2 complete + L3 complete+propagation_trace
    （v2 五层可读：activated>0 样本必须有真传播证据，prop_trace.csv.gz
    入 files）+ L5.outcome 与历史 verdict 相同（同 seed 重放确定性）+
    replay verified + 证据可读 + audit v2 PASS
  E abort Crash：COMPLETE + outcome=Crash（obs 管线真实产出，历史结局仅
    先验——跨环境同 seed 注入位点不同，2026-10-12 实证）+ L2.status ∈
    {not_observed_before_crash, complete} + 截断绝不误报 no_divergence +
    L3 complete+propagation_trace（截断 caveat 允许、path_complete 可
    false——崩溃截断语义，不降级 L3 口径）+ replay verified + audit v2
    PASS
  F 可审计性：全部样本 observation.json 可被审计器解析、audit v2 PASS
    （规则 R1：activated>0 且 L3 非 propagation_trace → 强制 FAIL，即
    audit v2 PASS 已隐含五层全过）、identity.gem5_opt_sha256 == 冻结
    sha、身份/hash 一致

子命令：
  --select [--campaign X] [--record-out PATH]
      只读扫主树 runs/lsu/pilot/AGU（优先 checklist 短流载体；备选
      runs/lsu/pilot_w1 长流），选出 1 个 Masked/SDC（activated>0，样本号
      大=最近）与 1 个 Crash/simulator_assert（activated>0）；打印
      (ITEM, s, outcome, verdict 路径, 载体) 与理由；selection.json 落
      <outdir-root>/<campaign>/（"正常"用例由 driver 的 golden ref 承担，
      无需选择）。
  --run --watch-pids P1,P2,... [--campaign X] [--poll-interval 30]
      watcher 守护：轮询 /proc（绝不 kill/信号被 watched PID）直到任一
      driver 退出 → 互锁确认 guard slots_held<4（lsu_guard import，host
      全局锁目录=主树；连续两轮确认，排除生产 driver 换样间隙的瞬时空槽）
      → subprocess 本 worktree tools/lsu_obs_driver.py（--phase screening
      --replay-policy per_sample，env LSU_GEM5_BIN/LSU_GUARD_DIR/
      PYTHONHASHSEED=0；同 ITEM 一次调用带两个 --samples，不同 ITEM 分两次）
      → 自动 --validate + --report。driver 有界重试（≤3 次，以样本 COMPLETE
      为准——GUARD_FAILURE 时 rc 仍 0；重试前经 guard clear-stale 显式处置
      上一尝试死亡 pid 的 stale claim，绝不触碰存活 claim/生产 campaign）
      → 自动 --validate + --report。watcher 自身只轮询 /proc 与锁文件，
      绝不直接起 gem5。
  --validate --campaign X [--outdir-root R] [--expect-gem5-sha H]
      B/D/E/F 逐项机器判定（退出码 0=全 PASS）。
  --self-check
      完整性检查器有效性证明：tmp 合成 v2 合规好样本（含真实 L3 传播
      trace，audit v2 干净 PASS）→ 故意篡改 files sha 与 chain_complete
      → 断言 lsu_audit 判 FAIL 且检出篡改本身（基准 v2 合规，篡改检出
      不被 R1 等规则噪声污染）。
  --report --campaign X
      写 <outdir>/<campaign>/handoff_e2e.json + .md（选择清单+证据路径、
      逐样本 verdict/L1/L2 摘要、replay 证据、B/D/E/F 判定、绝对路径、
      运行环境 hash）。

已知上游缺陷（OBS-5a 报告，主负责人修）：lsu_obs_driver.run_item 以
sample_index=0 的 manifest 跑所有样本（m0-for-all-samples）——所有样本误用
sample-0 seed。本工具不绕过不降验收：validate D 的"outcome 与历史 verdict
相同"与 audit (vi) 的 seed 重算会如实 FAIL，直到驱动修复（修复须落本
worktree 分支，watcher 在触发时刻才 subprocess 驱动文件）。
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

WT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WT / "tools"))
import lsu_audit as A          # noqa: E402  独立审计器（OBS-6a）
import lsu_obs_core as OC      # noqa: E402  verify_complete/gz_probe
import lsu_runner as LR        # noqa: E402  parse_items（清单解析，只读）
import lsu_campaign as LC      # noqa: E402  WL_BINARY/MODEL_FLAGS（映射唯一来源）

MT = Path("/home/sdc/gem5-fi-ding")
PILOT_CHECKLIST_ROOT = MT / "runs/lsu/pilot/AGU"   # checklist 短流（优先）
PILOT_W1_ROOT = MT / "runs/lsu/pilot_w1"           # w1 长流（备选）
OUTDIR_ROOT = MT / "runs/lsu/obs"                  # E2E 产物（新目录，允许写）
FROZEN_GEM5_SHA = ("10590f6295bc4dec09fc51c538dd857abaf2efb92"
                   "fb3c373422a24e1aaf1e36c")
SLOTS_TOTAL = 4                                     # guard 硬上限（用户判据）
DEFAULT_CAMPAIGN = "obs_e2e_20261012"
VERSION = "lsu_obs_e2e v2 (OBS-5a; observation v2 契约 2026-10-13)"
SAMPLE_DIR_RE = A.SAMPLE_DIR_RE


def log(msg):
    print(f"[{time.strftime('%F %T')}] {msg}", flush=True)


def _sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ================================================================ --select
def item_meta():
    """清单 ITEM → runid/family/载体二进制（映射来源 = lsu_campaign，与
    lsu_runner.build_manifest 同源；不调 build_manifest 以免逐 item 哈希
    gem5 二进制）。"""
    out = {}
    for item, run_id, fields in LR.parse_items():
        model = run_id.split("-")[0]
        fam = LC.MODEL_FLAGS.get(model, (None,))[0]
        wl_text = fields.get("负载", "") + " " + fields.get("负载/oracle", "")
        wl = next((b for k, b in LC.WL_BINARY.items() if k in wl_text), None)
        out[item] = {"runid": run_id, "family": fam, "carrier_bin": wl}
    return out


def scan_candidates():
    """只读扫描两个 pilot 根 → 候选列表（activated>0 才有观测链可验）。

    两种目录布局都支持：pilot/AGU 为扁平 <root>/ITEM-X_sN/；pilot_w1 为嵌套
    <root>/ITEM-X/ITEM-X_sN/。"""
    roots = [("checklist", PILOT_CHECKLIST_ROOT), ("w1", PILOT_W1_ROOT)]
    item_dir_re = SAMPLE_DIR_RE  # ITEM-\d+_s\d+
    cands = {"masked_sdc": [], "crash": []}
    stats = {}
    for kind, root in roots:
        n_verdict = 0
        if not root.is_dir():
            stats[str(root)] = "目录不存在（跳过）"
            continue
        sample_dirs = []
        for entry in sorted(root.iterdir()):
            if not entry.is_dir():
                continue
            if item_dir_re.match(entry.name):          # 扁平（pilot/AGU）
                sample_dirs.append(entry)
            elif re.match(r"^ITEM-\d+$", entry.name):  # 嵌套（pilot_w1）
                for sub in sorted(entry.iterdir()):
                    if sub.is_dir() and item_dir_re.match(sub.name):
                        sample_dirs.append(sub)
        for d in sample_dirs:
            m = item_dir_re.match(d.name)
            vp = d / "l5_verdict.json"
            if not vp.exists():
                continue
            try:
                v = json.loads(vp.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            n_verdict += 1
            if not (v.get("activated") or 0) > 0:
                continue
            base = {"root_kind": kind, "root": str(root), "item": m.group(1),
                    "sample": int(m.group(2)), "activated": v.get("activated"),
                    "crash_kind": v.get("crash_kind"),
                    "verdict_path": str(vp.resolve())}
            if v.get("outcome") in ("Masked", "SDC"):
                cands["masked_sdc"].append({**base, "outcome": v["outcome"]})
            elif v.get("outcome") == "Crash":
                cands["crash"].append({**base, "outcome": "Crash"})
        stats[str(root)] = (f"{kind} 根（{'嵌套' if kind == 'w1' else '扁平'}"
                            f"布局），{n_verdict} 个可读 verdict")
    return cands, stats


def select_candidates():
    """选择规则（钉死、确定性）：优先 checklist 短流载体 →（Crash 另优先
    simulator_assert）→ 样本号大=最近 → ITEM 号小。返回 (selection, stats)。"""
    cands, stats = scan_candidates()
    meta = item_meta()

    def rank(c):
        return (0 if c["root_kind"] == "checklist" else 1,
                0 if c.get("crash_kind") == "simulator_assert" else 1,
                -c["sample"], c["item"])

    def enrich(c):
        m = meta.get(c["item"], {})
        carrier = (f"se:{m['carrier_bin']}（checklist 短流）"
                   if c["root_kind"] == "checklist" and m.get("carrier_bin")
                   else "w1_all（长流 rerun 指定）" if c["root_kind"] == "w1"
                   else "unknown")
        return {**c, "runid": m.get("runid"), "family": m.get("family"),
                "carrier": carrier}

    sel = {"tool": VERSION, "selected_at": time.strftime("%F %T"),
           "scan_roots": stats, "selection_rule":
           "优先 checklist 短流载体 → (Crash 优先 simulator_assert) → "
           "样本号大=最近 → ITEM 号小；activated>0 才入选"}
    ms = sorted(cands["masked_sdc"], key=rank)
    cr = sorted(cands["crash"], key=rank)
    sel["masked_or_sdc"] = (enrich(ms[0]) | {
        "reason": f"Masked/SDC 候选 {len(ms)} 个，按规则取最优（checklist "
                  f"载体优先、样本号最大=最近）"}
    ) if ms else None
    sel["crash"] = (enrich(cr[0]) | {
        "reason": f"Crash 候选 {len(cr)} 个，按规则取最优（checklist 载体、"
                  f"simulator_assert、样本号最大=最近）"}
    ) if cr else None
    if sel["masked_or_sdc"] and sel["crash"]:
        sel["same_item"] = (sel["masked_or_sdc"]["item"]
                            == sel["crash"]["item"])
    return sel, cands


def print_selection(sel):
    for key, label in (("masked_or_sdc", "Masked/SDC（验收 D）"),
                       ("crash", "Crash/simulator_assert（验收 E）")):
        c = sel.get(key)
        if not c:
            log(f"选择失败：{label} 无候选")
            continue
        log(f"选择[{label}]: (ITEM={c['item']}, s={c['sample']}, "
            f"outcome={c['outcome']}, verdict={c['verdict_path']}, "
            f"载体={c['carrier']})")
        log(f"  理由: {c['reason']}；activated={c['activated']}, "
            f"runid={c['runid']}, family={c['family']}")
    if sel.get("masked_or_sdc") and sel.get("crash"):
        log(f"两样本 {'同 ITEM（一次 driver 调用带两个 --samples）' if sel['same_item'] else '不同 ITEM（分两次 driver 调用）'}")
    log("正常用例（验收 B）由 driver 的 no-fault golden ref 承担，无需选择")


def cmd_select(args):
    sel, _ = select_candidates()
    print_selection(sel)
    if not (sel.get("masked_or_sdc") and sel.get("crash")):
        print("ERROR: 候选不足（需至少 1 Masked/SDC 与 1 Crash）",
              file=sys.stderr)
        return 1
    out = Path(args.record_out) if args.record_out else \
        Path(args.outdir_root) / args.campaign / "selection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sel, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    log(f"selection 已冻结: {out}")
    return 0


# ================================================================ guard 互锁
def guard_slots_held():
    """host 全局锁目录（主树）experiment 槽位存活持有数（PID+pid_start 双核验）。"""
    os.environ["LSU_GUARD_DIR"] = str(MT / "runs/lsu/guard")
    import lsu_guard as G   # 模块常量在 import 时读 env
    n = 0
    for _slot, lk in G._all_slot_locks_on_disk().items():
        if lk and not lk.get("corrupt") and G._lock_live(lk):
            n += 1
    return n


# ================================================================ --run
class RunLog:
    """e2e 运行事件落盘（--report 引用；原子重写）。"""

    def __init__(self, path):
        self.path = Path(path)
        self.data = {"tool": VERSION, "campaign": None, "events": [],
                     "driver_invocations": []}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass

    def event(self, name, detail=None):
        self.data["events"].append({"time": time.strftime("%F %T"),
                                    "event": name, "detail": detail})
        self._flush()

    def invocation(self, rec):
        self.data["driver_invocations"].append(rec)
        self._flush()
        return rec   # 调用方后续 mutate（补 exit_code/ended），_flush 即时落盘

    def _flush(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        os.replace(tmp, self.path)


def driver_argv(campaign, outdir_root, item, samples):
    return [sys.executable, str(WT / "tools" / "lsu_obs_driver.py"),
            "--items", item, "--phase", "screening", "--campaign", campaign,
            "--samples", *[str(s) for s in samples],
            "--replay-policy", "per_sample", "--outdir-root", str(outdir_root)]


def wait_for_trigger(pids, interval):
    """轮询 /proc 直到任一 watched PID 消失且确有槽空（绝不信号任何 PID）。

    槽空须连续两轮确认（30s 间隔）：生产 driver 在样本间隙会瞬时释放再重取
    槽位，单轮 slots<4 可能只是换样间隙——两轮连续 <4 才是真正空槽。"""
    consecutive = 0
    while True:
        alive = [p for p in pids if Path(f"/proc/{p}").exists()]
        slots = guard_slots_held()
        if len(alive) < len(pids):
            if slots < SLOTS_TOTAL:
                consecutive += 1
                if consecutive >= 2:
                    log(f"触发：watched driver 已退出（存活 {alive}），"
                        f"slots_held={slots}<{SLOTS_TOTAL} 连续 {consecutive} "
                        f"轮确认 → 启动 E2E")
                    return
                log(f"watched driver 已退出，slots_held={slots}"
                    f"（第 {consecutive}/2 轮确认），再等一轮排除换样间隙")
            else:
                consecutive = 0
                log(f"watched driver 已退出但 slots_held={slots}≥{SLOTS_TOTAL}"
                    f"（槽未空），继续等待")
        else:
            consecutive = 0
            log(f"watch: {len(alive)}/{len(pids)} 个生产 driver 存活，"
                f"slots_held={slots}")
        time.sleep(interval)


def _samples_complete(outdir_root, campaign, sel):
    """两个选中样本是否都已 COMPLETE（driver rc=0 不代表完成——
    GUARD_FAILURE 时 run_item 返回状态串、进程仍退 0，必须查 COMPLETE）。"""
    for key in ("masked_or_sdc", "crash"):
        c = sel.get(key) or {}
        d = (Path(outdir_root) / campaign / c.get("item", "NONE")
             / f"{c.get('item', 'NONE')}_s{c.get('sample', -1)}")
        if not (d / OC.COMPLETE).exists():
            return False, d
    return True, None


def run_driver(campaign, outdir_root, sel, runlog, attempts=3):
    """执行 E2E driver，有界重试（无人值守鲁棒性）：
    * 换样间隙竞态 → 首个 guard run acquire 拒绝 → GUARD_FAILURE（rc 仍 0）
      → 以样本 COMPLETE 为准判定成败，未完成则重试（driver 对 COMPLETE
      样本只读核验跳过，重试幂等）；
    * 重试前处置上一尝试死亡 driver 遗留的 stale claim（仅清 confirm-dead-pid
      匹配且确死的 claim；guard clear-stale 拒绝一切存活 claim，生产 campaign
      不受影响）。"""
    ms, cr = sel["masked_or_sdc"], sel["crash"]
    env = {**os.environ,
           "LSU_GEM5_BIN": str(MT / "build/ARM/gem5.opt"),
           "LSU_GUARD_DIR": str(MT / "runs/lsu/guard"),
           "PYTHONHASHSEED": "0"}
    if sel.get("same_item"):
        plans = [([ms["item"]], [ms["sample"], cr["sample"]])]
    else:
        plans = [([ms["item"]], [ms["sample"]]), ([cr["item"]], [cr["sample"]])]
    rc_all = 0
    for items, samples in plans:
        argv = driver_argv(campaign, outdir_root, items[0], samples)
        for attempt in range(1, attempts + 1):
            log(f"driver 启动（尝试 {attempt}/{attempts}）: {' '.join(argv)}")
            rec = runlog.invocation({"argv": argv, "attempt": attempt,
                                     "started": time.strftime("%F %T")})
            t0 = time.time()
            proc = subprocess.Popen(argv, cwd=str(WT), env=env)
            rec["driver_pid"] = proc.pid
            rc = proc.wait()
            rec.update({"exit_code": rc, "driver_pid": proc.pid,
                        "ended": time.strftime("%F %T"),
                        "elapsed_s": round(time.time() - t0, 1)})
            runlog._flush()
            done, missing = _samples_complete(outdir_root, campaign, sel)
            log(f"driver 退出 code={rc}；样本 COMPLETE={done}"
                f"{'' if done else f'（缺 {missing}）'}")
            if done:
                break
            if attempt < attempts:
                # 处置本尝试死亡 driver 的 stale claim（guard 拒绝存活 claim）
                r = subprocess.run(
                    [sys.executable, str(WT / "tools/lsu_guard.py"),
                     "clear-stale", "--type", "claim",
                     "--confirm-dead-pid", str(proc.pid)],
                    capture_output=True, text=True, env=env, cwd=str(WT))
                log(f"stale-claim 处置（dead pid={proc.pid}）: "
                    f"{(r.stdout + r.stderr).strip()[:200]}")
                log("等待 120s 后重试（避开换样间隙/gate 瞬态）")
                time.sleep(120)
            else:
                rc_all |= 1
    return rc_all


def cmd_run(args):
    outdir_root = Path(args.outdir_root)
    camp_dir = outdir_root / args.campaign
    camp_dir.mkdir(parents=True, exist_ok=True)
    runlog = RunLog(camp_dir / "e2e_run_log.json")
    runlog.data["campaign"] = args.campaign
    runlog.event("watcher-start",
                 f"watch_pids={args.watch_pids} poll={args.poll_interval}s")
    pids = [int(x) for x in args.watch_pids.split(",") if x.strip()]
    if not pids:
        print("ERROR: --watch-pids 为空", file=sys.stderr)
        return 2

    # selection：优先读已冻结的 selection.json（选择时刻钉死），缺失则现选
    sel_path = camp_dir / "selection.json"
    if sel_path.exists():
        sel = json.loads(sel_path.read_text(encoding="utf-8"))
        log(f"selection 载入（已冻结）: {sel_path}")
    else:
        log("selection.json 缺失 → 现场选择并冻结")
        sel, _ = select_candidates()
        print_selection(sel)
        if not (sel.get("masked_or_sdc") and sel.get("crash")):
            runlog.event("select-failed", "候选不足，watcher 退出")
            return 1
        sel_path.write_text(json.dumps(sel, ensure_ascii=False, indent=1)
                            + "\n", encoding="utf-8")

    wait_for_trigger(pids, args.poll_interval)
    runlog.event("trigger-fired", "driver 退出且槽空，启动 E2E driver")
    rc = run_driver(args.campaign, outdir_root, sel, runlog)
    runlog.event("driver-done", f"driver rc={rc}")
    v = validate_and_print(args.campaign, outdir_root,
                           args.expect_gem5_sha, sel)
    report(args.campaign, outdir_root, args.expect_gem5_sha, sel)
    runlog.event("e2e-complete", f"validate={'PASS' if v else 'FAIL'}")
    return 0 if v else 1


# ================================================================ --validate
def _load_sample(camp, cand):
    if not cand:
        return None, "selection 缺该候选"
    d = camp / cand["item"] / f"{cand['item']}_s{cand['sample']}"
    if not (d / OC.COMPLETE).exists():
        return None, f"无 COMPLETE 标记: {d}"
    try:
        obs = json.loads((d / "observation.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return None, f"observation.json 不可解析: {e} ({d})"
    return (d, obs), None


def _fault_probe_path(d, obs, lv):
    """L1/L2 fault 轨迹定位（含 .staging 残留名的 basename 回退，同审计器）。"""
    probe = (obs.get(lv) or {}).get("fault") or {}
    p = probe.get("path")
    if not p:
        return None
    fp = Path(p)
    if not fp.is_absolute():
        fp = Path(d) / fp
    if not fp.exists():
        cand = Path(d) / Path(p).name
        if cand.exists():
            return cand
    return fp if fp.exists() else None


def validate_campaign(campaign, outdir_root, expect_gem5_sha, selection):
    """B/D/E/F 机器判定。返回 (lines, all_pass)。"""
    outdir_root = Path(outdir_root)
    camp = outdir_root / campaign
    lines = []

    def add(cls, ok, detail):
        lines.append({"class": cls, "pass": bool(ok), "detail": detail})

    ms, ms_err = _load_sample(camp, (selection or {}).get("masked_or_sdc"))
    cr, cr_err = _load_sample(camp, (selection or {}).get("crash"))
    audit = {}
    for key, pair in (("masked_or_sdc", ms), ("crash", cr)):
        if pair:
            audit[key] = A.audit_sample_dir(pair[0])

    # ---- B：正常（no-fault golden）
    b_ok, b_detail = True, []
    gkey = None
    for pair in (ms, cr):
        if pair:
            gkey = (pair[1].get("identity") or {}).get("baseline_key")
            break
    if gkey is None:
        b_ok = False
        b_detail.append(f"无样本可定位 baseline_key（{ms_err}; {cr_err}）")
    else:
        gdir = outdir_root / "golden" / gkey
        ok, reason = OC.verify_complete(
            gdir, {"gem5_opt_sha256": expect_gem5_sha, "baseline_key": gkey})
        if not ok:
            b_ok = False
            b_detail.append(f"verify_complete: {reason}")
        rg = A.audit_golden_dir(gdir, expect_gem5_sha=expect_gem5_sha)
        if rg["audit"] != "PASS":
            b_ok = False
            b_detail.append(f"golden 审计: {rg['reasons']}")
        else:
            b_detail.append(f"golden={gdir}")
    add("B", b_ok, "; ".join(b_detail) if b_ok else "FAIL: " + "; ".join(b_detail))

    # ---- D：Masked/SDC 样本
    d_ok, d_detail = True, []
    if ms is None:
        d_ok = False
        d_detail.append(f"样本缺失/不可读: {ms_err}")
    else:
        d, obs = ms
        ident = obs.get("identity") or {}
        l1s = (obs.get("L1") or {}).get("status")
        l2s = (obs.get("L2") or {}).get("status")
        if l1s != "complete" or l2s != "complete":
            d_ok = False
            d_detail.append(f"L1.status={l1s} L2.status={l2s}（均须 complete）")
        hist = ((selection or {}).get("masked_or_sdc") or {}).get("outcome")
        outcome = (obs.get("L5") or {}).get("outcome")
        if outcome != hist or outcome not in ("Masked", "SDC"):
            d_ok = False
            d_detail.append(f"L5.outcome={outcome} != 历史 verdict {hist}"
                            f"（同 seed 重放确定性不成立）")
        rd = obs.get("replay_determinism") or {}
        if not rd.get("verified"):
            d_ok = False
            d_detail.append(f"replay_determinism.verified={rd.get('verified')}")
        # L3（v2 五层可读）：真实传播证据——status=complete 且
        # method=propagation_trace（unsupported/proxy 不算数，R1 对偶的
        # kit 侧显式断言），prop_trace.csv.gz 须入 files（sha 由审计全量复核）
        l3 = obs.get("L3") or {}
        if l3.get("status") != "complete" \
                or l3.get("method") != "propagation_trace":
            d_ok = False
            d_detail.append(
                f"L3 status={l3.get('status')!r} method="
                f"{l3.get('method')!r}（v2 五层可读须 L3 complete + "
                f"propagation_trace——activated>0 样本必须有真传播证据）")
        if not any(f.get("name") == "prop_trace.csv.gz"
                   for f in obs.get("files") or []):
            d_ok = False
            d_detail.append("files 无 prop_trace.csv.gz（L3 传播证据文件缺失）")
        # 证据可读：fault ctrace+msnap + commit_diff + micro_diff + L5 文件
        for lv, nm in (("L1", "msnap"), ("L2", "ctrace")):
            if _fault_probe_path(d, obs, lv) is None:
                d_ok = False
                d_detail.append(f"{lv} fault {nm} 轨迹缺失/不可定位")
        if (obs.get("L1") or {}).get("micro_diff") is None:
            d_ok = False
            d_detail.append("L1.micro_diff 缺失")
        if (obs.get("L2") or {}).get("commit_diff") is None:
            d_ok = False
            d_detail.append("L2.commit_diff 缺失")
        if not any(f.get("name") == "l5_verdict.json"
                   for f in obs.get("files") or []):
            d_ok = False
            d_detail.append("files 无 l5_verdict.json（L5 证据缺失）")
        if audit.get("masked_or_sdc", {}).get("audit") != "PASS":
            d_ok = False
            d_detail.append(f"audit FAIL: "
                            f"{audit.get('masked_or_sdc', {}).get('reasons')}")
        if ident.get("gem5_opt_sha256") != expect_gem5_sha:
            d_ok = False
            d_detail.append(f"identity.gem5_opt_sha256="
                            f"{ident.get('gem5_opt_sha256')} != 冻结 sha")
        if d_ok:
            d_detail = [f"样本={d} outcome={outcome} L1=complete "
                        f"L2=complete L3=complete(propagation_trace) "
                        f"replay=verified"]
    add("D", d_ok, "; ".join(d_detail) if d_ok else "FAIL: " + "; ".join(d_detail))

    # ---- E：abort Crash 样本
    e_ok, e_detail = True, []
    if cr is None:
        e_ok = False
        e_detail.append(f"样本缺失/不可读: {cr_err}")
    else:
        d, obs = cr
        ident = obs.get("identity") or {}
        l2 = obs.get("L2") or {}
        outcome = (obs.get("L5") or {}).get("outcome")
        hist = ((selection or {}).get("crash") or {}).get("outcome")
        if outcome != "Crash":
            e_ok = False
            e_detail.append(
                f"L5.outcome={outcome}（须经 obs 管线真实产出 Crash。历史 "
                f"verdict {hist} 仅作候选先验——2026-10-12 实证：历史批次"
                f"（PYTHONHASHSEED 未固定、无 ctrace 对象）与 obs 管线"
                f"（PYTHONHASHSEED=0 + ctrace/msnap）同 seed 注入位点不同，"
                f"跨环境结局不可复现；确定论以管线内 replay 为准）")
        elif hist and outcome != hist:
            e_detail.append(f"finding: 历史 {hist} vs obs 环境 {outcome}"
                            f"（跨环境 RNG 流分歧，管线内 replay 为准）")
        if l2.get("status") not in ("not_observed_before_crash", "complete"):
            e_ok = False
            e_detail.append(f"L2.status={l2.get('status')}（须 "
                            f"not_observed_before_crash/complete）")
        # L3（v2）：crash 样本同样须真实传播证据（R1 对偶的 kit 侧显式
        # 断言）；截断 caveat 允许、path_complete 可 false——崩溃截断语义
        # （abort 前缀打捞的诚实证据），但不降级 L3 口径
        l3 = obs.get("L3") or {}
        if l3.get("status") != "complete" \
                or l3.get("method") != "propagation_trace":
            e_ok = False
            e_detail.append(
                f"L3 status={l3.get('status')!r} method="
                f"{l3.get('method')!r}（v2：crash 样本也须 complete + "
                f"propagation_trace；截断 caveat 允许——崩溃截断语义不"
                f"降级 L3 口径）")
        # 截断诚实性：fault trace 截断 → 必须标注 truncated 且绝不 no_divergence
        fp = _fault_probe_path(d, obs, "L2")
        if fp is not None:
            rp = OC.gz_probe(fp)
            if rp["truncated"]:
                stored = (l2.get("fault") or {}).get("truncated")
                if stored is not True:
                    e_ok = False
                    e_detail.append("fault ctrace 实测截断但 probe 未标 "
                                    "truncated=true")
                cd = l2.get("commit_diff") or {}
                if cd.get("verdict") == "no_divergence":
                    e_ok = False
                    e_detail.append(
                        "截断 fault trace 被记为 no_divergence（严重诚实性"
                        "违规——必须 truncated_no_divergence_in_prefix / "
                        "diverged / not_observed_before_crash）")
        if (obs.get("replay_determinism") or {}).get("verified") is not True:
            e_ok = False
            e_detail.append("replay_determinism.verified != true")
        if audit.get("crash", {}).get("audit") != "PASS":
            e_ok = False
            e_detail.append(f"audit FAIL: "
                            f"{audit.get('crash', {}).get('reasons')}")
        if ident.get("gem5_opt_sha256") != expect_gem5_sha:
            e_ok = False
            e_detail.append("identity.gem5_opt_sha256 != 冻结 sha")
        if e_ok:
            e_detail = [f"样本={d} L2.status={l2.get('status')} "
                        f"commit_diff.verdict="
                        f"{(l2.get('commit_diff') or {}).get('verdict')} "
                        f"L3=propagation_trace(path_complete="
                        f"{((l3.get('evidence') or {}).get('path_complete'))}"
                        f") replay=verified"]
    add("E", e_ok, "; ".join(e_detail) if e_ok else "FAIL: " + "; ".join(e_detail))

    # ---- F：可审计性（全部样本 + golden：解析/audit/身份 sha 一致）
    f_ok, f_detail = True, []
    for key, pair, err in (("masked_or_sdc", ms, ms_err), ("crash", cr, cr_err)):
        if pair is None:
            f_ok = False
            f_detail.append(f"{key}: {err}")
            continue
        if audit.get(key, {}).get("audit") != "PASS":
            f_ok = False
            f_detail.append(f"{key} audit FAIL: "
                            f"{audit[key].get('reasons')}")
        if (pair[1].get("identity") or {}).get("gem5_opt_sha256") \
                != expect_gem5_sha:
            f_ok = False
            f_detail.append(f"{key} identity.gem5_opt_sha256 != 冻结 sha")
    if gkey is not None:
        rg = A.audit_golden_dir(outdir_root / "golden" / gkey,
                                expect_gem5_sha=expect_gem5_sha)
        if rg["audit"] != "PASS":
            f_ok = False
            f_detail.append(f"golden audit FAIL: {rg['reasons']}")
    if f_ok:
        f_detail = [f"全部样本 audit v2 PASS（五层全过：activated>0 → L3 "
                    f"须 propagation_trace），identity/hash 一致 "
                    f"(gem5_opt_sha256={expect_gem5_sha[:16]}...)"]
    add("F", f_ok, "; ".join(f_detail) if f_ok else "FAIL: " + "; ".join(f_detail))

    return lines, all(l["pass"] for l in lines)


def validate_and_print(campaign, outdir_root, expect_gem5_sha, selection):
    lines, ok = validate_campaign(campaign, outdir_root, expect_gem5_sha,
                                  selection)
    for l in lines:
        log(f"验收 {l['class']}: {'PASS' if l['pass'] else 'FAIL'} — "
            f"{l['detail']}")
    log(f"验收 B/D/E/F 总判定: {'PASS' if ok else 'FAIL'}")
    return ok


def load_selection(campaign, outdir_root):
    p = Path(outdir_root) / campaign / "selection.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
    return None


def _apply_crash_override(args, sel):
    """--crash-sample ITEM:sNNN：主负责人覆盖 crash 候选（v2 语义）。

    2026-10-12 实证：跨环境（PYTHONHASHSEED/ctrace 对象集）同 seed 注入
    位点不同 → 历史 Crash 结局不可跨环境复现。crash 候选 = obs 环境探针
    真实产出 Crash 的样本（历史结局仅先验）；覆盖事实与理由随 selection
    记录，绝不静默。
    """
    cs = getattr(args, "crash_sample", None)
    if not cs:
        return sel
    item, _, s = cs.partition(":")
    s = s.lstrip("s")
    if not item.startswith("ITEM-") or not s.isdigit():
        raise SystemExit(f"--crash-sample 格式须为 ITEM-XXX:sNNN，得到 {cs!r}")
    sel = dict(sel or {})
    sel["crash"] = {
        "item": item, "sample": int(s), "outcome": None,
        "selection_note": ("v2 主负责人覆盖（--crash-sample）：obs 环境探针"
                           "候选；跨环境结局不可复现（同 seed 注入位点不同，"
                           "2026-10-12 实证），历史结局仅先验，确定论以管线"
                           "内 replay 为准"),
    }
    return sel


def cmd_validate(args):
    sel = load_selection(args.campaign, args.outdir_root)
    if sel is None:
        print(f"ERROR: {Path(args.outdir_root) / args.campaign / 'selection.json'}"
              f" 缺失（先 --select）", file=sys.stderr)
        return 2
    sel = _apply_crash_override(args, sel)
    return 0 if validate_and_print(args.campaign, args.outdir_root,
                                   args.expect_gem5_sha, sel) else 1


# ================================================================ --report
def _sample_summary(camp, cand):
    pair, err = _load_sample(camp, cand)
    if pair is None:
        return {"error": err}
    d, obs = pair
    l2cd = (obs.get("L2") or {}).get("commit_diff") or {}
    l3 = obs.get("L3") or {}
    rd = obs.get("replay_determinism") or {}
    return {
        "sample_dir": str(d.resolve()),
        "outcome": (obs.get("L5") or {}).get("outcome"),
        "crash_kind": (obs.get("L5") or {}).get("crash_kind"),
        "activated": (obs.get("L0") or {}).get("activated"),
        "L1_status": (obs.get("L1") or {}).get("status"),
        "L2_status": (obs.get("L2") or {}).get("status"),
        "commit_diff_verdict": l2cd.get("verdict"),
        "commit_diff_first_errant_seq": (l2cd.get("first_errant_commit")
                                         or {}).get("seq"),
        "L3_status": l3.get("status"),
        "L3_method": l3.get("method"),
        "L3_path_complete": (l3.get("evidence") or {}).get("path_complete"),
        "L3_truncated": l3.get("truncated"),
        "chain_complete": obs.get("chain_complete"),
        "chain_status_reason": obs.get("chain_status_reason"),
        "replay_verified": rd.get("verified"),
        "replay_evidence": rd.get("evidence"),
        "violations": obs.get("violations"),
        "identity": obs.get("identity"),
    }


def report(campaign, outdir_root, expect_gem5_sha, selection=None):
    outdir_root = Path(outdir_root)
    camp = outdir_root / campaign
    sel = selection or load_selection(campaign, outdir_root)
    lines, ok = validate_campaign(campaign, outdir_root, expect_gem5_sha, sel)
    runlog = {}
    rl_path = camp / "e2e_run_log.json"
    if rl_path.exists():
        try:
            runlog = json.loads(rl_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            runlog = {"error": "e2e_run_log.json 不可读"}
    doc = {
        "tool": VERSION, "campaign": campaign,
        "generated_at": time.strftime("%F %T"),
        "environment": {
            "gem5_opt": str(MT / "build/ARM/gem5.opt"),
            "gem5_opt_sha256": _sha256_file(MT / "build/ARM/gem5.opt"),
            "expect_gem5_sha256": expect_gem5_sha,
            "gem5_sha_matches_frozen":
                _sha256_file(MT / "build/ARM/gem5.opt") == expect_gem5_sha,
            "lsu_proxy_sha256": _sha256_file(WT / "configs/se/lsu_proxy.py"),
            "worktree": str(WT),
            "worktree_git_commit": subprocess.run(
                ["git", "-C", str(WT), "rev-parse", "HEAD"],
                capture_output=True, text=True).stdout.strip(),
            "outdir_root": str(outdir_root),
        },
        "selection": sel,
        "driver_invocations": runlog.get("driver_invocations", []),
        "run_events": runlog.get("events", []),
        "samples": {
            "masked_or_sdc": _sample_summary(camp, (sel or {}).get("masked_or_sdc")),
            "crash": _sample_summary(camp, (sel or {}).get("crash")),
        },
        "acceptance_BDEF": lines,
        "acceptance_all_pass": ok,
    }
    # v2：完整链计数（样本 observation 顶层 chain_complete 直读；不可读
    # 样本不计入任一侧，由 acceptance B/D/E/F 的 FAIL 诚实暴露）
    chain_vals = [s.get("chain_complete") for s in doc["samples"].values()
                  if "error" not in s]
    doc["chain_complete_count"] = sum(1 for v in chain_vals if v is True)
    doc["chain_incomplete_count"] = sum(1 for v in chain_vals if v is False)
    camp.mkdir(parents=True, exist_ok=True)
    (camp / "handoff_e2e.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    md = [f"# LSU 观测链 E2E handoff — {campaign}",
          f"* 生成: {doc['generated_at']}（{VERSION}）",
          f"* worktree: `{WT}` @ `{doc['environment']['worktree_git_commit']}`",
          f"* gem5: `{doc['environment']['gem5_opt']}` "
          f"sha256=`{doc['environment']['gem5_opt_sha256'][:16]}...` "
          f"冻结件匹配={doc['environment']['gem5_sha_matches_frozen']}", ""]
    md += ["## 样本选择", ""]
    for key, label in (("masked_or_sdc", "Masked/SDC（验收 D）"),
                       ("crash", "Crash/simulator_assert（验收 E）")):
        c = (sel or {}).get(key)
        md.append(f"- **{label}**: " + (
            f"`{c['item']}` s{c['sample']} outcome={c.get('outcome')} "
            f"activated={c.get('activated')}；verdict=`{c.get('verdict_path')}`；"
            f"载体={c.get('carrier')}；理由: {c.get('reason', '—')}"
            + (f"；注: {c['selection_note']}" if c.get("selection_note") else "")
            if c else "（缺失）"))
    md.append("- **正常（验收 B）**: driver no-fault golden ref（自动先跑）")
    md += ["", "## 逐样本摘要", ""]
    for key, s in doc["samples"].items():
        md.append(f"### {key}")
        if "error" in s:
            md.append(f"- 不可读: {s['error']}")
        else:
            md += [f"- 目录: `{s['sample_dir']}`",
                   f"- L5: outcome={s['outcome']} crash_kind={s['crash_kind']} "
                   f"activated={s['activated']}",
                   f"- L1: {s['L1_status']}；L2: {s['L2_status']}"
                   f"（commit_diff={s['commit_diff_verdict']}, "
                   f"first_errant_seq={s['commit_diff_first_errant_seq']}）",
                   f"- L3: {s['L3_status']}"
                   f"（method={s['L3_method']}, "
                   f"path_complete={s['L3_path_complete']}, "
                   f"truncated={s['L3_truncated']}）",
                   f"- chain_complete={s['chain_complete']}"
                   f"（{s['chain_status_reason']}）",
                   f"- replay verified={s['replay_verified']} "
                   f"evidence={json.dumps(s['replay_evidence'], ensure_ascii=False)}"]
        md.append("")
    md += [f"chain_complete 样本计数: {doc['chain_complete_count']} complete / "
           f"{doc['chain_incomplete_count']} incomplete"
           f"（v2 顶层直读；L3 非 propagation_trace 即 incomplete）", ""]
    md += ["## 验收判定 B/D/E/F", ""]
    for l in lines:
        md.append(f"- **{l['class']}**: {'**PASS**' if l['pass'] else '**FAIL**'}"
                  f" — {l['detail']}")
    md += ["", f"**总判定: {'PASS' if ok else 'FAIL'}**", "",
           f"## driver 调用", ""]
    for inv in doc["driver_invocations"]:
        md.append(f"- `{' '.join(inv['argv'])}` → exit={inv.get('exit_code')}"
                  f"（{inv.get('started')}→{inv.get('ended', inv.get('started'))}）")
    if not doc["driver_invocations"]:
        md.append("- （无——driver 未运行或 run log 缺失）")
    md.append("")
    (camp / "handoff_e2e.md").write_text("\n".join(md), encoding="utf-8")
    log(f"handoff 已写: {camp / 'handoff_e2e.json'} 与 "
        f"{camp / 'handoff_e2e.md'}")
    return doc


def cmd_report(args):
    sel = _apply_crash_override(
        args, load_selection(args.campaign, args.outdir_root))
    report(args.campaign, args.outdir_root, args.expect_gem5_sha,
           selection=sel)
    return 0


# ================================================================ --self-check
# v2 合成 prop_trace 夹具（与 tests/test_lsu_l3_propagation.py 的 FULL_CHAIN
# 同款，逐列对齐 CHAOSPropagation.cc writeNode 契约：十进制数值列、无值列=
# 空串、addr=无前缀小写 hex、detail='k=v;k=v' 无逗号）。
_PROP_HEADER = ("# lsu-propagation v1: node_id,tick,ptag,kind,dyn_inst_seq,"
                "request_id,addr,phys_reg,arch_reg,detail\n")
_PROP_FULL_CHAIN = _PROP_HEADER + (
    "0,123450,1,inj,77,,1a2b3000,,,"
    "site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=8;"
    "new_size=8;old_addr=1a2b3000;new_addr=1a2b3008\n"
    "1,123450,1,addr_form,77,,1a2b3008,,,"
    "site=lsq_pushRequest_PRE;old_addr=1a2b3000;new_addr=1a2b3008\n"
    "2,124000,1,mem_req,77,77,1a2b3008,,,"
    "site=lsq_sendFragmentToTranslation;family=addrpath;size=8\n"
    "3,130000,1,resp,77,77,1a2b3008,,,"
    "family=addrpath;size=8;data_fnv=0123456789abcdef\n"
    "4,130001,1,taint_reg,77,77,1a2b3008,42,5,class=int;dest_idx=0\n"
    "5,140000,1,consumer,90,,,42,5,class=int;src_idx=1;pc=8f00\n"
    "6,140000,1,errant_commit,90,,,,,trigger=first_consumer;pc=8f00\n"
    "7,150000,0,funnel,,,,,,"
    "site=CHAOSAddrPath;attempted=12;eligible=5;injected=1\n"
)
# crash 截断件：链止于 consumer（无 errant_commit 尾节点 → path_complete=
# false），且以无 gzip trailer 的 Z_SYNC_FLUSH 前缀落盘（abort 真形态）
_PROP_CRASH_PREFIX = _PROP_HEADER + (
    "0,123450,1,inj,77,,1a2b3000,,,"
    "site=lsq_pushRequest_PRE;family=addrpath;is_load=1;old_size=8;"
    "new_size=8;old_addr=1a2b3000;new_addr=1a2b3008\n"
    "1,123450,1,addr_form,77,,1a2b3008,,,"
    "site=lsq_pushRequest_PRE;old_addr=1a2b3000;new_addr=1a2b3008\n"
    "2,124000,1,mem_req,77,77,1a2b3008,,,"
    "site=lsq_sendFragmentToTranslation;family=addrpath;size=8\n"
    "3,130000,1,resp,77,77,1a2b3008,,,"
    "family=addrpath;size=8;data_fnv=0123456789abcdef\n"
    "4,130001,1,taint_reg,77,77,1a2b3008,42,5,class=int;dest_idx=0\n"
    "5,140000,1,consumer,90,,,42,5,class=int;src_idx=1;pc=8f00\n"
)


def _sc_write_prop_trace(path, text, truncated_prefix=False):
    """写合成 prop_trace.csv.gz（prop_trace.csv.gz v1 契约）。

    truncated_prefix=True → 无 gzip trailer 的 Z_SYNC_FLUSH 前缀
    （CHAOSPropagation abort 时的真实形态：每节点 flush、abort 后无
    trailer——解析器截断打捞契约的输入侧，同 L3 测试 write_gz）。"""
    import zlib
    if not truncated_prefix:
        import gzip
        with gzip.open(path, "wt", encoding="utf-8") as f:
            f.write(text)
    else:
        co = zlib.compressobj(9, zlib.DEFLATED, 31)  # wbits=31: gzip 头
        Path(path).write_bytes(
            co.compress(text.encode("utf-8"))
            + co.flush(zlib.Z_SYNC_FLUSH))            # 无 trailer


def _sc_build_sample(parent, item, s, l5, *, crash_truncated=False):
    """self-check/测试共用的最小合成 COMPLETE 样本（full 模式，v2 契约）。

    v2（2026-10-13 适配）：样本经 OC.build_l3(prop_trace_path=...) 委托
    lsu_l3_propagation 产出真实 L3，OC.build_observation(prop_trace_path=)
    产出顶层 v2 字段（schema=lsu-observation-v2、chain_complete 四状态）。
    masked/SDC（crash_truncated=False）= 完整传播链（errant_commit 尾节点
    在 → path_complete=true）；crash = 截断前缀（无 errant_commit 尾节点 →
    path_complete=false + 截断 caveat，仍 complete/propagation_trace——
    崩溃截断语义，绝不冒充 no_divergence，也不降级 L3 口径）。"""
    import gzip
    import micro_diff
    staging = parent / f"{item}_s{s}.staging"
    staging.mkdir(parents=True, exist_ok=True)
    ref_lines = [f"{i},0,{100 + i},400080,add,1,1,5,66,"
                 f"0000000000000001" for i in range(12)]
    big = [f"{i},0,{100 + i},400080,add,1,1,5,66,"
           f"0000000000000001" for i in range(300)]

    def wctr(path, lines):
        with gzip.open(path, "wt") as f:
            for l in lines:
                f.write(l + "\n")

    ctr_ref = parent / "sc_ref_ctr.csv.gz"
    msn_ref = parent / "sc_ref_msn.csv.gz"
    wctr(ctr_ref, ref_lines if not crash_truncated else big)
    rows = [micro_diff._synth_row(i, (i + 1) * 1000, 1000 + i * 500)
            for i in range(6)]
    micro_diff._write_snap(str(msn_ref), rows)
    wctr(staging / "commit_trace.csv.gz", ref_lines)
    if crash_truncated:  # 截断 fault ctrace（真实 abort 形态）
        wctr(staging / "commit_trace.csv.gz", big)
        blob = (staging / "commit_trace.csv.gz").read_bytes()
        (staging / "commit_trace.csv.gz").write_bytes(
            blob[:int(len(blob) * 0.6)])
    # v2 L3 证据：prop_trace.csv.gz（完整链 / crash 截断前缀）
    _sc_write_prop_trace(staging / "prop_trace.csv.gz",
                         _PROP_FULL_CHAIN if not crash_truncated
                         else _PROP_CRASH_PREFIX,
                         truncated_prefix=crash_truncated)
    micro_diff._write_snap(str(staging / "micro_snap.csv.gz"), rows)
    inj = ("Tick: 887040, Site: lsq_sendFragmentToTranslation, "
           "mode=low_bit_flip, old_vaddr=0x7ffffefd00, "
           "new_vaddr=0x87ffffefd00, faults_injected: 1")
    (staging / "addrpath_injections.log").write_text(inj + "\n")
    (staging / "gem5.out").write_text(
        "CHAOS_LSU_TRIGGER: freq-based attempted=1 eligible=265143 "
        "injected=1 activated=1\n")
    (staging / "l5_verdict.json").write_text(
        json.dumps(l5, ensure_ascii=False, indent=1))
    from lsu_seed import lsu_seed
    l0 = OC.parse_l0((staging / "gem5.out").read_text(), inj + "\n")
    l1 = OC.build_l1(msn_ref, staging / "micro_snap.csv.gz")
    l2 = OC.build_l2(ctr_ref, staging / "commit_trace.csv.gz", l5=l5)
    # 真实 L3：委托 lsu_l3_propagation（同 driver post_process 接线路径）
    l3 = OC.build_l3("addrpath", l2,
                     prop_trace_path=staging / "prop_trace.csv.gz")
    l4 = OC.build_l4(l0, l1, l2, l5,
                     fault_msnap_path=staging / "micro_snap.csv.gz")
    ident = {"campaign": "selfcheck", "item": item, "runid": "A01-F0-W9",
             "sample": f"s{s}", "seed": lsu_seed("A01-F0-W9", "screening", s),
             "phase": "screening", "git_commit": "a" * 40,
             "gem5_opt_sha256": "b" * 64, "lsu_proxy_sha256": "c" * 64,
             "workload": "se:gap_bfs", "workload_sha256": "d" * 64,
             "config_family": "C4-LSU", "pythonhashseed": 0,
             "baseline_key": "e" * 32, "obs_mode": "full",
             "coverage_scope": "full_run", "prop_traced": True}
    files = [{"name": n, "path": n, "sha256": OC.sha256_file(staging / n),
              "bytes": (staging / n).stat().st_size}
             for n in ("addrpath_injections.log", "prop_trace.csv.gz",
                       "commit_trace.csv.gz", "micro_snap.csv.gz",
                       "gem5.out", "l5_verdict.json")]
    obs = OC.build_observation(ident, l0, l1, l2, l3, l4, l5,
                               {"policy": "per_sample", "verified": True,
                                "evidence": {}}, files,
                               prop_trace_path=staging / "prop_trace.csv.gz")
    (staging / "observation.json").write_text(
        json.dumps(obs, ensure_ascii=False, indent=1))
    final = parent / f"{item}_s{s}"
    OC.finalize_sample(staging, final)
    return final


def _sc_build_golden(parent, key, gem5_sha):
    """self-check/测试共用：no_fault_golden 目录（COMPLETE 协议）。"""
    import gzip
    staging = Path(str(parent / key) + ".staging")
    staging.mkdir(parents=True, exist_ok=True)
    with gzip.open(staging / "commit_trace.csv.gz", "wt") as f:
        for i in range(12):
            f.write(f"{i},0,{100 + i},400080,add,1,1,5,66,"
                    f"0000000000000001\n")
    import micro_diff
    micro_diff._write_snap(
        str(staging / "micro_snap.csv.gz"),
        [micro_diff._synth_row(i, (i + 1) * 1000, 1000 + i * 500)
         for i in range(6)])
    (staging / "gem5.out").write_text("no-fault golden\n")
    files = [{"name": n, "path": n, "sha256": OC.sha256_file(staging / n),
              "bytes": (staging / n).stat().st_size}
             for n in ("commit_trace.csv.gz", "micro_snap.csv.gz", "gem5.out")]
    obs = {"schema": OC.SCHEMA,
           "identity": {"gem5_opt_sha256": gem5_sha, "baseline_key": key,
                        "kind": "no_fault_golden", "campaign": "selfcheck"},
           "files": files, "violations": [], "degradations": []}
    (staging / "observation.json").write_text(
        json.dumps(obs, ensure_ascii=False, indent=1))
    gdir = parent / key
    OC.finalize_sample(staging, gdir)
    return gdir


def cmd_self_check(args):
    """完整性检查器有效性证明（v2）：基准样本 v2 合规（含真实 L3 传播
    trace）→ audit v2 干净 PASS；篡改 files sha + chain_complete → 审计器
    必 FAIL 且检出篡改本身（基准无 R1 噪声——L3 已是 propagation_trace）。"""
    tmp = Path(tempfile.mkdtemp(prefix="lsu_e2e_selfcheck_"))
    print(f"self-check 工作区: {tmp}")
    l5 = {"outcome": "SDC", "activated": 1, "injected": 1,
          "crash_kind": None, "detected_na": True, "checksum": "x",
          "classes": {}, "conservation": "OK"}
    good = _sc_build_sample(tmp, "ITEM-990", 3, l5)
    bad = _sc_build_sample(tmp, "ITEM-990", 4, l5)
    # 篡改 1：证据文件内容（sha 失配）
    with open(bad / "gem5.out", "a") as f:
        f.write("TAMPERED\n")
    # 篡改 2：chain_complete 存储值翻转 + 同步修复 COMPLETE 标记 sha
    obs = json.loads((bad / "observation.json").read_text())
    obs["chain_complete"] = not obs["chain_complete"]
    (bad / "observation.json").write_text(
        json.dumps(obs, ensure_ascii=False, indent=1))
    comp = json.loads((bad / "COMPLETE").read_text())
    comp["observation_sha256"] = OC.sha256_file(bad / "observation.json")
    (bad / "COMPLETE").write_text(json.dumps(comp, indent=1) + "\n")

    a_good = A.audit_sample_dir(good)
    a_bad = A.audit_sample_dir(bad)
    ok = True
    for name, cond, detail in (
            ("good_sample_passes_audit", a_good["audit"] == "PASS",
             str(a_good)),
            ("tampered_sample_fails_audit", a_bad["audit"] == "FAIL",
             str(a_bad)),
            ("sha_tamper_detected",
             any("sha_mismatch" in x for x in a_bad["reasons"]),
             str(a_bad["reasons"])),
            ("chain_tamper_detected",
             any("chain_complete_recompute_mismatch" in x
                 for x in a_bad["reasons"]), str(a_bad["reasons"]))):
        print(("PASS" if cond else "FAIL"), name, "" if cond else f"<- {detail}")
        ok = ok and cond
    print(f"SELF-CHECK: {'PASS' if ok else 'FAIL'}"
          f"（完整性检查器有效性{'已证明' if ok else '未证明'}）")
    return 0 if ok else 1


# ================================================================ CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse
                                 .RawDescriptionHelpFormatter)
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--self-check", dest="self_check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--campaign", default=DEFAULT_CAMPAIGN)
    ap.add_argument("--watch-pids", default=None,
                    help="逗号分隔的生产 driver PID（只轮询，绝不信号）")
    ap.add_argument("--poll-interval", type=int, default=30)
    ap.add_argument("--outdir-root", default=str(OUTDIR_ROOT))
    ap.add_argument("--record-out", default=None,
                    help="--select 的 selection.json 输出路径覆盖（测试用）")
    ap.add_argument("--crash-sample", dest="crash_sample", default=None,
                    help="ITEM-XXX:sNNN 覆盖 crash 候选（v2：obs 环境探针"
                         "产物；历史结局仅先验——跨环境不可复现）")
    ap.add_argument("--expect-gem5-sha", dest="expect_gem5_sha",
                    default=FROZEN_GEM5_SHA)
    args = ap.parse_args()
    n = sum(bool(x) for x in (args.select, args.run, args.validate,
                              args.self_check, args.report))
    if n != 1:
        ap.error("必须且只选一个子命令（--select/--run/--validate/"
                 "--self-check/--report）")
    if args.run and not args.watch_pids:
        ap.error("--run 需要 --watch-pids P1,P2,...")
    if args.select:
        return cmd_select(args)
    if args.run:
        return cmd_run(args)
    if args.validate:
        return cmd_validate(args)
    if args.self_check:
        return cmd_self_check(args)
    return cmd_report(args)


if __name__ == "__main__":
    sys.exit(main())
