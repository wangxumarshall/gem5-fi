#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fsu_chain_check.py — FSU 传播链审计器（L0–L5，单祖先直接 parent 链）。

判定原则（与任务书第八节一致）:
  1. 主链只由 parent_event_id 的单祖先链构成；每一步必须是直接 parent。
  2. 旁支单独记录，不混入主链。
  3. tick 沿主链单调不降；回退即违规。
  4. chain_end 只是生命周期收口，不占 L0–L5，不能冒充 L5。
  5. full 必须有真实 L5 见证（errant commit / 架构状态差异 / oracle 差异）。
  6. contained 必须有实时含住事件与检测层级；后续层写 N/A。
  7. Masked / contained / Crash / Timeout / SDC / 未激活严格区分；
     缺事件只能标 Unknown，绝不推断 Masked。

用法:
  python3 tools/fsu_chain_check.py <fsu_prop_evt.txt[.gz]> \
      [--run-id FSU-...] [--sample-run-id s1]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fsu_prop_fields as P  # noqa: E402

LAYERS = ["L0", "L1", "L2", "L3", "L4", "L5"]
MAX_PATHS = 20000


def _tick(evt):
    try:
        return int(str(evt.get("tick", "")).strip())
    except (TypeError, ValueError):
        return None


def _clean(evt, key):
    return str(evt.get(key, "")).strip()


def _is_true(v):
    return str(v).strip() in P.CONTAINED_TRUE


def _empty(v):
    return str(v).strip() in P.EMPTY_VALUES


def _l5_witness_ok(evt):
    """真实 L5 见证：L5 层 + 非空 outcome + 真实架构/软件差异。"""
    if _clean(evt, "kind") not in P.L5_WITNESS_KINDS:
        return False
    if _clean(evt, "detection_layer") != "L5":
        return False
    outcome = _clean(evt, "outcome")
    if _empty(outcome):
        return False
    if _clean(evt, "kind") == "commit":
        return (outcome in ("errant_commit", "sdc", "sdc_escape")
                or not _empty(_clean(evt, "oracle_diff")))
    return (not _empty(outcome)) or (not _empty(_clean(evt, "oracle_diff")))


def _containment(evt):
    """返回 (layer, terminal_kind) 或 None。"""
    kind = _clean(evt, "kind")
    if kind not in P.CONTAIN_KINDS:
        return None
    dl = _clean(evt, "detection_layer")
    if dl not in LAYERS:
        return None
    return dl, kind


def _group_by_fault(events):
    groups = {}
    for e in events:
        groups.setdefault(_clean(e, "fault_id") or "<empty>", []).append(e)
    return groups


def _children_map(events):
    by_id, children = {}, {}
    dup = []
    for e in events:
        eid = _clean(e, "event_id")
        if eid in by_id:
            dup.append(eid)
        by_id[eid] = e
        children.setdefault(_clean(e, "parent_event_id"), []).append(e)
    return by_id, children, dup


def _enumerate_paths(root, children, violations):
    """从根沿直接 parent→child 边枚举路径（tick 不降，防环）。"""
    paths = []
    stack = [(root, [root], {_clean(root, "event_id")})]
    while stack and len(paths) < MAX_PATHS:
        node, path, seen = stack.pop()
        kids = children.get(_clean(node, "event_id"), [])
        advanced = False
        for kid in kids:
            kid_id = _clean(kid, "event_id")
            if kid_id in seen:
                violations.append(f"cycle:{kid_id}")
                continue
            t0, t1 = _tick(node), _tick(kid)
            if t0 is not None and t1 is not None and t1 < t0:
                violations.append(f"tick_regression:{kid_id}")
                continue
            advanced = True
            stack.append((kid, path + [kid], seen | {kid_id}))
        if not advanced:
            paths.append(path)
    if not paths:
        paths = [[root]]
    return paths


def _path_layers(path):
    out = []
    for e in path:
        layer = P.layer_of(e)
        if layer is not None:
            out.append((e, layer))
    return out


def _score(path):
    contains = sum(1 for e in path if _containment(e))
    l5 = sum(1 for e in path if _l5_witness_ok(e))
    layered = _path_layers(path)
    deep = LAYERS.index(layered[-1][1]) if layered else -1
    kind = 3 if contains else 2 if l5 else 1 if deep >= 0 else 0
    return (kind, deep, len(path))


def _check_one(fid, events):
    violations = []
    by_id, children, dup = _children_map(events)
    for d in dup:
        violations.append(f"duplicate_event_id:{d}")

    roots = [e for e in events
             if _clean(e, "kind") == "fault_applied"
             and _clean(e, "parent_event_id") == ""]
    if not roots:
        return {
            "fault_id": fid, "root_event_id": None, "path_event_ids": [],
            "off_chain_event_ids": sorted(by_id), "layers": [],
            "deepest_layer": None, "layers_na": [],
            "terminal": "no_root", "beyond": "Unknown",
            "violations": violations + ["no_fault_applied_root"],
            "admitted": False, "l5_witness_event_id": None,
            "containment_event_id": None, "containment_layer": None,
        }
    if len(roots) > 1:
        violations.append("multiple_fault_applied_roots")
    root = roots[0]

    # 非根事件 parent 必须在本 fault 组内
    for e in events:
        eid, pid = _clean(e, "event_id"), _clean(e, "parent_event_id")
        if pid and pid not in by_id:
            violations.append(f"orphan_parent:{eid}->{pid}")

    # 未激活：根事件显式 activated=0 → 非合格 seed
    if _clean(root, "activated") == "0":
        return {
            "fault_id": fid, "root_event_id": _clean(root, "event_id"),
            "path_event_ids": [_clean(root, "event_id")],
            "off_chain_event_ids": sorted(
                set(by_id) - {_clean(root, "event_id")}),
            "layers": ["L0"], "deepest_layer": "L0", "layers_na": [],
            "terminal": "not_activated", "beyond": "N/A",
            "violations": violations, "admitted": False,
            "l5_witness_event_id": None, "containment_event_id": None,
            "containment_layer": None,
        }

    paths = _enumerate_paths(root, children, violations)
    best = max(paths, key=_score)
    layered = _path_layers(best)
    layers = [l for _, l in layered]
    path_ids = [_clean(e, "event_id") for e in best]

    # 层级不得回退
    idx = [LAYERS.index(l) for l in layers]
    for a, b in zip(idx, idx[1:]):
        if b < a:
            violations.append("layer_regression")

    l5_evt = next((e for e in best if _l5_witness_ok(e)), None)
    # 任何自称 L5 但无真实见证的事件
    for e, l in layered:
        if l == "L5" and not _l5_witness_ok(e):
            violations.append(f"l5_without_witness:{_clean(e, 'event_id')}")
    # chain_end 不得自称 L5
    for e in best:
        if _clean(e, "kind") in P.LIFECYCLE_KINDS and _clean(e, "detection_layer") == "L5":
            violations.append(f"chain_end_claimed_l5:{_clean(e, 'event_id')}")

    not_act = next((e for e in best if _clean(e, "kind") == "not_activated"), None)
    contain = next(((_containment(e), e) for e in best if _containment(e)), None)
    if not_act is not None:
        terminal = "not_activated"
        contained_id, contained_layer = None, None
    elif contain:
        (dl, ckind), cevt = contain
        if ckind == "crash":
            terminal = "crash"
        elif ckind == "timeout":
            terminal = "timeout"
        elif _clean(cevt, "outcome") in ("sdc", "sdc_escape"):
            terminal = "sdc"
        else:
            terminal = f"contained_{dl}"
        contained_id = _clean(cevt, "event_id")
        contained_layer = dl
    else:
        contained_id, contained_layer = None, None
        if l5_evt is not None:
            # FSU 规格只要求 L0 + 直接载体 + 真实 L5 见证；真实未到达的中间层
            # 记 N/A，但不得用跳接事件凑层。
            if "L0" not in layers or "L1" not in layers:
                violations.append("incomplete_carrier_sequence")
                terminal = (f"provable_to_{layers[-1]}_then_unknown"
                            if layers else "unknown")
            elif not any(l in ("L2", "L3", "L4") for l in layers):
                violations.append("no_intermediate_layer")
                terminal = f"provable_to_{layers[-1]}_then_unknown"
            else:
                terminal = "full"
        elif layers:
            terminal = f"provable_to_{layers[-1]}_then_unknown"
        else:
            terminal = "unknown"

    closed = (terminal in P.CLOSED_TERMINALS
              or terminal.startswith("contained_"))
    beyond = "N/A" if closed else "Unknown"
    layers_na = []
    if closed and layers:
        deepest_idx = LAYERS.index(layers[-1])
        layers_na = [l for l in LAYERS if l not in layers
                     and LAYERS.index(l) < deepest_idx]
        if terminal == "full":
            layers_na = [l for l in LAYERS if l not in layers]
        else:
            layers_na = LAYERS[deepest_idx + 1:]
    admitted = closed and not violations
    return {
        "fault_id": fid,
        "root_event_id": _clean(root, "event_id"),
        "path_event_ids": path_ids,
        "layers": layers,
        "deepest_layer": layers[-1] if layers else None,
        "layers_na": layers_na,
        "terminal": terminal,
        "beyond": beyond,
        "l5_witness_event_id": _clean(l5_evt, "event_id") if l5_evt else None,
        "containment_event_id": contained_id,
        "containment_layer": contained_layer,
        "off_chain_event_ids": sorted(set(by_id) - set(path_ids)),
        "violations": violations,
        "admitted": admitted,
    }


def check_stream(path, run_id=None, sample_run_id=None):
    events, truncated, reason = P.read_stream(path)
    identity = []
    for e in events:
        if run_id is not None and _clean(e, "run_id") != run_id:
            identity.append(f"run_id:{_clean(e, 'event_id')}:"
                            f"{_clean(e, 'run_id')}!={run_id}")
        if sample_run_id is not None and _clean(e, "sample_run_id") != sample_run_id:
            identity.append(f"sample_run_id:{_clean(e, 'event_id')}:"
                            f"{_clean(e, 'sample_run_id')}!={sample_run_id}")
    faults = {}
    for fid, group in sorted(_group_by_fault(events).items()):
        result = _check_one(fid, group)
        if identity:
            result["violations"].extend(identity)
            result["admitted"] = False
        if truncated:
            result["violations"].append("truncated_stream")
            result["admitted"] = False
        faults[fid] = result
    return {
        "path": str(path),
        "event_count": len(events),
        "truncated": truncated,
        "truncation_reason": reason,
        "identity_violations": identity,
        "faults": faults,
        "admitted_faults": sorted(fid for fid, r in faults.items() if r["admitted"]),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="FSU 传播链审计器")
    ap.add_argument("stream")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--sample-run-id", default=None)
    a = ap.parse_args(argv)
    result = check_stream(a.stream, a.run_id, a.sample_run_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["admitted_faults"] else 1


if __name__ == "__main__":
    sys.exit(main())
