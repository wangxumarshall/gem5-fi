#!/usr/bin/env python3
"""lsu_audit.py — LSU observation campaign 逐样本独立审计器（OBS 计划 T6a，Subagent-C；
2026-10-13 纠偏轮升级 v2：六条强制 FAIL 规则 + 三条附加规则，默认规则集 v2）。

独立于生产者（lsu_obs_driver/lsu_obs_core 的写入路径）的只读完整性检查器：
解析每个 COMPLETE 样本的 observation.json，独立复核身份/hash/文件链，绝不重跑
任何实验、绝不写被审计目录（唯一允许的写 = --json OUT 汇总落盘，且 OUT 绝不
允许位于被审计树内；--self-check 的合成样本一律建在系统临时目录）。

两种模式：
  模式 1（观测 campaign）：--campaign-root DIR [--rules v1|v2]
      遍历 DIR/<ITEM>/<ITEM>_s*/：
        * 有 COMPLETE → 逐样本审计（检查 i-vi + 规则集，见下）
        * 无 COMPLETE → 列 staging/quarantine/incomplete 残留
        * <ITEM>_sN.replay/ → 重放证据目录（driver 设计保留，单列不计残留）
  模式 2（旧 pilot 样本）：--legacy-root DIR --item ITEM-xxx
      只读扫 l5_verdict.json，逐样本输出 outcome 完整、L1-L4 观测链未采集
      （OBS 前产物）——绝不写旧目录（--json OUT 落在旧目录内直接拒绝）。
      legacy 模式不受 v2 规则影响（旧样本无 observation.json，只有台账标记）。

COMPLETE 样本基础检查（任一不符 = audit FAIL；v1/v2 两规则集共用）：
  (i)   schema 关键字段存在（顶层/identity/L0/L5/replay 必填键，
        对齐 schemas/observation.schema.json required 列表）
  (ii)  files 列表逐项存在且 sha256 复核——**全量复核，不是抽样**
  (iii) chain_complete 重算并与存储值比对（v1 样本用 lsu_obs_core.
        chain_complete()；v2 契约样本用本审计器独立推导的 _v2_chain_complete）
  (iv)  L1/L2 status 合法枚举（complete / not_observed_before_crash /
        not_observed_before_timeout / N/A(inactive_no_activation) /
        not_collected(l0l5_mode) / error）；L3/L4 按 schema 枚举
  (v)   见规则 3（v2）/(v)（v1，历史复现）
  (vi)  identity.seed 与 lsu_seed(runid, phase, sample_index) 重算一致
        （身份一致性：sample 号与 seed 派生不符 = 身份造假/驱动 bug 证据）
  附加：COMPLETE 标记内 observation_sha256 与 observation.json 实际 sha 一致。

=========================== 规则集 v2（默认）===========================
中央纠偏指令 2026-10-13（LSU 故障注入轨道纠偏轮，Subagent-C）：修改完整性
审计器，使指定情况**强制 FAIL**，不降低标准让测试通过。六条强制规则 +
三条附加规则，每规则一个 _rule_* 独立检查器（返回 reasons 列表），主审计
循环聚合。`--rules v1` 复现历史审计行为（v1 = 升级前代码路径，无下列规则）。

  R1  activated>0 但 L3 unsupported（status=="unsupported" 或
      method∈{None,"proxy"}）→ FAIL `L3_unsupported_for_activated_sample`
      （activated 样本必须有真传播证据；unsupported/proxy 不得算数。
      即"当前 E2E 样本全 chain_complete=false 不得算数"的机器执行）
  R2  attempted/eligible 缺失（L0.attempted is None 或 L0.eligible is
      None）→ FAIL `L0_funnel_incomplete`（injected/activated 缺失同理
      补齐——v1 仅查键存在，v2 连 None 值一并拦截）
  R3  ref/fault trace 或 msnap 不可读（L1/L2 的 ref/fault probe error 非
      "截断"类，或文件缺失/空）→ FAIL `evidence_trace_unreadable`
      ——例外（v1 已有，保留）：层级状态为 not_observed_before_crash/
      _timeout 时空 fault trace 是 W2.1 批量 flush 契约的诚实结果，记
      note 不 FAIL。截断 trace 另受 (v.b) 约束：绝不允许记成 no_divergence。
  R4  空 trace 被报告成真实 commit divergence（L2.fault rows==0 且
      commit_diff.verdict=="diverged" 或 total_divergence_points>0）→
      FAIL `empty_trace_fake_divergence`（BUG-4 类记录——审计器主动拦截，
      即使生产侧已修）
  R5  detector_na 被计为 Detected/Contained（L5.classes["Detected/
      Contained"]>0 且 L5.detected_na==True，或 L4.detected==True 且
      L4.detector∈{"not_present","none_wired"}）→ FAIL
      `detector_na_counted_as_detected`
  R6  chain_complete=true 但存在 missing/unsupported/proxy 层
      （chain_complete==True 且 missing_levels 非空，或任一层级
      status=="unsupported"，或 L3.method=="proxy"）→ FAIL
      `chain_complete_with_degraded_layer`
  R7  schema 版本：observation.json 的 schema 须为 "lsu-observation-v2"；
      v1 样本 → FAIL `schema_version_pre_correction`（纠偏前历史样本，
      按 v2 规则如实 FAIL——中央知情且期望的行为，不静默降级）
  R8  v2 契约顶层字段（execution_complete/evidence_complete/
      needs_backfill/missing_levels）缺失 → FAIL `contract_v2_fields_missing`
      （类型不符 → `contract_v2_fields_bad_type`）
  R9  L4.detector 须为 "not_present"；"none_wired" 为 v1 值 → FAIL
      `L4_detector_v1_value_none_wired`（schema_version 类，同 R7 处理）

v2 契约（B 并行实现的 obs_core v2 字段；本审计器只按契约读，不 import
生产者 v2 实现）：
  顶层：schema="lsu-observation-v2", execution_complete: bool,
        evidence_complete: bool, chain_complete: bool,
        needs_backfill: bool, missing_levels: [str]
  L3：{"status": "complete"|"unsupported"|"N/A(inactive_no_activation)",
       "method": "propagation_trace"|None|"proxy",
       "correlation_keys": [...], "evidence": {..., "path_complete": bool},
       "caveats": [...]}
  L4：{"status": "complete"|..., "detector": "not_present", "detected": bool,
       "detected_na": bool, "l4_source": "first_verifiable_anomaly",
       "first_anomaly": {...}|None}
  L0：attempted/eligible/injected/activated 四字段（None=缺失）
  现有 v1 字段（identity/L1/L2/L5/files/violations/replay_determinism）不变。

三条独立判据，绝不混同：
  * audit PASS/FAIL     = 完整性（基础检查 + 规则集），与结论好坏无关
  * chain_complete      = 观测链是否闭合（L3 unsupported 等 → False，诚实）
  * missing_layers      = 覆盖率指标：L1-L4 中状态非 complete 也非
    N/A(inactive_no_activation) 的层级（not_collected(l0l5_mode) 与
    unsupported、not_observed_before_* 均计入——它们确实没采到该层数据，
    诚实标注不等于数据已采）。audit PASS ≠ chain_complete ≠ missing 为空。

用法：
  python3 tools/lsu_audit.py --campaign-root runs/lsu/obs/obs_e2e_20261012 \
      [--rules v1|v2] [--json OUT.json]
  python3 tools/lsu_audit.py --legacy-root runs/lsu/pilot/AGU --item ITEM-002 \
      [--json OUT.json]
  python3 tools/lsu_audit.py --self-check
退出码：0=全部 PASS（模式 2 恒 0；--self-check 全部检出）；1=存在 FAIL
（或 self-check 有规则未检出）；2=用法错误。
"""
import argparse
import gzip
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import lsu_obs_core as OC          # noqa: E402  chain_complete/sha256/gz_probe 复用（零漂移）
from lsu_seed import lsu_seed      # noqa: E402  seed 派生重算（身份一致性）

VERSION = "lsu_audit v2 (OBS-6a, rules v2 default; 中央纠偏指令 2026-10-13)"
RULES_V1 = "v1"
RULES_V2 = "v2"
RULES_DEFAULT = RULES_V2
SCHEMA_V1 = "lsu-observation-v1"
SCHEMA_V2 = "lsu-observation-v2"

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
NOT_OBSERVED_STATES = ("not_observed_before_crash", "not_observed_before_timeout")

# v2 契约顶层字段（规则 R8）：字段名 → 契约类型
V2_TOP_FIELDS = (("execution_complete", bool), ("evidence_complete", bool),
                 ("needs_backfill", bool), ("missing_levels", list))

SAMPLE_DIR_RE = re.compile(r"^(ITEM-\d+)_s(\d+)$")


def _load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ================================================================ 规则集 v2
def _rule_l3_unsupported_for_activated(obs):
    """R1：activated>0 但 L3 unsupported（status=="unsupported" 或
    method∈{None,"proxy"}）→ FAIL（中央纠偏指令 2026-10-13 规则 1）。"""
    activated = (obs.get("L0") or {}).get("activated") or 0
    if not activated:
        return []
    l3 = obs.get("L3") or {}
    if l3.get("status") == "unsupported" or l3.get("method") in (None, "proxy"):
        return [f"L3_unsupported_for_activated_sample: activated={activated} "
                f"但 L3 status={l3.get('status')!r} method="
                f"{l3.get('method')!r}（activated>0 的样本必须有真传播证据"
                f"（method=propagation_trace）；unsupported/proxy 不得算数"
                f"——中央纠偏指令 2026-10-13 规则 1）"]
    return []


def _rule_l0_funnel_incomplete(obs):
    """R2：L0 漏斗字段缺失（attempted/eligible is None → FAIL；中央指令
    明文补齐 attempted/eligible，injected/activated 缺失一并拦截）。"""
    l0 = obs.get("L0") or {}
    missing = [k for k in ("attempted", "eligible", "injected", "activated")
               if l0.get(k) is None]
    if missing:
        return ["L0_funnel_incomplete: L0 漏斗字段缺失/None: "
                + ",".join(missing)
                + "（attempted/eligible 缺失即 FAIL——中央纠偏指令 "
                  "2026-10-13 规则 2；injected/activated 缺失同理）"]
    return []


def _err_class(err):
    """probe error 三分类：ok（None）/ truncated（截断=诚实证据可接受）/
    bad（file missing / empty file / unreadable —— R3 拦截对象）。"""
    if err is None:
        return "ok"
    if str(err).startswith("truncated"):
        return "truncated"
    return "bad"


def _rule_evidence_trace_unreadable(d, obs, ident):
    """R3：L1/L2 的 ref/fault trace（或 msnap）不可读 → FAIL。

    两路独立证据都查：(a) observation.json 里生产者记录的 probe error；
    (b) 审计器现场 gz_probe 复核（文件缺失/空/不可读）。截断类 error 是
    诚实证据（可接受，另受 v.b 约束）。例外（v1 已有，保留）：层级状态为
    not_observed_before_crash/_timeout 时空 fault trace 是 W2.1 批量 flush
    契约的诚实结果 → 记 note 不 FAIL。fault 探针路径缺失时按 basename
    回退定位（.staging 残留名，v1 行为）；ref 是 golden 基线、不在样本
    目录内，**绝不**做 basename 回退（同名会错配到 fault 轨迹）。
    返回 (reasons, notes)。
    """
    d = Path(d)
    reasons, notes = [], []
    activated = (obs.get("L0") or {}).get("activated") or 0
    mode = (ident or {}).get("obs_mode")
    demand = bool(activated) and mode == "full"
    for lv in ("L1", "L2"):
        entry = obs.get(lv) or {}
        lv_status = entry.get("status")
        for side in ("ref", "fault"):
            pr = entry.get(side)
            if not isinstance(pr, dict):
                pr = None
            if pr is None:
                if demand and side == "fault":
                    reasons.append(f"evidence_trace_unreadable: {lv}.fault "
                                   f"探针记录缺失（full 模式且 activated>0）")
                continue
            # (a) 记录态 probe error（生产者自报）
            if _err_class(pr.get("error")) == "bad":
                if side == "fault" and lv_status in NOT_OBSERVED_STATES:
                    notes.append(f"{lv}_fault_empty_under_not_observed: "
                                 f"记录 probe error={pr.get('error')!r}"
                                 f"（W2.1 批量 flush 契约的诚实结果）")
                else:
                    reasons.append(f"evidence_trace_unreadable: {lv}.{side} "
                                   f"记录 probe error={pr.get('error')!r}")
            # (b) 现场复核
            p = pr.get("path")
            if not p:
                if demand and side == "fault":
                    reasons.append(f"evidence_trace_unreadable: {lv}.fault "
                                   f"探针无 path（full 模式且 activated>0）")
                continue
            fp = Path(p)
            if not fp.is_absolute():
                fp = d / fp
            if not fp.exists():
                cand = d / Path(p).name
                if side == "fault" and cand.exists():
                    notes.append(f"{lv}_probe_path_stale_resolved_by_basename:"
                                 f" 记录路径 {p}（.staging 残留名）→ 回退 "
                                 f"{cand}")
                    fp = cand
                else:
                    if side == "fault" and lv_status in NOT_OBSERVED_STATES:
                        notes.append(f"{lv}_fault_empty_under_not_observed: "
                                     f"file missing（记录路径 {p}；W2.1 批量"
                                     f" flush 契约的诚实结果）")
                    else:
                        reasons.append(f"evidence_trace_unreadable: {lv}."
                                       f"{side} file missing（记录路径 {p}）")
                    continue
            rp = OC.gz_probe(fp)
            if _err_class(rp["error"]) == "bad":
                if side == "fault" and lv_status in NOT_OBSERVED_STATES:
                    notes.append(f"{lv}_fault_empty_under_not_observed: "
                                 f"{rp['error']}（W2.1 批量 flush 契约的"
                                 f"诚实结果，见层级 note）")
                else:
                    reasons.append(f"evidence_trace_unreadable: {lv}.{side} "
                                   f"{rp['error']}（现场复核 {fp}）")
            # (v.b) 截断 fault trace 绝不允许记成 no_divergence（v1 检查保留）
            if lv == "L2" and side == "fault" and rp["truncated"]:
                cd = entry.get("commit_diff") or {}
                if cd.get("verdict") == "no_divergence":
                    reasons.append(
                        "L2_truncated_reported_no_divergence: 截断 fault "
                        "trace 绝不允许记为 no_divergence（须 "
                        "truncated_no_divergence_in_prefix / diverged / "
                        "not_observed_before_*）")
    return reasons, notes


def _rule_empty_trace_fake_divergence(obs):
    """R4：空 trace 被报告成真实 commit divergence（BUG-4 类）——
    L2.fault rows==0 且（verdict=="diverged" 或 points>0）→ FAIL。"""
    l2 = obs.get("L2") or {}
    cd = l2.get("commit_diff")
    if not isinstance(cd, dict):
        return []
    claim = (cd.get("verdict") == "diverged"
             or (cd.get("total_divergence_points") or 0) > 0)
    if not claim:
        return []
    fault = l2.get("fault") or {}
    if fault.get("rows") == 0:
        return [f"empty_trace_fake_divergence: L2.fault rows==0 但 "
                f"commit_diff.verdict={cd.get('verdict')!r} "
                f"total_divergence_points={cd.get('total_divergence_points')}"
                f"（BUG-4 类：空 trace 绝不允许报真实 divergence——中央纠偏"
                f"指令 2026-10-13 规则 4，审计器主动拦截，即使生产侧已修）"]
    return []


def _rule_detector_na_counted_as_detected(obs):
    """R5：detector_na 被计为 Detected/Contained → FAIL（两条款）。"""
    reasons = []
    l5 = obs.get("L5") or {}
    l4 = obs.get("L4") or {}
    dc = (l5.get("classes") or {}).get("Detected/Contained") or 0
    if dc > 0 and l5.get("detected_na") is True:
        reasons.append(f"detector_na_counted_as_detected: L5.classes"
                       f"['Detected/Contained']={dc} 且 L5.detected_na==True"
                       f"（规则 5a——detected_na 绝不冒充 Detected）")
    if l4.get("detected") is True and l4.get("detector") in ("not_present",
                                                             "none_wired"):
        reasons.append(f"detector_na_counted_as_detected: L4.detected==True "
                       f"但 L4.detector={l4.get('detector')!r}（规则 5b——"
                       f"detector 未接线时 detected 必须为 False）")
    return reasons


def _rule_chain_complete_with_degraded_layer(obs):
    """R6：chain_complete==True 但存在 missing/unsupported/proxy 层 → FAIL。"""
    if obs.get("chain_complete") is not True:
        return []
    degraded = []
    ml = obs.get("missing_levels")
    if ml:
        degraded.append(f"missing_levels={ml!r}")
    for lv in ("L1", "L2", "L3", "L4"):
        if (obs.get(lv) or {}).get("status") == "unsupported":
            degraded.append(f"{lv}.status==unsupported")
    if (obs.get("L3") or {}).get("method") == "proxy":
        degraded.append("L3.method==proxy")
    if degraded:
        return ["chain_complete_with_degraded_layer: chain_complete=true 但"
                " 存在降级层: " + "; ".join(degraded)
                + "（中央纠偏指令 2026-10-13 规则 6）"]
    return []


def _rule_path_complete_false_chain_true(obs):
    """R10（中央纠偏指令 2026-10-13 二轮规则 1）：activated>0 且
    L3.path_complete=false 但 chain_complete=true → 强制 FAIL。"""
    act = (obs.get("L0") or {}).get("activated") or 0
    l3 = obs.get("L3") or {}
    l3ev = l3.get("evidence") or {}
    if (act and l3.get("method") == "propagation_trace"
            and l3ev.get("path_complete") is False
            and obs.get("chain_complete") is True):
        return ["path_complete_false_chain_true: activated>0 且 "
                "L3.path_complete=false 但 chain_complete=true（中央纠偏"
                "指令 2026-10-13 二轮规则 1：path_complete=false 默认"
                "chain_complete=false）"]
    return []


def _rule_l3_complete_without_terminal(obs):
    """R11（二轮规则 2）：activated>0 且 L3 complete 但无可验证终点
    （无 resp/taint_reg/consumer/errant_commit 节点，也无完整下游扫描
    证明的 terminal_reason）→ 强制 FAIL。仅有 inj→addr_form→mem_req
    不算完整。"""
    act = (obs.get("L0") or {}).get("activated") or 0
    l3 = obs.get("L3") or {}
    l3ev = l3.get("evidence") or {}
    if not (act and l3.get("status") == "complete"
            and l3.get("method") == "propagation_trace"):
        return []
    if l3ev.get("terminal_verified") is True:
        return []
    # 兼容无 terminal_verified 键的旧形态：查终点节点计数
    has_terminal_node = any(
        ((l3ev.get(k) or {}).get("count", 0) or 0) > 0
        for k in ("responses", "tainted_regs", "consumers"))
    has_errant = l3ev.get("first_errant_commit") is not None
    if has_terminal_node or has_errant:
        return []
    return ["l3_complete_without_verified_terminal: activated>0 且 L3 "
            "complete 但无可验证终点（仅 inj→addr_form→mem_req 不算"
            "完整；须 resp/taint_reg/consumer/errant_commit 或完整下游"
            "扫描证明的 terminal_reason——中央纠偏指令 2026-10-13 二轮"
            "规则 2）"]


def _rule_l3_terminal_from_l2(obs):
    """R12（二轮规则 3）：L3 终点/errant 证据来源于 L2 timing divergence
    而非 prop_trace 节点 → 强制 FAIL。结构判据：L3 evidence 宣称
    first_errant_commit/terminal 但无 prop_trace 关联键
    （node_id/dyn_inst_seq/ptag）——纯 seq 对齐 L2 即为冒充。"""
    l3 = obs.get("L3") or {}
    l3ev = l3.get("evidence") or {}
    if l3.get("method") != "propagation_trace":
        return []
    claims = []
    fe = l3ev.get("first_errant_commit")
    term = l3ev.get("terminal")
    for label, node in (("first_errant_commit", fe), ("terminal", term)):
        if not isinstance(node, dict):
            continue
        has_pt_keys = any(k in node for k in
                          ("node_id", "dyn_inst_seq", "ptag", "tick"))
        if not has_pt_keys:
            claims.append(label)
    if claims:
        return ["l3_terminal_from_l2: L3 终点证据 " + "/".join(claims)
                + " 无 prop_trace 关联键（node_id/dyn_inst_seq/ptag/tick）"
                "——疑似 L2 timing divergence 冒充 L3 传播终点（中央纠偏"
                "指令 2026-10-13 二轮规则 3）"]
    return []


def _rule_l0_l5_funnel_inconsistent(obs):
    """R13（二轮规则 6）：L0 attempted/eligible 有真实值而 L5 为 null
    （未经同源回填）→ 强制 FAIL；两侧均有值且不等 → FAIL。"""
    l0, l5 = obs.get("L0") or {}, obs.get("L5") or {}
    reasons = []
    for k in ("attempted", "eligible"):
        l0v, l5v = l0.get(k), l5.get(k)
        if l0v is not None and l5v is None:
            reasons.append(f"l0_l5_funnel_inconsistent: L0.{k}={l0v} 有"
                           f"真实值而 L5.{k}=null（须同源回填或审计 FAIL"
                           f"——中央纠偏指令 2026-10-13 二轮规则 6）")
        elif l0v is not None and l5v is not None and l0v != l5v:
            reasons.append(f"l0_l5_funnel_inconsistent: L0.{k}={l0v} != "
                           f"L5.{k}={l5v}（漏斗源冲突）")
    return reasons


def _rule_schema_version(obs):
    """R7：schema 须为 lsu-observation-v2；v1 样本按 v2 规则如实 FAIL。"""
    if obs.get("schema") == SCHEMA_V2:
        return []
    return [f"schema_version_pre_correction: schema={obs.get('schema')!r} != "
            f"{SCHEMA_V2!r}（纠偏前历史样本，按 v2 规则如实 FAIL——中央"
            f"知情且期望的行为，不静默降级；中央纠偏指令 2026-10-13 规则 7）"]


def _rule_contract_v2_fields(obs):
    """R8：v2 契约顶层四字段缺失（或类型不符）→ FAIL。"""
    reasons = []
    for k, typ in V2_TOP_FIELDS:
        if k not in obs:
            reasons.append(f"contract_v2_fields_missing: {k}（v2 契约顶层"
                           f"字段缺失——中央纠偏指令 2026-10-13 规则 8）")
        elif not isinstance(obs[k], typ):
            reasons.append(f"contract_v2_fields_bad_type: {k} 须为 "
                           f"{typ.__name__}，实录 {type(obs[k]).__name__}")
    return reasons


def _rule_l4_detector_v1_value(obs):
    """R9：L4.detector 须为 "not_present"；"none_wired" 是 v1 值 →
    schema_version 类 FAIL（同 R7 处理）。"""
    l4 = obs.get("L4") or {}
    if l4.get("detector") == "none_wired":
        return ["L4_detector_v1_value_none_wired: L4.detector='none_wired' "
                "为 v1 值（v2 契约须为 'not_present'）——schema_version 类"
                " FAIL，同规则 7 处理（中央纠偏指令 2026-10-13 规则 9）"]
    return []


def _v1_chain_complete(o):
    """v1 历史规则重算（升级前 lsu_obs_core.chain_complete 的逐字复现）。

    纠偏集成裁决（主负责人，2026-10-13）：OC.chain_complete 已被 Sub-B 升级为
    v2 语义（拒 proxy/L0 四字段全查）——v1 复现路径必须**自包含**，不得 import
    生产者，否则 v1 模式随生产者升级漂移（合并实测：s3/s10 在 v1 模式被
    v2 语义误判 mismatch）。v1 规则 = violations / L0 injected None / L5 无效 /
    replay 未验证 / inactive N/A / activated>0 时 L1/L2/L4 诚实终态 + L3
    status=complete（**不查 method**——v1 接受 proxy 口径，正是纠偏对象）。
    """
    if o.get("violations"):
        return False, "violations present: " + "; ".join(o["violations"][:3])
    l0, l5 = o.get("L0") or {}, o.get("L5") or {}
    if l0.get("injected") is None:
        return False, "L0 funnel missing"
    if l5.get("outcome") in (None, "INCONCLUSIVE"):
        return False, "L5 无有效结局"
    if not (o.get("replay_determinism") or {}).get("verified"):
        return False, "replay determinism 未验证"
    if not l0.get("activated"):
        for lv in ("L1", "L2", "L3", "L4"):
            if (o.get(lv) or {}).get("status") != "N/A(inactive_no_activation)":
                return False, f"activated=0 但 {lv} 非 N/A(inactive)"
        return True, "inactive 样本：L0/L5 完整，L1-L4 N/A(inactive)"
    ok_states = {"complete", "not_observed_before_crash",
                 "not_observed_before_timeout"}
    for lv in ("L1", "L2", "L4"):
        if (o.get(lv) or {}).get("status") not in ok_states:
            return False, f"{lv} status={(o.get(lv) or {}).get('status')}"
    if (o.get("L3") or {}).get("status") != "complete":
        return False, f"L3 {(o.get('L3') or {}).get('status')}"
    return True, "L0-L5 complete"


def _v2_chain_complete(o):
    """v2 完整链重算（审计器独立推导，不 import 生产者 v2 实现）。

    纠偏集成裁决（主负责人，2026-10-13，按冻结契约）：chain_complete=层级规则，
    execution_complete/evidence_complete/needs_backfill 为**独立轴**不合取
    （四状态拆分的目的即各轴独立；额外合取对真实 final 样本全部冗余——
    gem5_exit 恒存在、needs_backfill/evidence 由层级规则蕴含——只会制造
    边缘分歧）。
      * L0 漏斗四字段（attempted/eligible/injected/activated）任一 None
        → False（R2 对偶）
      * activated>0 时 L3 须 status=complete 且 method=propagation_trace
        （proxy/None 不算——R1/R6 对偶）
    """
    if o.get("violations"):
        return False, "violations present: " + "; ".join(o["violations"][:3])
    l0, l5 = o.get("L0") or {}, o.get("L5") or {}
    for k in ("attempted", "eligible", "injected", "activated"):
        if l0.get(k) is None:
            return False, f"L0 funnel incomplete: {k} is None"
    if l5.get("outcome") in (None, "INCONCLUSIVE"):
        return False, "L5 无有效结局"
    if not (o.get("replay_determinism") or {}).get("verified"):
        return False, "replay determinism 未验证"
    if not l0.get("activated"):
        for lv in ("L1", "L2", "L3", "L4"):
            if (o.get(lv) or {}).get("status") != "N/A(inactive_no_activation)":
                return False, f"activated=0 但 {lv} 非 N/A(inactive)"
        return True, "inactive 样本：L0/L5 完整，L1-L4 N/A(inactive)"
    ok_states = {"complete", "not_observed_before_crash",
                 "not_observed_before_timeout"}
    for lv in ("L1", "L2", "L4"):
        if (o.get(lv) or {}).get("status") not in ok_states:
            return False, f"{lv} status={(o.get(lv) or {}).get('status')}"
    l3 = o.get("L3") or {}
    if l3.get("status") != "complete" or l3.get("method") != "propagation_trace":
        return False, (f"L3 status={l3.get('status')} method="
                       f"{l3.get('method')}（v2 须 propagation_trace）")
    # 二轮规则 1/2（与 obs_core.chain_complete 同契约，独立实现零漂移对齐）
    l3ev = l3.get("evidence") or {}
    if not l3ev.get("terminal_verified", True):
        return False, "L3 无可验证终点（二轮规则 2）"
    if not l3ev.get("path_complete", False):
        return False, "L3.path_complete=false（二轮规则 1：activated>0 默认 false）"
    return True, "L0-L5 complete (v2: L3 propagation_trace 抵达错误提交)"


# ---------------------------------------------------------------- mode 1
def _v1_check_fault_traces(d, obs, ident, reasons, notes):
    """v1 检查 (v)（历史复现，--rules v1 专用；v2 模式由规则 R3 取代）。

    activated>0 且 full → fault trace 存在且可探 + 截断诚实性。
    """
    d = Path(d)
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
            # 空/不可读 fault trace 的合法情形（2026-10-12 E2E s416 实证）：
            # 层级状态为 not_observed_before_crash/_timeout 时，0 字节
            # ctrace 是 W2.1 生产者 FLUSH_EVERY 批量刷盘契约的诚实结果
            # （abort 早于首个刷盘点；lsu_obs_core.build_l2 前置守卫同步
            # 修复）——记 note 不判 FAIL。其余状态（complete 等）仍 FAIL。
            lv_status = (obs.get(lv) or {}).get("status")
            if rp["error"] in ("file missing", "empty file") \
                    or (rp["error"] or "").startswith("unreadable"):
                if lv_status in NOT_OBSERVED_STATES:
                    notes.append(f"{lv}_fault_empty_under_not_observed: "
                                 f"{rp['error']}（生产者批量 flush 契约的"
                                 f"诚实结果，见层级 note）")
                else:
                    reasons.append(f"{lv}_fault_unreadable: {rp['error']}")
            if lv == "L2" and rp["truncated"]:
                cd = (obs.get("L2") or {}).get("commit_diff") or {}
                if cd.get("verdict") == "no_divergence":
                    reasons.append(
                        "L2_truncated_reported_no_divergence: 截断 fault "
                        "trace 绝不允许记为 no_divergence（须 "
                        "truncated_no_divergence_in_prefix / diverged / "
                        "not_observed_before_*）")


def audit_sample_dir(d, rules_version=RULES_DEFAULT):
    """审计一个含 COMPLETE 的样本目录（只读）。返回审计记录 dict。

    rules_version="v2"（默认）：基础检查 (i)-(iv)/(vi) + 规则 R1-R9 +
    chain_complete 用 _v2_chain_complete 重算（v2 契约样本）。
    rules_version="v1"：升级前行为逐字复现（检查 (v) 原路径，无 R1-R9）。
    """
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
        return {"sample": d.name, "rules_version": rules_version,
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

    # (iii) chain_complete 重算一致（纠偏集成裁决 2026-10-13）：
    #   rules=v1 → 全部用自包含 _v1_chain_complete（历史逐字复现，不随
    #   生产者 OC.chain_complete 的 v2 升级漂移）
    #   rules=v2 → v1 契约样本（存储值由 v1 生产者计算）用 _v1；
    #              v2 契约样本用审计器独立 _v2_chain_complete
    stored = obs.get("chain_complete")
    if rules_version == RULES_V1 or obs.get("schema") != SCHEMA_V2:
        recomputed, why = _v1_chain_complete(obs)
    else:
        recomputed, why = _v2_chain_complete(obs)
    if stored != recomputed:
        reasons.append(f"chain_complete_recompute_mismatch: stored={stored} "
                       f"recomputed={recomputed} ({why})")

    # (iv) 状态合法枚举
    for lv, legal in (("L1", L1L2_LEGAL), ("L2", L1L2_LEGAL),
                      ("L3", L3_LEGAL), ("L4", L4_LEGAL)):
        st = (obs.get(lv) or {}).get("status")
        if st not in legal:
            reasons.append(f"{lv}_status_illegal: {st!r}")

    # (v)/(R3) fault/ref trace 探查：v2 = 规则 R3（含 ref 侧 + 记录态 error
    #         + 现场复核 + W2.1 空例外 + v.b）；v1 = 原检查 (v)（历史复现）
    if rules_version == RULES_V2:
        r3_reasons, r3_notes = _rule_evidence_trace_unreadable(d, obs, ident)
        reasons.extend(r3_reasons)
        notes.extend(r3_notes)
    else:
        _v1_check_fault_traces(d, obs, ident, reasons, notes)

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

    # 规则集 v2：R1-R9 聚合（每规则独立检查器，便于测试与后续扩展）
    if rules_version == RULES_V2:
        reasons.extend(_rule_l3_unsupported_for_activated(obs))
        reasons.extend(_rule_l0_funnel_incomplete(obs))
        reasons.extend(_rule_empty_trace_fake_divergence(obs))
        reasons.extend(_rule_detector_na_counted_as_detected(obs))
        reasons.extend(_rule_chain_complete_with_degraded_layer(obs))
        reasons.extend(_rule_path_complete_false_chain_true(obs))
        reasons.extend(_rule_l3_complete_without_terminal(obs))
        reasons.extend(_rule_l3_terminal_from_l2(obs))
        reasons.extend(_rule_l0_l5_funnel_inconsistent(obs))
        reasons.extend(_rule_schema_version(obs))
        reasons.extend(_rule_contract_v2_fields(obs))
        reasons.extend(_rule_l4_detector_v1_value(obs))

    missing = [lv for lv in ("L1", "L2", "L3", "L4")
               if (obs.get(lv) or {}).get("status") not in COVERAGE_COLLECTED]
    return {"sample": d.name, "rules_version": rules_version,
            "missing_layers": missing,
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


def audit_campaign_root(root, rules_version=RULES_DEFAULT):
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
                    records.append(audit_sample_dir(sub, rules_version))
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
        "rules_version": rules_version,
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
    """模式 2：旧 pilot 样本（只读）。每样本 = outcome 完整、L1-L4 未采集。

    不受 v2 规则影响（旧样本无 observation.json，只有台账标记）。
    """
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


# ---------------------------------------------------------------- self-check
def _sc_ctr_line(seq):
    return (f"{seq},0,{100 + seq},400080,add,1,1,5,66,"
            f"000000000000000{seq % 10}")


def _sc_write_gz(path, lines):
    with gzip.open(path, "wt") as f:
        for l in lines:
            f.write(l + "\n")


def _sc_build_valid_v2_sample(camp, s=0):
    """合成一个合规 v2 契约样本（控制组）：L3 complete+propagation_trace、
    L4 detector=not_present、漏斗四字段齐全、轨迹文件真实可读、seed 一致。
    绝不依赖生产者 v2 实现——纯手工按契约构造；只写系统临时目录。"""
    item = "ITEM-901"
    d = camp / item / f"{item}_s{s}"
    d.mkdir(parents=True, exist_ok=True)
    runid, phase = "SC01-F0-W1", "screening"
    ref_lines = [_sc_ctr_line(i) for i in range(6)]
    fault_lines = list(ref_lines)
    fault_lines[3] = _sc_ctr_line(3).replace("0000000000000003",
                                             "ffffffffffffffff")
    _sc_write_gz(d / "ref_commit_trace.csv.gz", ref_lines)
    _sc_write_gz(d / "ref_micro_snap.csv.gz", [f"snap,{i}" for i in range(4)])
    _sc_write_gz(d / "commit_trace.csv.gz", fault_lines)
    _sc_write_gz(d / "micro_snap.csv.gz", [f"snap,{i}" for i in range(4)])
    (d / "gem5.out").write_text(
        "CHAOS_LSU_TRIGGER: freq-based attempted=1 eligible=265143 "
        "injected=1 activated=1\n...sim_exit...\n")
    (d / "addrpath_injections.log").write_text(
        "Tick: 887040, Site: lsq_sendFragmentToTranslation, "
        "mode=low_bit_flip, old_vaddr=0x7ffffefd00, "
        "new_vaddr=0x87ffffefd00, faults_injected: 1\n")
    l5 = {"outcome": "SDC", "activated": 1, "injected": 1,
          "crash_kind": None, "timed_out": False, "detected_na": True,
          "checksum": "0123456789abcdef",
          "classes": {"Masked": 0, "Detected/Contained": 0, "SDC": 1,
                      "Crash": 0, "Timeout": 0},
          "conservation": "OK", "first_detection_source": "None"}
    (d / "l5_verdict.json").write_text(
        json.dumps(l5, ensure_ascii=False, indent=1))

    def probe(name):
        p = d / name
        return {"path": name, "bytes": p.stat().st_size, "rows": 6,
                "truncated": False, "readable": True, "error": None}

    names = ["addrpath_injections.log", "commit_trace.csv.gz",
             "micro_snap.csv.gz", "gem5.out", "l5_verdict.json",
             "ref_commit_trace.csv.gz", "ref_micro_snap.csv.gz"]
    files = [{"name": n, "path": n, "sha256": OC.sha256_file(d / n),
              "bytes": (d / n).stat().st_size} for n in names]
    obs = {
        "schema": SCHEMA_V2,
        "identity": {
            "campaign": "selfcheck", "item": item, "runid": runid,
            "sample": f"s{s}", "seed": lsu_seed(runid, phase, s),
            "phase": phase, "git_commit": "a" * 40,
            "gem5_opt_sha256": "b" * 64, "lsu_proxy_sha256": "c" * 64,
            "workload": "se:gap_bfs", "workload_sha256": "d" * 64,
            "config_family": "C4-LSU", "pythonhashseed": 0,
            "baseline_key": "e" * 32, "obs_mode": "full",
            "coverage_scope": "full_run"},
        "L0": {"attempted": 1, "eligible": 265143, "injected": 1,
               "activated": 1, "funnel_source": "stdout",
               "injections": [{"tick": 887040,
                               "site": "lsq_sendFragmentToTranslation",
                               "mode": "low_bit_flip", "faults": 1,
                               "field": "vaddr->vaddr",
                               "old": "0x7ffffefd00", "new": "0x87ffffefd00",
                               "dynamic_target": "vaddr", "raw": "..."}]},
        "L1": {"status": "complete", "ref": probe("ref_micro_snap.csv.gz"),
               "fault": probe("micro_snap.csv.gz"),
               "micro_diff": {"no_divergence": False,
                              "first_divergence_snap_seq": 2}},
        "L2": {"status": "complete", "ref": probe("ref_commit_trace.csv.gz"),
               "fault": probe("commit_trace.csv.gz"),
               "commit_diff": {"verdict": "diverged", "primary_class":
                               "value_error", "latency_seq": 3,
                               "first_errant_commit": {"seq": 3,
                                                       "class": "value_error",
                                                       "tick": 103},
                               "total_divergence_points": 1,
                               "divergence_counts": {"value_error": 1},
                               "tick_tol": 0, "aligned_pairs": 6,
                               "ref_instructions": 6, "run_instructions": 6,
                               "ref_truncated": False,
                               "run_truncated": False, "aux": {}}},
        "L3": {"status": "complete", "method": "propagation_trace",
               "correlation_keys": ["dynInstSeqNum", "request_id", "ptag"],
               "evidence": {"path_complete": True,
                            "terminal_verified": True,
                            "terminal": {"kind": "errant_commit",
                                         "node_id": 11, "dyn_inst_seq": 415,
                                         "tick": 103},
                            "terminal_reason": None,
                            "first_errant_commit": {"node_id": 11,
                                                    "dyn_inst_seq": 415,
                                                    "tick": 103}},
               "caveats": []},
        "L4": {"status": "complete", "detector": "not_present",
               "detected": False, "detected_na": True,
               "l4_source": "first_verifiable_anomaly",
               "first_anomaly": {"source": "L2", "tick": 103, "seq": 3,
                                 "latency_ticks_from_first_injection": 0}},
        "L5": {**l5, "attempted": 1, "eligible": 265143},
        "replay_determinism": {"policy": "per_sample", "verified": True,
                               "evidence": {}},
        "violations": [], "degradations": [], "files": files,
        "chain_complete": True,
        "chain_status_reason": "L0-L5 complete (v2: L3 propagation_trace)",
        "execution_complete": True, "evidence_complete": True,
        "needs_backfill": False, "missing_levels": [],
    }
    return d, obs


def _sc_finalize(d, obs):
    """写 observation.json + COMPLETE（sha 对齐），返回审计记录。"""
    (d / "observation.json").write_text(
        json.dumps(obs, ensure_ascii=False, indent=1))
    (d / OC.COMPLETE).write_text(json.dumps({
        "finalized_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "schema": obs.get("schema"),
        "observation_sha256": OC.sha256_file(d / "observation.json"),
        "git_commit": (obs.get("identity") or {}).get("git_commit"),
        "baseline_key": (obs.get("identity") or {}).get("baseline_key"),
    }, ensure_ascii=False, indent=1) + "\n")
    return audit_sample_dir(d, rules_version=RULES_V2)


def _sc_violation(base_dir, base_obs, tmp, name, patch):
    """拷贝控制组样本 → patch(obs, d)（可改 obs 与盘上文件）→ 重新对齐
    files sha / COMPLETE sha → 审计。返回审计记录。"""
    d = tmp / "violations" / name
    shutil.copytree(base_dir, d)
    obs = json.loads(json.dumps(base_obs))     # 深拷贝
    # 路径改写：控制组 obs 的相对路径在新目录下依旧成立（同名样本目录）
    patch(obs, d)
    for fe in obs.get("files", []):
        fp = Path(fe["path"])
        if not fp.is_absolute():
            fp = d / fp
        if fp.exists():
            fe["sha256"] = OC.sha256_file(fp)
            fe["bytes"] = fp.stat().st_size
    return _sc_finalize(d, obs)


def self_check():
    """--self-check：完整性检查器有效性证明（中央纠偏指令 2026-10-13）。

    对每条 v2 规则（R1-R9，R5 双条款）各构造一个违规合成样本，断言审计器
    FAIL 且 reason 含对应规则 token；另构造一个合规 v2 样本断言 PASS（控制
    组——证明检查器不是无条件 FAIL）。全部在 tempfile.mkdtemp 合成树上
    完成：不跑 gem5、不触碰任何真实 runs/ 目录。
    """
    tmp = Path(tempfile.mkdtemp(prefix="lsu_audit_selfcheck_"))
    fails = []
    print(f"[self-check] 合成树: {tmp}")

    base_dir, base_obs = _sc_build_valid_v2_sample(tmp / "camp")
    ctrl = _sc_finalize(base_dir, json.loads(json.dumps(base_obs)))
    ok = ctrl["audit"] == "PASS" and not ctrl["reasons"]
    print(("PASS" if ok else "FAIL"), "control_valid_v2_sample_passes")
    if not ok:
        fails.append("control")
        print("   ", json.dumps(ctrl, ensure_ascii=False))

    def p_r1(obs, d):
        obs["L3"] = {"status": "unsupported", "method": None,
                     "reason": "非 PRF 家族（selfcheck 合成）"}
        obs["missing_levels"] = ["L3"]
        ok_, why = _v2_chain_complete(obs)
        obs["chain_complete"], obs["chain_status_reason"] = ok_, why

    def p_r2(obs, d):
        obs["L0"]["attempted"] = None
        obs["missing_levels"] = ["L0"]
        ok_, why = _v2_chain_complete(obs)
        obs["chain_complete"], obs["chain_status_reason"] = ok_, why

    def p_r3(obs, d):
        (d / "commit_trace.csv.gz").write_bytes(b"")   # 现场变空文件

    def p_r4(obs, d):
        obs["L2"]["fault"]["rows"] = 0
        obs["L2"]["fault"]["error"] = "empty file"
        obs["L2"]["fault"]["bytes"] = 0
        obs["L2"]["commit_diff"]["verdict"] = "diverged"
        obs["L2"]["commit_diff"]["total_divergence_points"] = 3

    def p_r5a(obs, d):
        obs["L5"]["classes"]["Detected/Contained"] = 1

    def p_r5b(obs, d):
        obs["L4"]["detected"] = True

    def p_r6(obs, d):
        obs["missing_levels"] = ["L4"]      # 存储值声称缺层但 chain 仍 True

    def p_r7(obs, d):
        obs["schema"] = SCHEMA_V1

    def p_r8(obs, d):
        del obs["needs_backfill"]

    def p_r9(obs, d):
        obs["L4"]["detector"] = "none_wired"

    cases = [
        ("R1_L3_unsupported_for_activated", p_r1,
         "L3_unsupported_for_activated_sample"),
        ("R2_L0_funnel_incomplete", p_r2, "L0_funnel_incomplete"),
        ("R3_evidence_trace_unreadable", p_r3, "evidence_trace_unreadable"),
        ("R4_empty_trace_fake_divergence", p_r4,
         "empty_trace_fake_divergence"),
        ("R5a_detector_na_counted_as_detected", p_r5a,
         "detector_na_counted_as_detected"),
        ("R5b_detector_na_counted_as_detected", p_r5b,
         "detector_na_counted_as_detected"),
        ("R6_chain_complete_with_degraded_layer", p_r6,
         "chain_complete_with_degraded_layer"),
        ("R7_schema_version_pre_correction", p_r7,
         "schema_version_pre_correction"),
        ("R8_contract_v2_fields_missing", p_r8,
         "contract_v2_fields_missing"),
        ("R9_L4_detector_v1_value_none_wired", p_r9,
         "L4_detector_v1_value_none_wired"),
    ]
    for name, patch, token in cases:
        rec = _sc_violation(base_dir, base_obs, tmp, name, patch)
        hit = rec["audit"] == "FAIL" and any(token in x
                                             for x in rec["reasons"])
        print(("PASS" if hit else "FAIL"), f"selfcheck_{name}")
        if not hit:
            fails.append(name)
            print("   ", json.dumps(rec, ensure_ascii=False))
        else:
            print("    reason:", next(x for x in rec["reasons"]
                                     if token in x)[:160])

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"[self-check] {'全部检出' if not fails else '未检出: ' + str(fails)}")
    return 0 if not fails else 1


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
    ap.add_argument("--rules", choices=(RULES_V1, RULES_V2),
                    default=RULES_DEFAULT,
                    help=f"规则集：v2=六条强制 FAIL 规则+三条附加（默认）；"
                         f"v1=历史审计行为复现（无 R1-R9）")
    ap.add_argument("--self-check", action="store_true",
                    help="自检：对每条 v2 规则构造违规合成样本，断言审计器"
                         " FAIL（完整性检查器有效性证明；不触碰真实 runs/）")
    ap.add_argument("--json", default=None,
                    help="汇总+逐样本记录 JSON 输出路径（绝不写在被审计树内）")
    args = ap.parse_args()

    if args.self_check:
        if args.campaign_root or args.legacy_root:
            ap.error("--self-check 不能与 --campaign-root/--legacy-root 同用")
        return self_check()

    if not args.campaign_root and not args.legacy_root:
        ap.error("需要 --campaign-root（模式 1）或 --legacy-root --item（模式 2）"
                 "或 --self-check")
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
        res = audit_campaign_root(args.campaign_root, args.rules)
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

    # 模式 2（legacy，只读；不受规则集影响）
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
                       ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        print(f"[json] {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
