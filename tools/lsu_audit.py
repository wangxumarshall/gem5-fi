#!/usr/bin/env python3
"""lsu_audit.py — LSU observation campaign 逐样本独立审计器（OBS 计划 T6a，Subagent-C）。

独立于生产者（lsu_obs_driver/lsu_obs_core 的写入路径）的只读完整性检查器：
解析每个 COMPLETE 样本的 observation.json，独立复核身份/hash/文件链，绝不重跑
任何实验、绝不写被审计目录（唯一允许的写 = --json OUT 汇总落盘，且 OUT 绝不
允许位于被审计树内）。

两种模式：
  模式 1（观测 campaign）：--campaign-root DIR
      遍历 DIR/<ITEM>/<ITEM>_s*/：
        * 有 COMPLETE → 逐样本审计（检查 i-vi，见下）
        * 无 COMPLETE → 列 staging/quarantine/incomplete 残留
        * <ITEM>_sN.replay/ → 重放证据目录（driver 设计保留，单列不计残留）
  模式 2（旧 pilot 样本）：--legacy-root DIR --item ITEM-xxx
      只读扫 l5_verdict.json，逐样本输出 outcome 完整、L1-L4 观测链未采集
      （OBS 前产物）——绝不写旧目录（--json OUT 落在旧目录内直接拒绝）。

COMPLETE 样本六项检查（任一不符 = audit FAIL）：
  (i)   schema 关键字段存在（顶层/identity/L0/L5/replay 必填键，
        对齐 schemas/observation.schema.json required 列表）
  (ii)  files 列表逐项存在且 sha256 复核——**全量复核，不是抽样**
  (iii) chain_complete 用 lsu_obs_core.chain_complete() 重算并与存储值比对
  (iv)  L1/L2 status 合法枚举（complete / not_observed_before_crash /
        not_observed_before_timeout / N/A(inactive_no_activation) /
        not_collected(l0l5_mode) / error）；L3/L4 按 schema 枚举
  (v)   activated>0 且 obs_mode=full → L1.fault/L2.fault trace 存在且
        gz_probe 可探（截断=诚实证据可接受，但见 (v.b)）；(v.b) 截断 fault
        trace 绝不允许被记成 no_divergence（必须
        truncated_no_divergence_in_prefix / diverged / not_observed_before_*）
  (vi)  identity.seed 与 lsu_seed(runid, phase, sample_index) 重算一致
        （身份一致性：sample 号与 seed 派生不符 = 身份造假/驱动 bug 证据）
  附加：COMPLETE 标记内 observation_sha256 与 observation.json 实际 sha 一致。

三条独立判据，绝不混同：
  * audit PASS/FAIL     = 完整性（上述六项），与结论好坏无关
  * chain_complete      = 观测链是否闭合（L3 unsupported 等 → False，诚实）
  * missing_layers      = 覆盖率指标：L1-L4 中状态非 complete 也非
    N/A(inactive_no_activation) 的层级（not_collected(l0l5_mode) 与
    unsupported、not_observed_before_* 均计入——它们确实没采到该层数据，
    诚实标注不等于数据已采）。audit PASS ≠ chain_complete ≠ missing 为空。

用法：
  python3 tools/lsu_audit.py --campaign-root runs/lsu/obs/obs_e2e_20261012 \
      [--json OUT.json]
  python3 tools/lsu_audit.py --legacy-root runs/lsu/pilot/AGU --item ITEM-002 \
      [--json OUT.json]
退出码：0=全部 PASS（模式 2 恒 0）；1=存在 FAIL；2=用法错误。
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import lsu_obs_core as OC          # noqa: E402  chain_complete/sha256/gz_probe 复用（零漂移）
from lsu_seed import lsu_seed      # noqa: E402  seed 派生重算（身份一致性）

VERSION = "lsu_audit v1 (OBS-6a)"

# schemas/observation.schema.json required 列表的程序化镜像（schema 文件本身
# 不被 import——jsonschema 非stdlib；此处逐键核对，键集与 schema 同源维护）
TOP_REQUIRED = ["schema", "identity", "L0", "L1", "L2", "L3", "L4", "L5",
                "replay_determinism", "violations", "files", "chain_complete",
                "chain_status_reason"]
IDENT_REQUIRED = ["campaign", "runid", "sample", "seed", "git_commit",
                  "gem5_opt_sha256", "workload", "workload_sha256",
                  "baseline_key", "pythonhashseed"]
L0_REQUIRED = ["attempted", "eligible", "injected", "activated",
               "injections", "funnel_source"]
L5_REQUIRED = ["outcome", "first_detection_source"]
REPLAY_REQUIRED = ["policy", "verified"]

L1L2_LEGAL = {"complete", "not_observed_before_crash",
              "not_observed_before_timeout", "N/A(inactive_no_activation)",
              "not_collected(l0l5_mode)", "error"}
L3_LEGAL = {"complete", "unsupported", "N/A(inactive_no_activation)", "error"}
L4_LEGAL = {"complete", "N/A(inactive_no_activation)",
            "not_collected(l0l5_mode)", "error"}
# 覆盖率口径：complete 与 inactive-N/A 之外的层级 = 该层数据未采集
COVERAGE_COLLECTED = {"complete", "N/A(inactive_no_activation)"}
PHASES = {"engineering", "pilot", "screening", "confirmatory",
          "sensitivity", "reproduction"}

SAMPLE_DIR_RE = re.compile(r"^(ITEM-\d+)_s(\d+)$")


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ---------------------------------------------------------------- mode 1
def audit_sample_dir(d):
    """审计一个含 COMPLETE 的样本目录（只读）。返回审计记录 dict。"""
    d = Path(d)
    reasons = []
    notes = []

    # COMPLETE 标记（协议要求 JSON；不可读即完整性异常）
    comp = _load_json(d / OC.COMPLETE)
    if comp is None:
        reasons.append("complete_marker_unreadable: COMPLETE 非合法 JSON")

    # observation.json 可解析性（不可解析 = 最高级失败，直接返回）
    try:
        obs = json.loads((d / "observation.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return {"sample": d.name,
                "missing_layers": ["L0", "L1", "L2", "L3", "L4", "L5"],
                "violations": [], "chain_complete": None,
                "audit": "FAIL",
                "reasons": [f"observation_unparseable: {e}"]}

    # (i) schema 关键字段
    for k in TOP_REQUIRED:
        if k not in obs:
            reasons.append(f"schema_missing_key: {k}")
    ident = obs.get("identity") or {}
    for k in IDENT_REQUIRED:
        if k not in ident:
            reasons.append(f"identity_missing_key: {k}")
    for k in L0_REQUIRED:
        if k not in (obs.get("L0") or {}):
            reasons.append(f"L0_missing_key: {k}")
    for k in L5_REQUIRED:
        if k not in (obs.get("L5") or {}):
            reasons.append(f"L5_missing_key: {k}")
    for k in REPLAY_REQUIRED:
        if k not in (obs.get("replay_determinism") or {}):
            reasons.append(f"replay_missing_key: {k}")

    # COMPLETE.observation_sha256 与 observation.json 实际 sha 一致
    if comp and comp.get("observation_sha256"):
        actual = OC.sha256_file(d / "observation.json")
        if actual != comp["observation_sha256"]:
            reasons.append("complete_marker_sha_mismatch: observation.json "
                           "与 COMPLETE 标记记录的 sha 不符（事后被改写）")

    # (ii) files 全量存在 + sha256 复核（绝不抽样）
    files = obs.get("files") or []
    if not files:
        reasons.append("files_list_empty")
    for fe in files:
        fp = Path(fe.get("path", ""))
        if not fp.is_absolute():
            fp = d / fp
        if not fp.exists():
            reasons.append(f"file_missing: {fe.get('path')}")
            continue
        if not fe.get("sha256") or OC.sha256_file(fp) != fe["sha256"]:
            reasons.append(f"sha_mismatch: {fe.get('path')}")

    # (iii) chain_complete 重算一致
    stored = obs.get("chain_complete")
    recomputed, why = OC.chain_complete(obs)
    if stored != recomputed:
        reasons.append(f"chain_complete_recompute_mismatch: stored={stored} "
                       f"recomputed={recomputed} ({why})")

    # (iv) 状态合法枚举
    for lv, legal in (("L1", L1L2_LEGAL), ("L2", L1L2_LEGAL),
                      ("L3", L3_LEGAL), ("L4", L4_LEGAL)):
        st = (obs.get(lv) or {}).get("status")
        if st not in legal:
            reasons.append(f"{lv}_status_illegal: {st!r}")

    # (v) activated>0 且 full → fault trace 存在且可探 + 截断诚实性
    activated = (obs.get("L0") or {}).get("activated") or 0
    mode = ident.get("obs_mode")
    if activated and mode == "full":
        for lv in ("L1", "L2"):
            probe = (obs.get(lv) or {}).get("fault") or {}
            p = probe.get("path")
            if not p:
                reasons.append(f"{lv}_fault_probe_missing: full 模式且 "
                               f"activated>0，但无 fault trace 探针记录")
                continue
            fp = Path(p)
            if not fp.is_absolute():
                fp = d / fp
            if not fp.exists():
                # 已知生产者缺陷的诚实回退：driver 的 post_process 在 .staging
                # 内构建 L1/L2 探针，finalize 重命名后 observation.json 里的
                # 绝对探针路径指向已不存在的 .staging 路径。轨迹文件本身按
                # 固定名（commit_trace.csv.gz / micro_snap.csv.gz）就在样本
                # 目录内——按 basename 回退定位并记 note（不静默、不误判 FAIL；
                # sha 一致性由 files 全量复核独立保证）。
                cand = d / Path(p).name
                if cand.exists():
                    notes.append(f"{lv}_probe_path_stale_resolved_by_basename: "
                                 f"记录路径 {p}（.staging 残留名）→ 回退 "
                                 f"{cand}")
                    fp = cand
                else:
                    reasons.append(f"{lv}_fault_file_missing: {p}")
                    continue
            rp = OC.gz_probe(fp)
            if rp["error"] in ("file missing", "empty file") \
                    or (rp["error"] or "").startswith("unreadable"):
                reasons.append(f"{lv}_fault_unreadable: {rp['error']}")
            if lv == "L2" and rp["truncated"]:
                cd = (obs.get("L2") or {}).get("commit_diff") or {}
                if cd.get("verdict") == "no_divergence":
                    reasons.append(
                        "L2_truncated_reported_no_divergence: 截断 fault "
                        "trace 绝不允许记为 no_divergence（须 "
                        "truncated_no_divergence_in_prefix / diverged / "
                        "not_observed_before_*）")

    # (vi) identity.seed 与 (runid, phase, sample) 派生一致
    if (ident.get("runid") and ident.get("phase") in PHASES
            and ident.get("sample") is not None
            and ident.get("seed") is not None):
        mm = re.match(r"^s(\d+)$", str(ident["sample"]))
        if mm:
            expect = lsu_seed(ident["runid"], ident["phase"], int(mm.group(1)))
            if int(ident["seed"]) != expect:
                reasons.append(
                    f"identity_seed_mismatch: sample={ident['sample']} "
                    f"phase={ident['phase']} 期望 seed={expect} 实录="
                    f"{ident['seed']}（sample 号与 seed 派生不符——疑似全部"
                    f"样本误用 sample-0 seed，见 OBS-5a E2E 报告）")

    missing = [lv for lv in ("L1", "L2", "L3", "L4")
               if (obs.get(lv) or {}).get("status") not in COVERAGE_COLLECTED]
    return {"sample": d.name, "missing_layers": missing,
            "violations": obs.get("violations") or [],
            "chain_complete": stored,
            "audit": "PASS" if not reasons else "FAIL",
            "reasons": reasons, "notes": notes}


def audit_golden_dir(d, expect_gem5_sha=None):
    """审计 no_fault_golden 目录（L1/L2 比对基线；只读，比 fault 样本更严：
    golden trace 必须完整可读——截断的 golden 基线会污染全部比对）。"""
    d = Path(d)
    reasons = []
    if not (d / OC.COMPLETE).exists():
        return {"sample": f"golden:{d.name}", "audit": "FAIL",
                "reasons": ["no COMPLETE marker"]}
    obs = _load_json(d / "observation.json")
    if obs is None:
        return {"sample": f"golden:{d.name}", "audit": "FAIL",
                "reasons": ["observation.json 不可解析"]}
    ident = obs.get("identity") or {}
    if ident.get("kind") != "no_fault_golden":
        reasons.append(f"identity.kind={ident.get('kind')!r} 非 no_fault_golden")
    files = obs.get("files") or []
    if not files:
        reasons.append("files_list_empty")
    for fe in files:
        fp = Path(fe.get("path", ""))
        if not fp.is_absolute():
            fp = d / fp
        if not fp.exists():
            reasons.append(f"file_missing: {fe.get('path')}")
        elif OC.sha256_file(fp) != fe.get("sha256"):
            reasons.append(f"sha_mismatch: {fe.get('path')}")
    for name in ("commit_trace.csv.gz", "micro_snap.csv.gz"):
        fe = next((f for f in files if f.get("name") == name), None)
        if fe is None:
            reasons.append(f"golden_missing_trace: {name}")
            continue
        fp = Path(fe["path"])
        if not fp.is_absolute():
            fp = d / fp
        rp = OC.gz_probe(fp)
        # gz_probe 语义：readable=True 仅表示"可打开读"（截断另由 truncated
        # 标志诚实标注）——golden 基线必须两者都干净：截断的 golden 会污染
        # 全部 L1/L2 比对，绝不允许作为基线。
        if not rp["readable"] or rp["truncated"]:
            reasons.append(f"golden_trace_not_readable: {name}: "
                           f"{rp['error'] or 'truncated'}")
    if expect_gem5_sha and ident.get("gem5_opt_sha256") != expect_gem5_sha:
        reasons.append(f"golden gem5_opt_sha256={ident.get('gem5_opt_sha256')}"
                       f" != 期望 {expect_gem5_sha}")
    return {"sample": f"golden:{d.name}", "audit": "PASS" if not reasons
            else "FAIL", "reasons": reasons}


def audit_campaign_root(root):
    """模式 1：遍历 campaign 目录，返回 (records, residues, replay_dirs, summary)。"""
    root = Path(root)
    if not root.is_dir():
        return None
    records, residues, replay_dirs = [], [], []
    for item_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        if not re.match(r"^ITEM-\d+$", item_dir.name):
            continue
        for sub in sorted(p for p in item_dir.iterdir() if p.is_dir()):
            m = SAMPLE_DIR_RE.match(sub.name)
            if m:
                if (sub / OC.COMPLETE).exists():
                    records.append(audit_sample_dir(sub))
                else:
                    residues.append({"sample": sub.name,
                                     "kind": "incomplete_no_COMPLETE"})
            elif sub.name.endswith(".staging"):
                residues.append({"sample": sub.name, "kind": "staging"})
            elif ".quarantine." in sub.name:
                residues.append({"sample": sub.name, "kind": "quarantine"})
            elif sub.name.endswith(".replay"):
                replay_dirs.append(sub.name)
    hist = {}
    for r in records:
        key = ",".join(r["missing_layers"]) if r["missing_layers"] else "none"
        hist[key] = hist.get(key, 0) + 1
    summary = {
        "campaign_root": str(root), "auditor": VERSION,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "samples_audited": len(records),
        "audit_pass": sum(1 for r in records if r["audit"] == "PASS"),
        "audit_fail": sum(1 for r in records if r["audit"] == "FAIL"),
        "chain_complete_true": sum(1 for r in records
                                   if r["chain_complete"] is True),
        "chain_complete_false": sum(1 for r in records
                                    if r["chain_complete"] is False),
        "chain_complete_missing": sum(1 for r in records
                                      if r["chain_complete"] is None),
        "missing_layers_histogram": dict(sorted(hist.items())),
        "residues": residues,
        "replay_evidence_dirs": replay_dirs,
    }
    return records, residues, replay_dirs, summary


# ---------------------------------------------------------------- mode 2
def audit_legacy_root(root, item):
    """模式 2：旧 pilot 样本（只读）。每样本 = outcome 完整、L1-L4 未采集。"""
    root = Path(root)
    if not root.is_dir():
        return None
    records = []
    dirs = [d for d in root.iterdir()
            if d.is_dir() and SAMPLE_DIR_RE.match(d.name)
            and SAMPLE_DIR_RE.match(d.name).group(1) == item]
    dirs.sort(key=lambda d: int(SAMPLE_DIR_RE.match(d.name).group(2)))
    for d in dirs:
        vpath = d / "l5_verdict.json"
        v = _load_json(vpath)
        rec = {"item": item, "sample": d.name,
               "chain": "outcome_complete_chain_pending",
               "missing_levels": ["L1", "L2", "L3", "L4"],
               "evidence": str(vpath.resolve()) if vpath.exists() else None,
               "note": "旧 pilot 样本仅有 L5 verdict（OBS 观测链前产物）；"
                       "L0-L4 未采集，绝不写旧目录"}
        if v is None:
            rec["outcome"] = None
            rec["error"] = ("l5_verdict.json 不可读"
                            if vpath.exists() else "l5_verdict.json 缺失")
        else:
            rec["outcome"] = v.get("outcome")
            rec["crash_kind"] = v.get("crash_kind")
            rec["activated"] = v.get("activated")
        records.append(rec)
    tally = {}
    for r in records:
        k = str(r.get("outcome"))
        tally[k] = tally.get(k, 0) + 1
    summary = {"legacy_root": str(root), "item": item, "auditor": VERSION,
               "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
               "samples": len(records), "outcome_tally": tally}
    return records, summary


# ---------------------------------------------------------------- CLI
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse
                                 .RawDescriptionHelpFormatter)
    ap.add_argument("--campaign-root", default=None,
                    help="模式 1：观测 campaign 目录（含 ITEM-*/<ITEM>_s*/）")
    ap.add_argument("--legacy-root", default=None,
                    help="模式 2：旧 pilot 样本根目录（只读）")
    ap.add_argument("--item", default=None,
                    help="模式 2 必填：ITEM-xxx")
    ap.add_argument("--json", default=None,
                    help="汇总+逐样本记录 JSON 输出路径（绝不写在被审计树内）")
    args = ap.parse_args()

    if not args.campaign_root and not args.legacy_root:
        ap.error("需要 --campaign-root（模式 1）或 --legacy-root --item（模式 2）")
    if args.legacy_root and not args.item:
        ap.error("模式 2 需要 --item ITEM-xxx")

    # --json 落点保护：绝不写进被审计树
    if args.json:
        outp = Path(args.json).resolve()
        guarded = [Path(p).resolve()
                   for p in (args.campaign_root, args.legacy_root) if p]
        for g in guarded:
            if outp == g or str(outp).startswith(str(g) + "/"):
                print(f"ERROR: --json 输出 {outp} 位于被审计目录 {g} 内——"
                      f"绝不写被审计树", file=sys.stderr)
                return 2

    if args.campaign_root:
        res = audit_campaign_root(args.campaign_root)
        if res is None:
            print(f"ERROR: {args.campaign_root} 不是目录", file=sys.stderr)
            return 2
        records, residues, replay_dirs, summary = res
        for r in records:
            print(json.dumps(r, ensure_ascii=False))
        for r in residues:
            print(json.dumps({"residue": r}, ensure_ascii=False))
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        if args.json:
            Path(args.json).write_text(
                json.dumps({"summary": summary, "records": records,
                            "residues": residues,
                            "replay_evidence_dirs": replay_dirs},
                           ensure_ascii=False, indent=1) + "\n",
                encoding="utf-8")
            print(f"[json] {args.json}")
        return 0 if summary["audit_fail"] == 0 else 1

    # 模式 2（legacy，只读）
    res = audit_legacy_root(args.legacy_root, args.item)
    if res is None:
        print(f"ERROR: {args.legacy_root} 不是目录", file=sys.stderr)
        return 2
    records, summary = res
    for r in records:
        print(json.dumps(r, ensure_ascii=False))
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if args.json:
        Path(args.json).write_text(
            json.dumps({"summary": summary, "records": records},
                       ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"[json] {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
