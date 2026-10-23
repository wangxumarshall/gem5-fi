#!/usr/bin/env python3
"""lsu_chain_check.py — [MDSPEC][C1] L0→L5 传播链完整性检查器。

规格（表 9 完整性/传播终止判定列，全部 RunID 共文）：
"完整：存在 L0 fault_applied，且每条边由共享键与时间/可达性同时证明，最终
到达 (1) errant commit/错误内存副作用/软件 oracle 差异，或 (2) 明确检测并
contained，或 (3) 明确 squash/replay/mask 且无错误副作用。若链在某节点后
缺事件，只能标'截至该节点可证，后续 Unknown'，不得推断 Masked。"

实现（计划 Task C1 Interfaces）：
- check_chain(events, spec_nodes=None) → {edges, terminal}
- 边证明规则：必须在 parent_event_id DAG 的**同一条祖先路径**上依次
  找到 L0,L1,...；所选事件 tick 单调。禁止把两个分支或乱序阶段上的
  独立证人拼成一条链。
- TLB family 使用表 9 专用层级：L1 只认 tlb_lookup；下游
  cache_access 属 L3，绝不能冒充 DTLB lookup。
- 终止判定：
  * full                    —— L0→L5 全边 proven，且同一祖先链包含
                                errant_commit 与**真实检测事件**（[R6-GATE-D1]
                                非生命周期 kind + detection_layer + outcome +
                                链关联 corr；生命周期 chain_end 永不充当 L5）
  * provable_to_Ln_then_unknown —— 在 Ln 后缺事件（绝不推断 Masked）
  * detected_contained      —— 存在显式 detection_layer 事件且 contained=1
  * squash_replay_masked    —— 存在显式 squash/replay/mask 证据事件
  （后两者只认显式事件，缺席不猜测——诚实纪律）
- L5（检测/结局）事件当前由 runner/reclass 离线 join 产出；PROP-EVT 流内
  无 L5 kind 时链至 L4 止，L4→L5 标 missing（→ Unknown，非 Masked）。

用法：python3 tools/lsu_chain_check.py <prop_evt.txt[.gz]> [--run-id X]
（退出码 0=检查完成；结果打印 JSON；对多 fault_id 分别判定）
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lsu_prop_fields as P  # noqa: E402

# 规格层级序（表 9 传播路径：L0 注入 → L1 单元内部 → L2 请求/翻译 →
# L3 cache/内存 → L4 架构可见 → L5 检测/结局）
LAYERS = ["L0", "L1", "L2", "L3", "L4", "L5"]

# [R6-GATE-D1] L5 = 检测/结局层。它的**唯一**合法证据是"真实检测事件"：
# 一个非生命周期 kind 的事件，同时携带 非空 detection_layer、非空 outcome、
# 以及链关联 corr（即该事件确实由 correlate*/污染集成员关系关联进本故障链）。
# chain_end 由 CHAOSPropagation 退出回调发射，是**链生命周期标记**（规范
# 词汇表 _CORR 中 corr=none，无关联语义），故结构性**永不**充当 L5：它不占
# 任何层级（_layer_of → None）。这样 ready_by_chain_end_only 由构造堵死，
# 而不再只是一条文案（D1）。真实流实证：T04/T02 的 chain_end 为
# outcome=errant_commit_seen / detection_layer=None / corr=none，其真实检测
# 点是 errant_commit（未富化 ⇒ 只到 L4）；T05/T08 的 tlb_translate_result 才
# 是带 dl+contained+outcome+corr 的真实检测事件。
_LIFECYCLE_KINDS = frozenset({"chain_end"})

# 链关联 corr 取值（lsu_prop_fields.CORR_VALUES 去掉生命周期值 "none"）。
_CHAIN_CORR = frozenset({"seq_primary", "addr_fallback", "origin",
                         "taint_prop"})

_EMPTY_DETECTION = ("", "None", "none", "Unknown", "unknown")
_EMPTY_OUTCOME = ("", "run_end", "unknown", "Unknown")


def _explicit_l5(evt):
    """真实检测事件 = 非生命周期 kind + detection_layer + outcome + 链关联 corr。

    生命周期 chain_end 恒为 False（corr=none）——这是 D1 的结构性保证。
    """
    if evt.get("kind", "") in _LIFECYCLE_KINDS:
        return False
    if str(evt.get("detection_layer", "")).strip() in _EMPTY_DETECTION:
        return False
    if str(evt.get("outcome", "")).strip() in _EMPTY_OUTCOME:
        return False
    return str(evt.get("corr", "")).strip() in _CHAIN_CORR


_L4_TERMINAL_KINDS = {"errant_commit"}  # L4 终局：首个错误提交（v1/H0）

# 闭合终局（链已收敛 → beyond=""）。其余（provable_to_*_then_unknown /
# detected_translation_outcome_pending / no_l0_fault_applied）为开放终局，
# beyond="Unknown"。此集合与 _terminal 的返回值必须一致——
# tests/test_lsu_chain_check.py 钉死该自洽性。
CLOSED_TERMINALS = {
    "full",
    "detected_contained",
    "squash_replay_masked",
    "crash_translation_blocked",
    "timeout_translation_blocked",
    "sdc_translation_blocked",
}


_TLB_SIGNATURE_KINDS = {
    "tlb_lookup", "tlb_pfn", "tlb_state", "tlb_walk", "tlb_refill",
    "tlb_translate_result",
}

_TLB_KIND_LAYER = {
    "inj": "L0",
    "tlb_lookup": "L1",
    "tlb_pfn": "L2", "tlb_state": "L2", "tlb_walk": "L2",
    "tlb_refill": "L2", "tlb_translate": "L2",
    "tlb_translate_result": "L2", "tlb_fault": "L2",
    # Table 9 T-series L3 is the request/cache/memory side after translation.
    "lsq_sendfrag": "L3", "mem_req": "L3", "lq_read": "L3",
    "lq_complete": "L3", "sq_execute": "L3", "sq_writeback": "L3",
    "sq_complete": "L3", "resp": "L3", "cache_access": "L3",
    "cache_return": "L3", "cache_fill": "L3", "cache_evict": "L3",
    "mshr_alloc": "L3", "mshr_merge": "L3", "mshr_fill": "L3",
    "mshr_free": "L3", "cache_writeback": "L3",
    "taint_reg": "L4", "consumer": "L4", "errant_commit": "L4",
    "chain_end": "L5",
}


def _family_of(chain_events):
    """Infer only families whose table-9 path differs from the global map."""
    for evt in chain_events:
        run_id = evt.get("run_id", "")
        if run_id.startswith("T") or evt.get("kind", "") in _TLB_SIGNATURE_KINDS:
            return "tlb"
    return "generic"


def _obs_layer_of(evt, family="generic"):
    """Observation layer of a kind (family-specific map).  Independent of the
    D1 L5 promotion below, so prefix proofs keep working for detection
    events (whose observation layer is L2 for the T-series)."""
    kind = evt.get("kind", "")
    if family == "tlb":
        return _TLB_KIND_LAYER.get(kind)
    return P.KIND_LAYER.get(kind)


def _layer_of(evt, family="generic"):
    # [R6-GATE-D1] 生命周期 chain_end 不占任何层级；真实检测事件占 L5
    # （检测/结局层，spec 表 9 "L5 检测/结局"）。
    if evt.get("kind", "") in _LIFECYCLE_KINDS:
        return None
    if _explicit_l5(evt):
        return "L5"
    return _obs_layer_of(evt, family)


def _tick(evt):
    try:
        return int(evt.get("tick", "0") or 0)
    except ValueError:
        return 0


def _group_by_fault(events):
    """按 fault_id 分组（fault_id=0 的非链事件不参与链证明）。"""
    groups = {}
    for e in events:
        fid = e.get("fault_id", "")
        if not fid or fid == "0":
            continue
        groups.setdefault(fid, []).append(e)
    return groups


def _ancestry(evt, by_id):
    """Return root→evt along parent_event_id; cycles/missing parents stop."""
    out = []
    seen = set()
    cur = evt
    while cur is not None:
        eid = cur.get("event_id", "")
        marker = eid if eid != "" else id(cur)
        if marker in seen:
            break
        seen.add(marker)
        out.append(cur)
        parent = cur.get("parent_event_id", "")
        cur = by_id.get(parent) if parent != "" else None
    out.reverse()
    return out


def _ordered_prefix(path, family):
    """Select one tick-monotone L0→... subsequence from one DAG ancestry."""
    selected = []
    want = 0
    last_tick = -1
    for evt in path:
        layer = _layer_of(evt, family)
        if layer not in LAYERS:
            continue
        idx = LAYERS.index(layer)
        tick = _tick(evt)
        if idx == want and tick >= last_tick:
            selected.append(evt)
            want += 1
            last_tick = tick
            if want == len(LAYERS):
                break
    return selected


def _best_ordered_path(chain_events, family):
    """Best contiguous layer prefix on any single parent DAG ancestry."""
    by_id = {e.get("event_id", ""): e for e in chain_events
             if e.get("event_id", "") != ""}
    best = []
    for evt in chain_events:
        selected = _ordered_prefix(_ancestry(evt, by_id), family)
        if len(selected) > len(best):
            best = selected
    return best


def _event_has_prefix(chain_events, target, family):
    """Whether target descends from a contiguous L0..target-layer prefix.

    [R6-GATE-D1] Uses the *observation* layer of the target (not the L5
    promotion) so a detection event is still proven to descend from the
    unit's own L0→L_obs prefix.
    """
    layer = _obs_layer_of(target, family)
    if layer not in LAYERS:
        return False
    target_idx = LAYERS.index(layer)
    by_id = {e.get("event_id", ""): e for e in chain_events
             if e.get("event_id", "") != ""}
    ancestry = _ancestry(target, by_id)
    selected = _ordered_prefix(ancestry, family)
    return len(selected) > target_idx


def _edges_for(chain_events, family):
    """Prove edges only from one contiguous, tick-monotone DAG path."""
    path = _best_ordered_path(chain_events, family)
    by_layer = {}
    for evt in path:
        by_layer[_layer_of(evt, family)] = [evt]
    edges = {}
    for i in range(len(LAYERS) - 1):
        a, b = LAYERS[i], LAYERS[i + 1]
        proven = len(path) > i + 1
        edges[f"{a}->{b}"] = "proven" if proven else "missing"
        if proven:
            e1, e2 = path[i], path[i + 1]
            shared = ["fault_id", "parent_event_path"]
            if (e1.get("dyn_inst_seq") and e2.get("dyn_inst_seq")
                    and e1["dyn_inst_seq"] == e2["dyn_inst_seq"]):
                shared.append("dyn_inst_seq")
            edges[f"{a}->{b}_witness"] = {
                "from": f"{a}:{e1.get('kind')}@t{e1.get('tick')}",
                "to": f"{b}:{e2.get('kind')}@t{e2.get('tick')}",
                "shared_keys": shared,
            }
    return edges, by_layer, path


def _terminal(chain_events, edges, by_layer, path, family,
              oracle_outcome=None):
    """终止判定（规格三终局 + Unknown 兜底；缺席不猜测）。

    [H2-fix] tlb_fault = Hardware 检测，表示**翻译阶段阻断**，它本身
    **不是**终局：不得据此无条件写 contained=1。终局由"翻译阻断证据 +
    runner/oracle 结局（L5 五类）"联合决定：

      oracle=Crash/Timeout/SDC  → <kind>_translation_blocked（闭合：确实
                                  产生了错误结局，翻译阻断是其机理）
      oracle=Detected/Contained → detected_contained（闭合）
      oracle=Masked（oracle 干净）→ provable_to_L2_then_unknown
                                  （**绝不**因 oracle 干净就推断 Masked/
                                  Contained —— 规格表 9 判定列钉死）
      oracle 缺失/INCONCLUSIVE  → detected_translation_outcome_pending
                                  （开放，beyond=Unknown）

    "Handled"（guest 自行处理翻译故障后继续）在本事件流内**不可判别**
    ——干净 oracle 无法区分"被吸收"与"没造成影响"，故只能标 Unknown
    （诚实：不引入不可观测的语义）。
    """
    translation_blocked = False
    for e in chain_events:
        if (e.get("kind") == "tlb_fault"
                and e.get("detection_layer") == "Hardware"
                and _event_has_prefix(chain_events, e, family)):
            translation_blocked = True
            if e.get("contained") == "1":
                # 显式 contained 证据（非推断）优先于 oracle 兜底
                return "detected_contained"
    if translation_blocked:
        if oracle_outcome in ("Crash", "Timeout", "SDC"):
            return f"{oracle_outcome.lower()}_translation_blocked"
        if oracle_outcome == "Detected/Contained":
            return "detected_contained"
        if oracle_outcome in ("Masked",):
            # oracle 干净 ≠ 链完整 ≠ Masked：只按可证层级报告
            pass
        else:
            return "detected_translation_outcome_pending"
    # 显式 contained 检测（L5 证据事件）
    for e in chain_events:
        if (e.get("detection_layer") and e.get("contained") == "1"
                and _event_has_prefix(chain_events, e, family)):
            return "detected_contained"
    # 显式 squash/replay/mask（L5 证据事件）
    for e in chain_events:
        if (any(k in e.get("kind", "") for k in ("squash", "replay", "mask"))
                and _event_has_prefix(chain_events, e, family)):
            return "squash_replay_masked"
    # 逐边最深可证层级
    deepest = LAYERS[len(path) - 1] if path else None
    if deepest is None:
        return "no_l0_fault_applied"
    # full（规格终局 1：到达 errant commit + 显式链终局）要求 L0→L5
    # 全路径连续。abort 样本若没有 chain_end，就只能诚实停在 L4；不得
    # 单靠 errant_commit 补造 L5。
    # The ordered prefix records only one representative per layer (often a
    # taint_reg for L4), so inspect the chosen L5 event's ancestry for the
    # errant_commit rather than requiring it to be that representative.  This
    # still forbids cross-branch splicing: both witnesses are on one ancestry.
    l4_terminal = False
    explicit_l5 = False
    if deepest == "L5":
        by_id = {e.get("event_id", ""): e for e in chain_events
                 if e.get("event_id", "") != ""}
        chosen_ancestry = _ancestry(path[-1], by_id)
        l4_terminal = any(e.get("kind") in _L4_TERMINAL_KINDS
                          for e in chosen_ancestry)
        explicit_l5 = _explicit_l5(path[-1])
    if deepest == "L5" and l4_terminal and explicit_l5:
        return "full"
    if deepest == "L0" and not by_layer.get("L1"):
        return "provable_to_L0_then_unknown"
    return f"provable_to_{deepest}_then_unknown"


def check_chain(events, spec_nodes=None, oracle_outcome=None):
    """主入口：events = lsu_prop_fields 解析的事件列表。

    oracle_outcome: runner/分类器的 L5 结局（Masked/Detected/Contained/
    SDC/Crash/Timeout/INCONCLUSIVE），用于把"翻译阶段阻断"join 成终局。
    缺省 None ⇒ 翻译阻断保持 pending（不猜测）。

    返回 {faults: {fault_id: {edges, terminal, provable_to, beyond}},
          spec_nodes, oracle_outcome}。
    """
    result = {"faults": {}, "spec_nodes": spec_nodes or LAYERS,
              "oracle_outcome": oracle_outcome}
    for fid, chain in _group_by_fault(events).items():
        family = _family_of(chain)
        edges, by_layer, path = _edges_for(chain, family)
        term = _terminal(chain, edges, by_layer, path, family, oracle_outcome)
        provable = LAYERS[len(path) - 1] if path else None
        result["faults"][fid] = {
            "edges": edges,
            "terminal": term,
            "provable_to": provable,
            # beyond=Unknown 仅用于开放终局（"可证至 Ln 后未知" / 翻译阻断
            # 待 join）；闭合终局 beyond 为空——链已收敛，无"后续未知"。
            # 绝不 Masked。
            "beyond": "" if term in CLOSED_TERMINALS else "Unknown",
            "event_count": len(chain),
            "family": family,
            "path_event_ids": [e.get("event_id", "") for e in path],
        }
    return result


# ==================================================================== R6-GATE
# Formal-admission HARD GATE (Agent B, R6).  `check_chain` proves edges and
# reports an honest terminal; `check_admission` turns that into a binding
# admission verdict for one *activated* sample so that `ready_contract.json`
# can never mark a RunID READY on the strength of `activated=1`, `RC=0`, or a
# bare `chain_end`.  An activated sample is admitted ONLY IF either
#   (1) a family-specific COMPLETE L0→L5 chain on one parent-event DAG, or
#   (2) propagation stops at a layer with an explicit containment layer +
#       reason + per-layer metrics, and every later layer is N/A(contained).
# Everything else fails LOUDLY with a named rule (see GATE_VIOLATIONS).
GATE_VIOLATIONS = (
    "unknown_in_activated_chain",
    "tlb_l1_faked_by_cache_access",
    "tlb_l1_missing",
    "cross_branch_edge",
    "cross_request_edge",
    "time_reversed_edge",
    "ready_by_activated_only",
    "ready_by_rc0",
    "ready_by_chain_end_only",
    "missing_mandatory_metric",
    "contained_without_later_na",
    "no_closed_chain_and_no_containment",
)

# cache/memory kinds that must never stand in for the TLB family's L1 DTLB
# lookup (table 9 T-series L1 is the post-injection lookup observation).
_FORCED_L1_KINDS = frozenset({
    "cache_access", "cache_return", "cache_fill", "cache_evict",
    "mshr_alloc", "mshr_merge", "mshr_fill", "mshr_free", "mshr_busy",
    "mshr_arb", "cache_writeback",
})

# Per-layer mandatory metrics: a field that MUST be present (non-empty) on the
# layer's witness on the admitted path.  Absence is a LOUD failure, never a
# silent zero.  "default" applies to every family; family keys override.
MANDATORY_METRICS = {
    "default": {
        "L0": ("fault_id", "event_id"),
        "L1": ("event_id",),
        "L2": ("event_id",),
        "L3": ("event_id",),
        "L4": ("event_id",),
        "L5": ("outcome", "detection_layer", "contained"),
    },
    # Table 9 T-series: L1 must carry the DTLB lookup payload, L2 the PA.
    "tlb": {
        "L1": ("event_id", "dyn_inst_seq", "field", "state_before",
               "state_after"),
        "L2": ("event_id", "va"),
    },
}


def _metrics_for(family):
    tbl = dict(MANDATORY_METRICS["default"])
    if family in MANDATORY_METRICS:
        tbl.update(MANDATORY_METRICS[family])
    return tbl


def _has_unknown(events):
    """Any Unknown evidence in an activated sample (mission-forbidden #1)."""
    for e in events:
        if e.get("fault_id", "") in ("", "0"):
            continue
        if e.get("kind") == "unknown":
            return e
        if str(e.get("evidence_status", "")).strip().lower() == "unknown":
            return e
    return None


def _layer_spans(chain_events, family):
    """min/max tick per layer over the whole chain event set."""
    lo, hi = {}, {}
    for e in chain_events:
        layer = _layer_of(e, family)
        if layer not in LAYERS:
            continue
        t = _tick(e)
        if layer not in lo or t < lo[layer]:
            lo[layer] = t
        if layer not in hi or t > hi[layer]:
            hi[layer] = t
    return lo, hi


def _legacy_edge_count(chain_events, family):
    """Edge count a pairwise (DAG-blind) checker would prove: two witnesses of
    adjacent layers are joined whenever their ticks are non-decreasing."""
    lo, hi = _layer_spans(chain_events, family)
    n = 0
    for i in range(len(LAYERS) - 1):
        a, b = LAYERS[i], LAYERS[i + 1]
        if a in lo and b in hi and lo[a] <= hi[b]:
            n += 1
        else:
            break
    return n


def _deepest_index(chain_events, family):
    return max((LAYERS.index(_layer_of(e, family)) for e in chain_events
                if _layer_of(e, family) in LAYERS), default=-1)


def _splice_detected(chain_events, family, path):
    """True when pairwise joining proves more edges than the single DAG path
    can, i.e. the 'chain' is stitched from witness events on different
    branches (mission-forbidden #3, cross-branch case)."""
    dag = len(path) - 1
    if dag >= _deepest_index(chain_events, family):
        return False
    return _legacy_edge_count(chain_events, family) > dag


def _creq_mismatch(e1, e2):
    """Adjacent witnesses claiming different request identities (both stamped,
    non-zero) => cross-request stitch (mission-forbidden #3)."""
    r1 = str(e1.get("request_id", "")).strip()
    r2 = str(e2.get("request_id", "")).strip()
    return (r1 != "" and r2 != "" and r1 != "0" and r2 != "0" and r1 != r2)


def _ancestry_request_breaks(chain_events, family, path):
    """[R6-GATE-D3] Adjacent witnesses on the *chosen ancestry* whose stamped,
    non-zero `request_id` differs.

    The per-edge check below only sees the ≤6 layer representatives, so a
    stream whose DAG walks resp(req=A) → resp(req=B) → … under one fault_id
    slipped through (real T04: event 47 req=304 → event 48 req=310, both L3).
    Walking the whole ancestry catches cross-request stitching anywhere on the
    proven path (mission-forbidden #3).
    """
    if not path:
        return []
    by_id = {e.get("event_id", ""): e for e in chain_events
             if e.get("event_id", "") != ""}
    anc = _ancestry(path[-1], by_id)
    return [(a, b) for a, b in zip(anc, anc[1:]) if _creq_mismatch(a, b)]


def _time_reversed_gap(chain_events, family, path):
    """A deeper-layer witness whose tick precedes the last proven witness =
    reversed-in-time stitch (mission-forbidden #3)."""
    if not path:
        return None
    deepest = _deepest_index(chain_events, family)
    if len(path) - 1 >= deepest:
        return None
    b = LAYERS[len(path)]                 # first missing layer of the prefix
    ta = _tick(path[-1])
    by_layer = {}
    for e in chain_events:
        if _layer_of(e, family) == b:
            by_layer.setdefault(b, []).append(e)
    if any(_tick(e) < ta for e in by_layer.get(b, [])):
        return (f"time_reversed_edge: {b} 见证 tick 早于已证 {LAYERS[len(path) - 1]}"
                f" 见证（{ta}）——逆时拼接禁止")
    return None


def _containment_issues(bundle, run_id):
    """Option-2 containment: returns issue list, or None when not claimed."""
    c = bundle.get("containment")
    if not isinstance(c, dict):
        return None
    issues = []
    layer = str(c.get("layer", ""))
    if layer not in LAYERS:
        issues.append(f"contained_without_later_na: {run_id} containment.layer="
                      f"{layer!r} 非法（须 ∈ {LAYERS}）")
    else:
        later = LAYERS[LAYERS.index(layer) + 1:]
        na = [str(x) for x in (c.get("na_layers") or [])]
        if sorted(na) != sorted(later):
            issues.append(f"contained_without_later_na: {run_id} containment"
                          f".layer={layer} 后续层必须全部 N/A(contained) 且等于"
                          f" {later}，实录 na_layers={na}")
    if not str(c.get("reason", "")).strip():
        issues.append(f"missing_mandatory_metric: {run_id} containment 缺 reason"
                      f"（显式含住理由为必录）")
    m = c.get("metrics")
    if not isinstance(m, dict) or not m:
        issues.append(f"missing_mandatory_metric: {run_id} containment 缺逐层"
                      f"指标 metrics")
    return issues


def _missing_metrics(path, family):
    tbl = _metrics_for(family)
    out = []
    for evt in path:
        layer = _layer_of(evt, family)
        for f in tbl.get(layer, ()):
            if not str(evt.get(f, "")).strip():
                out.append((layer, f, evt.get("kind")))
    return out


def _crutch_violations(res, bundle, events):
    """Name the three forbidden READY crutches when the chain is not admitted."""
    run_id = res["run_id"]
    v = res["violations"]
    v.append(f"no_closed_chain_and_no_containment: {run_id} 既无 family-specific "
             f"L0→L5 完整链，也无显式 containment——不得判 READY")
    v.append(f"ready_by_activated_only: {run_id} activated={bundle.get('activated')}"
             f" 本身不是 READY 依据（须完整链或 containment）")
    if bundle.get("rc") == 0:
        v.append(f"ready_by_rc0: {run_id} RC=0 不是 READY 依据（进程正常退出"
                 f"≠链完整）")
    if any(str(e.get("kind")) == "chain_end" for e in events):
        v.append(f"ready_by_chain_end_only: {run_id} 仅存在 chain_end 事件，"
                 f"不构成 L5 结终局证据——不得据此判 READY")


def check_admission(bundle):
    """Hard gate verdict for ONE activated sample.

    bundle = {run_id, activated, events (PROP-EVT list), [rc],
              [oracle_outcome], [containment]}
    Returns {run_id, applicable, admitted, path, terminal, family,
             path_layers, violations, reasons, n_events}.  `admitted` is True
    only when option (1) or (2) holds AND no violation token fired.
    """
    run_id = str(bundle.get("run_id", "?"))
    try:
        act = int(bundle.get("activated") or 0)
    except (TypeError, ValueError):
        act = 0
    events = list(bundle.get("events") or [])
    res = {"run_id": run_id, "applicable": act > 0, "admitted": None,
           "path": None, "terminal": None, "family": None, "path_layers": [],
           "violations": [], "reasons": [], "n_events": len(events)}
    if act <= 0:
        res["reasons"].append("activated=0：非 activated 样本，门禁不适用")
        return res
    viol = res["violations"]
    u = _has_unknown(events)
    if u is not None:
        viol.append(f"unknown_in_activated_chain: {run_id} activated={act} 存在"
                    f" Unknown 事件 kind={u.get('kind')!r} event_id="
                    f"{u.get('event_id')!r}——activated 样本中任何 Unknown 一律"
                    f"不得 READY")
    verdict = check_chain(events, oracle_outcome=bundle.get("oracle_outcome"))
    faults = verdict["faults"]
    if not faults:
        _crutch_violations(res, bundle, events)
        res["admitted"] = False
        return res
    fid, f = max(faults.items(),
                 key=lambda kv: len(kv[1]["path_event_ids"]))
    family = f["family"]
    res["terminal"] = f["terminal"]
    res["family"] = family
    chain = [e for e in events if e.get("fault_id", "") == fid]
    path = _best_ordered_path(chain, family)
    res["path_layers"] = [_layer_of(e, family) for e in path]

    # (2) TLB L1 impersonation — family-specific, loud.
    if family == "tlb":
        l1 = next((e for e in path if _layer_of(e, family) == "L1"), None)
        l1kind = l1.get("kind") if l1 else None
        if l1kind != "tlb_lookup":
            imp = sorted({e.get("kind") for e in chain
                          if e.get("kind") in _FORCED_L1_KINDS})
            if imp:
                viol.append(f"tlb_l1_faked_by_cache_access: {run_id} TLB 族 L1 "
                            f"必须为 tlb_lookup，实际 L1={l1kind!r}；cache 族事件"
                            f" {imp} 不得冒充 DTLB lookup")
            else:
                viol.append(f"tlb_l1_missing: {run_id} TLB 族缺 tlb_lookup L1"
                            f"（实际 L1={l1kind!r}）")

    # (3) edge stitching integrity — branch / request / time.
    if _splice_detected(chain, family, path):
        viol.append(f"cross_branch_edge: {run_id} fault {fid} 成对拼接比单 DAG "
                    f"路径多证出边——边见证分散在多个分支，禁止跨分支拼接")
    for i in range(len(path) - 1):
        e1, e2 = path[i], path[i + 1]
        lay = f"{LAYERS[i]}->{LAYERS[i + 1]}"
        if _creq_mismatch(e1, e2):
            viol.append(f"cross_request_edge: {run_id} fault {fid} {lay} 见证 "
                        f"request_id 不一致（{e1.get('request_id')!r}≠"
                        f"{e2.get('request_id')!r}）——禁止跨请求拼接")
        if _tick(e2) < _tick(e1):
            viol.append(f"time_reversed_edge: {run_id} fault {fid} {lay} 见证"
                        f"时间倒挂（{_tick(e1)}→{_tick(e2)}）——禁止逆时拼接")
    tr = _time_reversed_gap(chain, family, path)
    if tr:
        viol.append(f"{tr}（{run_id} fault {fid}）")
    # [R6-GATE-D3] 跨请求拼接：整条所选祖先上任意相邻见证 request_id 不一致。
    breaks = _ancestry_request_breaks(chain, family, path)
    if breaks:
        a, b = breaks[0]
        viol.append(f"cross_request_edge: {run_id} fault {fid} 所选祖先上 "
                    f"{len(breaks)} 处相邻见证 request_id 不一致（首例 event "
                    f"{a.get('event_id')}:{a.get('kind')} req="
                    f"{a.get('request_id')!r} → event {b.get('event_id')}:"
                    f"{b.get('kind')} req={b.get('request_id')!r}）——整条祖先"
                    f"禁止跨请求拼接")

    # (4) per-layer mandatory metrics on the proven path — LOUD when missing.
    for layer, field, kind in _missing_metrics(path, family):
        viol.append(f"missing_mandatory_metric: {run_id} fault {fid} {layer} 见证"
                    f" kind={kind!r} 缺必录指标 '{field}'——逐层指标缺失必须"
                    f"响亮失败")

    # (1)/(2) admission decision.
    opt1 = (f["terminal"] == "full")
    cont_issues = _containment_issues(bundle, run_id)
    opt2 = cont_issues is not None and not cont_issues
    if cont_issues:
        viol.extend(cont_issues)
    if opt1:
        res["path"] = "full_chain"
    elif opt2:
        res["path"] = "contained"
    else:
        _crutch_violations(res, bundle, events)
    res["admitted"] = bool((opt1 or opt2) and not viol)
    return res


def main():
    if len(sys.argv) < 2:
        print("usage: lsu_chain_check.py <prop_evt.txt[.gz]> [--run-id X] "
              "[--oracle-outcome Masked|SDC|Crash|Timeout|"
              "Detected/Contained]", file=sys.stderr)
        return 2
    argv = sys.argv[1:]
    oracle = None
    if "--oracle-outcome" in argv:
        i = argv.index("--oracle-outcome")
        oracle = argv[i + 1]
        del argv[i:i + 2]
    path = Path(argv[0])
    events, truncated = P.read_events(path)
    verdict = check_chain(events, oracle_outcome=oracle)
    verdict["truncated_stream"] = truncated
    verdict["total_events"] = len(events)
    print(json.dumps(verdict, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
