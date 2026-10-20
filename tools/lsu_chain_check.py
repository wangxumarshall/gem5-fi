#!/usr/bin/env python3
"""lsu_chain_check.py — [MDSPEC][C1] L0→L5 传播链完整性检查器。

规格（表 9 完整性/传播终止判定列，全部 RunID 共文）：
"完整：存在 L0 fault_applied，且每条边由共享键与时间/可达性同时证明，最终
到达 (1) errant commit/错误内存副作用/软件 oracle 差异，或 (2) 明确检测并
contained，或 (3) 明确 squash/replay/mask 且无错误副作用。若链在某节点后
缺事件，只能标'截至该节点可证，后续 Unknown'，不得推断 Masked。"

实现（计划 Task C1 Interfaces）：
- check_chain(events, spec_nodes=None) → {edges, terminal}
- 边证明规则：相邻层级 Ln→Ln+1 = 存在 e1∈Layer(n) 与 e2∈Layer(n+1)，
  fault_id 相同（跨单元关联键；可选 dyn_inst_seq 双键加强）且
  time(e2) >= time(e1)（时间/可达性）。
- 终止判定：
  * full                    —— 全边 proven 且到达 L4/L5 终局事件之一
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


def _layer_of(evt):
    return P.KIND_LAYER.get(evt.get("kind", ""))


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


def _edges_for(chain_events):
    """逐边判定：Ln→Ln+1 proven 当且仅当存在共享 fault_id 的
    (e1∈Ln, e2∈Ln+1) 且 tick(e2) >= tick(e1)（时间/可达性）。"""
    by_layer = {}
    for e in chain_events:
        lay = _layer_of(e)
        if lay:
            by_layer.setdefault(lay, []).append(e)
    edges = {}
    for i in range(len(LAYERS) - 1):
        a, b = LAYERS[i], LAYERS[i + 1]
        ev_a, ev_b = by_layer.get(a, []), by_layer.get(b, [])
        proven = False
        witness = None
        for e1 in ev_a:
            for e2 in ev_b:
                if _tick(e2) >= _tick(e1):
                    proven = True
                    witness = {
                        "from": f"{a}:{e1.get('kind')}@t{e1.get('tick')}",
                        "to": f"{b}:{e2.get('kind')}@t{e2.get('tick')}",
                        "shared_keys": ["fault_id"],
                    }
                    if (e1.get("dyn_inst_seq") and e2.get("dyn_inst_seq")
                            and e1["dyn_inst_seq"] == e2["dyn_inst_seq"]):
                        witness["shared_keys"].append("dyn_inst_seq")
                    break
            if proven:
                break
        edges[f"{a}->{b}"] = "proven" if proven else "missing"
        if witness:
            edges[f"{a}->{b}_witness"] = witness
    return edges, by_layer


def _terminal(chain_events, edges, by_layer):
    """终止判定（规格三终局 + Unknown 兜底；缺席不猜测）。"""
    # [H2-fix] tlb_fault = Hardware 检测 + contained（翻译层遏制——
    # A01 POST 根因：corrupted vaddr 未映射 → MMU 检测 → 传播被遏制）
    for e in chain_events:
        if (e.get("kind") == "tlb_fault"
                and e.get("detection_layer") == "Hardware"
                and e.get("contained") == "1"):
            return "detected_contained"
    # 显式 contained 检测（L5 证据事件）
    for e in chain_events:
        if (e.get("detection_layer") and e.get("contained") == "1"
                and e.get("kind") in _L5_OUTCOME_KINDS):
            return "detected_contained"
    # 显式 squash/replay/mask（L5 证据事件）
    for e in chain_events:
        if any(k in e.get("kind", "") for k in ("squash", "replay", "mask")):
            if e.get("kind") in _L5_OUTCOME_KINDS or _layer_of(e):
                # 只认 kind 明示的事件（缺席不推断 Masked——规格钉死）
                if e.get("kind") in _L5_OUTCOME_KINDS:
                    return "squash_replay_masked"
    # 逐边最深可证层级
    deepest = None
    for i, lay in enumerate(LAYERS):
        if by_layer.get(lay):
            deepest = lay
        else:
            break
    if deepest is None:
        return "no_l0_fault_applied"
    # full（规格终局 1：到达 errant commit + 链终局事件）= L0→L4 各边
    # proven 且 L4 终局事件在场。L4→L5（chain_end）是运行终局的证据，
    # 正常退出时应在案；abort 样本无 chain_end（退出回调不运行）——
    # 此时 full 仍可成立（L4 终局即到达），L4→L5 标 missing=诚实。
    l4_terminal = any(e.get("kind") in _L4_TERMINAL_KINDS
                      for e in by_layer.get("L4", []))
    l0_to_l4_proven = all(edges[f"{LAYERS[i]}->{LAYERS[i+1]}"] == "proven"
                          for i in range(len(LAYERS) - 2))  # L0→…→L4
    if l0_to_l4_proven and l4_terminal:
        return "full"
    if deepest == "L0" and not by_layer.get("L1"):
        return "provable_to_L0_then_unknown"
    return f"provable_to_{deepest}_then_unknown"


def check_chain(events, spec_nodes=None):
    """主入口：events = lsu_prop_fields 解析的事件列表。

    返回 {faults: {fault_id: {edges, terminal, provable_to, beyond}},
          spec_nodes}（spec_nodes 透传记录判据来源）。
    """
    result = {"faults": {}, "spec_nodes": spec_nodes or LAYERS}
    for fid, chain in _group_by_fault(events).items():
        edges, by_layer = _edges_for(chain)
        term = _terminal(chain, edges, by_layer)
        provable = None
        for lay in LAYERS:
            if by_layer.get(lay):
                provable = lay
            else:
                break
        result["faults"][fid] = {
            "edges": edges,
            "terminal": term,
            "provable_to": provable,
            "beyond": "" if term == "full" else "Unknown",  # 绝不 Masked
            "event_count": len(chain),
        }
    return result


def main():
    if len(sys.argv) < 2:
        print("usage: lsu_chain_check.py <prop_evt.txt[.gz]> [--run-id X]",
              file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    events, truncated = P.read_events(path)
    verdict = check_chain(events)
    verdict["truncated_stream"] = truncated
    verdict["total_events"] = len(events)
    print(json.dumps(verdict, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
