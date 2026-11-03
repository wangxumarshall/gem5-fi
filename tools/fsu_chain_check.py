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
  8. [FSU][F5] 永久故障：根可为 `fault_installed`（L0）；一个 fault 只允许
     一个安装根；`exposure` 是同一 fault_id 的旁支（不占层、不计独立
     fault）；首个 activated exposure 必须出现在通往 L5 的直接 parent 链上；
     `chain_end` 的 exposures_total/sampled/dropped/activated 必须自洽且与
     流内实际 exposure 样本一致（截断时由 truncated=True 阻断认证）。

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


def _int_or_none(evt, key):
    text = _clean(evt, key)
    if not text:
        return None
    try:
        return int(text, 10)
    except ValueError:
        return None


def _mask_ok(evt, key):
    text = _clean(evt, key)
    if not text:
        return None
    try:
        return int(text, 16)
    except ValueError:
        return None


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
            # [FSU][F5] Sampled non-activation exposures are dead-end branch
            # evidence, not chain forks. Descending into them would blow up
            # the path space (MAX_PATHS) and could hide the real activation
            # chain. Skip a branch event that has no children of its own;
            # an activated exposure carries the L2-L5 chain and is kept.
            if (_clean(kid, "kind") in P.BRANCH_KINDS
                    and kid_id not in children):
                continue
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


def _f5_accounting(fid, events, root, violations, truncated):
    """Validate one permanent fault's install/exposure/terminal accounting.

    Returns a dict of observed counters. Every rule is about the SINGLE
    installed fault: exposure events never create additional faults, and
    the capacity fields on chain_end must reconcile with the samples that
    actually reached the stream.
    """
    root_id = _clean(root, "event_id")
    root_mask = _mask_ok(root, "fault_mask")
    root_pol = _int_or_none(root, "stuck_polarity")
    root_first_sn = _int_or_none(root, "first_eligible_sn")
    exposures = [e for e in events if _clean(e, "kind") in P.BRANCH_KINDS]
    activated_events = [e for e in exposures
                        if _clean(e, "activated") == "1"]
    exp_ids = []
    for e in exposures:
        eid = _clean(e, "event_id")
        if not _clean(e, "parent_event_id"):
            violations.append(f"exposure_without_parent:{eid}")
        if _clean(e, "fault_id") != str(fid):
            violations.append(f"exposure_wrong_fault_id:{eid}")
        ie = _clean(e, "install_event")
        if ie and ie != root_id:
            violations.append(f"exposure_wrong_install_event:{eid}")
        m = _mask_ok(e, "fixed_mask")
        if m is not None and root_mask is not None and m != root_mask:
            violations.append(f"exposure_mask_drift:{eid}")
        p = _int_or_none(e, "stuck_polarity")
        if p is not None and root_pol is not None and p != root_pol:
            violations.append(f"exposure_polarity_drift:{eid}")
        # Verify the recorded values really implement forced stuck-at:
        # after == applyStuck(before, mask, polarity), no non-target bit
        # moved, and `activated` equals the polarity-difference predicate.
        cb = _mask_ok(e, "correct_before")
        sa = _mask_ok(e, "stuck_after")
        if cb is not None and sa is not None and m is not None \
                and p in (0, 1):
            expected = (cb | m) if p else (cb & ~m)
            if sa != expected:
                violations.append(f"f5_stuck_apply_mismatch:{eid}")
            if ((cb ^ sa) & ~m) != 0:
                violations.append(f"f5_non_target_bit_changed:{eid}")
            act_expected = bool(((~cb) & m) if p else (cb & m))
            if (_clean(e, "activated") == "1") != act_expected:
                violations.append(f"f5_activation_flag_mismatch:{eid}")
        xid = _int_or_none(e, "exposure_id")
        if xid is not None:
            exp_ids.append(xid)
    if len(exp_ids) != len(set(exp_ids)):
        violations.append("duplicate_exposure_id")

    ends = [e for e in events
            if _clean(e, "kind") == "chain_end"
            and _clean(e, "exposures_total")]
    end = ends[-1] if ends else None
    total = sampled = dropped = activated_total = None
    first_act_sn = None
    if end is not None:
        total = _int_or_none(end, "exposures_total")
        sampled = _int_or_none(end, "exposures_sampled")
        dropped = _int_or_none(end, "exposures_dropped")
        activated_total = _int_or_none(end, "activated_exposure_count")
        first_act_sn = _int_or_none(end, "first_activated_sn")
        ie = _clean(end, "install_event")
        if ie and ie != root_id:
            violations.append(f"chain_end_wrong_install_event:{ie}")
        m = _mask_ok(end, "fixed_mask")
        if m is not None and root_mask is not None and m != root_mask:
            violations.append("chain_end_mask_drift")
        p = _int_or_none(end, "stuck_polarity")
        if p is not None and root_pol is not None and p != root_pol:
            violations.append("chain_end_polarity_drift")
        e_first = _int_or_none(end, "first_eligible_sn")
        if e_first is not None and root_first_sn is not None \
                and e_first != root_first_sn:
            violations.append("chain_end_first_eligible_sn_mismatch")
        r_sn = _int_or_none(root, "dyn_inst_seq")
        if e_first is not None and r_sn is not None and e_first != r_sn:
            violations.append("install_sn_not_first_eligible_sn")
    elif _clean(root, "kind") == "fault_installed":
        violations.append("missing_f5_chain_end")

    if total is not None and sampled is not None and dropped is not None:
        if total != sampled + dropped:
            violations.append(
                f"f5_capacity_mismatch:total={total},sampled={sampled},"
                f"dropped={dropped}")
        if dropped < 0 or sampled < 0:
            violations.append("f5_capacity_negative")
    if (not truncated and sampled is not None
            and sampled != len(exposures)):
        violations.append(
            f"f5_sampled_mismatch:sampled={sampled},"
            f"observed={len(exposures)}")
    if activated_total is not None:
        if activated_total < len(activated_events):
            violations.append(
                f"f5_activated_count_underflow:declared={activated_total},"
                f"observed={len(activated_events)}")
        if activated_total > 0 and not activated_events:
            violations.append("f5_first_activated_exposure_missing")
        if activated_total > 0 and first_act_sn is None:
            violations.append("f5_missing_first_activated_sn")
        if first_act_sn is not None and not any(
                _int_or_none(e, "dyn_inst_seq") == first_act_sn
                for e in activated_events):
            violations.append("f5_first_activated_sn_not_observed")
    if not exposures and total not in (None, 0):
        violations.append("f5_exposures_total_without_events")
    return {
        "root_event_id": root_id,
        "exposure_events": len(exposures),
        "activated_events": len(activated_events),
        "exposures_total": total,
        "exposures_sampled": sampled,
        "exposures_dropped": dropped,
        "activated_exposure_count": activated_total,
        "first_activated_sn": first_act_sn,
        "chain_end_event_id": _clean(end, "event_id") if end else None,
        "chain_end_terminal": _clean(end, "terminal") if end else None,
    }


def _check_one(fid, events, truncated=False):
    violations = []
    by_id, children, dup = _children_map(events)
    for d in dup:
        violations.append(f"duplicate_event_id:{d}")

    roots = [e for e in events
             if _clean(e, "kind") in P.ROOT_KINDS
             and _clean(e, "parent_event_id") == ""]
    if not roots:
        return {
            "fault_id": fid, "root_event_id": None, "path_event_ids": [],
            "off_chain_event_ids": sorted(by_id), "layers": [],
            "deepest_layer": None, "layers_na": [],
            "terminal": "no_root", "beyond": "Unknown",
            "violations": violations + ["no_fault_applied_root"],
            "admitted": False, "certified": False,
            "l5_witness_event_id": None,
            "containment_event_id": None, "containment_layer": None,
            "f5": None,
        }
    if len(roots) > 1:
        kinds = {_clean(e, "kind") for e in roots}
        if kinds == {"fault_installed"}:
            violations.append("multiple_fault_installed_roots")
        else:
            violations.append("multiple_fault_roots")
            if "fault_installed" in kinds:
                violations.append("fault_installed_with_other_root")
    root = roots[0]
    is_f5 = _clean(root, "kind") == "fault_installed"
    f5 = _f5_accounting(fid, events, root, violations, truncated) \
        if is_f5 else None

    # 非根事件 parent 必须在本 fault 组内
    for e in events:
        eid, pid = _clean(e, "event_id"), _clean(e, "parent_event_id")
        if pid and pid not in by_id:
            violations.append(f"orphan_parent:{eid}->{pid}")

    # 未激活：根事件显式 activated=0 → 非合格 seed。F5's installation is
    # not an activation judgement; its exposure events carry activated.
    if not is_f5 and _clean(root, "activated") == "0":
        return {
            "fault_id": fid, "root_event_id": _clean(root, "event_id"),
            "path_event_ids": [_clean(root, "event_id")],
            "off_chain_event_ids": sorted(
                set(by_id) - {_clean(root, "event_id")}),
            "layers": ["L0"], "deepest_layer": "L0", "layers_na": [],
            "terminal": "not_activated", "beyond": "N/A",
            "violations": violations, "admitted": False, "certified": False,
            "l5_witness_event_id": None, "containment_event_id": None,
            "containment_layer": None, "f5": f5,
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

    # [FSU][F5] A permanent fault's terminal is defined by its OWN exposure
    # accounting, not by a generic lifecycle marker:
    #   activated_exposure_count == 0  -> not_activated
    #   activated > 0 but no L5 commit -> exposed_unconsumed (honest Unknown)
    #   real L5 commit                -> full, and the direct chain MUST pass
    #                                    through the first activated exposure.
    if is_f5 and f5 is not None:
        act = f5.get("activated_exposure_count") or 0
        ct = f5.get("chain_end_terminal") or ""
        if l5_evt is not None and act > 0:
            first_sn = f5.get("first_activated_sn")
            through = any(
                _clean(e, "kind") in P.BRANCH_KINDS
                and _clean(e, "activated") == "1"
                and (first_sn is None
                     or _int_or_none(e, "dyn_inst_seq") == first_sn)
                for e in best)
            if not through:
                violations.append(
                    "activation_chain_not_through_first_activated")
        if l5_evt is None:
            if act > 0:
                terminal = "exposed_unconsumed"
            elif (f5.get("exposures_total") or 0) > 0:
                terminal = "not_activated"
        if ct == "committed" and l5_evt is None:
            violations.append("f5_chain_end_claims_commit_without_l5")
        if ct == "not_activated" and act > 0:
            violations.append("f5_chain_end_terminal_contradicts_activation")

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
        "f5": f5,
        "admitted": admitted,
        # certified is the same closed-terminal + no-violation gate; the
        # seed-level audit additionally requires intact evidence (gzip EOF,
        # stats, hashes) and recomputes it, never hard-coding true.
        "certified": admitted,
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
    orphan_exposure_groups = []
    orphan_exposure_violations = []
    for fid, group in sorted(_group_by_fault(events).items()):
        # [FSU][F5] An exposure is a branch of ONE installed fault. A group
        # with exposure events but no root is not a fault and must never be
        # counted as one; report it loudly instead.
        has_root = any(_clean(e, "kind") in P.ROOT_KINDS for e in group)
        has_branch = any(_clean(e, "kind") in P.BRANCH_KINDS for e in group)
        if has_branch and not has_root:
            orphan_exposure_groups.append(fid)
            for e in group:
                if _clean(e, "kind") in P.BRANCH_KINDS:
                    orphan_exposure_violations.append(
                        f"exposure_without_fault_installed_root:{fid}:"
                        f"{_clean(e, 'event_id')}")
            continue
        result = _check_one(fid, group, truncated=truncated)
        if identity:
            result["violations"].extend(identity)
            result["admitted"] = False
        if truncated:
            result["violations"].append("truncated_stream")
            result["admitted"] = False
        faults[fid] = result
    admitted_faults = sorted(fid for fid, r in faults.items() if r["admitted"])
    all_violations = []
    for r in faults.values():
        all_violations.extend(r.get("violations", []))
    all_violations.extend(orphan_exposure_violations)
    all_violations.extend(identity)
    if truncated:
        all_violations.append("truncated_stream")
    admitted = (bool(admitted_faults) and not truncated and not identity
                and not orphan_exposure_violations)
    # Seed-level certified requires EVERY fault to be closed; one fault
    # reaching L5 must never auto-certify the others.
    certified = admitted and all(r.get("certified") for r in faults.values())
    return {
        "path": str(path),
        "event_count": len(events),
        "truncated": truncated,
        "truncation_reason": reason,
        "identity_violations": identity,
        "faults": faults,
        "fault_count": len(faults),
        "orphan_exposure_groups": orphan_exposure_groups,
        "orphan_exposure_violations": orphan_exposure_violations,
        "fault_terminals": {fid: r.get("terminal")
                            for fid, r in faults.items()},
        "admitted_faults": admitted_faults,
        "all_faults_admitted": bool(faults) and all(
            r.get("admitted") for r in faults.values()),
        "all_faults_certified": bool(faults) and all(
            r.get("certified") for r in faults.values()),
        "admitted": admitted,
        "certified": certified,
        "violations": all_violations,
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
