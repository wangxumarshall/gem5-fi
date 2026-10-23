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
                                errant_commit 与显式 L5 结局
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

# L5 的显式终局证据 kind：chain_end 由 CHAOSPropagation 退出回调发射
# （gem5 正常退出时每条故障链一条；abort 样本的链终局由离线 reclass join）。
# detected_contained 需要 detection_layer 非空且 contained=1；
# squash_replay_masked 需要 kind 明示 squash/replay/mask。
_L5_OUTCOME_KINDS = {"chain_end"}

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


def _explicit_l5(evt):
    """A lifecycle run_end marker is not detection/outcome evidence."""
    if evt.get("kind") != "chain_end":
        return False
    detection = evt.get("detection_layer", "")
    outcome = evt.get("outcome", "")
    return (evt.get("contained") == "1"
            or detection not in ("", "None", "none", "Unknown", "unknown")
            or outcome not in ("", "run_end", "unknown", "Unknown"))


def _layer_of(evt, family="generic"):
    kind = evt.get("kind", "")
    if kind == "chain_end" and not _explicit_l5(evt):
        return None
    if family == "tlb":
        return _TLB_KIND_LAYER.get(kind)
    return P.KIND_LAYER.get(kind)


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
    """Whether target descends from a contiguous L0..target-layer prefix."""
    layer = _layer_of(target, family)
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
