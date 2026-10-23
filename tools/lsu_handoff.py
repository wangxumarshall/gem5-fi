#!/usr/bin/env python3
"""lsu_handoff.py — 链路台账 ledger + campaign handoff 生成器（OBS T6；纠偏轮 v2，中央指令 2026-10-13）。

用户指令 2026-10-12 + 纠偏 2026-10-13：
  * 既有结果只标记"结局完成、完整链待补跑"——本工具 --ledger 只读扫描，
    不写任何既有样本目录、不碰 Excel；台账落 runs/lsu/obs/（--out-dir 可
    覆盖为 tmp 干跑目录，绝不误写主树真实 ledger）。
  * 台账术语 v2：每行含 execution_complete / chain_complete=false /
    missing_levels / needs_chain_backfill（保留 outcome 字段与
    evidence_root；AGU 批次属 outcome-only——campaign 执行完成 ≠
    chain_complete，L1-L4 完整链待补跑）。
  * 每个 campaign 输出 handoff.json + handoff.md（第四节全字段：RunID、
    代码/二进制/config/workload hashes、seed 与尝试数、九分类计数与守恒、
    完整链数量/缺失层级、证据索引、首次分歧/传播摘要、重试、资源峰值、
    wall time、绝对路径、Git 提交）。campaign 聚合 v2：execution/
    evidence/chain 三计数分开（chain_incomplete_count 单列待补跑，不入
    完整完成数）。

用法：
  python3 tools/lsu_handoff.py --ledger --campaign p4_agu_formal_20261012 \
      [--freeze docs/gem5-fi/lsu/evidence/P4/p4_freeze_agu_formal_20261012.json] \
      [--out-dir <tmp 干跑目录>]
  python3 tools/lsu_handoff.py --campaign-handoff runs/lsu/obs/<campaign> \
      [--out-dir runs/lsu/obs/<campaign>]
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_obs_core as OC   # noqa: E402  missing_levels/状态字段零漂移复用
import lsu_runner as LR

OBS_ROOT = Path("/home/sdc/gem5-fi-ding/runs/lsu/obs")   # 主树观测产物根
MT = Path("/home/sdc/gem5-fi-ding")                      # 主树（runs/ 只在主树）
GEM5_FROZEN_SHA = "10590f6295bc4dec09fc51c538dd857abaf2efb92fb3c373422a24e1aaf1e36c"


# ---------------------------------------------------------------- ledger
def _item_unit_dirs(it, carrier):
    """(主 unit 目录, 载体)。checklist→pilot/AGU；w1→pilot_w1/<it>。

    runs/ 只存在于主树（worktree 是 tracked-only checkout）——一律用 MT。
    """
    if carrier == "carrier_w1":
        return MT / "runs/lsu/pilot_w1" / it, MT / "runs/lsu/pilot_w1" / it
    return MT / "runs/lsu/pilot/AGU", MT / "runs/lsu/pilot/AGU"


def build_ledger(campaign, freeze_path):
    freeze = json.loads(Path(freeze_path).read_text(encoding="utf-8"))
    runids = freeze.get("runids", {})
    items_by_runid = {}
    for item_id, run_id, _fields in LR.parse_items():
        items_by_runid[run_id] = item_id
    rows = []
    for carrier, rlist in runids.items():
        if not isinstance(rlist, list):   # counts/excluded 是说明字符串，跳过
            continue
        for runid_raw in rlist:
            # 重点项标记 "(K)"（A01-F0-W3(K)）——剥后缀再查清单，K 标志入台账
            key_flag = runid_raw.endswith("(K)")
            runid = runid_raw[:-3] if key_flag else runid_raw
            it = items_by_runid.get(runid)
            if it is None:
                rows.append({"runid": runid_raw, "item": None,
                             "carrier": carrier,
                             "error": "RunID 不在清单（Excel/manifest 冲突？）"})
                continue
            udir, _ = _item_unit_dirs(it, carrier)
            rj = udir / f"{it}_result.json"
            status, summary = None, {}
            if rj.exists():
                try:
                    d = json.loads(rj.read_text())
                    status = d.get("status")
                    summary = {k: d.get(k) for k in
                               ("attempted_runs", "activated_runs", "five_class",
                                "post_activation_simulator_failure",
                                "injected_not_activated_runs",
                                "classifier_failures", "conservation", "campaign")}
                except json.JSONDecodeError:
                    status = "RESULT_JSON_CORRUPT"
            # 实时样本计数（formal 进行中时 result.json 尚为 pilot 期数据）
            n_samples = len(list(udir.glob(f"{it}_s*/l5_verdict.json")))
            # 台账术语 v2（中央指令 2026-10-13）：AGU 批次属 outcome-only
            # （正式命令未启用 ctrace/msnap）——execution_complete 由结果
            # 证据如实判定；chain_complete 结构性 False；L1-L4（无 L5 证据
            # 时含 L5）待补跑。执行完成 ≠ chain_complete。
            exec_complete = bool(n_samples) and status not in (
                None, "RESULT_JSON_CORRUPT")
            missing = (["L1", "L2", "L3", "L4", "L5"] if not n_samples
                       else ["L1", "L2", "L3", "L4"])
            rows.append({
                "runid": runid, "item": it, "carrier": carrier,
                "key_runid": key_flag,
                "unit_dir": str(udir),
                "outcome_status": status, "l5_samples_on_disk": n_samples,
                "audit_summary_asof_result_json": summary,
                "execution_complete": exec_complete,
                "chain_complete": False,
                "missing_levels": missing,
                "needs_chain_backfill": True,
                "evidence_root": str(udir),
                "note": ("AGU 批次 outcome-only（正式命令未启用 ctrace/"
                         "msnap）：execution_complete（结局有效）≠ "
                         "chain_complete；L1-L4 完整链待补跑（OBS 计划；"
                         "历史补链后置）"),
            })
    return {"campaign": campaign, "generated": time.strftime("%F %T"),
            "freeze": str(freeze_path),
            "gem5_opt_sha256": GEM5_FROZEN_SHA,
            "ledger_kind": "chain_status_marking_v2",
            "rows": rows,
            "totals": {
                "runids": len(rows),
                "with_l5_evidence": sum(1 for r in rows
                                        if r.get("l5_samples_on_disk")),
                "execution_complete": sum(1 for r in rows
                                          if r.get("execution_complete")),
                "chain_complete": sum(1 for r in rows
                                      if r.get("chain_complete")),
                "needs_chain_backfill": sum(1 for r in rows
                                            if r.get("needs_chain_backfill")),
            }}


# ------------------------------------------------------- campaign handoff
def _nine_class_counts(obs_list):
    """九分类计数（[R6-ORACLE][G3] 未定结局必须显式计数，不得静默丢弃）。

    审计 G3：旧实现对 `l5.error or outcome=="INCONCLUSIVE"` 直接 `continue`
    —— 一个 activated 样本被静默丢弃（丢弃比 Unknown 更糟）。现在单列
    `inconclusive` / `classifier_error` 两个桶 + `unrecorded` 明细（含
    activated 与原因），守恒式显式写明（activated = 五类 + simfail +
    not_activated + inconclusive + classifier_error）。
    """
    five = {k: 0 for k in ("Masked", "Detected/Contained", "SDC", "Crash",
                           "Timeout")}
    fds = {k: 0 for k in ("Hardware RAS", "OS", "Application", "None")}
    simfail = not_act = inconclusive = cls_error = 0
    unrecorded = []
    for i, o in enumerate(obs_list):
        l5 = o.get("L5", {})
        out, act = l5.get("outcome"), (o.get("L0", {}).get("activated") or 0)
        # 先判 INCONCLUSIVE：lsu_l5_classify 的"输入不完整"结局**同时**带
        # error 字段（reason），若先判 error 会把"结局未定"误记成"分类器
        # 崩溃"——两者都单列但语义不同（实测暴露）。
        if out == "INCONCLUSIVE":
            inconclusive += 1
            why = l5.get("error_class") or "无 oracle 比较"
            unrecorded.append({"index": i, "activated": act,
                               "error_class": l5.get("error_class"),
                               "reason": f"inconclusive: 结局未定（{why}）"
                                         f"——单列，不丢"})
            continue
        if l5.get("error"):
            cls_error += 1
            unrecorded.append({"index": i, "activated": act,
                               "reason": f"classifier_error: {l5['error']}"})
            continue
        if not act:
            not_act += 1
            continue
        if out == "Crash" and l5.get("crash_kind") == "simulator_assert":
            simfail += 1
        elif out in five:
            five[out] += 1
        src = l5.get("first_detection_source")
        if src in fds:
            fds[src] += 1
    return {"five_class": five, "first_detection_source": fds,
            "post_activation_simulator_failure": simfail,
            "injected_not_activated": not_act,
            "inconclusive": inconclusive, "classifier_error": cls_error,
            "samples_total": len(obs_list), "unrecorded": unrecorded,
            "conservation": (
                "activated = five_class + post_activation_simulator_failure "
                "+ injected_not_activated + inconclusive + classifier_error"
                "（逐样本见 observation.json L5；未定结局单列 unrecorded，"
                "绝不静默丢弃）")}


def build_campaign_handoff(cdir, out_dir=None):
    cdir = Path(cdir)
    out_dir = Path(out_dir) if out_dir else cdir
    obs_list, samples = [], []
    for oj in sorted(cdir.glob("*/**/observation.json")):
        try:
            o = json.loads(oj.read_text())
        except json.JSONDecodeError:
            samples.append({"path": str(oj), "error": "unparseable"})
            continue
        obs_list.append(o)
        l2f = ((o.get("L2") or {}).get("commit_diff") or {})
        fe = l2f.get("first_errant_commit") or {}
        # v2 四状态（v1 历史样本缺字段时如实记 None；missing_levels 用
        # obs_core 同源规则回补——零漂移）
        ml = o.get("missing_levels")
        if not isinstance(ml, list):
            ml = OC.missing_levels(o)
        samples.append({
            "runid": o["identity"]["runid"], "sample": o["identity"]["sample"],
            "seed": o["identity"]["seed"], "obs_mode":
                o["identity"].get("obs_mode"),
            "outcome": (o.get("L5") or {}).get("outcome"),
            "execution_complete": o.get("execution_complete"),
            "evidence_complete": o.get("evidence_complete"),
            "chain_complete": o.get("chain_complete"),
            "needs_backfill": o.get("needs_backfill"),
            "missing_levels": ml,
            "first_divergence": ({"seq": fe.get("seq"), "tick": fe.get("tick"),
                                  "class": fe.get("class")} if fe else None),
            "violations": o.get("violations"), "path": str(oj)})
    ident = (obs_list[0]["identity"] if obs_list else {})
    handoff = {
        "campaign": cdir.name,
        "generated": time.strftime("%F %T"),
        "git_commit": ident.get("git_commit")
        or subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                          capture_output=True, text=True).stdout.strip(),
        "gem5_opt_sha256": ident.get("gem5_opt_sha256", GEM5_FROZEN_SHA),
        "lsu_proxy_sha256": ident.get("lsu_proxy_sha256"),
        "workload": ident.get("workload"),
        "workload_sha256": ident.get("workload_sha256"),
        "baseline_key": ident.get("baseline_key"),
        "nine_class": _nine_class_counts(obs_list),
        "conservation": ("activated(五类+simfail) + not_activated + "
                         "classifier_error + inconclusive = attempted"
                         "（逐样本见 observation.json L5.conservation；"
                         "未定结局单列 nine_class.unrecorded，绝不静默丢弃）"),
        "full_chain": {
            "samples_total": len(obs_list),
            # 纠偏轮 v2（中央指令 2026-10-13）：执行完成 ≠ chain_complete，
            # execution/evidence/chain 三计数分开单列。
            "execution_complete_count": sum(
                1 for o in obs_list if o.get("execution_complete")),
            "evidence_complete_count": sum(
                1 for o in obs_list if o.get("evidence_complete")),
            "chain_complete_count": sum(
                1 for o in obs_list if o.get("chain_complete")),
            "chain_incomplete_count": sum(
                1 for o in obs_list if o.get("chain_complete") is False),
            "false_reasons_histogram": _hist(
                [(o.get("chain_status_reason") or "").split("（")[0].split("——")[0]
                 for o in obs_list if not o.get("chain_complete")]),
            "note": ("campaign 执行完成 ≠ chain_complete：execution/"
                     "evidence/chain 三计数分开；chain_complete=false 样本"
                     "单列待补跑，不计入完整实验完成数"),
        },
        "retries": _retries(cdir),
        "resource_peaks": _hostmon_peaks(),
        "evidence_index": [s["path"] for s in samples if s.get("path")],
        "abs_paths": {"campaign_dir": str(cdir.resolve()),
                      "golden_root": str((cdir.parent / "golden").resolve())},
        "samples": samples,
    }
    return handoff


def _hist(seq):
    out = {}
    for s in seq:
        out[s] = out.get(s, 0) + 1
    return out


def _retries(cdir):
    """guard.out 里 ACQUIRE REFUSED 重试与 quarantine/staging 残留计数。"""
    n_refused = n_quarantine = 0
    for g in cdir.glob("**/*guard.out"):
        try:
            n_refused += g.read_text(errors="replace").count("ACQUIRE REFUSED")
        except OSError:
            pass
    n_quarantine = len(list(cdir.glob("**/*.quarantine.*")))
    return {"acquire_refused_events": n_refused,
            "quarantine_dirs": n_quarantine}


def _hostmon_peaks():
    """从 hostmon JSONL 取资源峰值（缺失→n/a，不造假）。"""
    out = {"source": "n/a (hostmon 未运行或无数据)"}
    files = sorted(OBS_ROOT.glob("hostmon/hostmon_*.jsonl"))
    if not files:
        return out
    peaks = {"min_mem_available_gib": None, "min_swap_free_gib": None,
             "max_gem5_n": 0, "min_home_free_gib": None, "max_so_ps": 0}
    for f in files[-2:]:
        for line in f.read_text(errors="replace").splitlines():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = d.get("mem_available_gib")
            if m is not None:
                peaks["min_mem_available_gib"] = m if \
                    peaks["min_mem_available_gib"] is None else \
                    min(peaks["min_mem_available_gib"], m)
            s = d.get("swap_free_gib")
            if s is not None:
                peaks["min_swap_free_gib"] = s if \
                    peaks["min_swap_free_gib"] is None else \
                    min(peaks["min_swap_free_gib"], s)
            peaks["max_gem5_n"] = max(peaks["max_gem5_n"],
                                      d.get("gem5_n") or 0)
            h = d.get("home_free_gib")
            if h is not None:
                peaks["min_home_free_gib"] = h if \
                    peaks["min_home_free_gib"] is None else \
                    min(peaks["min_home_free_gib"], h)
            peaks["max_so_ps"] = max(peaks["max_so_ps"], d.get("so_ps") or 0)
    return {"source": str(files[-1]), **peaks}


def _md(handoff):
    fc = handoff["full_chain"]
    lines = [f"# handoff — {handoff['campaign']}", "",
             f"生成：{handoff['generated']}", "",
             f"- git_commit：`{handoff['git_commit']}`",
             f"- gem5_opt_sha256：`{handoff['gem5_opt_sha256']}`",
             f"- workload：{handoff.get('workload')} (`{handoff.get('workload_sha256')}`)",
             f"- baseline_key：`{handoff.get('baseline_key')}`", "",
             "## 九分类计数", "",
             "```json", json.dumps(handoff["nine_class"], ensure_ascii=False,
                                  indent=1), "```", "",
             f"## 执行/证据/完整链（三计数分开，执行完成 ≠ chain_complete）",
             "",
             f"- execution_complete：{fc['execution_complete_count']}"
             f"/{fc['samples_total']}",
             f"- evidence_complete：{fc['evidence_complete_count']}"
             f"/{fc['samples_total']}",
             f"- chain_complete：{fc['chain_complete_count']}"
             f"/{fc['samples_total']}"
             f"（chain_incomplete={fc['chain_incomplete_count']} 单列待补跑，"
             f"不入完整完成数）", "",
             "```json", json.dumps(fc["false_reasons_histogram"],
                                  ensure_ascii=False, indent=1), "```", "",
             f"## 重试：{json.dumps(handoff['retries'], ensure_ascii=False)}", "",
             f"## 资源峰值：{json.dumps(handoff['resource_peaks'], ensure_ascii=False)}", "",
             "## 样本索引", ""]
    for s in handoff["samples"]:
        lines.append(f"- {s.get('runid')} {s.get('sample')} seed={s.get('seed')} "
                     f"→ {s.get('outcome')} exec={s.get('execution_complete')} "
                     f"evid={s.get('evidence_complete')} "
                     f"chain={s.get('chain_complete')} "
                     f"missing={s.get('missing_levels')} `{s.get('path')}`")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--ledger", action="store_true")
    g.add_argument("--campaign-handoff", dest="campaign_handoff")
    ap.add_argument("--campaign", default="p4_agu_formal_20261012")
    ap.add_argument("--freeze",
                    default="docs/gem5-fi/lsu/evidence/P4/"
                            "p4_freeze_agu_formal_20261012.json")
    ap.add_argument("--out-dir", default=None,
                    help="输出目录（ledger 干跑验证用 tmp；缺省=主树 "
                         "runs/lsu/obs/，真实台账由主负责人合并后执行）")
    args = ap.parse_args()
    if args.ledger:
        ledger = build_ledger(args.campaign, args.freeze)
        out = (Path(args.out_dir) / f"chain_ledger_{args.campaign}.json"
               if args.out_dir
               else OBS_ROOT / f"chain_ledger_{args.campaign}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(ledger, ensure_ascii=False, indent=1))
        print(f"ledger → {out}  runids={ledger['totals']['runids']} "
              f"with_l5={ledger['totals']['with_l5_evidence']} "
              f"execution_complete={ledger['totals']['execution_complete']} "
              f"chain_complete={ledger['totals']['chain_complete']} "
              f"needs_chain_backfill="
              f"{ledger['totals']['needs_chain_backfill']}")
        return 0
    h = build_campaign_handoff(args.campaign_handoff, args.out_dir)
    outj = Path(args.out_dir or args.campaign_handoff) / "handoff.json"
    outm = Path(args.out_dir or args.campaign_handoff) / "handoff.md"
    outj.parent.mkdir(parents=True, exist_ok=True)
    outj.write_text(json.dumps(h, ensure_ascii=False, indent=1))
    outm.write_text(_md(h))
    print(f"handoff → {outj} / {outm}  samples={h['full_chain']['samples_total']}")
    return 0


if __name__ == "__main__":
    main()
